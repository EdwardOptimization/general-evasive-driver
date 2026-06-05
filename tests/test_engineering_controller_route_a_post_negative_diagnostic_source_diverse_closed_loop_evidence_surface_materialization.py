import csv
from pathlib import Path

from autodrift.engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_materialization import (
    materialize_post_negative_source_diverse_evidence_surface,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _truthy(row, key: str) -> bool:
    return row[key] == "True"


def test_m2734_materializes_source_diverse_surface_without_same_surface_repair_or_overclaim(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2734.md"
    follow_up_manifest = tmp_path / "m2735.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    summary = materialize_post_negative_source_diverse_evidence_surface(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_"
        "evidence_surface_materialization_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["input_source_row_count"] == 6
    assert summary["evidence_surface_candidate_row_count"] == 18
    assert summary["m2693_candidate_row_count"] == 9
    assert summary["m2716_candidate_row_count"] == 9
    assert summary["source_diversity_family_count"] == 2
    assert summary["source_diversity_bucket_row_count"] == 2
    assert summary["blocked_surface_row_count"] == 12
    assert summary["negative_diagnostic_context_row_count"] == 31
    assert summary["m2728_success_count"] == 1
    assert summary["m2728_collision_count"] == 3
    assert summary["m2728_offtrack_count"] == 27
    assert summary["m2728_negative_diagnostic_preserved"] is True
    assert summary["same_surface_repair_execution_admitted"] is False
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["selected_next_action"] == (
        "m2735_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_result_audit"
    )
    assert summary["environment_reset_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_result_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["level3_self_id_claim_made"] is False

    candidate_rows = _read_csv(output_dir / "evidence_surface_candidate_rows.csv")
    diversity_rows = _read_csv(output_dir / "source_diversity_bucket_rows.csv")
    blocked_rows = _read_csv(output_dir / "blocked_surface_rows.csv")
    context_rows = _read_csv(output_dir / "negative_diagnostic_context_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert len(candidate_rows) == 18
    assert {row["materialization_admitted"] for row in candidate_rows} == {"True"}
    assert {row["same_surface_m2728_repair"] for row in candidate_rows} == {"False"}
    assert {row["protected_or_hf3_blocked"] for row in candidate_rows} == {"False"}
    assert {row["diagnostic_only_no_verdict"] for row in candidate_rows} == {"True"}
    assert {row["hidden_oracle_actor_input_detected"] for row in candidate_rows} == {"False"}

    m2693_rows = [row for row in candidate_rows if row["source_milestone"] == "m2693"]
    m2716_rows = [row for row in candidate_rows if row["source_milestone"] == "m2716"]
    assert len(m2693_rows) == 9
    assert len(m2716_rows) == 9
    assert {row["source_execution_row_count"] for row in m2693_rows} == {"1"}
    assert {row["source_execution_row_count"] for row in m2716_rows} == {"4"}
    assert sum(int(row["offtrack_count"]) for row in m2693_rows) == 7
    assert sum(int(row["speed_too_low_count"]) for row in m2693_rows) == 2
    assert sum(int(row["diagnostic_success_count"]) for row in m2716_rows) == 3
    assert sum(int(row["collision_count"]) for row in m2716_rows) == 2
    assert sum(int(row["offtrack_count"]) for row in m2716_rows) == 31

    assert len(diversity_rows) == 2
    assert {row["candidate_count"] for row in diversity_rows} == {"9"}
    assert {row["same_surface_m2728_repair_count"] for row in diversity_rows} == {"0"}
    assert {row["protected_or_hf3_blocked_count"] for row in diversity_rows} == {"0"}

    assert len(blocked_rows) == 12
    assert {
        row["blocked_family"]
        for row in blocked_rows
    } == {"same_surface_repair_loop", "protected_mitigation_blocker", "hf3_source_dependency_blocker"}
    same_surface_block = next(row for row in blocked_rows if row["blocked_family"] == "same_surface_repair_loop")
    assert same_surface_block["blocking_count"] == "31"
    assert same_surface_block["materialization_admitted"] == "False"
    assert len([row for row in blocked_rows if row["blocked_family"] == "protected_mitigation_blocker"]) == 10
    assert {row["actor_visible_allowed"] for row in blocked_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in blocked_rows} == {"False"}

    assert len(context_rows) == 31
    assert sum(1 for row in context_rows if _truthy(row, "success")) == 1
    assert sum(1 for row in context_rows if _truthy(row, "collision")) == 3
    assert sum(1 for row in context_rows if row["termination_reason"] == "off_track") == 27
    assert {row["direct_same_surface_repair_execution_admitted"] for row in context_rows} == {"False"}
    assert {row["diagnostic_only_no_verdict"] for row in context_rows} == {"True"}

    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {row["actor_visible_allowed"] for row in actor_rows} == {"False"}
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2734"] == "True"}
    assert allowed_claims == {
        "source_diverse_evidence_surface_materialized",
        "source_diverse_candidate_rows_materialized",
        "m2728_negative_diagnostic_context_preserved",
        "same_surface_repair_rejected",
        "protected_blocker_preserved",
        "hf3_blocker_preserved",
        "actor_contract_preserved",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
