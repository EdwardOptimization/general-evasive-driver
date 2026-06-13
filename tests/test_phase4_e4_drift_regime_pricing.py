from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e4_drift_regime_pricing as e4  # noqa: E402


def _base_row(
    *,
    role: str,
    cell_id: str,
    seed: int,
    validation_unit: int | str,
    arm: str,
    candidate: str,
    success: bool,
    score: float,
    failure_mode: str = "controlled_drift",
) -> dict[str, str]:
    return {
        "mode": "full",
        "role": role,
        "cell_id": cell_id,
        "seed": str(seed),
        "validation_unit": str(validation_unit),
        "variant": e4.VARIANT,
        "arm": arm,
        "candidate": candidate,
        "selected_candidate": candidate,
        "steps": "90",
        "drift_success": str(bool(success)),
        "score": str(float(score)),
        "failure_mode": failure_mode,
        "first_failure_reason": "",
        "high_sideslip_steps": "60",
        "rear_saturation_steps": "65",
        "controlled_drift_steps": "50",
        "longest_controlled_drift_run": "30",
        "max_abs_beta_rad": "0.22",
        "max_abs_yaw_rate_rad_s": "0.6",
        "max_rear_slip_angle_rad": "0.14",
        "max_rear_longitudinal_slip": "0.1",
        "telemetry_samples": "90",
        "rear_telemetry_samples": "90",
        "reset_obs_finite": "True",
        "finite_obs_all": "True",
        "variant_match": "True",
        "termination_reason": "",
        "completion_reason": "max_steps",
        "backend_model": "Sedan",
        "backend_tire": "TMeasy",
        "trace_signature": "fake",
        "claim_boundary": e4.CLAIM_BOUNDARY,
    }


def _passing_rows(prereg: dict) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for cell in prereg["cells"]:
        cell_id = cell["cell_id"]
        for idx, seed in enumerate(prereg["selection_seeds"][cell_id]):
            rows.append(
                _base_row(
                    role="selection",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit="",
                    arm="per_instance_tuned_reflex",
                    candidate="reflex:v4_gain1p0_speed7_betadamp0",
                    success=True,
                    score=100.0,
                )
            )
            rows.append(
                _base_row(
                    role="selection",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit="",
                    arm="native_chrono_oracle",
                    candidate="native:structured_countersteer_hold",
                    success=True,
                    score=120.0,
                )
            )
            rows.append(
                _base_row(
                    role="selection",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit="",
                    arm="drift_specialized_oracle",
                    candidate="drift:beta0p16_balanced",
                    success=True,
                    score=130.0,
                )
            )
        for unit, seed in enumerate(prereg["validation_seeds"][cell_id]):
            rows.append(
                _base_row(
                    role="validation",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit=unit,
                    arm="fixed_star",
                    candidate="fixed_star",
                    success=False,
                    score=20.0,
                    failure_mode="fail_to_enter",
                )
            )
            rows.append(
                _base_row(
                    role="validation",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit=unit,
                    arm="per_instance_tuned_reflex",
                    candidate="reflex:v4_gain1p0_speed7_betadamp0",
                    success=(unit % 5 == 0),
                    score=40.0,
                    failure_mode="fail_to_stabilize",
                )
            )
            rows.append(
                _base_row(
                    role="validation",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit=unit,
                    arm="native_chrono_oracle",
                    candidate="native:structured_countersteer_hold",
                    success=(unit % 2 == 0),
                    score=90.0,
                )
            )
            rows.append(
                _base_row(
                    role="validation",
                    cell_id=cell_id,
                    seed=seed,
                    validation_unit=unit,
                    arm="drift_specialized_oracle",
                    candidate="drift:beta0p16_balanced",
                    success=True,
                    score=140.0,
                )
            )
    return rows


def test_preregistration_freezes_e4_cells_and_disjoint_seed_streams() -> None:
    prereg = e4.build_preregistration()

    assert prereg["frozen_before_any_e4_drift_pricing_run"] is True
    assert prereg["chrono_vehicle_variant"] == "sedan_tmeasy"
    assert prereg["min_validation_units_per_cell"] == 20
    assert prereg["quick_mode_is_verdict"] is False
    assert prereg["arms"]["oracle"].startswith("per validation unit max")

    for cell in prereg["cells"]:
        cell_id = cell["cell_id"]
        assert len(prereg["validation_seeds"][cell_id]) == 20
        assert set(prereg["selection_seeds"][cell_id]).isdisjoint(prereg["validation_seeds"][cell_id])


def test_summarize_full_reports_paired_oracle_gaps_and_blocks_track_f() -> None:
    prereg = e4.build_preregistration()
    rows = _passing_rows(prereg)

    summary = e4.summarize(rows, prereg, quick=False, elapsed_s=1.0)

    assert summary["protocol_gates"]["all_passed"] is True
    assert summary["decision"]["e4_verdict"] == "drift_pricing_completed"
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["decision"]["f2_training_admitted"] is False
    assert summary["validation_row_count"] == len(prereg["cells"]) * 20 * 4
    for readout in summary["cell_readouts"]:
        assert readout["validation_units"] == 20
        assert readout["oracle_minus_fixed_star"]["mean"] == 1.0
        assert readout["oracle_minus_per_instance_tuned_reflex"]["n_pairs"] == 20
        assert readout["reflex_failure_modes"]["fail_to_enter"] == 20


def test_summarize_full_fails_when_selection_oracle_adequacy_is_missing() -> None:
    prereg = e4.build_preregistration()
    rows = _passing_rows(prereg)
    for row in rows:
        if row["role"] == "selection" and row["arm"] in {"native_chrono_oracle", "drift_specialized_oracle"}:
            row["score"] = "1.0"

    summary = e4.summarize(rows, prereg, quick=False, elapsed_s=1.0)

    assert summary["protocol_gates"]["oracle_adequacy_gate_passed"] is False
    assert summary["protocol_gates"]["all_passed"] is False
    assert summary["decision"]["e4_verdict"] == "drift_pricing_protocol_failed"


def test_quick_smoke_decision_never_admits_track_f_or_f2() -> None:
    summary = {
        "protocol_gates": {"all_passed": True},
        "decision": {
            "e4_verdict": "drift_pricing_completed",
            "track_f_admitted": True,
            "f2_training_admitted": True,
            "next_admitted_step": "bad",
        },
    }

    e4.apply_quick_smoke_decision(summary)

    assert summary["quick_mode_is_verdict"] is False
    assert summary["decision"]["e4_verdict"] == "quick_smoke_passed"
    assert summary["decision"]["track_f_admitted"] is False
    assert summary["decision"]["f2_training_admitted"] is False
