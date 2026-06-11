"""WP0.2/WP0.3 closing measurement (harness milestone M3215): degraded-regime
sweep over the extended degradation modes on BOTH task families + the
noise-buys-delay bridge validation.

Plan anchor: docs/research-plan-phase2-capability-boundary-tracking.md WP0.2
(degradation realism with a falsifiable bridge) and WP0.3 (statistical
hardening); G-A gate criteria. Pre-registration (criteria frozen BEFORE the
full run): experiments/feasibility_audit/wp0_degraded_sweep_prereg.json,
echoed into summary.json before any cell result is read.

Task surfaces (tight windows only):
  family #1  B2K2_final at reveal 9.5 m (ramp_policy_voi_regime machinery,
             episode seeds reuse the 20260618 stream so val seeds k=0,1
             extend the degraded_regime_final anchors bit-compatibly).
  family #2  F2C1_offset_jitter_react (frozen final_spec in
             experiments/feasibility_audit/family2_spec.json), with the
             drive-side (throttle) seeker family from family2_design.py --
             the family's clean-acceptance winner -- competing alongside the
             brake-side style; fresh SEED_BASE 20260625 (20260624 A-D consumed
             by the design measurement).

Degradation cells per family (M3214 wrapper, ego channels 0-8 only):
  anchors  clean | delay 5 (100 ms) | delay 12 (240 ms) | delay 25 (500 ms) |
           iid noise 0.05
  NEW (5)  AR(1) rho=0.9 sigma_eq=0.05 | AR(1) rho=0.95 sigma_eq=0.05 |
           dropout p=0.2 | episode_random delay U[5,25] | piecewise delay [5,25]
  (sigma_eq = stationary std; ar1_sigma = sigma_eq*sqrt(1-rho^2))

Per-cell readout (pre-registered):
  - matched anchor (PRIMARY): VoI_matched = same-cell degraded per-mu oracle
    success minus the best belief-free arm floor = max(best seeker over the
    per-cell re-calibrated detector grid, best fixed plan), validation stream.
  - clean-anchor VoI reported as secondary.
  - 12 mu points x 2 selection seeds + >= 10 validation seeds (>= 120
    validation episodes per arm per cell), Wilson 95% CIs per arm and a
    Newcombe 95% CI on the VoI difference.

Bridge validation (WP0.2, falsifiable): per degradation cell, the
measurement-A protocol (slip_onset_detectability, sub-limit ramps, task
outcomes never consulted) measures the calibrated detector's median detection
latency; dL = cell median - clean median (steps). Prediction: the cell's
VoI_matched equals the same family's pure-delay curve {clean, d5, d12, d25}
linearly interpolated at dL (clamped at the endpoints; if ramp miss rate >
0.5, dL saturates to the largest pure-delay anchor, declared). PASS =
threshold classification (VoI_matched >= 0.15) agreement >= 75% over the 10
new cells (families pooled) AND Spearman(predicted, measured) >= 0.6.
AR(1) genuinely threatens the prediction (it defeats time-averaging); either
direction is reported as measured.

G-A gate (pre-registered): family #2 clean-cell VoI_matched <= 0.05 AND
VoI_matched >= 0.15 in >= 3 of the 5 NEW degraded family-#2 cells -> the
two-regime law direction replicates on family #2 (route WP1 on both
families); otherwise the law is scoped family-specific per the plan's G-A
fallback (WP1 still runs on family #1).

Budget rule (pre-registered): if the projected full runtime exceeds 2.5 h,
cells are dropped (and reported), validation seeds are never reduced.

Progress is flushed per completed unit to progress.jsonl (resume-safe: rerun
skips completed units) and summary_partial.json; summary.json is written only
on full completion.

Hard constraints: pure CPU numpy, zero training, deterministic seeds, no git
operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/wp0_degraded_sweep.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/wp0_degraded_sweep.py --full
"""

from __future__ import annotations

import argparse
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
FAMILY2_SCRIPT = REPO / "scripts/feasibility_audit/family2_design.py"
FAMILY2_SPEC = REPO / "experiments/feasibility_audit/family2_spec.json"
PREREG_JSON = REPO / "experiments/feasibility_audit/wp0_degraded_sweep_prereg.json"
DEFAULT_RUN_DIR = REPO / "runs/feasibility_audit/wp0_degraded_sweep"

SEED_BASE = 20260625  # fresh stream for the family-2 scan + calibration/latency
DT = 0.02
REVEAL = 9.5
VOI_BAR = 0.15
CLEAN_BAR = 0.05
BRIDGE_AGREEMENT_BAR = 0.75
BRIDGE_SPEARMAN_BAR = 0.6
MISS_RATE_SATURATION = 0.5

ALL_WINDOWS = (1, 5, 12, 25)
TAU_SAFETY, TAU_FLOOR = 1.2, 0.08
CALIB_MUS = (0.5, 0.9)
CALIB_SEEDS_PER_MU = 3
CALIB_STEPS = 230
CALIB_BRAKE_LIMIT_FRAC = 0.55
CALIB_DRIVE_LIMIT_FRAC = 0.50

# family-1 controller grids (trimmed exactly as degraded_regime_final)
F1_SEEKER_RATES = (2000.0, 6000.0, 20000.0)
F1_SEEKER_DELTAS = (0.06, 0.15)
F1_SEEKER_DVS = (0.0, 0.75)
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)

# family-2 controller grids (winner-centred trim of the design grid)
F2_SEEKER_STYLES = ("drive", "brake")
F2_SEEKER_RATES = (6000.0, 20000.0)
F2_SEEKER_BACKOFFS = (0.06, 0.15)
F2_SEEKER_DVS = (0.0, 0.75)
F2_FIXED_SWERVE_SPEEDS = (6.5, 8.5, 10.5, 12.0)
F2_FIXED_COMMIT_SPEEDS = (9.5, 10.5, 11.5)

# bridge latency protocol (measurement-A reuse, hardened counts)
LAT_RATES = (0.10, 0.40)
LAT_N_PER_RATE = 6
LAT_N_CALIB = 6
LAT_N_SUBLIMIT = 4

