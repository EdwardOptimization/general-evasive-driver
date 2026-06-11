"""B4 minute-scale drive-structure env-contract smoke.

This script verifies that a single AutoDrift episode can carry a warmup-gate
familiarization phase into a later emergency-obstacle phase, record a raw
obstacle pass without finish_on_pass truncation, and continue to max_steps.

It uses a scripted survival controller only to keep the infrastructure smoke
alive. It is not a driver-performance arm.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import write_json
from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig, WarmupGateConfig
from autodrift.policies import split_drive_brake_action


PREREG_PATH = Path("experiments/feasibility_audit/minute_scale_drive_structure_prereg.json")
QUICK_OUTPUT = Path("experiments/feasibility_audit/minute_scale_drive_structure_smoke_quick.json")
FULL_OUTPUT = Path("experiments/feasibility_audit/minute_scale_drive_structure_smoke.json")
QUICK_RUN_DIR = Path("runs/feasibility_audit/minute_scale_drive_structure_smoke_quick")
FULL_RUN_DIR = Path("runs/feasibility_audit/minute_scale_drive_structure_smoke")
QUICK_SEEDS = (20260940, 20260941)
FULL_SEEDS = (20260940, 20260941, 20260942, 20260943)
REPLAY_SEEDS = (20260940, 20260941)
DT = 0.02
QUICK_MAX_STEPS = 1200
FULL_MAX_STEPS = 3000


@dataclass(frozen=True)
class EpisodeSummary:
    seed: int
    frames: int
    final_step: int
    terminated: bool
    truncated: bool
    termination_reason: str
    completion_reason: str
    obs72_shape_pass: bool
    finite_obs_pass: bool
    first_active_kind: str
    warmup_first_step: int | None
    warmup_pass_step: int | None
    warmup_inactive_step: int | None
    emergency_first_step: int | None
    raw_pass_step: int | None
    obstacle_completed_any: bool
    collision_any: bool
    max_abs_lateral_error: float
    min_speed: float
    max_speed: float

    @property
    def post_pass_steps(self) -> int:
        if self.raw_pass_step is None:
            return 0
        return max(0, self.final_step - int(self.raw_pass_step))


def build_config(max_steps: int) -> DriftEnvConfig:
    return DriftEnvConfig(
        max_steps=max_steps,
        track_kind="circle",
        track_radius=1_000_000.0,
        track_width=200.0,
        friction_limited_speed=False,
        speed_range=(6.0, 6.0),
        max_speed_limit=20.0,
        obstacle=ObstacleTaskConfig(
            enabled=True,
            distance_range=(120.0, 120.0),
            half_width_range=(0.5, 0.5),
            lateral_offset_range=(40.0, 40.0),
            finish_on_pass=False,
            perception_reveal_step=250,
            perception_reveal_distance=150.0,
            pass_reward=0.0,
        ),
        warmup_gate=WarmupGateConfig(
            enabled=True,
            distance_range=(24.0, 24.0),
            lateral_offset_range=(25.0, 25.0),
            half_width_range=(0.5, 0.5),
            reveal_step=0,
            max_active_steps=260,
            finish_pass_distance=2.0,
        ),
    )


def scripted_survival_action(info: dict[str, Any]) -> np.ndarray:
    speed = float(info["speed"])
    speed_ref = float(info["speed_ref"])
    drive_brake = float(np.clip(0.30 * (speed_ref - speed) / max(speed_ref, 1.0) + 0.02, -0.2, 0.2))
    return split_drive_brake_action(0.0, drive_brake)


def _row(seed: int, obs: np.ndarray, info: dict[str, Any], *, phase: str) -> dict[str, Any]:
    return {
        "seed": seed,
        "phase": phase,
        "step": int(info["step"]),
        "obs_shape": int(obs.shape[0]),
        "obs_finite": bool(np.all(np.isfinite(obs))),
        "active_obstacle_kind": str(info["active_obstacle_kind"]),
        "warmup_gate_active": bool(info["warmup_gate_active"]),
        "warmup_gate_visible": bool(info["warmup_gate_visible"]),
        "warmup_gate_passed": bool(info["warmup_gate_passed"]),
        "warmup_gate_distance": float(info["warmup_gate_distance"]),
        "obstacle_perception_visible": bool(info["obstacle_perception_visible"]),
        "obstacle_passed_raw": bool(info["obstacle_passed_raw"]),
        "obstacle_completed": bool(info["obstacle_completed"]),
        "collision": bool(info["collision"]),
        "termination_reason": str(info["termination_reason"]),
        "completion_reason": str(info["completion_reason"]),
        "speed": float(info["speed"]),
        "lateral_error": float(info["lateral_error"]),
        "heading_error": float(info["heading_error"]),
        "obstacle_distance": float(info["obstacle_distance"]),
        "active_obstacle_body_x": float(info["active_obstacle_body_x"]),
        "active_obstacle_body_y": float(info["active_obstacle_body_y"]),
    }


def rollout(seed: int, *, max_steps: int) -> tuple[EpisodeSummary, list[dict[str, Any]]]:
    env = AutoDriftEnv(build_config(max_steps))
    obs, info = env.reset(seed=seed)
    rows: list[dict[str, Any]] = [_row(seed, obs, info, phase="reset")]
    first_active_kind = str(info["active_obstacle_kind"])
    warmup_first_step = int(info["step"]) if info["active_obstacle_kind"] == "warmup_gate" else None
    warmup_pass_step = int(info["step"]) if info["warmup_gate_passed"] else None
    warmup_inactive_step = None if info["warmup_gate_active"] else int(info["step"])
    emergency_first_step = int(info["step"]) if info["active_obstacle_kind"] == "emergency_obstacle" else None
    raw_pass_step = int(info["step"]) if info["obstacle_passed_raw"] else None
    obstacle_completed_any = bool(info["obstacle_completed"])
    collision_any = bool(info["collision"])
    obs72_shape_pass = obs.shape == (72,)
    finite_obs_pass = bool(np.all(np.isfinite(obs)))
    max_abs_lateral_error = abs(float(info["lateral_error"]))
    min_speed = float(info["speed"])
    max_speed = float(info["speed"])
    terminated = False
    truncated = False

    for _ in range(max_steps):
        action = scripted_survival_action(info)
        obs, _, terminated, truncated, info = env.step(action)
        rows.append(_row(seed, obs, info, phase="step"))
        obs72_shape_pass = obs72_shape_pass and obs.shape == (72,)
        finite_obs_pass = finite_obs_pass and bool(np.all(np.isfinite(obs)))
        max_abs_lateral_error = max(max_abs_lateral_error, abs(float(info["lateral_error"])))
        min_speed = min(min_speed, float(info["speed"]))
        max_speed = max(max_speed, float(info["speed"]))
        if info["active_obstacle_kind"] == "warmup_gate" and warmup_first_step is None:
            warmup_first_step = int(info["step"])
        if info["warmup_gate_passed"] and warmup_pass_step is None:
            warmup_pass_step = int(info["step"])
        if not info["warmup_gate_active"] and warmup_inactive_step is None:
            warmup_inactive_step = int(info["step"])
        if info["active_obstacle_kind"] == "emergency_obstacle" and emergency_first_step is None:
            emergency_first_step = int(info["step"])
        if info["obstacle_passed_raw"] and raw_pass_step is None:
            raw_pass_step = int(info["step"])
        obstacle_completed_any = obstacle_completed_any or bool(info["obstacle_completed"])
        collision_any = collision_any or bool(info["collision"])
        if terminated or truncated:
            break

    summary = EpisodeSummary(
        seed=seed,
        frames=len(rows),
        final_step=int(info["step"]),
        terminated=bool(terminated),
        truncated=bool(truncated),
        termination_reason=str(info["termination_reason"]),
        completion_reason=str(info["completion_reason"]),
        obs72_shape_pass=obs72_shape_pass,
        finite_obs_pass=finite_obs_pass,
        first_active_kind=first_active_kind,
        warmup_first_step=warmup_first_step,
        warmup_pass_step=warmup_pass_step,
        warmup_inactive_step=warmup_inactive_step,
        emergency_first_step=emergency_first_step,
        raw_pass_step=raw_pass_step,
        obstacle_completed_any=obstacle_completed_any,
        collision_any=collision_any,
        max_abs_lateral_error=float(max_abs_lateral_error),
        min_speed=float(min_speed),
        max_speed=float(max_speed),
    )
    return summary, rows


def episode_signature(rows: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    def stable_float(value: Any) -> float | str:
        numeric = float(value)
        if not np.isfinite(numeric):
            return "nan"
        return round(numeric, 9)

    return tuple(
        (
            int(row["step"]),
            str(row["active_obstacle_kind"]),
            bool(row["warmup_gate_active"]),
            bool(row["warmup_gate_passed"]),
            bool(row["obstacle_passed_raw"]),
            bool(row["obstacle_completed"]),
            bool(row["collision"]),
            str(row["termination_reason"]),
            str(row["completion_reason"]),
            stable_float(row["speed"]),
            stable_float(row["lateral_error"]),
            stable_float(row["active_obstacle_body_x"]),
            stable_float(row["active_obstacle_body_y"]),
        )
        for row in rows
    )


def deterministic_replay_failures(seeds: tuple[int, ...], *, max_steps: int) -> list[int]:
    failures: list[int] = []
    for seed in seeds:
        _, left_rows = rollout(seed, max_steps=max_steps)
        _, right_rows = rollout(seed, max_steps=max_steps)
        if episode_signature(left_rows) != episode_signature(right_rows):
            failures.append(seed)
    return failures


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize_episode(summary: EpisodeSummary, *, max_steps: int) -> dict[str, Any]:
    return {
        "seed": summary.seed,
        "frames": summary.frames,
        "final_step": summary.final_step,
        "terminated": summary.terminated,
        "truncated": summary.truncated,
        "termination_reason": summary.termination_reason,
        "completion_reason": summary.completion_reason,
        "obs72_shape_pass": summary.obs72_shape_pass,
        "finite_obs_pass": summary.finite_obs_pass,
        "first_active_kind": summary.first_active_kind,
        "warmup_first_step": summary.warmup_first_step,
        "warmup_pass_step": summary.warmup_pass_step,
        "warmup_inactive_step": summary.warmup_inactive_step,
        "emergency_first_step": summary.emergency_first_step,
        "raw_pass_step": summary.raw_pass_step,
        "post_pass_steps": summary.post_pass_steps,
        "obstacle_completed_any": summary.obstacle_completed_any,
        "collision_any": summary.collision_any,
        "max_abs_lateral_error": summary.max_abs_lateral_error,
        "min_speed": summary.min_speed,
        "max_speed": summary.max_speed,
        "max_steps_reached_pass": (
            summary.final_step == max_steps
            and summary.truncated
            and not summary.terminated
            and summary.completion_reason == "max_steps"
            and summary.termination_reason == ""
        ),
        "warmup_sequence_pass": (
            summary.first_active_kind == "warmup_gate"
            and summary.warmup_first_step is not None
            and summary.warmup_pass_step is not None
            and summary.warmup_inactive_step is not None
            and summary.warmup_inactive_step <= summary.emergency_first_step
            if summary.emergency_first_step is not None
            else False
        ),
        "emergency_sequence_pass": (
            summary.emergency_first_step is not None
            and summary.warmup_inactive_step is not None
            and summary.emergency_first_step >= summary.warmup_inactive_step
        ),
        "raw_pass_continuation_pass": (
            summary.raw_pass_step is not None
            and not summary.obstacle_completed_any
            and summary.post_pass_steps >= 200
        ),
    }


def run(*, quick: bool) -> dict[str, Any]:
    max_steps = QUICK_MAX_STEPS if quick else FULL_MAX_STEPS
    seeds = QUICK_SEEDS if quick else FULL_SEEDS
    run_dir = QUICK_RUN_DIR if quick else FULL_RUN_DIR
    output = QUICK_OUTPUT if quick else FULL_OUTPUT
    all_rows: list[dict[str, Any]] = []
    episode_summaries: list[EpisodeSummary] = []
    for seed in seeds:
        summary, rows = rollout(seed, max_steps=max_steps)
        episode_summaries.append(summary)
        all_rows.extend(rows)
    rows_path = run_dir / "frame_rows.csv"
    write_rows(rows_path, all_rows)
    replay_failures = deterministic_replay_failures(REPLAY_SEEDS, max_steps=max_steps)
    episode_readouts = [summarize_episode(summary, max_steps=max_steps) for summary in episode_summaries]
    readouts = {
        "all_pass": False,
        "episodes": len(episode_summaries),
        "frames": len(all_rows),
        "duration_s": max_steps * DT,
        "obs72_shape_pass": all(row["obs72_shape_pass"] for row in episode_readouts),
        "finite_obs_pass": all(row["finite_obs_pass"] for row in episode_readouts),
        "max_steps_reached_pass": all(row["max_steps_reached_pass"] for row in episode_readouts),
        "warmup_sequence_pass": all(row["warmup_sequence_pass"] for row in episode_readouts),
        "emergency_sequence_pass": all(row["emergency_sequence_pass"] for row in episode_readouts),
        "raw_pass_continuation_pass": all(row["raw_pass_continuation_pass"] for row in episode_readouts),
        "deterministic_replay_pass": len(replay_failures) == 0,
        "deterministic_replay_failures": replay_failures,
        "min_raw_pass_step": min(row["raw_pass_step"] for row in episode_readouts if row["raw_pass_step"] is not None),
        "min_post_pass_steps": min(row["post_pass_steps"] for row in episode_readouts),
        "max_abs_lateral_error": max(row["max_abs_lateral_error"] for row in episode_readouts),
        "min_speed": min(row["min_speed"] for row in episode_readouts),
        "max_speed": max(row["max_speed"] for row in episode_readouts),
    }
    readouts["all_pass"] = all(
        bool(readouts[key])
        for key in (
            "obs72_shape_pass",
            "finite_obs_pass",
            "max_steps_reached_pass",
            "warmup_sequence_pass",
            "emergency_sequence_pass",
            "raw_pass_continuation_pass",
            "deterministic_replay_pass",
        )
    )
    result = {
        "protocol": "minute_scale_drive_structure_smoke",
        "roadmap_unit": "B4 minute-scale drive structure",
        "quick": quick,
        "preregistration": str(PREREG_PATH),
        "rows_csv": str(rows_path),
        "seed_count": len(seeds),
        "seeds": list(seeds),
        "replay_seeds": list(REPLAY_SEEDS),
        "profile": {
            "dt": DT,
            "max_steps": max_steps,
            "duration_s": max_steps * DT,
            "track_radius": 1_000_000.0,
            "track_width": 200.0,
            "speed_mps": 6.0,
            "obstacle_finish_on_pass": False,
            "obstacle_reveal_step": 250,
            "warmup_gate_max_active_steps": 260,
        },
        "scripted_controller": "zero-steer speed hold survival controller; not a driver-performance arm",
        "readouts": readouts,
        "episodes": episode_readouts,
        "claim_boundary": (
            "B4 minute-scale env-contract smoke only; no training, no driver mutation, "
            "no validation ranking, no promotion, no driver-performance, no current-sim "
            "robustness-result, no high-fidelity sufficiency, no paper, no repair-success, "
            "no feasibility-proof, and no self-ID claim."
        ),
    }
    write_json(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    result = run(quick=bool(args.quick))
    print({"all_pass": result["readouts"]["all_pass"], "output": QUICK_OUTPUT.as_posix() if args.quick else FULL_OUTPUT.as_posix()})


if __name__ == "__main__":
    main()
