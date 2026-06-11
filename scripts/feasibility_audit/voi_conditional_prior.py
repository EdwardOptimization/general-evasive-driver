"""Conditional VoI: is PRECISE mu knowledge still valuable GIVEN a coarse prior bin?

User proposition under test: side channels (road appearance / wipers / temperature)
only bound mu to a coarse range (literature precision ~ +/-0.2..0.3); precise
capability knowledge requires command->response self-identification. Formally:
    conditional VoI(bin) = E_{mu in bin}[per-mu oracle outcome]
                           - max_{single bin-aware plan} E_{mu in bin}[outcome]
on a CONTINUOUS-mu variant of the Task-B B2 commitment family
(scripts/feasibility_audit/voi_commitment_task_design.py): mu ~ U(bin), hazard
distance follows the monotone B2 mu<->d mapping (piecewise-linear interpolation
through (0.30,24),(0.55,38),(0.85,49),(1.15,62)), every mu point is an exact
build_env_config member (mu_range and distance_range degenerate at the point).

Bin-aware fixed-plan family (the "coarse prior is enough" adversary):
  - entry-speed commitment grid (0.5 m/s) x 2 steering variants,
  - reveal-silence ladders allowed to use the BIN + own driven distance
    (continuous version of the Task-C adversarial ladders),
  - robust-CEM plan directly optimizing the bin-average (reduced budget).
Per-mu oracle: best of the same structured candidates at that mu + local
entry-speed refinement + reduced-budget per-mu CEM when not yet at 1.0.

Split-seed protocol (as Task B): plan/oracle selection on selection seeds,
headline numbers re-evaluated on disjoint validation seeds.

Knob iteration (only if the +/-0.2 bin conditional VoI < 0.2): tighten deadline,
reveal distance, obstacle half-width, mu<->d slope -- each re-measured, all
iterations logged.

Pure CPU numpy, deterministic seeds, no training, new files only.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/voi_conditional_prior.py
    PYTHONPATH=src python scripts/feasibility_audit/voi_conditional_prior.py --quick
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TASK_B_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_task_design.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/voi_conditional_prior.json"
RUN_DIR = REPO / "runs/feasibility_audit/voi_conditional_prior"

SEED_BASE = 20260611  # fresh stream, disjoint from Task B (20260612) / Task C (20260613)
VOI_TARGET = 0.20

CLAIM_BOUNDARY = (
    "Feasibility-audit task-design measurement only: conditional VoI of precise mu given a "
    "coarse prior bin is measured with scripted bin-aware plans and a per-mu empirical oracle "
    "on a continuous-mu variant of the B2 commitment family. No driver-performance, "
    "repair-success, robustness, validation, ranking, promotion, paper, or self-ID "
    "*capability* claim is made."
)

# B2 anchors: mu <-> hazard distance and design-intended oracle entry speed
MU_KNOTS = (0.30, 0.55, 0.85, 1.15)
D_KNOTS = (24.0, 38.0, 49.0, 62.0)
V_ORACLE_KNOTS = (5.0, 7.5, 10.0, 13.0)
SLOPE_PIVOT_MU = 0.70

# coarse-prior bins (real-world side-channel precision tiers)
BINS = (
    ("full_pm0.45", 0.25, 1.15, "no-prior control (whole domain)"),
    ("wide_pm0.30", 0.40, 1.00, "side-channel precision +/-0.30"),
    ("medium_pm0.20", 0.45, 0.85, "side-channel precision +/-0.20"),
    ("narrow_pm0.10", 0.55, 0.75, "side-channel precision +/-0.10"),
)

V_GRID = tuple(round(4.5 + 0.5 * i, 1) for i in range(20))  # 4.5 .. 14.0
STEER_VARIANTS = (("A", 0.85, 3.0, 3.0), ("B", 1.0, 3.0, 4.5))  # (tag, cap, offset, gain)
CEM_CLIP = ((4.0, 14.5), (0.5, 1.0), (2.2, 4.2), (1.5, 6.0))  # v, cap, offset, gain


def interp_lin(x: float, xs: tuple[float, ...], ys: tuple[float, ...]) -> float:
    """Piecewise-linear with LINEAR extrapolation outside the knot range."""
    if x <= xs[0]:
        s = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return ys[0] + s * (x - xs[0])
    if x >= xs[-1]:
        s = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return ys[-1] + s * (x - xs[-1])
    return float(np.interp(x, xs, ys))


@dataclass(frozen=True)
class Variant:
    """Task-knob variant of the B2 family (knob iteration design freedom)."""

    variant_id: str
    max_steps: int = 285
    reveal_distance: float = 12.0
    obstacle_half_width: float = 1.25
    slope_scale: float = 1.0  # mu<->d slope multiplier around d(SLOPE_PIVOT_MU)
    note: str = ""

    def d_of_mu(self, mu: float) -> float:
        base = interp_lin(mu, MU_KNOTS, D_KNOTS)
        pivot = interp_lin(SLOPE_PIVOT_MU, MU_KNOTS, D_KNOTS)
        return max(pivot + self.slope_scale * (base - pivot), self.reveal_distance + 6.0)

    def mu_of_d(self, d: float) -> float:
        pivot = interp_lin(SLOPE_PIVOT_MU, MU_KNOTS, D_KNOTS)
        base = pivot + (d - pivot) / self.slope_scale
        return interp_lin(base, D_KNOTS, MU_KNOTS)

    def v_oracle_est(self, mu: float) -> float:
        return interp_lin(mu, MU_KNOTS, V_ORACLE_KNOTS)


BASE_VARIANT = Variant(variant_id="base_B2_continuous", note="B2 knobs unchanged, continuous mu")
KNOB_VARIANTS = (
    Variant(variant_id="K1_deadline265", max_steps=265, note="deadline 5.7 -> 5.3 s"),
    Variant(variant_id="K2_reveal10", reveal_distance=10.0, note="reveal 12 -> 10 m"),
    Variant(
        variant_id="K3_deadline265_reveal10",
        max_steps=265,
        reveal_distance=10.0,
        note="deadline 5.3 s + reveal 10 m",
    ),
    Variant(
        variant_id="K4_slope135_halfwidth145",
        slope_scale=1.35,
        obstacle_half_width=1.45,
        note="mu<->d slope x1.35 (pivot mu=0.70) + obstacle half-width 1.25 -> 1.45",
    ),
)


def load_task_b_module():
    spec = importlib.util.spec_from_file_location("voi_commitment_task_design", TASK_B_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def variant_design(mod, variant: Variant):
    b2 = next(d for d in mod.candidate_designs() if d.design_id == "B2_mu_correlated_hazard_tight")
    return dataclasses.replace(
        b2,
        design_id=f"B2_continuous::{variant.variant_id}",
        max_steps=variant.max_steps,
        reveal_distance=variant.reveal_distance,
        obstacle_half_width=variant.obstacle_half_width,
    )


def point_env_config(mod, design, variant: Variant, mu: float) -> dict[str, Any]:
    d = variant.d_of_mu(mu)
    level = mod.LevelSpec(mu=mu, d_lo=d, d_hi=d, entry_speed=variant.v_oracle_est(mu))
    return mod.level_env_config(design, level)


# ------------------------------------------------------------------- plan zoo


class TunedLadderController:
    """Reveal-silence ladder (continuous version of the Task-C adversarial ladder).
    Strictly bin-aware + position-indexed: uses ONLY the prior bin (through its
    break schedule) and the integrated own speed; freezes the target at reveal."""

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
        object.__setattr__(inner.plan, "v_entry", float(target))
        if inner.reveal_step is not None and self.post_reveal_brake_to is not None:
            object.__setattr__(inner.plan, "brake_to", float(self.post_reveal_brake_to))
        return inner.act(obs)


def ladder_breaks_for_bin(
    variant: Variant, lo: float, hi: float, delta: float, margin: float
) -> list[tuple[float, float]]:
    """Silence past driven distance p implies hazard distance > p + reveal, hence
    mu > mu_of_d(p + reveal + margin); target the (estimated) oracle speed of the
    implied mu lower bound, shifted by delta."""
    breaks: list[tuple[float, float]] = []
    d_hi = variant.d_of_mu(hi)
    p = 0.0
    last_v: float | None = None
    while p <= d_hi + 2.0:
        mu_imp = min(max(variant.mu_of_d(p + variant.reveal_distance + margin), lo), hi)
        v = float(np.clip(variant.v_oracle_est(mu_imp) + delta, 3.5, 14.5))
        v = round(v, 2)
        if last_v is None or abs(v - last_v) > 1e-9:
            breaks.append((p, v))
            last_v = v
        p += 2.0
    return breaks


@dataclass
class Candidate:
    name: str
    group: str  # grid | ladder | cem_robust | refine | cem_point
    build: Callable[[], Any]  # -> controller
    v_entry: float | None = None  # commitment speed if applicable (mechanism plots)


def plan_from_params(mod, name: str, params: np.ndarray):
    v, cap, off, gain = (float(np.clip(params[i], *CEM_CLIP[i])) for i in range(4))
    return mod.PlanSpec(name=name, v_entry=v, brake_to=None, swerve_offset=off, swerve_gain=gain, steer_cap=cap)


def grid_candidates(mod, design) -> list[Candidate]:
    out: list[Candidate] = []
    for v in V_GRID:
        for tag, cap, off, gain in STEER_VARIANTS:
            plan = mod.PlanSpec(
                name=f"grid_v{v:g}_{tag}", v_entry=float(v), brake_to=None,
                swerve_offset=off, swerve_gain=gain, steer_cap=cap,
            )
            out.append(
                Candidate(plan.name, "grid", (lambda p=plan: mod.CommitmentController(p, design)), v_entry=float(v))
            )
    return out


def ladder_candidates(mod, design, variant: Variant, lo: float, hi: float) -> list[Candidate]:
    out: list[Candidate] = []
    for delta in (-0.5, 0.0, 0.5, 1.0):
        for margin in (1.0, 3.0):
            breaks = ladder_breaks_for_bin(variant, lo, hi, delta, margin)
            name = f"ladder_d{delta:g}_m{margin:g}"
            plan = mod.PlanSpec(name=name, v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
            out.append(
                Candidate(
                    name, "ladder",
                    (lambda b=breaks, p=plan: TunedLadderController(mod, p, design, b)),
                )
            )
    breaks = ladder_breaks_for_bin(variant, lo, hi, 0.5, 1.0)
    brake_to = max(variant.v_oracle_est(lo) - 0.5, 3.5)
    name = "ladder_d0.5_m1_brake"
    plan = mod.PlanSpec(name=name, v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
    out.append(
        Candidate(
            name, "ladder",
            (lambda b=breaks, p=plan, bt=brake_to: TunedLadderController(mod, p, design, b, post_reveal_brake_to=bt)),
        )
    )
    return out


# ----------------------------------------------------------------- evaluation


class BinMeasurement:
    """Runs all candidates on the mu grid of one (variant, bin)."""

    def __init__(self, mod, design, variant: Variant, bin_id: str, lo: float, hi: float,
                 n_points: int, n_sel: int, n_val: int, rows_out: list[dict[str, Any]]):
        from autodrift.config import build_env_config
        from autodrift.env import AutoDriftEnv

        self.mod, self.design, self.variant = mod, design, variant
        self.bin_id, self.lo, self.hi = bin_id, lo, hi
        self.rows_out = rows_out
        self.mus = [lo + (i + 0.5) / n_points * (hi - lo) for i in range(n_points)]
        self.ds = [variant.d_of_mu(m) for m in self.mus]
        self.seeds_sel = [SEED_BASE * 10 + k for k in range(n_sel)]
        self.seeds_val = [SEED_BASE * 10 + 100 + k for k in range(n_val)]
        self.envs = []
        for mu in self.mus:
            env = AutoDriftEnv(build_env_config(point_env_config(mod, design, variant, mu)))
            assert env.base_obs_dim == mod.OBS_DIM
            self.envs.append(env)
        # results[name][point] = {"sel": [rows], "val": [rows]}
        self.results: dict[str, list[dict[str, list[dict[str, Any]]]]] = {}
        self.groups: dict[str, str] = {}
        self.v_entries: dict[str, float | None] = {}
        self.episodes = 0

    def close(self) -> None:
        for env in self.envs:
            env.close()

    def _run(self, cand: Candidate, point: int, seeds: list[int], phase: str) -> list[dict[str, Any]]:
        controller = cand.build()
        rows = []
        for k, seed in enumerate(seeds):
            row = self.mod.rollout(self.envs[point], controller, seed + 17 * point + 1000 * k)
            self.episodes += 1
            row.update(
                {
                    "variant": self.variant.variant_id, "bin": self.bin_id,
                    "mu_point": round(self.mus[point], 4), "d_point": round(self.ds[point], 2),
                    "plan": cand.name, "plan_group": cand.group, "phase": phase,
                }
            )
            self.rows_out.append(row)
            rows.append(row)
        return rows

    def eval_candidate(self, cand: Candidate, points: list[int] | None = None, phase: str = "sel") -> None:
        points = points if points is not None else list(range(len(self.mus)))
        slot = self.results.setdefault(cand.name, [{"sel": [], "val": []} for _ in self.mus])
        self.groups[cand.name] = cand.group
        self.v_entries[cand.name] = cand.v_entry
        seeds = self.seeds_sel if phase == "sel" else self.seeds_val
        for point in points:
            if slot[point][phase]:
                continue
            slot[point][phase] = self._run(cand, point, seeds, phase)

    # -- aggregates ----------------------------------------------------------
    def point_stat(self, name: str, point: int, phase: str, key: str) -> float:
        rows = self.results[name][point][phase]
        if not rows:
            return float("nan")
        if key == "success":
            return float(np.mean([1.0 if r["success"] else 0.0 for r in rows]))
        return float(np.mean([r[key] for r in rows]))

    def bin_mean(self, name: str, phase: str, key: str) -> float:
        return float(np.mean([self.point_stat(name, p, phase, key) for p in range(len(self.mus))]))


def cem_optimize(score: Callable[[np.ndarray], float], mean0: np.ndarray, std0: np.ndarray,
                 iters: int, pop: int, elite: int, rng: np.random.Generator) -> tuple[np.ndarray, list[dict[str, float]]]:
    mean, std = mean0.copy(), std0.copy()
    best_params, best_score = mean0.copy(), -np.inf
    history = []
    for it in range(iters):
        samples = mean[None, :] + std[None, :] * rng.standard_normal((pop, len(mean)))
        for i in range(4):
            samples[:, i] = np.clip(samples[:, i], *CEM_CLIP[i])
        scores = np.array([score(s) for s in samples])
        order = np.argsort(scores)[::-1]
        if scores[order[0]] > best_score:
            best_score, best_params = float(scores[order[0]]), samples[order[0]].copy()
        elite_set = samples[order[:elite]]
        mean = elite_set.mean(axis=0)
        std = 0.7 * elite_set.std(axis=0) + 0.05
        history.append({"iter": it, "best": round(float(scores[order[0]]), 4), "mean_v": round(float(mean[0]), 2)})
    return best_params, history


def measure_bin(mod, design, variant: Variant, bin_spec: tuple[str, float, float, str],
                n_points: int, n_sel: int, n_val: int, cem_pop: int, cem_iters: int,
                rows_out: list[dict[str, Any]]) -> dict[str, Any]:
    bin_id, lo, hi, bin_note = bin_spec
    bm = BinMeasurement(mod, design, variant, bin_id, lo, hi, n_points, n_sel, n_val, rows_out)
    n_pts = len(bm.mus)
    try:
        # [1] structured bin-aware fixed plans: grid + ladders
        fixed_cands = grid_candidates(mod, design) + ladder_candidates(mod, design, variant, lo, hi)
        for cand in fixed_cands:
            bm.eval_candidate(cand, phase="sel")

        # [2] robust-CEM fixed plan: optimize the BIN AVERAGE on a subgrid, 1 seed
        subgrid = list(range(0, n_pts, 2))
        cem_calls = {"n": 0}

        def robust_score(params: np.ndarray) -> float:
            cem_calls["n"] += 1
            plan = plan_from_params(mod, f"_cem_tmp_{cem_calls['n']}", params)
            controller = mod.CommitmentController(plan, design)
            succ, ret = [], []
            for point in subgrid:
                row = mod.rollout(bm.envs[point], controller, bm.seeds_sel[0] + 17 * point)
                bm.episodes += 1
                succ.append(1.0 if row["success"] else 0.0)
                ret.append(row["return"])
            return float(np.mean(succ)) + 2e-4 * float(np.mean(ret))

        v_lo_safe = variant.v_oracle_est(lo)
        v_hi_need = variant.d_of_mu(hi) / design.deadline_s + 1.0
        mean0 = np.array([0.5 * (v_lo_safe + v_hi_need), 0.9, 3.0, 3.5])
        std0 = np.array([1.5, 0.12, 0.5, 1.0])
        rng = np.random.default_rng(SEED_BASE + hash(bin_id) % 1000)
        best_params, cem_hist = cem_optimize(robust_score, mean0, std0, cem_iters, cem_pop, max(3, cem_pop // 4), rng)
        cem_plan = plan_from_params(mod, "cem_robust", best_params)
        cem_cand = Candidate(
            "cem_robust", "cem_robust",
            (lambda p=cem_plan: mod.CommitmentController(p, design)), v_entry=float(cem_plan.v_entry),
        )
        bm.eval_candidate(cem_cand, phase="sel")
        all_cands = {c.name: c for c in fixed_cands}
        all_cands[cem_cand.name] = cem_cand

        # [3] best single bin-aware plan (selection seeds), then validation
        def fixed_key(name: str) -> tuple[float, float]:
            return (bm.bin_mean(name, "sel", "success"), bm.bin_mean(name, "sel", "return"))

        best_fixed = max(all_cands, key=fixed_key)
        best_fixed_ret = max(all_cands, key=lambda n: bm.bin_mean(n, "sel", "return"))
        for name in {best_fixed, best_fixed_ret}:
            bm.eval_candidate(all_cands[name], phase="val")

        # [4] per-mu oracle: best candidate at each point; refine if below 1.0
        oracle_choice: list[str] = []
        for point in range(n_pts):
            def point_key(name: str) -> tuple[float, float]:
                return (bm.point_stat(name, point, "sel", "success"),
                        bm.point_stat(name, point, "sel", "return"))

            best = max(all_cands, key=point_key)
            if bm.point_stat(best, point, "sel", "success") < 1.0 - 1e-9:
                v_base = bm.v_entries.get(best) or variant.v_oracle_est(bm.mus[point])
                local: list[Candidate] = []
                for dv in (-0.25, 0.25):
                    for tag, cap, off, gain in STEER_VARIANTS:
                        v = float(np.clip(v_base + dv, 4.0, 14.5))
                        plan = mod.PlanSpec(name=f"pt{point}_v{v:g}_{tag}", v_entry=v, brake_to=None,
                                            swerve_offset=off, swerve_gain=gain, steer_cap=cap)
                        local.append(Candidate(plan.name, "refine",
                                               (lambda p=plan: mod.CommitmentController(p, design)), v_entry=v))
                for cand in local:
                    bm.eval_candidate(cand, points=[point], phase="sel")
                    all_cands[cand.name] = cand
                # reduced-budget per-mu CEM (1 seed) if still not solved
                cand_pool = [n for n in all_cands if bm.results[n][point]["sel"]]
                best = max(cand_pool, key=point_key)
                if bm.point_stat(best, point, "sel", "success") < 1.0 - 1e-9:
                    def point_score(params: np.ndarray, _pt=point) -> float:
                        plan = plan_from_params(mod, "_cem_pt_tmp", params)
                        controller = mod.CommitmentController(plan, design)
                        row = mod.rollout(bm.envs[_pt], controller, bm.seeds_sel[0] + 17 * _pt)
                        bm.episodes += 1
                        return (1.0 if row["success"] else 0.0) + 2e-4 * float(row["return"])

                    m0 = np.array([v_base, 0.9, 3.0, 3.5])
                    s0 = np.array([0.8, 0.1, 0.4, 0.8])
                    rng_pt = np.random.default_rng(SEED_BASE + 7 * point + hash(bin_id) % 997)
                    params_pt, _ = cem_optimize(point_score, m0, s0, 2, 8, 3, rng_pt)
                    plan_pt = plan_from_params(mod, f"pt{point}_cem", params_pt)
                    cand_pt = Candidate(plan_pt.name, "cem_point",
                                        (lambda p=plan_pt: mod.CommitmentController(p, design)),
                                        v_entry=float(plan_pt.v_entry))
                    bm.eval_candidate(cand_pt, points=[point], phase="sel")
                    all_cands[cand_pt.name] = cand_pt
                    cand_pool.append(cand_pt.name)
                    best = max(cand_pool, key=point_key)
            oracle_choice.append(best)
            bm.eval_candidate(all_cands[best], points=[point], phase="val")

        # oracle by return (may differ from success-oracle)
        oracle_choice_ret: list[str] = []
        for point in range(n_pts):
            pool = [n for n in all_cands if bm.results[n][point]["sel"]]
            best_r = max(pool, key=lambda n: bm.point_stat(n, point, "sel", "return"))
            oracle_choice_ret.append(best_r)
            bm.eval_candidate(all_cands[best_r], points=[point], phase="val")

        # [5] aggregates
        def agg(metric: str) -> dict[str, Any]:
            o_in = float(np.mean([bm.point_stat(oracle_choice[p], p, "sel", metric) for p in range(n_pts)]))
            o_val = float(np.mean([bm.point_stat(oracle_choice[p], p, "val", metric) for p in range(n_pts)]))
            if metric == "return":
                o_in = float(np.mean([bm.point_stat(oracle_choice_ret[p], p, "sel", metric) for p in range(n_pts)]))
                o_val = float(np.mean([bm.point_stat(oracle_choice_ret[p], p, "val", metric) for p in range(n_pts)]))
                f_name = best_fixed_ret
            else:
                f_name = best_fixed
            f_in = bm.bin_mean(f_name, "sel", metric)
            f_val = bm.bin_mean(f_name, "val", metric)
            return {
                "oracle_in_sample": round(o_in, 4), "oracle_validated": round(o_val, 4),
                "best_fixed_plan": f_name,
                "best_fixed_in_sample": round(f_in, 4), "best_fixed_validated": round(f_val, 4),
                "voi_in_sample": round(o_in - f_in, 4), "voi_validated": round(o_val - f_val, 4),
            }

        success_agg, return_agg = agg("success"), agg("return")

        # [6] mechanism: feasible entry-speed band per mu point (grid variant A, sel seeds)
        bands = []
        for point in range(n_pts):
            ok = [v for v in V_GRID
                  if bm.point_stat(f"grid_v{v:g}_A", point, "sel", "success") >= 1.0 - 1e-9]
            bands.append({
                "mu": round(bm.mus[point], 4), "d_m": round(bm.ds[point], 2),
                "v_min": min(ok) if ok else None, "v_max": max(ok) if ok else None,
                "n_feasible_speeds": len(ok),
                "oracle_plan": oracle_choice[point],
                "oracle_success_in_sample": round(bm.point_stat(oracle_choice[point], point, "sel", "success"), 3),
                "oracle_success_validated": round(bm.point_stat(oracle_choice[point], point, "val", "success"), 3),
                "best_fixed_success_validated": round(bm.point_stat(best_fixed, point, "val", "success"), 3)
                if bm.results[best_fixed][point]["val"] else None,
            })
        tops = [b["v_max"] for b in bands if b["v_max"] is not None]
        bots = [b["v_min"] for b in bands if b["v_min"] is not None]
        mu_span = bm.mus[-1] - bm.mus[0]
        inter_lo = max(bots) if bots and len(bots) == n_pts else None
        inter_hi = min(tops) if tops and len(tops) == n_pts else None
        mechanism = {
            "bands_per_mu_point": bands,
            "band_top_shift_mps_per_mu": round((tops[-1] - tops[0]) / mu_span, 2) if len(tops) >= 2 else None,
            "band_bottom_shift_mps_per_mu": round((bots[-1] - bots[0]) / mu_span, 2) if len(bots) >= 2 else None,
            "band_intersection_over_bin": (
                {"lo": inter_lo, "hi": inter_hi, "width": round(inter_hi - inter_lo, 2), "empty": inter_hi < inter_lo}
                if inter_lo is not None and inter_hi is not None else {"empty": True, "note": "some point has no feasible grid speed"}
            ),
        }

        top_fixed = sorted(
            ({"plan": n, "group": bm.groups[n], "mean_success_sel": round(bm.bin_mean(n, "sel", "success"), 4),
              "mean_return_sel": round(bm.bin_mean(n, "sel", "return"), 1)}
             for n in all_cands if all(bm.results[n][p]["sel"] for p in range(n_pts))),
            key=lambda r: -r["mean_success_sel"],
        )[:6]

        return {
            "bin_id": bin_id, "bin_note": bin_note, "mu_lo": lo, "mu_hi": hi,
            "prior_half_width": round(0.5 * (hi - lo), 3),
            "n_mu_points": n_pts, "mu_points": [round(m, 4) for m in bm.mus],
            "d_points_m": [round(d, 2) for d in bm.ds],
            "seeds": {"selection": bm.seeds_sel, "validation": bm.seeds_val},
            "episodes": bm.episodes,
            "voi_success": success_agg,
            "voi_return": return_agg,
            "oracle_plan_per_point": oracle_choice,
            "top_fixed_plans": top_fixed,
            "cem_robust": {"params_v_cap_off_gain": [round(float(x), 3) for x in best_params],
                           "history": cem_hist},
            "mechanism": mechanism,
        }
    finally:
        bm.close()


# ----------------------------------------------------------------------- main


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


def run_variant(mod, variant: Variant, bins, n_points, n_sel, n_val, cem_pop, cem_iters, rows_out) -> dict[str, Any]:
    design = variant_design(mod, variant)
    out = {"variant": dataclasses.asdict(variant), "deadline_s": design.deadline_s, "bins": {}}
    for bin_spec in bins:
        t0 = time.time()
        res = measure_bin(mod, design, variant, bin_spec, n_points, n_sel, n_val, cem_pop, cem_iters, rows_out)
        res["elapsed_s"] = round(time.time() - t0, 1)
        out["bins"][bin_spec[0]] = res
        v = res["voi_success"]
        print(
            f"  [{variant.variant_id}] {bin_spec[0]:<14} VoI(success)={v['voi_in_sample']:.3f} "
            f"(val {v['voi_validated']:.3f}) oracle={v['oracle_validated']:.3f} "
            f"fixed={v['best_fixed_validated']:.3f} ({v['best_fixed_plan']}) "
            f"VoI(return)={res['voi_return']['voi_validated']:.1f} "
            f"[{res['episodes']} eps, {res['elapsed_s']}s]"
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=2)
    parser.add_argument("--val-seeds", type=int, default=2)
    parser.add_argument("--cem-pop", type=int, default=12)
    parser.add_argument("--cem-iters", type=int, default=3)
    parser.add_argument("--time-budget-s", type=float, default=700.0)
    args = parser.parse_args()
    if args.quick:
        args.points, args.sel_seeds, args.val_seeds, args.cem_pop, args.cem_iters = 4, 1, 1, 6, 2

    started = time.time()
    mod = load_task_b_module()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, Any]] = []

    print(f"[1/3] base variant ({BASE_VARIANT.variant_id}): 4 prior bins x {args.points} mu points")
    base = run_variant(mod, BASE_VARIANT, BINS, args.points, args.sel_seeds, args.val_seeds,
                       args.cem_pop, args.cem_iters, rows_out)

    # knob iteration: only if the +/-0.2 prior bin fails the 0.2 conditional-VoI bar
    medium_voi = base["bins"]["medium_pm0.20"]["voi_success"]["voi_validated"]
    wide_voi = base["bins"]["wide_pm0.30"]["voi_success"]["voi_validated"]
    iterations = []
    if medium_voi < VOI_TARGET:
        print(f"[2/3] medium-bin VoI {medium_voi:.3f} < {VOI_TARGET}: iterating task knobs")
        iter_bins = tuple(b for b in BINS if b[0] in ("wide_pm0.30", "medium_pm0.20"))
        for variant in KNOB_VARIANTS:
            if time.time() - started > args.time_budget_s - 130.0:
                iterations.append({"variant": variant.variant_id, "skipped": "time budget"})
                print(f"  [{variant.variant_id}] skipped (time budget)")
                continue
            res = run_variant(mod, variant, iter_bins, args.points, args.sel_seeds, args.val_seeds,
                              args.cem_pop, args.cem_iters, rows_out)
            res["medium_voi_validated"] = res["bins"]["medium_pm0.20"]["voi_success"]["voi_validated"]
            res["target_met"] = bool(res["medium_voi_validated"] >= VOI_TARGET)
            iterations.append(res)
            if res["target_met"]:
                print(f"  target met by {variant.variant_id}")
                break
    else:
        print(f"[2/3] medium-bin VoI {medium_voi:.3f} >= {VOI_TARGET}: no knob iteration needed")

    print("[3/3] writing artifacts")
    from autodrift.artifacts import utc_timestamp, write_csv_rows

    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, rows_out)

    curve = [
        {
            "bin_id": b, "prior_half_width": base["bins"][b]["prior_half_width"],
            "voi_success_in_sample": base["bins"][b]["voi_success"]["voi_in_sample"],
            "voi_success_validated": base["bins"][b]["voi_success"]["voi_validated"],
            "voi_return_validated": base["bins"][b]["voi_return"]["voi_validated"],
            "best_fixed_plan": base["bins"][b]["voi_success"]["best_fixed_plan"],
            "band_intersection": base["bins"][b]["mechanism"]["band_intersection_over_bin"],
        }
        for b in ("narrow_pm0.10", "medium_pm0.20", "wide_pm0.30", "full_pm0.45")
    ]

    narrow_voi = base["bins"]["narrow_pm0.10"]["voi_success"]["voi_validated"]
    final_medium = medium_voi
    if iterations and any(isinstance(i, dict) and i.get("target_met") for i in iterations):
        final_medium = max(i["medium_voi_validated"] for i in iterations if "medium_voi_validated" in i)
    if medium_voi >= VOI_TARGET:
        verdict = "confirmed"
        verdict_note = (
            "Even given a +/-0.20 coarse prior, precise mu knowledge adds >= 0.2 success on the "
            "UNMODIFIED continuous B2 family: coarse side channels cannot replace "
            "command->response self-identification here."
        )
    elif wide_voi >= VOI_TARGET:
        verdict = "partially_confirmed"
        verdict_note = (
            "Precise mu stays valuable when the side channel is only +/-0.30 accurate, but a "
            "+/-0.20 prior plus bin-aware hedging already recovers most of the oracle on the "
            "unmodified family"
            + (
                "; a knob-tightened variant restores VoI >= 0.2 at +/-0.20 (see knob_iterations)."
                if final_medium >= VOI_TARGET else
                "; knob iteration did not restore VoI >= 0.2 at +/-0.20 within this env's expressiveness."
            )
        )
    else:
        verdict = "refuted_at_tested_widths"
        verdict_note = (
            "Within this task structure, coarse priors of +/-0.20..0.30 plus bin-aware hedge plans "
            "(ladders / robust-CEM) capture nearly the whole oracle: the user proposition fails here."
        )

    payload = {
        "protocol": "feasibility_audit_voi_conditional_prior",
        "generated_by": "scripts/feasibility_audit/voi_conditional_prior.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "proposition_under_test": (
            "Side channels (road appearance / wipers / temperature) only give a coarse mu range "
            "(+/-0.2..0.3 literature precision); precise capability knowledge requires "
            "instruction->response identification. Tested as: conditional VoI(precise mu | coarse "
            "bin) significantly positive?"
        ),
        "voi_definition": (
            "conditional VoI(bin) = E_{mu in bin}[per-mu oracle outcome] - max_{bin-aware fixed "
            "plan} E_{mu in bin}[outcome]; mu on a deterministic midpoint grid (~U(bin)); fixed "
            "plans may use the bin and own driven distance (silence ladders) but not mu; "
            "success = outcome_bucket == success_obstacle_pass; selection on selection seeds, "
            "headline on disjoint validation seeds."
        ),
        "continuousization": {
            "mu_to_distance_knots": {"mu": MU_KNOTS, "d_m": D_KNOTS},
            "interpolation": "piecewise linear, linear extrapolation outside [0.30, 1.15]",
            "oracle_speed_prior_knots_for_ladders": {"mu": MU_KNOTS, "v_mps": V_ORACLE_KNOTS},
        },
        "panel": {
            "mu_points_per_bin": args.points, "selection_seeds": args.sel_seeds,
            "validation_seeds": args.val_seeds, "cem_pop": args.cem_pop, "cem_iters": args.cem_iters,
            "seed_formula": "20260611*10 + {0,1 sel | 100,101 val} + 17*point + 1000*k",
        },
        "task_b_anchor": {
            "discrete_B2_voi_success_augmented_in_sample": 0.4375,
            "source": "experiments/feasibility_audit/voi_commitment_adversarial_audit.json",
        },
        "headline_curve_voi_vs_prior_width": curve,
        "base_variant": base,
        "knob_iterations": iterations,
        "voi_target": VOI_TARGET,
        "verdict": verdict,
        "verdict_note": verdict_note,
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {"episode_rows_csv": str(rows_csv), "results_json": str(RESULTS_JSON)},
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {RESULTS_JSON}")
    print(f"episode rows -> {rows_csv} ({len(rows_out)} rows)")
    print(
        "HEADLINE: VoI(success|prior) validated: "
        + ", ".join(f"{c['bin_id']}={c['voi_success_validated']:.3f}" for c in curve)
        + f" | verdict={verdict} | elapsed {time.time() - started:.0f}s"
    )


if __name__ == "__main__":
    main()
