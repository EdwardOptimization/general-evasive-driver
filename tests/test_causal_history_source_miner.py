import numpy as np

from autodrift.causal_history_source_miner import (
    classify_source_miner_result,
    normalized_l2,
    observation_distance_metrics,
    passes_matched_current,
    source_diversity,
)


def test_normalized_l2_is_dimension_scaled():
    left = np.zeros(4, dtype=np.float32)
    right = np.ones(4, dtype=np.float32)

    assert normalized_l2(left, right) == 1.0


def test_observation_metrics_and_matched_current_thresholds():
    left = np.zeros(72, dtype=np.float32)
    right = left.copy()
    right[0] = 0.04
    right[5] = 0.02
    right[9] = 0.02
    right[12:44] = 0.01
    right[44:72] = 0.01
    left[[44, 51, 58, 65]] = 1.0
    right[[44, 51, 58, 65]] = 1.0

    metrics = observation_distance_metrics(left, right)

    assert metrics["obstacle_slot_presence_match"] is True
    assert passes_matched_current(
        metrics,
        {
            "ego_response_l2": 0.08,
            "actuator_state_l2": 0.05,
            "previous_command_l2": 0.05,
            "scene_context_l2": 0.10,
            "obstacle_position_l2": 0.10,
            "road_boundary_l2": 0.12,
        },
    )


def test_source_diversity_reports_share_caps():
    rows = [
        {"seed": 1, "fault_pair": "a->b", "preferred_fault_family": "a", "wrong_fault_family": "b"},
        {"seed": 1, "fault_pair": "a->b", "preferred_fault_family": "a", "wrong_fault_family": "b"},
        {"seed": 2, "fault_pair": "c->d", "preferred_fault_family": "c", "wrong_fault_family": "d"},
    ]

    summary = source_diversity(rows)

    assert summary["unique_source_seeds"] == 2
    assert summary["unique_fault_pairs"] == 2
    assert summary["max_single_seed_share"] == 2 / 3


def test_classify_source_miner_result_requires_structural_thresholds():
    assert (
        classify_source_miner_result(
            candidate_rows=200,
            matched_current_pairs=80,
            unique_source_seeds=12,
            unique_fault_pairs=6,
            finite_metric_rows=200,
            evaluated_rows=200,
        )
        == "causal_history_source_structural_pass"
    )
    assert (
        classify_source_miner_result(
            candidate_rows=12,
            matched_current_pairs=12,
            unique_source_seeds=2,
            unique_fault_pairs=2,
            finite_metric_rows=12,
            evaluated_rows=12,
        )
        == "causal_history_source_structural_sparse"
    )
