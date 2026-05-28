"""Run the corrected public controller-profile pilot."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.controller_profile_runtime import profile_runtime_summary, wrap_env_with_profile_mask
from autodrift.corrected_profile_configs import (
    DEFAULT_OUTPUT_DIR,
    EVAL_EPISODES_PER_CHECKPOINT,
    EVAL_SEED_BASE,
    TRAINING_SEED_BASE,
    TRAINING_SEED_OFFSETS,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy, run_episode_with_policy, summarize_rows


DEFAULT_RUN_DIR = Path("runs/m1209_corrected_profile_pilot")
DEFAULT_CONFIG_GLOB = "m1207_*.json"
MAIN_PROFILES = {
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_25",
    "L3_online_gru",
}
SELECTED_FINITE_METRICS = (
    "eval_success_rate",
    "eval_collision_rate",
    "eval_clearance_margin_mean",
    "eval_clearance_margin_p10",
    "eval_return_mean",
    "eval_termination_rate",
    "eval_steps_mean",
)


def corrected_profile_config_paths(
    *,
    config_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config_glob: str = DEFAULT_CONFIG_GLOB,
) -> list[Path]:
    paths = sorted(Path(config_dir).glob(config_glob))
    if not paths:
        raise FileNotFoundError(f"no corrected profile configs found under {config_dir}")
    return paths


def training_seed(base: int, offset: int) -> int:
    return int(base) + int(offset)


def write_seed_config(source_config_path: Path | str, output_path: Path | str, *, seed: int) -> dict[str, Any]:
    config = deepcopy(read_json(source_config_path))
    config.setdefault("ppo", {})["seed"] = int(seed)
    config["ppo"]["eval_episodes"] = 1
    write_json(output_path, config)
    return config


def parameter_count(model: Any) -> int:
    return int(sum(parameter.numel() for parameter in model.parameters()))


def evaluate_checkpoint_with_config(
    *,
    checkpoint_path: Path | str,
    config: dict[str, Any],
    eval_seed_base: int,
    eval_episodes: int,
    device: str = "cpu",
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    env_config = build_env_config(config["env"])
    env = wrap_env_with_profile_mask(AutoDriftEnv(env_config), config)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
    runtime = profile_runtime_summary(config)
    policy = ActorPolicy(
        model,
        env_config,
        reset_hidden_policy=str(runtime["reset_hidden_policy"]),
    )
    rows: list[dict[str, Any]] = []
    for episode_index in range(int(eval_episodes)):
        seed = int(eval_seed_base) + episode_index
        rows.append(run_episode_with_policy(env, policy, "checkpoint", seed))
    env.close()

    summary = dict(summarize_rows(rows))
    margins = [float(row["min_clearance_margin"]) for row in rows]
    summary.update(
        {
            "success_rate": float(np.mean([bool(row["obstacle_completed"]) for row in rows])),
            "collision_rate": float(np.mean([bool(row["collision"]) for row in rows])),
            "clearance_margin_mean": float(np.mean(margins)),
            "clearance_margin_p10": float(np.percentile(margins, 10.0)),
            "control_smoothness": float(np.mean([float(row["action_rate_mean"]) for row in rows])),
            "spin_or_unstable_rate": float(
                np.mean([bool(float(row["high_sideslip_fraction"]) > 0.5) for row in rows])
            ),
        }
    )
    return rows, summary, parameter_count(model)


def seed_row_from_eval(
    *,
    profile_name: str,
    source_config_path: Path,
    config_path: Path,
    run_dir: Path,
    checkpoint_path: Path,
    train_log_path: Path,
    seed_offset: int,
    seed: int,
    returncode: int,
    runtime_seconds: float,
    eval_summary: dict[str, Any] | None,
    eval_runtime_seconds: float | None,
    parameter_count_value: int | None,
    failure: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "profile_name": profile_name,
        "is_main_profile": profile_name in MAIN_PROFILES,
        "seed_offset": int(seed_offset),
        "training_seed": int(seed),
        "source_config_path": str(source_config_path),
        "config_path": str(config_path),
        "run_dir": str(run_dir),
        "checkpoint": str(checkpoint_path),
        "train_log": str(train_log_path),
        "returncode": int(returncode),
        "status": "completed" if returncode == 0 and not failure else "failed",
        "failure": failure,
        "runtime_seconds": float(runtime_seconds),
        "eval_runtime_seconds": float(eval_runtime_seconds or 0.0),
        "parameter_count": int(parameter_count_value or 0),
        "private_holdout_used": False,
        "promoted": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
    }
    if eval_summary:
        row.update(
            {
                "eval_policy": "checkpoint",
                "eval_episodes": int(eval_summary["episodes"]),
                "eval_seed_base": int(eval_summary.get("eval_seed_base", 0)),
                "eval_success_rate": float(eval_summary["success_rate"]),
                "eval_collision_rate": float(eval_summary["collision_rate"]),
                "eval_clearance_margin_mean": float(eval_summary["clearance_margin_mean"]),
                "eval_clearance_margin_p10": float(eval_summary["clearance_margin_p10"]),
                "eval_min_clearance_margin_mean": float(eval_summary["min_clearance_margin_mean"]),
                "eval_min_clearance_margin_min": float(eval_summary["min_clearance_margin_min"]),
                "eval_return_mean": float(eval_summary["return_mean"]),
                "eval_steps_mean": float(eval_summary["steps_mean"]),
                "eval_termination_rate": float(eval_summary["termination_rate"]),
                "eval_lateral_rmse_mean": float(eval_summary["lateral_rmse_mean"]),
                "eval_lateral_peak_mean": float(eval_summary["lateral_peak_mean"]),
                "eval_beta_abs_error_mean": float(eval_summary["beta_abs_error_mean"]),
                "eval_control_smoothness": float(eval_summary["control_smoothness"]),
                "eval_spin_or_unstable_rate": float(eval_summary["spin_or_unstable_rate"]),
                "eval_mu_min": float(eval_summary["mu_min"]),
                "eval_mu_max": float(eval_summary["mu_max"]),
            }
        )
    return row


def finite_selected_metrics(row: dict[str, Any]) -> bool:
    return all(np.isfinite(float(row.get(metric, float("nan")))) for metric in SELECTED_FINITE_METRICS)


def aggregate_profile_rows(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in seed_rows:
        groups[str(row["profile_name"])].append(row)

    aggregate_rows: list[dict[str, Any]] = []
    for profile_name in sorted(groups):
        rows = groups[profile_name]
        completed = [row for row in rows if row["status"] == "completed"]
        aggregate: dict[str, Any] = {
            "profile_name": profile_name,
            "is_main_profile": profile_name in MAIN_PROFILES,
            "seed_runs": len(rows),
            "completed_seed_runs": len(completed),
            "failed_seed_runs": len(rows) - len(completed),
            "private_holdout_used": False,
            "promoted": False,
            "profile_specific_tuning": False,
            "actor_input_contract_changed": False,
        }
        for key in SELECTED_FINITE_METRICS + (
            "eval_min_clearance_margin_min",
            "eval_lateral_rmse_mean",
            "eval_beta_abs_error_mean",
            "eval_control_smoothness",
            "eval_spin_or_unstable_rate",
            "parameter_count",
        ):
            values = [float(row[key]) for row in completed if key in row and np.isfinite(float(row[key]))]
            aggregate[f"{key}_mean"] = float(np.mean(values)) if values else float("nan")
        aggregate["all_selected_metrics_finite"] = bool(completed and all(finite_selected_metrics(row) for row in completed))
        aggregate_rows.append(aggregate)
    return aggregate_rows


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not existing else f"src{os.pathsep}{existing}"
    return env


def run_profile_seed(
    *,
    source_config_path: Path,
    profile_name: str,
    seed_offset: int,
    seed: int,
    run_dir: Path,
    eval_seed_base: int,
    eval_episodes: int,
    device: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profile_run_dir = run_dir / "profile_runs" / profile_name / f"seed_{seed}"
    profile_run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "configs" / f"{profile_name}_seed{seed}.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = write_seed_config(source_config_path, config_path, seed=seed)
    checkpoint_path = profile_run_dir / "checkpoint.pt"
    train_log_path = profile_run_dir / "train.log"
    cmd = [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(config_path),
        "--run-dir",
        str(profile_run_dir),
        "--save",
        str(checkpoint_path),
        "--seed",
        str(seed),
        "--device",
        str(device),
        "--vector-env-mode",
        str(config["ppo"].get("vector_env_mode", "sync")),
        "--eval-episodes",
        "1",
    ]
    start = time.perf_counter()
    with train_log_path.open("w", encoding="utf-8") as log_file:
        completed = subprocess.run(
            cmd,
            cwd=Path.cwd(),
            env=_subprocess_env(),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
        )
    runtime_seconds = time.perf_counter() - start
    if completed.returncode != 0:
        return (
            seed_row_from_eval(
                profile_name=profile_name,
                source_config_path=source_config_path,
                config_path=config_path,
                run_dir=profile_run_dir,
                checkpoint_path=checkpoint_path,
                train_log_path=train_log_path,
                seed_offset=seed_offset,
                seed=seed,
                returncode=completed.returncode,
                runtime_seconds=runtime_seconds,
                eval_summary=None,
                eval_runtime_seconds=None,
                parameter_count_value=None,
                failure="train_ppo_failed",
            ),
            [],
        )

    eval_start = time.perf_counter()
    eval_rows, eval_summary, param_count = evaluate_checkpoint_with_config(
        checkpoint_path=checkpoint_path,
        config=config,
        eval_seed_base=eval_seed_base,
        eval_episodes=eval_episodes,
        device=device,
    )
    eval_runtime_seconds = time.perf_counter() - eval_start
    eval_summary["eval_seed_base"] = int(eval_seed_base)
    for row in eval_rows:
        row.update(
            {
                "profile_name": profile_name,
                "seed_offset": int(seed_offset),
                "training_seed": int(seed),
                "checkpoint": str(checkpoint_path),
                "config_path": str(config_path),
            }
        )
    seed_row = seed_row_from_eval(
        profile_name=profile_name,
        source_config_path=source_config_path,
        config_path=config_path,
        run_dir=profile_run_dir,
        checkpoint_path=checkpoint_path,
        train_log_path=train_log_path,
        seed_offset=seed_offset,
        seed=seed,
        returncode=completed.returncode,
        runtime_seconds=runtime_seconds,
        eval_summary=eval_summary,
        eval_runtime_seconds=eval_runtime_seconds,
        parameter_count_value=param_count,
    )
    seed_row["finite_metrics"] = finite_selected_metrics(seed_row)
    return seed_row, eval_rows


def run_corrected_profile_pilot(
    *,
    config_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config_glob: str = DEFAULT_CONFIG_GLOB,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    training_seed_base: int = TRAINING_SEED_BASE,
    seed_offsets: tuple[int, ...] = TRAINING_SEED_OFFSETS,
    eval_seed_base: int = EVAL_SEED_BASE,
    eval_episodes: int = EVAL_EPISODES_PER_CHECKPOINT,
    device: str = "cpu",
) -> dict[str, Any]:
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    profile_paths = corrected_profile_config_paths(config_dir=config_dir, config_glob=config_glob)
    protocol = {
        "profiles": [read_json(path)["controller_profile"]["name"] for path in profile_paths],
        "main_profiles": sorted(MAIN_PROFILES),
        "training_seed_base": int(training_seed_base),
        "training_seed_offsets": list(seed_offsets),
        "eval_seed_base": int(eval_seed_base),
        "eval_episodes": int(eval_episodes),
        "device": str(device),
        "config_dir": str(config_dir),
        "config_glob": str(config_glob),
        "claim_scope": "public pilot trend only",
    }
    write_json(output / "protocol.json", protocol)

    start = time.perf_counter()
    seed_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    for config_path in profile_paths:
        config = read_json(config_path)
        profile_name = str(config["controller_profile"]["name"])
        for offset in seed_offsets:
            seed = training_seed(training_seed_base, int(offset))
            seed_row, rows = run_profile_seed(
                source_config_path=config_path,
                profile_name=profile_name,
                seed_offset=int(offset),
                seed=seed,
                run_dir=output,
                eval_seed_base=int(eval_seed_base),
                eval_episodes=int(eval_episodes),
                device=device,
            )
            seed_rows.append(seed_row)
            eval_rows.extend(rows)
            write_csv_rows(output / "profile_seed_rows.csv", seed_rows)
            write_csv_rows(output / "eval_rows.csv", eval_rows)

    aggregate_rows = aggregate_profile_rows(seed_rows)
    write_csv_rows(output / "profile_aggregate.csv", aggregate_rows)
    completed_seed_runs = [row for row in seed_rows if row["status"] == "completed"]
    failed_seed_runs = [row for row in seed_rows if row["status"] != "completed"]
    summary = {
        "result_class": "corrected_profile_pilot_completed" if not failed_seed_runs else "corrected_profile_pilot_incomplete",
        "generated_at_utc": utc_timestamp(),
        "runtime_seconds": float(time.perf_counter() - start),
        "profile_count": len(profile_paths),
        "main_profile_count": len([path for path in profile_paths if read_json(path)["controller_profile"]["name"] in MAIN_PROFILES]),
        "diagnostic_profile_count": len(profile_paths)
        - len([path for path in profile_paths if read_json(path)["controller_profile"]["name"] in MAIN_PROFILES]),
        "total_seed_runs": len(seed_rows),
        "completed_seed_runs": len(completed_seed_runs),
        "failed_seed_runs": len(failed_seed_runs),
        "all_selected_profile_seed_runs_complete": not failed_seed_runs,
        "all_eval_metrics_finite": bool(completed_seed_runs and all(finite_selected_metrics(row) for row in completed_seed_runs)),
        "seed_offsets": list(seed_offsets),
        "protocol": protocol,
        "artifacts": {
            "protocol_json": str(output / "protocol.json"),
            "profile_seed_rows_csv": str(output / "profile_seed_rows.csv"),
            "eval_rows_csv": str(output / "eval_rows.csv"),
            "profile_aggregate_csv": str(output / "profile_aggregate.csv"),
        },
        "claim_scope": "public pilot trend only",
        "private_holdout_used": False,
        "promoted": False,
        "candidate_replay_started": False,
        "profile_specific_tuning": False,
        "profile_superiority_claimed": False,
        "self_identification_claimed": False,
        "paper_level_claimed": False,
        "actor_input_contract_changed": False,
    }
    write_json(output / "summary.json", summary)
    return summary


def _parse_seed_offsets(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config-glob", default=DEFAULT_CONFIG_GLOB)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--training-seed-base", type=int, default=TRAINING_SEED_BASE)
    parser.add_argument("--seed-offsets", default=",".join(str(offset) for offset in TRAINING_SEED_OFFSETS))
    parser.add_argument("--eval-seed-base", type=int, default=EVAL_SEED_BASE)
    parser.add_argument("--eval-episodes", type=int, default=EVAL_EPISODES_PER_CHECKPOINT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args(argv)
    summary = run_corrected_profile_pilot(
        config_dir=args.config_dir,
        config_glob=args.config_glob,
        run_dir=args.run_dir,
        training_seed_base=args.training_seed_base,
        seed_offsets=_parse_seed_offsets(args.seed_offsets),
        eval_seed_base=args.eval_seed_base,
        eval_episodes=args.eval_episodes,
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"profile_seed_rows={args.run_dir / 'profile_seed_rows.csv'}")
    print(f"profile_aggregate={args.run_dir / 'profile_aggregate.csv'}")
    print(f"result_class={summary['result_class']}")
    return 0 if summary["failed_seed_runs"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
