"""WP1 stage-1 data pipeline (Phase-2 plan WP1.1 + WP1.5 infrastructure):
mu-decoupled rollout collection for the supervised belief estimator, with the
anti-leak dataset acceptance gate and the C3 excitation-gap task variant.

Plan anchors: docs/research-plan-phase2-capability-boundary-tracking.md WP1.1
(behavior policy decoupled from mu; decision-frame single-frame->mu probe
R^2 <= 0.1 gates data acceptance, linear probe primary + small-MLP probe
secondary; 5 s sub-limit familiarization prefix as a standard fixture per
docs/selfid-belief-decomposition-2026-06.md; fresh training SEED_BASE disjoint
from the regime measurement's selection/validation streams) and WP1.5 (C3
variant: mu-informative excitation confined to t < 1.0 s of the task segment,
sub-limit segment with zero shortfall events > 2.5 s, decision at t >= 3.5 s,
per-episode telemetry of the last-excitation-to-decision gap).

Task surface: family #1 only (M3215 G-A fallback routing,
docs/m3215-wp0-degraded-sweep-bridge-validation.md Section 7) = B2K2_final at
reveal 9.5 m. Eligible degradation cells FROZEN by the M3215 hardened matched
panel: {delay5, delay12, delay25, noise0.05}; cell definitions are imported
from scripts/feasibility_audit/wp0_degraded_sweep.py (single source).

Episode construction (one env episode per record):
  [familiarization prefix, 5 s] sub-limit ordinary driving (speed hold +
      gentle mu-FREE force pulses capped at 600 N brake / 600 N drive --
      commanded utilization < 0.5 even at the mu floor 0.25, so per M1 of the
      belief-decomposition doc the prefix is structurally mu-blind -- + small
      steering weave). The env's beta-target INITIALIZATION transient (first
      ~10 frames, policy-independent and identical for every arm of this task
      family) can touch the friction boundary at low mu; it is accounted
      separately (initial_transient_max_util) from the commanded prefix
      utilization. The obstacle is moved PREFIX_DIST_OFFSET_M further away
      so the reveal cannot occur inside the prefix. A vehicle-RLS (kappa_b,
      kappa_d) runs over the prefix frames and its estimates are stored
      per-episode (the heterogeneous-belief standard fixture; with vehicle
      randomization OFF -- the stage-1 default, matching the frozen M3215
      panel -- truth is kappa=1).
  [task segment] one of the mu-DECOUPLED behavior scripts below, until the
      decision tick (reveal frame) + 1 frame, then the rollout stops.

Behavior scripts (all parameters drawn from rng([SEED_BASE, 303, seed]) --
never from mu; ramp force schedules are OPEN-LOOP so the command sequence
cannot encode the detector's mu-dependent stopping time; speed-tracking forces
are capped at mu-free constants 1500 N drive / 600 N brake so closed-loop
re-equilibration is force-limited identically across mu):
  fixed_speed   track a randomized mu-free MULTI-SINE speed schedule (base
                U(6.0, 8.5) + 3 sinusoids, total amp U(1.0, 2.25) m/s, clip
                [5.0, 9.5]) all the way in. The schedule (M3216 bounded data
                iteration) phase-randomizes the longitudinal actuator state
                at any tick: with a constant target, the decision tick ~
                d(mu) correlation (Spearman 0.93) plus the convergence
                transient leaked mu into obs 8/11/3/7 at the decision frame
                (linear OOF R^2 0.13-0.30 on the delay cells, measured on
                the stopped M3216 first run).
  ramp_release  settle, then an open-loop brake-force ramp (rate in {6000,
                20000} N/s, peak U(0.5, 1.0)*6000 N, hold <= 0.4 s) that may
                touch saturation (the mu-informative excitation), release,
                then track the same randomized multi-sine schedule.
  c3_ramp_release (variant="c3") ramp to FULL brake immediately (excitation
                window ends < 1.0 s into the task segment), release, then
                track U(5.5, 6.5) with the mu-free caps; the obstacle is an
                additional C3_EXTRA_DIST_M further away so the decision tick
                lands >= 3.5 s after the task start with a > 2.5 s
                excitation-free gap.

Per-episode record: degraded observation sequence (frames 0..decision+1),
true mu label (mu_eff: the planner interface consumes mu), decision tick
(first obstacle-present frame), role (train/sel/val), variant, behavior
parameters, prefix RLS kappa estimates, and truth-frame excitation telemetry
(last step with rear-tire utilization > 0.8, computed from env internals --
harness-only, never part of the observations).

Pre-registered (frozen before any run; stage-1 smoke validates infrastructure
only and makes no measurement claim):
  - dataset acceptance gate: per cell, decision-frame single-frame -> mu
    linear ridge probe out-of-fold R^2 <= 0.1 (PRIMARY) and small-MLP probe
    out-of-fold R^2 <= 0.1 (SECONDARY); both reported, PASS requires both.
  - C3 telemetry gate: every C3 episode has (a) decision time >= 3.5 s after
    task start, (b) no truth-frame excitation event after task_start + 1.0 s,
    (c) last-excitation-to-decision gap > 2.5 s (vacuously true when the
    brake actuator censors high-mu episodes below the excitation bar --
    has_excitation is reported).
  - seed streams (disjoint from every stream in use: 20260611..20260625 bases
    at x10/x100, see experiments/feasibility_audit/wp1_seed_streams.json):
    episode seed = 20270101*100 + cell_index*1_000_000 + role_offset + i with
    role offsets train +0 / sel +400000 / val +600000 / injection-smoke
    +800000; mu draws rng([20270101, 101, seed]); behavior rng([20270101,
    303, seed]); jitter rng([20270101, 777, seed]); vehicle scales (flag,
    default OFF) rng([20270101, 555, seed]).

Hard constraints: pure CPU numpy (+ torch for the MLP probe only),
zero training of driving policies, deterministic seeds, no git operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/wp1_data_pipeline.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/wp1_data_pipeline.py --full
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
REGIME_SCRIPT = REPO / "scripts/feasibility_audit/ramp_policy_voi_regime.py"
DEGRADED_SCRIPT = REPO / "scripts/feasibility_audit/degraded_regime_final.py"
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
SLIP_SCRIPT = REPO / "scripts/feasibility_audit/slip_onset_detectability.py"
WP0_SCRIPT = REPO / "scripts/feasibility_audit/wp0_degraded_sweep.py"
BELIEF_SCRIPT = REPO / "scripts/feasibility_audit/belief_decomposition.py"
DEFAULT_RUN_DIR = REPO / "runs/feasibility_audit/wp1_dataset"

SEED_BASE = 20270101  # fresh stream; all prior bases 20260611..20260625 (x10/x100)
EPISODE_SEED_BASE = SEED_BASE * 100  # 2_027_010_100: disjoint from every x10 stream
ROLE_OFFSETS = {"train": 0, "sel": 400_000, "val": 600_000, "smoke_eval": 800_000}

DT = 0.02
REVEAL = 9.5
OBS_DIM = 72
PREFIX_S = 5.0
PREFIX_STEPS = int(PREFIX_S / DT)  # 250
PREFIX_BRAKE_CAP_N = 600.0   # mu-free: commanded utilization < 0.5 at the mu floor 0.25
PREFIX_DRIVE_CAP_N = 600.0
PREFIX_TRANSIENT_SKIP = 15   # frames (0.3 s): the env's beta-target initialization transient
# decays below 0.5 utilization by ~frame 12 even at the mu floor (measured)
# (policy-independent, identical for every arm of this task family) is accounted
# separately from the commanded sub-limit prefix utilization
PREFIX_DIST_OFFSET_M = 60.0  # obstacle pushed out so reveal cannot hit the prefix
C3_EXTRA_DIST_M = 40.0       # additional distance so decision >= 3.5 s task-clock
MAX_STEPS_STD = 1000
MAX_STEPS_C3 = 1300
POST_DECISION_FRAMES = 1

TRACK_DRIVE_CAP_N = 1500.0  # mu-free closed-loop caps (< capacity at mu=0.25: 1680 N)
TRACK_BRAKE_CAP_N = 600.0
C3_TRACK_DRIVE_CAP_N = 1200.0  # tighter C3 cap: utilization <= 0.72 even at mu=0.25
EXCITATION_UTIL_BAR = 0.8   # truth rear-tire utilization counting as mu-informative contact
C3_EXCITE_END_S = 1.0
C3_GAP_BAR_S = 2.5
C3_DECISION_MIN_S = 3.5
PROBE_R2_BAR = 0.1
PROBE_FOLDS = 5
MLP_HIDDEN = 64
MLP_EPOCHS = 300
MU_GRID_POINTS = 12

# eligible cells frozen by the M3215 hardened matched panel (routing item 1)
ELIGIBLE_CELL_IDS = ("delay5", "delay12", "delay25", "noise0.05")

VEH_RANGES = {  # used only when --vehicle-randomization is set (mirrors belief_decomposition)
    "mass_scale": (0.85, 1.20),
    "brake_scale": (0.80, 1.15),
    "drive_scale": (0.80, 1.15),
    "tire_stiffness_scale": (0.65, 1.35),
    "actuator_tau_scale": (0.75, 1.75),
}

CLAIM_BOUNDARY = (
    "Feasibility-audit WP1 estimator-training DATA PIPELINE only (Phase-2 manual takeover): "
    "mu-decoupled scripted behavior policies with a 5 s sub-limit familiarization prefix are "
    "rolled out on the B2K2_final family (reveal 9.5 m) under the frozen M3215 eligible "
    "degradation cells to collect (degraded observation sequence, true mu, decision tick) "
    "records, plus the pre-registered decision-frame probe leak gate and C3 gap telemetry. "
    "No driver promotion, policy training, repair-success, gate-validity, paper, "
    "high-fidelity, robustness-result, feasibility-proof, or self-ID capability claim."
)


def load_module(path: Path, name: str):
    import importlib.util

    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_stack() -> dict[str, Any]:
    reg = load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_a = load_module(SLIP_SCRIPT, "slip_onset_detectability")
    deg = load_module(DEGRADED_SCRIPT, "degraded_regime_final")
    wp0 = load_module(WP0_SCRIPT, "wp0_degraded_sweep")
    bd = load_module(BELIEF_SCRIPT, "belief_decomposition")
    return {"reg": reg, "mod_b": mod_b, "mod_a": mod_a, "deg": deg, "wp0": wp0,
            "bd": bd, "interp": mod_c.interp_lin}


def cells_by_id(wp0) -> dict[str, dict[str, Any]]:
    return {c["cell_id"]: c for c in wp0.CELLS}


def episode_seed(cell_index: int, role: str, i: int) -> int:
    return EPISODE_SEED_BASE + cell_index * 1_000_000 + ROLE_OFFSETS[role] + int(i)


def mu_grid(n: int = MU_GRID_POINTS) -> list[float]:
    lo, hi = 0.25, 1.15
    return [lo + (i + 0.5) / n * (hi - lo) for i in range(n)]


def mu_offgrid(n: int) -> list[float]:
    """Held-out mu points off the 12-point grid: midpoints between grid points."""
    g = mu_grid()
    mids = [0.5 * (g[i] + g[i + 1]) for i in range(len(g) - 1)]
    step = max(len(mids) // max(n, 1), 1)
    return mids[::step][:n]


def draw_mu(seed: int) -> float:
    rng = np.random.default_rng([SEED_BASE, 101, int(seed)])
    return float(rng.uniform(0.25, 1.15))


def jittered_distance(interp, reg, mu: float, seed: int) -> float:
    base = reg.d_of_mu(interp, mu)
    eps = float(np.random.default_rng([SEED_BASE, 777, int(seed)]).uniform(-reg.JITTER_D_M, reg.JITTER_D_M))
    return max(base + eps, reg.D_FLOOR_M)


def sample_vehicle_scales(seed: int) -> dict[str, float]:
    rng = np.random.default_rng([SEED_BASE, 555, int(seed)])
    return {k: float(rng.uniform(*r)) for k, r in VEH_RANGES.items()}


# ------------------------------------------------------------ behavior scripts


class BehaviorScript:
    """mu-decoupled scripted behavior: prefix + task segment.

    All schedule parameters come from rng([SEED_BASE, 303, seed]); mu is never
    read. Steering = centerline tracking (mod_a.centerline_steer) + a small
    prefix weave. Force ramps are open-loop; closed-loop speed tracking uses
    mu-free force caps so command sequences cannot encode mu.
    """

    def __init__(self, mods, variant: str, seed: int):
        rng = np.random.default_rng([SEED_BASE, 303, int(seed)])
        self.mod_a = mods["mod_a"]
        self.mod_b = mods["mod_b"]
        self.reg = mods["reg"]
        self.variant = variant
        # seed-derived mu-FREE lateral dither (sum of 3 sinusoid aim offsets,
        # full episode): masks the micro-scale deterministic decision-frame
        # leak (mu-correlated arrival time x slowly-decaying lateral state in
        # the UNdegraded geometry channels) with behavioral variance that is
        # orders of magnitude larger than the leak signal.
        amp = float(rng.uniform(0.06, 0.12))
        self._dither_a = rng.dirichlet(np.ones(3)) * amp
        self._dither_w = rng.uniform(0.5, 1.8, size=3)
        self._dither_phi = rng.uniform(0.0, 2.0 * np.pi, size=3)
        # stage-2 leak repair (M3216 pre-registered bounded data iteration):
        # seed-derived mu-FREE multi-sine SPEED schedule replaces the constant
        # tracking target in the standard task segment. Mechanism repaired
        # (measured on the stopped M3216 full run, delay cells linear OOF R^2
        # 0.13-0.30): decision tick ~ d(mu) (Spearman 0.93) x the constant-
        # target convergence transient left a mu-readable signature in the
        # longitudinal actuator/command channels (obs 8/11/3/7) at the
        # decision frame. The schedule phase-randomizes the longitudinal
        # state at any tick -- the exact mirror of the lateral-dither repair.
        # C3 episodes are NOT touched (their probes pass and the variant
        # requires the sub-limit constant-speed quiet segment).
        v_amp = float(rng.uniform(1.0, 2.25))
        self._vsched_a = rng.dirichlet(np.ones(3)) * v_amp
        self._vsched_w = rng.uniform(0.2, 1.2, size=3)
        self._vsched_phi = rng.uniform(0.0, 2.0 * np.pi, size=3)
        if variant == "c3":
            kind = "c3_ramp_release"
        else:
            kind = "fixed_speed" if rng.uniform() < 0.5 else "ramp_release"
        self.kind = kind
        self.params: dict[str, float] = {"kind_code": {"fixed_speed": 0, "ramp_release": 1,
                                                       "c3_ramp_release": 2}[kind]}
        if kind == "fixed_speed":
            self.params["v_target"] = float(rng.uniform(6.0, 8.5))  # multi-sine base
            self.params["ramp_rate"] = 0.0
            self.params["ramp_peak_n"] = 0.0
            self.params["ramp_t0"] = -1.0
            self.params["ramp_hold_steps"] = 0.0
        elif kind == "ramp_release":
            self.params["v_target"] = float(rng.uniform(6.0, 8.5))  # multi-sine base
            self.params["ramp_rate"] = float(rng.choice([6000.0, 20000.0]))
            self.params["ramp_peak_n"] = float(rng.uniform(0.5, 1.0) * 6000.0)
            self.params["ramp_t0"] = float(rng.integers(25, 36))
            self.params["ramp_hold_steps"] = float(rng.integers(8, 21))
        else:  # c3_ramp_release: excitation confined to t' < 1.0 s
            self.params["v_target"] = float(rng.uniform(5.5, 6.5))
            self.params["ramp_rate"] = 20000.0
            self.params["ramp_peak_n"] = 6000.0
            self.params["ramp_t0"] = 5.0
            self.params["ramp_hold_steps"] = 0.0  # release governed by C3_EXCITE_END_S
        self._f_cmd = 0.0
        self._ramp_done = False

    # -- helpers ---------------------------------------------------------------
    def _lateral_offset(self, t: int) -> float:
        s = t * DT
        return float(sum(a * math.sin(w * s + p) for a, w, p in
                         zip(self._dither_a, self._dither_w, self._dither_phi)))

    def _v_sched(self, tp: int) -> float:
        """mu-free multi-sine speed target for the standard task segment."""
        s = tp * DT
        wave = sum(a * math.sin(w * s + p) for a, w, p in
                   zip(self._vsched_a, self._vsched_w, self._vsched_phi))
        return float(np.clip(self.params["v_target"] + wave, 5.0, 9.5))

    def _steer(self, obs: np.ndarray, offset_m: float, j: int = 2,
               gain: float = 1.6, cap: float = 0.45) -> float:
        """Centerline pure-pursuit with a lateral aim offset (mirrors
        mod_b.CommitmentController._steer)."""
        lx = float(obs[12 + 2 * j]) * 80.0
        ly = float(obs[13 + 2 * j]) * 20.0
        rx = float(obs[28 + 2 * j]) * 80.0
        ry = float(obs[29 + 2 * j]) * 20.0
        xt, yt = 0.5 * (lx + rx), 0.5 * (ly + ry) + offset_m
        alpha = math.atan2(yt, max(xt, 1.0))
        dist = max(math.hypot(xt, yt), 2.0)
        steer_angle = math.atan2(2.0 * self.mod_b.WHEELBASE * math.sin(alpha), dist)
        return float(np.clip(gain * steer_angle / self.mod_b.MAX_STEER_RAD, -cap, cap))

    def _track(self, vx: float, v_target: float,
               drive_cap_n: float, brake_cap_n: float) -> tuple[float, float]:
        err = v_target - vx
        if err >= -0.15:
            thr01 = float(np.clip(0.55 * err, 0.0, drive_cap_n / 8200.0))
            brk01 = 0.0
        else:
            thr01 = 0.0
            brk01 = float(np.clip(-0.5 * err, 0.0, brake_cap_n / 6000.0))
        return 2.0 * thr01 - 1.0, 2.0 * brk01 - 1.0

    def act(self, t: int, obs: np.ndarray) -> np.ndarray:
        obs = np.asarray(obs, dtype=np.float64)
        vx = float(obs[0]) * 20.0
        steer = self._steer(obs, self._lateral_offset(t))
        if t < PREFIX_STEPS:
            s = t * DT
            cycle = s % 5.0
            if 1.0 <= cycle < 2.0:  # gentle mu-free brake pulse
                brk01 = (PREFIX_BRAKE_CAP_N / 6000.0) * min(cycle - 1.0, 0.4) / 0.4
                return np.array([steer, -1.0, 2.0 * brk01 - 1.0])
            if 2.5 <= cycle < 4.0:  # gentle re-acceleration
                thr01 = float(np.clip(0.55 * (8.5 - vx), 0.0, PREFIX_DRIVE_CAP_N / 8200.0))
                return np.array([steer, 2.0 * thr01 - 1.0, -1.0])
            thr01 = float(np.clip(0.45 * (8.0 - vx), 0.0, PREFIX_DRIVE_CAP_N / 8200.0))
            return np.array([steer, 2.0 * thr01 - 1.0, -1.0])

        tp = t - PREFIX_STEPS  # task-segment clock (steps)
        p = self.params
        if self.kind == "fixed_speed":
            thr, brk = self._track(vx, self._v_sched(tp), TRACK_DRIVE_CAP_N, TRACK_BRAKE_CAP_N)
            return np.array([steer, thr, brk])

        if self.kind == "c3_ramp_release":
            if tp < 5:
                thr, brk = self._track(vx, 8.0, C3_TRACK_DRIVE_CAP_N, TRACK_BRAKE_CAP_N)
                return np.array([steer, thr, brk])
            if tp * DT < C3_EXCITE_END_S - 0.2:  # release at 0.8 s task-clock: leaves
                # actuator-decay margin so truth excitation ends < 1.0 s
                self._f_cmd = min(self._f_cmd + p["ramp_rate"] * DT, p["ramp_peak_n"])
                return np.array([steer, -1.0, 2.0 * min(self._f_cmd / 6000.0, 1.0) - 1.0])
            thr, brk = self._track(vx, p["v_target"], C3_TRACK_DRIVE_CAP_N, TRACK_BRAKE_CAP_N)
            return np.array([steer, thr, brk])

        # ramp_release
        t0 = int(p["ramp_t0"])
        ramp_steps = int(math.ceil(p["ramp_peak_n"] / (p["ramp_rate"] * DT)))
        t_end = t0 + ramp_steps + int(p["ramp_hold_steps"])
        if tp < 25:
            thr, brk = self._track(vx, 8.0, TRACK_DRIVE_CAP_N, TRACK_BRAKE_CAP_N)
            return np.array([steer, thr, brk])
        if t0 <= tp < t_end and not self._ramp_done:
            self._f_cmd = min(self._f_cmd + p["ramp_rate"] * DT, p["ramp_peak_n"])
            return np.array([steer, -1.0, 2.0 * min(self._f_cmd / 6000.0, 1.0) - 1.0])
        if tp >= t_end:
            self._ramp_done = True
        thr, brk = self._track(vx, self._v_sched(tp), TRACK_DRIVE_CAP_N, TRACK_BRAKE_CAP_N)
        return np.array([steer, thr, brk])


# ------------------------------------------------------------- episode rollout


def make_episode_env(mods, cell: dict[str, Any], mu: float, seed: int, variant: str,
                     vehicle_rand: bool):
    reg, mod_b, deg, wp0 = mods["reg"], mods["mod_b"], mods["deg"], mods["wp0"]
    interp = mods["interp"]
    design = reg.make_design(mod_b, REVEAL)
    d_base = jittered_distance(interp, reg, mu, seed)
    d_total = d_base + PREFIX_DIST_OFFSET_M + (C3_EXTRA_DIST_M if variant == "c3" else 0.0)
    level = mod_b.LevelSpec(mu=mu, d_lo=d_total, d_hi=d_total,
                            entry_speed=reg.v_star(interp, mu))
    cfg = mod_b.level_env_config(design, level)
    cfg["max_steps"] = MAX_STEPS_C3 if variant == "c3" else MAX_STEPS_STD
    scales = None
    if vehicle_rand:
        scales = sample_vehicle_scales(seed)
        cfg["randomization"].update({
            "mass_scale_range": [scales["mass_scale"]] * 2,
            "brake_scale_range": [scales["brake_scale"]] * 2,
            "drive_scale_range": [scales["drive_scale"]] * 2,
            "tire_stiffness_scale_range": [scales["tire_stiffness_scale"]] * 2,
            "actuator_tau_scale_range": [scales["actuator_tau_scale"]] * 2,
        })
    env = wp0.make_degraded_env_cfg(deg, cfg, cell["degradation"])
    return env, scales, d_total


def run_episode(mods, cell: dict[str, Any], mu: float, seed: int, variant: str,
                role: str, vehicle_rand: bool) -> dict[str, Any]:
    reg, bd = mods["reg"], mods["bd"]
    env, scales, d_total = make_episode_env(mods, cell, mu, seed, variant, vehicle_rand)
    mass_scale = scales["mass_scale"] if scales else 1.0
    cap_r = reg.TIRE_CAP * mu * reg.FZR * mass_scale  # truth rear capacity (harness-only)
    behavior = BehaviorScript(mods, variant, seed)
    rls = bd.VehicleRLS(r_noise_ax=max((15.0 * float(cell["degradation"].get("noise_std", 0.0))) ** 2, 0.04))
    frames: list[np.ndarray] = []
    decision_tick = -1
    last_excitation_step = -1
    prefix_max_util = 0.0
    initial_transient_max_util = 0.0
    task_max_util_nonexcite = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        frames.append(np.asarray(obs, dtype=np.float32).copy())
        max_steps = MAX_STEPS_C3 if variant == "c3" else MAX_STEPS_STD
        for t in range(max_steps):
            obs_arr = np.asarray(obs, dtype=np.float64)
            if t < PREFIX_STEPS:
                rls.update_obs(obs_arr)
            action = behavior.act(t, obs_arr)
            obs, _, terminated, truncated, _ = env.step(np.asarray(action, dtype=np.float64))
            frames.append(np.asarray(obs, dtype=np.float32).copy())
            forces = env.last_forces  # EnvShim -> base env truth (harness-only)
            util = math.hypot(float(forces.fx_rear), float(forces.fy_rear)) / max(cap_r, 1.0)
            frame_idx = t + 1
            if frame_idx <= PREFIX_TRANSIENT_SKIP:
                initial_transient_max_util = max(initial_transient_max_util, util)
            elif frame_idx <= PREFIX_STEPS:
                prefix_max_util = max(prefix_max_util, util)
            if util > EXCITATION_UTIL_BAR:
                last_excitation_step = frame_idx
            elif frame_idx > PREFIX_STEPS:
                task_max_util_nonexcite = max(task_max_util_nonexcite, util)
            if decision_tick < 0 and float(frames[-1][44]) > 0.5:
                decision_tick = frame_idx
            if decision_tick >= 0 and frame_idx >= decision_tick + POST_DECISION_FRAMES:
                break
            if terminated or truncated:
                break
    finally:
        env.close()
    kb_hat, kd_hat = rls.kappas
    decision_time_task_s = ((decision_tick - PREFIX_STEPS) * DT) if decision_tick >= 0 else float("nan")
    has_excitation = last_excitation_step >= 0
    if decision_tick >= 0 and has_excitation:
        gap_s = (decision_tick - last_excitation_step) * DT
    elif decision_tick >= 0:
        gap_s = decision_tick * DT  # no excitation at all: gap = full episode age
    else:
        gap_s = float("nan")
    return {
        "frames": np.stack(frames).astype(np.float32),
        "mu": float(mu),
        "seed": int(seed),
        "role": role,
        "variant": variant,
        "decision_tick": int(decision_tick),
        "decision_time_task_s": float(decision_time_task_s),
        "last_excitation_step": int(last_excitation_step),
        "has_excitation": bool(has_excitation),
        "excitation_to_decision_gap_s": float(gap_s),
        "prefix_max_util": float(prefix_max_util),
        "initial_transient_max_util": float(initial_transient_max_util),
        "task_max_util_nonexcite": float(task_max_util_nonexcite),
        "kappa_b_hat": float(kb_hat),
        "kappa_d_hat": float(kd_hat),
        "rls_frames": int(rls.n_frames),
        "behavior_params": dict(behavior.params),
        "d_total": float(d_total),
    }


# ------------------------------------------------------------------ leak probe


def _fold_indices(n: int, folds: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng([SEED_BASE, 909, seed])
    perm = rng.permutation(n)
    return [perm[f::folds] for f in range(folds)]


def _standardize_fold(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-fold standardization with near-constant columns ZEROED (sd <= 1e-6 on
    the train fold) and the test side clipped to +/-10 sd: many decision-frame
    channels are geometry constants whose 1e-7-scale jitter would otherwise be
    amplified into out-of-fold garbage."""
    mu_x, sd_x = x_train.mean(0), x_train.std(0)
    mask = sd_x > 1e-6
    xt = np.zeros_like(x_train)
    xv = np.zeros_like(x_test)
    xt[:, mask] = (x_train[:, mask] - mu_x[mask]) / sd_x[mask]
    xv[:, mask] = np.clip((x_test[:, mask] - mu_x[mask]) / sd_x[mask], -10.0, 10.0)
    return xt, xv


