import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_post_clearance_corrective_readiness_index import (
    materialize_post_clearance_corrective_readiness_index,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2804_readiness_index_preserves_negative_clearance_and_blockers(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2804.md"
    follow_up_manifest = tmp_path / "m2805.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_post_clearance_corrective_readiness_index(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_route_a_post_clearance_corrective_readiness_index_pass"
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["m2803_synthesis_pivot_preserved"] is True
    assert summary["m2801_triad_execution_row_count"] == 216
    assert summary["m2801_candidate_minus_source_delta_row_count"] == 72
    assert summary["m2801_candidate_minus_m2791_start_delta_row_count"] == 72
    assert summary["m2801_candidate_minus_source_obstacle_clearance_positive_count"] == 23
    assert summary["m2801_candidate_minus_source_obstacle_clearance_negative_count"] == 49
    assert summary["m2801_candidate_minus_m2791_start_obstacle_clearance_positive_count"] == 23
    assert summary["m2801_candidate_minus_m2791_start_obstacle_clearance_negative_count"] == 49
    assert summary["m2801_stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count"] == 4
    assert summary["m2801_stable_avoidable_candidate_minus_m2791_start_obstacle_clearance_negative_count"] == 2
    assert summary["m2801_negative_clearance_preserved"] is True
    assert summary["m2801_stable_avoidable_retention_risk_preserved"] is True
    assert summary["same_clearance_corrective_repair_loop_closed"] is True
    assert summary["same_clearance_corrective_update_admitted"] is False
    assert summary["same_style_triad_panel_admitted"] is False
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["admitted_next_action_count"] == 1
    assert summary["selected_next_action"] == "m2805_route_a_post_clearance_corrective_readiness_index_result_audit"
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

    assert {
        "m2803_clearance_corrective_branch_synthesis",
        "m2802_fresh_holdout_triad_result_audit",
        "m2801_fresh_holdout_triad_summary",
        "m2801_candidate_minus_source_clearance_deltas",
        "m2801_candidate_minus_m2791_start_clearance_deltas",
        "m2801_stable_avoidable_retention_risk",
        "m2800_clearance_corrective_training_result_audit",
        "m2799_clearance_corrective_preflight",
        "m2749_prior_route_a_readiness_index",
        "m2667_protected_mitigation_blocker",
        "m2541_baseline_actor_contract",
        "m2505_public_benchmark_pack",
        "m2508_runtime_inference_cost_report",
        "m2638_hf3_source_dependency_blocker",
        "post_m2470_route_plan",
    } == {row["evidence_id"] for row in evidence_rows}

    source_row = next(
        row for row in evidence_rows if row["evidence_id"] == "m2801_candidate_minus_source_clearance_deltas"
    )
    assert source_row["row_count"] == "72"
    assert source_row["clearance_positive_count"] == "23"
    assert source_row["clearance_negative_count"] == "49"
    assert source_row["hidden_oracle_actor_input_detected"] == "False"

    assert {
        "baseline_checkpoint_list",
        "actor_input_output_contract",
        "public_benchmark_pack",
        "known_failure_taxonomy",
        "runtime_inference_cost_report",
        "scenario_role_metric_report",
        "clearance_corrective_negative_result",
        "stable_avoidable_retention_risk",
        "protected_mitigation_blocker",
        "hf3_source_dependency",
        "driver_performance_or_validation",
    } == {row["deliverable_id"] for row in deliverable_rows}

    assert {
        "m2804_blocker_clearance_negative_fresh_holdout",
        "m2804_blocker_stable_avoidable_retention_risk",
        "m2804_blocker_same_clearance_corrective_local_search",
        "m2804_blocker_protected_mitigation",
        "m2804_blocker_hf3_source_dependency_unavailable",
        "m2804_blocker_validation_performance_not_admitted",
        "m2804_blocker_actor_contract_guard",
    } == {row["blocker_id"] for row in blocker_rows}

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == "m2805_route_a_post_clearance_corrective_readiness_index_result_audit"
    assert {
        row["admission_status"]
        for row in next_rows
        if row["candidate_action_id"] == "same_clearance_localized_corrective_update"
    } == {"not_admitted"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2804"] == "True"}
    assert allowed_claims == {
        "route_a_post_clearance_corrective_readiness_index_materialized",
        "m2801_negative_clearance_indexed",
        "stable_avoidable_retention_risk_indexed",
        "route_a_deliverable_readiness_refreshed",
        "protected_blocker_preserved",
        "hf3_blocker_preserved",
        "actor_contract_indexed",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
