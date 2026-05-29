from __future__ import annotations

import numpy as np

from autodrift.decisive_history_t5_response_mismatch import (
    ACTION_HISTORY_SLICE,
    EGO_RESPONSE_SLICE,
    RESPONSE_MISMATCH_ANCHORS,
    RESPONSE_MISMATCH_VARIANTS,
    RESPONSE_SLICE,
    DonorObservationStream,
    apply_response_mismatch,
    build_response_mismatch_summary,
    build_variant_summary,
    donor_frame_at,
)
from autodrift.decisive_history_t5_timing_interventions import (
    STATE_DELTA_FIELDS,
    build_anchor_summary,
    build_timing_pair_summary,
    finalize_timing_rows,
)


def test_response_mismatch_variants_and_anchors_are_bounded() -> None:
    assert {"reveal", "decision_minus_8", "decision"} <= set(RESPONSE_MISMATCH_ANCHORS)
    assert {
        "normal",
        "donor_response_current_frame_at_anchor",
        "donor_ego_response_stream_from_anchor",
        "donor_action_history_stream_from_anchor",
        "donor_response_action_stream_from_anchor",
        "donor_response_action_plus_hidden_from_anchor",
        "zero_current_response_from_anchor",
    } <= set(RESPONSE_MISMATCH_VARIANTS)


def test_apply_response_mismatch_preserves_scene_context() -> None:
    target = np.arange(72, dtype=np.float32)
    donor = np.arange(100, 172, dtype=np.float32)
    transformed = apply_response_mismatch(
        target,
        donor,
        variant="donor_response_action_stream_from_anchor",
        relative_step=3,
    )
    assert np.all(transformed[RESPONSE_SLICE] == donor[RESPONSE_SLICE])
    assert np.all(transformed[12:] == target[12:])


def test_apply_response_mismatch_can_swap_substreams() -> None:
    target = np.arange(72, dtype=np.float32)
    donor = np.arange(100, 172, dtype=np.float32)
    ego = apply_response_mismatch(target, donor, variant="donor_ego_response_stream_from_anchor", relative_step=1)
    assert np.all(ego[EGO_RESPONSE_SLICE] == donor[EGO_RESPONSE_SLICE])
    assert np.all(ego[ACTION_HISTORY_SLICE] == target[ACTION_HISTORY_SLICE])
    action = apply_response_mismatch(
        target,
        donor,
        variant="donor_action_history_stream_from_anchor",
        relative_step=1,
    )
    assert np.all(action[EGO_RESPONSE_SLICE] == target[EGO_RESPONSE_SLICE])
    assert np.all(action[ACTION_HISTORY_SLICE] == donor[ACTION_HISTORY_SLICE])


def test_current_frame_variant_only_swaps_at_anchor() -> None:
    target = np.arange(72, dtype=np.float32)
    donor = np.arange(100, 172, dtype=np.float32)
    at_anchor = apply_response_mismatch(
        target,
        donor,
        variant="donor_response_current_frame_at_anchor",
        relative_step=0,
    )
    later = apply_response_mismatch(
        target,
        donor,
        variant="donor_response_current_frame_at_anchor",
        relative_step=2,
    )
    assert np.all(at_anchor[RESPONSE_SLICE] == donor[RESPONSE_SLICE])
    assert np.all(later == target)


def test_donor_frame_at_reuses_last_frame_after_exhaustion() -> None:
    first = np.zeros(72, dtype=np.float32)
    second = np.ones(72, dtype=np.float32)
    stream = DonorObservationStream(status="ok", candidate_id="d0", frames=[first, second], hidden=None)
    frame, exhausted = donor_frame_at(stream, 3)
    assert exhausted is True
    assert frame is second


def _base_row(variant: str, *, margin: float) -> dict:
    row = {
        "candidate_id": "c0",
        "retarget_mode": "close_wide",
        "anchor_name": "reveal",
        "anchor_step": 18,
        "variant": variant,
        "target_replay_status": "ok",
        "donor_response_l2_mean": 0.2,
        "first_action_steer": 0.0,
        "first_action_throttle": 0.0,
        "first_action_brake": 0.0,
        "decision_action_steer": 0.0,
        "decision_action_throttle": 0.0,
        "decision_action_brake": 0.0,
        "terminal_margin": margin,
        "success": True,
    }
    for field in STATE_DELTA_FIELDS:
        row[f"decision_state_{field}"] = 0.0
    return row


def test_response_mismatch_summary_keeps_guardrails_false() -> None:
    rows = finalize_timing_rows(
        [
            _base_row("normal", margin=0.5),
            _base_row("donor_response_action_stream_from_anchor", margin=0.4),
        ]
    )
    pair_rows = build_timing_pair_summary(rows)
    anchor_rows = build_anchor_summary(pair_rows)
    variant_rows = build_variant_summary(rows)
    summary = build_response_mismatch_summary(
        rows,
        pair_rows,
        anchor_rows,
        variant_rows,
        eligible_target_count=1,
        anchor_count=1,
        variant_count=2,
        continuation_steps=64,
    )
    assert summary["intervention_row_count"] == 2
    assert summary["max_donor_response_l2_mean"] == 0.2
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
