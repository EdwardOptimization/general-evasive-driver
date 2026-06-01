"""Materialize training-seed repeat checkpoints for current-sim comparison."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any, Callable, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.paper_route_current_sim_checkpoint_profile_materialization import (
    RESET_CONTROL_PROFILE,
    RESET_CONTROL_SOURCE_PROFILE,
    _bool,
    _load_profile_config,
    _profile_rows_from_workload,
    default_training_runner,
    read_csv_rows,
)


DEFAULT_BASE_WORKLOAD = Path("runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv")
DEFAULT_EXISTING_MATERIALIZED_WORKLOAD = Path(
    "runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2177_paper_route_current_sim_training_seed_repeat_materialization")
TRAINABLE_PROFILES = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_25",
    "L2_window_50",
    "L2_window_100",
    "L3_online_gru",
)
NEW_REPEAT_SEEDS = {
    "repeat_1_seed_21761": {
        "seed_group": "21761",
        "seeds": {
            "L0_current_masked": 2176100,
            "L1_one_step": 2176101,
            "L2_window_13": 2176102,
            "L2_window_25": 2176103,
            "L2_window_50": 2176104,
            "L2_window_100": 2176105,
            "L3_online_gru": 2176106,
        },
    },
    "repeat_2_seed_21762": {
        "seed_group": "21762",
        "seeds": {
            "L0_current_masked": 2176200,
            "L1_one_step": 2176201,
            "L2_window_13": 2176202,
            "L2_window_25": 2176203,
            "L2_window_50": 2176204,
            "L2_window_100": 2176205,
            "L3_online_gru": 2176206,
        },
    },
}
EXTRA_WORKLOAD_FIELDS = [
    "training_repeat_id",
    "training_seed_group",
    "profile_training_seed",
    "profile_checkpoint_source_profile",
    "checkpoint_materialization_mode",
    "base_workload_id",
]
PROFILE_FIELDNAMES = [
    "training_repeat_id",
    "training_seed_group",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "training_enabled",
    "profile_training_seed",
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
REPEAT_GROUP_FIELDNAMES = [
    "training_repeat_id",
    "training_seed_group",
    "role",
    "training_started",
    "profile_count",
    "trainable_profile_count",
    "materialized_workload_path",
    "materialized_workload_count",
    "checkpoint_path_exists_count",
    "source_artifact",
]
TrainingRunner = Callable[[list[str], Path, Path], int]


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _training_command(*, config_path: Path, run_dir: Path, checkpoint_path: Path, seed: int, device: str) -> list[str]:
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
        "--seed",
        str(seed),
        "--device",
        str(device),
    ]


def _checkpoint_path(output_dir: Path, repeat_id: str, profile_name: str) -> Path:
    return output_dir / "repeats" / repeat_id / "checkpoints" / profile_name / "checkpoint.pt"


def _run_dir(output_dir: Path, repeat_id: str, profile_name: str) -> Path:
    return output_dir / "repeats" / repeat_id / "profiles" / profile_name


def _write_workload(path: Path, rows: list[dict[str, Any]], base_fieldnames: list[str]) -> None:
    fieldnames = list(base_fieldnames)
    for field in EXTRA_WORKLOAD_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)
    write_csv_rows(path, rows, fieldnames=fieldnames)


def _existing_repeat_group_row(existing_materialized_workload: Path) -> dict[str, Any]:
    rows = read_csv_rows(existing_materialized_workload)
    return {
        "training_repeat_id": "repeat_0_existing",
        "training_seed_group": "11900",
        "role": "existing_reference",
        "training_started": False,
        "profile_count": len({row.get("profile_name", "") for row in rows}),
        "trainable_profile_count": 7,
        "materialized_workload_path": str(existing_materialized_workload),
        "materialized_workload_count": len(rows),
        "checkpoint_path_exists_count": sum(bool(row.get("checkpoint_path")) and Path(str(row.get("checkpoint_path"))).exists() for row in rows),
        "source_artifact": "runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json",
    }


def materialize_training_seed_repeats(
    *,
    base_workload: Path | str = DEFAULT_BASE_WORKLOAD,
    existing_materialized_workload: Path | str = DEFAULT_EXISTING_MATERIALIZED_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    device: str = "cpu",
    target_new_workload_count: int = 640,
    training_runner: TrainingRunner = default_training_runner,
) -> dict[str, Any]:
    base_workload = Path(base_workload)
    existing_materialized_workload = Path(existing_materialized_workload)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_rows = read_csv_rows(base_workload)
    profile_rows = _profile_rows_from_workload(base_rows)
    profile_by_name = {str(row["profile_name"]): row for row in profile_rows}
    profile_configs = {name: _load_profile_config(row) for name, row in profile_by_name.items()}
    base_fieldnames = list(base_rows[0].keys()) if base_rows else []

    repeat_group_rows = [_existing_repeat_group_row(existing_materialized_workload)]
    profile_checkpoint_rows: list[dict[str, Any]] = []
    all_new_workload_rows: list[dict[str, Any]] = []
    new_training_command_count = 0
    successful_training_command_count = 0
    failed_training_command_count = 0
    reset_control_trained_count = 0

    for repeat_id, spec in NEW_REPEAT_SEEDS.items():
        seed_group = str(spec["seed_group"])
        seeds: dict[str, int] = dict(spec["seeds"])  # type: ignore[arg-type]
        checkpoint_by_profile: dict[str, Path] = {}
        repeat_workload_rows: list[dict[str, Any]] = []
        for profile_name in sorted(profile_by_name):
            profile_row = profile_by_name[profile_name]
            config_path = Path(str(profile_row.get("profile_config_path", "")))
            config = profile_configs[profile_name]
            controller_profile = dict(config.get("controller_profile", {}))
            training_enabled = bool(profile_name in TRAINABLE_PROFILES and _bool(controller_profile.get("training_enabled")))
            profile_seed = seeds.get(profile_name)
            checkpoint_path = _checkpoint_path(output_dir, repeat_id, profile_name)
            run_dir = _run_dir(output_dir, repeat_id, profile_name)
            stdout_path = output_dir / "logs" / repeat_id / f"{profile_name}.stdout.txt"
            stderr_path = output_dir / "logs" / repeat_id / f"{profile_name}.stderr.txt"
            command: list[str] = []
            returncode = 0
            source_profile = profile_name
            mode = "train_frozen_profile_config_seed_override"
            training_started = False

            if profile_name == RESET_CONTROL_PROFILE:
                training_enabled = False
                mode = "alias_same_weights_reset_hidden_control"
                source_profile = RESET_CONTROL_SOURCE_PROFILE
                checkpoint_path = checkpoint_by_profile.get(RESET_CONTROL_SOURCE_PROFILE, _checkpoint_path(output_dir, repeat_id, RESET_CONTROL_SOURCE_PROFILE))
                profile_seed = seeds.get(RESET_CONTROL_SOURCE_PROFILE)
            elif training_enabled and profile_seed is not None:
                command = _training_command(
                    config_path=config_path,
                    run_dir=run_dir,
                    checkpoint_path=checkpoint_path,
                    seed=int(profile_seed),
                    device=device,
                )
                training_started = True
                new_training_command_count += 1
                returncode = training_runner(command, stdout_path, stderr_path)
                if returncode == 0 and checkpoint_path.exists():
                    successful_training_command_count += 1
                else:
                    failed_training_command_count += 1

            if profile_name == RESET_CONTROL_PROFILE and training_started:
                reset_control_trained_count += 1
            checkpoint_by_profile[profile_name] = checkpoint_path
            profile_checkpoint_rows.append(
                {
                    "training_repeat_id": repeat_id,
                    "training_seed_group": seed_group,
                    "profile_name": profile_name,
                    "profile_level": str(profile_row.get("profile_level", "")),
                    "profile_config_path": str(config_path),
                    "training_enabled": bool(training_enabled),
                    "profile_training_seed": int(profile_seed or 0),
                    "checkpoint_materialization_mode": mode,
                    "checkpoint_source_profile_name": source_profile,
                    "training_started_for_profile": bool(training_started),
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

        for row in base_rows:
            profile_name = str(row.get("profile_name", ""))
            checkpoint_path = checkpoint_by_profile.get(profile_name)
            source_profile = RESET_CONTROL_SOURCE_PROFILE if profile_name == RESET_CONTROL_PROFILE else profile_name
            materialized = dict(row)
            materialized.update(
                {
                    "workload_id": f"{repeat_id}::{row.get('workload_id', '')}",
                    "checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else "",
                    "training_repeat_id": repeat_id,
                    "training_seed_group": seed_group,
                    "profile_training_seed": int(seeds.get(source_profile, 0)),
                    "profile_checkpoint_source_profile": source_profile,
                    "checkpoint_materialization_mode": (
                        "alias_same_weights_reset_hidden_control"
                        if profile_name == RESET_CONTROL_PROFILE
                        else "train_frozen_profile_config_seed_override"
                    ),
                    "base_workload_id": str(row.get("workload_id", "")),
                }
            )
            repeat_workload_rows.append(materialized)
            all_new_workload_rows.append(materialized)

        repeat_path = output_dir / "repeats" / repeat_id / "materialized_workload.csv"
        _write_workload(repeat_path, repeat_workload_rows, base_fieldnames)
        repeat_group_rows.append(
            {
                "training_repeat_id": repeat_id,
                "training_seed_group": seed_group,
                "role": "new_repeat",
                "training_started": True,
                "profile_count": len(profile_by_name),
                "trainable_profile_count": len(TRAINABLE_PROFILES),
                "materialized_workload_path": str(repeat_path),
                "materialized_workload_count": len(repeat_workload_rows),
                "checkpoint_path_exists_count": sum(
                    bool(row.get("checkpoint_path")) and Path(str(row.get("checkpoint_path"))).exists()
                    for row in repeat_workload_rows
                ),
                "source_artifact": str(output_dir / "summary.json"),
            }
        )

    combined_workload_path = output_dir / "combined_new_repeat_materialized_workload.csv"
    _write_workload(combined_workload_path, all_new_workload_rows, base_fieldnames)
    checkpoint_path_missing_count = sum(not str(row.get("checkpoint_path", "")).strip() for row in all_new_workload_rows)
    checkpoint_path_exists_count = sum(
        bool(row.get("checkpoint_path")) and Path(str(row.get("checkpoint_path"))).exists()
        for row in all_new_workload_rows
    )
    forbidden_input_violation = any(
        _bool(row.get("uses_hidden_oracle_actor_inputs"))
        or _bool(row.get("uses_wheel_or_slip_inputs"))
        or _bool(row.get("uses_reference_or_ttc_inputs"))
        for row in profile_checkpoint_rows
    )
    profile_specific_tuning = any(_bool(row.get("profile_specific_tuning")) for row in base_rows)
    guardrail_flags = {
        "actor_input_contract_changed": bool(forbidden_input_violation),
        "profile_specific_tuning": bool(profile_specific_tuning),
        "measured_rollout_started": False,
        "policy_action_executed_for_measured_execution": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "private_holdout_used": False,
        "promoted": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    pass_gate = (
        len(repeat_group_rows) == 3
        and new_training_command_count == 14
        and successful_training_command_count == 14
        and failed_training_command_count == 0
        and len(all_new_workload_rows) == int(target_new_workload_count)
        and checkpoint_path_missing_count == 0
        and checkpoint_path_exists_count == len(all_new_workload_rows)
        and reset_control_trained_count == 0
        and guardrail_violation_count == 0
    )
    result_class = (
        "current_sim_training_seed_repeat_materialization_pass"
        if pass_gate
        else "current_sim_training_seed_repeat_materialization_fail_closed"
    )

    write_csv_rows(output_dir / "repeat_group_rows.csv", repeat_group_rows, REPEAT_GROUP_FIELDNAMES)
    write_csv_rows(output_dir / "profile_checkpoint_rows.csv", profile_checkpoint_rows, PROFILE_FIELDNAMES)
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": output_dir,
        "base_workload": base_workload,
        "existing_materialized_workload": existing_materialized_workload,
        "repeat_group_count": len(repeat_group_rows),
        "new_repeat_group_count": len(NEW_REPEAT_SEEDS),
        "existing_repeat_group_count": 1,
        "new_training_command_count": int(new_training_command_count),
        "successful_training_command_count": int(successful_training_command_count),
        "failed_training_command_count": int(failed_training_command_count),
        "new_materialized_workload_count": len(all_new_workload_rows),
        "target_new_workload_count": int(target_new_workload_count),
        "checkpoint_path_missing_count": int(checkpoint_path_missing_count),
        "checkpoint_path_exists_count": int(checkpoint_path_exists_count),
        "reset_control_trained_count": int(reset_control_trained_count),
        "profile_counts": _count_by(all_new_workload_rows, "profile_name"),
        "repeat_counts": _count_by(all_new_workload_rows, "training_repeat_id"),
        "task_family_counts": _count_by(all_new_workload_rows, "task_family"),
        "training_started": True,
        "environment_rollout_started_for_training": True,
        "ppo_used_for_training": True,
        "measured_rollout_started": False,
        "policy_action_executed_for_measured_execution": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": int(guardrail_violation_count),
        "artifacts": {
            "summary": output_dir / "summary.json",
            "repeat_group_rows": output_dir / "repeat_group_rows.csv",
            "profile_checkpoint_rows": output_dir / "profile_checkpoint_rows.csv",
            "combined_new_repeat_materialized_workload": combined_workload_path,
            "run_state": output_dir / "run_state.json",
        },
        "next_blocker": "m2178-paper-route-current-sim-training-seed-repeat-materialization-result-audit",
    }
    write_json(output_dir / "summary.json", summary)
    write_run_state(
        output_dir / "run_state.json",
        {
            "status": "completed" if pass_gate else "failed",
            "result_class": result_class,
            "new_training_command_count": int(new_training_command_count),
            "new_materialized_workload_count": len(all_new_workload_rows),
            "guardrail_violation_count": int(guardrail_violation_count),
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize current-sim training-seed repeat checkpoints.")
    parser.add_argument("--base-workload", type=Path, default=DEFAULT_BASE_WORKLOAD)
    parser.add_argument("--existing-materialized-workload", type=Path, default=DEFAULT_EXISTING_MATERIALIZED_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--target-new-workload-count", type=int, default=640)
    args = parser.parse_args()
    summary = materialize_training_seed_repeats(
        base_workload=args.base_workload,
        existing_materialized_workload=args.existing_materialized_workload,
        output_dir=args.output_dir,
        device=args.device,
        target_new_workload_count=int(args.target_new_workload_count),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"result_class={summary['result_class']}")
    if summary["result_class"] != "current_sim_training_seed_repeat_materialization_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
