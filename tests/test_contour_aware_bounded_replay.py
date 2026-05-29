from __future__ import annotations

from autodrift.contour_aware_bounded_replay import (
    CLEAN_LABEL,
    CONTROL_ONLY_LABEL,
    DOMINATED_LABEL,
    directed_pairs_from_rows,
    select_diagnostic_replay_rows,
    build_summary,
)
from autodrift.source_diverse_pairability_history_interventions import VARIANTS


def _directed_row(pair_id: str, *, reason: str = "clean_edge_window_primary", label: str = CLEAN_LABEL, source_edge: str = "a|b") -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "target_anchor_id": f"{pair_id}-target",
        "donor_anchor_id": f"{pair_id}-donor",
        "target_source_family": "a",
        "donor_source_family": "b",
        "target_anchor_window": "w",
        "donor_anchor_window": "w",
        "target_anchor_step": 10,
        "donor_anchor_step": 14,
        "same_window": True,
        "step_distance": 4,
        "source_edge": source_edge,
        "source_run": "run",
        "rule_reason": reason,
        "selection_source": "clean_edge_window",
        "label": label,
    }


def test_directed_pairs_from_rows_preserves_direction_fields() -> None:
    pair = directed_pairs_from_rows([_directed_row("pair-0")])[0]

    assert pair.pair_id == "run::pair-0"
    assert pair.target_anchor_id == "pair-0-target"
    assert pair.donor_anchor_id == "pair-0-donor"
    assert pair.target_anchor_step == 10
    assert pair.donor_anchor_step == 14
    assert pair.step_distance == 4


def test_select_diagnostic_replay_rows_caps_each_reason() -> None:
    rows = []
    for reason in ("endpoint_neighbor_exclusion", "negative_diagnostic_edge", "mixed_dominated_edge"):
        for index in range(40):
            rows.append(_directed_row(f"{reason}-{index}", reason=reason, label=CONTROL_ONLY_LABEL))

    selected = select_diagnostic_replay_rows(rows, per_reason_cap=32)

    assert len(selected) == 96
    assert {row["rule_reason"] for row in selected} == {
        "endpoint_neighbor_exclusion",
        "negative_diagnostic_edge",
        "mixed_dominated_edge",
    }


def test_build_summary_passes_for_synthetic_replay_result() -> None:
    primary_rows = []
    clean_by_edge = [13, 12, 8, 6]
    edges = ["a|b", "c|d", "e|f", "g|h"]
    for edge, clean_count in zip(edges, clean_by_edge):
        for index in range(36):
            label = CLEAN_LABEL if index < clean_count else "history_null_all_controls_null"
            item = _directed_row(f"{edge}-{index}", label=label, source_edge=edge)
            item["source_run"] = "run-a" if index % 2 == 0 else "run-b"
            primary_rows.append(item)
    diagnostic_rows = []
    for reason in ("endpoint_neighbor_exclusion", "negative_diagnostic_edge", "mixed_dominated_edge"):
        for index in range(24):
            diagnostic_rows.append(_directed_row(f"{reason}-{index}", reason=reason, label=DOMINATED_LABEL))
    classified_rows = [
        dict(row, pair_id=f"{row['source_run']}::{row['pair_id']}", label=row["label"])
        for row in primary_rows + diagnostic_rows
    ]
    intervention_rows = []
    for row in primary_rows + diagnostic_rows:
        for variant in VARIANTS:
            intervention_rows.append({"pair_id": f"{row['source_run']}::{row['pair_id']}", "variant": variant, "target_replay_status": "ok"})

    summary = build_summary(
        primary_replay_rows=primary_rows,
        diagnostic_replay_rows=diagnostic_rows,
        intervention_rows=intervention_rows,
        classified_rows=classified_rows,
        continuation_steps=64,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["primary_clean_directed_pair_count"] == 39
    assert summary["diagnostic_dominated_or_control_count"] == 72
