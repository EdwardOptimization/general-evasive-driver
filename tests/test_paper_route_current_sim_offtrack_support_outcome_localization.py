from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_offtrack_support_outcome_localization as localization
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    *,
    task_family: str,
    source_family_template: str,
    capability_pair: str,
    profile_name: str,
    history_representation: str,
    outcome_bucket: str,
) -> dict[str, object]:
    return {
        "task_source_id": f"{task_family}-{source_family_template}",
        "task_family": task_family,
        "source_family_template": source_family_template,
        "capability_pair": capability_pair,
        "profile_name": profile_name,
        "profile_level": profile_name.split("_", maxsplit=1)[0],
        "history_representation": history_representation,
        "outcome_bucket": outcome_bucket,
        "success": outcome_bucket == "success_obstacle_pass",
        "collision": outcome_bucket == "collision_failure",
        "termination_reason": "off_track" if outcome_bucket == "off_track_noncollision_noncompletion" else "",
    }


def test_outcome_localization_labels_support_slices_without_ranking(tmp_path: Path) -> None:
    episode_rows = tmp_path / "episode_rows.csv"
    summary = tmp_path / "summary.json"
    rows = []
    for _ in range(64):
        rows.append(
            _episode(
                task_family="T1",
                source_family_template="stable",
                capability_pair="reactive",
                profile_name="L0_current_masked",
                history_representation="current_response",
                outcome_bucket="success_obstacle_pass",
            )
        )
    for _ in range(16):
        rows.append(
            _episode(
                task_family="T1",
                source_family_template="stable",
                capability_pair="reactive",
                profile_name="L1_one_step",
                history_representation="one_step_command_response",
                outcome_bucket="off_track_noncollision_noncompletion",
            )
        )
    for _ in range(64):
        rows.append(
            _episode(
                task_family="T5",
                source_family_template="boundary",
                capability_pair="terminal",
                profile_name="L3_online_gru",
                history_representation="online_recurrent_hidden",
                outcome_bucket="off_track_noncollision_noncompletion",
            )
        )
    write_csv_rows(episode_rows, rows)
    write_json(summary, {"result_class": "current_sim_controlled_comparison_measured_execution_pass", "episode_count": len(rows)})

    result = localization.run_outcome_localization(
        episode_rows=episode_rows,
        summary=summary,
        output_dir=tmp_path / "out",
    )

    assert result["result_class"] == "current_sim_offtrack_support_outcome_localization_pass"
    assert result["input_episode_count"] == len(rows)
    assert result["guardrail_violation_count"] == 0
    assert result["controller_family_ranking_claim_made"] is False
    assert result["comparison_ready_candidate_count"] >= 1
    assert result["offtrack_dominated_count"] >= 1
    assert (tmp_path / "out" / "group_outcome_support.csv").exists()
    assert (tmp_path / "out" / "claim_boundary.csv").exists()
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["policy_action_executed"] is False


def test_support_label_rules_are_deterministic() -> None:
    assert (
        localization.support_label(episode_count=64, success_count=24, collision_count=0, offtrack_count=10)
        == "comparison_ready_candidate"
    )
    assert localization.support_label(episode_count=64, success_count=8, collision_count=0, offtrack_count=40) == "candidate_support"
    assert localization.support_label(episode_count=64, success_count=1, collision_count=0, offtrack_count=60) == "offtrack_dominated"
    assert localization.support_label(episode_count=64, success_count=1, collision_count=20, offtrack_count=0) == "collision_dominated"
    assert localization.support_label(episode_count=8, success_count=8, collision_count=0, offtrack_count=0) == "low_sample_count"