CLAIM_BOUNDARY = (
    "Feasibility-audit policy-family VoI measurement only (Phase-2 WP0.2/WP0.3, manual "
    "takeover): scripted per-mu oracle ramps, belief-free threshold seekers with per-cell "
    "re-calibrated shortfall detectors, and no-detection fixed plans are rolled out on "
    "B2K2_final (reveal 9.5 m) and the frozen F2C1_offset_jitter_react family under the M3214 "
    "observation-degradation wrapper extended modes, plus a measurement-A detection-latency "
    "bridge. Auxiliary measurement; the engineering incumbent is unchanged. No driver "
    "promotion, training, validation ranking, repair-success, gate-validity, paper, "
    "high-fidelity, robustness-result, feasibility-proof, or self-ID capability claim."
)

CELLS: tuple[dict[str, Any], ...] = (
    {"cell_id": "clean", "kind": "anchor_clean", "noisy": False, "pure_delay_steps": 0,
     "degradation": {"delay_steps": 0, "noise_std": 0.0}},
    {"cell_id": "delay5", "kind": "anchor_delay", "noisy": False, "pure_delay_steps": 5,
     "degradation": {"delay_steps": 5}},
    {"cell_id": "delay12", "kind": "anchor_delay", "noisy": False, "pure_delay_steps": 12,
     "degradation": {"delay_steps": 12}},
    {"cell_id": "delay25", "kind": "anchor_delay", "noisy": False, "pure_delay_steps": 25,
     "degradation": {"delay_steps": 25}},
    {"cell_id": "noise0.05", "kind": "anchor_noise", "noisy": True, "pure_delay_steps": None,
     "degradation": {"noise_std": 0.05}},
    {"cell_id": "ar1_r0.9_s0.05eq", "kind": "new", "noisy": True, "pure_delay_steps": None,
     "degradation": {"ar1_rho": 0.9, "ar1_sigma": round(0.05 * math.sqrt(1.0 - 0.9 ** 2), 6)}},
    {"cell_id": "ar1_r0.95_s0.05eq", "kind": "new", "noisy": True, "pure_delay_steps": None,
     "degradation": {"ar1_rho": 0.95, "ar1_sigma": round(0.05 * math.sqrt(1.0 - 0.95 ** 2), 6)}},
    {"cell_id": "dropout0.2", "kind": "new", "noisy": False, "pure_delay_steps": None,
     "degradation": {"dropout_prob": 0.2}},
    {"cell_id": "eprand_d5_25", "kind": "new", "noisy": False, "pure_delay_steps": None,
     "degradation": {"delay_profile": "episode_random", "delay_lo": 5, "delay_hi": 25}},
    {"cell_id": "piecewise_d5_25", "kind": "new", "noisy": False, "pure_delay_steps": None,
     "degradation": {"delay_profile": "piecewise", "delay_lo": 5, "delay_hi": 25}},
)
QUICK_CELL_IDS = ("clean", "delay12", "ar1_r0.9_s0.05eq", "eprand_d5_25")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def wilson_ci(p_hat: float, n: int, z: float = 1.96) -> list[float]:
    if n == 0 or not np.isfinite(p_hat):
        return [float("nan"), float("nan")]
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(max(p_hat * (1 - p_hat), 0.0) / n + z * z / (4 * n * n)) / denom
    return [round(center - half, 4), round(center + half, 4)]


def newcombe_diff_ci(p1: float, n1: int, p2: float, n2: int) -> list[float]:
    """95% CI for p1 - p2 from the Wilson intervals (Newcombe hybrid score)."""
    l1, u1 = wilson_ci(p1, n1)
    l2, u2 = wilson_ci(p2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return [round(lo, 4), round(hi, 4)]


def spearman_rho(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None

    def avg_ranks(values: list[float]) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64)
        order = np.argsort(arr, kind="mergesort")
        ranks = np.empty(len(arr), dtype=np.float64)
        i = 0
        while i < len(arr):
            j = i
            while j + 1 < len(arr) and arr[order[j + 1]] == arr[order[i]]:
                j += 1
            ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
            i = j + 1
        return ranks

    rx, ry = avg_ranks(xs), avg_ranks(ys)
    sx, sy = rx.std(), ry.std()
    if sx == 0.0 or sy == 0.0:
        return None
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


# ------------------------------------------------------------- degraded envs


def make_degraded_env_cfg(deg_mod, cfg_dict: dict[str, Any], degradation: dict[str, Any]):
    """Generic version of degraded_regime_final.make_degraded_env: any wrapper block."""
    from autodrift.config import build_env_config
    from autodrift.observation_degradation_wrapper import make_env_from_config

    cfg_dict = dict(cfg_dict)
    block = dict(degradation) if degradation else {"delay_steps": 0, "noise_std": 0.0}
    cfg_dict["observation_degradation"] = block
    return deg_mod.EnvShim(make_env_from_config(build_env_config(cfg_dict)))


def make_f1_pool(reg, deg_mod, mod_b, interp, design, degradation: dict[str, Any]):
    class GenericDegradedPool(reg.EnvPool):
        def env_for(self, mu: float, seed: int):
            key = (round(mu, 6), int(seed))
            if key not in self._cache:
                d = reg.jittered_distance(self.interp, mu, seed)
                level = self.mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d,
                                             entry_speed=reg.v_star(self.interp, mu))
                cfg_dict = self.mod_b.level_env_config(self.design, level)
                shim = make_degraded_env_cfg(deg_mod, cfg_dict, degradation)
                assert shim.base_obs_dim == self.mod_b.OBS_DIM
                self._cache[key] = shim
            return self._cache[key]

    return GenericDegradedPool(mod_b, interp, design)


