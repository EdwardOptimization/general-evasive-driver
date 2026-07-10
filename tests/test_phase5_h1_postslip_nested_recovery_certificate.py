from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_h1_postslip_nested_recovery_certificate.py"
SPEC = importlib.util.spec_from_file_location("phase5_h1_certificate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_physical_zero_pedals_map_to_negative_one_normalized() -> None:
    action = mod.g0.physical_command_to_model_action(0.0, 0.0, 0.0)
    np.testing.assert_array_equal(action, np.asarray([0.0, -1.0, -1.0]))
    full_brake = mod.g0.physical_command_to_model_action(0.0, 0.0, 1.0)
    np.testing.assert_array_equal(full_brake, np.asarray([0.0, -1.0, 1.0]))


def test_control_library_is_strictly_nested_and_has_no_pedal_conflict() -> None:
    policies = mod.policy_library()
    baseline = {spec.policy_id for spec in policies if spec.in_baseline_set}
    expanded = {spec.policy_id for spec in policies}
    assert len(baseline) == 6
    assert len(expanded) == 30
    assert baseline < expanded
    assert all(not (spec.throttle > 0.0 and spec.brake > 0.0) for spec in policies)


def test_mirrored_cells_have_mirrored_initial_body_state() -> None:
    positive, negative = mod.QUICK_CELLS
    positive_scenario = mod._scenario(positive, 1)
    negative_scenario = mod._scenario(negative, 1)
    positive_state = positive_scenario["initial_state"]
    negative_state = negative_scenario["initial_state"]
    assert positive_state["vx"] == negative_state["vx"]
    assert positive_state["vy"] == -negative_state["vy"]
    assert positive_state["yaw_rate"] == -negative_state["yaw_rate"]


def _row(policy_id: str, *, baseline: bool, success: bool, steer: float) -> dict:
    return {
        "policy_id": policy_id,
        "policy_family": "pedal_only" if baseline else "countersteer_feedback",
        "in_baseline_set": baseline,
        "initial_state_sha256": "same",
        "initial_state_match": True,
        "initial_slide_truth": True,
        "success": success,
        "recovery_step": 20 if success else None,
        "recovery_time_s": 0.4 if success else None,
        "vx_at_recovery_mps": 8.0 if success else None,
        "completion_reason": "recovered" if success else "spin",
        "max_abs_steer": steer,
        "final_beta_rad": 0.05 if success else 1.2,
        "final_vx_mps": 8.0 if success else 3.0,
    }


def test_seed_verdict_requires_added_steering_for_strictness() -> None:
    cell = mod.QUICK_CELLS[0]
    rows = [
        _row("pedal_coast", baseline=True, success=False, steer=0.0),
        _row("pedal_brake0p50", baseline=True, success=False, steer=0.0),
        _row("steer", baseline=False, success=True, steer=0.8),
    ]
    verdict = mod.seed_verdict(cell, 1, rows)
    assert verdict["weak_inclusion_pass"] is True
    assert verdict["strict_expansion_witness"] is True
    rows[0]["success"] = True
    rows[0]["recovery_step"] = 10
    rows[0]["recovery_time_s"] = 0.2
    verdict = mod.seed_verdict(cell, 1, rows)
    assert verdict["strict_expansion_witness"] is False


def test_preregistration_freezes_robust_scope_and_rejects_old_counts() -> None:
    prereg = mod.build_preregistration()
    assert len(prereg["cells"]["full"]) == 18
    assert prereg["seeds"]["full_per_cell"] == 3
    assert prereg["control_sets"]["baseline_subset_of_expanded"] is True
    assert prereg["control_sets"]["esc_claim"] is False
    assert "normalized pedal zero" in prereg["invalid_predecessor_warning"]
    assert "at least 6 of 18 cells" in prereg["decision_rule"]["full_support"]
