import argparse

import numpy as np
import pandas as pd
import pytest
import torch

from autodrift.response_amplification_actor_coupling import (
    alpha_candidate_passes,
    apply_actor_coupling_pass_rules,
    evaluate_alpha_ladder,
    parse_actor_coupling_view,
    parse_alpha_list,
    parse_head_type,
    train_actor_coupling_seed,
)


def _arrays(rows: int = 20) -> dict[str, np.ndarray]:
    normal_hidden = np.zeros((rows, 5), dtype=np.float32)
    variant_hidden = np.ones((rows, 5), dtype=np.float32) * 0.2
    normal_base = np.zeros((rows, 3, 3), dtype=np.float32)
    target_wrong = np.zeros_like(normal_base)
    target_wrong[:, :, 0] = 0.012
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
        "sequence_mask": np.ones((rows, 3), dtype=np.float32),
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


def test_parse_alpha_list_sorts_and_rejects_invalid():
    assert parse_alpha_list("0.5,0.1") == (0.1, 0.5)
    with pytest.raises(argparse.ArgumentTypeError):
        parse_alpha_list("-0.1")
    with pytest.raises(argparse.ArgumentTypeError):
        parse_alpha_list("0.1,0.1")


def test_parse_actor_coupling_view_is_restricted():
    assert parse_actor_coupling_view("fused_plus_next_hidden") == "fused_plus_next_hidden"
    with pytest.raises(argparse.ArgumentTypeError):
        parse_actor_coupling_view("fused")


def test_parse_head_type_is_restricted():
    assert parse_head_type("mlp") == "mlp"
    assert parse_head_type("gated") == "gated"
    with pytest.raises(argparse.ArgumentTypeError):
        parse_head_type("transformer")


def test_alpha_candidate_passes_requires_source_holdout_and_thresholds():
    row = {
        "split": "source_holdout_validation",
        "alpha": 1.0,
        "normal_delta_l2_mean": 0.001,
        "normal_delta_l2_p95": 0.002,
        "predicted_normal_wrong_gap_l2_mean": 0.012,
        "predicted_normal_wrong_gap_l2_p10": 0.005,
        "gap_improvement_ratio": 4.0,
        "wrong_target_mse_improvement": 0.8,
        "normal_action_drift_first_l2_p95": 0.003,
    }

    assert alpha_candidate_passes(row)
    row["split"] = "train"
    assert not alpha_candidate_passes(row)


def test_evaluate_alpha_ladder_selects_largest_passing_alpha():
    arrays = _arrays(rows=4)
    metadata = _metadata(rows=4)
    prediction_normal = np.zeros((4, 3, 3), dtype=np.float32)
    prediction_wrong = arrays["target_delta_wrong"].copy()

    rows, summary = evaluate_alpha_ladder(
        arrays=arrays,
        metadata=metadata,
        prediction_normal=prediction_normal,
        prediction_wrong=prediction_wrong,
        alphas=(0.5, 1.0),
    )

    assert rows
    assert summary["alpha_passed"] is True
    assert summary["selected_alpha"] == 1.0


def test_train_actor_coupling_seed_learns_synthetic_residual_and_alpha_passes():
    arrays = _arrays()
    metadata = _metadata()

    head, metrics, summary, alpha_rows = train_actor_coupling_seed(
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        alphas=(0.5, 1.0),
        hidden_dim=16,
        epochs=120,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=17,
        wrong_target_coef=1.0,
        gap_margin_coef=0.1,
        smoothness_coef=0.0,
        target_gap=0.004,
        device=torch.device("cpu"),
    )

    assert head.max_sequence_length == 3
    assert metrics[0]["epoch"] == 0
    assert alpha_rows
    assert summary["alpha_passed"] is True
    assert summary["selected_alpha"] > 0.0
    result = apply_actor_coupling_pass_rules([summary])
    assert result["actor_coupling_exact_passed"] is True


def test_branch_specific_gap_training_reports_hard_row_terms():
    arrays = _arrays()
    metadata = _metadata()

    _head, metrics, summary, _alpha_rows = train_actor_coupling_seed(
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        alphas=(1.0,),
        hidden_dim=16,
        epochs=20,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=19,
        wrong_target_coef=2.0,
        gap_margin_coef=0.1,
        smoothness_coef=0.0,
        normal_first_coef=5.0,
        normal_first_topk_coef=2.0,
        normal_first_threshold=0.004,
        normal_first_topk_fraction=0.1,
        wrong_first_gap_coef=1.0,
        wrong_first_target_gap=0.006,
        branch_specific_gap=True,
        wrong_sequence_gap_coef=1.0,
        wrong_sequence_target_gap=0.012,
        wrong_hard_coef=0.5,
        wrong_hard_fraction=0.25,
        target_gap=0.004,
        device=torch.device("cpu"),
    )

    assert summary["branch_specific_gap"] is True
    assert summary["wrong_hard_fraction"] == 0.25
    assert any("wrong_sequence_gap_hinge" in row for row in metrics)
    assert any(row["hard_row_count"] > 0 for row in metrics)