def make_f2_pool(fam2, deg_mod, cand, degradation: dict[str, Any]):
    class F2DegradedPool(fam2.EnvPool):
        def env_for(self, mu: float, seed: int):
            key = (round(mu, 6), int(seed))
            if key not in self._cache:
                cfg_dict = fam2.env_config(self.cand, mu, seed)
                shim = make_degraded_env_cfg(deg_mod, cfg_dict, degradation)
                assert shim.base_obs_dim == fam2.OBS_DIM
                self._cache[key] = shim
            return self._cache[key]

    return F2DegradedPool(cand)


def make_f2_classes(reg, deg_mod, fam2):
    detector_cls, _ = deg_mod.make_classes(reg)

    class DegradedFamily2Ramp(fam2.Family2Ramp):
        """family2_design.Family2Ramp with the detector swapped for the
        degradation-aware variant (W-frame moving average over ego channels
        with branch-unanimity gating; W=1 reproduces reg.ShortfallDetector
        exactly -- the clean-cell replication anchor)."""

        def __init__(self, mod_r, cand, name, mode, *, smooth_window: int = 1, **kw):
            self._smooth_window = max(int(smooth_window), 1)
            super().__init__(mod_r, cand, name, mode, **kw)
            self.detector = detector_cls(self.detector.tau, self._smooth_window)

    return detector_cls, DegradedFamily2Ramp


def f2_seed(point: int, k: int, phase: str) -> int:
    return SEED_BASE * 10 + 17 * point + 1000 * k + (0 if phase == "sel" else 100_000)


# ----------------------------------------------------- per-cell tau calibration


def tau_variants(noisy: bool, cal: dict[str, Any]) -> list[tuple[int, float]]:
    """(smooth_window, tau) seeker detector variants for one cell. Noise-free
    cells (pure delay / dropout / time-varying delay: the shortfall stream is
    time-shifted or held, not noised) keep the clean grid plus the calibrated
    floor when elevated. Noise-like cells (iid / AR(1)) get re-calibrated taus
    at every smoothing window; selection picks the latency/threshold trade."""
    if not noisy:
        variants = [(1, 0.08), (1, 0.18)]
        tau1 = float(cal["w1"]["tau"])
        if tau1 > 0.18:
            variants.append((1, round(tau1, 3)))
        return variants
    out, seen = [], set()
    for w in ALL_WINDOWS:
        v = (w, round(float(cal[f"w{w}"]["tau"]), 3))
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def calibrate_cell(reg, mod_a, detector_cls, pool, quick: bool, seed_offset: int) -> dict[str, Any]:
    """Sub-limit brake+drive episodes with tau=inf detectors at every smoothing
    window in parallel; the observed max shortfall is the cell's noise floor;
    tau = max(1.2*max, 0.08). Harness-only privilege: sub-limit caps use the
    true mu (the detector never sees it) -- the Measurement-A calibration."""
    maxima: dict[int, list[float]] = {w: [] for w in ALL_WINDOWS}
    n_eps = 0
    mus = CALIB_MUS if not quick else (0.9,)
    n_seeds = CALIB_SEEDS_PER_MU if not quick else 1
    for mu in mus:
        f_limit = reg.TIRE_CAP * mu * reg.FZR
        brake_cap_n = CALIB_BRAKE_LIMIT_FRAC * f_limit
        drive_cap01 = min(CALIB_DRIVE_LIMIT_FRAC * f_limit / reg.MAX_DRIVE, 1.0)
        for j in range(n_seeds):
            seed = SEED_BASE * 10 + int(mu * 100) * 101 + j + seed_offset
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
    out: dict[str, Any] = {"n_episodes": n_eps, "safety_factor": TAU_SAFETY, "tau_floor": TAU_FLOOR}
    for w in ALL_WINDOWS:
        mx = max(maxima[w]) if maxima[w] else 0.0
        out[f"w{w}"] = {"max_signal": round(mx, 4), "tau": round(max(TAU_SAFETY * mx, TAU_FLOOR), 4)}
    return out


# --------------------------------------------------- bridge: detection latency


def latency_cell(reg, deg_mod, mod_a, cell: dict[str, Any], cell_index: int,
                 rows_out: list[dict[str, Any]], quick: bool) -> dict[str, Any]:
    """Measurement-A longitudinal protocol on the degraded stream (sub-limit
    ramps; ground-truth onset from env internals, never degraded). Task
    outcomes are never consulted -- bridge inputs only."""
    cfg_dict = mod_a.ramp_env_config(track_width=5.0)
    env = make_degraded_env_cfg(deg_mod, cfg_dict, cell["degradation"])
    n_calib = LAT_N_CALIB if not quick else 3
    n_ramp = LAT_N_PER_RATE if not quick else 2
    n_sub = LAT_N_SUBLIMIT if not quick else 2
    base = SEED_BASE * 100 + cell_index * 10_007
    try:
        cal = mod_a.calibrate_tau(env, "long", n_calib, base + 10_000, mod_a.TAU_FLOOR_LONG)
        tau = cal["tau"]
        ramp_rows = []
        for ri, rate in enumerate(LAT_RATES):
            for k in range(n_ramp):
                seed = base + ri * 10_000 + k + 1_000_000
                res = mod_a.run_episode(env, "long", "ramp", rate, seed, tau)
                ramp_rows.append(res)
                rows_out.append({**res.row(), "cell": cell["cell_id"], "block": "ramp"})
        sub_rows = []
        for k in range(n_sub):
            seed = base + k + 2_000_000
            res = mod_a.run_episode(env, "long", "sublimit", LAT_RATES[k % len(LAT_RATES)], seed, tau,
                                    sublimit_frac=0.6)
            sub_rows.append(res)
            rows_out.append({**res.row(), "cell": cell["cell_id"], "block": "sublimit"})
        fp = [r for r in sub_rows if r.fired_step >= 0 and r.sat_step < 0]
        return {
            "cell_id": cell["cell_id"],
            "degradation": cell["degradation"],
            "tau_recalibrated": round(float(tau), 4),
            "overall": mod_a.cell_stats(ramp_rows),
            "per_rate": {f"rate={r:g}": mod_a.cell_stats([x for x in ramp_rows if x.rate == r])
                         for r in LAT_RATES},
            "false_positive": {"n_sublimit": len(sub_rows), "fp_count": len(fp)},
        }
    finally:
        env.close()


