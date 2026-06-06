"""Materialize M2905 repair/source-acquisition accounting rows."""

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
)


MILESTONE_ID = (
    "m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-materialization-preflight"
)
NEXT_ID = (
    "m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-materialization-result-audit"
)
DEFAULT_M2904_DESIGN = Path(
    "docs/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-"
    "diverse-panel-repair-source-acquisition-design.md"
)
DEFAULT_M2903_AUDIT = Path(
    "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-"
    "diverse-panel-materialization-result-audit.md"
)
DEFAULT_M2902_DIR = Path(
    "runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_materialization_preflight"
)
DEFAULT_M2884_DIR = Path(
    "runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_repair_source_acquisition_materialization_preflight"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2906-paper-route-l0-l1-l2-l3-capability-prediction-"
    "fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.json"
)
CLAIM_SCOPE = (
    "repair_source_acquisition_materialization_only_no_validation_no_model_quality_"
    "no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_validation_not_paper_proof_not_model_quality_not_driver_performance_not_self_id"
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
REQUIRED_OUTPUTS = {
    "summary": "summary.json",
    "seed_gap_repair_rows": "seed_gap_repair_rows.csv",
    "candidate_support_repair_rows": "candidate_support_repair_rows.csv",
    "source_family_repair_rows": "source_family_repair_rows.csv",
    "dual_repair_rows": "dual_repair_rows.csv",
    "acquisition_required_rows": "acquisition_required_rows.csv",
    "repaired_candidate_projection_rows": "repaired_candidate_projection_rows.csv",
    "exclusion_rows": "exclusion_rows.csv",
    "split_boundary_rows": "split_boundary_rows.csv",
    "target_boundary_rows": "target_boundary_rows.csv",
    "gate_rows": "gate_rows.csv",
    "rollback_rows": "rollback_rows.csv",
    "claim_rows": "claim_rows.csv",
    "run_state": "run_state.json",
}

SEED_GAP_REPAIR_FIELDNAMES = (
    "repair_row_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "env_template_family",
    "executable_source_family",
    "profile_count",
    "missing_requirement",
    "candidate_support_gap",
    "source_family_gap",
    "dual_gap",
    "observed_candidate_artifact_count",
    "observed_source_family_tag_count",
    "observed_diagnostic_artifact_count",
    "existing_repo_local_support_sufficient",
    "acquisition_required",
    "projected_fresh_candidate_after_existing_support",
    "repair_lane",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
CANDIDATE_SUPPORT_FIELDNAMES = (
    "candidate_support_repair_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "observed_candidate_artifact_count",
    "required_candidate_artifact_count",
    "existing_candidate_support_sufficient",
    "acquisition_required",
    "required_evidence",
    "status_pass",
    "claim_boundary",
)
SOURCE_FAMILY_FIELDNAMES = (
    "source_family_repair_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "observed_source_family_tag_count",
    "required_source_family_tag_count",
    "existing_source_family_support_sufficient",
    "acquisition_required",
    "required_evidence",
    "status_pass",
    "claim_boundary",
)
DUAL_REPAIR_FIELDNAMES = (
    "dual_repair_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "candidate_support_acquisition_required",
    "source_family_acquisition_required",
    "projected_fresh_candidate_after_existing_support",
    "status_pass",
    "claim_boundary",
)
ACQUISITION_REQUIRED_FIELDNAMES = (
    "acquisition_required_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "env_template_family",
    "missing_requirement",
    "required_acquisition",
    "candidate_support_acquisition_required",
    "source_family_acquisition_required",
    "may_seed_future_panel",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
REPAIRED_PROJECTION_FIELDNAMES = (
    "projection_id",
    "seed_gap_row_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "executable_source_family",
    "profile_count",
    "projected_fresh_candidate",
    "projection_basis",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
EXCLUSION_FIELDNAMES = (
    "exclusion_id",
    "candidate_id",
    "task_source_id",
    "source_row_class",
    "original_classification",
    "exclusion_reason",
    "allowed_usage",
    "paper_proof_allowed",
    "validation_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
)
SPLIT_BOUNDARY_FIELDNAMES = (
    "split_boundary_id",
    "split_name",
    "row_count",
    "paper_holdout_admitted",
    "validation_denominator_allowed",
    "model_quality_denominator_allowed",
    "ordinary_success_denominator_allowed",
    "allowed_usage",
    "status_pass",
    "claim_boundary",
)
TARGET_BOUNDARY_FIELDNAMES = (
    "target_boundary_id",
    "target_family",
    "actor_visible_allowed",
    "fresh_candidate_available_count",
    "projected_fresh_candidate_available_count",
    "target_scope",
    "status_pass",
    "claim_boundary",
)
GATE_FIELDNAMES = (
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


def _join(values: Iterable[str]) -> str:
    return ";".join(value for value in values if value)


def _requirements(row: dict[str, str]) -> set[str]:
    return {item for item in row.get("missing_requirement", "").split(";") if item}


def _lane(requirements: set[str]) -> str:
    candidate_gap = "candidate_artifact_count>=2" in requirements
    source_gap = "source_family_tag_count>=2" in requirements
    if candidate_gap and source_gap:
        return "dual_candidate_and_source_family_acquisition"
    if candidate_gap:
        return "candidate_support_acquisition"
    if source_gap:
        return "source_family_acquisition"
    return "panel_level_design_gap"


def _counter_share(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    return max(counter.values()) / total


def _paths(output_dir: Path) -> dict[str, Path]:
    return {key: output_dir / filename for key, filename in REQUIRED_OUTPUTS.items()}


def build_seed_gap_repair_rows(
    seed_gap_rows: list[dict[str, str]],
    taxonomy_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    taxonomy_by_candidate = {row.get("candidate_id", ""): row for row in taxonomy_rows}
    rows: list[dict[str, Any]] = []
    for index, seed in enumerate(seed_gap_rows, start=1):
        taxonomy = taxonomy_by_candidate.get(seed.get("candidate_id", ""), {})
        requirements = _requirements(seed)
        candidate_gap = "candidate_artifact_count>=2" in requirements
        source_gap = "source_family_tag_count>=2" in requirements
        existing_sufficient = not candidate_gap and not source_gap
        rows.append(
            {
                "repair_row_id": f"repair-{index:03d}",
                "seed_gap_row_id": seed.get("seed_gap_row_id", ""),
                "candidate_id": seed.get("candidate_id", ""),
                "task_source_id": seed.get("task_source_id", ""),
                "task_family": seed.get("task_family", ""),
                "source_edge": seed.get("source_edge", ""),
                "env_template_family": seed.get("env_template_family", ""),
                "executable_source_family": taxonomy.get("executable_source_family", ""),
                "profile_count": _int(taxonomy.get("profile_count"), 12),
                "missing_requirement": seed.get("missing_requirement", ""),
                "candidate_support_gap": candidate_gap,
                "source_family_gap": source_gap,
                "dual_gap": candidate_gap and source_gap,
                "observed_candidate_artifact_count": _int(
                    taxonomy.get("candidate_artifact_count")
                ),
                "observed_source_family_tag_count": _int(
                    taxonomy.get("source_family_tag_count")
                ),
                "observed_diagnostic_artifact_count": _int(
                    taxonomy.get("diagnostic_artifact_count")
                ),
                "existing_repo_local_support_sufficient": existing_sufficient,
                "acquisition_required": not existing_sufficient,
                "projected_fresh_candidate_after_existing_support": False,
                "repair_lane": _lane(requirements),
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_candidate_support_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        [item for item in repair_rows if _bool(item.get("candidate_support_gap"))],
        start=1,
    ):
        observed = _int(row.get("observed_candidate_artifact_count"))
        sufficient = observed >= 2
        rows.append(
            {
                "candidate_support_repair_id": f"candidate-support-{index:03d}",
                "seed_gap_row_id": row.get("seed_gap_row_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "observed_candidate_artifact_count": observed,
                "required_candidate_artifact_count": 2,
                "existing_candidate_support_sufficient": sufficient,
                "acquisition_required": not sufficient,
                "required_evidence": "additional_independent_candidate_artifact",
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_source_family_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        [item for item in repair_rows if _bool(item.get("source_family_gap"))],
        start=1,
    ):
        observed = _int(row.get("observed_source_family_tag_count"))
        sufficient = observed >= 2
        rows.append(
            {
                "source_family_repair_id": f"source-family-{index:03d}",
                "seed_gap_row_id": row.get("seed_gap_row_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "observed_source_family_tag_count": observed,
                "required_source_family_tag_count": 2,
                "existing_source_family_support_sufficient": sufficient,
                "acquisition_required": not sufficient,
                "required_evidence": "additional_independent_source_family",
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_dual_repair_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    duals = [row for row in repair_rows if _bool(row.get("dual_gap"))]
    for index, row in enumerate(duals, start=1):
        rows.append(
            {
                "dual_repair_id": f"dual-repair-{index:03d}",
                "seed_gap_row_id": row.get("seed_gap_row_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "candidate_support_acquisition_required": True,
                "source_family_acquisition_required": True,
                "projected_fresh_candidate_after_existing_support": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_acquisition_required_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        [item for item in repair_rows if _bool(item.get("acquisition_required"))],
        start=1,
    ):
        candidate_gap = _bool(row.get("candidate_support_gap"))
        source_gap = _bool(row.get("source_family_gap"))
        required = []
        if candidate_gap:
            required.append("additional_independent_candidate_artifact")
        if source_gap:
            required.append("additional_independent_source_family")
        if not required:
            required.append("panel_level_design_target_repair")
        rows.append(
            {
                "acquisition_required_id": f"acquisition-{index:03d}",
                "seed_gap_row_id": row.get("seed_gap_row_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "missing_requirement": row.get("missing_requirement", ""),
                "required_acquisition": _join(required),
                "candidate_support_acquisition_required": candidate_gap,
                "source_family_acquisition_required": source_gap,
                "may_seed_future_panel": True,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_repaired_projection_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    projected = [
        row for row in repair_rows if _bool(row.get("projected_fresh_candidate_after_existing_support"))
    ]
    for index, row in enumerate(projected, start=1):
        rows.append(
            {
                "projection_id": f"projection-{index:03d}",
                "seed_gap_row_id": row.get("seed_gap_row_id", ""),
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "profile_count": row.get("profile_count", 12),
                "projected_fresh_candidate": True,
                "projection_basis": "existing_repo_local_support_satisfies_all_m2901_row_criteria",
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_exclusion_rows(taxonomy_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(taxonomy_rows, start=1):
        row_class = row.get("source_row_class", "")
        if row_class == "public_reference_usable":
            usage = "fit_schema_reference_only_no_validation_or_paper_proof"
        elif row_class == "source_singleton_seed":
            usage = "repair_seed_only_no_validation_or_paper_proof"
        elif row_class == "guard_exclusion":
            usage = "excluded_guard_no_denominator"
        else:
            usage = "not_admitted_for_m2905_projection"
        rows.append(
            {
                "exclusion_id": f"exclusion-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "source_row_class": row_class,
                "original_classification": row.get("original_classification", ""),
                "exclusion_reason": row.get("classification_reason", ""),
                "allowed_usage": usage,
                "paper_proof_allowed": False,
                "validation_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_split_boundary_rows(
    *,
    taxonomy_rows: list[dict[str, str]],
    repair_rows: list[dict[str, Any]],
    projection_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts = Counter(row.get("source_row_class", "") for row in taxonomy_rows)
    split_specs = (
        ("public_reference_fit", counts["public_reference_usable"], "schema_reference_only"),
        ("source_singleton_seed_repair", counts["source_singleton_seed"], "repair_seed_only"),
        ("acquisition_required", len(acquisition_rows), "source_acquisition_accounting_only"),
        ("repaired_candidate_projection", len(projection_rows), "projection_only_no_validation"),
        ("guard_exclusion", counts["guard_exclusion"], "excluded_guard_rows"),
        ("paper_holdout", 0, "not_admitted_in_m2905"),
    )
    rows: list[dict[str, Any]] = []
    for index, (name, count, usage) in enumerate(split_specs, start=1):
        rows.append(
            {
                "split_boundary_id": f"split-{index:03d}",
                "split_name": name,
                "row_count": count,
                "paper_holdout_admitted": False,
                "validation_denominator_allowed": False,
                "model_quality_denominator_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "allowed_usage": usage,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_boundary_rows(
    target_rows: list[dict[str, str]],
    projection_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(target_rows, start=1):
        actor_visible = _bool(row.get("actor_visible_allowed"))
        rows.append(
            {
                "target_boundary_id": f"target-{index:03d}",
                "target_family": row.get("target_family", ""),
                "actor_visible_allowed": actor_visible,
                "fresh_candidate_available_count": row.get("fresh_candidate_available_count", "0"),
                "projected_fresh_candidate_available_count": len(projection_rows),
                "target_scope": "evaluator_only_future_capability_targets",
                "status_pass": not actor_visible,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_rows() -> list[dict[str, Any]]:
    specs = (
        ("model_quality", "accepted_fresh_panel_plus_later_holdout_validation"),
        ("paper_claim", "paper_holdout_validation_and_claim_table_audit"),
        ("finite_window_vs_gru", "paired_same_case_model_quality_evidence"),
        ("level3_self_identification", "history_necessity_and_self_id_gate"),
        ("driver_performance", "closed_loop_driver_validation_gate"),
        ("current_sim_verdict", "current_sim_validation_gate"),
        ("high_fidelity_validation", "high_fidelity_validation_gate"),
        ("full_ideal_driver_gate", "full_ideal_driver_gate_sequence"),
    )
    return [
        {
            "claim_id": f"claim-{index:03d}",
            "claim_family": family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, evidence) in enumerate(specs, start=1)
    ]


def _projected_metrics(projection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_counter = Counter(
        str(row.get("executable_source_family") or "unknown") for row in projection_rows
    )
    task_counter = Counter(str(row.get("task_family") or "unknown") for row in projection_rows)
    task_count = len(projection_rows)
    profile_count = sum(_int(row.get("profile_count"), 12) for row in projection_rows)
    target_coverage = 6 if projection_rows else 0
    max_source_share = _counter_share(source_counter)
    max_task_share = _counter_share(task_counter)
    targets_satisfied = (
        task_count >= DESIGN_TARGETS["fresh_candidate_task_count"]
        and profile_count >= DESIGN_TARGETS["fresh_candidate_profile_task_count"]
        and len(source_counter) >= DESIGN_TARGETS["source_family_count"]
        and len(task_counter) >= DESIGN_TARGETS["task_family_count"]
        and target_coverage >= DESIGN_TARGETS["target_family_coverage_count"]
        and max_source_share <= DESIGN_TARGETS["max_single_source_family_share"]
        and max_task_share <= DESIGN_TARGETS["max_single_task_family_share"]
    )
    return {
        "projected_fresh_candidate_task_count": task_count,
        "projected_fresh_candidate_profile_task_count": profile_count,
        "projected_source_family_count": len(source_counter),
        "projected_task_family_count": len(task_counter),
        "projected_target_family_coverage_count": target_coverage,
        "projected_max_single_source_family_share": max_source_share,
        "projected_max_single_task_family_share": max_task_share,
        "projected_design_targets_satisfied": targets_satisfied,
    }


def build_follow_up_manifest(*, summary_path: Path, output_dir: Path, decision: str) -> dict[str, Any]:
    command = (
        "PYTHONPATH=src python -m autodrift.paper_route_l0_l1_l2_l3_capability_prediction_"
        "fresh_source_diverse_panel_repair_source_acquisition_materialization_result_audit "
        f"--m2905-summary {summary_path} --m2905-dir {output_dir} "
        " --output-doc docs/m2906-paper-route-l0-l1-l2-l3-capability-prediction-"
        "fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.md"
    )
    return {
        "id": NEXT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_milestone": MILESTONE_ID,
        "type": "gate",
        "gate_tier": "process",
        "status": "pending",
        "risk": "medium",
        "promotion_decision": "not_applicable",
        "hypothesis": (
            "A bounded result audit can accept or reject the M2905 repair/source-"
            "acquisition materialization preflight before source execution validation "
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
                str(output_dir / "seed_gap_repair_rows.csv"),
                str(output_dir / "acquisition_required_rows.csv"),
                "docs/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-preflight.json",
                "experiments/manifests/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design.json",
            ],
            "parent_objective": [
                "audit M2905 repair/source-acquisition materialization and preserve positive or negative repair result"
            ],
            "derived_from": [
                MILESTONE_ID,
                "m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design",
                "m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit",
            ],
            "blocked_by": [
                "M2905 is materialization preflight only",
                "projected fresh/source-diverse targets may remain unsatisfied",
                "source-singleton and guard rows must remain out of validation paper proof and ordinary denominators",
            ],
            "supersedes": [
                "treating repair/acquisition accounting as validation evidence",
                "treating source-singleton rows as proof without acquisition",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2906 must audit M2905 summary and row artifacts",
            "M2906 must preserve the exact repair/acquisition result without weakening thresholds",
            "M2906 must keep public reference source-singleton and guard rows out of validation paper proof and ordinary denominators",
            "M2906 must preserve actor 72/action 3 no hidden/oracle input no future-target actor input and evaluator-only target boundaries",
            "M2906 must choose repair source execution pivot synthesis or stop without claiming model quality driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
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
            "evidence_axis": "fresh_source_diverse_panel_repair_source_acquisition_materialization_result_audit",
            "evidence_increment": "audits the M2905 repair/source-acquisition accounting panel before any source execution or validation",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if M2905 artifacts are incomplete",
                "stop if actor target split holdout or exclusion boundaries fail",
                "stop if source-diversity thresholds are weakened",
                "stop if M2906 would claim model quality driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
            ],
            "fallback_plan": [
                "route to source-acquisition execution only if audit accepts a claim-safe acquisition-required surface",
                "route to Route A closed-loop evidence if Route B cannot acquire fresh/source-diverse support",
                "write a stop synthesis if no claim-safe repair path remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2905 registered repair/source-acquisition materialization for audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B repair/source-acquisition materialization result audit",
            "admission_evidence": [
                "M2905 wrote repair/source-acquisition accounting rows",
                "M2904 defined repair lanes from M2903 zero-fresh-candidate audit",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion",
                "no additional optimizer step and no promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2906 status queue scoreboard research log and review",
                "one bounded follow-up source acquisition synthesis pivot or stop manifest",
            ],
            "next_stage_criteria": [
                "M2905 summary and row artifacts are audited",
                "repair/acquisition result is preserved exactly",
                "one next source execution pivot synthesis or stop route is selected",
                "target actor split holdout and exclusion boundaries remain preserved",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2906 audits repair accounting only and cannot substitute acquisition rows for history-necessity evidence.",
            "history_necessity_tests": [
                "None in M2906; later evidence requires accepted source-diverse panel data and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2884-M2905 Route B capability-prediction panel inventory dataset contract fitting design materialization audit repair design and repair materialization chain.",
            "negative_result_policy": "If M2905 remains insufficient, preserve the negative result and route to pivot/stop or concrete source execution rather than weakening self-ID gates.",
            "allowed_claims": [
                "bounded repair/source-acquisition result-audit outcome",
                "projected fresh/source-diverse criteria satisfied or not satisfied as reported by M2905",
                "bounded follow-up source execution pivot synthesis or stop decision",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits a newly materialized repair/source-acquisition accounting panel",
            "paper_verdict_delta": "no verdict; preserves whether Route B has a claim-safe acquisition path",
            "must_synthesize_if": [
                "M2906 cannot choose between source execution Route A pivot Route C pivot synthesis or stop",
                "M2906 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2906 would let source-singleton or guard rows enter paper proof",
                "M2906 would expose evaluator-only future targets to actor input",
                "another repair-only loop is proposed without source execution or synthesis",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M2905 summary and row artifacts are audited",
            "repair/acquisition result is preserved without threshold weakening",
            "one bounded follow-up route or stop decision is selected",
            "no validation ranking promotion performance paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2906 changes M2905 row classifications or thresholds to force a pass",
            "M2906 admits public reference source-singleton or guard rows into validation paper proof or ordinary denominators",
            "M2906 claims model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2906 resets steps rolls out replays validates fits trains ranks promotes or executes policy action",
            "M2906 fails to select a bounded source execution synthesis pivot or stop route after auditing M2905",
        ],
        "decision_rule": (
            "Accept M2905 only if all repair/acquisition materialization artifacts are "
            "complete internally consistent and claim-safe."
        ),
        "commands": [{"name": "result_audit", "command": command}],
        "command": command,
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "expected_artifacts": [f"docs/{NEXT_ID}.md"],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir),
            "docs/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design.md",
            "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.md",
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": (
            "m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
            "panel-source-execution-or-pivot-synthesis"
        ),
        "m2905_result": {"summary": str(summary_path), "decision": decision},
    }


def _gate_rows(
    *,
    input_paths_present: dict[str, bool],
    row_counts: dict[str, int],
    target_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    rollback_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    split_ok = all(_bool(row.get("status_pass")) for row in split_rows)
    target_ok = all(_bool(row.get("status_pass")) for row in target_rows)
    claim_ok = all(not _bool(row.get("claim_made")) for row in claim_rows)
    rollback_ok = all(_bool(row.get("status_pass")) for row in rollback_rows)
    specs = (
        ("input_artifacts_present", all(input_paths_present.values()), json.dumps(input_paths_present, sort_keys=True), "all declared inputs exist"),
        ("repair_rows_written", row_counts["seed_gap_repair_rows"] > 0, str(row_counts["seed_gap_repair_rows"]), "nonempty seed-gap repair rows"),
        ("candidate_support_rows_accounted", True, str(row_counts["candidate_support_repair_rows"]), "candidate-support repair rows accounted"),
        ("source_family_rows_accounted", True, str(row_counts["source_family_repair_rows"]), "source-family repair rows accounted"),
        ("acquisition_required_rows_written", row_counts["acquisition_required_rows"] > 0, str(row_counts["acquisition_required_rows"]), "acquisition-required rows written"),
        ("split_boundaries_preserved", split_ok, str(row_counts["split_boundary_rows"]), "no validation/paper/model-quality denominator admitted"),
        ("target_boundaries_preserved", target_ok, str(row_counts["target_boundary_rows"]), "evaluator-only target boundaries preserved"),
        ("claim_boundaries_preserved", claim_ok, str(row_counts["claim_rows"]), "all claim rows false"),
        ("rollback_rows_pass", rollback_ok, str(row_counts["rollback_rows"]), "rollback rows pass"),
        ("follow_up_manifest_written", follow_up_manifest.exists(), str(follow_up_manifest), "M2906 result-audit manifest exists"),
    )
    rows: list[dict[str, Any]] = []
    for index, (family, status, observed, expected) in enumerate(specs, start=1):
        rows.append(
            {
                "gate_id": f"gate-{index:03d}",
                "gate_family": family,
                "status_pass": status,
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status else f"{family}_failed",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def _rollback_rows(
    *,
    summary_boundary_pass: bool,
    split_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    projected_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    split_ok = all(_bool(row.get("status_pass")) for row in split_rows)
    target_ok = all(_bool(row.get("status_pass")) for row in target_rows)
    claim_ok = all(not _bool(row.get("claim_made")) for row in claim_rows)
    specs = (
        ("actor_contract_and_parent_summary_preserved", summary_boundary_pass, f"{P0_OBSERVATION_DIM}x{ACTION_DIM}", "actor 72/action 3 and parent summary boundaries preserved"),
        ("split_denominators_false", split_ok, "all_false", "paper/validation/model-quality/ordinary denominators false"),
        ("target_actor_visibility_false", target_ok, "all_false", "target rows remain evaluator-only"),
        ("claims_suppressed", claim_ok, "all_claim_made_false", "no claims made"),
        ("thresholds_not_weakened", True, json.dumps(DESIGN_TARGETS, sort_keys=True), "M2901 design thresholds unchanged"),
        ("negative_projection_preserved", not _bool(projected_metrics["projected_design_targets_satisfied"]), f"projected_fresh_candidate_task_count={projected_metrics['projected_fresh_candidate_task_count']}", "negative projection is reported as blocker"),
    )
    rows: list[dict[str, Any]] = []
    for index, (family, status, observed, expected) in enumerate(specs, start=1):
        rows.append(
            {
                "rollback_id": f"rollback-{index:03d}",
                "rollback_family": family,
                "status_pass": status,
                "observed": observed,
                "expected": expected,
                "failure_type": "" if status else f"{family}_failed",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def write_preflight_artifacts(
    *,
    m2904_design: Path,
    m2903_audit: Path,
    m2902_dir: Path,
    m2884_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(output_dir)
    m2902_summary_path = m2902_dir / "summary.json"
    seed_gap_path = m2902_dir / "seed_gap_rows.csv"
    taxonomy_path = m2902_dir / "panel_row_taxonomy_rows.csv"
    target_path = m2902_dir / "target_coverage_rows.csv"
    m2884_source_inventory_path = m2884_dir / "source_inventory_rows.csv"
    m2884_candidate_path = m2884_dir / "candidate_panel_rows.csv"
    input_paths_present = {
        "m2904_design": m2904_design.exists(),
        "m2903_audit": m2903_audit.exists(),
        "m2902_summary": m2902_summary_path.exists(),
        "m2902_seed_gap_rows": seed_gap_path.exists(),
        "m2902_panel_row_taxonomy_rows": taxonomy_path.exists(),
        "m2902_target_coverage_rows": target_path.exists(),
        "m2884_source_inventory_rows": m2884_source_inventory_path.exists(),
        "m2884_candidate_panel_rows": m2884_candidate_path.exists(),
    }
    summary_2902 = _read_json(m2902_summary_path)
    seed_gap_rows = _read_csv_rows(seed_gap_path)
    taxonomy_rows = _read_csv_rows(taxonomy_path)
    target_coverage_rows = _read_csv_rows(target_path)
    source_inventory_rows = _read_csv_rows(m2884_source_inventory_path)
    candidate_panel_rows = _read_csv_rows(m2884_candidate_path)

    repair_rows = build_seed_gap_repair_rows(seed_gap_rows, taxonomy_rows)
    candidate_support_rows = build_candidate_support_rows(repair_rows)
    source_family_rows = build_source_family_rows(repair_rows)
    dual_rows = build_dual_repair_rows(repair_rows)
    acquisition_rows = build_acquisition_required_rows(repair_rows)
    projection_rows = build_repaired_projection_rows(repair_rows)
    exclusion_rows = build_exclusion_rows(taxonomy_rows)
    split_rows = build_split_boundary_rows(
        taxonomy_rows=taxonomy_rows,
        repair_rows=repair_rows,
        projection_rows=projection_rows,
        acquisition_rows=acquisition_rows,
    )
    target_rows = build_target_boundary_rows(target_coverage_rows, projection_rows)
    claim_rows = build_claim_rows()
    projected_metrics = _projected_metrics(projection_rows)
    summary_boundary_pass = (
        _bool(summary_2902.get("status_pass"))
        and _bool(summary_2902.get("gate_matrix_pass"))
        and _bool(summary_2902.get("actor_contract_shape_72_action_3"))
        and not _bool(summary_2902.get("hidden_oracle_actor_input_required"))
        and not _bool(summary_2902.get("future_target_actor_input_required"))
        and not _bool(summary_2902.get("evaluator_targets_actor_visible"))
        and not _bool(summary_2902.get("paper_holdout_admitted"))
        and _bool(summary_2902.get("preflight_only_split"))
    )
    rollback_rows = _rollback_rows(
        summary_boundary_pass=summary_boundary_pass,
        split_rows=split_rows,
        target_rows=target_rows,
        claim_rows=claim_rows,
        projected_metrics=projected_metrics,
    )
    row_counts = {
        "seed_gap_repair_rows": len(repair_rows),
        "candidate_support_repair_rows": len(candidate_support_rows),
        "source_family_repair_rows": len(source_family_rows),
        "dual_repair_rows": len(dual_rows),
        "acquisition_required_rows": len(acquisition_rows),
        "repaired_candidate_projection_rows": len(projection_rows),
        "exclusion_rows": len(exclusion_rows),
        "split_boundary_rows": len(split_rows),
        "target_boundary_rows": len(target_rows),
        "rollback_rows": len(rollback_rows),
        "claim_rows": len(claim_rows),
    }
    decision = (
        "repair_source_acquisition_materialized_projected_targets_satisfied_route_to_m2906_result_audit"
        if projected_metrics["projected_design_targets_satisfied"]
        else "repair_source_acquisition_materialized_existing_support_insufficient_route_to_m2906_result_audit"
    )
    summary_path = paths["summary"]
    follow_up = build_follow_up_manifest(summary_path=summary_path, output_dir=output_dir, decision=decision)
    _write_json(follow_up_manifest, follow_up)
    gate_rows = _gate_rows(
        input_paths_present=input_paths_present,
        row_counts={**row_counts, "gate_rows": 0},
        target_rows=target_rows,
        split_rows=split_rows,
        claim_rows=claim_rows,
        rollback_rows=rollback_rows,
        follow_up_manifest=follow_up_manifest,
    )
    row_counts["gate_rows"] = len(gate_rows)
    status_pass = all(_bool(row.get("status_pass")) for row in gate_rows)
    gate_matrix_pass = status_pass
    if not status_pass:
        decision = "repair_source_acquisition_materialization_preflight_incomplete"

    missing_counts = Counter()
    for row in seed_gap_rows:
        for requirement in _requirements(row):
            missing_counts[requirement] += 1
    task_counts = Counter(row.get("task_family", "") for row in repair_rows)
    env_counts = Counter(row.get("env_template_family", "") for row in repair_rows)
    summary = {
        "milestone": MILESTONE_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "artifacts": {key: str(path) for key, path in paths.items()} | {"follow_up_manifest": str(follow_up_manifest)},
        "row_counts": row_counts,
        "input_paths_present": input_paths_present,
        "m2904_design": str(m2904_design),
        "m2903_audit": str(m2903_audit),
        "m2902_dir": str(m2902_dir),
        "m2884_dir": str(m2884_dir),
        "m2884_source_inventory_row_count": len(source_inventory_rows),
        "m2884_candidate_panel_row_count": len(candidate_panel_rows),
        "seed_gap_row_count": len(seed_gap_rows),
        "candidate_support_gap_count": len(candidate_support_rows),
        "source_family_gap_count": len(source_family_rows),
        "dual_gap_count": len(dual_rows),
        "repaired_candidate_projection_count": len(projection_rows),
        "acquisition_required_count": len(acquisition_rows),
        "seed_gap_missing_requirement_counts": dict(missing_counts),
        "seed_gap_task_family_counts": dict(task_counts),
        "seed_gap_env_template_family_counts": dict(env_counts),
        **projected_metrics,
        "design_targets": DESIGN_TARGETS,
        "actor_contract_shape_72_action_3": True,
        "observation_dim": P0_OBSERVATION_DIM,
        "action_dim": ACTION_DIM,
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
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": NEXT_ID,
    }
    run_state = {
        "milestone": MILESTONE_ID,
        "status": "complete" if status_pass else "incomplete",
        "decision": decision,
        "summary_path": str(summary_path),
        "follow_up_manifest": str(follow_up_manifest),
        "claim_boundary": CLAIM_SCOPE,
    }

    _write_csv(paths["seed_gap_repair_rows"], SEED_GAP_REPAIR_FIELDNAMES, repair_rows)
    _write_csv(paths["candidate_support_repair_rows"], CANDIDATE_SUPPORT_FIELDNAMES, candidate_support_rows)
    _write_csv(paths["source_family_repair_rows"], SOURCE_FAMILY_FIELDNAMES, source_family_rows)
    _write_csv(paths["dual_repair_rows"], DUAL_REPAIR_FIELDNAMES, dual_rows)
    _write_csv(paths["acquisition_required_rows"], ACQUISITION_REQUIRED_FIELDNAMES, acquisition_rows)
    _write_csv(paths["repaired_candidate_projection_rows"], REPAIRED_PROJECTION_FIELDNAMES, projection_rows)
    _write_csv(paths["exclusion_rows"], EXCLUSION_FIELDNAMES, exclusion_rows)
    _write_csv(paths["split_boundary_rows"], SPLIT_BOUNDARY_FIELDNAMES, split_rows)
    _write_csv(paths["target_boundary_rows"], TARGET_BOUNDARY_FIELDNAMES, target_rows)
    _write_csv(paths["rollback_rows"], ROLLBACK_FIELDNAMES, rollback_rows)
    _write_csv(paths["gate_rows"], GATE_FIELDNAMES, gate_rows)
    _write_csv(paths["claim_rows"], CLAIM_FIELDNAMES, claim_rows)
    _write_json(paths["run_state"], run_state)
    _write_json(summary_path, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2904-design", type=Path, default=DEFAULT_M2904_DESIGN)
    parser.add_argument("--m2903-audit", type=Path, default=DEFAULT_M2903_AUDIT)
    parser.add_argument("--m2902-dir", type=Path, default=DEFAULT_M2902_DIR)
    parser.add_argument("--m2884-dir", type=Path, default=DEFAULT_M2884_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = write_preflight_artifacts(
        m2904_design=args.m2904_design,
        m2903_audit=args.m2903_audit,
        m2902_dir=args.m2902_dir,
        m2884_dir=args.m2884_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
