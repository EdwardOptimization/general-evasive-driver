from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_controlled_routing_smoke_measured_runner as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _spec(task_id: str, *, generated: bool = False) -> dict[str, object]:
    return {
        "task_source_id": task_id,
        "panel_source_id": f"panel-{task_id}",
        "panel_task_family": "T2_same_current_different_older_history" if generated else "T1_reactive_active_safety",
        "source_origin": "test",
        "source_kind": "same_current_brake_authority_older_history_proxy" if generated else "anchor_neighborhood",
        "source_edge": "edge",
        "window_tag": "window",
        "source_role_semantics": "role",
        "parent_feasibility_tier_id": "tier",
        "normalized_surface_variant": "surface",
        "sampled_obstacle_label": "label",
        "source_reference": f"ref-{task_id}",
        "materialization_semantics": "smoke_proxy",
        "proxy_template_family": "t4_staged_warmup_capability",
        "generated_source_row": generated,
        "paper_validity_claim": "false",
        "env_config": {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "obstacle_relative_velocity_mode": "zero",
            "wheel_observation_mode": "none",
        },
    }


def _workload(task_id: str, profile: str, *, generated: bool = False) -> dict[str, object]:
    spec = _spec(task_id, generated=generated)
    return {
        "workload_id": f"{task_id}::{profile}",
        "task_source_id": task_id,
        "panel_source_id": spec["panel_source_id"],
        "panel_task_family": spec["panel_task_family"],
        "source_origin": spec["source_origin"],
        "source_kind": spec["source_kind"],
        "source_edge": spec["source_edge"],
        "window_tag": spec["window_tag"],
        "source_role_semantics": spec["source_role_semantics"],
        "parent_feasibility_tier_id": spec["parent_feasibility_tier_id"],
        "normalized_surface_variant": spec["normalized_surface_variant"],
        "sampled_obstacle_label": spec["sampled_obstacle_label"],
        "materialization_semantics": spec["materialization_semantics"],
        "proxy_template_family": spec["proxy_template_family"],
        "generated_source_row": generated,
        "paper_validity_claim": "false",
        "profile_name": profile,
        "profile_config_path": f"/tmp/{profile}.json",
        "checkpoint_path": f"/tmp/{profile}.pt",
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_inputs(tmp_path: Path, *, fail_one: bool = False) -> tuple[Path, Path]:
    specs = [_spec("task_a"), _spec("task_b", generated=True)]
    workloads = [
        _workload("task_a", "L0_current_masked"),
        _workload("task_a", "L3_online_gru"),
        _workload("task_b", "L0_current_masked", generated=True),
        _workload("task_b", "L3_online_gru", generated=True),
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
        "obstacle_label": executable_spec["sampled_obstacle_label"],
    }


def test_controlled_routing_smoke_measured_runner_preserves_metadata(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path)

    summary = runner.run_controlled_routing_smoke_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=203900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "controlled_routing_smoke_measured_execution_pass"
    assert summary["episode_count"] == 4
    assert summary["failure_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["family_quota_pass"] is True
    assert summary["source_kind_quota_pass"] is True
    assert summary["proxy_template_quota_pass"] is True
    assert summary["generated_proxy_quota_pass"] is True
    assert summary["metric_completeness_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    episode_rows = (tmp_path / "out" / "episode_rows.csv").read_text(encoding="utf-8")
    assert "panel_task_family" in episode_rows
    assert "same_current_brake_authority_older_history_proxy" in episode_rows
    assert "generated=true|semantics=smoke_proxy|paper_claim=false" in summary["generated_proxy_counts"]
    assert (tmp_path / "out" / "family_aggregate.csv").exists()
    assert (tmp_path / "out" / "generated_proxy_aggregate.csv").exists()


def test_controlled_routing_smoke_measured_runner_preserves_failures(tmp_path: Path) -> None:
    specs_path, workload_path = _write_inputs(tmp_path, fail_one=True)

    summary = runner.run_controlled_routing_smoke_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=203900,
        target_episode_count=4,
        target_spec_count=2,
        target_profile_count=2,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "controlled_routing_smoke_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 3
    assert summary["failure_count"] == 1
    failure_rows = (tmp_path / "out" / "failure_rows.csv").read_text(encoding="utf-8")
    assert "synthetic rollout failure" in failure_rows
    assert "same_current_brake_authority_older_history_proxy" in failure_rows
    summary_json = read_json(tmp_path / "out" / "summary.json")
    assert summary_json["paper_level_claim_made"] is False
    assert summary_json["level3_self_id_claim_made"] is False


def test_controlled_routing_smoke_measured_runner_fails_closed_on_schema_mismatch(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    write_json(specs_path, {"executable_task_specs": [_spec("task_a")]})
    row = _workload("missing_task", "L0_current_masked")
    write_csv_rows(workload_path, [row])

    summary = runner.run_controlled_routing_smoke_measured_execution(
        output_dir=tmp_path / "out",
        executable_task_specs_path=specs_path,
        workload_path=workload_path,
        eval_seed_base=203900,
        target_episode_count=1,
        target_spec_count=1,
        target_profile_count=1,
        rollout_fn=_fake_rollout,
    )

    assert summary["result_class"] == "controlled_routing_smoke_measured_execution_incomplete_or_fail"
    assert summary["episode_count"] == 0
    validation_failures = (tmp_path / "out" / "validation_failure_rows.csv").read_text(encoding="utf-8")
    assert "missing_executable_spec" in validation_failures
