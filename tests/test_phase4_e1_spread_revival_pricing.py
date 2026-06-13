from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e1_spread_revival_pricing as e1  # noqa: E402


def test_preregistration_uses_e0_envelope_and_blocks_full_verdict() -> None:
    prereg = e1.build_preregistration()

    assert prereg["e0_axis_table_sha256"]
    assert prereg["quick_mode_is_verdict"] is False
    assert prereg["quick_variants"] == ["sedan_tmeasy", "bmw_e90_tmeasy", "uazbus_tmeasy"]
    assert "payload_position_or_cg_height" in prereg["blocked_by_e0_without_new_connector"]
    assert prereg["full_mode_placeholder"]["status"] == "not_registered_by_M3249"


def test_choose_fixed_and_pertuned_uses_global_and_per_variant_scores() -> None:
    g0 = (1.0, 1.0, 1.0)
    g1 = (1.8, 1.45, 1.4)
    results = {
        ("sedan_tmeasy", g0): {"score": 1.0},
        ("sedan_tmeasy", g1): {"score": 3.0},
        ("bmw_e90_tmeasy", g0): {"score": 5.0},
        ("bmw_e90_tmeasy", g1): {"score": 1.0},
    }

    fixed, tuned = e1.choose_fixed_and_pertuned(results)

    assert fixed == g0  # global scores: g0=6, g1=4
    assert tuned["sedan_tmeasy"] == g1
    assert tuned["bmw_e90_tmeasy"] == g0


def test_summarize_quick_requires_all_arms_and_candidates() -> None:
    prereg = {
        "quick_variants": ["sedan_tmeasy"],
        "quick_mode_is_verdict": False,
    }
    rows = []
    base = {
        "variant": "sedan_tmeasy",
        "chrono_outcome": "success",
        "reset_obs_finite": True,
        "variant_match": True,
    }
    for arm in e1.ARMS:
        rows.append({**base, "arm": arm, "candidate": arm})
    rows.append({**base, "arm": "native_oracle_candidate", "candidate": "structured:full_brake"})
    rows.append({**base, "arm": "native_oracle_candidate", "candidate": "cem_iter0_sample0"})

    summary = e1.summarize_quick(rows, prereg)

    assert summary["quick_gates"]["all_passed"] is True
    assert summary["decision"]["status_pass"] is True
    assert summary["decision"]["e1_full_verdict"] is None
