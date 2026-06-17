"""Cross-vehicle DE-RISK (1/2): does UAZBUS achieve controlled drift on Chrono?

Before the full ~12-18 day cross-vehicle build (docs/north-star-2026-06.md
"Piece (2) cross-vehicle"), prove the DRIFT teacher generalizes to UAZBUS (the
recommended heavy RWD/4WD 2nd vehicle). The drift TEACHER is E4's
``DriftFeedbackPolicy`` (state feedback on obs72 sideslip/yaw; NO mass/grip
literals -- gains are re-tunable). The drift CELL params (mu/speed/initial_beta/
yaw_rate_scale) are Sedan-tuned and must be re-tuned per vehicle.

This script does NOT modify any protected module. It imports E4's frozen
machinery (DriftFeedbackPolicy, _obs_kinematics, _rear_saturation, the
controlled_drift criterion, run-episode loop logic) read-only and runs it on a
UAZBUS scenario (chrono_vehicle_variant=uazbus_tmeasy + a UAZBUS params block:
measured mass 2858, its Chrono geometry). It SWEEPS the cell params and a grid
of DriftFeedbackSpec gains to find a setting where UAZBUS achieves
controlled_drift sustained >= MIN_SUSTAIN (24) steps on Chrono.

Reuses the EXACT E4 success criterion so the number is directly comparable:
controlled_drift = |beta| >= 0.10 AND rear_saturated AND 2 <= vx <= 28 AND
|yaw| <= 2.7; drift_success = longest run of controlled_drift >= 24.

Run (from repo root; base env -- the worker spawns the chrono env itself):
    PYTHONPATH=src python scripts/feasibility_audit/cross_vehicle_uazbus_drift_derisk.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/cross_vehicle_uazbus_drift_derisk.py --full
"""

from __future__ import annotations

import argparse
import itertools
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

import phase4_e4_drift_regime_pricing as e4  # noqa: E402  (read-only reuse)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

VARIANT = "uazbus_tmeasy"
# Measured in Chrono (cross_vehicle probe): UAZBUS total mass 2858 kg, wheelbase
# 2.30 m, max_steer 0.471 rad, rear axle static load ~14463 N. The backend only
# consumes params.mass/mu/actuator-tau; iz/lf/lr/cf/cr are inert for Chrono (it
# uses the UAZBUS vehicle's own inertia/geometry), so we thread the measured
# total mass and leave single-track params as documentation of the real vehicle.
UAZBUS_MASS = 2858.0
UAZBUS_WHEELBASE = 2.30
DT = e4.DT
TRACK_WIDTH = e4.TRACK_WIDTH
MAX_STEPS = e4.MAX_STEPS  # 90, same episode length E4 priced the Sedan drift on
MIN_SUSTAIN = e4.MIN_SUSTAIN_STEPS  # 24

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "cross_vehicle_uazbus_derisk"
RESULT_JSON = RUN_DIR / "drift_derisk.json"
STDERR_LOG = RUN_DIR / "drift_chrono_worker_stderr.log"

CLAIM_BOUNDARY = (
    "Cross-vehicle DE-RISK only: re-tunes the drift CELL params + the E4 "
    "DriftFeedbackPolicy gains on a UAZBUS Chrono scenario to test whether the "
    "drift teacher generalizes (controlled_drift sustain >= 24) before the full "
    "cross-vehicle build. No protected module is modified; no training; no "
    "promotion; no paper claim."
)


