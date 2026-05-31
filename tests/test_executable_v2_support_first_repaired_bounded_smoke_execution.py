from __future__ import annotations

from pathlib import Path

import pytest

from autodrift import executable_v2_support_first_repaired_bounded_smoke_execution as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


PROFILES = ["L0_current_masked", "L3_online_gru"]


def _spec(spec_id: str, role: str, surface: str, label: str) -> dict[str, object]:
    return {
        "task_source_id": f"{spec_id}__repair_finish_extended",
        "support_first_v2_panel_spec_id": f"{spec_id}__repair_finish_extended",
        "support_first_materialized_v2_panel_spec_id": f"{spec_id}__repair_finish_extended",
        "base_task_source_id": spec_id,
        "base_support_first_v2_panel_spec_id": spec_id,
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
        "repair_variant_id": "finish_extended",
        "repair_variant_kind": "geometry",
        "geometry_variant_id": "finish_extended_v1",
        "success_semantics_variant_id": "role_aware_success_v1",
        "role_semantics_id": f"{role}::role_aware_success_v1",
        "diagnostic_only_no_ranking_claim": True,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "env_config": {"history_length": 1},
    }


def _metadata_row(
    *,
    spec_id: str,
    role: str,
    surface: str,
    label: str,
    profile: str,
    variant: str,
    row_index: int,
) -> dict[str, object]:
    rollout = variant == "finish_extended"
    task_source_id = f"{spec_id}__repair_{variant}" if rollout else spec_id
    workload_id = f"{task_source_id}::{profile}" if rollout else f"{spec_id}::{profile}"
    return {
        "repair_row_id": f"repair-{row_index:04d}",
        "repair_source_key": f"{spec_id}::{profile}",
        "repair_variant_id": variant,
        "repair_variant_kind": "geometry" if rollout else "baseline",
        "geometry_variant_id": f"{variant}_geometry",
        "success_semantics_variant_id": "original_binary_success" if variant == "original" else "role_aware_success_v1",
        "role_semantics_id": f"{role}::role_aware_success_v1",
        "config_delta_json": "{}",
        "diagnostic_only_no_ranking_claim": True,
        "execution_design_required": rollout,
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": rollout,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "workload_id": workload_id,
        "support_first_workload_id": f"{spec_id}::{profile}",
        "task_source_id": task_source_id,
        "support_first_v2_panel_spec_id": task_source_id,
        "support_first_materialized_v2_panel_spec_id": task_source_id,
        "source_scenario_spec_id": f"{spec_id}_scenario",
        "controller_profile_name": profile,
        "profile_name": profile,
        "scenario_profile_name": f"{role}_{surface}_grid_v0",
        "scenario_profile_group": role,
        "profile_config_path": str(Path("configs") / f"{profile}.json"),
        "checkpoint_path": str(Path("profile_runs") / profile / "checkpoint.pt"),
        "task_family": role,
        "source_edge": surface,
        "window_tag": "mu_0p7::steady_surface",
        "executable_source_family": surface,
        "env_template_family": surface,
        "role_panel_id": role,
        "v2_role_surface_id": f"{role}::{surface}",
        "surface_variant": surface,
        "hidden_dynamics_bucket": "mu_0p7::steady_surface",
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": surface,
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "sampled_obstacle_label": label,
        "allowed_labels_metadata_only": label,
        "strata": f"synthetic;role_{role};profile_{profile}",
        "base_workload_id": f"{spec_id}::{profile}",
        "base_support_first_workload_id": f"{spec_id}::{profile}",
        "base_task_source_id": spec_id,
        "base_support_first_v2_panel_spec_id": spec_id,
        "execution_row_kind": "rollout_geometry_variant" if rollout else "import_existing_episode",
        "repaired_workload_id": f"{task_source_id}::{profile}" if rollout else "",
        "repaired_import_row_id": f"repair-{row_index:04d}" if not rollout else "",
        "import_source_episode_workload_id": f"{spec_id}::{profile}" if not rollout else "",
        "semantic_recompute_required": variant == "semantics_only",
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    source_specs = [
        ("spec_a", "stable_aeb", "steady_surface", "aeb_feasible"),
        ("spec_b", "drift_required_recovery", "post_friction_step", "drift_required"),
    ]
    specs = [_spec(*values) for values in source_specs]
    workload_rows: list[dict[str, object]] = []
    import_rows: list[dict[str, object]] = []
    source_episode_rows: list[dict[str, object]] = []
    row_index = 0
    for spec_id, role, surface, label in source_specs:
        for profile in PROFILES:
            workload_rows.append(
                _metadata_row(
                    spec_id=spec_id,
                    role=role,
                    surface=surface,
                    label=label,
                    profile=profile,
                    variant="finish_extended",
                    row_index=row_index,
                )
            )
            row_index += 1
            for variant in ["original", "semantics_only"]:
                import_rows.append(
                    _metadata_row(
                        spec_id=spec_id,
                        role=role,
                        surface=surface,
                        label=label,
                        profile=profile,
                        variant=variant,
                        row_index=row_index,
                    )
                )
                row_index += 1
            source_episode_rows.append(_fake_source_episode(spec_id, profile, role, surface, label))

    specs_path = tmp_path / "repaired_specs.json"
    workload_path = tmp_path / "repaired_workload.csv"
    import_path = tmp_path / "repaired_import.csv"
    source_episode_path = tmp_path / "source_episodes.csv"
    write_json(specs_path, {"support_first_repaired_measured_executable_specs": specs})
    write_csv_rows(workload_path, workload_rows)
    write_csv_rows(import_path, import_rows)
    write_csv_rows(source_episode_path, source_episode_rows)
    return specs_path, workload_path, import_path, source_episode_path


def _profile_rows(tmp_path: Path) -> list[dict[str, object]]:
    return [
        {
            "profile_name": name,
            "config_path": str(tmp_path / "configs" / f"{name}.json"),
            "checkpoint_path": str(tmp_path / "profile_runs" / name / "checkpoint.pt"),
        }
        for name in PROFILES
    ]


def _metric_row(*, workload_id: str, task_source_id: str, profile: str, role: str, surface: str, label: str) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "task_source_id": task_source_id,
        "profile_name": profile,
        "task_family": role,
        "source_edge": surface,
        "window_tag": "mu_0p7::steady_surface",
        "strata": f"synthetic;role_{role};profile_{profile}",
        "executable_source_family": surface,
        "env_template_family": surface,
        "profile_config_path": "fake_config.json",
        "checkpoint_path": "fake_checkpoint.pt",
        "profile_env_history_length": 1,
        "eval_seed": 1,
        "routing_smoke_only": False,
        "full_rollout_execution": True,
        "private_holdout_used": False,
        "promoted": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "success": True,
        "obstacle_completed": True,
        "obstacle_passed_raw": True,
        "collision": False,
        "obstacle_label": label,
        "sampled_obstacle_label": label,
        "min_clearance_margin": 1.0,
        "return": 10.0,
        "steps": 32,
        "action_rate_mean": 0.05,
        "high_sideslip_fraction": 0.0,
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "obstacle_passed",
        "dt": 0.02,
        "track_width": 5.0,
        "first_obstacle_pass_step": 16,
        "first_obstacle_pass_time_s": 0.32,
        "first_recovery_step": 20,
        "first_recovery_time_s": 0.40,
        "recovery_success": True,
        "recovery_time_proxy": 0.08,
        "max_abs_beta": 0.1,
        "max_abs_yaw_rate": 0.2,
        "drift_used": False,
        "controlled_drift_recovery_success": True,
        "impact_speed_proxy": 0.0,
        "impact_beta_abs": 0.0,
        "impact_yaw_rate_abs": 0.0,
        "impact_severity_proxy": 0.0,
        "collision_mitigation_score": 0.0,
        "max_off_track_overshoot": 0.0,
        "time_to_first_off_track_s": 0.0,
        "off_track_severity_proxy": 0.0,
    }


