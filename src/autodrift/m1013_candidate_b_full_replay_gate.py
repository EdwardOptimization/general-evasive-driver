"""Full public replay gate for M1013 Candidate B."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.capability_step_temporal_sequence_public_replay_gate import (
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_BASE_SUMMARY,
    DEFAULT_CORPUS,
    DEFAULT_ENV_CONFIG,
    run_temporal_sequence_public_replay_gate,
)


DEFAULT_CANDIDATE_B_CHECKPOINT = Path(
    "runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt"
)
DEFAULT_RUN_DIR = Path("runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate")


def classify_m1019_gate(
    *,
    actor_inputs_changed: bool,
    exact_contract_pass_count: int,
    candidate_preflight_pass_count: int,
    six_public_replay_gates_pass: bool,
    source_diverse_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "m1013_candidate_b_full_replay_gate_contract_artifact"
    if int(exact_contract_pass_count) <= 0:
        return "m1013_candidate_b_full_replay_gate_exact_retention_failed"
    if int(candidate_preflight_pass_count) <= 0:
        return "m1013_candidate_b_full_replay_gate_m267_preflight_failed"
    if not bool(six_public_replay_gates_pass):
        return "m1013_candidate_b_full_replay_gate_public_replay_proof_washout"
    if not bool(source_diverse_pass):
        return "m1013_candidate_b_full_replay_gate_source_diverse_diagnostic_failed"
    if not bool(behavior_pass):
        return "m1013_candidate_b_full_replay_gate_behavior_regression"
    return "m1013_candidate_b_full_replay_gate_pass"


def failure_types_for_m1019_result(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    if (
        result_class.endswith("_exact_retention_failed")
        or result_class.endswith("_m267_preflight_failed")
        or result_class.endswith("_public_replay_proof_washout")
        or result_class.endswith("_source_diverse_diagnostic_failed")
    ):
        return ["proof_washout"]
    return ["metric_artifact"]


def next_blocker_for_m1019_result(result_class: str) -> str:
    if result_class.endswith("_pass"):
        return "candidate_b_promotion_generalization_or_branch_synthesis_audit"
    if result_class.endswith("_exact_retention_failed"):
        return "candidate_b_exact_retention_failure_audit"
    if result_class.endswith("_m267_preflight_failed"):
        return "candidate_b_m267_preflight_failure_audit"
    if result_class.endswith("_public_replay_proof_washout"):
        return "candidate_b_public_replay_failure_audit"
    if result_class.endswith("_source_diverse_diagnostic_failed"):
        return "candidate_b_source_diverse_diagnostic_failure_audit"
    if result_class.endswith("_behavior_regression"):
        return "candidate_b_behavior_regression_audit"
    return "candidate_b_contract_artifact_audit"


def _candidate_csv(run_dir: Path, checkpoint: Path, alpha: float) -> Path:
    path = run_dir / "candidate_b_checkpoints.csv"
    write_csv_rows(path, [{"alpha": float(alpha), "checkpoint": str(checkpoint)}])
    return path


def run_m1013_candidate_b_full_replay_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    temporal_corpus: Path,
    temporal_metadata: Path | None,
    base_temporal_summary: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path,
    behavior_episodes: int,
    max_continuation_steps: int,
    candidate_alpha: float = 0.5,
    preference_margin: float = 0.05,
    lambda_pref: float = 1.0,
    lambda_anchor: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate_csv = _candidate_csv(run_dir, candidate_checkpoint, candidate_alpha)
    summary = run_temporal_sequence_public_replay_gate(
        base_checkpoint=base_checkpoint,
        candidate_checkpoints_csv=candidate_csv,
        interpolation_metrics_csv=None,
        corpus_path=temporal_corpus,
        base_summary_path=base_temporal_summary,
        run_dir=run_dir,
        device=device,
        env_config_path=env_config_path,
        behavior_episodes=behavior_episodes,
        max_continuation_steps=max_continuation_steps,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    inner_result_class = str(summary["result_class"])
    source_diverse_summary = summary.get("source_diverse_protected_summary", {})
    source_diverse_pass = bool(
        isinstance(source_diverse_summary, dict) and source_diverse_summary.get("overall_pass", False)
    )
    result_class = classify_m1019_gate(
        actor_inputs_changed=bool(summary.get("actor_inputs_changed", False)),
        exact_contract_pass_count=int(summary.get("exact_contract_pass_count", 0)),
        candidate_preflight_pass_count=int(summary.get("candidate_preflight_pass_count", 0)),
        six_public_replay_gates_pass=bool(summary.get("six_public_replay_gates_pass", False)),
        source_diverse_pass=source_diverse_pass,
        behavior_pass=bool(summary.get("behavior_pass", False)),
        training_started=bool(summary.get("training_started", False)),
        ppo_used=bool(summary.get("ppo_used", False)),
        promoted=bool(summary.get("promoted", False)),
    )
    summary.update(
        {
            "run_type": "m1013_candidate_b_full_replay_gate",
            "inner_run_type": "capability_step_temporal_sequence_public_replay_gate",
            "inner_result_class": inner_result_class,
            "result_class": result_class,
            "failure_types": failure_types_for_m1019_result(result_class),
            "next_blocker": next_blocker_for_m1019_result(result_class),
            "candidate_b_checkpoint": candidate_checkpoint,
            "candidate_b_alpha": float(candidate_alpha),
            "candidate_b_checkpoints_csv": candidate_csv,
            "temporal_metadata": temporal_metadata,
            "source_diverse_pass": bool(source_diverse_pass),
            "promotion_decision": "not_applicable",
            "checkpoint_promoted": False,
            "promoted": False,
            "ppo_used": False,
            "training_started": False,
            "private_holdout_used": False,
        }
    )
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M1013 Candidate B full public replay gate.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_B_CHECKPOINT)
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--temporal-metadata", type=Path, default=None)
    parser.add_argument("--base-temporal-summary", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--candidate-alpha", type=float, default=0.5)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_m1013_candidate_b_full_replay_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        temporal_corpus=args.temporal_corpus,
        temporal_metadata=args.temporal_metadata,
        base_temporal_summary=args.base_temporal_summary,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
        candidate_alpha=args.candidate_alpha,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(f"result_class={summary['result_class']}")
    print(f"inner_result_class={summary['inner_result_class']}")
    print(f"exact_contract_pass_count={summary['exact_contract_pass_count']}")
    print(f"candidate_preflight_pass_count={summary['candidate_preflight_pass_count']}")
    print(f"public_replay_gates_passed={summary['public_replay_gates_passed']}")
    print(f"source_diverse_pass={summary['source_diverse_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
