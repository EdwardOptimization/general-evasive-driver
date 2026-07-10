#!/usr/bin/env python3
"""Price the experimental route for a pre-slip reachable-set dual proof.

M3265 is deliberately a protocol/pricing milestone. It must demonstrate that
the search can recover a known larger-control-set counterexample, can generate
both bounded-sideslip and deliberate-slide trajectories under matched plant
semantics, and can read the Chrono tire-truth fields needed by a later verdict.
It does not decide reachable-set dominance.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable

import numpy as np

from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

MILESTONE_ID = "m3265-phase5-g0-preslip-reachability-proof-pricing"
SEED_BASE = 32650017
DT = 0.02
CAR_HALF_LENGTH_M = 2.2
CAR_HALF_WIDTH_M = 0.9
GRIP_BETA_MAX_RAD = 0.12
SLIDE_BETA_MIN_RAD = 0.20
SLIDE_DWELL_STEPS = 4

PREREG_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing_prereg.json"
QUICK_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing_quick.json"
FULL_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json"
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing"


@dataclass(frozen=True)
class SearchBudget:
    segments: int
    population: int
    elites: int
    iterations: int


@dataclass(frozen=True)
class PlanarCell:
    cell_id: str
    mu: float
    speed_mps: float
    obstacle_x_m: float
    obstacle_half_width_m: float
    obstacle_half_depth_m: float
    horizon_s: float
    road_half_width_m: float = 5.0
    initial_beta_rad: float = 0.0
    initial_yaw_rate_rad_s: float = 0.0


QUICK_BUDGET = SearchBudget(segments=5, population=20, elites=5, iterations=4)
FULL_BUDGET = SearchBudget(segments=7, population=64, elites=12, iterations=12)

QUICK_CELLS = (
    PlanarCell("quick_mu0p60_v14_ttc0p90", 0.60, 14.0, 12.6, 0.85, 0.65, 1.35),
)

FULL_CELLS = (
    PlanarCell("mu0p35_v12_ttc0p95", 0.35, 12.0, 11.4, 0.80, 0.65, 1.40),
    PlanarCell("mu0p60_v14_ttc0p80", 0.60, 14.0, 11.2, 0.85, 0.65, 1.30),
    PlanarCell("mu0p90_v16_ttc0p70", 0.90, 16.0, 11.2, 0.90, 0.65, 1.20),
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(_jsonable(rows))


def _append_progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _seed_for(*parts: Any) -> int:
    material = ":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "little") % 2_000_000_000


def physical_command_to_model_action(steer: float, throttle: float, brake: float) -> np.ndarray:
    """Convert physical 0..1 pedals to the repo's normalized -1..1 action contract."""

    return np.asarray(
        [
            np.clip(steer, -1.0, 1.0),
            2.0 * np.clip(throttle, 0.0, 1.0) - 1.0,
            2.0 * np.clip(brake, 0.0, 1.0) - 1.0,
        ],
        dtype=np.float64,
    )


def _box_axes(psi: float) -> tuple[tuple[float, float], tuple[float, float]]:
    return ((math.cos(psi), math.sin(psi)), (-math.sin(psi), math.cos(psi)))


def _box_corners(
    cx: float,
    cy: float,
    psi: float,
    half_length: float,
    half_width: float,
) -> tuple[tuple[float, float], ...]:
    c = math.cos(psi)
    s = math.sin(psi)
    return tuple(
        (
            cx + sx * c - sy * s,
            cy + sx * s + sy * c,
        )
        for sx in (-half_length, half_length)
        for sy in (-half_width, half_width)
    )


