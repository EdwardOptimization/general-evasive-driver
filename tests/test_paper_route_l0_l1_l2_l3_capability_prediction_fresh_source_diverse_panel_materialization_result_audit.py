import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_materialization_result_audit import (
    NEXT_ID,
    write_audit_artifacts,
)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_m2902_fixture(tmp_path: Path, *, claim_made: bool = False) -> tuple[Path, Path]:
    m2902_dir = tmp_path / "runs" / "m2902"
    artifacts = {
        "panel_row_taxonomy_rows": str(m2902_dir / "panel_row_taxonomy_rows.csv"),
        "source_diversity_rows": str(m2902_dir / "source_diversity_rows.csv"),
        "split_contract_rows": str(m2902_dir / "split_contract_rows.csv"),
        "target_coverage_rows": str(m2902_dir / "target_coverage_rows.csv"),
        "seed_gap_rows": str(m2902_dir / "seed_gap_rows.csv"),
        "guard_exclusion_rows": str(m2902_dir / "guard_exclusion_rows.csv"),
        "materialization_gate_rows": str(m2902_dir / "materialization_gate_rows.csv"),
        "rollback_rows": str(m2902_dir / "rollback_rows.csv"),
        "claim_rows": str(m2902_dir / "claim_rows.csv"),
        "run_state": str(m2902_dir / "run_state.json"),
        "follow_up_manifest": str(tmp_path / "experiments" / "manifests" / "m2903.json"),
        "summary": str(m2902_dir / "summary.json"),
    }
    taxonomy_rows = [
        {
            "taxonomy_row_id": "taxonomy-001",
            "candidate_id": "public",
            "task_source_id": "task-public",
            "source_row_class": "public_reference_usable",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "taxonomy_row_id": "taxonomy-002",
            "candidate_id": "seed",
            "task_source_id": "task-seed",
            "source_row_class": "source_singleton_seed",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "taxonomy_row_id": "taxonomy-003",
            "candidate_id": "guard",
            "task_source_id": "task-guard",
            "source_row_class": "guard_exclusion",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    source_diversity_rows = [
        {
            "diversity_row_id": "diversity-001",
            "row_class": "public_reference_usable",
            "task_count": 1,
            "profile_task_count": 12,
            "fresh_source_diverse_targets_satisfied": "False",
            "status_pass": "True",
        },
        {
            "diversity_row_id": "diversity-002",
            "row_class": "fresh_source_diverse_candidate",
            "task_count": 0,
            "profile_task_count": 0,
            "fresh_source_diverse_targets_satisfied": "False",
            "status_pass": "True",
        },
    ]
    split_rows = [
        {
            "split_row_id": "split-001",
            "split_name": "public_reference_fit",
            "paper_holdout_admitted": "False",
            "validation_denominator_allowed": "False",
            "model_quality_denominator_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
            "status_pass": "True",
        }
    ]
    target_rows = [
        {
            "target_coverage_row_id": "target-001",
            "target_family": "future_yaw_authority",
            "fresh_candidate_available_count": 0,
            "actor_visible_allowed": "False",
            "status_pass": "True",
        }
    ]
    seed_rows = [
        {
            "seed_gap_row_id": "seed-gap-001",
            "candidate_id": "seed",
            "task_source_id": "task-seed",
            "source_row_class": "source_singleton_seed",
            "missing_requirement": "source_family_tag_count>=2",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        }
    ]
    guard_rows = [
        {
            "guard_exclusion_row_id": "guard-001",
            "candidate_id": "guard",
            "task_source_id": "task-guard",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        }
    ]
    gate_rows = [
        {
            "gate_id": "gate-001",
            "gate_family": "fixture",
            "status_pass": "True",
        }
    ]
    rollback_rows = [
        {
            "rollback_id": "rollback-001",
            "rollback_family": "fixture",
            "status_pass": "True",
        }
    ]
    claim_rows = [
        {
            "claim_id": "claim-001",
            "claim_family": "model_quality",
            "claim_made": str(claim_made),
            "claim_allowed": "False",
        }
    ]
    _write_rows(Path(artifacts["panel_row_taxonomy_rows"]), taxonomy_rows)
    _write_rows(Path(artifacts["source_diversity_rows"]), source_diversity_rows)
    _write_rows(Path(artifacts["split_contract_rows"]), split_rows)
    _write_rows(Path(artifacts["target_coverage_rows"]), target_rows)
    _write_rows(Path(artifacts["seed_gap_rows"]), seed_rows)
    _write_rows(Path(artifacts["guard_exclusion_rows"]), guard_rows)
    _write_rows(Path(artifacts["materialization_gate_rows"]), gate_rows)
    _write_rows(Path(artifacts["rollback_rows"]), rollback_rows)
    _write_rows(Path(artifacts["claim_rows"]), claim_rows)
    _write_json(Path(artifacts["run_state"]), {"status": "complete"})
    summary = {
        "artifacts": artifacts,
        "row_counts": {
            "panel_row_taxonomy_rows": len(taxonomy_rows),
            "source_diversity_rows": len(source_diversity_rows),
            "split_contract_rows": len(split_rows),
            "target_coverage_rows": len(target_rows),
            "seed_gap_rows": len(seed_rows),
            "guard_exclusion_rows": len(guard_rows),
            "materialization_gate_rows": len(gate_rows),
            "rollback_rows": len(rollback_rows),
            "claim_rows": len(claim_rows),
        },
        "status_pass": True,
        "gate_matrix_pass": True,
        "decision": "fresh_panel_materialized_insufficient_diversity_route_to_m2903_result_audit",
        "fresh_source_diverse_targets_satisfied": False,
        "public_reference_usable_count": 1,
        "fresh_candidate_task_count": 0,
        "fresh_candidate_profile_task_count": 0,
        "source_singleton_seed_count": 1,
        "guard_exclusion_count": 1,
        "fresh_panel_gap_count": 0,
        "rejected_boundary_violation_count": 0,
        "target_family_coverage_count": 0,
        "source_family_count": 0,
        "task_family_count": 0,
        "actor_contract_shape_72_action_3": True,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": False,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "model_quality_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "driver_performance_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
    }
    _write_json(m2902_dir / "summary.json", summary)
    return m2902_dir / "summary.json", m2902_dir


def test_m2903_accepts_claim_safe_negative_materialization_audit(tmp_path: Path) -> None:
    summary_path, m2902_dir = _write_m2902_fixture(tmp_path)
    output_doc = tmp_path / "docs" / "m2903.md"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2904.json"

    audit = write_audit_artifacts(
        m2902_summary=summary_path,
        m2902_dir=m2902_dir,
        output_doc=output_doc,
        follow_up_manifest=follow_up_manifest,
    )

    assert audit["status_pass"] is True
    assert (
        audit["decision"]
        == "accept_m2902_materialization_claim_safe_insufficient_diversity_route_to_m2904_repair_source_acquisition_design"
    )
    assert audit["audit_gates"]["negative_diversity_result_preserved"] is True
    assert audit["claim_made_count"] == 0
    assert output_doc.exists()
    assert "zero admitted fresh/source-diverse candidates" in output_doc.read_text(encoding="utf-8")
    manifest = read_json(follow_up_manifest)
    assert manifest["id"] == NEXT_ID
    assert manifest["local_search_guard"]["actual_progress_type"] == "design_only"


def test_m2903_fails_closed_when_claim_boundary_breaks(tmp_path: Path) -> None:
    summary_path, m2902_dir = _write_m2902_fixture(tmp_path, claim_made=True)

    audit = write_audit_artifacts(
        m2902_summary=summary_path,
        m2902_dir=m2902_dir,
        output_doc=tmp_path / "docs" / "m2903.md",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2904.json",
    )

    assert audit["status_pass"] is False
    assert audit["decision"] == "reject_m2902_materialization_audit_route_to_manual_repair"
    assert audit["audit_gates"]["claim_boundary_pass"] is False
    assert audit["claim_made_count"] == 1
