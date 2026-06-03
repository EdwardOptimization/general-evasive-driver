from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from autodrift import paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel as diagnostic
from autodrift.artifacts import read_json, write_csv_rows, write_json


TARGET_FIELDNAMES = [
    "reset_target_id",
    "preflight_id",
    "overlay_id",
    "source_candidate_id",
    "source_panel_id",
    "candidate_group",
    "role_scope",
    "sampled_obstacle_label_scope",
    "split",
    "overlay_family",
    "env_config_overlay_hash",
    "effective_env_config_path",
    "eval_seed",
    "expected_observation_dim",
]


class _FakeConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = deepcopy(data)


class _FakeScenario:
    label = "aes_feasible"


class _FakeEnv:
    def __init__(self, config: _FakeConfig) -> None:
        self.config = config
        self.obstacle_scenario = None
        self.step_count = 0

    def reset(self, *, seed: int) -> tuple[np.ndarray, dict[str, Any]]:
        data = self.config.data
        obstacle = dict(data.get("obstacle") or {})
        randomization = dict(data.get("randomization") or {})
        nominal_hidden = list(randomization.get("mu_range", [])) == [0.9, 0.9]
        threshold_relaxed = obstacle.get("max_threshold_score") is None
        geometry_wider = list(obstacle.get("distance_range", [])) == [18.0, 38.0]
        success = bool(nominal_hidden or threshold_relaxed or geometry_wider or int(seed) % 2 == 0)
        if not success:
            raise RuntimeError("failed to sample an obstacle scenario matching the configured filters")
        self.obstacle_scenario = _FakeScenario()
        return np.ones(72, dtype=np.float64), {
            "initial_mu": 0.7,
            "mu": 0.7,
            "mass_scale": 1.0,
            "tire_stiffness_scale": 1.0,
            "brake_scale": 1.0,
            "steer_tau_scale": 1.0,
            "drive_tau_scale": 1.0,
            "speed_ref": 12.0,
            "obstacle_distance": 25.0,
            "obstacle_lateral_offset": 0.1,
            "active_obstacle_half_width": 0.7,
            "obstacle_threshold_score": 0.2,
        }

    def close(self) -> None:
        return None


def _base_effective_config() -> dict[str, Any]:
    return {
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
        "obstacle": {
            "enabled": True,
            "allowed_labels": ["aes_feasible"],
            "distance_range": [20.0, 34.0],
            "lateral_offset_range": [-0.4, 0.4],
            "half_width_range": [0.55, 0.8],
            "max_sample_attempts": 10000,
            "max_threshold_score": 0.35,
            "require_aeb_infeasible": True,
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
            "perception_reveal_distance": 55.0,
            "perception_reveal_step": 0,
        },
        "randomization": {
            "mu_range": [0.25, 1.15],
            "mass_scale_range": [0.85, 1.2],
            "cg_shift_range": [-0.12, 0.12],
            "inertia_scale_range": [0.85, 1.25],
            "tire_stiffness_scale_range": [0.65, 1.35],
            "drive_scale_range": [0.8, 1.15],
            "brake_scale_range": [0.8, 1.15],
            "actuator_tau_scale_range": [0.75, 1.75],
        },
    }


