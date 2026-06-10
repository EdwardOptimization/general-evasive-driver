"""Stratified feasibility-label report for the fixed M3082/M3084 64-row fresh panel.

Part A of the feasibility-audit stratified reporting route step:
1. Rebuild the generator feasibility label for each of the 64 panel rows by
   constructing the measurement environment through the exact same code path
   used by the M3088/M3090/M3095/M3105 measurement preflights
   (``profile_config_for_runtime`` -> ``env_config_for_executable_profile`` ->
   ``wrap_env_with_profile_mask(AutoDriftEnv(...))`` -> ``reset(seed=eval_seed)``)
   and reading ``env.unwrapped.obstacle_scenario.label``
   (``autodrift.scenarios.classify_obstacle_scenario``).
2. Join the labels with the per-row M3105 incumbent outcomes and emit a
   stratified table (per label: n / success / collision / offtrack /
   speed_too_low) plus a per-row CSV.

Deterministic: ``AutoDriftEnv.reset(seed=eval_seed)`` re-seeds the env RNG, so
labels are a pure function of (executable spec env_config, profile binding,
eval_seed). No training, no validation, no checkpoint is touched. CPU only.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/stratified_panel_report.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_M3084_DIR = REPO_ROOT / (
    "runs/m3084_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_"
    "direct_action_safety_reflex_fresh_robustness_measurement_preflight"
)
DEFAULT_M3105_DIR = REPO_ROOT / (
    "runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_"
    "hard_safety_direct_action_repair_full_fresh_measurement_preflight"
)
DEFAULT_M3012_DIR = REPO_ROOT / (
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_CSV = REPO_ROOT / "experiments/feasibility_audit/panel_feasibility_labels.csv"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "runs/feasibility_audit/stratified_panel_report_summary.json"

LABEL_ORDER = ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"]
OUTCOME_KEYS = ["success", "collision", "offtrack", "speed_too_low", "other"]

# Independent-audit expectation from docs/feasibility-takeover-2026-06-route-decision.md.
EXPECTED_LABEL_COUNTS = {"aeb_feasible": 55, "aes_feasible": 0, "drift_required": 3, "unavoidable": 6}


def build_panel_plan(m3084_dir: Path, m3012_dir: Path) -> list[dict]:
    """Rebuild the 64-row measurement plan exactly as m3090/m3095/m3105 did."""
    source = {
        "m3084_measurement_rows": read_csv_rows(m3084_dir / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(m3012_dir / "executable_workload_rows.csv"),
    }
    return m3090.full_fresh_plan(source)


def load_executable_specs(m3012_dir: Path) -> dict[tuple[str, str], dict]:
    payload = read_json(m3012_dir / "executable_source_specs.json")
    return {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }


def feasibility_label_for_plan_row(
    plan: dict,
    specs: dict[tuple[str, str], dict],
    profile_cache: dict[tuple[str, str], dict],
    *,
    seed: int | None = None,
) -> str:
    """Build the measurement env for one plan row, reset, and read the generator label."""
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
    try:
        env.reset(seed=int(plan["eval_seed"] if seed is None else seed))
        scenario = env.unwrapped.obstacle_scenario
        if scenario is None:
            raise RuntimeError("env has no obstacle scenario after reset")
        return str(scenario.label)
    finally:
        env.close()


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


def stratify(rows: list[dict], label_key: str, outcome_field: str) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for label in LABEL_ORDER:
        subset = [row for row in rows if row[label_key] == label]
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
    parser.add_argument("--m3105-dir", type=Path, default=DEFAULT_M3105_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--device", default="cpu", choices=["cpu"], help="cpu only; kept for CLI parity")
    args = parser.parse_args()

    plan_rows = build_panel_plan(args.m3084_dir, args.m3012_dir)
    if len(plan_rows) != 64:
        raise RuntimeError(f"expected 64 panel plan rows, got {len(plan_rows)}")
    specs = load_executable_specs(args.m3012_dir)
    m3105_rows = read_csv_rows(args.m3105_dir / "measurement_episode_rows.csv")
    m3105_by_panel_row = {str(row.get("fresh_panel_row_id", "")): row for row in m3105_rows}
    if len(m3105_by_panel_row) != 64:
        raise RuntimeError(f"expected 64 distinct m3105 panel rows, got {len(m3105_by_panel_row)}")

    profile_cache: dict[tuple[str, str], dict] = {}
    output_rows: list[dict] = []
    for plan in plan_rows:
        panel_row_id = str(plan["fresh_panel_row_id"])
        m3105_row = m3105_by_panel_row[panel_row_id]
        if int(m3105_row["eval_seed"]) != int(plan["eval_seed"]):
            raise RuntimeError(f"eval_seed mismatch on {panel_row_id}")
        label = feasibility_label_for_plan_row(plan, specs, profile_cache)
        output_rows.append(
            {
                "fresh_panel_row_id": panel_row_id,
                "eval_seed": int(plan["eval_seed"]),
                "spec": str(plan["executable_source_spec_id"]),
                "label": label,
                "m3105_outcome": outcome_key(m3105_row),
                "m3105_outcome_bucket": str(m3105_row.get("outcome_bucket", "")),
                "m3105_termination_reason": str(m3105_row.get("termination_reason", "")),
                "binding_role": str(plan.get("binding_role", "")),
                "axis_id": str(plan.get("axis_id", "")),
                "task_family": str(plan.get("task_family", "")),
            }
        )
        print(f"{panel_row_id} seed={plan['eval_seed']} label={label} m3105={output_rows[-1]['m3105_outcome']}")

    label_counts = Counter(row["label"] for row in output_rows)
    table = stratify(output_rows, "label", "m3105_outcome")
    expectation_match = {
        label: label_counts.get(label, 0) == expected for label, expected in EXPECTED_LABEL_COUNTS.items()
    }

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(
        args.output_csv,
        output_rows,
        fieldnames=[
            "fresh_panel_row_id",
            "eval_seed",
            "spec",
            "label",
            "m3105_outcome",
            "m3105_outcome_bucket",
            "m3105_termination_reason",
            "binding_role",
            "axis_id",
            "task_family",
        ],
    )
    summary = {
        "generated_at_utc": utc_timestamp(),
        "panel_row_count": len(output_rows),
        "label_counts": {label: label_counts.get(label, 0) for label in LABEL_ORDER},
        "expected_label_counts": EXPECTED_LABEL_COUNTS,
        "expected_label_counts_match": expectation_match,
        "stratified_m3105_outcomes": table,
        "per_row_csv": str(args.output_csv),
        "claim_boundary": (
            "Feasibility-audit stratified reporting only; generator labels and recorded M3105 "
            "outcomes are joined and counted. No driver-performance, repair-success, robustness, "
            "validation, ranking, promotion, high-fidelity, paper, or self-ID claim is made."
        ),
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.summary_json, summary)

    print()
    print("label_counts:", dict(label_counts))
    print("expected_match:", expectation_match)
    print(render_table(table))
    print(f"rows_csv: {args.output_csv}")
    print(f"summary_json: {args.summary_json}")


if __name__ == "__main__":
    main()
