"""Promotion/generalization gate for M1013 Candidate B."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.capability_step_temporal_sequence_public_replay_gate import (
    DEFAULT_BASE_SUMMARY,
    DEFAULT_CORPUS,
    TemporalSequenceCandidate,
    exact_contract_rows,
)
from autodrift.m1013_candidate_b_full_replay_gate import DEFAULT_CANDIDATE_B_CHECKPOINT
from autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate import (
    DEFAULT_OOD_ENV_CONFIG,
    DirectionTargetCandidate,
    _behavior_eval_specs,
    _fresh_eval_specs,
    _run_eval_specs,
    _run_old_key_diagnostic,
    _run_public_replay_gates,
    _run_source_diverse_diagnostic,
    compare_behavior_rows,
    compare_eval_rows,
)
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG


DEFAULT_BASE_CHECKPOINT = Path("runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt")
DEFAULT_RUN_DIR = Path("runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate")
DEFAULT_FRESH_SEEDS = (102100, 102101)
DEFAULT_OOD_SEEDS = (102120,)
DEFAULT_BEHAVIOR_SEEDS = (9505, 9506, 102130, 102131)


def classify_candidate_b_promotion_gate(
    *,
    actor_inputs_changed: bool,
    exact_contract_pass_count: int,
    proof_pass: bool,
    source_diverse_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "candidate_b_promotion_gate_contract_artifact"
    if int(exact_contract_pass_count) <= 0:
        return "candidate_b_promotion_gate_exact_retention_failed"
    if not bool(proof_pass) or not bool(source_diverse_pass):
        return "candidate_b_promotion_gate_proof_washout"
    if not bool(generalization_pass):
        return "candidate_b_promotion_gate_generalization_regression"
    if not bool(behavior_pass):
        return "candidate_b_promotion_gate_behavior_regression"
    return "candidate_b_promotion_gate_candidate"


def failure_types_for_candidate_b_result(result_class: str) -> list[str]:
    if result_class.endswith("_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_exact_retention_failed") or result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    return ["metric_artifact"]


def next_blocker_for_candidate_b_result(result_class: str) -> str:
    if result_class.endswith("_candidate"):
        return "candidate_b_promotion_audit"
    if result_class.endswith("_exact_retention_failed"):
        return "candidate_b_exact_retention_failure_audit"
    if result_class.endswith("_proof_washout"):
        return "candidate_b_proof_washout_audit"
    if result_class.endswith("_generalization_regression"):
        return "candidate_b_generalization_regression_audit"
    if result_class.endswith("_behavior_regression"):
        return "candidate_b_behavior_regression_audit"
    return "candidate_b_promotion_gate_contract_audit"


def _parse_seeds(text: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in str(text).split(",") if item.strip())


def run_candidate_b_promotion_generalization_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    temporal_corpus: Path,
    base_temporal_summary: Path,
    run_dir: Path,
    device: str,
    fresh_env_config: Path,
    ood_env_config: Path,
    behavior_env_config: Path,
    fresh_seeds: tuple[int, ...],
    ood_seeds: tuple[int, ...],
    behavior_seeds: tuple[int, ...],
    fresh_episodes: int,
    ood_episodes: int,
    behavior_episodes: int,
    max_continuation_steps: int,
    candidate_alpha: float = 0.5,
    preference_margin: float = 0.05,
    lambda_pref: float = 1.0,
    lambda_anchor: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    exact_rows = exact_contract_rows(
        base_checkpoint=base_checkpoint,
        candidates=[TemporalSequenceCandidate(alpha=float(candidate_alpha), checkpoint=candidate_checkpoint)],
        corpus_path=temporal_corpus,
        base_summary_path=base_temporal_summary,
        device=device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    exact_contract_pass_count = sum(1 for row in exact_rows if bool(row.get("exact_contract_gate_pass", False)))
    exact_actor_inputs_changed = any(bool(row.get("actor_inputs_changed", False)) for row in exact_rows)
    candidate = DirectionTargetCandidate(alpha=float(candidate_alpha), checkpoint=candidate_checkpoint)
    proof_rows = _run_public_replay_gates(
        base_checkpoint=base_checkpoint,
        candidate=candidate,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    proof_pass = all(bool(row["gate_pass"]) for row in proof_rows)
    source_diverse_summary = _run_source_diverse_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate=candidate,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    source_diverse_pass = bool(source_diverse_summary.get("overall_pass", False))
    old_key_summary = _run_old_key_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate=candidate,
        device=device,
        run_dir=run_dir,
    )
    eval_rows = _run_eval_specs(
        specs=_fresh_eval_specs(
            base_checkpoint=base_checkpoint,
            candidate=candidate,
            fresh_env_config=fresh_env_config,
            ood_env_config=ood_env_config,
            fresh_seeds=fresh_seeds,
            ood_seeds=ood_seeds,
            fresh_episodes=fresh_episodes,
            ood_episodes=ood_episodes,
        ),
        device=device,
        run_dir=run_dir / "evals",
    )
    generalization_comparisons = compare_eval_rows(eval_rows, candidate_label=candidate.label)
    generalization_pass = all(bool(row["generalization_pass"]) for row in generalization_comparisons)
    fresh_rows = [row for row in eval_rows if row["distribution"] == "fresh_public"]
    ood_rows = [row for row in eval_rows if row["distribution"] == "moderate_ood"]
    behavior_rows = _run_eval_specs(
        specs=_behavior_eval_specs(
            base_checkpoint=base_checkpoint,
            candidate=candidate,
            env_config_path=behavior_env_config,
            seeds=behavior_seeds,
            episodes=behavior_episodes,
        ),
        device=device,
        run_dir=run_dir / "behavior_evals",
    )
    behavior_comparisons = compare_behavior_rows(behavior_rows, candidate_label=candidate.label)
    behavior_pass = all(bool(row["behavior_pass"]) for row in behavior_comparisons)
    actor_inputs_changed = bool(exact_actor_inputs_changed)
    result_class = classify_candidate_b_promotion_gate(
        actor_inputs_changed=actor_inputs_changed,
        exact_contract_pass_count=exact_contract_pass_count,
        proof_pass=proof_pass,
        source_diverse_pass=source_diverse_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "m1013_candidate_b_promotion_generalization_gate",
        "baseline_checkpoint": base_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
        "candidate_label": candidate.label,
        "candidate_alpha": float(candidate_alpha),
        "temporal_corpus": temporal_corpus,
        "base_temporal_summary": base_temporal_summary,
        "fresh_env_config": fresh_env_config,
        "ood_env_config": ood_env_config,
        "behavior_env_config": behavior_env_config,
        "fresh_seeds": list(fresh_seeds),
        "ood_seeds": list(ood_seeds),
        "behavior_seeds": list(behavior_seeds),
        "fresh_episodes": int(fresh_episodes),
        "ood_episodes": int(ood_episodes),
        "behavior_episodes": int(behavior_episodes),
        "max_continuation_steps": int(max_continuation_steps),
        "exact_contract_pass_count": int(exact_contract_pass_count),
        "proof_replay_surface_count": int(len(proof_rows)),
        "proof_replay_gates_passed": int(sum(1 for row in proof_rows if bool(row.get("gate_pass", False)))),
        "proof_pass": bool(proof_pass),
        "failed_proof_surfaces": [row["surface"] for row in proof_rows if not bool(row["gate_pass"])],
        "source_diverse_pass": bool(source_diverse_pass),
        "source_diverse_protected_status": "pass" if source_diverse_pass else "diagnostic_failed",
        "source_diverse_protected_summary": source_diverse_summary,
        "old_key_9944_status": "diagnostic_only",
        "old_key_neighborhood_summary": old_key_summary,
        "fresh_generalization_comparison_count": int(
            sum(1 for row in generalization_comparisons if row["distribution"] == "fresh_public")
        ),
        "ood_generalization_comparison_count": int(
            sum(1 for row in generalization_comparisons if row["distribution"] == "moderate_ood")
        ),
        "generalization_pass": bool(generalization_pass),
        "failed_generalization_rows": [
            f"{row['distribution']}:{row['seed']}"
            for row in generalization_comparisons
            if not bool(row["generalization_pass"])
        ],
        "behavior_seed_count": int(len(behavior_seeds)),
        "behavior_pass": bool(behavior_pass),
        "failed_behavior_seeds": [int(row["seed"]) for row in behavior_comparisons if not bool(row["behavior_pass"])],
        "reset_zero_all_ordering_retained": bool(
            behavior_comparisons
            and all(bool(row["reset_zero_all_ordering_retained"]) for row in behavior_comparisons)
        ),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_candidate_b_result(result_class),
        "next_blocker": next_blocker_for_candidate_b_result(result_class),
        "exact_contract_summary_csv": run_dir / "exact_contract_summary.csv",
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "fresh_randomized_eval_summary_csv": run_dir / "fresh_randomized_eval_summary.csv",
        "ood_eval_summary_csv": run_dir / "ood_eval_summary.csv",
        "generalization_comparison_csv": run_dir / "generalization_comparison.csv",
        "behavior_summary_csv": run_dir / "behavior_summary.csv",
        "behavior_comparison_csv": run_dir / "behavior_comparison.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_csv_rows(run_dir / "exact_contract_summary.csv", exact_rows)
    write_csv_rows(run_dir / "proof_replay_summary.csv", proof_rows)
    write_csv_rows(run_dir / "fresh_randomized_eval_summary.csv", fresh_rows)
    write_csv_rows(run_dir / "ood_eval_summary.csv", ood_rows)
    write_csv_rows(run_dir / "generalization_comparison.csv", generalization_comparisons)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    write_csv_rows(run_dir / "route_decision.csv", [_route_decision_row(summary)])
    write_json(run_dir / "summary.json", summary)
    return summary


def _route_decision_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_class": str(summary["result_class"]),
        "exact_contract_pass_count": int(summary["exact_contract_pass_count"]),
        "proof_pass": bool(summary["proof_pass"]),
        "source_diverse_pass": bool(summary["source_diverse_pass"]),
        "generalization_pass": bool(summary["generalization_pass"]),
        "behavior_pass": bool(summary["behavior_pass"]),
        "actor_inputs_changed": bool(summary["actor_inputs_changed"]),
        "training_started": bool(summary["training_started"]),
        "ppo_used": bool(summary["ppo_used"]),
        "promoted": bool(summary["promoted"]),
        "next_blocker": str(summary["next_blocker"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Candidate B promotion/generalization gate.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_B_CHECKPOINT)
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--base-temporal-summary", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--fresh-env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--ood-env-config", type=Path, default=DEFAULT_OOD_ENV_CONFIG)
    parser.add_argument("--behavior-env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--fresh-seeds", type=_parse_seeds, default=DEFAULT_FRESH_SEEDS)
    parser.add_argument("--ood-seeds", type=_parse_seeds, default=DEFAULT_OOD_SEEDS)
    parser.add_argument("--behavior-seeds", type=_parse_seeds, default=DEFAULT_BEHAVIOR_SEEDS)
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--candidate-alpha", type=float, default=0.5)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_candidate_b_promotion_generalization_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        temporal_corpus=args.temporal_corpus,
        base_temporal_summary=args.base_temporal_summary,
        run_dir=args.run_dir,
        device=args.device,
        fresh_env_config=args.fresh_env_config,
        ood_env_config=args.ood_env_config,
        behavior_env_config=args.behavior_env_config,
        fresh_seeds=args.fresh_seeds,
        ood_seeds=args.ood_seeds,
        behavior_seeds=args.behavior_seeds,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
        candidate_alpha=args.candidate_alpha,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(f"result_class={summary['result_class']}")
    print(f"exact_contract_pass_count={summary['exact_contract_pass_count']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"source_diverse_pass={summary['source_diverse_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
