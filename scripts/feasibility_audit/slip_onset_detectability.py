"""Measurement A: slip-onset detectability and detection latency in obs72.

New self-ID paradigm (threshold-seeking / incremental limit search): the
identification signal is embedded in the useful action itself. A driver ramps
brake/steering toward an estimated limit and stops the ramp the moment the car
"feels" slightly loose. This script measures the obs72 counterpart of that
feeling:

  longitudinal: shortfall between the deceleration EXPECTED from the brake
      actuator state (ch8) under a self-calibrated affine model and the actual
      body ax (ch3, corrected by the yaw_rate*vy term from ch1/ch2). The
      command->force gain (brake_scale) and mass are randomized and unknown, so
      the detector identifies the local gain online and flags its collapse:
      it detects the EFFECTIVE combined limit (0.98*mu*Fz_rear / mass), not mu
      (M150 "capability not parameter").
  lateral: deficit between the yaw rate EXPECTED from the steering state (ch5)
      under a self-calibrated linear-region gain (regressor steer*vx) and the
      actual yaw rate (ch2). Front-tire tanh saturation makes yaw response
      sublinear -> deficit.

Protocol per axis:
  1. CALIBRATION  sub-limit episodes (stimulus capped clearly below the true
     limit using env internals -- harness-only privilege, the DETECTOR never
     sees privileged state). tau = max(1.5 * max calibration signal, floor).
  2. RAMP        command ramps at 0.05/0.1/0.2/0.4 full-scale-per-second on the
     B2K2_final dynamics family extended with brake_scale [0.80,1.15] and
     mass_scale [0.85,1.20] randomization, continuous mu in [0.25,1.15].
     Ground-truth onset from env internals (rear force clamp active /
     front-tire utilization >= 0.90). Measures detection delay (steps),
     overshoot depth (command fraction beyond the limit), miss rate.
  3. SUBLIMIT    fresh sub-limit episodes with the final tau -> false-positive
     rate.

Harness deviations from the B2K2_final task env (documented in the JSON):
  - obstacle disabled (the ramp happens pre-reveal; pre-reveal obs72 is
    bit-identical to the task family because the obstacle slot is zero until
    reveal), max_steps 600 instead of 285 (slow ramps need > 5.7 s; native-
    window flags are reported), and the lateral delay measurement additionally
    runs on a 30 m wide track so that off_track termination does not censor
    the truth onset (native-width runs are kept for the detection-vs-offtrack
    lead measurement; detector inputs do not include track width).

Run:
    PYTHONPATH=src python scripts/feasibility_audit/slip_onset_detectability.py
    PYTHONPATH=src python scripts/feasibility_audit/slip_onset_detectability.py --quick
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv

REPO = Path(__file__).resolve().parents[2]
RESULTS_JSON = REPO / "experiments/feasibility_audit/slip_onset_detectability.json"
RUN_DIR = REPO / "runs/feasibility_audit/slip_onset_detectability"

DT = 0.02
V0 = 8.0
SEED_BASE = 20260616  # fresh stream (B=20260612, C=20260613, final=20260615)
OBS_DIM = 72
ROAD_LEFT_START, ROAD_RIGHT_START = 12, 28
WHEELBASE = 2.80
MAX_STEER_RAD = 0.62
BASE_MASS = 1450.0
BASE_MAX_BRAKE = 6000.0

RAMP_RATES = (0.05, 0.10, 0.20, 0.40)  # command full-scale fraction per second
MU_BIN_EDGES = (0.25, 0.45, 0.65, 0.85, 1.15)
NATIVE_MAX_STEPS = 285  # B2K2_final deadline window (5.7 s)
HARNESS_MAX_STEPS = 600
LAT_TRUTH_UTILIZATION = 0.90  # front-tire utilization defining lateral onset
TAU_FLOOR_LONG = 0.15  # m/s^2
TAU_FLOOR_LAT = 0.03  # rad/s
TAU_CALIB_SAFETY = 1.5

CLAIM_BOUNDARY = (
    "Feasibility-audit SIGNAL measurement only: scripted open-loop brake/steer ramps on the "
    "B2K2_final dynamics family (extended with brake_scale/mass randomization) measure whether "
    "and how fast a pure-obs72 detector can flag tire-limit onset, plus false-positive/miss "
    "rates and overshoot depth. No driver-performance, training, gate-validity, repair-success, "
    "or self-ID capability claim is made."
)


# ------------------------------------------------------------------ env family


def ramp_env_config(track_width: float = 5.0, max_steps: int = HARNESS_MAX_STEPS) -> dict[str, Any]:
    """B2K2_final dynamics/track family, obstacle out (pre-reveal phase),
    brake_scale + mass_scale randomization enabled, continuous mu."""
    return {
        "dt": DT,
        "max_steps": max_steps,
        "track_kind": "circle",
        "track_radius": 900.0,
        "track_width": track_width,
        "speed_range": [V0, V0],
        "beta_target_range": [0.40, 0.40],
        "friction_limited_speed": False,
        "history_length": 1,
        "action_history_mode": "full",
        "wheel_observation_mode": "none",
        "include_privileged_params": False,
        "randomization": {
            "mu_range": [0.25, 1.15],
            "mass_scale_range": [0.85, 1.20],
            "brake_scale_range": [0.80, 1.15],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "obstacle": {"enabled": False},
    }


# --------------------------------------------------- actor-visible detector


class GatedRLS:
    """Recursive least squares with forgetting; updates are gated externally."""

    def __init__(self, dim: int, lam: float = 0.995, p0: float = 100.0):
        self.theta = np.zeros(dim, dtype=np.float64)
        self.P = np.eye(dim, dtype=np.float64) * p0
        self.lam = lam
        self.n_updates = 0

    def predict(self, x: np.ndarray) -> float:
        return float(np.dot(x, self.theta))

    def update(self, x: np.ndarray, y: float) -> None:
        Px = self.P @ x
        gain = Px / (self.lam + float(np.dot(x, Px)))
        err = y - float(np.dot(x, self.theta))
        self.theta = self.theta + gain * err
        self.P = (self.P - np.outer(gain, Px)) / self.lam
        self.n_updates += 1


class SlipOnsetDetector:
    """Actor-visible slip-onset detector: a pure function of the obs72 stream.

    Feed raw 72-dim frames in temporal order via step(); no env internals, no
    privileged parameters, no actions required (uses actuator-state channels).

    axis="long" (threshold braking):
        y    = 15*obs[3] - (2.5*obs[2]) * (12*obs[1])        # ax minus r*vy
        x    = [1, obs[8], (20*obs[0])^2 / 100]              # bias, brake state, drag
        sig  = y - theta.x                                   # decel shortfall, m/s^2
    axis="lat" (threshold steering):
        y    = 2.5*obs[2]                                    # yaw rate
        x    = [1, obs[5] * 20*obs[0] / 10]                  # bias, steer*vx
        sig  = sign(obs[5]) * (theta.x - y)                  # yaw-rate deficit, rad/s

    Gated RLS: always update during WARMUP_STEPS; afterwards update only while
    sig < UPDATE_GATE_FRACTION*tau (one-sided gate: response shortfall freezes
    the model, over-response keeps adapting). Armed once >= MIN_UPDATES updates
    AND the excitation channel (obs[8] / obs[5]*vx) spans >= min_span. Fires
    after PERSIST_K consecutive armed steps with sig > tau.

    The fitted theta is the LOCAL command->response gain, so the detector flags
    the effective combined limit (capability), never mu/brake_scale themselves.
    """

    WARMUP_STEPS = 10
    MIN_UPDATES = 15
    PERSIST_K = 3
    UPDATE_GATE_FRACTION = 0.5

    def __init__(self, axis: str, tau: float):
        if axis not in ("long", "lat"):
            raise ValueError(f"unknown axis: {axis}")
        self.axis = axis
        self.tau = float(tau)
        self.rls = GatedRLS(3 if axis == "long" else 2)
        self.min_span = 0.04 if axis == "long" else 0.30
        self.t = -1
        self.exceed_run = 0
        self.fired_step: int | None = None
        self.armed_step: int | None = None
        self._exc_min = math.inf
        self._exc_max = -math.inf

    def _features(self, obs: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        if self.axis == "long":
            vx = 20.0 * obs[0]
            vy = 12.0 * obs[1]
            r = 2.5 * obs[2]
            ax = 15.0 * obs[3]
            b = float(obs[8])
            y = ax - r * vy
            x = np.array([1.0, b, vx * vx / 100.0], dtype=np.float64)
            return x, y, b, 1.0
        vx = 20.0 * obs[0]
        r = 2.5 * obs[2]
        steer = float(obs[5])
        y = r
        x = np.array([1.0, steer * vx / 10.0], dtype=np.float64)
        return x, y, steer * vx, (1.0 if steer >= 0.0 else -1.0)

    def step(self, obs: np.ndarray) -> dict[str, Any]:
        self.t += 1
        obs = np.asarray(obs, dtype=np.float64)
        x, y, excitation, sign = self._features(obs)
        pred = self.rls.predict(x)
        signal = (y - pred) if self.axis == "long" else sign * (pred - y)
        in_warmup = self.t < self.WARMUP_STEPS
        if in_warmup or signal < self.UPDATE_GATE_FRACTION * self.tau:
            self.rls.update(x, y)
            self._exc_min = min(self._exc_min, excitation)
            self._exc_max = max(self._exc_max, excitation)
        armed = (
            not in_warmup
            and self.rls.n_updates >= self.MIN_UPDATES
            and (self._exc_max - self._exc_min) >= self.min_span
        )
        if armed and self.armed_step is None:
            self.armed_step = self.t
        if self.fired_step is None:
            if armed and signal > self.tau:
                self.exceed_run += 1
                if self.exceed_run >= self.PERSIST_K:
                    self.fired_step = self.t
            else:
                self.exceed_run = 0
        return {
            "t": self.t,
            "signal": float(signal),
            "pred": float(pred),
            "y": float(y),
            "armed": bool(armed),
            "fired": self.fired_step is not None,
            "gain": float(self.rls.theta[1]),
        }


def detector_spec(tau_long: float, tau_lat: float) -> dict[str, Any]:
    """Machine-readable spec of the actor-visible detector for measurement B /
    future policies. Everything is a function of raw obs72 frames only."""
    return {
        "class": "scripts/feasibility_audit/slip_onset_detectability.py::SlipOnsetDetector",
        "input": "raw 72-dim observation frames in temporal order (history_length=1 layout)",
        "channels_used": {
            "vx": {"index": 0, "scale": 20.0},
            "vy": {"index": 1, "scale": 12.0},
            "yaw_rate": {"index": 2, "scale": 2.5},
            "ax_body": {"index": 3, "scale": 15.0},
            "steer_state": {"index": 5, "scale": "max_steer (0.62 rad, not randomized)"},
            "brake_actuator_state": {"index": 8, "scale": "fraction of max_brake_force (randomized, unknown to actor)"},
        },
        "longitudinal": {
            "target": "y = 15*obs[3] - (2.5*obs[2])*(12*obs[1])",
            "regressors": "[1, obs[8], (20*obs[0])^2/100]",
            "signal": "y - theta.x  (decel shortfall, m/s^2)",
            "tau": tau_long,
            "min_excitation_span_obs8": 0.04,
        },
        "lateral": {
            "target": "y = 2.5*obs[2]",
            "regressors": "[1, obs[5]*(20*obs[0])/10]",
            "signal": "sign(obs[5]) * (theta.x - y)  (yaw-rate deficit, rad/s)",
            "tau": tau_lat,
            "min_excitation_span_steer_times_vx": 0.30,
        },
        "estimator": "RLS, forgetting 0.995, P0=100*I, gated updates",
        "warmup_steps": SlipOnsetDetector.WARMUP_STEPS,
        "min_updates_to_arm": SlipOnsetDetector.MIN_UPDATES,
        "update_gate": "update only while signal < 0.5*tau (one-sided; warmup always updates)",
        "fire_rule": f"signal > tau for {SlipOnsetDetector.PERSIST_K} consecutive armed steps",
        "identifies": (
            "effective combined actuation limit (0.98*mu*Fz_rear/mass longitudinal; front-tire "
            "tanh saturation lateral), NOT mu or brake_scale (M150 capability-not-parameter)"
        ),
    }


# -------------------------------------------------------------- stimulus side


def centerline_steer(obs: np.ndarray, j: int = 2, gain: float = 1.6, cap: float = 0.45) -> float:
    lx = obs[ROAD_LEFT_START + 2 * j] * 80.0
    ly = obs[ROAD_LEFT_START + 2 * j + 1] * 20.0
    rx = obs[ROAD_RIGHT_START + 2 * j] * 80.0
    ry = obs[ROAD_RIGHT_START + 2 * j + 1] * 20.0
    xt, yt = 0.5 * (lx + rx), 0.5 * (ly + ry)
    alpha = math.atan2(yt, max(xt, 1.0))
    dist = max(math.hypot(xt, yt), 2.0)
    steer_angle = math.atan2(2.0 * WHEELBASE * math.sin(alpha), dist)
    return float(np.clip(gain * steer_angle / MAX_STEER_RAD, -cap, cap))


class BrakeRampController:
    """Brake command ramps at `rate` full-scale/s up to `cap`; steering holds centerline."""

    def __init__(self, rate: float, cap: float = 1.0):
        self.rate, self.cap, self.t = rate, cap, 0

    def act(self, obs: np.ndarray) -> np.ndarray:
        brake01 = min(self.rate * self.t * DT, self.cap)
        self.t += 1
        return np.array([centerline_steer(obs), -1.0, 2.0 * brake01 - 1.0], dtype=np.float64)


class SteerRampController:
    """Steer command ramps at `rate` full-scale/s up to `cap`; throttle holds V0."""

    def __init__(self, rate: float, cap: float = 1.0, v_target: float = V0):
        self.rate, self.cap, self.v_target, self.t = rate, cap, v_target, 0

    def act(self, obs: np.ndarray) -> np.ndarray:
        vx = 20.0 * float(obs[0])
        err = self.v_target - vx
        if err >= -0.15:
            throttle01, brake01 = float(np.clip(0.55 * err, 0.0, 1.0)), 0.0
        else:
            throttle01, brake01 = 0.0, float(np.clip(-0.5 * err, 0.0, 1.0))
        steer = min(self.rate * self.t * DT, self.cap)
        self.t += 1
        return np.array([steer, 2.0 * throttle01 - 1.0, 2.0 * brake01 - 1.0], dtype=np.float64)


def brake_sat_fraction(params) -> float:
    """Command fraction at which the rear longitudinal clamp binds (>1 = unsaturable)."""
    return 0.98 * params.mu * params.static_fzr / params.max_brake_force


def sublimit_steer_cap(params, v: float, u_star: float) -> float:
    """Steady-state steer (normalized) that holds front utilization ~u_star (<1).
    Harness-only construction (uses env params); the detector never sees this."""
    cap_f = params.mu * params.static_fzf
    cap_r = params.mu * params.static_fzr
    f_front = u_star * cap_f
    ay = f_front * params.wheelbase / (params.mass * params.lr)
    f_rear = min(params.mass * ay * params.lf / params.wheelbase, 0.95 * cap_r)
    alpha_f = (cap_f / params.cf) * math.atanh(u_star)
    alpha_r = (cap_r / params.cr) * math.atanh(min(f_rear / cap_r, 0.95))
    radius = v * v / max(ay, 1e-6)
    delta = params.wheelbase / radius + alpha_f - alpha_r
    return float(np.clip(delta / params.max_steer, 0.02, 1.0))


# ----------------------------------------------------------------- episodes


@dataclass
class EpisodeResult:
    axis: str
    condition: str
    rate: float
    seed: int
    mu: float
    mass_scale: float
    brake_scale: float
    cap: float
    end_step: int
    term_reason: str
    sat_step: int  # -1 = truth onset never occurred
    fired_step: int  # -1 = never fired
    armed_step: int
    delay_steps: float
    cmd_at_sat: float  # command-fraction (brake state frac / steer norm) at truth onset
    cmd_at_detect: float
    overshoot_frac: float  # cmd_at_detect - cmd_at_sat
    overshoot_pct: float  # 100 * overshoot_frac / cmd_at_sat
    u_at_detect: float  # lateral: front utilization at detection
    post_onset_steps: int  # episode steps available after truth onset (-1 if no onset)
    sat_in_native: bool
    detect_in_native: bool
    max_signal_presat: float
    signal_at_sat_plus10: float
    fitted_gain: float

    def row(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def run_episode(
    env: AutoDriftEnv,
    axis: str,
    condition: str,
    rate: float,
    seed: int,
    tau: float,
    sublimit_frac: float | None = None,
    trace_path: Path | None = None,
) -> EpisodeResult:
    obs, _ = env.reset(seed=seed)
    p = env.params
    if axis == "long":
        b_sat = brake_sat_fraction(p)
        cap = min(0.6 * b_sat, 1.0) if condition != "ramp" else 1.0
        if condition != "ramp" and sublimit_frac is not None:
            cap = min(sublimit_frac * b_sat, 1.0)
        controller: Any = BrakeRampController(rate, cap=cap)
    else:
        cap = 1.0 if condition == "ramp" else sublimit_steer_cap(p, V0, sublimit_frac or 0.5)
        controller = SteerRampController(rate, cap=cap)

    detector = SlipOnsetDetector(axis, tau)
    trace_rows: list[dict[str, Any]] = []

    def truth(step: int) -> tuple[bool, float, float]:
        """(onset_active, command_fraction_now, utilization_now)"""
        if axis == "long":
            b_state = max(-env.state.drive_force, 0.0) / p.max_brake_force
            sat = (-env.state.drive_force) >= 0.98 * p.mu * p.static_fzr - 1e-9
            util = min(abs(env.last_forces.fx_rear) / max(0.98 * p.mu * p.static_fzr, 1e-9), 1.0)
            return sat, b_state, util
        u_front = abs(env.last_forces.fy_front) / max(p.mu * p.static_fzf, 1e-9)
        return u_front >= LAT_TRUTH_UTILIZATION, float(env.state.steer / p.max_steer), u_front

    det = detector.step(obs)
    sat_active, cmd_now, util_now = truth(0)
    sat_step = 0 if sat_active else -1
    cmd_at_sat = cmd_now if sat_active else float("nan")
    signals: list[float] = [det["signal"]]
    cmds: list[float] = [cmd_now]
    utils: list[float] = [util_now]

    terminated = truncated = False
    step = 0
    while not (terminated or truncated):
        action = controller.act(np.asarray(obs, dtype=np.float64))
        obs, _, terminated, truncated, info = env.step(action)
        step += 1
        det = detector.step(obs)
        sat_active, cmd_now, util_now = truth(step)
        signals.append(det["signal"])
        cmds.append(cmd_now)
        utils.append(util_now)
        if sat_active and sat_step < 0:
            sat_step = step
            cmd_at_sat = cmd_now
        if trace_path is not None:
            trace_rows.append(
                {
                    "t": step,
                    "cmd_fraction": round(cmd_now, 5),
                    "y": round(det["y"], 5),
                    "pred": round(det["pred"], 5),
                    "signal": round(det["signal"], 5),
                    "truth_sat": int(sat_active),
                    "utilization": round(util_now, 5),
                    "vx": round(20.0 * float(np.asarray(obs)[0]), 4),
                }
            )

    fired = detector.fired_step if detector.fired_step is not None else -1
    delay = float(fired - sat_step) if (fired >= 0 and sat_step >= 0) else float("nan")
    cmd_at_detect = cmds[fired] if fired >= 0 else float("nan")
    overshoot = (cmd_at_detect - cmd_at_sat) if (fired >= 0 and sat_step >= 0) else float("nan")
    overshoot_pct = (
        100.0 * overshoot / cmd_at_sat if (fired >= 0 and sat_step >= 0 and cmd_at_sat > 1e-9) else float("nan")
    )
    presat_end = sat_step if sat_step >= 0 else len(signals)
    max_presat = float(np.max(signals[: max(presat_end, 1)])) if presat_end > 0 else float("nan")
    sig_at_sat10 = (
        float(signals[sat_step + 10]) if (sat_step >= 0 and sat_step + 10 < len(signals)) else float("nan")
    )
    if trace_path is not None and trace_rows:
        with trace_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(trace_rows[0].keys()))
            writer.writeheader()
            writer.writerows(trace_rows)

    return EpisodeResult(
        axis=axis,
        condition=condition,
        rate=rate,
        seed=seed,
        mu=float(p.mu),
        mass_scale=float(p.mass / BASE_MASS),
        brake_scale=float(p.max_brake_force / BASE_MAX_BRAKE),
        cap=float(cap),
        end_step=step,
        term_reason=str(env.termination_reason or env.completion_reason or ""),
        sat_step=sat_step,
        fired_step=fired,
        armed_step=detector.armed_step if detector.armed_step is not None else -1,
        delay_steps=delay,
        cmd_at_sat=float(cmd_at_sat),
        cmd_at_detect=float(cmd_at_detect),
        overshoot_frac=float(overshoot),
        overshoot_pct=float(overshoot_pct),
        u_at_detect=float(utils[fired]) if fired >= 0 else float("nan"),
        post_onset_steps=(step - sat_step) if sat_step >= 0 else -1,
        sat_in_native=bool(0 <= sat_step <= NATIVE_MAX_STEPS),
        detect_in_native=bool(0 <= fired <= NATIVE_MAX_STEPS),
        max_signal_presat=max_presat,
        signal_at_sat_plus10=sig_at_sat10,
        fitted_gain=float(det["gain"]),
    )


# -------------------------------------------------------------- aggregation


def pct(values: list[float], q: float) -> float:
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=np.float64)
    return float(np.percentile(arr, q)) if arr.size else float("nan")


def mu_bin_label(mu: float) -> str:
    idx = int(np.clip(np.searchsorted(MU_BIN_EDGES, mu, side="right") - 1, 0, len(MU_BIN_EDGES) - 2))
    return f"[{MU_BIN_EDGES[idx]:.2f},{MU_BIN_EDGES[idx + 1]:.2f})"


def cell_stats(rows: list[EpisodeResult]) -> dict[str, Any]:
    n = len(rows)
    saturated = [r for r in rows if r.sat_step >= 0]
    detected = [r for r in saturated if r.fired_step >= 0]
    missed = [r for r in saturated if r.fired_step < 0]
    return {
        "n": n,
        "n_truth_onset": len(saturated),
        "n_detected": len(detected),
        "n_missed": len(missed),
        "miss_rate": (len(missed) / len(saturated)) if saturated else float("nan"),
        "missed_post_onset_steps_median": pct([float(r.post_onset_steps) for r in missed], 50),
        "u_at_detect_median": pct([r.u_at_detect for r in detected], 50),
        "delay_steps_median": pct([r.delay_steps for r in detected], 50),
        "delay_steps_p90": pct([r.delay_steps for r in detected], 90),
        "overshoot_frac_median": pct([r.overshoot_frac for r in detected], 50),
        "overshoot_pct_median": pct([r.overshoot_pct for r in detected], 50),
        "overshoot_pct_p90": pct([r.overshoot_pct for r in detected], 90),
        "onset_in_native_window_frac": (
            float(np.mean([r.sat_in_native for r in saturated])) if saturated else float("nan")
        ),
        "detect_in_native_window_frac": (
            float(np.mean([r.detect_in_native for r in detected])) if detected else float("nan")
        ),
    }


def aggregate_axis(ramp_rows: list[EpisodeResult], sub_rows: list[EpisodeResult]) -> dict[str, Any]:
    table: dict[str, dict[str, Any]] = {}
    for rate in RAMP_RATES:
        for i in range(len(MU_BIN_EDGES) - 1):
            label = f"[{MU_BIN_EDGES[i]:.2f},{MU_BIN_EDGES[i + 1]:.2f})"
            rows = [r for r in ramp_rows if r.rate == rate and mu_bin_label(r.mu) == label]
            table[f"rate={rate:g}|mu={label}"] = cell_stats(rows)
    per_rate = {f"rate={rate:g}": cell_stats([r for r in ramp_rows if r.rate == rate]) for rate in RAMP_RATES}
    unsaturable = [r for r in ramp_rows if r.sat_step < 0]
    fp_ramp_unsaturable = [r for r in unsaturable if r.fired_step >= 0]
    fp_sub = [r for r in sub_rows if r.fired_step >= 0 and r.sat_step < 0]
    sub_with_onset = [r for r in sub_rows if r.sat_step >= 0]  # sub-limit construction failed
    detected = [r for r in ramp_rows if r.sat_step >= 0 and r.fired_step >= 0]
    saturated = [r for r in ramp_rows if r.sat_step >= 0]
    return {
        "per_cell": table,
        "per_rate": per_rate,
        "overall": cell_stats(ramp_rows),
        "false_positives": {
            "sublimit_episodes": len(sub_rows),
            "sublimit_construction_leaks": len(sub_with_onset),
            "fp_count": len(fp_sub),
            "fp_rate": (len(fp_sub) / max(len(sub_rows) - len(sub_with_onset), 1)),
            "ramp_unsaturable_episodes": len(unsaturable),
            "ramp_unsaturable_fp_count": len(fp_ramp_unsaturable),
        },
        "signal_validation": {
            "max_presat_signal_p99": pct([r.max_signal_presat for r in saturated], 99),
            "signal_at_onset_plus10_median": pct([r.signal_at_sat_plus10 for r in saturated], 50),
            "separation_ratio_median_over_p99": (
                pct([r.signal_at_sat_plus10 for r in saturated], 50)
                / max(pct([r.max_signal_presat for r in saturated], 99), 1e-9)
            ),
        },
        "fitted_gain_median": pct([r.fitted_gain for r in detected], 50),
    }


# ------------------------------------------------------------------ protocol


def calibrate_tau(env: AutoDriftEnv, axis: str, n: int, seed0: int, floor: float) -> dict[str, Any]:
    """Sub-limit episodes with tau=inf-like gate (huge tau -> always update,
    never fire); tau = max(SAFETY * max signal, floor)."""
    maxima: list[float] = []
    leaks = 0
    for k in range(n):
        rate = RAMP_RATES[k % len(RAMP_RATES)]
        res = run_episode(env, axis, "calib", rate, seed0 + k, tau=1e9, sublimit_frac=0.5)
        if res.sat_step >= 0:
            leaks += 1
            continue
        maxima.append(res.max_signal_presat)
    tau = max(TAU_CALIB_SAFETY * max(maxima), floor) if maxima else floor
    return {
        "n_episodes": n,
        "n_construction_leaks": leaks,
        "max_signal": max(maxima) if maxima else float("nan"),
        "p99_signal": pct(maxima, 99),
        "tau_floor": floor,
        "tau": float(tau),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    n_ramp = 8 if args.quick else 60
    n_sub_per_rate = 2 if args.quick else 16
    n_calib = 8 if args.quick else 32
    n_native_lat = 6 if args.quick else 40

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    traces_dir = RUN_DIR / "traces"
    traces_dir.mkdir(exist_ok=True)
    t0 = time.time()

    env_long = AutoDriftEnv(build_env_config(ramp_env_config(track_width=5.0)))
    env_lat_wide = AutoDriftEnv(build_env_config(ramp_env_config(track_width=30.0)))
    env_lat_native = AutoDriftEnv(build_env_config(ramp_env_config(track_width=5.0)))
    assert env_long.base_obs_dim == OBS_DIM, f"obs layout changed: {env_long.base_obs_dim}"

    results: dict[str, Any] = {
        "protocol": "slip_onset_detectability_v1",
        "generated_at_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "claim_boundary": CLAIM_BOUNDARY,
        "seed_base": SEED_BASE,
        "quick": bool(args.quick),
        "env_family": {
            "base": "B2K2_final dynamics/track family (docs/selfid-task-final-spec-2026-06.md)",
            "config": ramp_env_config(),
            "deviations": [
                "obstacle disabled (ramp = pre-reveal phase; pre-reveal obs72 identical to task family)",
                f"max_steps {HARNESS_MAX_STEPS} instead of {NATIVE_MAX_STEPS} (native-window flags reported)",
                "randomization extended: brake_scale [0.80,1.15], mass_scale [0.85,1.20] (paradigm requirement)",
                "lateral delay measurement on track_width=30 m (off_track censoring); native 5 m kept for lead-time",
            ],
        },
        "truth_definitions": {
            "long": "rear clamp active: |drive_force| >= 0.98*mu*static_fzr (hard clamp in dynamics.py tire_forces)",
            "lat": f"front utilization |fy_front|/(mu*static_fzf) >= {LAT_TRUTH_UTILIZATION}",
        },
    }

    # ---- calibration
    cal_long = calibrate_tau(env_long, "long", n_calib, SEED_BASE * 100 + 10_000, TAU_FLOOR_LONG)
    cal_lat = calibrate_tau(env_lat_wide, "lat", n_calib, SEED_BASE * 100 + 20_000, TAU_FLOOR_LAT)
    tau_long, tau_lat = cal_long["tau"], cal_lat["tau"]
    results["calibration"] = {"long": cal_long, "lat": cal_lat}
    results["detector_spec"] = detector_spec(tau_long, tau_lat)
    print(f"[calib] tau_long={tau_long:.4f} m/s^2  tau_lat={tau_lat:.4f} rad/s")

    episode_rows: list[dict[str, Any]] = []

    def run_block(env, axis, condition, tau, seed0, n_per_rate, sublimit_frac=None, trace_tag=None):
        rows = []
        for ri, rate in enumerate(RAMP_RATES):
            for k in range(n_per_rate):
                seed = seed0 + ri * 10_000 + k
                trace_path = None
                if trace_tag is not None and k == 0:
                    trace_path = traces_dir / f"{trace_tag}_rate{rate:g}.csv"
                res = run_episode(env, axis, condition, rate, seed, tau, sublimit_frac, trace_path)
                rows.append(res)
                episode_rows.append(res.row())
        return rows

    # ---- longitudinal
    ramp_long = run_block(env_long, "long", "ramp", tau_long, SEED_BASE * 100 + 1_000_000, n_ramp, trace_tag="long_ramp")
    sub_long = run_block(env_long, "long", "sublimit", tau_long, SEED_BASE * 100 + 1_500_000, n_sub_per_rate, sublimit_frac=0.6)
    results["longitudinal"] = aggregate_axis(ramp_long, sub_long)
    print(f"[long] overall: {json.dumps(results['longitudinal']['overall'])}")

    # ---- lateral (wide harness for delay physics)
    ramp_lat = run_block(env_lat_wide, "lat", "ramp", tau_lat, SEED_BASE * 100 + 2_000_000, n_ramp, trace_tag="lat_ramp")
    sub_lat = run_block(env_lat_wide, "lat", "sublimit", tau_lat, SEED_BASE * 100 + 2_500_000, n_sub_per_rate, sublimit_frac=0.5)
    results["lateral"] = aggregate_axis(ramp_lat, sub_lat)
    print(f"[lat]  overall: {json.dumps(results['lateral']['overall'])}")

    # ---- lateral on native 5 m track: detection-vs-offtrack lead time
    native_rows = run_block(env_lat_native, "lat", "ramp", tau_lat, SEED_BASE * 100 + 3_000_000, max(n_native_lat // len(RAMP_RATES), 1))
    leads = []
    for r in native_rows:
        if r.fired_step >= 0 and r.term_reason == "off_track":
            leads.append(r.end_step - r.fired_step)
    results["lateral_native_track"] = {
        "n": len(native_rows),
        "n_offtrack_terminations": sum(1 for r in native_rows if r.term_reason == "off_track"),
        "n_truth_onset_before_offtrack": sum(1 for r in native_rows if r.sat_step >= 0),
        "n_detected": sum(1 for r in native_rows if r.fired_step >= 0),
        "detect_to_offtrack_lead_steps_median": pct([float(v) for v in leads], 50),
        "detect_to_offtrack_lead_steps_p10": pct([float(v) for v in leads], 10),
        "note": "lead = steps between detector firing and off_track termination on the native 5 m track",
    }
    print(f"[lat-native] {json.dumps(results['lateral_native_track'])}")

    # ---- theory check: overshoot ~= tau/gain + persist_k*dt*rate (command fraction)
    det_long = [r for r in ramp_long if r.sat_step >= 0 and r.fired_step >= 0 and np.isfinite(r.fitted_gain)]
    if det_long:
        pred = [
            tau_long / max(abs(r.fitted_gain), 1e-6) + SlipOnsetDetector.PERSIST_K * DT * r.rate
            for r in det_long
        ]
        results["theory_check_long"] = {
            "formula": "overshoot_frac ~= tau/|d a/d b| + persist_k*dt*rate",
            "predicted_overshoot_frac_median": pct(pred, 50),
            "measured_overshoot_frac_median": pct([r.overshoot_frac for r in det_long], 50),
        }

    # ---- artifacts
    episodes_csv = RUN_DIR / "episodes.csv"
    with episodes_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(episode_rows[0].keys()))
        writer.writeheader()
        writer.writerows(episode_rows)
    results["artifacts"] = {
        "episodes_csv": str(episodes_csv.relative_to(REPO)),
        "traces_dir": str(traces_dir.relative_to(REPO)),
        "results_json": str(RESULTS_JSON.relative_to(REPO)),
    }
    results["n_episodes_total"] = len(episode_rows)
    results["elapsed_s"] = round(time.time() - t0, 1)

    for env in (env_long, env_lat_wide, env_lat_native):
        env.close()

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(results, indent=1, default=float))
    print(f"[done] {len(episode_rows)} episodes in {results['elapsed_s']}s -> {RESULTS_JSON}")


if __name__ == "__main__":
    main()