def test_normal_sequence_safe_training_reports_sequence_terms():
    arrays = _arrays()
    metadata = _metadata()

    _head, metrics, summary, _alpha_rows = train_actor_coupling_seed(
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        alphas=(1.0,),
        hidden_dim=16,
        epochs=20,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=23,
        wrong_target_coef=2.0,
        gap_margin_coef=0.1,
        smoothness_coef=0.0,
        normal_sequence_mean_coef=4.0,
        normal_sequence_mean_threshold=0.002,
        normal_sequence_topk_coef=2.0,
        normal_sequence_topk_threshold=0.0045,
        normal_sequence_topk_fraction=0.1,
        normal_first_coef=5.0,
        normal_first_topk_coef=2.0,
        normal_first_threshold=0.004,
        normal_first_topk_fraction=0.1,
        wrong_first_gap_coef=1.0,
        wrong_first_target_gap=0.006,
        branch_specific_gap=True,
        wrong_sequence_gap_coef=1.0,
        wrong_sequence_target_gap=0.012,
        wrong_hard_coef=0.5,
        wrong_hard_fraction=0.25,
        target_gap=0.004,
        device=torch.device("cpu"),
    )

    assert summary["normal_sequence_mean_coef"] == 4.0
    assert summary["normal_sequence_mean_threshold"] == 0.002
    assert summary["normal_sequence_topk_coef"] == 2.0
    assert summary["normal_sequence_topk_threshold"] == 0.0045
    assert summary["normal_sequence_topk_fraction"] == 0.1
    assert any("normal_sequence_mean_hinge" in row for row in metrics)
    assert any("normal_sequence_topk_hinge" in row for row in metrics)


def test_gated_head_training_reports_gate_terms_and_alpha_diagnostics():
    arrays = _arrays()
    metadata = _metadata()

    _head, metrics, summary, alpha_rows = train_actor_coupling_seed(
        arrays=arrays,
        metadata=metadata,
        features_normal=arrays["normal_hidden"],
        features_variant=arrays["variant_hidden"],
        alphas=(1.0,),
        hidden_dim=16,
        epochs=20,
        learning_rate=0.01,
        weight_decay=0.0,
        seed=29,
        head_type="gated",
        max_residual=0.04,
        wrong_target_coef=2.0,
        gap_margin_coef=0.1,
        smoothness_coef=0.0,
        normal_sequence_mean_coef=4.0,
        normal_sequence_mean_threshold=0.002,
        normal_sequence_topk_coef=2.0,
        normal_sequence_topk_threshold=0.0045,
        normal_sequence_topk_fraction=0.1,
        normal_gate_coef=1.0,
        normal_gate_topk_coef=1.0,
        normal_gate_threshold=0.10,
        normal_gate_topk_fraction=0.1,
        normal_first_coef=5.0,
        normal_first_topk_coef=2.0,
        normal_first_threshold=0.004,
        normal_first_topk_fraction=0.1,
        wrong_first_gap_coef=1.0,
        wrong_first_target_gap=0.006,
        branch_specific_gap=True,
        wrong_sequence_gap_coef=1.0,
        wrong_sequence_target_gap=0.012,
        wrong_hard_coef=0.5,
        wrong_hard_fraction=0.25,
        wrong_gate_open_coef=0.25,
        wrong_gate_target=0.50,
        raw_amplifier_l2_coef=0.01,
        target_gap=0.004,
        device=torch.device("cpu"),
    )

    assert summary["head_type"] == "gated"
    assert summary["max_residual"] == 0.04
    assert summary["normal_gate_coef"] == 1.0
    assert summary["wrong_gate_open_coef"] == 0.25
    assert summary["normal_gate_mean"] is not None
    assert summary["wrong_gate_mean"] is not None
    assert any("normal_gate_mean_loss" in row for row in metrics)
    assert any("wrong_gate_open_hinge" in row for row in metrics)
    assert any("raw_amplifier_l2" in row for row in metrics)
    assert any("normal_gate_mean" in row for row in alpha_rows)
    assert any("wrong_gate_mean" in row for row in alpha_rows)
