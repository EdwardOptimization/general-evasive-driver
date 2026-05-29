"""No-training recoverable active-set source generator."""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_pair_expansion_planner import expanded_terminal_source_rows
from autodrift.calibrated_terminal_boundary_history_interventions import AnchorReplayState, replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, hidden_stats, phase_for_step
from autodrift.decisive_history_t5_interventions import _clone_hidden
from autodrift.evaluate import ActorPolicy
from autodrift.temporal_active_set_anchor_sensitivity_miner import AnchorCandidate, ContinuationResult, _asdict_rows, _finite_float
from autodrift.terminal_boundary_task_sampling_calibration import CalibrationSpec, build_calibration_specs


DEFAULT_RUN_DIR = Path("runs/m1560_recoverable_active_set_generator_smoke")
ANCHOR_WINDOWS = (
    "reveal",
    "reveal_plus_4",
    "decision_minus_24",
    "decision_minus_16",
    "decision_minus_8",
    "decision",
)
PREDECISION_WINDOWS = {"reveal", "reveal_plus_4", "decision_minus_24", "decision_minus_16", "decision_minus_8"}
HOLD_STEPS = (1, 4, 8, 12)
LOCAL_OVERRIDES = (
    "steer_left",
    "steer_right",
    "brake_more",
    "brake_less",
    "throttle_release",
    "steer_left_brake_more",
    "steer_right_brake_more",
    "steer_left_brake_less",
    "steer_right_brake_less",
)
MARGIN_GAP_THRESHOLD = 0.02
STRONG_MARGIN_GAP_THRESHOLD = 0.05
RECOVERABLE_MARGIN_ABS_MAX = 0.50
STRONG_MARGIN_ABS_MAX = 0.25
HIGH_MARGIN_SAFE_MIN = 0.50
GUARDRAILS = {
    "candidate_materialized": False,
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "training_corpus_exported": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def _max_share(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return max((count / max(1, total) for count in counts.values()), default=0.0)


def _success(info: Mapping[str, Any], terminal_margin: float) -> bool:
    return bool(info.get("obstacle_completed", False)) and not bool(info.get("collision", False)) and terminal_margin > 0.0


def _continuation_reason(info: Mapping[str, Any], *, terminated: bool, truncated: bool, exhausted: bool) -> str:
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


def source_specs(*, seed: int, seed_count: int, max_source_specs: int) -> list[CalibrationSpec]:
    """Build bounded public source specs for recoverable active-set mining."""

    base_rows = max(1, int(np.ceil(max_source_specs / 10.0)))
    rows = expanded_terminal_source_rows(seed=seed, seed_count=seed_count, max_base_rows=base_rows)
    return build_calibration_specs(rows, max_calibration_specs=max_source_specs)


def anchor_step_for_window(spec: CalibrationSpec, window: str) -> int:
    """Map recoverable active-set anchor windows to simulator steps."""

    hook = spec.hook_spec
    reveal = int(hook.reveal_step)
    decision = int(hook.decision_step)
    max_step = max(0, int(hook.env_config.max_steps) - 1)
    if window == "reveal":
        step = reveal
    elif window == "reveal_plus_4":
        step = reveal + 4
    elif window == "decision_minus_24":
        step = decision - 24
    elif window == "decision_minus_16":
        step = decision - 16
    elif window == "decision_minus_8":
        step = decision - 8
    elif window == "decision":
        step = decision
    else:
        raise ValueError(f"unknown anchor window: {window}")
    return int(min(max(step, 0), max_step))


def build_anchor_candidates(
    specs: Sequence[CalibrationSpec],
    *,
    max_anchors: int,
    windows: Sequence[str] = ANCHOR_WINDOWS,
) -> list[AnchorCandidate]:
    """Select source-family balanced anchors with duplicate step suppression."""

    grouped: dict[str, list[AnchorCandidate]] = defaultdict(list)
    for spec in specs:
        artifact = spec.artifact_row
        seen_steps: set[int] = set()
        for window in windows:
            step = anchor_step_for_window(spec, window)
            if step in seen_steps:
                continue
            seen_steps.add(step)
            grouped[str(artifact.source_family)].append(
                AnchorCandidate(
                    anchor_id=f"{artifact.calibration_id}|{window}|{step}",
                    calibration_id=str(artifact.calibration_id),
                    source_row_id=str(artifact.source_row_id),
                    source_family=str(artifact.source_family),
                    task_family=str(artifact.task_family),
                    seed=int(artifact.seed),
                    mode_name=str(artifact.mode_name),
                    anchor_window=str(window),
                    anchor_step=int(step),
                    reveal_step=int(artifact.reveal_step),
                    decision_step=int(artifact.decision_step),
                    phase=phase_for_step(int(step), int(artifact.reveal_step), int(artifact.decision_step)),
                    base_distance_min=float(artifact.base_distance_min),
                    base_distance_max=float(artifact.base_distance_max),
                    retarget_distance_min=float(artifact.retarget_distance_min),
                    retarget_distance_max=float(artifact.retarget_distance_max),
                )
            )

    selected: list[AnchorCandidate] = []
    families = sorted(grouped)
    while families and len(selected) < int(max_anchors):
        progressed = False
        for family in list(families):
            rows = grouped[family]
            if not rows:
                families.remove(family)
                continue
            selected.append(rows.pop(0))
            progressed = True
            if len(selected) >= int(max_anchors):
                break
        if not progressed:
            break
    return selected


def apply_local_override(action: Sequence[float], override: str, *, steer_delta: float = 0.25, brake_delta: float = 0.35) -> np.ndarray:
    """Apply one local override to the actor action vector."""

    result = np.asarray(action, dtype=np.float64).copy()
    if result.shape != (3,):
        raise ValueError(f"expected action shape (3,), got {result.shape}")
    if override == "steer_left":
        result[0] += steer_delta
    elif override == "steer_right":
        result[0] -= steer_delta
    elif override == "brake_more":
        result[2] += brake_delta
    elif override == "brake_less":
        result[2] -= brake_delta
    elif override == "throttle_release":
        result[1] = -1.0
    elif override == "steer_left_brake_more":
        result[0] += steer_delta
        result[2] += brake_delta
    elif override == "steer_right_brake_more":
        result[0] -= steer_delta
        result[2] += brake_delta
    elif override == "steer_left_brake_less":
        result[0] += steer_delta
        result[2] -= brake_delta
    elif override == "steer_right_brake_less":
        result[0] -= steer_delta
        result[2] -= brake_delta
    else:
        raise ValueError(f"unknown local override: {override}")
    return np.clip(result, -1.0, 1.0).astype(np.float32)


def run_hold_continuation(
    *,
    replay: AnchorReplayState,
    spec: CalibrationSpec,
    model: Any,
    continuation_steps: int,
    override: str | None = None,
    hold_steps: int = 0,
    override_fn: Any = apply_local_override,
) -> ContinuationResult:
    """Continue from a replay anchor, optionally holding a local override."""

    if not replay.reached_anchor:
        return ContinuationResult(
            replay_status=str(replay.first_failure),
            terminal_margin=float("nan"),
            success=False,
            collision=False,
            obstacle_completed=False,
            terminal_reason=str(replay.first_failure),
            first_action=(float("nan"), float("nan"), float("nan")),
            executed_first_action=(float("nan"), float("nan"), float("nan")),
            hidden_norm=0.0,
            hidden_checksum=0.0,
            continuation_steps=0,
            error_type=str(replay.error_type),
            error_message=str(replay.error_message),
        )
    assert replay.env is not None
    assert replay.observation is not None
    env = copy.deepcopy(replay.env)
    policy = ActorPolicy(model, spec.hook_spec.env_config)
    policy.hidden = _clone_hidden(replay.hidden)
    observation = np.asarray(replay.observation, dtype=np.float32).copy()
    info = dict(replay.info)
    hidden_norm, hidden_checksum = hidden_stats(policy.hidden)
    min_margin = float(info.get("min_clearance_margin", float("nan")))
    first_action = np.full(3, np.nan, dtype=np.float64)
    executed_first_action = np.full(3, np.nan, dtype=np.float64)
    terminated = False
    truncated = False
    steps = 0
    try:
        for step_index in range(int(continuation_steps)):
            if not np.all(np.isfinite(observation)):
                raise ValueError("nonfinite_observation")
            action = np.asarray(policy.act(observation, info), dtype=np.float64)
            if not np.all(np.isfinite(action)):
                raise ValueError("nonfinite_action")
            if step_index == 0:
                first_action = action.copy()
            if override is not None and step_index < int(hold_steps):
                executed = override_fn(action, override)
            else:
                executed = action
            if step_index == 0:
                executed_first_action = np.asarray(executed, dtype=np.float64)
            observation, _, terminated, truncated, info = env.step(executed)
            steps += 1
            margin = float(info.get("min_clearance_margin", float("nan")))
            if np.isfinite(margin):
                min_margin = min(min_margin, margin) if np.isfinite(min_margin) else margin
            if terminated or truncated:
                break
    except Exception as exc:
        return ContinuationResult(
            replay_status="continuation_exception",
            terminal_margin=float("nan"),
            success=False,
            collision=False,
            obstacle_completed=False,
            terminal_reason="continuation_exception",
            first_action=tuple(float(value) for value in first_action),
            executed_first_action=tuple(float(value) for value in executed_first_action),
            hidden_norm=float(hidden_norm),
            hidden_checksum=float(hidden_checksum),
            continuation_steps=steps,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    terminal_margin = float(info.get("min_clearance_margin", min_margin))
    return ContinuationResult(
        replay_status="ok",
        terminal_margin=terminal_margin,
        success=_success(info, terminal_margin),
        collision=bool(info.get("collision", False)),
        obstacle_completed=bool(info.get("obstacle_completed", False)),
        terminal_reason=_continuation_reason(info, terminated=bool(terminated), truncated=bool(truncated), exhausted=not (terminated or truncated)),
        first_action=tuple(float(value) for value in first_action),
        executed_first_action=tuple(float(value) for value in executed_first_action),
        hidden_norm=float(hidden_norm),
        hidden_checksum=float(hidden_checksum),
        continuation_steps=steps,
    )


def anchor_result_row(candidate: AnchorCandidate, normal: ContinuationResult) -> dict[str, Any]:
    """Flatten normal anchor result."""

    row = asdict(candidate)
    row.update(
        {
            "normal_replay_status": normal.replay_status,
            "normal_terminal_margin": normal.terminal_margin,
            "normal_success": normal.success,
            "normal_collision": normal.collision,
            "normal_obstacle_completed": normal.obstacle_completed,
            "normal_terminal_reason": normal.terminal_reason,
            "baseline_action_steer": normal.first_action[0],
            "baseline_action_throttle": normal.first_action[1],
            "baseline_action_brake": normal.first_action[2],
            "hidden_norm": normal.hidden_norm,
            "hidden_checksum": normal.hidden_checksum,
            "continuation_steps": normal.continuation_steps,
            "error_type": normal.error_type,
            "error_message": normal.error_message,
        }
    )
    return row


def local_hold_row(
    candidate: AnchorCandidate,
    normal: ContinuationResult,
    *,
    override: str,
    hold_steps: int,
    result: ContinuationResult,
) -> dict[str, Any]:
    """Flatten one local hold continuation result."""

    signed_gap = float("nan")
    abs_gap = float("nan")
    if np.isfinite(normal.terminal_margin) and np.isfinite(result.terminal_margin):
        signed_gap = float(normal.terminal_margin - result.terminal_margin)
        abs_gap = abs(signed_gap)
    row = asdict(candidate)
    row.update(
        {
            "override": override,
            "hold_steps": int(hold_steps),
            "replay_status": result.replay_status,
            "normal_terminal_margin": normal.terminal_margin,
            "hold_terminal_margin": result.terminal_margin,
            "signed_terminal_margin_gap_from_normal": signed_gap,
            "abs_terminal_margin_gap_from_normal": abs_gap,
            "normal_success": normal.success,
            "hold_success": result.success,
            "success_flip": bool(result.success != normal.success),
            "normal_collision": normal.collision,
            "hold_collision": result.collision,
            "collision_flip": bool(result.collision != normal.collision),
            "normal_terminal_reason": normal.terminal_reason,
            "hold_terminal_reason": result.terminal_reason,
            "baseline_action_steer": normal.first_action[0],
            "baseline_action_throttle": normal.first_action[1],
            "baseline_action_brake": normal.first_action[2],
            "hold_first_action_steer": result.executed_first_action[0],
            "hold_first_action_throttle": result.executed_first_action[1],
            "hold_first_action_brake": result.executed_first_action[2],
            "continuation_steps": result.continuation_steps,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }
    )
    return row


def classify_anchor(anchor: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Classify one anchor into recoverability triage labels."""

    if str(anchor.get("normal_replay_status", "")) != "ok":
        return {
            "triage_label": "replay_failed",
            "recoverable_boundary": False,
            "strong_recoverable_boundary": False,
            "max_abs_terminal_margin_gap": 0.0,
            "success_flip_count": 0,
            "collision_flip_count": 0,
            "best_override": "",
            "best_hold_steps": 0,
        }
    valid = [row for row in rows if str(row.get("replay_status", "")) == "ok"]
    max_gap = max((_finite_float(row.get("abs_terminal_margin_gap_from_normal")) for row in valid), default=0.0)
    success_flips = sum(1 for row in valid if bool(row.get("success_flip", False)))
    collision_flips = sum(1 for row in valid if bool(row.get("collision_flip", False)))
    best = max(valid, key=lambda row: _finite_float(row.get("abs_terminal_margin_gap_from_normal"))) if valid else {}
    margin = _finite_float(anchor.get("normal_terminal_margin"), default=float("nan"))
    normal_success = bool(anchor.get("normal_success", False))
    normal_collision = bool(anchor.get("normal_collision", False))
    changed = max_gap >= MARGIN_GAP_THRESHOLD or success_flips > 0 or collision_flips > 0
    strong_changed = max_gap >= STRONG_MARGIN_GAP_THRESHOLD or collision_flips > 0
    recoverable = bool(np.isfinite(margin) and abs(margin) <= RECOVERABLE_MARGIN_ABS_MAX and changed)
    strong = bool(np.isfinite(margin) and abs(margin) <= STRONG_MARGIN_ABS_MAX and strong_changed)
    if strong:
        label = "strong_recoverable_boundary"
    elif recoverable:
        label = "recoverable_boundary"
    elif normal_collision and not changed:
        label = "already_colliding"
    elif normal_success and np.isfinite(margin) and margin > HIGH_MARGIN_SAFE_MIN and collision_flips == 0:
        label = "high_margin_safe"
    else:
        label = "inactive_boundary"
    return {
        "triage_label": label,
        "recoverable_boundary": recoverable,
        "strong_recoverable_boundary": strong,
        "max_abs_terminal_margin_gap": max_gap,
        "success_flip_count": success_flips,
        "collision_flip_count": collision_flips,
        "best_override": str(best.get("override", "")),
        "best_hold_steps": int(best.get("hold_steps") or 0),
    }


def recoverable_active_anchor_rows(anchor_rows: Sequence[dict[str, Any]], local_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate local hold rows into recoverability labels."""

    by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in local_rows:
        by_anchor[str(row.get("anchor_id", ""))].append(row)
    result: list[dict[str, Any]] = []
    for anchor in anchor_rows:
        row = dict(anchor)
        row.update(classify_anchor(anchor, by_anchor.get(str(anchor.get("anchor_id", "")), [])))
        result.append(row)
    return result


def _group_summary(rows: Sequence[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    result: list[dict[str, Any]] = []
    for value, group in sorted(grouped.items()):
        result.append(
            {
                key: value,
                "anchor_count": len(group),
                "recoverable_boundary_anchor_count": sum(1 for row in group if bool(row.get("recoverable_boundary", False))),
                "strong_recoverable_boundary_anchor_count": sum(1 for row in group if bool(row.get("strong_recoverable_boundary", False))),
                "already_colliding_count": sum(1 for row in group if row.get("triage_label") == "already_colliding"),
                "high_margin_safe_count": sum(1 for row in group if row.get("triage_label") == "high_margin_safe"),
                "max_abs_terminal_margin_gap": max((_finite_float(row.get("max_abs_terminal_margin_gap")) for row in group), default=0.0),
            }
        )
    return result


def build_summary(
    *,
    specs: Sequence[CalibrationSpec],
    anchor_rows: Sequence[dict[str, Any]],
    local_rows: Sequence[dict[str, Any]],
    triage_rows: Sequence[dict[str, Any]],
    max_source_specs: int,
    max_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build recoverable active-set generator summary and gates."""

    guardrails = dict(GUARDRAILS)
    replay_ok = [row for row in anchor_rows if row.get("normal_replay_status") == "ok"]
    recoverable_rows = [row for row in triage_rows if bool(row.get("recoverable_boundary", False))]
    strong_rows = [row for row in triage_rows if bool(row.get("strong_recoverable_boundary", False))]
    predecision_rows = [row for row in recoverable_rows if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS]
    active_family_counts = Counter(str(row.get("source_family", "")) for row in recoverable_rows)
    active_window_counts = Counter(str(row.get("anchor_window", "")) for row in recoverable_rows)
    local_ok = [row for row in local_rows if row.get("replay_status") == "ok"]
    already_colliding_count = sum(1 for row in triage_rows if row.get("triage_label") == "already_colliding")
    high_margin_active_count = sum(1 for row in recoverable_rows if bool(row.get("normal_success", False)) and _finite_float(row.get("normal_terminal_margin")) > HIGH_MARGIN_SAFE_MIN)
    summary = {
        "result_class": "recoverable_active_set_generator_smoke",
        "source_spec_count": len(specs),
        "max_source_specs": int(max_source_specs),
        "anchor_candidate_count": len(anchor_rows),
        "max_anchors": int(max_anchors),
        "replay_ok_anchor_count": len(replay_ok),
        "local_hold_row_count": len(local_rows),
        "local_hold_failure_count": len(local_rows) - len(local_ok),
        "override_count": len(LOCAL_OVERRIDES),
        "hold_step_count": len(HOLD_STEPS),
        "continuation_steps": int(continuation_steps),
        "recoverable_boundary_anchor_count": len(recoverable_rows),
        "strong_recoverable_boundary_anchor_count": len(strong_rows),
        "predecision_recoverable_anchor_count": len(predecision_rows),
        "active_source_family_count": len(active_family_counts),
        "active_window_count": len(active_window_counts),
        "max_single_active_family_share": _max_share(active_family_counts),
        "max_single_active_window_share": _max_share(active_window_counts),
        "success_flip_count": sum(1 for row in local_ok if bool(row.get("success_flip", False))),
        "collision_flip_count": sum(1 for row in local_ok if bool(row.get("collision_flip", False))),
        "already_colliding_count": already_colliding_count,
        "high_margin_safe_count": sum(1 for row in triage_rows if row.get("triage_label") == "high_margin_safe"),
        "high_margin_active_share": high_margin_active_count / max(1, len(recoverable_rows)),
        "near_boundary_collision_only_share": already_colliding_count / max(1, len(triage_rows)),
        "triage_label_counts": dict(sorted(Counter(str(row.get("triage_label", "")) for row in triage_rows).items())),
        "active_source_family_counts": dict(sorted(active_family_counts.items())),
        "active_window_counts": dict(sorted(active_window_counts.items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 160
        and int(summary["anchor_candidate_count"]) >= 256
        and int(summary["replay_ok_anchor_count"]) >= 128
        and int(summary["recoverable_boundary_anchor_count"]) >= 24
        and int(summary["strong_recoverable_boundary_anchor_count"]) >= 8
        and int(summary["predecision_recoverable_anchor_count"]) >= 12
        and int(summary["active_source_family_count"]) >= 4
        and int(summary["active_window_count"]) >= 3
        and float(summary["max_single_active_family_share"]) <= 0.35
        and float(summary["max_single_active_window_share"]) <= 0.45
        and (int(summary["collision_flip_count"]) >= 4 or int(summary["success_flip_count"]) >= 8)
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["recoverable_boundary_anchor_count"]) >= 48
        and int(summary["strong_recoverable_boundary_anchor_count"]) >= 16
        and int(summary["active_source_family_count"]) >= 5
        and int(summary["active_window_count"]) >= 4
        and float(summary["max_single_active_family_share"]) <= 0.30
        and float(summary["near_boundary_collision_only_share"]) <= 0.40
        and float(summary["high_margin_active_share"]) <= 0.25
    )
    return summary


def run_recoverable_active_set_generator_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 4,
    max_source_specs: int = 240,
    max_anchors: int = 256,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded no-training recoverable active-set generator smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    candidates = build_anchor_candidates(specs, max_anchors=max_anchors)
    anchor_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        spec = specs_by_id[candidate.calibration_id]
        replay = replay_to_anchor(
            pair_id=candidate.anchor_id,
            side="target",
            spec=spec,
            anchor_step=int(candidate.anchor_step),
            model=model,
        )
        normal = run_hold_continuation(
            replay=replay,
            spec=spec,
            model=model,
            continuation_steps=continuation_steps,
        )
        anchor_rows.append(anchor_result_row(candidate, normal))
        for override in LOCAL_OVERRIDES:
            for hold_steps in HOLD_STEPS:
                result = run_hold_continuation(
                    replay=replay,
                    spec=spec,
                    model=model,
                    continuation_steps=continuation_steps,
                    override=override,
                    hold_steps=int(hold_steps),
                )
                local_rows.append(
                    local_hold_row(
                        candidate,
                        normal,
                        override=override,
                        hold_steps=int(hold_steps),
                        result=result,
                    )
                )

    triage_rows = recoverable_active_anchor_rows(anchor_rows, local_rows)
    recoverable_rows = [row for row in triage_rows if bool(row.get("recoverable_boundary", False))]
    summary = build_summary(
        specs=specs,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        triage_rows=triage_rows,
        max_source_specs=max_source_specs,
        max_anchors=max_anchors,
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "local_hold_rows.csv", local_rows)
    write_csv_rows(output / "recoverable_active_anchor_rows.csv", recoverable_rows)
    write_csv_rows(output / "triage_summary.csv", _group_summary(triage_rows, "triage_label"))
    write_csv_rows(output / "source_family_summary.csv", _group_summary(triage_rows, "source_family"))
    write_csv_rows(output / "window_summary.csv", _group_summary(triage_rows, "anchor_window"))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run recoverable active-set generator smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=4)
    parser.add_argument("--max-source-specs", type=int, default=240)
    parser.add_argument("--max-anchors", type=int, default=256)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_recoverable_active_set_generator_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_source_specs=int(args.max_source_specs),
        max_anchors=int(args.max_anchors),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"recoverable_boundary_anchor_count={summary['recoverable_boundary_anchor_count']}")
    print(f"strong_recoverable_boundary_anchor_count={summary['strong_recoverable_boundary_anchor_count']}")
    print(f"active_source_family_count={summary['active_source_family_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
