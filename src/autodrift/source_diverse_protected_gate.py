"""Run a source-diverse protected replay-gate bundle."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec


@dataclass(frozen=True)
class ReplayGateSpec:
    label: str
    corpus_csv: Path
    baseline_policy: str
    candidate_policy: str


@dataclass(frozen=True)
class DiagnosticCsvSpec:
    label: str
    csv_path: Path


def parse_replay_gate_spec(raw: str) -> ReplayGateSpec:
    """Parse NAME=CORPUS_CSV,BASELINE_POLICY,CANDIDATE_POLICY."""

    if "=" not in raw:
        raise ValueError(f"replay gate spec must be NAME=CORPUS,BASELINE,CANDIDATE, got {raw!r}")
    label, payload = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise ValueError(f"replay gate spec has empty name: {raw!r}")
    parts = [part.strip() for part in payload.split(",")]
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"replay gate spec must be NAME=CORPUS,BASELINE,CANDIDATE, got {raw!r}")
    if parts[1] == parts[2]:
        raise ValueError(f"replay gate {label!r} must use different baseline and candidate policies")
    return ReplayGateSpec(
        label=label,
        corpus_csv=Path(parts[0]),
        baseline_policy=parts[1],
        candidate_policy=parts[2],
    )


def parse_diagnostic_csv_spec(raw: str) -> DiagnosticCsvSpec:
    """Parse NAME=CSV_PATH."""

    if "=" not in raw:
        raise ValueError(f"diagnostic CSV spec must be NAME=PATH, got {raw!r}")
    label, path = raw.split("=", 1)
    label = label.strip()
    path = path.strip()
    if not label or not path:
        raise ValueError(f"diagnostic CSV spec must be NAME=PATH, got {raw!r}")
    return DiagnosticCsvSpec(label=label, csv_path=Path(path))


def _checkpoint_lookup(specs: tuple[CheckpointSpec, ...]) -> dict[str, CheckpointSpec]:
    lookup: dict[str, CheckpointSpec] = {}
    for spec in specs:
        if spec.label in lookup:
            raise ValueError(f"duplicate checkpoint policy label: {spec.label}")
        lookup[spec.label] = spec
    return lookup


def _checkpoint_specs_for_gate(
    lookup: dict[str, CheckpointSpec],
    gate_spec: ReplayGateSpec,
) -> tuple[CheckpointSpec, CheckpointSpec]:
    missing = [
        label
        for label in (gate_spec.baseline_policy, gate_spec.candidate_policy)
        if label not in lookup
    ]
    if missing:
        raise ValueError(f"replay gate {gate_spec.label!r} references missing policies: {', '.join(missing)}")
    return (lookup[gate_spec.baseline_policy], lookup[gate_spec.candidate_policy])


def ingest_diagnostic_csv(spec: DiagnosticCsvSpec) -> dict[str, Any]:
    frame = pd.read_csv(spec.csv_path)
    result: dict[str, Any] = {
        "label": spec.label,
        "csv_path": spec.csv_path,
        "rows": int(len(frame)),
    }
    if "accepted" in frame:
        accepted = frame["accepted"].astype(bool)
        result["accepted_rows"] = int(accepted.sum())
        result["accepted_fraction"] = float(accepted.mean()) if len(accepted) else 0.0
    if "policy" in frame:
        result["policies"] = sorted(str(policy) for policy in frame["policy"].unique())
    if "normal_margin" in frame:
        result["normal_margin_max"] = float(frame["normal_margin"].astype(float).max())
        result["normal_margin_min"] = float(frame["normal_margin"].astype(float).min())
    if "margin_gap" in frame:
        result["margin_gap_min"] = float(frame["margin_gap"].astype(float).min())
        result["margin_gap_max"] = float(frame["margin_gap"].astype(float).max())
    return result


def aggregate_results(
    replay_summaries: list[dict[str, Any]],
    diagnostic_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [summary["label"] for summary in replay_summaries if not bool(summary.get("gate_pass", False))]
    return {
        "run_type": "source_diverse_protected_gate",
        "actor_inputs_changed": False,
        "replay_gate_count": len(replay_summaries),
        "replay_gates_passed": len(replay_summaries) - len(failed),
        "replay_gates_failed": len(failed),
        "failed_replay_gates": failed,
        "diagnostic_count": len(diagnostic_summaries),
        "overall_pass": len(failed) == 0,
        "failure_types": ["none"] if not failed else ["proof_washout"],
    }


def run_source_diverse_protected_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    replay_gate_specs: tuple[ReplayGateSpec, ...],
    diagnostic_csv_specs: tuple[DiagnosticCsvSpec, ...],
    env_config_path: Path,
    max_rows: int,
    max_continuation_steps: int,
    max_normal_success_drop: float,
    max_normal_margin_regression: float,
    max_margin_gap_regression: float,
    max_success_drop_count_regression: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_lookup = _checkpoint_lookup(checkpoint_specs)
    replay_summaries: list[dict[str, Any]] = []
    for gate_spec in replay_gate_specs:
        gate_run_dir = run_dir / "replay_gates" / gate_spec.label
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=_checkpoint_specs_for_gate(checkpoint_lookup, gate_spec),
            corpus_csv=gate_spec.corpus_csv,
            env_config_path=env_config_path,
            max_rows=max_rows,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=gate_spec.baseline_policy,
            candidate_policy=gate_spec.candidate_policy,
            max_normal_success_drop=max_normal_success_drop,
            max_normal_margin_regression=max_normal_margin_regression,
            max_margin_gap_regression=max_margin_gap_regression,
            max_success_drop_count_regression=max_success_drop_count_regression,
            device=device,
            run_dir=gate_run_dir,
        )
        replay_summaries.append(
            {
                "label": gate_spec.label,
                "run_dir": gate_run_dir,
                "corpus_csv": gate_spec.corpus_csv,
                "baseline_policy": gate_spec.baseline_policy,
                "candidate_policy": gate_spec.candidate_policy,
                "rows": int(summary["rows"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "gate_pass": bool(summary["gate_pass"]),
            }
        )
    diagnostic_summaries = [ingest_diagnostic_csv(spec) for spec in diagnostic_csv_specs]
    aggregate = aggregate_results(replay_summaries, diagnostic_summaries)
    result = {
        **aggregate,
        "env_config": env_config_path,
        "max_rows": int(max_rows),
        "max_continuation_steps": int(max_continuation_steps),
        "checkpoint_policies": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "replay_gates": replay_summaries,
        "diagnostics": diagnostic_summaries,
        "replay_gate_summary_csv": run_dir / "replay_gate_summary.csv",
        "diagnostic_summary_csv": run_dir / "diagnostic_summary.csv",
    }
    write_csv_rows(run_dir / "replay_gate_summary.csv", replay_summaries)
    write_csv_rows(run_dir / "diagnostic_summary.csv", diagnostic_summaries)
    write_json(run_dir / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a source-diverse protected replay-gate bundle.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--replay-gate", action="append", type=parse_replay_gate_spec, required=True)
    parser.add_argument("--diagnostic-csv", action="append", type=parse_diagnostic_csv_spec, default=[])
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--max-normal-success-drop", type=float, default=0.0)
    parser.add_argument("--max-normal-margin-regression", type=float, default=0.005)
    parser.add_argument("--max-margin-gap-regression", type=float, default=0.001)
    parser.add_argument("--max-success-drop-count-regression", type=int, default=0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="source_diverse_protected_gate")
    result = run_source_diverse_protected_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        replay_gate_specs=tuple(args.replay_gate),
        diagnostic_csv_specs=tuple(args.diagnostic_csv),
        env_config_path=args.env_config,
        max_rows=args.max_rows,
        max_continuation_steps=args.max_continuation_steps,
        max_normal_success_drop=args.max_normal_success_drop,
        max_normal_margin_regression=args.max_normal_margin_regression,
        max_margin_gap_regression=args.max_margin_gap_regression,
        max_success_drop_count_regression=args.max_success_drop_count_regression,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series({key: value for key, value in result.items() if key not in {"replay_gates", "diagnostics"}}).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
