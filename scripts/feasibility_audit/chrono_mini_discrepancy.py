"""A3 HF4-mini discrepancy measurement: current-sim vs Chrono backend, 16+7 rows.

Row selection from the fixed M3082/M3084 64-row panel
(``experiments/feasibility_audit/panel_feasibility_labels.csv``):
- one recorded-success row per executable source spec (16 rows, lowest panel
  row number per spec), and
- all 7 recorded residual-failure rows (5 collisions + 2 offtracks; these are
  the unavoidable/drift_required rows of the route-decision audit).

For every selected row the same M3105 incumbent ``ActiveSafetyReflexDriver``
is run closed-loop twice on the *same* reconstructed scenario:
1. current-sim: the exact M3088/M3090 measurement env rebuild path +
   ``run_episode_with_policy`` (reusing ``fresh_panel_retest`` helpers), and
2. Chrono: ``ChronoVehicleBackend`` in the pinned chrono conda env via the
   JSONL worker. Scenario elements (vehicle hidden params, initial state,
   obstacle position/half-width, warmup gate, perception reveal step,
   friction-step step index and replacement mu) are read out of the
   current-sim env after ``reset(seed)`` and copied to the Chrono side, so
   both backends solve the same task instance. The friction-step replacement
   mu is the only post-reset RNG draw of the env; it is action-independent
   and is consumed from a sacrificial reset to pre-compute it.

Deterministic: fixed seeds (old-panel 401500-base), deterministic driver and
backend; the first two Chrono rows are re-run and compared exactly.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/chrono_mini_discrepancy.py

Outputs:
    experiments/feasibility_audit/chrono_mini_discrepancy.csv
    runs/feasibility_audit/chrono_mini_discrepancy_summary.json
    runs/feasibility_audit/chrono_mini_scenarios/*.json
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fresh_panel_retest as fpr  # noqa: E402  (verified deterministic helpers)
from autodrift.active_safety_reflex_driver import DRIVER_ID, ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.chrono_vehicle_backend import BACKEND_ID, KNOWN_DIFFERENCES, scenario_from_env  # noqa: E402
from autodrift.controller_family_full_rollout_execution import read_csv_rows  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_full_fresh_runtime_measurement_preflight as m3090  # noqa: E402

LABELS_CSV = REPO_ROOT / "experiments/feasibility_audit/panel_feasibility_labels.csv"
ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/chrono_mini_discrepancy.csv"
SUMMARY_JSON = REPO_ROOT / "runs/feasibility_audit/chrono_mini_discrepancy_summary.json"
SCENARIO_DIR = REPO_ROOT / "runs/feasibility_audit/chrono_mini_scenarios"
STDERR_LOG = REPO_ROOT / "runs/feasibility_audit/chrono_mini_worker_stderr.log"

CLAIM_BOUNDARY = (
    "HF backend mini discrepancy measurement only: per-row outcome comparison of the same "
    "incumbent driver on the same reconstructed scenarios under two dynamics backends. No "
    "driver-performance verdict, validation, ranking, promotion, repair-success, "
    "fidelity-sufficiency, or full HF4 claim is made."
)


def select_rows(label_rows: list[dict]) -> list[dict]:
    by_number = sorted(label_rows, key=lambda row: int(str(row["fresh_panel_row_id"]).rsplit("-", 1)[1]))
    failures = [row for row in by_number if str(row["m3105_outcome"]) != "success"]
    if len(failures) != 7:
        raise RuntimeError(f"expected 7 recorded residual-failure rows, found {len(failures)}")
    selected: list[dict] = []
    seen_specs: set[str] = set()
    for row in by_number:
        spec = str(row["spec"])
        if str(row["m3105_outcome"]) == "success" and spec not in seen_specs:
            seen_specs.add(spec)
            selected.append({**row, "row_kind": "spec_success"})
    if len(seen_specs) != 16:
        raise RuntimeError(f"expected success rows for 16 specs, found {len(seen_specs)}")
    selected.extend({**row, "row_kind": "residual_failure"} for row in failures)
    return selected


def export_scenario(plan: dict, seed: int, specs: dict, profile_cache: dict) -> dict:
    env = fpr.build_env_for_plan_row(plan, specs, profile_cache)
    try:
        env.reset(seed=int(seed))
        e = env.unwrapped
        new_mu = None
        if e.friction_step_at is not None:
            # the friction-step replacement mu is the next (and only) post-reset
            # env RNG draw; consume it here on this sacrificial reset
            new_mu = float(e.rng.uniform(*e.config.friction_step.mu_range))
        scenario = scenario_from_env(env, friction_step_new_mu=new_mu)
    finally:
        env.close()
    scenario["scenario_id"] = str(plan["fresh_panel_row_id"])
    return scenario


def run_chrono_episode(client: ChronoWorkerClient, driver: ActiveSafetyReflexDriver, scenario: dict) -> dict:
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]))
    spinup = reset_reply["info"].get("spinup", {})
    speeds: list[float] = []
    signature = float(np.sum(obs, dtype=np.float64))
    terminated = False
    truncated = False
    info: dict = dict(reset_reply["info"])
    steps = 0
    while not (terminated or truncated) and steps < int(scenario["max_steps"]) + 5:
        action = driver.act(obs)
        obs, terminated, truncated, status, info = client.step(action)
        signature += float(np.sum(obs, dtype=np.float64))
        speeds.append(float(info["speed"]))
        steps += 1
    collision = bool(info.get("collision", False))
    completed = bool(info.get("obstacle_completed", False))
    reason = str(info.get("termination_reason", ""))
    if completed and not collision:
        outcome = "success"
    elif reason == "obstacle_collision" or collision:
        outcome = "collision"
    elif reason == "off_track":
        outcome = "offtrack"
    elif reason == "speed_too_low":
        outcome = "speed_too_low"
    else:
        outcome = "other"
    margin = info.get("min_clearance_margin")
    return {
        "outcome": outcome,
        "steps": steps,
        "terminated": terminated,
        "truncated": truncated,
        "termination_reason": reason,
        "obstacle_completed": completed,
        "collision": collision,
        "min_clearance_margin": float(margin) if isinstance(margin, (int, float)) else float("nan"),
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
        "spinup_speed_gap": float(spinup.get("spinup_speed_gap", float("nan"))),
        "trace_signature": signature,
    }


def main() -> None:
    label_rows = read_csv_rows(LABELS_CSV)
    if len(label_rows) != 64:
        raise RuntimeError(f"expected 64 panel label rows, got {len(label_rows)}")
    selected = select_rows(label_rows)

    source = {
        "m3084_measurement_rows": read_csv_rows(fpr.DEFAULT_M3084_DIR / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(fpr.DEFAULT_M3012_DIR / "executable_workload_rows.csv"),
    }
    plan_rows = m3090.full_fresh_plan(source)
    plans = {str(plan["fresh_panel_row_id"]): plan for plan in plan_rows}
    payload = read_json(fpr.DEFAULT_M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }
    profile_cache: dict = {}

    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    client = ChronoWorkerClient(stderr_log=STDERR_LOG)
    driver = ActiveSafetyReflexDriver()
    out_rows: list[dict] = []
    chrono_results: list[dict] = []
    try:
        for index, row in enumerate(selected, start=1):
            row_id = str(row["fresh_panel_row_id"])
            plan = plans[row_id]
            seed = int(plan["eval_seed"])
            if seed != int(row["eval_seed"]):
                raise RuntimeError(f"seed mismatch on {row_id}")

            scenario = export_scenario(plan, seed, specs, profile_cache)
            write_json(SCENARIO_DIR / f"{row_id}.json", scenario)

            current = fpr.measure_row(plan, seed, specs, profile_cache, "fa-chrono-mini-current", index)
            chrono = run_chrono_episode(client, driver, scenario)
            chrono_results.append(chrono)

            record = {
                "episode_id": f"fa-chrono-mini-{index:04d}",
                "fresh_panel_row_id": row_id,
                "eval_seed": seed,
                "spec": str(row["spec"]),
                "label": str(row["label"]),
                "row_kind": str(row["row_kind"]),
                "binding_role": str(row["binding_role"]),
                "axis_id": str(row["axis_id"]),
                "task_family": str(row["task_family"]),
                "runtime_driver_id": DRIVER_ID,
                "recorded_m3105_outcome": str(row["m3105_outcome"]),
                "current_sim_outcome": str(current["outcome"]),
                "current_sim_matches_recorded": str(current["outcome"]) == str(row["m3105_outcome"]),
                "current_sim_steps": int(current["steps"]),
                "current_sim_termination_reason": str(current["termination_reason"]),
                "current_sim_min_clearance_margin": current["min_clearance_margin"],
                "current_sim_speed_mean": current["speed_mean"],
                "chrono_outcome": chrono["outcome"],
                "chrono_steps": chrono["steps"],
                "chrono_termination_reason": chrono["termination_reason"],
                "chrono_min_clearance_margin": chrono["min_clearance_margin"],
                "chrono_speed_mean": chrono["speed_mean"],
                "chrono_spinup_speed_gap": chrono["spinup_speed_gap"],
                "outcome_match": chrono["outcome"] == str(current["outcome"]),
                "claim_boundary": CLAIM_BOUNDARY,
            }
            out_rows.append(record)
            print(
                f"{row_id} [{record['row_kind']}] label={record['label']} "
                f"current={record['current_sim_outcome']} chrono={record['chrono_outcome']} "
                f"match={record['outcome_match']} chrono_steps={record['chrono_steps']}"
            )

        # determinism: re-run the first two chrono rows and compare exactly
        determinism_identical = True
        for index in range(2):
            row_id = str(selected[index]["fresh_panel_row_id"])
            scenario = read_json(SCENARIO_DIR / f"{row_id}.json")
            repeat = run_chrono_episode(client, driver, scenario)
            same = (
                repeat["outcome"] == chrono_results[index]["outcome"]
                and repeat["steps"] == chrono_results[index]["steps"]
                and repeat["trace_signature"] == chrono_results[index]["trace_signature"]
            )
            determinism_identical = determinism_identical and same
            print(f"determinism repeat {row_id}: identical={same}")
    finally:
        client.close()

    success_rows = [row for row in out_rows if row["row_kind"] == "spec_success"]
    failure_rows = [row for row in out_rows if row["row_kind"] == "residual_failure"]
    transitions = Counter(
        (str(row["current_sim_outcome"]), str(row["chrono_outcome"])) for row in out_rows
    )
    summary = {
        "milestone": "feasibility-route-hf-backend-a3-chrono-mini-discrepancy",
        "generated_at_utc": utc_timestamp(),
        "backend_id": BACKEND_ID,
        "runtime_driver_id": DRIVER_ID,
        "row_count": len(out_rows),
        "spec_success_rows": len(success_rows),
        "residual_failure_rows": len(failure_rows),
        "current_sim_reproduces_recorded_outcomes": all(r["current_sim_matches_recorded"] for r in out_rows),
        "chrono_determinism_repeat_identical": bool(determinism_identical),
        "success_rows_outcome_match": sum(1 for r in success_rows if r["outcome_match"]),
        "success_rows_chrono_outcomes": dict(Counter(str(r["chrono_outcome"]) for r in success_rows)),
        "failure_rows_outcome_match": sum(1 for r in failure_rows if r["outcome_match"]),
        "failure_rows_chrono_outcomes": dict(Counter(str(r["chrono_outcome"]) for r in failure_rows)),
        "outcome_transitions_current_to_chrono": {f"{a}->{b}": n for (a, b), n in sorted(transitions.items())},
        "rows_csv": str(ROWS_CSV),
        "scenario_dir": str(SCENARIO_DIR),
        "known_differences": list(KNOWN_DIFFERENCES),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    ROWS_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(ROWS_CSV, out_rows)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json(SUMMARY_JSON, summary)
    print()
    print("success rows (16): chrono outcomes:", summary["success_rows_chrono_outcomes"])
    print("failure rows (7): chrono outcomes:", summary["failure_rows_chrono_outcomes"])
    print("transitions:", summary["outcome_transitions_current_to_chrono"])
    print(f"rows_csv={ROWS_CSV}")
    print(f"summary={SUMMARY_JSON}")


if __name__ == "__main__":
    main()
