"""B3 validation: v5 candidate vs v4 incumbent on four 64-row panels, row by row.

Panels (same 16 spec x profile-binding structure and row order as M3082/M3084,
env rebuilt through the exact fresh_panel_retest.py recipe):

1. ``feasible_only``: the existing deployment-criterion panel (base 601500,
   seeds taken verbatim from
   ``experiments/feasibility_audit/feasible_only_panel_rows.csv``).
2. ``fresh``: the fresh-seed retest panel (base 501500, seed formula).
3. ``old``: the fixed M3082/M3084 panel (base 401500, seed formula) —
   hard no-regression panel: v5 success must stay >= 57 and the
   min_clearance_margin on the 7 known infeasible-row failures must not
   degrade by more than 1e-3 vs the same-run v4 measurement.
4. ``holdout``: a NEW feasible-only panel built by the same deterministic
   label scan at base 701500 (stride 1000), seeds disjoint from all panels
   above — guards against overfitting v5 to the 5 known failure rows.

Both drivers are run on every row of every panel in the same process:
- v4: deployable ``ActiveSafetyReflexDriver`` (M3105 incumbent, untouched);
- v5: ``ActiveSafetyDriverV5Candidate`` (v4 + curvature grip-priority governor
  + anti-spin trim overlay, candidate only).

Outputs:
- experiments/feasibility_audit/v5_panel_validation_rows.csv (one row per
  panel x row x driver)
- experiments/feasibility_audit/v5_panel_validation_summary.json

Deterministic, CPU-only. Usage:
    PYTHONPATH=src python scripts/feasibility_audit/v5_panel_validation.py
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import fresh_panel_retest as fpr  # noqa: E402  (shared env/rollout recipe)

from autodrift.active_safety_driver_v5_curvature_speed_governor_candidate import (  # noqa: E402
    DRIVER_ID as V5_DRIVER_ID,
    V5_POLICY_CONFIG,
    ActiveSafetyDriverV5Candidate,
)
from autodrift.active_safety_reflex_driver import (  # noqa: E402
    DRIVER_ID as V4_DRIVER_ID,
    ActiveSafetyReflexDriver,
    policy_config_fingerprint,
)
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.controller_family_full_rollout_execution import read_csv_rows  # noqa: E402
from autodrift.evaluate import run_episode_with_policy  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/v5_panel_validation_rows.csv"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "experiments/feasibility_audit/v5_panel_validation_summary.json"
FEASIBLE_PANEL_CSV = REPO_ROOT / "experiments/feasibility_audit/feasible_only_panel_rows.csv"
OLD_PANEL_LABELS_CSV = REPO_ROOT / "experiments/feasibility_audit/panel_feasibility_labels.csv"

HOLDOUT_SEED_BASE = 701500
HOLDOUT_SEED_STRIDE = 1000
PANEL_ORDER = ["feasible_only", "fresh", "old", "holdout"]
MARGIN_GUARD_TOLERANCE = 1e-3

# the 7 known old-panel failures of the incumbent (all infeasible-labeled rows)
OLD_PANEL_GUARD_ROWS = [
    "m3082-fresh-panel-0007",
    "m3082-fresh-panel-0010",
    "m3082-fresh-panel-0013",
    "m3082-fresh-panel-0024",
    "m3082-fresh-panel-0025",
    "m3082-fresh-panel-0026",
    "m3082-fresh-panel-0029",
]

CLAIM_BOUNDARY = (
    "v5 candidate same-row validation measurement only; the v5 driver is a candidate and the "
    "deployable ActiveSafetyReflexDriver is unchanged. No promotion, checkpoint mutation, "
    "driver-performance verdict, robustness-result, high-fidelity, paper, or self-ID claim is made."
)


class MeasurementPolicy:
    """Adapter exposing an obs72->action3 driver to the shared rollout loop."""

    def __init__(self, act_fn: Callable[[np.ndarray], np.ndarray]) -> None:
        self._act_fn = act_fn

    def reset(self) -> None:
        pass

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        return self._act_fn(np.asarray(observation, dtype=np.float32))


def measure_row(
    plan: dict,
    seed: int,
    specs: dict,
    profile_cache: dict,
    *,
    panel: str,
    driver_name: str,
    driver_id: str,
    act_fn: Callable[[np.ndarray], np.ndarray],
    row_number: int,
) -> dict:
    env = fpr.build_env_for_plan_row(plan, specs, profile_cache)
    try:
        label = fpr.label_for_seed(env, seed)
        episode = run_episode_with_policy(env, MeasurementPolicy(act_fn), driver_id, int(seed))
    finally:
        env.close()
    success = bool(episode.get("obstacle_completed", False)) and not bool(episode.get("collision", False))
    record = {
        "validation_episode_id": f"v5val-{panel}-{driver_name}-{row_number:04d}",
        "panel": panel,
        "driver": driver_name,
        "runtime_driver_id": driver_id,
        "fresh_panel_row_id": str(plan["fresh_panel_row_id"]),
        "eval_seed": int(seed),
        "spec": str(plan["executable_source_spec_id"]),
        "base_profile_name": str(plan["base_profile_name"]),
        "binding_role": str(plan.get("binding_role", "")),
        "axis_id": str(plan.get("axis_id", "")),
        "task_family": str(plan.get("task_family", "")),
        "label": label,
        "steps": int(episode.get("steps", 0)),
        "success": success,
        "collision": bool(episode.get("collision", False)),
        "obstacle_completed": bool(episode.get("obstacle_completed", False)),
        "termination_reason": str(episode.get("termination_reason", "")),
        "outcome_bucket": str(episode.get("outcome_bucket", "")),
        "min_clearance_margin": episode.get("min_clearance_margin", ""),
        "return": episode.get("return", ""),
        "speed_mean": episode.get("speed_mean", ""),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    record["outcome"] = fpr.outcome_key(record)
    return record


def build_holdout_seeds(
    plan_rows: list[dict], specs: dict, profile_cache: dict, excluded: set[int]
) -> dict[str, tuple[int, str, int]]:
    """Deterministic feasible-label seed scan at HOLDOUT_SEED_BASE (Part C recipe)."""
    chosen: dict[str, tuple[int, str, int]] = {}
    used = set(excluded)
    for plan in plan_rows:
        row_number = int(str(plan["fresh_panel_row_id"]).rsplit("-", 1)[1])
        offset = fpr.seed_for_panel_row(row_number, 0)
        env = fpr.build_env_for_plan_row(plan, specs, profile_cache)
        seed = None
        label = None
        attempts = 0
        try:
            for k in range(0, 64):
                candidate = HOLDOUT_SEED_BASE + offset + k * HOLDOUT_SEED_STRIDE
                attempts += 1
                candidate_label = fpr.label_for_seed(env, candidate)
                if candidate_label in fpr.FEASIBLE_LABELS and candidate not in used:
                    seed, label = candidate, candidate_label
                    break
        finally:
            env.close()
        if seed is None:
            raise RuntimeError(f"no feasible holdout seed found for {plan['fresh_panel_row_id']}")
        used.add(seed)
        chosen[str(plan["fresh_panel_row_id"])] = (seed, str(label), attempts)
    return chosen


def stratified(rows: list[dict]) -> dict[str, dict[str, int]]:
    return fpr.stratify(rows)


def panel_driver_summary(rows: list[dict]) -> dict[str, Any]:
    feasible = [r for r in rows if r["label"] in fpr.FEASIBLE_LABELS]
    aeb = [r for r in rows if r["label"] == "aeb_feasible"]
    return {
        "n": len(rows),
        "success": sum(1 for r in rows if r["outcome"] == "success"),
        "collision": sum(1 for r in rows if r["outcome"] == "collision"),
        "offtrack": sum(1 for r in rows if r["outcome"] == "offtrack"),
        "speed_too_low": sum(1 for r in rows if r["outcome"] == "speed_too_low"),
        "feasible_n": len(feasible),
        "feasible_success": sum(1 for r in feasible if r["outcome"] == "success"),
        "aeb_feasible_n": len(aeb),
        "aeb_feasible_success": sum(1 for r in aeb if r["outcome"] == "success"),
        "stratified_outcomes": stratified(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows-csv", type=Path, default=DEFAULT_ROWS_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument(
        "--panels", default="feasible_only,fresh,old,holdout", help="comma list from: " + ",".join(PANEL_ORDER)
    )
    args = parser.parse_args()
    panels = [p.strip() for p in str(args.panels).split(",") if p.strip()]
    for panel in panels:
        if panel not in PANEL_ORDER:
            raise SystemExit(f"unknown panel {panel!r}")

    source = {
        "m3084_measurement_rows": read_csv_rows(fpr.DEFAULT_M3084_DIR / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(fpr.DEFAULT_M3012_DIR / "executable_workload_rows.csv"),
    }
    plan_rows = fpr.m3090.full_fresh_plan(source)
    if len(plan_rows) != 64:
        raise RuntimeError(f"expected 64 panel plan rows, got {len(plan_rows)}")
    payload = read_json(fpr.DEFAULT_M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }
    profile_cache: dict[tuple[str, str], dict] = {}

    # --- per-panel seed maps (fresh_panel_row_id -> seed) ---
    feasible_csv_rows = read_csv_rows(FEASIBLE_PANEL_CSV)
    feasible_seeds = {str(r["fresh_panel_row_id"]): int(r["eval_seed"]) for r in feasible_csv_rows}
    seed_maps: dict[str, dict[str, int]] = {}
    old_seeds: dict[str, int] = {}
    fresh_seeds: dict[str, int] = {}
    for plan in plan_rows:
        row_id = str(plan["fresh_panel_row_id"])
        row_number = int(row_id.rsplit("-", 1)[1])
        old_seed = fpr.seed_for_panel_row(row_number, fpr.OLD_SEED_BASE)
        if int(plan["eval_seed"]) != old_seed:
            raise RuntimeError(f"old panel seed mismatch on {row_id}")
        old_seeds[row_id] = old_seed
        fresh_seeds[row_id] = fpr.seed_for_panel_row(row_number, fpr.RETEST_SEED_BASE)
    seed_maps["old"] = old_seeds
    seed_maps["fresh"] = fresh_seeds
    seed_maps["feasible_only"] = feasible_seeds

    holdout_meta: dict[str, Any] = {}
    if "holdout" in panels:
        excluded = set(old_seeds.values()) | set(fresh_seeds.values()) | set(feasible_seeds.values())
        chosen = build_holdout_seeds(plan_rows, specs, profile_cache, excluded)
        seed_maps["holdout"] = {row_id: seed for row_id, (seed, _label, _att) in chosen.items()}
        holdout_meta = {
            "seed_base": HOLDOUT_SEED_BASE,
            "seed_stride": HOLDOUT_SEED_STRIDE,
            "excluded_seed_count": len(excluded),
            "scan_labels": dict(Counter(label for (_s, label, _a) in chosen.values())),
            "max_scan_attempts": max(att for (_s, _l, att) in chosen.values()),
        }
        print(f"[holdout] scan complete: labels={holdout_meta['scan_labels']}")

    drivers: list[tuple[str, str, Callable[[], Callable[[np.ndarray], np.ndarray]]]] = [
        ("v4", V4_DRIVER_ID, lambda: ActiveSafetyReflexDriver().act),
        ("v5", V5_DRIVER_ID, lambda: ActiveSafetyDriverV5Candidate().act),
    ]

    all_rows: list[dict] = []
    summary: dict[str, Any] = {
        "generated_at_utc": utc_timestamp(),
        "v4_driver_id": V4_DRIVER_ID,
        "v5_driver_id": V5_DRIVER_ID,
        "v5_policy_config_sha256": policy_config_fingerprint(V5_POLICY_CONFIG),
        "v5_governor_config": dict(V5_POLICY_CONFIG["governor"]),
        "margin_guard_tolerance": MARGIN_GUARD_TOLERANCE,
        "panels": {},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if holdout_meta:
        summary["holdout_scan"] = holdout_meta

    for panel in panels:
        seed_map = seed_maps[panel]
        panel_rows: dict[str, list[dict]] = {}
        for driver_name, driver_id, factory in drivers:
            rows: list[dict] = []
            for plan in plan_rows:
                row_id = str(plan["fresh_panel_row_id"])
                act_fn = factory()
                record = measure_row(
                    plan,
                    seed_map[row_id],
                    specs,
                    profile_cache,
                    panel=panel,
                    driver_name=driver_name,
                    driver_id=driver_id,
                    act_fn=act_fn,
                    row_number=len(rows) + 1,
                )
                rows.append(record)
            panel_rows[driver_name] = rows
            stats = panel_driver_summary(rows)
            print(
                f"[{panel}] {driver_name}: success={stats['success']}/{stats['n']} "
                f"collision={stats['collision']} offtrack={stats['offtrack']} "
                f"speed_too_low={stats['speed_too_low']} "
                f"feasible={stats['feasible_success']}/{stats['feasible_n']}"
            )
            all_rows.extend(rows)

        v4_rows = {r["fresh_panel_row_id"]: r for r in panel_rows["v4"]}
        v5_rows = {r["fresh_panel_row_id"]: r for r in panel_rows["v5"]}
        fixed = sorted(
            rid for rid in v4_rows if not v4_rows[rid]["success"] and v5_rows[rid]["success"]
        )
        regressed = sorted(
            rid for rid in v4_rows if v4_rows[rid]["success"] and not v5_rows[rid]["success"]
        )
        panel_summary: dict[str, Any] = {
            "v4": panel_driver_summary(panel_rows["v4"]),
            "v5": panel_driver_summary(panel_rows["v5"]),
            "rows_fixed_by_v5": fixed,
            "rows_regressed_by_v5": regressed,
        }
        if panel == "old":
            guard = []
            for rid in OLD_PANEL_GUARD_ROWS:
                v4_margin = float(v4_rows[rid]["min_clearance_margin"])
                v5_margin = float(v5_rows[rid]["min_clearance_margin"])
                delta = v5_margin - v4_margin
                guard.append(
                    {
                        "fresh_panel_row_id": rid,
                        "v4_outcome": v4_rows[rid]["outcome"],
                        "v5_outcome": v5_rows[rid]["outcome"],
                        "v4_min_clearance_margin": v4_margin,
                        "v5_min_clearance_margin": v5_margin,
                        "margin_delta": delta,
                        "guard_pass": bool(delta >= -MARGIN_GUARD_TOLERANCE),
                    }
                )
            panel_summary["infeasible_row_margin_guard"] = guard
            panel_summary["margin_guard_pass"] = all(g["guard_pass"] for g in guard)
            panel_summary["no_regression_pass"] = bool(
                panel_summary["v5"]["success"] >= 57 and not regressed and panel_summary["margin_guard_pass"]
            )
            # cross-check the same-run v4 measurement against the recorded M3105 outcomes
            if OLD_PANEL_LABELS_CSV.exists():
                recorded = {
                    str(r["fresh_panel_row_id"]): str(r["m3105_outcome"])
                    for r in read_csv_rows(OLD_PANEL_LABELS_CSV)
                }
                mismatches = [
                    rid
                    for rid, rec in recorded.items()
                    if rid in v4_rows and rec != v4_rows[rid]["outcome"]
                ]
                panel_summary["v4_reproduction_mismatches_vs_recorded"] = mismatches
        summary["panels"][panel] = panel_summary
        if fixed:
            print(f"[{panel}] fixed by v5: {fixed}")
        if regressed:
            print(f"[{panel}] REGRESSED by v5: {regressed}")

    args.rows_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(args.rows_csv, all_rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.summary_json, summary)
    print(f"rows_csv: {args.rows_csv}")
    print(f"summary_json: {args.summary_json}")


if __name__ == "__main__":
    main()
