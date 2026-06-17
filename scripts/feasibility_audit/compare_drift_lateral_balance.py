"""DIAGNOSIS: term-by-term lateral/yaw force balance, pwr3 vs Chrono, at the drift saddle.

Two complementary comparisons over the held-out split, saddle window steps 10-30:

(A) ALONG-TRAJECTORY: pwr3's logged internal terms vs Chrono's measured terms at each model's OWN
    state. Shows the compounded divergence (the symptom).

(B) FORCE-LAW AT CHRONO'S STATE (the clean isolator): take Chrono's MEASURED per-wheel slip angle
    + Fz at each saddle step and push them through pwr3's EXACT tyre force law (_wheel_forces).
    Compare the resulting per-wheel Fy to Chrono's measured Fy. This removes the state-divergence
    feedback and asks: does pwr3's tyre LAW reproduce Chrono's lateral force at the measured
    (alpha, Fz)? If yes, the residual is dynamic/feedback (yaw balance / relaxation timing); if no,
    the tyre curve itself is the term.

Run:  PYTHONPATH=src python scripts/feasibility_audit/compare_drift_lateral_balance.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from autodrift.gpu_physics_pwr3 import (  # noqa: E402
    PhysParams, make_phys_param_batch, _wheel_forces,
)

C = np.load(ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_chrono.npz", allow_pickle=True)
M = np.load(ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_pwr3.npz")
MU = 0.48
SIGMA_SCALE = 0.165
W0, W1 = 10, 30  # saddle window

cols = [str(x) for x in C["columns"]]
ci = {x: i for i, x in enumerate(cols)}
va_c = list(int(s) for s in C["held_out"])
va_m = list(int(s) for s in M["held_out"])


def chrono_arr(si):
    return C[f"sc{si}"]


def main():
    # ---- build a pwr3 tyre-law evaluator at arbitrary (sx, alpha, fz) ----
    P = make_phys_param_batch(PhysParams(sigma_scale=SIGMA_SCALE), n=1, mu=MU)

    def pwr3_fy(alpha, fz, sx=0.0):
        a = torch.tensor(np.atleast_1d(alpha), dtype=torch.float32)
        f = torch.tensor(np.atleast_1d(fz), dtype=torch.float32)
        s = torch.tensor(np.atleast_1d(np.broadcast_to(sx, a.shape)), dtype=torch.float32)
        fz_nom = P["mass"] * P["gravity"] * 0.5  # not used by exact tyre
        Pn = make_phys_param_batch(PhysParams(sigma_scale=SIGMA_SCALE), n=len(a), mu=MU)
        fx, fy = _wheel_forces(s, a, f, fz_nom, Pn.mu / Pn["mu0"], Pn, 1.0)
        return fy.numpy()

    # ===== (B) FORCE-LAW AT CHRONO STATE =====
    # accumulate per-wheel: Chrono measured Fy vs pwr3-law Fy at Chrono's (alpha, Fz)
    acc = {w: {"chrono": [], "law": [], "alpha": [], "fz": []} for w in ("FL", "FR", "RL", "RR")}
    rear_axle = {"chrono": [], "law": []}
    front_axle = {"chrono": [], "law": []}
    for si in va_c:
        arr = chrono_arr(si)
        for k in range(W0, min(W1, arr.shape[0])):
            for w in ("FL", "FR", "RL", "RR"):
                al = arr[k, ci[f"alpha_{w}"]]
                fz = arr[k, ci[f"Fz_{w}"]]
                fy_c = arr[k, ci[f"Fy_{w}"]]
                sx = arr[k, ci[f"sx_{w}"]]
                # pwr3 slip-angle sign: alpha_r = atan2(vy_r, vx); Chrono GetSlipAngle sign may flip.
                # use the magnitude-consistent signed alpha by matching Chrono's: Fy<0 with alpha>0.
                fy_law = float(pwr3_fy(al, fz, sx if w in ("RL", "RR") else 0.0)[0])
                acc[w]["chrono"].append(fy_c)
                acc[w]["law"].append(fy_law)
                acc[w]["alpha"].append(al)
                acc[w]["fz"].append(fz)
            rc = arr[k, ci["Fy_RL"]] + arr[k, ci["Fy_RR"]]
            fc = arr[k, ci["Fy_FL"]] + arr[k, ci["Fy_FR"]]
            rl_law = float(pwr3_fy(arr[k, ci["alpha_RL"]], arr[k, ci["Fz_RL"]], arr[k, ci["sx_RL"]])[0])
            rr_law = float(pwr3_fy(arr[k, ci["alpha_RR"]], arr[k, ci["Fz_RR"]], arr[k, ci["sx_RR"]])[0])
            fl_law = float(pwr3_fy(arr[k, ci["alpha_FL"]], arr[k, ci["Fz_FL"]], 0.0)[0])
            fr_law = float(pwr3_fy(arr[k, ci["alpha_FR"]], arr[k, ci["Fz_FR"]], 0.0)[0])
            rear_axle["chrono"].append(rc); rear_axle["law"].append(rl_law + rr_law)
            front_axle["chrono"].append(fc); front_axle["law"].append(fl_law + fr_law)

    print("=" * 100)
    print("(B) FORCE-LAW AT CHRONO'S MEASURED STATE — does pwr3's EXACT TMeasy curve reproduce")
    print("    Chrono's per-wheel Fy at Chrono's measured (alpha, Fz)?  Saddle steps %d-%d, all held-out." % (W0, W1))
    print("    (isolates the TYRE CURVE from state-divergence feedback)")
    print("=" * 100)
    print("%-6s %10s %10s %10s %10s" % ("wheel", "Chrono_Fy", "pwr3_law", "bias(law-C)", "MAE"))
    for w in ("FL", "FR", "RL", "RR"):
        c = np.array(acc[w]["chrono"]); l = np.array(acc[w]["law"])
        print("%-6s %10.0f %10.0f %10.0f %10.0f" % (w, c.mean(), l.mean(), (l - c).mean(), np.abs(l - c).mean()))
    rc = np.array(rear_axle["chrono"]); rl = np.array(rear_axle["law"])
    fc = np.array(front_axle["chrono"]); fl = np.array(front_axle["law"])
    print("-" * 60)
    print("%-6s %10.0f %10.0f %10.0f %10.0f" % ("REAR", rc.mean(), rl.mean(), (rl - rc).mean(), np.abs(rl - rc).mean()))
    print("%-6s %10.0f %10.0f %10.0f %10.0f" % ("FRONT", fc.mean(), fl.mean(), (fl - fc).mean(), np.abs(fl - fc).mean()))

    # ===== (A) ALONG-TRAJECTORY divergence at the saddle =====
    print()
    print("=" * 100)
    print("(A) ALONG-TRAJECTORY state at the saddle (each model at its OWN state). Mean over held-out, steps %d-%d." % (W0, W1))
    print("=" * 100)
    keys = ["vx", "vy", "wz"]
    mrow = {si: i for i, si in enumerate(va_m)}
    cdat = {k: [] for k in keys}; mdat = {k: [] for k in keys}
    c_alphar = []; m_alphar = []; c_Fyr = []; m_Fyr = []; c_Fyf = []; m_Fyf = []
    c_split = []; m_split = []  # rear lateral load split
    for si in va_c:
        arr = chrono_arr(si); r = mrow[si]
        for k in range(W0, min(W1, arr.shape[0])):
            cdat["vx"].append(arr[k, ci["vx"]]); cdat["vy"].append(arr[k, ci["vy"]]); cdat["wz"].append(arr[k, ci["wz"]])
            mdat["vx"].append(M["vx"][r, k]); mdat["vy"].append(M["vy"][r, k]); mdat["wz"].append(M["wz"][r, k])
            c_alphar.append(0.5 * (arr[k, ci["alpha_RL"]] + arr[k, ci["alpha_RR"]]))
            m_alphar.append(M["alpha_r_inst"][r, k])
            c_Fyr.append(arr[k, ci["Fy_RL"]] + arr[k, ci["Fy_RR"]]); m_Fyr.append(M["Fy_r"][r, k])
            c_Fyf.append(arr[k, ci["Fy_FL"]] + arr[k, ci["Fy_FR"]]); m_Fyf.append(M["Fy_f"][r, k])
            c_split.append(arr[k, ci["Fz_RL"]] - arr[k, ci["Fz_RR"]])
            m_split.append(M["fz_rl"][r, k] - M["fz_rr"][r, k])
    for k in keys:
        cm = np.mean(cdat[k]); mm = np.mean(mdat[k])
        print("  %-4s  Chrono %+7.3f   pwr3 %+7.3f   (pwr3-Chrono %+7.3f)" % (k, cm, mm, mm - cm))
    print("  alpha_rear  Chrono %+7.4f   pwr3 %+7.4f   (%+7.4f)" % (np.mean(c_alphar), np.mean(m_alphar), np.mean(m_alphar) - np.mean(c_alphar)))
    print("  Fy_rear[N]  Chrono %+7.0f   pwr3 %+7.0f   (%+7.0f)" % (np.mean(c_Fyr), np.mean(m_Fyr), np.mean(m_Fyr) - np.mean(c_Fyr)))
    print("  Fy_front[N] Chrono %+7.0f   pwr3 %+7.0f   (%+7.0f)" % (np.mean(c_Fyf), np.mean(m_Fyf), np.mean(m_Fyf) - np.mean(c_Fyf)))
    print("  rear Fz split RL-RR[N] Chrono %+7.0f  pwr3 %+7.0f  (%+7.0f)" % (np.mean(c_split), np.mean(m_split), np.mean(m_split) - np.mean(c_split)))


if __name__ == "__main__":
    main()
