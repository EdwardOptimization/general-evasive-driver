import numpy as np

import autodrift.engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight as m3139


def test_action_probe_rows_bind_public_api_to_incumbent_action():
    rows = m3139.action_probe_rows()

    assert len(rows) >= 5
    assert all(row["driver_id"] == m3139.DRIVER_ID for row in rows)
    assert all(row["incumbent_policy_id"] == m3139.INCUMBENT_POLICY_ID for row in rows)
    assert all(row["action_finite"] is True for row in rows)
    assert all(row["action_bounded"] is True for row in rows)
    assert all(row["action_equivalent_to_incumbent"] is True for row in rows)
    assert all(float(row["max_abs_delta_vs_incumbent"]) <= 1e-7 for row in rows)


def test_residual_blocker_rows_preserve_collision_and_offtrack_failures():
    episodes = [
        {
            "source_measurement_episode_id": "src-1",
            "fresh_panel_row_id": "fresh-1",
            "axis_id": "collision_lateral_intrusion",
            "binding_role": "candidate",
            "task_family": "T5",
            "eval_seed": "101",
            "collision": "True",
            "termination_reason": "obstacle_collision",
            "outcome_bucket": "collision_failure",
        },
        {
            "source_measurement_episode_id": "src-2",
            "fresh_panel_row_id": "fresh-2",
            "axis_id": "offtrack_recovery",
            "binding_role": "parent",
            "task_family": "T5",
            "eval_seed": "102",
            "collision": "False",
            "termination_reason": "off_track",
            "outcome_bucket": "offtrack_failure",
        },
        {
            "source_measurement_episode_id": "src-3",
            "fresh_panel_row_id": "fresh-3",
            "axis_id": "speed_floor",
            "binding_role": "candidate",
            "task_family": "T5",
            "eval_seed": "103",
            "collision": "False",
            "termination_reason": "",
            "outcome_bucket": "success_obstacle_pass",
        },
    ]

    rows = m3139.residual_blocker_rows(episodes)

    assert [row["blocker_family"] for row in rows] == ["collision", "offtrack"]
    assert rows[0]["collision"] is True
    assert rows[1]["offtrack"] is True
    assert all(row["speed_too_low"] is False for row in rows)


def test_gate_matrix_accepts_m3138_incumbent_route_and_blocks_overclaims():
    contract = {
        "driver_id": m3139.DRIVER_ID,
        "incumbent_policy_id": m3139.INCUMBENT_POLICY_ID,
        "incumbent_measurement_id": m3139.M3105_ID,
        "policy_config_sha256": m3139.policy_config_fingerprint(m3139.V4_POLICY_CONFIG),
        "observation_shape": m3139.P0_OBSERVATION_DIM,
        "action_shape": m3139.ACTION_DIM,
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
    }
    source = {
        "source_exists": {"m3138_audit": True},
        "m3138_audit_text": "retain M3105/M3103 no-regression direct-action path",
        "m3103_summary": {"status_pass": True, "gate_matrix_pass": True},
        "m3105_summary": {
            "status_pass": True,
            "gate_matrix_pass": True,
            "measurement_episode_row_count": 64,
            "measurement_failure_row_count": 0,
            "measurement_success_count": 57,
            "measurement_collision_count": 5,
            "measurement_offtrack_count": 2,
            "measurement_speed_too_low_count": 0,
        },
    }
    probes = [
        {
            "action_finite": True,
            "action_bounded": True,
            "action_equivalent_to_incumbent": True,
        }
        for _ in range(5)
    ]
    blockers = [{"blocker_family": "collision"} for _ in range(5)] + [{"blocker_family": "offtrack"} for _ in range(2)]
    claims = m3139.claim_boundary_rows(follow_up_manifest_registered=True)

    rows = m3139.gate_matrix_rows(
        source=source,
        contract=contract,
        probes=probes,
        evidence_rows=[{}],
        blocker_rows=blockers,
        claim_rows=claims,
        required_artifacts_present=True,
        follow_up_manifest_registered=True,
    )
    by_id = {row["gate_id"]: row for row in rows}

    assert by_id["m3139-m3138_retains_m3105_incumbent"]["status_pass"] is True
    assert by_id["m3139-action_probes_equivalent_to_incumbent"]["status_pass"] is True
    assert by_id["m3139-residual_blocker_rows_present"]["status_pass"] is True
    assert by_id["m3139-claim_boundary_pass"]["status_pass"] is True


def test_follow_up_manifest_is_result_audit_not_validation(tmp_path):
    manifest = m3139.build_follow_up_manifest(output_dir=tmp_path / "m3139", doc_path=tmp_path / "m3139.md")

    assert manifest["id"] == m3139.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["workflow_synthesis"]["branch"] == "active_safety_driver_m3105_incumbent_deployable_interface"
    assert manifest["local_search_guard"]["actual_progress_type"] == "new_tool_or_infra"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_m3105_incumbent_deployable_reflex_interface_result_audit_doc",
            "command": "true",
        }
    ]
    assert "validation" in manifest["forbidden_shortcuts"][1]


def test_public_action_rejects_wrong_shape_through_runner_import():
    with np.testing.assert_raises(ValueError):
        m3139.active_safety_reflex_action(np.zeros(m3139.P0_OBSERVATION_DIM - 1, dtype=np.float32))