def signed_sat_separation(
    a: tuple[tuple[float, float], ...],
    axes_a: tuple[tuple[float, float], ...],
    b: tuple[tuple[float, float], ...],
    axes_b: tuple[tuple[float, float], ...],
) -> float:
    """Positive when OBBs are separated, non-positive when they overlap."""

    gaps: list[float] = []
    for axis in axes_a + axes_b:
        a_proj = [point[0] * axis[0] + point[1] * axis[1] for point in a]
        b_proj = [point[0] * axis[0] + point[1] * axis[1] for point in b]
        gaps.append(max(min(b_proj) - max(a_proj), min(a_proj) - max(b_proj)))
    return max(gaps)


def _expand_segments(segments: np.ndarray, steps: int) -> np.ndarray:
    indices = np.minimum(
        (np.arange(steps, dtype=np.int64) * len(segments)) // max(steps, 1),
        len(segments) - 1,
    )
    return np.asarray(segments, dtype=np.float64)[indices]


def simulate_planar(cell: PlanarCell, segments: np.ndarray, mode: str) -> dict[str, Any]:
    params = VehicleParams(mu=float(cell.mu))
    model = SingleTrackDriftModel(params)
    beta0 = float(cell.initial_beta_rad)
    state = VehicleState(
        x=0.0,
        y=0.0,
        psi=0.0,
        vx=float(cell.speed_mps * math.cos(beta0)),
        vy=float(cell.speed_mps * math.sin(beta0)),
        yaw_rate=float(cell.initial_yaw_rate_rad_s),
    )
    steps = max(1, int(round(float(cell.horizon_s) / DT)))
    commands = _expand_segments(segments, steps)
    obstacle = _box_corners(
        float(cell.obstacle_x_m),
        0.0,
        0.0,
        float(cell.obstacle_half_depth_m),
        float(cell.obstacle_half_width_m),
    )
    obstacle_axes = _box_axes(0.0)

    min_separation = float("inf")
    max_abs_beta = 0.0
    max_abs_rear_alpha = 0.0
    max_rear_lateral_utilization = 0.0
    slide_run = 0
    max_slide_run = 0
    slide_onset_x: float | None = None
    collision = False
    offroad = False
    passed = False
    simultaneous_pedal = 0.0

    for command in commands:
        steer, throttle, brake = (float(value) for value in command)
        simultaneous_pedal += throttle * brake
        action = physical_command_to_model_action(steer, throttle, brake)
        state, forces = model.step(state, action, DT)

        beta = abs(math.atan2(state.vy, max(abs(state.vx), 1e-9)))
        max_abs_beta = max(max_abs_beta, beta)
        max_abs_rear_alpha = max(max_abs_rear_alpha, abs(float(forces.alpha_rear)))
        rear_capacity = max(float(cell.mu) * float(forces.fz_rear), 1.0)
        rear_fx_fraction = min(abs(float(forces.fx_rear)) / rear_capacity, 1.0)
        rear_lat_capacity = math.sqrt(max(rear_capacity**2 * (1.0 - rear_fx_fraction**2), 1.0))
        max_rear_lateral_utilization = max(
            max_rear_lateral_utilization,
            abs(float(forces.fy_rear)) / rear_lat_capacity,
        )

        if beta >= SLIDE_BETA_MIN_RAD:
            slide_run += 1
            if slide_onset_x is None:
                slide_onset_x = float(state.x)
        else:
            slide_run = 0
        max_slide_run = max(max_slide_run, slide_run)

        car = _box_corners(
            float(state.x),
            float(state.y),
            float(state.psi),
            CAR_HALF_LENGTH_M,
            CAR_HALF_WIDTH_M,
        )
        separation = signed_sat_separation(car, _box_axes(float(state.psi)), obstacle, obstacle_axes)
        min_separation = min(min_separation, separation)
        if separation <= 0.0:
            collision = True
            break

        lateral_projection = (
            CAR_HALF_LENGTH_M * abs(math.sin(float(state.psi)))
            + CAR_HALF_WIDTH_M * abs(math.cos(float(state.psi)))
        )
        if abs(float(state.y)) + lateral_projection > float(cell.road_half_width_m):
            offroad = True
            break

        if float(state.x) > float(cell.obstacle_x_m + cell.obstacle_half_depth_m + CAR_HALF_LENGTH_M):
            passed = True
            break

    grip_valid = max_abs_beta <= GRIP_BETA_MAX_RAD + 1e-12
    slide_valid = (
        max_slide_run >= SLIDE_DWELL_STEPS
        and slide_onset_x is not None
        and slide_onset_x <= float(cell.obstacle_x_m)
        and max_rear_lateral_utilization >= 0.90
    )
    mode_valid = grip_valid if mode == "grip" else slide_valid
    success = bool(mode_valid and passed and not collision and not offroad)
    progress = min(max(float(state.x), 0.0) / max(float(cell.obstacle_x_m), 1e-6), 1.5)
    if mode == "grip":
        mode_progress = max(0.0, 1.0 - max(max_abs_beta - GRIP_BETA_MAX_RAD, 0.0) / 0.20)
    else:
        beta_progress = min(max_abs_beta / SLIDE_BETA_MIN_RAD, 1.0)
        dwell_progress = min(max_slide_run / max(SLIDE_DWELL_STEPS, 1), 1.0)
        mode_progress = beta_progress * dwell_progress
    bounded_separation = float(np.clip(min_separation, -3.0, 3.0))
    score = (
        10_000.0 * float(mode_valid)
        + 1_000.0 * float(success)
        + 100.0 * mode_progress
        + 20.0 * bounded_separation
        + 5.0 * progress
        - 0.2 * simultaneous_pedal
    )
    return {
        "mode": mode,
        "mode_valid": mode_valid,
        "success": success,
        "passed": passed,
        "collision": collision,
        "offroad": offroad,
        "score": score,
        "min_sat_separation_m": min_separation,
        "max_abs_beta_rad": max_abs_beta,
        "max_abs_rear_slip_angle_rad": max_abs_rear_alpha,
        "max_rear_lateral_utilization": max_rear_lateral_utilization,
        "max_slide_dwell_steps": max_slide_run,
        "slide_onset_x_m": slide_onset_x,
        "final_x_m": float(state.x),
        "final_y_m": float(state.y),
        "final_yaw_rad": float(state.psi),
        "simultaneous_pedal_integral": simultaneous_pedal,
    }


