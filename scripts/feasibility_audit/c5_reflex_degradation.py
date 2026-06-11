"""C5 pricing measurement: fixed reflex vs identified+tuned vs per-vehicle-tuned vs oracle
under vehicle dispersion, on mid-demand and limit-demand obstacle surfaces.

Prereg: experiments/feasibility_audit/c5_prereg.json (frozen before any
selection/validation rollout; read at runtime and echoed into the results).

Arms (all scripted, zero training):
  fixed_v4_incumbent  M3105 v4 reflex verbatim (secondary; family transfer)
  fixed_star          one 27-grid config selected on pooled S0 selection rows (primary fixed floor)
  v4_rls              5 s sub-limit familiarization prefix -> VehicleRLS kappa_b/kappa_d ->
                      frozen kappa map applied to fixed_star
  v4_pertuned         per (level, surface, instance) 27-grid winner on selection rows
  oracle              reveal-constrained privileged search (structured candidates + CEM,
                      early stop); defines the causal-solvability denominator

Grid: 4 dispersion levels (S0 nominal / S1 current / S2 extended / S3 adversarial corner)
x 2 task surfaces (T-mid / T-limit) x 12 vehicle instances x (10|12) paired validation seeds.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/c5_reflex_degradation.py [--quick]
"""

from __future__ import annotations

import argparse
import json
import math
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import numpy as np

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import outcome_bucket_from_info, run_episode_with_policy
from autodrift.scenarios import classify_obstacle_scenario
from autodrift.engineering_controller_active_safety_driver_v2_speed_floor_aware_direct_action_repair_materialization_preflight import (
    V2_POLICY_CONFIG,
    speed_floor_aware_direct_action,
)
import autodrift.engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight as m4

REPO = Path(__file__).resolve().parents[2]
PREREG = REPO / "experiments/feasibility_audit/c5_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/c5_reflex_degradation.json"
RUN_DIR = REPO / "runs/feasibility_audit/c5_reflex_degradation"

BASE = 20260712
GRAV = 9.81
MASS_NOM = 1450.0
MAX_BRAKE, MAX_DRIVE = 6000.0, 8200.0
DT = 0.02

LEVELS = ["S0", "S1", "S2", "S3"]
LEVEL_RANGES = {
    "S0": {"mass": (1.0, 1.0), "brake": (1.0, 1.0), "drive": (1.0, 1.0), "stiff": (1.0, 1.0), "tau": (1.0, 1.0)},
    "S1": {"mass": (0.85, 1.20), "brake": (0.80, 1.15), "drive": (0.80, 1.15), "stiff": (0.65, 1.35), "tau": (0.75, 1.75)},
    "S2": {"mass": (0.70, 1.50), "brake": (0.60, 1.30), "drive": (0.60, 1.30), "stiff": (0.50, 1.50), "tau": (0.75, 2.50)},
    "S3": {"mass": (1.40, 1.50), "brake": (0.60, 0.70), "drive": (0.60, 0.72), "stiff": (0.50, 0.62), "tau": (2.25, 2.50)},
}
SURFACES = ["T_mid", "T_limit"]
MU_DOMAIN = (0.25, 1.15)
TRACK_R = 60.0

GRID_BRAKE = (0.6, 1.0, 1.8)
GRID_STEER = (1.0, 1.45, 1.9)
GRID_RELEV = (1.0, 1.4, 1.8)
GRID = [(b, s, r) for b in GRID_BRAKE for s in GRID_STEER for r in GRID_RELEV]
IDENTITY_INDEX = GRID.index((1.0, 1.0, 1.0))

CLAIM_BOUNDARY = (
    "Feasibility-audit pricing measurement only: scripted reflex controllers, an RLS "
    "identification arm, a grid-tuned upper bound, and a privileged oracle compared on a "
    "vehicle-randomized obstacle family. Zero training; RL never run. No driver promotion, "
    "repair-success, gate-validity, paper, or self-ID capability claim."
)


# ----------------------------------------------------------------- controllers


def composed_action(obs: np.ndarray, v2cfg: dict, v4cfg: dict) -> np.ndarray:
    """v2 speed-floor base (tunable config) + v4 local hard-safety layer (tunable config).

    Mirrors m4.v4_v2_fallback_no_regression_hard_safety_direct_action exactly when
    (v2cfg, v4cfg) == (V2_POLICY_CONFIG, V4_POLICY_CONFIG); asserted at startup."""
    obs = np.asarray(obs, dtype=np.float32)
    action = np.asarray(speed_floor_aware_direct_action(obs, v2cfg), dtype=np.float32).copy()
    f = m4._hard_safety_features(obs, v4cfg)
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


