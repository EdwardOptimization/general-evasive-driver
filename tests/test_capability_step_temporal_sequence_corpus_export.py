import numpy as np
import pandas as pd

from autodrift.capability_step_temporal_sequence_corpus_export import (
    _pad_2d_sequence,
    compute_row_weights,
    load_positive_temporal_rows,
)


def test_pad_2d_sequence_masks_and_pads():
    values, mask = _pad_2d_sequence(
        [np.array([1.0, 2.0], dtype=np.float32), np.array([3.0, 4.0], dtype=np.float32)],
        length=4,
        width=2,
    )

    assert values.shape == (4, 2)
    assert mask.tolist() == [True, True, False, False]
    assert np.all(values[0] == np.array([1.0, 2.0], dtype=np.float32))
    assert np.all(values[2:] == 0.0)


def test_compute_row_weights_balances_variant_and_pair_counts():
    rows = pd.DataFrame(
        [
            {"variant": "reset_then_warm_history", "fault_pair": "a->b"},
            {"variant": "reset_then_warm_history", "fault_pair": "a->b"},
            {"variant": "reset_then_warm_history", "fault_pair": "a->b"},
            {"variant": "delayed_capability_history", "fault_pair": "c->d"},
        ]
    )

    weights = compute_row_weights(rows)

    assert weights.shape == (4,)
    assert abs(float(weights.mean()) - 1.0) < 1e-6
    assert weights[-1] > weights[0]


def test_load_positive_temporal_rows_filters_diagnostics(tmp_path):
    run_dir = tmp_path / "m994"
    run_dir.mkdir()
    pd.DataFrame(
        [
            {"variant": "reset_then_warm_history", "sequence_outcome_critical": True},
            {"variant": "delayed_capability_history", "sequence_outcome_critical": True},
            {"variant": "cross_fault_response_window", "sequence_outcome_critical": True},
            {"variant": "zero_command_history_window", "sequence_outcome_critical": True},
            {"variant": "reset_then_warm_history", "sequence_outcome_critical": False},
        ]
    ).to_csv(run_dir / "accepted_sequence_rows.csv", index=False)

    rows = load_positive_temporal_rows(run_dir)

    assert rows["variant"].tolist() == ["reset_then_warm_history", "delayed_capability_history"]
