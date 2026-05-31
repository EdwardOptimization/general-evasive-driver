from __future__ import annotations

import csv
from pathlib import Path

from autodrift.multi_slice_bounded_diagnostic_comparison import run_multi_slice_comparison


def _candidate(role: str) -> dict[str, object]:
    return {
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
    }


def _episode(role: str, profile_name: str, outcome_bucket: str) -> dict[str, object]:
    return {
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "profile_name": profile_name,
        "outcome_bucket": outcome_bucket,
        "termination_reason": "" if outcome_bucket == "success_obstacle_pass" else "off_track",
        "min_clearance_margin": 1.0,
        "return": 1.0,
        "steps": 10,
        "action_rate_mean": 0.0,
        "high_sideslip_fraction": 0.0,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_run_multi_slice_comparison_writes_candidate_and_aggregate_tables(tmp_path: Path) -> None:
    admitted_path = tmp_path / "admitted.csv"
    episode_path = tmp_path / "episode_rows.csv"
    output_dir = tmp_path / "out"
    _write_csv(admitted_path, [_candidate("stable_aes_only"), _candidate("stable_aeb")])
    _write_csv(
        episode_path,
        [
            _episode("stable_aes_only", "L0_current_masked", "success_obstacle_pass"),
            _episode("stable_aes_only", "L2_window_25", "off_track_noncollision_noncompletion"),
            _episode("stable_aeb", "L1_one_step", "success_obstacle_pass"),
            _episode("stable_aeb", "L3_online_gru", "success_obstacle_pass"),
        ],
    )

    summary = run_multi_slice_comparison(
        admitted_candidates_path=admitted_path,
        episode_rows_path=episode_path,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "multi_slice_bounded_diagnostic_comparison_pass"
    assert summary["candidate_count"] == 2
    assert summary["matched_episode_count"] == 4
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "candidate_profile_group_comparison.csv").exists()
    assert (output_dir / "aggregate_profile_group_comparison.csv").exists()
    assert (output_dir / "candidate_support.csv").exists()