# ------------------------------------------------------- family-1 cell measure


def measure_cell_f1(reg, deg_mod, mod_b, interp, design, cell, mus, sel_seeds, val_seeds,
                    rows_out, controller_cls, cal, clean_anchor, quick) -> dict[str, Any]:
    tm = reg.TierMeasurement(mod_b, interp, design, 0, REVEAL, mus, sel_seeds, val_seeds, rows_out)
    tm.pool.close()
    tm.pool = make_f1_pool(reg, deg_mod, mod_b, interp, design, cell["degradation"])
    n_pts = len(mus)
    n_val = n_pts * len(val_seeds)

    def ramp(name: str, smooth_window: int = 1, **kw) -> Callable[[], Any]:
        return lambda: controller_cls(mod_b, interp, design, name, smooth_window=smooth_window, **kw)

    variants = tau_variants(cell["noisy"], cal)
    rates = F1_SEEKER_RATES if not quick else (6000.0, 20000.0)
    deltas = F1_SEEKER_DELTAS if not quick else (0.06,)
    for r in rates:
        for w, tau in variants:
            for delta in deltas:
                for dv in F1_SEEKER_DVS:
                    name = f"seeker_r{r:g}_w{w}_t{tau:g}_d{delta:g}_v{dv:+g}"
                    tm.register(name, "seeker",
                                ramp(name, smooth_window=w, mode="seeker", ramp_rate=r, tau=tau,
                                     backoff=delta, strategy="hold", dv=dv))
    for v in (reg.FIXED_SPEED_GRID if not quick else (4.5, 7.5, 10.5)):
        plan = mod_b.PlanSpec(name=f"fixed_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        tm.register(plan.name, "fixed_speed", (lambda p=plan: mod_b.CommitmentController(p, design)))
    for frac, hold_s in (reg.FIXED_RAMP_GRID if not quick else reg.FIXED_RAMP_GRID[:1]):
        name = f"fixedramp_f{frac:g}_h{hold_s:g}"
        tm.register(name, "fixed_ramp", ramp(name, mode="fixed_ramp", fixed_frac=frac, fixed_hold_s=hold_s))
    for name in list(tm.results):
        tm.eval(name, phase="sel")

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

    best_seeker = tm.best_in_group("seeker")
    best_fixed_speed = tm.best_in_group("fixed_speed")
    best_fixed_ramp = tm.best_in_group("fixed_ramp")
    for point, mu in enumerate(mus):
        dv_o = float(oracle_choice[point].split("dv")[1])
        tm.builders[oracle_choice[point]] = ramp(oracle_choice[point], mode="oracle", mu_true=mu, dv=dv_o)
        tm.eval(oracle_choice[point], points=[point], phase="val")
    tm.eval(best_seeker, phase="val")
    tm.eval(best_fixed_speed, phase="val")
    tm.eval(best_fixed_ramp, phase="val")

    def pack(name: str) -> dict[str, Any]:
        succ = tm.tier_mean(name, "val")
        return {
            "plan": name,
            "success_sel": round(tm.tier_mean(name, "sel"), 4),
            "success_val": round(succ, 4),
            "wilson95_val": wilson_ci(succ, n_val),
            "collision_val": round(tm.tier_mean(name, "val", "collided"), 4),
            "per_point_success_val": [round(tm.point_stat(name, p, "val", "success"), 3)
                                      for p in range(n_pts)],
        }

    oracle_val = float(np.mean([tm.point_stat(oracle_choice[p], p, "val", "success")
                                for p in range(n_pts)]))
    seeker_val = tm.tier_mean(best_seeker, "val")
    fs_val = tm.tier_mean(best_fixed_speed, "val")
    fr_val = tm.tier_mean(best_fixed_ramp, "val")
    fixed_val = max(fs_val, fr_val)
    fixed_arm = best_fixed_speed if fs_val >= fr_val else best_fixed_ramp
    floor_val = max(seeker_val, fixed_val)
    floor_arm = best_seeker if seeker_val >= fixed_val else fixed_arm

    summary = {
        "cell_id": cell["cell_id"],
        "kind": cell["kind"],
        "degradation": cell["degradation"],
        "noisy_treatment": cell["noisy"],
        "episodes": tm.pool.episodes,
        "n_val_episodes_per_arm": n_val,
        "detector_variants_offered": [{"smooth_window": w, "tau": t} for w, t in variants],
        "oracle_degraded": {
            "success_val": round(oracle_val, 4),
            "wilson95_val": wilson_ci(oracle_val, n_val),
            "plan_per_point": oracle_choice,
            "per_point_success_val": [round(tm.point_stat(oracle_choice[p], p, "val", "success"), 3)
                                      for p in range(n_pts)],
        },
        "best_seeker": pack(best_seeker),
        "best_fixed": {**pack(fixed_arm), "candidates": {best_fixed_speed: round(fs_val, 4),
                                                         best_fixed_ramp: round(fr_val, 4)}},
        "floor": {"arm": floor_arm, "success_val": round(floor_val, 4),
                  "wilson95_val": wilson_ci(floor_val, n_val)},
        "voi_matched_val": round(oracle_val - floor_val, 4),
        "voi_matched_ci95_newcombe": newcombe_diff_ci(oracle_val, n_val, floor_val, n_val),
    }
    if clean_anchor is not None:
        summary["voi_clean_anchor_val"] = round(float(clean_anchor) - floor_val, 4)
    tm.pool.close()
    return summary


# ------------------------------------------------------- family-2 cell measure


def measure_cell_f2(fam2, reg, deg_mod, f2_ramp_cls, cand, cell, mus, sel_ks, val_ks,
                    rows_out, cal, clean_anchor, quick) -> dict[str, Any]:
    pool = make_f2_pool(fam2, deg_mod, cand, cell["degradation"])
    n_pts = len(mus)
    n_val = n_pts * len(val_ks)
    cell_tag = {"cell": cell["cell_id"], "family": "F2C1"}
    try:
        variants = tau_variants(cell["noisy"], cal)
        styles = F2_SEEKER_STYLES if not quick else ("drive",)
        rates = F2_SEEKER_RATES if not quick else (6000.0,)
        backoffs = F2_SEEKER_BACKOFFS if not quick else (0.06,)
        dvs = F2_SEEKER_DVS

        def seeker_builder(style, r, w, tau, b, dv, name):
            return f2_ramp_cls(reg, cand, name, "seeker", smooth_window=w, ramp_rate=r,
                               tau=tau, backoff=b, dv=dv, seek_style=style)

        # [1] seeker selection grid (stream sel)
        seeker_grid: dict[str, tuple] = {}
        seeker_sel: dict[str, tuple[float, float]] = {}
        for style in styles:
            for r in rates:
                for w, tau in variants:
                    for b in backoffs:
                        for dv in dvs:
                            name = f"seeker_{style}_r{r:g}_w{w}_t{tau:g}_b{b:g}_v{dv:+g}"
                            seeker_grid[name] = (style, r, w, tau, b, dv)
                            controller = seeker_builder(style, r, w, tau, b, dv, name)
                            rows = [pool.rollout(controller, mu, f2_seed(p, k, "sel"), plan=name,
                                                 plan_group="seeker", mu_point=round(mu, 4),
                                                 phase="sel", **cell_tag)
                                    for p, mu in enumerate(mus) for k in sel_ks]
                            rows_out.extend(rows)
                            seeker_sel[name] = (float(np.mean([x["success"] for x in rows])),
                                                float(np.mean([x["return"] for x in rows])))
        best_seeker = max(seeker_grid, key=lambda n: seeker_sel[n])

        # [2] fixed-plan floor arms (no detection; selection then best -> val)
        fixed_plans = [fam2.F2Plan(name=f"swerve_only_v{v:g}_react", v_entry=float(v), brake_to=None)
                       for v in (F2_FIXED_SWERVE_SPEEDS if not quick else (8.5, 12.0))]
        for v in (F2_FIXED_COMMIT_SPEEDS if not quick else (10.5,)):
            for side, bias in (("bias_left", 1.0), ("bias_right", -1.0)):
                fixed_plans.append(fam2.F2Plan(name=f"commit_v{v:g}_{side}", v_entry=float(v),
                                               brake_to=max(v - 1.0, 4.0), bias=bias))
        fixed_sel: dict[str, tuple[float, float]] = {}
        plan_by_name = {}
        for plan in fixed_plans:
            plan_by_name[plan.name] = plan
            controller = fam2.Family2Controller(plan, cand)
            rows = [pool.rollout(controller, mu, f2_seed(p, k, "sel"), plan=plan.name,
                                 plan_group="fixed", mu_point=round(mu, 4), phase="sel", **cell_tag)
                    for p, mu in enumerate(mus) for k in sel_ks]
            rows_out.extend(rows)
            fixed_sel[plan.name] = (float(np.mean([x["success"] for x in rows])),
                                    float(np.mean([x["return"] for x in rows])))
        best_fixed = max(fixed_sel, key=lambda n: fixed_sel[n])

        # [3] oracle dv per point (stream sel)
        oracle_dv: list[float] = []
        for p, mu in enumerate(mus):
            cands = []
            for odv in (ORACLE_DVS if not quick else (0.0, 0.5)):
                controller = f2_ramp_cls(reg, cand, f"oracle_dv{odv:+g}", "oracle", mu_true=mu, dv=odv)
                rows = [pool.rollout(controller, mu, f2_seed(p, k, "sel"), plan=f"oracle_dv{odv:+g}",
                                     plan_group="oracle", mu_point=round(mu, 4), phase="sel", **cell_tag)
                        for k in sel_ks]
                rows_out.extend(rows)
                cands.append((float(np.mean([x["success"] for x in rows])),
                              float(np.mean([x["return"] for x in rows])), odv))
            oracle_dv.append(max(cands)[2])

        # [4] validation (disjoint stream)
        def run_val(builder, name, group):
            rows = []
            for p, mu in enumerate(mus):
                controller = builder(p, mu)
                for k in val_ks:
                    row = pool.rollout(controller, mu, f2_seed(p, k, "val"), plan=name,
                                       plan_group=group, mu_point=round(mu, 4), phase="val", **cell_tag)
                    rows.append(row)
                    rows_out.append(row)
            return rows

        sp = seeker_grid[best_seeker]
        seeker_rows = run_val(lambda p, mu: seeker_builder(*sp, best_seeker), best_seeker, "seeker_val")
        oracle_rows = run_val(lambda p, mu: f2_ramp_cls(reg, cand, f"oracle_dv{oracle_dv[p]:+g}",
                                                        "oracle", mu_true=mu, dv=oracle_dv[p]),
                              "oracle_per_point", "oracle_val")
        fixed_rows = run_val(lambda p, mu: fam2.Family2Controller(plan_by_name[best_fixed], cand),
                             best_fixed, "fixed_val")

        def rate_of(rows, key="success") -> float:
            return float(np.mean([1.0 if x[key] else 0.0 for x in rows]))

        def per_point(rows) -> list[float]:
            return [round(float(np.mean([1.0 if x["success"] else 0.0 for x in rows
                                         if x["mu_point"] == round(mu, 4)])), 3) for mu in mus]

        oracle_val = rate_of(oracle_rows)
        seeker_val = rate_of(seeker_rows)
        fixed_val = rate_of(fixed_rows)
        floor_val = max(seeker_val, fixed_val)
        floor_arm = best_seeker if seeker_val >= fixed_val else best_fixed
        mu_errs = [abs(x["mu_hat"] - x["mu"]) for x in seeker_rows
                   if x.get("mu_hat") is not None and np.isfinite(x.get("mu_hat", float("nan")))
                   and not x.get("censored")]
        summary = {
            "cell_id": cell["cell_id"],
            "kind": cell["kind"],
            "degradation": cell["degradation"],
            "noisy_treatment": cell["noisy"],
            "episodes": pool.episodes,
            "n_val_episodes_per_arm": n_val,
            "detector_variants_offered": [{"smooth_window": w, "tau": t} for w, t in variants],
            "oracle_degraded": {
                "success_val": round(oracle_val, 4),
                "wilson95_val": wilson_ci(oracle_val, n_val),
                "dv_per_point": oracle_dv,
                "per_point_success_val": per_point(oracle_rows),
            },
            "best_seeker": {
                "plan": best_seeker,
                "success_sel": round(seeker_sel[best_seeker][0], 4),
                "success_val": round(seeker_val, 4),
                "wilson95_val": wilson_ci(seeker_val, n_val),
                "collision_val": round(rate_of(seeker_rows, "collided"), 4),
                "timeout_val": round(rate_of(seeker_rows, "timeout"), 4),
                "per_point_success_val": per_point(seeker_rows),
                "mu_abs_err_mean_uncensored": round(float(np.mean(mu_errs)), 4) if mu_errs else None,
                "censored_fraction": round(rate_of(seeker_rows, "censored"), 4),
                "id_step_mean": round(float(np.mean([x.get("id_step", -1) for x in seeker_rows])), 1),
            },
            "best_fixed": {
                "plan": best_fixed,
                "success_val": round(fixed_val, 4),
                "wilson95_val": wilson_ci(fixed_val, n_val),
                "per_point_success_val": per_point(fixed_rows),
            },
            "floor": {"arm": floor_arm, "success_val": round(floor_val, 4),
                      "wilson95_val": wilson_ci(floor_val, n_val)},
            "voi_matched_val": round(oracle_val - floor_val, 4),
            "voi_matched_ci95_newcombe": newcombe_diff_ci(oracle_val, n_val, floor_val, n_val),
        }
        if clean_anchor is not None:
            summary["voi_clean_anchor_val"] = round(float(clean_anchor) - floor_val, 4)
        return summary
    finally:
        pool.close()


# ----------------------------------------------------------------- aggregation


def bridge_table(payload: dict[str, Any], families: list[str]) -> dict[str, Any]:
    lat = payload["latency_bridge_inputs"]
    if "clean" not in lat:
        return {"status": "incomplete", "reason": "clean latency cell missing"}
    clean_med = lat["clean"]["overall"].get("delay_steps_median")
    if clean_med is None:
        return {"status": "incomplete", "reason": "clean latency median missing"}

    delta_l: dict[str, float | None] = {}
    saturated: dict[str, bool] = {}
    for cell in CELLS:
        cid = cell["cell_id"]
        if cid not in lat:
            continue
        ov = lat[cid]["overall"]
        med = ov.get("delay_steps_median")
        miss = float(ov.get("miss_rate", 0.0) or 0.0)
        if med is None or miss > MISS_RATE_SATURATION:
            delta_l[cid] = None  # saturation handled per family below
            saturated[cid] = True
        else:
            delta_l[cid] = max(float(med) - float(clean_med), 0.0)
            saturated[cid] = False

    out: dict[str, Any] = {"clean_latency_median_steps": clean_med,
                           "delta_l_steps": {k: (round(v, 2) if v is not None else None)
                                             for k, v in delta_l.items()},
                           "saturated_cells": [k for k, v in saturated.items() if v],
                           "per_family": {}, "pooled_new_cells": {}}
    pooled_pred, pooled_meas, pooled_rows = [], [], []
    for fam in families:
        cells = {c["cell_id"]: c for c in payload["cells"][fam]}
        xs, ys = [], []
        for cell in CELLS:
            d = cell["pure_delay_steps"]
            cid = cell["cell_id"]
            if d is None or cid not in cells or delta_l.get(cid) is None:
                continue
            xs.append(delta_l[cid])
            ys.append(cells[cid]["voi_matched_val"])
        if len(xs) < 2:
            out["per_family"][fam] = {"status": "incomplete", "reason": "pure-delay curve too short"}
            continue
        order = np.argsort(xs)
        xs_s = list(np.asarray(xs)[order])
        ys_s = list(np.asarray(ys)[order])
        x_max = max(xs_s)
        rows = []
        for cell in CELLS:
            cid = cell["cell_id"]
            if cell["kind"] != "new" or cid not in cells:
                continue
            dl = delta_l.get(cid)
            if dl is None:
                dl = x_max  # pre-registered saturation rule
            pred = float(np.interp(dl, xs_s, ys_s))
            meas = float(cells[cid]["voi_matched_val"])
            agree = (pred >= VOI_BAR) == (meas >= VOI_BAR)
            rows.append({"cell_id": cid, "delta_l_steps": round(float(dl), 2),
                         "delta_l_saturated": bool(saturated.get(cid, False)),
                         "voi_predicted": round(pred, 4), "voi_measured": round(meas, 4),
                         "classification_agree": bool(agree)})
            pooled_pred.append(pred)
            pooled_meas.append(meas)
            pooled_rows.append(agree)
        out["per_family"][fam] = {
            "pure_delay_curve": {"delta_l_steps": [round(float(x), 2) for x in xs_s],
                                 "voi_matched": [round(float(y), 4) for y in ys_s]},
            "new_cells": rows,
        }
    if pooled_rows:
        agreement = float(np.mean([1.0 if a else 0.0 for a in pooled_rows]))
        rho = spearman_rho(pooled_pred, pooled_meas)
        out["pooled_new_cells"] = {
            "n": len(pooled_rows),
            "classification_agreement": round(agreement, 4),
            "agreement_bar": BRIDGE_AGREEMENT_BAR,
            "spearman_predicted_vs_measured": (round(rho, 4) if rho is not None else None),
            "spearman_bar": BRIDGE_SPEARMAN_BAR,
            "bridge_pass": bool(agreement >= BRIDGE_AGREEMENT_BAR
                                and rho is not None and rho >= BRIDGE_SPEARMAN_BAR),
        }
    return out


def ga_gate(payload: dict[str, Any]) -> dict[str, Any]:
    f2_cells = {c["cell_id"]: c for c in payload["cells"].get("family2", [])}
    if "clean" not in f2_cells:
        return {"status": "incomplete", "reason": "family-2 clean cell missing"}
    clean_voi = float(f2_cells["clean"]["voi_matched_val"])
    new_rows = []
    for cell in CELLS:
        if cell["kind"] != "new":
            continue
        c = f2_cells.get(cell["cell_id"])
        if c is None:
            continue
        new_rows.append({"cell_id": cell["cell_id"], "voi_matched_val": c["voi_matched_val"],
                         "at_or_above_bar": bool(c["voi_matched_val"] >= VOI_BAR)})
    n_new = len(new_rows)
    n_above = sum(1 for r in new_rows if r["at_or_above_bar"])
    clean_pass = clean_voi <= CLEAN_BAR
    degraded_pass = n_new > 0 and n_above >= math.ceil(n_new / 2)
    return {
        "criteria": {
            "clean_rule": f"family-2 clean-cell voi_matched_val <= {CLEAN_BAR}",
            "degraded_rule": f"voi_matched_val >= {VOI_BAR} in >= half of the NEW family-2 degraded cells",
        },
        "family2_clean_voi_matched_val": round(clean_voi, 4),
        "clean_pass": bool(clean_pass),
        "new_cells": new_rows,
        "n_new_cells_at_or_above_bar": n_above,
        "n_new_cells": n_new,
        "degraded_pass": bool(degraded_pass),
        "ga_verdict": ("law_replicated_on_family2" if (clean_pass and degraded_pass)
                       else "law_not_replicated_family_specific_scope"),
        "routing": ("route WP1 on both families" if (clean_pass and degraded_pass)
                    else "pre-registered G-A fallback: scope papers family-specific; WP1 still runs on family #1"),
    }


# ------------------------------------------------------------------------ main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="smoke test (tiny grids, subset of cells)")
    parser.add_argument("--full", action="store_true", help="full pre-registered run")
    parser.add_argument("--families", type=str, default="family1,family2")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=2)
    parser.add_argument("--val-seeds", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    if args.quick == args.full:
        parser.error("exactly one of --quick / --full is required")
    quick = args.quick
    run_dir = args.output_dir or (DEFAULT_RUN_DIR.parent / (DEFAULT_RUN_DIR.name + "_quick")
                                  if quick else DEFAULT_RUN_DIR)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows_dir = run_dir / "rows"
    rows_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.jsonl"
    families = [f.strip() for f in args.families.split(",") if f.strip()]
    cells = list(CELLS) if not quick else [c for c in CELLS if c["cell_id"] in QUICK_CELL_IDS]
    if quick:
        args.points, args.sel_seeds, args.val_seeds = 4, 1, 2

    started = time.time()
    prereg = None
    if PREREG_JSON.exists():
        prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    elif args.full:
        raise SystemExit(f"--full requires the frozen pre-registration {PREREG_JSON}")

    reg = load_module(REGIME_SCRIPT, "ramp_policy_voi_regime")
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_a = load_module(SLIP_SCRIPT, "slip_onset_detectability")
    deg_mod = load_module(DEGRADED_SCRIPT, "degraded_regime_final")
    fam2 = load_module(FAMILY2_SCRIPT, "family2_design")
    interp = mod_c.interp_lin
    f1_detector_cls, f1_controller_cls = deg_mod.make_classes(reg)
    f2_detector_cls, f2_ramp_cls = make_f2_classes(reg, deg_mod, fam2)

    spec = json.loads(FAMILY2_SPEC.read_text(encoding="utf-8"))
    assert spec["final_spec"]["status"] == "frozen", "family-2 final_spec must be frozen"
    winner_id = spec["winner"]
    cand = next(c for c in fam2.frozen_candidates() if c.candidate_id == winner_id)

    lo, hi = reg.MU_DOMAIN
    mus = [lo + (i + 0.5) / args.points * (hi - lo) for i in range(args.points)]
    sel_seeds = list(range(args.sel_seeds))
    val_seeds = list(range(args.val_seeds))

    # resume state
    done: dict[str, dict[str, Any]] = {}
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["unit"]] = rec["payload"]

    def mark_done(unit: str, unit_payload: dict[str, Any]) -> None:
        done[unit] = unit_payload
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(fam2.to_jsonable({"unit": unit, "payload": unit_payload})) + "\n")

    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp0_degraded_sweep_bridge_validation",
        "generated_by": "scripts/feasibility_audit/wp0_degraded_sweep.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(quick),
        "preregistration": ({"file": str(PREREG_JSON), "frozen_criteria_echo": prereg}
                            if prereg is not None else None),
        "cells_spec": [dict(c) for c in cells],
        "families": {
            "family1": {"family": "B2K2_final", "reveal_m": REVEAL,
                        "episode_seed_stream": "ramp_policy_voi_regime TierMeasurement.seed_for "
                                               "(20260618 base; val k=0,1 extend the "
                                               "degraded_regime_final anchors)"},
            "family2": {"family": spec["final_spec"]["family_id"], "reveal_m": cand.reveal,
                        "winner": winner_id, "episode_seed_stream":
                            f"SEED_BASE {SEED_BASE}: sel offset 0, val offset 100000, "
                            "calib offset 700000 (20260624 A-D consumed by the design run)"},
        },
        "statistics": {"mu_points": [round(m, 4) for m in mus],
                       "selection_seeds": args.sel_seeds, "validation_seeds": args.val_seeds,
                       "val_episodes_per_arm_per_cell": args.points * args.val_seeds},
        "calibration": {fam: {} for fam in families},
        "latency_bridge_inputs": {},
        "cells": {fam: [] for fam in families},
        "bridge": {},
        "ga_gate": {},
        "status": "running",
    }

    def flush_partial(final: bool = False) -> None:
        from autodrift.artifacts import utc_timestamp
        payload["generated_at_utc"] = utc_timestamp()
        payload["elapsed_s"] = round(time.time() - started, 1)
        target = run_dir / ("summary.json" if final else "summary_partial.json")
        target.write_text(json.dumps(fam2.to_jsonable(payload), indent=2), encoding="utf-8")

    def write_rows(unit: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        from autodrift.artifacts import write_csv_rows
        write_csv_rows(rows_dir / f"{unit}.csv", rows)

    # [1/5] per-(family, cell) detector tau calibration
    print(f"[1/5] tau calibration: {len(families)} families x {len(cells)} cells", flush=True)
    calibrations: dict[tuple[str, str], dict[str, Any]] = {}
    f1_design = reg.make_design(mod_b, REVEAL)
    for fam in families:
        for cell in cells:
            unit = f"calib_{fam}_{cell['cell_id']}"
            if unit in done:
                calibrations[(fam, cell["cell_id"])] = done[unit]
                payload["calibration"][fam][cell["cell_id"]] = done[unit]
                continue
            if fam == "family1":
                pool = make_f1_pool(reg, deg_mod, mod_b, interp, f1_design, cell["degradation"])
                detector_cls, offset = f1_detector_cls, 500_000
            else:
                pool = make_f2_pool(fam2, deg_mod, cand, cell["degradation"])
                detector_cls, offset = f2_detector_cls, 700_000
            try:
                cal = calibrate_cell(reg, mod_a, detector_cls, pool, quick, offset)
            finally:
                pool.close()
            calibrations[(fam, cell["cell_id"])] = cal
            payload["calibration"][fam][cell["cell_id"]] = cal
            mark_done(unit, cal)
            print(f"  {fam} {cell['cell_id']:<18} " +
                  " ".join(f"tau_w{w}={cal[f'w{w}']['tau']:.3f}" for w in ALL_WINDOWS), flush=True)
            flush_partial()

    # [2/5] bridge inputs: measurement-A detection latency per degradation cell
    print(f"[2/5] detection-latency bridge inputs ({len(cells)} cells)", flush=True)
    for ci, cell in enumerate(cells):
        unit = f"latency_{cell['cell_id']}"
        if unit in done:
            payload["latency_bridge_inputs"][cell["cell_id"]] = done[unit]
            continue
        lat_rows: list[dict[str, Any]] = []
        res = latency_cell(reg, deg_mod, mod_a, cell, ci, lat_rows, quick)
        payload["latency_bridge_inputs"][cell["cell_id"]] = res
        write_rows(unit, lat_rows)
        mark_done(unit, res)
        ov = res["overall"]
        print(f"  {cell['cell_id']:<18} tau={res['tau_recalibrated']:.3f} "
              f"median={ov['delay_steps_median']} p90={ov['delay_steps_p90']} "
              f"miss={ov['miss_rate']:.2f}", flush=True)
        flush_partial()

    # [3/5] + [4/5] per-family degraded cells (clean cell first: clean anchor)
    for fam in families:
        stage = "3/5" if fam == "family1" else "4/5"
        print(f"[{stage}] {fam} cells: {len(cells)} x {args.points} pts x "
              f"{args.sel_seeds}+{args.val_seeds} seeds", flush=True)
        ordered = sorted(cells, key=lambda c: c["cell_id"] != "clean")
        clean_anchor: float | None = None
        for cell in ordered:
            unit = f"cell_{fam}_{cell['cell_id']}"
            if unit in done:
                summary = done[unit]
            else:
                t0 = time.time()
                cell_rows: list[dict[str, Any]] = []
                cal = calibrations[(fam, cell["cell_id"])]
                if fam == "family1":
                    summary = measure_cell_f1(reg, deg_mod, mod_b, interp, f1_design, cell, mus,
                                              sel_seeds, val_seeds, cell_rows, f1_controller_cls,
                                              cal, clean_anchor, quick)
                else:
                    summary = measure_cell_f2(fam2, reg, deg_mod, f2_ramp_cls, cand, cell, mus,
                                              sel_seeds, val_seeds, cell_rows, cal,
                                              clean_anchor, quick)
                summary["elapsed_s"] = round(time.time() - t0, 1)
                write_rows(unit, cell_rows)
                mark_done(unit, summary)
            payload["cells"][fam] = [c for c in payload["cells"][fam]
                                     if c["cell_id"] != cell["cell_id"]] + [summary]
            if cell["cell_id"] == "clean":
                clean_anchor = float(summary["oracle_degraded"]["success_val"])
            print(f"  {fam} {cell['cell_id']:<18} oracle={summary['oracle_degraded']['success_val']:.3f} "
                  f"floor={summary['floor']['success_val']:.3f} ({summary['floor']['arm']}) "
                  f"VoI_matched={summary['voi_matched_val']:+.3f} "
                  f"[{summary.get('episodes', '?')} eps {summary.get('elapsed_s', '?')}s]", flush=True)
            flush_partial()
        order_index = {c["cell_id"]: i for i, c in enumerate(cells)}
        payload["cells"][fam].sort(key=lambda c: order_index[c["cell_id"]])

    # [5/5] bridge + G-A verdicts
    print("[5/5] bridge prediction + G-A gate", flush=True)
    payload["bridge"] = bridge_table(payload, families)
    payload["ga_gate"] = ga_gate(payload) if "family2" in families else {"status": "skipped"}
    payload["status"] = "completed"
    payload["artifacts"] = {
        "summary_json": str(run_dir / "summary.json"),
        "progress_jsonl": str(progress_path),
        "rows_dir": str(rows_dir),
        "preregistration_json": str(PREREG_JSON) if prereg is not None else None,
    }
    flush_partial(final=True)
    pooled = payload["bridge"].get("pooled_new_cells", {})
    print(f"results -> {run_dir / 'summary.json'}", flush=True)
    print("HEADLINE: GA=" + str(payload["ga_gate"].get("ga_verdict", "n/a"))
          + f" | bridge_pass={pooled.get('bridge_pass', 'n/a')}"
          + f" agreement={pooled.get('classification_agreement', 'n/a')}"
          + f" spearman={pooled.get('spearman_predicted_vs_measured', 'n/a')}"
          + f" | elapsed {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