def linear_probe_r2(x: np.ndarray, y: np.ndarray, folds: int = PROBE_FOLDS,
                    ridge_lambda: float = 1.0) -> float:
    """Out-of-fold R^2 of a ridge regression decision frame -> mu."""
    n = len(y)
    if n < folds + 2:
        return float("nan")
    y_hat = np.zeros(n)
    fold_idx = _fold_indices(n, folds, 1)
    for test in fold_idx:
        train = np.setdiff1d(np.arange(n), test)
        xt, xv = _standardize_fold(x[train], x[test])
        xt1 = np.hstack([xt, np.ones((len(xt), 1))])
        xv1 = np.hstack([xv, np.ones((len(xv), 1))])
        a = xt1.T @ xt1 + ridge_lambda * np.eye(xt1.shape[1])
        w = np.linalg.solve(a, xt1.T @ y[train])
        y_hat[test] = xv1 @ w
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / max(ss_tot, 1e-12)


def mlp_probe_r2(x: np.ndarray, y: np.ndarray, folds: int = PROBE_FOLDS,
                 hidden: int = MLP_HIDDEN, epochs: int = MLP_EPOCHS) -> float:
    """Out-of-fold R^2 of a small MLP probe (secondary, catches nonlinear leaks)."""
    import torch
    import torch.nn as nn

    n = len(y)
    if n < folds + 2:
        return float("nan")
    y_hat = np.zeros(n)
    fold_idx = _fold_indices(n, folds, 2)
    for fi, test in enumerate(fold_idx):
        torch.manual_seed(SEED_BASE + 13 * fi)
        train = np.setdiff1d(np.arange(n), test)
        xt_np, xv_np = _standardize_fold(x[train], x[test])
        xt = torch.tensor(xt_np, dtype=torch.float32)
        xv = torch.tensor(xv_np, dtype=torch.float32)
        yt = torch.tensor(y[train], dtype=torch.float32).unsqueeze(1)
        net = nn.Sequential(nn.Linear(x.shape[1], hidden), nn.ReLU(),
                            nn.Linear(hidden, 1))
        opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
        for _ in range(epochs):
            opt.zero_grad()
            loss = nn.functional.mse_loss(net(xt), yt)
            loss.backward()
            opt.step()
        with torch.no_grad():
            y_hat[test] = net(xv).squeeze(1).numpy()
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / max(ss_tot, 1e-12)


