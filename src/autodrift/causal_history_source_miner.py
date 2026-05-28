"""Materialize no-training causal-history source candidates."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_sequence_intervention_probe import (
    collect_fault_trace_window,
    fault_map_from_config,
    load_snapshot_step_lookup,
    select_source_rows,
    source_pair_key,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.extreme_dynamics_scenario_corpus import load_scenario_config
from autodrift.source_balanced_bc_v2_objective import model_parameter_checksum
from autodrift.train_ppo import resolve_device


DEFAULT_THRESHOLDS = {
    "ego_response_l2": 0.08,
    "actuator_state_l2": 0.05,
    "previous_command_l2": 0.05,
    "scene_context_l2": 0.10,
    "obstacle_position_l2": 0.10,
    "road_boundary_l2": 0.12,
    "recent_window_l2": 0.10,
    "older_history_l2": 0.20,
}


def normalized_l2(left: np.ndarray, right: np.ndarray) -> float:
    left_arr = np.asarray(left, dtype=np.float64).reshape(-1)
    right_arr = np.asarray(right, dtype=np.float64).reshape(-1)
    if left_arr.shape != right_arr.shape or left_arr.size == 0:
        return float("nan")
    diff = left_arr - right_arr
    if not np.all(np.isfinite(diff)):
        return float("nan")
    return float(np.linalg.norm(diff) / np.sqrt(float(diff.size)))


def _segment(observation: np.ndarray, start: int, stop: int | None) -> np.ndarray:
    obs = np.asarray(observation, dtype=np.float32).reshape(-1)
    end = obs.shape[0] if stop is None else min(int(stop), obs.shape[0])
    begin = min(int(start), end)
    return obs[begin:end]


def obstacle_presence_match(left: np.ndarray, right: np.ndarray) -> bool:
    left_obs = np.asarray(left, dtype=np.float32).reshape(-1)
    right_obs = np.asarray(right, dtype=np.float32).reshape(-1)
    if left_obs.shape[0] < 72 or right_obs.shape[0] < 72:
        return True
    present_indices = (44, 51, 58, 65)
    return all(bool(left_obs[index] > 0.5) == bool(right_obs[index] > 0.5) for index in present_indices)


def observation_distance_metrics(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    return {
        "ego_response_l2": normalized_l2(_segment(left, 0, 5), _segment(right, 0, 5)),
        "actuator_state_l2": normalized_l2(_segment(left, 5, 9), _segment(right, 5, 9)),
        "previous_command_l2": normalized_l2(_segment(left, 9, 12), _segment(right, 9, 12)),
        "road_boundary_l2": normalized_l2(_segment(left, 12, 44), _segment(right, 12, 44)),
        "obstacle_position_l2": normalized_l2(_segment(left, 44, 72), _segment(right, 44, 72)),
        "scene_context_l2": normalized_l2(_segment(left, 12, None), _segment(right, 12, None)),
        "full_observation_l2": normalized_l2(left, right),
        "obstacle_slot_presence_match": obstacle_presence_match(left, right),
    }


def history_window_l2(
    left_observations: list[np.ndarray],
    right_observations: list[np.ndarray],
) -> float:
    count = min(len(left_observations), len(right_observations))
    if count <= 0:
        return float("nan")
    distances = [
        normalized_l2(left_observations[-count + index], right_observations[-count + index])
        for index in range(count)
    ]
    finite = [value for value in distances if np.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def hidden_l2(left: torch.Tensor, right: torch.Tensor) -> float:
    left_arr = left.detach().cpu().numpy().reshape(-1)
    right_arr = right.detach().cpu().numpy().reshape(-1)
    return normalized_l2(left_arr, right_arr)


def passes_matched_current(metrics: dict[str, Any], thresholds: dict[str, float]) -> bool:
    if not bool(metrics.get("obstacle_slot_presence_match", True)):
        return False
    required = (
        "ego_response_l2",
        "actuator_state_l2",
        "previous_command_l2",
        "scene_context_l2",
        "obstacle_position_l2",
        "road_boundary_l2",
    )
    for key in required:
        value = float(metrics.get(key, float("nan")))
        if not np.isfinite(value) or value > float(thresholds[key]):
            return False
    return True


def numeric_summary(values: list[float]) -> dict[str, Any]:
    finite = np.asarray([float(value) for value in values if np.isfinite(float(value))], dtype=np.float64)
    if finite.size == 0:
        return {"count": 0, "min": None, "mean": None, "p50": None, "p90": None, "p95": None, "max": None}
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "mean": float(np.mean(finite)),
        "p50": float(np.quantile(finite, 0.50)),
        "p90": float(np.quantile(finite, 0.90)),
        "p95": float(np.quantile(finite, 0.95)),
        "max": float(np.max(finite)),
    }


def source_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "unique_source_seeds": 0,
            "unique_fault_pairs": 0,
            "unique_preferred_fault_families": 0,
            "unique_wrong_fault_families": 0,
            "max_single_seed_share": None,
            "max_single_fault_pair_share": None,
        }
    frame = pd.DataFrame(rows)
    seed_counts = frame["seed"].value_counts() if "seed" in frame.columns else pd.Series(dtype=int)
    pair_counts = frame["fault_pair"].value_counts() if "fault_pair" in frame.columns else pd.Series(dtype=int)
    total = float(len(frame))
    return {
        "rows": int(len(frame)),
        "unique_source_seeds": int(frame["seed"].nunique()) if "seed" in frame.columns else 0,
        "unique_fault_pairs": int(frame["fault_pair"].nunique()) if "fault_pair" in frame.columns else 0,
        "unique_preferred_fault_families": int(frame["preferred_fault_family"].nunique())
        if "preferred_fault_family" in frame.columns
        else 0,
        "unique_wrong_fault_families": int(frame["wrong_fault_family"].nunique())
        if "wrong_fault_family" in frame.columns
        else 0,
        "max_single_seed_share": float(seed_counts.max() / total) if len(seed_counts) else None,
        "max_single_fault_pair_share": float(pair_counts.max() / total) if len(pair_counts) else None,
    }


def classify_source_miner_result(
    *,
    candidate_rows: int,
    matched_current_pairs: int,
    unique_source_seeds: int,
    unique_fault_pairs: int,
    finite_metric_rows: int,
    evaluated_rows: int,
) -> str:
    if evaluated_rows <= 0:
        return "causal_history_source_no_rows"
    if finite_metric_rows < evaluated_rows:
        return "causal_history_source_nonfinite_metrics"
    if matched_current_pairs == 0:
        return "causal_history_source_no_matched_current"
    structural_pass = (
        int(candidate_rows) >= 200
        and int(matched_current_pairs) >= 80
        and int(unique_source_seeds) >= 12
        and int(unique_fault_pairs) >= 6
    )
    if structural_pass:
        return "causal_history_source_structural_pass"
    return "causal_history_source_structural_sparse"


def _fault_pair_from_row(row: pd.Series) -> str:
    pair = str(row.get("pairing_rule", "")).strip()
    if pair:
        return pair
    return source_pair_key(row)


def run_causal_history_source_miner(
    *,
    checkpoint_path: Path,
    config_path: Path,
    source_rows_path: Path,
    max_source_rows: int,
    per_fault_pair_cap: int,
    history_length: int,
    recent_window_length: int,
    device: str,
    run_dir: Path,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    threshold_values = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    config = load_scenario_config(config_path)
    env_config = load_env_config(Path(config.get("env_config", "configs/ppo_m541_matched_l3_variance_4096.json")))
    fault_by_name = fault_map_from_config(config)
    source_frame = pd.read_csv(source_rows_path)
    selected_rows = select_source_rows(
        source_frame,
        max_source_rows=max_source_rows,
        per_fault_pair_cap=per_fault_pair_cap,
    )
    snapshot_steps = load_snapshot_step_lookup(source_rows_path)
    resolved_device = resolve_device(device)
    model, _ = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    checksum_before = model_parameter_checksum(model)

    trace_cache: dict[tuple[int, str, int, int], Any] = {}

    def trace_for(seed: int, fault_name: str, step: int) -> Any:
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

    candidate_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    evaluated_rows: list[dict[str, Any]] = []

    for source_index, row in selected_rows.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        preferred_fault = str(row["preferred_fault"])
        wrong_fault = str(row["wrong_fault"])
        preferred_step = int(row["step"])
        wrong_snapshot_id = int(row["wrong_snapshot_id"])
        wrong_step = int(snapshot_steps[wrong_snapshot_id])
        fault_pair = _fault_pair_from_row(row)
        try:
            preferred_trace = trace_for(seed, preferred_fault, preferred_step)
            wrong_trace = trace_for(seed, wrong_fault, wrong_step)
        except Exception as exc:  # pragma: no cover - surfaced in artifacts.
            rejected_rows.append(
                {
                    "source_index": int(source_index),
                    "seed": seed,
                    "preferred_fault": preferred_fault,
                    "wrong_fault": wrong_fault,
                    "fault_pair": fault_pair,
                    "rejection_reason": "trace_reconstruction_failed",
                    "error": str(exc),
                }
            )
            continue
        preferred_current = preferred_trace[-1]
        wrong_current = wrong_trace[-1]
        current_metrics = observation_distance_metrics(preferred_current.observation, wrong_current.observation)
        recent_left = [point.observation for point in preferred_trace[-max(1, int(recent_window_length)) :]]
        recent_right = [point.observation for point in wrong_trace[-max(1, int(recent_window_length)) :]]
        older_left = [point.observation for point in preferred_trace[: -max(1, int(recent_window_length))]]
        older_right = [point.observation for point in wrong_trace[: -max(1, int(recent_window_length))]]
        recent_l2 = history_window_l2(recent_left, recent_right)
        older_l2 = history_window_l2(older_left, older_right)
        hidden_distance = hidden_l2(preferred_current.hidden, wrong_current.hidden)
        matched_current = passes_matched_current(current_metrics, threshold_values)
        same_recent = bool(
            matched_current
            and np.isfinite(recent_l2)
            and recent_l2 <= float(threshold_values["recent_window_l2"])
            and (
                (np.isfinite(older_l2) and older_l2 >= float(threshold_values["older_history_l2"]))
                or str(row.get("preferred_fault_family", "")) != str(row.get("wrong_fault_family", ""))
            )
        )
        metrics_finite = bool(
            all(
                np.isfinite(float(current_metrics[key]))
                for key in (
                    "ego_response_l2",
                    "actuator_state_l2",
                    "previous_command_l2",
                    "scene_context_l2",
                    "obstacle_position_l2",
                    "road_boundary_l2",
                )
            )
        )
        base = {
            "source_index": int(source_index),
            "pair_id": int(row.get("pair_id", source_index)),
            "preferred_snapshot_id": int(row.get("preferred_snapshot_id", -1)),
            "wrong_snapshot_id": int(row.get("wrong_snapshot_id", wrong_snapshot_id)),
            "seed": seed,
            "preferred_fault": preferred_fault,
            "preferred_fault_family": str(row.get("preferred_fault_family", "")),
            "wrong_fault": wrong_fault,
            "wrong_fault_family": str(row.get("wrong_fault_family", "")),
            "fault_pair": fault_pair,
            "preferred_step": int(preferred_step),
            "wrong_step": int(wrong_step),
            "matched_current_pass": matched_current,
            "same_recent_window_pass": same_recent,
            "recent_window_l2": recent_l2,
            "older_history_l2": older_l2,
            "current_hidden_l2": hidden_distance,
            "reset_margin_gap": float(row.get("reset_margin_gap", float("nan"))),
            "reset_action_l2_gap": float(row.get("reset_action_l2_gap", float("nan"))),
            "normal_margin": float(row.get("normal_margin", float("nan"))),
            "wrong_history_action_critical": bool(row.get("wrong_history_action_critical", False)),
            "reset_history_action_critical": bool(row.get("reset_history_action_critical", False)),
            **current_metrics,
        }
        evaluated_rows.append(base)
        if matched_current:
            candidate_rows.append(
                {
                    **base,
                    "acceptance_reason": "matched_current_older_history_candidate"
                    if not same_recent
                    else "same_recent_older_history_candidate",
                }
            )
        else:
            rejected_rows.append({**base, "rejection_reason": "current_frame_match_failed" if metrics_finite else "nonfinite_metrics"})

    checksum_after = model_parameter_checksum(model)
    actor_parameters_changed = bool(str(checksum_after) != str(checksum_before))
    matched_current_rows = [row for row in evaluated_rows if bool(row.get("matched_current_pass", False))]
    same_recent_rows = [row for row in evaluated_rows if bool(row.get("same_recent_window_pass", False))]
    finite_metric_rows = [
        row
        for row in evaluated_rows
        if all(
            np.isfinite(float(row.get(key, float("nan"))))
            for key in (
                "ego_response_l2",
                "actuator_state_l2",
                "previous_command_l2",
                "scene_context_l2",
                "obstacle_position_l2",
                "road_boundary_l2",
            )
        )
    ]
    candidate_diversity = source_diversity(candidate_rows)
    result_class = classify_source_miner_result(
        candidate_rows=len(candidate_rows),
        matched_current_pairs=len(matched_current_rows),
        unique_source_seeds=int(candidate_diversity["unique_source_seeds"]),
        unique_fault_pairs=int(candidate_diversity["unique_fault_pairs"]),
        finite_metric_rows=len(finite_metric_rows),
        evaluated_rows=len(evaluated_rows),
    )

    distance_keys = [
        "ego_response_l2",
        "actuator_state_l2",
        "previous_command_l2",
        "road_boundary_l2",
        "obstacle_position_l2",
        "scene_context_l2",
        "full_observation_l2",
        "recent_window_l2",
        "older_history_l2",
        "current_hidden_l2",
    ]
    distance_summary = [
        {"metric": key, **numeric_summary([float(row.get(key, float("nan"))) for row in evaluated_rows])}
        for key in distance_keys
    ]
    write_csv_rows(run_dir / "selected_source_rows.csv", selected_rows.to_dict("records"))
    write_csv_rows(run_dir / "evaluated_rows.csv", evaluated_rows)
    write_csv_rows(run_dir / "candidate_rows.csv", candidate_rows)
    write_csv_rows(run_dir / "rejected_rows.csv", rejected_rows)
    write_csv_rows(run_dir / "distance_summary.csv", distance_summary)

    structural_smoke_pass = result_class == "causal_history_source_structural_pass"
    summary = {
        "run_type": "causal_history_source_miner",
        "checkpoint": checkpoint_path,
        "config": config_path,
        "source_rows": source_rows_path,
        "max_source_rows": int(max_source_rows),
        "per_fault_pair_cap": int(per_fault_pair_cap),
        "history_length": int(history_length),
        "recent_window_length": int(recent_window_length),
        "thresholds": threshold_values,
        "selected_source_rows": int(len(selected_rows)),
        "evaluated_rows": int(len(evaluated_rows)),
        "finite_metric_rows": int(len(finite_metric_rows)),
        "candidate_rows": int(len(candidate_rows)),
        "matched_current_pairs": int(len(matched_current_rows)),
        "same_recent_window_candidates": int(len(same_recent_rows)),
        "rejected_rows": int(len(rejected_rows)),
        "candidate_diversity": candidate_diversity,
        "evaluated_diversity": source_diversity(evaluated_rows),
        "same_recent_diversity": source_diversity(same_recent_rows),
        "distance_summary": distance_summary,
        "result_class": result_class,
        "structural_smoke_pass": structural_smoke_pass,
        "actor_parameters_changed": actor_parameters_changed,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
        "selected_source_rows_csv": run_dir / "selected_source_rows.csv",
        "evaluated_rows_csv": run_dir / "evaluated_rows.csv",
        "candidate_rows_csv": run_dir / "candidate_rows.csv",
        "rejected_rows_csv": run_dir / "rejected_rows.csv",
        "distance_summary_csv": run_dir / "distance_summary.csv",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize no-training causal-history source candidates.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--max-source-rows", type=int, default=768)
    parser.add_argument("--per-fault-pair-cap", type=int, default=96)
    parser.add_argument("--history-length", type=int, default=12)
    parser.add_argument("--recent-window-length", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="causal_history_source_miner")
    summary = run_causal_history_source_miner(
        checkpoint_path=args.checkpoint,
        config_path=args.config,
        source_rows_path=args.source_rows,
        max_source_rows=args.max_source_rows,
        per_fault_pair_cap=args.per_fault_pair_cap,
        history_length=args.history_length,
        recent_window_length=args.recent_window_length,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
