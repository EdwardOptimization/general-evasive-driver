from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autodrift import paper_route_current_sim_dual_axis_metric_selected_measured_validation as runner


def _env_config(index: int) -> dict[str, Any]:
    return {
        "track_radius": 12.0 + index,
        "track_width": 2.0,
        "history_length": 1,
        "action_history_mode": "full",
        "include_privileged_params": False,
        "wheel_observation_mode": "none",
        "obstacle_relative_velocity_mode": "zero",
    }


def _spec(index: int) -> dict[str, Any]:
    return {
        "reset_target_index": index,
        "reset_target_key": f"pack|scenario_{index}|orig{index}",
        "env_config_hash": f"orig{index}",
        "pack_id": "pack",
        "pack_index": 0,
        "scenario_spec_id": f"scenario_{index}",
        "scenario_family_id": "family",
        "role_family": "avoidance",
        "sampled_obstacle_label": "obstacle",
        "allowed_labels_metadata_only": "obstacle",
        "same_scene_group_id": f"pack|scenario_{index}",
        "hidden_dynamics_bucket": "bucket",
        "obstacle_longitudinal_timing_bucket": "timing",
        "obstacle_lateral_offset_bucket": "lateral",
        "initial_speed_mps": 12.0,
        "track_radius_m": 12.0 + index,
        "track_width_m": 2.0,
        "family_ids": "f1|f2",
        "family_count": 2,
        "effective_candidate_ids": "c1",
        "effective_candidate_count": 1,
        "scenario_reference_count": 3,
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "actor_contract_guardrail_pass": True,
        "contract_violation_count": 0,
        "labels_enter_actor_input": False,
        "ranking_admissible": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "execution_blocked_by_unsupported_capability": False,
        "scenario_redesign_executed_claim_made": False,
        "env_config": _env_config(index),
    }


def _selected(index: int) -> dict[str, Any]:
    return {
        "matrix_id": f"profile::seed_{index}",
        "profile_name": "profile",
        "seed_id": str(index),
        "selected_checkpoint_path": f"checkpoint_{index}.pt",
        "selected_checkpoint_step": "1",
        "selected_checkpoint_kind": "test",
        "selected_readiness_floor_pass": True,
    }


def _config_root(tmp_path: Path, selected_rows: list[dict[str, Any]]) -> Path:
    root = tmp_path / "configs"
    for row in selected_rows:
        path = root / str(row["profile_name"]) / f"seed_{int(row['seed_id'])}" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"env": {"history_length": 1}}), encoding="utf-8")
    return root


def _preflight_workload(specs: list[dict[str, Any]], selected_rows: list[dict[str, Any]], config_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metric_specs = runner.metric_selected_reset_target_specs(
        specs,
        soft_offtrack_tolerance_m=0.20,
    )
    for selected_index, selected in enumerate(selected_rows):
        for spec, metric_spec in zip(specs, metric_specs, strict=True):
            reset_index = int(spec["reset_target_index"])
            rows.append(
                {
                    "workload_id": f"{selected['matrix_id']}::{metric_spec['metric_selected_reset_target_key']}",
                    "selected_checkpoint_index": selected_index,
                    "reset_target_index": reset_index,
                    "eval_seed": 244300 + selected_index * 100000 + reset_index,
                    "selected_key": selected["matrix_id"],
                    "profile_config_path": str(
                        config_root / selected["profile_name"] / f"seed_{int(selected['seed_id'])}" / "config.json"
                    ),
                    "original_reset_target_key": spec["reset_target_key"],
                    "metric_selected_reset_target_key": metric_spec["metric_selected_reset_target_key"],
                    "original_env_config_hash": spec["env_config_hash"],
                    "metric_selected_env_config_hash": metric_spec["metric_selected_env_config_hash"],
                    "pack_id": spec["pack_id"],
                    "scenario_spec_id": spec["scenario_spec_id"],
                    "family_ids": spec["family_ids"],
                    "family_count": spec["family_count"],
                    "effective_candidate_ids": spec["effective_candidate_ids"],
                    "effective_candidate_count": spec["effective_candidate_count"],
                    "scenario_reference_count": spec["scenario_reference_count"],
                    "soft_offtrack_metric_enabled": True,
                    "soft_offtrack_tolerance_m": 0.20,
                    "sensitivity_thresholds_m": "0.02|0.05|0.10|0.20",
                }
            )
    return rows


def _rollout(_workload_row: dict[str, Any], _spec: dict[str, Any], _seed: int) -> dict[str, Any]:
    return {
        "policy": "checkpoint",
        "seed": _seed,
        "steps": 10,
        "terminated": True,
        "truncated": False,
        "obstacle_label": "obstacle",
        "collision": False,
        "obstacle_completed": True,
        "min_clearance_margin": 0.5,
        "termination_reason": "",
        "obstacle_passed_raw": True,
        "completion_reason": "obstacle_completed",
        "outcome_bucket": "success_obstacle_pass",
        "return": 1.0,
        "action_rate_mean": 0.01,
        "high_sideslip_fraction": 0.0,
        "max_off_track_overshoot": 0.10,
        "time_to_first_off_track_s": 1.0,
    }


def test_metric_selected_measured_validation_runs_injected_rollouts(tmp_path: Path) -> None:
    specs = [_spec(0), _spec(1)]
    selected_rows = [_selected(0), _selected(1)]
    config_root = _config_root(tmp_path, selected_rows)

    summary = runner.run_metric_selected_measured_validation(
        reset_target_specs=specs,
        selected_rows=selected_rows,
        preflight_workload_rows=_preflight_workload(specs, selected_rows, config_root),
        config_root=config_root,
        output_dir=tmp_path / "out",
        target_reset_target_count=2,
        target_selected_checkpoint_count=2,
        target_episode_count=4,
        rollout_fn=_rollout,
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["episode_count"] == 4
    assert summary["failure_count"] == 0
    assert summary["validation_failure_count"] == 0
    assert summary["metric_selected_actual_success_count"] == 4
    assert summary["metric_selected_soft_offtrack_violation_count"] == 4
    assert summary["metric_selected_hard_offtrack_failure_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "episode_rows.csv").exists()
    assert (tmp_path / "out" / "decision_rows.csv").exists()


def test_metric_selected_measured_validation_fails_closed_on_validation_gap(tmp_path: Path) -> None:
    specs = [_spec(0)]
    selected_rows = [_selected(0)]
    config_root = _config_root(tmp_path, selected_rows)
    selected_rows[0]["selected_readiness_floor_pass"] = ""

    summary = runner.run_metric_selected_measured_validation(
        reset_target_specs=specs,
        selected_rows=selected_rows,
        preflight_workload_rows=_preflight_workload(specs, selected_rows, config_root),
        config_root=config_root,
        output_dir=tmp_path / "out",
        target_reset_target_count=1,
        target_selected_checkpoint_count=1,
        target_episode_count=1,
        rollout_fn=_rollout,
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["episode_count"] == 0
    assert summary["validation_failure_count"] > 0
