from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


SCRIPT = Path("scripts/feasibility_audit/chrono_native_oracle_pricing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("chrono_native_oracle_pricing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_d1b_prereg_selects_three_gap_rows_per_level_and_two_variants():
    mod = _load_module()
    prereg = mod.build_preregistration()
    rows = prereg["selected_rows"]

    assert prereg["protocol"] == "d1b_chrono_native_oracle_pricing_preregistration"
    assert prereg["frozen_before_any_d1b_rollout"] is True
    assert prereg["chrono_vehicle_variants"] == ["sedan_tmeasy", "bmw_e90_tmeasy"]
    assert len(rows) == 9
    assert {row["level"] for row in rows} == {"S1", "S2", "S3"}
    for level in ("S1", "S2", "S3"):
        assert sum(row["level"] == level for row in rows) == 3
    assert all(row["source_oracle_solved"] for row in rows)
    assert all(row["source_pertuned_outcome"] != "success" for row in rows)
    assert all(row["oracle_by"].startswith("structured:") for row in rows)


def test_structured_tail_candidate_set_is_stable_and_action_bounded():
    mod = _load_module()
    candidates = mod.structured_tail_candidates()

    assert len(candidates) == 15
    assert candidates[0][0] == "full_brake"
    assert candidates[-1][0] == "swerve_-1_n20"
    for _name, tail in candidates:
        action = tail(0)
        assert action.shape == (3,)
        assert np.all(action >= -1.0)
        assert np.all(action <= 1.0)


def test_segments_tail_holds_last_segment_after_horizon():
    mod = _load_module()
    segments = np.asarray(
        [
            [0.0, -1.0, 1.0],
            [0.5, -0.5, 0.0],
            [-0.5, -1.0, 1.0],
        ],
        dtype=np.float32,
    )
    tail = mod._segments_tail(segments, segment_len=4)

    np.testing.assert_allclose(tail(0), segments[0])
    np.testing.assert_allclose(tail(5), segments[1])
    np.testing.assert_allclose(tail(99), segments[-1])