def probe_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in records if r["decision_tick"] >= 0]
    if len(valid) < PROBE_FOLDS + 2:
        return {"n": len(valid), "status": "insufficient", "gate_pass": None}
    x = np.stack([r["frames"][r["decision_tick"]] for r in valid]).astype(np.float64)
    y = np.array([r["mu"] for r in valid], dtype=np.float64)
    r2_lin = linear_probe_r2(x, y)
    r2_mlp = mlp_probe_r2(x, y)
    return {
        "n": len(valid),
        "r2_linear_oof": round(r2_lin, 4),
        "r2_mlp_oof": round(r2_mlp, 4),
        "bar": PROBE_R2_BAR,
        "gate_pass": bool(r2_lin <= PROBE_R2_BAR and r2_mlp <= PROBE_R2_BAR),
    }


def c3_telemetry_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    c3 = [r for r in records if r["variant"] == "c3" and r["decision_tick"] >= 0]
    if not c3:
        return {"n": 0, "gate_pass": None}
    excite_end_bar = PREFIX_STEPS * DT + C3_EXCITE_END_S
    violations = []
    for r in c3:
        ok_decision = r["decision_time_task_s"] >= C3_DECISION_MIN_S
        ok_excite_window = (not r["has_excitation"]) or \
            (r["last_excitation_step"] * DT <= excite_end_bar)
        ok_gap = (not r["has_excitation"]) or (r["excitation_to_decision_gap_s"] > C3_GAP_BAR_S)
        if not (ok_decision and ok_excite_window and ok_gap):
            violations.append({"seed": r["seed"], "mu": r["mu"],
                               "decision_time_task_s": r["decision_time_task_s"],
                               "last_excitation_step": r["last_excitation_step"],
                               "gap_s": r["excitation_to_decision_gap_s"]})
    excited = [r for r in c3 if r["has_excitation"]]
    return {
        "n": len(c3),
        "n_with_excitation": len(excited),
        "min_decision_time_task_s": round(min(r["decision_time_task_s"] for r in c3), 3),
        "min_gap_s_excited": (round(min(r["excitation_to_decision_gap_s"] for r in excited), 3)
                              if excited else None),
        "max_excitation_time_s": (round(max(r["last_excitation_step"] for r in excited) * DT, 3)
                                  if excited else None),
        "bars": {"decision_min_s": C3_DECISION_MIN_S, "gap_bar_s": C3_GAP_BAR_S,
                 "excite_end_task_s": C3_EXCITE_END_S},
        "violations": violations,
        "gate_pass": bool(not violations),
    }


