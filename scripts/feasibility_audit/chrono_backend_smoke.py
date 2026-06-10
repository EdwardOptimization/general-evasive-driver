"""A2 closed-loop smoke of the Chrono vehicle backend with the M3105 incumbent.

Runs the deployable ``ActiveSafetyReflexDriver`` (M3105 v4 incumbent, executed
in this base environment) closed-loop against ``ChronoVehicleBackend``
(executed in the pinned ``chrono`` conda env via the JSONL worker) on three
procedural circle-track scenarios at mu = 0.3 / 0.6 / 0.9, >= 320 control
steps each (termination events are recorded but do not stop the smoke loop so
the dynamics get exercised for the full horizon).

Assertions per step: observation shape (72,), all values finite, driver action
finite within [-1, 1], chassis position bounded, speed bounded, ride height
sane. Additionally measures an open-loop full-brake deceleration per mu to
quantify the effective grip mapping (Chrono TMeasy vs AutoDrift mu*g).

Deterministic: fixed scenario seeds, deterministic driver, deterministic
backend (verified by a repeat of the first scenario, compared bitwise).

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/chrono_backend_smoke.py

Output: runs/feasibility_audit/chrono_smoke_summary.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from autodrift.active_safety_reflex_driver import DRIVER_ID, ActiveSafetyReflexDriver
from autodrift.artifacts import utc_timestamp, write_json
from autodrift.chrono_vehicle_backend import BACKEND_ID, KNOWN_DIFFERENCES, smoke_scenario
from chrono_worker_client import ChronoWorkerClient

OUTPUT_JSON = REPO_ROOT / "runs/feasibility_audit/chrono_smoke_summary.json"
STDERR_LOG = REPO_ROOT / "runs/feasibility_audit/chrono_smoke_worker_stderr.log"
SMOKE_STEPS = 320
SMOKE_SEED_BASE = 901500
SMOKE_MUS = (0.3, 0.6, 0.9)
GRAVITY = 9.81

CLAIM_BOUNDARY = (
    "Chrono backend closed-loop smoke measurement only: shape/finiteness/boundedness of the "
    "backend under the incumbent driver, plus an open-loop grip-mapping probe. No "
    "driver-performance verdict, validation, ranking, promotion, repair-success, or "
    "high-fidelity-discrepancy claim is made."
)


def run_smoke_episode(client: ChronoWorkerClient, driver: ActiveSafetyReflexDriver, seed: int, mu: float) -> dict:
    scenario = smoke_scenario(seed, mu, max_steps=SMOKE_STEPS + 40)
    scenario["terminate_on_failure"] = False
    obs, reset_reply = client.reset(scenario, episode_id=scenario["scenario_id"], seed=seed)
    checks = {
        "obs_shape_72_all_steps": obs.shape == (72,),
        "obs_finite_all_steps": bool(np.all(np.isfinite(obs))),
        "action_finite_all_steps": True,
        "action_in_range_all_steps": True,
        "position_bounded_all_steps": True,
        "speed_bounded_all_steps": True,
        "ride_height_sane_all_steps": True,
    }
    speeds: list[float] = []
    lat_errors: list[float] = []
    action_abs_max = 0.0
    failure_events: list = []
    trace_signature: list[float] = [float(np.sum(obs, dtype=np.float64))]
    steps_run = 0
    for _ in range(SMOKE_STEPS):
        action = driver.act(obs)
        if not np.all(np.isfinite(action)):
            checks["action_finite_all_steps"] = False
        if np.max(np.abs(action)) > 1.0 + 1e-6:
            checks["action_in_range_all_steps"] = False
        action_abs_max = max(action_abs_max, float(np.max(np.abs(action))))
        obs, terminated, truncated, status, info = client.step(action)
        steps_run += 1
        trace_signature.append(float(np.sum(obs, dtype=np.float64)))
        if obs.shape != (72,):
            checks["obs_shape_72_all_steps"] = False
        if not np.all(np.isfinite(obs)):
            checks["obs_finite_all_steps"] = False
        if abs(float(info["x"])) > 300.0 or abs(float(info["y"])) > 300.0:
            checks["position_bounded_all_steps"] = False
        if float(info["speed"]) > 35.0:
            checks["speed_bounded_all_steps"] = False
        if not (0.0 <= float(info["z"]) <= 0.6):
            checks["ride_height_sane_all_steps"] = False
        speeds.append(float(info["speed"]))
        lat_errors.append(float(info["lateral_error"]))
        failure_events = info.get("failure_events", failure_events)
        if terminated:
            break  # only true terminations terminate (terminate_on_failure=False)
    return {
        "scenario_id": scenario["scenario_id"],
        "seed": int(seed),
        "mu": float(mu),
        "speed_ref": float(scenario["speed_ref"]),
        "steps_run": steps_run,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "speed_mean": float(np.mean(speeds)),
        "speed_max": float(np.max(speeds)),
        "abs_lateral_error_mean": float(np.mean(np.abs(lat_errors))),
        "abs_lateral_error_max": float(np.max(np.abs(lat_errors))),
        "action_abs_max": action_abs_max,
        "failure_events": failure_events,
        "min_clearance_margin": float(info["min_clearance_margin"]),
        "obstacle_passed_raw": bool(info["obstacle_passed_raw"]),
        "trace_signature_sum": float(np.sum(trace_signature)),
        "trace_signature_first8": trace_signature[:8],
    }


def run_brake_probe(client: ChronoWorkerClient, mu: float) -> dict:
    """Open-loop full-brake from 12 m/s on a straight to measure effective grip."""

    scenario = smoke_scenario(700000 + int(mu * 100), mu, max_steps=400)
    scenario["terminate_on_failure"] = False
    scenario["obstacle"]["enabled"] = False
    scenario["initial_state"].update({"x": 18.0, "y": 0.0, "psi": math.pi / 2, "vx": 12.0, "vy": 0.0, "yaw_rate": 0.0})
    obs, _ = client.reset(scenario, episode_id=f"brake-probe-mu{mu:g}")
    brake_action = np.array([0.0, -1.0, 1.0], dtype=np.float32)
    v_prev = None
    decels: list[float] = []
    for _ in range(200):
        obs, terminated, truncated, status, info = client.step(brake_action)
        speed = float(info["speed"])
        if v_prev is not None and speed > 1.5:
            decels.append((v_prev - speed) / float(scenario["dt"]))
        v_prev = speed
        if speed < 1.2:
            break
    peak = float(np.max(decels)) if decels else float("nan")
    mean = float(np.mean(sorted(decels, reverse=True)[: max(len(decels) // 2, 1)])) if decels else float("nan")
    return {
        "mu": float(mu),
        "autodrift_mu_g": float(mu * GRAVITY),
        "peak_decel_mps2": peak,
        "sustained_decel_mps2": mean,
        "effective_mu_peak": peak / GRAVITY,
        "effective_mu_over_scenario_mu": (peak / GRAVITY) / mu,
        "samples": len(decels),
    }


def main() -> None:
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    driver = ActiveSafetyReflexDriver()
    episodes = []
    try:
        for index, mu in enumerate(SMOKE_MUS):
            row = run_smoke_episode(client, driver, SMOKE_SEED_BASE + index, mu)
            episodes.append(row)
            print(
                f"mu={mu:g} steps={row['steps_run']} all_checks_pass={row['all_checks_pass']} "
                f"speed_mean={row['speed_mean']:.2f} |lat_err|_max={row['abs_lateral_error_max']:.2f} "
                f"failure_events={row['failure_events']}"
            )
        repeat = run_smoke_episode(client, driver, SMOKE_SEED_BASE, SMOKE_MUS[0])
        determinism_identical = (
            repeat["trace_signature_sum"] == episodes[0]["trace_signature_sum"]
            and repeat["trace_signature_first8"] == episodes[0]["trace_signature_first8"]
        )
        print(f"determinism repeat identical: {determinism_identical}")
        brake_rows = [run_brake_probe(client, mu) for mu in SMOKE_MUS]
        for row in brake_rows:
            print(
                f"brake probe mu={row['mu']:g}: peak {row['peak_decel_mps2']:.2f} m/s^2 "
                f"(mu*g={row['autodrift_mu_g']:.2f}, ratio {row['effective_mu_over_scenario_mu']:.2f})"
            )
    finally:
        client.close()

    status_pass = (
        all(row["all_checks_pass"] for row in episodes)
        and all(row["steps_run"] >= 300 for row in episodes)
        and determinism_identical
    )
    summary = {
        "milestone": "feasibility-route-hf-backend-a2-chrono-smoke",
        "generated_at_utc": utc_timestamp(),
        "result_class": "chrono_backend_smoke_pass" if status_pass else "chrono_backend_smoke_failed",
        "status_pass": bool(status_pass),
        "backend_id": BACKEND_ID,
        "runtime_driver_id": DRIVER_ID,
        "driver_execution_env": "base (torch available)",
        "backend_execution_env": "conda env 'chrono' (pychrono 10.0.0) via JSONL worker",
        "control_dt_s": 0.02,
        "internal_step_s": 0.001,
        "substeps_per_control_step": 20,
        "smoke_steps_per_scenario": SMOKE_STEPS,
        "scenario_mus": list(SMOKE_MUS),
        "episodes": episodes,
        "determinism_repeat_identical": bool(determinism_identical),
        "grip_mapping_brake_probe": brake_rows,
        "known_differences": list(KNOWN_DIFFERENCES),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_JSON, summary)
    print(f"status_pass={status_pass}")
    print(f"summary={OUTPUT_JSON}")


if __name__ == "__main__":
    main()
