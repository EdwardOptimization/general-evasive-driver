import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_package_with_limitations_protocol_materialization import (
    materialize_package_with_limitations_protocol,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2688_package_protocol_materialization_preserves_limitations(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2688.md"
    follow_up_manifest = tmp_path / "m2689.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_package_with_limitations_protocol(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_route_a_package_with_limitations_protocol_materialization_pass"
    assert summary["package_published"] is False
    assert summary["route_a_required_artifacts_covered"] == 6
    assert summary["route_a_artifact_coverage_complete"] is True
    assert summary["protected_mitigation_blocker_visible"] is True
    assert summary["current_sim_offtrack_blocker_visible"] is True
    assert summary["hf3_source_dependency_blocker_visible"] is True
    assert summary["paper_self_id_blocker_visible"] is True
    assert summary["m2684_offtrack_outcome_count"] == 202
    assert summary["m2684_offtrack_termination_count"] == 203
    assert summary["m2664_protected_gate_blocking_row_count"] == 25
    assert summary["m2664_protected_gate_regressed_row_count"] == 79
    assert summary["m2635_availability_blocker"] == "dependency_source_unavailable"
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
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
    assert summary["selected_next_action"] == "m2689_package_protocol_materialization_result_audit"

    schema_rows = _read_csv(output_dir / "package_manifest_schema_rows.csv")
    artifact_rows = _read_csv(output_dir / "package_artifact_inventory_rows.csv")
    provenance_rows = _read_csv(output_dir / "package_provenance_map_rows.csv")
    blocker_rows = _read_csv(output_dir / "known_blocker_disclosure_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_action_contract_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "package_protocol_gate_matrix.csv")

    assert {row["field_name"] for row in schema_rows}.issuperset(
        {
            "package_id",
            "artifact_id",
            "source_path",
            "known_blocker_refs",
            "blocked_interpretation",
        }
    )

    required_artifacts = {
        row["artifact_id"]
        for row in artifact_rows
        if row["package_required"] == "True" and row["package_inclusion_status"] == "included_with_limitations"
    }
    assert required_artifacts == {
        "baseline_checkpoint_list",
        "actor_input_output_contract",
        "public_benchmark_pack",
        "runtime_inference_cost_report",
        "scenario_role_metric_report",
        "known_failure_taxonomy",
    }
    assert {
        "route_b_current_sim_offtrack_blocker",
        "hf3_source_dependency_blocker",
        "post_m2470_route_plan",
    }.issubset({row["artifact_id"] for row in artifact_rows if row["artifact_role"] == "supporting_context"})

    assert len(provenance_rows) >= 10
    assert {row["source_exists"] for row in provenance_rows} == {"True"}

    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    assert blocker_ids == {
        "protected_mitigation_blocker",
        "current_sim_offtrack_blocker",
        "hf3_source_dependency_blocker",
        "paper_self_id_blocker",
    }
    assert {row["package_disclosure_required"] for row in blocker_rows} == {"True"}
    assert {row["actor_visible"] for row in blocker_rows} == {"False"}
    offtrack_row = next(row for row in blocker_rows if row["blocker_id"] == "current_sim_offtrack_blocker")
    assert "202/216" in offtrack_row["blocker_status"]
    assert "203/216" in offtrack_row["blocker_status"]

    actor_by_field = {row["contract_field"]: row for row in actor_rows}
    assert actor_by_field["observation_shape"]["observed_value"] == "72"
    assert actor_by_field["action_shape"]["observed_value"] == "3"
    assert actor_by_field["hidden_oracle_actor_input_detected"]["observed_value"] == "False"
    assert actor_by_field["package_labels_actor_visible"]["actor_visible"] == "False"
    assert {row["status_pass"] for row in actor_rows} == {"True"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2688"] == "True"}
    assert allowed_claims == {
        "package_protocol_materialized",
        "package_artifacts_traced",
        "package_limitations_disclosed",
    }
    blocked_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2688"] == "False"}
    assert {
        "driver_performance",
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
        "m2688_gate_protected_mitigation_blocker_visible",
        "m2688_gate_current_sim_offtrack_blocker_visible",
        "m2688_gate_hf3_source_dependency_blocker_visible",
        "m2688_gate_no_package_publication",
    }.issubset({row["gate_id"] for row in gate_rows})
    assert doc_path.read_text(encoding="utf-8").strip()
