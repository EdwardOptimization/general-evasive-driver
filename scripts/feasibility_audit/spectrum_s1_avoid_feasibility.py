"""S1 scenario-spectrum AVOID feasibility PRE-CHECK (group B of the master variable table,
docs/coverage-spectrum-design-2026-06.md). The drift half lives in
spectrum_s1_feasibility_precheck.py; this is the mirrored AVOID half on the SEDAN.

Grounds the frozen avoid spectrum in DATA (robotics-recipe DR philosophy: don't guess which
geometry extensions stay avoidable — measure it). For every candidate avoid cell, run the
SEDAN-fitted avoid ORACLE (ramp_policy_voi_regime.RampPolicyController, mode='oracle') in Chrono
and record avoid SUCCESS (F2 _avoid_success semantics). A cell is FEASIBLE if oracle success
>= 0.8 over a couple seeds. Oracle rollouts only — NO training.

Unlike the cross-vehicle UAZBUS de-risk (which re-physicalizes the oracle for a 2x-heavier
vehicle), the Sedan IS the vehicle the oracle was fitted to (default V_KNOTS / FZR / MASS), so
NO re-physicalization is needed: the unmodified ramp_policy_voi_regime is the matching oracle.

Grid (docs group B):
  BASE          reveal {9.5,12,16,22,30} (e2p.CLEAN_REVEALS) x mu {0.3625,0.5875,0.8125,1.0375}
                (e2p.MU_POINTS) — mostly known-feasible (~1.0); the baseline.
  + KNIFE-EDGE  reveal 8.0 m added (group B "+ 8.0 m knife-edge"), at all 4 mu.
  + OFFSET      obstacle lateral OFFSET spread {-0.9, -0.45, +0.45, +0.9} m at a couple binding
                reveal x mu cells (offset shifts the obstacle across-track along the circle
                normal — env normal_left = -radial; matches env.py obstacle_lateral_offset).
  + WIDTH       obstacle half_width variants {0.6, 1.0, 1.4, 1.8} m at a couple binding cells.
  Geometry variants are NOT crossed into the full product — just enough to see which extensions
  stay avoidable.

Run (base env; the worker spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/spectrum_s1_avoid_feasibility.py
    PYTHONPATH=src python scripts/feasibility_audit/spectrum_s1_avoid_feasibility.py --quick
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
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (REPO / "src", SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402
import phase4_e2prime_chrono_two_regime_hardened as e2p  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

# ---- the Sedan avoid oracle: the default (Sedan-fitted) regime module, no re-physicalization
VARIANT = "sedan_tmeasy"
MAX_STEPS = 285  # avoidance episode horizon (ramp_policy MAX_STEPS)
FEASIBLE_THRESHOLD = 0.80  # oracle success >= 0.8 -> avoidable

# BASE grid (docs group B): keep the existing 5x4 avoid grid as the baseline.
BASE_REVEALS = e2p.CLEAN_REVEALS    # (9.5, 12.0, 16.0, 22.0, 30.0)
BASE_MUS = e2p.MU_POINTS            # (0.3625, 0.5875, 0.8125, 1.0375)

# NEW geometry variants (docs group B "+ add 8.0 m (knife-edge), + offset spread, + width").
KNIFE_EDGE_REVEAL = 8.0
# binding cells where the avoid constraint actually bites (tight reveal, low + mid mu)
BINDING_CELLS = ((9.5, 0.3625), (12.0, 0.5875))
OFFSET_SPREAD_M = (-0.9, -0.45, 0.45, 0.9)   # lateral across-track shift of the obstacle
WIDTH_VARIANTS_M = (0.6, 1.0, 1.4, 1.8)      # obstacle half_width (default sampled ~0.6-1.0)

RUN_DIR = REPO / "runs" / "feasibility_audit" / "spectrum_s1"
OUT = RUN_DIR / "avoid_feasibility.json"
STDERR_LOG = RUN_DIR / "avoid_chrono_worker_stderr.log"

CLAIM_BOUNDARY = (
    "S1 spectrum AVOID feasibility pre-check only: runs the unmodified Sedan-fitted avoid oracle "
    "(ramp_policy_voi_regime RampPolicyController mode='oracle') on the avoid reveal x mu grid plus "
    "new geometry extensions (knife-edge reveal, obstacle lateral offset spread, obstacle width "
    "variants) on Chrono, and records oracle avoid success per cell to ground the frozen S1 avoid "
    "spectrum in data. No training, promotion, or capability claim."
)


# ----------------------------------------------------------- module loader (reused pattern) ----
def _load_regime_copy(name: str):
    """Load a fresh copy of ramp_policy_voi_regime under a unique module name (mirrors the
    cross_vehicle_uazbus_avoid_derisk loader). For the Sedan no globals are patched — the
    on-disk module already IS the Sedan-fitted oracle."""
    path = SCRIPTS_DIR / "ramp_policy_voi_regime.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _e2_context_for(reg):
    mod_b = reg.load_module(reg.TASK_B_SCRIPT, f"{reg.__name__}_task_b")
    mod_c = reg.load_module(reg.COND_SCRIPT, f"{reg.__name__}_cond")
    return mod_b, mod_c.interp_lin


# --------------------------------------------- scenario + geometry variant injection ----------
def _sedan_scenario(reg, mod_b, interp, *, reveal: float, mu: float, seed: int) -> dict[str, Any]:
    scenario = e2_smoke._make_scenario(reg, mod_b, interp, reveal=float(reveal), mu=float(mu),
                                       seed=int(seed), variant=VARIANT)
    scenario["max_steps"] = int(MAX_STEPS)
    scenario["scenario_id"] = f"sedanavoid-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    return scenario


def _apply_geometry(scenario: dict[str, Any], *, lateral_offset_m: float = 0.0,
                    half_width_m: float | None = None) -> dict[str, Any]:
    """Shift / resize the obstacle in the baked scenario dict (the Chrono backend reads
    obstacle x/y/half_width directly, and the same fields drive the obs the controller sees, so a
    post-hoc edit is self-consistent — both collision AND perception use these fields).

    lateral_offset_m: move the obstacle across-track along the circle normal. The env builds
      obstacle_position with normal_left = [-tangent_y, tangent_x]; for a CCW circle centered at
      origin that equals -radial, so a POSITIVE env offset moves the obstacle toward the origin.
      We replicate exactly: normal_left = -radial_unit at the obstacle, shift += offset*normal_left.
    half_width_m: override the obstacle half_width (collision radius = ego_half_width + half_width).
    """
    ob = scenario.get("obstacle") or {}
    if not ob.get("enabled"):
        return scenario
    if half_width_m is not None:
        ob["half_width"] = float(half_width_m)
    if lateral_offset_m != 0.0:
        ox, oy = float(ob["x"]), float(ob["y"])
        r = math.hypot(ox, oy)
        if r > 1e-6:
            radial = (ox / r, oy / r)
            normal_left = (-radial[0], -radial[1])  # env.py convention for CCW circle
            ob["x"] = ox + lateral_offset_m * normal_left[0]
            ob["y"] = oy + lateral_offset_m * normal_left[1]
    scenario["obstacle"] = ob
    return scenario


def _avoid_success(info: dict[str, Any]) -> bool:
    """F2 _avoidance_success semantics: no collision, no off-track, completion in
    {obstacle_pass, max_steps}. (Identical to the cross-vehicle de-risk helper.)"""
    collision = bool(info.get("collision", False)) or \
        str(info.get("termination_reason", "")) == "obstacle_collision"
    offtrack = str(info.get("termination_reason", "")) == "off_track"
    completion = str(info.get("completion_reason", "") or "")
    return bool((not collision) and (not offtrack) and completion in ("obstacle_pass", "max_steps"))


def _run_episode(client: ChronoWorkerClient, scenario: dict[str, Any], controller: Any,
                 *, seed: int) -> dict[str, Any]:
    if hasattr(controller, "reset"):
        controller.reset()
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
    backend = dict(reset_reply.get("backend_info", {}))
    info = dict(reset_reply.get("info", {}))
    variant_match = backend.get("chrono_vehicle_variant") == VARIANT
    terminated = truncated = False
    steps = 0
    collision_any = False
    max_steps = int(scenario["max_steps"]) + 5
    while not (terminated or truncated) and steps < max_steps:
        action = np.asarray(controller.act(np.asarray(obs, dtype=np.float64)), dtype=np.float32)
        obs, terminated, truncated, status, info = client.step(action)
        if not (obs.shape == (72,) and np.isfinite(obs).all()):
            break
        collision_any = collision_any or bool(info.get("collision", False)) or \
            str(info.get("termination_reason", "")) == "obstacle_collision"
        steps += 1
    success = bool(_avoid_success(info) and not collision_any)
    margin = info.get("min_clearance_margin")
    return {
        "success": success,
        "collision": bool(collision_any),
        "steps": int(steps),
        "outcome": e2_smoke._outcome_from_info(info),
        "completion_reason": str(info.get("completion_reason", "") or ""),
        "termination_reason": str(info.get("termination_reason", "") or ""),
        "min_clearance_margin": float(margin) if isinstance(margin, (int, float)) else float("nan"),
        "variant_match": bool(variant_match),
        "vehicle_total_mass": backend.get("vehicle_total_mass"),
    }


class _RestartingRunner:
    """Restart-on-error wrapper around the Chrono worker (same as the cross-vehicle de-risk)."""

    def __init__(self):
        self.client: ChronoWorkerClient | None = None
        self.count = 0

    def _ensure(self) -> ChronoWorkerClient:
        if self.client is None:
            self.client = ChronoWorkerClient(stderr_log=STDERR_LOG, read_timeout_s=600.0)
            self.count = 0
        return self.client

    def restart(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def run(self, scenario, controller, *, seed) -> dict[str, Any]:
        if self.count >= 40:
            self.restart()
        try:
            out = _run_episode(self._ensure(), scenario, controller, seed=seed)
        except Exception as exc:
            self.restart()
            out = _run_episode(self._ensure(), scenario, controller, seed=seed)
            out["restart_after_error"] = f"{type(exc).__name__}: {exc}"
        self.count += 1
        return out

    def close(self):
        self.restart()


def _oracle_builder(reg, mod_b, interp, *, reveal: float, mu: float) -> Callable[[], Any]:
    """The Sedan-fitted avoid oracle for a (reveal, mu) cell (mode='oracle', knows mu)."""
    design = reg.make_design(mod_b, float(reveal))
    return lambda: reg.RampPolicyController(
        mod_b, interp, design, f"sedan_oracle_dv0_{reg.__name__}", mode="oracle",
        mu_true=float(mu), dv=0.0)


# ---------------------------------------------------------------------- grid runners ----------
def _run_cell(runner: _RestartingRunner, reg, mod_b, interp, *, reveal: float, mu: float,
              seeds: list[int], lateral_offset_m: float = 0.0,
              half_width_m: float | None = None, geometry: str = "base") -> dict[str, Any]:
    builder = _oracle_builder(reg, mod_b, interp, reveal=reveal, mu=mu)
    n_ok = 0
    rows = []
    for seed in seeds:
        scenario = _sedan_scenario(reg, mod_b, interp, reveal=reveal, mu=mu, seed=seed)
        _apply_geometry(scenario, lateral_offset_m=lateral_offset_m, half_width_m=half_width_m)
        res = runner.run(scenario, builder(), seed=seed)
        n_ok += int(res["success"])
        rows.append({"seed": seed, "success": bool(res["success"]), "outcome": res["outcome"],
                     "margin": round(res["min_clearance_margin"], 3),
                     "variant_match": res["variant_match"]})
    success_rate = n_ok / max(len(seeds), 1)
    feasible = success_rate >= FEASIBLE_THRESHOLD
    return {
        "reveal": float(reveal), "mu": float(mu), "geometry": geometry,
        "lateral_offset_m": float(lateral_offset_m),
        "half_width_m": (None if half_width_m is None else float(half_width_m)),
        "n_seeds": len(seeds), "n_success": n_ok, "success": round(success_rate, 4),
        "feasible": bool(feasible), "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seeds", type=int, default=0)
    args = parser.parse_args()
    quick = bool(args.quick)
    n_seeds = args.seeds or (1 if quick else 2)
    seeds = [101 + i for i in range(n_seeds)]

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()

    reg = _load_regime_copy("sedan_avoid_regime")
    mod_b, interp = _e2_context_for(reg)

    base_reveals = BASE_REVEALS if not quick else (9.5, 30.0)
    base_mus = BASE_MUS if not quick else (0.3625, 0.8125)
    binding = BINDING_CELLS if not quick else (BINDING_CELLS[0],)
    offset_spread = OFFSET_SPREAD_M if not quick else (-0.9, 0.9)
    width_variants = WIDTH_VARIANTS_M if not quick else (0.6, 1.8)

    runner = _RestartingRunner()
    cells: list[dict[str, Any]] = []
    try:
        print(f"[s1-avoid] Sedan avoid feasibility (oracle): variant={VARIANT} seeds={seeds} "
              f"threshold>={FEASIBLE_THRESHOLD}", flush=True)

        # --- BASE grid (reveal x mu) ---
        print(f"[BASE] {len(base_reveals)} reveals x {len(base_mus)} mu (the existing avoid grid baseline)", flush=True)
        for reveal in base_reveals:
            for mu in base_mus:
                c = _run_cell(runner, reg, mod_b, interp, reveal=reveal, mu=mu, seeds=seeds,
                              geometry="base")
                cells.append(c)
                tag = "FEASIBLE" if c["feasible"] else "infeasible"
                print(f"  reveal={reveal:>4.1f} mu={mu:.4f} | oracle success={c['success']:.2f} "
                      f"({c['n_success']}/{c['n_seeds']}) -> {tag}", flush=True)

        # --- KNIFE-EDGE reveal 8.0 (new tighter tier) across all base mu ---
        print(f"[KNIFE-EDGE] reveal={KNIFE_EDGE_REVEAL} m x {len(base_mus)} mu (group B knife-edge)", flush=True)
        for mu in base_mus:
            c = _run_cell(runner, reg, mod_b, interp, reveal=KNIFE_EDGE_REVEAL, mu=mu, seeds=seeds,
                          geometry="knife_edge_reveal8.0")
            cells.append(c)
            tag = "FEASIBLE" if c["feasible"] else "infeasible"
            print(f"  reveal={KNIFE_EDGE_REVEAL:>4.1f} mu={mu:.4f} | oracle success={c['success']:.2f} "
                  f"({c['n_success']}/{c['n_seeds']}) -> {tag}", flush=True)

        # --- OFFSET spread at a couple binding cells ---
        print(f"[OFFSET] lateral offset spread {offset_spread} m at binding cells {binding}", flush=True)
        for reveal, mu in binding:
            for off in offset_spread:
                c = _run_cell(runner, reg, mod_b, interp, reveal=reveal, mu=mu, seeds=seeds,
                              lateral_offset_m=off, geometry=f"offset{off:+g}")
                cells.append(c)
                tag = "FEASIBLE" if c["feasible"] else "infeasible"
                print(f"  reveal={reveal:>4.1f} mu={mu:.4f} offset={off:+.2f}m | "
                      f"oracle success={c['success']:.2f} ({c['n_success']}/{c['n_seeds']}) -> {tag}",
                      flush=True)

        # --- WIDTH variants at a couple binding cells ---
        print(f"[WIDTH] obstacle half_width variants {width_variants} m at binding cells {binding}", flush=True)
        for reveal, mu in binding:
            for w in width_variants:
                c = _run_cell(runner, reg, mod_b, interp, reveal=reveal, mu=mu, seeds=seeds,
                              half_width_m=w, geometry=f"width{w:g}")
                cells.append(c)
                tag = "FEASIBLE" if c["feasible"] else "infeasible"
                print(f"  reveal={reveal:>4.1f} mu={mu:.4f} half_width={w:.2f}m | "
                      f"oracle success={c['success']:.2f} ({c['n_success']}/{c['n_seeds']}) -> {tag}",
                      flush=True)
    finally:
        runner.close()

    feasible_cells = [c for c in cells if c["feasible"]]
    geom_groups: dict[str, dict[str, int]] = {}
    for c in cells:
        g = c["geometry"].split("reveal")[0].split("0.")[0] if False else c["geometry"]
        # group by family prefix (base / knife_edge / offset / width)
        fam = ("base" if c["geometry"] == "base"
               else "knife_edge" if c["geometry"].startswith("knife_edge")
               else "offset" if c["geometry"].startswith("offset")
               else "width" if c["geometry"].startswith("width")
               else c["geometry"])
        gg = geom_groups.setdefault(fam, {"total": 0, "feasible": 0})
        gg["total"] += 1
        gg["feasible"] += int(c["feasible"])

    payload = {
        "protocol": "spectrum_s1_avoid_feasibility",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": VARIANT,
        "oracle": "ramp_policy_voi_regime.RampPolicyController(mode='oracle') — Sedan-fitted, no re-physicalization",
        "feasible_threshold": FEASIBLE_THRESHOLD,
        "max_steps": MAX_STEPS,
        "seeds": seeds,
        "grid": {
            "base_reveals": list(base_reveals), "base_mus": list(base_mus),
            "knife_edge_reveal_m": KNIFE_EDGE_REVEAL,
            "binding_cells": [list(c) for c in binding],
            "offset_spread_m": list(offset_spread),
            "width_variants_m": list(width_variants),
        },
        "sedan_oracle_constants": {"FZR_n": reg.FZR, "MASS_kg": reg.MASS,
                                   "V_KNOTS_mps": list(reg.V_KNOTS), "MU_KNOTS": list(reg.MU_KNOTS)},
        "cells": cells,
        "feasible_cells": feasible_cells,
        "geometry_family_summary": geom_groups,
        "n_cells": len(cells),
        "n_feasible": len(feasible_cells),
        "elapsed_s": round(time.time() - started, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"\n=== AVOID FEASIBLE-CELL LIST: {len(feasible_cells)}/{len(cells)} cells ===")
    for fam, gg in geom_groups.items():
        print(f"  [{fam}] {gg['feasible']}/{gg['total']} feasible")
    for c in feasible_cells:
        geo = "" if c["geometry"] == "base" else f" geom={c['geometry']}"
        print(f"  reveal={c['reveal']:>4.1f} mu={c['mu']:.4f}{geo} success={c['success']:.2f}")
    print(f"\nwrote {OUT}  [{payload['elapsed_s']}s]")


if __name__ == "__main__":
    main()
