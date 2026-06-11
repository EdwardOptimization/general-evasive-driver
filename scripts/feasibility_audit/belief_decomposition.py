"""Heterogeneous-belief decomposition: vehicle knowledge vs road-surface knowledge.

User mechanism (production-AD background): two neglected information sources in
real driving -- (a) seeing the vehicle class gives a strong VEHICLE-parameter
prior before the first meter; (b) a few seconds of ordinary sub-limit driving
identifies vehicle parameters (mass-normalized brake/drive authority, steering
stiffness, actuator lag) WITHOUT identifying mu, because the sub-limit tire
response sits in the tanh linear region where capacity (mu) cancels.

Three measurements (all scripted controllers, zero training; RLS = recursive
least squares, not training):

  M1  Sub-limit mu-leakage curve on dynamics.py: fixed command sequences at
      tire-utilization levels {0.2,0.4,0.6,0.8,0.95}, mu swept; trajectory
      divergence / Gaussian-observer mu-posterior width quantifies how
      aggressive driving must be before mu leaks at all. Same data: RLS
      identifiability of the vehicle parameters (kappa_b, kappa_d, stiffness
      scale, actuator tau) -- identifiable sub-limit while mu is not.

  M2  Four-tier oracle prize decomposition on the degraded tight-window family
      (reveal 9.5 m, matched anchor: every arm runs on the same degraded
      stream), with per-episode VEHICLE randomization added to the B2K2 family
      (mass/brake/drive/stiffness/actuator-tau scales; cg+inertia held nominal):
        T0 knows nothing  = best belief-free arm (seeker w/ nominal vehicle
                            belief, fixed plans) -- the floor;
        T1 knows vehicle  = same seeker family with TRUE vehicle authority
                            ratios fed in (its vehicle-RLS off), mu still
                            unknown (domain-floor ramp + degraded detection);
        T2 knows mu       = per-mu oracle ramp with nominal vehicle belief
                            (+ optional in-episode vehicle RLS on the degraded
                            stream, selection decides);
        T3 knows both     = matched per-mu oracle with true vehicle belief.
      prize(T3-T0) = vehicle(T1-T0) + surface(T2-T0) + interaction, per cell,
      12 mu points x 10 validation seeds (120 episodes/arm/cell), Wilson CIs +
      episode-paired bootstrap CIs on the decomposition terms.

  M3  Familiarization-period value curve: a 5 s / 15 s sub-limit ordinary
      driving prefix (gentle throttle/brake/steer, utilization < 0.5, no
      hazard) on the SAME vehicle + degradation cell lets the seeker's vehicle
      RLS converge before the task; prefix length -> (RLS vehicle-parameter
      error, task success). How close does zero-risk familiarization push T0
      toward T1?

Physics reduction used throughout (derived from dynamics.py, stated in the
doc): this controller family consumes vehicle knowledge ONLY through the two
mass-normalized authority ratios kappa_b = brake_scale/mass_scale and
kappa_d = drive_scale/mass_scale. Capacity deceleration mu*0.98*g*lf/wb is
mass-free, and mu_hat = realized_force/(0.98*Fzr) is invariant to a consistent
mass belief (mass cancels), so "knowing the vehicle" = knowing kappa_b/kappa_d
(stiffness/tau are randomized in the env but unused by this controller class;
declared). The RLS therefore estimates kappa_b, kappa_d.

Controller/task machinery is REUSED from ramp_policy_voi_regime.py and
degraded_regime_final.py (loaded as modules); belief injection is implemented
as (i) scaling the detector's actuator-state channels by the believed
authority ratios and (ii) remapping commanded brake/throttle fractions by
1/kappa_believed (exact: with true belief the oracle realizes exact capacity
braking; with nominal belief on a randomized vehicle, detection acquires a
bias floor no averaging removes and braking force is mis-scaled).

Hard constraints: pure CPU numpy, zero training, deterministic seeds, new
files only, no git operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/belief_decomposition.py
    PYTHONPATH=src python scripts/feasibility_audit/belief_decomposition.py --quick
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO = Path(__file__).resolve().parents[2]
REGIME_SCRIPT = REPO / "scripts/feasibility_audit/ramp_policy_voi_regime.py"
DEGRADED_SCRIPT = REPO / "scripts/feasibility_audit/degraded_regime_final.py"
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
SLIP_SCRIPT = REPO / "scripts/feasibility_audit/slip_onset_detectability.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/belief_decomposition.json"
RUN_DIR = REPO / "runs/feasibility_audit/belief_decomposition"

SEED_BASE = 20260622  # fresh stream (regime=20260618, degraded=20260620)
DT = 0.02
REVEAL = 9.5
# (delay_steps, noise_std): clean replication-context cell + the 4 required
CELLS_DEFAULT = ((0, 0.0), (5, 0.0), (12, 0.0), (0, 0.05), (5, 0.05))

# vehicle randomization (subset of dynamics.RandomizationConfig; cg shift and
# inertia held nominal -- they do not enter this controller family's math)
VEH_RANGES = {
    "mass_scale": (0.85, 1.20),
    "brake_scale": (0.80, 1.15),
    "drive_scale": (0.80, 1.15),
    "tire_stiffness_scale": (0.65, 1.35),
    "actuator_tau_scale": (0.75, 1.75),
}

# nominal constants (mirror reg)
MASS, GRAV, LF, LR, WB = 1450.0, 9.81, 1.35, 1.45, 2.80
FZR = MASS * GRAV * LF / WB
FZF = MASS * GRAV * LR / WB
MAX_BRAKE, MAX_DRIVE = 6000.0, 8200.0
TIRE_CAP = 0.98
CF_NOM, CR_NOM = 95000.0, 110000.0
DRAG_COEFF, ROLLING = 0.34, 75.0

# M1 protocol
M1_UTILIZATIONS = (0.2, 0.4, 0.6, 0.8, 0.95)
M1_PAIRS = ((0.3, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.1), (0.3, 1.1))
M1_V0 = 12.0
M1_STEPS = 300  # 6 s
M1_NOISE_STD = 0.05  # normalized-channel sigma (matches the M3214 noise cell)
M1_OBS_SCALES = np.array([20.0, 12.0, 2.5, 15.0, 15.0])  # vx,vy,yaw,ax,ay
M1_POSTERIOR_MU_TRUE = 0.7
M1_POSTERIOR_GRID = np.round(np.arange(0.25, 1.1501, 0.025), 4)
M1_RLS_VEH_SEEDS = 6
M1_RLS_MUS = (0.4, 0.7, 1.0)  # mu-invariance check of vehicle estimates

# M2 grids (trimmed, justified by the clean/degraded winners)
SEEKER_RATES = (6000.0, 20000.0)
SEEKER_DELTAS = (0.06, 0.15)
SEEKER_DVS = (0.0, 0.75)
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)
SMOOTH_WINDOWS_NOISE = (1, 12, 25)
CALIB_MUS = (0.5, 0.9)
CALIB_VEH_SEEDS = 3
CALIB_STEPS = 230
CALIB_FRAC = 0.55
TAU_SAFETY, TAU_FLOOR = 1.2, 0.08

# M3 protocol
PREFIX_SECONDS = (5.0, 15.0)
PREFIX_UTIL_CAP = 0.45  # of the true-mu rear capacity (harness-only cap, as in tau calibration)

CLAIM_BOUNDARY = (
    "Feasibility-audit policy-family measurement only: scripted threshold-seeking/oracle ramp "
    "controllers (ramp_policy_voi_regime.py family) with belief-injection wrappers are rolled "
    "out on a VEHICLE-RANDOMIZED B2K2_final variant (reveal 9.5 m) under the M3214 observation-"
    "degradation wrapper, plus pure-dynamics sub-limit leakage measurements. No driver "
    "promotion, training, repair-success, gate-validity, paper, or self-ID capability claim."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------- vehicle belief


def sample_vehicle_scales(seed: int) -> dict[str, float]:
    rng = np.random.default_rng([SEED_BASE, 555, int(seed)])
    return {k: float(rng.uniform(*rng_range)) for k, rng_range in VEH_RANGES.items()}


def true_kappas(scales: dict[str, float]) -> tuple[float, float]:
    return (scales["brake_scale"] / scales["mass_scale"],
            scales["drive_scale"] / scales["mass_scale"])


class Belief:
    """Mass-normalized authority-ratio belief consumed by the controllers."""

    def __init__(self, kb: float = 1.0, kd: float = 1.0):
        self.kb, self.kd = float(kb), float(kd)

    def set(self, kb: float, kd: float) -> None:
        self.kb, self.kd = float(kb), float(kd)


class VehicleRLS:
    """2-parameter recursive least squares on the longitudinal channel:
        y = ax + resist(vx)/m_nom  ~=  theta1 * Fd_nom - theta2 * Fb_nom
    with Fd_nom = obs7*MAX_DRIVE, Fb_nom = obs8*MAX_BRAKE (nominal-frame
    regressors; truth theta1 = drive_scale/mass, theta2 = brake_scale/mass).
    kappa_d = theta1*m_nom, kappa_b = theta2*m_nom. Bayesian blend with the
    kappa=1 nominal prior via the P0 ridge. Frames gated to near-straight
    low-lateral motion; all channels read from the SAME (degraded) stream, so
    the regression stays time-consistent under pure delay."""

    def __init__(self, prior_sigma_kappa: float = 0.30, r_noise_ax: float = 0.36):
        s = prior_sigma_kappa / MASS
        self.theta = np.array([1.0 / MASS, 1.0 / MASS])
        self.p = np.diag([s * s, s * s])
        self.r = r_noise_ax
        self.n_frames = 0

    def update_frame(self, vx: float, ax: float, fd_nom: float, fb_nom: float,
                     steer: float, ay: float) -> None:
        if abs(steer) > 0.10 or abs(ay) > 1.5 or vx < 1.5:
            return
        if fd_nom < 250.0 and fb_nom < 250.0:
            return
        phi = np.array([fd_nom, -fb_nom])
        resist = DRAG_COEFF * vx * abs(vx) + ROLLING * math.tanh(vx)
        y = ax + resist / MASS
        denom = self.r + float(phi @ self.p @ phi)
        k = (self.p @ phi) / denom
        self.theta = self.theta + k * (y - float(phi @ self.theta))
        self.p = self.p - np.outer(k, phi @ self.p)
        self.n_frames += 1

    def update_obs(self, obs: np.ndarray) -> None:
        self.update_frame(
            vx=float(obs[0]) * 20.0,
            ax=float(obs[3]) * 15.0,
            fd_nom=float(obs[7]) * MAX_DRIVE,
            fb_nom=float(obs[8]) * MAX_BRAKE,
            steer=float(obs[5]) * 0.62,
            ay=float(obs[4]) * 15.0,
        )

    @property
    def kappas(self) -> tuple[float, float]:
        kd = float(np.clip(self.theta[0] * MASS, 0.4, 2.5))
        kb = float(np.clip(self.theta[1] * MASS, 0.4, 2.5))
        return kb, kd


# ------------------------------------------ M1: pure-dynamics leakage + RLS


def m1_make_model(mu: float, scales: dict[str, float] | None = None):
    from autodrift.dynamics import SingleTrackDriftModel, VehicleParams

    base = VehicleParams()
    if scales is None:
        params = dataclasses.replace(base, mu=mu)
    else:
        params = dataclasses.replace(
            base,
            mu=mu,
            mass=base.mass * scales["mass_scale"],
            max_drive_force=base.max_drive_force * scales["drive_scale"],
            max_brake_force=base.max_brake_force * scales["brake_scale"],
            cf=base.cf * scales["tire_stiffness_scale"],
            cr=base.cr * scales["tire_stiffness_scale"],
            drive_tau=base.drive_tau * scales["actuator_tau_scale"],
            steer_tau=base.steer_tau * scales["actuator_tau_scale"],
        )
    return SingleTrackDriftModel(params)


def m1_body_acc(model, state, forces) -> tuple[float, float]:
    p = model.params
    drag = p.drag_coeff * state.vx * abs(state.vx)
    rolling = p.rolling_resistance * math.tanh(state.vx)
    fx_body = forces.fx_rear - forces.fy_front * math.sin(state.steer) - drag - rolling
    fy_body = forces.fy_front * math.cos(state.steer) + forces.fy_rear
    return (fx_body / p.mass + state.yaw_rate * state.vy,
            fy_body / p.mass - state.yaw_rate * state.vx)


def m1_commands(u: float, mu_anchor: float) -> list[tuple[float, float, float]]:
    """(steer_rad, drive_force_N, brake_force_N) per step; pure segments:
    settle / drive pulse / coast / brake pulse / coast / steer sine / coast.
    Forces sized to u x the anchor-mu capacity (nominal vehicle frame);
    brake additionally capped by the 6000 N actuator."""
    f_rear = u * TIRE_CAP * mu_anchor * FZR
    f_drive = min(f_rear, MAX_DRIVE)
    f_brake = min(f_rear, MAX_BRAKE)
    cap_f = mu_anchor * FZF
    alpha = (cap_f / CF_NOM) * math.atanh(min(u, 0.97))
    cmds = []
    for t in range(M1_STEPS):
        s = t * DT
        steer, fd, fb = 0.0, 0.0, 0.0
        if 0.5 <= s < 1.5:
            fd = f_drive
        elif 2.0 <= s < 3.0:
            fb = f_brake
        elif 3.5 <= s < 5.5:
            steer = alpha * math.sin(2.0 * math.pi * (s - 3.5) / 2.0)
        cmds.append((steer, fd, fb))
    return cmds


def m1_rollout(model, cmds, collect_actuator: bool = False):
    """Open-loop rollout; returns T x 5 observable array [vx,vy,yaw,ax,ay]
    (+ optionally actuator fractions / commands for RLS & tau fitting)."""
    from autodrift.dynamics import VehicleState

    p = model.params
    state = VehicleState(x=0.0, y=0.0, psi=0.0, vx=M1_V0, vy=0.0, yaw_rate=0.0)
    rows, extra = [], []
    for steer, fd, fb in cmds:
        a0 = float(np.clip(steer / p.max_steer, -1.0, 1.0))
        thr01 = float(np.clip(fd / p.max_drive_force, 0.0, 1.0))
        brk01 = float(np.clip(fb / p.max_brake_force, 0.0, 1.0))
        action = np.array([a0, 2.0 * thr01 - 1.0, 2.0 * brk01 - 1.0])
        state, forces = model.step(state, action, DT)
        ax, ay = m1_body_acc(model, state, forces)
        rows.append([state.vx, state.vy, state.yaw_rate, ax, ay])
        if collect_actuator:
            fd_frac = max(state.drive_force, 0.0) / p.max_drive_force
            fb_frac = max(-state.drive_force, 0.0) / p.max_brake_force
            extra.append([fd_frac, fb_frac, thr01, brk01, state.steer,
                          forces.fy_front, forces.fy_rear,
                          forces.alpha_front, forces.alpha_rear])
    traj = np.asarray(rows)
    return (traj, np.asarray(extra)) if collect_actuator else traj


def m1_divergence(t1: np.ndarray, t2: np.ndarray) -> dict[str, float]:
    d = np.abs(t1 - t2)
    sigma = M1_NOISE_STD * M1_OBS_SCALES
    z = (t1 - t2) / sigma
    return {
        "max_dvx_mps": float(d[:, 0].max()),
        "max_dyaw_radps": float(d[:, 2].max()),
        "max_dax_mps2": float(d[:, 3].max()),
        "max_day_mps2": float(d[:, 4].max()),
        "seq_discriminability_d": float(np.sqrt(np.sum(z * z))),
        "per_frame_peak_snr": float(np.max(np.abs(z))),
    }


def m1_leakage() -> dict[str, Any]:
    out_pairs = []
    cache: dict[tuple[float, float, float], np.ndarray] = {}

    def traj_for(mu: float, u: float, anchor: float) -> np.ndarray:
        key = (round(mu, 4), u, round(anchor, 4))
        if key not in cache:
            cache[key] = m1_rollout(m1_make_model(mu), m1_commands(u, anchor))
        return cache[key]

    for mu1, mu2 in M1_PAIRS:
        anchor = min(mu1, mu2)  # neither vehicle saturates for u < 1
        for u in M1_UTILIZATIONS:
            div = m1_divergence(traj_for(mu1, u, anchor), traj_for(mu2, u, anchor))
            out_pairs.append({"mu_pair": [mu1, mu2], "utilization": u,
                              "anchor_mu": anchor, **div})
    # Gaussian-observer posterior over mu at mu*=0.7 (expected log-likelihood;
    # deterministic dynamics, noise model = the M3214 noise-0.05 cell)
    posterior = []
    sigma = M1_NOISE_STD * M1_OBS_SCALES
    prior_std = float(np.std(M1_POSTERIOR_GRID))
    for u in M1_UTILIZATIONS:
        ref = traj_for(M1_POSTERIOR_MU_TRUE, u, M1_POSTERIOR_MU_TRUE)
        logw = []
        for mu in M1_POSTERIOR_GRID:
            t = traj_for(float(mu), u, M1_POSTERIOR_MU_TRUE)
            z = (t - ref) / sigma
            logw.append(-0.5 * float(np.sum(z * z)))
        logw = np.asarray(logw)
        w = np.exp(logw - logw.max())
        w /= w.sum()
        mean = float(np.sum(w * M1_POSTERIOR_GRID))
        std = float(np.sqrt(np.sum(w * (M1_POSTERIOR_GRID - mean) ** 2)))
        posterior.append({"utilization": u, "mu_true": M1_POSTERIOR_MU_TRUE,
                          "posterior_mean": round(mean, 4),
                          "posterior_std": round(std, 4),
                          "prior_std": round(prior_std, 4),
                          "posterior_to_prior_std_ratio": round(std / prior_std, 4)})
    return {"pairs": out_pairs, "posterior_mu": posterior,
            "noise_model": f"iid Gaussian, std {M1_NOISE_STD} on normalized channels "
                           f"(physical sigma {list(np.round(M1_NOISE_STD * M1_OBS_SCALES, 3))} "
                           "on [vx,vy,yaw_rate,ax,ay])"}


def m1_fit_tau(extra: np.ndarray) -> float:
    """Grid-fit the drive actuator lag on drive-pulse frames in fraction space
    (scale-free: obs7 and thr01 share the unknown drive_scale denominator)."""
    obs7, thr01 = extra[:, 0], extra[:, 2]
    best_tau, best_err = None, np.inf
    for tau in np.arange(0.05, 0.165, 0.005):
        pred, f = [], 0.0
        a = min(DT / max(tau, DT), 1.0)
        for t in range(len(thr01)):
            f = f + (thr01[t] - f) * a
            pred.append(f)
        mask = (thr01 > 0.02) | (np.asarray(pred) > 0.02)
        err = float(np.sum((np.asarray(pred)[mask] - obs7[mask]) ** 2))
        if err < best_err:
            best_tau, best_err = float(tau), err
    return best_tau


def m1_rls_identifiability(quick: bool) -> dict[str, Any]:
    """Vehicle-parameter identification from the SAME sub-limit data (RLS on
    noisy observables): kappa_b/kappa_d via VehicleRLS, stiffness scale via
    lateral LS, drive tau via lag fit. Includes the mu-invariance check."""
    rows = []
    n_veh = M1_RLS_VEH_SEEDS if not quick else 2
    for vi in range(n_veh):
        scales = sample_vehicle_scales(910_000 + vi)
        kb_true, kd_true = true_kappas(scales)
        for mu in (M1_RLS_MUS if not quick else (0.7,)):
            for u in (M1_UTILIZATIONS if not quick else (0.2, 0.8)):
                for noise in (0.0, M1_NOISE_STD):
                    model = m1_make_model(mu, scales)
                    # commands sized in the TRUE vehicle's capacity frame so the
                    # episode is genuinely at utilization u (harness privilege,
                    # cap only -- the estimator never sees mu or the scales)
                    fzr_true = FZR * scales["mass_scale"]
                    fzf_true = FZF * scales["mass_scale"]
                    cmds = []
                    f_rear = u * TIRE_CAP * mu * fzr_true
                    alpha = (mu * fzf_true / (CF_NOM * scales["tire_stiffness_scale"])) \
                        * math.atanh(min(u, 0.97))
                    for t in range(M1_STEPS):
                        s = t * DT
                        steer, fd, fb = 0.0, 0.0, 0.0
                        if 0.5 <= s < 1.5:
                            fd = min(f_rear, MAX_DRIVE * scales["drive_scale"])
                        elif 2.0 <= s < 3.0:
                            fb = min(f_rear, MAX_BRAKE * scales["brake_scale"])
                        elif 3.5 <= s < 5.5:
                            steer = alpha * math.sin(2.0 * math.pi * (s - 3.5) / 2.0)
                        cmds.append((steer, fd, fb))
                    traj, extra = m1_rollout(model, cmds, collect_actuator=True)
                    rng = np.random.default_rng([SEED_BASE, 911, vi, int(mu * 100), int(u * 100), int(noise * 100)])
                    noisy = traj + rng.normal(0.0, 1.0, traj.shape) * (noise * M1_OBS_SCALES)
                    rls = VehicleRLS(r_noise_ax=max((15.0 * noise) ** 2, 0.04))
                    for t in range(M1_STEPS):
                        rls.update_frame(vx=noisy[t, 0], ax=noisy[t, 3],
                                         fd_nom=extra[t, 0] * MAX_DRIVE,
                                         fb_nom=extra[t, 1] * MAX_BRAKE,
                                         steer=extra[t, 4], ay=noisy[t, 4])
                    kb_hat, kd_hat = rls.kappas
                    # stiffness scale via lateral LS on steer-segment frames;
                    # slip angles recomputed from the NOISY observables + the
                    # (observable) steer actuator state; mass uses the truth
                    # (mass alone is unidentifiable, see physics_reduction --
                    # the honest estimand is stiffness-per-mass; declared)
                    m_true = MASS * scales["mass_scale"]
                    seg = slice(175, 275)
                    vx_n, vy_n, yaw_n = noisy[seg, 0], noisy[seg, 1], noisy[seg, 2]
                    steer_n = extra[seg, 4]
                    af = np.arctan2(vy_n + LF * yaw_n, np.abs(np.maximum(vx_n, 0.5))) - steer_n
                    ar = np.arctan2(vy_n - LR * yaw_n, np.abs(np.maximum(vx_n, 0.5)))
                    y_lat = m_true * (noisy[seg, 4] + yaw_n * vx_n)
                    z = -(CF_NOM * af * np.cos(steer_n) + CR_NOM * ar)
                    ss_hat = float(np.sum(z * y_lat) / max(np.sum(z * z), 1e-9))
                    tau_hat = m1_fit_tau(extra)
                    rows.append({
                        "veh_seed": vi, "mu": mu, "utilization": u, "noise_std": noise,
                        "kappa_b_true": round(kb_true, 4), "kappa_b_hat": round(kb_hat, 4),
                        "kappa_d_true": round(kd_true, 4), "kappa_d_hat": round(kd_hat, 4),
                        "kappa_b_abs_err": round(abs(kb_hat - kb_true), 4),
                        "kappa_d_abs_err": round(abs(kd_hat - kd_true), 4),
                        "stiffness_scale_true": round(scales["tire_stiffness_scale"], 4),
                        "stiffness_scale_hat": round(ss_hat, 4),
                        "drive_tau_true": round(0.08 * scales["actuator_tau_scale"], 4),
                        "drive_tau_hat": tau_hat,
                        "rls_frames": rls.n_frames,
                    })
    # aggregates
    def agg(key_true: str, key_hat: str, noise: float, u: float) -> float | None:
        vals = [abs(r[key_hat] - r[key_true]) for r in rows
                if r["noise_std"] == noise and r["utilization"] == u and r[key_hat] is not None]
        return round(float(np.median(vals)), 4) if vals else None

    summary = {}
    for noise in (0.0, M1_NOISE_STD):
        for u in M1_UTILIZATIONS:
            if any(r["noise_std"] == noise and r["utilization"] == u for r in rows):
                summary[f"u{u:g}_noise{noise:g}"] = {
                    "kappa_b_abs_err_median": agg("kappa_b_true", "kappa_b_hat", noise, u),
                    "kappa_d_abs_err_median": agg("kappa_d_true", "kappa_d_hat", noise, u),
                    "stiffness_abs_err_median": agg("stiffness_scale_true", "stiffness_scale_hat", noise, u),
                    "drive_tau_abs_err_median": agg("drive_tau_true", "drive_tau_hat", noise, u),
                }
    # mu-invariance of the vehicle estimates (max spread of kappa_b_hat across mu)
    inv = []
    for vi in range(n_veh):
        for u in (M1_UTILIZATIONS if not quick else (0.2, 0.8)):
            hats = [r["kappa_b_hat"] for r in rows
                    if r["veh_seed"] == vi and r["utilization"] == u and r["noise_std"] == 0.0]
            if len(hats) >= 2:
                inv.append(max(hats) - min(hats))
    return {"rows": rows, "summary_abs_err_median": summary,
            "kappa_b_hat_mu_spread_max": (round(float(max(inv)), 4) if inv else None),
            "note": "kappa = authority/mass ratios; the only vehicle quantities this "
                    "controller family consumes (mass alone is unidentifiable AND unneeded "
                    "longitudinally: capacity decel and mu_hat are mass-free)"}


# --------------------------------------- M2: vehicle-randomized degraded pool


def make_classes(reg, deg):
    DegradationAwareDetector, _ = deg.make_classes(reg)

    class BeliefDetector(DegradationAwareDetector):
        """Authority-belief injection: scale the actuator-state channels by the
        believed kappas BEFORE the (smoothed) shortfall math. With true belief
        the detector sees exactly the clean-vehicle signal model; with nominal
        belief on a randomized vehicle the shortfall acquires a multiplicative
        bias 1 - kappa_true/kappa_bel that no time-averaging removes."""

        def __init__(self, tau: float, smooth_window: int, belief: Belief):
            self.belief = belief
            super().__init__(tau, smooth_window)

        def update(self, obs: np.ndarray) -> None:
            obs = np.asarray(obs, dtype=np.float64).copy()
            obs[7] *= self.belief.kd
            obs[8] *= self.belief.kb
            super().update(obs)

    class BeliefRampController(reg.RampPolicyController):
        """RampPolicyController with (i) the belief detector, (ii) command
        remapping f' = f/kappa_bel on the brake/throttle channels (full
        commands f >= 0.999 kept at 1: 'maximum available' semantics), and
        (iii) optional in-episode vehicle RLS feeding the belief live."""

        def __init__(self, *args, belief: Belief | None = None, smooth_window: int = 1,
                     rls: bool = False, rls_r_ax: float = 0.36, **kw):
            # attributes referenced by reset() must exist before the parent
            # __init__ (which ends in self.reset()) runs
            self.belief = belief if belief is not None else Belief()
            self.smooth_window = smooth_window
            self.use_rls = rls
            self.rls_r_ax = rls_r_ax
            self.rls_obj: VehicleRLS | None = None
            super().__init__(*args, **kw)
            self.detector = BeliefDetector(self.detector.tau, smooth_window, self.belief)
            self.detector.reset()

        def reset(self) -> None:
            super().reset()
            if self.use_rls:
                self.rls_obj = VehicleRLS(r_noise_ax=self.rls_r_ax)
                self.belief.set(1.0, 1.0)

        def act(self, obs: np.ndarray) -> np.ndarray:
            obs = np.asarray(obs, dtype=np.float64)
            if self.use_rls and self.rls_obj is not None:
                self.rls_obj.update_obs(obs)
                kb, kd = self.rls_obj.kappas
                self.belief.set(kb, kd)
            censored_before = self.censored
            action = super().act(obs)
            # censor-branch mu_hat was computed in the nominal frame; correct
            # it to the believed frame (applied force scales with kappa_b)
            if self.censored and not censored_before and self.mu_hat is not None:
                self.mu_hat = float(np.clip(self.mu_hat * self.belief.kb, 0.10, 1.40))
            for idx, kappa in ((1, self.belief.kd), (2, self.belief.kb)):
                f = 0.5 * (float(action[idx]) + 1.0)
                if 1e-6 < f < 0.999:
                    action[idx] = 2.0 * min(f / max(kappa, 1e-6), 1.0) - 1.0
            return action

    return BeliefDetector, BeliefRampController


class TruthBeliefContext(Belief):
    """Belief that the harness sets to the episode's true kappas before each
    rollout (T1/T3 arms). Shared instance; pool.rollout updates it."""


def make_pool_cls(reg, deg, mod_b):
    class VehiclePool(reg.EnvPool):
        def __init__(self, mod_b_, interp, design, delay_steps: int, noise_std: float,
                     truth_ctx: TruthBeliefContext):
            super().__init__(mod_b_, interp, design)
            self.delay_steps, self.noise_std = delay_steps, noise_std
            self.truth_ctx = truth_ctx

        def env_for(self, mu: float, seed: int):
            key = (round(mu, 6), int(seed))
            if key not in self._cache:
                d = reg.jittered_distance(self.interp, mu, seed)
                level = self.mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d,
                                             entry_speed=reg.v_star(self.interp, mu))
                cfg = self.mod_b.level_env_config(self.design, level)
                s = sample_vehicle_scales(seed)
                cfg["randomization"].update({
                    "mass_scale_range": [s["mass_scale"]] * 2,
                    "brake_scale_range": [s["brake_scale"]] * 2,
                    "drive_scale_range": [s["drive_scale"]] * 2,
                    "tire_stiffness_scale_range": [s["tire_stiffness_scale"]] * 2,
                    "actuator_tau_scale_range": [s["actuator_tau_scale"]] * 2,
                })
                self._cache[key] = deg.make_degraded_env(reg, self.mod_b, cfg,
                                                         self.delay_steps, self.noise_std)
            return self._cache[key]

        def rollout(self, controller, mu: float, seed: int, **tags):
            kb, kd = true_kappas(sample_vehicle_scales(seed))
            self.truth_ctx.set(kb, kd)
            return super().rollout(controller, mu, seed, **tags)

    return VehiclePool


def make_tier_cls(reg):
    class FreshTier(reg.TierMeasurement):
        def seed_for(self, point: int, k: int, phase: str) -> int:
            return SEED_BASE * 10 + 17 * point + 1000 * k + (0 if phase == "sel" else 100000)

    return FreshTier


# ------------------------------------------------- M2: per-cell tau calibration


def calibrate_cell(reg, deg, mod_b, mod_a, interp, detector_cls, pool_cls, truth_ctx,
                   delay_steps: int, noise_std: float, windows: tuple[int, ...],
                   quick: bool) -> dict[str, Any]:
    """Sub-limit ramps on vehicle-randomized degraded envs; tau=inf detectors
    for both belief modes (nominal / truth) x all windows in parallel on the
    SAME episodes. Harness privilege: sub-limit caps use true mu AND the true
    brake/drive scales (cap only; detectors never see them)."""
    design = reg.make_design(mod_b, REVEAL)
    pool = pool_cls(mod_b, interp, design, delay_steps, noise_std, truth_ctx)
    maxima: dict[tuple[str, int], list[float]] = {}
    n_eps = 0
    try:
        mus = CALIB_MUS if not quick else (0.9,)
        n_veh = CALIB_VEH_SEEDS if not quick else 1
        for mu in mus:
            for j in range(n_veh):
                seed = SEED_BASE * 10 + int(mu * 100) * 101 + j + 700000
                scales = sample_vehicle_scales(seed)
                kb_t, kd_t = true_kappas(scales)
                fzr_true = FZR * scales["mass_scale"]
                f_limit = TIRE_CAP * mu * fzr_true
                brake_frac_cmd = min(CALIB_FRAC * f_limit / (MAX_BRAKE * scales["brake_scale"]), 1.0)
                drive_frac_cmd = min(0.50 * f_limit / (MAX_DRIVE * scales["drive_scale"]), 1.0)
                env = pool.env_for(mu, seed)
                obs, _ = env.reset(seed=seed)
                dets = {}
                for w in windows:
                    dets[("nominal", w)] = detector_cls(1e9, w, Belief(1.0, 1.0))
                    dets[("truth", w)] = detector_cls(1e9, w, Belief(kb_t, kd_t))
                f_cmd01 = 0.0
                for t in range(CALIB_STEPS):
                    obs_arr = np.asarray(obs, dtype=np.float64)
                    for det in dets.values():
                        det.update(obs_arr)
                    vx = float(obs_arr[0]) * 20.0
                    steer = mod_a.centerline_steer(obs_arr)
                    if t < 15 or not (t < 140 and vx > 2.5):
                        thr01 = float(np.clip(0.55 * (reg.V0 - vx), 0.0, drive_frac_cmd))
                        action = [steer, 2.0 * thr01 - 1.0, -1.0]
                    else:
                        f_cmd01 = min(f_cmd01 + (3000.0 / MAX_BRAKE) * DT, brake_frac_cmd)
                        action = [steer, -1.0, 2.0 * f_cmd01 - 1.0]
                    obs, _, terminated, truncated, _ = env.step(np.asarray(action, dtype=np.float64))
                    if terminated or truncated:
                        break
                n_eps += 1
                for key, det in dets.items():
                    maxima.setdefault(key, []).append(float(det.max_shortfall))
    finally:
        pool.close()
    out: dict[str, Any] = {"n_episodes": n_eps, "delay_steps": delay_steps, "noise_std": noise_std}
    for mode in ("nominal", "truth"):
        out[mode] = {}
        for w in windows:
            mx = max(maxima.get((mode, w), [0.0]))
            out[mode][f"w{w}"] = {"max_signal": round(mx, 4),
                                  "tau": round(max(TAU_SAFETY * mx, TAU_FLOOR), 4)}
    return out


def tau_variants(noise_std: float, cal_mode: dict[str, Any]) -> list[tuple[int, float]]:
    if noise_std <= 0.0:
        variants = [(1, 0.08)]
        tau1 = cal_mode["w1"]["tau"]
        if tau1 > 0.09:
            variants.append((1, round(tau1, 3)))
        return variants
    out, seen = [], set()
    for w in SMOOTH_WINDOWS_NOISE:
        v = (w, round(cal_mode[f"w{w}"]["tau"], 3))
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


# ------------------------------------------------------------ M2: cell measure


def wilson_ci(p_hat: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return (round(center - half, 4), round(center + half, 4))


def measure_cell(reg, deg, mod_b, mod_a, interp, design, delay_steps, noise_std, mus,
                 sel_seeds, val_seeds, rows_out, controller_cls, pool_cls, tier_cls,
                 truth_ctx, cal, quick) -> dict[str, Any]:
    tm = tier_cls(mod_b, interp, design, 0, REVEAL, mus, sel_seeds, val_seeds, rows_out)
    tm.pool.close()
    tm.pool = pool_cls(mod_b, interp, design, delay_steps, noise_std, truth_ctx)
    n_pts = len(mus)
    rls_r = max((15.0 * noise_std) ** 2, 0.04)

    def ramp(name: str, belief, w: int = 1, rls: bool = False, **kw) -> Callable[[], Any]:
        return lambda: controller_cls(mod_b, interp, design, name, belief=belief,
                                      smooth_window=w, rls=rls, rls_r_ax=rls_r, **kw)

    rates = SEEKER_RATES if not quick else (20000.0,)
    deltas = SEEKER_DELTAS if not quick else (0.06,)
    dvs = SEEKER_DVS if not quick else (0.0,)

    # T0 / T1 seekers (per-belief-mode calibrated detector variants)
    for tier, mode, belief_factory in (("t0", "nominal", lambda: Belief(1.0, 1.0)),
                                       ("t1", "truth", lambda: truth_ctx)):
        for r in rates:
            for w, tau in tau_variants(noise_std, cal[mode]):
                for delta in deltas:
                    for dv in dvs:
                        name = f"{tier}_seeker_r{r:g}_w{w}_t{tau:g}_d{delta:g}_v{dv:+g}"
                        tm.register(name, f"{tier}_seeker",
                                    ramp(name, belief_factory(), w=w, mode="seeker",
                                         ramp_rate=r, tau=tau, backoff=delta,
                                         strategy="hold", dv=dv))
    # belief-free fixed plans (shared control arms; no vehicle knowledge used)
    for v in (reg.FIXED_SPEED_GRID if not quick else (4.5, 7.5, 10.5)):
        plan = mod_b.PlanSpec(name=f"fixed_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        tm.register(plan.name, "fixed_speed", (lambda p=plan: mod_b.CommitmentController(p, design)))
    for frac, hold_s in (reg.FIXED_RAMP_GRID if not quick else reg.FIXED_RAMP_GRID[:1]):
        name = f"fixedramp_f{frac:g}_h{hold_s:g}"
        tm.register(name, "fixed_ramp", ramp(name, Belief(1.0, 1.0), mode="fixed_ramp",
                                             fixed_frac=frac, fixed_hold_s=hold_s))
    for name in list(tm.results):
        tm.eval(name, phase="sel")

    # T2 (mu known, vehicle nominal +/- RLS) and T3 (both known): per-point dv selection
    dv_grid = ORACLE_DVS if not quick else (0.0, 0.5)
    t2_choice, t3_choice = [], []
    for point, mu in enumerate(mus):
        cands2, cands3 = [], []
        for dv in dv_grid:
            for rls_on in ((False, True) if not quick else (True,)):
                name = f"t2_oracle_dv{dv:+g}_rls{int(rls_on)}"
                if name not in tm.results:
                    tm.register(name, "t2_oracle", lambda: None)
                tm.builders[name] = ramp(name, Belief(1.0, 1.0), mode="oracle",
                                         mu_true=mu, dv=dv, rls=rls_on)
                tm.eval(name, points=[point], phase="sel")
                cands2.append(name)
            name3 = f"t3_oracle_dv{dv:+g}"
            if name3 not in tm.results:
                tm.register(name3, "t3_oracle", lambda: None)
            tm.builders[name3] = ramp(name3, truth_ctx, mode="oracle", mu_true=mu, dv=dv)
            tm.eval(name3, points=[point], phase="sel")
            cands3.append(name3)
        pick = lambda cands: max(cands, key=lambda n: (tm.point_stat(n, point, "sel", "success"),
                                                       tm.point_stat(n, point, "sel", "return")))
        t2_choice.append(pick(cands2))
        t3_choice.append(pick(cands3))

    # selection -> validation
    best_t0 = tm.best_in_group("t0_seeker")
    best_t1 = tm.best_in_group("t1_seeker")
    best_fs = tm.best_in_group("fixed_speed")
    best_fr = tm.best_in_group("fixed_ramp")
    for point, mu in enumerate(mus):
        for choice, tier in ((t2_choice[point], "t2"), (t3_choice[point], "t3")):
            dv = float(choice.split("dv")[1].split("_")[0])
            if tier == "t2":
                rls_on = bool(int(choice.split("rls")[1]))
                tm.builders[choice] = ramp(choice, Belief(1.0, 1.0), mode="oracle",
                                           mu_true=mu, dv=dv, rls=rls_on)
            else:
                tm.builders[choice] = ramp(choice, truth_ctx, mode="oracle", mu_true=mu, dv=dv)
            tm.eval(choice, points=[point], phase="val")
    for name in (best_t0, best_t1, best_fs, best_fr):
        tm.eval(name, phase="val")

    def per_point_rows(choices: list[str], phase: str) -> list[list[dict[str, Any]]]:
        return [tm.results[choices[p]][p][phase] for p in range(n_pts)]

    def tier_mean_oracle(choices: list[str], phase: str) -> float:
        return float(np.mean([tm.point_stat(choices[p], p, phase, "success") for p in range(n_pts)]))

    seek0_val = tm.tier_mean(best_t0, "val")
    seek1_val = tm.tier_mean(best_t1, "val")
    fixed_val = max(tm.tier_mean(best_fs, "val"), tm.tier_mean(best_fr, "val"))
    fixed_arm = best_fs if tm.tier_mean(best_fs, "val") >= tm.tier_mean(best_fr, "val") else best_fr
    t2_val = tier_mean_oracle(t2_choice, "val")
    t3_val = tier_mean_oracle(t3_choice, "val")

    # tier values = max(tier-specific arm, belief-free fixed floor), with the
    # winning arm recorded; episode-paired bootstrap on the decomposition.
    def tier_rows(arm_kind: str) -> dict[tuple[int, int], float]:
        """(point, seed_k) -> success for the chosen arm of a tier."""
        if arm_kind == "fixed":
            rows = {(p, k): tm.results[fixed_arm][p]["val"][k]["success"]
                    for p in range(n_pts) for k in range(len(val_seeds))}
        elif arm_kind in ("t0", "t1"):
            arm = best_t0 if arm_kind == "t0" else best_t1
            rows = {(p, k): tm.results[arm][p]["val"][k]["success"]
                    for p in range(n_pts) for k in range(len(val_seeds))}
        else:
            choices = t2_choice if arm_kind == "t2" else t3_choice
            rows = {(p, k): tm.results[choices[p]][p]["val"][k]["success"]
                    for p in range(n_pts) for k in range(len(val_seeds))}
        return {key: (1.0 if v else 0.0) for key, v in rows.items()}

    tier_def = {}
    tier_def["t0"] = ("t0", seek0_val) if seek0_val >= fixed_val else ("fixed", fixed_val)
    tier_def["t1"] = ("t1", seek1_val) if seek1_val >= fixed_val else ("fixed", fixed_val)
    tier_def["t2"] = ("t2", t2_val) if t2_val >= fixed_val else ("fixed", fixed_val)
    tier_def["t3"] = ("t3", t3_val) if t3_val >= fixed_val else ("fixed", fixed_val)
    tier_rows_map = {t: tier_rows(kind) for t, (kind, _v) in tier_def.items()}
    keys = sorted(tier_rows_map["t0"])
    n_eps_val = len(keys)

    t0v, t1v, t2v, t3v = (tier_def[t][1] for t in ("t0", "t1", "t2", "t3"))
    prize = t3v - t0v
    vehicle_comp = t1v - t0v
    surface_comp = t2v - t0v
    interaction = prize - vehicle_comp - surface_comp

    rng = np.random.default_rng([SEED_BASE, 888, delay_steps, int(noise_std * 1000)])
    boots = {"prize": [], "vehicle": [], "surface": [], "interaction": []}
    arr = {t: np.array([tier_rows_map[t][k] for k in keys]) for t in tier_rows_map}
    for _ in range(2000):
        idx = rng.integers(0, n_eps_val, n_eps_val)
        m = {t: float(arr[t][idx].mean()) for t in arr}
        boots["prize"].append(m["t3"] - m["t0"])
        boots["vehicle"].append(m["t1"] - m["t0"])
        boots["surface"].append(m["t2"] - m["t0"])
        boots["interaction"].append((m["t3"] - m["t0"]) - (m["t1"] - m["t0"]) - (m["t2"] - m["t0"]))
    ci = {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
          for k, v in boots.items()}

    summary = {
        "reveal_m": REVEAL,
        "delay_steps": delay_steps,
        "delay_ms": round(delay_steps * DT * 1000.0),
        "noise_std": noise_std,
        "episodes": tm.pool.episodes,
        "n_val_episodes_per_arm": n_eps_val,
        "arms": {
            "t0_best_seeker": {"plan": best_t0, "success_val": round(seek0_val, 4)},
            "t1_best_seeker": {"plan": best_t1, "success_val": round(seek1_val, 4)},
            "best_fixed": {"plan": fixed_arm, "success_val": round(fixed_val, 4)},
            "t2_oracle": {"success_val": round(t2_val, 4),
                          "plan_per_point": t2_choice,
                          "rls_selected_fraction": round(float(np.mean(
                              [1.0 if c.endswith("rls1") else 0.0 for c in t2_choice])), 3)},
            "t3_oracle": {"success_val": round(t3_val, 4), "plan_per_point": t3_choice},
        },
        "tiers_val": {
            "T0_know_nothing": {"success": round(t0v, 4), "arm": tier_def["t0"][0],
                                "wilson_ci95": wilson_ci(t0v, n_eps_val)},
            "T1_know_vehicle": {"success": round(t1v, 4), "arm": tier_def["t1"][0],
                                "wilson_ci95": wilson_ci(t1v, n_eps_val)},
            "T2_know_mu": {"success": round(t2v, 4), "arm": tier_def["t2"][0],
                           "wilson_ci95": wilson_ci(t2v, n_eps_val)},
            "T3_know_both": {"success": round(t3v, 4), "arm": tier_def["t3"][0],
                             "wilson_ci95": wilson_ci(t3v, n_eps_val)},
        },
        "decomposition_val": {
            "prize_T3_minus_T0": round(prize, 4),
            "vehicle_component_T1_minus_T0": round(vehicle_comp, 4),
            "surface_component_T2_minus_T0": round(surface_comp, 4),
            "interaction": round(interaction, 4),
            "bootstrap_ci95_paired": ci,
        },
        "detector_variants": {m: tau_variants(noise_std, cal[m]) for m in ("nominal", "truth")},
    }
    return summary, tm, best_t1


# --------------------------------------------------- M3: familiarization prefix


def run_prefix_rls(reg, deg, mod_b, mod_a, interp, design, mu, seed, delay_steps,
                   noise_std, prefix_steps: int, rls_r: float) -> tuple[VehicleRLS, dict[str, Any]]:
    """Ordinary sub-limit driving on the same vehicle/surface/degradation cell,
    no hazard in range; the vehicle RLS accumulates over the prefix."""
    level = mod_b.LevelSpec(mu=mu, d_lo=200.0, d_hi=200.0, entry_speed=reg.v_star(interp, mu))
    cfg = mod_b.level_env_config(design, level)
    cfg["max_steps"] = prefix_steps + 10
    s = sample_vehicle_scales(seed)
    cfg["randomization"].update({
        "mass_scale_range": [s["mass_scale"]] * 2,
        "brake_scale_range": [s["brake_scale"]] * 2,
        "drive_scale_range": [s["drive_scale"]] * 2,
        "tire_stiffness_scale_range": [s["tire_stiffness_scale"]] * 2,
        "actuator_tau_scale_range": [s["actuator_tau_scale"]] * 2,
    })
    env = deg.make_degraded_env(reg, mod_b, cfg, delay_steps, noise_std)
    rls = VehicleRLS(r_noise_ax=rls_r)
    fzr_true = FZR * s["mass_scale"]
    f_cap = PREFIX_UTIL_CAP * TIRE_CAP * mu * fzr_true  # harness-only cap (true mu/scales)
    brake_cap01 = min(f_cap / (MAX_BRAKE * s["brake_scale"]), 1.0)
    drive_cap01 = min(f_cap / (MAX_DRIVE * s["drive_scale"]), 1.0)
    max_util = 0.0
    try:
        obs, _ = env.reset(seed=seed + 31337)
        for t in range(prefix_steps):
            obs_arr = np.asarray(obs, dtype=np.float64)
            rls.update_obs(obs_arr)
            vx = float(obs_arr[0]) * 20.0
            s_t = t * DT
            steer = mod_a.centerline_steer(obs_arr) + 0.05 * math.sin(2.0 * math.pi * s_t / 2.5)
            cycle = s_t % 5.0
            if 1.0 <= cycle < 2.0:  # gentle brake pulse
                action = [steer, -1.0, 2.0 * brake_cap01 * min(cycle - 1.0, 0.4) / 0.4 - 1.0]
            elif 2.5 <= cycle < 4.0:  # gentle re-acceleration
                thr01 = float(np.clip(0.55 * (reg.V0 + 0.5 - vx), 0.0, drive_cap01))
                action = [steer, 2.0 * thr01 - 1.0, -1.0]
            else:  # speed hold
                thr01 = float(np.clip(0.45 * (reg.V0 - vx), 0.0, drive_cap01))
                action = [steer, 2.0 * thr01 - 1.0, -1.0]
            obs, _, terminated, truncated, _ = env.step(np.asarray(action, dtype=np.float64))
            base = env.unwrapped if hasattr(env, "unwrapped") else env._base
            forces = base.last_forces
            cap_r = TIRE_CAP * mu * fzr_true
            util = math.hypot(forces.fx_rear, forces.fy_rear) / max(cap_r, 1.0)
            max_util = max(max_util, util)
            if terminated or truncated:
                break
    finally:
        env.close()
    kb_hat, kd_hat = rls.kappas
    kb_t, kd_t = true_kappas(s)
    telemetry = {
        "prefix_steps": prefix_steps,
        "rls_frames": rls.n_frames,
        "max_rear_utilization_truth": round(max_util, 3),
        "kappa_b_abs_err": round(abs(kb_hat - kb_t), 4),
        "kappa_d_abs_err": round(abs(kd_hat - kd_t), 4),
    }
    return rls, telemetry


def measure_prefix_cell(reg, deg, mod_b, mod_a, interp, design, delay_steps, noise_std,
                        mus, val_seeds, rows_out, controller_cls, pool_cls, tier_cls,
                        truth_ctx, best_t1_plan: str, cal, quick) -> list[dict[str, Any]]:
    """For each prefix length: prefix-RLS belief -> T1-config seeker -> task."""
    # parse the T1-selected seeker config: t1_seeker_r{r}_w{w}_t{tau}_d{delta}_v{dv}
    parts = best_t1_plan.split("_")
    r = float(parts[2][1:])
    w = int(parts[3][1:])
    tau = float(parts[4][1:])
    delta = float(parts[5][1:])
    dv = float(parts[6][1:])
    rls_r = max((15.0 * noise_std) ** 2, 0.04)
    out = []
    for prefix_s in (PREFIX_SECONDS if not quick else (5.0,)):
        prefix_steps = int(prefix_s / DT)
        tm = tier_cls(mod_b, interp, design, 0, REVEAL, mus, [0], val_seeds, rows_out)
        tm.pool.close()
        tm.pool = pool_cls(mod_b, interp, design, delay_steps, noise_std, truth_ctx)
        name = f"prefix{prefix_s:g}s_seeker"
        tm.register(name, "prefix_seeker", lambda: None)
        kb_errs, kd_errs = [], []
        try:
            for point, mu in enumerate(mus):
                for k in range(len(val_seeds)):
                    seed = tm.seed_for(point, k, "val")
                    rls, tel = run_prefix_rls(reg, deg, mod_b, mod_a, interp, design, mu,
                                              seed, delay_steps, noise_std, prefix_steps, rls_r)
                    kb_errs.append(tel["kappa_b_abs_err"])
                    kd_errs.append(tel["kappa_d_abs_err"])
                    kb_hat, kd_hat = rls.kappas
                    belief = Belief(kb_hat, kd_hat)  # frozen at task start
                    tm.builders[name] = (lambda b=belief: controller_cls(
                        mod_b, interp, design, name, belief=b, smooth_window=w,
                        rls=False, mode="seeker", ramp_rate=r, tau=tau,
                        backoff=delta, strategy="hold", dv=dv))
                    # one (point, seed) at a time: temporary val_seeds slice
                    controller = tm.builders[name]()
                    row = tm.pool.rollout(controller, mu, seed, reveal_tier=REVEAL,
                                          plan=name, plan_group="prefix_seeker",
                                          mu_point=round(mu, 4), phase="val",
                                          prefix_s=prefix_s, **tel)
                    tm.results[name][point]["val"].append(row)
                    rows_out.append(row)
        finally:
            tm.pool.close()
        succ = tm.tier_mean(name, "val")
        n = len(mus) * len(val_seeds)
        out.append({
            "prefix_s": prefix_s,
            "success_val": round(succ, 4),
            "wilson_ci95": wilson_ci(succ, n),
            "kappa_b_abs_err_median": round(float(np.median(kb_errs)), 4),
            "kappa_d_abs_err_median": round(float(np.median(kd_errs)), 4),
            "seeker_config_from_t1": {"rate": r, "w": w, "tau": tau, "delta": delta, "dv": dv},
            "n_episodes": n,
        })
    return out


# ------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=2)
    parser.add_argument("--val-seeds", type=int, default=10)
    parser.add_argument("--skip-m1", action="store_true")
    parser.add_argument("--results-json", type=Path, default=RESULTS_JSON)
    args = parser.parse_args()
    cells = CELLS_DEFAULT
    if args.quick:
        args.points, args.sel_seeds, args.val_seeds = 4, 1, 2
        cells = ((0, 0.0), (0, 0.05))

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    reg = load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    deg = load_module(DEGRADED_SCRIPT, "degraded_regime_final")
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_a = load_module(SLIP_SCRIPT, "slip_onset_detectability")
    interp = mod_c.interp_lin
    detector_cls, controller_cls = make_classes(reg, deg)
    truth_ctx = TruthBeliefContext()
    pool_cls = make_pool_cls(reg, deg, mod_b)
    tier_cls = make_tier_cls(reg)

    lo, hi = reg.MU_DOMAIN
    mus = [lo + (i + 0.5) / args.points * (hi - lo) for i in range(args.points)]
    sel_seeds = list(range(args.sel_seeds))
    val_seeds = list(range(args.val_seeds))

    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_belief_decomposition",
        "generated_by": "scripts/feasibility_audit/belief_decomposition.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "question": (
            "Decompose the degraded-regime belief prize into VEHICLE knowledge (class prior / "
            "familiarization-identifiable) vs SURFACE knowledge (mu), and measure how much of the "
            "vehicle share a zero-risk sub-limit familiarization period recovers."
        ),
        "physics_reduction": (
            "This controller family consumes vehicle knowledge only through kappa_b = "
            "brake_scale/mass_scale and kappa_d = drive_scale/mass_scale: capacity deceleration "
            "mu*0.98*g*lf/wb is mass-free and mu_hat = realized/(0.98*Fzr_bel) is invariant to a "
            "consistent mass belief. Stiffness/actuator-tau scales are randomized in the env but "
            "not consumed by the scripted controllers (declared limitation)."
        ),
        "vehicle_randomization": {k: list(v) for k, v in VEH_RANGES.items()},
        "task_surface": {
            "family": "B2K2_final + per-episode vehicle randomization, reveal 9.5 m",
            "mu_points": [round(m, 4) for m in mus],
            "selection_seeds": args.sel_seeds, "validation_seeds": args.val_seeds,
            "seed_base": SEED_BASE,
            "vehicle_seed_note": "scales ~ U(ranges) keyed by [20260622, 555, rollout_seed]",
            "cells": [{"delay_steps": d, "delay_ms": round(d * DT * 1000), "noise_std": n}
                      for d, n in cells],
            "anchor": "matched (every tier runs on the same degraded stream; no dead-reckoning credit)",
        },
        "m1_subliminal_leakage": {},
        "m2_calibration": {},
        "m2_cells": [],
        "m3_familiarization": {},
        "artifacts": {},
    }

    def flush() -> None:
        payload["elapsed_s"] = round(time.time() - started, 1)
        from autodrift.artifacts import utc_timestamp
        payload["generated_at_utc"] = utc_timestamp()
        args.results_json.parent.mkdir(parents=True, exist_ok=True)
        args.results_json.write_text(json.dumps(reg.to_jsonable(payload), indent=2), encoding="utf-8")

    # [1/3] M1
    if not args.skip_m1:
        print("[1/3] M1 sub-limit mu-leakage + vehicle RLS identifiability", flush=True)
        leak = m1_leakage()
        payload["m1_subliminal_leakage"] = {
            "leakage": leak,
            "rls_identifiability": m1_rls_identifiability(args.quick),
            "protocol": {
                "command_sequence": "settle/drive 1s/coast/brake 1s/coast/steer-sine 2s/coast, "
                                    "forces = u x anchor-mu capacity, v0 12 m/s, 6 s, dt 0.02",
                "utilizations": list(M1_UTILIZATIONS),
                "mu_pairs": [list(p) for p in M1_PAIRS],
                "anchor_rule": "pairwise anchor = min(mu) of the pair (neither vehicle saturates)",
            },
        }
        for p in leak["posterior_mu"]:
            print(f"  u={p['utilization']:.2f} -> mu-posterior std {p['posterior_std']:.4f} "
                  f"(prior {p['prior_std']:.4f}, ratio {p['posterior_to_prior_std_ratio']:.3f})", flush=True)
        flush()
    else:
        print("[1/3] M1 skipped", flush=True)

    # [2/3] M2
    design = reg.make_design(mod_b, REVEAL)
    print(f"[2/3] M2 four-tier decomposition: {len(cells)} cells x {args.points} mu x "
          f"{args.sel_seeds}+{args.val_seeds} seeds", flush=True)
    rows_out: list[dict[str, Any]] = []
    windows = (1,) + tuple(w for w in SMOOTH_WINDOWS_NOISE if w != 1)
    best_t1_by_cell: dict[tuple[int, float], str] = {}
    for delay_steps, noise_std in cells:
        cal = calibrate_cell(reg, deg, mod_b, mod_a, interp, detector_cls, pool_cls,
                             truth_ctx, delay_steps, noise_std, windows, args.quick)
        payload["m2_calibration"][f"delay{delay_steps}_noise{noise_std:g}"] = cal
        print(f"  cal delay={delay_steps} noise={noise_std:g}: "
              f"nominal w1 tau={cal['nominal']['w1']['tau']:.3f} "
              f"truth w1 tau={cal['truth']['w1']['tau']:.3f}", flush=True)
        t0 = time.time()
        summary, tm, best_t1 = measure_cell(reg, deg, mod_b, mod_a, interp, design,
                                            delay_steps, noise_std, mus, sel_seeds, val_seeds,
                                            rows_out, controller_cls, pool_cls, tier_cls,
                                            truth_ctx, cal, args.quick)
        tm.pool.close()
        summary["elapsed_s"] = round(time.time() - t0, 1)
        payload["m2_cells"].append(summary)
        best_t1_by_cell[(delay_steps, noise_std)] = best_t1
        t = summary["tiers_val"]
        d = summary["decomposition_val"]
        print(f"  cell delay={delay_steps:>2} noise={noise_std:g} | "
              f"T0={t['T0_know_nothing']['success']:.3f} T1={t['T1_know_vehicle']['success']:.3f} "
              f"T2={t['T2_know_mu']['success']:.3f} T3={t['T3_know_both']['success']:.3f} | "
              f"prize={d['prize_T3_minus_T0']:+.3f} veh={d['vehicle_component_T1_minus_T0']:+.3f} "
              f"surf={d['surface_component_T2_minus_T0']:+.3f} int={d['interaction']:+.3f} "
              f"[{summary['episodes']} eps, {summary['elapsed_s']}s]", flush=True)
        flush()

    # [3/3] M3
    print("[3/3] M3 familiarization-prefix value curve", flush=True)
    for delay_steps, noise_std in cells:
        res = measure_prefix_cell(reg, deg, mod_b, mod_a, interp, design, delay_steps,
                                  noise_std, mus, val_seeds, rows_out, controller_cls,
                                  pool_cls, tier_cls, truth_ctx,
                                  best_t1_by_cell[(delay_steps, noise_std)],
                                  payload["m2_calibration"][f"delay{delay_steps}_noise{noise_std:g}"],
                                  args.quick)
        cell_sum = next(c for c in payload["m2_cells"]
                        if c["delay_steps"] == delay_steps and c["noise_std"] == noise_std)
        t0v = cell_sum["tiers_val"]["T0_know_nothing"]["success"]
        t1v = cell_sum["tiers_val"]["T1_know_vehicle"]["success"]
        for r in res:
            r["t0_reference"] = t0v
            r["t1_reference"] = t1v
            gap = t1v - t0v
            r["recapture_fraction_of_T1_minus_T0"] = (
                round((r["success_val"] - t0v) / gap, 4) if abs(gap) > 1e-9 else None)
        payload["m3_familiarization"][f"delay{delay_steps}_noise{noise_std:g}"] = res
        for r in res:
            print(f"  delay={delay_steps:>2} noise={noise_std:g} prefix={r['prefix_s']:>4.1f}s | "
                  f"success={r['success_val']:.3f} (T0={t0v:.3f}, T1={t1v:.3f}, "
                  f"recapture={r['recapture_fraction_of_T1_minus_T0']}) "
                  f"kappa_b_err={r['kappa_b_abs_err_median']:.4f}", flush=True)
        flush()

    from autodrift.artifacts import write_csv_rows
    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, rows_out)
    payload["artifacts"] = {"episode_rows_csv": str(rows_csv),
                            "results_json": str(args.results_json)}
    payload["n_episodes_total"] = len(rows_out)
    flush()
    print(f"results -> {args.results_json}", flush=True)
    print("HEADLINE: " + " | ".join(
        f"d{c['delay_steps']}n{c['noise_std']:g}: prize={c['decomposition_val']['prize_T3_minus_T0']:+.3f} "
        f"veh={c['decomposition_val']['vehicle_component_T1_minus_T0']:+.3f} "
        f"surf={c['decomposition_val']['surface_component_T2_minus_T0']:+.3f}"
        for c in payload["m2_cells"]), flush=True)


if __name__ == "__main__":
    main()
