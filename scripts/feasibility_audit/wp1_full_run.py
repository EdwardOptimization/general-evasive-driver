"""WP1 full-run orchestrator (harness milestone M3216): the pre-registered
modular-belief substitution experiment (Phase-2 plan WP1, C2 + C3 learning
gate) on family #1 only (M3215 G-A fallback routing).

Plan anchors: docs/research-plan-phase2-capability-boundary-tracking.md WP1
(review-hardened criteria), docs/m3215-wp0-degraded-sweep-bridge-validation.md
Section 7 (eligible cells frozen = F1 {delay5, delay12, delay25, noise0.05}),
docs/selfid-belief-decomposition-2026-06.md (5 s familiarization prefix as a
standard fixture; vehicle RLS; L4 class-prior scope), and the stage-1
infrastructure (wp1_data_pipeline.py, wp1_estimator_trainer.py,
experiments/feasibility_audit/wp1_seed_streams.json).

Pre-registration: experiments/feasibility_audit/wp1_prereg.json is REQUIRED
for --full and is echoed into summary.json before any verdict is computed.
The construction pilot (--pilot) runs ONLY on the substitution SELECTION
stream (subst_sel) to fix two construction constants (the standard-block
deadline allowance and the C3 reaction budget) over declared grids before the
prereg freeze -- construction criteria are distinct from the tested readouts
(family-2 design discipline).

Episode construction (substitution evaluation, all arms paired on identical
episodes; the stage-2 freeze of the handover design that stage 1 deferred):
  [prefix, 5 s scripted] the wp1_data_pipeline standard sub-limit
      familiarization prefix (mu-free force caps + lateral dither, vehicle RLS
      fixture; vehicle randomization OFF = the frozen M3215 measurement
      condition).
  [offset 40 m, stage-2 revision] the obstacle prefix offset is set to the
      MEASURED nominal prefix travel (39.85 m, mu- and seed-invariant because
      the prefix is mu-free and the dither is lateral-only; rounded to 40 m)
      for BOTH training data and evaluation, replacing the stage-1 60 m
      value: at handover the obstacle then sits at ~d_base + 0.15 m, so the
      controller's internal distance/deadline bookkeeping (which starts at
      handover) is consistent with the true geometry and the B2K2 commitment
      tension is preserved. Measured stage-1 defect this fixes: with the 60 m
      offset, ~20 m of unmodeled distance remain at handover and every
      v-target-law arm (oracle included) decelerates prematurely and times
      out under a B2K2-equivalent deadline.
  [deadline] env max_steps = 250 (prefix) + ALLOWANCE + 285 (B2K2 deadline);
      ALLOWANCE pilot-frozen over the declared grid {0, 25, 50} (first value
      with delay5 sel-stream oracle >= 0.5 and prize >= 0.15).

C3 block (excitation-to-decision gap variant, plan WP1.5): the scripted
c3_ramp_release behavior (excitation < 1.0 s task-clock, then sub-limit
cruise) drives until the reveal; the controller takes over AT the reveal with
per-episode deadline = scripted-probe reveal tick + REACTION_BUDGET (pilot
grid {90, 100, 110, 125, 150}, argmax sel-stream prize subject to oracle >=
0.5, tie -> smaller). Belief-free C3 floor candidates: no-belief handover +
constant-mu handovers {0.45, 0.70, 0.95} (selection on subst_sel, best ->
validation).

Arms (per cell): floor = max(best belief-free seeker over the frozen M3215
per-cell tau grid x rates x backoffs x dv, best fixed plan), selection on
subst_sel (12 mu x 2 seeds), validation on subst_val (12 mu x 20 seeds = 240
episodes, episode-paired with every other arm); matched oracle = per-mu
oracle with per-point dv selected on subst_sel; injected arms = the cell's
best-sel seeker config + BeliefInjector(estimator), injection at the decision
tick (the frozen WP1.3 hook), for 5 estimator arms x 8 training seeds.

Pre-registered primary (frozen in wp1_prereg.json): L3_GRU recaptures >= 50%
of the re-measured matched prize in >= 3 of the 4 eligible cells, each cell
with the one-sided 97.5% lower bound of the episode-paired (arm - floor) mean
difference > 0 under a two-way (episode + training-seed cluster) SE. All
other arms exploratory; L0-succeeds and all-arms-fail routes per the plan.

Seed streams (stage-2 freeze, disjoint from train/sel/val/smoke_eval):
substitution sel = role offset +200000, substitution val = +900000, episode
index i = block + 100*point + k with block 0 (standard), 10000 (C3), 50000
(L4 exploratory block, subst_val only). Estimator training seeds 0..7
(torch seed 20270101 + 1000*arm_index + 17*train_seed).

Hard constraints: pure CPU (torch single-thread per worker), zero driving-
policy training, deterministic seeds, managed-progress resume
(progress.jsonl), no git operations.

Run:
    PYTHONPATH=src python scripts/feasibility_audit/wp1_full_run.py --pilot
    PYTHONPATH=src python scripts/feasibility_audit/wp1_full_run.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/wp1_full_run.py --full
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts/feasibility_audit"
PREREG_JSON = REPO / "experiments/feasibility_audit/wp1_prereg.json"
M3215_SUMMARY = REPO / "runs/feasibility_audit/wp0_degraded_sweep/summary.json"
DEFAULT_RUN_DIR = REPO / "runs/feasibility_audit/wp1_full"
PILOT_RUN_DIR = REPO / "runs/feasibility_audit/wp1_construction_pilot"

sys.path.insert(0, str(SCRIPTS))

SEED_BASE = 20270101
SUBST_SEL_OFFSET = 200_000
SUBST_VAL_OFFSET = 900_000
C3_BLOCK = 10_000
L4_BLOCK = 50_000

B2K2_TASK_STEPS = 285          # frozen B2K2_final deadline (5.7 s)
PREFIX_OFFSET_M = 40.0         # stage-2 frozen obstacle offset = measured prefix travel
ALLOWANCE_GRID = (0, 25, 50)
C3_BUDGET_GRID = (90, 100, 110, 125, 150)
C3_PROBE_MAX_STEPS = 1600
PILOT_ORACLE_BAR = 0.5
PILOT_PRIZE_BAR = 0.15

ELIGIBLE_CELL_IDS = ("delay5", "delay12", "delay25", "noise0.05")
SEEKER_RATES = (2000.0, 6000.0, 20000.0)
SEEKER_BACKOFFS = (0.06, 0.15)
SEEKER_DVS = (0.0, 0.75)
ORACLE_DVS = (-0.5, 0.0, 0.5, 1.0)
FIXED_SPEED_GRID = (4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5)
FIXED_RAMP_GRID = ((0.35, 1.0), (0.70, 1.0), (1.00, 0.6))
C3_FLOOR_CONST_MUS = (0.45, 0.70, 0.95)

ARMS = ("L0_frame", "L2_window_25", "L2_window_50", "L2_window_100", "L3_GRU")
HISTORY_ARMS = ("L2_window_25", "L2_window_50", "L2_window_100", "L3_GRU")
PRIMARY_ARM = "L3_GRU"
N_TRAIN_SEEDS = 8
RECAPTURE_BAR = 0.5
PRIMARY_CELLS_REQUIRED = 3
TOST_BOUND = 0.05
Z_ONESIDED_975 = 1.959963984540054
Z_TWOSIDED_90 = 1.6448536269514722

DATA_COUNTS_FULL = {"train": 240, "sel": 40, "val_offgrid": 24, "c3_train": 160, "c3_val": 24}
VAL_KS = 20
SEL_KS = 2
L4_KS = 6
L4_CELL = "delay5"

CLAIM_BOUNDARY = (
    "Feasibility-audit WP1 modular-belief substitution measurement only (Phase-2 manual "
    "takeover, harness milestone M3216): capacity/compute-matched supervised mu estimators "
    "are substituted into the SAME scripted seeker family used by the regime measurements on "
    "the prefix-carrying B2K2_final construction under the frozen M3215 eligible degradation "
    "cells, against a re-measured belief-free floor and matched per-mu oracle. Auxiliary "
    "measurement; the engineering incumbent and ActiveSafetyReflexDriver are unchanged. "
    "No driver promotion, validation ranking, repair-success, gate-validity, paper, "
    "high-fidelity, robustness-result, feasibility-proof, or self-ID capability claim."
)

# --------------------------------------------------------------------- globals

MODS: dict[str, Any] | None = None
PIPE = None
TRAINER = None
CTRL_CLS = None
DESIGN = None
BD_CTRL_CLS = None


def _ensure_mods() -> None:
    global MODS, PIPE, TRAINER, CTRL_CLS, DESIGN, BD_CTRL_CLS
    if MODS is not None:
        return
    import torch

    torch.set_num_threads(1)
    import wp1_data_pipeline as pipe
    import wp1_estimator_trainer as trainer

    PIPE = pipe
    TRAINER = trainer
    MODS = pipe.load_stack()
    # stage-2 frozen construction: obstacle offset = measured nominal prefix
    # travel (applies to BOTH data collection and evaluation; single source)
    pipe.PREFIX_DIST_OFFSET_M = PREFIX_OFFSET_M
    reg, mod_b, deg = MODS["reg"], MODS["mod_b"], MODS["deg"]
    _, CTRL = deg.make_classes(reg)
    CTRL_CLS = CTRL
    DESIGN = reg.make_design(mod_b, pipe.REVEAL)
    _, BD_CTRL_CLS = MODS["bd"].make_classes(reg, deg)


def cell_by_id(cell_id: str) -> dict[str, Any]:
    return {c["cell_id"]: c for c in MODS["wp0"].CELLS}[cell_id]


def cell_index(cell_id: str) -> int:
    return ELIGIBLE_CELL_IDS.index(cell_id)


def subst_seed(cell_id: str, phase: str, point: int, k: int, block: int = 0) -> int:
    off = SUBST_SEL_OFFSET if phase == "sel" else SUBST_VAL_OFFSET
    return (PIPE.EPISODE_SEED_BASE + cell_index(cell_id) * 1_000_000 + off
            + block + 100 * int(point) + int(k))


def mu_grid() -> list[float]:
    _ensure_mods()
    return PIPE.mu_grid()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


# ----------------------------------------------------------------- controllers


class ConstInjector:
    """Belief-free constant-mu injector (a fixed plan in belief space)."""

    def __init__(self, value: float):
        self.value = float(value)

    def observe(self, obs: np.ndarray) -> None:  # noqa: ARG002
        return None

    def estimate(self) -> float:
        return self.value


def make_injector(spec: dict[str, Any] | None):
    if spec is None:
        return None
    if spec["kind"] == "const":
        return ConstInjector(spec["value"])
    import torch

    model = TRAINER.build_arm(spec["arm"])
    model.load_state_dict(torch.load(spec["path"], map_location="cpu"))
    return TRAINER.BeliefInjector(model, spec["arm"])


def build_controller(spec: dict[str, Any], mu: float, injector=None):
    reg, mod_b = MODS["reg"], MODS["mod_b"]
    interp = MODS["interp"]
    kind = spec["type"]
    if kind == "seeker":
        return CTRL_CLS(mod_b, interp, DESIGN, spec["name"], smooth_window=int(spec["w"]),
                        mode="seeker", ramp_rate=spec["rate"], tau=spec["tau"],
                        backoff=spec["backoff"], strategy="hold", dv=spec["dv"],
                        injected_belief=injector)
    if kind == "oracle":
        return CTRL_CLS(mod_b, interp, DESIGN, spec["name"], mode="oracle",
                        mu_true=mu, dv=spec["dv"])
    if kind == "fixed_speed":
        plan = mod_b.PlanSpec(name=spec["name"], v_entry=float(spec["v"]),
                              brake_to=None, steer_cap=0.85)
        return mod_b.CommitmentController(plan, DESIGN)
    if kind == "fixed_ramp":
        return CTRL_CLS(mod_b, interp, DESIGN, spec["name"], mode="fixed_ramp",
                        fixed_frac=spec["frac"], fixed_hold_s=spec["hold"])
    raise ValueError(kind)


def floor_seeker_specs(cell: dict[str, Any], cal: dict[str, Any]) -> list[dict[str, Any]]:
    variants = MODS["wp0"].tau_variants(cell["noisy"], cal)
    specs = []
    for r in SEEKER_RATES:
        for w, tau in variants:
            for d in SEEKER_BACKOFFS:
                for v in SEEKER_DVS:
                    specs.append({"type": "seeker", "rate": r, "w": w, "tau": tau,
                                  "backoff": d, "dv": v,
                                  "name": f"seeker_r{r:g}_w{w}_t{tau:g}_d{d:g}_v{v:+g}"})
    return specs


def fixed_specs() -> list[dict[str, Any]]:
    specs = [{"type": "fixed_speed", "v": v, "name": f"fixed_v{v:g}"} for v in FIXED_SPEED_GRID]
    specs += [{"type": "fixed_ramp", "frac": f, "hold": h, "name": f"fixedramp_f{f:g}_h{h:g}"}
              for f, h in FIXED_RAMP_GRID]
    return specs


def c3_seeker_spec(cell: dict[str, Any], cal: dict[str, Any]) -> dict[str, Any]:
    """Frozen C3 handover config: rate 20000, backoff 0.06, dv 0; detector =
    the cell's calibrated (window, tau) pair with the smallest tau."""
    variants = MODS["wp0"].tau_variants(cell["noisy"], cal)
    w, tau = min(variants, key=lambda v: (v[1], v[0]))
    return {"type": "seeker", "rate": 20000.0, "w": w, "tau": tau, "backoff": 0.06,
            "dv": 0.0, "name": f"c3_handover_r20000_w{w}_t{tau:g}"}