def rls_cfgs(star: tuple[float, float, float], kb_hat: float, kd_hat: float) -> tuple[dict, dict]:
    """Frozen kappa map (prereg) applied on top of the fixed_star config."""
    v2, v4 = grid_cfgs(*star)
    mb = float(np.clip(1.0 / max(kb_hat, 1e-6), 0.5, 2.4))
    for gk in ("obstacle_brake", "edge_brake", "stability_brake"):
        v2["gains"][gk] *= mb
    for gk in ("local_obstacle_brake", "local_edge_brake"):
        v4["gains"][gk] *= mb
    mr = float(np.clip(1.0 / max(kb_hat, 1e-6), 1.0, 1.8))
    v2["thresholds"]["obstacle_relevance_distance_m"] *= mr
    v4["thresholds"]["obstacle_relevance_distance_m"] *= mr
    v4["thresholds"]["local_hard_safety_speed_mps"] *= float(np.clip(math.sqrt(max(kb_hat, 1e-6)), 0.7, 1.3))
    v2["gains"]["speed_floor_throttle_boost"] *= float(np.clip(1.0 / max(kd_hat, 1e-6), 0.5, 2.0))
    return v2, v4


# ----------------------------------------------------------------- vehicle RLS
# (machinery from scripts/feasibility_audit/belief_decomposition.py, reused verbatim)


class VehicleRLS:
    def __init__(self, prior_sigma_kappa: float = 0.30, r_noise_ax: float = 0.04):
        s = prior_sigma_kappa / MASS_NOM
        self.theta = np.array([1.0 / MASS_NOM, 1.0 / MASS_NOM])
        self.p = np.diag([s * s, s * s])
        self.r = r_noise_ax
        self.n_frames = 0

    def update_obs(self, obs: np.ndarray) -> None:
        vx = float(obs[0]) * 20.0
        ax = float(obs[3]) * 15.0
        fd_nom = float(obs[7]) * MAX_DRIVE
        fb_nom = float(obs[8]) * MAX_BRAKE
        steer = float(obs[5]) * 0.62
        ay = float(obs[4]) * 15.0
        if abs(steer) > 0.10 or abs(ay) > 1.5 or vx < 1.5:
            return
        if fd_nom < 250.0 and fb_nom < 250.0:
            return
        phi = np.array([fd_nom, -fb_nom])
        resist = 0.34 * vx * abs(vx) + 75.0 * math.tanh(vx)
        y = ax + resist / MASS_NOM
        denom = self.r + float(phi @ self.p @ phi)
        k = (self.p @ phi) / denom
        self.theta = self.theta + k * (y - float(phi @ self.theta))
        self.p = self.p - np.outer(k, phi @ self.p)
        self.n_frames += 1

    @property
    def kappas(self) -> tuple[float, float]:
        kd = float(np.clip(self.theta[0] * MASS_NOM, 0.4, 2.5))
        kb = float(np.clip(self.theta[1] * MASS_NOM, 0.4, 2.5))
        return kb, kd


def sample_vehicle(level: str, instance: int) -> dict[str, float]:
    if level == "S0":
        return {"mass": 1.0, "brake": 1.0, "drive": 1.0, "stiff": 1.0, "tau": 1.0}
    rng = np.random.default_rng([BASE, 11, LEVELS.index(level), instance])
    rg = LEVEL_RANGES[level]
    return {k: float(rng.uniform(*rg[k])) for k in ("mass", "brake", "drive", "stiff", "tau")}


def true_kappas(veh: dict[str, float]) -> tuple[float, float]:
    return veh["brake"] / veh["mass"], veh["drive"] / veh["mass"]


