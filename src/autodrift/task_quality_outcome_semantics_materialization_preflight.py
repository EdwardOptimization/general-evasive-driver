"""No-rollout materialization of revised task-quality outcome semantics."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.task_quality_scenario_taxonomy_execution import (
    TARGET_EPISODE_COUNT,
    TARGET_PROFILE_COUNT,
    TARGET_SCENARIO_FAMILY_COUNT,
    TARGET_SCENARIO_SPEC_COUNT,
    load_scenario_specs,
)


DEFAULT_SCENARIO_SPECS = Path("runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json")
DEFAULT_SCENARIO_MATRIX = Path("runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1743_task_quality_outcome_semantics_materialization_preflight")
EVALUATION_ROLES = ("benchmark", "diagnostic_stress", "mitigation_diagnostic")
PRIMARY_METRIC_FAMILIES = (
    "avoidance_success",
    "controlled_drift_recovery",
    "collision_mitigation",
    "boundary_robustness",
    "hidden_dynamics_robustness",
)
REQUIRED_METRICS = (
    "benchmark_success",
    "avoidance_success",
    "controlled_drift_recovery_success",
    "collision_mitigation_score",
    "impact_severity_proxy",
    "off_track_violation",
    "off_track_severity_proxy",
    "recovery_success",
    "recovery_time_proxy",
    "hidden_dynamics_robustness",
    "diagnostic_only_no_ranking_claim",
)
FORBIDDEN_GUARDRAILS = (
    "environment_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "unsupported_faults_treated_as_covered",
)
OUTCOME_SEMANTICS_REGISTRY: dict[str, dict[str, Any]] = {
    "ordinary_stable_avoidance": {
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
        "family_semantics": (
            "Obstacle passed, no collision, no off-track termination, bounded sideslip/yaw, "
            "and stable corridor recovery by episode end."
        ),
        "ranking_eligible_after_audit": True,
        "diagnostic_only_no_ranking_claim": False,
        "required_metric_subset": (
            "benchmark_success",
            "avoidance_success",
            "off_track_violation",
            "recovery_success",
            "recovery_time_proxy",
        ),
    },
    "aeb_infeasible_stable_aes": {
        "evaluation_role": "benchmark",
        "primary_metric_family": "avoidance_success",
        "family_semantics": "Obstacle passed by steering/braking, no collision, no off-track termination, and bounded recovery time.",
        "ranking_eligible_after_audit": True,
        "diagnostic_only_no_ranking_claim": False,
        "required_metric_subset": (
            "benchmark_success",
            "avoidance_success",
            "off_track_violation",
            "recovery_success",
            "recovery_time_proxy",
        ),
    },
    "drift_required_avoidance": {
        "evaluation_role": "benchmark",
        "primary_metric_family": "controlled_drift_recovery",
        "family_semantics": (
            "Obstacle passed with controlled high-yaw/sideslip allowed; collision, unrecovered spin, "
            "and road-boundary violation remain failures."
        ),
        "ranking_eligible_after_audit": True,
        "diagnostic_only_no_ranking_claim": False,
        "required_metric_subset": (
            "benchmark_success",
            "controlled_drift_recovery_success",
            "off_track_violation",
            "recovery_success",
            "recovery_time_proxy",
        ),
    },
    "unavoidable_mitigation": {
        "evaluation_role": "mitigation_diagnostic",
        "primary_metric_family": "collision_mitigation",
        "family_semantics": "Do not score as ordinary success; measure impact severity, heading/yaw at contact, and lower-severity trajectory choice.",
        "ranking_eligible_after_audit": False,
        "diagnostic_only_no_ranking_claim": True,
        "required_metric_subset": (
            "collision_mitigation_score",
            "impact_severity_proxy",
            "diagnostic_only_no_ranking_claim",
        ),
    },
    "off_track_boundary_stress": {
        "evaluation_role": "diagnostic_stress",
        "primary_metric_family": "boundary_robustness",
        "family_semantics": "Boundary stress panel; report off-track frequency, severity, time-to-off-track, and recovery separately.",
        "ranking_eligible_after_audit": False,
        "diagnostic_only_no_ranking_claim": True,
        "required_metric_subset": (
            "off_track_violation",
            "off_track_severity_proxy",
            "recovery_success",
            "recovery_time_proxy",
            "diagnostic_only_no_ranking_claim",
        ),
    },
    "hidden_dynamics_stress": {
        "evaluation_role": "diagnostic_stress",
        "primary_metric_family": "hidden_dynamics_robustness",
        "family_semantics": (
            "Hidden-dynamics stress panel; supported avoidance labels may be audited separately, "
            "but the family aggregate remains diagnostic until promotion."
        ),
        "ranking_eligible_after_audit": False,
        "diagnostic_only_no_ranking_claim": True,
        "required_metric_subset": (
            "hidden_dynamics_robustness",
            "avoidance_success",
            "collision_mitigation_score",
            "off_track_violation",
            "diagnostic_only_no_ranking_claim",
        ),
    },
}
METRIC_SUPPORT_STATUS: dict[str, dict[str, str]] = {
    "benchmark_success": {
        "support_status": "derivable_from_existing_rollout_rows",
        "reason": "obstacle completion, collision, outcome bucket, and off-track termination are logged.",
    },
    "avoidance_success": {
        "support_status": "derivable_from_existing_rollout_rows",
        "reason": "success_obstacle_pass outcome and collision/off-track fields are logged.",
    },
    "controlled_drift_recovery_success": {
        "support_status": "partially_supported_needs_recovery_definition",
        "reason": "sideslip and episode outcome exist, but recovery time threshold must be pre-registered.",
    },
    "collision_mitigation_score": {
        "support_status": "partially_supported_needs_metric_definition",
        "reason": "collision and clearance are logged, but impact severity proxy is not yet a formal score.",
    },
    "impact_severity_proxy": {
        "support_status": "unsupported_until_instrumented",
        "reason": "impact speed/heading at contact is not yet explicitly recorded as a metric.",
    },
    "off_track_violation": {
        "support_status": "derivable_from_existing_rollout_rows",
        "reason": "outcome bucket and termination reason include off-track information.",
    },
    "off_track_severity_proxy": {
        "support_status": "unsupported_until_instrumented",
        "reason": "distance/time beyond boundary is not yet explicitly recorded.",
    },
    "recovery_success": {
        "support_status": "partially_supported_needs_metric_definition",
        "reason": "episode outcome is logged, but stable corridor recovery threshold is not formalized.",
    },
    "recovery_time_proxy": {
        "support_status": "unsupported_until_instrumented",
        "reason": "time-to-recovery after avoidance/drift is not explicitly logged.",
    },
    "hidden_dynamics_robustness": {
        "support_status": "partially_supported_needs_metric_definition",
        "reason": "hidden-dynamics buckets are metadata, but robustness scoring across labels and buckets is not formalized.",
    },
    "diagnostic_only_no_ranking_claim": {
        "support_status": "metadata_supported",
        "reason": "diagnostic rows can be marked as not ranking-eligible in materialized metadata.",
    },
}


def outcome_semantics_registry_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, item in sorted(OUTCOME_SEMANTICS_REGISTRY.items()):
        rows.append(
            {
                "scenario_family": family,
                "evaluation_role": item["evaluation_role"],
                "primary_metric_family": item["primary_metric_family"],
                "family_semantics": item["family_semantics"],
                "ranking_eligible_after_audit": bool(item["ranking_eligible_after_audit"]),
                "diagnostic_only_no_ranking_claim": bool(item["diagnostic_only_no_ranking_claim"]),
                "required_metric_subset": ";".join(str(metric) for metric in item["required_metric_subset"]),
            }
        )
    return rows


def validate_registry_metric_subsets() -> list[dict[str, str]]:
    supported_metrics = set(REQUIRED_METRICS)
    rows: list[dict[str, str]] = []
    for family, item in sorted(OUTCOME_SEMANTICS_REGISTRY.items()):
        for metric in item["required_metric_subset"]:
            if str(metric) not in supported_metrics:
                rows.append({"scenario_family": family, "unknown_required_metric": str(metric)})
    return rows


def metric_support_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in REQUIRED_METRICS:
        item = METRIC_SUPPORT_STATUS[metric]
        rows.append(
            {
                "metric_name": metric,
                "support_status": item["support_status"],
                "reason": item["reason"],
                "silently_approximated": False,
                "requires_future_instrumentation": item["support_status"] == "unsupported_until_instrumented",
            }
        )
    return rows


def unsupported_metric_gap_rows() -> list[dict[str, Any]]:
    return [
        row
        for row in metric_support_rows()
        if row["support_status"] in {"unsupported_until_instrumented", "partially_supported_needs_metric_definition", "partially_supported_needs_recovery_definition"}
    ]


def semantics_for_family(scenario_family: str) -> dict[str, Any]:
    return OUTCOME_SEMANTICS_REGISTRY[str(scenario_family)]


def _metric_flags_for_family(scenario_family: str) -> dict[str, bool]:
    required = set(str(metric) for metric in semantics_for_family(scenario_family)["required_metric_subset"])
    return {f"metric_required_{metric}": metric in required for metric in REQUIRED_METRICS}


def _allowed_labels(row: Mapping[str, Any]) -> str:
    return str(row.get("allowed_labels_metadata_only", ""))


def materialized_spec_rows(specs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        scenario_family = str(spec["scenario_family"])
        semantics = semantics_for_family(scenario_family)
        rows.append(
            {
                "scenario_spec_id": str(spec["scenario_spec_id"]),
                "m1728_scenario_spec_id": str(spec.get("m1728_scenario_spec_id", spec["scenario_spec_id"])),
                "scenario_family_id": str(spec["scenario_family_id"]),
                "scenario_family": scenario_family,
                "scenario_role": str(spec["scenario_role"]),
                "allowed_labels_metadata_only": _allowed_labels(spec),
                "evaluation_role": str(semantics["evaluation_role"]),
                "primary_metric_family": str(semantics["primary_metric_family"]),
                "ranking_eligible_after_audit": bool(semantics["ranking_eligible_after_audit"]),
                "diagnostic_only_no_ranking_claim": bool(semantics["diagnostic_only_no_ranking_claim"]),
                "benchmark_row": str(semantics["evaluation_role"]) == "benchmark",
                "hidden_dynamics_bucket": str(spec["hidden_dynamics_bucket"]),
                "road_boundary_bucket": str(spec["road_boundary_bucket"]),
                "obstacle_timing_bucket": str(spec["obstacle_timing_bucket"]),
                "obstacle_lateral_bucket": str(spec["obstacle_lateral_bucket"]),
                "sampling_repair_variant_id": str(spec.get("sampling_repair_variant_id", "not_applicable")),
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                **_metric_flags_for_family(scenario_family),
            }
        )
    return rows


def materialized_matrix_rows(matrix_rows: list[Mapping[str, Any]], spec_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    semantics_by_spec = {str(row["scenario_spec_id"]): row for row in spec_rows}
    output: list[dict[str, Any]] = []
    for row in matrix_rows:
        semantics = semantics_by_spec[str(row["scenario_spec_id"])]
        item = dict(row)
        item.update(
            {
                "evaluation_role": semantics["evaluation_role"],
                "primary_metric_family": semantics["primary_metric_family"],
                "ranking_eligible_after_audit": bool(semantics["ranking_eligible_after_audit"]),
                "diagnostic_only_no_ranking_claim": bool(semantics["diagnostic_only_no_ranking_claim"]),
                "benchmark_row": bool(semantics["benchmark_row"]),
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                **{key: value for key, value in semantics.items() if str(key).startswith("metric_required_")},
            }
        )
        output.append(item)
    return output


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def run_outcome_semantics_materialization_preflight(
    *,
    scenario_specs_path: Path | str = DEFAULT_SCENARIO_SPECS,
    workload_path: Path | str = DEFAULT_SCENARIO_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    specs = load_scenario_specs(scenario_specs_path)
    matrix = read_csv_rows(workload_path)
    registry_rows = outcome_semantics_registry_rows()
    registry_metric_errors = validate_registry_metric_subsets()
    support_rows = metric_support_rows()
    unsupported_rows = unsupported_metric_gap_rows()
    spec_rows = materialized_spec_rows(specs)
    matrix_rows = materialized_matrix_rows(matrix, spec_rows)
    role_counts = _count_by_key(spec_rows, "evaluation_role")
    metric_family_counts = _count_by_key(spec_rows, "primary_metric_family")
    matrix_role_counts = _count_by_key(matrix_rows, "evaluation_role")
    silent_unsupported_approximation_count = sum(bool(row["silently_approximated"]) for row in support_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    family_count = len({str(row["scenario_family"]) for row in spec_rows})
    profile_count = len({str(row["profile_name"]) for row in matrix_rows})
    result_passes = (
        len(specs) == TARGET_SCENARIO_SPEC_COUNT
        and len(matrix_rows) == TARGET_EPISODE_COUNT
        and family_count == TARGET_SCENARIO_FAMILY_COUNT
        and profile_count == TARGET_PROFILE_COUNT
        and set(role_counts) == set(EVALUATION_ROLES)
        and set(metric_family_counts) == set(PRIMARY_METRIC_FAMILIES)
        and not registry_metric_errors
        and bool(unsupported_rows)
        and silent_unsupported_approximation_count == 0
        and guardrail_violation_count == 0
    )

    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "outcome_semantics_registry": str(output / "outcome_semantics_registry.csv"),
        "outcome_semantics_registry_json": str(output / "outcome_semantics_registry.json"),
        "metric_support": str(output / "metric_support.csv"),
        "unsupported_metric_gaps": str(output / "unsupported_metric_gaps.csv"),
        "registry_metric_errors": str(output / "registry_metric_errors.csv"),
        "semantics_scenario_specs": str(output / "semantics_scenario_specs.csv"),
        "semantics_scenario_specs_json": str(output / "semantics_scenario_specs.json"),
        "semantics_scenario_matrix": str(output / "semantics_scenario_matrix.csv"),
    }
    summary = {
        "result_class": (
            "task_quality_outcome_semantics_materialization_preflight_pass"
            if result_passes
            else "task_quality_outcome_semantics_materialization_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "source_scenario_specs": str(scenario_specs_path),
        "source_scenario_matrix": str(workload_path),
        "scenario_spec_count": len(spec_rows),
        "target_scenario_spec_count": TARGET_SCENARIO_SPEC_COUNT,
        "scenario_matrix_cell_count": len(matrix_rows),
        "target_scenario_matrix_cell_count": TARGET_EPISODE_COUNT,
        "scenario_family_count": family_count,
        "target_scenario_family_count": TARGET_SCENARIO_FAMILY_COUNT,
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "evaluation_role_counts": role_counts,
        "matrix_evaluation_role_counts": matrix_role_counts,
        "primary_metric_family_counts": metric_family_counts,
        "registry_row_count": len(registry_rows),
        "metric_support_row_count": len(support_rows),
        "registry_metric_error_count": len(registry_metric_errors),
        "unsupported_metric_gap_count": len(unsupported_rows),
        "silent_unsupported_approximation_count": silent_unsupported_approximation_count,
        "benchmark_role_present": "benchmark" in role_counts,
        "diagnostic_stress_role_present": "diagnostic_stress" in role_counts,
        "mitigation_diagnostic_role_present": "mitigation_diagnostic" in role_counts,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "unsupported_faults_treated_as_covered": False,
        "artifacts": artifacts,
        "next_blocker": "m1744-paper-route-task-quality-outcome-semantics-materialization-preflight-result-audit",
    }
    write_csv_rows(output / "outcome_semantics_registry.csv", registry_rows)
    write_json(
        output / "outcome_semantics_registry.json",
        {
            "generated_at_utc": generated_at,
            "evaluation_roles": EVALUATION_ROLES,
            "primary_metric_families": PRIMARY_METRIC_FAMILIES,
            "required_metrics": REQUIRED_METRICS,
            "outcome_semantics_registry": registry_rows,
        },
    )
    write_csv_rows(output / "metric_support.csv", support_rows)
    write_csv_rows(output / "unsupported_metric_gaps.csv", unsupported_rows)
    write_csv_rows(
        output / "registry_metric_errors.csv",
        registry_metric_errors,
        fieldnames=["scenario_family", "unknown_required_metric"],
    )
    write_csv_rows(output / "semantics_scenario_specs.csv", spec_rows)
    write_json(
        output / "semantics_scenario_specs.json",
        {
            "generated_at_utc": generated_at,
            "semantics_scenario_specs": spec_rows,
        },
    )
    write_csv_rows(output / "semantics_scenario_matrix.csv", matrix_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout task-quality outcome semantics.")
    parser.add_argument("--scenario-specs", type=Path, default=DEFAULT_SCENARIO_SPECS)
    parser.add_argument("--workload", type=Path, default=DEFAULT_SCENARIO_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = run_outcome_semantics_materialization_preflight(
        scenario_specs_path=args.scenario_specs,
        workload_path=args.workload,
        output_dir=args.output_dir,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scenario_spec_count={summary['scenario_spec_count']}")
    print(f"scenario_matrix_cell_count={summary['scenario_matrix_cell_count']}")
    print(f"unsupported_metric_gap_count={summary['unsupported_metric_gap_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
