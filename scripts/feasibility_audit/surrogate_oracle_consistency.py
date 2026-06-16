"""M1 decisive sub-test (A1.iii): does the grey-box surrogate reproduce Chrono's drift-SUCCESS
verdict, not just the open-loop velocity? Open-loop divergence (vx RMSE, beta@24) already passes;
the criterion that actually matters for RL is the *behavioural* one:

    controlled_drift = finite & |beta|>=0.10 & rear_saturated & (2<=vx<=28 & |yaw|<=2.7)
    drift_success    = longest consecutive controlled_drift run >= 24    (E4 truth)

We replay each labelled rollout's action sequence through the grey-box (analytic single-track +
Phase-A residual) from the recorded init, recompute the IDENTICAL criterion on the surrogate's
trajectory, and compare to Chrono's stored verdict. The surrogate's rear-saturation signal is the
rear slip angle alpha_rear = atan2(vy - lr*yaw, |vx|) >= REAR_SLIP_ANGLE_THRESHOLD (matching
Chrono's _rear_saturation slip-angle branch; the single-track has no explicit long-slip, so this
is the slip-angle-only proxy — reported alongside its agreement with Chrono's measured rear slip).

Outputs: drift_success confusion matrix + agreement, per-step controlled_drift / rear_sat
agreement, and alpha_rear-vs-Chrono-rear-slip calibration (the rear-sat head A1.ii signal).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_e4_drift_regime_pricing as e4  # noqa: E402
from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import (  # noqa: E402
    make_param_batch, analytic_step, grey_box_step, ResidualDynamicsMLP,
)

DT = 0.02
DEV = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_default_dtype(torch.float32)
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_labels.npz"
MLP = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseA.pt"
B_THR, RS_THR, SUSTAIN = e4.BETA_THRESHOLD_RAD, e4.REAR_SLIP_ANGLE_THRESHOLD_RAD, e4.MIN_SUSTAIN_STEPS
VMIN, VMAX, WLIM = e4.MIN_SPEED_MPS, e4.MAX_SPEED_MPS, e4.YAW_RATE_LIMIT_RAD_S


def load():
    d = np.load(DATA, allow_pickle=True)
    return (d["actions"], d["chrono_v"], d["beta"], d["rear_sat"], d["rear_slip_angle"],
            d["controlled_drift"], d["drift_success"].astype(bool), d["init"].astype(np.float32),
            float(d["mu"][0]))


def longest_run(flags: np.ndarray) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def surrogate_rollout(actions, init, P, mlp, lr):
    """Replay one action sequence; return per-step (vx,vy,yaw, beta, alpha_rear, controlled_drift)."""
    T = actions.shape[0]
    st = torch.zeros(1, 8, device=DEV); st[0, 3:6] = torch.tensor(init, device=DEV)
    A = torch.tensor(actions.astype(np.float32), device=DEV)
    out = np.zeros((T, 6), dtype=np.float64)
    with torch.no_grad():
        for t in range(T):
            st, _ = (grey_box_step(st, A[t:t+1], P, DT, mlp) if mlp is not None
                     else analytic_step(st, A[t:t+1], P, DT))
            vx, vy, yaw = float(st[0, 3]), float(st[0, 4]), float(st[0, 5])
            beta = np.arctan2(vy, abs(vx) + 1e-6)
            alpha_rear = np.arctan2(vy - lr * yaw, abs(vx) + 1e-6)
            finite = np.isfinite([vx, vy, yaw]).all()
            rsat = abs(alpha_rear) >= RS_THR
            cd = bool(finite and abs(beta) >= B_THR and rsat and VMIN <= vx <= VMAX and abs(yaw) <= WLIM)
            out[t] = (vx, vy, yaw, beta, alpha_rear, cd)
    return out


def main():
    actions, chrono_v, beta_c, rear_sat_c, rear_slip_c, cd_c, succ_c, init, mu = load()
    P1 = make_param_batch(VehicleParams(mu=mu, mass=1684.0), 1, device=DEV, dtype=torch.float32)
    lr = float(P1["lr"][0])
    mlp = None
    if MLP.exists():
        mlp = ResidualDynamicsMLP().to(DEV); mlp.load_state_dict(torch.load(MLP, map_location=DEV)); mlp.eval()
    R = len(actions)

    for label, use_mlp in (("analytic single-track", None), ("grey-box (+residual)", mlp)):
        succ_s = np.zeros(R, bool)
        cd_step_agree = rsat_step_agree = step_tot = 0
        alpha_err = []
        for i in range(R):
            o = surrogate_rollout(actions[i], init[i], P1, use_mlp, lr)
            succ_s[i] = longest_run(o[:, 5].astype(bool)) >= SUSTAIN
            T = min(len(o), len(cd_c[i]))
            cd_step_agree += int((o[:T, 5].astype(bool) == cd_c[i][:T]).sum())
            rsat_s = np.abs(o[:T, 4]) >= RS_THR
            rsat_step_agree += int((rsat_s == rear_sat_c[i][:T]).sum())
            step_tot += T
            alpha_err.append(np.abs(np.abs(o[:T, 4]) - rear_slip_c[i][:T]))
        # drift_success confusion vs Chrono
        tp = int((succ_s & succ_c).sum()); tn = int((~succ_s & ~succ_c).sum())
        fp = int((succ_s & ~succ_c).sum()); fn = int((~succ_s & succ_c).sum())
        agree = (tp + tn) / R
        bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
        aerr = np.concatenate(alpha_err)
        print(f"\n=== {label} (R={R}, Chrono drift_success={int(succ_c.sum())}/{R}) ===")
        print(f"  drift_success: agree={agree:.3f} balanced_acc={bal:.3f} | "
              f"TP={tp} TN={tn} FP={fp} FN={fn}")
        print(f"  per-step controlled_drift agree={cd_step_agree/step_tot:.3f} | "
              f"rear_sat agree={rsat_step_agree/step_tot:.3f}")
        print(f"  |alpha_rear|-vs-Chrono-rear-slip: MAE={aerr.mean():.4f} p90={np.quantile(aerr,0.9):.4f}")

    print(f"\nGATE (A1.iii): drift_success agreement >= 0.90 AND balanced_acc >= 0.90")


if __name__ == "__main__":
    main()
