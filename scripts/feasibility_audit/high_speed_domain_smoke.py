#!/usr/bin/env python3
"""B2 high-speed observation-normalization and preview smoke.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/high_speed_domain_smoke.py [--quick]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.dynamics import RandomizationConfig
from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObservationScaleConfig, ObstacleTaskConfig


REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/high_speed_domain_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/high_speed_domain_smoke.json"
QUICK_JSON = REPO / "experiments/feasibility_audit/high_speed_domain_smoke_quick.json"
RUN_DIR = REPO / "runs/feasibility_audit/high_speed_domain_smoke"
SEED_BASE = 20260824

SELECTED_CHANNELS = {
    "ego_vx": [0],
    "ego_vy": [1],
    "ego_ax": [3],
    "ego_ay": [4],
    "road_y": list(range(13, 28, 2)) + list(range(29, 44, 2)),
    "obs_rel_vy": [48, 55, 62, 69],
}

HIGH_SPEED_SCALE = ObservationScaleConfig(
    ego_vx=40.0,
    ego_vy=40.0,
    ego_ax=50.0,
    ego_ay=60.0,
    road_y=60.0,
    obstacle_rel_vy=30.0,
    road_lookahead_time_s=2.5,
    road_lookahead_max_distance=120.0,
)


def env_config(mode: str) -> DriftEnvConfig:
    scaled = mode.startswith("scaled_")
    crosser = mode.endswith("_crosser")
    return DriftEnvConfig(
        dt=0.02,
        max_steps=70,
        track_kind="circle",
        track_radius=250.0,
        track_width=12.0,
        speed_range=(36.0, 36.0),
        beta_target_range=(0.04, 0.04),
        friction_limited_speed=False,
        max_speed_limit=45.0,
        obstacle_relative_velocity_mode="ego",
        observation_scale=HIGH_SPEED_SCALE if scaled else ObservationScaleConfig(),
        randomization=RandomizationConfig(
            mu_range=(1.15, 1.15),
            mass_scale_range=(1.0, 1.0),
            cg_shift_range=(0.0, 0.0),
            inertia_scale_range=(1.0, 1.0),
            tire_stiffness_scale_range=(1.0, 1.0),
            drive_scale_range=(1.0, 1.0),
            brake_scale_range=(1.0, 1.0),
            actuator_tau_scale_range=(1.0, 1.0),
        ),
        obstacle=ObstacleTaskConfig(
            enabled=crosser,
            distance_range=(55.0, 55.0),
            half_width_range=(0.7, 0.7),
            lateral_offset_range=(-4.0, -4.0),
            allowed_labels=("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
            finish_on_pass=False,
            max_sample_attempts=50,
            perception_reveal_step=0,
            motion_mode="constant_velocity_crosser" if crosser else "static",
            crosser_lateral_velocity_range=(24.0, 24.0),
        ),
    )


def scripted_action() -> np.ndarray:
    return np.array([0.0, -1.0, -1.0], dtype=np.float32)


def frame_row(mode: str, seed: int, step: int, obs: np.ndarray, info: dict[str, Any],
              terminated: bool, truncated: bool) -> dict[str, Any]:
    return {
        "mode": mode,
        "seed": seed,
        "step": step,
        "obs_shape": int(obs.shape[0]),
        "speed_ref": float(info["speed_ref"]),
        "speed": float(info["speed"]),
        "max_speed_limit": float(info["max_speed_limit"]),
        "road_lookahead_distance_max": float(info["road_lookahead_distance_max"]),
        "road_lookahead_time_s": float(info["road_lookahead_time_s"]),
        "obstacle_enabled": bool(info["obstacle_enabled"]),
        "obstacle_label": str(info["obstacle_label"]),
        "obstacle_lateral_velocity": float(info["obstacle_lateral_velocity"]),
        "obstacle_predicted_lateral_offset_at_arrival": float(
            info["obstacle_predicted_lateral_offset_at_arrival"]
        ),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "termination_reason": str(info["termination_reason"]),
        "completion_reason": str(info["completion_reason"]),
        "ego_vx": float(obs[0]),
        "ego_vy": float(obs[1]),
        "ego_ax": float(obs[3]),
        "ego_ay": float(obs[4]),
        "road_y_max_abs": float(np.max(np.abs(obs[SELECTED_CHANNELS["road_y"]]))),
        "obs_rel_vy_max_abs": float(np.max(np.abs(obs[SELECTED_CHANNELS["obs_rel_vy"]]))),
    }


def rollout(mode: str, seed: int, *, max_steps: int = 36) -> list[dict[str, Any]]:
    config = env_config(mode)
    env = AutoDriftEnv(config)
    rows: list[dict[str, Any]] = []
    try:
        obs, info = env.reset(seed=seed)
        rows.append(frame_row(mode, seed, 0, obs, info, False, False))
        terminated = truncated = False
        for step in range(1, max_steps + 1):
            obs, _reward, terminated, truncated, info = env.step(scripted_action())
            rows.append(frame_row(mode, seed, step, obs, info, terminated, truncated))
            if terminated or truncated:
                break
    finally:
        env.close()
    return rows


def replay_signature(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "step",
        "obs_shape",
        "speed",
        "road_lookahead_distance_max",
        "road_lookahead_time_s",
        "obstacle_label",
        "obstacle_predicted_lateral_offset_at_arrival",
        "terminated",
        "truncated",
        "termination_reason",
        "ego_vx",
        "ego_vy",
        "ego_ax",
        "ego_ay",
        "road_y_max_abs",
        "obs_rel_vy_max_abs",
    ]
    return [{key: row[key] for key in keys} for row in rows]


def deterministic_equal(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    if len(left) != len(right):
        return False
    for lhs, rhs in zip(replay_signature(left), replay_signature(right), strict=True):
        for key, value in lhs.items():
            other = rhs[key]
            if isinstance(value, float):
                if abs(value - float(other)) > 1e-7:
                    return False
            elif value != other:
                return False
    return True


def max_abs(rows: list[dict[str, Any]], mode: str, column: str) -> float:
    values = [abs(float(row[column])) for row in rows if row["mode"] == mode]
    return max(values) if values else 0.0


def channel_readouts(rows: list[dict[str, Any]], mode: str) -> dict[str, float]:
    return {
        "ego_vx_max_abs": max_abs(rows, mode, "ego_vx"),
        "ego_vy_max_abs": max_abs(rows, mode, "ego_vy"),
        "ego_ax_max_abs": max_abs(rows, mode, "ego_ax"),
        "ego_ay_max_abs": max_abs(rows, mode, "ego_ay"),
        "road_y_max_abs": max_abs(rows, mode, "road_y_max_abs"),
        "obs_rel_vy_max_abs": max_abs(rows, mode, "obs_rel_vy_max_abs"),
    }


def summarize(rows: list[dict[str, Any]], replay_seeds: list[int]) -> dict[str, Any]:
    modes = sorted({str(row["mode"]) for row in rows})
    readouts_by_mode = {mode: channel_readouts(rows, mode) for mode in modes}
    scaled_modes = [mode for mode in modes if mode.startswith("scaled_")]
    legacy_modes = [mode for mode in modes if mode.startswith("legacy_")]
    scaled_values = [
        value
        for mode in scaled_modes
        for key, value in readouts_by_mode[mode].items()
        if key in {
            "ego_vx_max_abs",
            "ego_vy_max_abs",
            "ego_ax_max_abs",
            "ego_ay_max_abs",
            "road_y_max_abs",
            "obs_rel_vy_max_abs",
        }
    ]
    legacy_values = [
        readouts_by_mode[mode]["ego_vx_max_abs"]
        for mode in legacy_modes
    ]
    scaled_preview_times = [
        float(row["road_lookahead_time_s"])
        for row in rows
        if str(row["mode"]).startswith("scaled_")
    ]
    legacy_preview_times = [
        float(row["road_lookahead_time_s"])
        for row in rows
        if row["mode"] == "legacy_fixed_preview"
    ]
    high_speed_rows = [row for row in rows if float(row["speed_ref"]) >= 35.9]
    crosser_rows = [row for row in rows if row["mode"] == "scaled_high_speed_crosser"]
    label_rows_ok = [
        row for row in crosser_rows
        if row["obstacle_label"] in {"aeb_feasible", "aes_feasible", "drift_required", "unavoidable"}
        and np.isfinite(float(row["obstacle_predicted_lateral_offset_at_arrival"]))
        and abs(float(row["obstacle_lateral_velocity"])) > 0.0
        and float(row["speed_ref"]) >= 35.9
    ]

    replay_failures = []
    for seed in replay_seeds:
        left = rollout("scaled_high_speed_crosser", seed)
        right = rollout("scaled_high_speed_crosser", seed)
        if not deterministic_equal(left, right):
            replay_failures.append(seed)

    readouts = {
        "modes": modes,
        "episodes": len({(row["mode"], row["seed"]) for row in rows}),
        "frames": len(rows),
        "channel_readouts_by_mode": readouts_by_mode,
        "obs72_shape_pass": all(int(row["obs_shape"]) == 72 for row in rows),
        "high_speed_reached_pass": len(high_speed_rows) == len(rows) and len(rows) > 0,
        "legacy_saturation_exposed_pass": max(legacy_values, default=0.0) >= 1.2,
        "scaled_normalization_pass": max(scaled_values, default=0.0) <= 1.0,
        "scaled_selected_channel_max_abs": max(scaled_values, default=0.0),
        "fixed_preview_short_exposed_pass": bool(legacy_preview_times) and min(legacy_preview_times) <= 1.12,
        "legacy_preview_time_min_s": min(legacy_preview_times) if legacy_preview_times else 0.0,
        "speed_aware_preview_pass": bool(scaled_preview_times) and min(scaled_preview_times) >= 2.45,
        "scaled_preview_time_min_s": min(scaled_preview_times) if scaled_preview_times else 0.0,
        "high_speed_label_pass": len(label_rows_ok) == len(crosser_rows) and len(crosser_rows) > 0,
        "high_speed_label_rows": len(label_rows_ok),
        "high_speed_crosser_rows": len(crosser_rows),
        "deterministic_replay_pass": len(replay_failures) == 0,
        "deterministic_replay_failures": replay_failures,
    }
    readouts["all_pass"] = all(
        bool(readouts[key])
        for key in (
            "obs72_shape_pass",
            "high_speed_reached_pass",
            "legacy_saturation_exposed_pass",
            "scaled_normalization_pass",
            "fixed_preview_short_exposed_pass",
            "speed_aware_preview_pass",
            "high_speed_label_pass",
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
    modes = ["legacy_fixed_preview", "scaled_high_speed", "scaled_high_speed_crosser"]

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

    result = {
        "protocol": "high_speed_domain_normalization_preview_smoke",
        "quick": bool(args.quick),
        "roadmap_unit": "B2 >20 m/s speed domain",
        "preregistration": str(PREREG.relative_to(REPO)),
        "seed_base": SEED_BASE,
        "seed_count": seed_count,
        "replay_seeds": replay_seeds,
        "high_speed_profile": {
            "speed_mps": 36.0,
            "track_radius_m": 250.0,
            "max_speed_limit_mps": 45.0,
            "observation_scale": {
                "ego_vx": HIGH_SPEED_SCALE.ego_vx,
                "ego_vy": HIGH_SPEED_SCALE.ego_vy,
                "ego_ax": HIGH_SPEED_SCALE.ego_ax,
                "ego_ay": HIGH_SPEED_SCALE.ego_ay,
                "road_y": HIGH_SPEED_SCALE.road_y,
                "obstacle_rel_vy": HIGH_SPEED_SCALE.obstacle_rel_vy,
                "road_lookahead_time_s": HIGH_SPEED_SCALE.road_lookahead_time_s,
                "road_lookahead_max_distance": HIGH_SPEED_SCALE.road_lookahead_max_distance,
            },
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
