import numpy as np

import autodrift.engineering_controller_active_safety_driver_v3_high_speed_obstacle_edge_hard_safety_direct_action_repair_materialization_preflight as m3098


def test_v3_direct_action_preserves_shape_and_bounds():
    action = m3098.high_speed_obstacle_edge_hard_safety_direct_action(
        np.zeros(m3098.P0_OBSERVATION_DIM, dtype=np.float32),
        m3098.V3_POLICY_CONFIG,
    )

    assert action.shape == (m3098.ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert m3098.V3_POLICY_CONFIG["output_components"] == list(m3098.ACTION_COMPONENTS)
    assert m3098.V3_POLICY_CONFIG["runtime_base_policy_required"] is False


def test_v3_probes_keep_low_speed_recovery_and_add_hard_safety_braking():
    probe_rows = m3098._probe_rows()
    by_id = {row["probe_id"]: row for row in probe_rows}

    low_speed = by_id["m3098-probe-clear_low_speed"]
    obstacle = by_id["m3098-probe-high_speed_obstacle"]
    edge = by_id["m3098-probe-high_speed_edge"]

    assert low_speed["status_pass"] is True
    assert obstacle["status_pass"] is True
    assert edge["status_pass"] is True
    assert low_speed["throttle"] > 0.0
    assert obstacle["brake"] > 0.4
    assert obstacle["throttle"] < 0.0
    assert edge["brake"] > 0.0
    assert edge["throttle"] < 0.0


def test_rule_and_claim_rows_preserve_materialization_boundary():
    rule_families = {row["rule_family"] for row in m3098.build_rule_rows()}
    claim_rows = m3098.build_claim_boundary_rows(follow_up_manifest_registered=True)
    claims = {row["claim_id"]: row for row in claim_rows}

    assert "high_speed_obstacle_braking_and_throttle_suppression" in rule_families
    assert "high_speed_edge_braking_and_corridor_recovery" in rule_families
    assert claims["m3098-follow_up_result_audit_registered"]["claim_made"] is True
    assert claims["m3098-rollout_measurement"]["claim_made"] is False
    assert claims["m3098-repair_success"]["claim_made"] is False
    assert all(row["status_pass"] for row in claim_rows)


def test_follow_up_manifest_routes_to_result_audit(tmp_path):
    manifest = m3098.build_follow_up_manifest(
        output_dir=tmp_path / "m3098",
        doc_path=tmp_path / "m3098.md",
    )

    assert manifest["id"] == m3098.NEXT_ID
    assert manifest["gate_tier"] == "process"
    assert manifest["training_stage"]["stage"] == "process"
    assert manifest["local_search_guard"]["actual_progress_type"] == "result_audit"
    assert manifest["commands"] == [
        {"name": "active_safety_driver_v3_repair_materialization_result_audit_doc", "command": "true"}
    ]
    assert "measurement validation" in manifest["forbidden_shortcuts"][0]
