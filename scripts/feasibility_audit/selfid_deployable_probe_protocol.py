"""Deployable steering-excitation probe protocol for the self-ID commitment task.

Stage 1 of the G1' FAIL_TEACHER_TASK_REWORK route (docs/
selfid-g1prime-ignition-gate-2026-06.md section 6, item 1 "P4 physical-register
repair"): the full-brake probe pulse writes mu into the SPEED register (post-
probe single-frame -> mu R^2 = 0.9409 on the final spec), so any later frame
re-derives mu without history. This script replaces it with a TRANSIENT
STEERING MICRO-EXCITATION whose mu-imprint lives only in the yaw/ay response
HISTORY, and treats the excitation protocol itself as a DEPLOYABLE design
variable with explicit real-world constraints (lane keeping, ride comfort,
small steering amplitude, completion before the commitment point).

Task family: final B2K2 spec loaded from experiments/feasibility_audit/
selfid_task_final_spec.json at runtime (mu in [0.25,1.15], jittered hazard
distance, reveal 9.5 m). Probe / ridge / teacher machinery reused from the
Task-B + final-spec scripts via importlib (no existing file modified).

#############################  PRE-REGISTRATION  #############################
Written BEFORE any measurement run; a mechanical copy is emitted to
experiments/feasibility_audit/selfid_deployable_probe_preregistration.json at
process start (full mode), before any episode executes.

Deployable constraints (level 0, adjudicated PER EPISODE on ground truth).
MEASUREMENT RULE (paired baseline): every episode is paired with a seed-matched
NO-EXCITATION rollout of the same controller (identical env draw, identical
actions before step 12); constraints C1-C3 are adjudicated on the EXCITATION-
ATTRIBUTABLE deviation |trace_excited(t) - trace_baseline(t)|. Rationale
(measured in the pipeline smoke): the env reset places the car with a random
initial sideslip (rng.normal(0, 0.04) rad) and steer=0, so the scripted cruise
itself wanders (no-probe absolute peaks ~0.6 m lateral / ~0.2 rad/s yaw);
absolute peaks would adjudicate the simulator's reset transient, not the
protocol. Absolute peaks are still recorded and reported.
  C1 lane keeping  peak |lateral deviation attributable to the excitation|
                   <= 0.35 m during/after the excitation
                   (3.5 m real lane - 1.8 m car width comfort margin; stricter
                   than the sim track_width = 5 m),
  C2 comfort       peak excitation-attributable |ay| <= 2.0 m/s^2
                   (passenger-car comfort threshold),
  C3 comfort       peak excitation-attributable |yaw_rate| <= 0.15 rad/s,
  C4 amplitude     steering excitation amplitude <= 0.10 x max_steer
                   (micro-excitation; enforced by construction, recorded),
  C5 window        excitation finishes before the earliest possible
                   commitment/reveal point (commit step = 12 + L <= earliest
                   reveal step ~ floor((d_of_mu(0.25) - J - reveal)/(v0*dt))).

Protocol grid (>= 12 deployable candidate points): waveforms = sine 1 Hz x1
cycle, sine 2 Hz x1/x2 cycles, biphasic +/-A pulse (lobe 0.26 s ~1.9 Hz, lobe
0.50 s ~1.0 Hz), displacement-neutral triphasic +A/-A/+A (lobes w,2w,w; w=6
-> 0.48 s, w=12 -> 0.96 s) x amplitudes (0.03, 0.06, 0.10) x max_steer = 21
candidates. Diagnostics (measured for the trade-off curve, NEVER selectable):
duration diagnostics sine 0.5 Hz x1 / sine 1 Hz x2 (L=100 violates C5);
amplitude diagnostics 0.15 / 0.20 (violate C4); brake_legacy (the old
full-brake pulse, contrast); no_probe (information-null control, also the
paired baseline source).

Per protocol point (160 fresh-seed episodes, continuous mu, episode seeds
SHARED across points => paired curve): (a) history-window -> mu ridge R^2
(channels obs[0:12], window 132 steps, stride 4, same 60/20/20 episode-split
protocol as the final spec); (b) TRANSIENCE: post-probe single-frame -> mu
R^2, adjudicated as the MAX over single frames at lags {+5,+10,+20,+40} steps
after the last excitation action, plus frame 109 (legacy window end) and the
window-end frame; (c) per-episode constraint peaks C1-C3 + peak |ax|
(reported); (d) pre-commit speed disturbance (paired |vx - vx_baseline|, peak
during excitation and mean right after it) -- the axis on which steering must
beat braking.

Selection rule: eligible = CANDIDATE points satisfying C4 + C5 by construction
and C1-C3 in 100 % of episodes at the current ladder level; among eligible
points that pass BOTH R^2 bars (history >= 0.9, adjudicated leak <= 0.1),
select the SHORTEST excitation (tie -> higher history R^2) -- shorter probes
maximize the teacher's pre-commit braking window. ACCEPTANCE (adjudicating) =
    history-window R^2 >= 0.9  AND  adjudicated post-probe single-frame
    R^2 <= 0.1  AND  all constraints satisfied in every episode.
If no level-0 point passes, walk the pre-registered relaxation ladder
  L1 yaw<=0.20 | L2 lat<=0.45, ay<=2.5, yaw<=0.25 | L3 lat<=0.60, ay<=3.0,
  yaw<=0.35 | L4 = L3 + diagnostic amplitudes (C4 relaxed)
and record WHICH constraint is binding at each level (deployment-narrative
data, not a failure).

Teacher update acceptance (adjudicating, measured on a fresh disjoint eval
stream, scripted per-mu oracle = cruise v0 -> selected steering excitation ->
commit v_oracle_est(mu) at excitation end -> reactive swerve; constraints
adjudicated on the same paired-baseline rule with a seed-matched zero-
amplitude teacher, window = excitation + settle, clipped at reveal):
    closed-loop success rate >= 0.85  AND  Spearman(speed_at_reveal, mu)
    >= 0.95  AND  excitation-window constraint satisfaction rate = 100 %
    (at the selection's relaxation level; level-0 rate also reported).
The legacy brake-pulse teacher is re-measured on the SAME eval set as the
contrast row (leak / speed disturbance / comfort).

Seed streams (all disjoint from final-spec 20260615* and G1' 20260616*):
  base 20260617; trade-off probe env seed = 20260617*100 + episode (shared
  across protocol points -> paired); teacher eval env seed = 20260617*10 +
  700000 + j; teacher eval mu = U(0.25,1.15) from default_rng([20260617, 2, j]).
##############################################################################

Claim boundary: feasibility-audit PROBE-PROTOCOL design measurement only --
scripted controllers, linear probes and a scripted privileged teacher. No
driver-performance, repair-success, robustness, validation, ranking,
promotion, paper, or self-ID *capability* claim is made. "Deployable" refers
to the explicit constraint set above, not to a road-vehicle qualification.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/selfid_deployable_probe_protocol.py
    PYTHONPATH=src python scripts/feasibility_audit/selfid_deployable_probe_protocol.py --quick
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
FINAL_SPEC_SCRIPT = REPO / "scripts/feasibility_audit/selfid_task_final_spec.py"
FINAL_SPEC_JSON = REPO / "experiments/feasibility_audit/selfid_task_final_spec.json"
RUN_DIR = REPO / "runs/feasibility_audit/selfid_deployable_probe"
TRADEOFF_JSON = REPO / "experiments/feasibility_audit/selfid_deployable_probe_tradeoff.json"
PREREG_JSON = REPO / "experiments/feasibility_audit/selfid_deployable_probe_preregistration.json"

DP_SEED = 20260617  # fresh stream (final spec 20260615, G1' 20260616)
DT = 0.02
V0 = 8.0
MU_LO, MU_HI = 0.25, 1.15
PULSE_START = 12  # first excitation step (anchor frame <= step 11 stays pre-probe)
PROBE_WINDOW = 132  # probe env max_steps = 140; legacy window 110 (frame 109 kept for contrast)
SETTLE_STEPS = 25  # 0.5 s comfort settle window after the last excitation action
POST_LAGS = (5, 10, 20, 40)  # adjudicated single-frame leak lags (steps after pulse end)
LEGACY_FINAL_FRAME = 109  # final frame index of the old 110-step probe window

# level-0 deployable constraints + pre-registered relaxation ladder
RELAX_LADDER = (
    {"level": 0, "lat_m": 0.35, "ay_mps2": 2.0, "yaw_radps": 0.15, "allow_diag_amp": False},
    {"level": 1, "lat_m": 0.35, "ay_mps2": 2.0, "yaw_radps": 0.20, "allow_diag_amp": False},
    {"level": 2, "lat_m": 0.45, "ay_mps2": 2.5, "yaw_radps": 0.25, "allow_diag_amp": False},
    {"level": 3, "lat_m": 0.60, "ay_mps2": 3.0, "yaw_radps": 0.35, "allow_diag_amp": False},
    {"level": 4, "lat_m": 0.60, "ay_mps2": 3.0, "yaw_radps": 0.35, "allow_diag_amp": True},
)
AMP_CAP = 0.10  # C4: fraction of max_steer
R2_HISTORY_MIN = 0.9
R2_LEAK_MAX = 0.1
TEACHER_SUCCESS_MIN = 0.85
TEACHER_SPEARMAN_MIN = 0.95

CLAIM_BOUNDARY = (
    "Feasibility-audit probe-protocol design measurement only: scripted steering micro-"
    "excitations, linear ridge probes and a scripted privileged per-mu teacher on the final "
    "B2K2 commitment family. No driver-performance, repair-success, robustness-result, "
    "validation, ranking, promotion, paper, or self-ID *capability* claim is made. "
    "'Deployable' refers to the explicit pre-registered constraint set, not a road-vehicle "
    "qualification."
)


# ------------------------------------------------------------------ protocols


@dataclass(frozen=True)
class ProbeProtocol:
    """One excitation protocol point. amp is in steering-action units
    (fraction of max_steer = 0.62 rad)."""

    name: str
    kind: str  # "sine" | "biphasic" | "brake_legacy" | "none"
    amp: float
    freq_hz: float
    length_steps: int
    role: str  # "candidate" | "amp_diagnostic" | "duration_diagnostic" | "contrast" | "control"

    @property
    def duration_s(self) -> float:
        return self.length_steps * DT

    @property
    def deployable_amp(self) -> bool:
        return self.kind in ("sine", "biphasic") and self.amp <= AMP_CAP + 1e-12

    def steer_offset(self, k: int) -> float:
        if self.kind == "sine":
            return self.amp * math.sin(2.0 * math.pi * self.freq_hz * k * DT)
        if self.kind == "biphasic":
            half = self.length_steps // 2
            return self.amp if k < half else -self.amp
        if self.kind == "triphasic":  # +A (w), -A (2w), +A (w): zero net heading AND displacement
            w = self.length_steps // 4
            return self.amp if (k < w or k >= 3 * w) else -self.amp
        return 0.0


def protocol_grid() -> list[ProbeProtocol]:
    shapes = [
        ("sine_1Hz_1cyc", "sine", 1.0, 50),
        ("sine_2Hz_1cyc", "sine", 2.0, 25),
        ("sine_2Hz_2cyc", "sine", 2.0, 50),
        ("biph_0.26s", "biphasic", round(1.0 / (26 * DT), 3), 26),
        ("biph_0.50s", "biphasic", 1.0, 50),
        ("triph_0.48s", "triphasic", round(1.0 / (24 * DT), 3), 24),
        ("triph_0.96s", "triphasic", round(1.0 / (48 * DT), 3), 48),
    ]
    out: list[ProbeProtocol] = []
    for amp in (0.03, 0.06, 0.10):
        for sname, kind, f, L in shapes:
            out.append(ProbeProtocol(f"{sname}_a{amp:g}", kind, amp, f, L, "candidate"))
    for amp in (0.06, 0.10):  # duration diagnostics: violate the C5 window by construction
        out.append(ProbeProtocol(f"sine_0.5Hz_1cyc_a{amp:g}", "sine", amp, 0.5, 100, "duration_diagnostic"))
        out.append(ProbeProtocol(f"sine_1Hz_2cyc_a{amp:g}", "sine", amp, 1.0, 100, "duration_diagnostic"))
    for amp in (0.15, 0.20):  # amplitude diagnostics: violate C4 by construction
        out.append(ProbeProtocol(f"sine_1Hz_1cyc_a{amp:g}", "sine", amp, 1.0, 50, "amp_diagnostic"))
        out.append(ProbeProtocol(f"triph_0.96s_a{amp:g}", "triphasic", amp, round(1.0 / (48 * DT), 3), 48, "amp_diagnostic"))
    out.append(ProbeProtocol("brake_legacy", "brake_legacy", 1.0, 0.0, 10, "contrast"))
    out.append(ProbeProtocol("no_probe", "none", 0.0, 0.0, 10, "control"))
    return out


PREREGISTERED: dict[str, Any] = {
    "question": (
        "Can a transient steering micro-excitation, under explicit deployable constraints, "
        "replace the full-brake probe so that mu is inferable from the response HISTORY "
        "(R^2 >= 0.9) but NOT from any post-probe single frame (R^2 <= 0.1)?"
    ),
    "deployable_constraints_level0": {
        "C1_lane_peak_lateral_dev_m": 0.35,
        "C2_comfort_peak_abs_ay_mps2": 2.0,
        "C3_comfort_peak_abs_yaw_rate_radps": 0.15,
        "C4_steer_amplitude_max_fraction_of_max_steer": AMP_CAP,
        "C5_excitation_completes_before_commit_and_earliest_reveal": True,
    },
    "paired_baseline_rule": (
        "C1-C3 are adjudicated on the excitation-ATTRIBUTABLE deviation "
        "|trace_excited(t) - trace_baseline(t)| against a seed-matched no-excitation rollout "
        "of the same controller (identical env draw and pre-step-12 actions). Reason "
        "(measured in the pipeline smoke BEFORE this pre-registration): the env reset draws a "
        "random initial sideslip (normal(0, 0.04) rad, steer=0), so the scripted cruise itself "
        "wanders ~0.6 m lateral / ~0.2 rad/s yaw; absolute peaks would adjudicate the reset "
        "transient, not the protocol. Absolute peaks are recorded and reported alongside."
    ),
    "relaxation_ladder": [dict(level=lv["level"], lat_m=lv["lat_m"], ay_mps2=lv["ay_mps2"],
                               yaw_radps=lv["yaw_radps"], allow_diag_amp=lv["allow_diag_amp"])
                          for lv in RELAX_LADDER],
    "selection_rule": (
        "eligible = candidate points with C4+C5 by construction and C1-C3 satisfied in 100% of "
        "episodes at the current ladder level; among eligible points passing BOTH R^2 bars "
        "(history >= 0.9, adjudicated leak <= 0.1) select the SHORTEST excitation (tie -> "
        "higher history R^2; shorter probes maximize the teacher's pre-commit window); walk "
        "the ladder only if no point at the current level passes acceptance; record the "
        "binding constraint(s) at every level."
    ),
    "acceptance_protocol": {
        "history_window_r2_min": R2_HISTORY_MIN,
        "post_probe_single_frame_r2_max": R2_LEAK_MAX,
        "leak_adjudication": (
            "max ridge R^2 over single frames at lags +5/+10/+20/+40 steps after the last "
            "excitation action, plus frame 109 (legacy window end, if >= pulse_end+4) and the "
            "window-end frame 131"
        ),
        "constraints": "per-episode satisfaction of C1-C3 in all episodes (rate = 1.0)",
    },
    "acceptance_teacher": {
        "closed_loop_success_min": TEACHER_SUCCESS_MIN,
        "spearman_speed_at_reveal_vs_mu_min": TEACHER_SPEARMAN_MIN,
        "excitation_window_constraint_rate": 1.0,
        "teacher": (
            "cruise v0=8 (steps 0..11) -> selected steering excitation (steps 12..12+L-1, "
            "lane keeping + v0 hold active) -> commit v_oracle_est(mu) from step 12+L -> "
            "reactive swerve post-reveal (steer_cap 0.85 / offset 3.0 / gain 3.0); constraint "
            "adjudication on the paired-baseline rule (seed-matched zero-amplitude teacher, "
            "window = excitation + 0.5 s settle, clipped at the first reveal of either arm)"
        ),
        "contrast": "legacy full-brake teacher (G1' OracleTeacher protocol) on the SAME eval set",
    },
    "measurement_protocol": {
        "episodes_per_point": 160,
        "episode_seeds_shared_across_points": True,
        "window_steps": PROBE_WINDOW,
        "channels": "obs[0:12] (ego response + previous command), stride 4 for the history window",
        "ridge": "episode-level 60/20/20 split, alpha picked on val, test R^2 (Task-B episode_ridge_r2)",
        "ground_truth": "lateral_error from track.frame, vx/yaw_rate from state, ay/ax from body acceleration",
        "speed_disturbance": "paired |vx - vx_baseline| peak during excitation and mean over 0.1 s after it",
    },
    "contrast_rows": {
        "brake_legacy_final_spec_numbers": {"r2_single_frame_post_probe": 0.9409, "r2_history": 0.9999},
        "no_probe_final_spec_numbers": {"r2_history": -3.085},
    },
    "seed_streams": {
        "base": DP_SEED,
        "tradeoff_probe_env": f"{DP_SEED}*100 + episode (shared across protocol points -> paired)",
        "teacher_eval_env": f"{DP_SEED}*10 + 700000 + j",
        "teacher_eval_mu": f"U({MU_LO},{MU_HI}) from default_rng([{DP_SEED}, 2, j])",
        "disjoint_from": ["final spec 20260615*", "G1' 20260616* (demo +300000 / eval +600000)"],
    },
}


# ----------------------------------------------------------- family machinery


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_FAMILY_CACHE = None


def get_family():
    """Per-process cached family (workers are reused across tasks)."""
    global _FAMILY_CACHE
    if _FAMILY_CACHE is None:
        _FAMILY_CACHE = load_family()
    return _FAMILY_CACHE


def load_family():
    """Rebuild the final-spec task family from the authoritative JSON (same as G1')."""
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_f = load_module(FINAL_SPEC_SCRIPT, "selfid_task_final_spec")
    spec = json.loads(FINAL_SPEC_JSON.read_text(encoding="utf-8"))
    fs = spec["final_spec"]
    env_knobs = fs["env_knobs"]
    fam = fs["scenario_family"]
    knobs = mod_f.Knobs(
        iteration=0,
        reveal_distance=float(env_knobs["perception_reveal_distance_m"]),
        max_steps=int(env_knobs["max_steps"]),
        obstacle_half_width=float(env_knobs["obstacle_half_width_m"]),
        jitter_d_m=float(fam["distance_jitter"]["J_m"]),
        mu1=float(fam["theta_anchors_mu"][0]),
        pass_reward=float(env_knobs["pass_reward"]),
        collision_penalty=float(env_knobs["collision_penalty"]),
        d_knots=tuple(float(x) for x in fam["mu_to_distance_knots"]["d_m"]),
        v_oracle_knots=tuple(float(x) for x in fam["design_oracle_speed_knots"]["v_mps"]),
        note="deployable probe protocol (from final spec JSON)",
    )
    design = mod_f.make_design(mod_b, knobs)
    variant = mod_f.make_variant(mod_c, knobs)
    return mod_b, mod_c, mod_f, knobs, design, variant, spec


def earliest_reveal_step(variant, knobs) -> int:
    """C5 window bound: earliest reveal over the mu domain (worst-case jitter),
    at constant v0 -- conservative because braking only delays the reveal."""
    d_min = min(variant.d_of_mu(mu) for mu in np.linspace(MU_LO, MU_HI, 91))
    d_min = max(d_min - knobs.jitter_d_m, knobs.reveal_distance + 5.0)
    return int(math.floor((d_min - knobs.reveal_distance) / (V0 * DT)))


# ----------------------------------------------------------------- controllers


class ProbeExcitationController:
    """Cruise v0 + excitation overlay (lane keeping stays active); no commit."""

    def __init__(self, mod_b, design, protocol: ProbeProtocol):
        plan = mod_b.PlanSpec(name=f"dp_{protocol.name}", v_entry=V0, brake_to=None)
        self.inner = mod_b.CommitmentController(plan, design)
        self.protocol = protocol

    def reset(self) -> None:
        self.inner.reset()

    def act(self, obs: np.ndarray) -> np.ndarray:
        t = self.inner.t
        action = self.inner.act(obs)
        p = self.protocol
        if PULSE_START <= t < PULSE_START + p.length_steps:
            k = t - PULSE_START
            if p.kind == "brake_legacy":
                return np.asarray([float(action[0]), -1.0, 1.0], dtype=np.float64)
            if p.kind in ("sine", "biphasic"):
                steer = float(np.clip(float(action[0]) + p.steer_offset(k), -1.0, 1.0))
                return np.asarray([steer, float(action[1]), float(action[2])], dtype=np.float64)
        return action


class ProbeTeacher:
    """Scripted per-mu oracle: cruise v0 -> excitation -> commit v_oracle_est(mu)
    at excitation end -> reactive swerve. Only the teacher sees mu (via v_mu)."""

    def __init__(self, mod_b, design, v_mu: float, protocol: ProbeProtocol):
        plan = mod_b.PlanSpec(name="dp_teacher", v_entry=float(v_mu), brake_to=None,
                              swerve_offset=3.0, swerve_gain=3.0, steer_cap=0.85)
        self.inner = mod_b.CommitmentController(plan, design)
        self.protocol = protocol
        self.commit_step = PULSE_START + protocol.length_steps

    def reset(self) -> None:
        self.inner.reset()

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def act(self, obs: np.ndarray) -> np.ndarray:
        inner = self.inner
        t = inner.t
        action = inner.act(obs)
        p = self.protocol
        if inner.reveal_step is None and t < self.commit_step:
            vx = float(obs[0]) * 20.0
            throttle, brake = inner._speed_actions(vx, V0)
            steer = float(action[0])
            if PULSE_START <= t:
                k = t - PULSE_START
                if p.kind == "brake_legacy":
                    return np.asarray([steer, -1.0, 1.0], dtype=np.float64)
                steer = float(np.clip(steer + p.steer_offset(k), -1.0, 1.0))
            return np.asarray([steer, throttle, brake], dtype=np.float64)
        return action


# ----------------------------------------------------------- trade-off worker


TRACE_KEYS = ("lat", "vx", "yaw", "ay", "ax", "steer")
METRIC_KEYS = ("lat_dev_peak_m", "ay_peak_mps2", "yaw_peak_radps", "ax_peak_mps2",
               "dvx_pulse_peak_mps", "dvx_post_mps", "steer_cmd_peak",
               "abs_lat_dev_peak_m", "abs_ay_peak_mps2", "abs_yaw_peak_radps")


def episode_constraint_metrics(trace: np.ndarray, base: np.ndarray, pulse_end: int,
                               window_end: int | None = None) -> dict[str, float]:
    """Per-episode peaks, channels ordered as TRACE_KEYS (rows of (6, T) arrays).

    Adjudicating C1-C3 values are EXCITATION-ATTRIBUTABLE: |trace - base| with
    a seed-matched no-excitation baseline (paired-baseline rule). Absolute
    peaks (abs_*: lateral vs own pre-excitation mean, raw |ay| / |yaw|) are
    reported alongside."""
    lat, vx, yaw, ay, ax, steer = (trace[i] for i in range(6))
    d = trace - base[:, : trace.shape[1]]
    d_lat, d_vx, d_yaw, d_ay, d_ax, _d_st = (d[i] for i in range(6))
    end = min(window_end if window_end is not None else trace.shape[1], trace.shape[1])
    settle_end = min(pulse_end + SETTLE_STEPS, end)
    own_lat = float(np.mean(lat[5:PULSE_START]))
    sl_comfort = slice(PULSE_START, max(settle_end, PULSE_START + 1))
    sl_lat = slice(PULSE_START, max(end, PULSE_START + 1))
    sl_pulse = slice(PULSE_START, max(min(pulse_end, end), PULSE_START + 1))
    post_hi = min(pulse_end + 5, end)
    post = d_vx[pulse_end:post_hi] if post_hi > pulse_end else d_vx[-1:]
    return {
        "lat_dev_peak_m": float(np.max(np.abs(d_lat[sl_lat]))),
        "ay_peak_mps2": float(np.max(np.abs(d_ay[sl_comfort]))),
        "yaw_peak_radps": float(np.max(np.abs(d_yaw[sl_comfort]))),
        "ax_peak_mps2": float(np.max(np.abs(d_ax[sl_comfort]))),
        "dvx_pulse_peak_mps": float(np.max(np.abs(d_vx[sl_pulse]))),
        "dvx_post_mps": float(abs(float(np.mean(post)))),
        "steer_cmd_peak": float(np.max(np.abs(steer[sl_comfort]))),
        "abs_lat_dev_peak_m": float(np.max(np.abs(lat[sl_lat] - own_lat))),
        "abs_ay_peak_mps2": float(np.max(np.abs(ay[sl_comfort]))),
        "abs_yaw_peak_radps": float(np.max(np.abs(yaw[sl_comfort]))),
    }


def constraint_pass(metrics: dict[str, float], level: dict[str, Any]) -> bool:
    return (metrics["lat_dev_peak_m"] <= level["lat_m"]
            and metrics["ay_peak_mps2"] <= level["ay_mps2"]
            and metrics["yaw_peak_radps"] <= level["yaw_radps"])


def rollout_probe_episode(env, mod_b, design, p: ProbeProtocol, seed: int):
    """One probe-env episode: returns (mu, frames (T,12), trace (6,T), early)."""
    controller = ProbeExcitationController(mod_b, design, p)
    obs, info = env.reset(seed=seed)
    controller.reset()
    mu = float(info["mu"])
    frames: list[np.ndarray] = []
    trace = np.zeros((6, PROBE_WINDOW), dtype=np.float64)
    terminated = truncated = False
    early = False
    t_done = 0
    for t in range(PROBE_WINDOW):
        if terminated or truncated:
            early = True
            break
        action = controller.act(np.asarray(obs, dtype=np.float64))
        obs, _r, terminated, truncated, info = env.step(action)
        o = np.asarray(obs, dtype=np.float64)
        frames.append(o[:12].copy())
        frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
        trace[:, t] = (float(frame.lateral_error), float(env.state.vx), float(env.state.yaw_rate),
                       float(o[4]) * 15.0, float(o[3]) * 15.0, float(action[0]))
        t_done = t + 1
    if t_done < PROBE_WINDOW:  # pad early-terminated episodes
        trace[:, t_done:] = trace[:, t_done - 1: t_done]
        while len(frames) < PROBE_WINDOW:
            frames.append(frames[-1].copy())
    return mu, np.stack(frames), trace, early


def run_tradeoff_condition(task: dict[str, Any]) -> dict[str, Any]:
    """Worker: one protocol point x n_episodes on the probe env (no reveal in
    window). Returns R^2s, constraint aggregates and per-episode rows."""
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv

    mod_b, _c, _f, _k, design, _v, _spec = get_family()
    p = ProbeProtocol(**task["protocol"])
    cond_index = int(task["cond_index"])
    n_episodes = int(task["episodes"])
    pulse_end = PULSE_START + p.length_steps
    baseline = task.get("baseline_traces")  # (n_eps, 6, T) or None (= own baseline)

    env = AutoDriftEnv(build_env_config(mod_b.probe_env_config(design)))
    frames_eps: list[np.ndarray] = []
    traces_eps: list[np.ndarray] = []
    metrics_eps: list[dict[str, float]] = []
    mus: list[float] = []
    rows: list[dict[str, Any]] = []
    early_terms = 0
    try:
        for episode in range(n_episodes):
            seed = DP_SEED * 100 + episode  # shared across points -> paired design
            mu, frames, trace, early = rollout_probe_episode(env, mod_b, design, p, seed)
            mus.append(mu)
            early_terms += 1 if early else 0
            base = baseline[episode] if baseline is not None else trace
            metrics = episode_constraint_metrics(trace, base, pulse_end)
            metrics_eps.append(metrics)
            frames_eps.append(frames)
            traces_eps.append(trace)
            rows.append({"stage": "tradeoff", "condition": p.name, "role": p.role,
                         "cond_index": cond_index, "episode": episode, "seed": seed,
                         "mu": round(mu, 4), "early_terminated": early,
                         **{key: round(val, 4) for key, val in metrics.items()}})
    finally:
        env.close()

    y = np.asarray(mus)
    hist = np.stack([f[::4].reshape(-1) for f in frames_eps])
    r2_hist, _ = mod_b.episode_ridge_r2(hist, y)

    def frame_r2(idx: int) -> float:
        r2, _ = mod_b.episode_ridge_r2(np.stack([f[idx] for f in frames_eps]), y)
        return float(r2)

    leak_frames: dict[str, int] = {"anchor_pre_pulse_f10": 10, f"in_pulse_last_f{pulse_end - 1}": pulse_end - 1}
    adjudicated: list[str] = []
    for lag in POST_LAGS:
        idx = pulse_end - 1 + lag
        if idx <= PROBE_WINDOW - 1:
            key = f"post_lag{lag}_f{idx}"
            leak_frames[key] = idx
            adjudicated.append(key)
    if LEGACY_FINAL_FRAME >= pulse_end + 4:
        leak_frames[f"legacy_window_end_f{LEGACY_FINAL_FRAME}"] = LEGACY_FINAL_FRAME
        adjudicated.append(f"legacy_window_end_f{LEGACY_FINAL_FRAME}")
    leak_frames[f"window_end_f{PROBE_WINDOW - 1}"] = PROBE_WINDOW - 1
    adjudicated.append(f"window_end_f{PROBE_WINDOW - 1}")
    leak_curve = {key: round(frame_r2(idx), 4) for key, idx in leak_frames.items()}
    leak_adj = max(leak_curve[key] for key in adjudicated)

    agg = {key: {"max": round(float(np.max([m[key] for m in metrics_eps])), 4),
                 "mean": round(float(np.mean([m[key] for m in metrics_eps])), 4)}
           for key in metrics_eps[0]}
    pass_rates = {f"level{lv['level']}": round(float(np.mean(
        [1.0 if constraint_pass(m, lv) else 0.0 for m in metrics_eps])), 4) for lv in RELAX_LADDER}
    out = {
        "protocol": asdict(p), "cond_index": cond_index, "episodes": n_episodes,
        "early_terminated_episodes": early_terms,
        "mu_range": [round(float(y.min()), 3), round(float(y.max()), 3)],
        "r2_history_window": round(float(r2_hist), 4),
        "r2_single_frame_curve": leak_curve,
        "r2_post_probe_single_frame_adjudicated": round(float(leak_adj), 4),
        "adjudicated_leak_frames": adjudicated,
        "constraints": agg,
        "constraint_pass_rate": pass_rates,
        "rows": rows,
    }
    if task.get("return_traces"):
        out["traces"] = np.stack(traces_eps)
    return out


# -------------------------------------------------------------- teacher worker


def rollout_teacher_episode(env, mod_b, design, v_mu: float, p: ProbeProtocol, seed: int,
                            max_trace_steps: int | None = None):
    """One closed-loop teacher episode. Returns (teacher, trace (6,T), info-dict).
    max_trace_steps truncates the ROLLOUT (paired-baseline arm only needs the
    excitation + settle prefix)."""
    teacher = ProbeTeacher(mod_b, design, v_mu, p)
    obs, info = env.reset(seed=seed)
    teacher.reset()
    cols: list[tuple[float, ...]] = []
    episode_return = 0.0
    terminated = truncated = False
    while not (terminated or truncated):
        if max_trace_steps is not None and len(cols) >= max_trace_steps:
            break
        o = np.asarray(obs, dtype=np.float64)
        action = teacher.act(o)
        obs, r, terminated, truncated, info = env.step(action)
        episode_return += float(r)
        o2 = np.asarray(obs, dtype=np.float64)
        frame = env.track.frame(env.state.x, env.state.y, env.state.psi)
        cols.append((float(frame.lateral_error), float(env.state.vx), float(env.state.yaw_rate),
                     float(o2[4]) * 15.0, float(o2[3]) * 15.0, float(action[0])))
    trace = np.asarray(cols, dtype=np.float64).T if cols else np.zeros((6, 0))
    done = terminated or truncated
    bucket = (mod_b.outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
              if done else "truncated_for_baseline")
    return teacher, trace, {"bucket": bucket, "return": episode_return, "steps": trace.shape[1]}


def run_teacher_chunk(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Worker: closed-loop teacher episodes (with paired-baseline constraint
    traces) on the B2K2 family. arm in {steer, brake_legacy}."""
    mod_b, _c, mod_f, knobs, design, variant, _spec = get_family()
    p = ProbeProtocol(**task["protocol"])
    base_p = ProbeProtocol(name=f"baseline_{p.name}", kind="none", amp=0.0, freq_hz=0.0,
                           length_steps=p.length_steps, role="control")
    pulse_end = PULSE_START + p.length_steps
    level = task["level"]
    pool = mod_f.EnvPool(mod_b, design, variant, knobs)
    rows: list[dict[str, Any]] = []
    try:
        for j in task["episode_indices"]:
            mu = float(np.random.default_rng([DP_SEED, 2, int(j)]).uniform(MU_LO, MU_HI))
            seed = DP_SEED * 10 + 700000 + int(j)
            env = pool.env_for(mu, seed)
            v_mu = variant.v_oracle_est(mu)
            # paired baseline: zero-amplitude teacher, same commit step, same env draw
            base_teacher, base_trace, _b = rollout_teacher_episode(
                env, mod_b, design, v_mu, base_p, seed, max_trace_steps=pulse_end + SETTLE_STEPS)
            teacher, trace, outcome = rollout_teacher_episode(env, mod_b, design, v_mu, p, seed)
            reveal = teacher.reveal_step
            base_reveal = base_teacher.reveal_step
            # constraints adjudicated on the excitation window + settle, clipped at
            # the first reveal of either arm (post-reveal avoidance is allowed to
            # exceed comfort) and at the baseline trace length
            window_end = min(trace.shape[1], base_trace.shape[1], pulse_end + SETTLE_STEPS,
                             reveal if reveal is not None else 10 ** 9,
                             base_reveal if base_reveal is not None else 10 ** 9)
            if window_end > PULSE_START + 1:
                metrics = episode_constraint_metrics(trace[:, :window_end], base_trace,
                                                     pulse_end, window_end)
            else:
                metrics = {key: float("nan") for key in METRIC_KEYS}
            finite = math.isfinite(metrics["lat_dev_peak_m"])
            ok = constraint_pass(metrics, level) if finite else False
            ok0 = constraint_pass(metrics, RELAX_LADDER[0]) if finite else False
            rows.append({
                "stage": "teacher", "arm": task["arm"], "condition": p.name, "episode": int(j),
                "seed": seed, "mu": round(mu, 4), "outcome_bucket": outcome["bucket"],
                "success": outcome["bucket"] == "success_obstacle_pass", "steps": outcome["steps"],
                "return": round(outcome["return"], 2),
                "reveal_step": -1 if reveal is None else int(reveal),
                "speed_at_reveal": (round(float(teacher.speed_at_reveal), 3)
                                    if math.isfinite(teacher.speed_at_reveal) else None),
                "commit_step": pulse_end,
                "constraint_window_end": int(window_end),
                "constraint_pass_selected_level": ok,
                "constraint_pass_level0": ok0,
                **{key: (round(val, 4) if math.isfinite(val) else None) for key, val in metrics.items()},
            })
    finally:
        pool.close()
    return rows


def teacher_summary(rows: list[dict[str, Any]], mod_f) -> dict[str, Any]:
    revealed = [r for r in rows if r["reveal_step"] >= 0 and r["speed_at_reveal"] is not None]
    rho = (mod_f.spearman_tie_corrected([r["speed_at_reveal"] for r in revealed],
                                        [r["mu"] for r in revealed])
           if len(revealed) >= 3 else float("nan"))
    finite = [r for r in rows if r["lat_dev_peak_m"] is not None]
    summary = {
        "episodes": len(rows),
        "revealed": len(revealed),
        "reveal_coverage": round(len(revealed) / max(len(rows), 1), 4),
        "success_rate": round(float(np.mean([1.0 if r["success"] else 0.0 for r in rows])), 4),
        "spearman_speed_at_reveal_vs_mu": round(float(rho), 4) if math.isfinite(rho) else None,
        "constraint_pass_rate_selected_level": round(float(np.mean(
            [1.0 if r["constraint_pass_selected_level"] else 0.0 for r in rows])), 4),
        "constraint_pass_rate_level0": round(float(np.mean(
            [1.0 if r["constraint_pass_level0"] else 0.0 for r in rows])), 4),
        "reveal_before_commit_episodes": int(sum(1 for r in rows if 0 <= r["reveal_step"] < r["commit_step"])),
    }
    for key in ("lat_dev_peak_m", "ay_peak_mps2", "yaw_peak_radps", "ax_peak_mps2",
                "dvx_pulse_peak_mps", "dvx_post_mps"):
        vals = [r[key] for r in finite]
        summary[f"{key}_max"] = round(float(np.max(vals)), 4) if vals else None
        summary[f"{key}_mean"] = round(float(np.mean(vals)), 4) if vals else None
    return summary


# ------------------------------------------------------------------ selection


def select_protocol(conditions: list[dict[str, Any]], within_window: dict[str, bool]) -> dict[str, Any]:
    """Pre-registered ladder walk. Returns the selection record incl. binding
    constraints at every level below the one finally used."""

    def eligible(cond: dict[str, Any], lv: dict[str, Any]) -> bool:
        p = cond["protocol"]
        role_ok = p["role"] == "candidate" or (lv["allow_diag_amp"] and p["role"] == "amp_diagnostic")
        return (role_ok and within_window[p["name"]]
                and cond["constraint_pass_rate"][f"level{lv['level']}"] >= 1.0 - 1e-12)

    def violated(cond: dict[str, Any], lv: dict[str, Any]) -> list[str]:
        out = []
        c = cond["constraints"]
        if c["lat_dev_peak_m"]["max"] > lv["lat_m"]:
            out.append(f"C1 lane (peak {c['lat_dev_peak_m']['max']} > {lv['lat_m']} m)")
        if c["ay_peak_mps2"]["max"] > lv["ay_mps2"]:
            out.append(f"C2 ay (peak {c['ay_peak_mps2']['max']} > {lv['ay_mps2']} m/s^2)")
        if c["yaw_peak_radps"]["max"] > lv["yaw_radps"]:
            out.append(f"C3 yaw (peak {c['yaw_peak_radps']['max']} > {lv['yaw_radps']} rad/s)")
        if cond["protocol"]["role"] == "amp_diagnostic":
            out.append(f"C4 amplitude ({cond['protocol']['amp']} > {AMP_CAP})")
        return out

    ladder_log: list[dict[str, Any]] = []
    chosen = None
    for lv in RELAX_LADDER:
        pool = [c for c in conditions if eligible(c, lv)]
        passing = [c for c in pool
                   if c["r2_history_window"] >= R2_HISTORY_MIN
                   and c["r2_post_probe_single_frame_adjudicated"] <= R2_LEAK_MAX]
        # pre-registered: shortest excitation among acceptance-passing eligible points
        best = (min(passing, key=lambda c: (c["protocol"]["length_steps"], -c["r2_history_window"]))
                if passing else None)
        best_r2 = max(pool, key=lambda c: c["r2_history_window"]) if pool else None
        # binding analysis: highest-R^2 measurable points blocked at this level
        blocked = [c for c in conditions
                   if (c["protocol"]["role"] in ("candidate", "amp_diagnostic"))
                   and within_window[c["protocol"]["name"]]
                   and c["r2_history_window"] >= R2_HISTORY_MIN and not eligible(c, lv)]
        blocked.sort(key=lambda c: -c["r2_history_window"])
        entry = {
            "level": lv["level"], "thresholds": {k: lv[k] for k in ("lat_m", "ay_mps2", "yaw_radps", "allow_diag_amp")},
            "eligible_points": [c["protocol"]["name"] for c in pool],
            "eligible_passing_both_r2_bars": [c["protocol"]["name"] for c in passing],
            "best_eligible_by_r2": None if best_r2 is None else {
                "name": best_r2["protocol"]["name"],
                "r2_history_window": best_r2["r2_history_window"],
                "r2_post_probe_single_frame_adjudicated": best_r2["r2_post_probe_single_frame_adjudicated"],
            },
            "selected_if_this_level": None if best is None else {
                "name": best["protocol"]["name"],
                "r2_history_window": best["r2_history_window"],
                "r2_post_probe_single_frame_adjudicated": best["r2_post_probe_single_frame_adjudicated"],
            },
            "passes_acceptance": bool(best is not None),
            "binding_constraints_blocking_r2_geq_0.9": [
                {"name": c["protocol"]["name"], "r2_history_window": c["r2_history_window"],
                 "violates": violated(c, lv)} for c in blocked[:4]
            ],
        }
        ladder_log.append(entry)
        if best is not None and chosen is None:
            chosen = {"level": lv["level"], "condition": best}
            break
    return {"ladder_log": ladder_log, "chosen": chosen}


# ----------------------------------------------------------------------- misc


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


# ----------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="pipeline smoke (NOT the protocol run)")
    parser.add_argument("--episodes", type=int, default=160, help="episodes per protocol point")
    parser.add_argument("--teacher-episodes", type=int, default=96)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    mode = "quick_pipeline_check" if args.quick else "preregistered_protocol_run"
    if args.quick:
        args.episodes, args.teacher_episodes, args.workers = 30, 16, 8

    started = time.time()
    out_dir = RUN_DIR / ("smoke" if args.quick else "full")
    out_dir.mkdir(parents=True, exist_ok=True)

    from autodrift.artifacts import utc_timestamp, write_csv_rows

    mod_b, _mc, mod_f, knobs, design, variant, spec = load_family()
    reveal_floor_step = earliest_reveal_step(variant, knobs)
    commit_cap = reveal_floor_step  # commit step (12 + L) must be <= earliest reveal step
    protocols = protocol_grid()
    within_window = {p.name: (PULSE_START + p.length_steps) <= commit_cap for p in protocols}

    prereg = {
        "protocol": "feasibility_audit_selfid_deployable_probe_preregistration",
        "written_at_utc": utc_timestamp(),
        "written_before_any_measurement": True,
        "mode": mode,
        "criteria": PREREGISTERED,
        "c5_window_bound": {"earliest_reveal_step_at_v0": reveal_floor_step,
                            "commit_step_cap": commit_cap,
                            "within_window_by_point": within_window},
        "protocol_grid": [asdict(p) for p in protocols],
        "panel": {"episodes_per_point": args.episodes, "teacher_episodes": args.teacher_episodes},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if not args.quick:
        PREREG_JSON.write_text(json.dumps(to_jsonable(prereg), indent=2), encoding="utf-8")
        (out_dir / "preregistration.json").write_text(json.dumps(to_jsonable(prereg), indent=2), encoding="utf-8")
        print(f"[0/4] pre-registration written -> {PREREG_JSON}")
    else:
        print("[0/4] quick pipeline check: pre-registration NOT (re)written")
    n_candidates = sum(1 for p in protocols if p.role == "candidate")
    print(f"      grid: {len(protocols)} points ({n_candidates} deployable candidates), "
          f"commit-step cap {commit_cap} (earliest reveal at v0)")

    # [1] trade-off sweep ----------------------------------------------------
    # the no_probe control runs FIRST: its per-episode traces are the seed-
    # matched paired baseline for every other point (pre-registered rule)
    base_index = next(i for i, p in enumerate(protocols) if p.name == "no_probe")
    print(f"[1/4] trade-off sweep: {len(protocols)} points x {args.episodes} episodes "
          f"({args.workers} workers); paired baseline = no_probe")
    base_res = run_tradeoff_condition({"protocol": asdict(protocols[base_index]),
                                       "cond_index": base_index, "episodes": args.episodes,
                                       "return_traces": True})
    baseline_traces = base_res.pop("traces")
    tasks = [{"protocol": asdict(p), "cond_index": i, "episodes": args.episodes,
              "baseline_traces": baseline_traces}
             for i, p in enumerate(protocols) if i != base_index]
    conditions: list[dict[str, Any]] = [base_res]
    all_rows: list[dict[str, Any]] = list(base_res.pop("rows"))

    def report(res: dict[str, Any]) -> None:
        p = res["protocol"]
        print(f"      {p['name']:<24} R2_hist={res['r2_history_window']:>7.3f} "
              f"leak={res['r2_post_probe_single_frame_adjudicated']:>7.3f} "
              f"lat={res['constraints']['lat_dev_peak_m']['max']:.3f} "
              f"ay={res['constraints']['ay_peak_mps2']['max']:.2f} "
              f"yaw={res['constraints']['yaw_peak_radps']['max']:.3f} "
              f"dvx={res['constraints']['dvx_post_mps']['max']:.3f} "
              f"passL0={res['constraint_pass_rate']['level0']:.2f}")

    report(base_res)
    with ProcessPoolExecutor(max_workers=args.workers) as pool_exec:
        for res in pool_exec.map(run_tradeoff_condition, tasks):
            all_rows.extend(res.pop("rows"))
            conditions.append(res)
            report(res)
    conditions.sort(key=lambda c: c["cond_index"])

    # [2] pre-registered selection (ladder walk) ------------------------------
    print("[2/4] selection (pre-registered ladder walk)")
    selection = select_protocol(conditions, within_window)
    chosen = selection["chosen"]
    if chosen is None:
        print("      NO protocol point passes acceptance at any ladder level")
        sel_protocol = None
        sel_level = None
    else:
        sel_level = next(lv for lv in RELAX_LADDER if lv["level"] == chosen["level"])
        sel_protocol = ProbeProtocol(**chosen["condition"]["protocol"])
        print(f"      selected {sel_protocol.name} at ladder level {chosen['level']} "
              f"(R2_hist={chosen['condition']['r2_history_window']}, "
              f"leak={chosen['condition']['r2_post_probe_single_frame_adjudicated']})")

    # [3] teacher closed loop (selected protocol + legacy brake contrast) -----
    teacher_rows: list[dict[str, Any]] = []
    teacher_block: dict[str, Any] = {"evaluated": False}
    if sel_protocol is not None:
        print(f"[3/4] teacher closed loop: {args.teacher_episodes} episodes x 2 arms")
        brake = next(p for p in protocols if p.name == "brake_legacy")
        chunks = np.array_split(np.arange(args.teacher_episodes), max(args.workers, 1))
        t_tasks = []
        for arm, proto in (("steer", sel_protocol), ("brake_legacy", brake)):
            for chunk in chunks:
                if len(chunk):
                    t_tasks.append({"arm": arm, "protocol": asdict(proto),
                                    "episode_indices": [int(j) for j in chunk],
                                    "level": {k: sel_level[k] for k in ("lat_m", "ay_mps2", "yaw_radps")}})
        with ProcessPoolExecutor(max_workers=args.workers) as pool_exec:
            for rows in pool_exec.map(run_teacher_chunk, t_tasks):
                teacher_rows.extend(rows)
        steer_rows = [r for r in teacher_rows if r["arm"] == "steer"]
        brake_rows = [r for r in teacher_rows if r["arm"] == "brake_legacy"]
        steer_sum = teacher_summary(steer_rows, mod_f)
        brake_sum = teacher_summary(brake_rows, mod_f)
        t_pass = bool(steer_sum["success_rate"] >= TEACHER_SUCCESS_MIN
                      and (steer_sum["spearman_speed_at_reveal_vs_mu"] or -1.0) >= TEACHER_SPEARMAN_MIN
                      and steer_sum["constraint_pass_rate_selected_level"] >= 1.0 - 1e-12)
        teacher_block = {
            "evaluated": True,
            "eval_episodes": args.teacher_episodes,
            "selected_protocol": asdict(sel_protocol),
            "commit_step": PULSE_START + sel_protocol.length_steps,
            "steer_teacher": steer_sum,
            "brake_legacy_teacher_contrast": brake_sum,
            "acceptance": {
                "success_geq_0.85": bool(steer_sum["success_rate"] >= TEACHER_SUCCESS_MIN),
                "spearman_geq_0.95": bool((steer_sum["spearman_speed_at_reveal_vs_mu"] or -1.0) >= TEACHER_SPEARMAN_MIN),
                "constraint_rate_eq_1.0": bool(steer_sum["constraint_pass_rate_selected_level"] >= 1.0 - 1e-12),
                "TEACHER_PASS": t_pass,
            },
        }
        print(f"      steer teacher: succ={steer_sum['success_rate']} "
              f"rho={steer_sum['spearman_speed_at_reveal_vs_mu']} "
              f"constraints={steer_sum['constraint_pass_rate_selected_level']} PASS={t_pass}")
        print(f"      brake teacher: succ={brake_sum['success_rate']} "
              f"rho={brake_sum['spearman_speed_at_reveal_vs_mu']} "
              f"dvx_post={brake_sum['dvx_post_mps_max']}")
    else:
        print("[3/4] teacher closed loop SKIPPED (no selected protocol)")

    # [4] summary --------------------------------------------------------------
    brake_cond = next(c for c in conditions if c["protocol"]["name"] == "brake_legacy")
    noprobe_cond = next(c for c in conditions if c["protocol"]["name"] == "no_probe")
    level0 = RELAX_LADDER[0]
    level0_pool = [c for c in conditions
                   if c["protocol"]["role"] == "candidate" and within_window[c["protocol"]["name"]]
                   and c["constraint_pass_rate"]["level0"] >= 1.0 - 1e-12]
    level0_best = (max(level0_pool, key=lambda c: c["r2_history_window"]) if level0_pool else None)

    protocol_pass = bool(chosen is not None and chosen["level"] == 0)
    acceptance = {
        "selection_found": bool(chosen is not None),
        "ladder_level_used": None if chosen is None else chosen["level"],
        "selected_point": None if chosen is None else chosen["condition"]["protocol"]["name"],
        "r2_history_window": None if chosen is None else chosen["condition"]["r2_history_window"],
        "r2_history_geq_0.9": bool(chosen is not None
                                   and chosen["condition"]["r2_history_window"] >= R2_HISTORY_MIN),
        "r2_post_probe_single_frame": None if chosen is None
        else chosen["condition"]["r2_post_probe_single_frame_adjudicated"],
        "r2_leak_leq_0.1": bool(chosen is not None
                                and chosen["condition"]["r2_post_probe_single_frame_adjudicated"] <= R2_LEAK_MAX),
        "constraints_all_episodes_at_level0": protocol_pass,
        "PROTOCOL_PASS_AT_LEVEL0": protocol_pass,
    }

    summary = {
        "protocol": "feasibility_audit_selfid_deployable_probe_tradeoff",
        "generated_by": "scripts/feasibility_audit/selfid_deployable_probe_protocol.py",
        "generated_at_utc": utc_timestamp(),
        "mode": mode,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": {"json": str(PREREG_JSON), "criteria": PREREGISTERED},
        "final_spec_digest": {
            "source": str(FINAL_SPEC_JSON),
            "generated_at_utc": spec.get("generated_at_utc"),
            "reveal_distance": knobs.reveal_distance, "jitter_d_m": knobs.jitter_d_m,
            "d_knots": list(knobs.d_knots), "v_oracle_knots": list(knobs.v_oracle_knots),
        },
        "c5_window_bound": {"earliest_reveal_step_at_v0": reveal_floor_step,
                            "commit_step_cap": commit_cap},
        "deployable_constraints_level0": {k: level0[k] for k in ("lat_m", "ay_mps2", "yaw_radps")},
        "amplitude_cap_fraction_max_steer": AMP_CAP,
        "panel": {"episodes_per_point": args.episodes, "window_steps": PROBE_WINDOW,
                  "teacher_episodes": args.teacher_episodes, "workers": args.workers,
                  "points_total": len(protocols), "points_candidates": n_candidates},
        "tradeoff_curve": [
            {**{k: c["protocol"][k] for k in ("name", "kind", "amp", "freq_hz", "length_steps", "role")},
             "duration_s": round(c["protocol"]["length_steps"] * DT, 2),
             "within_window": within_window[c["protocol"]["name"]],
             "r2_history_window": c["r2_history_window"],
             "r2_post_probe_single_frame_adjudicated": c["r2_post_probe_single_frame_adjudicated"],
             "r2_single_frame_curve": c["r2_single_frame_curve"],
             "lat_dev_peak_max_m": c["constraints"]["lat_dev_peak_m"]["max"],
             "ay_peak_max_mps2": c["constraints"]["ay_peak_mps2"]["max"],
             "yaw_peak_max_radps": c["constraints"]["yaw_peak_radps"]["max"],
             "ax_peak_max_mps2": c["constraints"]["ax_peak_mps2"]["max"],
             "dvx_pulse_peak_max_mps": c["constraints"]["dvx_pulse_peak_mps"]["max"],
             "dvx_post_max_mps": c["constraints"]["dvx_post_mps"]["max"],
             "steer_cmd_peak_max": c["constraints"]["steer_cmd_peak"]["max"],
             "abs_lat_dev_peak_max_m": c["constraints"]["abs_lat_dev_peak_m"]["max"],
             "abs_ay_peak_max_mps2": c["constraints"]["abs_ay_peak_mps2"]["max"],
             "abs_yaw_peak_max_radps": c["constraints"]["abs_yaw_peak_radps"]["max"],
             "constraint_pass_rate": c["constraint_pass_rate"],
             "early_terminated_episodes": c["early_terminated_episodes"]}
            for c in conditions
        ],
        "selection": selection,
        "level0_best_deployable": None if level0_best is None else {
            "name": level0_best["protocol"]["name"],
            "r2_history_window": level0_best["r2_history_window"],
            "r2_post_probe_single_frame_adjudicated": level0_best["r2_post_probe_single_frame_adjudicated"],
        },
        "acceptance_protocol": acceptance,
        "teacher": teacher_block,
        "brake_vs_steer_contrast": {
            "brake_legacy": {
                "r2_history_window": brake_cond["r2_history_window"],
                "r2_post_probe_single_frame_adjudicated": brake_cond["r2_post_probe_single_frame_adjudicated"],
                "dvx_post_max_mps": brake_cond["constraints"]["dvx_post_mps"]["max"],
                "ax_peak_max_mps2": brake_cond["constraints"]["ax_peak_mps2"]["max"],
                "final_spec_reference": {"r2_single_frame": 0.9409, "r2_history": 0.9999},
            },
            "no_probe": {
                "r2_history_window": noprobe_cond["r2_history_window"],
                "r2_post_probe_single_frame_adjudicated": noprobe_cond["r2_post_probe_single_frame_adjudicated"],
                "final_spec_reference": {"r2_history": -3.085},
            },
            "selected_steer": None if chosen is None else {
                "name": chosen["condition"]["protocol"]["name"],
                "r2_history_window": chosen["condition"]["r2_history_window"],
                "r2_post_probe_single_frame_adjudicated": chosen["condition"]["r2_post_probe_single_frame_adjudicated"],
                "dvx_post_max_mps": chosen["condition"]["constraints"]["dvx_post_mps"]["max"],
                "ax_peak_max_mps2": chosen["condition"]["constraints"]["ax_peak_mps2"]["max"],
            },
            "deployment_note": (
                "in production the two channels would FUSE (brake pre-fill style mu estimation is "
                "current industry practice); the transient steering channel is kept separate here "
                "because it is the clean carrier of HISTORY NECESSITY for the gate measurement."
            ),
        },
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {
            "run_dir": str(out_dir),
            "tradeoff_rows_csv": str(out_dir / "tradeoff_rows.csv"),
            "teacher_rows_csv": str(out_dir / "teacher_rows.csv"),
            "results_json": str(TRADEOFF_JSON if not args.quick else out_dir / "tradeoff.json"),
        },
    }
    write_csv_rows(out_dir / "tradeoff_rows.csv", all_rows)
    if teacher_rows:
        write_csv_rows(out_dir / "teacher_rows.csv", teacher_rows)
    target = TRADEOFF_JSON if not args.quick else out_dir / "tradeoff.json"
    target.write_text(json.dumps(to_jsonable(summary), indent=2), encoding="utf-8")
    print(f"[4/4] summary -> {target}")
    sel_name = "NONE" if chosen is None else chosen["condition"]["protocol"]["name"]
    t_verdict = (teacher_block.get("acceptance", {}).get("TEACHER_PASS")
                 if teacher_block.get("evaluated") else None)
    print(
        f"HEADLINE: protocol={sel_name} level={acceptance['ladder_level_used']} "
        f"R2_hist={acceptance['r2_history_window']} leak={acceptance['r2_post_probe_single_frame']} "
        f"PROTOCOL_PASS_L0={acceptance['PROTOCOL_PASS_AT_LEVEL0']} TEACHER_PASS={t_verdict} | "
        f"elapsed {time.time() - started:.0f}s"
    )


if __name__ == "__main__":
    main()
