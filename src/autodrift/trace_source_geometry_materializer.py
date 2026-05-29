"""Trace-backed source geometry materialization for forward source mining.

This module implements schema and helper logic only. It does not train, replay,
run PPO, promote checkpoints, or change actor inputs.
"""

from __future__ import annotations

import argparse
import copy
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    TracePoint,
    collect_fault_trace_window,
    fault_map_from_config,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.forward_geometry_source_miner import DEFAULT_SOURCE_STEP_OFFSETS, source_steps_for_reveal
from autodrift.matched_history_outcome_gate import OutcomeSnapshot
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device
from autodrift.warmup_latched_outcome_probe import source_diversity
from autodrift.wrong_history_boundary_relocation_surface import obstacle_body_geometry


REQUIRED_REVEAL_COLUMNS = (
    "source_index",
    "seed",
    "reveal_step",
    "preferred_fault",
    "wrong_fault",
    "capability_pair",
    "preferred_reveal_bucket",
    "wrong_reveal_bucket",
    "matched_current_pass",
    "bucketed_current_pass",
)

SOURCE_GEOMETRY_FIELDS = (
    "source_geometry_index",
    "upstream_source_index",
    "seed",
    "reveal_step",
    "source_step",
    "source_step_offset",
    "source_to_reveal_steps",
    "preferred_fault",
    "preferred_fault_family",
    "wrong_fault",
    "wrong_fault_family",
    "capability_pair",
    "preferred_reveal_bucket",
    "wrong_reveal_bucket",
    "matched_current_pass",
    "bucketed_current_pass",
    "matched_or_bucketed_reveal_pass",
    "source_body_x",
    "source_body_y",
    "source_half_width",
    "wrong_source_body_x",
    "wrong_source_body_y",
    "wrong_source_half_width",
    "preferred_active_obstacle_kind",
    "preferred_active_obstacle_body_x",
    "preferred_active_obstacle_body_y",
    "preferred_active_obstacle_half_width",
    "trace_reconstruction_status",
    "geometry_materialization_status",
)

REJECTED_FIELDS = (
    "upstream_source_index",
    "seed",
    "reveal_step",
    "source_step",
    "preferred_fault",
    "wrong_fault",
    "rejection_reason",
    "error",
)


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


