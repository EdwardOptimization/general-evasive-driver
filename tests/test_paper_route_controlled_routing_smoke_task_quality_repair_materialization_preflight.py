from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight as preflight
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _parent_spec(task_source_id: str, *, family: str, source_kind: str, generated: bool = False) -> dict[str, object]:
    return {
        "task_source_id": task_source_id,
        "panel_source_id": f"panel_{task_source_id}",
        "panel_task_family": family,
        "source_origin": "unit_test",
        "source_kind": source_kind,
        "source_edge": "edge",
        "window_tag": "window",
        "source_role_semantics": "role",
        "parent_feasibility_tier_id": "tier",
        "normalized_surface_variant": "surface",
        "sampled_obstacle_label": "label",
        "source_reference": "reference",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "template",
        "generated_source_row": generated,
        "paper_validity_claim": False,
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "wheel_observation_mode": "none",
            "obstacle_relative_velocity_mode": "zero",
            "track_width": 5.0,
            "max_steps": 100,
            "obstacle": {"distance_range": [10.0, 20.0], "half_width_range": [0.5, 1.0]},
            "warmup_gate": {"reveal_step": 20},
        },
    }


def _candidate(
    repair_candidate_id: str,
    repair_axis: str,
    *,
    parent_task_source_id: str = "",
    parent_profile_name: str = "",
    parent_panel_task_family: str = "",
    parent_source_kind: str = "",
    target_generated_source_row: bool = False,
    split: str = "public_debug",
) -> dict[str, object]:
    return {
        "repair_candidate_id": repair_candidate_id,
        "repair_branch_id": "test_branch",
        "repair_axis": repair_axis,
        "repair_sequence_index": 0,
        "repair_source_family": "family",
        "source_split": split,
        "parent_task_source_id": parent_task_source_id,
        "parent_profile_name": parent_profile_name,
        "parent_panel_task_family": parent_panel_task_family,
        "parent_source_kind": parent_source_kind,
        "target_generated_source_row": target_generated_source_row,
        "obstacle_distance_delta_m": 4.0,
        "obstacle_half_width_delta_m": -0.1,
        "track_width_delta_m": 1.0,
        "warmup_reveal_step_delta": -5,
        "max_steps_delta": 10,
    }


def _write_fixture(tmp_path: Path, *, unresolved: bool = False) -> tuple[Path, Path, Path, Path]:
    parent_specs = [
        _parent_spec("exact_source", family="T1", source_kind="kind_exact"),
        _parent_spec("l2_source", family="T2", source_kind="kind_l2"),
        _parent_spec("family_source", family="T3", source_kind="kind_family"),
        _parent_spec("kind_source", family="T4", source_kind="kind_zero"),
        _parent_spec("generated_source", family="T5", source_kind="kind_generated", generated=True),
    ]
    candidates = [
        _candidate("c0", "success_neighborhood_expansion", parent_task_source_id="exact_source"),
        _candidate("c1", "l2_offtrack_relief", parent_profile_name="L2_window_13"),
        _candidate("c2", "family_offtrack_relief", parent_panel_task_family="T3"),
        _candidate("c3", "zero_success_source_kind_relief", parent_source_kind="missing_kind" if unresolved else "kind_zero"),
        _candidate("c4", "generated_proxy_support_check", target_generated_source_row=True, split="public_gate"),
    ]
    templates_path = tmp_path / "templates.json"
    parent_specs_path = tmp_path / "parent_specs.json"
    parent_workload_path = tmp_path / "workload.csv"
    source_profile_path = tmp_path / "source_profile.csv"
    write_json(
        templates_path,
        {
            "result_class": "controlled_routing_smoke_task_quality_repair_templates_pass",
            "expected_candidate_source_count": len(candidates),
            "expected_repair_axis_counts": {
                "family_offtrack_relief": 1,
                "generated_proxy_support_check": 1,
                "l2_offtrack_relief": 1,
                "success_neighborhood_expansion": 1,
                "zero_success_source_kind_relief": 1,
            },
            "expected_source_split_counts": {"public_debug": 4, "public_gate": 1},
            "candidates": candidates,
        },
    )
    write_json(parent_specs_path, {"executable_task_specs": parent_specs})
    write_csv_rows(
        parent_workload_path,
        [
            {
                "profile_name": "L0_current_masked",
                "profile_config_path": "cfg0.json",
                "checkpoint_path": "ckpt0.pt",
            },
            {
                "profile_name": "L3_online_gru",
                "profile_config_path": "cfg1.json",
                "checkpoint_path": "ckpt1.pt",
            },
        ],
    )
    write_csv_rows(
        source_profile_path,
        [
            {
                "task_source_id": "l2_source",
                "profile_name": "L2_window_13",
                "offtrack_outcome_count": 1,
            }
        ],
    )
    return templates_path, parent_specs_path, parent_workload_path, source_profile_path


def test_repair_materialization_preflight_resolves_all_parent_modes(tmp_path: Path) -> None:
    templates_path, parent_specs_path, parent_workload_path, source_profile_path = _write_fixture(tmp_path)

    summary = preflight.run_repair_materialization_preflight(
        templates_path=templates_path,
        parent_specs_path=parent_specs_path,
        parent_workload_path=parent_workload_path,
        source_profile_localization_path=source_profile_path,
        output_dir=tmp_path / "out",
        target_profile_count=2,
    )

    assert summary["result_class"] == "controlled_routing_smoke_task_quality_repair_materialization_preflight_pass"
    assert summary["repaired_spec_count"] == 5
    assert summary["planned_workload_count"] == 10
    assert summary["unresolved_parent_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    specs = read_json(tmp_path / "out" / "executable_task_specs.json")["executable_task_specs"]
    assert {spec["parent_resolution_method"] for spec in specs} == {
        "exact_task_source_id",
        "source_profile_offtrack_slice",
        "family_slice",
        "source_kind_slice",
        "generated_proxy_slice",
    }
    assert all(spec["env_config"]["track_width"] == 6.0 for spec in specs)


def test_repair_materialization_preflight_fails_closed_on_unresolved_parent(tmp_path: Path) -> None:
    templates_path, parent_specs_path, parent_workload_path, source_profile_path = _write_fixture(tmp_path, unresolved=True)

    summary = preflight.run_repair_materialization_preflight(
        templates_path=templates_path,
        parent_specs_path=parent_specs_path,
        parent_workload_path=parent_workload_path,
        source_profile_localization_path=source_profile_path,
        output_dir=tmp_path / "out",
        target_profile_count=2,
    )

    assert summary["result_class"] == "controlled_routing_smoke_task_quality_repair_materialization_preflight_incomplete_or_fail"
    assert summary["unresolved_parent_count"] == 1
    assert summary["repaired_spec_count"] == 4
