"""Bounded history interventions over fresh ambiguity measured pairs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.decisive_history_t5_interventions import _clone_hidden
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy
from autodrift.fresh_ambiguity_measured_mining import source_row_to_hook_spec
from autodrift.fresh_ambiguity_source_mining import FreshAmbiguitySourceRow, default_source_specs, expand_source_specs


DEFAULT_PAIR_CANDIDATES = Path("runs/m1531_fresh_ambiguity_measured_mining_smoke/measured_pair_candidates.csv")
DEFAULT_RUN_DIR = Path("runs/m1534_fresh_ambiguity_history_intervention_smoke")
DEFAULT_SOURCE_SEED = 1531
VARIANTS = (
    "normal",
    "reset_hidden_once_at_anchor",
    "reset_hidden_every_step_from_anchor",
    "zero_current_response_from_anchor",
    "zero_action_history_from_anchor",
    "delayed_hidden_8_at_anchor",
    "delayed_hidden_16_at_anchor",
    "wrong_history_donor_hidden_at_anchor",
    "donor_response_action_stream_from_anchor",
    "donor_response_action_plus_hidden_from_anchor",
)
GUARDRAIL_KEYS = (
    "candidate_materialized",
    "training_started",
    "evaluation_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "training_corpus_exported",
    "labels_enter_actor_input",
    "level3_self_id_claim_made",
)


@dataclass(frozen=True)
class AcceptedMeasuredPair:
    """One accepted M1531 measured pair."""

    pair_id: str
    left_trace_id: str
    right_trace_id: str
    left_source_family: str
    right_source_family: str
    task_family: str
    scene_context_distance: float
    current_ego_distance: float
    first_action_l2: float
    terminal_margin_gap: float


@dataclass
class AnchorReplayState:
    """Replay state immediately before an anchor action."""

    pair_id: str
    side: str
    source_row_id: str
    source_row: FreshAmbiguitySourceRow
    anchor_name: str
    anchor_step: int
    env: AutoDriftEnv | None
    observation: np.ndarray | None
    info: dict[str, Any]
    hidden: torch.Tensor | None
    hidden_by_step: dict[int, torch.Tensor]
    response_action_frame: np.ndarray | None
    first_failure: str = "none"
    error_type: str = ""
    error_message: str = ""

    @property
    def reached_anchor(self) -> bool:
        return self.env is not None and self.observation is not None and self.first_failure == "none"


def load_accepted_pairs(path: Path | str = DEFAULT_PAIR_CANDIDATES) -> list[AcceptedMeasuredPair]:
    """Load accepted measured pairs from M1531 artifacts."""

    pairs: list[AcceptedMeasuredPair] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("accepted", "")).lower() != "true":
                continue
            pairs.append(
                AcceptedMeasuredPair(
                    pair_id=str(row["pair_id"]),
                    left_trace_id=str(row["left_trace_id"]),
                    right_trace_id=str(row["right_trace_id"]),
                    left_source_family=str(row["left_source_family"]),
                    right_source_family=str(row["right_source_family"]),
                    task_family=str(row["task_family"]),
                    scene_context_distance=float(row["scene_context_distance"]),
                    current_ego_distance=float(row["current_ego_distance"]),
                    first_action_l2=float(row["first_action_l2"]),
                    terminal_margin_gap=float(row["terminal_margin_gap"]),
                )
            )
    return pairs


def source_row_key(row: FreshAmbiguitySourceRow) -> str:
    """Return stable key matching M1531 trace id structure."""

    return f"{row.source_family}|{row.seed}|fresh-{row.source_family}-{row.source_index:03d}"


def source_rows_by_trace_id(*, source_seed: int = DEFAULT_SOURCE_SEED, seed_count: int = 1) -> dict[str, FreshAmbiguitySourceRow]:
    """Map M1531 trace ids to fresh source rows."""

    rows = expand_source_specs(default_source_specs(seed=source_seed, seed_count=seed_count))
    return {source_row_key(row): row for row in rows}


def anchor_step_for(row: FreshAmbiguitySourceRow, anchor_name: str) -> int:
    """Return anchor step for a source row."""

    reveal = int(row.reveal_step)
    decision = int(row.decision_step)
    if anchor_name == "decision":
        return decision
    if anchor_name == "decision_minus_8":
        return max(reveal, decision - 8)
    if anchor_name == "decision_minus_16":
        return max(reveal, decision - 16)
    if anchor_name == "reveal_plus_4":
        return min(decision - 1, reveal + 4)
    raise ValueError(f"unknown anchor: {anchor_name}")


def replay_to_anchor(
    *,
    pair_id: str,
    side: str,
    row: FreshAmbiguitySourceRow,
    anchor_name: str,
    model: Any,
) -> AnchorReplayState:
    """Replay fixed public actor until just before an anchor action."""

    anchor_step = anchor_step_for(row, anchor_name)
    spec = source_row_to_hook_spec(row)
    policy = ActorPolicy(model, spec.env_config)
    hidden_by_step: dict[int, torch.Tensor] = {}
    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
        policy.reset()
        while int(info.get("step", 0)) < int(anchor_step):
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
                    pair_id=pair_id,
                    side=side,
                    source_row_id=source_row_key(row),
                    source_row=row,
                    anchor_name=anchor_name,
                    anchor_step=anchor_step,
                    env=None,
                    observation=None,
                    info=info,
                    hidden=_clone_hidden(policy.hidden),
                    hidden_by_step=hidden_by_step,
                    response_action_frame=None,
                    first_failure="did_not_reach_anchor_step",
                )
        return AnchorReplayState(
            pair_id=pair_id,
            side=side,
            source_row_id=source_row_key(row),
            source_row=row,
            anchor_name=anchor_name,
            anchor_step=anchor_step,
            env=env,
            observation=np.asarray(observation, dtype=np.float32),
            info=info,
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            response_action_frame=np.asarray(observation[:12], dtype=np.float32).copy(),
        )
    except Exception as exc:
        return AnchorReplayState(
            pair_id=pair_id,
            side=side,
            source_row_id=source_row_key(row),
            source_row=row,
            anchor_name=anchor_name,
            anchor_step=anchor_step,
            env=None,
            observation=None,
            info={},
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            response_action_frame=None,
            first_failure="target_replay_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


def _success(info: Mapping[str, Any], terminal_margin: float) -> bool:
    return bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)) and terminal_margin > 0.0


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


def _hidden_for_variant(
    *,
    variant: str,
    target: AnchorReplayState,
    donor: AnchorReplayState | None,
) -> tuple[torch.Tensor | None, str]:
    if variant == "normal":
        return _clone_hidden(target.hidden), "not_applicable"
    if variant in {"zero_current_response_from_anchor", "zero_action_history_from_anchor", "donor_response_action_stream_from_anchor"}:
        return _clone_hidden(target.hidden), "not_applicable"
    if variant in {"reset_hidden_once_at_anchor", "reset_hidden_every_step_from_anchor"}:
        return None, "not_applicable"
    if variant == "delayed_hidden_8_at_anchor":
        return _clone_hidden(target.hidden_by_step.get(int(target.anchor_step) - 8)), "ok"
    if variant == "delayed_hidden_16_at_anchor":
        return _clone_hidden(target.hidden_by_step.get(int(target.anchor_step) - 16)), "ok"
    if variant in {"wrong_history_donor_hidden_at_anchor", "donor_response_action_plus_hidden_from_anchor"}:
        if donor is None or not donor.reached_anchor:
            return None, "missing_donor"
        return _clone_hidden(donor.hidden), "ok"
    raise ValueError(f"unknown variant: {variant}")


def _policy_for_variant(model: Any, row: FreshAmbiguitySourceRow, variant: str) -> ActorPolicy:
    spec = source_row_to_hook_spec(row)
    ablation = "none"
    reset_hidden_policy = "episode_persistent"
    if variant == "zero_current_response_from_anchor":
        ablation = "zero_current_response"
    elif variant == "zero_action_history_from_anchor":
        ablation = "zero_action_history"
    elif variant == "reset_hidden_every_step_from_anchor":
        reset_hidden_policy = "every_step_control"
    return ActorPolicy(model, spec.env_config, ablation=ablation, reset_hidden_policy=reset_hidden_policy)


def _inject_donor_response(observation: np.ndarray, donor: AnchorReplayState | None) -> np.ndarray:
    result = np.asarray(observation, dtype=np.float32).copy()
    if donor is not None and donor.response_action_frame is not None:
        result[:12] = donor.response_action_frame
    return result


def _failure_row(
    *,
    pair: AcceptedMeasuredPair,
    target_side: str,
    donor_side: str,
    variant: str,
    anchor_name: str,
    target: AnchorReplayState | None,
    donor_status: str,
    target_status: str,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    return {
        "pair_id": pair.pair_id,
        "target_side": target_side,
        "donor_side": donor_side,
        "anchor_name": anchor_name,
        "anchor_step": target.anchor_step if target is not None else "",
        "variant": variant,
        "target_replay_status": target_status,
        "donor_replay_status": donor_status,
        "error_type": error_type,
        "error_message": error_message,
        "first_action_steer": "",
        "first_action_throttle": "",
        "first_action_brake": "",
        "normal_first_action_l2": "",
        "terminal_margin": "",
        "normal_terminal_margin": "",
        "terminal_margin_gap_from_normal": "",
        "success": False,
        "success_drop_from_normal": False,
        "collision": False,
        "obstacle_completed": False,
        "terminal_reason": target_status,
        "continuation_steps": 0,
    }


def run_intervention_variant(
    *,
    pair: AcceptedMeasuredPair,
    target_side: str,
    target_row: FreshAmbiguitySourceRow,
    donor_side: str,
    donor_row: FreshAmbiguitySourceRow,
    anchor_name: str,
    variant: str,
    model: Any,
    continuation_steps: int = 64,
) -> dict[str, Any]:
    """Run one bounded history intervention continuation."""

    target = replay_to_anchor(pair_id=pair.pair_id, side=target_side, row=target_row, anchor_name=anchor_name, model=model)
    donor = replay_to_anchor(pair_id=pair.pair_id, side=donor_side, row=donor_row, anchor_name=anchor_name, model=model)
    if not target.reached_anchor:
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            anchor_name=anchor_name,
            target=target,
            donor_status="not_run",
            target_status=target.first_failure,
            error_type=target.error_type,
            error_message=target.error_message,
        )

    hidden, donor_status = _hidden_for_variant(variant=variant, target=target, donor=donor)
    if donor_status == "missing_donor":
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            anchor_name=anchor_name,
            target=target,
            donor_status=donor_status,
            target_status="ok",
        )
    if donor_status == "ok" and hidden is None and variant.startswith("delayed_hidden"):
        return _failure_row(
            pair=pair,
            target_side=target_side,
            donor_side=donor_side,
            variant=variant,
            anchor_name=anchor_name,
            target=target,
            donor_status="missing_delayed_hidden",
            target_status="ok",
        )

    assert target.env is not None
    assert target.observation is not None
    policy = _policy_for_variant(model, target_row, variant)
    policy.hidden = _clone_hidden(hidden)
    observation = target.observation
    if variant in {"donor_response_action_stream_from_anchor", "donor_response_action_plus_hidden_from_anchor"}:
        observation = _inject_donor_response(observation, donor)
    info = target.info
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    first_action: np.ndarray | None = None
    terminated = False
    truncated = False
    steps = 0
    for _ in range(int(continuation_steps)):
        if not np.all(np.isfinite(observation)):
            raise ValueError("nonfinite_observation")
        action = policy.act(observation, info)
        if not np.all(np.isfinite(action)):
            raise ValueError("nonfinite_action")
        if first_action is None:
            first_action = np.asarray(action, dtype=np.float64)
        observation, _, terminated, truncated, info = target.env.step(action)
        steps += 1
        margin = float(info.get("min_clearance_margin", float("nan")))
        if np.isfinite(margin):
            min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
        if terminated or truncated:
            break
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    first = first_action if first_action is not None else np.zeros(3, dtype=np.float64)
    return {
        "pair_id": pair.pair_id,
        "target_side": target_side,
        "donor_side": donor_side,
        "anchor_name": anchor_name,
        "anchor_step": target.anchor_step,
        "variant": variant,
        "target_source_family": target_row.source_family,
        "donor_source_family": donor_row.source_family,
        "target_replay_status": "ok",
        "donor_replay_status": donor_status,
        "error_type": "",
        "error_message": "",
        "first_action_steer": float(first[0]),
        "first_action_throttle": float(first[1]),
        "first_action_brake": float(first[2]),
        "normal_first_action_l2": None,
        "terminal_margin": terminal_margin,
        "normal_terminal_margin": None,
        "terminal_margin_gap_from_normal": None,
        "success": _success(info, terminal_margin),
        "success_drop_from_normal": None,
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "terminal_reason": _terminal_reason(info, bool(terminated), bool(truncated), exhausted=not (terminated or truncated)),
        "continuation_steps": steps,
    }


def _group_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return str(row.get("pair_id", "")), str(row.get("target_side", "")), str(row.get("anchor_name", ""))


def finalize_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach normal action and terminal margin comparisons."""

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
            try:
                action = np.asarray(
                    [
                        float(row.get("first_action_steer", 0.0)),
                        float(row.get("first_action_throttle", 0.0)),
                        float(row.get("first_action_brake", 0.0)),
                    ],
                    dtype=np.float64,
                )
                normal_action = np.asarray(
                    [
                        float(normal.get("first_action_steer", 0.0)),
                        float(normal.get("first_action_throttle", 0.0)),
                        float(normal.get("first_action_brake", 0.0)),
                    ],
                    dtype=np.float64,
                )
                normal_margin = float(normal.get("terminal_margin", float("nan")))
                terminal_margin = float(row.get("terminal_margin", float("nan")))
            except (TypeError, ValueError):
                finalized.append(item)
                continue
            item["normal_first_action_l2"] = float(np.linalg.norm(action - normal_action))
            item["normal_terminal_margin"] = normal_margin
            item["terminal_margin_gap_from_normal"] = normal_margin - terminal_margin
            item["success_drop_from_normal"] = bool(normal.get("success", False)) and not bool(row.get("success", False))
        finalized.append(item)
    return finalized


