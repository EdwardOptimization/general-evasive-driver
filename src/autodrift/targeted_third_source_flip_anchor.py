"""Targeted third-source flip-anchor source-generation repair."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.calibrated_pair_expansion_planner import expanded_terminal_source_rows
from autodrift.calibrated_terminal_boundary_history_interventions import replay_to_anchor
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT, assert_p0_model_contract
from autodrift.flip_anchor_source_generation_repair import (
    GUARDRAILS,
    REPAIR_LOCAL_OVERRIDES,
    apply_repair_override,
    build_flip_anchor_summary,
    _flip_rows,
    _group_summary,
)
from autodrift.recoverable_active_set_generator import (
    anchor_result_row,
    build_anchor_candidates,
    local_hold_row,
    recoverable_active_anchor_rows,
    run_hold_continuation,
)
from autodrift.temporal_active_set_anchor_sensitivity_miner import _asdict_rows
from autodrift.terminal_boundary_task_sampling_calibration import CalibrationMode, _retarget_hook_spec


DEFAULT_RUN_DIR = Path("runs/m1570_targeted_third_source_flip_anchor_smoke")
EXISTING_FLIP_SOURCE_FAMILIES = {"t5_boundary_axis_retarget", "t5_near_boundary_warmup"}
TARGETED_SOURCE_FAMILIES = {"t5_high_speed_close_obstacle", "late_reveal_boundary"}
DIAGNOSTIC_SOURCE_FAMILIES = {"curved_boundary_obstacle"}
TARGETED_HOLD_STEPS = (1, 4, 8, 12, 16, 20, 24)
TARGETED_LOCAL_OVERRIDES = (
    *REPAIR_LOCAL_OVERRIDES,
    "steer_left_full_brake_long",
    "steer_right_full_brake_long",
    "brake_pulse_then_release",
    "steer_left_brake_release",
    "steer_right_brake_release",
)


def _targeted_high_speed_modes() -> tuple[CalibrationMode, ...]:
    return (
        CalibrationMode("hs_close_wide", 0.68, 0.50, 2.0, 0),
        CalibrationMode("hs_very_close_wide", 0.58, 0.70, 2.0, 0),
        CalibrationMode("hs_close_faster", 0.68, 0.45, 4.0, 0),
        CalibrationMode("hs_very_close_faster", 0.58, 0.65, 4.0, 0),
        CalibrationMode("hs_late_close", 0.70, 0.45, 2.0, 4),
        CalibrationMode("hs_late_very_close", 0.60, 0.65, 3.0, 6),
        CalibrationMode("hs_late_faster", 0.72, 0.40, 5.0, 6),
        CalibrationMode("hs_low_authority_close", 0.70, 0.45, 2.0, 0, low_authority_band=True),
        CalibrationMode("hs_low_authority_wide", 0.62, 0.70, 3.0, 0, low_authority_band=True),
        CalibrationMode("hs_low_authority_late", 0.66, 0.55, 3.0, 6, low_authority_band=True),
        CalibrationMode("hs_aeb_close", 0.68, 0.50, 2.0, 4, require_aeb_infeasible=True),
        CalibrationMode("hs_aeb_wide", 0.60, 0.70, 3.0, 4, require_aeb_infeasible=True),
        CalibrationMode("hs_aeb_low_authority", 0.62, 0.70, 4.0, 6, require_aeb_infeasible=True, low_authority_band=True),
        CalibrationMode("hs_moderate_close", 0.76, 0.30, 2.5, 0),
        CalibrationMode("hs_moderate_late", 0.78, 0.35, 3.0, 4),
        CalibrationMode("hs_boundary_pressure", 0.72, 0.60, 1.0, 0),
        CalibrationMode("hs_boundary_pressure_late", 0.74, 0.55, 2.0, 6),
        CalibrationMode("hs_recovery_window", 0.82, 0.25, 2.0, -2),
    )


def _targeted_late_reveal_modes() -> tuple[CalibrationMode, ...]:
    return (
        CalibrationMode("lr_moderate_close", 0.82, 0.25, 0.0, 4),
        CalibrationMode("lr_moderate_wide", 0.82, 0.45, 0.0, 4),
        CalibrationMode("lr_close_wide", 0.72, 0.50, 1.0, 6),
        CalibrationMode("lr_late_close", 0.78, 0.35, 1.5, 8),
        CalibrationMode("lr_late_wide", 0.76, 0.55, 1.5, 8),
        CalibrationMode("lr_very_late_moderate", 0.86, 0.30, 1.0, 10),
        CalibrationMode("lr_very_late_wide", 0.84, 0.50, 1.0, 10),
        CalibrationMode("lr_speed_pressure", 0.78, 0.35, 3.0, 6),
        CalibrationMode("lr_speed_wide", 0.76, 0.55, 3.0, 6),
        CalibrationMode("lr_low_authority_moderate", 0.84, 0.30, 1.0, 6, low_authority_band=True),
        CalibrationMode("lr_low_authority_wide", 0.80, 0.50, 1.5, 8, low_authority_band=True),
        CalibrationMode("lr_aeb_moderate", 0.82, 0.35, 1.0, 6, require_aeb_infeasible=True),
        CalibrationMode("lr_aeb_wide", 0.78, 0.55, 2.0, 8, require_aeb_infeasible=True),
        CalibrationMode("lr_aeb_low_authority", 0.80, 0.55, 2.0, 8, require_aeb_infeasible=True, low_authority_band=True),
        CalibrationMode("lr_boundary_pressure", 0.74, 0.65, 0.0, 6),
        CalibrationMode("lr_boundary_recover", 0.90, 0.20, 0.0, 4),
        CalibrationMode("lr_predecision_probe", 0.88, 0.30, 2.0, 2),
        CalibrationMode("lr_late_brake_band", 0.80, 0.40, 2.5, 10),
    )


def _comparison_modes() -> tuple[CalibrationMode, ...]:
    return (
        CalibrationMode("cmp_close_wide", 0.70, 0.40, 0.0, 0),
        CalibrationMode("cmp_very_close_wide", 0.60, 0.60, 0.0, 0),
        CalibrationMode("cmp_close_high_speed", 0.70, 0.40, 3.0, 0),
        CalibrationMode("cmp_late_close_high_speed", 0.70, 0.40, 3.0, 8),
        CalibrationMode("cmp_low_authority_close", 0.70, 0.40, 1.5, 0, low_authority_band=True),
        CalibrationMode("cmp_low_authority_very_close", 0.62, 0.60, 1.5, 4, low_authority_band=True),
        CalibrationMode("cmp_aeb_close", 0.68, 0.50, 1.5, 4, require_aeb_infeasible=True),
        CalibrationMode("cmp_aeb_low_authority", 0.62, 0.65, 3.0, 8, require_aeb_infeasible=True, low_authority_band=True),
    )


def targeted_calibration_modes(source_family: str) -> tuple[CalibrationMode, ...]:
    """Return source-family specific retarget modes for M1570."""

    if source_family == "t5_high_speed_close_obstacle":
        return _targeted_high_speed_modes()
    if source_family == "late_reveal_boundary":
        return _targeted_late_reveal_modes()
    return _comparison_modes()


def targeted_source_specs(*, seed: int, seed_count: int, max_source_specs: int) -> list[Any]:
    """Build target-heavy calibration specs while retaining comparison families."""

    base_rows = max(1, int(np.ceil(max_source_specs / 10.0)))
    rows = expanded_terminal_source_rows(seed=seed, seed_count=seed_count, max_base_rows=base_rows)
    specs: list[Any] = []
    for row in rows:
        for mode in targeted_calibration_modes(str(row.source_family)):
            if len(specs) >= int(max_source_specs):
                return specs
            specs.append(_retarget_hook_spec(row, mode, calibration_index=len(specs)))
    return specs


def apply_targeted_override(action: Sequence[float], override: str) -> np.ndarray:
    """Apply diagnostic overrides for targeted third-source flip probing."""

    if override in REPAIR_LOCAL_OVERRIDES:
        return apply_repair_override(action, override)
    result = np.asarray(action, dtype=np.float64).copy()
    if result.shape != (3,):
        raise ValueError(f"expected action shape (3,), got {result.shape}")
    if override == "steer_left_full_brake_long":
        result[0] += 0.34
        result[1] = -1.0
        result[2] = 1.0
    elif override == "steer_right_full_brake_long":
        result[0] -= 0.34
        result[1] = -1.0
        result[2] = 1.0
    elif override == "brake_pulse_then_release":
        result[1] = -1.0
        result[2] = 1.0
    elif override == "steer_left_brake_release":
        result[0] += 0.30
        result[1] = -1.0
        result[2] = -1.0
    elif override == "steer_right_brake_release":
        result[0] -= 0.30
        result[1] = -1.0
        result[2] = -1.0
    else:
        raise ValueError(f"unknown targeted override: {override}")
    return np.clip(result, -1.0, 1.0).astype(np.float32)


def build_targeted_flip_anchor_summary(
    *,
    specs: Sequence[Any],
    anchor_rows: Sequence[Mapping[str, Any]],
    local_rows: Sequence[Mapping[str, Any]],
    triage_rows: Sequence[Mapping[str, Any]],
    max_source_specs: int,
    max_anchors: int,
    continuation_steps: int,
) -> dict[str, Any]:
    """Build M1570 summary with explicit third-source gates."""

    summary = build_flip_anchor_summary(
        specs=specs,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        triage_rows=triage_rows,
        max_source_specs=max_source_specs,
        max_anchors=max_anchors,
        continuation_steps=continuation_steps,
    )
    recoverable_rows = [row for row in triage_rows if bool(row.get("recoverable_boundary", False))]
    flip_rows = _flip_rows(recoverable_rows)
    third_source_rows = [
        row for row in flip_rows if str(row.get("source_family", "")) not in EXISTING_FLIP_SOURCE_FAMILIES
    ]
    targeted_rows = [row for row in flip_rows if str(row.get("source_family", "")) in TARGETED_SOURCE_FAMILIES]
    targeted_family_counts = Counter(str(row.get("source_family", "")) for row in targeted_rows)
    third_family_counts = Counter(str(row.get("source_family", "")) for row in third_source_rows)
    summary.update(
        {
            "result_class": "targeted_third_source_flip_anchor_smoke",
            "targeted_source_families": sorted(TARGETED_SOURCE_FAMILIES),
            "existing_flip_source_families": sorted(EXISTING_FLIP_SOURCE_FAMILIES),
            "diagnostic_source_families": sorted(DIAGNOSTIC_SOURCE_FAMILIES),
            "override_count": len(TARGETED_LOCAL_OVERRIDES),
            "hold_step_count": len(TARGETED_HOLD_STEPS),
            "third_source_flip_anchor_count": len(third_source_rows),
            "targeted_family_flip_anchor_count": len(targeted_rows),
            "third_source_collision_flip_anchor_count": sum(
                1 for row in third_source_rows if int(row.get("collision_flip_count") or 0) > 0
            ),
            "third_source_success_flip_anchor_count": sum(
                1 for row in third_source_rows if int(row.get("success_flip_count") or 0) > 0
            ),
            "targeted_family_collision_flip_anchor_count": sum(
                1 for row in targeted_rows if int(row.get("collision_flip_count") or 0) > 0
            ),
            "targeted_family_success_flip_anchor_count": sum(
                1 for row in targeted_rows if int(row.get("success_flip_count") or 0) > 0
            ),
            "third_source_flip_family_counts": dict(sorted(third_family_counts.items())),
            "targeted_flip_family_counts": dict(sorted(targeted_family_counts.items())),
        }
    )
    summary["passes_public_smoke_gates"] = (
        int(summary["source_spec_count"]) >= 300
        and int(summary["anchor_candidate_count"]) >= 320
        and int(summary["replay_ok_anchor_count"]) >= 160
        and int(summary["recoverable_boundary_anchor_count"]) >= 48
        and int(summary["strong_recoverable_boundary_anchor_count"]) >= 16
        and int(summary["active_source_family_count"]) >= 5
        and int(summary["active_window_count"]) >= 5
        and int(summary["distinct_collision_flip_anchor_count"]) >= 8
        and int(summary["distinct_success_flip_anchor_count"]) >= 8
        and int(summary["flip_anchor_source_family_count"]) >= 3
        and int(summary["third_source_flip_anchor_count"]) >= 1
        and int(summary["targeted_family_flip_anchor_count"]) >= 1
        and int(summary["flip_anchor_window_count"]) >= 3
        and float(summary["max_single_flip_source_family_share"]) <= 0.60
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["history_interventions_executed"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["candidate_materialized"])
    )
    summary["passes_evidence_quality_targets"] = (
        bool(summary["passes_public_smoke_gates"])
        and int(summary["distinct_collision_flip_anchor_count"]) >= 10
        and int(summary["distinct_success_flip_anchor_count"]) >= 10
        and int(summary["flip_anchor_source_family_count"]) >= 3
        and int(summary["third_source_flip_anchor_count"]) >= 3
        and int(summary["targeted_family_flip_anchor_count"]) >= 3
        and float(summary["max_single_flip_source_family_share"]) <= 0.50
    )
    return summary


def run_targeted_third_source_flip_anchor_smoke(
    output_dir: Path | str,
    *,
    checkpoint: Path | str = DEFAULT_CHECKPOINT,
    seed: int = 1843,
    seed_count: int = 6,
    max_source_specs: int = 360,
    max_anchors: int = 360,
    continuation_steps: int = 64,
    device: str = "cpu",
) -> dict[str, Any]:
    """Run the bounded targeted third-source source-generation smoke."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = targeted_source_specs(seed=seed, seed_count=seed_count, max_source_specs=max_source_specs)
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
        for override in TARGETED_LOCAL_OVERRIDES:
            for hold_steps in TARGETED_HOLD_STEPS:
                result = run_hold_continuation(
                    replay=replay,
                    spec=spec,
                    model=model,
                    continuation_steps=continuation_steps,
                    override=override,
                    hold_steps=int(hold_steps),
                    override_fn=apply_targeted_override,
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
    flip_rows = _flip_rows(recoverable_rows)
    targeted_rows = [row for row in flip_rows if str(row.get("source_family", "")) in TARGETED_SOURCE_FAMILIES]
    summary = build_targeted_flip_anchor_summary(
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
    write_csv_rows(output / "flip_anchor_rows.csv", flip_rows)
    write_csv_rows(output / "targeted_flip_anchor_rows.csv", targeted_rows)
    write_csv_rows(output / "source_family_summary.csv", _group_summary(triage_rows, "source_family"))
    write_csv_rows(output / "window_summary.csv", _group_summary(triage_rows, "anchor_window"))
    write_csv_rows(output / "flip_source_summary.csv", _group_summary(flip_rows, "source_family"))
    write_csv_rows(output / "guardrail_summary.csv", [{"guardrail": key, "violated": value} for key, value in GUARDRAILS.items()])
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run targeted third-source flip-anchor source-generation smoke.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--seed", type=int, default=1843)
    parser.add_argument("--seed-count", type=int, default=6)
    parser.add_argument("--max-source-specs", type=int, default=360)
    parser.add_argument("--max-anchors", type=int, default=360)
    parser.add_argument("--continuation-steps", type=int, default=64)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_targeted_third_source_flip_anchor_smoke(
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
    print(f"third_source_flip_anchor_count={summary['third_source_flip_anchor_count']}")
    print(f"targeted_family_flip_anchor_count={summary['targeted_family_flip_anchor_count']}")
    print(f"distinct_collision_flip_anchor_count={summary['distinct_collision_flip_anchor_count']}")
    print(f"distinct_success_flip_anchor_count={summary['distinct_success_flip_anchor_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")


if __name__ == "__main__":
    main()