# --- UAZBUS drift cell sweep grid -------------------------------------------
# Sedan's frozen E4 cell low_mu_power_oversteer: mu=0.48 speed=9 beta=0.22
# yaw_rate_scale=1.20 radius=70. UAZBUS is ~1.7x heavier & shorter wheelbase ->
# sweep around (and below) the Sedan point: lower mu (easier to break rear),
# and a speed range so the heavier vehicle can still power-oversteer at a sane,
# in-bounds speed (vx must stay 2..28 m/s for controlled_drift).
def _cell_grid(quick: bool) -> list[dict[str, Any]]:
    # Focused on the PROVEN power-oversteer region: an open-loop probe found
    # UAZBUS sustains controlled drift for the full episode at mu~0.30, v~7,
    # full throttle + hard steer (longest=90/90, beta~0.68, rear-sat 90/90). The
    # Sedan-tuned cell (mu 0.48, v 9) is too high-grip/fast for UAZBUS to break
    # the rear loose and HOLD it; lower mu + lower speed is where it drifts.
    mus = (0.25, 0.30) if quick else (0.25, 0.30, 0.35, 0.40, 0.48)
    speeds = (6.0, 7.0) if quick else (6.0, 7.0, 8.0, 9.0)
    betas = (0.22,) if quick else (0.18, 0.22, 0.26)
    yaw_scales = (1.20,) if quick else (1.20, 1.35)
    radii = (70.0,) if quick else (60.0, 70.0)
    cells: list[dict[str, Any]] = []
    for mu, speed, beta, yscale, radius in itertools.product(mus, speeds, betas, yaw_scales, radii):
        cells.append(
            {
                "cell_id": f"uaz_mu{mu:g}_v{speed:g}_b{beta:g}_y{yscale:g}_r{radius:g}",
                "mu": float(mu),
                "speed_mps": float(speed),
                "initial_beta_rad": float(beta),
                "heading_error_rad": -0.10,
                "yaw_rate_scale": float(yscale),
                "track_radius": float(radius),
                "track_width": TRACK_WIDTH,
            }
        )
    return cells


# --- DriftFeedbackPolicy gain sweep -----------------------------------------
# E4's three frozen specs are the Sedan-tuned seeds. For the heavier UAZBUS we
# add stronger-rotation / higher-throttle variants (power-oversteer on a heavy
# RWD needs more drive to break the rear; more counter-steer ff to hold it).
def _drift_specs(quick: bool) -> list[e4.DriftFeedbackSpec]:
    DriftFeedbackSpec = e4.DriftFeedbackSpec
    # The open-loop probe proved UAZBUS sustains drift under HIGH SUSTAINED
    # THROTTLE + strong steer-ff at high target_beta (~0.5-0.68). The Sedan
    # specs (target_beta 0.16-0.28, low base throttle that DROPS at the speed
    # target) let the drift die. These UAZBUS specs aim high target_beta, large
    # steer_ff, high speed_target (so throttle stays near full), and small brake.
    # DriftFeedbackPolicy throttle = clip(0.18 + throttle_gain*(speed_target-vx),
    # 0,0.65); a high speed_target keeps it pinned at the 0.65 ceiling.
    # The open-loop probe held beta~0.68 at 90/90 with a CONSTANT hard steer
    # (-0.55) + pinned full throttle. The closed-loop beta_gain/yaw_gain feedback
    # FIGHTS the drift (cuts steer when beta is high) -> beta oscillates across
    # the 0.10 controlled threshold and the sustained run breaks. So drive these
    # near-open-loop: large steer_ff, SMALL beta_gain/yaw_gain, throttle pinned.
    specs = [
        # name, target_beta, beta_gain, yaw_gain, steer_ff, speed_target, throttle_gain, brake_gain
        DriftFeedbackSpec("uaz_ol_steer0p55", 0.50, 0.25, 0.05, 0.55, 20.0, 0.45, 0.0),
        DriftFeedbackSpec("uaz_ol_steer0p50", 0.45, 0.30, 0.08, 0.50, 18.0, 0.42, 0.0),
        DriftFeedbackSpec("uaz_ol_steer0p60", 0.55, 0.20, 0.05, 0.60, 22.0, 0.48, 0.0),
    ]
    if not quick:
        specs += [
            DriftFeedbackSpec("uaz_ol_steer0p55_b0p40", 0.40, 0.35, 0.10, 0.55, 18.0, 0.45, 0.0),
            DriftFeedbackSpec("uaz_ol_steer0p65", 0.60, 0.15, 0.04, 0.65, 22.0, 0.50, 0.0),
            DriftFeedbackSpec("uaz_ol_steer0p50_softfb", 0.45, 0.40, 0.12, 0.50, 18.0, 0.42, 0.0),
            DriftFeedbackSpec("uaz_ol_steer0p55_lowsp", 0.50, 0.25, 0.05, 0.55, 16.0, 0.40, 0.0),
        ]
        # keep the 3 Sedan-tuned seeds as a negative control (they should fail)
        specs += list(e4.DRIFT_FEEDBACK_SPECS)
    return specs


