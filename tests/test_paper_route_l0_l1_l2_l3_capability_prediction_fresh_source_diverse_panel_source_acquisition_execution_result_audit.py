from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import (
    paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_source_acquisition_execution_result_audit as m2909,
)


def _rows(count: int, prefix: str) -> list[dict[str, object]]:
    return [{"row_id": f"{prefix}-{index:03d}"} for index in range(1, count + 1)]


def _write_m2908_fixture(tmp_path: Path, *, claim_made: bool = False) -> tuple[Path, Path]:
    m2908_dir = tmp_path / "runs" / "m2908"
    m2908_dir.mkdir(parents=True)
    input_rows = [
        {
            "source_acquisition_input_id": f"input-{index:03d}",
            "acquisition_required_id": f"acquisition-{index:03d}",
            "task_source_id": f"task-{index:03d}",
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
        }
        for index in range(1, 35)
    ]
    resolution_rows = [
        {
            "resolution_id": f"resolution-{index:03d}",
            "task_source_id": f"task-{index:03d}",
            "execution_admitted": True,
            "actor_contract_shape_72_action_3": True,
        }
        for index in range(1, 35)
    ]
    execution_rows = [
        {
            "source_acquisition_execution_id": f"execution-{index:03d}",
            "acquisition_required_id": f"acquisition-{index:03d}",
            "success": index % 5 == 0,
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
            "ranking_run": False,
            "model_quality_claim_made": False,
            "paper_claim_made": False,
            "finite_window_vs_gru_claim_made": False,
            "level3_self_id_claim_made": False,
            "driver_performance_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "high_fidelity_validation_claim_made": False,
            "full_ideal_driver_gate_passed": False,
        }
        for index in range(1, 35)
    ]
    candidate_rows = [
        {
            "candidate_support_evidence_id": f"candidate-support-{index:03d}",
            "acquisition_required_id": f"acquisition-{index:03d}",
            "added_candidate_artifact_count": 1,
            "candidate_support_satisfied_after_acquisition": True,
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
            "status_pass": True,
        }
        for index in range(1, 25)
    ]
    source_rows = [
        {
            "source_family_evidence_id": f"source-family-{index:03d}",
            "acquisition_required_id": f"acquisition-{index:03d}",
            "independent_source_family_evidence_added": False,
            "source_family_evidence_rejection_reason": "same_executable_source_family_not_independent",
            "added_source_family_tag_count": 0,
            "source_family_satisfied_after_acquisition": False,
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
            "status_pass": True,
        }
        for index in range(1, 18)
    ]
    projection_rows = [
        {
            "projection_id": f"projection-{index:03d}",
            "acquisition_required_id": f"acquisition-{index:03d}",
            "projected_fresh_candidate_after_source_acquisition": True,
            "paper_proof_allowed": False,
            "validation_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
        }
        for index in range(1, 18)
    ]
    split_rows = [
        {
            "split_boundary_id": f"split-{index:03d}",
            "status_pass": True,
            "paper_holdout_admitted": False,
            "validation_denominator_allowed": False,
            "model_quality_denominator_allowed": False,
            "ordinary_success_denominator_allowed": False,
        }
        for index in range(1, 6)
    ]
    target_rows = [
        {
            "target_boundary_id": f"target-{index:03d}",
            "status_pass": True,
            "actor_visible_allowed": False,
        }
        for index in range(1, 6)
    ]
    actor_rows = [
        {
            "actor_contract_id": f"actor-{index:03d}",
            "status_pass": True,
            "actor_visible_allowed": False,
        }
        for index in range(1, 10)
    ]
    claim_rows = [
        {
            "claim_id": f"claim-{index:03d}",
            "claim_family": f"claim-{index:03d}",
            "claim_made": claim_made and index == 1,
            "claim_allowed": False,
        }
        for index in range(1, 11)
    ]
    gate_rows = [
        {
            "gate_id": f"gate-{index:03d}",
            "gate_family": "fixture",
            "status_pass": True,
        }
        for index in range(1, 16)
    ]
    paths = {
        "source_acquisition_input_rows": m2908_dir / "source_acquisition_input_rows.csv",
        "execution_resolution_rows": m2908_dir / "execution_resolution_rows.csv",
        "source_acquisition_execution_rows": m2908_dir / "source_acquisition_execution_rows.csv",
        "acquisition_failure_rows": m2908_dir / "acquisition_failure_rows.csv",
        "candidate_support_evidence_rows": m2908_dir / "candidate_support_evidence_rows.csv",
        "source_family_evidence_rows": m2908_dir / "source_family_evidence_rows.csv",
        "repaired_candidate_projection_rows": m2908_dir / "repaired_candidate_projection_rows.csv",
        "split_boundary_rows": m2908_dir / "split_boundary_rows.csv",
        "target_boundary_rows": m2908_dir / "target_boundary_rows.csv",
        "actor_contract_rows": m2908_dir / "actor_contract_rows.csv",
        "claim_rows": m2908_dir / "claim_rows.csv",
        "gate_rows": m2908_dir / "gate_rows.csv",
        "run_state": m2908_dir / "run_state.json",
    }
    write_csv_rows(paths["source_acquisition_input_rows"], input_rows)
    write_csv_rows(paths["execution_resolution_rows"], resolution_rows)
    write_csv_rows(paths["source_acquisition_execution_rows"], execution_rows)
    write_csv_rows(paths["acquisition_failure_rows"], [], fieldnames=["failure_id"])
    write_csv_rows(paths["candidate_support_evidence_rows"], candidate_rows)
    write_csv_rows(paths["source_family_evidence_rows"], source_rows)
    write_csv_rows(paths["repaired_candidate_projection_rows"], projection_rows)
    write_csv_rows(paths["split_boundary_rows"], split_rows)
    write_csv_rows(paths["target_boundary_rows"], target_rows)
    write_csv_rows(paths["actor_contract_rows"], actor_rows)
    write_csv_rows(paths["claim_rows"], claim_rows)
    write_csv_rows(paths["gate_rows"], gate_rows)
    write_json(paths["run_state"], {"complete": True})
    summary = {
        "status_pass": True,
        "gate_matrix_pass": True,
        "decision": "source_acquisition_execution_preflight_complete_projected_design_targets_unsatisfied_route_to_m2909_result_audit",
        "artifacts": {key: str(path) for key, path in paths.items()},
        "row_counts": {
            "source_acquisition_input_rows": 34,
            "execution_resolution_rows": 34,
            "source_acquisition_execution_rows": 34,
            "acquisition_failure_rows": 0,
            "candidate_support_evidence_rows": 24,
            "source_family_evidence_rows": 17,
            "repaired_candidate_projection_rows": 17,
            "split_boundary_rows": 5,
            "target_boundary_rows": 5,
            "actor_contract_rows": 9,
            "claim_rows": 10,
            "gate_rows": 15,
        },
        "fixed_m2905_acquisition_required_row_count": 34,
        "accounted_acquisition_row_count": 34,
        "source_acquisition_execution_row_count": 34,
        "acquisition_failure_row_count": 0,
        "candidate_support_required_count": 24,
        "candidate_support_evidence_added_count": 24,
        "source_family_required_count": 17,
        "independent_source_family_evidence_added_count": 0,
        "repaired_candidate_projection_count": 17,
        "projected_design_targets_satisfied": False,
        "projected_fresh_candidate_task_count": 17,
        "projected_fresh_candidate_profile_task_count": 204,
        "projected_target_family_coverage_count": 5,
        "all_selected_metrics_finite": True,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "source_acquisition_rows_paper_proof_allowed": False,
        "source_acquisition_rows_validation_denominator_allowed": False,
        "source_acquisition_rows_ordinary_success_denominator_allowed": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
    }
    summary_path = m2908_dir / "summary.json"
    write_json(summary_path, summary)
    return summary_path, m2908_dir


