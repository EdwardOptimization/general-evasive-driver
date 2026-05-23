"""Targeted replay for exact old-key neighborhood compact cases."""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.critical_key_replay_guard import CheckpointPolicy, parse_checkpoint_policy
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import load_env_config
from autodrift.hidden_swap_gate import DecisionSnapshot, clone_hidden
from autodrift.outcome_sensitive_corpus import (
    ProbeConfig,
    build_outcome_sensitive_row,
    obstacle_override_config,
    probe_action,
    relocate_obstacle_snapshot,
    should_probe,
)
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import ActorCritic, resolve_device


COMPACT_REQUIRED_COLUMNS = [
    "key",
    "seed",
    "source_condition",
    "source_step",
    "paired_step",
    "target_obstacle_distance",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
    "reference_normal_margin",
    "reference_wrong_history_margin",
    "reference_margin_gap",
]


def _require_columns(frame: pd.DataFrame, columns: list[str], *, label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def _tuple_range(value: Any) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"expected two-value range, got {value!r}")
    return (float(value[0]), float(value[1]))


def _randomization(raw: Any) -> dict[str, tuple[float, float]]:
    output: dict[str, tuple[float, float]] = {}
    for key, value in (raw or {}).items():
        output[str(key)] = _tuple_range(value)
    return output


def _probe_config(raw: dict[str, Any]) -> ProbeConfig:
    return ProbeConfig(
        strategy=str(raw.get("strategy", "steer_brake")),
        steer_amplitude=float(raw.get("steer_amplitude", 0.25)),
        brake_level=float(raw.get("brake_level", 0.20)),
        throttle_level=float(raw.get("throttle_level", 0.0)),
        period_steps=int(raw.get("period_steps", 20)),
        until_step=raw.get("until_step"),
        until_distance=raw.get("until_distance"),
    )


def _requests_by_condition(compact: pd.DataFrame) -> dict[str, dict[int, set[int]]]:
    requests: dict[str, dict[int, set[int]]] = {"nominal": {}, "perturbed": {}}
    for _, row in compact.iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        if source not in requests:
            raise ValueError(f"unexpected source_condition {source!r}")
        paired = "perturbed" if source == "nominal" else "nominal"
        requests[source].setdefault(seed, set()).add(int(row["source_step"]))
        requests[paired].setdefault(seed, set()).add(int(row["paired_step"]))
    return requests


def collect_targeted_probe_snapshots(
    *,
    model: ActorCritic,
    env_config: DriftEnvConfig,
    condition: str,
    seed: int,
    requested_steps: set[int],
    max_probe_steps: int,
    probe_config: ProbeConfig,
) -> dict[int, DecisionSnapshot]:
    if not requested_steps:
        return {}
    max_step = max(int(step) for step in requested_steps)
    env = AutoDriftEnv(env_config)
    snapshots: dict[int, DecisionSnapshot] = {}
    try:
        obs, info = env.reset(seed=int(seed))
        hidden = None
        terminated = False
        truncated = False
        probe_steps = 0
        probe_steer_abs_sum = 0.0
        probe_brake_sum = 0.0
        while not (terminated or truncated):
            step = int(info.get("step", 0))
            if step in requested_steps:
                snapshot_info = dict(info)
                snapshot_info["active_probe_strategy"] = probe_config.strategy
                snapshot_info["active_probe_steps"] = int(probe_steps)
                snapshot_info["active_probe_steer_abs_mean"] = (
                    probe_steer_abs_sum / max(probe_steps, 1) if probe_steps else 0.0
                )
                snapshot_info["active_probe_brake_mean"] = (
                    probe_brake_sum / max(probe_steps, 1) if probe_steps else 0.0
                )
                snapshots[int(step)] = DecisionSnapshot(
                    condition=condition,
                    seed=int(seed),
                    step=int(step),
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=clone_hidden(hidden),
                    env=copy.deepcopy(env),
                    info=snapshot_info,
                    obstacle_distance=float(info.get("obstacle_distance", float("nan"))),
                    snapshot_score=0.0,
                )
            if step >= max_step and all(int(step_item) in snapshots for step_item in requested_steps):
                break
            if step >= int(max_probe_steps):
                break
            policy_action, _, _, next_hidden = model.act_recurrent(obs, hidden, deterministic=True)
            hidden = next_hidden
            if should_probe(info, probe_config):
                action = probe_action(probe_config.strategy, step, probe_config)
                probe_steps += 1
                probe_steer_abs_sum += abs(float(action[0]))
                probe_brake_sum += max((float(action[2]) + 1.0) * 0.5, 0.0)
            else:
                action = policy_action
            obs, _, terminated, truncated, info = env.step(action)
    finally:
        env.close()
    return snapshots


