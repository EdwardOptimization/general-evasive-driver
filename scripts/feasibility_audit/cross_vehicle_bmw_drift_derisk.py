"""Cross-vehicle DE-RISK (1/2): does BMW_E90 achieve controlled drift on Chrono?

Mirrors cross_vehicle_uazbus_drift_derisk.py exactly, swapping the UAZBUS variant/
mass for BMW_E90 (a registered RWD sporty sedan). Before the full BMW do-both
build, prove the DRIFT teacher (E4's ``DriftFeedbackPolicy``, state feedback on
obs72 sideslip/yaw; NO mass/grip literals) generalizes to BMW_E90. The drift CELL
params (mu/speed/initial_beta/yaw_rate_scale) are Sedan-tuned and re-tuned here.

BMW_E90 is a LIGHTER RWD sporty car (native mass ~1800 kg) than UAZBUS (2858) and
the Sedan (1450 forced). Its controllable-drift mu/speed will differ from both, so
this SWEEPS the cell mu (between the UAZBUS 0.25 and the Sedan 0.48) + speed + a
grid of DriftFeedbackSpec gains to find a setting where BMW achieves
controlled_drift sustained >= MIN_SUSTAIN (24) steps on Chrono.

Reuses the EXACT E4 success criterion: controlled_drift = |beta| >= 0.10 AND
rear_saturated AND 2 <= vx <= 28 AND |yaw| <= 2.7; drift_success = longest run of
controlled_drift >= 24.

Run (from repo root; base env -- the worker spawns the chrono env itself):
    conda run -n base python scripts/feasibility_audit/cross_vehicle_bmw_drift_derisk.py --quick
    conda run -n base python scripts/feasibility_audit/cross_vehicle_bmw_drift_derisk.py --full
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
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_e4_drift_regime_pricing as e4  # noqa: E402  (read-only reuse)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

VARIANT = "bmw_e90_tmeasy"
# Measured in Chrono (cross_vehicle probe): BMW_E90 native total mass ~1800 kg
# (chrono_base_vehicle_mass=1800.1), wheelbase 2.776 m, max_steer 0.4363 rad,
# rear axle static load ~9060 N at the native mass. The backend matches total
# mass to params.mass; iz/lf/lr/cf/cr are inert for Chrono (it uses the BMW
# vehicle's own inertia/geometry), so we thread the native mass and leave
# single-track params as documentation of the real vehicle.
BMW_MASS = 1800.0
BMW_WHEELBASE = 2.776
DT = e4.DT
TRACK_WIDTH = e4.TRACK_WIDTH
MAX_STEPS = e4.MAX_STEPS  # 90, same episode length E4 priced the Sedan drift on
MIN_SUSTAIN = e4.MIN_SUSTAIN_STEPS  # 24

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "cross_vehicle_bmw_derisk"
RESULT_JSON = RUN_DIR / "drift_derisk.json"
STDERR_LOG = RUN_DIR / "drift_chrono_worker_stderr.log"

CLAIM_BOUNDARY = (
    "Cross-vehicle DE-RISK only: re-tunes the drift CELL params + the E4 "
    "DriftFeedbackPolicy gains on a BMW_E90 Chrono scenario to test whether the "
    "drift teacher generalizes (controlled_drift sustain >= 24) before the full "
    "BMW do-both build. No protected module is modified; no training; no "
    "promotion; no paper claim."
)


# --- BMW drift cell sweep grid ----------------------------------------------
# Sedan's frozen E4 cell low_mu_power_oversteer: mu=0.48 speed=9 beta=0.22
# yaw_rate_scale=1.20 radius=70. UAZBUS (heavier) drifted at mu0.25 v6. BMW is
# lighter RWD/sporty -> bracket the two: sweep mu 0.25..0.48 and a speed range
# so the lighter vehicle can break the rear loose and HOLD it at an in-bounds
# speed (vx must stay 2..28 m/s for controlled_drift).
def _cell_grid(quick: bool) -> list[dict[str, Any]]:
    # Full sweep spans the controllable-drift envelope: mu 0.20..0.48 (incl. the
    # UAZBUS-winning 0.25 and below), speed 5..9, and BOTH a low and a HIGH entry
    # beta (the open-loop trace showed higher seeded beta gives BMW its longest
    # controlled run, so 0.30 gives the teacher its best shot). yaw_scale/radius
    # are fixed to representative values (the trace confirmed r60/r70 + yaw 1.20
    # behave equivalently) to keep the official sweep tractable.
    # CORRECTION (high-speed probe _bmw_uaz_highspeed_drift_probe.py): BMW's controllable-drift
    # regime is at HIGHER entry speed (~v16) than the original v5-9 sweep — open-loop already reached
    # sustain 23/24 at v16. The original (5,6,7,9) sweep UNDER-SWEPT and wrongly returned a hard
    # negative. Re-aim the cell at the high-speed regime where BMW actually breaks the rear loose.
    mus = (0.25, 0.40) if quick else (0.20, 0.25, 0.30, 0.40, 0.48)
    speeds = (14.0, 16.0, 18.0) if quick else (12.0, 14.0, 16.0, 18.0, 20.0)
    betas = (0.30,) if quick else (0.28, 0.30)
    yaw_scales = (1.20,) if quick else (1.20,)
    radii = (70.0,) if quick else (70.0,)
    cells: list[dict[str, Any]] = []
    for mu, speed, beta, yscale, radius in itertools.product(mus, speeds, betas, yaw_scales, radii):
        cells.append(
            {
                "cell_id": f"bmw_mu{mu:g}_v{speed:g}_b{beta:g}_y{yscale:g}_r{radius:g}",
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
# Same near-open-loop family that proved on UAZBUS: large steer_ff, high
# target_beta, high speed_target (so throttle stays pinned at the 0.65 ceiling),
# SMALL beta_gain/yaw_gain (so the feedback does not fight the drift). For the
# LIGHTER BMW we also add a slightly lower-throttle / lower-target_beta variant
# (less drive may be needed to break a lighter rear) plus the Sedan/UAZBUS seeds
# as negative/positive controls.
def _drift_specs(quick: bool) -> list[e4.DriftFeedbackSpec]:
    DriftFeedbackSpec = e4.DriftFeedbackSpec
    specs = [
        # name, target_beta, beta_gain, yaw_gain, steer_ff, speed_target, throttle_gain, brake_gain
        DriftFeedbackSpec("bmw_ol_steer0p50", 0.45, 0.30, 0.08, 0.50, 18.0, 0.42, 0.0),
        DriftFeedbackSpec("bmw_ol_steer0p55", 0.50, 0.25, 0.05, 0.55, 20.0, 0.45, 0.0),
        DriftFeedbackSpec("bmw_ol_steer0p45_b0p35", 0.35, 0.30, 0.08, 0.45, 16.0, 0.40, 0.0),
        # high-steer variants the high-speed probe found winning (steer 0.60-0.62, open-loop hit 23 @v16)
        DriftFeedbackSpec("bmw_ol_steer0p60_hi", 0.55, 0.18, 0.04, 0.60, 22.0, 0.50, 0.0),
        DriftFeedbackSpec("bmw_ol_steer0p62_hi", 0.58, 0.15, 0.03, 0.62, 24.0, 0.52, 0.0),
    ]
    if not quick:
        specs += [
            DriftFeedbackSpec("bmw_ol_steer0p60", 0.55, 0.20, 0.05, 0.60, 22.0, 0.48, 0.0),
            DriftFeedbackSpec("bmw_ol_steer0p40_b0p30", 0.30, 0.35, 0.10, 0.40, 15.0, 0.38, 0.0),
            DriftFeedbackSpec("bmw_ol_steer0p50_softfb", 0.45, 0.40, 0.12, 0.50, 18.0, 0.42, 0.0),
            DriftFeedbackSpec("bmw_ol_steer0p55_lowsp", 0.50, 0.25, 0.05, 0.55, 16.0, 0.40, 0.0),
        ]
        # keep the 3 Sedan-tuned seeds as a negative control (they should fail)
        specs += list(e4.DRIFT_FEEDBACK_SPECS)
    return specs


def _scenario_for_bmw_cell(cell: dict[str, Any], *, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    radius = float(cell["track_radius"])
    speed = float(cell["speed_mps"]) + float(rng.normal(0.0, 0.20))
    beta = float(cell["initial_beta_rad"]) + float(rng.normal(0.0, 0.015))
    heading_error = float(cell["heading_error_rad"]) + float(rng.normal(0.0, 0.010))
    yaw_rate = float(cell["yaw_rate_scale"]) * speed / radius
    return {
        "scenario_id": f"bmwdrift-{cell['cell_id']}-seed{seed}",
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
            "mass": BMW_MASS,
            "mu": float(cell["mu"]),
            "max_steer": 0.62,
            "max_steer_rate": 3.5,
            "max_drive_force": 8200.0,
            "max_brake_force": 6000.0,
            "drive_tau": 0.08,
            "steer_tau": 0.06,
            "iz": 2800.0,
            "lf": 1.30,
            "lr": 1.48,
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

    print(f"[bmw-drift] variant={VARIANT} mass={BMW_MASS} cells={len(cells)} "
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
                    scenario = _scenario_for_bmw_cell(cell, seed=seed)
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
        "protocol": "cross_vehicle_bmw_drift_derisk",
        "claim_boundary": CLAIM_BOUNDARY,
        "variant": VARIANT,
        "bmw_mass_kg": BMW_MASS,
        "bmw_wheelbase_m": BMW_WHEELBASE,
        "min_sustain_steps": MIN_SUSTAIN,
        "max_steps": MAX_STEPS,
        "controlled_drift_criterion": (
            "|beta|>=0.10 AND rear_saturated AND 2<=vx<=28 AND |yaw|<=2.7; "
            "drift_success = longest run of controlled_drift >= 24 (exact E4 criterion)"
        ),
        "n_cells": len(cells),
        "n_specs": len(specs),
        "seeds_per_pair": seeds_per,
        "bmw_drifts": any_drift,
        "best": best,
        "sweep_rows": sweep_rows,
        "elapsed_s": round(time.time() - started, 1),
    }
    RESULT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print("\n=== BMW_E90 DRIFT DE-RISK VERDICT ===")
    if best:
        print(f"best cell: {best['cell_id']}  spec: {best['spec']}")
        print(f"best longest_controlled_drift_run = {best['best_longest_controlled_drift_run']} "
              f"(MIN_SUSTAIN={MIN_SUSTAIN})  successes={best['successes']}/{seeds_per}")
        print(f"best max|beta| = {best['best_max_abs_beta_rad']:.3f} rad  "
              f"rear_sat_steps = {best['best_rear_saturation_steps']}")
    print(f"BMW_E90 achieves controlled drift (sustain>={MIN_SUSTAIN}): {'YES' if any_drift else 'NO'}")
    print(f"result -> {RESULT_JSON}  [{payload['elapsed_s']}s]")


if __name__ == "__main__":
    main()
