from __future__ import annotations

from autodrift.history_pairability_source_miner import (
    PAIRABILITY_SOURCE_FAMILIES,
    pairability_modes_for_source_family,
    pairability_source_specs,
    tier_flags,
    tier_label,
    threshold_sweep_summary,
)


def _pair(edge: str, label: str, high_late: bool = False) -> dict[str, object]:
    return {
        "source_edge": edge,
        "left_source_family": edge.split("|")[0],
        "right_source_family": edge.split("|")[1],
        "left_anchor_window": "reveal",
        "right_anchor_window": "decision",
        "tier_a_strict": label == "tier_a_strict",
        "tier_b_moderate": label in {"tier_a_strict", "tier_b_moderate"},
        "tier_c_diagnostic": label in {"tier_a_strict", "tier_c_diagnostic"},
        "raw_tier_b_no_context_guard": label in {"tier_a_strict", "tier_b_moderate"},
        "high_speed_or_late_pair": high_late,
    }


def test_tier_flags_are_inclusive_with_context_guard() -> None:
    flags = tier_flags(response_action_l2=0.50, hidden_l2=3.2, context_l2=3.5)
    assert flags["tier_a_strict"] is True
    assert flags["tier_b_moderate"] is True
    assert flags["tier_c_diagnostic"] is True
    assert tier_label(response_action_l2=0.50, hidden_l2=3.2, context_l2=3.5) == "tier_a_strict"

    assert tier_label(response_action_l2=0.70, hidden_l2=2.2, context_l2=3.5) == "tier_b_moderate"
    assert tier_label(response_action_l2=0.90, hidden_l2=2.7, context_l2=3.5) == "tier_c_diagnostic"
    assert tier_label(response_action_l2=0.70, hidden_l2=2.2, context_l2=5.0) == "context_mismatch_dominated"


def test_pairability_modes_cover_high_speed_late_and_base_modes() -> None:
    high_speed = pairability_modes_for_source_family("t5_high_speed_close_obstacle")
    late = pairability_modes_for_source_family("late_reveal_boundary")
    near = pairability_modes_for_source_family("t5_near_boundary_warmup")

    assert any(mode.name.startswith("hs_hist") for mode in high_speed)
    assert any(mode.name.startswith("late_hist") for mode in late)
    assert not any(mode.name.startswith("hs_hist") for mode in near)


def test_pairability_source_specs_are_source_balanced() -> None:
    specs = pairability_source_specs(seed=1901, seed_count=1, max_source_specs=44)
    families = {spec.artifact_row.source_family for spec in specs}

    assert "t5_high_speed_close_obstacle" in families
    assert "late_reveal_boundary" in families
    assert len(families & PAIRABILITY_SOURCE_FAMILIES) >= 8


def test_threshold_sweep_summary_counts_endpoint_diversity() -> None:
    rows = [
        _pair("a|b", "tier_a_strict", True),
        _pair("a|c", "tier_b_moderate", False),
        _pair("d|e", "tier_c_diagnostic", True),
    ]
    summary = {row["tier"]: row for row in threshold_sweep_summary(rows)}

    assert summary["tier_a_strict"]["pair_count"] == 1
    assert summary["tier_b_moderate"]["pair_count"] == 2
    assert summary["tier_c_diagnostic"]["pair_count"] == 2
    assert summary["tier_b_moderate"]["endpoint_source_family_count"] == 3
