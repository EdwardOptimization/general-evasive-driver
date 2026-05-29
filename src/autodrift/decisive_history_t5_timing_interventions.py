"""Timing-amplified measured interventions for the T5 high-speed subset."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec
from autodrift.decisive_history_t5_interventions import (
    DONOR_MODE,
    ELIGIBLE_MODES,
    ELIGIBLE_SOURCE_FAMILY,
    GUARDRAIL_KEYS,
    _clone_hidden,
    _guardrail_rows,
    _success,
    donor_spec_for_mode,
    eligible_retarget_specs,
)
from autodrift.decisive_history_source_retarget import RetargetedHookSpec
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy


DEFAULT_RUN_DIR = Path("runs/m1521_t5_timing_amplified_intervention_smoke")
TIMING_ANCHORS = ("decision", "decision_minus_8", "reveal_plus_4", "reveal")
TIMING_VARIANTS = (
    "normal",
    "reset_hidden_once_at_anchor",
    "reset_hidden_every_step_from_anchor",
    "zero_current_response_from_anchor",
    "zero_action_history_from_anchor",
    "delayed_hidden_8_at_anchor",
    "wrong_history_donor_hidden_at_anchor",
)
OUTCOME_MARGIN_GAP_THRESHOLD = 0.02
ACTION_DIVERGENCE_THRESHOLD = 0.05
STATE_DIVERGENCE_THRESHOLD = 0.10
STATE_DELTA_FIELDS = ("x", "y", "vx", "vy", "yaw_rate")


@dataclass
class AnchorReplayState:
    """Environment and policy state exactly before the anchor-step action."""

    spec: DecisiveHistoryEnvHookSpec
    retarget_mode: str
    anchor_name: str
    anchor_step: int
    env: AutoDriftEnv | None
    observation: np.ndarray | None
    info: dict[str, Any]
    hidden: torch.Tensor | None
    hidden_by_step: dict[int, torch.Tensor]
    first_failure: str = "none"
    error_type: str = ""
    error_message: str = ""

    @property
    def reached_anchor(self) -> bool:
        return self.env is not None and self.observation is not None and self.first_failure == "none"


def anchor_step_for(spec: DecisiveHistoryEnvHookSpec, anchor_name: str) -> int:
    """Return bounded anchor step for a named timing-amplification anchor."""

    reveal = int(spec.reveal_step)
    decision = int(spec.decision_step)
    if anchor_name == "decision":
        return decision
    if anchor_name == "decision_minus_8":
        return max(reveal, decision - 8)
    if anchor_name == "reveal_plus_4":
        return min(decision - 1, reveal + 4)
    if anchor_name == "reveal":
        return reveal
    raise ValueError(f"unknown timing anchor: {anchor_name}")


def _terminal_reason(info: Mapping[str, Any], terminated: bool, truncated: bool, exhausted: bool) -> str:
    if bool(info.get("collision", False)):
        return "collision"
    if bool(info.get("obstacle_completed", False)):
        return "obstacle_completed"
    if truncated:
        return "truncated"
    if terminated:
        return "terminated"
    if exhausted:
        return "continuation_steps"
    return "running"


def _state_values(env: AutoDriftEnv | None) -> dict[str, float | None]:
    if env is None:
        return {field: None for field in STATE_DELTA_FIELDS}
    state = getattr(env, "state", None)
    if state is None:
        return {field: None for field in STATE_DELTA_FIELDS}
    return {field: float(getattr(state, field)) for field in STATE_DELTA_FIELDS}


def _prefixed_state(prefix: str, values: Mapping[str, float | None]) -> dict[str, float | None]:
    return {f"{prefix}_{field}": values.get(field) for field in STATE_DELTA_FIELDS}


def _action_l2(action: Sequence[float], normal_action: Sequence[float] | None) -> float | None:
    if normal_action is None:
        return None
    left = np.asarray(action, dtype=np.float64)
    right = np.asarray(normal_action, dtype=np.float64)
    return float(np.linalg.norm(left - right))


def _policy_for_variant(model: Any, spec: DecisiveHistoryEnvHookSpec, variant: str) -> ActorPolicy:
    ablation = "none"
    reset_hidden_policy = "episode_persistent"
    if variant == "zero_current_response_from_anchor":
        ablation = "zero_current_response"
    elif variant == "zero_action_history_from_anchor":
        ablation = "zero_action_history"
    elif variant == "reset_hidden_every_step_from_anchor":
        reset_hidden_policy = "every_step_control"
    return ActorPolicy(model, spec.env_config, ablation=ablation, reset_hidden_policy=reset_hidden_policy)


def replay_to_anchor(
    spec: DecisiveHistoryEnvHookSpec,
    retarget_mode: str,
    anchor_name: str,
    model: Any,
) -> AnchorReplayState:
    """Replay deterministic fixed policy until just before an anchor action."""

    anchor_step = anchor_step_for(spec, anchor_name)
    policy = ActorPolicy(model, spec.env_config)
    hidden_by_step: dict[int, torch.Tensor] = {}
    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
        policy.reset()
        while int(info.get("step", 0)) < anchor_step:
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(hidden_by_step)))
            action = policy.act(observation, info)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            hidden_by_step[step] = _clone_hidden(policy.hidden)
            observation, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                return AnchorReplayState(
                    spec=spec,
                    retarget_mode=retarget_mode,
                    anchor_name=anchor_name,
                    anchor_step=anchor_step,
                    env=None,
                    observation=None,
                    info=info,
                    hidden=_clone_hidden(policy.hidden),
                    hidden_by_step=hidden_by_step,
                    first_failure="did_not_reach_anchor_step",
                )
        return AnchorReplayState(
            spec=spec,
            retarget_mode=retarget_mode,
            anchor_name=anchor_name,
            anchor_step=anchor_step,
            env=env,
            observation=observation,
            info=info,
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
        )
    except Exception as exc:
        return AnchorReplayState(
            spec=spec,
            retarget_mode=retarget_mode,
            anchor_name=anchor_name,
            anchor_step=anchor_step,
            env=None,
            observation=None,
            info={},
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            first_failure="target_replay_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


def _initial_hidden_for_variant(
    state: AnchorReplayState,
    *,
    variant: str,
    donor_state: AnchorReplayState | None,
    delay_steps: int,
) -> tuple[torch.Tensor | None, str, str]:
    if variant == "normal":
        return _clone_hidden(state.hidden), "", "not_applicable"
    if variant in {"zero_current_response_from_anchor", "zero_action_history_from_anchor"}:
        return _clone_hidden(state.hidden), "", "not_applicable"
    if variant in {"reset_hidden_once_at_anchor", "reset_hidden_every_step_from_anchor"}:
        return None, "", "not_applicable"
    if variant == "delayed_hidden_8_at_anchor":
        delayed_step = int(state.anchor_step) - int(delay_steps)
        hidden = state.hidden_by_step.get(delayed_step)
        if hidden is None:
            return None, "", "missing_delayed_hidden"
        return _clone_hidden(hidden), "", "ok"
    if variant == "wrong_history_donor_hidden_at_anchor":
        if donor_state is None:
            return None, "", "missing_donor"
        if not donor_state.reached_anchor:
            return None, donor_state.spec.candidate_id, f"donor_failed:{donor_state.first_failure}"
        return _clone_hidden(donor_state.hidden), donor_state.spec.candidate_id, "ok"
    raise ValueError(f"unknown timing intervention variant: {variant}")


def _failure_row(
    *,
    target: RetargetedHookSpec,
    anchor_name: str,
    anchor_step: int,
    variant: str,
    donor_candidate_id: str,
    donor_status: str,
    target_replay_status: str,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate_id": target.hook_spec.candidate_id,
        "retarget_mode": target.retarget_mode,
        "anchor_name": anchor_name,
        "anchor_step": anchor_step,
        "variant": variant,
        "seed": target.hook_spec.seed,
        "reveal_step": target.hook_spec.reveal_step,
        "decision_step": target.hook_spec.decision_step,
        "donor_candidate_id": donor_candidate_id,
        "donor_status": donor_status,
        "target_replay_status": target_replay_status,
        "error_type": error_type,
        "error_message": error_message,
        "reached_anchor": False,
        "reached_decision": False,
        "reached_post_decision": False,
        "terminal_reason": target_replay_status,
        "collision": False,
        "obstacle_completed": False,
        "success": False,
    }
    row.update(_prefixed_state("anchor_state", {field: None for field in STATE_DELTA_FIELDS}))
    row.update(_prefixed_state("decision_state", {field: None for field in STATE_DELTA_FIELDS}))
    return row


def run_timing_intervention_variant(
    *,
    target: RetargetedHookSpec,
    anchor_name: str,
    variant: str,
    model: Any,
    donor: RetargetedHookSpec | None = None,
    continuation_steps: int = 64,
    delay_steps: int = 8,
) -> dict[str, Any]:
    """Run one timing-amplified intervention continuation."""

    state = replay_to_anchor(target.hook_spec, target.retarget_mode, anchor_name, model)
    donor_state = (
        replay_to_anchor(donor.hook_spec, donor.retarget_mode, anchor_name, model)
        if donor is not None
        else None
    )
    donor_candidate_id = donor.hook_spec.candidate_id if donor is not None else ""
    if not state.reached_anchor:
        return _failure_row(
            target=target,
            anchor_name=anchor_name,
            anchor_step=state.anchor_step,
            variant=variant,
            donor_candidate_id=donor_candidate_id,
            donor_status="not_run",
            target_replay_status=state.first_failure,
            error_type=state.error_type,
            error_message=state.error_message,
        )

    injected_hidden, injected_donor_id, donor_status = _initial_hidden_for_variant(
        state,
        variant=variant,
        donor_state=donor_state,
        delay_steps=delay_steps,
    )
    if injected_donor_id:
        donor_candidate_id = injected_donor_id
    if donor_status not in {"ok", "not_applicable"}:
        return _failure_row(
            target=target,
            anchor_name=anchor_name,
            anchor_step=state.anchor_step,
            variant=variant,
            donor_candidate_id=donor_candidate_id,
            donor_status=donor_status,
            target_replay_status="ok",
        )

    assert state.env is not None
    assert state.observation is not None
    policy = _policy_for_variant(model, target.hook_spec, variant)
    policy.hidden = _clone_hidden(injected_hidden)
    observation = state.observation
    info = state.info
    anchor_state = _state_values(state.env)
    first_action: np.ndarray | None = None
    decision_action: np.ndarray | None = None
    decision_state: dict[str, float | None] | None = None
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    terminated = False
    truncated = False
    reward_sum = 0.0
    terminal_step = int(info.get("step", state.anchor_step))
    reached_decision = terminal_step >= int(target.hook_spec.decision_step)
    for _ in range(int(continuation_steps)):
        if not np.all(np.isfinite(observation)):
            raise ValueError("nonfinite_observation")
        step_before_action = int(info.get("step", terminal_step))
        if step_before_action == int(target.hook_spec.decision_step) and decision_state is None:
            decision_state = _state_values(state.env)
        action = policy.act(observation, info)
        if not np.all(np.isfinite(action)):
            raise ValueError("nonfinite_action")
        if first_action is None:
            first_action = np.asarray(action, dtype=np.float64)
        if step_before_action == int(target.hook_spec.decision_step) and decision_action is None:
            decision_action = np.asarray(action, dtype=np.float64)
        observation, reward, terminated, truncated, info = state.env.step(action)
        reward_sum += float(reward)
        terminal_step = int(info.get("step", terminal_step))
        reached_decision = reached_decision or terminal_step >= int(target.hook_spec.decision_step)
        margin = float(info.get("min_clearance_margin", float("nan")))
        if np.isfinite(margin):
            min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
        if terminated or truncated:
            break
    if decision_state is None and terminal_step == int(target.hook_spec.decision_step):
        decision_state = _state_values(state.env)
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    terminal_reason = _terminal_reason(info, bool(terminated), bool(truncated), exhausted=not (terminated or truncated))
    first = first_action if first_action is not None else np.zeros(3, dtype=np.float64)
    decision = decision_action if decision_action is not None else np.full(3, np.nan, dtype=np.float64)
    row: dict[str, Any] = {
        "candidate_id": target.hook_spec.candidate_id,
        "retarget_mode": target.retarget_mode,
        "anchor_name": anchor_name,
        "anchor_step": state.anchor_step,
        "variant": variant,
        "seed": target.hook_spec.seed,
        "reveal_step": target.hook_spec.reveal_step,
        "decision_step": target.hook_spec.decision_step,
        "donor_candidate_id": donor_candidate_id,
        "donor_status": donor_status,
        "target_replay_status": "ok",
        "error_type": "",
        "error_message": "",
        "anchor_margin": float(state.info.get("min_clearance_margin", float("nan"))),
        "first_action_steer": float(first[0]),
        "first_action_throttle": float(first[1]),
        "first_action_brake": float(first[2]),
        "decision_action_steer": float(decision[0]),
        "decision_action_throttle": float(decision[1]),
        "decision_action_brake": float(decision[2]),
        "normal_first_action_l2": None,
        "normal_decision_action_l2": None,
        "decision_state_delta_l2": None,
        "terminal_step": terminal_step,
        "terminal_reason": terminal_reason,
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "success": _success(info, terminal_margin),
        "terminal_margin": terminal_margin,
        "min_margin_after_anchor": min_margin,
        "normal_terminal_margin": None,
        "margin_gap_from_normal": None,
        "success_drop_from_normal": None,
        "reward_sum_after_anchor": reward_sum,
        "reached_anchor": True,
        "reached_decision": bool(reached_decision),
        "reached_post_decision": terminal_step > int(target.hook_spec.decision_step),
    }
    row.update(_prefixed_state("anchor_state", anchor_state))
    row.update(_prefixed_state("decision_state", decision_state or {field: None for field in STATE_DELTA_FIELDS}))
    return row


def _group_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("candidate_id", "")), str(row.get("anchor_name", ""))


def finalize_timing_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach normal action, state, and outcome comparisons."""

    normal_by_key = {
        _group_key(row): row
        for row in rows
        if row.get("variant") == "normal" and row.get("target_replay_status") == "ok"
    }
    finalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        normal = normal_by_key.get(_group_key(row))
        if normal is not None and row.get("target_replay_status") == "ok":
            first_action = [
                float(row.get("first_action_steer", 0.0)),
                float(row.get("first_action_throttle", 0.0)),
                float(row.get("first_action_brake", 0.0)),
            ]
            normal_first_action = [
                float(normal.get("first_action_steer", 0.0)),
                float(normal.get("first_action_throttle", 0.0)),
                float(normal.get("first_action_brake", 0.0)),
            ]
            decision_action = [
                float(row.get("decision_action_steer", float("nan"))),
                float(row.get("decision_action_throttle", float("nan"))),
                float(row.get("decision_action_brake", float("nan"))),
            ]
            normal_decision_action = [
                float(normal.get("decision_action_steer", float("nan"))),
                float(normal.get("decision_action_throttle", float("nan"))),
                float(normal.get("decision_action_brake", float("nan"))),
            ]
            item["normal_first_action_l2"] = _action_l2(first_action, normal_first_action)
            if all(np.isfinite(decision_action)) and all(np.isfinite(normal_decision_action)):
                item["normal_decision_action_l2"] = _action_l2(decision_action, normal_decision_action)
            normal_margin = float(normal.get("terminal_margin", float("nan")))
            terminal_margin = float(row.get("terminal_margin", float("nan")))
            item["normal_terminal_margin"] = normal_margin
            item["margin_gap_from_normal"] = normal_margin - terminal_margin
            item["success_drop_from_normal"] = bool(normal.get("success", False)) and not bool(row.get("success", False))
            deltas: list[float] = []
            for field in STATE_DELTA_FIELDS:
                left = row.get(f"decision_state_{field}")
                right = normal.get(f"decision_state_{field}")
                if left in {"", None} or right in {"", None}:
                    continue
                left_f = float(left)
                right_f = float(right)
                if np.isfinite(left_f) and np.isfinite(right_f):
                    delta = left_f - right_f
                    item[f"decision_state_delta_{field}"] = delta
                    deltas.append(delta)
            item["decision_state_delta_l2"] = float(np.linalg.norm(deltas)) if deltas else None
        finalized.append(item)
    return finalized


