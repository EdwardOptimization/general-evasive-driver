from autodrift.gate_margin_replay_admission import summarize_replay_rows


def _row(
    *,
    normal_l2=0.002,
    normal_regression=0.0,
    wrong_margin=0.0,
    wrong_risk=0.0,
    success=False,
    collision=False,
):
    return {
        "head_seed": 6890,
        "split": "source_holdout_validation",
        "normal_first_action_l2": normal_l2,
        "normal_margin_regression": normal_regression,
        "wrong_margin_improvement": wrong_margin,
        "wrong_risk_improvement": wrong_risk,
        "wrong_success_improved": success,
        "wrong_collision_reduced": collision,
    }


def test_summarize_replay_rows_classifies_positive_risk_improvement():
    _split, summary = summarize_replay_rows(
        [_row(wrong_risk=0.02)],
        max_first_action_l2=0.006,
        min_wrong_risk_improvement=0.01,
        max_normal_margin_regression=0.005,
    )

    assert summary["replay_result_class"] == "replay_positive"
    assert summary["replay_admission_passed"] is True


def test_summarize_replay_rows_classifies_normal_regression_before_positive():
    _split, summary = summarize_replay_rows(
        [_row(normal_regression=0.02, wrong_risk=0.10)],
        max_first_action_l2=0.006,
        min_wrong_risk_improvement=0.01,
        max_normal_margin_regression=0.005,
    )

    assert summary["replay_result_class"] == "normal_regression"
    assert summary["replay_admission_passed"] is False


def test_summarize_replay_rows_classifies_empty_as_reconstruction_failure():
    split, summary = summarize_replay_rows(
        [],
        max_first_action_l2=0.006,
        min_wrong_risk_improvement=0.01,
        max_normal_margin_regression=0.005,
    )

    assert split == []
    assert summary["replay_result_class"] == "surface_reconstruction_failure"
    assert summary["replay_admission_passed"] is False
