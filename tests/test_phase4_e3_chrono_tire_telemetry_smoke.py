from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e3_chrono_tire_telemetry_smoke as telemetry  # noqa: E402


def test_preregistration_freezes_tire_telemetry_smoke_scope() -> None:
    prereg = telemetry.build_preregistration()

    assert prereg["frozen_before_any_tire_telemetry_rollout"] is True
    assert prereg["quick_mode_is_verdict"] is False
    assert prereg["chrono_variant"] == "sedan_tmeasy"
    assert [case["case_id"] for case in prereg["cases"]] == ["coast_hold", "brake_steer"]
    assert prereg["sample_steps"] == [0, 1, 6, 12]
    assert telemetry.expected_sample_count(prereg) == 8
    assert telemetry.expected_wheel_count(prereg) == 32
    assert prereg["full_e3_placeholder"]["status"] == "not_registered_by_M3254"


def test_base_scenario_keeps_obs72_action3_contract_inputs() -> None:
    scenario = telemetry.base_scenario(case_id="unit", mu=0.5875, speed_mps=8.0)

    assert scenario["chrono_vehicle_variant"] == "sedan_tmeasy"
    assert scenario["dt"] == 0.02
    assert scenario["track_radius"] == 900.0
    assert scenario["obstacle_slots"] == 4
    assert scenario["obstacle"]["enabled"] is False
    assert scenario["params"]["max_steer"] == 0.62
    assert scenario["initial_state"]["vx"] == 8.0


def _passing_sample_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case_id in ("coast_hold", "brake_steer"):
        for step in (0, 1, 6, 12):
            rows.append(
                {
                    "case_id": case_id,
                    "sample_step": str(step),
                    "obs72_finite": "True",
                    "tire_telemetry_available": "True",
                    "tire_telemetry_wheel_count": "4",
                    "tire_telemetry_error": "",
                }
            )
    return rows


def _passing_wheel_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sample in _passing_sample_rows():
        for wheel_index in range(4):
            row = {
                "case_id": sample["case_id"],
                "sample_step": sample["sample_step"],
                "wheel_index": str(wheel_index),
            }
            for field in telemetry.WHEEL_NUMERIC_FIELDS:
                row[field] = "1.0"
            row["normal_load_n"] = str(3000.0 + 10.0 * wheel_index)
            rows.append(row)
    return rows


def test_summarize_quick_requires_finite_four_wheel_telemetry_and_blocks_track_f() -> None:
    prereg = telemetry.build_preregistration()

    summary = telemetry.summarize_quick(_passing_sample_rows(), _passing_wheel_rows(), prereg, elapsed_s=1.0)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["sample_row_count"] == 8
    assert summary["wheel_row_count"] == 32
    assert summary["decision"]["telemetry_quick_verdict"] == "tire_telemetry_smoke_passed"
    assert summary["decision"]["full_e3_verdict"] == "not_decided_by_quick_mode"
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["min_tire_normal_load_n"] == 3000.0


def test_summarize_quick_fails_missing_wheel_rows() -> None:
    prereg = telemetry.build_preregistration()

    summary = telemetry.summarize_quick(_passing_sample_rows(), _passing_wheel_rows()[:-1], prereg, elapsed_s=1.0)

    assert summary["protocol_gates"]["wheel_row_count_complete"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["telemetry_quick_verdict"] == "tire_telemetry_smoke_failed"
