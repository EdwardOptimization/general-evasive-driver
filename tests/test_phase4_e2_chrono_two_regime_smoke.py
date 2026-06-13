from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e2_chrono_two_regime_smoke as e2  # noqa: E402


def test_preregistration_freezes_quick_nonverdict_scope() -> None:
    prereg = e2.build_preregistration()

    assert prereg["frozen_before_any_e2_chrono_rollout"] is True
    assert prereg["quick_mode_is_verdict"] is False
    assert prereg["quick_variants"] == ["sedan_tmeasy"]
    assert prereg["quick_arms"] == ["oracle_ramp", "threshold_seeker", "fixed_ramp"]
    assert "delay25_tight" in {cell["cell_id"] for cell in prereg["quick_cells"]}
    assert len(e2.expected_quick_units(prereg)) == 18
    assert prereg["full_e2_placeholder"]["status"] == "not_registered_by_M3251"


def test_ego_degradation_filter_delays_only_ego_channels() -> None:
    obs0 = np.arange(72, dtype=np.float32)
    obs1 = obs0 + 100.0
    obs2 = obs0 + 200.0
    filt = e2.EgoDegradationFilter(delay_steps=1, noise_std=0.0, seed=123)

    out0 = filt.reset(obs0)
    out1 = filt.step(obs1)
    out2 = filt.step(obs2)

    np.testing.assert_allclose(out0, obs0)
    np.testing.assert_allclose(out1[:9], obs0[:9])
    np.testing.assert_allclose(out1[9:], obs1[9:])
    np.testing.assert_allclose(out2[:9], obs1[:9])
    np.testing.assert_allclose(out2[9:], obs2[9:])


def test_summarize_quick_requires_all_expected_rows_and_keeps_track_f_blocked() -> None:
    prereg = e2.build_preregistration()
    rows = []
    for unit in e2.expected_quick_units(prereg):
        rows.append(
            {
                "role": "quick_eval",
                "variant": unit["variant"],
                "cell_id": unit["cell"]["cell_id"],
                "reveal_m": str(unit["reveal"]),
                "mu": str(unit["mu"]),
                "seed": str(unit["seed"]),
                "arm": unit["arm"],
                "success": "True" if unit["arm"] == "oracle_ramp" else "False",
                "reset_obs_finite": "True",
                "variant_match": "True",
            }
        )
    calibration = {
        "sedan_tmeasy": {
            "variant": "sedan_tmeasy",
            "tau": 0.08,
            "max_shortfall": 0.01,
            "outcome": "timeout_other",
            "reset_obs_finite": True,
            "variant_match": True,
        }
    }

    summary = e2.summarize_quick(rows, prereg, calibration=calibration, elapsed_s=1.0)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e2_quick_verdict"] == "protocol_smoke_passed"
    assert summary["decision"]["two_regime_law_verdict"] == "not_decided_by_quick_mode"
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["quick_mode_is_verdict"] is False


def test_summarize_quick_fails_missing_degraded_spot() -> None:
    prereg = e2.build_preregistration()
    rows = []
    for unit in e2.expected_quick_units(prereg):
        if unit["cell"]["cell_id"] != "clean":
            continue
        rows.append(
            {
                "role": "quick_eval",
                "variant": unit["variant"],
                "cell_id": unit["cell"]["cell_id"],
                "reveal_m": str(unit["reveal"]),
                "mu": str(unit["mu"]),
                "seed": str(unit["seed"]),
                "arm": unit["arm"],
                "success": "False",
                "reset_obs_finite": "True",
                "variant_match": "True",
            }
        )

    summary = e2.summarize_quick(rows, prereg, calibration={"sedan_tmeasy": {}}, elapsed_s=1.0)

    assert summary["protocol_gates"]["degraded_spot_rows_present"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e2_quick_verdict"] == "protocol_smoke_failed"
