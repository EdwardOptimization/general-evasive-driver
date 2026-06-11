"""Measurement C: quantifying the "muscle-memory save" -- reflex-layer recovery
from graded limit-ramp overshoot.

New-paradigm self-ID frame (threshold-braking / incremental limit seeking): the
identification act is embedded in the useful action itself. A threshold-seeker
ramps brake/steer toward an estimated limit; if the ramp overshoots, the only
thing standing between the overshoot and a crash is the reflex layer ("muscle
memory"). This script measures, on the B2K2_final environment family
(continuous-mu, r=900 m circle, reveal-9.5 obstacle, WITH dynamics
randomization re-enabled), how deep an overshoot the deployed reflex layers can
still recover, and what the recovery costs (time, longitudinal distance, speed).

Scenario construction (state injection, physics-graded):
  After a normal env.reset(seed) (which samples vehicle params with mu pinned
  per cell and the spec's mu->d jittered obstacle), the ego state is overwritten
  with a "ramp overshot the limit" state at overshoot level o in
  {1.05, 1.15, 1.30, 1.50} x the friction limit of the SAMPLED vehicle:
    - rear sideslip:  beta = -o * alpha_sat_r, alpha_sat_r = artanh(0.95)*mu*Fzr/cr
                      (rear slip angle at 95 % force saturation; o=1.0 means the
                      rear tire is exactly at its saturation knee)
    - yaw overshoot:  yaw_rate = kappa*v + o * mu*g/v  (o x the maximum
                      sustainable steady-state yaw rate, surplus into the turn)
    - steer overshoot: front slip forced to o x its saturation angle (steering
                      ramped past front grip), within the actuator limit
    - brake overshoot: drive_force = -min(o * mu*Fzr, max_brake) (brake ramp
                      past the rear friction circle; the tire clamp makes
                      |ax| < F_cmd/m -- the slip signal of measurement A)
    - geometry:       lateral offset {0.5, 1.5, 3.0} m toward the OUTSIDE
                      boundary, course drifting outward; speeds {8, 12, 16} m/s.
  The very next observation is handed to the driver under test: the reflex
  layer takes over exactly at the moment the threshold-seeker lost the car.

Drivers compared on identical (cell, seed) pairs:
  - baseline_coast : steer->0, no throttle, no brake (no muscle memory; the
                     "startled novice lets go" control)
  - v4_incumbent   : ActiveSafetyReflexDriver (M3105 deployable incumbent)
  - v5_candidate   : ActiveSafetyDriverV5Candidate (curvature governor + ESC)

Recovery definition ("back in the controllable corridor"): >= 10 consecutive
steps with |beta| <= 0.08 rad, |yaw_rate - kappa*vx| <= 0.20 rad/s,
|lateral_error| <= 2.5 m (the marked corridor half-width) and speed >= 1.5 m/s,
before any hard termination (off_track at |lat| > 5 m, collision, yaw-rate
limit) within a 250-step (5 s) horizon. "speed_too_low" terminations are
counted separately as "stalled" (stopped, not crashed, but not recovered).

Outputs:
  experiments/feasibility_audit/reflex_overshoot_recovery.json   (aggregates)
  runs/feasibility_audit/reflex_overshoot_recovery/episodes.csv  (raw rows)

Claim boundary: feasibility-audit recovery-envelope measurement of two existing
scripted reflex stacks on synthetic injected overshoot states. No promotion,
ranking-for-deployment, training, gate-validity or self-ID capability claim.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/reflex_overshoot_recovery.py [--quick]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RESULTS_JSON = REPO / "experiments/feasibility_audit/reflex_overshoot_recovery.json"
RUN_DIR = REPO / "runs/feasibility_audit/reflex_overshoot_recovery"
EPISODES_CSV = RUN_DIR / "episodes.csv"

SEED_BASE = 20260617  # fresh stream (final-spec=20260615, B=20260612, C=20260613)

# --- B2K2_final family knobs (experiments/feasibility_audit/selfid_task_final_spec.json) ---
TRACK_RADIUS = 900.0
TRACK_WIDTH = 5.0  # hard off-track at |lateral_error| > 5.0; marked corridor half-width = 2.5
DT = 0.02
MAX_STEPS = 285
REVEAL_DISTANCE = 9.5
OBSTACLE_HALF_WIDTH = 1.25
PASS_REWARD = 40.0
COLLISION_PENALTY = 60.0
MU_KNOTS = (0.30, 0.55, 0.85, 1.15)
D_KNOTS = (24.0, 38.0, 47.0, 52.0)
JITTER_D_M = 0.75
D_FLOOR_M = 14.5

# --- measurement grid ---
MU_LEVELS = (0.30, 0.45, 0.60, 0.85)
OVERSHOOTS = (1.05, 1.15, 1.30, 1.50)
SPEEDS_MPS = (8.0, 12.0, 16.0)
LATERAL_OFFSETS_M = (0.5, 1.5, 3.0)  # toward the outside boundary
N_SEEDS = 8

# --- recovery / stability definition ---
HORIZON_STEPS = 250  # 5.0 s
SUSTAIN_STEPS = 10  # 0.2 s of continuous stability required
STABLE_BETA_RAD = 0.08
STABLE_YAW_SURPLUS_RADPS = 0.20
STABLE_LAT_M = 2.5  # back inside the marked corridor
STABLE_MIN_SPEED_MPS = 1.5
CONTAINED_BETA_RAD = 0.25  # bounded persistent drift still counts as "contained"
BOUNDARY_RATE_BAR = 0.75  # "recoverable" bar for the instability-boundary surface

ATANH_095 = math.atanh(0.95)  # 1.8318: slip-angle multiple at 95 % tanh saturation
HEADING_ERR_FRACTION = 0.4  # nose rotated into the turn by 0.4 x the slip depth
MAX_INJECTED_BETA_RAD = 0.50
MAX_INJECTED_YAW_RADPS = 3.0

CLAIM_BOUNDARY = (
    "Feasibility-audit reflex-recovery-envelope measurement only: graded synthetic overshoot "
    "states are injected into the B2K2_final continuous-mu family (with dynamics randomization "
    "re-enabled) and two existing scripted reflex stacks (M3105 v4 incumbent, v5 candidate) plus "
    "a coast baseline are measured for recovery rate, recovery time and longitudinal cost. No "
    "driver promotion, deployment ranking, training, repair-success, gate-validity, paper, or "
    "self-ID capability claim is made."
)


def d_of_mu(mu: float) -> float:
    return float(np.interp(mu, MU_KNOTS, D_KNOTS))


def jittered_distance(mu: float, rollout_seed: int) -> float:
    # same jitter law as the final spec (seed stream namespaced by our SEED_BASE)
    eps = float(
        np.random.default_rng([SEED_BASE, 777, int(rollout_seed)]).uniform(-JITTER_D_M, JITTER_D_M)
    )
    return max(d_of_mu(mu) + eps, D_FLOOR_M)


def centerline_compensation(d: float) -> float:
    return float(TRACK_RADIUS - math.sqrt(max(TRACK_RADIUS**2 - d**2, 1.0)))


def env_config_dict(mu: float, d: float, obstacle_enabled: bool = True) -> dict[str, Any]:
    """B2K2_final level config (mirrors voi_commitment_task_design.level_env_config)
    with deliberate harness deltas, all documented in the JSON:
      1. dynamics randomization RE-ENABLED at the library defaults (mu stays pinned)
      2. finish_on_pass=False so an episode cannot truncate mid-slide just because
         the obstacle was passed; collision detection is unchanged.
      3. every cell is also run with obstacle_enabled=False (twin episode, identical
         ego/params/injection) to separate pure slide-recovery capability from the
         in-family reveal-9.5 obstacle interaction."""
    return {
        "dt": DT,
        "max_steps": MAX_STEPS,
        "track_kind": "circle",
        "track_radius": TRACK_RADIUS,
        "track_width": TRACK_WIDTH,
        "speed_range": [8.0, 8.0],
        "beta_target_range": [0.40, 0.40],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "wheel_observation_mode": "none",
        "include_privileged_params": False,
        "randomization": {
            "mu_range": [mu, mu],
            "mass_scale_range": [0.85, 1.20],
            "cg_shift_range": [-0.12, 0.12],
            "inertia_scale_range": [0.85, 1.25],
            "tire_stiffness_scale_range": [0.65, 1.35],
            "drive_scale_range": [0.80, 1.15],
            "brake_scale_range": [0.80, 1.15],
            "actuator_tau_scale_range": [0.75, 1.75],
        },
        "obstacle": {
            "enabled": bool(obstacle_enabled),
            "distance_range": [d, d],
            "half_width_range": [OBSTACLE_HALF_WIDTH, OBSTACLE_HALF_WIDTH],
            "lateral_offset_range": [centerline_compensation(d), centerline_compensation(d)],
            "finish_on_pass": False,
            "finish_pass_distance": 2.0,
            "pass_reward": PASS_REWARD,
            "collision_penalty": COLLISION_PENALTY,
            "perception_reveal_step": 0,
            "perception_reveal_distance": REVEAL_DISTANCE,
            "require_aeb_infeasible": False,
        },
    }


def inject_overshoot(env, speed: float, offset_m: float, overshoot: float) -> dict[str, float]:
    """Overwrite the freshly-reset env state with a graded limit-ramp-overshoot
    slide and rebuild the observation history. Deterministic given the reset.

    Returns injection diagnostics. Uses the SAMPLED params (env.params) so the
    overshoot is graded against the realized vehicle, never the nominal one.
    """
    from autodrift.dynamics import VehicleState

    p = env.params
    state = env.state
    # keep the reset track angle so the obstacle stays at its spec'd distance ahead
    angle = math.atan2(state.y, state.x)
    radius_pos = TRACK_RADIUS + offset_m  # outward = +lateral_error (CCW circle)
    x = radius_pos * math.cos(angle)
    y = radius_pos * math.sin(angle)
    tangent_heading = angle + math.pi / 2.0  # CCW
    kappa = 1.0 / TRACK_RADIUS

    fzr = p.static_fzr
    fzf = p.static_fzf
    alpha_sat_r = ATANH_095 * p.mu * fzr / max(p.cr, 1e-6)
    alpha_sat_f = ATANH_095 * p.mu * fzf / max(p.cf, 1e-6)

    # rear slid out: velocity right of nose (CCW turn), depth = o x saturation slip
    beta = -min(overshoot * alpha_sat_r, MAX_INJECTED_BETA_RAD)
    heading_err = min(HEADING_ERR_FRACTION * overshoot * alpha_sat_r, 0.35)  # nose into turn
    psi = tangent_heading + heading_err
    vx = speed * math.cos(beta)
    vy = speed * math.sin(beta)
    # yaw overshoot: o x the maximum sustainable yaw rate, surplus into the turn
    yaw_rate = min(kappa * speed + overshoot * p.mu * p.gravity / max(speed, 1.0), MAX_INJECTED_YAW_RADPS)
    # steering ramped past front grip: front slip at -o x saturation (pulling into turn)
    steer = float(
        np.clip(
            math.atan2(vy + p.lf * yaw_rate, abs(vx)) + overshoot * alpha_sat_f,
            -p.max_steer,
            p.max_steer,
        )
    )
    # brake ramped past the rear friction circle
    brake_force = min(overshoot * p.mu * fzr, p.max_brake_force)
    drive_force = -brake_force

    env.state = VehicleState(
        x=x, y=y, psi=psi, vx=vx, vy=vy, yaw_rate=yaw_rate, steer=steer, drive_force=drive_force
    )
    # consistent "last command" = the overshooting ramp command itself
    steer_norm = float(np.clip(steer / max(p.max_steer, 1e-6), -1.0, 1.0))
    brake_norm = float(np.clip(brake_force / max(p.max_brake_force, 1e-6), 0.0, 1.0))
    env.last_action = np.array([steer_norm, -1.0, 2.0 * brake_norm - 1.0], dtype=np.float64)
    env.last_control = env._control_from_action(env.last_action)
    env.last_steer_rate = 0.0
    env.last_forces = env.model.tire_forces(vx, vy, yaw_rate, steer, drive_force)
    env._reset_raw_wheel_state()
    env.max_off_track_overshoot = 0.0
    base_observation = env._base_observation()
    env.obs_history = [base_observation.copy() for _ in range(env.config.history_length)]

    # commanded long. decel vs friction-limited decel: the measurement-A slip signal
    ax_cmd = brake_force / p.mass
    ax_limit = p.mu * p.gravity
    return {
        "beta_inj_rad": beta,
        "yaw_rate_inj_radps": yaw_rate,
        "steer_inj_rad": steer,
        "brake_force_inj_n": brake_force,
        "alpha_sat_r_rad": alpha_sat_r,
        "alpha_sat_f_rad": alpha_sat_f,
        "ax_cmd_mps2": ax_cmd,
        "ax_shortfall_cmd_minus_limit_mps2": max(ax_cmd - ax_limit, 0.0),
        "heading_err_inj_rad": heading_err,
    }


def run_recovery(env, act_fn: Callable[[np.ndarray], np.ndarray], v0: float) -> dict[str, Any]:
    """Step the env under act_fn until recovery is confirmed, a terminal fires,
    or the horizon ends. Returns the per-episode outcome row fragment."""
    arc = 2.0 * math.pi * TRACK_RADIUS
    frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    prev_progress = frame.progress
    progress_made = 0.0
    speeds: list[float] = []
    progress_hist: list[float] = []
    stable_flags: list[bool] = []
    max_abs_beta = 0.0
    max_abs_lat = abs(frame.lateral_error)
    obs = env._observation()

    termination = ""
    recovered_at: int | None = None
    first_stable_step: int | None = None
    steps_run = 0
    for t in range(1, HORIZON_STEPS + 1):
        action = np.asarray(act_fn(np.asarray(obs, dtype=np.float32)), dtype=np.float64)
        obs, _reward, terminated, truncated, info = env.step(action)
        steps_run = t
        frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
        dp = (frame.progress - prev_progress) % arc
        if dp > arc / 2.0:
            dp -= arc
        prev_progress = frame.progress
        progress_made += dp
        speed = math.hypot(env.state.vx, env.state.vy)
        beta = math.atan2(env.state.vy, max(env.state.vx, 1e-6))
        yaw_surplus = abs(env.state.yaw_rate - frame.curvature * env.state.vx)
        max_abs_beta = max(max_abs_beta, abs(beta))
        max_abs_lat = max(max_abs_lat, abs(frame.lateral_error))
        speeds.append(speed)
        progress_hist.append(progress_made)
        stable = (
            abs(beta) <= STABLE_BETA_RAD
            and yaw_surplus <= STABLE_YAW_SURPLUS_RADPS
            and abs(frame.lateral_error) <= STABLE_LAT_M
            and speed >= STABLE_MIN_SPEED_MPS
        )
        stable_flags.append(stable)
        if stable and first_stable_step is None:
            first_stable_step = t
        if terminated:
            termination = str(env.termination_reason)
            break
        if len(stable_flags) >= SUSTAIN_STEPS and all(stable_flags[-SUSTAIN_STEPS:]):
            recovered_at = t - SUSTAIN_STEPS + 1  # first step of the sustained window
            break
        if truncated:
            termination = "max_steps"
            break

    recovered = recovered_at is not None
    final_frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
    final_speed = math.hypot(env.state.vx, env.state.vy)
    final_beta = math.atan2(env.state.vy, max(env.state.vx, 1e-6))
    if recovered:
        idx = recovered_at - 1
        speed_at = speeds[idx]
        prog_at = progress_hist[idx]
        recovery_steps = recovered_at
        distance_lost = v0 * recovery_steps * DT - prog_at
        speed_loss = v0 - speed_at
        outcome = "recovered"
    else:
        recovery_steps = -1
        distance_lost = v0 * steps_run * DT - (progress_hist[-1] if progress_hist else 0.0)
        speed_loss = v0 - (speeds[-1] if speeds else v0)
        if termination == "speed_too_low":
            outcome = "stalled"
        elif termination in ("off_track", "obstacle_collision", "yaw_rate_limit", "speed_too_high", "non_finite_state"):
            outcome = termination
        elif abs(final_frame.lateral_error) <= STABLE_LAT_M and abs(final_beta) <= CONTAINED_BETA_RAD:
            # safe containment without clean stabilization: held inside the marked
            # corridor in a bounded persistent drift (v2 speed-floor behavior on ice)
            outcome = "contained_drift"
        else:
            outcome = "not_stabilized"
    return {
        "outcome": outcome,
        "recovered": recovered,
        "recovery_steps": recovery_steps,
        "recovery_time_s": recovery_steps * DT if recovered else float("nan"),
        "distance_lost_m": float(distance_lost),
        "speed_loss_mps": float(speed_loss),
        "steps_run": steps_run,
        "first_stable_step": -1 if first_stable_step is None else first_stable_step,
        "final_beta_rad": float(final_beta),
        "final_lateral_m": float(final_frame.lateral_error),
        "final_speed_mps": float(final_speed),
        "max_abs_beta_rad": float(max_abs_beta),
        "max_abs_lateral_m": float(max_abs_lat),
        "min_obstacle_clearance_m": float(env.min_obstacle_clearance),
        "collided": bool(env.collision),
    }


def cell_seed(mu_idx: int, o_idx: int, v_idx: int, off_idx: int, k: int) -> int:
    return SEED_BASE * 100 + mu_idx * 100000 + o_idx * 10000 + v_idx * 1000 + off_idx * 100 + k


def build_drivers() -> dict[str, Callable[[np.ndarray], np.ndarray]]:
    from autodrift.active_safety_driver_v5_curvature_speed_governor_candidate import (
        ActiveSafetyDriverV5Candidate,
    )
    from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver

    v4 = ActiveSafetyReflexDriver()
    v5 = ActiveSafetyDriverV5Candidate()
    coast = np.array([0.0, -1.0, -1.0], dtype=np.float32)
    return {
        "baseline_coast": lambda obs: coast,
        "v4_incumbent": v4.act,
        "v5_candidate": v5.act,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def filt(**kv):
        out = rows
        for key, value in kv.items():
            out = [r for r in out if r[key] == value]
        return out

    def outcome_counts_of(sub: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in sub:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
        return counts

    SAVED_OUTCOMES = {"recovered", "contained_drift", "stalled"}

    def save_rate_of(sub: list[dict[str, Any]]) -> float:
        return sum(1 for r in sub if r["outcome"] in SAVED_OUTCOMES) / max(len(sub), 1)

    drivers = sorted({r["driver"] for r in rows})
    obstacle_modes = sorted({r["obstacle_on"] for r in rows})
    cells = []
    for ob in obstacle_modes:
        for driver in drivers:
            for mu in MU_LEVELS:
                for o in OVERSHOOTS:
                    for v in SPEEDS_MPS:
                        for off in LATERAL_OFFSETS_M:
                            sub = filt(
                                driver=driver, mu=mu, overshoot=o, speed_mps=v, offset_m=off, obstacle_on=ob
                            )
                            if not sub:
                                continue
                            rec = [r for r in sub if r["recovered"]]
                            cells.append(
                                {
                                    "driver": driver,
                                    "obstacle_on": ob,
                                    "mu": mu,
                                    "overshoot": o,
                                    "speed_mps": v,
                                    "offset_m": off,
                                    "n": len(sub),
                                    "recovery_rate": len(rec) / len(sub),
                                    "save_rate": save_rate_of(sub),
                                    "mean_recovery_steps": (
                                        float(np.mean([r["recovery_steps"] for r in rec])) if rec else float("nan")
                                    ),
                                    "mean_recovery_time_s": (
                                        float(np.mean([r["recovery_time_s"] for r in rec])) if rec else float("nan")
                                    ),
                                    "mean_distance_lost_m": (
                                        float(np.mean([r["distance_lost_m"] for r in rec])) if rec else float("nan")
                                    ),
                                    "mean_speed_loss_mps": (
                                        float(np.mean([r["speed_loss_mps"] for r in rec])) if rec else float("nan")
                                    ),
                                    "outcomes": outcome_counts_of(sub),
                                }
                            )

    # instability-boundary surface: per (obstacle_on, driver, mu, v), marginal over offsets+seeds
    boundary = []
    for ob in obstacle_modes:
        for driver in drivers:
            for mu in MU_LEVELS:
                for v in SPEEDS_MPS:
                    curve = []
                    for o in OVERSHOOTS:
                        sub = filt(driver=driver, mu=mu, overshoot=o, speed_mps=v, obstacle_on=ob)
                        if not sub:
                            continue
                        rate = sum(1 for r in sub if r["recovered"]) / len(sub)
                        curve.append(
                            {
                                "overshoot": o,
                                "recovery_rate": rate,
                                "save_rate": save_rate_of(sub),
                                "n": len(sub),
                            }
                        )
                    if not curve:
                        continue
                    ok = [c["overshoot"] for c in curve if c["recovery_rate"] >= BOUNDARY_RATE_BAR]
                    saved = [c["overshoot"] for c in curve if c["save_rate"] >= BOUNDARY_RATE_BAR]
                    perfect = [c["overshoot"] for c in curve if c["recovery_rate"] >= 1.0]
                    boundary.append(
                        {
                            "driver": driver,
                            "obstacle_on": ob,
                            "mu": mu,
                            "speed_mps": v,
                            "rate_curve": curve,
                            "max_recoverable_overshoot_rate_ge_0p75": max(ok) if ok else float("nan"),
                            "max_saveable_overshoot_rate_ge_0p75": max(saved) if saved else float("nan"),
                            "max_recoverable_overshoot_rate_eq_1p0": max(perfect) if perfect else float("nan"),
                        }
                    )

    # paired v4 vs v5 on identical (cell, seed, obstacle_on)
    paired_by_mode = {}
    for ob in obstacle_modes:
        paired = {"n_pairs": 0, "both": 0, "v4_only": 0, "v5_only": 0, "neither": 0}
        deltas_steps: list[float] = []
        deltas_dist: list[float] = []
        by_key: dict[tuple, dict[str, dict[str, Any]]] = {}
        for r in rows:
            if r["obstacle_on"] != ob:
                continue
            key = (r["mu"], r["overshoot"], r["speed_mps"], r["offset_m"], r["seed"])
            by_key.setdefault(key, {})[r["driver"]] = r
        for key, dr in by_key.items():
            if "v4_incumbent" not in dr or "v5_candidate" not in dr:
                continue
            a, b = dr["v4_incumbent"], dr["v5_candidate"]
            paired["n_pairs"] += 1
            if a["recovered"] and b["recovered"]:
                paired["both"] += 1
                deltas_steps.append(b["recovery_steps"] - a["recovery_steps"])
                deltas_dist.append(b["distance_lost_m"] - a["distance_lost_m"])
            elif a["recovered"]:
                paired["v4_only"] += 1
            elif b["recovered"]:
                paired["v5_only"] += 1
            else:
                paired["neither"] += 1
        paired["mean_recovery_steps_delta_v5_minus_v4_when_both"] = (
            float(np.mean(deltas_steps)) if deltas_steps else float("nan")
        )
        paired["mean_distance_lost_delta_v5_minus_v4_when_both"] = (
            float(np.mean(deltas_dist)) if deltas_dist else float("nan")
        )
        paired_by_mode["obstacle_on" if ob else "obstacle_off"] = paired

    # driver-level rollups per obstacle mode
    overall = []
    for ob in obstacle_modes:
        for driver in drivers:
            sub = filt(driver=driver, obstacle_on=ob)
            rec = [r for r in sub if r["recovered"]]
            overall.append(
                {
                    "driver": driver,
                    "obstacle_on": ob,
                    "n": len(sub),
                    "recovery_rate": len(rec) / max(len(sub), 1),
                    "save_rate": save_rate_of(sub),
                    "mean_recovery_steps": float(np.mean([r["recovery_steps"] for r in rec])) if rec else float("nan"),
                    "mean_distance_lost_m": float(np.mean([r["distance_lost_m"] for r in rec])) if rec else float("nan"),
                    "mean_speed_loss_mps": float(np.mean([r["speed_loss_mps"] for r in rec])) if rec else float("nan"),
                    "outcomes": outcome_counts_of(sub),
                }
            )
    return {
        "overall": overall,
        "cells": cells,
        "boundary_surface": boundary,
        "paired_v4_v5": paired_by_mode,
    }


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="reduced smoke grid")
    args = parser.parse_args()

    import sys

    sys.path.insert(0, str(REPO / "src"))
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv

    mu_levels = MU_LEVELS if not args.quick else (0.30, 0.85)
    overshoots = OVERSHOOTS if not args.quick else (1.05, 1.50)
    speeds = SPEEDS_MPS if not args.quick else (8.0, 16.0)
    offsets = LATERAL_OFFSETS_M if not args.quick else (0.5, 3.0)
    n_seeds = N_SEEDS if not args.quick else 2

    drivers = build_drivers()
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    started = time.time()
    n_cells = len(mu_levels) * len(overshoots) * len(speeds) * len(offsets)
    cell_count = 0
    for mu_idx, mu in enumerate(MU_LEVELS):
        if mu not in mu_levels:
            continue
        for o_idx, o in enumerate(OVERSHOOTS):
            if o not in overshoots:
                continue
            for v_idx, v in enumerate(SPEEDS_MPS):
                if v not in speeds:
                    continue
                for off_idx, off in enumerate(LATERAL_OFFSETS_M):
                    if off not in offsets:
                        continue
                    cell_count += 1
                    for k in range(n_seeds):
                        seed = cell_seed(mu_idx, o_idx, v_idx, off_idx, k)
                        d = jittered_distance(mu, seed)
                        for obstacle_on in (True, False):
                            env = AutoDriftEnv(
                                build_env_config(env_config_dict(mu, d, obstacle_enabled=obstacle_on))
                            )
                            assert env.base_obs_dim == 72, f"obs layout changed: {env.base_obs_dim}"
                            try:
                                for driver_name, act_fn in drivers.items():
                                    env.reset(seed=seed)
                                    inj = inject_overshoot(env, speed=v, offset_m=off, overshoot=o)
                                    result = run_recovery(env, act_fn, v0=v)
                                    rows.append(
                                        {
                                            "driver": driver_name,
                                            "obstacle_on": obstacle_on,
                                            "mu": mu,
                                            "overshoot": o,
                                            "speed_mps": v,
                                            "offset_m": off,
                                            "seed": seed,
                                            "obstacle_d_m": round(d, 3),
                                            "mass_scale": round(env.params.mass / 1450.0, 4),
                                            "stiff_scale": round(env.params.cr / 110000.0, 4),
                                            **{key: round(val, 5) for key, val in inj.items()},
                                            **result,
                                        }
                                    )
                            finally:
                                env.close()
                    elapsed = time.time() - started
                    print(
                        f"[{cell_count}/{n_cells}] mu={mu} o={o} v={v} off={off} "
                        f"rows={len(rows)} elapsed={elapsed:.0f}s",
                        flush=True,
                    )

    summary = aggregate(rows)
    payload = {
        "protocol": "reflex_overshoot_recovery_v1",
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "quick_mode": bool(args.quick),
        "family": {
            "base": "B2K2_final (experiments/feasibility_audit/selfid_task_final_spec.json)",
            "harness_deltas": [
                "dynamics randomization re-enabled at library defaults (mu pinned per cell)",
                "obstacle finish_on_pass=False (episode must not truncate mid-recovery)",
            ],
            "track_radius_m": TRACK_RADIUS,
            "track_width_m": TRACK_WIDTH,
            "reveal_distance_m": REVEAL_DISTANCE,
            "mu_to_d_knots": {"mu": MU_KNOTS, "d_m": D_KNOTS},
            "jitter_d_m": JITTER_D_M,
            "d_floor_m": D_FLOOR_M,
        },
        "grid": {
            "mu_levels": MU_LEVELS,
            "overshoot_levels": OVERSHOOTS,
            "speeds_mps": SPEEDS_MPS,
            "lateral_offsets_m": LATERAL_OFFSETS_M,
            "n_seeds_per_cell": N_SEEDS,
            "seed_law": "20260617*100 + mu_idx*1e5 + o_idx*1e4 + v_idx*1e3 + off_idx*100 + k",
        },
        "injection_model": {
            "rear_slip": "beta = -o * artanh(0.95)*mu*Fzr/cr (sampled params), cap 0.50 rad",
            "yaw": "yaw_rate = kappa*v + o*mu*g/v (o x max sustainable yaw rate), cap 3.0 rad/s",
            "steer": "front slip forced to -o x artanh(0.95)*mu*Fzf/cf within actuator limit",
            "brake": "drive_force = -min(o*mu*Fzr, max_brake) (past the rear friction circle)",
            "heading": "nose rotated into turn by 0.4 x slip depth; course drifts outward",
            "side": "slide toward the OUTSIDE boundary; offset = initial |lateral_error|",
        },
        "recovery_definition": {
            "sustain_steps": SUSTAIN_STEPS,
            "beta_max_rad": STABLE_BETA_RAD,
            "yaw_surplus_max_radps": STABLE_YAW_SURPLUS_RADPS,
            "lateral_max_m": STABLE_LAT_M,
            "min_speed_mps": STABLE_MIN_SPEED_MPS,
            "horizon_steps": HORIZON_STEPS,
            "hard_failures": ["off_track", "obstacle_collision", "yaw_rate_limit", "speed_too_high"],
            "stalled": "speed_too_low termination (stopped; safe-ish but NOT recovered)",
            "contained_drift": (
                "no terminal, ended inside marked corridor (|lat|<=2.5) with |beta|<=0.25: "
                "safe containment in a bounded persistent drift, but not clean stabilization"
            ),
            "save_rate": "outcome in {recovered, contained_drift, stalled} (= did not crash)",
            "boundary_rate_bar": BOUNDARY_RATE_BAR,
        },
        "drivers": {
            "baseline_coast": "steer 0, no throttle, no brake (no-reflex control)",
            "v4_incumbent": "src/autodrift/active_safety_reflex_driver.py (M3105)",
            "v5_candidate": "src/autodrift/active_safety_driver_v5_curvature_speed_governor_candidate.py",
        },
        "n_episodes": len(rows),
        "elapsed_s": round(time.time() - started, 1),
        "summary": summary,
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(to_jsonable(payload), indent=1))

    fieldnames = list(rows[0].keys())
    with EPISODES_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"episodes={len(rows)} -> {RESULTS_JSON}")
    for entry in summary["overall"]:
        print(
            f"  ob={'on ' if entry['obstacle_on'] else 'off'} {entry['driver']:16s} "
            f"recovery_rate={entry['recovery_rate']:.3f} "
            f"steps={entry['mean_recovery_steps']:.1f} dist_lost={entry['mean_distance_lost_m']:.1f} m "
            f"outcomes={entry['outcomes']}"
        )


if __name__ == "__main__":
    main()
