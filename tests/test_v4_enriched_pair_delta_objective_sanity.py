from __future__ import annotations

import numpy as np

from autodrift.v4_enriched_pair_delta_objective_sanity import (
    action_vector,
    classify_enriched_pair_delta_objective_sanity,
    pair_requests,
    row_weight,
)


def _row(**overrides):
    row = {
        "left_source_group_id": "10",
        "right_source_group_id": "20",
        "left_step": "21",
        "right_step": "21",
        "normal_first_steer": "0.1",
        "normal_first_throttle": "0.2",
        "normal_first_brake": "0.0",
        "first_override_steer": "0.15",
        "first_override_throttle": "0.2",
        "first_override_brake": "0.0",
        "objective_sample_weight": "1.0",
        "abs_margin_delta": "0.02",
        "terminal_reason": "collision",
    }
    row.update(overrides)
    return row


def test_action_vector_reads_prefixed_fields() -> None:
    vec = action_vector(_row(), "normal_first")

    assert np.allclose(vec, [0.1, 0.2, 0.0])


def test_pair_requests_deduplicates_source_step_pairs() -> None:
    requests = pair_requests([_row(), _row(), _row(left_source_group_id="11")])

    assert requests == [
        {"left_source_group_id": 10, "right_source_group_id": 20, "left_step": 21, "right_step": 21},
        {"left_source_group_id": 11, "right_source_group_id": 20, "left_step": 21, "right_step": 21},
    ]


def test_row_weight_caps_collision_weight() -> None:
    assert row_weight(_row(abs_margin_delta="0.50")) == 10.0


def test_classify_enriched_pair_delta_objective_sanity_pass() -> None:
    result = classify_enriched_pair_delta_objective_sanity(
        tensor_rows_reconstructed=10,
        expected_rows=10,
        missing_tensor_count=0,
        exact_losses_finite=True,
        improvement_rows_present=True,
        degradation_rows_present=True,
        per_split_metrics_written=True,
        actor_parameters_changed=False,
    )

    assert result == "v4_enriched_pair_delta_objective_sanity_pass"


def test_classify_enriched_pair_delta_objective_sanity_reconstruction_blocked() -> None:
    result = classify_enriched_pair_delta_objective_sanity(
        tensor_rows_reconstructed=9,
        expected_rows=10,
        missing_tensor_count=1,
        exact_losses_finite=True,
        improvement_rows_present=True,
        degradation_rows_present=True,
        per_split_metrics_written=True,
        actor_parameters_changed=False,
    )

    assert result == "v4_enriched_pair_delta_objective_sanity_reconstruction_blocked"