def _scenario_for_uaz_cell(cell: dict[str, Any], *, seed: int) -> dict[str, Any]:
    """A UAZBUS drift scenario mirroring e4.scenario_for_cell exactly, with the
    variant + measured UAZBUS mass swapped in (single-track params are inert for
    the Chrono backend but kept for documentation)."""
    rng = np.random.default_rng(seed)
    radius = float(cell["track_radius"])
    speed = float(cell["speed_mps"]) + float(rng.normal(0.0, 0.20))
    beta = float(cell["initial_beta_rad"]) + float(rng.normal(0.0, 0.015))
    heading_error = float(cell["heading_error_rad"]) + float(rng.normal(0.0, 0.010))
    yaw_rate = float(cell["yaw_rate_scale"]) * speed / radius
    return {
        "scenario_id": f"uazdrift-{cell['cell_id']}-seed{seed}",
        "dt": DT,
        "max_steps": MAX_STEPS,
        "track_kind": "circle",
        "track_radius": radius,
        "track_width": float(cell["track_width"]),
        "road_lookahead_count": 8,
        "road_lookahead_spacing": 5.0,
        "obstacle_slots": 4,
        "obstacle_relative_velocity_mode": "ego",
        "soft_offtrack_metric_enabled": False,
        "soft_offtrack_tolerance_m": 0.0,
        "chrono_vehicle_variant": VARIANT,
        "params": {
            "mass": UAZBUS_MASS,
            "mu": float(cell["mu"]),
            "max_steer": 0.62,
            "max_steer_rate": 3.5,
            "max_drive_force": 8200.0,
            "max_brake_force": 6000.0,
            "drive_tau": 0.08,
            "steer_tau": 0.06,
            "iz": 4800.0,
            "lf": 1.1,
            "lr": 1.2,
            "cf": 110000.0,
            "cr": 130000.0,
        },
        "initial_state": {
            "x": radius,
            "y": 0.0,
            "psi": math.pi / 2.0 + heading_error,
            "vx": speed * math.cos(beta),
            "vy": speed * math.sin(beta),
            "yaw_rate": yaw_rate,
        },
        "speed_ref": speed,
        "obstacle": {"enabled": False},
        "warmup_gate": {"enabled": False},
        "friction_step": {"at": None, "new_mu": None},
        "terminate_on_failure": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--seeds", type=int, default=0, help="override seeds-per-(cell,spec)")
    args = parser.parse_args()
    quick = not args.full  # default = quick smoke unless --full
    if args.quick:
        quick = True
    seeds_per = args.seeds or (1 if quick else 3)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    cells = _cell_grid(quick)
    specs = _drift_specs(quick)
    started = time.time()

    print(f"[uaz-drift] variant={VARIANT} mass={UAZBUS_MASS} cells={len(cells)} "
          f"specs={len(specs)} seeds/pair={seeds_per} "
          f"(combos={len(cells)*len(specs)*seeds_per})", flush=True)

    runner = e4.RestartingChronoRunner(STDERR_LOG)
    sweep_rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    try:
        for cell in cells:
            side = float(cell["initial_beta_rad"])
            for spec in specs:
                runs = []
                for si in range(seeds_per):
                    seed = abs(hash((cell["cell_id"], spec.name, si))) % 2_000_000_000
                    scenario = _scenario_for_uaz_cell(cell, seed=seed)
                    policy = e4.DriftFeedbackPolicy(spec, side=side)
                    result = runner.run(scenario, policy, seed=seed)
                    runs.append(result)
                longest = max(int(r["longest_controlled_drift_run"]) for r in runs)
                successes = sum(int(r["drift_success"]) for r in runs)
                row = {
                    "cell_id": cell["cell_id"],
                    "mu": cell["mu"],
                    "speed_mps": cell["speed_mps"],
                    "initial_beta_rad": cell["initial_beta_rad"],
                    "yaw_rate_scale": cell["yaw_rate_scale"],
                    "track_radius": cell["track_radius"],
                    "spec": spec.name,
                    "spec_params": spec.__dict__,
                    "seeds": seeds_per,
                    "successes": successes,
                    "best_longest_controlled_drift_run": longest,
                    "mean_longest_controlled_drift_run": round(
                        float(np.mean([r["longest_controlled_drift_run"] for r in runs])), 2),
                    "best_max_abs_beta_rad": round(max(r["max_abs_beta_rad"] for r in runs), 4),
                    "best_rear_saturation_steps": max(r["rear_saturation_steps"] for r in runs),
                    "best_max_rear_slip_angle_rad": round(max(r["max_rear_slip_angle_rad"] for r in runs), 4),
                    "best_max_rear_longitudinal_slip": round(max(r["max_rear_longitudinal_slip"] for r in runs), 4),
                    # E4's run_episode compares against its own VARIANT (sedan);
                    # re-check the real backend variant against ours instead.
                    "variant_match": all(
                        r.get("backend_info", {}).get("chrono_vehicle_variant") == VARIANT for r in runs),
                    "vehicle_total_mass": runs[0].get("backend_info", {}).get("vehicle_total_mass"),
                    "first_failure_reasons": sorted({r["first_failure_reason"] for r in runs if r["first_failure_reason"]}),
                }
                sweep_rows.append(row)
                key = (longest, successes)
                if best is None or key > (best["best_longest_controlled_drift_run"], best["successes"]):
                    best = row
                print(f"  {cell['cell_id']:42s} {spec.name:26s} "
                      f"longest={longest:3d} succ={successes}/{seeds_per} "
                      f"beta_max={row['best_max_abs_beta_rad']:.3f} "
                      f"rearsat_steps={row['best_rear_saturation_steps']:3d}", flush=True)
    finally:
        runner.close()

    any_drift = bool(best and best["best_longest_controlled_drift_run"] >= MIN_SUSTAIN)
    payload = {
        "protocol": "cross_vehicle_uazbus_drift_derisk",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": VARIANT,
        "uazbus_mass_kg": UAZBUS_MASS,
        "uazbus_wheelbase_m": UAZBUS_WHEELBASE,
        "min_sustain_steps": MIN_SUSTAIN,
        "max_steps": MAX_STEPS,
        "controlled_drift_criterion": (
            "|beta|>=0.10 AND rear_saturated AND 2<=vx<=28 AND |yaw|<=2.7; "
            "drift_success = longest run of controlled_drift >= 24 (exact E4 criterion)"
        ),
        "n_cells": len(cells),
        "n_specs": len(specs),
        "seeds_per_pair": seeds_per,
        "uazbus_drifts": any_drift,
        "best": best,
        "sweep_rows": sweep_rows,
        "elapsed_s": round(time.time() - started, 1),
    }
    RESULT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("\n=== UAZBUS DRIFT DE-RISK VERDICT ===")
    if best:
        print(f"best cell: {best['cell_id']}  spec: {best['spec']}")
        print(f"best longest_controlled_drift_run = {best['best_longest_controlled_drift_run']} "
              f"(MIN_SUSTAIN={MIN_SUSTAIN})  successes={best['successes']}/{seeds_per}")
        print(f"best max|beta| = {best['best_max_abs_beta_rad']:.3f} rad  "
              f"rear_sat_steps = {best['best_rear_saturation_steps']}")
    print(f"UAZBUS achieves controlled drift (sustain>={MIN_SUSTAIN}): {'YES' if any_drift else 'NO'}")
    print(f"result -> {RESULT_JSON}  [{payload['elapsed_s']}s]")


if __name__ == "__main__":
    main()
