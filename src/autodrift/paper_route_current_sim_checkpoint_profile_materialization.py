"""Checkpoint/profile materialization for the current-sim comparison panel."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_WORKLOAD = Path("runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m2171_paper_route_current_sim_checkpoint_profile_materialization")
TARGET_PROFILE_COUNT = 8
TARGET_WORKLOAD_COUNT = 320
RESET_CONTROL_PROFILE = "L3_reset_control"
RESET_CONTROL_SOURCE_PROFILE = "L3_online_gru"
PROFILE_CHECKPOINT_FIELDNAMES = [
    "profile_name",
    "profile_level",
    "profile_config_path",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_dim",
    "training_enabled",
    "checkpoint_materialization_mode",
    "checkpoint_source_profile_name",
    "training_started_for_profile",
    "training_command",
    "run_dir",
    "checkpoint_path",
    "checkpoint_exists",
    "training_returncode",
    "stdout_path",
    "stderr_path",
    "input_contract",
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]
FORBIDDEN_GUARDRAILS = (
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "winner_selected",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "measured_rollout_started",
    "environment_rollout_started_for_measured_execution",
    "policy_action_executed_for_measured_execution",
    "private_holdout_used",
    "promoted",
)
TrainingRunner = Callable[[list[str], Path, Path], int]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _profile_rows_from_workload(workload_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in workload_rows:
        profile_name = str(row.get("profile_name", "")).strip()
        if not profile_name:
            continue
        if profile_name not in by_name:
            by_name[profile_name] = {
                "profile_name": profile_name,
                "profile_level": str(row.get("profile_level", "")),
                "profile_config_path": str(row.get("profile_config_path", "")),
                "history_representation": str(row.get("history_representation", "")),
                "history_window_steps": str(row.get("history_window_steps", "")),
            }
    return [by_name[name] for name in sorted(by_name)]


def _load_profile_config(profile_row: Mapping[str, Any]) -> dict[str, Any]:
    config_path = Path(str(profile_row.get("profile_config_path", "")))
    if not config_path.exists():
        raise FileNotFoundError(f"profile config not found: {config_path}")
    payload = read_json(config_path)
    controller_profile = payload.get("controller_profile", {})
    if not isinstance(controller_profile, Mapping):
        raise ValueError(f"profile config {config_path} is missing controller_profile")
    return dict(payload)


def _checkpoint_path_for(output_dir: Path, profile_name: str) -> Path:
    return output_dir / "checkpoints" / profile_name / "checkpoint.pt"


def _run_dir_for(output_dir: Path, profile_name: str) -> Path:
    return output_dir / "profiles" / profile_name


def _training_command(*, config_path: Path, run_dir: Path, checkpoint_path: Path, device: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(config_path),
        "--run-dir",
        str(run_dir),
        "--save",
        str(checkpoint_path),
        "--device",
        str(device),
    ]


def default_training_runner(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
    env = dict(os.environ)
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    completed = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return int(completed.returncode)


def _profile_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "current_sim_profile_checkpoints_materialized",
            "admissible": True,
            "reason": "M2171 may claim only checkpoint/workload readiness if all checkpoint paths exist",
        },
        {
            "claim": "measured_execution_admissible",
            "admissible": False,
            "reason": "materialization result must be audited before measured execution command design",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "no M2151 measured execution has run",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "checkpoint materialization is not controller outcome evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "checkpoint materialization does not test history necessity",
        },
    ]


def materialize_profile_checkpoints(
    *,
    workload_path: Path | str = DEFAULT_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    device: str = "cpu",
    target_profile_count: int = TARGET_PROFILE_COUNT,
    target_workload_count: int = TARGET_WORKLOAD_COUNT,
    training_runner: TrainingRunner = default_training_runner,
) -> dict[str, Any]:
    workload_path = Path(workload_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workload_rows = read_csv_rows(workload_path)
    profile_rows = _profile_rows_from_workload(workload_rows)
    profile_configs = {row["profile_name"]: _load_profile_config(row) for row in profile_rows}
    checkpoint_by_profile: dict[str, Path] = {}
    profile_checkpoint_rows: list[dict[str, Any]] = []
    training_command_count = 0
    successful_training_command_count = 0
    failed_training_command_count = 0

    for profile_row in profile_rows:
        profile_name = str(profile_row["profile_name"])
        config_path = Path(str(profile_row["profile_config_path"]))
        config = profile_configs[profile_name]
        controller_profile = dict(config.get("controller_profile", {}))
        training_enabled = _bool(controller_profile.get("training_enabled"))
        checkpoint_path = _checkpoint_path_for(output_dir, profile_name)
        run_dir = _run_dir_for(output_dir, profile_name)
        stdout_path = output_dir / "logs" / f"{profile_name}.stdout.txt"
        stderr_path = output_dir / "logs" / f"{profile_name}.stderr.txt"
        command: list[str] = []
        returncode = 0
        materialization_mode = "train_frozen_profile_config"
        source_profile = profile_name
        training_started_for_profile = False

        if profile_name == RESET_CONTROL_PROFILE:
            training_enabled = False
            materialization_mode = "alias_same_weights_reset_hidden_control"
            source_profile = RESET_CONTROL_SOURCE_PROFILE
            checkpoint_path = checkpoint_by_profile.get(RESET_CONTROL_SOURCE_PROFILE, _checkpoint_path_for(output_dir, RESET_CONTROL_SOURCE_PROFILE))
        elif training_enabled:
            command = _training_command(config_path=config_path, run_dir=run_dir, checkpoint_path=checkpoint_path, device=device)
            training_started_for_profile = True
            training_command_count += 1
            returncode = training_runner(command, stdout_path, stderr_path)
            if returncode == 0 and checkpoint_path.exists():
                successful_training_command_count += 1
            else:
                failed_training_command_count += 1
        else:
            materialization_mode = "not_trainable_without_alias"

        checkpoint_by_profile[profile_name] = checkpoint_path
        profile_checkpoint_rows.append(
            {
                "profile_name": profile_name,
                "profile_level": str(profile_row.get("profile_level", "")),
                "profile_config_path": str(config_path),
                "actor_encoder": str(controller_profile.get("actor_encoder", "")),
                "actor_history_length": int(controller_profile.get("actor_history_length", 0) or 0),
                "env_history_length": int(controller_profile.get("env_history_length", 0) or 0),
                "observation_dim": int(controller_profile.get("observation_dim", 0) or 0),
                "training_enabled": bool(training_enabled),
                "checkpoint_materialization_mode": materialization_mode,
                "checkpoint_source_profile_name": source_profile,
                "training_started_for_profile": bool(training_started_for_profile),
                "training_command": " ".join(command),
                "run_dir": str(run_dir),
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_exists": bool(checkpoint_path.exists()),
                "training_returncode": int(returncode),
                "stdout_path": str(stdout_path) if command else "",
                "stderr_path": str(stderr_path) if command else "",
                "input_contract": str(controller_profile.get("input_contract", "")),
                "uses_hidden_oracle_actor_inputs": _bool(controller_profile.get("uses_hidden_oracle_actor_inputs")),
                "uses_wheel_or_slip_inputs": _bool(controller_profile.get("uses_wheel_or_slip_inputs")),
                "uses_reference_or_ttc_inputs": _bool(controller_profile.get("uses_reference_or_ttc_inputs")),
            }
        )

    materialized_workload: list[dict[str, Any]] = []
    for row in workload_rows:
        profile_name = str(row.get("profile_name", ""))
        materialized = dict(row)
        checkpoint_path = checkpoint_by_profile.get(profile_name)
        materialized["checkpoint_path"] = str(checkpoint_path) if checkpoint_path is not None else ""
        materialized_workload.append(materialized)

    checkpoint_path_present_count = sum(bool(str(row.get("checkpoint_path", "")).strip()) for row in materialized_workload)
    checkpoint_path_missing_count = len(materialized_workload) - checkpoint_path_present_count
    checkpoint_path_exists_count = sum(bool(str(row.get("checkpoint_path", "")).strip()) and Path(str(row.get("checkpoint_path"))).exists() for row in materialized_workload)
    trainable_profile_count = sum(
        bool(row.get("training_started_for_profile")) for row in profile_checkpoint_rows
    )
    alias_profile_count = sum(
        str(row.get("checkpoint_materialization_mode", "")) == "alias_same_weights_reset_hidden_control"
        for row in profile_checkpoint_rows
    )
    profile_specific_tuning = any(_bool(row.get("profile_specific_tuning")) for row in workload_rows)
    forbidden_input_violation = any(
        _bool(row.get("uses_hidden_oracle_actor_inputs"))
        or _bool(row.get("uses_wheel_or_slip_inputs"))
        or _bool(row.get("uses_reference_or_ttc_inputs"))
        for row in profile_checkpoint_rows
    )
    reset_control_trained = any(
        row.get("profile_name") == RESET_CONTROL_PROFILE and _bool(row.get("training_started_for_profile"))
        for row in profile_checkpoint_rows
    )
    guardrail_flags = {
        "actor_input_contract_changed": bool(forbidden_input_violation),
        "profile_specific_tuning": bool(profile_specific_tuning),
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "measured_rollout_started": False,
        "environment_rollout_started_for_measured_execution": False,
        "policy_action_executed_for_measured_execution": False,
        "private_holdout_used": False,
        "promoted": False,
    }
    guardrail_violation_count = sum(1 for key in FORBIDDEN_GUARDRAILS if guardrail_flags.get(key))
    count_pass = len(profile_rows) == int(target_profile_count) and len(materialized_workload) == int(target_workload_count)
    pass_gate = (
        count_pass
        and training_command_count == 7
        and successful_training_command_count == 7
        and failed_training_command_count == 0
        and trainable_profile_count == 7
        and alias_profile_count == 1
        and not reset_control_trained
        and checkpoint_path_missing_count == 0
        and checkpoint_path_exists_count == len(materialized_workload)
        and guardrail_violation_count == 0
    )
    result_class = (
        "current_sim_checkpoint_profile_materialization_pass"
        if pass_gate
        else "current_sim_checkpoint_profile_materialization_fail_closed"
    )

    write_csv_rows(output_dir / "profile_checkpoint_rows.csv", profile_checkpoint_rows, PROFILE_CHECKPOINT_FIELDNAMES)
    write_csv_rows(output_dir / "materialized_workload.csv", materialized_workload, list(materialized_workload[0].keys()) if materialized_workload else [])
    write_csv_rows(output_dir / "claim_boundary.csv", _profile_claim_boundary_rows(), CLAIM_FIELDNAMES)
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "workload_path": workload_path,
        "output_dir": output_dir,
        "profile_count": len(profile_rows),
        "target_profile_count": int(target_profile_count),
        "input_workload_count": len(workload_rows),
        "materialized_workload_count": len(materialized_workload),
        "target_workload_count": int(target_workload_count),
        "count_pass": bool(count_pass),
        "profile_counts": _count_by(materialized_workload, "profile_name"),
        "task_family_counts": _count_by(materialized_workload, "task_family"),
        "trainable_profile_count": int(trainable_profile_count),
        "alias_profile_count": int(alias_profile_count),
        "training_command_count": int(training_command_count),
        "successful_training_command_count": int(successful_training_command_count),
        "failed_training_command_count": int(failed_training_command_count),
        "checkpoint_path_present_count": int(checkpoint_path_present_count),
        "checkpoint_path_missing_count": int(checkpoint_path_missing_count),
        "checkpoint_path_exists_count": int(checkpoint_path_exists_count),
        "reset_control_trained": bool(reset_control_trained),
        "reset_control_checkpoint_source_profile": RESET_CONTROL_SOURCE_PROFILE,
        "training_started": bool(training_command_count > 0),
        "environment_rollout_started_for_training": bool(training_command_count > 0),
        "ppo_used_for_training": bool(training_command_count > 0),
        "measured_rollout_started": False,
        "environment_rollout_started_for_measured_execution": False,
        "policy_action_executed_for_measured_execution": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "private_holdout_used": False,
        "promoted": False,
        "profile_specific_tuning": bool(profile_specific_tuning),
        "actor_input_contract_changed": bool(forbidden_input_violation),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": int(guardrail_violation_count),
        "artifacts": {
            "summary": output_dir / "summary.json",
            "profile_checkpoint_rows": output_dir / "profile_checkpoint_rows.csv",
            "materialized_workload": output_dir / "materialized_workload.csv",
            "claim_boundary": output_dir / "claim_boundary.csv",
            "run_state": output_dir / "run_state.json",
        },
        "next_blocker": "m2172-paper-route-current-sim-checkpoint-profile-materialization-result-audit",
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "status": "completed" if pass_gate else "failed",
            "result_class": result_class,
            "training_started": bool(training_command_count > 0),
            "measured_rollout_started": False,
            "guardrail_violation_count": int(guardrail_violation_count),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize current-sim profile checkpoints and workload paths.")
    parser.add_argument("--workload", type=Path, default=DEFAULT_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--target-profile-count", type=int, default=TARGET_PROFILE_COUNT)
    parser.add_argument("--target-workload-count", type=int, default=TARGET_WORKLOAD_COUNT)
    args = parser.parse_args()
    summary = materialize_profile_checkpoints(
        workload_path=args.workload,
        output_dir=args.output_dir,
        device=args.device,
        target_profile_count=args.target_profile_count,
        target_workload_count=args.target_workload_count,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    if summary["result_class"] != "current_sim_checkpoint_profile_materialization_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
