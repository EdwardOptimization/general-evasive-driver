import numpy as np

from autodrift.hidden_envelope_probe import CURRENT_RESPONSE, FULL_OBSERVATION, RESPONSE_HIDDEN
from autodrift.matched_current_response_ambiguity import (
    MATCH_CURRENT_RESPONSE_CONTEXT,
    add_feature_distances,
    build_match_features,
    nearest_visible_candidate_pairs,
    physical_pair_key,
    select_ambiguity_pairs,
    source_obstacle_bucket_key,
    summarize_ambiguity_pairs,
    visible_distance_threshold,
)


def test_build_match_features_concatenates_response_and_context():
    full = np.asarray(
        [
            [1.0, 2.0, 10.0, 11.0],
            [3.0, 4.0, 12.0, 13.0],
        ],
        dtype=np.float32,
    )
    response = full[:, :2]

    features = build_match_features(
        full,
        response,
        response_dim=2,
        match_feature_set=MATCH_CURRENT_RESPONSE_CONTEXT,
    )

    assert features.shape == (2, 4)
    np.testing.assert_allclose(features, full)


def test_nearest_visible_candidate_pairs_finds_target_ambiguity():
    rows = [
        {"episode": 0, "seed": 100, "step": 0},
        {"episode": 1, "seed": 101, "step": 0},
        {"episode": 2, "seed": 102, "step": 0},
    ]
    match_features = np.asarray(
        [
            [0.0, 0.0],
            [0.02, 0.01],
            [3.0, 3.0],
        ],
        dtype=np.float32,
    )
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 2.0, 0.1], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 0.1, 0.2], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 0.1, 0.2], dtype=np.float32),
    }

    candidates = nearest_visible_candidate_pairs(
        rows=rows,
        match_features=match_features,
        targets=targets,
        nearest_k=1,
        exclude_same_episode=True,
    )
    threshold = visible_distance_threshold(
        candidates,
        max_visible_distance=None,
        max_visible_quantile=0.50,
    )
    accepted = select_ambiguity_pairs(
        candidates,
        visible_threshold=threshold,
        min_target_z_delta=1.0,
        max_pairs_per_target=10,
    )

    assert any(row["target"] == "future_braking_deceleration" for row in accepted)
    assert all(row["accepted"] is True for row in accepted)


def test_select_ambiguity_pairs_can_limit_physical_pair_repeats():
    candidates = []
    for target in [
        "future_braking_deceleration",
        "future_yaw_response",
        "future_lateral_accel_response",
    ]:
        candidates.append(
            {
                "left_seed": 1,
                "left_step": 10,
                "right_seed": 2,
                "right_step": 20,
                "target": target,
                "visible_distance": 0.01,
                "target_z_delta": 3.0,
            }
        )
    candidates.append(
        {
            "left_seed": 3,
            "left_step": 10,
            "right_seed": 4,
            "right_step": 20,
            "target": "future_yaw_response",
            "visible_distance": 0.02,
            "target_z_delta": 2.0,
        }
    )

    selected = select_ambiguity_pairs(
        candidates,
        visible_threshold=0.05,
        min_target_z_delta=1.0,
        max_pairs_per_target=10,
        max_pairs_per_physical_pair=1,
    )

    counts = {}
    for row in selected:
        key = physical_pair_key(row)
        counts[key] = counts.get(key, 0) + 1
    assert max(counts.values()) == 1
    assert len(selected) == 2


def test_select_ambiguity_pairs_can_limit_left_step_repeats():
    candidates = [
        {
            "left_seed": 1,
            "left_step": 10,
            "right_seed": 2,
            "right_step": 20 + index,
            "target": "future_braking_deceleration",
            "visible_distance": 0.01 + 0.001 * index,
            "target_z_delta": 4.0 - index,
        }
        for index in range(2)
    ]
    candidates.append(
        {
            "left_seed": 3,
            "left_step": 11,
            "right_seed": 4,
            "right_step": 30,
            "target": "future_braking_deceleration",
            "visible_distance": 0.02,
            "target_z_delta": 2.0,
        }
    )

    selected = select_ambiguity_pairs(
        candidates,
        visible_threshold=0.05,
        min_target_z_delta=1.0,
        max_pairs_per_target=10,
        max_pairs_per_left_step=1,
    )

    assert [int(row["left_step"]) for row in selected] == [10, 11]


def test_select_ambiguity_pairs_can_limit_source_obstacle_bucket_repeats():
    candidates = [
        {
            "left_seed": 1 + index,
            "left_step": 10 + index,
            "right_seed": 10 + index,
            "right_step": 20 + index,
            "target": "future_yaw_response",
            "visible_distance": 0.01 + 0.001 * index,
            "target_z_delta": 4.0 - index,
            "left_obstacle_distance": 12.0,
            "left_obstacle_lateral_offset": 0.2,
        }
        for index in range(2)
    ]
    candidates.append(
        {
            "left_seed": 8,
            "left_step": 18,
            "right_seed": 9,
            "right_step": 28,
            "target": "future_yaw_response",
            "visible_distance": 0.02,
            "target_z_delta": 2.0,
            "left_obstacle_distance": 22.0,
            "left_obstacle_lateral_offset": 0.2,
        }
    )

    selected = select_ambiguity_pairs(
        candidates,
        visible_threshold=0.05,
        min_target_z_delta=1.0,
        max_pairs_per_target=10,
        max_pairs_per_source_obstacle_bucket=1,
        obstacle_distance_bucket_width=5.0,
        obstacle_lateral_bucket_width=1.0,
    )

    buckets = [
        source_obstacle_bucket_key(row, distance_width=5.0, lateral_width=1.0)
        for row in selected
    ]
    assert len(selected) == 2
    assert len(set(buckets)) == 2


def test_add_feature_distances_and_summary_compare_hidden_to_current():
    pair_rows = [
        {
            "left_index": 0,
            "right_index": 1,
            "target": "future_braking_deceleration",
            "target_z_delta": 2.0,
            "visible_distance": 0.1,
        }
    ]
    features = {
        CURRENT_RESPONSE: np.asarray([[0.0], [0.1]], dtype=np.float32),
        RESPONSE_HIDDEN: np.asarray([[0.0], [2.0]], dtype=np.float32),
        FULL_OBSERVATION: np.asarray([[0.0], [0.1]], dtype=np.float32),
    }

    enriched = add_feature_distances(
        pair_rows,
        features,
        feature_sets=(CURRENT_RESPONSE, RESPONSE_HIDDEN, FULL_OBSERVATION),
    )
    summary = summarize_ambiguity_pairs(
        checkpoint_label="candidate",
        probe_seed=9510,
        sample_count=2,
        match_feature_set=MATCH_CURRENT_RESPONSE_CONTEXT,
        nearest_k=1,
        visible_threshold=0.2,
        min_target_z_delta=1.0,
        candidate_rows=enriched,
        accepted_rows=enriched,
    )

    assert enriched[0]["response_hidden_more_separated_than_current_response"] is False
    assert summary[0]["accepted_count"] == 1
    assert summary[0]["accepted_target_z_delta_mean"] == 2.0
