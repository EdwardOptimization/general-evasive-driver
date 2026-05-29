from __future__ import annotations

from autodrift.history_sensitive_active_set_miner import (
    build_control_substitution_summary,
    classify_history_sensitive_pair,
    history_sensitive_pair_rows,
)


def _row(
    *,
    pair_id: str = "pair-0",
    variant: str,
    gap: float,
    success_drop: bool = False,
    collision_increase: bool = False,
) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "target_anchor_id": "target",
        "donor_anchor_id": "donor",
        "target_source_family": "t5_high_speed_close_obstacle",
        "donor_source_family": "t5_near_boundary_warmup",
        "target_anchor_window": "decision_minus_16",
        "donor_anchor_window": "decision_minus_16",
        "target_anchor_step": 10,
        "donor_anchor_step": 12,
        "same_window": True,
        "contrasting_normal_outcome": True,
        "variant": variant,
        "terminal_margin_gap_from_normal": gap,
        "success_drop_from_normal": success_drop,
        "collision_increase_from_normal": collision_increase,
        "terminal_margin": 0.2,
        "success": True,
        "collision": False,
        "target_donor_hidden_l2": 2.0,
        "target_donor_response_action_l2": 0.3,
    }


def test_classify_clean_history_sensitive_pair() -> None:
    result = classify_history_sensitive_pair(
        [
            _row(variant="normal", gap=0.0),
            _row(variant="wrong_history_donor_hidden_at_anchor", gap=0.08),
            _row(variant="donor_response_action_plus_hidden_from_anchor", gap=0.07),
            _row(variant="donor_response_action_stream_from_anchor", gap=0.01),
            _row(variant="zero_current_response_from_anchor", gap=0.02),
        ]
    )

    assert result["history_positive"] is True
    assert result["history_sensitive_clean"] is True
    assert result["classification"] == "history_sensitive_clean"
    assert result["hidden_specific_gap"] > 0.01


def test_classify_control_substitution_dominated_pair() -> None:
    result = classify_history_sensitive_pair(
        [
            _row(variant="normal", gap=0.0),
            _row(variant="wrong_history_donor_hidden_at_anchor", gap=0.01),
            _row(variant="donor_response_action_plus_hidden_from_anchor", gap=0.015),
            _row(variant="donor_response_action_stream_from_anchor", gap=0.08),
            _row(variant="zero_all_response_from_anchor", gap=0.07),
        ]
    )

    assert result["history_positive"] is False
    assert result["history_sensitive_clean"] is False
    assert result["classification"] == "control_substitution_dominated"


def test_history_sensitive_pair_rows_and_control_summary() -> None:
    rows = [
        _row(pair_id="pair-a", variant="normal", gap=0.0),
        _row(pair_id="pair-a", variant="wrong_history_donor_hidden_at_anchor", gap=0.08),
        _row(pair_id="pair-a", variant="donor_response_action_plus_hidden_from_anchor", gap=0.08),
        _row(pair_id="pair-a", variant="donor_response_action_stream_from_anchor", gap=0.0),
        _row(pair_id="pair-b", variant="normal", gap=0.0),
        _row(pair_id="pair-b", variant="wrong_history_donor_hidden_at_anchor", gap=0.0),
        _row(pair_id="pair-b", variant="donor_response_action_plus_hidden_from_anchor", gap=0.0),
        _row(pair_id="pair-b", variant="zero_current_response_from_anchor", gap=0.03),
    ]

    pair_rows = history_sensitive_pair_rows(rows)
    labels = {row["pair_id"]: row["classification"] for row in pair_rows}
    assert labels == {
        "pair-a": "history_sensitive_clean",
        "pair-b": "control_substitution_dominated",
    }

    summary = build_control_substitution_summary(pair_rows)
    counts = {row["classification"]: row["pair_count"] for row in summary}
    assert counts["history_sensitive_clean"] == 1
    assert counts["control_substitution_dominated"] == 1
