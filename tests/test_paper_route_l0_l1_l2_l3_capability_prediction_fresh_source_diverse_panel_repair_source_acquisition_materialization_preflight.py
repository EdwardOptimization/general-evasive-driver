import csv
import json
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight import (
    NEXT_ID,
    write_preflight_artifacts,
)


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_fixture_inputs(
    tmp_path: Path,
    *,
    actor_visible_target: bool = False,
) -> tuple[Path, Path, Path, Path]:
    m2904_design = tmp_path / "docs" / "m2904.md"
    m2903_audit = tmp_path / "docs" / "m2903.md"
    m2902_dir = tmp_path / "runs" / "m2902"
    m2884_dir = tmp_path / "runs" / "m2884"
    m2904_design.parent.mkdir(parents=True, exist_ok=True)
    m2904_design.write_text("M2904 design fixture\n", encoding="utf-8")
    m2903_audit.write_text("M2903 audit fixture\n", encoding="utf-8")
    seed_gap_rows = [
        {
            "seed_gap_row_id": "seed-gap-001",
            "candidate_id": "candidate-seed-a",
            "task_source_id": "task-seed-a",
            "source_row_class": "source_singleton_seed",
            "task_family": "T4",
            "source_edge": "edge-a",
            "env_template_family": "env-a",
            "missing_requirement": "candidate_artifact_count>=2",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
        {
            "seed_gap_row_id": "seed-gap-002",
            "candidate_id": "candidate-seed-b",
            "task_source_id": "task-seed-b",
            "source_row_class": "source_singleton_seed",
            "task_family": "T5",
            "source_edge": "edge-b",
            "env_template_family": "env-b",
            "missing_requirement": "candidate_artifact_count>=2;source_family_tag_count>=2",
            "paper_proof_allowed": "False",
            "ordinary_success_denominator_allowed": "False",
        },
    ]
    taxonomy_rows = [
        {
            "taxonomy_row_id": "taxonomy-001",
            "candidate_id": "candidate-public",
            "task_source_id": "task-public",
            "source_row_class": "public_reference_usable",
            "original_classification": "usable",
            "task_family": "T4",
            "executable_source_family": "family-public",
            "profile_count": 12,
            "candidate_artifact_count": 2,
            "source_family_tag_count": 2,
            "diagnostic_artifact_count": 2,
            "classification_reason": "public reference",
        },
        {
            "taxonomy_row_id": "taxonomy-002",
            "candidate_id": "candidate-seed-a",
            "task_source_id": "task-seed-a",
            "source_row_class": "source_singleton_seed",
            "original_classification": "source-singleton",
            "task_family": "T4",
            "executable_source_family": "family-a",
            "profile_count": 12,
            "candidate_artifact_count": 1,
            "source_family_tag_count": 2,
            "diagnostic_artifact_count": 2,
            "classification_reason": "candidate support gap",
        },
        {
            "taxonomy_row_id": "taxonomy-003",
            "candidate_id": "candidate-seed-b",
            "task_source_id": "task-seed-b",
            "source_row_class": "source_singleton_seed",
            "original_classification": "source-singleton",
            "task_family": "T5",
            "executable_source_family": "family-b",
            "profile_count": 12,
            "candidate_artifact_count": 1,
            "source_family_tag_count": 1,
            "diagnostic_artifact_count": 2,
            "classification_reason": "dual gap",
        },
        {
            "taxonomy_row_id": "taxonomy-004",
            "candidate_id": "candidate-guard",
            "task_source_id": "task-guard",
            "source_row_class": "guard_exclusion",
            "original_classification": "guard",
            "task_family": "T5",
            "executable_source_family": "family-guard",
            "profile_count": 12,
            "candidate_artifact_count": 0,
            "source_family_tag_count": 1,
            "diagnostic_artifact_count": 2,
            "classification_reason": "guard",
        },
    ]
    target_rows = [
        {
            "target_coverage_row_id": "target-001",
            "target_family": "future_yaw_authority",
            "fresh_candidate_available_count": 0,
            "actor_visible_allowed": str(actor_visible_target),
            "status_pass": "True",
        }
    ]
    _write_rows(m2902_dir / "seed_gap_rows.csv", seed_gap_rows)
    _write_rows(m2902_dir / "panel_row_taxonomy_rows.csv", taxonomy_rows)
    _write_rows(m2902_dir / "target_coverage_rows.csv", target_rows)
    _write_json(
        m2902_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "future_target_actor_input_required": False,
            "evaluator_targets_actor_visible": False,
            "paper_holdout_admitted": False,
            "preflight_only_split": True,
        },
    )
    _write_rows(
        m2884_dir / "source_inventory_rows.csv",
        [
            {
                "source_inventory_id": "source-001",
                "artifact_tag": "fixture",
                "path_exists": "True",
                "candidate_row_count": 2,
                "guard_row_count": 1,
            }
        ],
    )
    _write_rows(
        m2884_dir / "candidate_panel_rows.csv",
        [
            {
                "candidate_id": row["candidate_id"],
                "task_source_id": row["task_source_id"],
                "classification": row["original_classification"],
            }
            for row in taxonomy_rows
        ],
    )
    return m2904_design, m2903_audit, m2902_dir, m2884_dir


def test_m2905_materializes_acquisition_required_repair_rows(tmp_path: Path) -> None:
    m2904_design, m2903_audit, m2902_dir, m2884_dir = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2905"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2906.json"

    summary = write_preflight_artifacts(
        m2904_design=m2904_design,
        m2903_audit=m2903_audit,
        m2902_dir=m2902_dir,
        m2884_dir=m2884_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["decision"]
        == "repair_source_acquisition_materialized_existing_support_insufficient_route_to_m2906_result_audit"
    )
    assert summary["seed_gap_row_count"] == 2
    assert summary["candidate_support_gap_count"] == 2
    assert summary["source_family_gap_count"] == 1
    assert summary["dual_gap_count"] == 1
    assert summary["acquisition_required_count"] == 2
    assert summary["repaired_candidate_projection_count"] == 0
    assert summary["projected_design_targets_satisfied"] is False
    assert summary["model_quality_claim_made"] is False

    acquisition_rows = _read_rows(output_dir / "acquisition_required_rows.csv")
    projection_rows = _read_rows(output_dir / "repaired_candidate_projection_rows.csv")
    split_rows = _read_rows(output_dir / "split_boundary_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_rows.csv")

    assert len(acquisition_rows) == 2
    assert projection_rows == []
    assert {row["validation_denominator_allowed"] for row in split_rows} == {"False"}
    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert follow_up_manifest.exists()
    assert read_json(follow_up_manifest)["id"] == NEXT_ID


def test_m2905_fails_closed_on_actor_visible_target_boundary(tmp_path: Path) -> None:
    m2904_design, m2903_audit, m2902_dir, m2884_dir = _write_fixture_inputs(
        tmp_path,
        actor_visible_target=True,
    )

    summary = write_preflight_artifacts(
        m2904_design=m2904_design,
        m2903_audit=m2903_audit,
        m2902_dir=m2902_dir,
        m2884_dir=m2884_dir,
        output_dir=tmp_path / "runs" / "m2905",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2906.json",
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == "repair_source_acquisition_materialization_preflight_incomplete"
    target_rows = _read_rows(tmp_path / "runs" / "m2905" / "target_boundary_rows.csv")
    assert target_rows[0]["actor_visible_allowed"] == "True"
    assert target_rows[0]["status_pass"] == "False"
