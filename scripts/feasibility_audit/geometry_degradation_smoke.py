#!/usr/bin/env python3
"""B3 geometry-channel degradation and split-mu expressibility smoke.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/geometry_degradation_smoke.py [--quick]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.observation_degradation_wrapper import make_observation_degradation_env


REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/geometry_degradation_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/geometry_degradation_smoke.json"
QUICK_JSON = REPO / "experiments/feasibility_audit/geometry_degradation_smoke_quick.json"
RUN_DIR = REPO / "runs/feasibility_audit/geometry_degradation_smoke"
SEED_BASE = 20260825

ROAD_SLICE = slice(12, 44)
SLOT0_CONTINUOUS = slice(45, 49)
SLOT0_PRESENT_SIZE_INDICES = np.array([44, 49, 50], dtype=np.int64)
EMPTY_SLOT_SLICES = (slice(51, 58), slice(58, 65), slice(65, 72))


def env_config() -> DriftEnvConfig:
    return DriftEnvConfig(
        dt=0.02,
        max_steps=80,
        track_kind="circle",
        track_radius=70.0,
        track_width=8.0,
        speed_range=(12.0, 12.0),
        beta_target_range=(0.04, 0.04),
        friction_limited_speed=False,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(26.0, 26.0),
            half_width_range=(0.8, 0.8),
            lateral_offset_range=(-1.2, -1.2),
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
            max_sample_attempts=50,
            perception_reveal_step=0,
        ),
    )


def action_sequence(seed: int, steps: int) -> list[np.ndarray]:
    rng = np.random.default_rng([SEED_BASE, seed, 17])
    return [
        np.array(
            [
                0.10 * np.sin(0.17 * step) + float(rng.uniform(-0.02, 0.02)),
                -1.0,
                -1.0,
            ],
            dtype=np.float32,
        )
        for step in range(steps)
    ]


def rollout(env, seed: int, actions: list[np.ndarray]) -> list[tuple[np.ndarray, dict[str, Any], bool, bool]]:
    obs, info = env.reset(seed=seed)
    rows = [(np.asarray(obs, dtype=np.float32).copy(), dict(info), False, False)]
    for action in actions:
        obs, _reward, terminated, truncated, info = env.step(action)
        rows.append((np.asarray(obs, dtype=np.float32).copy(), dict(info), bool(terminated), bool(truncated)))
        if terminated or truncated:
            break
    env.close()
    return rows


def degraded_env(config: DriftEnvConfig):
    return make_observation_degradation_env(
        config,
        geometry_scope="road_and_obstacle",
        geometry_noise_std=0.04,
    )


def paired_rollout(seed: int, *, max_steps: int = 24) -> list[dict[str, Any]]:
    config = env_config()
    actions = action_sequence(seed, max_steps)
    raw = rollout(AutoDriftEnv(config), seed, actions)
    degraded = rollout(degraded_env(config), seed, actions)
    rows: list[dict[str, Any]] = []
    for step, ((raw_obs, raw_info, raw_term, raw_trunc), (deg_obs, deg_info, deg_term, deg_trunc)) in enumerate(
        zip(raw, degraded, strict=True)
    ):
        empty_slot_delta = max(
            float(np.max(np.abs(deg_obs[slot] - raw_obs[slot])))
            for slot in EMPTY_SLOT_SLICES
        )
        rows.append(
            {
                "seed": seed,
                "step": step,
                "obs_shape_raw": int(raw_obs.shape[0]),
                "obs_shape_degraded": int(deg_obs.shape[0]),
                "ego_command_delta_max_abs": float(np.max(np.abs(deg_obs[:12] - raw_obs[:12]))),
                "road_delta_max_abs": float(np.max(np.abs(deg_obs[ROAD_SLICE] - raw_obs[ROAD_SLICE]))),
                "slot0_continuous_delta_max_abs": float(
                    np.max(np.abs(deg_obs[SLOT0_CONTINUOUS] - raw_obs[SLOT0_CONTINUOUS]))
                ),
                "slot0_present_size_delta_max_abs": float(
                    np.max(np.abs(deg_obs[SLOT0_PRESENT_SIZE_INDICES] - raw_obs[SLOT0_PRESENT_SIZE_INDICES]))
                ),
                "empty_slot_delta_max_abs": empty_slot_delta,
                "raw_terminated": raw_term,
                "degraded_terminated": deg_term,
                "raw_truncated": raw_trunc,
                "degraded_truncated": deg_trunc,
                "raw_termination_reason": str(raw_info["termination_reason"]),
                "degraded_termination_reason": str(deg_info["termination_reason"]),
            }
        )
    return rows


def replay_signature(frames: list[tuple[np.ndarray, dict[str, Any], bool, bool]]) -> list[dict[str, Any]]:
    return [
        {
            "obs": obs.tolist(),
            "terminated": terminated,
            "truncated": truncated,
            "termination_reason": str(info["termination_reason"]),
            "completion_reason": str(info["completion_reason"]),
        }
        for obs, info, terminated, truncated in frames
    ]


def deterministic_equal(left: list[tuple[np.ndarray, dict[str, Any], bool, bool]],
                        right: list[tuple[np.ndarray, dict[str, Any], bool, bool]]) -> bool:
    lhs = replay_signature(left)
    rhs = replay_signature(right)
    if len(lhs) != len(rhs):
        return False
    for left_row, right_row in zip(lhs, rhs, strict=True):
        if left_row.keys() != right_row.keys():
            return False
        if not np.allclose(left_row["obs"], right_row["obs"], atol=0.0, rtol=0.0):
            return False
        for key in ("terminated", "truncated", "termination_reason", "completion_reason"):
            if left_row[key] != right_row[key]:
                return False
    return True


def summarize(rows: list[dict[str, Any]], replay_seeds: list[int]) -> dict[str, Any]:
    road_deltas = [float(row["road_delta_max_abs"]) for row in rows]
    obstacle_deltas = [float(row["slot0_continuous_delta_max_abs"]) for row in rows]
    ego_command_deltas = [float(row["ego_command_delta_max_abs"]) for row in rows]
    present_size_deltas = [float(row["slot0_present_size_delta_max_abs"]) for row in rows]
    empty_slot_deltas = [float(row["empty_slot_delta_max_abs"]) for row in rows]
    replay_failures = []
    config = env_config()
    for seed in replay_seeds:
        actions = action_sequence(seed, 24)
        left = rollout(degraded_env(config), seed, actions)
        right = rollout(degraded_env(config), seed, actions)
        if not deterministic_equal(left, right):
            replay_failures.append(seed)

    readouts = {
        "episodes": len({int(row["seed"]) for row in rows}),
        "frames": len(rows),
        "obs72_shape_pass": all(int(row["obs_shape_raw"]) == 72 and int(row["obs_shape_degraded"]) == 72 for row in rows),
        "ego_command_untouched_pass": max(ego_command_deltas, default=0.0) <= 1e-12,
        "ego_command_delta_max_abs": max(ego_command_deltas, default=0.0),
        "road_boundary_degraded_pass": max(road_deltas, default=0.0) > 0.0,
        "road_delta_max_abs": max(road_deltas, default=0.0),
        "obstacle_geometry_degraded_pass": max(obstacle_deltas, default=0.0) > 0.0,
        "obstacle_continuous_delta_max_abs": max(obstacle_deltas, default=0.0),
        "present_and_size_untouched_pass": max(present_size_deltas, default=0.0) <= 1e-12,
        "present_size_delta_max_abs": max(present_size_deltas, default=0.0),
        "empty_slots_untouched_pass": max(empty_slot_deltas, default=0.0) <= 1e-12,
        "empty_slot_delta_max_abs": max(empty_slot_deltas, default=0.0),
        "termination_consistency_pass": all(
            row["raw_terminated"] == row["degraded_terminated"]
            and row["raw_truncated"] == row["degraded_truncated"]
            and row["raw_termination_reason"] == row["degraded_termination_reason"]
            for row in rows
        ),
        "deterministic_replay_pass": len(replay_failures) == 0,
        "deterministic_replay_failures": replay_failures,
        "split_mu_expressibility": {
            "current_sim_expressible": False,
            "current_obstacle_env_expressible": False,
            "source_only_four_wheel_primitives_present": True,
            "reason": (
                "DriftObstacleEnv currently runs SingleTrackDriftModel, a bicycle model with "
                "one scalar VehicleParams.mu and aggregated front/rear tire forces. That path "
                "has no left/right wheel contacts or per-side normal loads, so a split-mu flag "
                "there would be a fake label rather than a physical obstacle-env mechanism. "
                "The repository also contains source-only four-wheel HF0 primitives that can "
                "express split-mu source shapes, but they are not integrated as this B3 "
                "obstacle-env outcome backend."
            ),
        },
    }
    readouts["split_mu_declared_not_expressible_pass"] = (
        readouts["split_mu_expressibility"]["current_sim_expressible"] is False
    )
    readouts["all_pass"] = all(
        bool(readouts[key])
        for key in (
            "obs72_shape_pass",
            "ego_command_untouched_pass",
            "road_boundary_degraded_pass",
            "obstacle_geometry_degraded_pass",
            "present_and_size_untouched_pass",
            "empty_slots_untouched_pass",
            "termination_consistency_pass",
            "deterministic_replay_pass",
            "split_mu_declared_not_expressible_pass",
        )
    )
    return readouts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    seed_count = int(prereg["seed_discipline"]["quick_seed_count" if args.quick else "full_seed_count"])
    replay_count = min(int(prereg["seed_discipline"]["deterministic_replay_count"]), seed_count)
    seeds = [SEED_BASE + idx for idx in range(seed_count)]
    replay_seeds = seeds[:replay_count]

    rows: list[dict[str, Any]] = []
    for seed in seeds:
        rows.extend(paired_rollout(seed))
    readouts = summarize(rows, replay_seeds)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows_csv = RUN_DIR / ("frame_rows_quick.csv" if args.quick else "frame_rows.csv")
    with rows_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "protocol": "geometry_degradation_and_split_mu_expressibility_smoke",
        "quick": bool(args.quick),
        "roadmap_unit": "B3 geometry-channel degradation + split-mu",
        "preregistration": str(PREREG.relative_to(REPO)),
        "seed_base": SEED_BASE,
        "seed_count": seed_count,
        "replay_seeds": replay_seeds,
        "geometry_degradation_profile": {
            "geometry_scope": "road_and_obstacle",
            "geometry_noise_std": 0.04,
            "road_indices": [12, 43],
            "obstacle_continuous_indices": [45, 48],
            "obstacle_present_and_size_untouched": [44, 49, 50],
        },
        "readouts": readouts,
        "rows_csv": str(rows_csv.relative_to(REPO)),
        "claim_boundary": prereg["claim_boundary"],
    }
    output = QUICK_JSON if args.quick else RESULTS_JSON
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output.relative_to(REPO)), "all_pass": readouts["all_pass"]}, sort_keys=True))


if __name__ == "__main__":
    main()
