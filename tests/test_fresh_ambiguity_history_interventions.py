import pytest

from autodrift.fresh_ambiguity_history_interventions import (
    AcceptedMeasuredPair,
    build_pair_summary,
    build_summary,
    build_variant_summary,
    finalize_rows,
    load_accepted_pairs,
    source_row_key,
    source_rows_by_trace_id,
)
from autodrift.fresh_ambiguity_source_mining import default_source_specs, expand_source_specs


def test_source_rows_by_trace_id_matches_measured_trace_ids():
    rows = source_rows_by_trace_id(source_seed=1531, seed_count=1)

    assert "capability_step_down|153700|fresh-capability_step_down-000" in rows
    assert "capability_step_up|153800|fresh-capability_step_up-000" in rows
    assert all(key == source_row_key(row) for key, row in rows.items())


def test_load_accepted_pairs_filters_rejected_rows(tmp_path):
    path = tmp_path / "pairs.csv"
    path.write_text(
        "\n".join(
            [
                "pair_id,left_trace_id,right_trace_id,left_source_family,right_source_family,task_family,scene_context_distance,current_ego_distance,recent_window_distance,older_evidence_distance,hidden_capability_distance,first_action_l2,prefix_action_l2,terminal_margin_gap,accepted,reasons",
                "pair-a,left,right,a,b,T4,0.01,0.02,0.02,0.2,0.2,0.3,0.3,1.0,True,",
                "pair-b,left,right,a,b,T4,0.01,0.02,0.02,0.2,0.2,0.3,0.3,1.0,False,weak",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    pairs = load_accepted_pairs(path)

    assert len(pairs) == 1
    assert pairs[0].pair_id == "pair-a"
    assert pairs[0].first_action_l2 == 0.3


def test_finalize_rows_attaches_normal_comparisons():
    rows = [
        {
            "pair_id": "pair",
            "target_side": "left",
            "anchor_name": "decision",
            "variant": "normal",
            "target_replay_status": "ok",
            "first_action_steer": 0.0,
            "first_action_throttle": 0.0,
            "first_action_brake": 0.0,
            "terminal_margin": 1.0,
            "success": True,
        },
        {
            "pair_id": "pair",
            "target_side": "left",
            "anchor_name": "decision",
            "variant": "wrong_history_donor_hidden_at_anchor",
            "target_replay_status": "ok",
            "first_action_steer": 0.2,
            "first_action_throttle": 0.0,
            "first_action_brake": 0.0,
            "terminal_margin": 0.4,
            "success": False,
        },
    ]

    finalized = finalize_rows(rows)

    assert finalized[1]["normal_first_action_l2"] == 0.2
    assert finalized[1]["normal_terminal_margin"] == 1.0
    assert finalized[1]["terminal_margin_gap_from_normal"] == 0.6
    assert finalized[1]["success_drop_from_normal"] is True


def test_finalize_rows_leaves_missing_action_failure_rows_unchanged():
    rows = [
        {
            "pair_id": "pair",
            "target_side": "left",
            "anchor_name": "reveal_plus_4",
            "variant": "normal",
            "target_replay_status": "ok",
            "first_action_steer": 0.0,
            "first_action_throttle": 0.0,
            "first_action_brake": 0.0,
            "terminal_margin": 1.0,
            "success": True,
        },
        {
            "pair_id": "pair",
            "target_side": "left",
            "anchor_name": "reveal_plus_4",
            "variant": "delayed_hidden_16_at_anchor",
            "target_replay_status": "ok",
            "first_action_steer": "",
            "first_action_throttle": "",
            "first_action_brake": "",
            "terminal_margin": "",
            "success": False,
        },
    ]

    finalized = finalize_rows(rows)

    assert finalized[1]["first_action_steer"] == ""
    assert finalized[1].get("terminal_margin_gap_from_normal") is None


def test_pair_and_variant_summaries_separate_channels():
    rows = finalize_rows(
        [
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "normal",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 1.0,
                "success": True,
            },
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "donor_response_action_stream_from_anchor",
                "target_replay_status": "ok",
                "first_action_steer": 0.1,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.7,
                "success": True,
            },
        ]
    )

    pair_summary = build_pair_summary(rows)
    variant_summary = build_variant_summary(rows)

    assert pair_summary[0]["donor_response_action_row_count"] == 1
    assert pair_summary[0]["max_donor_response_action_margin_gap"] == pytest.approx(0.3)
    assert {row["variant"] for row in variant_summary} == {
        "normal",
        "donor_response_action_stream_from_anchor",
    }


def test_build_summary_keeps_guardrails_false_and_detects_quality():
    pair = AcceptedMeasuredPair(
        pair_id="pair",
        left_trace_id="left",
        right_trace_id="right",
        left_source_family="a",
        right_source_family="b",
        task_family="T4",
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        first_action_l2=0.2,
        terminal_margin_gap=1.0,
    )
    rows = finalize_rows(
        [
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "normal",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 1.0,
                "success": True,
            },
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "wrong_history_donor_hidden_at_anchor",
                "target_replay_status": "ok",
                "first_action_steer": 0.2,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.4,
                "success": False,
            },
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "donor_response_action_stream_from_anchor",
                "target_replay_status": "ok",
                "first_action_steer": 0.1,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 0.5,
                "success": True,
            },
            {
                "pair_id": "pair",
                "target_side": "left",
                "anchor_name": "decision",
                "variant": "reset_hidden_once_at_anchor",
                "target_replay_status": "ok",
                "first_action_steer": 0.0,
                "first_action_throttle": 0.0,
                "first_action_brake": 0.0,
                "terminal_margin": 1.0,
                "success": True,
            },
        ]
    )

    summary = build_summary(pairs=(pair, pair, pair), rows=rows, pair_summary=build_pair_summary(rows), continuation_steps=64)

    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
    assert summary["passes_evidence_quality_targets"] is True
    assert summary["max_wrong_history_margin_gap"] == 0.6


def test_default_rows_are_importable_without_materialization():
    rows = expand_source_specs(default_source_specs(seed=1531, seed_count=1))

    assert rows
    assert all(row.candidate_materialized is False for row in rows)
