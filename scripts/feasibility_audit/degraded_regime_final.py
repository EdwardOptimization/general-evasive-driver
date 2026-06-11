"""Final measurement of the capability-boundary-tracking thesis: does the value
of a persistent capability belief RE-EMERGE under observation degradation?

Context (docs/capability-boundary-tracking-thesis-2026-06.md Section 7,
docs/selfid-threshold-seeking-regime-2026-06.md): under clean noiseless
observation, VoI(belief) = 0.000 at every reveal window -- the belief-free
threshold seeker matches the per-mu oracle everywhere, because incipient-slip
detection is fast (140-400 ms). Detection latency is the single support of
belief irrelevance. The M3214 observation-degradation wrapper (delay/noise on
ego channels 0-8, geometry untouched) exists precisely to lengthen that
latency. This script runs the two TIGHTEST reveal tiers of the regime
measurement (9.5 and 12 m) over a degradation matrix:

    delay_steps in {0, 5, 12, 25}   (0 - 0.5 s at dt=0.02)
  x noise_std   in {0, 0.05}        (per-channel, ego response channels 0-8)

and asks, per cell, what the per-mu oracle (belief upper bound) buys over the
best belief-free seeker, what a +/-0.2 prior-granted seeker buys over the
plain seeker, and what embedded detection buys over no-detection fixed plans.

Controller family: REUSED from scripts/feasibility_audit/ramp_policy_voi_regime.py
(loaded as a module), with two degradation-honesty additions:

  1. Per-cell detector re-calibration: the single-frame shortfall detector's
     threshold tau is re-calibrated per degradation cell on sub-limit ramps
     (the noise floor of the shortfall signal rises under obs noise); seekers
     get the calibrated tau in their selection grid, so "an untuned seeker"
     cannot fake belief value.
  2. A smoothing option (W-frame moving average over ego channels 0-8 before
     the detector math) competes in the seeker selection grid in noise cells:
     the standard engineering response to sensor noise, whose cost is exactly
     the latency the thesis is about.

All controller classes (including the per-mu oracle) run on the SAME degraded
observation stream of each cell, so VoI(belief) = oracle - seeker isolates
what KNOWING mu is worth given identical sensing. The oracle never uses the
detector, so it is structurally (near-)immune to degradation; fixed plans use
observations only for speed tracking; the prior seeker's bin-floor start and
bin-floor fallback do not depend on detection. The environment truth is never
degraded -- only what the controller reads.

Mechanism evidence: Measurement A's detection-latency protocol
(scripts/feasibility_audit/slip_onset_detectability.py, RLS SlipOnsetDetector,
per-cell tau re-calibration via its own calibrate_tau) is re-run small-scale
on the degraded streams to show HOW detection latency grows with degradation.

Pre-registered decision rule (written before the run):
  - if any degraded cell has VoI(belief) >= 0.15 on validation seeds ->
    belief value re-emerges under degraded sensing (report the sensor
    condition it corresponds to);
  - if all degraded cells < 0.15 -> the constructive null closes completely:
    passive fast adaptation + reflex is self-sufficient in this simulator
    universe even under degraded sensing of this depth.

Hard constraints: pure CPU numpy, zero training, deterministic seeds, new
files only, no git operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/degraded_regime_final.py
    PYTHONPATH=src python scripts/feasibility_audit/degraded_regime_final.py --quick
"""

from __future__ import annotations

import argparse
import collections
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
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
SLIP_SCRIPT = REPO / "scripts/feasibility_audit/slip_onset_detectability.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/degraded_regime_final.json"
RUN_DIR = REPO / "runs/feasibility_audit/degraded_regime_final"

SEED_BASE = 20260620  # fresh stream (regime=20260618); regime episode seeds are
# intentionally REUSED via reg.TierMeasurement.seed_for (20260618-based) so the
# clean cell (delay 0, noise 0) is a bit-for-bit replication anchor of the
# original measurement (the wrapper is identity there).

DT = 0.02
DELAYS_DEFAULT = (0, 5, 12, 25)
NOISES_DEFAULT = (0.0, 0.05)
REVEALS_DEFAULT = (9.5, 12.0)
VOI_RESURRECTION_THRESHOLD = 0.15

# trimmed seeker grid (justified by the clean-run selection results in
# experiments/feasibility_audit/ramp_policy_voi_regime.json: rate 800 N/s and
# strategy 'retry' never uniquely won at 9.5/12; deltas and dv both mattered)
SEEKER_RATES = (2000.0, 6000.0, 20000.0)
SEEKER_DELTAS = (0.06, 0.15)
SEEKER_DVS = (0.0, 0.75)
PRIOR_RATES = (6000.0, 20000.0)
PRIOR_DVS = (0.0, 0.75)
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)

# detector tau calibration
CALIB_MUS = (0.5, 0.9)
CALIB_SEEDS_PER_MU = 3
CALIB_STEPS = 230
CALIB_BRAKE_LIMIT_FRAC = 0.55  # commanded brake cap as a fraction of the tire limit
CALIB_DRIVE_LIMIT_FRAC = 0.50
TAU_SAFETY = 1.2
TAU_FLOOR = 0.08
# moving-average windows offered to seekers in noise cells: obs-noise std 0.05
# on ax is ~0.75 m/s^2 (~1090 N force-equivalent), so useful single-frame-rule
# thresholds need substantial averaging; the window cost IS detection latency.
SMOOTH_WINDOWS = (5, 12, 25)
ALL_WINDOWS = (1,) + SMOOTH_WINDOWS

