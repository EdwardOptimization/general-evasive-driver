"""Physical-ceiling probe for the 4 high-speed feasible-row offtrack failures.

For each failure row of the feasible-only panel (rows 0010/0013/0024/0029) this
script replays the episode under a family of *privileged-search* action
schedules (these are NOT candidate controllers; they bound what any reflex
policy could achieve):

- constant steer x constant brake grid (throttle = no drive),
- v4 closed-loop steer + constant brake levels,
- v4 closed-loop steer + early full-brake burst of N steps then coast,
- scaled v4 steer (+ optional extra vy damping) with zero brake,
- crude drift schedules (full steer + throttle).

Success criterion is the real episode criterion (obstacle passed, no collision,
no termination). The best achieved obstacle distance per row bounds the
distance-to-pass shortfall. Result (2026-06 run): only row 0024 is reachable
(zero-brake coast passes); rows 0010/0029 fall ~1.5-2 m of longitudinal travel
short under every schedule, and row 0013 falls ~8.4 m short — these three rows
start 5-11 m/s above the friction-limited cornering speed with the pass point
only ~22 m ahead, so the offtrack precedes the pass under all probed controls.

Outputs: experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv

Deterministic, CPU-only. Usage:
    PYTHONPATH=src python scripts/feasibility_audit/v5_offtrack_ceiling_probe.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import fresh_panel_retest as fpr  # noqa: E402

from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import read_json, write_csv_rows  # noqa: E402
from autodrift.controller_family_full_rollout_execution import read_csv_rows  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT_CSV = REPO_ROOT / "experiments/feasibility_audit/v5_offtrack_ceiling_probe.csv"
FEASIBLE_PANEL_CSV = REPO_ROOT / "experiments/feasibility_audit/feasible_only_panel_rows.csv"

TARGET_EPISODES = [
    "fa-feasible-panel-episode-0010",
    "fa-feasible-panel-episode-0013",
    "fa-feasible-panel-episode-0024",
    "fa-feasible-panel-episode-0029",
]

CLAIM_BOUNDARY = (
    "Privileged-search physical-ceiling probe only; schedules are not candidate controllers and "
    "no driver-performance, repair-success, validation, ranking, or promotion claim is made."
)


def schedules() -> list[tuple[str, Callable]]:
    out: list[tuple[str, Callable]] = []
    for steer in [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.8, 1.0]:
        for brake in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            def pol(k, obs, v4, s=steer, b=brake):
                return np.array([s, -1.0, -1.0 + 2.0 * b], dtype=np.float32)
            out.append((f"const_steer{steer:.2f}_brake{brake:.1f}", pol))
    for brake in [0.0, 0.3, 0.5, 0.7, 0.85, 1.0]:
        def pol(k, obs, v4, b=brake):
            a = v4.act(obs).copy()
            a[1] = -1.0
            a[2] = -1.0 + 2.0 * b
            return a
        out.append((f"v4steer_brake{brake:.2f}", pol))
    for burst in [5, 10, 15, 20, 25]:
        def pol(k, obs, v4, n=burst):
            a = v4.act(obs).copy()
            a[1] = -1.0
            a[2] = 1.0 if k < n else -1.0
            return a
        out.append((f"v4steer_burst{burst}", pol))
    for alpha in [0.6, 0.8, 1.0, 1.2, 1.4]:
        for damp in [0.0, 0.3, 0.6]:
            def pol(k, obs, v4, a_=alpha, d=damp):
                act = v4.act(obs).copy()
                act[0] = float(np.clip(a_ * act[0] - d * obs[1], -1.0, 1.0))
                act[1] = -1.0
                act[2] = -1.0
                return act
            out.append((f"v4steer_scale{alpha:.1f}_vydamp{damp:.1f}", pol))
    for name, vec in [
        ("drift_full", [1.0, 1.0, -1.0]),
        ("drift_thr0.3", [1.0, 0.3, -1.0]),
        ("drift_thr0.0", [0.8, 0.0, -1.0]),
    ]:
        def pol(k, obs, v4, v=tuple(vec)):
            return np.array(v, dtype=np.float32)
        out.append((name, pol))

    def flick(k, obs, v4):
        if k < 15:
            return np.array([1.0, 1.0, -1.0], dtype=np.float32)
        a = v4.act(obs).copy()
        a[1] = -1.0
        return a
    out.append(("drift_flick15_then_v4", flick))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    args = parser.parse_args()

    source = {
        "m3084_measurement_rows": read_csv_rows(fpr.DEFAULT_M3084_DIR / "measurement_episode_rows.csv"),
        "m3012_workload_rows": read_csv_rows(fpr.DEFAULT_M3012_DIR / "executable_workload_rows.csv"),
    }
    plan_rows = fpr.m3090.full_fresh_plan(source)
    plan_by_id = {str(p["fresh_panel_row_id"]): p for p in plan_rows}
    payload = read_json(fpr.DEFAULT_M3012_DIR / "executable_source_specs.json")
    specs = {
        (str(r.get("task_source_id", "")), str(r.get("executable_source_spec_id", ""))): r
        for r in payload["executable_source_specs"]
    }
    panel = {str(r["retest_episode_id"]): r for r in read_csv_rows(FEASIBLE_PANEL_CSV)}
    cache: dict = {}
    rows: list[dict] = []
    for episode_id in TARGET_EPISODES:
        meta = panel[episode_id]
        plan = plan_by_id[str(meta["fresh_panel_row_id"])]
        seed = int(meta["eval_seed"])
        best = None
        n_pass = 0
        for name, pol in schedules():
            env = fpr.build_env_for_plan_row(plan, specs, cache)
            v4 = ActiveSafetyReflexDriver()
            try:
                obs, info = env.reset(seed=seed)
                term = trunc = False
                k = 0
                while not (term or trunc):
                    obs, _r, term, trunc, info = env.step(pol(k, np.asarray(obs, dtype=np.float32), v4))
                    k += 1
            finally:
                env.close()
            ok = bool(info["obstacle_completed"]) and not bool(info["collision"])
            n_pass += int(ok)
            rec = (ok, -float(info["obstacle_distance"]), name, int(info["step"]), str(info["termination_reason"]))
            if best is None or rec[:2] > best[:2]:
                best = rec
        rows.append(
            {
                "episode_id": episode_id,
                "fresh_panel_row_id": str(meta["fresh_panel_row_id"]),
                "eval_seed": seed,
                "spec": str(meta["spec"]),
                "label": str(meta["label"]),
                "schedules_probed": len(schedules()),
                "schedules_passing": n_pass,
                "physically_reachable_under_probe": bool(best[0]),
                "best_schedule": best[2],
                "best_obstacle_distance_at_termination_m": -best[1],
                "best_steps": best[3],
                "best_termination_reason": best[4],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
        print(
            f"{episode_id}: passing={n_pass}/{len(schedules())} best={best[2]} "
            f"odist={-best[1]:.2f} reason={best[4]}"
        )
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv_rows(args.out_csv, rows)
    print(f"out_csv: {args.out_csv}")


if __name__ == "__main__":
    main()
