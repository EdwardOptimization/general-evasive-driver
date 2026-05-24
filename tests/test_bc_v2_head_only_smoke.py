import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.bc_v2_head_only_smoke import (
    SequenceDeltaHead,
    freeze_actor,
    masked_weighted_delta_mse,
    row_delta_mse,
    train_sequence_delta_head,
)
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic


def _arrays(rows: int = 16) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    observation = np.zeros((rows, 72), dtype=np.float32)
    normal_hidden = rng.normal(size=(rows, 8)).astype(np.float32) * 0.1
    variant_hidden = normal_hidden + 0.02
    base = np.zeros((rows, 3, 3), dtype=np.float32)
    target = base.copy()
    target[:, :, 0] = normal_hidden[:, :1] * 0.4
    target[:, :, 1] = normal_hidden[:, 1:2] * -0.3
    target[:, :, 2] = 0.05
    mask = np.ones((rows, 3), dtype=np.float32)
    weights = np.full(rows, 1.0 / rows, dtype=np.float32)
    return {
        "observation": observation,
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": mask,
        "variant_base_action": np.zeros((rows, 3), dtype=np.float32),
        "weight": weights,
        "row_id": np.arange(rows, dtype=np.int64),
        "source_index": np.repeat(np.array([1, 2], dtype=np.int64), rows // 2),
        "sequence_length": np.full(rows, 3, dtype=np.int64),
    }


def _metadata(rows: int = 16) -> pd.DataFrame:
    split = ["train"] * (rows // 2) + ["source_holdout_validation"] * (rows // 2)
    return pd.DataFrame(
        {
            "source_index": np.repeat([1, 2], rows // 2),
            "split": split,
            "surface": ["fresh"] * rows,
            "target": ["yaw"] * rows,
            "variant": ["delayed"] * rows,
            "grid_name": ["g0"] * rows,
            "sequence_length": [3] * rows,
            "corpus_weight": [1.0 / rows] * rows,
        }
    )


def test_masked_weighted_delta_mse_uses_mask_and_weights():
    prediction = torch.tensor([[[1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]])
    target = torch.zeros_like(prediction)
    mask = torch.tensor([[1.0, 0.0]])
    weight = torch.tensor([2.0])

    loss = masked_weighted_delta_mse(prediction, target, mask, weight)

    assert loss.item() == pytest.approx(1.0 / 3.0)


def test_row_delta_mse_matches_masked_numpy_metric():
    prediction = np.array([[[1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]], dtype=np.float32)
    target = np.zeros_like(prediction)
    mask = np.array([[1.0, 0.0]], dtype=np.float32)

    assert row_delta_mse(prediction, target, mask)[0] == pytest.approx(1.0 / 3.0)


def test_freeze_actor_preserves_checksum_and_disables_grad():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    before = model_parameter_checksum(model)

    freeze_actor(model)

    assert all(not parameter.requires_grad for parameter in model.parameters())
    assert model_parameter_checksum(model) == before


def test_train_sequence_delta_head_reduces_synthetic_train_loss():
    arrays = _arrays()
    metadata = _metadata()
    features = arrays["normal_hidden"].copy()
    variant_features = arrays["variant_hidden"].copy()

    head, rows, summary, predictions = train_sequence_delta_head(
        arrays=arrays,
        metadata=metadata,
        features_normal=features,
        features_variant=variant_features,
        hidden_dim=16,
        epochs=120,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=7,
        device=torch.device("cpu"),
    )

    assert isinstance(head, SequenceDeltaHead)
    assert summary["train_delta_mse_improvement"] > 0.3
    assert predictions["normal_prediction"].shape == (16, 3, 3)
    assert any(row["epoch"] == 0 for row in rows)
    assert any(row["epoch"] == 120 for row in rows)
