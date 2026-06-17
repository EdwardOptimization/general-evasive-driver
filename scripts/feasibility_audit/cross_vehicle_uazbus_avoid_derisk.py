"""Cross-vehicle DE-RISK (2/2): re-physicalize the avoid oracle for UAZBUS.

Before the full ~12-18 day cross-vehicle build (docs/north-star-2026-06.md
"Piece (2) cross-vehicle"), prove the AVOIDANCE oracle generalizes to UAZBUS.
The avoid oracle (ramp_policy_voi_regime.RampPolicyController, mode='oracle') is
SEDAN-FITTED: hardcoded module globals V_KNOTS=(4.5,7.5,9.5,10.5) @ MU_KNOTS,
MASS=1450, FZR=6858.3 (rear static load). These are WRONG for UAZBUS (~2x mass,
~2x rear load), so its plan systematically under/over-brakes.

This script (NO protected module is modified):
  (A) MEASURES UAZBUS's rear static load FZR from Chrono reset tire telemetry.
  (B) MEASURES UAZBUS's safe-entry-speed-vs-mu (V_KNOTS): drive UAZBUS straight
      at the obstacle at increasing entry speeds (swerve-only commitment, the
      standard safe-entry probe) per mu, find the MAX entry speed that still
      clears (no collision/offtrack + obstacle passed) on Chrono.
  (C) Builds a UAZBUS-parameterized oracle = a FRESH copy of the regime module
      with FZR/MASS/V_KNOTS patched to the measured UAZBUS values (the on-disk
      Sedan module is untouched; the protected import path is unaffected).
  (D) Runs the re-physicalized oracle on the UAZBUS avoidance grid (reveal x mu),
      and ALSO runs the UNMODIFIED Sedan-fitted oracle on UAZBUS (the baseline
      gap the scoping predicted), on the SAME scenarios/seeds.

Avoidance scenarios are the EXACT F2 cross-vehicle scenarios
(phase4_e2_chrono_two_regime_smoke._make_scenario) with chrono_vehicle_variant=
uazbus_tmeasy and params.mass overridden to the measured UAZBUS mass (what the
real cross-vehicle build threads). Success = _avoidance_success semantics:
no collision, no off-track, completion in {obstacle_pass, max_steps}.

Run (from repo root; base env -- the worker spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/cross_vehicle_uazbus_avoid_derisk.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/cross_vehicle_uazbus_avoid_derisk.py --full
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

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402
import phase4_e2prime_chrono_two_regime_hardened as e2p  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

VARIANT = "uazbus_tmeasy"
UAZBUS_MASS = 2858.0  # measured total mass in Chrono
DT = 0.02
MAX_STEPS = 285  # match the avoidance episode horizon (ramp_policy MAX_STEPS)

AVOID_REVEALS = e2p.CLEAN_REVEALS    # (9.5, 12.0, 16.0, 22.0, 30.0)
AVOID_MUS = e2p.MU_POINTS            # (0.3625, 0.5875, 0.8125, 1.0375)
# Entry-speed probe grid for V_KNOTS measurement (m/s); a fine ladder so the
# safe-entry boundary is located to ~0.5 m/s.
ENTRY_SPEED_LADDER = (4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0)
# V_KNOTS are measured at the SAME mu knots the Sedan oracle uses, on a
# mid/tight reveal where the safe-entry constraint actually binds.
V_KNOTS_MU_KNOTS = (0.30, 0.55, 0.85, 1.15)
V_KNOTS_REVEAL = 16.0  # binding reveal for the safe-entry probe

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "cross_vehicle_uazbus_derisk"
RESULT_JSON = RUN_DIR / "avoid_derisk.json"
STDERR_LOG = RUN_DIR / "avoid_chrono_worker_stderr.log"

CLAIM_BOUNDARY = (
    "Cross-vehicle DE-RISK only: measures UAZBUS rear static load + safe-entry "
    "speed vs mu on Chrono, builds a UAZBUS-parameterized copy of the avoid "
    "oracle (Sedan module untouched), and compares its avoid success on the "
    "UAZBUS reveal x mu grid against the unmodified Sedan-fitted oracle, to test "
    "whether the avoid teacher generalizes after re-physicalization before the "
    "full cross-vehicle build. No protected module is modified; no training; no "
    "promotion; no paper claim."
)


def _load_regime_copy(name: str):
    """Load a FRESH, independent copy of ramp_policy_voi_regime.py under a unique
    module name (so patching its globals never touches the on-disk file nor the
    protected import path used elsewhere)."""
    path = SCRIPTS_DIR / "ramp_policy_voi_regime.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _e2_context_for(reg):
    """Build the (mod_b, interp) the scenario/controller helpers need, using
    the SAME task-design + conditional-prior modules the regime module uses."""
    mod_b = reg.load_module(reg.TASK_B_SCRIPT, f"{reg.__name__}_task_b")
    mod_c = reg.load_module(reg.COND_SCRIPT, f"{reg.__name__}_cond")
    return mod_b, mod_c.interp_lin


def _uaz_scenario(reg, mod_b, interp, *, reveal: float, mu: float, seed: int) -> dict[str, Any]:
    scenario = e2_smoke._make_scenario(reg, mod_b, interp, reveal=float(reveal), mu=float(mu),
                                       seed=int(seed), variant=VARIANT)
    # Thread the real UAZBUS mass (what the cross-vehicle build does); the
    # default AutoDrift analytic mass (1450) is NOT UAZBUS.
    scenario["params"]["mass"] = UAZBUS_MASS
    scenario["max_steps"] = int(MAX_STEPS)
    scenario["scenario_id"] = f"uazavoid-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    return scenario


def _avoid_success(info: dict[str, Any]) -> bool:
    """F2 _avoidance_success semantics: no collision, no off-track, completion in
    {obstacle_pass, max_steps}."""
    collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
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
        "rear_static_load_n": backend.get("_rear_static_load_n"),
    }


class _RestartingRunner:
    """Tiny restart-on-error wrapper (the worker occasionally dies on a hard
    Chrono solve)."""

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


# --------------------------------------------------------- (A) measure FZR -----
def measure_rear_static_load(runner: _RestartingRunner, reg, mod_b, interp) -> dict[str, Any]:
    """Read UAZBUS rear axle static normal load from a settled reset diagnostic."""
    scenario = _uaz_scenario(reg, mod_b, interp, reveal=30.0, mu=0.6, seed=12345)
    client = runner._ensure()
    obs, reply = client.reset(scenario, episode_id="fzr-probe", seed=1)
    info = reply.get("info", {})
    tel = info.get("tire_telemetry", []) or []
    rear = [r for r in tel if str(r.get("axle")) == "rear"]
    front = [r for r in tel if str(r.get("axle")) == "front"]
    rear_total = float(sum(abs(float(r.get("normal_load_n", 0.0))) for r in rear))
    front_total = float(sum(abs(float(r.get("normal_load_n", 0.0))) for r in front))
    bi = reply.get("backend_info", {})
    return {
        "rear_axle_static_load_n": round(rear_total, 1),
        "front_axle_static_load_n": round(front_total, 1),
        "rear_per_wheel_static_load_n": round(rear_total / max(len(rear), 1), 1),
        "rear_fraction": round(rear_total / max(rear_total + front_total, 1e-6), 4),
        "vehicle_total_mass": bi.get("vehicle_total_mass"),
        "wheelbase_m": bi.get("chrono_wheelbase_m"),
    }


# ------------------------------------------- (B) measure safe-entry V_KNOTS ----
def measure_v_knots(runner: _RestartingRunner, reg, mod_b, interp, *, seeds: list[int],
                    quick: bool) -> dict[str, Any]:
    """For each mu knot, drive UAZBUS straight at the obstacle at increasing
    entry speeds (swerve-only commitment = the standard safe-entry probe) and
    find the MAX entry speed that still clears across all seeds (the UAZBUS
    safe-entry speed for that mu). Reveal is fixed at a binding tier."""
    ladder = ENTRY_SPEED_LADDER if not quick else (5.5, 7.5, 9.5, 11.0)
    mu_knots = V_KNOTS_MU_KNOTS
    design = reg.make_design(mod_b, V_KNOTS_REVEAL)
    out: dict[str, Any] = {"reveal_m": V_KNOTS_REVEAL, "mu_knots": list(mu_knots),
                           "entry_speed_ladder": list(ladder), "per_mu": []}
    v_knots: list[float] = []
    for mu in mu_knots:
        safe_max = 0.0
        ladder_rows = []
        for v in ladder:
            plan = mod_b.PlanSpec(name=f"swerve_v{v:g}", v_entry=float(v), brake_to=None, steer_cap=0.85)
            n_ok = 0
            for seed in seeds:
                scenario = _uaz_scenario(reg, mod_b, interp, reveal=V_KNOTS_REVEAL, mu=float(mu), seed=seed)
                # force the entry speed: set the straight-line entry vx to v
                scenario["initial_state"]["vx"] = float(v)
                scenario["initial_state"]["vy"] = 0.0
                scenario["speed_ref"] = float(v)
                controller = mod_b.CommitmentController(plan, design)
                res = runner.run(scenario, controller, seed=seed)
                n_ok += int(res["success"])
            cleared = n_ok == len(seeds)
            ladder_rows.append({"entry_speed_mps": float(v), "cleared_all": cleared,
                                "n_ok": n_ok, "n": len(seeds)})
            if cleared:
                safe_max = float(v)
        v_knots.append(safe_max)
        out["per_mu"].append({"mu": float(mu), "safe_entry_speed_mps": safe_max, "ladder": ladder_rows})
        print(f"  [V_KNOTS] mu={mu:.2f} -> safe_entry_speed={safe_max:.1f} m/s", flush=True)
    out["v_knots_mps"] = v_knots
    return out


# ----------------------------------------- (C) re-physicalize the oracle -------
def _patch_regime_for_uazbus(reg, *, fzr: float, mass: float, v_knots: tuple[float, ...]) -> None:
    """Patch a FRESH regime-module copy in place with measured UAZBUS physics.

    Mutates: FZR (rear static load), MASS, V_KNOTS (safe-entry knots), and the
    derived MU_CENSOR. The oracle's _limit_est uses TIRE_CAP*FZR*mu; v_star uses
    V_KNOTS; the shortfall detector uses MASS/FZR. Patching all of them makes the
    oracle's brake-force ceiling and entry-speed law physical for UAZBUS.
    """
    reg.FZR = float(fzr)
    reg.MASS = float(mass)
    reg.V_KNOTS = tuple(float(v) for v in v_knots)
    reg.MU_CENSOR = reg.MAX_BRAKE / (reg.TIRE_CAP * reg.FZR)


def _oracle_builder(reg, mod_b, interp, *, reveal: float, mu: float) -> Callable[[], Any]:
    design = reg.make_design(mod_b, float(reveal))
    return lambda: reg.RampPolicyController(
        mod_b, interp, design, f"oracle_dv0_{reg.__name__}", mode="oracle", mu_true=float(mu), dv=0.0)


# ------------------------------------------------- (D) grid comparison ---------
def run_avoid_grid(runner: _RestartingRunner, reg_uaz, reg_sedan, mb_u, interp_u, mb_s, interp_s,
                   *, seeds: list[int], quick: bool) -> dict[str, Any]:
    reveals = AVOID_REVEALS if not quick else (16.0, 30.0)
    mus = AVOID_MUS if not quick else (0.3625, 0.8125)
    grid = [(float(r), float(m)) for r in reveals for m in mus]
    rows = []
    n_uaz_ok = n_sedan_ok = n_total = 0
    for reveal, mu in grid:
        uaz_b = _oracle_builder(reg_uaz, mb_u, interp_u, reveal=reveal, mu=mu)
        sedan_b = _oracle_builder(reg_sedan, mb_s, interp_s, reveal=reveal, mu=mu)
        for seed in seeds:
            scenario = _uaz_scenario(reg_uaz, mb_u, interp_u, reveal=reveal, mu=mu, seed=seed)
            r_uaz = runner.run(scenario, uaz_b(), seed=seed)
            # same scenario (identical geometry) for the Sedan-fitted oracle
            scenario_s = _uaz_scenario(reg_sedan, mb_s, interp_s, reveal=reveal, mu=mu, seed=seed)
            r_sedan = runner.run(scenario_s, sedan_b(), seed=seed)
            n_total += 1
            n_uaz_ok += int(r_uaz["success"])
            n_sedan_ok += int(r_sedan["success"])
            rows.append({
                "reveal": reveal, "mu": mu, "seed": seed,
                "uaz_oracle_success": r_uaz["success"], "uaz_oracle_outcome": r_uaz["outcome"],
                "uaz_oracle_margin": round(r_uaz["min_clearance_margin"], 3),
                "sedan_oracle_success": r_sedan["success"], "sedan_oracle_outcome": r_sedan["outcome"],
                "sedan_oracle_margin": round(r_sedan["min_clearance_margin"], 3),
                "variant_match": r_uaz["variant_match"] and r_sedan["variant_match"],
                "vehicle_total_mass": r_uaz["vehicle_total_mass"],
            })
        # per-cell readout
        cell = [row for row in rows if row["reveal"] == reveal and row["mu"] == mu]
        print(f"  [grid] reveal={reveal:>4.1f} mu={mu:.4f} | "
              f"uaz_oracle={sum(r['uaz_oracle_success'] for r in cell)}/{len(cell)} "
              f"sedan_oracle={sum(r['sedan_oracle_success'] for r in cell)}/{len(cell)}", flush=True)
    return {
        "grid_cells": len(grid),
        "n_episodes_per_oracle": n_total,
        "uaz_oracle_avoid_success": round(n_uaz_ok / max(n_total, 1), 4),
        "sedan_oracle_avoid_success": round(n_sedan_ok / max(n_total, 1), 4),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--seeds", type=int, default=0)
    args = parser.parse_args()
    quick = not args.full
    if args.quick:
        quick = True
    n_seeds = args.seeds or (1 if quick else 3)
    seeds = [101 + i for i in range(n_seeds)]

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()

    # fresh module copies: one stays Sedan (baseline oracle), one gets patched
    reg_sedan = _load_regime_copy("uaz_avoid_regime_sedan")
    reg_uaz = _load_regime_copy("uaz_avoid_regime_uaz")
    mb_s, interp_s = _e2_context_for(reg_sedan)
    mb_u, interp_u = _e2_context_for(reg_uaz)

    runner = _RestartingRunner()
    try:
        print(f"[uaz-avoid] variant={VARIANT} mass={UAZBUS_MASS} seeds={seeds}", flush=True)
        print("[A] measuring UAZBUS rear static load (FZR) ...", flush=True)
        fzr_info = measure_rear_static_load(runner, reg_uaz, mb_u, interp_u)
        measured_fzr = float(fzr_info["rear_axle_static_load_n"])
        print(f"    rear_axle_static_load FZR = {measured_fzr:.1f} N "
              f"(Sedan-fitted oracle FZR = {reg_sedan.FZR:.1f} N); "
              f"rear_fraction={fzr_info['rear_fraction']}", flush=True)

        print("[B] measuring UAZBUS safe-entry speed vs mu (V_KNOTS) ...", flush=True)
        v_knots_info = measure_v_knots(runner, reg_uaz, mb_u, interp_u, seeds=seeds, quick=quick)
        measured_v_knots = tuple(v_knots_info["v_knots_mps"])
        print(f"    UAZBUS V_KNOTS = {measured_v_knots}  (Sedan oracle V_KNOTS = {reg_sedan.V_KNOTS})", flush=True)

        print("[C] re-physicalizing the oracle (patching FZR/MASS/V_KNOTS on the UAZBUS copy) ...", flush=True)
        _patch_regime_for_uazbus(reg_uaz, fzr=measured_fzr, mass=UAZBUS_MASS, v_knots=measured_v_knots)
        print(f"    patched reg_uaz: FZR={reg_uaz.FZR:.1f} MASS={reg_uaz.MASS:.1f} "
              f"V_KNOTS={reg_uaz.V_KNOTS} MU_CENSOR={reg_uaz.MU_CENSOR:.4f}", flush=True)

        print("[D] running both oracles on the UAZBUS avoidance grid (reveal x mu) ...", flush=True)
        grid = run_avoid_grid(runner, reg_uaz, reg_sedan, mb_u, interp_u, mb_s, interp_s,
                              seeds=seeds, quick=quick)
    finally:
        runner.close()

    uaz_succ = grid["uaz_oracle_avoid_success"]
    sedan_succ = grid["sedan_oracle_avoid_success"]
    rephys_avoids_well = bool(uaz_succ >= 0.80)
    payload = {
        "protocol": "cross_vehicle_uazbus_avoid_derisk",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": VARIANT,
        "uazbus_mass_kg": UAZBUS_MASS,
        "sedan_oracle_constants": {"FZR_n": reg_sedan.FZR, "MASS_kg": reg_sedan.MASS,
                                   "V_KNOTS_mps": list(reg_sedan.V_KNOTS), "MU_KNOTS": list(reg_sedan.MU_KNOTS)},
        "measured_uazbus_fzr": fzr_info,
        "measured_uazbus_v_knots": v_knots_info,
        "rephysicalized_oracle_constants": {"FZR_n": reg_uaz.FZR, "MASS_kg": reg_uaz.MASS,
                                            "V_KNOTS_mps": list(reg_uaz.V_KNOTS)},
        "grid": grid,
        "rephysicalized_oracle_avoid_success": uaz_succ,
        "sedan_fitted_oracle_avoid_success": sedan_succ,
        "rephysicalized_oracle_avoids_well": rephys_avoids_well,
        "elapsed_s": round(time.time() - started, 1),
    }
    RESULT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("\n=== UAZBUS AVOID DE-RISK VERDICT ===")
    print(f"measured UAZBUS FZR (rear axle static load) = {measured_fzr:.1f} N "
          f"(Sedan oracle used {reg_sedan.FZR:.1f} N)")
    print(f"measured UAZBUS V_KNOTS = {measured_v_knots} @ mu {V_KNOTS_MU_KNOTS} "
          f"(Sedan oracle used {reg_sedan.V_KNOTS})")
    print(f"re-physicalized oracle avoid success on UAZBUS = {uaz_succ:.3f}")
    print(f"UNMODIFIED Sedan-fitted oracle avoid success on UAZBUS = {sedan_succ:.3f}")
    print(f"re-physicalized oracle avoids well (>=0.80): {'YES' if rephys_avoids_well else 'NO'}")
    print(f"result -> {RESULT_JSON}  [{payload['elapsed_s']}s]")


if __name__ == "__main__":
    main()