# latency rerun (Measurement A protocol on degraded streams)
LAT_RATES = (0.10, 0.40)
LAT_N_PER_RATE = 4
LAT_N_CALIB = 6
LAT_N_SUBLIMIT = 4

CLAIM_BOUNDARY = (
    "Feasibility-audit policy-family VoI measurement only: the scripted threshold-seeking "
    "controller family of ramp_policy_voi_regime.py (per-mu oracle ramp, belief-free seekers "
    "with per-cell re-calibrated shortfall detectors, +/-0.2 prior-granted seekers, "
    "no-detection fixed plans) is rolled out on the B2K2_final family at reveal 9.5/12 m with "
    "the M3214 observation-degradation wrapper (delay/noise on ego channels 0-8). No driver "
    "promotion, training, repair-success, gate-validity, paper, or self-ID capability claim."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ----------------------------------------------------------- degraded env glue


class EnvShim:
    """Route reset/step/close through the ObservationDegradationWrapper and
    everything else (base_obs_dim, params, state, last_forces,
    termination_reason, ...) to the base env: gymnasium 1.3 wrappers do not
    forward attributes. The controller/detector only ever see wrapper output;
    truth readouts (used by harness-only code) come from the base env."""

    def __init__(self, env):
        self._env = env
        self._base = env.unwrapped

    def reset(self, **kw):
        return self._env.reset(**kw)

    def step(self, action):
        return self._env.step(action)

    def close(self):
        return self._env.close()

    def __getattr__(self, name):
        return getattr(self._base, name)


def make_degraded_env(reg, mod_b, cfg_dict: dict[str, Any], delay_steps: int, noise_std: float) -> EnvShim:
    from autodrift.config import build_env_config
    from autodrift.observation_degradation_wrapper import make_env_from_config

    cfg_dict = dict(cfg_dict)
    cfg_dict["observation_degradation"] = {"delay_steps": int(delay_steps), "noise_std": float(noise_std)}
    env = make_env_from_config(build_env_config(cfg_dict))
    shim = EnvShim(env)
    assert shim.base_obs_dim == mod_b.OBS_DIM, f"obs layout changed: {shim.base_obs_dim}"
    return shim


def make_degraded_pool(reg, mod_b, interp, design, delay_steps: int, noise_std: float):
    """reg.EnvPool with env construction swapped to the degradation wrapper
    (identical construction path for ALL cells including delay0/noise0)."""

    class DegradedEnvPool(reg.EnvPool):
        def env_for(self, mu: float, seed: int):
            key = (round(mu, 6), int(seed))
            if key not in self._cache:
                d = reg.jittered_distance(self.interp, mu, seed)
                level = self.mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d,
                                             entry_speed=reg.v_star(self.interp, mu))
                cfg_dict = self.mod_b.level_env_config(self.design, level)
                self._cache[key] = make_degraded_env(reg, self.mod_b, cfg_dict, delay_steps, noise_std)
            return self._cache[key]

    return DegradedEnvPool(mod_b, interp, design)


# ----------------------------------------------- degradation-aware detector/controller


def make_classes(reg):
    """Subclasses of the regime module's detector/controller (module is loaded
    dynamically, so the subclasses are built here)."""

    class DegradationAwareDetector(reg.ShortfallDetector):
        """reg.ShortfallDetector with an optional W-frame moving average over
        the ego channels 0-8 BEFORE the single-frame shortfall math (gates
        included). W=1 reproduces the original detector EXACTLY (clean-cell
        replication anchor). For W>1 the actuator branch (brake vs drive) must
        be unanimous over the whole raw window, otherwise the frame is treated
        as force-free: averaging across a brake<->drive transition mixes a
        decaying applied force with an opposite-sign response and produces
        fake shortfall ~1.0 (seen in calibration), which is branch
        misclassification, not signal. tau is the per-cell re-calibrated
        threshold."""

        BRAKE_ON_N = 400.0
        DRIVE_ON_N = 600.0

        def __init__(self, tau: float, smooth_window: int = 1):
            self.smooth_window = max(int(smooth_window), 1)
            self._ego_hist: collections.deque = collections.deque(maxlen=self.smooth_window)
            super().__init__(tau)

        def reset(self) -> None:
            self._ego_hist.clear()
            super().reset()

        def update(self, obs: np.ndarray) -> None:
            if self.smooth_window > 1:
                obs = np.asarray(obs, dtype=np.float64)
                self._ego_hist.append(obs[:9].copy())
                hist = np.asarray(self._ego_hist, dtype=np.float64)
                smoothed = obs.copy()
                smoothed[:9] = hist.mean(axis=0)
                all_brake = bool(np.all(hist[:, 8] * reg.MAX_BRAKE > self.BRAKE_ON_N))
                all_drive = bool(np.all(hist[:, 7] * reg.MAX_DRIVE > self.DRIVE_ON_N))
                if not (all_brake or all_drive):
                    # force the "neither branch" path in the parent update
                    smoothed[7] = 0.0
                    smoothed[8] = 0.0
                obs = smoothed
            super().update(obs)

    class DegradedRampController(reg.RampPolicyController):
        """reg.RampPolicyController with the detector swapped for the
        degradation-aware variant (smoothing window is a selection-grid knob)."""

        def __init__(self, *args, smooth_window: int = 1, **kw):
            super().__init__(*args, **kw)
            self.detector = DegradationAwareDetector(self.detector.tau, smooth_window)

    return DegradationAwareDetector, DegradedRampController


