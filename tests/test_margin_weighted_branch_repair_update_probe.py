import argparse

from autodrift.margin_weighted_branch_repair_update_probe import (
    _branch_gate_flags,
    classify_repair_update_probe,
    failure_types_for_result_class,
    parse_float_list,
)


def test_parse_float_list_rejects_empty_and_nonpositive() -> None:
    assert parse_float_list("0.001,0.003") == (0.001, 0.003)

    try:
        parse_float_list("")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("empty float list should fail")

    try:
        parse_float_list("0.0")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("nonpositive float should fail")


def test_branch_gate_flags_require_exact_near_cliff_rows() -> None:
    row = {
        "weighted_branch_trust_loss": 0.09,
        "primary_weighted_branch_trust_loss": 0.06,
        "max_weighted_row_contribution": 0.04,
        "row_6_contribution": 0.04,
        "row_15_contribution": 0.015,
        "row_16_contribution": 0.04,
    }
    flags = _branch_gate_flags(
        row,
        branch_trust_gate=0.10,
        primary_branch_trust_gate=0.07,
        max_row_contribution_gate=0.05,
        row6_contribution_gate=0.05,
        row15_contribution_gate=0.02,
        row16_contribution_gate=0.05,
    )
    assert flags["branch_gate_pass"] is True

    row["row_15_contribution"] = 0.021
    flags = _branch_gate_flags(
        row,
        branch_trust_gate=0.10,
        primary_branch_trust_gate=0.07,
        max_row_contribution_gate=0.05,
        row6_contribution_gate=0.05,
        row15_contribution_gate=0.02,
        row16_contribution_gate=0.05,
    )
    assert flags["row_15_contribution_pass"] is False
    assert flags["branch_gate_pass"] is False


def test_repair_update_classifier_routes_exact_branch_candidate() -> None:
    result = classify_repair_update_probe(
        raw_actor_mean_changed=True,
        raw_non_actor_changed=False,
        exact_candidate_count=2,
        branch_candidate_count=1,
        training_started=True,
        ppo_used=False,
        promoted=False,
    )
    assert result == "margin_weighted_branch_repair_update_exact_branch_candidate"
    assert failure_types_for_result_class(result) == ["none"]


def test_repair_update_classifier_flags_branch_trust_blocker() -> None:
    result = classify_repair_update_probe(
        raw_actor_mean_changed=True,
        raw_non_actor_changed=False,
        exact_candidate_count=2,
        branch_candidate_count=0,
        training_started=True,
        ppo_used=False,
        promoted=False,
    )
    assert result == "margin_weighted_branch_repair_update_branch_trust_blocked"
    assert failure_types_for_result_class(result) == ["proof_washout"]
