from __future__ import annotations

import csv

import numpy as np
import pandas as pd
import pytest

from autodrift.active_set_radius_anchor import (
    RADIUS_PROFILES,
    _save_profile_anchor,
    build_spillover_failed_rows,
    old_key_case_id,
)


def test_old_key_case_id_uses_fixed_float_formatting() -> None:
    row = {
        "key": "9951|perturbed|35|32",
        "target_obstacle_distance": 10,
        "relocated_obstacle_body_y": -1.2,
        "relocated_obstacle_half_width": 1.4,
    }

    assert old_key_case_id(row) == "9951|perturbed|35|32|10.000000|-1.200000|1.400000"


def test_build_spillover_failed_rows_filters_candidate_and_schema(tmp_path) -> None:
    path = tmp_path / "guard_results.csv"
    rows = [
        {
            "policy": "base",
            "key": "9951|perturbed|35|32",
            "seed": 9951,
            "source_condition": "perturbed",
            "source_step": 35,
            "paired_step": 32,
            "target_obstacle_distance": 10.0,
            "relocated_obstacle_body_y": -1.2,
            "relocated_obstacle_half_width": 1.4,
            "reference_normal_margin": 0.1,
            "reference_wrong_history_margin": -0.1,
            "reference_margin_gap": 0.2,
            "accepted": True,
            "normal_success": True,
            "wrong_history_margin": -0.1,
        },
        {
            "policy": "candidate",
            "key": "9951|perturbed|35|32",
            "seed": 9951,
            "source_condition": "perturbed",
            "source_step": 35,
            "paired_step": 32,
            "target_obstacle_distance": 10.0,
            "relocated_obstacle_body_y": -1.2,
            "relocated_obstacle_half_width": 1.4,
            "reference_normal_margin": 0.1,
            "reference_wrong_history_margin": -0.1,
            "reference_margin_gap": 0.2,
            "accepted": False,
            "normal_success": True,
            "wrong_history_margin": 0.01,
        },
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    filtered = build_spillover_failed_rows(
        path,
        candidate_policy="candidate",
        spillover_case_ids=("9951|perturbed|35|32|10.000000|-1.200000|1.400000",),
    )

    assert len(filtered) == 1
    assert filtered.loc[0, "case_id"] == "9951|perturbed|35|32|10.000000|-1.200000|1.400000"
    assert bool(filtered.loc[0, "candidate_normal_success"]) is True
    assert filtered.loc[0, "candidate_wrong_history_margin"] == pytest.approx(0.01)
    assert bool(filtered.loc[0, "candidate_normal_success_regression"]) is False


def test_save_profile_anchor_offsets_spillover_sources_and_writes_radius(tmp_path) -> None:
    base_arrays = {
        "observation": np.zeros((2, 72), dtype=np.float32),
        "hidden": np.zeros((2, 128), dtype=np.float32),
        "reference_action": np.zeros((2, 3), dtype=np.float32),
        "source_index": np.asarray([0, 4], dtype=np.int64),
        "step_index": np.asarray([0, 1], dtype=np.int64),
        "weight": np.asarray([75.0, 75.0], dtype=np.float32),
    }
    spillover_arrays = {
        "observation": np.ones((1, 72), dtype=np.float32),
        "hidden": np.ones((1, 128), dtype=np.float32),
        "reference_action": np.ones((1, 3), dtype=np.float32),
        "source_index": np.asarray([0], dtype=np.int64),
        "step_index": np.asarray([0], dtype=np.int64),
        "weight": np.asarray([75.0], dtype=np.float32),
    }
    output = tmp_path / "medium_radius_anchor.npz"

    summary = _save_profile_anchor(
        output_npz=output,
        base_arrays=base_arrays,
        spillover_arrays=spillover_arrays,
        profile=RADIUS_PROFILES["medium"],
    )

    data = np.load(output)
    assert summary["rows"] == 3
    assert data["source_index"].tolist() == [0, 4, 5]
    assert data["radius"].tolist() == pytest.approx([0.00030, 0.00035, 0.00015])
