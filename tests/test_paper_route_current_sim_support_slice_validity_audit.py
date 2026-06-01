from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_support_slice_validity_audit as audit
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _group(
    *,
    group_key: str,
    group_value: str,
    support_label: str,
    episode_count: int = 96,
    success_count: int = 40,
    collision_count: int = 0,
    offtrack_count: int = 56,
    profile_count: int = 8,
    history_representation_count: int = 4,
    task_source_count: int = 24,
) -> dict[str, object]:
    return {
        "group_key": group_key,
        "group_value": group_value,
        "episode_count": episode_count,
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_count": offtrack_count,
        "success_rate": success_count / episode_count,
        "collision_rate": collision_count / episode_count,
        "offtrack_rate": offtrack_count / episode_count,
        "profile_count": profile_count,
        "history_representation_count": history_representation_count,
        "task_source_count": task_source_count,
        "support_label": support_label,
        "comparison_ready_candidate": support_label == "comparison_ready_candidate",
        "controller_family_ranking_claim_made": False,
    }


def _episode(row_id: int) -> dict[str, object]:
    return {"episode_id": row_id, "outcome_bucket": "success_obstacle_pass", "success": True}


def test_support_slice_validity_audit_classifies_without_ranking(tmp_path: Path) -> None:
    group_support = tmp_path / "group_outcome_support.csv"
    summary = tmp_path / "summary.json"
    episode_rows = tmp_path / "episode_rows.csv"
    rows = [
        _group(group_key="task_family", group_value="task_family=T1", support_label="candidate_support"),
        _group(
            group_key="task_family x history_representation",
            group_value="task_family=T1|history_representation=explicit_finite_window",
            support_label="comparison_ready_candidate",
            history_representation_count=1,
        ),
        _group(
            group_key="task_family x profile_name",
            group_value="task_family=T1|profile_name=L2_window_25",
            support_label="comparison_ready_candidate",
            profile_count=1,
            history_representation_count=1,
        ),
        _group(
            group_key="overall",
            group_value="overall",
            support_label="offtrack_dominated",
            episode_count=128,
            success_count=4,
            offtrack_count=124,
        ),
        _group(
            group_key="task_family",
            group_value="task_family=tiny",
            support_label="candidate_support",
            episode_count=24,
            success_count=12,
            offtrack_count=12,
            task_source_count=4,
        ),
    ]
    write_csv_rows(group_support, rows)
    write_json(summary, {"result_class": "current_sim_offtrack_support_outcome_localization_pass", "input_episode_count": 128})
    write_csv_rows(episode_rows, [_episode(i) for i in range(128)])

    result = audit.run_validity_audit(
        group_support=group_support,
        summary=summary,
        episode_rows=episode_rows,
        output_dir=tmp_path / "out",
    )

    assert result["result_class"] == "current_sim_support_slice_validity_audit_pass"
    assert result["scene_backed_candidate_count"] == 1
    assert result["history_family_diagnostic_count"] == 1
    assert result["profile_only_candidate_count"] == 1
    assert result["denominator_imbalanced_count"] == 1
    assert result["global_or_scene_blocker_count"] == 1
    assert result["ranking_admissible_count"] == 0
    assert result["guardrail_violation_count"] == 0
    assert (tmp_path / "out" / "slice_validity.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["policy_action_executed"] is False


def test_validity_classifier_keeps_profile_candidates_out_of_ranking() -> None:
    row = _group(
        group_key="profile_name",
        group_value="profile_name=L2_window_25",
        support_label="comparison_ready_candidate",
        profile_count=1,
        history_representation_count=1,
        task_source_count=288,
        episode_count=288,
    )

    classified = audit.classify_validity(row)

    assert classified["validity_label"] == "profile_only_candidate"
    assert classified["contains_profile_axis"] is True
    assert classified["ranking_admissible"] is False
