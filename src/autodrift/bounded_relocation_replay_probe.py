"""No-training bounded relocation replay probe for warmup-history rows."""

from __future__ import annotations

import argparse
import copy
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
)
from autodrift.causal_history_candidate_outcome_probe import replay_probe_variant
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.warmup_latched_outcome_probe import (
    CONTROL_VARIANTS,
    WARMUP_HISTORY_VARIANTS,
    build_warmup_variant_hiddens,
    source_diversity,
)
from autodrift.wrong_history_boundary_relocation_surface import (
    obstacle_body_geometry,
    relocate_outcome_snapshot,
)


DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025
DEFAULT_MIN_MARGIN_GAP = 0.02
DEFAULT_MIN_BODY_X = 2.0
DEFAULT_MIN_HALF_WIDTH = 0.05


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if np.isfinite(result) else float(default)


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(float(value) != 0.0) if np.isfinite(float(value)) else False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _source_key(row: pd.Series | dict[str, Any]) -> str:
    if "selected_index" in row and str(row.get("selected_index", "")) != "":
        return f"selected:{row.get('selected_index')}"
    return "|".join(
        str(row.get(column, ""))
        for column in ("source_index", "seed", "reveal_step", "preferred_fault", "wrong_fault")
    )


def _require_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"candidate rows missing required columns: {missing}")


def prepare_candidate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = (
        "seed",
        "reveal_step",
        "preferred_fault",
        "wrong_fault",
        "variant",
        "capability_pair",
        "preferred_reveal_bucket",
        "sequence_action_l2_mean",
        "margin_gap",
        "body_longitudinal_offset",
        "body_lateral_offset",
        "half_width_inflation",
    )
    _require_columns(frame, required)
    output = frame.copy()
    for column in (
        "sequence_action_l2_mean",
        "margin_gap",
        "normal_margin",
        "variant_margin",
        "body_longitudinal_offset",
        "body_lateral_offset",
        "half_width_inflation",
        "proxy_normal_margin",
    ):
        if column in output.columns:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    for column in ("matched_current_pass", "bucketed_current_pass", "proxy_preferred_normal_margin"):
        if column in output.columns:
            output[column] = output[column].map(_bool_value)
    output["history_variant"] = output["variant"].astype(str).isin(WARMUP_HISTORY_VARIANTS)
    output["control_variant"] = output["variant"].astype(str).isin(CONTROL_VARIANTS)
    output["source_key"] = [_source_key(row) for _, row in output.iterrows()]
    return output


