"""Executable manifest support for the AutoDrift research harness."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_json
from autodrift.research_schema import SCOREBOARD_FIELDS


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: str
    returncode: int
    log_path: str
    started_at_utc: str
    ended_at_utc: str
    elapsed_seconds: float


@dataclass(frozen=True)
class GateResult:
    name: str
    value: float
    op: str
    threshold: float
    passed: bool


@dataclass(frozen=True)
class ManifestSummary:
    metrics: dict[str, float | str | None]
    gates: list[GateResult]
    decision: str
    reason: str
    scoreboard_row: dict[str, str]


def _resolve(root: Path, path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _row_matches(row: dict[str, str], match: dict[str, Any]) -> bool:
    return all(str(row.get(key, "")) == str(value) for key, value in match.items())


def _coerce_metric(value: str, metric_name: str) -> float | str | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return value


def extract_manifest_metrics(manifest: dict[str, Any], root: Path | str = ".") -> dict[str, float | str | None]:
    """Extract named metrics from manifest-declared artifacts."""

    root_path = Path(root)
    metrics: dict[str, float | str | None] = {}
    for spec in manifest.get("metric_extractors", []):
        if spec.get("type", "csv") != "csv":
            raise ValueError(f"unsupported metric extractor type: {spec.get('type')!r}")
        metric_name = str(spec["metric"])
        csv_path = _resolve(root_path, spec["path"])
        rows = _read_csv_rows(csv_path)
        match = spec.get("match", {})
        matches = [row for row in rows if _row_matches(row, match)]
        if not matches:
            raise ValueError(f"metric {metric_name!r} found no row in {csv_path} for match {match}")
        if len(matches) > 1:
            raise ValueError(f"metric {metric_name!r} matched {len(matches)} rows in {csv_path}")
        column = str(spec["column"])
        if column not in matches[0]:
            raise ValueError(f"metric {metric_name!r} column {column!r} is missing from {csv_path}")
        metrics[metric_name] = _coerce_metric(matches[0][column], metric_name)
    return metrics


def _metric_as_float(metrics: dict[str, float | str | None], name: str) -> float:
    value = metrics.get(name)
    if value is None:
        raise ValueError(f"metric {name!r} is missing")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"metric {name!r} is not numeric: {value!r}") from exc


def _gate_value(gate: dict[str, Any], metrics: dict[str, float | str | None]) -> float:
    if "metric" in gate:
        return _metric_as_float(metrics, str(gate["metric"]))
    if gate.get("aggregation") == "difference":
        left = _metric_as_float(metrics, str(gate["left_metric"]))
        right = _metric_as_float(metrics, str(gate["right_metric"]))
        return left - right
    raise ValueError(f"gate {gate.get('name', '<unnamed>')!r} has no supported value expression")


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    if op == "!=":
        return value != threshold
    raise ValueError(f"unsupported gate operator: {op!r}")


def evaluate_manifest_gates(manifest: dict[str, Any], metrics: dict[str, float | str | None]) -> list[GateResult]:
    results: list[GateResult] = []
    for gate in manifest.get("gates", []):
        value = _gate_value(gate, metrics)
        threshold = float(gate["threshold"])
        op = str(gate["op"])
        results.append(
            GateResult(
                name=str(gate["name"]),
                value=value,
                op=op,
                threshold=threshold,
                passed=_compare(value, op, threshold),
            )
        )
    return results


def _format_scoreboard_value(value: float | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _decision_labels(manifest: dict[str, Any]) -> tuple[str, str]:
    labels = manifest.get("decision_labels", {})
    if not isinstance(labels, dict):
        return "accepted", "rejected"
    return str(labels.get("pass", "accepted")), str(labels.get("fail", "rejected"))


def build_manifest_summary(manifest: dict[str, Any], root: Path | str = ".") -> ManifestSummary:
    metrics = extract_manifest_metrics(manifest, root=root)
    gates = evaluate_manifest_gates(manifest, metrics)
    pass_label, fail_label = _decision_labels(manifest)
    if not gates:
        decision = "manual_review"
        reason = "no structured gates defined"
    else:
        passed = all(gate.passed for gate in gates)
        decision = pass_label if passed else fail_label
        if passed:
            reason = "all structured gates passed"
        else:
            failures = [
                f"{gate.name}={gate.value:.6g} {gate.op} {gate.threshold:.6g}"
                for gate in gates
                if not gate.passed
            ]
            reason = "failed gates: " + "; ".join(failures)

    row = {field: "" for field in SCOREBOARD_FIELDS}
    row["milestone"] = str(manifest["id"])
    row["type"] = str(manifest["type"])
    row["checkpoint"] = str(manifest.get("scoreboard_checkpoint", ""))
    for field in SCOREBOARD_FIELDS:
        if field in metrics:
            row[field] = _format_scoreboard_value(metrics[field])
    row["decision"] = decision
    row["reason"] = reason
    return ManifestSummary(metrics=metrics, gates=gates, decision=decision, reason=reason, scoreboard_row=row)


def upsert_scoreboard_row(scoreboard_path: Path | str, row: dict[str, str]) -> None:
    path = Path(scoreboard_path)
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != SCOREBOARD_FIELDS:
                raise ValueError(f"scoreboard must have fields {SCOREBOARD_FIELDS}, got {reader.fieldnames}")
            rows = [dict(existing) for existing in reader if existing["milestone"] != row["milestone"]]
    rows.append({field: str(row.get(field, "")) for field in SCOREBOARD_FIELDS})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCOREBOARD_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _git_text(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifact_provenance(manifest: dict[str, Any], root: Path | str = ".") -> list[dict[str, Any]]:
    root_path = Path(root)
    artifacts: list[dict[str, Any]] = []
    for spec in manifest.get("required_artifacts", []):
        path_text = spec.get("path") if isinstance(spec, dict) else spec
        if not path_text:
            continue
        path = _resolve(root_path, str(path_text))
        record: dict[str, Any] = {"path": str(path_text), "exists": path.exists()}
        if path.exists() and path.is_file():
            record["size_bytes"] = path.stat().st_size
            record["sha256"] = _sha256(path)
        artifacts.append(record)
    return artifacts


def write_run_receipt(
    manifest: dict[str, Any],
    run_dir: Path | str,
    command_results: list[CommandResult],
    root: Path | str = ".",
) -> Path:
    root_path = Path(root)
    output_dir = Path(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "manifest_id": manifest["id"],
        "status": "completed" if all(result.returncode == 0 for result in command_results) else "failed",
        "created_at_utc": utc_timestamp(),
        "root": str(root_path.resolve()),
        "git": {
            "commit": _git_text(root_path, "rev-parse", "HEAD"),
            "status_short": _git_text(root_path, "status", "--short"),
        },
        "runtime": {
            "python": sys.executable,
            "platform": platform.platform(),
            "pid": os.getpid(),
        },
        "commands": [asdict(result) for result in command_results],
        "required_artifacts": collect_artifact_provenance(manifest, root=root_path),
    }
    receipt_path = output_dir / "run_receipt.json"
    write_json(receipt_path, receipt)
    return receipt_path


def run_manifest_commands(
    manifest: dict[str, Any],
    root: Path | str = ".",
    run_dir: Path | str | None = None,
    stop_on_failure: bool = True,
) -> list[CommandResult]:
    root_path = Path(root)
    output_dir = (
        Path(run_dir)
        if run_dir is not None
        else root_path / "runs" / "research_manifest" / f"{manifest['id']}_{utc_timestamp()}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[CommandResult] = []
    for index, spec in enumerate(manifest.get("commands", []), start=1):
        name = str(spec.get("name", f"command_{index:02d}"))
        command = str(spec["command"])
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        log_path = output_dir / f"{index:02d}_{safe_name}.log"
        started = utc_timestamp()
        start_time = time.monotonic()
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(command + "\n\n")
            handle.flush()
            process = subprocess.run(
                command,
                cwd=root_path,
                shell=True,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        ended = utc_timestamp()
        result = CommandResult(
            name=name,
            command=command,
            returncode=int(process.returncode),
            log_path=str(log_path),
            started_at_utc=started,
            ended_at_utc=ended,
            elapsed_seconds=time.monotonic() - start_time,
        )
        results.append(result)
        if stop_on_failure and result.returncode != 0:
            break
    write_run_receipt(manifest, output_dir, results, root=root_path)
    return results


def load_manifest(path: Path | str) -> dict[str, Any]:
    return read_json(path)


def summarize_manifest_to_scoreboard(
    manifest_path: Path | str,
    scoreboard_path: Path | str,
    root: Path | str = ".",
) -> ManifestSummary:
    manifest = load_manifest(manifest_path)
    summary = build_manifest_summary(manifest, root=root)
    upsert_scoreboard_row(scoreboard_path, summary.scoreboard_row)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or summarize an AutoDrift research manifest.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    run_parser = subparsers.add_parser("run", help="Run manifest commands and write a run receipt.")
    run_parser.add_argument("--manifest", type=Path, required=True)
    run_parser.add_argument("--root", type=Path, default=Path("."))
    run_parser.add_argument("--run-dir", type=Path, default=None)
    run_parser.add_argument("--scoreboard", type=Path, default=None)
    run_parser.add_argument("--no-stop-on-failure", action="store_true")

    summarize_parser = subparsers.add_parser("summarize", help="Extract metrics, evaluate gates, and update scoreboard.")
    summarize_parser.add_argument("--manifest", type=Path, required=True)
    summarize_parser.add_argument("--root", type=Path, default=Path("."))
    summarize_parser.add_argument("--scoreboard", type=Path, default=Path("experiments/scoreboard.csv"))

    args = parser.parse_args()
    if args.mode == "run":
        manifest = load_manifest(args.manifest)
        results = run_manifest_commands(
            manifest,
            root=args.root,
            run_dir=args.run_dir,
            stop_on_failure=not args.no_stop_on_failure,
        )
        failed = [result for result in results if result.returncode != 0]
        print(f"manifest={manifest['id']} commands={len(results)} failed={len(failed)}")
        if results:
            print(f"run_dir={Path(results[0].log_path).parent}")
        if args.scoreboard is not None and not failed:
            summary = summarize_manifest_to_scoreboard(args.manifest, args.scoreboard, root=args.root)
            print(f"decision={summary.decision} reason={summary.reason}")
        if failed:
            raise SystemExit(1)
        return

    summary = summarize_manifest_to_scoreboard(args.manifest, args.scoreboard, root=args.root)
    print(f"decision={summary.decision}")
    print(f"reason={summary.reason}")


if __name__ == "__main__":
    main()
