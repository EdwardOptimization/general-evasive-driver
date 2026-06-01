from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_task_quality_offtrack_support_repair_candidates as candidates
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(task_id: str, family: str, outcome: str) -> dict[str, object]:
    return {
        "task_source_id": task_id,
        "task_family": family,
        "outcome_bucket": outcome,
    }


def _spec(task_id: str, family: str, template: str, capability: str) -> dict[str, object]:
    return {
        "task_source_id": task_id,
        "task_family": family,
        "source_family_template": template,
        "capability_pair": capability,
        "claim_level_target": f"claim-{capability}",
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    specs = [
        _spec("t1_a", "T1_reactive_emergency_avoidance", "t5_boundary_axis_retarget", "reactive_current_response"),
        _spec("t2_a", "T2_delayed_actuator_response", "t4_actuator_delay_response", "delayed_actuator_response"),
        _spec("t3_a", "T3_diagnostic_warmup_obstacle_reveal", "t4_staged_warmup_capability", "diagnostic_warmup"),
        _spec("t4_a", "T4_same_current_different_older_history", "t4_capability_step_temporal", "older_history_ambiguity"),
        _spec("t5_a", "T5_terminal_boundary_near_constraint", "t5_high_speed_close_obstacle", "terminal_boundary"),
        _spec("support_a", "T1_reactive_emergency_avoidance", "t5_boundary_axis_retarget", "reactive_current_response"),
    ]
    original_rows = [
        *[_episode("t1_a", "T1_reactive_emergency_avoidance", "off_track_noncollision_noncompletion") for _ in range(3)],
        *[_episode("t3_a", "T3_diagnostic_warmup_obstacle_reveal", "off_track_noncollision_noncompletion") for _ in range(3)],
        *[_episode("t4_a", "T4_same_current_different_older_history", "off_track_noncollision_noncompletion") for _ in range(3)],
        *[_episode("t5_a", "T5_terminal_boundary_near_constraint", "off_track_noncollision_noncompletion") for _ in range(3)],
        *[_episode("support_a", "T1_reactive_emergency_avoidance", "success_obstacle_pass") for _ in range(3)],
    ]
    repeat_rows = [
        *[_episode("t2_a", "T2_delayed_actuator_response", "off_track_noncollision_noncompletion") for _ in range(3)],
        *[_episode("support_a", "T1_reactive_emergency_avoidance", "success_obstacle_pass") for _ in range(3)],
    ]
    original = tmp_path / "original.csv"
    repeat = tmp_path / "repeat.csv"
    spec_path = tmp_path / "specs.json"
    write_csv_rows(original, original_rows)
    write_csv_rows(repeat, repeat_rows)
    write_json(spec_path, {"executable_task_specs": specs})
    return original, repeat, spec_path


def test_current_sim_support_repair_candidate_generation_is_quota_balanced(tmp_path: Path) -> None:
    original, repeat, specs = _write_fixture(tmp_path)

    summary = candidates.run_candidate_generation(
        original_episodes=original,
        repeat_episodes=repeat,
        executable_task_specs=specs,
        output_dir=tmp_path / "out",
        candidate_config=tmp_path / "repair_candidates.json",
    )

    assert summary["result_class"] == "current_sim_task_quality_offtrack_support_repair_candidate_generation_pass"
    assert summary["candidate_count"] == 288
    assert summary["axis_counts"] == candidates.AXIS_QUOTAS
    assert summary["split_counts"] == candidates.EXPECTED_SPLITS
    assert summary["duplicate_candidate_id_count"] == 0
    assert summary["boolean_guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["environment_rollout_started"] is False

    config = read_json(tmp_path / "repair_candidates.json")
    assert config["candidate_count"] == 288
    assert len(config["candidates"]) == 288
    assert {row["repair_split"] for row in config["candidates"]} == {"public_debug", "public_gate"}
    assert all(row["ranking_admissible_by_default"] is False for row in config["candidates"])
    assert all(row["actor_input_contract_changed"] is False for row in config["candidates"])
    assert (tmp_path / "out" / "repair_candidate_rows.csv").exists()


def test_current_sim_support_repair_candidate_generation_rejects_bad_quota(tmp_path: Path) -> None:
    original, repeat, specs = _write_fixture(tmp_path)

    try:
        candidates.run_candidate_generation(
            original_episodes=original,
            repeat_episodes=repeat,
            executable_task_specs=specs,
            output_dir=tmp_path / "out",
            candidate_config=tmp_path / "repair_candidates.json",
            axis_quotas={"offtrack_saturation_relief": 95},
        )
    except ValueError as exc:
        assert "quota for offtrack_saturation_relief" in str(exc)
    else:
        raise AssertionError("expected invalid quota to fail")
