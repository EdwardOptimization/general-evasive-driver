"""Execute same-budget training-stability repair with candidate checkpoints."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.controller_profile_runtime import mask_spec_from_config
from autodrift.paper_route_current_sim_matched_budget_profile_training_execution import (
    EXPECTED_PROFILES,
    EXPECTED_SEED_IDS,
    RUN_ROW_FIELDNAMES,
    SELECTED_METRICS,
    _as_float,
    _config_contract_violation,
    _finite_selected_metrics,
    _readiness_floor,
)
from autodrift.train_ppo import evaluate_actor


DEFAULT_MEDIUM_MATRIX = Path("runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/training_matrix.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2241_paper_route_current_sim_training_stability_repair_execution")
DEFAULT_TASK_ID = "m2241-paper-route-current-sim-training-stability-repair-execution"
DEFAULT_NEXT_BLOCKER = "m2242-paper-route-current-sim-training-stability-repair-result-audit"
EXPECTED_TOTAL_STEPS = 32768
CHECKPOINT_INTERVAL_STEPS = 4096
CANDIDATE_STEPS = tuple(range(CHECKPOINT_INTERVAL_STEPS, EXPECTED_TOTAL_STEPS + 1, CHECKPOINT_INTERVAL_STEPS))
EXPECTED_CANDIDATE_COUNT = len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS) * len(CANDIDATE_STEPS)

COMMAND_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "source_config_path",
    "repair_config_path",
    "run_dir",
    "checkpoint_path",
    "command",
]

CANDIDATE_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "candidate_step",
    "candidate_kind",
    "candidate_path",
    "candidate_exists",
    "selected_metrics_finite",
    "readiness_floor_pass",
    "eval_return_mean",
    "eval_termination_rate",
    "eval_steps_mean",
    "eval_lateral_rmse_mean",
    "eval_beta_abs_error_mean",
    "selection_rank",
    "selected_checkpoint",
    "selected_beats_final",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

SELECTED_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "selected_checkpoint_path",
    "selected_checkpoint_step",
    "selected_checkpoint_kind",
    "selected_readiness_floor_pass",
    "selected_eval_return_mean",
    "selected_eval_termination_rate",
    "selected_eval_steps_mean",
    "selected_eval_lateral_rmse_mean",
    "selected_eval_beta_abs_error_mean",
    "final_readiness_floor_pass",
    "final_eval_return_mean",
    "final_eval_termination_rate",
    "selected_beats_final",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

AGGREGATE_FIELDNAMES = [
    "profile_name",
    "seed_runs",
    "completed_run_count",
    "failed_run_count",
    "selected_passing_seed_count",
    "selected_readiness_floor_pass",
    "final_passing_seed_count",
    "final_readiness_floor_pass",
    "selected_eval_return_mean_mean",
    "selected_eval_termination_rate_mean",
    "final_eval_return_mean_mean",
    "final_eval_termination_rate_mean",
    "selected_beats_final_count",
    "all_selected_metrics_finite",
    "ranking_admissible",
    "winner_selected",
]

CommandRunner = Callable[[Sequence[str], Path, Mapping[str, str], Any], int]
CandidateEvaluator = Callable[[Path, Mapping[str, Any], int, int, str], dict[str, float]]


def _read_csv(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not existing else f"src{os.pathsep}{existing}"
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    return env


def _default_runner(cmd: Sequence[str], cwd: Path, env: Mapping[str, str], stdout: Any) -> int:
    completed = subprocess.run(cmd, cwd=cwd, env=dict(env), stdout=stdout, stderr=subprocess.STDOUT, check=False)
    return int(completed.returncode)


def _default_candidate_evaluator(
    checkpoint_path: Path,
    config: Mapping[str, Any],
    seed_id: int,
    eval_episodes: int,
    device: str,
) -> dict[str, float]:
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=device)
    env_config = build_env_config(config.get("env", {}))
    mask_spec = mask_spec_from_config(dict(config)) if "controller_profile" in config else None
    return evaluate_actor(
        model,
        episodes=int(eval_episodes),
        seed=int(seed_id) + 10_000,
        env_config=env_config,
        observation_mask_spec=mask_spec,
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _load_training_matrix(path: Path | str) -> list[dict[str, str]]:
    rows = _read_csv(path)
    return sorted(rows, key=lambda row: (str(row["profile_name"]), int(row["seed_id"])))


def _write_repair_config(source_config: Path, output_config: Path) -> dict[str, Any]:
    config = read_json(source_config)
    ppo = dict(config.get("ppo", {}))
    ppo["total_steps"] = EXPECTED_TOTAL_STEPS
    ppo["checkpoint_interval_steps"] = CHECKPOINT_INTERVAL_STEPS
    config["ppo"] = ppo
    output_config.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_config, config)
    return config


def _validate_matrix(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    profile_names = tuple(sorted({str(row.get("profile_name", "")) for row in rows}))
    seed_ids = tuple(sorted({int(row.get("seed_id", -1)) for row in rows}))
    validation = {
        "expected_run_count": len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS),
        "matrix_row_count": len(rows),
        "profile_names": list(profile_names),
        "seed_ids": list(seed_ids),
        "profile_set_matched": profile_names == EXPECTED_PROFILES,
        "seed_set_matched": seed_ids == EXPECTED_SEED_IDS,
        "missing_config_count": 0,
        "source_contract_violation_count": 0,
        "source_budget_violation_count": 0,
    }
    for row in rows:
        source_config = Path(str(row.get("generated_config_path", "")))
        if not source_config.exists():
            validation["missing_config_count"] += 1
            continue
        config = read_json(source_config)
        ppo = config.get("ppo", {})
        if int(ppo.get("total_steps", -1)) != EXPECTED_TOTAL_STEPS:
            validation["source_budget_violation_count"] += 1
        if _config_contract_violation(config):
            validation["source_contract_violation_count"] += 1
    validation["validation_pass"] = bool(
        validation["matrix_row_count"] == validation["expected_run_count"]
        and validation["profile_set_matched"]
        and validation["seed_set_matched"]
        and validation["missing_config_count"] == 0
        and validation["source_contract_violation_count"] == 0
        and validation["source_budget_violation_count"] == 0
    )
    return validation


def build_repair_plan(
    *,
    training_matrix: Path | str,
    output_dir: Path | str,
    execution_root: Path | str,
    device: str = "cpu",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _load_training_matrix(training_matrix)
    validation = _validate_matrix(rows)
    output = Path(output_dir)
    execution = Path(execution_root)
    plan_rows: list[dict[str, Any]] = []
    for row in rows:
        profile_name = str(row["profile_name"])
        seed_id = int(row["seed_id"])
        source_config = Path(row["generated_config_path"])
        repair_config = output / "configs" / profile_name / f"seed_{seed_id}" / "config.json"
        if source_config.exists():
            _write_repair_config(source_config, repair_config)
        run_dir = execution / "profiles" / profile_name / f"seed_{seed_id}"
        checkpoint_path = execution / "checkpoints" / profile_name / f"seed_{seed_id}" / "checkpoint.pt"
        cmd = [
            sys.executable,
            "-m",
            "autodrift.train_ppo",
            "--config",
            str(repair_config),
            "--run-dir",
            str(run_dir),
            "--save",
            str(checkpoint_path),
            "--seed",
            str(seed_id),
            "--device",
            str(device),
            "--vector-env-mode",
            "sync",
        ]
        plan_rows.append(
            {
                "matrix_id": row["matrix_id"],
                "profile_name": profile_name,
                "seed_id": seed_id,
                "source_config_path": str(source_config),
                "repair_config_path": str(repair_config),
                "run_dir": str(run_dir),
                "checkpoint_path": str(checkpoint_path),
                "command": " ".join(cmd),
                "cmd": cmd,
            }
        )
    return plan_rows, validation


def _candidate_path(checkpoint_path: Path, step: int) -> tuple[str, Path]:
    if int(step) == EXPECTED_TOTAL_STEPS:
        return "final", checkpoint_path
    return "periodic", checkpoint_path.parent / "checkpoints" / f"checkpoint_step_{int(step)}.pt"


def _candidate_merit(row: Mapping[str, Any]) -> tuple[int, float, float, float, int]:
    finite = _bool(row.get("selected_metrics_finite"))
    if not finite:
        return (1, float("inf"), float("inf"), float("inf"), int(row.get("candidate_step", EXPECTED_TOTAL_STEPS)))
    return (
        0 if _bool(row.get("readiness_floor_pass")) else 1,
        _as_float(row.get("eval_termination_rate")),
        -_as_float(row.get("eval_return_mean")),
        _as_float(row.get("eval_lateral_rmse_mean")),
        int(row.get("candidate_step", EXPECTED_TOTAL_STEPS)),
    )


def _evaluate_candidates_for_run(
    *,
    plan: Mapping[str, Any],
    evaluator: CandidateEvaluator,
    device: str,
) -> list[dict[str, Any]]:
    config = read_json(plan["repair_config_path"])
    eval_episodes = int(config.get("ppo", {}).get("eval_episodes", 32))
    checkpoint_path = Path(str(plan["checkpoint_path"]))
    rows: list[dict[str, Any]] = []
    for step in CANDIDATE_STEPS:
        kind, path = _candidate_path(checkpoint_path, int(step))
        candidate_exists = path.exists()
        metrics: dict[str, float] = {}
        if candidate_exists:
            metrics = evaluator(path, config, int(plan["seed_id"]), eval_episodes, device)
        selected_metrics_finite = bool(metrics and _finite_selected_metrics(metrics))
        rows.append(
            {
                "matrix_id": plan["matrix_id"],
                "profile_name": plan["profile_name"],
                "seed_id": int(plan["seed_id"]),
                "candidate_step": int(step),
                "candidate_kind": kind,
                "candidate_path": str(path),
                "candidate_exists": candidate_exists,
                "selected_metrics_finite": selected_metrics_finite,
                "readiness_floor_pass": bool(metrics and _readiness_floor(metrics)),
                "eval_return_mean": metrics.get("return_mean", ""),
                "eval_termination_rate": metrics.get("termination_rate", ""),
                "eval_steps_mean": metrics.get("steps_mean", ""),
                "eval_lateral_rmse_mean": metrics.get("lateral_rmse_mean", ""),
                "eval_beta_abs_error_mean": metrics.get("beta_abs_error_mean", ""),
                "selection_rank": "",
                "selected_checkpoint": False,
                "selected_beats_final": False,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    ranked = sorted(range(len(rows)), key=lambda index: _candidate_merit(rows[index]))
    final_row = next(row for row in rows if int(row["candidate_step"]) == EXPECTED_TOTAL_STEPS)
    selected_index = ranked[0] if ranked else len(rows) - 1
    selected_row = rows[selected_index]
    for rank, index in enumerate(ranked, start=1):
        rows[index]["selection_rank"] = rank
    selected_beats_final = _candidate_merit(selected_row) < _candidate_merit(final_row)
    rows[selected_index]["selected_checkpoint"] = True
    rows[selected_index]["selected_beats_final"] = selected_beats_final
    return rows


def _run_training_plan(
    *,
    plan_rows: Sequence[Mapping[str, Any]],
    command_runner: CommandRunner,
    fail_fast: bool,
) -> list[dict[str, Any]]:
    env = _subprocess_env()
    run_rows: list[dict[str, Any]] = []
    for plan in plan_rows:
        run_dir = Path(str(plan["run_dir"]))
        checkpoint_path = Path(str(plan["checkpoint_path"]))
        eval_summary_path = run_dir / "eval_summary.json"
        train_log_path = run_dir / "train.log"
        run_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()
        with train_log_path.open("w", encoding="utf-8") as log_file:
            returncode = int(command_runner(plan["cmd"], Path.cwd(), env, log_file))
        runtime_seconds = time.perf_counter() - start
        failure = ""
        if returncode != 0:
            failure = "train_ppo_failed"
        checkpoint_exists = checkpoint_path.exists()
        eval_summary_exists = eval_summary_path.exists()
        if not failure and not checkpoint_exists:
            failure = "checkpoint_missing"
        if not failure and not eval_summary_exists:
            failure = "eval_summary_missing"
        eval_summary: dict[str, Any] = {}
        if eval_summary_exists:
            eval_summary = read_json(eval_summary_path)
        selected_metrics_finite = bool(eval_summary and _finite_selected_metrics(eval_summary))
        if not failure and not selected_metrics_finite:
            failure = "nonfinite_eval_metrics"
        run_rows.append(
            {
                "matrix_id": plan["matrix_id"],
                "profile_name": plan["profile_name"],
                "seed_id": int(plan["seed_id"]),
                "status": "completed" if not failure else "failed",
                "failure": failure,
                "returncode": returncode,
                "runtime_seconds": runtime_seconds,
                "config_path": plan["repair_config_path"],
                "run_dir": plan["run_dir"],
                "checkpoint_path": plan["checkpoint_path"],
                "train_log_path": str(train_log_path),
                "eval_summary_path": str(eval_summary_path),
                "command": plan["command"],
                "checkpoint_exists": checkpoint_exists,
                "eval_summary_exists": eval_summary_exists,
                "selected_metrics_finite": selected_metrics_finite,
                "readiness_floor_pass": bool(eval_summary and _readiness_floor(eval_summary)),
                "eval_return_mean": eval_summary.get("return_mean", ""),
                "eval_termination_rate": eval_summary.get("termination_rate", ""),
                "eval_steps_mean": eval_summary.get("steps_mean", ""),
                "eval_lateral_rmse_mean": eval_summary.get("lateral_rmse_mean", ""),
                "eval_beta_abs_error_mean": eval_summary.get("beta_abs_error_mean", ""),
                "private_holdout_used": False,
                "profile_specific_tuning": False,
                "winner_selected": False,
                "controller_family_ranking_claim_made": False,
                "finite_window_vs_gru_conclusion_made": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
        if failure and fail_fast:
            break
    return run_rows


def _selected_rows(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_key[(str(row["profile_name"]), int(row["seed_id"]))].append(row)
    selected: list[dict[str, Any]] = []
    for (profile_name, seed_id), rows in sorted(by_key.items()):
        selected_row = next(row for row in rows if _bool(row.get("selected_checkpoint")))
        final_row = next(row for row in rows if int(row.get("candidate_step", -1)) == EXPECTED_TOTAL_STEPS)
        selected.append(
            {
                "matrix_id": selected_row["matrix_id"],
                "profile_name": profile_name,
                "seed_id": seed_id,
                "selected_checkpoint_path": selected_row["candidate_path"],
                "selected_checkpoint_step": int(selected_row["candidate_step"]),
                "selected_checkpoint_kind": selected_row["candidate_kind"],
                "selected_readiness_floor_pass": _bool(selected_row["readiness_floor_pass"]),
                "selected_eval_return_mean": selected_row["eval_return_mean"],
                "selected_eval_termination_rate": selected_row["eval_termination_rate"],
                "selected_eval_steps_mean": selected_row["eval_steps_mean"],
                "selected_eval_lateral_rmse_mean": selected_row["eval_lateral_rmse_mean"],
                "selected_eval_beta_abs_error_mean": selected_row["eval_beta_abs_error_mean"],
                "final_readiness_floor_pass": _bool(final_row["readiness_floor_pass"]),
                "final_eval_return_mean": final_row["eval_return_mean"],
                "final_eval_termination_rate": final_row["eval_termination_rate"],
                "selected_beats_final": _bool(selected_row["selected_beats_final"]),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return selected


def _aggregate_profiles(
    selected_rows: Sequence[Mapping[str, Any]],
    run_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    run_by_profile: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    selected_by_profile: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in run_rows:
        run_by_profile[str(row["profile_name"])].append(row)
    for row in selected_rows:
        selected_by_profile[str(row["profile_name"])].append(row)
    aggregates: list[dict[str, Any]] = []
    for profile_name in EXPECTED_PROFILES:
        runs = run_by_profile.get(profile_name, [])
        selected = selected_by_profile.get(profile_name, [])
        completed = [row for row in runs if str(row.get("status")) == "completed"]
        selected_passing = [row for row in selected if _bool(row.get("selected_readiness_floor_pass"))]
        final_passing = [row for row in selected if _bool(row.get("final_readiness_floor_pass"))]
        selected_returns = [_as_float(row.get("selected_eval_return_mean")) for row in selected]
        selected_terms = [_as_float(row.get("selected_eval_termination_rate")) for row in selected]
        final_returns = [_as_float(row.get("final_eval_return_mean")) for row in selected]
        final_terms = [_as_float(row.get("final_eval_termination_rate")) for row in selected]
        aggregates.append(
            {
                "profile_name": profile_name,
                "seed_runs": len(runs),
                "completed_run_count": len(completed),
                "failed_run_count": len(runs) - len(completed),
                "selected_passing_seed_count": len(selected_passing),
                "selected_readiness_floor_pass": len(selected_passing) >= 2,
                "final_passing_seed_count": len(final_passing),
                "final_readiness_floor_pass": len(final_passing) >= 2,
                "selected_eval_return_mean_mean": float(np.mean(selected_returns)) if selected_returns else float("nan"),
                "selected_eval_termination_rate_mean": float(np.mean(selected_terms)) if selected_terms else float("nan"),
                "final_eval_return_mean_mean": float(np.mean(final_returns)) if final_returns else float("nan"),
                "final_eval_termination_rate_mean": float(np.mean(final_terms)) if final_terms else float("nan"),
                "selected_beats_final_count": sum(1 for row in selected if _bool(row.get("selected_beats_final"))),
                "all_selected_metrics_finite": bool(
                    selected and all(np.isfinite(_as_float(row.get("selected_eval_return_mean"))) for row in selected)
                ),
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return aggregates


def execute_training_stability_repair(
    *,
    training_matrix: Path | str = DEFAULT_MEDIUM_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    execution_root: Path | str | None = None,
    device: str = "cpu",
    fail_fast: bool = True,
    command_runner: CommandRunner = _default_runner,
    candidate_evaluator: CandidateEvaluator = _default_candidate_evaluator,
    task_id: str = DEFAULT_TASK_ID,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    execution = Path(execution_root) if execution_root is not None else output
    plan_rows, validation = build_repair_plan(
        training_matrix=training_matrix,
        output_dir=output,
        execution_root=execution,
        device=device,
    )
    write_csv_rows(output / "command_matrix.csv", [{key: row[key] for key in COMMAND_FIELDNAMES} for row in plan_rows])

    start = time.perf_counter()
    if validation["validation_pass"]:
        run_rows = _run_training_plan(plan_rows=plan_rows, command_runner=command_runner, fail_fast=fail_fast)
    else:
        run_rows = []
    candidate_rows: list[dict[str, Any]] = []
    if run_rows and all(str(row.get("status")) == "completed" for row in run_rows):
        plan_by_key = {(str(row["profile_name"]), int(row["seed_id"])): row for row in plan_rows}
        for run_row in run_rows:
            plan = plan_by_key[(str(run_row["profile_name"]), int(run_row["seed_id"]))]
            candidate_rows.extend(_evaluate_candidates_for_run(plan=plan, evaluator=candidate_evaluator, device=device))
    selected_rows = _selected_rows(candidate_rows) if candidate_rows else []
    aggregate_rows = _aggregate_profiles(selected_rows, run_rows)
    runtime_seconds = time.perf_counter() - start

    write_csv_rows(output / "run_rows.csv", run_rows, fieldnames=RUN_ROW_FIELDNAMES)
    write_csv_rows(output / "candidate_eval_rows.csv", candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "selected_checkpoint_rows.csv", selected_rows, fieldnames=SELECTED_FIELDNAMES)
    write_csv_rows(output / "profile_aggregate.csv", aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)

    completed_run_count = sum(1 for row in run_rows if str(row.get("status")) == "completed")
    failed_run_count = len(run_rows) - completed_run_count
    all_run_metrics_finite = bool(run_rows and all(_bool(row.get("selected_metrics_finite")) for row in run_rows))
    all_candidate_metrics_finite = bool(
        candidate_rows and all(_bool(row.get("selected_metrics_finite")) for row in candidate_rows)
    )
    all_selected_metrics_finite = bool(
        selected_rows and all(np.isfinite(_as_float(row.get("selected_eval_return_mean"))) for row in selected_rows)
    )
    selected_checkpoint_profile_floor_pass_count = sum(
        1 for row in aggregate_rows if _bool(row.get("selected_readiness_floor_pass"))
    )
    final_checkpoint_profile_floor_pass_count = sum(
        1 for row in aggregate_rows if _bool(row.get("final_readiness_floor_pass"))
    )
    selected_beats_final_count = sum(1 for row in selected_rows if _bool(row.get("selected_beats_final")))
    guardrail_flags = {
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "actor_input_contract_changed": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_training_stability_repair_execution_pass"
        if (
            validation["validation_pass"]
            and completed_run_count == validation["expected_run_count"]
            and failed_run_count == 0
            and len(candidate_rows) == EXPECTED_CANDIDATE_COUNT
            and len(selected_rows) == validation["expected_run_count"]
            and all_run_metrics_finite
            and all_candidate_metrics_finite
            and all_selected_metrics_finite
            and guardrail_violation_count == 0
        )
        else "current_sim_training_stability_repair_execution_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "runtime_seconds": runtime_seconds,
        "training_matrix": str(training_matrix),
        "output_dir": str(output),
        "execution_root": str(execution),
        "device": str(device),
        "fail_fast": bool(fail_fast),
        "expected_total_steps": EXPECTED_TOTAL_STEPS,
        "checkpoint_interval_steps": CHECKPOINT_INTERVAL_STEPS,
        "candidate_steps": list(CANDIDATE_STEPS),
        "expected_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "candidate_eval_count": len(candidate_rows),
        "selected_checkpoint_count": len(selected_rows),
        "completed_run_count": completed_run_count,
        "failed_run_count": failed_run_count,
        "all_run_metrics_finite": all_run_metrics_finite,
        "all_candidate_metrics_finite": all_candidate_metrics_finite,
        "all_selected_metrics_finite": all_selected_metrics_finite,
        "final_checkpoint_profile_floor_pass_count": final_checkpoint_profile_floor_pass_count,
        "selected_checkpoint_profile_floor_pass_count": selected_checkpoint_profile_floor_pass_count,
        "selected_beats_final_count": selected_beats_final_count,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "private_holdout_used": False,
        "training_started": bool(validation["validation_pass"]),
        "ppo_started": bool(validation["validation_pass"]),
        "environment_rollout_started": bool(validation["validation_pass"]),
        "measured_rollout_started": False,
        "policy_action_executed": bool(validation["validation_pass"]),
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        **validation,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "command_matrix": str(output / "command_matrix.csv"),
            "run_rows": str(output / "run_rows.csv"),
            "candidate_eval_rows": str(output / "candidate_eval_rows.csv"),
            "selected_checkpoint_rows": str(output / "selected_checkpoint_rows.csv"),
            "profile_aggregate": str(output / "profile_aggregate.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": str(task_id),
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-matrix", type=Path, default=DEFAULT_MEDIUM_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--execution-root", type=Path, default=None)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--no-fail-fast", dest="fail_fast", action="store_false")
    parser.set_defaults(fail_fast=True)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = execute_training_stability_repair(
        training_matrix=args.training_matrix,
        output_dir=args.output_dir,
        execution_root=args.execution_root,
        device=str(args.device),
        fail_fast=bool(args.fail_fast),
        task_id=str(args.task_id),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"candidate_eval_rows={Path(args.output_dir) / 'candidate_eval_rows.csv'}")
    print(f"selected_checkpoint_rows={Path(args.output_dir) / 'selected_checkpoint_rows.csv'}")
    print(f"result_class={summary['result_class']}")
    print(f"completed_run_count={summary['completed_run_count']}")
    print(f"candidate_eval_count={summary['candidate_eval_count']}")
    print(f"selected_checkpoint_count={summary['selected_checkpoint_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
