from pathlib import Path

import numpy as np

from autodrift.artifacts import write_json
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight as m3075


def _write_direct_action_artifact(path: Path, *, base_policy_required: bool = False) -> None:
    weight = np.zeros((72, 3), dtype=np.float32)
    bias = np.zeros((3,), dtype=np.float32)
    np.savez_compressed(
        path,
        linear_weight=weight,
        linear_bias=bias,
        action_low=np.full((3,), -1.0, dtype=np.float32),
        action_high=np.full((3,), 1.0, dtype=np.float32),
        observation_dim=np.asarray([72]),
        action_dim=np.asarray([3]),
        output_semantics=np.asarray(["direct_action_clipped"]),
        output_components=np.asarray(["steer", "throttle", "brake"]),
        base_policy_required_at_runtime=np.asarray([base_policy_required]),
    )


def test_direct_action_policy_outputs_clipped_action_without_base_policy() -> None:
    weight = np.zeros((72, 3), dtype=np.float32)
    weight[0, 0] = 2.0
    bias = np.asarray([0.25, -0.25, 0.5], dtype=np.float32)
    policy = m3075.DirectActionActorPolicy(
        weight=weight,
        bias=bias,
        action_low=np.full((3,), -1.0, dtype=np.float32),
        action_high=np.full((3,), 1.0, dtype=np.float32),
        output_semantics="direct_action_clipped",
    )

    action = policy.act(np.asarray([1.0] + [0.0] * 71, dtype=np.float32), {})
    telemetry = policy.telemetry()

    assert np.allclose(action, np.asarray([1.0, -0.25, 0.5], dtype=np.float32))
    assert telemetry["runtime_base_policy_required"] is False
    assert telemetry["direct_action_step_count"] == 1
    assert telemetry["action_clip_fraction"] == 1.0
    assert telemetry["final_action_abs_max"] == 1.0


def test_load_direct_action_artifact_rejects_runtime_base_policy_dependency(tmp_path: Path) -> None:
    artifact_path = tmp_path / "candidate_direct_action_repair_reflex_layer.npz"
    _write_direct_action_artifact(artifact_path, base_policy_required=True)

    artifact = m3075.load_direct_action_artifact(artifact_path)

    assert artifact["contract_pass"] is False
    assert artifact["base_policy_required_at_runtime"] is True


def test_load_direct_action_artifact_accepts_m3073_contract(tmp_path: Path) -> None:
    artifact_path = tmp_path / "candidate_direct_action_repair_reflex_layer.npz"
    _write_direct_action_artifact(artifact_path)

    artifact = m3075.load_direct_action_artifact(artifact_path)
    guards = m3075.direct_action_adapter_guard_rows(artifact, [])

    assert artifact["contract_pass"] is True
    assert artifact["output_semantics"] == "direct_action_clipped"
    assert artifact["output_components"] == ["steer", "throttle", "brake"]
    assert all(m3075._bool(row["status_pass"]) for row in guards)


def test_workload_plan_does_not_require_checkpoint_path(tmp_path: Path) -> None:
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
                "checkpoint_path": str(tmp_path / "missing_checkpoint.pt"),
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

    plan = m3075.workload_plan(source)

    assert len(plan) == 1
    assert plan[0]["status_pass"] is True
    assert plan[0]["runtime_base_policy_required"] is False
    assert plan[0]["direct_action_profile_name"] == "route_a_candidate+m3073_repair_direct_action"
