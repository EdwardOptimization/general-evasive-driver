import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_target_protected_tradeoff_report import (
    SUBJECT_ID,
    build_scenario_role_metric_report,
    materialize_target_protected_tradeoff_report,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


BEHAVIOR_FIELDNAMES = [
    "scenario_role",
    "subject_id",
    "seed",
    "dynamics_axis_id",
    "observation_shape",
    "action_shape",
    "actor_input_leak_flags",
    "diagnostic_only_no_ranking_claim",
    "ranking_or_winner_field_emitted",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "final_abs_lateral_velocity",
    "final_abs_yaw_rate",
    "severity_proxy",
]

GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "target_or_reference_family",
    "subject_id",
    "metric",
    "evaluated_row_count",
    "gate_pass",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "failure_type",
    "blocks_claims",
]

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "target_preservation_gates_all_passed",
    "protected_component_gates_all_passed",
    "target_and_protected_gates_all_passed",
    "target_gate_pass_count",
    "protected_component_gate_pass_count",
    "protected_component_regressed_row_count",
    "failed_gate_ids",
    "selected_for_repair_trace",
    "diagnostic_only_no_ranking_claim",
    "success_rate_field_emitted",
    "ranking_or_winner_field_emitted",
]


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _behavior_row(
    role,
    seed,
    axis,
    *,
    clearance,
    margin,
    severity,
    final_lat=0.0,
    final_yaw=0.0,
):
    return {
        "scenario_role": role,
        "subject_id": SUBJECT_ID,
        "seed": seed,
        "dynamics_axis_id": axis,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_input_leak_flags": "none",
        "diagnostic_only_no_ranking_claim": True,
        "ranking_or_winner_field_emitted": False,
        "minimum_obstacle_clearance_m": clearance,
        "minimum_road_margin_m": margin,
        "final_abs_lateral_velocity": final_lat,
        "final_abs_yaw_rate": final_yaw,
        "severity_proxy": severity,
    }


def _behavior_rows(stage):
    rows = []
    axes = [f"axis_{index}" for index in range(8)]
    for index, axis in enumerate(axes):
        seed = 265700 + index
        if stage == "baseline":
            rows.extend(
                [
                    _behavior_row("stable_avoidable", seed, axis, clearance=5.0, margin=0.0, severity=0.0),
                    _behavior_row("stable_aes", seed, axis, clearance=5.0, margin=-0.5, severity=0.0),
                    _behavior_row(
                        "drift_required_recovery",
                        seed,
                        axis,
                        clearance=0.2,
                        margin=-0.2,
                        severity=0.0,
                        final_lat=1.0,
                        final_yaw=1.0,
                    ),
                    _behavior_row(
                        "unavoidable_mitigation",
                        seed,
                        axis,
                        clearance=-1.0,
                        margin=0.0,
                        severity=3.0,
                    ),
                ]
            )
        elif stage == "m2648":
            protected_clearance = -1.1 if index == 1 else -0.95
            protected_severity = 3.2 if index == 1 else 2.9
            rows.extend(
                [
                    _behavior_row("stable_avoidable", seed, axis, clearance=5.0, margin=1.0, severity=0.0),
                    _behavior_row("stable_aes", seed, axis, clearance=5.0, margin=0.5, severity=0.0),
                    _behavior_row(
                        "drift_required_recovery",
                        seed,
                        axis,
                        clearance=1.0,
                        margin=0.5,
                        severity=0.0,
                        final_lat=0.2,
                        final_yaw=0.2,
                    ),
                    _behavior_row(
                        "unavoidable_mitigation",
                        seed,
                        axis,
                        clearance=protected_clearance,
                        margin=0.0,
                        severity=protected_severity,
                    ),
                ]
            )
        else:
            protected_clearance = -1.2 if index in {1, 2} else -0.9
            protected_severity = 3.3 if index == 1 else 2.8
            rows.extend(
                [
                    _behavior_row("stable_avoidable", seed, axis, clearance=5.0, margin=1.2, severity=0.0),
                    _behavior_row("stable_aes", seed, axis, clearance=5.0, margin=0.8, severity=0.0),
                    _behavior_row(
                        "drift_required_recovery",
                        seed,
                        axis,
                        clearance=1.2,
                        margin=0.7,
                        severity=0.0,
                        final_lat=0.1,
                        final_yaw=0.1,
                    ),
                    _behavior_row(
                        "unavoidable_mitigation",
                        seed,
                        axis,
                        clearance=protected_clearance,
                        margin=0.0,
                        severity=protected_severity,
                    ),
                ]
            )
    return rows


