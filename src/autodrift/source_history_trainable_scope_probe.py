"""Trainable-scope source-history diagnostic probe."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.fresh_trajectory_boundary_sampler import _finite_float
from autodrift.source_history_directional_feasibility_probe import (
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
)
from autodrift.source_history_pair_group_objective_probe import (
    _group_indices,
    _pair_group_loss,
    _row_summary,
    _summarize_group_rows,
)
from autodrift.source_history_policy_gate import _checkpoint_contract
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_SCOPES = ("actor_mean_only_replay", "fusion_head", "current_step_gru_fusion_head")
PARAMETER_GROUPS = (
    "actor_mean",
    "response_context_fusion",
    "online_gru_cell",
    "response_encoder",
    "context_encoder",
    "critic",
    "log_std",
    "sequence_tail",
    "privileged",
    "other",
)
SCOPE_ALLOWED_GROUPS = {
    "actor_mean_only_replay": {"actor_mean"},
    "fusion_head": {"actor_mean", "response_context_fusion"},
    "current_step_gru_fusion_head": {"actor_mean", "response_context_fusion", "online_gru_cell"},
}


def _stable_pair_bucket(pair_id: int, split_mod: int = 5) -> int:
    return int((int(pair_id) * 2654435761) % int(split_mod))


def _stable_eval_pair(pair_id: int, split_mod: int = 5, split_offset: int = 0) -> bool:
    return _stable_pair_bucket(pair_id, split_mod=split_mod) == int(split_offset)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _split_rows(meta_rows: list[dict[str, Any]], *, split_mod: int = 5, split_offset: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(meta_rows):
        pair_id = int(row["pair_id"])
        split = "eval" if _stable_eval_pair(pair_id, split_mod=split_mod, split_offset=split_offset) else "train"
        rows.append(
            {
                "row_index": int(index),
                "split": split,
                "split_mod": int(split_mod),
                "split_offset": int(split_offset),
                "pair_bucket": int(_stable_pair_bucket(pair_id, split_mod=split_mod)),
                "pair_id": pair_id,
                "probe_template": str(row["probe_template"]),
                "history_intervention_id": int(row["history_intervention_id"]),
                "condition": str(row["condition"]),
            }
        )
    return rows


def _load_split_plan(path: Path) -> dict[tuple[int, str], int]:
    rows = _read_csv_rows(path)
    plan: dict[tuple[int, str], int] = {}
    pair_folds: dict[int, int] = {}
    for row in rows:
        pair_id = int(float(row["pair_id"]))
        probe_template = str(row["probe_template"])
        fold = int(float(row["assigned_eval_fold"]))
        key = (pair_id, probe_template)
        if key in plan and plan[key] != fold:
            raise ValueError(f"conflicting split-plan fold for key={key}")
        plan[key] = fold
        if pair_id in pair_folds and pair_folds[pair_id] != fold:
            raise ValueError(f"split plan is not pair-disjoint for pair_id={pair_id}")
        pair_folds[pair_id] = fold
    if not plan:
        raise ValueError("split plan is empty")
    return plan


def _split_rows_from_plan(
    meta_rows: list[dict[str, Any]],
    split_plan: dict[tuple[int, str], int],
    *,
    split_mod: int = 5,
    split_offset: int = 0,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(meta_rows):
        pair_id = int(row["pair_id"])
        probe_template = str(row["probe_template"])
        key = (pair_id, probe_template)
        if key not in split_plan:
            raise ValueError(f"split plan missing key={key}")
        pair_bucket = int(split_plan[key])
        if pair_bucket < 0 or pair_bucket >= int(split_mod):
            raise ValueError(f"split plan fold {pair_bucket} outside split_mod={split_mod}")
        split = "eval" if pair_bucket == int(split_offset) else "train"
        rows.append(
            {
                "row_index": int(index),
                "split": split,
                "split_mod": int(split_mod),
                "split_offset": int(split_offset),
                "pair_bucket": int(pair_bucket),
                "pair_id": pair_id,
                "probe_template": probe_template,
                "history_intervention_id": int(row["history_intervention_id"]),
                "condition": str(row["condition"]),
            }
        )
    return rows


def _indices_for_split(split_rows: list[dict[str, Any]], split: str) -> list[int]:
    return [int(row["row_index"]) for row in split_rows if str(row["split"]) == split]


def _slice_batch(batch: SourceHistoryBatch, indices: list[int]) -> SourceHistoryBatch:
    idx = torch.as_tensor(indices, dtype=torch.long, device=batch.observations.device)
    return SourceHistoryBatch(
        observations=batch.observations.index_select(dim=0, index=idx),
        correct_hidden=batch.correct_hidden.index_select(dim=0, index=idx),
        wrong_hidden=batch.wrong_hidden.index_select(dim=0, index=idx),
        preferred_actions=batch.preferred_actions.index_select(dim=0, index=idx),
        rejected_actions=batch.rejected_actions.index_select(dim=0, index=idx),
    )


def _slice_meta(meta_rows: list[dict[str, Any]], indices: list[int]) -> list[dict[str, Any]]:
    return [meta_rows[index] for index in indices]


def _parameter_group(name: str) -> str:
    if name.startswith("actor_mean."):
        return "actor_mean"
    if name.startswith("response_context_fusion."):
        return "response_context_fusion"
    if name.startswith("online_gru_cell."):
        return "online_gru_cell"
    if name.startswith("response_encoder."):
        return "response_encoder"
    if name.startswith("context_encoder."):
        return "context_encoder"
    if name.startswith("critic."):
        return "critic"
    if name == "log_std":
        return "log_std"
    if name.startswith("sequence_tail."):
        return "sequence_tail"
    if name.startswith("privileged_"):
        return "privileged"
    return "other"


def _set_trainable_scope(model: ActorCritic, scope: str) -> None:
    allowed = SCOPE_ALLOWED_GROUPS[scope]
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(_parameter_group(name) in allowed)


def _trainable_parameters(model: ActorCritic) -> list[torch.nn.Parameter]:
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def _parameter_group_delta(
    base_state: dict[str, torch.Tensor],
    updated_state: dict[str, torch.Tensor],
) -> dict[str, dict[str, Any]]:
    groups = {
        group: {
            "sq": 0.0,
            "max_abs": 0.0,
            "changed": False,
            "parameter_count": 0,
        }
        for group in PARAMETER_GROUPS
    }
    for name, base_tensor in sorted(base_state.items()):
        updated_tensor = updated_state[name].detach().cpu()
        delta = updated_tensor - base_tensor
        group = _parameter_group(name)
        max_abs = float(torch.max(torch.abs(delta)).item()) if delta.numel() else 0.0
        sq = float(torch.sum(delta.float().pow(2)).item())
        groups[group]["sq"] += sq
        groups[group]["max_abs"] = max(float(groups[group]["max_abs"]), max_abs)
        groups[group]["changed"] = bool(groups[group]["changed"] or max_abs > 0.0)
        groups[group]["parameter_count"] = int(groups[group]["parameter_count"]) + int(delta.numel())
    return {
        group: {
            "l2": float(np.sqrt(float(data["sq"]))),
            "max_abs": float(data["max_abs"]),
            "changed": bool(data["changed"]),
            "parameter_count": int(data["parameter_count"]),
        }
        for group, data in groups.items()
    }


def _parameter_group_rows(
    *,
    scope: str,
    split_offset: int,
    allowed_groups: set[str],
    deltas: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in PARAMETER_GROUPS:
        data = deltas[group]
        allowed = group in allowed_groups
        rows.append(
            {
                "scope": scope,
                "split_offset": int(split_offset),
                "parameter_group": group,
                "allowed_to_change": allowed,
                "changed": bool(data["changed"]),
                "l2": float(data["l2"]),
                "max_abs": float(data["max_abs"]),
                "parameter_count": int(data["parameter_count"]),
                "forbidden_mutation": bool(data["changed"] and not allowed),
            }
        )
    return rows


def _parameter_anchor_loss(
    model: ActorCritic,
    anchor_state: dict[str, torch.Tensor],
    allowed_groups: set[str],
    device: torch.device,
) -> torch.Tensor:
    losses: list[torch.Tensor] = []
    for name, parameter in model.named_parameters():
        if _parameter_group(name) in allowed_groups:
            anchor = anchor_state[name].to(device=device, dtype=torch.float32)
            losses.append(torch.mean((parameter - anchor).pow(2)))
    if not losses:
        return torch.zeros((), dtype=torch.float32, device=device)
    return torch.stack(losses).mean()


def _summary_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_summary = _row_summary(rows)
    group_summary = _summarize_group_rows(rows)
    group_summary.pop("group_rows")
    return {**row_summary, **group_summary}


def _load_group_weights(path: Path) -> tuple[dict[tuple[int, str], float], bool, float]:
    rows = _read_csv_rows(path)
    weights: dict[tuple[int, str], float] = {}
    pair_specific = False
    max_weight = 0.0
    for row in rows:
        key = (int(float(row["pair_id"])), str(row["probe_template"]))
        weight = _finite_float(row["group_weight"])
        if key in weights and abs(weights[key] - weight) > 1e-9:
            raise ValueError(f"conflicting group weight for key={key}")
        weights[key] = float(weight)
        max_weight = max(max_weight, float(weight))
        pair_specific = pair_specific or str(row.get("pair_specific_weight_used", "")).lower() == "true"
    if not weights:
        raise ValueError("group weights are empty")
    return weights, pair_specific, max_weight


def _load_group_metadata(path: Path | None) -> dict[tuple[int, str], dict[str, Any]]:
    if path is None:
        return {}
    rows = _read_csv_rows(path)
    metadata: dict[tuple[int, str], dict[str, Any]] = {}
    for row in rows:
        key = (int(float(row["pair_id"])), str(row["probe_template"]))
        metadata[key] = {
            "source_family_pair": str(row.get("source_family_pair", "unknown")),
            "source_fault_pair": str(row.get("source_fault_pair", "unknown")),
            "margin_bucket": str(row.get("margin_bucket", "unknown")),
            "group_weight": _finite_float(row.get("group_weight", 1.0)),
            "failed_combo_boost": _finite_float(row.get("failed_combo_boost", 0.0)),
            "pair_specific_weight_used": _truthy(row.get("pair_specific_weight_used", False)),
        }
    return metadata


def _load_baseline_repeat_groups(path: Path | None, scope: str) -> dict[tuple[int, int, str], dict[str, Any]]:
    if path is None:
        return {}
    rows = _read_csv_rows(Path(path) / "group_rows.csv")
    groups: dict[tuple[int, int, str], dict[str, Any]] = {}
    for row in rows:
        if str(row.get("scope", scope)) != scope:
            continue
        if str(row.get("split", "")) != "full":
            continue
        key = (int(float(row["split_offset"])), int(float(row["pair_id"])), str(row["probe_template"]))
        groups[key] = {
            "all_rows_both_positive": _truthy(row.get("all_rows_both_positive", False)),
            "group_min_margin": _finite_float(row.get("group_min_margin", 0.0)),
        }
    return groups


def _baseline_pass_offsets(path: Path | None, scope: str) -> set[int]:
    if path is None:
        return set()
    rows = _read_csv_rows(Path(path) / "scope_summaries.csv")
    offsets: set[int] = set()
    for row in rows:
        if str(row.get("scope", scope)) == scope and _offset_pass(row):
            offsets.add(int(float(row["split_offset"])))
    return offsets


def _weights_for_meta_rows(
    meta_rows: list[dict[str, Any]],
    group_weights: dict[tuple[int, str], float] | None,
    device: torch.device,
) -> torch.Tensor | None:
    if group_weights is None:
        return None
    values: list[float] = []
    for row in meta_rows:
        key = (int(row["pair_id"]), str(row["probe_template"]))
        if key not in group_weights:
            raise ValueError(f"group weights missing key={key}")
        values.append(float(group_weights[key]))
    return torch.as_tensor(values, dtype=torch.float32, device=device)


def _weighted_mean(values: torch.Tensor, weights: torch.Tensor | None) -> torch.Tensor:
    if weights is None:
        return values.mean()
    return torch.sum(values * weights) / torch.clamp(torch.sum(weights), min=1e-6)


def _weighted_directional_losses(
    evaluation: Any,
    row_weights: torch.Tensor | None,
    *,
    target_margin: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    correct_terms = torch.nn.functional.softplus(float(target_margin) - evaluation.correct_margin)
    wrong_terms = torch.nn.functional.softplus(float(target_margin) - evaluation.wrong_margin)
    return _weighted_mean(correct_terms, row_weights), _weighted_mean(wrong_terms, row_weights)


def _weighted_pair_group_loss(
    *,
    min_margin: torch.Tensor,
    groups: dict[tuple[int, str], list[int]],
    group_weights: dict[tuple[int, str], float] | None,
    target_margin: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    group_floor_terms: list[torch.Tensor] = []
    group_balance_terms: list[torch.Tensor] = []
    group_min_terms: list[torch.Tensor] = []
    weight_terms: list[torch.Tensor] = []
    for key, indices in groups.items():
        idx = torch.as_tensor(indices, dtype=torch.long, device=min_margin.device)
        values = min_margin.index_select(dim=0, index=idx)
        group_min = torch.min(values)
        weight = 1.0 if group_weights is None else float(group_weights.get(key, 1.0))
        weight_tensor = torch.as_tensor(weight, dtype=torch.float32, device=min_margin.device)
        group_min_terms.append(group_min)
        group_floor_terms.append(torch.nn.functional.softplus(float(target_margin) - group_min) * weight_tensor)
        group_balance_terms.append(torch.mean((values - torch.mean(values)).pow(2)) * weight_tensor)
        weight_terms.append(weight_tensor)
    if not group_floor_terms:
        zero = torch.zeros((), dtype=torch.float32, device=min_margin.device)
        return zero, zero, zero
    weight_sum = torch.clamp(torch.stack(weight_terms).sum(), min=1e-6)
    return (
        torch.stack(group_floor_terms).sum() / weight_sum,
        torch.stack(group_balance_terms).sum() / weight_sum,
        torch.stack(group_min_terms).mean(),
    )


def _bucket_key(
    key: tuple[int, str],
    group_metadata: dict[tuple[int, str], dict[str, Any]],
    bucket_columns: tuple[str, ...],
) -> tuple[str, ...]:
    metadata = group_metadata.get(key, {})
    values = [str(metadata.get(column, "unknown")) for column in bucket_columns]
    return tuple(values) if values else ("all",)


def _robust_minfold_losses(
    *,
    min_margin: torch.Tensor,
    groups: dict[tuple[int, str], list[int]],
    group_metadata: dict[tuple[int, str], dict[str, Any]],
    baseline_repeat_groups: dict[tuple[int, int, str], dict[str, Any]],
    split_offset: int,
    bucket_columns: tuple[str, ...],
    target_margin: float,
    retention_margin_eps: float,
    minfold_temperature: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    bucket_terms: dict[tuple[str, ...], list[torch.Tensor]] = {}
    retention_terms: list[torch.Tensor] = []
    for key, indices in groups.items():
        idx = torch.as_tensor(indices, dtype=torch.long, device=min_margin.device)
        values = min_margin.index_select(dim=0, index=idx)
        group_min = torch.min(values)
        floor_term = torch.nn.functional.softplus(float(target_margin) - group_min)
        bucket_terms.setdefault(_bucket_key(key, group_metadata, bucket_columns), []).append(floor_term)
        baseline = baseline_repeat_groups.get((int(split_offset), int(key[0]), str(key[1])))
        if baseline and _truthy(baseline.get("all_rows_both_positive", False)):
            baseline_margin = _finite_float(baseline.get("group_min_margin", 0.0))
            retention_terms.append(
                torch.nn.functional.softplus(
                    torch.as_tensor(
                        baseline_margin - float(retention_margin_eps),
                        dtype=torch.float32,
                        device=min_margin.device,
                    )
                    - group_min
                )
            )
    if bucket_terms:
        tau = max(float(minfold_temperature), 1e-6)
        bucket_losses = []
        for values in bucket_terms.values():
            stacked = torch.stack(values)
            bucket_losses.append(torch.as_tensor(tau, dtype=torch.float32, device=min_margin.device) * torch.logsumexp(stacked / tau, dim=0))
        bucket_cvar = torch.stack(bucket_losses).mean()
    else:
        bucket_cvar = torch.zeros((), dtype=torch.float32, device=min_margin.device)
    retention = (
        torch.stack(retention_terms).mean()
        if retention_terms
        else torch.zeros((), dtype=torch.float32, device=min_margin.device)
    )
    return bucket_cvar, retention


def _eval_scope_split(
    *,
    model: ActorCritic,
    batch: SourceHistoryBatch,
    meta_rows: list[dict[str, Any]],
    scope: str,
    split_offset: int,
    split: str,
    target_margin: float,
    group_weights: dict[tuple[int, str], float] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if not meta_rows:
        empty = {
            "row_count": 0,
            "both_positive_count": 0,
            "mutually_exclusive_count": 0,
            "both_directional_fraction": 0.0,
            "mutually_exclusive_fraction": 0.0,
            "min_margin_mean": 0.0,
            "min_margin_p10": 0.0,
            "pair_probe_group_count": 0,
            "group_all_rows_both_positive_count": 0,
            "group_any_row_both_positive_count": 0,
            "group_all_rows_both_positive_fraction": 0.0,
            "group_any_row_both_positive_fraction": 0.0,
            "group_min_margin_mean": 0.0,
            "group_min_margin_p10": 0.0,
            "group_balance_loss_mean": 0.0,
        }
        return empty, [], []
    evaluation = _directional_eval(model, batch, target_margin=target_margin, lambda_min=0.0)
    rows = _directional_rows(meta_rows=meta_rows, evaluation=evaluation, init_name=scope)
    for row in rows:
        row["split"] = split
        row["split_offset"] = int(split_offset)
        if group_weights is not None:
            row["group_weight"] = float(group_weights.get((int(row["pair_id"]), str(row["probe_template"])), 1.0))
    group_summary = _summarize_group_rows(rows)
    group_rows = [
        {
            **row,
            "scope": scope,
            "split": split,
            "split_offset": int(split_offset),
            "group_weight": float(group_weights.get((int(row["pair_id"]), str(row["probe_template"])), 1.0))
            if group_weights is not None
            else 1.0,
        }
        for row in group_summary.pop("group_rows")
    ]
    return {**_row_summary(rows), **group_summary}, rows, group_rows


def _prefixed(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in values.items()}


def _classify_scope(summary: dict[str, Any]) -> str:
    if bool(summary["forbidden_parameter_mutation_detected"]):
        return "trainable_scope_contract_artifact"
    if (
        float(summary["eval_group_all_rows_both_positive_fraction"]) >= 0.25
        and float(summary["eval_both_directional_fraction"]) >= 0.25
        and int(summary["full_group_all_rows_both_positive_count"]) > 15
        and int(summary["full_both_positive_count"]) > 30
    ):
        return "trainable_scope_directional_strong"
    if int(summary["full_group_all_rows_both_positive_count"]) > 15 or int(summary["full_both_positive_count"]) > 30:
        return "trainable_scope_directional_mixed"
    return "trainable_scope_directional_negative"


def _offset_pass(summary: dict[str, Any]) -> bool:
    return bool(
        not _truthy(summary["forbidden_parameter_mutation_detected"])
        and float(summary["eval_group_all_rows_both_positive_fraction"]) >= 0.25
        and float(summary["eval_both_directional_fraction"]) >= 0.25
        and int(summary["full_group_all_rows_both_positive_count"]) > 15
        and int(summary["full_both_positive_count"]) > 30
    )


def _repeat_summaries(scope_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scope: dict[str, list[dict[str, Any]]] = {}
    for row in scope_summaries:
        by_scope.setdefault(str(row["scope"]), []).append(row)
    repeat_rows: list[dict[str, Any]] = []
    for scope, rows in sorted(by_scope.items()):
        offset_count = len(rows)
        pass_count = sum(_offset_pass(row) for row in rows)
        any_forbidden = any(bool(row["forbidden_parameter_mutation_detected"]) for row in rows)
        eval_both = [_finite_float(row["eval_both_directional_fraction"]) for row in rows]
        eval_group = [_finite_float(row["eval_group_all_rows_both_positive_fraction"]) for row in rows]
        full_both = [_finite_float(row["full_both_positive_count"]) for row in rows]
        full_group = [_finite_float(row["full_group_all_rows_both_positive_count"]) for row in rows]
        required_pass_count = min(3, int(offset_count))
        repeat_strong = bool(
            not any_forbidden
            and pass_count >= required_pass_count
            and float(np.mean(eval_both)) >= 0.25
            and float(np.mean(eval_group)) >= 0.25
            and float(np.mean(full_both)) > 30.0
            and float(np.mean(full_group)) > 15.0
        )
        if any_forbidden:
            repeat_class = "trainable_scope_repeat_contract_artifact"
        elif repeat_strong:
            repeat_class = "trainable_scope_repeat_strong"
        elif pass_count > 0:
            repeat_class = "trainable_scope_repeat_mixed"
        else:
            repeat_class = "trainable_scope_repeat_negative"
        repeat_rows.append(
            {
                "scope": scope,
                "offset_count": int(offset_count),
                "offset_pass_count": int(pass_count),
                "required_pass_count": int(required_pass_count),
                "mean_eval_both_directional_fraction": float(np.mean(eval_both)) if eval_both else 0.0,
                "mean_eval_group_all_rows_both_positive_fraction": float(np.mean(eval_group)) if eval_group else 0.0,
                "mean_full_both_positive_count": float(np.mean(full_both)) if full_both else 0.0,
                "mean_full_group_all_rows_both_positive_count": float(np.mean(full_group)) if full_group else 0.0,
                "min_eval_both_directional_fraction": float(np.min(eval_both)) if eval_both else 0.0,
                "min_eval_group_all_rows_both_positive_fraction": float(np.min(eval_group)) if eval_group else 0.0,
                "forbidden_parameter_mutation_detected": bool(any_forbidden),
                "repeat_class": repeat_class,
            }
        )
    return repeat_rows


def _top_failed_combo(group_metadata: dict[tuple[int, str], dict[str, Any]]) -> tuple[str, str]:
    scores: dict[tuple[str, str], float] = {}
    for key, metadata in group_metadata.items():
        combo = (str(metadata.get("source_family_pair", "unknown")), str(key[1]))
        scores[combo] = scores.get(combo, 0.0) + _finite_float(metadata.get("failed_combo_boost", 0.0))
    if not scores:
        return "", ""
    return max(scores, key=lambda combo: (scores[combo], combo[0], combo[1]))


def _retention_diagnostic_rows(
    group_rows: list[dict[str, Any]],
    baseline_repeat_groups: dict[tuple[int, int, str], dict[str, Any]],
    group_metadata: dict[tuple[int, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in group_rows:
        if str(row.get("split", "")) != "full":
            continue
        split_offset = int(row["split_offset"])
        pair_id = int(row["pair_id"])
        probe_template = str(row["probe_template"])
        baseline = baseline_repeat_groups.get((split_offset, pair_id, probe_template))
        if baseline is None:
            continue
        metadata = group_metadata.get((pair_id, probe_template), {})
        baseline_positive = _truthy(baseline.get("all_rows_both_positive", False))
        current_positive = _truthy(row.get("all_rows_both_positive", False))
        baseline_margin = _finite_float(baseline.get("group_min_margin", 0.0))
        current_margin = _finite_float(row.get("group_min_margin", 0.0))
        rows.append(
            {
                "split_offset": split_offset,
                "pair_id": pair_id,
                "probe_template": probe_template,
                "source_family_pair": str(metadata.get("source_family_pair", "unknown")),
                "source_fault_pair": str(metadata.get("source_fault_pair", "unknown")),
                "margin_bucket": str(metadata.get("margin_bucket", "unknown")),
                "group_weight": _finite_float(row.get("group_weight", metadata.get("group_weight", 1.0))),
                "baseline_all_rows_both_positive": baseline_positive,
                "current_all_rows_both_positive": current_positive,
                "lost_baseline_positive": bool(baseline_positive and not current_positive),
                "baseline_group_min_margin": baseline_margin,
                "current_group_min_margin": current_margin,
                "group_min_margin_delta": current_margin - baseline_margin,
            }
        )
    return rows


def _bucket_diagnostic_rows(
    group_rows: list[dict[str, Any]],
    group_metadata: dict[tuple[int, str], dict[str, Any]],
    bucket_columns: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, tuple[str, ...]], list[dict[str, Any]]] = {}
    for row in group_rows:
        if str(row.get("split", "")) != "full":
            continue
        key = (int(row["pair_id"]), str(row["probe_template"]))
        bucket = _bucket_key(key, group_metadata, bucket_columns)
        grouped.setdefault((int(row["split_offset"]), bucket), []).append(row)
    rows: list[dict[str, Any]] = []
    for (split_offset, bucket), values in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        margins = [_finite_float(row.get("group_min_margin", 0.0)) for row in values]
        rows.append(
            {
                "split_offset": int(split_offset),
                "bucket": "|".join(bucket),
                "group_count": int(len(values)),
                "all_rows_both_positive_count": int(
                    sum(_truthy(row.get("all_rows_both_positive", False)) for row in values)
                ),
                "group_min_margin_mean": float(np.mean(margins)) if margins else 0.0,
                "group_min_margin_min": float(np.min(margins)) if margins else 0.0,
            }
        )
    return rows


def _train_scope(
    *,
    model: ActorCritic,
    checkpoint_data: dict[str, Any],
    base_state: dict[str, torch.Tensor],
    train_batch: SourceHistoryBatch,
    train_meta_rows: list[dict[str, Any]],
    full_batch: SourceHistoryBatch,
    full_meta_rows: list[dict[str, Any]],
    eval_batch: SourceHistoryBatch,
    eval_meta_rows: list[dict[str, Any]],
    run_dir: Path,
    scope: str,
    split_offset: int,
    steps: int,
    lr: float,
    target_margin: float,
    lambda_group_floor: float,
    lambda_group_balance: float,
    lambda_anchor: float,
    group_weights: dict[tuple[int, str], float] | None,
    group_metadata: dict[tuple[int, str], dict[str, Any]],
    baseline_repeat_groups: dict[tuple[int, int, str], dict[str, Any]],
    robust_minfold: bool,
    bucket_columns: tuple[str, ...],
    lambda_bucket_cvar: float,
    lambda_retention: float,
    retention_margin_eps: float,
    minfold_temperature: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    device = next(model.parameters()).device
    allowed_groups = set(SCOPE_ALLOWED_GROUPS[scope])
    _set_trainable_scope(model, scope)
    trainable_count, frozen_count = _parameter_counts(model)
    optimizer = torch.optim.Adam(_trainable_parameters(model), lr=float(lr))
    train_groups = _group_indices(train_meta_rows)
    train_row_weights = _weights_for_meta_rows(train_meta_rows, group_weights, device)
    trace_rows: list[dict[str, Any]] = []
    for step in range(int(steps)):
        optimizer.zero_grad()
        eval_row = _directional_eval(model, train_batch, target_margin=target_margin, lambda_min=0.0)
        if group_weights is None:
            correct_loss = eval_row.correct_loss
            wrong_loss = eval_row.wrong_loss
            group_floor, group_balance, group_min = _pair_group_loss(
                min_margin=eval_row.min_margin,
                groups=train_groups,
                target_margin=target_margin,
            )
        else:
            correct_loss, wrong_loss = _weighted_directional_losses(
                eval_row,
                train_row_weights,
                target_margin=target_margin,
            )
            group_floor, group_balance, group_min = _weighted_pair_group_loss(
                min_margin=eval_row.min_margin,
                groups=train_groups,
                group_weights=group_weights,
                target_margin=target_margin,
            )
        if robust_minfold:
            bucket_cvar, retention = _robust_minfold_losses(
                min_margin=eval_row.min_margin,
                groups=train_groups,
                group_metadata=group_metadata,
                baseline_repeat_groups=baseline_repeat_groups,
                split_offset=int(split_offset),
                bucket_columns=bucket_columns,
                target_margin=target_margin,
                retention_margin_eps=retention_margin_eps,
                minfold_temperature=minfold_temperature,
            )
        else:
            bucket_cvar = torch.zeros((), dtype=torch.float32, device=device)
            retention = torch.zeros((), dtype=torch.float32, device=device)
        anchor = _parameter_anchor_loss(model, base_state, allowed_groups, device)
        loss = (
            correct_loss
            + wrong_loss
            + float(lambda_group_floor) * group_floor
            + float(lambda_group_balance) * group_balance
            + float(lambda_bucket_cvar) * bucket_cvar
            + float(lambda_retention) * retention
            + float(lambda_anchor) * anchor
        )
        loss.backward()
        optimizer.step()
        trace_rows.append(
            {
                "scope": scope,
                "split_offset": int(split_offset),
                "step": int(step + 1),
                "loss": float(loss.detach().cpu().item()),
                "correct_loss": float(correct_loss.detach().cpu().item()),
                "wrong_history_loss": float(wrong_loss.detach().cpu().item()),
                "group_floor_loss": float(group_floor.detach().cpu().item()),
                "group_balance_loss": float(group_balance.detach().cpu().item()),
                "bucket_cvar_loss": float(bucket_cvar.detach().cpu().item()),
                "retention_loss": float(retention.detach().cpu().item()),
                "group_min_margin_mean": float(group_min.detach().cpu().item()),
                "anchor_loss": float(anchor.detach().cpu().item()),
                "weighted_loss_enabled": bool(group_weights is not None),
                "robust_minfold_enabled": bool(robust_minfold),
                "row_weight_mean": float(train_row_weights.mean().detach().cpu().item())
                if train_row_weights is not None
                else 1.0,
            }
        )

    full_summary, full_rows, full_group_rows = _eval_scope_split(
        model=model,
        batch=full_batch,
        meta_rows=full_meta_rows,
        scope=scope,
        split_offset=split_offset,
        split="full",
        target_margin=target_margin,
        group_weights=group_weights,
    )
    train_summary, train_rows, train_group_rows = _eval_scope_split(
        model=model,
        batch=train_batch,
        meta_rows=train_meta_rows,
        scope=scope,
        split_offset=split_offset,
        split="train",
        target_margin=target_margin,
        group_weights=group_weights,
    )
    eval_summary, eval_rows, eval_group_rows = _eval_scope_split(
        model=model,
        batch=eval_batch,
        meta_rows=eval_meta_rows,
        scope=scope,
        split_offset=split_offset,
        split="eval",
        target_margin=target_margin,
        group_weights=group_weights,
    )
    state_after = _clone_state_dict(model)
    deltas = _parameter_group_delta(base_state, state_after)
    parameter_rows = _parameter_group_rows(
        scope=scope,
        split_offset=split_offset,
        allowed_groups=allowed_groups,
        deltas=deltas,
    )
    forbidden_mutation = any(bool(row["forbidden_mutation"]) for row in parameter_rows)
    checkpoint_path = run_dir / "checkpoints" / f"offset_{int(split_offset)}_{scope}_candidate.pt"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        model=model,
        path=checkpoint_path,
        metadata={
            "source_history_trainable_scope_probe": {
                "scope": scope,
                "split_offset": int(split_offset),
                "run_dir": str(run_dir),
                "steps": int(steps),
                "lr": float(lr),
                "target_margin": float(target_margin),
                "allowed_groups": sorted(allowed_groups),
                "weighted_loss_enabled": bool(group_weights is not None),
                "robust_minfold_enabled": bool(robust_minfold),
            }
        },
    )
    scope_summary = {
        "scope": scope,
        "split_offset": int(split_offset),
        "checkpoint": str(checkpoint_path),
        "steps": int(steps),
        "lr": float(lr),
        "target_margin": float(target_margin),
        "lambda_group_floor": float(lambda_group_floor),
        "lambda_group_balance": float(lambda_group_balance),
        "lambda_anchor": float(lambda_anchor),
        "trainable_parameter_count": int(trainable_count),
        "frozen_parameter_count": int(frozen_count),
        "allowed_parameter_groups": "|".join(sorted(allowed_groups)),
        "forbidden_parameter_mutation_detected": bool(forbidden_mutation),
        "weighted_loss_enabled": bool(group_weights is not None),
        "robust_minfold_enabled": bool(robust_minfold),
        "lambda_bucket_cvar": float(lambda_bucket_cvar),
        "lambda_retention": float(lambda_retention),
        "retention_margin_eps": float(retention_margin_eps),
        "minfold_temperature": float(minfold_temperature),
        **_prefixed("full", full_summary),
        **_prefixed("train", train_summary),
        **_prefixed("eval", eval_summary),
    }
    for row in parameter_rows:
        group = str(row["parameter_group"])
        scope_summary[f"{group}_l2"] = float(row["l2"])
        scope_summary[f"{group}_changed"] = bool(row["changed"])
    scope_summary["scope_class"] = _classify_scope(scope_summary)
    write_json(run_dir / f"offset_{int(split_offset)}_{scope}_summary.json", scope_summary)
    rows = full_rows + train_rows + eval_rows
    group_rows = full_group_rows + train_group_rows + eval_group_rows
    return scope_summary, rows, group_rows, parameter_rows, trace_rows


def classify_probe(repeat_summaries: list[dict[str, Any]]) -> tuple[str, str]:
    classes = {str(row["repeat_class"]) for row in repeat_summaries}
    if "trainable_scope_repeat_contract_artifact" in classes:
        return "source_history_trainable_scope_repeat_contract_artifact", "repair mutation guard before rerun"
    if "trainable_scope_repeat_strong" in classes:
        return "source_history_trainable_scope_repeat_strong", "route to result audit and proof-retention design"
    if "trainable_scope_repeat_mixed" in classes:
        return "source_history_trainable_scope_repeat_mixed", "route to result audit and scope/corpus decision"
    return "source_history_trainable_scope_repeat_negative", "route to corpus refresh or sequence preference design"


def run_trainable_scope_probe(
    *,
    checkpoint_path: Path,
    history_run_dir: Path,
    intervention_run_dir: Path,
    run_dir: Path,
    device: str = "auto",
    steps: int = 400,
    lr: float = 2e-4,
    target_margin: float = 0.05,
    lambda_group_floor: float = 4.0,
    lambda_group_balance: float = 0.5,
    lambda_anchor: float = 0.001,
    scopes: Iterable[str] = DEFAULT_SCOPES,
    split_mod: int = 5,
    split_offsets: Iterable[int] = (0,),
    split_plan_path: Path | None = None,
    group_weight_rows_path: Path | None = None,
    baseline_repeat_run_dir: Path | None = None,
    robust_minfold: bool = False,
    bucket_columns: Iterable[str] = ("source_family_pair", "probe_template", "margin_bucket"),
    lambda_bucket_cvar: float = 0.0,
    lambda_retention: float = 0.0,
    retention_margin_eps: float = 0.02,
    minfold_temperature: float = 0.25,
) -> dict[str, Any]:
    checkpoint_path = Path(checkpoint_path)
    history_run_dir = Path(history_run_dir)
    intervention_run_dir = Path(intervention_run_dir)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)

    scope_names = [str(scope) for scope in scopes]
    offset_values = [int(offset) for offset in split_offsets]
    unknown_scopes = [scope for scope in scope_names if scope not in SCOPE_ALLOWED_GROUPS]
    if unknown_scopes:
        raise ValueError(f"unknown trainable scopes: {unknown_scopes}")
    if int(split_mod) < 2:
        raise ValueError("split_mod must be at least 2")
    if not offset_values:
        raise ValueError("at least one split offset is required")
    if any(offset < 0 or offset >= int(split_mod) for offset in offset_values):
        raise ValueError("split offsets must satisfy 0 <= offset < split_mod")

    base_model, base_checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    contract_ok, contract_reason = _checkpoint_contract(base_model, base_checkpoint)
    if not contract_ok:
        raise ValueError(f"checkpoint contract violation: {contract_reason}")
    base_model.eval()
    base_state = _clone_state_dict(base_model)
    full_batch = _load_source_history_batch(
        model=base_model,
        history_run_dir=history_run_dir,
        intervention_run_dir=intervention_run_dir,
        device=resolved_device,
    )
    full_meta_rows = _source_history_meta_rows(history_run_dir)
    split_plan = _load_split_plan(split_plan_path) if split_plan_path is not None else None
    group_weights: dict[tuple[int, str], float] | None = None
    pair_specific_weight_used = False
    max_group_weight = 0.0
    if group_weight_rows_path is not None:
        group_weights, pair_specific_weight_used, max_group_weight = _load_group_weights(group_weight_rows_path)
    split_plan_used = split_plan is not None
    group_weights_used = group_weights is not None
    bucket_column_values = tuple(str(column) for column in bucket_columns if str(column))
    group_metadata = _load_group_metadata(group_weight_rows_path)
    baseline_repeat_groups = _load_baseline_repeat_groups(baseline_repeat_run_dir, scope_names[0])
    if robust_minfold and not group_metadata:
        raise ValueError("robust_minfold requires --group-weight-rows with source metadata")
    if robust_minfold and not baseline_repeat_groups:
        raise ValueError("robust_minfold requires --baseline-repeat-run-dir")

    scope_summaries: list[dict[str, Any]] = []
    all_split_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
    all_parameter_rows: list[dict[str, Any]] = []
    all_trace_rows: list[dict[str, Any]] = []
    split_pair_counts: list[dict[str, Any]] = []
    for split_offset in offset_values:
        if split_plan is None:
            split_rows = _split_rows(full_meta_rows, split_mod=int(split_mod), split_offset=int(split_offset))
        else:
            split_rows = _split_rows_from_plan(
                full_meta_rows,
                split_plan,
                split_mod=int(split_mod),
                split_offset=int(split_offset),
            )
        train_indices = _indices_for_split(split_rows, "train")
        eval_indices = _indices_for_split(split_rows, "eval")
        if not train_indices or not eval_indices:
            raise ValueError(f"split offset {split_offset} produced an empty train or eval split")
        train_batch = _slice_batch(full_batch, train_indices)
        eval_batch = _slice_batch(full_batch, eval_indices)
        train_meta_rows = _slice_meta(full_meta_rows, train_indices)
        eval_meta_rows = _slice_meta(full_meta_rows, eval_indices)
        pair_split: dict[int, str] = {int(row["pair_id"]): str(row["split"]) for row in split_rows}
        train_pairs = sorted(pair_id for pair_id, split in pair_split.items() if split == "train")
        eval_pairs = sorted(pair_id for pair_id, split in pair_split.items() if split == "eval")
        if set(train_pairs) & set(eval_pairs):
            raise ValueError(f"pair split is not disjoint for split offset {split_offset}")
        split_pair_counts.append(
            {
                "split_offset": int(split_offset),
                "train_row_count": int(len(train_indices)),
                "eval_row_count": int(len(eval_indices)),
                "train_pair_count": int(len(train_pairs)),
                "eval_pair_count": int(len(eval_pairs)),
            }
        )
        all_split_rows.extend(split_rows)
        for scope in scope_names:
            model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
            contract_ok, contract_reason = _checkpoint_contract(model, checkpoint_data)
            if not contract_ok:
                raise ValueError(f"{scope} checkpoint contract violation: {contract_reason}")
            model.eval()
            scope_summary, rows, group_rows, parameter_rows, trace_rows = _train_scope(
                model=model,
                checkpoint_data=checkpoint_data,
                base_state=base_state,
                train_batch=train_batch,
                train_meta_rows=train_meta_rows,
                full_batch=full_batch,
                full_meta_rows=full_meta_rows,
                eval_batch=eval_batch,
                eval_meta_rows=eval_meta_rows,
                run_dir=run_dir,
                scope=scope,
                split_offset=int(split_offset),
                steps=steps,
                lr=lr,
                target_margin=target_margin,
                lambda_group_floor=lambda_group_floor,
                lambda_group_balance=lambda_group_balance,
                lambda_anchor=lambda_anchor,
                group_weights=group_weights,
                group_metadata=group_metadata,
                baseline_repeat_groups=baseline_repeat_groups,
                robust_minfold=robust_minfold,
                bucket_columns=bucket_column_values,
                lambda_bucket_cvar=lambda_bucket_cvar,
                lambda_retention=lambda_retention,
                retention_margin_eps=retention_margin_eps,
                minfold_temperature=minfold_temperature,
            )
            scope_summaries.append(scope_summary)
            all_rows.extend(rows)
            all_group_rows.extend(group_rows)
            all_parameter_rows.extend(parameter_rows)
            all_trace_rows.extend(trace_rows)

    repeat_summaries = _repeat_summaries(scope_summaries)
    write_csv_rows(run_dir / "scope_summaries.csv", scope_summaries)
    write_csv_rows(run_dir / "repeat_summaries.csv", repeat_summaries)
    write_csv_rows(run_dir / "split_rows.csv", all_split_rows)
    write_csv_rows(run_dir / "directional_rows.csv", all_rows)
    write_csv_rows(run_dir / "group_rows.csv", all_group_rows)
    write_csv_rows(run_dir / "parameter_group_delta.csv", all_parameter_rows)
    write_csv_rows(run_dir / "train_trace.csv", all_trace_rows)
    result_class, recommended_next_step = classify_probe(repeat_summaries)
    best_scope_row = sorted(
        scope_summaries,
        key=lambda row: (
            -float(row["eval_group_all_rows_both_positive_fraction"]),
            -float(row["eval_both_directional_fraction"]),
            -float(row["full_group_all_rows_both_positive_count"]),
            -float(row["full_both_positive_count"]),
        ),
    )[0]
    best_repeat = sorted(
        repeat_summaries,
        key=lambda row: (
            -int(row["offset_pass_count"]),
            -float(row["mean_eval_group_all_rows_both_positive_fraction"]),
            -float(row["mean_eval_both_directional_fraction"]),
            -float(row["mean_full_group_all_rows_both_positive_count"]),
        ),
    )[0]
    baseline_pass_offsets = _baseline_pass_offsets(baseline_repeat_run_dir, str(best_repeat["scope"]))
    current_pass_offsets = {
        int(row["split_offset"])
        for row in scope_summaries
        if str(row["scope"]) == str(best_repeat["scope"]) and _offset_pass(row)
    }
    baseline_pass_lost_offsets = sorted(baseline_pass_offsets - current_pass_offsets)
    retention_rows = _retention_diagnostic_rows(all_group_rows, baseline_repeat_groups, group_metadata)
    bucket_rows = _bucket_diagnostic_rows(all_group_rows, group_metadata, bucket_column_values)
    top_source_family, top_probe_template = _top_failed_combo(group_metadata)
    top_current_positive = 0
    top_baseline_positive = 0
    for row in all_group_rows:
        if str(row.get("split", "")) != "full":
            continue
        pair_id = int(row["pair_id"])
        probe_template = str(row["probe_template"])
        metadata = group_metadata.get((pair_id, probe_template), {})
        if str(metadata.get("source_family_pair", "")) != top_source_family or probe_template != top_probe_template:
            continue
        top_current_positive += int(_truthy(row.get("all_rows_both_positive", False)))
        baseline = baseline_repeat_groups.get((int(row["split_offset"]), pair_id, probe_template))
        top_baseline_positive += int(bool(baseline and _truthy(baseline.get("all_rows_both_positive", False))))
    any_forbidden = any(bool(row["forbidden_parameter_mutation_detected"]) for row in scope_summaries)
    total_train_rows = int(sum(int(row["train_row_count"]) for row in split_pair_counts))
    total_eval_rows = int(sum(int(row["eval_row_count"]) for row in split_pair_counts))
    summary = {
        "run_type": "source_history_trainable_scope_probe",
        "checkpoint": str(checkpoint_path),
        "history_run_dir": str(history_run_dir),
        "intervention_run_dir": str(intervention_run_dir),
        "steps": int(steps),
        "lr": float(lr),
        "target_margin": float(target_margin),
        "lambda_group_floor": float(lambda_group_floor),
        "lambda_group_balance": float(lambda_group_balance),
        "lambda_anchor": float(lambda_anchor),
        "scope_count": int(len(scope_summaries)),
        "base_scope_count": int(len(scope_names)),
        "offset_count": int(len(offset_values)),
        "split_mod": int(split_mod),
        "split_offsets": "|".join(str(offset) for offset in offset_values),
        "scopes": "|".join(scope_names),
        "split_plan_used": bool(split_plan_used),
        "split_plan_path": str(split_plan_path) if split_plan_path is not None else "",
        "group_weights_used": bool(group_weights_used),
        "group_weight_rows_path": str(group_weight_rows_path) if group_weight_rows_path is not None else "",
        "weighted_loss_enabled": bool(group_weights_used),
        "robust_minfold_used": bool(robust_minfold),
        "baseline_repeat_run_dir": str(baseline_repeat_run_dir) if baseline_repeat_run_dir is not None else "",
        "bucket_columns": "|".join(bucket_column_values),
        "lambda_bucket_cvar": float(lambda_bucket_cvar),
        "lambda_retention": float(lambda_retention),
        "retention_margin_eps": float(retention_margin_eps),
        "minfold_temperature": float(minfold_temperature),
        "pair_specific_weight_used": bool(pair_specific_weight_used),
        "max_group_weight": float(max_group_weight),
        "train_row_count": int(split_pair_counts[0]["train_row_count"]),
        "eval_row_count": int(split_pair_counts[0]["eval_row_count"]),
        "total_train_row_count": total_train_rows,
        "total_eval_row_count": total_eval_rows,
        "full_row_count": int(len(full_meta_rows)),
        "train_pair_count": int(split_pair_counts[0]["train_pair_count"]),
        "eval_pair_count": int(split_pair_counts[0]["eval_pair_count"]),
        "pair_split_disjoint": True,
        "best_scope": str(best_scope_row["scope"]),
        "best_scope_class": str(best_scope_row["scope_class"]),
        "best_split_offset": int(best_scope_row["split_offset"]),
        "best_eval_group_all_rows_both_positive_fraction": float(
            best_scope_row["eval_group_all_rows_both_positive_fraction"]
        ),
        "best_eval_both_directional_fraction": float(best_scope_row["eval_both_directional_fraction"]),
        "best_full_group_all_rows_both_positive_count": int(
            best_scope_row["full_group_all_rows_both_positive_count"]
        ),
        "best_full_both_positive_count": int(best_scope_row["full_both_positive_count"]),
        "best_repeat_scope": str(best_repeat["scope"]),
        "best_repeat_class": str(best_repeat["repeat_class"]),
        "best_repeat_offset_pass_count": int(best_repeat["offset_pass_count"]),
        "best_repeat_required_pass_count": int(best_repeat["required_pass_count"]),
        "best_repeat_mean_eval_group_all_rows_both_positive_fraction": float(
            best_repeat["mean_eval_group_all_rows_both_positive_fraction"]
        ),
        "best_repeat_mean_eval_both_directional_fraction": float(
            best_repeat["mean_eval_both_directional_fraction"]
        ),
        "best_repeat_mean_full_group_all_rows_both_positive_count": float(
            best_repeat["mean_full_group_all_rows_both_positive_count"]
        ),
        "best_repeat_mean_full_both_positive_count": float(best_repeat["mean_full_both_positive_count"]),
        "baseline_pass_offsets": "|".join(str(offset) for offset in sorted(baseline_pass_offsets)),
        "current_pass_offsets": "|".join(str(offset) for offset in sorted(current_pass_offsets)),
        "baseline_pass_lost_offsets": "|".join(str(offset) for offset in baseline_pass_lost_offsets),
        "baseline_pass_lost_offset_count": int(len(baseline_pass_lost_offsets)),
        "repeat_offset_pass_count": int(best_repeat["offset_pass_count"]),
        "top_failed_source_family_pair": top_source_family,
        "top_failed_probe_template": top_probe_template,
        "top_failed_combo_baseline_positive_count": int(top_baseline_positive),
        "top_failed_combo_current_positive_count": int(top_current_positive),
        "top_failed_combo_positive_delta": int(top_current_positive - top_baseline_positive),
        "forbidden_parameter_mutation_detected": bool(any_forbidden),
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
        "scope_summaries_csv": run_dir / "scope_summaries.csv",
        "repeat_summaries_csv": run_dir / "repeat_summaries.csv",
        "split_rows_csv": run_dir / "split_rows.csv",
        "directional_rows_csv": run_dir / "directional_rows.csv",
        "group_rows_csv": run_dir / "group_rows.csv",
        "parameter_group_delta_csv": run_dir / "parameter_group_delta.csv",
        "train_trace_csv": run_dir / "train_trace.csv",
        "weighted_group_diagnostics_csv": run_dir / "weighted_group_diagnostics.csv",
        "retention_group_diagnostics_csv": run_dir / "retention_group_diagnostics.csv",
        "bucket_cvar_diagnostics_csv": run_dir / "bucket_cvar_diagnostics.csv",
    }
    if group_weights is not None:
        weight_rows = [
            {
                "pair_id": int(pair_id),
                "probe_template": str(probe_template),
                "group_weight": float(weight),
                "pair_specific_weight_used": False,
            }
            for (pair_id, probe_template), weight in sorted(group_weights.items())
        ]
        write_csv_rows(run_dir / "weighted_group_diagnostics.csv", weight_rows)
    else:
        write_csv_rows(run_dir / "weighted_group_diagnostics.csv", [])
    write_csv_rows(run_dir / "retention_group_diagnostics.csv", retention_rows)
    write_csv_rows(run_dir / "bucket_cvar_diagnostics.csv", bucket_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run source-history trainable-scope diagnostic probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--history-run-dir", type=Path, required=True)
    parser.add_argument("--intervention-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--target-margin", type=float, default=0.05)
    parser.add_argument("--lambda-group-floor", type=float, default=4.0)
    parser.add_argument("--lambda-group-balance", type=float, default=0.5)
    parser.add_argument("--lambda-anchor", type=float, default=0.001)
    parser.add_argument("--scopes", type=str, default=",".join(DEFAULT_SCOPES))
    parser.add_argument("--split-mod", type=int, default=5)
    parser.add_argument("--split-offsets", type=str, default="0")
    parser.add_argument("--split-plan", type=Path, default=None)
    parser.add_argument("--group-weight-rows", type=Path, default=None)
    parser.add_argument("--baseline-repeat-run-dir", type=Path, default=None)
    parser.add_argument("--robust-minfold", action="store_true")
    parser.add_argument("--bucket-columns", type=str, default="source_family_pair,probe_template,margin_bucket")
    parser.add_argument("--lambda-bucket-cvar", type=float, default=0.0)
    parser.add_argument("--lambda-retention", type=float, default=0.0)
    parser.add_argument("--retention-margin-eps", type=float, default=0.02)
    parser.add_argument("--minfold-temperature", type=float, default=0.25)
    args = parser.parse_args()
    scopes = [scope.strip() for scope in str(args.scopes).split(",") if scope.strip()]
    split_offsets = [int(offset.strip()) for offset in str(args.split_offsets).split(",") if offset.strip()]
    bucket_columns = [column.strip() for column in str(args.bucket_columns).split(",") if column.strip()]
    summary = run_trainable_scope_probe(
        checkpoint_path=args.checkpoint,
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
        scopes=scopes,
        split_mod=args.split_mod,
        split_offsets=split_offsets,
        split_plan_path=args.split_plan,
        group_weight_rows_path=args.group_weight_rows,
        baseline_repeat_run_dir=args.baseline_repeat_run_dir,
        robust_minfold=args.robust_minfold,
        bucket_columns=bucket_columns,
        lambda_bucket_cvar=args.lambda_bucket_cvar,
        lambda_retention=args.lambda_retention,
        retention_margin_eps=args.retention_margin_eps,
        minfold_temperature=args.minfold_temperature,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={args.run_dir}")


if __name__ == "__main__":
    main()
