import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.response_amplification_shadow import (
    ResponseAmplifierHead,
    amplify_wrong_delta,
    assign_source_balanced_weights,
    apply_shadow_pass_rules,
    assign_source_holdout_by_pair,
    select_shadow_candidate_rows,
    shadow_view_seed_passes,
    summarize_shadow_predictions,
    train_response_amplifier_head,
)


def _candidate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "normal_success": [True, True, False, True],
            "wrong_success": [True, True, True, True],
            "normal_margin": [0.2, 1.2, 0.2, 0.3],
            "wrong_first_action_l2": [0.005, 0.010, 0.020, 0.001],
            "wrong_action_sequence_mean_l2": [0.002, 0.004, 0.006, 0.001],
            "context_distance": [0.3, 0.1, 0.2, 0.4],
            "sequence_length": [5, 5, 7, 9],
            "physical_pair_key": ["a", "b", "c", "d"],
            "left_seed": [1, 2, 3, 4],
        }
    )


def _arrays(rows: int = 20) -> dict[str, np.ndarray]:
    normal_hidden = np.zeros((rows, 5), dtype=np.float32)
    variant_hidden = np.ones((rows, 5), dtype=np.float32) * 0.2
    normal_base = np.zeros((rows, 3, 3), dtype=np.float32)
    target_wrong = np.zeros_like(normal_base)
    target_wrong[:, :, 0] = 0.012
    target_wrong[:, :, 1] = 0.01
    mask = np.ones((rows, 3), dtype=np.float32)
    return {
        "observation": np.zeros((rows, 72), dtype=np.float32),
        "normal_hidden": normal_hidden,
        "variant_hidden": variant_hidden,
        "normal_base_action_sequence": normal_base,
        "variant_base_action_sequence": normal_base + 0.001,
        "normal_action_sequence": normal_base,
        "wrong_action_sequence": normal_base + 0.001,
        "target_action_sequence": normal_base,
        "target_delta_normal": np.zeros_like(normal_base),
        "target_delta_wrong": target_wrong,
        "wrong_target_action_sequence": normal_base + target_wrong,
        "sequence_mask": mask,
        "variant_base_action": np.zeros((rows, 3), dtype=np.float32),
        "weight": np.full(rows, 1.0 / rows, dtype=np.float32),
        "row_id": np.arange(rows, dtype=np.int64),
        "source_index": np.repeat(np.array([1, 2], dtype=np.int64), rows // 2),
        "sequence_length": np.full(rows, 3, dtype=np.int64),
    }


def _metadata(rows: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_index": np.repeat([1, 2], rows // 2),
            "split": ["train"] * (rows // 2) + ["source_holdout_validation"] * (rows // 2),
            "surface": ["fresh"] * rows,
            "target": ["drift_required"] * rows,
            "variant": ["wrong_matched_history"] * rows,
            "grid_name": ["response_amplification_shadow"] * rows,
            "physical_pair_key": ["p1"] * (rows // 2) + ["p2"] * (rows // 2),
            "sequence_length": [3] * rows,
            "corpus_weight": [1.0 / rows] * rows,
        }
    )


def test_select_shadow_candidate_rows_filters_and_caps():
    selected = select_shadow_candidate_rows(
        _candidate_frame(),
        sequence_lengths=(5, 7, 9),
        max_rows=8,
        max_rows_per_physical_pair=2,
        max_rows_per_left_seed=2,
        min_wrong_first_action_l2=0.002,
    )

    assert len(selected) == 1
    assert selected.loc[0, "physical_pair_key"] == "a"


def test_assign_source_holdout_by_pair_uses_whole_pairs():
    rows = [{"physical_pair_key": f"p{i}", "split": "unassigned"} for i in range(6)]

    assign_source_holdout_by_pair(rows)

    by_pair = {row["physical_pair_key"]: row["split"] for row in rows}
    assert "source_holdout_validation" in by_pair.values()
    assert "train" in by_pair.values()


def test_assign_source_balanced_weights_equalizes_source_mass():
    rows = [
        {"source_index": 1},
        {"source_index": 1},
        {"source_index": 2},
    ]

    assign_source_balanced_weights(rows)

    source_mass = {}
    for row in rows:
        source_mass[row["source_index"]] = source_mass.get(row["source_index"], 0.0) + row["weight"]
    assert source_mass[1] == pytest.approx(0.5)
    assert source_mass[2] == pytest.approx(0.5)


def test_amplify_wrong_delta_scales_and_clips_existing_direction():
    base = np.full((3, 3), 0.001, dtype=np.float32)

    amplified = amplify_wrong_delta(
        base,
        target_wrong_sequence_mean_l2=0.030,
        max_abs_delta=0.010,
        min_base_direction_norm=1e-8,
    )

    assert amplified is not None
    assert amplified.shape == (3, 3)
    assert float(np.abs(amplified).max()) <= 0.0100001
    assert amplify_wrong_delta(
        np.zeros((3, 3), dtype=np.float32),
        target_wrong_sequence_mean_l2=0.030,
        max_abs_delta=0.010,
        min_base_direction_norm=1e-8,
    ) is None


def test_train_response_amplifier_head_learns_synthetic_wrong_delta():
    arrays = _arrays()
    metadata = _metadata()

    head, metrics, summary, predictions = train_response_amplifier_head(
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        hidden_dim=16,
        epochs=100,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=11,
        wrong_target_coef=1.0,
        gap_margin_coef=0.1,
        zero_regularizer_coef=0.1,
        target_gap=0.004,
        device=torch.device("cpu"),
    )

    assert isinstance(head, ResponseAmplifierHead)
    assert metrics[0]["epoch"] == 0
    assert summary["source_holdout_wrong_target_mse"] < summary["source_holdout_zero_head_wrong_target_mse"]
    assert predictions["prediction_normal"].shape == (20, 3, 3)


def test_shadow_prediction_summary_and_pass_rules():
    arrays = _arrays(rows=4)
    metadata = _metadata(rows=4)
    prediction_normal = np.zeros((4, 3, 3), dtype=np.float32)
    prediction_wrong = arrays["target_delta_wrong"].copy()

    row_metrics, _, split_summary, _ = summarize_shadow_predictions(
        arrays,
        metadata,
        prediction_normal=prediction_normal,
        prediction_wrong=prediction_wrong,
    )

    assert len(row_metrics) == 4
    assert {row["split"] for row in split_summary} == {"train", "source_holdout_validation"}

    passing = {
        "source_holdout_normal_delta_l2_mean": 0.001,
        "source_holdout_normal_delta_l2_p95": 0.002,
        "source_holdout_predicted_normal_wrong_gap_l2_mean": 0.011,
        "source_holdout_predicted_normal_wrong_gap_l2_p10": 0.005,
        "source_holdout_gap_improvement_ratio": 4.0,
        "source_holdout_wrong_target_mse_improvement": 0.7,
    }
    assert shadow_view_seed_passes(passing)
    rows = [{"view": "next_hidden", "shadow_view_seed_passed": True} for _ in range(2)]
    rows.append({"view": "fused", "shadow_view_seed_passed": True})
    result = apply_shadow_pass_rules(rows)
    assert result["shadow_passed"] is True
    assert result["view_pass_counts"]["next_hidden"] == 2
