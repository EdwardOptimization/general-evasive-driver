import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic
from autodrift.wrong_history_feature_separability_audit import (
    batched_recurrent_outputs,
    classify_signal_collapse,
    compute_row_feature_metrics,
    row_cosine_distance,
    row_l2,
    summarize_feature_group,
    weighted_median,
)


def _arrays(rows: int = 6) -> dict[str, np.ndarray]:
    observation = np.zeros((rows, 72), dtype=np.float32)
    normal_hidden = np.zeros((rows, 4), dtype=np.float32)
    variant_hidden = normal_hidden.copy()
    variant_hidden[: rows // 2, 0] = 0.2
    variant_hidden[rows // 2 :, 0] = 0.02
    base = np.zeros((rows, 3, 3), dtype=np.float32)
    target = base.copy()
    target[:, :, 0] = 0.1
    return {
        "observation": observation,
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "target_action_sequence": target,
        "normal_base_action_sequence": base,
        "sequence_mask": np.ones((rows, 3), dtype=np.float32),
        "variant_base_action": np.zeros((rows, 3), dtype=np.float32),
        "weight": np.full(rows, 1.0 / rows, dtype=np.float32),
        "row_id": np.arange(rows, dtype=np.int64),
        "source_index": np.array([30, 30, 30, 1, 1, 1], dtype=np.int64),
        "sequence_length": np.full(rows, 3, dtype=np.int64),
    }


def _metadata(rows: int = 6) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": [30, 30, 30, 1, 1, 1],
            "split": ["train", "train", "train", "source_holdout_validation", "source_holdout_validation", "source_holdout_validation"],
            "surface": ["s"] * rows,
            "target": ["t"] * rows,
            "variant": ["wrong_matched_history"] * (rows // 2) + ["delayed_history"] * (rows // 2),
            "grid_name": ["g"] * rows,
            "sequence_length": [3] * rows,
            "corpus_weight": [1.0 / rows] * rows,
        }
    )


def _outputs(rows: int = 6, feature_gap: float = 0.1, action_gap: float = 0.02) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    normal = {
        "features": np.zeros((rows, 4), dtype=np.float32),
        "next_hidden": np.zeros((rows, 4), dtype=np.float32),
        "actor_mean": np.zeros((rows, 3), dtype=np.float32),
        "actor_action": np.zeros((rows, 3), dtype=np.float32),
    }
    variant = {key: value.copy() for key, value in normal.items()}
    variant["features"][:, 0] = feature_gap
    variant["next_hidden"][:, 0] = feature_gap
    variant["actor_mean"][:, 0] = action_gap
    variant["actor_action"][:, 0] = action_gap
    return normal, variant


def test_row_distance_helpers():
    left = np.array([[1.0, 0.0], [0.0, 0.0]])
    right = np.array([[0.0, 1.0], [0.0, 0.0]])

    assert row_l2(left, right)[0] == pytest.approx(np.sqrt(2.0))
    assert row_cosine_distance(left, right)[0] == pytest.approx(1.0)
    assert row_cosine_distance(left, right)[1] == pytest.approx(0.0)


def test_compute_row_feature_metrics_and_summary():
    arrays = _arrays()
    metadata = _metadata()
    normal, variant = _outputs()

    rows = compute_row_feature_metrics(arrays, metadata, normal_outputs=normal, variant_outputs=variant)
    summary = summarize_feature_group(rows, ("source_index", "variant"))

    assert rows.shape[0] == 6
    assert rows["fused_feature_l2"].mean() == pytest.approx(0.1)
    assert rows["actor_tanh_action_l2"].mean() == pytest.approx(0.02)
    assert len(summary) == 2
    assert all("fused_feature_l2_weighted_mean" in row for row in summary)


def test_weighted_median_uses_weights():
    rows = pd.DataFrame({"value": [0.0, 10.0], "weight": [0.9, 0.1]})

    assert weighted_median(rows, "value") == pytest.approx(0.0)


def test_classify_signal_collapse_detects_actor_insensitivity():
    arrays = _arrays()
    metadata = _metadata()
    normal, variant = _outputs(feature_gap=0.1, action_gap=0.001)
    rows = compute_row_feature_metrics(arrays, metadata, normal_outputs=normal, variant_outputs=variant)

    classification = classify_signal_collapse(rows)

    assert classification["classification"] == "actor_action_insensitivity"


def test_batched_recurrent_outputs_preserves_model_checksum():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=8, actor_encoder="human_view_online_gru")
    before = model_parameter_checksum(model)
    observations = np.zeros((4, 72), dtype=np.float32)
    hidden = np.zeros((4, 8), dtype=np.float32)

    outputs = batched_recurrent_outputs(model, observations, hidden, device=torch.device("cpu"), batch_size=2)

    assert outputs["features"].shape == (4, 8)
    assert outputs["next_hidden"].shape == (4, 8)
    assert outputs["actor_action"].shape == (4, 3)
    assert model_parameter_checksum(model) == before
