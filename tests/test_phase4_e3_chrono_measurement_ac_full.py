from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e3_chrono_measurement_ac_full as full_e3  # noqa: E402


def test_preregistration_freezes_full_e3_truth_definitions_and_counts() -> None:
    prereg = full_e3.build_preregistration()

    assert prereg["frozen_before_any_full_e3_rollout"] is True
    assert prereg["chrono_variant"] == "sedan_tmeasy"
    assert prereg["expected_full_latency_rows"] == 24
    assert prereg["expected_full_recovery_rows"] == 72
    assert prereg["expected_quick_latency_rows"] == 2
    assert prereg["expected_quick_recovery_rows"] == 4
    assert prereg["measurement_a"]["truth_definitions"]["truth_persist_steps"] == 2
    assert "max_abs_tire_longitudinal_slip" in prereg["measurement_a"]["truth_definitions"]["long"]
    assert prereg["measurement_c"]["recovery_definition"]["stable_run_steps"] == 10


def test_truth_signal_uses_frozen_axis_specific_tire_diagnostics() -> None:
    info = {
        "max_abs_tire_longitudinal_slip": 0.31,
        "max_abs_tire_slip_angle_rad": 0.07,
    }

    assert full_e3._truth_signal("long", info) == 0.31
    assert full_e3._truth_signal("lat", info) == 0.07


def _latency_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": "A_long",
            "axis": "long",
            "truth_onset_step": "20",
            "detector_fired_step": "35",
            "latency_steps": "15",
            "missed_detection": "False",
            "early_fire": "False",
            "reset_obs_finite": "True",
            "runtime_obs_finite_all": "True",
            "variant_match": "True",
            "telemetry_available_all": "True",
            "wheel_count_all_four": "True",
        },
        {
            "case_id": "A_lat",
            "axis": "lat",
            "truth_onset_step": "50",
            "detector_fired_step": "70",
            "latency_steps": "20",
            "missed_detection": "False",
            "early_fire": "False",
            "reset_obs_finite": "True",
            "runtime_obs_finite_all": "True",
            "variant_match": "True",
            "telemetry_available_all": "True",
            "wheel_count_all_four": "True",
        },
    ]


def _recovery_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for overshoot in ("1.05", "1.15"):
        for driver, recovered in (("baseline_coast", "False"), ("v4_incumbent", "True")):
            rows.append(
                {
                    "case_id": f"C_{overshoot}_{driver}",
                    "overshoot": overshoot,
                    "driver": driver,
                    "recovered": recovered,
                    "reset_obs_finite": "True",
                    "runtime_obs_finite_all": "True",
                    "variant_match": "True",
                    "telemetry_available_all": "True",
                    "wheel_count_all_four": "True",
                }
            )
    return rows


def test_summarize_quick_panel_separates_protocol_completion_from_track_f_admission() -> None:
    prereg = full_e3.build_preregistration()

    summary = full_e3.summarize_panel(
        _latency_rows(),
        _recovery_rows(),
        prereg,
        mode="quick",
        elapsed_s=1.0,
        latency_path=full_e3.LATENCY_ROWS_QUICK_CSV,
        recovery_path=full_e3.RECOVERY_ROWS_QUICK_CSV,
        metrics_path=full_e3.METRICS_QUICK_CSV,
    )

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["quick_protocol_verdict"] == "full_e3_protocol_smoke_passed"
    assert summary["decision"]["full_e3_verdict"] == "not_decided_by_quick_mode"
    assert summary["decision"]["cp3_evidence_ready"] is False
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["measurement_a_summary"]["detector_miss_rate"] == 0.0
    assert summary["measurement_c_summary"]["v4_recovery_rate"] == 1.0
    assert summary["measurement_c_summary"]["baseline_recovery_rate"] == 0.0


def test_summarize_quick_panel_fails_protocol_when_truth_onset_missing() -> None:
    prereg = full_e3.build_preregistration()
    rows = _latency_rows()
    rows[0]["truth_onset_step"] = "-1"

    summary = full_e3.summarize_panel(
        rows,
        _recovery_rows(),
        prereg,
        mode="quick",
        elapsed_s=1.0,
        latency_path=full_e3.LATENCY_ROWS_QUICK_CSV,
        recovery_path=full_e3.RECOVERY_ROWS_QUICK_CSV,
        metrics_path=full_e3.METRICS_QUICK_CSV,
    )

    assert summary["protocol_gates"]["measurement_a_truth_onsets_observed"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["quick_protocol_verdict"] == "full_e3_protocol_smoke_failed"
    assert summary["decision"]["full_e3_verdict"] == "not_decided_by_quick_mode"
