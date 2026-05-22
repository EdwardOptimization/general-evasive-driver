"""Replay M162 boundary-outcome rows under candidate policies."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.evaluate import load_env_config
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec, parse_checkpoint_spec
from autodrift.hidden_envelope_probe import response_feature_dim_for_model
from autodrift.matched_history_outcome_gate import (
    OutcomeSnapshot,
    collect_requested_outcome_snapshots,
    replay_outcome_variant,
)
from autodrift.train_ppo import resolve_device
from autodrift.wrong_history_boundary_relocation_surface import relocate_outcome_snapshot


REQUIRED_CORPUS_COLUMNS = (
    "row_id",
    "target",
    "physical_pair_key",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
)


def validate_corpus_frame(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_CORPUS_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("boundary corpus CSV is missing columns: " + ", ".join(missing))


def _requests(frame: pd.DataFrame) -> dict[int, set[int]]:
    requests: dict[int, set[int]] = {}
    for _, row in frame.iterrows():
        requests.setdefault(int(row["left_seed"]), set()).add(int(row["left_step"]))
        requests.setdefault(int(row["right_seed"]), set()).add(int(row["right_step"]))
    return requests


def _snapshot(snapshots: dict[tuple[int, int], OutcomeSnapshot], seed: int, step: int) -> OutcomeSnapshot:
    key = (int(seed), int(step))
    if key not in snapshots:
        raise ValueError(f"missing reconstructed snapshot seed={seed} step={step}")
    return snapshots[key]


def _result_fields(prefix: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}_success": bool(result.get("success", False)),
        f"{prefix}_collision": bool(result.get("collision", False)),
        f"{prefix}_terminal_reason": str(result.get("terminal_reason", "")),
        f"{prefix}_obstacle_completed": bool(result.get("obstacle_completed", False)),
        f"{prefix}_return": float(result.get("return", float("nan"))),
        f"{prefix}_steps": int(result.get("steps", 0)),
        f"{prefix}_margin": float(result.get("min_clearance_margin", float("nan"))),
        f"{prefix}_first_steer": float(result.get("first_steer", float("nan"))),
        f"{prefix}_first_throttle": float(result.get("first_throttle", float("nan"))),
        f"{prefix}_first_brake": float(result.get("first_brake", float("nan"))),
        f"{prefix}_first_action_distance": float(result.get("first_action_distance", float("nan"))),
        f"{prefix}_trajectory_distance_mean": float(result.get("action_trajectory_distance_mean", float("nan"))),
    }


def replay_boundary_rows_for_policy(
    *,
    checkpoint_spec: CheckpointSpec,
    corpus_frame: pd.DataFrame,
    env_config_path: Path,
    max_continuation_steps: int,
    device: str,
) -> list[dict[str, Any]]:
    validate_corpus_frame(corpus_frame)
    resolved_device = resolve_device(device)
    env_config = load_env_config(env_config_path)
    model, _ = load_actor_critic_checkpoint(checkpoint_spec.path, device=str(resolved_device))
    model.eval()
    response_dim = response_feature_dim_for_model(model)
    snapshots = collect_requested_outcome_snapshots(
        model=model,
        env_config=env_config,
        requests=_requests(corpus_frame),
        device=resolved_device,
    )
    rows: list[dict[str, Any]] = []
    for _, row in corpus_frame.reset_index(drop=True).iterrows():
        left = _snapshot(snapshots, int(row["left_seed"]), int(row["left_step"]))
        right = _snapshot(snapshots, int(row["right_seed"]), int(row["right_step"]))
        relocated = relocate_outcome_snapshot(
            left,
            body_longitudinal=float(row["relocated_obstacle_body_x"]),
            body_lateral=float(row["relocated_obstacle_body_y"]),
            half_width=float(row["relocated_obstacle_half_width"]),
        )
        normal, normal_actions = replay_outcome_variant(
            model=model,
            snapshot=relocated,
            env_config=env_config,
            variant="normal",
            response_dim=response_dim,
            variant_hidden=None,
            normal_first_action=None,
            normal_actions=None,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_first_action = np.asarray(
            [normal["first_steer"], normal["first_throttle"], normal["first_brake"]],
            dtype=np.float32,
        )
        wrong, _ = replay_outcome_variant(
            model=model,
            snapshot=relocated,
            env_config=env_config,
            variant="wrong_matched_history",
            response_dim=response_dim,
            variant_hidden=right.hidden,
            normal_first_action=normal_first_action,
            normal_actions=normal_actions,
            max_continuation_steps=max_continuation_steps,
            device=resolved_device,
        )
        normal_margin = float(normal.get("min_clearance_margin", float("nan")))
        wrong_margin = float(wrong.get("min_clearance_margin", float("nan")))
        margin_gap = (
            normal_margin - wrong_margin
            if np.isfinite(normal_margin) and np.isfinite(wrong_margin)
            else float("nan")
        )
        normal_success = bool(normal.get("success", False))
        wrong_success = bool(wrong.get("success", False))
        rows.append(
            {
                "policy": checkpoint_spec.label,
                "checkpoint": str(checkpoint_spec.path),
                "row_id": int(row["row_id"]),
                "target": str(row["target"]),
                "physical_pair_key": str(row["physical_pair_key"]),
                "left_seed": int(row["left_seed"]),
                "right_seed": int(row["right_seed"]),
                "left_step": int(row["left_step"]),
                "right_step": int(row["right_step"]),
                "relocated_obstacle_body_x": float(row["relocated_obstacle_body_x"]),
                "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
                "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
                "normal_success": normal_success,
                "wrong_history_success": wrong_success,
                "success_drop": bool(normal_success and not wrong_success),
                "normal_margin": normal_margin,
                "wrong_history_margin": wrong_margin,
                "margin_gap": margin_gap,
                **_result_fields("normal", normal),
                **_result_fields("wrong_history", wrong),
            }
        )
    return rows


def summarize_replay_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for (policy, target), group in frame.groupby(["policy", "target"], observed=True):
        summary_rows.append(_summary_row(str(policy), str(target), group))
    for policy, group in frame.groupby("policy", observed=True):
        summary_rows.append(_summary_row(str(policy), "__all__", group))
    return summary_rows


def _summary_row(policy: str, target: str, group: pd.DataFrame) -> dict[str, Any]:
    gaps = group["margin_gap"].astype(float)
    finite_gaps = gaps[np.isfinite(gaps)]
    return {
        "policy": policy,
        "target": target,
        "rows": int(len(group)),
        "physical_pairs": int(group["physical_pair_key"].nunique()),
        "normal_success_rate": float(group["normal_success"].astype(bool).mean()),
        "wrong_history_success_rate": float(group["wrong_history_success"].astype(bool).mean()),
        "success_drop_count": int(group["success_drop"].astype(bool).sum()),
        "success_drop_rate": float(group["success_drop"].astype(bool).mean()),
        "normal_margin_mean": float(group["normal_margin"].astype(float).mean()),
        "wrong_history_margin_mean": float(group["wrong_history_margin"].astype(float).mean()),
        "margin_gap_mean": float(finite_gaps.mean()) if len(finite_gaps) else float("nan"),
        "margin_gap_min": float(finite_gaps.min()) if len(finite_gaps) else float("nan"),
        "margin_gap_max": float(finite_gaps.max()) if len(finite_gaps) else float("nan"),
        "wrong_first_action_distance_mean": float(group["wrong_history_first_action_distance"].astype(float).mean()),
        "wrong_trajectory_distance_mean": float(group["wrong_history_trajectory_distance_mean"].astype(float).mean()),
    }


def compare_policy_replays(
    rows: list[dict[str, Any]],
    *,
    baseline_policy: str,
    candidate_policy: str,
    max_normal_success_drop: float,
    max_normal_margin_regression: float,
    max_margin_gap_regression: float,
    max_success_drop_count_regression: int,
) -> dict[str, Any]:
    frame = pd.DataFrame(rows)
    baseline = frame[frame["policy"].astype(str) == str(baseline_policy)].copy()
    candidate = frame[frame["policy"].astype(str) == str(candidate_policy)].copy()
    if baseline.empty or candidate.empty:
        raise ValueError("baseline and candidate policies must both have replay rows")
    merged = baseline.merge(
        candidate,
        on="row_id",
        suffixes=("_baseline", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(baseline) or len(merged) != len(candidate):
        raise ValueError("baseline and candidate replay rows must cover the same row_id set")
    baseline_normal_success = float(merged["normal_success_baseline"].astype(bool).mean())
    candidate_normal_success = float(merged["normal_success_candidate"].astype(bool).mean())
    baseline_wrong_success = float(merged["wrong_history_success_baseline"].astype(bool).mean())
    candidate_wrong_success = float(merged["wrong_history_success_candidate"].astype(bool).mean())
    baseline_success_drops = int(merged["success_drop_baseline"].astype(bool).sum())
    candidate_success_drops = int(merged["success_drop_candidate"].astype(bool).sum())
    normal_success_delta = candidate_normal_success - baseline_normal_success
    normal_margin_delta = float(
        merged["normal_margin_candidate"].astype(float).mean()
        - merged["normal_margin_baseline"].astype(float).mean()
    )
    margin_gap_delta = float(
        merged["margin_gap_candidate"].astype(float).mean()
        - merged["margin_gap_baseline"].astype(float).mean()
    )
    success_drop_delta = candidate_success_drops - baseline_success_drops
    gates = {
        "normal_success_retention": bool(normal_success_delta >= -float(max_normal_success_drop)),
        "normal_margin_retention": bool(normal_margin_delta >= -float(max_normal_margin_regression)),
        "wrong_history_gap_retention": bool(margin_gap_delta >= -float(max_margin_gap_regression)),
        "success_drop_count_retention": bool(success_drop_delta >= -int(max_success_drop_count_regression)),
    }
    return {
        "baseline_policy": str(baseline_policy),
        "candidate_policy": str(candidate_policy),
        "rows": int(len(merged)),
        "baseline_normal_success_rate": baseline_normal_success,
        "candidate_normal_success_rate": candidate_normal_success,
        "normal_success_delta": normal_success_delta,
        "baseline_wrong_history_success_rate": baseline_wrong_success,
        "candidate_wrong_history_success_rate": candidate_wrong_success,
        "wrong_history_success_delta": candidate_wrong_success - baseline_wrong_success,
        "baseline_success_drop_count": baseline_success_drops,
        "candidate_success_drop_count": candidate_success_drops,
        "success_drop_count_delta": success_drop_delta,
        "normal_margin_mean_delta": normal_margin_delta,
        "margin_gap_mean_delta": margin_gap_delta,
        "max_normal_success_drop": float(max_normal_success_drop),
        "max_normal_margin_regression": float(max_normal_margin_regression),
        "max_margin_gap_regression": float(max_margin_gap_regression),
        "max_success_drop_count_regression": int(max_success_drop_count_regression),
        **{f"{name}_pass": passed for name, passed in gates.items()},
        "gate_pass": bool(all(gates.values())),
    }


def run_boundary_outcome_replay_gate(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    corpus_csv: Path,
    env_config_path: Path,
    max_rows: int,
    max_continuation_steps: int,
    baseline_policy: str,
    candidate_policy: str,
    max_normal_success_drop: float,
    max_normal_margin_regression: float,
    max_margin_gap_regression: float,
    max_success_drop_count_regression: int,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    corpus_frame = pd.read_csv(corpus_csv)
    validate_corpus_frame(corpus_frame)
    if max_rows > 0:
        corpus_frame = corpus_frame.sort_values(["row_id"]).head(int(max_rows)).reset_index(drop=True)
    all_rows: list[dict[str, Any]] = []
    for checkpoint_spec in checkpoint_specs:
        all_rows.extend(
            replay_boundary_rows_for_policy(
                checkpoint_spec=checkpoint_spec,
                corpus_frame=corpus_frame,
                env_config_path=env_config_path,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
        )
    summary_rows = summarize_replay_rows(all_rows)
    comparison = compare_policy_replays(
        all_rows,
        baseline_policy=baseline_policy,
        candidate_policy=candidate_policy,
        max_normal_success_drop=max_normal_success_drop,
        max_normal_margin_regression=max_normal_margin_regression,
        max_margin_gap_regression=max_margin_gap_regression,
        max_success_drop_count_regression=max_success_drop_count_regression,
    )
    write_csv_rows(run_dir / "boundary_replay_rows.csv", all_rows)
    write_csv_rows(run_dir / "policy_summary.csv", summary_rows)
    write_csv_rows(run_dir / "comparison_summary.csv", [comparison])
    result = {
        "run_type": "boundary_outcome_replay_gate",
        "checkpoints": [{"label": spec.label, "path": spec.path} for spec in checkpoint_specs],
        "corpus_csv": corpus_csv,
        "env_config": env_config_path,
        "max_rows": int(max_rows),
        "max_continuation_steps": int(max_continuation_steps),
        "device": str(resolve_device(device)),
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "replay_rows_csv": run_dir / "boundary_replay_rows.csv",
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "comparison_summary_csv": run_dir / "comparison_summary.csv",
        **comparison,
    }
    write_json(run_dir / "summary.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay fixed boundary-outcome rows under candidate policies.")
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_spec, required=True)
    parser.add_argument("--corpus-csv", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--max-normal-success-drop", type=float, default=0.0)
    parser.add_argument("--max-normal-margin-regression", type=float, default=0.005)
    parser.add_argument("--max-margin-gap-regression", type=float, default=0.001)
    parser.add_argument("--max-success-drop-count-regression", type=int, default=0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="boundary_outcome_replay_gate")
    summary = run_boundary_outcome_replay_gate(
        checkpoint_specs=tuple(args.checkpoint_policy),
        corpus_csv=args.corpus_csv,
        env_config_path=args.env_config,
        max_rows=args.max_rows,
        max_continuation_steps=args.max_continuation_steps,
        baseline_policy=args.baseline_policy,
        candidate_policy=args.candidate_policy,
        max_normal_success_drop=args.max_normal_success_drop,
        max_normal_margin_regression=args.max_normal_margin_regression,
        max_margin_gap_regression=args.max_margin_gap_regression,
        max_success_drop_count_regression=args.max_success_drop_count_regression,
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
