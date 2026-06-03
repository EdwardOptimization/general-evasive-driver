from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    paper_route_current_sim_dual_axis_scenario_quality_concrete_overlay_reset_validation as reset_validation,
)


def _stable_overlay() -> dict[str, Any]:
    return {
        "track_width": 7.5,
        "speed_range": [8.0, 12.0],
        "friction_limited_speed": False,
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": 0.2,
        "obstacle": {
            "enabled": True,
            "distance_range": [34.0, 52.0],
            "lateral_offset_range": [-0.25, 0.25],
            "half_width_range": [0.45, 0.65],
            "allowed_labels": ["aeb_feasible"],
            "require_aeb_infeasible": False,
            "max_sample_attempts": 10000,
            "perception_reveal_step": 0,
            "perception_reveal_distance": 70.0,
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
        },
    }


def _aes_overlay() -> dict[str, Any]:
    return {
        "track_width": 7.5,
        "speed_range": [10.0, 14.0],
        "friction_limited_speed": False,
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": 0.2,
        "obstacle": {
            "enabled": True,
            "distance_range": [20.0, 34.0],
            "lateral_offset_range": [-0.4, 0.4],
            "half_width_range": [0.55, 0.8],
            "allowed_labels": ["aes_feasible"],
            "require_aeb_infeasible": True,
            "max_threshold_score": 0.35,
            "max_sample_attempts": 10000,
            "perception_reveal_step": 0,
            "perception_reveal_distance": 55.0,
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
        },
    }


class _FakeConfig:
    def __init__(self, data: dict[str, Any]):
        self.data = dict(data)


class _FakeScenario:
    def __init__(self, label: str):
        self.label = label


class _FakeEnv:
    def __init__(self, config: _FakeConfig):
        self.config = config
        self.step_count = 0
        self.obstacle_scenario = None

    def reset(self, seed: int):
        if float(self.config.data.get("track_width", 0.0)) == 99.0:
            raise RuntimeError("synthetic reset failure")
        labels = self.config.data.get("obstacle", {}).get("allowed_labels", ["synthetic"])
        label = str(labels[0]) if labels else "synthetic"
        self.obstacle_scenario = _FakeScenario(label)
        return np.full(72, float(seed % 11), dtype=np.float32), {"obstacle_label": label}

    def close(self) -> None:
        pass


def _row_bool(value: bool) -> bool:
    return value


def _write_m2461_dir(tmp_path: Path, *, target_count: int = 6, failing_reset_index: int | None = None) -> Path:
    source = tmp_path / "m2461"
    source.mkdir()
    write_json(
        source / "summary.json",
        {
            "result_class": "scenario_quality_concrete_overlay_materialization_preflight_pass",
            "target_preflight_row_count": 6,
            "concrete_overlay_row_count": 6,
            "adapter_concrete_overlay_available_count": 6,
            "adapter_static_check_fail_count": 0,
            "adapter_reset_attempted_count": 0,
            "guardrail_violation_count": 0,
        },
    )

    overlay_rows = []
    candidate_rows = []
    preflight_rows = []
    reset_check_rows = []
    target_ids = [
        ("stable_1", "stable_feasibility_support", "R0_stable_avoidable", _stable_overlay()),
        ("stable_2", "stable_feasibility_support", "R0_stable_avoidable", _stable_overlay()),
        ("stable_3", "stable_feasibility_support", "R0_stable_avoidable", _stable_overlay()),
        ("aes_1", "stable_aes_support", "R1_aeb_infeasible_stable_aes", _aes_overlay()),
        ("aes_2", "stable_aes_support", "R1_aeb_infeasible_stable_aes", _aes_overlay()),
        ("aes_3", "stable_aes_support", "R1_aeb_infeasible_stable_aes", _aes_overlay()),
    ][:target_count]
    for index, (candidate_id, group, family, overlay) in enumerate(target_ids, start=1):
        if failing_reset_index == index:
            overlay = dict(overlay)
            overlay["track_width"] = 99.0
        overlay_json = json.dumps(overlay, sort_keys=True)
        preflight_id = f"m2458_preflight_{index:03d}"
        overlay_rows.append(
            {
                "overlay_id": f"m2461_overlay_{index:03d}",
                "preflight_id": preflight_id,
                "source_candidate_id": candidate_id,
                "candidate_group": group,
                "overlay_family": family,
                "env_config_overlay_json": overlay_json,
                "allowed_overlay_keys": "|".join(sorted(reset_validation.ALLOWED_OVERLAY_KEYS)),
                "allowed_labels_metadata_only": _row_bool(True),
                "labels_enter_actor_input": _row_bool(False),
                "actor_input_contract_changed": _row_bool(False),
                "scenario_redesign_executed": _row_bool(False),
                "policy_action_executed": _row_bool(False),
                "repair_execution_started": _row_bool(False),
                "training_started": _row_bool(False),
                "ranking_admissible": _row_bool(False),
                "winner_selected": _row_bool(False),
            }
        )
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_group": group,
                "source_panel_id": f"panel_{index}",
                "source_panel_class": "scenario_quality_blocker",
                "source_panel_scope": "stable_or_aes_quality",
                "role_family": family,
                "sampled_obstacle_label": "aeb_feasible" if group == "stable_feasibility_support" else "aes_feasible",
                "hidden_dynamics_bucket": "",
                "obstacle_longitudinal_timing_bucket": "",
                "obstacle_lateral_offset_bucket": "",
                "geometry_lever_class": "test_geometry",
                "boundary_protocol_class": "road_containment_actual_success_required",
                "split": "public_debug",
                "episode_count": 1,
                "actual_success_rate": 0.0,
                "hard_offtrack_rate": 0.0,
                "collision_rate": 0.0,
                "labels_enter_actor_input": _row_bool(False),
                "actor_input_contract_changed": _row_bool(False),
                "scenario_redesign_executed": _row_bool(False),
                "policy_action_executed": _row_bool(False),
                "repair_execution_started": _row_bool(False),
                "training_started": _row_bool(False),
                "ranking_admissible": _row_bool(False),
                "winner_selected": _row_bool(False),
                "reason": "synthetic",
                "env_config_overlay_json": overlay_json,
            }
        )
        preflight_rows.append(
            {
                "preflight_id": preflight_id,
                "source_candidate_id": candidate_id,
                "source_panel_id": f"panel_{index}",
                "candidate_group": group,
                "role_scope": family,
                "sampled_obstacle_label_scope": "aeb_feasible" if group == "stable_feasibility_support" else "aes_feasible",
                "split": "public_debug",
                "preflight_lane": "static_then_reset",
                "intended_evidence_role": "synthetic",
                "geometry_lever_class": "test_geometry",
                "boundary_protocol_class": "road_containment_actual_success_required",
                "static_check_required": _row_bool(True),
                "reset_check_required": _row_bool(True),
                "concrete_overlay_required": _row_bool(True),
                "concrete_overlay_available": _row_bool(True),
                "concrete_overlay_source": "env_config_overlay_json",
                "env_config_overlay_json": overlay_json,
                "blocked_reason": "",
                "labels_enter_actor_input": _row_bool(False),
                "actor_input_contract_changed": _row_bool(False),
                "scenario_redesign_executed": _row_bool(False),
                "policy_action_executed": _row_bool(False),
                "repair_execution_started": _row_bool(False),
                "training_started": _row_bool(False),
                "ranking_admissible": _row_bool(False),
                "winner_selected": _row_bool(False),
            }
        )
        reset_check_rows.append(
            {
                "preflight_id": preflight_id,
                "reset_attempted": _row_bool(False),
                "reset_success": _row_bool(False),
                "observation_shape_unchanged": _row_bool(False),
                "blocked_reason": "reset_execution_not_enabled_in_m2458_adapter",
                "failure_type": "scenario_sampling_failure",
                "reason": "blocked before M2464",
            }
        )

    write_csv_rows(source / "concrete_overlay_rows.csv", overlay_rows)
    write_csv_rows(source / "candidate_rows_with_overlays.csv", candidate_rows)
    write_csv_rows(source / "adapter_preflight_work_items.csv", preflight_rows)
    write_csv_rows(source / "adapter_reset_check_rows.csv", reset_check_rows)
    return source


