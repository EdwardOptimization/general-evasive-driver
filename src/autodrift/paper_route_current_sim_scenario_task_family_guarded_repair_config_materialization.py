"""Materialize guarded repair configs for the scenario task-family route."""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.paper_route_current_sim_training_stability_repair_execution import EXPECTED_PROFILES, EXPECTED_SEED_IDS


DEFAULT_SOURCE_CONFIG_ROOT = Path("runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs")
DEFAULT_REPAIR_GATE_SPEC = Path(
    "runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs")
DEFAULT_TRAINING_OUTPUT_ROOT = Path("runs/m2303_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution")
DEFAULT_NEXT_BLOCKER = "m2303-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-design"

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
    "track_cost_scale": 3.4,
    "heading_cost_scale": 0.35,
    "road_margin_cost_scale": 3.4,
    "road_margin_warning_fraction": 0.45,
    "off_track_penalty": 10.0,
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
    "termination_penalty",
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
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
    "repair_gate_spec_encoded",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def source_config_path(root: Path | str, profile_name: str, seed_id: int) -> Path:
    return Path(root) / str(profile_name) / f"seed_{int(seed_id)}" / "config.json"


def generated_config_path(output_dir: Path | str, profile_name: str, seed_id: int) -> Path:
    return Path(output_dir) / "configs" / str(profile_name) / f"seed_{int(seed_id)}" / "config.json"


