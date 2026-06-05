import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_a_post_recoverability_negative_readiness_index import (
    materialize_post_recoverability_negative_readiness_index,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2820_readiness_index_preserves_negative_recoverability_and_boundaries(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2820.md"
    follow_up_manifest = tmp_path / "m2821.json"

    summary = materialize_post_recoverability_negative_readiness_index(
        output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == "engineering_controller_route_a_post_recoverability_negative_readiness_index_pass"
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["m2819_admission_preserved"] is True
    assert summary["m2818_pivot_preserved"] is True
    assert summary["m2816_status_pass"] is True
    assert summary["m2816_gate_matrix_pass"] is True
    assert summary["m2816_fixed_row_count"] == 12
    assert summary["m2816_accounted_count"] == 12
    assert summary["m2816_episode_count"] == 12
    assert summary["m2816_execution_failure_count"] == 0
    assert summary["m2816_diagnostic_success_count"] == 6
    assert summary["m2816_diagnostic_collision_count"] == 1
    assert summary["m2816_diagnostic_offtrack_termination_count"] == 5
    assert summary["m2816_post_event_available_count"] == 7
    assert summary["m2816_recoverability_window_row_count"] == 12
    assert summary["m2816_recoverability_available_count"] == 0
    assert summary["m2816_recoverability_success_count"] == 0
    assert summary["m2816_negative_recoverability_preserved"] is True
    assert summary["m2804_prior_readiness_preserved"] is True
    assert summary["m2804_negative_clearance_preserved"] is True
    assert summary["m2804_stable_avoidable_retention_risk_preserved"] is True
    assert summary["same_recoverability_repair_admitted"] is False
    assert summary["same_recoverability_ranking_admitted"] is False
    assert summary["hf3_source_dependency_paused"] is True
    assert summary["protected_mitigation_blocker_preserved"] is True
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["guardrails_outside_success_denominator"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["observation_shape"] == 72
    assert summary["action_shape"] == 3
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["recoverability_labels_actor_visible"] is False
    assert summary["action_response_labels_actor_visible"] is False
    assert summary["admitted_next_action_count"] == 1
    assert summary["selected_next_action"] == "m2821_post_recoverability_negative_readiness_index_result_audit"
    assert summary["follow_up_manifest_exists"] is True
    assert summary["environment_reset_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["replay_run"] is False
    assert summary["measured_validation_run"] is False
    assert summary["training_run"] is False
    assert summary["ppo_run"] is False
    assert summary["repair_run"] is False
    assert summary["source_build_run"] is False
    assert summary["adapter_probe_run"] is False
    assert summary["external_high_fidelity_simulation_included"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["validation_readiness_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["full_ideal_driver_gate_passed"] is False
    assert summary["level3_self_id_claim_made"] is False

    evidence_rows = _read_csv(output_dir / "evidence_index.csv")
    deliverable_rows = _read_csv(output_dir / "deliverable_readiness_rows.csv")
    blocker_rows = _read_csv(output_dir / "blocker_matrix.csv")
    next_rows = _read_csv(output_dir / "next_action_admission_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {
        "m2819_post_recoverability_negative_index_design",
        "m2818_recoverability_window_branch_synthesis",
        "m2817_recoverability_window_result_audit",
        "m2816_recoverability_window_summary",
        "m2816_recoverability_window_rows",
        "m2816_post_offtrack_action_response_rows",
        "m2816_gate_matrix",
        "m2804_prior_readiness_index",
        "m2804_prior_evidence_index",
        "m2804_prior_blocker_matrix",
        "m2804_prior_next_action_admission",
        "m2805_prior_readiness_result_audit",
        "m2777_action_response_belief_synthesis",
        "m2643_source_only_generalization_synthesis",
        "m2541_baseline_actor_contract",
        "m2505_public_benchmark_pack",
        "m2508_runtime_inference_cost_report",
        "m2638_hf3_source_dependency_blocker",
        "post_m2470_route_plan",
    } == {row["evidence_id"] for row in evidence_rows}

    recoverability_row = next(row for row in evidence_rows if row["evidence_id"] == "m2816_recoverability_window_rows")
    assert recoverability_row["row_count"] == "12"
    assert recoverability_row["post_event_available_count"] == "7"
    assert recoverability_row["recoverability_window_available_count"] == "0"
    assert recoverability_row["recoverability_success_count"] == "0"
    assert recoverability_row["diagnostic_collision_count"] == "1"
    assert recoverability_row["diagnostic_offtrack_termination_count"] == "5"
    assert recoverability_row["hidden_oracle_actor_input_detected"] == "False"

    assert {
        "baseline_checkpoint_list",
        "actor_input_output_contract",
        "public_benchmark_pack",
        "known_failure_taxonomy",
        "runtime_inference_cost_report",
        "scenario_role_metric_report",
        "prior_clearance_corrective_readiness_index",
        "post_recoverability_negative_result",
        "action_response_recoverability_diagnostic_rows",
        "protected_mitigation_and_guardrail_boundary",
        "hf3_source_dependency",
        "driver_performance_or_validation",
    } == {row["deliverable_id"] for row in deliverable_rows}

    assert {
        "m2820_blocker_recoverability_window_absent",
        "m2820_blocker_diagnostic_collision_and_offtrack",
        "m2820_blocker_same_recoverability_local_search",
        "m2820_blocker_negative_clearance_and_stable_avoidable_retention",
        "m2820_blocker_protected_mitigation_and_guardrails",
        "m2820_blocker_hf3_source_dependency_unavailable",
        "m2820_blocker_validation_performance_not_admitted",
        "m2820_blocker_actor_contract_guard",
    } == {row["blocker_id"] for row in blocker_rows}

    admitted = [row for row in next_rows if row["admission_status"] == "admitted"]
    assert len(admitted) == 1
    assert admitted[0]["candidate_action_id"] == "m2821_post_recoverability_negative_readiness_index_result_audit"
    assert {
        row["admission_status"]
        for row in next_rows
        if row["candidate_action_id"] == "same_recoverability_window_repair_or_ranking"
    } == {"not_admitted"}
    assert {
        row["admission_status"]
        for row in next_rows
        if row["candidate_action_id"] == "validation_or_driver_performance_claim"
    } == {"not_admitted"}

    allowed_claims = {row["claim_family"] for row in claim_rows if row["allowed_in_m2820"] == "True"}
    assert allowed_claims == {
        "route_a_post_recoverability_negative_readiness_index_materialized",
        "m2816_negative_recoverability_indexed",
        "m2818_pivot_preserved",
        "m2804_prior_readiness_blockers_carried_forward",
        "negative_clearance_and_stable_avoidable_risk_preserved",
        "protected_guardrails_preserved",
        "hf3_blocker_preserved",
        "actor_contract_indexed",
        "follow_up_result_audit_registered",
    }
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == "m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-materialization-result-audit"
    assert follow_up["type"] == "gate"
    assert follow_up["gate_tier"] == "process"
    assert follow_up["commands"] == [{"name": "result_audit", "command": "true"}]
    assert follow_up["scoreboard_checkpoint"] == (
        "docs/m2821-engineering-controller-route-a-post-recoverability-negative-readiness-index-"
        "materialization-result-audit.md"
    )
