from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/feasibility_audit/moving_obstacle_pricing.py"


def load_module():
    spec = importlib.util.spec_from_file_location("moving_obstacle_pricing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_quick_row_streams_are_dynamic_and_disjoint():
    mod = load_module()
    selection = mod.sample_rows(True, "selection")
    validation = mod.sample_rows(True, "validation")
    sel_seeds = {row["eval_seed"] for rows in selection.values() for row in rows}
    val_seeds = {row["eval_seed"] for rows in validation.values() for row in rows}
    assert sel_seeds.isdisjoint(val_seeds)
    assert sorted(selection) == ["fast_late_centering", "slow_early_centering"]
    assert all(len(rows) == 2 for rows in selection.values())
    assert all(len(rows) == 4 for rows in validation.values())
    for rows in [*selection.values(), *validation.values()]:
        for row in rows:
            assert abs(row["crosser_lateral_velocity_mps"]) > 0.0
            assert np.isfinite(row["predicted_lateral_offset_at_arrival_m"])
            config = mod.row_env_config(row)
            assert config.obstacle.motion_mode == "constant_velocity_crosser"
            assert config.obstacle_relative_velocity_mode == "ego"
            assert config.obstacle.perception_reveal_distance == row["reveal_distance_m"]


def test_aggregate_primary_gap_uses_oracle_solved_denominator():
    mod = load_module()
    row_base = {
        "cell": "toy",
        "oracle_solved": True,
        "fixed_v4_incumbent_outcome": "collision",
        "fixed_star_outcome": "collision",
        "v4_rls_outcome": "collision",
        "v4_pertuned_outcome": "collision",
    }
    rows = [
        {**row_base, "eval_seed": 1},
        {**row_base, "eval_seed": 2, "v4_pertuned_outcome": "success"},
        {**row_base, "eval_seed": 3, "oracle_solved": False},
    ]
    out = mod.aggregate_cells(rows, quick=True)["toy"]
    assert out["n_rows_unfiltered"] == 3
    assert out["n_rows_oracle_solved"] == 2
    gap = out["readouts_oracle_solved_denominator"]["structural_gap_oracle_minus_pertuned"]
    assert gap["value"] == 0.5