# -------------------------------------------------------------------- episodes


def make_eval_env(cell: dict[str, Any], mu: float, seed: int, variant: str,
                  vehicle_rand: bool, max_steps: int):
    reg, mod_b, deg, wp0 = MODS["reg"], MODS["mod_b"], MODS["deg"], MODS["wp0"]
    interp = MODS["interp"]
    d_base = PIPE.jittered_distance(interp, reg, mu, seed)
    d_total = d_base + PIPE.PREFIX_DIST_OFFSET_M + (PIPE.C3_EXTRA_DIST_M if variant == "c3" else 0.0)
    level = mod_b.LevelSpec(mu=mu, d_lo=d_total, d_hi=d_total,
                            entry_speed=reg.v_star(interp, mu))
    cfg = mod_b.level_env_config(DESIGN, level)
    cfg["max_steps"] = int(max_steps)
    if vehicle_rand:
        scales = PIPE.sample_vehicle_scales(seed)
        cfg["randomization"].update({
            "mass_scale_range": [scales["mass_scale"]] * 2,
            "brake_scale_range": [scales["brake_scale"]] * 2,
            "drive_scale_range": [scales["drive_scale"]] * 2,
            "tire_stiffness_scale_range": [scales["tire_stiffness_scale"]] * 2,
            "actuator_tau_scale_range": [scales["actuator_tau_scale"]] * 2,
        })
    return wp0.make_degraded_env_cfg(deg, cfg, cell["degradation"]), d_total


def _bucket(info, term: bool, trunc: bool) -> str:
    return MODS["mod_b"].outcome_bucket_from_info(info, terminated=term, truncated=trunc)


