from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_scenario_redesign_materialization_preflight as preflight
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


def _template_row(candidate_id: str, *, tier: str = preflight.TIER_C) -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "feasibility_tier_id": tier,
        "source_split": "public_gate",
        "source_role_semantics": "stable_aes_only",
        "surface_variant": "steady_surface",
        "speed_ref": 18.0,
        "mu": 0.4,
        "target_support_mode": "boundary_mixed_support",
        "target_boundary_mode": "near_miss",
        "friction_step_enabled": False,
        "friction_step_at": "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.0,
        "pre_obstacle_track_width": 5.5,
        "max_threshold_score": 0.30,
    }


def _selected_source(candidate_id: str, *, tier: str = preflight.TIER_C) -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "feasibility_tier_id": tier,
        "source_role_semantics": "stable_aes_only",
        "source_split": "public_gate",
        "surface_variant": "steady_surface",
        "speed_ref": 18.0,
        "mu": 0.4,
        "target_support_mode": "boundary_mixed_support",
        "target_boundary_mode": "near_miss",
        "paper_holdout_candidate": False,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def _accepted_cell(candidate_id: str, *, threshold: float, distance: float, half_width: float) -> dict[str, object]:
    return {
        "candidate_source_id": candidate_id,
        "source_v1_bounded_panel_spec_id": candidate_id,
        "source_scenario_spec_id": f"{candidate_id}_scenario",
        "source_role_semantics": "stable_aes_only",
        "profile_name": "unit",
        "profile_group": "stable_aes_only",
        "speed_ref": 18.0,
        "mu": 0.4,
        "obstacle_distance": distance,
        "obstacle_half_width": half_width,
        "label": "aes_feasible",
        "threshold_score": threshold,
        "time_to_obstacle": distance / 18.0,
        "time_after_friction_step": "",
        "friction_step_at": "",
        "accepted": True,
        "reject_reason": "accepted",
    }


def _write_profile_run(root: Path) -> None:
    for name in EXPECTED_PROFILE_NAMES:
        config_path = root / "configs" / f"{name}_seed167400.json"
        checkpoint_path = root / "profile_runs" / name / "seed_167400" / "checkpoint.pt"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}\n", encoding="utf-8")
        checkpoint_path.write_text("placeholder\n", encoding="utf-8")


def test_representative_cell_rule_uses_tier_specific_sort() -> None:
    source = _selected_source("src", tier=preflight.TIER_C)
    cells = {
        "src": [
            _accepted_cell("src", threshold=0.20, distance=20.0, half_width=0.5),
            _accepted_cell("src", threshold=0.05, distance=30.0, half_width=0.7),
        ]
    }

    cell, rule = preflight.representative_cell_for_source(source=source, accepted_cells=cells)

    assert rule == "boundary_min_threshold"
    assert cell is not None
    assert float(cell["threshold_score"]) == 0.05


def test_materialization_preflight_writes_no_rollout_workload(tmp_path: Path) -> None:
    source = _selected_source("src")
    subset = tmp_path / "subset.json"
    template = tmp_path / "template.json"
    accepted = tmp_path / "accepted.csv"
    profile_run = tmp_path / "profiles"
    output = tmp_path / "out"
    write_json(subset, {"selected_sources": [source]})
    write_json(template, {"candidate_sources": [_template_row("src")]})
    write_csv_rows(accepted, [_accepted_cell("src", threshold=0.05, distance=30.0, half_width=0.7)])
    _write_profile_run(profile_run)

    summary = preflight.run_materialization_preflight(
        subset_config_path=subset,
        template_path=template,
        accepted_cells_path=accepted,
        profile_run_dir=profile_run,
        output_dir=output,
        target_executable_spec_count=1,
    )

    assert summary["result_class"] == "task_quality_scenario_materialization_preflight_pass"
    assert summary["executable_spec_count"] == 1
    assert summary["selected_accepted_cell_count"] == 1
    assert summary["workload_cell_count"] == len(EXPECTED_PROFILE_NAMES)
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    specs = read_json(output / "executable_task_specs.json")["executable_task_specs"]
    assert specs[0]["env_config"]["include_privileged_params"] is False
    assert specs[0]["env_config"]["obstacle_relative_velocity_mode"] == "zero"