def build_timing_pair_summary(
    rows: Sequence[dict[str, Any]],
    *,
    margin_gap_threshold: float = OUTCOME_MARGIN_GAP_THRESHOLD,
    action_divergence_threshold: float = ACTION_DIVERGENCE_THRESHOLD,
    state_divergence_threshold: float = STATE_DIVERGENCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Summarize effects per target and anchor."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row)].append(row)
    summaries: list[dict[str, Any]] = []
    for (candidate_id, anchor_name), group in sorted(grouped.items()):
        normal = next((row for row in group if row.get("variant") == "normal"), {})
        gaps = [
            float(row.get("margin_gap_from_normal", 0.0))
            for row in group
            if row.get("variant") != "normal" and row.get("margin_gap_from_normal") is not None
        ]
        action_l2s = [
            float(row.get("normal_first_action_l2", 0.0))
            for row in group
            if row.get("variant") != "normal" and row.get("normal_first_action_l2") is not None
        ]
        state_l2s = [
            float(row.get("decision_state_delta_l2", 0.0))
            for row in group
            if row.get("variant") != "normal" and row.get("decision_state_delta_l2") is not None
        ]
        outcome_relevant = [
            str(row.get("variant", ""))
            for row in group
            if row.get("variant") != "normal"
            and (
                bool(row.get("success_drop_from_normal", False))
                or float(row.get("margin_gap_from_normal") or 0.0) >= margin_gap_threshold
            )
        ]
        divergence_relevant = [
            str(row.get("variant", ""))
            for row in group
            if row.get("variant") != "normal"
            and (
                float(row.get("normal_first_action_l2") or 0.0) >= action_divergence_threshold
                or float(row.get("decision_state_delta_l2") or 0.0) >= state_divergence_threshold
            )
        ]
        summaries.append(
            {
                "candidate_id": candidate_id,
                "retarget_mode": normal.get("retarget_mode", group[0].get("retarget_mode", "")),
                "anchor_name": anchor_name,
                "anchor_step": normal.get("anchor_step", group[0].get("anchor_step", "")),
                "normal_success": bool(normal.get("success", False)),
                "normal_terminal_margin": normal.get("terminal_margin", ""),
                "variant_count": len(group),
                "max_margin_gap_from_normal": max(gaps) if gaps else 0.0,
                "max_first_action_l2": max(action_l2s) if action_l2s else 0.0,
                "max_decision_state_delta_l2": max(state_l2s) if state_l2s else 0.0,
                "success_drop_variants": "|".join(
                    str(row.get("variant", ""))
                    for row in group
                    if bool(row.get("success_drop_from_normal", False))
                ),
                "outcome_relevant_variants": "|".join(outcome_relevant),
                "outcome_relevant_variant_count": len(outcome_relevant),
                "divergence_relevant_variants": "|".join(divergence_relevant),
                "divergence_relevant_variant_count": len(divergence_relevant),
            }
        )
    return summaries


def build_anchor_summary(pair_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize effects by timing anchor."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        grouped[str(row.get("anchor_name", ""))].append(row)
    summaries: list[dict[str, Any]] = []
    for anchor_name, group in sorted(grouped.items()):
        summaries.append(
            {
                "anchor_name": anchor_name,
                "pair_count": len(group),
                "max_margin_gap_from_normal": max(float(row.get("max_margin_gap_from_normal", 0.0)) for row in group),
                "max_first_action_l2": max(float(row.get("max_first_action_l2", 0.0)) for row in group),
                "max_decision_state_delta_l2": max(float(row.get("max_decision_state_delta_l2", 0.0)) for row in group),
                "outcome_relevant_variant_count": sum(int(row.get("outcome_relevant_variant_count", 0)) for row in group),
                "divergence_relevant_variant_count": sum(
                    int(row.get("divergence_relevant_variant_count", 0)) for row in group
                ),
            }
        )
    return summaries


def build_timing_summary(
    rows: Sequence[dict[str, Any]],
    pair_rows: Sequence[dict[str, Any]],
    anchor_rows: Sequence[dict[str, Any]],
    *,
    eligible_target_count: int,
    anchor_count: int,
    variant_count: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build summary for timing-amplified T5 intervention smoke."""

    guardrails = _guardrail_rows()
    replay_failures = [row for row in rows if row.get("target_replay_status") != "ok"]
    donor_failures = [row for row in rows if str(row.get("donor_status", "")) not in {"", "ok", "not_applicable"}]
    gap_values = [
        float(row["margin_gap_from_normal"])
        for row in rows
        if row.get("margin_gap_from_normal") is not None and np.isfinite(float(row["margin_gap_from_normal"]))
    ]
    state_values = [
        float(row["decision_state_delta_l2"])
        for row in rows
        if row.get("decision_state_delta_l2") is not None and np.isfinite(float(row["decision_state_delta_l2"]))
    ]
    action_values = [
        float(row["normal_first_action_l2"])
        for row in rows
        if row.get("normal_first_action_l2") is not None and np.isfinite(float(row["normal_first_action_l2"]))
    ]
    return {
        "result_class": "t5_timing_amplified_intervention_smoke",
        "eligible_source_family": ELIGIBLE_SOURCE_FAMILY,
        "eligible_target_count": int(eligible_target_count),
        "anchor_count": int(anchor_count),
        "variant_count": int(variant_count),
        "continuation_steps": int(continuation_steps),
        "intervention_row_count": len(rows),
        "pair_row_count": len(pair_rows),
        "anchor_row_count": len(anchor_rows),
        "normal_row_count": sum(1 for row in rows if row.get("variant") == "normal"),
        "ablation_row_count": sum(1 for row in rows if row.get("variant") != "normal"),
        "wrong_history_row_count": sum(1 for row in rows if row.get("variant") == "wrong_history_donor_hidden_at_anchor"),
        "target_replay_failure_count": len(replay_failures),
        "donor_replay_failure_count": len(donor_failures),
        "outcome_relevant_variant_count": sum(int(row.get("outcome_relevant_variant_count", 0)) for row in pair_rows),
        "divergence_relevant_variant_count": sum(
            int(row.get("divergence_relevant_variant_count", 0)) for row in pair_rows
        ),
        "max_margin_gap_from_normal": max(gap_values) if gap_values else 0.0,
        "max_first_action_l2": max(action_values) if action_values else 0.0,
        "max_decision_state_delta_l2": max(state_values) if state_values else 0.0,
        "success_drop_count": sum(1 for row in rows if bool(row.get("success_drop_from_normal", False))),
        "guardrail_violation_count": sum(1 for row in guardrails if row["violated"]),
        "candidate_materialized": False,
        "training_started": False,
        "evaluation_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "training_corpus_exported": False,
        "labels_enter_actor_input": False,
        "level3_self_id_claim_made": False,
    }


def run_timing_intervention_smoke(
    run_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    continuation_steps: int = 64,
    anchors: Sequence[str] = TIMING_ANCHORS,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run timing-amplified intervention continuations for eligible rows."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    targets = eligible_retarget_specs()
    rows: list[dict[str, Any]] = []
    for target in targets:
        for anchor_name in anchors:
            for variant in TIMING_VARIANTS:
                donor = (
                    donor_spec_for_mode(targets, target.retarget_mode)
                    if variant == "wrong_history_donor_hidden_at_anchor"
                    else None
                )
                rows.append(
                    run_timing_intervention_variant(
                        target=target,
                        anchor_name=anchor_name,
                        variant=variant,
                        model=model,
                        donor=donor,
                        continuation_steps=continuation_steps,
                    )
                )
    finalized = finalize_timing_rows(rows)
    pair_rows = build_timing_pair_summary(finalized)
    anchor_rows = build_anchor_summary(pair_rows)
    summary = build_timing_summary(
        finalized,
        pair_rows,
        anchor_rows,
        eligible_target_count=len(targets),
        anchor_count=len(anchors),
        variant_count=len(TIMING_VARIANTS),
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "timing_intervention_rows.csv", finalized)
    write_csv_rows(output / "timing_intervention_pair_summary.csv", pair_rows)
    write_csv_rows(output / "timing_intervention_anchor_summary.csv", anchor_rows)
    write_csv_rows(output / "timing_intervention_guardrail_summary.csv", _guardrail_rows())
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run timing-amplified T5 intervention smoke.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--anchors", nargs="+", choices=TIMING_ANCHORS, default=list(TIMING_ANCHORS))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_timing_intervention_smoke(
        args.run_dir,
        checkpoint=args.checkpoint,
        continuation_steps=int(args.continuation_steps),
        anchors=tuple(args.anchors),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"max_margin_gap_from_normal={summary['max_margin_gap_from_normal']}")
    print(f"max_decision_state_delta_l2={summary['max_decision_state_delta_l2']}")


if __name__ == "__main__":
    main()
