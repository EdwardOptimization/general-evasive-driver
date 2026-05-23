from __future__ import annotations

from autodrift.current_family_rejected_boundary_targets import (
    rejected_boundary_acceptance,
    select_collision_side_target,
)


def test_rejected_boundary_acceptance_requires_failed_lower_margin():
    accepted, reason = rejected_boundary_acceptance(
        candidate_margin=-2.0e-5,
        candidate_success=False,
        baseline_margin=-1.0e-6,
        action_l2=0.02,
        min_margin_decrease=1.0e-5,
        max_action_l2=0.1,
    )
    assert accepted is True
    assert reason == "accepted"

    accepted, reason = rejected_boundary_acceptance(
        candidate_margin=-2.0e-5,
        candidate_success=True,
        baseline_margin=-1.0e-6,
        action_l2=0.02,
        min_margin_decrease=1.0e-5,
        max_action_l2=0.1,
    )
    assert accepted is False
    assert reason == "candidate_successful"

    accepted, reason = rejected_boundary_acceptance(
        candidate_margin=-2.0e-6,
        candidate_success=False,
        baseline_margin=-1.0e-6,
        action_l2=0.02,
        min_margin_decrease=1.0e-5,
        max_action_l2=0.1,
    )
    assert accepted is False
    assert reason == "insufficient_collision_margin_decrease"


def test_select_collision_side_target_prefers_larger_margin_decrease():
    rows = [
        {
            "accepted": True,
            "margin_decrease": 1.0e-5,
            "candidate_margin": -1.1e-5,
            "action_l2": 0.01,
            "candidate_id": 1,
        },
        {
            "accepted": True,
            "margin_decrease": 3.0e-5,
            "candidate_margin": -3.1e-5,
            "action_l2": 0.05,
            "candidate_id": 2,
        },
        {
            "accepted": False,
            "margin_decrease": 4.0e-5,
            "candidate_margin": -4.1e-5,
            "action_l2": 0.02,
            "candidate_id": 3,
        },
    ]

    selected = select_collision_side_target(rows)

    assert selected is not None
    assert selected["candidate_id"] == 2