# -------------------------------------------------------------------- dataset


def save_cell_npz(path: Path, records: list[dict[str, Any]]) -> None:
    t_max = max(len(r["frames"]) for r in records)
    n = len(records)
    obs = np.zeros((n, t_max, OBS_DIM), dtype=np.float32)
    for i, r in enumerate(records):
        obs[i, : len(r["frames"])] = r["frames"]
    role_code = {"train": 0, "sel": 1, "val": 2}
    variant_code = {"standard": 0, "c3": 1}
    bp_keys = ("kind_code", "v_target", "ramp_rate", "ramp_peak_n", "ramp_t0", "ramp_hold_steps")
    np.savez_compressed(
        path,
        obs=obs,
        length=np.array([len(r["frames"]) for r in records], dtype=np.int32),
        decision_tick=np.array([r["decision_tick"] for r in records], dtype=np.int32),
        mu=np.array([r["mu"] for r in records], dtype=np.float32),
        seed=np.array([r["seed"] for r in records], dtype=np.int64),
        role=np.array([role_code[r["role"]] for r in records], dtype=np.int8),
        variant=np.array([variant_code[r["variant"]] for r in records], dtype=np.int8),
        mu_on_grid=np.array([r.get("mu_on_grid", False) for r in records], dtype=bool),
        decision_time_task_s=np.array([r["decision_time_task_s"] for r in records], dtype=np.float32),
        last_excitation_step=np.array([r["last_excitation_step"] for r in records], dtype=np.int32),
        excitation_to_decision_gap_s=np.array([r["excitation_to_decision_gap_s"] for r in records],
                                              dtype=np.float32),
        prefix_max_util=np.array([r["prefix_max_util"] for r in records], dtype=np.float32),
        initial_transient_max_util=np.array([r["initial_transient_max_util"] for r in records],
                                            dtype=np.float32),
        kappa_b_hat=np.array([r["kappa_b_hat"] for r in records], dtype=np.float32),
        kappa_d_hat=np.array([r["kappa_d_hat"] for r in records], dtype=np.float32),
        behavior_params=np.array([[r["behavior_params"][k] for k in bp_keys] for r in records],
                                 dtype=np.float32),
        behavior_param_keys=np.array(bp_keys),
        prefix_steps=np.array([PREFIX_STEPS], dtype=np.int32),
    )