def _write_m2464_fixture(root: Path, *, include_r1: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    config_dir = root / "effective_env_configs"
    config_dir.mkdir()
    write_json(
        root / "summary.json",
        {
            "result_class": "scenario_quality_concrete_overlay_reset_validation_fail",
            "target_reset_count": 6,
            "static_validation_pass_count": 6,
            "effective_env_config_written_count": 6,
            "environment_reset_attempt_count": 6,
            "environment_reset_success_count": 4,
            "environment_reset_failure_count": 2,
            "failure_types_observed": ["scenario_sampling_failure"],
        },
    )
    rows: list[dict[str, Any]] = []
    for index in range(1, 4):
        path = config_dir / f"r0_{index}.json"
        write_json(path, {"effective_env_config": _base_effective_config()})
        rows.append(
            {
                "reset_target_id": f"m2464_reset_target_{index:03d}",
                "preflight_id": f"m2458_preflight_{index:03d}",
                "overlay_id": f"m2461_overlay_{index:03d}",
                "source_candidate_id": f"r0_candidate_{index}",
                "source_panel_id": "r0_panel",
                "candidate_group": "stable_feasibility_support",
                "role_scope": "R0_stable_avoidable",
                "sampled_obstacle_label_scope": "aeb_feasible",
                "split": "public_debug",
                "overlay_family": "R0_stable_avoidable",
                "env_config_overlay_hash": "hash-r0",
                "effective_env_config_path": str(path),
                "eval_seed": 246400 + index,
                "expected_observation_dim": 72,
            }
        )
    if include_r1:
        for index in range(4, 7):
            path = config_dir / f"r1_{index}.json"
            write_json(path, {"effective_env_config": _base_effective_config()})
            rows.append(
                {
                    "reset_target_id": f"m2464_reset_target_{index:03d}",
                    "preflight_id": f"m2458_preflight_{index:03d}",
                    "overlay_id": f"m2461_overlay_{index:03d}",
                    "source_candidate_id": f"m2455_stable_aes_support_{index - 3:03d}",
                    "source_panel_id": "r1_panel",
                    "candidate_group": "stable_aes_support",
                    "role_scope": "R1_aeb_infeasible_stable_aes",
                    "sampled_obstacle_label_scope": "aes_feasible",
                    "split": "public_debug",
                    "overlay_family": "R1_aeb_infeasible_stable_aes",
                    "env_config_overlay_hash": "hash-r1",
                    "effective_env_config_path": str(path),
                    "eval_seed": 246400 + index,
                    "expected_observation_dim": 72,
                }
            )
    write_csv_rows(root / "reset_target_rows.csv", rows, fieldnames=TARGET_FIELDNAMES)
    write_csv_rows(root / "reset_validation_rows.csv", [], fieldnames=["reset_target_id", "environment_reset_success"])
    write_csv_rows(root / "reset_failure_rows.csv", [], fieldnames=["reset_target_id", "failure_type", "failure_reason"])
    return root


def test_r1_reset_sampling_diagnostic_panel_writes_seed_and_variant_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    m2464_dir = _write_m2464_fixture(tmp_path / "m2464")
    monkeypatch.setattr(diagnostic, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(diagnostic, "AutoDriftEnv", _FakeEnv)

    summary = diagnostic.run_r1_reset_sampling_diagnostic_panel(
        m2464_dir=m2464_dir,
        output_dir=tmp_path / "out",
        eval_seed_base=100,
        reset_seed_count=4,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == diagnostic.RESULT_COMPLETE
    assert summary["r1_source_target_count"] == 3
    assert summary["source_overlay_hash_count"] == 1
    assert summary["source_unique_effective_config_count"] == 1
    assert summary["variant_count"] == 5
    assert summary["diagnostic_attempt_count"] == 20
    assert summary["baseline_reset_success_count"] == 2
    assert summary["baseline_reset_failure_count"] == 2
    assert summary["environment_step_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert "seed_fragility" in summary["diagnostic_classification"]
    assert "hidden_dynamics_randomization_fragility" in summary["diagnostic_classification"]
    assert "threshold_strictness_signal" in summary["diagnostic_classification"]

    output = Path(summary["output_dir"])
    diagnostic_rows = diagnostic.read_csv_rows(output / "diagnostic_rows.csv")
    variant_rows = diagnostic.read_csv_rows(output / "variant_rows.csv")
    classification_keys = {
        row["classification_key"] for row in diagnostic.read_csv_rows(output / "classification_rows.csv")
    }
    assert len(diagnostic_rows) == 20
    assert all(row["environment_step_count"] == "0" for row in diagnostic_rows)
    assert all(row["policy_action_executed"] == "False" for row in diagnostic_rows)
    assert all(row["diagnostic_only"] == "True" for row in variant_rows)
    assert all(row["repair_candidate"] == "False" for row in variant_rows)
    assert all(row["promoted"] == "False" for row in variant_rows)
    assert {"seed_fragility", "hidden_dynamics_randomization_fragility", "threshold_strictness_signal"}.issubset(
        classification_keys
    )
    assert (output / "run_state.json").exists()
    assert read_json(output / "diagnostic_env_configs" / "threshold_relaxed.json")["repair_candidate"] is False


def test_r1_reset_sampling_diagnostic_panel_fails_closed_on_missing_r1_targets(tmp_path: Path) -> None:
    m2464_dir = _write_m2464_fixture(tmp_path / "m2464", include_r1=False)

    summary = diagnostic.run_r1_reset_sampling_diagnostic_panel(
        m2464_dir=m2464_dir,
        output_dir=tmp_path / "out",
        eval_seed_base=100,
        reset_seed_count=4,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == diagnostic.RESULT_FAIL
    assert summary["r1_source_target_count"] == 0
    assert summary["diagnostic_attempt_count"] == 0
    assert summary["guardrail_violation_count"] > 0
    assert summary["diagnostic_classification"] == "diagnostic_incomplete"
    assert (Path(summary["output_dir"]) / "run_state.json").exists()
