from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from autodrift.artifacts import read_json, write_json
from autodrift.executable_v2_support_first_repaired_runner_adapter import (
    IMPORT_VARIANTS,
    ROLLOUT_VARIANTS,
    apply_config_delta,
    parse_config_delta,
    run_repaired_runner_adapter,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _base_env(label: str) -> dict[str, object]:
    return {
        "dt": 0.05,
        "max_steps": 100,
        "track_kind": "circle",
        "track_radius": 18.0,
        "track_width": 5.0,
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero",
        "wheel_observation_mode": "none",
        "obstacle": {
            "enabled": True,
            "allowed_labels": [label],
            "max_sample_attempts": 1,
        },
    }


def _spec(spec_id: str, role: str, surface: str, label: str) -> dict[str, object]:
    return {
        "task_source_id": spec_id,
        "support_first_v2_panel_spec_id": spec_id,
        "support_first_materialized_v2_panel_spec_id": spec_id,
        "source_scenario_spec_id": f"{spec_id}_scenario",
        "role_panel_id": role,
        "v2_role_surface_id": f"{role}::{surface}",
        "surface_variant": surface,
        "scenario_profile_name": f"{role}_{surface}_grid_v0",
        "scenario_profile_group": role,
        "task_family": role,
        "source_edge": surface,
        "window_tag": "mu_0p7::steady_surface",
        "executable_source_family": surface,
        "env_template_family": surface,
        "hidden_dynamics_bucket": "mu_0p7::steady_surface",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": surface,
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "sampled_obstacle_label": label,
        "allowed_labels_metadata_only": label,
        "diagnostic_only_no_ranking_claim": True,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "env_config": _base_env(label),
    }


def _repair_rows(specs: list[dict[str, object]], profiles: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    deltas = {
        "original": {},
        "semantics_only": {"success_semantics": "role_aware_success_v1"},
        "finish_extended": {
            "success_semantics": "role_aware_success_v1",
            "max_steps_multiplier": 1.5,
            "finish_rule": "post_obstacle_recovery_window_v1",
        },
        "road_relaxed": {
            "success_semantics": "role_aware_success_v1",
            "track_width_multiplier": 1.5,
            "offtrack_overshoot_tolerance_m": 0.5,
        },
        "road_relaxed_finish_extended": {
            "success_semantics": "role_aware_success_v1",
            "max_steps_multiplier": 1.5,
            "track_width_multiplier": 1.5,
            "offtrack_overshoot_tolerance_m": 0.5,
            "finish_rule": "post_obstacle_recovery_window_v1",
        },
    }
    index = 0
    for spec in specs:
        for profile in profiles:
            base_workload = f"{spec['task_source_id']}::{profile}"
            for variant, delta in deltas.items():
                rows.append(
                    {
                        "repair_row_id": f"repair-{index:04d}",
                        "repair_source_key": base_workload,
                        "repair_variant_id": variant,
                        "repair_variant_kind": "geometry" if variant in ROLLOUT_VARIANTS else "baseline",
                        "geometry_variant_id": f"{variant}_geometry",
                        "success_semantics_variant_id": "original_binary_success"
                        if variant == "original"
                        else "role_aware_success_v1",
                        "role_semantics_id": f"{spec['role_panel_id']}::role_aware_success_v1",
                        "config_delta_json": json.dumps(delta, sort_keys=True),
                        "workload_id": base_workload,
                        "support_first_workload_id": base_workload,
                        "task_source_id": spec["task_source_id"],
                        "support_first_v2_panel_spec_id": spec["support_first_v2_panel_spec_id"],
                        "support_first_materialized_v2_panel_spec_id": spec[
                            "support_first_materialized_v2_panel_spec_id"
                        ],
                        "source_scenario_spec_id": spec["source_scenario_spec_id"],
                        "controller_profile_name": profile,
                        "profile_name": profile,
                        "scenario_profile_name": spec["scenario_profile_name"],
                        "scenario_profile_group": spec["scenario_profile_group"],
                        "profile_config_path": f"configs/{profile}.json",
                        "checkpoint_path": f"profile_runs/{profile}/checkpoint.pt",
                        "task_family": spec["task_family"],
                        "source_edge": spec["source_edge"],
                        "window_tag": spec["window_tag"],
                        "executable_source_family": spec["executable_source_family"],
                        "env_template_family": spec["env_template_family"],
                        "role_panel_id": spec["role_panel_id"],
                        "v2_role_surface_id": spec["v2_role_surface_id"],
                        "surface_variant": spec["surface_variant"],
                        "hidden_dynamics_bucket": spec["hidden_dynamics_bucket"],
                        "road_boundary_bucket": spec["road_boundary_bucket"],
                        "obstacle_timing_bucket": spec["obstacle_timing_bucket"],
                        "obstacle_lateral_bucket": spec["obstacle_lateral_bucket"],
                        "sampled_obstacle_label": spec["sampled_obstacle_label"],
                        "allowed_labels_metadata_only": spec["allowed_labels_metadata_only"],
                        "strata": "synthetic",
                    }
                )
                index += 1
    return rows


def test_apply_config_delta_validates_and_patches_env_config() -> None:
    patched = apply_config_delta(
        _base_env("aeb_feasible"),
        {
            "success_semantics": "role_aware_success_v1",
            "max_steps_multiplier": 1.5,
            "track_width_multiplier": 1.5,
            "offtrack_overshoot_tolerance_m": 0.5,
            "finish_rule": "post_obstacle_recovery_window_v1",
        },
    )

    assert patched["max_steps"] == 150
    assert patched["track_width"] == 7.5
    assert patched["include_privileged_params"] is False
    assert patched["wheel_observation_mode"] == "none"


def test_parse_config_delta_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="unknown repair config delta keys"):
        parse_config_delta('{"unknown_shortcut": true}')


def test_repaired_runner_adapter_separates_rollout_and_import_rows(tmp_path: Path) -> None:
    specs = [
        _spec("spec_a", "stable_aeb", "steady_surface", "aeb_feasible"),
        _spec("spec_b", "drift_required_recovery", "post_friction_step", "drift_required"),
    ]
    profiles = ["L0_current_masked", "L3_online_gru"]
    repair_matrix = tmp_path / "repair_matrix.csv"
    measured_specs = tmp_path / "measured_specs.json"
    episode_rows = tmp_path / "episodes.csv"
    output = tmp_path / "out"
    _write_csv(repair_matrix, _repair_rows(specs, profiles))
    write_json(measured_specs, {"support_first_measured_executable_specs": specs})
    _write_csv(
        episode_rows,
        [
            {"workload_id": f"{spec['task_source_id']}::{profile}", "success": "False"}
            for spec in specs
            for profile in profiles
        ],
    )

    summary = run_repaired_runner_adapter(
        repair_matrix_path=repair_matrix,
        measured_specs_path=measured_specs,
        episode_rows_path=episode_rows,
        output_dir=output,
        sources_per_role_surface=1,
        target_role_surface_count=2,
        target_controller_profile_count=2,
        target_selected_source_spec_count=2,
        target_executable_spec_count=2 * len(ROLLOUT_VARIANTS),
        target_rollout_workload_cell_count=2 * 2 * len(ROLLOUT_VARIANTS),
        target_import_row_count=2 * 2 * len(IMPORT_VARIANTS),
        target_total_panel_row_count=2 * 2 * (len(ROLLOUT_VARIANTS) + len(IMPORT_VARIANTS)),
    )

    assert summary["result_class"] == "support_first_repaired_runner_adapter_pass"
    assert summary["executable_spec_count"] == 6
    assert summary["rollout_workload_cell_count"] == 12
    assert summary["import_row_count"] == 8
    assert summary["environment_reset_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["real_m1884_matrix_executed"] is False

    payload = read_json(output / "repaired_measured_executable_specs.json")
    emitted = payload["support_first_repaired_measured_executable_specs"]
    road_relaxed = [row for row in emitted if row["repair_variant_id"] == "road_relaxed"][0]
    finish_extended = [row for row in emitted if row["repair_variant_id"] == "finish_extended"][0]
    assert road_relaxed["env_config"]["track_width"] == 7.5
    assert finish_extended["env_config"]["max_steps"] == 150
    assert road_relaxed["labels_enter_actor_input"] is False
    assert road_relaxed["v2_ranking_admissible_by_default"] is False

    workload_text = (output / "repaired_measured_workload_matrix.csv").read_text(encoding="utf-8")
    import_text = (output / "repaired_measured_import_rows.csv").read_text(encoding="utf-8")
    assert "rollout_geometry_variant" in workload_text
    assert "import_existing_episode" in import_text
    assert "semantics_only" in import_text
    assert "controller_family_ranking" in (output / "repaired_measured_claim_boundary.csv").read_text(
        encoding="utf-8"
    )