def collect_cell(mods, cell: dict[str, Any], cell_index: int, counts: dict[str, int],
                 vehicle_rand: bool, log=print) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    # standard episodes: train/sel continuous mu, val on grid + off-grid points
    for role, n in (("train", counts["train"]), ("sel", counts["sel"])):
        for i in range(n):
            seed = episode_seed(cell_index, role, i)
            rec = run_episode(mods, cell, draw_mu(seed), seed, "standard", role, vehicle_rand)
            rec["mu_on_grid"] = False
            records.append(rec)
    val_mus = [(m, True) for m in mu_grid()] + [(m, False) for m in mu_offgrid(counts["val_offgrid"])]
    for i, (mu, on_grid) in enumerate(val_mus):
        seed = episode_seed(cell_index, "val", i)
        rec = run_episode(mods, cell, mu, seed, "standard", "val", vehicle_rand)
        rec["mu_on_grid"] = on_grid
        records.append(rec)
    # C3 variant episodes (own contiguous index block inside the same streams)
    for role, n, base in (("train", counts["c3_train"], 100_000), ("val", counts["c3_val"], 100_000)):
        for i in range(n):
            seed = episode_seed(cell_index, role, base + i)
            rec = run_episode(mods, cell, draw_mu(seed), seed, "c3", role, vehicle_rand)
            rec["mu_on_grid"] = False
            records.append(rec)

    std = [r for r in records if r["variant"] == "standard"]
    c3 = [r for r in records if r["variant"] == "c3"]
    summary = {
        "cell_id": cell["cell_id"],
        "degradation": cell["degradation"],
        "n_episodes": len(records),
        "n_invalid_decision": sum(1 for r in records if r["decision_tick"] < 0),
        "probe_gate_standard": probe_gate(std),
        "probe_gate_c3": probe_gate(c3),
        "c3_telemetry": c3_telemetry_gate(records),
        "prefix_max_util_overall": round(max(r["prefix_max_util"] for r in records), 4),
        "initial_transient_max_util_overall": round(
            max(r["initial_transient_max_util"] for r in records), 4),
        "decision_tick_mean": round(float(np.mean([r["decision_tick"] for r in records
                                                   if r["decision_tick"] >= 0])), 1),
        "kappa_b_hat_median": round(float(np.median([r["kappa_b_hat"] for r in records])), 4),
        "kappa_d_hat_median": round(float(np.median([r["kappa_d_hat"] for r in records])), 4),
    }
    log(f"  {cell['cell_id']:<10} n={summary['n_episodes']} invalid={summary['n_invalid_decision']} "
        f"probe_lin={summary['probe_gate_standard'].get('r2_linear_oof')} "
        f"probe_mlp={summary['probe_gate_standard'].get('r2_mlp_oof')} "
        f"c3_gap_pass={summary['c3_telemetry']['gate_pass']} "
        f"prefix_util_max={summary['prefix_max_util_overall']}", flush=True)
    return records, summary


