from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration as m2680


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _episode(
    *,
    profile_name: str,
    task_source_id: str,
    task_family: str,
    outcome_bucket: str,
    termination_reason: str,
) -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "task_source_id": task_source_id,
        "task_family": task_family,
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "min_clearance_margin": 1.0,
        "return": 2.0,
        "steps": 10,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
    }


def test_m2680_dominance_and_comparison_rows_keep_nonverdict_boundary() -> None:
    rows = [
        _episode(
            profile_name="L0_current_masked",
            task_source_id="spec_a",
            task_family="T4",
            outcome_bucket="off_track_noncollision_noncompletion",
            termination_reason="off_track",
        )
        for _ in range(10)
    ]
    rows.append(
        _episode(
            profile_name="L0_current_masked",
            task_source_id="spec_a",
            task_family="T4",
            outcome_bucket="success_obstacle_pass",
            termination_reason="",
        )
    )

    dominance_rows = m2680.build_dominance_rows(rows, ("task_source_id",), slice_kind="spec")
    assert len(dominance_rows) == 1
    row = dominance_rows[0]
    assert row["dominant_outcome"] == "off_track_noncollision_noncompletion"
    assert row["outcome_dominance_blocked"] is True
    assert row["task_quality_blocked"] is True
    assert row["hidden_dynamics_bucket_present"] is False
    assert row["interpretable_for_history_comparison"] is False

    comparison_rows = m2680.build_comparison_interpretability_rows(
        comparison_rows=[
            {
                "comparison": "L3_online_minus_L3_reset_control",
                "left_group": "L3_online_gru",
                "right_group": "L3_reset_control_corrected",
                "left_episode_count": 72,
                "right_episode_count": 72,
                "success_rate_delta": -0.1,
                "collision_rate_delta": 0.2,
                "clearance_margin_mean_delta": -0.5,
                "return_mean_delta": 1.0,
                "diagnostic_only_no_ranking_claim": True,
            }
        ],
        global_offtrack_blocked=True,
        hidden_dynamics_missing=True,
    )
    assert comparison_rows[0]["blocked_by_reset_control"] is True
    assert comparison_rows[0]["blocked_by_mixed_metrics"] is True
    assert comparison_rows[0]["blocked_by_outcome_dominance"] is True
    assert comparison_rows[0]["interpretable_for_ranking"] is False
    assert comparison_rows[0]["allowed_for_synthesis_only"] is True


def test_m2680_materializer_writes_required_artifacts_from_existing_rows(tmp_path: Path) -> None:
    m2677_dir = tmp_path / "m2677"
    out_dir = tmp_path / "out"
    doc_path = tmp_path / "m2680.md"
    follow_up_manifest = tmp_path / "m2681.json"
    m2677_dir.mkdir()
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    profiles = [f"profile_{index:02d}" for index in range(m2680.TARGET_PROFILE_COUNT)]
    specs = [f"spec_{index:02d}" for index in range(m2680.TARGET_SPEC_COUNT)]
    episode_rows = []
    for profile_index, profile_name in enumerate(profiles):
        for spec_index, spec in enumerate(specs):
            success = spec_index % 24 == 0 and profile_index == 0
            collision = spec_index % 24 == 1 and profile_index == 1
            if success:
                outcome = "success_obstacle_pass"
                termination = ""
            elif collision:
                outcome = "collision_failure"
                termination = "obstacle_collision"
            else:
                outcome = "off_track_noncollision_noncompletion"
                termination = "off_track"
            episode_rows.append(
                _episode(
                    profile_name=profile_name,
                    task_source_id=spec,
                    task_family="T4" if spec_index < 36 else "T5",
                    outcome_bucket=outcome,
                    termination_reason=termination,
                )
            )

    write_json(m2677_dir / "summary.json", {"status_pass": True})
    write_csv_rows(m2677_dir / "episode_rows.csv", episode_rows)
    write_csv_rows(
        m2677_dir / "profile_aggregate.csv",
        [
            {"profile_name": "L3_reset_control_corrected", "success_rate": 0.26},
            {"profile_name": "L3_online_gru", "success_rate": 0.19},
        ],
    )
    write_csv_rows(m2677_dir / "spec_aggregate.csv", [{"task_source_id": spec} for spec in specs])
    write_csv_rows(
        m2677_dir / "comparison_aggregate.csv",
        [
            {
                "comparison": f"L2_window_{index}_normal_minus_current_tiled",
                "left_group": f"L2_window_{index}",
                "right_group": f"L2_window_{index}_current_tiled",
                "left_episode_count": 72,
                "right_episode_count": 72,
                "success_rate_delta": 0.0,
                "collision_rate_delta": 0.0,
                "clearance_margin_mean_delta": 1.0,
                "return_mean_delta": -1.0,
                "diagnostic_only_no_ranking_claim": True,
            }
            for index in range(m2680.TARGET_COMPARISON_COUNT)
        ],
    )
    for name in [
        "outcome_aggregate",
        "termination_reason_aggregate",
        "profile_outcome_aggregate",
        "hidden_dynamics_aggregate",
        "profile_hidden_dynamics_worst_bucket",
        "runtime_enforcement_join_rows",
        "claim_boundary_rows",
        "gate_matrix",
    ]:
        write_csv_rows(m2677_dir / f"{name}.csv", [])

    summary = m2680.materialize_task_quality_outcome_dominance_calibration(
        m2677_dir=m2677_dir,
        output_dir=out_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration_pass"
    )
    assert summary["episode_count"] == 864
    assert summary["spec_outcome_dominance_row_count"] == 72
    assert summary["profile_outcome_dominance_row_count"] == 12
    assert summary["task_family_outcome_dominance_row_count"] == 2
    assert summary["comparison_interpretability_row_count"] == 11
    assert summary["calibration_gap_row_count"] >= 8
    assert summary["global_outcome_dominance_blocked"] is True
    assert summary["hidden_dynamics_bucket_missing"] is True
    assert summary["comparison_ranking_interpretable_count"] == 0
    assert summary["controller_family_ranking_claim_made"] is False
    assert summary["paper_level_claim_made"] is False
    assert read_json(out_dir / "summary.json") == summary
    assert doc_path.read_text(encoding="utf-8").strip()

    spec_rows = _read_csv(out_dir / "spec_outcome_dominance_rows.csv")
    comparison_rows = _read_csv(out_dir / "comparison_interpretability_rows.csv")
    claim_rows = _read_csv(out_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(out_dir / "gate_matrix.csv")
    assert len(spec_rows) == 72
    assert {row["interpretable_for_ranking"] for row in comparison_rows} == {"False"}
    assert {row["allowed_in_m2680"] for row in claim_rows if row["claim_id"] == "paper_level_evidence"} == {
        "False"
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}