def select_replay_candidates(
    frame: pd.DataFrame,
    *,
    max_candidate_rows: int,
    per_capability_pair_cap: int,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    candidates = prepare_candidate_frame(frame)
    candidates = candidates[
        candidates["history_variant"]
        & (candidates["sequence_action_l2_mean"] >= float(min_sequence_action_l2))
    ].copy()
    if candidates.empty:
        return candidates
    candidates["_preferred_proxy_rank"] = (
        candidates["proxy_preferred_normal_margin"].astype(bool)
        if "proxy_preferred_normal_margin" in candidates.columns
        else False
    )
    candidates["_nonnegative_margin_gap_rank"] = candidates["margin_gap"] >= 0.0
    candidates["_score"] = (
        candidates["sequence_action_l2_mean"].fillna(0.0) / 0.10
        + candidates["margin_gap"].fillna(0.0).clip(lower=0.0) / 0.02
        + candidates["_preferred_proxy_rank"].astype(float)
        + 0.25 * candidates["_nonnegative_margin_gap_rank"].astype(float)
    )
    candidates = candidates.sort_values(
        ["_score", "sequence_action_l2_mean", "margin_gap", "seed", "reveal_step"],
        ascending=[False, False, False, True, True],
    )
    selected_groups: list[pd.DataFrame] = []
    for _, group in candidates.groupby("capability_pair", observed=True):
        selected_groups.append(group.head(max(1, int(per_capability_pair_cap))))
    if not selected_groups:
        return candidates.head(0)
    selected = pd.concat(selected_groups, ignore_index=True).sort_values("_score", ascending=False)
    if int(max_candidate_rows) > 0:
        selected = selected.head(int(max_candidate_rows))
    selected["selected_replay_rank"] = np.arange(len(selected), dtype=int)
    return selected.reset_index(drop=True)


def bounded_relocation_geometry(
    *,
    source_body_x: float,
    source_body_y: float,
    source_half_width: float,
    body_longitudinal_offset: float,
    body_lateral_offset: float,
    half_width_inflation: float,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> dict[str, float]:
    body_x = max(float(min_body_x), float(source_body_x) + float(body_longitudinal_offset))
    half_width = max(float(min_half_width), float(source_half_width) + float(half_width_inflation))
    return {
        "relocated_body_x": float(body_x),
        "relocated_body_y": float(source_body_y) + float(body_lateral_offset),
        "relocated_half_width": float(half_width),
    }


def classify_actual_replay_result(
    *,
    variant: str,
    normal_success: bool,
    variant_success: bool,
    normal_margin: float,
    variant_margin: float,
    sequence_action_l2_mean: float,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
    min_margin_gap: float = DEFAULT_MIN_MARGIN_GAP,
) -> dict[str, Any]:
    normal_viable = bool(normal_success and np.isfinite(normal_margin) and normal_margin >= 0.0)
    success_drop = bool(normal_success and not variant_success)
    margin_gap = (
        float(normal_margin) - float(variant_margin)
        if np.isfinite(normal_margin) and np.isfinite(variant_margin)
        else float("nan")
    )
    sequence_action_critical = bool(float(sequence_action_l2_mean) >= float(min_sequence_action_l2))
    outcome_critical = bool(
        normal_viable
        and sequence_action_critical
        and (success_drop or (np.isfinite(margin_gap) and margin_gap >= float(min_margin_gap)))
    )
    history_positive = bool(outcome_critical and str(variant) in WARMUP_HISTORY_VARIANTS)
    control_positive = bool(outcome_critical and str(variant) in CONTROL_VARIANTS)
    return {
        "normal_viable": normal_viable,
        "success_drop": success_drop,
        "margin_gap": margin_gap,
        "sequence_action_critical": sequence_action_critical,
        "outcome_critical": outcome_critical,
        "history_positive": history_positive,
        "control_positive": control_positive,
    }


def _trace_to_outcome_snapshot(point: TracePoint) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=int(point.seed),
        step=int(point.step),
        observation=np.asarray(point.observation, dtype=np.float32).copy(),
        hidden=point.hidden.detach().clone(),
        env=copy.deepcopy(point.env),
        info=dict(point.info),
    )


def _outcome_to_trace(snapshot: OutcomeSnapshot, *, fault: Any) -> TracePoint:
    return TracePoint(
        seed=int(snapshot.seed),
        fault=fault,
        step=int(snapshot.step),
        observation=np.asarray(snapshot.observation, dtype=np.float32).copy(),
        hidden=snapshot.hidden.detach().clone(),
        env=copy.deepcopy(snapshot.env),
        info=dict(snapshot.info),
    )


def relocate_trace_point(
    point: TracePoint,
    *,
    body_longitudinal_offset: float,
    body_lateral_offset: float,
    half_width_inflation: float,
    min_body_x: float = DEFAULT_MIN_BODY_X,
    min_half_width: float = DEFAULT_MIN_HALF_WIDTH,
) -> tuple[TracePoint, dict[str, float]]:
    snapshot = _trace_to_outcome_snapshot(point)
    source_x, source_y, source_half_width = obstacle_body_geometry(snapshot)
    geometry = bounded_relocation_geometry(
        source_body_x=source_x,
        source_body_y=source_y,
        source_half_width=source_half_width,
        body_longitudinal_offset=body_longitudinal_offset,
        body_lateral_offset=body_lateral_offset,
        half_width_inflation=half_width_inflation,
        min_body_x=min_body_x,
        min_half_width=min_half_width,
    )
    relocated = relocate_outcome_snapshot(
        snapshot,
        body_longitudinal=geometry["relocated_body_x"],
        body_lateral=geometry["relocated_body_y"],
        half_width=geometry["relocated_half_width"],
    )
    return _outcome_to_trace(relocated, fault=point.fault), {
        "source_body_x": float(source_x),
        "source_body_y": float(source_y),
        "source_half_width": float(source_half_width),
        **geometry,
    }


def summarize_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    output: list[dict[str, Any]] = []
    for value, group in frame.groupby(key, observed=True):
        output.append(
            {
                key: str(value),
                "rows": int(len(group)),
                "history_positive_rows": int(group["history_positive"].astype(bool).sum())
                if "history_positive" in group.columns
                else 0,
                "control_positive_rows": int(group["control_positive"].astype(bool).sum())
                if "control_positive" in group.columns
                else 0,
                "outcome_critical_rows": int(group["outcome_critical"].astype(bool).sum())
                if "outcome_critical" in group.columns
                else 0,
                "unique_source_seeds": int(group["seed"].nunique()) if "seed" in group.columns else 0,
                "unique_capability_pairs": int(group["capability_pair"].nunique())
                if "capability_pair" in group.columns
                else 0,
                "unique_reveal_buckets": int(group["preferred_reveal_bucket"].nunique())
                if "preferred_reveal_bucket" in group.columns
                else 0,
            }
        )
    return output


def build_replay_summary(
    *,
    run_dir: Path,
    candidate_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    actor_parameters_changed: bool,
    min_margin_gap: float,
    min_sequence_action_l2: float,
) -> dict[str, Any]:
    history_positive = [row for row in replay_rows if bool(row.get("history_positive", False))]
    control_positive = [row for row in replay_rows if bool(row.get("control_positive", False))]
    normal_failed = [
        row
        for row in replay_rows
        if (not bool(row.get("normal_success", False))) or _finite(row.get("normal_margin")) < 0.0
    ]
    result_class = "bounded_relocation_replay_positive" if history_positive else "bounded_relocation_replay_no_history_positive"
    return {
        "run_type": "bounded_relocation_replay_probe",
        "selected_candidate_rows": int(len(candidate_rows)),
        "actual_replay_rows": int(len(replay_rows)),
        "history_positive_rows": int(len(history_positive)),
        "control_positive_rows": int(len(control_positive)),
        "normal_failed_rows": int(len(normal_failed)),
        "rejected_rows": int(len(rejected_rows)),
        "min_margin_gap": float(min_margin_gap),
        "min_sequence_action_l2": float(min_sequence_action_l2),
        "selected_candidate_diversity": source_diversity(candidate_rows),
        "actual_replay_diversity": source_diversity(replay_rows),
        "history_positive_diversity": source_diversity(history_positive),
        "control_positive_diversity": source_diversity(control_positive),
        "variant_summary": summarize_rows(replay_rows, "variant"),
        "relocation_summary": summarize_rows(replay_rows, "relocation_key"),
        "result_class": result_class,
        "replay_started": True,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_parameters_changed": bool(actor_parameters_changed),
        "actor_input_contract_changed": False,
        "selected_candidate_rows_csv": run_dir / "selected_candidate_rows.csv",
        "actual_replay_rows_csv": run_dir / "actual_replay_rows.csv",
        "history_positive_rows_csv": run_dir / "history_positive_rows.csv",
        "control_positive_rows_csv": run_dir / "control_positive_rows.csv",
        "variant_summary_csv": run_dir / "variant_summary.csv",
        "source_diversity_summary_csv": run_dir / "source_diversity_summary.csv",
        "relocation_summary_csv": run_dir / "relocation_summary.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def run_bounded_relocation_replay_probe(
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
    frame = pd.read_csv(candidate_rows_path)
    selected = select_replay_candidates(
        frame,
        max_candidate_rows=max_candidate_rows,
        per_capability_pair_cap=per_capability_pair_cap,
        min_sequence_action_l2=min_sequence_action_l2,
    )
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
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

    replay_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for selected_index, row in selected.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        reveal_step = int(row["reveal_step"])
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        requested_variant = str(row["variant"])
        variants = tuple(dict.fromkeys((requested_variant, "reset_hidden", "zero_current_response")))
        try:
            preferred_trace = trace_for(seed, preferred_fault, reveal_step)
            wrong_trace = trace_for(seed, wrong_fault, reveal_step)
            relocated_point, relocation = relocate_trace_point(
                preferred_trace[-1],
                body_longitudinal_offset=float(row["body_longitudinal_offset"]),
                body_lateral_offset=float(row["body_lateral_offset"]),
                half_width_inflation=float(row["half_width_inflation"]),
            )
            variant_hiddens = build_warmup_variant_hiddens(
                model=model,
                preferred_trace=preferred_trace,
                wrong_trace=wrong_trace,
                recent_window_length=recent_window_length,
                device=resolved_device,
            )
        except Exception as exc:  # pragma: no cover - surfaced in artifacts.
            rejected_rows.append(
                {
                    "selected_index": int(selected_index),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "variant": requested_variant,
                    "rejection_reason": "trace_or_relocation_failed",
                    "error": str(exc),
                }
            )
            continue

        normal, normal_actions = replay_probe_variant(
            model=model,
            snapshot=relocated_point,
            variant="normal",
            initial_hidden=relocated_point.hidden,
            max_continuation_steps=max_continuation_steps,
            normal_first_action=None,
            normal_actions=None,
            response_dim=response_dim,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        normal_margin = _finite(normal.get("min_clearance_margin"))
        normal_success = bool(normal.get("success", False))
        relocation_key = (
            f"x={relocation['relocated_body_x']:.3f}|"
            f"y={relocation['relocated_body_y']:.3f}|"
            f"w={relocation['relocated_half_width']:.3f}"
        )
        for variant in variants:
            hidden = variant_hiddens.get(variant, relocated_point.hidden).detach().clone()
            result, _ = replay_probe_variant(
                model=model,
                snapshot=relocated_point,
                variant=variant,
                initial_hidden=hidden,
                max_continuation_steps=max_continuation_steps,
                normal_first_action=normal_first_action,
                normal_actions=normal_actions,
                response_dim=response_dim,
                device=resolved_device,
            )
            variant_margin = _finite(result.get("min_clearance_margin"))
            classification = classify_actual_replay_result(
                variant=variant,
                normal_success=normal_success,
                variant_success=bool(result.get("success", False)),
                normal_margin=normal_margin,
                variant_margin=variant_margin,
                sequence_action_l2_mean=_finite(result.get("action_trajectory_distance_mean"), 0.0),
                min_sequence_action_l2=min_sequence_action_l2,
                min_margin_gap=min_margin_gap,
            )
            replay_rows.append(
                {
                    "selected_index": int(selected_index),
                    "source_index": int(row.get("source_index", selected_index)),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "capability_pair": str(row.get("capability_pair", "")),
                    "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
                    "variant": variant,
                    "normal_success": normal_success,
                    "variant_success": bool(result.get("success", False)),
                    "normal_margin": normal_margin,
                    "variant_margin": variant_margin,
                    "normal_terminal_reason": str(normal.get("terminal_reason", "")),
                    "variant_terminal_reason": str(result.get("terminal_reason", "")),
                    "first_action_l2": _finite(result.get("first_action_distance"), 0.0),
                    "sequence_action_l2_mean": _finite(result.get("action_trajectory_distance_mean"), 0.0),
                    "sequence_action_l2_max": _finite(result.get("action_trajectory_distance_max"), 0.0),
                    "relocation_key": relocation_key,
                    **relocation,
                    **classification,
                }
            )

    candidate_records = _records(selected)
    history_positive = [row for row in replay_rows if bool(row.get("history_positive", False))]
    control_positive = [row for row in replay_rows if bool(row.get("control_positive", False))]
    variant_summary = summarize_rows(replay_rows, "variant")
    relocation_summary = summarize_rows(replay_rows, "relocation_key")
    source_diversity_summary = [
        {"row_set": "selected_candidate_rows", **source_diversity(candidate_records)},
        {"row_set": "actual_replay_rows", **source_diversity(replay_rows)},
        {"row_set": "history_positive_rows", **source_diversity(history_positive)},
        {"row_set": "control_positive_rows", **source_diversity(control_positive)},
    ]
    checksum_after = model_parameter_checksum(model)
    summary = build_replay_summary(
        run_dir=run_dir,
        candidate_rows=candidate_records,
        replay_rows=replay_rows,
        rejected_rows=rejected_rows,
        actor_parameters_changed=str(checksum_after) != str(checksum_before),
        min_margin_gap=min_margin_gap,
        min_sequence_action_l2=min_sequence_action_l2,
    )
    write_csv_rows(run_dir / "selected_candidate_rows.csv", candidate_records)
    write_csv_rows(run_dir / "actual_replay_rows.csv", replay_rows)
    write_csv_rows(run_dir / "history_positive_rows.csv", history_positive)
    write_csv_rows(run_dir / "control_positive_rows.csv", control_positive)
    write_csv_rows(run_dir / "variant_summary.csv", variant_summary)
    write_csv_rows(run_dir / "source_diversity_summary.csv", source_diversity_summary)
    write_csv_rows(run_dir / "relocation_summary.csv", relocation_summary)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--candidate-rows", type=Path, required=True)
    parser.add_argument("--max-candidate-rows", type=int, default=128)
    parser.add_argument("--per-capability-pair-cap", type=int, default=12)
    parser.add_argument("--history-length", type=int, default=56)
    parser.add_argument("--recent-window-length", type=int, default=4)
    parser.add_argument("--max-continuation-steps", type=int, default=48)
    parser.add_argument("--min-margin-gap", type=float, default=DEFAULT_MIN_MARGIN_GAP)
    parser.add_argument("--min-sequence-action-l2", type=float, default=DEFAULT_MIN_SEQUENCE_ACTION_L2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="bounded_relocation_replay_probe")
    summary = run_bounded_relocation_replay_probe(
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
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")
    print(f"actual_replay_rows={summary['actual_replay_rows']}")
    print(f"history_positive_rows={summary['history_positive_rows']}")
    print(f"result_class={summary['result_class']}")


if __name__ == "__main__":
    main()
