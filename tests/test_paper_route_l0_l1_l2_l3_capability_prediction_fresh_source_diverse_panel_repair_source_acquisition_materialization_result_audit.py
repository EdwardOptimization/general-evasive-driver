import csv
import json
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_result_audit import (
    NEXT_ID,
    write_audit_artifacts,
)


def _write_rows(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_m2905_fixture(
    tmp_path: Path,
    *,
    claim_made: bool = False,
) -> tuple[Path, Path]:
    m2905_dir = tmp_path / "runs" / "m2905"
    artifacts = {
        "seed_gap_repair_rows": str(m2905_dir / "seed_gap_repair_rows.csv"),
        "candidate_support_repair_rows": str(m2905_dir / "candidate_support_repair_rows.csv"),
        "source_family_repair_rows": str(m2905_dir / "source_family_repair_rows.csv"),
        "dual_repair_rows": str(m2905_dir / "dual_repair_rows.csv"),
        "acquisition_required_rows": str(m2905_dir / "acquisition_required_rows.csv"),
        "repaired_candidate_projection_rows": str(
            m2905_dir / "repaired_candidate_projection_rows.csv"
        ),
        "exclusion_rows": str(m2905_dir / "exclusion_rows.csv"),
        "split_boundary_rows": str(m2905_dir / "split_boundary_rows.csv"),
        "target_boundary_rows": str(m2905_dir / "target_boundary_rows.csv"),
        "gate_rows": str(m2905_dir / "gate_rows.csv"),
        "rollback_rows": str(m2905_dir / "rollback_rows.csv"),
        "claim_rows": str(m2905_dir / "claim_rows.csv"),
        "run_state": str(m2905_dir / "run_state.json"),
        "summary": str(m2905_dir / "summary.json"),
        "follow_up_manifest": str(tmp_path / "experiments" / "manifests" / "m2906.json"),
    }
    seed_rows = [
        {
            "repair_row_id": "repair-001",
            "seed_gap_row_id": "seed-gap-001",
            "candidate_id": "candidate-a",
            "task_source_id": "task-a",
            "task_family": "T4",
            "missing_requirement": "candidate_artifact_count>=2",
            "candidate_support_gap": "True",
            "source_family_gap": "False",
            "dual_gap": "False",
            "acquisition_required": "True",
            "projected_fresh_candidate_after_existing_support": "False",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "repair_row_id": "repair-002",
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-b",
            "task_source_id": "task-b",
            "task_family": "T5",
            "missing_requirement": "candidate_artifact_count>=2;source_family_tag_count>=2",
            "candidate_support_gap": "True",
            "source_family_gap": "True",
            "dual_gap": "True",
            "acquisition_required": "True",
            "projected_fresh_candidate_after_existing_support": "False",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    candidate_rows = [
        {
            "candidate_support_repair_id": "candidate-support-001",
            "seed_gap_row_id": "seed-gap-001",
            "candidate_id": "candidate-a",
            "task_source_id": "task-a",
            "acquisition_required": "True",
            "status_pass": "True",
        },
        {
            "candidate_support_repair_id": "candidate-support-002",
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-b",
            "task_source_id": "task-b",
            "acquisition_required": "True",
            "status_pass": "True",
        },
    ]
    source_rows = [
        {
            "source_family_repair_id": "source-family-001",
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-b",
            "task_source_id": "task-b",
            "acquisition_required": "True",
            "status_pass": "True",
        }
    ]
    dual_rows = [
        {
            "dual_repair_id": "dual-repair-001",
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-b",
            "task_source_id": "task-b",
            "status_pass": "True",
        }
    ]
    acquisition_rows = [
        {
            "acquisition_required_id": "acquisition-001",
            "seed_gap_row_id": "seed-gap-001",
            "candidate_id": "candidate-a",
            "task_source_id": "task-a",
            "candidate_support_acquisition_required": "True",
            "source_family_acquisition_required": "False",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "acquisition_required_id": "acquisition-002",
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-b",
            "task_source_id": "task-b",
            "candidate_support_acquisition_required": "True",
            "source_family_acquisition_required": "True",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    projection_fields = [
        "projection_id",
        "seed_gap_row_id",
        "candidate_id",
        "task_source_id",
        "projected_fresh_candidate",
        "paper_proof_allowed",
        "validation_denominator_allowed",
        "ordinary_success_denominator_allowed",
    ]
    exclusion_rows = [
        {
            "exclusion_id": "exclusion-001",
            "candidate_id": "candidate-public",
            "task_source_id": "task-public",
            "source_row_class": "public_reference_usable",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "exclusion_id": "exclusion-002",
            "candidate_id": "candidate-a",
            "task_source_id": "task-a",
            "source_row_class": "source_singleton_seed",
            "paper_proof_allowed": "False",
            "validation_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    split_rows = [
        {
            "split_boundary_id": "split-001",
            "split_name": "acquisition_required",
            "paper_holdout_admitted": "False",
            "validation_denominator_allowed": "False",
            "model_quality_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
            "status_pass": "True",
        }
    ]
    target_rows = [
        {
            "target_boundary_id": "target-001",
            "target_family": "future_yaw_authority",
            "actor_visible_allowed": "False",
            "status_pass": "True",
        }
    ]
    gate_rows = [{"gate_id": "gate-001", "gate_family": "fixture", "status_pass": "True"}]
    rollback_rows = [
        {"rollback_id": "rollback-001", "rollback_family": "fixture", "status_pass": "True"}
    ]
    claim_rows = [
        {
            "claim_id": "claim-001",
            "claim_family": "model_quality",
            "claim_made": str(claim_made),
            "claim_allowed": "False",
        }
    ]

    _write_rows(Path(artifacts["seed_gap_repair_rows"]), list(seed_rows[0]), seed_rows)
    _write_rows(Path(artifacts["candidate_support_repair_rows"]), list(candidate_rows[0]), candidate_rows)
    _write_rows(Path(artifacts["source_family_repair_rows"]), list(source_rows[0]), source_rows)
    _write_rows(Path(artifacts["dual_repair_rows"]), list(dual_rows[0]), dual_rows)
    _write_rows(Path(artifacts["acquisition_required_rows"]), list(acquisition_rows[0]), acquisition_rows)
    _write_rows(Path(artifacts["repaired_candidate_projection_rows"]), projection_fields, [])
    _write_rows(Path(artifacts["exclusion_rows"]), list(exclusion_rows[0]), exclusion_rows)
    _write_rows(Path(artifacts["split_boundary_rows"]), list(split_rows[0]), split_rows)
    _write_rows(Path(artifacts["target_boundary_rows"]), list(target_rows[0]), target_rows)
    _write_rows(Path(artifacts["gate_rows"]), list(gate_rows[0]), gate_rows)
    _write_rows(Path(artifacts["rollback_rows"]), list(rollback_rows[0]), rollback_rows)
    _write_rows(Path(artifacts["claim_rows"]), list(claim_rows[0]), claim_rows)
    _write_json(Path(artifacts["run_state"]), {"status": "complete"})

    row_counts = {
        "seed_gap_repair_rows": len(seed_rows),
        "candidate_support_repair_rows": len(candidate_rows),
        "source_family_repair_rows": len(source_rows),
        "dual_repair_rows": len(dual_rows),
        "acquisition_required_rows": len(acquisition_rows),
        "repaired_candidate_projection_rows": 0,
        "exclusion_rows": len(exclusion_rows),
        "split_boundary_rows": len(split_rows),
        "target_boundary_rows": len(target_rows),
        "gate_rows": len(gate_rows),
        "rollback_rows": len(rollback_rows),
        "claim_rows": len(claim_rows),
    }
    summary = {
        "artifacts": artifacts,
        "row_counts": row_counts,
        "status_pass": True,
        "gate_matrix_pass": True,
        "decision": "repair_source_acquisition_materialized_existing_support_insufficient_route_to_m2906_result_audit",
        "seed_gap_row_count": len(seed_rows),
        "candidate_support_gap_count": len(candidate_rows),
        "source_family_gap_count": len(source_rows),
        "dual_gap_count": len(dual_rows),
        "acquisition_required_count": len(acquisition_rows),
        "repaired_candidate_projection_count": 0,
        "projected_fresh_candidate_task_count": 0,
        "projected_fresh_candidate_profile_task_count": 0,
        "projected_source_family_count": 0,
        "projected_task_family_count": 0,
        "projected_target_family_coverage_count": 0,
        "projected_design_targets_satisfied": False,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "source_singleton_rows_paper_proof_allowed": False,
        "guard_rows_ordinary_success_denominator_allowed": False,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
    }
    _write_json(m2905_dir / "summary.json", summary)
    return m2905_dir / "summary.json", m2905_dir


def test_m2906_accepts_claim_safe_negative_repair_acquisition_audit(tmp_path: Path) -> None:
    summary_path, m2905_dir = _write_m2905_fixture(tmp_path)
    output_doc = tmp_path / "docs" / "m2906.md"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2907.json"

    audit = write_audit_artifacts(
        m2905_summary=summary_path,
        m2905_dir=m2905_dir,
        output_doc=output_doc,
        follow_up_manifest=follow_up_manifest,
    )

    assert audit["status_pass"] is True
    assert (
        audit["decision"]
        == "accept_m2905_repair_source_acquisition_materialization_claim_safe_existing_support_insufficient_route_to_m2907_source_execution_or_pivot_synthesis"
    )
    assert audit["audit_gates"]["negative_projection_result_preserved"] is True
    assert audit["acquisition_required_count"] == 2
    assert audit["projection_row_count"] == 0
    assert output_doc.exists()
    assert "0 repaired-candidate projections" in output_doc.read_text(encoding="utf-8")
    manifest = read_json(follow_up_manifest)
    assert manifest["id"] == NEXT_ID
    assert manifest["local_search_guard"]["actual_progress_type"] == "synthesis_decision"


def test_m2906_fails_closed_when_claim_boundary_breaks(tmp_path: Path) -> None:
    summary_path, m2905_dir = _write_m2905_fixture(tmp_path, claim_made=True)

    audit = write_audit_artifacts(
        m2905_summary=summary_path,
        m2905_dir=m2905_dir,
        output_doc=tmp_path / "docs" / "m2906.md",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2907.json",
    )

    assert audit["status_pass"] is False
    assert (
        audit["decision"]
        == "reject_m2905_repair_source_acquisition_materialization_audit_route_to_manual_repair"
    )
    assert audit["audit_gates"]["claim_boundary_pass"] is False
    assert audit["claim_made_count"] == 1
