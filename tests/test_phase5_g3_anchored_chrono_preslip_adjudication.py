from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_g3_anchored_chrono_preslip_adjudication.py"
SPEC = importlib.util.spec_from_file_location("phase5_g3_adjudication", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_anchor_is_exact_replayed_m3267_required_slide_witness() -> None:
    prereg = mod.build_preregistration()
    anchor = prereg["frozen_feasibility_anchor"]
    assert anchor["source_arm"] == "required_slide"
    assert anchor["source_exact_replay_pass"] is True
    assert anchor["source_d_star_m"] == 21.699999999999946
    assert len(anchor["source_segments_float64_sha256"]) == 64


def test_anchor_is_inserted_at_preregistered_search_distance() -> None:
    candidates = mod._anchored_structured_candidates(
        "required_slide",
        mod.QUICK_CELLS[0].cell_id,
        mod.QUICK_BUDGET.segments,
        chrono=True,
    )
    expected = mod._anchor_segments(mod.QUICK_BUDGET.segments)
    assert np.array_equal(candidates[mod.ANCHOR_INSERTION_INDEX], expected)
    assert mod.build_preregistration()["frozen_feasibility_anchor"]["joint_search_distance_m"] == 23.0


def test_final_route_has_explicit_stop_rule_and_fresh_seed() -> None:
    prereg = mod.build_preregistration()
    assert prereg["seed_discipline"]["seed_base"] == 32690017
    assert prereg["stop_rule"].startswith("This is the final")
    assert "M3267 planar incompleteness remains" in prereg["claim_boundary"]
