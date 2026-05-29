from __future__ import annotations

from pathlib import Path

from autodrift.contour_aware_candidate_corpus_export import (
    CLEAN_LABEL,
    build_manifest,
    build_summary,
    run_contour_aware_candidate_corpus_export,
)


def _row(pair_id: str, *, label: str = CLEAN_LABEL, m1602_label: str = CLEAN_LABEL, source_edge: str = "a|b") -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "label": label,
        "m1602_label": m1602_label,
        "source_edge": source_edge,
    }


def test_build_summary_passes_for_candidate_package() -> None:
    positive = []
    for edge, count in zip(["a|b", "c|d", "e|f", "g|h"], [13, 12, 8, 6]):
        for index in range(count):
            positive.append(_row(f"{edge}-{index}", source_edge=edge))
    diagnostic = [_row(f"d-{index}", label="control_only_positive", m1602_label="control_only_positive", source_edge="x|y") for index in range(232)]
    manifest = build_manifest(positive, diagnostic)

    summary = build_summary(positive, diagnostic, manifest)

    assert summary["passes_public_smoke_gates"] is True
    assert summary["positive_candidate_count"] == 39
    assert summary["diagnostic_guardrail_count"] == 232
    assert summary["training_corpus_exported"] is False
    assert summary["loss_constructed"] is False


def test_build_summary_fails_when_diagnostic_used_as_positive() -> None:
    positive = [_row("shared")]
    diagnostic = [_row("shared", label="control_only_positive", m1602_label="control_only_positive")]
    manifest = build_manifest(positive, diagnostic)

    summary = build_summary(positive, diagnostic, manifest)

    assert summary["diagnostic_rows_used_as_positive"] is True
    assert summary["passes_public_smoke_gates"] is False


def test_run_corpus_export_writes_package_artifacts(tmp_path: Path) -> None:
    candidates = tmp_path / "candidate_rows.csv"
    diagnostics = tmp_path / "diagnostic_rows.csv"
    candidates.write_text(
        "pair_id,label,m1602_label,source_edge\n"
        "p0,history_control_separated,history_control_separated,a|b\n",
        encoding="utf-8",
    )
    diagnostics.write_text(
        "pair_id,label,m1602_label,source_edge\n"
        "d0,control_only_positive,control_only_positive,x|y\n",
        encoding="utf-8",
    )
    output = tmp_path / "run"

    summary = run_contour_aware_candidate_corpus_export(output, candidate_rows=candidates, diagnostic_rows=diagnostics)

    assert summary["positive_candidate_count"] == 1
    assert (output / "summary.json").exists()
    assert (output / "positive_candidate_rows.csv").exists()
    assert (output / "diagnostic_guardrail_rows.csv").exists()
    assert (output / "corpus_manifest.json").exists()
