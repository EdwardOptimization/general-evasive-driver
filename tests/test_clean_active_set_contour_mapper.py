from __future__ import annotations

import csv
from pathlib import Path

from autodrift.clean_active_set_contour_mapper import ContourInput, build_summary, enrich_contour_rows, feature_group_summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_enrich_contour_rows_joins_normal_metadata(tmp_path: Path) -> None:
    classified = tmp_path / "classified.csv"
    intervention = tmp_path / "intervention.csv"
    _write_csv(
        classified,
        [
            {
                "pair_id": "pair-0|left_target",
                "label": "history_control_separated",
                "source_edge": "a|b",
                "target_anchor_id": "ta",
                "donor_anchor_id": "da",
                "target_source_family": "a",
                "donor_source_family": "b",
                "target_anchor_window": "reveal_plus_4",
                "donor_anchor_window": "reveal_plus_4",
                "history_max_gap": 0.03,
                "control_max_gap": 0.001,
                "wrong_history_gap": 0.03,
                "donor_plus_hidden_gap": 0.03,
                "donor_response_action_only_gap": 0.001,
                "hidden_specific_gap": 0.029,
            }
        ],
    )
    _write_csv(
        intervention,
        [
            {
                "pair_id": "pair-0|left_target",
                "variant": "normal",
                "target_anchor_step": 34,
                "donor_anchor_step": 42,
                "same_window": True,
                "step_distance": 8,
                "selection_source": "clean_edge_window",
                "selected_pair_id": "selected-0000",
                "original_pair_id": "pair-0",
                "pair_response_action_l2": 0.12,
                "pair_context_l2": 0.4,
                "pair_hidden_l2": 3.1,
                "normal_terminal_margin": 1.2,
            }
        ],
    )

    rows = enrich_contour_rows([ContourInput("unit", classified, intervention)])

    assert rows[0]["source_run"] == "unit"
    assert rows[0]["metadata_joined"] is True
    assert rows[0]["direction"] == "left_target"
    assert rows[0]["selection_source"] == "clean_edge_window"
    assert rows[0]["history_gap_band"] == "signal_0p02_0p05"
    assert rows[0]["hidden_l2_band"] == "tier_a_signal"


def test_build_summary_tracks_label_coverage_and_guardrails() -> None:
    rows = []
    for index in range(51):
        rows.append({"source_run": f"run-{index % 3}", "source_edge": f"edge-{index % 20}", "label": "history_control_separated", "metadata_joined": True})
    for index in range(70):
        rows.append({"source_run": f"run-{index % 3}", "source_edge": f"edge-{index % 20}", "label": "history_positive_control_dominated", "metadata_joined": True})
    for index in range(79):
        rows.append({"source_run": f"run-{index % 3}", "source_edge": f"edge-{index % 20}", "label": "control_only_positive", "metadata_joined": True})
    for index in range(328):
        rows.append({"source_run": f"run-{index % 3}", "source_edge": f"edge-{index % 20}", "label": "history_null_all_controls_null", "metadata_joined": True})
    for row in rows:
        row.update(
            {
                "window_pair": "w|w",
                "selection_source": "clean_edge",
                "history_gap_band": "sub_threshold",
                "control_gap_band": "zero",
                "hidden_specific_gap_band": "below_hidden_specific",
                "response_action_l2_band": "tier_a_ok",
                "hidden_l2_band": "tier_a_signal",
                "normal_margin_band": "positive_mid",
                "history_max_gap": 0.0,
                "control_max_gap": 0.0,
                "hidden_specific_gap": 0.0,
            }
        )

    summary = build_summary(rows)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["null_result_classification"] == "contour_mapping_public_pass"


def test_feature_group_summary_has_multiple_group_families() -> None:
    rows = [
        {
            "source_run": "run",
            "source_edge": "a|b",
            "label": "history_control_separated",
            "window_pair": "w|w",
            "selection_source": "clean_edge",
            "history_gap_band": "signal",
            "control_gap_band": "zero",
            "hidden_specific_gap_band": "signal",
            "response_action_l2_band": "tier_a_ok",
            "hidden_l2_band": "tier_a_signal",
            "normal_margin_band": "near_boundary",
            "metadata_joined": True,
            "history_max_gap": 0.03,
            "control_max_gap": 0.0,
            "hidden_specific_gap": 0.02,
        }
    ]

    summary = feature_group_summary(rows)

    assert {row["group_name"] for row in summary} >= {
        "source_run_source_edge",
        "source_edge_window_pair",
        "source_edge_selection_source",
    }
