"""Task-C: ADVERSARIAL audit of the Task-B commitment task design (B2 family).

Attacks measured here (each maps to a project failure mode):

  A1 current-frame substitution: does the CURRENT frame at commitment time leak
     mu (so a hidden-swap / wrong-history gate could be defeated by re-deriving
     mu from the present frame)? Quantified as ridge R^2 of (single frame -> mu)
     vs (history -> mu) under three behavior conditions, including a
     mid-acceleration "commit transition" condition.
  A2 reactive escape hatch: (a) independent numeric optimal-control bound
     (friction-circle point mass, brake/steer allocation sweep) on the claimed
     post-reveal irrecoverability cells; (b) in-env reactive-parameter sweep
     (brake_to / steer_cap / swerve_offset / pure_brake) on fast arrivals at
     low mu.
  A3 mu-agnostic counter-plan attack on the VoI number itself:
     (a) fine entry-speed sweep (hedge plans);
     (b) TUNED position-indexed ladders that exploit the reveal-silence
         shortcut (hazard not seen by distance s => near-theta levels ruled
         out; in B2 distance is perfectly mu-correlated, so silence IS mu
         information that requires zero self-identification).
     The augmented best-fixed plan re-prices VoI(success).
  A4 reward-hacking / alignment check: per-level return-vs-success ordering,
     best failing return vs succeeding returns, knife-edge (fractional
     success) cell census given the only seed noise is ~0.3 m initial pose.
  A5 gate-measurability stats: speed_at_reveal separability (adjacent-theta
     Cohen's d) for the oracle plans; forgeability of gate signature 1
     (Spearman(reveal speed, mu)) by the zero-self-ID ladder.

Reuses the Task-B machinery by importing
scripts/feasibility_audit/voi_commitment_task_design.py via importlib (no file
is modified). Pure CPU numpy, deterministic seeds, no policy training.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_adversarial_audit.py
    PYTHONPATH=src python scripts/feasibility_audit/voi_commitment_adversarial_audit.py --quick
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/voi_commitment_adversarial_audit.json"
RUN_DIR = REPO / "runs/feasibility_audit/voi_commitment_adversarial_audit"
TASK_B_JSON = REPO / "experiments/feasibility_audit/voi_commitment_task_design.json"

SEED_BASE = 20260613  # fresh, disjoint from Task B's 20260612 streams

CLAIM_BOUNDARY = (
    "Feasibility-audit ADVERSARIAL task-design review only: scripted mu-agnostic counter-plans, "
    "leakage probes and numeric physics bounds are run against the Task-B B2 commitment family. "
    "No driver-performance, repair-success, robustness, validation, ranking, promotion, "
    "high-fidelity, paper, or self-ID capability claim is made."
)


def load_task_b_module():
    import sys

    spec = importlib.util.spec_from_file_location("voi_commitment_task_design", TASK_B_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # required for dataclass __module__ resolution
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------- A3: ladders


class TunedLadderController:
    """Position-indexed ladder with custom breaks; freezes its speed target at
    reveal. Strictly mu-agnostic: uses only integrated observed vx (distance)
    and the obstacle-visible flag. Wraps the Task-B CommitmentController."""

    def __init__(self, mod, plan, design, breaks: list[tuple[float, float]], post_reveal_brake_to: float | None = None):
        self.inner = mod.CommitmentController(plan, design)
        self.inner.ladder_breaks = list(breaks)
        self.post_reveal_brake_to = post_reveal_brake_to
        self._frozen: float | None = None

    def reset(self) -> None:
        self.inner.reset()
        self._frozen = None

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def act(self, obs):
        inner = self.inner
        if inner.reveal_step is not None and self._frozen is None:
            self._frozen = inner._ladder_target()
        target = self._frozen if self._frozen is not None else inner._ladder_target()
        # frozen-dataclass override: post-reveal hold speed follows the ladder
        object.__setattr__(inner.plan, "v_entry", float(target))
        if inner.reveal_step is not None and self.post_reveal_brake_to is not None:
            object.__setattr__(inner.plan, "brake_to", float(self.post_reveal_brake_to))
        return inner.act(obs)


def adversarial_controllers(mod, design) -> list[tuple[str, str, Any]]:
    """(name, group, controller) for every adversarial mu-agnostic plan."""
    out: list[tuple[str, str, Any]] = []
    P = mod.PlanSpec

    # (a) fine entry-speed hedge sweep
    for v in np.arange(4.5, 14.01, 0.5):
        plan = P(name=f"adv_swerve_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        out.append((plan.name, "fine_sweep", mod.CommitmentController(plan, design)))

    # (b) tuned reveal-silence ladders (zero self-ID; position-indexed only)
    ladders: dict[str, tuple[list[tuple[float, float]], float | None]] = {
        # exploit: theta1 tolerates 7.5 m/s arrival; silence past 13/27/38 m rules
        # out theta1/2/3 (B2 reveal distance 12 m, hazards at 24/38/49/62 m)
        "adv_ladder_75_oracle": ([(0.0, 7.5), (27.0, 10.0), (38.0, 13.0)], None),
        "adv_ladder_75_aggressive": ([(0.0, 7.5), (13.0, 10.0), (27.0, 13.0)], None),
        "adv_ladder_75_max": ([(0.0, 7.5), (27.0, 13.0)], None),
        "adv_ladder_65": ([(0.0, 6.5), (13.0, 8.5), (27.0, 11.0), (38.0, 13.5)], None),
        "adv_ladder_8_aggressive": ([(0.0, 8.0), (13.0, 10.5), (27.0, 13.5)], None),
        "adv_ladder_75_aggr_brake7": ([(0.0, 7.5), (13.0, 10.0), (27.0, 13.0)], 7.0),
        "adv_ladder_5_orig_repro": (
            [(max(level.d_lo - design.reveal_distance + 1.0, 0.0), level.entry_speed) for level in design.levels],
            None,
        ),
    }
    for name, (breaks, brake_to) in ladders.items():
        plan = P(name=name, v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
        out.append((name, "ladder", TunedLadderController(mod, plan, design, breaks, post_reveal_brake_to=brake_to)))
    return out


def reactive_escape_controllers(mod, design) -> list[tuple[str, Any]]:
    """Post-reveal reaction sweep on FAST commitments (escape-hatch search)."""
    P = mod.PlanSpec
    out: list[tuple[str, Any]] = []
    for v_entry in (10.0, 13.0):
        for brake_to, steer_cap, offset, gain in (
            (None, 0.85, 3.0, 3.0),
            (None, 1.0, 3.0, 4.5),
            (None, 1.0, 3.8, 3.0),
            (None, 1.0, 2.6, 6.0),
            (3.5, 1.0, 3.0, 4.5),
            (5.0, 0.85, 3.0, 3.0),
            (6.5, 1.0, 3.4, 3.0),
        ):
            name = f"esc_v{v_entry:g}_b{brake_to if brake_to is not None else 'none'}_c{steer_cap:g}_o{offset:g}_g{gain:g}"
            plan = P(name=name, v_entry=v_entry, brake_to=brake_to, swerve_offset=offset, swerve_gain=gain, steer_cap=steer_cap)
            out.append((name, mod.CommitmentController(plan, design)))
        name = f"esc_v{v_entry:g}_pure_brake"
        plan = P(name=name, v_entry=v_entry, brake_to=None, pure_brake=True)
        out.append((name, mod.CommitmentController(plan, design)))
    return out


# ------------------------------------------------- A2a: numeric physics bound


def best_post_reveal_lateral(mu: float, v0: float, distance: float, eta: float, dt: float = 0.002) -> dict[str, float]:
    """Friction-circle point mass: maximize lateral offset achieved by the time
    longitudinal position reaches `distance`, over (i) constant brake/steer
    allocation and (ii) full-brake-then-full-steer switching strategies.
    Returns the bound and whether a full stop fits before the obstacle."""
    a_max = eta * mu * 9.81

    def run(strategy) -> tuple[float, bool]:
        x = 0.0
        y = 0.0
        vx = v0
        vy = 0.0
        t = 0.0
        while x < distance and t < 8.0:
            speed = math.hypot(vx, vy)
            if speed < 0.05:
                return float("inf"), True  # stopped short of the obstacle
            frac_brake = strategy(t, speed)
            a_long = -frac_brake * a_max
            a_lat = math.sqrt(max(a_max**2 - a_long**2, 0.0))
            ux, uy = vx / speed, vy / speed
            ax = a_long * ux - a_lat * uy
            ay = a_long * uy + a_lat * ux
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt
        return y, False

    best = -1.0
    stopped = False
    for kappa in np.arange(0.0, 1.0001, 0.05):
        y_end, did_stop = run(lambda t, v, k=kappa: float(k))
        stopped = stopped or did_stop
        best = max(best, y_end if math.isfinite(y_end) else best)
    for v_switch in np.arange(1.0, v0, 0.5):
        y_end, did_stop = run(lambda t, v, vs=v_switch: 1.0 if v > vs else 0.0)
        stopped = stopped or did_stop
        best = max(best, y_end if math.isfinite(y_end) else best)
    aeb_stop = v0**2 / (2.0 * max(0.9 * mu * 9.81, 1e-6))
    return {
        "mu": mu,
        "arrival_speed_mps": v0,
        "reveal_distance_m": distance,
        "friction_fraction_eta": eta,
        "max_lateral_offset_m": round(best, 3),
        "full_stop_fits_before_obstacle": bool(stopped or aeb_stop <= distance - 0.3),
        "aeb_stop_distance_m": round(aeb_stop, 2),
    }


# ------------------------------------------------ A1: current-frame leak probe


def collect_leak_condition(mod, design, mode: str, n_episodes: int) -> dict[str, Any]:
    """Like Task-B's probe but fits (single current frame -> mu) alongside the
    full-history probe, to price the current-frame substitution channel."""
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv

    env = AutoDriftEnv(build_env_config(mod.probe_env_config(design)))
    v_entry = {"probe_pulses": 8.0, "no_probe": 8.0, "accel_commit": 11.5}[mode]
    plan = mod.PlanSpec(name=f"leak_{mode}", v_entry=v_entry, brake_to=None, probe_pulses=(mode == "probe_pulses"))
    window = mod.PROBE_WINDOW_STEPS
    hist, final_frame, final5, mid_frame, mus = [], [], [], [], []
    try:
        for episode in range(n_episodes):
            seed = SEED_BASE * 100 + {"probe_pulses": 0, "no_probe": 1, "accel_commit": 2}[mode] * 10000 + episode
            controller = mod.CommitmentController(plan, design)
            obs, info = env.reset(seed=seed)
            controller.reset()
            mus.append(float(info["mu"]))
            frames = []
            terminated = truncated = False
            for _t in range(window):
                if terminated or truncated:
                    break
                action = controller.act(np.asarray(obs, dtype=np.float64))
                obs, _r, terminated, truncated, info = env.step(action)
                frames.append(np.asarray(obs[: mod.PROBE_FRAME_CHANNELS], dtype=np.float64).copy())
            while len(frames) < window:
                frames.append(frames[-1].copy())
            stacked = np.stack(frames)
            hist.append(stacked[:: mod.PROBE_FRAME_STRIDE].reshape(-1))
            final_frame.append(stacked[-1])
            final5.append(stacked[-5:].reshape(-1))
            mid_frame.append(stacked[window // 2])
    finally:
        env.close()
    y = np.asarray(mus)
    out = {"mode": mode, "episodes": n_episodes, "v_entry": v_entry}
    for label, feats in (
        ("history_stride4", hist),
        ("current_frame_final", final_frame),
        ("current_frames_last5", final5),
        ("current_frame_mid", mid_frame),
    ):
        r2, alpha = mod.episode_ridge_r2(np.stack(feats), y)
        out[f"r2_{label}"] = round(float(r2), 4)
        out[f"alpha_{label}"] = alpha
    return out


# ------------------------------------------------------------------ analytics


def cell_stats(rows: list[dict[str, Any]], plan: str, level: int) -> dict[str, float]:
    sub = [r for r in rows if r["plan"] == plan and r["level_index"] == level]
    if not sub:
        return {}
    succ = np.array([1.0 if r["success"] else 0.0 for r in sub])
    ret = np.array([r["return"] for r in sub])
    spd = np.array([r["speed_at_reveal"] for r in sub if math.isfinite(r["speed_at_reveal"])])
    return {
        "n": len(sub),
        "success": float(succ.mean()),
        "return_mean": float(ret.mean()),
        "speed_at_reveal_mean": float(spd.mean()) if len(spd) else float("nan"),
        "speed_at_reveal_std": float(spd.std()) if len(spd) else float("nan"),
    }


def spearman(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    if ra.std() < 1e-12 or rb.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


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
    parser.add_argument("--seeds", type=int, default=16, help="seeds per level (matches Task B final panel)")
    parser.add_argument("--leak-episodes", type=int, default=160)
    parser.add_argument("--escape-seeds", type=int, default=8)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if args.quick:
        args.seeds, args.leak_episodes, args.escape_seeds = 4, 40, 2

    started = time.time()
    mod = load_task_b_module()
    design = next(d for d in mod.candidate_designs() if d.design_id == "B2_mu_correlated_hazard_tight")
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    from autodrift.artifacts import utc_timestamp, write_csv_rows
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv

    episode_rows: list[dict[str, Any]] = []

    def run_panel(named_controllers: list[tuple[str, str, Any]], n_seeds: int, levels=None) -> None:
        levels = levels if levels is not None else list(range(len(design.levels)))
        for level_index in levels:
            level = design.levels[level_index]
            env = AutoDriftEnv(build_env_config(mod.level_env_config(design, level)))
            try:
                for name, group, controller in named_controllers:
                    for seed in mod.seeds_for_level(level_index, n_seeds):
                        row = mod.rollout(env, controller, seed)
                        row.update(
                            {
                                "design_id": design.design_id,
                                "level_index": level_index,
                                "level_mu": level.mu,
                                "plan": name,
                                "plan_group": group,
                            }
                        )
                        episode_rows.append(row)
            finally:
                env.close()

    # ---- [1/5] original 13 plans (reproduction) + adversarial plans, full panel
    print("[1/5] full-panel rollouts: original plans (reproduction) + adversarial counter-plans")
    original = [(p.name, "original", mod.CommitmentController(p, design)) for p in mod.plan_family(design)]
    adversarial = adversarial_controllers(mod, design)
    run_panel(original + adversarial, args.seeds)

    # reproduction check against the Task-B JSON success matrix
    task_b = json.loads(TASK_B_JSON.read_text()) if TASK_B_JSON.exists() else None
    repro = {"checked": False}
    if task_b is not None and args.seeds == 16:
        ref = task_b["final_design"]["success_matrix_measured"]
        mismatches = []
        for plan_name, per_mu in ref.items():
            for level_index, level in enumerate(design.levels):
                got = cell_stats(episode_rows, plan_name, level_index).get("success")
                want = per_mu[f"mu_{level.mu:g}"]
                if got is None or abs(round(got, 3) - want) > 1e-9:  # Task-B JSON stores 3-decimal rounding
                    mismatches.append({"plan": plan_name, "mu": level.mu, "task_b": want, "rerun": got})
        repro = {"checked": True, "cells": len(ref) * 4, "mismatches": mismatches}
        print(f"  reproduction: {len(ref) * 4} cells, {len(mismatches)} mismatches")

    # ---- VoI re-pricing with the augmented plan family
    plan_names = sorted({r["plan"] for r in episode_rows})
    n_levels = len(design.levels)
    succ = np.full((len(plan_names), n_levels, args.seeds), np.nan)
    for i, name in enumerate(plan_names):
        for j in range(n_levels):
            vals = [1.0 if r["success"] else 0.0 for r in episode_rows if r["plan"] == name and r["level_index"] == j]
            succ[i, j, : len(vals)] = vals
    assert not np.isnan(succ).any()
    voi_aug = mod.voi_from_matrix(succ)
    original_names = {p.name for p in mod.plan_family(design)}
    orig_idx = [i for i, n in enumerate(plan_names) if n in original_names]
    voi_orig = mod.voi_from_matrix(succ[orig_idx])
    plan_means = succ.mean(axis=(1, 2))
    top = np.argsort(plan_means)[::-1][:8]
    top_fixed = [
        {
            "plan": plan_names[i],
            "mean_success": round(float(plan_means[i]), 4),
            "per_level": [round(float(succ[i, j].mean()), 4) for j in range(n_levels)],
        }
        for i in top
    ]
    print(
        f"  VoI(success) original family: {voi_orig['voi_in_sample']:.4f} (val {voi_orig['voi_split_validated']:.4f}) | "
        f"augmented adversarial family: {voi_aug['voi_in_sample']:.4f} (val {voi_aug['voi_split_validated']:.4f})"
    )
    print(f"  best fixed now: {plan_names[int(voi_aug['best_fixed_plan_index'])]} mean={plan_means.max():.4f}")

    # ---- [2/5] reactive escape sweep at the irrecoverability cells
    print("[2/5] reactive escape sweep (fast commitments at theta1/theta2)")
    escape = [(name, "escape", c) for name, c in reactive_escape_controllers(mod, design)]
    run_panel(escape, args.escape_seeds, levels=[0, 1])
    esc_rows = [r for r in episode_rows if r.get("plan_group") == "escape"]
    esc_summary = {}
    for level_index in (0, 1):
        sub = [r for r in esc_rows if r["level_index"] == level_index]
        n_succ = sum(1 for r in sub if r["success"])
        by_plan = {}
        for r in sub:
            by_plan.setdefault(r["plan"], []).append(1.0 if r["success"] else 0.0)
        esc_summary[f"level{level_index}_mu{design.levels[level_index].mu:g}"] = {
            "episodes": len(sub),
            "successes": n_succ,
            "best_variant": max(((np.mean(v), k) for k, v in by_plan.items()))[1],
            "best_variant_success": round(float(max(np.mean(v) for v in by_plan.values())), 3),
            "mean_speed_at_reveal": round(float(np.nanmean([r["speed_at_reveal"] for r in sub])), 2),
        }
        print(f"  level{level_index}: {n_succ}/{len(sub)} reactive successes")

    # ---- [3/5] numeric irrecoverability bounds (independent of designer's calc)
    print("[3/5] numeric friction-circle optimal-control bounds")
    required = design.required_offset()
    physics_cells = []
    for mu, v0 in ((0.30, 9.9), (0.30, 7.5), (0.30, 11.0), (0.55, 12.8), (0.85, 13.0), (1.15, 13.0)):
        for eta in (0.85, 1.0):
            bound = best_post_reveal_lateral(mu, v0, design.reveal_distance, eta)
            bound["required_offset_m"] = required
            bound["pass_feasible"] = bool(bound["max_lateral_offset_m"] >= required)
            physics_cells.append(bound)
    for cell in physics_cells:
        if cell["friction_fraction_eta"] == 1.0:
            print(
                f"  mu={cell['mu']:.2f} v={cell['arrival_speed_mps']:.1f} eta=1.0: "
                f"max_lat={cell['max_lateral_offset_m']:.2f} m (need {required:.2f}) "
                f"pass_feasible={cell['pass_feasible']} stop_fits={cell['full_stop_fits_before_obstacle']}"
            )

    # ---- [4/5] current-frame substitution probe
    print("[4/5] current-frame leakage probe")
    leak = [collect_leak_condition(mod, design, mode, args.leak_episodes) for mode in ("probe_pulses", "no_probe", "accel_commit")]
    for entry in leak:
        print(
            f"  {entry['mode']:<13} R2 hist={entry['r2_history_stride4']:.3f} "
            f"final_frame={entry['r2_current_frame_final']:.3f} last5={entry['r2_current_frames_last5']:.3f} "
            f"mid={entry['r2_current_frame_mid']:.3f}"
        )

    # ---- [5/5] reward alignment + gate measurability
    print("[5/5] reward alignment and gate stats")
    panel_rows = [r for r in episode_rows if r.get("plan_group") in ("original", "fine_sweep", "ladder")]
    alignment = []
    for level_index, level in enumerate(design.levels):
        sub = [r for r in panel_rows if r["level_index"] == level_index]
        succ_rows = [r for r in sub if r["success"]]
        fail_rows = [r for r in sub if not r["success"]]
        by_plan: dict[str, list[dict[str, Any]]] = {}
        for r in sub:
            by_plan.setdefault(r["plan"], []).append(r)
        means = [(k, float(np.mean([1.0 if x["success"] else 0.0 for x in v])), float(np.mean([x["return"] for x in v]))) for k, v in by_plan.items()]
        sp = spearman([m[2] for m in means], [m[1] for m in means])
        timeout_fail = [r for r in fail_rows if r["outcome_bucket"].startswith("max_steps") or r["termination_reason"] == ""]
        collision_fail = [r for r in fail_rows if "collision" in (r["termination_reason"] or "") or "collision" in r["outcome_bucket"]]
        alignment.append(
            {
                "level_mu": level.mu,
                "spearman_plan_return_vs_success": round(sp, 3),
                "best_failing_episode_return": round(max((r["return"] for r in fail_rows), default=float("nan")), 1),
                "best_failing_plan_mean_return": round(max((m[2] for m in means if m[1] < 0.5), default=float("nan")), 1),
                "oracle_plan_mean_return": round(max((m[2] for m in means if m[1] >= 0.95), default=float("nan")), 1),
                "median_successful_episode_return": round(float(np.median([r["return"] for r in succ_rows])) if succ_rows else float("nan"), 1),
                "max_timeout_failure_return": round(max((r["return"] for r in timeout_fail), default=float("nan")), 1),
                "max_collision_failure_return": round(max((r["return"] for r in collision_fail), default=float("nan")), 1),
                "failing_beats_oracle": bool(
                    max((m[2] for m in means if m[1] < 0.5), default=-1e9) > max((m[2] for m in means if m[1] >= 0.95), default=1e9)
                ),
            }
        )
    knife = {"fractional_cells": 0, "total_cells": 0, "examples": []}
    for name in plan_names:
        for j in range(n_levels):
            p = float(succ[plan_names.index(name), j].mean())
            knife["total_cells"] += 1
            if 1e-9 < p < 1 - 1e-9:
                knife["fractional_cells"] += 1
                if len(knife["examples"]) < 12:
                    knife["examples"].append({"plan": name, "mu": design.levels[j].mu, "success": round(p, 3)})

    oracle_plans = ["swerve_only_v5", "swerve_only_v7.5", "commit_v10", "swerve_only_v13"]
    gate_speed = []
    for j, plan in enumerate(oracle_plans):
        stats = cell_stats(episode_rows, plan, j)
        gate_speed.append({"level_mu": design.levels[j].mu, "oracle_plan": plan, **{k: round(v, 3) for k, v in stats.items()}})
    cohens_d = []
    for j in range(3):
        m1, s1 = gate_speed[j]["speed_at_reveal_mean"], gate_speed[j]["speed_at_reveal_std"]
        m2, s2 = gate_speed[j + 1]["speed_at_reveal_mean"], gate_speed[j + 1]["speed_at_reveal_std"]
        pooled = math.sqrt(max((s1**2 + s2**2) / 2.0, 1e-6))
        cohens_d.append(round(abs(m2 - m1) / pooled, 1))

    # ladder forgery of gate signature 1 (no self-ID, only position)
    best_ladder = max(
        (n for n in plan_names if n.startswith("adv_ladder")),
        key=lambda n: float(succ[plan_names.index(n)].mean()),
    )
    ladder_speeds = [cell_stats(episode_rows, best_ladder, j).get("speed_at_reveal_mean", float("nan")) for j in range(n_levels)]
    ladder_prep_energy = float(
        np.nanmean([r["prep_action_sq_mean"] for r in episode_rows if r["plan"] == best_ladder])
    )
    no_probe_prep_energy = float(
        np.nanmean([r["prep_action_sq_mean"] for r in episode_rows if r["plan"] == "swerve_only_v7.5"])
    )
    gate_forgery = {
        "best_ladder": best_ladder,
        "ladder_mean_success": round(float(succ[plan_names.index(best_ladder)].mean()), 4),
        "ladder_per_level_success": [round(float(succ[plan_names.index(best_ladder), j].mean()), 3) for j in range(n_levels)],
        "ladder_speed_at_reveal_per_level": [round(s, 2) for s in ladder_speeds],
        "ladder_spearman_revealspeed_vs_mu": round(spearman(ladder_speeds, [l.mu for l in design.levels]), 3),
        "ladder_prep_action_energy": round(ladder_prep_energy, 3),
        "steady_tracking_prep_action_energy": round(no_probe_prep_energy, 3),
        "task_b_gate3_bar": 0.72,
        "recomputed_gate3_bar_with_adversarial_family": round(
            float(voi_aug["best_fixed_split_validated"] + 0.5 * voi_aug["voi_split_validated"]), 4
        ),
    }

    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, episode_rows)
    payload = {
        "protocol": "feasibility_audit_voi_commitment_adversarial_audit",
        "generated_by": "scripts/feasibility_audit/voi_commitment_adversarial_audit.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "design_under_attack": "B2_mu_correlated_hazard_tight (experiments/feasibility_audit/voi_commitment_task_design.json)",
        "elapsed_s": round(time.time() - started, 1),
        "panel": {"seeds_per_level": args.seeds, "seed_formula": "same as Task B: 20260612*10 + level*1000 + k"},
        "reproduction_check": repro,
        "voi_repricing": {
            "original_family_voi_success_in_sample": round(float(voi_orig["voi_in_sample"]), 4),
            "original_family_voi_success_split_validated": round(float(voi_orig["voi_split_validated"]), 4),
            "augmented_family_voi_success_in_sample": round(float(voi_aug["voi_in_sample"]), 4),
            "augmented_family_voi_success_split_validated": round(float(voi_aug["voi_split_validated"]), 4),
            "augmented_best_fixed_plan": plan_names[int(voi_aug["best_fixed_plan_index"])],
            "augmented_best_fixed_mean_success": round(float(plan_means.max()), 4),
            "augmented_oracle_in_sample": round(float(voi_aug["oracle_in_sample"]), 4),
            "voi_target": 0.25,
            "still_meets_target_in_sample": bool(voi_aug["voi_in_sample"] >= 0.25),
            "still_meets_target_split_validated": bool(voi_aug["voi_split_validated"] >= 0.25),
            "top_fixed_plans": top_fixed,
            "note": (
                "augmented family adds fine entry-speed hedges and tuned reveal-silence ladders; "
                "ladders are mu-agnostic (position-indexed) and exploit the perfect mu<->hazard-distance "
                "correlation: silence past 13/27/38 m identifies theta with zero self-identification."
            ),
        },
        "reactive_escape": esc_summary,
        "physics_irrecoverability_bounds": {
            "required_lateral_offset_m": required,
            "method": (
                "friction-circle point mass, total accel eta*mu*g, optimal over constant "
                "brake/steer allocations and full-brake-then-full-steer switches, dt=0.002"
            ),
            "cells": physics_cells,
        },
        "current_frame_leak_probe": {
            "window_steps": mod.PROBE_WINDOW_STEPS,
            "conditions": leak,
            "interpretation_note": (
                "r2_current_frame_final is the wrong-history-gate substitution channel: if high, a policy "
                "can re-derive mu from the present frame and the gate cannot prove history dependence."
            ),
        },
        "reward_alignment": alignment,
        "knife_edge_census": knife,
        "gate_measurability": {
            "oracle_speed_at_reveal": gate_speed,
            "adjacent_theta_cohens_d": cohens_d,
            "signature_forgery": gate_forgery,
        },
        "artifacts": {"episode_rows_csv": str(rows_csv), "results_json": str(RESULTS_JSON)},
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {RESULTS_JSON}")
    print(f"episode rows -> {rows_csv} ({len(episode_rows)} rows)")
    print(
        f"HEADLINE: augmented VoI(success)={voi_aug['voi_in_sample']:.4f} "
        f"(val {voi_aug['voi_split_validated']:.4f}) vs original {voi_orig['voi_in_sample']:.4f}; "
        f"escape successes L0={esc_summary.get('level0_mu0.3', {}).get('successes')} | "
        f"leak final-frame R2: " + ", ".join(f"{e['mode']}={e['r2_current_frame_final']:.3f}" for e in leak)
    )


if __name__ == "__main__":
    main()
