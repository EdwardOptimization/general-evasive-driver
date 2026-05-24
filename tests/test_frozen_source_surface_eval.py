import copy
from pathlib import Path

import numpy as np
import pytest
import torch

from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.frozen_source_surface_eval import (
    BaselineCheckpointSpec,
    FrozenSourceSnapshot,
    build_offpolicy_recurrent_hidden,
    collect_frozen_source_snapshots,
    load_validated_baseline,
    observation_for_model,
    parse_baseline_checkpoint_spec,
    replay_baseline_from_snapshot,
    validate_checkpoint_metadata,
)
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


def _checkpoint_config(model: ActorCritic, level: str) -> dict:
    return {
        "actor_encoder": model.actor_encoder,
        "actor_history_length": model.actor_history_length,
        "action_sequence_horizon": model.action_sequence_horizon,
        "response_prediction_dim": model.response_prediction_dim,
        "response_prediction_horizon": model.response_prediction_horizon,
        "log_std_init": -1.0,
        "log_std_min": model.log_std_min,
        "log_std_max": model.log_std_max,
        "history_baseline_level": level,
    }


def _write_checkpoint(path: Path, model: ActorCritic, level: str) -> None:
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _checkpoint_config(model, level),
            "metadata": {
                "history_baseline": {
                    "level": level,
                    "input_contract": "P0_human_view_no_wheel_no_oracle",
                }
            },
        },
        path,
    )


def test_parse_baseline_checkpoint_spec() -> None:
    spec = parse_baseline_checkpoint_spec("l3_s3530=L3_online_gru:runs/example/checkpoint.pt")

    assert spec.label == "l3_s3530"
    assert spec.history_level == "L3_online_gru"
    assert spec.path == Path("runs/example/checkpoint.pt")


def test_validate_checkpoint_metadata_rejects_level_mismatch() -> None:
    checkpoint = {
        "config": {"history_baseline_level": "L0_current_observation"},
        "metadata": {
            "history_baseline": {
                "level": "L0_current_observation",
                "input_contract": "P0_human_view_no_wheel_no_oracle",
            }
        },
    }

    with pytest.raises(ValueError, match="does not match declared"):
        validate_checkpoint_metadata(
            checkpoint,
            BaselineCheckpointSpec("l3", "L3_online_gru", Path("checkpoint.pt")),
        )


def test_load_validated_baseline_accepts_matching_metadata(tmp_path: Path) -> None:
    model = ActorCritic(obs_dim=HUMAN_VIEW_OBS_DIM, act_dim=3, hidden_size=8, actor_encoder="mlp")
    checkpoint_path = tmp_path / "l0.pt"
    _write_checkpoint(checkpoint_path, model, "L0_current_observation")

    loaded, _, metadata = load_validated_baseline(
        BaselineCheckpointSpec("l0", "L0_current_observation", checkpoint_path),
        device=torch.device("cpu"),
    )

    assert loaded.actor_encoder == "mlp"
    assert metadata["history_level"] == "L0_current_observation"


def test_observation_for_model_stacks_temporal_history_current_first() -> None:
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM * 4,
        act_dim=3,
        hidden_size=8,
        actor_encoder="temporal_gru",
        actor_history_length=4,
    )
    base_history = tuple(np.full(HUMAN_VIEW_OBS_DIM, value, dtype=np.float32) for value in (0, 1, 2, 3))

    obs = observation_for_model(model, base_history)

    assert obs.shape == (HUMAN_VIEW_OBS_DIM * 4,)
    assert np.all(obs[:HUMAN_VIEW_OBS_DIM] == 0)
    assert np.all(obs[HUMAN_VIEW_OBS_DIM : HUMAN_VIEW_OBS_DIM * 2] == 1)


def test_build_offpolicy_recurrent_hidden_consumes_source_observation_prefix() -> None:
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )
    prefix = tuple(np.zeros(HUMAN_VIEW_OBS_DIM, dtype=np.float32) for _ in range(3))

    hidden = build_offpolicy_recurrent_hidden(model, prefix, device=torch.device("cpu"))

    assert hidden is not None
    assert hidden.shape == (1, 8)


def test_replay_baseline_from_snapshot_supports_feedforward_and_temporal_gru() -> None:
    env_config = DriftEnvConfig(max_steps=8, history_length=1)
    env = AutoDriftEnv(env_config)
    obs, info = env.reset(seed=7)
    base_history = tuple(np.asarray(obs, dtype=np.float32).copy() for _ in range(4))
    snapshot = FrozenSourceSnapshot(
        seed=7,
        step=0,
        observation=np.asarray(obs, dtype=np.float32).copy(),
        base_history=base_history,
        prefix_observations=(),
        env=copy.deepcopy(env),
        info=dict(info),
    )
    mlp = ActorCritic(obs_dim=HUMAN_VIEW_OBS_DIM, act_dim=3, hidden_size=8, actor_encoder="mlp")
    temporal = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM * 4,
        act_dim=3,
        hidden_size=8,
        actor_encoder="temporal_gru",
        actor_history_length=4,
    )

    mlp_result = replay_baseline_from_snapshot(
        model=mlp,
        snapshot=snapshot,
        max_continuation_steps=2,
        device=torch.device("cpu"),
    )
    temporal_result = replay_baseline_from_snapshot(
        model=temporal,
        snapshot=snapshot,
        max_continuation_steps=2,
        device=torch.device("cpu"),
    )

    assert mlp_result["steps"] > 0
    assert temporal_result["steps"] > 0
    env.close()


def test_collect_frozen_source_snapshots_records_history_prefix() -> None:
    source = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )

    snapshots = collect_frozen_source_snapshots(
        source_model=source,
        env_config=DriftEnvConfig(max_steps=8, history_length=1),
        requests={11: {0, 2}},
        max_history_length=4,
        device=torch.device("cpu"),
    )

    assert (11, 0) in snapshots
    assert (11, 2) in snapshots
    assert len(snapshots[(11, 2)].prefix_observations) == 2
    assert len(snapshots[(11, 2)].base_history) == 4
