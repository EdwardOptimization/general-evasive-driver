from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_h0_fixed_library_overlap_certificate.py"
SPEC = importlib.util.spec_from_file_location("phase5_h0_certificate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_action_library_is_complete_deduplicated_and_hash_frozen() -> None:
    library = mod.build_action_library()
    assert len(library) == 20
    assert sum(len(row["provenance"]) for row in library) == 21
    assert len({row["segments_float64_sha256"] for row in library}) == 20
    assert len(mod.action_library_sha256(library)) == 64


def test_action_library_keeps_failed_source_searches() -> None:
    library = mod.build_action_library()
    provenance = [item for row in library for item in row["provenance"]]
    failed_slide = [
        item
        for item in provenance
        if item["source_arm"] == "required_slide" and item["source_d_star_m"] is None
    ]
    assert len(failed_slide) == 3


def test_seed_verdict_supports_grip_ordering_and_detects_counterexample() -> None:
    cell = mod.g1.BoundaryCell("synthetic", 0.6, 16.0)
    rows = [
        {
            "action_id": "grip",
            "grip_d_star_m": 12.0,
            "required_slide_d_star_m": None,
            "free_d_star_m": 12.0,
            "free_boundary": {"free_mode_classification": "grip_like"},
        },
        {
            "action_id": "slide",
            "grip_d_star_m": None,
            "required_slide_d_star_m": 15.0,
            "free_d_star_m": 15.0,
            "free_boundary": {"free_mode_classification": "controlled_slide_like"},
        },
    ]
    verdict = mod._seed_verdict(cell, 1, rows)
    assert verdict["overlap_complete"] is True
    assert verdict["no_drift_advantage_pass"] is True
    assert verdict["free_slide_counterexample"] is False

    rows[1]["required_slide_d_star_m"] = 11.0
    rows[1]["free_d_star_m"] = 11.0
    counterexample = mod._seed_verdict(cell, 1, rows)
    assert counterexample["no_drift_advantage_pass"] is False
    assert counterexample["free_slide_counterexample"] is True


def test_local_frame_gate_requires_zero_initial_pose() -> None:
    point = mod.g1.TrajectoryPoint(0.0, 0.0, 0.0, 16.0, 0.0, 0.0)
    shifted = mod.g1.TrajectoryPoint(0.01, 0.0, 0.0, 16.0, 0.0, 0.0)
    assert mod._local_frame_pass([point]) is True
    assert mod._local_frame_pass([shifted]) is False
    assert mod._local_frame_pass([]) is False


def test_preregistration_freezes_overlap_scope_and_no_optimization() -> None:
    prereg = mod.build_preregistration()
    assert prereg["action_library"]["unique_action_count"] == 20
    assert prereg["action_library"]["provenance_count"] == 21
    assert prereg["seeds"]["full_per_cell"] == 8
    assert len(prereg["cells"]["full"]) == 3
    assert "optimization or action mutation" in prereg["forbidden"]
    assert "not a continuous Chrono control-set proof" in prereg["claim_boundary"]
