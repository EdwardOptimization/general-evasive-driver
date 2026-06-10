"""Research-cycle harness for long-running AutoDrift experiments."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_json


QUEUE_FIELDS = ["id", "priority", "status", "kind", "hypothesis", "command", "success_artifact", "notes"]
ALLOWED_STATUSES = {"planned", "pending", "running", "completed", "failed", "blocked"}


@dataclass(frozen=True)
class ResearchTask:
    id: str
    priority: int
    status: str
    kind: str
    hypothesis: str
    command: str
    success_artifact: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ResearchRunResult:
    task_id: str | None
    status: str
    returncode: int
    run_dir: str | None = None
    command_log: str | None = None


def _validate_task(task: ResearchTask) -> None:
    if not task.id:
        raise ValueError("research task id cannot be empty")
    if task.status not in ALLOWED_STATUSES:
        raise ValueError(f"unknown research task status {task.status!r} for task {task.id!r}")
    if task.status in {"pending", "running"} and not task.command:
        raise ValueError(f"research task {task.id!r} is {task.status} but has no command")


def load_queue(path: Path | str) -> list[ResearchTask]:
    queue_path = Path(path)
    with queue_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != QUEUE_FIELDS:
            raise ValueError(f"research queue must have fields {QUEUE_FIELDS}, got {reader.fieldnames}")
        tasks = [
            ResearchTask(
                id=str(row["id"]).strip(),
                priority=int(row["priority"]),
                status=str(row["status"]).strip(),
                kind=str(row["kind"]).strip(),
                hypothesis=str(row["hypothesis"]).strip(),
                command=str(row["command"]).strip(),
                success_artifact=str(row["success_artifact"]).strip(),
                notes=str(row["notes"]).strip(),
            )
            for row in reader
        ]
    for task in tasks:
        _validate_task(task)
    return tasks


def write_queue(path: Path | str, tasks: list[ResearchTask]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        _validate_task(task)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for task in tasks:
            writer.writerow(asdict(task))


def select_next_task(tasks: list[ResearchTask]) -> ResearchTask | None:
    pending = [task for task in tasks if task.status == "pending"]
    if not pending:
        return None
    return sorted(pending, key=lambda task: (task.priority, task.id))[0]


def select_next_status_task(tasks: list[ResearchTask]) -> ResearchTask | None:
    for status in ("pending", "planned"):
        candidates = [task for task in tasks if task.status == status]
        if candidates:
            return sorted(candidates, key=lambda task: (task.priority, task.id))[0]
    return None


def queue_counts(tasks: list[ResearchTask]) -> dict[str, int]:
    return {status: sum(1 for task in tasks if task.status == status) for status in sorted(ALLOWED_STATUSES)}


def _task_to_json(task: ResearchTask | None) -> dict[str, Any] | None:
    return asdict(task) if task is not None else None


def write_research_status(
    path: Path | str,
    tasks: list[ResearchTask],
    next_task: ResearchTask | None,
    last_result: ResearchRunResult | None = None,
) -> None:
    write_json(
        path,
        {
            "updated_at_utc": utc_timestamp(),
            "counts": queue_counts(tasks),
            "next_task": _task_to_json(next_task),
            "last_result": asdict(last_result) if last_result is not None else None,
        },
    )


def _load_last_result(path: Path | str) -> ResearchRunResult | None:
    status_path = Path(path)
    if not status_path.exists():
        return None
    data = read_json(status_path)
    last_result = data.get("last_result")
    if not last_result:
        return None
    return ResearchRunResult(
        task_id=last_result.get("task_id"),
        status=str(last_result.get("status", "unknown")),
        returncode=int(last_result.get("returncode", 0)),
        run_dir=last_result.get("run_dir"),
        command_log=last_result.get("command_log"),
    )


def plan_next_task(queue_path: Path | str, status_path: Path | str) -> ResearchTask | None:
    tasks = load_queue(queue_path)
    next_task = select_next_status_task(tasks)
    write_research_status(status_path, tasks, next_task, last_result=_load_last_result(status_path))
    return next_task


def _replace_task(tasks: list[ResearchTask], task_id: str, **updates: Any) -> list[ResearchTask]:
    return [replace(task, **updates) if task.id == task_id else task for task in tasks]


def _resolve_artifact(path: str, cwd: Path) -> Path:
    artifact = Path(path)
    return artifact if artifact.is_absolute() else cwd / artifact


def _command_argv_and_env(command: str) -> tuple[list[str], dict[str, str] | None]:
    parts = shlex.split(command)
    env_updates: dict[str, str] = {}
    while parts and _is_env_assignment(parts[0]):
        key, value = parts.pop(0).split("=", 1)
        env_updates[key] = value
    if not parts:
        raise ValueError("research task command has no executable")
    if not env_updates:
        return parts, None
    env = os.environ.copy()
    env.update(env_updates)
    return parts, env


def _is_env_assignment(token: str) -> bool:
    if "=" not in token:
        return False
    key, _value = token.split("=", 1)
    if not key:
        return False
    return all(char == "_" or char.isalnum() for char in key) and not key[0].isdigit()


def append_research_log(path: Path | str, task: ResearchTask, result: ResearchRunResult) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        today = datetime.now(timezone.utc).date().isoformat()
        output.write_text(f"# AutoDrift Research Log\n\nLast updated: {today}\n\n", encoding="utf-8")
    with output.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(f"## {utc_timestamp()} {task.id}\n\n")
        handle.write(f"- status: `{result.status}`\n")
        handle.write(f"- kind: `{task.kind}`\n")
        handle.write(f"- hypothesis: {task.hypothesis}\n")
        handle.write(f"- command: `{task.command}`\n")
        handle.write(f"- returncode: `{result.returncode}`\n")
        if result.run_dir is not None:
            handle.write(f"- run dir: `{result.run_dir}`\n")
        if result.command_log is not None:
            handle.write(f"- command log: `{result.command_log}`\n")
        if task.success_artifact:
            handle.write(f"- success artifact: `{task.success_artifact}`\n")
        if task.notes:
            handle.write(f"- notes: {task.notes}\n")
        handle.write("\n")


def run_next_task(
    queue_path: Path | str,
    status_path: Path | str,
    log_path: Path | str,
    cwd: Path | str = ".",
    run_root: Path | str = "runs/research",
) -> ResearchRunResult:
    cwd_path = Path(cwd)
    tasks = load_queue(queue_path)
    task = select_next_task(tasks)
    if task is None:
        result = ResearchRunResult(task_id=None, status="idle", returncode=0)
        write_research_status(
            status_path,
            tasks,
            select_next_status_task(tasks),
            last_result=_load_last_result(status_path) or result,
        )
        return result

    running_task = replace(task, status="running")
    tasks = _replace_task(tasks, task.id, status="running")
    write_queue(queue_path, tasks)
    write_research_status(status_path, tasks, running_task)

    run_dir = Path(run_root) / f"{task.id}_{utc_timestamp()}"
    if not run_dir.is_absolute():
        run_dir = cwd_path / run_dir
    run_dir.mkdir(parents=True, exist_ok=False)
    command_log = run_dir / "command.log"
    argv, env = _command_argv_and_env(task.command)
    with command_log.open("w", encoding="utf-8") as handle:
        handle.write(task.command + "\n\n")
        handle.flush()
        process = subprocess.run(
            argv,
            cwd=cwd_path,
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )

    artifact_ok = True
    if task.success_artifact:
        artifact_ok = _resolve_artifact(task.success_artifact, cwd_path).exists()
    final_status = "completed" if process.returncode == 0 and artifact_ok else "failed"
    tasks = _replace_task(tasks, task.id, status=final_status)
    write_queue(queue_path, tasks)
    next_task = select_next_status_task(tasks)
    result = ResearchRunResult(
        task_id=task.id,
        status=final_status,
        returncode=int(process.returncode),
        run_dir=str(run_dir),
        command_log=str(command_log),
    )
    write_research_status(status_path, tasks, next_task, last_result=result)
    append_research_log(log_path, task, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or run the next AutoDrift research task.")
    parser.add_argument("--queue", type=Path, default=Path("experiments/research_queue.csv"))
    parser.add_argument("--status", type=Path, default=Path("experiments/research_status.json"))
    parser.add_argument("--log", type=Path, default=Path("docs/research-log.md"))
    parser.add_argument("--cwd", type=Path, default=Path("."))
    parser.add_argument("--run-root", type=Path, default=Path("runs/research"))
    parser.add_argument("--mode", choices=["plan", "run-next"], default="plan")
    args = parser.parse_args()

    if args.mode == "plan":
        task = plan_next_task(args.queue, args.status)
        if task is None:
            print("next_task=none")
        else:
            print(f"next_task={task.id}")
            print(f"command={task.command}")
        return

    result = run_next_task(args.queue, args.status, args.log, cwd=args.cwd, run_root=args.run_root)
    print(f"task={result.task_id or 'none'} status={result.status} returncode={result.returncode}")
    if result.run_dir is not None:
        print(f"run_dir={result.run_dir}")


if __name__ == "__main__":
    main()