def _fake_source_episode(spec_id: str, profile: str, role: str, surface: str, label: str) -> dict[str, object]:
    row = _metric_row(
        workload_id=f"{spec_id}::{profile}",
        task_source_id=spec_id,
        profile=profile,
        role=role,
        surface=surface,
        label=label,
    )
    row.update(
        {
            "support_first_workload_id": f"{spec_id}::{profile}",
            "support_first_v2_panel_spec_id": spec_id,
            "support_first_materialized_v2_panel_spec_id": spec_id,
            "source_scenario_spec_id": f"{spec_id}_scenario",
            "controller_profile_name": profile,
            "scenario_profile_name": f"{role}_{surface}_grid_v0",
            "scenario_profile_group": role,
            "role_panel_id": role,
            "v2_role_surface_id": f"{role}::{surface}",
            "surface_variant": surface,
            "hidden_dynamics_bucket": "mu_0p7::steady_surface",
            "road_boundary_bucket": "circle_r18",
            "obstacle_timing_bucket": surface,
            "obstacle_lateral_bucket": "support_first_width_0p7",
            "allowed_labels_metadata_only": label,
            "support_first_measured_runner_execution": True,
            "environment_rollout_started": True,
            "measured_rollout_started": True,
            "policy_action_executed": True,
        }
    )
    return row


