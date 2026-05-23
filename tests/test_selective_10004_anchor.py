from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from autodrift.selective_10004_anchor import TARGET_CASE_ID, export_selective_10004_profiles


def _write_sources(path: Path) -> None:
    rows = [
        {
            "source_index": "0",
            "source_label": "base_hard_guard",
            "case_id": "",
            "branch": "",
            "role": "existing_hard_guard",
            "rows": "2",
            "radius": "0.0003",
            "weight_mean": "75.0",
        },
        {
            "source_index": "7",
            "source_label": "old_key_branch_split",
            "case_id": TARGET_CASE_ID,
            "branch": "wrong_history",
            "role": "branch_split_hard_guard",
            "rows": "6",
            "radius": "0.0002",
            "weight_mean": "75.0",
        },
        {
            "source_index": "8",
            "source_label": "old_key_branch_split",
            "case_id": "10023|perturbed|12|12|11.000000|-0.800000|1.200000",
            "branch": "wrong_history",
            "role": "branch_split_hard_guard",
            "rows": "2",
            "radius": "0.0002",
            "weight_mean": "75.0",
        },
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_anchor(path: Path) -> None:
    rows = 10
    source_index = np.asarray([0, 0, 7, 7, 7, 7, 7, 7, 8, 8], dtype=np.int64)
    np.savez(
        path,
        observation=np.zeros((rows, 72), dtype=np.float32),
        hidden=np.zeros((rows, 64), dtype=np.float32),
        reference_action=np.zeros((rows, 3), dtype=np.float32),
        source_index=source_index,
        step_index=np.asarray([0, 1, 0, 1, 2, 3, 4, 5, 0, 1], dtype=np.int64),
        weight=np.full(rows, 75.0, dtype=np.float32),
        radius=np.full(rows, 0.0002, dtype=np.float32),
    )


def test_export_selective_profiles_only_changes_10004_radius(tmp_path: Path) -> None:
    anchor = tmp_path / "anchor.npz"
    sources = tmp_path / "sources.csv"
    _write_anchor(anchor)
    _write_sources(sources)

    summary = export_selective_10004_profiles(
        base_anchor_npz=anchor,
        base_sources_csv=sources,
        run_dir=tmp_path / "out",
    )

    assert summary["profile_count"] == 6
    r0010 = np.load(tmp_path / "out" / "r0010" / "selective_anchor.npz")
    target_mask = r0010["source_index"] == 7
    other_mask = ~target_mask
    assert int(target_mask.sum()) == 6
    assert np.allclose(r0010["radius"][target_mask], 0.0010)
    assert np.allclose(r0010["radius"][other_mask], 0.0002)


def test_tail_profiles_keep_target_but_drop_early_target_rows(tmp_path: Path) -> None:
    anchor = tmp_path / "anchor.npz"
    sources = tmp_path / "sources.csv"
    _write_anchor(anchor)
    _write_sources(sources)

    export_selective_10004_profiles(
        base_anchor_npz=anchor,
        base_sources_csv=sources,
        run_dir=tmp_path / "out",
    )

    tail = np.load(tmp_path / "out" / "tail_r0005" / "selective_anchor.npz")
    target_mask = tail["source_index"] == 7
    assert int(target_mask.sum()) == 2
    assert np.array_equal(tail["step_index"][target_mask], np.asarray([4, 5], dtype=np.int64))
    assert np.allclose(tail["radius"][target_mask], 0.0005)
    assert int((tail["source_index"] == 8).sum()) == 2

    with (tmp_path / "out" / "tail_r0005" / "selective_sources.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    target_rows = [row for row in rows if row["case_id"] == TARGET_CASE_ID]
    assert len(target_rows) == 1
    assert target_rows[0]["rows"] == "2"
    assert target_rows[0]["role"] == "selective_10004_wrong_history_guard"
