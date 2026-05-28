from __future__ import annotations

from autodrift.capability_separable_source_constructor import (
    classify_capability_separable_result,
    evaluate_action_separability,
)


def _row(condition: str, candidate_id: int, steer: float, margin: float, success: bool = True):
    return {
        "condition": condition,
        "candidate_id": candidate_id,
        "candidate_steer": steer,
        "candidate_throttle": 0.0,
        "candidate_brake": 0.0,
        "action_l2_from_shared_base": abs(steer),
        "min_clearance_margin": margin,
        "success": success,
        "collision": not success,
    }


def test_evaluate_action_separability_accepts_cross_regret():
    result = evaluate_action_separability(
        pair_id=7,
        candidate_rows=[
            _row("A", 0, -0.2, 0.10),
            _row("A", 1, 0.2, 0.02),
            _row("B", 0, -0.2, 0.01),
            _row("B", 1, 0.2, 0.11),
        ],
        min_best_action_l2=0.25,
        min_cross_regret_margin=0.05,
    )

    assert result["accepted"]
    assert result["best_candidate_A"] == 0
    assert result["best_candidate_B"] == 1
    assert result["cross_regret_A"] > 0.05
    assert result["cross_regret_B"] > 0.05


def test_evaluate_action_separability_rejects_low_regret():
    result = evaluate_action_separability(
        pair_id=8,
        candidate_rows=[
            _row("A", 0, -0.2, 0.10),
            _row("A", 1, 0.2, 0.09),
            _row("B", 0, -0.2, 0.09),
            _row("B", 1, 0.2, 0.10),
        ],
        min_best_action_l2=0.25,
        min_cross_regret_margin=0.05,
    )

    assert not result["accepted"]
    assert result["rejection_reason"] == "insufficient_cross_regret"


def test_classify_capability_separable_result():
    assert (
        classify_capability_separable_result(
            matched_pair_count=0,
            action_rollouts=0,
            accepted_separable_pairs=0,
            best_actions_diverged_pairs=0,
            low_regret_pairs=0,
        )
        == "matched_state_empty"
    )
    assert (
        classify_capability_separable_result(
            matched_pair_count=10,
            action_rollouts=100,
            accepted_separable_pairs=1,
            best_actions_diverged_pairs=1,
            low_regret_pairs=0,
        )
        == "capability_separable_signal"
    )
    assert (
        classify_capability_separable_result(
            matched_pair_count=10,
            action_rollouts=100,
            accepted_separable_pairs=0,
            best_actions_diverged_pairs=3,
            low_regret_pairs=3,
        )
        == "action_divergent_low_regret"
    )
