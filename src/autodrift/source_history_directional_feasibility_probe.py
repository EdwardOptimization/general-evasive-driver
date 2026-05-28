"""Actor-mean-only directional feasibility probe for source-history rows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_history_objective_update import (
    SourceHistoryBatch,
    _clone_state_dict,
    _load_source_history_batch,
    _parameter_counts,
    _save_checkpoint,
    _set_actor_mean_trainable_only,
    _state_delta,
)
from autodrift.source_history_policy_gate import (
    _checkpoint_contract,
    _read_csv,
)
from autodrift.train_ppo import ActorCritic, resolve_device


@dataclass(frozen=True)
class DirectionalEval:
    loss: torch.Tensor
    correct_loss: torch.Tensor
    wrong_loss: torch.Tensor
    min_loss: torch.Tensor
    correct_margin: torch.Tensor
    wrong_margin: torch.Tensor
    min_margin: torch.Tensor


def _source_history_meta_rows(history_run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _read_csv(history_run_dir / "history_intervention_rows.csv"):
        rows.append(
            {
                "history_intervention_id": int(float(row["history_intervention_id"])),
                "intervention_id": int(float(row["intervention_id"])),
                "pair_id": int(float(row["pair_id"])),
                "condition": str(row["condition"]),
                "probe_template": str(row["probe_template"]),
                "correct_history_id": int(float(row["correct_history_id"])),
            }
        )
    return rows


def _directional_eval(
    model: ActorCritic,
    batch: SourceHistoryBatch,
    *,
    target_margin: float,
    lambda_min: float,
) -> DirectionalEval:
    dist_correct, _value_correct, _next_correct = model.forward_recurrent(batch.observations, batch.correct_hidden)
    dist_wrong, _value_wrong, _next_wrong = model.forward_recurrent(batch.observations, batch.wrong_hidden)
    logp_cp = dist_correct.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_cr = dist_correct.log_prob(batch.rejected_actions).sum(dim=-1)
    logp_wp = dist_wrong.log_prob(batch.preferred_actions).sum(dim=-1)
    logp_wr = dist_wrong.log_prob(batch.rejected_actions).sum(dim=-1)
    correct_margin = logp_cp - logp_cr
    wrong_margin = logp_wr - logp_wp
    min_margin = torch.minimum(correct_margin, wrong_margin)
    correct_loss = torch.nn.functional.softplus(float(target_margin) - correct_margin)
    wrong_loss = torch.nn.functional.softplus(float(target_margin) - wrong_margin)
    min_loss = torch.nn.functional.softplus(float(target_margin) - min_margin)
    loss = correct_loss.mean() + wrong_loss.mean() + float(lambda_min) * min_loss.mean()
    return DirectionalEval(
        loss=loss,
        correct_loss=correct_loss.mean(),
        wrong_loss=wrong_loss.mean(),
        min_loss=min_loss.mean(),
        correct_margin=correct_margin,
        wrong_margin=wrong_margin,
        min_margin=min_margin,
    )


def _actor_mean_anchor_loss(model: ActorCritic, anchor_state: dict[str, torch.Tensor], device: torch.device) -> torch.Tensor:
    loss = torch.zeros((), dtype=torch.float32, device=device)
    count = 0
    for name, parameter in model.actor_mean.named_parameters():
        key = f"actor_mean.{name}"
        loss = loss + torch.mean((parameter - anchor_state[key].to(device=device, dtype=torch.float32)).pow(2))
        count += 1
    return loss / max(count, 1)


def _directional_rows(
    *,
    meta_rows: list[dict[str, Any]],
    evaluation: DirectionalEval,
    init_name: str,
) -> list[dict[str, Any]]:
    correct = evaluation.correct_margin.detach().cpu().numpy().astype(np.float64)
    wrong = evaluation.wrong_margin.detach().cpu().numpy().astype(np.float64)
    minimum = evaluation.min_margin.detach().cpu().numpy().astype(np.float64)
    rows: list[dict[str, Any]] = []
    for index, meta in enumerate(meta_rows):
        correct_positive = bool(correct[index] > 0.0)
        wrong_positive = bool(wrong[index] > 0.0)
        rows.append(
            {
                **meta,
                "init_name": init_name,
                "correct_preference_margin": float(correct[index]),
                "wrong_history_preference_margin": float(wrong[index]),
                "min_preference_margin": float(minimum[index]),
                "correct_positive": correct_positive,
                "wrong_history_positive": wrong_positive,
                "both_positive": bool(correct_positive and wrong_positive),
                "mutually_exclusive": bool(correct_positive != wrong_positive),
            }
        )
    return rows


def _summarize_directional_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    correct_positive_count = sum(bool(row["correct_positive"]) for row in rows)
    wrong_positive_count = sum(bool(row["wrong_history_positive"]) for row in rows)
    both_positive_count = sum(bool(row["both_positive"]) for row in rows)
    mutually_exclusive_count = sum(bool(row["mutually_exclusive"]) for row in rows)
    min_margins = [_finite_float(row["min_preference_margin"]) for row in rows]
    return {
        "row_count": int(row_count),
        "correct_positive_count": int(correct_positive_count),
        "wrong_history_positive_count": int(wrong_positive_count),
        "both_positive_count": int(both_positive_count),
        "mutually_exclusive_count": int(mutually_exclusive_count),
        "correct_positive_fraction": float(correct_positive_count / row_count) if row_count else 0.0,
        "wrong_history_positive_fraction": float(wrong_positive_count / row_count) if row_count else 0.0,
        "both_directional_fraction": float(both_positive_count / row_count) if row_count else 0.0,
        "mutually_exclusive_fraction": float(mutually_exclusive_count / row_count) if row_count else 0.0,
        "min_margin_mean": float(np.mean(min_margins)) if min_margins else 0.0,
        "min_margin_p10": float(np.percentile(np.asarray(min_margins, dtype=np.float64), 10)) if min_margins else 0.0,
        "min_margin_min": float(np.min(min_margins)) if min_margins else 0.0,
        "min_margin_max": float(np.max(min_margins)) if min_margins else 0.0,
    }


def _classify_candidate(summary: dict[str, Any]) -> str:
    if float(summary["both_directional_fraction"]) >= 0.50 and int(summary["both_positive_count"]) > 0:
        return "actor_mean_directional_feasible"
    if int(summary["both_positive_count"]) > 0 or float(summary["mutually_exclusive_fraction"]) < 1.0:
        return "actor_mean_directional_mixed"
    return "actor_mean_directional_capacity_limited"


def _train_candidate(
    *,
    model: ActorCritic,
    checkpoint_data: dict[str, Any],
    base_state: dict[str, torch.Tensor],
    batch: SourceHistoryBatch,
    meta_rows: list[dict[str, Any]],
    run_dir: Path,
    init_name: str,
    steps: int,
    lr: float,
    target_margin: float,
    lambda_min: float,
    lambda_anchor: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    device = next(model.parameters()).device
    _set_actor_mean_trainable_only(model)
    trainable_count, frozen_count = _parameter_counts(model)
    initial_state = _clone_state_dict(model)
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        evaluation = _directional_eval(model, batch, target_margin=target_margin, lambda_min=lambda_min)
        anchor = _actor_mean_anchor_loss(model, base_state, device)
        loss = evaluation.loss + float(lambda_anchor) * anchor
        loss.backward()
        optimizer.step()
        trace_rows.append(
            {
                "init_name": init_name,
                "step": int(step + 1),
                "loss": float(loss.detach().cpu().item()),
                "directional_loss": float(evaluation.loss.detach().cpu().item()),
                "correct_loss": float(evaluation.correct_loss.detach().cpu().item()),
                "wrong_history_loss": float(evaluation.wrong_loss.detach().cpu().item()),
                "min_loss": float(evaluation.min_loss.detach().cpu().item()),
                "anchor_loss": float(anchor.detach().cpu().item()),
                "min_margin_mean": float(evaluation.min_margin.detach().mean().cpu().item()),
            }
        )

    final_eval = _directional_eval(model, batch, target_margin=target_margin, lambda_min=lambda_min)
    rows = _directional_rows(meta_rows=meta_rows, evaluation=final_eval, init_name=init_name)
    row_summary = _summarize_directional_rows(rows)
    state_after = _clone_state_dict(model)
    delta = _state_delta(base_state, state_after)
    init_delta = _state_delta(initial_state, state_after)
    checkpoint_path = run_dir / "checkpoints" / f"{init_name}_directional_candidate.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_path,
        metadata={
            "source_history_directional_feasibility_probe": {
                "init_name": init_name,
                "run_dir": str(run_dir),
                "steps": int(steps),
                "lr": float(lr),
                "target_margin": float(target_margin),
            }
        },
    )
    candidate_summary = {
        "init_name": init_name,
        "checkpoint": str(checkpoint_path),
        "steps": int(steps),
        "lr": float(lr),
        "target_margin": float(target_margin),
        "lambda_min": float(lambda_min),
        "lambda_anchor": float(lambda_anchor),
        "final_loss": float(final_eval.loss.detach().cpu().item()),
        "final_correct_loss": float(final_eval.correct_loss.detach().cpu().item()),
        "final_wrong_history_loss": float(final_eval.wrong_loss.detach().cpu().item()),
        "final_min_loss": float(final_eval.min_loss.detach().cpu().item()),
        "trainable_parameter_count": int(trainable_count),
        "frozen_parameter_count": int(frozen_count),
        "non_actor_mean_mutation_detected": bool(delta["non_actor_mean_changed"]),
        "actor_mean_changed": bool(delta["actor_mean_changed"]),
        "actor_mean_l2_from_base": float(delta["actor_mean_l2"]),
        "actor_mean_max_abs_from_base": float(delta["actor_mean_max_abs"]),
        "non_actor_mean_l2_from_base": float(delta["non_actor_mean_l2"]),
        "non_actor_mean_max_abs_from_base": float(delta["non_actor_mean_max_abs"]),
        "actor_mean_l2_from_init": float(init_delta["actor_mean_l2"]),
        "actor_mean_max_abs_from_init": float(init_delta["actor_mean_max_abs"]),
        **row_summary,
    }
    candidate_summary["candidate_class"] = _classify_candidate(candidate_summary)
    write_json(run_dir / f"{init_name}_candidate_summary.json", candidate_summary)
    return candidate_summary, rows, trace_rows


def classify_probe(candidate_summaries: list[dict[str, Any]]) -> tuple[str, str]:
    if any(str(row.get("candidate_class")) == "actor_mean_directional_feasible" for row in candidate_summaries):
        return "source_history_actor_mean_directional_feasibility_positive", "route to result audit and retention design"
    if any(str(row.get("candidate_class")) == "actor_mean_directional_mixed" for row in candidate_summaries):
        return "source_history_actor_mean_directional_feasibility_mixed", "route to pair-group directional objective design"
    return "source_history_actor_mean_directional_capacity_limited", "route to trainable-scope escalation or corpus relabel audit"


def run_directional_feasibility_probe(
    *,
    checkpoint_path: Path,
    m1288_checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    steps: int = 300,
    lr: float = 3e-4,
    target_margin: float = 0.05,
    lambda_min: float = 2.0,
    lambda_anchor: float = 0.001,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    m1288_checkpoint_path = Path(m1288_checkpoint_path)
    history_run_dir = Path(history_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)

    base_model, base_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(base_model, base_checkpoint)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    base_model.eval()
    base_state = _clone_state_dict(base_model)
    batch = _load_source_history_batch(
        model=base_model,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        device=resolved_device,
    )
    meta_rows = _source_history_meta_rows(history_run_dir)

    candidate_summaries: list[dict[str, Any]] = []
    all_directional_rows: list[dict[str, Any]] = []
    all_trace_rows: list[dict[str, Any]] = []
    for init_name, init_checkpoint in (
        ("base_init", checkpoint_path),
        ("m1288_init", m1288_checkpoint_path),
    ):
        model, checkpoint_data = load_actor_critic_checkpoint(init_checkpoint, device=str(resolved_device))
        contract_ok, contract_reason = _checkpoint_contract(model, checkpoint_data)
        if not contract_ok:
            raise ValueError(f"{init_name} checkpoint contract violation: {contract_reason}")
        model.eval()
        candidate_summary, directional_rows, trace_rows = _train_candidate(
            model=model,
            checkpoint_data=checkpoint_data,
            base_state=base_state,
            batch=batch,
            meta_rows=meta_rows,
            run_dir=run_dir,
            init_name=init_name,
            steps=steps,
            lr=lr,
            target_margin=target_margin,
            lambda_min=lambda_min,
            lambda_anchor=lambda_anchor,
        )
        candidate_summaries.append(candidate_summary)
        all_directional_rows.extend(directional_rows)
        all_trace_rows.extend(trace_rows)

    write_csv_rows(run_dir / "candidate_summaries.csv", candidate_summaries)
    write_csv_rows(run_dir / "directional_feasibility_rows.csv", all_directional_rows)
    write_csv_rows(run_dir / "train_trace.csv", all_trace_rows)
    result_class, recommended_next_step = classify_probe(candidate_summaries)
    best = sorted(
        candidate_summaries,
        key=lambda row: (
            -float(row["both_directional_fraction"]),
            -float(row["min_margin_mean"]),
            float(row["mutually_exclusive_fraction"]),
        ),
    )[0]
    summary = {
        "run_type": "source_history_actor_mean_directional_feasibility_probe",
        "checkpoint": str(checkpoint_path),
        "m1288_checkpoint": str(m1288_checkpoint_path),
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "steps": int(steps),
        "lr": float(lr),
        "target_margin": float(target_margin),
        "lambda_min": float(lambda_min),
        "lambda_anchor": float(lambda_anchor),
        "candidate_count": int(len(candidate_summaries)),
        "best_init_name": str(best["init_name"]),
        "best_candidate_class": str(best["candidate_class"]),
        "best_both_directional_fraction": float(best["both_directional_fraction"]),
        "best_both_positive_count": int(best["both_positive_count"]),
        "best_mutually_exclusive_fraction": float(best["mutually_exclusive_fraction"]),
        "best_min_margin_mean": float(best["min_margin_mean"]),
        "best_min_margin_p10": float(best["min_margin_p10"]),
        "any_non_actor_mean_mutation_detected": any(
            bool(row["non_actor_mean_mutation_detected"]) for row in candidate_summaries
        ),
        "result_class": result_class,
        "recommended_next_step": recommended_next_step,
        "labels_enter_actor_input": False,
        "objective_update_started": True,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "candidate_summaries_csv": run_dir / "candidate_summaries.csv",
        "directional_feasibility_rows_csv": run_dir / "directional_feasibility_rows.csv",
        "train_trace_csv": run_dir / "train_trace.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run actor_mean-only source-history directional feasibility probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--m1288-checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--target-margin", type=float, default=0.05)
    parser.add_argument("--lambda-min", type=float, default=2.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.001)
    args = parser.parse_args()
    summary = run_directional_feasibility_probe(
        checkpoint_path=args.checkpoint,
        m1288_checkpoint_path=args.m1288_checkpoint,
        history_run_dir=args.history_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        steps=args.steps,
        lr=args.lr,
        target_margin=args.target_margin,
        lambda_min=args.lambda_min,
        lambda_anchor=args.lambda_anchor,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
