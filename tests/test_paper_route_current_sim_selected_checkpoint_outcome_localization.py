from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from autodrift import paper_route_current_sim_selected_checkpoint_outcome_localization as localization
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_training_stability_repair_execution import EXPECTED_PROFILES, EXPECTED_SEED_IDS


def _selected_inputs(tmp_path: Path) -> tuple[Path, Path]:
    selected_rows = []
    config_root = tmp_path / "configs"
    for profile in EXPECTED_PROFILES:
        for seed in EXPECTED_SEED_IDS:
            checkpoint_path = tmp_path / "checkpoints" / profile / f"seed_{seed}" / "checkpoint.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_bytes(b"fake")
            write_json(
                config_root / profile / f"seed_{seed}" / "config.json",
                {
                    "env": {},
                    "controller_profile": {
                        "name": profile,
                        "observation_mask": "none",
                        "previous_command_mask_indices": [],
                        "history_transform": "none",
                        "reset_hidden_policy": "not_applicable",
                    },
                },
            )
            selected_rows.append(
                {
                    "matrix_id": f"{profile}::seed_{seed}",
                    "profile_name": profile,
                    "seed_id": seed,
                    "selected_checkpoint_path": str(checkpoint_path),
                    "selected_checkpoint_step": 8192,
                    "selected_checkpoint_kind": "periodic",
                    "selected_readiness_floor_pass": False,
                }
            )
    selected_path = tmp_path / "selected_checkpoint_rows.csv"
    write_csv_rows(selected_path, selected_rows)
    return selected_path, config_root


def _fake_offtrack_runner(
    checkpoint_path: Path,
    config: Mapping[str, Any],
    selected_row: Mapping[str, Any],
    episode_seed: int,
    device: str,
) -> dict[str, Any]:
    del checkpoint_path, config, selected_row, device
    return {
        "seed": episode_seed,
        "policy": "checkpoint",
        "steps": 60,
        "terminated": True,
        "truncated": False,
        "collision": False,
        "obstacle_completed": False,
        "termination_reason": "off_track",
        "outcome_bucket": "off_track_noncollision_noncompletion",
        "return": 25.0,
        "lateral_rmse": 2.0,
        "lateral_peak": 4.0,
        "beta_abs_error_mean": 0.2,
        "beta_abs_peak": 0.4,
        "high_sideslip_fraction": 0.1,
        "speed_mean": 18.0,
        "action_rate_mean": 0.3,
        "min_clearance_margin": 0.1,
        "max_off_track_overshoot": 1.5,
        "off_track_severity_proxy": 1.0,
        "time_to_first_off_track_s": 1.2,
        "impact_speed_proxy": 0.0,
        "impact_severity_proxy": 0.0,
    }


def test_selected_checkpoint_outcome_localization_routes_offtrack(tmp_path: Path) -> None:
    selected_path, config_root = _selected_inputs(tmp_path)

    summary = localization.run_selected_checkpoint_outcome_localization(
        selected_rows_path=selected_path,
        config_root=config_root,
        output_dir=tmp_path / "out",
        episode_runner=_fake_offtrack_runner,
    )

    assert summary["result_class"] == "current_sim_selected_checkpoint_outcome_localization_pass"
    assert summary["episode_row_count"] == 480
    assert summary["profile_seed_groups_complete"] is True
    assert summary["global_outcome"]["dominant_failure_mode"] == "offtrack_dominated_failure"
    assert summary["primary_repair_route"] == "offtrack_recovery_reward_and_corridor_repair_design"
    assert (tmp_path / "out" / "episode_rows.csv").exists()
    assert (tmp_path / "out" / "repair_route_candidates.csv").exists()


def test_selected_checkpoint_outcome_localization_reports_missing_inputs(tmp_path: Path) -> None:
    selected_path, config_root = _selected_inputs(tmp_path)
    first = localization.read_csv_rows(selected_path)[0]
    Path(first["selected_checkpoint_path"]).unlink()

    summary = localization.run_selected_checkpoint_outcome_localization(
        selected_rows_path=selected_path,
        config_root=config_root,
        output_dir=tmp_path / "out",
        episode_runner=_fake_offtrack_runner,
    )

    assert summary["result_class"] == "current_sim_selected_checkpoint_outcome_localization_fail"
    assert summary["missing_input_count"] == 1
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["episode_row_count"] == 448
