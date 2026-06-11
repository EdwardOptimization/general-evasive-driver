"""Validate AutoDrift research-process state.

This is intentionally a lightweight repository-state check. It does not run
training or benchmarks; it verifies that the research queue, manifests,
scoreboard, and status file are internally consistent.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json
from autodrift.research_cycle import ALLOWED_STATUSES, ResearchTask, load_queue, queue_counts
from autodrift.research_schema import (
    PROCESS_V2_ENFORCE_FROM_PRIORITY,
    PROCESS_V2_FAILURE_TYPES,
    PROCESS_V2_GATE_TIERS,
    PROCESS_V2_LINEAGE_FIELDS,
    PROCESS_V2_PRIVATE_HOLDOUT_POLICIES,
    PROCESS_V2_PROMOTION_DECISIONS,
    PROCESS_V3_SYNTHESIS_DECISIONS,
    PROCESS_V3_SYNTHESIS_ENFORCE_FROM_PRIORITY,
    PROCESS_V3_SYNTHESIS_FIELDS,
    PROCESS_V3_SYNTHESIS_QUESTIONS,
    PROCESS_V4_TRAINING_STAGE_ENFORCE_FROM_PRIORITY,
    PROCESS_V4_TRAINING_STAGE_FIELDS,
    PROCESS_V4_TRAINING_STAGES,
    PROCESS_V5_SELF_ID_CLAIM_LEVELS,
    PROCESS_V5_SELF_ID_DISCIPLINE_ENFORCE_FROM_PRIORITY,
    PROCESS_V5_SELF_ID_DISCIPLINE_FIELDS,
    PROCESS_V6_ACTUAL_PROGRESS_TYPES,
    PROCESS_V6_DEFAULT_NON_EVIDENCE_STREAK_LIMIT,
    PROCESS_V6_EVIDENCE_PROGRESS_TYPES,
    PROCESS_V6_LOCAL_SEARCH_GUARD_ENFORCE_FROM_PRIORITY,
    PROCESS_V6_LOCAL_SEARCH_GUARD_FIELDS,
    PROCESS_V6_LOCAL_SEARCH_RISK_LEVELS,
    PROCESS_V7_CERTIFIED_DEAD_END_RESIDUAL_SEEDS,
    PROCESS_V7_DEAD_END_CERTIFICATION_ARTIFACTS,
    PROCESS_V7_FEASIBILITY_PRICING_ENFORCE_FROM_PRIORITY,
    PROCESS_V7_FEASIBILITY_PRICING_FIELDS,
    PROCESS_V7_PRICED_EVIDENCE_AXIS_TOKENS,
    PROCESS_V7_PRICED_INTENTS,
    PROCESS_V7_REPAIR_LIKE_TOKENS,
    PROCESS_V7B_DEPENDENCY_STREAK_LIMIT,
    PROCESS_V7B_DEPENDENCY_UNAVAILABLE_TOKENS,
    PROCESS_V7B_ESCALATION_DIR,
    SCOREBOARD_FIELDS,
)


ENFORCE_FROM_PRIORITY = 870
MANIFEST_REQUIRED_FIELDS = (
    "id",
    "type",
    "hypothesis",
    "success_criteria",
    "failure_criteria",
    "commands",
    "required_artifacts",
    "baseline_checkpoints",
    "decision_rule",
)
MANIFEST_TYPES = {"infrastructure", "objective_sanity", "driver_candidate", "gate"}
GATE_OPERATORS = {">", ">=", "<", "<=", "==", "!="}
PROCESS_V2_REQUIRED_FIELDS = (
    "gate_tier",
    "promotion_decision",
    "failure_types",
    "lineage",
    "review_artifact",
    "public_gates",
    "private_holdout_policy",
    "forbidden_shortcuts",
)
PROCESS_V3_REQUIRED_FIELDS = (
    "workflow_synthesis",
)
PROCESS_V4_REQUIRED_FIELDS = (
    "training_stage",
)
PROCESS_V5_REQUIRED_FIELDS = (
    "self_id_evidence_discipline",
)
PROCESS_V6_REQUIRED_FIELDS = (
    "local_search_guard",
)


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    message: str


def _is_enforced(task: ResearchTask, enforce_from_priority: int) -> bool:
    return int(task.priority) >= int(enforce_from_priority)


def _is_process_v2(task: ResearchTask, process_v2_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v2_from_priority)


def _is_process_v3(task: ResearchTask, process_v3_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v3_from_priority)


def _is_process_v4(task: ResearchTask, process_v4_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v4_from_priority)


def _is_process_v5(task: ResearchTask, process_v5_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v5_from_priority)


def _is_process_v6(task: ResearchTask, process_v6_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v6_from_priority)


def _is_process_v7(task: ResearchTask, process_v7_from_priority: int) -> bool:
    return int(task.priority) >= int(process_v7_from_priority)


def _manifest_path(manifest_dir: Path, task_id: str) -> Path:
    return manifest_dir / f"{task_id}.json"


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _is_text_or_list_or_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        return all(isinstance(item, str) for item in value)
    return False


def _has_lineage_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(isinstance(item, str) and bool(item.strip()) for item in value)
    return False


def _path_exists(root: Path, path_text: str) -> bool:
    path = Path(path_text)
    return path.exists() if path.is_absolute() else (root / path).exists()


def _required_artifact_paths(manifest: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for artifact in manifest.get("required_artifacts", []):
        if isinstance(artifact, dict):
            path = artifact.get("path")
        else:
            path = artifact
        if isinstance(path, str) and path.strip():
            paths.add(path.strip())
    return paths


def normalize_next_task(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        task_id = value.get("id")
        return str(task_id) if task_id else None
    raise ValueError(f"research_status next_task must be string, object, or null, got {type(value).__name__}")


def _milestone_number(milestone: str) -> int | None:
    if not milestone.startswith("m"):
        return None
    digits = []
    for character in milestone[1:]:
        if not character.isdigit():
            break
        digits.append(character)
    return int("".join(digits)) if digits else None


def load_scoreboard(path: Path, *, reject_extra_fields_from_milestone: int | None = None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SCOREBOARD_FIELDS:
            raise ValueError(f"scoreboard must have fields {SCOREBOARD_FIELDS}, got {reader.fieldnames}")
        rows: list[dict[str, str]] = []
        for index, row in enumerate(reader, start=2):
            milestone = str(row.get("milestone", ""))
            milestone_number = _milestone_number(milestone)
            reject_extra = (
                reject_extra_fields_from_milestone is None
                or (milestone_number is not None and milestone_number >= reject_extra_fields_from_milestone)
            )
            if None in row and reject_extra:
                raise ValueError(f"scoreboard row {index} has extra fields: {row[None]}")
            row.pop(None, None)
            rows.append(dict(row))
        return rows


def _validate_manifest(
    task: ResearchTask,
    manifest: dict[str, Any],
    process_v2: bool = False,
    process_v3: bool = False,
    process_v4: bool = False,
    process_v5: bool = False,
    process_v6: bool = False,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in MANIFEST_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: manifest missing fields {missing}"))
        return issues
    if manifest["id"] != task.id:
        issues.append(ValidationIssue("error", f"{task.id}: manifest id {manifest['id']!r} does not match queue id"))
    if manifest["type"] not in MANIFEST_TYPES:
        issues.append(
            ValidationIssue("error", f"{task.id}: manifest type must be one of {sorted(MANIFEST_TYPES)}")
        )
    for field in ("hypothesis", "decision_rule"):
        if not _non_empty_text(manifest[field]):
            issues.append(ValidationIssue("error", f"{task.id}: manifest field {field!r} must be non-empty text"))
    for field in ("success_criteria", "failure_criteria", "commands", "required_artifacts", "baseline_checkpoints"):
        if not _non_empty_list(manifest[field]):
            issues.append(ValidationIssue("error", f"{task.id}: manifest field {field!r} must be a non-empty list"))
    issues.extend(_validate_metric_extractors(task, manifest))
    issues.extend(_validate_gates(task, manifest))
    if process_v2:
        issues.extend(_validate_process_v2_manifest(task, manifest))
    if process_v3:
        issues.extend(_validate_process_v3_manifest(task, manifest))
    if process_v4:
        issues.extend(_validate_process_v4_manifest(task, manifest))
    if process_v5:
        issues.extend(_validate_process_v5_manifest(task, manifest))
    if process_v6:
        issues.extend(_validate_process_v6_manifest(task, manifest))
    return issues


def _validate_process_v2_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in PROCESS_V2_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: process-v2 manifest missing fields {missing}"))
        return issues

    gate_tier = manifest.get("gate_tier")
    if gate_tier not in PROCESS_V2_GATE_TIERS:
        issues.append(
            ValidationIssue("error", f"{task.id}: gate_tier must be one of {sorted(PROCESS_V2_GATE_TIERS)}")
        )

    promotion_decision = manifest.get("promotion_decision")
    if promotion_decision not in PROCESS_V2_PROMOTION_DECISIONS:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: promotion_decision must be one of {sorted(PROCESS_V2_PROMOTION_DECISIONS)}",
            )
        )
    if task.status == "completed" and promotion_decision == "pending":
        issues.append(ValidationIssue("error", f"{task.id}: completed process-v2 task cannot keep pending promotion_decision"))

    failure_types = manifest.get("failure_types")
    if not isinstance(failure_types, list):
        issues.append(ValidationIssue("error", f"{task.id}: failure_types must be a list"))
    else:
        unknown = [item for item in failure_types if item not in PROCESS_V2_FAILURE_TYPES]
        if unknown:
            issues.append(
                ValidationIssue("error", f"{task.id}: unknown failure_types {unknown}; allowed {sorted(PROCESS_V2_FAILURE_TYPES)}")
            )
        if "none" in failure_types and len(failure_types) > 1:
            issues.append(ValidationIssue("error", f"{task.id}: failure_types cannot combine 'none' with other failures"))
        if task.status == "completed" and promotion_decision in {"reject", "repair"} and not failure_types:
            issues.append(
                ValidationIssue("error", f"{task.id}: rejected or repair process-v2 task must classify failure_types")
            )

    lineage = manifest.get("lineage")
    if not isinstance(lineage, dict):
        issues.append(ValidationIssue("error", f"{task.id}: lineage must be an object"))
    else:
        missing_lineage = [field for field in PROCESS_V2_LINEAGE_FIELDS if field not in lineage]
        if missing_lineage:
            issues.append(ValidationIssue("error", f"{task.id}: lineage missing fields {missing_lineage}"))
        for field in PROCESS_V2_LINEAGE_FIELDS:
            if field in lineage and not _is_text_or_list_or_null(lineage[field]):
                issues.append(
                    ValidationIssue(
                        "error",
                        f"{task.id}: lineage.{field} must be text, list of text, or null",
                    )
                )
        if task.status != "planned" and not _has_lineage_value(lineage.get("derived_from")):
            issues.append(ValidationIssue("error", f"{task.id}: lineage.derived_from must identify a parent experiment"))
        if task.kind != "infrastructure" and not _has_lineage_value(lineage.get("blocked_by")):
            issues.append(ValidationIssue("error", f"{task.id}: lineage.blocked_by must identify the current blocker"))

    if not _non_empty_text(manifest.get("review_artifact")):
        issues.append(ValidationIssue("error", f"{task.id}: review_artifact must be non-empty text"))

    if not _non_empty_list(manifest.get("public_gates")):
        issues.append(ValidationIssue("error", f"{task.id}: public_gates must be a non-empty list"))
    if manifest.get("private_holdout_policy") not in PROCESS_V2_PRIVATE_HOLDOUT_POLICIES:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: private_holdout_policy must be one of {sorted(PROCESS_V2_PRIVATE_HOLDOUT_POLICIES)}",
            )
        )
    if not _non_empty_list(manifest.get("forbidden_shortcuts")):
        issues.append(ValidationIssue("error", f"{task.id}: forbidden_shortcuts must be a non-empty list"))
    return issues


def _workflow_synthesis(manifest: dict[str, Any]) -> dict[str, Any] | None:
    synthesis = manifest.get("workflow_synthesis")
    return synthesis if isinstance(synthesis, dict) else None


def _workflow_synthesis_decision(manifest: dict[str, Any]) -> str:
    synthesis = _workflow_synthesis(manifest)
    if synthesis is None:
        return "not_applicable"
    decision = synthesis.get("synthesis_decision")
    return str(decision) if isinstance(decision, str) else ""


def _is_workflow_synthesis_milestone(manifest: dict[str, Any]) -> bool:
    return _workflow_synthesis_decision(manifest) != "not_applicable"


def _validate_process_v3_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in PROCESS_V3_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: process-v3 manifest missing fields {missing}"))
        return issues

    synthesis = _workflow_synthesis(manifest)
    if not isinstance(synthesis, dict):
        return [ValidationIssue("error", f"{task.id}: workflow_synthesis must be an object")]

    missing_synthesis = [field for field in PROCESS_V3_SYNTHESIS_FIELDS if field not in synthesis]
    if missing_synthesis:
        issues.append(ValidationIssue("error", f"{task.id}: workflow_synthesis missing fields {missing_synthesis}"))
        return issues

    for field in ("branch", "evidence_axis", "evidence_increment", "claim_scope", "synthesis_trigger"):
        if not _non_empty_text(synthesis.get(field)):
            issues.append(ValidationIssue("error", f"{task.id}: workflow_synthesis.{field} must be non-empty text"))

    for field in ("stop_condition", "fallback_plan"):
        value = synthesis.get(field)
        if not _non_empty_list(value) or not all(_non_empty_text(item) for item in value):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.{field} must be a non-empty list of non-empty text",
                )
            )

    cadence = synthesis.get("synthesis_cadence")
    if not isinstance(cadence, int):
        issues.append(ValidationIssue("error", f"{task.id}: workflow_synthesis.synthesis_cadence must be an integer"))
    elif cadence < 10 or cadence > 20:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: workflow_synthesis.synthesis_cadence must be between 10 and 20 milestones",
            )
        )

    decision = synthesis.get("synthesis_decision")
    if decision not in PROCESS_V3_SYNTHESIS_DECISIONS:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: workflow_synthesis.synthesis_decision must be one of "
                f"{sorted(PROCESS_V3_SYNTHESIS_DECISIONS)}",
            )
        )
    elif decision != "not_applicable" and manifest.get("gate_tier") != "process":
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: workflow synthesis decision {decision!r} requires gate_tier='process'",
            )
        )
    elif decision != "not_applicable":
        synthesis_artifact = synthesis.get("synthesis_artifact")
        if not _non_empty_text(synthesis_artifact):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.synthesis_artifact must be non-empty text for synthesis milestones",
                )
            )
        elif str(synthesis_artifact).strip() not in _required_artifact_paths(manifest):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.synthesis_artifact must be listed in required_artifacts",
                )
            )

        questions = synthesis.get("synthesis_questions")
        if not _non_empty_list(questions) or not all(_non_empty_text(question) for question in questions):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.synthesis_questions must be a non-empty list of non-empty text",
                )
            )
        else:
            question_set = {str(question).strip() for question in questions}
            missing_questions = [
                question for question in PROCESS_V3_SYNTHESIS_QUESTIONS if question not in question_set
            ]
            if missing_questions:
                issues.append(
                    ValidationIssue(
                        "error",
                        f"{task.id}: workflow_synthesis.synthesis_questions missing {missing_questions}",
                    )
                )

    return issues


def _validate_process_v3_branch_cadence(records: list[tuple[ResearchTask, dict[str, Any]]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    branch_counts: dict[str, int] = {}
    branch_closed_by: dict[str, str] = {}
    sorted_records = sorted(records, key=lambda item: (item[0].priority, item[0].id))

    for task, manifest in sorted_records:
        synthesis = _workflow_synthesis(manifest)
        if synthesis is None:
            continue
        branch = synthesis.get("branch")
        cadence = synthesis.get("synthesis_cadence")
        decision = synthesis.get("synthesis_decision")
        if not _non_empty_text(branch) or not isinstance(cadence, int) or decision not in PROCESS_V3_SYNTHESIS_DECISIONS:
            continue

        branch_text = str(branch)
        if branch_text in branch_closed_by:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.branch {branch_text!r} was closed by "
                    f"{branch_closed_by[branch_text]}; use a new branch before continuing",
                )
            )
            continue

        if _is_workflow_synthesis_milestone(manifest):
            if decision == "continue":
                branch_counts[branch_text] = 0
            else:
                branch_closed_by[branch_text] = task.id
            continue

        branch_counts[branch_text] = branch_counts.get(branch_text, 0) + 1
        if branch_counts[branch_text] > cadence:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: workflow_synthesis.branch {branch_text!r} has "
                    f"{branch_counts[branch_text]} non-synthesis milestones since the last synthesis; "
                    f"cadence is {cadence}, so add a gate_tier='process' synthesis milestone with "
                    "workflow_synthesis.synthesis_decision before continuing",
                )
            )

    return issues


def _manifest_command_text(manifest: dict[str, Any]) -> str:
    commands = manifest.get("commands", [])
    if not isinstance(commands, list):
        return ""
    parts: list[str] = []
    for command in commands:
        if isinstance(command, dict):
            parts.append(str(command.get("command", "")))
        elif isinstance(command, str):
            parts.append(command)
    return "\n".join(parts).lower()


def _validate_process_v4_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in PROCESS_V4_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: process-v4 manifest missing fields {missing}"))
        return issues

    training_stage = manifest.get("training_stage")
    if not isinstance(training_stage, dict):
        return [ValidationIssue("error", f"{task.id}: training_stage must be an object")]

    missing_stage = [field for field in PROCESS_V4_TRAINING_STAGE_FIELDS if field not in training_stage]
    if missing_stage:
        issues.append(ValidationIssue("error", f"{task.id}: training_stage missing fields {missing_stage}"))
        return issues

    stage = training_stage.get("stage")
    if stage not in PROCESS_V4_TRAINING_STAGES:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: training_stage.stage must be one of {sorted(PROCESS_V4_TRAINING_STAGES)}",
            )
        )

    if not _non_empty_text(training_stage.get("stage_objective")):
        issues.append(ValidationIssue("error", f"{task.id}: training_stage.stage_objective must be non-empty text"))

    for field in ("admission_evidence", "blocked_shortcuts", "allowed_updates", "next_stage_criteria"):
        value = training_stage.get(field)
        if not _non_empty_list(value) or not all(_non_empty_text(item) for item in value):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: training_stage.{field} must be a non-empty list of non-empty text",
                )
            )

    command_text = _manifest_command_text(manifest)
    runs_train_ppo = "autodrift.train_ppo" in command_text
    if runs_train_ppo and stage != "guarded_rl":
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: manifests that run train_ppo must use training_stage.stage='guarded_rl'",
            )
        )

    if stage == "guarded_rl":
        evidence_text = " ".join(str(item).lower() for item in training_stage.get("admission_evidence", []))
        has_pre_or_post = any(
            token in evidence_text
            for token in ("pretrain", "posttrain", "action-grounding", "action grounding", "capability")
        )
        has_proof = any(token in evidence_text for token in ("proof", "exact", "public gate"))
        has_rollback = any(token in evidence_text for token in ("rollback", "retention", "repair", "projection"))
        if not (has_pre_or_post and has_proof and has_rollback):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: guarded_rl stage must cite pre/posttrain capability evidence, "
                    "exact/proof gates, and rollback or repair protection in admission_evidence",
                )
            )

    return issues


def _validate_process_v5_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in PROCESS_V5_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: process-v5 manifest missing fields {missing}"))
        return issues

    discipline = manifest.get("self_id_evidence_discipline")
    if not isinstance(discipline, dict):
        return [ValidationIssue("error", f"{task.id}: self_id_evidence_discipline must be an object")]

    missing_discipline = [field for field in PROCESS_V5_SELF_ID_DISCIPLINE_FIELDS if field not in discipline]
    if missing_discipline:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: self_id_evidence_discipline missing fields {missing_discipline}",
            )
        )
        return issues

    claim_level = discipline.get("claim_level")
    if claim_level not in PROCESS_V5_SELF_ID_CLAIM_LEVELS:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: self_id_evidence_discipline.claim_level must be one of "
                f"{sorted(PROCESS_V5_SELF_ID_CLAIM_LEVELS)}",
            )
        )

    for field in ("current_frame_substitution_risk", "temporal_evidence_window", "negative_result_policy"):
        if not _non_empty_text(discipline.get(field)):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: self_id_evidence_discipline.{field} must be non-empty text",
                )
            )

    for field in ("history_necessity_tests", "allowed_claims"):
        value = discipline.get(field)
        if not _non_empty_list(value) or not all(_non_empty_text(item) for item in value):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: self_id_evidence_discipline.{field} must be a non-empty list of non-empty text",
                )
            )

    return issues


def _validate_non_negative_int(task: ResearchTask, field: str, value: Any) -> ValidationIssue | None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return ValidationIssue("error", f"{task.id}: local_search_guard.{field} must be a non-negative integer")
    return None


def _validate_process_v6_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = [field for field in PROCESS_V6_REQUIRED_FIELDS if field not in manifest]
    if missing:
        issues.append(ValidationIssue("error", f"{task.id}: process-v6 manifest missing fields {missing}"))
        return issues

    guard = manifest.get("local_search_guard")
    if not isinstance(guard, dict):
        return [ValidationIssue("error", f"{task.id}: local_search_guard must be an object")]

    missing_guard = [field for field in PROCESS_V6_LOCAL_SEARCH_GUARD_FIELDS if field not in guard]
    if missing_guard:
        issues.append(ValidationIssue("error", f"{task.id}: local_search_guard missing fields {missing_guard}"))
        return issues

    progress_type = guard.get("actual_progress_type")
    if progress_type not in PROCESS_V6_ACTUAL_PROGRESS_TYPES:
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: local_search_guard.actual_progress_type must be one of "
                f"{sorted(PROCESS_V6_ACTUAL_PROGRESS_TYPES)}",
            )
        )

    for field in ("process_overhead", "local_search_risk"):
        if guard.get(field) not in PROCESS_V6_LOCAL_SEARCH_RISK_LEVELS:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: local_search_guard.{field} must be one of "
                    f"{sorted(PROCESS_V6_LOCAL_SEARCH_RISK_LEVELS)}",
                )
            )

    for field in ("same_failure_repeat_count", "same_public_gate_repair_count"):
        issue = _validate_non_negative_int(task, field, guard.get(field))
        if issue is not None:
            issues.append(issue)

    for field in ("evidence_expansion", "paper_verdict_delta"):
        if not _non_empty_text(guard.get(field)):
            issues.append(ValidationIssue("error", f"{task.id}: local_search_guard.{field} must be non-empty text"))

    must_synthesize_if = guard.get("must_synthesize_if")
    if not _non_empty_list(must_synthesize_if) or not all(_non_empty_text(item) for item in must_synthesize_if):
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: local_search_guard.must_synthesize_if must be a non-empty list of non-empty text",
            )
        )

    repeat_count = guard.get("same_failure_repeat_count")
    repair_count = guard.get("same_public_gate_repair_count")
    trigger_repeat = isinstance(repeat_count, int) and repeat_count >= 3
    trigger_repair = isinstance(repair_count, int) and repair_count >= 3
    high_risk = guard.get("local_search_risk") == "high"
    if (trigger_repeat or trigger_repair or high_risk) and not _is_workflow_synthesis_milestone(manifest):
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: local_search_guard requires a workflow synthesis decision when "
                "local_search_risk is high or repeat/repair counts reach 3",
            )
        )

    return issues


def _validate_process_v6_local_search_cadence(records: list[tuple[ResearchTask, dict[str, Any]]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    non_evidence_counts: dict[str, int] = {}
    sorted_records = sorted(records, key=lambda item: (item[0].priority, item[0].id))

    for task, manifest in sorted_records:
        synthesis = _workflow_synthesis(manifest)
        if synthesis is None:
            continue
        branch = synthesis.get("branch")
        if not _non_empty_text(branch):
            continue

        branch_text = str(branch)
        if _is_workflow_synthesis_milestone(manifest):
            non_evidence_counts[branch_text] = 0
            continue

        guard = manifest.get("local_search_guard")
        if not isinstance(guard, dict):
            continue
        progress_type = guard.get("actual_progress_type")
        if progress_type in PROCESS_V6_EVIDENCE_PROGRESS_TYPES:
            non_evidence_counts[branch_text] = 0
            continue

        limit = guard.get("non_evidence_streak_limit", PROCESS_V6_DEFAULT_NON_EVIDENCE_STREAK_LIMIT)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: local_search_guard.non_evidence_streak_limit must be a positive integer when set",
                )
            )
            limit = PROCESS_V6_DEFAULT_NON_EVIDENCE_STREAK_LIMIT

        non_evidence_counts[branch_text] = non_evidence_counts.get(branch_text, 0) + 1
        if non_evidence_counts[branch_text] > limit:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: local_search_guard branch {branch_text!r} has "
                    f"{non_evidence_counts[branch_text]} consecutive non-evidence milestones; "
                    f"limit is {limit}, so add a process synthesis milestone or produce new data/panel evidence",
                )
            )

    return issues


def _manifest_intent(manifest: dict[str, Any]) -> str | None:
    intent = manifest.get("milestone_intent")
    if isinstance(intent, str) and intent.strip():
        return intent.strip().lower()
    return None


def _requires_feasibility_pricing(manifest: dict[str, Any]) -> bool:
    intent = _manifest_intent(manifest)
    if intent is not None:
        return intent in PROCESS_V7_PRICED_INTENTS
    synthesis = _workflow_synthesis(manifest)
    axis = "" if synthesis is None else str(synthesis.get("evidence_axis", "")).lower()
    return any(token in axis for token in PROCESS_V7_PRICED_EVIDENCE_AXIS_TOKENS)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _dead_end_scan_text(task: ResearchTask, manifest: dict[str, Any]) -> str:
    synthesis = _workflow_synthesis(manifest) or {}
    parts = [
        task.hypothesis,
        task.notes,
        str(manifest.get("hypothesis", "")),
        str(synthesis.get("evidence_axis", "")),
        str(manifest.get("milestone_intent", "")),
    ]
    return " ".join(parts).lower()


def _certified_dead_end_reason(task: ResearchTask, manifest: dict[str, Any]) -> str | None:
    text = _dead_end_scan_text(task, manifest)
    repair_like = _requires_feasibility_pricing(manifest) or any(
        token in text for token in PROCESS_V7_REPAIR_LIKE_TOKENS
    )
    mentioned_seeds = [seed for seed in PROCESS_V7_CERTIFIED_DEAD_END_RESIDUAL_SEEDS if seed in text]
    if repair_like and mentioned_seeds:
        return (
            f"residual hard-safety rows (seeds {', '.join(mentioned_seeds)}) are oracle-certified "
            "unrepairable by any controller, causal or privileged"
        )
    if repair_like and "drift_required" in text and "reflex" in text:
        return "reflex-family drift_required repair is a certified dead end"
    if (
        "reflex" in text
        and any(token in text for token in ("retun", "re-tune", "tuning", "per-instance"))
        and any(token in text for token in ("spread", "vehicle"))
    ):
        return "vehicle-spread reflex retuning was rejected by the pre-registered C5 pricing (0/8 cells)"
    return None


def _has_new_pricing_artifact(root: Path, manifest: dict[str, Any]) -> bool:
    pricing = manifest.get("feasibility_pricing")
    if not isinstance(pricing, dict):
        return False
    artifact = pricing.get("pricing_artifact")
    if not _non_empty_text(artifact):
        return False
    normalized = str(artifact).strip()
    if normalized in PROCESS_V7_DEAD_END_CERTIFICATION_ARTIFACTS:
        return False
    return _path_exists(root, normalized)


def _validate_process_v7_manifest(task: ResearchTask, manifest: dict[str, Any], root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if _requires_feasibility_pricing(manifest):
        pricing = manifest.get("feasibility_pricing")
        if not isinstance(pricing, dict):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: process-v7 repair/improvement/training milestone requires a "
                    "feasibility_pricing object (feasibility-oracle-first, WP6.2 G1): "
                    f"{{{', '.join(PROCESS_V7_FEASIBILITY_PRICING_FIELDS)}}}",
                )
            )
        else:
            missing = [field for field in PROCESS_V7_FEASIBILITY_PRICING_FIELDS if field not in pricing]
            if missing:
                issues.append(
                    ValidationIssue("error", f"{task.id}: feasibility_pricing missing fields {missing}")
                )
            else:
                artifact = pricing.get("pricing_artifact")
                if not _non_empty_text(artifact):
                    issues.append(
                        ValidationIssue(
                            "error",
                            f"{task.id}: feasibility_pricing.pricing_artifact must be non-empty text",
                        )
                    )
                elif not _path_exists(root, str(artifact).strip()):
                    issues.append(
                        ValidationIssue(
                            "error",
                            f"{task.id}: feasibility_pricing.pricing_artifact does not exist: {artifact}",
                        )
                    )
                for field in ("priced_gap", "threshold"):
                    if not _is_number(pricing.get(field)):
                        issues.append(
                            ValidationIssue(
                                "error",
                                f"{task.id}: feasibility_pricing.{field} must be a number",
                            )
                        )
                if not isinstance(pricing.get("gap_meets_threshold"), bool):
                    issues.append(
                        ValidationIssue(
                            "error",
                            f"{task.id}: feasibility_pricing.gap_meets_threshold must be a boolean",
                        )
                    )

    dead_end_reason = _certified_dead_end_reason(task, manifest)
    if dead_end_reason is not None and not _has_new_pricing_artifact(root, manifest):
        issues.append(
            ValidationIssue(
                "error",
                f"{task.id}: certified dead end — {dead_end_reason}; see "
                f"{PROCESS_V7_DEAD_END_CERTIFICATION_ARTIFACTS[0]} and "
                f"{PROCESS_V7_DEAD_END_CERTIFICATION_ARTIFACTS[1]}; this target is auto-rejected "
                "unless the manifest carries a NEW feasibility_pricing.pricing_artifact that "
                "re-prices the gap",
            )
        )

    return issues


def _mentions_dependency_unavailable(task: ResearchTask, manifest: dict[str, Any]) -> bool:
    text = " ".join([task.hypothesis, task.notes, str(manifest.get("hypothesis", ""))]).lower()
    return any(token in text for token in PROCESS_V7B_DEPENDENCY_UNAVAILABLE_TOKENS)


def _escalation_exists(root: Path, branch: str, task_ids: list[str]) -> bool:
    directory = root / PROCESS_V7B_ESCALATION_DIR
    if not directory.exists():
        return False
    needles = [branch.lower()] + [task_id.lower() for task_id in task_ids]
    for path in sorted(directory.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        content = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(needle in content for needle in needles):
            return True
    return False


def _validate_process_v7_escalation_protocol(
    records: list[tuple[ResearchTask, dict[str, Any]]], root: Path
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    streaks: dict[str, list[str]] = {}
    sorted_records = sorted(records, key=lambda item: (item[0].priority, item[0].id))

    for task, manifest in sorted_records:
        if task.status != "completed":
            continue
        synthesis = _workflow_synthesis(manifest)
        if synthesis is None:
            continue
        branch = synthesis.get("branch")
        if not _non_empty_text(branch):
            continue
        branch_text = str(branch)
        if not _mentions_dependency_unavailable(task, manifest):
            streaks[branch_text] = []
            continue
        streaks.setdefault(branch_text, []).append(task.id)
        streak = streaks[branch_text]
        if len(streak) >= PROCESS_V7B_DEPENDENCY_STREAK_LIMIT and not _escalation_exists(root, branch_text, streak):
            issues.append(
                ValidationIssue(
                    "error",
                    f"{task.id}: branch {branch_text!r} has {len(streak)} consecutive completed "
                    f"milestones reporting an unavailable dependency ({', '.join(streak)}); "
                    "escalate instead of bookkeeping — write a "
                    f"{PROCESS_V7B_ESCALATION_DIR}/<date>-<slug>.md escalation note naming this "
                    "branch or these milestones (template: "
                    f"{PROCESS_V7B_ESCALATION_DIR}/README.md) and set the queue row to blocked",
                )
            )

    return issues


def _validate_metric_extractors(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    extractors = manifest.get("metric_extractors", [])
    if extractors == []:
        return issues
    if not isinstance(extractors, list):
        return [ValidationIssue("error", f"{task.id}: metric_extractors must be a list")]
    for index, extractor in enumerate(extractors):
        prefix = f"{task.id}: metric_extractors[{index}]"
        if not isinstance(extractor, dict):
            issues.append(ValidationIssue("error", f"{prefix} must be an object"))
            continue
        if extractor.get("type", "csv") != "csv":
            issues.append(ValidationIssue("error", f"{prefix} type must be 'csv'"))
        for field in ("metric", "path", "column"):
            if not _non_empty_text(extractor.get(field)):
                issues.append(ValidationIssue("error", f"{prefix} field {field!r} must be non-empty text"))
        match = extractor.get("match", {})
        if not isinstance(match, dict):
            issues.append(ValidationIssue("error", f"{prefix} match must be an object when present"))
    return issues


def _validate_gates(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    gates = manifest.get("gates", [])
    if gates == []:
        return issues
    if not isinstance(gates, list):
        return [ValidationIssue("error", f"{task.id}: gates must be a list")]
    for index, gate in enumerate(gates):
        prefix = f"{task.id}: gates[{index}]"
        if not isinstance(gate, dict):
            issues.append(ValidationIssue("error", f"{prefix} must be an object"))
            continue
        if not _non_empty_text(gate.get("name")):
            issues.append(ValidationIssue("error", f"{prefix} field 'name' must be non-empty text"))
        if gate.get("op") not in GATE_OPERATORS:
            issues.append(ValidationIssue("error", f"{prefix} op must be one of {sorted(GATE_OPERATORS)}"))
        if "threshold" not in gate:
            issues.append(ValidationIssue("error", f"{prefix} must define threshold"))
        has_metric = _non_empty_text(gate.get("metric"))
        has_difference = (
            gate.get("aggregation") == "difference"
            and _non_empty_text(gate.get("left_metric"))
            and _non_empty_text(gate.get("right_metric"))
        )
        if not has_metric and not has_difference:
            issues.append(
                ValidationIssue(
                    "error",
                    f"{prefix} must define either metric or aggregation='difference' with left_metric/right_metric",
                )
            )
    return issues


def _status_counts_match(tasks: list[ResearchTask], status: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_counts = queue_counts(tasks)
    status_counts = status.get("counts")
    if not isinstance(status_counts, dict):
        return [ValidationIssue("error", "research_status.json must contain counts object")]
    for key in sorted(ALLOWED_STATUSES):
        expected = int(expected_counts.get(key, 0))
        actual = int(status_counts.get(key, 0))
        if actual != expected:
            issues.append(ValidationIssue("error", f"status count mismatch for {key}: expected {expected}, got {actual}"))
    return issues


def _expected_next_task(tasks: list[ResearchTask]) -> str | None:
    for status in ("pending", "planned"):
        candidates = [task for task in tasks if task.status == status]
        if candidates:
            return sorted(candidates, key=lambda task: (task.priority, task.id))[0].id
    return None


def validate_research_state(
    root: Path,
    queue_path: Path,
    status_path: Path,
    manifest_dir: Path,
    scoreboard_path: Path,
    enforce_from_priority: int = ENFORCE_FROM_PRIORITY,
    process_v2_from_priority: int = PROCESS_V2_ENFORCE_FROM_PRIORITY,
    process_v3_from_priority: int = PROCESS_V3_SYNTHESIS_ENFORCE_FROM_PRIORITY,
    process_v4_from_priority: int = PROCESS_V4_TRAINING_STAGE_ENFORCE_FROM_PRIORITY,
    process_v5_from_priority: int = PROCESS_V5_SELF_ID_DISCIPLINE_ENFORCE_FROM_PRIORITY,
    process_v6_from_priority: int = PROCESS_V6_LOCAL_SEARCH_GUARD_ENFORCE_FROM_PRIORITY,
    process_v7_from_priority: int = PROCESS_V7_FEASIBILITY_PRICING_ENFORCE_FROM_PRIORITY,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    tasks = load_queue(queue_path)
    task_by_id = {task.id: task for task in tasks}
    if len(task_by_id) != len(tasks):
        issues.append(ValidationIssue("error", "research_queue.csv contains duplicate task ids"))

    status = read_json(status_path)
    issues.extend(_status_counts_match(tasks, status))
    try:
        next_task = normalize_next_task(status.get("next_task"))
    except ValueError as exc:
        issues.append(ValidationIssue("error", str(exc)))
        next_task = None
    expected_next = _expected_next_task(tasks)
    if next_task != expected_next:
        issues.append(ValidationIssue("error", f"next_task mismatch: expected {expected_next!r}, got {next_task!r}"))

    last_result = status.get("last_result")
    if last_result:
        task_id = last_result.get("task_id")
        if task_id and task_id not in task_by_id:
            issues.append(ValidationIssue("error", f"last_result task_id {task_id!r} is not in research_queue.csv"))
        run_dir = last_result.get("run_dir")
        if run_dir and not _path_exists(root, str(run_dir)):
            issues.append(ValidationIssue("error", f"last_result run_dir does not exist: {run_dir}"))
        command_log = last_result.get("command_log")
        if command_log and str(command_log).endswith(".md") and not _path_exists(root, str(command_log)):
            issues.append(ValidationIssue("error", f"last_result command_log document does not exist: {command_log}"))

    if not scoreboard_path.exists():
        issues.append(ValidationIssue("error", f"missing scoreboard: {scoreboard_path}"))
        scoreboard_rows: list[dict[str, str]] = []
    else:
        scoreboard_rows = load_scoreboard(
            scoreboard_path,
            reject_extra_fields_from_milestone=process_v2_from_priority // 10 + 5,
        )
    scoreboard_ids = [row["milestone"] for row in scoreboard_rows]
    scoreboard_by_id = {row["milestone"]: row for row in scoreboard_rows}
    if len(scoreboard_ids) != len(set(scoreboard_ids)):
        issues.append(ValidationIssue("error", "experiments/scoreboard.csv contains duplicate milestone rows"))

    process_v3_records: list[tuple[ResearchTask, dict[str, Any]]] = []
    process_v6_records: list[tuple[ResearchTask, dict[str, Any]]] = []
    for task in tasks:
        if task.status not in ALLOWED_STATUSES:
            issues.append(ValidationIssue("error", f"{task.id}: unknown status {task.status!r}"))
        if task.status == "completed" and task.success_artifact and not _path_exists(root, task.success_artifact):
            if _is_enforced(task, enforce_from_priority):
                issues.append(ValidationIssue("error", f"{task.id}: success_artifact is missing: {task.success_artifact}"))
        if not _is_enforced(task, enforce_from_priority):
            continue
        path = _manifest_path(manifest_dir, task.id)
        if not path.exists():
            issues.append(ValidationIssue("error", f"{task.id}: missing manifest {path}"))
            continue
        manifest = read_json(path)
        process_v2 = _is_process_v2(task, process_v2_from_priority)
        process_v3 = _is_process_v3(task, process_v3_from_priority)
        process_v4 = _is_process_v4(task, process_v4_from_priority)
        process_v5 = _is_process_v5(task, process_v5_from_priority)
        process_v6 = _is_process_v6(task, process_v6_from_priority)
        issues.extend(
            _validate_manifest(
                task,
                manifest,
                process_v2=process_v2,
                process_v3=process_v3,
                process_v4=process_v4,
                process_v5=process_v5,
                process_v6=process_v6,
            )
        )
        if process_v3:
            process_v3_records.append((task, manifest))
        if process_v6:
            process_v6_records.append((task, manifest))
        if task.status == "completed":
            if process_v2 and manifest.get("review_artifact") and not _path_exists(root, str(manifest["review_artifact"])):
                issues.append(ValidationIssue("error", f"{task.id}: review_artifact is missing: {manifest['review_artifact']}"))
            if task.id not in scoreboard_ids:
                issues.append(ValidationIssue("error", f"{task.id}: completed enforced task missing scoreboard row"))
            for artifact in manifest.get("required_artifacts", []):
                artifact_path = artifact.get("path") if isinstance(artifact, dict) else artifact
                if not artifact_path or not _path_exists(root, str(artifact_path)):
                    issues.append(ValidationIssue("error", f"{task.id}: required artifact missing: {artifact_path}"))
            if manifest.get("metric_extractors") and manifest.get("gates") and task.id in scoreboard_by_id:
                try:
                    from autodrift.research_manifest import build_manifest_summary

                    expected = build_manifest_summary(manifest, root=root)
                except Exception as exc:  # pragma: no cover - exact exception type depends on external artifact shape.
                    issues.append(ValidationIssue("error", f"{task.id}: could not recompute structured gates: {exc}"))
                else:
                    actual_decision = scoreboard_by_id[task.id].get("decision", "")
                    if actual_decision != expected.decision:
                        issues.append(
                            ValidationIssue(
                                "error",
                                f"{task.id}: scoreboard decision {actual_decision!r} does not match "
                                f"structured gate decision {expected.decision!r}",
                            )
                        )
    issues.extend(_validate_process_v3_branch_cadence(process_v3_records))
    issues.extend(_validate_process_v6_local_search_cadence(process_v6_records))
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AutoDrift research-process state.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--queue", type=Path, default=Path("experiments/research_queue.csv"))
    parser.add_argument("--status", type=Path, default=Path("experiments/research_status.json"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("experiments/manifests"))
    parser.add_argument("--scoreboard", type=Path, default=Path("experiments/scoreboard.csv"))
    parser.add_argument("--enforce-from-priority", type=int, default=ENFORCE_FROM_PRIORITY)
    parser.add_argument("--process-v2-from-priority", type=int, default=PROCESS_V2_ENFORCE_FROM_PRIORITY)
    parser.add_argument(
        "--process-v3-from-priority",
        type=int,
        default=PROCESS_V3_SYNTHESIS_ENFORCE_FROM_PRIORITY,
    )
    parser.add_argument(
        "--process-v4-from-priority",
        type=int,
        default=PROCESS_V4_TRAINING_STAGE_ENFORCE_FROM_PRIORITY,
    )
    parser.add_argument(
        "--process-v5-from-priority",
        type=int,
        default=PROCESS_V5_SELF_ID_DISCIPLINE_ENFORCE_FROM_PRIORITY,
    )
    parser.add_argument(
        "--process-v6-from-priority",
        type=int,
        default=PROCESS_V6_LOCAL_SEARCH_GUARD_ENFORCE_FROM_PRIORITY,
    )
    args = parser.parse_args()

    issues = validate_research_state(
        root=args.root,
        queue_path=args.queue,
        status_path=args.status,
        manifest_dir=args.manifest_dir,
        scoreboard_path=args.scoreboard,
        enforce_from_priority=args.enforce_from_priority,
        process_v2_from_priority=args.process_v2_from_priority,
        process_v3_from_priority=args.process_v3_from_priority,
        process_v4_from_priority=args.process_v4_from_priority,
        process_v5_from_priority=args.process_v5_from_priority,
        process_v6_from_priority=args.process_v6_from_priority,
    )
    for issue in issues:
        print(f"{issue.severity}: {issue.message}")
    if any(issue.severity == "error" for issue in issues):
        raise SystemExit(1)
    enforced_count = sum(1 for task in load_queue(args.queue) if _is_enforced(task, args.enforce_from_priority))
    print(
        "research validation passed "
        f"(enforce_from_priority={args.enforce_from_priority}, enforced_tasks={enforced_count}, "
        f"process_v2_from_priority={args.process_v2_from_priority}, "
        f"process_v3_from_priority={args.process_v3_from_priority}, "
        f"process_v4_from_priority={args.process_v4_from_priority}, "
        f"process_v5_from_priority={args.process_v5_from_priority}, "
        f"process_v6_from_priority={args.process_v6_from_priority})"
    )


if __name__ == "__main__":
    main()
