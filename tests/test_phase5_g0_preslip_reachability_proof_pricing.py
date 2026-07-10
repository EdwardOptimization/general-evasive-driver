from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.py"
SPEC = importlib.util.spec_from_file_location("phase5_g0_pricing", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_physical_command_mapping_uses_true_zero_pedals() -> None:
    action = mod.physical_command_to_model_action(0.25, 0.0, 0.0)
    np.testing.assert_allclose(action, np.asarray([0.25, -1.0, -1.0]))
    np.testing.assert_allclose(
        mod.physical_command_to_model_action(-1.0, 1.0, 1.0),
        np.asarray([-1.0, 1.0, 1.0]),
    )


def test_signed_sat_separation_distinguishes_clear_and_overlap() -> None:
    axes = mod._box_axes(0.0)
    base = mod._box_corners(0.0, 0.0, 0.0, 1.0, 0.5)
    clear = mod._box_corners(3.0, 0.0, 0.0, 1.0, 0.5)
    overlap = mod._box_corners(1.5, 0.0, 0.0, 1.0, 0.5)
    assert mod.signed_sat_separation(base, axes, clear, axes) > 0.0
    assert mod.signed_sat_separation(base, axes, overlap, axes) <= 0.0


def test_zhao_larger_control_set_positive_control_is_detected() -> None:
    result = mod.dubins_positive_control()
    assert result["conservative_clearance_m"] < 0.0
    assert result["beyond_limit_clearance_m"] > 0.0
    assert result["positive_control_pass"] is True


def test_planar_search_is_deterministic_for_a_small_budget() -> None:
    cell = mod.PlanarCell(
        "test",
        mu=0.60,
        speed_mps=12.0,
        obstacle_x_m=10.0,
        obstacle_half_width_m=0.8,
        obstacle_half_depth_m=0.6,
        horizon_s=1.0,
    )
    budget = mod.SearchBudget(segments=3, population=8, elites=2, iterations=2)
    first = mod.cem_search_planar(cell, "grip", budget, seed=123)
    second = mod.cem_search_planar(cell, "grip", budget, seed=123)
    assert first["best"]["score"] == second["best"]["score"]
    np.testing.assert_array_equal(first["best_segments_physical"], second["best_segments_physical"])


def test_preregistration_forbids_a_pricing_stage_dominance_claim() -> None:
    prereg = mod.build_preregistration()
    assert "reachable-set dominance" in prereg["forbidden_claims"]
    assert prereg["decision_rule"]["block_and_reprice"].startswith("any gate fails")
