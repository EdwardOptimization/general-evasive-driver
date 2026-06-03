import csv
import json

from autodrift.engineering_controller_failure_surface_mitigation_regression_localization import (
    run_mitigation_regression_localization,
)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_mitigation_regression_localization_identifies_single_regressed_seed(tmp_path):
    output_dir = tmp_path / "run"

    summary = run_mitigation_regression_localization(output_dir)

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_failure_surface_mitigation_regression_localization_pass"
    )
    assert summary["mitigation_row_count"] == 5
    assert summary["mitigation_improved_row_count"] == 4
    assert summary["mitigation_regressed_row_count"] == 1
    assert (
        summary["regressed_source_row_id"]
        == "m2523_m1154_policy_actor_unavoidable_mitigation_seed_254302"
    )
    assert summary["regressed_seed"] == 254302
    assert summary["single_low_baseline_regression"] is True
    assert summary["all_mitigation_rows_road_margin_improved"] is True
    assert summary["all_mitigation_rows_command_conflict_improved"] is True
    assert summary["proof_washout_detected"] is True
    assert summary["behavior_regression_detected"] is True
    assert summary["objective_weakness_detected"] is True
    assert summary["metric_artifact_detected"] is False
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["candidate_config_mutated"] is False
    assert summary["active_config_overwritten"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["new_policy_action_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["fresh_generalization_run"] is False

    rows = _read_csv(output_dir / "mitigation_regression_rows.csv")
    findings = json.loads((output_dir / "localization_findings.json").read_text())

    assert len(rows) == 5
    assert {row["row_class"] for row in rows} == {
        "improved_mitigation_row",
        "regressed_mitigation_row",
    }
    regressed = [row for row in rows if row["row_class"] == "regressed_mitigation_row"]
    assert len(regressed) == 1
    assert regressed[0]["seed"] == "254302"
    assert regressed[0]["localization_label"] == (
        "low_baseline_severity_tradeoff_after_command_conflict_projection"
    )
    assert float(regressed[0]["severity_delta"]) > 0.0
    assert float(regressed[0]["road_margin_delta_m"]) > 0.0
    assert float(regressed[0]["command_conflict_delta"]) < 0.0
    assert findings["decision"] == "route_to_mitigation_preserving_repair_design"
    assert findings["metric_artifact_detected"] is False
    assert findings["recommended_next_manifest"] == (
        "m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design"
    )
