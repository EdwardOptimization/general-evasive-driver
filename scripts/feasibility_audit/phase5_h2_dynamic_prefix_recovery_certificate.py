#!/usr/bin/env python3
"""Branch nested recovery controls from continuously reached Chrono slide states."""

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
import phase5_h1_postslip_nested_recovery_certificate as h1


MILESTONE_ID = "m3272-phase5-h2-dynamic-prefix-recovery-certificate"
SEED_BASE = 32720023
PREFIX_TOTAL_STEPS = 120
RECOVERY_STEPS = h1.HORIZON_STEPS
MIN_TIME_ADVANTAGE_S = 0.20
MIN_QUICK_ELIGIBLE_CELLS = 3
MIN_FULL_ROBUST_ELIGIBLE_CELLS = 8
MIN_FULL_ROBUST_STRICT_CELLS = 3

SOURCE_PATH = (
    REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
)
PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h2_dynamic_prefix_recovery_certificate_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h2_dynamic_prefix_recovery_certificate_quick.json"
)
FULL_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h2_dynamic_prefix_recovery_certificate.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_h2_dynamic_prefix_recovery_certificate"


@dataclass(frozen=True)
class BranchCell:
    cell_id: str
    branch_step: int
    branch_time_s: float
    mu: float = 0.48
    speed_mps: float = 16.0


def _branch_cell(step: int) -> BranchCell:
    return BranchCell(f"h2_branch_step{step:03d}", step, step * h1.DT)


QUICK_CELLS = tuple(_branch_cell(step) for step in (30, 45, 60, 75, 90))
FULL_CELLS = tuple(_branch_cell(step) for step in range(30, 97, 6))
QUICK_SEEDS_PER_CELL = 1
FULL_SEEDS_PER_CELL = 3


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


def source_segments() -> np.ndarray:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    return np.asarray(payload["chrono"]["search"]["best_segments_physical"], dtype="<f8")


def source_segments_sha256() -> str:
    return hashlib.sha256(source_segments().tobytes()).hexdigest()


def _scenario(cell: BranchCell, seed: int) -> dict[str, Any]:
    import phase4_f2_train as f2

    scenario = f2._avoidance_scenario(
        seed,
        max_steps=int(cell.branch_step) + RECOVERY_STEPS,
        reveal=30.0,
        mu=float(cell.mu),
    )
    scenario["scenario_id"] = f"{MILESTONE_ID}-{cell.cell_id}-{seed}"
    scenario["obstacle"] = {"enabled": False}
    scenario["track_width"] = 100.0
    scenario["speed_ref"] = float(cell.speed_mps)
    scenario["initial_state"]["vx"] = float(cell.speed_mps)
    scenario["initial_state"]["vy"] = 0.0
    scenario["initial_state"]["yaw_rate"] = 0.0
    return scenario


def _prefix_actions(branch_step: int) -> np.ndarray:
    physical = g0._expand_segments(source_segments(), PREFIX_TOTAL_STEPS)[:branch_step]
    return np.asarray(
        [g0.physical_command_to_model_action(*command) for command in physical],
        dtype=np.float64,
    )


def _array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(array, dtype="<f8").tobytes()).hexdigest()


