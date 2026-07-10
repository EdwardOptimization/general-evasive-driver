#!/usr/bin/env python3
"""Adjudicate bounded pre-slip grip versus required-slide reachable sets.

The experiment searches the minimum clearable lane-aligned OBB distance D* for
matched grip, required controlled-slide, and unconstrained free arms. Smaller D*
means a larger obstacle-avoidance feasible set. The dynamics run without an
obstacle; candidate trajectories are judged offline against the exact OBB
first-contact geometry, so collision termination cannot hide slide onset.
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
import phase5_g0b_slide_mode_onset_pricing as g0b


MILESTONE_ID = "m3267-phase5-g1-preslip-reachable-set-adjudication"
SEED_BASE = 32670017
PROTOCOL_REVISION = "r1"
INITIAL_REGISTERED_AT_UTC = "2026-07-10T08:35:30.883494+00:00"
PROTOCOL_AMENDED_AT_UTC = "2026-07-10T08:46:59+00:00"
DT = 0.02
ARMS = ("grip", "required_slide", "free")
GRIP_BETA_MAX_RAD = 0.12
SLIDE_BETA_MIN_RAD = 0.20
SLIDE_BETA_MAX_RAD = 0.60
GLOBAL_BETA_MAX_RAD = 0.70
SLIDE_DWELL_STEPS = 4
REAR_SLIP_MIN_RAD = 0.15
MIN_SPEED_MPS = 4.0
DISTANCE_MIN_M = 7.0
DISTANCE_MAX_M = 26.0
DISTANCE_TOLERANCE_M = 0.25
DISTANCE_REFINE_STEP_M = 0.10
CAR_HALF_LENGTH_M = g0.CAR_HALF_LENGTH_M
CAR_HALF_WIDTH_M = g0.CAR_HALF_WIDTH_M

PREREG_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_prereg.json"
QUICK_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json"
FULL_PATH = REPO_ROOT / "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication.json"
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication"


@dataclass(frozen=True)
class BoundaryBudget:
    segments: int
    population: int
    elites: int
    iterations: int
    search_seeds: int
    horizon_s: float


@dataclass(frozen=True)
class BoundaryCell:
    cell_id: str
    mu: float
    speed_mps: float
    obstacle_half_width_m: float = 0.85
    obstacle_half_depth_m: float = 0.65
    road_half_width_m: float = 5.0


QUICK_PLANAR_BUDGET = BoundaryBudget(8, 24, 6, 5, 1, 2.4)
FULL_PLANAR_BUDGET = BoundaryBudget(10, 72, 14, 14, 3, 2.6)
QUICK_CHRONO_BUDGET = BoundaryBudget(7, 6, 2, 2, 1, 2.2)
FULL_CHRONO_BUDGET = BoundaryBudget(9, 24, 6, 7, 2, 2.6)

QUICK_PLANAR_CELLS = (BoundaryCell("quick_planar_mu0p60_v14", 0.60, 14.0),)
FULL_PLANAR_CELLS = (
    BoundaryCell("planar_mu0p35_v12", 0.35, 12.0),
    BoundaryCell("planar_mu0p60_v14", 0.60, 14.0),
    BoundaryCell("planar_mu0p90_v16", 0.90, 16.0),
)
QUICK_CHRONO_CELLS = (BoundaryCell("quick_chrono_mu0p48_v16", 0.48, 16.0),)
FULL_CHRONO_CELLS = (
    BoundaryCell("chrono_mu0p35_v16", 0.35, 16.0),
    BoundaryCell("chrono_mu0p60_v16", 0.60, 16.0),
    BoundaryCell("chrono_mu0p90_v16", 0.90, 16.0),
)


@dataclass(frozen=True)
class TrajectoryPoint:
    x: float
    y: float
    psi: float
    speed: float
    beta: float
    rear_slip: float


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


def _resample_segments(segments: np.ndarray, count: int) -> np.ndarray:
    source = np.asarray(segments, dtype=np.float64)
    indices = np.minimum((np.arange(count) * len(source)) // max(count, 1), len(source) - 1)
    return source[indices].copy()


def _parent_slide_segments(cell_id: str, count: int, *, chrono: bool) -> np.ndarray | None:
    path = REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if chrono:
        source = payload["chrono"]["search"].get("best_segments_physical")
        return None if source is None else _resample_segments(np.asarray(source, dtype=np.float64), count)
    target_mu = None
    if "0p35" in cell_id:
        target_mu = 0.35
    elif "0p60" in cell_id:
        target_mu = 0.60
    elif "0p90" in cell_id:
        target_mu = 0.90
    candidates = payload["planar"]["searches"]
    chosen = None
    for item in candidates:
        source_cell = next(
            (row for row in payload["planar"]["cells"] if row["cell_id"] == item["cell_id"]),
            None,
        )
        if source_cell is not None and target_mu is not None and math.isclose(float(source_cell["mu"]), target_mu):
            chosen = item
            break
    if chosen is None:
        chosen = candidates[0]
    source = chosen.get("best_segments_physical")
    return None if source is None else _resample_segments(np.asarray(source, dtype=np.float64), count)


def _structured_candidates(arm: str, cell_id: str, segments: int, *, chrono: bool) -> list[np.ndarray]:
    grip = np.zeros((segments, 3), dtype=np.float64)
    grip[:, 0] = 0.75
    grip_turnback = grip.copy()
    grip_turnback[max(1, segments // 2) :, 0] = -0.20
    grip_brake = grip.copy()
    grip_brake[:, 2] = 0.30
    pulse_steps = max(1, segments // 4)
    grip_pulse_soft = np.zeros((segments, 3), dtype=np.float64)
    grip_pulse_soft[:pulse_steps, 0] = 0.45
    grip_pulse_firm = np.zeros((segments, 3), dtype=np.float64)
    grip_pulse_firm[:pulse_steps, 0] = 0.65
    grip_pulse_counter = grip_pulse_firm.copy()
    grip_pulse_counter[pulse_steps : min(2 * pulse_steps, segments), 0] = -0.25

    slide_parent = _parent_slide_segments(cell_id, segments, chrono=chrono)
    slide_candidates = g0b._structured_slide_candidates(segments)
    if slide_parent is not None:
        slide_candidates = [slide_parent, *slide_candidates]

    if arm == "grip":
        return [grip_pulse_soft, grip_pulse_firm, grip_pulse_counter, grip, grip_turnback, grip_brake]
    if arm == "required_slide":
        return slide_candidates
    return [grip_pulse_soft, grip_pulse_firm, grip_pulse_counter, grip, grip_turnback, *slide_candidates]


def simulate_planar_trajectory(cell: BoundaryCell, segments: np.ndarray, horizon_s: float) -> list[TrajectoryPoint]:
    model = SingleTrackDriftModel(VehicleParams(mu=float(cell.mu)))
    state = VehicleState(0.0, 0.0, 0.0, float(cell.speed_mps), 0.0, 0.0)
    steps = max(1, int(round(float(horizon_s) / DT)))
    commands = g0._expand_segments(np.asarray(segments, dtype=np.float64), steps)
    points: list[TrajectoryPoint] = [
        TrajectoryPoint(0.0, 0.0, 0.0, float(cell.speed_mps), 0.0, 0.0)
    ]
    for command in commands:
        state, forces = model.step(
            state,
            g0.physical_command_to_model_action(*command),
            DT,
        )
        speed = math.hypot(float(state.vx), float(state.vy))
        beta = abs(math.atan2(float(state.vy), max(abs(float(state.vx)), 1e-9)))
        points.append(
            TrajectoryPoint(
                float(state.x),
                float(state.y),
                float(state.psi),
                speed,
                beta,
                abs(float(forces.alpha_rear)),
            )
        )
    return points


def _controlled_slide_onset(points: list[TrajectoryPoint]) -> tuple[int | None, int]:
    run = 0
    max_run = 0
    onset: int | None = None
    for index, point in enumerate(points):
        controlled = (
            SLIDE_BETA_MIN_RAD <= point.beta <= SLIDE_BETA_MAX_RAD
            and point.rear_slip >= REAR_SLIP_MIN_RAD
            and point.speed >= MIN_SPEED_MPS
        )
        run = run + 1 if controlled else 0
        max_run = max(max_run, run)
        if run >= SLIDE_DWELL_STEPS and onset is None:
            onset = index - SLIDE_DWELL_STEPS + 1
    return onset, max_run


def evaluate_trajectory_at_distance(
    points: list[TrajectoryPoint],
    cell: BoundaryCell,
    arm: str,
    distance_m: float,
) -> dict[str, Any]:
    obstacle = g0._box_corners(
        float(distance_m),
        0.0,
        0.0,
        float(cell.obstacle_half_depth_m),
        float(cell.obstacle_half_width_m),
    )
    obstacle_axes = g0._box_axes(0.0)
    collision = False
    offroad = False
    passed = False
    pass_index: int | None = None
    terminal_index: int | None = None
    min_separation = float("inf")
    max_beta_until_pass = 0.0
    min_speed_until_pass = float("inf")
    contact_plane = float(distance_m - cell.obstacle_half_depth_m)

    for index, point in enumerate(points):
        car = g0._box_corners(
            point.x,
            point.y,
            point.psi,
            CAR_HALF_LENGTH_M,
            CAR_HALF_WIDTH_M,
        )
        separation = g0.signed_sat_separation(car, g0._box_axes(point.psi), obstacle, obstacle_axes)
        min_separation = min(min_separation, separation)
        max_beta_until_pass = max(max_beta_until_pass, point.beta)
        min_speed_until_pass = min(min_speed_until_pass, point.speed)
        lateral_projection = CAR_HALF_LENGTH_M * abs(math.sin(point.psi)) + CAR_HALF_WIDTH_M * abs(math.cos(point.psi))
        if abs(point.y) + lateral_projection > float(cell.road_half_width_m):
            offroad = True
            terminal_index = index
            break
        if separation <= 0.0:
            collision = True
            terminal_index = index
            break
        rear_projection = CAR_HALF_LENGTH_M * abs(math.cos(point.psi)) + CAR_HALF_WIDTH_M * abs(math.sin(point.psi))
        if point.x - rear_projection > float(distance_m + cell.obstacle_half_depth_m):
            passed = True
            pass_index = index
            terminal_index = index
            break

    considered = points if terminal_index is None else points[: terminal_index + 1]
    onset_index, max_controlled_dwell = _controlled_slide_onset(considered)
    onset_before_contact = False
    onset_front_x = None
    if onset_index is not None:
        onset_point = considered[onset_index]
        front_projection = (
            CAR_HALF_LENGTH_M * abs(math.cos(onset_point.psi))
            + CAR_HALF_WIDTH_M * abs(math.sin(onset_point.psi))
        )
        onset_front_x = onset_point.x + front_projection
        onset_before_contact = onset_front_x <= contact_plane + 1e-12

    stable = max_beta_until_pass <= GLOBAL_BETA_MAX_RAD and min_speed_until_pass >= MIN_SPEED_MPS
    grip_valid = max_beta_until_pass <= GRIP_BETA_MAX_RAD + 1e-12 and min_speed_until_pass >= MIN_SPEED_MPS
    slide_valid = (
        stable
        and onset_index is not None
        and onset_before_contact
        and max_controlled_dwell >= SLIDE_DWELL_STEPS
    )
    free_valid = stable
    mode_valid = {"grip": grip_valid, "required_slide": slide_valid, "free": free_valid}[arm]
    success = bool(mode_valid and passed and not collision and not offroad)
    if max_beta_until_pass <= GRIP_BETA_MAX_RAD:
        free_mode = "grip_like"
    elif onset_index is not None and onset_before_contact:
        free_mode = "controlled_slide_like"
    else:
        free_mode = "ambiguous_or_late_slide"
    mode_progress = 1.0
    if arm == "grip":
        mode_progress = max(0.0, 1.0 - max(max_beta_until_pass - GRIP_BETA_MAX_RAD, 0.0) / 0.30)
    elif arm == "required_slide":
        mode_progress = min(max_controlled_dwell / SLIDE_DWELL_STEPS, 1.0)
        if onset_index is not None and not onset_before_contact:
            mode_progress *= 0.5
    bounded_sep = float(np.clip(min_separation, -3.0, 3.0))
    score = (
        10_000.0 * float(mode_valid)
        + 3_000.0 * float(success)
        + 100.0 * mode_progress
        + 20.0 * bounded_sep
        - 30.0 * float(distance_m)
    )
    return {
        "arm": arm,
        "distance_m": float(distance_m),
        "mode_valid": mode_valid,
        "success": success,
        "passed": passed,
        "collision": collision,
        "offroad": offroad,
        "stable": stable,
        "score": score,
        "min_sat_separation_m": min_separation,
        "max_beta_until_pass_rad": max_beta_until_pass,
        "min_speed_until_pass_mps": min_speed_until_pass,
        "controlled_slide_onset_index": onset_index,
        "controlled_slide_onset_time_s": None if onset_index is None else onset_index * DT,
        "controlled_slide_onset_front_x_m": onset_front_x,
        "obstacle_contact_plane_x_m": contact_plane,
        "onset_before_contact": onset_before_contact,
        "max_controlled_slide_dwell_steps": max_controlled_dwell,
        "free_mode_classification": free_mode,
    }


def refine_distance_for_trajectory(
    points: list[TrajectoryPoint], cell: BoundaryCell, arm: str
) -> dict[str, Any]:
    distances = np.arange(DISTANCE_MIN_M, DISTANCE_MAX_M + 0.5 * DISTANCE_REFINE_STEP_M, DISTANCE_REFINE_STEP_M)
    rows = [evaluate_trajectory_at_distance(points, cell, arm, float(distance)) for distance in distances]
    successes = [row for row in rows if bool(row["success"])]
    if not successes:
        best = max(rows, key=lambda row: float(row["score"]))
        return {"d_star_m": None, "boundary": best, "success_count": 0}
    best = min(successes, key=lambda row: float(row["distance_m"]))
    return {"d_star_m": float(best["distance_m"]), "boundary": best, "success_count": len(successes)}


def _cem_search_joint(
    *,
    cell: BoundaryCell,
    arm: str,
    budget: BoundaryBudget,
    seed: int,
    chrono: bool,
    evaluate_population: Callable[[np.ndarray, np.ndarray], list[dict[str, Any]]],
) -> dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    structured = _structured_candidates(arm, cell.cell_id, budget.segments, chrono=chrono)
    mean = structured[0].copy()
    std = np.tile(np.asarray([0.48, 0.44, 0.44], dtype=np.float64), (budget.segments, 1))
    distance_mean = 15.0
    distance_std = 4.5
    best_actions: np.ndarray | None = None
    best_distance: float | None = None
    best_result: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []

    for iteration in range(budget.iterations):
        population = rng.normal(mean[None], std[None], size=(budget.population, budget.segments, 3))
        population[:, :, 0] = np.clip(population[:, :, 0], -1.0, 1.0)
        population[:, :, 1:] = np.clip(population[:, :, 1:], 0.0, 1.0)
        distances = np.clip(
            rng.normal(distance_mean, distance_std, size=budget.population),
            DISTANCE_MIN_M,
            DISTANCE_MAX_M,
        )
        for index, candidate in enumerate(structured[: budget.population]):
            population[index] = candidate
            distances[index] = min(11.0 + 3.0 * index, DISTANCE_MAX_M)
        results = evaluate_population(population, distances)
        scores = np.asarray([float(row["score"]) for row in results], dtype=np.float64)
        order = np.argsort(scores)[::-1]
        elite_indices = order[: budget.elites]
        elite_actions = population[elite_indices]
        elite_distances = distances[elite_indices]
        mean = 0.62 * mean + 0.38 * np.mean(elite_actions, axis=0)
        std = np.maximum(0.62 * std + 0.38 * np.std(elite_actions, axis=0), 0.04)
        distance_mean = 0.62 * distance_mean + 0.38 * float(np.mean(elite_distances))
        distance_std = max(0.62 * distance_std + 0.38 * float(np.std(elite_distances)), 0.15)
        top = int(order[0])
        if best_result is None or float(results[top]["score"]) > float(best_result["score"]):
            best_result = dict(results[top])
            best_actions = population[top].copy()
            best_distance = float(distances[top])
        history.append(
            {
                "iteration": iteration,
                "best_score": float(scores[top]),
                "best_distance_m": float(distances[top]),
                "mode_valid_count": sum(bool(row["mode_valid"]) for row in results),
                "success_count": sum(bool(row["success"]) for row in results),
            }
        )
    assert best_result is not None and best_actions is not None and best_distance is not None
    return {
        "cell_id": cell.cell_id,
        "arm": arm,
        "seed": int(seed),
        "budget": asdict(budget),
        "best_search_result": best_result,
        "best_search_distance_m": best_distance,
        "best_segments_physical": best_actions,
        "history": history,
    }


def search_planar(cell: BoundaryCell, arm: str, budget: BoundaryBudget, seed: int) -> dict[str, Any]:
    cache: dict[bytes, list[TrajectoryPoint]] = {}

    def evaluator(population: np.ndarray, distances: np.ndarray) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for actions, distance in zip(population, distances):
            key = actions.tobytes()
            points = cache.get(key)
            if points is None:
                points = simulate_planar_trajectory(cell, actions, budget.horizon_s)
                cache[key] = points
            rows.append(evaluate_trajectory_at_distance(points, cell, arm, float(distance)))
        return rows

    result = _cem_search_joint(
        cell=cell,
        arm=arm,
        budget=budget,
        seed=seed,
        chrono=False,
        evaluate_population=evaluator,
    )
    points = simulate_planar_trajectory(cell, result["best_segments_physical"], budget.horizon_s)
    result["refined"] = refine_distance_for_trajectory(points, cell, arm)
    result["best_trajectory"] = [asdict(point) for point in points]
    return result


def _chrono_scenario(cell: BoundaryCell, budget: BoundaryBudget, seed: int) -> dict[str, Any]:
    import phase4_f2_train as f2

    steps = int(round(budget.horizon_s / DT))
    scenario = f2._avoidance_scenario(seed, max_steps=steps, reveal=30.0, mu=float(cell.mu))
    scenario["scenario_id"] = f"{MILESTONE_ID}-{cell.cell_id}-{seed}"
    scenario["obstacle"] = {"enabled": False}
    scenario["track_width"] = 100.0
    scenario["speed_ref"] = float(cell.speed_mps)
    scenario["initial_state"]["vx"] = float(cell.speed_mps)
    scenario["initial_state"]["vy"] = 0.0
    scenario["initial_state"]["yaw_rate"] = 0.0
    return scenario


def _chrono_trajectory(
    step_rows: list[tuple[np.ndarray, bool, bool, str, dict]],
    scenario: dict[str, Any],
) -> list[TrajectoryPoint]:
    initial = scenario["initial_state"]
    x0 = float(initial["x"])
    y0 = float(initial["y"])
    psi0 = float(initial["psi"])
    cos0 = math.cos(psi0)
    sin0 = math.sin(psi0)
    vx0 = float(initial.get("vx", 0.0))
    vy0 = float(initial.get("vy", 0.0))
    points = [
        TrajectoryPoint(
            0.0,
            0.0,
            0.0,
            math.hypot(vx0, vy0),
            abs(math.atan2(vy0, max(abs(vx0), 1e-9))),
            0.0,
        )
    ]
    for _, _, _, _, info in step_rows:
        vx = float(info.get("vx_body", 0.0))
        vy = float(info.get("vy_body", 0.0))
        beta = abs(math.atan2(vy, max(abs(vx), 1e-9)))
        rear_slip, _, _ = g0b._rear_front_tire_slip(info)
        dx = float(info.get("x", x0)) - x0
        dy = float(info.get("y", y0)) - y0
        local_x = cos0 * dx + sin0 * dy
        local_y = -sin0 * dx + cos0 * dy
        local_psi = math.atan2(
            math.sin(float(info.get("psi", psi0)) - psi0),
            math.cos(float(info.get("psi", psi0)) - psi0),
        )
        points.append(
            TrajectoryPoint(
                local_x,
                local_y,
                local_psi,
                math.hypot(vx, vy),
                beta,
                0.0 if not math.isfinite(rear_slip) else rear_slip,
            )
        )
    return points


def _evaluate_chrono_population(
    clients: list[Any],
    scenario: dict[str, Any],
    cell: BoundaryCell,
    arm: str,
    budget: BoundaryBudget,
    population: np.ndarray,
    distances: np.ndarray,
    tag: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any] | None] = [None] * len(population)
    counter = {"index": 0}
    lock = threading.Lock()
    steps = int(round(budget.horizon_s / DT))

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
                episode_id=f"{scenario['scenario_id']}-{arm}-{tag}-{index}",
                seed=_seed_for("chrono", cell.cell_id, arm, tag, index),
            )
            step_rows, _ = client.step_many(actions)
            points = _chrono_trajectory(step_rows, scenario)
            row = evaluate_trajectory_at_distance(points, cell, arm, float(distances[index]))
            row["finite_rear_tire_steps"] = sum(point.rear_slip > 0.0 for point in points)
            results[index] = row

    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = [executor.submit(worker, index) for index in range(len(clients))]
        for future in futures:
            future.result()
    assert all(result is not None for result in results)
    return [dict(result) for result in results if result is not None]


def search_chrono(
    clients: list[Any], cell: BoundaryCell, arm: str, budget: BoundaryBudget, seed: int
) -> dict[str, Any]:
    scenario = _chrono_scenario(cell, budget, seed)
    iteration = {"value": 0}

    def evaluator(population: np.ndarray, distances: np.ndarray) -> list[dict[str, Any]]:
        tag = f"seed{seed}-iter{iteration['value']}"
        iteration["value"] += 1
        return _evaluate_chrono_population(clients, scenario, cell, arm, budget, population, distances, tag)

    result = _cem_search_joint(
        cell=cell,
        arm=arm,
        budget=budget,
        seed=seed,
        chrono=True,
        evaluate_population=evaluator,
    )
    steps = int(round(budget.horizon_s / DT))
    physical = g0._expand_segments(result["best_segments_physical"], steps)
    actions = np.asarray(
        [g0.physical_command_to_model_action(*command) for command in physical], dtype=np.float64
    )
    client = clients[0]
    client.reset(scenario, episode_id=f"{scenario['scenario_id']}-{arm}-refine", seed=seed)
    step_rows, _ = client.step_many(actions)
    points = _chrono_trajectory(step_rows, scenario)
    result["refined"] = refine_distance_for_trajectory(points, cell, arm)
    result["best_trajectory"] = [asdict(point) for point in points]
    client.reset(scenario, episode_id=f"{scenario['scenario_id']}-{arm}-replay", seed=seed)
    replay_rows, _ = client.step_many(actions)
    replay_points = _chrono_trajectory(replay_rows, scenario)
    lhs = np.asarray([[point.x, point.y, point.psi, point.speed, point.beta, point.rear_slip] for point in points])
    rhs = np.asarray(
        [[point.x, point.y, point.psi, point.speed, point.beta, point.rear_slip] for point in replay_points]
    )
    same_shape = lhs.shape == rhs.shape
    max_replay_error = float(np.max(np.abs(lhs - rhs))) if same_shape and lhs.size else float("inf")
    result["replay"] = {
        "same_shape": same_shape,
        "max_abs_error": max_replay_error,
        "exact_pass": bool(same_shape and max_replay_error <= 1e-12),
    }
    return result


def _arm_summary(searches: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [item for item in searches if item["refined"]["d_star_m"] is not None]
    if not successful:
        return {
            "d_star_m": None,
            "successful_search_seeds": 0,
            "seed_d_stars_m": [item["refined"]["d_star_m"] for item in searches],
            "best_seed": None,
            "best_boundary": None,
        }
    best = min(successful, key=lambda item: float(item["refined"]["d_star_m"]))
    return {
        "d_star_m": float(best["refined"]["d_star_m"]),
        "successful_search_seeds": len(successful),
        "seed_d_stars_m": [item["refined"]["d_star_m"] for item in searches],
        "best_seed": int(best["seed"]),
        "best_boundary": best["refined"]["boundary"],
        "best_segments_physical": best["best_segments_physical"],
    }


def _cell_verdict(cell: BoundaryCell, by_arm: dict[str, dict[str, Any]]) -> dict[str, Any]:
    grip = by_arm["grip"]["d_star_m"]
    slide = by_arm["required_slide"]["d_star_m"]
    free = by_arm["free"]["d_star_m"]
    complete = grip is not None and slide is not None and free is not None
    drift_advantage = None if not complete else float(grip - slide)
    free_consistency = bool(
        complete and float(free) <= min(float(grip), float(slide)) + DISTANCE_TOLERANCE_M
    )
    no_drift_advantage = bool(
        complete and float(grip) <= float(slide) + DISTANCE_TOLERANCE_M
    )
    free_boundary = by_arm["free"].get("best_boundary") or {}
    free_uses_early_slide = free_boundary.get("free_mode_classification") == "controlled_slide_like"
    free_counterexample = bool(
        complete
        and free_uses_early_slide
        and float(free) + DISTANCE_TOLERANCE_M < float(grip)
    )
    return {
        "cell_id": cell.cell_id,
        "grip_d_star_m": grip,
        "required_slide_d_star_m": slide,
        "free_d_star_m": free,
        "drift_advantage_m": drift_advantage,
        "all_arms_complete": complete,
        "free_consistency_pass": free_consistency,
        "no_drift_advantage_pass": no_drift_advantage,
        "free_mode_classification": free_boundary.get("free_mode_classification"),
        "free_counterexample": free_counterexample,
    }


def run_backend(
    *,
    backend: str,
    cells: tuple[BoundaryCell, ...],
    budget: BoundaryBudget,
    progress_path: Path,
) -> dict[str, Any]:
    searches: list[dict[str, Any]] = []
    arm_rows: list[dict[str, Any]] = []
    clients: list[Any] = []
    try:
        if backend == "chrono":
            from chrono_worker_client import ChronoWorkerClient

            worker_count = 2 if budget.population <= 6 else 8
            clients = [ChronoWorkerClient(stderr_log=None) for _ in range(worker_count)]
        for cell in cells:
            by_arm_searches: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
            for arm in ARMS:
                for search_index in range(budget.search_seeds):
                    seed = _seed_for(backend, cell.cell_id, arm, search_index)
                    if backend == "planar":
                        result = search_planar(cell, arm, budget, seed)
                    else:
                        result = search_chrono(clients, cell, arm, budget, seed)
                    result["backend"] = backend
                    searches.append(result)
                    by_arm_searches[arm].append(result)
                    _append_progress(
                        progress_path,
                        {
                            "stage": "search_done",
                            "backend": backend,
                            "cell_id": cell.cell_id,
                            "arm": arm,
                            "search_index": search_index,
                            "d_star_m": result["refined"]["d_star_m"],
                        },
                    )
            by_arm = {arm: _arm_summary(by_arm_searches[arm]) for arm in ARMS}
            verdict = _cell_verdict(cell, by_arm)
            for arm in ARMS:
                arm_rows.append(
                    {
                        "backend": backend,
                        "cell_id": cell.cell_id,
                        "mu": cell.mu,
                        "speed_mps": cell.speed_mps,
                        "arm": arm,
                        **{key: value for key, value in by_arm[arm].items() if key != "best_segments_physical"},
                    }
                )
            _append_progress(progress_path, {"stage": "cell_done", "backend": backend, **verdict})
        cell_verdicts: list[dict[str, Any]] = []
        for cell in cells:
            relevant = [row for row in arm_rows if row["cell_id"] == cell.cell_id]
            by_arm = {
                arm: next(row for row in relevant if row["arm"] == arm)
                for arm in ARMS
            }
            cell_verdicts.append(_cell_verdict(cell, by_arm))
        return {
            "backend": backend,
            "budget": asdict(budget),
            "cells": [asdict(cell) for cell in cells],
            "searches": searches,
            "arm_rows": arm_rows,
            "cell_verdicts": cell_verdicts,
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
        "registered_at_utc": INITIAL_REGISTERED_AT_UTC,
        "protocol_revision": PROTOCOL_REVISION,
        "protocol_revision_history": [
            {
                "revision": "r0",
                "quick_artifact": (
                    "experiments/feasibility_audit/"
                    "phase5_g1_preslip_reachable_set_adjudication_quick_invalid_v0.json"
                ),
                "outcome": (
                    "invalid smoke: Chrono world coordinates were evaluated as lane-local coordinates; "
                    "post-terminal samples also entered slide classification"
                ),
            },
            {
                "revision": PROTOCOL_REVISION,
                "amended_at_utc": PROTOCOL_AMENDED_AT_UTC,
                "changes": [
                    "transform Chrono world poses into the scenario-initial lane frame",
                    "truncate mode classification at first collision, off-road, or pass event",
                    "add deterministic early-steer/recenter grip candidates and exact Chrono replay gate",
                ],
                "unchanged": [
                    "claim and 0.25 m threshold",
                    "cells, arm definitions, dynamics, geometry, and budgets",
                    "SHA256-derived quick/full and arm seed streams",
                ],
            },
        ],
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "parent_pricing": [
            "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json",
            "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json",
        ],
        "primary_claim": (
            "Within the frozen lane-aligned static-OBB domain, the minimum clearable distance of the matched grip arm "
            "is no larger than that of the required controlled-slide arm, up to 0.25 m search/refinement tolerance."
        ),
        "metric": {
            "d_star": "minimum obstacle-center distance cleared by a mode-valid trajectory; smaller is better",
            "drift_advantage_m": "grip_d_star - required_slide_d_star; positive favors slide",
            "tolerance_m": DISTANCE_TOLERANCE_M,
            "refinement_step_m": DISTANCE_REFINE_STEP_M,
        },
        "arms": {
            "grip": "beta <=0.12 through pass, speed >=4 m/s, common road/actuator constraints",
            "required_slide": (
                "four consecutive frames with beta in [0.20,0.60], rear slip >=0.15, speed >=4 m/s, onset front "
                "before the OBB near face; beta never exceeds 0.70 through pass"
            ),
            "free": "no mode requirement, but beta <=0.70, speed >=4 m/s, and common road/actuator constraints",
        },
        "geometry": {
            "vehicle_half_length_m": CAR_HALF_LENGTH_M,
            "vehicle_half_width_m": CAR_HALF_WIDTH_M,
            "obstacle_half_width_m": 0.85,
            "obstacle_half_depth_m": 0.65,
            "orientation": "lane-aligned only",
            "contact_rule": "controlled-slide onset vehicle-front projection must not cross obstacle near face",
        },
        "budgets": {
            "quick_planar": asdict(QUICK_PLANAR_BUDGET),
            "full_planar": asdict(FULL_PLANAR_BUDGET),
            "quick_chrono": asdict(QUICK_CHRONO_BUDGET),
            "full_chrono": asdict(FULL_CHRONO_BUDGET),
        },
        "cells": {
            "quick_planar": [asdict(cell) for cell in QUICK_PLANAR_CELLS],
            "full_planar": [asdict(cell) for cell in FULL_PLANAR_CELLS],
            "quick_chrono": [asdict(cell) for cell in QUICK_CHRONO_CELLS],
            "full_chrono": [asdict(cell) for cell in FULL_CHRONO_CELLS],
        },
        "positive_and_health_gates": {
            "literature_positive_control": "M3265 0.20/0.26 rad/s witness remains true",
            "same_plant_slide_entry": "M3266 full protocol_gates_passed remains true",
            "all_arms_complete": "every cell has finite D* for grip, required_slide, and free",
            "free_consistency": "free D* <= min(grip D*, slide D*) +0.25 m in every cell",
            "no_drift_advantage": "grip D* <= slide D* +0.25 m in every cell",
            "free_counterexample": "no early-controlled-slide free solution beats grip by >0.25 m",
            "chrono_local_frame": "every stored Chrono trajectory starts exactly at local (0,0,0)",
            "chrono_exact_replay": "best action sequence replays with <=1e-12 max state/telemetry error",
        },
        "seed_discipline": {
            "seed_base": SEED_BASE,
            "quick_full": "disjoint cell sets and SHA256-derived optimizer streams",
            "arm_streams": "disjoint; budgets identical within backend",
        },
        "decision_rule": {
            "support": "all health gates and all planar plus Chrono no-drift-advantage gates pass",
            "falsify": "any valid required-slide or early-slide free arm beats grip by more than 0.25 m",
            "inconclusive": "any arm-completeness, free-consistency, telemetry, or replay gate fails",
        },
        "claim_boundary": (
            "finite-domain detailed-model adjudication supporting or falsifying the bounded theorem bridge; not a universal vehicle theorem"
        ),
        "out_of_scope": [
            "split-mu",
            "moving obstacles",
            "terminal yaw or pose requirements",
            "rear steering or direct yaw moment enabled only in slide",
            "non-lane-aligned obstacles",
            "real-vehicle validation",
        ],
    }


def run(*, quick: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode_name = "quick" if quick else "full"
    run_dir = RUN_DIR / mode_name
    progress_path = run_dir / "progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()
    planar = run_backend(
        backend="planar",
        cells=QUICK_PLANAR_CELLS if quick else FULL_PLANAR_CELLS,
        budget=QUICK_PLANAR_BUDGET if quick else FULL_PLANAR_BUDGET,
        progress_path=progress_path,
    )
    chrono = run_backend(
        backend="chrono",
        cells=QUICK_CHRONO_CELLS if quick else FULL_CHRONO_CELLS,
        budget=QUICK_CHRONO_BUDGET if quick else FULL_CHRONO_BUDGET,
        progress_path=progress_path,
    )
    literature = json.loads(
        (REPO_ROOT / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json").read_text(
            encoding="utf-8"
        )
    )
    onset = json.loads(
        (REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json").read_text(
            encoding="utf-8"
        )
    )
    all_verdicts = [*planar["cell_verdicts"], *chrono["cell_verdicts"]]
    chrono_searches = list(chrono["searches"])
    local_frame_pass = all(
        search["best_trajectory"]
        and abs(float(search["best_trajectory"][0]["x"])) <= 1e-12
        and abs(float(search["best_trajectory"][0]["y"])) <= 1e-12
        and abs(float(search["best_trajectory"][0]["psi"])) <= 1e-12
        for search in chrono_searches
    )
    gates = {
        "literature_positive_control_pass": bool(literature["positive_control"]["positive_control_pass"]),
        "same_plant_slide_entry_pass": bool(onset["gates"]["protocol_gates_passed"]),
        "all_arms_complete_pass": all(bool(row["all_arms_complete"]) for row in all_verdicts),
        "free_consistency_pass": all(bool(row["free_consistency_pass"]) for row in all_verdicts),
        "no_drift_advantage_pass": all(bool(row["no_drift_advantage_pass"]) for row in all_verdicts),
        "no_free_slide_counterexample_pass": not any(bool(row["free_counterexample"]) for row in all_verdicts),
        "chrono_local_frame_pass": local_frame_pass,
        "chrono_exact_replay_pass": all(bool(search["replay"]["exact_pass"]) for search in chrono_searches),
    }
    health = (
        gates["literature_positive_control_pass"]
        and gates["same_plant_slide_entry_pass"]
        and gates["all_arms_complete_pass"]
        and gates["free_consistency_pass"]
        and gates["chrono_local_frame_pass"]
        and gates["chrono_exact_replay_pass"]
    )
    falsified = health and (
        not gates["no_drift_advantage_pass"] or not gates["no_free_slide_counterexample_pass"]
    )
    supported = health and gates["no_drift_advantage_pass"] and gates["no_free_slide_counterexample_pass"]
    decision = "bounded_empirical_support" if supported else ("counterexample_found" if falsified else "inconclusive")
    drift_advantages = [
        float(row["drift_advantage_m"])
        for row in all_verdicts
        if row["drift_advantage_m"] is not None
    ]
    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode_name,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "lane-aligned static-OBB finite-domain detailed-model result; does not extend the bounded theorem universally"
        ),
        "planar": planar,
        "chrono": chrono,
        "combined_cell_verdicts": all_verdicts,
        "gates": gates,
        "max_drift_advantage_m": max(drift_advantages, default=None),
        "decision": decision,
        "theory_bridge_supported": supported,
        "dominance_claim_admitted": supported,
        "incumbent_changed": False,
        "self_id_claim": False,
    }
    _write_csv(run_dir / "planar_arm_rows.csv", list(planar["arm_rows"]))
    _write_csv(run_dir / "chrono_arm_rows.csv", list(chrono["arm_rows"]))
    _write_csv(run_dir / "cell_verdicts.csv", all_verdicts)
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
            _jsonable(
                {
                    "path": str(output.relative_to(REPO_ROOT)),
                    **summary["gates"],
                    "max_drift_advantage_m": summary["max_drift_advantage_m"],
                    "decision": summary["decision"],
                }
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
