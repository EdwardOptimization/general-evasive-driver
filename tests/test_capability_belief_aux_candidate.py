import numpy as np
import torch

from autodrift.capability_belief_aux_candidate import (
    _feature_anchor_loss,
    save_checkpoint_like,
    summarize_candidate_seed,
    train_one_candidate_seed,
)
from autodrift.capability_belief_hidden_integration import p0_history_sequences
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


def _checkpoint(path, hidden_size=24):
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=hidden_size,
        actor_encoder="human_view_online_gru",
    )
    config = {
        "actor_encoder": "human_view_online_gru",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    torch.save({"model_state": model.state_dict(), "config": config, "metadata": {"test": True}}, path)
    return model, {"config": config}


def _synthetic_arrays(pair_count: int = 36, history_window: int = 4) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(789)
    feature_dim = history_window * HUMAN_VIEW_OBS_DIM
    x_i = np.zeros((pair_count, feature_dim), dtype=np.float32)
    x_j = np.zeros((pair_count, feature_dim), dtype=np.float32)
    for target_index in range(len(CAPABILITY_TARGETS)):
        x_i[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM + target_index] = rng.normal(size=pair_count)
        x_j[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM + target_index] = rng.normal(size=pair_count)
    y_i = 1.25 * x_i[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM:(history_window - 1) * HUMAN_VIEW_OBS_DIM + len(CAPABILITY_TARGETS)] - 0.1
    y_j = 1.25 * x_j[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM:(history_window - 1) * HUMAN_VIEW_OBS_DIM + len(CAPABILITY_TARGETS)] - 0.1
    return {
        "student_p0_i": x_i.astype(np.float32),
        "student_p0_j": x_j.astype(np.float32),
        "teacher_capability_i": y_i.astype(np.float32),
        "teacher_capability_j": y_j.astype(np.float32),
        "teacher_capability_delta": (y_i - y_j).astype(np.float32),
        "teacher_capability_abs_delta_z": np.abs(y_i - y_j).astype(np.float32),
        "pair_weight": np.linspace(1.0, 2.0, pair_count, dtype=np.float32),
        "dominant_target_index": np.arange(pair_count, dtype=np.int64) % len(CAPABILITY_TARGETS),
        "dominant_hidden_group_index": np.zeros(pair_count, dtype=np.int64),
        "hidden_group_distances": np.zeros((pair_count, 6), dtype=np.float32),
        "sample_i": np.arange(pair_count, dtype=np.int64),
        "sample_j": np.arange(pair_count, dtype=np.int64) + pair_count,
    }


def test_save_checkpoint_like_preserves_config_and_metadata(tmp_path):
    checkpoint = tmp_path / "source.pt"
    model, source = _checkpoint(checkpoint)
    out = tmp_path / "out.pt"

    save_checkpoint_like(model, source, out, {"run_type": "test"})

    loaded, data = load_actor_critic_checkpoint(out, device="cpu")
    assert loaded.actor_encoder == "human_view_online_gru"
    assert data["metadata"]["run_type"] == "test"


def test_feature_anchor_loss_is_zero_for_identical_models(tmp_path):
    checkpoint = tmp_path / "source.pt"
    _, _ = _checkpoint(checkpoint)
    model, _ = load_actor_critic_checkpoint(checkpoint, device="cpu")
    reference, _ = load_actor_critic_checkpoint(checkpoint, device="cpu")
    seq = torch.as_tensor(p0_history_sequences(np.zeros((2, 4 * HUMAN_VIEW_OBS_DIM), dtype=np.float32), 4))

    loss = _feature_anchor_loss(model, reference, seq, seq, "response_hidden")

    assert float(loss.item()) == 0.0


def test_summarize_candidate_seed_reports_improvements():
    rows = [
        {"optimization_seed": 1, "phase": "before", "split": "train", "combined_loss": 2.0, "target_loss": 1.0, "delta_loss": 2.0, "feature_anchor_loss": 0.0, **{f"{target}_loss": 1.0 for target in CAPABILITY_TARGETS}, **{f"{target}_delta_loss": 1.0 for target in CAPABILITY_TARGETS}},
        {"optimization_seed": 1, "phase": "after", "split": "train", "combined_loss": 1.0, "target_loss": 0.5, "delta_loss": 1.0, "feature_anchor_loss": 0.1, **{f"{target}_loss": 0.5 for target in CAPABILITY_TARGETS}, **{f"{target}_delta_loss": 0.5 for target in CAPABILITY_TARGETS}},
        {"optimization_seed": 1, "phase": "before", "split": "val", "combined_loss": 2.0, "target_loss": 1.0, "delta_loss": 2.0, "feature_anchor_loss": 0.0, **{f"{target}_loss": 1.0 for target in CAPABILITY_TARGETS}, **{f"{target}_delta_loss": 1.0 for target in CAPABILITY_TARGETS}},
        {"optimization_seed": 1, "phase": "after", "split": "val", "combined_loss": 1.0, "target_loss": 0.5, "delta_loss": 1.0, "feature_anchor_loss": 0.2, **{f"{target}_loss": 0.5 for target in CAPABILITY_TARGETS}, **{f"{target}_delta_loss": 0.5 for target in CAPABILITY_TARGETS}},
    ]

    summary = summarize_candidate_seed(rows, 1)

    assert summary["val_combined_loss_improvement"] == 1.0
    assert summary["val_anchor_loss_after"] == 0.2
    assert summary["objective_seed_pass"]


def test_train_one_candidate_seed_creates_objective_signal(tmp_path):
    checkpoint = tmp_path / "source.pt"
    _checkpoint(checkpoint)
    arrays = _synthetic_arrays(pair_count=36, history_window=4)

    _, _, _, summary = train_one_candidate_seed(
        checkpoint_path=checkpoint,
        arrays=arrays,
        optimization_seed=91,
        train_fraction=0.75,
        steps=120,
        batch_size=16,
        learning_rate=1e-3,
        weight_decay=1e-4,
        history_window=4,
        feature_source="response_hidden",
        delta_loss_coef=0.5,
        anchor_coef=0.1,
        device=torch.device("cpu"),
    )

    assert summary["val_combined_loss_improvement"] > 0.0
    assert summary["val_target_loss_improvement"] > 0.0
    assert summary["val_delta_loss_improvement"] > 0.0
