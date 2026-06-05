import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_c_hf0_source_only_interface_evidence_handoff_materialization import (
    materialize_route_c_hf0_source_only_interface_evidence_handoff,
)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_m2832_hf0_source_only_handoff_materialization_preserves_boundaries(tmp_path):
    output_dir = tmp_path / "run"
    follow_up_manifest = tmp_path / "m2833.json"

    summary = materialize_route_c_hf0_source_only_interface_evidence_handoff(
        output_dir,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_c_hf0_source_only_interface_evidence_handoff_materialization_pass"
    )
    assert summary["source_artifacts_reanalyzed_only"] is True
    assert summary["source_artifacts_exist"] is True
    assert summary["missing_source_artifacts"] == []
    assert summary["required_artifacts_present"] is True
    assert summary["handoff_artifact_inventory_row_count"] >= 17
    assert summary["source_only_interface_handoff_row_count"] >= 10
    assert summary["actor_contract_guard_row_count"] == 11
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["blocker_boundary_row_count"] == 3
    assert summary["claim_boundary_row_count"] == 20
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["follow_up_manifest_exists"] is True
    assert summary["selected_next_action"] == "m2833_route_c_hf0_source_only_interface_evidence_handoff_result_audit"

    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["actor_view_only_extraction"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["labels_actor_visible"] is False
    assert summary["diagnostics_actor_visible"] is False
    assert summary["m2482_catalog_row_count"] == 10
    assert summary["m2482_source_only_admitted_fixture_count"] == 3
    assert summary["m2484_fixture_count"] == 3
    assert summary["m2484_reset_count"] == 3
    assert summary["m2484_step_count"] == 6
    assert summary["m2484_canned_actions_only"] is True
    assert summary["m2498_telemetry_row_count"] == 300
    assert summary["m2498_unique_role_reset_observation_digest_count"] == 3
    assert summary["m2498_role_reset_observation_digests_differentiated"] is True
    assert summary["m2501_subject_count"] == 3
    assert summary["m2501_role_count"] == 3
    assert summary["m2501_telemetry_row_count"] == 900
    assert summary["m2501_role_subject_panel_row_count"] == 9
    assert summary["m2505_required_files_present"] is True
    assert summary["m2508_measurement_row_count"] == 300
    assert summary["m2508_model_parameter_count"] == 164679
    assert summary["m2548_hf0_p0_parity_check_count"] == 5
    assert summary["m2548_action_mapping_check_count"] == 7
    assert summary["m2548_actor_inference_cost_row_count"] == 270
    assert summary["m2592_source_only_adapter_blocker_closure_claim_allowed"] is True
    assert summary["m2638_selected_platform_source_dependency_blocker_active"] is True
    assert summary["m2828_candidate_execution_row_count"] == 16
    assert summary["m2828_diagnostic_success_count"] == 5
    assert summary["m2828_diagnostic_collision_count"] == 1
    assert summary["m2828_diagnostic_offtrack_count"] == 10
    assert summary["m2828_mixed_outcomes_preserved"] is True

    assert summary["external_high_fidelity_imported"] is False
    assert summary["source_build_run"] is False
    assert summary["adapter_probe_run"] is False
    assert summary["backend_started"] is False
    assert summary["environment_reset_run"] is False
    assert summary["environment_step_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["measured_validation_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    inventory_rows = _read_csv(output_dir / "handoff_artifact_inventory_rows.csv")
    handoff_rows = _read_csv(output_dir / "source_only_interface_handoff_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    blocker_rows = _read_csv(output_dir / "blocker_boundary_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {"m2482_fixture_catalog", "m2501_baseline_comparison", "m2638_selected_platform_blocker"}.issubset(
        {row["handoff_artifact_id"] for row in inventory_rows}
    )
    assert {row["external_hf3_execution_evidence"] for row in inventory_rows} == {"False"}
    assert {row["driver_performance_evidence"] for row in inventory_rows} == {"False"}

    handoff_by_id = {row["row_id"]: row for row in handoff_rows}
    assert handoff_by_id["m2482_fixture_catalog"]["row_count"] == "10"
    assert handoff_by_id["m2498_parameterized_role_panel"]["row_count"] == "300"
    assert handoff_by_id["m2501_baseline_comparison"]["row_count"] == "900"
    assert handoff_by_id["m2638_selected_platform_blocker"]["external_hf3_required"] == "True"
    assert {row["labels_actor_visible"] for row in handoff_rows} == {"False"}
    assert {row["hidden_values_actor_visible"] for row in handoff_rows} == {"False"}
    assert {row["diagnostics_actor_visible"] for row in handoff_rows} == {"False"}

    assert {row["pass"] for row in actor_rows} == {"True"}
    actor_by_id = {row["guard_id"]: row for row in actor_rows}
    assert actor_by_id["observation_shape_72"]["observed"] == "72"
    assert actor_by_id["action_shape_3"]["observed"] == "3"
    assert actor_by_id["no_hidden_oracle_actor_input"]["actor_visible"] == "False"

    blocker_by_id = {row["blocker_id"]: row for row in blocker_rows}
    assert blocker_by_id["m2638_selected_platform_source_dependency"]["status"] == "active"
    assert blocker_by_id["m2638_selected_platform_source_dependency"]["execution_allowed_in_m2832"] == "False"
    assert blocker_by_id["m2828_post_package_mixed_diagnostic_outcomes"]["ordinary_success_denominator_allowed"] == "False"
    assert blocker_by_id["m2494_metadata_only_role_blocker"]["status"] == (
        "resolved_for_parameterized_source_only_role_panel_path"
    )

    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert {row["claim_allowed"] for row in claim_rows} == {"False"}
    assert {"driver_performance", "high_fidelity_validation_result", "level3_self_identification"}.issubset(
        {row["claim_family"] for row in claim_rows}
    )

    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {
        "m2638_selected_platform_blocker_present",
        "m2828_mixed_outcomes_preserved",
        "actor_observation_shape_72_preserved",
        "driver_performance_paper_high_fidelity_self_id_claims_forbidden",
        "follow_up_manifest_registered",
    }.issubset({row["gate_id"] for row in gate_rows})

    run_state = read_json(output_dir / "run_state.json")
    assert run_state["status_pass"] is True
    assert run_state["source_artifacts_reanalyzed_only"] is True
    assert run_state["forbidden_execution_flags"]["environment_reset_run"] is False

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == "m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-result-audit"
    assert follow_up["type"] == "gate"
    assert follow_up["gate_tier"] == "process"
    assert follow_up["commands"] == [{"name": "result_audit", "command": "true"}]
    assert follow_up["scoreboard_checkpoint"] == (
        "docs/m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-result-audit.md"
    )