# --------------------------------------------------------- per-cell tau calibration


def calibrate_cell_tau(reg, mod_b, mod_a, interp, detector_cls, delay_steps: int,
                       noise_std: float, quick: bool) -> dict[str, Any]:
    """Sub-limit brake ramp + gentle drive episodes on the degraded stream with
    tau=inf detectors (all smoothing windows in parallel); the observed
    max_shortfall is the cell's noise floor. tau_cal = max(1.2*max, 0.08).
    Harness-only privilege: the sub-limit caps use the true mu (the detector
    never sees it), exactly as in Measurement A's calibration."""
    design = reg.make_design(mod_b, 9.5)
    pool = make_degraded_pool(reg, mod_b, interp, design, delay_steps, noise_std)
    maxima: dict[int, list[float]] = {w: [] for w in ALL_WINDOWS}
    n_eps = 0
    try:
        mus = CALIB_MUS if not quick else (0.9,)
        n_seeds = CALIB_SEEDS_PER_MU if not quick else 1
        for mu in mus:
            f_limit = reg.TIRE_CAP * mu * reg.FZR
            brake_cap_n = CALIB_BRAKE_LIMIT_FRAC * f_limit
            drive_cap01 = min(CALIB_DRIVE_LIMIT_FRAC * f_limit / reg.MAX_DRIVE, 1.0)
            for j in range(n_seeds):
                seed = SEED_BASE * 10 + int(mu * 100) * 101 + j
                env = pool.env_for(mu, seed)
                obs, _ = env.reset(seed=seed)
                dets = {w: detector_cls(1e9, w) for w in ALL_WINDOWS}
                f_cmd = 0.0
                for t in range(CALIB_STEPS):
                    obs_arr = np.asarray(obs, dtype=np.float64)
                    for det in dets.values():
                        det.update(obs_arr)
                    vx = float(obs_arr[0]) * 20.0
                    steer = mod_a.centerline_steer(obs_arr)
                    if t < 15:
                        thr01 = float(np.clip(0.55 * (reg.V0 - vx), 0.0, drive_cap01))
                        action = [steer, 2.0 * thr01 - 1.0, -1.0]
                    elif t < 140 and vx > 2.5:
                        f_cmd = min(f_cmd + 3000.0 * DT, brake_cap_n)
                        action = [steer, -1.0, 2.0 * min(f_cmd / reg.MAX_BRAKE, 1.0) - 1.0]
                    else:
                        thr01 = float(np.clip(0.55 * (reg.V0 - vx), 0.0, drive_cap01))
                        action = [steer, 2.0 * thr01 - 1.0, -1.0]
                    obs, _, terminated, truncated, _ = env.step(np.asarray(action, dtype=np.float64))
                    if terminated or truncated:
                        break
                n_eps += 1
                for w, det in dets.items():
                    maxima[w].append(float(det.max_shortfall))
    finally:
        pool.close()
    out = {"n_episodes": n_eps, "delay_steps": delay_steps, "noise_std": noise_std,
           "brake_cap_limit_frac": CALIB_BRAKE_LIMIT_FRAC, "safety_factor": TAU_SAFETY,
           "tau_floor": TAU_FLOOR}
    for w in ALL_WINDOWS:
        mx = max(maxima[w]) if maxima[w] else 0.0
        out[f"w{w}"] = {"max_signal": round(mx, 4),
                        "tau": round(max(TAU_SAFETY * mx, TAU_FLOOR), 4)}
    return out


def seeker_tau_variants(noise_std: float, cal: dict[str, Any]) -> list[tuple[int, float]]:
    """(smooth_window, tau) selection-grid variants for one cell. Noise-free
    cells keep the original clean-run grid (the shortfall stream is only
    time-shifted by delay; calibration confirms the floor). Noise cells get the
    re-calibrated raw arm (W=1: expected to be effectively non-detecting, the
    honest 'untuned protocol' fallback) plus re-calibrated averaged arms at
    every window -- selection seeds pick the latency/threshold trade-off."""
    if noise_std <= 0.0:
        variants = [(1, 0.08), (1, 0.18)]
        tau1 = cal["w1"]["tau"]
        if tau1 > 0.18:
            variants.append((1, round(tau1, 3)))
        return variants
    variants = [(w, round(cal[f"w{w}"]["tau"], 3)) for w in ALL_WINDOWS]
    seen, out = set(), []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


# ------------------------------------------------------------------ cell measurement


