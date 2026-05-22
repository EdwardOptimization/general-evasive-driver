import numpy as np
import pytest
import torch

from autodrift.capability_belief_hidden_integration import (
    FEATURE_SOURCES,
    evaluate_hidden_objective,
    p0_history_sequences,
    train_one_hidden_seed,
)
from autodrift.capability_belief_objective_sanity import validate_dataset_contract
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM


def _synthetic_sequence_arrays(pair_count: int = 30, history_window: int = 4) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(456)
    feature_dim = history_window * HUMAN_VIEW_OBS_DIM
    x_i = np.zeros((pair_count, feature_dim), dtype=np.float32)
    x_j = np.zeros((pair_count, feature_dim), dtype=np.float32)
    for target_index in range(len(CAPABILITY_TARGETS)):
        x_i[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM + target_index] = rng.normal(size=pair_count)
        x_j[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM + target_index] = rng.normal(size=pair_count)
    y_i = 1.5 * x_i[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM:(history_window - 1) * HUMAN_VIEW_OBS_DIM + len(CAPABILITY_TARGETS)] + 0.2
    y_j = 1.5 * x_j[:, (history_window - 1) * HUMAN_VIEW_OBS_DIM:(history_window - 1) * HUMAN_VIEW_OBS_DIM + len(CAPABILITY_TARGETS)] + 0.2
    pair_weight = np.linspace(1.0, 2.0, pair_count, dtype=np.float32)
    return {
        "student_p0_i": x_i.astype(np.float32),
        "student_p0_j": x_j.astype(np.float32),
        "teacher_capability_i": y_i.astype(np.float32),
        "teacher_capability_j": y_j.astype(np.float32),
        "teacher_capability_delta": (y_i - y_j).astype(np.float32),
        "teacher_capability_abs_delta_z": np.abs(y_i - y_j).astype(np.float32),
        "pair_weight": pair_weight,
        "dominant_target_index": np.arange(pair_count, dtype=np.int64) % len(CAPABILITY_TARGETS),
        "dominant_hidden_group_index": np.zeros(pair_count, dtype=np.int64),
        "hidden_group_distances": np.zeros((pair_count, 6), dtype=np.float32),
        "sample_i": np.arange(pair_count, dtype=np.int64),
        "sample_j": np.arange(pair_count, dtype=np.int64) + pair_count,
    }


def test_p0_history_sequences_reshapes_25_frame_contract():
    flat = np.zeros((2, 3 * HUMAN_VIEW_OBS_DIM), dtype=np.float32)
    seq = p0_history_sequences(flat, history_window=3)

    assert seq.shape == (2, 3, HUMAN_VIEW_OBS_DIM)


def test_p0_history_sequences_rejects_wrong_dim():
    flat = np.zeros((2, 11), dtype=np.float32)

    with pytest.raises(ValueError, match="feature dim"):
        p0_history_sequences(flat, history_window=3)


def test_feature_sources_are_explicit():
    assert FEATURE_SOURCES == ("response_hidden", "policy_features")


def test_evaluate_hidden_objective_reports_losses():
    arrays = _synthetic_sequence_arrays(pair_count=6, history_window=3)
    validate_dataset_contract(arrays)
    seq_i = torch.as_tensor(p0_history_sequences(arrays["student_p0_i"], 3), dtype=torch.float32)
    seq_j = torch.as_tensor(p0_history_sequences(arrays["student_p0_j"], 3), dtype=torch.float32)
    batch = type(
        "Batch",
        (),
        {
            "seq_i": seq_i,
            "seq_j": seq_j,
            "y_i": torch.as_tensor(arrays["teacher_capability_i"], dtype=torch.float32),
            "y_j": torch.as_tensor(arrays["teacher_capability_j"], dtype=torch.float32),
            "weights": torch.ones(6),
        },
    )()
    model = ActorCritic(
        obs_dim=HUMAN_VIEW_OBS_DIM,
        act_dim=3,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
    )
    from autodrift.capability_belief_hidden_integration import CapabilityBeliefHead

    head = CapabilityBeliefHead(16, len(CAPABILITY_TARGETS))

    metrics = evaluate_hidden_objective(model, head, batch, "response_hidden", delta_loss_coef=0.5)

    assert metrics["combined_loss"] > 0.0
    for target in CAPABILITY_TARGETS:
        assert f"{target}_loss" in metrics
        assert f"{target}_delta_loss" in metrics


def test_train_one_hidden_seed_reduces_synthetic_validation_loss():
    arrays = _synthetic_sequence_arrays(pair_count=36, history_window=4)

    _, summary = train_one_hidden_seed(
        arrays=arrays,
        optimization_seed=88,
        train_fraction=0.75,
        steps=160,
        batch_size=16,
        learning_rate=1e-3,
        weight_decay=1e-4,
        hidden_size=24,
        history_window=4,
        feature_source="response_hidden",
        delta_loss_coef=0.5,
        device=torch.device("cpu"),
    )

    assert summary["val_combined_loss_improvement"] > 0.0
    assert summary["val_target_loss_improvement"] > 0.0
    assert summary["val_delta_loss_improvement"] > 0.0
    assert summary["feature_source"] == "response_hidden"
