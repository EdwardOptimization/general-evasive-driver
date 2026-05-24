import argparse

import numpy as np

from autodrift.wrong_history_fusion_boundary_probe import (
    apply_view_pass_rules,
    build_feature_views,
    diagnostic_view_passes,
    parse_views,
)


def test_parse_views_rejects_invalid_and_duplicate():
    assert parse_views("fused,next_hidden") == ("fused", "next_hidden")
    try:
        parse_views("fused,bad")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("invalid view was accepted")
    try:
        parse_views("fused,fused")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("duplicate view was accepted")


def test_build_feature_views_shapes_and_concat():
    normal = {
        "features": np.ones((3, 2), dtype=np.float32),
        "next_hidden": np.full((3, 4), 2.0, dtype=np.float32),
    }
    variant = {
        "features": np.full((3, 2), 3.0, dtype=np.float32),
        "next_hidden": np.full((3, 4), 4.0, dtype=np.float32),
    }

    views = build_feature_views(normal, variant, ("fused", "next_hidden", "fused_plus_next_hidden"))

    assert views["fused"][0].shape == (3, 2)
    assert views["next_hidden"][0].shape == (3, 4)
    assert views["fused_plus_next_hidden"][0].shape == (3, 6)
    assert np.allclose(views["fused_plus_next_hidden"][0][:, :2], 1.0)
    assert np.allclose(views["fused_plus_next_hidden"][0][:, 2:], 2.0)


def test_diagnostic_view_passes_requires_improvement_over_fused():
    row = {
        "normal_validation_delta_mse": 0.0009,
        "wrong_validation_gap_mse": 0.0002,
        "wrong_validation_prediction_gap_l2": 0.006,
    }

    assert diagnostic_view_passes(row, fused_same_seed_l2=0.001)
    assert not diagnostic_view_passes(row, fused_same_seed_l2=0.003)


def test_apply_view_pass_rules_counts_non_fused_views():
    rows = []
    for seed in (1, 2, 3):
        rows.append(
            {
                "seed": seed,
                "view": "fused",
                "normal_validation_delta_mse": 0.0005,
                "wrong_validation_gap_mse": 0.0,
                "wrong_validation_prediction_gap_l2": 0.0005,
            }
        )
        rows.append(
            {
                "seed": seed,
                "view": "next_hidden",
                "normal_validation_delta_mse": 0.0008,
                "wrong_validation_gap_mse": 0.0002,
                "wrong_validation_prediction_gap_l2": 0.006,
            }
        )

    result = apply_view_pass_rules(rows)

    assert result["diagnostic_passed"] is True
    assert result["view_pass_counts"]["next_hidden"] == 3
    assert result["fused_weak_seed_count"] == 3