def _run_episode(
    client: Any,
    cell: BranchCell,
    seed: int,
    spec: h1.PolicySpec,
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
    trace = [h1._state_vector(obs, reset_info)]
    runtime_obs_finite = bool(np.isfinite(obs).all())
    tire_truth_steps = 0
    prefix_rows, prefix_stopped_early = client.step_many(_prefix_actions(cell.branch_step))
    for prefix_obs, _terminated, _truncated, _status, prefix_info in prefix_rows:
        runtime_obs_finite = runtime_obs_finite and bool(np.isfinite(prefix_obs).all())
        rear_slip, _front_slip, wheel_count = g0b._rear_front_tire_slip(prefix_info)
        if wheel_count >= 4 and math.isfinite(rear_slip):
            tire_truth_steps += 1
        trace.append(h1._state_vector(prefix_obs, prefix_info))

    if prefix_rows:
        obs, prefix_terminated, prefix_truncated, prefix_status, branch_info = prefix_rows[-1]
    else:
        prefix_terminated = prefix_truncated = False
        prefix_status = "reset"
        branch_info = reset_info
    branch_vx, branch_vy, branch_yaw, branch_beta = h1._kinematics(obs, branch_info)
    branch_rear_slip, branch_front_slip, branch_wheel_count = g0b._rear_front_tire_slip(
        branch_info
    )
    dwell_rows = prefix_rows[-g0b.SLIDE_DWELL_STEPS :]
    four_frame_beta_dwell = (
        len(dwell_rows) == g0b.SLIDE_DWELL_STEPS
        and all(
            abs(h1._kinematics(row[0], row[4])[3]) >= g0b.SLIDE_BETA_MIN_RAD
            for row in dwell_rows
        )
    )
    branch_slide_truth = bool(
        not prefix_stopped_early
        and not prefix_terminated
        and not prefix_truncated
        and four_frame_beta_dwell
        and abs(branch_beta) >= g0b.SLIDE_BETA_MIN_RAD
        and math.isfinite(branch_rear_slip)
        and branch_rear_slip >= g0b.REAR_SLIP_MIN_RAD
        and branch_wheel_count >= 4
    )
    branch_vector = h1._state_vector(obs, branch_info)
    prefix_trajectory = np.vstack(trace)
    prefix_hash = _array_sha256(prefix_trajectory)
    branch_hash = _array_sha256(branch_vector)

    stable_run = 0
    recovery_step: int | None = None
    max_abs_beta = abs(branch_beta)
    max_abs_yaw = abs(branch_yaw)
    max_abs_steer = 0.0
    min_vx = branch_vx
    collision = bool(branch_info.get("collision", False))
    completion_reason = "prefix_invalid" if not branch_slide_truth else "horizon"
    final_vx, final_vy, final_yaw, final_beta = branch_vx, branch_vy, branch_yaw, branch_beta
    recovery_rollout_steps = 0
    if branch_slide_truth:
        for step in range(1, RECOVERY_STEPS + 1):
            action, steer = h1._policy_action(spec, final_beta, final_yaw)
            obs, terminated, truncated, status, info = client.step(action)
            recovery_rollout_steps = step
            runtime_obs_finite = runtime_obs_finite and bool(np.isfinite(obs).all())
            final_vx, final_vy, final_yaw, final_beta = h1._kinematics(obs, info)
            rear_slip, _front_slip, wheel_count = g0b._rear_front_tire_slip(info)
            if wheel_count >= 4 and math.isfinite(rear_slip):
                tire_truth_steps += 1
            trace.append(h1._state_vector(obs, info))
            max_abs_beta = max(max_abs_beta, abs(final_beta))
            max_abs_yaw = max(max_abs_yaw, abs(final_yaw))
            max_abs_steer = max(max_abs_steer, abs(steer))
            min_vx = min(min_vx, final_vx)
            collision = collision or bool(info.get("collision", False))
            recovered_now = (
                abs(final_beta) <= h1.RECOVERY_BETA_MAX_RAD
                and abs(final_yaw) <= h1.RECOVERY_YAW_MAX_RAD_S
                and final_vx >= h1.RECOVERY_MIN_VX_MPS
                and not collision
            )
            stable_run = stable_run + 1 if recovered_now else 0
            if stable_run >= h1.RECOVERY_STABLE_STEPS:
                recovery_step = step - h1.RECOVERY_STABLE_STEPS + 1
                completion_reason = "recovered"
                break
            if abs(final_beta) > h1.SPIN_BETA_RAD:
                completion_reason = "spin"
                break
            if abs(final_vx) < 1.5 and abs(final_beta) > 0.25:
                completion_reason = "stopped_sideways"
                break
            if terminated or truncated:
                completion_reason = str(info.get("termination_reason", status or "terminated"))
                break

    trajectory = np.vstack(trace)
    total_steps = len(trace) - 1
    success = recovery_step is not None
    return {
        "cell_id": cell.cell_id,
        "branch_step": cell.branch_step,
        "branch_time_s": cell.branch_time_s,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "validation_seed": seed,
        "policy_id": spec.policy_id,
        "policy_family": spec.family,
        "in_baseline_set": spec.in_baseline_set,
        "yaw_gain": spec.yaw_gain,
        "beta_gain": spec.beta_gain,
        "physical_throttle": spec.throttle,
        "physical_brake": spec.brake,
        "prefix_source_segments_sha256": source_segments_sha256(),
        "prefix_trajectory_sha256": prefix_hash,
        "branch_state_sha256": branch_hash,
        "prefix_stopped_early": prefix_stopped_early,
        "branch_beta_rad": branch_beta,
        "branch_yaw_rate_rad_s": branch_yaw,
        "branch_vx_mps": branch_vx,
        "branch_vy_mps": branch_vy,
        "branch_rear_slip_angle_rad": branch_rear_slip,
        "branch_front_slip_angle_rad": branch_front_slip,
        "branch_tire_wheel_count": branch_wheel_count,
        "branch_four_frame_beta_dwell": four_frame_beta_dwell,
        "branch_slide_truth": branch_slide_truth,
        "recovery_rollout_steps": recovery_rollout_steps,
        "total_rollout_steps": total_steps,
        "tire_truth_steps": tire_truth_steps,
        "tire_truth_complete": tire_truth_steps == total_steps,
        "runtime_obs_finite": runtime_obs_finite,
        "success": success,
        "recovery_step": recovery_step,
        "recovery_time_s": None if recovery_step is None else recovery_step * h1.DT,
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
            RECOVERY_STEPS + 1 if row["recovery_step"] is None else int(row["recovery_step"]),
            abs(float(row["final_beta_rad"])),
            -float(row["final_vx_mps"]),
            str(row["policy_id"]),
        ),
    )


