import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.bc_v2_wrong_history_contrast import (
    per_row_masked_mse,
    seed_passes,
    train_one_contrast_seed,
    wrong_history_indices,
    wrong_history_margin_loss,
)
from autodrift.bc_v2_head_only_smoke import SequenceDeltaHead


def _arrays(rows: int = 16) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(123)
    normal_hidden = rng.normal(size=(rows, 8)).astype(np.float32) * 0.1
    variant_hidden = normal_hidden.copy()
    variant_hidden[rows // 2:] += 0.5
    base = np.zeros((rows, 3, 3), dtype=np.float32)
    target = base.copy()
    target[:, :, 0] = normal_hidden[:, :1] * 0.3
    target[:, :, 1] = -normal_hidden[:, 1:2] * 0.2
    target[:, :, 2] = 0.02
    return {
        "observation": np.zeros((rows, 72), dtype=np.float32),
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": np.ones((rows, 3), dtype=np.float32),
        "variant_base_action": np.zeros((rows, 3), dtype=np.float32),
        "weight": np.full(rows, 1.0 / rows, dtype=np.float32),
        "row_id": np.arange(rows, dtype=np.int64),
        "source_index": np.repeat([30, 32], rows // 2).astype(np.int64),
        "sequence_length": np.full(rows, 3, dtype=np.int64),
    }


def _metadata(rows: int = 16) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": np.repeat([30, 32], rows // 2),
            "split": ["train"] * (rows // 2) + ["source_holdout_validation"] * (rows // 2),
            "surface": ["ood"] * rows,
            "target": ["future_yaw_response"] * rows,
            "variant": ["wrong_matched_history"] * rows,
            "grid_name": ["g0"] * rows,
            "sequence_length": [3] * rows,
            "corpus_weight": [1.0 / rows] * rows,
        }
    )


def test_wrong_history_indices_selects_split():
    metadata = _metadata()

    assert wrong_history_indices(metadata).shape[0] == 16
    assert wrong_history_indices(metadata, "train").shape[0] == 8
    assert wrong_history_indices(metadata, "source_holdout_validation").shape[0] == 8


def test_wrong_history_margin_loss_prefers_wrong_farther_from_target():
    head = SequenceDeltaHead(feature_dim=2, hidden_dim=4, max_sequence_length=1)
    batch = {
        "features_normal": torch.zeros((2, 2)),
        "features_variant": torch.ones((2, 2)),
        "target_delta": torch.zeros((2, 1, 3)),
        "mask": torch.ones((2, 1)),
        "weight": torch.ones(2),
    }
    with torch.no_grad():
        for parameter in head.parameters():
            parameter.zero_()

    loss, d_normal, d_wrong = wrong_history_margin_loss(head, batch, np.array([0, 1]), margin_mse=0.1)

    assert torch.allclose(d_normal, torch.zeros_like(d_normal))
    assert torch.allclose(d_wrong, torch.zeros_like(d_wrong))
    assert loss.item() == pytest.approx(torch.nn.functional.softplus(torch.tensor(0.1)).item())


def test_per_row_masked_mse_uses_prefix_mask():
    prediction = torch.tensor([[[1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]])
    target = torch.zeros_like(prediction)
    mask = torch.tensor([[1.0, 0.0]])

    row = per_row_masked_mse(prediction, target, mask)

    assert row.item() == pytest.approx(1.0 / 3.0)


def test_seed_passes_thresholds():
    assert seed_passes(
        {
            "actor_parameters_changed": False,
            "best_head_checkpoint_written": True,
            "actor_checkpoint_written": False,
            "normal_validation_delta_mse": 0.0009,
            "wrong_train_gap_mse": 0.0003,
            "wrong_validation_gap_mse": 0.0002,
            "wrong_train_prediction_gap_l2": 0.02,
            "wrong_validation_prediction_gap_l2": 0.01,
        }
    )
    assert not seed_passes(
        {
            "actor_parameters_changed": False,
            "best_head_checkpoint_written": True,
            "actor_checkpoint_written": False,
            "normal_validation_delta_mse": 0.0009,
            "wrong_train_gap_mse": 0.0,
            "wrong_validation_gap_mse": 0.0002,
            "wrong_train_prediction_gap_l2": 0.02,
            "wrong_validation_prediction_gap_l2": 0.01,
        }
    )


def test_train_one_contrast_seed_runs_and_writes_heads(tmp_path):
    arrays = _arrays()
    metadata = _metadata()

    summary, metrics, _, source_summary, target_summary, history_summary = train_one_contrast_seed(
        seed=6510,
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        epochs=40,
        learning_rate=0.01,
        weight_decay=0.0,
        hidden_dim=16,
        contrast_coef=1.0,
        wrong_zero_coef=0.05,
        margin_mse=0.00025,
        device=torch.device("cpu"),
        seed_dir=tmp_path / "seed_6510",
    )

    assert summary["best_head_checkpoint_written"] is True
    assert summary["final_head_checkpoint_written"] is True
    assert metrics
    assert source_summary
    assert target_summary
    assert history_summary
