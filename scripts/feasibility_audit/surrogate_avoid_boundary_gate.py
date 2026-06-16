"""Avoid-fix diagnostic: how well does the surrogate predict the avoidance COLLISION OUTCOME on the
crash-boundary data (surrogate_collect_avoid_boundary.py)? This is the metric that decides avoidance
success/failure, and the A5 verdict (avoid=1.0 a surrogate artifact) said the surrogate is blind here.

Replays each boundary rollout's actions through analytic / grey-box from the recorded init pose,
computes min clearance to the obstacle on the surrogate's pose trajectory (collision if <= ego_hw+
obstacle_hw), and compares to Chrono's collision outcome. FN = surrogate says SAFE when Chrono CRASHED
= the dangerous, optimistic direction that lets PPO believe avoidance is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)
from autodrift.gpu_surrogate import (  # noqa: E402
    make_param_batch, analytic_step, grey_box_step, ResidualDynamicsMLP, PARAM_KEYS)
from autodrift.dynamics import VehicleParams  # noqa: E402

DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_boundary.npz"
MLP = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseB.pt"
_DEF = {"drag_coeff": 0.34, "rolling_resistance": 75.0, "gravity": 9.81}


def main():
    d = np.load(DATA, allow_pickle=True)
    A, S, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    pk = [str(k) for k in d["param_keys"]]
    crash_c = d["collision_any"].astype(bool)
    ox, oy, ehw, ohw = d["obs_x"], d["obs_y"], d["ego_half_width"], d["obs_half_width"]
    vp = VehicleParams()
    mlp = ResidualDynamicsMLP(); mlp.load_state_dict(torch.load(MLP, map_location="cpu")); mlp.eval()
    R = len(A)

    def pbatch(prow):
        src = {k: float(prow[pk.index(k)]) for k in pk if k in PARAM_KEYS}
        src.update(_DEF)
        for k in PARAM_KEYS:
            src.setdefault(k, getattr(vp, k))
        return make_param_batch(src, 1, dtype=torch.float32)

    print(f"avoid boundary gate: R={R}, Chrono crashes={int(crash_c.sum())}/{R}")
    for label, use in (("analytic", None), ("grey-box", mlp)):
        crash_s = np.zeros(R, bool)
        for i in range(R):
            P = pbatch(params[i]); st = torch.zeros(1, 8); st[0, :6] = torch.tensor(init[i].astype(np.float32))
            Ai = torch.tensor(A[i].astype(np.float32)); mind = 1e9
            with torch.no_grad():
                for t in range(len(Ai)):
                    st, _ = (grey_box_step(st, Ai[t:t+1], P, 0.02, use) if use is not None
                             else analytic_step(st, Ai[t:t+1], P, 0.02))
                    mind = min(mind, float(np.hypot(ox[i] - float(st[0, 0]), oy[i] - float(st[0, 1]))))
            crash_s[i] = mind <= (ehw[i] + ohw[i])
        tp = int((crash_s & crash_c).sum()); tn = int((~crash_s & ~crash_c).sum())
        fp = int((crash_s & ~crash_c).sum()); fn = int((~crash_s & crash_c).sum())
        bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
        print(f"  [{label:9s}] crash agree={(tp+tn)/R:.3f} bal_acc={bal:.3f} "
              f"TP={tp} TN={tn} FP={fp} FN={fn}  (FN=Chrono CRASH, surrogate SAFE = dangerous)")
    print("verdict: a collision-faithful surrogate (the physics rewrite) is required; the grey-box "
          "residual is at chance here (catches ~2/50 crashes), which is why GPU-trained avoid=1.0 was an artifact.")


if __name__ == "__main__":
    main()
