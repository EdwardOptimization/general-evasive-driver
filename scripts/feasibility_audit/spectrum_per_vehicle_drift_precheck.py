"""PER-VEHICLE drift feasibility pre-check over the FROZEN S1 drift spectrum (12 beta* x mu cells),
for the FINAL integrated driver build (distill_both_final_integrated.py).

WHY: the integrated driver trains ONE FiLM network over the full drift+avoid spectrum x ALL 3
vehicles. The 36 avoid cells are scenario-defined (vehicle-agnostic geometry, run on each
vehicle's variant/mass + re-physicalized oracle). The 12 DRIFT cells (beta*{0.18,0.28,0.36,0.45}
x mu{0.35,0.45,0.55}), however, are physics-feasible at DIFFERENT entry speeds per vehicle
(Sedan ~v12, UAZBUS power-oversteers at low speed ~v6, BMW only drifts at HIGH speed ~v16). So
before pooling drift demos we must GROUND each vehicle's feasible (cell, speed, spec) set in
Chrono DATA, not guesses -- exactly the robotics-recipe feasibility-precheck philosophy that
spectrum_s1_feasibility_precheck.py used for the Sedan.

This module reuses spectrum_s1_feasibility_precheck's machinery (the 12-cell grid via
precheck.MUS/BETAS + specs_for, the e4 RestartingChronoRunner + DriftFeedbackPolicy oracle +
the EXACT controlled_drift sustain>=24 success criterion) but threads each vehicle's variant +
measured mass + a per-vehicle ENTRY-SPEED BAND and a per-vehicle CANDIDATE SPEC SET (the Sedan
strong-gain specs_for laws PLUS the per-vehicle de-risked DriftFeedbackPolicy spec that the
cross-vehicle de-risk proved establishes+holds that vehicle's drift). A cell is FEASIBLE for a
vehicle if some (speed, spec) clears sustain>=24 AND the rear actually saturates>=24 (non-trivial
drift). Oracle rollouts only -- NO training.

The Sedan result is ALREADY known (12/12 @v12, runs/.../spectrum_s1/feasibility_precheck.json);
we re-run it here too for a single uniform artifact, but it can be skipped with --vehicles.

Run (base env; the worker spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/spectrum_per_vehicle_drift_precheck.py \
        --vehicles uazbus bmw --full
    PYTHONPATH=src python scripts/feasibility_audit/spectrum_per_vehicle_drift_precheck.py \
        --vehicles sedan uazbus bmw
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (REPO_ROOT / "src", SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import phase4_e4_drift_regime_pricing as e4  # noqa: E402  (DriftFeedbackPolicy/Spec + runner, read-only)
import spectrum_s1_feasibility_precheck as precheck  # noqa: E402  (12-cell grid + specs_for, read-only)
import distill_both_uazbus as uaz  # noqa: E402  (UAZBUS variant/mass/drift spec)
import distill_both_bmw as bmw  # noqa: E402  (BMW variant/mass/drift spec)

OUT_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "spectrum_s1"
DEFAULT_OUT = OUT_DIR / "feasibility_precheck_per_vehicle.json"

DT, MAX_STEPS, TRACK_WIDTH = e4.DT, e4.MAX_STEPS, e4.TRACK_WIDTH
MIN_SUSTAIN = e4.MIN_SUSTAIN_STEPS  # 24
RADIUS = 70.0

# The FROZEN drift spectrum (same 12 cells the Sedan full-scenario used).
MUS = precheck.MUS      # (0.35, 0.45, 0.55)
BETAS = precheck.BETAS  # (0.18, 0.28, 0.36, 0.45)


# --- per-vehicle config: variant, mass, entry-speed band, extra candidate spec --------------
# The speed band is where each vehicle's controllable-drift regime LIVES (the de-risk findings):
#   Sedan  -- v12 (precheck-confirmed 12/12).
#   UAZBUS -- heavy RWD/4WD power-oversteers at LOW speed (~v6); sweep a low band.
#   BMW    -- only drifts at HIGH entry speed (~v16); sweep a high band.
# The candidate spec set = the Sedan strong-gain specs_for(beta) laws (which establish+hold the
# Sedan drift) PLUS the per-vehicle de-risked DriftFeedbackPolicy spec (the cross-vehicle de-risk
# winner for that vehicle). A cell clears if ANY (speed, spec) sustains controlled drift >= 24.
def _vehicle_cfg(name: str) -> dict[str, Any]:
    if name == "sedan":
        return {"variant": precheck.VARIANT, "mass": precheck.SEDAN_MASS,
                "speeds": (9.0, 12.0, 14.0), "extra_specs": ()}
    if name == "uazbus":
        return {"variant": uaz.VARIANT, "mass": uaz.UAZBUS_MASS,
                "speeds": (5.0, 6.0, 7.0, 8.0), "extra_specs": (uaz.UAZBUS_DRIFT_SPEC,)}
    if name == "bmw":
        return {"variant": bmw.VARIANT, "mass": bmw.BMW_MASS,
                "speeds": (12.0, 14.0, 16.0, 18.0), "extra_specs": (bmw.BMW_DRIFT_SPEC,)}
    raise ValueError(f"unknown vehicle {name!r}")


def _candidate_specs(name: str, beta: float) -> list[e4.DriftFeedbackSpec]:
    """The Sedan strong-gain specs_for(beta) laws + the per-vehicle de-risked spec (de-duped)."""
    cfg = _vehicle_cfg(name)
    specs = list(precheck.specs_for(beta)) + list(cfg["extra_specs"])
    seen, out = set(), []
    for s in specs:
        if s.name not in seen:
            seen.add(s.name)
            out.append(s)
    return out


def _scen(name: str, mu: float, speed: float, beta: float, seed: int) -> dict[str, Any]:
    """precheck.scen() builder threaded with the vehicle's variant + measured mass."""
    cfg = _vehicle_cfg(name)
    rng = np.random.default_rng(seed)
    speed = speed + float(rng.normal(0.0, 0.1))
    return {
        "scenario_id": f"pvdrift-{name}-mu{mu:g}-v{speed:g}-b{beta:g}-s{seed}",
        "dt": DT, "max_steps": MAX_STEPS,
        "track_kind": "circle", "track_radius": RADIUS, "track_width": TRACK_WIDTH,
        "road_lookahead_count": 8, "road_lookahead_spacing": 5.0, "obstacle_slots": 4,
        "obstacle_relative_velocity_mode": "ego", "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0, "chrono_vehicle_variant": cfg["variant"],
        "params": {"mass": cfg["mass"], "mu": mu, "max_steer": 0.62, "max_steer_rate": 3.5,
                   "max_drive_force": 8200.0, "max_brake_force": 6000.0, "drive_tau": 0.08,
                   "steer_tau": 0.06, "iz": 2800.0, "lf": 1.30, "lr": 1.48, "cf": 110000.0, "cr": 130000.0},
        "initial_state": {"x": RADIUS, "y": 0.0, "psi": math.pi / 2.0 - 0.10,
                          "vx": speed * math.cos(beta), "vy": speed * math.sin(beta),
                          "yaw_rate": 1.20 * speed / RADIUS},
        "speed_ref": speed, "obstacle": {"enabled": False}, "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None}, "terminate_on_failure": False,
    }