def familiarization_rls(level: str, instance: int, veh: dict[str, float]) -> dict[str, Any]:
    """5 s sub-limit prefix on an obstacle-free quasi-straight arc (R=600); RLS on the
    actor-visible stream. Gentle fixed-fraction pulses keep utilization sub-limit for
    every vehicle/mu in the domain (drive frac 0.10, brake frac 0.12)."""
    seed = 9_100_000 + LEVELS.index(level) * 1000 + instance * 10
    mu = float(np.random.default_rng([BASE, 21, LEVELS.index(level), instance]).uniform(*MU_DOMAIN))
    cfg = build_env_config({
        "max_steps": 270, "track_kind": "circle", "track_radius": 600.0, "track_width": 5.0,
        "speed_range": [9.0, 9.0], "history_length": 1, "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero", "friction_step": {"enabled": False},
        "obstacle": {"enabled": False},
        "randomization": {
            "mu_range": [mu, mu], "mass_scale_range": [veh["mass"]] * 2,
            "brake_scale_range": [veh["brake"]] * 2, "drive_scale_range": [veh["drive"]] * 2,
            "tire_stiffness_scale_range": [veh["stiff"]] * 2, "actuator_tau_scale_range": [veh["tau"]] * 2,
            "cg_shift_range": [0.0, 0.0], "inertia_scale_range": [1.0, 1.0]},
    })
    env = AutoDriftEnv(cfg)
    rls = VehicleRLS()
    v2f, v4f = V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG
    max_util = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        for t in range(250):  # 5 s
            obs_arr = np.asarray(obs, dtype=np.float64)
            rls.update_obs(obs_arr)
            steer = float(composed_action(obs_arr.astype(np.float32), v2f, v4f)[0])
            s_t = t * DT
            cycle = s_t % 2.5
            vx = obs_arr[0] * 20.0
            if 0.6 <= cycle < 1.2:
                action = [steer, -1.0, 2.0 * 0.12 - 1.0]  # gentle brake pulse
            elif 1.4 <= cycle < 2.2:
                thr = 0.10 if vx < 10.5 else 0.0
                action = [steer, 2.0 * thr - 1.0, -1.0]  # gentle drive pulse
            else:
                thr = float(np.clip(0.05 * (9.5 - vx), 0.0, 0.10))
                action = [steer, 2.0 * thr - 1.0, -1.0]
            obs, _, term, trunc, _ = env.step(np.asarray(action, dtype=np.float64))
            if t >= 25:  # skip the 0.5 s spawn transient (env-given, not commanded)
                forces = env.last_forces
                cap_r = 0.98 * env.params.mu * env.params.static_fzr
                max_util = max(max_util, math.hypot(forces.fx_rear, forces.fy_rear) / max(cap_r, 1.0))
            if term or trunc:
                break
    finally:
        env.close()
    kb_hat, kd_hat = rls.kappas
    kb_t, kd_t = true_kappas(veh)
    return {
        "kappa_b_hat": kb_hat, "kappa_d_hat": kd_hat,
        "kappa_b_true": kb_t, "kappa_d_true": kd_t,
        "kappa_b_abs_err": abs(kb_hat - kb_t), "kappa_d_abs_err": abs(kd_hat - kd_t),
        "rls_frames": rls.n_frames, "prefix_mu": mu, "max_rear_utilization": max_util,
    }


# ------------------------------------------------------------------ task rows


def row_env_config(surface: str, v: float, mu: float, s_arc: float, hw: float, veh: dict[str, float]):
    phi = s_arc / TRACK_R
    dt_comp = TRACK_R * math.sin(phi)
    c_comp = TRACK_R * (1.0 - math.cos(phi))
    if surface == "T_mid":
        reveal = {"perception_reveal_step": 34, "perception_reveal_distance": None}
    else:
        reveal = {"perception_reveal_step": 0, "perception_reveal_distance": 16.0}
    return build_env_config({
        "max_steps": 480, "track_kind": "circle", "track_radius": TRACK_R, "track_width": 5.0,
        "speed_range": [v, v], "history_length": 1, "include_privileged_params": False,
        "obstacle_relative_velocity_mode": "zero", "friction_step": {"enabled": False},
        "obstacle": {"enabled": True, "distance_range": [dt_comp, dt_comp],
                     "half_width_range": [hw, hw], "lateral_offset_range": [c_comp, c_comp],
                     "allowed_labels": ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"],
                     "max_sample_attempts": 50, "finish_on_pass": True, **reveal},
        "randomization": {
            "mu_range": [mu, mu], "mass_scale_range": [veh["mass"]] * 2,
            "brake_scale_range": [veh["brake"]] * 2, "drive_scale_range": [veh["drive"]] * 2,
            "tire_stiffness_scale_range": [veh["stiff"]] * 2, "actuator_tau_scale_range": [veh["tau"]] * 2,
            "cg_shift_range": [0.0, 0.0], "inertia_scale_range": [1.0, 1.0]},
    })


def capped_speed(v_target: float, mu: float) -> float:
    return min(v_target, 0.92 * math.sqrt(mu * GRAV * TRACK_R))


def adjusted_label(v: float, mu: float, d_eff: float, hw: float, veh: dict[str, float]) -> str:
    """Per-instance feasibility (prereg): scenarios.py model with reveal-bounded distance
    and actuator-authority-bounded braking; lateral terms mass-free (unchanged)."""
    a_eff = min(0.9 * mu * GRAV, MAX_BRAKE * veh["brake"] / (MASS_NOM * veh["mass"]))
    req = 0.9 + hw + 0.3
    t = d_eff / max(v, 1e-6)
    if v * v / (2.0 * max(a_eff, 1e-6)) <= d_eff - 0.3:
        return "aeb"
    if 0.5 * 0.42 * mu * GRAV * t * t >= req:
        return "aes"
    if 0.5 * 0.85 * mu * GRAV * t * t >= req:
        return "drift"
    return "unav"


