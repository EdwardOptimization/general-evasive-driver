"""Cross-vehicle DE-RISK (2/2): re-physicalize the avoid oracle for BMW_E90.

Mirrors cross_vehicle_uazbus_avoid_derisk.py exactly, swapping the UAZBUS
variant/mass for BMW_E90 (a registered RWD sporty sedan). Before the full
BMW do-both build, prove the AVOIDANCE oracle generalizes to BMW_E90.

The avoid oracle (ramp_policy_voi_regime.RampPolicyController, mode='oracle') is
SEDAN-FITTED: hardcoded module globals V_KNOTS=(4.5,7.5,9.5,10.5) @ MU_KNOTS,
MASS=1450, FZR=6858.3 (rear static load). BMW_E90's native Chrono mass is
~1800 kg with a heavier rear load, so the Sedan plan may under/over-brake.

This script (NO protected module is modified):
  (A) MEASURES BMW_E90's rear static load FZR from Chrono reset tire telemetry.
  (B) MEASURES BMW_E90's safe-entry-speed-vs-mu (V_KNOTS): drive BMW straight at
      the obstacle at increasing entry speeds (swerve-only commitment) per mu,
      find the MAX entry speed that still clears on Chrono.
  (C) Builds a BMW-parameterized oracle = a FRESH copy of the regime module with
      FZR/MASS/V_KNOTS patched to the measured BMW values (Sedan module untouched).
  (D) Runs the re-physicalized oracle on the BMW avoidance grid (reveal x mu), and
      ALSO runs the UNMODIFIED Sedan-fitted oracle on BMW, on the SAME scenarios.

Success = _avoidance_success semantics: no collision, no off-track, completion in
{obstacle_pass, max_steps}.

Run (from repo root; base env -- the worker spawns the chrono env itself):
    conda run -n base python scripts/feasibility_audit/cross_vehicle_bmw_avoid_derisk.py --quick
    conda run -n base python scripts/feasibility_audit/cross_vehicle_bmw_avoid_derisk.py --full
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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

VARIANT = "bmw_e90_tmeasy"
# Measured in Chrono (cross_vehicle probe): BMW_E90 native total mass ~1800 kg
# (chrono_base_vehicle_mass=1800.1), wheelbase 2.776 m, max_steer 0.4363 rad,
# rear axle static load ~9060 N at the native mass. We thread the native mass
# (the faithful "BMW as itself" choice, mirroring UAZBUS threading its measured
# 2858) so the oracle is physicalized for the real BMW, not forced to Sedan 1450.
BMW_MASS = 1800.0
DT = 0.02
MAX_STEPS = 285  # match the avoidance episode horizon (ramp_policy MAX_STEPS)

AVOID_REVEALS = e2p.CLEAN_REVEALS    # (9.5, 12.0, 16.0, 22.0, 30.0)
AVOID_MUS = e2p.MU_POINTS            # (0.3625, 0.5875, 0.8125, 1.0375)
ENTRY_SPEED_LADDER = (4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0)
V_KNOTS_MU_KNOTS = (0.30, 0.55, 0.85, 1.15)
V_KNOTS_REVEAL = 16.0  # binding reveal for the safe-entry probe

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "cross_vehicle_bmw_derisk"
RESULT_JSON = RUN_DIR / "avoid_derisk.json"
STDERR_LOG = RUN_DIR / "avoid_chrono_worker_stderr.log"

CLAIM_BOUNDARY = (
    "Cross-vehicle DE-RISK only: measures BMW_E90 rear static load + safe-entry "
    "speed vs mu on Chrono, builds a BMW-parameterized copy of the avoid oracle "
    "(Sedan module untouched), and compares its avoid success on the BMW reveal x "
    "mu grid against the unmodified Sedan-fitted oracle, to test whether the avoid "
    "teacher generalizes after re-physicalization before the full BMW do-both "
    "build. No protected module is modified; no training; no promotion; no claim."
)


def _load_regime_copy(name: str):
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


def _bmw_scenario(reg, mod_b, interp, *, reveal: float, mu: float, seed: int) -> dict[str, Any]:
    scenario = e2_smoke._make_scenario(reg, mod_b, interp, reveal=float(reveal), mu=float(mu),
                                       seed=int(seed), variant=VARIANT)
    scenario["params"]["mass"] = BMW_MASS
    scenario["max_steps"] = int(MAX_STEPS)
    scenario["scenario_id"] = f"bmwavoid-r{reveal:g}-mu{mu:.4f}-seed{seed}"
    return scenario


def _avoid_success(info: dict[str, Any]) -> bool:
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
    }


class _RestartingRunner:
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
    scenario = _bmw_scenario(reg, mod_b, interp, reveal=30.0, mu=0.6, seed=12345)
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
        "chrono_base_vehicle_mass": bi.get("chrono_base_vehicle_mass"),
        "wheelbase_m": bi.get("chrono_wheelbase_m"),
        "max_steer_rad": bi.get("chrono_max_steer_rad"),
    }


# ------------------------------------------- (B) measure safe-entry V_KNOTS ----
def measure_v_knots(runner: _RestartingRunner, reg, mod_b, interp, *, seeds: list[int],
                    quick: bool) -> dict[str, Any]:
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
                scenario = _bmw_scenario(reg, mod_b, interp, reveal=V_KNOTS_REVEAL, mu=float(mu), seed=seed)
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
def _patch_regime_for_bmw(reg, *, fzr: float, mass: float, v_knots: tuple[float, ...]) -> None:
    reg.FZR = float(fzr)
    reg.MASS = float(mass)
    reg.V_KNOTS = tuple(float(v) for v in v_knots)
    reg.MU_CENSOR = reg.MAX_BRAKE / (reg.TIRE_CAP * reg.FZR)


def _oracle_builder(reg, mod_b, interp, *, reveal: float, mu: float) -> Callable[[], Any]:
    design = reg.make_design(mod_b, float(reveal))
    return lambda: reg.RampPolicyController(
        mod_b, interp, design, f"oracle_dv0_{reg.__name__}", mode="oracle", mu_true=float(mu), dv=0.0)


# ------------------------------------------------- (D) grid comparison ---------
def run_avoid_grid(runner: _RestartingRunner, reg_bmw, reg_sedan, mb_u, interp_u, mb_s, interp_s,
                   *, seeds: list[int], quick: bool) -> dict[str, Any]:
    reveals = AVOID_REVEALS if not quick else (16.0, 30.0)
    mus = AVOID_MUS if not quick else (0.3625, 0.8125)
    grid = [(float(r), float(m)) for r in reveals for m in mus]
    rows = []
    n_bmw_ok = n_sedan_ok = n_total = 0
    for reveal, mu in grid:
        bmw_b = _oracle_builder(reg_bmw, mb_u, interp_u, reveal=reveal, mu=mu)
        sedan_b = _oracle_builder(reg_sedan, mb_s, interp_s, reveal=reveal, mu=mu)
        for seed in seeds:
            scenario = _bmw_scenario(reg_bmw, mb_u, interp_u, reveal=reveal, mu=mu, seed=seed)
            r_bmw = runner.run(scenario, bmw_b(), seed=seed)
            scenario_s = _bmw_scenario(reg_sedan, mb_s, interp_s, reveal=reveal, mu=mu, seed=seed)
            r_sedan = runner.run(scenario_s, sedan_b(), seed=seed)
            n_total += 1
            n_bmw_ok += int(r_bmw["success"])
            n_sedan_ok += int(r_sedan["success"])
            rows.append({
                "reveal": reveal, "mu": mu, "seed": seed,
                "bmw_oracle_success": r_bmw["success"], "bmw_oracle_outcome": r_bmw["outcome"],
                "bmw_oracle_margin": round(r_bmw["min_clearance_margin"], 3),
                "sedan_oracle_success": r_sedan["success"], "sedan_oracle_outcome": r_sedan["outcome"],
                "sedan_oracle_margin": round(r_sedan["min_clearance_margin"], 3),
                "variant_match": r_bmw["variant_match"] and r_sedan["variant_match"],
                "vehicle_total_mass": r_bmw["vehicle_total_mass"],
            })
        cell = [row for row in rows if row["reveal"] == reveal and row["mu"] == mu]
        print(f"  [grid] reveal={reveal:>4.1f} mu={mu:.4f} | "
              f"bmw_oracle={sum(r['bmw_oracle_success'] for r in cell)}/{len(cell)} "
              f"sedan_oracle={sum(r['sedan_oracle_success'] for r in cell)}/{len(cell)}", flush=True)
    return {
        "grid_cells": len(grid),
        "n_episodes_per_oracle": n_total,
        "bmw_oracle_avoid_success": round(n_bmw_ok / max(n_total, 1), 4),
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

    reg_sedan = _load_regime_copy("bmw_avoid_regime_sedan")
    reg_bmw = _load_regime_copy("bmw_avoid_regime_bmw")
    mb_s, interp_s = _e2_context_for(reg_sedan)
    mb_u, interp_u = _e2_context_for(reg_bmw)

    runner = _RestartingRunner()
    try:
        print(f"[bmw-avoid] variant={VARIANT} mass={BMW_MASS} seeds={seeds}", flush=True)
        print("[A] measuring BMW_E90 rear static load (FZR) ...", flush=True)
        fzr_info = measure_rear_static_load(runner, reg_bmw, mb_u, interp_u)
        measured_fzr = float(fzr_info["rear_axle_static_load_n"])
        print(f"    rear_axle_static_load FZR = {measured_fzr:.1f} N "
              f"(Sedan-fitted oracle FZR = {reg_sedan.FZR:.1f} N); "
              f"rear_fraction={fzr_info['rear_fraction']} total_mass={fzr_info['vehicle_total_mass']}", flush=True)

        print("[B] measuring BMW_E90 safe-entry speed vs mu (V_KNOTS) ...", flush=True)
        v_knots_info = measure_v_knots(runner, reg_bmw, mb_u, interp_u, seeds=seeds, quick=quick)
        measured_v_knots = tuple(v_knots_info["v_knots_mps"])
        print(f"    BMW V_KNOTS = {measured_v_knots}  (Sedan oracle V_KNOTS = {reg_sedan.V_KNOTS})", flush=True)

        print("[C] re-physicalizing the oracle (patching FZR/MASS/V_KNOTS on the BMW copy) ...", flush=True)
        _patch_regime_for_bmw(reg_bmw, fzr=measured_fzr, mass=BMW_MASS, v_knots=measured_v_knots)
        print(f"    patched reg_bmw: FZR={reg_bmw.FZR:.1f} MASS={reg_bmw.MASS:.1f} "
              f"V_KNOTS={reg_bmw.V_KNOTS} MU_CENSOR={reg_bmw.MU_CENSOR:.4f}", flush=True)

        print("[D] running both oracles on the BMW avoidance grid (reveal x mu) ...", flush=True)
        grid = run_avoid_grid(runner, reg_bmw, reg_sedan, mb_u, interp_u, mb_s, interp_s,
                              seeds=seeds, quick=quick)
    finally:
        runner.close()

    bmw_succ = grid["bmw_oracle_avoid_success"]
    sedan_succ = grid["sedan_oracle_avoid_success"]
    rephys_avoids_well = bool(bmw_succ >= 0.80)
    payload = {
        "protocol": "cross_vehicle_bmw_avoid_derisk",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": VARIANT,
        "bmw_mass_kg": BMW_MASS,
        "sedan_oracle_constants": {"FZR_n": reg_sedan.FZR, "MASS_kg": reg_sedan.MASS,
                                   "V_KNOTS_mps": list(reg_sedan.V_KNOTS), "MU_KNOTS": list(reg_sedan.MU_KNOTS)},
        "measured_bmw_fzr": fzr_info,
        "measured_bmw_v_knots": v_knots_info,
        "rephysicalized_oracle_constants": {"FZR_n": reg_bmw.FZR, "MASS_kg": reg_bmw.MASS,
                                            "V_KNOTS_mps": list(reg_bmw.V_KNOTS)},
        "grid": grid,
        "rephysicalized_oracle_avoid_success": bmw_succ,
        "sedan_fitted_oracle_avoid_success": sedan_succ,
        "rephysicalized_oracle_avoids_well": rephys_avoids_well,
        "elapsed_s": round(time.time() - started, 1),
    }
    RESULT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("\n=== BMW_E90 AVOID DE-RISK VERDICT ===")
    print(f"measured BMW FZR (rear axle static load) = {measured_fzr:.1f} N "
          f"(Sedan oracle used {reg_sedan.FZR:.1f} N)")
    print(f"measured BMW V_KNOTS = {measured_v_knots} @ mu {V_KNOTS_MU_KNOTS} "
          f"(Sedan oracle used {reg_sedan.V_KNOTS})")
    print(f"re-physicalized oracle avoid success on BMW = {bmw_succ:.3f}")
    print(f"UNMODIFIED Sedan-fitted oracle avoid success on BMW = {sedan_succ:.3f}")
    print(f"re-physicalized oracle avoids well (>=0.80): {'YES' if rephys_avoids_well else 'NO'}")
    print(f"result -> {RESULT_JSON}  [{payload['elapsed_s']}s]")


if __name__ == "__main__":
    main()
