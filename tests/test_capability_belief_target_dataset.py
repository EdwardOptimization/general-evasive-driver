import json

import numpy as np
import pytest

from autodrift.capability_belief_target_dataset import (
    CAPABILITY_TARGETS,
    P0_PER_FRAME_INDICES,
    build_capability_belief_dataset,
    combine_datasets,
    hidden_metric_by_pair,
    p0_history_features,
)


def test_p0_history_features_uses_deployable_p0_indices():
    observations = np.arange(2 * 85, dtype=np.float32).reshape(2, 85)

    features = p0_history_features(observations)

    np.testing.assert_array_equal(features, observations[:, list(P0_PER_FRAME_INDICES)])
    assert features.shape[1] == 72


def test_hidden_metric_by_pair_reads_sample_key(tmp_path):
    path = tmp_path / "hidden.csv"
    path.write_text(
        "sample_i,sample_j,dominant_target,dominant_hidden_group,target_distance,friction_distance,mass_geometry_distance\n"
        "1,2,future_yaw_response,mass_geometry,3.0,0.2,2.0\n",
        encoding="utf-8",
    )

    mapping = hidden_metric_by_pair(path)

    assert mapping[(1, 2)]["dominant_target"] == "future_yaw_response"


def test_build_capability_belief_dataset_separates_student_and_teacher_arrays():
    observations = np.arange(4 * 85, dtype=np.float32).reshape(4, 85)
    targets = {
        "future_braking_deceleration": np.asarray([0.0, 1.0, 0.2, 0.3], dtype=np.float32),
        "future_yaw_response": np.asarray([0.0, 4.0, 0.2, 0.3], dtype=np.float32),
        "future_lateral_accel_response": np.asarray([0.0, 2.0, 0.2, 0.3], dtype=np.float32),
    }
    pair_rows = [
        {
            "surface": "p0_close_target_divergent",
            "sample_i": 0,
            "sample_j": 1,
            "seed_i": 9000,
            "seed_j": 9001,
            "episode_i": 0,
            "episode_j": 1,
            "step_i": 5,
            "step_j": 5,
        }
    ]
    hidden_metric_rows = {
        (0, 1): {
            "dominant_target": "future_yaw_response",
            "dominant_hidden_group": "mass_geometry",
            "target_distance": "3.5",
            "friction_distance": "0.1",
            "braking_authority_distance": "0.2",
            "drive_authority_distance": "0.3",
            "tire_lateral_authority_distance": "0.4",
            "mass_geometry_distance": "2.0",
            "actuator_delay_distance": "0.5",
        }
    }

    arrays, rows, summary = build_capability_belief_dataset(observations, targets, pair_rows, hidden_metric_rows)

    assert arrays["student_p0_i"].shape == (1, 72)
    assert arrays["teacher_capability_i"].shape == (1, len(CAPABILITY_TARGETS))
    assert "mu" not in arrays
    assert rows[0]["dominant_target"] == "future_yaw_response"
    assert rows[0]["dominant_hidden_group"] == "mass_geometry"
    assert summary["dominant_target_counts"]["future_yaw_response"] == 1
    assert summary["dominant_hidden_group_counts"]["mass_geometry"] == 1


def test_build_capability_belief_dataset_rejects_missing_hidden_metric():
    observations = np.zeros((2, 85), dtype=np.float32)
    targets = {target: np.zeros(2, dtype=np.float32) for target in CAPABILITY_TARGETS}
    pair_rows = [{"sample_i": 0, "sample_j": 1}]

    with pytest.raises(ValueError, match="missing hidden metric"):
        build_capability_belief_dataset(observations, targets, pair_rows, {})


def test_combine_datasets_concatenates_arrays(tmp_path):
    first = tmp_path / "first.npz"
    second = tmp_path / "second.npz"
    arrays = {
        "student_p0_i": np.zeros((1, 72), dtype=np.float32),
        "student_p0_j": np.ones((1, 72), dtype=np.float32),
        "teacher_capability_i": np.zeros((1, 3), dtype=np.float32),
        "teacher_capability_j": np.ones((1, 3), dtype=np.float32),
        "teacher_capability_delta": np.zeros((1, 3), dtype=np.float32),
        "teacher_capability_abs_delta_z": np.ones((1, 3), dtype=np.float32),
        "pair_weight": np.ones(1, dtype=np.float32),
        "dominant_target_index": np.asarray([1], dtype=np.int64),
        "dominant_hidden_group_index": np.asarray([4], dtype=np.int64),
        "hidden_group_distances": np.ones((1, 6), dtype=np.float32),
        "sample_i": np.asarray([0], dtype=np.int64),
        "sample_j": np.asarray([1], dtype=np.int64),
    }
    np.savez_compressed(first, **arrays)
    np.savez_compressed(second, **arrays)
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps({"seed": 1, "dominant_target_counts": {"future_yaw_response": 1}}), encoding="utf-8")

    combined, summary = combine_datasets((first, second), (summary_path,))

    assert combined["student_p0_i"].shape[0] == 2
    assert summary["pairs"] == 2
    assert summary["dominant_target_counts"]["future_yaw_response"] == 2
