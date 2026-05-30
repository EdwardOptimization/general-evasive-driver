"""No-rollout materialization for the metric-specific bounded panel."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_executable_workload_materialization_preflight import (
    DEFAULT_M1674_RUN_DIR,
    profile_artifact_rows,
)
from autodrift.controller_family_measured_routing_smoke import assert_human_view_env_contract
from autodrift.task_quality_outcome_semantics_materialization_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1743_OUTPUT_DIR,
    METRIC_SUPPORT_STATUS,
)
from autodrift.task_quality_scenario_taxonomy_preflight import unsupported_scenario_feature_rows
from autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight import (
    DEFAULT_OUTPUT_DIR as DEFAULT_M1734_OUTPUT_DIR,
)


DEFAULT_SEMANTICS_SCENARIO_SPECS = DEFAULT_M1743_OUTPUT_DIR / "semantics_scenario_specs.json"
DEFAULT_REPAIRED_SCENARIO_SPECS = DEFAULT_M1734_OUTPUT_DIR / "repaired_scenario_specs.json"
DEFAULT_OUTPUT_DIR = Path("runs/m1771_metric_specific_bounded_panel_materialization_preflight")
EXPECTED_ROLE_PANEL_COUNT = 4
EXPECTED_SPECS_PER_ROLE = 6
EXPECTED_PANEL_SPEC_COUNT = EXPECTED_ROLE_PANEL_COUNT * EXPECTED_SPECS_PER_ROLE
EXPECTED_PROFILE_COUNT = 12
EXPECTED_PANEL_CELL_COUNT = EXPECTED_PANEL_SPEC_COUNT * EXPECTED_PROFILE_COUNT
ROLE_PANEL_SELECTIONS: tuple[dict[str, Any], ...] = (
    {
        "role_panel_id": "stable_avoidance_aes",
        "role_panel_label": "Stable avoidance and AES",
        "source_scenario_spec_ids": (
            "m1728-s1-00",
            "m1728-s1-02",
            "m1728-s1-08",
            "m1728-s2-01",
            "m1728-s2-04",
            "m1728-s2-09",
        ),
        "panel_primary_metric_family": "avoidance_success",
        "panel_evaluation_role": "benchmark",
        "panel_metric_contract": (
            "benchmark_success",
            "avoidance_success",
            "off_track_violation",
            "off_track_severity_proxy",
            "recovery_success",
            "recovery_time_proxy",
        ),
        "ranking_admission_condition": (
            "non-mitigation rows are not dominated by one failure bucket and "
            "road-boundary retention is interpretable"
        ),
    },
    {
        "role_panel_id": "drift_required_recovery",
        "role_panel_label": "Drift-required avoidance and recovery",
        "source_scenario_spec_ids": (
            "m1728-s3-00",
            "m1728-s3-01",
            "m1728-s3-04",
            "m1728-s3-06",
            "m1728-s3-08",
            "m1728-s3-11",
        ),
        "panel_primary_metric_family": "controlled_drift_recovery",
        "panel_evaluation_role": "benchmark",
        "panel_metric_contract": (
            "benchmark_success",
            "avoidance_success",
            "controlled_drift_recovery_success",
            "drift_used",
            "recovery_success",
            "recovery_time_proxy",
        ),
        "ranking_admission_condition": "successful rows must also show recovery after high-yaw behavior",
    },
    {
        "role_panel_id": "hidden_dynamics_robustness",
        "role_panel_label": "Hidden-dynamics robustness",
        "source_scenario_spec_ids": (
            "m1728-s6-00",
            "m1728-s6-02",
            "m1728-s6-04",
            "m1728-s6-06",
            "m1728-s6-08",
            "m1728-s6-10",
        ),
        "panel_primary_metric_family": "hidden_dynamics_robustness",
        "panel_evaluation_role": "diagnostic_stress",
        "panel_metric_contract": (
            "hidden_dynamics_robustness",
            "avoidance_success",
            "collision_mitigation_score",
            "off_track_violation",
            "impact_severity_proxy",
        ),
        "ranking_admission_condition": "hidden buckets must be balanced and collision/off-track kept separate",
    },
    {
        "role_panel_id": "unavoidable_mitigation",
        "role_panel_label": "Unavoidable mitigation",
        "source_scenario_spec_ids": (
            "m1728-s4-00",
            "m1728-s4-02",
            "m1728-s4-04",
            "m1728-s4-08",
            "m1728-s4-09",
            "m1728-s4-11",
        ),
        "panel_primary_metric_family": "collision_mitigation",
        "panel_evaluation_role": "mitigation_diagnostic",
        "panel_metric_contract": (
            "collision_mitigation_score",
            "impact_severity_proxy",
            "impact_speed_proxy",
            "impact_beta_abs",
            "impact_yaw_rate_abs",
            "off_track_severity_proxy",
        ),
        "ranking_admission_condition": "mitigation rows are scored by severity, not raw obstacle-pass success",
    },
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
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


def _payload_rows(path: Path | str, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    payload = read_json(path)
    for key in keys:
        if key in payload:
            return [dict(row) for row in payload[key]]
    raise KeyError(f"{path} does not contain any of {keys}")


def load_semantics_scenario_specs(path: Path | str = DEFAULT_SEMANTICS_SCENARIO_SPECS) -> list[dict[str, Any]]:
    return _payload_rows(path, ("semantics_scenario_specs", "scenario_specs"))


def load_repaired_scenario_specs(path: Path | str = DEFAULT_REPAIRED_SCENARIO_SPECS) -> list[dict[str, Any]]:
    return _payload_rows(path, ("repaired_scenario_specs", "scenario_specs"))


def _metric_flag(metric: str) -> str:
    return f"metric_required_{metric}"


def _contract_metric_flags(metrics: Iterable[str]) -> dict[str, bool]:
    required = set(str(metric) for metric in metrics)
    known = sorted({*METRIC_SUPPORT_STATUS.keys(), "impact_speed_proxy", "impact_beta_abs", "impact_yaw_rate_abs", "drift_used"})
    return {_metric_flag(metric): metric in required for metric in known}


def metric_contract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel in ROLE_PANEL_SELECTIONS:
        metrics = tuple(str(metric) for metric in panel["panel_metric_contract"])
        for metric in metrics:
            support = METRIC_SUPPORT_STATUS.get(
                metric,
                {
                    "support_status": "derivable_from_existing_rollout_rows",
                    "reason": "metric is already present in instrumented evaluator rows.",
                },
            )
            rows.append(
                {
                    "role_panel_id": panel["role_panel_id"],
                    "panel_primary_metric_family": panel["panel_primary_metric_family"],
                    "metric_name": metric,
                    "support_status": support["support_status"],
                    "reason": support["reason"],
                    "primary_for_panel": metric == panel["panel_primary_metric_family"],
                    "ranking_admission_condition": panel["ranking_admission_condition"],
                    "diagnostic_only_no_ranking_claim": True,
                }
            )
    return rows


def materialized_panel_specs(
    *,
    semantics_specs: list[Mapping[str, Any]],
    repaired_specs: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    semantics_by_id = {str(row["scenario_spec_id"]): dict(row) for row in semantics_specs}
    repaired_by_id = {str(row["scenario_spec_id"]): dict(row) for row in repaired_specs}
    specs: list[dict[str, Any]] = []
    for panel_index, panel in enumerate(ROLE_PANEL_SELECTIONS, start=1):
        for spec_index, source_id in enumerate(panel["source_scenario_spec_ids"]):
            source_id = str(source_id)
            if source_id not in semantics_by_id:
                raise KeyError(f"missing semantics spec {source_id}")
            if source_id not in repaired_by_id:
                raise KeyError(f"missing repaired spec {source_id}")
            semantics = semantics_by_id[source_id]
            repaired = repaired_by_id[source_id]
            bounded_id = f"m1771-bp{panel_index}-{spec_index:02d}"
            metrics = tuple(str(metric) for metric in panel["panel_metric_contract"])
            row = {
                **semantics,
                "scenario_spec_id": bounded_id,
                "bounded_panel_spec_id": bounded_id,
                "source_scenario_spec_id": source_id,
                "m1728_scenario_spec_id": str(semantics.get("m1728_scenario_spec_id", source_id)),
                "role_panel_id": str(panel["role_panel_id"]),
                "role_panel_label": str(panel["role_panel_label"]),
                "role_panel_index": panel_index,
                "role_panel_spec_index": spec_index,
                "panel_evaluation_role": str(panel["panel_evaluation_role"]),
                "panel_primary_metric_family": str(panel["panel_primary_metric_family"]),
                "panel_metric_contract": ";".join(metrics),
                "ranking_admission_condition": str(panel["ranking_admission_condition"]),
                "ranking_eligible_after_audit": False,
                "diagnostic_only_no_ranking_claim": True,
                "bounded_panel_materialization": True,
                "labels_enter_actor_input": False,
                "environment_reset_scheduled": False,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
                "sampling_repair_source": str(repaired.get("sampling_repair_source", semantics.get("sampling_repair_source", ""))),
                "sampling_repair_variant_id": str(
                    repaired.get("sampling_repair_variant_id", semantics.get("sampling_repair_variant_id", ""))
                ),
                "sampling_repair_applied": bool(repaired.get("sampling_repair_applied", False)),
                "env_config": deepcopy(dict(repaired["env_config"])),
                **_contract_metric_flags(metrics),
            }
            specs.append(row)
    return specs


def panel_spec_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "env_config"}


def panel_matrix_rows(
    panel_specs: list[Mapping[str, Any]],
    *,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
) -> list[dict[str, Any]]:
    profiles = profile_artifact_rows(m1674_run_dir=m1674_run_dir)
    rows: list[dict[str, Any]] = []
    for spec in panel_specs:
        for profile in profiles:
            rows.append(
                {
                    "bounded_panel_workload_id": f"{spec['bounded_panel_spec_id']}::{profile['profile_name']}",
                    "scenario_workload_id": f"{spec['scenario_spec_id']}::{profile['profile_name']}",
                    "scenario_spec_id": spec["scenario_spec_id"],
                    "bounded_panel_spec_id": spec["bounded_panel_spec_id"],
                    "source_scenario_spec_id": spec["source_scenario_spec_id"],
                    "m1728_scenario_spec_id": spec["m1728_scenario_spec_id"],
                    "role_panel_id": spec["role_panel_id"],
                    "role_panel_label": spec["role_panel_label"],
                    "scenario_family_id": spec["scenario_family_id"],
                    "scenario_family": spec["scenario_family"],
                    "scenario_role": spec["scenario_role"],
                    "profile_name": profile["profile_name"],
                    "profile_config_path": profile["config_path"],
                    "checkpoint_path": profile["checkpoint_path"],
                    "config_exists": profile["config_exists"],
                    "checkpoint_exists": profile["checkpoint_exists"],
                    "evaluation_role": spec["evaluation_role"],
                    "primary_metric_family": spec["primary_metric_family"],
                    "panel_evaluation_role": spec["panel_evaluation_role"],
                    "panel_primary_metric_family": spec["panel_primary_metric_family"],
                    "panel_metric_contract": spec["panel_metric_contract"],
                    "ranking_eligible_after_audit": False,
                    "diagnostic_only_no_ranking_claim": True,
                    "labels_enter_actor_input": False,
                    "allowed_labels_metadata_only": spec["allowed_labels_metadata_only"],
                    "hidden_dynamics_bucket": spec["hidden_dynamics_bucket"],
                    "road_boundary_bucket": spec["road_boundary_bucket"],
                    "obstacle_timing_bucket": spec["obstacle_timing_bucket"],
                    "obstacle_lateral_bucket": spec["obstacle_lateral_bucket"],
                    "sampling_repair_source": spec["sampling_repair_source"],
                    "sampling_repair_variant_id": spec["sampling_repair_variant_id"],
                    "sampling_repair_applied": spec["sampling_repair_applied"],
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    **{
                        key: value
                        for key, value in spec.items()
                        if str(key).startswith("metric_required_")
                    },
                }
            )
    return rows


def role_summary_rows(panel_specs: list[Mapping[str, Any]], matrix_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    cells_by_role = Counter(str(row["role_panel_id"]) for row in matrix_rows)
    specs_by_role: dict[str, list[Mapping[str, Any]]] = {}
    for spec in panel_specs:
        specs_by_role.setdefault(str(spec["role_panel_id"]), []).append(spec)
    rows: list[dict[str, Any]] = []
    for panel in ROLE_PANEL_SELECTIONS:
        role = str(panel["role_panel_id"])
        specs = specs_by_role.get(role, [])
        rows.append(
            {
                "role_panel_id": role,
                "role_panel_label": panel["role_panel_label"],
                "spec_count": len(specs),
                "cell_count": cells_by_role.get(role, 0),
                "panel_evaluation_role": panel["panel_evaluation_role"],
                "panel_primary_metric_family": panel["panel_primary_metric_family"],
                "source_scenario_spec_ids": ";".join(str(spec["source_scenario_spec_id"]) for spec in specs),
                "scenario_families": ";".join(sorted({str(spec["scenario_family"]) for spec in specs})),
                "hidden_dynamics_buckets": ";".join(sorted({str(spec["hidden_dynamics_bucket"]) for spec in specs})),
                "road_boundary_buckets": ";".join(sorted({str(spec["road_boundary_bucket"]) for spec in specs})),
                "obstacle_timing_buckets": ";".join(sorted({str(spec["obstacle_timing_bucket"]) for spec in specs})),
                "obstacle_lateral_buckets": ";".join(sorted({str(spec["obstacle_lateral_bucket"]) for spec in specs})),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
    return rows


def contract_violation_rows(panel_specs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in panel_specs:
        try:
            assert_human_view_env_contract(build_env_config(dict(spec["env_config"])))
        except Exception as exc:  # noqa: BLE001 - preflight must preserve all violations.
            rows.append(
                {
                    "bounded_panel_spec_id": str(spec["bounded_panel_spec_id"]),
                    "source_scenario_spec_id": str(spec["source_scenario_spec_id"]),
                    "role_panel_id": str(spec["role_panel_id"]),
                    "violation": str(exc),
                }
            )
    return rows


def _count_by_key(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def run_metric_specific_bounded_panel_materialization_preflight(
    *,
    semantics_scenario_specs_path: Path | str = DEFAULT_SEMANTICS_SCENARIO_SPECS,
    repaired_scenario_specs_path: Path | str = DEFAULT_REPAIRED_SCENARIO_SPECS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    m1674_run_dir: Path | str = DEFAULT_M1674_RUN_DIR,
    target_profile_count: int = EXPECTED_PROFILE_COUNT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    semantics_specs = load_semantics_scenario_specs(semantics_scenario_specs_path)
    repaired_specs = load_repaired_scenario_specs(repaired_scenario_specs_path)
    panel_specs = materialized_panel_specs(semantics_specs=semantics_specs, repaired_specs=repaired_specs)
    matrix_rows = panel_matrix_rows(panel_specs, m1674_run_dir=m1674_run_dir)
    role_rows = role_summary_rows(panel_specs, matrix_rows)
    metric_rows = metric_contract_rows()
    unsupported_rows = unsupported_scenario_feature_rows()
    contract_rows = contract_violation_rows(panel_specs)

    role_counts = _count_by_key(panel_specs, "role_panel_id")
    profile_count = len({str(row["profile_name"]) for row in matrix_rows})
    missing_config_count = sum(row.get("config_exists") != True for row in matrix_rows)
    missing_checkpoint_count = sum(row.get("checkpoint_exists") != True for row in matrix_rows)
    labels_enter_actor_input_count = sum(bool(row.get("labels_enter_actor_input")) for row in panel_specs)
    unsupported_faults_treated_as_covered_count = sum(
        bool(row.get("covered_by_current_preflight")) for row in unsupported_rows
    )
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    expected_cell_count = EXPECTED_PANEL_SPEC_COUNT * target_profile_count
    role_balance_passed = (
        len(role_counts) == EXPECTED_ROLE_PANEL_COUNT
        and all(count == EXPECTED_SPECS_PER_ROLE for count in role_counts.values())
    )
    result_passes = (
        len(panel_specs) == EXPECTED_PANEL_SPEC_COUNT
        and profile_count == target_profile_count
        and len(matrix_rows) == expected_cell_count
        and role_balance_passed
        and len(contract_rows) == 0
        and missing_config_count == 0
        and missing_checkpoint_count == 0
        and labels_enter_actor_input_count == 0
        and unsupported_faults_treated_as_covered_count == 0
        and guardrail_violation_count == 0
    )

    generated_at = utc_timestamp()
    artifacts = {
        "summary": str(output / "summary.json"),
        "bounded_panel_specs": str(output / "bounded_panel_specs.csv"),
        "bounded_panel_specs_json": str(output / "bounded_panel_specs.json"),
        "bounded_panel_matrix": str(output / "bounded_panel_matrix.csv"),
        "bounded_panel_role_summary": str(output / "bounded_panel_role_summary.csv"),
        "bounded_panel_metric_contract": str(output / "bounded_panel_metric_contract.csv"),
        "bounded_panel_metric_contract_json": str(output / "bounded_panel_metric_contract.json"),
        "unsupported_feature_boundary": str(output / "unsupported_feature_boundary.csv"),
        "contract_violations": str(output / "contract_violations.csv"),
    }
    summary = {
        "result_class": (
            "metric_specific_bounded_panel_materialization_preflight_pass"
            if result_passes
            else "metric_specific_bounded_panel_materialization_preflight_fail"
        ),
        "generated_at_utc": generated_at,
        "output_dir": str(output),
        "semantics_scenario_specs_path": str(semantics_scenario_specs_path),
        "repaired_scenario_specs_path": str(repaired_scenario_specs_path),
        "panel_spec_count": len(panel_specs),
        "target_panel_spec_count": EXPECTED_PANEL_SPEC_COUNT,
        "role_panel_count": len(role_counts),
        "target_role_panel_count": EXPECTED_ROLE_PANEL_COUNT,
        "specs_per_role": role_counts,
        "target_specs_per_role": EXPECTED_SPECS_PER_ROLE,
        "role_balance_passed": role_balance_passed,
        "profile_count": profile_count,
        "target_profile_count": target_profile_count,
        "panel_cell_count": len(matrix_rows),
        "target_panel_cell_count": expected_cell_count,
        "missing_config_count": missing_config_count,
        "missing_checkpoint_count": missing_checkpoint_count,
        "contract_violation_count": len(contract_rows),
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "unsupported_feature_boundary_count": len(unsupported_rows),
        "unsupported_faults_treated_as_covered_count": unsupported_faults_treated_as_covered_count,
        "evaluation_role_counts": _count_by_key(panel_specs, "panel_evaluation_role"),
        "primary_metric_family_counts": _count_by_key(panel_specs, "panel_primary_metric_family"),
        "scenario_family_counts": _count_by_key(panel_specs, "scenario_family"),
        "hidden_dynamics_bucket_counts": _count_by_key(panel_specs, "hidden_dynamics_bucket"),
        "road_boundary_bucket_counts": _count_by_key(panel_specs, "road_boundary_bucket"),
        "obstacle_timing_bucket_counts": _count_by_key(panel_specs, "obstacle_timing_bucket"),
        "obstacle_lateral_bucket_counts": _count_by_key(panel_specs, "obstacle_lateral_bucket"),
        "metric_contract_row_count": len(metric_rows),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
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
        "next_blocker": "m1772-paper-route-metric-specific-bounded-panel-materialization-result-audit",
    }

    write_csv_rows(output / "bounded_panel_specs.csv", [panel_spec_csv_row(row) for row in panel_specs])
    write_json(
        output / "bounded_panel_specs.json",
        {
            "generated_at_utc": generated_at,
            "bounded_panel_specs": panel_specs,
        },
    )
    write_csv_rows(output / "bounded_panel_matrix.csv", matrix_rows)
    write_csv_rows(output / "bounded_panel_role_summary.csv", role_rows)
    write_csv_rows(output / "bounded_panel_metric_contract.csv", metric_rows)
    write_json(
        output / "bounded_panel_metric_contract.json",
        {
            "generated_at_utc": generated_at,
            "role_panels": [
                {
                    **{key: value for key, value in panel.items() if key != "source_scenario_spec_ids"},
                    "source_scenario_spec_ids": list(panel["source_scenario_spec_ids"]),
                }
                for panel in ROLE_PANEL_SELECTIONS
            ],
            "metric_contract_rows": metric_rows,
        },
    )
    write_csv_rows(output / "unsupported_feature_boundary.csv", unsupported_rows)
    write_csv_rows(
        output / "contract_violations.csv",
        contract_rows,
        fieldnames=["bounded_panel_spec_id", "source_scenario_spec_id", "role_panel_id", "violation"],
    )
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-rollout metric-specific bounded panel.")
    parser.add_argument("--semantics-scenario-specs", type=Path, default=DEFAULT_SEMANTICS_SCENARIO_SPECS)
    parser.add_argument("--repaired-scenario-specs", type=Path, default=DEFAULT_REPAIRED_SCENARIO_SPECS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--m1674-run-dir", type=Path, default=DEFAULT_M1674_RUN_DIR)
    args = parser.parse_args()

    summary = run_metric_specific_bounded_panel_materialization_preflight(
        semantics_scenario_specs_path=args.semantics_scenario_specs,
        repaired_scenario_specs_path=args.repaired_scenario_specs,
        output_dir=args.output_dir,
        m1674_run_dir=args.m1674_run_dir,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_spec_count={summary['panel_spec_count']}")
    print(f"role_panel_count={summary['role_panel_count']}")
    print(f"panel_cell_count={summary['panel_cell_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
