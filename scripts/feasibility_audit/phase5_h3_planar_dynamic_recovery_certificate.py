#!/usr/bin/env python3
"""Test strict post-slip recovery on continuously reached planar slide states."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from autodrift.dynamics import SingleTrackDriftModel, VehicleParams, VehicleState
import phase5_g0_preslip_reachability_proof_pricing as g0
import phase5_g0b_slide_mode_onset_pricing as g0b
import phase5_g1_preslip_reachable_set_adjudication as g1
import phase5_h1_postslip_nested_recovery_certificate as h1


MILESTONE_ID = "m3273-phase5-h3-planar-dynamic-recovery-certificate"
MIN_TIME_ADVANTAGE_S = 0.20
PREFIX_TOTAL_STEPS = 120
SOURCE_PATH = (
    REPO_ROOT / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
)
PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h3_planar_dynamic_recovery_certificate_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h3_planar_dynamic_recovery_certificate_quick.json"
)
FULL_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h3_planar_dynamic_recovery_certificate.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_h3_planar_dynamic_recovery_certificate"


@dataclass(frozen=True)
class PlanarBranchCell:
    cell_id: str
    source_cell_id: str
    mu: float
    speed_mps: float
    branch_step: int
    branch_time_s: float


SOURCE_CELLS = {
    "mu0p35_v12": (0.35, 12.0),
    "mu0p60_v14": (0.60, 14.0),
    "mu0p90_v16": (0.90, 16.0),
}


def _cell(source_cell_id: str, step: int) -> PlanarBranchCell:
    mu, speed = SOURCE_CELLS[source_cell_id]
    return PlanarBranchCell(
        f"h3_{source_cell_id}_step{step:03d}",
        source_cell_id,
        mu,
        speed,
        step,
        step * h1.DT,
    )


QUICK_CELLS = (
    _cell("mu0p35_v12", 45),
    _cell("mu0p35_v12", 60),
    _cell("mu0p35_v12", 75),
    _cell("mu0p60_v14", 35),
    _cell("mu0p60_v14", 50),
    _cell("mu0p60_v14", 65),
    _cell("mu0p90_v16", 30),
    _cell("mu0p90_v16", 44),
    _cell("mu0p90_v16", 58),
)
FULL_CELLS = tuple(
    _cell(source, step)
    for source, steps in (
        ("mu0p35_v12", (42, 54, 66, 78, 90, 102, 114)),
        ("mu0p60_v14", (34, 44, 54, 64, 74, 84, 90)),
        ("mu0p90_v16", (30, 38, 46, 54, 62, 70, 78)),
    )
    for step in steps
)


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


def source_segments_by_cell() -> dict[str, np.ndarray]:
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    return {
        str(row["cell_id"]): np.asarray(row["best_segments_physical"], dtype="<f8")
        for row in payload["planar"]["searches"]
    }


def source_hashes() -> dict[str, str]:
    return {
        cell_id: hashlib.sha256(segments.tobytes()).hexdigest()
        for cell_id, segments in source_segments_by_cell().items()
    }


def _state_metrics(
    model: SingleTrackDriftModel,
    state: VehicleState,
) -> tuple[float, float, float]:
    beta = math.atan2(state.vy, max(abs(state.vx), 1e-9))
    forces = model.tire_forces(
        state.vx,
        state.vy,
        state.yaw_rate,
        state.steer,
        state.drive_force,
    )
    return beta, abs(float(forces.alpha_rear)), abs(float(forces.alpha_front))


def _simulate_prefix(cell: PlanarBranchCell) -> dict[str, Any]:
    model = SingleTrackDriftModel(VehicleParams(mu=cell.mu))
    state = VehicleState(0.0, 0.0, 0.0, cell.speed_mps, 0.0, 0.0)
    physical = g0._expand_segments(
        source_segments_by_cell()[cell.source_cell_id],
        PREFIX_TOTAL_STEPS,
    )[: cell.branch_step]
    trace = [state.as_array()]
    beta_trace: list[float] = []
    rear_trace: list[float] = []
    for command in physical:
        state, _forces = model.step(
            state,
            g0.physical_command_to_model_action(*command),
            h1.DT,
        )
        beta, rear_slip, _front_slip = _state_metrics(model, state)
        beta_trace.append(beta)
        rear_trace.append(rear_slip)
        trace.append(state.as_array())
    branch_beta, branch_rear_slip, branch_front_slip = _state_metrics(model, state)
    dwell = beta_trace[-g0b.SLIDE_DWELL_STEPS :]
    branch_slide_truth = bool(
        len(dwell) == g0b.SLIDE_DWELL_STEPS
        and all(abs(beta) >= g0b.SLIDE_BETA_MIN_RAD for beta in dwell)
        and abs(branch_beta) >= g0b.SLIDE_BETA_MIN_RAD
        and branch_rear_slip >= g0b.REAR_SLIP_MIN_RAD
    )
    trajectory = np.vstack(trace)
    return {
        "model": model,
        "state": state,
        "trajectory": trajectory,
        "trajectory_sha256": hashlib.sha256(np.asarray(trajectory, dtype="<f8").tobytes()).hexdigest(),
        "state_sha256": hashlib.sha256(state.as_array().astype("<f8").tobytes()).hexdigest(),
        "branch_beta_rad": branch_beta,
        "branch_yaw_rate_rad_s": state.yaw_rate,
        "branch_vx_mps": state.vx,
        "branch_rear_slip_angle_rad": branch_rear_slip,
        "branch_front_slip_angle_rad": branch_front_slip,
        "branch_four_frame_beta_dwell": len(dwell) == g0b.SLIDE_DWELL_STEPS
        and all(abs(beta) >= g0b.SLIDE_BETA_MIN_RAD for beta in dwell),
        "branch_slide_truth": branch_slide_truth,
    }


def _run_policy(cell: PlanarBranchCell, spec: h1.PolicySpec, *, tag: str) -> dict[str, Any]:
    prefix = _simulate_prefix(cell)
    model: SingleTrackDriftModel = prefix["model"]
    state = VehicleState.from_array(prefix["state"].as_array())
    trace = [np.asarray(row, dtype=np.float64) for row in prefix["trajectory"]]
    stable_run = 0
    recovery_step: int | None = None
    max_abs_steer = 0.0
    max_abs_beta = abs(float(prefix["branch_beta_rad"]))
    max_abs_yaw = abs(state.yaw_rate)
    min_vx = state.vx
    completion_reason = "prefix_invalid" if not prefix["branch_slide_truth"] else "horizon"
    final_beta = float(prefix["branch_beta_rad"])
    if prefix["branch_slide_truth"]:
        for step in range(1, h1.HORIZON_STEPS + 1):
            action, steer = h1._policy_action(spec, final_beta, state.yaw_rate)
            state, _forces = model.step(state, action, h1.DT)
            final_beta, _rear_slip, _front_slip = _state_metrics(model, state)
            trace.append(state.as_array())
            max_abs_steer = max(max_abs_steer, abs(steer))
            max_abs_beta = max(max_abs_beta, abs(final_beta))
            max_abs_yaw = max(max_abs_yaw, abs(state.yaw_rate))
            min_vx = min(min_vx, state.vx)
            recovered_now = (
                abs(final_beta) <= h1.RECOVERY_BETA_MAX_RAD
                and abs(state.yaw_rate) <= h1.RECOVERY_YAW_MAX_RAD_S
                and state.vx >= h1.RECOVERY_MIN_VX_MPS
            )
            stable_run = stable_run + 1 if recovered_now else 0
            if stable_run >= h1.RECOVERY_STABLE_STEPS:
                recovery_step = step - h1.RECOVERY_STABLE_STEPS + 1
                completion_reason = "recovered"
                break
            if abs(final_beta) > h1.SPIN_BETA_RAD:
                completion_reason = "spin"
                break
            if abs(state.vx) < 1.5 and abs(final_beta) > 0.25:
                completion_reason = "stopped_sideways"
                break
    trajectory = np.vstack(trace)
    success = recovery_step is not None
    return {
        "cell_id": cell.cell_id,
        "source_cell_id": cell.source_cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "branch_step": cell.branch_step,
        "branch_time_s": cell.branch_time_s,
        "policy_id": spec.policy_id,
        "policy_family": spec.family,
        "in_baseline_set": spec.in_baseline_set,
        "physical_throttle": spec.throttle,
        "physical_brake": spec.brake,
        "prefix_source_segments_sha256": source_hashes()[cell.source_cell_id],
        "prefix_trajectory_sha256": prefix["trajectory_sha256"],
        "branch_state_sha256": prefix["state_sha256"],
        "branch_beta_rad": prefix["branch_beta_rad"],
        "branch_yaw_rate_rad_s": prefix["branch_yaw_rate_rad_s"],
        "branch_vx_mps": prefix["branch_vx_mps"],
        "branch_rear_slip_angle_rad": prefix["branch_rear_slip_angle_rad"],
        "branch_front_slip_angle_rad": prefix["branch_front_slip_angle_rad"],
        "branch_four_frame_beta_dwell": prefix["branch_four_frame_beta_dwell"],
        "branch_slide_truth": prefix["branch_slide_truth"],
        "success": success,
        "recovery_step": recovery_step,
        "recovery_time_s": None if recovery_step is None else recovery_step * h1.DT,
        "vx_at_recovery_mps": None if not success else state.vx,
        "completion_reason": completion_reason,
        "max_abs_steer": max_abs_steer,
        "max_abs_beta_rad": max_abs_beta,
        "max_abs_yaw_rate_rad_s": max_abs_yaw,
        "min_vx_mps": min_vx,
        "final_beta_rad": final_beta,
        "final_yaw_rate_rad_s": state.yaw_rate,
        "final_vx_mps": state.vx,
        "trajectory_shape": list(trajectory.shape),
        "trajectory_float64_sha256": hashlib.sha256(
            np.asarray(trajectory, dtype="<f8").tobytes()
        ).hexdigest(),
        "tag": tag,
    }


def _best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        rows,
        key=lambda row: (
            not bool(row["success"]),
            h1.HORIZON_STEPS + 1
            if row["recovery_step"] is None
            else int(row["recovery_step"]),
            abs(float(row["final_beta_rad"])),
            -float(row["final_vx_mps"]),
            str(row["policy_id"]),
        ),
    )


def cell_verdict(cell: PlanarBranchCell, rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_rows = [row for row in rows if bool(row["in_baseline_set"])]
    baseline_best = _best_row(baseline_rows)
    expanded_best = _best_row(rows)
    baseline_success = any(bool(row["success"]) for row in baseline_rows)
    expanded_success = any(bool(row["success"]) for row in rows)
    baseline_time = (
        None
        if not baseline_success
        else min(float(row["recovery_time_s"]) for row in baseline_rows if row["success"])
    )
    expanded_time = (
        None
        if not expanded_success
        else min(float(row["recovery_time_s"]) for row in rows if row["success"])
    )
    time_advantage = (
        None
        if expanded_time is None
        else (
            (h1.HORIZON_STEPS + 1) * h1.DT - expanded_time
            if baseline_time is None
            else baseline_time - expanded_time
        )
    )
    eligible = bool(
        len({row["prefix_trajectory_sha256"] for row in rows}) == 1
        and len({row["branch_state_sha256"] for row in rows}) == 1
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
        "source_cell_id": cell.source_cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "branch_step": cell.branch_step,
        "branch_time_s": cell.branch_time_s,
        "candidate_count": len(rows),
        "baseline_candidate_count": len(baseline_rows),
        "prefix_trajectory_hash_count": len({row["prefix_trajectory_sha256"] for row in rows}),
        "branch_state_hash_count": len({row["branch_state_sha256"] for row in rows}),
        "branch_beta_rad": rows[0]["branch_beta_rad"],
        "branch_yaw_rate_rad_s": rows[0]["branch_yaw_rate_rad_s"],
        "branch_rear_slip_angle_rad": rows[0]["branch_rear_slip_angle_rad"],
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
        else [
            expanded_time,
            (h1.HORIZON_STEPS + 1) * h1.DT if baseline_time is None else baseline_time,
        ],
    }


def _run_cell(cell: PlanarBranchCell, policies: list[h1.PolicySpec]) -> dict[str, Any]:
    rows = [_run_policy(cell, spec, tag="primary") for spec in policies]
    verdict = cell_verdict(cell, rows)
    baseline_best = _best_row([row for row in rows if bool(row["in_baseline_set"])])
    expanded_best = _best_row(rows)
    by_id = {spec.policy_id: spec for spec in policies}
    replays = []
    for role, original in (("baseline_best", baseline_best), ("expanded_best", expanded_best)):
        replayed = _run_policy(cell, by_id[str(original["policy_id"])], tag=f"replay-{role}")
        replays.append(
            {
                "cell_id": cell.cell_id,
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
            }
        )
    return {"cell": asdict(cell), "candidate_rows": rows, "cell_verdict": verdict, "replay_rows": replays}


def build_preregistration() -> dict[str, Any]:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    policies = h1.policy_library()
    baseline = [spec.policy_id for spec in policies if spec.in_baseline_set]
    expanded = [spec.policy_id for spec in policies]
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "priced_by": {
            "path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
            "sha256": _sha256_file(SOURCE_PATH),
            "planar_entry_cells_passed": sum(
                bool(row["mode_valid"]) for row in source["planar"]["best_rows"]
            ),
            "planar_entry_cell_count": len(source["planar"]["best_rows"]),
        },
        "m3271_m3272_disposition": (
            "Chrono direct reset was tire-inconsistent and the valid moderate dynamic prefix "
            "had zero steering advantage; H3 changes the physics axis to M3266-priced deeper "
            "planar states and does not repair Chrono policies or thresholds"
        ),
        "primary_claim": (
            "On eligible continuously reached deep planar slide states, the unchanged expanded "
            "finite policy set strictly enlarges finite-horizon recovery relative to its exact "
            "zero-steer baseline subset."
        ),
        "source_prefixes": {
            "segments_float64_sha256_by_cell": source_hashes(),
            "segments_physical_by_cell": {
                key: value.tolist() for key, value in source_segments_by_cell().items()
            },
            "expanded_total_steps": PREFIX_TOTAL_STEPS,
            "role": "common state generation only",
        },
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
            "eligibility": "four-frame beta>=0.20 and branch rear slip>=0.15 with matched full Markov state",
        },
        "control_sets": {
            "baseline_policy_ids": baseline,
            "expanded_policy_ids": expanded,
            "baseline_subset_of_expanded": set(baseline).issubset(expanded),
            "policies": [asdict(spec) for spec in policies],
            "physical_zero_maps_to_normalized_minus_one": True,
            "esc_claim": False,
        },
        "recovery_contract": {
            "horizon_steps": h1.HORIZON_STEPS,
            "dt_s": h1.DT,
            "beta_abs_max_rad": h1.RECOVERY_BETA_MAX_RAD,
            "yaw_rate_abs_max_rad_s": h1.RECOVERY_YAW_MAX_RAD_S,
            "minimum_forward_speed_mps": h1.RECOVERY_MIN_VX_MPS,
            "stable_steps": h1.RECOVERY_STABLE_STEPS,
            "minimum_time_advantage_s": MIN_TIME_ADVANTAGE_S,
        },
        "decision_rule": {
            "quick_support": "at least 6/9 cells eligible and 2 strict across at least 2 mu tiers",
            "full_support": "at least 15/21 eligible and 5 strict across at least 2 mu tiers with all health gates passing",
            "strict_witness": "added steering succeeds at least 0.20 s before the best baseline or while all baselines fail",
        },
        "claim_boundary": (
            "exact deterministic finite-prefix/finite-state/finite-policy single-track-model "
            "certificate; not detailed Chrono strictness, all post-slip states, or real cars"
        ),
        "forbidden": [
            "changing prefixes branches policies thresholds or action mapping after results",
            "claiming H3 overrides M3272's valid Chrono negative",
            "calling uniform braking ESC",
            "using normalized pedal zero as physical zero",
            "counting ineligible branch states",
            "universalizing the compact-model witness",
            "mutating ActiveSafetyReflexDriver or training a policy",
        ],
    }


def run(*, quick: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    cells = QUICK_CELLS if quick else FULL_CELLS
    policies = h1.policy_library()
    chunks = [_run_cell(cell, policies) for cell in cells]
    candidate_rows = [row for chunk in chunks for row in chunk["candidate_rows"]]
    cell_verdicts = [chunk["cell_verdict"] for chunk in chunks]
    replay_rows = [row for chunk in chunks for row in chunk["replay_rows"]]
    eligible = [row for row in cell_verdicts if bool(row["eligible_slide_state"])]
    strict = [row for row in cell_verdicts if bool(row["strict_expansion_witness"])]
    strict_mu = {float(row["mu"]) for row in strict}
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    baseline_ids = {spec.policy_id for spec in policies if spec.in_baseline_set}
    expanded_ids = {spec.policy_id for spec in policies}
    gates = {
        "source_prefixes_frozen_pass": source_hashes()
        == prereg["source_prefixes"]["segments_float64_sha256_by_cell"],
        "physical_action_contract_pass": np.array_equal(
            g0.physical_command_to_model_action(0.0, 0.0, 0.0),
            np.asarray([0.0, -1.0, -1.0]),
        ),
        "nested_control_sets_pass": baseline_ids < expanded_ids,
        "row_count_pass": len(candidate_rows) == len(cells) * len(policies),
        "matched_prefix_state_pass": all(
            int(row["prefix_trajectory_hash_count"]) == 1
            and int(row["branch_state_hash_count"]) == 1
            for row in cell_verdicts
        ),
        "exact_replay_pass": len(replay_rows) == len(cells) * 2
        and all(bool(row["exact_pass"]) for row in replay_rows),
        "weak_recovery_set_inclusion_pass": all(
            bool(row["weak_inclusion_pass"]) for row in cell_verdicts
        ),
        "quick_eligible_count_pass": not quick or len(eligible) >= 6,
        "quick_strict_count_pass": not quick or len(strict) >= 2,
        "quick_strict_mu_coverage_pass": not quick or len(strict_mu) >= 2,
        "full_eligible_count_pass": quick or len(eligible) >= 15,
        "full_strict_count_pass": quick or len(strict) >= 5,
        "full_strict_mu_coverage_pass": quick or len(strict_mu) >= 2,
    }
    health_names = (
        "source_prefixes_frozen_pass",
        "physical_action_contract_pass",
        "nested_control_sets_pass",
        "row_count_pass",
        "matched_prefix_state_pass",
        "exact_replay_pass",
        "weak_recovery_set_inclusion_pass",
    )
    threshold_names = (
        "quick_eligible_count_pass",
        "quick_strict_count_pass",
        "quick_strict_mu_coverage_pass",
        "full_eligible_count_pass",
        "full_strict_count_pass",
        "full_strict_mu_coverage_pass",
    )
    healthy = all(gates[name] for name in health_names)
    supported = healthy and all(gates[name] for name in threshold_names)
    decision = (
        "planar_dynamic_strict_recovery_support"
        if supported
        else ("no_strict_witness" if healthy else "inconclusive")
    )
    mode = "quick" if quick else "full"
    run_dir = RUN_DIR / mode
    g1._write_csv(run_dir / "candidate_rows.csv", candidate_rows)
    g1._write_csv(run_dir / "cell_verdicts.csv", cell_verdicts)
    g1._write_csv(run_dir / "replay_rows.csv", replay_rows)
    return {
        "milestone_id": MILESTONE_ID,
        "mode": mode,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": build_preregistration()["claim_boundary"],
        "cells": [asdict(cell) for cell in cells],
        "policy_library": [asdict(spec) for spec in policies],
        "candidate_rows": candidate_rows,
        "cell_verdicts": cell_verdicts,
        "replay_rows": replay_rows,
        "gates": gates,
        "eligible_cell_count": len(eligible),
        "strict_cell_count": len(strict),
        "strict_cell_ids": [row["cell_id"] for row in strict],
        "strict_mu_tiers": sorted(strict_mu),
        "decision": decision,
        "finite_planar_postslip_strict_certificate_admitted": supported,
        "chrono_postslip_strict_claim_admitted": False,
        "universal_postslip_claim_admitted": False,
        "m3272_overridden": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }


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
                    "decision": summary["decision"],
                    "eligible_cell_count": summary["eligible_cell_count"],
                    "strict_cell_count": summary["strict_cell_count"],
                    **summary["gates"],
                }
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
