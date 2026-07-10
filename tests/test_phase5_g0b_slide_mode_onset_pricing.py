from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_g0b_slide_mode_onset_pricing.py"
SPEC = importlib.util.spec_from_file_location("phase5_g0b_pricing", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_axle_specific_tire_slip_does_not_use_all_wheel_maximum() -> None:
    info = {
        "tire_telemetry": [
            {"axle": "front", "slip_angle_rad": 0.70},
            {"axle": "front", "slip_angle_rad": -0.60},
            {"axle": "rear", "slip_angle_rad": 0.12},
            {"axle": "rear", "slip_angle_rad": -0.10},
        ]
    }
    rear, front, count = mod._rear_front_tire_slip(info)
    assert rear == 0.12
    assert front == 0.70
    assert count == 4


def test_initial_deep_slide_is_detected_in_planar_positive_control() -> None:
    cell = mod.OnsetCell("positive", mu=0.60, speed_mps=12.0, emergency_obstacle_x_m=20.0)
    segments = np.zeros((4, 3), dtype=np.float64)
    result = mod.simulate_planar_onset(
        cell,
        segments,
        horizon_s=0.4,
        initial_beta_rad=0.28,
        initial_yaw_rate_rad_s=0.0,
    )
    assert result["max_abs_beta_rad"] >= 0.28
    assert result["max_abs_rear_slip_angle_rad"] >= mod.REAR_SLIP_MIN_RAD


def test_planar_onset_search_replays_deterministically_with_small_budget() -> None:
    cell = mod.OnsetCell("determinism", mu=0.60, speed_mps=12.0, emergency_obstacle_x_m=10.0)
    budget = mod.OnsetBudget(segments=3, population=8, elites=2, iterations=2, horizon_s=0.6)
    first = mod.search_planar_onset(cell, budget, seed=456)
    second = mod.search_planar_onset(cell, budget, seed=456)
    assert first["best"]["score"] == second["best"]["score"]
    np.testing.assert_array_equal(first["best_segments_physical"], second["best_segments_physical"])


def test_preregistration_keeps_m3266_as_pricing_only() -> None:
    prereg = mod.build_preregistration()
    assert prereg["claim_boundary"].endswith("no reachable-set dominance")
    assert "lowering the 0.20 rad slide threshold or four-frame dwell after reading results" in prereg[
        "forbidden_changes"
    ]
