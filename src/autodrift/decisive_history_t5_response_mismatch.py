"""Response/action-history mismatch diagnostics for T5 timing probes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.decisive_history_t5_interventions import (
    ELIGIBLE_SOURCE_FAMILY,
    GUARDRAIL_KEYS,
    _clone_hidden,
    _guardrail_rows,
    _success,
    donor_spec_for_mode,
    eligible_retarget_specs,
)
from autodrift.decisive_history_t5_timing_interventions import (
    STATE_DELTA_FIELDS,
    _prefixed_state,
    _state_values,
    _terminal_reason,
    anchor_step_for,
    build_anchor_summary,
    build_timing_pair_summary,
    finalize_timing_rows,
    replay_to_anchor,
)
from autodrift.decisive_history_source_retarget import RetargetedHookSpec
from autodrift.evaluate import ActorPolicy


DEFAULT_RUN_DIR = Path("runs/m1524_t5_response_mismatch_intervention_smoke")
RESPONSE_MISMATCH_ANCHORS = ("reveal", "decision_minus_8", "decision")
RESPONSE_MISMATCH_VARIANTS = (
    "normal",
    "donor_response_current_frame_at_anchor",
    "donor_ego_response_stream_from_anchor",
    "donor_action_history_stream_from_anchor",
    "donor_response_action_stream_from_anchor",
    "donor_response_action_plus_hidden_from_anchor",
    "zero_current_response_from_anchor",
)
RESPONSE_SLICE = slice(0, 12)
EGO_RESPONSE_SLICE = slice(0, 9)
ACTION_HISTORY_SLICE = slice(9, 12)


@dataclass
class DonorObservationStream:
    """Donor observations replayed from an anchor under the fixed policy."""

    status: str
    candidate_id: str
    frames: list[np.ndarray]
    hidden: Any
    exhausted_after_index: int | None = None
    error_type: str = ""
    error_message: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok" and bool(self.frames)


def collect_donor_observation_stream(
    donor: RetargetedHookSpec,
    *,
    anchor_name: str,
    model: Any,
    continuation_steps: int,
) -> DonorObservationStream:
    """Collect donor observations from anchor onward without mutating target state."""

    state = replay_to_anchor(donor.hook_spec, donor.retarget_mode, anchor_name, model)
    if not state.reached_anchor:
        return DonorObservationStream(
            status=state.first_failure,
            candidate_id=donor.hook_spec.candidate_id,
            frames=[],
            hidden=_clone_hidden(state.hidden),
            error_type=state.error_type,
            error_message=state.error_message,
        )
    assert state.env is not None
    assert state.observation is not None
    policy = ActorPolicy(model, donor.hook_spec.env_config)
    policy.hidden = _clone_hidden(state.hidden)
    observation = state.observation
    info = state.info
    frames: list[np.ndarray] = []
    exhausted_after_index: int | None = None
    for index in range(int(continuation_steps) + 1):
        frames.append(np.asarray(observation, dtype=np.float32).copy())
        action = policy.act(observation, info)
        observation, _, terminated, truncated, info = state.env.step(action)
        if terminated or truncated:
            exhausted_after_index = index
            break
    return DonorObservationStream(
        status="ok",
        candidate_id=donor.hook_spec.candidate_id,
        frames=frames,
        hidden=_clone_hidden(state.hidden),
        exhausted_after_index=exhausted_after_index,
    )


def donor_frame_at(stream: DonorObservationStream, relative_step: int) -> tuple[np.ndarray | None, bool]:
    """Return donor frame for a relative step and whether the stream was exhausted."""

    if not stream.frames:
        return None, False
    index = max(0, int(relative_step))
    exhausted = index >= len(stream.frames)
    return stream.frames[min(index, len(stream.frames) - 1)], exhausted


def apply_response_mismatch(
    observation: np.ndarray,
    donor_observation: np.ndarray | None,
    *,
    variant: str,
    relative_step: int,
) -> np.ndarray:
    """Apply diagnostic response/action-history observation surgery."""

    transformed = np.asarray(observation, dtype=np.float32).copy()
    if variant == "normal":
        return transformed
    if variant == "zero_current_response_from_anchor":
        transformed[RESPONSE_SLICE] = 0.0
        return transformed
    if donor_observation is None:
        return transformed
    donor = np.asarray(donor_observation, dtype=np.float32)
    if variant == "donor_response_current_frame_at_anchor":
        if int(relative_step) == 0:
            transformed[RESPONSE_SLICE] = donor[RESPONSE_SLICE]
        return transformed
    if variant == "donor_ego_response_stream_from_anchor":
        transformed[EGO_RESPONSE_SLICE] = donor[EGO_RESPONSE_SLICE]
        return transformed
    if variant == "donor_action_history_stream_from_anchor":
        transformed[ACTION_HISTORY_SLICE] = donor[ACTION_HISTORY_SLICE]
        return transformed
    if variant in {
        "donor_response_action_stream_from_anchor",
        "donor_response_action_plus_hidden_from_anchor",
    }:
        transformed[RESPONSE_SLICE] = donor[RESPONSE_SLICE]
        return transformed
    raise ValueError(f"unknown response mismatch variant: {variant}")


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


def _l2(left: np.ndarray, right: np.ndarray, part: slice) -> float:
    return float(np.linalg.norm(np.asarray(left[part], dtype=np.float64) - np.asarray(right[part], dtype=np.float64)))


def run_response_mismatch_variant(
    *,
    target: RetargetedHookSpec,
    anchor_name: str,
    variant: str,
    model: Any,
    donor: RetargetedHookSpec | None = None,
    continuation_steps: int = 64,
) -> dict[str, Any]:
    """Run one response/action-history mismatch diagnostic."""

    state = replay_to_anchor(target.hook_spec, target.retarget_mode, anchor_name, model)
    donor_stream = (
        collect_donor_observation_stream(
            donor,
            anchor_name=anchor_name,
            model=model,
            continuation_steps=continuation_steps,
        )
        if donor is not None
        else DonorObservationStream(status="not_applicable", candidate_id="", frames=[], hidden=None)
    )
    donor_candidate_id = donor.hook_spec.candidate_id if donor is not None else ""
    if not state.reached_anchor:
        return _failure_row(
            target=target,
            anchor_name=anchor_name,
            anchor_step=anchor_step_for(target.hook_spec, anchor_name),
            variant=variant,
            donor_candidate_id=donor_candidate_id,
            donor_status=donor_stream.status,
            target_replay_status=state.first_failure,
            error_type=state.error_type,
            error_message=state.error_message,
        )
    if variant.startswith("donor_") and not donor_stream.ok:
        return _failure_row(
            target=target,
            anchor_name=anchor_name,
            anchor_step=state.anchor_step,
            variant=variant,
            donor_candidate_id=donor_candidate_id,
            donor_status=donor_stream.status,
            target_replay_status="ok",
            error_type=donor_stream.error_type,
            error_message=donor_stream.error_message,
        )

    assert state.env is not None
    assert state.observation is not None
    policy = ActorPolicy(model, target.hook_spec.env_config)
    if variant == "donor_response_action_plus_hidden_from_anchor":
        policy.hidden = _clone_hidden(donor_stream.hidden)
    else:
        policy.hidden = _clone_hidden(state.hidden)
    observation = state.observation
    info = state.info
    anchor_state = _state_values(state.env)
    first_action: np.ndarray | None = None
    decision_action: np.ndarray | None = None
    decision_state: dict[str, float | None] | None = None
    response_l2_values: list[float] = []
    action_history_l2_values: list[float] = []
    donor_exhausted = False
    anchor_response_l2 = 0.0
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
        relative_step = step_before_action - int(state.anchor_step)
        donor_frame, exhausted = donor_frame_at(donor_stream, relative_step)
        donor_exhausted = donor_exhausted or exhausted
        if donor_frame is not None:
            response_l2 = _l2(observation, donor_frame, RESPONSE_SLICE)
            action_history_l2 = _l2(observation, donor_frame, ACTION_HISTORY_SLICE)
            response_l2_values.append(response_l2)
            action_history_l2_values.append(action_history_l2)
            if relative_step == 0:
                anchor_response_l2 = response_l2
        diagnostic_observation = apply_response_mismatch(
            observation,
            donor_frame,
            variant=variant,
            relative_step=relative_step,
        )
        if step_before_action == int(target.hook_spec.decision_step) and decision_state is None:
            decision_state = _state_values(state.env)
        action = policy.act(diagnostic_observation, info)
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
        "donor_status": donor_stream.status,
        "target_replay_status": "ok",
        "donor_exhausted": donor_exhausted,
        "error_type": "",
        "error_message": "",
        "anchor_margin": float(state.info.get("min_clearance_margin", float("nan"))),
        "donor_response_l2_at_anchor": anchor_response_l2,
        "donor_response_l2_mean": float(np.mean(response_l2_values)) if response_l2_values else 0.0,
        "donor_action_history_l2_mean": float(np.mean(action_history_l2_values)) if action_history_l2_values else 0.0,
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


def build_variant_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize response-mismatch effects by variant."""

    summaries: list[dict[str, Any]] = []
    for variant in sorted({str(row.get("variant", "")) for row in rows}):
        group = [row for row in rows if row.get("variant") == variant]
        gaps = [
            float(row.get("margin_gap_from_normal", 0.0))
            for row in group
            if row.get("margin_gap_from_normal") is not None
        ]
        action_l2s = [
            float(row.get("normal_first_action_l2", 0.0))
            for row in group
            if row.get("normal_first_action_l2") is not None
        ]
        donor_l2s = [
            float(row.get("donor_response_l2_mean", 0.0))
            for row in group
            if row.get("donor_response_l2_mean") is not None
        ]
        summaries.append(
            {
                "variant": variant,
                "row_count": len(group),
                "max_margin_gap_from_normal": max(gaps) if gaps else 0.0,
                "max_first_action_l2": max(action_l2s) if action_l2s else 0.0,
                "mean_donor_response_l2": float(np.mean(donor_l2s)) if donor_l2s else 0.0,
                "success_drop_count": sum(1 for row in group if bool(row.get("success_drop_from_normal", False))),
            }
        )
    return summaries


