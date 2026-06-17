"""S1 scenario-spectrum FEASIBILITY PRE-CHECK (the first step, robotics-recipe style: ground the frozen
spectrum in DATA, not guesses). Sweeps the drift master-variable grid (target beta* x mu x entry speed) on
the Sedan and runs the parameterized DriftFeedbackSpec ORACLE in Chrono per cell, measuring the longest
controlled_drift run vs the sustain threshold. A cell is FEASIBLE if some teacher law clears sustain>=24
(it can break+hold the rear) and NON-TRIVIAL (the rear actually saturates). Emits the feasible-cell list
that the pre-registered S1 spectrum freezes. Oracle rollouts only — NO training. (docs/coverage-spectrum-
design-2026-06.md "Feasibility pre-check"; robotics-recipes-for-autodrift-2026-06.md DR philosophy.)

Run (base env; the worker spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/spectrum_s1_feasibility_precheck.py
"""
from __future__ import annotations
import itertools, json, math, sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", Path(__file__).resolve().parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import phase4_e4_drift_regime_pricing as e4  # noqa: E402

VARIANT = "sedan_tmeasy"
SEDAN_MASS = 1684.0
DT, MAX_STEPS, TRACK_WIDTH = e4.DT, e4.MAX_STEPS, e4.TRACK_WIDTH
MIN_SUSTAIN = e4.MIN_SUSTAIN_STEPS  # 24
OUT = REPO / "runs/feasibility_audit/spectrum_s1/feasibility_precheck.json"
LOG = REPO / "runs/feasibility_audit/spectrum_s1/precheck_stderr.log"

# the drift master-variable grid (docs/coverage-spectrum-design-2026-06.md table A)
MUS = (0.35, 0.45, 0.55)
BETAS = (0.18, 0.28, 0.36, 0.45)
SPEEDS = (7.0, 9.0, 12.0)       # entry speed matters for feasibility (BMW needed v16; sweep a band)
RADIUS = 70.0


_TUNED = {round(s.target_beta, 2): s for s in e4.DRIFT_FEEDBACK_SPECS}  # 0.16/0.22/0.28, beta_gain 2.0-3.2


def specs_for(beta: float):
    """Use the EXISTING TUNED DriftFeedbackSpec laws (beta_gain 2.0-3.2 — these are what actually
    establish+hold the Sedan drift; the canonical do-both cell uses beta0p28_recover) for the betas they
    cover, and EXTRAPOLATE from the 0.28 tuned spec (keeping its strong gains) for the higher targets."""
    t16, t22, t28 = _TUNED[0.16], _TUNED[0.22], _TUNED[0.28]
    if beta <= 0.20:
        return [t16, t22]
    if beta <= 0.30:
        return [t22, t28]
    # beta* 0.36 / 0.45: extrapolate from the strong 0.28 spec — raise target + steer_ff, keep gains.
    mk = lambda b, sff: e4.DriftFeedbackSpec(  # noqa: E731
        f"b{b:g}_x", b, t28.beta_gain, t28.yaw_gain, sff, t28.speed_target, t28.throttle_gain, t28.brake_gain)
    if beta <= 0.40:
        return [mk(0.36, 0.38), t28]
    return [mk(0.45, 0.46), mk(0.40, 0.42)]


def scen(mu, speed, beta, seed):
    rng = np.random.default_rng(seed)
    speed = speed + float(rng.normal(0.0, 0.1))
    return {
        "scenario_id": f"s1-mu{mu:g}-v{speed:g}-b{beta:g}-s{seed}", "dt": DT, "max_steps": MAX_STEPS,
        "track_kind": "circle", "track_radius": RADIUS, "track_width": TRACK_WIDTH,
        "road_lookahead_count": 8, "road_lookahead_spacing": 5.0, "obstacle_slots": 4,
        "obstacle_relative_velocity_mode": "ego", "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0, "chrono_vehicle_variant": VARIANT,
        "params": {"mass": SEDAN_MASS, "mu": mu, "max_steer": 0.62, "max_steer_rate": 3.5,
                   "max_drive_force": 8200.0, "max_brake_force": 6000.0, "drive_tau": 0.08,
                   "steer_tau": 0.06, "iz": 2800.0, "lf": 1.30, "lr": 1.48, "cf": 110000.0, "cr": 130000.0},
        "initial_state": {"x": RADIUS, "y": 0.0, "psi": math.pi / 2.0 - 0.10,
                          "vx": speed * math.cos(beta), "vy": speed * math.sin(beta),
                          "yaw_rate": 1.20 * speed / RADIUS},
        "speed_ref": speed, "obstacle": {"enabled": False}, "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None}, "terminate_on_failure": False,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    runner = e4.RestartingChronoRunner(LOG)
    cells = []
    n = len(MUS) * len(BETAS)
    print(f"[s1-precheck] Sedan drift feasibility: {n} (mu,beta) cells x {len(SPEEDS)} speeds x 2 specs", flush=True)
    try:
        for mu, beta in itertools.product(MUS, BETAS):
            best = {"longest": 0, "beta_max": 0.0, "rearsat": 0, "speed": None, "spec": None}
            for speed in SPEEDS:
                for spec in specs_for(beta):
                    seed = abs(hash((mu, beta, speed, spec.name))) % 2_000_000_000
                    r = runner.run(scen(mu, speed, beta, seed),
                                   e4.DriftFeedbackPolicy(spec, side=beta), seed=seed)
                    lg = int(r["longest_controlled_drift_run"])
                    if lg > best["longest"]:
                        best = {"longest": lg, "beta_max": round(r["max_abs_beta_rad"], 3),
                                "rearsat": int(r["rear_saturation_steps"]), "speed": speed, "spec": spec.name}
            feasible = best["longest"] >= MIN_SUSTAIN and best["rearsat"] >= MIN_SUSTAIN
            cells.append({"mu": mu, "beta": beta, **best, "feasible": bool(feasible)})
            tag = "FEASIBLE" if feasible else ("near" if best["longest"] >= 18 else "infeasible")
            print(f"  mu={mu:.2f} beta*={beta:.2f} | best sustain={best['longest']:3d} @v{best['speed']} "
                  f"beta_max={best['beta_max']:.3f} rearsat={best['rearsat']:3d} spec={best['spec']} -> {tag}", flush=True)
    finally:
        runner.close()
    feas = [c for c in cells if c["feasible"]]
    OUT.write_text(json.dumps({"variant": VARIANT, "mass": SEDAN_MASS, "min_sustain": MIN_SUSTAIN,
                               "grid": {"mu": MUS, "beta": BETAS, "speed": SPEEDS}, "cells": cells,
                               "feasible_cells": feas}, indent=2))
    print(f"\n=== FEASIBLE-CELL LIST: {len(feas)}/{len(cells)} cells ===")
    for c in feas:
        print(f"  mu={c['mu']:.2f} beta*={c['beta']:.2f} v{c['speed']} sustain={c['longest']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
