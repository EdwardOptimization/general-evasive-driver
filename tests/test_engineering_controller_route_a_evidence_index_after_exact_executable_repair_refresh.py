import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh import (
    materialize_evidence_index_after_exact_executable_repair_refresh,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2731_evidence_index_preserves_negative_repair_diagnostic_and_blockers(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2731.md"
    follow_up_manifest = tmp_path / "m2732.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_evidence_index_after_exact_executable_repair_refresh(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["repair_execution_row_count"] == 31
    assert summary["m2728_success_count"] == 1
    assert summary["m2728_collision_count"] == 3
    assert summary["m2728_offtrack_count"] == 27
    assert summary["m2728_negative_diagnostic_preserved"] is True
    assert summary["same_surface_repair_closed"] is True
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["admitted_next_action_count"] == 1
    assert summary["selected_next_action"] == (
        "m2732_route_a_evidence_index_after_exact_executable_repair_result_audit"
    )
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
    blocker_rows = _read_csv(output_dir / "blocker_matrix.csv")
    next_rows = _read_csv(output_dir / "next_action_admission_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    evidence_ids = {row["evidence_id"] for row in evidence_rows}
    assert {
        "m2730_repair_result_synthesis",
        "m2728_negative_offtrack_repair_diagnostic",
        "m2667_protected_readiness_blocker",
        "m2638_hf3_source_dependency_blocker",
        "m2541_baseline_actor_contract",
        "post_m2470_route_plan",
    }.issubset(evidence_ids)

    m2728_row = next(
        row for row in evidence_rows if row["evidence_id"] == "m2728_negative_offtrack_repair_diagnostic"
    )
    assert m2728_row["row_count"] == "31"
    assert m2728_row["diagnostic_success_count"] == "1"
    assert m2728_row["collision_count"] == "3"
    assert m2728_row["offtrack_count"] == "27"
    assert m2728_row["hidden_oracle_actor_input_detected"] == "False"

    assert {
        "m2731_blocker_current_m1690_exact_executable_offtrack_negative",
        "m2731_blocker_same_surface_repair_local_search",
        "m2731_blocker_protected_mitigation",
        "m2731_blocker_hf3_source_dependency_unavailable",
    }.issubset({row["blocker_id"] for row in blocker_rows})

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == (
        "m2732_route_a_evidence_index_after_exact_executable_repair_result_audit"
    )
    assert {
        row["admission_status"]
        for row in next_rows
        if row["candidate_action_id"] == "same_surface_exact_executable_offtrack_repair_execution"
    } == {"not_admitted"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2731"] == "True"}
    assert allowed_claims == {
        "route_a_evidence_index_materialized",
        "m2728_negative_diagnostic_indexed",
        "m2638_hf3_blocker_preserved",
        "actor_contract_indexed",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
