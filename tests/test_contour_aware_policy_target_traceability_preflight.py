from __future__ import annotations

import csv
from pathlib import Path

from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
import autodrift.contour_aware_policy_target_traceability_preflight as preflight_module
from autodrift.contour_aware_policy_target_traceability_preflight import (
    REQUIRED_VARIANTS,
    run_contour_aware_policy_target_traceability_preflight,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.write_text(
        ",".join(keys)
        + "\n"
        + "\n".join(",".join(str(row.get(key, "")) for key in keys) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def _row(pair_id: str, *, role: str, source_run: str = "m1592_clean_repair") -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "corpus_role": role,
        "source_run": source_run,
        "source_edge": "a|b",
        "contour_pair_id": pair_id.replace("src::", ""),
        "selected_pair_id": "selected-0000",
        "original_pair_id": "pair-0000",
        "target_anchor_id": "target|0",
        "donor_anchor_id": "donor|0",
    }


def _make_package(tmp_path: Path, *, positive_count: int = 39, diagnostic_count: int = 232) -> tuple[Path, Path, dict[str, Path]]:
    candidate_dir = tmp_path / "candidate"
    replay_dir = tmp_path / "replay"
    candidate_dir.mkdir()
    replay_dir.mkdir()
    source_dirs = {
        "m1588_selector": tmp_path / "src1588",
        "m1592_clean_repair": tmp_path / "src1592",
    }
    for source_dir in source_dirs.values():
        source_dir.mkdir()
    positives = [_row(f"src::p-{index}", role=POSITIVE_ROLE) for index in range(positive_count)]
    diagnostics = [_row(f"src::d-{index}", role=DIAGNOSTIC_ROLE, source_run="m1588_selector") for index in range(diagnostic_count)]
    replay_rows = [{"pair_id": row["pair_id"]} for row in positives + diagnostics]
    intervention_rows = []
    for row in positives + diagnostics:
        for variant in REQUIRED_VARIANTS:
            intervention_rows.append({"pair_id": row["pair_id"], "variant": variant})
    _write_csv(candidate_dir / "positive_candidate_rows.csv", positives)
    _write_csv(candidate_dir / "diagnostic_guardrail_rows.csv", diagnostics)
    _write_csv(replay_dir / "replay_pair_rows.csv", replay_rows)
    _write_csv(replay_dir / "intervention_rows.csv", intervention_rows)
    return candidate_dir, replay_dir, source_dirs


def test_traceability_preflight_public_pass(tmp_path: Path, monkeypatch) -> None:
    candidate_dir, replay_dir, source_dirs = _make_package(tmp_path)
    monkeypatch.setattr(preflight_module, "SOURCE_RUN_DIRS", source_dirs)
    run_dir = tmp_path / "run"

    summary = run_contour_aware_policy_target_traceability_preflight(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        run_dir=run_dir,
    )

    assert summary["passes_public_smoke_gates"] is True
    assert summary["positive_candidate_count"] == 39
    assert summary["diagnostic_guardrail_count"] == 232
    assert summary["source_run_resolution_failure_count"] == 0
    assert summary["positive_replay_pair_match_count"] == 39
    assert summary["positive_normal_variant_match_count"] == 39
    assert summary["positive_wrong_history_hidden_variant_match_count"] == 39
    assert summary["positive_donor_response_action_plus_hidden_variant_match_count"] == 39
    assert summary["tensor_target_materialized"] is False
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "positive_traceability_rows.csv").exists()
    assert (run_dir / "diagnostic_traceability_rows.csv").exists()
    assert (run_dir / "missing_traceability_rows.csv").exists()


def test_traceability_preflight_reports_missing_variant(tmp_path: Path, monkeypatch) -> None:
    candidate_dir, replay_dir, source_dirs = _make_package(tmp_path)
    monkeypatch.setattr(preflight_module, "SOURCE_RUN_DIRS", source_dirs)
    intervention_path = replay_dir / "intervention_rows.csv"
    with intervention_path.open(newline="", encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if not (row["pair_id"] == "src::p-0" and row["variant"] == "wrong_history_hidden")
        ]
    _write_csv(intervention_path, rows)
    run_dir = tmp_path / "run"

    summary = run_contour_aware_policy_target_traceability_preflight(
        candidate_run_dir=candidate_dir,
        replay_run_dir=replay_dir,
        run_dir=run_dir,
    )

    assert summary["passes_public_smoke_gates"] is False
    assert summary["positive_wrong_history_hidden_variant_match_count"] == 38
    assert summary["missing_traceability_row_count"] == 1
    with (run_dir / "missing_traceability_rows.csv").open(newline="", encoding="utf-8") as handle:
        missing = list(csv.DictReader(handle))
    assert missing[0]["pair_id"] == "src::p-0"
    assert "wrong_history_hidden_missing" in missing[0]["missing_reasons"]