def build_response_mismatch_summary(
    rows: Sequence[dict[str, Any]],
    pair_rows: Sequence[dict[str, Any]],
    anchor_rows: Sequence[dict[str, Any]],
    variant_rows: Sequence[dict[str, Any]],
    *,
    eligible_target_count: int,
    anchor_count: int,
    variant_count: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build summary for response/action-history mismatch smoke."""

    guardrails = _guardrail_rows()
    replay_failures = [row for row in rows if row.get("target_replay_status") != "ok"]
    donor_failures = [row for row in rows if str(row.get("donor_status", "")) not in {"", "ok", "not_applicable"}]
    gap_values = [
        float(row["margin_gap_from_normal"])
        for row in rows
        if row.get("margin_gap_from_normal") is not None and np.isfinite(float(row["margin_gap_from_normal"]))
    ]
    action_values = [
        float(row["normal_first_action_l2"])
        for row in rows
        if row.get("normal_first_action_l2") is not None and np.isfinite(float(row["normal_first_action_l2"]))
    ]
    donor_response_values = [
        float(row["donor_response_l2_mean"])
        for row in rows
        if row.get("donor_response_l2_mean") is not None and np.isfinite(float(row["donor_response_l2_mean"]))
    ]
    return {
        "result_class": "t5_response_mismatch_intervention_smoke",
        "eligible_source_family": ELIGIBLE_SOURCE_FAMILY,
        "eligible_target_count": int(eligible_target_count),
        "anchor_count": int(anchor_count),
        "variant_count": int(variant_count),
        "continuation_steps": int(continuation_steps),
        "intervention_row_count": len(rows),
        "pair_row_count": len(pair_rows),
        "anchor_row_count": len(anchor_rows),
        "variant_row_count": len(variant_rows),
        "normal_row_count": sum(1 for row in rows if row.get("variant") == "normal"),
        "mismatch_row_count": sum(1 for row in rows if row.get("variant") != "normal"),
        "target_replay_failure_count": len(replay_failures),
        "donor_replay_failure_count": len(donor_failures),
        "outcome_relevant_variant_count": sum(int(row.get("outcome_relevant_variant_count", 0)) for row in pair_rows),
        "divergence_relevant_variant_count": sum(
            int(row.get("divergence_relevant_variant_count", 0)) for row in pair_rows
        ),
        "max_margin_gap_from_normal": max(gap_values) if gap_values else 0.0,
        "max_first_action_l2": max(action_values) if action_values else 0.0,
        "max_donor_response_l2_mean": max(donor_response_values) if donor_response_values else 0.0,
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


def run_response_mismatch_smoke(
    run_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    continuation_steps: int = 64,
    anchors: Sequence[str] = RESPONSE_MISMATCH_ANCHORS,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run response/action-history mismatch diagnostics."""

    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    targets = eligible_retarget_specs()
    rows: list[dict[str, Any]] = []
    for target in targets:
        for anchor_name in anchors:
            for variant in RESPONSE_MISMATCH_VARIANTS:
                donor = donor_spec_for_mode(targets, target.retarget_mode) if variant.startswith("donor_") else None
                rows.append(
                    run_response_mismatch_variant(
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
    variant_rows = build_variant_summary(finalized)
    summary = build_response_mismatch_summary(
        finalized,
        pair_rows,
        anchor_rows,
        variant_rows,
        eligible_target_count=len(targets),
        anchor_count=len(anchors),
        variant_count=len(RESPONSE_MISMATCH_VARIANTS),
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "response_mismatch_rows.csv", finalized)
    write_csv_rows(output / "response_mismatch_pair_summary.csv", pair_rows)
    write_csv_rows(output / "response_mismatch_anchor_summary.csv", anchor_rows)
    write_csv_rows(output / "response_mismatch_variant_summary.csv", variant_rows)
    write_csv_rows(output / "response_mismatch_guardrail_summary.csv", _guardrail_rows())
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run T5 response/action-history mismatch smoke.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--anchors", nargs="+", choices=RESPONSE_MISMATCH_ANCHORS, default=list(RESPONSE_MISMATCH_ANCHORS))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_response_mismatch_smoke(
        args.run_dir,
        checkpoint=args.checkpoint,
        continuation_steps=int(args.continuation_steps),
        anchors=tuple(args.anchors),
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"intervention_row_count={summary['intervention_row_count']}")
    print(f"max_margin_gap_from_normal={summary['max_margin_gap_from_normal']}")
    print(f"max_donor_response_l2_mean={summary['max_donor_response_l2_mean']}")


if __name__ == "__main__":
    main()
