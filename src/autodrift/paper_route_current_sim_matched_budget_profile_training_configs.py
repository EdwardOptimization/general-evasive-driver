"""Materialize matched-budget profile training configs without running training."""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


SOURCE_CONFIG_DIR = Path("configs/paper_route_profiles")
DEFAULT_OUTPUT_DIR = Path("runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs")
DEFAULT_CONFIG_OUTPUT_DIR = Path("configs/paper_route_profiles/m2227_matched_budget_short_v0")
DEFAULT_TRAINING_OUTPUT_ROOT = Path("runs/m2228_paper_route_current_sim_matched_budget_profile_training_execution")
DEFAULT_NEXT_BLOCKER = "m2228-paper-route-current-sim-matched-budget-profile-training-config-materialization-result-audit"

PROFILE_SOURCES = {
    "L0_current_masked": "m1190_l0_current_masked_smoke.json",
    "L1_one_step": "m1190_l1_one_step_smoke.json",
    "L2_window_25": "m1190_l2_window_25_smoke.json",
    "L2_window_50": "m1190_l2_window_50_smoke.json",
    "L3_online_gru": "m1190_l3_online_gru_smoke.json",
}
ALIAS_CONTROL_PROFILE = "L3_reset_control"
ALIAS_SOURCE_PROFILE = "L3_online_gru"
SEED_IDS = (222601, 222602, 222603)
MATCHED_BUDGET_OVERRIDES: dict[str, Any] = {
    "total_steps": 8192,
    "rollout_steps": 128,
    "num_envs": 4,
    "update_epochs": 2,
    "minibatch_size": 256,
    "learning_rate": 0.0001,
    "clip_coef": 0.1,
    "max_grad_norm": 0.25,
    "eval_episodes": 32,
    "checkpoint_interval_steps": 0,
    "device": "cpu",
    "vector_env_mode": "sync",
}
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
TRAINING_MATRIX_FIELDNAMES = [
    "matrix_id",
    "profile_name",
    "seed_id",
    "source_config_path",
    "generated_config_path",
    "run_dir",
    "checkpoint_path",
    "training_command",
    *BUDGET_FIELDS,
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
PROFILE_PLAN_FIELDNAMES = [
    "profile_name",
    "role",
    "source_profile_name",
    "trainable",
    "seed_count",
    "config_count",
    "alias_checkpoint_source_profile",
    "notes",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _profile_slug(profile_name: str) -> str:
    return profile_name.lower()


def config_filename(profile_name: str, seed_id: int) -> str:
    return f"m2227_matched_budget_short_v0_{_profile_slug(profile_name)}_seed{int(seed_id)}.json"


def _source_config_path(profile_name: str, source_config_dir: Path) -> Path:
    return source_config_dir / PROFILE_SOURCES[profile_name]


def build_matched_budget_config(
    *,
    profile_name: str,
    seed_id: int,
    source_config_dir: Path | str = SOURCE_CONFIG_DIR,
) -> dict[str, Any]:
    source_dir = Path(source_config_dir)
    config = deepcopy(read_json(_source_config_path(profile_name, source_dir)))
    profile = dict(config["controller_profile"])
    ppo = dict(config["ppo"])

    profile.update(
        {
            "matched_budget_profile_training_config": True,
            "matched_budget_stage": "matched_budget_short_v0",
            "matched_budget_seed_id": int(seed_id),
            "source_config_path": str(_source_config_path(profile_name, source_dir)),
            "config_generation_only": False,
            "training_enabled": True,
            "private_holdout_used": False,
            "profile_specific_tuning": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }
    )
    ppo.update(MATCHED_BUDGET_OVERRIDES)
    ppo["seed"] = int(seed_id)

    config["controller_profile"] = profile
    config["ppo"] = ppo
    config["matched_budget_training_protocol"] = {
        "stage": "matched_budget_short_v0",
        "primary_trainable_profiles": list(PROFILE_SOURCES),
        "alias_control_profile": ALIAS_CONTROL_PROFILE,
        "alias_source_profile": ALIAS_SOURCE_PROFILE,
        "seed_ids": list(SEED_IDS),
        "budget_overrides": dict(MATCHED_BUDGET_OVERRIDES),
        "ranking_admissible": False,
        "winner_selected": False,
        "training_started": False,
    }
    return config


def _contract_violation(config: Mapping[str, Any]) -> bool:
    profile = config.get("controller_profile", {})
    env = config.get("env", {})
    return bool(
        _bool(profile.get("uses_hidden_oracle_actor_inputs"))
        or _bool(profile.get("uses_wheel_or_slip_inputs"))
        or _bool(profile.get("uses_reference_or_ttc_inputs"))
        or _bool(env.get("include_privileged_params"))
        or str(env.get("wheel_observation_mode", "")).strip() != "none"
        or str(env.get("obstacle_relative_velocity_mode", "")).strip() != "zero"
    )


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


def _matrix_row(
    *,
    profile_name: str,
    seed_id: int,
    source_config_path: Path,
    generated_config_path: Path,
    training_output_root: Path,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    profile = config["controller_profile"]
    ppo = config["ppo"]
    env = config["env"]
    run_dir = training_output_root / "profiles" / profile_name / f"seed_{int(seed_id)}"
    checkpoint_path = training_output_root / "checkpoints" / profile_name / f"seed_{int(seed_id)}" / "checkpoint.pt"
    command = _training_command(config_path=generated_config_path, run_dir=run_dir, checkpoint_path=checkpoint_path)
    return {
        "matrix_id": f"{profile_name}::seed_{int(seed_id)}",
        "profile_name": profile_name,
        "seed_id": int(seed_id),
        "source_config_path": str(source_config_path),
        "generated_config_path": str(generated_config_path),
        "run_dir": str(run_dir),
        "checkpoint_path": str(checkpoint_path),
        "training_command": " ".join(command),
        **{field: ppo[field] for field in BUDGET_FIELDS},
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


def _profile_plan_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "profile_name": profile_name,
            "role": "primary_trainable",
            "source_profile_name": profile_name,
            "trainable": True,
            "seed_count": len(SEED_IDS),
            "config_count": len(SEED_IDS),
            "alias_checkpoint_source_profile": "",
            "notes": "matched-budget trainable profile",
        }
        for profile_name in PROFILE_SOURCES
    ]
    rows.append(
        {
            "profile_name": ALIAS_CONTROL_PROFILE,
            "role": "alias_reset_control",
            "source_profile_name": ALIAS_SOURCE_PROFILE,
            "trainable": False,
            "seed_count": 0,
            "config_count": 0,
            "alias_checkpoint_source_profile": ALIAS_SOURCE_PROFILE,
            "notes": "generated after admitted L3 checkpoint; not trained in M2227",
        }
    )
    return rows


def _claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "matched_budget_training_configs_materialized",
            "admissible": True,
            "reason": "M2227 writes config and command artifacts only",
        },
        {
            "claim": "training_completed",
            "admissible": False,
            "reason": "M2227 does not execute training commands",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "no matched-budget checkpoints or measured execution exist yet",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "config materialization is not outcome evidence",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2227 runs no history intervention",
        },
    ]


