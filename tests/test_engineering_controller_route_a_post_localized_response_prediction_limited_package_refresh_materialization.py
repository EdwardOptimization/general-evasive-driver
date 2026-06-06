import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_post_localized_response_prediction_limited_package_refresh_materialization import (
    materialize_post_localized_response_prediction_limited_package_refresh,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2873_limited_package_refresh_materializes_latest_negative_evidence(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2873.md"
    follow_up_manifest = tmp_path / "m2874.json"

    summary = materialize_post_localized_response_prediction_limited_package_refresh(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_post_localized_response_prediction_limited_package_refresh_materialization_pass"
    )
    assert summary["route_a_package_content_covered"] == 6
    assert summary["route_a_package_limitations_covered"] == 9
    assert summary["latest_negative_evidence_row_count"] == 5
    assert summary["known_blocker_disclosure_row_count"] == 8
    assert summary["m2824_recoverability_available_count"] == 0
    assert summary["m2824_recoverability_success_count"] == 0
    assert summary["m2838_diagnostic_success_count"] == 1
    assert summary["m2838_diagnostic_collision_count"] == 2
    assert summary["m2838_diagnostic_offtrack_count"] == 13
    assert summary["m2868_baseline_success_count"] == 0
    assert summary["m2868_candidate_success_count"] == 0
    assert summary["m2868_baseline_collision_count"] == 1
    assert summary["m2868_candidate_collision_count"] == 1
    assert summary["m2868_terminal_outcomes_unchanged"] is True
    assert summary["protected_mitigation_blocker_visible"] is True
    assert summary["localized_response_prediction_no_terminal_improvement_visible"] is True
    assert summary["hf3_dependency_blocker_visible"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["package_labels_actor_visible"] is False
    assert summary["diagnostic_labels_actor_visible"] is False
    assert summary["package_published"] is False
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["repair_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_readiness_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["selected_next_action"] == "m2874_limited_package_refresh_materialization_result_audit"

    schema_rows = _read_csv(output_dir / "package_manifest_schema_rows.csv")
    artifact_rows = _read_csv(output_dir / "package_artifact_inventory_rows.csv")
    provenance_rows = _read_csv(output_dir / "package_provenance_map_rows.csv")
    negative_rows = _read_csv(output_dir / "latest_negative_evidence_rows.csv")
    blocker_rows = _read_csv(output_dir / "known_blocker_disclosure_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_action_contract_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "package_gate_matrix.csv")

    assert {row["field_name"] for row in schema_rows}.issuperset(
        {"refresh_reason", "evidence_cutoff_milestone", "latest_negative_evidence_refs"}
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
        "scenario_role_metric_report",
        "known_failure_taxonomy",
    }
    limitation_artifacts = {
        row["artifact_id"]
        for row in artifact_rows
        if row["artifact_role"] == "package_limitations" and row["package_inclusion_status"] == "included_with_limitations"
    }
    assert {
        "prior_limited_package_summary",
        "fresh_source_diverse_negative_diagnostics",
        "localized_response_prediction_negative_diagnostics",
        "hf3_source_dependency_blocker",
    }.issubset(limitation_artifacts)

    assert len(provenance_rows) >= 18
    assert {row["source_exists"] for row in provenance_rows} == {"True"}

    negative_by_id = {row["negative_evidence_id"]: row for row in negative_rows}
    assert set(negative_by_id) == {
        "protected_mitigation_blocker",
        "negative_recoverability_diagnostics",
        "negative_mechanism_localized_repair",
        "fresh_source_diverse_negative_diagnostics",
        "localized_response_prediction_no_terminal_improvement",
    }
    assert "1 diagnostic success, 2 collisions, 13 off_track rows" in negative_by_id[
        "fresh_source_diverse_negative_diagnostics"
    ]["observed_value"]
    assert "baseline success 0 candidate success 0 baseline collision 1 candidate collision 1" in negative_by_id[
        "localized_response_prediction_no_terminal_improvement"
    ]["observed_value"]
    assert {row["actor_visible"] for row in negative_rows} == {"False"}
    assert {row["ordinary_success_denominator_allowed"] for row in negative_rows} == {"False"}

    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    assert {
        "protected_mitigation_blocker",
        "offtrack_collision_behavior",
        "recoverability_gap",
        "localized_response_prediction_no_terminal_improvement",
        "hf3_dependency_blocker",
        "self_id_gap",
        "scenario_sampling_caution",
        "package_publication_blocker",
    } == blocker_ids
    assert {row["package_disclosure_required"] for row in blocker_rows} == {"True"}
    assert {row["actor_visible"] for row in blocker_rows} == {"False"}

    actor_by_field = {row["contract_field"]: row for row in actor_rows}
    assert actor_by_field["observation_shape"]["observed_value"] == "72"
    assert actor_by_field["action_shape"]["observed_value"] == "3"
    assert actor_by_field["hidden_oracle_actor_input_detected"]["observed_value"] == "False"
    assert actor_by_field["diagnostic_labels_actor_visible"]["observed_value"] == "False"
    assert {row["status_pass"] for row in actor_rows} == {"True"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2873"] == "True"}
    assert allowed_claims == {
        "local_package_refresh_materialized",
        "prior_package_traced",
        "latest_negative_evidence_disclosed",
        "actor_contract_preserved",
        "bounded_audit_handoff",
    }
    blocked_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2873"] == "False"}
    assert {
        "driver_performance",
        "localized_response_prediction_success",
        "validation_readiness",
        "paper_evidence",
        "current_sim_verdict",
        "high_fidelity_validation_result",
        "level3_self_identification",
    }.issubset(blocked_claims)
    assert {row["status_pass"] for row in claim_rows} == {"True"}

    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {
        "m2873_gate_m2838_negative_diagnostics_included",
        "m2873_gate_m2868_no_terminal_improvement_included",
        "m2873_gate_m2836_hf3_blocker_preserved",
        "m2873_gate_no_performance_or_paper_claim",
    }.issubset({row["gate_id"] for row in gate_rows})

    assert doc_path.read_text(encoding="utf-8").strip()
    assert follow_up_manifest.exists()
    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"].startswith("m2874-")
    assert follow_up["commands"][0]["command"] == "true"
