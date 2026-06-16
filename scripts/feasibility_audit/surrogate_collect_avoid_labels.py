"""Collect Chrono AVOIDANCE rollouts to validate the surrogate's fidelity in the avoidance regime
(the M1 validation was drift-cell-only; the grey-box residual was fit ONLY on mu=0.48 drift data,
so its avoidance fidelity is unknown — and the GPU PPO smoke train hit avoid=1.000 vs CPU 0.700,
which is suspect). Drives the E2' entry-speed avoidance oracle on Chrono across the reveal x mu grid
(+ action noise) and records, per step: action, full pose+velocity (x,y,psi,vx,vy,yaw), collision,
min_clearance, obstacle_longitudinal, plus the per-rollout avoid_success and the scenario params
(mass/mu/lf/... differ from drift) + obstacle world pose — so the surrogate replay can be scored
on velocity divergence AND the collision/pass OUTCOME transfer.

Usage: python surrogate_collect_avoid_labels.py [n_workers=8] [seeds_per_combo=6]
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
SEEDS_PER_COMBO = int(sys.argv[2]) if len(sys.argv) > 2 else 6
MAX_STEPS = 285
NOISE_SIGMAS = [0.0, 0.0, 0.1, 0.2]
OUT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"

REVEALS = list(f2.AVOIDANCE_REVEALS_FULL)
MUS = list(f2.AVOIDANCE_MUS_FULL)
COMBOS = [(r, m) for r in REVEALS for m in MUS]
_PARAM_KEYS = ("mass", "iz", "lf", "lr", "mu", "cf", "cr", "max_steer", "max_steer_rate",
               "max_drive_force", "max_brake_force", "drive_tau", "steer_tau")

_lock = threading.Lock()
_rollouts: list[dict] = []


def _pose(info: dict) -> tuple[float, float, float, float, float, float]:
    return (float(info.get("x", 0.0)), float(info.get("y", 0.0)), float(info.get("psi", 0.0)),
            float(info.get("vx_body", 0.0)), float(info.get("vy_body", 0.0)), float(info.get("yaw_rate", 0.0)))


def _worker(wid: int) -> int:
    client = ChronoWorkerClient(stderr_log=ROOT / f"runs/feasibility_audit/phase4_f2/avoid_w{wid}_stderr.log")
    rng = np.random.default_rng(3000 + wid)
    done = 0
    try:
        # each worker takes a slice of (combo, seed) tasks
        tasks = [(r, m, s) for (r, m) in COMBOS for s in range(SEEDS_PER_COMBO)]
        tasks = tasks[wid::N_WORKERS]
        for (reveal, mu, s) in tasks:
            seed = f2._seed_for(f"avoid_w{wid}_r{reveal:g}_mu{mu:.3f}", s)
            sigma = NOISE_SIGMAS[s % len(NOISE_SIGMAS)]
            scenario = f2._avoidance_scenario(int(seed), max_steps=MAX_STEPS, reveal=float(reveal), mu=float(mu))
            teacher = f2.make_avoidance_teacher(reveal=float(reveal), mu=float(mu))
            policy = teacher.factory()
            params = dict(scenario["params"])
            ob = dict(scenario.get("obstacle") or {})
            obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
            rinfo = dict(reset_reply.get("info", {}))
            init = _pose(rinfo)
            actions, states, collisions, clears, obs_long = [], [], [], [], []
            terminated = truncated = False
            steps = 0
            collision_any = offtrack_any = False
            completion = ""
            while not (terminated or truncated) and steps < MAX_STEPS:
                a = np.asarray(policy(steps, obs), dtype=np.float64)
                if sigma > 0:
                    a = np.clip(a + rng.normal(0.0, sigma, size=3), -1.0, 1.0)
                obs, terminated, truncated, status, info = client.step(a.astype(np.float32))
                actions.append(a); states.append(_pose(info))
                collision_any = collision_any or bool(info.get("collision", False))
                offtrack_any = offtrack_any or (str(info.get("termination_reason", "")) == "off_track")
                collisions.append(bool(info.get("collision", False)))
                clears.append(float(info.get("min_obstacle_clearance", float("nan"))))
                obs_long.append(float(info.get("obstacle_longitudinal", float("nan"))))
                completion = str(info.get("completion_reason", "") or completion)
                steps += 1
            cleared = completion in ("max_steps", "obstacle_pass") or steps >= MAX_STEPS
            avoid_success = bool((not collision_any) and (not offtrack_any) and cleared)
            if steps >= 5:
                with _lock:
                    _rollouts.append({
                        "actions": np.array(actions), "chrono_state": np.array(states, dtype=np.float64),
                        "collision": np.array(collisions, dtype=bool), "min_clear": np.array(clears, dtype=np.float64),
                        "obstacle_long": np.array(obs_long, dtype=np.float64),
                        "init": np.array(init), "avoid_success": avoid_success,
                        "mu": float(mu), "reveal": float(reveal), "sigma": float(sigma),
                        "obs_x": float(ob.get("x", 0.0)), "obs_y": float(ob.get("y", 0.0)),
                        "obs_half_width": float(ob.get("half_width", 1.25)),
                        "ego_half_width": float(ob.get("ego_half_width", 0.90)),
                        "params": np.array([float(params[k]) for k in _PARAM_KEYS]),
                    })
                done += 1
    finally:
        client.close()
    return done


def main():
    print(f"avoid labels: {N_WORKERS} workers, {len(COMBOS)} reveal×mu combos × {SEEDS_PER_COMBO} seeds "
          f"= {len(COMBOS)*SEEDS_PER_COMBO} rollouts (reveals={REVEALS} mus={MUS})", flush=True)
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        counts = list(ex.map(_worker, range(N_WORKERS)))
    n_succ = sum(1 for r in _rollouts if r["avoid_success"])
    print(f"collected {sum(counts)} rollouts ({len(_rollouts)} saved, {n_succ} avoid_success)", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    obj = ("actions", "chrono_state", "collision", "min_clear", "obstacle_long")
    np.savez_compressed(
        OUT,
        **{k: np.array([r[k] for r in _rollouts], dtype=object) for k in obj},
        init=np.array([r["init"] for r in _rollouts]),
        params=np.array([r["params"] for r in _rollouts]),
        avoid_success=np.array([r["avoid_success"] for r in _rollouts]),
        mu=np.array([r["mu"] for r in _rollouts]), reveal=np.array([r["reveal"] for r in _rollouts]),
        sigma=np.array([r["sigma"] for r in _rollouts]),
        obs_x=np.array([r["obs_x"] for r in _rollouts]), obs_y=np.array([r["obs_y"] for r in _rollouts]),
        obs_half_width=np.array([r["obs_half_width"] for r in _rollouts]),
        ego_half_width=np.array([r["ego_half_width"] for r in _rollouts]),
        param_keys=np.array(_PARAM_KEYS),
    )
    print(f"saved {OUT}  ({len(_rollouts)} rollouts)", flush=True)


if __name__ == "__main__":
    main()
