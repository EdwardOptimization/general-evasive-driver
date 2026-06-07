from pathlib import Path

import numpy as np

from autodrift.artifacts import write_json
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_closed_loop_measurement_preflight as m3080
import autodrift.engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight as m3078


def test_deterministic_safety_reflex_policy_outputs_bounded_direct_action() -> None:
    policy = m3080.DeterministicSafetyReflexPolicy(policy_config=m3078.DEFAULT_POLICY_CONFIG)
    observation = np.zeros(72, dtype=np.float32)
    observation[13:28:2] = 0.15
    observation[29:44:2] = -0.15

    action = policy.act(observation, {})
    telemetry = policy.telemetry()

    assert action.shape == (3,)
    assert np.all(np.isfinite(action))
    assert float(np.max(np.abs(action))) <= 1.0
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["direct_action_step_count"] == 1
    assert telemetry["action_clip_fraction"] == 0.0


def test_policy_contract_rejects_runtime_base_policy_dependency() -> None:
    config = dict(m3078.DEFAULT_POLICY_CONFIG)
    config["runtime_base_policy_required"] = True

    assert m3080.policy_contract_pass(m3078.DEFAULT_POLICY_CONFIG) is True
    assert m3080.policy_contract_pass(config) is False


def test_workload_plan_preserves_same_denominator_contract(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_json(config_path, {"env": {}})
    source = {
        "m3037_baseline_rows": [
            {
                "baseline_measurement_row_id": "baseline-1",
                "source_episode_index": "1",
                "eval_seed": "123",
                "success": "False",
                "collision": "False",
            }
        ],
        "m3012_workload_rows": [
            {
                "executable_workload_id": "workload-1",
                "workload_contract_id": "contract-1",
                "source_resolution_id": "source-resolution-1",
                "profile_binding_id": "profile-binding-1",
                "executable_source_spec_id": "spec-1",
                "task_source_id": "task-1",
                "profile_binding_name": "route_a_candidate",
                "binding_role": "candidate",
                "task_family": "T4",
                "source_edge": "unit",
                "window_tag": "unit",
                "executable_source_family": "unit_family",
                "env_template_family": "unit_env",
                "config_path": str(config_path),
                "actor_observation_dim": "72",
                "actor_action_dim": "3",
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
        ],
    }

    plan = m3080.workload_plan(source)

    assert len(plan) == 1
    assert plan[0]["measurement_episode_id"] == "m3080-measurement-episode-0001"
    assert plan[0]["status_pass"] is True
    assert plan[0]["runtime_base_policy_required"] is False
    assert plan[0]["direct_action_profile_name"] == "route_a_candidate+m3078_deterministic_safety_reflex"


def test_follow_up_manifest_preserves_result_audit_boundary(tmp_path: Path) -> None:
    output_dir = tmp_path / "m3080"
    doc_path = tmp_path / "m3080.md"
    summary_path = output_dir / "summary.json"

    manifest = m3080.build_follow_up_manifest(
        output_dir=output_dir,
        doc_path=doc_path,
        summary_path=summary_path,
    )

    assert manifest["id"] == m3080.NEXT_ID
    assert manifest["status"] == "pending"
    assert manifest["gate_tier"] == "process"
    assert manifest["promotion_decision"] == "not_applicable"
    assert "validation ranking promotion" in manifest["workflow_synthesis"]["claim_scope"]
