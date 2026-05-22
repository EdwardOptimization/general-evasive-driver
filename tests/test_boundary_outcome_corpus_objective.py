import argparse

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.boundary_outcome_corpus_objective import (
    REQUIRED_CORPUS_ARRAYS,
    boundary_outcome_corpus_arrays,
    boundary_outcome_metadata,
    boundary_outcome_weight,
    load_corpus_npz,
    outcome_score,
    parse_seed_list,
    physical_pair_key,
    select_boundary_outcome_rows,
    split_groups,
    train_one_seed,
    validate_corpus_arrays,
)


def _boundary_row(
    *,
    variant: str = "wrong_matched_history",
    accepted: bool = True,
    checkpoint_label: str = "m156_s20",
    target: str = "braking",
    left_step: int = 10,
    right_step: int = 20,
    margin_gap: float = 0.03,
    success_drop: bool = True,
) -> dict[str, object]:
    return {
        "variant": variant,
        "accepted": accepted,
        "checkpoint_label": checkpoint_label,
        "target": target,
        "left_seed": 1,
        "right_seed": 2,
        "left_step": left_step,
        "right_step": right_step,
        "relocated_obstacle_body_x": 8.0,
        "relocated_obstacle_body_y": -0.5,
        "relocated_obstacle_half_width": 0.8,
        "normal_margin": 0.04,
        "variant_margin": 0.04 - margin_gap,
        "normal_success": True,
        "variant_success": not success_drop,
        "success_drop": success_drop,
        "margin_gap": margin_gap,
        "normal_first_steer": 0.1,
        "normal_first_throttle": -0.2,
        "normal_first_brake": 0.3,
    }


def _example(index: int, *, group_index: int, target_index: int) -> dict[str, object]:
    return {
        "row_id": index,
        "checkpoint_label": "m156_s20",
        "target": "braking",
        "target_index": target_index,
        "physical_pair_key": f"{group_index}:10:{group_index + 100}:20",
        "group_index": group_index,
        "left_seed": group_index,
        "right_seed": group_index + 100,
        "left_step": 10,
        "right_step": 20,
        "normal_margin": 0.04,
        "wrong_history_margin": -0.01,
        "margin_gap": 0.05,
        "normal_success": True,
        "wrong_history_success": False,
        "success_drop": True,
        "preferred_score": 1.04,
        "rejected_score": -0.01,
        "score_delta": 1.05,
        "weight": 0.1,
        "observation": np.full(4, index, dtype=np.float32),
        "preferred_hidden": np.full(3, index + 1, dtype=np.float32),
        "rejected_hidden": np.full(3, -index - 1, dtype=np.float32),
        "preferred_action": np.zeros(2, dtype=np.float32),
    }


def _synthetic_arrays(pair_count: int = 36, obs_dim: int = 6, hidden_dim: int = 4) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(123)
    group_index = np.arange(pair_count, dtype=np.int64)
    target_index = group_index % 3
    observation = rng.normal(size=(pair_count, obs_dim)).astype(np.float32) * 0.05
    latent = rng.normal(size=(pair_count, 1)).astype(np.float32)
    preferred_hidden = np.zeros((pair_count, hidden_dim), dtype=np.float32)
    rejected_hidden = np.zeros((pair_count, hidden_dim), dtype=np.float32)
    preferred_hidden[:, :1] = latent + 0.7
    rejected_hidden[:, :1] = latent - 0.7
    preferred_score = (preferred_hidden[:, 0] + 0.2 * observation[:, 0]).astype(np.float32)
    rejected_score = (rejected_hidden[:, 0] + 0.2 * observation[:, 0]).astype(np.float32)
    return {
        "observation": observation,
        "preferred_hidden": preferred_hidden,
        "rejected_hidden": rejected_hidden,
        "preferred_action": np.zeros((pair_count, 3), dtype=np.float32),
        "weight": np.ones(pair_count, dtype=np.float32),
        "preferred_score": preferred_score,
        "rejected_score": rejected_score,
        "score_delta": (preferred_score - rejected_score).astype(np.float32),
        "group_index": group_index,
        "target_index": target_index,
    }


def test_parse_seed_list_rejects_empty():
    assert parse_seed_list("1,2, 3") == (1, 2, 3)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_list("")


