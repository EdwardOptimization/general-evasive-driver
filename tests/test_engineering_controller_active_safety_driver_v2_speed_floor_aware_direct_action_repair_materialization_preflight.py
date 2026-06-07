import numpy as np

from autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight import (
    actor_visible_safety_reflex_action,
)
import autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight as m3093
from autodrift.high_fidelity_interface import ACTION_DIM


def test_speed_floor_repair_lifts_clear_low_speed_throttle() -> None:
    obs = m3093._probe_observation(speed_mps=3.0)

    v1 = actor_visible_safety_reflex_action(obs)
    v2 = m3093.speed_floor_aware_direct_action(obs)

    assert v2.shape == (ACTION_DIM,)
    assert np.all(np.isfinite(v2))
    assert np.max(np.abs(v2)) <= 1.0
    assert v2[1] > v1[1]
    assert v2[1] > 0.0
    assert v2[2] <= v1[2]


def test_urgent_obstacle_still_brakes_and_avoids() -> None:
    obs = m3093._probe_observation(speed_mps=14.0, obstacle=True)

    action = m3093.speed_floor_aware_direct_action(obs)

    assert action.shape == (ACTION_DIM,)
    assert np.all(np.isfinite(action))
    assert np.max(np.abs(action)) <= 1.0
    assert action[2] > 0.0
    assert action[0] < 0.0


def test_follow_up_manifest_preserves_materialization_audit_boundary(tmp_path) -> None:
    manifest = m3093.build_follow_up_manifest(output_dir=tmp_path / "m3093", doc_path=tmp_path / "m3093.md")

    assert manifest["id"] == m3093.NEXT_ID
    assert manifest["status"] == "pending"
    assert manifest["gate_tier"] == "process"
    assert manifest["promotion_decision"] == "not_applicable"
    assert "Result audit only" in manifest["workflow_synthesis"]["claim_scope"]
    assert "repair-success" in manifest["forbidden_shortcuts"][1]


def test_claim_and_rule_rows_keep_hidden_inputs_out() -> None:
    rule_rows = m3093.build_rule_rows()
    exclusion_rows = m3093.build_actor_input_exclusion_rows()
    claim_rows = m3093.build_claim_boundary_rows(follow_up_manifest_registered=True)

    assert any("speed_floor" in row["rule_family"] for row in rule_rows)
    assert all(row["direct_action_output"] is True for row in rule_rows)
    assert all(row["runtime_base_policy_required"] is False for row in rule_rows)
    assert all(row["hidden_oracle_actor_input_required"] is False for row in rule_rows)
    assert all(row["status_pass"] is True for row in exclusion_rows)
    assert all(row["status_pass"] is True for row in claim_rows)
