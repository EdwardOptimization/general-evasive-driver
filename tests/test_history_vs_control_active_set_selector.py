from __future__ import annotations

from autodrift.history_vs_control_active_set_selector import (
    CONTROL_VARIANTS,
    HISTORY_VARIANTS,
    REQUIRED_VARIANTS,
    build_summary,
    classify_directed_pair,
)


def _rows(*, history_gap: float, control_gap: float, donor_only_gap: float = 0.0, success_drop: bool = False) -> list[dict[str, object]]:
    rows = []
    for variant in sorted(REQUIRED_VARIANTS):
        gap = 0.0
        if variant == "wrong_history_hidden":
            gap = history_gap
        if variant == "donor_response_action_plus_hidden":
            gap = history_gap
        if variant == "donor_response_action_only":
            gap = donor_only_gap
        if variant in CONTROL_VARIANTS and variant != "donor_response_action_only":
            gap = control_gap
        rows.append(
            {
                "pair_id": "pair-0",
                "variant": variant,
                "source_edge": "a|b",
                "target_source_family": "a",
                "donor_source_family": "b",
                "terminal_margin_gap_from_normal": gap,
                "success_drop_from_normal": success_drop if variant in HISTORY_VARIANTS else False,
                "collision_increase_from_normal": False,
            }
        )
    return rows


def test_classify_clean_history_control_separated() -> None:
    row = classify_directed_pair("pair-0", _rows(history_gap=0.05, control_gap=0.01, donor_only_gap=0.0))

    assert row["label"] == "history_control_separated"
    assert row["hidden_specific_gap"] >= 0.01


def test_classify_control_dominated_and_control_only() -> None:
    dominated = classify_directed_pair("pair-0", _rows(history_gap=0.05, control_gap=0.04, donor_only_gap=0.0))
    control_only = classify_directed_pair("pair-0", _rows(history_gap=0.0, control_gap=0.03, donor_only_gap=0.0))

    assert dominated["label"] == "history_positive_control_dominated"
    assert control_only["label"] == "control_only_positive"


def test_build_summary_tracks_clean_shortfall() -> None:
    rows = []
    for index in range(144):
        if index < 7:
            label = "history_control_separated"
            edge = f"edge-{index % 4}"
        elif index < 23:
            label = "history_positive_control_dominated"
            edge = f"edge-{index % 6}"
        else:
            label = "history_null_all_controls_null"
            edge = f"edge-{index % 8}"
        rows.append(
            {
                "pair_id": f"pair-{index}",
                "label": label,
                "source_edge": edge,
                "target_source_family": f"fam-{index % 4}",
                "donor_source_family": f"fam-{(index + 1) % 4}",
                "history_max_gap": 0.03 if label != "history_null_all_controls_null" else 0.0,
                "control_max_gap": 0.01,
            }
        )

    summary = build_summary(rows)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is False
    assert summary["null_result_classification"] == "selector_public_pass_clean_shortfall"
