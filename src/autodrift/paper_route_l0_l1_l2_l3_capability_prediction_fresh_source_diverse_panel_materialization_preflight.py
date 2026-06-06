"""Materialize the M2902 fresh/source-diverse capability panel preflight.

This module turns the M2901 design contract into machine-auditable accounting
rows. It intentionally separates "artifacts were materialized and claims stayed
safe" from "the fresh/source-diverse panel is large enough for model-quality
claims".
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import (
    ACTION_DIM,
    P0_OBSERVATION_DIM,
    REQUIRED_PROFILES,
)


DEFAULT_MILESTONE = (
    "m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_materialization_preflight"
)
DEFAULT_M2901_DESIGN = Path(
    "docs/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-design.md"
)
DEFAULT_M2884_DIR = Path(
    "runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight"
)
DEFAULT_M2887_DIR = Path(
    "runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_"
    "preflight"
)
DEFAULT_M2898_DIR = Path(
    "runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_"
    "preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
    "fresh-source-diverse-panel-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "preflight_accounting_only_no_validation_no_model_quality_no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_paper_proof_not_validation_not_full_driver_not_self_identification_evidence"
)
REQUIRED_TARGET_FAMILIES = (
    "future_braking_deceleration_envelope",
    "future_yaw_authority",
    "future_lateral_acceleration_response",
    "actuator_response_lag_proxy",
    "recovery_margin_after_maneuver",
    "first_critical_action_quality",
)
DESIGN_TARGETS = {
    "fresh_candidate_task_count": 24,
    "fresh_candidate_profile_task_count": 288,
    "source_family_count": 3,
    "task_family_count": 2,
    "max_single_source_family_share": 0.40,
    "max_single_task_family_share": 0.70,
    "target_family_coverage_count": 6,
}

PANEL_TAXONOMY_FIELDNAMES = (
    "taxonomy_row_id",
    "candidate_id",
    "task_source_id",
    "source_row_class",
    "original_classification",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "diagnostic_artifact_tags",
    "diagnostic_artifact_count",
    "candidate_artifact_count",
    "guard_artifact_count",
    "paired_delta_count",
    "source_family_tag_count",
    "profile_count",
    "required_profiles_present",
    "config_checkpoint_complete",
    "deployable_history_features_available",
    "future_capability_targets_available",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_required",
    "future_target_actor_input_required",
    "evaluator_targets_actor_visible",
    "admitted_for_fresh_panel_candidate",
    "public_reference_fit_allowed",
    "paper_proof_allowed",
    "ordinary_success_denominator_allowed",
    "classification_reason",
    "claim_boundary",
    "forbidden_interpretation",
)
SOURCE_DIVERSITY_FIELDNAMES = (
    "diversity_row_id",
    "scope",
    "row_class",
    "task_count",
    "profile_task_count",
    "source_family_count",
    "task_family_count",
    "target_family_coverage_count",
    "max_single_source_family_share",
    "max_single_task_family_share",
    "design_min_task_count",
    "design_min_profile_task_count",
    "design_min_source_family_count",
    "design_min_task_family_count",
    "design_max_single_source_family_share",
    "design_max_single_task_family_share",
    "design_required_target_family_count",
    "fresh_source_diverse_targets_satisfied",
    "status_pass",
    "failure_type",
    "claim_boundary",
)
SPLIT_CONTRACT_FIELDNAMES = (
    "split_row_id",
    "split_name",
    "row_class",
    "task_count",
    "profile_task_count",
    "paper_holdout_admitted",
    "validation_denominator_allowed",
    "model_quality_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "allowed_usage",
    "status_pass",
    "failure_type",
    "claim_boundary",
)
TARGET_COVERAGE_FIELDNAMES = (
    "target_coverage_row_id",
    "target_family",
    "required_columns",
    "available_columns",
    "public_reference_available_count",
    "fresh_candidate_available_count",
    "source_singleton_seed_available_count",
    "actor_visible_allowed",
    "target_scope",
    "status_pass",
    "failure_type",
    "claim_boundary",
)
SEED_GAP_FIELDNAMES = (
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "source_row_class",
    "task_family",
    "source_edge",
    "env_template_family",
    "missing_requirement",
    "repair_route",
    "may_seed_future_panel",
    "paper_proof_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
GUARD_EXCLUSION_FIELDNAMES = (
    "guard_exclusion_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "env_template_family",
    "diagnostic_artifact_tags",
    "exclusion_reason",
    "paper_proof_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
MATERIALIZATION_GATE_FIELDNAMES = (
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
)
ROLLBACK_FIELDNAMES = (
    "rollback_id",
    "rollback_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
)
CLAIM_FIELDNAMES = (
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_csv(path: Path, fieldnames: Iterable[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(str(value))
    except ValueError:
        return default


def _float_str(value: float) -> str:
    return f"{value:.6f}"


def _safe_share(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return max(counter.values()) / total


def _join(values: Iterable[str]) -> str:
    return ";".join(value for value in values if value)


def _target_row_by_family(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        row.get("target_family", ""): row
        for row in rows
        if row.get("target_family", "") in REQUIRED_TARGET_FAMILIES
    }


def _row_meets_fresh_candidate_contract(
    row: dict[str, str],
    public_reference_ids: set[str],
) -> tuple[bool, list[str]]:
    missing: list[str] = []
    task_source_id = row.get("task_source_id", "")
    if task_source_id in public_reference_ids:
        missing.append("task_source_id_outside_public_reference_usable")
    if row.get("classification", "") == "guard":
        missing.append("classification_not_guard")
    if not _bool(row.get("required_profiles_present")):
        missing.append("required_profiles_present")
    if not _bool(row.get("config_checkpoint_complete")):
        missing.append("config_checkpoint_complete")
    if _int(row.get("candidate_artifact_count")) < 2:
        missing.append("candidate_artifact_count>=2")
    if _int(row.get("source_family_tag_count")) < 2:
        missing.append("source_family_tag_count>=2")
    if _int(row.get("diagnostic_artifact_count")) < 2:
        missing.append("diagnostic_artifact_count>=2")
    if not _bool(row.get("deployable_history_features_available")):
        missing.append("deployable_history_features_available")
    if not _bool(row.get("future_capability_targets_available")):
        missing.append("future_capability_targets_available")
    if not _bool(row.get("actor_contract_shape_72_action_3")):
        missing.append("actor_contract_shape_72_action_3")
    if _bool(row.get("hidden_oracle_actor_input_required")):
        missing.append("hidden_oracle_actor_input_required_false")
    if _bool(row.get("future_target_actor_input_required")):
        missing.append("future_target_actor_input_required_false")
    if _bool(row.get("evaluator_targets_actor_visible")):
        missing.append("evaluator_targets_actor_visible_false")
    return not missing, missing


def _classify_panel_row(
    row: dict[str, str],
    public_reference_ids: set[str],
) -> tuple[str, bool, str]:
    boundary_violation_reasons = []
    if not _bool(row.get("actor_contract_shape_72_action_3")):
        boundary_violation_reasons.append("actor_contract_shape_not_72x3")
    if _bool(row.get("hidden_oracle_actor_input_required")):
        boundary_violation_reasons.append("hidden_oracle_actor_input_required")
    if _bool(row.get("future_target_actor_input_required")):
        boundary_violation_reasons.append("future_target_actor_input_required")
    if _bool(row.get("evaluator_targets_actor_visible")):
        boundary_violation_reasons.append("evaluator_targets_actor_visible")
    if boundary_violation_reasons:
        return "rejected_boundary_violation", False, _join(boundary_violation_reasons)

    classification = row.get("classification", "")
    task_source_id = row.get("task_source_id", "")
    if classification == "guard":
        return "guard_exclusion", False, "prior_surface_or_package_limitation_guard"
    if task_source_id in public_reference_ids:
        return "public_reference_usable", False, "existing_m2884_m2887_m2898_public_reference_fit_only"

    meets_fresh_contract, missing = _row_meets_fresh_candidate_contract(row, public_reference_ids)
    if meets_fresh_contract:
        return "fresh_source_diverse_candidate", True, "fresh_candidate_contract_satisfied"
    if classification == "source-singleton":
        return "source_singleton_seed", False, _join(missing)
    return "fresh_panel_gap", False, _join(missing)


def _panel_taxonomy_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    public_reference_ids = {
        row.get("task_source_id", "")
        for row in candidate_rows
        if row.get("classification", "") == "usable"
    }
    taxonomy_rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_rows, start=1):
        row_class, admitted, reason = _classify_panel_row(row, public_reference_ids)
        taxonomy_rows.append(
            {
                "taxonomy_row_id": f"taxonomy-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "source_row_class": row_class,
                "original_classification": row.get("classification", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "diagnostic_artifact_tags": row.get("diagnostic_artifact_tags", ""),
                "diagnostic_artifact_count": _int(row.get("diagnostic_artifact_count")),
                "candidate_artifact_count": _int(row.get("candidate_artifact_count")),
                "guard_artifact_count": _int(row.get("guard_artifact_count")),
                "paired_delta_count": _int(row.get("paired_delta_count")),
                "source_family_tag_count": _int(row.get("source_family_tag_count")),
                "profile_count": _int(row.get("profile_count"), len(REQUIRED_PROFILES)),
                "required_profiles_present": _bool(row.get("required_profiles_present")),
                "config_checkpoint_complete": _bool(row.get("config_checkpoint_complete")),
                "deployable_history_features_available": _bool(
                    row.get("deployable_history_features_available")
                ),
                "future_capability_targets_available": _bool(
                    row.get("future_capability_targets_available")
                ),
                "actor_contract_shape_72_action_3": _bool(
                    row.get("actor_contract_shape_72_action_3")
                ),
                "hidden_oracle_actor_input_required": _bool(
                    row.get("hidden_oracle_actor_input_required")
                ),
                "future_target_actor_input_required": _bool(
                    row.get("future_target_actor_input_required")
                ),
                "evaluator_targets_actor_visible": _bool(
                    row.get("evaluator_targets_actor_visible")
                ),
                "admitted_for_fresh_panel_candidate": admitted,
                "public_reference_fit_allowed": row_class == "public_reference_usable",
                "paper_proof_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "classification_reason": reason,
                "claim_boundary": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return taxonomy_rows


def _rows_for_class(
    taxonomy_rows: list[dict[str, Any]],
    row_class: str,
) -> list[dict[str, Any]]:
    return [row for row in taxonomy_rows if row["source_row_class"] == row_class]


def _profile_task_count(rows: list[dict[str, Any]]) -> int:
    return sum(_int(row.get("profile_count"), len(REQUIRED_PROFILES)) for row in rows)


def _source_diversity_metrics(
    rows: list[dict[str, Any]],
    target_family_coverage_count: int,
) -> dict[str, Any]:
    source_counter = Counter(
        row.get("executable_source_family") or "unknown_source_family" for row in rows
    )
    task_counter = Counter(row.get("task_family") or "unknown_task_family" for row in rows)
    return {
        "task_count": len(rows),
        "profile_task_count": _profile_task_count(rows),
        "source_family_count": len(source_counter),
        "task_family_count": len(task_counter),
        "target_family_coverage_count": target_family_coverage_count if rows else 0,
        "max_single_source_family_share": _safe_share(source_counter),
        "max_single_task_family_share": _safe_share(task_counter),
    }


def _fresh_targets_satisfied(metrics: dict[str, Any]) -> bool:
    return (
        metrics["task_count"] >= DESIGN_TARGETS["fresh_candidate_task_count"]
        and metrics["profile_task_count"] >= DESIGN_TARGETS["fresh_candidate_profile_task_count"]
        and metrics["source_family_count"] >= DESIGN_TARGETS["source_family_count"]
        and metrics["task_family_count"] >= DESIGN_TARGETS["task_family_count"]
        and metrics["target_family_coverage_count"]
        >= DESIGN_TARGETS["target_family_coverage_count"]
        and metrics["max_single_source_family_share"]
        <= DESIGN_TARGETS["max_single_source_family_share"]
        and metrics["max_single_task_family_share"]
        <= DESIGN_TARGETS["max_single_task_family_share"]
    )


def _source_diversity_rows(
    taxonomy_rows: list[dict[str, Any]],
    target_family_coverage_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    row_classes = (
        "public_reference_usable",
        "fresh_source_diverse_candidate",
        "source_singleton_seed",
        "fresh_panel_gap",
        "guard_exclusion",
        "rejected_boundary_violation",
    )
    fresh_rows = _rows_for_class(taxonomy_rows, "fresh_source_diverse_candidate")
    fresh_metrics = _source_diversity_metrics(fresh_rows, target_family_coverage_count)
    targets_satisfied = _fresh_targets_satisfied(fresh_metrics)
    rows: list[dict[str, Any]] = []
    for index, row_class in enumerate(row_classes, start=1):
        class_rows = _rows_for_class(taxonomy_rows, row_class)
        coverage_count = target_family_coverage_count if row_class == "fresh_source_diverse_candidate" else 0
        metrics = _source_diversity_metrics(class_rows, coverage_count)
        row_targets_satisfied = targets_satisfied if row_class == "fresh_source_diverse_candidate" else False
        rows.append(
            {
                "diversity_row_id": f"diversity-{index:03d}",
                "scope": "m2902_materialized_panel_taxonomy",
                "row_class": row_class,
                "task_count": metrics["task_count"],
                "profile_task_count": metrics["profile_task_count"],
                "source_family_count": metrics["source_family_count"],
                "task_family_count": metrics["task_family_count"],
                "target_family_coverage_count": metrics["target_family_coverage_count"],
                "max_single_source_family_share": _float_str(
                    metrics["max_single_source_family_share"]
                ),
                "max_single_task_family_share": _float_str(
                    metrics["max_single_task_family_share"]
                ),
                "design_min_task_count": DESIGN_TARGETS["fresh_candidate_task_count"],
                "design_min_profile_task_count": DESIGN_TARGETS[
                    "fresh_candidate_profile_task_count"
                ],
                "design_min_source_family_count": DESIGN_TARGETS["source_family_count"],
                "design_min_task_family_count": DESIGN_TARGETS["task_family_count"],
                "design_max_single_source_family_share": _float_str(
                    DESIGN_TARGETS["max_single_source_family_share"]
                ),
                "design_max_single_task_family_share": _float_str(
                    DESIGN_TARGETS["max_single_task_family_share"]
                ),
                "design_required_target_family_count": DESIGN_TARGETS[
                    "target_family_coverage_count"
                ],
                "fresh_source_diverse_targets_satisfied": row_targets_satisfied,
                "status_pass": True,
                "failure_type": ""
                if row_class != "fresh_source_diverse_candidate" or row_targets_satisfied
                else "fresh_panel_materialized_insufficient_diversity",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows, fresh_metrics, targets_satisfied


def _target_coverage_rows(
    evaluator_target_rows: list[dict[str, str]],
    taxonomy_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    by_family = _target_row_by_family(evaluator_target_rows)
    public_rows = _rows_for_class(taxonomy_rows, "public_reference_usable")
    fresh_rows = _rows_for_class(taxonomy_rows, "fresh_source_diverse_candidate")
    seed_rows = _rows_for_class(taxonomy_rows, "source_singleton_seed")
    rows: list[dict[str, Any]] = []
    covered = 0
    for index, target_family in enumerate(REQUIRED_TARGET_FAMILIES, start=1):
        target_row = by_family.get(target_family, {})
        actor_visible_allowed = _bool(target_row.get("actor_visible_allowed"))
        status_pass = (
            _bool(target_row.get("status_pass"))
            and bool(target_row.get("available_columns", ""))
            and not actor_visible_allowed
        )
        fresh_available_count = sum(
            1 for row in fresh_rows if _bool(row.get("future_capability_targets_available"))
        )
        if status_pass and fresh_available_count:
            covered += 1
        rows.append(
            {
                "target_coverage_row_id": f"target-{index:03d}",
                "target_family": target_family,
                "required_columns": target_row.get("required_columns", ""),
                "available_columns": target_row.get("available_columns", ""),
                "public_reference_available_count": sum(
                    1
                    for row in public_rows
                    if _bool(row.get("future_capability_targets_available"))
                ),
                "fresh_candidate_available_count": fresh_available_count,
                "source_singleton_seed_available_count": sum(
                    1 for row in seed_rows if _bool(row.get("future_capability_targets_available"))
                ),
                "actor_visible_allowed": actor_visible_allowed,
                "target_scope": "evaluator_only_future_capability_targets",
                "status_pass": status_pass,
                "failure_type": ""
                if status_pass
                else (
                    "actor_visible_target_contract_violation"
                    if actor_visible_allowed
                    else "target_family_unavailable"
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows, covered


def _split_contract_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    split_specs = (
        (
            "public_reference_fit",
            "public_reference_usable",
            "schema_fit_calibration_only_no_validation_or_paper_proof",
            False,
            False,
            False,
            False,
        ),
        (
            "fresh_panel_candidate",
            "fresh_source_diverse_candidate",
            "candidate_surface_for_m2903_audit_only_no_quality_claim",
            False,
            False,
            False,
            False,
        ),
        (
            "source_singleton_seed",
            "source_singleton_seed",
            "repair_seed_gap_analysis_only",
            False,
            False,
            False,
            False,
        ),
        (
            "guard_exclusion",
            "guard_exclusion",
            "excluded_from_validation_paper_proof_and_ordinary_denominators",
            False,
            False,
            False,
            False,
        ),
        (
            "paper_holdout",
            "",
            "not_admitted_in_m2902_preflight",
            False,
            False,
            False,
            False,
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, (
        split_name,
        row_class,
        allowed_usage,
        paper_holdout_admitted,
        validation_allowed,
        model_quality_allowed,
        ordinary_allowed,
    ) in enumerate(split_specs, start=1):
        class_rows = _rows_for_class(taxonomy_rows, row_class) if row_class else []
        rows.append(
            {
                "split_row_id": f"split-{index:03d}",
                "split_name": split_name,
                "row_class": row_class,
                "task_count": len(class_rows),
                "profile_task_count": _profile_task_count(class_rows),
                "paper_holdout_admitted": paper_holdout_admitted,
                "validation_denominator_allowed": validation_allowed,
                "model_quality_denominator_allowed": model_quality_allowed,
                "ordinary_success_denominator_allowed": ordinary_allowed,
                "allowed_usage": allowed_usage,
                "status_pass": (
                    not paper_holdout_admitted
                    and not validation_allowed
                    and not model_quality_allowed
                    and not ordinary_allowed
                ),
                "failure_type": "",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _missing_requirements(row: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if _int(row.get("candidate_artifact_count")) < 2:
        missing.append("candidate_artifact_count>=2")
    if _int(row.get("source_family_tag_count")) < 2:
        missing.append("source_family_tag_count>=2")
    if _int(row.get("diagnostic_artifact_count")) < 2:
        missing.append("diagnostic_artifact_count>=2")
    if not _bool(row.get("required_profiles_present")):
        missing.append("required_profiles_present")
    if not _bool(row.get("config_checkpoint_complete")):
        missing.append("config_checkpoint_complete")
    if not _bool(row.get("deployable_history_features_available")):
        missing.append("deployable_history_features_available")
    if not _bool(row.get("future_capability_targets_available")):
        missing.append("future_capability_targets_available")
    if not _bool(row.get("actor_contract_shape_72_action_3")):
        missing.append("actor_contract_shape_72_action_3")
    if _bool(row.get("hidden_oracle_actor_input_required")):
        missing.append("hidden_oracle_actor_input_required_false")
    if _bool(row.get("future_target_actor_input_required")):
        missing.append("future_target_actor_input_required_false")
    if _bool(row.get("evaluator_targets_actor_visible")):
        missing.append("evaluator_targets_actor_visible_false")
    return missing or ["panel_level_design_target_gap"]


def _seed_gap_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gap_candidates = [
        row
        for row in taxonomy_rows
        if row["source_row_class"] in {"source_singleton_seed", "fresh_panel_gap"}
    ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(gap_candidates, start=1):
        rows.append(
            {
                "seed_gap_row_id": f"seed-gap-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "source_row_class": row.get("source_row_class", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "env_template_family": row.get("env_template_family", ""),
                "missing_requirement": _join(_missing_requirements(row)),
                "repair_route": (
                    "source_acquisition_or_candidate_support_materialization_before_claim"
                ),
                "may_seed_future_panel": True,
                "paper_proof_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _guard_exclusion_rows(taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guard_rows = _rows_for_class(taxonomy_rows, "guard_exclusion")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(guard_rows, start=1):
        rows.append(
            {
                "guard_exclusion_row_id": f"guard-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "env_template_family": row.get("env_template_family", ""),
                "diagnostic_artifact_tags": row.get("diagnostic_artifact_tags", ""),
                "exclusion_reason": row.get("classification_reason", ""),
                "paper_proof_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _claim_rows() -> list[dict[str, Any]]:
    claim_specs = (
        (
            "model_quality",
            "m2903_positive_audit_plus_later_holdout_validation",
        ),
        (
            "paper_claim",
            "paper_holdout_validation_and_claim_table_audit",
        ),
        (
            "finite_window_vs_gru",
            "paired_same_case_model_quality_evidence",
        ),
        (
            "level3_self_identification",
            "self_identification_gate_and_artifact_trace",
        ),
        (
            "driver_performance",
            "full_driver_rollout_gate",
        ),
        (
            "current_sim_verdict",
            "current_sim_validation_gate",
        ),
        (
            "high_fidelity_validation",
            "high_fidelity_validation_gate",
        ),
        (
            "full_ideal_driver_gate",
            "full_ideal_driver_gate_sequence",
        ),
    )
    return [
        {
            "claim_id": f"claim-{index:03d}",
            "claim_family": claim_family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (claim_family, evidence_required) in enumerate(claim_specs, start=1)
    ]


def _rollback_rows(
    taxonomy_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
    targets_satisfied: bool,
) -> list[dict[str, Any]]:
    fresh_rows = _rows_for_class(taxonomy_rows, "fresh_source_diverse_candidate")
    admitted_boundary_ok = all(
        _bool(row.get("actor_contract_shape_72_action_3"))
        and not _bool(row.get("hidden_oracle_actor_input_required"))
        and not _bool(row.get("future_target_actor_input_required"))
        and not _bool(row.get("evaluator_targets_actor_visible"))
        for row in fresh_rows
    )
    split_boundary_ok = all(
        not _bool(row.get("paper_holdout_admitted"))
        and not _bool(row.get("validation_denominator_allowed"))
        and not _bool(row.get("model_quality_denominator_allowed"))
        and not _bool(row.get("ordinary_success_denominator_allowed"))
        for row in split_rows
    )
    no_claims = all(not _bool(row.get("claim_made")) for row in claim_rows)
    specs = (
        (
            "actor_contract_preserved",
            admitted_boundary_ok,
            f"{P0_OBSERVATION_DIM}x{ACTION_DIM}",
            "72x3 actor input/action contract and evaluator-only target boundary",
        ),
        (
            "public_reference_not_validation",
            split_boundary_ok,
            "all_split_denominators_false",
            "public reference and fresh candidates stay out of validation/paper denominators",
        ),
        (
            "source_singleton_and_guard_excluded",
            split_boundary_ok,
            "source_singleton_guard_denominators_false",
            "seed/guard rows excluded from proof and ordinary denominators",
        ),
        (
            "claims_suppressed",
            no_claims,
            "no_claim_rows_true",
            "no model-quality/paper/driver/self-id claim in M2902",
        ),
        (
            "negative_design_result_routed_without_weakened_criteria",
            True,
            f"fresh_source_diverse_targets_satisfied={targets_satisfied}",
            "route positive or negative result to M2903 audit without threshold changes",
        ),
        (
            "follow_up_manifest_registered",
            follow_up_manifest.exists(),
            str(follow_up_manifest),
            "M2903 result-audit manifest path",
        ),
    )
    rows: list[dict[str, Any]] = []
    for index, (family, status_pass, observed, expected) in enumerate(specs, start=1):
        rows.append(
            {
                "rollback_id": f"rollback-{index:03d}",
                "rollback_family": family,
                "status_pass": status_pass,
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status_pass else f"{family}_failed",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _materialization_gate_rows(
    input_paths_present: dict[str, bool],
    taxonomy_rows: list[dict[str, Any]],
    source_diversity_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    seed_gap_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    rollback_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
    targets_satisfied: bool,
) -> list[dict[str, Any]]:
    input_ok = all(input_paths_present.values())
    split_ok = all(_bool(row.get("status_pass")) for row in split_rows)
    target_accounted = len(target_rows) == len(REQUIRED_TARGET_FAMILIES) and all(
        _bool(row.get("status_pass")) and not _bool(row.get("actor_visible_allowed"))
        for row in target_rows
    )
    rollback_ok = all(_bool(row.get("status_pass")) for row in rollback_rows)
    claim_ok = all(not _bool(row.get("claim_made")) for row in claim_rows)
    specs = (
        (
            "input_artifacts_present",
            input_ok,
            json.dumps(input_paths_present, sort_keys=True),
            "all declared M2901/M2884/M2887/M2898 inputs exist",
        ),
        (
            "panel_taxonomy_materialized",
            bool(taxonomy_rows),
            str(len(taxonomy_rows)),
            "nonempty panel taxonomy rows",
        ),
        (
            "source_diversity_accounted",
            bool(source_diversity_rows),
            str(len(source_diversity_rows)),
            "source diversity rows written for every row class",
        ),
        (
            "split_contract_preserves_preflight_only_boundary",
            split_ok,
            json.dumps(
                {
                    row["split_name"]: row["ordinary_success_denominator_allowed"]
                    for row in split_rows
                },
                sort_keys=True,
            ),
            "no paper holdout/validation/model-quality/ordinary denominator admitted",
        ),
        (
            "target_coverage_accounted",
            target_accounted,
            str(len(target_rows)),
            f"{len(REQUIRED_TARGET_FAMILIES)} evaluator-only target families",
        ),
        (
            "seed_and_guard_accounting_written",
            bool(seed_gap_rows) or bool(guard_rows),
            json.dumps(
                {"seed_gap_rows": len(seed_gap_rows), "guard_rows": len(guard_rows)},
                sort_keys=True,
            ),
            "seed gap and guard exclusion rows are explicit",
        ),
        (
            "rollback_boundaries_pass",
            rollback_ok,
            str(len(rollback_rows)),
            "rollback rows preserve actor/split/claim boundaries",
        ),
        (
            "claim_suppression_pass",
            claim_ok,
            str(len(claim_rows)),
            "all claim rows remain false",
        ),
        (
            "design_targets_reported_without_promotion",
            True,
            f"fresh_source_diverse_targets_satisfied={targets_satisfied}",
            "positive and negative diversity outcomes are reporting only in M2902",
        ),
        (
            "follow_up_manifest_written",
            follow_up_manifest.exists(),
            str(follow_up_manifest),
            "M2903 result-audit manifest written",
        ),
    )
    return [
        {
            "gate_id": f"gate-{index:03d}",
            "gate_family": family,
            "status_pass": status_pass,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if status_pass else f"{family}_failed",
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, status_pass, observed, expected) in enumerate(specs, start=1)
    ]


def build_follow_up_manifest(
    *,
    output_dir: Path,
    summary_path: Path,
    decision: str,
    fresh_source_diverse_targets_satisfied: bool,
) -> dict[str, Any]:
    command = (
        "PYTHONPATH=src python -m autodrift.paper_route_l0_l1_l2_l3_capability_prediction_"
        "fresh_source_diverse_panel_materialization_result_audit "
        "--m2902-summary "
        f"{summary_path} "
        "--m2902-dir "
        f"{output_dir} "
        "--output-doc docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
        "fresh-source-diverse-panel-materialization-result-audit.md"
    )
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_milestone": DEFAULT_MILESTONE,
        "type": "gate",
        "gate_tier": "process",
        "status": "pending",
        "risk": "low",
        "promotion_decision": "not_applicable",
        "hypothesis": (
            "A bounded result audit can accept or reject the M2902 fresh/source-diverse "
            "panel materialization preflight before repair source acquisition validation "
            "ranking model-quality paper or self-ID claims."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "panel_row_taxonomy_rows.csv"),
                str(output_dir / "source_diversity_rows.csv"),
                str(output_dir / "split_contract_rows.csv"),
                str(output_dir / "target_coverage_rows.csv"),
                str(output_dir / "seed_gap_rows.csv"),
                str(output_dir / "guard_exclusion_rows.csv"),
                str(output_dir / "materialization_gate_rows.csv"),
                str(output_dir / "rollback_rows.csv"),
                str(output_dir / "claim_rows.csv"),
                "docs/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight.json",
                "experiments/manifests/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.json",
            ],
            "parent_objective": [
                "audit M2902 materialized panel taxonomy and preserve positive or negative diversity result without changing thresholds"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design",
                "m2884-m2888 capability-prediction panel inventory and dataset materialization chain",
            ],
            "blocked_by": [
                "M2902 is a materialization preflight only",
                "fresh/source-diverse targets may be unsatisfied and must route to repair or stop instead of proof",
                "public reference source-singleton and guard rows must remain out of validation paper proof and ordinary denominators",
            ],
            "supersedes": [
                "treating M2902 materialization as model-quality evidence without audit",
                "treating source-singleton or guard rows as paper proof",
            ],
            "invalidates": [],
        },
        "review_artifact": (
            "docs/reviews/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
            "fresh-source-diverse-panel-materialization-result-audit.md"
        ),
        "public_gates": [
            "M2903 must audit M2902 summary and all required artifact row counts",
            "M2903 must preserve the exact M2902 diversity result without weakening thresholds",
            "M2903 must keep public reference source-singleton and guard rows out of validation paper proof and ordinary denominators",
            "M2903 must preserve actor 72/action 3 no hidden/oracle input no future-target actor input and evaluator-only target boundaries",
            "M2903 must choose audit repair source acquisition pivot or stop without claiming model quality driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate fit train rank promote publish or select a winner",
            "do not change actor input or action contract",
            "do not expose hidden dynamics oracle labels future targets route labels or verdict labels to actor input",
            "do not downgrade source-diversity thresholds to force a pass",
            "do not treat public reference source-singleton or guard rows as model-quality or paper denominators",
            "do not claim prediction quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "workflow_synthesis": {
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_fresh_panel_expansion",
            "evidence_axis": "fresh_source_diverse_panel_materialization_result_audit",
            "evidence_increment": "audits M2902 materialized panel accounting rows before any model-quality interpretation",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if M2902 summary or row artifacts are internally inconsistent",
                "stop if actor target split holdout or exclusion boundaries fail",
                "stop if source-diversity thresholds are weakened",
                "stop if M2903 would claim model quality driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
            ],
            "fallback_plan": [
                "route to panel-source repair if diversity targets are unsatisfied",
                "route to later model-quality design only if audit accepts a sufficient fresh/source-diverse surface",
                "route to Route A or Route C if Route B panel expansion remains unavailable",
                "stop the branch if claim-safe repair is not available",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2902 registered a materialization result that needs audit before any next route",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B fresh/source-diverse panel materialization result audit",
            "admission_evidence": [
                "M2902 status_pass true gate_matrix_pass true materialized panel taxonomy source-diversity split target seed-gap guard rollback and claim rows",
                "M2901 defines source-diversity target coverage split holdout rollback and audit semantics",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion",
                "no additional optimizer step and no promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.md",
                "docs/reviews/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.md",
                "M2903 status queue scoreboard research log and review",
                "one bounded follow-up repair design synthesis or stop manifest",
            ],
            "next_stage_criteria": [
                "M2902 summary and all row artifacts are audited",
                "negative or positive diversity result is preserved exactly",
                "one next audit repair pivot or stop decision is selected",
                "target actor split holdout and exclusion boundaries remain preserved",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2903 audits panel accounting only and cannot substitute current-frame evidence for history necessity.",
            "history_necessity_tests": [
                "None in M2903; later evidence requires an accepted source-diverse panel and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2884-M2902 Route B capability-prediction panel inventory dataset contract fitting design and fresh-panel materialization chain.",
            "negative_result_policy": "If M2902 shows insufficient fresh/source-diverse coverage, preserve the negative result and route to panel-source repair or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "bounded materialization result-audit outcome",
                "fresh/source-diverse criteria satisfied or not satisfied as reported by M2902",
                "bounded follow-up repair pivot or stop decision",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a newly materialized panel accounting surface before choosing repair or later validation design",
            "paper_verdict_delta": "no verdict; preserves the prerequisite audit for any later model-quality route",
            "must_synthesize_if": [
                "M2903 cannot choose between repair Route A pivot Route C pivot or stop",
                "M2903 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2903 would let source-singleton or guard rows enter paper proof",
                "M2903 would expose evaluator-only future targets to actor input",
                "M2903 fails source-diversity criteria and another repair-only loop is proposed",
            ],
        },
        "failure_criteria": [
            "M2903 changes M2902 row classifications or diversity thresholds to force a pass",
            "M2903 admits public reference source-singleton or guard rows into validation paper proof or ordinary denominators",
            "M2903 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2903 resets steps rolls out replays validates fits trains ranks promotes or executes policy action",
            "M2903 fails to select a bounded repair design synthesis pivot or stop route after auditing M2902",
        ],
        "decision_rule": (
            "Accept M2902 only if all materialization artifacts are complete internally consistent "
            "and claim-safe; preserve a negative diversity result as repair/source-acquisition "
            "input rather than model-quality evidence."
        ),
        "commands": [
            {
                "name": "fresh_source_diverse_panel_materialization_result_audit",
                "command": command,
            }
        ],
        "required_artifacts": [
            {
                "path": (
                    "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
                    "fresh-source-diverse-panel-materialization-result-audit.md"
                ),
                "type": "markdown",
            }
        ],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir),
            "docs/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.md",
            "docs/m2900-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-audit-synthesis-or-model-quality-design.md",
        ],
        "m2902_result": {
            "m2902_summary": str(summary_path),
            "m2902_output_dir": str(output_dir),
            "m2902_decision": decision,
            "fresh_source_diverse_targets_satisfied": fresh_source_diverse_targets_satisfied,
        },
        "command": command,
        "success_criteria": [
            {
                "name": "m2902_summary_audited",
                "description": "Audit summary.json and all required M2902 artifact rows for internal consistency.",
                "artifact": (
                    "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
                    "fresh-source-diverse-panel-materialization-result-audit.md"
                ),
            },
            {
                "name": "negative_or_positive_diversity_result_preserved",
                "description": "If diversity targets fail, route to repair/source acquisition; if they pass, route to later claim-safe validation design.",
                "artifact": str(summary_path),
            },
            {
                "name": "claim_boundary_preserved",
                "description": "No paper/model-quality/driver/current-sim/full-driver/self-ID claim is made from M2902.",
                "artifact": str(summary_path),
            },
        ],
        "expected_artifacts": [
            (
                "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
                "fresh-source-diverse-panel-materialization-result-audit.md"
            ),
        ],
        "review": {
            "required": True,
            "artifact": (
                "docs/reviews/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
                "fresh-source-diverse-panel-materialization-result-audit-review.md"
            ),
        },
        "scoreboard_checkpoint": (
            "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-"
            "fresh-source-diverse-panel-materialization-result-audit.md"
        ),
        "paper_route": {
            "route_id": (
                "paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
                "panel_materialization_result_audit"
            ),
            "claim_scope": CLAIM_SCOPE,
            "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        },
    }


def write_preflight_artifacts(
    *,
    m2901_design: Path,
    m2884_dir: Path,
    m2887_dir: Path,
    m2898_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_panel_path = m2884_dir / "candidate_panel_rows.csv"
    source_inventory_path = m2884_dir / "source_inventory_rows.csv"
    profile_task_path = m2887_dir / "profile_task_rows.csv"
    evaluator_target_path = m2887_dir / "evaluator_target_rows.csv"
    m2887_summary_path = m2887_dir / "summary.json"
    m2898_summary_path = m2898_dir / "summary.json"
    input_paths_present = {
        "m2901_design": m2901_design.exists(),
        "m2884_candidate_panel_rows": candidate_panel_path.exists(),
        "m2884_source_inventory_rows": source_inventory_path.exists(),
        "m2887_profile_task_rows": profile_task_path.exists(),
        "m2887_evaluator_target_rows": evaluator_target_path.exists(),
        "m2887_summary": m2887_summary_path.exists(),
        "m2898_summary": m2898_summary_path.exists(),
    }

    candidate_rows = _read_csv_rows(candidate_panel_path)
    source_inventory_rows = _read_csv_rows(source_inventory_path)
    profile_task_rows = _read_csv_rows(profile_task_path)
    evaluator_target_rows = _read_csv_rows(evaluator_target_path)
    m2887_summary = _read_json(m2887_summary_path)
    m2898_summary = _read_json(m2898_summary_path)

    taxonomy_rows = _panel_taxonomy_rows(candidate_rows)
    target_rows, target_family_coverage_count = _target_coverage_rows(
        evaluator_target_rows,
        taxonomy_rows,
    )
    source_diversity_rows, fresh_metrics, targets_satisfied = _source_diversity_rows(
        taxonomy_rows,
        target_family_coverage_count,
    )
    split_rows = _split_contract_rows(taxonomy_rows)
    seed_rows = _seed_gap_rows(taxonomy_rows)
    guard_rows = _guard_exclusion_rows(taxonomy_rows)
    claim_rows = _claim_rows()

    summary_path = output_dir / "summary.json"
    follow_up_payload = build_follow_up_manifest(
        output_dir=output_dir,
        summary_path=summary_path,
        decision=(
            "fresh_panel_materialized_candidate_surface_route_to_m2903_result_audit"
            if targets_satisfied
            else "fresh_panel_materialized_insufficient_diversity_route_to_m2903_result_audit"
        ),
        fresh_source_diverse_targets_satisfied=targets_satisfied,
    )
    _write_json(follow_up_manifest, follow_up_payload)

    rollback_rows = _rollback_rows(
        taxonomy_rows,
        split_rows,
        claim_rows,
        follow_up_manifest,
        targets_satisfied,
    )
    gate_rows = _materialization_gate_rows(
        input_paths_present,
        taxonomy_rows,
        source_diversity_rows,
        split_rows,
        target_rows,
        seed_rows,
        guard_rows,
        rollback_rows,
        claim_rows,
        follow_up_manifest,
        targets_satisfied,
    )

    row_class_counts = Counter(row["source_row_class"] for row in taxonomy_rows)
    status_pass = all(_bool(row.get("status_pass")) for row in gate_rows)
    gate_matrix_pass = status_pass
    decision = (
        "fresh_panel_materialized_candidate_surface_route_to_m2903_result_audit"
        if targets_satisfied
        else "fresh_panel_materialized_insufficient_diversity_route_to_m2903_result_audit"
    )
    if not status_pass:
        decision = "fresh_panel_materialization_preflight_incomplete"

    artifacts = {
        "summary": str(summary_path),
        "panel_row_taxonomy_rows": str(output_dir / "panel_row_taxonomy_rows.csv"),
        "source_diversity_rows": str(output_dir / "source_diversity_rows.csv"),
        "split_contract_rows": str(output_dir / "split_contract_rows.csv"),
        "target_coverage_rows": str(output_dir / "target_coverage_rows.csv"),
        "seed_gap_rows": str(output_dir / "seed_gap_rows.csv"),
        "guard_exclusion_rows": str(output_dir / "guard_exclusion_rows.csv"),
        "materialization_gate_rows": str(output_dir / "materialization_gate_rows.csv"),
        "rollback_rows": str(output_dir / "rollback_rows.csv"),
        "claim_rows": str(output_dir / "claim_rows.csv"),
        "run_state": str(output_dir / "run_state.json"),
        "follow_up_manifest": str(follow_up_manifest),
    }
    row_counts = {
        "panel_row_taxonomy_rows": len(taxonomy_rows),
        "source_diversity_rows": len(source_diversity_rows),
        "split_contract_rows": len(split_rows),
        "target_coverage_rows": len(target_rows),
        "seed_gap_rows": len(seed_rows),
        "guard_exclusion_rows": len(guard_rows),
        "materialization_gate_rows": len(gate_rows),
        "rollback_rows": len(rollback_rows),
        "claim_rows": len(claim_rows),
    }
    summary = {
        "milestone": DEFAULT_MILESTONE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "fresh_source_diverse_targets_satisfied": targets_satisfied,
        "row_counts": row_counts,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "input_paths_present": input_paths_present,
        "m2901_design": str(m2901_design),
        "m2884_dir": str(m2884_dir),
        "m2887_dir": str(m2887_dir),
        "m2898_dir": str(m2898_dir),
        "m2884_source_inventory_row_count": len(source_inventory_rows),
        "m2887_profile_task_row_count": len(profile_task_rows),
        "m2887_status_pass": bool(m2887_summary.get("status_pass")),
        "m2887_gate_matrix_pass": bool(m2887_summary.get("gate_matrix_pass")),
        "m2898_status_pass": bool(m2898_summary.get("status_pass")),
        "m2898_gate_matrix_pass": bool(m2898_summary.get("gate_matrix_pass")),
        "public_reference_usable_count": row_class_counts["public_reference_usable"],
        "fresh_candidate_task_count": fresh_metrics["task_count"],
        "fresh_candidate_profile_task_count": fresh_metrics["profile_task_count"],
        "source_singleton_seed_count": row_class_counts["source_singleton_seed"],
        "guard_exclusion_count": row_class_counts["guard_exclusion"],
        "fresh_panel_gap_count": row_class_counts["fresh_panel_gap"],
        "rejected_boundary_violation_count": row_class_counts[
            "rejected_boundary_violation"
        ],
        "target_family_coverage_count": fresh_metrics["target_family_coverage_count"],
        "source_family_count": fresh_metrics["source_family_count"],
        "task_family_count": fresh_metrics["task_family_count"],
        "max_single_source_family_share": fresh_metrics["max_single_source_family_share"],
        "max_single_task_family_share": fresh_metrics["max_single_task_family_share"],
        "design_targets": DESIGN_TARGETS,
        "paper_holdout_admitted": False,
        "preflight_only_split": True,
        "actor_contract_shape_72_action_3": True,
        "observation_dim": P0_OBSERVATION_DIM,
        "action_dim": ACTION_DIM,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "evaluator_targets_actor_visible": any(
            _bool(row.get("actor_visible_allowed")) for row in target_rows
        ),
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
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
    }

    run_state = {
        "milestone": DEFAULT_MILESTONE,
        "status": "complete" if status_pass else "incomplete",
        "decision": decision,
        "fresh_source_diverse_targets_satisfied": targets_satisfied,
        "summary_path": str(summary_path),
        "follow_up_manifest": str(follow_up_manifest),
        "claim_boundary": CLAIM_SCOPE,
    }

    _write_csv(Path(artifacts["panel_row_taxonomy_rows"]), PANEL_TAXONOMY_FIELDNAMES, taxonomy_rows)
    _write_csv(
        Path(artifacts["source_diversity_rows"]),
        SOURCE_DIVERSITY_FIELDNAMES,
        source_diversity_rows,
    )
    _write_csv(Path(artifacts["split_contract_rows"]), SPLIT_CONTRACT_FIELDNAMES, split_rows)
    _write_csv(Path(artifacts["target_coverage_rows"]), TARGET_COVERAGE_FIELDNAMES, target_rows)
    _write_csv(Path(artifacts["seed_gap_rows"]), SEED_GAP_FIELDNAMES, seed_rows)
    _write_csv(Path(artifacts["guard_exclusion_rows"]), GUARD_EXCLUSION_FIELDNAMES, guard_rows)
    _write_csv(
        Path(artifacts["materialization_gate_rows"]),
        MATERIALIZATION_GATE_FIELDNAMES,
        gate_rows,
    )
    _write_csv(Path(artifacts["rollback_rows"]), ROLLBACK_FIELDNAMES, rollback_rows)
    _write_csv(Path(artifacts["claim_rows"]), CLAIM_FIELDNAMES, claim_rows)
    _write_json(Path(artifacts["run_state"]), run_state)
    _write_json(summary_path, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2901-design", type=Path, default=DEFAULT_M2901_DESIGN)
    parser.add_argument("--m2884-dir", type=Path, default=DEFAULT_M2884_DIR)
    parser.add_argument("--m2887-dir", type=Path, default=DEFAULT_M2887_DIR)
    parser.add_argument("--m2898-dir", type=Path, default=DEFAULT_M2898_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()

    summary = write_preflight_artifacts(
        m2901_design=args.m2901_design,
        m2884_dir=args.m2884_dir,
        m2887_dir=args.m2887_dir,
        m2898_dir=args.m2898_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
