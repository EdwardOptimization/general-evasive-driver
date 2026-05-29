from __future__ import annotations

from pathlib import Path

from autodrift.contour_aware_candidate_materialization import (
    CLEAN_LABEL,
    CONTROL_ONLY_LABEL,
    DOMINATED_LABEL,
    build_summary,
    run_contour_aware_candidate_materialization,
    select_candidate_rows,
)


def _row(
    pair_id: str,
    *,
    label: str = CLEAN_LABEL,
    m1602_label: str = CLEAN_LABEL,
    rule_bucket: str = "primary",
    rule_reason: str = "clean_edge_window_primary",
    source_edge: str = "a|b",
    missing_variants: str = "",
) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "label": label,
        "m1602_label": m1602_label,
        "rule_bucket": rule_bucket,
        "rule_reason": rule_reason,
        "source_edge": source_edge,
        "missing_variants": missing_variants,
    }


def test_select_candidate_rows_keeps_only_primary_clean_complete_rows() -> None:
    rows = [
        _row("clean"),
        _row("wrong-label", label=DOMINATED_LABEL),
        _row("wrong-m1602", m1602_label=DOMINATED_LABEL),
        _row("diagnostic", rule_bucket="diagnostic", rule_reason="mixed_dominated_edge"),
        _row("missing", missing_variants="reset_hidden"),
    ]

    selected = select_candidate_rows(rows)

    assert [row["pair_id"] for row in selected] == ["clean"]


def test_build_summary_passes_for_synthetic_materialization() -> None:
    candidate_rows = []
    edges = ["a|b", "c|d", "e|f", "g|h"]
    counts = [13, 12, 8, 6]
    for edge, count in zip(edges, counts):
        for index in range(count):
            candidate_rows.append(_row(f"{edge}-{index}", source_edge=edge))
    primary_rows = list(candidate_rows) + [_row("null-primary", label="history_null_all_controls_null")]
    diagnostic_rows = []
    for index in range(232):
        label = DOMINATED_LABEL if index < 39 else CONTROL_ONLY_LABEL if index < 81 else "history_null_all_controls_null"
        reason = ("endpoint_neighbor_exclusion", "negative_diagnostic_edge", "mixed_dominated_edge")[index % 3]
        diagnostic_rows.append(_row(f"diag-{index}", label=label, m1602_label=label, rule_bucket="diagnostic", rule_reason=reason))

    summary = build_summary(primary_rows, diagnostic_rows, candidate_rows, diagnostic_rows)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["candidate_directed_pair_count"] == 39
    assert summary["max_candidate_source_edge_share"] == 13 / 39
    assert summary["diagnostic_dominated_or_control_count"] == 81
    assert summary["training_corpus_exported"] is False


def test_run_materialization_writes_expected_artifacts(tmp_path: Path) -> None:
    primary = tmp_path / "primary.csv"
    diagnostic = tmp_path / "diagnostic.csv"
    primary.write_text(
        "pair_id,label,m1602_label,rule_bucket,rule_reason,source_edge,missing_variants\n"
        "p0,history_control_separated,history_control_separated,primary,clean_edge_window_primary,a|b,\n"
        "p1,history_null_all_controls_null,history_null_all_controls_null,primary,clean_edge_window_primary,a|b,\n",
        encoding="utf-8",
    )
    diagnostic.write_text(
        "pair_id,label,m1602_label,rule_bucket,rule_reason,source_edge,missing_variants\n"
        "d0,control_only_positive,control_only_positive,diagnostic,negative_diagnostic_edge,x|y,\n",
        encoding="utf-8",
    )
    output = tmp_path / "run"

    summary = run_contour_aware_candidate_materialization(
        output,
        primary_classified_rows=primary,
        diagnostic_classified_rows=diagnostic,
    )

    assert summary["candidate_directed_pair_count"] == 1
    assert (output / "summary.json").exists()
    assert (output / "candidate_rows.csv").exists()
    assert (output / "diagnostic_guardrail_rows.csv").exists()
    assert (output / "guardrail_summary.csv").exists()
