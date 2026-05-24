import pytest

from autodrift.env import DriftEnvConfig
from autodrift.history_baselines import (
    L0_CURRENT_OBSERVATION,
    L2_FINITE_WINDOW,
    L3_ONLINE_GRU,
    build_history_baseline_spec,
    history_baseline_spec_to_dict,
)


def test_l0_current_observation_validates_p0_feedforward_contract() -> None:
    spec = build_history_baseline_spec(
        level=L0_CURRENT_OBSERVATION,
        actor_encoder="mlp",
        actor_history_length=1,
        env_config=DriftEnvConfig(history_length=1),
    )

    assert spec.explicit
    assert spec.input_contract == "P0_human_view_no_wheel_no_oracle"
    assert not spec.uses_recurrent_hidden
    assert not spec.uses_finite_window
    assert spec.matched_baseline_ready
    payload = history_baseline_spec_to_dict(spec)
    assert payload["level"] == L0_CURRENT_OBSERVATION
    assert "hidden_physical_params" in payload["forbidden_inputs"]


def test_l0_current_observation_rejects_recurrent_actor() -> None:
    with pytest.raises(ValueError, match="requires actor_encoder='mlp'"):
        build_history_baseline_spec(
            level=L0_CURRENT_OBSERVATION,
            actor_encoder="human_view_online_gru",
            actor_history_length=1,
            env_config=DriftEnvConfig(history_length=1),
        )


def test_l3_online_gru_validates_mainline_recurrent_contract() -> None:
    spec = build_history_baseline_spec(
        level=L3_ONLINE_GRU,
        actor_encoder="human_view_online_gru",
        actor_history_length=1,
        env_config=DriftEnvConfig(history_length=1),
    )

    assert spec.explicit
    assert spec.uses_recurrent_hidden
    assert not spec.uses_finite_window
    assert spec.env_history_length == 1


@pytest.mark.parametrize(
    "env_config, message",
    [
        (DriftEnvConfig(include_privileged_params=True), "cannot include privileged params"),
        (DriftEnvConfig(wheel_observation_mode="front_rear"), "wheel_observation_mode='none'"),
    ],
)
def test_l3_online_gru_rejects_non_p0_inputs(env_config: DriftEnvConfig, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build_history_baseline_spec(
            level=L3_ONLINE_GRU,
            actor_encoder="human_view_online_gru",
            actor_history_length=1,
            env_config=env_config,
        )


def test_l2_finite_window_requires_matching_temporal_gru_window() -> None:
    spec = build_history_baseline_spec(
        level=L2_FINITE_WINDOW,
        actor_encoder="temporal_gru",
        actor_history_length=4,
        env_config=DriftEnvConfig(history_length=4),
    )

    assert spec.explicit
    assert not spec.uses_recurrent_hidden
    assert spec.uses_finite_window
    assert spec.env_history_length == 4


def test_l2_finite_window_rejects_history_mismatch() -> None:
    with pytest.raises(ValueError, match="actor_history_length == env history_length"):
        build_history_baseline_spec(
            level=L2_FINITE_WINDOW,
            actor_encoder="temporal_gru",
            actor_history_length=3,
            env_config=DriftEnvConfig(history_length=4),
        )
