from __future__ import annotations

from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter as adapter


EFFECTIVE_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "source_candidate_config_path",
    "effective_candidate_config_path",
    "static_validation_pass",
    "effective_candidate_config_written",
    "effective_candidate_config_inside_run_dir",
    "selected_scenario_count",
    "selected_base_pack_count",
    "candidate_without_matching_scenarios",
    "candidate_without_env_config",
    "actor_contract_violation_count",
    "active_config_overwritten",
    "environment_load_attempted",
    "environment_reset_attempted",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "failure_reasons",
]
SCENARIO_FIELDNAMES = [
    "candidate_id",
    "pack_id",
    "pack_path",
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "source_slice_axis",
    "source_slice_value",
    "actor_contract_id",
    "include_privileged_params",
    "wheel_observation_mode",
    "obstacle_relative_velocity_mode",
    "history_length",
    "env_config_present",
    "actor_contract_guardrail_pass",
]


class _FakeConfig:
    def __init__(self, data):
        self.data = dict(data)


class _FakeEnv:
    def __init__(self, config):
        self.config = config

    def reset(self, seed: int):
        return np.full(72, float(seed % 5), dtype=np.float32), {"reset_only": True}

    def close(self) -> None:
        pass


def _env_config() -> dict[str, object]:
    return {
        "history_length": 1,
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "track_kind": "circle",
    }


def _selected(candidate_id: str, pack: str, scenario: str, *, include_env: bool = True) -> dict[str, object]:
    selected = {
        "candidate_id": candidate_id,
        "pack_id": pack,
        "pack_path": f"{pack}.json",
        "scenario_spec_id": scenario,
        "scenario_family_id": "R0",
        "role_family": "R0_stable_avoidable",
        "source_slice_axis": "role_family",
        "source_slice_value": "R0_stable_avoidable",
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "history_length": 1,
        "actor_contract_guardrail_pass": include_env,
    }
    if include_env:
        selected["env_config"] = _env_config()
    return selected


def _write_source(tmp_path: Path, *, include_env: bool = True) -> Path:
    source = tmp_path / "source"
    config_dir = source / "effective_candidate_configs"
    config_dir.mkdir(parents=True)
    candidate_specs = {
        "candidate_a": [
            _selected("candidate_a", "pack_0", "scenario_0", include_env=include_env),
            _selected("candidate_a", "pack_0", "scenario_1", include_env=True),
        ],
        "candidate_b": [
            _selected("candidate_b", "pack_0", "scenario_1", include_env=True),
        ],
    }
    effective_rows = []
    scenario_rows = []
    for candidate_id, selected in candidate_specs.items():
        path = config_dir / f"{candidate_id}.json"
        write_json(
            path,
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": f"{candidate_id}_spec",
                "repair_family": "offtrack_containment_repair",
                "source_slice_axis": "role_family",
                "source_slice_value": "R0_stable_avoidable",
                "selected_scenario_specs": selected,
                "selected_scenario_count": len(selected),
                "claim_boundary": {
                    "active_config_overwritten": False,
                    "environment_step_count": 0,
                    "policy_action_executed": False,
                    "rollout_started": False,
                    "repair_execution_started": False,
                    "training_started": False,
                    "ranking_admissible": False,
                    "winner_selected": False,
                },
            },
        )
        effective_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": f"{candidate_id}_spec",
                "repair_family": "offtrack_containment_repair",
                "source_slice_axis": "role_family",
                "source_slice_value": "R0_stable_avoidable",
                "source_candidate_config_path": "",
                "effective_candidate_config_path": str(path),
                "static_validation_pass": True,
                "effective_candidate_config_written": True,
                "effective_candidate_config_inside_run_dir": True,
                "selected_scenario_count": len(selected),
                "selected_base_pack_count": 1,
                "candidate_without_matching_scenarios": False,
                "candidate_without_env_config": False,
                "actor_contract_violation_count": 0,
                "active_config_overwritten": False,
                "environment_load_attempted": False,
                "environment_reset_attempted": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "failure_reasons": "",
            }
        )
        for item in selected:
            scenario_rows.append(
                {
                    "candidate_id": candidate_id,
                    "pack_id": item["pack_id"],
                    "pack_path": item["pack_path"],
                    "scenario_spec_id": item["scenario_spec_id"],
                    "scenario_family_id": item["scenario_family_id"],
                    "role_family": item["role_family"],
                    "source_slice_axis": item["source_slice_axis"],
                    "source_slice_value": item["source_slice_value"],
                    "actor_contract_id": item["actor_contract_id"],
                    "include_privileged_params": False,
                    "wheel_observation_mode": "none",
                    "obstacle_relative_velocity_mode": "zero",
                    "history_length": 1,
                    "env_config_present": include_env,
                    "actor_contract_guardrail_pass": include_env,
                }
            )
    write_json(
        source / "summary.json",
        {"result_class": "current_sim_dual_axis_effective_config_schema_repair_materialization_pass"},
    )
    write_csv_rows(source / "effective_candidate_config_rows.csv", effective_rows, fieldnames=EFFECTIVE_FIELDNAMES)
    write_csv_rows(source / "effective_candidate_scenario_rows.csv", scenario_rows, fieldnames=SCENARIO_FIELDNAMES)
    return source


def test_effective_candidate_reset_adapter_deduplicates_targets_and_resets_once(tmp_path: Path, monkeypatch) -> None:
    source = _write_source(tmp_path)
    monkeypatch.setattr(adapter, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(adapter, "AutoDriftEnv", _FakeEnv)

    summary = adapter.run_effective_candidate_reset_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        target_candidate_scenario_reference_count=3,
        target_unique_reset_target_count=2,
        eval_seed_base=10,
    )

    assert summary["result_class"] == "current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass"
    assert summary["candidate_scenario_reference_count"] == 3
    assert summary["unique_reset_target_count"] == 2
    assert summary["environment_reset_attempt_count"] == 2
    assert summary["environment_reset_success_count"] == 2
    assert summary["candidate_reset_pass_count"] == 2
    assert summary["environment_step_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["guardrail_violation_count"] == 0
    target_rows = adapter.read_csv_rows(tmp_path / "out" / "reset_target_rows.csv")
    assert len(target_rows) == 2
    assert sorted(int(row["reference_count"]) for row in target_rows) == [1, 2]


def test_effective_candidate_reset_adapter_fails_closed_before_reset_on_static_failure(tmp_path: Path, monkeypatch) -> None:
    source = _write_source(tmp_path, include_env=False)
    monkeypatch.setattr(adapter, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(adapter, "AutoDriftEnv", _FakeEnv)

    summary = adapter.run_effective_candidate_reset_validation_adapter(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        target_candidate_scenario_reference_count=3,
        target_unique_reset_target_count=2,
        eval_seed_base=10,
    )

    assert summary["result_class"] == "current_sim_dual_axis_effective_candidate_reset_validation_adapter_fail"
    assert summary["static_validation_failure_count"] == 1
    assert summary["environment_load_attempt_count"] == 0
    assert summary["environment_reset_attempt_count"] == 0
    assert summary["environment_step_count"] == 0
    static_rows = adapter.read_csv_rows(tmp_path / "out" / "static_validation_rows.csv")
    assert "missing_env_config" in static_rows[0]["failure_reasons"]
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["training_repair_success_claim_made"] is False
