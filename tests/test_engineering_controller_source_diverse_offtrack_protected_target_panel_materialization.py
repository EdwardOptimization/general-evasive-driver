from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.engineering_controller_source_diverse_offtrack_protected_target_panel_materialization import (
    materialize_source_diverse_offtrack_protected_target_panel,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m2684_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "episode_count": 6,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    write_csv_rows(
        root / "episode_rows.csv",
        [
            {
                "task_family": "T4",
                "source_edge": "actuator_delay_step|capability_step_up",
                "outcome_bucket": "off_track_noncollision_noncompletion",
                "termination_reason": "off_track",
            },
            {
                "task_family": "T4",
                "source_edge": "actuator_delay_step|capability_step_up",
                "outcome_bucket": "success_obstacle_pass",
                "termination_reason": "",
            },
            {
                "task_family": "T4",
                "source_edge": "curved_boundary_obstacle|t5_boundary_axis_retarget",
                "outcome_bucket": "off_track_noncollision_noncompletion",
                "termination_reason": "off_track",
            },
            {
                "task_family": "T4",
                "source_edge": "curved_boundary_obstacle|t5_boundary_axis_retarget",
                "outcome_bucket": "collision_failure",
                "termination_reason": "obstacle_collision",
            },
            {
                "task_family": "T5",
                "source_edge": "drive_loss_proxy|curved_boundary_obstacle",
                "outcome_bucket": "off_track_noncollision_noncompletion",
                "termination_reason": "off_track",
            },
            {
                "task_family": "T5",
                "source_edge": "drive_loss_proxy|curved_boundary_obstacle",
                "outcome_bucket": "off_track_noncollision_noncompletion",
                "termination_reason": "off_track",
            },
        ],
    )
    write_csv_rows(
        root / "outcome_aggregate.csv",
        [
            {"outcome_bucket": "off_track_noncollision_noncompletion", "episode_count": 4},
            {"outcome_bucket": "success_obstacle_pass", "episode_count": 1},
            {"outcome_bucket": "collision_failure", "episode_count": 1},
        ],
    )
    write_csv_rows(
        root / "termination_reason_aggregate.csv",
        [
            {"termination_reason": "off_track", "episode_count": 4},
            {"termination_reason": "obstacle_collision", "episode_count": 1},
            {"termination_reason": "", "episode_count": 1},
        ],
    )


def _write_m2664_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "protected_gate_blocking_row_count": 5,
            "protected_gate_regressed_row_count": 9,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    write_csv_rows(
        root / "combined_failure_taxonomy_rows.csv",
        [
            {
                "taxonomy_id": "tax0",
                "subject_id": "policy0",
                "dynamics_axis_id": "fresh_protected_fault_delay_noise",
                "blocking_gate_row_count": 3,
                "regressed_row_count": 4,
                "protected_blocker_preserved": True,
                "actor_visible_allowed": False,
            }
        ],
    )


def _write_m2667_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "m2664_protected_gate_blocking_row_count": 5,
            "m2664_protected_gate_regressed_row_count": 9,
            "actor_contract_shape_72_action_3": True,
        },
    )
    write_csv_rows(
        root / "known_failure_boundary_rows.csv",
        [
            {
                "boundary_id": "protected_subject",
                "taxonomy_axis": "subject",
                "subject_or_axis_or_metric": "policy0",
                "row_count": 3,
                "blocking_row_count": 3,
                "regressed_row_count": 4,
                "protected_blocker_preserved": True,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
            },
            {
                "boundary_id": "protected_axis",
                "taxonomy_axis": "dynamics_axis",
                "subject_or_axis_or_metric": "fresh_protected_fault_delay_noise",
                "row_count": 2,
                "blocking_row_count": 2,
                "regressed_row_count": 5,
                "protected_blocker_preserved": True,
                "protected_rows_in_success_denominator": False,
                "actor_visible_allowed": False,
            },
        ],
    )


def _write_m2688_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "known_blocker_disclosure_row_count": 4,
            "actor_contract_shape_72_action_3": True,
        },
    )
    write_csv_rows(
        root / "known_blocker_disclosure_rows.csv",
        [
            {
                "blocker_id": "current_sim_offtrack_blocker",
                "blocker_status": "active: 4/6 off-track outcomes and 4/6 off-track terminations",
                "actor_visible": False,
            },
            {
                "blocker_id": "protected_mitigation_blocker",
                "blocker_status": "active: 5 protected blocking rows and 9 regressed row count",
                "actor_visible": False,
            },
        ],
    )


def test_m2691_materializes_source_diverse_target_panel_without_claims(tmp_path: Path) -> None:
    m2684_dir = tmp_path / "m2684"
    m2664_dir = tmp_path / "m2664"
    m2667_dir = tmp_path / "m2667"
    m2688_dir = tmp_path / "m2688"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2691.md"
    follow_up_manifest = tmp_path / "m2692.json"
    follow_up_manifest.write_text("{}\n", encoding="utf-8")
    _write_m2684_source(m2684_dir)
    _write_m2664_source(m2664_dir)
    _write_m2667_source(m2667_dir)
    _write_m2688_source(m2688_dir)

    summary = materialize_source_diverse_offtrack_protected_target_panel(
        m2684_dir=m2684_dir,
        m2664_dir=m2664_dir,
        m2667_dir=m2667_dir,
        m2688_dir=m2688_dir,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == (
        "engineering_controller_source_diverse_offtrack_protected_target_panel_materialization_pass"
    )
    assert summary["source_diverse_panel_present"] is True
    assert summary["offtrack_target_row_count"] == 3
    assert summary["protected_target_row_count"] == 2
    assert summary["m2684_offtrack_outcome_count"] == 4
    assert summary["m2684_offtrack_termination_count"] == 4
    assert summary["m2664_protected_gate_blocking_row_count"] == 5
    assert summary["m2664_protected_gate_regressed_row_count"] == 9
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["target_labels_actor_visible"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["same_public_gate_repair_loop"] is False
    assert summary["requires_new_measured_execution_before_audit"] is False
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["current_sim_verdict_claim_made"] is False
    assert summary["high_fidelity_validation_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    blocker_rows = _read_csv(output_dir / "blocker_source_rows.csv")
    target_rows = _read_csv(output_dir / "target_panel_rows.csv")
    source_plan_rows = _read_csv(output_dir / "source_diversity_plan_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_family"] for row in blocker_rows} == {
        "current_sim_offtrack",
        "protected_mitigation",
        "package_blocker_disclosure",
    }
    assert {"current_sim_offtrack_containment", "protected_mitigation_preservation"} == {
        row["target_family"] for row in target_rows
    }
    assert {row["target_labels_actor_visible"] for row in target_rows} == {"False"}
    assert {row["hidden_oracle_actor_input_required"] for row in target_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in target_rows} == {"False"}
    assert any(row["plan_family"] == "joint_blocker_admission_surface" for row in source_plan_rows)
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert {
        row["allowed_in_m2691"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper_evidence", "current_sim_verdict"}
    } == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()
