from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization as m2682


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _episode(
    *,
    profile_name: str,
    task_source_id: str,
    task_family: str,
    source_edge: str,
    outcome_bucket: str,
    termination_reason: str,
) -> dict[str, object]:
    return {
        "profile_name": profile_name,
        "task_source_id": task_source_id,
        "task_family": task_family,
        "source_edge": source_edge,
        "workload_id": f"{task_source_id}::{profile_name}",
        "window_tag": "reveal_plus_4",
        "strata": f"task_family_{task_family}",
        "executable_source_family": source_edge.split("|")[0],
        "env_template_family": f"{task_family.lower()}_template",
        "outcome_bucket": outcome_bucket,
        "termination_reason": termination_reason,
        "profile_env_history_length": 1,
    }


def _write_m2680_sources(m2680_dir: Path) -> None:
    m2680_dir.mkdir()
    write_json(
        m2680_dir / "summary.json",
        {
            "status_pass": True,
            "global_outcome_dominance_blocked": True,
            "hidden_dynamics_bucket_missing": True,
            "comparison_ranking_interpretable_count": 0,
        },
    )
    write_csv_rows(m2680_dir / "spec_outcome_dominance_rows.csv", [{"slice_kind": "spec"}])
    write_csv_rows(m2680_dir / "profile_outcome_dominance_rows.csv", [{"slice_kind": "profile"}])
    write_csv_rows(m2680_dir / "task_family_outcome_dominance_rows.csv", [{"slice_kind": "task_family"}])
    write_csv_rows(
        m2680_dir / "comparison_interpretability_rows.csv",
        [{"comparison": "diagnostic", "interpretable_for_ranking": False}],
    )
    write_csv_rows(
        m2680_dir / "calibration_gap_rows.csv",
        [
            {"gap_id": "global_offtrack_dominance", "blocks_interpretation": True},
            {"gap_id": "role_semantics_missing", "blocks_interpretation": True},
        ],
    )
    write_csv_rows(m2680_dir / "claim_boundary_rows.csv", [{"claim_id": "paper_level_evidence"}])
    write_csv_rows(m2680_dir / "gate_matrix.csv", [{"gate_id": "required_artifacts_present"}])


