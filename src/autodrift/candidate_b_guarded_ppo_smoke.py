"""Smoke-scale guarded PPO proposal from the Candidate B public-gate base."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.m1013_candidate_b_promotion_generalization_gate import (
    DEFAULT_BEHAVIOR_SEEDS,
    DEFAULT_FRESH_SEEDS,
    DEFAULT_OOD_SEEDS,
    failure_types_for_candidate_b_result,
    run_candidate_b_promotion_generalization_gate,
)
from autodrift.m1013_candidate_b_full_replay_gate import DEFAULT_CANDIDATE_B_CHECKPOINT
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate import DEFAULT_OOD_ENV_CONFIG
from autodrift.public_base_post_promotion_guarded_ppo_smoke import (
    _actor_inputs_changed,
    _training_metrics_finite,
    run_ppo_proposal,
)


DEFAULT_CONFIG = Path("configs/ppo_m1026_candidate_b_guarded_smoke.json")
DEFAULT_RUN_DIR = Path("runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke")
DEFAULT_PPO_RUN_DIR = Path("runs/ppo_m1026_candidate_b_guarded_smoke_seed61026")
DEFAULT_TEMPORAL_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_BASE_TEMPORAL_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")


def classify_candidate_b_guarded_ppo(
    *,
    actor_inputs_changed: bool,
    ppo_returncode: int,
    training_metrics_finite: bool,
    exact_retention_pass: bool,
    proof_pass: bool,
    source_diverse_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    promoted: bool,
    private_holdout_used: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(promoted) or bool(private_holdout_used):
        return "candidate_b_guarded_ppo_contract_artifact"
    if int(ppo_returncode) != 0 or not bool(training_metrics_finite):
        return "candidate_b_guarded_ppo_training_instability"
    if not bool(exact_retention_pass):
        return "candidate_b_guarded_ppo_exact_retention_regression"
    if not bool(proof_pass) or not bool(source_diverse_pass):
        return "candidate_b_guarded_ppo_proof_washout"
    if not bool(generalization_pass):
        return "candidate_b_guarded_ppo_generalization_regression"
    if not bool(behavior_pass):
        return "candidate_b_guarded_ppo_behavior_regression"
    return "candidate_b_guarded_ppo_raw_candidate"


def failure_types_for_guarded_ppo_result(result_class: str) -> list[str]:
    if result_class.endswith("_raw_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_training_instability"):
        return ["training_instability"]
    if result_class.endswith("_exact_retention_regression") or result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    return ["metric_artifact"]


def next_blocker_for_guarded_ppo_result(result_class: str) -> str:
    if result_class.endswith("_raw_candidate"):
        return "candidate_b_guarded_ppo_raw_candidate_full_gate_design"
    if result_class.endswith("_training_instability"):
        return "candidate_b_guarded_ppo_recipe_audit"
    if result_class.endswith("_exact_retention_regression") or result_class.endswith("_proof_washout"):
        return "candidate_b_guarded_ppo_exact_repair_projection_design"
    if result_class.endswith("_generalization_regression"):
        return "candidate_b_guarded_ppo_generalization_regression_audit"
    if result_class.endswith("_behavior_regression"):
        return "candidate_b_guarded_ppo_behavior_regression_audit"
    return "candidate_b_guarded_ppo_contract_audit"


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _exact_retention_pass(path: Path) -> bool:
    if not path.exists():
        return False
    frame = pd.read_csv(path)
    if "exact_gate_pass" not in frame.columns:
        return False
    return bool(frame["exact_gate_pass"].astype(bool).any())


def training_metrics_path(ppo_run_dir: Path) -> Path:
    train_metrics = ppo_run_dir / "train_metrics.csv"
    if train_metrics.exists():
        return train_metrics
    return ppo_run_dir / "metrics.csv"


def _route_decision_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_class": str(summary["result_class"]),
        "ppo_returncode": int(summary["ppo_returncode"]),
        "training_metrics_finite": bool(summary["training_metrics_finite"]),
        "exact_retention_pass": bool(summary["exact_retention_pass"]),
        "proof_pass": bool(summary["proof_pass"]),
        "source_diverse_pass": bool(summary["source_diverse_pass"]),
        "generalization_pass": bool(summary["generalization_pass"]),
        "behavior_pass": bool(summary["behavior_pass"]),
        "actor_inputs_changed": bool(summary["actor_inputs_changed"]),
        "promoted": bool(summary["promoted"]),
        "next_blocker": str(summary["next_blocker"]),
    }


def run_candidate_b_guarded_ppo_smoke(
    *,
    base_checkpoint: Path,
    config_path: Path,
    run_dir: Path,
    ppo_run_dir: Path,
    device: str,
    temporal_corpus: Path,
    base_temporal_summary: Path,
    fresh_episodes: int,
    ood_episodes: int,
    behavior_episodes: int,
    max_continuation_steps: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    ppo_log = run_dir / "ppo_stdout.log"
    ppo_returncode = run_ppo_proposal(
        config_path=config_path,
        init_checkpoint=base_checkpoint,
        ppo_run_dir=ppo_run_dir,
        device=device,
        log_path=ppo_log,
    )
    raw_checkpoint = ppo_run_dir / "checkpoint.pt"
    raw_checkpoint_exists = raw_checkpoint.exists()
    train_metrics_csv = training_metrics_path(ppo_run_dir)
    eval_summary_json = ppo_run_dir / "eval_summary.json"
    training_metrics_finite = bool(
        raw_checkpoint_exists and _training_metrics_finite(train_metrics_csv, eval_summary_json)
    )
    gate_summary: dict[str, Any] = {"status": "not_run_no_raw_checkpoint"}
    actor_inputs_changed = False
    exact_retention_pass = False
    proof_pass = False
    source_diverse_pass = False
    generalization_pass = False
    behavior_pass = False
    if raw_checkpoint_exists:
        actor_inputs_changed = _actor_inputs_changed(base_checkpoint, raw_checkpoint)
        gate_summary = run_candidate_b_promotion_generalization_gate(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=raw_checkpoint,
            temporal_corpus=temporal_corpus,
            base_temporal_summary=base_temporal_summary,
            run_dir=run_dir / "raw_candidate_gate",
            device=device,
            fresh_env_config=DEFAULT_ENV_CONFIG,
            ood_env_config=DEFAULT_OOD_ENV_CONFIG,
            behavior_env_config=DEFAULT_ENV_CONFIG,
            fresh_seeds=DEFAULT_FRESH_SEEDS,
            ood_seeds=DEFAULT_OOD_SEEDS,
            behavior_seeds=DEFAULT_BEHAVIOR_SEEDS,
            fresh_episodes=fresh_episodes,
            ood_episodes=ood_episodes,
            behavior_episodes=behavior_episodes,
            max_continuation_steps=max_continuation_steps,
            candidate_alpha=1.0,
        )
        _copy_if_exists(Path(gate_summary["exact_contract_summary_csv"]), run_dir / "exact_retention_summary.csv")
        _copy_if_exists(Path(gate_summary["proof_replay_summary_csv"]), run_dir / "proof_replay_summary.csv")
        _copy_if_exists(Path(gate_summary["fresh_randomized_eval_summary_csv"]), run_dir / "fresh_randomized_eval_summary.csv")
        _copy_if_exists(Path(gate_summary["ood_eval_summary_csv"]), run_dir / "ood_eval_summary.csv")
        _copy_if_exists(Path(gate_summary["generalization_comparison_csv"]), run_dir / "generalization_comparison.csv")
        _copy_if_exists(Path(gate_summary["behavior_summary_csv"]), run_dir / "behavior_summary.csv")
        _copy_if_exists(Path(gate_summary["behavior_comparison_csv"]), run_dir / "behavior_comparison.csv")
        exact_retention_pass = _exact_retention_pass(run_dir / "exact_retention_summary.csv")
        proof_pass = bool(gate_summary.get("proof_pass", False))
        source_diverse_pass = bool(gate_summary.get("source_diverse_pass", False))
        generalization_pass = bool(gate_summary.get("generalization_pass", False))
        behavior_pass = bool(gate_summary.get("behavior_pass", False))
    result_class = classify_candidate_b_guarded_ppo(
        actor_inputs_changed=actor_inputs_changed,
        ppo_returncode=ppo_returncode,
        training_metrics_finite=training_metrics_finite,
        exact_retention_pass=exact_retention_pass,
        proof_pass=proof_pass,
        source_diverse_pass=source_diverse_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        promoted=False,
        private_holdout_used=False,
    )
    summary = {
        "run_type": "candidate_b_guarded_ppo_smoke",
        "base_checkpoint": base_checkpoint,
        "config_path": config_path,
        "ppo_run_dir": ppo_run_dir,
        "raw_checkpoint": raw_checkpoint,
        "ppo_returncode": int(ppo_returncode),
        "ppo_log": ppo_log,
        "raw_checkpoint_exists": bool(raw_checkpoint_exists),
        "training_metrics_finite": bool(training_metrics_finite),
        "train_metrics_csv": train_metrics_csv,
        "eval_summary_json": eval_summary_json,
        "gate_summary": gate_summary,
        "exact_retention_pass": bool(exact_retention_pass),
        "proof_pass": bool(proof_pass),
        "source_diverse_pass": bool(source_diverse_pass),
        "generalization_pass": bool(generalization_pass),
        "behavior_pass": bool(behavior_pass),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "training_started": bool(ppo_returncode == 0),
        "ppo_used": True,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_guarded_ppo_result(result_class),
        "next_blocker": next_blocker_for_guarded_ppo_result(result_class),
        "exact_retention_summary_csv": run_dir / "exact_retention_summary.csv",
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "fresh_randomized_eval_summary_csv": run_dir / "fresh_randomized_eval_summary.csv",
        "ood_eval_summary_csv": run_dir / "ood_eval_summary.csv",
        "behavior_summary_csv": run_dir / "behavior_summary.csv",
        "behavior_comparison_csv": run_dir / "behavior_comparison.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "summary_json": run_dir / "summary.json",
    }
    (run_dir / "ppo_run_dir.txt").write_text(str(ppo_run_dir) + "\n", encoding="utf-8")
    write_csv_rows(run_dir / "route_decision.csv", [_route_decision_row(summary)])
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run smoke-scale guarded PPO from Candidate B.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CANDIDATE_B_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--ppo-run-dir", type=Path, default=DEFAULT_PPO_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "config"], default="auto")
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_TEMPORAL_CORPUS)
    parser.add_argument("--base-temporal-summary", type=Path, default=DEFAULT_BASE_TEMPORAL_SUMMARY)
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_candidate_b_guarded_ppo_smoke(
        base_checkpoint=args.base_checkpoint,
        config_path=args.config,
        run_dir=args.run_dir,
        ppo_run_dir=args.ppo_run_dir,
        device=args.device,
        temporal_corpus=args.temporal_corpus,
        base_temporal_summary=args.base_temporal_summary,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"ppo_returncode={summary['ppo_returncode']}")
    print(f"exact_retention_pass={summary['exact_retention_pass']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"source_diverse_pass={summary['source_diverse_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
