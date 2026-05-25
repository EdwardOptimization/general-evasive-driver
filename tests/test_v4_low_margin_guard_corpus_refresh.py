from __future__ import annotations

import csv
from pathlib import Path

from autodrift.v4_low_margin_guard_corpus_refresh import (
    classify_result,
    run_low_margin_guard_corpus_refresh,
    summarize_accepted,
)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "contrast_group_id",
        "seed",
        "source_index",
        "step",
        "fault_family_pair",
        "alpha",
        "branch",
        "success",
        "collision",
        "terminal_reason",
        "min_clearance_margin",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _row(index: int, *, margin: float, seed: int | None = None, source_index: int | None = None) -> dict[str, object]:
    seed_value = 9000 + (index % 10) if seed is None else seed
    source_value = index if source_index is None else source_index
    return {
        "contrast_group_id": f"{source_value}|2|zero_command_obs|{index}",
        "seed": seed_value,
        "source_index": source_value,
        "step": 20 + (index % 7),
        "fault_family_pair": f"family{index % 5}->family{(index + 1) % 5}",
        "alpha": 0.2,
        "branch": "normal",
        "success": True,
        "collision": False,
        "terminal_reason": "obstacle_completed",
        "min_clearance_margin": margin,
    }


def test_low_margin_refresh_passes_source_diverse_rows(tmp_path: Path) -> None:
    replay = tmp_path / "replay.csv"
    _write_rows(replay, [_row(index, margin=1e-5) for index in range(90)])

    summary = run_low_margin_guard_corpus_refresh(
        reference_replay_rows_path=replay,
        run_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "v4_low_margin_guard_refresh_source_diverse_pass"
    assert summary["low_margin_corpus_pass"] is True
    assert summary["fresh_accepted_low_margin_guard_row_count"] == 90
    assert Path(summary["accepted_low_margin_guard_rows_csv"]).exists()


def test_low_margin_refresh_rejects_diagnostic_band_only(tmp_path: Path) -> None:
    replay = tmp_path / "replay.csv"
    _write_rows(replay, [_row(index, margin=0.01) for index in range(90)])

    summary = run_low_margin_guard_corpus_refresh(
        reference_replay_rows_path=replay,
        run_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "v4_low_margin_guard_refresh_diagnostic_band_only"
    assert summary["low_margin_corpus_pass"] is False
    assert summary["candidate_row_count"] == 90
    assert summary["fresh_accepted_low_margin_guard_row_count"] == 0


def test_low_margin_refresh_rejects_single_source_primary_rows(tmp_path: Path) -> None:
    replay = tmp_path / "replay.csv"
    _write_rows(replay, [_row(index, margin=1e-5, seed=88000, source_index=12) for index in range(12)])

    summary = run_low_margin_guard_corpus_refresh(
        reference_replay_rows_path=replay,
        run_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "v4_low_margin_guard_refresh_single_source_or_sparse"
    assert summary["low_margin_corpus_pass"] is False
    assert summary["fresh_accepted_low_margin_guard_row_count"] == 12
    assert summary["unique_seed_count"] == 1
    assert summary["unique_source_index_count"] == 1


def test_classify_result_detects_reference_contract_violation() -> None:
    accepted_summary = summarize_accepted(
        [],
        min_rows=80,
        min_seeds=8,
        min_source_indices=8,
        min_fault_pairs=4,
        max_seed_dominance=0.25,
        max_source_index_dominance=0.15,
        max_fault_pair_dominance=0.40,
    )

    assert (
        classify_result(
            reference_contract_ok=False,
            accepted_summary=accepted_summary,
            candidates=[],
            diagnostic_rows=0,
        )
        == "v4_low_margin_guard_refresh_contract_violation"
    )
