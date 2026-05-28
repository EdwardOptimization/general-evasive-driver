"""Controller-profile metadata for paper-route L0/L1/L2/L3 comparisons."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.env import DriftEnvConfig
from autodrift.history_baselines import (
    L0_CURRENT_OBSERVATION,
    L1_ONE_STEP_FEEDBACK,
    L2_FINITE_WINDOW,
    L3_ONLINE_GRU,
    P0_ALLOWED_INPUTS,
    P0_FORBIDDEN_INPUTS,
)


HUMAN_VIEW_OBS_DIM = 72
HUMAN_VIEW_RESPONSE_FEATURE_DIM = 12
PREVIOUS_COMMAND_INDICES = (9, 10, 11)
FINITE_WINDOW_STEPS = (13, 25, 50, 100)
CONTROL_DT_SECONDS = 0.02

NO_MASK = "none"
ZERO_PREVIOUS_COMMANDS = "zero_previous_command_fields"


@dataclass(frozen=True)
class ControllerProfile:
    """A deployable controller profile for fair L0/L1/L2/L3 comparison."""

    name: str
    level: str
    actor_encoder: str
    env_history_length: int
    actor_history_length: int
    history_baseline_level: str
    observation_mask: str = NO_MASK
    previous_command_mask_indices: tuple[int, ...] = ()
    uses_recurrent_hidden: bool = False
    uses_finite_window: bool = False
    reset_hidden_policy: str = "not_applicable"
    window_steps: int = 1
    window_seconds: float = 0.02
    description: str = ""

    @property
    def observation_dim(self) -> int:
        return HUMAN_VIEW_OBS_DIM * int(self.env_history_length)

    @property
    def is_training_profile(self) -> bool:
        return self.reset_hidden_policy != "every_step_control"


def _finite_window_profile(steps: int) -> ControllerProfile:
    return ControllerProfile(
        name=f"L2_window_{steps}",
        level="L2_finite_window",
        actor_encoder="temporal_gru",
        env_history_length=int(steps),
        actor_history_length=int(steps),
        history_baseline_level=L2_FINITE_WINDOW,
        uses_finite_window=True,
        reset_hidden_policy="per_decision_window",
        window_steps=int(steps),
        window_seconds=round(float(steps) * CONTROL_DT_SECONDS, 2),
        description="Finite-window command-response profile with no online recurrent hidden state.",
    )


def all_profiles() -> tuple[ControllerProfile, ...]:
    """Return the canonical paper-route controller profiles."""

    return (
        ControllerProfile(
            name="L0_current_masked",
            level="L0_current_observation",
            actor_encoder="mlp",
            env_history_length=1,
            actor_history_length=1,
            history_baseline_level=L0_CURRENT_OBSERVATION,
            observation_mask=ZERO_PREVIOUS_COMMANDS,
            previous_command_mask_indices=PREVIOUS_COMMAND_INDICES,
            window_steps=1,
            window_seconds=CONTROL_DT_SECONDS,
            description="Current-only profile with previous physical commands masked to zero.",
        ),
        ControllerProfile(
            name="L1_one_step",
            level="L1_one_step_feedback",
            actor_encoder="mlp",
            env_history_length=1,
            actor_history_length=1,
            history_baseline_level=L1_ONE_STEP_FEEDBACK,
            window_steps=1,
            window_seconds=CONTROL_DT_SECONDS,
            description="Canonical one-step command-response feedback profile.",
        ),
        *(_finite_window_profile(steps) for steps in FINITE_WINDOW_STEPS),
        ControllerProfile(
            name="L3_online_gru",
            level="L3_online_gru",
            actor_encoder="human_view_online_gru",
            env_history_length=1,
            actor_history_length=1,
            history_baseline_level=L3_ONLINE_GRU,
            uses_recurrent_hidden=True,
            reset_hidden_policy="episode_persistent",
            window_steps=1,
            window_seconds=CONTROL_DT_SECONDS,
            description="Online GRU profile with episode-persistent recurrent hidden state.",
        ),
        ControllerProfile(
            name="L3_reset_control",
            level="L3_online_gru_reset_control",
            actor_encoder="human_view_online_gru",
            env_history_length=1,
            actor_history_length=1,
            history_baseline_level=L3_ONLINE_GRU,
            observation_mask=NO_MASK,
            uses_recurrent_hidden=True,
            reset_hidden_policy="every_step_control",
            window_steps=1,
            window_seconds=CONTROL_DT_SECONDS,
            description="Online GRU architecture with hidden state reset for recurrent-memory control.",
        ),
    )


def profile_names() -> tuple[str, ...]:
    return tuple(profile.name for profile in all_profiles())


def get_profile(name: str) -> ControllerProfile:
    for profile in all_profiles():
        if profile.name == name:
            return profile
    raise ValueError("unknown controller profile: " + str(name))


def profile_env_config(profile: ControllerProfile, base: DriftEnvConfig | None = None) -> DriftEnvConfig:
    """Return a contract-clean env config for a controller profile."""

    source = base or DriftEnvConfig()
    return DriftEnvConfig(
        dt=source.dt,
        max_steps=source.max_steps,
        track_kind=source.track_kind,
        track_radius=source.track_radius,
        track_width=source.track_width,
        speed_range=source.speed_range,
        beta_target_range=source.beta_target_range,
        termination_penalty=source.termination_penalty,
        friction_limited_speed=source.friction_limited_speed,
        friction_speed_margin=source.friction_speed_margin,
        history_length=int(profile.env_history_length),
        action_history_mode="full",
        include_privileged_params=False,
        privileged_observation_mode="basic",
        obstacle_relative_velocity_mode="zero",
        wheel_observation_mode="none",
        road_lookahead_count=8,
        road_lookahead_spacing=source.road_lookahead_spacing,
        obstacle_slots=4,
        friction_step=source.friction_step,
        obstacle=source.obstacle,
        randomization=source.randomization,
    )


def profile_ppo_overrides(profile: ControllerProfile, hidden_size: int = 64) -> dict[str, Any]:
    """Return PPO config fields needed to instantiate the profile."""

    return {
        "actor_encoder": profile.actor_encoder,
        "actor_history_length": int(profile.actor_history_length),
        "history_baseline_level": profile.history_baseline_level,
        "hidden_size": int(hidden_size),
        "recurrent_sequence_training": bool(profile.uses_recurrent_hidden and profile.reset_hidden_policy != "every_step_control"),
    }


def apply_observation_mask(profile: ControllerProfile, observation: np.ndarray) -> np.ndarray:
    """Apply profile observation masking without changing the actor contract."""

    obs = np.asarray(observation, dtype=np.float32).copy()
    if profile.observation_mask == NO_MASK:
        return obs
    if profile.observation_mask != ZERO_PREVIOUS_COMMANDS:
        raise ValueError(f"unknown observation mask: {profile.observation_mask}")
    frame_dim = HUMAN_VIEW_OBS_DIM
    if obs.shape[-1] % frame_dim != 0:
        raise ValueError("observation length must be divisible by the human-view frame dimension")
    frame_count = obs.shape[-1] // frame_dim
    for frame_index in range(frame_count):
        offset = frame_index * frame_dim
        for index in profile.previous_command_mask_indices:
            obs[..., offset + int(index)] = 0.0
    return obs


def profile_contract(profile: ControllerProfile) -> dict[str, Any]:
    return {
        "input_contract": "P0_human_view_no_wheel_no_oracle",
        "allowed_inputs": list(P0_ALLOWED_INPUTS),
        "forbidden_inputs": list(P0_FORBIDDEN_INPUTS),
        "uses_hidden_oracle_actor_inputs": False,
        "uses_wheel_or_slip_inputs": False,
        "uses_reference_or_ttc_inputs": False,
        "observation_mask": profile.observation_mask,
        "previous_command_mask_indices": list(profile.previous_command_mask_indices),
    }


def profile_to_row(profile: ControllerProfile) -> dict[str, Any]:
    row = asdict(profile)
    row["observation_dim"] = profile.observation_dim
    row["allowed_inputs"] = ";".join(P0_ALLOWED_INPUTS)
    row["forbidden_inputs"] = ";".join(P0_FORBIDDEN_INPUTS)
    row["uses_hidden_oracle_actor_inputs"] = False
    row["uses_wheel_or_slip_inputs"] = False
    row["uses_reference_or_ttc_inputs"] = False
    row["is_training_profile"] = profile.is_training_profile
    return row


def profile_summary() -> dict[str, Any]:
    profiles = all_profiles()
    return {
        "result_class": "controller_profile_scaffold_ready",
        "profile_count": len(profiles),
        "profile_names": list(profile_names()),
        "finite_window_steps": list(FINITE_WINDOW_STEPS),
        "l0_previous_command_mask_indices": list(PREVIOUS_COMMAND_INDICES),
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


def write_profile_smoke(run_dir: Path | str) -> None:
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "summary.json", profile_summary())
    rows = [profile_to_row(profile) for profile in all_profiles()]
    write_csv_rows(output / "profile_rows.csv", rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    write_profile_smoke(args.run_dir)
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"profile_rows={args.run_dir / 'profile_rows.csv'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