def precheck_vehicle(name: str, runner: e4.RestartingChronoRunner) -> dict[str, Any]:
    cfg = _vehicle_cfg(name)
    speeds = cfg["speeds"]
    cells = []
    n = len(MUS) * len(BETAS)
    print(f"\n[pv-precheck:{name}] variant={cfg['variant']} mass={cfg['mass']} | "
          f"{n} (mu,beta) cells x {len(speeds)} speeds {speeds} x candidate specs", flush=True)
    for mu, beta in itertools.product(MUS, BETAS):
        best = {"longest": 0, "beta_max": 0.0, "rearsat": 0, "speed": None, "spec": None}
        for speed in speeds:
            for spec in _candidate_specs(name, beta):
                seed = abs(hash((name, mu, beta, speed, spec.name))) % 2_000_000_000
                r = runner.run(_scen(name, mu, speed, beta, seed),
                               e4.DriftFeedbackPolicy(spec, side=beta), seed=seed)
                lg = int(r["longest_controlled_drift_run"])
                if lg > best["longest"]:
                    best = {"longest": lg, "beta_max": round(r["max_abs_beta_rad"], 3),
                            "rearsat": int(r["rear_saturation_steps"]), "speed": float(speed),
                            "spec": spec.name}
        feasible = best["longest"] >= MIN_SUSTAIN and best["rearsat"] >= MIN_SUSTAIN
        cells.append({"mu": mu, "beta": beta, **best, "feasible": bool(feasible)})
        tag = "FEASIBLE" if feasible else ("near" if best["longest"] >= 18 else "infeasible")
        print(f"  mu={mu:.2f} beta*={beta:.2f} | best sustain={best['longest']:3d} @v{best['speed']} "
              f"beta_max={best['beta_max']:.3f} rearsat={best['rearsat']:3d} spec={best['spec']} -> {tag}",
              flush=True)
    feas = [c for c in cells if c["feasible"]]
    print(f"  === {name}: {len(feas)}/{len(cells)} drift cells FEASIBLE ===", flush=True)
    return {"vehicle": name, "variant": cfg["variant"], "mass": cfg["mass"],
            "speeds": list(speeds), "cells": cells, "feasible_cells": feas,
            "n_feasible": len(feas), "n_total": len(cells)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vehicles", nargs="+", default=["sedan", "uazbus", "bmw"],
                    choices=["sedan", "uazbus", "bmw"])
    ap.add_argument("--full", action="store_true", help="(no-op; kept for CLI parity)")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log = OUT_DIR / "pv_precheck_stderr.log"
    runner = e4.RestartingChronoRunner(log)
    t0 = time.time()
    out: dict[str, Any] = {"min_sustain": MIN_SUSTAIN, "grid": {"mu": list(MUS), "beta": list(BETAS)},
                           "radius": RADIUS, "per_vehicle": {}}
    try:
        for name in args.vehicles:
            out["per_vehicle"][name] = precheck_vehicle(name, runner)
    finally:
        runner.close()
    out["elapsed_s"] = round(time.time() - t0, 1)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"\n=== PER-VEHICLE DRIFT FEASIBILITY (sustain>={MIN_SUSTAIN}) ===", flush=True)
    for name, d in out["per_vehicle"].items():
        print(f"  {name:7s}: {d['n_feasible']:2d}/{d['n_total']} cells feasible "
              f"(speeds {d['speeds']})", flush=True)
    print(f"\nwrote {args.out}  ({out['elapsed_s']}s)", flush=True)


if __name__ == "__main__":
    main()
