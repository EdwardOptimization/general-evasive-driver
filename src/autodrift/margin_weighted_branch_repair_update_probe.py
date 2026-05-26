"""Actor-mean-only temporal repair update with margin-weighted branch trust."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.branch_preserving_temporal_repair_evaluator import (
    DEFAULT_ACTIVE_ROWS,
    DEFAULT_M267_CORPUS,
    EvaluatedCheckpoint,
    build_branch_examples,
)
from autodrift.capability_step_temporal_sequence_objective import load_corpus
from autodrift.capability_step_temporal_sequence_update_probe import (
    ACTOR_MEAN_PREFIX,
    DEFAULT_ALPHAS,
    changed_parameter_names,
    clone_state_dict,
    differentiable_temporal_loss,
    evaluate_state_exact,
    interpolate_actor_mean_state,
    parse_alphas,
    recurrent_logp_sums,
    set_actor_mean_trainable_only,
    state_checksum,
    tensors_from_corpus,
    _save_checkpoint,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.margin_weighted_branch_trust_region_evaluator import (
    DEFAULT_MARGIN_FLOOR,
    DEFAULT_M1004_REPLAY_ROWS,
    evaluate_margin_weighted_trust_for_checkpoint,
    load_base_wrong_margins,
    margin_slack,
    source_normalized_weight,
)
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_CHECKPOINT = Path("runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt")
DEFAULT_CORPUS = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz")
DEFAULT_METADATA = Path("runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv")
DEFAULT_BASE_SUMMARY = Path("runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json")
DEFAULT_RUN_DIR = Path("runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe")
DEFAULT_REPAIR_ALPHAS = (0.0025, *DEFAULT_ALPHAS)
DEFAULT_LAMBDA_WRONG_TRUST_VALUES = (0.001, 0.003, 0.01, 0.03)
DEFAULT_BRANCH_TRUST_GATE = 0.10
DEFAULT_PRIMARY_BRANCH_TRUST_GATE = 0.07
DEFAULT_MAX_ROW_CONTRIBUTION_GATE = 0.05
DEFAULT_ROW6_CONTRIBUTION_GATE = 0.05
DEFAULT_ROW15_CONTRIBUTION_GATE = 0.02
DEFAULT_ROW16_CONTRIBUTION_GATE = 0.05


def parse_float_list(text: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one float")
    if any(value <= 0.0 for value in values):
        raise argparse.ArgumentTypeError("values must be positive")
    return values


def _lambda_token(value: float) -> str:
    return str(float(value)).replace(".", "_").replace("-", "neg_")


def branch_trust_tensors_from_examples(
    *,
    examples: list[Any],
    base_wrong_margins: dict[int, float],
    margin_floor: float,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    total_source_weight = float(sum(float(example.weight) for example in examples))
    weights: list[float] = []
    row_ids: list[int] = []
    margins: list[float] = []
    slacks: list[float] = []
    for example in examples:
        row_id = int(example.row_id)
        slack = margin_slack(float(base_wrong_margins[row_id]), margin_floor=margin_floor)
        weights.append(source_normalized_weight(row_id, total_source_weight) / (slack * slack))
        row_ids.append(row_id)
        margins.append(float(base_wrong_margins[row_id]))
        slacks.append(slack)
    return {
        "obs": torch.as_tensor(
            np.stack([np.asarray(example.observation, dtype=np.float32) for example in examples], axis=0),
            dtype=torch.float32,
            device=device,
        ),
        "wrong_hidden": torch.stack(
            [example.wrong_hidden.detach().to(device=device, dtype=torch.float32).reshape(-1) for example in examples],
            dim=0,
        ),
        "base_wrong_action": torch.as_tensor(
            np.stack([np.asarray(example.base_wrong_action, dtype=np.float32) for example in examples], axis=0),
            dtype=torch.float32,
            device=device,
        ),
        "weights": torch.as_tensor(weights, dtype=torch.float32, device=device),
        "row_ids": torch.as_tensor(row_ids, dtype=torch.long, device=device),
        "base_wrong_margin": torch.as_tensor(margins, dtype=torch.float32, device=device),
        "margin_slack": torch.as_tensor(slacks, dtype=torch.float32, device=device),
    }


def differentiable_branch_trust_loss(
    model: ActorCritic,
    branch_tensors: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    features, _next_hidden = model.recurrent_features_tensor(branch_tensors["obs"], branch_tensors["wrong_hidden"])
    action = torch.tanh(model.actor_mean(features))
    delta_sq = torch.sum(torch.square(action - branch_tensors["base_wrong_action"]), dim=1)
    contributions = branch_tensors["weights"] * delta_sq
    row_ids = branch_tensors["row_ids"]
    primary_mask = (row_ids == 6) | (row_ids == 15)
    total = torch.sum(contributions)
    row_metric_values: dict[str, torch.Tensor] = {}
    for row_id in (6, 11, 15, 16):
        row_mask = row_ids == int(row_id)
        row_metric_values[f"row_{row_id}_contribution"] = torch.sum(contributions[row_mask])
    return total, {
        "weighted_branch_trust_loss": total.detach(),
        "primary_weighted_branch_trust_loss": torch.sum(contributions[primary_mask]).detach(),
        "max_weighted_row_contribution": torch.max(contributions).detach(),
        **{name: value.detach() for name, value in row_metric_values.items()},
    }


def train_actor_mean_repair_update(
    *,
    model: ActorCritic,
    temporal_tensors: dict[str, torch.Tensor],
    branch_tensors: dict[str, torch.Tensor],
    base_normal_logp: torch.Tensor,
    epochs: int,
    lr: float,
    seed: int,
    grad_clip_norm: float,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
    lambda_wrong_trust: float,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    set_actor_mean_trainable_only(model)
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    rows: list[dict[str, Any]] = []
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad(set_to_none=True)
        temporal_loss, temporal_metrics = differentiable_temporal_loss(
            model,
            temporal_tensors,
            base_normal_logp=base_normal_logp,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        branch_loss, branch_metrics = differentiable_branch_trust_loss(model, branch_tensors)
        loss = temporal_loss + float(lambda_wrong_trust) * branch_loss
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite M1013 loss at epoch {epoch}: {float(loss.detach().cpu())}")
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.actor_mean.parameters(), float(grad_clip_norm)).detach().cpu().item())
        optimizer.step()
        if epoch == 1 or epoch == int(epochs) or epoch % max(1, int(epochs) // 20) == 0:
            rows.append(
                {
                    "epoch": int(epoch),
                    "lambda_wrong_trust": float(lambda_wrong_trust),
                    "loss": float(loss.detach().cpu().item()),
                    "temporal_loss": float(temporal_loss.detach().cpu().item()),
                    "branch_loss": float(branch_loss.detach().cpu().item()),
                    "grad_norm": grad_norm,
                    **{name: float(value.cpu().item()) for name, value in temporal_metrics.items()},
                    **{name: float(value.cpu().item()) for name, value in branch_metrics.items()},
                }
            )
    return rows


def _branch_gate_flags(
    row: dict[str, Any],
    *,
    branch_trust_gate: float,
    primary_branch_trust_gate: float,
    max_row_contribution_gate: float,
    row6_contribution_gate: float,
    row15_contribution_gate: float,
    row16_contribution_gate: float,
) -> dict[str, Any]:
    flags = {
        "branch_trust_pass": bool(float(row["weighted_branch_trust_loss"]) <= float(branch_trust_gate)),
        "primary_branch_trust_pass": bool(float(row["primary_weighted_branch_trust_loss"]) <= float(primary_branch_trust_gate)),
        "max_row_contribution_pass": bool(float(row["max_weighted_row_contribution"]) <= float(max_row_contribution_gate)),
        "row_6_contribution_pass": bool(float(row.get("row_6_contribution", 0.0)) <= float(row6_contribution_gate)),
        "row_15_contribution_pass": bool(float(row.get("row_15_contribution", 0.0)) <= float(row15_contribution_gate)),
        "row_16_contribution_pass": bool(float(row.get("row_16_contribution", 0.0)) <= float(row16_contribution_gate)),
    }
    flags["branch_gate_pass"] = bool(all(flags.values()))
    return flags


def classify_repair_update_probe(
    *,
    raw_actor_mean_changed: bool,
    raw_non_actor_changed: bool,
    exact_candidate_count: int,
    branch_candidate_count: int,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if bool(raw_non_actor_changed) or not bool(raw_actor_mean_changed):
        return "margin_weighted_branch_repair_update_contract_artifact"
    if not bool(training_started) or bool(ppo_used) or bool(promoted):
        return "margin_weighted_branch_repair_update_contract_artifact"
    if int(exact_candidate_count) <= 0:
        return "margin_weighted_branch_repair_update_no_exact_candidate"
    if int(branch_candidate_count) <= 0:
        return "margin_weighted_branch_repair_update_branch_trust_blocked"
    return "margin_weighted_branch_repair_update_exact_branch_candidate"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_exact_branch_candidate"):
        return ["none"]
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_no_exact_candidate"):
        return ["objective_overfit"]
    if result_class.endswith("_branch_trust_blocked"):
        return ["proof_washout"]
    return ["objective_overfit"]


def _base_metrics_from_summary(base_summary_path: Path) -> dict[str, float]:
    base_summary = pd.read_json(base_summary_path, typ="series")
    return {
        "weighted_total_loss": float(base_summary["weighted_total_loss"]),
        "weighted_normal_sequence_nll": float(base_summary["weighted_normal_sequence_nll"]),
        "weighted_temporal_preference_loss": float(base_summary["weighted_temporal_preference_loss"]),
        "weighted_logp_gap_mean": float(base_summary["weighted_logp_gap_mean"]),
        "temporal_logp_gap_p10": float(base_summary["temporal_logp_gap_p10"]),
    }


def run_margin_weighted_branch_repair_update_probe(
    *,
    checkpoint_path: Path,
    corpus_path: Path,
    metadata_path: Path,
    base_summary_path: Path,
    m267_corpus_csv: Path,
    m1004_replay_rows_csv: Path,
    run_dir: Path,
    device: str,
    env_config_path: Path,
    active_rows: tuple[int, ...],
    max_continuation_steps: int,
    margin_floor: float,
    epochs: int,
    seed: int,
    lr: float,
    grad_clip_norm: float,
    alphas: tuple[float, ...],
    lambda_wrong_trust_values: tuple[float, ...],
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
    branch_trust_gate: float,
    primary_branch_trust_gate: float,
    max_row_contribution_gate: float,
    row6_contribution_gate: float,
    row15_contribution_gate: float,
    row16_contribution_gate: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    corpus = load_corpus(corpus_path)
    metadata = pd.read_csv(metadata_path)
    temporal_tensors = tensors_from_corpus(corpus, resolved_device)
    base_state = clone_state_dict(model)
    base_checksum = state_checksum(base_state)
    base_non_actor_checksum = state_checksum(base_state, exclude_actor_mean=True)
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(model, temporal_tensors, "normal_hidden").detach()
    base_metrics = _base_metrics_from_summary(base_summary_path)
    examples, branch_example_rows = build_branch_examples(
        base_model=model,
        m267_corpus_csv=m267_corpus_csv,
        env_config_path=env_config_path,
        active_rows=active_rows,
        max_continuation_steps=max_continuation_steps,
        device=resolved_device,
        epsilon_logp=0.0,
        d_min_fraction=0.0,
        d_min_absolute=0.0,
    )
    base_wrong_margins = load_base_wrong_margins(m1004_replay_rows_csv, active_rows=active_rows, base_policy="m974_base")
    branch_tensors = branch_trust_tensors_from_examples(
        examples=examples,
        base_wrong_margins=base_wrong_margins,
        margin_floor=margin_floor,
        device=resolved_device,
    )
    train_rows: list[dict[str, Any]] = []
    interpolation_rows: list[dict[str, Any]] = []
    branch_rows: list[dict[str, Any]] = []
    candidate_checkpoint_rows: list[dict[str, Any]] = []
    raw_checkpoint_rows: list[dict[str, Any]] = []
    raw_changed_union: set[str] = set()
    raw_non_actor_changed = False
    raw_actor_mean_changed = False
    checkpoint_dir = run_dir / "checkpoints"

    for lambda_wrong_trust in lambda_wrong_trust_values:
        model.load_state_dict({name: tensor.to(device=resolved_device) for name, tensor in base_state.items()})
        model.train()
        lambda_rows = train_actor_mean_repair_update(
            model=model,
            temporal_tensors=temporal_tensors,
            branch_tensors=branch_tensors,
            base_normal_logp=base_normal_logp,
            epochs=epochs,
            lr=lr,
            seed=seed,
            grad_clip_norm=grad_clip_norm,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
            lambda_wrong_trust=float(lambda_wrong_trust),
        )
        train_rows.extend(lambda_rows)
        raw_state = clone_state_dict(model)
        raw_changed = changed_parameter_names(base_state, raw_state)
        raw_changed_union.update(raw_changed)
        raw_actor_mean_changed = bool(raw_actor_mean_changed or any(name.startswith(ACTOR_MEAN_PREFIX) for name in raw_changed))
        raw_lambda_non_actor_changed = bool(base_non_actor_checksum != state_checksum(raw_state, exclude_actor_mean=True))
        raw_non_actor_changed = bool(raw_non_actor_changed or raw_lambda_non_actor_changed)
        lambda_dir = checkpoint_dir / f"lambda_{_lambda_token(float(lambda_wrong_trust))}"
        raw_checkpoint = lambda_dir / "raw_actor_mean_update.pt"
        _save_checkpoint(
            checkpoint_data=checkpoint_data,
            state_dict=raw_state,
            destination=raw_checkpoint,
            objective="margin_weighted_branch_repair_update_probe_raw",
        )
        raw_checkpoint_rows.append(
            {
                "lambda_wrong_trust": float(lambda_wrong_trust),
                "checkpoint": raw_checkpoint,
                "changed_parameter_names": ";".join(raw_changed),
                "raw_non_actor_changed": raw_lambda_non_actor_changed,
            }
        )
        for alpha in alphas:
            candidate_state = interpolate_actor_mean_state(base_state, raw_state, float(alpha))
            candidate_label = f"lambda_{_lambda_token(float(lambda_wrong_trust))}_alpha_{str(float(alpha)).replace('.', '_')}"
            candidate_path = lambda_dir / f"alpha_{str(float(alpha)).replace('.', '_')}.pt"
            temporal_row = evaluate_state_exact(
                model=model,
                state=candidate_state,
                corpus=corpus,
                tensors=temporal_tensors,
                base_normal_logp=base_normal_logp,
                base_metrics=base_metrics,
                device=resolved_device,
                alpha=float(alpha),
                candidate="interpolation",
                preference_margin=preference_margin,
                lambda_pref=lambda_pref,
                lambda_anchor=lambda_anchor,
            )
            branch_summary, per_branch_rows = evaluate_margin_weighted_trust_for_checkpoint(
                model=model,
                checkpoint=EvaluatedCheckpoint(label=candidate_label, path=candidate_path, alpha=float(alpha)),
                examples=examples,
                base_wrong_margins=base_wrong_margins,
                margin_floor=margin_floor,
                device=resolved_device,
            )
            row_contributions = {
                f"row_{int(row['row_id'])}_contribution": float(row["weighted_trust_contribution"])
                for row in per_branch_rows
            }
            combined = {
                **temporal_row,
                "lambda_wrong_trust": float(lambda_wrong_trust),
                "checkpoint_label": candidate_label,
                "checkpoint": candidate_path,
                "weighted_branch_trust_loss": float(branch_summary["weighted_branch_trust_loss"]),
                "primary_weighted_branch_trust_loss": float(branch_summary["primary_weighted_branch_trust_loss"]),
                "primary_contribution_fraction": float(branch_summary["primary_contribution_fraction"]),
                "max_weighted_row_contribution": float(branch_summary["weighted_trust_contribution_max"]),
                **row_contributions,
            }
            combined.update(
                _branch_gate_flags(
                    combined,
                    branch_trust_gate=branch_trust_gate,
                    primary_branch_trust_gate=primary_branch_trust_gate,
                    max_row_contribution_gate=max_row_contribution_gate,
                    row6_contribution_gate=row6_contribution_gate,
                    row15_contribution_gate=row15_contribution_gate,
                    row16_contribution_gate=row16_contribution_gate,
                )
            )
            combined["exact_and_branch_gate_pass"] = bool(combined["exact_gate_pass"] and combined["branch_gate_pass"])
            interpolation_rows.append(combined)
            branch_rows.extend(
                {
                    **row,
                    "lambda_wrong_trust": float(lambda_wrong_trust),
                    "candidate_label": candidate_label,
                }
                for row in per_branch_rows
            )
            if bool(combined["exact_and_branch_gate_pass"]):
                _save_checkpoint(
                    checkpoint_data=checkpoint_data,
                    state_dict=candidate_state,
                    destination=candidate_path,
                    objective="margin_weighted_branch_repair_update_probe_candidate",
                )
                candidate_checkpoint_rows.append(
                    {
                        "lambda_wrong_trust": float(lambda_wrong_trust),
                        "alpha": float(alpha),
                        "checkpoint": candidate_path,
                        "weighted_total_loss": float(combined["weighted_total_loss"]),
                        "weighted_branch_trust_loss": float(combined["weighted_branch_trust_loss"]),
                    }
                )

    exact_rows = [row for row in interpolation_rows if bool(row["exact_gate_pass"])]
    joint_rows = [row for row in interpolation_rows if bool(row["exact_and_branch_gate_pass"])]
    best_candidate = (
        sorted(
            joint_rows,
            key=lambda row: (
                float(row["weighted_total_loss"]),
                float(row["weighted_branch_trust_loss"]),
                float(row["candidate_action_l2_mean"]),
            ),
        )[0]
        if joint_rows
        else {}
    )
    result_class = classify_repair_update_probe(
        raw_actor_mean_changed=raw_actor_mean_changed,
        raw_non_actor_changed=raw_non_actor_changed,
        exact_candidate_count=len(exact_rows),
        branch_candidate_count=len(joint_rows),
        training_started=True,
        ppo_used=False,
        promoted=False,
    )
    write_csv_rows(run_dir / "branch_examples.csv", branch_example_rows)
    write_csv_rows(run_dir / "train_history.csv", train_rows)
    write_csv_rows(run_dir / "interpolation_metrics.csv", interpolation_rows)
    write_csv_rows(run_dir / "branch_metric_rows.csv", branch_rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", candidate_checkpoint_rows)
    write_csv_rows(run_dir / "raw_checkpoints.csv", raw_checkpoint_rows)
    summary = {
        "run_type": "margin_weighted_branch_repair_update_probe",
        "checkpoint": checkpoint_path,
        "corpus": corpus_path,
        "metadata": metadata_path,
        "base_summary": base_summary_path,
        "m267_corpus": m267_corpus_csv,
        "m1004_replay_rows": m1004_replay_rows_csv,
        "row_count": int(corpus["sequence_mask"].shape[0]),
        "positive_row_count": int(metadata["positive_target"].astype(bool).sum()) if "positive_target" in metadata else int(len(metadata)),
        "branch_row_count": int(len(examples)),
        "active_rows": list(active_rows),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "grad_clip_norm": float(grad_clip_norm),
        "interpolation_alphas": list(alphas),
        "lambda_wrong_trust_values": list(lambda_wrong_trust_values),
        "preference_margin": float(preference_margin),
        "lambda_pref": float(lambda_pref),
        "lambda_anchor": float(lambda_anchor),
        "margin_floor": float(margin_floor),
        "branch_trust_gate": float(branch_trust_gate),
        "primary_branch_trust_gate": float(primary_branch_trust_gate),
        "max_row_contribution_gate": float(max_row_contribution_gate),
        "row6_contribution_gate": float(row6_contribution_gate),
        "row15_contribution_gate": float(row15_contribution_gate),
        "row16_contribution_gate": float(row16_contribution_gate),
        "base_checksum": base_checksum,
        "raw_changed_parameter_names": sorted(raw_changed_union),
        "raw_actor_mean_changed": bool(raw_actor_mean_changed),
        "raw_non_actor_changed": bool(raw_non_actor_changed),
        "exact_candidate_count": int(len(exact_rows)),
        "exact_and_branch_candidate_count": int(len(joint_rows)),
        "best_candidate": best_candidate,
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "candidate_checkpoints": candidate_checkpoint_rows,
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
        "train_history_csv": run_dir / "train_history.csv",
        "interpolation_metrics_csv": run_dir / "interpolation_metrics.csv",
        "branch_metric_rows_csv": run_dir / "branch_metric_rows.csv",
        "raw_checkpoints_csv": run_dir / "raw_checkpoints.csv",
        "training_started": True,
        "optimizer_started": True,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "next_blocker": (
            "M267/M264 repaired candidate preflight design"
            if result_class.endswith("_exact_branch_candidate")
            else "margin-weighted branch repair update audit"
        ),
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    if raw_non_actor_changed:
        raise RuntimeError(f"M1013 changed non-actor_mean parameters: {sorted(raw_changed_union)}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run margin-weighted branch repair actor_mean update probe.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--base-summary", type=Path, default=DEFAULT_BASE_SUMMARY)
    parser.add_argument("--m267-corpus", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--m1004-replay-rows", type=Path, default=DEFAULT_M1004_REPLAY_ROWS)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--active-rows", type=parse_alphas, default=",".join(str(row) for row in DEFAULT_ACTIVE_ROWS))
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--margin-floor", type=float, default=DEFAULT_MARGIN_FLOOR)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=1013)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--alphas", type=parse_alphas, default=",".join(str(alpha) for alpha in DEFAULT_REPAIR_ALPHAS))
    parser.add_argument(
        "--lambda-wrong-trust-values",
        type=parse_float_list,
        default=",".join(str(value) for value in DEFAULT_LAMBDA_WRONG_TRUST_VALUES),
    )
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    parser.add_argument("--branch-trust-gate", type=float, default=DEFAULT_BRANCH_TRUST_GATE)
    parser.add_argument("--primary-branch-trust-gate", type=float, default=DEFAULT_PRIMARY_BRANCH_TRUST_GATE)
    parser.add_argument("--max-row-contribution-gate", type=float, default=DEFAULT_MAX_ROW_CONTRIBUTION_GATE)
    parser.add_argument("--row6-contribution-gate", type=float, default=DEFAULT_ROW6_CONTRIBUTION_GATE)
    parser.add_argument("--row15-contribution-gate", type=float, default=DEFAULT_ROW15_CONTRIBUTION_GATE)
    parser.add_argument("--row16-contribution-gate", type=float, default=DEFAULT_ROW16_CONTRIBUTION_GATE)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="margin_weighted_branch_repair_update_probe")
    summary = run_margin_weighted_branch_repair_update_probe(
        checkpoint_path=args.checkpoint,
        corpus_path=args.corpus,
        metadata_path=args.metadata,
        base_summary_path=args.base_summary,
        m267_corpus_csv=args.m267_corpus,
        m1004_replay_rows_csv=args.m1004_replay_rows,
        run_dir=run_dir,
        device=args.device,
        env_config_path=args.env_config,
        active_rows=tuple(int(value) for value in args.active_rows),
        max_continuation_steps=args.max_continuation_steps,
        margin_floor=args.margin_floor,
        epochs=args.epochs,
        seed=args.seed,
        lr=args.lr,
        grad_clip_norm=args.grad_clip_norm,
        alphas=tuple(args.alphas),
        lambda_wrong_trust_values=tuple(args.lambda_wrong_trust_values),
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
        branch_trust_gate=args.branch_trust_gate,
        primary_branch_trust_gate=args.primary_branch_trust_gate,
        max_row_contribution_gate=args.max_row_contribution_gate,
        row6_contribution_gate=args.row6_contribution_gate,
        row15_contribution_gate=args.row15_contribution_gate,
        row16_contribution_gate=args.row16_contribution_gate,
    )
    print(f"result_class={summary['result_class']}")
    print(f"exact_candidate_count={summary['exact_candidate_count']}")
    print(f"exact_and_branch_candidate_count={summary['exact_and_branch_candidate_count']}")
    print(f"raw_changed_parameter_names={summary['raw_changed_parameter_names']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
