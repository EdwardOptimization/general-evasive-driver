import pandas as pd
import pytest

from autodrift.old_key_neighborhood_targeted_replay import (
    _requests_by_condition,
    _require_columns,
    summarize_policy_rows,
)


def test_requests_by_condition_maps_source_and_paired_steps():
    compact = pd.DataFrame(
        [
            {
                "seed": 100,
                "source_condition": "perturbed",
                "source_step": 30,
                "paired_step": 24,
            },
            {
                "seed": 101,
                "source_condition": "nominal",
                "source_step": 20,
                "paired_step": 26,
            },
        ]
    )

    requests = _requests_by_condition(compact)

    assert requests["perturbed"][100] == {30}
    assert requests["nominal"][100] == {24}
    assert requests["nominal"][101] == {20}
    assert requests["perturbed"][101] == {26}


def test_requests_by_condition_rejects_unknown_source_condition():
    compact = pd.DataFrame(
        [{"seed": 100, "source_condition": "bad", "source_step": 30, "paired_step": 24}]
    )

    with pytest.raises(ValueError, match="source_condition"):
        _requests_by_condition(compact)


def test_summarize_policy_rows_reports_pass_and_margin_stats():
    rows = [
        {
            "policy": "p0",
            "found_rows": 1,
            "accepted": True,
            "normal_success": True,
            "margin_gap": 0.01,
            "margin_gap_delta_vs_reference": 0.001,
        },
        {
            "policy": "p0",
            "found_rows": 1,
            "accepted": False,
            "normal_success": True,
            "margin_gap": 0.005,
            "margin_gap_delta_vs_reference": -0.002,
        },
    ]

    summary = summarize_policy_rows(rows)

    assert summary == [
        {
            "policy": "p0",
            "cases": 2,
            "found_cases": 2,
            "accepted_cases": 1,
            "policy_pass": False,
            "normal_success_cases": 2,
            "margin_gap_mean": pytest.approx(0.0075),
            "margin_gap_min": pytest.approx(0.005),
            "margin_gap_delta_mean": pytest.approx(-0.0005),
            "margin_gap_delta_min": pytest.approx(-0.002),
        }
    ]


def test_require_columns_reports_missing_columns():
    with pytest.raises(ValueError, match="missing columns"):
        _require_columns(pd.DataFrame([{"a": 1}]), ["a", "b"], label="frame")
