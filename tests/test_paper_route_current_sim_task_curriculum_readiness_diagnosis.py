from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_task_curriculum_readiness_diagnosis as diagnosis
from autodrift.artifacts import read_json, write_csv_rows


def _run_row(
    *,
    root: Path,
    profile: str,
    seed: int,
    ret: float,
    termination: float,
    floor_pass: bool,
) -> dict[str, object]:
    run_dir = root / "profiles" / profile / f"seed_{seed}"
    return {
        "matrix_id": f"{profile}::seed_{seed}",
        "profile_name": profile,
        "seed_id": seed,
        "status": "completed",
        "failure": "",
        "returncode": 0,
        "runtime_seconds": 1.0,
        "config_path": "config.json",
        "run_dir": str(run_dir),
        "checkpoint_path": str(root / "checkpoints" / profile / f"seed_{seed}" / "checkpoint.pt"),
        "train_log_path": str(run_dir / "train.log"),
        "eval_summary_path": str(run_dir / "eval_summary.json"),
        "command": "python -m autodrift.train_ppo",
        "checkpoint_exists": True,
        "eval_summary_exists": True,
        "selected_metrics_finite": True,
        "readiness_floor_pass": floor_pass,
        "eval_return_mean": ret,
        "eval_termination_rate": termination,
        "eval_steps_mean": 64.0,
        "eval_lateral_rmse_mean": 1.0,
        "eval_beta_abs_error_mean": 0.1,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _train_metrics(path: Path, *, best: float, final: float, best_term: float, final_term: float) -> None:
    write_csv_rows(
        path,
        [
            {
                "step": 512,
                "update": 1,
                "num_envs": 4,
                "curriculum_stage": "base",
                "rollout_return_mean": best,
                "reward_mean": 0.0,
                "episode_count": 4,
                "episode_length_mean": 50.0,
                "termination_rate": best_term,
            },
            {
                "step": 1024,
                "update": 2,
                "num_envs": 4,
                "curriculum_stage": "base",
                "rollout_return_mean": final,
                "reward_mean": 0.0,
                "episode_count": 4,
                "episode_length_mean": 40.0,
                "termination_rate": final_term,
            },
        ],
    )


def _materialize_budget(root: Path, rows: list[dict[str, object]]) -> None:
    write_csv_rows(root / "run_rows.csv", rows)
    for row in rows:
        _train_metrics(
            Path(str(row["run_dir"])) / "train_metrics.csv",
            best=70.0,
            final=45.0,
            best_term=0.1,
            final_term=0.45,
        )


def test_readiness_diagnosis_classifies_late_regression_route(tmp_path: Path) -> None:
    short_root = tmp_path / "short"
    medium_root = tmp_path / "medium"
    profiles = ("L0_current_masked", "L3_online_gru")
    seeds = (1, 2)
    short_rows = []
    medium_rows = []
    for profile in profiles:
        for seed in seeds:
            short_rows.append(
                _run_row(root=short_root, profile=profile, seed=seed, ret=35.0, termination=0.8, floor_pass=False)
            )
            medium_rows.append(
                _run_row(root=medium_root, profile=profile, seed=seed, ret=48.0, termination=0.45, floor_pass=False)
            )
    _materialize_budget(short_root, short_rows)
    _materialize_budget(medium_root, medium_rows)

    summary = diagnosis.run_readiness_diagnosis(
        short_run_dir=short_root,
        medium_run_dir=medium_root,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_task_curriculum_readiness_diagnosis_pass"
    assert summary["route_classification"]["primary"] == "training_plateau_or_late_regression"
    assert summary["guardrail"]["training_started"] is False
    assert summary["guardrail"]["ranking_admissible"] is False
    assert (tmp_path / "out" / "row_diagnosis.csv").exists()
    assert (tmp_path / "out" / "seed_diagnosis.csv").exists()
    assert (tmp_path / "out" / "budget_delta.csv").exists()
    assert (tmp_path / "out" / "training_plateau.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["guardrail"]["finite_window_vs_gru_conclusion_made"] is False


def test_readiness_diagnosis_reports_missing_artifacts(tmp_path: Path) -> None:
    short_root = tmp_path / "short"
    medium_root = tmp_path / "medium"
    write_csv_rows(
        short_root / "run_rows.csv",
        [
            _run_row(
                root=short_root,
                profile="L0_current_masked",
                seed=1,
                ret=55.0,
                termination=0.2,
                floor_pass=True,
            )
        ],
    )

    summary = diagnosis.run_readiness_diagnosis(
        short_run_dir=short_root,
        medium_run_dir=medium_root,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == "current_sim_task_curriculum_readiness_diagnosis_artifact_gap"
    assert summary["route_classification"]["primary"] == "insufficient_existing_artifacts"
    assert summary["missing_artifact_count"] >= 1
