#!/usr/bin/env python3
"""B2b high-speed domain pricing protocol.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/high_speed_pricing.py --quick
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/high_speed_pricing.py

Quick mode is a protocol smoke only. Full mode is the preregistered B2b
pricing panel over the M3224 high-speed observation/preview profile.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import numpy as np

from autodrift.config import build_env_config
from autodrift.env import (
    AutoDriftEnv,
    DriftEnvConfig,
    EGO_OBS_DIM,
    LAST_ACTION_OBS_DIM,
    OBSTACLE_SLOT_DIM,
    ObservationScaleConfig,
    ROAD_POINT_DIM,
)
from autodrift.evaluate import outcome_bucket_from_info
from autodrift.scenarios import classify_obstacle_scenario
from autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight import (
    V2_POLICY_CONFIG,
    speed_floor_aware_direct_action,
)
import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight as m4


REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/high_speed_pricing_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/high_speed_pricing.json"
QUICK_JSON = REPO / "experiments/feasibility_audit/high_speed_pricing_quick.json"
RUN_DIR = REPO / "runs/feasibility_audit/high_speed_pricing"

SEED_BASE = 20260924
TRACK_R = 250.0
TRACK_WIDTH = 12.0
DT = 0.02

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

GRID_BRAKE = (0.7, 1.0, 1.6)
GRID_STEER = (1.0, 1.5, 2.2)
GRID_RELEV = (1.0, 1.6, 2.4)
GRID = [(b, s, r) for b in GRID_BRAKE for s in GRID_STEER for r in GRID_RELEV]
IDENTITY_INDEX = GRID.index((1.0, 1.0, 1.0))

ARMS = ["fixed_v4_incumbent", "fixed_star", "v4_rls", "v4_pertuned"]
FAIL_MODES = ["success", "collision", "offtrack", "speed_too_low", "timeout_other"]

CLAIM_BOUNDARY = (
    "B2b high-speed pricing measurement only: scripted reflex baselines on the "
    "M3224 high-speed observation/preview profile, an explicitly scale-aware "
    "fixed* and per-cell tuned reflex floor, a nominal/no-spread inert RLS arm, "
    "and a reveal-constrained privileged oracle compared on high-speed obstacle "
    "windows. Zero training; no incumbent driver mutation, validation ranking, "
    "promotion, driver-performance, high-fidelity sufficiency, paper, "
    "repair-success, robustness-result, feasibility-proof, or self-ID claim. "
    "Quick mode is protocol smoke only and is not a pricing verdict."
)

CELL_SPECS = [
    {"cell": "hs24_tight_mu055", "speed_mps": 24.0, "mu": 0.55, "reveal_m": 22.0, "distance_m": 26.0, "half_width_m": 1.00},
    {"cell": "hs30_tight_mu075", "speed_mps": 30.0, "mu": 0.75, "reveal_m": 30.0, "distance_m": 34.0, "half_width_m": 1.00},
    {"cell": "hs36_tight_mu095", "speed_mps": 36.0, "mu": 0.95, "reveal_m": 30.0, "distance_m": 34.0, "half_width_m": 1.00},
    {"cell": "hs36_tight_mu075", "speed_mps": 36.0, "mu": 0.75, "reveal_m": 30.0, "distance_m": 34.0, "half_width_m": 1.05},
    {"cell": "hs36_mid_mu075", "speed_mps": 36.0, "mu": 0.75, "reveal_m": 38.0, "distance_m": 42.0, "half_width_m": 1.05},
    {"cell": "hs30_mid_mu055", "speed_mps": 30.0, "mu": 0.55, "reveal_m": 38.0, "distance_m": 42.0, "half_width_m": 1.10},
]


# ----------------------------------------------------------------- controllers


def canonicalize_high_speed_obs(obs: np.ndarray) -> np.ndarray:
    """Map M3224 high-speed-scaled obs72 back to the legacy controller scales.

    The env keeps NN-facing channels in range by changing observation scales.
    The scripted v2/v4 reflex code hard-codes legacy inverse scales. Primary
    B2b classical arms therefore use this explicit adapter; the raw incumbent
    transfer is still reported as `fixed_v4_incumbent`.
    """
    out = np.asarray(obs, dtype=np.float32).copy()
    out[0] *= HIGH_SPEED_SCALE.ego_vx / 20.0
    out[1] *= HIGH_SPEED_SCALE.ego_vy / 12.0
    out[3] *= HIGH_SPEED_SCALE.ego_ax / 15.0
    out[4] *= HIGH_SPEED_SCALE.ego_ay / 15.0
    for idx in list(range(13, 28, 2)) + list(range(29, 44, 2)):
        out[idx] *= HIGH_SPEED_SCALE.road_y / 20.0
    for idx in (48, 55, 62, 69):
        out[idx] *= HIGH_SPEED_SCALE.obstacle_rel_vy / 12.0
    return out


def composed_action(obs: np.ndarray, v2cfg: dict, v4cfg: dict, *, scale_aware: bool) -> np.ndarray:
    ctrl_obs = canonicalize_high_speed_obs(obs) if scale_aware else np.asarray(obs, dtype=np.float32)
    action = np.asarray(speed_floor_aware_direct_action(ctrl_obs, v2cfg), dtype=np.float32).copy()
    f = m4._hard_safety_features(ctrl_obs, v4cfg)
    g = v4cfg["gains"]
    th = v4cfg["thresholds"]
    lsr = float(np.clip((f["vx_body"] - float(th["local_hard_safety_speed_mps"])) / 6.0, 0.0, 1.0))
    oexc = float(np.clip((f["obstacle_urgency"] - float(th["local_obstacle_urgency_trigger"])) / 0.5, 0.0, 1.0))
    eexc = float(np.clip((f["edge_urgency"] - float(th["local_edge_urgency_trigger"])) / 0.28, 0.0, 1.0))
    lr = lsr * max(oexc, eexc)
    if lr > 0.0:
        action[0] += (
            float(g["local_obstacle_steer"]) * f["obstacle_avoid_direction"] * oexc
            + float(g["local_edge_steer"]) * f["road_center_error"] * eexc
        )
        bp = float(np.clip((float(action[2]) + 1.0) / 2.0, 0.0, 1.0))
        bp = float(np.clip(bp + lsr * (float(g["local_obstacle_brake"]) * oexc + float(g["local_edge_brake"]) * eexc), 0.0, 1.0))
        action[2] = -1.0 + 2.0 * bp
        if f["vx_body"] > float(th["speed_floor_preserve_below_mps"]):
            action[1] -= float(g["local_throttle_suppression"]) * lr
    return np.clip(action, -1.0, 1.0).astype(np.float32)


def grid_cfgs(bm: float, stm: float, rm: float) -> tuple[dict, dict]:
    v2 = deepcopy(V2_POLICY_CONFIG)
    v4 = deepcopy(m4.V4_POLICY_CONFIG)
    for gk in ("obstacle_brake", "edge_brake", "stability_brake"):
        v2["gains"][gk] *= bm
    for gk in ("local_obstacle_brake", "local_edge_brake"):
        v4["gains"][gk] *= bm
    v2["gains"]["obstacle_steer"] *= stm
    v4["gains"]["local_obstacle_steer"] *= stm
    v2["thresholds"]["obstacle_relevance_distance_m"] *= rm
    v4["thresholds"]["obstacle_relevance_distance_m"] *= rm
    return v2, v4


# -------------------------------------------------------------------- scenarios


def obstacle_slot_start(config: DriftEnvConfig) -> int:
    road_dim = 2 * config.road_lookahead_count * ROAD_POINT_DIM
    action_dim = LAST_ACTION_OBS_DIM if config.action_history_mode == "full" else 0
    return EGO_OBS_DIM + action_dim + road_dim


def active_obstacle_present(obs: np.ndarray, config: DriftEnvConfig) -> bool:
    start = obstacle_slot_start(config)
    slot = np.asarray(obs[start:start + OBSTACLE_SLOT_DIM], dtype=np.float64)
    return bool(slot[0] > 0.5)


def active_cells(quick: bool) -> list[dict[str, Any]]:
    return CELL_SPECS[:2] if quick else CELL_SPECS


def _phase_seed_offset(phase: str) -> int:
    if phase == "selection":
        return 0
    if phase == "validation":
        return 6000
    raise ValueError(f"unknown phase {phase!r}")


def make_row(cell: dict[str, Any], cell_index: int, phase: str, row_index: int) -> dict[str, Any]:
    rng = np.random.default_rng([SEED_BASE, cell_index, _phase_seed_offset(phase), row_index])
    speed = float(cell["speed_mps"] + rng.uniform(-0.35, 0.35))
    mu = float(cell["mu"] + rng.uniform(-0.025, 0.025))
    reveal = float(cell["reveal_m"] + rng.uniform(-1.0, 1.0))
    distance = float(max(reveal + 2.0, cell["distance_m"] + rng.uniform(-1.2, 1.2)))
    half_width = float(cell["half_width_m"] + rng.uniform(-0.05, 0.05))
    lateral = float(rng.uniform(-0.15, 0.15))
    scenario = classify_obstacle_scenario(
        speed=speed,
        mu=mu,
        obstacle_distance=distance,
        obstacle_half_width=half_width,
        obstacle_lateral_offset=lateral,
    )
    return {
        "cell": str(cell["cell"]),
        "phase": phase,
        "row_index": int(row_index),
        "eval_seed": int(SEED_BASE + cell_index * 10000 + _phase_seed_offset(phase) + row_index * 37),
        "speed_mps": speed,
        "mu": mu,
        "distance_m": distance,
        "half_width_m": half_width,
        "lateral_offset_m": lateral,
        "reveal_distance_m": reveal,
        "required_lateral_offset_m": float(scenario.required_lateral_offset),
        "label": str(scenario.label),
    }


def sample_rows(quick: bool, phase: str) -> dict[str, list[dict[str, Any]]]:
    n_rows = 2 if quick and phase == "selection" else 4 if quick else 4 if phase == "selection" else 8
    rows: dict[str, list[dict[str, Any]]] = {}
    for cell_index, cell in enumerate(active_cells(quick)):
        rows[str(cell["cell"])] = [make_row(cell, cell_index, phase, idx) for idx in range(n_rows)]
    return rows


def row_env_config(row: dict[str, Any]) -> DriftEnvConfig:
    return build_env_config(
        {
            "dt": DT,
            "max_steps": 220,
            "track_kind": "circle",
            "track_radius": TRACK_R,
            "track_width": TRACK_WIDTH,
            "speed_range": (row["speed_mps"], row["speed_mps"]),
            "beta_target_range": (0.04, 0.04),
            "friction_limited_speed": False,
            "max_speed_limit": 45.0,
            "obstacle_relative_velocity_mode": "ego",
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
            "randomization": {
                "mu_range": (row["mu"], row["mu"]),
                "mass_scale_range": (1.0, 1.0),
                "cg_shift_range": (0.0, 0.0),
                "inertia_scale_range": (1.0, 1.0),
                "tire_stiffness_scale_range": (1.0, 1.0),
                "drive_scale_range": (1.0, 1.0),
                "brake_scale_range": (1.0, 1.0),
                "actuator_tau_scale_range": (1.0, 1.0),
            },
            "obstacle": {
                "enabled": True,
                "distance_range": (row["distance_m"], row["distance_m"]),
                "half_width_range": (row["half_width_m"], row["half_width_m"]),
                "lateral_offset_range": (row["lateral_offset_m"], row["lateral_offset_m"]),
                "finish_on_pass": True,
                "pass_reward": 10.0,
                "allowed_labels": ("aeb_feasible", "aes_feasible", "drift_required", "unavoidable"),
                "max_sample_attempts": 1,
                "perception_reveal_step": 0,
                "perception_reveal_distance": row["reveal_distance_m"],
                "motion_mode": "static",
            },
        }
    )


# -------------------------------------------------------------------- rollout


def light_rollout(row: dict[str, Any], controller: Callable[[int, np.ndarray], np.ndarray]) -> dict[str, Any]:
    env = AutoDriftEnv(row_env_config(row))
    obs, info = env.reset(seed=int(row["eval_seed"]))
    term = trunc = False
    t = 0
    reveal_step = None
    reset_obs_finite = bool(np.isfinite(obs).all() and obs.shape == (72,))
    reset_speed_ref = float(info.get("speed_ref", float("nan")))
    reset_preview_time = float(info.get("road_lookahead_time_s", float("nan")))
    while not (term or trunc):
        if reveal_step is None and active_obstacle_present(obs, env.config):
            reveal_step = t
        action = np.asarray(controller(t, obs), dtype=np.float32)
        obs, _reward, term, trunc, info = env.step(action)
        t += 1
    env.close()
    bucket = outcome_bucket_from_info(info, terminated=term, truncated=trunc)
    return {
        "bucket": bucket,
        "steps": int(info.get("step", t)),
        "reveal_step": reveal_step,
        "reset_obs_finite": reset_obs_finite,
        "reset_speed_ref": reset_speed_ref,
        "reset_preview_time_s": reset_preview_time,
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "completion_reason": str(info.get("completion_reason", "") or ""),
        "min_clearance_margin": float(info.get("min_clearance_margin", float("nan"))),
        "obstacle_label_runtime": str(info.get("obstacle_label", "") or ""),
        "obstacle_motion_mode": str(info.get("obstacle_motion_mode", "") or ""),
    }


def failure_mode(bucket: str, reason: str) -> str:
    if bucket == "success_obstacle_pass":
        return "success"
    if bucket == "collision_failure" or reason == "obstacle_collision":
        return "collision"
    if reason == "off_track":
        return "offtrack"
    if reason == "speed_too_low":
        return "speed_too_low"
    return "timeout_other"


# --------------------------------------------------------------------- oracle


def _structured_candidates() -> list[tuple[str, Callable[[int], np.ndarray]]]:
    cands: list[tuple[str, Callable[[int], np.ndarray]]] = [
        ("full_brake", lambda rel: np.array([0.0, -1.0, 1.0], dtype=np.float32))
    ]
    for st in (0.35, 0.65, 1.0, -0.35, -0.65, -1.0):
        cands.append((f"brake_steer_{st:+.2f}", lambda rel, st=st: np.array([st, -1.0, 1.0], dtype=np.float32)))
    for st in (0.65, 1.0, -0.65, -1.0):
        cands.append((f"coast_steer_{st:+.2f}", lambda rel, st=st: np.array([st, -1.0, -1.0], dtype=np.float32)))
    for st in (1.0, -1.0):
        for n in (8, 16, 24):
            cands.append(
                (
                    f"swerve_{st:+.0f}_n{n}",
                    lambda rel, st=st, n=n: (
                        np.array([st, -1.0, 1.0], dtype=np.float32)
                        if rel < n
                        else np.array([0.0, -1.0, 1.0], dtype=np.float32)
                    ),
                )
            )
    return cands


def oracle_solve(
    row: dict[str, Any],
    reveal_step: int,
    prefix_ctrl: Callable[[np.ndarray], np.ndarray],
    rng: np.random.Generator,
    quick: bool,
) -> dict[str, Any]:
    rollouts = 0
    structured_attempts = 0
    cem_attempts = 0
    best_score = -float("inf")
    best_by = ""

    def rollout_tail(name: str, tail_fn: Callable[[int], np.ndarray], family: str) -> dict[str, Any]:
        nonlocal rollouts, structured_attempts, cem_attempts, best_score, best_by

        def ctrl(t: int, obs: np.ndarray) -> np.ndarray:
            if t < reveal_step:
                return prefix_ctrl(obs)
            return tail_fn(t - reveal_step)

        res = light_rollout(row, ctrl)
        rollouts += 1
        if family == "structured":
            structured_attempts += 1
        else:
            cem_attempts += 1
        score = float(res["steps"]) + 25.0 * max(float(res["min_clearance_margin"]), -3.0)
        if score > best_score:
            best_score = score
            best_by = f"{family}:{name}"
        return res

    for name, fn in _structured_candidates():
        res = rollout_tail(name, fn, "structured")
        if res["bucket"] == "success_obstacle_pass":
            return {
                "solved": True,
                "by": f"structured:{name}",
                "rollouts": rollouts,
                "structured_attempts": structured_attempts,
                "cem_attempts": cem_attempts,
                "best_failed_by": "",
            }

    n_seg, seg_len = (6, 8) if quick else (10, 8)
    pop, elites, iters = (8, 2, 2) if quick else (20, 5, 5)
    mean = np.tile(np.array([0.0, -1.0, 1.0], dtype=np.float64), (n_seg, 1))
    std = np.full_like(mean, 0.6)
    for it in range(iters):
        samples = np.clip(rng.normal(mean[None], std[None], size=(pop, n_seg, 3)), -1.0, 1.0)
        scored: list[tuple[float, int]] = []
        for i in range(pop):
            seg = samples[i]

            def tail(rel: int, seg: np.ndarray = seg) -> np.ndarray:
                return seg[min(rel // seg_len, n_seg - 1)].astype(np.float32)

            res = rollout_tail(f"cem_iter{it}_sample{i}", tail, "cem")
            if res["bucket"] == "success_obstacle_pass":
                return {
                    "solved": True,
                    "by": f"cem_iter{it}",
                    "rollouts": rollouts,
                    "structured_attempts": structured_attempts,
                    "cem_attempts": cem_attempts,
                    "best_failed_by": "",
                }
            score = float(res["steps"]) + 25.0 * max(float(res["min_clearance_margin"]), -3.0)
            scored.append((score, i))
        scored.sort(key=lambda item: (-item[0], item[1]))
        elite = samples[[i for _score, i in scored[:elites]]]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), 0.15)
    return {
        "solved": False,
        "by": "",
        "rollouts": rollouts,
        "structured_attempts": structured_attempts,
        "cem_attempts": cem_attempts,
        "best_failed_by": best_by,
    }


# ----------------------------------------------------------------- statistics


def wilson_ci(p: float, n: int, z: float = 1.96) -> list[float]:
    if n == 0 or not math.isfinite(p):
        return [float("nan"), float("nan")]
    den = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]


def newcombe_diff_ci(p1: float, n1: int, p2: float, n2: int) -> list[float]:
    if n1 == 0 or n2 == 0 or not math.isfinite(p1) or not math.isfinite(p2):
        return [float("nan"), float("nan")]
    l1, u1 = wilson_ci(p1, n1)
    l2, u2 = wilson_ci(p2, n2)
    d = p1 - p2
    return [
        round(d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), 4),
        round(d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2), 4),
    ]


def paired_bootstrap_ci(a: np.ndarray, b: np.ndarray, rng: np.random.Generator, n_boot: int = 2000) -> list[float]:
    n = len(a)
    if n == 0:
        return [float("nan"), float("nan")]
    idx = rng.integers(0, n, size=(n_boot, n))
    diffs = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


def aggregate_cells(episode_rows: list[dict[str, Any]], quick: bool) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    rng_boot = np.random.default_rng([SEED_BASE, 88, int(quick)])
    for cell in sorted({row["cell"] for row in episode_rows}):
        rows = [row for row in episode_rows if row["cell"] == cell]
        filt = [row for row in rows if bool(row["oracle_solved"])]
        out: dict[str, Any] = {
            "n_rows_unfiltered": len(rows),
            "n_rows_oracle_solved": len(filt),
            "oracle_solvability": round(sum(1 for row in rows if row["oracle_solved"]) / max(len(rows), 1), 4),
            "labels": {label: sum(1 for row in rows if row["label"] == label) for label in sorted({r["label"] for r in rows})},
        }
        for tag, sub in (("oracle_solved_denominator", filt), ("unfiltered", rows)):
            arms_block = {}
            for arm in ARMS:
                n = len(sub)
                p = sum(1 for row in sub if row[f"{arm}_outcome"] == "success") / max(n, 1)
                arms_block[arm] = {
                    "success": round(p, 4),
                    "n": n,
                    "wilson_ci95": wilson_ci(p, n),
                    "failure_modes": {mode: sum(1 for row in sub if row[f"{arm}_outcome"] == mode) for mode in FAIL_MODES},
                }
            out[tag] = arms_block

        n = len(filt)
        vec = {
            arm: np.array([1.0 if row[f"{arm}_outcome"] == "success" else 0.0 for row in filt])
            for arm in ARMS
        }
        oracle_vec = np.ones(n, dtype=np.float64)
        p = {arm: float(vec[arm].mean()) if n else float("nan") for arm in ARMS}
        out["readouts_oracle_solved_denominator"] = {
            "structural_gap_oracle_minus_pertuned": {
                "value": round(1.0 - p["v4_pertuned"], 4) if n else float("nan"),
                "paired_bootstrap_ci95": paired_bootstrap_ci(oracle_vec, vec["v4_pertuned"], rng_boot),
                "newcombe_ci95": newcombe_diff_ci(1.0, n, p["v4_pertuned"], n),
            },
            "structural_gap_oracle_minus_fixed_star": {
                "value": round(1.0 - p["fixed_star"], 4) if n else float("nan"),
                "paired_bootstrap_ci95": paired_bootstrap_ci(oracle_vec, vec["fixed_star"], rng_boot),
            },
            "pertuned_minus_fixed_star": {
                "value": round(p["v4_pertuned"] - p["fixed_star"], 4) if n else float("nan"),
                "paired_bootstrap_ci95": paired_bootstrap_ci(vec["v4_pertuned"], vec["fixed_star"], rng_boot),
            },
            "scale_adapter_lift_fixed_star_minus_raw_incumbent": {
                "value": round(p["fixed_star"] - p["fixed_v4_incumbent"], 4) if n else float("nan"),
                "paired_bootstrap_ci95": paired_bootstrap_ci(vec["fixed_star"], vec["fixed_v4_incumbent"], rng_boot),
            },
        }
        cells[cell] = out
    return cells


# ------------------------------------------------------------------- main run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--device", default="cpu", choices=["cpu"])
    args = parser.parse_args()
    quick = bool(args.quick)

    t_start = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    progress_path = RUN_DIR / ("progress_quick.json" if quick else "progress.json")
    rows_csv = RUN_DIR / ("episode_rows_quick.csv" if quick else "episode_rows.csv")
    results_json = QUICK_JSON if quick else RESULTS_JSON
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    def progress(stage: str, **kw: Any) -> None:
        payload = {"stage": stage, "elapsed_s": round(time.time() - t_start, 1), **kw}
        progress_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[{time.time() - t_start:7.1f}s] {stage} {kw}", flush=True)

    rng0 = np.random.default_rng(0)
    for _ in range(200):
        obs = rng0.normal(0, 0.3, 72).astype(np.float32)
        lhs = composed_action(obs, V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG, scale_aware=False)
        rhs = m4.v4_v2_fallback_no_regression_hard_safety_direct_action(obs, m4.V4_POLICY_CONFIG)
        assert np.array_equal(lhs, rhs), "raw composed action != canonical v4"
    progress("gate_raw_composed_equals_v4_pass")

    probe = np.zeros(72, dtype=np.float32)
    probe[0] = 36.0 / HIGH_SPEED_SCALE.ego_vx
    assert abs(float(canonicalize_high_speed_obs(probe)[0] * 20.0) - 36.0) < 1e-6
    progress("gate_scale_adapter_pass")

    selection_rows = sample_rows(quick, "selection")
    validation_rows = sample_rows(quick, "validation")
    all_sel = {row["eval_seed"] for rows in selection_rows.values() for row in rows}
    all_val = {row["eval_seed"] for rows in validation_rows.values() for row in rows}
    assert not (all_sel & all_val), "selection/validation seed overlap"
    active_cell_names = [str(cell["cell"]) for cell in active_cells(quick)]
    progress("rows_sampled", cells=active_cell_names, selection=len(all_sel), validation=len(all_val))

    row_contract_failures = []
    for cell_name in active_cell_names:
        for row in selection_rows[cell_name][:1] + validation_rows[cell_name][:1]:
            res = light_rollout(row, lambda _t, obs: composed_action(obs, V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG, scale_aware=True))
            if (
                not res["reset_obs_finite"]
                or res["reset_speed_ref"] < 23.0
                or res["reset_preview_time_s"] < 2.45
                or res["obstacle_motion_mode"] != "static"
                or not res["obstacle_label_runtime"]
            ):
                row_contract_failures.append({"cell": cell_name, "seed": row["eval_seed"], "probe": res})
    assert not row_contract_failures, f"high-speed row contract failures: {row_contract_failures[:2]}"
    progress("gate_high_speed_rows_pass", checked=2 * len(active_cell_names))

    grid_cfg_cache = [grid_cfgs(*grid) for grid in GRID]
    selection_stats: dict[str, list[dict[str, Any]]] = {}
    n_selection_episodes = 0
    for cell_name in active_cell_names:
        per_cfg = []
        for gi, (v2c, v4c) in enumerate(grid_cfg_cache):
            succ = 0
            hard = 0
            for row in selection_rows[cell_name]:
                res = light_rollout(row, lambda _t, obs, v2c=v2c, v4c=v4c: composed_action(obs, v2c, v4c, scale_aware=True))
                n_selection_episodes += 1
                mode = failure_mode(res["bucket"], res["termination_reason"])
                succ += mode == "success"
                hard += mode in ("collision", "offtrack")
            per_cfg.append({"grid_index": gi, "grid": GRID[gi], "sel_success": succ, "sel_hard_fail": hard})
        selection_stats[cell_name] = per_cfg
    progress("selection_sweep_done", episodes=n_selection_episodes)

    pool = np.zeros(len(GRID), dtype=np.float64)
    pool_hard = np.zeros(len(GRID), dtype=np.float64)
    for cell_name in active_cell_names:
        for cfg in selection_stats[cell_name]:
            pool[cfg["grid_index"]] += cfg["sel_success"]
            pool_hard[cfg["grid_index"]] += cfg["sel_hard_fail"]

    def grid_rank_key(gi: int, succ: float, hard: float) -> tuple[Any, ...]:
        dist = sum(1 for value in GRID[gi] if value != 1.0)
        return (-succ, hard, dist, gi)

    star_index = min(range(len(GRID)), key=lambda gi: grid_rank_key(gi, pool[gi], pool_hard[gi]))
    star = GRID[star_index]
    star_cfg = grid_cfg_cache[star_index]
    progress("fixed_star_selected", grid=star, selection_success=int(pool[star_index]), identity_success=int(pool[IDENTITY_INDEX]))

    pertuned_choice: dict[str, int] = {}
    for cell_name, per_cfg in selection_stats.items():
        def kf(cfg: dict[str, Any]) -> tuple[Any, ...]:
            gi = int(cfg["grid_index"])
            dist_star = sum(1 for a, b in zip(GRID[gi], star, strict=True) if a != b)
            return (-cfg["sel_success"], cfg["sel_hard_fail"], dist_star, gi)

        pertuned_choice[cell_name] = int(min(per_cfg, key=kf)["grid_index"])

    incumbent_cfg = (V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG)
    rls_cfg = star_cfg
    episode_rows: list[dict[str, Any]] = []
    n_validation_arm_episodes = 0
    n_oracle_rollouts = 0
    n_oracle_attempted_rows = 0
    n_rows_with_reveal = 0
    for cell_i, cell_name in enumerate(active_cell_names):
        pertuned_cfg = grid_cfg_cache[pertuned_choice[cell_name]]
        for row in validation_rows[cell_name]:
            arm_results: dict[str, dict[str, Any]] = {}
            for arm, cfg, scale_aware in (
                ("fixed_v4_incumbent", incumbent_cfg, False),
                ("fixed_star", star_cfg, True),
                ("v4_rls", rls_cfg, True),
                ("v4_pertuned", pertuned_cfg, True),
            ):
                v2c, v4c = cfg
                res = light_rollout(row, lambda _t, obs, v2c=v2c, v4c=v4c, scale_aware=scale_aware: composed_action(obs, v2c, v4c, scale_aware=scale_aware))
                n_validation_arm_episodes += 1
                arm_results[arm] = res
            reveal = arm_results["fixed_star"]["reveal_step"]
            if reveal is not None:
                n_rows_with_reveal += 1
            reveal_step = 0 if reveal is None else int(reveal)
            oracle = oracle_solve(
                row,
                reveal_step,
                lambda obs: composed_action(obs, star_cfg[0], star_cfg[1], scale_aware=True),
                np.random.default_rng([SEED_BASE, 51, cell_i, row["row_index"], int(quick)]),
                quick,
            )
            n_oracle_attempted_rows += 1
            n_oracle_rollouts += int(oracle["rollouts"])
            base = {
                "cell": cell_name,
                "eval_seed": row["eval_seed"],
                "row_index": row["row_index"],
                "speed_mps": round(float(row["speed_mps"]), 4),
                "mu": round(float(row["mu"]), 4),
                "distance_m": round(float(row["distance_m"]), 4),
                "reveal_distance_m": round(float(row["reveal_distance_m"]), 4),
                "half_width_m": round(float(row["half_width_m"]), 4),
                "lateral_offset_m": round(float(row["lateral_offset_m"]), 4),
                "required_lateral_offset_m": round(float(row["required_lateral_offset_m"]), 4),
                "label": row["label"],
                "fixed_star_grid": str(star),
                "pertuned_grid": str(GRID[pertuned_choice[cell_name]]),
                "fixed_v4_incumbent_policy": "raw_transfer_on_m3224_scaled_obs",
                "scale_adapter_policy": "fixed_star_v4_rls_v4_pertuned_use_known_m3224_observation_scale_adapter",
                "rls_arm_policy": "nominal_no_spread_inert_identical_to_fixed_star",
                "reveal_step": reveal_step,
                "fixed_star_had_reveal": reveal is not None,
                "oracle_solved": bool(oracle["solved"]),
                "oracle_by": str(oracle["by"]),
                "oracle_best_failed_by": str(oracle["best_failed_by"]),
                "oracle_rollouts": int(oracle["rollouts"]),
                "oracle_structured_attempts": int(oracle["structured_attempts"]),
                "oracle_cem_attempts": int(oracle["cem_attempts"]),
            }
            for arm, res in arm_results.items():
                base[f"{arm}_outcome"] = failure_mode(res["bucket"], res["termination_reason"])
                base[f"{arm}_bucket"] = str(res["bucket"])
                base[f"{arm}_steps"] = int(res["steps"])
                base[f"{arm}_min_clearance_margin"] = round(float(res["min_clearance_margin"]), 4)
            episode_rows.append(base)
        progress(
            "validation_cell_done",
            cell=cell_name,
            done=cell_i + 1,
            total=len(active_cell_names),
            validation_arm_episodes=n_validation_arm_episodes,
            oracle_rollouts=n_oracle_rollouts,
        )

    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(episode_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(episode_rows)

    cells = aggregate_cells(episode_rows, quick)
    qualifying = []
    for cell_name, out in cells.items():
        gap = out["readouts_oracle_solved_denominator"]["structural_gap_oracle_minus_pertuned"]
        if gap["value"] >= 0.15 and gap["paired_bootstrap_ci95"][0] > 0.0:
            qualifying.append(cell_name)

    all_oracle_attempted = n_oracle_attempted_rows == len(episode_rows)
    all_rows_visible = n_rows_with_reveal == len(episode_rows)
    all_oracles_exercised_cem = all(row["oracle_cem_attempts"] > 0 or row["oracle_solved"] for row in episode_rows)
    protocol_smoke_pass = bool(
        quick
        and all_oracle_attempted
        and all_rows_visible
        and all_oracles_exercised_cem
        and len(active_cell_names) == 2
        and len(episode_rows) == 8
    )
    full_pricing_positive = bool((not quick) and len(qualifying) >= 2)

    payload = {
        "protocol": "b2b_high_speed_pricing",
        "generated_by": "scripts/feasibility_audit/high_speed_pricing.py",
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration_echo": {
            "file": str(PREREG),
            "decision_rule": prereg["decision_rule"],
            "quick_decision_rule": prereg["quick_decision_rule"],
        },
        "seed_base": SEED_BASE,
        "high_speed_profile": {
            "track_radius_m": TRACK_R,
            "track_width_m": TRACK_WIDTH,
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
            "scale_adapter": "primary classical arms canonicalize high-speed obs back to legacy controller scales; raw incumbent transfer is reported separately",
        },
        "cells": cells,
        "cell_specs": active_cells(quick),
        "fixed_star": {
            "grid": star,
            "grid_index": star_index,
            "selection_success": int(pool[star_index]),
            "selection_n": int(sum(len(rows) for rows in selection_rows.values())),
            "identity_selection_success": int(pool[IDENTITY_INDEX]),
        },
        "pertuned_choice": {cell: {"grid_index": gi, "grid": GRID[gi]} for cell, gi in pertuned_choice.items()},
        "b2b_decision": {
            "mode": "protocol_smoke" if quick else "full_pricing",
            "accepted": protocol_smoke_pass if quick else full_pricing_positive,
            "quick_protocol_smoke_pass": protocol_smoke_pass,
            "full_pricing_positive": full_pricing_positive,
            "qualifying_cells": qualifying,
            "rule": prereg["quick_decision_rule"] if quick else prereg["decision_rule"],
            "interpretation": (
                "Quick mode validates the protocol only; it does not price B2b."
                if quick
                else "Full mode is positive iff >=2 cells satisfy oracle-minus-pertuned >=0.15 with paired CI95 lower >0 on the oracle-solved denominator."
            ),
        },
        "protocol_gates": {
            "selection_validation_seed_disjoint": not (all_sel & all_val),
            "all_oracle_attempted": all_oracle_attempted,
            "all_rows_visible_under_fixed_star": all_rows_visible,
            "structured_and_cem_or_success_coverage": all_oracles_exercised_cem,
            "validation_rows": len(episode_rows),
            "rows_with_reveal": n_rows_with_reveal,
            "oracle_attempted_rows": n_oracle_attempted_rows,
        },
        "budget": {
            "selection_episodes": n_selection_episodes,
            "validation_arm_episodes": n_validation_arm_episodes,
            "oracle_rollouts": n_oracle_rollouts,
            "elapsed_s": round(time.time() - t_start, 1),
        },
        "episode_rows_csv": str(rows_csv),
    }
    results_json.parent.mkdir(parents=True, exist_ok=True)
    results_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    progress(
        "done",
        results=str(results_json),
        accepted=payload["b2b_decision"]["accepted"],
        qualifying=qualifying,
        elapsed_s=round(time.time() - t_start, 1),
    )
    print(json.dumps({"result": str(results_json), "accepted": payload["b2b_decision"]["accepted"]}, indent=2))
    if quick and not protocol_smoke_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
