"""No-training temporal active-set anchor sensitivity miner."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_pair_expansion_planner import expanded_terminal_source_rows
from autodrift.calibrated_terminal_boundary_history_interventions import replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract, hidden_stats, phase_for_step
from autodrift.decisive_history_t5_interventions import _clone_hidden
from autodrift.evaluate import ActorPolicy
from autodrift.terminal_boundary_task_sampling_calibration import CalibrationSpec, build_calibration_specs


DEFAULT_RUN_DIR = Path("runs/m1556_temporal_active_set_anchor_sensitivity_miner_smoke")
ANCHOR_WINDOWS = (
    "reveal",
    "reveal_plus_4",
    "decision_minus_16",
    "decision_minus_8",
    "decision",
    "post_decision_8",
)
PREDECISION_WINDOWS = {"reveal", "reveal_plus_4", "decision_minus_16", "decision_minus_8"}
OVERRIDES = (
    "steer_left",
    "steer_right",
    "brake_more",
    "brake_less",
    "steer_left_brake_more",
    "steer_right_brake_more",
)
TERMINAL_MARGIN_GAP_THRESHOLD = 0.02
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


@dataclass(frozen=True)
class AnchorCandidate:
    """One candidate temporal active-set anchor before local perturbation."""

    anchor_id: str
    calibration_id: str
    source_row_id: str
    source_family: str
    task_family: str
    seed: int
    mode_name: str
    anchor_window: str
    anchor_step: int
    reveal_step: int
    decision_step: int
    phase: str
    base_distance_min: float
    base_distance_max: float
    retarget_distance_min: float
    retarget_distance_max: float


@dataclass(frozen=True)
class ContinuationResult:
    """Fixed-policy continuation result from one anchor."""

    replay_status: str
    terminal_margin: float
    success: bool
    collision: bool
    obstacle_completed: bool
    terminal_reason: str
    first_action: tuple[float, float, float]
    executed_first_action: tuple[float, float, float]
    hidden_norm: float
    hidden_checksum: float
    continuation_steps: int
    error_type: str = ""
    error_message: str = ""


def _asdict_rows(rows: Sequence[Any]) -> list[dict[str, Any]]:
    return [asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row) for row in rows]


def _max_share(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return max((count / max(1, total) for count in counts.values()), default=0.0)


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


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


def anchor_step_for_window(spec: CalibrationSpec, window: str) -> int:
    """Map a named temporal window to a bounded simulator step."""

    hook = spec.hook_spec
    reveal = int(hook.reveal_step)
    decision = int(hook.decision_step)
    max_step = max(0, int(hook.env_config.max_steps) - 1)
    if window == "reveal":
        step = reveal
    elif window == "reveal_plus_4":
        step = reveal + 4
    elif window == "decision_minus_16":
        step = decision - 16
    elif window == "decision_minus_8":
        step = decision - 8
    elif window == "decision":
        step = decision
    elif window == "post_decision_8":
        step = decision + 8
    else:
        raise ValueError(f"unknown anchor window: {window}")
    return int(min(max(step, 0), max_step))


def build_anchor_candidates(
    specs: Sequence[CalibrationSpec],
    *,
    max_anchors: int = 96,
    windows: Sequence[str] = ANCHOR_WINDOWS,
) -> list[AnchorCandidate]:
    """Build a source-family round-robin anchor set."""

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
    """Apply a one-step local action override in the actor action space."""

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
    elif override == "steer_left_brake_more":
        result[0] += steer_delta
        result[2] += brake_delta
    elif override == "steer_right_brake_more":
        result[0] -= steer_delta
        result[2] += brake_delta
    else:
        raise ValueError(f"unknown local override: {override}")
    return np.clip(result, -1.0, 1.0).astype(np.float32)


def run_anchor_continuation(
    *,
    candidate: AnchorCandidate,
    spec: CalibrationSpec,
    model: Any,
    continuation_steps: int = 64,
    override: str | None = None,
) -> ContinuationResult:
    """Run fixed policy from one anchor with an optional one-step override."""

    replay = replay_to_anchor(
        pair_id=candidate.anchor_id,
        side="target",
        spec=spec,
        anchor_step=int(candidate.anchor_step),
        model=model,
    )
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

    policy = ActorPolicy(model, spec.hook_spec.env_config)
    policy.hidden = _clone_hidden(replay.hidden)
    observation = np.asarray(replay.observation, dtype=np.float32)
    info = replay.info
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
                executed = action if override is None else apply_local_override(action, override)
                executed_first_action = np.asarray(executed, dtype=np.float64)
            else:
                executed = action
            observation, _, terminated, truncated, info = replay.env.step(executed)
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


def _candidate_result_row(candidate: AnchorCandidate, normal: ContinuationResult) -> dict[str, Any]:
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


def _local_row(candidate: AnchorCandidate, normal: ContinuationResult, override: str, result: ContinuationResult) -> dict[str, Any]:
    signed_gap = float("nan")
    abs_gap = float("nan")
    if np.isfinite(normal.terminal_margin) and np.isfinite(result.terminal_margin):
        signed_gap = float(normal.terminal_margin - result.terminal_margin)
        abs_gap = abs(signed_gap)
    success_flip = bool(result.success != normal.success)
    collision_flip = bool(result.collision != normal.collision)
    row = asdict(candidate)
    row.update(
        {
            "override": override,
            "replay_status": result.replay_status,
            "normal_terminal_margin": normal.terminal_margin,
            "override_terminal_margin": result.terminal_margin,
            "signed_terminal_margin_gap_from_normal": signed_gap,
            "abs_terminal_margin_gap_from_normal": abs_gap,
            "normal_success": normal.success,
            "override_success": result.success,
            "success_flip": success_flip,
            "normal_collision": normal.collision,
            "override_collision": result.collision,
            "collision_flip": collision_flip,
            "normal_terminal_reason": normal.terminal_reason,
            "override_terminal_reason": result.terminal_reason,
            "baseline_action_steer": normal.first_action[0],
            "baseline_action_throttle": normal.first_action[1],
            "baseline_action_brake": normal.first_action[2],
            "override_action_steer": result.executed_first_action[0],
            "override_action_throttle": result.executed_first_action[1],
            "override_action_brake": result.executed_first_action[2],
            "continuation_steps": result.continuation_steps,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }
    )
    return row


def active_anchor_rows(anchor_rows: Sequence[dict[str, Any]], local_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate local perturbation rows into active anchor rows."""

    by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in local_rows:
        by_anchor[str(row.get("anchor_id", ""))].append(row)
    anchors_by_id = {str(row.get("anchor_id", "")): row for row in anchor_rows}
    accepted: list[dict[str, Any]] = []
    for anchor_id, rows in sorted(by_anchor.items()):
        anchor_base = anchors_by_id.get(anchor_id, {})
        if str(anchor_base.get("normal_replay_status", "")) != "ok":
            continue
        valid_rows = [row for row in rows if str(row.get("replay_status", "")) == "ok"]
        if not valid_rows:
            continue
        max_gap = max((_finite_float(row.get("abs_terminal_margin_gap_from_normal")) for row in valid_rows), default=0.0)
        success_flips = sum(1 for row in valid_rows if bool(row.get("success_flip", False)))
        collision_flips = sum(1 for row in valid_rows if bool(row.get("collision_flip", False)))
        if max_gap < TERMINAL_MARGIN_GAP_THRESHOLD and success_flips == 0 and collision_flips == 0:
            continue
        anchor = dict(anchor_base)
        best = max(valid_rows, key=lambda row: _finite_float(row.get("abs_terminal_margin_gap_from_normal")))
        anchor.update(
            {
                "max_abs_terminal_margin_gap": max_gap,
                "best_override": best.get("override", ""),
                "success_flip_count": success_flips,
                "collision_flip_count": collision_flips,
                "active_set_positive": True,
                "predecision_anchor": str(anchor.get("anchor_window", "")) in PREDECISION_WINDOWS,
                "near_boundary_normal_margin": abs(float(anchor.get("normal_terminal_margin") or 0.0)) <= 0.10,
            }
        )
        accepted.append(anchor)
    return accepted


