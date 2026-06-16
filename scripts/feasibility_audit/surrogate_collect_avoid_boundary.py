"""Collect CRASH-BOUNDARY Chrono avoidance rollouts. The clean oracle avoids 120/120, so the
surrogate never sees the hard near-collision cases where avoidance is actually decided (and the
A5 verdict showed avoid=1.0 on the surrogate was an artifact of exactly this). Here we drive the
oracle with an ENTRY-AGGRESSION sweep (under-brake / over-throttle by a fixed bias) so the ego
arrives progressively too fast -> a spread of crashes and just-passes spanning the 2.15 m collision
boundary. Records the same full pose+collision fields as surrogate_collect_avoid_labels so the grey-box
/ physics surrogate can be scored AND trained on boundary fidelity.

Usage: python surrogate_collect_avoid_boundary.py [n_workers=8] [seeds_per_combo=4]
"""
from __future__ import annotations

import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_f2_train as f2  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

N_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
SEEDS_PER_COMBO = int(sys.argv[2]) if len(sys.argv) > 2 else 4
MAX_STEPS = 285
ENTRY_BIAS = [0.0, 0.2, 0.35, 0.5]   # under-brake/over-throttle aggression -> boundary spread
OUT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_boundary.npz"

REVEALS = list(f2.AVOIDANCE_REVEALS_FULL)
MUS = list(f2.AVOIDANCE_MUS_FULL)
COMBOS = [(r, m) for r in REVEALS for m in MUS]
_PARAM_KEYS = ("mass", "iz", "lf", "lr", "mu", "cf", "cr", "max_steer", "max_steer_rate",
               "max_drive_force", "max_brake_force", "drive_tau", "steer_tau")
_lock = threading.Lock()
_rollouts: list[dict] = []


def _pose(info):
    return (float(info.get("x", 0.0)), float(info.get("y", 0.0)), float(info.get("psi", 0.0)),
            float(info.get("vx_body", 0.0)), float(info.get("vy_body", 0.0)), float(info.get("yaw_rate", 0.0)))


def _apply_bias(a, bias):
    a = a.copy()
    a[1] = np.clip(a[1] + bias, -1.0, 1.0)       # more throttle
    a[2] = np.clip(a[2] - 2.0 * bias, -1.0, 1.0)  # less brake
    return a


def _worker(wid):
    client = ChronoWorkerClient(stderr_log=ROOT / f"runs/feasibility_audit/phase4_f2/avoidb_w{wid}_stderr.log")
    done = 0
    try:
        tasks = [(r, m, s, b) for (r, m) in COMBOS for s in range(SEEDS_PER_COMBO) for b in ENTRY_BIAS]
        tasks = tasks[wid::N_WORKERS]
        for (reveal, mu, s, bias) in tasks:
            seed = f2._seed_for(f"avoidb_w{wid}_r{reveal:g}_mu{mu:.3f}_b{bias}", s)
            scenario = f2._avoidance_scenario(int(seed), max_steps=MAX_STEPS, reveal=float(reveal), mu=float(mu))
            policy = f2.make_avoidance_teacher(reveal=float(reveal), mu=float(mu)).factory()
            params = dict(scenario["params"]); ob = dict(scenario.get("obstacle") or {})
            obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
            init = _pose(dict(reset_reply.get("info", {})))
            actions, states, collisions = [], [], []
            terminated = truncated = False; steps = 0
            collision_any = offtrack_any = False; completion = ""
            while not (terminated or truncated) and steps < MAX_STEPS:
                a = _apply_bias(np.asarray(policy(steps, obs), dtype=np.float64), bias)
                obs, terminated, truncated, status, info = client.step(a.astype(np.float32))
                actions.append(a); states.append(_pose(info))
                collision_any = collision_any or bool(info.get("collision", False))
                offtrack_any = offtrack_any or (str(info.get("termination_reason", "")) == "off_track")
                collisions.append(bool(info.get("collision", False)))
                completion = str(info.get("completion_reason", "") or completion)
                steps += 1
            cleared = completion in ("max_steps", "obstacle_pass") or steps >= MAX_STEPS
            avoid_success = bool((not collision_any) and (not offtrack_any) and cleared)
            if steps >= 5:
                with _lock:
                    _rollouts.append({
                        "actions": np.array(actions), "chrono_state": np.array(states, dtype=np.float64),
                        "collision": np.array(collisions, dtype=bool), "init": np.array(init),
                        "avoid_success": avoid_success, "collision_any": collision_any,
                        "mu": float(mu), "reveal": float(reveal), "bias": float(bias),
                        "obs_x": float(ob.get("x", 0.0)), "obs_y": float(ob.get("y", 0.0)),
                        "obs_half_width": float(ob.get("half_width", 1.25)), "ego_half_width": float(ob.get("ego_half_width", 0.90)),
                        "params": np.array([float(params[k]) for k in _PARAM_KEYS]),
                    })
                done += 1
    finally:
        client.close()
    return done


def main():
    n_tasks = len(COMBOS) * SEEDS_PER_COMBO * len(ENTRY_BIAS)
    print(f"avoid BOUNDARY: {N_WORKERS} workers, {len(COMBOS)} combos × {SEEDS_PER_COMBO} seeds × "
          f"{len(ENTRY_BIAS)} bias = {n_tasks} rollouts", flush=True)
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        list(ex.map(_worker, range(N_WORKERS)))
    n_crash = sum(1 for r in _rollouts if r["collision_any"])
    print(f"collected {len(_rollouts)} rollouts, {n_crash} crashes ({100*n_crash/max(len(_rollouts),1):.0f}%)", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    obj = ("actions", "chrono_state", "collision")
    np.savez_compressed(
        OUT, **{k: np.array([r[k] for r in _rollouts], dtype=object) for k in obj},
        init=np.array([r["init"] for r in _rollouts]), params=np.array([r["params"] for r in _rollouts]),
        avoid_success=np.array([r["avoid_success"] for r in _rollouts]),
        collision_any=np.array([r["collision_any"] for r in _rollouts]),
        mu=np.array([r["mu"] for r in _rollouts]), reveal=np.array([r["reveal"] for r in _rollouts]),
        bias=np.array([r["bias"] for r in _rollouts]),
        obs_x=np.array([r["obs_x"] for r in _rollouts]), obs_y=np.array([r["obs_y"] for r in _rollouts]),
        obs_half_width=np.array([r["obs_half_width"] for r in _rollouts]),
        ego_half_width=np.array([r["ego_half_width"] for r in _rollouts]),
        param_keys=np.array(_PARAM_KEYS))
    print(f"saved {OUT}  ({len(_rollouts)} rollouts)", flush=True)


if __name__ == "__main__":
    main()
