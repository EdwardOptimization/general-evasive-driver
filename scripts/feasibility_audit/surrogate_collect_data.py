"""Collect Chrono drift-cell rollout trajectories for the B-surrogate (residual training +
physics-rewrite validation). Drives the E4 drift oracle + Gaussian action noise (to cover the
off-policy states PPO will visit) over many rollouts on a small worker pool, saving per-rollout
(action sequence, Chrono vx/vy/yaw_rate trajectory, init state, mu) to an .npz.

Usage: python surrogate_collect_data.py [n_workers=8] [rollouts_per_worker=20]
"""
from __future__ import annotations

import math
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
ROLLOUTS_PER_WORKER = int(sys.argv[2]) if len(sys.argv) > 2 else 20
MAX_STEPS = 90
NOISE_SIGMAS = [0.0, 0.1, 0.2, 0.35]  # cycled across rollouts -> off-policy coverage
OUT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"

_cell = f2._drift_cell()
_MU = float(_cell["mu"])
_lock = threading.Lock()
_rollouts: list[dict] = []


def _state_from_info(info: dict) -> tuple[float, float, float]:
    return float(info.get("vx_body", 0.0)), float(info.get("vy_body", 0.0)), float(info.get("yaw_rate", 0.0))


def _worker(wid: int) -> int:
    teacher = f2.make_drift_teacher()
    client = ChronoWorkerClient(stderr_log=ROOT / f"runs/feasibility_audit/phase4_f2/collect_w{wid}_stderr.log")
    rng = np.random.default_rng(1000 + wid)
    done = 0
    try:
        for r in range(ROLLOUTS_PER_WORKER):
            seed = f2._seed_for(f"collect_w{wid}", r)
            sigma = NOISE_SIGMAS[r % len(NOISE_SIGMAS)]
            scenario = f2._drift_scenario(seed, max_steps=MAX_STEPS, difficulty="hard")
            policy = teacher.factory()
            obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
            rinfo = dict(reset_reply.get("info", {}))
            vx0, vy0, w0 = _state_from_info(rinfo)
            if abs(vx0) < 1e-6:
                b0, sp = float(_cell["initial_beta_rad"]), float(_cell["speed_mps"])
                vx0, vy0, w0 = sp * math.cos(b0), sp * math.sin(b0), sp / float(_cell["track_radius"])
            actions, chrono_v = [], []
            terminated = truncated = False
            steps = 0
            while not (terminated or truncated) and steps < MAX_STEPS:
                a = np.asarray(policy(steps, obs), dtype=np.float64)
                if sigma > 0:
                    a = np.clip(a + rng.normal(0.0, sigma, size=3), -1.0, 1.0)
                obs, terminated, truncated, status, info = client.step(a.astype(np.float32))
                actions.append(a)
                chrono_v.append(_state_from_info(info))
                steps += 1
            if steps >= 8:
                with _lock:
                    _rollouts.append({
                        "actions": np.array(actions), "chrono_v": np.array(chrono_v),
                        "init": np.array([vx0, vy0, w0]), "mu": _MU, "sigma": sigma,
                    })
                done += 1
    finally:
        client.close()
    return done


def main():
    print(f"collecting: {N_WORKERS} workers x {ROLLOUTS_PER_WORKER} rollouts (drift cell mu={_MU})", flush=True)
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        counts = list(ex.map(_worker, range(N_WORKERS)))
    print(f"collected {sum(counts)} rollouts ({len(_rollouts)} saved)", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT,
        actions=np.array([r["actions"] for r in _rollouts], dtype=object),
        chrono_v=np.array([r["chrono_v"] for r in _rollouts], dtype=object),
        init=np.array([r["init"] for r in _rollouts]),
        mu=np.array([r["mu"] for r in _rollouts]),
        sigma=np.array([r["sigma"] for r in _rollouts]),
    )
    tot = sum(len(r["actions"]) for r in _rollouts)
    print(f"saved {OUT}  ({len(_rollouts)} rollouts, {tot} transitions)", flush=True)


if __name__ == "__main__":
    main()