def _budget_signature(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(row[field] for field in BUDGET_FIELDS)


def materialize_matched_budget_profile_training_configs(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config_output_dir: Path | str = DEFAULT_CONFIG_OUTPUT_DIR,
    source_config_dir: Path | str = SOURCE_CONFIG_DIR,
    training_output_root: Path | str = DEFAULT_TRAINING_OUTPUT_ROOT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    configs_dir = Path(config_output_dir)
    source_dir = Path(source_config_dir)
    training_root = Path(training_output_root)
    output.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)

    matrix_rows: list[dict[str, Any]] = []
    generated_paths: list[str] = []
    contract_violation_count = 0
    budget_signature_set: set[tuple[Any, ...]] = set()
    seed_sets_by_profile: dict[str, list[int]] = {}

    for profile_name in PROFILE_SOURCES:
        seed_sets_by_profile[profile_name] = []
        for seed_id in SEED_IDS:
            config = build_matched_budget_config(profile_name=profile_name, seed_id=seed_id, source_config_dir=source_dir)
            if _contract_violation(config):
                contract_violation_count += 1
            generated_path = configs_dir / config_filename(profile_name, seed_id)
            write_json(generated_path, config)
            generated_paths.append(str(generated_path))
            row = _matrix_row(
                profile_name=profile_name,
                seed_id=seed_id,
                source_config_path=_source_config_path(profile_name, source_dir),
                generated_config_path=generated_path,
                training_output_root=training_root,
                config=config,
            )
            matrix_rows.append(row)
            budget_signature_set.add(_budget_signature(row))
            seed_sets_by_profile[profile_name].append(int(seed_id))

    profile_plan_rows = _profile_plan_rows()
    write_csv_rows(output / "training_matrix.csv", matrix_rows, fieldnames=TRAINING_MATRIX_FIELDNAMES)
    write_csv_rows(output / "profile_plan.csv", profile_plan_rows, fieldnames=PROFILE_PLAN_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", _claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    expected_config_count = len(PROFILE_SOURCES) * len(SEED_IDS)
    generated_config_count = len(generated_paths)
    budget_matched = len(budget_signature_set) == 1
    seed_policy_matched = all(tuple(seeds) == tuple(SEED_IDS) for seeds in seed_sets_by_profile.values())
    trainable_profile_count = len(PROFILE_SOURCES)
    training_matrix_row_count = len(matrix_rows)
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
        "current_sim_matched_budget_profile_training_config_materialization_pass"
        if (
            generated_config_count == expected_config_count
            and training_matrix_row_count == expected_config_count
            and budget_matched
            and seed_policy_matched
            and contract_violation_count == 0
            and guardrail_violation_count == 0
        )
        else "current_sim_matched_budget_profile_training_config_materialization_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "config_output_dir": str(configs_dir),
        "source_config_dir": str(source_dir),
        "training_output_root": str(training_root),
        "stage": "matched_budget_short_v0",
        "trainable_profiles": list(PROFILE_SOURCES),
        "alias_control_profile": ALIAS_CONTROL_PROFILE,
        "alias_source_profile": ALIAS_SOURCE_PROFILE,
        "seed_ids": list(SEED_IDS),
        "trainable_profile_count": trainable_profile_count,
        "seeds_per_profile": len(SEED_IDS),
        "expected_config_count": expected_config_count,
        "generated_config_count": generated_config_count,
        "training_matrix_row_count": training_matrix_row_count,
        "budget_fields": list(BUDGET_FIELDS),
        "budget_overrides": dict(MATCHED_BUDGET_OVERRIDES),
        "budget_signature_count": len(budget_signature_set),
        "budget_matched": budget_matched,
        "seed_policy_matched": seed_policy_matched,
        "contract_violation_count": contract_violation_count,
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
            "profile_plan": str(output / "profile_plan.csv"),
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
            "task_id": "m2227-paper-route-current-sim-matched-budget-profile-training-config-materialization",
            "status": "completed" if result_class.endswith("_pass") else "failed",
            "result_class": result_class,
            "next_blocker": next_blocker,
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config-output-dir", type=Path, default=DEFAULT_CONFIG_OUTPUT_DIR)
    parser.add_argument("--source-config-dir", type=Path, default=SOURCE_CONFIG_DIR)
    parser.add_argument("--training-output-root", type=Path, default=DEFAULT_TRAINING_OUTPUT_ROOT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = materialize_matched_budget_profile_training_configs(
        output_dir=args.output_dir,
        config_output_dir=args.config_output_dir,
        source_config_dir=args.source_config_dir,
        training_output_root=args.training_output_root,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"generated_config_count={summary['generated_config_count']}")
    print(f"training_matrix_row_count={summary['training_matrix_row_count']}")
    print(f"budget_matched={summary['budget_matched']}")
    print(f"contract_violation_count={summary['contract_violation_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