def seed_verdict(cell: BranchCell, seed: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_rows = [row for row in rows if bool(row["in_baseline_set"])]
    baseline_best = _best_row(baseline_rows)
    expanded_best = _best_row(rows)
    baseline_success = any(bool(row["success"]) for row in baseline_rows)
    expanded_success = any(bool(row["success"]) for row in rows)
    baseline_time = (
        None if not baseline_success else min(float(row["recovery_time_s"]) for row in baseline_rows if row["success"])
    )
    expanded_time = (
        None if not expanded_success else min(float(row["recovery_time_s"]) for row in rows if row["success"])
    )
    time_advantage = (
        None
        if expanded_time is None
        else ((RECOVERY_STEPS + 1) * h1.DT - expanded_time if baseline_time is None else baseline_time - expanded_time)
    )
    eligible = bool(
        len({row["branch_state_sha256"] for row in rows}) == 1
        and len({row["prefix_trajectory_sha256"] for row in rows}) == 1
        and all(bool(row["branch_slide_truth"]) for row in rows)
    )
    strict = bool(
        eligible
        and expanded_success
        and not bool(expanded_best["in_baseline_set"])
        and float(expanded_best["max_abs_steer"]) > 0.05
        and time_advantage is not None
        and time_advantage + 1e-12 >= MIN_TIME_ADVANTAGE_S
    )
    return {
        "cell_id": cell.cell_id,
        "branch_step": cell.branch_step,
        "branch_time_s": cell.branch_time_s,
        "validation_seed": seed,
        "candidate_count": len(rows),
        "baseline_candidate_count": len(baseline_rows),
        "prefix_trajectory_hash_count": len({row["prefix_trajectory_sha256"] for row in rows}),
        "branch_state_hash_count": len({row["branch_state_sha256"] for row in rows}),
        "branch_beta_rad": rows[0]["branch_beta_rad"],
        "branch_yaw_rate_rad_s": rows[0]["branch_yaw_rate_rad_s"],
        "branch_rear_slip_angle_rad": rows[0]["branch_rear_slip_angle_rad"],
        "branch_slide_truth": all(bool(row["branch_slide_truth"]) for row in rows),
        "eligible_slide_state": eligible,
        "baseline_recovered": baseline_success,
        "expanded_recovered": expanded_success,
        "weak_inclusion_pass": not baseline_success or expanded_success,
        "strict_expansion_witness": strict,
        "best_baseline_policy_id": baseline_best["policy_id"],
        "best_baseline_completion_reason": baseline_best["completion_reason"],
        "best_baseline_recovery_time_s": baseline_time,
        "best_expanded_policy_id": expanded_best["policy_id"],
        "best_expanded_policy_family": expanded_best["policy_family"],
        "best_expanded_recovery_time_s": expanded_time,
        "best_expanded_vx_at_recovery_mps": expanded_best["vx_at_recovery_mps"],
        "best_expanded_max_abs_steer": expanded_best["max_abs_steer"],
        "recovery_time_advantage_s": time_advantage,
        "strict_deadline_interval_s": None
        if not strict
        else [expanded_time, (RECOVERY_STEPS + 1) * h1.DT if baseline_time is None else baseline_time],
        "no_input_recovered": next(
            bool(row["success"]) for row in rows if row["policy_id"] == "pedal_coast"
        ),
        "uniform_brake_recovered": any(
            bool(row["success"]) and str(row["policy_id"]).startswith("pedal_brake")
            for row in rows
        ),
    }


def cell_verdict(cell: BranchCell, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cell_id": cell.cell_id,
        "branch_step": cell.branch_step,
        "branch_time_s": cell.branch_time_s,
        "seed_count": len(rows),
        "eligible_seed_count": sum(bool(row["eligible_slide_state"]) for row in rows),
        "strict_seed_count": sum(bool(row["strict_expansion_witness"]) for row in rows),
        "all_seeds_eligible": all(bool(row["eligible_slide_state"]) for row in rows),
        "all_seeds_strict": all(bool(row["strict_expansion_witness"]) for row in rows),
        "all_seeds_weak_inclusion": all(bool(row["weak_inclusion_pass"]) for row in rows),
        "min_time_advantage_s": min(
            (float(row["recovery_time_advantage_s"]) for row in rows if row["recovery_time_advantage_s"] is not None),
            default=None,
        ),
    }


def _run_cell(
    cell: BranchCell,
    seeds: list[int],
    policies: list[h1.PolicySpec],
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
                    "original_prefix_sha256": original["prefix_trajectory_sha256"],
                    "replay_prefix_sha256": replayed["prefix_trajectory_sha256"],
                    "original_trajectory_sha256": original["trajectory_float64_sha256"],
                    "replay_trajectory_sha256": replayed["trajectory_float64_sha256"],
                    "exact_pass": (
                        original["prefix_trajectory_sha256"] == replayed["prefix_trajectory_sha256"]
                        and original["trajectory_float64_sha256"]
                        == replayed["trajectory_float64_sha256"]
                    ),
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


def _branch_group(step: int) -> str:
    if step <= 48:
        return "early"
    if step <= 72:
        return "middle"
    return "late"


def build_preregistration() -> dict[str, Any]:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    policies = h1.policy_library()
    baseline_ids = [spec.policy_id for spec in policies if spec.in_baseline_set]
    expanded_ids = [spec.policy_id for spec in policies]
    segments = source_segments()
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "priced_by": {
            "path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
            "sha256": _sha256_file(SOURCE_PATH),
            "same_plant_entry_onset_s": source["chrono"]["best_replay"]["first_slide_dwell_time_s"],
            "same_plant_entry_dwell_steps": source["chrono"]["best_replay"]["max_slide_dwell_steps"],
            "same_plant_entry_max_beta_rad": source["chrono"]["best_replay"]["max_abs_beta_rad"],
            "same_plant_entry_max_rear_slip_rad": source["chrono"]["best_replay"]["max_abs_rear_tire_slip_angle_rad"],
        },
        "m3271_disposition": (
            "direct body-state injection failed rear-tire slide truth; H2 branches without reset "
            "from the continuously simulated M3266 source prefix"
        ),
        "primary_claim": (
            "For eligible continuously reached branch states and the frozen nested policy "
            "libraries, added countersteer feedback creates strict finite-horizon recovery "
            "witnesses or at least a 0.20 s recovery-time interval unavailable to the baseline."
        ),
        "source_prefix": {
            "segments_float64_sha256": source_segments_sha256(),
            "segments_physical": segments.tolist(),
            "expanded_total_steps": PREFIX_TOTAL_STEPS,
            "contains_simultaneous_pedal_segments": bool(np.any(segments[:, 1] * segments[:, 2] > 0.0)),
            "role": "common state-generation history only; not a compared recovery policy",
        },
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
            "eligibility": (
                "prefix completes; final four prefix frames beta>=0.20; branch rear slip>=0.15; "
                "four-wheel tire truth; identical prefix and branch hashes across policies"
            ),
        },
        "seeds": {
            "seed_base": SEED_BASE,
            "quick_per_cell": QUICK_SEEDS_PER_CELL,
            "full_per_cell": FULL_SEEDS_PER_CELL,
            "quick_full_disjoint": True,
        },
        "control_sets": {
            "baseline_policy_ids": baseline_ids,
            "expanded_policy_ids": expanded_ids,
            "baseline_subset_of_expanded": set(baseline_ids).issubset(expanded_ids),
            "policies": [asdict(spec) for spec in policies],
            "physical_zero_maps_to_normalized_minus_one": True,
            "recovery_policies_use_simultaneous_pedals": False,
            "esc_claim": False,
        },
        "recovery_contract": {
            "horizon_steps": RECOVERY_STEPS,
            "dt_s": h1.DT,
            "beta_abs_max_rad": h1.RECOVERY_BETA_MAX_RAD,
            "yaw_rate_abs_max_rad_s": h1.RECOVERY_YAW_MAX_RAD_S,
            "minimum_forward_speed_mps": h1.RECOVERY_MIN_VX_MPS,
            "stable_steps": h1.RECOVERY_STABLE_STEPS,
            "minimum_time_advantage_s": MIN_TIME_ADVANTAGE_S,
        },
        "decision_rule": {
            "quick_support": "at least 3/5 branch cells eligible and at least 1 eligible strict witness",
            "full_support": (
                "all health and weak-inclusion gates pass; at least 8/12 cells eligible on all "
                "3 seeds; at least 3 cells strict on all seeds spanning at least 2 branch groups"
            ),
            "strict_witness": (
                "an added steering policy recovers and either every baseline fails or its best "
                "recovery is at least 0.20 s later; the open deadline interval certifies strict "
                "finite-horizon membership"
            ),
        },
        "claim_boundary": (
            "exact finite-prefix/finite-branch/finite-policy Chrono certificate on one signed "
            "Sedan/TMeasy entry family; not all post-slip states, policies, vehicles, or real cars"
        ),
        "forbidden": [
            "resetting body wheel or tire state at the branch",
            "changing prefix branch grid policies thresholds or seeds after results",
            "calling uniform braking ESC",
            "using normalized pedal zero as physical zero",
            "counting ineligible branch states in the denominator for strict recovery",
            "hiding ineligible or baseline-success cells",
            "universalizing the finite signed entry family",
            "mutating ActiveSafetyReflexDriver or training a policy",
        ],
    }


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode = "quick" if quick else "full"
    cells = QUICK_CELLS if quick else FULL_CELLS
    seeds_per_cell = QUICK_SEEDS_PER_CELL if quick else FULL_SEEDS_PER_CELL
    policies = h1.policy_library()
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
    policies_ids = {spec.policy_id for spec in policies}
    baseline_ids = {spec.policy_id for spec in policies if spec.in_baseline_set}
    expected_rows = len(cells) * seeds_per_cell * len(policies)
    robust_eligible = [row for row in cell_verdicts if bool(row["all_seeds_eligible"])]
    robust_strict = [row for row in cell_verdicts if bool(row["all_seeds_strict"])]
    strict_groups = {_branch_group(int(row["branch_step"])) for row in robust_strict}
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    gates = {
        "source_prefix_frozen_pass": source_segments_sha256()
        == prereg["source_prefix"]["segments_float64_sha256"],
        "physical_action_contract_pass": (
            np.array_equal(
                g0.physical_command_to_model_action(0.0, 0.0, 0.0),
                np.asarray([0.0, -1.0, -1.0]),
            )
            and all(
                not (float(row["physical_throttle"]) > 0.0 and float(row["physical_brake"]) > 0.0)
                for row in candidate_rows
            )
        ),
        "nested_control_sets_pass": baseline_ids < policies_ids,
        "row_count_pass": len(candidate_rows) == expected_rows,
        "matched_prefix_hash_pass": all(
            int(row["prefix_trajectory_hash_count"]) == 1 for row in seed_verdicts
        ),
        "matched_branch_state_hash_pass": all(
            int(row["branch_state_hash_count"]) == 1 for row in seed_verdicts
        ),
        "runtime_obs_finite_pass": all(bool(row["runtime_obs_finite"]) for row in candidate_rows),
        "tire_truth_pass": all(bool(row["tire_truth_complete"]) for row in candidate_rows),
        "exact_replay_pass": (
            len(replay_rows) == len(cells) * 2
            and all(bool(row["exact_pass"]) for row in replay_rows)
        ),
        "weak_recovery_set_inclusion_pass": all(
            bool(row["weak_inclusion_pass"]) for row in seed_verdicts
        ),
        "quick_eligible_count_pass": not quick or len(robust_eligible) >= MIN_QUICK_ELIGIBLE_CELLS,
        "quick_strict_witness_pass": not quick or len(robust_strict) >= 1,
        "full_eligible_count_pass": quick or len(robust_eligible) >= MIN_FULL_ROBUST_ELIGIBLE_CELLS,
        "full_strict_count_pass": quick or len(robust_strict) >= MIN_FULL_ROBUST_STRICT_CELLS,
        "full_strict_branch_group_pass": quick or len(strict_groups) >= 2,
    }
    health_names = (
        "source_prefix_frozen_pass",
        "physical_action_contract_pass",
        "nested_control_sets_pass",
        "row_count_pass",
        "matched_prefix_hash_pass",
        "matched_branch_state_hash_pass",
        "runtime_obs_finite_pass",
        "tire_truth_pass",
        "exact_replay_pass",
        "weak_recovery_set_inclusion_pass",
    )
    threshold_names = (
        "quick_eligible_count_pass",
        "quick_strict_witness_pass",
        "full_eligible_count_pass",
        "full_strict_count_pass",
        "full_strict_branch_group_pass",
    )
    healthy = all(gates[name] for name in health_names)
    supported = healthy and all(gates[name] for name in threshold_names)
    decision = (
        "dynamic_prefix_strict_recovery_support"
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
        "expected_candidate_rows": expected_rows,
        "candidate_rows": candidate_rows,
        "seed_verdicts": seed_verdicts,
        "cell_verdicts": cell_verdicts,
        "replay_rows": replay_rows,
        "gates": gates,
        "robust_eligible_cell_count": len(robust_eligible),
        "robust_eligible_cell_ids": [row["cell_id"] for row in robust_eligible],
        "robust_strict_cell_count": len(robust_strict),
        "robust_strict_cell_ids": [row["cell_id"] for row in robust_strict],
        "robust_strict_branch_groups": sorted(strict_groups),
        "decision": decision,
        "finite_postslip_strict_certificate_admitted": supported,
        "universal_postslip_claim_admitted": False,
        "m3271_overridden": False,
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
                    "robust_eligible_cell_count": summary["robust_eligible_cell_count"],
                    "robust_strict_cell_count": summary["robust_strict_cell_count"],
                    **summary["gates"],
                }
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
