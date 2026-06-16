"""Avoidance-regime fidelity gate: does the surrogate faithfully reproduce Chrono's AVOIDANCE
dynamics + the collision/pass OUTCOME? The grey-box residual was fit ONLY on mu=0.48 drift data,
so this tests whether it helps or HURTS on avoidance (different mu/vehicle/regime). Compares, on the
held-out avoidance rollouts:

  analytic single-track (scenario-parameterised, NO learned residual) -- the honest avoid baseline
  grey-box (+ drift-trained residual)                                  -- does the residual break it?
  physics (Sedan-calibrated; mass overridden to the avoid vehicle)     -- the generalisation arm

Metrics: velocity divergence (vx/vy/yaw) like the drift gate; position RMSE over the maneuver; and
the collision/avoid-success OUTCOME agreement (replay the SAME oracle actions, compute min clearance
to the obstacle on the surrogate's pose trajectory, collision if <= ego_hw+obs_hw).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from autodrift.gpu_surrogate import (  # noqa: E402
    make_param_batch, analytic_step, grey_box_step, ResidualDynamicsMLP, PARAM_KEYS,
)

DEV = "cpu"  # per-rollout sequential replay; CPU avoids GPU per-step sync
torch.set_default_dtype(torch.float32)
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
MLP = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseB.pt"
COLL_RADIUS = 2.15  # ego_half_width(0.90) + obstacle.half_width(1.25)
_DEFAULTS = {"drag_coeff": 0.34, "rolling_resistance": 75.0, "gravity": 9.81}


def load():
    d = np.load(DATA, allow_pickle=True)
    return d


def _param_batch(prow, pkeys):
    src = {k: float(prow[list(pkeys).index(k)]) for k in pkeys if k in PARAM_KEYS}
    for k, v in _DEFAULTS.items():
        src[k] = v
    # fill any missing PARAM_KEYS from VehicleParams defaults
    from autodrift.dynamics import VehicleParams
    vp = VehicleParams()
    for k in PARAM_KEYS:
        src.setdefault(k, getattr(vp, k))
    return make_param_batch(src, 1, device=DEV, dtype=torch.float32)


def replay(actions, init6, P, mlp):
    """Replay actions from full init pose; return surrogate state traj [T,8]."""
    T = actions.shape[0]
    st = torch.zeros(1, 8)
    st[0, :6] = torch.tensor(init6.astype(np.float32))
    A = torch.tensor(actions.astype(np.float32))
    out = np.zeros((T, 8))
    with torch.no_grad():
        for t in range(T):
            st, _ = (grey_box_step(st, A[t:t+1], P, 0.02, mlp) if mlp is not None
                     else analytic_step(st, A[t:t+1], P, 0.02))
            out[t] = st[0].numpy()
    return out


def main():
    d = load()
    actions = d["actions"]; states = d["chrono_state"]; init = d["init"]
    params = d["params"]; pkeys = [str(k) for k in d["param_keys"]]
    avoid_succ_c = d["avoid_success"].astype(bool)
    obs_x = d["obs_x"]; obs_y = d["obs_y"]; ego_hw = d["ego_half_width"]; ohw = d["obs_half_width"]
    R = len(actions)
    mlp = ResidualDynamicsMLP(); mlp.load_state_dict(torch.load(MLP, map_location=DEV)); mlp.eval()
    print(f"avoid fidelity: R={R} rollouts, Chrono avoid_success={int(avoid_succ_c.sum())}/{R}")

    for label, use_mlp in (("analytic (no residual)", None), ("grey-box (+drift residual)", mlp)):
        vx_se = []; vel_div = []; pos_err30 = []; succ_s = np.zeros(R, bool)
        for i in range(R):
            P = _param_batch(params[i], pkeys)
            sur = replay(actions[i], init[i], P, use_mlp)
            ch = states[i]  # [T,6] = x,y,psi,vx,vy,yaw
            T = min(len(sur), len(ch))
            vx_se.append((sur[:T, 3] - ch[:T, 3]) ** 2)
            # velocity divergence (beta-ish): |vy/vx diff|
            bs = np.arctan2(sur[:T, 4], np.abs(sur[:T, 3]) + 1e-6)
            bc = np.arctan2(ch[:T, 4], np.abs(ch[:T, 3]) + 1e-6)
            vel_div.append(np.abs(bs - bc))
            k = min(30, T - 1)
            pos_err30.append(np.hypot(sur[k, 0] - ch[k, 0], sur[k, 1] - ch[k, 1]))
            # surrogate collision outcome (same actions): min clearance to obstacle
            clear = np.hypot(obs_x[i] - sur[:T, 0], obs_y[i] - sur[:T, 1]).min()
            collided = clear <= (ego_hw[i] + ohw[i])
            succ_s[i] = (not collided)
        vx_rmse = float(np.sqrt(np.concatenate(vx_se).mean()))
        vdiv = np.concatenate(vel_div)
        agree = float((succ_s == avoid_succ_c).mean())
        tp = int((succ_s & avoid_succ_c).sum()); tn = int((~succ_s & ~avoid_succ_c).sum())
        fp = int((succ_s & ~avoid_succ_c).sum()); fn = int((~succ_s & avoid_succ_c).sum())
        print(f"\n[{label}]")
        print(f"  velocity: vx_rmse={vx_rmse:.3f}  beta_div mean={vdiv.mean():.4f} p90={np.quantile(vdiv,0.9):.4f}")
        print(f"  position @step30: rmse={np.sqrt(np.mean(np.array(pos_err30)**2)):.3f} m  p90={np.quantile(pos_err30,0.9):.3f} m")
        print(f"  avoid-outcome agree={agree:.3f}  TP={tp} TN={tn} FP={fp} FN={fn}  "
              f"(FP = surrogate says SAFE, Chrono CRASHED -> optimistic, the dangerous direction)")


if __name__ == "__main__":
    main()
