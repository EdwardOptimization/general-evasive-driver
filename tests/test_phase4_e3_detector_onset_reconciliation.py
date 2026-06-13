from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "feasibility_audit"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase4_e3_detector_onset_reconciliation as recon  # noqa: E402


def test_preregistration_freezes_m3257_counts_and_definition() -> None:
    prereg = recon.build_preregistration()

    assert prereg["frozen_before_any_m3257_rollout"] is True
    assert prereg["expected_full_case_rows"] == 24
    assert prereg["expected_quick_case_rows"] == 2
    assert prereg["onset_definitions"]["reconciled_actor_visible_onset"]["corroboration_max_lead_steps"] == 150
    assert "m3255_original_early_fire_rate" in prereg["baseline_anomaly"]


def test_reconcile_onset_promotes_corroborated_early_detector_fire() -> None:
    result = recon.reconcile_onset_steps(original_truth_onset_step=94, detector_fired_step=54)

    assert result["reconciled_onset_step"] == 54
    assert result["reconciled_latency_steps"] == 0
    assert result["reconciled_early_fire"] is False
    assert result["detector_corroborated_by_later_tire_truth"] is True
    assert result["uncorroborated_detector_fire"] is False


def test_reconcile_onset_keeps_late_detector_latency() -> None:
    result = recon.reconcile_onset_steps(original_truth_onset_step=80, detector_fired_step=135)

    assert result["reconciled_onset_step"] == 80
    assert result["reconciled_latency_steps"] == 55
    assert result["reconciled_early_fire"] is False
    assert result["detector_corroborated_by_later_tire_truth"] is False


def test_reconcile_onset_reports_miss_when_detector_never_fires() -> None:
    result = recon.reconcile_onset_steps(original_truth_onset_step=85, detector_fired_step=-1)

    assert result["reconciled_onset_step"] == 85
    assert result["reconciled_latency_steps"] == ""
    assert result["reconciled_missed_detection"] is True
    assert result["reconciliation_label"] == "detector_missed_tire_truth"


def test_reconcile_onset_does_not_promote_uncorroborated_large_lead() -> None:
    result = recon.reconcile_onset_steps(original_truth_onset_step=300, detector_fired_step=10)

    assert result["reconciled_onset_step"] == 300
    assert result["reconciled_latency_steps"] == -290
    assert result["reconciled_early_fire"] is True
    assert result["detector_corroborated_by_later_tire_truth"] is False
    assert result["uncorroborated_detector_fire"] is True
