"""Artifact-only support audit for current-sim scenario/task quality."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json


DEFAULT_EPISODE_ROWS = [
    Path("runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv"),
    Path("runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv"),
    Path(
        "runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv"
    ),
]
DEFAULT_TRAINING_MATRICES = [
    Path("runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv"),
    Path("runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/training_matrix.csv"),
    Path("runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv"),
    Path("runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv"),
]
DEFAULT_OUTPUT_DIR = Path("runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit")
DEFAULT_NEXT_BLOCKER = "m2275-paper-route-current-sim-scenario-task-quality-support-audit-result-audit"

ROLE_FAMILIES = {
    "R0_stable_avoidable": {
        "labels": {"aes_feasible", "stable_avoidable", "R0_stable_avoidable"},
        "description": "Stable steering/braking avoidance role.",
    },
    "R1_aeb_infeasible_stable_aes": {
        "labels": {"aeb_infeasible_stable_aes", "stable_aes_required", "R1_aeb_infeasible_stable_aes"},
        "description": "AEB insufficient, stable AES sufficient.",
    },
    "R2_handling_limit_drift_capable_avoidance": {
        "labels": {"drift_required", "handling_limit", "R2_handling_limit_drift_capable_avoidance"},
        "description": "Handling-limit or drift-capable avoidance role.",
    },
    "R3_recovery_after_limit": {
        "labels": {"recovery_after_limit", "post_limit_recovery", "R3_recovery_after_limit"},
        "description": "Post-maneuver recovery role.",
    },
    "R4_unavoidable_mitigation": {
        "labels": {"unavoidable", "mitigation", "R4_unavoidable_mitigation"},
        "description": "Unavoidable collision mitigation role.",
    },
    "R5_hidden_dynamics_robustness": {
        "labels": {"hidden_dynamics_robustness", "dynamics_robustness", "R5_hidden_dynamics_robustness"},
        "description": "Hidden dynamics variation support role.",
    },
}

SCENARIO_AXES = {
    "initial_speed_bucket": ("speed_mean",),
    "obstacle_longitudinal_timing_bucket": ("obstacle_distance", "obstacle_x", "obstacle_spawn_distance"),
    "obstacle_lateral_offset_bucket": ("obstacle_lateral_offset", "obstacle_y"),
    "road_width_bucket": ("track_width",),
    "road_curvature_bucket": ("left_curve_steps", "right_curve_steps", "near_zero_steps"),
    "friction_bucket": ("initial_mu", "mu"),
    "brake_scale_bucket": ("brake_scale",),
    "actuator_lag_bucket": ("steer_tau_scale", "drive_tau_scale"),
    "vehicle_mass_or_inertia_bucket": ("mass_scale", "inertia_scale", "mass"),
    "recovery_window_bucket": ("first_recovery_time_s", "recovery_time_proxy"),
    "role_family": ("obstacle_label",),
}

METRICS = {
    "success_rate": ("outcome_bucket", "obstacle_completed"),
    "collision_rate": ("collision", "outcome_bucket"),
    "offtrack_rate": ("termination_reason", "outcome_bucket"),
    "spin_or_high_sideslip_rate": ("high_sideslip_fraction", "max_abs_beta", "max_abs_yaw_rate"),
    "clearance_margin_tail": ("min_clearance_margin",),
    "impact_speed_or_mitigation_proxy": ("impact_speed_proxy", "collision_mitigation_score"),
    "recovery_success_rate": ("recovery_success", "controlled_drift_recovery_success"),
    "post_maneuver_stability_rate": ("max_abs_beta", "high_sideslip_fraction", "recovery_success"),
    "control_smoothness": ("action_rate_mean",),
    "role_completion_rate": ("obstacle_label", "obstacle_completed", "outcome_bucket"),
}

DIAGNOSTIC_METRICS = {
    "termination_reason_histogram": ("termination_reason",),
    "offtrack_timing_bucket": ("time_to_first_off_track_s",),
    "offtrack_severity_bucket": ("max_off_track_overshoot", "off_track_severity_proxy"),
    "clearance_risk_bucket": ("min_clearance_margin",),
    "profile_seed_stability": ("profile_name", "seed_id", "selected_readiness_floor_pass"),
    "scenario_axis_coverage": tuple(sorted({column for columns in SCENARIO_AXES.values() for column in columns})),
    "max_source_dominance": ("profile_name", "seed_id", "episode_seed"),
    "missing_label_rate": ("obstacle_label",),
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if np.isfinite(parsed) else None


def _panel_name(path: Path | str) -> str:
    text = str(path)
    if "m2244" in text:
        return "baseline_m2244"
    if "m2253" in text:
        return "generic_m2253"
    if "m2265" in text:
        return "targeted_m2265"
    return Path(path).parent.name or Path(path).stem


def _matrix_name(path: Path | str) -> str:
    text = str(path)
    if "m2227" in text:
        return "short_v0_m2227"
    if "m2233" in text:
        return "medium_v1_m2233"
    if "m2248" in text:
        return "generic_reward_m2248"
    if "m2259" in text:
        return "targeted_containment_m2259"
    return Path(path).parent.name or Path(path).stem


def _annotate(rows: Sequence[Mapping[str, Any]], panel: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["panel"] = panel
        item["profile_seed"] = f"{item.get('profile_name', '')}|{item.get('seed_id', '')}"
        output.append(item)
    return output


def _available_columns(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(str(key) for key in row)
    return columns


def _non_empty_count(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> int:
    return sum(1 for row in rows if any(str(row.get(column, "")).strip() for column in columns))


def _finite_count(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> int:
    return sum(1 for row in rows if any(_float_or_none(row.get(column)) is not None for column in columns))


def _role_for_label(label: str) -> str | None:
    normalized = str(label).strip()
    for role, spec in ROLE_FAMILIES.items():
        if normalized in spec["labels"]:
            return role
    return None


def _role_support_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_role: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    unknown_count = 0
    for row in episode_rows:
        role = _role_for_label(str(row.get("obstacle_label", "")))
        if role is None:
            unknown_count += 1
        else:
            by_role[role].append(row)

    hidden_columns = ("mu", "initial_mu", "mass_scale", "inertia_scale", "brake_scale", "steer_tau_scale")
    hidden_support = _finite_count(episode_rows, hidden_columns)
    recovery_support = sum(
        1
        for row in episode_rows
        if _bool(row.get("recovery_success"))
        or _bool(row.get("controlled_drift_recovery_success"))
        or (_float_or_none(row.get("high_sideslip_fraction")) or 0.0) > 0.05
    )

    rows: list[dict[str, Any]] = []
    for role, spec in ROLE_FAMILIES.items():
        role_rows = by_role.get(role, [])
        support_status = "present_label" if role_rows else "missing"
        evidence_source = "obstacle_label"
        row_count = len(role_rows)
        if role == "R3_recovery_after_limit" and not role_rows and recovery_support:
            support_status = "proxy_present_not_role_label"
            evidence_source = "recovery/high_sideslip metrics"
            row_count = recovery_support
        if role == "R5_hidden_dynamics_robustness" and not role_rows and hidden_support:
            support_status = "proxy_present_not_role_label"
            evidence_source = "hidden dynamics diagnostic columns"
            row_count = hidden_support
        panels = {str(row.get("panel", "")) for row in role_rows}
        profile_seeds = {str(row.get("profile_seed", "")) for row in role_rows}
        rows.append(
            {
                "role_family": role,
                "description": spec["description"],
                "support_status": support_status,
                "evidence_source": evidence_source,
                "row_count": row_count,
                "panel_count": len(panels),
                "profile_seed_count": len(profile_seeds),
                "safe_for_training_claim": support_status == "present_label" and row_count >= 64 and len(profile_seeds) >= 3,
                "notes": "explicit role label support" if support_status == "present_label" else "needs explicit scenario family support",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    if unknown_count:
        rows.append(
            {
                "role_family": "unknown_or_unmapped",
                "description": "Rows whose obstacle_label cannot be mapped to M2273 roles.",
                "support_status": "unmapped_label",
                "evidence_source": "obstacle_label",
                "row_count": unknown_count,
                "panel_count": "",
                "profile_seed_count": "",
                "safe_for_training_claim": False,
                "notes": "label mapping must be extended before claims",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return rows


def _axis_support_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    columns = _available_columns(episode_rows)
    total = len(episode_rows)
    rows: list[dict[str, Any]] = []
    for axis, axis_columns in SCENARIO_AXES.items():
        present_columns = [column for column in axis_columns if column in columns]
        finite_count = _finite_count(episode_rows, present_columns)
        non_empty_count = _non_empty_count(episode_rows, present_columns)
        if not present_columns:
            status = "missing"
        elif axis in {"obstacle_longitudinal_timing_bucket", "obstacle_lateral_offset_bucket"}:
            status = "missing_direct_axis"
        elif finite_count == total or non_empty_count == total:
            status = "present"
        else:
            status = "partial"
        values = Counter()
        for row in episode_rows:
            key = "|".join(str(row.get(column, "")) for column in present_columns)
            if key.strip("|"):
                values[key] += 1
        rows.append(
            {
                "axis": axis,
                "candidate_columns": "|".join(axis_columns),
                "present_columns": "|".join(present_columns),
                "support_status": status,
                "non_empty_count": non_empty_count,
                "finite_count": finite_count,
                "total_rows": total,
                "coverage_rate": non_empty_count / max(1, total),
                "unique_value_count": len(values),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return rows


def _metric_coverage_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    columns = _available_columns(episode_rows)
    rows: list[dict[str, Any]] = []
    for group, metrics in (("primary", METRICS), ("diagnostic", DIAGNOSTIC_METRICS)):
        for metric, metric_columns in metrics.items():
            present_columns = [column for column in metric_columns if column in columns]
            non_empty_count = _non_empty_count(episode_rows, present_columns)
            support_status = "present" if present_columns and non_empty_count > 0 else "missing"
            rows.append(
                {
                    "metric_group": group,
                    "metric": metric,
                    "candidate_columns": "|".join(metric_columns),
                    "present_columns": "|".join(present_columns),
                    "support_status": support_status,
                    "non_empty_count": non_empty_count,
                    "total_rows": len(episode_rows),
                    "coverage_rate": non_empty_count / max(1, len(episode_rows)),
                    "diagnostic_only": True,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return rows


def _readiness_rows(
    role_rows: Sequence[Mapping[str, Any]],
    axis_rows: Sequence[Mapping[str, Any]],
    metric_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    explicit_roles = [row for row in role_rows if row.get("support_status") == "present_label"]
    complete_roles = [row for row in explicit_roles if int(row.get("row_count", 0) or 0) >= 64]
    present_or_proxy_roles = [row for row in role_rows if row.get("support_status") in {"present_label", "proxy_present_not_role_label"}]
    present_axes = [row for row in axis_rows if row.get("support_status") == "present"]
    metric_present = [row for row in metric_rows if row.get("support_status") == "present" and row.get("metric_group") == "primary"]
    return [
        {
            "floor": "role_family_label_completeness",
            "required": len(ROLE_FAMILIES),
            "actual": len(explicit_roles),
            "gap": len(ROLE_FAMILIES) - len(explicit_roles),
            "passed": len(explicit_roles) == len(ROLE_FAMILIES),
            "notes": "requires explicit role labels, not only proxies",
        },
        {
            "floor": "role_family_min_public_rows_64",
            "required": len(ROLE_FAMILIES),
            "actual": len(complete_roles),
            "gap": len(ROLE_FAMILIES) - len(complete_roles),
            "passed": len(complete_roles) == len(ROLE_FAMILIES),
            "notes": "all role families need >=64 public diagnostic rows before training claims",
        },
        {
            "floor": "role_family_present_or_proxy_support",
            "required": len(ROLE_FAMILIES),
            "actual": len(present_or_proxy_roles),
            "gap": len(ROLE_FAMILIES) - len(present_or_proxy_roles),
            "passed": len(present_or_proxy_roles) == len(ROLE_FAMILIES),
            "notes": "proxy support is diagnostic only and not enough for training claims",
        },
        {
            "floor": "scenario_axis_direct_support",
            "required": len(SCENARIO_AXES),
            "actual": len(present_axes),
            "gap": len(SCENARIO_AXES) - len(present_axes),
            "passed": len(present_axes) == len(SCENARIO_AXES),
            "notes": "missing direct obstacle timing/lateral axes blocks benchmark-pack claims",
        },
        {
            "floor": "primary_metric_coverage",
            "required": len(METRICS),
            "actual": len(metric_present),
            "gap": len(METRICS) - len(metric_present),
            "passed": len(metric_present) == len(METRICS),
            "notes": "all primary metrics must be computable per role",
        },
    ]


def _support_gap_rows(
    role_rows: Sequence[Mapping[str, Any]],
    axis_rows: Sequence[Mapping[str, Any]],
    metric_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in role_rows:
        if row.get("support_status") != "present_label":
            rows.append(
                {
                    "gap_type": "role_family",
                    "name": row["role_family"],
                    "support_status": row["support_status"],
                    "severity": "high" if row["support_status"] == "missing" else "medium",
                    "recommended_fix": "add explicit scenario role labels and support rows",
                }
            )
    for row in axis_rows:
        if row.get("support_status") != "present":
            rows.append(
                {
                    "gap_type": "scenario_axis",
                    "name": row["axis"],
                    "support_status": row["support_status"],
                    "severity": "high" if row["support_status"] == "missing" else "medium",
                    "recommended_fix": "instrument scenario generation/config metadata",
                }
            )
    for row in metric_rows:
        if row.get("support_status") != "present":
            rows.append(
                {
                    "gap_type": "metric",
                    "name": row["metric"],
                    "support_status": row["support_status"],
                    "severity": "medium",
                    "recommended_fix": "add metric column or artifact computation",
                }
            )
    return rows


def _matrix_rows(training_matrices: Sequence[Path | str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in training_matrices:
        if not Path(path).exists():
            continue
        matrix_name = _matrix_name(path)
        for row in read_csv_rows(path):
            item = dict(row)
            item["matrix_name"] = matrix_name
            rows.append(item)
    return rows


def _contract_rows(matrix_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in matrix_rows:
        grouped[str(row.get("matrix_name", ""))].append(row)
    output: list[dict[str, Any]] = []
    for name, rows in sorted(grouped.items()):
        output.append(
            {
                "matrix_name": name,
                "row_count": len(rows),
                "profile_count": len({str(row.get("profile_name", "")) for row in rows}),
                "seed_count": len({str(row.get("seed_id", "")) for row in rows}),
                "hidden_oracle_actor_input_rows": sum(1 for row in rows if _bool(row.get("uses_hidden_oracle_actor_inputs"))),
                "wheel_or_slip_actor_input_rows": sum(1 for row in rows if _bool(row.get("uses_wheel_or_slip_inputs"))),
                "reference_or_ttc_actor_input_rows": sum(1 for row in rows if _bool(row.get("uses_reference_or_ttc_inputs"))),
                "training_started_rows": sum(1 for row in rows if _bool(row.get("training_started"))),
                "policy_action_executed_rows": sum(1 for row in rows if _bool(row.get("policy_action_executed"))),
                "ranking_admissible_rows": sum(1 for row in rows if _bool(row.get("ranking_admissible"))),
                "winner_selected_rows": sum(1 for row in rows if _bool(row.get("winner_selected"))),
            }
        )
    return output


def _route_rows(
    *,
    readiness_rows: Sequence[Mapping[str, Any]],
    gap_rows: Sequence[Mapping[str, Any]],
    contract_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    high_role_gaps = sum(1 for row in gap_rows if row.get("gap_type") == "role_family" and row.get("severity") == "high")
    high_axis_gaps = sum(1 for row in gap_rows if row.get("gap_type") == "scenario_axis" and row.get("severity") == "high")
    metric_gaps = sum(1 for row in gap_rows if row.get("gap_type") == "metric")
    contract_violations = sum(
        int(row.get("hidden_oracle_actor_input_rows", 0) or 0)
        + int(row.get("wheel_or_slip_actor_input_rows", 0) or 0)
        + int(row.get("reference_or_ttc_actor_input_rows", 0) or 0)
        for row in contract_rows
    )

    if contract_violations:
        route = "contract_artifact_repair"
        reason = "training matrices contain actor-contract support violations"
    elif high_role_gaps or high_axis_gaps:
        route = "scenario_task_family_generation_design"
        reason = "role-family or direct scenario-axis support is missing"
    elif metric_gaps:
        route = "metric_instrumentation_repair_design"
        reason = "role support exists but some metrics are missing"
    elif not all(_bool(row.get("passed")) for row in readiness_rows):
        route = "readiness_floor_calibration_design"
        reason = "support exists but readiness floors are not met"
    else:
        route = "role_specific_benchmark_pack_materialization_design"
        reason = "support and metric coverage are complete enough for materialization design"
    return [
        {
            "route": route,
            "admitted": True,
            "support_reason": reason,
            "high_role_gap_count": high_role_gaps,
            "high_axis_gap_count": high_axis_gaps,
            "metric_gap_count": metric_gaps,
            "contract_violation_count": contract_violations,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
    ]


def run_support_audit(
    *,
    episode_rows: Sequence[Path | str] = DEFAULT_EPISODE_ROWS,
    training_matrices: Sequence[Path | str] = DEFAULT_TRAINING_MATRICES,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    missing_inputs = [str(path) for path in list(episode_rows) + list(training_matrices) if not Path(path).exists()]
    annotated_rows: list[dict[str, Any]] = []
    for path in episode_rows:
        if not Path(path).exists():
            continue
        annotated_rows.extend(_annotate(read_csv_rows(path), _panel_name(path)))
    matrices = _matrix_rows(training_matrices)

    role_rows = _role_support_rows(annotated_rows)
    axis_rows = _axis_support_rows(annotated_rows)
    metric_rows = _metric_coverage_rows(annotated_rows)
    readiness_rows = _readiness_rows(role_rows, axis_rows, metric_rows)
    gap_rows = _support_gap_rows(role_rows, axis_rows, metric_rows)
    contract_rows = _contract_rows(matrices)
    route_rows = _route_rows(readiness_rows=readiness_rows, gap_rows=gap_rows, contract_rows=contract_rows)

    write_csv_rows(output / "role_support.csv", role_rows)
    write_csv_rows(output / "scenario_axis_support.csv", axis_rows)
    write_csv_rows(output / "metric_coverage.csv", metric_rows)
    write_csv_rows(output / "readiness_floor_gap.csv", readiness_rows)
    write_csv_rows(output / "support_gap_report.csv", gap_rows)
    write_csv_rows(output / "training_matrix_contract_support.csv", contract_rows)
    write_csv_rows(output / "redesign_routes.csv", route_rows)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "ppo_started": False,
        "replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "winner_selected": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    role_missing_count = sum(1 for row in role_rows if row.get("support_status") == "missing")
    direct_axis_missing_count = sum(1 for row in axis_rows if row.get("support_status") in {"missing", "missing_direct_axis"})
    result_class = (
        "current_sim_scenario_task_quality_support_audit_pass"
        if not missing_inputs and route_rows and guardrail_violation_count == 0
        else "current_sim_scenario_task_quality_support_audit_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "episode_row_inputs": [str(path) for path in episode_rows],
        "training_matrix_inputs": [str(path) for path in training_matrices],
        "output_dir": str(output),
        "episode_row_count": len(annotated_rows),
        "training_matrix_row_count": len(matrices),
        "missing_input_count": len(missing_inputs),
        "missing_inputs": missing_inputs,
        "role_family_count": len(ROLE_FAMILIES),
        "explicit_role_family_count": sum(1 for row in role_rows if row.get("support_status") == "present_label"),
        "role_missing_count": role_missing_count,
        "direct_axis_missing_count": direct_axis_missing_count,
        "primary_metric_missing_count": sum(
            1 for row in metric_rows if row.get("metric_group") == "primary" and row.get("support_status") != "present"
        ),
        "readiness_floor_pass_count": sum(1 for row in readiness_rows if _bool(row.get("passed"))),
        "readiness_floor_count": len(readiness_rows),
        "primary_route": route_rows[0]["route"] if route_rows else "",
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "role_support": str(output / "role_support.csv"),
            "scenario_axis_support": str(output / "scenario_axis_support.csv"),
            "metric_coverage": str(output / "metric_coverage.csv"),
            "readiness_floor_gap": str(output / "readiness_floor_gap.csv"),
            "support_gap_report": str(output / "support_gap_report.csv"),
            "training_matrix_contract_support": str(output / "training_matrix_contract_support.csv"),
            "redesign_routes": str(output / "redesign_routes.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, action="append", default=None)
    parser.add_argument("--training-matrix", type=Path, action="append", default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_support_audit(
        episode_rows=args.episode_rows or DEFAULT_EPISODE_ROWS,
        training_matrices=args.training_matrix or DEFAULT_TRAINING_MATRICES,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"primary_route={summary['primary_route']}")
    print(f"result_class={summary['result_class']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
