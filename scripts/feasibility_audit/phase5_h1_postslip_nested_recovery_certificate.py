#!/usr/bin/env python3
"""Test strict post-slip recovery expansion under nested finite control sets."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import threading
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase5_g0_preslip_reachability_proof_pricing as g0
import phase5_g0b_slide_mode_onset_pricing as g0b
import phase5_g1_preslip_reachable_set_adjudication as g1


MILESTONE_ID = "m3271-phase5-h1-postslip-nested-recovery-certificate"
SEED_BASE = 32710019
DT = 0.02
HORIZON_STEPS = 130
RECOVERY_BETA_MAX_RAD = 0.12
RECOVERY_YAW_MAX_RAD_S = 0.60
RECOVERY_STABLE_STEPS = 10
RECOVERY_MIN_VX_MPS = 4.0
SPIN_BETA_RAD = 1.40
INITIAL_SLIDE_BETA_MIN_RAD = 0.20
INITIAL_REAR_SLIP_MIN_RAD = 0.15
MIN_FULL_ROBUST_STRICT_CELLS = 6

SOURCE_ENTRY_PATH = (
    REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
)
PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate_quick.json"
)
FULL_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate"


@dataclass(frozen=True)
class RecoveryCell:
    cell_id: str
    mu: float
    speed_mps: float
    beta_abs_rad: float
    yaw_abs_rad_s: float
    side: int


@dataclass(frozen=True)
class PolicySpec:
    policy_id: str
    family: str
    yaw_gain: float
    beta_gain: float
    throttle: float
    brake: float
    in_baseline_set: bool


def _cell(beta: float, yaw: float, side: int) -> RecoveryCell:
    side_tag = "pos" if side > 0 else "neg"
    beta_tag = str(beta).replace(".", "p")
    yaw_tag = str(yaw).replace(".", "p")
    return RecoveryCell(
        f"h1_mu0p50_b{beta_tag}_r{yaw_tag}_{side_tag}",
        0.50,
        14.0,
        beta,
        yaw,
        side,
    )


QUICK_CELLS = (_cell(0.8, 3.5, 1), _cell(0.8, 3.5, -1))
FULL_CELLS = tuple(
    _cell(beta, yaw, side)
    for beta in (0.6, 0.8, 1.0)
    for yaw in (3.0, 3.5, 4.0)
    for side in (1, -1)
)
QUICK_SEEDS_PER_CELL = 1
FULL_SEEDS_PER_CELL = 3


BASELINE_PEDALS = (
    ("coast", 0.0, 0.0),
    ("brake0p25", 0.0, 0.25),
    ("brake0p50", 0.0, 0.50),
    ("brake0p75", 0.0, 0.75),
    ("brake1p00", 0.0, 1.00),
    ("throttle0p25", 0.25, 0.0),
)
STEERING_PEDALS = (
    ("coast", 0.0, 0.0),
    ("brake0p20", 0.0, 0.20),
    ("brake0p50", 0.0, 0.50),
    ("throttle0p20", 0.20, 0.0),
)
STEERING_GAINS = (
    (0.08, 0.30),
    (0.15, 0.60),
    (0.25, 1.00),
    (0.40, 1.50),
    (0.80, 2.50),
    (1.40, 3.50),
)


def policy_library() -> list[PolicySpec]:
    rows = [
        PolicySpec(f"pedal_{name}", "pedal_only", 0.0, 0.0, throttle, brake, True)
        for name, throttle, brake in BASELINE_PEDALS
    ]
    for yaw_gain, beta_gain in STEERING_GAINS:
        gain_tag = f"kg{yaw_gain:.2f}_kb{beta_gain:.2f}".replace(".", "p")
        for pedal_name, throttle, brake in STEERING_PEDALS:
            rows.append(
                PolicySpec(
                    f"steer_{gain_tag}_{pedal_name}",
                    "countersteer_feedback",
                    yaw_gain,
                    beta_gain,
                    throttle,
                    brake,
                    False,
                )
            )
    return rows


def _jsonable(value: Any) -> Any:
    return g1._jsonable(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    g1._write_json(path, payload)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_for(*parts: Any) -> int:
    material = ":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "little") % 2_000_000_000


def _scenario(cell: RecoveryCell, seed: int) -> dict[str, Any]:
    import phase4_f2_train as f2

    scenario = f2._avoidance_scenario(
        seed,
        max_steps=HORIZON_STEPS,
        reveal=30.0,
        mu=float(cell.mu),
    )
    scenario["scenario_id"] = f"{MILESTONE_ID}-{cell.cell_id}-{seed}"
    scenario["obstacle"] = {"enabled": False}
    scenario["track_width"] = 100.0
    scenario["speed_ref"] = float(cell.speed_mps)
    beta = float(cell.side) * float(cell.beta_abs_rad)
    yaw = float(cell.side) * float(cell.yaw_abs_rad_s)
    scenario["initial_state"]["vx"] = float(cell.speed_mps * math.cos(beta))
    scenario["initial_state"]["vy"] = float(cell.speed_mps * math.sin(beta))
    scenario["initial_state"]["yaw_rate"] = yaw
    return scenario


def _kinematics(obs: np.ndarray, info: dict[str, Any]) -> tuple[float, float, float, float]:
    vx = float(info.get("vx_body", float(obs[0]) * 20.0))
    vy = float(info.get("vy_body", float(obs[1]) * 12.0))
    yaw = float(info.get("yaw_rate", float(obs[2]) * 2.5))
    beta = math.atan2(vy, max(abs(vx), 1e-9))
    return vx, vy, yaw, beta


def _policy_action(spec: PolicySpec, beta: float, yaw_rate: float) -> tuple[np.ndarray, float]:
    steer = 0.0
    if spec.family == "countersteer_feedback":
        steer = float(np.clip(-(spec.yaw_gain * yaw_rate + spec.beta_gain * beta), -1.0, 1.0))
    return g0.physical_command_to_model_action(steer, spec.throttle, spec.brake), steer


def _state_vector(obs: np.ndarray, info: dict[str, Any]) -> np.ndarray:
    vx, vy, yaw, beta = _kinematics(obs, info)
    rear_slip, front_slip, wheel_count = g0b._rear_front_tire_slip(info)
    return np.asarray(
        [
            float(info.get("x", 0.0)),
            float(info.get("y", 0.0)),
            float(info.get("psi", 0.0)),
            vx,
            vy,
            yaw,
            beta,
            rear_slip,
            front_slip,
            float(wheel_count),
        ],
        dtype="<f8",
    )


def _array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(array, dtype="<f8").tobytes()).hexdigest()


def _run_episode(
    client: Any,
    cell: RecoveryCell,
    seed: int,
    spec: PolicySpec,
    *,
    tag: str,
) -> dict[str, Any]:
    scenario = _scenario(cell, seed)
    obs, reset_reply = client.reset(
        scenario,
        episode_id=f"{scenario['scenario_id']}-{spec.policy_id}-{tag}",
        seed=seed,
    )
    reset_info = dict(reset_reply.get("info", {}))
    initial_vector = _state_vector(obs, reset_info)
    initial_vx, initial_vy, initial_yaw, initial_beta = _kinematics(obs, reset_info)
    initial_rear_slip, initial_front_slip, initial_wheel_count = g0b._rear_front_tire_slip(
        reset_info
    )
    trace = [initial_vector]
    stable_run = 0
    recovery_step: int | None = None
    max_abs_beta = abs(initial_beta)
    max_abs_yaw = abs(initial_yaw)
    max_abs_steer = 0.0
    min_vx = initial_vx
    runtime_obs_finite = bool(np.isfinite(obs).all())
    tire_truth_steps = 0
    collision = False
    completion_reason = "horizon"
    final_vx, final_vy, final_yaw, final_beta = initial_vx, initial_vy, initial_yaw, initial_beta
    rollout_steps = 0
    for step in range(1, HORIZON_STEPS + 1):
        action, steer = _policy_action(spec, final_beta, final_yaw)
        obs, terminated, truncated, status, info = client.step(action)
        rollout_steps = step
        runtime_obs_finite = runtime_obs_finite and bool(np.isfinite(obs).all())
        final_vx, final_vy, final_yaw, final_beta = _kinematics(obs, info)
        rear_slip, _front_slip, wheel_count = g0b._rear_front_tire_slip(info)
        if wheel_count >= 4 and math.isfinite(rear_slip):
            tire_truth_steps += 1
        trace.append(_state_vector(obs, info))
        max_abs_beta = max(max_abs_beta, abs(final_beta))
        max_abs_yaw = max(max_abs_yaw, abs(final_yaw))
        max_abs_steer = max(max_abs_steer, abs(steer))
        min_vx = min(min_vx, final_vx)
        collision = collision or bool(info.get("collision", False))
        recovered_now = (
            abs(final_beta) <= RECOVERY_BETA_MAX_RAD
            and abs(final_yaw) <= RECOVERY_YAW_MAX_RAD_S
            and final_vx >= RECOVERY_MIN_VX_MPS
            and not collision
        )
        stable_run = stable_run + 1 if recovered_now else 0
        if stable_run >= RECOVERY_STABLE_STEPS:
            recovery_step = step - RECOVERY_STABLE_STEPS + 1
            completion_reason = "recovered"
            break
        if abs(final_beta) > SPIN_BETA_RAD:
            completion_reason = "spin"
            break
        if abs(final_vx) < 1.5 and abs(final_beta) > 0.25:
            completion_reason = "stopped_sideways"
            break
        if terminated or truncated:
            completion_reason = str(info.get("termination_reason", status or "terminated"))
            break

    trajectory = np.vstack(trace)
    expected_beta = float(cell.side) * float(cell.beta_abs_rad)
    expected_yaw = float(cell.side) * float(cell.yaw_abs_rad_s)
    success = recovery_step is not None
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "beta_abs_rad": cell.beta_abs_rad,
        "yaw_abs_rad_s": cell.yaw_abs_rad_s,
        "side": cell.side,
        "validation_seed": seed,
        "policy_id": spec.policy_id,
        "policy_family": spec.family,
        "in_baseline_set": spec.in_baseline_set,
        "yaw_gain": spec.yaw_gain,
        "beta_gain": spec.beta_gain,
        "physical_throttle": spec.throttle,
        "physical_brake": spec.brake,
        "simultaneous_pedals": bool(spec.throttle > 0.0 and spec.brake > 0.0),
        "initial_state_sha256": _array_sha256(initial_vector),
        "initial_beta_rad": initial_beta,
        "initial_yaw_rate_rad_s": initial_yaw,
        "initial_vx_mps": initial_vx,
        "initial_vy_mps": initial_vy,
        "initial_rear_slip_angle_rad": initial_rear_slip,
        "initial_front_slip_angle_rad": initial_front_slip,
        "initial_tire_wheel_count": initial_wheel_count,
        "initial_state_match": bool(
            abs(initial_beta - expected_beta) <= 0.02
            and abs(initial_yaw - expected_yaw) <= 0.05
        ),
        "initial_slide_truth": bool(
            abs(initial_beta) >= INITIAL_SLIDE_BETA_MIN_RAD
            and math.isfinite(initial_rear_slip)
            and initial_rear_slip >= INITIAL_REAR_SLIP_MIN_RAD
            and initial_wheel_count >= 4
        ),
        "rollout_steps": rollout_steps,
        "tire_truth_steps": tire_truth_steps,
        "tire_truth_complete": tire_truth_steps == rollout_steps,
        "runtime_obs_finite": runtime_obs_finite,
        "success": success,
        "recovery_step": recovery_step,
        "recovery_time_s": None if recovery_step is None else recovery_step * DT,
        "vx_at_recovery_mps": None if not success else final_vx,
        "completion_reason": completion_reason,
        "collision": collision,
        "max_abs_beta_rad": max_abs_beta,
        "max_abs_yaw_rate_rad_s": max_abs_yaw,
        "max_abs_steer": max_abs_steer,
        "min_vx_mps": min_vx,
        "final_beta_rad": final_beta,
        "final_yaw_rate_rad_s": final_yaw,
        "final_vx_mps": final_vx,
        "trajectory_shape": list(trajectory.shape),
        "trajectory_float64_sha256": _array_sha256(trajectory),
    }


def _best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        rows,
        key=lambda row: (
            not bool(row["success"]),
            HORIZON_STEPS + 1 if row["recovery_step"] is None else int(row["recovery_step"]),
            abs(float(row["final_beta_rad"])),
            -float(row["final_vx_mps"]),
            str(row["policy_id"]),
        ),
    )


def seed_verdict(cell: RecoveryCell, seed: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_rows = [row for row in rows if bool(row["in_baseline_set"])]
    baseline_best = _best_row(baseline_rows)
    expanded_best = _best_row(rows)
    baseline_success = any(bool(row["success"]) for row in baseline_rows)
    expanded_success = any(bool(row["success"]) for row in rows)
    strict = bool(
        expanded_success
        and not baseline_success
        and not bool(expanded_best["in_baseline_set"])
        and float(expanded_best["max_abs_steer"]) > 0.05
    )
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "beta_abs_rad": cell.beta_abs_rad,
        "yaw_abs_rad_s": cell.yaw_abs_rad_s,
        "side": cell.side,
        "validation_seed": seed,
        "candidate_count": len(rows),
        "baseline_candidate_count": len(baseline_rows),
        "initial_state_hash_count": len({row["initial_state_sha256"] for row in rows}),
        "initial_state_match": all(bool(row["initial_state_match"]) for row in rows),
        "initial_slide_truth": all(bool(row["initial_slide_truth"]) for row in rows),
        "baseline_recovered": baseline_success,
        "expanded_recovered": expanded_success,
        "weak_inclusion_pass": not baseline_success or expanded_success,
        "strict_expansion_witness": strict,
        "best_baseline_policy_id": baseline_best["policy_id"],
        "best_baseline_completion_reason": baseline_best["completion_reason"],
        "best_baseline_recovery_time_s": baseline_best["recovery_time_s"],
        "best_expanded_policy_id": expanded_best["policy_id"],
        "best_expanded_policy_family": expanded_best["policy_family"],
        "best_expanded_recovery_time_s": expanded_best["recovery_time_s"],
        "best_expanded_vx_at_recovery_mps": expanded_best["vx_at_recovery_mps"],
        "best_expanded_max_abs_steer": expanded_best["max_abs_steer"],
        "no_input_recovered": next(
            bool(row["success"]) for row in rows if row["policy_id"] == "pedal_coast"
        ),
        "uniform_brake_recovered": any(
            bool(row["success"]) and str(row["policy_id"]).startswith("pedal_brake")
            for row in rows
        ),
    }


def cell_verdict(cell: RecoveryCell, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "beta_abs_rad": cell.beta_abs_rad,
        "yaw_abs_rad_s": cell.yaw_abs_rad_s,
        "side": cell.side,
        "seed_count": len(rows),
        "strict_seed_count": sum(bool(row["strict_expansion_witness"]) for row in rows),
        "all_seeds_strict": all(bool(row["strict_expansion_witness"]) for row in rows),
        "all_seeds_initial_slide": all(bool(row["initial_slide_truth"]) for row in rows),
        "all_seeds_weak_inclusion": all(bool(row["weak_inclusion_pass"]) for row in rows),
        "baseline_recovery_seed_count": sum(bool(row["baseline_recovered"]) for row in rows),
        "expanded_recovery_seed_count": sum(bool(row["expanded_recovered"]) for row in rows),
    }


def _run_cell(
    cell: RecoveryCell,
    seeds: list[int],
    policies: list[PolicySpec],
    worker_count: int,
) -> dict[str, Any]:
    from chrono_worker_client import ChronoWorkerClient

    tasks = [(seed, spec) for seed in seeds for spec in policies]
    rows: list[dict[str, Any] | None] = [None] * len(tasks)
    counter = {"value": 0}
    lock = threading.Lock()
    clients: list[Any] = []
    try:
        clients = [ChronoWorkerClient(stderr_log=None) for _ in range(worker_count)]

        def worker(worker_index: int) -> None:
            client = clients[worker_index]
            while True:
                with lock:
                    index = counter["value"]
                    counter["value"] += 1
                if index >= len(tasks):
                    return
                seed, spec = tasks[index]
                rows[index] = _run_episode(client, cell, seed, spec, tag="primary")

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(worker, index) for index in range(worker_count)]
            for future in futures:
                future.result()
    finally:
        for client in clients:
            try:
                client.close()
            except Exception:
                pass
    assert all(row is not None for row in rows)
    candidate_rows = [dict(row) for row in rows if row is not None]
    verdicts = [
        seed_verdict(
            cell,
            seed,
            [row for row in candidate_rows if int(row["validation_seed"]) == seed],
        )
        for seed in seeds
    ]

    first_seed = seeds[0]
    first_rows = [row for row in candidate_rows if int(row["validation_seed"]) == first_seed]
    baseline_best = _best_row([row for row in first_rows if bool(row["in_baseline_set"])])
    expanded_best = _best_row(first_rows)
    policy_by_id = {spec.policy_id: spec for spec in policies}
    replay_rows: list[dict[str, Any]] = []
    replay_client = ChronoWorkerClient(stderr_log=None)
    try:
        for role, original in (("baseline_best", baseline_best), ("expanded_best", expanded_best)):
            replayed = _run_episode(
                replay_client,
                cell,
                first_seed,
                policy_by_id[str(original["policy_id"])],
                tag=f"replay-{role}",
            )
            replay_rows.append(
                {
                    "cell_id": cell.cell_id,
                    "validation_seed": first_seed,
                    "role": role,
                    "policy_id": original["policy_id"],
                    "original_trajectory_sha256": original["trajectory_float64_sha256"],
                    "replay_trajectory_sha256": replayed["trajectory_float64_sha256"],
                    "exact_pass": original["trajectory_float64_sha256"]
                    == replayed["trajectory_float64_sha256"],
                    "original_success": original["success"],
                    "replay_success": replayed["success"],
                }
            )
    finally:
        replay_client.close()
    return {
        "cell": asdict(cell),
        "validation_seeds": seeds,
        "candidate_rows": candidate_rows,
        "seed_verdicts": verdicts,
        "cell_verdict": cell_verdict(cell, verdicts),
        "replay_rows": replay_rows,
    }


def build_preregistration() -> dict[str, Any]:
    policies = policy_library()
    baseline_ids = [spec.policy_id for spec in policies if spec.in_baseline_set]
    expanded_ids = [spec.policy_id for spec in policies]
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "priced_by": {
            "path": str(SOURCE_ENTRY_PATH.relative_to(REPO_ROOT)),
            "sha256": _sha256_file(SOURCE_ENTRY_PATH),
            "measured_basis": (
                "same Chrono/TMeasy plant enters a four-frame slide from beta=0 at 0.50 s, "
                "max beta 0.484 rad, rear slip 0.541 rad, and exact replay"
            ),
        },
        "invalid_predecessor_warning": (
            "scripts/audits/chrono_recovery.py and recovery_reachability.py used normalized "
            "pedal zero as physical zero; normalized zero is 50 percent pedal. Their recovery "
            "counts are not evidence for this milestone."
        ),
        "primary_claim": (
            "For the frozen finite initialized-slide state panel and nested finite control "
            "libraries, adding countersteer feedback strictly expands the recovery set."
        ),
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
        },
        "seeds": {
            "seed_base": SEED_BASE,
            "quick_per_cell": QUICK_SEEDS_PER_CELL,
            "full_per_cell": FULL_SEEDS_PER_CELL,
            "quick_full_disjoint": True,
        },
        "control_sets": {
            "baseline_name": "zero_steer_physical_pedal_library",
            "expanded_name": "baseline_union_countersteer_feedback_library",
            "baseline_policy_ids": baseline_ids,
            "expanded_policy_ids": expanded_ids,
            "baseline_subset_of_expanded": set(baseline_ids).issubset(expanded_ids),
            "policies": [asdict(spec) for spec in policies],
            "pedal_contract": (
                "physical throttle/brake in [0,1] converted to normalized [-1,1]; physical "
                "zero pedal maps to -1, and no candidate uses simultaneous pedals"
            ),
            "esc_claim": False,
        },
        "initial_slide_contract": {
            "body_beta_abs_min_rad": INITIAL_SLIDE_BETA_MIN_RAD,
            "rear_tire_slip_abs_min_rad": INITIAL_REAR_SLIP_MIN_RAD,
            "four_wheel_tire_truth_required": True,
            "configured_reset_match_tolerance": {"beta_rad": 0.02, "yaw_rate_rad_s": 0.05},
        },
        "recovery_contract": {
            "horizon_steps": HORIZON_STEPS,
            "dt_s": DT,
            "beta_abs_max_rad": RECOVERY_BETA_MAX_RAD,
            "yaw_rate_abs_max_rad_s": RECOVERY_YAW_MAX_RAD_S,
            "minimum_forward_speed_mps": RECOVERY_MIN_VX_MPS,
            "stable_steps": RECOVERY_STABLE_STEPS,
            "spin_beta_abs_rad": SPIN_BETA_RAD,
            "collision_allowed": False,
            "stopping_sideways_counts_as_recovery": False,
        },
        "decision_rule": {
            "quick_support": "both mirrored quick cells are strict witnesses on their fresh seed",
            "full_support": (
                "all health and weak-inclusion gates pass; at least 6 of 18 cells are strict "
                "on all 3 seeds; robust strict cells cover both signs and at least 2 beta tiers"
            ),
            "strict_witness": (
                "no baseline policy recovers, an added steering policy recovers, and the winning "
                "policy uses max absolute steer >0.05"
            ),
            "inconclusive": "any state-match, tire-truth, row-count, nesting, or replay gate fails",
        },
        "claim_boundary": (
            "exact finite-state/finite-policy Chrono certificate for selected initialized slide "
            "states; not all no-steer controls, all post-slip states, all vehicles, or real cars"
        ),
        "forbidden": [
            "calling uniform braking ESC",
            "using normalized pedal zero as physical zero",
            "dropping baseline policies from the expanded set",
            "counting a stop-sideways outcome as recovery",
            "changing cells, policies, thresholds, or seeds after quick/full",
            "universalizing the finite-state result",
            "mutating ActiveSafetyReflexDriver or training a policy",
        ],
    }


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode = "quick" if quick else "full"
    cells = QUICK_CELLS if quick else FULL_CELLS
    seeds_per_cell = QUICK_SEEDS_PER_CELL if quick else FULL_SEEDS_PER_CELL
    policies = policy_library()
    run_dir = RUN_DIR / mode
    checkpoint_path = run_dir / "checkpoint.json"
    progress_path = run_dir / "progress.jsonl"
    chunks: list[dict[str, Any]] = []
    if resume and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        chunks = list(checkpoint.get("chunks", []))
    elif progress_path.exists():
        progress_path.unlink()
    completed = {chunk["cell"]["cell_id"] for chunk in chunks}
    for cell in cells:
        if cell.cell_id in completed:
            continue
        seeds = [_seed_for(mode, cell.cell_id, index) for index in range(seeds_per_cell)]
        chunk = _run_cell(cell, seeds, policies, 6 if quick else 8)
        chunks.append(chunk)
        g0._append_progress(progress_path, {"stage": "cell_done", **chunk["cell_verdict"]})
        _write_json(
            checkpoint_path,
            {"milestone_id": MILESTONE_ID, "mode": mode, "chunks": chunks},
        )

    candidate_rows = [row for chunk in chunks for row in chunk["candidate_rows"]]
    seed_verdicts = [row for chunk in chunks for row in chunk["seed_verdicts"]]
    cell_verdicts = [chunk["cell_verdict"] for chunk in chunks]
    replay_rows = [row for chunk in chunks for row in chunk["replay_rows"]]
    baseline_ids = {spec.policy_id for spec in policies if spec.in_baseline_set}
    expanded_ids = {spec.policy_id for spec in policies}
    expected_rows = len(cells) * seeds_per_cell * len(policies)
    robust_strict = [row for row in cell_verdicts if bool(row["all_seeds_strict"])]
    strict_signs = {int(row["side"]) for row in robust_strict}
    strict_beta_tiers = {float(row["beta_abs_rad"]) for row in robust_strict}
    source_entry = json.loads(SOURCE_ENTRY_PATH.read_text(encoding="utf-8"))
    action_contract_pass = (
        np.array_equal(
            g0.physical_command_to_model_action(0.0, 0.0, 0.0),
            np.asarray([0.0, -1.0, -1.0]),
        )
        and all(not bool(row["simultaneous_pedals"]) for row in candidate_rows)
        and all(
            abs(float(row["max_abs_steer"])) <= 1e-12
            for row in candidate_rows
            if bool(row["in_baseline_set"])
        )
    )
    gates = {
        "source_same_plant_slide_entry_pass": bool(
            source_entry["gates"]["protocol_gates_passed"]
        ),
        "physical_action_contract_pass": action_contract_pass,
        "nested_control_sets_pass": baseline_ids < expanded_ids,
        "row_count_pass": len(candidate_rows) == expected_rows,
        "initial_state_match_pass": all(bool(row["initial_state_match"]) for row in candidate_rows),
        "matched_initial_hash_pass": all(
            int(row["initial_state_hash_count"]) == 1 for row in seed_verdicts
        ),
        "initial_slide_truth_pass": all(bool(row["initial_slide_truth"]) for row in candidate_rows),
        "runtime_obs_finite_pass": all(bool(row["runtime_obs_finite"]) for row in candidate_rows),
        "tire_truth_pass": all(bool(row["tire_truth_complete"]) for row in candidate_rows),
        "exact_replay_pass": (
            len(replay_rows) == len(cells) * 2
            and all(bool(row["exact_pass"]) for row in replay_rows)
        ),
        "weak_recovery_set_inclusion_pass": all(
            bool(row["weak_inclusion_pass"]) for row in seed_verdicts
        ),
        "quick_strict_witness_pass": (
            not quick
            or len(robust_strict) == len(cells)
        ),
        "full_strict_count_pass": quick or len(robust_strict) >= MIN_FULL_ROBUST_STRICT_CELLS,
        "full_strict_sign_coverage_pass": quick or strict_signs == {-1, 1},
        "full_strict_beta_coverage_pass": quick or len(strict_beta_tiers) >= 2,
    }
    health_names = (
        "source_same_plant_slide_entry_pass",
        "physical_action_contract_pass",
        "nested_control_sets_pass",
        "row_count_pass",
        "initial_state_match_pass",
        "matched_initial_hash_pass",
        "initial_slide_truth_pass",
        "runtime_obs_finite_pass",
        "tire_truth_pass",
        "exact_replay_pass",
        "weak_recovery_set_inclusion_pass",
    )
    healthy = all(gates[name] for name in health_names)
    strict_names = (
        "quick_strict_witness_pass",
        "full_strict_count_pass",
        "full_strict_sign_coverage_pass",
        "full_strict_beta_coverage_pass",
    )
    supported = healthy and all(gates[name] for name in strict_names)
    decision = (
        "strict_recovery_expansion_support"
        if supported
        else ("no_strict_witness" if healthy else "inconclusive")
    )
    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": build_preregistration()["claim_boundary"],
        "cells": [asdict(cell) for cell in cells],
        "seeds_per_cell": seeds_per_cell,
        "policy_library": [asdict(spec) for spec in policies],
        "baseline_policy_count": len(baseline_ids),
        "expanded_policy_count": len(expanded_ids),
        "expected_candidate_rows": expected_rows,
        "candidate_rows": candidate_rows,
        "seed_verdicts": seed_verdicts,
        "cell_verdicts": cell_verdicts,
        "replay_rows": replay_rows,
        "gates": gates,
        "robust_strict_cell_count": len(robust_strict),
        "robust_strict_cell_ids": [row["cell_id"] for row in robust_strict],
        "robust_strict_signs": sorted(strict_signs),
        "robust_strict_beta_tiers": sorted(strict_beta_tiers),
        "decision": decision,
        "finite_postslip_strict_certificate_admitted": supported,
        "universal_postslip_claim_admitted": False,
        "old_audit_counts_admitted": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }
    g1._write_csv(run_dir / "candidate_rows.csv", candidate_rows)
    g1._write_csv(run_dir / "seed_verdicts.csv", seed_verdicts)
    g1._write_csv(run_dir / "cell_verdicts.csv", cell_verdicts)
    g1._write_csv(run_dir / "replay_rows.csv", replay_rows)
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
    summary = run(quick=bool(args.quick), resume=bool(args.resume))
    _write_json(output, summary)
    print(
        json.dumps(
            _jsonable(
                {
                    "path": str(output.relative_to(REPO_ROOT)),
                    "decision": summary["decision"],
                    "robust_strict_cell_count": summary["robust_strict_cell_count"],
                    **summary["gates"],
                }
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