def _gate(gate_id, family, target_family, metric, *, passed, improved, regressed, unchanged=0):
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "target_or_reference_family": target_family,
        "subject_id": SUBJECT_ID,
        "metric": metric,
        "evaluated_row_count": improved + regressed + unchanged,
        "gate_pass": passed,
        "improved_row_count": improved,
        "regressed_row_count": regressed,
        "unchanged_row_count": unchanged,
        "failure_type": "" if passed else "behavior_regression",
        "blocks_claims": True,
    }


def _m2648_gates():
    return [
        _gate(
            "target_road_boundary_margin_control",
            "target_repair",
            "road_departure_dominant_gap",
            "minimum_road_margin_m",
            passed=True,
            improved=16,
            regressed=0,
        ),
        _gate(
            "target_drift_collision_recovery_tradeoff",
            "target_repair",
            "drift_recovery_mixed_gap",
            "drift_tradeoff_proxy",
            passed=True,
            improved=8,
            regressed=0,
        ),
        _gate(
            "protected_mitigation_reference",
            "protected_reference",
            "mitigation_collision_saturated_reference",
            "severity_proxy",
            passed=False,
            improved=7,
            regressed=1,
        ),
    ]


def _m2655_gates():
    return [
        _gate(
            "target_road_boundary_margin_control",
            "target_preservation",
            "road_departure_dominant_gap",
            "minimum_road_margin_m",
            passed=True,
            improved=16,
            regressed=0,
        ),
        _gate(
            "target_drift_collision_recovery_tradeoff",
            "target_preservation",
            "drift_recovery_mixed_gap",
            "drift_tradeoff_proxy",
            passed=True,
            improved=8,
            regressed=0,
        ),
        _gate(
            "severity_proxy_non_regression",
            "protected_component",
            "mitigation_collision_saturated_reference",
            "severity_proxy",
            passed=False,
            improved=7,
            regressed=1,
        ),
        _gate(
            "obstacle_penetration_non_regression",
            "protected_component",
            "mitigation_collision_saturated_reference",
            "obstacle_penetration_proxy_m",
            passed=False,
            improved=6,
            regressed=2,
        ),
        _gate(
            "minimum_obstacle_clearance_preservation",
            "protected_component",
            "mitigation_collision_saturated_reference",
            "minimum_obstacle_clearance_m",
            passed=False,
            improved=6,
            regressed=2,
        ),
        _gate(
            "event_transition_guard",
            "protected_component",
            "mitigation_collision_saturated_reference",
            "events",
            passed=True,
            improved=0,
            regressed=0,
            unchanged=8,
        ),
    ]


def test_scenario_role_report_preserves_target_and_protected_gate_split():
    rows = build_scenario_role_metric_report(
        _behavior_rows("baseline"),
        _behavior_rows("m2648"),
        _behavior_rows("m2655"),
        _m2655_gates(),
    )
    by_role = {row["scenario_role"]: row for row in rows}

    assert len(rows) == 4
    assert by_role["stable_avoidable"]["role_class"] == "target"
    assert by_role["stable_avoidable"]["m2655_gate_pass"] is True
    assert by_role["drift_required_recovery"]["m2655_improved_count"] == 8
    assert by_role["unavoidable_mitigation"]["role_class"] == "protected"
    assert by_role["unavoidable_mitigation"]["m2655_gate_pass"] is False
    assert by_role["unavoidable_mitigation"]["protected_role_excluded_from_target_success_denominator"] is True
    assert by_role["unavoidable_mitigation"]["hidden_or_oracle_actor_input_detected"] is False


