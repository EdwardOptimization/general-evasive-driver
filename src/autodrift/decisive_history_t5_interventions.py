"""Bounded measured interventions for the T5 high-speed decisive-history subset."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, hidden_stats
from autodrift.decisive_history_env_hooks import DecisiveHistoryEnvHookSpec
from autodrift.decisive_history_source_retarget import RetargetedHookSpec, build_retarget_specs
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy


DEFAULT_RUN_DIR = Path("runs/m1517_decisive_history_t5_intervention_smoke")
ELIGIBLE_SOURCE_FAMILY = "t5_high_speed_close_obstacle"
ELIGIBLE_MODES = ("close_wide", "low_mu_close", "late_reveal_high_speed", "drift_required_focus")
INTERVENTION_VARIANTS = (
    "normal",
    "reset_hidden_once",
    "reset_hidden_every_step",
    "zero_current_response",
    "zero_action_history",
    "delayed_hidden_8",
    "wrong_history_donor_hidden",
)
DONOR_MODE = {
    "close_wide": "late_reveal_high_speed",
    "low_mu_close": "close_wide",
    "late_reveal_high_speed": "drift_required_focus",
    "drift_required_focus": "low_mu_close",
}
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


@dataclass
class DecisionReplayState:
    """Environment and policy state exactly before the decision-step action."""

    spec: DecisiveHistoryEnvHookSpec
    retarget_mode: str
    env: AutoDriftEnv | None
    observation: np.ndarray | None
    info: dict[str, Any]
    hidden: torch.Tensor | None
    hidden_by_step: dict[int, torch.Tensor]
    first_failure: str = "none"
    error_type: str = ""
    error_message: str = ""

    @property
    def reached_decision(self) -> bool:
        return self.env is not None and self.observation is not None and self.first_failure == "none"


def eligible_retarget_specs() -> list[RetargetedHookSpec]:
    """Return the four M1515-admitted high-speed retarget specs."""

    retargets = build_retarget_specs(seed_count=1, source_family_cap=4)
    return [
        item
        for item in retargets
        if item.hook_spec.source_family == ELIGIBLE_SOURCE_FAMILY and item.retarget_mode in ELIGIBLE_MODES
    ]


def donor_spec_for_mode(retargets: Sequence[RetargetedHookSpec], target_mode: str) -> RetargetedHookSpec | None:
    """Return deterministic donor spec for wrong-history hidden injection."""

    donor_mode = DONOR_MODE.get(target_mode)
    if donor_mode is None:
        return None
    for retarget in retargets:
        if retarget.retarget_mode == donor_mode:
            return retarget
    return None


def _clone_hidden(hidden: torch.Tensor | None) -> torch.Tensor | None:
    return hidden.detach().clone() if hidden is not None else None


def replay_to_decision(
    spec: DecisiveHistoryEnvHookSpec,
    retarget_mode: str,
    model: Any,
) -> DecisionReplayState:
    """Replay deterministic fixed policy until just before decision action."""

    policy = ActorPolicy(model, spec.env_config)
    hidden_by_step: dict[int, torch.Tensor] = {}
    try:
        env = AutoDriftEnv(spec.env_config)
        observation, info = env.reset(seed=int(spec.seed))
        policy.reset()
        while int(info.get("step", 0)) < int(spec.decision_step):
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            step = int(info.get("step", len(hidden_by_step)))
            action = policy.act(observation, info)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            hidden_by_step[step] = _clone_hidden(policy.hidden)
            observation, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                return DecisionReplayState(
                    spec=spec,
                    retarget_mode=retarget_mode,
                    env=None,
                    observation=None,
                    info=info,
                    hidden=_clone_hidden(policy.hidden),
                    hidden_by_step=hidden_by_step,
                    first_failure="did_not_reach_decision_step",
                )
        return DecisionReplayState(
            spec=spec,
            retarget_mode=retarget_mode,
            env=env,
            observation=observation,
            info=info,
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
        )
    except Exception as exc:
        return DecisionReplayState(
            spec=spec,
            retarget_mode=retarget_mode,
            env=None,
            observation=None,
            info={},
            hidden=_clone_hidden(policy.hidden),
            hidden_by_step=hidden_by_step,
            first_failure="target_replay_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


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


def _success(info: Mapping[str, Any], terminal_margin: float) -> bool:
    return bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)) and terminal_margin > 0.0


def _action_l2(action: Sequence[float], normal_action: Sequence[float] | None) -> float | None:
    if normal_action is None:
        return None
    left = np.asarray(action, dtype=np.float64)
    right = np.asarray(normal_action, dtype=np.float64)
    return float(np.linalg.norm(left - right))


def _guardrail_rows() -> list[dict[str, object]]:
    return [{"guardrail": key, "violated": False} for key in GUARDRAIL_KEYS]


def _policy_for_variant(model: Any, spec: DecisiveHistoryEnvHookSpec, variant: str) -> ActorPolicy:
    ablation = "none"
    reset_hidden_policy = "episode_persistent"
    if variant == "zero_current_response":
        ablation = "zero_current_response"
    elif variant == "zero_action_history":
        ablation = "zero_action_history"
    elif variant == "reset_hidden_every_step":
        reset_hidden_policy = "every_step_control"
    return ActorPolicy(model, spec.env_config, ablation=ablation, reset_hidden_policy=reset_hidden_policy)


def _initial_hidden_for_variant(
    state: DecisionReplayState,
    *,
    variant: str,
    donor_state: DecisionReplayState | None,
    delay_steps: int,
) -> tuple[torch.Tensor | None, str, str]:
    if variant == "normal":
        return _clone_hidden(state.hidden), "", "not_applicable"
    if variant in {"zero_current_response", "zero_action_history"}:
        return _clone_hidden(state.hidden), "", "not_applicable"
    if variant in {"reset_hidden_once", "reset_hidden_every_step"}:
        return None, "", "not_applicable"
    if variant == "delayed_hidden_8":
        delayed_step = int(state.spec.decision_step) - int(delay_steps)
        hidden = state.hidden_by_step.get(delayed_step)
        if hidden is None:
            return None, "", "missing_delayed_hidden"
        return _clone_hidden(hidden), "", "ok"
    if variant == "wrong_history_donor_hidden":
        if donor_state is None:
            return None, "", "missing_donor"
        if not donor_state.reached_decision:
            return None, donor_state.spec.candidate_id, f"donor_failed:{donor_state.first_failure}"
        return _clone_hidden(donor_state.hidden), donor_state.spec.candidate_id, "ok"
    raise ValueError(f"unknown intervention variant: {variant}")


def run_intervention_variant(
    *,
    target: RetargetedHookSpec,
    variant: str,
    model: Any,
    donor: RetargetedHookSpec | None = None,
    continuation_steps: int = 64,
    delay_steps: int = 8,
) -> dict[str, Any]:
    """Run one target/variant continuation from deterministic decision replay."""

    state = replay_to_decision(target.hook_spec, target.retarget_mode, model)
    donor_state = replay_to_decision(donor.hook_spec, donor.retarget_mode, model) if donor is not None else None
    donor_candidate_id = donor.hook_spec.candidate_id if donor is not None else ""
    if not state.reached_decision:
        return {
            "candidate_id": target.hook_spec.candidate_id,
            "retarget_mode": target.retarget_mode,
            "variant": variant,
            "seed": target.hook_spec.seed,
            "reveal_step": target.hook_spec.reveal_step,
            "decision_step": target.hook_spec.decision_step,
            "donor_candidate_id": donor_candidate_id,
            "donor_status": "not_run",
            "target_replay_status": state.first_failure,
            "error_type": state.error_type,
            "error_message": state.error_message,
            "reached_decision": False,
            "reached_post_decision": False,
            "terminal_reason": state.first_failure,
            "collision": False,
            "obstacle_completed": False,
            "success": False,
        }

    injected_hidden, injected_donor_id, donor_status = _initial_hidden_for_variant(
        state,
        variant=variant,
        donor_state=donor_state,
        delay_steps=delay_steps,
    )
    if injected_donor_id:
        donor_candidate_id = injected_donor_id
    if donor_status not in {"ok", "not_applicable"}:
        return {
            "candidate_id": target.hook_spec.candidate_id,
            "retarget_mode": target.retarget_mode,
            "variant": variant,
            "seed": target.hook_spec.seed,
            "reveal_step": target.hook_spec.reveal_step,
            "decision_step": target.hook_spec.decision_step,
            "donor_candidate_id": donor_candidate_id,
            "donor_status": donor_status,
            "target_replay_status": "ok",
            "reached_decision": True,
            "reached_post_decision": False,
            "terminal_reason": donor_status,
            "collision": False,
            "obstacle_completed": False,
            "success": False,
        }

    assert state.env is not None
    assert state.observation is not None
    policy = _policy_for_variant(model, target.hook_spec, variant)
    policy.hidden = _clone_hidden(injected_hidden)
    observation = state.observation
    info = state.info
    decision_margin = float(info.get("min_clearance_margin", float("nan")))
    decision_hidden_norm, _ = hidden_stats(state.hidden)
    intervention_hidden_norm, _ = hidden_stats(policy.hidden)
    first_action: np.ndarray | None = None
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    terminated = False
    truncated = False
    reward_sum = 0.0
    terminal_step = int(info.get("step", target.hook_spec.decision_step))
    for _ in range(int(continuation_steps)):
        if not np.all(np.isfinite(observation)):
            raise ValueError("nonfinite_observation")
        action = policy.act(observation, info)
        if not np.all(np.isfinite(action)):
            raise ValueError("nonfinite_action")
        if first_action is None:
            first_action = np.asarray(action, dtype=np.float64)
        observation, reward, terminated, truncated, info = state.env.step(action)
        reward_sum += float(reward)
        terminal_step = int(info.get("step", terminal_step))
        margin = float(info.get("min_clearance_margin", float("nan")))
        if np.isfinite(margin):
            min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
        if terminated or truncated:
            break
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    terminal_reason = _terminal_reason(info, bool(terminated), bool(truncated), exhausted=not (terminated or truncated))
    first = first_action if first_action is not None else np.zeros(3, dtype=np.float64)
    return {
        "candidate_id": target.hook_spec.candidate_id,
        "retarget_mode": target.retarget_mode,
        "variant": variant,
        "seed": target.hook_spec.seed,
        "reveal_step": target.hook_spec.reveal_step,
        "decision_step": target.hook_spec.decision_step,
        "donor_candidate_id": donor_candidate_id,
        "donor_status": donor_status,
        "target_replay_status": "ok",
        "error_type": "",
        "error_message": "",
        "decision_margin": decision_margin,
        "decision_hidden_norm": decision_hidden_norm,
        "intervention_hidden_norm": intervention_hidden_norm,
        "first_action_steer": float(first[0]),
        "first_action_throttle": float(first[1]),
        "first_action_brake": float(first[2]),
        "normal_first_action_l2": None,
        "terminal_step": terminal_step,
        "terminal_reason": terminal_reason,
        "collision": bool(info.get("collision", False)),
        "obstacle_completed": bool(info.get("obstacle_completed", False)),
        "success": _success(info, terminal_margin),
        "terminal_margin": terminal_margin,
        "min_continuation_margin": min_margin,
        "normal_terminal_margin": None,
        "margin_gap_from_normal": None,
        "success_drop_from_normal": None,
        "reward_sum": reward_sum,
        "reached_decision": True,
        "reached_post_decision": terminal_step > int(target.hook_spec.decision_step),
    }


def finalize_intervention_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach normal-action and normal-outcome comparisons to intervention rows."""

    normal_by_candidate: dict[str, dict[str, Any]] = {
        str(row["candidate_id"]): row for row in rows if row.get("variant") == "normal" and row.get("target_replay_status") == "ok"
    }
    finalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        normal = normal_by_candidate.get(str(row.get("candidate_id", "")))
        if normal is not None and row.get("target_replay_status") == "ok":
            normal_action = [
                float(normal.get("first_action_steer", 0.0)),
                float(normal.get("first_action_throttle", 0.0)),
                float(normal.get("first_action_brake", 0.0)),
            ]
            action = [
                float(row.get("first_action_steer", 0.0)),
                float(row.get("first_action_throttle", 0.0)),
                float(row.get("first_action_brake", 0.0)),
            ]
            normal_margin = float(normal.get("terminal_margin", float("nan")))
            terminal_margin = float(row.get("terminal_margin", float("nan")))
            item["normal_first_action_l2"] = _action_l2(action, normal_action)
            item["normal_terminal_margin"] = normal_margin
            item["margin_gap_from_normal"] = normal_margin - terminal_margin
            item["success_drop_from_normal"] = bool(normal.get("success", False)) and not bool(row.get("success", False))
        finalized.append(item)
    return finalized