def _training_command(*, config_path: Path, run_dir: Path, checkpoint_path: Path) -> str:
    return " ".join(
        [
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
    )


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


def _gate_counts(repair_gate_spec: Mapping[str, Any]) -> dict[str, int]:
    offtrack_policy = repair_gate_spec.get("offtrack_target_policy", {})
    collision_policy = repair_gate_spec.get("collision_guardrail_policy", {})
    return {
        "offtrack_target_slice_count": int(offtrack_policy.get("target_slice_count", 0) or 0),
        "collision_guardrail_slice_count": int(collision_policy.get("guardrail_slice_count", 0) or 0),
    }


def build_guarded_repair_config(
    *,
    profile_name: str,
    seed_id: int,
    repair_gate_spec: Mapping[str, Any],
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
        raise ValueError("M2302 must not widen track_width")
    build_env_config(env)

    gate_counts = _gate_counts(repair_gate_spec)
    profile = dict(config["controller_profile"])
    profile.update(
        {
            "scenario_task_family_guarded_repair_config": True,
            "matched_budget_stage": "scenario_task_family_guarded_repair_v2",
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
    config["scenario_task_family_guarded_repair_protocol"] = {
        "stage": "scenario_task_family_guarded_repair_v2",
        "source_stage": str(config.get("midcourse_corridor_containment_repair_protocol", {}).get("stage", "")),
        "source_config_path": str(source_path),
        "profiles": list(EXPECTED_PROFILES),
        "seed_ids": list(EXPECTED_SEED_IDS),
        "reward_overrides": dict(REPAIR_ENV_OVERRIDES),
        "obstacle_reward_overrides": dict(REPAIR_OBSTACLE_OVERRIDES),
        "repair_gate_spec_encoded": True,
        "offtrack_target_slice_count": gate_counts["offtrack_target_slice_count"],
        "collision_guardrail_slice_count": gate_counts["collision_guardrail_slice_count"],
        "track_width_widened": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "training_started": False,
        "acceptance_criteria": {
            "target_episode_count": int(
                repair_gate_spec.get("completeness_policy", {}).get("target_episode_count", 1080) or 1080
            ),
            "reduce_global_offtrack_count": bool(
                repair_gate_spec.get("offtrack_target_policy", {}).get("reduce_global_offtrack_count", True)
            ),
            "reduce_or_hold_target_slice_offtrack_count": bool(
                repair_gate_spec.get("offtrack_target_policy", {}).get(
                    "reduce_or_hold_target_slice_offtrack_count", True
                )
            ),
            "do_not_increase_global_collision_count": bool(
                repair_gate_spec.get("collision_guardrail_policy", {}).get(
                    "do_not_increase_global_collision_count", True
                )
            ),
            "do_not_increase_guardrail_slice_collision_count": bool(
                repair_gate_spec.get("collision_guardrail_policy", {}).get(
                    "do_not_increase_guardrail_slice_collision_count", True
                )
            ),
            "return_improvement_alone_sufficient": False,
        },
    }
    return config


def _budget_signature(config: Mapping[str, Any]) -> tuple[Any, ...]:
    ppo = config["ppo"]
    return tuple(ppo[field] for field in BUDGET_FIELDS)


def _reward_changed(source: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    source_env = source["env"]
    repaired_env = repaired["env"]
    source_obstacle = source_env.get("obstacle", {})
    repaired_obstacle = repaired_env.get("obstacle", {})
    for key, value in REPAIR_ENV_OVERRIDES.items():
        if source_env.get(key) != value or repaired_env.get(key) != value:
            return True
    for key, value in REPAIR_OBSTACLE_OVERRIDES.items():
        if source_obstacle.get(key) != value or repaired_obstacle.get(key) != value:
            return True
    return False


def _matrix_row(
    *,
    profile_name: str,
    seed_id: int,
    source_path: Path,
    generated_path: Path,
    training_output_root: Path,
    source_config: Mapping[str, Any],
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
        "training_command": _training_command(config_path=generated_path, run_dir=run_dir, checkpoint_path=checkpoint_path),
        **{field: ppo[field] for field in BUDGET_FIELDS},
        "track_width": float(env["track_width"]),
        "track_width_widened": float(env["track_width"]) != float(source_config["env"]["track_width"]),
        "track_cost_scale": float(env["track_cost_scale"]),
        "heading_cost_scale": float(env["heading_cost_scale"]),
        "road_margin_cost_scale": float(env["road_margin_cost_scale"]),
        "road_margin_warning_fraction": float(env["road_margin_warning_fraction"]),
        "off_track_penalty": float(env["off_track_penalty"]),
        "termination_penalty": float(env["termination_penalty"]),
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
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "repair_gate_spec_encoded": True,
    }


def _claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "guarded_repair_configs_materialized",
            "admissible": True,
            "reason": "M2302 writes shared guarded repair configs and matrix artifacts only",
        },
        {"claim": "training_completed", "admissible": False, "reason": "M2302 does not execute training commands"},
        {"claim": "controller_family_ranking", "admissible": False, "reason": "no guarded-repair checkpoints exist yet"},
        {"claim": "finite_window_vs_gru_conclusion", "admissible": False, "reason": "config materialization is not outcome evidence"},
        {"claim": "level3_self_identification", "admissible": False, "reason": "M2302 runs no history intervention"},
    ]


def materialize_guarded_repair_configs(
    *,
    source_config_root: Path | str = DEFAULT_SOURCE_CONFIG_ROOT,
    repair_gate_spec_path: Path | str = DEFAULT_REPAIR_GATE_SPEC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    training_output_root: Path | str = DEFAULT_TRAINING_OUTPUT_ROOT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    source_root = Path(source_config_root)
    training_root = Path(training_output_root)
    output.mkdir(parents=True, exist_ok=True)
    repair_gate_spec = read_json(repair_gate_spec_path)
    copied_gate_spec_path = output / "repair_gate_spec.json"
    write_json(copied_gate_spec_path, repair_gate_spec)

    matrix_rows: list[dict[str, Any]] = []
    generated_paths: list[str] = []
    budget_signatures: set[tuple[Any, ...]] = set()
    contract_violation_count = 0
    track_width_widened_count = 0
    reward_changed_count = 0
    profile_specific_tuning_count = 0
    ranking_admissible_count = 0
    winner_selected_count = 0

    for profile_name in EXPECTED_PROFILES:
        for seed_id in EXPECTED_SEED_IDS:
            source_path = source_config_path(source_root, profile_name, int(seed_id))
            source_config = read_json(source_path)
            config = build_guarded_repair_config(
                profile_name=profile_name,
                seed_id=int(seed_id),
                repair_gate_spec=repair_gate_spec,
                source_config_root=source_root,
            )
            generated_path = generated_config_path(output, profile_name, int(seed_id))
            write_json(generated_path, config)
            generated_paths.append(str(generated_path))
            budget_signatures.add(_budget_signature(config))
            contract_violation_count += int(_contract_violation(config))
            track_width_widened = float(config["env"]["track_width"]) != float(source_config["env"]["track_width"])
            track_width_widened_count += int(track_width_widened)
            reward_changed_count += int(_reward_changed(source_config, config))
            profile_specific_tuning_count += int(_bool(config["controller_profile"].get("profile_specific_tuning")))
            ranking_admissible_count += int(_bool(config["controller_profile"].get("ranking_admissible")))
            winner_selected_count += int(_bool(config["controller_profile"].get("winner_selected")))
            matrix_rows.append(
                _matrix_row(
                    profile_name=profile_name,
                    seed_id=int(seed_id),
                    source_path=source_path,
                    generated_path=generated_path,
                    training_output_root=training_root,
                    source_config=source_config,
                    config=config,
                )
            )

    write_csv_rows(output / "training_matrix.csv", matrix_rows, fieldnames=MATRIX_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_rows(), fieldnames=CLAIM_FIELDNAMES)
    write_json(
        output / "generated_config_paths.json",
        {"generated_config_paths": generated_paths},
    )

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "scenario_specs_changed": False,
        "track_width_widened": track_width_widened_count > 0,
        "profile_specific_tuning": profile_specific_tuning_count > 0,
        "controller_family_ranking_claim_made": False,
        "winner_selected": winner_selected_count > 0,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    profile_names = sorted({str(row["profile_name"]) for row in matrix_rows})
    seed_ids = sorted({int(row["seed_id"]) for row in matrix_rows})
    repair_gate_spec_copied = copied_gate_spec_path.exists()
    passes = (
        len(matrix_rows) == len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS)
        and len(profile_names) == len(EXPECTED_PROFILES)
        and len(seed_ids) == len(EXPECTED_SEED_IDS)
        and len(budget_signatures) == 1
        and contract_violation_count == 0
        and track_width_widened_count == 0
        and reward_changed_count == len(matrix_rows)
        and profile_specific_tuning_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and repair_gate_spec_copied
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_guarded_repair_config_materialization_pass"
            if passes
            else "current_sim_scenario_task_family_guarded_repair_config_materialization_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "source_config_root": str(source_root),
        "repair_gate_spec_path": str(repair_gate_spec_path),
        "output_dir": str(output),
        "training_output_root": str(training_root),
        "config_count": len(matrix_rows),
        "target_config_count": len(EXPECTED_PROFILES) * len(EXPECTED_SEED_IDS),
        "profile_count": len(profile_names),
        "target_profile_count": len(EXPECTED_PROFILES),
        "seed_count": len(seed_ids),
        "target_seed_count": len(EXPECTED_SEED_IDS),
        "budget_signature_count": len(budget_signatures),
        "actor_contract_violation_count": contract_violation_count,
        "track_width_widened_count": track_width_widened_count,
        "reward_changed_config_count": reward_changed_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "repair_gate_spec_copied": repair_gate_spec_copied,
        **_gate_counts(repair_gate_spec),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "scenario_specs_changed": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "training_matrix": str(output / "training_matrix.csv"),
            "generated_config_paths": str(output / "generated_config_paths.json"),
            "repair_gate_spec": str(copied_gate_spec_path),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-config-root", type=Path, default=DEFAULT_SOURCE_CONFIG_ROOT)
    parser.add_argument("--repair-gate-spec", type=Path, default=DEFAULT_REPAIR_GATE_SPEC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--training-output-root", type=Path, default=DEFAULT_TRAINING_OUTPUT_ROOT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_guarded_repair_configs(
        source_config_root=args.source_config_root,
        repair_gate_spec_path=args.repair_gate_spec,
        output_dir=args.output_dir,
        training_output_root=args.training_output_root,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"config_count={summary['config_count']}")
    print(f"budget_signature_count={summary['budget_signature_count']}")
    print(f"actor_contract_violation_count={summary['actor_contract_violation_count']}")
    print(f"track_width_widened_count={summary['track_width_widened_count']}")
    print(f"reward_changed_config_count={summary['reward_changed_config_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
