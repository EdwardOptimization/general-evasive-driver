#!/usr/bin/env python3
"""Final anchored Chrono pre-slip reachable-boundary adjudication."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase5_g1_preslip_reachable_set_adjudication as g1
import phase5_g2_chrono_preslip_boundary_adjudication as g2


MILESTONE_ID = "m3269-phase5-g3-anchored-chrono-preslip-adjudication"
SEED_BASE = 32690017
ANCHOR_SOURCE_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json"
)
ANCHOR_INSERTION_INDEX = 4

PREREG_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication_prereg.json"
)
QUICK_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication_quick.json"
)
FULL_PATH = (
    REPO_ROOT
    / "experiments/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication.json"
)
RUN_DIR = REPO_ROOT / "runs/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication"

QUICK_BUDGET = g1.BoundaryBudget(7, 6, 2, 2, 1, 2.2)
FULL_BUDGET = g1.BoundaryBudget(9, 16, 4, 5, 2, 2.6)
QUICK_CELLS = (g1.BoundaryCell("g3_quick_chrono_mu0p48_v16", 0.48, 16.0),)
FULL_CELLS = (
    g1.BoundaryCell("g3_chrono_mu0p35_v16", 0.35, 16.0),
    g1.BoundaryCell("g3_chrono_mu0p60_v16", 0.60, 16.0),
    g1.BoundaryCell("g3_chrono_mu0p90_v16", 0.90, 16.0),
)

_ORIGINAL_STRUCTURED_CANDIDATES = g1._structured_candidates


def _anchor_record() -> dict[str, Any]:
    payload = json.loads(ANCHOR_SOURCE_PATH.read_text(encoding="utf-8"))
    return next(row for row in payload["chrono"]["searches"] if row["arm"] == "required_slide")


def _anchor_segments(count: int) -> np.ndarray:
    source = np.asarray(_anchor_record()["best_segments_physical"], dtype=np.float64)
    return g1._resample_segments(source, count)


def _anchor_sha256() -> str:
    source = np.asarray(_anchor_record()["best_segments_physical"], dtype="<f8")
    return hashlib.sha256(source.tobytes()).hexdigest()


def _anchored_structured_candidates(
    arm: str,
    cell_id: str,
    segments: int,
    *,
    chrono: bool,
) -> list[np.ndarray]:
    candidates = list(
        _ORIGINAL_STRUCTURED_CANDIDATES(arm, cell_id, segments, chrono=chrono)
    )
    if chrono and arm == "required_slide":
        index = min(ANCHOR_INSERTION_INDEX, len(candidates))
        candidates.insert(index, _anchor_segments(segments))
    return candidates


def _configure_delegate() -> None:
    g1._structured_candidates = _anchored_structured_candidates
    g2.MILESTONE_ID = MILESTONE_ID
    g2.SEED_BASE = SEED_BASE
    g2.PREREG_PATH = PREREG_PATH
    g2.QUICK_PATH = QUICK_PATH
    g2.FULL_PATH = FULL_PATH
    g2.RUN_DIR = RUN_DIR
    g2.QUICK_BUDGET = QUICK_BUDGET
    g2.FULL_BUDGET = FULL_BUDGET
    g2.QUICK_CELLS = QUICK_CELLS
    g2.FULL_CELLS = FULL_CELLS


def build_preregistration() -> dict[str, Any]:
    anchor = _anchor_record()
    return {
        "milestone_id": MILESTONE_ID,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "priced_by": [
            "experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json",
            "experiments/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication_quick.json",
        ],
        "theory_certificate": "docs/preslip-reachable-set-dual-proof-theory-2026-07.md",
        "primary_claim": (
            "Within three frozen Chrono/TMeasy lane-aligned static-OBB cells, pooled grip-mode "
            "D-star is no larger than required controlled-slide D-star by more than 0.25 m."
        ),
        "frozen_feasibility_anchor": {
            "source_artifact": str(ANCHOR_SOURCE_PATH.relative_to(REPO_ROOT)),
            "source_cell_id": anchor["cell_id"],
            "source_arm": anchor["arm"],
            "source_seed": anchor["seed"],
            "source_d_star_m": anchor["refined"]["d_star_m"],
            "source_exact_replay_pass": anchor["replay"]["exact_pass"],
            "source_segments_shape": list(np.asarray(anchor["best_segments_physical"]).shape),
            "source_segments_float64_sha256": _anchor_sha256(),
            "candidate_insertion_index": ANCHOR_INSERTION_INDEX,
            "joint_search_distance_m": 11.0 + 3.0 * ANCHOR_INSERTION_INDEX,
            "role": (
                "known feasible required-slide seed for search recall; it receives no extra "
                "actuator authority and is re-evaluated under every frozen cell"
            ),
        },
        "cells": {
            "quick": [asdict(cell) for cell in QUICK_CELLS],
            "full": [asdict(cell) for cell in FULL_CELLS],
        },
        "budgets": {"quick": asdict(QUICK_BUDGET), "full": asdict(FULL_BUDGET)},
        "metric": {
            "d_star": "minimum obstacle-center distance cleared; smaller is better",
            "distance_range_m": [g1.DISTANCE_MIN_M, g1.DISTANCE_MAX_M],
            "refinement_step_m": g1.DISTANCE_REFINE_STEP_M,
            "tolerance_m": g1.DISTANCE_TOLERANCE_M,
        },
        "mode_and_geometry_contract": {
            "grip": "beta<=0.12 through pass",
            "required_slide": (
                "four frames beta in [0.20,0.60], rear slip>=0.15, onset vehicle front before "
                "OBB near face, global beta<=0.70 through pass"
            ),
            "common": "speed>=4 m/s, lane-aligned OBB, road containment, no collision",
            "pooling": "reclassify every stored best trajectory under every mode predicate",
        },
        "health_gates": {
            "positive_controls": "M3265 literature and M3266 slide-entry controls remain true",
            "all_seeds_complete": "every dedicated arm/seed and pooled arm has finite D-star",
            "free_consistency": "dedicated free D-star <= best pooled constrained D-star +0.25 m",
            "seed_robust": "worst dedicated grip seed <= best dedicated slide seed +0.25 m",
            "connector": "local frame, finite rear tire truth, and exact replay <=1e-12",
        },
        "decision_rule": {
            "support": "every health, pooled no-drift, seed-robust, and no-counterexample gate passes",
            "falsify": "under healthy searches, slide beats grip by more than 0.25 m",
            "inconclusive": "any arm, seed, free, frame, tire, replay, or robustness gate fails",
        },
        "seed_discipline": {
            "seed_base": SEED_BASE,
            "quick_full": "disjoint cells and SHA256-derived optimizer streams",
            "arm_streams": "disjoint, with identical budgets within each cell",
        },
        "stop_rule": (
            "This is the final detailed-model optimizer route. Any failed quick/full gate stops "
            "further local search repair and leaves empirical support unproved."
        ),
        "claim_boundary": (
            "finite selected Chrono/TMeasy cells only; M3267 planar incompleteness remains; no "
            "universal detailed-vehicle, split-mu, moving-obstacle, cross-vehicle, or real-car claim"
        ),
    }


def run(*, quick: bool, resume: bool) -> dict[str, Any]:
    _configure_delegate()
    summary = g2.run(quick=quick, resume=resume)
    summary["milestone_id"] = MILESTONE_ID
    summary["claim_boundary"] = build_preregistration()["claim_boundary"]
    summary["frozen_feasibility_anchor"] = build_preregistration()["frozen_feasibility_anchor"]
    summary["final_optimizer_route"] = True
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
        g1._write_json(PREREG_PATH, build_preregistration())
        print(PREREG_PATH.relative_to(REPO_ROOT))
        return
    output = QUICK_PATH if args.quick else FULL_PATH
    if args.resume and output.exists():
        print(output.relative_to(REPO_ROOT))
        return
    summary = run(quick=bool(args.quick), resume=bool(args.resume))
    g1._write_json(output, summary)
    print(
        json.dumps(
            g1._jsonable(
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
