"""Promotion/generalization comparison gate for the M966 direction-target candidate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.evaluate import evaluate_policy, load_env_config
from autodrift.public_base_direction_target_actor_fit_replay_gate import (
    DEFAULT_BASE_CHECKPOINT,
    DEFAULT_ENV_CONFIG,
    DirectionTargetCandidate,
    _actor_inputs_changed,
    _run_old_key_diagnostic,
    _run_public_replay_gates,
    _run_source_diverse_diagnostic,
)


DEFAULT_CANDIDATE_CHECKPOINT = Path("runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt")
DEFAULT_RUN_DIR = Path("runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate")
DEFAULT_OOD_ENV_CONFIG = Path("configs/eval_m574_moderate_ood_l3.json")
DEFAULT_FRESH_SEEDS = (96700, 96701)
DEFAULT_OOD_SEEDS = (96720,)
DEFAULT_BEHAVIOR_SEEDS = (9505, 9506, 96730, 96731)
BASE_POLICY_LABEL = "m399_base"
SUCCESS_TOLERANCE = 0.01
TERMINATION_TOLERANCE = 0.01
MARGIN_TOLERANCE = 0.005


@dataclass(frozen=True)
class EvalSpec:
    distribution: str
    env_config_path: Path
    seed: int
    episodes: int
    policy_label: str
    checkpoint: Path
    ablation: str = "none"


def classify_promotion_generalization_gate(
    *,
    actor_inputs_changed: bool,
    proof_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "direction_target_actor_fit_promotion_gate_contract_artifact"
    if not bool(proof_pass):
        return "direction_target_actor_fit_promotion_gate_proof_washout"
    if not bool(generalization_pass):
        return "direction_target_actor_fit_promotion_gate_generalization_regression"
    if not bool(behavior_pass):
        return "direction_target_actor_fit_promotion_gate_behavior_regression"
    return "direction_target_actor_fit_promotion_gate_candidate"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    return ["metric_artifact"]


def _episode_rates(episode_rows: list[dict[str, Any]]) -> dict[str, float]:
    frame = pd.DataFrame(episode_rows)
    if frame.empty:
        return {
            "collision_rate": 0.0,
            "obstacle_completed_rate": 0.0,
            "truncated_rate": 0.0,
        }
    return {
        "collision_rate": float(frame["collision"].astype(bool).mean()) if "collision" in frame else 0.0,
        "obstacle_completed_rate": (
            float(frame["obstacle_completed"].astype(bool).mean()) if "obstacle_completed" in frame else 0.0
        ),
        "truncated_rate": float(frame["truncated"].astype(bool).mean()) if "truncated" in frame else 0.0,
    }


def _run_eval_specs(*, specs: list[EvalSpec], device: str, run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    env_cache: dict[Path, Any] = {}
    for spec in specs:
        env_config = env_cache.setdefault(spec.env_config_path, load_env_config(spec.env_config_path))
        eval_dir = run_dir / spec.distribution / f"seed{spec.seed}_{spec.policy_label}_{spec.ablation}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        episode_rows, summary = evaluate_policy(
            policy_name="checkpoint",
            episodes=int(spec.episodes),
            seed=int(spec.seed),
            checkpoint=spec.checkpoint,
            device=device,
            env_config=env_config,
            checkpoint_ablation=spec.ablation,
        )
        pd.DataFrame(episode_rows).to_csv(eval_dir / "episodes.csv", index=False)
        write_json(eval_dir / "summary.json", summary)
        write_json(
            eval_dir / "manifest.json",
            {
                "run_type": "evaluate",
                "distribution": spec.distribution,
                "policy": "checkpoint",
                "label": spec.policy_label,
                "checkpoint": spec.checkpoint,
                "checkpoint_ablation": spec.ablation,
                "episodes": int(spec.episodes),
                "seed": int(spec.seed),
                "device": device,
                "env_config": spec.env_config_path,
            },
        )
        rates = _episode_rates(episode_rows)
        rows.append(
            {
                "distribution": spec.distribution,
                "env_config": str(spec.env_config_path),
                "seed": int(spec.seed),
                "policy_label": spec.policy_label,
                "checkpoint": str(spec.checkpoint),
                "ablation": spec.ablation,
                "run_dir": str(eval_dir),
                "episodes": int(summary["episodes"]),
                "success_rate": 1.0 - float(summary["termination_rate"]),
                "termination_rate": float(summary["termination_rate"]),
                "min_clearance_margin_mean": float(summary["min_clearance_margin_mean"]),
                "min_clearance_margin_min": float(summary["min_clearance_margin_min"]),
                "return_mean": float(summary["return_mean"]),
                **rates,
            }
        )
    return rows


def compare_eval_rows(
    rows: list[dict[str, Any]],
    *,
    candidate_label: str,
    success_tolerance: float = SUCCESS_TOLERANCE,
    termination_tolerance: float = TERMINATION_TOLERANCE,
    margin_tolerance: float = MARGIN_TOLERANCE,
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for (distribution, seed), group in frame.groupby(["distribution", "seed"], observed=True):
        base = group[group["policy_label"].eq(BASE_POLICY_LABEL) & group["ablation"].eq("none")]
        candidate = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("none")]
        if base.empty or candidate.empty:
            continue
        base_row = base.iloc[0]
        candidate_row = candidate.iloc[0]
        success_delta = float(candidate_row["success_rate"]) - float(base_row["success_rate"])
        termination_delta = float(candidate_row["termination_rate"]) - float(base_row["termination_rate"])
        margin_delta = float(candidate_row["min_clearance_margin_mean"]) - float(base_row["min_clearance_margin_mean"])
        collision_delta = float(candidate_row["collision_rate"]) - float(base_row["collision_rate"])
        pass_row = bool(
            success_delta >= -float(success_tolerance)
            and termination_delta <= float(termination_tolerance)
            and margin_delta >= -float(margin_tolerance)
            and collision_delta <= float(termination_tolerance)
        )
        comparisons.append(
            {
                "distribution": str(distribution),
                "seed": int(seed),
                "base_success_rate": float(base_row["success_rate"]),
                "candidate_success_rate": float(candidate_row["success_rate"]),
                "success_delta": success_delta,
                "base_termination_rate": float(base_row["termination_rate"]),
                "candidate_termination_rate": float(candidate_row["termination_rate"]),
                "termination_delta": termination_delta,
                "base_margin_mean": float(base_row["min_clearance_margin_mean"]),
                "candidate_margin_mean": float(candidate_row["min_clearance_margin_mean"]),
                "margin_mean_delta": margin_delta,
                "base_collision_rate": float(base_row["collision_rate"]),
                "candidate_collision_rate": float(candidate_row["collision_rate"]),
                "collision_rate_delta": collision_delta,
                "generalization_pass": pass_row,
            }
        )
    return comparisons


def compare_behavior_rows(rows: list[dict[str, Any]], *, candidate_label: str) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for seed, group in frame.groupby("seed", observed=True):
        base = group[group["policy_label"].eq(BASE_POLICY_LABEL) & group["ablation"].eq("none")].iloc[0]
        normal = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("none")].iloc[0]
        reset = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("reset_recurrent_state")].iloc[0]
        zero_all = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("zero_all_response")].iloc[0]
        success_delta = float(normal["success_rate"]) - float(base["success_rate"])
        termination_delta = float(normal["termination_rate"]) - float(base["termination_rate"])
        ordering = (
            float(normal["success_rate"]) >= float(reset["success_rate"])
            and float(reset["success_rate"]) >= float(zero_all["success_rate"])
        )
        pass_row = bool(
            success_delta >= -SUCCESS_TOLERANCE
            and termination_delta <= TERMINATION_TOLERANCE
            and ordering
        )
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


def _fresh_eval_specs(
    *,
    base_checkpoint: Path,
    candidate: DirectionTargetCandidate,
    fresh_env_config: Path,
    ood_env_config: Path,
    fresh_seeds: tuple[int, ...],
    ood_seeds: tuple[int, ...],
    fresh_episodes: int,
    ood_episodes: int,
) -> list[EvalSpec]:
    specs: list[EvalSpec] = []
    for distribution, env_config, seeds, episodes in (
        ("fresh_public", fresh_env_config, fresh_seeds, fresh_episodes),
        ("moderate_ood", ood_env_config, ood_seeds, ood_episodes),
    ):
        for seed in seeds:
            specs.extend(
                [
                    EvalSpec(
                        distribution=distribution,
                        env_config_path=env_config,
                        seed=int(seed),
                        episodes=int(episodes),
                        policy_label=BASE_POLICY_LABEL,
                        checkpoint=base_checkpoint,
                    ),
                    EvalSpec(
                        distribution=distribution,
                        env_config_path=env_config,
                        seed=int(seed),
                        episodes=int(episodes),
                        policy_label=candidate.label,
                        checkpoint=candidate.checkpoint,
                    ),
                ]
            )
    return specs


def _behavior_eval_specs(
    *,
    base_checkpoint: Path,
    candidate: DirectionTargetCandidate,
    env_config_path: Path,
    seeds: tuple[int, ...],
    episodes: int,
) -> list[EvalSpec]:
    specs: list[EvalSpec] = []
    for seed in seeds:
        specs.extend(
            [
                EvalSpec(
                    distribution="behavior",
                    env_config_path=env_config_path,
                    seed=int(seed),
                    episodes=int(episodes),
                    policy_label=BASE_POLICY_LABEL,
                    checkpoint=base_checkpoint,
                ),
                EvalSpec(
                    distribution="behavior",
                    env_config_path=env_config_path,
                    seed=int(seed),
                    episodes=int(episodes),
                    policy_label=candidate.label,
                    checkpoint=candidate.checkpoint,
                ),
                EvalSpec(
                    distribution="behavior",
                    env_config_path=env_config_path,
                    seed=int(seed),
                    episodes=int(episodes),
                    policy_label=candidate.label,
                    checkpoint=candidate.checkpoint,
                    ablation="reset_recurrent_state",
                ),
                EvalSpec(
                    distribution="behavior",
                    env_config_path=env_config_path,
                    seed=int(seed),
                    episodes=int(episodes),
                    policy_label=candidate.label,
                    checkpoint=candidate.checkpoint,
                    ablation="zero_all_response",
                ),
            ]
        )
    return specs


def _route_decision_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "result_class": str(summary["result_class"]),
            "proof_pass": bool(summary["proof_pass"]),
            "generalization_pass": bool(summary["generalization_pass"]),
            "behavior_pass": bool(summary["behavior_pass"]),
            "actor_inputs_changed": bool(summary["actor_inputs_changed"]),
            "training_started": bool(summary["training_started"]),
            "ppo_used": bool(summary["ppo_used"]),
            "promoted": bool(summary["promoted"]),
            "next_blocker": str(summary["next_blocker"]),
        }
    ]


def run_promotion_generalization_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    run_dir: Path,
    device: str,
    fresh_env_config: Path = DEFAULT_ENV_CONFIG,
    ood_env_config: Path = DEFAULT_OOD_ENV_CONFIG,
    behavior_env_config: Path = DEFAULT_ENV_CONFIG,
    fresh_episodes: int = 256,
    ood_episodes: int = 128,
    behavior_episodes: int = 80,
    max_continuation_steps: int = 60,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate = DirectionTargetCandidate(alpha=1.0, checkpoint=candidate_checkpoint)
    actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate.checkpoint)
    proof_rows = _run_public_replay_gates(
        base_checkpoint=base_checkpoint,
        candidate=candidate,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    proof_pass = all(bool(row["gate_pass"]) for row in proof_rows) and not actor_inputs_changed
    source_diverse_summary = _run_source_diverse_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate=candidate,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
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
            fresh_seeds=DEFAULT_FRESH_SEEDS,
            ood_seeds=DEFAULT_OOD_SEEDS,
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
            seeds=DEFAULT_BEHAVIOR_SEEDS,
            episodes=behavior_episodes,
        ),
        device=device,
        run_dir=run_dir / "behavior_evals",
    )
    behavior_comparisons = compare_behavior_rows(behavior_rows, candidate_label=candidate.label)
    behavior_pass = all(bool(row["behavior_pass"]) for row in behavior_comparisons)
    result_class = classify_promotion_generalization_gate(
        actor_inputs_changed=actor_inputs_changed,
        proof_pass=proof_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    if result_class.endswith("_candidate"):
        next_blocker = "direction-target actor-fit promotion audit"
    elif result_class.endswith("_proof_washout"):
        next_blocker = "direction-target actor-fit proof_washout audit"
    elif result_class.endswith("_generalization_regression"):
        next_blocker = "direction-target actor-fit generalization regression audit"
    elif result_class.endswith("_behavior_regression"):
        next_blocker = "direction-target actor-fit behavior regression audit"
    else:
        next_blocker = "direction-target actor-fit promotion gate contract audit"
    summary = {
        "run_type": "public_base_direction_target_actor_fit_promotion_generalization_gate",
        "baseline_checkpoint": base_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
        "candidate_label": candidate.label,
        "fresh_env_config": fresh_env_config,
        "ood_env_config": ood_env_config,
        "behavior_env_config": behavior_env_config,
        "fresh_episodes": int(fresh_episodes),
        "ood_episodes": int(ood_episodes),
        "behavior_episodes": int(behavior_episodes),
        "max_continuation_steps": int(max_continuation_steps),
        "proof_replay_surface_count": int(len(proof_rows)),
        "proof_replay_gates_passed": int(sum(1 for row in proof_rows if bool(row.get("gate_pass", False)))),
        "proof_pass": bool(proof_pass),
        "failed_proof_surfaces": [row["surface"] for row in proof_rows if not bool(row["gate_pass"])],
        "source_diverse_protected_status": (
            "pass" if bool(source_diverse_summary.get("overall_pass", False)) else "diagnostic_failed"
        ),
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
        "behavior_seed_count": int(len(DEFAULT_BEHAVIOR_SEEDS)),
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
    parser = argparse.ArgumentParser(description="Run no-training promotion/generalization gate for M966 alpha_1_0.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--fresh-env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--ood-env-config", type=Path, default=DEFAULT_OOD_ENV_CONFIG)
    parser.add_argument("--behavior-env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_promotion_generalization_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        run_dir=args.run_dir,
        device=args.device,
        fresh_env_config=args.fresh_env_config,
        ood_env_config=args.ood_env_config,
        behavior_env_config=args.behavior_env_config,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
