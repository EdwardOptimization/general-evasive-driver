"""No-training promotion/generalization gate for materialized source-history candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy
from autodrift.evaluate import evaluate_policy, load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.materialized_source_history_interpolation_preflight import (
    _actor_inputs_changed,
    _clone_state_dict,
    _eval_exact_for_checkpoint,
)
from autodrift.materialized_source_history_objective_evaluator import (
    DEFAULT_CORRECT_MARGIN,
    DEFAULT_WRONG_COEF,
    DEFAULT_WRONG_MARGIN,
)
from autodrift.materialized_source_history_pair_group_update import _state_delta
from autodrift.old_key_neighborhood_targeted_replay import run_targeted_replay
from autodrift.public_base_controlled_fusion_candidate_replay_gate import (
    DEFAULT_OLD_KEY_COMPACT_CORPUS,
    DEFAULT_OLD_KEY_REFERENCE_MANIFEST,
    DEFAULT_PUBLIC_REPLAY_SURFACES,
    DEFAULT_SOURCE_DIVERSE_SURFACES,
)
from autodrift.source_diverse_protected_gate import ReplayGateSpec, run_source_diverse_protected_gate


DEFAULT_BASE_CHECKPOINT = Path("runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt")
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt"
)
DEFAULT_CORPUS_RUN_DIR = Path("runs/m1336_materialized_source_history_objective_corpus_export")
DEFAULT_RUN_DIR = Path("runs/m1369_public_base_promotion_generalization_gate")
DEFAULT_FRESH_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_OOD_ENV_CONFIG = Path("configs/eval_m574_moderate_ood_l3.json")
DEFAULT_FRESH_SEEDS = (136900, 136901, 136902)
DEFAULT_OOD_SEEDS = (136920, 136921)
DEFAULT_BEHAVIOR_SEEDS = (9505, 9506, 136930, 136931)
BASE_POLICY_LABEL = "public_base"
CANDIDATE_POLICY_LABEL = "candidate"
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


def parse_seed_tuple(text: str) -> tuple[int, ...]:
    seeds = tuple(int(item.strip()) for item in str(text).split(",") if item.strip())
    if not seeds:
        raise argparse.ArgumentTypeError("expected at least one seed")
    if len(set(seeds)) != len(seeds):
        raise argparse.ArgumentTypeError("seeds must be unique")
    return seeds


def classify_public_base_promotion_gate(
    *,
    actor_inputs_changed: bool,
    forbidden_parameter_mutation_detected: bool,
    log_std_l2: float,
    exact_pass: bool,
    proof_pass: bool,
    source_diverse_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if (
        bool(actor_inputs_changed)
        or bool(forbidden_parameter_mutation_detected)
        or float(log_std_l2) != 0.0
        or bool(training_started)
        or bool(ppo_used)
        or bool(promoted)
    ):
        return "materialized_source_history_public_base_promotion_gate_contract_artifact"
    if not bool(exact_pass):
        return "materialized_source_history_public_base_promotion_gate_exact_retention_failed"
    if not bool(proof_pass) or not bool(source_diverse_pass):
        return "materialized_source_history_public_base_promotion_gate_proof_washout"
    if not bool(generalization_pass):
        return "materialized_source_history_public_base_promotion_gate_generalization_regression"
    if not bool(behavior_pass):
        return "materialized_source_history_public_base_promotion_gate_behavior_regression"
    return "materialized_source_history_public_base_promotion_gate_candidate"


def failure_types_for_result_class(result_class: str) -> list[str]:
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


def next_blocker_for_result_class(result_class: str) -> str:
    if result_class.endswith("_candidate"):
        return "m1370-paper-route-public-base-promotion-audit"
    if result_class.endswith("_contract_artifact"):
        return "m1370-paper-route-public-base-contract-audit"
    if result_class.endswith("_exact_retention_failed") or result_class.endswith("_proof_washout"):
        return "m1370-paper-route-public-base-proof-failure-audit"
    if result_class.endswith("_generalization_regression"):
        return "m1370-paper-route-public-base-generalization-regression-audit"
    if result_class.endswith("_behavior_regression"):
        return "m1370-paper-route-public-base-behavior-regression-audit"
    return "m1370-paper-route-public-base-promotion-gate-artifact-audit"


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


def compare_generalization_rows(
    rows: list[dict[str, Any]],
    *,
    candidate_label: str = CANDIDATE_POLICY_LABEL,
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
            and collision_delta <= float(termination_tolerance)
            and margin_delta >= -float(margin_tolerance)
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


def compare_behavior_rows(
    rows: list[dict[str, Any]],
    *,
    candidate_label: str = CANDIDATE_POLICY_LABEL,
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for seed, group in frame.groupby("seed", observed=True):
        base = group[group["policy_label"].eq(BASE_POLICY_LABEL) & group["ablation"].eq("none")]
        normal = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("none")]
        reset = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("reset_recurrent_state")]
        zero_all = group[group["policy_label"].eq(candidate_label) & group["ablation"].eq("zero_all_response")]
        if base.empty or normal.empty or reset.empty or zero_all.empty:
            continue
        base_row = base.iloc[0]
        normal_row = normal.iloc[0]
        reset_row = reset.iloc[0]
        zero_all_row = zero_all.iloc[0]
        success_delta = float(normal_row["success_rate"]) - float(base_row["success_rate"])
        termination_delta = float(normal_row["termination_rate"]) - float(base_row["termination_rate"])
        ordering = (
            float(normal_row["success_rate"]) >= float(reset_row["success_rate"])
            and float(reset_row["success_rate"]) >= float(zero_all_row["success_rate"])
        )
        pass_row = bool(
            success_delta >= -SUCCESS_TOLERANCE
            and termination_delta <= TERMINATION_TOLERANCE
            and ordering
        )
        comparisons.append(
            {
                "seed": int(seed),
                "base_success_rate": float(base_row["success_rate"]),
                "candidate_success_rate": float(normal_row["success_rate"]),
                "reset_success_rate": float(reset_row["success_rate"]),
                "zero_all_success_rate": float(zero_all_row["success_rate"]),
                "candidate_success_delta": success_delta,
                "candidate_termination_delta": termination_delta,
                "reset_zero_all_ordering_retained": ordering,
                "behavior_pass": pass_row,
            }
        )
    return comparisons


def _generalization_specs(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
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
                    EvalSpec(distribution, env_config, seed, episodes, BASE_POLICY_LABEL, base_checkpoint),
                    EvalSpec(distribution, env_config, seed, episodes, CANDIDATE_POLICY_LABEL, candidate_checkpoint),
                ]
            )
    return specs


def _behavior_specs(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config: Path,
    seeds: tuple[int, ...],
    episodes: int,
) -> list[EvalSpec]:
    specs: list[EvalSpec] = []
    for seed in seeds:
        specs.extend(
            [
                EvalSpec("behavior", env_config, seed, episodes, BASE_POLICY_LABEL, base_checkpoint),
                EvalSpec("behavior", env_config, seed, episodes, CANDIDATE_POLICY_LABEL, candidate_checkpoint),
                EvalSpec(
                    "behavior",
                    env_config,
                    seed,
                    episodes,
                    CANDIDATE_POLICY_LABEL,
                    candidate_checkpoint,
                    "reset_recurrent_state",
                ),
                EvalSpec(
                    "behavior",
                    env_config,
                    seed,
                    episodes,
                    CANDIDATE_POLICY_LABEL,
                    candidate_checkpoint,
                    "zero_all_response",
                ),
            ]
        )
    return specs


def _run_public_replay_gates(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    checkpoint_specs = (
        CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
        CheckpointSpec(label=CANDIDATE_POLICY_LABEL, path=candidate_checkpoint),
    )
    rows: list[dict[str, Any]] = []
    for label, corpus_csv in DEFAULT_PUBLIC_REPLAY_SURFACES:
        gate_dir = run_dir / "proof_replay" / label
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=checkpoint_specs,
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=CANDIDATE_POLICY_LABEL,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        rows.append(
            {
                "surface": label,
                "run_dir": str(gate_dir),
                "corpus_csv": str(corpus_csv),
                "rows": int(summary["rows"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "gate_pass": bool(summary["gate_pass"]),
            }
        )
    return rows


def _run_source_diverse_diagnostic(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> dict[str, Any]:
    replay_specs = tuple(
        ReplayGateSpec(
            label=label,
            corpus_csv=corpus_csv,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=CANDIDATE_POLICY_LABEL,
        )
        for label, corpus_csv in DEFAULT_SOURCE_DIVERSE_SURFACES
    )
    return run_source_diverse_protected_gate(
        checkpoint_specs=(
            CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
            CheckpointSpec(label=CANDIDATE_POLICY_LABEL, path=candidate_checkpoint),
        ),
        replay_gate_specs=replay_specs,
        diagnostic_csv_specs=(),
        env_config_path=env_config_path,
        max_rows=0,
        max_continuation_steps=max_continuation_steps,
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.005,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
        device=device,
        run_dir=run_dir / "source_diverse_protected_diagnostic",
    )


def _run_old_key_diagnostic(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    return run_targeted_replay(
        reference_manifest=DEFAULT_OLD_KEY_REFERENCE_MANIFEST,
        compact_corpus_csv=DEFAULT_OLD_KEY_COMPACT_CORPUS,
        checkpoint_policies=(
            CheckpointPolicy(name=BASE_POLICY_LABEL, path=base_checkpoint),
            CheckpointPolicy(name=CANDIDATE_POLICY_LABEL, path=candidate_checkpoint),
        ),
        run_dir=run_dir / "old_key_neighborhood_diagnostic",
        device=device,
    )


def _exact_contract_rows(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    device: str,
) -> list[dict[str, Any]]:
    base_model, base_data = load_actor_critic_checkpoint(base_checkpoint, device="cpu")
    candidate_model, candidate_data = load_actor_critic_checkpoint(candidate_checkpoint, device="cpu")
    actor_inputs_changed = _actor_inputs_changed(base_model, base_data, candidate_model, candidate_data)
    parameter_delta = _state_delta(_clone_state_dict(base_model), candidate_model.state_dict())
    base_exact, base_group, base_eval_fold = _eval_exact_for_checkpoint(
        checkpoint_path=base_checkpoint,
        corpus_run_dir=corpus_run_dir,
        run_dir=run_dir / "base",
        device=device,
        correct_margin=DEFAULT_CORRECT_MARGIN,
        wrong_margin=DEFAULT_WRONG_MARGIN,
        wrong_coef=DEFAULT_WRONG_COEF,
    )
    candidate_exact, candidate_group, candidate_eval_fold = _eval_exact_for_checkpoint(
        checkpoint_path=candidate_checkpoint,
        corpus_run_dir=corpus_run_dir,
        run_dir=run_dir / "candidate",
        device=device,
        correct_margin=DEFAULT_CORRECT_MARGIN,
        wrong_margin=DEFAULT_WRONG_MARGIN,
        wrong_coef=DEFAULT_WRONG_COEF,
    )
    base_combined = float(base_exact.get("combined_loss_mean", float("nan")))
    candidate_combined = float(candidate_exact.get("combined_loss_mean", float("nan")))
    base_group_min = float(base_group.get("group_min_joint_margin_mean", float("nan")))
    candidate_group_min = float(candidate_group.get("group_min_joint_margin_mean", float("nan")))
    combined_delta = candidate_combined - base_combined
    group_min_delta = candidate_group_min - base_group_min
    eval_fold_delta = float(candidate_eval_fold) - float(base_eval_fold)
    exact_pass = bool(
        not actor_inputs_changed
        and not bool(parameter_delta["forbidden_parameter_mutation_detected"])
        and float(parameter_delta["log_std_l2"]) == 0.0
        and bool(base_exact.get("exact_objective_finite", False))
        and bool(candidate_exact.get("exact_objective_finite", False))
        and combined_delta <= 1.0e-12
        and group_min_delta >= -1.0e-12
        and eval_fold_delta >= -1.0e-12
    )
    return [
        {
            "base_checkpoint": str(base_checkpoint),
            "candidate_checkpoint": str(candidate_checkpoint),
            "corpus_run_dir": str(corpus_run_dir),
            "actor_inputs_changed": bool(actor_inputs_changed),
            "forbidden_parameter_mutation_detected": bool(
                parameter_delta["forbidden_parameter_mutation_detected"]
            ),
            "log_std_l2": float(parameter_delta["log_std_l2"]),
            "allowed_parameter_l2": float(parameter_delta["allowed_parameter_l2"]),
            "allowed_parameter_max_abs": float(parameter_delta["allowed_parameter_max_abs"]),
            "base_combined_loss_mean": base_combined,
            "candidate_combined_loss_mean": candidate_combined,
            "combined_loss_delta_vs_base": combined_delta,
            "base_group_min_joint_margin_mean": base_group_min,
            "candidate_group_min_joint_margin_mean": candidate_group_min,
            "group_min_joint_margin_delta_vs_base": group_min_delta,
            "base_eval_fold_4_group_min_joint_margin_mean": float(base_eval_fold),
            "candidate_eval_fold_4_group_min_joint_margin_mean": float(candidate_eval_fold),
            "eval_fold_4_group_min_joint_margin_delta_vs_base": eval_fold_delta,
            "base_exact_objective_finite": bool(base_exact.get("exact_objective_finite", False)),
            "candidate_exact_objective_finite": bool(candidate_exact.get("exact_objective_finite", False)),
            "exact_pass": bool(exact_pass),
        }
    ]


def _route_decision_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_class": str(summary["result_class"]),
        "exact_pass": bool(summary["exact_pass"]),
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


def run_public_base_promotion_generalization_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    corpus_run_dir: Path,
    run_dir: Path,
    device: str,
    fresh_env_config: Path,
    ood_env_config: Path,
    fresh_seeds: tuple[int, ...],
    ood_seeds: tuple[int, ...],
    behavior_seeds: tuple[int, ...],
    fresh_episodes: int,
    ood_episodes: int,
    behavior_episodes: int,
    max_continuation_steps: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    exact_rows = _exact_contract_rows(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        corpus_run_dir=corpus_run_dir,
        run_dir=run_dir / "exact_contract",
        device=device,
    )
    exact = exact_rows[0]
    exact_pass = bool(exact["exact_pass"])
    actor_inputs_changed = bool(exact["actor_inputs_changed"])
    forbidden_parameter_mutation_detected = bool(exact["forbidden_parameter_mutation_detected"])
    log_std_l2 = float(exact["log_std_l2"])
    proof_rows = _run_public_replay_gates(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    proof_pass = all(bool(row["gate_pass"]) for row in proof_rows) and not actor_inputs_changed
    source_diverse_summary = _run_source_diverse_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        env_config_path=fresh_env_config,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    source_diverse_pass = bool(source_diverse_summary.get("overall_pass", False)) and not actor_inputs_changed
    old_key_summary = _run_old_key_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        device=device,
        run_dir=run_dir,
    )
    eval_rows = _run_eval_specs(
        specs=_generalization_specs(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=candidate_checkpoint,
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
    generalization_comparisons = compare_generalization_rows(eval_rows)
    generalization_pass = bool(generalization_comparisons) and all(
        bool(row["generalization_pass"]) for row in generalization_comparisons
    )
    behavior_rows = _run_eval_specs(
        specs=_behavior_specs(
            base_checkpoint=base_checkpoint,
            candidate_checkpoint=candidate_checkpoint,
            env_config=fresh_env_config,
            seeds=behavior_seeds,
            episodes=behavior_episodes,
        ),
        device=device,
        run_dir=run_dir / "behavior_evals",
    )
    behavior_comparisons = compare_behavior_rows(behavior_rows)
    behavior_pass = bool(behavior_comparisons) and all(bool(row["behavior_pass"]) for row in behavior_comparisons)
    result_class = classify_public_base_promotion_gate(
        actor_inputs_changed=actor_inputs_changed,
        forbidden_parameter_mutation_detected=forbidden_parameter_mutation_detected,
        log_std_l2=log_std_l2,
        exact_pass=exact_pass,
        proof_pass=proof_pass,
        source_diverse_pass=source_diverse_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    fresh_rows = [row for row in eval_rows if row["distribution"] == "fresh_public"]
    ood_rows = [row for row in eval_rows if row["distribution"] == "moderate_ood"]
    summary = {
        "run_type": "materialized_source_history_public_base_promotion_generalization_gate",
        "baseline_checkpoint": base_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
        "corpus_run_dir": corpus_run_dir,
        "fresh_env_config": fresh_env_config,
        "ood_env_config": ood_env_config,
        "fresh_seeds": list(fresh_seeds),
        "ood_seeds": list(ood_seeds),
        "behavior_seeds": list(behavior_seeds),
        "fresh_episodes": int(fresh_episodes),
        "ood_episodes": int(ood_episodes),
        "behavior_episodes": int(behavior_episodes),
        "max_continuation_steps": int(max_continuation_steps),
        "exact_pass": bool(exact_pass),
        "proof_replay_surface_count": int(len(proof_rows)),
        "proof_replay_gates_passed": int(sum(1 for row in proof_rows if bool(row["gate_pass"]))),
        "proof_pass": bool(proof_pass),
        "failed_proof_surfaces": [row["surface"] for row in proof_rows if not bool(row["gate_pass"])],
        "source_diverse_pass": bool(source_diverse_pass),
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
        "forbidden_parameter_mutation_detected": bool(forbidden_parameter_mutation_detected),
        "log_std_l2": float(log_std_l2),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "next_blocker": next_blocker_for_result_class(result_class),
        "exact_contract_summary_csv": run_dir / "exact_contract_summary.csv",
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "source_diverse_summary_json": run_dir / "source_diverse_summary.json",
        "old_key_summary_json": run_dir / "old_key_neighborhood_summary.json",
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
    write_json(run_dir / "source_diverse_summary.json", source_diverse_summary)
    write_json(run_dir / "old_key_neighborhood_summary.json", old_key_summary)
    write_csv_rows(run_dir / "fresh_randomized_eval_summary.csv", fresh_rows)
    write_csv_rows(run_dir / "ood_eval_summary.csv", ood_rows)
    write_csv_rows(run_dir / "generalization_comparison.csv", generalization_comparisons)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    write_csv_rows(run_dir / "route_decision.csv", [_route_decision_row(summary)])
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run materialized source-history public-base promotion gate.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--corpus-run-dir", type=Path, default=DEFAULT_CORPUS_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--fresh-env-config", type=Path, default=DEFAULT_FRESH_ENV_CONFIG)
    parser.add_argument("--ood-env-config", type=Path, default=DEFAULT_OOD_ENV_CONFIG)
    parser.add_argument("--fresh-seeds", type=parse_seed_tuple, default=DEFAULT_FRESH_SEEDS)
    parser.add_argument("--ood-seeds", type=parse_seed_tuple, default=DEFAULT_OOD_SEEDS)
    parser.add_argument("--behavior-seeds", type=parse_seed_tuple, default=DEFAULT_BEHAVIOR_SEEDS)
    parser.add_argument("--fresh-episodes", type=int, default=256)
    parser.add_argument("--ood-episodes", type=int, default=128)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_public_base_promotion_generalization_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        corpus_run_dir=args.corpus_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        fresh_env_config=args.fresh_env_config,
        ood_env_config=args.ood_env_config,
        fresh_seeds=args.fresh_seeds,
        ood_seeds=args.ood_seeds,
        behavior_seeds=args.behavior_seeds,
        fresh_episodes=args.fresh_episodes,
        ood_episodes=args.ood_episodes,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"exact_pass={summary['exact_pass']}")
    print(f"proof_pass={summary['proof_pass']}")
    print(f"source_diverse_pass={summary['source_diverse_pass']}")
    print(f"generalization_pass={summary['generalization_pass']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