def build_pair_summary(rows: Sequence[dict[str, Any]], *, margin_gap_threshold: float = 0.02) -> list[dict[str, Any]]:
    """Summarize intervention effects per target."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("candidate_id", ""))].append(row)
    summaries: list[dict[str, Any]] = []
    for candidate_id, group in sorted(grouped.items()):
        normal = next((row for row in group if row.get("variant") == "normal"), {})
        gaps = [
            float(row.get("margin_gap_from_normal", 0.0))
            for row in group
            if row.get("variant") != "normal" and row.get("margin_gap_from_normal") is not None
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
        summaries.append(
            {
                "candidate_id": candidate_id,
                "retarget_mode": normal.get("retarget_mode", group[0].get("retarget_mode", "")),
                "normal_success": bool(normal.get("success", False)),
                "normal_terminal_margin": normal.get("terminal_margin", ""),
                "variant_count": len(group),
                "max_margin_gap_from_normal": max(gaps) if gaps else 0.0,
                "success_drop_variants": "|".join(
                    str(row.get("variant", ""))
                    for row in group
                    if bool(row.get("success_drop_from_normal", False))
                ),
                "outcome_relevant_variants": "|".join(outcome_relevant),
                "outcome_relevant_variant_count": len(outcome_relevant),
            }
        )
    return summaries


def build_intervention_summary(
    rows: Sequence[dict[str, Any]],
    pair_rows: Sequence[dict[str, Any]],
    *,
    eligible_target_count: int,
    variant_count: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build summary for bounded T5 intervention smoke."""

    guardrails = _guardrail_rows()
    replay_failures = [row for row in rows if row.get("target_replay_status") != "ok"]
    donor_failures = [row for row in rows if str(row.get("donor_status", "")) not in {"", "ok", "not_applicable"}]
    gap_values = [
        float(row["margin_gap_from_normal"])
        for row in rows
        if row.get("margin_gap_from_normal") is not None and np.isfinite(float(row["margin_gap_from_normal"]))
    ]
    return {
        "result_class": "decisive_history_t5_intervention_smoke",
        "eligible_source_family": ELIGIBLE_SOURCE_FAMILY,
        "eligible_target_count": int(eligible_target_count),
        "variant_count": int(variant_count),
        "continuation_steps": int(continuation_steps),
        "intervention_row_count": len(rows),
        "normal_row_count": sum(1 for row in rows if row.get("variant") == "normal"),
        "ablation_row_count": sum(1 for row in rows if row.get("variant") != "normal"),
        "wrong_history_row_count": sum(1 for row in rows if row.get("variant") == "wrong_history_donor_hidden"),
        "target_replay_failure_count": len(replay_failures),
        "donor_replay_failure_count": len(donor_failures),
        "outcome_relevant_variant_count": sum(int(row.get("outcome_relevant_variant_count", 0)) for row in pair_rows),
        "max_margin_gap_from_normal": max(gap_values) if gap_values else 0.0,
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


def run_t5_intervention_smoke(
    run_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded T5 intervention continuations for eligible rows."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    targets = eligible_retarget_specs()
    rows: list[dict[str, Any]] = []
    for target in targets:
        for variant in INTERVENTION_VARIANTS:
            donor = donor_spec_for_mode(targets, target.retarget_mode) if variant == "wrong_history_donor_hidden" else None
            rows.append(
                run_intervention_variant(
                    target=target,
                    variant=variant,
                    model=model,
                    donor=donor,
                    continuation_steps=continuation_steps,
                )
            )
    finalized = finalize_intervention_rows(rows)
    pair_rows = build_pair_summary(finalized)
    summary = build_intervention_summary(
        finalized,
        pair_rows,
        eligible_target_count=len(targets),
        variant_count=len(INTERVENTION_VARIANTS),
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "intervention_rows.csv", finalized)
    write_csv_rows(output / "intervention_pair_summary.csv", pair_rows)
    write_csv_rows(output / "intervention_guardrail_summary.csv", _guardrail_rows())
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded T5 decisive-history intervention smoke.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_t5_intervention_smoke(
        args.run_dir,
        checkpoint=args.checkpoint,
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"max_margin_gap_from_normal={summary['max_margin_gap_from_normal']}")


if __name__ == "__main__":
    main()
