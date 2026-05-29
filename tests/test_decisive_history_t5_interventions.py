from __future__ import annotations

from autodrift.decisive_history_t5_interventions import (
    DONOR_MODE,
    ELIGIBLE_MODES,
    INTERVENTION_VARIANTS,
    build_intervention_summary,
    build_pair_summary,
    donor_spec_for_mode,
    eligible_retarget_specs,
    finalize_intervention_rows,
)


def test_eligible_retarget_specs_are_high_speed_modes_only() -> None:
    specs = eligible_retarget_specs()
    assert len(specs) == 4
    assert {item.retarget_mode for item in specs} == set(ELIGIBLE_MODES)
    assert {item.hook_spec.source_family for item in specs} == {"t5_high_speed_close_obstacle"}
    assert all(item.hook_spec.env_config.history_length == 1 for item in specs)
    assert all(not item.hook_spec.labels_enter_actor_input for item in specs)


def test_donor_spec_for_mode_uses_cycle() -> None:
    specs = eligible_retarget_specs()
    for mode, donor_mode in DONOR_MODE.items():
        donor = donor_spec_for_mode(specs, mode)
        assert donor is not None
        assert donor.retarget_mode == donor_mode


def test_intervention_variant_set_contains_required_controls() -> None:
    assert {
        "normal",
        "reset_hidden_once",
        "reset_hidden_every_step",
        "zero_current_response",
        "zero_action_history",
        "delayed_hidden_8",
        "wrong_history_donor_hidden",
    } <= set(INTERVENTION_VARIANTS)


def test_finalize_rows_computes_margin_gap_and_success_drop() -> None:
    rows = [
        {
            "candidate_id": "c0",
            "variant": "normal",
            "target_replay_status": "ok",
            "first_action_steer": 0.0,
            "first_action_throttle": 0.1,
            "first_action_brake": 0.0,
            "terminal_margin": 0.5,
            "success": True,
        },
        {
            "candidate_id": "c0",
            "variant": "reset_hidden_once",
            "target_replay_status": "ok",
            "first_action_steer": 0.3,
            "first_action_throttle": 0.1,
            "first_action_brake": 0.0,
            "terminal_margin": -0.1,
            "success": False,
        },
    ]
    finalized = finalize_intervention_rows(rows)
    reset_row = finalized[1]
    assert reset_row["normal_terminal_margin"] == 0.5
    assert reset_row["margin_gap_from_normal"] == 0.6
    assert reset_row["success_drop_from_normal"] is True
    assert reset_row["normal_first_action_l2"] == 0.3


def test_pair_summary_marks_outcome_relevant_variants() -> None:
    rows = finalize_intervention_rows(
        [
            {
                "candidate_id": "c0",
                "retarget_mode": "close_wide",
                "variant": "normal",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.4,
                "success": True,
            },
            {
                "candidate_id": "c0",
                "retarget_mode": "close_wide",
                "variant": "zero_action_history",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.1,
                "success": True,
            },
        ]
    )
    summary = build_pair_summary(rows)
    assert summary[0]["candidate_id"] == "c0"
    assert summary[0]["max_margin_gap_from_normal"] == 0.30000000000000004
    assert summary[0]["outcome_relevant_variants"] == "zero_action_history"


def test_intervention_summary_keeps_guardrails_false() -> None:
    rows = finalize_intervention_rows(
        [
            {
                "candidate_id": "c0",
                "variant": "normal",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.4,
                "success": True,
            },
            {
                "candidate_id": "c0",
                "variant": "wrong_history_donor_hidden",
                "target_replay_status": "ok",
                "donor_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.3,
                "success": True,
            },
        ]
    )
    pairs = build_pair_summary(rows)
    summary = build_intervention_summary(rows, pairs, eligible_target_count=1, variant_count=2, continuation_steps=64)
    assert summary["intervention_row_count"] == 2
    assert summary["wrong_history_row_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