def measure_cell(reg, mod_b, interp, design, reveal: float, delay_steps: int, noise_std: float,
                 mus: list[float], sel_seeds: list[int], val_seeds: list[int],
                 rows_out: list[dict[str, Any]], controller_cls, cal: dict[str, Any],
                 clean_oracle_anchor: dict[str, float] | None, quick: bool) -> dict[str, Any]:
    """One (reveal tier, degradation cell): the trimmed controller zoo with
    selection -> validation, mirroring reg.measure_tier. Episode seeds reuse
    reg.TierMeasurement.seed_for (20260618 stream) so the clean cell replicates
    the original regime measurement, and episode geometry is IDENTICAL across
    cells (jitter keyed by rollout seed only) -- the clean-cell oracle is the
    degradation-free anchor on the same episodes."""
    tm = reg.TierMeasurement(mod_b, interp, design, 0, reveal, mus, sel_seeds, val_seeds, rows_out)
    tm.pool.close()
    tm.pool = make_degraded_pool(reg, mod_b, interp, design, delay_steps, noise_std)
    n_pts = len(mus)
    cell_tag = {"delay_steps": delay_steps, "noise_std": noise_std}

    def ramp(name: str, smooth_window: int = 1, **kw) -> Callable[[], Any]:
        return lambda: controller_cls(mod_b, interp, design, name, smooth_window=smooth_window, **kw)

    # [1] belief-free seekers (per-cell re-calibrated detector variants)
    variants = seeker_tau_variants(noise_std, cal)
    rates = SEEKER_RATES if not quick else (6000.0, 20000.0)
    deltas = SEEKER_DELTAS if not quick else (0.06,)
    dvs = SEEKER_DVS
    variant_of: dict[str, tuple[int, float]] = {}
    for r in rates:
        for w, tau in variants:
            for delta in deltas:
                for dv in dvs:
                    name = f"seeker_r{r:g}_w{w}_t{tau:g}_d{delta:g}_v{dv:+g}"
                    variant_of[name] = (w, tau)
                    tm.register(name, "seeker",
                                ramp(name, smooth_window=w, mode="seeker", ramp_rate=r, tau=tau,
                                     backoff=delta, strategy="hold", dv=dv))
    # no-detection fixed plans (immune control arms)
    for v in (reg.FIXED_SPEED_GRID if not quick else (4.5, 7.5, 10.5)):
        plan = mod_b.PlanSpec(name=f"fixed_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        tm.register(plan.name, "fixed_speed", (lambda p=plan: mod_b.CommitmentController(p, design)))
    for frac, hold_s in (reg.FIXED_RAMP_GRID if not quick else reg.FIXED_RAMP_GRID[:1]):
        name = f"fixedramp_f{frac:g}_h{hold_s:g}"
        tm.register(name, "fixed_ramp", ramp(name, mode="fixed_ramp", fixed_frac=frac, fixed_hold_s=hold_s))
    for name in list(tm.results):
        tm.eval(name, phase="sel")

    # [2] prior-granted seekers (+/-0.2 bin floor start). Detector arm: the
    # (W, tau) variant the best belief-free seeker selected in this cell
    # (clean cells: the original (1, 0.08)) -- the prior arm differs from the
    # seeker ONLY by the granted bin, never by detector tuning.
    best_seeker_sel = tm.best_in_group("seeker")
    prior_w, prior_tau = (1, 0.08) if noise_std <= 0.0 else variant_of[best_seeker_sel]
    prior_grid = [(r, dv) for r in (PRIOR_RATES if not quick else (20000.0,))
                  for dv in (PRIOR_DVS if not quick else (0.0,))]
    prior_names = []
    for r, dv in prior_grid:
        name = f"prior_r{r:g}_w{prior_w}_t{prior_tau:g}_v{dv:+g}"
        prior_names.append(name)
        tm.register(name, "prior_seeker", lambda: None)  # per-point builders below
    for point, mu in enumerate(mus):
        lo = max(reg.MU_DOMAIN[0], mu - reg.PRIOR_HALF_WIDTH)
        for (r, dv), name in zip(prior_grid, prior_names):
            tm.builders[name] = ramp(name, smooth_window=prior_w, mode="prior", ramp_rate=r,
                                     tau=prior_tau, backoff=reg.PRIOR_DELTA, strategy=reg.PRIOR_STRAT,
                                     mu_start=lo, prior_lo=lo, dv=dv)
            tm.eval(name, points=[point], phase="sel")

    # [3] per-mu oracle with dv fine-tune (selection per point)
    oracle_choice: list[str] = []
    for point, mu in enumerate(mus):
        cands = []
        for dv in (ORACLE_DVS if not quick else (0.0, 0.5)):
            name = f"oracle_dv{dv:+g}"
            if name not in tm.results:
                tm.register(name, "oracle", lambda: None)
            tm.builders[name] = ramp(name, mode="oracle", mu_true=mu, dv=dv)
            tm.eval(name, points=[point], phase="sel")
            cands.append(name)
        best = max(cands, key=lambda n: (tm.point_stat(n, point, "sel", "success"),
                                         tm.point_stat(n, point, "sel", "return")))
        oracle_choice.append(best)

    # [4] selection -> validation
    best_seeker = best_seeker_sel
    best_prior = tm.best_in_group("prior_seeker")
    best_fixed_speed = tm.best_in_group("fixed_speed")
    best_fixed_ramp = tm.best_in_group("fixed_ramp")
    for point, mu in enumerate(mus):
        lo = max(reg.MU_DOMAIN[0], mu - reg.PRIOR_HALF_WIDTH)
        r, dv = prior_grid[prior_names.index(best_prior)]
        tm.builders[best_prior] = ramp(best_prior, smooth_window=prior_w, mode="prior", ramp_rate=r,
                                       tau=prior_tau, backoff=reg.PRIOR_DELTA, strategy=reg.PRIOR_STRAT,
                                       mu_start=lo, prior_lo=lo, dv=dv)
        dv_o = float(oracle_choice[point].split("dv")[1])
        tm.builders[oracle_choice[point]] = ramp(oracle_choice[point], mode="oracle", mu_true=mu, dv=dv_o)
        tm.eval(oracle_choice[point], points=[point], phase="val")
        tm.eval(best_prior, points=[point], phase="val")
    tm.eval(best_seeker, phase="val")
    tm.eval(best_fixed_speed, phase="val")
    tm.eval(best_fixed_ramp, phase="val")

    # [5] aggregates
    def oracle_mean(phase: str, key: str = "success") -> float:
        return float(np.mean([tm.point_stat(oracle_choice[p], p, phase, key) for p in range(n_pts)]))

    def pack(name: str) -> dict[str, Any]:
        return {
            "plan": name,
            "success_sel": round(tm.tier_mean(name, "sel"), 4),
            "success_val": round(tm.tier_mean(name, "val"), 4),
            "on_time_val": round(tm.tier_mean(name, "val", "on_time"), 4),
            "collision_val": round(tm.tier_mean(name, "val", "collided"), 4),
            "per_point_success_val": [round(tm.point_stat(name, p, "val", "success"), 3)
                                      for p in range(n_pts)],
        }

    def id_telemetry(name: str, phase: str) -> dict[str, Any]:
        rows = [r for p in range(n_pts) for r in tm.results[name][p][phase]]
        id_steps = [r["id_step"] for r in rows if r.get("id_step", -1) >= 0 and not r.get("censored")]
        return {
            "identified_fraction": round(float(np.mean([1.0 if (r.get("id_step", -1) >= 0
                                                                and not r.get("censored")) else 0.0
                                                        for r in rows])), 4) if rows else None,
            "censored_fraction": round(float(np.mean([1.0 if r.get("censored") else 0.0
                                                      for r in rows])), 4) if rows else None,
            "id_step_mean": round(float(np.mean(id_steps)), 1) if id_steps else None,
            "mu_abs_err_mean": round(float(np.nanmean([abs(r["mu_hat"] - r["mu"]) for r in rows
                                                       if r.get("mu_hat") is not None
                                                       and np.isfinite(r.get("mu_hat", float("nan")))
                                                       and not r.get("censored")])), 4)
            if any(r.get("mu_hat") is not None and not r.get("censored")
                   and np.isfinite(r.get("mu_hat", float("nan"))) for r in rows) else None,
            "overshoot_episode_fraction": round(float(np.mean([1.0 if r.get("overshoot_events", 0) > 0
                                                               else 0.0 for r in rows])), 4) if rows else None,
        }

    oracle_val = oracle_mean("val")
    seeker_val = tm.tier_mean(best_seeker, "val")
    prior_val = tm.tier_mean(best_prior, "val")
    fixed_val = max(tm.tier_mean(best_fixed_speed, "val"), tm.tier_mean(best_fixed_ramp, "val"))
    # PRIMARY anchor (pre-registered): the tier's CLEAN-cell oracle on the same
    # episodes. In this deterministic simulator a mu-knowing agent can
    # dead-reckon its ego state from the UNDEGRADED command channels (9-11) +
    # known dynamics, so the clean oracle is an attainable ceiling for the
    # belief-endowed class under any sensing degradation. The same-cell
    # degraded oracle (no dead-reckoning credit) is the control-matched
    # SECONDARY readout.
    anchor = clean_oracle_anchor if clean_oracle_anchor is not None else {
        "success_val": oracle_val, "success_sel": oracle_mean("sel")}
    summary = {
        "reveal_m": reveal,
        **cell_tag,
        "delay_ms": round(delay_steps * DT * 1000.0),
        "episodes": tm.pool.episodes,
        "detector_variants_offered": [{"smooth_window": w, "tau": t} for w, t in variants],
        "prior_detector_variant": {"smooth_window": prior_w, "tau": prior_tau},
        "oracle_clean_anchor": {k: round(float(v), 4) for k, v in anchor.items()},
        "oracle_degraded": {
            "success_sel": round(oracle_mean("sel"), 4),
            "success_val": round(oracle_val, 4),
            "on_time_val": round(oracle_mean("val", "on_time"), 4),
            "plan_per_point": oracle_choice,
            "per_point_success_val": [round(tm.point_stat(oracle_choice[p], p, "val", "success"), 3)
                                      for p in range(n_pts)],
        },
        "best_seeker": {**pack(best_seeker), "id_telemetry_val": id_telemetry(best_seeker, "val")},
        "best_prior_seeker": {**pack(best_prior), "id_telemetry_val": id_telemetry(best_prior, "val")},
        "best_fixed_speed": pack(best_fixed_speed),
        "best_fixed_ramp": pack(best_fixed_ramp),
        "voi_belief_val": round(float(anchor["success_val"]) - seeker_val, 4),
        "voi_belief_sel": round(float(anchor["success_sel"]) - tm.tier_mean(best_seeker, "sel"), 4),
        "voi_belief_matched_val": round(oracle_val - seeker_val, 4),
        "sensing_execution_cost_val": round(float(anchor["success_val"]) - oracle_val, 4),
        "voi_residual_prior_val": round(float(anchor["success_val"]) - prior_val, 4),
        "prior_advantage_val": round(prior_val - seeker_val, 4),
        "detection_value_val": round(seeker_val - fixed_val, 4),
        "seeker_family_sel_means": {n: round(tm.tier_mean(n, "sel"), 4)
                                    for n in sorted(tm.results) if tm.groups[n] == "seeker"},
    }
    tm.pool.close()
    return summary


# ----------------------------------------------- detection-latency rerun (mechanism)


def latency_rerun_cell(reg, mod_b, mod_a, delay_steps: int, noise_std: float,
                       rows_out: list[dict[str, Any]], quick: bool) -> dict[str, Any]:
    """Measurement A's longitudinal protocol on the degraded stream, small
    scale: per-cell tau re-calibration (mod_a.calibrate_tau, its own honest
    procedure), then brake ramps with ground-truth onset from env internals
    (NOT degraded) -> detection delay including the observation delay."""
    cfg_dict = mod_a.ramp_env_config(track_width=5.0)
    env = make_degraded_env(reg, mod_b, cfg_dict, delay_steps, noise_std)
    n_calib = LAT_N_CALIB if not quick else 3
    n_ramp = LAT_N_PER_RATE if not quick else 2
    n_sub = LAT_N_SUBLIMIT if not quick else 2
    cell_id = f"delay{delay_steps}_noise{noise_std:g}"
    try:
        cal = mod_a.calibrate_tau(env, "long", n_calib,
                                  SEED_BASE * 100 + delay_steps * 1009 + int(noise_std * 1000) * 13 + 10_000,
                                  mod_a.TAU_FLOOR_LONG)
        tau = cal["tau"]
        ramp_rows = []
        for ri, rate in enumerate(LAT_RATES):
            for k in range(n_ramp):
                seed = SEED_BASE * 100 + delay_steps * 1009 + int(noise_std * 1000) * 13 + ri * 10_000 + k + 1_000_000
                res = mod_a.run_episode(env, "long", "ramp", rate, seed, tau)
                ramp_rows.append(res)
                rows_out.append({**res.row(), "cell": cell_id, "block": "ramp"})
        sub_rows = []
        for k in range(n_sub):
            seed = SEED_BASE * 100 + delay_steps * 1009 + int(noise_std * 1000) * 13 + k + 2_000_000
            res = mod_a.run_episode(env, "long", "sublimit", LAT_RATES[k % len(LAT_RATES)], seed, tau,
                                    sublimit_frac=0.6)
            sub_rows.append(res)
            rows_out.append({**res.row(), "cell": cell_id, "block": "sublimit"})
        fp = [r for r in sub_rows if r.fired_step >= 0 and r.sat_step < 0]
        return {
            "delay_steps": delay_steps,
            "noise_std": noise_std,
            "delay_ms": round(delay_steps * DT * 1000.0),
            "tau_recalibrated": round(float(tau), 4),
            "calibration": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in cal.items()},
            "overall": mod_a.cell_stats(ramp_rows),
            "per_rate": {f"rate={r:g}": mod_a.cell_stats([x for x in ramp_rows if x.rate == r])
                         for r in LAT_RATES},
            "false_positive": {"n_sublimit": len(sub_rows), "fp_count": len(fp)},
        }
    finally:
        env.close()


