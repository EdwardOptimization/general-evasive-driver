from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_benchmark_spec_preflight as preflight
from autodrift.artifacts import read_json, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materializes_no_rollout_benchmark_spec_preflight(tmp_path: Path) -> None:
    summary = preflight.materialize_spec_preflight(
        config_output_path=tmp_path / "benchmark.json",
        output_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_benchmark_spec_preflight_pass"
    assert summary["profile_count"] == 8
    assert summary["task_family_count"] == 5
    assert summary["unsupported_metric_gap_count"] > 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["measured_rollout_started"] is False
    profile_rows = _read_csv(tmp_path / "run" / "profile_matrix.csv")
    assert [row["profile_name"] for row in profile_rows] == list(preflight.PROFILE_ORDER)
    task_rows = _read_csv(tmp_path / "run" / "task_family_specs.csv")
    assert {row["task_family"] for row in task_rows} == {
        "T1_reactive_emergency_avoidance",
        "T2_delayed_actuator_response",
        "T3_diagnostic_warmup_obstacle_reveal",
        "T4_same_current_different_older_history",
        "T5_terminal_boundary_near_constraint",
    }
    config = read_json(tmp_path / "benchmark.json")
    assert config["claim_scope"] == "no_rollout_benchmark_spec_preflight_only"


def test_preflight_fails_when_required_profile_is_missing(tmp_path: Path) -> None:
    summary = preflight.materialize_spec_preflight(
        profile_config_paths=list(preflight.DEFAULT_PROFILE_CONFIGS[:-1]),
        config_output_path=tmp_path / "benchmark.json",
        output_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_benchmark_spec_preflight_fail"
    assert summary["missing_profile_count"] == 1
    assert summary["missing_profiles"] == ["L3_reset_control"]


def test_preflight_detects_forbidden_profile_inputs(tmp_path: Path) -> None:
    source = read_json(preflight.DEFAULT_PROFILE_CONFIGS[0])
    source["controller_profile"]["uses_hidden_oracle_actor_inputs"] = True
    bad_profile = tmp_path / "bad_profile.json"
    write_json(bad_profile, source)

    profile_paths = [bad_profile, *list(preflight.DEFAULT_PROFILE_CONFIGS[1:])]
    summary = preflight.materialize_spec_preflight(
        profile_config_paths=profile_paths,
        config_output_path=tmp_path / "benchmark.json",
        output_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_benchmark_spec_preflight_fail"
    assert summary["forbidden_profile_violation_count"] == 1
    assert summary["guardrail_violation_count"] == 1
