#!/usr/bin/env python3
"""B1 moving-obstacle env-contract smoke.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/moving_obstacle_smoke.py [--quick]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.env import (
    AutoDriftEnv,
    DriftEnvConfig,
    EGO_OBS_DIM,
    LAST_ACTION_OBS_DIM,
    OBSTACLE_SLOT_DIM,
    ObstacleTaskConfig,
    ROAD_POINT_DIM,
)


REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/moving_obstacle_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/moving_obstacle_smoke.json"
QUICK_JSON = REPO / "experiments/feasibility_audit/moving_obstacle_smoke_quick.json"
RUN_DIR = REPO / "runs/feasibility_audit/moving_obstacle_smoke"
SEED_BASE = 20260823


def obstacle_slot_start(config: DriftEnvConfig) -> int:
    road_dim = 2 * config.road_lookahead_count * ROAD_POINT_DIM
    action_dim = LAST_ACTION_OBS_DIM if config.action_history_mode == "full" else 0
    return EGO_OBS_DIM + action_dim + road_dim


def first_obstacle_slot(obs: np.ndarray, config: DriftEnvConfig) -> np.ndarray:
    start = obstacle_slot_start(config)
    return np.asarray(obs[start:start + OBSTACLE_SLOT_DIM], dtype=np.float64)


def env_config(*, motion_mode: str, relative_velocity_mode: str) -> DriftEnvConfig:
    return DriftEnvConfig(
        dt=0.02,
        max_steps=90,
        track_kind="circle",
        track_radius=60.0,
        track_width=8.5,
        speed_range=(12.0, 12.0),
        beta_target_range=(0.04, 0.04),
        friction_limited_speed=False,
        obstacle_relative_velocity_mode=relative_velocity_mode,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(24.0, 24.0),
            half_width_range=(0.7, 0.7),
            lateral_offset_range=(-2.0, -2.0),
            finish_on_pass=True,
            pass_reward=10.0,
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
            max_sample_attempts=100,
            perception_reveal_step=0,
            motion_mode=motion_mode,
            crosser_lateral_velocity_range=(4.0, 4.0),
        ),
    )


def scripted_action(obs: np.ndarray, config: DriftEnvConfig) -> np.ndarray:
    slot = first_obstacle_slot(obs, config)
    if slot[0] <= 0.0:
        return np.array([0.0, 0.0, -1.0], dtype=np.float32)
    x_m = float(slot[1] * 80.0)
    y_m = float(slot[2] * 20.0)
    steer = -0.25 * float(np.sign(y_m)) if x_m < 22.0 and abs(y_m) < 3.0 else 0.0
    return np.array([steer, 0.0, -1.0], dtype=np.float32)


def frame_row(mode: str, seed: int, step: int, obs: np.ndarray, info: dict[str, Any],
              reward: float, terminated: bool, truncated: bool, config: DriftEnvConfig) -> dict[str, Any]:
    slot = first_obstacle_slot(obs, config)
    return {
        "mode": mode,
        "seed": seed,
        "step": step,
        "present": float(slot[0]),
        "slot_x_m": float(slot[1] * 80.0),
        "slot_y_m": float(slot[2] * 20.0),
        "slot_rel_vx_mps": float(slot[3] * 20.0),
        "slot_rel_vy_mps": float(slot[4] * 12.0),
        "active_obstacle_body_x": float(info["active_obstacle_body_x"]),
        "active_obstacle_body_y": float(info["active_obstacle_body_y"]),
        "obstacle_motion_mode": str(info["obstacle_motion_mode"]),
        "obstacle_label": str(info["obstacle_label"]),
        "obstacle_lateral_velocity": float(info["obstacle_lateral_velocity"]),
        "predicted_lateral_offset_at_arrival": float(info["obstacle_predicted_lateral_offset_at_arrival"]),
        "required_lateral_offset": float(info["obstacle_required_lateral_offset"]),
        "reward": float(reward),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "termination_reason": str(info["termination_reason"]),
        "completion_reason": str(info["completion_reason"]),
        "collision": bool(info["collision"]),
        "obstacle_completed": bool(info["obstacle_completed"]),
    }


def rollout(mode: str, seed: int, *, max_steps: int = 40) -> list[dict[str, Any]]:
    if mode == "legacy_static_zero_relvel":
        config = env_config(motion_mode="static", relative_velocity_mode="zero")
    elif mode == "moving_crosser_zero_relvel":
        config = env_config(motion_mode="constant_velocity_crosser", relative_velocity_mode="zero")
    elif mode == "moving_crosser_ego_relvel":
        config = env_config(motion_mode="constant_velocity_crosser", relative_velocity_mode="ego")
    else:
        raise ValueError(f"unknown mode {mode!r}")

    env = AutoDriftEnv(config)
    obs, info = env.reset(seed=seed)
    rows = [frame_row(mode, seed, 0, obs, info, 0.0, False, False, config)]
    for step in range(1, max_steps + 1):
        obs, reward, terminated, truncated, info = env.step(scripted_action(obs, config))
        rows.append(frame_row(mode, seed, step, obs, info, reward, terminated, truncated, config))
        if terminated or truncated:
            break
    env.close()
    return rows


def replay_signature(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "step",
        "slot_x_m",
        "slot_y_m",
        "slot_rel_vx_mps",
        "slot_rel_vy_mps",
        "active_obstacle_body_x",
        "active_obstacle_body_y",
        "reward",
        "terminated",
        "truncated",
        "termination_reason",
        "completion_reason",
        "collision",
        "obstacle_completed",
    ]
    return [{key: row[key] for key in keys} for row in rows]


def deterministic_equal(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    if len(left) != len(right):
        return False
    for lhs, rhs in zip(replay_signature(left), replay_signature(right), strict=True):
        if lhs.keys() != rhs.keys():
            return False
        for key, value in lhs.items():
            other = rhs[key]
            if isinstance(value, float):
                if abs(value - float(other)) > 1e-7:
                    return False
            elif value != other:
                return False
    return True


def summarize(rows: list[dict[str, Any]], replay_seeds: list[int]) -> dict[str, Any]:
    zero_modes = {"legacy_static_zero_relvel", "moving_crosser_zero_relvel"}
    zero_violations = [
        row for row in rows
        if row["mode"] in zero_modes
        and row["present"] == 1.0
        and (abs(row["slot_rel_vx_mps"]) > 1e-12 or abs(row["slot_rel_vy_mps"]) > 1e-12)
    ]
    moving_ego = [row for row in rows if row["mode"] == "moving_crosser_ego_relvel"]
    by_seed: dict[int, list[dict[str, Any]]] = {}
    for row in moving_ego:
        by_seed.setdefault(int(row["seed"]), []).append(row)
    body_y_deltas = {
        seed: max(row["active_obstacle_body_y"] for row in seed_rows)
        - min(row["active_obstacle_body_y"] for row in seed_rows)
        for seed, seed_rows in by_seed.items()
        if len(seed_rows) >= 9
    }
    rel_norm_max = max(
        (float(np.hypot(row["slot_rel_vx_mps"], row["slot_rel_vy_mps"])) for row in moving_ego),
        default=0.0,
    )
    moving_rows = [row for row in rows if row["mode"].startswith("moving_crosser")]
    label_rows_ok = [
        row for row in moving_rows
        if abs(row["obstacle_lateral_velocity"]) > 0.0
        and np.isfinite(row["predicted_lateral_offset_at_arrival"])
        and row["required_lateral_offset"] >= 0.0
    ]
    replay_failures = []
    for seed in replay_seeds:
        left = rollout("moving_crosser_ego_relvel", seed)
        right = rollout("moving_crosser_ego_relvel", seed)
        if not deterministic_equal(left, right):
            replay_failures.append(seed)

    readouts = {
        "legacy_zero_relvel_contract_pass": len(zero_violations) == 0,
        "zero_relvel_violation_count": len(zero_violations),
        "moving_kinematics_pass": bool(body_y_deltas) and all(delta >= 0.5 for delta in body_y_deltas.values()),
        "moving_body_y_delta_min": min(body_y_deltas.values()) if body_y_deltas else 0.0,
        "ego_relvel_nonzero_pass": rel_norm_max > 1e-6,
        "ego_relvel_norm_max_mps": rel_norm_max,
        "label_rederivation_pass": len(label_rows_ok) == len(moving_rows) and len(moving_rows) > 0,
        "dynamic_label_rows": len(label_rows_ok),
        "dynamic_rows": len(moving_rows),
        "deterministic_replay_pass": len(replay_failures) == 0,
        "deterministic_replay_failures": replay_failures,
    }
    readouts["all_pass"] = all(
        bool(readouts[key])
        for key in (
            "legacy_zero_relvel_contract_pass",
            "moving_kinematics_pass",
            "ego_relvel_nonzero_pass",
            "label_rederivation_pass",
            "deterministic_replay_pass",
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
    modes = [
        "legacy_static_zero_relvel",
        "moving_crosser_zero_relvel",
        "moving_crosser_ego_relvel",
    ]

    rows: list[dict[str, Any]] = []
    for mode in modes:
        for seed in seeds:
            rows.extend(rollout(mode, seed))
    readouts = summarize(rows, replay_seeds)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows_csv = RUN_DIR / ("episode_rows_quick.csv" if args.quick else "episode_rows.csv")
    with rows_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "protocol": "moving_obstacle_kinematics_smoke",
        "quick_mode": bool(args.quick),
        "generated_by": "scripts/feasibility_audit/moving_obstacle_smoke.py",
        "preregistration": str(PREREG),
        "claim_boundary": prereg["claim_boundary"],
        "seed_base": SEED_BASE,
        "seed_count": seed_count,
        "modes": modes,
        "readouts": readouts,
        "decision": {
            "accepted": bool(readouts["all_pass"]),
            "rule": prereg["decision_rule"],
        },
        "budget": {
            "episodes": len(seeds) * len(modes),
            "frames": len(rows),
            "deterministic_replays": len(replay_seeds),
        },
        "episode_rows_csv": str(rows_csv),
    }
    out = QUICK_JSON if args.quick else RESULTS_JSON
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"result": str(out), "accepted": payload["decision"]["accepted"], **readouts}, indent=2))
    if not readouts["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