# ------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=2)
    parser.add_argument("--val-seeds", type=int, default=2)
    parser.add_argument("--reveals", type=str, default=",".join(f"{r:g}" for r in REVEALS_DEFAULT))
    parser.add_argument("--delays", type=str, default=",".join(str(d) for d in DELAYS_DEFAULT))
    parser.add_argument("--noises", type=str, default=",".join(f"{n:g}" for n in NOISES_DEFAULT))
    parser.add_argument("--skip-latency", action="store_true")
    parser.add_argument("--results-json", type=Path, default=RESULTS_JSON)
    args = parser.parse_args()
    reveals = tuple(float(x) for x in args.reveals.split(","))
    delays = tuple(int(x) for x in args.delays.split(","))
    noises = tuple(float(x) for x in args.noises.split(","))
    if args.quick:
        args.points, args.sel_seeds, args.val_seeds = 4, 1, 1
        reveals, delays, noises = (9.5,), (0, 25), (0.0, 0.05)

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    reg = load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_a = load_module(SLIP_SCRIPT, "slip_onset_detectability")
    interp = mod_c.interp_lin
    detector_cls, controller_cls = make_classes(reg)

    lo, hi = reg.MU_DOMAIN
    mus = [lo + (i + 0.5) / args.points * (hi - lo) for i in range(args.points)]
    sel_seeds = list(range(args.sel_seeds))
    val_seeds = list(range(args.val_seeds))
    cells = [(d, n) for d in delays for n in noises]

    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_degraded_regime_final",
        "generated_by": "scripts/feasibility_audit/degraded_regime_final.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "question": (
            "Clean-sensing VoI(belief)=0.000 rests entirely on 140-400 ms detection latency "
            "(docs/selfid-threshold-seeking-regime-2026-06.md). Does belief value re-emerge when "
            "the ego-response channels are delayed/noisy (M3214 wrapper), with the seeker given a "
            "fair per-cell detector re-calibration?"
        ),
        "decision_rule": {
            "pre_registered": True,
            "threshold": VOI_RESURRECTION_THRESHOLD,
            "rule": (
                f"if any degraded cell (delay>0 or noise>0) has voi_belief_val >= "
                f"{VOI_RESURRECTION_THRESHOLD} on validation seeds -> belief value re-emerges under "
                "degraded sensing; if all degraded cells are below -> the constructive null closes: "
                "passive fast adaptation + reflex is self-sufficient in this simulator universe"
            ),
            "voi_definition": (
                "voi_belief_val = clean-cell oracle success (degradation-free anchor, per PI spec: "
                "the oracle knows mu and needs no detection; in this deterministic sim it can "
                "dead-reckon ego state from the undegraded command channels) minus the best "
                "belief-free seeker in the cell, identical episodes. voi_belief_matched_val "
                "(secondary) uses the same-cell degraded oracle instead (no dead-reckoning credit); "
                "the two bracket the value of belief from above/below."
            ),
        },
        "degradation_matrix": {
            "delay_steps": list(delays),
            "delay_ms": [round(d * DT * 1000.0) for d in delays],
            "noise_std_ego_channels": list(noises),
            "wrapper": "src/autodrift/observation_degradation_wrapper.py (M3214 task family)",
            "semantics": "ego response channels 0-8 delayed then noised; geometry/commands/truth untouched",
            "construction": "identical wrapper path for every cell including delay0/noise0 (clean anchor)",
        },
        "task_surface": {
            "family": "B2K2_final, reveal tiers " + ",".join(f"{r:g}" for r in reveals) + " m (tightest two)",
            "mu_points": [round(m, 4) for m in mus],
            "selection_seeds": args.sel_seeds,
            "validation_seeds": args.val_seeds,
            "seed_note": (
                "episode seeds reuse reg.TierMeasurement.seed_for (20260618 stream) so the clean "
                "cell bit-replicates the original regime measurement; wrapper noise stream 20260610"
            ),
        },
        "controller_family": {
            "source": "scripts/feasibility_audit/ramp_policy_voi_regime.py (reused)",
            "trim_note": (
                "seeker grid trimmed vs the clean run (rates 2000/6000/20000, strategy hold, "
                "deltas 0.06/0.15, dv 0/0.75) -- rate 800 and 'retry' never uniquely won at "
                "9.5/12 m in the clean run; tau grid is per-cell re-calibrated (see calibration)"
            ),
            "degradation_fairness": (
                "per-cell tau re-calibration on sub-limit ramps (1.2x observed max shortfall, floor "
                "0.08) + optional 5-frame ego-channel moving average competing in selection"
            ),
        },
        "calibration": {},
        "detection_latency_rerun": {},
        "cells": [],
        "voi_curves": {},
        "artifacts": {},
    }

    def flush_partial() -> None:
        payload["elapsed_s"] = round(time.time() - started, 1)
        from autodrift.artifacts import utc_timestamp
        payload["generated_at_utc"] = utc_timestamp()
        args.results_json.parent.mkdir(parents=True, exist_ok=True)
        args.results_json.write_text(json.dumps(reg.to_jsonable(payload), indent=2), encoding="utf-8")

    # [1/4] per-cell detector tau calibration
    print(f"[1/4] per-cell detector tau calibration ({len(cells)} cells)", flush=True)
    calibrations: dict[tuple[int, float], dict[str, Any]] = {}
    for delay_steps, noise_std in cells:
        cal = calibrate_cell_tau(reg, mod_b, mod_a, interp, detector_cls, delay_steps, noise_std, args.quick)
        calibrations[(delay_steps, noise_std)] = cal
        payload["calibration"][f"delay{delay_steps}_noise{noise_std:g}"] = cal
        print(f"  delay={delay_steps:>2} noise={noise_std:g} -> "
              + " ".join(f"tau_w{w}={cal[f'w{w}']['tau']:.3f}" for w in ALL_WINDOWS)
              + " (max " + " ".join(f"w{w}={cal[f'w{w}']['max_signal']:.3f}" for w in ALL_WINDOWS) + ")",
              flush=True)
    flush_partial()

    # [2/4] Measurement-A latency rerun on degraded streams (mechanism evidence)
    lat_rows: list[dict[str, Any]] = []
    if not args.skip_latency:
        print(f"[2/4] detection-latency rerun on degraded streams ({len(cells)} cells)", flush=True)
        for delay_steps, noise_std in cells:
            res = latency_rerun_cell(reg, mod_b, mod_a, delay_steps, noise_std, lat_rows, args.quick)
            payload["detection_latency_rerun"][f"delay{delay_steps}_noise{noise_std:g}"] = res
            ov = res["overall"]
            print(f"  delay={delay_steps:>2} noise={noise_std:g} -> tau={res['tau_recalibrated']:.3f} "
                  f"delay_median={ov['delay_steps_median']} p90={ov['delay_steps_p90']} "
                  f"miss={ov['miss_rate']:.2f} overshoot%={ov['overshoot_pct_median']} "
                  f"fp={res['false_positive']['fp_count']}/{res['false_positive']['n_sublimit']}", flush=True)
            flush_partial()
    else:
        print("[2/4] latency rerun skipped", flush=True)

    # [3/4] regime cells
    n_cells_total = len(reveals) * len(cells)
    print(f"[3/4] degraded regime: {len(reveals)} tiers x {len(cells)} cells = {n_cells_total}, "
          f"{args.points} mu points x {args.sel_seeds}+{args.val_seeds} seeds", flush=True)
    rows_out: list[dict[str, Any]] = []
    done = 0
    for reveal in reveals:
        design = reg.make_design(mod_b, reveal)
        # the clean cell must run first: its oracle is the tier's degradation-free anchor
        tier_cells = sorted(cells, key=lambda c: (c[0] != 0 or c[1] != 0.0, c))
        clean_anchor: dict[str, float] | None = None
        for delay_steps, noise_std in tier_cells:
            t0 = time.time()
            summary = measure_cell(reg, mod_b, interp, design, reveal, delay_steps, noise_std,
                                   mus, sel_seeds, val_seeds, rows_out, controller_cls,
                                   calibrations[(delay_steps, noise_std)], clean_anchor, args.quick)
            summary["elapsed_s"] = round(time.time() - t0, 1)
            if delay_steps == 0 and noise_std == 0.0:
                clean_anchor = {"success_val": summary["oracle_degraded"]["success_val"],
                                "success_sel": summary["oracle_degraded"]["success_sel"]}
            payload["cells"].append(summary)
            done += 1
            print(f"  [{done}/{n_cells_total}] reveal={reveal:g} delay={delay_steps:>2} noise={noise_std:g} | "
                  f"oracle_deg={summary['oracle_degraded']['success_val']:.3f} "
                  f"seeker={summary['best_seeker']['success_val']:.3f} ({summary['best_seeker']['plan']}) "
                  f"prior={summary['best_prior_seeker']['success_val']:.3f} "
                  f"fixed={max(summary['best_fixed_speed']['success_val'], summary['best_fixed_ramp']['success_val']):.3f} | "
                  f"VoI(belief)={summary['voi_belief_val']:+.3f} "
                  f"VoI_matched={summary['voi_belief_matched_val']:+.3f} "
                  f"prior_adv={summary['prior_advantage_val']:+.3f} "
                  f"detect={summary['detection_value_val']:+.3f} "
                  f"[{summary['episodes']} eps, {summary['elapsed_s']}s]", flush=True)
            flush_partial()

    # [4/4] curves + decision + artifacts
    print("[4/4] curves, decision, artifacts", flush=True)
    for reveal in reveals:
        payload["voi_curves"][f"reveal_{reveal:g}m"] = [
            {
                "delay_steps": c["delay_steps"], "delay_ms": c["delay_ms"], "noise_std": c["noise_std"],
                "oracle_clean_anchor": c["oracle_clean_anchor"]["success_val"],
                "oracle_degraded": c["oracle_degraded"]["success_val"],
                "seeker": c["best_seeker"]["success_val"],
                "prior_seeker": c["best_prior_seeker"]["success_val"],
                "fixed": max(c["best_fixed_speed"]["success_val"], c["best_fixed_ramp"]["success_val"]),
                "voi_belief": c["voi_belief_val"],
                "voi_belief_matched": c["voi_belief_matched_val"],
                "prior_advantage": c["prior_advantage_val"],
                "voi_residual_prior": c["voi_residual_prior_val"],
                "detection_value": c["detection_value_val"],
            }
            for c in payload["cells"] if c["reveal_m"] == reveal
        ]
    degraded_cells = [c for c in payload["cells"] if c["delay_steps"] > 0 or c["noise_std"] > 0]
    max_cell = max(degraded_cells, key=lambda c: c["voi_belief_val"]) if degraded_cells else None
    resurrected = [c for c in degraded_cells if c["voi_belief_val"] >= VOI_RESURRECTION_THRESHOLD]
    matched_resurrected = [c for c in degraded_cells
                           if c["voi_belief_matched_val"] >= VOI_RESURRECTION_THRESHOLD]
    payload["decision"] = {
        "n_degraded_cells": len(degraded_cells),
        "max_voi_belief_val_degraded": (round(max_cell["voi_belief_val"], 4) if max_cell else None),
        "max_cell": ({"reveal_m": max_cell["reveal_m"], "delay_steps": max_cell["delay_steps"],
                      "noise_std": max_cell["noise_std"]} if max_cell else None),
        "cells_at_or_above_threshold": [
            {"reveal_m": c["reveal_m"], "delay_steps": c["delay_steps"], "noise_std": c["noise_std"],
             "voi_belief_val": c["voi_belief_val"]} for c in resurrected
        ],
        "cells_at_or_above_threshold_matched_secondary": [
            {"reveal_m": c["reveal_m"], "delay_steps": c["delay_steps"], "noise_std": c["noise_std"],
             "voi_belief_matched_val": c["voi_belief_matched_val"]} for c in matched_resurrected
        ],
        "verdict": ("belief_value_re_emerges" if resurrected else "constructive_null_closes"),
        "verdict_matched_secondary": ("belief_value_re_emerges" if matched_resurrected
                                      else "constructive_null_closes"),
    }
    payload["env_fidelity_notes"] = [
        "all clean-run fidelity caveats apply (rear-clamp no-lockup, 6000 N brake actuator "
        "censoring mu>~0.89); the degradation wrapper changes ONLY what the controller reads",
        "the oracle runs on the same degraded stream (it uses vx for speed tracking) so its "
        "success can itself drop with degradation; voi_belief = oracle - seeker on identical "
        "sensing isolates the value of knowing mu, not the value of clean sensing",
    ]

    from autodrift.artifacts import write_csv_rows
    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, rows_out)
    payload["artifacts"]["episode_rows_csv"] = str(rows_csv)
    if lat_rows:
        lat_csv = RUN_DIR / "latency_rows.csv"
        write_csv_rows(lat_csv, lat_rows)
        payload["artifacts"]["latency_rows_csv"] = str(lat_csv)
    payload["artifacts"]["results_json"] = str(args.results_json)
    payload["n_regime_episodes"] = len(rows_out)
    flush_partial()
    print(f"results -> {args.results_json}", flush=True)
    print("HEADLINE: verdict=" + payload["decision"]["verdict"] + " | " + " | ".join(
        f"r{c['reveal_m']:g} d{c['delay_steps']} n{c['noise_std']:g}: VoI={c['voi_belief_val']:+.3f}"
        for c in payload["cells"]), flush=True)


if __name__ == "__main__":
    main()
