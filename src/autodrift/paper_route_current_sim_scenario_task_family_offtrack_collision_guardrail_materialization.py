"""Materialize offtrack target and collision guardrail slices from M2295."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_ALL_SLICES = Path("runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/all_slices.csv")
DEFAULT_DOMINANT_SLICES = Path(
    "runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv"
)
DEFAULT_ROUTE_RECOMMENDATION = Path(
    "runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/route_recommendation.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail")
DEFAULT_NEXT_BLOCKER = "m2299-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-result-audit"

NON_PROFILE_AXES = {
    "termination_reason",
    "outcome_bucket",
    "role_family",
    "sampled_obstacle_label",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "hidden_dynamics_bucket",
}
PROFILE_AXES = {"profile_name", "profile_seed"}
PRIMARY_OFFTRACK_SLICES = {
    ("termination_reason", "off_track"),
    ("outcome_bucket", "off_track_noncollision_noncompletion"),
}
REQUIRED_PRIMARY_GUARDRAILS = {
    ("outcome_bucket", "collision_failure"),
    ("termination_reason", "obstacle_collision"),
    ("role_family", "R4_unavoidable_mitigation"),
}
OFFTRACK_THRESHOLD = 100
COLLISION_THRESHOLD = 50

MATERIALIZED_FIELDNAMES = [
    "slice_role",
    "axis",
    "group_key",
    "episode_count",
    "success_count",
    "success_rate",
    "failure_count",
    "failure_rate",
    "offtrack_count",
    "offtrack_rate",
    "collision_count",
    "collision_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_failure_count",
    "other_failure_rate",
    "mean_return",
    "mean_steps",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_high_sideslip_fraction",
    "mean_action_rate",
    "dominant_failure_mode",
    "dominant_failure_count",
    "selection_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _int(row: Mapping[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _float(row: Mapping[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _axis_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("axis", "")), str(row.get("group_key", ""))


def _materialized_row(row: Mapping[str, Any], *, role: str, reason: str) -> dict[str, Any]:
    output = {field: row.get(field, "") for field in MATERIALIZED_FIELDNAMES}
    output.update(
        {
            "slice_role": role,
            "selection_reason": reason,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
    )
    return output


def offtrack_target_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = _axis_key(row)
        axis, _group = key
        if axis not in NON_PROFILE_AXES:
            continue
        dominant = str(row.get("dominant_failure_mode", ""))
        offtrack_count = _int(row, "offtrack_count")
        reason = ""
        if key in PRIMARY_OFFTRACK_SLICES:
            reason = "primary_offtrack_slice"
        elif dominant == "offtrack_dominated_failure" and offtrack_count >= OFFTRACK_THRESHOLD:
            reason = f"offtrack_dominated_count_ge_{OFFTRACK_THRESHOLD}"
        if reason and key not in seen:
            output.append(_materialized_row(row, role="offtrack_target", reason=reason))
            seen.add(key)
    return output


def collision_guardrail_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = _axis_key(row)
        axis, _group = key
        if axis not in NON_PROFILE_AXES:
            continue
        dominant = str(row.get("dominant_failure_mode", ""))
        collision_count = _int(row, "collision_count")
        reason = ""
        if key in REQUIRED_PRIMARY_GUARDRAILS:
            reason = "required_collision_guardrail"
        elif dominant == "collision_dominated_failure":
            reason = "collision_dominated_failure"
        elif collision_count >= COLLISION_THRESHOLD:
            reason = f"collision_count_ge_{COLLISION_THRESHOLD}"
        if reason and key not in seen:
            output.append(_materialized_row(row, role="collision_guardrail", reason=reason))
            seen.add(key)
    return output


def profile_diagnostic_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("axis", "")) in PROFILE_AXES and _int(row, "failure_count") > 0:
            output.append(_materialized_row(row, role="profile_diagnostic_only", reason="profile_axis_excluded"))
    return output


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "target_guardrail_materialization",
            "admissible": True,
            "reason": "materialization consumes existing slice artifacts without rerun",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "profile axes are diagnostic-only and excluded from targets and guardrails",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "target materialization is not measured repair evidence",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "materialization does not run the comparison protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "materialization does not test history necessity",
        },
    ]


def _repair_gate_spec(
    *,
    offtrack_targets: Sequence[Mapping[str, Any]],
    collision_guardrails: Sequence[Mapping[str, Any]],
    route_recommendation: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "generated_at_utc": utc_timestamp(),
        "route": str(route_recommendation[0].get("route", "")) if route_recommendation else "",
        "offtrack_target_policy": {
            "reduce_global_offtrack_count": True,
            "reduce_or_hold_target_slice_offtrack_count": True,
            "target_slice_count": len(offtrack_targets),
            "target_slices": [
                {"axis": row.get("axis", ""), "group_key": row.get("group_key", "")}
                for row in offtrack_targets
            ],
        },
        "collision_guardrail_policy": {
            "do_not_increase_global_collision_count": True,
            "do_not_increase_guardrail_slice_collision_count": True,
            "guardrail_slice_count": len(collision_guardrails),
            "guardrail_slices": [
                {"axis": row.get("axis", ""), "group_key": row.get("group_key", "")}
                for row in collision_guardrails
            ],
        },
        "completeness_policy": {
            "target_episode_count": 1080,
            "metadata_missing_count": 0,
            "metric_completeness_failure_count": 0,
            "guardrail_violation_count": 0,
        },
        "claim_boundary": {
            "ranking_admissible": False,
            "winner_selected": False,
            "paper_level_claim_made": False,
            "finite_window_vs_gru_conclusion_made": False,
            "level3_self_id_claim_made": False,
        },
    }


def run_materialization(
    *,
    all_slices_path: Path | str = DEFAULT_ALL_SLICES,
    dominant_slices_path: Path | str = DEFAULT_DOMINANT_SLICES,
    route_recommendation_path: Path | str = DEFAULT_ROUTE_RECOMMENDATION,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    all_slices = read_csv_rows(all_slices_path)
    dominant_slices = read_csv_rows(dominant_slices_path)
    route_recommendation = read_csv_rows(route_recommendation_path)

    offtrack_targets = offtrack_target_rows(all_slices)
    collision_guardrails = collision_guardrail_rows(all_slices)
    profile_diagnostics = profile_diagnostic_rows(all_slices)
    matrix_rows = [*offtrack_targets, *collision_guardrails]
    profile_target_count = sum(1 for row in matrix_rows if str(row.get("axis", "")) in PROFILE_AXES and row.get("slice_role") == "offtrack_target")
    profile_guardrail_count = sum(
        1 for row in matrix_rows if str(row.get("axis", "")) in PROFILE_AXES and row.get("slice_role") == "collision_guardrail"
    )

    write_csv_rows(output / "offtrack_target_slices.csv", offtrack_targets, fieldnames=MATERIALIZED_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_slices.csv", collision_guardrails, fieldnames=MATERIALIZED_FIELDNAMES)
    write_csv_rows(output / "profile_diagnostic_slices.csv", profile_diagnostics, fieldnames=MATERIALIZED_FIELDNAMES)
    write_csv_rows(output / "target_guardrail_matrix.csv", matrix_rows, fieldnames=MATERIALIZED_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)
    repair_gate_spec = _repair_gate_spec(
        offtrack_targets=offtrack_targets,
        collision_guardrails=collision_guardrails,
        route_recommendation=route_recommendation,
    )
    repair_gate_spec_path = output / "repair_gate_spec.json"
    write_json(repair_gate_spec_path, repair_gate_spec)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    passes = (
        len(all_slices) > 0
        and len(offtrack_targets) >= 8
        and len(collision_guardrails) >= 3
        and profile_target_count == 0
        and profile_guardrail_count == 0
        and repair_gate_spec_path.exists()
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass"
            if passes
            else "current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "all_slices_path": str(all_slices_path),
        "dominant_slices_path": str(dominant_slices_path),
        "route_recommendation_path": str(route_recommendation_path),
        "output_dir": str(output),
        "input_slice_count": len(all_slices),
        "dominant_slice_count": len(dominant_slices),
        "route_recommendation_count": len(route_recommendation),
        "offtrack_target_slice_count": len(offtrack_targets),
        "collision_guardrail_slice_count": len(collision_guardrails),
        "profile_diagnostic_slice_count": len(profile_diagnostics),
        "profile_target_slice_count": profile_target_count,
        "profile_guardrail_slice_count": profile_guardrail_count,
        "repair_gate_spec_exists": repair_gate_spec_path.exists(),
        "primary_route": str(route_recommendation[0].get("route", "")) if route_recommendation else "",
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "offtrack_target_slices": str(output / "offtrack_target_slices.csv"),
            "collision_guardrail_slices": str(output / "collision_guardrail_slices.csv"),
            "profile_diagnostic_slices": str(output / "profile_diagnostic_slices.csv"),
            "target_guardrail_matrix": str(output / "target_guardrail_matrix.csv"),
            "repair_gate_spec": str(repair_gate_spec_path),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-slices", type=Path, default=DEFAULT_ALL_SLICES)
    parser.add_argument("--dominant-slices", type=Path, default=DEFAULT_DOMINANT_SLICES)
    parser.add_argument("--route-recommendation", type=Path, default=DEFAULT_ROUTE_RECOMMENDATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_materialization(
        all_slices_path=args.all_slices,
        dominant_slices_path=args.dominant_slices,
        route_recommendation_path=args.route_recommendation,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"offtrack_target_slice_count={summary['offtrack_target_slice_count']}")
    print(f"collision_guardrail_slice_count={summary['collision_guardrail_slice_count']}")
    print(f"profile_target_slice_count={summary['profile_target_slice_count']}")
    print(f"profile_guardrail_slice_count={summary['profile_guardrail_slice_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
