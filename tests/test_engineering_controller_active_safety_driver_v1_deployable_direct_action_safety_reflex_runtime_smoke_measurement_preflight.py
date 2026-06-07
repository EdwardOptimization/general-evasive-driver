from pathlib import Path

from autodrift.artifacts import write_json
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088


AXES = [
    "collision_lateral_intrusion",
    "offtrack_boundary_recovery",
    "speed_floor_stress",
    "stability_action_pressure",
]
BINDINGS = ["candidate", "parent"]


def _measurement_row(
    index: int,
    *,
    axis_id: str,
    binding_role: str,
    workload_id: str,
    eval_seed: int,
) -> dict[str, object]:
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
        "eval_seed": eval_seed,
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


def test_smoke_plan_selects_first_m3084_row_per_axis_binding_without_seed_offset(tmp_path: Path) -> None:
    workload_rows: list[dict[str, object]] = []
    measurement_rows: list[dict[str, object]] = []
    expected_ids: list[str] = []
    expected_seeds: list[int] = []
    index = 1
    for axis_id in AXES:
        for binding_role in BINDINGS:
            workload = _workload_row(tmp_path, index, binding_role=binding_role)
            workload_rows.append(workload)
            workload_id = str(workload["executable_workload_id"])
            first = _measurement_row(
                index,
                axis_id=axis_id,
                binding_role=binding_role,
                workload_id=workload_id,
                eval_seed=401500 + index,
            )
            later = _measurement_row(
                1000 + index,
                axis_id=axis_id,
                binding_role=binding_role,
                workload_id=workload_id,
                eval_seed=901500 + index,
            )
            measurement_rows.extend([later, first])
            expected_ids.append(str(first["measurement_episode_id"]))
            expected_seeds.append(int(first["eval_seed"]))
            index += 1

    plan = m3088.smoke_plan(
        {
            "m3084_measurement_rows": measurement_rows,
            "m3012_workload_rows": workload_rows,
        }
    )

    assert len(plan) == 8
    assert [row["source_measurement_episode_id"] for row in plan] == expected_ids
    assert [row["eval_seed"] for row in plan] == expected_seeds
    assert all(row["status_pass"] is True for row in plan)
    assert all(row["runtime_base_policy_required"] is False for row in plan)
    assert {row["axis_id"] for row in plan} == set(AXES)
    assert {row["binding_role"] for row in plan} == set(BINDINGS)


def test_follow_up_manifest_preserves_runtime_smoke_audit_boundary(tmp_path: Path) -> None:
    manifest = m3088.build_follow_up_manifest(
        output_dir=tmp_path / "m3088",
        doc_path=tmp_path / "m3088.md",
    )

    assert manifest["id"] == m3088.NEXT_ID
    assert manifest["status"] == "pending"
    assert manifest["gate_tier"] == "process"
    assert manifest["promotion_decision"] == "not_applicable"
    assert "Result audit only" in manifest["workflow_synthesis"]["claim_scope"]
    assert "driver-performance" in manifest["forbidden_shortcuts"][1]
    assert "M3089 must select exactly one" in manifest["public_gates"][3]


def test_contract_guards_include_m3086_runtime_package_evidence() -> None:
    source = {
        "m3086_interface_rows": [{"status_pass": True}],
        "m3086_probe_rows": [{"status_pass": True}],
        "m3086_exclusion_rows": [{"status_pass": True}],
        "m3086_claim_rows": [{"status_pass": True}],
    }
    contract = {
        "observation_shape": 72,
        "action_shape": 3,
        "action_components": ["steer", "throttle", "brake"],
        "output_semantics": "direct_action_clipped",
    }

    rows = m3088.contract_guard_rows(source=source, contract=contract, plan_rows=[], episodes=[], failures=[])
    guards = {row["guard_id"]: row for row in rows}

    assert guards["m3088-contract_observation_shape"]["status_pass"] is True
    assert guards["m3088-contract_action_components"]["status_pass"] is True
    assert guards["m3088-m3086_interface_rows_pass"]["status_pass"] is True
    assert guards["m3088-m3086_action_probe_rows_pass"]["status_pass"] is True
    assert guards["m3088-m3086_actor_input_exclusion_rows_pass"]["status_pass"] is True
    assert guards["m3088-sample_action_finite"]["status_pass"] is True
    assert guards["m3088-sample_action_bounded"]["status_pass"] is True
