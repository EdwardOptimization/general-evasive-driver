"""Measurement B: VoI of belief over the threshold-seeking ramp-policy family,
as a window-tightness regime map on the B2K2_final task surface.

New-paradigm frame (user mechanism, threshold braking / incremental limit
seeking): identification is embedded in the useful action itself. A real driver
estimates a maximum brake force, ramps toward it, freezes at the first hint of
slip, and muscle-memory-rescues an overshoot. Four loops: prior belief ->
confidence-scaled ramp -> slip-onset edge-holding -> reflex rescue. The old
probe-pulse + blind-commitment paradigm is retired; this script asks the
remaining question: GIVEN a reactive threshold-seeking execution layer, how
much is belief (knowing mu) still worth, and in which operating windows?

Controller classes (all scripted, mu-agnostic except the oracle):
  oracle_ramp   per-mu oracle: knows mu, jumps straight to 95 % of the friction
                limit when braking and tracks the per-mu oracle entry speed
                with a small dv fine-tune selected per (tier, mu point) on
                selection seeds (belief-value upper bound).
  seeker        threshold-seeker family: brake-force ramp from the domain-floor
                limit at rate r; single-frame longitudinal shortfall detector
                (Measurement A's detector is NOT on disk yet -> a simple
                self-implemented shortfall detector is used here and flagged);
                at onset (shortfall > tau) read mu_hat from the realized force,
                back off by delta, optionally re-approach at r/2 (strategy
                hold|retry); then track v*(mu_hat). Detection stays on
                passively (brake AND drive side) whenever |steer| is small, so
                throttle saturation later in the episode refines a censored
                estimate -- identification embedded in whatever useful action
                is running.
  prior_seeker  same seeker, but granted the +/-0.2 mu bin: the ramp starts at
                the bin-lower-bound limit (bypass control arm).
  fixed_speed   entry-speed commitment grid, no detection (lower bound;
                identical to the old-paradigm fixed-plan family).
  fixed_ramp    blind brake ramp to a fixed force fraction for a fixed hold
                time, then commit to whatever speed resulted (no detection).

Task surface: B2K2_final geometry (mu->d knots (0.30,0.55,0.85,1.15) ->
(24,38,47,52) m, jitter +/-0.75 m floor 14.5 m, rewards 40/60, deadline 285
steps, obstacle half-width 1.25, v0=8) with perception_reveal_distance swept
over {9.5, 12, 16, 22, 30} m (tight -> loose). 12 continuous-mu points x
selection/validation seeds; jitter keyed by rollout seed only, so the same
(mu point, seed) episode geometry is identical across tiers.

Outputs (per tier): success matrix per controller class, VoI(belief) = oracle -
best no-belief seeker, VoI(residual | +/-0.2 prior) = oracle - prior-granted
seeker, detection value = best seeker - best no-detection plan; plus a
speed-accuracy frontier (ramp rate x start conservatism -> on-time rate,
overshoot rate) on one pre-registered middle tier.

Physics note used by the detector (src/autodrift/dynamics.py): the rear tire
clamps fx at 0.98*mu*Fzr, so when the commanded/applied brake (or drive) force
exceeds the limit the realized |ax| falls short of applied_force/mass -- the
shortfall IS the slip signal, and the realized force at saturation equals the
limit, giving mu_hat directly. The brake actuator caps at 6000 N < tire limit
for mu > ~0.893: brake-side identification is censored there (reported).

Hard constraints: pure CPU numpy, zero training, deterministic seeds, new files
only, no git operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/ramp_policy_voi_regime.py
    PYTHONPATH=src python scripts/feasibility_audit/ramp_policy_voi_regime.py --quick
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
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/ramp_policy_voi_regime.json"
RUN_DIR = REPO / "runs/feasibility_audit/ramp_policy_voi_regime"

SEED_BASE = 20260618  # fresh stream (cond=20260611, B=20260612, C=20260613, final=20260615, G1'=20260616, C-reflex/probe=20260617)

# ---- B2K2_final geometry (docs/selfid-task-final-spec-2026-06.md +
#      experiments/feasibility_audit/selfid_task_final_spec.json) -------------
MU_DOMAIN = (0.25, 1.15)
MU_KNOTS = (0.30, 0.55, 0.85, 1.15)
D_KNOTS = (24.0, 38.0, 47.0, 52.0)
V_KNOTS = (4.5, 7.5, 9.5, 10.5)  # design-estimate oracle entry speeds
JITTER_D_M = 0.75
D_FLOOR_M = 14.5  # final-spec jitter floor (reveal 9.5 + 5); kept FIXED across tiers
MAX_STEPS = 285
OB_HALF_WIDTH = 1.25
PASS_REWARD, COLLISION_PENALTY = 40.0, 60.0
V0 = 8.0
DT = 0.02

REVEAL_TIERS = (9.5, 12.0, 16.0, 22.0, 30.0)  # tight -> loose

# ---- nominal vehicle constants (degenerate non-mu randomization in this
#      family; public params, NOT the hidden mu) ------------------------------
MASS, GRAV, LF, LR, WHEELBASE = 1450.0, 9.81, 1.35, 1.45, 2.80
FZR = MASS * GRAV * LF / WHEELBASE  # 6858.3 N rear static load
MAX_BRAKE, MAX_DRIVE = 6000.0, 8200.0
TIRE_CAP = 0.98  # dynamics.py clamp fraction
MU_CENSOR = MAX_BRAKE / (TIRE_CAP * FZR)  # ~0.893: brake-side ID ceiling
DRAG_COEFF, ROLLING = 0.34, 75.0
RESCUE_TAU = 0.35  # shortfall depth that counts as an overshoot (reflex-rescue) event

# observation channels (mod_b layout, asserted at runtime)
IDX_VX, IDX_VY, IDX_YAW, IDX_AX, IDX_STEER = 0, 1, 2, 3, 5
IDX_THR_STATE, IDX_BRK_STATE = 7, 8
IDX_OBST_PRESENT = 44

# ---- shared speed laws (calibration: final-spec full-bin oracle entry speeds
#      at reveal 9.5 are ~10.1*sqrt(mu) across all 12 mu points) ---------------
RHO_DODGE = 10.1  # dodge-feasible speed = RHO*sqrt(mu)*(window/9.5), capped
V_CAP = 13.0
DEADLINE_S = MAX_STEPS * DT

# ---- controller family grids ------------------------------------------------
SEEKER_RATES = (800.0, 2000.0, 6000.0, 20000.0)  # N/s
SEEKER_TAUS = (0.08, 0.18)
SEEKER_DELTAS = (0.06, 0.15)
SEEKER_STRATS = ("hold", "retry")
SEEKER_DVMAPS = (0.0, 0.75)  # mu-agnostic global offset on the entry-speed law
PRIOR_RATES = (2000.0, 6000.0, 20000.0)
PRIOR_TAUS = (0.08,)
PRIOR_DELTA, PRIOR_STRAT = 0.10, "hold"
PRIOR_DVMAPS = (0.0, 0.75)
PRIOR_HALF_WIDTH = 0.20
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)
FIXED_SPEED_GRID = (4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5)
FIXED_RAMP_GRID = ((0.35, 1.0), (0.70, 1.0), (1.00, 0.6))  # (force fraction, hold s)
FRONTIER_RATES = (800.0, 2000.0, 6000.0, 20000.0, 60000.0)
FRONTIER_CONSERVATISM = (0.0, 0.3, 0.6, 0.9)  # mu_assumed = 0.25 + c*0.9
SETTLE_STEPS = 10

CLAIM_BOUNDARY = (
    "Feasibility-audit policy-family VoI measurement only: scripted threshold-seeking ramp "
    "controllers (with a self-implemented single-frame shortfall detector standing in for the "
    "not-yet-materialized Measurement-A detector), a per-mu oracle ramp, prior-granted and "
    "no-detection control arms are rolled out on the B2K2_final family with the perception "
    "reveal distance swept. No driver promotion, training, repair-success, gate-validity, "
    "paper, or self-ID capability claim is made."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------- task surface


def d_of_mu(interp, mu: float) -> float:
    return float(interp(mu, MU_KNOTS, D_KNOTS))


def v_star(interp, mu: float) -> float:
    return float(np.clip(interp(mu, MU_KNOTS, V_KNOTS), 3.8, 14.5))


def jittered_distance(interp, mu: float, rollout_seed: int) -> float:
    base = d_of_mu(interp, mu)
    eps = float(np.random.default_rng([SEED_BASE, 777, int(rollout_seed)]).uniform(-JITTER_D_M, JITTER_D_M))
    return max(base + eps, D_FLOOR_M)


def make_design(mod_b, reveal: float):
    b2 = next(d for d in mod_b.candidate_designs() if d.design_id == "B2_mu_correlated_hazard_tight")
    return dataclasses.replace(
        b2,
        design_id=f"B2K2_final_reveal{reveal:g}",
        reveal_distance=reveal,
        max_steps=MAX_STEPS,
        obstacle_half_width=OB_HALF_WIDTH,
        pass_reward=PASS_REWARD,
        collision_penalty=COLLISION_PENALTY,
    )


class EnvPool:
    """Per-(mu, jittered d) degenerate env configs for ONE reveal tier, keyed by
    rollout seed (jitter depends on the seed only -> identical geometry across
    tiers for the same (mu point, seed))."""

    def __init__(self, mod_b, interp, design):
        from autodrift.config import build_env_config
        from autodrift.env import AutoDriftEnv

        self._build = build_env_config
        self._env_cls = AutoDriftEnv
        self.mod_b, self.interp, self.design = mod_b, interp, design
        self._cache: dict[tuple[float, int], Any] = {}
        self.episodes = 0

    def env_for(self, mu: float, seed: int):
        key = (round(mu, 6), int(seed))
        if key not in self._cache:
            d = jittered_distance(self.interp, mu, seed)
            level = self.mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d, entry_speed=v_star(self.interp, mu))
            env = self._env_cls(self._build(self.mod_b.level_env_config(self.design, level)))
            assert env.base_obs_dim == self.mod_b.OBS_DIM
            self._cache[key] = env
        return self._cache[key]

    def rollout(self, controller, mu: float, seed: int, **tags) -> dict[str, Any]:
        env = self.env_for(mu, seed)
        row = self.mod_b.rollout(env, controller, seed)
        self.episodes += 1
        bucket = row["outcome_bucket"]
        row["passed"] = bool(bucket == "success_obstacle_pass")
        row["collided"] = bool(bucket == "collision_failure")
        row["timeout"] = bool(bucket == "max_steps_noncompletion")
        row["on_time"] = bool(row["passed"] or row["collided"])  # reached the obstacle zone by deadline
        row["d_jittered"] = round(jittered_distance(self.interp, mu, seed), 3)
        telemetry = getattr(controller, "telemetry_row", None)
        row.update(telemetry() if callable(telemetry) else {})
        row.update(tags)
        return row

    def close(self) -> None:
        for env in self._cache.values():
            env.close()
        self._cache.clear()


# ------------------------------------------------------------------- detector


class ShortfallDetector:
    """Single-frame longitudinal shortfall detector (simple stand-in for the
    Measurement-A detector, which is not on disk yet).

    Uses only on-board channels: vx, vy, yaw_rate, ax, steer, and the actuator
    force states obs[7]/obs[8] (lagged applied force -> no lag model needed).
    Realized rear longitudinal force = m*(ax - yaw_rate*vy) + drag + rolling
    (front-lateral coupling term ignored; updates gated to |steer| < 0.06 rad).
    shortfall = 1 - realized/applied; onset when shortfall > tau with the
    realized force then equal to the tire limit -> mu_hat = realized/(0.98*Fzr).
    shortfall > RESCUE_TAU counts as an overshoot (reflex-rescue) event.
    """

    def __init__(self, tau: float):
        self.tau = tau
        self.reset()

    def reset(self) -> None:
        self.onset = False  # event flag for the current frame
        self.onset_side: str | None = None
        self.mu_sample: float | None = None
        self.max_shortfall = 0.0
        self.overshoot_events = 0
        self._deep_prev = False
        self.brake_onset_seen = False
        self.n_onsets = 0
        self.samples: list[float] = []

    def update(self, obs: np.ndarray) -> None:
        self.onset = False
        self.onset_side = None
        self.mu_sample = None
        vx = float(obs[IDX_VX]) * 20.0
        vy = float(obs[IDX_VY]) * 12.0
        yaw = float(obs[IDX_YAW]) * 2.5
        ax = float(obs[IDX_AX]) * 15.0
        ay = float(obs[4]) * 15.0
        steer = float(obs[IDX_STEER]) * 0.62
        thr = float(obs[IDX_THR_STATE])
        brk = float(obs[IDX_BRK_STATE])
        # gates: the single-frame model ignores front-lateral coupling, so only
        # near-straight, low-sideslip frames are trusted (false low-mu samples
        # otherwise appear during the swerve).
        if abs(steer) > 0.05 or abs(ay) > 1.0 or abs(vy) > 0.4 or vx < 2.0:
            self._deep_prev = False
            return
        resist = DRAG_COEFF * vx * abs(vx) + ROLLING * math.tanh(vx)
        fx_rear = MASS * (ax - yaw * vy) + resist
        if brk * MAX_BRAKE > 400.0:
            applied, realized = brk * MAX_BRAKE, -fx_rear
            side = "brake"
        elif thr * MAX_DRIVE > 600.0:
            applied, realized = thr * MAX_DRIVE, fx_rear
            side = "drive"
        else:
            self._deep_prev = False
            return
        realized = max(realized, 0.0)
        shortfall = 1.0 - realized / applied
        self.max_shortfall = max(self.max_shortfall, shortfall)
        if shortfall > self.tau and realized > 200.0:
            self.onset = True
            self.onset_side = side
            self.mu_sample = realized / (TIRE_CAP * FZR)
            self.samples.append(self.mu_sample)
            self.n_onsets += 1
            if side == "brake":
                self.brake_onset_seen = True
        deep = shortfall > RESCUE_TAU
        if deep and not self._deep_prev:
            self.overshoot_events += 1
        self._deep_prev = deep


# ---------------------------------------------------------- ramp policy family


class RampPolicyController:
    """Threshold-seeking ramp policy wrapper around mod_b.CommitmentController.

    The inner controller supplies steering, reveal bookkeeping and the
    post-reveal brake->swerve reaction; this wrapper owns the longitudinal
    channel pre-reveal (settle -> ramp -> [reapproach] -> limit_hold -> track)
    and caps the post-reveal bang-bang brake at the believed force limit.
    Modes: seeker | prior | oracle | fixed_ramp.
    """

    def __init__(self, mod_b, interp, design, name: str, mode: str, *,
                 ramp_rate: float = 6000.0, tau: float = 0.08, backoff: float = 0.06,
                 strategy: str = "hold", mu_start: float = MU_DOMAIN[0],
                 mu_true: float | None = None, dv: float = 0.0,
                 prior_lo: float | None = None,
                 fixed_frac: float | None = None, fixed_hold_s: float | None = None):
        self.mod_b, self.interp, self.design = mod_b, interp, design
        self.name, self.mode = name, mode
        self.ramp_rate, self.backoff, self.strategy = ramp_rate, backoff, strategy
        self.mu_start, self.mu_true, self.dv = mu_start, mu_true, dv
        self.prior_lo = prior_lo
        self.fixed_frac, self.fixed_hold_s = fixed_frac, fixed_hold_s
        self.reveal = design.reveal_distance
        plan = mod_b.PlanSpec(name=name, v_entry=V0, brake_to=V0 - 1.0, steer_cap=0.85)
        self.inner = mod_b.CommitmentController(plan, design)
        self.detector = ShortfallDetector(tau)
        self.reset()

    # delegate bookkeeping attributes used by mod_b.rollout
    def __getattr__(self, name):
        if name == "inner":
            raise AttributeError(name)
        return getattr(self.inner, name)

    def reset(self) -> None:
        self.inner.reset()
        self.detector.reset()
        self.k = 0
        self.phase = "settle"
        self.mu_hat: float | None = self.mu_true if self.mode == "oracle" else None
        self.mu_floor = self.prior_lo if self.prior_lo is not None else MU_DOMAIN[0]
        self.censored = False
        self.id_step = -1
        self.retried = False
        self._mu_first: float | None = None
        self._hold_count = 0
        self._cap_count = 0
        self.f_cmd = 0.95 * TIRE_CAP * FZR * self.mu_start
        self.v_commit: float | None = None
        self._brake_to_frozen: float | None = None
        self._mu_at_freeze: float | None = None

    # -- belief helpers --------------------------------------------------------
    def _mu_eff(self) -> float:
        if self.mode == "oracle":
            return self.mu_true
        return self.mu_hat if self.mu_hat is not None else self.mu_floor

    def _v_dodge(self, mu: float, window_m: float) -> float:
        return float(min(RHO_DODGE * math.sqrt(max(mu, 0.05)) * max(window_m, 2.0) / 9.5, V_CAP))

    def _v_target(self) -> float:
        """Entry-speed law shared by oracle/seeker/prior: midpoint of the
        [deadline floor vd, dodge-feasible cap vr(mu, tier reveal)] band, at
        least vd+0.3, never above vr; oracle adds its fine-tune dv, seekers a
        mu-agnostic map offset dv (selected per tier)."""
        if self.mode == "fixed_ramp":
            return self.v_commit if self.v_commit is not None else V0
        mu_eff = self._mu_eff()
        d_rem = d_of_mu(self.interp, mu_eff) - self.inner.dist + 2.5
        t_rem = max(DEADLINE_S - self.k * DT, 0.5)
        vd = max(d_rem, 0.0) / t_rem
        vr = self._v_dodge(mu_eff, self.reveal)
        base = min(max(0.5 * (vd + vr), vd + 0.3), vr)
        return float(np.clip(base + self.dv, 3.9, V_CAP))

    def _limit_est(self) -> float | None:
        if self.mode == "oracle":
            return TIRE_CAP * FZR * self.mu_true
        if self.mu_hat is not None:
            return TIRE_CAP * FZR * self.mu_hat
        return None

    def _reaction_brake_to(self, obs: np.ndarray, vx: float) -> float:
        """Window-aware reaction hold speed, frozen at the observed reveal
        window (re-derived only when mu_hat changes): dodge-feasible speed for
        (mu_eff, bx_at_reveal), never above the reveal-crossing speed."""
        mu_eff = self._mu_eff()
        if self._brake_to_frozen is None or self._mu_at_freeze != mu_eff:
            bx = float(obs[45]) * 80.0
            if self._brake_to_frozen is None:
                self._bx_rev = max(bx, 2.0)
                v_rev = self.inner.speed_at_reveal
                self._v_rev = vx if not np.isfinite(v_rev) else max(v_rev, vx)
            self._brake_to_frozen = float(np.clip(min(self._v_dodge(mu_eff, self._bx_rev), self._v_rev), 3.8, V_CAP))
            self._mu_at_freeze = mu_eff
        return self._brake_to_frozen

    def _ingest_detection(self) -> None:
        det = self.detector
        if det.onset and det.mu_sample is not None and self.mode in ("seeker", "prior"):
            if self.mu_hat is None or self.censored:
                self.id_step = self.k if self.mu_hat is None else self.id_step
                self.censored = False
            self.mu_hat = float(np.clip(np.median(det.samples[-5:]), 0.10, 1.40))

    # -- longitudinal phase machine (pre-reveal) -------------------------------
    def _longitudinal(self, obs: np.ndarray, vx: float) -> tuple[float, float]:
        det = self.detector
        brk_state = float(obs[IDX_BRK_STATE])
        v_t = self._v_target()

        if self.mode == "oracle":
            if vx > v_t + 0.2:
                frac = min(0.95 * self._limit_est() / MAX_BRAKE, 1.0)
                return -1.0, 2.0 * frac - 1.0
            return self.inner._speed_actions(vx, v_t)

        if self.phase == "settle":
            if self.k >= SETTLE_STEPS:
                self.phase = "ramp" if self.mode in ("seeker", "prior", "fixed_ramp") else "track"
            return self.inner._speed_actions(vx, V0)

        if self.mode == "fixed_ramp":
            if self.phase == "ramp":
                target = self.fixed_frac * MAX_BRAKE
                self.f_cmd = min(self.f_cmd + 4000.0 * DT, target)
                if self.k >= SETTLE_STEPS + int(self.fixed_hold_s / DT):
                    self.v_commit = max(vx, 3.8)
                    self.phase = "track"
                return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0
            return self.inner._speed_actions(vx, self._v_target())

        # seeker / prior phases
        if self.phase == "ramp":
            self.f_cmd += self.ramp_rate * DT
            if det.onset and det.onset_side == "brake":
                if self.strategy == "retry" and not self.retried:
                    self.retried = True
                    self._mu_first = self.mu_hat
                    self.phase = "reapproach_hold"
                    self._hold_count = 0
                else:
                    self.phase = "limit_hold"
            elif self.f_cmd >= MAX_BRAKE and brk_state >= 0.965:
                self._cap_count += 1
                if self._cap_count >= 8:  # actuator-cap censoring: tire never slipped
                    self.censored = True
                    self.mu_hat = MU_CENSOR
                    self.id_step = self.k
                    self.phase = "track"
            elif vx < 4.0:  # ran out of speed before onset: conservative lower bound
                self.censored = True
                self.mu_hat = max(brk_state * MAX_BRAKE / (TIRE_CAP * FZR), self.mu_floor)
                self.id_step = self.k
                self.phase = "track"
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        if self.phase == "reapproach_hold":
            self._hold_count += 1
            self.f_cmd = (1.0 - 2.0 * self.backoff) * (self._limit_est() or 0.3 * MAX_BRAKE)
            if self._hold_count >= 8:
                self.phase = "reapproach_ramp"
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        if self.phase == "reapproach_ramp":
            self.f_cmd += 0.5 * self.ramp_rate * DT
            if det.onset and det.onset_side == "brake":
                self.phase = "limit_hold"
            elif self.f_cmd >= MAX_BRAKE and brk_state >= 0.965:
                self.phase = "limit_hold"
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        if self.phase == "limit_hold":
            # edge-holding: keep braking at (1-delta)*limit while still above the
            # mu_hat-implied target speed (the identification act doubles as the
            # useful slow-down), then release.
            v_t = self._v_target()
            if vx <= v_t + 0.25:
                self.phase = "track"
                return self.inner._speed_actions(vx, v_t)
            self.f_cmd = (1.0 - self.backoff) * (self._limit_est() or 0.3 * MAX_BRAKE)
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        return self.inner._speed_actions(vx, self._v_target())

    # -- policy ----------------------------------------------------------------
    def act(self, obs: np.ndarray) -> np.ndarray:
        obs = np.asarray(obs, dtype=np.float64)
        self.detector.update(obs)
        self._ingest_detection()
        vx = float(obs[IDX_VX]) * 20.0
        v_t = self._v_target()
        object.__setattr__(self.inner.plan, "v_entry", float(v_t))
        pre_reveal = self.inner.reveal_step is None and float(obs[IDX_OBST_PRESENT]) <= 0.5
        if pre_reveal:
            object.__setattr__(self.inner.plan, "brake_to", float(max(v_t - 1.0, 3.5)))
        elif self.mode == "fixed_ramp":
            object.__setattr__(self.inner.plan, "brake_to", None)  # swerve-only commitment
        else:
            object.__setattr__(self.inner.plan, "brake_to", self._reaction_brake_to(obs, vx))
        action = self.inner.act(obs)
        if pre_reveal:
            thr, brk = self._longitudinal(obs, vx)
            action[1], action[2] = thr, brk
        else:
            if action[1] <= -0.99 and action[2] >= 0.99:  # inner full-brake phase
                limit = self._limit_est()
                if limit is not None:
                    frac = 0.95 if self.mode == "oracle" else (1.0 - self.backoff)
                    action[2] = 2.0 * min(frac * limit / MAX_BRAKE, 1.0) - 1.0
                # else: unidentified -> keep full brake (detector reads mu live)
        self.k += 1
        return action

    def telemetry_row(self) -> dict[str, Any]:
        return {
            "mu_hat": float("nan") if self.mu_hat is None else round(float(self.mu_hat), 4),
            "censored": bool(self.censored),
            "id_step": int(self.id_step),
            "overshoot_events": int(self.detector.overshoot_events),
            "max_shortfall": round(float(self.detector.max_shortfall), 4),
            "n_onsets": int(self.detector.n_onsets),
            "v_target_final": round(float(self._v_target()), 3),
            "phase_final": self.phase,
        }


# ----------------------------------------------------------------- measurement


class TierMeasurement:
    """All controller classes on the 12-point mu grid of one reveal tier."""

    def __init__(self, mod_b, interp, design, tier_idx: int, reveal: float,
                 mus: list[float], sel_seeds: list[int], val_seeds: list[int],
                 rows_out: list[dict[str, Any]]):
        self.mod_b, self.interp, self.design = mod_b, interp, design
        self.tier_idx, self.reveal = tier_idx, reveal
        self.mus, self.sel_seeds, self.val_seeds = mus, sel_seeds, val_seeds
        self.pool = EnvPool(mod_b, interp, design)
        self.rows_out = rows_out
        self.results: dict[str, list[dict[str, list[dict[str, Any]]]]] = {}
        self.groups: dict[str, str] = {}
        self.builders: dict[str, Callable[[], Any]] = {}

    def seed_for(self, point: int, k: int, phase: str) -> int:
        return SEED_BASE * 10 + 17 * point + 1000 * k + (0 if phase == "sel" else 100000)

    def register(self, name: str, group: str, builder: Callable[[], Any]) -> None:
        self.results.setdefault(name, [{"sel": [], "val": []} for _ in self.mus])
        self.groups[name] = group
        self.builders[name] = builder

    def eval(self, name: str, points: list[int] | None = None, phase: str = "sel") -> None:
        points = points if points is not None else list(range(len(self.mus)))
        seeds = self.sel_seeds if phase == "sel" else self.val_seeds
        slot = self.results[name]
        controller = self.builders[name]()
        for point in points:
            if slot[point][phase]:
                continue
            rows = []
            for k in seeds:
                seed = self.seed_for(point, k, phase)
                row = self.pool.rollout(
                    controller, self.mus[point], seed,
                    reveal_tier=self.reveal, plan=name, plan_group=self.groups[name],
                    mu_point=round(self.mus[point], 4), phase=phase,
                )
                rows.append(row)
                self.rows_out.append(row)
            slot[point][phase] = rows

    def point_stat(self, name: str, point: int, phase: str, key: str) -> float:
        rows = self.results[name][point][phase]
        if not rows:
            return float("nan")
        return float(np.mean([float(r[key]) if not isinstance(r[key], bool) else (1.0 if r[key] else 0.0)
                              for r in rows]))

    def tier_mean(self, name: str, phase: str, key: str = "success") -> float:
        return float(np.mean([self.point_stat(name, p, phase, key) for p in range(len(self.mus))]))

    def best_in_group(self, group: str) -> str:
        names = [n for n in self.results if self.groups[n] == group and self.results[n][0]["sel"]]
        return max(names, key=lambda n: (self.tier_mean(n, "sel", "success"), self.tier_mean(n, "sel", "return")))


def seeker_name(r: float, tau: float, delta: float, strat: str, dv: float) -> str:
    return f"seeker_r{r:g}_t{tau:g}_d{delta:g}_{strat}_v{dv:+g}"


def measure_tier(mod_b, interp, design, tier_idx: int, reveal: float, mus: list[float],
                 sel_seeds: list[int], val_seeds: list[int], rows_out: list[dict[str, Any]],
                 quick: bool) -> tuple[dict[str, Any], TierMeasurement]:
    tm = TierMeasurement(mod_b, interp, design, tier_idx, reveal, mus, sel_seeds, val_seeds, rows_out)
    n_pts = len(mus)

    def ramp(name, **kw):
        return lambda: RampPolicyController(mod_b, interp, design, name, **kw)

    # [1] register the zoo
    rates = SEEKER_RATES if not quick else (2000.0, 20000.0)
    taus = SEEKER_TAUS if not quick else (0.08,)
    deltas = SEEKER_DELTAS if not quick else (0.06,)
    strats = SEEKER_STRATS if not quick else ("hold",)
    dvmaps = SEEKER_DVMAPS if not quick else (0.0,)
    for r in rates:
        for tau in taus:
            for delta in deltas:
                for strat in strats:
                    for dv in dvmaps:
                        name = seeker_name(r, tau, delta, strat, dv)
                        tm.register(name, "seeker", ramp(name, mode="seeker", ramp_rate=r, tau=tau,
                                                         backoff=delta, strategy=strat, dv=dv))
    for v in (FIXED_SPEED_GRID if not quick else (4.5, 7.5, 10.5)):
        # swerve-only commitment = the validated old-paradigm adversary family
        plan = mod_b.PlanSpec(name=f"fixed_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        tm.register(plan.name, "fixed_speed", (lambda p=plan: mod_b.CommitmentController(p, design)))
    for frac, hold_s in (FIXED_RAMP_GRID if not quick else FIXED_RAMP_GRID[:1]):
        name = f"fixedramp_f{frac:g}_h{hold_s:g}"
        tm.register(name, "fixed_ramp", ramp(name, mode="fixed_ramp", fixed_frac=frac, fixed_hold_s=hold_s))

    # evaluate the mu-agnostic zoo on selection seeds
    for name in list(tm.results):
        tm.eval(name, phase="sel")

    # prior-granted seekers (bin depends on the episode mu -> per-point builders)
    prior_grid = [(r, tau, dv) for r in (PRIOR_RATES if not quick else (6000.0,))
                  for tau in (PRIOR_TAUS if not quick else (0.08,))
                  for dv in (PRIOR_DVMAPS if not quick else (0.0,))]
    prior_names = []
    for r, tau, dv in prior_grid:
        name = f"prior_r{r:g}_t{tau:g}_v{dv:+g}"
        prior_names.append(name)
        tm.register(name, "prior_seeker", lambda: None)  # placeholder builder
    for point, mu in enumerate(mus):
        lo = max(MU_DOMAIN[0], mu - PRIOR_HALF_WIDTH)
        for (r, tau, dv), name in zip(prior_grid, prior_names):
            tm.builders[name] = ramp(name, mode="prior", ramp_rate=r, tau=tau, backoff=PRIOR_DELTA,
                                     strategy=PRIOR_STRAT, mu_start=lo, prior_lo=lo, dv=dv)
            tm.eval(name, points=[point], phase="sel")

    # per-mu oracle with dv fine-tune (selection on sel seeds, per point)
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

    # [2] selection -> validation
    best_seeker = tm.best_in_group("seeker")
    best_prior = tm.best_in_group("prior_seeker")
    best_fixed_speed = tm.best_in_group("fixed_speed")
    best_fixed_ramp = tm.best_in_group("fixed_ramp")
    for point, mu in enumerate(mus):
        lo = max(MU_DOMAIN[0], mu - PRIOR_HALF_WIDTH)
        # rebind point-dependent builders before validating that point
        r, tau, dv = prior_grid[prior_names.index(best_prior)]
        tm.builders[best_prior] = ramp(best_prior, mode="prior", ramp_rate=r, tau=tau,
                                       backoff=PRIOR_DELTA, strategy=PRIOR_STRAT, mu_start=lo,
                                       prior_lo=lo, dv=dv)
        dv = float(oracle_choice[point].split("dv")[1])
        tm.builders[oracle_choice[point]] = ramp(oracle_choice[point], mode="oracle", mu_true=mu, dv=dv)
        tm.eval(oracle_choice[point], points=[point], phase="val")
        tm.eval(best_prior, points=[point], phase="val")
    tm.eval(best_seeker, phase="val")
    tm.eval(best_fixed_speed, phase="val")
    tm.eval(best_fixed_ramp, phase="val")

    # [3] aggregates
    def oracle_mean(phase: str, key: str = "success") -> float:
        return float(np.mean([tm.point_stat(oracle_choice[p], p, phase, key) for p in range(n_pts)]))

    def pack(name: str) -> dict[str, Any]:
        return {
            "plan": name,
            "success_sel": round(tm.tier_mean(name, "sel"), 4),
            "success_val": round(tm.tier_mean(name, "val"), 4),
            "on_time_val": round(tm.tier_mean(name, "val", "on_time"), 4),
            "collision_val": round(tm.tier_mean(name, "val", "collided"), 4),
            "per_point_success_val": [round(tm.point_stat(name, p, "val", "success"), 3) for p in range(n_pts)],
        }

    oracle_val = oracle_mean("val")
    seeker_val = tm.tier_mean(best_seeker, "val")
    prior_val = tm.tier_mean(best_prior, "val")
    fixed_val = max(tm.tier_mean(best_fixed_speed, "val"), tm.tier_mean(best_fixed_ramp, "val"))
    seeker_rows_sel = [r for name in tm.results if tm.groups[name] == "seeker"
                       for p in range(n_pts) for r in tm.results[name][p]["sel"]]
    summary = {
        "reveal_distance_m": reveal,
        "n_mu_points": n_pts,
        "mu_points": [round(m, 4) for m in mus],
        "episodes": tm.pool.episodes,
        "oracle": {
            "success_sel": round(oracle_mean("sel"), 4),
            "success_val": round(oracle_val, 4),
            "on_time_val": round(oracle_mean("val", "on_time"), 4),
            "plan_per_point": oracle_choice,
            "per_point_success_val": [round(tm.point_stat(oracle_choice[p], p, "val", "success"), 3)
                                      for p in range(n_pts)],
        },
        "best_seeker": pack(best_seeker),
        "best_prior_seeker": pack(best_prior),
        "best_fixed_speed": pack(best_fixed_speed),
        "best_fixed_ramp": pack(best_fixed_ramp),
        "voi_belief_val": round(oracle_val - seeker_val, 4),
        "voi_belief_sel": round(oracle_mean("sel") - tm.tier_mean(best_seeker, "sel"), 4),
        "voi_residual_prior_val": round(oracle_val - prior_val, 4),
        "detection_value_val": round(seeker_val - fixed_val, 4),
        "seeker_family_sel_means": {
            n: round(tm.tier_mean(n, "sel"), 4) for n in sorted(tm.results)
            if tm.groups[n] == "seeker"
        },
        "seeker_telemetry_sel": {
            "overshoot_episode_fraction": round(float(np.mean([1.0 if r.get("overshoot_events", 0) > 0 else 0.0
                                                               for r in seeker_rows_sel])), 4),
            "censored_fraction": round(float(np.mean([1.0 if r.get("censored") else 0.0
                                                      for r in seeker_rows_sel])), 4),
            "mu_abs_err_mean_uncensored": round(float(np.nanmean([
                abs(r["mu_hat"] - r["mu"]) for r in seeker_rows_sel
                if r.get("mu_hat") is not None and not r.get("censored") and np.isfinite(r.get("mu_hat", float("nan")))
            ])), 4) if seeker_rows_sel else None,
        },
    }
    return summary, tm


# -------------------------------------------------------------------- frontier


def run_frontier(mod_b, interp, design, reveal: float, mus: list[float], sel_seeds: list[int],
                 rows_out: list[dict[str, Any]], quick: bool) -> dict[str, Any]:
    pool = EnvPool(mod_b, interp, design)
    rates = FRONTIER_RATES if not quick else (2000.0, 20000.0)
    cons = FRONTIER_CONSERVATISM if not quick else (0.0, 0.6)
    points = []
    try:
        for r in rates:
            for c in cons:
                mu_assumed = MU_DOMAIN[0] + c * (MU_DOMAIN[1] - MU_DOMAIN[0])
                name = f"frontier_r{r:g}_c{c:g}"
                controller = RampPolicyController(mod_b, interp, design, name, mode="seeker",
                                                  ramp_rate=r, tau=0.08, backoff=0.06,
                                                  strategy="hold", mu_start=mu_assumed)
                rows = []
                for p, mu in enumerate(mus):
                    for k in sel_seeds:
                        seed = SEED_BASE * 10 + 17 * p + 1000 * k + 500000
                        row = pool.rollout(controller, mu, seed, reveal_tier=reveal, plan=name,
                                           plan_group="frontier", mu_point=round(mu, 4), phase="frontier")
                        rows.append(row)
                        rows_out.append(row)
                points.append({
                    "ramp_rate_nps": r,
                    "start_conservatism": c,
                    "mu_assumed_start": round(mu_assumed, 3),
                    "success": round(float(np.mean([r_["success"] for r_ in rows])), 4),
                    "on_time_rate": round(float(np.mean([1.0 if r_["on_time"] else 0.0 for r_ in rows])), 4),
                    "overshoot_rate": round(float(np.mean([1.0 if r_.get("overshoot_events", 0) > 0 else 0.0
                                                           for r_ in rows])), 4),
                    "collision_rate": round(float(np.mean([1.0 if r_["collided"] else 0.0 for r_ in rows])), 4),
                    "timeout_rate": round(float(np.mean([1.0 if r_["timeout"] else 0.0 for r_ in rows])), 4),
                    "mean_max_shortfall": round(float(np.mean([r_.get("max_shortfall", 0.0) for r_ in rows])), 4),
                    "mean_id_step": round(float(np.mean([r_.get("id_step", -1) for r_ in rows])), 1),
                })
        return {"grid_points": points, "episodes": pool.episodes,
                "fixed_params": {"tau": 0.08, "delta": 0.06, "strategy": "hold"},
                "seed_note": "frontier stream = regime sel seeds + 500000"}
    finally:
        pool.close()


# -------------------------------------------------------------- detector check


def detector_self_check(mod_b, interp, quick: bool) -> list[dict[str, Any]]:
    """Stand-in validation for the missing Measurement-A detector: ramp on a
    late-reveal env at known mu (pre-reveal ID window exists at every mu),
    compare mu_hat with truth."""
    design = make_design(mod_b, 9.5)
    pool = EnvPool(mod_b, interp, design)
    out = []
    try:
        for mu in ((0.30, 0.55, 0.80, 1.05) if not quick else (0.30, 0.80)):
            for r in ((2000.0, 20000.0) if not quick else (6000.0,)):
                name = f"check_mu{mu:g}_r{r:g}"
                controller = RampPolicyController(mod_b, interp, design, name, mode="seeker",
                                                  ramp_rate=r, tau=0.08, backoff=0.06, strategy="hold")
                row = pool.rollout(controller, mu, SEED_BASE * 10 + 900000, reveal_tier=9.5,
                                   plan=name, plan_group="detector_check", mu_point=mu, phase="check")
                out.append({
                    "mu_true": mu, "ramp_rate": r,
                    "mu_hat": row.get("mu_hat"), "censored": row.get("censored"),
                    "id_step": row.get("id_step"),
                    "abs_err": (round(abs(row["mu_hat"] - mu), 4)
                                if row.get("mu_hat") is not None and np.isfinite(row.get("mu_hat", float("nan")))
                                else None),
                })
        return out
    finally:
        pool.close()


# ------------------------------------------------------------------------ main


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=2)
    parser.add_argument("--val-seeds", type=int, default=2)
    parser.add_argument("--results-json", type=Path, default=RESULTS_JSON)
    args = parser.parse_args()
    tiers = REVEAL_TIERS
    if args.quick:
        args.points, args.sel_seeds, args.val_seeds = 4, 1, 1
        tiers = (9.5, 30.0)

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    interp = mod_c.interp_lin

    lo, hi = MU_DOMAIN
    mus = [lo + (i + 0.5) / args.points * (hi - lo) for i in range(args.points)]
    sel_seeds = list(range(args.sel_seeds))
    val_seeds = list(range(args.val_seeds))
    rows_out: list[dict[str, Any]] = []

    print(f"[1/4] detector self-check (Measurement-A detector not on disk; simple shortfall stand-in)")
    det_check = detector_self_check(mod_b, interp, args.quick)
    for c in det_check:
        print(f"  mu={c['mu_true']:.2f} r={c['ramp_rate']:g} -> mu_hat={c['mu_hat']} "
              f"censored={c['censored']} err={c['abs_err']}")

    print(f"[2/4] regime sweep: {len(tiers)} reveal tiers x {args.points} mu points x "
          f"{args.sel_seeds}+{args.val_seeds} seeds")
    tier_summaries = []
    for tier_idx, reveal in enumerate(tiers):
        t0 = time.time()
        design = make_design(mod_b, reveal)
        summary, tm = measure_tier(mod_b, interp, design, tier_idx, reveal, mus,
                                   sel_seeds, val_seeds, rows_out, args.quick)
        tm.pool.close()
        summary["elapsed_s"] = round(time.time() - t0, 1)
        tier_summaries.append(summary)
        print(f"  reveal={reveal:>4.1f} m | oracle={summary['oracle']['success_val']:.3f} "
              f"seeker={summary['best_seeker']['success_val']:.3f} ({summary['best_seeker']['plan']}) "
              f"prior={summary['best_prior_seeker']['success_val']:.3f} "
              f"fixed={max(summary['best_fixed_speed']['success_val'], summary['best_fixed_ramp']['success_val']):.3f} | "
              f"VoI(belief)={summary['voi_belief_val']:+.3f} "
              f"VoI(res|prior)={summary['voi_residual_prior_val']:+.3f} "
              f"detect_value={summary['detection_value_val']:+.3f} "
              f"[{summary['episodes']} eps, {summary['elapsed_s']}s]")

    # [3] frontier on the pre-registered middle tier: the tier whose validated
    # VoI(belief) is closest to the midpoint of (min, max) across tiers; if the
    # spread is < 0.02 (flat regime map), fall back to reveal=12.
    vois = [s["voi_belief_val"] for s in tier_summaries]
    if max(vois) - min(vois) < 0.02:
        frontier_tier = 12.0 if 12.0 in tiers else tiers[min(1, len(tiers) - 1)]
        frontier_rule = "flat regime map (<0.02 spread) -> fallback reveal=12"
    else:
        mid = 0.5 * (max(vois) + min(vois))
        frontier_tier = tiers[int(np.argmin([abs(v - mid) for v in vois]))]
        frontier_rule = "tier with VoI(belief) closest to midpoint(min,max)"
    print(f"[3/4] speed-accuracy frontier on reveal={frontier_tier:g} m ({frontier_rule})")
    design_f = make_design(mod_b, frontier_tier)
    frontier = run_frontier(mod_b, interp, design_f, frontier_tier, mus, sel_seeds, rows_out, args.quick)
    frontier["reveal_tier_m"] = frontier_tier
    frontier["tier_selection_rule"] = frontier_rule
    ft = next(s for s in tier_summaries if s["reveal_distance_m"] == frontier_tier)
    frontier["reference_points_from_regime_stage_val"] = {
        "oracle": {"success": ft["oracle"]["success_val"], "on_time": ft["oracle"]["on_time_val"]},
        "best_seeker": {"success": ft["best_seeker"]["success_val"], "on_time": ft["best_seeker"]["on_time_val"],
                        "plan": ft["best_seeker"]["plan"]},
        "best_prior_seeker": {"success": ft["best_prior_seeker"]["success_val"],
                              "on_time": ft["best_prior_seeker"]["on_time_val"],
                              "plan": ft["best_prior_seeker"]["plan"]},
    }
    for p in frontier["grid_points"]:
        print(f"    r={p['ramp_rate_nps']:>6g} c={p['start_conservatism']:.1f} | "
              f"success={p['success']:.3f} on_time={p['on_time_rate']:.3f} "
              f"overshoot={p['overshoot_rate']:.3f} timeout={p['timeout_rate']:.3f}")

    print("[4/4] writing artifacts")
    from autodrift.artifacts import utc_timestamp, write_csv_rows

    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, rows_out)

    regime_matrix = [
        {
            "reveal_m": s["reveal_distance_m"],
            "oracle": s["oracle"]["success_val"],
            "seeker": s["best_seeker"]["success_val"],
            "prior_seeker": s["best_prior_seeker"]["success_val"],
            "fixed_speed": s["best_fixed_speed"]["success_val"],
            "fixed_ramp": s["best_fixed_ramp"]["success_val"],
            "voi_belief": s["voi_belief_val"],
            "voi_residual_prior": s["voi_residual_prior_val"],
            "detection_value": s["detection_value_val"],
        }
        for s in tier_summaries
    ]

    payload = {
        "protocol": "feasibility_audit_ramp_policy_voi_regime",
        "generated_by": "scripts/feasibility_audit/ramp_policy_voi_regime.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "paradigm": (
            "Threshold-seeking (identification embedded in the useful braking action): prior "
            "belief -> confidence-scaled brake-force ramp -> shortfall slip-onset edge-holding -> "
            "reflex backoff on overshoot. Replaces the retired probe-pulse + blind-commitment "
            "paradigm; measures the residual value of belief GIVEN this reactive layer."
        ),
        "task_surface": {
            "family": "B2K2_final (selfid_task_final_spec.json env_knobs), reveal distance swept",
            "reveal_tiers_m": list(tiers),
            "mu_domain": MU_DOMAIN,
            "mu_to_distance_knots": {"mu": MU_KNOTS, "d_m": D_KNOTS},
            "oracle_speed_knots": {"mu": MU_KNOTS, "v_mps": V_KNOTS},
            "distance_jitter_m": JITTER_D_M,
            "distance_floor_m": D_FLOOR_M,
            "jitter_note": "jitter keyed by rollout seed only -> identical episode geometry across tiers",
            "max_steps": MAX_STEPS, "deadline_s": MAX_STEPS * DT,
            "rewards": {"pass": PASS_REWARD, "collision": COLLISION_PENALTY},
        },
        "detector": {
            "status": "Measurement-A detector NOT on disk; simple single-frame shortfall stand-in implemented here",
            "signal": "shortfall = 1 - realized_rear_fx/applied_force from obs channels (vx,vy,yaw,ax,steer,thr_state,brk_state)",
            "mu_from_onset": "mu_hat = realized_force/(0.98*Fzr) (tire clamp makes realized=limit at saturation)",
            "gates": "|steer| < 0.06 rad, vx > 2 m/s, applied force > 400 N (brake) / 600 N (drive)",
            "brake_side_censoring_mu": round(MU_CENSOR, 4),
            "self_check": det_check,
        },
        "panel": {
            "mu_points": [round(m, 4) for m in mus],
            "selection_seeds": args.sel_seeds, "validation_seeds": args.val_seeds,
            "seed_formula": "20260618*10 + 17*point + 1000*k (+100000 val, +500000 frontier, +900000 check)",
            "jitter_seed_formula": "U(-0.75,0.75) from default_rng([20260618, 777, rollout_seed]), floor 14.5 m",
        },
        "controller_family": {
            "shared_speed_law": (
                "entry target = clip(min(max(0.5*(vd+vr), vd+0.3), vr) + dv, 3.9, 13) with "
                "vd = remaining-distance/remaining-time deadline floor (mu->d map at mu_eff) and "
                f"vr = {RHO_DODGE}*sqrt(mu_eff)*(reveal/9.5) dodge-feasible cap (calibrated on the "
                "final-spec full-bin oracle entry speeds ~10.1*sqrt(mu) at reveal 9.5)"
            ),
            "oracle_ramp": "mu_eff = true mu; brake at 0.95*limit when slowing; dv fine-tune in " + str(ORACLE_DVS) + " selected per (tier, point)",
            "seeker_grid": {"ramp_rate_nps": SEEKER_RATES, "tau": SEEKER_TAUS,
                            "delta": SEEKER_DELTAS, "strategy": SEEKER_STRATS,
                            "dv_map_offset": SEEKER_DVMAPS,
                            "start": "0.95*limit(mu=0.25) domain floor"},
            "prior_seeker_grid": {"ramp_rate_nps": PRIOR_RATES, "tau": PRIOR_TAUS,
                                  "delta": PRIOR_DELTA, "strategy": PRIOR_STRAT,
                                  "dv_map_offset": PRIOR_DVMAPS,
                                  "start": "0.95*limit(bin_lo), bin = [mu-0.2, mu+0.2] clipped"},
            "fixed_speed_grid_mps": FIXED_SPEED_GRID,
            "fixed_ramp_grid": FIXED_RAMP_GRID,
            "shared_reaction": (
                "mod_b.CommitmentController brake->swerve; reaction hold speed = "
                "clip(min(vr(mu_eff, bx_at_reveal), v_at_reveal), 3.8, 13) frozen at reveal, "
                "re-derived when mu_hat updates; post-reveal full brake capped at believed limit "
                "(0.95 oracle / (1-delta) identified seeker); fixed families are swerve-only "
                "commitments (old-paradigm adversary form)"
            ),
        },
        "regime_matrix_success_validated": regime_matrix,
        "tiers": tier_summaries,
        "frontier": frontier,
        "env_fidelity_notes": [
            "dynamics.py clamps fx_rear at the friction limit with no lockup/instability mode: "
            "over-commanding the brake in a straight line costs only rear lateral capacity "
            "(negligible on the r=900 m arc), so in-env overshoot is nearly free and fast ramps "
            "are not intrinsically punished -- frontier overshoot-rate axis must be read with "
            "this in mind (measurement C, reflex_overshoot_recovery.py, covers injected "
            "instability instead).",
            "brake actuator (6000 N) saturates below the tire limit for mu > ~0.893: brake-side "
            "identification is censored at high mu; seekers recover via passive drive-side "
            "shortfall during re-acceleration.",
        ],
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {"episode_rows_csv": str(rows_csv), "results_json": str(args.results_json)},
    }
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {args.results_json}")
    print(f"episode rows -> {rows_csv} ({len(rows_out)} rows)")
    print("HEADLINE: " + " | ".join(
        f"reveal {m['reveal_m']:g}: VoI(belief)={m['voi_belief']:+.3f} VoI(res|prior)={m['voi_residual_prior']:+.3f}"
        for m in regime_matrix) + f" | elapsed {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
