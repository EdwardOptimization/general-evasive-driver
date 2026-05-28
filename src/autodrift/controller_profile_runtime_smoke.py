"""No-training runtime smoke for generated controller-profile configs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config
from autodrift.controller_profile_runtime import (
    CURRENT_TILED_HISTORY,
    mask_spec_from_config,
    profile_runtime_summary,
    wrap_env_with_profile_mask,
)
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import ActorPolicy
from autodrift.train_ppo import ActorCritic


DEFAULT_CONFIG_DIR = Path("configs/paper_route_profiles")
DEFAULT_RUN_DIR = Path("runs/m1192_controller_profile_runtime_smoke")
CONFIG_GLOB = "m1190_*_smoke.json"
SMOKE_ACTION = np.array([0.5, 0.2, -0.3], dtype=np.float32)


def generated_config_paths(config_dir: Path | str = DEFAULT_CONFIG_DIR, config_glob: str = CONFIG_GLOB) -> list[Path]:
    paths = sorted(Path(config_dir).glob(config_glob))
    if not paths:
        raise FileNotFoundError(f"no generated profile configs found under {config_dir}")
    return paths


def _build_model(config: dict[str, Any], obs_dim: int, act_dim: int) -> ActorCritic:
    ppo = config.get("ppo", {})
    return ActorCritic(
        obs_dim=int(obs_dim),
        act_dim=int(act_dim),
        hidden_size=int(ppo.get("hidden_size", 64)),
        actor_encoder=str(ppo.get("actor_encoder", "mlp")),
        actor_history_length=int(ppo.get("actor_history_length", 1)),
        action_sequence_horizon=int(ppo.get("action_sequence_horizon", 1)),
    )


def _previous_command_abs_sum(obs: np.ndarray, indices: tuple[int, ...]) -> float:
    if not indices:
        return 0.0
    return float(np.abs(obs[list(indices)]).sum())


def _is_current_tiled(obs: np.ndarray, frame_dim: int) -> bool:
    if obs.shape[-1] % frame_dim != 0:
        return False
    frame_count = obs.shape[-1] // frame_dim
    if frame_count <= 1:
        return True
    frames = obs.reshape(frame_count, frame_dim)
    return bool(np.allclose(frames[1:, :], frames[0:1, :]))


class _ResetPolicySpyModel:
    is_online_recurrent = True
    action_sequence_horizon = 1

    def __init__(self, action_dim: int):
        self.action_dim = int(action_dim)
        self.hidden_inputs: list[Any] = []

    def act_recurrent(
        self,
        observation: np.ndarray,
        hidden: Any,
        deterministic: bool = True,
    ) -> tuple[np.ndarray, None, None, str]:
        del observation, deterministic
        self.hidden_inputs.append(hidden)
        return np.zeros(self.action_dim, dtype=np.float32), None, None, "next_hidden"


def _reset_policy_routing_ok(config: dict[str, Any], runtime: dict[str, Any], obs_dim: int, act_dim: int) -> bool:
    profile = config["controller_profile"]
    if not bool(profile.get("corrected_reset_control", False)):
        return True
    if runtime.get("reset_hidden_policy") != "every_step_control":
        return False
    model = _ResetPolicySpyModel(act_dim)
    policy = ActorPolicy(
        model,  # type: ignore[arg-type]
        build_env_config(config["env"]),
        reset_hidden_policy=str(runtime["reset_hidden_policy"]),
    )
    policy.hidden = "existing_hidden"
    policy.act(np.zeros(obs_dim, dtype=np.float32), {})
    return bool(model.hidden_inputs == [None])


def smoke_one_profile(config_path: Path | str, *, seed: int = 1192) -> dict[str, Any]:
    config_path = Path(config_path)
    config = read_json(config_path)
    profile = config["controller_profile"]
    runtime = profile_runtime_summary(config)
    spec = mask_spec_from_config(config)

    raw_env = AutoDriftEnv(build_env_config(config["env"]))
    wrapped_env = wrap_env_with_profile_mask(AutoDriftEnv(build_env_config(config["env"])), config)

    raw_reset_obs, _ = raw_env.reset(seed=seed)
    wrapped_reset_obs, _ = wrapped_env.reset(seed=seed)
    raw_step_obs, *_ = raw_env.step(SMOKE_ACTION)
    wrapped_step_obs, *_ = wrapped_env.step(SMOKE_ACTION)

    obs_dim = int(wrapped_env.observation_space.shape[0])
    act_dim = int(wrapped_env.action_space.shape[0])
    model = _build_model(config, obs_dim, act_dim)
    if model.is_online_recurrent:
        action, _, _, _ = model.act_recurrent(wrapped_reset_obs, deterministic=True)
    else:
        action, _, _ = model.act(wrapped_reset_obs, deterministic=True)

    raw_step_command_sum = _previous_command_abs_sum(raw_step_obs, spec.previous_command_mask_indices)
    wrapped_step_command_sum = _previous_command_abs_sum(wrapped_step_obs, spec.previous_command_mask_indices)
    previous_command_mask_expected = bool(spec.previous_command_mask_indices)
    reset_mask_ok = (not spec.enabled) or bool(
        np.allclose(wrapped_reset_obs[list(spec.previous_command_mask_indices)], 0.0)
    )
    step_mask_ok = (not spec.enabled) or bool(
        np.allclose(wrapped_step_obs[list(spec.previous_command_mask_indices)], 0.0)
    )
    previous_command_mask_observed = (not previous_command_mask_expected) or bool(
        step_mask_ok and raw_step_command_sum > 1.0e-6 and wrapped_step_command_sum == 0.0
    )
    current_tiled_expected = spec.history_transform == CURRENT_TILED_HISTORY
    frame_dim = int(spec.frame_dim)
    raw_reset_current_tiled = _is_current_tiled(raw_reset_obs, frame_dim)
    wrapped_reset_current_tiled = _is_current_tiled(wrapped_reset_obs, frame_dim)
    raw_step_current_tiled = _is_current_tiled(raw_step_obs, frame_dim)
    wrapped_step_current_tiled = _is_current_tiled(wrapped_step_obs, frame_dim)
    current_tiled_reset_ok = (not current_tiled_expected) or wrapped_reset_current_tiled
    current_tiled_step_ok = (not current_tiled_expected) or wrapped_step_current_tiled
    current_tiled_observed = (not current_tiled_expected) or bool(
        wrapped_step_current_tiled and not raw_step_current_tiled
    )
    mask_observed = bool(previous_command_mask_observed and current_tiled_observed)
    unmasked_unchanged = bool(
        spec.enabled
        or (
            np.allclose(wrapped_reset_obs, raw_reset_obs)
            and np.allclose(wrapped_step_obs, raw_step_obs)
        )
    )
    contract_ok = bool(
        profile.get("uses_hidden_oracle_actor_inputs") is False
        and profile.get("uses_wheel_or_slip_inputs") is False
        and profile.get("uses_reference_or_ttc_inputs") is False
        and config["env"].get("include_privileged_params") is False
        and config["env"].get("wheel_observation_mode") == "none"
        and runtime["hidden_or_oracle_actor_inputs"] is False
        and runtime["wheel_or_slip_actor_inputs"] is False
    )
    obs_dim_matches = bool(obs_dim == int(profile["observation_dim"]))
    action_shape_ok = bool(tuple(action.shape) == (act_dim,))
    reset_policy_routing_ok = _reset_policy_routing_ok(config, runtime, obs_dim, act_dim)
    row_pass = bool(
        reset_mask_ok
        and step_mask_ok
        and mask_observed
        and current_tiled_reset_ok
        and current_tiled_step_ok
        and unmasked_unchanged
        and contract_ok
        and obs_dim_matches
        and action_shape_ok
        and reset_policy_routing_ok
    )

    raw_env.close()
    wrapped_env.close()

    return {
        "profile_name": profile["name"],
        "config_path": str(config_path),
        "actor_encoder": profile["actor_encoder"],
        "actor_history_length": int(profile["actor_history_length"]),
        "env_history_length": int(config["env"]["history_length"]),
        "observation_dim": obs_dim,
        "profile_observation_dim": int(profile["observation_dim"]),
        "action_dim": act_dim,
        "mask_enabled": spec.enabled,
        "observation_mask": spec.observation_mask,
        "history_transform": spec.history_transform,
        "reset_hidden_policy": spec.reset_hidden_policy,
        "previous_command_mask_indices": list(spec.previous_command_mask_indices),
        "reset_mask_ok": reset_mask_ok,
        "step_mask_ok": step_mask_ok,
        "mask_observed": mask_observed,
        "previous_command_mask_observed": previous_command_mask_observed,
        "current_tiled_expected": current_tiled_expected,
        "raw_reset_current_tiled": raw_reset_current_tiled,
        "wrapped_reset_current_tiled": wrapped_reset_current_tiled,
        "raw_step_current_tiled": raw_step_current_tiled,
        "wrapped_step_current_tiled": wrapped_step_current_tiled,
        "current_tiled_reset_ok": current_tiled_reset_ok,
        "current_tiled_step_ok": current_tiled_step_ok,
        "current_tiled_observed": current_tiled_observed,
        "reset_policy_routing_ok": reset_policy_routing_ok,
        "raw_step_previous_command_abs_sum": raw_step_command_sum,
        "wrapped_step_previous_command_abs_sum": wrapped_step_command_sum,
        "unmasked_unchanged": unmasked_unchanged,
        "obs_dim_matches_profile": obs_dim_matches,
        "model_forward_ok": action_shape_ok,
        "contract_ok": contract_ok,
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "candidate_replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "passed": row_pass,
    }


def run_runtime_smoke(
    *,
    config_dir: Path | str = DEFAULT_CONFIG_DIR,
    run_dir: Path | str = DEFAULT_RUN_DIR,
    config_glob: str = CONFIG_GLOB,
    seed: int = 1192,
) -> dict[str, Any]:
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = generated_config_paths(config_dir, config_glob=config_glob)
    rows = [smoke_one_profile(path, seed=seed) for path in paths]
    l0_rows = [row for row in rows if row["profile_name"] == "L0_current_masked"]
    unmasked_rows = [row for row in rows if not row["mask_enabled"]]
    current_tiled_rows = [row for row in rows if row["current_tiled_expected"]]
    corrected_reset_rows = [row for row in rows if row["profile_name"] == "L3_reset_control_corrected"]

    summary = {
        "result_class": "controller_profile_runtime_smoke_pass" if all(row["passed"] for row in rows) else "controller_profile_runtime_smoke_fail",
        "generated_at_utc": utc_timestamp(),
        "config_dir": str(config_dir),
        "config_glob": str(config_glob),
        "config_count": len(rows),
        "profile_names": [row["profile_name"] for row in rows],
        "all_configs_instantiated": bool(all(row["passed"] for row in rows)),
        "l0_mask_observed": bool(l0_rows and all(row["mask_observed"] for row in l0_rows)),
        "unmasked_profiles_unchanged": bool(unmasked_rows and all(row["unmasked_unchanged"] for row in unmasked_rows)),
        "current_tiled_profile_count": len(current_tiled_rows),
        "current_tiled_profiles_observed": bool(current_tiled_rows and all(row["current_tiled_observed"] for row in current_tiled_rows)),
        "corrected_reset_profile_count": len(corrected_reset_rows),
        "corrected_reset_policy_routing_ok": bool(
            corrected_reset_rows and all(row["reset_policy_routing_ok"] for row in corrected_reset_rows)
        ),
        "contract_ok": bool(all(row["contract_ok"] for row in rows)),
        "model_forward_ok": bool(all(row["model_forward_ok"] for row in rows)),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "candidate_replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "actor_input_contract_changed": False,
        "rows_csv": str(output / "profile_runtime_rows.csv"),
        "summary_json": str(output / "summary.json"),
    }
    write_csv_rows(output / "profile_runtime_rows.csv", rows)
    write_json(output / "summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--config-glob", default=CONFIG_GLOB)
    parser.add_argument("--seed", type=int, default=1192)
    args = parser.parse_args(argv)
    summary = run_runtime_smoke(config_dir=args.config_dir, run_dir=args.run_dir, config_glob=args.config_glob, seed=args.seed)
    print(f"summary={summary['summary_json']}")
    print(f"rows={summary['rows_csv']}")
    print(f"result_class={summary['result_class']}")
    return 0 if summary["all_configs_instantiated"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
