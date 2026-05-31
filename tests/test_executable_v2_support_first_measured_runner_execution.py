from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_support_first_measured_runner_execution as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    specs: list[dict[str, object]] = []
    workload: list[dict[str, object]] = []
    profiles = ["L0_current_masked", "L3_online_gru"]
    spec_rows = [
        ("sfm_000", "stable_aeb", "steady_surface", "aeb_feasible", "mu_0p70::steady_surface"),
        (
            "sfm_001",
            "drift_required_recovery",
            "post_friction_step",
            "drift_required",
            "mu_0p25::post_friction_step",
        ),
    ]
    for spec_id, role, surface, label, hidden_bucket in spec_rows:
        spec = {
            "task_source_id": spec_id,
            "support_first_v2_panel_spec_id": spec_id,
            "support_first_materialized_v2_panel_spec_id": f"mat_{spec_id}",
            "source_scenario_spec_id": f"{spec_id}_scenario",
            "role_panel_id": role,
            "v2_role_surface_id": f"{role}::{surface}",
            "surface_variant": surface,
            "scenario_profile_name": f"{role}_{surface}_grid_v0",
            "scenario_profile_group": role,
            "task_family": role,
            "source_edge": surface,
            "window_tag": hidden_bucket,
            "executable_source_family": surface,
            "env_template_family": surface,
            "hidden_dynamics_bucket": hidden_bucket,
            "road_boundary_bucket": "circle_r18",
            "obstacle_timing_bucket": surface,
            "obstacle_lateral_bucket": "support_first_width_0p7",
            "sampled_obstacle_label": label,
            "allowed_labels_metadata_only": label,
            "env_config": {"history_length": 1},
        }
        specs.append(spec)
        for profile_name in profiles:
            workload_id = f"{spec_id}::{profile_name}"
            workload.append(
                {
                    "workload_id": workload_id,
                    "support_first_workload_id": workload_id,
                    "task_source_id": spec_id,
                    "support_first_v2_panel_spec_id": spec_id,
                    "support_first_materialized_v2_panel_spec_id": f"mat_{spec_id}",
                    "source_scenario_spec_id": f"{spec_id}_scenario",
                    "controller_profile_name": profile_name,
                    "profile_name": profile_name,
                    "scenario_profile_name": f"{role}_{surface}_grid_v0",
                    "scenario_profile_group": role,
                    "profile_config_path": str(tmp_path / "configs" / f"{profile_name}.json"),
                    "checkpoint_path": str(tmp_path / "profile_runs" / profile_name / "checkpoint.pt"),
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "task_family": role,
                    "source_edge": surface,
                    "window_tag": hidden_bucket,
                    "executable_source_family": surface,
                    "env_template_family": surface,
                    "role_panel_id": role,
                    "v2_role_surface_id": f"{role}::{surface}",
                    "surface_variant": surface,
                    "hidden_dynamics_bucket": hidden_bucket,
                    "road_boundary_bucket": "circle_r18",
                    "obstacle_timing_bucket": surface,
                    "obstacle_lateral_bucket": "support_first_width_0p7",
                    "sampled_obstacle_label": label,
                    "allowed_labels_metadata_only": label,
                    "strata": f"support_first;role_{role};surface_{surface};profile_{profile_name}",
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                    "controller_family_ranking_claim_made": False,
                    "paper_level_claim_made": False,
                    "level3_self_id_claim_made": False,
                }
            )
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    write_json(specs_path, {"support_first_measured_executable_specs": specs})
    write_csv_rows(workload_path, workload)
    return specs_path, workload_path