def test_m2909_accepts_partial_candidate_support_and_source_family_insufficiency(tmp_path: Path) -> None:
    summary_path, m2908_dir = _write_m2908_fixture(tmp_path)
    output_doc = tmp_path / "docs" / "m2909.md"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2910.json"

    audit = m2909.write_audit_artifacts(
        m2908_summary=summary_path,
        m2908_dir=m2908_dir,
        output_doc=output_doc,
        follow_up_manifest=follow_up_manifest,
    )

    assert audit["status_pass"] is True
    assert audit["decision"] == (
        "accept_m2908_source_acquisition_execution_claim_safe_partial_candidate_support_"
        "source_family_insufficient_route_to_m2910_continuation_or_pivot_synthesis"
    )
    assert audit["candidate_support_evidence_added_count"] == 24
    assert audit["independent_source_family_evidence_added_count"] == 0
    assert audit["projection_row_count"] == 17
    assert output_doc.exists()
    assert "same-family execution" in output_doc.read_text(encoding="utf-8")
    assert read_json(follow_up_manifest)["id"] == m2909.NEXT_ID


def test_m2909_rejects_claim_boundary_break(tmp_path: Path) -> None:
    summary_path, m2908_dir = _write_m2908_fixture(tmp_path, claim_made=True)
    output_doc = tmp_path / "docs" / "m2909.md"

    audit = m2909.write_audit_artifacts(
        m2908_summary=summary_path,
        m2908_dir=m2908_dir,
        output_doc=output_doc,
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2910.json",
    )

    assert audit["status_pass"] is False
    assert audit["decision"] == "reject_m2908_source_acquisition_execution_result_audit_route_to_manual_repair"
    assert audit["audit_gates"]["claim_boundary_pass"] is False
