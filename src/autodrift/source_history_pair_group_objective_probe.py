"""Pair-group source-history directional objective probe."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_history_directional_feasibility_probe import (
    _actor_mean_anchor_loss,
    _directional_eval,
    _directional_rows,
    _source_history_meta_rows,
)
from autodrift.source_history_objective_update import (
    SourceHistoryBatch,
    _clone_state_dict,
    _load_source_history_batch,
    _parameter_counts,
    _save_checkpoint,
    _set_actor_mean_trainable_only,
    _state_delta,
)
from autodrift.source_history_policy_gate import _checkpoint_contract
from autodrift.train_ppo import ActorCritic, resolve_device


def _group_indices(meta_rows: list[dict[str, Any]]) -> dict[tuple[int, str], list[int]]:
    groups: dict[tuple[int, str], list[int]] = {}
    for index, row in enumerate(meta_rows):
        key = (int(row["pair_id"]), str(row["probe_template"]))
        groups.setdefault(key, []).append(index)
    return groups


def _pair_group_loss(
    *,
    min_margin: torch.Tensor,
    groups: dict[tuple[int, str], list[int]],
    target_margin: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    group_floor_terms: list[torch.Tensor] = []
    group_balance_terms: list[torch.Tensor] = []
    group_min_terms: list[torch.Tensor] = []
    for indices in groups.values():
        idx = torch.as_tensor(indices, dtype=torch.long, device=min_margin.device)
        values = min_margin.index_select(dim=0, index=idx)
        group_min = torch.min(values)
        group_min_terms.append(group_min)
        group_floor_terms.append(torch.nn.functional.softplus(float(target_margin) - group_min))
        group_balance_terms.append(torch.mean((values - torch.mean(values)).pow(2)))
    if not group_floor_terms:
        zero = torch.zeros((), dtype=torch.float32, device=min_margin.device)
        return zero, zero, zero
    return (
        torch.stack(group_floor_terms).mean(),
        torch.stack(group_balance_terms).mean(),
        torch.stack(group_min_terms).mean(),
    )


def _summarize_group_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["pair_id"]), str(row["probe_template"]))
        groups.setdefault(key, []).append(row)
    group_rows: list[dict[str, Any]] = []
    for (pair_id, probe_template), members in sorted(groups.items()):
        both_count = sum(bool(member["both_positive"]) for member in members)
        min_margins = [_finite_float(member["min_preference_margin"]) for member in members]
        group_min = min(min_margins) if min_margins else 0.0
        group_balance = float(np.mean((np.asarray(min_margins, dtype=np.float64) - np.mean(min_margins)) ** 2)) if min_margins else 0.0
        group_rows.append(
            {
                "pair_id": int(pair_id),
                "probe_template": str(probe_template),
                "row_count": int(len(members)),
                "both_positive_count": int(both_count),
                "all_rows_both_positive": bool(both_count == len(members) and len(members) > 0),
                "any_row_both_positive": bool(both_count > 0),
                "group_min_margin": float(group_min),
                "group_balance_loss": group_balance,
            }
        )
    group_count = len(group_rows)
    all_count = sum(bool(row["all_rows_both_positive"]) for row in group_rows)
    any_count = sum(bool(row["any_row_both_positive"]) for row in group_rows)
    group_mins = [_finite_float(row["group_min_margin"]) for row in group_rows]
    balances = [_finite_float(row["group_balance_loss"]) for row in group_rows]
    return {
        "group_rows": group_rows,
        "pair_probe_group_count": int(group_count),
        "group_all_rows_both_positive_count": int(all_count),
        "group_any_row_both_positive_count": int(any_count),
        "group_all_rows_both_positive_fraction": float(all_count / group_count) if group_count else 0.0,
        "group_any_row_both_positive_fraction": float(any_count / group_count) if group_count else 0.0,
        "group_min_margin_mean": float(np.mean(group_mins)) if group_mins else 0.0,
        "group_min_margin_p10": float(np.percentile(np.asarray(group_mins, dtype=np.float64), 10)) if group_mins else 0.0,
        "group_balance_loss_mean": float(np.mean(balances)) if balances else 0.0,
    }


def _classify_candidate(summary: dict[str, Any]) -> str:
    if (
        float(summary["group_all_rows_both_positive_fraction"]) >= 0.25
        and float(summary["both_directional_fraction"]) >= 0.25
        and int(summary["group_all_rows_both_positive_count"]) > 14
        and not bool(summary["non_actor_mean_mutation_detected"])
    ):
        return "pair_group_directional_strong"
    if int(summary["group_all_rows_both_positive_count"]) > 14 or float(summary["both_directional_fraction"]) > 0.1842105263:
        return "pair_group_directional_mixed"
    return "pair_group_directional_negative"


def _row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    both_count = sum(bool(row["both_positive"]) for row in rows)
    mutually_exclusive = sum(bool(row["mutually_exclusive"]) for row in rows)
    min_margins = [_finite_float(row["min_preference_margin"]) for row in rows]
    return {
        "row_count": int(row_count),
        "both_positive_count": int(both_count),
        "mutually_exclusive_count": int(mutually_exclusive),
        "both_directional_fraction": float(both_count / row_count) if row_count else 0.0,
        "mutually_exclusive_fraction": float(mutually_exclusive / row_count) if row_count else 0.0,
        "min_margin_mean": float(np.mean(min_margins)) if min_margins else 0.0,
        "min_margin_p10": float(np.percentile(np.asarray(min_margins, dtype=np.float64), 10)) if min_margins else 0.0,
    }


def _train_candidate(
    *,
    model: ActorCritic,
    checkpoint_data: dict[str, Any],
    base_state: dict[str, torch.Tensor],
    batch: SourceHistoryBatch,
    meta_rows: list[dict[str, Any]],
    groups: dict[tuple[int, str], list[int]],
    run_dir: Path,
    init_name: str,
    steps: int,
    lr: float,
    target_margin: float,
    lambda_group_floor: float,
    lambda_group_balance: float,
    lambda_anchor: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    device = next(model.parameters()).device
    _set_actor_mean_trainable_only(model)
    trainable_count, frozen_count = _parameter_counts(model)
    init_state = _clone_state_dict(model)
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        eval_row = _directional_eval(model, batch, target_margin=target_margin, lambda_min=0.0)
        group_floor, group_balance, group_min = _pair_group_loss(
            min_margin=eval_row.min_margin,
            groups=groups,
            target_margin=target_margin,
        )
        anchor = _actor_mean_anchor_loss(model, base_state, device)
        loss = (
            eval_row.correct_loss
            + eval_row.wrong_loss
            + float(lambda_group_floor) * group_floor
            + float(lambda_group_balance) * group_balance
            + float(lambda_anchor) * anchor
        )
        loss.backward()
        optimizer.step()
        trace_rows.append(
            {
                "init_name": init_name,
                "step": int(step + 1),
                "loss": float(loss.detach().cpu().item()),
                "correct_loss": float(eval_row.correct_loss.detach().cpu().item()),
                "wrong_history_loss": float(eval_row.wrong_loss.detach().cpu().item()),
                "group_floor_loss": float(group_floor.detach().cpu().item()),
                "group_balance_loss": float(group_balance.detach().cpu().item()),
                "group_min_margin_mean": float(group_min.detach().cpu().item()),
                "anchor_loss": float(anchor.detach().cpu().item()),
            }
        )

    final_eval = _directional_eval(model, batch, target_margin=target_margin, lambda_min=0.0)
    rows = _directional_rows(meta_rows=meta_rows, evaluation=final_eval, init_name=init_name)
    group_summary = _summarize_group_rows(rows)
    group_rows = [{**row, "init_name": init_name} for row in group_summary.pop("group_rows")]
    state_after = _clone_state_dict(model)
    delta = _state_delta(base_state, state_after)
    init_delta = _state_delta(init_state, state_after)
    checkpoint_path = run_dir / "checkpoints" / f"{init_name}_pair_group_candidate.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_path,
        metadata={
            "source_history_pair_group_objective_probe": {
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
        "lambda_group_floor": float(lambda_group_floor),
        "lambda_group_balance": float(lambda_group_balance),
        "lambda_anchor": float(lambda_anchor),
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
        **_row_summary(rows),
        **group_summary,
    }
    candidate_summary["candidate_class"] = _classify_candidate(candidate_summary)
    write_json(run_dir / f"{init_name}_candidate_summary.json", candidate_summary)
    return candidate_summary, rows, group_rows, trace_rows


def classify_probe(candidate_summaries: list[dict[str, Any]]) -> tuple[str, str]:
    classes = {str(row["candidate_class"]) for row in candidate_summaries}
    if "pair_group_directional_strong" in classes:
        return "source_history_pair_group_objective_strong", "route to result audit and proof-retention design"
    if "pair_group_directional_mixed" in classes:
        return "source_history_pair_group_objective_mixed", "route to result audit and scope-or-refresh decision"
    return "source_history_pair_group_objective_negative", "route to trainable-scope escalation or corpus relabel audit"


def run_pair_group_objective_probe(
    *,
    checkpoint_path: Path,
    m1288_checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    steps: int = 500,
    lr: float = 3e-4,
    target_margin: float = 0.05,
    lambda_group_floor: float = 4.0,
    lambda_group_balance: float = 0.5,
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
    groups = _group_indices(meta_rows)

    candidate_summaries: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
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
        candidate_summary, rows, group_rows, trace_rows = _train_candidate(
            model=model,
            checkpoint_data=checkpoint_data,
            base_state=base_state,
            batch=batch,
            meta_rows=meta_rows,
            groups=groups,
            run_dir=run_dir,
            init_name=init_name,
            steps=steps,
            lr=lr,
            target_margin=target_margin,
            lambda_group_floor=lambda_group_floor,
            lambda_group_balance=lambda_group_balance,
            lambda_anchor=lambda_anchor,
        )
        candidate_summaries.append(candidate_summary)
        all_rows.extend(rows)
        all_group_rows.extend(group_rows)
        all_trace_rows.extend(trace_rows)

    write_csv_rows(run_dir / "candidate_summaries.csv", candidate_summaries)
    write_csv_rows(run_dir / "directional_rows.csv", all_rows)
    write_csv_rows(run_dir / "group_rows.csv", all_group_rows)
    write_csv_rows(run_dir / "train_trace.csv", all_trace_rows)
    result_class, recommended_next_step = classify_probe(candidate_summaries)
    best = sorted(
        candidate_summaries,
        key=lambda row: (
            -float(row["group_all_rows_both_positive_fraction"]),
            -float(row["both_directional_fraction"]),
            -float(row["group_min_margin_mean"]),
        ),
    )[0]
    summary = {
        "run_type": "source_history_pair_group_objective_probe",
        "checkpoint": str(checkpoint_path),
        "m1288_checkpoint": str(m1288_checkpoint_path),
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "steps": int(steps),
        "lr": float(lr),
        "target_margin": float(target_margin),
        "lambda_group_floor": float(lambda_group_floor),
        "lambda_group_balance": float(lambda_group_balance),
        "lambda_anchor": float(lambda_anchor),
        "candidate_count": int(len(candidate_summaries)),
        "best_init_name": str(best["init_name"]),
        "best_candidate_class": str(best["candidate_class"]),
        "best_both_directional_fraction": float(best["both_directional_fraction"]),
        "best_both_positive_count": int(best["both_positive_count"]),
        "best_mutually_exclusive_fraction": float(best["mutually_exclusive_fraction"]),
        "best_group_all_rows_both_positive_count": int(best["group_all_rows_both_positive_count"]),
        "best_group_all_rows_both_positive_fraction": float(best["group_all_rows_both_positive_fraction"]),
        "best_group_any_row_both_positive_count": int(best["group_any_row_both_positive_count"]),
        "best_group_min_margin_mean": float(best["group_min_margin_mean"]),
        "best_group_min_margin_p10": float(best["group_min_margin_p10"]),
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
        "directional_rows_csv": run_dir / "directional_rows.csv",
        "group_rows_csv": run_dir / "group_rows.csv",
        "train_trace_csv": run_dir / "train_trace.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pair-group source-history directional objective probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--m1288-checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--target-margin", type=float, default=0.05)
    parser.add_argument("--lambda-group-floor", type=float, default=4.0)
    parser.add_argument("--lambda-group-balance", type=float, default=0.5)
    parser.add_argument("--lambda-anchor", type=float, default=0.001)
    args = parser.parse_args()
    summary = run_pair_group_objective_probe(
        checkpoint_path=args.checkpoint,
        m1288_checkpoint_path=args.m1288_checkpoint,
        history_run_dir=args.history_run_dir,
        intervention_run_dir=args.intervention_run_dir,
        run_dir=args.run_dir,
        device=args.device,
        steps=args.steps,
        lr=args.lr,
        target_margin=args.target_margin,
        lambda_group_floor=args.lambda_group_floor,
        lambda_group_balance=args.lambda_group_balance,
        lambda_anchor=args.lambda_anchor,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
