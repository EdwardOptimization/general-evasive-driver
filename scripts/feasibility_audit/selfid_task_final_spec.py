"""Final task spec for the self-ID commitment family: repair round + ignition gate.

Base family = B2 continuous-mu + K2 (perception_reveal_distance = 10 m), with the
four adversarial-audit repairs applied and the FULL acceptance checklist measured
in one run (every iteration re-measures every item, never only the changed one):

  P1 reward recalibration   collision_penalty 20 -> >=60, pass_reward 10 -> >=40
                            (both are native ObstacleTaskConfig knobs). Accept:
                            per-anchor-level Goodman-Kruskal gamma(plan return,
                            plan success) >= 0.9 AND tie-normalized Spearman >=
                            0.9 (raw tie-corrected Spearman is structurally capped
                            < 0.9 by success ties; cap reported); theta1/theta4
                            oracle return beats EVERY failing plan by >= 10 % of
                            that plan's return.
  P2 anti-ladder geometry   d = d_of_mu(mu) + eps, eps ~ U(-J, J) per episode
     + free-prior control   (script-level mixture; native env feature documented).
                            Accept: tuned silence-ladder family (knows the +/-0.2
                            prior bin AND the jitter) <= best simple fixed plan
                            (validated), and conditional VoI(+/-0.2 prior, best
                            fixed taken over grid+ladder+robust-CEM adversaries)
                            >= 0.20 on validation seeds.
  P3 theta1 unavoidability  point-mass eta=1.0 friction-circle bound deficit
                            >= 0.5 m for every fast arrival (plans with
                            v_entry >= 10) at theta1, and in-env reactive escape
                            sweep 0/128.
  P4 gate protocol          measurement anchor frame <= first probe pulse (the
                            post-probe single frame leaks mu, R^2 ~ 0.97); the
                            three gate signatures are CONJUNCTIVE. Measured
                            support: anchor-frame R^2 <= 0.1, final-frame R^2
                            reported.
  KE knife-edge mitigation  fractional cells of the anchor success matrix < 15 %
                            (baseline 38/160 = 23.75 % from the adversarial
                            audit); key cells re-measured with 2 disjoint
                            validation seed groups, |delta| <= 0.25.
  I5 integrity recheck      anchor oracle success >= 0.9 per level on FRESH
                            seeds; medium-bin validated oracle >= 0.9; active
                            probe R^2 >= 0.9 (no-probe contrast reported);
                            "always slow" return <= 0.8 x oracle return on
                            theta3/theta4.

Reuses the Task-B / conditional-prior / adversarial-audit machinery via
importlib (no existing file modified). Pure CPU numpy, deterministic seeds, no
training, new files only.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/selfid_task_final_spec.py
    PYTHONPATH=src python scripts/feasibility_audit/selfid_task_final_spec.py --quick
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
COND_SCRIPT = REPO / "scripts/feasibility_audit/voi_conditional_prior.py"
AUDIT_SCRIPT = REPO / "scripts/feasibility_audit/voi_commitment_adversarial_audit.py"
RESULTS_JSON = REPO / "experiments/feasibility_audit/selfid_task_final_spec.json"
RUN_DIR = REPO / "runs/feasibility_audit/selfid_task_final_spec"

SEED_BASE = 20260615  # fresh stream (B=20260612, C=20260613, cond=20260611)
VOI_TARGET = 0.20
KNIFE_EDGE_TARGET = 0.15
KNIFE_EDGE_BASELINE = 38.0 / 160.0
P3_DEFICIT_TARGET = 0.50
FAST_PLAN_V = 10.0
FIRST_PULSE_STEP = 12  # PULSES[0] start in the Task-B controller
ANCHOR_FRAME_STEP = 11  # last guaranteed pre-pulse frame

CLAIM_BOUNDARY = (
    "Feasibility-audit task-DESIGN repair measurement only: the B2-continuous+K2 commitment "
    "family is re-knobbed (reward recalibration, distance jitter, reveal geometry) and ALL "
    "acceptance items are re-measured with scripted mu-agnostic / bin-aware adversarial plans, "
    "per-mu empirical oracles, numeric physics bounds and linear probes. No driver-performance, "
    "repair-success, robustness-result, validation, ranking, promotion, paper, or self-ID "
    "*capability* claim is made."
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------- knobs


@dataclass(frozen=True)
class Knobs:
    """Iterable repair knobs. Everything else is pinned to B2-continuous."""

    iteration: int = 1
    reveal_distance: float = 10.0  # K2
    max_steps: int = 285  # deadline 5.7 s
    obstacle_half_width: float = 1.25
    jitter_d_m: float = 2.0  # P2 anti-ladder distance jitter (uniform +/-)
    mu1: float = 0.30  # theta1 anchor mu
    pass_reward: float = 40.0  # P1 (>= 40)
    collision_penalty: float = 60.0  # P1 (>= 60)
    # mu<->d map knots at mu (0.30, 0.55, 0.85, 1.15). The B2 top knots (49, 62)
    # are NOT reveal-10 feasible (in-env dodge ceiling at mu=1.15 is ~11 m/s but
    # d=62 demands >= 10.9 m/s average -> empty band); retuned so every theta
    # keeps a nonempty feasible band under jitter.
    d_knots: tuple[float, float, float, float] = (24.0, 38.0, 47.0, 52.0)
    # design-estimate oracle entry speeds at the knots (feeds ladder targets,
    # CEM inits and the level-tuned commit plans; adversaries get the tuned values)
    v_oracle_knots: tuple[float, float, float, float] = (4.5, 7.5, 9.5, 10.5)
    note: str = ""


MEDIUM_BIN = (0.45, 0.85)  # +/-0.20 side-channel prior
FULL_BIN = (0.25, 1.15)  # no-prior control


def make_design(mod_b, knobs: Knobs):
    b2 = next(d for d in mod_b.candidate_designs() if d.design_id == "B2_mu_correlated_hazard_tight")
    mus = (knobs.mu1, 0.55, 0.85, 1.15)
    levels = tuple(
        mod_b.LevelSpec(mu=m, d_lo=d, d_hi=d, entry_speed=v)
        for m, d, v in zip(mus, knobs.d_knots, knobs.v_oracle_knots)
    )
    return dataclasses.replace(
        b2,
        design_id=f"B2K2_final_iter{knobs.iteration}",
        reveal_distance=knobs.reveal_distance,
        max_steps=knobs.max_steps,
        obstacle_half_width=knobs.obstacle_half_width,
        pass_reward=knobs.pass_reward,
        collision_penalty=knobs.collision_penalty,
        levels=levels,
    )


def make_variant(mod_c, knobs: Knobs):
    # retune the module-level mu<->d / oracle-speed knots used by Variant,
    # ladder_breaks_for_bin and the CEM inits (our loaded module instance only)
    mod_c.D_KNOTS = tuple(knobs.d_knots)
    mod_c.V_ORACLE_KNOTS = tuple(knobs.v_oracle_knots)
    return mod_c.Variant(
        variant_id=f"final_iter{knobs.iteration}",
        max_steps=knobs.max_steps,
        reveal_distance=knobs.reveal_distance,
        obstacle_half_width=knobs.obstacle_half_width,
        note="B2 continuous + K2 + final-spec repairs",
    )


def jittered_distance(variant, knobs: Knobs, mu: float, rollout_seed: int) -> float:
    base = variant.d_of_mu(mu)
    eps = float(np.random.default_rng([SEED_BASE, 777, int(rollout_seed)]).uniform(-knobs.jitter_d_m, knobs.jitter_d_m))
    return max(base + eps, knobs.reveal_distance + 5.0)


class EnvPool:
    """Per-(mu, jittered d) degenerate env configs, keyed by rollout seed."""

    def __init__(self, mod_b, design, variant, knobs: Knobs):
        from autodrift.config import build_env_config
        from autodrift.env import AutoDriftEnv

        self._build_env_config = build_env_config
        self._env_cls = AutoDriftEnv
        self.mod_b, self.design, self.variant, self.knobs = mod_b, design, variant, knobs
        self._cache: dict[tuple[float, int], Any] = {}
        self.episodes = 0

    def env_for(self, mu: float, seed: int):
        key = (round(mu, 6), seed)
        if key not in self._cache:
            d = jittered_distance(self.variant, self.knobs, mu, seed)
            level = self.mod_b.LevelSpec(mu=mu, d_lo=d, d_hi=d, entry_speed=self.variant.v_oracle_est(mu))
            env = self._env_cls(self._build_env_config(self.mod_b.level_env_config(self.design, level)))
            assert env.base_obs_dim == self.mod_b.OBS_DIM
            self._cache[key] = env
        return self._cache[key]

    def rollout(self, controller, mu: float, seed: int, **tags) -> dict[str, Any]:
        env = self.env_for(mu, seed)
        row = self.mod_b.rollout(env, controller, seed)
        self.episodes += 1
        row["passed"] = bool(row["outcome_bucket"] == "success_obstacle_pass")
        row["collided"] = bool(row["outcome_bucket"] == "collision_failure")
        row["d_jittered"] = round(jittered_distance(self.variant, self.knobs, mu, seed), 3)
        row.update(tags)
        return row

    def close(self) -> None:
        for env in self._cache.values():
            env.close()
        self._cache.clear()


# ------------------------------------------------------------ rank statistics


def average_ranks(values) -> np.ndarray:
    v = np.asarray(values, dtype=np.float64)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), dtype=np.float64)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        ranks[order[i : j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def spearman_tie_corrected(a, b) -> float:
    ra, rb = average_ranks(a), average_ranks(b)
    if ra.std() < 1e-12 or rb.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_ceiling(a) -> float:
    """Max achievable tie-corrected Spearman vs an untied covariate, given the
    tie structure of `a` (perfect alignment bound)."""
    a = np.asarray(a, dtype=np.float64)
    ideal = np.empty(len(a), dtype=np.float64)
    ideal[np.argsort(a, kind="mergesort")] = np.arange(1, len(a) + 1)
    return spearman_tie_corrected(a, ideal)


def goodman_kruskal_gamma(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    concordant = discordant = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            da, db = a[i] - a[j], b[i] - b[j]
            if da == 0 or db == 0:
                continue
            if da * db > 0:
                concordant += 1
            else:
                discordant += 1
    if concordant + discordant == 0:
        return float("nan")
    return (concordant - discordant) / (concordant + discordant)


def reprice(row: dict[str, Any], knobs: Knobs, pass_reward: float, collision_penalty: float) -> float:
    """Exact linear re-pricing: pass_reward / collision_penalty are single
    additive terminal events in env.step (verified by the identity check)."""
    return (
        float(row["return"])
        + (pass_reward - knobs.pass_reward) * (1.0 if row["passed"] else 0.0)
        - (collision_penalty - knobs.collision_penalty) * (1.0 if row["collided"] else 0.0)
    )


# ------------------------------------------------------------- anchor ladders


def anchor_ladder_controllers(mod_b, mod_c, design, variant, knobs: Knobs) -> list[tuple[str, Any]]:
    """Tuned discrete silence ladders for the 4-anchor panel (jitter-aware)."""
    mus = [level.mu for level in design.levels]
    ds = [variant.d_of_mu(mu) for mu in mus]
    vs = [level.entry_speed for level in design.levels]
    out: list[tuple[str, Any]] = []

    def add(name: str, breaks: list[tuple[float, float]]) -> None:
        plan = mod_b.PlanSpec(name=name, v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
        out.append((name, mod_c.TunedLadderController(mod_b, plan, design, breaks)))

    for tag, margin in (("cons", knobs.jitter_d_m), ("mid", 0.0), ("aggr", -knobs.jitter_d_m)):
        for dv, vtag in ((0.0, ""), (1.0, "_fast")):
            breaks = [(0.0, vs[0] + dv)]
            for i in range(1, len(mus)):
                p = max(ds[i - 1] + margin - knobs.reveal_distance + 1.0, 0.0)
                breaks.append((p, min(vs[i] + dv, 14.5)))
            add(f"aladder_{tag}{vtag}", breaks)
    # the audit's strongest shape: gamble a 7.5 start, then jump
    add("aladder_75_aggr", [(0.0, 7.5), (max(ds[0] - knobs.reveal_distance + 1.0, 0.0), 10.0), (max(ds[1] - knobs.reveal_distance + 1.0, 0.0), 13.0)])
    add("aladder_75_max", [(0.0, 7.5), (max(ds[1] - knobs.reveal_distance + 1.0, 0.0), 13.0)])
    return out


def anchor_plan_zoo(mod_b, mod_c, design, variant, knobs: Knobs) -> list[tuple[str, str, Callable[[], Any]]]:
    """(name, group, fresh-controller factory). 13 original + 20 fine sweep + 8 ladders."""
    zoo: list[tuple[str, str, Callable[[], Any]]] = []
    for plan in mod_b.plan_family(design):
        zoo.append((plan.name, "original", (lambda p=plan: mod_b.CommitmentController(p, design))))
    for v in np.arange(4.5, 14.01, 0.5):
        plan = mod_b.PlanSpec(name=f"adv_swerve_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
        zoo.append((plan.name, "fine_sweep", (lambda p=plan: mod_b.CommitmentController(p, design))))
    for name, controller in anchor_ladder_controllers(mod_b, mod_c, design, variant, knobs):
        zoo.append((name, "ladder", (lambda c=controller: c)))  # TunedLadder resets per rollout
    return zoo


def plan_v_entry(name: str) -> float | None:
    for prefix in ("adv_swerve_v", "swerve_only_v", "commit_v", "grid_v"):
        if name.startswith(prefix):
            rest = name[len(prefix) :].split("_")[0]
            try:
                return float(rest)
            except ValueError:
                return None
    if name == "always_max_v14.5":
        return 14.5
    if name == "always_crawl_v4.5":
        return 4.5
    return None


# ----------------------------------------------------------- bin measurement


class JitterBinMeasurement:
    """Conditional-VoI measurement on a continuous-mu bin with per-episode
    jittered hazard distance (every (point, seed) is its own env)."""

    def __init__(self, mod_b, mod_c, design, variant, knobs: Knobs, bin_id: str, lo: float, hi: float,
                 n_points: int, sel_seeds: list[int], val_seeds: list[int], seed_offset: int,
                 rows_out: list[dict[str, Any]]):
        self.mod_b, self.mod_c = mod_b, mod_c
        self.design, self.variant, self.knobs = design, variant, knobs
        self.bin_id, self.lo, self.hi = bin_id, lo, hi
        self.mus = [lo + (i + 0.5) / n_points * (hi - lo) for i in range(n_points)]
        self.sel_seeds, self.val_seeds = sel_seeds, val_seeds
        self.seed_offset = seed_offset
        self.pool = EnvPool(mod_b, design, variant, knobs)
        self.rows_out = rows_out
        # results[name][point][phase] = [rows]
        self.results: dict[str, list[dict[str, list[dict[str, Any]]]]] = {}
        self.groups: dict[str, str] = {}
        self.builders: dict[str, Callable[[], Any]] = {}
        self.v_entries: dict[str, float | None] = {}

    def seed_for(self, point: int, k: int, phase: str) -> int:
        return SEED_BASE * 10 + self.seed_offset + 17 * point + 1000 * k + (0 if phase == "sel" else 100000)

    def register(self, name: str, group: str, builder: Callable[[], Any], v_entry: float | None = None) -> None:
        self.results.setdefault(name, [{"sel": [], "val": []} for _ in self.mus])
        self.groups[name] = group
        self.builders[name] = builder
        self.v_entries[name] = v_entry

    def eval(self, name: str, points: list[int] | None = None, phase: str = "sel") -> None:
        points = points if points is not None else list(range(len(self.mus)))
        seeds = self.sel_seeds if phase == "sel" else self.val_seeds
        slot = self.results[name]
        for point in points:
            if slot[point][phase]:
                continue
            controller = self.builders[name]()
            rows = []
            for k in seeds:
                seed = self.seed_for(point, k, phase)
                row = self.pool.rollout(
                    controller, self.mus[point], seed,
                    stage=f"bin_{self.bin_id}", plan=name, plan_group=self.groups[name],
                    mu_point=round(self.mus[point], 4), phase=phase, iteration=self.knobs.iteration,
                )
                rows.append(row)
                self.rows_out.append(row)
            slot[point][phase] = rows

    def point_stat(self, name: str, point: int, phase: str, key: str) -> float:
        rows = self.results[name][point][phase]
        if not rows:
            return float("nan")
        if key == "success":
            return float(np.mean([1.0 if r["success"] else 0.0 for r in rows]))
        return float(np.mean([r[key] for r in rows]))

    def bin_mean(self, name: str, phase: str, key: str = "success") -> float:
        return float(np.mean([self.point_stat(name, p, phase, key) for p in range(len(self.mus))]))


def bin_ladder_set(mod_b, mod_c, design, variant, knobs: Knobs, lo: float, hi: float, reduced: bool):
    """Bin-aware silence ladders, tuned with knowledge of the prior bin AND jitter."""
    deltas = (0.0, 0.5) if reduced else (-0.5, 0.0, 0.5, 1.0)
    margins = (-knobs.jitter_d_m - 1.0, 1.0) if reduced else (-knobs.jitter_d_m - 1.0, 0.0, 1.0, 3.0)
    out = []
    for delta in deltas:
        for margin in margins:
            breaks = mod_c.ladder_breaks_for_bin(variant, lo, hi, delta, margin)
            name = f"ladder_d{delta:g}_m{margin:g}"
            plan = mod_b.PlanSpec(name=name, v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
            out.append((name, lambda b=breaks, p=plan: mod_c.TunedLadderController(mod_b, p, design, b)))
    if not reduced:
        breaks = mod_c.ladder_breaks_for_bin(variant, lo, hi, 0.5, 1.0)
        brake_to = max(variant.v_oracle_est(lo) - 0.5, 3.5)
        plan = mod_b.PlanSpec(name="ladder_d0.5_m1_brake", v_entry=breaks[0][1], brake_to=None, ladder=True, steer_cap=0.85)
        out.append(("ladder_d0.5_m1_brake", lambda b=breaks, p=plan, bt=brake_to: mod_c.TunedLadderController(mod_b, p, design, b, post_reveal_brake_to=bt)))
    return out


def measure_bin(mod_b, mod_c, design, variant, knobs: Knobs, bin_id: str, lo: float, hi: float,
                n_points: int, n_sel: int, n_val: int, seed_offset: int, rows_out: list[dict[str, Any]],
                with_cem: bool, reduced: bool, cem_pop: int = 12, cem_iters: int = 3) -> dict[str, Any]:
    bm = JitterBinMeasurement(
        mod_b, mod_c, design, variant, knobs, bin_id, lo, hi, n_points,
        sel_seeds=list(range(n_sel)), val_seeds=list(range(n_val)), seed_offset=seed_offset, rows_out=rows_out,
    )
    n_pts = len(bm.mus)
    try:
        # [1] grid (simple fixed commitments)
        grid_names = []
        steer_variants = (("A", 0.85, 3.0, 3.0),) if reduced else (("A", 0.85, 3.0, 3.0), ("B", 1.0, 3.0, 4.5))
        for v in [round(4.5 + 0.5 * i, 1) for i in range(20)]:
            for tag, cap, off, gain in steer_variants:
                plan = mod_b.PlanSpec(name=f"grid_v{v:g}_{tag}", v_entry=float(v), brake_to=None,
                                      swerve_offset=off, swerve_gain=gain, steer_cap=cap)
                bm.register(plan.name, "grid", (lambda p=plan: mod_b.CommitmentController(p, design)), v_entry=float(v))
                grid_names.append(plan.name)
        # [2] bin-aware silence ladders (know the bin + jitter)
        ladder_names = []
        for name, builder in bin_ladder_set(mod_b, mod_c, design, variant, knobs, lo, hi, reduced):
            bm.register(name, "ladder", builder)
            ladder_names.append(name)
        for name in list(bm.results):
            bm.eval(name, phase="sel")

        # [3] robust-CEM bin-average plan
        cem_info: dict[str, Any] = {"enabled": with_cem}
        if with_cem:
            subgrid = list(range(0, n_pts, 2))

            def robust_score(params: np.ndarray) -> float:
                plan = mod_c.plan_from_params(mod_b, "_cem_tmp", params)
                controller = mod_b.CommitmentController(plan, design)
                succ, ret = [], []
                for point in subgrid:
                    seed = bm.seed_for(point, 0, "sel")
                    row = bm.pool.rollout(controller, bm.mus[point], seed,
                                          stage=f"bin_{bin_id}", plan="_cem_eval", plan_group="cem_search",
                                          mu_point=round(bm.mus[point], 4), phase="search", iteration=knobs.iteration)
                    succ.append(1.0 if row["success"] else 0.0)
                    ret.append(row["return"])
                return float(np.mean(succ)) + 2e-4 * float(np.mean(ret))

            v_lo_safe = variant.v_oracle_est(lo)
            v_hi_need = variant.d_of_mu(hi) / design.deadline_s + 1.0
            mean0 = np.array([0.5 * (v_lo_safe + v_hi_need), 0.9, 3.0, 3.5])
            std0 = np.array([1.5, 0.12, 0.5, 1.0])
            rng = np.random.default_rng([SEED_BASE, 99, seed_offset])
            best_params, _hist = mod_c.cem_optimize(robust_score, mean0, std0, cem_iters, cem_pop, max(3, cem_pop // 4), rng)
            cem_plan = mod_c.plan_from_params(mod_b, "cem_robust", best_params)
            bm.register("cem_robust", "cem_robust", (lambda p=cem_plan: mod_b.CommitmentController(p, design)),
                        v_entry=float(cem_plan.v_entry))
            bm.eval("cem_robust", phase="sel")
            cem_info["params_v_cap_off_gain"] = [round(float(x), 3) for x in best_params]

        # [4] per-mu oracle with refinement
        oracle_choice: list[str] = []
        for point in range(n_pts):
            def point_key(name: str) -> tuple[float, float]:
                return (bm.point_stat(name, point, "sel", "success"), bm.point_stat(name, point, "sel", "return"))

            pool_names = [n for n in bm.results if bm.results[n][point]["sel"]]
            best = max(pool_names, key=point_key)
            if bm.point_stat(best, point, "sel", "success") < 1.0 - 1e-9:
                v_base = bm.v_entries.get(best) or variant.v_oracle_est(bm.mus[point])
                for dv in (-0.25, 0.25):
                    for tag, cap, off, gain in (("A", 0.85, 3.0, 3.0), ("B", 1.0, 3.0, 4.5)):
                        v = float(np.clip(v_base + dv, 4.0, 14.5))
                        plan = mod_b.PlanSpec(name=f"pt{point}_v{v:g}_{tag}", v_entry=v, brake_to=None,
                                              swerve_offset=off, swerve_gain=gain, steer_cap=cap)
                        bm.register(plan.name, "refine", (lambda p=plan: mod_b.CommitmentController(p, design)), v_entry=v)
                        bm.eval(plan.name, points=[point], phase="sel")
                pool_names = [n for n in bm.results if bm.results[n][point]["sel"]]
                best = max(pool_names, key=point_key)
                if with_cem and bm.point_stat(best, point, "sel", "success") < 1.0 - 1e-9:
                    def point_score(params: np.ndarray, _pt=point) -> float:
                        plan = mod_c.plan_from_params(mod_b, "_cem_pt", params)
                        controller = mod_b.CommitmentController(plan, design)
                        seed = bm.seed_for(_pt, 0, "sel")
                        row = bm.pool.rollout(controller, bm.mus[_pt], seed,
                                              stage=f"bin_{bin_id}", plan="_cem_pt_eval", plan_group="cem_search",
                                              mu_point=round(bm.mus[_pt], 4), phase="search", iteration=knobs.iteration)
                        return (1.0 if row["success"] else 0.0) + 2e-4 * float(row["return"])

                    m0 = np.array([v_base, 0.9, 3.0, 3.5])
                    s0 = np.array([0.8, 0.1, 0.4, 0.8])
                    rng_pt = np.random.default_rng([SEED_BASE, 98, seed_offset, point])
                    params_pt, _ = mod_c.cem_optimize(point_score, m0, s0, 2, 8, 3, rng_pt)
                    plan_pt = mod_c.plan_from_params(mod_b, f"pt{point}_cem", params_pt)
                    bm.register(plan_pt.name, "cem_point", (lambda p=plan_pt: mod_b.CommitmentController(p, design)),
                                v_entry=float(plan_pt.v_entry))
                    bm.eval(plan_pt.name, points=[point], phase="sel")
                    pool_names.append(plan_pt.name)
                    best = max(pool_names, key=point_key)
            oracle_choice.append(best)
            bm.eval(best, points=[point], phase="val")

        # [5] best fixed plans (selection seeds) -> validation
        full_cov = [n for n in bm.results if all(bm.results[n][p]["sel"] for p in range(n_pts))]

        def bin_key(name: str) -> tuple[float, float]:
            return (bm.bin_mean(name, "sel"), bm.bin_mean(name, "sel", "return"))

        best_fixed_all = max(full_cov, key=bin_key)  # adversary incl. ladders + cem
        best_grid = max([n for n in full_cov if bm.groups[n] == "grid"], key=bin_key)
        best_ladder = max([n for n in full_cov if bm.groups[n] == "ladder"], key=bin_key)
        for name in {best_fixed_all, best_grid, best_ladder}:
            bm.eval(name, phase="val")

        oracle_val = float(np.mean([bm.point_stat(oracle_choice[p], p, "val", "success") for p in range(n_pts)]))
        oracle_sel = float(np.mean([bm.point_stat(oracle_choice[p], p, "sel", "success") for p in range(n_pts)]))
        out = {
            "bin_id": bin_id, "mu_lo": lo, "mu_hi": hi, "prior_half_width": round(0.5 * (hi - lo), 3),
            "n_mu_points": n_pts, "mu_points": [round(m, 4) for m in bm.mus],
            "n_sel_seeds": n_sel, "n_val_seeds": n_val,
            "seed_formula": f"20260615*10 + {seed_offset} + 17*point + 1000*k (+100000 val)",
            "episodes": bm.pool.episodes,
            "oracle_in_sample": round(oracle_sel, 4),
            "oracle_validated": round(oracle_val, 4),
            "oracle_plan_per_point": oracle_choice,
            "oracle_success_per_point_validated": [
                round(bm.point_stat(oracle_choice[p], p, "val", "success"), 3) for p in range(n_pts)
            ],
            "best_fixed_all_plan": best_fixed_all,
            "best_fixed_all_group": bm.groups[best_fixed_all],
            "best_fixed_all_in_sample": round(bm.bin_mean(best_fixed_all, "sel"), 4),
            "best_fixed_all_validated": round(bm.bin_mean(best_fixed_all, "val"), 4),
            "best_simple_fixed_plan": best_grid,
            "best_simple_fixed_in_sample": round(bm.bin_mean(best_grid, "sel"), 4),
            "best_simple_fixed_validated": round(bm.bin_mean(best_grid, "val"), 4),
            "best_ladder_plan": best_ladder,
            "best_ladder_in_sample": round(bm.bin_mean(best_ladder, "sel"), 4),
            "best_ladder_validated": round(bm.bin_mean(best_ladder, "val"), 4),
            "voi_in_sample": round(oracle_sel - bm.bin_mean(best_fixed_all, "sel"), 4),
            "voi_validated": round(oracle_val - bm.bin_mean(best_fixed_all, "val"), 4),
            "cem_robust": cem_info,
            "top_fixed_plans_sel": sorted(
                ({"plan": n, "group": bm.groups[n], "mean_success_sel": round(bm.bin_mean(n, "sel"), 4)} for n in full_cov),
                key=lambda r: -r["mean_success_sel"],
            )[:6],
        }
        return out
    finally:
        bm.pool.close()


# ----------------------------------------------------------------- probe / P4


def probe_and_leak(mod_b, design, n_episodes: int) -> dict[str, Any]:
    """Active-probe inferability + P4 anchor-frame leak measurement (fresh seeds)."""
    from autodrift.config import build_env_config
    from autodrift.env import AutoDriftEnv

    out: dict[str, Any] = {"episodes_per_mode": n_episodes, "window_steps": mod_b.PROBE_WINDOW_STEPS,
                           "anchor_frame_step": ANCHOR_FRAME_STEP, "first_pulse_step": FIRST_PULSE_STEP}
    env = AutoDriftEnv(build_env_config(mod_b.probe_env_config(design)))
    try:
        for mode_idx, mode in enumerate(("probe_pulses", "no_probe")):
            plan = mod_b.PlanSpec(name=f"probe_{mode}", v_entry=mod_b.V0, brake_to=None,
                                  probe_pulses=(mode == "probe_pulses"))
            hist, anchor, final = [], [], []
            mus = []
            for episode in range(n_episodes):
                seed = SEED_BASE * 100 + mode_idx * 10000 + episode
                controller = mod_b.CommitmentController(plan, design)
                obs, info = env.reset(seed=seed)
                controller.reset()
                mus.append(float(info["mu"]))
                frames = []
                terminated = truncated = False
                for _t in range(mod_b.PROBE_WINDOW_STEPS):
                    if terminated or truncated:
                        break
                    action = controller.act(np.asarray(obs, dtype=np.float64))
                    obs, _r, terminated, truncated, info = env.step(action)
                    frames.append(np.asarray(obs[: mod_b.PROBE_FRAME_CHANNELS], dtype=np.float64).copy())
                while len(frames) < mod_b.PROBE_WINDOW_STEPS:
                    frames.append(frames[-1].copy())
                stacked = np.stack(frames)
                hist.append(stacked[:: mod_b.PROBE_FRAME_STRIDE].reshape(-1))
                anchor.append(stacked[ANCHOR_FRAME_STEP - 1])  # frame after ANCHOR_FRAME_STEP steps
                final.append(stacked[-1])
            y = np.asarray(mus)
            r2_hist, _ = mod_b.episode_ridge_r2(np.stack(hist), y)
            r2_anchor, _ = mod_b.episode_ridge_r2(np.stack(anchor), y)
            r2_final, _ = mod_b.episode_ridge_r2(np.stack(final), y)
            out[mode] = {
                "r2_raw_history": round(float(r2_hist), 4),
                "r2_anchor_frame_pre_pulse": round(float(r2_anchor), 4),
                "r2_final_frame_post_probe": round(float(r2_final), 4),
                "mu_range": [round(float(y.min()), 3), round(float(y.max()), 3)],
            }
    finally:
        env.close()
    return out


# ------------------------------------------------------------------ iteration


def measure_iteration(mod_b, mod_c, mod_audit, knobs: Knobs, args, rows_out: list[dict[str, Any]]) -> dict[str, Any]:
    t0 = time.time()
    design = make_design(mod_b, knobs)
    variant = make_variant(mod_c, knobs)
    required_offset = design.required_offset()
    n_anchor = args.anchor_seeds
    result: dict[str, Any] = {"knobs": dataclasses.asdict(knobs), "required_lateral_offset_m": required_offset}

    # ---------- [A] anchor panel (4 theta levels, jittered, full plan zoo)
    zoo = anchor_plan_zoo(mod_b, mod_c, design, variant, knobs)
    pool = EnvPool(mod_b, design, variant, knobs)
    anchor_rows: list[dict[str, Any]] = []
    for level_index, level in enumerate(design.levels):
        for name, group, build in zoo:
            controller = build()
            for k in range(n_anchor):
                seed = SEED_BASE * 10 + level_index * 1000 + k
                row = pool.rollout(controller, level.mu, seed, stage="anchor_panel", plan=name,
                                   plan_group=group, level_index=level_index, level_mu=level.mu,
                                   phase="panel", iteration=knobs.iteration)
                anchor_rows.append(row)
                rows_out.append(row)
    plan_names = [name for name, _g, _b in zoo]
    n_levels = len(design.levels)
    builders: dict[str, Callable[[], Any]] = {name: build for name, _g, build in zoo}
    groups_by_name: dict[str, str] = {name: group for name, group, _b in zoo}
    cells: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for r in anchor_rows:
        cells.setdefault((r["plan"], r["level_index"]), []).append(r)

    def cell_rows(name: str, level: int) -> list[dict[str, Any]]:
        return cells.get((name, level), [])

    def stat_of(name: str, j: int, key: str) -> float:
        rows = cell_rows(name, j)
        if not rows:
            return float("nan")
        if key == "success":
            return float(np.mean([1.0 if r["success"] else 0.0 for r in rows]))
        if key in ("passed", "collided"):
            return float(np.mean([1.0 if r[key] else 0.0 for r in rows]))
        return float(np.mean([r[key] for r in rows]))

    # census matrix = the 41 mu-agnostic zoo plans only (comparable to the audit's census)
    succ = np.array([[stat_of(n, j, "success") for j in range(n_levels)] for n in plan_names])

    # ---------- anchor oracle refinement (stronger reaction variants + speed offsets)
    REFINE_VARIANTS = (("A", 0.85, 3.0, 3.0), ("B", 1.0, 3.0, 4.5), ("C", 1.0, 3.8, 3.0), ("D", 1.0, 2.6, 6.0))
    level_plan_names: list[list[str]] = [list(plan_names) for _ in range(n_levels)]
    plan_v_entry_map: dict[str, float | None] = {n: plan_v_entry(n) for n in plan_names}
    for j in range(n_levels):
        zoo_best = max(plan_names, key=lambda n: (stat_of(n, j, "success"), stat_of(n, j, "return")))
        if stat_of(zoo_best, j, "success") >= 1.0 - 1e-9:
            continue
        v_base = plan_v_entry_map.get(zoo_best) or design.levels[j].entry_speed
        for dv in (-0.5, -0.25, 0.0, 0.25, 0.5):
            v = float(np.clip(v_base + dv, 4.0, 14.5))
            for tag, cap, off, gain in REFINE_VARIANTS:
                name = f"aref{j}_v{v:g}_{tag}"
                plan = mod_b.PlanSpec(name=name, v_entry=v, brake_to=None,
                                      swerve_offset=off, swerve_gain=gain, steer_cap=cap)
                builders[name] = (lambda p=plan: mod_b.CommitmentController(p, design))
                groups_by_name[name] = "refine_anchor"
                plan_v_entry_map[name] = v
                controller = builders[name]()
                for k in range(n_anchor):
                    seed = SEED_BASE * 10 + j * 1000 + k
                    row = pool.rollout(controller, design.levels[j].mu, seed, stage="anchor_refine",
                                       plan=name, plan_group="refine_anchor", level_index=j,
                                       level_mu=design.levels[j].mu, phase="panel", iteration=knobs.iteration)
                    cells.setdefault((name, j), []).append(row)
                    rows_out.append(row)
                level_plan_names[j].append(name)

    # final per-level oracle over zoo + refined plans
    oracle_name = [
        max(level_plan_names[j], key=lambda n: (stat_of(n, j, "success"), stat_of(n, j, "return")))
        for j in range(n_levels)
    ]

    # ---------- [KE] knife-edge census + key-cell seed-group retest
    frac_cells = int(np.sum((succ > 1e-9) & (succ < 1 - 1e-9)))
    total_cells = int(succ.size)
    best_fixed_idx = int(np.argmax(succ.mean(axis=1)))
    ladder_idx = [i for i, (_n, g, _b) in enumerate(zoo) if g == "ladder"]
    best_ladder_idx = max(ladder_idx, key=lambda i: succ[i].mean())

    key_cells = []
    fresh_oracle = []
    group_seeds = {"A": range(100, 100 + args.keycell_seeds), "B": range(200, 200 + args.keycell_seeds)}
    for j in range(n_levels):
        for role, name in (("oracle", oracle_name[j]), ("best_fixed", plan_names[best_fixed_idx]),
                           ("best_ladder", plan_names[best_ladder_idx])):
            stats = {}
            for gtag, ks in group_seeds.items():
                vals = []
                for k in ks:
                    seed = SEED_BASE * 10 + j * 1000 + k
                    row = pool.rollout(builders[name](), design.levels[j].mu, seed, stage="key_cells",
                                       plan=name, plan_group=groups_by_name[name], level_index=j,
                                       level_mu=design.levels[j].mu, phase=f"group{gtag}",
                                       iteration=knobs.iteration)
                    vals.append(1.0 if row["success"] else 0.0)
                    rows_out.append(row)
                stats[gtag] = float(np.mean(vals))
            cell = {"role": role, "plan": name, "level_mu": design.levels[j].mu,
                    "panel_success": round(stat_of(name, j, "success"), 3),
                    "groupA_success": round(stats["A"], 3), "groupB_success": round(stats["B"], 3),
                    "consistent": bool(abs(stats["A"] - stats["B"]) <= 0.25),
                    "gate_relevant": role in ("oracle", "best_fixed")}
            key_cells.append(cell)
            if role == "oracle":
                fresh_oracle.append({"level_mu": design.levels[j].mu, "plan": name,
                                     "fresh_success": round(0.5 * (stats["A"] + stats["B"]), 4)})

    # ---------- [P3] theta1 unavoidability: physics bound + reactive escape
    fast_rows = [r for r in anchor_rows
                 if r["level_index"] == 0 and (plan_v_entry(r["plan"]) or 0.0) >= FAST_PLAN_V
                 and math.isfinite(r["speed_at_reveal"])]
    speeds = sorted({round(r["speed_at_reveal"], 1) for r in fast_rows})
    bound_cache = {}
    for v in speeds:
        b = mod_audit.best_post_reveal_lateral(design.levels[0].mu, float(v), knobs.reveal_distance, 1.0)
        bound_cache[v] = required_offset - b["max_lateral_offset_m"]
    deficits = [bound_cache[round(r["speed_at_reveal"], 1)] for r in fast_rows]
    esc = [(name, c) for name, c in mod_audit.reactive_escape_controllers(mod_b, design)]
    esc_success = 0
    esc_total = 0
    for name, controller in esc:
        for k in range(args.escape_seeds):
            seed = SEED_BASE * 10 + 0 * 1000 + k
            row = pool.rollout(controller, design.levels[0].mu, seed, stage="escape", plan=name,
                               plan_group="escape", level_index=0, level_mu=design.levels[0].mu,
                               phase="escape", iteration=knobs.iteration)
            esc_total += 1
            esc_success += 1 if row["success"] else 0
            rows_out.append(row)
    pool.close()

    # ---------- [B] medium-bin conditional VoI (the +/-0.2 free-prior control arm)
    medium = measure_bin(mod_b, mod_c, design, variant, knobs, "medium_pm0.20", *MEDIUM_BIN,
                         n_points=args.bin_points, n_sel=args.sel_seeds, n_val=args.val_seeds,
                         seed_offset=50000, rows_out=rows_out, with_cem=True, reduced=False,
                         cem_pop=args.cem_pop, cem_iters=args.cem_iters)
    # ---------- [C] full-bin no-prior control (reduced zoo, context only)
    full = measure_bin(mod_b, mod_c, design, variant, knobs, "full_pm0.45", *FULL_BIN,
                       n_points=args.bin_points, n_sel=max(2, args.sel_seeds - 1), n_val=max(2, args.val_seeds - 1),
                       seed_offset=90000, rows_out=rows_out, with_cem=False, reduced=True)

    # ---------- [D] probe inferability + P4 anchor-frame leak
    leak = probe_and_leak(mod_b, design, args.probe_episodes)

    # ---------- [P1] reward repricing search (exact linear repricing)
    level_vec = []
    for j in range(n_levels):
        names = level_plan_names[j]
        level_vec.append((
            names,
            np.array([stat_of(n, j, "success") for n in names]),
            np.array([stat_of(n, j, "return") for n in names]),
            np.array([stat_of(n, j, "passed") for n in names]),
            np.array([stat_of(n, j, "collided") for n in names]),
        ))

    def level_returns(j: int, pass_r: float, col_p: float) -> np.ndarray:
        _names, _s, base, pf, cf = level_vec[j]
        return base + (pass_r - knobs.pass_reward) * pf - (col_p - knobs.collision_penalty) * cf

    def p1_eval(pass_r: float, col_p: float) -> dict[str, Any]:
        per_level = []
        for j in range(n_levels):
            _names, s, *_rest = level_vec[j]
            ret = level_returns(j, pass_r, col_p)
            gamma = goodman_kruskal_gamma(s, ret)
            sp = spearman_tie_corrected(s, ret)
            ceil = spearman_ceiling(s)
            per_level.append({
                "level_mu": design.levels[j].mu,
                "gamma_return_vs_success": round(float(gamma), 4),
                "spearman_tie_corrected": round(float(sp), 4),
                "spearman_ceiling_given_ties": round(float(ceil), 4),
                "spearman_normalized": round(float(sp / ceil), 4) if ceil > 0 else None,
            })
        gaps = {}
        for tag, j in (("theta1", 0), ("theta4", 3)):
            names, s, *_rest = level_vec[j]
            ret = level_returns(j, pass_r, col_p)
            oi = names.index(oracle_name[j])
            oracle_ret = float(ret[oi])
            failing = [(names[i], float(ret[i])) for i in range(len(names)) if s[i] < 0.5 and i != oi]
            worst = max(failing, key=lambda t: t[1]) if failing else (None, float("nan"))
            ok = bool(failing) and all(oracle_ret >= fr + 0.10 * abs(fr) for _n, fr in failing)
            gaps[tag] = {"oracle_plan": oracle_name[j], "oracle_return": round(oracle_ret, 1),
                         "best_failing_plan": worst[0], "best_failing_return": round(worst[1], 1),
                         "gap": round(oracle_ret - worst[1], 1),
                         "gap_required": round(0.10 * abs(worst[1]), 1), "dominates_all_failing": ok}
        ok_levels = all((pl["gamma_return_vs_success"] >= 0.9) and (pl["spearman_normalized"] or 0.0) >= 0.9
                        for pl in per_level)
        ok_gaps = gaps["theta1"]["dominates_all_failing"] and gaps["theta4"]["dominates_all_failing"]
        return {"pass_reward": pass_r, "collision_penalty": col_p, "per_level": per_level,
                "oracle_dominance_gaps": gaps, "criteria_met": bool(ok_levels and ok_gaps)}

    chosen = None
    for pass_r in [40.0 + 5.0 * i for i in range(13)]:
        for col_p in [60.0 + 10.0 * i for i in range(9)]:
            cand = p1_eval(pass_r, col_p)
            if cand["criteria_met"]:
                chosen = cand
                break
        if chosen:
            break
    p1_at_run = p1_eval(knobs.pass_reward, knobs.collision_penalty)
    p1 = chosen if chosen is not None else p1_at_run

    # repricing identity check (rerun a few episodes at the chosen rewards)
    identity_max_diff = None
    if chosen is not None and (chosen["pass_reward"] != knobs.pass_reward or chosen["collision_penalty"] != knobs.collision_penalty):
        check_knobs = dataclasses.replace(knobs, pass_reward=chosen["pass_reward"], collision_penalty=chosen["collision_penalty"])
        check_design = make_design(mod_b, check_knobs)
        check_pool = EnvPool(mod_b, check_design, variant, check_knobs)
        diffs = []
        for name, group, build in (zoo[4], zoo[7], zoo[20]):  # a slow, a mid, a fast plan
            for j in (0, 3):
                for k in (0, 1):
                    seed = SEED_BASE * 10 + j * 1000 + k
                    row_new = check_pool.rollout(build(), design.levels[j].mu, seed, stage="identity_check",
                                                 plan=name, plan_group=group, level_index=j,
                                                 level_mu=design.levels[j].mu, phase="check",
                                                 iteration=knobs.iteration)
                    ref = [r for r in cell_rows(name, j) if r["seed"] == seed]
                    if ref:
                        repriced = reprice(ref[0], knobs, chosen["pass_reward"], chosen["collision_penalty"])
                        diffs.append(abs(repriced - row_new["return"]))
                    rows_out.append(row_new)
        check_pool.close()
        identity_max_diff = round(float(max(diffs)), 6) if diffs else None

    # ---------- [I5] integrity items
    crawl_vs_oracle = []
    for tag, j in (("theta3", 2), ("theta4", 3)):
        names, _s, *_rest = level_vec[j]
        ret = level_returns(j, p1["pass_reward"], p1["collision_penalty"])
        crawl_r = float(ret[names.index("always_crawl_v4.5")])
        oracle_r = float(ret[names.index(oracle_name[j])])
        crawl_vs_oracle.append({"level": tag, "level_mu": design.levels[j].mu,
                                "always_crawl_return": round(crawl_r, 1), "oracle_return": round(oracle_r, 1),
                                "ratio": round(crawl_r / oracle_r, 3) if oracle_r > 0 else None,
                                "clearly_worse": bool(oracle_r > 0 and crawl_r <= 0.8 * oracle_r)})

    # ---------- acceptance assembly
    accept: dict[str, Any] = {}
    accept["P1_reward_alignment"] = {
        "PASS": bool(p1["criteria_met"]),
        "chosen_pass_reward": p1["pass_reward"], "chosen_collision_penalty": p1["collision_penalty"],
        "run_pass_reward": knobs.pass_reward, "run_collision_penalty": knobs.collision_penalty,
        "repricing_identity_max_abs_diff": identity_max_diff,
        "per_level": p1["per_level"], "oracle_dominance_gaps": p1["oracle_dominance_gaps"],
        "at_run_rewards_criteria_met": bool(p1_at_run["criteria_met"]),
        "metric_note": (
            "raw tie-corrected Spearman is structurally capped below 0.9 by success ties "
            "(cap reported per level); acceptance uses Goodman-Kruskal gamma >= 0.9 AND "
            "Spearman/cap >= 0.9, both of which equal 1.0 under perfect alignment."
        ),
    }
    ladder_ok = medium["best_ladder_validated"] <= medium["best_simple_fixed_validated"] + 1e-9
    voi_ok = medium["voi_validated"] >= VOI_TARGET
    accept["P2_anti_ladder_and_conditional_voi"] = {
        "PASS": bool(ladder_ok and voi_ok),
        "best_ladder_validated": medium["best_ladder_validated"],
        "best_simple_fixed_validated": medium["best_simple_fixed_validated"],
        "ladder_leq_simple_fixed": bool(ladder_ok),
        "voi_medium_validated": medium["voi_validated"],
        "voi_medium_in_sample": medium["voi_in_sample"],
        "voi_target": VOI_TARGET, "voi_target_met": bool(voi_ok),
        "best_fixed_all_plan": medium["best_fixed_all_plan"],
        "best_fixed_all_group": medium["best_fixed_all_group"],
        "best_fixed_all_validated": medium["best_fixed_all_validated"],
        "jitter_d_m": knobs.jitter_d_m,
    }
    min_deficit = float(min(deficits)) if deficits else float("nan")
    accept["P3_theta1_unavoidability"] = {
        "PASS": bool(deficits and min_deficit >= P3_DEFICIT_TARGET and esc_success == 0),
        "min_pointmass_eta1_deficit_m": round(min_deficit, 3),
        "deficit_target_m": P3_DEFICIT_TARGET,
        "fast_arrival_speed_range_mps": [min(speeds), max(speeds)] if speeds else None,
        "fast_arrival_episodes": len(fast_rows),
        "deficit_by_arrival_speed": {f"{v:g}": round(bound_cache[v], 3) for v in speeds},
        "reactive_escape_successes": esc_success, "reactive_escape_episodes": esc_total,
    }
    anchor_ok = leak["probe_pulses"]["r2_anchor_frame_pre_pulse"] <= 0.10
    accept["P4_gate_protocol"] = {
        "PASS": bool(anchor_ok),
        "anchor_frame_step": ANCHOR_FRAME_STEP, "first_pulse_step": FIRST_PULSE_STEP,
        "r2_anchor_frame_pre_pulse": leak["probe_pulses"]["r2_anchor_frame_pre_pulse"],
        "r2_final_frame_post_probe": leak["probe_pulses"]["r2_final_frame_post_probe"],
        "protocol": [
            "gate measurement anchor (hidden-swap / wrong-history comparisons) MUST be taken at a "
            f"frame index <= first probe pulse (step {FIRST_PULSE_STEP}); post-probe single frames "
            "leak mu and would let a policy re-derive mu without history.",
            "the three behavioral signatures (reveal-speed Spearman >= 0.8, prep action energy above "
            "no-probe baseline, panel success >= gate-3 bar) are CONJUNCTIVE -- any single signature "
            "is forgeable by silence ladders.",
        ],
    }
    frac = frac_cells / total_cells
    gate_cells = [c for c in key_cells if c["gate_relevant"]]
    ke_ok = frac < KNIFE_EDGE_TARGET and all(c["consistent"] for c in gate_cells)
    accept["KE_knife_edge"] = {
        "PASS": bool(ke_ok),
        "fractional_cells": frac_cells, "total_cells": total_cells,
        "fraction": round(frac, 4), "target": KNIFE_EDGE_TARGET,
        "baseline_audit_fraction": round(KNIFE_EDGE_BASELINE, 4),
        "census_note": "census over the 41 mu-agnostic zoo plans x 4 anchors (comparable to the audit's 40x4)",
        "key_cells": key_cells,
        "gate_relevant_cells_all_consistent": bool(all(c["consistent"] for c in gate_cells)),
        "consistency_note": (
            "acceptance requires consistency (|groupA - groupB| <= 0.25) for the gate-relevant "
            "cells (oracle, best_fixed); best-ladder cells are reported as diagnostics "
            "(ladders sit on band edges by construction)."
        ),
    }
    oracle_anchor_ok = all(c["fresh_success"] >= 0.9 for c in fresh_oracle)
    probe_ok = leak["probe_pulses"]["r2_raw_history"] >= 0.9
    bin_oracle_ok = medium["oracle_validated"] >= 0.9
    crawl_ok = all(c["clearly_worse"] for c in crawl_vs_oracle)
    accept["I5_integrity"] = {
        "PASS": bool(oracle_anchor_ok and probe_ok and bin_oracle_ok and crawl_ok),
        "anchor_oracle_fresh_seeds": fresh_oracle,
        "anchor_oracle_all_geq_0.9": bool(oracle_anchor_ok),
        "medium_bin_oracle_validated": medium["oracle_validated"],
        "medium_bin_oracle_geq_0.9": bool(bin_oracle_ok),
        "probe_r2_raw_history": leak["probe_pulses"]["r2_raw_history"],
        "no_probe_r2_raw_history": leak["no_probe"]["r2_raw_history"],
        "probe_r2_geq_0.9": bool(probe_ok),
        "always_slow_vs_oracle": crawl_vs_oracle,
        "reward_tension_ok": bool(crawl_ok),
    }
    all_pass = all(v["PASS"] for v in accept.values())

    success_matrix = {
        plan_names[i]: {f"mu_{design.levels[j].mu:g}": round(float(succ[i, j]), 3) for j in range(n_levels)}
        for i in range(len(plan_names))
    }
    result.update({
        "elapsed_s": round(time.time() - t0, 1),
        "acceptance": accept, "all_pass": bool(all_pass),
        "anchor_panel": {
            "seeds_per_level": n_anchor, "plans": len(plan_names),
            "success_matrix": success_matrix,
            "oracle_plan_per_level": oracle_name,
            "best_fixed_plan": plan_names[best_fixed_idx],
            "best_fixed_mean_success": round(float(succ[best_fixed_idx].mean()), 4),
            "best_ladder_plan": plan_names[best_ladder_idx],
            "best_ladder_mean_success": round(float(succ[best_ladder_idx].mean()), 4),
        },
        "medium_bin": medium, "full_bin": full, "probe_leak": leak,
        "gate3_bar_recomputed": round(medium["best_fixed_all_validated"] + 0.5 * max(medium["voi_validated"], 0.0), 4),
    })
    return result


def adjust_knobs(knobs: Knobs, accept: dict[str, Any]) -> tuple[Knobs, str]:
    """Rule-based knob adjustment from the failure pattern (max 2 moves)."""
    moves = []
    j, hw, reveal = knobs.jitter_d_m, knobs.obstacle_half_width, knobs.reveal_distance
    pr, cp = knobs.pass_reward, knobs.collision_penalty
    d_knots = list(knobs.d_knots)
    p1 = accept["P1_reward_alignment"]
    if p1["PASS"] and (p1["chosen_pass_reward"] != pr or p1["chosen_collision_penalty"] != cp):
        pr, cp = p1["chosen_pass_reward"], p1["chosen_collision_penalty"]
        moves.append(f"rewards -> ({pr},{cp}) from repricing search")
    # deadline-vs-dodge pinch at the top thetas: pull the hazard closer
    for entry in accept["I5_integrity"]["anchor_oracle_fresh_seeds"]:
        if entry["fresh_success"] < 0.9:
            idx = {0.55: 1, 0.85: 2, 1.15: 3}.get(entry["level_mu"])
            if idx is not None and d_knots[idx] > d_knots[idx - 1] + 3.0:
                d_knots[idx] = round(d_knots[idx] - 2.0, 1)
                moves.append(f"d_knots[{idx}] -> {d_knots[idx]} (theta mu={entry['level_mu']} oracle pinch)")
    if not accept["P3_theta1_unavoidability"]["PASS"]:
        hw = min(hw + 0.15, 1.45)
        moves.append(f"obstacle_half_width -> {hw}")
    if not accept["P2_anti_ladder_and_conditional_voi"]["ladder_leq_simple_fixed"]:
        j = j + 1.0
        moves.append(f"jitter up -> {j}")
    elif (not accept["KE_knife_edge"]["PASS"]) or (not accept["I5_integrity"]["medium_bin_oracle_geq_0.9"]):
        j = max(round(j * 0.6, 2), 0.75)
        moves.append(f"jitter down -> {j}")
    if accept["P2_anti_ladder_and_conditional_voi"]["ladder_leq_simple_fixed"] and \
            not accept["P2_anti_ladder_and_conditional_voi"]["voi_target_met"] and j <= 1.0:
        reveal = max(reveal - 0.5, 9.0)
        moves.append(f"reveal -> {reveal}")
    new = dataclasses.replace(knobs, iteration=knobs.iteration + 1, jitter_d_m=j,
                              obstacle_half_width=hw, reveal_distance=reveal,
                              pass_reward=pr, collision_penalty=cp, d_knots=tuple(d_knots),
                              note="; ".join(moves) if moves else "no rule fired")
    return new, "; ".join(moves) if moves else "no rule fired"


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


def final_spec_payload(mod_c, knobs: Knobs, final: dict[str, Any]) -> dict[str, Any]:
    """The actual task spec: every knob needed to regenerate the family."""
    variant = make_variant(mod_c, knobs)
    return {
        "family_id": "B2K2_final (B2 continuous-mu + K2 reveal-10 + adversarial repairs)",
        "env_knobs": {
            "track_kind": "circle", "track_radius_m": 900.0, "track_width_m": 5.0, "dt_s": 0.02,
            "initial_speed_mps": 8.0, "speed_range": [8.0, 8.0], "friction_limited_speed": False,
            "beta_target_range": [0.40, 0.40],
            "max_steps": knobs.max_steps, "deadline_s": round(knobs.max_steps * 0.02, 2),
            "perception_reveal_distance_m": knobs.reveal_distance,
            "obstacle_half_width_m": knobs.obstacle_half_width,
            "required_lateral_offset_m": round(0.90 + knobs.obstacle_half_width + 0.30, 3),
            "finish_on_pass": True, "finish_pass_distance_m": 2.0,
            "pass_reward": knobs.pass_reward, "collision_penalty": knobs.collision_penalty,
            "all_non_mu_randomization": "pinned to 1.0 / 0.0 (degenerate)",
        },
        "scenario_family": {
            "mu_domain": [0.25, 1.15],
            "theta_anchors_mu": [knobs.mu1, 0.55, 0.85, 1.15],
            "mu_to_distance_knots": {"mu": [0.30, 0.55, 0.85, 1.15], "d_m": list(knobs.d_knots)},
            "knot_retune_note": (
                "B2 top knots (49, 62) are reveal-10 infeasible (theta4 deadline floor above the "
                "in-env dodge ceiling ~11 m/s at mu=1.15); retuned to keep a nonempty feasible "
                "entry-speed band at every theta under jitter."
            ),
            "design_oracle_speed_knots": {"mu": [0.30, 0.55, 0.85, 1.15], "v_mps": list(knobs.v_oracle_knots)},
            "interpolation": "piecewise linear, linear extrapolation outside",
            "distance_jitter": {
                "law": "d = d_of_mu(mu) + eps, eps ~ U(-J, J) per episode",
                "J_m": knobs.jitter_d_m,
                "floor_m": knobs.reveal_distance + 5.0,
                "purpose": "P2 anti-ladder: breaks the exact mu<->d inversion (silence is no longer mu)",
            },
            "obstacle_lateral_offset": "centerline-compensated per episode: R - sqrt(R^2 - d^2)",
            "prior_bins": {"medium_pm0.20": list(MEDIUM_BIN), "full_pm0.45": list(FULL_BIN)},
        },
        "gate_protocol": {
            "free_prior_control_arm": (
                "any gate run MUST include a control arm where the policy receives the +/-0.2 mu bin "
                "as a free observation constant; the bin-aware best fixed plan "
                f"({final['medium_bin']['best_fixed_all_plan']}, validated "
                f"{final['medium_bin']['best_fixed_all_validated']}) is its scripted ceiling -- a "
                "'self-identifying' policy that only matches this ceiling has learned a bin hedge, "
                "not identification."
            ),
            "measurement_anchor": (
                f"hidden-swap / wrong-history comparisons anchored at frame <= step {FIRST_PULSE_STEP} "
                "(before the first probe pulse); measured pre-pulse anchor-frame R^2 = "
                f"{final['probe_leak']['probe_pulses']['r2_anchor_frame_pre_pulse']}, post-probe final "
                f"frame R^2 = {final['probe_leak']['probe_pulses']['r2_final_frame_post_probe']}"
            ),
            "signatures_conjunctive": [
                "S1 reveal-crossing speed Spearman(speed, mu) >= 0.8 across the panel",
                "S2 preparation-segment action energy above the no-probe baseline",
                f"S3 panel success >= gate-3 bar = best_fixed_validated + 0.5*VoI_validated = "
                f"{final['gate3_bar_recomputed']}",
                "ALL THREE must hold simultaneously (each alone is ladder-forgeable).",
            ],
        },
        "env_feature_needs": [
            "mu-conditional obstacle distance sampling WITH a noise term in ONE config "
            "(e.g. obstacle.distance_from_mu knots + obstacle.distance_jitter); currently a "
            "per-episode mixture of degenerate configs",
            "per-episode centerline compensation tied to the sampled distance "
            "(lateral_offset = R - sqrt(R^2 - d^2)); currently computed at the script level",
            "independent initial_speed_range decoupled from speed_ref (inherited gap)",
            "reward speed target decoupled from speed_ref (inherited gap)",
        ],
        "seed_streams": {
            "base": SEED_BASE,
            "anchor_panel": "20260615*10 + level*1000 + k (k 0..15; key-cell groups k 100.. / 200..)",
            "bins": "20260615*10 + offset(50000 medium / 90000 full) + 17*point + 1000*k (+100000 val)",
            "probe": "20260615*100 + mode*10000 + episode",
            "jitter": "U(-J,J) from default_rng([20260615, 777, rollout_seed])",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-iters", type=int, default=3)
    parser.add_argument("--anchor-seeds", type=int, default=16)
    parser.add_argument("--keycell-seeds", type=int, default=8)
    parser.add_argument("--escape-seeds", type=int, default=8)
    parser.add_argument("--bin-points", type=int, default=12)
    parser.add_argument("--sel-seeds", type=int, default=3)
    parser.add_argument("--val-seeds", type=int, default=3)
    parser.add_argument("--cem-pop", type=int, default=12)
    parser.add_argument("--cem-iters", type=int, default=3)
    parser.add_argument("--probe-episodes", type=int, default=160)
    parser.add_argument("--jitter", type=float, default=2.0)
    parser.add_argument("--reveal", type=float, default=10.0)
    parser.add_argument("--half-width", type=float, default=1.25)
    parser.add_argument("--pass-reward", type=float, default=40.0)
    parser.add_argument("--collision-penalty", type=float, default=60.0)
    args = parser.parse_args()
    if args.quick:
        args.max_iters, args.anchor_seeds, args.keycell_seeds, args.escape_seeds = 1, 4, 4, 2
        args.bin_points, args.sel_seeds, args.val_seeds = 4, 2, 2
        args.cem_pop, args.cem_iters, args.probe_episodes = 6, 2, 40

    started = time.time()
    mod_b = load_module(TASK_B_SCRIPT, "voi_commitment_task_design")
    mod_c = load_module(COND_SCRIPT, "voi_conditional_prior")
    mod_audit = load_module(AUDIT_SCRIPT, "voi_commitment_adversarial_audit")
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    knobs = Knobs(jitter_d_m=args.jitter, reveal_distance=args.reveal,
                  obstacle_half_width=args.half_width, pass_reward=args.pass_reward,
                  collision_penalty=args.collision_penalty, note="initial")
    rows_out: list[dict[str, Any]] = []
    iterations: list[dict[str, Any]] = []
    final = None
    for it in range(1, args.max_iters + 1):
        print(f"[iter {it}/{args.max_iters}] knobs: jitter={knobs.jitter_d_m} reveal={knobs.reveal_distance} "
              f"hw={knobs.obstacle_half_width} pass={knobs.pass_reward} col={knobs.collision_penalty}")
        res = measure_iteration(mod_b, mod_c, mod_audit, knobs, args, rows_out)
        status = {k: v["PASS"] for k, v in res["acceptance"].items()}
        print(f"  acceptance: {status} | all_pass={res['all_pass']} | {res['elapsed_s']}s")
        iterations.append(res)
        final = res
        if res["all_pass"]:
            # if the repricing chose different rewards than the run, do one confirming
            # iteration at the chosen rewards only when identity check is unavailable
            break
        if it < args.max_iters:
            knobs, moves = adjust_knobs(knobs, res["acceptance"])
            print(f"  knob moves: {moves}")

    from autodrift.artifacts import utc_timestamp, write_csv_rows

    rows_csv = RUN_DIR / "episode_rows.csv"
    write_csv_rows(rows_csv, rows_out)

    final_knobs = Knobs(**{**final["knobs"]})
    if final["acceptance"]["P1_reward_alignment"]["PASS"]:
        final_knobs = dataclasses.replace(
            final_knobs,
            pass_reward=final["acceptance"]["P1_reward_alignment"]["chosen_pass_reward"],
            collision_penalty=final["acceptance"]["P1_reward_alignment"]["chosen_collision_penalty"],
        )
    payload = {
        "protocol": "feasibility_audit_selfid_task_final_spec",
        "generated_by": "scripts/feasibility_audit/selfid_task_final_spec.py",
        "generated_at_utc": utc_timestamp(),
        "claim_boundary": CLAIM_BOUNDARY,
        "builds_on": {
            "task_b_design": "experiments/feasibility_audit/voi_commitment_task_design.json",
            "adversarial_audit": "experiments/feasibility_audit/voi_commitment_adversarial_audit.json",
            "conditional_prior": "experiments/feasibility_audit/voi_conditional_prior.json",
        },
        "final_spec": final_spec_payload(mod_c, final_knobs, final),
        "acceptance_table": final["acceptance"],
        "all_acceptance_pass": final["all_pass"],
        "iteration_log": [
            {"iteration": r["knobs"]["iteration"], "knobs": r["knobs"],
             "acceptance_pass": {k: v["PASS"] for k, v in r["acceptance"].items()},
             "all_pass": r["all_pass"],
             "voi_medium_validated": r["medium_bin"]["voi_validated"],
             "knife_edge_fraction": r["acceptance"]["KE_knife_edge"]["fraction"],
             "p3_min_deficit_m": r["acceptance"]["P3_theta1_unavoidability"]["min_pointmass_eta1_deficit_m"],
             "elapsed_s": r["elapsed_s"]}
            for r in iterations
        ],
        "final_iteration_detail": final,
        "panel_args": {k: getattr(args, k) for k in
                       ("anchor_seeds", "keycell_seeds", "escape_seeds", "bin_points", "sel_seeds",
                        "val_seeds", "cem_pop", "cem_iters", "probe_episodes")},
        "elapsed_s": round(time.time() - started, 1),
        "artifacts": {"episode_rows_csv": str(rows_csv), "results_json": str(RESULTS_JSON)},
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")
    print(f"results -> {RESULTS_JSON}")
    print(f"episode rows -> {rows_csv} ({len(rows_out)} rows)")
    print(
        "HEADLINE: all_pass=" + str(final["all_pass"]) + " | " +
        ", ".join(f"{k.split('_')[0]}={'PASS' if v['PASS'] else 'FAIL'}" for k, v in final["acceptance"].items()) +
        f" | VoI(medium)={final['medium_bin']['voi_validated']:.3f} | "
        f"knife-edge={final['acceptance']['KE_knife_edge']['fraction']:.3f} | "
        f"elapsed {time.time() - started:.0f}s"
    )


if __name__ == "__main__":
    main()
