"""Execute M2230 matched-budget profile training from the M2227 matrix."""

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
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_TRAINING_MATRIX = Path("runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2230_paper_route_current_sim_matched_budget_profile_training_execution")
DEFAULT_EXECUTION_ROOT = DEFAULT_OUTPUT_DIR
DEFAULT_NEXT_BLOCKER = "m2231-paper-route-current-sim-matched-budget-profile-training-execution-result-audit"

EXPECTED_PROFILES = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_25",
    "L2_window_50",
    "L3_online_gru",
)
EXPECTED_SEED_IDS = (222601, 222602, 222603)
BUDGET_FIELDS = (
    "total_steps",
    "rollout_steps",
    "num_envs",
    "update_epochs",
    "minibatch_size",
    "learning_rate",
    "clip_coef",
    "max_grad_norm",
    "eval_episodes",
)
EXPECTED_BUDGET = {
    "total_steps": "8192",
    "rollout_steps": "128",
    "num_envs": "4",
    "update_epochs": "2",
    "minibatch_size": "256",
    "learning_rate": "0.0001",
    "clip_coef": "0.1",
    "max_grad_norm": "0.25",
    "eval_episodes": "32",
}
SELECTED_METRICS = (
    "return_mean",
    "steps_mean",
    "termination_rate",
    "lateral_rmse_mean",
    "beta_abs_error_mean",
)
RUN_ROW_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "status",
    "failure",
    "returncode",
    "runtime_seconds",
    "config_path",
    "run_dir",
    "checkpoint_path",
    "train_log_path",
    "eval_summary_path",
    "command",
    "checkpoint_exists",
    "eval_summary_exists",
    "selected_metrics_finite",
    "readiness_floor_pass",
    "eval_return_mean",
    "eval_termination_rate",
    "eval_steps_mean",
    "eval_lateral_rmse_mean",
    "eval_beta_abs_error_mean",
    "private_holdout_used",
    "profile_specific_tuning",
    "winner_selected",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
AGGREGATE_FIELDNAMES = [
    "profile_name",
    "seed_runs",
    "completed_run_count",
    "failed_run_count",
    "passing_seed_count",
    "readiness_floor_pass",
    "eval_return_mean_mean",
    "eval_termination_rate_mean",
    "all_selected_metrics_finite",
    "ranking_admissible",
    "winner_selected",
]
COMMAND_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "config_path",
    "run_dir",
    "checkpoint_path",
    "command",
]


CommandRunner = Callable[[Sequence[str], Path, Mapping[str, str], Any], int]


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


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite_selected_metrics(eval_summary: Mapping[str, Any]) -> bool:
    return all(np.isfinite(_as_float(eval_summary.get(key))) for key in SELECTED_METRICS)


def _readiness_floor(eval_summary: Mapping[str, Any]) -> bool:
    return bool(
        _as_float(eval_summary.get("termination_rate")) <= 0.4
        and _as_float(eval_summary.get("return_mean")) >= 50.0
    )


def _budget_signature(row: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in BUDGET_FIELDS)


def _config_contract_violation(config: Mapping[str, Any]) -> bool:
    profile = config.get("controller_profile", {})
    env = config.get("env", {})
    return bool(
        profile.get("input_contract") != "P0_human_view_no_wheel_no_oracle"
        or bool(profile.get("uses_hidden_oracle_actor_inputs"))
        or bool(profile.get("uses_wheel_or_slip_inputs"))
        or bool(profile.get("uses_reference_or_ttc_inputs"))
        or bool(env.get("include_privileged_params"))
        or str(env.get("wheel_observation_mode", "")) != "none"
        or str(env.get("obstacle_relative_velocity_mode", "")) != "zero"
    )


def load_training_matrix(path: Path | str) -> list[dict[str, str]]:
    rows = _read_csv(path)
    return sorted(rows, key=lambda row: (str(row["profile_name"]), int(row["seed_id"])))


