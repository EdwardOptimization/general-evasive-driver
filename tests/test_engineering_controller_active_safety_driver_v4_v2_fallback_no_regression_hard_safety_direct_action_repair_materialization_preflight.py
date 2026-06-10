import numpy as np

import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight as m3103


def test_v4_policy_preserves_direct_action_contract():
    obs = np.zeros(m3103.P0_OBSERVATION_DIM, dtype=np.float32)
    action = m3103.v4_v2_fallback_no_regression_hard_safety_direct_action(obs)

    assert action.shape == (m3103.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert m3103.V4_POLICY_CONFIG["policy_id"] == m3103.POLICY_ID
    assert m3103.V4_POLICY_CONFIG["runtime_base_policy_required"] is False
    assert m3103.V4_POLICY_CONFIG["checkpoint_model_required"] is False
    assert m3103.V4_POLICY_CONFIG["recurrent_hidden_state_required"] is False
    assert m3103.V4_POLICY_CONFIG["output_components"] == list(m3103.ACTION_COMPONENTS)


def test_no_regression_guards_cover_m3100_regression_rows():
    regression_rows = [
        {"comparison_id": "m3100-same-row-comparison-0014"},
        {"comparison_id": "m3100-same-row-comparison-0048"},
    ]
    rows = m3103.build_no_regression_guard_rows(regression_rows)
    by_id = {row["guard_id"]: row for row in rows}

    assert by_id["m3103-no-regression-speed-floor-stress"]["status_pass"] is True
    assert by_id["m3103-no-regression-row-0014"]["status_pass"] is True
    assert by_id["m3103-no-regression-row-0048"]["status_pass"] is True
    assert by_id["m3103-no-regression-comparison-complete"]["status_pass"] is True


def test_claim_boundary_blocks_measurement_and_repair_success():
    rows = m3103.build_claim_boundary_rows(follow_up_manifest_registered=True)
    by_id = {row["claim_id"]: row for row in rows}

    assert by_id["m3103-follow_up_result_audit_registered"]["allowed_in_m3103"] is True
    assert by_id["m3103-follow_up_result_audit_registered"]["claim_made"] is True
    assert by_id["m3103-rollout_measurement"]["allowed_in_m3103"] is False
    assert by_id["m3103-rollout_measurement"]["claim_made"] is False
    assert by_id["m3103-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in rows)


def test_follow_up_manifest_is_result_audit_not_measurement(tmp_path):
    manifest = m3103.build_follow_up_manifest(
        output_dir=tmp_path / "m3103",
        doc_path=tmp_path / "m3103.md",
    )

    assert manifest["id"] == m3103.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {
            "name": "active_safety_driver_v4_no_regression_repair_materialization_result_audit_doc",
            "command": "true",
        }
    ]
    assert "measurement" in manifest["forbidden_shortcuts"][0]
    assert "repair-success" in manifest["hypothesis"]
