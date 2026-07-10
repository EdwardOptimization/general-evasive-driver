from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_g2_chrono_preslip_boundary_adjudication.py"
SPEC = importlib.util.spec_from_file_location("phase5_g2_adjudication", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def _boundary(mode: str) -> dict[str, object]:
    return {"free_mode_classification": mode}


def test_preregistration_uses_fresh_seed_and_keeps_planar_negative_visible() -> None:
    prereg = mod.build_preregistration()
    assert prereg["seed_discipline"]["seed_base"] == 32680017
    assert prereg["metric"]["tolerance_m"] == 0.25
    assert "cannot be overwritten" in prereg["negative_result_policy"]
    assert len(prereg["cells"]["full"]) == 3


def test_pooling_reclassifies_free_grip_trajectory_into_grip_set() -> None:
    cell = mod.g1.BoundaryCell("pool", 0.6, 16.0)
    points = [
        mod.g1.TrajectoryPoint(0.0, 0.0, 0.0, 16.0, 0.0, 0.0),
        mod.g1.TrajectoryPoint(20.0, 3.0, 0.0, 15.0, 0.02, 0.02),
        mod.g1.TrajectoryPoint(30.0, 3.0, 0.0, 14.0, 0.02, 0.02),
    ]
    search = {
        "cell_id": "pool",
        "arm": "free",
        "seed": 1,
        "best_trajectory": [mod.asdict(point) for point in points],
    }
    rows = [
        {"arm": "grip", "d_star_m": 20.0, "seed_d_stars_m": [20.0], "best_boundary": _boundary("grip_like")},
        {"arm": "required_slide", "d_star_m": 24.0, "seed_d_stars_m": [24.0], "best_boundary": _boundary("controlled_slide_like")},
        {"arm": "free", "d_star_m": 18.0, "seed_d_stars_m": [18.0], "best_boundary": _boundary("grip_like")},
    ]
    verdict, candidates = mod._pooled_cell_verdict(cell, [search], rows)
    grip_candidates = [row for row in candidates if row["target_arm"] == "grip"]
    assert grip_candidates
    assert verdict["pooled_sources"]["grip"]["source_arm"] == "free"


def test_free_early_slide_requires_distance_gain_for_counterexample() -> None:
    assert mod.DISTANCE_TOLERANCE_M == 0.25
    grip_d = 12.0
    free_d = 11.7
    assert free_d + mod.DISTANCE_TOLERANCE_M < grip_d