def _structured_candidates(mode: str, segments: int) -> list[np.ndarray]:
    coast = np.zeros((segments, 3), dtype=np.float64)
    coast[:, 0] = 0.85
    hard_brake = coast.copy()
    hard_brake[:, 2] = 0.55
    s_turn = coast.copy()
    s_turn[max(1, segments // 2) :, 0] = -0.25

    if mode == "grip":
        return [coast, hard_brake, s_turn]

    power = np.zeros((segments, 3), dtype=np.float64)
    split = max(1, segments // 2)
    power[:split, 0] = 1.0
    power[:split, 1] = 1.0
    power[split:, 0] = -0.45
    power[split:, 1] = 0.35
    trail = np.zeros((segments, 3), dtype=np.float64)
    trail[:split, 0] = 1.0
    trail[:split, 2] = 0.75
    trail[split:, 0] = -0.55
    trail[split:, 1] = 0.60
    return [power, trail, s_turn]


def cem_search_planar(
    cell: PlanarCell,
    mode: str,
    budget: SearchBudget,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    mean = _structured_candidates(mode, budget.segments)[0].copy()
    std = np.tile(np.asarray([0.45, 0.42, 0.42], dtype=np.float64), (budget.segments, 1))
    best_segments: np.ndarray | None = None
    best_result: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []

    for iteration in range(budget.iterations):
        population = rng.normal(
            mean[None, :, :],
            std[None, :, :],
            size=(budget.population, budget.segments, 3),
        )
        population[:, :, 0] = np.clip(population[:, :, 0], -1.0, 1.0)
        population[:, :, 1:] = np.clip(population[:, :, 1:], 0.0, 1.0)
        structured = _structured_candidates(mode, budget.segments)
        for idx, candidate in enumerate(structured[: len(population)]):
            population[idx] = candidate

        results = [simulate_planar(cell, candidate, mode) for candidate in population]
        scores = np.asarray([float(result["score"]) for result in results], dtype=np.float64)
        order = np.argsort(scores)[::-1]
        elite_idx = order[: budget.elites]
        elites = population[elite_idx]
        mean = 0.65 * mean + 0.35 * np.mean(elites, axis=0)
        std = np.maximum(0.65 * std + 0.35 * np.std(elites, axis=0), 0.05)

        top = int(order[0])
        if best_result is None or float(results[top]["score"]) > float(best_result["score"]):
            best_result = dict(results[top])
            best_segments = population[top].copy()
        history.append(
            {
                "iteration": iteration,
                "best_score": float(scores[top]),
                "mode_valid_count": sum(bool(result["mode_valid"]) for result in results),
                "success_count": sum(bool(result["success"]) for result in results),
            }
        )

    assert best_result is not None and best_segments is not None
    return {
        "cell_id": cell.cell_id,
        "mode": mode,
        "seed": int(seed),
        "budget": asdict(budget),
        "best": best_result,
        "best_segments_physical": best_segments,
        "history": history,
    }


def dubins_positive_control(
    *,
    speed_mps: float = 15.0,
    obstacle_x_m: float = 22.0,
    obstacle_radius_m: float = 3.7,
    conservative_yaw_rate_rad_s: float = 0.20,
    beyond_limit_yaw_rate_rad_s: float = 0.26,
) -> dict[str, Any]:
    """Reproduce the known larger-yaw-set emergency-control witness."""

    dt = 0.0005
    horizon = obstacle_x_m / speed_mps

    def clearance(yaw_rate: float) -> float:
        x = 0.0
        y = 0.0
        psi = 0.0
        min_distance = float("inf")
        for _ in range(int(math.ceil(horizon / dt)) + 1):
            min_distance = min(min_distance, math.hypot(x - obstacle_x_m, y))
            x += dt * speed_mps * math.cos(psi)
            y += dt * speed_mps * math.sin(psi)
            psi += dt * yaw_rate
        return min_distance - obstacle_radius_m

    conservative_clearance = clearance(conservative_yaw_rate_rad_s)
    beyond_clearance = clearance(beyond_limit_yaw_rate_rad_s)
    return {
        "source": "Zhao et al. 2022 control-set counterexample parameters",
        "speed_mps": speed_mps,
        "obstacle_x_m": obstacle_x_m,
        "obstacle_radius_m": obstacle_radius_m,
        "conservative_yaw_rate_rad_s": conservative_yaw_rate_rad_s,
        "beyond_limit_yaw_rate_rad_s": beyond_limit_yaw_rate_rad_s,
        "conservative_clearance_m": conservative_clearance,
        "beyond_limit_clearance_m": beyond_clearance,
        "positive_control_pass": conservative_clearance < 0.0 and beyond_clearance > 0.0,
    }


def _chrono_probe_profiles(steps: int) -> dict[str, np.ndarray]:
    grip = np.zeros((steps, 3), dtype=np.float64)
    grip[:, 0] = 0.48
    grip[:, 1] = 0.18

    slide = np.zeros((steps, 3), dtype=np.float64)
    split = max(1, steps // 2)
    slide[:split, 0] = 1.0
    slide[:split, 1] = 1.0
    slide[split:, 0] = -0.55
    slide[split:, 1] = 0.45
    return {"grip_probe": grip, "slide_probe": slide}


def run_chrono_connector_probe(*, quick: bool) -> dict[str, Any]:
    """Exercise matched actions and tire telemetry; this is not a Chrono verdict."""

    try:
        import phase4_f2_train as f2
        from chrono_worker_client import ChronoWorkerClient
    except Exception as exc:  # pragma: no cover - environment-specific path
        return {
            "connector_pass": False,
            "error": f"import failed: {type(exc).__name__}: {exc}",
            "rows": [],
        }

    steps = 36 if quick else 54
    scenario = f2._avoidance_scenario(
        _seed_for("chrono", "scenario", "quick" if quick else "full"),
        max_steps=steps,
        reveal=12.0,
        mu=0.48,
    )
    scenario["scenario_id"] = f"{MILESTONE_ID}-chrono-connector-{'quick' if quick else 'full'}"
    scenario["speed_ref"] = 16.0
    scenario["track_width"] = 30.0
    scenario["initial_state"]["vx"] = 16.0
    scenario["initial_state"]["vy"] = 0.0
    scenario["initial_state"]["yaw_rate"] = 0.0

    rows: list[dict[str, Any]] = []
    client = None
    try:
        client = ChronoWorkerClient(stderr_log=None)
        for profile_name, physical_commands in _chrono_probe_profiles(steps).items():
            actions = np.asarray(
                [physical_command_to_model_action(*command) for command in physical_commands],
                dtype=np.float64,
            )
            obs, reset_reply = client.reset(
                scenario,
                episode_id=f"{scenario['scenario_id']}-{profile_name}",
                seed=_seed_for("chrono", profile_name),
            )
            step_rows, _ = client.step_many(actions)
            max_beta = 0.0
            max_tire_slip = 0.0
            finite_telemetry_steps = 0
            max_slide_run = 0
            slide_run = 0
            final_info: dict[str, Any] = {}
            for _, _, _, _, info in step_rows:
                final_info = info
                vx = float(info.get("vx_body", 0.0))
                vy = float(info.get("vy_body", 0.0))
                beta = abs(math.atan2(vy, max(abs(vx), 1e-9)))
                max_beta = max(max_beta, beta)
                tire_slip = float(info.get("max_abs_tire_slip_angle_rad", float("nan")))
                if math.isfinite(tire_slip):
                    finite_telemetry_steps += 1
                    max_tire_slip = max(max_tire_slip, abs(tire_slip))
                if beta >= SLIDE_BETA_MIN_RAD:
                    slide_run += 1
                else:
                    slide_run = 0
                max_slide_run = max(max_slide_run, slide_run)
            rows.append(
                {
                    "profile": profile_name,
                    "reset_obs_finite": bool(obs.shape == (72,) and np.isfinite(obs).all()),
                    "backend_id": str(reset_reply.get("backend_id", "")),
                    "step_count": len(step_rows),
                    "finite_tire_telemetry_steps": finite_telemetry_steps,
                    "max_abs_beta_rad": max_beta,
                    "max_abs_tire_slip_angle_rad": max_tire_slip,
                    "max_slide_dwell_steps": max_slide_run,
                    "collision": bool(final_info.get("collision", False)),
                    "completion_reason": str(final_info.get("completion_reason", "")),
                    "min_clearance_margin_m": final_info.get("min_clearance_margin", None),
                }
            )
    except Exception as exc:  # pragma: no cover - environment-specific path
        return {
            "connector_pass": False,
            "error": f"runtime failed: {type(exc).__name__}: {exc}",
            "rows": rows,
        }
    finally:
        if client is not None:
            client.close()

    profiles = {str(row["profile"]): row for row in rows}
    connector_pass = (
        set(profiles) == {"grip_probe", "slide_probe"}
        and all(bool(row["reset_obs_finite"]) for row in rows)
        and all(int(row["finite_tire_telemetry_steps"]) > 0 for row in rows)
    )
    return {"connector_pass": connector_pass, "error": "", "rows": rows}


def build_preregistration() -> dict[str, Any]:
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_question": (
            "Is the dual-proof route capable of detecting a known larger-control-set drift-only witness, "
            "finding both grip-bounded and deliberate-slide candidates under matched plant semantics, and "
            "collecting Chrono tire truth before a full reachable-set adjudication?"
        ),
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "primary_scope": {
            "initial_state": "pre-slip, straight or explicitly bounded incipient-slip state",
            "road": "static, uniform scalar mu",
            "obstacle": "static, lane-aligned oriented box",
            "terminal_requirement": "collision-free pass with common road/progress constraints; no terminal yaw target",
            "actuators": "matched steering, throttle, and brake authority in both arms",
        },
        "arms": {
            "grip": f"max body sideslip <= {GRIP_BETA_MAX_RAD:.2f} rad through the obstacle pass",
            "slide": (
                f"body sideslip >= {SLIDE_BETA_MIN_RAD:.2f} rad for >= {SLIDE_DWELL_STEPS} control steps "
                "before obstacle center, with rear lateral utilization >= 0.90"
            ),
            "free": "reserved for M3266; no mode constraint",
        },
        "positive_control": {
            "source": "Zhao et al., IFAC-PapersOnLine 55(24), 2022, doi:10.1016/j.ifacol.2022.10.275",
            "frozen_parameters": {
                "speed_mps": 15.0,
                "obstacle_x_m": 22.0,
                "obstacle_radius_m": 3.7,
                "conservative_yaw_rate_rad_s": 0.20,
                "beyond_limit_yaw_rate_rad_s": 0.26,
            },
            "pass_rule": "conservative clearance < 0 and beyond-limit clearance > 0",
        },
        "search": {
            "optimizer": "matched-budget CEM over piecewise-constant physical steer/throttle/brake commands",
            "action_mapping": "physical pedals in [0,1] are mapped to repo-normalized [-1,1] before stepping",
            "quick_budget": asdict(QUICK_BUDGET),
            "full_budget": asdict(FULL_BUDGET),
            "quick_cells": [asdict(cell) for cell in QUICK_CELLS],
            "full_cells": [asdict(cell) for cell in FULL_CELLS],
            "optimizer_seed_base": SEED_BASE,
            "grip_and_slide_seed_streams": "disjoint SHA256-derived streams",
        },
        "public_gates": {
            "positive_control": "known 0.20/0.26 rad/s witness is recovered",
            "planar_mode_expressibility": "each frozen cell yields at least one mode-valid grip and slide candidate",
            "search_health": "best score is finite and each arm writes iteration history",
            "chrono_connector": "both structured profiles return finite obs72 and finite tire-slip telemetry",
            "claim_guard": "M3265 prices the proof route only and cannot establish dominance",
        },
        "decision_rule": {
            "admit_m3266": (
                "all positive-control, planar mode-expressibility, search-health, determinism, and Chrono connector gates pass"
            ),
            "block_and_reprice": "any gate fails; do not interpret absence of a drift-only cell",
        },
        "forbidden_claims": [
            "reachable-set dominance",
            "universal no-drift theorem for detailed vehicles",
            "Chrono drift-only set is empty",
            "production ESC comparison",
            "driver promotion or self-ID",
        ],
    }


def run_pricing(*, quick: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode_name = "quick" if quick else "full"
    budget = QUICK_BUDGET if quick else FULL_BUDGET
    cells = QUICK_CELLS if quick else FULL_CELLS
    run_subdir = RUN_DIR / mode_name
    progress_path = run_subdir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    positive = dubins_positive_control()
    _append_progress(progress_path, {"stage": "positive_control", **positive})

    searches: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] = []
    for cell in cells:
        for mode in ("grip", "slide"):
            seed = _seed_for(mode_name, cell.cell_id, mode)
            result = cem_search_planar(cell, mode, budget, seed)
            searches.append(result)
            best = dict(result["best"])
            best_rows.append(
                {
                    "cell_id": cell.cell_id,
                    "mode": mode,
                    "seed": seed,
                    **best,
                    "best_segments_physical_json": json.dumps(
                        _jsonable(result["best_segments_physical"]), separators=(",", ":")
                    ),
                }
            )
            _append_progress(
                progress_path,
                {
                    "stage": "planar_search_done",
                    "cell_id": cell.cell_id,
                    "mode": mode,
                    "mode_valid": best["mode_valid"],
                    "success": best["success"],
                    "score": best["score"],
                },
            )

    chrono = run_chrono_connector_probe(quick=quick)
    _append_progress(
        progress_path,
        {
            "stage": "chrono_connector_done",
            "connector_pass": chrono["connector_pass"],
            "error": chrono["error"],
        },
    )

    planar_mode_expressibility = all(bool(row["mode_valid"]) for row in best_rows)
    search_health = all(
        math.isfinite(float(search["best"]["score"])) and len(search["history"]) == budget.iterations
        for search in searches
    )
    determinism_rows: list[dict[str, Any]] = []
    for cell in cells[:1]:
        for mode in ("grip", "slide"):
            seed = _seed_for(mode_name, cell.cell_id, mode)
            rerun = cem_search_planar(cell, mode, budget, seed)
            original = next(
                search for search in searches if search["cell_id"] == cell.cell_id and search["mode"] == mode
            )
            same_score = abs(float(rerun["best"]["score"]) - float(original["best"]["score"])) <= 1e-12
            same_segments = bool(
                np.array_equal(rerun["best_segments_physical"], original["best_segments_physical"])
            )
            determinism_rows.append(
                {
                    "cell_id": cell.cell_id,
                    "mode": mode,
                    "same_score": same_score,
                    "same_segments": same_segments,
                    "pass": same_score and same_segments,
                }
            )
    determinism_pass = all(bool(row["pass"]) for row in determinism_rows)
    protocol_gates_passed = bool(
        positive["positive_control_pass"]
        and planar_mode_expressibility
        and search_health
        and determinism_pass
        and chrono["connector_pass"]
    )

    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode_name,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "proof-route pricing only; no reachable-set dominance, detailed-model theorem, promotion, paper, or self-ID claim"
        ),
        "positive_control": positive,
        "planar": {
            "budget": asdict(budget),
            "cells": [asdict(cell) for cell in cells],
            "searches": searches,
            "best_rows": best_rows,
        },
        "chrono_connector": chrono,
        "determinism_rows": determinism_rows,
        "gates": {
            "positive_control_pass": bool(positive["positive_control_pass"]),
            "planar_mode_expressibility_pass": planar_mode_expressibility,
            "search_health_pass": search_health,
            "determinism_pass": determinism_pass,
            "chrono_connector_pass": bool(chrono["connector_pass"]),
            "protocol_gates_passed": protocol_gates_passed,
        },
        "decision": "admit_m3266_full_dual_proof" if protocol_gates_passed else "block_and_reprice",
        "dominance_claim_admitted": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }

    _write_csv(run_subdir / "planar_best_rows.csv", best_rows)
    _write_csv(run_subdir / "chrono_connector_rows.csv", list(chrono["rows"]))
    _write_csv(run_subdir / "determinism_rows.csv", determinism_rows)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-prereg", action="store_true")
    group.add_argument("--quick", action="store_true")
    group.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.write_prereg:
        _write_json(PREREG_PATH, build_preregistration())
        print(PREREG_PATH.relative_to(REPO_ROOT))
        return

    output_path = QUICK_PATH if args.quick else FULL_PATH
    if args.resume and output_path.exists():
        print(output_path.relative_to(REPO_ROOT))
        return
    summary = run_pricing(quick=bool(args.quick))
    _write_json(output_path, summary)
    print(json.dumps(_jsonable({"path": str(output_path.relative_to(REPO_ROOT)), **summary["gates"], "decision": summary["decision"]}), sort_keys=True))


if __name__ == "__main__":
    main()