def build_execution_plan(
    *,
    training_matrix: Path | str,
    execution_root: Path | str,
    device: str = "cpu",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_training_matrix(training_matrix)
    execution = Path(execution_root)
    expected_count = len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS)
    profile_names = tuple(sorted({str(row.get("profile_name", "")) for row in rows}))
    seed_ids = tuple(sorted({int(row.get("seed_id", -1)) for row in rows}))
    budget_signatures = {_budget_signature(row) for row in rows}

    validation = {
        "expected_run_count": expected_count,
        "matrix_row_count": len(rows),
        "profile_names": list(profile_names),
        "seed_ids": list(seed_ids),
        "budget_signature_count": len(budget_signatures),
        "profile_set_matched": profile_names == EXPECTED_PROFILES,
        "seed_set_matched": seed_ids == EXPECTED_SEED_IDS,
        "budget_matched": len(budget_signatures) == 1 and next(iter(budget_signatures), ()) == tuple(
            EXPECTED_BUDGET[field] for field in BUDGET_FIELDS
        ),
        "missing_config_count": 0,
        "contract_violation_count": 0,
        "config_budget_violation_count": 0,
    }

    plan_rows: list[dict[str, Any]] = []
    for row in rows:
        profile_name = str(row["profile_name"])
        seed_id = int(row["seed_id"])
        config_path = Path(row["generated_config_path"])
        if not config_path.exists():
            validation["missing_config_count"] += 1
            config: dict[str, Any] = {}
        else:
            config = read_json(config_path)
            if _config_contract_violation(config):
                validation["contract_violation_count"] += 1
            ppo = config.get("ppo", {})
            for field, expected in EXPECTED_BUDGET.items():
                if str(ppo.get(field)) != expected:
                    validation["config_budget_violation_count"] += 1
                    break

        run_dir = execution / "profiles" / profile_name / f"seed_{seed_id}"
        checkpoint_path = execution / "checkpoints" / profile_name / f"seed_{seed_id}" / "checkpoint.pt"
        cmd = [
            sys.executable,
            "-m",
            "autodrift.train_ppo",
            "--config",
            str(config_path),
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
                "config_path": str(config_path),
                "run_dir": str(run_dir),
                "checkpoint_path": str(checkpoint_path),
                "command": " ".join(cmd),
                "cmd": cmd,
            }
        )

    validation["validation_pass"] = bool(
        validation["matrix_row_count"] == expected_count
        and validation["profile_set_matched"]
        and validation["seed_set_matched"]
        and validation["budget_matched"]
        and validation["missing_config_count"] == 0
        and validation["contract_violation_count"] == 0
        and validation["config_budget_violation_count"] == 0
    )
    return plan_rows, validation


def _default_runner(cmd: Sequence[str], cwd: Path, env: Mapping[str, str], stdout: Any) -> int:
    completed = subprocess.run(cmd, cwd=cwd, env=dict(env), stdout=stdout, stderr=subprocess.STDOUT, check=False)
    return int(completed.returncode)


