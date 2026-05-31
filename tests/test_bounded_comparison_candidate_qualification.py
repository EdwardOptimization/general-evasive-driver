from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_json
from autodrift.bounded_comparison_candidate_qualification import (
    QUALIFICATION_FIELDNAMES,
    QualificationThresholds,
    qualify_candidate,
    run_qualification,
)


def _candidate(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": "stable_aes_only",
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "episode_count": 60,
        "success_count": 17,
        "collision_count": 2,
        "offtrack_outcome_count": 41,
        "success_rate": 0.2833333333,
        "collision_rate": 0.0333333333,
        "offtrack_outcome_rate": 0.6833333333,
        "nonzero_success_profile_count": 4,
        "profiles_with_success": "L0_current_masked;L1_one_step;L3_online_gru;L3_reset_control_corrected",
        "support_label": "comparison_ready_candidate",
    }
    row.update(overrides)
    return row


def test_qualify_candidate_admits_bounded_diagnostic_candidate() -> None:
    qualified = qualify_candidate(
        _candidate(),
        thresholds=QualificationThresholds(),
        l2_total_success_count=0,
    )
    assert qualified["admitted_for_bounded_comparison"] is True
    assert qualified["admitted_scope"] == "bounded_diagnostic_comparison_not_finite_window_vs_gru"
    assert qualified["success_profile_groups"] == "L0;L1;L3"
    assert qualified["l2_success_present"] is False
    assert qualified["rejection_reasons"] == ""


def test_qualify_candidate_rejects_collision_dominated_support() -> None:
    qualified = qualify_candidate(
        _candidate(
            support_label="candidate_support",
            collision_count=19,
            collision_rate=0.7916666667,
            offtrack_outcome_count=0,
            offtrack_outcome_rate=0.0,
        ),
        thresholds=QualificationThresholds(),
        l2_total_success_count=0,
    )
    assert qualified["admitted_for_bounded_comparison"] is False
    assert "source_label_not_comparison_ready_candidate" in qualified["rejection_reasons"]
    assert "collision_rate_above_threshold" in qualified["rejection_reasons"]


def test_run_qualification_writes_admitted_and_rejected_rows(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    candidates_path = tmp_path / "comparison_support_candidates.csv"
    output_dir = tmp_path / "out"
    write_json(summary_path, {"l2_total_success_count": 0})
    rows = [
        _candidate(),
        _candidate(
            source_role_semantics="drift_required_recovery",
            parent_feasibility_tier_id="tier_e_mitigation_only",
            sampled_obstacle_label="drift_required",
            episode_count=24,
            success_count=5,
            collision_count=19,
            offtrack_outcome_count=0,
            success_rate=0.2083333333,
            collision_rate=0.7916666667,
            offtrack_outcome_rate=0.0,
            support_label="candidate_support",
        ),
    ]
    with candidates_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary = run_qualification(
        summary_path=summary_path,
        candidates_path=candidates_path,
        output_dir=output_dir,
        thresholds=QualificationThresholds(),
    )

    assert summary["result_class"] == "bounded_comparison_candidate_qualification_pass"
    assert summary["source_candidate_count"] == 2
    assert summary["admitted_candidate_count"] == 1
    assert summary["rejected_candidate_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "candidate_qualification_rows.csv").exists()

    with (output_dir / "candidate_qualification_rows.csv").open(newline="", encoding="utf-8") as handle:
        output_rows = list(csv.DictReader(handle))
    assert len(output_rows) == 2
    assert set(output_rows[0]) == set(QUALIFICATION_FIELDNAMES)
