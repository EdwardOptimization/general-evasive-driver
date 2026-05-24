import numpy as np
import pandas as pd

from autodrift.combined_shape_source_diversity_expansion import default_shape_grid_specs
from autodrift.source_diverse_sequence_target_corpus import (
    add_source_balanced_weights,
    materialize_candidate_sequence,
    select_balanced_candidates,
    split_for_source,
    source_balance_summary,
)
from autodrift.trust_projected_sequence_shape import build_projected_sequence_candidates


def test_split_for_source_keeps_physical_pair_group_together():
    assert split_for_source(20) == "source_holdout_validation"
    assert split_for_source(32) == "source_holdout_validation"
    assert split_for_source(13) == "train"


def test_select_balanced_candidates_caps_per_source_and_grid():
    rows = []
    for idx in range(20):
        rows.append(_accepted_row(source=13, grid="source8_recovery_style", family="targeted_constant_delta", idx=idx))
    for idx in range(20):
        rows.append(_accepted_row(source=13, grid="source7_preservation_style", family="targeted_decay_hold", idx=idx))
    for idx in range(20):
        rows.append(_accepted_row(source=14, grid="source8_recovery_style", family="targeted_constant_delta", idx=idx))
    frame = pd.DataFrame(rows)

    selected = select_balanced_candidates(
        frame,
        max_rows_per_source=16,
        max_rows_per_source_grid=8,
        max_rows_per_source_family=16,
        max_rows_per_source_sequence_length=16,
    )

    assert selected["source_index"].value_counts().max() == 16
    assert selected.groupby(["source_index", "grid_name"], observed=True).size().max() == 8


def test_add_source_balanced_weights_equalizes_source_totals():
    frame = pd.DataFrame(
        [
            _accepted_row(source=13, grid="source8_recovery_style", family="targeted_constant_delta", idx=0),
            _accepted_row(source=13, grid="source8_recovery_style", family="targeted_constant_delta", idx=1),
            _accepted_row(source=7, grid="source7_preservation_style", family="targeted_decay_hold", idx=0),
        ]
    )

    weighted = add_source_balanced_weights(frame)
    totals = weighted.groupby("source_index")["corpus_weight"].sum().to_dict()

    assert totals[13] == 0.5
    assert totals[7] == 0.5


def test_materialize_candidate_sequence_matches_grid_candidate_id():
    spec = default_shape_grid_specs()[0]
    base = np.zeros((9, 3), dtype=np.float32)
    offset = 0
    target = None
    for length in spec.sequence_lengths:
        candidates = build_projected_sequence_candidates(
            base[:length],
            steer_deltas=spec.steer_deltas,
            throttle_deltas=spec.throttle_deltas,
            brake_deltas=spec.brake_deltas,
            families=spec.families,
            per_step_action_l2=0.10,
            sequence_mean_l2_limit=0.08,
            sequence_max_l2_limit=0.10,
            max_delta_delta_l2_limit=0.08,
        )
        candidate = candidates[-1]
        target = (offset + candidate.candidate.candidate_id, candidate.candidate)
        offset += len(candidates)
    assert target is not None
    candidate_id, candidate = target
    row = pd.Series(
        {
            "grid_name": spec.name,
            "candidate_id": candidate_id,
            "sequence_length": candidate.sequence_length,
            "family": candidate.family,
        }
    )

    target_sequence, base_sequence = materialize_candidate_sequence(row, base)

    assert target_sequence.shape == base_sequence.shape
    assert target_sequence.shape[0] == candidate.sequence_length
    assert np.allclose(target_sequence, candidate.action_sequence)


def test_source_balance_summary_records_grid_and_weight_totals():
    frame = pd.DataFrame(
        [
                {
                    **_accepted_row(source=13, grid="source8_recovery_style", family="targeted_constant_delta", idx=0),
                    "corpus_weight": 0.5,
                    "split": "train",
                },
                {
                    **_accepted_row(source=13, grid="source7_preservation_style", family="targeted_decay_hold", idx=1),
                    "corpus_weight": 0.5,
                    "split": "train",
                },
        ]
    )

    rows = source_balance_summary(frame)

    assert rows[0]["rows"] == 2
    assert rows[0]["weight_sum"] == 1.0
    assert rows[0]["grid_names"] == "source7_preservation_style;source8_recovery_style"


def _accepted_row(source: int, grid: str, family: str, idx: int) -> dict[str, object]:
    return {
        "source_index": source,
        "grid_name": grid,
        "family": family,
        "sequence_length": 9 if idx % 2 == 0 else 7,
        "margin_improvement": 1.0 / (idx + 1),
        "risk_improvement": 1.0 / (idx + 2),
        "sequence_mean_l2": 0.02 + idx * 1e-4,
        "sequence_max_l2": 0.04 + idx * 1e-4,
        "max_delta_delta_l2": 0.01,
        "target": "future_yaw_response",
        "surface": "fresh",
        "variant": "delayed_history",
    }
