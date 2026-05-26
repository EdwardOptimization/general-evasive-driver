"""Smoke PPO proposal plus gates from the promoted alpha_1_0 public base."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import evaluate_policy, load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate import (
    DEFAULT_BEHAVIOR_SEEDS,
    DEFAULT_FRESH_SEEDS,
    DEFAULT_OOD_ENV_CONFIG,
    DEFAULT_OOD_SEEDS,
    MARGIN_TOLERANCE,
    SUCCESS_TOLERANCE,
    TERMINATION_TOLERANCE,
)
from autodrift.public_base_direction_target_actor_fit_replay_gate import (
    DEFAULT_ENV_CONFIG,
    DEFAULT_PUBLIC_REPLAY_SURFACES,
)


DEFAULT_BASE_CHECKPOINT = Path("runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt")
DEFAULT_PPO_CONFIG = Path("configs/ppo_m972_post_promotion_guarded_smoke.json")
DEFAULT_RUN_DIR = Path("runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke")
DEFAULT_PPO_RUN_DIR = Path("runs/ppo_m972_post_promotion_guarded_smoke_seed5972")
BASE_LABEL = "alpha1_base"
CANDIDATE_LABEL = "m972_raw_ppo"


def _config_signature(checkpoint_path: Path) -> dict[str, Any]:
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


def _actor_inputs_changed(base_checkpoint: Path, candidate_checkpoint: Path) -> bool:
    return _config_signature(base_checkpoint) != _config_signature(candidate_checkpoint)


def classify_post_promotion_guarded_ppo(
    *,
    actor_inputs_changed: bool,
    ppo_returncode: int,
    training_metrics_finite: bool,
    proof_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    promoted: bool,
    private_holdout_used: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(promoted) or bool(private_holdout_used):
        return "post_promotion_guarded_ppo_contract_artifact"
    if int(ppo_returncode) != 0 or not bool(training_metrics_finite):
        return "post_promotion_guarded_ppo_training_instability"
    if not bool(proof_pass):
        return "post_promotion_guarded_ppo_proof_washout"
    if not bool(generalization_pass):
        return "post_promotion_guarded_ppo_generalization_regression"
    if not bool(behavior_pass):
        return "post_promotion_guarded_ppo_behavior_regression"
    return "post_promotion_guarded_ppo_raw_candidate"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_raw_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_training_instability"):
        return ["training_instability"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    return ["metric_artifact"]


def run_ppo_proposal(
    *,
    config_path: Path,
    init_checkpoint: Path,
    ppo_run_dir: Path,
    device: str,
    log_path: Path,
) -> int:
    command = [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(config_path),
        "--init-checkpoint",
        str(init_checkpoint),
        "--run-dir",
        str(ppo_run_dir),
    ]
    if device != "config":
        command.extend(["--device", device])
    env = os.environ.copy()
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env["PYTHONPATH"] = str(Path("src"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(" ".join(command) + "\n\n")
        handle.flush()
        result = subprocess.run(
            command,
            stdout=handle,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )
    return int(result.returncode)


def _training_metrics_finite(metrics_csv: Path, eval_summary_json: Path) -> bool:
    if not metrics_csv.exists() or not eval_summary_json.exists():
        return False
    frame = pd.read_csv(metrics_csv)
    numeric = frame.select_dtypes(include=["number"])
    if not numeric.empty:
        for value in numeric.to_numpy().reshape(-1):
            if not math.isfinite(float(value)):
                return False
    try:
        import json

        summary = json.loads(eval_summary_json.read_text(encoding="utf-8"))
    except Exception:
        return False
    for value in summary.values():
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            return False
    return True


def _run_proof_replay_gates(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate_checkpoint)
    checkpoints = (
        CheckpointSpec(label=BASE_LABEL, path=base_checkpoint),
        CheckpointSpec(label=CANDIDATE_LABEL, path=candidate_checkpoint),
    )
    for surface, corpus_csv in DEFAULT_PUBLIC_REPLAY_SURFACES:
        gate_dir = run_dir / "proof_gates" / f"{surface}_replay"
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=checkpoints,
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_LABEL,
            candidate_policy=CANDIDATE_LABEL,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        rows.append(
            {
                "surface": surface,
                "run_dir": str(gate_dir),
                "corpus_csv": str(corpus_csv),
                "rows": int(summary["rows"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "actor_inputs_changed": bool(actor_inputs_changed),
                "gate_pass": bool(summary["gate_pass"]) and not bool(actor_inputs_changed),
            }
        )
    return rows


def _episode_rates(episode_rows: list[dict[str, Any]]) -> dict[str, float]:
    frame = pd.DataFrame(episode_rows)
    if frame.empty:
        return {"collision_rate": 0.0, "obstacle_completed_rate": 0.0, "truncated_rate": 0.0}
    return {
        "collision_rate": float(frame["collision"].astype(bool).mean()) if "collision" in frame else 0.0,
        "obstacle_completed_rate": (
            float(frame["obstacle_completed"].astype(bool).mean()) if "obstacle_completed" in frame else 0.0
        ),
        "truncated_rate": float(frame["truncated"].astype(bool).mean()) if "truncated" in frame else 0.0,
    }


def _evaluate_checkpoint(
    *,
    distribution: str,
    env_config_path: Path,
    seed: int,
    episodes: int,
    policy_label: str,
    checkpoint: Path,
    ablation: str,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    env_config = load_env_config(env_config_path)
    eval_dir = run_dir / distribution / f"seed{seed}_{policy_label}_{ablation}"
    eval_dir.mkdir(parents=True, exist_ok=True)
    episode_rows, summary = evaluate_policy(
        policy_name="checkpoint",
        episodes=int(episodes),
        seed=int(seed),
        checkpoint=checkpoint,
        device=device,
        env_config=env_config,
        checkpoint_ablation=ablation,
    )
    pd.DataFrame(episode_rows).to_csv(eval_dir / "episodes.csv", index=False)
    write_json(eval_dir / "summary.json", summary)
    rates = _episode_rates(episode_rows)
    return {
        "distribution": distribution,
        "env_config": str(env_config_path),
        "seed": int(seed),
        "policy_label": policy_label,
        "checkpoint": str(checkpoint),
        "ablation": ablation,
        "run_dir": str(eval_dir),
        "episodes": int(summary["episodes"]),
        "success_rate": 1.0 - float(summary["termination_rate"]),
        "termination_rate": float(summary["termination_rate"]),
        "min_clearance_margin_mean": float(summary["min_clearance_margin_mean"]),
        "min_clearance_margin_min": float(summary["min_clearance_margin_min"]),
        "return_mean": float(summary["return_mean"]),
        **rates,
    }


def _run_generalization_evals(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    device: str,
    run_dir: Path,
    fresh_episodes: int,
    ood_episodes: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in DEFAULT_FRESH_SEEDS:
        for label, checkpoint in ((BASE_LABEL, base_checkpoint), (CANDIDATE_LABEL, candidate_checkpoint)):
            rows.append(
                _evaluate_checkpoint(
                    distribution="fresh_public",
                    env_config_path=DEFAULT_ENV_CONFIG,
                    seed=int(seed),
                    episodes=fresh_episodes,
                    policy_label=label,
                    checkpoint=checkpoint,
                    ablation="none",
                    device=device,
                    run_dir=run_dir,
                )
            )
    for seed in DEFAULT_OOD_SEEDS:
        for label, checkpoint in ((BASE_LABEL, base_checkpoint), (CANDIDATE_LABEL, candidate_checkpoint)):
            rows.append(
                _evaluate_checkpoint(
                    distribution="moderate_ood",
                    env_config_path=DEFAULT_OOD_ENV_CONFIG,
                    seed=int(seed),
                    episodes=ood_episodes,
                    policy_label=label,
                    checkpoint=checkpoint,
                    ablation="none",
                    device=device,
                    run_dir=run_dir,
                )
            )
    return rows


def _compare_generalization(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for (distribution, seed), group in frame.groupby(["distribution", "seed"], observed=True):
        base = group[group["policy_label"].eq(BASE_LABEL)].iloc[0]
        candidate = group[group["policy_label"].eq(CANDIDATE_LABEL)].iloc[0]
        success_delta = float(candidate["success_rate"]) - float(base["success_rate"])
        termination_delta = float(candidate["termination_rate"]) - float(base["termination_rate"])
        margin_delta = float(candidate["min_clearance_margin_mean"]) - float(base["min_clearance_margin_mean"])
        collision_delta = float(candidate["collision_rate"]) - float(base["collision_rate"])
        pass_row = bool(
            success_delta >= -SUCCESS_TOLERANCE
            and termination_delta <= TERMINATION_TOLERANCE
            and margin_delta >= -MARGIN_TOLERANCE
            and collision_delta <= TERMINATION_TOLERANCE
        )
        comparisons.append(
            {
                "distribution": str(distribution),
                "seed": int(seed),
                "base_success_rate": float(base["success_rate"]),
                "candidate_success_rate": float(candidate["success_rate"]),
                "success_delta": success_delta,
                "base_termination_rate": float(base["termination_rate"]),
                "candidate_termination_rate": float(candidate["termination_rate"]),
                "termination_delta": termination_delta,
                "base_margin_mean": float(base["min_clearance_margin_mean"]),
                "candidate_margin_mean": float(candidate["min_clearance_margin_mean"]),
                "margin_mean_delta": margin_delta,
                "base_collision_rate": float(base["collision_rate"]),
                "candidate_collision_rate": float(candidate["collision_rate"]),
                "collision_rate_delta": collision_delta,
                "generalization_pass": pass_row,
            }
        )
    return comparisons


def _run_behavior_evals(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    device: str,
    run_dir: Path,
    episodes: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in DEFAULT_BEHAVIOR_SEEDS:
        for label, checkpoint, ablation in (
            (BASE_LABEL, base_checkpoint, "none"),
            (CANDIDATE_LABEL, candidate_checkpoint, "none"),
            (CANDIDATE_LABEL, candidate_checkpoint, "reset_recurrent_state"),
            (CANDIDATE_LABEL, candidate_checkpoint, "zero_all_response"),
        ):
            rows.append(
                _evaluate_checkpoint(
                    distribution="behavior",
                    env_config_path=DEFAULT_ENV_CONFIG,
                    seed=int(seed),
                    episodes=episodes,
                    policy_label=label,
                    checkpoint=checkpoint,
                    ablation=ablation,
                    device=device,
                    run_dir=run_dir,
                )
            )
    return rows


def _compare_behavior(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for seed, group in frame.groupby("seed", observed=True):
        base = group[group["policy_label"].eq(BASE_LABEL) & group["ablation"].eq("none")].iloc[0]
        normal = group[group["policy_label"].eq(CANDIDATE_LABEL) & group["ablation"].eq("none")].iloc[0]
        reset = group[group["policy_label"].eq(CANDIDATE_LABEL) & group["ablation"].eq("reset_recurrent_state")].iloc[0]
        zero_all = group[group["policy_label"].eq(CANDIDATE_LABEL) & group["ablation"].eq("zero_all_response")].iloc[0]
        success_delta = float(normal["success_rate"]) - float(base["success_rate"])
        termination_delta = float(normal["termination_rate"]) - float(base["termination_rate"])
        ordering = (
            float(normal["success_rate"]) >= float(reset["success_rate"])
            and float(reset["success_rate"]) >= float(zero_all["success_rate"])
        )
        pass_row = bool(success_delta >= -SUCCESS_TOLERANCE and termination_delta <= TERMINATION_TOLERANCE and ordering)
        comparisons.append(
            {
                "seed": int(seed),
                "base_success_rate": float(base["success_rate"]),
                "candidate_success_rate": float(normal["success_rate"]),
                "reset_success_rate": float(reset["success_rate"]),
                "zero_all_success_rate": float(zero_all["success_rate"]),
                "candidate_success_delta": success_delta,
                "candidate_termination_delta": termination_delta,
                "reset_zero_all_ordering_retained": ordering,
                "behavior_pass": pass_row,
            }
        )
    return comparisons


def _route_decision_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "result_class": str(summary["result_class"]),
            "ppo_returncode": int(summary["ppo_returncode"]),
            "training_metrics_finite": bool(summary["training_metrics_finite"]),
            "proof_pass": bool(summary["proof_pass"]),
            "generalization_pass": bool(summary["generalization_pass"]),
            "behavior_pass": bool(summary["behavior_pass"]),
            "actor_inputs_changed": bool(summary["actor_inputs_changed"]),
            "promoted": bool(summary["promoted"]),
            "next_blocker": str(summary["next_blocker"]),
        }
    ]


def run_post_promotion_guarded_ppo_smoke(
    *,
    base_checkpoint: Path,
    config_path: Path,
    run_dir: Path,
    ppo_run_dir: Path,
    device: str,
    fresh_episodes: int = 256,
    ood_episodes: int = 128,
    behavior_episodes: int = 80,
    max_continuation_steps: int = 60,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    ppo_log = run_dir / "ppo_train.log"
    ppo_returncode = run_ppo_proposal(
        config_path=config_path,
        init_checkpoint=base_checkpoint,
        ppo_run_dir=ppo_run_dir,
        device=device,
        log_path=ppo_log,
    )
    (run_dir / "ppo_run_dir.txt").write_text(str(ppo_run_dir) + "\n", encoding="utf-8")
    raw_checkpoint = ppo_run_dir / "checkpoint.pt"
    train_metrics_csv = ppo_run_dir / "train_metrics.csv"
    eval_summary_json = ppo_run_dir / "eval_summary.json"
    training_metrics_finite = _training_metrics_finite(train_metrics_csv, eval_summary_json)
    raw_checkpoint_exists = raw_checkpoint.exists()
    actor_inputs_changed = bool(raw_checkpoint_exists and _actor_inputs_changed(base_checkpoint, raw_checkpoint))
    proof_rows: list[dict[str, Any]] = []
    generalization_rows: list[dict[str, Any]] = []
    generalization_comparisons: list[dict[str, Any]] = []
    behavior_rows: list[dict[str, Any]] = []
    behavior_comparisons: list[dict[str, Any]] = []
    proof_pass = False
    generalization_pass = False
    behavior_pass = False
    if int(ppo_returncode) == 0 and raw_checkpoint_exists and training_metrics_finite and not actor_inputs_changed:
        proof_rows = _run_proof_replay_gates(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=raw_checkpoint,
            env_config_path=DEFAULT_ENV_CONFIG,
            device=device,
            run_dir=run_dir,
            max_continuation_steps=max_continuation_steps,
        )
        proof_pass = all(bool(row["gate_pass"]) for row in proof_rows)
        generalization_rows = _run_generalization_evals(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=raw_checkpoint,
            device=device,
            run_dir=run_dir / "evals",
            fresh_episodes=fresh_episodes,
            ood_episodes=ood_episodes,
        )
        generalization_comparisons = _compare_generalization(generalization_rows)
        generalization_pass = all(bool(row["generalization_pass"]) for row in generalization_comparisons)
        behavior_rows = _run_behavior_evals(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=raw_checkpoint,
            device=device,
            run_dir=run_dir / "behavior_evals",
            episodes=behavior_episodes,
        )
        behavior_comparisons = _compare_behavior(behavior_rows)
        behavior_pass = all(bool(row["behavior_pass"]) for row in behavior_comparisons)
    result_class = classify_post_promotion_guarded_ppo(
        actor_inputs_changed=actor_inputs_changed,
        ppo_returncode=ppo_returncode,
        training_metrics_finite=training_metrics_finite,
        proof_pass=proof_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        promoted=False,
        private_holdout_used=False,
    )
    if result_class.endswith("_raw_candidate"):
        next_blocker = "post-promotion guarded PPO full public gate design"
    elif result_class.endswith("_training_instability"):
        next_blocker = "post-promotion guarded PPO recipe audit"
    elif result_class.endswith("_proof_washout"):
        next_blocker = "post-promotion guarded PPO exact repair/projection design"
    elif result_class.endswith("_generalization_regression"):
        next_blocker = "post-promotion guarded PPO generalization regression audit"
    elif result_class.endswith("_behavior_regression"):
        next_blocker = "post-promotion guarded PPO behavior regression audit"
    else:
        next_blocker = "post-promotion guarded PPO contract audit"
    fresh_rows = [row for row in generalization_rows if row["distribution"] == "fresh_public"]
    ood_rows = [row for row in generalization_rows if row["distribution"] == "moderate_ood"]
    summary = {
        "run_type": "public_base_post_promotion_guarded_ppo_smoke",
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
        "proof_replay_gates_passed": int(sum(1 for row in proof_rows if bool(row.get("gate_pass", False)))),
        "proof_replay_surface_count": int(len(proof_rows)),
        "proof_pass": bool(proof_pass),
        "failed_proof_surfaces": [row["surface"] for row in proof_rows if not bool(row["gate_pass"])],
        "generalization_pass": bool(generalization_pass),
        "failed_generalization_rows": [
            f"{row['distribution']}:{row['seed']}"
            for row in generalization_comparisons
            if not bool(row["generalization_pass"])
        ],
        "behavior_pass": bool(behavior_pass),
        "failed_behavior_seeds": [int(row["seed"]) for row in behavior_comparisons if not bool(row["behavior_pass"])],
        "reset_zero_all_ordering_retained": bool(
            behavior_comparisons
            and all(bool(row["reset_zero_all_ordering_retained"]) for row in behavior_comparisons)
        ),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "training_started": bool(ppo_returncode == 0),
        "ppo_used": True,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "next_blocker": next_blocker,
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "fresh_randomized_eval_summary_csv": run_dir / "fresh_randomized_eval_summary.csv",
        "ood_eval_summary_csv": run_dir / "ood_eval_summary.csv",
        "generalization_comparison_csv": run_dir / "generalization_comparison.csv",
        "behavior_summary_csv": run_dir / "behavior_summary.csv",
        "behavior_comparison_csv": run_dir / "behavior_comparison.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_csv_rows(run_dir / "proof_replay_summary.csv", proof_rows)
    write_csv_rows(run_dir / "fresh_randomized_eval_summary.csv", fresh_rows)
    write_csv_rows(run_dir / "ood_eval_summary.csv", ood_rows)
    write_csv_rows(run_dir / "generalization_comparison.csv", generalization_comparisons)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    write_csv_rows(run_dir / "route_decision.csv", _route_decision_rows(summary))
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run smoke guarded PPO from alpha_1_0 and gate the raw proposal.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--config", type=Path, default=DEFAULT_PPO_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--ppo-run-dir", type=Path, default=DEFAULT_PPO_RUN_DIR)
    parser.add_argument("--device", choices=["config", "auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_post_promotion_guarded_ppo_smoke(
        base_checkpoint=args.base_checkpoint,
        config_path=args.config,
        run_dir=args.run_dir,
        ppo_run_dir=args.ppo_run_dir,
        device=args.device,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"ppo_returncode={summary['ppo_returncode']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