def build_source_family_summary(anchor_rows: Sequence[dict[str, Any]], active_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize source-family coverage and active anchors."""

    candidate_counts = Counter(str(row.get("source_family", "")) for row in anchor_rows)
    active_counts = Counter(str(row.get("source_family", "")) for row in active_rows)
    rows: list[dict[str, Any]] = []
    for family in sorted(set(candidate_counts) | set(active_counts)):
        rows.append(
            {
                "source_family": family,
                "anchor_candidate_count": candidate_counts.get(family, 0),
                "active_anchor_count": active_counts.get(family, 0),
                "candidate_share": candidate_counts.get(family, 0) / max(1, len(anchor_rows)),
                "active_share": active_counts.get(family, 0) / max(1, len(active_rows)),
            }
        )
    return rows


def build_window_summary(anchor_rows: Sequence[dict[str, Any]], active_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize anchor-window coverage and sensitivity."""

    candidate_counts = Counter(str(row.get("anchor_window", "")) for row in anchor_rows)
    active_counts = Counter(str(row.get("anchor_window", "")) for row in active_rows)
    rows: list[dict[str, Any]] = []
    for window in ANCHOR_WINDOWS:
        rows.append(
            {
                "anchor_window": window,
                "anchor_candidate_count": candidate_counts.get(window, 0),
                "active_anchor_count": active_counts.get(window, 0),
                "candidate_share": candidate_counts.get(window, 0) / max(1, len(anchor_rows)),
                "active_share": active_counts.get(window, 0) / max(1, len(active_rows)),
            }
        )
    return rows


def build_summary(
    *,
    specs: Sequence[CalibrationSpec],
    anchor_rows: Sequence[dict[str, Any]],
    local_rows: Sequence[dict[str, Any]],
    active_rows: Sequence[dict[str, Any]],
    max_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build active-set miner summary and gates."""

    guardrails = dict(GUARDRAILS)
    candidate_family_counts = Counter(str(row.get("source_family", "")) for row in anchor_rows)
    active_family_counts = Counter(str(row.get("source_family", "")) for row in active_rows)
    valid_local_rows = [row for row in local_rows if str(row.get("replay_status", "")) == "ok"]
    success_flip_count = sum(1 for row in valid_local_rows if bool(row.get("success_flip", False)))
    collision_flip_count = sum(1 for row in valid_local_rows if bool(row.get("collision_flip", False)))
    predecision_count = sum(1 for row in active_rows if str(row.get("anchor_window", "")) in PREDECISION_WINDOWS)
    summary = {
        "result_class": "temporal_active_set_anchor_sensitivity_miner_smoke",
        "calibration_spec_count": len(specs),
        "anchor_candidate_count": len(anchor_rows),
        "max_anchors": int(max_anchors),
        "local_perturbation_row_count": len(local_rows),
        "override_count": len(OVERRIDES),
        "continuation_steps": int(continuation_steps),
        "anchor_replay_failure_count": sum(1 for row in anchor_rows if row.get("normal_replay_status") != "ok"),
        "local_perturbation_failure_count": sum(1 for row in local_rows if row.get("replay_status") != "ok"),
        "action_sensitive_anchor_count": len(active_rows),
        "predecision_sensitive_anchor_count": predecision_count,
        "source_family_count": len(candidate_family_counts),
        "active_source_family_count": len(active_family_counts),
        "max_single_family_share": _max_share(candidate_family_counts),
        "max_single_active_family_share": _max_share(active_family_counts),
        "success_flip_count": success_flip_count,
        "collision_flip_count": collision_flip_count,
        "active_anchor_window_count": len({str(row.get("anchor_window", "")) for row in active_rows}),
        "max_abs_terminal_margin_gap": max(
            (_finite_float(row.get("abs_terminal_margin_gap_from_normal")) for row in valid_local_rows),
            default=0.0,
        ),
        "near_boundary_active_anchor_count": sum(1 for row in active_rows if bool(row.get("near_boundary_normal_margin", False))),
        "anchor_window_counts": dict(sorted(Counter(str(row.get("anchor_window", "")) for row in anchor_rows).items())),
        "active_anchor_window_counts": dict(sorted(Counter(str(row.get("anchor_window", "")) for row in active_rows).items())),
        "source_family_counts": dict(sorted(candidate_family_counts.items())),
        "active_source_family_counts": dict(sorted(active_family_counts.items())),
        "guardrail_violation_count": sum(1 for value in guardrails.values() if bool(value)),
        **guardrails,
    }
    summary["passes_public_smoke_gates"] = (
        int(summary["anchor_candidate_count"]) >= 64
        and int(summary["local_perturbation_row_count"]) >= 384
        and int(summary["action_sensitive_anchor_count"]) >= 12
        and int(summary["predecision_sensitive_anchor_count"]) >= 6
        and int(summary["source_family_count"]) >= 4
        and float(summary["max_single_family_share"]) <= 0.40
        and int(summary["success_flip_count"]) >= 2
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["action_sensitive_anchor_count"]) >= 20
        and int(summary["predecision_sensitive_anchor_count"]) >= 10
        and int(summary["active_anchor_window_count"]) >= 3
        and int(summary["active_source_family_count"]) >= 4
        and float(summary["max_single_active_family_share"]) <= 0.35
    )
    return summary


def run_temporal_active_set_anchor_sensitivity_miner_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 3,
    max_base_rows: int = 24,
    max_calibration_specs: int = 240,
    max_anchors: int = 96,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run bounded no-training temporal active-set miner smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_rows = expanded_terminal_source_rows(seed=seed, seed_count=seed_count, max_base_rows=max_base_rows)
    specs = build_calibration_specs(source_rows, max_calibration_specs=max_calibration_specs)
    specs_by_id = {spec.artifact_row.calibration_id: spec for spec in specs}
    model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
    assert_p0_model_contract(model)
    candidates = build_anchor_candidates(specs, max_anchors=max_anchors)

    anchor_rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        spec = specs_by_id[candidate.calibration_id]
        normal = run_anchor_continuation(
            candidate=candidate,
            spec=spec,
            model=model,
            continuation_steps=continuation_steps,
        )
        anchor_rows.append(_candidate_result_row(candidate, normal))
        for override in OVERRIDES:
            result = run_anchor_continuation(
                candidate=candidate,
                spec=spec,
                model=model,
                continuation_steps=continuation_steps,
                override=override,
            )
            local_rows.append(_local_row(candidate, normal, override, result))

    active_rows = active_anchor_rows(anchor_rows, local_rows)
    summary = build_summary(
        specs=specs,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        active_rows=active_rows,
        max_anchors=max_anchors,
        continuation_steps=continuation_steps,
    )
    write_csv_rows(output / "source_spec_rows.csv", _asdict_rows([spec.artifact_row for spec in specs]))
    write_csv_rows(output / "anchor_candidate_rows.csv", anchor_rows)
    write_csv_rows(output / "local_perturbation_rows.csv", local_rows)
    write_csv_rows(output / "accepted_active_anchor_rows.csv", active_rows)
    write_csv_rows(output / "source_family_summary.csv", build_source_family_summary(anchor_rows, active_rows))
    write_csv_rows(output / "window_summary.csv", build_window_summary(anchor_rows, active_rows))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run temporal active-set anchor sensitivity miner smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=3)
    parser.add_argument("--max-base-rows", type=int, default=24)
    parser.add_argument("--max-calibration-specs", type=int, default=240)
    parser.add_argument("--max-anchors", type=int, default=96)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_temporal_active_set_anchor_sensitivity_miner_smoke(
        args.output_dir,
        checkpoint=args.checkpoint,
        seed=int(args.seed),
        seed_count=int(args.seed_count),
        max_base_rows=int(args.max_base_rows),
        max_calibration_specs=int(args.max_calibration_specs),
        max_anchors=int(args.max_anchors),
        continuation_steps=int(args.continuation_steps),
        device=args.device,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"anchor_candidate_count={summary['anchor_candidate_count']}")
    print(f"action_sensitive_anchor_count={summary['action_sensitive_anchor_count']}")
    print(f"success_flip_count={summary['success_flip_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