def test_outcome_score_and_weight_prefer_successful_normal_history():
    assert outcome_score(True, 0.5, success_bonus=1.0, margin_clip=0.2) == pytest.approx(1.2)
    assert outcome_score(False, -0.5, success_bonus=1.0, margin_clip=0.2) == pytest.approx(-0.2)

    drop = boundary_outcome_weight(
        normal_margin=0.04,
        wrong_margin=-0.02,
        normal_success=True,
        wrong_success=False,
        min_margin_gap=0.0,
        boundary_margin_scale=0.20,
        success_drop_bonus=1.0,
    )
    no_drop = boundary_outcome_weight(
        normal_margin=0.04,
        wrong_margin=-0.02,
        normal_success=True,
        wrong_success=True,
        min_margin_gap=0.0,
        boundary_margin_scale=0.20,
        success_drop_bonus=1.0,
    )

    assert drop > no_drop > 0.0


def test_select_boundary_outcome_rows_filters_and_caps_by_physical_pair():
    frame = pd.DataFrame(
        [
            _boundary_row(left_step=10, right_step=20, margin_gap=0.01),
            _boundary_row(left_step=10, right_step=20, margin_gap=0.04),
            _boundary_row(left_step=11, right_step=21, margin_gap=0.03),
            _boundary_row(variant="reset_hidden", left_step=12, right_step=22),
            _boundary_row(accepted=False, left_step=13, right_step=23),
            _boundary_row(checkpoint_label="m142_a400", left_step=14, right_step=24),
        ]
    )

    selected = select_boundary_outcome_rows(
        frame,
        checkpoint_label="m156_s20",
        accepted_only=True,
        min_margin_gap=0.0,
        max_rows_per_physical_pair=1,
        max_rows_per_target=0,
    )

    assert len(selected) == 2
    assert selected.iloc[0]["margin_gap"] == pytest.approx(0.04)
    assert {physical_pair_key(row) for _, row in selected.iterrows()} == {"1:10:2:20", "1:11:2:21"}


def test_boundary_outcome_arrays_and_metadata_separate_tensor_payloads():
    examples = [_example(0, group_index=0, target_index=0), _example(1, group_index=1, target_index=1), _example(2, group_index=2, target_index=0), _example(3, group_index=3, target_index=1)]

    arrays = boundary_outcome_corpus_arrays(examples)
    metadata = boundary_outcome_metadata(examples)
    contract = validate_corpus_arrays(arrays)

    assert set(REQUIRED_CORPUS_ARRAYS).issubset(arrays)
    assert contract.rows == 4
    assert contract.obs_dim == 4
    assert contract.hidden_dim == 3
    assert "observation" not in metadata.columns
    assert metadata.loc[0, "physical_pair_key"] == "0:10:100:20"


def test_load_corpus_npz_validates_contract(tmp_path):
    arrays = _synthetic_arrays(pair_count=8)
    path = tmp_path / "corpus.npz"
    np.savez_compressed(path, **arrays)

    loaded = load_corpus_npz(path)

    assert set(REQUIRED_CORPUS_ARRAYS).issubset(loaded)


def test_split_groups_keeps_physical_pairs_disjoint():
    arrays = _synthetic_arrays(pair_count=10)
    split = split_groups(arrays["group_index"], train_fraction=0.7, seed=4)

    assert len(split.train_groups) == 7
    assert len(split.val_groups) == 3
    assert not set(split.train_groups).intersection(set(split.val_groups))


def test_train_one_seed_reduces_synthetic_boundary_outcome_loss():
    arrays = _synthetic_arrays(pair_count=40)

    rows, summary = train_one_seed(
        arrays,
        optimization_seed=77,
        train_fraction=0.75,
        steps=120,
        batch_size=16,
        learning_rate=1e-3,
        weight_decay=1e-4,
        hidden_dim=24,
        delta_loss_coef=0.5,
        rank_loss_coef=0.25,
        device=torch.device("cpu"),
    )

    assert summary["val_combined_loss_improvement"] > 0.0
    assert summary["val_delta_loss_improvement"] > 0.0
    assert summary["val_pairwise_accuracy_after"] >= 0.60
    assert any(row["phase"] == "before" and row["split"] == "val" for row in rows)
    assert any(row["phase"] == "after" and row["split"] == "val" for row in rows)
