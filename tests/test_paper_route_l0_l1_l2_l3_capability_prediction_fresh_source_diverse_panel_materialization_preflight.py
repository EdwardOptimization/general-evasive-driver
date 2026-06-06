import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_materialization_preflight import (
    REQUIRED_TARGET_FAMILIES,
    write_preflight_artifacts,
)
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import (
    REQUIRED_PROFILES,
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


def _candidate(
    candidate_id: str,
    task_source_id: str,
    classification: str,
    *,
    candidate_artifact_count: int = 2,
    source_family_tag_count: int = 2,
    diagnostic_artifact_count: int = 2,
    executable_source_family: str = "capability_step_up",
    task_family: str = "T4",
    hidden_oracle_actor_input_required: bool = False,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "task_source_id": task_source_id,
        "task_family": task_family,
        "source_edge": "actuator_delay_step|capability_step_up",
        "window_tag": "reveal_plus_4",
        "executable_source_family": executable_source_family,
        "env_template_family": "t4_capability_step_temporal",
        "profile_count": len(REQUIRED_PROFILES),
        "required_profile_count": len(REQUIRED_PROFILES),
        "diagnostic_artifact_tags": "m2877_execution|m2838_selected_candidate",
        "diagnostic_artifact_count": diagnostic_artifact_count,
        "candidate_artifact_count": candidate_artifact_count,
        "guard_artifact_count": 1 if classification == "guard" else 0,
        "paired_delta_count": 1,
        "source_family_tag_count": source_family_tag_count,
        "required_profiles_present": "True",
        "config_checkpoint_complete": "True",
        "deployable_history_features_available": "True",
        "future_capability_targets_available": "True",
        "actor_contract_shape_72_action_3": "True",
        "hidden_oracle_actor_input_required": str(hidden_oracle_actor_input_required),
        "future_target_actor_input_required": "False",
        "evaluator_targets_actor_visible": "False",
        "classification": classification,
        "classification_reason": f"{classification} test row",
    }


def _profile_task_rows(task_source_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for task_source_id in task_source_ids:
        for profile_name in REQUIRED_PROFILES:
            rows.append(
                {
                    "profile_task_id": f"{task_source_id}::{profile_name}",
                    "task_source_id": task_source_id,
                    "profile_name": profile_name,
                    "profile_config_path": f"configs/{profile_name}.json",
                    "checkpoint_path": f"checkpoints/{profile_name}.pt",
                    "config_exists": "True",
                    "checkpoint_exists": "True",
                    "environment_rollout_scheduled": "False",
                    "training_scheduled": "False",
                }
            )
    return rows


def _target_rows(*, actor_visible_allowed: bool = False) -> list[dict[str, object]]:
    return [
        {
            "target_family": target_family,
            "required_columns": f"{target_family}_required",
            "available_columns": f"{target_family}_available",
            "status_pass": "True",
            "actor_visible_allowed": str(actor_visible_allowed),
        }
        for target_family in REQUIRED_TARGET_FAMILIES
    ]


def _write_fixture_inputs(
    tmp_path: Path,
    *,
    actor_visible_target: bool = False,
) -> tuple[Path, Path, Path, Path]:
    m2901_design = tmp_path / "docs" / "m2901.md"
    m2884_dir = tmp_path / "runs" / "m2884"
    m2887_dir = tmp_path / "runs" / "m2887"
    m2898_dir = tmp_path / "runs" / "m2898"
    m2901_design.parent.mkdir(parents=True, exist_ok=True)
    m2901_design.write_text("M2901 design fixture\n", encoding="utf-8")
    candidates = [
        _candidate("candidate-public", "task-public", "usable"),
        _candidate("candidate-fresh", "task-fresh", "source-singleton"),
        _candidate(
            "candidate-seed",
            "task-seed",
            "source-singleton",
            candidate_artifact_count=1,
            source_family_tag_count=1,
        ),
        _candidate("candidate-guard", "task-guard", "guard"),
        _candidate(
            "candidate-rejected",
            "task-rejected",
            "source-singleton",
            hidden_oracle_actor_input_required=True,
        ),
    ]
    _write_rows(m2884_dir / "candidate_panel_rows.csv", candidates)
    _write_rows(
        m2884_dir / "source_inventory_rows.csv",
        [
            {
                "source_id": "fixture-source",
                "row_count": len(candidates),
                "path_exists": "True",
                "classification": "candidate",
            }
        ],
    )
    _write_rows(
        m2887_dir / "profile_task_rows.csv",
        _profile_task_rows(["task-public"]),
    )
    _write_rows(
        m2887_dir / "evaluator_target_rows.csv",
        _target_rows(actor_visible_allowed=actor_visible_target),
    )
    (m2887_dir / "summary.json").write_text(
        '{"status_pass": true, "gate_matrix_pass": true}\n',
        encoding="utf-8",
    )
    m2898_dir.mkdir(parents=True, exist_ok=True)
    (m2898_dir / "summary.json").write_text(
        '{"status_pass": true, "gate_matrix_pass": true}\n',
        encoding="utf-8",
    )
    return m2901_design, m2884_dir, m2887_dir, m2898_dir


def test_m2902_materializes_fresh_panel_accounting_without_claims(tmp_path: Path) -> None:
    m2901_design, m2884_dir, m2887_dir, m2898_dir = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2902"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2903.json"

    summary = write_preflight_artifacts(
        m2901_design=m2901_design,
        m2884_dir=m2884_dir,
        m2887_dir=m2887_dir,
        m2898_dir=m2898_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert (
        summary["decision"]
        == "fresh_panel_materialized_insufficient_diversity_route_to_m2903_result_audit"
    )
    assert summary["fresh_source_diverse_targets_satisfied"] is False
    assert summary["public_reference_usable_count"] == 1
    assert summary["fresh_candidate_task_count"] == 1
    assert summary["fresh_candidate_profile_task_count"] == len(REQUIRED_PROFILES)
    assert summary["source_singleton_seed_count"] == 1
    assert summary["guard_exclusion_count"] == 1
    assert summary["rejected_boundary_violation_count"] == 1
    assert summary["target_family_coverage_count"] == len(REQUIRED_TARGET_FAMILIES)
    assert summary["paper_holdout_admitted"] is False
    assert summary["source_singleton_rows_paper_proof_allowed"] is False
    assert summary["guard_rows_ordinary_success_denominator_allowed"] is False
    assert summary["model_quality_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False

    taxonomy_rows = _read_rows(output_dir / "panel_row_taxonomy_rows.csv")
    split_rows = _read_rows(output_dir / "split_contract_rows.csv")
    target_rows = _read_rows(output_dir / "target_coverage_rows.csv")
    gate_rows = _read_rows(output_dir / "materialization_gate_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_rows.csv")

    classes_by_candidate = {row["candidate_id"]: row["source_row_class"] for row in taxonomy_rows}
    assert classes_by_candidate == {
        "candidate-public": "public_reference_usable",
        "candidate-fresh": "fresh_source_diverse_candidate",
        "candidate-seed": "source_singleton_seed",
        "candidate-guard": "guard_exclusion",
        "candidate-rejected": "rejected_boundary_violation",
    }
    assert {row["paper_holdout_admitted"] for row in split_rows} == {"False"}
    assert {row["ordinary_success_denominator_allowed"] for row in split_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in target_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert follow_up_manifest.exists()
    assert read_json(follow_up_manifest)["id"].startswith("m2903-")


def test_m2902_fails_closed_on_actor_visible_targets(tmp_path: Path) -> None:
    m2901_design, m2884_dir, m2887_dir, m2898_dir = _write_fixture_inputs(
        tmp_path,
        actor_visible_target=True,
    )

    summary = write_preflight_artifacts(
        m2901_design=m2901_design,
        m2884_dir=m2884_dir,
        m2887_dir=m2887_dir,
        m2898_dir=m2898_dir,
        output_dir=tmp_path / "runs" / "m2902",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2903.json",
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == "fresh_panel_materialization_preflight_incomplete"
    assert summary["evaluator_targets_actor_visible"] is True
    target_rows = _read_rows(tmp_path / "runs" / "m2902" / "target_coverage_rows.csv")
    assert {row["failure_type"] for row in target_rows} == {
        "actor_visible_target_contract_violation"
    }
