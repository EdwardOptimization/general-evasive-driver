from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_recurrent_profile_checkpoint_quality_audit as audit
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _profile_row(profile: str, *, checkpoint_path: str, training_enabled: bool = True) -> dict[str, object]:
    return {
        "profile_name": profile,
        "profile_level": profile,
        "profile_config_path": f"configs/{profile}.json",
        "actor_encoder": "human_view_online_gru" if profile.startswith("L3") else "temporal_gru",
        "actor_history_length": 1,
        "env_history_length": 1,
        "observation_dim": 72,
        "training_enabled": training_enabled,
        "checkpoint_materialization_mode": "train_frozen_profile_config" if training_enabled else "alias_same_weights_reset_hidden_control",
        "checkpoint_source_profile_name": "L3_online_gru" if not training_enabled else profile,
        "training_started_for_profile": training_enabled,
        "training_command": "train" if training_enabled else "",
        "run_dir": f"profiles/{profile}",
        "checkpoint_path": checkpoint_path,
        "checkpoint_exists": True,
        "training_returncode": 0,
        "stdout_path": "",
        "stderr_path": "",
        "input_contract": "P0_human_view_no_wheel_no_oracle",
        "uses_hidden_oracle_actor_inputs": False,
        "uses_wheel_or_slip_inputs": False,
        "uses_reference_or_ttc_inputs": False,
    }


def _write_profile_metrics(root: Path, profile: str, *, termination_rate: float, return_mean: float) -> None:
    profile_dir = root / "profiles" / profile
    write_csv_rows(
        profile_dir / "train_metrics.csv",
        [
            {
                "step": 1024,
                "update": 8,
                "num_envs": 2,
                "curriculum_stage": "base",
                "rollout_return_mean": return_mean,
                "reward_mean": 0.1,
                "episode_count": 4,
                "episode_length_mean": 42.0,
                "termination_rate": termination_rate,
            }
        ],
    )
    write_json(
        profile_dir / "eval_summary.json",
        {
            "return_mean": return_mean,
            "steps_mean": 64.0,
            "termination_rate": termination_rate,
            "lateral_rmse_mean": 2.0 if termination_rate >= 0.5 else 0.3,
            "beta_abs_error_mean": 0.1,
        },
    )


def _failure_metric(profile: str, *, success_count: int, offtrack_count: int) -> dict[str, object]:
    return {
        "candidate_id": "scene_candidate_000",
        "group_key": "task_family",
        "group_value": "task_family=T1",
        "group_axis": "profile_name",
        "group_name": profile,
        "failure_mode_label": "supported_success" if success_count else "early_offtrack_failure",
        "episode_count": success_count + offtrack_count,
        "success_count": success_count,
        "collision_count": 0,
        "offtrack_count": offtrack_count,
        "success_rate": 0.0,
        "collision_rate": 0.0,
        "offtrack_rate": 1.0,
    }


def test_checkpoint_quality_audit_flags_weak_l3_without_ranking(tmp_path: Path) -> None:
    materialization = tmp_path / "m2171"
    checkpoint_path = str(materialization / "checkpoints" / "L3_online_gru" / "checkpoint.pt")
    write_csv_rows(
        materialization / "profile_checkpoint_rows.csv",
        [
            _profile_row("L3_online_gru", checkpoint_path=checkpoint_path),
            _profile_row("L3_reset_control", checkpoint_path=checkpoint_path, training_enabled=False),
            _profile_row("L2_window_25", checkpoint_path=str(materialization / "checkpoints" / "L2_window_25" / "checkpoint.pt")),
        ],
    )
    _write_profile_metrics(materialization, "L3_online_gru", termination_rate=1.0, return_mean=12.0)
    _write_profile_metrics(materialization, "L2_window_25", termination_rate=0.0, return_mean=90.0)
    failure_metrics = tmp_path / "failure_metrics.csv"
    write_csv_rows(
        failure_metrics,
        [
            _failure_metric("L3_online_gru", success_count=0, offtrack_count=8),
            _failure_metric("L3_reset_control", success_count=0, offtrack_count=8),
            _failure_metric("L2_window_25", success_count=8, offtrack_count=0),
        ],
    )

    result = audit.run_checkpoint_quality_audit(
        checkpoint_materialization_dir=materialization,
        failure_metrics=failure_metrics,
        output_dir=tmp_path / "out",
    )

    assert result["result_class"] == "current_sim_recurrent_profile_checkpoint_quality_audit_pass"
    assert result["l3_online_diagnostic_success_count"] == 0
    assert result["l3_reset_aliases_online_checkpoint"] is True
    assert result["l3_weak_checkpoint_plausible"] is True
    assert result["matched_budget_training_needed"] is True
    assert result["ranking_admissible_count"] == 0
    assert result["winner_selected"] is False
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["finite_window_vs_gru_conclusion_made"] is False
    assert (tmp_path / "out" / "checkpoint_quality_summary.csv").exists()
    assert (tmp_path / "out" / "profile_failure_quality_join.csv").exists()
    quality_rows = audit.read_csv_rows(tmp_path / "out" / "checkpoint_quality_summary.csv")
    reset_row = next(row for row in quality_rows if row["profile_name"] == "L3_reset_control")
    assert reset_row["quality_metric_source_profile_name"] == "L3_online_gru"
    assert reset_row["quality_metric_source_mode"] == "inherited_checkpoint_source_metrics"