def build_pair_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize intervention effects by pair and target side."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row.get("pair_id", "")), str(row.get("target_side", ""))), []).append(row)
    summaries: list[dict[str, Any]] = []
    for (pair_id, target_side), group in sorted(grouped.items()):
        wrong_rows = [row for row in group if str(row.get("variant", "")).startswith("wrong_history")]
        donor_rows = [row for row in group if str(row.get("variant", "")).startswith("donor_response_action")]
        reset_zero_rows = [
            row
            for row in group
            if str(row.get("variant", "")).startswith("reset") or str(row.get("variant", "")).startswith("zero")
        ]
        summaries.append(
            {
                "pair_id": pair_id,
                "target_side": target_side,
                "variant_count": len(group),
                "wrong_history_row_count": len(wrong_rows),
                "donor_response_action_row_count": len(donor_rows),
                "reset_zero_control_row_count": len(reset_zero_rows),
                "max_wrong_history_margin_gap": max(
                    (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in wrong_rows),
                    default=0.0,
                ),
                "max_donor_response_action_margin_gap": max(
                    (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in donor_rows),
                    default=0.0,
                ),
                "max_reset_zero_margin_gap": max(
                    (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in reset_zero_rows),
                    default=0.0,
                ),
                "success_drop_count": sum(1 for row in group if bool(row.get("success_drop_from_normal", False))),
            }
        )
    return summaries