def test_concrete_overlay_reset_validation_passes_and_stops_after_reset(tmp_path: Path, monkeypatch) -> None:
    source = _write_m2461_dir(tmp_path)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_concrete_overlay_reset_validation(
        m2461_dir=source,
        output_dir=tmp_path / "out",
        target_reset_count=6,
        expected_observation_dim=72,
        eval_seed_base=246400,
    )

    assert summary["result_class"] == reset_validation.RESULT_PASS
    assert summary["target_reset_count"] == 6
    assert summary["static_validation_pass_count"] == 6
    assert summary["effective_env_config_written_count"] == 6
    assert summary["effective_env_config_outside_run_dir_count"] == 0
    assert summary["environment_load_attempt_count"] == 6
    assert summary["environment_reset_attempt_count"] == 6
    assert summary["environment_reset_success_count"] == 6
    assert summary["observation_dimension_failure_count"] == 0
    assert summary["obstacle_initialized_count"] == 6
    assert summary["environment_step_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["guardrail_violation_count"] == 0
    effective = read_json(tmp_path / "out" / "effective_env_configs" / "m2464_reset_target_001.json")
    assert effective["effective_env_config"]["obstacle_relative_velocity_mode"] == "zero"
    assert effective["claim_boundary"]["policy_action_executed"] is False


def test_concrete_overlay_reset_validation_fails_closed_when_target_count_is_not_six(
    tmp_path: Path, monkeypatch
) -> None:
    source = _write_m2461_dir(tmp_path, target_count=5)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_concrete_overlay_reset_validation(
        m2461_dir=source,
        output_dir=tmp_path / "out",
        target_reset_count=6,
        expected_observation_dim=72,
        eval_seed_base=246400,
    )

    assert summary["result_class"] == reset_validation.RESULT_FAIL
    assert summary["target_reset_count"] == 5
    assert summary["environment_reset_attempt_count"] == 0
    assert summary["effective_env_config_written_count"] == 0
    assert summary["guardrail_violation_count"] > 0
    assert "lineage_invalid" in summary["failure_types_observed"]


def test_concrete_overlay_reset_validation_records_reset_failure_without_repair(tmp_path: Path, monkeypatch) -> None:
    source = _write_m2461_dir(tmp_path, failing_reset_index=4)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_concrete_overlay_reset_validation(
        m2461_dir=source,
        output_dir=tmp_path / "out",
        target_reset_count=6,
        expected_observation_dim=72,
        eval_seed_base=246400,
    )

    assert summary["result_class"] == reset_validation.RESULT_FAIL
    assert summary["environment_reset_attempt_count"] == 6
    assert summary["environment_reset_success_count"] == 5
    assert summary["environment_reset_failure_count"] == 1
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert "scenario_sampling_failure" in summary["failure_types_observed"]
    failure_rows = (tmp_path / "out" / "reset_failure_rows.csv").read_text(encoding="utf-8")
    assert "synthetic reset failure" in failure_rows
