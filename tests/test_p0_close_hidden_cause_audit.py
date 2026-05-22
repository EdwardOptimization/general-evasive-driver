import json

import numpy as np
import pytest

from autodrift.p0_close_hidden_cause_audit import (
    HIDDEN_CAUSE_GROUPS,
    HIDDEN_FIELDS,
    aggregate_hidden_cause_summaries,
    evaluate_hidden_causes,
)


def _row(index: int, mu: float, brake_scale: float, yaw_target: float):
    row = {
        "episode": index,
        "seed": 9000 + index,
        "step": 5,
        "future_braking_deceleration": float(index),
        "future_yaw_response": float(yaw_target),
        "future_lateral_accel_response": float(index) * 0.1,
        "mu": mu,
        "mass_scale": 1.0,
        "inertia_scale": 1.0,
        "cg_shift": 0.0,
        "front_tire_stiffness_scale": 1.0,
        "rear_tire_stiffness_scale": 1.0,
        "drive_scale": 1.0,
        "brake_scale": brake_scale,
        "steer_tau_scale": 1.0,
        "drive_tau_scale": 1.0,
    }
    for field in HIDDEN_FIELDS:
        row.setdefault(field, 0.0)
    return row


def test_evaluate_hidden_causes_reports_group_and_target_summaries():
    sample_rows = [
        _row(0, mu=0.30, brake_scale=0.60, yaw_target=0.0),
        _row(1, mu=0.70, brake_scale=1.30, yaw_target=5.0),
        _row(2, mu=0.35, brake_scale=0.65, yaw_target=0.1),
        _row(3, mu=0.36, brake_scale=0.66, yaw_target=0.2),
    ]
    pair_rows = [
        {
            "rank": 1,
            "sample_i": 0,
            "sample_j": 1,
            "episode_i": 0,
            "episode_j": 1,
            "step_i": 5,
            "step_j": 5,
        }
    ]

    pair_metrics, group_summary, target_summary, cross_rows = evaluate_hidden_causes(sample_rows, pair_rows)

    assert len(pair_metrics) == 1
    assert pair_metrics[0]["dominant_target"] == "future_yaw_response"
    by_group = {row["hidden_group"]: row for row in group_summary}
    assert set(by_group) == set(HIDDEN_CAUSE_GROUPS)
    assert by_group["braking_authority"]["mean_distance"] > 0.0
    by_target = {row["target"]: row for row in target_summary}
    assert by_target["future_yaw_response"]["dominant_fraction"] == pytest.approx(1.0)
    assert any(row["pair_count"] >= 0 for row in cross_rows)


def test_evaluate_hidden_causes_rejects_out_of_range_pair():
    sample_rows = [_row(0, mu=0.3, brake_scale=0.6, yaw_target=0.0)]
    pair_rows = [
        {
            "sample_i": 0,
            "sample_j": 2,
            "episode_i": 0,
            "episode_j": 1,
            "step_i": 0,
            "step_j": 0,
        }
    ]

    with pytest.raises(ValueError, match="outside"):
        evaluate_hidden_causes(sample_rows, pair_rows)


def test_aggregate_hidden_cause_summaries(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    base = {
        "seed": 1,
        "hidden_group_summary": [
            {
                "hidden_group": "friction",
                "pairs": 10,
                "mean_distance": 1.0,
                "feature_target_corr": 0.2,
                "target_top_group_top_overlap": 0.3,
                "dominant_fraction": 0.4,
            }
        ],
        "target_summary": [
            {
                "target": "future_braking_deceleration",
                "pairs": 10,
                "mean_abs_diff": 2.0,
                "mean_z_abs_diff": 1.0,
                "dominant_fraction": 0.5,
            }
        ],
    }
    first.write_text(json.dumps(base), encoding="utf-8")
    other = dict(base)
    other["seed"] = 2
    other["hidden_group_summary"] = [dict(base["hidden_group_summary"][0], mean_distance=3.0)]
    second.write_text(json.dumps(other), encoding="utf-8")

    summary = aggregate_hidden_cause_summaries((first, second))

    friction = [row for row in summary["hidden_group_summary"] if row["hidden_group"] == "friction"][0]
    assert friction["mean_distance"] == pytest.approx(2.0)
    target = [row for row in summary["target_summary"] if row["target"] == "future_braking_deceleration"][0]
    assert target["pairs"] == 20
