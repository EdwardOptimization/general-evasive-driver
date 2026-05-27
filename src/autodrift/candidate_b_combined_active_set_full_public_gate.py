"""Full public gate for the M1038 combined active-set candidate."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from typing import Any

import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.candidate_b_combined_active_set_repair_projection_probe import (
    combined_anchor_family_loss_rows,
)
from autodrift.capability_step_temporal_sequence_objective import load_corpus
from autodrift.capability_step_temporal_sequence_update_probe import (
    changed_parameter_names,
    clone_state_dict,
    evaluate_state_exact,
    recurrent_logp_sums,
    tensors_from_corpus,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.exact_post_ppo_repair import ExactRepairConfig, exact_loss_summary, load_repair_corpora
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
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
from autodrift.train_ppo import resolve_device


DEFAULT_BASE_CHECKPOINT = Path(
    "runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m1038_candidate_b_combined_active_set_repair_projection_probe/"
    "temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt"
)
DEFAULT_TEMPORAL_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_TEMPORAL_BASE_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")
DEFAULT_M297_NPZ = Path("runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz")
DEFAULT_M270_NPZ = Path("runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz")
DEFAULT_COMBINED_ANCHOR_NPZ = Path(
    "runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz"
)
DEFAULT_RUN_DIR = Path("runs/m1040_candidate_b_combined_active_set_full_public_gate")
DEFAULT_FRESH_SEEDS = (103900, 103901)
DEFAULT_OOD_SEEDS = (103920,)
DEFAULT_BEHAVIOR_SEEDS = (9505, 9506, 103930, 103931)
ALLOWED_CHANGED_PREFIXES = ("actor_mean.", "response_context_fusion.0.")


def _parse_seeds(text: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in str(text).split(",") if item.strip())


def changed_parameters_allowed(names: list[str], *, allowed_prefixes: tuple[str, ...] = ALLOWED_CHANGED_PREFIXES) -> bool:
    return all(any(name.startswith(prefix) for prefix in allowed_prefixes) for name in names)


def classify_full_public_gate(
    *,
    actor_inputs_changed: bool,
    allowed_surface_contract_pass: bool,
    exact_pass: bool,
    proof_pass: bool,
    source_diverse_pass: bool,
    generalization_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "candidate_b_combined_active_set_full_public_gate_contract_artifact"
    if not bool(allowed_surface_contract_pass):
        return "candidate_b_combined_active_set_full_public_gate_contract_artifact"
    if not bool(exact_pass):
        return "candidate_b_combined_active_set_full_public_gate_exact_failed"
    if not bool(proof_pass):
        return "candidate_b_combined_active_set_full_public_gate_public_replay_washout"
    if not bool(source_diverse_pass):
        return "candidate_b_combined_active_set_full_public_gate_source_diagnostic_failed"
    if not bool(generalization_pass):
        return "candidate_b_combined_active_set_full_public_gate_generalization_regression"
    if not bool(behavior_pass):
        return "candidate_b_combined_active_set_full_public_gate_behavior_regression"
    return "candidate_b_combined_active_set_full_public_gate_candidate"


def failure_types_for_full_public_gate(result_class: str) -> list[str]:
    if result_class.endswith("_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_generalization_regression"):
        return ["scenario_sampling_failure"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    if (
        result_class.endswith("_exact_failed")
        or result_class.endswith("_public_replay_washout")
        or result_class.endswith("_source_diagnostic_failed")
    ):
        return ["proof_washout"]
    return ["metric_artifact"]


def next_blocker_for_full_public_gate(result_class: str) -> str:
    if result_class.endswith("_candidate"):
        return "candidate_b_combined_active_set_promotion_audit"
    if result_class.endswith("_exact_failed"):
        return "candidate_b_combined_active_set_exact_failure_audit"
    if result_class.endswith("_public_replay_washout"):
        return "candidate_b_combined_active_set_public_replay_failure_audit"
    if result_class.endswith("_source_diagnostic_failed"):
        return "candidate_b_combined_active_set_source_diagnostic_failure_audit"
    if result_class.endswith("_generalization_regression"):
        return "candidate_b_combined_active_set_generalization_regression_audit"
    if result_class.endswith("_behavior_regression"):
        return "candidate_b_combined_active_set_behavior_regression_audit"
    return "candidate_b_combined_active_set_contract_artifact_audit"


def _actor_input_signature(checkpoint_path: Path) -> dict[str, Any]:
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
    return _actor_input_signature(base_checkpoint) != _actor_input_signature(candidate_checkpoint)


def full_public_exact_contract_rows(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    temporal_corpus: Path,
    temporal_base_summary: Path,
    preference_npz: Path,
    outcome_npz: Path,
    combined_anchor_npz: Path,
    device: str,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> list[dict[str, Any]]:
    resolved_device = resolve_device(device)
    base_model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    candidate_model, _ = load_actor_critic_checkpoint(candidate_checkpoint, device=str(resolved_device))
    base_state = clone_state_dict(base_model)
    candidate_state = clone_state_dict(candidate_model)
    changed = changed_parameter_names(base_state, candidate_state)
    actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate_checkpoint)
    allowed_surface_contract_pass = bool(changed and changed_parameters_allowed(changed))

    corpus = load_corpus(temporal_corpus)
    tensors = tensors_from_corpus(corpus, resolved_device)
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(base_model, tensors, "normal_hidden").detach()
    base_metrics = read_json(temporal_base_summary)
    exact = evaluate_state_exact(
        model=base_model,
        state=candidate_state,
        corpus=corpus,
        tensors=tensors,
        base_normal_logp=base_normal_logp,
        base_metrics={name: float(base_metrics[name]) for name in (
            "weighted_total_loss",
            "weighted_normal_sequence_nll",
            "weighted_temporal_preference_loss",
            "weighted_logp_gap_mean",
            "temporal_logp_gap_p10",
        )},
        device=resolved_device,
        alpha=0.15,
        candidate="m1038_selected",
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    preference, outcome = load_repair_corpora(
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=resolved_device,
        obs_dim=int(base_model.obs_dim),
        hidden_size=int(base_model.actor_mean.in_features),
        act_dim=int(base_model.act_dim),
    )
    config = ExactRepairConfig()
    base_summary = exact_loss_summary(
        label="candidate_b_base",
        checkpoint=base_checkpoint,
        model=base_model,
        preference=preference,
        outcome=outcome,
        config=config,
    )
    candidate_summary = exact_loss_summary(
        label="m1038_selected",
        checkpoint=candidate_checkpoint,
        model=candidate_model,
        preference=preference,
        outcome=outcome,
        config=config,
    )
    m297_delta = float(candidate_summary["exact_m297_loss"]) - float(base_summary["exact_m297_loss"])
    m270_delta = float(candidate_summary["exact_m270_loss"]) - float(base_summary["exact_m270_loss"])

    with tempfile.TemporaryDirectory(prefix="m1040_anchor_family_") as tmpdir:
        family_csv = Path(tmpdir) / "candidate_checkpoints.csv"
        write_csv_rows(
            family_csv,
            [
                {
                    "candidate_label": "candidate_b_base",
                    "source_label": "base",
                    "alpha": 0.0,
                    "checkpoint": str(base_checkpoint),
                },
                {
                    "candidate_label": "m1038_selected",
                    "source_label": "candidate",
                    "alpha": 0.15,
                    "checkpoint": str(candidate_checkpoint),
                },
            ],
        )
        family_rows = combined_anchor_family_loss_rows(
            checkpoint_rows_csv=family_csv,
            combined_anchor_npz=combined_anchor_npz,
            device=device,
        )
    candidate_family = next(row for row in family_rows if row["candidate_label"] == "m1038_selected")
    exact.update(
        {
            "checkpoint": str(candidate_checkpoint),
            "actor_inputs_changed": bool(actor_inputs_changed),
            "allowed_changed_prefixes": ";".join(ALLOWED_CHANGED_PREFIXES),
            "allowed_surface_contract_pass": bool(allowed_surface_contract_pass),
            "changed_parameter_count": int(len(changed)),
            "changed_parameter_names": ";".join(changed),
            "exact_m297_loss": float(candidate_summary["exact_m297_loss"]),
            "exact_m270_loss": float(candidate_summary["exact_m270_loss"]),
            "exact_m297_delta_vs_base": m297_delta,
            "exact_m270_delta_vs_base": m270_delta,
            "exact_m297_no_regression": bool(m297_delta <= float(config.exact_m297_tolerance)),
            "exact_m270_no_regression": bool(m270_delta <= float(config.exact_m270_tolerance)),
            "m297_m270_exact_pass": bool(
                m297_delta <= float(config.exact_m297_tolerance)
                and m270_delta <= float(config.exact_m270_tolerance)
            ),
            "combined_anchor_total_loss": float(candidate_family["combined_anchor_total_loss"]),
            "combined_anchor_m267_loss": float(candidate_family["combined_anchor_m267_loss"]),
            "combined_anchor_m183_row16_loss": float(candidate_family["combined_anchor_m183_row16_loss"]),
        }
    )
    exact["full_exact_contract_gate_pass"] = bool(
        exact["exact_gate_pass"]
        and exact["m297_m270_exact_pass"]
        and not exact["actor_inputs_changed"]
        and exact["allowed_surface_contract_pass"]
    )
    return [exact]


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


def run_combined_active_set_full_public_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    temporal_corpus: Path,
    temporal_base_summary: Path,
    preference_npz: Path,
    outcome_npz: Path,
    combined_anchor_npz: Path,
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
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate = DirectionTargetCandidate(alpha=0.15, checkpoint=candidate_checkpoint)
    exact_rows = full_public_exact_contract_rows(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        temporal_corpus=temporal_corpus,
        temporal_base_summary=temporal_base_summary,
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        combined_anchor_npz=combined_anchor_npz,
        device=device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    exact_pass = all(bool(row["full_exact_contract_gate_pass"]) for row in exact_rows)
    actor_inputs_changed = any(bool(row["actor_inputs_changed"]) for row in exact_rows)
    allowed_surface_contract_pass = all(bool(row["allowed_surface_contract_pass"]) for row in exact_rows)

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
    result_class = classify_full_public_gate(
        actor_inputs_changed=actor_inputs_changed,
        allowed_surface_contract_pass=allowed_surface_contract_pass,
        exact_pass=exact_pass,
        proof_pass=proof_pass,
        source_diverse_pass=source_diverse_pass,
        generalization_pass=generalization_pass,
        behavior_pass=behavior_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "candidate_b_combined_active_set_full_public_gate",
        "baseline_checkpoint": base_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
        "candidate_label": candidate.label,
        "temporal_corpus": temporal_corpus,
        "temporal_base_summary": temporal_base_summary,
        "preference_npz": preference_npz,
        "outcome_npz": outcome_npz,
        "combined_anchor_npz": combined_anchor_npz,
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
        "exact_pass": bool(exact_pass),
        "proof_replay_surface_count": int(len(proof_rows)),
        "proof_replay_gates_passed": int(sum(1 for row in proof_rows if bool(row.get("gate_pass", False)))),
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
        "allowed_surface_contract_pass": bool(allowed_surface_contract_pass),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_full_public_gate(result_class),
        "next_blocker": next_blocker_for_full_public_gate(result_class),
        "exact_contract_summary_csv": run_dir / "exact_contract_summary.csv",
        "proof_replay_summary_csv": run_dir / "proof_replay_summary.csv",
        "source_diverse_summary_json": run_dir / "source_diverse_summary.json",
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
    write_csv_rows(run_dir / "fresh_randomized_eval_summary.csv", fresh_rows)
    write_csv_rows(run_dir / "ood_eval_summary.csv", ood_rows)
    write_csv_rows(run_dir / "generalization_comparison.csv", generalization_comparisons)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    write_csv_rows(run_dir / "route_decision.csv", [_route_decision_row(summary)])
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full public gate for the M1038 combined active-set candidate.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_TEMPORAL_CORPUS)
    parser.add_argument("--temporal-base-summary", type=Path, default=DEFAULT_TEMPORAL_BASE_SUMMARY)
    parser.add_argument("--preference-npz", type=Path, default=DEFAULT_M297_NPZ)
    parser.add_argument("--outcome-npz", type=Path, default=DEFAULT_M270_NPZ)
    parser.add_argument("--combined-anchor-npz", type=Path, default=DEFAULT_COMBINED_ANCHOR_NPZ)
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
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_combined_active_set_full_public_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        temporal_corpus=args.temporal_corpus,
        temporal_base_summary=args.temporal_base_summary,
        preference_npz=args.preference_npz,
        outcome_npz=args.outcome_npz,
        combined_anchor_npz=args.combined_anchor_npz,
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
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
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
