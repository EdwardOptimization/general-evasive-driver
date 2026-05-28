"""No-policy four-wheel fault source-shape smoke."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_separable_source_constructor import (
    classify_capability_separable_result,
    evaluate_action_separability,
)
from autodrift.four_wheel_dynamics import (
    FourWheelDriftModel,
    FourWheelFaultScales,
    FourWheelForces,
    FourWheelState,
    FourWheelVehicleParams,
)
from autodrift.fresh_trajectory_boundary_sampler import _finite_float


@dataclass(frozen=True)
class FourWheelFaultCase:
    name: str
    family: str
    severity: str
    scales: FourWheelFaultScales


@dataclass(frozen=True)
class FourWheelScenario:
    scenario_id: str
    seed: int
    state: FourWheelState
    obstacle_body_x: float
    obstacle_body_y: float
    obstacle_half_width: float
    obstacle_half_length: float = 1.0
    vehicle_half_width: float = 0.9
    vehicle_half_length: float = 2.2
    previous_action: tuple[float, float, float] = (0.0, -1.0, 1.0)


def _body_to_world(state: FourWheelState, body_x: float, body_y: float) -> np.ndarray:
    cos_psi = math.cos(state.psi)
    sin_psi = math.sin(state.psi)
    return np.asarray(
        [
            state.x + cos_psi * float(body_x) - sin_psi * float(body_y),
            state.y + sin_psi * float(body_x) + cos_psi * float(body_y),
        ],
        dtype=np.float64,
    )


def _world_to_body(state: FourWheelState, point: np.ndarray) -> tuple[float, float]:
    dx = float(point[0]) - state.x
    dy = float(point[1]) - state.y
    cos_psi = math.cos(state.psi)
    sin_psi = math.sin(state.psi)
    return (
        cos_psi * dx + sin_psi * dy,
        -sin_psi * dx + cos_psi * dy,
    )


def obstacle_margin(
    state: FourWheelState,
    obstacle_world: np.ndarray,
    *,
    obstacle_half_width: float,
    obstacle_half_length: float,
    vehicle_half_width: float,
    vehicle_half_length: float,
) -> tuple[float, bool, bool, float, float]:
    body_x, body_y = _world_to_body(state, obstacle_world)
    long_gap = abs(float(body_x)) - (float(vehicle_half_length) + float(obstacle_half_length))
    lat_gap = abs(float(body_y)) - (float(vehicle_half_width) + float(obstacle_half_width))
    collision = bool(long_gap <= 0.0 and lat_gap <= 0.0)
    if long_gap <= 0.0:
        margin = lat_gap
    elif lat_gap <= 0.0:
        margin = long_gap
    else:
        margin = math.hypot(long_gap, lat_gap)
    completed = bool(float(body_x) < -(float(vehicle_half_length) + float(obstacle_half_length)))
    return float(margin), collision, completed, float(body_x), float(body_y)


def build_human_view_observation(
    *,
    state: FourWheelState,
    previous_action: tuple[float, float, float],
    obstacle_body_x: float,
    obstacle_body_y: float,
    obstacle_half_width: float,
    ax: float = 0.0,
    ay: float = 0.0,
    steer_rate: float = 0.0,
    track_width: float = 8.0,
) -> np.ndarray:
    obs = np.zeros(72, dtype=np.float32)
    obs[0] = float(state.vx) / 20.0
    obs[1] = float(state.vy) / 12.0
    obs[2] = float(state.yaw_rate) / 2.5
    obs[3] = float(ax) / 12.0
    obs[4] = float(ay) / 12.0
    obs[5] = float(state.steer) / 0.62
    obs[6] = float(steer_rate) / 3.5
    obs[7] = float(np.clip(state.drive_force / 8200.0, -1.0, 1.0))
    obs[8] = float(np.clip(state.brake_force / 6000.0, 0.0, 1.0))
    obs[9:12] = np.asarray(previous_action, dtype=np.float32)

    road_start = 12
    for idx in range(8):
        x = float(idx + 1) * 5.0
        obs[road_start + 2 * idx] = x / 80.0
        obs[road_start + 2 * idx + 1] = (0.5 * track_width) / track_width
        obs[road_start + 16 + 2 * idx] = x / 80.0
        obs[road_start + 16 + 2 * idx + 1] = (-0.5 * track_width) / track_width

    obstacle_start = 44
    obs[obstacle_start] = 1.0
    obs[obstacle_start + 1] = float(obstacle_body_x) / 80.0
    obs[obstacle_start + 2] = float(obstacle_body_y) / track_width
    obs[obstacle_start + 3] = 0.0
    obs[obstacle_start + 4] = 0.0
    obs[obstacle_start + 5] = float(obstacle_half_width) / track_width
    obs[obstacle_start + 6] = 1.0 / 8.0
    return obs


def build_fault_cases() -> list[FourWheelFaultCase]:
    return [
        FourWheelFaultCase(
            name="split_mu_left_low",
            family="left_right_split_mu",
            severity="severe",
            scales=FourWheelFaultScales.split_mu(left_scale=0.25, right_scale=1.0),
        ),
        FourWheelFaultCase(
            name="split_mu_right_low",
            family="left_right_split_mu",
            severity="severe",
            scales=FourWheelFaultScales.split_mu(left_scale=1.0, right_scale=0.25),
        ),
        FourWheelFaultCase(
            name="front_left_brake_pull",
            family="single_wheel_brake_pull",
            severity="severe",
            scales=FourWheelFaultScales.single_wheel_brake_pull("front_left", brake_scale=2.0),
        ),
        FourWheelFaultCase(
            name="front_right_brake_pull",
            family="single_wheel_brake_pull",
            severity="severe",
            scales=FourWheelFaultScales.single_wheel_brake_pull("front_right", brake_scale=2.0),
        ),
        FourWheelFaultCase(
            name="rear_left_grip_collapse",
            family="single_wheel_grip_collapse",
            severity="severe",
            scales=FourWheelFaultScales.single_wheel_grip_collapse(
                "rear_left",
                mu_scale=0.2,
                lateral_stiffness_scale=0.2,
            ),
        ),
        FourWheelFaultCase(
            name="rear_right_grip_collapse",
            family="single_wheel_grip_collapse",
            severity="severe",
            scales=FourWheelFaultScales.single_wheel_grip_collapse(
                "rear_right",
                mu_scale=0.2,
                lateral_stiffness_scale=0.2,
            ),
        ),
        FourWheelFaultCase(
            name="rear_left_halfshaft_loss",
            family="halfshaft_torque_loss",
            severity="severe",
            scales=FourWheelFaultScales.halfshaft_torque_loss("rear_left", drive_scale=0.1),
        ),
        FourWheelFaultCase(
            name="rear_right_halfshaft_loss",
            family="halfshaft_torque_loss",
            severity="severe",
            scales=FourWheelFaultScales.halfshaft_torque_loss("rear_right", drive_scale=0.1),
        ),
    ]


def build_fault_pairs(faults: list[FourWheelFaultCase]) -> list[tuple[FourWheelFaultCase, FourWheelFaultCase]]:
    by_name = {fault.name: fault for fault in faults}
    return [
        (by_name["split_mu_left_low"], by_name["split_mu_right_low"]),
        (by_name["front_left_brake_pull"], by_name["front_right_brake_pull"]),
        (by_name["rear_left_grip_collapse"], by_name["rear_right_grip_collapse"]),
        (by_name["rear_left_halfshaft_loss"], by_name["rear_right_halfshaft_loss"]),
    ]


def build_scenarios() -> list[FourWheelScenario]:
    scenarios: list[FourWheelScenario] = []
    index = 0
    for speed in (16.0, 18.0, 20.0):
        for obstacle_x in (8.0, 10.0, 12.0):
            for obstacle_y in (-0.35, 0.0, 0.35):
                state = FourWheelState(
                    x=0.0,
                    y=0.0,
                    psi=0.0,
                    vx=float(speed),
                    vy=0.0,
                    yaw_rate=0.0,
                    steer=0.0,
                    drive_force=0.0,
                    brake_force=6000.0,
                )
                scenarios.append(
                    FourWheelScenario(
                        scenario_id=f"fw_seed{126800 + index}",
                        seed=126800 + index,
                        state=state,
                        obstacle_body_x=float(obstacle_x),
                        obstacle_body_y=float(obstacle_y),
                        obstacle_half_width=0.85,
                        previous_action=(0.0, -1.0, 1.0),
                    )
                )
                index += 1
    return scenarios


def build_action_lattice(*, sequence_length: int) -> list[dict[str, Any]]:
    base_actions = [
        ("hard_brake", (0.0, -1.0, 1.0)),
        ("left_steer_brake", (0.75, -1.0, 1.0)),
        ("right_steer_brake", (-0.75, -1.0, 1.0)),
        ("strong_left_steer_brake", (1.0, -1.0, 1.0)),
        ("strong_right_steer_brake", (-1.0, -1.0, 1.0)),
        ("left_steer_release", (0.75, -1.0, -1.0)),
        ("right_steer_release", (-0.75, -1.0, -1.0)),
        ("left_steer_half_brake", (0.75, -1.0, 0.0)),
        ("right_steer_half_brake", (-0.75, -1.0, 0.0)),
        ("counter_left", (0.75, -1.0, 1.0), (-0.45, -1.0, 0.3)),
        ("counter_right", (-0.75, -1.0, 1.0), (0.45, -1.0, 0.3)),
    ]
    candidates: list[dict[str, Any]] = []
    for candidate_id, item in enumerate(base_actions):
        name = item[0]
        first = np.asarray(item[1], dtype=np.float32)
        if len(item) == 2:
            sequence = np.tile(first.reshape(1, 3), (int(sequence_length), 1)).astype(np.float32)
        else:
            second = np.asarray(item[2], dtype=np.float32)
            split = max(1, int(sequence_length) // 2)
            sequence = np.vstack(
                [
                    np.tile(first.reshape(1, 3), (split, 1)),
                    np.tile(second.reshape(1, 3), (int(sequence_length) - split, 1)),
                ]
            ).astype(np.float32)
        flat = sequence.reshape(-1)
        candidates.append(
            {
                "candidate_id": candidate_id,
                "template": name,
                "sequence": sequence,
                "candidate_vector": flat,
                "candidate_steer": float(sequence[0, 0]),
                "candidate_throttle": float(sequence[0, 1]),
                "candidate_brake": float(sequence[0, 2]),
                "last_steer": float(sequence[-1, 0]),
                "last_throttle": float(sequence[-1, 1]),
                "last_brake": float(sequence[-1, 2]),
                "sequence_length": int(sequence.shape[0]),
                "action_l2_from_shared_base": float(np.linalg.norm(flat) / math.sqrt(int(sequence.shape[0]))),
            }
        )
    return candidates


def rollout_sequence(
    *,
    scenario: FourWheelScenario,
    fault: FourWheelFaultCase,
    sequence: np.ndarray,
    dt: float,
    params: FourWheelVehicleParams,
) -> dict[str, Any]:
    model = FourWheelDriftModel(params=params, fault_scales=fault.scales)
    state = FourWheelState.from_array(scenario.state.as_array().copy())
    obstacle_world = _body_to_world(state, scenario.obstacle_body_x, scenario.obstacle_body_y)
    min_margin = float("inf")
    collision = False
    completed = False
    final_body_x = float("nan")
    final_body_y = float("nan")
    yaw_moment_peak = 0.0
    total_return = 0.0
    last_forces: FourWheelForces | None = None
    for action in np.asarray(sequence, dtype=np.float32):
        state, forces = model.step(state, action, dt)
        last_forces = forces
        yaw_moment_peak = max(yaw_moment_peak, abs(float(forces.yaw_moment)))
        margin, step_collision, step_completed, body_x, body_y = obstacle_margin(
            state,
            obstacle_world,
            obstacle_half_width=scenario.obstacle_half_width,
            obstacle_half_length=scenario.obstacle_half_length,
            vehicle_half_width=scenario.vehicle_half_width,
            vehicle_half_length=scenario.vehicle_half_length,
        )
        min_margin = min(min_margin, margin)
        total_return += margin
        collision = collision or step_collision
        completed = completed or step_completed
        final_body_x = float(body_x)
        final_body_y = float(body_y)
        if collision:
            break
        if completed:
            break
    safe_stop = bool(
        (not collision)
        and (not completed)
        and abs(float(state.vx)) <= 1.0
        and np.isfinite(final_body_x)
        and final_body_x > scenario.vehicle_half_length + scenario.obstacle_half_length
        and np.isfinite(min_margin)
        and min_margin >= 0.0
    )
    if collision:
        terminal_reason = "collision"
    elif completed:
        terminal_reason = "obstacle_completed"
    elif safe_stop:
        terminal_reason = "safe_stop"
    else:
        terminal_reason = "horizon"
    success = bool((not collision) and (completed or safe_stop))
    return {
        "success": success,
        "collision": bool(collision),
        "safe_stop": safe_stop,
        "terminal_reason": terminal_reason,
        "obstacle_completed": bool(completed),
        "min_clearance_margin": float(min_margin),
        "return": float(total_return),
        "steps": int(sequence.shape[0]),
        "yaw_moment_abs_peak": float(yaw_moment_peak),
        "final_x": float(state.x),
        "final_y": float(state.y),
        "final_psi": float(state.psi),
        "final_vx": float(state.vx),
        "final_vy": float(state.vy),
        "final_yaw_rate": float(state.yaw_rate),
        "final_obstacle_body_x": final_body_x,
        "final_obstacle_body_y": final_body_y,
        "last_yaw_moment": float(last_forces.yaw_moment) if last_forces is not None else float("nan"),
    }


def evaluate_source_pair(
    *,
    pair_id: int,
    scenario: FourWheelScenario,
    condition_a: FourWheelFaultCase,
    condition_b: FourWheelFaultCase,
    candidates: list[dict[str, Any]],
    dt: float,
    params: FourWheelVehicleParams,
    min_best_action_l2: float,
    min_cross_regret_margin: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rollout_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        sequence = np.asarray(candidate["sequence"], dtype=np.float32)
        for condition, fault in (("A", condition_a), ("B", condition_b)):
            result = rollout_sequence(scenario=scenario, fault=fault, sequence=sequence, dt=dt, params=params)
            rollout_rows.append(
                {
                    "pair_id": int(pair_id),
                    "scenario_id": scenario.scenario_id,
                    "seed": int(scenario.seed),
                    "candidate_id": int(candidate["candidate_id"]),
                    "candidate_mode": "open_loop_sequence",
                    "condition": condition,
                    "fault_name": fault.name,
                    "fault_family": fault.family,
                    "fault_severity": fault.severity,
                    "sequence_length": int(candidate["sequence_length"]),
                    "template": str(candidate["template"]),
                    "candidate_steer": float(candidate["candidate_steer"]),
                    "candidate_throttle": float(candidate["candidate_throttle"]),
                    "candidate_brake": float(candidate["candidate_brake"]),
                    "last_steer": float(candidate["last_steer"]),
                    "last_throttle": float(candidate["last_throttle"]),
                    "last_brake": float(candidate["last_brake"]),
                    "candidate_vector": candidate["candidate_vector"].tolist(),
                    "action_l2_from_shared_base": float(candidate["action_l2_from_shared_base"]),
                    **result,
                }
            )
    decision = evaluate_action_separability(
        pair_id=pair_id,
        candidate_rows=rollout_rows,
        min_best_action_l2=min_best_action_l2,
        min_cross_regret_margin=min_cross_regret_margin,
    )
    pair_row = {
        "pair_id": int(pair_id),
        "scenario_id": scenario.scenario_id,
        "seed": int(scenario.seed),
        "condition_A_fault": condition_a.name,
        "condition_A_fault_family": condition_a.family,
        "condition_A_fault_severity": condition_a.severity,
        "condition_B_fault": condition_b.name,
        "condition_B_fault_family": condition_b.family,
        "condition_B_fault_severity": condition_b.severity,
        "fault_family_pair": f"{condition_a.family}->{condition_b.family}",
        "severity_pair": f"{condition_a.severity}->{condition_b.severity}",
        "obstacle_body_x": float(scenario.obstacle_body_x),
        "obstacle_body_y": float(scenario.obstacle_body_y),
        "obstacle_half_width": float(scenario.obstacle_half_width),
        **decision,
    }
    return pair_row, rollout_rows


def _scenario_row(scenario: FourWheelScenario) -> dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "seed": int(scenario.seed),
        "vx": float(scenario.state.vx),
        "vy": float(scenario.state.vy),
        "yaw_rate": float(scenario.state.yaw_rate),
        "brake_force": float(scenario.state.brake_force),
        "drive_force": float(scenario.state.drive_force),
        "obstacle_body_x": float(scenario.obstacle_body_x),
        "obstacle_body_y": float(scenario.obstacle_body_y),
        "obstacle_half_width": float(scenario.obstacle_half_width),
    }


def _snapshot_rows(scenarios: list[FourWheelScenario], faults: list[FourWheelFaultCase]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    snapshot_id = 0
    for scenario in scenarios:
        for fault in faults:
            obs = build_human_view_observation(
                state=scenario.state,
                previous_action=scenario.previous_action,
                obstacle_body_x=scenario.obstacle_body_x,
                obstacle_body_y=scenario.obstacle_body_y,
                obstacle_half_width=scenario.obstacle_half_width,
            )
            rows.append(
                {
                    "snapshot_id": int(snapshot_id),
                    "scenario_id": scenario.scenario_id,
                    "seed": int(scenario.seed),
                    "fault_name": fault.name,
                    "fault_family": fault.family,
                    "fault_severity": fault.severity,
                    "step": 0,
                    "observation_dim": int(obs.shape[0]),
                    "observation_sum": float(np.sum(obs)),
                    "obstacle_body_x": float(scenario.obstacle_body_x),
                    "obstacle_body_y": float(scenario.obstacle_body_y),
                    "obstacle_half_width": float(scenario.obstacle_half_width),
                    "vx": float(scenario.state.vx),
                    "vy": float(scenario.state.vy),
                    "yaw_rate": float(scenario.state.yaw_rate),
                    "brake_force": float(scenario.state.brake_force),
                    "drive_force": float(scenario.state.drive_force),
                }
            )
            snapshot_id += 1
    return rows


def _write_model_fidelity_limits(run_dir: Path) -> Path:
    output = run_dir / "model_fidelity_limits.md"
    output.write_text(
        "\n".join(
            [
                "# M1268 Model Fidelity Limits",
                "",
                "M1268 uses the compact in-repo four-wheel source model.",
                "",
                "Allowed claim: source-shape smoke over finite left-right/per-wheel force asymmetry.",
                "",
                "Blocked claims:",
                "",
                "- high-fidelity vehicle dynamics validation",
                "- real split-mu, blowout, stuck-caliper, or halfshaft validation",
                "- actor self-identification evidence",
                "- policy performance improvement",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return output


def run_four_wheel_source_shape_smoke(
    *,
    run_dir: Path,
    sequence_length: int = 72,
    dt: float = 0.02,
    min_best_action_l2: float = 0.12,
    min_cross_regret_margin: float = 0.02,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    params = FourWheelVehicleParams()
    faults = build_fault_cases()
    fault_pairs = build_fault_pairs(faults)
    scenarios = build_scenarios()
    candidates = build_action_lattice(sequence_length=sequence_length)

    lattice_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        lattice_rows.append(
            {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in candidate.items()
                if key != "sequence"
            }
        )

    pair_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    pair_id = 0
    for scenario in scenarios:
        for fault_a, fault_b in fault_pairs:
            pair_row, rows = evaluate_source_pair(
                pair_id=pair_id,
                scenario=scenario,
                condition_a=fault_a,
                condition_b=fault_b,
                candidates=candidates,
                dt=dt,
                params=params,
                min_best_action_l2=min_best_action_l2,
                min_cross_regret_margin=min_cross_regret_margin,
            )
            pair_rows.append(pair_row)
            rollout_rows.extend(rows)
            if bool(pair_row.get("accepted", False)):
                accepted_rows.append(pair_row)
            else:
                rejected_rows.append(pair_row)
            pair_id += 1

    all_four_collision_count = 0
    own_branch_viability_fail_count = 0
    best_actions_diverged_pairs = 0
    low_regret_pairs = 0
    for row in pair_rows:
        if _finite_float(row.get("best_action_l2"), default=0.0) >= min_best_action_l2:
            best_actions_diverged_pairs += 1
        min_regret = min(_finite_float(row.get("cross_regret_A")), _finite_float(row.get("cross_regret_B")))
        if np.isfinite(min_regret) and min_regret < min_cross_regret_margin:
            low_regret_pairs += 1
        if not (bool(row.get("best_A_success", False)) and bool(row.get("best_B_success", False))):
            own_branch_viability_fail_count += 1
        rows_for_pair = [rollout for rollout in rollout_rows if int(rollout["pair_id"]) == int(row["pair_id"])]
        best_ids = {int(row.get("best_candidate_A", -1)), int(row.get("best_candidate_B", -1))}
        cross_rows = [rollout for rollout in rows_for_pair if int(rollout["candidate_id"]) in best_ids]
        if cross_rows and all(bool(rollout.get("collision", False)) for rollout in cross_rows):
            all_four_collision_count += 1

    result_class = classify_capability_separable_result(
        matched_pair_count=len(pair_rows),
        action_rollouts=len(rollout_rows),
        accepted_separable_pairs=len(accepted_rows),
        best_actions_diverged_pairs=best_actions_diverged_pairs,
        low_regret_pairs=low_regret_pairs,
    )
    fidelity_path = _write_model_fidelity_limits(run_dir)

    write_csv_rows(run_dir / "scenario_summary.csv", [_scenario_row(scenario) for scenario in scenarios])
    write_csv_rows(run_dir / "snapshot_candidates.csv", _snapshot_rows(scenarios, faults))
    write_csv_rows(run_dir / "action_lattice.csv", lattice_rows)
    write_csv_rows(run_dir / "action_rollouts.csv", rollout_rows)
    write_csv_rows(run_dir / "matched_capability_pairs.csv", pair_rows)
    write_csv_rows(run_dir / "accepted_separable_pairs.csv", accepted_rows)
    write_csv_rows(run_dir / "rejected_pairs.csv", rejected_rows)

    unique_fault_family_pairs = {str(row.get("fault_family_pair", "")) for row in pair_rows}
    accepted_fault_family_pairs = {str(row.get("fault_family_pair", "")) for row in accepted_rows}
    summary = {
        "run_type": "four_wheel_fault_source_shape_smoke",
        "sequence_length": int(sequence_length),
        "dt": float(dt),
        "min_best_action_l2": float(min_best_action_l2),
        "min_cross_regret_margin": float(min_cross_regret_margin),
        "scenario_count": int(len(scenarios)),
        "fault_count": int(len(faults)),
        "fault_pair_count": int(len(fault_pairs)),
        "matched_pair_count": int(len(pair_rows)),
        "action_lattice_rows": int(len(lattice_rows)),
        "action_rollouts": int(len(rollout_rows)),
        "accepted_separable_pairs": int(len(accepted_rows)),
        "rejected_pairs": int(len(rejected_rows)),
        "best_actions_diverged_pairs": int(best_actions_diverged_pairs),
        "low_regret_pairs": int(low_regret_pairs),
        "own_branch_viability_fail_count": int(own_branch_viability_fail_count),
        "all_four_rollouts_collision_count": int(all_four_collision_count),
        "unique_fault_family_pairs": int(len(unique_fault_family_pairs)),
        "accepted_fault_family_pairs": int(len(accepted_fault_family_pairs)),
        "labels_enter_actor_input": False,
        "training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "accepted_thresholds_relaxed": False,
        "high_fidelity_validation_claimed": False,
        "result_class": result_class,
        "source_positive": bool(result_class == "capability_separable_signal"),
        "m1259_accepted_separable_pairs": 0,
        "m1262_accepted_separable_pairs": 0,
        "m1262_max_min_cross_regret": 0.0043813964,
        "scenario_summary_csv": run_dir / "scenario_summary.csv",
        "snapshot_candidates_csv": run_dir / "snapshot_candidates.csv",
        "action_lattice_csv": run_dir / "action_lattice.csv",
        "action_rollouts_csv": run_dir / "action_rollouts.csv",
        "matched_capability_pairs_csv": run_dir / "matched_capability_pairs.csv",
        "accepted_separable_pairs_csv": run_dir / "accepted_separable_pairs.csv",
        "rejected_pairs_csv": run_dir / "rejected_pairs.csv",
        "model_fidelity_limits_md": fidelity_path,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-policy four-wheel fault source-shape smoke.")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--sequence-length", type=int, default=72)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--min-best-action-l2", type=float, default=0.12)
    parser.add_argument("--min-cross-regret-margin", type=float, default=0.02)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="four_wheel_fault_source_shape")
    summary = run_four_wheel_source_shape_smoke(
        run_dir=run_dir,
        sequence_length=args.sequence_length,
        dt=args.dt,
        min_best_action_l2=args.min_best_action_l2,
        min_cross_regret_margin=args.min_cross_regret_margin,
    )
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
