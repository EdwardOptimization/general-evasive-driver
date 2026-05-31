from __future__ import annotations

import csv
from pathlib import Path

from autodrift.bounded_diagnostic_comparison import (
    filter_candidate_rows,
    run_bounded_diagnostic_comparison,
)


def _candidate() -> dict[str, object]:
    return {
        "candidate_key": "success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible",
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": "stable_aes_only",
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
    }


def _episode(profile_name: str, outcome_bucket: str) -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": "stable_aes_only",
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "outcome_bucket": outcome_bucket,
        "termination_reason": "" if outcome_bucket == "success_obstacle_pass" else "off_track",
        "min_clearance_margin": 1.0 if outcome_bucket == "success_obstacle_pass" else -0.5,
        "return": 10.0 if outcome_bucket == "success_obstacle_pass" else -1.0,
        "steps": 30,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_filter_candidate_rows_matches_all_key_fields() -> None:
    rows = [_episode("L0_current_masked", "success_obstacle_pass")]
    wrong = dict(rows[0])
    wrong["sampled_obstacle_label"] = "unavoidable"
    matched = filter_candidate_rows([rows[0], wrong], _candidate())
    assert matched == [rows[0]]


def test_run_bounded_diagnostic_comparison_writes_profile_and_group_tables(tmp_path: Path) -> None:
    admitted_path = tmp_path / "admitted.csv"
    episode_rows_path = tmp_path / "episode_rows.csv"
    output_dir = tmp_path / "out"
    _write_csv(admitted_path, [_candidate()])
    _write_csv(
        episode_rows_path,
        [
            _episode("L0_current_masked", "success_obstacle_pass"),
            _episode("L0_current_masked", "off_track_noncollision_noncompletion"),
            _episode("L3_online_gru", "success_obstacle_pass"),
        ],
    )

    summary = run_bounded_diagnostic_comparison(
        admitted_candidates_path=admitted_path,
        episode_rows_path=episode_rows_path,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "bounded_diagnostic_comparison_pass"
    assert summary["matched_episode_count"] == 3
    assert summary["profile_row_count"] == 2
    assert summary["profile_group_row_count"] == 2
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "profile_comparison.csv").exists()
    assert (output_dir / "profile_group_comparison.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
