from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_bounded_diagnostic_comparison as diagnostic
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    task_family: str,
    profile_name: str,
    history_representation: str,
    outcome_bucket: str,
) -> dict[str, object]:
    return {
        "task_family": task_family,
        "source_family_template": "template",
        "capability_pair": "capability",
        "profile_name": profile_name,
        "history_representation": history_representation,
        "outcome_bucket": outcome_bucket,
        "success": outcome_bucket == "success_obstacle_pass",
        "collision": outcome_bucket == "collision_failure",
        "termination_reason": "off_track" if outcome_bucket == "off_track_noncollision_noncompletion" else "",
    }


def _candidate(group_value: str) -> dict[str, object]:
    return {
        "group_key": "task_family",
        "group_value": group_value,
        "support_label": "candidate_support",
        "validity_label": "scene_backed_candidate",
        "episode_count": 64,
        "success_count": 32,
        "collision_count": 0,
        "offtrack_count": 32,
    }


def test_bounded_diagnostic_comparison_writes_diagnostic_matrices(tmp_path: Path) -> None:
    episode_rows = tmp_path / "episode_rows.csv"
    scene_candidates = tmp_path / "scene_backed_candidates.csv"
    validity_summary = tmp_path / "validity_summary.json"
    rows = []
    for _ in range(16):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L0_current_masked",
                history_representation="current_response",
                outcome_bucket="success_obstacle_pass",
            )
        )
    for _ in range(16):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L2_window_25",
                history_representation="explicit_finite_window",
                outcome_bucket="success_obstacle_pass",
            )
        )
    for _ in range(32):
        rows.append(
            _episode(
                task_family="T1",
                profile_name="L3_online_gru",
                history_representation="online_recurrent_hidden",
                outcome_bucket="off_track_noncollision_noncompletion",
            )
        )
    write_csv_rows(episode_rows, rows)
    write_csv_rows(scene_candidates, [_candidate("task_family=T1")])
    write_json(validity_summary, {"result_class": "current_sim_support_slice_validity_audit_pass", "scene_backed_candidate_count": 1})

    result = diagnostic.run_bounded_diagnostic_comparison(
        episode_rows=episode_rows,
        scene_backed_candidates=scene_candidates,
        validity_summary=validity_summary,
        output_dir=tmp_path / "out",
    )

    assert result["result_class"] == "current_sim_bounded_diagnostic_comparison_pass"
    assert result["scene_candidate_count"] == 1
    assert result["multi_profile_diagnostic_support_count"] == 1
    assert result["ranking_admissible_count"] == 0
    assert result["winner_selected"] is False
    assert (tmp_path / "out" / "scene_candidate_profile_matrix.csv").exists()
    assert (tmp_path / "out" / "scene_candidate_history_matrix.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["policy_action_executed"] is False


def test_group_filter_parser_matches_key_values() -> None:
    filters = diagnostic.parse_group_filter("task_family=T1|capability_pair=reactive")

    assert filters == {"task_family": "T1", "capability_pair": "reactive"}
    assert diagnostic._matches({"task_family": "T1", "capability_pair": "reactive"}, filters)
    assert not diagnostic._matches({"task_family": "T2", "capability_pair": "reactive"}, filters)
