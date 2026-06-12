from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/feasibility_audit/high_speed_pricing.py"


def load_module():
    spec = importlib.util.spec_from_file_location("high_speed_pricing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_scale_adapter_recovers_high_speed_channel():
    mod = load_module()
    obs = np.zeros(72, dtype=np.float32)
    obs[0] = 36.0 / mod.HIGH_SPEED_SCALE.ego_vx
    obs[1] = 4.0 / mod.HIGH_SPEED_SCALE.ego_vy
    obs[3] = 10.0 / mod.HIGH_SPEED_SCALE.ego_ax
    obs[4] = 12.0 / mod.HIGH_SPEED_SCALE.ego_ay
    adapted = mod.canonicalize_high_speed_obs(obs)
    assert abs(float(adapted[0] * 20.0) - 36.0) < 1e-6
    assert abs(float(adapted[1] * 12.0) - 4.0) < 1e-6
    assert abs(float(adapted[3] * 15.0) - 10.0) < 1e-6
    assert abs(float(adapted[4] * 15.0) - 12.0) < 1e-6


def test_quick_rows_use_high_speed_profile_and_disjoint_streams():
    mod = load_module()
    selection = mod.sample_rows(True, "selection")
    validation = mod.sample_rows(True, "validation")
    sel_seeds = {row["eval_seed"] for rows in selection.values() for row in rows}
    val_seeds = {row["eval_seed"] for rows in validation.values() for row in rows}
    assert sel_seeds.isdisjoint(val_seeds)
    assert sorted(selection) == ["hs24_tight_mu055", "hs30_tight_mu075"]
    assert all(len(rows) == 2 for rows in selection.values())
    assert all(len(rows) == 4 for rows in validation.values())
    for rows in [*selection.values(), *validation.values()]:
        for row in rows:
            assert row["speed_mps"] > 23.0
            assert row["distance_m"] > row["reveal_distance_m"]
            config = mod.row_env_config(row)
            assert config.observation_scale.ego_vx == mod.HIGH_SPEED_SCALE.ego_vx
            assert config.observation_scale.road_lookahead_time_s == 2.5
            assert config.max_speed_limit == 45.0
            assert config.obstacle.motion_mode == "static"


def test_aggregate_primary_gap_uses_oracle_solved_denominator():
    mod = load_module()
    row_base = {
        "cell": "toy",
        "label": "drift_required",
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
