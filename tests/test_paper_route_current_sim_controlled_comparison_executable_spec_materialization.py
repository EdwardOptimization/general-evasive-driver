from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_executable_spec_materialization as materialization
from autodrift.artifacts import read_json, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materializes_no_rollout_executable_specs(tmp_path: Path) -> None:
    summary = materialization.materialize_executable_specs(output_dir=tmp_path / "run")

    assert summary["result_class"] == "current_sim_controlled_comparison_executable_spec_materialization_pass"
    assert summary["executable_spec_count"] == 40
    assert summary["planned_workload_row_count"] == 320
    assert summary["task_family_count"] == 5
    assert summary["profile_count"] == 8
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    specs = read_json(tmp_path / "run" / "executable_task_specs.json")["executable_task_specs"]
    assert len(specs) == 40
    assert all(spec["env_config"]["include_privileged_params"] is False for spec in specs)
    assert all(spec["env_config"]["wheel_observation_mode"] == "none" for spec in specs)
    workload = _read_csv(tmp_path / "run" / "planned_workload.csv")
    assert len(workload) == 320
    assert {row["profile_name"] for row in workload} == set(materialization.DEFAULT_PROFILE_CONFIGS)


def test_materialization_fails_if_task_family_missing(tmp_path: Path) -> None:
    config = read_json(materialization.DEFAULT_BENCHMARK_CONFIG)
    config["task_families"] = [
        row for row in config["task_families"] if row["task_family"] != "T5_terminal_boundary_near_constraint"
    ]
    config_path = tmp_path / "benchmark.json"
    write_json(config_path, config)

    summary = materialization.materialize_executable_specs(
        benchmark_config_path=config_path,
        output_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_executable_spec_materialization_fail"
    assert summary["executable_spec_count"] == 32
    assert summary["task_family_count"] == 4


def test_materialization_preserves_claim_boundary(tmp_path: Path) -> None:
    summary = materialization.materialize_executable_specs(output_dir=tmp_path / "run")

    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    claim_rows = _read_csv(tmp_path / "run" / "claim_boundary.csv")
    blocked = {row["claim"] for row in claim_rows if row["admissible"] == "False"}
    assert "controller_family_ranking" in blocked
    assert "level3_self_identification" in blocked