def build_variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize intervention effects by variant."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("variant", "")), []).append(row)
    result: list[dict[str, Any]] = []
    for variant, group in sorted(grouped.items()):
        result.append(
            {
                "variant": variant,
                "row_count": len(group),
                "ok_count": sum(1 for row in group if row.get("target_replay_status") == "ok"),
                "max_margin_gap_from_normal": max(
                    (float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in group),
                    default=0.0,
                ),
                "max_first_action_l2": max(
                    (float(row.get("normal_first_action_l2") or 0.0) for row in group),
                    default=0.0,
                ),
                "success_drop_count": sum(1 for row in group if bool(row.get("success_drop_from_normal", False))),
            }
        )
    return result


def _guardrail_summary() -> dict[str, bool]:
    return {key: False for key in GUARDRAIL_KEYS}


def build_summary(
    *,
    pairs: Sequence[AcceptedMeasuredPair],
    rows: Sequence[dict[str, Any]],
    pair_summary: Sequence[dict[str, Any]],
    continuation_steps: int,
) -> dict[str, Any]:
    guardrails = _guardrail_summary()
    wrong_history_rows = [row for row in rows if row.get("variant") == "wrong_history_donor_hidden_at_anchor"]
    donor_rows = [row for row in rows if str(row.get("variant", "")).startswith("donor_response_action")]
    reset_zero_rows = [
        row for row in rows if str(row.get("variant", "")).startswith("reset") or str(row.get("variant", "")).startswith("zero")
    ]
    gap_values = [
        float(row.get("terminal_margin_gap_from_normal") or 0.0)
        for row in rows
        if row.get("variant") != "normal"
    ]
    wrong_gap_values = [float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in wrong_history_rows]
    donor_gap_values = [float(row.get("terminal_margin_gap_from_normal") or 0.0) for row in donor_rows]
    return {
        "result_class": "fresh_ambiguity_history_intervention_smoke",
        "accepted_pair_count": len(pairs),
        "target_side_count": len({(row.get("pair_id"), row.get("target_side")) for row in rows}),
        "variant_count": len(VARIANTS),
        "intervention_row_count": len(rows),
        "pair_summary_row_count": len(pair_summary),
        "anchor_replay_success_count": sum(1 for row in rows if row.get("target_replay_status") == "ok"),
        "anchor_replay_failure_count": sum(1 for row in rows if row.get("target_replay_status") != "ok"),
        "wrong_history_row_count": len(wrong_history_rows),
        "donor_response_action_row_count": len(donor_rows),
        "reset_zero_control_row_count": len(reset_zero_rows),
        "max_margin_gap_from_normal": max(gap_values) if gap_values else 0.0,
        "max_wrong_history_margin_gap": max(wrong_gap_values) if wrong_gap_values else 0.0,
        "max_donor_response_action_margin_gap": max(donor_gap_values) if donor_gap_values else 0.0,
        "success_drop_count": sum(1 for row in rows if bool(row.get("success_drop_from_normal", False))),
        "continuation_steps": int(continuation_steps),
        "guardrails": guardrails,
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        "passes_public_smoke_gates": (
            len(pairs) >= 3
            and len(wrong_history_rows) >= 2
            and len(donor_rows) >= 2
            and len(reset_zero_rows) >= 2
            and sum(1 for value in guardrails.values() if bool(value)) == 0
        ),
        "passes_evidence_quality_targets": (
            (max(wrong_gap_values) if wrong_gap_values else 0.0) >= 0.02
            or (max(donor_gap_values) if donor_gap_values else 0.0) >= 0.02
            or any(bool(row.get("success_drop_from_normal", False)) for row in wrong_history_rows + donor_rows)
        ),
        **guardrails,
    }