def _profile_rows(tmp_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in ["L0_current_masked", "L3_online_gru"]:
        rows.append(
            {
                "profile_name": name,
                "config_path": str(tmp_path / "configs" / f"{name}.json"),
                "checkpoint_path": str(tmp_path / "profile_runs" / name / "checkpoint.pt"),
            }
        )
    return rows


def _fake_episode_row(workload_row, eval_seed: int) -> dict[str, object]:
    return {
        "workload_id": workload_row["workload_id"],
        "task_source_id": workload_row["task_source_id"],
        "profile_name": workload_row["profile_name"],
        "task_family": workload_row["task_family"],
        "source_edge": workload_row["source_edge"],
        "window_tag": workload_row["window_tag"],
        "strata": workload_row["strata"],
        "executable_source_family": workload_row["executable_source_family"],
        "env_template_family": workload_row["env_template_family"],
        "profile_config_path": "fake_config.json",
        "checkpoint_path": "fake_checkpoint.pt",
        "profile_env_history_length": 1,
        "eval_seed": eval_seed,
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
        "obstacle_label": workload_row["sampled_obstacle_label"],
        "sampled_obstacle_label": workload_row["sampled_obstacle_label"],
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
        return _fake_episode_row(workload_row, eval_seed)

    monkeypatch.setattr(runner, "run_workload_cell", fake_run_workload_cell)


def test_support_first_measured_runner_execution_smoke(tmp_path: Path, monkeypatch) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)
    _patch_runtime(monkeypatch, tmp_path)

    summary = runner.run_support_first_measured_runner_execution(
        support_first_measured_specs_path=specs_path,
        support_first_workload_path=workload_path,
        output_dir=tmp_path / "out",
        resume=False,
        target_controller_profile_count=2,
        target_support_first_spec_count=2,
        target_role_panel_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_support_first_measured_runner_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["failure_count"] == 0
    assert summary["controller_profile_count"] == 2
    assert summary["support_first_spec_count"] == 2
    assert summary["role_panel_count"] == 2
    assert summary["role_surface_count"] == 2
    assert summary["metric_completeness_passed"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is True
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    episode_rows = read_csv_rows(tmp_path / "out" / "episode_rows.csv")
    assert len(episode_rows) == 4
    first = episode_rows[0]
    assert first["profile_name"] == first["controller_profile_name"]
    assert first["scenario_profile_name"]
    assert first["v2_role_surface_id"]
    assert first["support_first_measured_runner_execution"] == "True"
    assert first["full_rollout_execution"] == "False"
    assert first["sampled_obstacle_label"] in {"aeb_feasible", "drift_required"}
    assert (tmp_path / "out" / "controller_profile_aggregate.csv").exists()
    assert (tmp_path / "out" / "role_surface_aggregate.csv").exists()
    assert (tmp_path / "out" / "controller_profile_role_surface_aggregate.csv").exists()
    assert (tmp_path / "out" / "metric_completeness_summary.csv").exists()


def test_support_first_measured_runner_resume_skips_completed(tmp_path: Path, monkeypatch) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)
    call_log: list[str] = []
    _patch_runtime(monkeypatch, tmp_path, call_log)

    kwargs = {
        "support_first_measured_specs_path": specs_path,
        "support_first_workload_path": workload_path,
        "output_dir": tmp_path / "out",
        "target_controller_profile_count": 2,
        "target_support_first_spec_count": 2,
        "target_role_panel_count": 2,
        "target_role_surface_count": 2,
    }
    runner.run_support_first_measured_runner_execution(**kwargs, resume=False)
    runner.run_support_first_measured_runner_execution(**kwargs, resume=True)

    assert len(call_log) == 4
    assert len(read_csv_rows(tmp_path / "out" / "episode_rows.csv")) == 4
    state = read_json(tmp_path / "out" / "run_state.json")
    assert state["complete"] is True
    assert state["completed_count"] == 4


def test_support_first_measured_runner_records_failure_rows(tmp_path: Path, monkeypatch) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)
    profile_rows = _profile_rows(tmp_path)
    monkeypatch.setattr(runner, "profile_artifact_rows", lambda **_kwargs: profile_rows)
    monkeypatch.setattr(
        runner,
        "_load_profile_cache",
        lambda rows, device: {row["profile_name"]: ({}, object()) for row in rows},
    )

    def fake_run_workload_cell(workload_row, executable_spec, profile_config, model, profile_row, eval_seed):
        if str(workload_row["workload_id"]).endswith("L3_online_gru"):
            raise RuntimeError("synthetic rollout failure")
        return _fake_episode_row(workload_row, eval_seed)

    monkeypatch.setattr(runner, "run_workload_cell", fake_run_workload_cell)

    summary = runner.run_support_first_measured_runner_execution(
        support_first_measured_specs_path=specs_path,
        support_first_workload_path=workload_path,
        output_dir=tmp_path / "out",
        resume=False,
        target_controller_profile_count=2,
        target_support_first_spec_count=2,
        target_role_panel_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_support_first_measured_runner_execution_incomplete_or_fail"
    assert summary["episode_count"] == 2
    assert summary["failure_count"] == 2
    failures = read_csv_rows(tmp_path / "out" / "failure_rows.csv")
    assert len(failures) == 2
    assert failures[0]["controller_profile_name"] == "L3_online_gru"
    assert failures[0]["error_type"] == "RuntimeError"
    assert failures[0]["training_started"] == "False"
    assert failures[0]["controller_family_ranking_claim_made"] == "False"


def test_support_first_measured_runner_loader_requires_support_first_key(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    write_json(path, {"executable_task_specs": []})

    try:
        runner.load_support_first_measured_specs(path)
    except ValueError as exc:
        assert "support_first_measured_executable_specs" in str(exc)
    else:
        raise AssertionError("expected ValueError")
