"""Full HF4 discrepancy measurement: current-sim vs Chrono backend, 3 x 64-row panels.

Extends ``chrono_mini_discrepancy.py`` (23-row mini, 23/23 agreement) to the
full three-panel HF4 sweep. Panels (same 16 spec x profile-binding structure
and row order as M3082/M3084, env rebuilt through the exact
``fresh_panel_retest.py`` recipe):

1. ``old``: the fixed M3082/M3084 panel, seed base 401500, bindings/labels
   from ``experiments/feasibility_audit/panel_feasibility_labels.csv``;
2. ``fresh``: fresh-seed retest panel, seed base 501500, seeds verified
   against ``experiments/feasibility_audit/fresh_panel_retest_rows.csv``;
3. ``feasible_only``: deployment-criterion panel, seed base 601500, seeds
   taken verbatim from
   ``experiments/feasibility_audit/feasible_only_panel_rows.csv``.

Drivers:
- v4 incumbent (public ``ActiveSafetyReflexDriver``, untouched) on all
  3 x 64 = 192 rows;
- v5 candidate (``ActiveSafetyDriverV5Candidate``) on the feasible_only
  panel (64 rows).

For every (panel, driver, row) the same driver is run closed-loop twice on
the *same* reconstructed scenario:
1. current-sim: exact M3088/M3090 env rebuild path + run_episode_with_policy;
2. Chrono: ``ChronoVehicleBackend`` in the pinned chrono conda env via the
   JSONL worker. Scenario elements (vehicle hidden params, initial state,
   obstacle world position/half-width, warmup gate, perception reveal step,
   friction-step index and replacement mu) are exported from the current-sim
   env after ``reset(seed)`` via ``scenario_from_env``; the friction-step
   replacement mu (the env's only post-reset RNG draw) is pre-consumed on a
   sacrificial reset exactly as in the mini script.

Long-run mechanics: every completed row is appended to the rows CSV
immediately (crash-safe), ``--resume`` skips already-recorded
(panel, driver, row) keys, the chrono worker is restarted every
``--restart-every`` episodes to bound subprocess memory, and after the sweep
two designated rows are re-run and compared bitwise (trace signature).

Deterministic: fixed seeds, deterministic driver and both backends.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/chrono_hf4_full_discrepancy.py [--resume]

Outputs:
    experiments/feasibility_audit/chrono_hf4_full_rows.csv
    runs/feasibility_audit/chrono_hf4_full_summary.json
    runs/feasibility_audit/chrono_hf4_scenarios/*.json
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fresh_panel_retest as fpr  # noqa: E402  (verified deterministic helpers)
from autodrift.active_safety_driver_v5_curvature_speed_governor_candidate import (  # noqa: E402
    DRIVER_ID as V5_DRIVER_ID,
    ActiveSafetyDriverV5Candidate,
)
from autodrift.active_safety_reflex_driver import (  # noqa: E402
    DRIVER_ID as V4_DRIVER_ID,
    ActiveSafetyReflexDriver,
)
from autodrift.artifacts import read_json, utc_timestamp, write_json  # noqa: E402
from autodrift.chrono_vehicle_backend import BACKEND_ID, KNOWN_DIFFERENCES, scenario_from_env  # noqa: E402
from autodrift.controller_family_full_rollout_execution import read_csv_rows  # noqa: E402
from autodrift.evaluate import run_episode_with_policy  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/chrono_hf4_full_rows.csv"
SUMMARY_JSON = REPO_ROOT / "runs/feasibility_audit/chrono_hf4_full_summary.json"
SCENARIO_DIR = REPO_ROOT / "runs/feasibility_audit/chrono_hf4_scenarios"
STDERR_LOG = REPO_ROOT / "runs/feasibility_audit/chrono_hf4_worker_stderr.log"
OLD_LABELS_CSV = REPO_ROOT / "experiments/feasibility_audit/panel_feasibility_labels.csv"
FRESH_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/fresh_panel_retest_rows.csv"
FEASIBLE_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/feasible_only_panel_rows.csv"
V5VAL_ROWS_CSV = REPO_ROOT / "experiments/feasibility_audit/v5_panel_validation_rows.csv"

PANEL_ORDER = ["old", "fresh", "feasible_only"]
DEFAULT_UNITS = "old:v4,fresh:v4,feasible_only:v4,feasible_only:v5"
LABEL_ORDER = ["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"]

CLAIM_BOUNDARY = (
    "HF backend full-panel discrepancy measurement only: per-row outcome comparison of the same "
    "driver on the same reconstructed scenarios under two dynamics backends (current-sim vs "
    "Chrono Sedan/TMeasy). The v5 driver remains a candidate; the deployable "
    "ActiveSafetyReflexDriver is unchanged. No driver-performance verdict, validation, ranking, "
    "promotion, repair-success, fidelity-sufficiency, paper, or self-ID claim is made."
)

FIELDNAMES = [
    "episode_id",
    "panel",
    "driver",
    "runtime_driver_id",
    "fresh_panel_row_id",
    "eval_seed",
    "spec",
    "base_profile_name",
    "binding_role",
    "axis_id",
    "task_family",
    "label",
    "recorded_outcome",
    "current_sim_outcome",
    "current_sim_matches_recorded",
    "current_sim_steps",
    "current_sim_termination_reason",
    "current_sim_min_clearance_margin",
    "current_sim_speed_mean",
    "chrono_outcome",
    "chrono_steps",
    "chrono_termination_reason",
    "chrono_min_clearance_margin",
    "chrono_speed_mean",
    "chrono_spinup_speed_gap",
    "chrono_trace_signature",
    "outcome_match",
    "margin_delta_chrono_minus_current",
    "steps_delta_chrono_minus_current",
    "claim_boundary",
]


class MeasurementPolicy:
    """Adapter exposing an obs72->action3 driver to the shared rollout loop."""

    def __init__(self, act_fn: Callable[[np.ndarray], np.ndarray]) -> None:
        self._act_fn = act_fn

    def reset(self) -> None:
        pass

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        return self._act_fn(np.asarray(observation, dtype=np.float32))


DRIVERS: dict[str, tuple[str, Callable[[], Callable[[np.ndarray], np.ndarray]]]] = {
    "v4": (V4_DRIVER_ID, lambda: ActiveSafetyReflexDriver().act),
    "v5": (V5_DRIVER_ID, lambda: ActiveSafetyDriverV5Candidate().act),
}


def export_scenario(plan: dict, seed: int, specs: dict, profile_cache: dict, scenario_id: str) -> dict:
    """Sacrificial reset: snapshot the scenario and pre-consume the friction-step mu draw."""
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
    scenario["scenario_id"] = scenario_id
    return scenario


def measure_current_sim(
    plan: dict, seed: int, specs: dict, profile_cache: dict, driver_id: str, act_fn
) -> dict:
    env = fpr.build_env_for_plan_row(plan, specs, profile_cache)
    try:
        label = fpr.label_for_seed(env, seed)
        episode = run_episode_with_policy(env, MeasurementPolicy(act_fn), driver_id, int(seed))
    finally:
        env.close()
    record = {
        "label": label,
        "steps": int(episode.get("steps", 0)),
        "collision": bool(episode.get("collision", False)),
        "obstacle_completed": bool(episode.get("obstacle_completed", False)),
        "termination_reason": str(episode.get("termination_reason", "")),
        "outcome_bucket": str(episode.get("outcome_bucket", "")),
        "min_clearance_margin": episode.get("min_clearance_margin", ""),
        "speed_mean": episode.get("speed_mean", ""),
    }
    record["outcome"] = fpr.outcome_key(record)
    return record


def run_chrono_episode(client: ChronoWorkerClient, act_fn, scenario: dict) -> dict:
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]))
    spinup = reset_reply["info"].get("spinup", {})
    speeds: list[float] = []
    signature = float(np.sum(obs, dtype=np.float64))
    terminated = False
    truncated = False
    info: dict = dict(reset_reply["info"])
    steps = 0
    while not (terminated or truncated) and steps < int(scenario["max_steps"]) + 5:
        action = act_fn(obs)
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
        "termination_reason": reason,
        "min_clearance_margin": float(margin) if isinstance(margin, (int, float)) else float("nan"),
        "speed_mean": float(np.mean(speeds)) if speeds else float("nan"),
        "spinup_speed_gap": float(spinup.get("spinup_speed_gap", float("nan"))),
        "trace_signature": signature,
    }


def build_seed_maps(plan_rows: list[dict]) -> dict[str, dict[str, int]]:
    """Per-panel fresh_panel_row_id -> eval_seed maps, cross-checked against the panel CSVs."""
    feasible_csv_rows = read_csv_rows(FEASIBLE_ROWS_CSV)
    if len(feasible_csv_rows) != 64:
        raise RuntimeError(f"expected 64 feasible-only rows, got {len(feasible_csv_rows)}")
    feasible_seeds = {str(r["fresh_panel_row_id"]): int(r["eval_seed"]) for r in feasible_csv_rows}

    fresh_csv_rows = read_csv_rows(FRESH_ROWS_CSV)
    fresh_csv_seeds = {str(r["fresh_panel_row_id"]): int(r["eval_seed"]) for r in fresh_csv_rows}
    old_csv_rows = read_csv_rows(OLD_LABELS_CSV)
    old_csv_seeds = {str(r["fresh_panel_row_id"]): int(r["eval_seed"]) for r in old_csv_rows}

    old_seeds: dict[str, int] = {}
    fresh_seeds: dict[str, int] = {}
    for plan in plan_rows:
        row_id = str(plan["fresh_panel_row_id"])
        row_number = int(row_id.rsplit("-", 1)[1])
        old_seed = fpr.seed_for_panel_row(row_number, fpr.OLD_SEED_BASE)
        if int(plan["eval_seed"]) != old_seed or old_csv_seeds[row_id] != old_seed:
            raise RuntimeError(f"old panel seed mismatch on {row_id}")
        fresh_seed = fpr.seed_for_panel_row(row_number, fpr.RETEST_SEED_BASE)
        if fresh_csv_seeds[row_id] != fresh_seed:
            raise RuntimeError(f"fresh panel seed mismatch on {row_id}")
        old_seeds[row_id] = old_seed
        fresh_seeds[row_id] = fresh_seed
        if row_id not in feasible_seeds:
            raise RuntimeError(f"feasible-only panel missing row {row_id}")
    return {"old": old_seeds, "fresh": fresh_seeds, "feasible_only": feasible_seeds}


def load_recorded_outcomes() -> dict[tuple[str, str, str], str]:
    """(panel, driver, row_id) -> recorded current-sim outcome from the B3 validation run."""
    recorded: dict[tuple[str, str, str], str] = {}
    for row in read_csv_rows(V5VAL_ROWS_CSV):
        key = (str(row["panel"]), str(row["driver"]), str(row["fresh_panel_row_id"]))
        recorded[key] = str(row["outcome"])
    return recorded


def load_done_keys() -> dict[tuple[str, str, str], dict]:
    if not ROWS_CSV.exists():
        return {}
    rows = read_csv_rows(ROWS_CSV)
    return {(str(r["panel"]), str(r["driver"]), str(r["fresh_panel_row_id"])): r for r in rows}


def append_row(record: dict) -> None:
    ROWS_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not ROWS_CSV.exists()
    with ROWS_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: record.get(key, "") for key in FIELDNAMES})


class RestartingChronoClient:
    """Chrono worker wrapper: periodic restart + one restart-retry on worker error."""

    def __init__(self, restart_every: int):
        self.restart_every = max(1, int(restart_every))
        self.episodes_since_start = 0
        self.client: ChronoWorkerClient | None = None

    def _ensure(self) -> ChronoWorkerClient:
        if self.client is None:
            self.client = ChronoWorkerClient(stderr_log=STDERR_LOG)
            self.episodes_since_start = 0
        return self.client

    def restart(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def run_episode(self, act_fn, scenario: dict) -> dict:
        if self.episodes_since_start >= self.restart_every:
            self.restart()
        try:
            result = run_chrono_episode(self._ensure(), act_fn, scenario)
        except Exception as exc:  # worker died: restart once and retry from scenario reset
            print(f"  [chrono worker error: {exc!r}; restarting worker and retrying]", flush=True)
            self.restart()
            result = run_chrono_episode(self._ensure(), act_fn, scenario)
        self.episodes_since_start += 1
        return result

    def close(self) -> None:
        self.restart()


def margin_stats(deltas: list[float]) -> dict[str, float | int]:
    finite = [d for d in deltas if np.isfinite(d)]
    if not finite:
        return {"n": 0}
    arr = np.asarray(finite, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "mean_abs": float(np.mean(np.abs(arr))),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def transition_key(current: str, chrono: str) -> str:
    cur = "success" if current == "success" else "failure"
    chr_ = "success" if chrono == "success" else "failure"
    return f"{cur}->{chr_}"


def summarize(rows: list[dict], determinism: dict, units: list[tuple[str, str]]) -> dict:
    def f(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    by_unit: dict[str, Any] = {}
    for panel, driver in units:
        unit_rows = [r for r in rows if str(r["panel"]) == panel and str(r["driver"]) == driver]
        per_label: dict[str, Any] = {}
        for label in LABEL_ORDER:
            sub = [r for r in unit_rows if str(r["label"]) == label]
            if not sub:
                continue
            transitions = Counter(
                transition_key(str(r["current_sim_outcome"]), str(r["chrono_outcome"])) for r in sub
            )
            raw_transitions = Counter(
                f"{r['current_sim_outcome']}->{r['chrono_outcome']}" for r in sub
            )
            per_label[label] = {
                "n": len(sub),
                "current_sim_success": sum(1 for r in sub if str(r["current_sim_outcome"]) == "success"),
                "chrono_success": sum(1 for r in sub if str(r["chrono_outcome"]) == "success"),
                "transitions": {k: transitions[k] for k in sorted(transitions)},
                "raw_outcome_transitions": {k: raw_transitions[k] for k in sorted(raw_transitions)},
                "margin_delta_chrono_minus_current": margin_stats(
                    [f(r["margin_delta_chrono_minus_current"]) for r in sub]
                ),
            }
        flipped = [
            {
                "fresh_panel_row_id": str(r["fresh_panel_row_id"]),
                "eval_seed": int(r["eval_seed"]),
                "label": str(r["label"]),
                "current_sim_outcome": str(r["current_sim_outcome"]),
                "chrono_outcome": str(r["chrono_outcome"]),
                "current_sim_min_clearance_margin": f(r["current_sim_min_clearance_margin"]),
                "chrono_min_clearance_margin": f(r["chrono_min_clearance_margin"]),
                "current_sim_speed_mean": f(r["current_sim_speed_mean"]),
                "chrono_speed_mean": f(r["chrono_speed_mean"]),
            }
            for r in unit_rows
            if str(r["current_sim_outcome"]) != str(r["chrono_outcome"])
        ]
        by_unit[f"{panel}:{driver}"] = {
            "n": len(unit_rows),
            "outcome_match": sum(
                1 for r in unit_rows if str(r["current_sim_outcome"]) == str(r["chrono_outcome"])
            ),
            "current_sim_matches_recorded": sum(
                1 for r in unit_rows if str(r["current_sim_matches_recorded"]) == "True"
            ),
            "current_sim_success": sum(1 for r in unit_rows if str(r["current_sim_outcome"]) == "success"),
            "chrono_success": sum(1 for r in unit_rows if str(r["chrono_outcome"]) == "success"),
            "per_label": per_label,
            "flipped_rows": flipped,
            "margin_delta_all": margin_stats(
                [f(r["margin_delta_chrono_minus_current"]) for r in unit_rows]
            ),
        }
    return {
        "milestone": "feasibility-route-hf4-full-discrepancy",
        "generated_at_utc": utc_timestamp(),
        "backend_id": BACKEND_ID,
        "v4_driver_id": V4_DRIVER_ID,
        "v5_driver_id": V5_DRIVER_ID,
        "row_count": len(rows),
        "units": by_unit,
        "determinism": determinism,
        "rows_csv": str(ROWS_CSV),
        "scenario_dir": str(SCENARIO_DIR),
        "known_differences": list(KNOWN_DIFFERENCES),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="skip (panel,driver,row) keys already in the rows CSV")
    parser.add_argument("--units", default=DEFAULT_UNITS, help="comma list of panel:driver work units")
    parser.add_argument("--restart-every", type=int, default=16, help="chrono worker restart cadence (episodes)")
    parser.add_argument("--skip-determinism", action="store_true")
    args = parser.parse_args()

    units: list[tuple[str, str]] = []
    for item in str(args.units).split(","):
        panel, _, driver = item.strip().partition(":")
        if panel not in PANEL_ORDER or driver not in DRIVERS:
            raise SystemExit(f"unknown work unit {item!r}")
        units.append((panel, driver))

    if not args.resume and ROWS_CSV.exists():
        raise SystemExit(f"{ROWS_CSV} already exists; pass --resume to continue or remove it first")

    source = {
        "m3084_measurement_rows": read_csv_rows(fpr.DEFAULT_M3084_DIR / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(fpr.DEFAULT_M3012_DIR / "executable_workload_rows.csv"),
    }
    plan_rows = fpr.m3090.full_fresh_plan(source)
    if len(plan_rows) != 64:
        raise RuntimeError(f"expected 64 panel plan rows, got {len(plan_rows)}")
    plans = {str(plan["fresh_panel_row_id"]): plan for plan in plan_rows}
    payload = read_json(fpr.DEFAULT_M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in payload["executable_source_specs"]
    }
    profile_cache: dict = {}

    seed_maps = build_seed_maps(plan_rows)
    recorded = load_recorded_outcomes()
    done = load_done_keys() if args.resume else {}
    if done:
        print(f"resume: {len(done)} rows already recorded", flush=True)

    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    chrono = RestartingChronoClient(args.restart_every)
    total = sum(64 for _ in units)
    completed = len(done)
    try:
        for panel, driver in units:
            driver_id, factory = DRIVERS[driver]
            seed_map = seed_maps[panel]
            for index, plan in enumerate(plan_rows, start=1):
                row_id = str(plan["fresh_panel_row_id"])
                key = (panel, driver, row_id)
                if key in done:
                    continue
                seed = int(seed_map[row_id])

                scenario_path = SCENARIO_DIR / f"{panel}-{row_id}.json"
                if scenario_path.exists():
                    scenario = read_json(scenario_path)
                else:
                    scenario = export_scenario(plan, seed, specs, profile_cache, f"{panel}-{row_id}")
                    write_json(scenario_path, scenario)

                current = measure_current_sim(plan, seed, specs, profile_cache, driver_id, factory())
                chrono_result = chrono.run_episode(factory(), scenario)

                rec_outcome = recorded.get(key, "")
                cur_margin = current["min_clearance_margin"]
                try:
                    margin_delta = float(chrono_result["min_clearance_margin"]) - float(cur_margin)
                except (TypeError, ValueError):
                    margin_delta = float("nan")
                record = {
                    "episode_id": f"fa-chrono-hf4-{panel}-{driver}-{index:04d}",
                    "panel": panel,
                    "driver": driver,
                    "runtime_driver_id": driver_id,
                    "fresh_panel_row_id": row_id,
                    "eval_seed": seed,
                    "spec": str(plan["executable_source_spec_id"]),
                    "base_profile_name": str(plan["base_profile_name"]),
                    "binding_role": str(plan.get("binding_role", "")),
                    "axis_id": str(plan.get("axis_id", "")),
                    "task_family": str(plan.get("task_family", "")),
                    "label": str(current["label"]),
                    "recorded_outcome": rec_outcome,
                    "current_sim_outcome": str(current["outcome"]),
                    "current_sim_matches_recorded": str(current["outcome"]) == rec_outcome,
                    "current_sim_steps": int(current["steps"]),
                    "current_sim_termination_reason": str(current["termination_reason"]),
                    "current_sim_min_clearance_margin": cur_margin,
                    "current_sim_speed_mean": current["speed_mean"],
                    "chrono_outcome": chrono_result["outcome"],
                    "chrono_steps": chrono_result["steps"],
                    "chrono_termination_reason": chrono_result["termination_reason"],
                    "chrono_min_clearance_margin": chrono_result["min_clearance_margin"],
                    "chrono_speed_mean": chrono_result["speed_mean"],
                    "chrono_spinup_speed_gap": chrono_result["spinup_speed_gap"],
                    "chrono_trace_signature": repr(chrono_result["trace_signature"]),
                    "outcome_match": chrono_result["outcome"] == str(current["outcome"]),
                    "margin_delta_chrono_minus_current": margin_delta,
                    "steps_delta_chrono_minus_current": int(chrono_result["steps"]) - int(current["steps"]),
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                append_row(record)
                done[key] = record
                completed += 1
                print(
                    f"[{completed}/{total}] {panel}:{driver} {row_id} seed={seed} label={record['label']} "
                    f"current={record['current_sim_outcome']} chrono={record['chrono_outcome']} "
                    f"match={record['outcome_match']} chrono_steps={record['chrono_steps']}",
                    flush=True,
                )

        # determinism: re-run two designated rows and compare bitwise trace signatures
        determinism: dict[str, Any] = {"checked": False}
        if not args.skip_determinism:
            checks = []
            for panel, driver, row_id in (
                ("old", "v4", str(plan_rows[0]["fresh_panel_row_id"])),
                ("feasible_only", "v5", str(plan_rows[0]["fresh_panel_row_id"])),
            ):
                key = (panel, driver, row_id)
                if key not in done:
                    continue
                _, factory = DRIVERS[driver]
                scenario = read_json(SCENARIO_DIR / f"{panel}-{row_id}.json")
                repeat = chrono.run_episode(factory(), scenario)
                prior = done[key]
                identical = (
                    repeat["outcome"] == str(prior["chrono_outcome"])
                    and int(repeat["steps"]) == int(prior["chrono_steps"])
                    and repr(repeat["trace_signature"]) == str(prior["chrono_trace_signature"])
                )
                checks.append({"panel": panel, "driver": driver, "row": row_id, "identical": bool(identical)})
                print(f"determinism repeat {panel}:{driver} {row_id}: identical={identical}", flush=True)
            determinism = {"checked": True, "repeats": checks, "all_identical": all(c["identical"] for c in checks)}
    finally:
        chrono.close()

    all_rows = read_csv_rows(ROWS_CSV)
    summary = summarize(all_rows, determinism, units)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json(SUMMARY_JSON, summary)
    print()
    for unit_key, unit in summary["units"].items():
        print(
            f"{unit_key}: n={unit['n']} outcome_match={unit['outcome_match']} "
            f"current_success={unit['current_sim_success']} chrono_success={unit['chrono_success']} "
            f"flipped={len(unit['flipped_rows'])}"
        )
    print(f"rows_csv={ROWS_CSV}")
    print(f"summary={SUMMARY_JSON}")


if __name__ == "__main__":
    main()
