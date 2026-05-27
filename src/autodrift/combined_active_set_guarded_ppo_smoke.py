"""Smoke-scale guarded PPO proposal from the combined active-set public base."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.candidate_b_combined_active_set_full_public_gate import (
    DEFAULT_BEHAVIOR_SEEDS,
    DEFAULT_COMBINED_ANCHOR_NPZ,
    DEFAULT_FRESH_SEEDS,
    DEFAULT_M270_NPZ,
    DEFAULT_M297_NPZ,
    DEFAULT_OOD_SEEDS,
    DEFAULT_TEMPORAL_BASE_SUMMARY,
    DEFAULT_TEMPORAL_CORPUS,
    run_combined_active_set_full_public_gate,
)
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate import DEFAULT_OOD_ENV_CONFIG
from autodrift.public_base_post_promotion_guarded_ppo_smoke import (
    _actor_inputs_changed,
    _training_metrics_finite,
    run_ppo_proposal,
)


DEFAULT_BASE_CHECKPOINT = Path(
    "runs/m1038_candidate_b_combined_active_set_repair_projection_probe/"
    "temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt"
)
DEFAULT_CONFIG = Path("configs/ppo_m1044_combined_active_set_guarded_smoke.json")
DEFAULT_RUN_DIR = Path("runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke")
DEFAULT_PPO_RUN_DIR = Path("runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044")
PPO_ALLOWED_CHANGED_PREFIXES = (
    "actor_mean.",
    "context_encoder.",
    "critic.",
    "online_gru_cell.",
    "response_context_fusion.0.",
    "response_encoder.",
    "response_prediction_head.",
)


def classify_combined_active_set_guarded_ppo(
    *,
    actor_inputs_changed: bool,
    ppo_returncode: int,
    training_metrics_finite: bool,
    exact_pass: bool,
    proof_pass: bool,
    family_intersection_pass: bool = True,
    source_diverse_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    promoted: bool,
    private_holdout_used: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(promoted) or bool(private_holdout_used):
        return "combined_active_set_guarded_ppo_contract_artifact"
    if int(ppo_returncode) != 0 or not bool(training_metrics_finite):
        return "combined_active_set_guarded_ppo_training_instability"
    if not bool(exact_pass):
        return "combined_active_set_guarded_ppo_exact_retention_regression"
    if not bool(proof_pass) or not bool(family_intersection_pass):
        return "combined_active_set_guarded_ppo_public_replay_washout"
    if not bool(source_diverse_pass):
        return "combined_active_set_guarded_ppo_source_diagnostic_failed"
    if not bool(generalization_pass):
        return "combined_active_set_guarded_ppo_generalization_regression"
    if not bool(behavior_pass):
        return "combined_active_set_guarded_ppo_behavior_regression"
    return "combined_active_set_guarded_ppo_raw_candidate"


def failure_types_for_combined_active_set_guarded_ppo(result_class: str) -> list[str]:
    if result_class.endswith("_raw_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_training_instability"):
        return ["training_instability"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    if (
        result_class.endswith("_exact_retention_regression")
        or result_class.endswith("_public_replay_washout")
        or result_class.endswith("_source_diagnostic_failed")
    ):
        return ["proof_washout"]
    return ["metric_artifact"]


def next_blocker_for_combined_active_set_guarded_ppo(result_class: str) -> str:
    if result_class.endswith("_raw_candidate"):
        return "combined_active_set_guarded_ppo_promotion_audit"
    if result_class.endswith("_training_instability"):
        return "combined_active_set_guarded_ppo_recipe_audit"
    if result_class.endswith("_exact_retention_regression") or result_class.endswith("_public_replay_washout"):
        return "combined_active_set_guarded_ppo_exact_repair_projection_design"
    if result_class.endswith("_source_diagnostic_failed"):
        return "combined_active_set_guarded_ppo_source_diagnostic_failure_audit"
    if result_class.endswith("_generalization_regression"):
        return "combined_active_set_guarded_ppo_generalization_regression_audit"
    if result_class.endswith("_behavior_regression"):
        return "combined_active_set_guarded_ppo_behavior_regression_audit"
    return "combined_active_set_guarded_ppo_contract_audit"


def training_metrics_path(ppo_run_dir: Path) -> Path:
    train_metrics = ppo_run_dir / "train_metrics.csv"
    if train_metrics.exists():
        return train_metrics
    return ppo_run_dir / "metrics.csv"


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def _route_decision_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_class": str(summary["result_class"]),
        "ppo_returncode": int(summary["ppo_returncode"]),
        "training_metrics_finite": bool(summary["training_metrics_finite"]),
        "exact_pass": bool(summary["exact_pass"]),
        "proof_pass": bool(summary["proof_pass"]),
        "family_intersection_pass": bool(summary["family_intersection_pass"]),
        "source_diverse_pass": bool(summary["source_diverse_pass"]),
        "generalization_pass": bool(summary["generalization_pass"]),
        "behavior_pass": bool(summary["behavior_pass"]),
        "actor_inputs_changed": bool(summary["actor_inputs_changed"]),
        "promoted": bool(summary["promoted"]),
        "next_blocker": str(summary["next_blocker"]),
    }


def run_combined_active_set_guarded_ppo_smoke(
    *,
    base_checkpoint: Path,
    config_path: Path,
    run_dir: Path,
    ppo_run_dir: Path,
    device: str,
    temporal_corpus: Path,
    temporal_base_summary: Path,
    preference_npz: Path,
    outcome_npz: Path,
    combined_anchor_npz: Path,
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
    exact_pass = False
    proof_pass = False
    public_replay_pass = False
    family_intersection_pass = False
    source_diverse_pass = False
    generalization_pass = False
    behavior_pass = False
    if raw_checkpoint_exists:
        actor_inputs_changed = _actor_inputs_changed(base_checkpoint, raw_checkpoint)
        gate_summary = run_combined_active_set_full_public_gate(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=raw_checkpoint,
            temporal_corpus=temporal_corpus,
            temporal_base_summary=temporal_base_summary,
            preference_npz=preference_npz,
            outcome_npz=outcome_npz,
            combined_anchor_npz=combined_anchor_npz,
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
            preference_margin=0.05,
            lambda_pref=1.0,
            lambda_anchor=0.25,
            allowed_changed_prefixes=PPO_ALLOWED_CHANGED_PREFIXES,
        )
        _copy_if_exists(Path(gate_summary["exact_contract_summary_csv"]), run_dir / "exact_contract_summary.csv")
        _copy_if_exists(Path(gate_summary["proof_replay_summary_csv"]), run_dir / "proof_replay_summary.csv")
        _copy_if_exists(Path(gate_summary["family_intersection_summary_json"]), run_dir / "family_intersection_summary.json")
        _copy_if_exists(Path(gate_summary["source_diverse_summary_json"]), run_dir / "source_diverse_summary.json")
        _copy_if_exists(Path(gate_summary["fresh_randomized_eval_summary_csv"]), run_dir / "fresh_randomized_eval_summary.csv")
        _copy_if_exists(Path(gate_summary["ood_eval_summary_csv"]), run_dir / "ood_eval_summary.csv")
        _copy_if_exists(Path(gate_summary["generalization_comparison_csv"]), run_dir / "generalization_comparison.csv")
        _copy_if_exists(Path(gate_summary["behavior_summary_csv"]), run_dir / "behavior_summary.csv")
        _copy_if_exists(Path(gate_summary["behavior_comparison_csv"]), run_dir / "behavior_comparison.csv")
        exact_pass = bool(gate_summary.get("exact_pass", False))
        public_replay_pass = bool(gate_summary.get("proof_pass", False))
        family_intersection_pass = bool(gate_summary.get("family_intersection_pass", False))
        proof_pass = bool(public_replay_pass and family_intersection_pass)
        source_diverse_pass = bool(gate_summary.get("source_diverse_pass", False))
        generalization_pass = bool(gate_summary.get("generalization_pass", False))
        behavior_pass = bool(gate_summary.get("behavior_pass", False))

    result_class = classify_combined_active_set_guarded_ppo(
        actor_inputs_changed=actor_inputs_changed,
        ppo_returncode=ppo_returncode,
        training_metrics_finite=training_metrics_finite,
        exact_pass=exact_pass,
        proof_pass=proof_pass,
        family_intersection_pass=family_intersection_pass,
        source_diverse_pass=source_diverse_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        promoted=False,
        private_holdout_used=False,
    )
    summary = {
        "run_type": "combined_active_set_guarded_ppo_smoke",
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
        "exact_pass": bool(exact_pass),
        "proof_pass": bool(proof_pass),
        "public_replay_pass": bool(public_replay_pass),
        "family_intersection_pass": bool(family_intersection_pass),
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
        "failure_types": failure_types_for_combined_active_set_guarded_ppo(result_class),
        "next_blocker": next_blocker_for_combined_active_set_guarded_ppo(result_class),
        "exact_contract_summary_csv": run_dir / "exact_contract_summary.csv",
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "family_intersection_summary_json": run_dir / "family_intersection_summary.json",
        "source_diverse_summary_json": run_dir / "source_diverse_summary.json",
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
    parser = argparse.ArgumentParser(description="Run guarded PPO from the combined active-set public base.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--ppo-run-dir", type=Path, default=DEFAULT_PPO_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "config"], default="auto")
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_TEMPORAL_CORPUS)
    parser.add_argument("--temporal-base-summary", type=Path, default=DEFAULT_TEMPORAL_BASE_SUMMARY)
    parser.add_argument("--preference-npz", type=Path, default=DEFAULT_M297_NPZ)
    parser.add_argument("--outcome-npz", type=Path, default=DEFAULT_M270_NPZ)
    parser.add_argument("--combined-anchor-npz", type=Path, default=DEFAULT_COMBINED_ANCHOR_NPZ)
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_combined_active_set_guarded_ppo_smoke(
        base_checkpoint=args.base_checkpoint,
        config_path=args.config,
        run_dir=args.run_dir,
        ppo_run_dir=args.ppo_run_dir,
        device=args.device,
        temporal_corpus=args.temporal_corpus,
        temporal_base_summary=args.temporal_base_summary,
        preference_npz=args.preference_npz,
        outcome_npz=args.outcome_npz,
        combined_anchor_npz=args.combined_anchor_npz,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"ppo_returncode={summary['ppo_returncode']}")
    print(f"exact_pass={summary['exact_pass']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"family_intersection_pass={summary['family_intersection_pass']}")
    print(f"source_diverse_pass={summary['source_diverse_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