# ------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="smoke: 1 cell, small counts")
    parser.add_argument("--full", action="store_true", help="all 4 eligible cells, full counts")
    parser.add_argument("--cells", type=str, default=None,
                        help="comma-separated cell ids (default: eligible list)")
    parser.add_argument("--vehicle-randomization", action="store_true",
                        help="per-episode vehicle scales (default OFF, matching the frozen M3215 panel)")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    if args.quick == args.full:
        parser.error("exactly one of --quick / --full is required")

    counts = ({"train": 32, "sel": 10, "val_offgrid": 6, "c3_train": 8, "c3_val": 4}
              if args.quick else
              {"train": 240, "sel": 40, "val_offgrid": 24, "c3_train": 80, "c3_val": 24})
    run_dir = args.output_dir or (DEFAULT_RUN_DIR.parent / (DEFAULT_RUN_DIR.name + "_quick")
                                  if args.quick else DEFAULT_RUN_DIR)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    mods = load_stack()
    all_cells = cells_by_id(mods["wp0"])
    cell_ids = ([c.strip() for c in args.cells.split(",")] if args.cells
                else (["delay5"] if args.quick else list(ELIGIBLE_CELL_IDS)))
    for cid in cell_ids:
        assert cid in ELIGIBLE_CELL_IDS, f"{cid} is not in the frozen eligible list {ELIGIBLE_CELL_IDS}"

    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp1_data_pipeline",
        "generated_by": "scripts/feasibility_audit/wp1_data_pipeline.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(args.quick),
        "seed_base": SEED_BASE,
        "episode_seed_formula": ("20270101*100 + cell_index*1_000_000 + role_offset + i; "
                                 f"role_offsets={ROLE_OFFSETS}; mu rng [20270101,101,seed]; "
                                 "behavior rng [20270101,303,seed]; jitter rng [20270101,777,seed]"),
        "eligible_cells_frozen_by": "docs/m3215-wp0-degraded-sweep-bridge-validation.md Section 7",
        "cells_requested": cell_ids,
        "vehicle_randomization": bool(args.vehicle_randomization),
        "prefix": {"seconds": PREFIX_S, "brake_cap_n": PREFIX_BRAKE_CAP_N,
                   "drive_cap_n": PREFIX_DRIVE_CAP_N, "dist_offset_m": PREFIX_DIST_OFFSET_M},
        "c3": {"extra_dist_m": C3_EXTRA_DIST_M, "excite_end_task_s": C3_EXCITE_END_S,
               "gap_bar_s": C3_GAP_BAR_S, "decision_min_s": C3_DECISION_MIN_S},
        "excitation_util_bar_truth": EXCITATION_UTIL_BAR,
        "counts": counts,
        "cells": [],
        "status": "running",
    }

    eligible_idx = {cid: i for i, cid in enumerate(ELIGIBLE_CELL_IDS)}
    print(f"[wp1 data] cells={cell_ids} counts={counts}", flush=True)
    for cid in cell_ids:
        records, summary = collect_cell(mods, all_cells[cid], eligible_idx[cid],
                                        counts, args.vehicle_randomization)
        save_cell_npz(run_dir / f"{cid}.npz", records)
        summary["npz"] = str(run_dir / f"{cid}.npz")
        payload["cells"].append(summary)

    gates = [c["probe_gate_standard"].get("gate_pass") for c in payload["cells"]]
    c3_gates = [c["c3_telemetry"].get("gate_pass") for c in payload["cells"]]
    payload["dataset_gate_pass_all_cells"] = bool(all(g is True for g in gates))
    payload["c3_telemetry_pass_all_cells"] = bool(all(g is True for g in c3_gates))
    payload["elapsed_s"] = round(time.time() - started, 1)
    payload["status"] = "completed"
    (run_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"results -> {run_dir / 'summary.json'}", flush=True)
    print("HEADLINE: dataset_gate=" + str(payload["dataset_gate_pass_all_cells"])
          + f" c3_telemetry={payload['c3_telemetry_pass_all_cells']}"
          + f" | elapsed {payload['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()
