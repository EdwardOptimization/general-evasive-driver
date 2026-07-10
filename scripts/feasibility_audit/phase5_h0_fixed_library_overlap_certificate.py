#!/usr/bin/env python3
"""Exhaustively replay a frozen action library on pre-slip overlap cells."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
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


MILESTONE_ID = "m3270-phase5-h0-fixed-library-overlap-certificate"
SEED_BASE = 32700017
TOLERANCE_M = g1.DISTANCE_TOLERANCE_M
SOURCE_PATHS = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json",
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication.json",
)

PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h0_fixed_library_overlap_certificate_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h0_fixed_library_overlap_certificate_quick.json"
)
FULL_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_h0_fixed_library_overlap_certificate.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_h0_fixed_library_overlap_certificate"

QUICK_CELLS = (g1.BoundaryCell("h0_quick_mu0p60_v16", 0.60, 16.0),)
FULL_CELLS = (
    g1.BoundaryCell("h0_mu0p48_v16", 0.48, 16.0),
    g1.BoundaryCell("h0_mu0p60_v16", 0.60, 16.0),
    g1.BoundaryCell("h0_mu0p90_v16", 0.90, 16.0),
)
QUICK_SEEDS_PER_CELL = 2
FULL_SEEDS_PER_CELL = 8


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


def build_action_library() -> list[dict[str, Any]]:
    by_hash: dict[str, dict[str, Any]] = {}
    for source_path in SOURCE_PATHS:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        for search in payload["chrono"]["searches"]:
            segments = np.asarray(search["best_segments_physical"], dtype="<f8")
            segment_hash = hashlib.sha256(segments.tobytes()).hexdigest()
            provenance = {
                "source_artifact": str(source_path.relative_to(REPO_ROOT)),
                "source_cell_id": search["cell_id"],
                "source_arm": search["arm"],
                "source_seed": int(search["seed"]),
                "source_d_star_m": search["refined"]["d_star_m"],
            }
            if segment_hash not in by_hash:
                by_hash[segment_hash] = {
                    "action_id": f"action_{segment_hash[:16]}",
                    "segments_float64_sha256": segment_hash,
                    "segments_physical": segments,
                    "horizon_s": float(search["budget"]["horizon_s"]),
                    "provenance": [provenance],
                }
            else:
                existing = by_hash[segment_hash]
                if not math.isclose(float(existing["horizon_s"]), float(search["budget"]["horizon_s"])):
                    raise ValueError(f"duplicate action hash with different horizon: {segment_hash}")
                existing["provenance"].append(provenance)
    return [by_hash[key] for key in sorted(by_hash)]


def action_library_sha256(library: list[dict[str, Any]]) -> str:
    canonical = [
        {
            "action_id": row["action_id"],
            "segments_float64_sha256": row["segments_float64_sha256"],
            "horizon_s": row["horizon_s"],
            "provenance": row["provenance"],
        }
        for row in library
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _scenario(cell: g1.BoundaryCell, horizon_s: float, seed: int) -> dict[str, Any]:
    budget = g1.BoundaryBudget(1, 1, 1, 1, 1, horizon_s)
    g1.MILESTONE_ID = MILESTONE_ID
    return g1._chrono_scenario(cell, budget, seed)


def _trajectory_array(points: list[g1.TrajectoryPoint]) -> np.ndarray:
    return np.asarray(
        [[point.x, point.y, point.psi, point.speed, point.beta, point.rear_slip] for point in points],
        dtype=np.float64,
    )


def _local_frame_pass(points: list[g1.TrajectoryPoint]) -> bool:
    if not points:
        return False
    initial = points[0]
    return max(abs(initial.x), abs(initial.y), abs(initial.psi)) <= 1e-12


def _simulate_action(
    client: Any,
    cell: g1.BoundaryCell,
    action: dict[str, Any],
    seed: int,
    *,
    replay: bool,
) -> dict[str, Any]:
    horizon_s = float(action["horizon_s"])
    scenario = _scenario(cell, horizon_s, seed)
    steps = int(round(horizon_s / g1.DT))
    physical = g0._expand_segments(np.asarray(action["segments_physical"], dtype=np.float64), steps)
    commands = np.asarray(
        [g0.physical_command_to_model_action(*command) for command in physical],
        dtype=np.float64,
    )

    def rollout(tag: str) -> tuple[list[g1.TrajectoryPoint], list[tuple[np.ndarray, bool, bool, str, dict]]]:
        client.reset(
            scenario,
            episode_id=f"{MILESTONE_ID}-{cell.cell_id}-{seed}-{action['action_id']}-{tag}",
            seed=seed,
        )
        step_rows, _ = client.step_many(commands)
        return g1._chrono_trajectory(step_rows, scenario), step_rows

    points, step_rows = rollout("primary")
    classifications = {
        arm: g1.refine_distance_for_trajectory(points, cell, arm)
        for arm in g1.ARMS
    }
    replay_result: dict[str, Any] = {"performed": False, "exact_pass": None, "max_abs_error": None}
    if replay:
        replay_points, _ = rollout("replay")
        lhs = _trajectory_array(points)
        rhs = _trajectory_array(replay_points)
        same_shape = lhs.shape == rhs.shape
        max_error = float(np.max(np.abs(lhs - rhs))) if same_shape and lhs.size else float("inf")
        replay_result = {
            "performed": True,
            "same_shape": same_shape,
            "exact_pass": bool(same_shape and max_error <= 1e-12),
            "max_abs_error": max_error,
        }
    final_info = step_rows[-1][4] if step_rows else {}
    initial = points[0] if points else None
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "validation_seed": seed,
        "action_id": action["action_id"],
        "segments_float64_sha256": action["segments_float64_sha256"],
        "horizon_s": horizon_s,
        "provenance": action["provenance"],
        "trajectory_steps": len(points) - 1,
        "initial_local_pose": None
        if initial is None
        else {"x": initial.x, "y": initial.y, "psi": initial.psi},
        "local_frame_pass": _local_frame_pass(points),
        "finite_rear_tire_steps": sum(point.rear_slip > 0.0 for point in points),
        "termination_reason": str(final_info.get("termination_reason", "")),
        "grip_d_star_m": classifications["grip"]["d_star_m"],
        "required_slide_d_star_m": classifications["required_slide"]["d_star_m"],
        "free_d_star_m": classifications["free"]["d_star_m"],
        "grip_boundary": classifications["grip"]["boundary"],
        "required_slide_boundary": classifications["required_slide"]["boundary"],
        "free_boundary": classifications["free"]["boundary"],
        "replay": replay_result,
    }


def _seed_verdict(cell: g1.BoundaryCell, seed: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    def best(field: str) -> dict[str, Any] | None:
        eligible = [row for row in rows if row[field] is not None]
        return None if not eligible else min(eligible, key=lambda row: float(row[field]))

    grip = best("grip_d_star_m")
    slide = best("required_slide_d_star_m")
    free = best("free_d_star_m")
    complete = grip is not None and slide is not None and free is not None
    grip_d = None if grip is None else float(grip["grip_d_star_m"])
    slide_d = None if slide is None else float(slide["required_slide_d_star_m"])
    free_d = None if free is None else float(free["free_d_star_m"])
    free_mode = None if free is None else free["free_boundary"].get("free_mode_classification")
    no_drift = bool(complete and grip_d <= slide_d + TOLERANCE_M)
    free_consistency = bool(complete and free_d <= min(grip_d, slide_d) + TOLERANCE_M)
    free_counterexample = bool(
        complete
        and free_mode == "controlled_slide_like"
        and free_d + TOLERANCE_M < grip_d
    )
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "validation_seed": seed,
        "action_count": len(rows),
        "grip_candidate_count": sum(row["grip_d_star_m"] is not None for row in rows),
        "required_slide_candidate_count": sum(
            row["required_slide_d_star_m"] is not None for row in rows
        ),
        "free_candidate_count": sum(row["free_d_star_m"] is not None for row in rows),
        "grip_d_star_m": grip_d,
        "required_slide_d_star_m": slide_d,
        "free_d_star_m": free_d,
        "grip_action_id": None if grip is None else grip["action_id"],
        "required_slide_action_id": None if slide is None else slide["action_id"],
        "free_action_id": None if free is None else free["action_id"],
        "free_mode_classification": free_mode,
        "drift_advantage_m": None if not complete else grip_d - slide_d,
        "overlap_complete": complete,
        "no_drift_advantage_pass": no_drift,
        "free_consistency_pass": free_consistency,
        "free_slide_counterexample": free_counterexample,
    }


def _cell_verdict(cell: g1.BoundaryCell, rows: list[dict[str, Any]]) -> dict[str, Any]:
    gaps = [float(row["drift_advantage_m"]) for row in rows if row["drift_advantage_m"] is not None]
    return {
        "cell_id": cell.cell_id,
        "mu": cell.mu,
        "speed_mps": cell.speed_mps,
        "seed_count": len(rows),
        "overlap_seed_count": sum(bool(row["overlap_complete"]) for row in rows),
        "all_seeds_overlap_complete": all(bool(row["overlap_complete"]) for row in rows),
        "all_seeds_no_drift_advantage": all(bool(row["no_drift_advantage_pass"]) for row in rows),
        "all_seeds_free_consistent": all(bool(row["free_consistency_pass"]) for row in rows),
        "free_slide_counterexample": any(bool(row["free_slide_counterexample"]) for row in rows),
        "max_drift_advantage_m": max(gaps, default=None),
        "min_drift_advantage_m": min(gaps, default=None),
    }


def _run_cell(
    cell: g1.BoundaryCell,
    library: list[dict[str, Any]],
    seeds: list[int],
    worker_count: int,
) -> list[dict[str, Any]]:
    from chrono_worker_client import ChronoWorkerClient

    tasks = [(seed_index, seed, action) for seed_index, seed in enumerate(seeds) for action in library]
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
                seed_index, seed, action = tasks[index]
                rows[index] = _simulate_action(
                    client,
                    cell,
                    action,
                    seed,
                    replay=seed_index == 0,
                )

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(worker, worker_index) for worker_index in range(worker_count)]
            for future in futures:
                future.result()
    finally:
        for client in clients:
            try:
                client.close()
            except Exception:
                pass
    assert all(row is not None for row in rows)
    return [dict(row) for row in rows if row is not None]


def build_preregistration() -> dict[str, Any]:
    library = build_action_library()
    provenance_count = sum(len(row["provenance"]) for row in library)
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "priced_by": "experiments/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication.json",
        "primary_claim": (
            "For the frozen finite action library and overlap-domain Chrono cells, exhaustive "
            "fresh-seed replay finds finite grip and required-slide boundaries on every seed, "
            "and grip D-star is no larger than slide D-star by more than 0.25 m."
        ),
        "action_library": {
            "selection_rule": (
                "all unique best physical segment sequences from every Chrono search in M3267 "
                "corrected quick and M3269 full; include successful and failed source searches"
            ),
            "source_artifacts": [
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "sha256": _sha256_file(path),
                }
                for path in SOURCE_PATHS
            ],
            "unique_action_count": len(library),
            "provenance_count": provenance_count,
            "library_sha256": action_library_sha256(library),
            "actions": [
                {
                    key: _jsonable(row[key])
                    for key in (
                        "action_id",
                        "segments_float64_sha256",
                        "horizon_s",
                        "provenance",
                    )
                }
                for row in library
            ],
        },
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
        },
        "seeds": {
            "seed_base": SEED_BASE,
            "quick_per_cell": QUICK_SEEDS_PER_CELL,
            "full_per_cell": FULL_SEEDS_PER_CELL,
            "quick_full_disjoint": True,
            "exact_replay": "every action on the first fresh seed of each cell",
        },
        "metric": {
            "d_star": "minimum clearable obstacle-center distance; smaller is better",
            "distance_range_m": [g1.DISTANCE_MIN_M, g1.DISTANCE_MAX_M],
            "refinement_step_m": g1.DISTANCE_REFINE_STEP_M,
            "tolerance_m": TOLERANCE_M,
        },
        "mode_contract": {
            "grip": "beta<=0.12 through pass",
            "required_slide": (
                "four frames beta in [0.20,0.60], rear slip>=0.15, onset vehicle front before "
                "OBB near face, global beta<=0.70 through pass"
            ),
            "free": "global beta<=0.70 with common road, speed, and collision constraints",
            "classification": "every replayed trajectory is evaluated under all three predicates",
        },
        "decision_rule": {
            "support": (
                "all expected rows use the registered local frame and exact replays exist; every "
                "full cell/seed has finite grip, slide, and free D-star; grip<=slide+0.25 m; free "
                "consistency passes; no early-slide free counterexample"
            ),
            "counterexample": (
                "any complete full cell/seed has slide or controlled-slide-like free D-star more "
                "than 0.25 m below grip"
            ),
            "inconclusive": "any row, overlap, tire-truth, replay, or free-consistency gate fails",
        },
        "claim_boundary": (
            "exact finite-library/finite-cell simulator certificate plus independent numerical "
            "validation of the force-envelope theorem; not a continuous Chrono control-set proof"
        ),
        "forbidden": [
            "optimization or action mutation",
            "dropping failed source actions",
            "selecting full cells or seeds after replay",
            "interpreting the result as universal detailed-vehicle dominance",
            "overwriting M3269's inconclusive continuous-search verdict",
        ],
    }


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    mode = "quick" if quick else "full"
    cells = QUICK_CELLS if quick else FULL_CELLS
    seeds_per_cell = QUICK_SEEDS_PER_CELL if quick else FULL_SEEDS_PER_CELL
    library = build_action_library()
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
        replay_rows = _run_cell(cell, library, seeds, 4 if quick else 8)
        seed_verdicts = [
            _seed_verdict(
                cell,
                seed,
                [row for row in replay_rows if int(row["validation_seed"]) == seed],
            )
            for seed in seeds
        ]
        chunk = {
            "cell": asdict(cell),
            "validation_seeds": seeds,
            "replay_rows": replay_rows,
            "seed_verdicts": seed_verdicts,
            "cell_verdict": _cell_verdict(cell, seed_verdicts),
        }
        chunks.append(chunk)
        g0._append_progress(
            progress_path,
            {"stage": "cell_done", **chunk["cell_verdict"]},
        )
        _write_json(
            checkpoint_path,
            {
                "milestone_id": MILESTONE_ID,
                "mode": mode,
                "library_sha256": action_library_sha256(library),
                "chunks": chunks,
            },
        )

    replay_rows = [row for chunk in chunks for row in chunk["replay_rows"]]
    seed_verdicts = [row for chunk in chunks for row in chunk["seed_verdicts"]]
    cell_verdicts = [chunk["cell_verdict"] for chunk in chunks]
    expected_rows = len(cells) * seeds_per_cell * len(library)
    replay_gate_rows = [row for row in replay_rows if bool(row["replay"]["performed"])]
    literature = json.loads(SOURCE_PATHS[0].read_text(encoding="utf-8"))
    onset = json.loads(
        (
            REPO_ROOT
            / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
        ).read_text(encoding="utf-8")
    )
    gates = {
        "action_library_frozen_pass": action_library_sha256(library)
        == build_preregistration()["action_library"]["library_sha256"],
        "row_count_pass": len(replay_rows) == expected_rows,
        "local_frame_pass": all(bool(row["local_frame_pass"]) for row in replay_rows),
        "tire_truth_pass": all(int(row["finite_rear_tire_steps"]) > 0 for row in replay_rows),
        "exact_replay_pass": (
            len(replay_gate_rows) == len(cells) * len(library)
            and all(bool(row["replay"]["exact_pass"]) for row in replay_gate_rows)
        ),
        "literature_positive_control_pass": bool(
            literature["gates"]["literature_positive_control_pass"]
        ),
        "same_plant_slide_entry_pass": bool(onset["gates"]["protocol_gates_passed"]),
        "overlap_complete_pass": all(bool(row["overlap_complete"]) for row in seed_verdicts),
        "no_drift_advantage_pass": all(
            bool(row["no_drift_advantage_pass"]) for row in seed_verdicts
        ),
        "free_consistency_pass": all(bool(row["free_consistency_pass"]) for row in seed_verdicts),
        "no_free_slide_counterexample_pass": not any(
            bool(row["free_slide_counterexample"]) for row in seed_verdicts
        ),
    }
    health_names = (
        "action_library_frozen_pass",
        "row_count_pass",
        "local_frame_pass",
        "tire_truth_pass",
        "exact_replay_pass",
        "literature_positive_control_pass",
        "same_plant_slide_entry_pass",
        "overlap_complete_pass",
        "free_consistency_pass",
    )
    healthy = all(gates[name] for name in health_names)
    counterexample = healthy and (
        not gates["no_drift_advantage_pass"]
        or not gates["no_free_slide_counterexample_pass"]
    )
    supported = (
        healthy
        and gates["no_drift_advantage_pass"]
        and gates["no_free_slide_counterexample_pass"]
    )
    decision = "finite_library_overlap_support" if supported else (
        "counterexample_found" if counterexample else "inconclusive"
    )
    gaps = [
        float(row["drift_advantage_m"])
        for row in seed_verdicts
        if row["drift_advantage_m"] is not None
    ]
    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": build_preregistration()["claim_boundary"],
        "action_library": {
            "unique_action_count": len(library),
            "provenance_count": sum(len(row["provenance"]) for row in library),
            "library_sha256": action_library_sha256(library),
            "actions": _jsonable(library),
        },
        "cells": [asdict(cell) for cell in cells],
        "seeds_per_cell": seeds_per_cell,
        "expected_replay_rows": expected_rows,
        "replay_rows": replay_rows,
        "seed_verdicts": seed_verdicts,
        "cell_verdicts": cell_verdicts,
        "gates": gates,
        "max_drift_advantage_m": max(gaps, default=None),
        "min_drift_advantage_m": min(gaps, default=None),
        "decision": decision,
        "finite_library_certificate_admitted": supported,
        "continuous_chrono_dominance_claim_admitted": False,
        "m3269_overridden": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }
    library_rows = [
        {
            "action_id": row["action_id"],
            "segments_float64_sha256": row["segments_float64_sha256"],
            "horizon_s": row["horizon_s"],
            "provenance_json": json.dumps(_jsonable(row["provenance"]), sort_keys=True),
            "segments_physical_json": json.dumps(_jsonable(row["segments_physical"])),
        }
        for row in library
    ]
    flat_replay_rows = [
        {
            key: value
            for key, value in row.items()
            if key
            not in {
                "provenance",
                "initial_local_pose",
                "grip_boundary",
                "required_slide_boundary",
                "free_boundary",
                "replay",
            }
        }
        | {
            "provenance_json": json.dumps(_jsonable(row["provenance"]), sort_keys=True),
            "initial_local_pose_json": json.dumps(
                _jsonable(row["initial_local_pose"]), sort_keys=True
            ),
            "grip_boundary_json": json.dumps(_jsonable(row["grip_boundary"]), sort_keys=True),
            "required_slide_boundary_json": json.dumps(
                _jsonable(row["required_slide_boundary"]), sort_keys=True
            ),
            "free_boundary_json": json.dumps(_jsonable(row["free_boundary"]), sort_keys=True),
            "replay_json": json.dumps(_jsonable(row["replay"]), sort_keys=True),
        }
        for row in replay_rows
    ]
    g1._write_csv(run_dir / "action_library.csv", library_rows)
    g1._write_csv(run_dir / "replay_rows.csv", flat_replay_rows)
    g1._write_csv(run_dir / "seed_verdicts.csv", seed_verdicts)
    g1._write_csv(run_dir / "cell_verdicts.csv", cell_verdicts)
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
