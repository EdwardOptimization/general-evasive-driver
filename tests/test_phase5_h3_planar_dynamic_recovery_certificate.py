from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "phase5_h3_planar_dynamic_recovery_certificate.py"
SPEC = importlib.util.spec_from_file_location("phase5_h3_certificate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_three_source_prefixes_are_frozen() -> None:
    segments = mod.source_segments_by_cell()
    assert set(segments) == {"mu0p35_v12", "mu0p60_v14", "mu0p90_v16"}
    assert all(value.shape == (8, 3) for value in segments.values())
    assert all(len(value) == 64 for value in mod.source_hashes().values())


def test_full_grid_has_seven_branches_per_mu() -> None:
    assert len(mod.FULL_CELLS) == 21
    for mu in (0.35, 0.60, 0.90):
        assert sum(cell.mu == mu for cell in mod.FULL_CELLS) == 7


def test_prefix_state_is_complete_and_repeatable() -> None:
    first = mod._simulate_prefix(mod.QUICK_CELLS[0])
    second = mod._simulate_prefix(mod.QUICK_CELLS[0])
    assert first["state"].as_array().shape == (8,)
    assert first["trajectory_sha256"] == second["trajectory_sha256"]
    assert first["state_sha256"] == second["state_sha256"]


def test_preregistration_freezes_compact_model_scope() -> None:
    prereg = mod.build_preregistration()
    assert prereg["priced_by"]["planar_entry_cells_passed"] == 3
    assert prereg["control_sets"]["baseline_subset_of_expanded"] is True
    assert prereg["recovery_contract"]["minimum_time_advantage_s"] == 0.20
    assert "at least 6/9 cells eligible" in prereg["decision_rule"]["quick_support"]
    assert "not detailed Chrono strictness" in prereg["claim_boundary"]


def test_zero_physical_pedals_use_correct_normalized_action() -> None:
    action = mod.g0.physical_command_to_model_action(0.0, 0.0, 0.0)
    assert action.tolist() == [0.0, -1.0, -1.0]
