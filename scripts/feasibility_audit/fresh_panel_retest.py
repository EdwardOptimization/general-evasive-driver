"""Fresh-seed retest of the M3105 incumbent on a disjoint 64-row panel.

Part B of the feasibility-audit stratified reporting route step. Tests whether
the incumbent's 100% success rate on feasible (aeb_feasible) rows is a property
of the controller or an artifact of the 64 fixed M3082 seeds (401500-401871).

Panel structure is identical to M3082
(``engineering_controller_active_safety_driver_v1_..._fresh_robustness_panel_
materialization_preflight.build_fresh_panel_rows``): the same 16 executable
source specs x profile bindings in the same row order (the per-row workload
binding is taken verbatim from the M3084 measurement rows via
``m3090.full_fresh_plan``), with the eval seed formula

    eval_seed = SEED_BASE + axis_index * 100 + pair_index * 10 + role_index

re-instantiated at a new base ``RETEST_SEED_BASE = 501500`` (old base 401500;
the two seed sets 401500-401871 and 501500-501871 are disjoint, asserted at
runtime).

For every row the script:
1. rebuilds the measurement env through the exact same code path as
   M3088/M3090/M3095/M3105 (``profile_config_for_runtime`` ->
   ``env_config_for_executable_profile`` -> ``wrap_env_with_profile_mask`` ->
   ``AutoDriftEnv``),
2. reads the generator feasibility label after ``reset(seed=retest_seed)``
   (``autodrift.scenarios.classify_obstacle_scenario`` via
   ``env.obstacle_scenario.label``),
3. runs the incumbent ``ActiveSafetyReflexDriver`` (M3105 v4 policy config)
   closed-loop with the shared ``run_episode_with_policy`` rollout loop
   (which re-resets with the same seed; resets are deterministic).

Optionally (--feasible-only-panel, Part C) it additionally builds a
"deployment-criterion" panel: for each of the 64 row bindings it scans
deterministic candidate seeds (601500 + offset + k*1000, k = 0, 1, ...) until
the generator label is aeb_feasible or aes_feasible, then measures the
incumbent on those 64 feasible rows.

Deterministic, CPU-only, no file outside experiments/feasibility_audit and
runs/feasibility_audit is written.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/fresh_panel_retest.py \
        [--feasible-only-panel]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.active_safety_reflex_driver import DRIVER_ID, ActiveSafetyReflexDriver
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
from autodrift.evaluate import run_episode_with_policy
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_M3084_DIR = REPO_ROOT / (
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3012_DIR = REPO_ROOT / (
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_PANEL_LABELS_CSV = REPO_ROOT / "experiments/feasibility_audit/panel_feasibility_labels.csv"
DEFAULT_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/fresh_panel_retest_rows.csv"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "experiments/feasibility_audit/fresh_panel_retest_summary.json"
DEFAULT_FEASIBLE_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/feasible_only_panel_rows.csv"

OLD_SEED_BASE = 401500  # M3082 FRESH_SEED_BASE
RETEST_SEED_BASE = 501500  # old base + 100000
FEASIBLE_PANEL_SEED_BASE = 601500  # Part C deterministic scan base
FEASIBLE_PANEL_SEED_STRIDE = 1000
FEASIBLE_LABELS = {"aeb_feasible", "aes_feasible"}
LABEL_ORDER = ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"]
OUTCOME_KEYS = ["success", "collision", "offtrack", "speed_too_low", "other"]

CLAIM_BOUNDARY = (
    "Feasibility-audit fresh-seed retest measurement only; the M3105 incumbent reflex driver is "
    "executed closed-loop on a disjoint fresh-seed panel and per-label outcome counts are "
    "recorded. No driver-performance verdict, repair-success, robustness-result, validation, "
    "ranking, winner selection, checkpoint mutation/promotion, high-fidelity, paper, or self-ID "
    "claim is made."
)


class IncumbentReflexMeasurementPolicy:
    """Adapter exposing the deployable ActiveSafetyReflexDriver to the rollout loop."""

    def __init__(self) -> None:
        self.driver = ActiveSafetyReflexDriver()
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0

    def reset(self) -> None:
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        action = self.driver.act(observation)
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(action))))
        self.raw_action_l2_sum += float(np.linalg.norm(action))
        return action


def panel_indices(panel_row_number: int) -> tuple[int, int, int]:
    index = panel_row_number - 1
    return index // 16, (index % 16) // 2, index % 2


def seed_for_panel_row(panel_row_number: int, base: int) -> int:
    axis_index, pair_index, role_index = panel_indices(panel_row_number)
    return base + axis_index * 100 + pair_index * 10 + role_index


def build_env_for_plan_row(
    plan: dict,
    specs: dict[tuple[str, str], dict],
    profile_cache: dict[tuple[str, str], dict],
):
    executable_spec = specs[(str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))]
    profile_name = str(plan["base_profile_name"])
    config_path = str(plan["config_path"])
    cache_key = (profile_name, config_path)
    if cache_key not in profile_cache:
        profile_cache[cache_key] = m3088.m3075.profile_config_for_runtime(
            read_json(config_path), profile_name=profile_name
        )
    profile_config = profile_cache[cache_key]
    env_config = m3088.env_config_for_executable_profile(
        executable_spec=executable_spec, profile_config=profile_config
    )
    env = m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)
    if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
        env.close()
        raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
    if int(env.action_space.shape[0]) != ACTION_DIM:
        env.close()
        raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
    return env


def label_for_seed(env, seed: int) -> str:
    env.reset(seed=int(seed))
    scenario = env.unwrapped.obstacle_scenario
    if scenario is None:
        raise RuntimeError("env has no obstacle scenario after reset")
    return str(scenario.label)


def outcome_key(row: dict) -> str:
    bucket = str(row.get("outcome_bucket", ""))
    reason = str(row.get("termination_reason", ""))
    if bucket == "success_obstacle_pass":
        return "success"
    if bucket == "collision_failure" or reason == "obstacle_collision":
        return "collision"
    if reason == "off_track":
        return "offtrack"
    if reason == "speed_too_low":
        return "speed_too_low"
    return "other"


def measure_row(plan: dict, seed: int, specs: dict, profile_cache: dict, episode_prefix: str, row_number: int) -> dict:
    env = build_env_for_plan_row(plan, specs, profile_cache)
    try:
        label = label_for_seed(env, seed)
        policy = IncumbentReflexMeasurementPolicy()
        episode = run_episode_with_policy(
            env, policy, "active_safety_reflex_driver_m3105_incumbent_fresh_retest", int(seed)
        )
    finally:
        env.close()
    success = bool(episode.get("obstacle_completed", False)) and not bool(episode.get("collision", False))
    record = {
        "retest_episode_id": f"{episode_prefix}-{row_number:04d}",
        "fresh_panel_row_id": str(plan["fresh_panel_row_id"]),
        "source_measurement_episode_id": str(plan.get("source_measurement_episode_id", "")),
        "eval_seed": int(seed),
        "old_panel_eval_seed": int(plan["eval_seed"]),
        "spec": str(plan["executable_source_spec_id"]),
        "executable_workload_id": str(plan.get("executable_workload_id", "")),
        "base_profile_name": str(plan["base_profile_name"]),
        "binding_role": str(plan.get("binding_role", "")),
        "axis_id": str(plan.get("axis_id", "")),
        "task_family": str(plan.get("task_family", "")),
        "label": label,
        "runtime_driver_id": DRIVER_ID,
        "steps": int(episode.get("steps", 0)),
        "success": success,
        "collision": bool(episode.get("collision", False)),
        "obstacle_completed": bool(episode.get("obstacle_completed", False)),
        "termination_reason": str(episode.get("termination_reason", "")),
        "outcome_bucket": str(episode.get("outcome_bucket", "")),
        "min_clearance_margin": episode.get("min_clearance_margin", ""),
        "return": episode.get("return", ""),
        "speed_mean": episode.get("speed_mean", ""),
        "raw_action_abs_max": float(0.0),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    record["outcome"] = outcome_key(record)
    return record


def stratify(rows: list[dict], outcome_field: str = "outcome") -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for label in LABEL_ORDER:
        subset = [row for row in rows if row["label"] == label]
        if not subset:
            continue
        counts = Counter(row[outcome_field] for row in subset)
        table[label] = {"n": len(subset), **{key: counts.get(key, 0) for key in OUTCOME_KEYS}}
    return table


def render_table(table: dict[str, dict[str, int]]) -> str:
    lines = ["label                n  success  collision  offtrack  speed_too_low"]
    for label, counts in table.items():
        lines.append(
            f"{label:<18} {counts['n']:>4}  {counts['success']:>7}  {counts['collision']:>9}  "
            f"{counts['offtrack']:>8}  {counts['speed_too_low']:>13}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3084-dir", type=Path, default=DEFAULT_M3084_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--panel-labels-csv", type=Path, default=DEFAULT_PANEL_LABELS_CSV)
    parser.add_argument("--rows-csv", type=Path, default=DEFAULT_ROWS_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--feasible-rows-csv", type=Path, default=DEFAULT_FEASIBLE_ROWS_CSV)
    parser.add_argument("--feasible-only-panel", action="store_true", help="also run the Part C feasible-only panel")
    parser.add_argument("--device", default="cpu", choices=["cpu"], help="cpu only; kept for CLI parity")
    args = parser.parse_args()

    source = {
        "m3084_measurement_rows": read_csv_rows(args.m3084_dir / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(args.m3012_dir / "executable_workload_rows.csv"),
    }
    plan_rows = m3090.full_fresh_plan(source)
    if len(plan_rows) != 64:
        raise RuntimeError(f"expected 64 panel plan rows, got {len(plan_rows)}")
    payload = read_json(args.m3012_dir / "executable_source_specs.json")
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }

    # Seed bookkeeping: old panel seeds must follow the M3082 formula at OLD_SEED_BASE,
    # retest seeds are the same formula at RETEST_SEED_BASE, with zero overlap.
    old_seeds: set[int] = set()
    retest_seeds: list[int] = []
    for plan in plan_rows:
        row_number = int(str(plan["fresh_panel_row_id"]).rsplit("-", 1)[1])
        expected_old_seed = seed_for_panel_row(row_number, OLD_SEED_BASE)
        if int(plan["eval_seed"]) != expected_old_seed:
            raise RuntimeError(
                f"old panel seed mismatch on {plan['fresh_panel_row_id']}: "
                f"{plan['eval_seed']} != {expected_old_seed}"
            )
        old_seeds.add(expected_old_seed)
        retest_seeds.append(seed_for_panel_row(row_number, RETEST_SEED_BASE))
    if len(set(retest_seeds)) != 64:
        raise RuntimeError("retest seeds are not unique")
    overlap = sorted(set(retest_seeds) & old_seeds)
    if overlap:
        raise RuntimeError(f"retest seeds overlap the old panel: {overlap}")

    # Old-panel per-row labels + outcomes (Part A artifact) for the comparison table.
    old_label_rows = read_csv_rows(args.panel_labels_csv) if args.panel_labels_csv.exists() else []
    old_table = stratify(
        [{"label": row["label"], "outcome": row["m3105_outcome"]} for row in old_label_rows]
    ) if old_label_rows else {}

    profile_cache: dict[tuple[str, str], dict] = {}
    retest_rows: list[dict] = []
    for plan, seed in zip(plan_rows, retest_seeds):
        record = measure_row(plan, seed, specs, profile_cache, "fa-fresh-retest-episode", len(retest_rows) + 1)
        retest_rows.append(record)
        print(
            f"{record['fresh_panel_row_id']} seed={seed} label={record['label']} "
            f"outcome={record['outcome']} steps={record['steps']}"
        )

    retest_table = stratify(retest_rows)
    label_counts = Counter(row["label"] for row in retest_rows)
    feasible_rows = [row for row in retest_rows if row["label"] == "aeb_feasible"]
    feasible_success = sum(1 for row in feasible_rows if row["outcome"] == "success")
    overall_success = sum(1 for row in retest_rows if row["outcome"] == "success")

    args.rows_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(args.rows_csv, retest_rows)

    summary: dict[str, Any] = {
        "generated_at_utc": utc_timestamp(),
        "runtime_driver_id": DRIVER_ID,
        "panel_row_count": len(retest_rows),
        "old_seed_base": OLD_SEED_BASE,
        "retest_seed_base": RETEST_SEED_BASE,
        "seed_overlap_with_old_panel": 0,
        "retest_seed_min": min(retest_seeds),
        "retest_seed_max": max(retest_seeds),
        "label_counts": {label: label_counts.get(label, 0) for label in LABEL_ORDER},
        "overall": {
            "n": len(retest_rows),
            "success": overall_success,
            "success_rate": overall_success / len(retest_rows),
        },
        "aeb_feasible": {
            "n": len(feasible_rows),
            "success": feasible_success,
            "success_rate": feasible_success / len(feasible_rows) if feasible_rows else None,
        },
        "stratified_retest_outcomes": retest_table,
        "stratified_old_panel_m3105_outcomes": old_table,
        "rows_csv": str(args.rows_csv),
        "claim_boundary": CLAIM_BOUNDARY,
    }

    if args.feasible_only_panel:
        feasible_panel_rows: list[dict] = []
        used_seeds: set[int] = set(retest_seeds) | old_seeds
        for plan in plan_rows:
            row_number = int(str(plan["fresh_panel_row_id"]).rsplit("-", 1)[1])
            offset = seed_for_panel_row(row_number, 0)
            env = build_env_for_plan_row(plan, specs, profile_cache)
            chosen_seed = None
            chosen_label = None
            attempts = 0
            try:
                for k in range(0, 64):
                    candidate = FEASIBLE_PANEL_SEED_BASE + offset + k * FEASIBLE_PANEL_SEED_STRIDE
                    attempts += 1
                    label = label_for_seed(env, candidate)
                    if label in FEASIBLE_LABELS and candidate not in used_seeds:
                        chosen_seed = candidate
                        chosen_label = label
                        break
            finally:
                env.close()
            if chosen_seed is None:
                raise RuntimeError(f"no feasible seed found for {plan['fresh_panel_row_id']}")
            used_seeds.add(chosen_seed)
            record = measure_row(
                plan, chosen_seed, specs, profile_cache, "fa-feasible-panel-episode", len(feasible_panel_rows) + 1
            )
            if record["label"] != chosen_label:
                raise RuntimeError(f"label changed between scan and measurement on {plan['fresh_panel_row_id']}")
            record["seed_scan_attempts"] = attempts
            feasible_panel_rows.append(record)
            print(
                f"[feasible-only] {record['fresh_panel_row_id']} seed={chosen_seed} "
                f"label={record['label']} outcome={record['outcome']} attempts={attempts}"
            )
        write_csv_rows(args.feasible_rows_csv, feasible_panel_rows)
        feasible_panel_success = sum(1 for row in feasible_panel_rows if row["outcome"] == "success")
        summary["feasible_only_panel"] = {
            "seed_base": FEASIBLE_PANEL_SEED_BASE,
            "seed_stride": FEASIBLE_PANEL_SEED_STRIDE,
            "n": len(feasible_panel_rows),
            "label_counts": dict(Counter(row["label"] for row in feasible_panel_rows)),
            "success": feasible_panel_success,
            "success_rate": feasible_panel_success / len(feasible_panel_rows),
            "stratified_outcomes": stratify(feasible_panel_rows),
            "rows_csv": str(args.feasible_rows_csv),
        }

    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.summary_json, summary)

    print()
    print("retest label_counts:", {label: label_counts.get(label, 0) for label in LABEL_ORDER})
    print("retest stratified outcomes:")
    print(render_table(retest_table))
    if old_table:
        print("old panel (M3105) stratified outcomes:")
        print(render_table(old_table))
    if "feasible_only_panel" in summary:
        print("feasible-only panel stratified outcomes:")
        print(render_table(summary["feasible_only_panel"]["stratified_outcomes"]))
        print(
            "feasible-only success:",
            f"{summary['feasible_only_panel']['success']}/{summary['feasible_only_panel']['n']}",
        )
    print(f"aeb_feasible retest success: {feasible_success}/{len(feasible_rows)}")
    print(f"overall retest success: {overall_success}/{len(retest_rows)}")
    print(f"rows_csv: {args.rows_csv}")
    print(f"summary_json: {args.summary_json}")


if __name__ == "__main__":
    main()
