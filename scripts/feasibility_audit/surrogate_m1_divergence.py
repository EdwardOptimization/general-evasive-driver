"""B-surrogate M1, first signal: open-loop divergence of the analytic single-track GPU
model vs Chrono on the drift-oracle action sequence.

Drives the E4 beta0p28_recover drift oracle in Chrono, records the action sequence and the
Chrono (vx,vy,yaw_rate) trajectory, then replays the SAME actions from the SAME initial state
through autodrift.gpu_surrogate.analytic_step. The per-step divergence tells us how far the
*existing* analytic model is from Chrono in the drift saddle -> whether we need a richer
analytic model (double-track + Magic Formula), a learned residual, or both.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_f2_train as f2  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import make_param_batch, analytic_step  # noqa: E402

DT = 0.02
N_SEEDS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MAX_STEPS = 90


def _state_from_info(info: dict) -> tuple[float, float, float]:
    return float(info.get("vx_body", 0.0)), float(info.get("vy_body", 0.0)), float(info.get("yaw_rate", 0.0))


def run():
    cell = f2._drift_cell()
    mu = float(cell["mu"])
    teacher = f2.make_drift_teacher()
    # single-track params best-matched to the Chrono Sedan (mu from the cell, mass overridden to 1684)
    params = VehicleParams(mu=mu, mass=1684.0)
    torch.set_default_dtype(torch.float64)

    client = ChronoWorkerClient(stderr_log=ROOT / "runs/feasibility_audit/phase4_f2/m1_div_stderr.log")
    all_beta_div, cross_steps = [], []
    try:
        for s in range(N_SEEDS):
            seed = f2._seed_for("m1_div", s)
            scenario = f2._drift_scenario(seed, max_steps=MAX_STEPS, difficulty="hard")
            policy = teacher.factory()
            obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(seed))
            rinfo = dict(reset_reply.get("info", {}))
            vx0, vy0, w0 = _state_from_info(rinfo)
            if abs(vx0) < 1e-6:  # reset info may not carry raw state -> use the cell entry
                b0 = float(cell["initial_beta_rad"]); sp = float(cell["speed_mps"])
                vx0, vy0, w0 = sp * math.cos(b0), sp * math.sin(b0), sp / float(cell["track_radius"])

            actions, chrono_v = [], []
            terminated = truncated = False
            steps = 0
            while not (terminated or truncated) and steps < MAX_STEPS:
                a = np.asarray(policy(steps, obs), dtype=np.float32)
                obs, terminated, truncated, status, info = client.step(a)
                actions.append(a.astype(np.float64))
                chrono_v.append(_state_from_info(info))
                steps += 1
            if steps < 8:
                continue
            chrono_v = np.array(chrono_v)  # [T,3] vx,vy,yaw_rate after each step

            # replay the SAME actions through the analytic single-track from the same init
            P = make_param_batch(params, 1, dtype=torch.float64)
            st = torch.tensor([[0.0, 0.0, 0.0, vx0, vy0, w0, 0.0, 0.0]], dtype=torch.float64)
            sur_v = []
            for a in actions:
                st, _ = analytic_step(st, torch.tensor(a[None], dtype=torch.float64), P, DT)
                sur_v.append([float(st[0, 3]), float(st[0, 4]), float(st[0, 5])])
            sur_v = np.array(sur_v)

            beta_c = np.arctan2(chrono_v[:, 1], np.abs(chrono_v[:, 0]) + 1e-6)
            beta_s = np.arctan2(sur_v[:, 1], np.abs(sur_v[:, 0]) + 1e-6)
            bdiv = np.abs(beta_c - beta_s)
            all_beta_div.append(bdiv)
            cross = np.argmax(bdiv > 0.03) if (bdiv > 0.03).any() else len(bdiv)
            cross_steps.append(cross)
            print("seed %d: T=%d | beta_div @1step=%.4f @8=%.4f @24=%.4f max=%.4f | >0.03 rad at step %s | "
                  "vx_rmse=%.3f vy_rmse=%.3f w_rmse=%.3f" % (
                      s, steps, bdiv[0], bdiv[min(7, len(bdiv)-1)], bdiv[min(23, len(bdiv)-1)], bdiv.max(),
                      cross if cross < len(bdiv) else f">{len(bdiv)}",
                      np.sqrt(((chrono_v[:, 0]-sur_v[:, 0])**2).mean()),
                      np.sqrt(((chrono_v[:, 1]-sur_v[:, 1])**2).mean()),
                      np.sqrt(((chrono_v[:, 2]-sur_v[:, 2])**2).mean())))
    finally:
        client.close()

    if cross_steps:
        print("\n=== SUMMARY (analytic single-track vs Chrono, drift saddle) ===")
        print("median step where |beta| divergence crosses 0.03 rad: %.0f (gate wants >=24)" % np.median(cross_steps))
        print("mean beta divergence @24 steps: %.4f rad (gate wants p90<=0.03)" %
              np.mean([b[min(23, len(b)-1)] for b in all_beta_div]))


if __name__ == "__main__":
    run()