def test_materialize_target_protected_tradeoff_report_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2657.md"
    follow_up_manifest = tmp_path / "m2658.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    baseline_path = tmp_path / "baseline.csv"
    m2648_rows_path = tmp_path / "m2648.csv"
    m2648_gates_path = tmp_path / "m2648_gates.csv"
    m2655_rows_path = tmp_path / "m2655.csv"
    m2655_candidate_path = tmp_path / "m2655_candidate.csv"
    m2655_gates_path = tmp_path / "m2655_gates.csv"
    m2650_path = tmp_path / "m2650.json"

    write_csv_rows(baseline_path, _behavior_rows("baseline"), fieldnames=BEHAVIOR_FIELDNAMES)
    write_csv_rows(m2648_rows_path, _behavior_rows("m2648"), fieldnames=BEHAVIOR_FIELDNAMES)
    write_csv_rows(m2648_gates_path, _m2648_gates(), fieldnames=GATE_FIELDNAMES)
    write_csv_rows(m2655_rows_path, _behavior_rows("m2655"), fieldnames=BEHAVIOR_FIELDNAMES)
    write_csv_rows(m2655_gates_path, _m2655_gates(), fieldnames=GATE_FIELDNAMES)
    write_csv_rows(
        m2655_candidate_path,
        [
            {
                "candidate_id": "m2655_softened_gap_bias",
                "target_preservation_gates_all_passed": True,
                "protected_component_gates_all_passed": False,
                "target_and_protected_gates_all_passed": False,
                "target_gate_pass_count": 2,
                "protected_component_gate_pass_count": 1,
                "protected_component_regressed_row_count": 5,
                "failed_gate_ids": (
                    "severity_proxy_non_regression;obstacle_penetration_non_regression;"
                    "minimum_obstacle_clearance_preservation"
                ),
                "selected_for_repair_trace": True,
                "diagnostic_only_no_ranking_claim": True,
                "success_rate_field_emitted": False,
                "ranking_or_winner_field_emitted": False,
            }
        ],
        fieldnames=CANDIDATE_FIELDNAMES,
    )
    write_json(
        m2650_path,
        {
            "status_pass": True,
            "real_behavior_regression_localized": True,
            "likely_severity_proxy_component_driver": "obstacle_penetration_proxy_worsened",
            "regressed_scenario_role": "unavoidable_mitigation",
            "regressed_seed": 265701,
            "regressed_dynamics_axis_id": "axis_1",
            "regressed_subject_id": SUBJECT_ID,
        },
    )

    summary = materialize_target_protected_tradeoff_report(
        output_dir,
        baseline_behavior_rows=baseline_path,
        m2648_post_repair_rows=m2648_rows_path,
        m2648_gates=m2648_gates_path,
        m2655_post_repair_rows=m2655_rows_path,
        m2655_candidate_sweep=m2655_candidate_path,
        m2655_gates=m2655_gates_path,
        m2650_localization=m2650_path,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["new_repair_training_or_rollout_run"] is False
    assert summary["scenario_role_metric_report_row_count"] == 4
    assert summary["target_protected_tradeoff_row_count"] == 9
    assert summary["protected_regression_focus_row_count"] == 8
    assert summary["m2655_target_preservation_gates_all_passed"] is True
    assert summary["m2655_protected_component_gates_all_passed"] is False
    assert summary["m2655_target_and_protected_gates_all_passed"] is False
    assert summary["m2655_selected_candidate_treated_as_winner"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_input_detected"] is False
    assert summary["follow_up_manifest_registered"] is True

    assert len(_read_csv(output_dir / "scenario_role_metric_report.csv")) == 4
    assert len(_read_csv(output_dir / "target_protected_tradeoff_rows.csv")) == 9
    assert len(_read_csv(output_dir / "protected_regression_focus_rows.csv")) == 8
    gate_rows = _read_csv(output_dir / "report_gate_evaluation.csv")
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.exists()
