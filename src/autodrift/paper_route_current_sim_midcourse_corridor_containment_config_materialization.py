"""Materialize M2259 midcourse corridor-containment repair configs."""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.paper_route_current_sim_training_stability_repair_execution import EXPECTED_PROFILES, EXPECTED_SEED_IDS


DEFAULT_SOURCE_CONFIG_ROOT = Path("runs/m2241_paper_route_current_sim_training_stability_repair_execution/configs")
DEFAULT_OUTPUT_DIR = Path("runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs")
DEFAULT_TRAINING_OUTPUT_ROOT = Path("runs/m2261_paper_route_current_sim_midcourse_corridor_containment_training_execution")
DEFAULT_NEXT_BLOCKER = "m2260-paper-route-current-sim-midcourse-corridor-containment-config-materialization-result-audit"

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
    "checkpoint_interval_steps",
)
REPAIR_ENV_OVERRIDES: dict[str, Any] = {
    "track_cost_scale": 3.0,
    "heading_cost_scale": 0.30,
    "road_margin_cost_scale": 2.6,
    "road_margin_warning_fraction": 0.50,
    "off_track_penalty": 8.0,
    "termination_penalty": 8.0,
}
REPAIR_OBSTACLE_OVERRIDES: dict[str, Any] = {
    "clearance_margin_reward_scale": 1.0,
    "clearance_margin_reward_clip": 0.25,
    "dense_clearance_margin_reward_scale": 0.5,
    "dense_clearance_margin_reward_window": 10.0,
    "collision_penalty": 25.0,
}
MATRIX_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "source_config_path",
    "generated_config_path",
    "run_dir",
    "checkpoint_path",
    "training_command",
    *BUDGET_FIELDS,
    "track_width",
    "track_width_widened",
    "track_cost_scale",
    "heading_cost_scale",
    "road_margin_cost_scale",
    "road_margin_warning_fraction",
    "off_track_penalty",
    "dense_clearance_margin_reward_scale",
    "clearance_margin_reward_scale",
    "collision_penalty",
    "actor_encoder",
    "actor_history_length",
    "env_history_length",
    "observation_dim",
    "input_contract",
    "uses_hidden_oracle_actor_inputs",
    "uses_wheel_or_slip_inputs",
    "uses_reference_or_ttc_inputs",
    "include_privileged_params",
    "wheel_observation_mode",
    "obstacle_relative_velocity_mode",
    "training_started",
    "policy_action_executed",
    "profile_specific_tuning",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def source_config_path(root: Path | str, profile_name: str, seed_id: int) -> Path:
    return Path(root) / profile_name / f"seed_{int(seed_id)}" / "config.json"


def generated_config_path(output_dir: Path | str, profile_name: str, seed_id: int) -> Path:
    return Path(output_dir) / "configs" / profile_name / f"seed_{int(seed_id)}" / "config.json"


def _contract_violation(config: Mapping[str, Any]) -> bool:
    profile = config.get("controller_profile", {})
    env = config.get("env", {})
    return bool(
        _bool(profile.get("uses_hidden_oracle_actor_inputs"))
        or _bool(profile.get("uses_wheel_or_slip_inputs"))
        or _bool(profile.get("uses_reference_or_ttc_inputs"))
        or _bool(env.get("include_privileged_params"))
        or str(env.get("wheel_observation_mode", "")) != "none"
        or str(env.get("obstacle_relative_velocity_mode", "")) != "zero"
    )


