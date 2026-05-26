"""Public replay gate for temporal sequence objective update candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.capability_step_temporal_sequence_objective import load_corpus
from autodrift.capability_step_temporal_sequence_update_probe import (
    ACTOR_MEAN_PREFIX,
    changed_parameter_names,
    clone_state_dict,
    evaluate_state_exact,
    recurrent_logp_sums,
    tensors_from_corpus,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy
from autodrift.evaluate import evaluate_policy, load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.old_key_neighborhood_targeted_replay import run_targeted_replay
from autodrift.public_base_controlled_fusion_candidate_replay_gate import (
    DEFAULT_BEHAVIOR_SEEDS,
    DEFAULT_ENV_CONFIG,
    DEFAULT_OLD_KEY_COMPACT_CORPUS,
    DEFAULT_OLD_KEY_REFERENCE_MANIFEST,
    DEFAULT_PUBLIC_REPLAY_SURFACES,
    DEFAULT_SOURCE_DIVERSE_SURFACES,
)
from autodrift.source_diverse_protected_gate import ReplayGateSpec, run_source_diverse_protected_gate
from autodrift.train_ppo import resolve_device


DEFAULT_BASE_CHECKPOINT = Path("runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt")
DEFAULT_CANDIDATE_CHECKPOINTS = Path("runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv")
DEFAULT_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_METADATA = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv")
DEFAULT_BASE_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")
DEFAULT_RUN_DIR = Path("runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate")
BASE_POLICY_LABEL = "m974_base"
CANDIDATE_POLICY_PREFIX = "m1002_temporal"
M267_M264_SURFACE = "m267_m264"


@dataclass(frozen=True)
class TemporalSequenceCandidate:
    alpha: float
    checkpoint: Path

    @property
    def label(self) -> str:
        return f"{CANDIDATE_POLICY_PREFIX}_a{self.alpha:g}".replace(".", "_")


@dataclass(frozen=True)
class BehaviorSpec:
    label: str
    checkpoint: Path
    ablation: str
    seed: int


def checkpoint_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_temporal_sequence_candidates(
    candidate_checkpoints_csv: Path,
    interpolation_metrics_csv: Path | None = None,
) -> list[TemporalSequenceCandidate]:
    frame = pd.read_csv(candidate_checkpoints_csv)
    missing = [column for column in ("alpha", "checkpoint") if column not in frame.columns]
    if missing:
        raise ValueError("candidate checkpoint CSV is missing columns: " + ", ".join(missing))
    candidates = {
        float(row["alpha"]): TemporalSequenceCandidate(
            alpha=float(row["alpha"]),
            checkpoint=Path(str(row["checkpoint"])),
        )
        for _, row in frame.iterrows()
    }
    if interpolation_metrics_csv is not None and interpolation_metrics_csv.exists():
        metrics = pd.read_csv(interpolation_metrics_csv)
        if {"alpha", "weighted_total_loss", "exact_gate_pass"}.issubset(metrics.columns):
            exact = metrics[metrics["exact_gate_pass"].astype(bool)].copy()
            ranked = exact.sort_values(["weighted_total_loss", "candidate_action_l2_mean"], ascending=[True, True])
            ordered = [candidates[float(row["alpha"])] for _, row in ranked.iterrows() if float(row["alpha"]) in candidates]
            if ordered:
                return ordered
    return sorted(candidates.values(), key=lambda item: item.alpha, reverse=True)


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


def _surface_path(label: str) -> Path:
    for surface_label, corpus_csv in DEFAULT_PUBLIC_REPLAY_SURFACES:
        if surface_label == label:
            return corpus_csv
    raise ValueError(f"unknown public replay surface: {label}")


def _base_metrics(base_summary_path: Path) -> dict[str, float]:
    summary = read_json(base_summary_path)
    names = (
        "weighted_total_loss",
        "weighted_normal_sequence_nll",
        "weighted_temporal_preference_loss",
        "weighted_logp_gap_mean",
        "temporal_logp_gap_p10",
    )
    return {name: float(summary[name]) for name in names}


def exact_contract_rows(
    *,
    base_checkpoint: Path,
    candidates: list[TemporalSequenceCandidate],
    corpus_path: Path,
    base_summary_path: Path,
    device: str,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> list[dict[str, Any]]:
    resolved_device = resolve_device(device)
    base_model, _ = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    base_model.eval()
    base_state = clone_state_dict(base_model)
    corpus = load_corpus(corpus_path)
    tensors = tensors_from_corpus(corpus, resolved_device)
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(base_model, tensors, "normal_hidden").detach()
    base_metrics = _base_metrics(base_summary_path)

    rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        candidate_model, _ = load_actor_critic_checkpoint(candidate.checkpoint, device=str(resolved_device))
        candidate_state = clone_state_dict(candidate_model)
        changed = changed_parameter_names(base_state, candidate_state)
        non_actor_changed = any(not name.startswith(ACTOR_MEAN_PREFIX) for name in changed)
        actor_mean_changed = any(name.startswith(ACTOR_MEAN_PREFIX) for name in changed)
        actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate.checkpoint)
        exact = evaluate_state_exact(
            model=base_model,
            state=candidate_state,
            corpus=corpus,
            tensors=tensors,
            base_normal_logp=base_normal_logp,
            base_metrics=base_metrics,
            device=resolved_device,
            alpha=float(candidate.alpha),
            candidate=candidate.label,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        exact["rank"] = int(rank)
        exact["checkpoint"] = str(candidate.checkpoint)
        exact["checkpoint_sha256"] = checkpoint_sha256(candidate.checkpoint)
        exact["actor_inputs_changed"] = bool(actor_inputs_changed)
        exact["actor_mean_changed"] = bool(actor_mean_changed)
        exact["non_actor_parameter_changed"] = bool(non_actor_changed)
        exact["changed_parameter_count"] = int(len(changed))
        exact["changed_parameter_names"] = ";".join(changed)
        exact["contract_gate_pass"] = bool(not actor_inputs_changed and actor_mean_changed and not non_actor_changed)
        exact["exact_contract_gate_pass"] = bool(exact["exact_gate_pass"] and exact["contract_gate_pass"])
        rows.append(exact)
    return rows


def _replay_summary_row(
    *,
    surface: str,
    run_dir: Path,
    corpus_csv: Path,
    candidate: TemporalSequenceCandidate,
    summary: dict[str, Any],
    actor_inputs_changed: bool,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "alpha": float(candidate.alpha),
        "candidate_label": candidate.label,
        "candidate_checkpoint": str(candidate.checkpoint),
        "run_dir": str(run_dir),
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


def run_candidate_m267_preflight(
    *,
    base_checkpoint: Path,
    candidates: list[TemporalSequenceCandidate],
    exact_rows: list[dict[str, Any]],
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    exact_pass_alphas = {float(row["alpha"]) for row in exact_rows if bool(row.get("exact_contract_gate_pass", False))}
    corpus_csv = _surface_path(M267_M264_SURFACE)
    for candidate in candidates:
        if float(candidate.alpha) not in exact_pass_alphas:
            rows.append(
                {
                    "surface": M267_M264_SURFACE,
                    "alpha": float(candidate.alpha),
                    "candidate_label": candidate.label,
                    "candidate_checkpoint": str(candidate.checkpoint),
                    "run_dir": "",
                    "corpus_csv": str(corpus_csv),
                    "rows": 0,
                    "baseline_success_drop_count": 0,
                    "candidate_success_drop_count": 0,
                    "normal_success_delta": 0.0,
                    "normal_margin_mean_delta": 0.0,
                    "margin_gap_mean_delta": 0.0,
                    "actor_inputs_changed": _actor_inputs_changed(base_checkpoint, candidate.checkpoint),
                    "gate_pass": False,
                    "skipped_reason": "exact_contract_gate_failed",
                }
            )
            continue
        actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate.checkpoint)
        gate_dir = run_dir / "candidate_preflight" / candidate.label
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=(
                CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
                CheckpointSpec(label=candidate.label, path=candidate.checkpoint),
            ),
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=candidate.label,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        row = _replay_summary_row(
            surface=M267_M264_SURFACE,
            run_dir=gate_dir,
            corpus_csv=corpus_csv,
            candidate=candidate,
            summary=summary,
            actor_inputs_changed=actor_inputs_changed,
        )
        row["skipped_reason"] = ""
        rows.append(row)
    return rows


def select_preflight_candidate(
    candidates: list[TemporalSequenceCandidate],
    preflight_rows: list[dict[str, Any]],
) -> TemporalSequenceCandidate | None:
    passed = {float(row["alpha"]) for row in preflight_rows if bool(row.get("gate_pass", False))}
    for candidate in candidates:
        if float(candidate.alpha) in passed:
            return candidate
    return None


def _run_public_replay_gates(
    *,
    base_checkpoint: Path,
    candidate: TemporalSequenceCandidate,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate.checkpoint)
    checkpoints = (
        CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
        CheckpointSpec(label=candidate.label, path=candidate.checkpoint),
    )
    for surface, corpus_csv in DEFAULT_PUBLIC_REPLAY_SURFACES:
        gate_dir = run_dir / "full_gates" / f"{surface}_replay"
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=checkpoints,
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=candidate.label,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        rows.append(
            _replay_summary_row(
                surface=surface,
                run_dir=gate_dir,
                corpus_csv=corpus_csv,
                candidate=candidate,
                summary=summary,
                actor_inputs_changed=actor_inputs_changed,
            )
        )
    return rows


def _run_source_diverse_diagnostic(
    *,
    base_checkpoint: Path,
    candidate: TemporalSequenceCandidate,
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
            candidate_policy=candidate.label,
        )
        for label, corpus_csv in DEFAULT_SOURCE_DIVERSE_SURFACES
    )
    return run_source_diverse_protected_gate(
        checkpoint_specs=(
            CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
            CheckpointSpec(label=candidate.label, path=candidate.checkpoint),
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
    candidate: TemporalSequenceCandidate,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    return run_targeted_replay(
        reference_manifest=DEFAULT_OLD_KEY_REFERENCE_MANIFEST,
        compact_corpus_csv=DEFAULT_OLD_KEY_COMPACT_CORPUS,
        checkpoint_policies=(
            CheckpointPolicy(name=BASE_POLICY_LABEL, path=base_checkpoint),
            CheckpointPolicy(name=candidate.label, path=candidate.checkpoint),
        ),
        run_dir=run_dir / "old_key_neighborhood_diagnostic",
        device=device,
    )


def _run_behavior_evaluations(
    *,
    base_checkpoint: Path,
    candidate: TemporalSequenceCandidate,
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
                BehaviorSpec(label=BASE_POLICY_LABEL, checkpoint=base_checkpoint, ablation="none", seed=seed),
                BehaviorSpec(label=candidate.label, checkpoint=candidate.checkpoint, ablation="none", seed=seed),
                BehaviorSpec(
                    label=f"{candidate.label}_reset",
                    checkpoint=candidate.checkpoint,
                    ablation="reset_recurrent_state",
                    seed=seed,
                ),
                BehaviorSpec(
                    label=f"{candidate.label}_zero_all",
                    checkpoint=candidate.checkpoint,
                    ablation="zero_all_response",
                    seed=seed,
                ),
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
                "alpha": float(candidate.alpha) if spec.label != BASE_POLICY_LABEL else 0.0,
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


def _behavior_pass(rows: list[dict[str, Any]], candidate: TemporalSequenceCandidate) -> tuple[bool, list[dict[str, Any]]]:
    frame = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for seed in DEFAULT_BEHAVIOR_SEEDS:
        group = frame[frame["seed"].astype(int).eq(int(seed))]
        base = group[group["label"].eq(BASE_POLICY_LABEL)].iloc[0]
        normal = group[group["label"].eq(candidate.label)].iloc[0]
        reset = group[group["label"].eq(f"{candidate.label}_reset")].iloc[0]
        zero_all = group[group["label"].eq(f"{candidate.label}_zero_all")].iloc[0]
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


def classify_temporal_sequence_public_replay_gate(
    *,
    actor_inputs_changed: bool,
    exact_contract_pass_count: int,
    candidate_preflight_pass_count: int,
    selected_candidate: TemporalSequenceCandidate | None,
    six_public_replay_gates_pass: bool,
    behavior_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "temporal_sequence_public_replay_gate_contract_artifact"
    if int(exact_contract_pass_count) <= 0:
        return "temporal_sequence_public_replay_gate_no_exact_candidate"
    if int(candidate_preflight_pass_count) <= 0 or selected_candidate is None:
        return "temporal_sequence_public_replay_gate_no_preflight_candidate"
    if not bool(six_public_replay_gates_pass):
        return "temporal_sequence_public_replay_gate_proof_washout"
    if not bool(behavior_pass):
        return "temporal_sequence_public_replay_gate_behavior_regression"
    return "temporal_sequence_public_replay_gate_pass"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_pass"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_behavior_regression"):
        return ["behavior_regression"]
    if result_class.endswith("_no_exact_candidate") or result_class.endswith("_no_preflight_candidate"):
        return ["proof_washout"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    return ["metric_artifact"]


def _route_decision_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "result_class": str(summary["result_class"]),
            "selected_alpha": summary.get("selected_alpha"),
            "selected_checkpoint": summary.get("selected_checkpoint"),
            "exact_contract_pass_count": int(summary.get("exact_contract_pass_count", 0)),
            "candidate_preflight_pass_count": int(summary.get("candidate_preflight_pass_count", 0)),
            "public_replay_gates_passed": int(summary.get("public_replay_gates_passed", 0)),
            "six_public_replay_gates_pass": bool(summary.get("six_public_replay_gates_pass", False)),
            "behavior_pass": bool(summary.get("behavior_pass", False)),
            "training_started": bool(summary.get("training_started", False)),
            "ppo_used": bool(summary.get("ppo_used", False)),
            "promoted": bool(summary.get("promoted", False)),
            "next_blocker": str(summary.get("next_blocker", "")),
        }
    ]


def _next_blocker(result_class: str) -> str:
    if result_class.endswith("_pass"):
        return "temporal sequence candidate promotion/generalization audit design"
    if result_class.endswith("_no_exact_candidate"):
        return "temporal sequence exact contract failure audit"
    if result_class.endswith("_no_preflight_candidate"):
        return "temporal sequence M267/M264 proof_washout audit"
    if result_class.endswith("_proof_washout"):
        return "temporal sequence public replay failure audit"
    if result_class.endswith("_behavior_regression"):
        return "temporal sequence behavior regression audit"
    return "temporal sequence public replay contract audit"


def run_temporal_sequence_public_replay_gate(
    *,
    base_checkpoint: Path,
    candidate_checkpoints_csv: Path,
    interpolation_metrics_csv: Path | None,
    corpus_path: Path,
    base_summary_path: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path = DEFAULT_ENV_CONFIG,
    behavior_episodes: int = 80,
    max_continuation_steps: int = 60,
    preference_margin: float = 0.05,
    lambda_pref: float = 1.0,
    lambda_anchor: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidates = load_temporal_sequence_candidates(candidate_checkpoints_csv, interpolation_metrics_csv)
    exact_rows = exact_contract_rows(
        base_checkpoint=base_checkpoint,
        candidates=candidates,
        corpus_path=corpus_path,
        base_summary_path=base_summary_path,
        device=device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    preflight_rows = run_candidate_m267_preflight(
        base_checkpoint=base_checkpoint,
        candidates=candidates,
        exact_rows=exact_rows,
        env_config_path=env_config_path,
        device=device,
        run_dir=run_dir,
        max_continuation_steps=max_continuation_steps,
    )
    selected = select_preflight_candidate(candidates, preflight_rows)
    exact_contract_pass_count = sum(1 for row in exact_rows if bool(row.get("exact_contract_gate_pass", False)))
    candidate_preflight_pass_count = sum(1 for row in preflight_rows if bool(row.get("gate_pass", False)))
    public_replay_rows: list[dict[str, Any]] = []
    behavior_rows: list[dict[str, Any]] = []
    behavior_comparisons: list[dict[str, Any]] = []
    source_diverse_summary: dict[str, Any] = {"status": "not_run_no_selected_candidate", "overall_pass": False}
    old_key_summary: dict[str, Any] = {"status": "not_run_no_selected_candidate"}
    six_public_replay_gates_pass = False
    behavior_gate_pass = False
    actor_inputs_changed = any(bool(row.get("actor_inputs_changed", False)) for row in exact_rows)
    if selected is not None:
        public_replay_rows = _run_public_replay_gates(
            base_checkpoint=base_checkpoint,
            candidate=selected,
            env_config_path=env_config_path,
            device=device,
            run_dir=run_dir,
            max_continuation_steps=max_continuation_steps,
        )
        actor_inputs_changed = bool(actor_inputs_changed or _actor_inputs_changed(base_checkpoint, selected.checkpoint))
        six_public_replay_gates_pass = all(bool(row["gate_pass"]) for row in public_replay_rows)
        source_diverse_summary = _run_source_diverse_diagnostic(
            base_checkpoint=base_checkpoint,
            candidate=selected,
            env_config_path=env_config_path,
            device=device,
            run_dir=run_dir,
            max_continuation_steps=max_continuation_steps,
        )
        old_key_summary = _run_old_key_diagnostic(
            base_checkpoint=base_checkpoint,
            candidate=selected,
            device=device,
            run_dir=run_dir,
        )
        behavior_rows = _run_behavior_evaluations(
            base_checkpoint=base_checkpoint,
            candidate=selected,
            env_config_path=env_config_path,
            device=device,
            run_dir=run_dir,
            episodes=behavior_episodes,
        )
        behavior_gate_pass, behavior_comparisons = _behavior_pass(behavior_rows, selected)
    result_class = classify_temporal_sequence_public_replay_gate(
        actor_inputs_changed=actor_inputs_changed,
        exact_contract_pass_count=exact_contract_pass_count,
        candidate_preflight_pass_count=candidate_preflight_pass_count,
        selected_candidate=selected,
        six_public_replay_gates_pass=six_public_replay_gates_pass,
        behavior_pass=behavior_gate_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "capability_step_temporal_sequence_public_replay_gate",
        "baseline_checkpoint": base_checkpoint,
        "candidate_checkpoints_csv": candidate_checkpoints_csv,
        "interpolation_metrics_csv": interpolation_metrics_csv,
        "corpus": corpus_path,
        "base_summary": base_summary_path,
        "candidate_count": int(len(candidates)),
        "candidate_alphas_ranked": [float(candidate.alpha) for candidate in candidates],
        "selected_alpha": float(selected.alpha) if selected is not None else None,
        "selected_checkpoint": selected.checkpoint if selected is not None else None,
        "selected_candidate_label": selected.label if selected is not None else None,
        "selected_checkpoint_sha256": checkpoint_sha256(selected.checkpoint) if selected is not None else None,
        "env_config": env_config_path,
        "behavior_episodes": int(behavior_episodes),
        "max_continuation_steps": int(max_continuation_steps),
        "preference_margin": float(preference_margin),
        "lambda_pref": float(lambda_pref),
        "lambda_anchor": float(lambda_anchor),
        "exact_contract_pass_count": int(exact_contract_pass_count),
        "candidate_preflight_pass_count": int(candidate_preflight_pass_count),
        "candidate_preflight_failed_alphas": [
            float(row["alpha"]) for row in preflight_rows if not bool(row.get("gate_pass", False))
        ],
        "public_replay_surface_count": int(len(public_replay_rows)),
        "public_replay_gates_passed": int(sum(1 for row in public_replay_rows if bool(row.get("gate_pass", False)))),
        "six_public_replay_gates_pass": bool(six_public_replay_gates_pass),
        "failed_public_replay_surfaces": [row["surface"] for row in public_replay_rows if not bool(row["gate_pass"])],
        "source_diverse_protected_status": (
            "pass" if bool(source_diverse_summary.get("overall_pass", False)) else "diagnostic_failed"
        ),
        "source_diverse_protected_summary": source_diverse_summary,
        "old_key_9944_status": "diagnostic_only" if selected is not None else "not_run_no_selected_candidate",
        "old_key_neighborhood_summary": old_key_summary,
        "behavior_seeds": list(DEFAULT_BEHAVIOR_SEEDS),
        "behavior_pass": bool(behavior_gate_pass),
        "reset_zero_all_ordering_retained": bool(
            behavior_comparisons
            and all(bool(row["reset_zero_all_ordering_retained"]) for row in behavior_comparisons)
        ),
        "actor_inputs_changed": bool(actor_inputs_changed),
        "training_started": False,
        "optimizer_started": False,
        "replay_used": True,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "next_blocker": _next_blocker(result_class),
        "exact_contract_summary_csv": run_dir / "exact_contract_summary.csv",
        "candidate_preflight_summary_csv": run_dir / "candidate_preflight_summary.csv",
        "public_replay_gate_summary_csv": run_dir / "public_replay_gate_summary.csv",
        "behavior_summary_csv": run_dir / "behavior_summary.csv",
        "behavior_comparison_csv": run_dir / "behavior_comparison.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_csv_rows(run_dir / "exact_contract_summary.csv", exact_rows)
    write_csv_rows(run_dir / "candidate_preflight_summary.csv", preflight_rows)
    write_csv_rows(run_dir / "public_replay_gate_summary.csv", public_replay_rows)
    write_csv_rows(run_dir / "behavior_summary.csv", behavior_rows)
    write_csv_rows(run_dir / "behavior_comparison.csv", behavior_comparisons)
    write_csv_rows(run_dir / "route_decision.csv", _route_decision_rows(summary))
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run public replay gate for temporal sequence objective candidates.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoints", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINTS)
    parser.add_argument("--interpolation-metrics", type=Path, default=None)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--base-summary", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_temporal_sequence_public_replay_gate(
        base_checkpoint=args.base_checkpoint,
        candidate_checkpoints_csv=args.candidate_checkpoints,
        interpolation_metrics_csv=args.interpolation_metrics,
        corpus_path=args.corpus,
        base_summary_path=args.base_summary,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        behavior_episodes=args.behavior_episodes,
        max_continuation_steps=args.max_continuation_steps,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(f"result_class={summary['result_class']}")
    print(f"selected_alpha={summary['selected_alpha']}")
    print(f"exact_contract_pass_count={summary['exact_contract_pass_count']}")
    print(f"candidate_preflight_pass_count={summary['candidate_preflight_pass_count']}")
    print(f"public_replay_gates_passed={summary['public_replay_gates_passed']}")
    print(f"behavior_pass={summary['behavior_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
