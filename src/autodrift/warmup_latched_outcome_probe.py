"""No-training outcome probe for warmup-latched history candidates."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    TracePoint,
    collect_fault_trace_window,
    fault_map_from_config,
    roll_hidden_over_observations,
)
from autodrift.causal_history_candidate_outcome_probe import replay_probe_variant
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import ActorCritic, resolve_device


CONTROL_VARIANTS = ("reset_hidden", "zero_current_response")
WARMUP_HISTORY_VARIANTS = (
    "delayed_warmup_history_8",
    "delayed_warmup_history_16",
    "wrong_warmup_history_same_reveal",
    "same_recent_wrong_warmup_history",
    "warmup_removed",
    "warmup_shortened_8",
)
ALL_VARIANTS = (*CONTROL_VARIANTS, *WARMUP_HISTORY_VARIANTS)


def select_warmup_candidate_rows(
    rows: pd.DataFrame,
    *,
    max_candidate_rows: int,
    per_capability_pair_cap: int,
) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()
    frame = rows.copy()
    if "matched_or_bucketed_reveal_pass" in frame.columns:
        frame = frame[frame["matched_or_bucketed_reveal_pass"].astype(bool)].copy()
    if frame.empty:
        return frame
    if "capability_pair" not in frame.columns:
        frame["capability_pair"] = frame.apply(
            lambda row: f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}",
            axis=1,
        )
    sort_columns = [
        column
        for column in ("matched_current_pass", "current_hidden_l2", "warmup_history_l2")
        if column in frame.columns
    ]
    if sort_columns:
        ascending = [False] * len(sort_columns)
        frame = frame.sort_values(sort_columns, ascending=ascending)
    selected: list[pd.DataFrame] = []
    for _, group in frame.groupby("capability_pair", observed=True):
        selected.append(group.head(max(1, int(per_capability_pair_cap))))
    if not selected:
        return frame.head(0)
    output = pd.concat(selected, ignore_index=True)
    if int(max_candidate_rows) > 0:
        output = output.head(int(max_candidate_rows))
    return output.reset_index(drop=True)


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if np.isfinite(output) else default


def _first_action(result: dict[str, Any]) -> np.ndarray:
    return np.asarray(
        [
            result.get("first_steer", float("nan")),
            result.get("first_throttle", float("nan")),
            result.get("first_brake", float("nan")),
        ],
        dtype=np.float32,
    )


def _hidden_at_delay(trace: list[TracePoint], delay: int) -> torch.Tensor:
    index = max(0, len(trace) - 1 - int(delay))
    return trace[index].hidden.detach().clone()


def _hidden_from_shortened_warmup(
    model: ActorCritic,
    trace: list[TracePoint],
    *,
    length: int,
    device: torch.device,
) -> torch.Tensor:
    hidden = model.initial_hidden(1, device)
    observations = [point.observation for point in trace[max(0, len(trace) - 1 - int(length)) : -1]]
    return roll_hidden_over_observations(model, hidden, observations, device)


def build_warmup_variant_hiddens(
    *,
    model: ActorCritic,
    preferred_trace: list[TracePoint],
    wrong_trace: list[TracePoint],
    recent_window_length: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    preferred_current = preferred_trace[-1]
    wrong_current = wrong_trace[-1]
    reset_hidden = model.initial_hidden(1, device)
    recent = max(1, int(recent_window_length))
    start_index = max(0, len(wrong_trace) - 1 - recent)
    wrong_start = wrong_trace[start_index].hidden.detach().clone()
    preferred_recent_observations = [point.observation for point in preferred_trace[start_index:-1]]
    return {
        "reset_hidden": reset_hidden,
        "zero_current_response": preferred_current.hidden.detach().clone(),
        "delayed_warmup_history_8": _hidden_at_delay(preferred_trace, 8),
        "delayed_warmup_history_16": _hidden_at_delay(preferred_trace, 16),
        "wrong_warmup_history_same_reveal": wrong_current.hidden.detach().clone(),
        "same_recent_wrong_warmup_history": roll_hidden_over_observations(
            model,
            wrong_start,
            preferred_recent_observations,
            device,
        ),
        "warmup_removed": reset_hidden.detach().clone(),
        "warmup_shortened_8": _hidden_from_shortened_warmup(model, preferred_trace, length=8, device=device),
    }


def source_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "unique_source_seeds": 0,
            "unique_capability_pairs": 0,
            "unique_reveal_buckets": 0,
            "unique_variants": 0,
            "max_single_seed_share": None,
            "max_single_capability_pair_share": None,
        }
    frame = pd.DataFrame(rows)
    seed_counts = frame["seed"].value_counts() if "seed" in frame.columns else pd.Series(dtype=int)
    pair_counts = frame["capability_pair"].value_counts() if "capability_pair" in frame.columns else pd.Series(dtype=int)
    total = float(len(frame))
    return {
        "rows": int(len(frame)),
        "unique_source_seeds": int(frame["seed"].nunique()) if "seed" in frame.columns else 0,
        "unique_capability_pairs": int(frame["capability_pair"].nunique()) if "capability_pair" in frame.columns else 0,
        "unique_reveal_buckets": int(frame["preferred_reveal_bucket"].nunique())
        if "preferred_reveal_bucket" in frame.columns
        else 0,
        "unique_variants": int(frame["variant"].nunique()) if "variant" in frame.columns else 0,
        "max_single_seed_share": float(seed_counts.max() / total) if len(seed_counts) else None,
        "max_single_capability_pair_share": float(pair_counts.max() / total) if len(pair_counts) else None,
    }


def summarize_groups(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    output: list[dict[str, Any]] = []
    for group_key, group in frame.groupby(list(keys), observed=True):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        item = {key: value for key, value in zip(keys, group_key, strict=True)}
        item.update(
            {
                "rows": int(len(group)),
                "outcome_critical_rows": int(group["outcome_critical"].astype(bool).sum()),
                "warmup_history_positive_rows": int(group["warmup_history_positive"].astype(bool).sum()),
                "success_drop_rate": float(group["success_drop"].astype(bool).mean()),
                "margin_gap_mean": float(group["margin_gap"].astype(float).mean()),
                "sequence_action_l2_mean": float(group["sequence_action_l2_mean"].astype(float).mean()),
                "unique_seeds": int(group["seed"].nunique()),
                "unique_capability_pairs": int(group["capability_pair"].nunique()),
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique()),
            }
        )
        output.append(item)
    return output


def classify_warmup_outcome_probe_result(
    *,
    total_rows: int,
    normal_failed_rows: int,
    warmup_history_positive_rows: int,
    accepted_reset_rows: int,
    accepted_zero_current_rows: int,
    action_critical_rows: int,
    accepted_history_seeds: int,
    accepted_history_capability_pairs: int,
    accepted_history_reveal_buckets: int,
) -> str:
    if total_rows == 0:
        return "warmup_latched_outcome_no_rows"
    if normal_failed_rows >= total_rows:
        return "warmup_latched_outcome_normal_failed"
    positive = (
        int(warmup_history_positive_rows) >= 48
        and int(accepted_history_seeds) >= 12
        and int(accepted_history_capability_pairs) >= 6
        and int(accepted_history_reveal_buckets) >= 4
    )
    if positive:
        return "warmup_latched_outcome_positive_public"
    if warmup_history_positive_rows > 0:
        return "warmup_latched_outcome_history_sparse"
    if accepted_reset_rows > 0 or accepted_zero_current_rows > 0:
        return "warmup_latched_outcome_reset_or_current_only"
    if action_critical_rows > 0:
        return "warmup_latched_outcome_action_only"
    return "warmup_latched_outcome_no_signal"


def run_warmup_latched_outcome_probe(
    *,
    checkpoint_path: Path,
    config_path: Path,
    candidate_rows_path: Path,
    max_candidate_rows: int,
    per_capability_pair_cap: int,
    history_length: int,
    recent_window_length: int,
    max_continuation_steps: int,
    min_margin_gap: float,
    min_sequence_action_l2: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    candidate_frame = pd.read_csv(candidate_rows_path)
    selected_rows = select_warmup_candidate_rows(
        candidate_frame,
        max_candidate_rows=max_candidate_rows,
        per_capability_pair_cap=per_capability_pair_cap,
    )
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    response_dim = response_feature_dim_for_model(model)
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    outcome_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for selected_index, row in selected_rows.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        reveal_step = int(row["reveal_step"])
        capability_pair = str(row.get("capability_pair", f"{row.get('preferred_fault_family', '')}->{row.get('wrong_fault_family', '')}"))
        try:
            preferred_trace = trace_for(seed, preferred_fault, reveal_step)
            wrong_trace = trace_for(seed, wrong_fault, reveal_step)
        except Exception as exc:  # pragma: no cover - surfaced in artifacts.
            rejected_rows.append(
                {
                    "selected_index": int(selected_index),
                    "source_index": int(row.get("source_index", selected_index)),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "capability_pair": capability_pair,
                    "rejection_reason": "trace_reconstruction_failed",
                    "error": str(exc),
                }
            )
            continue

        preferred_snapshot = preferred_trace[-1]
        normal, normal_actions = replay_probe_variant(
            model=model,
            snapshot=preferred_snapshot,
            variant="normal",
            initial_hidden=preferred_snapshot.hidden,
            max_continuation_steps=max_continuation_steps,
            normal_first_action=None,
            normal_actions=None,
            response_dim=response_dim,
            device=resolved_device,
        )
        normal_first_action = _first_action(normal)
        normal_success = bool(normal.get("success", False))
        normal_margin = _finite(normal.get("min_clearance_margin"))
        normal_viable = bool(normal_success and np.isfinite(normal_margin) and normal_margin >= 0.0)
        variant_hiddens = build_warmup_variant_hiddens(
            model=model,
            preferred_trace=preferred_trace,
            wrong_trace=wrong_trace,
            recent_window_length=recent_window_length,
            device=resolved_device,
        )
        for variant in ALL_VARIANTS:
            result, _ = replay_probe_variant(
                model=model,
                snapshot=preferred_snapshot,
                variant=variant,
                initial_hidden=variant_hiddens[variant],
                max_continuation_steps=max_continuation_steps,
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                response_dim=response_dim,
                device=resolved_device,
            )
            variant_margin = _finite(result.get("min_clearance_margin"))
            margin_gap = (
                float(normal_margin - variant_margin)
                if np.isfinite(normal_margin) and np.isfinite(variant_margin)
                else float("nan")
            )
            success_drop = bool(normal_success and not bool(result.get("success", False)))
            sequence_action_l2 = _finite(result.get("action_trajectory_distance_mean"), default=0.0)
            first_action_l2 = _finite(result.get("first_action_distance"), default=0.0)
            sequence_action_critical = bool(sequence_action_l2 >= float(min_sequence_action_l2))
            outcome_critical = bool(
                normal_viable
                and sequence_action_critical
                and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap)))
            )
            warmup_history_positive = bool(outcome_critical and variant in WARMUP_HISTORY_VARIANTS)
            outcome_rows.append(
                {
                    "selected_index": int(selected_index),
                    "source_index": int(row.get("source_index", selected_index)),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "preferred_fault": preferred_fault,
                    "preferred_fault_family": str(row.get("preferred_fault_family", "")),
                    "wrong_fault": wrong_fault,
                    "wrong_fault_family": str(row.get("wrong_fault_family", "")),
                    "capability_pair": capability_pair,
                    "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
                    "wrong_reveal_bucket": str(row.get("wrong_reveal_bucket", "")),
                    "matched_current_pass": bool(row.get("matched_current_pass", False)),
                    "bucketed_current_pass": bool(row.get("bucketed_current_pass", False)),
                    "variant": variant,
                    "normal_success": normal_success,
                    "variant_success": bool(result.get("success", False)),
                    "success_drop": success_drop,
                    "normal_margin": normal_margin,
                    "variant_margin": variant_margin,
                    "margin_gap": margin_gap,
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "variant_terminal_reason": str(result.get("terminal_reason", "")),
                    "first_action_l2": first_action_l2,
                    "sequence_action_l2_mean": sequence_action_l2,
                    "sequence_action_l2_max": _finite(result.get("action_trajectory_distance_max"), default=0.0),
                    "sequence_action_critical": sequence_action_critical,
                    "outcome_critical": outcome_critical,
                    "warmup_history_positive": warmup_history_positive,
                }
            )

    accepted = [row for row in outcome_rows if bool(row.get("outcome_critical", False))]
    accepted_history = [row for row in outcome_rows if bool(row.get("warmup_history_positive", False))]
    accepted_reset = [row for row in accepted if str(row.get("variant", "")) == "reset_hidden"]
    accepted_zero_current = [row for row in accepted if str(row.get("variant", "")) == "zero_current_response"]
    action_critical = [row for row in outcome_rows if bool(row.get("sequence_action_critical", False))]
    normal_failed = [
        row
        for row in outcome_rows
        if (not bool(row.get("normal_success", False))) or _finite(row.get("normal_margin")) < 0.0
    ]
    accepted_history_diversity = source_diversity(accepted_history)
    result_class = classify_warmup_outcome_probe_result(
        total_rows=len(outcome_rows),
        normal_failed_rows=len(normal_failed),
        warmup_history_positive_rows=len(accepted_history),
        accepted_reset_rows=len(accepted_reset),
        accepted_zero_current_rows=len(accepted_zero_current),
        action_critical_rows=len(action_critical),
        accepted_history_seeds=int(accepted_history_diversity["unique_source_seeds"]),
        accepted_history_capability_pairs=int(accepted_history_diversity["unique_capability_pairs"]),
        accepted_history_reveal_buckets=int(accepted_history_diversity["unique_reveal_buckets"]),
    )
    checksum_after = model_parameter_checksum(model)
    actor_parameters_changed = bool(str(checksum_after) != str(checksum_before))
    variant_summary = summarize_groups(outcome_rows, ("variant",))
    capability_pair_summary = summarize_groups(outcome_rows, ("capability_pair",))
    reveal_bucket_summary = summarize_groups(outcome_rows, ("preferred_reveal_bucket",))

    write_csv_rows(run_dir / "selected_candidate_rows.csv", selected_rows.to_dict("records"))
    write_csv_rows(run_dir / "outcome_rows.csv", outcome_rows)
    write_csv_rows(run_dir / "accepted_outcome_rows.csv", accepted)
    write_csv_rows(run_dir / "accepted_warmup_history_rows.csv", accepted_history)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "capability_pair_summary.csv", capability_pair_summary)
    write_csv_rows(run_dir / "reveal_bucket_summary.csv", reveal_bucket_summary)
    summary = {
        "run_type": "warmup_latched_outcome_probe",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "candidate_rows": candidate_rows_path,
        "selected_candidate_rows": int(len(selected_rows)),
        "max_candidate_rows": int(max_candidate_rows),
        "per_capability_pair_cap": int(per_capability_pair_cap),
        "history_length": int(history_length),
        "recent_window_length": int(recent_window_length),
        "max_continuation_steps": int(max_continuation_steps),
        "min_margin_gap": float(min_margin_gap),
        "min_sequence_action_l2": float(min_sequence_action_l2),
        "outcome_rows": int(len(outcome_rows)),
        "accepted_outcome_rows": int(len(accepted)),
        "warmup_history_positive_rows": int(len(accepted_history)),
        "accepted_reset_rows": int(len(accepted_reset)),
        "accepted_zero_current_rows": int(len(accepted_zero_current)),
        "action_critical_rows": int(len(action_critical)),
        "normal_failed_rows": int(len(normal_failed)),
        "rejected_rows": int(len(rejected_rows)),
        "accepted_warmup_history_diversity": accepted_history_diversity,
        "accepted_outcome_diversity": source_diversity(accepted),
        "evaluated_diversity": source_diversity(outcome_rows),
        "variant_count": int(len({str(row.get("variant", "")) for row in outcome_rows})),
        "result_class": result_class,
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
        "selected_candidate_rows_csv": run_dir / "selected_candidate_rows.csv",
        "outcome_rows_csv": run_dir / "outcome_rows.csv",
        "accepted_outcome_rows_csv": run_dir / "accepted_outcome_rows.csv",
        "accepted_warmup_history_rows_csv": run_dir / "accepted_warmup_history_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "capability_pair_summary_csv": run_dir / "capability_pair_summary.csv",
        "reveal_bucket_summary_csv": run_dir / "reveal_bucket_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-training warmup-latched outcome intervention probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--candidate-rows", type=Path, required=True)
    parser.add_argument("--max-candidate-rows", type=int, default=384)
    parser.add_argument("--per-capability-pair-cap", type=int, default=48)
    parser.add_argument("--history-length", type=int, default=36)
    parser.add_argument("--recent-window-length", type=int, default=4)
    parser.add_argument("--max-continuation-steps", type=int, default=48)
    parser.add_argument("--min-margin-gap", type=float, default=0.02)
    parser.add_argument("--min-sequence-action-l2", type=float, default=0.025)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="warmup_latched_outcome_probe")
    summary = run_warmup_latched_outcome_probe(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        candidate_rows_path=args.candidate_rows,
        max_candidate_rows=args.max_candidate_rows,
        per_capability_pair_cap=args.per_capability_pair_cap,
        history_length=args.history_length,
        recent_window_length=args.recent_window_length,
        max_continuation_steps=args.max_continuation_steps,
        min_margin_gap=args.min_margin_gap,
        min_sequence_action_l2=args.min_sequence_action_l2,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
