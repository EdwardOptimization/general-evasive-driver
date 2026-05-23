import pytest

from autodrift.tail_action_sequence_amplification_gate import (
    parse_hold_steps,
    summarize_amplification_proof,
    tail_amplification_variant_specs,
)


def test_parse_hold_steps_deduplicates_and_rejects_non_positive_values():
    assert parse_hold_steps("2,4,4,8") == (2, 4, 8)
    with pytest.raises(ValueError, match="positive"):
        parse_hold_steps("2,0")


def test_tail_amplification_variant_specs_separate_natural_and_diagnostic_rows():
    specs = tail_amplification_variant_specs((2, 4))
    by_name = {spec.name: spec for spec in specs}

    assert by_name["wrong_tail_once"].family == "wrong_tail_once"
    assert by_name["wrong_tail_once"].hold_steps == 1
    assert not by_name["wrong_tail_once"].clamp_hidden
    assert by_name["wrong_tail_hidden_hold_2"].family == "wrong_tail_hidden_hold"
    assert by_name["wrong_tail_hidden_hold_2"].hold_steps == 2
    assert by_name["wrong_tail_hidden_hold_2"].clamp_hidden
    assert by_name["reset_tail"].reset_hidden
    assert by_name["zero_current_tail"].zero_current_response


def test_summarize_amplification_proof_reports_best_hidden_hold_variant():
    rows = [
        {
            "variant": "wrong_tail_once",
            "variant_family": "wrong_tail_once",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
        {
            "variant": "wrong_tail_hidden_hold_2",
            "variant_family": "wrong_tail_hidden_hold",
            "proof_candidate": True,
            "success_drop": True,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
        {
            "variant": "wrong_tail_hidden_hold_2",
            "variant_family": "wrong_tail_hidden_hold",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": True,
            "obstacle_completion_drop": False,
            "probe_seed": 2,
            "left_obstacle_label": "drift_required",
            "target": "future_braking_deceleration",
        },
        {
            "variant": "wrong_tail_hidden_hold_4",
            "variant_family": "wrong_tail_hidden_hold",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": False,
            "probe_seed": 1,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
        {
            "variant": "reset_tail",
            "variant_family": "baseline",
            "proof_candidate": True,
            "success_drop": False,
            "collision_gap": False,
            "obstacle_completion_drop": True,
            "probe_seed": 3,
            "left_obstacle_label": "unavoidable",
            "target": "future_yaw_response",
        },
    ]

    summary = summarize_amplification_proof(rows)

    assert summary["wrong_tail_once_total_proof_candidate_count"] == 1
    assert summary["wrong_tail_once_total_event_rows"] == 0
    assert summary["hidden_hold_total_proof_candidate_count"] == 3
    assert summary["hidden_hold_total_event_rows"] == 2
    assert summary["best_hidden_hold_variant"] == "wrong_tail_hidden_hold_2"
    assert summary["best_hidden_hold_event_rows"] == 2
    assert summary["best_hidden_hold_probe_seed_count"] == 2
    assert summary["best_hidden_hold_obstacle_label_count"] == 2
    assert summary["best_hidden_hold_target_count"] == 2
    assert summary["control_event_rows"] == 1
