from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import engineering_controller_route_a_post_cross_axis_negative_failure_localization_panel as m2756


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2753_dir = root / "m2753"
    m2753_dir.mkdir()
    write_json(
        m2753_dir / "summary.json",
        {
            "status_pass": True,
            "diagnostic_success_count": 0,
            "diagnostic_collision_count": 3,
            "diagnostic_offtrack_count": 9,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    candidate_rows = []
    execution_rows = []
    for index in range(12):
        candidate_id = f"m2753-cross-axis-candidate-{index + 1:04d}"
        task_source_id = f"m1680-spec-{index + 1:04d}"
        source_edge = "edge_a|edge_b" if index < 6 else "edge_c|edge_d"
        stress_axis = (
            "actuator_delay_or_response"
            if index < 3
            else "brake_or_drive_authority"
            if index < 6
            else "late_boundary_or_near_boundary"
            if index < 9
            else "curved_or_retargeted_obstacle"
        )
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": source_edge,
                "stress_axis_primary": stress_axis,
                "stress_axis_tags": stress_axis,
                "candidate_admitted": True,
                "prior_panel_excluded": False,
                "hidden_oracle_actor_input_required": False,
                "stress_axis_labels_actor_visible": False,
                "diagnostic_only_no_verdict": True,
            }
        )
        collision = index < 3
        execution_rows.append(
            {
                "candidate_id": candidate_id,
                "resolution_id": f"m2753-resolution-{index + 1:04d}",
                "task_source_id": task_source_id,
                "workload_id": f"{task_source_id}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": source_edge,
                "stress_axis_primary": stress_axis,
                "stress_axis_tags": stress_axis,
                "termination_reason": "obstacle_collision" if collision else "off_track",
                "outcome_bucket": "collision_failure" if collision else "off_track_noncollision_noncompletion",
                "min_clearance_margin": -0.25 if collision else 5.0 + index,
                "return": 10.0 + index,
                "success": False,
                "collision": collision,
                "obstacle_completed": False,
                "hidden_oracle_actor_input_required": False,
                "actor_input_contract_changed": False,
                "stress_axis_labels_actor_visible": False,
                "success_progress_labels_actor_visible": False,
                "verdict_labels_actor_visible": False,
            }
        )
    write_csv_rows(m2753_dir / "cross_axis_candidate_rows.csv", candidate_rows)
    write_csv_rows(m2753_dir / "candidate_execution_rows.csv", execution_rows)
    write_csv_rows(
        m2753_dir / "stress_axis_aggregate_rows.csv",
        [
            {
                "stress_axis_tag": axis,
                "candidate_count": count,
                "episode_count": count,
                "failure_count": 0,
                "accounted_count": count,
                "success_rate_diagnostic": 0.0,
                "collision_rate_diagnostic": 0.0,
                "offtrack_rate_diagnostic": 1.0,
                "clearance_margin_mean": 1.0,
                "return_mean": 1.0,
                "all_selected_metrics_finite": True,
                "ranking_claim_made": False,
                "success_rate_verdict_claim_made": False,
                "diagnostic_only_no_verdict": True,
            }
            for axis, count in [
                ("actuator_delay_or_response", 3),
                ("brake_or_drive_authority", 3),
                ("late_boundary_or_near_boundary", 3),
                ("curved_or_retargeted_obstacle", 3),
            ]
        ],
    )
    write_csv_rows(
        m2753_dir / "prior_panel_exclusion_rows.csv",
        [
            {
                "exclusion_id": f"m2753-prior-panel-exclusion-{index + 1:04d}",
                "source_panel": "m2737_candidate_execution_rows",
                "task_source_id": f"prior-{index + 1:04d}",
                "row_count": 2,
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "actor_visible_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "diagnostic_only_no_verdict": True,
            }
            for index in range(25)
        ],
    )
    write_csv_rows(
        m2753_dir / "blocker_guard_rows.csv",
        [
            {
                "guard_id": f"m2753-blocker-guard-{index + 1:04d}",
                "blocker_id": f"blocker-{index + 1:04d}",
                "route": "Route A",
                "evidence_family": "known_failure_boundary",
                "current_status": "active",
                "blocking_count": 1,
                "execution_candidate": False,
                "execution_admitted": False,
                "execution_run": False,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
                "diagnostic_only_no_verdict": True,
            }
            for index in range(6)
        ],
    )
    write_csv_rows(
        m2753_dir / "actor_contract_guard_rows.csv",
        [
            {"guard_id": "obs", "guard_family": "p0_observation_dim", "observed": 72, "expected": 72, "status_pass": True},
            {"guard_id": "act", "guard_family": "action_dim", "observed": 3, "expected": 3, "status_pass": True},
        ],
    )
    write_csv_rows(
        m2753_dir / "claim_boundary_rows.csv",
        [{"claim_id": "m2753-claim", "allowed_in_m2753": True, "claim_made": True, "status_pass": True}],
    )
    write_csv_rows(
        m2753_dir / "gate_matrix.csv",
        [{"gate_id": "m2753-gate", "gate_family": "artifact", "status_pass": True}],
    )
    docs = {}
    for name in ["m2755.md", "m2754.md", "route.md", "m2757.json"]:
        path = root / name
        path.write_text("present\n", encoding="utf-8")
        docs[name] = path
    return {
        "m2753_dir": m2753_dir,
        "m2755": docs["m2755.md"],
        "m2754": docs["m2754.md"],
        "route_plan": docs["route.md"],
        "follow_up": docs["m2757.json"],
    }


def test_m2756_materializes_negative_failure_localization_without_overclaims(tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2756"
    doc_path = tmp_path / "m2756.md"

    summary = m2756.materialize_post_cross_axis_negative_failure_localization_panel(
        output_dir,
        m2753_dir=paths["m2753_dir"],
        m2755_synthesis=paths["m2755"],
        m2754_audit=paths["m2754"],
        route_plan=paths["route_plan"],
        doc_path=doc_path,
        follow_up_manifest=paths["follow_up"],
    )

    assert summary["status_pass"] is True
    assert summary["failure_localization_row_count"] == 12
    assert summary["collision_negative_clearance_count"] == 3
    assert summary["offtrack_positive_clearance_count"] == 9
    assert summary["guardrail_context_row_count"] == 31
    assert summary["prior_panel_guardrail_row_count"] == 25
    assert summary["blocker_guardrail_row_count"] == 6
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["gate_matrix_pass"] is True

    localization_rows = _read_csv(output_dir / "failure_localization_rows.csv")
    assert {row["failure_family"] for row in localization_rows} == {
        "collision_negative_clearance",
        "offtrack_positive_clearance",
    }
    assert {row["actor_visible_allowed"] for row in localization_rows} == {"False"}
    assert {row["diagnostic_only_no_verdict"] for row in localization_rows} == {"True"}

    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    blocked_claims = [row for row in claim_rows if row["allowed_in_m2756"] == "False"]
    assert blocked_claims
    assert {row["claim_made"] for row in blocked_claims} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
