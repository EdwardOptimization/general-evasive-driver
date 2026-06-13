from __future__ import annotations

import math
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e3_chrono_measurement_ac_smoke as e3  # noqa: E402


def test_preregistration_freezes_nonverdict_ac_smoke_scope() -> None:
    prereg = e3.build_preregistration()

    assert prereg["frozen_before_any_e3_chrono_rollout"] is True
    assert prereg["quick_mode_is_verdict"] is False
    assert prereg["chrono_variant"] == "sedan_tmeasy"
    assert {case["axis"] for case in prereg["measurement_a_cases"]} == {"long", "lat"}
    assert {case["driver"] for case in prereg["measurement_c_cases"]} == {
        "baseline_coast",
        "v4_incumbent",
    }
    assert e3.expected_case_count(prereg) == 4
    assert prereg["full_e3_placeholder"]["status"] == "not_registered_by_M3253"


def test_overshoot_scenario_uses_planar_injection_without_obstacle() -> None:
    scenario = e3.overshoot_scenario(
        case_id="unit",
        mu=0.5875,
        speed_mps=8.0,
        overshoot=1.15,
        offset_m=1.5,
    )

    assert scenario["chrono_vehicle_variant"] == "sedan_tmeasy"
    assert scenario["obstacle"]["enabled"] is False
    assert scenario["initial_state"]["x"] == e3.TRACK_RADIUS + 1.5
    assert scenario["initial_state"]["vy"] < 0.0
    assert scenario["initial_state"]["yaw_rate"] > 8.0 / e3.TRACK_RADIUS
    assert all(math.isfinite(float(value)) for value in scenario["initial_state"].values())


def test_summarize_quick_requires_all_ac_rows_and_keeps_track_f_blocked() -> None:
    prereg = e3.build_preregistration()
    rows = [
        {
            "measurement": "A",
            "case_id": "A_long",
            "axis": "long",
            "driver": "",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
        {
            "measurement": "A",
            "case_id": "A_lat",
            "axis": "lat",
            "driver": "",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
        {
            "measurement": "C",
            "case_id": "C_baseline_coast",
            "axis": "",
            "driver": "baseline_coast",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
        {
            "measurement": "C",
            "case_id": "C_v4_incumbent",
            "axis": "",
            "driver": "v4_incumbent",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
    ]

    summary = e3.summarize_quick(rows, prereg, elapsed_s=1.0)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e3_quick_verdict"] == "protocol_smoke_passed"
    assert summary["decision"]["measurement_a_verdict"] == "not_decided_by_quick_mode"
    assert summary["decision"]["measurement_c_verdict"] == "not_decided_by_quick_mode"
    assert summary["decision"]["track_f_admitted"] is False


def test_summarize_quick_fails_missing_measurement_c_driver() -> None:
    prereg = e3.build_preregistration()
    rows = [
        {
            "measurement": "A",
            "case_id": "A_long",
            "axis": "long",
            "driver": "",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
        {
            "measurement": "A",
            "case_id": "A_lat",
            "axis": "lat",
            "driver": "",
            "reset_obs_finite": "True",
            "variant_match": "True",
        },
    ]

    summary = e3.summarize_quick(rows, prereg, elapsed_s=1.0)

    assert summary["protocol_gates"]["measurement_c_drivers_covered"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e3_quick_verdict"] == "protocol_smoke_failed"