def test_m2682_materializes_candidate_panel_and_bounded_subset(tmp_path: Path) -> None:
    m2677_dir = tmp_path / "m2677"
    m2680_dir = tmp_path / "m2680"
    out_dir = tmp_path / "out"
    doc_path = tmp_path / "m2682.md"
    follow_up_manifest = tmp_path / "m2683.json"
    m2677_dir.mkdir()
    follow_up_manifest.write_text("{}\n", encoding="utf-8")

    profiles = [f"profile_{index:02d}" for index in range(m2682.TARGET_PROFILE_COUNT)]
    source_edges = [
        "actuator_delay_step|capability_step_up",
        "capability_step_down|t4_actuator_delay_response",
        "t4_actuator_delay_response|actuator_delay_step",
        "t4_actuator_delay_response|capability_step_up",
        "t4_capability_step_temporal|capability_step_down",
        "t4_staged_warmup_capability|capability_step_up",
        "curved_boundary_obstacle|t5_boundary_axis_retarget",
        "actuator_delay_step|t5_near_boundary_warmup",
        "t5_near_boundary_warmup|t5_boundary_axis_retarget",
        "capability_step_down|t5_near_boundary_warmup",
        "brake_fade_or_loss_proxy|late_reveal_boundary",
        "drive_loss_proxy|curved_boundary_obstacle",
    ]
    episode_rows: list[dict[str, object]] = []
    for spec_index in range(m2682.TARGET_SPEC_COUNT):
        task_family = "T4" if spec_index < 36 else "T5"
        source_edge = source_edges[(spec_index // 6) % len(source_edges)]
        for profile_index, profile_name in enumerate(profiles):
            if spec_index % 12 == 0 and profile_index == 0:
                outcome = "success_obstacle_pass"
                termination = ""
            elif spec_index % 12 == 1 and profile_index in {0, 1}:
                outcome = "collision_failure"
                termination = "obstacle_collision"
            else:
                outcome = "off_track_noncollision_noncompletion"
                termination = "off_track"
            episode_rows.append(
                _episode(
                    profile_name=profile_name,
                    task_source_id=f"spec_{spec_index:02d}",
                    task_family=task_family,
                    source_edge=source_edge,
                    outcome_bucket=outcome,
                    termination_reason=termination,
                )
            )

    write_json(m2677_dir / "summary.json", {"status_pass": True})
    write_csv_rows(m2677_dir / "episode_rows.csv", episode_rows)
    write_csv_rows(m2677_dir / "profile_aggregate.csv", [{"profile_name": profile} for profile in profiles])
    write_csv_rows(
        m2677_dir / "spec_aggregate.csv",
        [{"task_source_id": f"spec_{index:02d}"} for index in range(m2682.TARGET_SPEC_COUNT)],
    )
    write_csv_rows(m2677_dir / "comparison_aggregate.csv", [{"comparison": "diagnostic"}])
    _write_m2680_sources(m2680_dir)

    summary = m2682.materialize_task_quality_role_semantics_repair(
        m2677_dir=m2677_dir,
        m2680_dir=m2680_dir,
        output_dir=out_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization_pass"
    )
    assert summary["episode_count"] == 864
    assert summary["role_task_quality_blocker_row_count"] > 0
    assert summary["repair_candidate_row_count"] > 0
    assert summary["excluded_candidate_row_count"] > 0
    assert 0 < summary["proposed_measured_subset_row_count"] < 864
    assert summary["proposed_subset_is_full_public_matrix"] is False
    assert summary["proposed_subset_selected_from_success_only"] is False
    assert summary["role_semantics_actor_visible"] is False
    assert summary["paper_level_claim_made"] is False
    assert read_json(out_dir / "summary.json") == summary
    assert doc_path.read_text(encoding="utf-8").strip()

    candidate_rows = _read_csv(out_dir / "repair_candidate_rows.csv")
    subset_rows = _read_csv(out_dir / "proposed_measured_subset_rows.csv")
    claim_rows = _read_csv(out_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(out_dir / "gate_matrix.csv")
    assert {row["diagnostic_only_no_verdict"] for row in candidate_rows} == {"True"}
    assert {row["role_semantics_actor_visible"] for row in candidate_rows} == {"False"}
    assert {row["not_selected_from_success_only"] for row in subset_rows} == {"True"}
    assert len({row["profile_name"] for row in subset_rows}) == 12
    assert len({row["task_family"] for row in subset_rows}) == 2
    assert {row["allowed_in_m2682"] for row in claim_rows if row["claim_id"] == "paper_level_evidence"} == {
        "False"
    }
    assert {row["status_pass"] for row in gate_rows} == {"True"}


def test_role_semantics_proxy_and_candidate_rows_are_diagnostic_only() -> None:
    actuator_row = {
        "source_edge": "actuator_delay_step|capability_step_up",
        "task_family": "T4",
        "executable_source_family": "capability_step_up",
    }
    boundary_row = {
        "source_edge": "curved_boundary_obstacle|t5_boundary_axis_retarget",
        "task_family": "T5",
        "executable_source_family": "curved_boundary_obstacle",
    }
    assert m2682.role_semantics_proxy(actuator_row) == "hidden_dynamics_or_actuator_response"
    assert m2682.role_semantics_proxy(boundary_row) == "boundary_or_reveal_geometry"

    blocker_rows = [
        m2682.build_one_blocker_row(
            "T4",
            "actuator_delay_step|capability_step_up",
            "hidden_dynamics_or_actuator_response",
            [
                _episode(
                    profile_name="p0",
                    task_source_id="s0",
                    task_family="T4",
                    source_edge="actuator_delay_step|capability_step_up",
                    outcome_bucket="success_obstacle_pass",
                    termination_reason="",
                ),
                _episode(
                    profile_name="p1",
                    task_source_id="s0",
                    task_family="T4",
                    source_edge="actuator_delay_step|capability_step_up",
                    outcome_bucket="off_track_noncollision_noncompletion",
                    termination_reason="off_track",
                ),
            ],
        ),
        m2682.build_one_blocker_row(
            "T5",
            "curved_boundary_obstacle|t5_boundary_axis_retarget",
            "boundary_or_reveal_geometry",
            [
                _episode(
                    profile_name="p0",
                    task_source_id="s1",
                    task_family="T5",
                    source_edge="curved_boundary_obstacle|t5_boundary_axis_retarget",
                    outcome_bucket="off_track_noncollision_noncompletion",
                    termination_reason="off_track",
                )
            ],
        ),
    ]
    candidates, excluded = m2682.build_repair_candidate_rows(blocker_rows, max_candidates=1)
    assert len(candidates) == 1
    assert len(excluded) == 1
    assert candidates[0]["diagnostic_only_no_verdict"] is True
    assert candidates[0]["actor_input_contract_changed"] is False
    assert candidates[0]["role_semantics_actor_visible"] is False
    assert candidates[0]["hidden_oracle_actor_input_required"] is False