def run_history_intervention_smoke(
    output_dir: Path | str,
    *,
    pair_candidates: Path | str = DEFAULT_PAIR_CANDIDATES,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    source_seed: int = DEFAULT_SOURCE_SEED,
    source_seed_count: int = 1,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded history interventions over accepted measured pairs."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pairs = load_accepted_pairs(pair_candidates)
    rows_by_trace = source_rows_by_trace_id(source_seed=source_seed, seed_count=source_seed_count)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)

    accepted_pair_rows: list[dict[str, Any]] = []
    intervention_rows: list[dict[str, Any]] = []
    anchor_replay_rows: list[dict[str, Any]] = []
    for pair in pairs:
        left_row = rows_by_trace[pair.left_trace_id]
        right_row = rows_by_trace[pair.right_trace_id]
        accepted_pair_rows.append(dict(pair.__dict__))
        for target_side, target_row, donor_side, donor_row in (
            ("left", left_row, "right", right_row),
            ("right", right_row, "left", left_row),
        ):
            anchor = "decision"
            target_state = replay_to_anchor(pair_id=pair.pair_id, side=target_side, row=target_row, anchor_name=anchor, model=model)
            donor_state = replay_to_anchor(pair_id=pair.pair_id, side=donor_side, row=donor_row, anchor_name=anchor, model=model)
            anchor_replay_rows.append(
                {
                    "pair_id": pair.pair_id,
                    "target_side": target_side,
                    "donor_side": donor_side,
                    "anchor_name": anchor,
                    "target_replay_status": "ok" if target_state.reached_anchor else target_state.first_failure,
                    "donor_replay_status": "ok" if donor_state.reached_anchor else donor_state.first_failure,
                    "target_source_family": target_row.source_family,
                    "donor_source_family": donor_row.source_family,
                }
            )
            for variant in VARIANTS:
                intervention_rows.append(
                    run_intervention_variant(
                        pair=pair,
                        target_side=target_side,
                        target_row=target_row,
                        donor_side=donor_side,
                        donor_row=donor_row,
                        anchor_name=anchor,
                        variant=variant,
                        model=model,
                        continuation_steps=continuation_steps,
                    )
                )
    finalized = finalize_rows(intervention_rows)
    pair_summary = build_pair_summary(finalized)
    variant_summary = build_variant_summary(finalized)
    guardrails = _guardrail_summary()
    summary = build_summary(
        pairs=pairs,
        rows=finalized,
        pair_summary=pair_summary,
        continuation_steps=continuation_steps,
    )

    write_csv_rows(output / "accepted_pair_rows.csv", accepted_pair_rows)
    write_csv_rows(output / "anchor_replay_rows.csv", anchor_replay_rows)
    write_csv_rows(output / "history_intervention_rows.csv", finalized)
    write_csv_rows(output / "history_intervention_pair_summary.csv", pair_summary)
    write_csv_rows(output / "history_intervention_variant_summary.csv", variant_summary)
    write_csv_rows(output / "history_intervention_guardrail_summary.csv", [guardrails])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded fresh ambiguity history interventions.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--pair-candidates", type=Path, default=DEFAULT_PAIR_CANDIDATES)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1534)
    parser.add_argument("--source-seed", type=int, default=DEFAULT_SOURCE_SEED)
    parser.add_argument("--source-seed-count", type=int, default=1)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    del args.seed
    summary = run_history_intervention_smoke(
        args.output_dir,
        pair_candidates=args.pair_candidates,
        checkpoint=args.checkpoint,
        source_seed=int(args.source_seed),
        source_seed_count=int(args.source_seed_count),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
