"""Collect Chrono drift-cell rollouts WITH the full E4 drift-success labels, for the M1
decisive sub-test (A1.iii: does the surrogate reproduce Chrono's drift-SUCCESS verdict, not
just the open-loop velocity?) and the rear-saturation head calibration (A1.ii).

The earlier surrogate_drift_data.npz saved only [vx,vy,yaw_rate]; the E4 success criterion also
needs `rear_saturated` (rear-tyre slip-angle/long-slip from tire telemetry) — which the surrogate
must emit to reproduce `controlled_drift`. Here we drive the SAME oracle + action noise on Chrono
and record, per step: obs-kinematics (vx,vy,yaw_rate,beta exactly as E4 reads them), the rear
slip-angle / longitudinal-slip + `rear_saturated`, the per-step `controlled_drift` flag, and the
rollout `drift_success` / longest-controlled-run — so the surrogate replay can be scored against
the identical criterion.

Usage: python surrogate_collect_drift_labels.py [n_workers=8] [rollouts_per_worker=20]
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
import phase4_e4_drift_regime_pricing as e4  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

N_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
ROLLOUTS_PER_WORKER = int(sys.argv[2]) if len(sys.argv) > 2 else 20
MAX_STEPS = 90
NOISE_SIGMAS = [0.0, 0.0, 0.1, 0.2, 0.35]  # extra weight on pure oracle (the success anchor)
OUT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_labels.npz"

_cell = f2._drift_cell()
_MU = float(_cell["mu"])
_lock = threading.Lock()
_rollouts: list[dict] = []


def _worker(wid: int) -> int:
    teacher = f2.make_drift_teacher()
    client = ChronoWorkerClient(stderr_log=ROOT / f"runs/feasibility_audit/phase4_f2/labels_w{wid}_stderr.log")
    rng = np.random.default_rng(2000 + wid)
    done = 0
    try:
        for r in range(ROLLOUTS_PER_WORKER):
            seed = f2._seed_for(f"labels_w{wid}", r)
            sigma = NOISE_SIGMAS[r % len(NOISE_SIGMAS)]
            scenario = f2._drift_scenario(seed, max_steps=MAX_STEPS, difficulty="hard")
            policy = teacher.factory()
            obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
            rinfo = dict(reset_reply.get("info", {}))
            vx0 = float(rinfo.get("vx_body", 0.0)); vy0 = float(rinfo.get("vy_body", 0.0)); w0 = float(rinfo.get("yaw_rate", 0.0))
            if abs(vx0) < 1e-6:
                b0, sp = float(_cell["initial_beta_rad"]), float(_cell["speed_mps"])
                vx0, vy0, w0 = sp * math.cos(b0), sp * math.sin(b0), sp / float(_cell["track_radius"])
            actions, chrono_v, rear_sat, rear_slip_ang, rear_long_slip, ctrl_drift, betas = [], [], [], [], [], [], []
            longest = current = 0
            terminated = truncated = False
            steps = 0
            while not (terminated or truncated) and steps < MAX_STEPS:
                a = np.asarray(policy(steps, obs), dtype=np.float64)
                if sigma > 0:
                    a = np.clip(a + rng.normal(0.0, sigma, size=3), -1.0, 1.0)
                obs, terminated, truncated, status, info = client.step(a.astype(np.float32))
                finite = e4._is_finite_obs(obs)
                if finite:
                    vx, vy, yaw_rate, beta = e4._obs_kinematics(obs)
                else:
                    vx, vy, yaw_rate, beta = 0.0, 0.0, float("inf"), float("inf")
                rsat, _rc, rsa, rls = e4._rear_saturation(info)
                high_beta = abs(beta) >= e4.BETA_THRESHOLD_RAD
                controlled = e4.MIN_SPEED_MPS <= vx <= e4.MAX_SPEED_MPS and abs(yaw_rate) <= e4.YAW_RATE_LIMIT_RAD_S
                cd = bool(finite and high_beta and rsat and controlled)
                current = current + 1 if cd else 0
                longest = max(longest, current)
                actions.append(a); chrono_v.append((vx, vy, yaw_rate)); betas.append(beta)
                rear_sat.append(bool(rsat)); rear_slip_ang.append(float(rsa)); rear_long_slip.append(float(rls))
                ctrl_drift.append(cd)
                steps += 1
            if steps >= 8:
                with _lock:
                    _rollouts.append({
                        "actions": np.array(actions), "chrono_v": np.array(chrono_v, dtype=np.float64),
                        "beta": np.array(betas, dtype=np.float64), "rear_sat": np.array(rear_sat, dtype=bool),
                        "rear_slip_angle": np.array(rear_slip_ang, dtype=np.float64),
                        "rear_long_slip": np.array(rear_long_slip, dtype=np.float64),
                        "controlled_drift": np.array(ctrl_drift, dtype=bool),
                        "drift_success": bool(longest >= e4.MIN_SUSTAIN_STEPS),
                        "longest_controlled": int(longest),
                        "init": np.array([vx0, vy0, w0]), "mu": _MU, "sigma": sigma,
                    })
                done += 1
    finally:
        client.close()
    return done


def main():
    print(f"labels: {N_WORKERS} workers x {ROLLOUTS_PER_WORKER} rollouts (drift mu={_MU}, "
          f"sustain>={e4.MIN_SUSTAIN_STEPS}, beta_thr={e4.BETA_THRESHOLD_RAD}, "
          f"rear_slip_thr={e4.REAR_SLIP_ANGLE_THRESHOLD_RAD})", flush=True)
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        counts = list(ex.map(_worker, range(N_WORKERS)))
    n_succ = sum(1 for r in _rollouts if r["drift_success"])
    print(f"collected {sum(counts)} rollouts ({len(_rollouts)} saved, {n_succ} drift_success)", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys_obj = ("actions", "chrono_v", "beta", "rear_sat", "rear_slip_angle", "rear_long_slip", "controlled_drift")
    np.savez_compressed(
        OUT,
        **{k: np.array([r[k] for r in _rollouts], dtype=object) for k in keys_obj},
        drift_success=np.array([r["drift_success"] for r in _rollouts]),
        longest_controlled=np.array([r["longest_controlled"] for r in _rollouts]),
        init=np.array([r["init"] for r in _rollouts]),
        mu=np.array([r["mu"] for r in _rollouts]),
        sigma=np.array([r["sigma"] for r in _rollouts]),
    )
    print(f"saved {OUT}  ({len(_rollouts)} rollouts)", flush=True)


if __name__ == "__main__":
    main()
