from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_h2_dynamic_prefix_recovery_certificate.py"
SPEC = importlib.util.spec_from_file_location("phase5_h2_certificate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_source_prefix_is_frozen_from_m3266() -> None:
    segments = mod.source_segments()
    assert segments.shape == (8, 3)
    assert len(mod.source_segments_sha256()) == 64
    assert (segments[:, 1] * segments[:, 2] > 0.0).any()


def test_branch_grid_is_frozen_inside_measured_dwell_window() -> None:
    assert [cell.branch_step for cell in mod.QUICK_CELLS] == [30, 45, 60, 75, 90]
    assert [cell.branch_step for cell in mod.FULL_CELLS] == list(range(30, 97, 6))
    assert len(mod.FULL_CELLS) == 12


def _row(policy_id: str, *, baseline: bool, success: bool, time_s: float | None) -> dict:
    return {
        "policy_id": policy_id,
        "policy_family": "pedal_only" if baseline else "countersteer_feedback",
        "in_baseline_set": baseline,
        "prefix_trajectory_sha256": "prefix",
        "branch_state_sha256": "branch",
        "branch_beta_rad": 0.3,
        "branch_yaw_rate_rad_s": 1.0,
        "branch_rear_slip_angle_rad": 0.2,
        "branch_slide_truth": True,
        "success": success,
        "recovery_step": None if time_s is None else int(round(time_s / mod.h1.DT)),
        "recovery_time_s": time_s,
        "vx_at_recovery_mps": 8.0 if success else None,
        "completion_reason": "recovered" if success else "horizon",
        "max_abs_steer": 0.0 if baseline else 0.6,
        "final_beta_rad": 0.05 if success else 0.4,
        "final_vx_mps": 8.0,
    }


def test_time_advantage_creates_strict_deadline_interval() -> None:
    rows = [
        _row("pedal_coast", baseline=True, success=True, time_s=0.8),
        _row("pedal_brake", baseline=True, success=False, time_s=None),
        _row("steer", baseline=False, success=True, time_s=0.5),
    ]
    verdict = mod.seed_verdict(mod.QUICK_CELLS[0], 1, rows)
    assert verdict["weak_inclusion_pass"] is True
    assert verdict["strict_expansion_witness"] is True
    assert verdict["recovery_time_advantage_s"] == pytest.approx(0.3)
    assert verdict["strict_deadline_interval_s"] == [0.5, 0.8]


def test_small_time_advantage_is_not_strict() -> None:
    rows = [
        _row("pedal_coast", baseline=True, success=True, time_s=0.6),
        _row("steer", baseline=False, success=True, time_s=0.5),
    ]
    verdict = mod.seed_verdict(mod.QUICK_CELLS[0], 1, rows)
    assert verdict["strict_expansion_witness"] is False


def test_preregistration_freezes_dynamic_branch_and_robust_thresholds() -> None:
    prereg = mod.build_preregistration()
    assert prereg["control_sets"]["baseline_subset_of_expanded"] is True
    assert prereg["control_sets"]["esc_claim"] is False
    assert prereg["recovery_contract"]["minimum_time_advantage_s"] == 0.20
    assert "at least 8/12 cells eligible" in prereg["decision_rule"]["full_support"]
    assert "resetting body wheel or tire state at the branch" in prereg["forbidden"]
