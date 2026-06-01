from __future__ import annotations

from pathlib import Path

import numpy as np
from gymnasium import spaces

from autodrift import paper_route_current_sim_scenario_task_family_reset_validation as reset_validation
from autodrift.artifacts import read_json, write_json


class _FakeEnv:
    def __init__(self, config):
        self.config = config
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(72,), dtype=np.float32)
        self.obstacle_scenario = object()

    def reset(self, seed: int):
        if bool(getattr(self.config, "raise_on_reset", False)):
            raise RuntimeError("synthetic reset failure")
        obstacle = dict(self.config.data.get("obstacle") or {})
        allowed_labels = list(obstacle.get("allowed_labels") or ["aes_feasible"])
        offset_range = tuple(obstacle.get("lateral_offset_range") or [0.0, 0.0])
        obs = np.full(72, float(seed % 11), dtype=np.float32)
        return obs, {
            "obstacle_label": str(allowed_labels[0]),
            "obstacle_distance": 24.0,
            "active_obstacle_half_width": 0.8,
            "obstacle_lateral_offset": float(offset_range[0]),
            "initial_mu": 0.7,
        }

    def close(self) -> None:
        pass


class _FakeConfig:
    def __init__(self, data):
        self.data = dict(data)
        self.raise_on_reset = bool(self.data.get("raise_on_reset", False))


def _env_config(
    *,
    label: str = "aes_feasible",
    offset: float = 0.0,
    privileged: bool = False,
    raise_on_reset: bool = False,
) -> dict[str, object]:
    return {
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": privileged,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "raise_on_reset": raise_on_reset,
        "obstacle": {
            "enabled": True,
            "allowed_labels": [label],
            "lateral_offset_range": [offset, offset],
        },
    }


def _spec(
    spec_id: str,
    *,
    family: str = "R1_aeb_infeasible_stable_aes",
    scenario_family: str = "R1",
    label: str = "aes_feasible",
    allowed_labels: str | None = None,
    bucket: str = "centerline",
    offset: float = 0.0,
    privileged: bool = False,
    raise_on_reset: bool = False,
) -> dict[str, object]:
    return {
        "scenario_spec_id": spec_id,
        "scenario_family_id": scenario_family,
        "role_family": family,
        "role_semantics": "synthetic role",
        "sampled_obstacle_label": label,
        "allowed_labels_metadata_only": allowed_labels or label,
        "labels_enter_actor_input": False,
        "same_scene_group_id": f"{spec_id}_scene",
        "hidden_dynamics_bucket": "nominal",
        "obstacle_longitudinal_timing_bucket": "mid",
        "obstacle_lateral_offset_m": offset,
        "obstacle_lateral_offset_bucket": bucket,
        "initial_speed_mps": 12.0,
        "track_kind": "circle",
        "track_radius_m": 18.0,
        "track_width_m": 6.0,
        "ranking_admissible": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "env_config": _env_config(
            label=label,
            offset=offset,
            privileged=privileged,
            raise_on_reset=raise_on_reset,
        ),
    }


def _write_config(path: Path, specs: list[dict[str, object]]) -> None:
    write_json(path, {"scenario_specs": specs})


def test_scenario_task_family_reset_validation_passes_on_synthetic_specs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs = [
        _spec("center", bucket="centerline", offset=0.0),
        _spec("left", bucket="left_offset", offset=1.2),
        _spec("right", bucket="right_offset", offset=-1.2),
    ]
    config = tmp_path / "config.json"
    _write_config(config, specs)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_scenario_task_family_reset_validation(
        config_path=config,
        output_dir=tmp_path / "out",
        target_spec_count=3,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_reset_validation_pass"
    assert summary["reset_attempt_count"] == 3
    assert summary["reset_success_count"] == 3
    assert summary["actor_contract_violation_count"] == 0
    assert summary["label_not_allowed_count"] == 0
    assert summary["lateral_offset_numeric_mismatch_count"] == 0
    assert summary["lateral_bucket_mismatch_count"] == 0
    assert summary["environment_reset_started"] is True
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert (tmp_path / "out" / "reset_validation_rows.csv").exists()
    assert (tmp_path / "out" / "label_consistency_rows.csv").exists()
    assert (tmp_path / "out" / "lateral_offset_consistency_rows.csv").exists()


def test_scenario_task_family_reset_validation_fails_closed_on_lateral_bucket_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = tmp_path / "config.json"
    _write_config(config, [_spec("left_wrong_sign", bucket="left_offset", offset=-1.2)])
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_scenario_task_family_reset_validation(
        config_path=config,
        output_dir=tmp_path / "out",
        target_spec_count=1,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_reset_validation_fail"
    assert summary["reset_failure_count"] == 0
    assert summary["lateral_offset_numeric_mismatch_count"] == 0
    assert summary["lateral_bucket_mismatch_count"] == 1
    rows = (tmp_path / "out" / "lateral_offset_consistency_rows.csv").read_text(encoding="utf-8")
    assert "left_wrong_sign" in rows


def test_scenario_task_family_reset_validation_records_contract_and_reset_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs = [
        _spec("contract_violation", privileged=True),
        _spec("reset_failure", raise_on_reset=True),
    ]
    config = tmp_path / "config.json"
    _write_config(config, specs)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_scenario_task_family_reset_validation(
        config_path=config,
        output_dir=tmp_path / "out",
        target_spec_count=2,
    )

    assert summary["result_class"] == "current_sim_scenario_task_family_reset_validation_fail"
    assert summary["reset_failure_count"] == 1
    assert summary["actor_contract_violation_count"] == 1
    failure_rows = (tmp_path / "out" / "reset_failures.csv").read_text(encoding="utf-8")
    assert "synthetic reset failure" in failure_rows
    summary_json = read_json(tmp_path / "out" / "summary.json")
    assert summary_json["measured_rollout_started"] is False
    assert summary_json["controller_family_ranking_claim_made"] is False
