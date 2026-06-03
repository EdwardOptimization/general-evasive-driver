import csv
import json

from autodrift.engineering_controller_source_only_behavior_outcome_rows import (
    METRIC_GAP_FIELDNAMES,
    materialize_source_only_behavior_outcome_rows,
)


FALSE_CLAIM_FLAGS = [
    "environment_rollout_run",
    "simulator_step_run",
    "external_high_fidelity_simulation_included",
    "policy_action_run",
    "policy_rollout_run",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_computed",
    "controller_family_verdict_computed",
    "driver_performance_claim_made",
    "verdict_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
]


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materialize_source_only_behavior_outcome_rows_writes_protocol_rows(tmp_path):
    out = tmp_path / "run"
    doc = tmp_path / "m2516.md"

    summary = materialize_source_only_behavior_outcome_rows(
        out,
        milestone="m2516-test",
        next_blocker="m2517-test",
        doc_path=doc,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_source_only_behavior_outcome_row_completeness_pass"
    )
    assert summary["behavior_outcome_row_count"] == 12
    assert summary["expected_behavior_outcome_row_count"] == 12
    assert summary["m2498_source_row_count"] == 3
    assert summary["m2501_source_row_count"] == 9
    assert summary["row_schema_field_count"] == 51
    assert summary["metric_registry_row_count"] == 40
    assert summary["metric_gap_row_count"] == 40
    assert summary["all_rows_have_required_fields"] is True
    assert summary["all_rows_source_only_diagnostic"] is True
    assert summary["all_rows_diagnostic_only_no_ranking_claim"] is True
    assert summary["metric_gaps_explicit"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["source_only_layer_separated_from_validation"] is True
    assert summary["partial_metric_names"] == []

    for flag in FALSE_CLAIM_FLAGS:
        assert summary[flag] is False

    rows = _read_csv(out / "behavior_outcome_rows.csv")
    assert len(rows) == 12
    assert len(rows[0]) == 51
    assert {row["evidence_layer"] for row in rows} == {"source_only_diagnostic"}
    assert {row["diagnostic_only_no_ranking_claim"] for row in rows} == {"true"}
    assert {row["observation_shape"] for row in rows} == {"72"}
    assert {row["action_shape"] for row in rows} == {"3"}
    assert {row["actor_input_leak_flags"] for row in rows} == {""}
    assert {row["success_rate_computed"] for row in rows if "success_rate_computed" in row} == set()
    assert all("collision_event" in row["metric_completeness_flags"] for row in rows)
    assert all("driver performance" in row["forbidden_interpretation"] for row in rows)
    assert {row["source_artifact"] for row in rows} == {
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv",
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv",
    }

    summary_on_disk = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary_on_disk == summary
    assert doc.exists()


def test_metric_gap_summary_keeps_unsupported_outcome_metrics_explicit(tmp_path):
    out = tmp_path / "run"
    summary = materialize_source_only_behavior_outcome_rows(out, doc_path=tmp_path / "m2516.md")

    gaps = _read_csv(out / "metric_gap_summary.csv")
    assert len(gaps) == summary["metric_registry_row_count"]
    assert set(gaps[0]) == set(METRIC_GAP_FIELDNAMES)
    gaps_by_name = {row["metric_name"]: row for row in gaps}

    for metric_name in [
        "collision_event",
        "obstacle_passed_event",
        "minimum_obstacle_clearance_m",
        "minimum_road_margin_m",
        "mitigation_delta_against_reference",
    ]:
        assert gaps_by_name[metric_name]["supported_row_count"] == "0"
        assert gaps_by_name[metric_name]["missing_row_count"] == "12"
        assert (
            gaps_by_name[metric_name]["support_status"]
            == "unsupported_by_existing_source_artifacts"
        )

    for metric_name in [
        "observation_shape",
        "action_shape",
        "action_finite",
        "action_within_bounds",
        "maximum_abs_yaw_rate",
        "maximum_abs_lateral_position",
        "diagnostic_only_no_ranking_claim",
    ]:
        assert gaps_by_name[metric_name]["supported_row_count"] == "12"
        assert gaps_by_name[metric_name]["missing_row_count"] == "0"

    assert set(summary["unsupported_metric_names"]).issuperset(
        {
            "collision_event",
            "minimum_obstacle_clearance_m",
            "mitigation_delta_against_reference",
        }
    )
