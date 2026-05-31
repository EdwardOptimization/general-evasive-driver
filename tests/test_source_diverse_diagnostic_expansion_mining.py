from __future__ import annotations

import csv
from pathlib import Path

from autodrift.source_diverse_diagnostic_expansion_mining import mine_expansion_candidates, run_mining


def _episode(
    profile_name: str,
    outcome_bucket: str,
    *,
    candidate_source_id: str = "source_a",
    role: str = "stable_aes_only",
) -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "candidate_source_id": candidate_source_id,
        "task_source_id": f"task_{candidate_source_id}",
        "base_geometry_source": f"geometry_{candidate_source_id}",
        "repair_candidate_id": f"repair_{candidate_source_id}",
        "outcome_bucket": outcome_bucket,
    }


def _diag(profile_name: str, *, role: str = "stable_aes_only") -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "repair_source_kind": "success_stabilizer",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "normalized_surface_variant": "post_friction_step",
        "sampled_obstacle_label": "aes_feasible",
        "same_slice_non_l2_success_l2_zero_pattern": "True",
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_mine_expansion_candidates_requires_l2_zero_and_non_l2_success() -> None:
    rows = [
        _episode("L2_window_25", "off_track_noncollision_noncompletion", candidate_source_id="a"),
        _episode("L2_window_50", "off_track_noncollision_noncompletion", candidate_source_id="b"),
        _episode("L0_current_masked", "success_obstacle_pass", candidate_source_id="a"),
        _episode("L3_online_gru", "success_obstacle_pass", candidate_source_id="b"),
    ]
    candidates = mine_expansion_candidates(diagnostic_rows=[_diag("L2_window_25")], episode_rows=rows)
    assert len(candidates) == 1
    assert candidates[0]["l2_success_count"] == 0
    assert candidates[0]["non_l2_success_count"] == 2
    assert candidates[0]["source_diverse_candidate"] is True
    assert candidates[0]["admitted_for_expansion"] is True


def test_mine_expansion_candidates_rejects_l2_success() -> None:
    rows = [
        _episode("L2_window_25", "success_obstacle_pass", candidate_source_id="a"),
        _episode("L0_current_masked", "success_obstacle_pass", candidate_source_id="a"),
    ]
    assert mine_expansion_candidates(diagnostic_rows=[_diag("L2_window_25")], episode_rows=rows) == []


def test_run_mining_writes_candidate_and_summary_outputs(tmp_path: Path) -> None:
    diagnostic_path = tmp_path / "l2.csv"
    episode_path = tmp_path / "episodes.csv"
    output_dir = tmp_path / "out"
    _write_csv(diagnostic_path, [_diag("L2_window_25")])
    _write_csv(
        episode_path,
        [
            _episode("L2_window_25", "off_track_noncollision_noncompletion", candidate_source_id="a"),
            _episode("L2_window_50", "off_track_noncollision_noncompletion", candidate_source_id="b"),
            _episode("L0_current_masked", "success_obstacle_pass", candidate_source_id="a"),
            _episode("L3_online_gru", "success_obstacle_pass", candidate_source_id="b"),
        ],
    )
    summary = run_mining(l2_diagnostic_path=diagnostic_path, episode_rows_path=episode_path, output_dir=output_dir)
    assert summary["result_class"] == "source_diverse_diagnostic_expansion_mining_pass"
    assert summary["candidate_count"] == 1
    assert summary["admitted_candidate_count"] == 1
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "diagnostic_expansion_candidates.csv").exists()
    assert (output_dir / "source_diversity_summary.csv").exists()
