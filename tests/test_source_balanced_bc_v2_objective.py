import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.source_balanced_bc_v2_objective import (
    batched_actions_from_hidden,
    compute_bc_v2_row_metrics,
    model_parameter_checksum,
    summarize_bc_v2_group,
)
from autodrift.train_ppo import ActorCritic


def _arrays() -> dict[str, np.ndarray]:
    observation = np.zeros((4, 72), dtype=np.float32)
    normal_hidden = np.zeros((4, 8), dtype=np.float32)
    variant_hidden = np.ones((4, 8), dtype=np.float32) * 0.1
    base = np.zeros((4, 3, 3), dtype=np.float32)
    target = base.copy()
    target[:, 0, 0] = 0.10
    target[:, 1, 1] = -0.05
    target[1, 2, 2] = 0.08
    mask = np.array(
        [
            [1, 1, 0],
            [1, 1, 1],
            [1, 1, 0],
            [1, 1, 0],
        ],
        dtype=np.float32,
    )
    return {
        "observation": observation,
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": mask,
        "variant_base_action": np.ones((4, 3), dtype=np.float32) * 0.02,
        "weight": np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32),
        "row_id": np.arange(4, dtype=np.int64),
        "source_index": np.array([1, 1, 2, 2], dtype=np.int64),
        "sequence_length": np.array([2, 3, 2, 2], dtype=np.int64),
    }


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": [1, 1, 2, 2],
            "split": ["train", "train", "source_holdout_validation", "source_holdout_validation"],
            "surface": ["fresh", "fresh", "ood", "ood"],
            "target": ["yaw", "yaw", "braking", "braking"],
            "variant": ["delayed", "delayed", "wrong", "wrong"],
            "grid_name": ["g0", "g1", "g0", "g1"],
            "sequence_length": [2, 3, 2, 2],
            "corpus_weight": [0.25, 0.25, 0.25, 0.25],
        }
    )


def test_compute_bc_v2_row_metrics_separates_normal_and_variant_losses():
    arrays = _arrays()
    metadata = _metadata()
    normal_action = np.tile(np.array([[0.10, 0.0, 0.0]], dtype=np.float32), (4, 1))
    variant_action = np.zeros((4, 3), dtype=np.float32)

    rows = compute_bc_v2_row_metrics(
        arrays,
        metadata,
        normal_action=normal_action,
        variant_action=variant_action,
    )

    assert rows["first_action_normal_mse"].mean() == pytest.approx(0.0)
    assert rows["first_action_variant_mse"].mean() > 0.0
    assert rows["sequence_delta_mse"].min() > 0.0
    assert rows["normal_variant_gap_l2"].mean() == pytest.approx(0.10)


def test_summarize_bc_v2_group_reports_source_balanced_metrics():
    arrays = _arrays()
    rows = compute_bc_v2_row_metrics(
        arrays,
        _metadata(),
        normal_action=np.zeros((4, 3), dtype=np.float32),
        variant_action=np.ones((4, 3), dtype=np.float32) * 0.1,
    )

    source_summary = summarize_bc_v2_group(rows, "source_index")
    split_summary = summarize_bc_v2_group(rows, "split")

    assert len(source_summary) == 2
    assert {row["split"] for row in split_summary} == {"train", "source_holdout_validation"}
    assert all(row["weight_sum"] == pytest.approx(0.5) for row in source_summary)


def test_model_checksum_is_stable_for_no_update_forward():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    arrays = _arrays()
    before = model_parameter_checksum(model)

    actions = batched_actions_from_hidden(
        model,
        arrays["observation"],
        arrays["normal_hidden"],
        device=torch.device("cpu"),
        batch_size=2,
    )
    after = model_parameter_checksum(model)

    assert actions.shape == (4, 3)
    assert np.isfinite(actions).all()
    assert before == after
