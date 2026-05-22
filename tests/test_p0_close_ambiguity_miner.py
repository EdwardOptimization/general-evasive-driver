import numpy as np
import pytest

from autodrift.p0_close_ambiguity_miner import (
    aggregate_miner_summaries,
    mine_close_ambiguity_pairs,
)


def _sample_rows(count: int):
    return [
        {
            "episode": index,
            "seed": 9000 + index,
            "step": 5,
            "sample_phase": "pre_limit_nonpost",
            "future_braking_deceleration": 0.0,
            "future_yaw_response": 0.0,
            "future_lateral_accel_response": 0.0,
        }
        for index in range(count)
    ]


def test_mine_close_ambiguity_pairs_finds_p0_close_target_divergent_pair():
    observations = np.zeros((4, 85), dtype=np.float32)
    observations[:, 2] = [0.00, 0.01, 2.00, 2.01]  # H1 yaw cue
    observations[:, 25] = [0.00, 0.01, 2.00, 2.01]  # context cue
    observations[:, 0] = [0.00, 0.01, 2.00, 2.01]  # P0-only vx remains close for pair 0-1
    observations[:, 1] = [0.00, 0.01, 2.00, 2.01]  # P0-only vy remains close for pair 0-1
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
    }

    pair_rows, summary_rows, summary = mine_close_ambiguity_pairs(
        observations=observations,
        targets=targets,
        sample_rows=_sample_rows(4),
        seed=3,
        max_search_samples=4,
        feature_quantile=0.34,
        target_quantile=0.50,
        max_export_pairs=5,
    )

    assert summary["p0_close_target_divergent_count"] >= 1
    assert any(row["surface"] == "p0_close_target_divergent" for row in pair_rows)
    assert any(row["surface"] == "h1_close_target_divergent" for row in pair_rows)
    by_surface = {row["surface"]: row for row in summary_rows}
    assert by_surface["p0_close_target_divergent"]["accepted_count"] >= 1


def test_mine_close_ambiguity_pairs_can_show_h1_ambiguity_disappears_under_p0():
    observations = np.zeros((4, 85), dtype=np.float32)
    observations[:, 2] = [0.00, 0.01, 2.00, 2.01]  # H1 pair 0-1 is close.
    observations[:, 25] = [0.00, 0.01, 2.00, 2.01]
    observations[:, 0] = [0.00, 5.00, 2.00, 2.01]  # P0 vx separates pair 0-1.
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 4.0, 0.1, 0.2], dtype=np.float32),
    }

    _, _, summary = mine_close_ambiguity_pairs(
        observations=observations,
        targets=targets,
        sample_rows=_sample_rows(4),
        seed=5,
        max_search_samples=4,
        feature_quantile=0.50,
        target_quantile=0.50,
        max_export_pairs=5,
    )

    assert summary["h1_close_target_divergent_count"] >= 1
    assert summary["h1_only_target_divergent_count"] >= 1


def test_mine_close_ambiguity_pairs_rejects_mismatched_targets():
    observations = np.zeros((4, 85), dtype=np.float32)
    targets = {
        "future_braking_deceleration": np.zeros(4, dtype=np.float32),
        "future_yaw_response": np.zeros(3, dtype=np.float32),
        "future_lateral_accel_response": np.zeros(4, dtype=np.float32),
    }

    with pytest.raises(ValueError, match="all target arrays"):
        mine_close_ambiguity_pairs(
            observations=observations,
            targets=targets,
            sample_rows=_sample_rows(4),
            seed=1,
        )


def test_aggregate_miner_summaries(tmp_path):
    import json

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    base = {
        "seed": 1,
        "h1_close_target_divergent_count": 10,
        "p0_close_target_divergent_count": 4,
        "both_h1_p0_close_target_divergent_count": 2,
        "h1_only_target_divergent_count": 8,
        "p0_only_target_divergent_count": 2,
        "h1_unique_episode_pairs": 7,
        "p0_unique_episode_pairs": 3,
    }
    first.write_text(json.dumps(base), encoding="utf-8")
    other = dict(base)
    other["seed"] = 2
    other["p0_close_target_divergent_count"] = 6
    second.write_text(json.dumps(other), encoding="utf-8")

    summary = aggregate_miner_summaries((first, second))

    assert summary["seeds"] == [1, 2]
    assert summary["metric_totals"]["total_p0_close_target_divergent_count"] == 10
    assert summary["h1_to_p0_count_ratio"] == pytest.approx(10 / 20)