def _snapshot(
    snapshots: dict[str, dict[int, dict[int, DecisionSnapshot]]],
    condition: str,
    seed: int,
    step: int,
) -> DecisionSnapshot | None:
    return snapshots.get(condition, {}).get(int(seed), {}).get(int(step))


def replay_compact_cases_for_policy(
    *,
    model: ActorCritic,
    compact: pd.DataFrame,
    manifest: dict[str, Any],
    policy_name: str,
) -> list[dict[str, Any]]:
    _require_columns(compact, COMPACT_REQUIRED_COLUMNS, label="compact corpus")
    base_config = obstacle_override_config(
        load_env_config(Path(manifest["env_config"])),
        distance_range=None,
        half_width_range=None,
        perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
        perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
    )
    configs = {
        "nominal": condition_config(
            base_config,
            _tuple_range(manifest["nominal_friction_mu_range"]),
            _randomization(manifest.get("nominal_randomization")),
        ),
        "perturbed": condition_config(
            base_config,
            _tuple_range(manifest["perturbed_friction_mu_range"]),
            _randomization(manifest.get("perturbed_randomization")),
        ),
    }
    probe = _probe_config(manifest.get("probe", {}))
    requests = _requests_by_condition(compact)
    snapshots: dict[str, dict[int, dict[int, DecisionSnapshot]]] = {"nominal": {}, "perturbed": {}}
    for condition, seed_requests in requests.items():
        for seed, steps in seed_requests.items():
            snapshots[condition][int(seed)] = collect_targeted_probe_snapshots(
                model=model,
                env_config=configs[condition],
                condition=condition,
                seed=int(seed),
                requested_steps=set(int(step) for step in steps),
                max_probe_steps=int(manifest["max_probe_steps"]),
                probe_config=probe,
            )

    rows: list[dict[str, Any]] = []
    for _, row in compact.reset_index(drop=True).iterrows():
        seed = int(row["seed"])
        source = str(row["source_condition"])
        paired = "perturbed" if source == "nominal" else "nominal"
        source_snapshot = _snapshot(snapshots, source, seed, int(row["source_step"]))
        paired_snapshot = _snapshot(snapshots, paired, seed, int(row["paired_step"]))
        base_row = {
            "policy": policy_name,
            "key": str(row["key"]),
            "seed": seed,
            "source_condition": source,
            "source_step": int(row["source_step"]),
            "paired_step": int(row["paired_step"]),
            "target_obstacle_distance": float(row["target_obstacle_distance"]),
            "relocated_obstacle_body_y": float(row["relocated_obstacle_body_y"]),
            "relocated_obstacle_half_width": float(row["relocated_obstacle_half_width"]),
            "reference_normal_margin": float(row["reference_normal_margin"]),
            "reference_wrong_history_margin": float(row["reference_wrong_history_margin"]),
            "reference_margin_gap": float(row["reference_margin_gap"]),
        }
        if source_snapshot is None or paired_snapshot is None:
            rows.append(
                {
                    **base_row,
                    "found_rows": 0,
                    "accepted": False,
                    "normal_success": False,
                    "normal_margin": float("nan"),
                    "wrong_history_margin": float("nan"),
                    "margin_gap": float("nan"),
                    "margin_gap_delta_vs_reference": float("nan"),
                }
            )
            continue

        snapshots_by_condition = {
            source: source_snapshot,
            paired: paired_snapshot,
        }
        relocated = {
            condition: relocate_obstacle_snapshot(
                snapshot,
                body_longitudinal=float(row["target_obstacle_distance"]),
                body_lateral=float(row["relocated_obstacle_body_y"]),
                half_width=float(row["relocated_obstacle_half_width"]),
            )
            for condition, snapshot in snapshots_by_condition.items()
        }
        outcome_row, _ = build_outcome_sensitive_row(
            seed,
            float(row["target_obstacle_distance"]),
            relocated["nominal"],
            relocated["perturbed"],
            model,
            configs["nominal"],
            configs["perturbed"],
            max_visible_distance=float(manifest["max_visible_distance"]),
            max_response_distance=manifest.get("max_response_distance"),
            max_context_distance=manifest.get("max_context_distance"),
            min_margin_gap=float(manifest["min_margin_gap"]),
            min_normal_margin=manifest.get("min_normal_margin"),
            max_normal_margin=manifest.get("max_normal_margin"),
            require_normal_success=bool(manifest["require_normal_success"]),
            max_continuation_steps=manifest.get("max_continuation_steps"),
        )
        normal_margin = float(outcome_row.get(f"{source}_normal_margin", float("nan")))
        wrong_margin = float(outcome_row.get(f"{source}_wrong_history_margin", float("nan")))
        margin_gap = float(outcome_row.get(f"{source}_margin_gap", float("nan")))
        rows.append(
            {
                **base_row,
                "found_rows": 1,
                "accepted": bool(outcome_row.get(f"{source}_accepted_outcome_sensitive", False)),
                "normal_success": bool(outcome_row.get(f"{source}_normal_success", False)),
                "normal_margin": normal_margin,
                "wrong_history_margin": wrong_margin,
                "margin_gap": margin_gap,
                "margin_gap_delta_vs_reference": margin_gap - float(row["reference_margin_gap"]),
            }
        )
    return rows


