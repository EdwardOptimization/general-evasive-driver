from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_g1_preslip_reachable_set_adjudication.py"
SPEC = importlib.util.spec_from_file_location("phase5_g1_adjudication", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _point(x: float, y: float, beta: float, rear_slip: float, speed: float = 10.0) -> object:
    return mod.TrajectoryPoint(x=x, y=y, psi=0.0, speed=speed, beta=beta, rear_slip=rear_slip)


def test_required_slide_onset_after_obb_contact_is_invalid() -> None:
    cell = mod.BoundaryCell("contact", mu=0.6, speed_mps=10.0)
    # D=10, near face=9.35, vehicle front at slide onset is x+2.2=9.6.
    points = [
        _point(0.0, 0.0, 0.0, 0.0),
        _point(7.4, 2.0, 0.22, 0.20),
        _point(7.5, 2.1, 0.24, 0.22),
        _point(7.6, 2.2, 0.25, 0.23),
        _point(7.7, 2.3, 0.26, 0.24),
        _point(14.0, 2.4, 0.20, 0.20),
    ]
    result = mod.evaluate_trajectory_at_distance(points, cell, "required_slide", 10.0)
    assert result["controlled_slide_onset_index"] == 1
    assert result["onset_before_contact"] is False
    assert result["mode_valid"] is False


def test_required_slide_onset_before_contact_can_be_mode_valid() -> None:
    cell = mod.BoundaryCell("contact", mu=0.6, speed_mps=10.0, road_half_width_m=8.0)
    points = [
        _point(0.0, 0.0, 0.0, 0.0),
        _point(5.0, 2.0, 0.22, 0.20),
        _point(5.2, 2.1, 0.24, 0.22),
        _point(5.4, 2.2, 0.25, 0.23),
        _point(5.6, 2.3, 0.26, 0.24),
        _point(14.0, 2.5, 0.20, 0.20),
    ]
    result = mod.evaluate_trajectory_at_distance(points, cell, "required_slide", 10.0)
    assert result["onset_before_contact"] is True
    assert result["mode_valid"] is True


def test_post_collision_slide_samples_do_not_make_mode_valid() -> None:
    cell = mod.BoundaryCell("terminal", mu=0.6, speed_mps=10.0, road_half_width_m=8.0)
    points = [
        _point(0.0, 0.0, 0.0, 0.0),
        _point(8.0, 0.0, 0.0, 0.0),
        _point(9.0, 2.5, 0.22, 0.20),
        _point(9.2, 2.6, 0.24, 0.22),
        _point(9.4, 2.7, 0.25, 0.23),
        _point(9.6, 2.8, 0.26, 0.24),
    ]
    result = mod.evaluate_trajectory_at_distance(points, cell, "required_slide", 10.0)
    assert result["collision"] is True
    assert result["controlled_slide_onset_index"] is None
    assert result["mode_valid"] is False


def test_chrono_world_pose_is_transformed_to_initial_lane_frame() -> None:
    psi0 = math.pi / 3.0
    scenario = {
        "initial_state": {"x": 100.0, "y": -40.0, "psi": psi0, "vx": 12.0, "vy": 0.0}
    }
    forward = 2.0
    left = 0.5
    world_x = 100.0 + math.cos(psi0) * forward - math.sin(psi0) * left
    world_y = -40.0 + math.sin(psi0) * forward + math.cos(psi0) * left
    rows = [
        (
            np.zeros(72),
            False,
            False,
            "",
            {
                "x": world_x,
                "y": world_y,
                "psi": psi0 + 0.1,
                "vx_body": 12.0,
                "vy_body": 0.0,
                "tire_telemetry": [],
            },
        )
    ]
    points = mod._chrono_trajectory(rows, scenario)
    assert points[0].x == 0.0
    assert points[0].y == 0.0
    assert math.isclose(points[1].x, forward, abs_tol=1e-12)
    assert math.isclose(points[1].y, left, abs_tol=1e-12)
    assert math.isclose(points[1].psi, 0.1, abs_tol=1e-12)


def test_structured_grip_candidates_include_clearable_early_pulse() -> None:
    cell = mod.QUICK_PLANAR_CELLS[0]
    candidates = mod._structured_candidates("grip", cell.cell_id, 8, chrono=False)
    boundaries = [
        mod.refine_distance_for_trajectory(
            mod.simulate_planar_trajectory(cell, candidate, mod.QUICK_PLANAR_BUDGET.horizon_s),
            cell,
            "grip",
        )
        for candidate in candidates
    ]
    assert any(row["d_star_m"] is not None for row in boundaries)


def test_free_counterexample_requires_clear_distance_gain() -> None:
    cell = mod.BoundaryCell("verdict", mu=0.6, speed_mps=10.0)
    by_arm = {
        "grip": {"d_star_m": 10.0, "best_boundary": {}},
        "required_slide": {"d_star_m": 9.5, "best_boundary": {}},
        "free": {
            "d_star_m": 9.4,
            "best_boundary": {"free_mode_classification": "controlled_slide_like"},
        },
    }
    result = mod._cell_verdict(cell, by_arm)
    assert result["no_drift_advantage_pass"] is False
    assert result["free_counterexample"] is True


def test_preregistration_uses_distance_boundary_and_bounded_scope() -> None:
    prereg = mod.build_preregistration()
    assert prereg["protocol_revision"] == "r1"
    assert prereg["protocol_revision_history"][0]["revision"] == "r0"
    assert prereg["metric"]["d_star"].startswith("minimum obstacle-center distance")
    assert prereg["decision_rule"]["falsify"].endswith("more than 0.25 m")
    assert "split-mu" in prereg["out_of_scope"]
