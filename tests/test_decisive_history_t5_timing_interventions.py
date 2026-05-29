from __future__ import annotations

from autodrift.decisive_history_t5_interventions import eligible_retarget_specs
from autodrift.decisive_history_t5_timing_interventions import (
    STATE_DELTA_FIELDS,
    TIMING_ANCHORS,
    TIMING_VARIANTS,
    anchor_step_for,
    build_anchor_summary,
    build_timing_pair_summary,
    build_timing_summary,
    finalize_timing_rows,
)


def test_anchor_step_for_bounds_named_anchors() -> None:
    spec = eligible_retarget_specs()[0].hook_spec
    assert anchor_step_for(spec, "decision") == spec.decision_step
    assert anchor_step_for(spec, "decision_minus_8") == max(spec.reveal_step, spec.decision_step - 8)
    assert anchor_step_for(spec, "reveal_plus_4") == min(spec.decision_step - 1, spec.reveal_step + 4)
    assert anchor_step_for(spec, "reveal") == spec.reveal_step


def test_timing_variants_contain_required_controls() -> None:
    assert {
        "normal",
        "reset_hidden_once_at_anchor",
        "reset_hidden_every_step_from_anchor",
        "zero_current_response_from_anchor",
        "zero_action_history_from_anchor",
        "delayed_hidden_8_at_anchor",
        "wrong_history_donor_hidden_at_anchor",
    } <= set(TIMING_VARIANTS)
    assert {"decision", "decision_minus_8", "reveal_plus_4", "reveal"} <= set(TIMING_ANCHORS)


def _base_row(variant: str, *, margin: float, success: bool = True) -> dict:
    row = {
        "candidate_id": "c0",
        "retarget_mode": "close_wide",
        "anchor_name": "reveal",
        "anchor_step": 18,
        "variant": variant,
        "target_replay_status": "ok",
        "first_action_steer": 0.0,
        "first_action_throttle": 0.0,
        "first_action_brake": 0.0,
        "decision_action_steer": 0.0,
        "decision_action_throttle": 0.0,
        "decision_action_brake": 0.0,
        "terminal_margin": margin,
        "success": success,
    }
    for field in STATE_DELTA_FIELDS:
        row[f"decision_state_{field}"] = 0.0
    return row


def test_finalize_timing_rows_groups_by_candidate_and_anchor() -> None:
    normal = _base_row("normal", margin=0.5)
    variant = _base_row("reset_hidden_every_step_from_anchor", margin=0.1)
    variant["first_action_steer"] = 0.3
    variant["decision_state_x"] = 0.4
    finalized = finalize_timing_rows([normal, variant])
    reset_row = finalized[1]
    assert reset_row["normal_terminal_margin"] == 0.5
    assert reset_row["margin_gap_from_normal"] == 0.4
    assert reset_row["success_drop_from_normal"] is False
    assert reset_row["normal_first_action_l2"] == 0.3
    assert reset_row["decision_state_delta_x"] == 0.4
    assert reset_row["decision_state_delta_l2"] == 0.4


def test_pair_and_anchor_summary_mark_outcome_and_divergence() -> None:
    normal = _base_row("normal", margin=0.5)
    variant = _base_row("zero_current_response_from_anchor", margin=-0.1, success=False)
    variant["first_action_steer"] = 0.2
    variant["decision_state_y"] = 0.3
    rows = finalize_timing_rows([normal, variant])
    pair_rows = build_timing_pair_summary(rows)
    assert pair_rows[0]["candidate_id"] == "c0"
    assert pair_rows[0]["anchor_name"] == "reveal"
    assert pair_rows[0]["max_margin_gap_from_normal"] == 0.6
    assert pair_rows[0]["success_drop_variants"] == "zero_current_response_from_anchor"
    assert pair_rows[0]["outcome_relevant_variant_count"] == 1
    assert pair_rows[0]["divergence_relevant_variant_count"] == 1
    anchor_rows = build_anchor_summary(pair_rows)
    assert anchor_rows[0]["anchor_name"] == "reveal"
    assert anchor_rows[0]["outcome_relevant_variant_count"] == 1
    assert anchor_rows[0]["divergence_relevant_variant_count"] == 1


def test_timing_summary_keeps_guardrails_false() -> None:
    rows = finalize_timing_rows(
        [
            _base_row("normal", margin=0.5),
            _base_row("wrong_history_donor_hidden_at_anchor", margin=0.4),
        ]
    )
    pair_rows = build_timing_pair_summary(rows)
    anchor_rows = build_anchor_summary(pair_rows)
    summary = build_timing_summary(
        rows,
        pair_rows,
        anchor_rows,
        eligible_target_count=1,
        anchor_count=1,
        variant_count=2,
        continuation_steps=64,
    )
    assert summary["intervention_row_count"] == 2
    assert summary["wrong_history_row_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
