"""Matched history-baseline metadata and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autodrift.env import DriftEnvConfig


UNSPECIFIED_HISTORY_BASELINE = "unspecified"
L0_CURRENT_OBSERVATION = "L0_current_observation"
L1_ONE_STEP_FEEDBACK = "L1_one_step_feedback"
L2_FINITE_WINDOW = "L2_finite_window"
L3_ONLINE_GRU = "L3_online_gru"

HISTORY_BASELINE_LEVELS = {
    UNSPECIFIED_HISTORY_BASELINE,
    L0_CURRENT_OBSERVATION,
    L1_ONE_STEP_FEEDBACK,
    L2_FINITE_WINDOW,
    L3_ONLINE_GRU,
}

P0_INPUT_CONTRACT = "P0_human_view_no_wheel_no_oracle"
P0_ALLOWED_INPUTS = (
    "ego_kinematics_and_imu_like_response",
    "steering_throttle_brake_actuator_state",
    "previous_physical_commands",
    "road_boundary_geometry_in_ego_frame",
    "obstacle_geometry_in_ego_frame",
)
P0_FORBIDDEN_INPUTS = (
    "hidden_physical_params",
    "wheel_or_slip_observations",
    "oracle_feasibility_labels",
    "controller_mode_or_reference_errors",
    "ttc_required_clearance_or_stopping_distance",
    "success_collision_progress_labels",
)


@dataclass(frozen=True)
class HistoryBaselineSpec:
    level: str
    explicit: bool
    input_contract: str
    actor_encoder: str
    actor_history_length: int
    env_history_length: int
    uses_recurrent_hidden: bool
    uses_finite_window: bool
    matched_baseline_ready: bool
    allowed_inputs: tuple[str, ...]
    forbidden_inputs: tuple[str, ...]
    notes: tuple[str, ...]
    limitation: str


def _require_supported_level(level: str) -> None:
    if level not in HISTORY_BASELINE_LEVELS:
        raise ValueError("history_baseline_level must be one of: " + ", ".join(sorted(HISTORY_BASELINE_LEVELS)))


def _require_p0_env_contract(env_config: DriftEnvConfig) -> None:
    if env_config.include_privileged_params:
        raise ValueError("explicit history baselines cannot include privileged params")
    if env_config.wheel_observation_mode != "none":
        raise ValueError("explicit history baselines require wheel_observation_mode='none'")
    if env_config.action_history_mode != "full":
        raise ValueError("explicit history baselines currently require action_history_mode='full'")
    if env_config.road_lookahead_count != 8 or env_config.obstacle_slots != 4:
        raise ValueError("explicit history baselines require the canonical 72-value P0 frame")


def build_history_baseline_spec(
    *,
    level: str,
    actor_encoder: str,
    actor_history_length: int,
    env_config: DriftEnvConfig,
) -> HistoryBaselineSpec:
    """Validate and describe a matched history-baseline configuration."""

    _require_supported_level(level)
    actor_history_length = int(actor_history_length)
    if level == UNSPECIFIED_HISTORY_BASELINE:
        return HistoryBaselineSpec(
            level=level,
            explicit=False,
            input_contract="legacy_or_unclassified",
            actor_encoder=str(actor_encoder),
            actor_history_length=actor_history_length,
            env_history_length=int(env_config.history_length),
            uses_recurrent_hidden=str(actor_encoder).endswith("online_gru") or str(actor_encoder) == "online_gru",
            uses_finite_window=str(actor_encoder) == "temporal_gru",
            matched_baseline_ready=False,
            allowed_inputs=(),
            forbidden_inputs=(),
            notes=("no explicit matched-history baseline contract declared",),
            limitation="No matched history-baseline level was declared.",
        )

    _require_p0_env_contract(env_config)

    uses_recurrent = False
    uses_window = False
    matched_ready = True
    limitation = ""
    if level == L0_CURRENT_OBSERVATION:
        if actor_encoder != "mlp":
            raise ValueError("L0_current_observation requires actor_encoder='mlp'")
        if env_config.history_length != 1:
            raise ValueError("L0_current_observation requires env history_length=1")
        limitation = "Feedforward current-frame baseline; current P0 frame still includes deployable previous-command fields."
    elif level == L1_ONE_STEP_FEEDBACK:
        if actor_encoder != "mlp":
            raise ValueError("L1_one_step_feedback requires actor_encoder='mlp'")
        if env_config.history_length != 1:
            raise ValueError("L1_one_step_feedback requires env history_length=1")
        limitation = "One-step feedback baseline; no multi-step recurrent or finite-window memory."
    elif level == L2_FINITE_WINDOW:
        if actor_encoder != "temporal_gru":
            raise ValueError("L2_finite_window requires actor_encoder='temporal_gru'")
        if env_config.history_length <= 1:
            raise ValueError("L2_finite_window requires env history_length > 1")
        if actor_history_length != env_config.history_length:
            raise ValueError("L2_finite_window requires actor_history_length == env history_length")
        uses_window = True
        limitation = "Finite-window baseline; no online recurrent hidden state."
    elif level == L3_ONLINE_GRU:
        if actor_encoder != "human_view_online_gru":
            raise ValueError("L3_online_gru requires actor_encoder='human_view_online_gru'")
        if env_config.history_length != 1:
            raise ValueError("L3_online_gru requires env history_length=1")
        uses_recurrent = True
        limitation = "Mainline online GRU recurrent-belief policy."
    else:  # pragma: no cover - safeguarded by _require_supported_level
        raise ValueError(f"unsupported history baseline level: {level}")

    return HistoryBaselineSpec(
        level=level,
        explicit=True,
        input_contract=P0_INPUT_CONTRACT,
        actor_encoder=str(actor_encoder),
        actor_history_length=actor_history_length,
        env_history_length=int(env_config.history_length),
        uses_recurrent_hidden=uses_recurrent,
        uses_finite_window=uses_window,
        matched_baseline_ready=matched_ready,
        allowed_inputs=P0_ALLOWED_INPUTS,
        forbidden_inputs=P0_FORBIDDEN_INPUTS,
        notes=("explicit matched-history baseline metadata only; actor observation contract is unchanged",),
        limitation=limitation,
    )


def history_baseline_spec_to_dict(spec: HistoryBaselineSpec) -> dict[str, Any]:
    return {
        "level": spec.level,
        "explicit": spec.explicit,
        "input_contract": spec.input_contract,
        "actor_encoder": spec.actor_encoder,
        "actor_history_length": spec.actor_history_length,
        "env_history_length": spec.env_history_length,
        "uses_recurrent_hidden": spec.uses_recurrent_hidden,
        "uses_finite_window": spec.uses_finite_window,
        "matched_baseline_ready": spec.matched_baseline_ready,
        "allowed_inputs": list(spec.allowed_inputs),
        "forbidden_inputs": list(spec.forbidden_inputs),
        "notes": list(spec.notes),
        "limitation": spec.limitation,
    }
