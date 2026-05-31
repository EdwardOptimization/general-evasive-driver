from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_measured_runner as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _spec(task_id: str, *, tier: str = "tier_b_feasible_emergency", role: str = "stable_aes_only") -> dict[str, object]:
    return {
        "task_source_id": task_id,
        "candidate_source_id": f"{task_id}_candidate",
        "source_v1_bounded_panel_spec_id": f"{task_id}_source",
        "source_scenario_spec_id": f"{task_id}_scenario",
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "source_split": "public_gate",
        "surface_variant": "steady_surface",
        "target_boundary_mode": "near_miss",
        "selected_accepted_cell_rule": "boundary_min_threshold",
        "label": "aes_feasible",
        "speed_ref": 18.0,
        "mu": 0.4,
        "obstacle_distance": 30.0,
        "obstacle_half_width": 0.8,
        "threshold_score": 0.05,
        "target_support_mode": "boundary_mixed_support",
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "obstacle_relative_velocity_mode": "zero",
            "wheel_observation_mode": "none",
        },
    }


def _workload(
    task_id: str,
    profile_name: str,
    *,
    tier: str = "tier_b_feasible_emergency",
    role: str = "stable_aes_only",
) -> dict[str, object]:
    return {
        "workload_id": f"{task_id}::{profile_name}",
        "task_source_id": task_id,
        "candidate_source_id": f"{task_id}_candidate",
        "profile_name": profile_name,
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "source_split": "public_gate",
        "surface_variant": "steady_surface",
        "target_boundary_mode": "near_miss",
        "selected_accepted_cell_rule": "boundary_min_threshold",
        "strata": f"{tier};{role};steady_surface;public_gate",
        "profile_config_path": f"/tmp/{profile_name}.json",
        "checkpoint_path": f"/tmp/{profile_name}.pt",
        "config_exists": True,
        "checkpoint_exists": True,
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_inputs(tmp_path: Path, *, fail_one: bool = False) -> tuple[Path, Path]:
    specs = [_spec("task_a"), _spec("task_b", tier="tier_d_handling_limit_drift_required", role="drift_required_recovery")]
    workloads = [
        _workload("task_a", "L0_current_masked"),
        _workload("task_a", "L3_online_gru"),
        _workload("task_b", "L0_current_masked", tier="tier_d_handling_limit_drift_required", role="drift_required_recovery"),
        _workload("task_b", "L3_online_gru", tier="tier_d_handling_limit_drift_required", role="drift_required_recovery"),
    ]
    if fail_one:
        workloads[-1]["workload_id"] = "task_b::fail"
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    write_json(specs_path, {"executable_task_specs": specs})
    write_csv_rows(workload_path, workloads)
    return specs_path, workload_path


def _fake_rollout(workload_row, executable_spec, eval_seed):
    if "fail" in str(workload_row["workload_id"]):
        raise RuntimeError("synthetic rollout failure")
    return {
        "return": 1.0,
        "steps": 20,
        "collision": False,
        "obstacle_completed": True,
        "min_clearance_margin": 0.25,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
        "outcome_bucket": "success",
        "termination_reason": "obstacle_completed",
        "obstacle_label": executable_spec["label"],
    }


def test_task_quality_measured_runner_preserves_metadata_and_aggregates(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)
    summary = runner.run_task_quality_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=123,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "task_quality_measured_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["failure_count"] == 0
    assert summary["spec_count"] == 2
    assert summary["profile_count"] == 2
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    episode_rows = (tmp_path / "out" / "episode_rows.csv").read_text(encoding="utf-8")
    assert "tier_d_handling_limit_drift_required" in episode_rows
    assert "drift_required_recovery" in episode_rows
    assert "selected_accepted_cell_rule" in episode_rows
    assert (tmp_path / "out" / "profile_aggregate.csv").exists()
    assert (tmp_path / "out" / "tier_aggregate.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()


def test_task_quality_measured_runner_preserves_rollout_failures(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path, fail_one=True)
    summary = runner.run_task_quality_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=123,
        target_episode_count=4,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "task_quality_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 3
    assert summary["failure_count"] == 1
    failure_rows = (tmp_path / "out" / "failure_rows.csv").read_text(encoding="utf-8")
    assert "synthetic rollout failure" in failure_rows
    assert "task_b::fail" in failure_rows
    summary_json = read_json(tmp_path / "out" / "summary.json")
    assert summary_json["paper_level_claim_made"] is False
    assert summary_json["level3_self_id_claim_made"] is False


def test_task_quality_measured_runner_fails_closed_on_schema_mismatch(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    write_json(specs_path, {"executable_task_specs": [_spec("task_a")]})
    row = _workload("missing_task", "L0_current_masked")
    write_csv_rows(workload_path, [row])

    summary = runner.run_task_quality_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=123,
        target_episode_count=1,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "task_quality_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    validation_failures = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "missing_executable_spec" in validation_failures
