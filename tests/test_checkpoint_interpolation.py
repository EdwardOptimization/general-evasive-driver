import numpy as np
import torch

from autodrift.checkpoint_interpolation import (
    interpolate_model_states,
    write_interpolated_checkpoint,
    write_interpolation_sweep,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic


def _model_config(**overrides):
    config = {
        "device": "cpu",
        "actor_encoder": "mlp",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    config.update(overrides)
    return config


def _write_checkpoint(path, state, config=None, metadata=None):
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in state.items()},
            "config": config or _model_config(),
            "metadata": metadata or {},
        },
        path,
    )


def _target_state_from(base_state, delta):
    return {key: value.detach().cpu() + delta for key, value in base_state.items()}


def test_interpolated_checkpoint_preserves_loadable_actor_contract(tmp_path):
    base_model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    base_state = base_model.state_dict()
    target_state = _target_state_from(base_state, 2.0)
    base_path = tmp_path / "base.pt"
    target_path = tmp_path / "target.pt"
    output_path = tmp_path / "interpolated.pt"
    _write_checkpoint(base_path, base_state)
    _write_checkpoint(target_path, target_state)

    row = write_interpolated_checkpoint(
        base_checkpoint_path=base_path,
        target_checkpoint_path=target_path,
        output_path=output_path,
        alpha=0.25,
        base_label="m37_102",
        target_label="m56_028",
        policy_label="m59_a250",
    )

    loaded, checkpoint = load_actor_critic_checkpoint(output_path, device="cpu")
    interpolated_state = checkpoint["model_state"]
    assert row["policy_label"] == "m59_a250"
    assert loaded.obs_dim == 13
    assert checkpoint["metadata"]["interpolation"]["alpha"] == 0.25
    assert checkpoint["metadata"]["interpolation"]["base_label"] == "m37_102"
    for key, base_tensor in base_state.items():
        np.testing.assert_allclose(interpolated_state[key], base_tensor + 0.5, atol=1e-6)


def test_interpolate_model_states_rejects_key_mismatch():
    base_state = {"a": torch.zeros(2)}
    target_state = {"b": torch.zeros(2)}

    with np.testing.assert_raises(ValueError):
        interpolate_model_states(base_state, target_state, alpha=0.5)


def test_interpolate_model_states_rejects_shape_mismatch():
    base_state = {"a": torch.zeros(2)}
    target_state = {"a": torch.zeros(3)}

    with np.testing.assert_raises(ValueError):
        interpolate_model_states(base_state, target_state, alpha=0.5)


def test_interpolate_model_states_rejects_changed_nonfloating_tensor():
    base_state = {"a": torch.tensor([1], dtype=torch.int64)}
    target_state = {"a": torch.tensor([2], dtype=torch.int64)}

    with np.testing.assert_raises(ValueError):
        interpolate_model_states(base_state, target_state, alpha=0.5)


def test_interpolation_sweep_writes_manifest_and_policy_args(tmp_path):
    model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    base_state = model.state_dict()
    target_state = _target_state_from(base_state, 1.0)
    base_path = tmp_path / "base.pt"
    target_path = tmp_path / "target.pt"
    _write_checkpoint(base_path, base_state)
    _write_checkpoint(target_path, target_state)

    manifest = write_interpolation_sweep(
        run_dir=tmp_path / "sweep",
        base_checkpoint_path=base_path,
        target_checkpoint_path=target_path,
        alphas=[0.125, 0.5],
        base_label="base",
        target_label="target",
        label_prefix="m59",
    )

    assert manifest["count"] == 2
    assert [row["policy_label"] for row in manifest["checkpoints"]] == ["m59_a125", "m59_a500"]
    assert (tmp_path / "sweep" / "manifest.json").exists()
    assert (tmp_path / "sweep" / "checkpoint_policies.csv").exists()
    policy_args = (tmp_path / "sweep" / "checkpoint_policy_args.txt").read_text(encoding="utf-8")
    assert "--checkpoint-policy m59_a125=" in policy_args


def test_interpolation_sweep_preserves_micro_alpha_precision(tmp_path):
    model = ActorCritic(obs_dim=13, act_dim=2, hidden_size=16)
    base_state = model.state_dict()
    target_state = _target_state_from(base_state, 1.0)
    base_path = tmp_path / "base.pt"
    target_path = tmp_path / "target.pt"
    _write_checkpoint(base_path, base_state)
    _write_checkpoint(target_path, target_state)

    manifest = write_interpolation_sweep(
        run_dir=tmp_path / "micro_sweep",
        base_checkpoint_path=base_path,
        target_checkpoint_path=target_path,
        alphas=[0.0001, 0.00025, 0.0005, 0.0025, 0.125, 0.5],
        base_label="base",
        target_label="target",
        label_prefix="m251",
    )

    rows = manifest["checkpoints"]
    labels = [row["policy_label"] for row in rows]
    paths = [row["path"] for row in rows]
    assert len(set(labels)) == len(labels)
    assert len(set(paths)) == len(paths)
    assert labels[:4] == ["m251_a0_0001", "m251_a0_00025", "m251_a0_0005", "m251_a0_0025"]
    assert labels[-2:] == ["m251_a125", "m251_a500"]
    assert [path.rsplit("/", 1)[-1] for path in paths[:4]] == [
        "alpha_0_0001.pt",
        "alpha_0_00025.pt",
        "alpha_0_0005.pt",
        "alpha_0_0025.pt",
    ]
