import argparse

import numpy as np
import pytest
import torch

from autodrift.capability_belief_objective_sanity import (
    REQUIRED_ARRAYS,
    evaluate_model,
    load_dataset_npz,
    parse_seed_list,
    split_pairs,
    train_one_seed,
    validate_dataset_contract,
)
from autodrift.capability_belief_target_dataset import CAPABILITY_TARGETS


def _synthetic_arrays(pair_count: int = 24, feature_dim: int = 8) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(123)
    latent_i = rng.normal(size=(pair_count, len(CAPABILITY_TARGETS))).astype(np.float32)
    latent_j = rng.normal(size=(pair_count, len(CAPABILITY_TARGETS))).astype(np.float32)
    x_i = np.zeros((pair_count, feature_dim), dtype=np.float32)
    x_j = np.zeros((pair_count, feature_dim), dtype=np.float32)
    x_i[:, : len(CAPABILITY_TARGETS)] = latent_i
    x_j[:, : len(CAPABILITY_TARGETS)] = latent_j
    x_i[:, len(CAPABILITY_TARGETS):] = 0.01 * rng.normal(size=(pair_count, feature_dim - len(CAPABILITY_TARGETS)))
    x_j[:, len(CAPABILITY_TARGETS):] = 0.01 * rng.normal(size=(pair_count, feature_dim - len(CAPABILITY_TARGETS)))
    y_i = (2.0 * latent_i + 0.1).astype(np.float32)
    y_j = (2.0 * latent_j + 0.1).astype(np.float32)
    pair_weight = np.linspace(1.0, 2.0, pair_count, dtype=np.float32)
    return {
        "student_p0_i": x_i,
        "student_p0_j": x_j,
        "teacher_capability_i": y_i,
        "teacher_capability_j": y_j,
        "teacher_capability_delta": (y_i - y_j).astype(np.float32),
        "teacher_capability_abs_delta_z": np.abs(y_i - y_j).astype(np.float32),
        "pair_weight": pair_weight,
        "dominant_target_index": np.arange(pair_count, dtype=np.int64) % len(CAPABILITY_TARGETS),
        "dominant_hidden_group_index": np.zeros(pair_count, dtype=np.int64),
        "hidden_group_distances": np.zeros((pair_count, 6), dtype=np.float32),
        "sample_i": np.arange(pair_count, dtype=np.int64),
        "sample_j": np.arange(pair_count, dtype=np.int64) + pair_count,
    }


def test_parse_seed_list_rejects_empty():
    assert parse_seed_list("1,2, 3") == (1, 2, 3)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_list("")


def test_validate_dataset_contract_uses_only_student_keys_as_inputs():
    arrays = _synthetic_arrays()

    contract = validate_dataset_contract(arrays)

    assert contract.student_input_keys == ("student_p0_i", "student_p0_j")
    assert "hidden_group_distances" in contract.training_metadata_keys
    assert contract.student_feature_dim == 8
    assert contract.target_dim == len(CAPABILITY_TARGETS)


def test_validate_dataset_contract_rejects_missing_array():
    arrays = _synthetic_arrays()
    arrays.pop("pair_weight")

    with pytest.raises(ValueError, match="missing arrays"):
        validate_dataset_contract(arrays)


def test_split_pairs_is_disjoint_and_nonempty():
    split = split_pairs(10, train_fraction=0.7, seed=4)

    assert len(split.train_indices) == 7
    assert len(split.val_indices) == 3
    assert not set(split.train_indices).intersection(set(split.val_indices))


def test_load_dataset_npz_validates_required_arrays(tmp_path):
    path = tmp_path / "dataset.npz"
    arrays = _synthetic_arrays()
    np.savez_compressed(path, **arrays)

    loaded = load_dataset_npz(path)

    assert set(REQUIRED_ARRAYS).issubset(loaded)


def test_evaluate_model_reports_target_and_delta_losses():
    batch = {
        "x_i": torch.zeros((2, 3)),
        "x_j": torch.zeros((2, 3)),
        "y_i": torch.zeros((2, len(CAPABILITY_TARGETS))),
        "y_j": torch.ones((2, len(CAPABILITY_TARGETS))),
        "weights": torch.ones(2),
    }

    metrics = evaluate_model(None, batch, delta_loss_coef=0.5)

    assert metrics["target_loss"] == pytest.approx(0.5)
    assert metrics["delta_loss"] == pytest.approx(1.0)
    for target in CAPABILITY_TARGETS:
        assert f"{target}_loss" in metrics
        assert f"{target}_delta_loss" in metrics


def test_train_one_seed_reduces_synthetic_validation_loss():
    arrays = _synthetic_arrays(pair_count=36, feature_dim=10)

    rows, summary = train_one_seed(
        arrays=arrays,
        optimization_seed=77,
        train_fraction=0.75,
        steps=120,
        batch_size=16,
        learning_rate=1e-3,
        weight_decay=1e-4,
        hidden_dim=24,
        delta_loss_coef=0.5,
        device=torch.device("cpu"),
    )

    assert summary["val_combined_loss_improvement"] > 0.0
    assert summary["val_target_loss_improvement"] > 0.0
    assert summary["val_delta_loss_improvement"] > 0.0
    assert any(row["phase"] == "before" and row["split"] == "val" for row in rows)
    assert any(row["phase"] == "after" and row["split"] == "val" for row in rows)
