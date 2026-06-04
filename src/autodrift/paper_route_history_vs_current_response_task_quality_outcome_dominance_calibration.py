"""Materialize Route B task-quality and outcome-dominance calibration rows.

M2680 is a no-rollout reanalysis of the already executed M2677 public T4/T5
comparison rows. It writes blocker and interpretability panels only. It does
not reset environments, execute policy actions, train, rank controller
families, select winners, promote checkpoints, or make paper/self-ID claims.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = (
    "m2680-paper-route-history-vs-current-response-task-quality-outcome-"
    "dominance-calibration-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2681-paper-route-history-vs-current-response-task-quality-outcome-"
    "dominance-calibration-result-audit"
)
DEFAULT_M2677_DIR = Path(
    "runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2680-paper-route-history-vs-current-response-task-quality-outcome-"
    "dominance-calibration-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2681-paper-route-history-vs-current-response-task-quality-"
    "outcome-dominance-calibration-result-audit.json"
)

TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_SPEC_COUNT = 72
TARGET_COMPARISON_COUNT = 11

OUTCOME_COLUMNS = [
    "success_obstacle_pass",
    "collision_failure",
    "off_track_noncollision_noncompletion",
    "speed_too_low_noncollision_noncompletion",
]
SELECTED_METRICS = [
    "min_clearance_margin",
    "return",
    "steps",
    "action_rate_mean",
    "high_sideslip_fraction",
]
CLAIM_SCOPE = (
    "Route B task-quality and outcome-dominance calibration materialization "
    "only; existing M2677 rows may be reaggregated into diagnostic blocker "
    "and interpretability panels, but no reset, step, rollout, replay, "
    "validation, training, PPO, private holdout, profile-specific tuning, "
    "controller-family ranking, winner selection, promotion, success-rate "
    "verdict, driver-performance, paper, finite-window-vs-GRU, current-"
    "response sufficiency, current-sim, high-fidelity validation, full ideal "
    "driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, comparison-delta verdict, driver performance, "
    "validation readiness or result, paper-level evidence, finite-window-vs-"
    "GRU result, current-response sufficiency result, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 "
    "self-identification"
)

DOMINANCE_FIELDNAMES = [
    "slice_kind",
    "slice_id",
    "profile_name",
    "task_source_id",
    "task_family",
    "episode_count",
    "profile_count",
    "spec_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "speed_too_low_count",
    "termination_offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "termination_offtrack_rate",
    "dominant_outcome",
    "dominance_share",
    "hidden_dynamics_bucket_present",
    "outcome_dominance_blocked",
    "task_quality_blocked",
    "interpretable_for_history_comparison",
    "reason",
    "claim_boundary",
]
COMPARISON_FIELDNAMES = [
    "comparison",
    "left_group",
    "right_group",
    "left_episode_count",
    "right_episode_count",
    "success_rate_delta",
    "collision_rate_delta",
    "clearance_margin_mean_delta",
    "return_mean_delta",
    "diagnostic_only_no_ranking_claim",
    "blocked_by_outcome_dominance",
    "blocked_by_reset_control",
    "blocked_by_current_tiled_zero_success_delta",
    "blocked_by_mixed_metrics",
    "blocked_by_hidden_dynamics_missing",
    "interpretable_for_ranking",
    "allowed_for_synthesis_only",
    "reason",
    "claim_boundary",
]
GAP_FIELDNAMES = [
    "gap_id",
    "gap_family",
    "failure_type",
    "observed",
    "threshold_or_expected",
    "blocks_interpretation",
    "recommended_next_action",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2680",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def materialize_task_quality_outcome_dominance_calibration(
    *,
    m2677_dir: Path | str = DEFAULT_M2677_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_dir = Path(m2677_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(source_dir, follow_up_manifest=Path(follow_up_manifest))

    episode_rows = source["episode_rows"]
    comparison_rows = source["comparison_aggregate_rows"]
    spec_rows = build_dominance_rows(episode_rows, ("task_source_id",), slice_kind="spec")
    profile_rows = build_dominance_rows(episode_rows, ("profile_name",), slice_kind="profile")
    task_family_rows = build_dominance_rows(episode_rows, ("task_family",), slice_kind="task_family")
    comparison_interpretability_rows = build_comparison_interpretability_rows(
        comparison_rows=comparison_rows,
        global_offtrack_blocked=global_offtrack_blocked(episode_rows),
        hidden_dynamics_missing=hidden_dynamics_missing(source),
    )
    calibration_gap_rows = build_calibration_gap_rows(
        source=source,
        spec_rows=spec_rows,
        profile_rows=profile_rows,
        task_family_rows=task_family_rows,
        comparison_rows=comparison_interpretability_rows,
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        spec_rows=spec_rows,
        profile_rows=profile_rows,
        task_family_rows=task_family_rows,
        comparison_rows=comparison_interpretability_rows,
        calibration_gap_rows=calibration_gap_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["spec_outcome_dominance_rows"], spec_rows, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(paths["profile_outcome_dominance_rows"], profile_rows, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(paths["task_family_outcome_dominance_rows"], task_family_rows, fieldnames=DOMINANCE_FIELDNAMES)
    write_csv_rows(
        paths["comparison_interpretability_rows"],
        comparison_interpretability_rows,
        fieldnames=COMPARISON_FIELDNAMES,
    )
    write_csv_rows(paths["calibration_gap_rows"], calibration_gap_rows, fieldnames=GAP_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"complete": False, "completed_count": 0, "failure_count": 1})

    required_artifacts_present = all(path.exists() for key, path in paths.items() if key != "doc")
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        spec_rows=spec_rows,
        profile_rows=profile_rows,
        task_family_rows=task_family_rows,
        comparison_rows=comparison_interpretability_rows,
        calibration_gap_rows=calibration_gap_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        source=source,
        output_dir=output,
        paths=paths,
        spec_rows=spec_rows,
        profile_rows=profile_rows,
        task_family_rows=task_family_rows,
        comparison_rows=comparison_interpretability_rows,
        calibration_gap_rows=calibration_gap_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    write_json(
        paths["run_state"],
        {
            "target_episode_count": TARGET_EPISODE_COUNT,
            "completed_count": len(episode_rows),
            "failure_count": 0 if summary["status_pass"] else 1,
            "complete": bool(summary["status_pass"]),
        },
    )
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    if required_artifacts_present:
        claim_rows = build_claim_boundary_rows(
            follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
            artifacts_present=True,
        )
        gate_rows = build_gate_matrix_rows(
            source=source,
            spec_rows=spec_rows,
            profile_rows=profile_rows,
            task_family_rows=task_family_rows,
            comparison_rows=comparison_interpretability_rows,
            calibration_gap_rows=calibration_gap_rows,
            claim_rows=claim_rows,
            required_artifacts_present=True,
        )
        write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
        write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
        summary = build_summary(
            source=source,
            output_dir=output,
            paths=paths,
            spec_rows=spec_rows,
            profile_rows=profile_rows,
            task_family_rows=task_family_rows,
            comparison_rows=comparison_interpretability_rows,
            calibration_gap_rows=calibration_gap_rows,
            claim_rows=claim_rows,
            gate_rows=gate_rows,
            required_artifacts_present=True,
            milestone=milestone,
            next_blocker=next_blocker,
            follow_up_manifest=Path(follow_up_manifest),
        )
        write_json(paths["summary"], summary)
        paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
        write_json(
            paths["run_state"],
            {
                "target_episode_count": TARGET_EPISODE_COUNT,
                "completed_count": len(episode_rows),
                "failure_count": 0 if summary["status_pass"] else 1,
                "complete": bool(summary["status_pass"]),
            },
        )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "spec_outcome_dominance_rows": output_dir / "spec_outcome_dominance_rows.csv",
        "profile_outcome_dominance_rows": output_dir / "profile_outcome_dominance_rows.csv",
        "task_family_outcome_dominance_rows": output_dir / "task_family_outcome_dominance_rows.csv",
        "comparison_interpretability_rows": output_dir / "comparison_interpretability_rows.csv",
        "calibration_gap_rows": output_dir / "calibration_gap_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(m2677_dir: Path, *, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "summary": m2677_dir / "summary.json",
        "episode_rows": m2677_dir / "episode_rows.csv",
        "profile_aggregate": m2677_dir / "profile_aggregate.csv",
        "spec_aggregate": m2677_dir / "spec_aggregate.csv",
        "comparison_aggregate": m2677_dir / "comparison_aggregate.csv",
        "outcome_aggregate": m2677_dir / "outcome_aggregate.csv",
        "termination_reason_aggregate": m2677_dir / "termination_reason_aggregate.csv",
        "profile_outcome_aggregate": m2677_dir / "profile_outcome_aggregate.csv",
        "hidden_dynamics_aggregate": m2677_dir / "hidden_dynamics_aggregate.csv",
        "profile_hidden_dynamics_worst_bucket": m2677_dir / "profile_hidden_dynamics_worst_bucket.csv",
        "runtime_enforcement_join_rows": m2677_dir / "runtime_enforcement_join_rows.csv",
        "claim_boundary_rows": m2677_dir / "claim_boundary_rows.csv",
        "gate_matrix": m2677_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {key: path.exists() for key, path in paths.items()},
        "summary": read_json(paths["summary"]) if paths["summary"].exists() else {},
        "episode_rows": read_csv_rows(paths["episode_rows"]),
        "profile_aggregate_rows": read_csv_rows(paths["profile_aggregate"]),
        "spec_aggregate_rows": read_csv_rows(paths["spec_aggregate"]),
        "comparison_aggregate_rows": read_csv_rows(paths["comparison_aggregate"]),
        "outcome_aggregate_rows": read_csv_rows(paths["outcome_aggregate"]),
        "termination_reason_aggregate_rows": read_csv_rows(paths["termination_reason_aggregate"]),
        "profile_outcome_aggregate_rows": read_csv_rows(paths["profile_outcome_aggregate"]),
        "hidden_dynamics_aggregate_rows": read_csv_rows(paths["hidden_dynamics_aggregate"]),
        "profile_hidden_dynamics_worst_bucket_rows": read_csv_rows(paths["profile_hidden_dynamics_worst_bucket"]),
        "runtime_enforcement_join_rows": read_csv_rows(paths["runtime_enforcement_join_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_matrix_rows": read_csv_rows(paths["gate_matrix"]),
    }


def build_dominance_rows(
    episode_rows: list[Mapping[str, Any]],
    keys: Sequence[str],
    *,
    slice_kind: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_values, group_rows in _group_rows(episode_rows, keys).items():
        rows.append(build_one_dominance_row(keys, group_values, group_rows, slice_kind=slice_kind))
    return rows


def build_one_dominance_row(
    keys: Sequence[str],
    group_values: tuple[str, ...],
    group_rows: list[Mapping[str, Any]],
    *,
    slice_kind: str,
) -> dict[str, Any]:
    outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in group_rows)
    episode_count = len(group_rows)
    dominant_outcome, dominant_count = max(outcome_counts.items(), key=lambda item: (item[1], item[0]))
    hidden_present = any(str(row.get("hidden_dynamics_bucket", "")).strip() for row in group_rows)
    dominance_share = dominant_count / episode_count if episode_count else 0.0
    offtrack_count = int(outcome_counts.get("off_track_noncollision_noncompletion", 0))
    collision_count = int(outcome_counts.get("collision_failure", 0))
    success_count = int(outcome_counts.get("success_obstacle_pass", 0))
    outcome_dominance_blocked = dominance_share >= 0.80 and dominant_outcome != "success_obstacle_pass"
    task_quality_blocked = offtrack_count / episode_count >= 0.70 if episode_count else True
    interpretable = bool(
        episode_count > 0
        and hidden_present
        and not outcome_dominance_blocked
        and not task_quality_blocked
        and success_count > 0
    )
    reason_parts = []
    if outcome_dominance_blocked:
        reason_parts.append(f"dominant_outcome={dominant_outcome} share={dominance_share:.4f}")
    if task_quality_blocked:
        reason_parts.append("offtrack task-quality blocker active")
    if not hidden_present:
        reason_parts.append("hidden_dynamics_bucket missing")
    if success_count == 0:
        reason_parts.append("zero success support")
    if not reason_parts:
        reason_parts.append("candidate diagnostic slice only")
    row = {
        "slice_kind": slice_kind,
        "slice_id": "|".join(f"{key}={value}" for key, value in zip(keys, group_values)),
        "profile_name": value_for_key(keys, group_values, "profile_name"),
        "task_source_id": value_for_key(keys, group_values, "task_source_id"),
        "task_family": value_for_key(keys, group_values, "task_family"),
        "episode_count": episode_count,
        "profile_count": len({str(row.get("profile_name", "")) for row in group_rows}),
        "spec_count": len({str(row.get("task_source_id", "")) for row in group_rows}),
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_outcome_count": offtrack_count,
        "speed_too_low_count": int(outcome_counts.get("speed_too_low_noncollision_noncompletion", 0)),
        "termination_offtrack_count": int(termination_counts.get("off_track", 0)),
        "success_rate": success_count / episode_count if episode_count else 0.0,
        "collision_rate": collision_count / episode_count if episode_count else 0.0,
        "offtrack_outcome_rate": offtrack_count / episode_count if episode_count else 0.0,
        "termination_offtrack_rate": int(termination_counts.get("off_track", 0)) / episode_count if episode_count else 0.0,
        "dominant_outcome": dominant_outcome,
        "dominance_share": dominance_share,
        "hidden_dynamics_bucket_present": hidden_present,
        "outcome_dominance_blocked": outcome_dominance_blocked,
        "task_quality_blocked": task_quality_blocked,
        "interpretable_for_history_comparison": interpretable,
        "reason": "; ".join(reason_parts),
        "claim_boundary": CLAIM_SCOPE,
    }
    return row


def build_comparison_interpretability_rows(
    *,
    comparison_rows: list[Mapping[str, Any]],
    global_offtrack_blocked: bool,
    hidden_dynamics_missing: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in comparison_rows:
        comparison = str(source_row.get("comparison", ""))
        success_delta = _float_or_zero(source_row.get("success_rate_delta", 0.0))
        collision_delta = _float_or_zero(source_row.get("collision_rate_delta", 0.0))
        clearance_delta = _float_or_zero(source_row.get("clearance_margin_mean_delta", 0.0))
        return_delta = _float_or_zero(source_row.get("return_mean_delta", 0.0))
        mixed_metrics = has_mixed_metric_directions(
            success_delta=success_delta,
            collision_delta=collision_delta,
            clearance_delta=clearance_delta,
            return_delta=return_delta,
        )
        reset_blocked = "reset" in comparison.lower() or "reset" in str(source_row.get("right_group", "")).lower()
        current_tiled_zero = "current_tiled" in comparison and abs(success_delta) < 1e-12
        reason_parts = ["diagnostic_only_no_ranking_claim"]
        if global_offtrack_blocked:
            reason_parts.append("global offtrack dominance blocks ranking")
        if reset_blocked:
            reason_parts.append("reset-control ambiguity")
        if current_tiled_zero:
            reason_parts.append("current-tiled success delta is zero")
        if mixed_metrics:
            reason_parts.append("mixed metric directions")
        if hidden_dynamics_missing:
            reason_parts.append("hidden-dynamics buckets missing")
        rows.append(
            {
                "comparison": comparison,
                "left_group": source_row.get("left_group", ""),
                "right_group": source_row.get("right_group", ""),
                "left_episode_count": _int_or_zero(source_row.get("left_episode_count", 0)),
                "right_episode_count": _int_or_zero(source_row.get("right_episode_count", 0)),
                "success_rate_delta": success_delta,
                "collision_rate_delta": collision_delta,
                "clearance_margin_mean_delta": clearance_delta,
                "return_mean_delta": return_delta,
                "diagnostic_only_no_ranking_claim": _bool(
                    source_row.get("diagnostic_only_no_ranking_claim", False)
                ),
                "blocked_by_outcome_dominance": bool(global_offtrack_blocked),
                "blocked_by_reset_control": bool(reset_blocked),
                "blocked_by_current_tiled_zero_success_delta": bool(current_tiled_zero),
                "blocked_by_mixed_metrics": bool(mixed_metrics),
                "blocked_by_hidden_dynamics_missing": bool(hidden_dynamics_missing),
                "interpretable_for_ranking": False,
                "allowed_for_synthesis_only": True,
                "reason": "; ".join(reason_parts),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def has_mixed_metric_directions(
    *,
    success_delta: float,
    collision_delta: float,
    clearance_delta: float,
    return_delta: float,
) -> bool:
    beneficial = [
        success_delta > 1e-12,
        collision_delta < -1e-12,
        clearance_delta > 1e-12,
        return_delta > 1e-12,
    ]
    harmful = [
        success_delta < -1e-12,
        collision_delta > 1e-12,
        clearance_delta < -1e-12,
        return_delta < -1e-12,
    ]
    return any(beneficial) and any(harmful)


def build_calibration_gap_rows(
    *,
    source: dict[str, Any],
    spec_rows: list[Mapping[str, Any]],
    profile_rows: list[Mapping[str, Any]],
    task_family_rows: list[Mapping[str, Any]],
    comparison_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    episode_rows = source["episode_rows"]
    outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in episode_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in episode_rows)
    episode_count = len(episode_rows)
    offtrack_outcome = int(outcome_counts.get("off_track_noncollision_noncompletion", 0))
    offtrack_termination = int(termination_counts.get("off_track", 0))
    success_count = int(outcome_counts.get("success_obstacle_pass", 0))
    l3_reset_row = _one_profile_aggregate(source, "L3_reset_control_corrected")
    l3_online_row = _one_profile_aggregate(source, "L3_online_gru")
    reset_success = _float_or_zero(l3_reset_row.get("success_rate", 0.0))
    online_success = _float_or_zero(l3_online_row.get("success_rate", 0.0))
    l2_zero_success_delta_rows = [
        row
        for row in comparison_rows
        if str(row.get("comparison", "")).startswith("L2_window_")
        and _bool(row.get("blocked_by_current_tiled_zero_success_delta", False))
    ]
    rows = [
        gap(
            "global_offtrack_dominance",
            "outcome_dominance",
            "scenario_sampling_failure",
            f"outcome_offtrack={offtrack_outcome}/{episode_count} termination_offtrack={offtrack_termination}/{episode_count}",
            "offtrack share below 0.70 before aggregate interpretation",
            True,
            "route to task-quality repair or interpretable-slice audit before another public rollout",
        ),
        gap(
            "success_support_thin",
            "outcome_support",
            "metric_artifact",
            f"success={success_count}/{episode_count}",
            "sufficient multi-profile success support before controller-family ranking",
            True,
            "materialize support slices and avoid winner selection",
        ),
        gap(
            "hidden_dynamics_bucket_missing",
            "instrumentation",
            "metric_artifact",
            f"hidden_rows={len(source['hidden_dynamics_aggregate_rows'])} profile_hidden_rows={len(source['profile_hidden_dynamics_worst_bucket_rows'])}",
            "non-empty hidden_dynamics_bucket rows for robustness interpretation",
            True,
            "add explicit bucket materialization in a later instrumentation route if hidden-dynamics robustness is needed",
        ),
        gap(
            "reset_control_ambiguity",
            "comparison_interpretability",
            "proof_washout",
            f"L3_reset_success={reset_success:.6f} L3_online_success={online_success:.6f}",
            "reset-control comparison not stronger on raw success before GRU-positive interpretation",
            reset_success >= online_success,
            "treat reset-control result as blocker or conditional self-ID evidence, not GRU proof",
        ),
        gap(
            "l2_current_tiled_zero_success_delta",
            "comparison_interpretability",
            "proof_washout",
            f"zero_success_delta_rows={len(l2_zero_success_delta_rows)}",
            "current-tiled controls separated before current-response sufficiency claims",
            len(l2_zero_success_delta_rows) > 0,
            "keep L2 normal versus current-tiled rows diagnostic-only",
        ),
        gap(
            "role_semantics_missing",
            "task_quality",
            "scenario_sampling_failure",
            "M2677 rows expose task_family/source_edge but no role semantics field",
            "role/task-quality semantics present before paper interpretation",
            True,
            "route to task-quality outcome-semantics planning before paper claims",
        ),
        gap(
            "private_holdout_absent",
            "generalization",
            "objective_overfit",
            "private_holdout_used=false for public M2677/M2680 route",
            "private holdout or fresh distribution before generalization claim",
            True,
            "keep public Route B rows as diagnostic only",
        ),
        gap(
            "paper_verdict_missing",
            "claim_boundary",
            "proof_washout",
            "M2680 materializes blockers and no verdict fields",
            "audited proof/generalization evidence before paper verdict",
            True,
            "route to M2681 result audit before any interpretation plan",
        ),
    ]
    spec_blocked = sum(1 for row in spec_rows if _bool(row.get("outcome_dominance_blocked", False)))
    profile_blocked = sum(1 for row in profile_rows if _bool(row.get("outcome_dominance_blocked", False)))
    family_blocked = sum(1 for row in task_family_rows if _bool(row.get("outcome_dominance_blocked", False)))
    rows.append(
        gap(
            "slice_outcome_dominance_spread",
            "outcome_dominance",
            "scenario_sampling_failure",
            f"spec_blocked={spec_blocked}/{len(spec_rows)} profile_blocked={profile_blocked}/{len(profile_rows)} task_family_blocked={family_blocked}/{len(task_family_rows)}",
            "most slices not dominated by non-success outcomes",
            spec_blocked > 0 or profile_blocked > 0 or family_blocked > 0,
            "use blocked-slice panel to choose repair, stop, or interpretable-slice planning",
        )
    )
    return rows


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    rows = [
        claim("calibration_materialization", "artifact", True, artifacts_present, "summary and calibration CSV rows"),
        claim("spec_outcome_dominance_rows", "artifact", True, artifacts_present, "72 spec calibration rows"),
        claim("profile_outcome_dominance_rows", "artifact", True, artifacts_present, "12 profile calibration rows"),
        claim("task_family_outcome_dominance_rows", "artifact", True, artifacts_present, "T4/T5 task-family rows"),
        claim("comparison_interpretability_rows", "artifact", True, artifacts_present, "11 diagnostic comparison rows"),
        claim("calibration_gap_rows", "artifact", True, artifacts_present, "blocker/gap materialization rows"),
        claim("claim_boundary_rows", "artifact", True, artifacts_present, "claim boundary CSV"),
        claim("gate_matrix", "artifact", True, artifacts_present, "gate matrix CSV"),
        claim("diagnostic_blocker_materialized", "diagnostic", True, True, "offtrack and hidden-dynamics blockers recorded"),
        claim("follow_up_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2681 result audit manifest"),
    ]
    blocked = [
        ("reset_or_rollout_execution", "execution", "future execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("replay_or_validation", "execution", "future replay or validation manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in public calibration"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("comparison_delta_verdict", "verdict", "future result audit and interpretation milestone"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_response_sufficiency_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    spec_rows: list[Mapping[str, Any]],
    profile_rows: list[Mapping[str, Any]],
    task_family_rows: list[Mapping[str, Any]],
    comparison_rows: list[Mapping[str, Any]],
    calibration_gap_rows: list[Mapping[str, Any]],
    claim_rows: list[Mapping[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    source_summary = source["summary"]
    episode_rows = source["episode_rows"]
    source_present = all(source["source_exists"].values())
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2680"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2680"])]
    return [
        gate("source_artifacts_present", "lineage", source_present, source["source_exists"], "all M2677 source artifacts and M2681 follow-up manifest present", "lineage_invalid"),
        gate("m2677_status_pass", "lineage", _bool(source_summary.get("status_pass", False)), source_summary.get("status_pass", None), True, "lineage_invalid"),
        gate("episode_rows_complete", "lineage", len(episode_rows) == TARGET_EPISODE_COUNT, len(episode_rows), TARGET_EPISODE_COUNT, "lineage_invalid"),
        gate("profile_count_complete", "lineage", len({str(row.get("profile_name", "")) for row in episode_rows}) == TARGET_PROFILE_COUNT, len({str(row.get("profile_name", "")) for row in episode_rows}), TARGET_PROFILE_COUNT, "lineage_invalid"),
        gate("spec_count_complete", "lineage", len({str(row.get("task_source_id", "")) for row in episode_rows}) == TARGET_SPEC_COUNT, len({str(row.get("task_source_id", "")) for row in episode_rows}), TARGET_SPEC_COUNT, "lineage_invalid"),
        gate("selected_metrics_finite", "metric", selected_metrics_are_finite(episode_rows), "episode selected metrics finite", "episode selected metrics finite", "metric_artifact"),
        gate("spec_rows_complete", "artifact", len(spec_rows) == TARGET_SPEC_COUNT, len(spec_rows), TARGET_SPEC_COUNT, "metric_artifact"),
        gate("profile_rows_complete", "artifact", len(profile_rows) == TARGET_PROFILE_COUNT, len(profile_rows), TARGET_PROFILE_COUNT, "metric_artifact"),
        gate("task_family_rows_present", "artifact", len(task_family_rows) >= 2, len(task_family_rows), ">=2 public task families", "metric_artifact"),
        gate("comparison_rows_complete", "artifact", len(comparison_rows) == TARGET_COMPARISON_COUNT, len(comparison_rows), TARGET_COMPARISON_COUNT, "metric_artifact"),
        gate("calibration_gap_rows_present", "artifact", len(calibration_gap_rows) >= 8, len(calibration_gap_rows), ">=8 blocker rows", "metric_artifact"),
        gate("offtrack_dominance_recorded", "metric_artifact", any(row["gap_id"] == "global_offtrack_dominance" for row in calibration_gap_rows), "recorded", "recorded", "metric_artifact"),
        gate("hidden_dynamics_missing_recorded", "metric_artifact", any(row["gap_id"] == "hidden_dynamics_bucket_missing" for row in calibration_gap_rows), "recorded", "recorded", "metric_artifact"),
        gate("comparison_rows_diagnostic_only", "claim_boundary", comparison_rows and all(_bool(row.get("diagnostic_only_no_ranking_claim", False)) and not _bool(row.get("interpretable_for_ranking", True)) for row in comparison_rows), "all diagnostic and non-ranking", "all diagnostic and non-ranking", "proof_washout"),
        gate("no_environment_execution_or_policy_action", "execution_guardrail", True, "M2680 reads CSV/JSON only", "no reset step rollout replay validation policy action", "objective_overfit"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claim_rows) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claim_rows), f"allowed={len(allowed_claim_rows)} blocked={len(blocked_claim_rows)}", "allowed claims true and blocked claims not made", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    source: dict[str, Any],
    output_dir: Path,
    paths: dict[str, Path],
    spec_rows: list[Mapping[str, Any]],
    profile_rows: list[Mapping[str, Any]],
    task_family_rows: list[Mapping[str, Any]],
    comparison_rows: list[Mapping[str, Any]],
    calibration_gap_rows: list[Mapping[str, Any]],
    claim_rows: list[Mapping[str, Any]],
    gate_rows: list[Mapping[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    episode_rows = source["episode_rows"]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    outcome_counts = dict(sorted(Counter(str(row.get("outcome_bucket", "")) for row in episode_rows).items()))
    termination_counts = dict(sorted(Counter(str(row.get("termination_reason", "")) for row in episode_rows).items()))
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2680"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2680"])]
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": _result_class(status_pass),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m2677_dir": str(source["paths"]["summary"].parent),
        "source_m2677_status_pass": _bool(source["summary"].get("status_pass", False)),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "episode_count": len(episode_rows),
        "target_episode_count": TARGET_EPISODE_COUNT,
        "profile_count": len({str(row.get("profile_name", "")) for row in episode_rows}),
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({str(row.get("task_source_id", "")) for row in episode_rows}),
        "target_spec_count": TARGET_SPEC_COUNT,
        "task_family_count": len({str(row.get("task_family", "")) for row in episode_rows}),
        "comparison_source_row_count": len(source["comparison_aggregate_rows"]),
        "target_comparison_count": TARGET_COMPARISON_COUNT,
        "outcome_counts": outcome_counts,
        "termination_reason_counts": termination_counts,
        "success_count": int(outcome_counts.get("success_obstacle_pass", 0)),
        "collision_count": int(outcome_counts.get("collision_failure", 0)),
        "offtrack_outcome_count": int(outcome_counts.get("off_track_noncollision_noncompletion", 0)),
        "termination_offtrack_count": int(termination_counts.get("off_track", 0)),
        "global_outcome_dominance_blocked": global_offtrack_blocked(episode_rows),
        "hidden_dynamics_bucket_missing": hidden_dynamics_missing(source),
        "selected_metrics_finite": selected_metrics_are_finite(episode_rows),
        "spec_outcome_dominance_row_count": len(spec_rows),
        "profile_outcome_dominance_row_count": len(profile_rows),
        "task_family_outcome_dominance_row_count": len(task_family_rows),
        "comparison_interpretability_row_count": len(comparison_rows),
        "calibration_gap_row_count": len(calibration_gap_rows),
        "spec_outcome_dominance_blocked_count": sum(_bool(row["outcome_dominance_blocked"]) for row in spec_rows),
        "profile_outcome_dominance_blocked_count": sum(_bool(row["outcome_dominance_blocked"]) for row in profile_rows),
        "task_family_outcome_dominance_blocked_count": sum(_bool(row["outcome_dominance_blocked"]) for row in task_family_rows),
        "comparison_ranking_interpretable_count": sum(_bool(row["interpretable_for_ranking"]) for row in comparison_rows),
        "comparison_synthesis_only_count": sum(_bool(row["allowed_for_synthesis_only"]) for row in comparison_rows),
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(blocked_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_started": False,
        "environment_step_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_validation_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_detected": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "promoted": False,
        "success_rate_verdict_claim_made": False,
        "comparison_delta_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2680 Paper Route History Vs Current Response Task Quality Outcome Dominance Calibration Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`",
            f"- source M2677 status pass: {summary['source_m2677_status_pass']}",
            f"- summary: `{summary['paths']['summary']}`",
            f"- spec rows: `{summary['paths']['spec_outcome_dominance_rows']}`",
            f"- profile rows: `{summary['paths']['profile_outcome_dominance_rows']}`",
            f"- task-family rows: `{summary['paths']['task_family_outcome_dominance_rows']}`",
            f"- comparison interpretability rows: `{summary['paths']['comparison_interpretability_rows']}`",
            f"- calibration gap rows: `{summary['paths']['calibration_gap_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- run state: `{summary['paths']['run_state']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Materialized Calibration Surface",
            "",
            f"- episode rows consumed: {summary['episode_count']} / {summary['target_episode_count']}",
            f"- profiles covered: {summary['profile_count']} / {summary['target_profile_count']}",
            f"- specs covered: {summary['spec_count']} / {summary['target_spec_count']}",
            f"- task families covered: {summary['task_family_count']}",
            f"- comparison rows covered: {summary['comparison_interpretability_row_count']} / {summary['target_comparison_count']}",
            f"- spec outcome-dominance rows: {summary['spec_outcome_dominance_row_count']}",
            f"- profile outcome-dominance rows: {summary['profile_outcome_dominance_row_count']}",
            f"- task-family outcome-dominance rows: {summary['task_family_outcome_dominance_row_count']}",
            f"- calibration gap rows: {summary['calibration_gap_row_count']}",
            f"- selected metrics finite: {summary['selected_metrics_finite']}",
            "",
            "## Blockers Recorded",
            "",
            f"- success count: {summary['success_count']}",
            f"- collision count: {summary['collision_count']}",
            f"- offtrack outcome count: {summary['offtrack_outcome_count']}",
            f"- offtrack termination count: {summary['termination_offtrack_count']}",
            f"- global outcome dominance blocked: {summary['global_outcome_dominance_blocked']}",
            f"- hidden-dynamics bucket missing: {summary['hidden_dynamics_bucket_missing']}",
            f"- spec dominance blocked rows: {summary['spec_outcome_dominance_blocked_count']}",
            f"- profile dominance blocked rows: {summary['profile_outcome_dominance_blocked_count']}",
            f"- task-family dominance blocked rows: {summary['task_family_outcome_dominance_blocked_count']}",
            f"- comparison rows interpretable for ranking: {summary['comparison_ranking_interpretable_count']}",
            f"- comparison rows allowed for synthesis only: {summary['comparison_synthesis_only_count']}",
            "",
            "## Guardrails",
            "",
            f"- environment reset started: {summary['environment_reset_started']}",
            f"- environment rollout started: {summary['environment_rollout_started']}",
            f"- policy action executed: {summary['policy_action_executed']}",
            f"- measured validation started: {summary['measured_validation_started']}",
            f"- training started: {summary['training_started']}",
            f"- replay started: {summary['replay_started']}",
            f"- PPO used: {summary['ppo_used']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- profile-specific tuning: {summary['profile_specific_tuning']}",
            f"- actor input contract changed: {summary['actor_input_contract_changed']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- controller-family ranking claim made: {summary['controller_family_ranking_claim_made']}",
            f"- success-rate verdict claim made: {summary['success_rate_verdict_claim_made']}",
            f"- paper-level claim made: {summary['paper_level_claim_made']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "No-rollout calibration materialization and diagnostic blocker localization from existing M2677 rows.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2680 passes only if the calibration artifacts are complete and the",
            "claim boundary remains clean. It does not make M2677 interpretable",
            "as controller-family ranking, paper evidence, current-sim verdict,",
            "finite-window-vs-GRU evidence, current-response sufficiency, high-",
            "fidelity validation, full ideal driver completion, or self-ID.",
            "",
        ]
    )


def selected_metrics_are_finite(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        for metric in SELECTED_METRICS:
            if not math.isfinite(_float_or_nan(row.get(metric, "nan"))):
                return False
    return True


def global_offtrack_blocked(rows: list[Mapping[str, Any]]) -> bool:
    if not rows:
        return True
    offtrack = sum(1 for row in rows if str(row.get("termination_reason", "")) == "off_track")
    return offtrack / len(rows) >= 0.70


def hidden_dynamics_missing(source: Mapping[str, Any]) -> bool:
    if source.get("hidden_dynamics_aggregate_rows") or source.get("profile_hidden_dynamics_worst_bucket_rows"):
        return False
    rows = source.get("episode_rows", [])
    return not any(str(row.get("hidden_dynamics_bucket", "")).strip() for row in rows)


def _group_rows(
    rows: Iterable[Mapping[str, Any]],
    keys: Sequence[str],
) -> dict[tuple[str, ...], list[Mapping[str, Any]]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return dict(sorted(groups.items()))


def value_for_key(keys: Sequence[str], values: Sequence[str], key: str) -> str:
    if key not in keys:
        return ""
    return str(values[list(keys).index(key)])


def _one_profile_aggregate(source: Mapping[str, Any], profile_name: str) -> dict[str, Any]:
    for row in source.get("profile_aggregate_rows", []):
        if str(row.get("profile_name", "")) == profile_name:
            return dict(row)
    return {}


def _result_class(status_pass: bool) -> str:
    if status_pass:
        return "paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration_pass"
    return "paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration_fail"


def claim(
    claim_id: str,
    family: str,
    allowed: bool,
    claim_made: bool,
    evidence: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim_family": family,
        "allowed_in_m2680": bool(allowed),
        "claim_made": bool(claim_made),
        "status_pass": bool(claim_made) if allowed else not bool(claim_made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def gap(
    gap_id: str,
    family: str,
    failure_type: str,
    observed: Any,
    expected: Any,
    blocks_interpretation: bool,
    next_action: str,
) -> dict[str, Any]:
    return {
        "gap_id": gap_id,
        "gap_family": family,
        "failure_type": failure_type,
        "observed": observed,
        "threshold_or_expected": expected,
        "blocks_interpretation": bool(blocks_interpretation),
        "recommended_next_action": next_action,
        "claim_boundary": CLAIM_SCOPE,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_or_zero(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _float_or_zero(value: Any) -> float:
    value_float = _float_or_nan(value)
    return value_float if math.isfinite(value_float) else 0.0


def _float_or_nan(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2677-dir", type=Path, default=DEFAULT_M2677_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_task_quality_outcome_dominance_calibration(
        m2677_dir=args.m2677_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"spec_rows={summary['spec_outcome_dominance_row_count']}")
    print(f"profile_rows={summary['profile_outcome_dominance_row_count']}")
    print(f"comparison_rows={summary['comparison_interpretability_row_count']}")
    print(f"next={summary['next_blocker']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