def parse_int_tuple(raw: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in str(raw).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    return values


def _require_columns(frame: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"source reveal rows missing required columns: {missing}")


def prepare_reveal_source_frame(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(frame, REQUIRED_REVEAL_COLUMNS)
    output = frame.copy()
    output["seed"] = pd.to_numeric(output["seed"], errors="coerce")
    output["reveal_step"] = pd.to_numeric(output["reveal_step"], errors="coerce")
    output["source_index"] = pd.to_numeric(output["source_index"], errors="coerce")
    for column in ("matched_current_pass", "bucketed_current_pass", "matched_or_bucketed_reveal_pass"):
        if column in output.columns:
            output[column] = output[column].map(_bool_value)
    if "matched_or_bucketed_reveal_pass" not in output.columns:
        output["matched_or_bucketed_reveal_pass"] = (
            output["matched_current_pass"].astype(bool) | output["bucketed_current_pass"].astype(bool)
        )
    for column in ("preferred_fault_family", "wrong_fault_family"):
        if column not in output.columns:
            output[column] = ""
    return output


def trace_point_to_outcome_snapshot(point: TracePoint) -> OutcomeSnapshot:
    return OutcomeSnapshot(
        seed=int(point.seed),
        step=int(point.step),
        observation=np.asarray(point.observation, dtype=np.float32).copy(),
        hidden=point.hidden.detach().clone(),
        env=copy.deepcopy(point.env),
        info=dict(point.info),
    )


def emergency_obstacle_geometry_from_trace_point(point: TracePoint) -> tuple[float, float, float]:
    return obstacle_body_geometry(trace_point_to_outcome_snapshot(point))


def active_obstacle_diagnostics(point: TracePoint) -> dict[str, Any]:
    info = dict(point.info)
    return {
        "preferred_active_obstacle_kind": str(info.get("active_obstacle_kind", "")),
        "preferred_active_obstacle_body_x": _finite(info.get("active_obstacle_body_x")),
        "preferred_active_obstacle_body_y": _finite(info.get("active_obstacle_body_y")),
        "preferred_active_obstacle_half_width": _finite(info.get("active_obstacle_half_width")),
    }


def trace_point_at_step(trace: list[TracePoint], step: int) -> TracePoint:
    for point in trace:
        if int(point.step) == int(step):
            return point
    raise ValueError(f"trace does not contain step={int(step)}")


def materialize_source_geometry_for_row(
    row: pd.Series | dict[str, Any],
    *,
    preferred_trace: list[TracePoint],
    wrong_trace: list[TracePoint],
    source_step_offsets: tuple[int, ...] = DEFAULT_SOURCE_STEP_OFFSETS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item = dict(row)
    seed = int(item["seed"])
    reveal_step = int(item["reveal_step"])
    preferred_fault = str(item["preferred_fault"])
    wrong_fault = str(item["wrong_fault"])
    upstream_source_index = int(_finite(item.get("source_index"), 0.0))
    source_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    for source_step in source_steps_for_reveal(reveal_step, offsets=source_step_offsets):
        try:
            preferred_point = trace_point_at_step(preferred_trace, source_step)
            wrong_point = trace_point_at_step(wrong_trace, source_step)
            source_x, source_y, source_half_width = emergency_obstacle_geometry_from_trace_point(preferred_point)
            wrong_x, wrong_y, wrong_half_width = emergency_obstacle_geometry_from_trace_point(wrong_point)
        except Exception as exc:
            rejected_rows.append(
                {
                    "upstream_source_index": upstream_source_index,
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "source_step": int(source_step),
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "rejection_reason": "trace_or_geometry_materialization_failed",
                    "error": str(exc),
                }
            )
            continue

        values = (source_x, source_y, source_half_width)
        if not all(np.isfinite(float(value)) for value in values):
            rejected_rows.append(
                {
                    "upstream_source_index": upstream_source_index,
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "source_step": int(source_step),
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "rejection_reason": "nonfinite_preferred_emergency_obstacle_geometry",
                    "error": "",
                }
            )
            continue

        output = {
            "source_geometry_index": -1,
            "upstream_source_index": upstream_source_index,
            "seed": seed,
            "reveal_step": reveal_step,
            "source_step": int(source_step),
            "source_step_offset": int(source_step) - reveal_step,
            "source_to_reveal_steps": reveal_step - int(source_step),
            "preferred_fault": preferred_fault,
            "preferred_fault_family": str(item.get("preferred_fault_family", "")),
            "wrong_fault": wrong_fault,
            "wrong_fault_family": str(item.get("wrong_fault_family", "")),
            "capability_pair": str(item.get("capability_pair", "")),
            "preferred_reveal_bucket": str(item.get("preferred_reveal_bucket", "")),
            "wrong_reveal_bucket": str(item.get("wrong_reveal_bucket", "")),
            "matched_current_pass": _bool_value(item.get("matched_current_pass", False)),
            "bucketed_current_pass": _bool_value(item.get("bucketed_current_pass", False)),
            "matched_or_bucketed_reveal_pass": _bool_value(
                item.get(
                    "matched_or_bucketed_reveal_pass",
                    _bool_value(item.get("matched_current_pass", False))
                    or _bool_value(item.get("bucketed_current_pass", False)),
                )
            ),
            "source_body_x": float(source_x),
            "source_body_y": float(source_y),
            "source_half_width": float(source_half_width),
            "wrong_source_body_x": float(wrong_x),
            "wrong_source_body_y": float(wrong_y),
            "wrong_source_half_width": float(wrong_half_width),
            **active_obstacle_diagnostics(preferred_point),
            "trace_reconstruction_status": "pass",
            "geometry_materialization_status": "pass",
        }
        source_rows.append(output)
    return source_rows, rejected_rows


def materialize_trace_source_geometry_from_rows(
    frame: pd.DataFrame,
    *,
    trace_for: Callable[[int, str, int], list[TracePoint]],
    source_step_offsets: tuple[int, ...] = DEFAULT_SOURCE_STEP_OFFSETS,
    max_source_rows: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = prepare_reveal_source_frame(frame)
    if int(max_source_rows) > 0:
        rows = rows.head(int(max_source_rows)).copy()
    source_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for _, row in rows.iterrows():
        seed = int(row["seed"])
        reveal_step = int(row["reveal_step"])
        try:
            preferred_trace = trace_for(seed, str(row["preferred_fault"]), reveal_step)
            wrong_trace = trace_for(seed, str(row["wrong_fault"]), reveal_step)
            accepted, rejected = materialize_source_geometry_for_row(
                row,
                preferred_trace=preferred_trace,
                wrong_trace=wrong_trace,
                source_step_offsets=source_step_offsets,
            )
            source_rows.extend(accepted)
            rejected_rows.extend(rejected)
        except Exception as exc:
            rejected_rows.append(
                {
                    "upstream_source_index": int(_finite(row.get("source_index"), 0.0)),
                    "seed": seed,
                    "reveal_step": reveal_step,
                    "source_step": "",
                    "preferred_fault": str(row["preferred_fault"]),
                    "wrong_fault": str(row["wrong_fault"]),
                    "rejection_reason": "trace_reconstruction_failed",
                    "error": str(exc),
                }
            )
    for index, row in enumerate(source_rows):
        row["source_geometry_index"] = int(index)
    return pd.DataFrame(source_rows), pd.DataFrame(rejected_rows)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.to_dict("records") if not frame.empty else []


def _numeric_summary(frame: pd.DataFrame, column: str) -> dict[str, float | None]:
    if column not in frame.columns:
        return {"min": None, "p50": None, "p95": None}
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return {"min": None, "p50": None, "p95": None}
    return {
        "min": float(values.min()),
        "p50": float(values.quantile(0.50)),
        "p95": float(values.quantile(0.95)),
    }


def _group_summary(frame: pd.DataFrame, key: str) -> list[dict[str, Any]]:
    if frame.empty or key not in frame.columns:
        return []
    rows: list[dict[str, Any]] = []
    for value, group in frame.groupby(key, observed=True):
        rows.append({key: value, "rows": int(len(group))})
    return rows


def build_trace_source_geometry_summary(
    *,
    source_rows: pd.DataFrame,
    rejected_rows: pd.DataFrame,
    source_materialization_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    source_body_x = _numeric_summary(source_rows, "source_body_x")
    source_to_reveal = _numeric_summary(source_rows, "source_to_reveal_steps")
    return {
        "run_type": "trace_source_geometry_materializer",
        "source_geometry_rows": int(len(source_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "source_body_x_min": source_body_x["min"],
        "source_body_x_p50": source_body_x["p50"],
        "source_body_x_p95": source_body_x["p95"],
        "source_to_reveal_steps_min": source_to_reveal["min"],
        "source_to_reveal_steps_p50": source_to_reveal["p50"],
        "source_to_reveal_steps_p95": source_to_reveal["p95"],
        "source_diversity": source_diversity(_records(source_rows)),
        "source_step_summary": _group_summary(source_rows, "source_step"),
        "rejection_summary": _group_summary(rejected_rows, "rejection_reason"),
        "source_materialization_started": bool(source_materialization_started),
        "source_mining_started": False,
        "source_preflight_started": False,
        "replay_started": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_parameters_changed": bool(actor_parameters_changed),
        "actor_input_contract_changed": False,
    }


def write_trace_source_geometry_outputs(
    *,
    run_dir: Path,
    source_rows: pd.DataFrame,
    rejected_rows: pd.DataFrame,
    source_materialization_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = build_trace_source_geometry_summary(
        source_rows=source_rows,
        rejected_rows=rejected_rows,
        source_materialization_started=source_materialization_started,
        actor_parameters_changed=actor_parameters_changed,
    )
    summary["source_geometry_rows_csv"] = run_dir / "source_geometry_rows.csv"
    summary["rejected_rows_csv"] = run_dir / "rejected_rows.csv"
    summary["source_step_summary_csv"] = run_dir / "source_step_summary.csv"
    summary["source_diversity_summary_csv"] = run_dir / "source_diversity_summary.csv"
    summary["summary_json"] = run_dir / "summary.json"
    write_csv_rows(run_dir / "source_geometry_rows.csv", _records(source_rows), fieldnames=SOURCE_GEOMETRY_FIELDS)
    write_csv_rows(run_dir / "rejected_rows.csv", _records(rejected_rows), fieldnames=REJECTED_FIELDS)
    write_csv_rows(run_dir / "source_step_summary.csv", summary["source_step_summary"])
    write_csv_rows(run_dir / "source_diversity_summary.csv", [{"row_set": "source_geometry_rows", **summary["source_diversity"]}])
    write_json(run_dir / "summary.json", summary)
    return summary


def run_trace_source_geometry_materializer_from_rows(
    *,
    source_rows_path: Path,
    trace_for: Callable[[int, str, int], list[TracePoint]],
    run_dir: Path,
    source_step_offsets: tuple[int, ...] = DEFAULT_SOURCE_STEP_OFFSETS,
    max_source_rows: int = 0,
    source_materialization_started: bool = False,
    actor_parameters_changed: bool = False,
) -> dict[str, Any]:
    source_frame = pd.read_csv(source_rows_path)
    source_rows, rejected_rows = materialize_trace_source_geometry_from_rows(
        source_frame,
        trace_for=trace_for,
        source_step_offsets=source_step_offsets,
        max_source_rows=max_source_rows,
    )
    return write_trace_source_geometry_outputs(
        run_dir=run_dir,
        source_rows=source_rows,
        rejected_rows=rejected_rows,
        source_materialization_started=source_materialization_started,
        actor_parameters_changed=actor_parameters_changed,
    )


def run_trace_source_geometry_materializer(
    *,
    checkpoint_path: Path,
    config_path: Path,
    source_rows_path: Path,
    run_dir: Path,
    device: str,
    history_length: int,
    source_step_offsets: tuple[int, ...] = DEFAULT_SOURCE_STEP_OFFSETS,
    max_source_rows: int = 0,
) -> dict[str, Any]:
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)
    trace_cache: dict[tuple[int, str, int, int], list[TracePoint]] = {}

    def trace_for(seed: int, fault_name: str, reveal_step: int) -> list[TracePoint]:
        key = (int(seed), str(fault_name), int(reveal_step), int(history_length))
        if key not in trace_cache:
            trace_cache[key] = collect_fault_trace_window(
                model=model,
                env_config=env_config,
                fault=fault_by_name[str(fault_name)],
                seed=int(seed),
                target_step=int(reveal_step),
                history_length=int(history_length),
                device=resolved_device,
            )
        return trace_cache[key]

    summary = run_trace_source_geometry_materializer_from_rows(
        source_rows_path=source_rows_path,
        trace_for=trace_for,
        run_dir=run_dir,
        source_step_offsets=source_step_offsets,
        max_source_rows=max_source_rows,
        source_materialization_started=True,
        actor_parameters_changed=str(model_parameter_checksum(model)) != str(checksum_before),
    )
    summary["checkpoint_path"] = str(checkpoint_path)
    summary["config_path"] = str(config_path)
    summary["source_rows_path"] = str(source_rows_path)
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--source-step-offsets", type=parse_int_tuple, default=DEFAULT_SOURCE_STEP_OFFSETS)
    parser.add_argument("--max-source-rows", type=int, default=0)
    parser.add_argument("--history-length", type=int, default=56)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Validate arguments only without loading a checkpoint or materializing traces.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    if args.no_run:
        print("trace source geometry materializer arguments validated")
        print(f"source_rows={args.source_rows}")
        print(f"run_dir={args.run_dir}")
        return
    if args.checkpoint is None or args.config is None:
        raise SystemExit("--checkpoint and --config are required unless --no-run is set")
    summary = run_trace_source_geometry_materializer(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        source_rows_path=args.source_rows,
        run_dir=args.run_dir,
        device=args.device,
        history_length=int(args.history_length),
        source_step_offsets=tuple(args.source_step_offsets),
        max_source_rows=int(args.max_source_rows),
    )
    print(f"summary_json={args.run_dir / 'summary.json'}")
    print(f"source_geometry_rows={summary['source_geometry_rows']}")
    print(f"rejected_rows={summary['rejected_rows']}")


if __name__ == "__main__":
    main()
