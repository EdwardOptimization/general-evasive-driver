from __future__ import annotations

from pathlib import Path

from autodrift.contour_aware_source_rule import (
    CLEAN_LABEL,
    CONTROL_ONLY_LABEL,
    DOMINATED_LABEL,
    MIXED_DIAGNOSTIC_EDGE,
    PRIMARY_SOURCE_EDGES,
    apply_contour_aware_source_rule,
    build_summary,
    run_contour_aware_source_rule,
)


def _row(
    *,
    source_edge: str,
    selection_source: str,
    label: str = CLEAN_LABEL,
    pair_id: str = "pair",
) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "source_edge": source_edge,
        "selection_source": selection_source,
        "label": label,
    }


def test_apply_rule_keeps_endpoint_and_diagnostic_out_of_primary() -> None:
    rows = [
        _row(source_edge=PRIMARY_SOURCE_EDGES[0], selection_source="clean_edge_window", pair_id="primary"),
        _row(source_edge=PRIMARY_SOURCE_EDGES[0], selection_source="clean_endpoint_neighbor", pair_id="endpoint"),
        _row(source_edge="capability_step_up|curved_boundary_obstacle", selection_source="negative_diagnostic_edge", pair_id="negative"),
        _row(source_edge=MIXED_DIAGNOSTIC_EDGE, selection_source="same_window_preferred", pair_id="mixed"),
        _row(source_edge="drive_loss_proxy|t5_near_boundary_warmup", selection_source="fallback_pairable", pair_id="excluded"),
    ]

    primary, diagnostic, excluded = apply_contour_aware_source_rule(rows)

    assert [row["pair_id"] for row in primary] == ["primary"]
    assert {row["rule_reason"] for row in diagnostic} == {
        "endpoint_neighbor_exclusion",
        "negative_diagnostic_edge",
        "mixed_dominated_edge",
    }
    assert [row["pair_id"] for row in excluded] == ["excluded"]


def test_build_summary_passes_for_pre_registered_synthetic_contour() -> None:
    primary = []
    clean_by_edge = [13, 12, 8, 6]
    for edge, clean_count in zip(PRIMARY_SOURCE_EDGES, clean_by_edge):
        for index in range(36):
            label = CLEAN_LABEL if index < clean_count else "history_null_all_controls_null"
            primary.append(_row(source_edge=edge, selection_source="clean_edge_window", label=label, pair_id=f"{edge}-{index}"))
    diagnostic = []
    for index in range(90):
        diagnostic.append(
            {
                **_row(
                    source_edge="capability_step_up|curved_boundary_obstacle",
                    selection_source="negative_diagnostic_edge",
                    label=DOMINATED_LABEL if index < 45 else "history_null_all_controls_null",
                    pair_id=f"neg-{index}",
                ),
                "rule_reason": "negative_diagnostic_edge",
            }
        )
    for index in range(60):
        diagnostic.append(
            {
                **_row(
                    source_edge=MIXED_DIAGNOSTIC_EDGE,
                    selection_source="same_window_preferred",
                    label=CONTROL_ONLY_LABEL if index < 10 else "history_null_all_controls_null",
                    pair_id=f"mix-{index}",
                ),
                "rule_reason": "mixed_dominated_edge",
            }
        )
    excluded = [_row(source_edge="other|edge", selection_source="fallback_pairable", label="history_null_all_controls_null", pair_id=f"ex-{index}") for index in range(234)]
    for row in primary:
        row["rule_reason"] = "clean_edge_window_primary"

    summary = build_summary(primary + diagnostic + excluded, primary, diagnostic, excluded)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["primary_clean_directed_pair_count"] == 39
    assert summary["max_primary_clean_source_edge_share"] == 13 / 39
    assert summary["diagnostic_dominated_or_control_count"] == 55


def test_run_contour_aware_source_rule_writes_artifacts(tmp_path: Path) -> None:
    contour_rows = tmp_path / "contour.csv"
    contour_rows.write_text(
        "pair_id,source_edge,selection_source,label\n"
        "p0,actuator_delay_step|capability_step_up,clean_edge_window,history_control_separated\n"
        "p1,other|edge,clean_endpoint_neighbor,control_only_positive\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "run"

    summary = run_contour_aware_source_rule(output_dir, contour_rows=contour_rows)

    assert summary["primary_rule_directed_pair_count"] == 1
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "primary_rule_rows.csv").exists()
    assert (output_dir / "diagnostic_rule_rows.csv").exists()
    assert (output_dir / "source_rule_summary.csv").exists()
