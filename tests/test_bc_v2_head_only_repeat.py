import argparse

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.bc_v2_head_only_repeat import parse_seed_list, train_one_repeat_seed


def _arrays(rows: int = 16) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(7)
    observation = np.zeros((rows, 72), dtype=np.float32)
    normal_hidden = rng.normal(size=(rows, 8)).astype(np.float32) * 0.1
    base = np.zeros((rows, 3, 3), dtype=np.float32)
    target = base.copy()
    target[:, :, 0] = normal_hidden[:, :1] * 0.35
    target[:, :, 1] = normal_hidden[:, 1:2] * -0.25
    target[:, :, 2] = 0.03
    return {
        "observation": observation,
        "normal_hidden": normal_hidden,
        "variant_hidden": normal_hidden + 0.01,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": np.ones((rows, 3), dtype=np.float32),
        "variant_base_action": np.zeros((rows, 3), dtype=np.float32),
        "weight": np.full(rows, 1.0 / rows, dtype=np.float32),
        "row_id": np.arange(rows, dtype=np.int64),
        "source_index": np.repeat(np.array([1, 2], dtype=np.int64), rows // 2),
        "sequence_length": np.full(rows, 3, dtype=np.int64),
    }


def _metadata(rows: int = 16) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": np.repeat([1, 2], rows // 2),
            "split": ["train"] * (rows // 2) + ["source_holdout_validation"] * (rows // 2),
            "surface": ["fresh"] * rows,
            "target": ["yaw"] * rows,
            "variant": ["delayed"] * rows,
            "grid_name": ["g0"] * rows,
            "sequence_length": [3] * rows,
            "corpus_weight": [1.0 / rows] * rows,
        }
    )


def test_parse_seed_list_rejects_empty():
    assert parse_seed_list("1, 2,3") == (1, 2, 3)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seed_list("")


def test_train_one_repeat_seed_saves_best_and_final_heads(tmp_path):
    arrays = _arrays()
    metadata = _metadata()

    summary, metrics, _, source_summary, target_summary = train_one_repeat_seed(
        seed=11,
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        epochs=80,
        learning_rate=0.01,
        weight_decay=0.0,
        hidden_dim=16,
        device=torch.device("cpu"),
        seed_dir=tmp_path / "seed_11",
    )

    assert summary["best_head_checkpoint_written"] is True
    assert summary["final_head_checkpoint_written"] is True
    assert summary["actor_checkpoint_written"] is False
    assert summary["train_delta_mse_improvement_at_best"] > 0.3
    assert len(metrics) == 81
    assert source_summary
    assert target_summary
