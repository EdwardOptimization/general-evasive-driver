"""Closed-loop replay/proof gate for the materialized controlled-fusion candidate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import evaluate_policy, load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.old_key_neighborhood_targeted_replay import run_targeted_replay
from autodrift.critical_key_replay_guard import CheckpointPolicy
from autodrift.source_diverse_protected_gate import (
    ReplayGateSpec,
    run_source_diverse_protected_gate,
)


DEFAULT_ENV_CONFIG = Path("configs/m121_human_view_zero_obstacle_relvel.json")
DEFAULT_PUBLIC_REPLAY_SURFACES: tuple[tuple[str, Path], ...] = (
    ("m183_m168", Path("runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("m183_m170", Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("m193_m189", Path("runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv")),
    ("m212_m204", Path("runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv")),
    ("m223_m219", Path("runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv")),
    ("m267_m264", Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")),
)
DEFAULT_SOURCE_DIVERSE_SURFACES: tuple[tuple[str, Path], ...] = (
    ("current_m333_surface", Path("runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("m317_continuity_surface", Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("m314_continuity_surface", Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
)
DEFAULT_OLD_KEY_REFERENCE_MANIFEST = Path("runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json")
DEFAULT_OLD_KEY_COMPACT_CORPUS = Path("runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv")
DEFAULT_BEHAVIOR_SEEDS = (9505, 9506)


@dataclass(frozen=True)
class BehaviorSpec:
    label: str
    checkpoint: Path
    ablation: str
    seed: int


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


def _run_public_replay_gates(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    replay_rows: list[dict[str, Any]] = []
    checkpoints = (
        CheckpointSpec(label="m399_base", path=base_checkpoint),
        CheckpointSpec(label="m944_a0725", path=candidate_checkpoint),
    )
    for label, corpus_csv in DEFAULT_PUBLIC_REPLAY_SURFACES:
        gate_dir = run_dir / "full_gates" / f"{label}_replay"
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=checkpoints,
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy="m399_base",
            candidate_policy="m944_a0725",
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        replay_rows.append(
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
    return replay_rows


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
            baseline_policy="m399_base",
            candidate_policy="m944_a0725",
        )
        for label, corpus_csv in DEFAULT_SOURCE_DIVERSE_SURFACES
    )
    return run_source_diverse_protected_gate(
        checkpoint_specs=(
            CheckpointSpec(label="m399_base", path=base_checkpoint),
            CheckpointSpec(label="m944_a0725", path=candidate_checkpoint),
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
            CheckpointPolicy(name="m399_base", path=base_checkpoint),
            CheckpointPolicy(name="m944_a0725", path=candidate_checkpoint),
        ),
        run_dir=run_dir / "old_key_neighborhood_diagnostic",
        device=device,
    )


def _run_behavior_evaluations(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    episodes: int,
) -> list[dict[str, Any]]:
    env_config = load_env_config(env_config_path)
    specs: list[BehaviorSpec] = []
    for seed in DEFAULT_BEHAVIOR_SEEDS:
        specs.extend(
            [
                BehaviorSpec(label="m399_base", checkpoint=base_checkpoint, ablation="none", seed=seed),
                BehaviorSpec(label="m944_a0725", checkpoint=candidate_checkpoint, ablation="none", seed=seed),
                BehaviorSpec(label="m944_a0725_reset", checkpoint=candidate_checkpoint, ablation="reset_recurrent_state", seed=seed),
                BehaviorSpec(label="m944_a0725_zero_all", checkpoint=candidate_checkpoint, ablation="zero_all_response", seed=seed),
            ]
        )
    rows: list[dict[str, Any]] = []
    for spec in specs:
        eval_dir = run_dir / "full_gates" / f"behavior_seed{spec.seed}_{spec.label}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        episode_rows, summary = evaluate_policy(
            policy_name="checkpoint",
            episodes=int(episodes),
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
                "policy": "checkpoint",
                "label": spec.label,
                "checkpoint": spec.checkpoint,
                "checkpoint_ablation": spec.ablation,
                "episodes": int(episodes),
                "seed": int(spec.seed),
                "device": device,
                "env_config": env_config_path,
            },
        )
        rows.append(
            {
                "seed": int(spec.seed),
                "label": spec.label,
                "checkpoint": str(spec.checkpoint),
                "ablation": spec.ablation,
                "run_dir": str(eval_dir),
                "episodes": int(summary["episodes"]),
                "success_rate": 1.0 - float(summary["termination_rate"]),
                "termination_rate": float(summary["termination_rate"]),
                "min_clearance_margin_mean": float(summary["min_clearance_margin_mean"]),
                "return_mean": float(summary["return_mean"]),
            }
        )
    return rows


def _behavior_pass(rows: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for seed in DEFAULT_BEHAVIOR_SEEDS:
        group = frame[frame["seed"].astype(int).eq(int(seed))]
        base = group[group["label"].eq("m399_base")].iloc[0]
        normal = group[group["label"].eq("m944_a0725")].iloc[0]
        reset = group[group["label"].eq("m944_a0725_reset")].iloc[0]
        zero_all = group[group["label"].eq("m944_a0725_zero_all")].iloc[0]
        success_delta = float(normal["success_rate"]) - float(base["success_rate"])
        termination_delta = float(normal["termination_rate"]) - float(base["termination_rate"])
        ordering = (
            float(normal["success_rate"]) >= float(reset["success_rate"])
            and float(reset["success_rate"]) >= float(zero_all["success_rate"])
        )
        pass_row = bool(success_delta >= -1e-9 and termination_delta <= 1e-9 and ordering)
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
    return all(bool(row["behavior_pass"]) for row in comparisons), comparisons


def classify_candidate_replay_gate(
    *,
    six_public_replay_gates_pass: bool,
    behavior_pass: bool,
    actor_inputs_changed: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "public_base_controlled_fusion_candidate_replay_gate_contract_artifact"
    if not bool(six_public_replay_gates_pass):
        return "public_base_controlled_fusion_candidate_replay_gate_proof_washout"
    if not bool(behavior_pass):
        return "public_base_controlled_fusion_candidate_replay_gate_behavior_regression"
    return "public_base_controlled_fusion_candidate_replay_gate_pass"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    return ["metric_artifact"]


def run_controlled_fusion_candidate_replay_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path = DEFAULT_ENV_CONFIG,
    behavior_episodes: int = 80,
    max_continuation_steps: int = 60,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate_checkpoint)
    replay_rows = _run_public_replay_gates(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        env_config_path=env_config_path,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    six_public_replay_gates_pass = all(bool(row["gate_pass"]) for row in replay_rows)
    source_diverse_summary = _run_source_diverse_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        env_config_path=env_config_path,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    old_key_summary = _run_old_key_diagnostic(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        device=device,
        run_dir=run_dir,
    )
    behavior_rows = _run_behavior_evaluations(
        base_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        env_config_path=env_config_path,
        device=device,
        run_dir=run_dir,
        episodes=behavior_episodes,
    )
    behavior_pass, behavior_comparisons = _behavior_pass(behavior_rows)
    result_class = classify_candidate_replay_gate(
        six_public_replay_gates_pass=six_public_replay_gates_pass,
        behavior_pass=behavior_pass,
        actor_inputs_changed=actor_inputs_changed,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "public_replay_gate_summary.csv", replay_rows)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    summary = {
        "run_type": "public_base_controlled_fusion_candidate_replay_gate",
        "baseline_checkpoint": base_checkpoint,
        "primary_checkpoint": candidate_checkpoint,
        "env_config": env_config_path,
        "behavior_episodes": int(behavior_episodes),
        "max_continuation_steps": int(max_continuation_steps),
        "exact_candidate_reference_pass": True,
        "public_replay_surface_count": int(len(replay_rows)),
        "public_replay_gates_passed": int(sum(1 for row in replay_rows if bool(row["gate_pass"]))),
        "six_public_replay_gates_pass": bool(six_public_replay_gates_pass),
        "failed_public_replay_surfaces": [row["surface"] for row in replay_rows if not bool(row["gate_pass"])],
        "source_diverse_protected_status": (
            "pass" if bool(source_diverse_summary.get("overall_pass", False)) else "diagnostic_failed"
        ),
        "source_diverse_protected_summary": source_diverse_summary,
        "old_key_9944_status": "diagnostic_only",
        "old_key_neighborhood_summary": old_key_summary,
        "behavior_seeds": list(DEFAULT_BEHAVIOR_SEEDS),
        "behavior_pass": bool(behavior_pass),
        "behavior_seed9505_success_delta": next(
            float(row["candidate_success_delta"]) for row in behavior_comparisons if int(row["seed"]) == 9505
        ),
        "behavior_seed9506_success_delta": next(
            float(row["candidate_success_delta"]) for row in behavior_comparisons if int(row["seed"]) == 9506
        ),
        "reset_zero_all_ordering_retained": bool(
            all(bool(row["reset_zero_all_ordering_retained"]) for row in behavior_comparisons)
        ),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "training_started": False,
        "optimizer_started": False,
        "replay_used": True,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "public_replay_gate_summary_csv": run_dir / "public_replay_gate_summary.csv",
        "behavior_summary_csv": run_dir / "behavior_summary.csv",
        "behavior_comparison_csv": run_dir / "behavior_comparison.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run closed-loop replay/proof gate for controlled-fusion candidate.")
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--candidate-checkpoint", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_controlled_fusion_candidate_replay_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
    )
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
