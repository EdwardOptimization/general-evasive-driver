"""Generate corrected public-pilot configs for profile-control comparisons."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_profile_runtime import CURRENT_TILED_HISTORY, NO_HISTORY_TRANSFORM


SOURCE_CONFIG_DIR = Path("configs/paper_route_profiles")
DEFAULT_OUTPUT_DIR = Path("configs/paper_route_corrected_profiles")
DEFAULT_RUN_DIR = Path("runs/m1207_corrected_profile_config_generation")

TRAINING_SEED_BASE = 110600
TRAINING_SEED_OFFSETS = (0, 1, 2)
EVAL_SEED_BASE = 120600
EVAL_EPISODES_PER_CHECKPOINT = 64

PILOT_PPO_OVERRIDES: dict[str, Any] = {
    "total_steps": 8192,
    "rollout_steps": 128,
    "num_envs": 4,
    "update_epochs": 2,
    "minibatch_size": 256,
    "device": "cpu",
    "vector_env_mode": "sync",
    # Public eval is produced by the pilot runner; keep train_ppo's built-in
    # eval small so config smoke and pilot runs do not duplicate 64 episodes.
    "eval_episodes": 1,
}


@dataclass(frozen=True)
class CorrectedProfileSpec:
    name: str
    source_name: str
    source_filename: str
    current_tiled: bool = False
    corrected_reset_control: bool = False
    description: str = ""


CORRECTED_PROFILE_SPECS: tuple[CorrectedProfileSpec, ...] = (
    CorrectedProfileSpec(
        name="L0_current_masked",
        source_name="L0_current_masked",
        source_filename="m1190_l0_current_masked_smoke.json",
        description="Current-only lower anchor with previous command fields masked.",
    ),
    CorrectedProfileSpec(
        name="L1_one_step",
        source_name="L1_one_step",
        source_filename="m1190_l1_one_step_smoke.json",
        description="One-step command-response feedback profile.",
    ),
    CorrectedProfileSpec(
        name="L2_window_13",
        source_name="L2_window_13",
        source_filename="m1190_l2_window_13_smoke.json",
        description="Short finite-window command-response profile.",
    ),
    CorrectedProfileSpec(
        name="L2_window_13_current_tiled",
        source_name="L2_window_13",
        source_filename="m1190_l2_window_13_smoke.json",
        current_tiled=True,
        description="Capacity-matched L2 window-13 control with older frames replaced by the current frame.",
    ),
    CorrectedProfileSpec(
        name="L2_window_25",
        source_name="L2_window_25",
        source_filename="m1190_l2_window_25_smoke.json",
        description="Representative finite-window command-response profile from the M1199 trend.",
    ),
    CorrectedProfileSpec(
        name="L2_window_25_current_tiled",
        source_name="L2_window_25",
        source_filename="m1190_l2_window_25_smoke.json",
        current_tiled=True,
        description="Capacity-matched L2 window-25 control with older frames replaced by the current frame.",
    ),
    CorrectedProfileSpec(
        name="L3_online_gru",
        source_name="L3_online_gru",
        source_filename="m1190_l3_online_gru_smoke.json",
        description="Online GRU profile with episode-persistent recurrent hidden state.",
    ),
    CorrectedProfileSpec(
        name="L3_reset_control_corrected",
        source_name="L3_reset_control",
        source_filename="m1190_l3_reset_control_smoke.json",
        corrected_reset_control=True,
        description="Online GRU control with every-step hidden reset enforced in evaluation.",
    ),
)


def config_filename(spec: CorrectedProfileSpec) -> str:
    return f"m1207_{spec.name.lower()}.json"


def corrected_protocol() -> dict[str, Any]:
    return {
        "training_seed_base": TRAINING_SEED_BASE,
        "training_seed_offsets": list(TRAINING_SEED_OFFSETS),
        "eval_seed_base": EVAL_SEED_BASE,
        "eval_episodes_per_checkpoint": EVAL_EPISODES_PER_CHECKPOINT,
        **PILOT_PPO_OVERRIDES,
    }


def build_corrected_profile_config(
    spec: CorrectedProfileSpec,
    *,
    source_dir: Path | str = SOURCE_CONFIG_DIR,
) -> dict[str, Any]:
    source_path = Path(source_dir) / spec.source_filename
    config = deepcopy(read_json(source_path))
    profile = dict(config["controller_profile"])
    ppo = dict(config["ppo"])

    profile.update(
        {
            "name": spec.name,
            "source_profile_name": spec.source_name,
            "description": spec.description,
            "corrected_profile_config": True,
            "m1206_corrected_pilot_profile": True,
            "config_generation_only": False,
            "private_holdout_used": False,
            "history_transform": CURRENT_TILED_HISTORY if spec.current_tiled else NO_HISTORY_TRANSFORM,
            "current_tiled_history_control": bool(spec.current_tiled),
            "corrected_reset_control": bool(spec.corrected_reset_control),
        }
    )
    if spec.current_tiled:
        profile["level"] = f"{profile['level']}_current_tiled_control"
        profile["reset_hidden_policy"] = "per_decision_window"
        profile["training_enabled"] = True
        profile["is_training_profile"] = True
    if spec.corrected_reset_control:
        profile["level"] = "L3_online_gru_reset_control_corrected"
        profile["reset_hidden_policy"] = "every_step_control"
        profile["training_enabled"] = True
        profile["is_training_profile"] = True
        profile["eval_reset_hidden_policy_enforced"] = True

    ppo.update(PILOT_PPO_OVERRIDES)
    ppo["seed"] = TRAINING_SEED_BASE
    if spec.corrected_reset_control:
        ppo["recurrent_sequence_training"] = False

    config["controller_profile"] = profile
    config["ppo"] = ppo
    config["m1206_corrected_pilot_protocol"] = corrected_protocol()
    return config


def build_corrected_profile_configs(
    *,
    source_dir: Path | str = SOURCE_CONFIG_DIR,
) -> dict[str, dict[str, Any]]:
    return {spec.name: build_corrected_profile_config(spec, source_dir=source_dir) for spec in CORRECTED_PROFILE_SPECS}


def config_rows(configs: dict[str, dict[str, Any]], output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> list[dict[str, Any]]:
    output = Path(output_dir)
    rows: list[dict[str, Any]] = []
    spec_by_name = {spec.name: spec for spec in CORRECTED_PROFILE_SPECS}
    for name, config in configs.items():
        spec = spec_by_name[name]
        profile = config["controller_profile"]
        ppo = config["ppo"]
        env = config["env"]
        rows.append(
            {
                "profile_name": name,
                "source_profile_name": profile["source_profile_name"],
                "path": str(output / config_filename(spec)),
                "actor_encoder": ppo["actor_encoder"],
                "actor_history_length": ppo["actor_history_length"],
                "env_history_length": env["history_length"],
                "observation_dim": profile["observation_dim"],
                "history_transform": profile["history_transform"],
                "current_tiled_history_control": profile["current_tiled_history_control"],
                "reset_hidden_policy": profile["reset_hidden_policy"],
                "corrected_reset_control": profile["corrected_reset_control"],
                "uses_hidden_oracle_actor_inputs": profile["uses_hidden_oracle_actor_inputs"],
                "uses_wheel_or_slip_inputs": profile["uses_wheel_or_slip_inputs"],
                "uses_reference_or_ttc_inputs": profile["uses_reference_or_ttc_inputs"],
                "training_enabled": profile["training_enabled"],
                "private_holdout_used": profile["private_holdout_used"],
            }
        )
    return rows


def config_summary(configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    profile_names = list(configs)
    current_tiled_profiles = [
        name for name, config in configs.items() if config["controller_profile"]["current_tiled_history_control"]
    ]
    corrected_reset_profiles = [
        name for name, config in configs.items() if config["controller_profile"]["corrected_reset_control"]
    ]
    return {
        "result_class": "corrected_profile_configs_generated",
        "generated_config_count": len(configs),
        "profile_names": profile_names,
        "current_tiled_profiles": current_tiled_profiles,
        "corrected_reset_profiles": corrected_reset_profiles,
        "protocol": corrected_protocol(),
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


def write_corrected_profile_configs(
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    source_dir: Path | str = SOURCE_CONFIG_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    run = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)

    configs = build_corrected_profile_configs(source_dir=source_dir)
    spec_by_name = {spec.name: spec for spec in CORRECTED_PROFILE_SPECS}
    for name, config in configs.items():
        write_json(output / config_filename(spec_by_name[name]), config)

    summary = config_summary(configs)
    write_json(run / "summary.json", summary)
    write_csv_rows(run / "config_rows.csv", config_rows(configs, output))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--source-dir", type=Path, default=SOURCE_CONFIG_DIR)
    args = parser.parse_args(argv)
    write_corrected_profile_configs(output_dir=args.output_dir, run_dir=args.run_dir, source_dir=args.source_dir)
    print(f"output_dir={args.output_dir}")
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"config_rows={args.run_dir / 'config_rows.csv'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
