import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_post_recoverability_negative_limited_package_materialization import (
    materialize_post_recoverability_limited_package,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2824_limited_package_materialization_preserves_recoverability_blockers(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2824.md"
    follow_up_manifest = tmp_path / "m2825.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_post_recoverability_limited_package(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_post_recoverability_negative_limited_package_materialization_pass"
    )
    assert summary["route_a_package_content_covered"] == 6
    assert summary["route_a_package_limitations_covered"] == 4
    assert summary["negative_recoverability_blocker_visible"] is True
    assert summary["same_recoverability_local_search_blocked"] is True
    assert summary["post_clearance_blocker_visible"] is True
    assert summary["hf3_source_dependency_blocker_visible"] is True
    assert summary["route_b_paper_self_id_blocker_visible"] is True
    assert summary["m2816_post_event_available_count"] == 7
    assert summary["m2816_recoverability_available_count"] == 0
    assert summary["m2816_recoverability_success_count"] == 0
    assert summary["m2816_diagnostic_collision_count"] == 1
    assert summary["m2816_diagnostic_offtrack_termination_count"] == 5
    assert summary["m2820_evidence_index_row_count"] == 19
    assert summary["m2820_deliverable_readiness_row_count"] == 12
    assert summary["m2820_blocker_matrix_row_count"] == 8
    assert summary["m2820_next_action_admission_row_count"] == 7
    assert summary["m2820_claim_boundary_row_count"] == 31
    assert summary["m2820_gate_matrix_row_count"] == 42
    assert summary["m2804_negative_clearance_preserved"] is True
    assert summary["m2804_stable_avoidable_retention_risk_preserved"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["package_published"] is False
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["recoverability_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_readiness_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["selected_next_action"] == "m2825_limited_package_materialization_result_audit"

    schema_rows = _read_csv(output_dir / "package_manifest_schema_rows.csv")
    artifact_rows = _read_csv(output_dir / "package_artifact_inventory_rows.csv")
    provenance_rows = _read_csv(output_dir / "package_provenance_map_rows.csv")
    blocker_rows = _read_csv(output_dir / "known_blocker_disclosure_rows.csv")
    recoverability_rows = _read_csv(output_dir / "recoverability_limitations_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_action_contract_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "package_gate_matrix.csv")

    assert {row["field_name"] for row in schema_rows}.issuperset(
        {"package_id", "known_blocker_refs", "post_recoverability_refs"}
    )

    package_content = {
        row["artifact_id"]
        for row in artifact_rows
        if row["artifact_role"] == "package_content" and row["package_inclusion_status"] == "included_with_limitations"
    }
    assert package_content == {
        "baseline_checkpoint_list",
        "actor_input_output_contract",
        "public_benchmark_pack",
        "runtime_inference_cost_report",
        "scenario_role_metric_report_plan",
        "known_failure_taxonomy",
    }
    limitation_artifacts = {
        row["artifact_id"]
        for row in artifact_rows
        if row["artifact_role"] == "package_limitations" and row["package_inclusion_status"] == "included_with_limitations"
    }
    assert limitation_artifacts == {
        "post_clearance_readiness_blockers",
        "negative_recoverability_diagnostics",
        "post_recoverability_readiness_index",
        "hf3_source_dependency_blocker",
    }

    assert len(provenance_rows) >= 14
    assert {row["source_exists"] for row in provenance_rows} == {"True"}

    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    assert blocker_ids == {
        "post_clearance_blocker",
        "negative_recoverability_blocker",
        "same_recoverability_local_search_blocker",
        "hf3_source_dependency_blocker",
        "route_b_paper_self_id_blocker",
    }
    assert {row["package_disclosure_required"] for row in blocker_rows} == {"True"}
    assert {row["actor_visible"] for row in blocker_rows} == {"False"}

    recoverability_by_id = {row["limitation_id"]: row for row in recoverability_rows}
    assert recoverability_by_id["recoverability_window_available_rows"]["observed_value"] == "0"
    assert recoverability_by_id["recoverability_success_rows"]["observed_value"] == "0"
    assert recoverability_by_id["diagnostic_collision_outcomes"]["observed_value"] == "1"
    assert recoverability_by_id["diagnostic_offtrack_terminations"]["observed_value"] == "5"
    assert recoverability_by_id["same_recoverability_repair_or_ranking_admitted"]["observed_value"] == "False"
    assert {row["actor_visible"] for row in recoverability_rows} == {"False"}

    actor_by_field = {row["contract_field"]: row for row in actor_rows}
    assert actor_by_field["observation_shape"]["observed_value"] == "72"
    assert actor_by_field["action_shape"]["observed_value"] == "3"
    assert actor_by_field["hidden_oracle_actor_input_detected"]["observed_value"] == "False"
    assert actor_by_field["recoverability_labels_actor_visible"]["actor_visible"] == "False"
    assert {row["status_pass"] for row in actor_rows} == {"True"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2824"] == "True"}
    assert allowed_claims == {
        "limited_package_materialized",
        "post_recoverability_limitations_disclosed",
        "package_artifacts_traced",
    }
    blocked_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2824"] == "False"}
    assert {
        "driver_performance",
        "repair_success",
        "recoverability_success",
        "validation_readiness",
        "paper_evidence",
        "finite_window_vs_gru",
        "current_sim_verdict",
        "high_fidelity_validation_result",
        "level3_self_identification",
    }.issubset(blocked_claims)
    assert {row["status_pass"] for row in claim_rows} == {"True"}

    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {
        "m2824_gate_negative_recoverability_blocker_visible",
        "m2824_gate_recoverability_limitations_complete",
        "m2824_gate_same_recoverability_local_search_blocked",
        "m2824_gate_no_validation_or_driver_performance_claim",
    }.issubset({row["gate_id"] for row in gate_rows})
    assert doc_path.read_text(encoding="utf-8").strip()
