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
from autodrift.research_schema import SCOREBOARD_FIELDS


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


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    message: str


def _is_enforced(task: ResearchTask, enforce_from_priority: int) -> bool:
    return int(task.priority) >= int(enforce_from_priority)


def _manifest_path(manifest_dir: Path, task_id: str) -> Path:
    return manifest_dir / f"{task_id}.json"


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _path_exists(root: Path, path_text: str) -> bool:
    path = Path(path_text)
    return path.exists() if path.is_absolute() else (root / path).exists()


def normalize_next_task(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        task_id = value.get("id")
        return str(task_id) if task_id else None
    raise ValueError(f"research_status next_task must be string, object, or null, got {type(value).__name__}")


def load_scoreboard(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SCOREBOARD_FIELDS:
            raise ValueError(f"scoreboard must have fields {SCOREBOARD_FIELDS}, got {reader.fieldnames}")
        return [dict(row) for row in reader]


def _validate_manifest(task: ResearchTask, manifest: dict[str, Any]) -> list[ValidationIssue]:
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
        scoreboard_rows = load_scoreboard(scoreboard_path)
    scoreboard_ids = [row["milestone"] for row in scoreboard_rows]
    scoreboard_by_id = {row["milestone"]: row for row in scoreboard_rows}
    if len(scoreboard_ids) != len(set(scoreboard_ids)):
        issues.append(ValidationIssue("error", "experiments/scoreboard.csv contains duplicate milestone rows"))

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
        issues.extend(_validate_manifest(task, manifest))
        if task.status == "completed":
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
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AutoDrift research-process state.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--queue", type=Path, default=Path("experiments/research_queue.csv"))
    parser.add_argument("--status", type=Path, default=Path("experiments/research_status.json"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("experiments/manifests"))
    parser.add_argument("--scoreboard", type=Path, default=Path("experiments/scoreboard.csv"))
    parser.add_argument("--enforce-from-priority", type=int, default=ENFORCE_FROM_PRIORITY)
    args = parser.parse_args()

    issues = validate_research_state(
        root=args.root,
        queue_path=args.queue,
        status_path=args.status,
        manifest_dir=args.manifest_dir,
        scoreboard_path=args.scoreboard,
        enforce_from_priority=args.enforce_from_priority,
    )
    for issue in issues:
        print(f"{issue.severity}: {issue.message}")
    if any(issue.severity == "error" for issue in issues):
        raise SystemExit(1)
    enforced_count = sum(1 for task in load_queue(args.queue) if _is_enforced(task, args.enforce_from_priority))
    print(
        "research validation passed "
        f"(enforce_from_priority={args.enforce_from_priority}, enforced_tasks={enforced_count})"
    )


if __name__ == "__main__":
    main()
