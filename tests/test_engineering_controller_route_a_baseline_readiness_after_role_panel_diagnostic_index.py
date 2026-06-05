import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index import (
    materialize_baseline_readiness_after_role_panel_diagnostic_index,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2749_readiness_index_preserves_role_panel_diagnostic_and_blockers(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2749.md"
    follow_up_manifest = tmp_path / "m2750.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_baseline_readiness_after_role_panel_diagnostic_index(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_route_a_baseline_readiness_after_role_panel_diagnostic_index_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["m2746_execution_row_count"] == 14
    assert summary["m2746_diagnostic_success_count"] == 1
    assert summary["m2746_diagnostic_collision_count"] == 1
    assert summary["m2746_offtrack_count"] == 9
    assert summary["m2746_speed_too_low_count"] == 3
    assert summary["m2746_unset_or_completed_count"] == 1
    assert summary["m2746_weak_diagnostic_preserved"] is True
    assert summary["same_panel_execution_closed"] is True
    assert summary["route_a_deliverable_readiness_row_count"] == 9
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["admitted_next_action_count"] == 1
    assert summary["selected_next_action"] == "m2750_route_a_readiness_after_role_panel_result_audit"
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_readiness_claim_made"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False

    evidence_rows = _read_csv(output_dir / "evidence_index.csv")
    deliverable_rows = _read_csv(output_dir / "deliverable_readiness_rows.csv")
    blocker_rows = _read_csv(output_dir / "blocker_matrix.csv")
    next_rows = _read_csv(output_dir / "next_action_admission_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    evidence_ids = {row["evidence_id"] for row in evidence_rows}
    assert {
        "m2748_role_panel_result_synthesis",
        "m2747_role_panel_result_audit",
        "m2746_role_panel_diagnostic_execution",
        "m2743_scenario_role_metric_panel",
        "m2740_failure_taxonomy",
        "m2667_route_a_artifact_readiness",
        "m2667_protected_mitigation_blocker",
        "m2541_baseline_actor_contract",
        "m2505_public_benchmark_pack",
        "m2508_runtime_inference_cost_report",
        "m2638_hf3_source_dependency_blocker",
        "post_m2470_route_plan",
    } == evidence_ids

    m2746_row = next(
        row for row in evidence_rows if row["evidence_id"] == "m2746_role_panel_diagnostic_execution"
    )
    assert m2746_row["row_count"] == "14"
    assert m2746_row["diagnostic_success_count"] == "1"
    assert m2746_row["collision_count"] == "1"
    assert m2746_row["offtrack_count"] == "9"
    assert m2746_row["speed_too_low_count"] == "3"
    assert m2746_row["unset_or_completed_count"] == "1"
    assert m2746_row["hidden_oracle_actor_input_detected"] == "False"

    assert {
        "baseline_checkpoint_list",
        "actor_input_output_contract",
        "public_benchmark_pack",
        "known_failure_taxonomy",
        "runtime_inference_cost_report",
        "scenario_role_metric_report",
        "protected_mitigation_blocker",
        "hf3_source_dependency",
        "driver_performance_or_validation",
    } == {row["deliverable_id"] for row in deliverable_rows}

    assert {
        "m2749_blocker_role_panel_weak_diagnostic",
        "m2749_blocker_same_panel_local_search",
        "m2749_blocker_protected_mitigation",
        "m2749_blocker_hf3_source_dependency_unavailable",
        "m2749_blocker_validation_performance_not_admitted",
        "m2749_blocker_actor_contract_guard",
    } == {row["blocker_id"] for row in blocker_rows}

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == "m2750_route_a_readiness_after_role_panel_result_audit"
    assert {
        row["admission_status"]
        for row in next_rows
        if row["candidate_action_id"] == "same_panel_role_execution"
    } == {"not_admitted"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2749"] == "True"}
    assert allowed_claims == {
        "route_a_readiness_after_role_panel_index_materialized",
        "m2746_role_panel_diagnostic_indexed",
        "route_a_deliverable_readiness_indexed",
        "m2667_protected_blocker_preserved",
        "m2638_hf3_blocker_preserved",
        "actor_contract_indexed",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