def sample_rows(level: str, surface: str, instance: int, veh: dict[str, float],
                phase: str, n_rows: int) -> list[dict[str, Any]]:
    """Deterministic scan: candidate k admitted per prereg admission rules."""
    L, S, v_i = LEVELS.index(level), SURFACES.index(surface), instance
    tag = 31 if phase == "sel" else 41
    seed_base = (6_000_000 if phase == "sel" else 7_000_000) + L * 200_000 + S * 100_000 + v_i * 5_000
    rows = []
    k = 0
    while len(rows) < n_rows and k < 400:
        rng = np.random.default_rng([BASE, tag, L, S, v_i, k])
        mu = float(rng.uniform(*MU_DOMAIN))
        if surface == "T_mid":
            v = capped_speed(float(rng.uniform(8.0, 12.0)), mu)
            s_arc = float(rng.uniform(18.0, 32.0))
            hw = float(rng.uniform(0.55, 1.15))
            lab = classify_obstacle_scenario(v, mu, TRACK_R * math.sin(s_arc / TRACK_R), hw).label
            ok = lab == "aeb_feasible"
            il = ""
        else:
            v = capped_speed(float(rng.uniform(13.0, 22.0)), mu)
            s_arc = float(rng.uniform(20.0, 42.0))
            hw = float(rng.uniform(0.70, 1.40))
            lab = classify_obstacle_scenario(v, mu, TRACK_R * math.sin(s_arc / TRACK_R), hw).label
            il = adjusted_label(v, mu, 16.0, hw, veh)
            ok = lab in ("aeb_feasible", "aes_feasible") and il in ("aeb", "aes", "drift")
        if ok:
            rows.append({"eval_seed": seed_base + k * 13, "v": v, "mu": mu, "s_arc": s_arc,
                         "hw": hw, "label": lab, "instance_label": il, "scan_k": k})
        k += 1
    if len(rows) < n_rows:
        raise RuntimeError(f"admission scan exhausted: {level}/{surface}/inst{instance}/{phase} got {len(rows)}/{n_rows}")
    return rows


# -------------------------------------------------------------------- rollout


def light_rollout(env, controller: Callable[[int, np.ndarray], np.ndarray], seed: int,
                  collect: bool = False) -> dict[str, Any]:
    obs, info = env.reset(seed=seed)
    term = trunc = False
    t = 0
    actions = []
    reveal_step = None
    while not (term or trunc):
        if reveal_step is None and float(obs[44]) > 0.5:
            reveal_step = t
        a = controller(t, obs)
        if collect:
            actions.append(np.asarray(a, dtype=np.float64))
        obs, _r, term, trunc, info = env.step(a)
        t += 1
    bucket = outcome_bucket_from_info(info, terminated=term, truncated=trunc)
    return {"bucket": bucket, "steps": int(info.get("step", t)), "reveal_step": reveal_step,
            "termination_reason": str(info.get("termination_reason", "") or ""),
            "actions": actions}


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


def oracle_solve(env, seed: int, reveal_step: int, prefix_ctrl, rng: np.random.Generator,
                 quick: bool) -> dict[str, Any]:
    """Reveal-constrained privileged search with early stop on first success."""
    rollouts = 0

    def attempt(tail_fn) -> bool:
        nonlocal rollouts
        def ctrl(t, obs):
            if t < reveal_step:
                return prefix_ctrl(obs)
            return tail_fn(t - reveal_step)
        res = light_rollout(env, ctrl, seed)
        rollouts += 1
        return res["bucket"] == "success_obstacle_pass"

    # structured candidates (15)
    cands: list[tuple[str, Callable[[int], np.ndarray]]] = [
        ("full_brake", lambda rel: np.array([0.0, -1.0, 1.0]))]
    for st in (0.4, 0.7, 1.0, -0.4, -0.7, -1.0):
        cands.append((f"brake_steer_{st:+.1f}", lambda rel, st=st: np.array([st, -1.0, 1.0])))
    for st in (0.7, 1.0, -0.7, -1.0):
        cands.append((f"coast_steer_{st:+.1f}", lambda rel, st=st: np.array([st, -1.0, -1.0])))
    for st in (1.0, -1.0):
        for n in (10, 20):
            cands.append((f"swerve_{st:+.0f}_n{n}",
                          lambda rel, st=st, n=n: np.array([st, -1.0, 1.0]) if rel < n else np.array([0.0, -1.0, 1.0])))
    for name, fn in cands:
        if attempt(fn):
            return {"solved": True, "by": f"structured:{name}", "rollouts": rollouts}

    # CEM fallback over piecewise-constant segments
    n_seg, seg_len = (6, 8) if quick else (10, 8)
    pop, elites, iters = (8, 2, 2) if quick else (20, 5, 5)
    mean = np.tile(np.array([0.0, -1.0, 1.0]), (n_seg, 1))
    std = np.full_like(mean, 0.6)
    for it in range(iters):
        samples = np.clip(rng.normal(mean[None], std[None], size=(pop, n_seg, 3)), -1.0, 1.0)
        scored = []
        for i in range(pop):
            seg = samples[i]
            def tail(rel, seg=seg):
                return seg[min(rel // seg_len, n_seg - 1)]
            def ctrl(t, obs):
                if t < reveal_step:
                    return prefix_ctrl(obs)
                return tail(t - reveal_step)
            res = light_rollout(env, ctrl, seed)
            rollouts += 1
            if res["bucket"] == "success_obstacle_pass":
                return {"solved": True, "by": f"cem_iter{it}", "rollouts": rollouts}
            score = res["steps"]  # later failure = closer to surviving
            scored.append((score, i))
        scored.sort(key=lambda x: (-x[0], x[1]))
        elite = samples[[i for _s, i in scored[:elites]]]
        mean = elite.mean(axis=0)
        std = np.maximum(elite.std(axis=0), 0.15)
    return {"solved": False, "by": None, "rollouts": rollouts}


# ----------------------------------------------------------------- statistics


def wilson_ci(p: float, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    den = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]


def newcombe_diff_ci(p1: float, n1: int, p2: float, n2: int) -> list[float]:
    l1, u1 = wilson_ci(p1, n1)
    l2, u2 = wilson_ci(p2, n2)
    d = p1 - p2
    return [round(d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), 4),
            round(d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2), 4)]