def build_containment_config(
    *,
    profile_name: str,
    seed_id: int,
    source_config_root: Path | str = DEFAULT_SOURCE_CONFIG_ROOT,
) -> dict[str, Any]:
    source_path = source_config_path(source_config_root, profile_name, seed_id)
    config = deepcopy(read_json(source_path))
    env = dict(config["env"])
    obstacle = dict(env.get("obstacle", {}))
    original_track_width = float(env.get("track_width", 0.0))
    env.update(REPAIR_ENV_OVERRIDES)
    obstacle.update(REPAIR_OBSTACLE_OVERRIDES)
    env["obstacle"] = obstacle
    repaired_track_width = float(env.get("track_width", 0.0))
    if repaired_track_width != original_track_width:
        raise ValueError("M2259 must not widen track_width as a repair")
    build_env_config(env)

    profile = dict(config["controller_profile"])
    profile.update(
        {
            "midcourse_corridor_containment_config": True,
            "matched_budget_stage": "midcourse_corridor_containment_v1",
            "matched_budget_seed_id": int(seed_id),
            "source_config_path": str(source_path),
            "profile_specific_tuning": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    config["env"] = env
    config["controller_profile"] = profile
    config["midcourse_corridor_containment_repair_protocol"] = {
        "stage": "midcourse_corridor_containment_v1",
        "source_stage": str(config.get("matched_budget_training_protocol", {}).get("stage", "matched_budget_medium_v1")),
        "profiles": list(EXPECTED_PROFILES),
        "seed_ids": list(EXPECTED_SEED_IDS),
        "reward_overrides": dict(REPAIR_ENV_OVERRIDES),
        "obstacle_reward_overrides": dict(REPAIR_OBSTACLE_OVERRIDES),
        "track_width_widened": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "training_started": False,
        "acceptance_criteria": {
            "mid_offtrack_delta_max": 0,
            "mild_overshoot_delta_max": 0,
            "global_offtrack_count_less_than": 110,
            "global_collision_count_max": 107,
            "max_step_noncompletion_count": 0,
            "return_improvement_alone_sufficient": False,
        },
    }
    return config


def _training_command(*, config_path: Path, run_dir: Path, checkpoint_path: Path) -> list[str]:
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
        "cpu",
    ]


def _budget_signature(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(row[field] for field in BUDGET_FIELDS)


def _matrix_row(
    *,
    profile_name: str,
    seed_id: int,
    source_path: Path,
    generated_path: Path,
    training_output_root: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    profile = config["controller_profile"]
    ppo = config["ppo"]
    env = config["env"]
    obstacle = env["obstacle"]
    run_dir = training_output_root / "profiles" / profile_name / f"seed_{int(seed_id)}"
    checkpoint_path = training_output_root / "checkpoints" / profile_name / f"seed_{int(seed_id)}" / "checkpoint.pt"
    return {
        "matrix_id": f"{profile_name}::seed_{int(seed_id)}",
        "profile_name": profile_name,
        "seed_id": int(seed_id),
        "source_config_path": str(source_path),
        "generated_config_path": str(generated_path),
        "run_dir": str(run_dir),
        "checkpoint_path": str(checkpoint_path),
        "training_command": " ".join(
            _training_command(config_path=generated_path, run_dir=run_dir, checkpoint_path=checkpoint_path)
        ),
        **{field: ppo[field] for field in BUDGET_FIELDS},
        "track_width": float(env["track_width"]),
        "track_width_widened": False,
        "track_cost_scale": float(env["track_cost_scale"]),
        "heading_cost_scale": float(env["heading_cost_scale"]),
        "road_margin_cost_scale": float(env["road_margin_cost_scale"]),
        "road_margin_warning_fraction": float(env["road_margin_warning_fraction"]),
        "off_track_penalty": float(env["off_track_penalty"]),
        "dense_clearance_margin_reward_scale": float(obstacle["dense_clearance_margin_reward_scale"]),
        "clearance_margin_reward_scale": float(obstacle["clearance_margin_reward_scale"]),
        "collision_penalty": float(obstacle["collision_penalty"]),
        "actor_encoder": profile["actor_encoder"],
        "actor_history_length": int(profile["actor_history_length"]),
        "env_history_length": int(env["history_length"]),
        "observation_dim": int(profile["observation_dim"]),
        "input_contract": profile["input_contract"],
        "uses_hidden_oracle_actor_inputs": _bool(profile["uses_hidden_oracle_actor_inputs"]),
        "uses_wheel_or_slip_inputs": _bool(profile["uses_wheel_or_slip_inputs"]),
        "uses_reference_or_ttc_inputs": _bool(profile["uses_reference_or_ttc_inputs"]),
        "include_privileged_params": _bool(env["include_privileged_params"]),
        "wheel_observation_mode": str(env["wheel_observation_mode"]),
        "obstacle_relative_velocity_mode": str(env["obstacle_relative_velocity_mode"]),
        "training_started": False,
        "policy_action_executed": False,
        "profile_specific_tuning": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "midcourse_corridor_containment_configs_materialized",
            "admissible": True,
            "reason": "M2259 writes shared targeted containment configs and matrix artifacts only",
        },
        {"claim": "training_completed", "admissible": False, "reason": "M2259 does not execute training commands"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "no targeted-containment checkpoints exist yet"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "config materialization is not outcome evidence"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2259 runs no history intervention"},
    ]


def materialize_containment_configs(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    source_config_root: Path | str = DEFAULT_SOURCE_CONFIG_ROOT,
    training_output_root: Path | str = DEFAULT_TRAINING_OUTPUT_ROOT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    source_root = Path(source_config_root)
    training_root = Path(training_output_root)
    output.mkdir(parents=True, exist_ok=True)

    matrix_rows: list[dict[str, Any]] = []
    generated_paths: list[str] = []
    budget_signatures: set[tuple[Any, ...]] = set()
    contract_violation_count = 0
    source_missing_count = 0
    target_value_mismatch_count = 0
    track_width_widened_count = 0
    for profile_name in EXPECTED_PROFILES:
        for seed_id in EXPECTED_SEED_IDS:
            source_path_value = source_config_path(source_root, profile_name, seed_id)
            if not source_path_value.exists():
                source_missing_count += 1
                continue
            config = build_containment_config(profile_name=profile_name, seed_id=seed_id, source_config_root=source_root)
            if _contract_violation(config):
                contract_violation_count += 1
            env = config["env"]
            obstacle = env["obstacle"]
            if any(env.get(key) != value for key, value in REPAIR_ENV_OVERRIDES.items()):
                target_value_mismatch_count += 1
            if any(obstacle.get(key) != value for key, value in REPAIR_OBSTACLE_OVERRIDES.items()):
                target_value_mismatch_count += 1
            generated_path_value = generated_config_path(output, profile_name, seed_id)
            generated_path_value.parent.mkdir(parents=True, exist_ok=True)
            write_json(generated_path_value, config)
            generated_paths.append(str(generated_path_value))
            row = _matrix_row(
                profile_name=profile_name,
                seed_id=seed_id,
                source_path=source_path_value,
                generated_path=generated_path_value,
                training_output_root=training_root,
                config=config,
            )
            matrix_rows.append(row)
            budget_signatures.add(_budget_signature(row))
            if bool(row["track_width_widened"]):
                track_width_widened_count += 1

    write_csv_rows(output / "training_matrix.csv", matrix_rows, fieldnames=MATRIX_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_rows(), fieldnames=CLAIM_FIELDNAMES)
    expected_config_count = len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS)
    profile_names = tuple(sorted({str(row["profile_name"]) for row in matrix_rows}))
    seed_ids = tuple(sorted({int(row["seed_id"]) for row in matrix_rows}))
    budget_signature_count = len(budget_signatures)
    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_started": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    result_class = (
        "current_sim_midcourse_corridor_containment_config_materialization_pass"
        if (
            len(generated_paths) == expected_config_count
            and len(matrix_rows) == expected_config_count
            and source_missing_count == 0
            and profile_names == tuple(EXPECTED_PROFILES)
            and seed_ids == tuple(EXPECTED_SEED_IDS)
            and budget_signature_count == 1
            and contract_violation_count == 0
            and target_value_mismatch_count == 0
            and track_width_widened_count == 0
            and guardrail_violation_count == 0
        )
        else "current_sim_midcourse_corridor_containment_config_materialization_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "stage": "midcourse_corridor_containment_v1",
        "output_dir": str(output),
        "source_config_root": str(source_root),
        "training_output_root": str(training_root),
        "profiles": list(EXPECTED_PROFILES),
        "seed_ids": list(EXPECTED_SEED_IDS),
        "expected_config_count": expected_config_count,
        "materialized_config_count": len(generated_paths),
        "training_matrix_row_count": len(matrix_rows),
        "source_missing_count": source_missing_count,
        "profile_set_matched": profile_names == tuple(EXPECTED_PROFILES),
        "seed_set_matched": seed_ids == tuple(EXPECTED_SEED_IDS),
        "budget_fields": list(BUDGET_FIELDS),
        "budget_signature_count": budget_signature_count,
        "target_reward_values": dict(REPAIR_ENV_OVERRIDES),
        "target_obstacle_reward_values": dict(REPAIR_OBSTACLE_OVERRIDES),
        "target_value_mismatch_count": target_value_mismatch_count,
        "contract_violation_count": contract_violation_count,
        "track_width_widened_count": track_width_widened_count,
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "training_started": False,
        "policy_action_executed": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "training_matrix": str(output / "training_matrix.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "run_state": str(output / "run_state.json"),
            "generated_configs": generated_paths,
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2259-paper-route-current-sim-midcourse-corridor-containment-config-materialization",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-config-root", type=Path, default=DEFAULT_SOURCE_CONFIG_ROOT)
    parser.add_argument("--training-output-root", type=Path, default=DEFAULT_TRAINING_OUTPUT_ROOT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_containment_configs(
        output_dir=args.output_dir,
        source_config_root=args.source_config_root,
        training_output_root=args.training_output_root,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"materialized_config_count={summary['materialized_config_count']}")
    print(f"training_matrix_row_count={summary['training_matrix_row_count']}")
    print(f"budget_signature_count={summary['budget_signature_count']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"target_value_mismatch_count={summary['target_value_mismatch_count']}")
    print(f"track_width_widened_count={summary['track_width_widened_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
