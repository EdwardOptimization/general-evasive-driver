from pathlib import Path

import pandas as pd
import pytest

from autodrift.boundary_conditioned_grounded_target_miner import (
    _diversity,
    _empty_float_stat,
    load_boundary_source_rows,
)


def test_load_boundary_source_rows_requires_contract_and_adds_selected_index(tmp_path: Path):
    path = tmp_path / "boundary.csv"
    pd.DataFrame([_boundary_row(source_index=7)]).to_csv(path, index=False)

    rows = load_boundary_source_rows(path)

    assert rows.loc[0, "selected_source_index"] == 7
    assert rows.loc[0, "source_index"] == 7


def test_load_boundary_source_rows_reports_missing_columns(tmp_path: Path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"source_index": 1}]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="missing columns"):
        load_boundary_source_rows(path)


def test_diversity_counts_physical_pairs_and_dominance():
    rows = pd.DataFrame(
        [
            _boundary_row(source_index=0, left_seed=1, right_seed=10, surface="fresh"),
            _boundary_row(source_index=1, left_seed=1, right_seed=10, surface="fresh"),
            _boundary_row(source_index=2, left_seed=2, right_seed=20, surface="ood", variant="delayed_history"),
        ]
    )

    summary = _diversity(rows)

    assert summary["rows"] == 3
    assert summary["unique_physical_pairs"] == 2
    assert summary["unique_left_seeds"] == 2
    assert summary["surfaces"] == 2
    assert summary["variants"] == 2
    assert summary["max_physical_pair_dominance"] == pytest.approx(2 / 3)


def test_empty_float_stat_returns_nan_for_empty_frame():
    assert _empty_float_stat(pd.DataFrame(), "value", "max") != _empty_float_stat(pd.DataFrame(), "value", "max")


def _boundary_row(
    *,
    source_index: int,
    left_seed: int = 1,
    right_seed: int = 2,
    left_step: int = 3,
    right_step: int = 4,
    surface: str = "ood",
    variant: str = "wrong_matched_history",
) -> dict[str, object]:
    return {
        "source_index": source_index,
        "coupling_row_index": source_index + 100,
        "surface": surface,
        "variant": variant,
        "target": "future_yaw_response",
        "left_seed": left_seed,
        "left_step": left_step,
        "right_seed": right_seed,
        "right_step": right_step,
        "capability_z_distance": 0.2,
        "action_distance": 0.001,
        "coupling_gap": 1.0,
    }
