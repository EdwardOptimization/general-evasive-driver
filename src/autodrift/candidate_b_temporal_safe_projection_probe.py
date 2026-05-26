"""Temporal-safe projection probe for Candidate B post-PPO repair candidates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.capability_step_temporal_sequence_objective import load_corpus
from autodrift.capability_step_temporal_sequence_update_probe import (
    changed_parameter_names,
    clone_state_dict,
    evaluate_state_exact,
    recurrent_logp_sums,
    tensors_from_corpus,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.exact_post_ppo_repair import (
    ExactRepairConfig,
    exact_loss_summary,
    load_repair_corpora,
)
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_BASE_CHECKPOINT = Path(
    "runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt"
)
DEFAULT_REPAIR_CANDIDATES: tuple[tuple[str, Path], ...] = (
    (
        "raw_conflict_s40",
        Path("runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/candidate_checkpoint.pt"),
    ),
    (
        "base_conflict_s40",
        Path("runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/candidate_checkpoint.pt"),
    ),
    (
        "line_conflict_s40",
        Path("runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/candidate_checkpoint.pt"),
    ),
)
DEFAULT_ALPHAS = (
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.60,
    0.75,
    1.00,
)
DEFAULT_TEMPORAL_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_TEMPORAL_BASE_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")
DEFAULT_M297_NPZ = Path("runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz")
DEFAULT_M270_NPZ = Path("runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz")
DEFAULT_M267_M264_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_M183_M170_CORPUS = Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")
DEFAULT_RUN_DIR = Path("runs/m1031_candidate_b_temporal_safe_projection_probe")
BASE_POLICY_LABEL = "candidate_b_base"


@dataclass(frozen=True)
class ProjectionCandidate:
    source_label: str
    alpha: float
    checkpoint: Path
    state: dict[str, torch.Tensor]

    @property
    def label(self) -> str:
        alpha_text = f"{self.alpha:g}".replace(".", "_")
        return f"m1031_{self.source_label}_a{alpha_text}"


def parse_alphas(text: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one alpha")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be in [0, 1]")
    return values


def parse_repair_candidates(text: str) -> tuple[tuple[str, Path], ...]:
    candidates: list[tuple[str, Path]] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise argparse.ArgumentTypeError("repair candidate specs must be LABEL=PATH")
        label, path_text = item.split("=", 1)
        label = label.strip()
        path_text = path_text.strip()
        if not label or not path_text:
            raise argparse.ArgumentTypeError("repair candidate specs must be LABEL=PATH")
        candidates.append((label, Path(path_text)))
    if not candidates:
        raise argparse.ArgumentTypeError("expected at least one repair candidate")
    return tuple(candidates)


def interpolate_full_state(
    base_state: dict[str, torch.Tensor],
    target_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    """Interpolate all floating tensors and preserve base non-floating tensors."""

    alpha_value = float(alpha)
    if alpha_value < 0.0 or alpha_value > 1.0:
        raise ValueError("alpha must be in [0, 1]")
    if set(base_state) != set(target_state):
        missing = sorted(set(base_state) - set(target_state))
        extra = sorted(set(target_state) - set(base_state))
        raise ValueError(f"state keys differ: missing={missing} extra={extra}")
    output: dict[str, torch.Tensor] = {}
    for name, base_tensor in base_state.items():
        target_tensor = target_state[name]
        if base_tensor.shape != target_tensor.shape:
            raise ValueError(f"state shape mismatch for {name!r}: {base_tensor.shape} vs {target_tensor.shape}")
        if torch.is_floating_point(base_tensor):
            if not torch.is_floating_point(target_tensor):
                raise ValueError(f"state dtype mismatch for floating tensor {name!r}")
            output[name] = base_tensor + alpha_value * (target_tensor - base_tensor)
        else:
            output[name] = base_tensor.clone()
    return output


def config_signature(model: ActorCritic, checkpoint: dict[str, Any]) -> dict[str, Any]:
    config = checkpoint.get("config", {})
    return {
        "obs_dim": int(model.obs_dim),
        "act_dim": int(model.act_dim),
        "actor_encoder": str(getattr(model, "actor_encoder", "")),
        "actor_history_length": int(getattr(model, "actor_history_length", 1)),
        "action_sequence_horizon": int(getattr(model, "action_sequence_horizon", 1)),
        "config_actor_encoder": str(config.get("actor_encoder", "")),
    }


def actor_inputs_changed(base_checkpoint: Path, candidate_checkpoint: Path) -> bool:
    base_model, base_data = load_actor_critic_checkpoint(base_checkpoint, device="cpu")
    candidate_model, candidate_data = load_actor_critic_checkpoint(candidate_checkpoint, device="cpu")
    return config_signature(base_model, base_data) != config_signature(candidate_model, candidate_data)


def _base_temporal_metrics(base_summary_path: Path) -> dict[str, float]:
    summary = read_json(base_summary_path)
    names = (
        "weighted_total_loss",
        "weighted_normal_sequence_nll",
        "weighted_temporal_preference_loss",
        "weighted_logp_gap_mean",
        "temporal_logp_gap_p10",
    )
    return {name: float(summary[name]) for name in names}


def _exact_temporal_rows(
    *,
    model: ActorCritic,
    base_checkpoint: Path,
    base_state: dict[str, torch.Tensor],
    base_source_checkpoint: dict[str, Any],
    candidates: list[ProjectionCandidate],
    temporal_corpus_path: Path,
    temporal_base_summary_path: Path,
    run_dir: Path,
    device: torch.device,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    corpus = load_corpus(temporal_corpus_path)
    tensors = tensors_from_corpus(corpus, device)
    model.load_state_dict({name: tensor.to(device=device) for name, tensor in base_state.items()})
    model.eval()
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(model, tensors, "normal_hidden").detach()
    base_metrics = _base_temporal_metrics(temporal_base_summary_path)
    checkpoint_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    checkpoint_dir = run_dir / "checkpoints"
    for rank, candidate in enumerate(candidates, start=1):
        model.load_state_dict({name: tensor.to(device=device) for name, tensor in candidate.state.items()})
        checkpoint_path = checkpoint_dir / f"{candidate.label}.pt"
        save_checkpoint_like(
            model=model,
            source_checkpoint=base_source_checkpoint,
            path=checkpoint_path,
            metadata={
                "run_type": "m1031_candidate_b_temporal_safe_projection_probe",
                "source_label": candidate.source_label,
                "source_checkpoint": candidate.checkpoint,
                "alpha": float(candidate.alpha),
                "base_checkpoint": base_checkpoint,
                "ppo_used": False,
                "promoted": False,
            },
        )
        changed = changed_parameter_names(base_state, candidate.state)
        exact = evaluate_state_exact(
            model=model,
            state=candidate.state,
            corpus=corpus,
            tensors=tensors,
            base_normal_logp=base_normal_logp,
            base_metrics=base_metrics,
            device=device,
            alpha=float(candidate.alpha),
            candidate=candidate.label,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        exact.update(
            {
                "rank": int(rank),
                "source_label": candidate.source_label,
                "source_checkpoint": str(candidate.checkpoint),
                "candidate_label": candidate.label,
                "checkpoint": str(checkpoint_path),
                "actor_inputs_changed": bool(actor_inputs_changed(base_checkpoint, checkpoint_path)),
                "changed_parameter_count": int(len(changed)),
                "changed_parameter_names": ";".join(changed),
            }
        )
        checkpoint_rows.append(
            {
                "source_label": candidate.source_label,
                "alpha": float(candidate.alpha),
                "candidate_label": candidate.label,
                "checkpoint": str(checkpoint_path),
            }
        )
        metric_rows.append(exact)
    return metric_rows, checkpoint_rows


def _exact_m297_m270_rows(
    *,
    model: ActorCritic,
    base_state: dict[str, torch.Tensor],
    metric_rows: list[dict[str, Any]],
    preference_npz: Path,
    outcome_npz: Path,
    device: torch.device,
    config: ExactRepairConfig,
) -> list[dict[str, Any]]:
    preference, outcome = load_repair_corpora(
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=device,
        obs_dim=int(model.obs_dim),
        hidden_size=int(model.actor_mean.in_features),
        act_dim=int(model.act_dim),
    )
    model.load_state_dict({name: tensor.to(device=device) for name, tensor in base_state.items()})
    base_summary = exact_loss_summary(
        label="candidate_b_base",
        checkpoint="candidate_b_base",
        model=model,
        preference=preference,
        outcome=outcome,
        config=config,
    )
    base_m297 = float(base_summary["exact_m297_loss"])
    base_m270 = float(base_summary["exact_m270_loss"])
    rows: list[dict[str, Any]] = []
    for row in metric_rows:
        checkpoint = Path(str(row["checkpoint"]))
        candidate_model, _ = load_actor_critic_checkpoint(checkpoint, device=str(device))
        summary = exact_loss_summary(
            label=str(row["candidate_label"]),
            checkpoint=checkpoint,
            model=candidate_model,
            preference=preference,
            outcome=outcome,
            config=config,
        )
        m297_delta = float(summary["exact_m297_loss"]) - base_m297
        m270_delta = float(summary["exact_m270_loss"]) - base_m270
        row.update(
            {
                "exact_m297_loss": float(summary["exact_m297_loss"]),
                "exact_m270_loss": float(summary["exact_m270_loss"]),
                "exact_m297_delta_vs_base": m297_delta,
                "exact_m270_delta_vs_base": m270_delta,
                "exact_m297_no_regression": bool(m297_delta <= float(config.exact_m297_tolerance)),
                "exact_m270_no_regression": bool(m270_delta <= float(config.exact_m270_tolerance)),
                "m297_m270_exact_pass": bool(
                    m297_delta <= float(config.exact_m297_tolerance)
                    and m270_delta <= float(config.exact_m270_tolerance)
                ),
                "movement_retained_pass": bool(
                    float(row["alpha"]) >= 0.10 or m297_delta <= -0.00005 or m270_delta <= -0.000002
                ),
                "base_m297_loss": base_m297,
                "base_m270_loss": base_m270,
            }
        )
        row["eligible_for_first_replay"] = bool(
            row["exact_gate_pass"]
            and row["m297_m270_exact_pass"]
            and row["movement_retained_pass"]
            and not row["actor_inputs_changed"]
        )
        rows.append(row)
    return rows


def select_projection_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = rank_projection_candidates(rows)
    return ranked[0] if ranked else None


def rank_projection_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [row for row in rows if bool(row.get("eligible_for_first_replay", False))]
    return sorted(
        eligible,
        key=lambda row: (
            -float(row["alpha"]),
            float(row["weighted_total_loss"]),
            float(row["exact_m297_loss"]),
            float(row["exact_m270_loss"]),
        ),
    )


def _row15_retained(replay_dir: Path, candidate_policy: str) -> bool:
    replay_rows_csv = replay_dir / "boundary_replay_rows.csv"
    if not replay_rows_csv.exists():
        return False
    frame = pd.read_csv(replay_rows_csv)
    rows = frame[
        frame["policy"].astype(str).eq(str(candidate_policy))
        & frame["row_id"].astype(int).eq(15)
    ]
    if rows.empty:
        return False
    return bool(rows["success_drop"].astype(bool).all() and (~rows["wrong_history_success"].astype(bool)).all())


def _run_first_replay(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    candidate_policy_label: str,
    env_config_path: Path,
    device: str,
    run_dir: Path,
    max_continuation_steps: int,
) -> tuple[list[dict[str, Any]], bool, bool, bool]:
    rows: list[dict[str, Any]] = []
    checkpoints = (
        CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
        CheckpointSpec(label=candidate_policy_label, path=candidate_checkpoint),
    )
    m267_dir = run_dir / "m267_m264"
    m267_summary = run_boundary_outcome_replay_gate(
        checkpoint_specs=checkpoints,
        corpus_csv=DEFAULT_M267_M264_CORPUS,
        env_config_path=env_config_path,
        max_rows=0,
        max_continuation_steps=max_continuation_steps,
        baseline_policy=BASE_POLICY_LABEL,
        candidate_policy=candidate_policy_label,
        max_normal_success_drop=0.0,
        max_normal_margin_regression=0.005,
        max_margin_gap_regression=0.001,
        max_success_drop_count_regression=0,
        device=device,
        run_dir=m267_dir,
    )
    row15_retained = _row15_retained(m267_dir, candidate_policy_label)
    m267_pass = bool(m267_summary["gate_pass"]) and row15_retained
    rows.append(
        {
            "surface": "m267_m264",
            "candidate_label": candidate_policy_label,
            "run_dir": str(m267_dir),
            "candidate_success_drop_count": int(m267_summary["candidate_success_drop_count"]),
            "baseline_success_drop_count": int(m267_summary["baseline_success_drop_count"]),
            "gate_pass": bool(m267_summary["gate_pass"]),
            "row15_retained": bool(row15_retained),
            "first_replay_pass": bool(m267_pass),
            "skipped_reason": "",
        }
    )
    m183_pass = False
    if m267_pass:
        m183_dir = run_dir / "m183_m170"
        m183_summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=checkpoints,
            corpus_csv=DEFAULT_M183_M170_CORPUS,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=candidate_policy_label,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=m183_dir,
        )
        m183_pass = bool(m183_summary["gate_pass"])
        rows.append(
            {
                "surface": "m183_m170",
                "candidate_label": candidate_policy_label,
                "run_dir": str(m183_dir),
                "candidate_success_drop_count": int(m183_summary["candidate_success_drop_count"]),
                "baseline_success_drop_count": int(m183_summary["baseline_success_drop_count"]),
                "gate_pass": bool(m183_summary["gate_pass"]),
                "row15_retained": "",
                "first_replay_pass": bool(m183_pass),
                "skipped_reason": "",
            }
        )
    else:
        rows.append(
            {
                "surface": "m183_m170",
                "candidate_label": candidate_policy_label,
                "run_dir": "",
                "candidate_success_drop_count": 0,
                "baseline_success_drop_count": 0,
                "gate_pass": False,
                "row15_retained": "",
                "first_replay_pass": False,
                "skipped_reason": "m267_m264_first_replay_failed",
            }
        )
    return rows, m267_pass, row15_retained, m183_pass


def classify_temporal_safe_projection(
    *,
    actor_inputs_changed: bool,
    temporal_exact_pass_count: int,
    temporal_and_exact_pass_count: int,
    eligible_candidate_count: int,
    selected_candidate: dict[str, Any] | None,
    m267_m264_pass: bool,
    row15_retained: bool,
    m183_m170_pass: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(actor_inputs_changed) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "candidate_b_temporal_safe_projection_contract_artifact"
    if int(temporal_exact_pass_count) <= 0:
        return "candidate_b_temporal_safe_projection_no_temporal_candidate"
    if int(temporal_and_exact_pass_count) <= 0:
        return "candidate_b_temporal_safe_projection_no_exact_candidate"
    if int(eligible_candidate_count) <= 0 or selected_candidate is None:
        return "candidate_b_temporal_safe_projection_base_equivalent"
    if not (bool(m267_m264_pass) and bool(row15_retained) and bool(m183_m170_pass)):
        return "candidate_b_temporal_safe_projection_proof_washout"
    return "candidate_b_temporal_safe_projection_first_replay_candidate"


def failure_types_for_temporal_safe_projection(result_class: str) -> list[str]:
    if result_class.endswith("_first_replay_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_base_equivalent"):
        return ["objective_overfit"]
    if result_class.endswith("_no_temporal_candidate") or result_class.endswith("_no_exact_candidate"):
        return ["proof_washout"]
    if result_class.endswith("_proof_washout"):
        return ["proof_washout"]
    return ["metric_artifact"]


def next_blocker_for_temporal_safe_projection(result_class: str) -> str:
    if result_class.endswith("_first_replay_candidate"):
        return "candidate_b_temporal_safe_projection_full_public_gate_design"
    if result_class.endswith("_no_temporal_candidate") or result_class.endswith("_base_equivalent"):
        return "candidate_b_direct_temporal_objective_integration_design"
    if result_class.endswith("_no_exact_candidate"):
        return "candidate_b_temporal_safe_projection_exact_failure_audit"
    if result_class.endswith("_proof_washout"):
        return "candidate_b_temporal_safe_projection_first_replay_failure_audit"
    return "candidate_b_temporal_safe_projection_contract_audit"


def _route_decision_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_class": str(summary["result_class"]),
        "selected_source_label": summary.get("selected_source_label"),
        "selected_alpha": summary.get("selected_alpha"),
        "selected_checkpoint": summary.get("selected_checkpoint"),
        "temporal_exact_pass_count": int(summary.get("temporal_exact_pass_count", 0)),
        "temporal_and_exact_pass_count": int(summary.get("temporal_and_exact_pass_count", 0)),
        "eligible_candidate_count": int(summary.get("eligible_candidate_count", 0)),
        "m267_m264_first_replay_pass": bool(summary.get("m267_m264_first_replay_pass", False)),
        "m267_m264_row15_retained": bool(summary.get("m267_m264_row15_retained", False)),
        "m183_m170_first_replay_pass": bool(summary.get("m183_m170_first_replay_pass", False)),
        "training_started": bool(summary.get("training_started", False)),
        "ppo_used": bool(summary.get("ppo_used", False)),
        "promoted": bool(summary.get("promoted", False)),
        "next_blocker": str(summary.get("next_blocker", "")),
    }


def run_temporal_safe_projection_probe(
    *,
    base_checkpoint: Path,
    repair_candidates: tuple[tuple[str, Path], ...],
    alphas: tuple[float, ...],
    temporal_corpus: Path,
    temporal_base_summary: Path,
    preference_npz: Path,
    outcome_npz: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path,
    max_continuation_steps: int,
    preference_margin: float = 0.05,
    lambda_pref: float = 1.0,
    lambda_anchor: float = 0.25,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, base_source_checkpoint = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    base_state = clone_state_dict(model)
    projected: list[ProjectionCandidate] = []
    for source_label, source_path in repair_candidates:
        source_model, _ = load_actor_critic_checkpoint(source_path, device=str(resolved_device))
        source_state = clone_state_dict(source_model)
        for alpha in alphas:
            projected.append(
                ProjectionCandidate(
                    source_label=source_label,
                    alpha=float(alpha),
                    checkpoint=source_path,
                    state=interpolate_full_state(base_state, source_state, float(alpha)),
                )
            )
    temporal_rows, checkpoint_rows = _exact_temporal_rows(
        model=model,
        base_checkpoint=base_checkpoint,
        base_state=base_state,
        base_source_checkpoint=base_source_checkpoint,
        candidates=projected,
        temporal_corpus_path=temporal_corpus,
        temporal_base_summary_path=temporal_base_summary,
        run_dir=run_dir,
        device=resolved_device,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    config = ExactRepairConfig()
    rows = _exact_m297_m270_rows(
        model=model,
        base_state=base_state,
        metric_rows=temporal_rows,
        preference_npz=preference_npz,
        outcome_npz=outcome_npz,
        device=resolved_device,
        config=config,
    )
    write_csv_rows(run_dir / "projection_metrics.csv", rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", checkpoint_rows)
    ranked_candidates = rank_projection_candidates(rows)
    selected = ranked_candidates[0] if ranked_candidates else None
    actor_input_change_count = sum(1 for row in rows if bool(row.get("actor_inputs_changed", False)))
    temporal_exact_pass_count = sum(1 for row in rows if bool(row.get("exact_gate_pass", False)))
    temporal_and_exact_pass_count = sum(
        1 for row in rows if bool(row.get("exact_gate_pass", False)) and bool(row.get("m297_m270_exact_pass", False))
    )
    eligible_count = sum(1 for row in rows if bool(row.get("eligible_for_first_replay", False)))
    replay_rows: list[dict[str, Any]] = []
    m267_pass = False
    row15_retained = False
    m183_pass = False
    attempted_candidate_count = 0
    first_replay_pass_candidate: dict[str, Any] | None = None
    if ranked_candidates:
        for attempt in ranked_candidates:
            attempted_candidate_count += 1
            attempt_label = str(attempt["candidate_label"])
            attempt_rows, attempt_m267_pass, attempt_row15_retained, attempt_m183_pass = _run_first_replay(
                base_checkpoint=base_checkpoint,
                candidate_checkpoint=Path(str(attempt["checkpoint"])),
                candidate_policy_label=attempt_label,
                env_config_path=env_config_path,
                device=device,
                run_dir=run_dir / "first_replay" / attempt_label,
                max_continuation_steps=max_continuation_steps,
            )
            replay_rows.extend(attempt_rows)
            if attempt_m267_pass and attempt_row15_retained and attempt_m183_pass:
                selected = attempt
                first_replay_pass_candidate = attempt
                m267_pass = attempt_m267_pass
                row15_retained = attempt_row15_retained
                m183_pass = attempt_m183_pass
                break
        if first_replay_pass_candidate is None:
            selected = ranked_candidates[0]
    else:
        replay_rows = [
            {
                "surface": "m267_m264",
                "candidate_label": "",
                "run_dir": "",
                "candidate_success_drop_count": 0,
                "baseline_success_drop_count": 0,
                "gate_pass": False,
                "row15_retained": False,
                "first_replay_pass": False,
                "skipped_reason": "no_eligible_projection_candidate",
            },
            {
                "surface": "m183_m170",
                "candidate_label": "",
                "run_dir": "",
                "candidate_success_drop_count": 0,
                "baseline_success_drop_count": 0,
                "gate_pass": False,
                "row15_retained": "",
                "first_replay_pass": False,
                "skipped_reason": "no_eligible_projection_candidate",
            },
        ]
    result_class = classify_temporal_safe_projection(
        actor_inputs_changed=bool(actor_input_change_count),
        temporal_exact_pass_count=temporal_exact_pass_count,
        temporal_and_exact_pass_count=temporal_and_exact_pass_count,
        eligible_candidate_count=eligible_count,
        selected_candidate=selected,
        m267_m264_pass=m267_pass,
        row15_retained=row15_retained,
        m183_m170_pass=m183_pass,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "candidate_b_temporal_safe_projection_probe",
        "base_checkpoint": base_checkpoint,
        "repair_candidates": [{"label": label, "checkpoint": path} for label, path in repair_candidates],
        "alphas": list(alphas),
        "temporal_corpus": temporal_corpus,
        "temporal_base_summary": temporal_base_summary,
        "preference_npz": preference_npz,
        "outcome_npz": outcome_npz,
        "env_config": env_config_path,
        "max_continuation_steps": int(max_continuation_steps),
        "candidate_count": int(len(rows)),
        "actor_input_change_count": int(actor_input_change_count),
        "temporal_exact_pass_count": int(temporal_exact_pass_count),
        "temporal_and_exact_pass_count": int(temporal_and_exact_pass_count),
        "eligible_candidate_count": int(eligible_count),
        "selected_candidate_label": selected.get("candidate_label") if selected is not None else None,
        "selected_source_label": selected.get("source_label") if selected is not None else None,
        "selected_alpha": float(selected["alpha"]) if selected is not None else None,
        "selected_checkpoint": selected.get("checkpoint") if selected is not None else None,
        "m267_m264_first_replay_pass": bool(m267_pass),
        "m267_m264_row15_retained": bool(row15_retained),
        "m183_m170_first_replay_pass": bool(m183_pass),
        "first_replay_attempted": bool(attempted_candidate_count > 0),
        "first_replay_attempted_candidate_count": int(attempted_candidate_count),
        "first_replay_pass_candidate_found": bool(first_replay_pass_candidate is not None),
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "checkpoint_promoted": False,
        "private_holdout_used": False,
        "result_class": result_class,
        "failure_types": failure_types_for_temporal_safe_projection(result_class),
        "next_blocker": next_blocker_for_temporal_safe_projection(result_class),
        "projection_metrics_csv": run_dir / "projection_metrics.csv",
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
        "first_replay_summary_csv": run_dir / "first_replay_summary.csv",
        "route_decision_csv": run_dir / "route_decision.csv",
        "summary_json": run_dir / "summary.json",
    }
    write_csv_rows(run_dir / "first_replay_summary.csv", replay_rows)
    write_csv_rows(run_dir / "route_decision.csv", [_route_decision_row(summary)])
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Candidate B temporal-safe projection probe.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument(
        "--repair-candidates",
        type=parse_repair_candidates,
        default=DEFAULT_REPAIR_CANDIDATES,
        help="Comma-separated LABEL=PATH repair candidates.",
    )
    parser.add_argument("--alphas", type=parse_alphas, default=DEFAULT_ALPHAS)
    parser.add_argument("--temporal-corpus", type=Path, default=DEFAULT_TEMPORAL_CORPUS)
    parser.add_argument("--temporal-base-summary", type=Path, default=DEFAULT_TEMPORAL_BASE_SUMMARY)
    parser.add_argument("--preference-npz", type=Path, default=DEFAULT_M297_NPZ)
    parser.add_argument("--outcome-npz", type=Path, default=DEFAULT_M270_NPZ)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    summary = run_temporal_safe_projection_probe(
        base_checkpoint=args.base_checkpoint,
        repair_candidates=args.repair_candidates,
        alphas=args.alphas,
        temporal_corpus=args.temporal_corpus,
        temporal_base_summary=args.temporal_base_summary,
        preference_npz=args.preference_npz,
        outcome_npz=args.outcome_npz,
        run_dir=args.run_dir,
        device=args.device,
        env_config_path=args.env_config,
        max_continuation_steps=args.max_continuation_steps,
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(f"result_class={summary['result_class']}")
    print(f"temporal_exact_pass_count={summary['temporal_exact_pass_count']}")
    print(f"temporal_and_exact_pass_count={summary['temporal_and_exact_pass_count']}")
    print(f"eligible_candidate_count={summary['eligible_candidate_count']}")
    print(f"selected_checkpoint={summary['selected_checkpoint']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