def paired_bootstrap_ci(a: np.ndarray, b: np.ndarray, rng: np.random.Generator,
                        n_boot: int = 2000) -> list[float]:
    n = len(a)
    if n == 0:
        return [float("nan"), float("nan")]
    idx = rng.integers(0, n, size=(n_boot, n))
    diffs = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


# ------------------------------------------------------------------- main run


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu"])
    args = ap.parse_args()
    quick = args.quick

    t_start = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    progress_path = RUN_DIR / ("progress_quick.json" if quick else "progress.json")
    rows_csv = RUN_DIR / ("episode_rows_quick.csv" if quick else "episode_rows.csv")
    results_json = RESULTS_JSON if not quick else RESULTS_JSON.with_name("c5_reflex_degradation_quick.json")

    prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    n_inst = 2 if quick else 12
    n_sel = 2 if quick else 6
    n_val = {"T_mid": 3 if quick else 10, "T_limit": 3 if quick else 12}
    levels = ["S0", "S2"] if quick else LEVELS

    def progress(stage: str, **kw):
        progress_path.write_text(json.dumps(
            {"stage": stage, "elapsed_s": round(time.time() - t_start, 1), **kw}, indent=2), encoding="utf-8")
        print(f"[{time.time() - t_start:7.1f}s] {stage} {kw}", flush=True)

    # ---- gate 1: composed == canonical v4
    rng0 = np.random.default_rng(0)
    for _ in range(200):
        o = rng0.normal(0, 0.3, 72).astype(np.float32)
        a1 = composed_action(o, V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG)
        a2 = m4.v4_v2_fallback_no_regression_hard_safety_direct_action(o, m4.V4_POLICY_CONFIG)
        assert np.array_equal(a1, a2), "composed action != canonical v4"
    progress("gate_composed_equals_v4_pass")

    # ---- vehicles + RLS prefixes
    vehicles: dict[tuple[str, int], dict] = {}
    rls_table: dict[tuple[str, int], dict] = {}
    for level in levels:
        for v_i in range(n_inst):
            veh = sample_vehicle(level, v_i)
            vehicles[(level, v_i)] = veh
            rls_table[(level, v_i)] = familiarization_rls(level, v_i, veh)
            assert rls_table[(level, v_i)]["max_rear_utilization"] < 0.6, \
                f"RLS prefix utilization breach {level}/{v_i}: {rls_table[(level, v_i)]}"
    progress("rls_prefixes_done", n=len(rls_table),
             med_kb_err=round(float(np.median([r["kappa_b_abs_err"] for r in rls_table.values()])), 4))

    # ---- row sampling (selection + validation) and seed disjointness
    sel_rows: dict[tuple[str, str, int], list[dict]] = {}
    val_rows: dict[tuple[str, str, int], list[dict]] = {}
    for level in levels:
        for surface in SURFACES:
            for v_i in range(n_inst):
                veh = vehicles[(level, v_i)]
                sel_rows[(level, surface, v_i)] = sample_rows(level, surface, v_i, veh, "sel", n_sel)
                val_rows[(level, surface, v_i)] = sample_rows(level, surface, v_i, veh, "val", n_val[surface])
    all_sel = {r["eval_seed"] for rows in sel_rows.values() for r in rows}
    all_val = {r["eval_seed"] for rows in val_rows.values() for r in rows}
    assert not (all_sel & all_val), "selection/validation seed overlap"
    progress("rows_sampled", sel=len(all_sel), val=len(all_val))

    env_cache: dict[tuple, AutoDriftEnv] = {}

    def env_for(surface: str, row: dict, level: str, v_i: int) -> AutoDriftEnv:
        key = (level, surface, v_i, row["eval_seed"])
        if key not in env_cache:
            if len(env_cache) > 600:
                for e in env_cache.values():
                    e.close()
                env_cache.clear()
            env_cache[key] = AutoDriftEnv(
                row_env_config(surface, row["v"], row["mu"], row["s_arc"], row["hw"], vehicles[(level, v_i)]))
        return env_cache[key]

    # ---- gate 3: light rollout vs run_episode_with_policy on sampled rows
    class _Policy:
        def __init__(self, v2c, v4c):
            self.v2c, self.v4c = v2c, v4c
        def reset(self):
            pass
        def act(self, observation, info):
            return composed_action(observation, self.v2c, self.v4c)

    gate_rows = [(lv, sf, vi, r) for (lv, sf, vi), rs in list(val_rows.items())[::max(1, len(val_rows) // 12)]
                 for r in rs[:1]][:12]
    for lv, sf, vi, r in gate_rows:
        env = env_for(sf, r, lv, vi)
        lr = light_rollout(env, lambda t, o: composed_action(o, V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG), r["eval_seed"])
        ep = run_episode_with_policy(env, _Policy(V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG), "gate", r["eval_seed"])
        ok = (ep["outcome_bucket"] == lr["bucket"]) and (int(ep["steps"]) == lr["steps"])
        assert ok, f"light rollout mismatch on {lv}/{sf}/{vi}/{r['eval_seed']}: {lr['bucket']} vs {ep['outcome_bucket']}"
    progress("gate_rollout_semantics_pass", checked=len(gate_rows))

    # ---- selection sweep: 27 grid configs on selection rows
    grid_cfg_cache = [grid_cfgs(*g) for g in GRID]
    sel_stats: dict[tuple[str, str, int], list[dict]] = {}
    n_sel_eps = 0
    for (level, surface, v_i), rows in sel_rows.items():
        per_cfg = []
        for gi, (v2c, v4c) in enumerate(grid_cfg_cache):
            succ = 0
            hard = 0
            for r in rows:
                env = env_for(surface, r, level, v_i)
                res = light_rollout(env, lambda t, o: composed_action(o, v2c, v4c), r["eval_seed"])
                n_sel_eps += 1
                fm = failure_mode(res["bucket"], res["termination_reason"])
                succ += fm == "success"
                hard += fm in ("collision", "offtrack")
            per_cfg.append({"grid_index": gi, "grid": GRID[gi], "sel_success": succ, "sel_hard_fail": hard})
        sel_stats[(level, surface, v_i)] = per_cfg
    progress("selection_sweep_done", episodes=n_sel_eps)

    # ---- fixed_star: pooled S0 selection (both surfaces)
    pool = np.zeros(len(GRID))
    pool_hard = np.zeros(len(GRID))
    s0 = "S0" if "S0" in levels else levels[0]
    for surface in SURFACES:
        for v_i in range(n_inst):
            for c in sel_stats[(s0, surface, v_i)]:
                pool[c["grid_index"]] += c["sel_success"]
                pool_hard[c["grid_index"]] += c["sel_hard_fail"]

    def grid_rank_key(gi: int, succ: float, hard: float) -> tuple:
        dist = sum(1 for m in GRID[gi] if m != 1.0)
        return (-succ, hard, dist, gi)

    star_index = min(range(len(GRID)), key=lambda gi: grid_rank_key(gi, pool[gi], pool_hard[gi]))
    star = GRID[star_index]
    star_cfg = grid_cfgs(*star)
    progress("fixed_star_selected", grid=star, sel_success=int(pool[star_index]),
             out_of=int(n_inst * n_sel * 2))

    # ---- pertuned winners per (level, surface, instance)
    pertuned_choice: dict[tuple[str, str, int], int] = {}
    for key, per_cfg in sel_stats.items():
        def kf(c):
            gi = c["grid_index"]
            dist_star = sum(1 for a, b in zip(GRID[gi], star) if a != b)
            return (-c["sel_success"], c["sel_hard_fail"], dist_star, gi)
        pertuned_choice[key] = min(per_cfg, key=kf)["grid_index"]

    # ---- validation
    incumbent_cfg = (V2_POLICY_CONFIG, m4.V4_POLICY_CONFIG)
    episode_rows: list[dict] = []
    n_val_eps = 0
    n_oracle_rollouts = 0
    cell_keys = [(lv, sf) for lv in levels for sf in SURFACES]
    for ci, (level, surface) in enumerate(cell_keys):
        for v_i in range(n_inst):
            veh = vehicles[(level, v_i)]
            rinfo = rls_table[(level, v_i)]
            rls_cfg = rls_cfgs(star, rinfo["kappa_b_hat"], rinfo["kappa_d_hat"])
            pt_cfg = grid_cfg_cache[pertuned_choice[(level, surface, v_i)]]
            for r in val_rows[(level, surface, v_i)]:
                env = env_for(surface, r, level, v_i)
                arm_results = {}
                star_trace = None
                for arm, (v2c, v4c) in (("fixed_v4_incumbent", incumbent_cfg), ("fixed_star", star_cfg),
                                        ("v4_rls", rls_cfg), ("v4_pertuned", pt_cfg)):
                    res = light_rollout(env, lambda t, o: composed_action(o, v2c, v4c), r["eval_seed"],
                                        collect=False)
                    n_val_eps += 1
                    arm_results[arm] = res
                    if arm == "fixed_star":
                        star_trace = res
                reveal = star_trace["reveal_step"]
                reveal = 0 if reveal is None else int(reveal)
                orc = oracle_solve(
                    env, r["eval_seed"], reveal,
                    lambda o: composed_action(o, star_cfg[0], star_cfg[1]),
                    np.random.default_rng([BASE, 51, LEVELS.index(level), SURFACES.index(surface), v_i, r["scan_k"]]),
                    quick)
                n_oracle_rollouts += orc["rollouts"]
                base_row = {
                    "level": level, "surface": surface, "instance": v_i, "eval_seed": r["eval_seed"],
                    "v": round(r["v"], 3), "mu": round(r["mu"], 4), "s_arc": round(r["s_arc"], 2),
                    "hw": round(r["hw"], 3), "gen_label": r["label"], "instance_label": r["instance_label"],
                    "mass": round(veh["mass"], 4), "brake": round(veh["brake"], 4), "drive": round(veh["drive"], 4),
                    "stiff": round(veh["stiff"], 4), "tau": round(veh["tau"], 4),
                    "kappa_b_hat": round(rinfo["kappa_b_hat"], 4), "kappa_d_hat": round(rinfo["kappa_d_hat"], 4),
                    "pertuned_grid": str(GRID[pertuned_choice[(level, surface, v_i)]]),
                    "reveal_step": reveal,
                    "oracle_solved": orc["solved"], "oracle_by": orc["by"] or "",
                    "oracle_rollouts": orc["rollouts"],
                }
                for arm, res in arm_results.items():
                    base_row[f"{arm}_outcome"] = failure_mode(res["bucket"], res["termination_reason"])
                    base_row[f"{arm}_steps"] = res["steps"]
                episode_rows.append(base_row)
        progress("validation_cell_done", cell=f"{level}/{surface}", done=ci + 1, total=len(cell_keys),
                 val_eps=n_val_eps, oracle_rollouts=n_oracle_rollouts)

    for e in env_cache.values():
        e.close()

    # ---- write episode rows CSV
    import csv
    with rows_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(episode_rows[0].keys()))
        w.writeheader()
        w.writerows(episode_rows)

    # ---- aggregation
    ARMS = ["fixed_v4_incumbent", "fixed_star", "v4_rls", "v4_pertuned"]
    FAIL_MODES = ["success", "collision", "offtrack", "speed_too_low", "timeout_other"]
    cells_out = {}
    rng_boot = np.random.default_rng([BASE, 88])
    for level in levels:
        for surface in SURFACES:
            rows = [r for r in episode_rows if r["level"] == level and r["surface"] == surface]
            filt = [r for r in rows if r["oracle_solved"]]
            out: dict[str, Any] = {
                "n_rows_unfiltered": len(rows), "n_rows_oracle_solved": len(filt),
                "oracle_solvability": round(sum(r["oracle_solved"] for r in rows) / max(len(rows), 1), 4),
            }
            for tag, sub in (("filtered", filt), ("unfiltered", rows)):
                arms_block = {}
                for arm in ARMS:
                    n = len(sub)
                    p = sum(1 for r in sub if r[f"{arm}_outcome"] == "success") / max(n, 1)
                    arms_block[arm] = {
                        "success": round(p, 4), "n": n, "wilson_ci95": wilson_ci(p, n),
                        "failure_modes": {m: sum(1 for r in sub if r[f"{arm}_outcome"] == m) for m in FAIL_MODES},
                    }
                out[tag] = arms_block
            sub = filt
            n = len(sub)
            vec = {arm: np.array([1.0 if r[f"{arm}_outcome"] == "success" else 0.0 for r in sub]) for arm in ARMS}
            p = {arm: float(vec[arm].mean()) if n else float("nan") for arm in ARMS}
            out["readouts_filtered"] = {
                "primary_prize_pertuned_minus_fixed_star": {
                    "value": round(p["v4_pertuned"] - p["fixed_star"], 4),
                    "paired_bootstrap_ci95": paired_bootstrap_ci(vec["v4_pertuned"], vec["fixed_star"], rng_boot),
                    "newcombe_ci95": newcombe_diff_ci(p["v4_pertuned"], n, p["fixed_star"], n),
                },
                "classical_residual_pertuned_minus_rls": {
                    "value": round(p["v4_pertuned"] - p["v4_rls"], 4),
                    "paired_bootstrap_ci95": paired_bootstrap_ci(vec["v4_pertuned"], vec["v4_rls"], rng_boot),
                    "newcombe_ci95": newcombe_diff_ci(p["v4_pertuned"], n, p["v4_rls"], n),
                },
                "rls_recovery_rls_minus_fixed_star": {
                    "value": round(p["v4_rls"] - p["fixed_star"], 4),
                    "paired_bootstrap_ci95": paired_bootstrap_ci(vec["v4_rls"], vec["fixed_star"], rng_boot),
                },
                "secondary_incumbent_prize_pertuned_minus_incumbent": {
                    "value": round(p["v4_pertuned"] - p["fixed_v4_incumbent"], 4),
                    "paired_bootstrap_ci95": paired_bootstrap_ci(vec["v4_pertuned"], vec["fixed_v4_incumbent"], rng_boot),
                },
            }
            cells_out[f"{level}/{surface}"] = out

    # ---- C5 decision (prereg rule)
    qualifying = []
    for cell, out in cells_out.items():
        ro = out["readouts_filtered"]
        prize = ro["primary_prize_pertuned_minus_fixed_star"]
        resid = ro["classical_residual_pertuned_minus_rls"]
        if (prize["value"] >= 0.15 and prize["paired_bootstrap_ci95"][0] > 0.0
                and resid["value"] >= 0.08):
            qualifying.append(cell)
    c5_supported = len(qualifying) >= 2

    pertuned_grid_hist: dict[str, int] = {}
    for key, gi in pertuned_choice.items():
        pertuned_grid_hist[str(GRID[gi])] = pertuned_grid_hist.get(str(GRID[gi]), 0) + 1

    payload = {
        "protocol": "c5_reflex_degradation",
        "generated_by": "scripts/feasibility_audit/c5_reflex_degradation.py",
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration_echo": {"file": str(PREREG), "decision_rule": prereg["preregistered_readouts"]["c5_decision_rule"]},
        "seed_base": BASE,
        "levels": levels, "surfaces": SURFACES, "instances_per_level": n_inst,
        "sel_rows_per_instance": n_sel, "val_rows_per_instance": n_val,
        "fixed_star": {"grid": star, "grid_index": star_index,
                       "pooled_s0_sel_success": int(pool[star_index]),
                       "pooled_s0_sel_n": int(n_inst * n_sel * 2),
                       "identity_pooled_s0_sel_success": int(pool[IDENTITY_INDEX])},
        "pertuned_grid_histogram": pertuned_grid_hist,
        "vehicles": {f"{lv}/{vi}": vehicles[(lv, vi)] for (lv, vi) in vehicles},
        "rls_identification": {
            f"{lv}/{vi}": {k: round(v, 4) if isinstance(v, float) else v for k, v in rls_table[(lv, vi)].items()}
            for (lv, vi) in rls_table},
        "rls_kappa_err_summary": {
            "kappa_b_abs_err_median": round(float(np.median([r["kappa_b_abs_err"] for r in rls_table.values()])), 4),
            "kappa_b_abs_err_p90": round(float(np.percentile([r["kappa_b_abs_err"] for r in rls_table.values()], 90)), 4),
            "kappa_d_abs_err_median": round(float(np.median([r["kappa_d_abs_err"] for r in rls_table.values()])), 4),
        },
        "cells": cells_out,
        "c5_decision": {"qualifying_cells": qualifying, "c5_supported": c5_supported,
                        "rule": ">=2 cells with primary_prize >= 0.15, paired CI95 lower > 0, classical_residual >= 0.08"},
        "budget": {"selection_episodes": n_sel_eps, "validation_episodes": n_val_eps,
                   "oracle_rollouts": n_oracle_rollouts,
                   "rls_prefixes": len(rls_table), "elapsed_s": round(time.time() - t_start, 1)},
        "episode_rows_csv": str(rows_csv),
    }
    results_json.parent.mkdir(parents=True, exist_ok=True)
    results_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    progress("done", results=str(results_json), elapsed_s=round(time.time() - t_start, 1),
             c5_supported=c5_supported, qualifying=qualifying)


if __name__ == "__main__":
    main()
