#!/usr/bin/env python3
"""Price same-plant deliberate-slide expressibility and onset time.

M3266 follows the frozen M3265 mode-expressibility failure. It separates mode
generation from obstacle clearance, keeps the 0.12/0.20 rad ambiguous band,
and records axle-specific Chrono tire truth. It cannot decide reachable-set
dominance.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys
import threading
from typing import Any, Callable

import numpy as np

from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase5_g0_preslip_reachability_proof_pricing as g0


MILESTONE_ID = "m3266-phase5-g0b-slide-mode-onset-pricing"
SEED_BASE = 32660017
DT = 0.02
GRIP_BETA_MAX_RAD = g0.GRIP_BETA_MAX_RAD
SLIDE_BETA_MIN_RAD = g0.SLIDE_BETA_MIN_RAD
SLIDE_DWELL_STEPS = g0.SLIDE_DWELL_STEPS
REAR_SLIP_MIN_RAD = 0.15

PREREG_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing_prereg.json"
QUICK_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing_quick.json"
FULL_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_g0b_slide_mode_onset_pricing"


@dataclass(frozen=True)
class OnsetBudget:
    segments: int
    population: int
    elites: int
    iterations: int
    horizon_s: float


@dataclass(frozen=True)
class OnsetCell:
    cell_id: str
    mu: float
    speed_mps: float
    emergency_obstacle_x_m: float


QUICK_PLANAR_BUDGET = OnsetBudget(segments=6, population=20, elites=5, iterations=4, horizon_s=2.0)
FULL_PLANAR_BUDGET = OnsetBudget(segments=8, population=72, elites=14, iterations=14, horizon_s=2.4)
QUICK_CHRONO_BUDGET = OnsetBudget(segments=6, population=8, elites=2, iterations=2, horizon_s=1.8)
FULL_CHRONO_BUDGET = OnsetBudget(segments=8, population=32, elites=8, iterations=8, horizon_s=2.4)

QUICK_CELLS = (OnsetCell("quick_mu0p60_v14", 0.60, 14.0, 11.2),)
FULL_CELLS = (
    OnsetCell("mu0p35_v12", 0.35, 12.0, 11.4),
    OnsetCell("mu0p60_v14", 0.60, 14.0, 11.2),
    OnsetCell("mu0p90_v16", 0.90, 16.0, 11.2),
)


def _jsonable(value: Any) -> Any:
    return g0._jsonable(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    g0._write_json(path, payload)


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
    g0._append_progress(path, payload)


def _seed_for(*parts: Any) -> int:
    material = ":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "little") % 2_000_000_000


def _structured_slide_candidates(segments: int) -> list[np.ndarray]:
    split = max(1, segments // 2)

    power = np.zeros((segments, 3), dtype=np.float64)
    power[:split, 0] = 1.0
    power[:split, 1] = 1.0
    power[split:, 0] = -0.55
    power[split:, 1] = 0.45

    trail = np.zeros((segments, 3), dtype=np.float64)
    trail[:split, 0] = 1.0
    trail[:split, 2] = 0.85
    trail[split:, 0] = -0.65
    trail[split:, 1] = 0.70

    flick = np.zeros((segments, 3), dtype=np.float64)
    first = max(1, segments // 4)
    second = max(first + 1, segments // 2)
    flick[:first, 0] = -0.80
    flick[:first, 1] = 0.20
    flick[first:second, 0] = 1.0
    flick[first:second, 2] = 0.80
    flick[second:, 0] = -0.70
    flick[second:, 1] = 0.80

    return [power, trail, flick]


def simulate_planar_onset(
    cell: OnsetCell,
    segments: np.ndarray,
    *,
    horizon_s: float,
    initial_beta_rad: float = 0.0,
    initial_yaw_rate_rad_s: float = 0.0,
) -> dict[str, Any]:
    model = SingleTrackDriftModel(VehicleParams(mu=float(cell.mu)))
    state = VehicleState(
        x=0.0,
        y=0.0,
        psi=0.0,
        vx=float(cell.speed_mps * math.cos(initial_beta_rad)),
        vy=float(cell.speed_mps * math.sin(initial_beta_rad)),
        yaw_rate=float(initial_yaw_rate_rad_s),
    )
    steps = max(1, int(round(float(horizon_s) / DT)))
    commands = g0._expand_segments(np.asarray(segments, dtype=np.float64), steps)

    max_abs_beta = abs(float(initial_beta_rad))
    max_abs_rear_slip = 0.0
    max_rear_utilization = 0.0
    run = 0
    max_run = 0
    first_dwell_step: int | None = None
    first_dwell_x: float | None = None
    max_pre_obstacle_run = 0
    simultaneous_pedal = 0.0

    for step, command in enumerate(commands):
        steer, throttle, brake = (float(value) for value in command)
        simultaneous_pedal += throttle * brake
        state, forces = model.step(
            state,
            g0.physical_command_to_model_action(steer, throttle, brake),
            DT,
        )
        beta = abs(math.atan2(state.vy, max(abs(state.vx), 1e-9)))
        max_abs_beta = max(max_abs_beta, beta)
        max_abs_rear_slip = max(max_abs_rear_slip, abs(float(forces.alpha_rear)))
        rear_capacity = max(float(cell.mu) * float(forces.fz_rear), 1.0)
        rear_fx_fraction = min(abs(float(forces.fx_rear)) / rear_capacity, 1.0)
        rear_lat_capacity = math.sqrt(max(rear_capacity**2 * (1.0 - rear_fx_fraction**2), 1.0))
        max_rear_utilization = max(
            max_rear_utilization,
            abs(float(forces.fy_rear)) / rear_lat_capacity,
        )
        if beta >= SLIDE_BETA_MIN_RAD:
            run += 1
        else:
            run = 0
        max_run = max(max_run, run)
        if float(state.x) <= float(cell.emergency_obstacle_x_m):
            max_pre_obstacle_run = max(max_pre_obstacle_run, run)
        if run >= SLIDE_DWELL_STEPS and first_dwell_step is None:
            first_dwell_step = step - SLIDE_DWELL_STEPS + 1
            first_dwell_x = float(state.x)

    mode_valid = (
        max_run >= SLIDE_DWELL_STEPS
        and max_abs_rear_slip >= REAR_SLIP_MIN_RAD
        and max_rear_utilization >= 0.90
    )
    onset_time_s = None if first_dwell_step is None else float(first_dwell_step * DT)
    onset_x_m = first_dwell_x
    pre_obstacle_mode_valid = bool(
        mode_valid
        and first_dwell_x is not None
        and first_dwell_x <= float(cell.emergency_obstacle_x_m)
    )
    beta_progress = min(max_abs_beta / SLIDE_BETA_MIN_RAD, 1.0)
    dwell_progress = min(max_run / max(SLIDE_DWELL_STEPS, 1), 1.0)
    pre_obstacle_progress = min(max_pre_obstacle_run / max(SLIDE_DWELL_STEPS, 1), 1.0)
    onset_reward = 0.0 if onset_time_s is None else max(float(horizon_s) - onset_time_s, 0.0)
    score = (
        10_000.0 * float(mode_valid)
        + 2_000.0 * float(pre_obstacle_mode_valid)
        + 150.0 * dwell_progress
        + 100.0 * pre_obstacle_progress
        + 60.0 * beta_progress
        + 20.0 * onset_reward
        - 0.2 * simultaneous_pedal
    )
    return {
        "mode_valid": mode_valid,
        "pre_obstacle_mode_valid": pre_obstacle_mode_valid,
        "score": score,
        "max_abs_beta_rad": max_abs_beta,
        "max_abs_rear_slip_angle_rad": max_abs_rear_slip,
        "max_rear_lateral_utilization": max_rear_utilization,
        "max_slide_dwell_steps": max_run,
        "max_pre_obstacle_slide_dwell_steps": max_pre_obstacle_run,
        "first_slide_dwell_time_s": onset_time_s,
        "first_slide_dwell_x_m": onset_x_m,
        "emergency_obstacle_x_m": float(cell.emergency_obstacle_x_m),
        "final_x_m": float(state.x),
        "final_y_m": float(state.y),
        "final_yaw_rad": float(state.psi),
        "simultaneous_pedal_integral": simultaneous_pedal,
    }


def _cem_search(
    *,
    segments: int,
    population_size: int,
    elites: int,
    iterations: int,
    seed: int,
    evaluate_population: Callable[[np.ndarray], list[dict[str, Any]]],
) -> dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    mean = _structured_slide_candidates(segments)[0].copy()
    std = np.tile(np.asarray([0.50, 0.45, 0.45], dtype=np.float64), (segments, 1))
    best_segments: np.ndarray | None = None
    best_result: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    all_best_rows: list[dict[str, Any]] = []

    for iteration in range(iterations):
        population = rng.normal(mean[None], std[None], size=(population_size, segments, 3))
        population[:, :, 0] = np.clip(population[:, :, 0], -1.0, 1.0)
        population[:, :, 1:] = np.clip(population[:, :, 1:], 0.0, 1.0)
        for index, candidate in enumerate(_structured_slide_candidates(segments)[:population_size]):
            population[index] = candidate
        results = evaluate_population(population)
        scores = np.asarray([float(result["score"]) for result in results], dtype=np.float64)
        order = np.argsort(scores)[::-1]
        elite_population = population[order[:elites]]
        mean = 0.60 * mean + 0.40 * np.mean(elite_population, axis=0)
        std = np.maximum(0.60 * std + 0.40 * np.std(elite_population, axis=0), 0.05)
        top = int(order[0])
        if best_result is None or float(results[top]["score"]) > float(best_result["score"]):
            best_result = dict(results[top])
            best_segments = population[top].copy()
        history.append(
            {
                "iteration": iteration,
                "best_score": float(scores[top]),
                "mode_valid_count": sum(bool(result["mode_valid"]) for result in results),
                "pre_obstacle_mode_valid_count": sum(
                    bool(result.get("pre_obstacle_mode_valid", False)) for result in results
                ),
            }
        )
        all_best_rows.append({"iteration": iteration, **results[top]})

    assert best_result is not None and best_segments is not None
    return {
        "best": best_result,
        "best_segments_physical": best_segments,
        "history": history,
        "iteration_best_rows": all_best_rows,
    }


def search_planar_onset(cell: OnsetCell, budget: OnsetBudget, seed: int) -> dict[str, Any]:
    result = _cem_search(
        segments=budget.segments,
        population_size=budget.population,
        elites=budget.elites,
        iterations=budget.iterations,
        seed=seed,
        evaluate_population=lambda population: [
            simulate_planar_onset(cell, candidate, horizon_s=budget.horizon_s)
            for candidate in population
        ],
    )
    return {"cell_id": cell.cell_id, "seed": int(seed), "budget": asdict(budget), **result}


def _rear_front_tire_slip(info: dict[str, Any]) -> tuple[float, float, int]:
    rear: list[float] = []
    front: list[float] = []
    for row in info.get("tire_telemetry", []) or []:
        try:
            value = abs(float(row.get("slip_angle_rad", float("nan"))))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        if str(row.get("axle", "")) == "rear":
            rear.append(value)
        elif str(row.get("axle", "")) == "front":
            front.append(value)
    return max(rear, default=float("nan")), max(front, default=float("nan")), len(rear) + len(front)


def _chrono_scenario(*, quick: bool, initial_beta_rad: float = 0.0) -> dict[str, Any]:
    import phase4_f2_train as f2

    budget = QUICK_CHRONO_BUDGET if quick else FULL_CHRONO_BUDGET
    steps = int(round(budget.horizon_s / DT))
    seed = _seed_for("chrono", "scenario", "quick" if quick else "full", initial_beta_rad)
    scenario = f2._avoidance_scenario(seed, max_steps=steps, reveal=30.0, mu=0.48)
    scenario["scenario_id"] = f"{MILESTONE_ID}-chrono-{'quick' if quick else 'full'}-b{initial_beta_rad:.3f}"
    scenario["obstacle"] = {"enabled": False}
    scenario["track_width"] = 100.0
    scenario["speed_ref"] = 16.0
    scenario["initial_state"]["vx"] = 16.0 * math.cos(initial_beta_rad)
    scenario["initial_state"]["vy"] = 16.0 * math.sin(initial_beta_rad)
    scenario["initial_state"]["yaw_rate"] = 0.0
    return scenario


def _analyze_chrono_steps(step_rows: list[tuple[np.ndarray, bool, bool, str, dict]]) -> dict[str, Any]:
    max_beta = 0.0
    max_rear_slip = 0.0
    max_front_slip = 0.0
    telemetry_steps = 0
    run = 0
    max_run = 0
    first_dwell_step: int | None = None
    final_info: dict[str, Any] = {}
    for step, (_, _, _, _, info) in enumerate(step_rows):
        final_info = info
        vx = float(info.get("vx_body", 0.0))
        vy = float(info.get("vy_body", 0.0))
        beta = abs(math.atan2(vy, max(abs(vx), 1e-9)))
        max_beta = max(max_beta, beta)
        rear_slip, front_slip, wheel_count = _rear_front_tire_slip(info)
        if wheel_count > 0:
            telemetry_steps += 1
        if math.isfinite(rear_slip):
            max_rear_slip = max(max_rear_slip, rear_slip)
        if math.isfinite(front_slip):
            max_front_slip = max(max_front_slip, front_slip)
        if beta >= SLIDE_BETA_MIN_RAD:
            run += 1
        else:
            run = 0
        max_run = max(max_run, run)
        if run >= SLIDE_DWELL_STEPS and first_dwell_step is None:
            first_dwell_step = step - SLIDE_DWELL_STEPS + 1
    mode_valid = max_run >= SLIDE_DWELL_STEPS and max_rear_slip >= REAR_SLIP_MIN_RAD
    onset_time = None if first_dwell_step is None else first_dwell_step * DT
    beta_progress = min(max_beta / SLIDE_BETA_MIN_RAD, 1.0)
    dwell_progress = min(max_run / max(SLIDE_DWELL_STEPS, 1), 1.0)
    score = 10_000.0 * float(mode_valid) + 200.0 * dwell_progress + 100.0 * beta_progress
    if onset_time is not None:
        score += max(2.5 - onset_time, 0.0) * 20.0
    return {
        "mode_valid": mode_valid,
        "pre_obstacle_mode_valid": mode_valid,
        "score": score,
        "max_abs_beta_rad": max_beta,
        "max_abs_rear_tire_slip_angle_rad": max_rear_slip,
        "max_abs_front_tire_slip_angle_rad": max_front_slip,
        "finite_axle_tire_telemetry_steps": telemetry_steps,
        "max_slide_dwell_steps": max_run,
        "first_slide_dwell_time_s": onset_time,
        "collision": bool(final_info.get("collision", False)),
        "termination_reason": str(final_info.get("termination_reason", "")),
        "completion_reason": str(final_info.get("completion_reason", "")),
    }


def _evaluate_chrono_population(
    clients: list[Any],
    scenario: dict[str, Any],
    population: np.ndarray,
    steps: int,
    seed_tag: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any] | None] = [None] * len(population)
    counter = {"index": 0}
    lock = threading.Lock()

    def worker(worker_index: int) -> None:
        client = clients[worker_index]
        while True:
            with lock:
                index = counter["index"]
                counter["index"] += 1
            if index >= len(population):
                return
            physical = g0._expand_segments(population[index], steps)
            actions = np.asarray(
                [g0.physical_command_to_model_action(*command) for command in physical],
                dtype=np.float64,
            )
            client.reset(
                scenario,
                episode_id=f"{scenario['scenario_id']}-{seed_tag}-{index}",
                seed=_seed_for("chrono", seed_tag, index),
            )
            step_rows, _ = client.step_many(actions)
            results[index] = _analyze_chrono_steps(step_rows)

    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = [executor.submit(worker, worker_index) for worker_index in range(len(clients))]
        for future in futures:
            future.result()
    assert all(result is not None for result in results)
    return [dict(result) for result in results if result is not None]


def run_chrono_onset_search(*, quick: bool) -> dict[str, Any]:
    from chrono_worker_client import ChronoWorkerClient

    budget = QUICK_CHRONO_BUDGET if quick else FULL_CHRONO_BUDGET
    worker_count = 2 if quick else 8
    steps = int(round(budget.horizon_s / DT))
    clients: list[Any] = []
    try:
        clients = [ChronoWorkerClient(stderr_log=None) for _ in range(worker_count)]

        detector_scenario = _chrono_scenario(quick=quick, initial_beta_rad=0.24)
        neutral = np.zeros((steps, 3), dtype=np.float64)
        neutral[:, 1:] = 0.0
        detector_rows = _evaluate_chrono_population(
            clients[:1], detector_scenario, neutral.reshape(1, steps, 3), steps, "detector_positive"
        )
        detector = detector_rows[0]

        scenario = _chrono_scenario(quick=quick, initial_beta_rad=0.0)
        iteration = {"value": 0}

        def evaluator(population: np.ndarray) -> list[dict[str, Any]]:
            tag = f"cem{iteration['value']}"
            iteration["value"] += 1
            return _evaluate_chrono_population(clients, scenario, population, steps, tag)

        search = _cem_search(
            segments=budget.segments,
            population_size=budget.population,
            elites=budget.elites,
            iterations=budget.iterations,
            seed=_seed_for("chrono", "cem", "quick" if quick else "full"),
            evaluate_population=evaluator,
        )
        best_physical = g0._expand_segments(search["best_segments_physical"], steps)
        replay_rows = _evaluate_chrono_population(
            clients[:1], scenario, best_physical.reshape(1, steps, 3), steps, "best_replay"
        )
        best_replay = replay_rows[0]
        replay_match = all(
            (
                original is None
                and replay is None
                or isinstance(original, (int, float))
                and isinstance(replay, (int, float))
                and math.isclose(float(original), float(replay), rel_tol=0.0, abs_tol=1e-9)
                or original == replay
            )
            for key, original in search["best"].items()
            for replay in [best_replay.get(key)]
        )
        return {
            "budget": asdict(budget),
            "worker_count": worker_count,
            "detector_positive_control": detector,
            "search": search,
            "best_replay": best_replay,
            "best_replay_match": replay_match,
        }
    finally:
        for client in clients:
            try:
                client.close()
            except Exception:
                pass


def build_preregistration() -> dict[str, Any]:
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_result": "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json",
        "research_question": (
            "Can the matched detailed plants demonstrably initiate and sustain the frozen deliberate-slide mode, "
            "and what is the earliest four-frame slide onset relative to the emergency obstacle distance?"
        ),
        "claim_boundary": "mode-expressibility and onset pricing only; no reachable-set dominance",
        "frozen_mode_definition": {
            "grip_beta_max_rad": GRIP_BETA_MAX_RAD,
            "slide_beta_min_rad": SLIDE_BETA_MIN_RAD,
            "slide_dwell_steps": SLIDE_DWELL_STEPS,
            "rear_tire_slip_min_rad": REAR_SLIP_MIN_RAD,
            "ambiguous_band_policy": "0.12 < beta < 0.20 belongs to neither primary arm",
        },
        "positive_controls": {
            "literature": "retain the M3265 0.20/0.26 rad/s witness",
            "classifier": "initialize the same Chrono plant at beta=0.24 rad; detector must report a valid four-frame slide",
            "same_plant_entry": "from beta=0 with obstacle disabled, matched-action CEM must generate a valid slide",
        },
        "budgets": {
            "quick_planar": asdict(QUICK_PLANAR_BUDGET),
            "full_planar": asdict(FULL_PLANAR_BUDGET),
            "quick_chrono": asdict(QUICK_CHRONO_BUDGET),
            "full_chrono": asdict(FULL_CHRONO_BUDGET),
        },
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
            "chrono": {"mu": 0.48, "speed_mps": 16.0, "obstacle_disabled_for_entry_search": True},
        },
        "seed_discipline": {
            "seed_base": SEED_BASE,
            "planar_and_chrono": "disjoint SHA256-derived streams",
            "best_replay": "same scenario and actions; independent episode id",
        },
        "public_gates": {
            "m3265_positive_control_retained": "M3265 positive_control_pass remains true",
            "planar_same_plant_entry": "all full cells produce mode_valid=true from beta=0",
            "planar_onset_rows": "earliest dwell time/x and pre-obstacle dwell are persisted for every cell",
            "chrono_classifier": "beta=0.24 positive control is mode_valid with axle-specific telemetry",
            "chrono_same_plant_entry": "beta=0 direct CEM produces mode_valid=true with rear slip >=0.15 rad",
            "chrono_replay": "best direct-CEM trajectory replays exactly within 1e-9",
        },
        "decision_rule": {
            "admit_final_adjudication": "all gates pass",
            "block": "any gate fails; do not infer reachable-set dominance",
        },
        "forbidden_changes": [
            "lowering the 0.20 rad slide threshold or four-frame dwell after reading results",
            "adding slide-only actuator authority",
            "using aggregate all-wheel slip instead of axle-specific truth for the Chrono gate",
            "claiming a drift-only set is empty from this pricing milestone",
        ],
    }


def run(*, quick: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode_name = "quick" if quick else "full"
    planar_budget = QUICK_PLANAR_BUDGET if quick else FULL_PLANAR_BUDGET
    cells = QUICK_CELLS if quick else FULL_CELLS
    run_dir = RUN_DIR / mode_name
    progress = run_dir / "progress.jsonl"
    if progress.exists():
        progress.unlink()

    parent = json.loads(
        (REPO_ROOT / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json").read_text(
            encoding="utf-8"
        )
    )
    literature_positive_retained = bool(parent["positive_control"]["positive_control_pass"])

    planar_searches: list[dict[str, Any]] = []
    planar_rows: list[dict[str, Any]] = []
    for cell in cells:
        search = search_planar_onset(cell, planar_budget, _seed_for(mode_name, cell.cell_id, "planar"))
        planar_searches.append(search)
        row = {
            "cell_id": cell.cell_id,
            "mu": cell.mu,
            "speed_mps": cell.speed_mps,
            "emergency_obstacle_x_m": cell.emergency_obstacle_x_m,
            **search["best"],
            "best_segments_physical_json": json.dumps(
                _jsonable(search["best_segments_physical"]), separators=(",", ":")
            ),
        }
        planar_rows.append(row)
        _append_progress(progress, {"stage": "planar_done", **row})

    chrono = run_chrono_onset_search(quick=quick)
    chrono_best = dict(chrono["search"]["best"])
    chrono_detector = dict(chrono["detector_positive_control"])
    _append_progress(
        progress,
        {
            "stage": "chrono_done",
            "detector_mode_valid": chrono_detector["mode_valid"],
            "entry_mode_valid": chrono_best["mode_valid"],
            "replay_match": chrono["best_replay_match"],
        },
    )

    gates = {
        "m3265_positive_control_retained": literature_positive_retained,
        "planar_same_plant_entry_pass": all(bool(row["mode_valid"]) for row in planar_rows),
        "planar_onset_rows_pass": all(
            row["first_slide_dwell_time_s"] is not None and row["first_slide_dwell_x_m"] is not None
            for row in planar_rows
        ),
        "chrono_classifier_pass": bool(chrono_detector["mode_valid"])
        and int(chrono_detector["finite_axle_tire_telemetry_steps"]) > 0,
        "chrono_same_plant_entry_pass": bool(chrono_best["mode_valid"])
        and float(chrono_best["max_abs_rear_tire_slip_angle_rad"]) >= REAR_SLIP_MIN_RAD,
        "chrono_replay_pass": bool(chrono["best_replay_match"]),
    }
    gates["protocol_gates_passed"] = all(gates.values())
    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode_name,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "mode-expressibility and slide-onset pricing only; no reachable-set verdict",
        "planar": {
            "budget": asdict(planar_budget),
            "cells": [asdict(cell) for cell in cells],
            "searches": planar_searches,
            "best_rows": planar_rows,
        },
        "chrono": chrono,
        "gates": gates,
        "decision": "admit_final_reachable_set_adjudication" if gates["protocol_gates_passed"] else "block_proof_route",
        "dominance_claim_admitted": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }
    _write_csv(run_dir / "planar_onset_best_rows.csv", planar_rows)
    _write_csv(run_dir / "chrono_iteration_best_rows.csv", list(chrono["search"]["iteration_best_rows"]))
    _write_csv(
        run_dir / "chrono_summary_rows.csv",
        [
            {"row_type": "detector_positive_control", **chrono_detector},
            {"row_type": "entry_search_best", **chrono_best},
            {"row_type": "entry_best_replay", **chrono["best_replay"]},
        ],
    )
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
    output = QUICK_PATH if args.quick else FULL_PATH
    if args.resume and output.exists():
        print(output.relative_to(REPO_ROOT))
        return
    summary = run(quick=bool(args.quick))
    _write_json(output, summary)
    print(
        json.dumps(
            _jsonable({"path": str(output.relative_to(REPO_ROOT)), **summary["gates"], "decision": summary["decision"]}),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