def run_std_episode(cell: dict[str, Any], mu: float, seed: int, ctrl_spec: dict[str, Any],
                    injector_spec: dict[str, Any] | None, max_steps: int) -> dict[str, Any]:
    """Prefix (scripted, injector fed each frame exactly once) -> handover."""
    env, _ = make_eval_env(cell, mu, seed, "standard", False, max_steps)
    behavior = PIPE.BehaviorScript(MODS, "standard", seed)
    injector = make_injector(injector_spec)
    controller = build_controller(ctrl_spec, mu, injector)
    if hasattr(controller, "reset"):
        controller.reset()
    ep_return = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        term = trunc = False
        info: dict[str, Any] = {}
        for t in range(PIPE.PREFIX_STEPS):
            if injector is not None:
                injector.observe(np.asarray(obs, dtype=np.float64))
            action = behavior.act(t, np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
            if term or trunc:
                break
        while not (term or trunc):
            action = controller.act(np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
        bucket = _bucket(info, term, trunc)
    finally:
        env.close()
    mu_injected = getattr(controller, "mu_injected", None)
    return {
        "seed": int(seed), "mu": round(float(mu), 4),
        "success": bucket == "success_obstacle_pass", "bucket": bucket,
        "collided": bucket == "collision_failure",
        "timeout": bucket == "max_steps_noncompletion",
        "return": round(ep_return, 3),
        "mu_hat": getattr(controller, "mu_hat", None),
        "censored": bool(getattr(controller, "censored", False)),
        "mu_injected": (None if mu_injected is None else round(float(mu_injected), 4)),
        "injection_step": int(getattr(controller, "injection_step", -1)),
    }


def run_c3_probe(cell: dict[str, Any], mu: float, seed: int) -> int:
    """Scripted-only c3 rollout; returns the reveal frame index (-1 invalid)."""
    env, _ = make_eval_env(cell, mu, seed, "c3", False, C3_PROBE_MAX_STEPS)
    behavior = PIPE.BehaviorScript(MODS, "c3", seed)
    try:
        obs, _ = env.reset(seed=seed)
        for t in range(C3_PROBE_MAX_STEPS):
            if float(np.asarray(obs)[44]) > 0.5:
                return t
            action = behavior.act(t, np.asarray(obs, dtype=np.float64))
            obs, _, term, trunc, _ = env.step(np.asarray(action, dtype=np.float64))
            if term or trunc:
                return -1
    finally:
        env.close()
    return -1


def run_c3_episode(cell: dict[str, Any], mu: float, seed: int, ctrl_spec: dict[str, Any],
                   injector_spec: dict[str, Any] | None, reveal_tick: int,
                   budget_steps: int) -> dict[str, Any]:
    """Scripted c3 behavior to the reveal tick, then controller handover with a
    per-episode deadline = reveal tick + budget."""
    max_steps = int(reveal_tick + budget_steps)
    env, _ = make_eval_env(cell, mu, seed, "c3", False, max_steps)
    behavior = PIPE.BehaviorScript(MODS, "c3", seed)
    injector = make_injector(injector_spec)
    if ctrl_spec["type"] == "oracle":
        controller = build_controller(ctrl_spec, mu)
    else:
        controller = build_controller(ctrl_spec, mu, injector)
    if hasattr(controller, "reset"):
        controller.reset()
    ep_return = 0.0
    try:
        obs, _ = env.reset(seed=seed)
        term = trunc = False
        info: dict[str, Any] = {}
        for t in range(max_steps):
            if float(np.asarray(obs)[44]) > 0.5:
                break
            if injector is not None and ctrl_spec["type"] != "oracle":
                injector.observe(np.asarray(obs, dtype=np.float64))
            action = behavior.act(t, np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
            if term or trunc:
                break
        while not (term or trunc):
            action = controller.act(np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
        bucket = _bucket(info, term, trunc)
    finally:
        env.close()
    mu_injected = getattr(controller, "mu_injected", None)
    return {
        "seed": int(seed), "mu": round(float(mu), 4),
        "success": bucket == "success_obstacle_pass", "bucket": bucket,
        "collided": bucket == "collision_failure",
        "timeout": bucket == "max_steps_noncompletion",
        "return": round(ep_return, 3),
        "reveal_tick": int(reveal_tick),
        "mu_injected": (None if mu_injected is None else round(float(mu_injected), 4)),
        "injection_step": int(getattr(controller, "injection_step", -1)),
    }


# ------------------------------------------------------------------- l4 block


def kappa_bin(x: float, width: float = 0.15) -> float:
    return float(np.clip(round(x / width) * width, 0.4, 2.5))


def run_l4_episode(cell: dict[str, Any], mu: float, seed: int, arm: str,
                   seeker_spec: dict[str, Any], max_steps: int) -> dict[str, Any]:
    bd = MODS["bd"]
    reg, mod_b = MODS["reg"], MODS["mod_b"]
    interp = MODS["interp"]
    scales = PIPE.sample_vehicle_scales(seed)
    kb_t, kd_t = bd.true_kappas(scales)
    rls_frames = {"rls_5s_uniform": PIPE.PREFIX_STEPS, "rls_1s_uniform": 50,
                  "rls_1s_classprior": 50, "rls_5s_classprior": PIPE.PREFIX_STEPS}
    env, _ = make_eval_env(cell, mu, seed, "standard", True, max_steps)
    behavior = PIPE.BehaviorScript(MODS, "standard", seed)
    rls = None
    if arm in rls_frames:
        rls = bd.VehicleRLS(prior_sigma_kappa=(0.075 if "classprior" in arm else 0.30),
                            r_noise_ax=max((15.0 * float(cell["degradation"].get("noise_std", 0.0))) ** 2, 0.04))
        if "classprior" in arm:
            rls.theta = np.array([kappa_bin(kd_t) / bd.MASS, kappa_bin(kb_t) / bd.MASS])
    ep_return = 0.0
    kb_hat, kd_hat = 1.0, 1.0
    try:
        obs, _ = env.reset(seed=seed)
        term = trunc = False
        info: dict[str, Any] = {}
        for t in range(PIPE.PREFIX_STEPS):
            if rls is not None and t < rls_frames[arm]:
                rls.update_obs(np.asarray(obs, dtype=np.float64))
            action = behavior.act(t, np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
            if term or trunc:
                break
        if rls is not None:
            kb_hat, kd_hat = rls.kappas
        elif arm == "truth":
            kb_hat, kd_hat = kb_t, kd_t
        belief = bd.Belief(kb_hat, kd_hat)
        controller = BD_CTRL_CLS(mod_b, interp, DESIGN, f"l4_{arm}", mode="seeker",
                                 smooth_window=int(seeker_spec["w"]),
                                 ramp_rate=seeker_spec["rate"], tau=seeker_spec["tau"],
                                 backoff=seeker_spec["backoff"], strategy="hold",
                                 dv=seeker_spec["dv"], belief=belief, rls=False)
        controller.reset()
        belief.set(kb_hat, kd_hat)
        while not (term or trunc):
            action = controller.act(np.asarray(obs, dtype=np.float64))
            obs, r, term, trunc, info = env.step(np.asarray(action, dtype=np.float64))
            ep_return += float(r)
        bucket = _bucket(info, term, trunc)
    finally:
        env.close()
    return {
        "seed": int(seed), "mu": round(float(mu), 4), "arm": arm,
        "success": bucket == "success_obstacle_pass", "bucket": bucket,
        "return": round(ep_return, 3),
        "kappa_b_true": round(kb_t, 4), "kappa_b_hat": round(kb_hat, 4),
        "kappa_b_abs_err": round(abs(kb_hat - kb_t), 4),
        "kappa_d_abs_err": round(abs(kd_hat - kd_t), 4),
    }


# ------------------------------------------------------------------ pool tasks


def task_data_chunk(cell_id: str, specs: list[tuple[float, int, str, str, bool]]) -> list[dict[str, Any]]:
    _ensure_mods()
    cell = cell_by_id(cell_id)
    records = []
    for mu, seed, variant, role, on_grid in specs:
        rec = PIPE.run_episode(MODS, cell, mu, seed, variant, role, False)
        rec["mu_on_grid"] = on_grid
        records.append(rec)
    return records


def task_train(cell_id: str, variant: str, arm: str, train_seed: int, npz_path: str,
               lr_grid: tuple[float, ...], max_epochs: int, model_path: str) -> dict[str, Any]:
    _ensure_mods()
    import torch

    with np.load(npz_path) as z:
        data = {k: z[k] for k in z.files}
    res, model = TRAINER.train_arm(arm, data, train_seed, lr_grid, max_epochs, 10,
                                   variant_filter=(1 if variant == "c3" else 0))
    torch.save(model.state_dict(), model_path)
    res["model_path"] = model_path
    res["variant"] = variant
    return res


def task_std_arm(cell_id: str, arm_name: str, ctrl_spec: dict[str, Any],
                 injector_spec: dict[str, Any] | None, phase: str, ks: list[int],
                 max_steps: int, oracle_dv_by_point: list[float] | None,
                 rows_path: str | None) -> dict[str, Any]:
    _ensure_mods()
    cell = cell_by_id(cell_id)
    rows = []
    for point, mu in enumerate(mu_grid()):
        spec = dict(ctrl_spec)
        if ctrl_spec["type"] == "oracle" and oracle_dv_by_point is not None:
            spec["dv"] = float(oracle_dv_by_point[point])
        for k in ks:
            seed = subst_seed(cell_id, phase, point, k)
            row = run_std_episode(cell, mu, seed, spec, injector_spec, max_steps)
            row.update({"point": point, "k": int(k), "arm": arm_name,
                        "cell": cell_id, "phase": phase})
            rows.append(row)
    if rows_path:
        from autodrift.artifacts import write_csv_rows

        write_csv_rows(Path(rows_path), rows)
    by_point = [float(np.mean([r["success"] for r in rows if r["point"] == p]))
                for p in range(len(mu_grid()))]
    inj = [r for r in rows if r["mu_injected"] is not None]
    return {
        "arm": arm_name, "cell": cell_id, "phase": phase, "n": len(rows),
        "success": round(float(np.mean([r["success"] for r in rows])), 4),
        "return": round(float(np.mean([r["return"] for r in rows])), 4),
        "per_point_success": [round(v, 3) for v in by_point],
        "episode_success": {f"{r['point']}:{r['k']}": (1 if r["success"] else 0) for r in rows},
        "injection_fired_fraction": (round(len(inj) / len(rows), 4) if rows else None),
        "mu_injected_abs_err_mean": (round(float(np.mean([abs(r["mu_injected"] - r["mu"])
                                                          for r in inj])), 4) if inj else None),
        "rows_path": rows_path,
    }


def task_oracle_sel(cell_id: str, ks: list[int], max_steps: int) -> dict[str, Any]:
    """Per-point oracle dv selection on the subst_sel stream."""
    _ensure_mods()
    cell = cell_by_id(cell_id)
    stats: dict[str, list[tuple[float, float]]] = {}
    for dv in ORACLE_DVS:
        spec = {"type": "oracle", "dv": dv, "name": f"oracle_dv{dv:+g}"}
        per_point = []
        for point, mu in enumerate(mu_grid()):
            rows = [run_std_episode(cell, mu, subst_seed(cell_id, "sel", point, k), spec, None,
                                    max_steps) for k in ks]
            per_point.append((float(np.mean([r["success"] for r in rows])),
                              float(np.mean([r["return"] for r in rows]))))
        stats[f"{dv:+g}"] = per_point
    dv_by_point = []
    for point in range(len(mu_grid())):
        best = max(ORACLE_DVS, key=lambda dv: stats[f"{dv:+g}"][point])
        dv_by_point.append(float(best))
    return {"cell": cell_id, "dv_by_point": dv_by_point,
            "sel_stats": {k: [[round(a, 3), round(b, 3)] for a, b in v] for k, v in stats.items()}}


def task_c3_probes(cell_id: str, phase: str, points: list[int], ks: list[int]) -> dict[str, Any]:
    _ensure_mods()
    cell = cell_by_id(cell_id)
    ticks = {}
    for point in points:
        mu = mu_grid()[point]
        for k in ks:
            seed = subst_seed(cell_id, phase, point, k, block=C3_BLOCK)
            ticks[f"{point}:{k}"] = run_c3_probe(cell, mu, seed)
    return {"cell": cell_id, "phase": phase, "ticks": ticks}


def task_c3_arm(cell_id: str, arm_name: str, ctrl_spec: dict[str, Any],
                injector_spec: dict[str, Any] | None, phase: str, ks: list[int],
                budget: int, ticks: dict[str, int], rows_path: str | None) -> dict[str, Any]:
    _ensure_mods()
    cell = cell_by_id(cell_id)
    rows = []
    for point, mu in enumerate(mu_grid()):
        for k in ks:
            tick = int(ticks[f"{point}:{k}"])
            if tick < 0:
                continue
            seed = subst_seed(cell_id, phase, point, k, block=C3_BLOCK)
            row = run_c3_episode(cell, mu, seed, ctrl_spec, injector_spec, tick, budget)
            row.update({"point": point, "k": int(k), "arm": arm_name,
                        "cell": cell_id, "phase": phase, "budget": budget})
            rows.append(row)
    if rows_path:
        from autodrift.artifacts import write_csv_rows

        write_csv_rows(Path(rows_path), rows)
    inj = [r for r in rows if r["mu_injected"] is not None]
    return {
        "arm": arm_name, "cell": cell_id, "phase": phase, "budget": budget, "n": len(rows),
        "success": round(float(np.mean([r["success"] for r in rows])), 4) if rows else None,
        "return": round(float(np.mean([r["return"] for r in rows])), 4) if rows else None,
        "episode_success": {f"{r['point']}:{r['k']}": (1 if r["success"] else 0) for r in rows},
        "injection_fired_fraction": (round(len(inj) / len(rows), 4) if rows else None),
        "mu_injected_abs_err_mean": (round(float(np.mean([abs(r["mu_injected"] - r["mu"])
                                                          for r in inj])), 4) if inj else None),
        "rows_path": rows_path,
    }


def task_l4_arm(arm: str, ks: list[int], seeker_spec: dict[str, Any], max_steps: int,
                rows_path: str | None) -> dict[str, Any]:
    _ensure_mods()
    cell = cell_by_id(L4_CELL)
    rows = []
    for point, mu in enumerate(mu_grid()):
        for k in ks:
            seed = subst_seed(L4_CELL, "val", point, k, block=L4_BLOCK)
            rows.append({**run_l4_episode(cell, mu, seed, arm, seeker_spec, max_steps),
                         "point": point, "k": int(k)})
    if rows_path:
        from autodrift.artifacts import write_csv_rows

        write_csv_rows(Path(rows_path), rows)
    succ = float(np.mean([r["success"] for r in rows]))
    return {
        "arm": arm, "cell": L4_CELL, "n": len(rows),
        "success": round(succ, 4),
        "wilson95": MODS["wp0"].wilson_ci(succ, len(rows)),
        "kappa_b_abs_err_median": round(float(np.median([r["kappa_b_abs_err"] for r in rows])), 4),
        "kappa_d_abs_err_median": round(float(np.median([r["kappa_d_abs_err"] for r in rows])), 4),
        "rows_path": rows_path,
    }


# ------------------------------------------------------------------ statistics


def two_way_diff_stats(arm_eps: dict[int, dict[str, int]], floor_eps: dict[str, int]) -> dict[str, Any]:
    """Episode-paired mean difference of (multi-seed arm) - floor with a
    two-way SE: episode-level SE of the per-episode (seed-mean - floor)
    difference + training-seed cluster SE, combined in quadrature."""
    keys = sorted(set(floor_eps).intersection(*[set(v) for v in arm_eps.values()]))
    seeds = sorted(arm_eps)
    d_e = np.array([np.mean([arm_eps[s][key] for s in seeds]) - floor_eps[key] for key in keys])
    delta = float(d_e.mean())
    se_ep = float(d_e.std(ddof=1) / math.sqrt(len(d_e))) if len(d_e) > 1 else float("nan")
    d_s = np.array([np.mean([arm_eps[s][key] - floor_eps[key] for key in keys]) for s in seeds])
    se_seed = float(d_s.std(ddof=1) / math.sqrt(len(seeds))) if len(seeds) > 1 else 0.0
    se = float(math.sqrt(se_ep ** 2 + se_seed ** 2))
    return {
        "n_episodes": len(keys), "n_seeds": len(seeds),
        "delta": round(delta, 4),
        "se_episode": round(se_ep, 4), "se_seed_cluster": round(se_seed, 4),
        "se_two_way": round(se, 4),
        "lower_975_one_sided": round(delta - Z_ONESIDED_975 * se, 4),
        "per_seed_delta": [round(float(x), 4) for x in d_s],
    }


def paired_arm_arm_stats(a_eps: dict[int, dict[str, int]], b_eps: dict[int, dict[str, int]]) -> dict[str, Any]:
    """Episode-paired (seed-paired) difference of arm A - arm B with the same
    two-way SE; used for the C3 L3 vs L2_100 readout + TOST."""
    seeds = sorted(set(a_eps) & set(b_eps))
    keys = sorted(set.intersection(*[set(a_eps[s]) for s in seeds],
                                   *[set(b_eps[s]) for s in seeds]))
    d_e = np.array([np.mean([a_eps[s][key] for s in seeds])
                    - np.mean([b_eps[s][key] for s in seeds]) for key in keys])
    delta = float(d_e.mean())
    se_ep = float(d_e.std(ddof=1) / math.sqrt(len(d_e))) if len(d_e) > 1 else float("nan")
    d_s = np.array([np.mean([a_eps[s][key] - b_eps[s][key] for key in keys]) for s in seeds])
    se_seed = float(d_s.std(ddof=1) / math.sqrt(len(seeds))) if len(seeds) > 1 else 0.0
    se = float(math.sqrt(se_ep ** 2 + se_seed ** 2))
    ci90 = [round(delta - Z_TWOSIDED_90 * se, 4), round(delta + Z_TWOSIDED_90 * se, 4)]
    return {
        "n_episodes": len(keys), "n_seeds": len(seeds),
        "delta": round(delta, 4), "se_two_way": round(se, 4),
        "lower_975_one_sided": round(delta - Z_ONESIDED_975 * se, 4),
        "ci90": ci90,
        "tost_equivalent": bool(ci90[0] > -TOST_BOUND and ci90[1] < TOST_BOUND),
    }


# ----------------------------------------------------------------------- pilot


def run_pilot(run_dir: Path, workers: int) -> None:
    _ensure_mods()
    wp0 = MODS["wp0"]
    cal = json.loads(M3215_SUMMARY.read_text(encoding="utf-8"))["calibration"]["family1"]
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    probe_arms = [
        {"type": "seeker", "rate": 20000.0, "w": 1, "tau": 0.08, "backoff": 0.06, "dv": 0.0,
         "name": "seeker_r20000_w1_t0.08_d0.06_v+0"},
        {"type": "seeker", "rate": 20000.0, "w": 1, "tau": 0.08, "backoff": 0.06, "dv": 0.75,
         "name": "seeker_r20000_w1_t0.08_d0.06_v+0.75"},
        {"type": "fixed_speed", "v": 6.5, "name": "fixed_v6.5"},
        {"type": "fixed_speed", "v": 9.5, "name": "fixed_v9.5"},
    ]
    ks = list(range(SEL_KS))
    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp1_construction_pilot",
        "stream": "subst_sel ONLY (selection stream; no validation episode consulted)",
        "allowance_grid": list(ALLOWANCE_GRID), "c3_budget_grid": list(C3_BUDGET_GRID),
        "selection_rules": {
            "allowance": "first value in declared order with delay5 oracle >= 0.5 and prize >= 0.15",
            "c3_budget": "argmax delay5 prize subject to oracle >= 0.5; tie -> smaller budget",
        },
        "standard": {}, "c3": {}, "prefix_travel_m": {},
    }
    with ProcessPoolExecutor(max_workers=workers) as pool:
        # prefix travel measurement (scripted prefix only, 4 seeds)
        travels = []
        for k in range(4):
            seed = subst_seed("delay5", "sel", 0, k)
            env, _ = make_eval_env(cell_by_id("delay5"), 0.7, seed, "standard", False, 400)
            try:
                obs, _ = env.reset(seed=seed)
                behavior = PIPE.BehaviorScript(MODS, "standard", seed)
                dist = 0.0
                for t in range(PIPE.PREFIX_STEPS):
                    vx = float(np.asarray(obs)[0]) * 20.0
                    dist += vx * PIPE.DT
                    action = behavior.act(t, np.asarray(obs, dtype=np.float64))
                    obs, _, term, trunc, _ = env.step(np.asarray(action, dtype=np.float64))
                    if term or trunc:
                        break
                travels.append(round(dist, 2))
            finally:
                env.close()
        payload["prefix_travel_m"] = {"samples": travels, "median": float(np.median(travels))}

        for cid in ("delay5", "delay12"):
            payload["standard"][cid] = {}
            for allowance in ALLOWANCE_GRID:
                max_steps = PIPE.PREFIX_STEPS + allowance + B2K2_TASK_STEPS
                futures = {a["name"]: pool.submit(task_std_arm, cid, a["name"], a, None,
                                                  "sel", ks, max_steps, None, None)
                           for a in probe_arms}
                oracle_fut = pool.submit(task_oracle_sel, cid, ks, max_steps)
                arms = {n: f.result() for n, f in futures.items()}
                osel = oracle_fut.result()
                oracle = float(np.mean([max(osel["sel_stats"][f"{dv:+g}"][p][0] for dv in ORACLE_DVS)
                                        for p in range(len(mu_grid()))]))
                floor = max(a["success"] for a in arms.values())
                payload["standard"][cid][f"allowance_{allowance}"] = {
                    "max_steps": max_steps,
                    "oracle_sel": round(oracle, 4), "floor_probe_sel": round(floor, 4),
                    "prize_probe": round(oracle - floor, 4),
                    "arms": {n: a["success"] for n, a in arms.items()},
                }
                print(f"[pilot std] {cid} allow={allowance} oracle={oracle:.3f} "
                      f"floor={floor:.3f} prize={oracle - floor:+.3f}", flush=True)

        for cid in ("delay5", "delay12"):
            probes = pool.submit(task_c3_probes, cid, "sel", list(range(len(mu_grid()))), ks).result()
            ticks = probes["ticks"]
            spec = c3_seeker_spec(cell_by_id(cid), cal[cid])
            payload["c3"][cid] = {"reveal_ticks": ticks}
            for budget in C3_BUDGET_GRID:
                floor_fut = pool.submit(task_c3_arm, cid, "c3_floor_nobelief", spec, None,
                                        "sel", ks, budget, ticks, None)
                oracle_fut = pool.submit(task_c3_arm, cid, "c3_oracle",
                                         {"type": "oracle", "dv": 0.0, "name": "c3_oracle"},
                                         None, "sel", ks, budget, ticks, None)
                floor, oracle = floor_fut.result(), oracle_fut.result()
                payload["c3"][cid][f"budget_{budget}"] = {
                    "oracle_sel": oracle["success"], "floor_nobelief_sel": floor["success"],
                    "prize_probe": (round(oracle["success"] - floor["success"], 4)
                                    if oracle["success"] is not None else None),
                }
                print(f"[pilot c3] {cid} budget={budget} oracle={oracle['success']} "
                      f"floor={floor['success']}", flush=True)

    payload["elapsed_s"] = round(time.time() - started, 1)
    (run_dir / "pilot.json").write_text(json.dumps(jsonable(payload), indent=2), encoding="utf-8")
    print(f"pilot -> {run_dir / 'pilot.json'}", flush=True)


# ------------------------------------------------------------------- main run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true", help="construction pilot (subst_sel only)")
    parser.add_argument("--quick", action="store_true", help="end-to-end smoke (1 cell, tiny counts)")
    parser.add_argument("--full", action="store_true", help="pre-registered full run")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    if sum([args.pilot, args.quick, args.full]) != 1:
        parser.error("exactly one of --pilot / --quick / --full is required")

    _ensure_mods()
    if args.pilot:
        run_pilot(args.output_dir or PILOT_RUN_DIR, args.workers)
        return

    quick = args.quick
    run_dir = Path(args.output_dir or (DEFAULT_RUN_DIR.parent / (DEFAULT_RUN_DIR.name + "_quick")
                                       if quick else DEFAULT_RUN_DIR))
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "rows").mkdir(exist_ok=True)
    (run_dir / "models").mkdir(exist_ok=True)
    progress_path = run_dir / "progress.jsonl"

    prereg = None
    if PREREG_JSON.exists():
        prereg = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    elif args.full:
        raise SystemExit(f"--full requires the frozen pre-registration {PREREG_JSON}")

    if args.full:
        frozen = prereg["construction_frozen"]
        assert float(frozen["prefix_dist_offset_m"]) == PREFIX_OFFSET_M, \
            "frozen offset must match the code constant"
        allowance = int(frozen["standard_deadline_allowance_steps"])
        c3_budget = int(frozen["c3_reaction_budget_steps"])
        cells = list(ELIGIBLE_CELL_IDS)
        counts = dict(DATA_COUNTS_FULL)
        n_seeds = N_TRAIN_SEEDS
        lr_grid: tuple[float, ...] = (1e-3, 3e-4)
        max_epochs = 200
        sel_ks = list(range(SEL_KS))
        val_ks = list(range(VAL_KS))
        l4_ks = list(range(L4_KS))
        l4_arms = ("nominal", "rls_5s_uniform", "rls_1s_uniform",
                   "rls_1s_classprior", "rls_5s_classprior", "truth")
    else:
        allowance, c3_budget = 0, 110
        cells = ["delay5"]
        counts = {"train": 24, "sel": 8, "val_offgrid": 2, "c3_train": 12, "c3_val": 4}
        n_seeds = 2
        lr_grid = (1e-3,)
        max_epochs = 30
        sel_ks = [0]
        val_ks = [0, 1, 2]
        l4_ks = [0, 1]
        l4_arms = ("nominal", "truth")

    std_max_steps = PIPE.PREFIX_STEPS + allowance + B2K2_TASK_STEPS
    m3215 = json.loads(M3215_SUMMARY.read_text(encoding="utf-8"))
    cal_f1 = m3215["calibration"]["family1"]

    # resume state
    done: dict[str, Any] = {}
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["unit"]] = rec["payload"]

    def mark_done(unit: str, payload_unit: Any) -> None:
        done[unit] = payload_unit
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(jsonable({"unit": unit, "payload": payload_unit})) + "\n")

    started = time.time()
    payload: dict[str, Any] = {
        "protocol": "feasibility_audit_wp1_modular_belief_full_run",
        "generated_by": "scripts/feasibility_audit/wp1_full_run.py",
        "claim_boundary": CLAIM_BOUNDARY,
        "quick_mode": bool(quick),
        "preregistration": ({"file": str(PREREG_JSON), "frozen_criteria_echo": prereg}
                            if prereg is not None else None),
        "construction": {
            "prefix_dist_offset_m": PREFIX_OFFSET_M,
            "standard_deadline_allowance_steps": allowance,
            "std_max_steps": std_max_steps,
            "c3_reaction_budget_steps": c3_budget,
            "prefix_steps": PIPE.PREFIX_STEPS,
            "b2k2_task_steps": B2K2_TASK_STEPS,
        },
        "eligible_cells": cells,
        "m3215_anchor_reference": {c["cell_id"]: {"voi_matched_val": c["voi_matched_val"],
                                                  "floor": c["floor"], "oracle": c["oracle_degraded"]["success_val"]}
                                   for c in m3215["cells"]["family1"] if c["cell_id"] in cells},
        "data": {}, "training": {}, "selection": {}, "validation": {},
        "c3": {}, "l4_exploratory": {}, "verdicts": {},
        "status": "running",
    }

    def flush_partial(final: bool = False) -> None:
        payload["elapsed_s"] = round(time.time() - started, 1)
        target = run_dir / ("summary.json" if final else "summary_partial.json")
        target.write_text(json.dumps(jsonable(payload), indent=2), encoding="utf-8")

    pool = ProcessPoolExecutor(max_workers=args.workers)

    # ---------------------------------------------------------- [1/7] dataset
    print(f"[1/7] dataset: cells={cells} counts={counts}", flush=True)
    for cid in cells:
        unit = f"data_{cid}"
        npz_path = run_dir / f"{cid}.npz"
        if unit in done and npz_path.exists():
            payload["data"][cid] = done[unit]
            continue
        specs: list[tuple[float, int, str, str, bool]] = []
        for role, n in (("train", counts["train"]), ("sel", counts["sel"])):
            for i in range(n):
                seed = PIPE.episode_seed(cell_index(cid), role, i)
                specs.append((PIPE.draw_mu(seed), seed, "standard", role, False))
        val_mus = ([(m, True) for m in PIPE.mu_grid()]
                   + [(m, False) for m in PIPE.mu_offgrid(counts["val_offgrid"])])
        for i, (mu, on_grid) in enumerate(val_mus):
            specs.append((mu, PIPE.episode_seed(cell_index(cid), "val", i), "standard", "val", on_grid))
        for role, n in (("train", counts["c3_train"]), ("val", counts["c3_val"])):
            for i in range(n):
                seed = PIPE.episode_seed(cell_index(cid), role, 100_000 + i)
                specs.append((PIPE.draw_mu(seed), seed, "c3", role, False))
        chunk = max(len(specs) // (args.workers * 2), 4)
        futures = [pool.submit(task_data_chunk, cid, specs[i: i + chunk])
                   for i in range(0, len(specs), chunk)]
        records: list[dict[str, Any]] = []
        for f in futures:
            records.extend(f.result())
        PIPE.save_cell_npz(npz_path, records)
        std = [r for r in records if r["variant"] == "standard"]
        c3 = [r for r in records if r["variant"] == "c3"]
        summary = {
            "n_episodes": len(records),
            "n_invalid_decision": sum(1 for r in records if r["decision_tick"] < 0),
            "probe_gate_standard": PIPE.probe_gate(std),
            "probe_gate_c3": PIPE.probe_gate(c3),
            "c3_telemetry": PIPE.c3_telemetry_gate(records),
            "prefix_max_util_overall": round(max(r["prefix_max_util"] for r in records), 4),
            "initial_transient_max_util_overall": round(
                max(r["initial_transient_max_util"] for r in records), 4),
            "kappa_b_hat_median": round(float(np.median([r["kappa_b_hat"] for r in records])), 4),
            "npz": str(npz_path),
        }
        payload["data"][cid] = summary
        mark_done(unit, summary)
        print(f"  {cid}: n={summary['n_episodes']} invalid={summary['n_invalid_decision']} "
              f"probe_lin={summary['probe_gate_standard'].get('r2_linear_oof')} "
              f"probe_mlp={summary['probe_gate_standard'].get('r2_mlp_oof')} "
              f"c3_pass={summary['c3_telemetry']['gate_pass']}", flush=True)
        flush_partial()

    gate_all = all(payload["data"][cid]["probe_gate_standard"].get("gate_pass") is True
                   and payload["data"][cid]["probe_gate_c3"].get("gate_pass") is True
                   for cid in cells)
    c3_gate_all = all(payload["data"][cid]["c3_telemetry"].get("gate_pass") is True for cid in cells)
    payload["data"]["dataset_gate_pass_all_cells"] = bool(gate_all)
    payload["data"]["c3_telemetry_pass_all_cells"] = bool(c3_gate_all)
    if args.full and not gate_all:
        payload["status"] = "stopped_dataset_leak_gate_failed"
        payload["verdicts"] = {"primary": "not_run_dataset_gate_failed",
                               "route": "pre-registered leak-gate stop: one bounded data iteration allowed"}
        flush_partial(final=True)
        print("HEADLINE: dataset leak gate FAILED -> stopped per pre-registration", flush=True)
        pool.shutdown()
        return

    # --------------------------------------------------------- [2/7] training
    train_units = [(cid, variant, arm, s)
                   for cid in cells for variant in ("standard", "c3")
                   for arm in ARMS for s in range(n_seeds)]
    print(f"[2/7] training: {len(train_units)} runs (5 arms x {n_seeds} seeds x "
          f"{len(cells)} cells x 2 variants)", flush=True)
    pending = {}
    for cid, variant, arm, s in train_units:
        unit = f"train_{cid}_{variant}_{arm}_s{s}"
        model_path = run_dir / "models" / f"{cid}_{variant}_{arm}_s{s}.pt"
        if unit in done and model_path.exists():
            continue
        pending[unit] = pool.submit(task_train, cid, variant, arm, s,
                                    str(run_dir / f"{cid}.npz"), lr_grid, max_epochs,
                                    str(model_path))
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
    capacity = {arm: TRAINER.param_counts(TRAINER.build_arm(arm)) for arm in ARMS}
    payload["training"] = {
        "capacity_report": capacity,
        "capacity_nonproj_spread": round(TRAINER.assert_capacity_matched(capacity), 4),
        "lr_grid": list(lr_grid), "max_epochs": max_epochs, "n_seeds": n_seeds,
        "runs": {u: done[u] for u in (f"train_{cid}_{v}_{a}_s{s}"
                                      for cid in cells for v in ("standard", "c3")
                                      for a in ARMS for s in range(n_seeds))},
    }
    for cid in cells:
        for arm in ARMS:
            maes = [done[f"train_{cid}_standard_{arm}_s{s}"]["val"]["mae"] for s in range(n_seeds)]
            print(f"  {cid} {arm:<14} std val MAE {np.mean(maes):.4f} "
                  f"(seeds {min(maes):.4f}..{max(maes):.4f})", flush=True)
    flush_partial()

    # -------------------------------------------------- [3/7] floor selection
    print("[3/7] floor/oracle selection on subst_sel", flush=True)
    selection: dict[str, Any] = {}
    for cid in cells:
        unit = f"sel_{cid}"
        if unit in done:
            selection[cid] = done[unit]
            payload["selection"][cid] = done[unit]
            continue
        cell = cell_by_id(cid)
        specs = floor_seeker_specs(cell, cal_f1[cid]) + fixed_specs()
        futures = {s["name"]: pool.submit(task_std_arm, cid, s["name"], s, None, "sel",
                                          sel_ks, std_max_steps, None, None)
                   for s in specs}
        oracle_fut = pool.submit(task_oracle_sel, cid, sel_ks, std_max_steps)
        results = {n: f.result() for n, f in futures.items()}
        spec_by_name = {s["name"]: s for s in specs}
        seekers = {n: r for n, r in results.items() if spec_by_name[n]["type"] == "seeker"}
        fixeds = {n: r for n, r in results.items() if spec_by_name[n]["type"] != "seeker"}
        best_seeker = max(seekers, key=lambda n: (seekers[n]["success"], seekers[n]["return"]))
        best_fixed = max(fixeds, key=lambda n: (fixeds[n]["success"], fixeds[n]["return"]))
        osel = oracle_fut.result()
        sel_payload = {
            "best_seeker": {"name": best_seeker, "spec": spec_by_name[best_seeker],
                            "sel_success": results[best_seeker]["success"]},
            "best_fixed": {"name": best_fixed, "spec": spec_by_name[best_fixed],
                           "sel_success": results[best_fixed]["success"]},
            "oracle_dv_by_point": osel["dv_by_point"],
            "n_seeker_configs": len(seekers), "n_fixed_configs": len(fixeds),
            "sel_table": {n: r["success"] for n, r in results.items()},
        }
        selection[cid] = sel_payload
        payload["selection"][cid] = sel_payload
        mark_done(unit, sel_payload)
        print(f"  {cid}: best_seeker={best_seeker} ({results[best_seeker]['success']}) "
              f"best_fixed={best_fixed} ({results[best_fixed]['success']})", flush=True)
        flush_partial()

    # ------------------------------------------------ [4/7] standard validation
    print(f"[4/7] standard validation: {len(cells)} cells x (floor+oracle+"
          f"{len(ARMS)}x{n_seeds} injected) x {12 * len(val_ks)} episodes", flush=True)
    val_arm_units: dict[str, list[tuple[str, str]]] = {cid: [] for cid in cells}
    pending = {}
    for cid in cells:
        sel = selection[cid]
        base_arms = [
            ("floor_seeker", sel["best_seeker"]["spec"], None, None),
            ("floor_fixed", sel["best_fixed"]["spec"], None, None),
            ("oracle", {"type": "oracle", "dv": 0.0, "name": "oracle_per_point"}, None,
             sel["oracle_dv_by_point"]),
        ]
        for arm_name, spec, inj, dvs in base_arms:
            unit = f"val_{cid}_{arm_name}"
            val_arm_units[cid].append((arm_name, unit))
            if unit in done:
                continue
            pending[unit] = pool.submit(task_std_arm, cid, arm_name, spec, inj, "val",
                                        val_ks, std_max_steps, dvs,
                                        str(run_dir / "rows" / f"{unit}.csv"))
        for arm in ARMS:
            for s in range(n_seeds):
                arm_name = f"{arm}_s{s}"
                unit = f"val_{cid}_{arm_name}"
                val_arm_units[cid].append((arm_name, unit))
                if unit in done:
                    continue
                inj = {"kind": "model", "arm": arm,
                       "path": str(run_dir / "models" / f"{cid}_standard_{arm}_s{s}.pt")}
                spec = dict(sel["best_seeker"]["spec"], name=f"injected_{arm}_s{s}")
                pending[unit] = pool.submit(task_std_arm, cid, arm_name, spec, inj, "val",
                                            val_ks, std_max_steps, None,
                                            str(run_dir / "rows" / f"{unit}.csv"))
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
        flush_partial()

    # ---------------------------------------------------------- [5/7] C3 block
    print("[5/7] C3 block (handover at reveal, per-episode deadline)", flush=True)
    c3_units: dict[str, dict[str, str]] = {cid: {} for cid in cells}
    for cid in cells:
        cell = cell_by_id(cid)
        spec = c3_seeker_spec(cell, cal_f1[cid])
        for phase, ks in (("sel", sel_ks), ("val", val_ks)):
            unit = f"c3probe_{cid}_{phase}"
            if unit not in done:
                mark_done(unit, pool.submit(task_c3_probes, cid, phase,
                                            list(range(len(mu_grid()))), ks).result())
        ticks_sel = done[f"c3probe_{cid}_sel"]["ticks"]
        ticks_val = done[f"c3probe_{cid}_val"]["ticks"]
        # floor candidate selection
        unit = f"c3sel_{cid}"
        if unit not in done:
            cands = {"c3_floor_nobelief": None}
            for v in C3_FLOOR_CONST_MUS:
                cands[f"c3_floor_const{v:g}"] = {"kind": "const", "value": v}
            futs = {n: pool.submit(task_c3_arm, cid, n, spec, inj, "sel", sel_ks,
                                   c3_budget, ticks_sel, None) for n, inj in cands.items()}
            res = {n: f.result() for n, f in futs.items()}
            best = max(res, key=lambda n: (res[n]["success"] or 0.0, res[n]["return"] or 0.0))
            mark_done(unit, {"best_floor": best, "candidates": {n: r["success"] for n, r in res.items()}})
        c3_floor_name = done[unit]["best_floor"]
        c3_floor_inj = (None if c3_floor_name == "c3_floor_nobelief"
                        else {"kind": "const", "value": float(c3_floor_name.rsplit("const", 1)[1])})
        pending = {}
        arms_c3 = [("c3_floor", spec, c3_floor_inj, False),
                   ("c3_oracle", {"type": "oracle", "dv": 0.0, "name": "c3_oracle"}, None, False)]
        for arm in ARMS:
            for s in range(n_seeds):
                inj = {"kind": "model", "arm": arm,
                       "path": str(run_dir / "models" / f"{cid}_c3_{arm}_s{s}.pt")}
                arms_c3.append((f"c3_{arm}_s{s}", spec, inj, True))
        for arm_name, cspec, inj, _ in arms_c3:
            unit = f"c3val_{cid}_{arm_name}"
            c3_units[cid][arm_name] = unit
            if unit in done:
                continue
            pending[unit] = pool.submit(task_c3_arm, cid, arm_name, cspec, inj, "val",
                                        val_ks, c3_budget, ticks_val,
                                        str(run_dir / "rows" / f"{unit}.csv"))
        for unit, fut in pending.items():
            mark_done(unit, fut.result())
        flush_partial()
        print(f"  {cid}: c3 floor={c3_floor_name} "
              f"({done[c3_units[cid]['c3_floor']]['success']}) "
              f"oracle={done[c3_units[cid]['c3_oracle']]['success']}", flush=True)

    # ----------------------------------------------- [6/7] L4 exploratory block
    print(f"[6/7] L4 exploratory block ({L4_CELL}, vehicle randomization ON)", flush=True)
    l4_seeker = selection[L4_CELL]["best_seeker"]["spec"] if L4_CELL in selection else None
    pending = {}
    for arm in l4_arms:
        unit = f"l4_{arm}"
        if unit in done:
            continue
        pending[unit] = pool.submit(task_l4_arm, arm, l4_ks, l4_seeker, std_max_steps,
                                    str(run_dir / "rows" / f"{unit}.csv"))
    for unit, fut in pending.items():
        mark_done(unit, fut.result())
    payload["l4_exploratory"] = {
        "note": ("exploratory, NOT gated (plan WP1.1 L4 scope): vehicle-randomized delay5, "
                 "prefix-RLS kappa belief fed to the cell's best floor seeker; class prior = "
                 "0.15-wide kappa bins with prior sigma 0.075 vs uniform 0.30"),
        "arms": {arm: done[f"l4_{arm}"] for arm in l4_arms},
    }
    flush_partial()
    pool.shutdown()

    # ------------------------------------------------------- [7/7] adjudication
    print("[7/7] adjudication", flush=True)
    n_pts = len(mu_grid())
    n_val = n_pts * len(val_ks)
    wilson = MODS["wp0"].wilson_ci
    newcombe = MODS["wp0"].newcombe_diff_ci

    cells_out: dict[str, Any] = {}
    primary_pass_cells = []
    l0_pass_cells = []
    pooled_num, pooled_den = {arm: 0.0 for arm in ARMS}, 0.0
    for cid in cells:
        floor_seeker = done[f"val_{cid}_floor_seeker"]
        floor_fixed = done[f"val_{cid}_floor_fixed"]
        oracle = done[f"val_{cid}_oracle"]
        floor = floor_seeker if floor_seeker["success"] >= floor_fixed["success"] else floor_fixed
        floor_name = (selection[cid]["best_seeker"]["name"] if floor is floor_seeker
                      else selection[cid]["best_fixed"]["name"])
        prize = oracle["success"] - floor["success"]
        cell_out: dict[str, Any] = {
            "floor": {"arm": floor_name, "success_val": floor["success"],
                      "wilson95": wilson(floor["success"], n_val),
                      "candidates": {"seeker": floor_seeker["success"],
                                     "fixed": floor_fixed["success"]}},
            "oracle": {"success_val": oracle["success"],
                       "wilson95": wilson(oracle["success"], n_val),
                       "dv_by_point": selection[cid]["oracle_dv_by_point"]},
            "prize_matched_remeasured": round(prize, 4),
            "prize_ci95_newcombe": newcombe(oracle["success"], n_val, floor["success"], n_val),
            "m3215_reference_prize": payload["m3215_anchor_reference"][cid]["voi_matched_val"],
            "arms": {},
        }
        floor_eps = floor["episode_success"]
        oracle_eps = oracle["episode_success"]
        for arm in ARMS:
            arm_eps = {s: done[f"val_{cid}_{arm}_s{s}"]["episode_success"] for s in range(n_seeds)}
            stats = two_way_diff_stats(arm_eps, floor_eps)
            succ = float(np.mean([done[f"val_{cid}_{arm}_s{s}"]["success"] for s in range(n_seeds)]))
            recapture = (stats["delta"] / prize) if prize > 0 else None
            cell_pass = bool(prize > 0 and recapture is not None and recapture >= RECAPTURE_BAR
                             and stats["lower_975_one_sided"] > 0)
            inj_frac = float(np.mean([done[f"val_{cid}_{arm}_s{s}"]["injection_fired_fraction"] or 0.0
                                      for s in range(n_seeds)]))
            mu_errs = [done[f"val_{cid}_{arm}_s{s}"]["mu_injected_abs_err_mean"]
                       for s in range(n_seeds)
                       if done[f"val_{cid}_{arm}_s{s}"]["mu_injected_abs_err_mean"] is not None]
            cell_out["arms"][arm] = {
                "success_val_mean_over_seeds": round(succ, 4),
                "per_seed_success": [done[f"val_{cid}_{arm}_s{s}"]["success"] for s in range(n_seeds)],
                "diff_vs_floor": stats,
                "recapture_fraction": (round(recapture, 4) if recapture is not None else None),
                "cell_pass_recapture_and_ci": cell_pass,
                "injection_fired_fraction": round(inj_frac, 4),
                "mu_injected_abs_err_mean": (round(float(np.mean(mu_errs)), 4) if mu_errs else None),
            }
            keys = sorted(set(floor_eps) & set(oracle_eps))
            pooled_num[arm] += sum(np.mean([arm_eps[s][k] for s in range(n_seeds)]) - floor_eps[k]
                                   for k in keys)
            if arm == ARMS[0]:
                pooled_den += sum(oracle_eps[k] - floor_eps[k] for k in keys)
        if cell_out["arms"][PRIMARY_ARM]["cell_pass_recapture_and_ci"]:
            primary_pass_cells.append(cid)
        if cell_out["arms"]["L0_frame"]["cell_pass_recapture_and_ci"]:
            l0_pass_cells.append(cid)
        cells_out[cid] = cell_out
    payload["validation"] = {"n_val_episodes_per_arm_per_cell": n_val, "cells": cells_out}
    payload["validation"]["pooled_fraction_by_arm"] = {
        arm: (round(pooled_num[arm] / pooled_den, 4) if pooled_den > 0 else None) for arm in ARMS}

    # C3 adjudication
    c3_out: dict[str, Any] = {}
    c3_verdicts: dict[str, str] = {}
    for cid in cells:
        floor = done[c3_units[cid]["c3_floor"]]
        oracle = done[c3_units[cid]["c3_oracle"]]
        n_c3 = floor["n"]
        cell_c3: dict[str, Any] = {
            "floor": {"arm": done[f"c3sel_{cid}"]["best_floor"], "success_val": floor["success"],
                      "wilson95": wilson(floor["success"], n_c3) if floor["success"] is not None else None},
            "oracle": {"success_val": oracle["success"],
                       "wilson95": wilson(oracle["success"], n_c3) if oracle["success"] is not None else None},
            "prize": (round(oracle["success"] - floor["success"], 4)
                      if None not in (oracle["success"], floor["success"]) else None),
            "n_episodes": n_c3,
            "arms": {},
        }
        floor_eps = floor["episode_success"]
        arm_eps_all = {}
        cleared = []
        for arm in ARMS:
            arm_eps = {s: done[c3_units[cid][f"c3_{arm}_s{s}"]]["episode_success"]
                       for s in range(n_seeds)}
            arm_eps_all[arm] = arm_eps
            stats = two_way_diff_stats(arm_eps, floor_eps)
            clears = bool(stats["lower_975_one_sided"] > 0)
            cell_c3["arms"][arm] = {
                "success_val_mean_over_seeds": round(float(np.mean(
                    [done[c3_units[cid][f"c3_{arm}_s{s}"]]["success"] for s in range(n_seeds)])), 4),
                "diff_vs_floor": stats, "clears_floor": clears,
            }
            if arm in HISTORY_ARMS and clears:
                cleared.append(arm)
        condition = bool(cleared)
        cell_c3["history_arm_clears_floor"] = cleared
        if condition:
            cmp_stats = paired_arm_arm_stats(arm_eps_all["L3_GRU"], arm_eps_all["L2_window_100"])
            cell_c3["l3_vs_l2w100"] = cmp_stats
            if cmp_stats["lower_975_one_sided"] > 0:
                verdict = "iir_wins"
            elif cmp_stats["tost_equivalent"]:
                verdict = "fir_sufficient"
            else:
                verdict = "indeterminate"
        else:
            verdict = "not_reported_no_history_arm_clears_floor"
        cell_c3["verdict"] = verdict
        c3_verdicts[cid] = verdict
        c3_out[cid] = cell_c3
    payload["c3"] = {"reaction_budget_steps": c3_budget, "cells": c3_out,
                     "per_cell_verdicts": c3_verdicts}

    primary_pass = len(primary_pass_cells) >= PRIMARY_CELLS_REQUIRED
    route = "wp2_proceeds" if primary_pass else "all_arms_fail_one_bounded_iteration_then_accept_bound"
    if not primary_pass and any(cells_out[cid]["arms"][a]["cell_pass_recapture_and_ci"]
                                for cid in cells for a in ARMS):
        route = "primary_fails_some_exploratory_arm_passes_report_descriptively"
    if len(l0_pass_cells) >= PRIMARY_CELLS_REQUIRED:
        route = "l0_succeeds_leak_audit_required"
    payload["verdicts"] = {
        "primary_arm": PRIMARY_ARM,
        "primary_rule": (f"recapture >= {RECAPTURE_BAR} of the re-measured matched prize in >= "
                         f"{PRIMARY_CELLS_REQUIRED} eligible cells, each with one-sided 97.5% "
                         "lower bound of the episode-paired (arm - floor) difference > 0 "
                         "(two-way episode + seed-cluster SE)"),
        "primary_pass_cells": primary_pass_cells,
        "primary_verdict": ("PASS" if primary_pass else "FAIL"),
        "l0_pass_cells": l0_pass_cells,
        "route": route,
        "c3_verdicts": c3_verdicts,
        "dataset_gate": payload["data"]["dataset_gate_pass_all_cells"],
        "c3_telemetry_gate": payload["data"]["c3_telemetry_pass_all_cells"],
    }
    payload["status"] = "completed"
    payload["artifacts"] = {
        "summary_json": str(run_dir / "summary.json"),
        "progress_jsonl": str(progress_path),
        "rows_dir": str(run_dir / "rows"),
        "models_dir": str(run_dir / "models"),
        "preregistration_json": str(PREREG_JSON) if prereg is not None else None,
    }
    flush_partial(final=True)
    print(f"results -> {run_dir / 'summary.json'}", flush=True)
    print("HEADLINE: primary=" + payload["verdicts"]["primary_verdict"]
          + f" cells={primary_pass_cells} route={route}"
          + f" | c3={c3_verdicts} | elapsed {payload['elapsed_s']}s", flush=True)


if __name__ == "__main__":
    main()
