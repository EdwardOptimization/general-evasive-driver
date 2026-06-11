"""WP0.1 Track F: family-#2 design freeze + clean-sensing acceptance.

Second task family for the C1 generality claim of the two-regime law
(docs/research-plan-phase2-capability-boundary-tracking.md WP0.1; thesis
docs/capability-boundary-tracking-thesis-2026-06.md Section 8).

Pinned geometry direction: large-radius straight (circle R=3000 m
approximation) + laterally offset single obstacle = asymmetric gap choice
(obstacle.lateral_offset_range, env.py:516,551). Geometric constraint found
during design (reported, not hidden): from a free centerline approach with a
single offset disc the WIDER gap is always the NEARER one, so the
"near-narrow vs far-wide" trade-off cannot exist without pinning the approach
line; the honest single-obstacle realization of a mu-dependent gap choice is
the mu-SIGNED open side (per-cell degenerate configs couple the offset sign
to mu), which two of the three frozen candidates implement.

Candidates (<= 3, ALL reported; knobs frozen in
experiments/feasibility_audit/family2_prereg.json BEFORE any run):
  F2C1_offset_jitter_react  random gap side per episode (coin by rollout
                            seed); side reactive at reveal; mu-commitment =
                            entry speed (B2K2 engine on the new geometry).
  F2C2_mu_signed_gap        open side flips with mu at 0.70: low mu ->
                            obstacle offset left (open RIGHT), high mu ->
                            offset right (open LEFT). Belief predicts side
                            (pre-reveal lateral bias) AND entry speed.
  F2C3_mu_signed_tight      tightened F2C2 (narrower corridor, wider
                            obstacle, reveal 8.5 m, deadline 4.8 s).

Stages:
  construct   28-plan mu-agnostic commitment family on streams A (selection)
              / B (validation); construction criterion (frozen): commitment
              VoI = per-mu-oracle - best-fixed >= 0.25 on stream B.
  accept      winner only: threshold-seeker (ShortfallDetector reused from
              ramp_policy_voi_regime.py; tau/rate/backoff/dv re-selected on
              stream C) vs per-mu parametric oracle (dv per point on C);
              PASS = oracle - seeker <= 0.05 on stream D (12 x 10 = 120
              validation episodes), with an oracle-strength guard against
              the plan-family oracle re-measured on D.

Machinery reuse: voi_commitment_task_design.py (VoI-first construction
flow, steering/speed-action laws), ramp_policy_voi_regime.py
(ShortfallDetector + ramp phase machine + oracle/seeker calibration
pattern), voi_current_task_family.py (fixed-plan baseline semantics).

Hard constraints: pure CPU numpy, zero training, deterministic seeds,
selection/validation seed streams disjoint, new files only, no git ops.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/family2_design.py
    PYTHONPATH=src python scripts/feasibility_audit/family2_design.py --quick
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RAMP_SCRIPT = REPO / "scripts/feasibility_audit/ramp_policy_voi_regime.py"
PREREG_JSON = REPO / "experiments/feasibility_audit/family2_prereg.json"
RESULTS_JSON = REPO / "experiments/feasibility_audit/family2_spec.json"
RUN_DIR = REPO / "runs/feasibility_audit/family2_design"

SEED_BASE = 20260624  # fresh stream (prior: 20260611..20260622)
STREAM_OFFSETS = {"A": 0, "B": 100_000, "C": 300_000, "D": 600_000}

DT = 0.02
V0 = 8.0
EGO_HALF = 0.90
SAFETY_MARGIN = 0.30
SWERVE_PAD = 0.35
WHEELBASE = 2.80
MAX_STEER_RAD = 0.62
TRACK_RADIUS = 3000.0
MU_DOMAIN = (0.25, 1.15)
JITTER_D_M = 0.75
D_FLOOR_M = 14.5
PASS_REWARD, COLLISION_PENALTY = 40.0, 60.0
V_CAP = 13.0
A_EFF_G = 0.565  # effective lateral fraction calibrated on B2K2 oracle speeds (10.1*sqrt(mu) at reveal 9.5, offset 2.45)
GRAV = 9.81

# vehicle constants shared with ramp_policy_voi_regime (same nominal vehicle)
MASS, LF, LR = 1450.0, 1.35, 1.45
FZR = MASS * GRAV * LF / (LF + LR)
MAX_BRAKE, MAX_DRIVE = 6000.0, 8200.0
TIRE_CAP = 0.98
MU_CENSOR = MAX_BRAKE / (TIRE_CAP * FZR)

OBS_DIM = 72
IDX_VX, IDX_BRK_STATE = 0, 8
IDX_OBST_PRESENT, IDX_OBST_BX, IDX_OBST_BY = 44, 45, 46
ROAD_LEFT_START, ROAD_RIGHT_START = 12, 28
ROAD_SPACING = 5.0
SETTLE_STEPS = 10

CONSTRUCTION_VOI_BAR = 0.25
ACCEPTANCE_GAP_BAR = 0.05
ORACLE_STRENGTH_SLACK = 0.02

PLAN_SPEEDS = (4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5)
PLAN_SIDES = (("react", 0.0), ("bias_left", 1.0), ("bias_right", -1.0))
SWERVE_ONLY_SPEEDS = (6.5, 8.5, 10.5, 12.0)
SEEKER_RATES = (2000.0, 6000.0, 20000.0)
SEEKER_TAUS = (0.08, 0.18)
SEEKER_BACKOFFS = (0.06, 0.15)
SEEKER_DVS = (0.0, 0.75)
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)

CLAIM_BOUNDARY = (
    "Feasibility-audit task-DESIGN measurement only: scripted mu-agnostic commitment plans, a "
    "per-mu oracle and a belief-free threshold-seeker are rolled out on candidate family-2 "
    "geometries to measure construction VoI and the clean-sensing seeker-vs-oracle gap. No "
    "driver promotion, training, repair-success, gate-validity, paper, or self-ID capability "
    "claim is made."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def interp_lin(x: float, xs: tuple[float, ...], ys: tuple[float, ...]) -> float:
    """Piecewise-linear with linear extrapolation outside the knots."""
    if x <= xs[0]:
        slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return ys[0] + slope * (x - xs[0])
    if x >= xs[-1]:
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return ys[-1] + slope * (x - xs[-1])
    return float(np.interp(x, xs, ys))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center - half, center + half)


# ------------------------------------------------------------------ candidates


@dataclass(frozen=True)
class F2Candidate:
    candidate_id: str
    corridor_half: float  # env track_width (hard offtrack at |lat| > this)
    ob_half_width: float
    delta_mag: float
    sign_rule: str  # "coin" | "mu_threshold"
    mu_side_threshold: float
    reveal: float
    max_steps: int
    d_knots_mu: tuple[float, ...]
    d_knots_d: tuple[float, ...]
    intent: str = ""

    @property
    def deadline_s(self) -> float:
        return self.max_steps * DT

    @property
    def clear(self) -> float:
        return self.ob_half_width + EGO_HALF + SAFETY_MARGIN + SWERVE_PAD

    def d_of_mu(self, mu: float) -> float:
        return interp_lin(mu, self.d_knots_mu, self.d_knots_d)

    def jittered_distance(self, mu: float, seed: int) -> float:
        eps = float(np.random.default_rng([SEED_BASE, 777, int(seed)]).uniform(-JITTER_D_M, JITTER_D_M))
        return max(self.d_of_mu(mu) + eps, D_FLOOR_M)

    def delta_signed(self, mu: float, seed: int) -> float:
        if self.sign_rule == "coin":
            sign = 1.0 if float(np.random.default_rng([SEED_BASE, 555, int(seed)]).uniform()) < 0.5 else -1.0
        else:
            sign = 1.0 if mu < self.mu_side_threshold else -1.0
        return sign * self.delta_mag

    def predicted_open_side(self, mu_eff: float) -> float:
        """+1 = open gap left (inward), -1 = open right; 0 = unpredictable."""
        if self.sign_rule == "coin":
            return 0.0
        return -1.0 if mu_eff < self.mu_side_threshold else 1.0

    def open_traverse_from_center(self) -> float:
        return max(self.clear - self.delta_mag, 0.5)


def frozen_candidates() -> list[F2Candidate]:
    return [
        F2Candidate(
            candidate_id="F2C1_offset_jitter_react",
            corridor_half=3.2, ob_half_width=1.0, delta_mag=0.8,
            sign_rule="coin", mu_side_threshold=float("nan"),
            reveal=9.5, max_steps=260,
            d_knots_mu=(0.30, 0.55, 0.85, 1.15), d_knots_d=(24.0, 40.0, 50.0, 58.0),
            intent="random gap side per episode; side reactive; mu-commitment = entry speed",
        ),
        F2Candidate(
            candidate_id="F2C2_mu_signed_gap",
            corridor_half=3.0, ob_half_width=1.0, delta_mag=0.85,
            sign_rule="mu_threshold", mu_side_threshold=0.70,
            reveal=9.5, max_steps=260,
            d_knots_mu=(0.30, 0.55, 0.85, 1.15), d_knots_d=(24.0, 40.0, 50.0, 58.0),
            intent="open side flips with mu at 0.70; belief predicts gap side AND entry speed",
        ),
        F2Candidate(
            candidate_id="F2C3_mu_signed_tight",
            corridor_half=2.9, ob_half_width=1.1, delta_mag=0.95,
            sign_rule="mu_threshold", mu_side_threshold=0.70,
            reveal=8.5, max_steps=240,
            d_knots_mu=(0.30, 0.55, 0.85, 1.15), d_knots_d=(22.0, 38.0, 48.0, 56.0),
            intent="tightened F2C2: closed side fully blocked, reveal 8.5, deadline 4.8 s",
        ),
    ]


def centerline_compensation(d: float) -> float:
    return float(TRACK_RADIUS - math.sqrt(max(TRACK_RADIUS**2 - d**2, 1.0)))


def env_config(cand: F2Candidate, mu: float, seed: int) -> dict[str, Any]:
    d = cand.jittered_distance(mu, seed)
    delta = cand.delta_signed(mu, seed)
    offset = centerline_compensation(d) + delta
    return {
        "dt": DT,
        "max_steps": cand.max_steps,
        "track_kind": "circle",
        "track_radius": TRACK_RADIUS,
        "track_width": cand.corridor_half,
        "speed_range": [V0, V0],
        "beta_target_range": [0.40, 0.40],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "wheel_observation_mode": "none",
        "include_privileged_params": False,
        "randomization": {
            "mu_range": [mu, mu],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "obstacle": {
            "enabled": True,
            "distance_range": [d, d],
            "half_width_range": [cand.ob_half_width, cand.ob_half_width],
            "lateral_offset_range": [offset, offset],
            "finish_on_pass": True,
            "finish_pass_distance": 2.0,
            "pass_reward": PASS_REWARD,
            "collision_penalty": COLLISION_PENALTY,
            "perception_reveal_step": 0,
            "perception_reveal_distance": cand.reveal,
            "require_aeb_infeasible": False,
        },
    }


# ------------------------------------------------------------------ controllers


@dataclass
class F2Plan:
    name: str
    v_entry: float
    brake_to: float | None
    bias: float = 0.0  # pre-reveal lateral line relative centerline (+left/inward)
    steer_cap: float = 0.85


class Family2Controller:
    """Observation-only commitment-plan executor for family 2 (side-parametric
    swerve; steering/speed-action laws adapted from
    voi_commitment_task_design.CommitmentController)."""

    def __init__(self, plan: F2Plan, cand: F2Candidate):
        self.plan = plan
        self.cand = cand
        self.reset()

    def reset(self) -> None:
        self.t = 0
        self.dist = 0.0
        self.reveal_step: int | None = None
        self.speed_at_reveal = float("nan")
        self.dist_at_reveal = float("nan")
        self.passed = False
        self.side: float | None = None  # chosen at reveal: +1 left, -1 right
        self.delta_est = float("nan")
        self.target_rel: float | None = None

    # -- observation helpers --------------------------------------------------
    def _mid(self, obs: np.ndarray, j: int) -> tuple[float, float]:
        lx = obs[ROAD_LEFT_START + 2 * j] * 80.0
        ly = obs[ROAD_LEFT_START + 2 * j + 1] * 20.0
        rx = obs[ROAD_RIGHT_START + 2 * j] * 80.0
        ry = obs[ROAD_RIGHT_START + 2 * j + 1] * 20.0
        return 0.5 * (lx + rx), 0.5 * (ly + ry)

    def _steer_to(self, obs: np.ndarray, j: int, offset_m: float, gain: float, cap: float) -> float:
        xt, yt = self._mid(obs, j)
        yt += offset_m
        alpha = math.atan2(yt, max(xt, 1.0))
        dist = max(math.hypot(xt, yt), 2.0)
        steer_angle = math.atan2(2.0 * WHEELBASE * math.sin(alpha), dist)
        return float(np.clip(gain * steer_angle / MAX_STEER_RAD, -cap, cap))

    @staticmethod
    def _speed_actions(vx: float, v_target: float) -> tuple[float, float]:
        err = v_target - vx
        if err >= -0.15:
            return 2.0 * float(np.clip(0.55 * err, 0.0, 1.0)) - 1.0, -1.0
        return -1.0, 2.0 * float(np.clip(-0.5 * err, 0.0, 1.0)) - 1.0

    def _y_rel(self, obs: np.ndarray) -> float:
        """Ego lateral offset relative centerline (+left), first-order estimate."""
        _, y0 = self._mid(obs, 0)
        return -y0

    def _classify_obstacle(self, obs: np.ndarray, bx: float, by: float) -> None:
        j = int(np.clip(round(bx / ROAD_SPACING) - 1, 0, 7))
        _, ym = self._mid(obs, j)
        self.delta_est = by - ym  # obstacle offset relative centerline (+left)
        open_side = -1.0 if self.delta_est > 0.0 else 1.0
        self.side = open_side
        target = self.delta_est + open_side * self.cand.clear
        limit = self.cand.corridor_half - 0.5
        self.target_rel = float(np.clip(target, -limit, limit))

    def _swerve_steer(self, obs: np.ndarray, bx: float, by: float, vx: float) -> float:
        if bx > max(4.0, 0.45 * vx):
            y_aim = by + (self.target_rel - self.delta_est)
            x_aim = max(bx, 3.0)
            alpha = math.atan2(y_aim, x_aim)
            dist = max(math.hypot(x_aim, y_aim), 2.0)
            steer_angle = math.atan2(2.0 * WHEELBASE * math.sin(alpha), dist)
            return float(np.clip(3.0 * steer_angle / MAX_STEER_RAD, -self.plan.steer_cap, self.plan.steer_cap))
        return self._steer_to(obs, 1, self.target_rel, 1.6, min(self.plan.steer_cap, 0.6))

    # -- policy ----------------------------------------------------------------
    def act(self, obs: np.ndarray) -> np.ndarray:
        plan = self.plan
        vx = float(obs[IDX_VX]) * 20.0
        self.dist += max(vx, 0.0) * DT
        revealed = bool(obs[IDX_OBST_PRESENT] > 0.5)
        bx = float(obs[IDX_OBST_BX]) * 80.0
        by = float(obs[IDX_OBST_BY]) * 20.0
        if revealed and self.reveal_step is None:
            self.reveal_step = self.t
            self.speed_at_reveal = vx
            self.dist_at_reveal = self.dist
            self._classify_obstacle(obs, bx, by)

        if self.reveal_step is None:
            steer = self._steer_to(obs, 2, plan.bias, 1.6, 0.45)
            throttle, brake = self._speed_actions(vx, plan.v_entry)
            action = [steer, throttle, brake]
        else:
            if revealed and bx < -0.5:
                self.passed = True
            if self.passed:
                steer = self._steer_to(obs, 2, 0.6 * (self.target_rel or 0.0), 1.0, 0.35)
                throttle, brake = self._speed_actions(vx, plan.v_entry)
                action = [steer, throttle, brake]
            else:
                brake_to = plan.brake_to
                if brake_to is not None and vx > brake_to + 0.2 and bx > 6.0:
                    steer = self._steer_to(obs, 2, self._y_rel(obs), 1.2, 0.2)
                    action = [steer, -1.0, 1.0]
                else:
                    steer = self._swerve_steer(obs, bx, by, vx)
                    v_hold = brake_to if brake_to is not None else plan.v_entry
                    throttle, brake = self._speed_actions(vx, max(v_hold, 3.5))
                    action = [steer, throttle, brake]
        self.t += 1
        return np.asarray(action, dtype=np.float64)

    def telemetry_row(self) -> dict[str, Any]:
        return {
            "side_chosen": 0.0 if self.side is None else float(self.side),
            "delta_est": round(float(self.delta_est), 3) if np.isfinite(self.delta_est) else None,
        }


class Family2Ramp:
    """Per-mu oracle / threshold-seeker on family 2.

    Pre-reveal longitudinal phase machine + detector ingestion adapted from
    ramp_policy_voi_regime.RampPolicyController; ShortfallDetector imported
    from that module (the load-bearing reuse). The seeker's belief mu_hat
    feeds the SAME decision laws as the oracle's true mu: predicted open
    side -> pre-reveal lateral bias; entry-speed law; reaction hold speed;
    brake cap at the believed force limit.
    """

    def __init__(self, mod_r, cand: F2Candidate, name: str, mode: str, *,
                 ramp_rate: float = 6000.0, tau: float = 0.08, backoff: float = 0.06,
                 mu_true: float | None = None, dv: float = 0.0, bias_mag: float = 1.0,
                 seek_style: str = "brake"):
        self.mod_r, self.cand = mod_r, cand
        self.name, self.mode = name, mode
        self.ramp_rate, self.backoff = ramp_rate, backoff
        self.mu_true, self.dv, self.bias_mag = mu_true, dv, bias_mag
        self.seek_style = seek_style  # "brake" (B2K2-style) | "drive" (repair round 1: identify while accelerating)
        self.inner = Family2Controller(F2Plan(name=name, v_entry=V0, brake_to=V0 - 1.0), cand)
        self.detector = mod_r.ShortfallDetector(tau)
        self.reset()

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
        self.censored = False
        self.id_step = -1
        self._cap_count = 0
        self.f_cmd = 0.95 * TIRE_CAP * FZR * MU_DOMAIN[0]
        self._brake_to_frozen: float | None = None
        self._mu_at_freeze: float | None = None

    # -- belief-conditioned laws ------------------------------------------------
    def _mu_eff(self) -> float:
        if self.mode == "oracle":
            return self.mu_true
        return self.mu_hat if self.mu_hat is not None else MU_DOMAIN[0]

    def _limit_est(self) -> float | None:
        if self.mode == "oracle":
            return TIRE_CAP * FZR * self.mu_true
        if self.mu_hat is not None:
            return TIRE_CAP * FZR * self.mu_hat
        return None

    def _v_dodge(self, mu: float, window_m: float, traverse_m: float) -> float:
        a = A_EFF_G * max(mu, 0.05) * GRAV
        return float(min(max(window_m, 2.0) * math.sqrt(a / (2.0 * max(traverse_m, 0.4))), V_CAP))

    def _planned_traverse(self) -> float:
        base = self.cand.open_traverse_from_center()
        bias = abs(self.inner.plan.bias)
        if self.cand.predicted_open_side(self._mu_eff()) != 0.0 and bias > 0.0:
            return max(base - bias, 0.5)
        return base

    def _v_target(self) -> float:
        mu_eff = self._mu_eff()
        d_rem = self.cand.d_of_mu(mu_eff) - self.inner.dist + 2.5
        t_rem = max(self.cand.deadline_s - self.k * DT, 0.5)
        vd = max(d_rem, 0.0) / t_rem
        vr = self._v_dodge(mu_eff, self.cand.reveal, self._planned_traverse())
        base = min(max(0.5 * (vd + vr), vd + 0.3), vr)
        return float(np.clip(base + self.dv, 3.9, V_CAP))

    def _reaction_brake_to(self, obs: np.ndarray, vx: float) -> float:
        mu_eff = self._mu_eff()
        if self._brake_to_frozen is None or self._mu_at_freeze != mu_eff:
            if self._brake_to_frozen is None:
                bx = float(obs[IDX_OBST_BX]) * 80.0
                self._bx_rev = max(bx, 2.0)
                v_rev = self.inner.speed_at_reveal
                self._v_rev = vx if not np.isfinite(v_rev) else max(v_rev, vx)
                tgt = self.inner.target_rel if self.inner.target_rel is not None else 0.0
                self._trav_rev = max(abs(tgt - self.inner._y_rel(obs)), 0.5)
            self._brake_to_frozen = float(np.clip(
                min(self._v_dodge(mu_eff, self._bx_rev, self._trav_rev), self._v_rev), 3.8, V_CAP))
            self._mu_at_freeze = mu_eff
        return self._brake_to_frozen

    def _ingest_detection(self) -> None:
        det = self.detector
        if det.onset and det.mu_sample is not None and self.mode == "seeker":
            if self.mu_hat is None or self.censored:
                self.id_step = self.k if self.mu_hat is None else self.id_step
                self.censored = False
            self.mu_hat = float(np.clip(np.median(det.samples[-5:]), 0.10, 1.40))

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
                if self.seek_style == "drive":
                    self.phase = "dramp"
                    self.f_cmd = 1200.0
                else:
                    self.phase = "ramp"
            return self.inner._speed_actions(vx, V0)

        if self.phase == "dramp":
            # repair round 1: throttle-force ramp; drive-side shortfall onset
            # identifies mu while the (deadline-useful) acceleration is running.
            self.f_cmd += self.ramp_rate * DT
            if det.onset and det.onset_side == "drive":
                self.phase = "track"
            elif self.f_cmd >= MAX_DRIVE:
                self._cap_count += 1
                if self._cap_count >= 8:  # unreachable for mu <= 1.15 (limit < MAX_DRIVE); guard anyway
                    self.censored = True
                    self.mu_hat = MAX_DRIVE / (TIRE_CAP * FZR)
                    self.id_step = self.k
                    self.phase = "track"
            elif vx >= V_CAP - 0.5:
                self.phase = "track"
            if self.phase == "track" and self.mu_hat is not None and self.id_step < 0:
                self.id_step = self.k
            return 2.0 * min(self.f_cmd / MAX_DRIVE, 1.0) - 1.0, -1.0

        if self.phase == "ramp":
            self.f_cmd += self.ramp_rate * DT
            if det.onset and det.onset_side == "brake":
                self.phase = "limit_hold"
            elif self.f_cmd >= MAX_BRAKE and brk_state >= 0.965:
                self._cap_count += 1
                if self._cap_count >= 8:
                    self.censored = True
                    self.mu_hat = MU_CENSOR
                    self.id_step = self.k
                    self.phase = "track"
            elif vx < 4.0:
                self.censored = True
                self.mu_hat = max(brk_state * MAX_BRAKE / (TIRE_CAP * FZR), MU_DOMAIN[0])
                self.id_step = self.k
                self.phase = "track"
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        if self.phase == "limit_hold":
            v_t = self._v_target()
            if vx <= v_t + 0.25:
                self.phase = "track"
                return self.inner._speed_actions(vx, v_t)
            self.f_cmd = (1.0 - self.backoff) * (self._limit_est() or 0.3 * MAX_BRAKE)
            return -1.0, 2.0 * min(self.f_cmd / MAX_BRAKE, 1.0) - 1.0

        return self.inner._speed_actions(vx, self._v_target())

    def act(self, obs: np.ndarray) -> np.ndarray:
        obs = np.asarray(obs, dtype=np.float64)
        self.detector.update(obs)
        self._ingest_detection()
        vx = float(obs[IDX_VX]) * 20.0
        v_t = self._v_target()
        self.inner.plan.v_entry = float(v_t)
        # pre-reveal lateral bias toward the predicted open side (oracle: from
        # the start; seeker: once mu_hat exists)
        side_pred = self.cand.predicted_open_side(self._mu_eff())
        if self.mode == "oracle" or self.mu_hat is not None:
            self.inner.plan.bias = float(side_pred * self.bias_mag)
        pre_reveal = self.inner.reveal_step is None and float(obs[IDX_OBST_PRESENT]) <= 0.5
        if pre_reveal:
            self.inner.plan.brake_to = float(max(v_t - 1.0, 3.5))
        else:
            self.inner.plan.brake_to = self._reaction_brake_to(obs, vx)
        action = self.inner.act(obs)
        if pre_reveal:
            thr, brk = self._longitudinal(obs, vx)
            action[1], action[2] = thr, brk
        else:
            if action[1] <= -0.99 and action[2] >= 0.99:
                limit = self._limit_est()
                if limit is not None:
                    frac = 0.95 if self.mode == "oracle" else (1.0 - self.backoff)
                    action[2] = 2.0 * min(frac * limit / MAX_BRAKE, 1.0) - 1.0
        self.k += 1
        return action

    def telemetry_row(self) -> dict[str, Any]:
        row = self.inner.telemetry_row()
        side_pred = self.cand.predicted_open_side(self._mu_eff())
        row.update({
            "mu_hat": float("nan") if self.mu_hat is None else round(float(self.mu_hat), 4),
            "censored": bool(self.censored),
            "id_step": int(self.id_step),
            "side_pred": float(side_pred),
            "overshoot_events": int(self.detector.overshoot_events),
            "max_shortfall": round(float(self.detector.max_shortfall), 4),
            "v_target_final": round(float(self._v_target()), 3),
            "phase_final": self.phase,
        })
        return row


# --------------------------------------------------------------------- rollout


class EnvPool:
    def __init__(self, cand: F2Candidate):
        from autodrift.config import build_env_config
        from autodrift.env import AutoDriftEnv

        self._build, self._env_cls = build_env_config, AutoDriftEnv
        self.cand = cand
        self._cache: dict[tuple[float, int], Any] = {}
        self.episodes = 0

    def env_for(self, mu: float, seed: int):
        key = (round(mu, 6), int(seed))
        if key not in self._cache:
            env = self._env_cls(self._build(env_config(self.cand, mu, seed)))
            assert env.base_obs_dim == OBS_DIM, f"obs layout changed: {env.base_obs_dim}"
            self._cache[key] = env
        return self._cache[key]

    def rollout(self, controller, mu: float, seed: int, **tags) -> dict[str, Any]:
        from autodrift.evaluate import outcome_bucket_from_info

        env = self.env_for(mu, seed)
        obs, info = env.reset(seed=seed)
        controller.reset()
        d0 = float(info.get("obstacle_distance", float("nan")))
        episode_return = 0.0
        terminated = truncated = False
        while not (terminated or truncated):
            action = controller.act(np.asarray(obs, dtype=np.float64))
            obs, reward, terminated, truncated, info = env.step(action)
            episode_return += float(reward)
        bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
        self.episodes += 1
        row = {
            "seed": seed, "mu": round(mu, 4), "obstacle_distance_initial": round(d0, 2),
            "outcome_bucket": bucket,
            "success": bucket == "success_obstacle_pass",
            "collided": bucket == "collision_failure",
            "timeout": bucket == "max_steps_noncompletion",
            "offtrack": bucket.startswith("off_track"),
            "steps": int(info.get("step", 0)), "return": round(episode_return, 2),
            "min_clearance_margin": round(float(info.get("min_clearance_margin", float("nan"))), 3),
            "reveal_step": -1 if controller.reveal_step is None else int(controller.reveal_step),
            "speed_at_reveal": round(float(controller.speed_at_reveal), 3),
        }
        telemetry = getattr(controller, "telemetry_row", None)
        row.update(telemetry() if callable(telemetry) else {})
        row.update(tags)
        return row

    def close(self) -> None:
        for env in self._cache.values():
            env.close()
        self._cache.clear()


def seed_for(point: int, k: int, stream: str) -> int:
    return SEED_BASE * 10 + 17 * point + 1000 * k + STREAM_OFFSETS[stream]


# ---------------------------------------------------------------- construction


def plan_family(cand: F2Candidate) -> list[F2Plan]:
    plans: list[F2Plan] = []
    for v in PLAN_SPEEDS:
        for side_name, bias in PLAN_SIDES:
            plans.append(F2Plan(name=f"commit_v{v:g}_{side_name}", v_entry=v,
                                brake_to=max(v - 1.0, 4.0), bias=bias))
    for v in SWERVE_ONLY_SPEEDS:
        plans.append(F2Plan(name=f"swerve_only_v{v:g}_react", v_entry=v, brake_to=None))
    return plans


def construct_candidate(cand: F2Candidate, mus: list[float], sel_ks: list[int], val_ks: list[int],
                        rows_out: list[dict[str, Any]]) -> dict[str, Any]:
    pool = EnvPool(cand)
    plans = plan_family(cand)
    n_pts, n_plans = len(mus), len(plans)
    success = {"A": np.zeros((n_plans, n_pts)), "B": np.zeros((n_plans, n_pts))}
    returns = {"A": np.zeros((n_plans, n_pts)), "B": np.zeros((n_plans, n_pts))}
    coll = {"B": np.zeros((n_plans, n_pts))}
    tout = {"B": np.zeros((n_plans, n_pts))}
    try:
        for pi, plan in enumerate(plans):
            controller = Family2Controller(plan, cand)
            for stream, ks in (("A", sel_ks), ("B", val_ks)):
                for point, mu in enumerate(mus):
                    rows = [pool.rollout(controller, mu, seed_for(point, k, stream),
                                         candidate=cand.candidate_id, plan=plan.name,
                                         plan_group="fixed", mu_point=round(mu, 4), stream=stream)
                            for k in ks]
                    rows_out.extend(rows)
                    success[stream][pi, point] = float(np.mean([r["success"] for r in rows]))
                    returns[stream][pi, point] = float(np.mean([r["return"] for r in rows]))
                    if stream == "B":
                        coll["B"][pi, point] = float(np.mean([r["collided"] for r in rows]))
                        tout["B"][pi, point] = float(np.mean([r["timeout"] for r in rows]))
    finally:
        pool.close()

    sel_s, val_s = success["A"], success["B"]
    oracle_idx = [int(max(range(n_plans), key=lambda i: (sel_s[i, p], returns["A"][i, p]))) for p in range(n_pts)]
    fixed_idx = int(max(range(n_plans), key=lambda i: (sel_s[i].mean(), returns["A"][i].mean())))
    oracle_val = float(np.mean([val_s[oracle_idx[p], p] for p in range(n_pts)]))
    fixed_val = float(val_s[fixed_idx].mean())
    voi_val = oracle_val - fixed_val
    voi_sel = float(np.mean([sel_s[oracle_idx[p], p] for p in range(n_pts)]) - sel_s[fixed_idx].mean())
    n_val_eps = len(val_ks)
    diagnosis = []
    if voi_val < CONSTRUCTION_VOI_BAR:
        if oracle_val < 0.75:
            diagnosis.append(f"oracle ceiling low ({oracle_val:.3f} < 0.75): infeasible cells / controller-family ceiling binds")
        if fixed_val > 0.70:
            diagnosis.append(f"best fixed plan high ({fixed_val:.3f} > 0.70): reactive dominance — geometry observable+reachable at reveal")
        if not diagnosis:
            diagnosis.append("VoI below bar without a dominant single cause (mid oracle, mid fixed)")
    return {
        "candidate_id": cand.candidate_id,
        "intent": cand.intent,
        "episodes": (len(sel_ks) + len(val_ks)) * n_pts * n_plans,
        "n_plans": n_plans,
        "mu_points": [round(m, 4) for m in mus],
        "oracle_plan_per_point": [plans[i].name for i in oracle_idx],
        "best_fixed_plan": plans[fixed_idx].name,
        "oracle_success_val": round(oracle_val, 4),
        "best_fixed_success_val": round(fixed_val, 4),
        "voi_commitment_val": round(voi_val, 4),
        "voi_commitment_sel": round(voi_sel, 4),
        "voi_bar": CONSTRUCTION_VOI_BAR,
        "construction_pass": bool(voi_val >= CONSTRUCTION_VOI_BAR),
        "oracle_per_point_success_val": [round(float(val_s[oracle_idx[p], p]), 3) for p in range(n_pts)],
        "best_fixed_per_point_success_val": [round(float(val_s[fixed_idx, p]), 3) for p in range(n_pts)],
        "best_fixed_collision_val": round(float(coll["B"][fixed_idx].mean()), 4),
        "best_fixed_timeout_val": round(float(tout["B"][fixed_idx].mean()), 4),
        "val_episodes_per_readout_arm": n_pts * n_val_eps,
        "binding_constraints_if_fail": diagnosis,
        "top5_fixed_plans_val": sorted(
            [{"plan": plans[i].name, "success_val": round(float(val_s[i].mean()), 4)} for i in range(n_plans)],
            key=lambda r: -r["success_val"])[:5],
    }


# ------------------------------------------------------------------ acceptance


def accept_candidate(mod_r, cand: F2Candidate, mus: list[float], sel_ks: list[int], val_ks: list[int],
                     construction: dict[str, Any], rows_out: list[dict[str, Any]],
                     seeker_styles: tuple[str, ...] = ("brake",),
                     seeker_rates: tuple[float, ...] = SEEKER_RATES) -> dict[str, Any]:
    pool = EnvPool(cand)
    n_pts = len(mus)
    try:
        # [1] seeker grid on stream C
        seeker_grid = [(style, r, tau, b, dv) for style in seeker_styles for r in seeker_rates
                       for tau in SEEKER_TAUS for b in SEEKER_BACKOFFS for dv in SEEKER_DVS]
        seeker_sel: dict[tuple, tuple[float, float]] = {}
        for params in seeker_grid:
            style, r, tau, b, dv = params
            name = f"seeker_{style}_r{r:g}_t{tau:g}_b{b:g}_v{dv:+g}"
            controller = Family2Ramp(mod_r, cand, name, "seeker", ramp_rate=r, tau=tau, backoff=b,
                                     dv=dv, seek_style=style)
            rows = [pool.rollout(controller, mu, seed_for(p, k, "C"), candidate=cand.candidate_id,
                                 plan=name, plan_group="seeker", mu_point=round(mu, 4), stream="C")
                    for p, mu in enumerate(mus) for k in sel_ks]
            rows_out.extend(rows)
            seeker_sel[params] = (float(np.mean([x["success"] for x in rows])),
                                  float(np.mean([x["return"] for x in rows])))
        best_params = max(seeker_grid, key=lambda q: seeker_sel[q])
        style, r, tau, b, dv = best_params
        best_seeker_name = f"seeker_{style}_r{r:g}_t{tau:g}_b{b:g}_v{dv:+g}"

        # [2] oracle dv per point on stream C
        oracle_dv: list[float] = []
        for p, mu in enumerate(mus):
            cands = []
            for odv in ORACLE_DVS:
                controller = Family2Ramp(mod_r, cand, f"oracle_dv{odv:+g}", "oracle", mu_true=mu, dv=odv)
                rows = [pool.rollout(controller, mu, seed_for(p, k, "C"), candidate=cand.candidate_id,
                                     plan=f"oracle_dv{odv:+g}", plan_group="oracle", mu_point=round(mu, 4),
                                     stream="C") for k in sel_ks]
                rows_out.extend(rows)
                cands.append((float(np.mean([x["success"] for x in rows])),
                              float(np.mean([x["return"] for x in rows])), odv))
            oracle_dv.append(max(cands)[2])

        # [3] validation on stream D (disjoint from everything above)
        def run_val(builder, name, group) -> list[dict[str, Any]]:
            rows = []
            for p, mu in enumerate(mus):
                controller = builder(p, mu)
                for k in val_ks:
                    row = pool.rollout(controller, mu, seed_for(p, k, "D"), candidate=cand.candidate_id,
                                       plan=name, plan_group=group, mu_point=round(mu, 4), stream="D")
                    rows.append(row)
                    rows_out.append(row)
            return rows

        seeker_rows = run_val(lambda p, mu: Family2Ramp(mod_r, cand, best_seeker_name, "seeker",
                                                        ramp_rate=r, tau=tau, backoff=b, dv=dv,
                                                        seek_style=style),
                              best_seeker_name, "seeker_val")
        oracle_rows = run_val(lambda p, mu: Family2Ramp(mod_r, cand, f"oracle_dv{oracle_dv[p]:+g}", "oracle",
                                                        mu_true=mu, dv=oracle_dv[p]),
                              "oracle_per_point", "oracle_val")
        # oracle-strength guard: plan-family per-point oracle + best fixed, re-measured on D
        plans = plan_family(cand)
        plan_by_name = {pl.name: pl for pl in plans}
        plan_oracle_rows = run_val(
            lambda p, mu: Family2Controller(plan_by_name[construction["oracle_plan_per_point"][p]], cand),
            "plan_oracle_per_point", "plan_oracle_val")
        best_fixed_rows = run_val(lambda p, mu: Family2Controller(plan_by_name[construction["best_fixed_plan"]], cand),
                                  construction["best_fixed_plan"], "fixed_val")

        def rate(rows, key="success") -> float:
            return float(np.mean([1.0 if x[key] else 0.0 for x in rows]))

        n_val = len(seeker_rows)
        oracle_succ, seeker_succ = rate(oracle_rows), rate(seeker_rows)
        plan_oracle_succ, fixed_succ = rate(plan_oracle_rows), rate(best_fixed_rows)
        gap = oracle_succ - seeker_succ
        strength_ok = oracle_succ >= plan_oracle_succ - ORACLE_STRENGTH_SLACK
        gap_pass = gap <= ACCEPTANCE_GAP_BAR
        mu_errs = [abs(x["mu_hat"] - x["mu"]) for x in seeker_rows
                   if x.get("mu_hat") is not None and np.isfinite(x.get("mu_hat", float("nan"))) and not x.get("censored")]
        side_ok = [1.0 if (x.get("side_pred", 0.0) == 0.0 or x.get("side_pred") == x.get("side_chosen")) else 0.0
                   for x in seeker_rows]
        return {
            "candidate_id": cand.candidate_id,
            "validation_episodes_per_arm": n_val,
            "seeker": {
                "plan": best_seeker_name,
                "params": {"seek_style": style, "ramp_rate_nps": r, "tau": tau, "backoff": b, "dv": dv},
                "styles_in_grid": list(seeker_styles),
                "tau_recalibration_note": "tau/rate/backoff/dv selected on stream C for THIS family (not inherited from B2K2)",
                "success_val": round(seeker_succ, 4),
                "wilson95": [round(x, 4) for x in wilson_ci(int(round(seeker_succ * n_val)), n_val)],
                "collision_val": round(rate(seeker_rows, "collided"), 4),
                "timeout_val": round(rate(seeker_rows, "timeout"), 4),
                "per_point_success_val": [round(float(np.mean([1.0 if x["success"] else 0.0 for x in seeker_rows
                                                               if x["mu_point"] == round(mu, 4)])), 3) for mu in mus],
                "mu_abs_err_mean_uncensored": round(float(np.mean(mu_errs)), 4) if mu_errs else None,
                "censored_fraction": round(float(np.mean([1.0 if x.get("censored") else 0.0 for x in seeker_rows])), 4),
                "id_step_mean": round(float(np.mean([x.get("id_step", -1) for x in seeker_rows])), 1),
                "side_pred_match_fraction": round(float(np.mean(side_ok)), 4),
            },
            "oracle": {
                "dv_per_point": oracle_dv,
                "success_val": round(oracle_succ, 4),
                "wilson95": [round(x, 4) for x in wilson_ci(int(round(oracle_succ * n_val)), n_val)],
                "collision_val": round(rate(oracle_rows, "collided"), 4),
                "timeout_val": round(rate(oracle_rows, "timeout"), 4),
                "per_point_success_val": [round(float(np.mean([1.0 if x["success"] else 0.0 for x in oracle_rows
                                                               if x["mu_point"] == round(mu, 4)])), 3) for mu in mus],
            },
            "plan_family_oracle_success_val_stream_D": round(plan_oracle_succ, 4),
            "best_fixed_success_val_stream_D": round(fixed_succ, 4),
            "voi_commitment_stream_D": round(plan_oracle_succ - fixed_succ, 4),
            "oracle_strength_guard": {
                "required": f"oracle >= plan_oracle - {ORACLE_STRENGTH_SLACK}",
                "oracle": round(oracle_succ, 4), "plan_oracle": round(plan_oracle_succ, 4),
                "pass": bool(strength_ok),
            },
            "voi_belief_clean_val": round(gap, 4),
            "gap_bar": ACCEPTANCE_GAP_BAR,
            "acceptance_pass": bool(gap_pass and strength_ok),
            "gap_pass": bool(gap_pass),
            "episodes": pool.episodes,
        }
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


def candidate_knob_table(cand: F2Candidate) -> dict[str, Any]:
    return {
        "candidate_id": cand.candidate_id,
        "intent": cand.intent,
        "track": {"kind": "circle", "radius_m": TRACK_RADIUS, "corridor_half_width_m": cand.corridor_half,
                  "offtrack_rule": "hard failure at |lateral_error| > corridor_half (env track_width knob)"},
        "obstacle": {
            "half_width_m": cand.ob_half_width,
            "lateral_offset_delta_mag_m": cand.delta_mag,
            "sign_rule": cand.sign_rule,
            "mu_side_threshold": None if math.isnan(cand.mu_side_threshold) else cand.mu_side_threshold,
            "centerline_compensation": "R - sqrt(R^2 - d^2) added to the signed offset",
            "effective_offset_jitter": "inherits ego reset radial noise N(0, 0.3) keyed by rollout seed",
            "open_side_traverse_from_center_nominal_m": round(cand.clear - cand.delta_mag, 3),
            "closed_side_room_nominal_m": round(cand.corridor_half - cand.delta_mag - cand.ob_half_width - EGO_HALF, 3),
        },
        "mu_to_distance_knots": {"mu": list(cand.d_knots_mu), "d_m": list(cand.d_knots_d)},
        "distance_jitter": {"law": "U(-0.75, 0.75) keyed [SEED_BASE,777,seed]", "floor_m": D_FLOOR_M},
        "reveal_distance_m": cand.reveal,
        "max_steps": cand.max_steps,
        "deadline_s": cand.deadline_s,
        "rewards": {"pass": PASS_REWARD, "collision": COLLISION_PENALTY},
        "initial_speed_mps": V0,
        "mu_domain": list(MU_DOMAIN),
    }


REPAIR_PREREG_JSON = REPO / "experiments/feasibility_audit/family2_prereg_repair1.json"
REPAIR_SEEKER_STYLES = ("brake", "drive")
REPAIR_SEEKER_RATES = (6000.0, 20000.0, 60000.0)


def run_repair_accept(args) -> None:
    """Pre-registered repair round 1: acceptance re-run on the frozen winner with
    the seeker grid extended by the drive_ramp style. Criteria, geometry, oracle,
    seed streams and validation counts are unchanged (family2_prereg_repair1.json)."""
    started = time.time()
    payload = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
    repair_prereg = json.loads(REPAIR_PREREG_JSON.read_text(encoding="utf-8"))
    assert payload.get("winner"), "repair-accept requires a winner in the existing results JSON"
    winner_id = payload["winner"]
    candidates = frozen_candidates()
    cand = next(c for c in candidates if c.candidate_id == winner_id)
    construction = next(e["construction"] for e in payload["candidates_all_reported"]
                        if e["construction"]["candidate_id"] == winner_id)
    mod_r = load_module(RAMP_SCRIPT, "ramp_policy_voi_regime")
    points = 4 if args.quick else 12
    lo, hi = MU_DOMAIN
    mus = [lo + (i + 0.5) / points * (hi - lo) for i in range(points)]
    acc_sel_ks = [0] if args.quick else list(range(4))
    acc_val_ks = [0, 1] if args.quick else list(range(10))
    rows_out: list[dict[str, Any]] = []
    print(f"[repair round 1] acceptance re-run on {winner_id}: styles {REPAIR_SEEKER_STYLES} "
          f"x rates {REPAIR_SEEKER_RATES}, {points} pts x {len(acc_val_ks)} val seeds")
    acceptance = accept_candidate(mod_r, cand, mus, acc_sel_ks, acc_val_ks, construction, rows_out,
                                  seeker_styles=REPAIR_SEEKER_STYLES, seeker_rates=REPAIR_SEEKER_RATES)
    print(f"  oracle={acceptance['oracle']['success_val']:.3f} seeker={acceptance['seeker']['success_val']:.3f} "
          f"({acceptance['seeker']['plan']}) gap={acceptance['voi_belief_clean_val']:+.4f} "
          f"(bar {ACCEPTANCE_GAP_BAR}) strength_guard={acceptance['oracle_strength_guard']['pass']} "
          f"PASS={acceptance['acceptance_pass']}")

    from autodrift.artifacts import utc_timestamp, write_csv_rows

    rows_csv = RUN_DIR / "episode_rows_repair1.csv"
    write_csv_rows(rows_csv, rows_out)
    payload["acceptance_round_0"] = payload["acceptance"]
    payload["acceptance"] = acceptance
    payload["repair_round_1"] = {
        "preregistration_file": str(REPAIR_PREREG_JSON),
        "what_changed": repair_prereg["repair_frozen"]["what_changes"],
        "declared_deviation": repair_prereg["repair_frozen"]["declared_deviation"],
        "episode_rows_csv": str(rows_csv),
    }
    if payload.get("final_spec"):
        payload["final_spec"]["status"] = ("frozen" if acceptance["acceptance_pass"]
                                           else "construction-passed, acceptance FAILED after repair round 1")
        payload["final_spec"]["clean_acceptance_numbers"] = {
            "round": 1,
            "oracle_success_val": acceptance["oracle"]["success_val"],
            "seeker_success_val": acceptance["seeker"]["success_val"],
            "voi_belief_clean_val": acceptance["voi_belief_clean_val"],
            "gap_bar": ACCEPTANCE_GAP_BAR,
            "seeker_params": acceptance["seeker"]["params"],
            "oracle_dv_per_point": acceptance["oracle"]["dv_per_point"],
            "validation_episodes_per_arm": acceptance["validation_episodes_per_arm"],
        }
    payload["generated_at_utc"] = utc_timestamp()
    payload["repair_elapsed_s"] = round(time.time() - started, 1)
    Path(args.results_json).write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results updated -> {args.results_json}")
    print(f"repair episode rows -> {rows_csv} ({len(rows_out)} rows)")
    print(f"HEADLINE: repair-round-1 acceptance gap={acceptance['voi_belief_clean_val']:+.4f} "
          f"({'PASS' if acceptance['acceptance_pass'] else 'FAIL'}) | elapsed {time.time() - started:.0f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--results-json", type=Path, default=RESULTS_JSON)
    parser.add_argument("--repair-accept", action="store_true",
                        help="pre-registered repair round 1 (family2_prereg_repair1.json): re-run "
                             "acceptance only, seeker grid extended with the drive_ramp style; "
                             "construction results loaded from the existing results JSON")
    args = parser.parse_args()

    if args.repair_accept:
        run_repair_accept(args)
        return

    sel_ks, val_ks = list(range(4)), list(range(8))
    acc_sel_ks, acc_val_ks = list(range(4)), list(range(10))
    if args.quick:
        args.points = 4
        sel_ks, val_ks, acc_sel_ks, acc_val_ks = [0], [0, 1], [0], [0, 1]

    started = time.time()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    mod_r = load_module(RAMP_SCRIPT, "ramp_policy_voi_regime")

    lo, hi = MU_DOMAIN
    mus = [lo + (i + 0.5) / args.points * (hi - lo) for i in range(args.points)]
    rows_out: list[dict[str, Any]] = []
    candidates = frozen_candidates()

    print(f"[1/3] construction stage: {len(candidates)} candidates x {len(plan_family(candidates[0]))} plans x "
          f"{args.points} mu points x {len(sel_ks)}+{len(val_ks)} seeds")
    construction_results = []
    for cand in candidates:
        t0 = time.time()
        res = construct_candidate(cand, mus, sel_ks, val_ks, rows_out)
        res["elapsed_s"] = round(time.time() - t0, 1)
        construction_results.append(res)
        print(f"  {cand.candidate_id:<28} VoI_val={res['voi_commitment_val']:+.3f} (bar {CONSTRUCTION_VOI_BAR}) "
              f"oracle={res['oracle_success_val']:.3f} fixed={res['best_fixed_success_val']:.3f} "
              f"({res['best_fixed_plan']}) pass={res['construction_pass']} [{res['elapsed_s']}s]")

    qualifying = [i for i, res in enumerate(construction_results) if res["construction_pass"]]
    winner_idx = max(qualifying, key=lambda i: construction_results[i]["voi_commitment_val"]) if qualifying else None

    acceptance = None
    if winner_idx is not None:
        cand = candidates[winner_idx]
        print(f"[2/3] acceptance stage on winner {cand.candidate_id} "
              f"({args.points} pts x {len(acc_val_ks)} val seeds = {args.points * len(acc_val_ks)} episodes/arm)")
        acceptance = accept_candidate(mod_r, cand, mus, acc_sel_ks, acc_val_ks,
                                      construction_results[winner_idx], rows_out)
        print(f"  oracle={acceptance['oracle']['success_val']:.3f} seeker={acceptance['seeker']['success_val']:.3f} "
              f"gap={acceptance['voi_belief_clean_val']:+.4f} (bar {ACCEPTANCE_GAP_BAR}) "
              f"strength_guard={acceptance['oracle_strength_guard']['pass']} "
              f"PASS={acceptance['acceptance_pass']}")
    else:
        print("[2/3] no candidate met the construction criterion -> acceptance skipped (pre-registered route)")

    print("[3/3] writing artifacts")
    from autodrift.artifacts import utc_timestamp, write_csv_rows

    rows_csv = RUN_DIR / ("episode_rows_quick.csv" if args.quick else "episode_rows.csv")
    write_csv_rows(rows_csv, rows_out)

    final_spec = None
    if winner_idx is not None:
        cand = candidates[winner_idx]
        final_spec = {
            "family_id": f"F2_{cand.candidate_id}",
            "status": "frozen" if (acceptance and acceptance["acceptance_pass"]) else "construction-passed, acceptance " + ("FAILED" if acceptance else "not run"),
            "env_knobs": candidate_knob_table(cand),
            "construction_criterion": {
                "voi_commitment_val": construction_results[winner_idx]["voi_commitment_val"],
                "bar": CONSTRUCTION_VOI_BAR,
                "oracle_plan_per_point": construction_results[winner_idx]["oracle_plan_per_point"],
                "best_fixed_plan": construction_results[winner_idx]["best_fixed_plan"],
            },
            "clean_acceptance_numbers": None if acceptance is None else {
                "oracle_success_val": acceptance["oracle"]["success_val"],
                "seeker_success_val": acceptance["seeker"]["success_val"],
                "voi_belief_clean_val": acceptance["voi_belief_clean_val"],
                "gap_bar": ACCEPTANCE_GAP_BAR,
                "seeker_params": acceptance["seeker"]["params"],
                "oracle_dv_per_point": acceptance["oracle"]["dv_per_point"],
                "validation_episodes_per_arm": acceptance["validation_episodes_per_arm"],
            },
            "degradation_scan_adapter": {
                "wrapper": "autodrift.observation_degradation_wrapper.make_env_from_config (add observation_degradation block to the env config)",
                "env_config_builder": "scripts/feasibility_audit/family2_design.py::env_config(candidate, mu, seed)",
                "controllers": "Family2Ramp(mode='oracle'|'seeker') in the same script; seeker tau must be re-calibrated per degradation cell (B2K2 lesson: noise makes single-frame detection blind)",
                "seed_streams_reserved_for_scan": "use a NEW SEED_BASE; A-D offsets of 20260624 are consumed by this design measurement",
            },
        }

    payload = {
        "protocol": "feasibility_audit_family2_design",
        "generated_by": "scripts/feasibility_audit/family2_design.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(args.quick),
        "preregistration": {
            "file": str(PREREG_JSON),
            "criteria_echo": {
                "construction_voi_bar": CONSTRUCTION_VOI_BAR,
                "acceptance_gap_bar": ACCEPTANCE_GAP_BAR,
                "oracle_strength_slack": ORACLE_STRENGTH_SLACK,
                "winner_rule": prereg["winner_selection_rule_frozen"],
            },
        },
        "seed_discipline": {
            "seed_base": SEED_BASE,
            "formula": "SEED_BASE*10 + 17*point + 1000*k + stream_offset",
            "stream_offsets": STREAM_OFFSETS,
            "sel_seeds_per_point": {"construction": len(sel_ks), "acceptance": len(acc_sel_ks)},
            "val_seeds_per_point": {"construction": len(val_ks), "acceptance": len(acc_val_ks)},
        },
        "design_constraint_note": (
            "single-disc geometric fact (reported): from a free centerline approach the wider gap is "
            "always the nearer one, so 'near-narrow vs far-wide' requires pinning the approach line; "
            "the mu-SIGNED open side (F2C2/F2C3) is the honest single-obstacle realization of a "
            "mu-dependent gap choice; the warmup-gate pin variant was rejected by design (gate "
            "collision lacks env-native failure semantics)"
        ),
        "candidates_all_reported": [
            {"knobs": candidate_knob_table(c), "construction": construction_results[i]}
            for i, c in enumerate(candidates)
        ],
        "winner": None if winner_idx is None else candidates[winner_idx].candidate_id,
        "acceptance": acceptance,
        "final_spec": final_spec,
        "env_expressiveness_gaps": [
            "mu-correlated obstacle distance AND mu-signed lateral offset both require per-episode mixtures of degenerate configs; a single env config cannot couple randomization.mu_range with obstacle.distance_range/lateral_offset_range (same gap as B2K2, now needed on two knobs: e.g. obstacle.distance_from_mu and obstacle.lateral_offset_from_mu knot tables)",
            "ego reset radial noise N(0,0.3) leaks into the obstacle's effective lateral offset (obstacle placed relative to the reset pose); a track-frame-anchored obstacle placement knob would decouple geometry jitter from reset noise",
            "warmup_gate collision is metric-only (no termination/penalty), so gate-based approach-line pinning cannot be expressed with env-native failure semantics",
        ],
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {"episode_rows_csv": str(rows_csv), "results_json": str(args.results_json),
                      "preregistration_json": str(PREREG_JSON)},
    }
    args.results_json.parent.mkdir(parents=True, exist_ok=True)
    args.results_json.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {args.results_json}")
    print(f"episode rows -> {rows_csv} ({len(rows_out)} rows)")
    headline = " | ".join(
        f"{r['candidate_id']}: VoI={r['voi_commitment_val']:+.3f} ({'PASS' if r['construction_pass'] else 'fail'})"
        for r in construction_results)
    if acceptance is not None:
        headline += (f" | acceptance gap={acceptance['voi_belief_clean_val']:+.4f} "
                     f"({'PASS' if acceptance['acceptance_pass'] else 'FAIL'})")
    print("HEADLINE: " + headline + f" | elapsed {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
