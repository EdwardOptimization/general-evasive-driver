"""Public proof gate for the M1061 family-intersection corpora."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec


@dataclass(frozen=True)
class SourceCorpusSpec:
    label: str
    corpus_csv: Path


def parse_source_corpus_spec(raw: str) -> SourceCorpusSpec:
    if "=" not in raw:
        raise ValueError(f"source corpus spec must be LABEL=PATH, got {raw!r}")
    label, path = raw.split("=", 1)
    label = label.strip()
    path = path.strip()
    if not label or not path:
        raise ValueError(f"source corpus spec must be LABEL=PATH, got {raw!r}")
    return SourceCorpusSpec(label=label, corpus_csv=Path(path))


def checkpoint_lookup(specs: tuple[CheckpointSpec, ...]) -> dict[str, CheckpointSpec]:
    lookup: dict[str, CheckpointSpec] = {}
    for spec in specs:
        if spec.label in lookup:
            raise ValueError(f"duplicate checkpoint policy label: {spec.label}")
        lookup[spec.label] = spec
    return lookup


def corpus_lookup(specs: tuple[SourceCorpusSpec, ...]) -> dict[str, SourceCorpusSpec]:
    lookup: dict[str, SourceCorpusSpec] = {}
    for spec in specs:
        if spec.label in lookup:
            raise ValueError(f"duplicate source corpus label: {spec.label}")
        lookup[spec.label] = spec
    return lookup


def validate_family_gate_specs(
    *,
    source_policies: tuple[CheckpointSpec, ...],
    source_corpora: tuple[SourceCorpusSpec, ...],
    candidate_policy: CheckpointSpec,
) -> tuple[dict[str, CheckpointSpec], dict[str, SourceCorpusSpec]]:
    sources = checkpoint_lookup(source_policies)
    corpora = corpus_lookup(source_corpora)
    if set(sources) != set(corpora):
        missing_corpora = sorted(set(sources) - set(corpora))
        missing_sources = sorted(set(corpora) - set(sources))
        details = []
        if missing_corpora:
            details.append("missing corpora for " + ", ".join(missing_corpora))
        if missing_sources:
            details.append("missing source policies for " + ", ".join(missing_sources))
        raise ValueError("source policy and corpus labels must match: " + "; ".join(details))
    if candidate_policy.label in sources:
        raise ValueError("candidate policy label must differ from source policy labels")
    for label, spec in sources.items():
        if not spec.path.exists():
            raise FileNotFoundError(f"source checkpoint {label!r} does not exist: {spec.path}")
    for label, spec in corpora.items():
        if not spec.corpus_csv.exists():
            raise FileNotFoundError(f"source corpus {label!r} does not exist: {spec.corpus_csv}")
    if not candidate_policy.path.exists():
        raise FileNotFoundError(f"candidate checkpoint does not exist: {candidate_policy.path}")
    return sources, corpora


def actor_input_signature(checkpoint_path: Path) -> dict[str, Any]:
    model, checkpoint = load_actor_critic_checkpoint(checkpoint_path, device="cpu")
    config = checkpoint.get("config", {})
    return {
        "obs_dim": int(model.obs_dim),
        "act_dim": int(model.act_dim),
        "actor_encoder": str(getattr(model, "actor_encoder", "")),
        "actor_history_length": int(getattr(model, "actor_history_length", 1)),
        "action_sequence_horizon": int(getattr(model, "action_sequence_horizon", 1)),
        "config_actor_encoder": str(config.get("actor_encoder", "")),
    }


def family_actor_inputs_changed(
    *,
    source_policies: tuple[CheckpointSpec, ...],
    candidate_policy: CheckpointSpec,
) -> bool:
    candidate_signature = actor_input_signature(candidate_policy.path)
    return any(actor_input_signature(spec.path) != candidate_signature for spec in source_policies)


def classify_family_intersection_public_gate(
    *,
    actor_inputs_changed: bool,
    replay_gates_passed: int,
    replay_gate_count: int,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
    private_holdout_used: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted) or bool(private_holdout_used):
        return "family_intersection_public_gate_contract_artifact"
    if int(replay_gates_passed) != int(replay_gate_count):
        return "family_intersection_public_gate_proof_washout"
    return "family_intersection_public_gate_pass"


def failure_types_for_family_intersection_gate(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    return ["metric_artifact"]


def run_family_intersection_public_gate(
    *,
    source_policies: tuple[CheckpointSpec, ...],
    source_corpora: tuple[SourceCorpusSpec, ...],
    candidate_policy: CheckpointSpec,
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
    sources, corpora = validate_family_gate_specs(
        source_policies=source_policies,
        source_corpora=source_corpora,
        candidate_policy=candidate_policy,
    )
    actor_inputs_changed = family_actor_inputs_changed(
        source_policies=source_policies,
        candidate_policy=candidate_policy,
    )
    replay_rows: list[dict[str, Any]] = []
    for label in sorted(sources):
        source = sources[label]
        corpus = corpora[label]
        gate_label = f"{label}_to_{candidate_policy.label}"
        gate_dir = run_dir / "replay_gates" / gate_label
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=(source, candidate_policy),
            corpus_csv=corpus.corpus_csv,
            env_config_path=env_config_path,
            max_rows=max_rows,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=source.label,
            candidate_policy=candidate_policy.label,
            max_normal_success_drop=max_normal_success_drop,
            max_normal_margin_regression=max_normal_margin_regression,
            max_margin_gap_regression=max_margin_gap_regression,
            max_success_drop_count_regression=max_success_drop_count_regression,
            device=device,
            run_dir=gate_dir,
        )
        replay_rows.append(
            {
                "label": gate_label,
                "source_policy": source.label,
                "candidate_policy": candidate_policy.label,
                "source_checkpoint": str(source.path),
                "candidate_checkpoint": str(candidate_policy.path),
                "corpus_csv": str(corpus.corpus_csv),
                "run_dir": str(gate_dir),
                "rows": int(summary["rows"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "gate_pass": bool(summary["gate_pass"]) and not bool(actor_inputs_changed),
            }
        )
    replay_gates_passed = int(sum(1 for row in replay_rows if bool(row["gate_pass"])))
    result_class = classify_family_intersection_public_gate(
        actor_inputs_changed=actor_inputs_changed,
        replay_gates_passed=replay_gates_passed,
        replay_gate_count=len(replay_rows),
        training_started=False,
        ppo_used=False,
        promoted=False,
        private_holdout_used=False,
    )
    diagnostic_rows = [
        {
            "source_policy": label,
            "source_checkpoint": str(sources[label].path),
            "source_corpus": str(corpora[label].corpus_csv),
        }
        for label in sorted(sources)
    ]
    summary = {
        "run_type": "family_intersection_public_gate",
        "source_policy_count": int(len(sources)),
        "source_corpus_count": int(len(corpora)),
        "candidate_policy": candidate_policy.label,
        "candidate_checkpoint": candidate_policy.path,
        "env_config": env_config_path,
        "max_rows": int(max_rows),
        "max_continuation_steps": int(max_continuation_steps),
        "replay_gate_count": int(len(replay_rows)),
        "replay_gates_passed": replay_gates_passed,
        "failed_replay_gates": [row["label"] for row in replay_rows if not bool(row["gate_pass"])],
        "actor_inputs_changed": bool(actor_inputs_changed),
        "overall_pass": bool(result_class.endswith("_pass")),
        "result_class": result_class,
        "failure_types": failure_types_for_family_intersection_gate(result_class),
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "replay_gate_summary_csv": run_dir / "replay_gate_summary.csv",
        "diagnostic_summary_csv": run_dir / "diagnostic_summary.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_csv_rows(run_dir / "replay_gate_summary.csv", replay_rows)
    write_csv_rows(run_dir / "diagnostic_summary.csv", diagnostic_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M1061 family-intersection public proof gate.")
    parser.add_argument("--source-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--source-corpus", action="append", type=parse_source_corpus_spec, required=True)
    parser.add_argument("--candidate-policy", type=parse_checkpoint_spec, required=True)
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

    run_dir = args.run_dir or make_run_dir(prefix="family_intersection_public_gate")
    summary = run_family_intersection_public_gate(
        source_policies=tuple(args.source_policy),
        source_corpora=tuple(args.source_corpus),
        candidate_policy=args.candidate_policy,
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
    print(pd.Series({key: value for key, value in summary.items() if key not in {"replay_gates"}}).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