def _fake_rollout_row(workload_row, eval_seed: int) -> dict[str, object]:
    return _metric_row(
        workload_id=workload_row["workload_id"],
        task_source_id=workload_row["task_source_id"],
        profile=workload_row["profile_name"],
        role=workload_row["role_panel_id"],
        surface=workload_row["surface_variant"],
        label=workload_row["sampled_obstacle_label"],
    ) | {"eval_seed": eval_seed}


def _patch_runtime(monkeypatch, tmp_path: Path, call_log: list[str] | None = None) -> None:
    profile_rows = _profile_rows(tmp_path)
    monkeypatch.setattr(runner, "profile_artifact_rows", lambda **_kwargs: profile_rows)
    monkeypatch.setattr(
        runner,
        "_load_profile_cache",
        lambda rows, device: {row["profile_name"]: ({}, object()) for row in rows},
    )

    def fake_run_workload_cell(workload_row, executable_spec, profile_config, model, profile_row, eval_seed):
        if call_log is not None:
            call_log.append(str(workload_row["workload_id"]))
        return _fake_rollout_row(workload_row, eval_seed)

    monkeypatch.setattr(runner, "run_workload_cell", fake_run_workload_cell)


def _run_smoke(tmp_path: Path, monkeypatch, *, source_episode_path: Path | None = None):
    specs_path, workload_path, import_path, default_source_episode_path = _write_inputs(tmp_path)
    _patch_runtime(monkeypatch, tmp_path)
    return runner.run_repaired_bounded_smoke_execution(
        support_first_repaired_measured_specs_path=specs_path,
        support_first_repaired_workload_path=workload_path,
        support_first_repaired_import_rows_path=import_path,
        source_episode_rows_path=source_episode_path or default_source_episode_path,
        output_dir=tmp_path / "out",
        resume=False,
        target_rollout_episode_count=4,
        target_import_episode_count=8,
        target_total_panel_row_count=12,
        target_controller_profile_count=2,
        target_selected_source_spec_count=2,
        target_repaired_executable_spec_count=2,
        target_role_panel_count=2,
        target_role_surface_count=2,
        target_repair_variant_count=3,
        target_rollout_variant_count=1,
        target_import_variant_count=2,
    )


