import numpy as np
import pytest

from autodrift.bc_capability_corpus import (
    capability_pair_rows,
    validate_capability_corpus_arrays,
)
from autodrift.input_observability_audit import TARGETS
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def _valid_arrays(row_count=4):
    return {
        "student_obs_seq": np.zeros((row_count, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "anchor_action_seq": np.zeros((row_count, 3), dtype=np.float32),
        "capability_target_seq": np.zeros((row_count, len(TARGETS)), dtype=np.float32),
        "done_seq": np.zeros((row_count,), dtype=np.bool_),
        "episode_start_seq": np.zeros((row_count,), dtype=np.bool_),
        "seed_seq": np.arange(row_count, dtype=np.int64),
        "episode_id_seq": np.arange(row_count, dtype=np.int64),
        "step_seq": np.arange(row_count, dtype=np.int64),
        "base_hidden_seq": np.zeros((row_count, 8), dtype=np.float32),
        "base_next_hidden_seq": np.zeros((row_count, 8), dtype=np.float32),
    }


def test_validate_capability_corpus_arrays_accepts_valid_schema():
    validate_capability_corpus_arrays(_valid_arrays())


def test_validate_capability_corpus_arrays_rejects_bad_actor_obs_shape():
    arrays = _valid_arrays()
    arrays["student_obs_seq"] = np.zeros((4, HUMAN_VIEW_OBS_DIM + 1), dtype=np.float32)

    with pytest.raises(ValueError, match="student_obs_seq"):
        validate_capability_corpus_arrays(arrays)


def test_capability_pair_rows_reference_valid_corpus_indices():
    row_count = 6
    observations = np.zeros((row_count, HUMAN_VIEW_OBS_DIM), dtype=np.float32)
    observations[:, 0] = np.linspace(0.0, 0.01, row_count)
    targets = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 2.0],
            [2.0, 2.0, 0.0],
            [0.0, 2.0, 2.0],
        ],
        dtype=np.float32,
    )
    seed_seq = np.arange(10, 10 + row_count, dtype=np.int64)
    episode_id_seq = np.arange(row_count, dtype=np.int64)
    step_seq = np.arange(row_count, dtype=np.int64)

    pairs, pair_summary, threshold = capability_pair_rows(
        student_obs_seq=observations,
        capability_target_seq=targets,
        seed_seq=seed_seq,
        episode_id_seq=episode_id_seq,
        step_seq=step_seq,
        response_dim=HUMAN_VIEW_RESPONSE_FEATURE_DIM,
        nearest_k=3,
        min_target_z_delta=0.5,
        max_pairs_per_target=2,
        max_visible_quantile=1.0,
    )

    assert threshold >= 0.0
    assert pairs
    assert len(pair_summary) == len(TARGETS)
    for row in pairs:
        assert 0 <= int(row["left_row"]) < row_count
        assert 0 <= int(row["right_row"]) < row_count
        assert int(row["left_seed"]) == int(seed_seq[int(row["left_row"])])
        assert int(row["right_seed"]) == int(seed_seq[int(row["right_row"])])
        assert float(row["target_z_delta"]) >= 0.5
