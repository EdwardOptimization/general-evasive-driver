from __future__ import annotations

from pathlib import Path

import numpy as np
from gymnasium import spaces

from autodrift import executable_v2_task_quality_reset_validation_preflight as reset_preflight
from autodrift.artifacts import read_json, write_json


class _FakeEnv:
    def __init__(self, config):
        self.config = config
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(72,), dtype=np.float32)
        self.obstacle_scenario = object()
        self.closed = False

    def reset(self, seed: int):
        if bool(getattr(self.config, "raise_on_reset", False)):
            raise RuntimeError("synthetic reset failure")
        obs = np.full(72, float(seed % 7), dtype=np.float32)
        return obs, {
            "obstacle_label": "aes_feasible",
            "initial_mu": 0.45,
            "speed_ref": 18.0,
            "obstacle_distance": 30.0,
            "active_obstacle_half_width": 0.8,
        }

    def close(self) -> None:
        self.closed = True


class _FakeConfig:
    def __init__(self, data):
        self.data = dict(data)
        self.raise_on_reset = bool(self.data.get("raise_on_reset", False))


def _env_config(*, raise_on_reset: bool = False, privileged: bool = False) -> dict[str, object]:
    return {
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": privileged,
        "obstacle_relative_velocity_mode": "zero",
        "wheel_observation_mode": "none",
        "raise_on_reset": raise_on_reset,
    }


def _spec(spec_id: str, *, raise_on_reset: bool = False, privileged: bool = False) -> dict[str, object]:
    return {
        "task_source_id": spec_id,
        "candidate_source_id": f"{spec_id}_candidate",
        "source_v1_bounded_panel_spec_id": f"{spec_id}_source",
        "source_scenario_spec_id": f"{spec_id}_scenario",
        "feasibility_tier_id": "tier_b_feasible_emergency",
        "source_role_semantics": "stable_aes_only",
        "source_split": "public_gate",
        "surface_variant": "steady_surface",
        "selected_accepted_cell_rule": "positive_support_max_threshold",
        "label": "aes_feasible",
        "labels_enter_actor_input": False,
        "paper_holdout_candidate": False,
        "v2_ranking_admissible_by_default": False,
        "env_config": _env_config(raise_on_reset=raise_on_reset, privileged=privileged),
    }


def _write_specs(path: Path, specs: list[dict[str, object]]) -> None:
    write_json(path, {"executable_task_specs": specs})


def test_task_quality_reset_validation_preflight_passes_on_synthetic_specs(tmp_path: Path, monkeypatch) -> None:
    specs_path = tmp_path / "specs.json"
    _write_specs(specs_path, [_spec("spec_0"), _spec("spec_1")])
    monkeypatch.setattr(reset_preflight, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_preflight, "AutoDriftEnv", _FakeEnv)

    summary = reset_preflight.run_task_quality_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_spec_count=2,
    )

    assert summary["result_class"] == "task_quality_reset_validation_preflight_pass"
    assert summary["input_executable_spec_count"] == 2
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["reset_failure_count"] == 0
    assert summary["observation_finite_count"] == 2
    assert summary["observation_dimension_failure_count"] == 0
    assert summary["obstacle_initialized_count"] == 2
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is True
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    rows = (tmp_path / "out" / "reset_rows.csv").read_text(encoding="utf-8")
    assert "spec_0" in rows
    assert (tmp_path / "out" / "contract_rows.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()


def test_task_quality_reset_validation_preflight_preserves_reset_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs_path = tmp_path / "specs.json"
    _write_specs(specs_path, [_spec("spec_0"), _spec("spec_1", raise_on_reset=True)])
    monkeypatch.setattr(reset_preflight, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_preflight, "AutoDriftEnv", _FakeEnv)

    summary = reset_preflight.run_task_quality_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_spec_count=2,
    )

    assert summary["result_class"] == "task_quality_reset_validation_preflight_fail"
    assert summary["reset_success_count"] == 1
    assert summary["reset_failure_count"] == 1
    failure_rows = (tmp_path / "out" / "reset_failure_rows.csv").read_text(encoding="utf-8")
    assert "spec_1" in failure_rows
    assert "synthetic reset failure" in failure_rows
    summary_json = read_json(tmp_path / "out" / "summary.json")
    assert summary_json["measured_rollout_started"] is False
    assert summary_json["controller_family_ranking_claim_made"] is False


def test_task_quality_reset_validation_preflight_fails_closed_on_contract_violation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs_path = tmp_path / "specs.json"
    _write_specs(specs_path, [_spec("spec_0", privileged=True)])
    monkeypatch.setattr(reset_preflight, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_preflight, "AutoDriftEnv", _FakeEnv)

    summary = reset_preflight.run_task_quality_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_spec_count=1,
    )

    assert summary["result_class"] == "task_quality_reset_validation_preflight_fail"
    assert summary["reset_success_count"] == 1
    assert summary["contract_violation_count"] == 1
    contract_rows = (tmp_path / "out" / "contract_rows.csv").read_text(encoding="utf-8")
    assert "include_privileged_params_false" in contract_rows
