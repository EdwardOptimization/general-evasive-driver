"""Generate contract-clean smoke configs for paper-route controller profiles."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_profiles import (
    ControllerProfile,
    all_profiles,
    profile_contract,
    profile_env_config,
    profile_ppo_overrides,
    profile_to_row,
)


DEFAULT_BASE_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_OUTPUT_DIR = Path("configs/paper_route_profiles")
DEFAULT_RUN_DIR = Path("runs/m1190_controller_profile_config_generation")

PPO_SMOKE_TEMPLATE: dict[str, Any] = {
    "total_steps": 1024,
    "rollout_steps": 64,
    "num_envs": 2,
    "update_epochs": 1,
    "minibatch_size": 128,
    "learning_rate": 0.0001,
    "clip_coef": 0.10,
    "max_grad_norm": 0.25,
    "eval_episodes": 5,
    "checkpoint_interval_steps": 0,
    "device": "cpu",
}


def config_filename(profile: ControllerProfile) -> str:
    return f"m1190_{profile.name.lower()}_smoke.json"


def _controller_profile_metadata(profile: ControllerProfile) -> dict[str, Any]:
    metadata = profile_to_row(profile)
    metadata.update(profile_contract(profile))
    metadata["training_enabled"] = bool(profile.is_training_profile)
    metadata["config_generation_only"] = True
    metadata["private_holdout_used"] = False
    return metadata


def build_profile_config(
    profile: ControllerProfile,
    *,
    base_config_data: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    """Build a JSON-serializable smoke config for one profile."""

    base_env = build_env_config(deepcopy(base_config_data.get("env", {})))
    env_config = profile_env_config(profile, base_env)

    ppo = dict(PPO_SMOKE_TEMPLATE)
    ppo.update(profile_ppo_overrides(profile))
    ppo["seed"] = int(seed)

    return {
        "controller_profile": _controller_profile_metadata(profile),
        "ppo": ppo,
        "env": env_config_to_dict(env_config),
    }


def build_all_profile_configs(base_config_path: Path | str = DEFAULT_BASE_CONFIG) -> dict[str, dict[str, Any]]:
    base_config_data = read_json(base_config_path)
    configs: dict[str, dict[str, Any]] = {}
    for index, profile in enumerate(all_profiles()):
        configs[profile.name] = build_profile_config(
            profile,
            base_config_data=base_config_data,
            seed=119000 + index,
        )
    return configs


def config_summary(configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    profile_names = list(configs)
    l2_windows = [
        int(config["controller_profile"]["window_steps"])
        for name, config in configs.items()
        if name.startswith("L2_window_")
    ]
    l0_config = configs["L0_current_masked"]["controller_profile"]
    return {
        "result_class": "controller_profile_configs_generated",
        "generated_config_count": len(configs),
        "profile_names": profile_names,
        "l2_window_steps": sorted(l2_windows),
        "l0_observation_mask": l0_config["observation_mask"],
        "l0_previous_command_mask_indices": l0_config["previous_command_mask_indices"],
        "hidden_or_oracle_actor_inputs": False,
        "wheel_or_slip_actor_inputs": False,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "candidate_replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
    }


def config_rows(configs: dict[str, dict[str, Any]], output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    output = Path(output_dir)
    for name, config in configs.items():
        profile = config["controller_profile"]
        ppo = config["ppo"]
        env = config["env"]
        rows.append(
            {
                "profile_name": name,
                "path": str(output / config_filename(get_profile_from_config_name(name))),
                "level": profile["level"],
                "actor_encoder": ppo["actor_encoder"],
                "actor_history_length": ppo["actor_history_length"],
                "history_baseline_level": ppo["history_baseline_level"],
                "env_history_length": env["history_length"],
                "observation_mask": profile["observation_mask"],
                "training_enabled": profile["training_enabled"],
                "uses_hidden_oracle_actor_inputs": profile["uses_hidden_oracle_actor_inputs"],
                "wheel_observation_mode": env.get("wheel_observation_mode", "none"),
                "private_holdout_used": profile["private_holdout_used"],
            }
        )
    return rows


def get_profile_from_config_name(name: str) -> ControllerProfile:
    for profile in all_profiles():
        if profile.name == name:
            return profile
    raise ValueError(f"unknown profile config name: {name}")


def write_generated_configs(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    base_config_path: Path | str = DEFAULT_BASE_CONFIG,
) -> dict[str, Any]:
    output = Path(output_dir)
    run = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)

    configs = build_all_profile_configs(base_config_path)
    for name, config in configs.items():
        profile = get_profile_from_config_name(name)
        write_json(output / config_filename(profile), config)

    summary = config_summary(configs)
    write_json(run / "summary.json", summary)
    write_csv_rows(run / "config_rows.csv", config_rows(configs, output))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE_CONFIG)
    args = parser.parse_args(argv)
    write_generated_configs(output_dir=args.output_dir, run_dir=args.run_dir, base_config_path=args.base_config)
    print(f"output_dir={args.output_dir}")
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"config_rows={args.run_dir / 'config_rows.csv'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