def test_repaired_bounded_smoke_execution_merges_rollout_and_import_rows(tmp_path: Path, monkeypatch) -> None:
    summary = _run_smoke(tmp_path, monkeypatch)

    assert summary["result_class"] == "executable_v2_support_first_repaired_bounded_smoke_execution_pass"
    assert summary["rollout_episode_count"] == 4
    assert summary["import_episode_count"] == 8
    assert summary["total_panel_row_count"] == 12
    assert summary["failure_count"] == 0
    assert summary["import_failure_count"] == 0
    assert summary["duplicate_panel_row_count"] == 0
    assert summary["metric_completeness_passed"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    rollout_rows = read_csv_rows(tmp_path / "out" / "rollout_episode_rows.csv")
    import_rows = read_csv_rows(tmp_path / "out" / "import_episode_rows.csv")
    panel_rows = read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert len(rollout_rows) == 4
    assert len(import_rows) == 8
    assert len(panel_rows) == 12
    assert rollout_rows[0]["execution_row_kind"] == "rollout_geometry_variant"
    assert rollout_rows[0]["environment_rollout_started"] == "True"
    assert import_rows[0]["execution_row_kind"] == "import_existing_episode"
    assert import_rows[0]["imported_episode_row"] == "True"
    assert import_rows[0]["environment_rollout_started"] == "False"
    assert import_rows[0]["source_environment_rollout_started"] == "True"
    assert {row["repair_variant_id"] for row in panel_rows} == {"finish_extended", "original", "semantics_only"}
    assert (tmp_path / "out" / "repair_variant_aggregate.csv").exists()
    assert (tmp_path / "out" / "controller_profile_role_surface_repair_variant_aggregate.csv").exists()
    assert (tmp_path / "out" / "import_rollout_alignment.csv").exists()


def test_repaired_bounded_smoke_execution_resume_skips_rollout_rows(tmp_path: Path, monkeypatch) -> None:
    specs_path, workload_path, import_path, source_episode_path = _write_inputs(tmp_path)
    call_log: list[str] = []
    _patch_runtime(monkeypatch, tmp_path, call_log)
    kwargs = {
        "support_first_repaired_measured_specs_path": specs_path,
        "support_first_repaired_workload_path": workload_path,
        "support_first_repaired_import_rows_path": import_path,
        "source_episode_rows_path": source_episode_path,
        "output_dir": tmp_path / "out",
        "target_rollout_episode_count": 4,
        "target_import_episode_count": 8,
        "target_total_panel_row_count": 12,
        "target_controller_profile_count": 2,
        "target_selected_source_spec_count": 2,
        "target_repaired_executable_spec_count": 2,
        "target_role_panel_count": 2,
        "target_role_surface_count": 2,
        "target_repair_variant_count": 3,
        "target_rollout_variant_count": 1,
        "target_import_variant_count": 2,
    }
    runner.run_repaired_bounded_smoke_execution(**kwargs, resume=False)
    runner.run_repaired_bounded_smoke_execution(**kwargs, resume=True)

    assert len(call_log) == 4
    assert len(read_csv_rows(tmp_path / "out" / "rollout_episode_rows.csv")) == 4
    assert len(read_csv_rows(tmp_path / "out" / "episode_rows.csv")) == 12
    state = read_json(tmp_path / "out" / "run_state.json")
    assert state["complete"] is True
    assert state["completed_rollout_count"] == 4


def test_repaired_bounded_smoke_execution_reports_missing_import_source(tmp_path: Path, monkeypatch) -> None:
    specs_path, workload_path, import_path, source_episode_path = _write_inputs(tmp_path)
    source_rows = read_csv_rows(source_episode_path)
    write_csv_rows(source_episode_path, source_rows[:-1])
    _patch_runtime(monkeypatch, tmp_path)

    summary = runner.run_repaired_bounded_smoke_execution(
        support_first_repaired_measured_specs_path=specs_path,
        support_first_repaired_workload_path=workload_path,
        support_first_repaired_import_rows_path=import_path,
        source_episode_rows_path=source_episode_path,
        output_dir=tmp_path / "out",
        resume=False,
        target_rollout_episode_count=4,
        target_import_episode_count=8,
        target_total_panel_row_count=12,
        target_controller_profile_count=2,
        target_selected_source_spec_count=2,
        target_repaired_executable_spec_count=2,
        target_role_panel_count=2,
        target_role_surface_count=2,
        target_repair_variant_count=3,
        target_rollout_variant_count=1,
        target_import_variant_count=2,
    )

    assert summary["result_class"] == "executable_v2_support_first_repaired_bounded_smoke_execution_incomplete_or_fail"
    assert summary["source_episode_join_missing_count"] == 2
    failures = read_csv_rows(tmp_path / "out" / "import_failure_rows.csv")
    assert len(failures) == 2
    assert failures[0]["error_type"] == "MissingImportSourceEpisode"
    assert failures[0]["controller_family_ranking_claim_made"] == "False"


def test_repaired_bounded_smoke_loader_requires_repaired_key(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    write_json(path, {"support_first_measured_executable_specs": []})

    with pytest.raises(ValueError, match="support_first_repaired_measured_executable_specs"):
        runner.load_support_first_repaired_measured_specs(path)
