import numpy as np
import pandas as pd
import torch

from autodrift.paired_hidden_snapshots import (
    SnapshotPairRecord,
    build_snapshot_arrays,
    summarize_snapshot_export,
)


class _Snapshot:
    def __init__(self, observation: np.ndarray, hidden: torch.Tensor, step: int):
        self.observation = observation
        self.hidden = hidden
        self.step = step


def _record(seed: int, accepted: bool) -> SnapshotPairRecord:
    pair_row = {
        "seed": seed,
        "pair_status": "paired",
        "accepted_match": accepted,
        "observation_distance": 0.1 * seed,
        "response_observation_distance": 0.05 * seed,
        "context_observation_distance": 0.02 * seed,
        "hidden_state_distance": 1.5 * seed,
    }
    nominal = _Snapshot(
        observation=np.asarray([seed, seed + 1], dtype=np.float32),
        hidden=torch.tensor([[seed, seed + 2]], dtype=torch.float32),
        step=10 + seed,
    )
    perturbed = _Snapshot(
        observation=np.asarray([seed + 3, seed + 4], dtype=np.float32),
        hidden=torch.tensor([[seed + 5, seed + 6]], dtype=torch.float32),
        step=20 + seed,
    )
    return SnapshotPairRecord(seed=seed, pair_row=pair_row, nominal=nominal, perturbed=perturbed)


def test_build_snapshot_arrays_exports_accepted_pairs_only_by_default():
    arrays = build_snapshot_arrays([_record(1, True), _record(2, False)])

    np.testing.assert_array_equal(arrays["seed"], np.asarray([1]))
    np.testing.assert_array_equal(arrays["accepted_match"], np.asarray([True]))
    np.testing.assert_array_equal(arrays["nominal_step"], np.asarray([11]))
    np.testing.assert_allclose(arrays["nominal_observation"], np.asarray([[1, 2]], dtype=np.float32))
    np.testing.assert_allclose(arrays["perturbed_observation"], np.asarray([[4, 5]], dtype=np.float32))
    np.testing.assert_allclose(arrays["nominal_hidden"], np.asarray([[1, 3]], dtype=np.float32))
    np.testing.assert_allclose(arrays["perturbed_hidden"], np.asarray([[6, 7]], dtype=np.float32))


def test_build_snapshot_arrays_can_include_unaccepted_pairs():
    arrays = build_snapshot_arrays([_record(1, True), _record(2, False)], accepted_only=False)

    np.testing.assert_array_equal(arrays["seed"], np.asarray([1, 2]))
    np.testing.assert_array_equal(arrays["accepted_match"], np.asarray([True, False]))


def test_summarize_snapshot_export_counts_pairs_and_distances():
    pair_frame = pd.DataFrame([_record(1, True).pair_row, _record(2, False).pair_row])
    arrays = build_snapshot_arrays([_record(1, True), _record(2, False)])

    summary = summarize_snapshot_export(pair_frame, arrays)

    assert summary["seeds"] == 2
    assert summary["paired"] == 2
    assert summary["accepted_matches"] == 1
    assert summary["exported_pairs"] == 1
    assert np.isclose(summary["accepted_rate"], 0.5)
    assert np.isclose(summary["mean_hidden_state_distance"], 2.25)
    assert np.isclose(summary["exported_mean_hidden_state_distance"], 1.5)