def _failed_row(plan: Mapping[str, Any], *, failure: str) -> dict[str, Any]:
    return {
        "matrix_id": plan["matrix_id"],
        "profile_name": plan["profile_name"],
        "seed_id": int(plan["seed_id"]),
        "status": "failed",
        "failure": failure,
        "returncode": -1,
        "runtime_seconds": 0.0,
        "config_path": plan["config_path"],
        "run_dir": plan["run_dir"],
        "checkpoint_path": plan["checkpoint_path"],
        "train_log_path": str(Path(plan["run_dir"]) / "train.log"),
        "eval_summary_path": str(Path(plan["run_dir"]) / "eval_summary.json"),
        "command": plan["command"],
        "checkpoint_exists": False,
        "eval_summary_exists": False,
        "selected_metrics_finite": False,
        "readiness_floor_pass": False,
        "eval_return_mean": "",
        "eval_termination_rate": "",
        "eval_steps_mean": "",
        "eval_lateral_rmse_mean": "",
        "eval_beta_abs_error_mean": "",
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def run_training_plan(
    *,
    plan_rows: Sequence[Mapping[str, Any]],
    command_runner: CommandRunner = _default_runner,
    fail_fast: bool = True,
) -> list[dict[str, Any]]:
    env = _subprocess_env()
    run_rows: list[dict[str, Any]] = []
    for plan in plan_rows:
        run_dir = Path(plan["run_dir"])
        checkpoint_path = Path(plan["checkpoint_path"])
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

        row = {
            "matrix_id": plan["matrix_id"],
            "profile_name": plan["profile_name"],
            "seed_id": int(plan["seed_id"]),
            "status": "completed" if not failure else "failed",
            "failure": failure,
            "returncode": returncode,
            "runtime_seconds": runtime_seconds,
            "config_path": plan["config_path"],
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
        run_rows.append(row)
        if failure and fail_fast:
            break
    return run_rows


def aggregate_profile_rows(run_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in run_rows:
        groups[str(row["profile_name"])].append(row)
    aggregates: list[dict[str, Any]] = []
    for profile_name in EXPECTED_PROFILES:
        rows = groups.get(profile_name, [])
        completed = [row for row in rows if str(row.get("status")) == "completed"]
        passing = [row for row in completed if bool(row.get("readiness_floor_pass"))]
        finite = bool(completed and all(bool(row.get("selected_metrics_finite")) for row in completed))
        returns = [_as_float(row.get("eval_return_mean")) for row in completed]
        terms = [_as_float(row.get("eval_termination_rate")) for row in completed]
        aggregates.append(
            {
                "profile_name": profile_name,
                "seed_runs": len(rows),
                "completed_run_count": len(completed),
                "failed_run_count": len(rows) - len(completed),
                "passing_seed_count": len(passing),
                "readiness_floor_pass": len(passing) >= 2,
                "eval_return_mean_mean": float(np.mean(returns)) if returns else float("nan"),
                "eval_termination_rate_mean": float(np.mean(terms)) if terms else float("nan"),
                "all_selected_metrics_finite": finite,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return aggregates


def _command_rows(plan_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{key: row[key] for key in COMMAND_FIELDNAMES} for row in plan_rows]


def execute_matched_budget_training(
    *,
    training_matrix: Path | str = DEFAULT_TRAINING_MATRIX,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    execution_root: Path | str = DEFAULT_EXECUTION_ROOT,
    device: str = "cpu",
    fail_fast: bool = True,
    command_runner: CommandRunner = _default_runner,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plan_rows, validation = build_execution_plan(
        training_matrix=training_matrix,
        execution_root=execution_root,
        device=device,
    )
    write_csv_rows(output / "command_matrix.csv", _command_rows(plan_rows), fieldnames=COMMAND_FIELDNAMES)

    start = time.perf_counter()
    if validation["validation_pass"]:
        run_rows = run_training_plan(plan_rows=plan_rows, command_runner=command_runner, fail_fast=fail_fast)
    else:
        run_rows = [_failed_row(plan, failure="preflight_validation_failed") for plan in plan_rows]
    runtime_seconds = time.perf_counter() - start

    aggregate_rows = aggregate_profile_rows(run_rows)
    write_csv_rows(output / "run_rows.csv", run_rows, fieldnames=RUN_ROW_FIELDNAMES)
    write_csv_rows(output / "profile_aggregate.csv", aggregate_rows, fieldnames=AGGREGATE_FIELDNAMES)

    completed_run_count = sum(1 for row in run_rows if row["status"] == "completed")
    failed_run_count = len(run_rows) - completed_run_count
    all_selected_metrics_finite = bool(run_rows and all(bool(row["selected_metrics_finite"]) for row in run_rows))
    quality_floor_profile_pass_count = sum(1 for row in aggregate_rows if bool(row["readiness_floor_pass"]))
    guardrail_flags = {
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "winner_selected": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    expected_run_count = len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS)
    result_class = (
        "current_sim_matched_budget_profile_training_execution_pass"
        if (
            validation["validation_pass"]
            and len(run_rows) == expected_run_count
            and completed_run_count == expected_run_count
            and failed_run_count == 0
            and all_selected_metrics_finite
            and guardrail_violation_count == 0
        )
        else "current_sim_matched_budget_profile_training_execution_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "runtime_seconds": runtime_seconds,
        "training_matrix": str(training_matrix),
        "output_dir": str(output),
        "execution_root": str(execution_root),
        "device": str(device),
        "fail_fast": bool(fail_fast),
        "expected_run_count": expected_run_count,
        "planned_run_count": len(plan_rows),
        "completed_run_count": completed_run_count,
        "failed_run_count": failed_run_count,
        "profile_count": len(EXPECTED_PROFILES),
        "seed_count": len(EXPECTED_SEED_IDS),
        "profiles": list(EXPECTED_PROFILES),
        "seed_ids": list(EXPECTED_SEED_IDS),
        **validation,
        "all_selected_metrics_finite": all_selected_metrics_finite,
        "quality_floor_profile_pass_count": quality_floor_profile_pass_count,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
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
        "artifacts": {
            "summary": str(output / "summary.json"),
            "command_matrix": str(output / "command_matrix.csv"),
            "run_rows": str(output / "run_rows.csv"),
            "profile_aggregate": str(output / "profile_aggregate.csv"),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2230-paper-route-current-sim-matched-budget-profile-training-execution-implementation-and-run",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-matrix", type=Path, default=DEFAULT_TRAINING_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--execution-root", type=Path, default=DEFAULT_EXECUTION_ROOT)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--no-fail-fast", dest="fail_fast", action="store_false")
    parser.set_defaults(fail_fast=True)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = execute_matched_budget_training(
        training_matrix=args.training_matrix,
        output_dir=args.output_dir,
        execution_root=args.execution_root,
        device=args.device,
        fail_fast=bool(args.fail_fast),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"run_rows={Path(args.output_dir) / 'run_rows.csv'}")
    print(f"profile_aggregate={Path(args.output_dir) / 'profile_aggregate.csv'}")
    print(f"result_class={summary['result_class']}")
    print(f"completed_run_count={summary['completed_run_count']}")
    print(f"failed_run_count={summary['failed_run_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
