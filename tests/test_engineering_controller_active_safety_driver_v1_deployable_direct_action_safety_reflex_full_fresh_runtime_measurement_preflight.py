from pathlib import Path

from autodrift.artifacts import write_json
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090


AXES = [
    "collision_lateral_intrusion",
    "offtrack_boundary_recovery",
    "speed_floor_stress",
    "stability_action_pressure",
]
BINDINGS = ["candidate", "parent"]


def _measurement_row(index: int, *, axis_id: str, binding_role: str, workload_id: str, eval_seed: int) -> dict[str, object]:
    return {
        "measurement_episode_id": f"m3084-measurement-episode-{index:04d}",
        "fresh_panel_row_id": f"m3082-fresh-panel-{index:04d}",
        "axis_id": axis_id,
        "axis_family": f"{axis_id}_family",
        "scenario_family": f"{axis_id}_scenario",
        "fresh_scenario_distribution": f"{axis_id}_fresh_distribution",
        "binding_role": binding_role,
        "task_family": "T5" if axis_id in AXES[:2] else "T4",
        "executable_workload_id": workload_id,
        "executable_source_spec_id": f"spec-{workload_id}",
        "task_source_id": f"task-{workload_id}",
        "base_profile_name": f"route_a_{binding_role}",
        "policy": "m3078_deterministic_safety_reflex_fresh",
        "eval_seed": eval_seed,
        "success": True,
        "collision": False,
        "obstacle_completed": True,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": 10.0 + index,
        "return": 100.0 + index,
        "action_rate_mean": 0.01 * index,
        "raw_action_abs_max": 1.0,
        "candidate_output_semantics": "direct_action_clipped",
        "runtime_base_policy_required": False,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
    }


def _workload_row(tmp_path: Path, index: int, *, binding_role: str) -> dict[str, object]:
    workload_id = f"workload-{index:04d}"
    config_path = tmp_path / f"config-{index}.json"
    write_json(config_path, {"env": {}})
    return {
        "executable_workload_id": workload_id,
        "executable_source_spec_id": f"spec-{workload_id}",
        "task_source_id": f"task-{workload_id}",
        "profile_binding_name": f"route_a_{binding_role}",
        "binding_role": binding_role,
        "task_family": "T5",
        "config_path": str(config_path),
        "actor_observation_dim": "72",
        "actor_action_dim": "3",
        "status_pass": True,
        "hidden_oracle_actor_input_required": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
    }


def _full_source(tmp_path: Path) -> dict[str, object]:
    workload_rows = []
    measurement_rows = []
    index = 1
    for axis_id in AXES:
        for binding_role in BINDINGS:
            for repeat in range(8):
                workload = _workload_row(tmp_path, index, binding_role=binding_role)
                workload_rows.append(workload)
                measurement_rows.append(
                    _measurement_row(
                        index,
                        axis_id=axis_id,
                        binding_role=binding_role,
                        workload_id=str(workload["executable_workload_id"]),
                        eval_seed=401000 + repeat + index * 10,
                    )
                )
                index += 1
    return {"m3084_measurement_rows": measurement_rows, "m3012_workload_rows": workload_rows}


def test_full_fresh_plan_preserves_complete_m3084_denominator_without_seed_offset(tmp_path: Path) -> None:
    source = _full_source(tmp_path)

    plan = m3090.full_fresh_plan(source)

    assert len(plan) == 64
    assert [row["source_measurement_episode_id"] for row in plan] == [
        row["measurement_episode_id"] for row in source["m3084_measurement_rows"]
    ]
    assert [row["eval_seed"] for row in plan] == [row["eval_seed"] for row in source["m3084_measurement_rows"]]
    assert all(row["status_pass"] is True for row in plan)
    assert all(row["runtime_base_policy_required"] is False for row in plan)
    assert {row["axis_id"] for row in plan} == set(AXES)
    assert {row["binding_role"] for row in plan} == set(BINDINGS)


def test_parity_rows_compare_runtime_rows_to_m3084_same_row_without_claims() -> None:
    source = [
        _measurement_row(1, axis_id=AXES[0], binding_role="candidate", workload_id="workload-0001", eval_seed=401500)
    ]
    episode = {
        "runtime_smoke_episode_id": "m3090-runtime-measurement-episode-0001",
        "source_measurement_episode_id": "m3084-measurement-episode-0001",
        "fresh_panel_row_id": "m3082-fresh-panel-0001",
        "axis_id": AXES[0],
        "binding_role": "candidate",
        "task_family": "T5",
        "eval_seed": 401500,
        "policy": "active_safety_reflex_driver_v1_full_fresh_runtime_measurement",
        "success": True,
        "collision": False,
        "termination_reason": "",
        "outcome_bucket": "success_obstacle_pass",
        "min_clearance_margin": 11.0,
        "return": 101.0,
        "action_rate_mean": 0.01,
        "raw_action_abs_max": 1.0,
    }

    rows = m3090.parity_rows([episode], source)

    assert rows[0]["success_match"] is True
    assert rows[0]["collision_match"] is True
    assert rows[0]["termination_reason_match"] is True
    assert rows[0]["outcome_bucket_match"] is True
    assert rows[0]["exact_seed_match"] is True
    assert rows[0]["clearance_margin_abs_delta"] == 0.0
    assert rows[0]["parity_result_claim_made"] is False
    assert rows[0]["validation_run"] is False
    assert rows[0]["driver_performance_claim_made"] is False


def test_follow_up_manifest_preserves_result_audit_boundary(tmp_path: Path) -> None:
    manifest = m3090.build_follow_up_manifest(
        output_dir=tmp_path / "m3090",
        doc_path=tmp_path / "m3090.md",
    )

    assert manifest["id"] == m3090.NEXT_ID
    assert manifest["status"] == "pending"
    assert manifest["gate_tier"] == "process"
    assert manifest["promotion_decision"] == "not_applicable"
    assert "Result audit only" in manifest["workflow_synthesis"]["claim_scope"]
    assert "driver-performance" in manifest["forbidden_shortcuts"][1]
    assert "M3091 must select exactly one" in manifest["public_gates"][3]