def summarize_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(rows)
    summaries: list[dict[str, Any]] = []
    for policy, group in frame.groupby("policy", observed=True):
        summaries.append(
            {
                "policy": str(policy),
                "cases": int(len(group)),
                "found_cases": int(group["found_rows"].astype(int).sum()),
                "accepted_cases": int(group["accepted"].astype(bool).sum()),
                "policy_pass": bool(group["accepted"].astype(bool).all()),
                "normal_success_cases": int(group["normal_success"].astype(bool).sum()),
                "margin_gap_mean": float(group["margin_gap"].astype(float).mean()),
                "margin_gap_min": float(group["margin_gap"].astype(float).min()),
                "margin_gap_delta_mean": float(group["margin_gap_delta_vs_reference"].astype(float).mean()),
                "margin_gap_delta_min": float(group["margin_gap_delta_vs_reference"].astype(float).min()),
            }
        )
    return summaries


def run_targeted_replay(
    *,
    reference_manifest: Path,
    compact_corpus_csv: Path,
    checkpoint_policies: tuple[CheckpointPolicy, ...],
    run_dir: Path,
    device: str,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(reference_manifest)
    compact = pd.read_csv(compact_corpus_csv)
    if "record_type" in compact:
        compact = compact[compact["record_type"].astype(str).eq("m341_mined_case")].copy()
    all_rows: list[dict[str, Any]] = []
    resolved_device = resolve_device(device)
    for policy in checkpoint_policies:
        model, _ = load_actor_critic_checkpoint(policy.path, device=str(resolved_device))
        model.eval()
        all_rows.extend(
            replay_compact_cases_for_policy(
                model=model,
                compact=compact,
                manifest=manifest,
                policy_name=policy.name,
            )
        )
    summaries = summarize_policy_rows(all_rows)
    write_csv_rows(run_dir / "guard_results.csv", all_rows)
    write_csv_rows(run_dir / "policy_summary.csv", summaries)
    summary = {
        "run_type": "old_key_neighborhood_targeted_replay",
        "actor_inputs_changed": False,
        "ppo_or_actor_update_run": False,
        "reference_manifest": reference_manifest,
        "compact_corpus_csv": compact_corpus_csv,
        "checkpoint_policies": [asdict(policy) for policy in checkpoint_policies],
        "device": str(resolved_device),
        "cases": int(len(compact)),
        "policies": int(len(checkpoint_policies)),
        "guard_results_csv": run_dir / "guard_results.csv",
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "policy_summary": summaries,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Targeted replay for exact old-key neighborhood compact cases.")
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--compact-corpus-csv", type=Path, required=True)
    parser.add_argument("--checkpoint-policy", action="append", type=parse_checkpoint_policy, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="old_key_targeted_replay")
    summary = run_targeted_replay(
        reference_manifest=args.reference_manifest,
        compact_corpus_csv=args.compact_corpus_csv,
        checkpoint_policies=tuple(args.checkpoint_policy),
        device=args.device,
        run_dir=run_dir,
    )
    print(pd.DataFrame(summary["policy_summary"]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
