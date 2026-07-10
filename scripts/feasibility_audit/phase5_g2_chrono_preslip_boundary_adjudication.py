#!/usr/bin/env python3
"""Run the fresh-seed Chrono-only pre-slip reachable-boundary adjudication."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase5_g1_preslip_reachable_set_adjudication as g1


MILESTONE_ID = "m3268-phase5-g2-chrono-preslip-boundary-adjudication"
SEED_BASE = 32680017
ARMS = g1.ARMS
DISTANCE_TOLERANCE_M = g1.DISTANCE_TOLERANCE_M

PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication_quick.json"
)
FULL_PATH = (
    REPO_ROOT / "experiments/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication"

QUICK_BUDGET = g1.BoundaryBudget(segments=7, population=6, elites=2, iterations=2, search_seeds=1, horizon_s=2.2)
FULL_BUDGET = g1.BoundaryBudget(segments=9, population=16, elites=4, iterations=5, search_seeds=2, horizon_s=2.6)

QUICK_CELLS = (g1.BoundaryCell("g2_quick_chrono_mu0p48_v16", 0.48, 16.0),)
FULL_CELLS = (
    g1.BoundaryCell("g2_chrono_mu0p35_v16", 0.35, 16.0),
    g1.BoundaryCell("g2_chrono_mu0p60_v16", 0.60, 16.0),
    g1.BoundaryCell("g2_chrono_mu0p90_v16", 0.90, 16.0),
)


def _jsonable(value: Any) -> Any:
    return g1._jsonable(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    g1._write_json(path, payload)


def _configure_parent() -> None:
    g1.SEED_BASE = SEED_BASE
    g1.MILESTONE_ID = MILESTONE_ID


def _points(search: dict[str, Any]) -> list[g1.TrajectoryPoint]:
    return [g1.TrajectoryPoint(**row) for row in search["best_trajectory"]]


def _pooled_cell_verdict(
    cell: g1.BoundaryCell,
    searches: list[dict[str, Any]],
    arm_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidate_rows: list[dict[str, Any]] = []
    for search in searches:
        points = _points(search)
        for target_arm in ARMS:
            refined = g1.refine_distance_for_trajectory(points, cell, target_arm)
            candidate_rows.append(
                {
                    "cell_id": cell.cell_id,
                    "source_arm": search["arm"],
                    "source_seed": search["seed"],
                    "target_arm": target_arm,
                    "d_star_m": refined["d_star_m"],
                    "boundary": refined["boundary"],
                }
            )

    pooled: dict[str, dict[str, Any] | None] = {}
    for arm in ARMS:
        eligible = [
            row
            for row in candidate_rows
            if row["target_arm"] == arm and row["d_star_m"] is not None
        ]
        pooled[arm] = (
            None if not eligible else min(eligible, key=lambda row: float(row["d_star_m"]))
        )

    dedicated = {arm: next(row for row in arm_rows if row["arm"] == arm) for arm in ARMS}
    dedicated_complete = all(row["d_star_m"] is not None for row in dedicated.values())
    every_seed_complete = all(
        all(value is not None for value in row["seed_d_stars_m"])
        and len(row["seed_d_stars_m"]) == FULL_BUDGET.search_seeds
        for row in dedicated.values()
    ) if len(searches) > len(ARMS) else dedicated_complete
    pooled_complete = all(pooled[arm] is not None for arm in ARMS)

    grip_d = None if pooled["grip"] is None else float(pooled["grip"]["d_star_m"])
    slide_d = (
        None if pooled["required_slide"] is None else float(pooled["required_slide"]["d_star_m"])
    )
    free_d = None if pooled["free"] is None else float(pooled["free"]["d_star_m"])
    dedicated_free_d = dedicated["free"]["d_star_m"]
    complete = grip_d is not None and slide_d is not None and free_d is not None
    free_consistency = bool(
        complete
        and dedicated_free_d is not None
        and float(dedicated_free_d) <= min(grip_d, slide_d) + DISTANCE_TOLERANCE_M
    )
    no_drift_advantage = bool(
        complete and grip_d <= slide_d + DISTANCE_TOLERANCE_M
    )

    grip_seed_ds = [float(value) for value in dedicated["grip"]["seed_d_stars_m"] if value is not None]
    slide_seed_ds = [
        float(value) for value in dedicated["required_slide"]["seed_d_stars_m"] if value is not None
    ]
    seed_robust_no_drift = bool(
        grip_seed_ds
        and slide_seed_ds
        and max(grip_seed_ds) <= min(slide_seed_ds) + DISTANCE_TOLERANCE_M
    )

    dedicated_free_boundary = dedicated["free"].get("best_boundary") or {}
    free_early_slide = (
        dedicated_free_boundary.get("free_mode_classification") == "controlled_slide_like"
    )
    free_slide_counterexample = bool(
        complete
        and free_early_slide
        and dedicated_free_d is not None
        and float(dedicated_free_d) + DISTANCE_TOLERANCE_M < grip_d
    )
    return (
        {
            "cell_id": cell.cell_id,
            "mu": cell.mu,
            "speed_mps": cell.speed_mps,
            "dedicated_grip_d_star_m": dedicated["grip"]["d_star_m"],
            "dedicated_required_slide_d_star_m": dedicated["required_slide"]["d_star_m"],
            "dedicated_free_d_star_m": dedicated_free_d,
            "pooled_grip_d_star_m": grip_d,
            "pooled_required_slide_d_star_m": slide_d,
            "pooled_free_d_star_m": free_d,
            "drift_advantage_m": None if not complete else grip_d - slide_d,
            "dedicated_all_arms_complete": dedicated_complete,
            "every_search_seed_complete": every_seed_complete,
            "pooled_all_arms_complete": pooled_complete,
            "free_consistency_pass": free_consistency,
            "no_drift_advantage_pass": no_drift_advantage,
            "seed_robust_no_drift_pass": seed_robust_no_drift,
            "free_mode_classification": dedicated_free_boundary.get("free_mode_classification"),
            "free_slide_counterexample": free_slide_counterexample,
            "pooled_sources": {
                arm: None
                if pooled[arm] is None
                else {
                    "source_arm": pooled[arm]["source_arm"],
                    "source_seed": pooled[arm]["source_seed"],
                }
                for arm in ARMS
            },
        },
        candidate_rows,
    )


def _combine_chunks(chunks: list[dict[str, Any]], budget: g1.BoundaryBudget) -> dict[str, Any]:
    searches = [row for chunk in chunks for row in chunk["searches"]]
    arm_rows = [row for chunk in chunks for row in chunk["arm_rows"]]
    cells = [row for chunk in chunks for row in chunk["cells"]]
    verdicts: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for cell_row in cells:
        cell = g1.BoundaryCell(**cell_row)
        cell_searches = [row for row in searches if row["cell_id"] == cell.cell_id]
        cell_arm_rows = [row for row in arm_rows if row["cell_id"] == cell.cell_id]
        verdict, rows = _pooled_cell_verdict(cell, cell_searches, cell_arm_rows)
        verdicts.append(verdict)
        candidate_rows.extend(rows)
    return {
        "backend": "chrono",
        "budget": asdict(budget),
        "cells": cells,
        "searches": searches,
        "arm_rows": arm_rows,
        "pooled_candidate_rows": candidate_rows,
        "cell_verdicts": verdicts,
    }


def _run_chunks(
    *,
    cells: tuple[g1.BoundaryCell, ...],
    budget: g1.BoundaryBudget,
    quick: bool,
    resume: bool,
) -> dict[str, Any]:
    mode = "quick" if quick else "full"
    run_dir = RUN_DIR / mode
    progress_path = run_dir / "progress.jsonl"
    checkpoint_path = run_dir / "checkpoint.json"
    chunks: list[dict[str, Any]] = []
    if resume and checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        chunks = list(checkpoint.get("chunks", []))
    elif progress_path.exists():
        progress_path.unlink()
    completed = {row["cells"][0]["cell_id"] for row in chunks if row.get("cells")}
    for cell in cells:
        if cell.cell_id in completed:
            continue
        chunk = g1.run_backend(
            backend="chrono",
            cells=(cell,),
            budget=budget,
            progress_path=progress_path,
        )
        chunks.append(chunk)
        _write_json(
            checkpoint_path,
            {
                "milestone_id": MILESTONE_ID,
                "mode": mode,
                "completed_cell_ids": [row["cells"][0]["cell_id"] for row in chunks],
                "chunks": chunks,
            },
        )
    return _combine_chunks(chunks, budget)


def build_preregistration() -> dict[str, Any]:
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "priced_by": (
            "experiments/feasibility_audit/"
            "phase5_g1_preslip_reachable_set_adjudication_quick.json"
        ),
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "primary_claim": (
            "Within the frozen Chrono/TMeasy lane-aligned static-OBB cells, the pooled minimum "
            "clearable distance of grip-mode trajectories is no larger than that of required "
            "controlled-slide trajectories by more than 0.25 m."
        ),
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
        },
        "budgets": {"quick": asdict(QUICK_BUDGET), "full": asdict(FULL_BUDGET)},
        "metric": {
            "d_star": "minimum obstacle-center distance cleared; smaller is better",
            "tolerance_m": DISTANCE_TOLERANCE_M,
            "refinement_step_m": g1.DISTANCE_REFINE_STEP_M,
            "distance_range_m": [g1.DISTANCE_MIN_M, g1.DISTANCE_MAX_M],
        },
        "arms": {
            "grip": "beta<=0.12 through pass, speed>=4 m/s, common actuator/road constraints",
            "required_slide": (
                "four frames with beta in [0.20,0.60] and rear slip>=0.15 before true contact; "
                "global beta<=0.70 and speed>=4 m/s through pass"
            ),
            "free": "no mode requirement; global beta<=0.70 and common constraints",
        },
        "pooling_rule": (
            "Persist dedicated grip/required-slide/free searches, then re-evaluate every stored "
            "best trajectory under every mode predicate. Use pooled constrained D-stars for the "
            "primary comparison while retaining dedicated free-search consistency."
        ),
        "positive_and_health_gates": {
            "literature_positive_control": "M3265 0.20/0.26 rad/s witness remains true",
            "same_plant_slide_entry": "M3266 full protocol gates remain true",
            "dedicated_all_arms_complete": "every arm and every optimizer seed has finite D-star",
            "pooled_all_arms_complete": "every cell has finite pooled grip, slide, and free D-star",
            "free_consistency": "dedicated free D-star <= min pooled constrained D-star +0.25 m",
            "seed_robust_no_drift": "worst dedicated grip seed <= best dedicated slide seed +0.25 m",
            "chrono_local_frame": "every trajectory begins at local (0,0,0)",
            "chrono_exact_replay": "every best action replays within 1e-12",
            "tire_truth": "every best search has finite rear-tire telemetry",
        },
        "decision_rule": {
            "support": (
                "all positive, health, pooled no-drift, seed-robust no-drift, and no-free-slide-"
                "counterexample gates pass in every full cell"
            ),
            "falsify": (
                "under healthy complete searches, any pooled required-slide or early-slide free "
                "trajectory beats pooled grip by more than 0.25 m"
            ),
            "inconclusive": "any completeness, free, replay, frame, tire, or seed-robustness gate fails",
        },
        "seed_discipline": {
            "seed_base": SEED_BASE,
            "quick_full": "disjoint cells and SHA256-derived streams",
            "arms": "disjoint optimizer streams with identical budgets",
        },
        "claim_boundary": (
            "finite Chrono/TMeasy cells only; supports the bounded force-envelope theorem bridge "
            "but does not prove a universal detailed-vehicle theorem"
        ),
        "negative_result_policy": (
            "M3267's planar incompleteness remains visible and cannot be overwritten by this panel"
        ),
        "out_of_scope": [
            "planar-set emptiness",
            "split-mu",
            "moving obstacles",
            "terminal pose requirements",
            "slide-only direct yaw moment",
            "other vehicles or tires",
            "real-car validation",
        ],
    }


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    if not PREREG_PATH.exists():
        raise FileNotFoundError(f"missing preregistration: {PREREG_PATH}")
    _configure_parent()
    backend = _run_chunks(
        cells=QUICK_CELLS if quick else FULL_CELLS,
        budget=QUICK_BUDGET if quick else FULL_BUDGET,
        quick=quick,
        resume=resume,
    )
    literature = json.loads(
        (
            REPO_ROOT
            / "experiments/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.json"
        ).read_text(encoding="utf-8")
    )
    onset = json.loads(
        (
            REPO_ROOT
            / "experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json"
        ).read_text(encoding="utf-8")
    )
    searches = backend["searches"]
    verdicts = backend["cell_verdicts"]
    local_frame = all(
        search["best_trajectory"]
        and all(
            abs(float(search["best_trajectory"][0][axis])) <= 1e-12
            for axis in ("x", "y", "psi")
        )
        for search in searches
    )
    gates = {
        "literature_positive_control_pass": bool(literature["positive_control"]["positive_control_pass"]),
        "same_plant_slide_entry_pass": bool(onset["gates"]["protocol_gates_passed"]),
        "dedicated_all_arms_complete_pass": all(
            bool(row["dedicated_all_arms_complete"]) for row in verdicts
        ),
        "every_search_seed_complete_pass": all(
            bool(row["every_search_seed_complete"]) for row in verdicts
        ),
        "pooled_all_arms_complete_pass": all(bool(row["pooled_all_arms_complete"]) for row in verdicts),
        "free_consistency_pass": all(bool(row["free_consistency_pass"]) for row in verdicts),
        "no_drift_advantage_pass": all(bool(row["no_drift_advantage_pass"]) for row in verdicts),
        "seed_robust_no_drift_pass": all(bool(row["seed_robust_no_drift_pass"]) for row in verdicts),
        "no_free_slide_counterexample_pass": not any(
            bool(row["free_slide_counterexample"]) for row in verdicts
        ),
        "chrono_local_frame_pass": local_frame,
        "chrono_exact_replay_pass": all(bool(search["replay"]["exact_pass"]) for search in searches),
        "chrono_tire_truth_pass": all(
            int(search["best_search_result"].get("finite_rear_tire_steps", 0)) > 0
            for search in searches
        ),
    }
    health_names = (
        "literature_positive_control_pass",
        "same_plant_slide_entry_pass",
        "dedicated_all_arms_complete_pass",
        "every_search_seed_complete_pass",
        "pooled_all_arms_complete_pass",
        "free_consistency_pass",
        "chrono_local_frame_pass",
        "chrono_exact_replay_pass",
        "chrono_tire_truth_pass",
    )
    healthy = all(gates[name] for name in health_names)
    falsified = healthy and (
        not gates["no_drift_advantage_pass"]
        or not gates["no_free_slide_counterexample_pass"]
    )
    supported = (
        healthy
        and gates["no_drift_advantage_pass"]
        and gates["seed_robust_no_drift_pass"]
        and gates["no_free_slide_counterexample_pass"]
    )
    decision = "bounded_empirical_support" if supported else (
        "counterexample_found" if falsified else "inconclusive"
    )
    advantages = [
        float(row["drift_advantage_m"])
        for row in verdicts
        if row["drift_advantage_m"] is not None
    ]
    mode = "quick" if quick else "full"
    summary = {
        "milestone_id": MILESTONE_ID,
        "mode": mode,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": build_preregistration()["claim_boundary"],
        "chrono": backend,
        "gates": gates,
        "max_drift_advantage_m": max(advantages, default=None),
        "decision": decision,
        "theory_bridge_supported": supported,
        "dominance_claim_admitted": supported,
        "m3267_planar_inconclusive_overridden": False,
        "incumbent_changed": False,
        "self_id_claim": False,
    }
    run_dir = RUN_DIR / mode
    g1._write_csv(run_dir / "dedicated_arm_rows.csv", list(backend["arm_rows"]))
    g1._write_csv(run_dir / "pooled_candidate_rows.csv", list(backend["pooled_candidate_rows"]))
    g1._write_csv(run_dir / "cell_verdicts.csv", list(verdicts))
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
