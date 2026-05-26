import argparse

import pytest

from autodrift.branch_preserving_temporal_repair_evaluator import (
    branch_residuals,
    branch_weight_for_row,
    classify_branch_preserving_evaluator,
    failure_types_for_result_class,
    separation_floor,
    _parse_active_rows,
)


def test_branch_weights_prioritize_active_rows() -> None:
    assert branch_weight_for_row(6) == 4.0
    assert branch_weight_for_row(15) == 4.0
    assert branch_weight_for_row(11) == 2.0
    assert branch_weight_for_row(16) == 2.0
    assert branch_weight_for_row(0) == 1.0


def test_separation_floor_uses_absolute_minimum() -> None:
    assert separation_floor(0.10, fraction=0.75, absolute=0.02) == pytest.approx(0.075)
    assert separation_floor(0.01, fraction=0.75, absolute=0.02) == 0.02


def test_branch_residuals_are_zero_inside_ceiling_and_floor() -> None:
    logp_delta, ceiling, separation = branch_residuals(
        candidate_wrong_logp=-2.0,
        base_wrong_logp=-2.0,
        candidate_separation=0.08,
        separation_floor_value=0.075,
        epsilon_logp=0.005,
    )
    assert logp_delta == 0.0
    assert ceiling == 0.0
    assert separation == 0.0


def test_branch_residuals_penalize_wrong_branch_lift_and_collapse() -> None:
    logp_delta, ceiling, separation = branch_residuals(
        candidate_wrong_logp=-1.90,
        base_wrong_logp=-2.0,
        candidate_separation=0.05,
        separation_floor_value=0.075,
        epsilon_logp=0.005,
    )
    assert round(logp_delta, 6) == 0.1
    assert ceiling > 0.0
    assert separation > 0.0


def test_evaluator_classifier_accepts_sensitive_no_update_metrics() -> None:
    result = classify_branch_preserving_evaluator(
        finite_metrics=True,
        base_branch_near_zero=True,
        proofwashing_candidates_active=True,
        temporal_base_reproduced=True,
        actor_parameters_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "branch_preserving_temporal_repair_evaluator_pass"
    assert failure_types_for_result_class(result) == ["none"]


def test_evaluator_classifier_flags_metric_artifact_when_not_sensitive() -> None:
    result = classify_branch_preserving_evaluator(
        finite_metrics=True,
        base_branch_near_zero=True,
        proofwashing_candidates_active=False,
        temporal_base_reproduced=True,
        actor_parameters_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "branch_preserving_temporal_repair_evaluator_not_sensitive"
    assert failure_types_for_result_class(result) == ["metric_artifact"]


def test_parse_active_rows_rejects_empty() -> None:
    assert _parse_active_rows("6,15") == (6, 15)
    try:
        _parse_active_rows("")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("empty active rows should fail")
