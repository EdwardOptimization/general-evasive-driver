import pandas as pd
import pytest

from autodrift.margin_weighted_branch_trust_region_evaluator import (
    classify_margin_weighted_branch_trust_evaluator,
    failure_types_for_result_class,
    load_base_wrong_margins,
    margin_scaled_contribution,
    margin_slack,
    source_normalized_weight,
)


def test_margin_slack_uses_absolute_margin_and_floor() -> None:
    assert margin_slack(-0.00025, margin_floor=1e-4) == pytest.approx(0.00025)
    assert margin_slack(-0.000025, margin_floor=1e-4) == pytest.approx(1e-4)


def test_margin_scaled_contribution_amplifies_near_cliff_primary_rows() -> None:
    total_source = 12.0
    row15 = margin_scaled_contribution(
        row_id=15,
        action_l2_sq=1e-8,
        base_wrong_margin=-2.5e-5,
        margin_floor=1e-4,
        total_source_weight=total_source,
    )
    row11 = margin_scaled_contribution(
        row_id=11,
        action_l2_sq=1e-8,
        base_wrong_margin=-3.26e-4,
        margin_floor=1e-4,
        total_source_weight=total_source,
    )
    assert source_normalized_weight(15, total_source) == pytest.approx(4.0 / total_source)
    assert row15 > row11


def test_load_base_wrong_margins_filters_policy_and_active_rows(tmp_path) -> None:
    path = tmp_path / "rows.csv"
    pd.DataFrame(
        [
            {"policy": "m974_base", "row_id": 6, "wrong_history_margin": -0.000117},
            {"policy": "candidate", "row_id": 6, "wrong_history_margin": 0.000033},
            {"policy": "m974_base", "row_id": 15, "wrong_history_margin": -0.000025},
        ]
    ).to_csv(path, index=False)
    margins = load_base_wrong_margins(path, active_rows=(6, 15))
    assert margins == {6: pytest.approx(-0.000117), 15: pytest.approx(-0.000025)}


def test_load_base_wrong_margins_rejects_missing_active_row(tmp_path) -> None:
    path = tmp_path / "rows.csv"
    pd.DataFrame([{"policy": "m974_base", "row_id": 6, "wrong_history_margin": -0.000117}]).to_csv(
        path,
        index=False,
    )
    with pytest.raises(ValueError, match="missing active row"):
        load_base_wrong_margins(path, active_rows=(6, 15))


def test_margin_weighted_classifier_accepts_sensitive_no_update_metrics() -> None:
    result = classify_margin_weighted_branch_trust_evaluator(
        finite_metrics=True,
        base_trust_zero=True,
        alpha_0_01_active=True,
        alpha_0_2_increases=True,
        primary_rows_dominate=True,
        actor_parameters_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "margin_weighted_branch_trust_region_evaluator_pass"
    assert failure_types_for_result_class(result) == ["none"]


def test_margin_weighted_classifier_flags_metric_artifact_when_not_sensitive() -> None:
    result = classify_margin_weighted_branch_trust_evaluator(
        finite_metrics=True,
        base_trust_zero=True,
        alpha_0_01_active=False,
        alpha_0_2_increases=True,
        primary_rows_dominate=True,
        actor_parameters_changed=False,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    assert result == "margin_weighted_branch_trust_region_evaluator_not_sensitive"
    assert failure_types_for_result_class(result) == ["metric_artifact"]
