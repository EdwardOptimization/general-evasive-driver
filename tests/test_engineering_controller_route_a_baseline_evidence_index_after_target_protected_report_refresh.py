import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh import (
    materialize_evidence_index_after_target_protected_report_refresh,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2659_evidence_index_refresh_indexes_target_and_protected_evidence(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2659.md"
    follow_up_manifest = tmp_path / "m2660.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_evidence_index_after_target_protected_report_refresh(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["new_repair_training_or_rollout_run"] is False
    assert summary["m2657_report_indexed"] is True
    assert summary["m2658_audit_indexed"] is True
    assert summary["target_protected_split_preserved"] is True
    assert summary["protected_failure_blocking"] is True
    assert summary["m2655_target_preservation_gates_all_passed"] is True
    assert summary["m2655_protected_component_gates_all_passed"] is False
    assert summary["m2655_target_and_protected_gates_all_passed"] is False
    assert summary["m2655_selected_candidate_treated_as_winner"] is False
    assert summary["admitted_next_action_count"] == 1
    assert (
        summary["selected_next_action"]
        == "m2660_route_a_baseline_evidence_index_refresh_result_audit"
    )
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False

    evidence_rows = _read_csv(output_dir / "evidence_index.csv")
    gap_rows = _read_csv(output_dir / "gap_matrix.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    next_rows = _read_csv(output_dir / "next_action_admission.csv")

    evidence_by_id = {row["evidence_id"]: row for row in evidence_rows}
    assert {
        "m2657_target_protected_report_summary",
        "m2657_target_tradeoff_rows",
        "m2657_protected_tradeoff_rows",
        "m2657_protected_regression_focus_rows",
        "m2658_target_protected_report_result_audit",
    }.issubset(evidence_by_id)
    assert evidence_by_id["m2657_target_tradeoff_rows"]["target_or_protected"] == "target"
    assert evidence_by_id["m2657_target_tradeoff_rows"]["target_improvement_evidence"] == "True"
    assert evidence_by_id["m2657_target_tradeoff_rows"]["protected_failure_blocking"] == "False"
    assert evidence_by_id["m2657_protected_tradeoff_rows"]["target_or_protected"] == "protected"
    assert evidence_by_id["m2657_protected_tradeoff_rows"]["protected_failure_blocking"] == "True"
    assert {row["hidden_oracle_actor_input_detected"] for row in evidence_rows} == {"False"}
    assert {row["source_exists"] for row in evidence_rows} == {"True"}

    protected_gap = {row["gap_id"]: row for row in gap_rows}[
        "route_a_protected_mitigation_blocker"
    ]
    assert protected_gap["current_status"] == "blocking"
    assert protected_gap["admission_to_next_action"] == "blocks_repair_success_and_promotion"

    allowed_claims = {
        row["claim_family"] for row in claim_rows if row["allowed_in_m2659"] == "True"
    }
    assert {
        "baseline_evidence_index_refreshed",
        "target_protected_report_indexed",
        "protected_failure_blocker_indexed",
        "follow_up_result_audit_registered",
    } == allowed_claims
    assert {row["status_pass"] for row in claim_rows} == {"True"}

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == (
        "m2660_route_a_baseline_evidence_index_refresh_result_audit"
    )
    assert doc_path.read_text(encoding="utf-8").strip()
