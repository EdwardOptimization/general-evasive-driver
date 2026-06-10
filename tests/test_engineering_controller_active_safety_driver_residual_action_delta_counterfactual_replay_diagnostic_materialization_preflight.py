import numpy as np

import autodrift.engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight as m3153
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _coverage(**updates):
    row = {
        "trace_episode_id": "m3147-action-delta-trace-episode-0001",
        "residual_failure_id": "m3147-residual-failure-0001",
        "m3144_measurement_episode_id": "m3144-measurement-episode-0007",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "axis_id": "collision_lateral_intrusion",
        "binding_role": "candidate",
        "task_family": "T5",
        "executable_workload_id": "m3012-executable-workload-0015",
        "executable_source_spec_id": "m3012-executable-source-spec-0008",
        "task_source_id": "m3006-src-0007",
        "base_profile_name": "route_a_candidate_m2655_mitigation_preserving",
        "eval_seed": "401530",
        "target_failure_kind": "collision",
        "terminal_termination_reason": "obstacle_collision",
        "terminal_outcome_bucket": "collision_failure",
    }
    row.update(updates)
    return row


def _effectiveness(**updates):
    row = {
        "effectiveness_row_id": "m3150-residual-delta-effectiveness-0001",
        "residual_failure_id": "m3147-residual-failure-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "counterfactual_sensitivity_label": "collision_delta_present_counterfactual_needed",
    }
    row.update(updates)
    return row


def _workload(**updates):
    row = {
        "executable_workload_id": "m3012-executable-workload-0015",
        "executable_source_spec_id": "m3012-executable-source-spec-0008",
        "task_source_id": "m3006-src-0007",
        "profile_binding_name": "route_a_candidate_m2655_mitigation_preserving",
        "config_path": "pyproject.toml",
        "status_pass": "True",
        "hidden_oracle_actor_input_required": "False",
        "future_target_actor_input_required": "False",
        "source_labels_actor_visible": "False",
        "route_labels_actor_visible": "False",
        "outcome_labels_actor_visible": "False",
        "success_progress_labels_actor_visible": "False",
        "verdict_labels_actor_visible": "False",
        "ttc_actor_input_required": "False",
    }
    row.update(updates)
    return row


def _episode(residual_id, variant_id, **updates):
    row = {
        "residual_failure_id": residual_id,
        "source_measurement_episode_id": "m3084-measurement-episode-0007",
        "fresh_panel_row_id": "m3082-fresh-panel-0007",
        "target_failure_kind": "collision",
        "source_m3150_sensitivity_label": "collision_delta_present_counterfactual_needed",
        "variant_id": variant_id,
        "termination_reason": "obstacle_collision",
        "outcome_bucket": "collision_failure",
        "success": False,
        "collision": True,
        "offtrack": False,
        "min_clearance_margin": -0.10,
        "return": 10.0,
        "speed_mean": 12.0,
        "steps": 20,
        "mean_delta_l1_vs_reference": 0.0,
        "max_delta_abs_vs_reference": 0.0,
    }
    row.update(updates)
    return row


def test_fixed_variants_are_predeclared_obs72_action3_bounded():
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.9
    obs[44] = 1.0
    obs[45] = 0.2
    obs[46] = 0.02
    obs[49] = 0.3

    rows = m3153.fixed_variant_rows()
    payloads = [m3153.counterfactual_variant_action(obs, row) for row in rows]

    assert [row["variant_id"] for row in rows] == [
        m3153.REFERENCE_VARIANT_ID,
        "decel_headroom_probe",
        "brake_saturation_probe",
        "lateral_headroom_probe",
    ]
    assert all(row["fixed_predeclared"] for row in rows)
    assert all(row["applies_to_all_residual_rows"] for row in rows)
    assert all(row["actor_observation_contract"] == "actor_visible_obs72_only" for row in rows)
    assert all(row["uses_hidden_label_at_runtime"] is False for row in rows)
    assert all(tuple(payload["action"].shape) == (ACTION_DIM,) for payload in payloads)
    assert all(np.all(np.isfinite(payload["action"])) for payload in payloads)
    assert all(float(np.max(np.abs(payload["action"]))) <= 1.0 for payload in payloads)
    assert np.max(np.abs(payloads[0]["delta_vs_reference"])) == 0.0


def test_counterfactual_replay_plan_preserves_source_identity_and_blocks_hidden_labels():
    source = {
        "m3147_coverage_rows": [_coverage()],
        "m3150_effectiveness_rows": [_effectiveness()],
        "m3012_workload_rows": [_workload()],
    }

    rows = m3153.counterfactual_replay_plan(source)

    assert len(rows) == 1
    row = rows[0]
    assert row["counterfactual_plan_row_id"] == "m3153-counterfactual-plan-row-0001"
    assert row["residual_failure_id"] == "m3147-residual-failure-0001"
    assert row["effectiveness_row_id"] == "m3150-residual-delta-effectiveness-0001"
    assert row["source_measurement_episode_id"] == "m3084-measurement-episode-0007"
    assert row["source_m3150_sensitivity_label"] == "collision_delta_present_counterfactual_needed"
    assert row["status_pass"] is True

    blocked = m3153.counterfactual_replay_plan(
        {
            "m3147_coverage_rows": [_coverage()],
            "m3150_effectiveness_rows": [_effectiveness()],
            "m3012_workload_rows": [_workload(outcome_labels_actor_visible="True")],
        }
    )
    assert blocked[0]["status_pass"] is False
    assert blocked[0]["hidden_label_violation"] is True


def test_counterfactual_comparison_rows_are_diagnostic_not_repair_success():
    rows = m3153.counterfactual_comparison_rows(
        [
            _episode("m3147-residual-failure-0001", m3153.REFERENCE_VARIANT_ID),
            _episode(
                "m3147-residual-failure-0001",
                "decel_headroom_probe",
                termination_reason="",
                outcome_bucket="success",
                success=True,
                collision=False,
                min_clearance_margin=0.40,
                mean_delta_l1_vs_reference=0.20,
                max_delta_abs_vs_reference=0.30,
            ),
        ]
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["counterfactual_diagnostic_label"] == "counterfactual_terminal_outcome_changed_to_success_diagnostic"
    assert row["action_channel_sensitive_diagnostic"] is True
    assert row["repair_success_claim_made"] is False
    assert row["validation_run"] is False
    assert row["driver_performance_claim_made"] is False
    assert row["claim_boundary"] == m3153.CLAIM_SCOPE


def test_claim_boundary_blocks_validation_repair_and_label_conditioned_actor():
    rows = m3153.claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3153-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3153-repair_implementation"]["allowed_in_m3153"] is False
    assert by_id["m3153-validation_result"]["claim_made"] is False
    assert by_id["m3153-repair_success"]["claim_made"] is False
    assert by_id["m3153-per_row_hidden_label_conditioned_actor"]["claim_made"] is False
    assert by_id["m3153-hidden_oracle_actor_inputs"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3153.build_follow_up_manifest(output_dir=tmp_path / "m3153", doc_path=tmp_path / "m3153.md")

    assert manifest["id"] == m3153.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]
