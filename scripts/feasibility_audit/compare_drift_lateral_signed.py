"""DIAGNOSIS (sign-aware): the lateral/yaw balance at the saddle, pwr3 vs Chrono, focused on the
honest-residual scenarios. All quantities sign-normalised per scenario (multiply by sign of the
scenario's drift so left/right drifts add instead of cancel).

Force-law isolator (B'): pwr3's EXACT tyre Fy evaluated AT CHRONO'S MEASURED per-wheel (alpha,Fz,sx)
vs Chrono's measured Fy -- per wheel, sign-normalised, magnitudes -- to settle whether the tyre
CURVE is the term. Then the yaw-moment decomposition: Mz_front vs Mz_rear, pwr3 vs Chrono, to see
which axle's lateral force drives the extra yaw that over-builds vy.

Run: PYTHONPATH=src python scripts/feasibility_audit/compare_drift_lateral_signed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from autodrift.gpu_physics_pwr3 import PhysParams, make_phys_param_batch, _wheel_forces

C = np.load(ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_chrono.npz", allow_pickle=True)
M = np.load(ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_pwr3.npz")
MU = 0.48; SIGMA_SCALE = 0.165
cols = [str(x) for x in C["columns"]]; ci = {x: i for i, x in enumerate(cols)}
va_c = [int(s) for s in C["held_out"]]
va_m = [int(s) for s in M["held_out"]]
mrow = {si: i for i, si in enumerate(va_m)}
WB = 2.776; LF = LR = WB / 2

# the honest-residual scenarios (top of the p90), measured earlier
WORST = [7, 153, 121, 104, 113, 73, 59, 96, 29, 78, 159, 76]

P1 = make_phys_param_batch(PhysParams(sigma_scale=SIGMA_SCALE), n=1, mu=MU)


def pwr3_fy(alpha, fz, sx):
    a = torch.tensor([alpha], dtype=torch.float32); f = torch.tensor([fz], dtype=torch.float32)
    s = torch.tensor([sx], dtype=torch.float32)
    fx, fy = _wheel_forces(s, a, f, torch.tensor([4000.0]), P1.mu / P1["mu0"], P1, 1.0)
    return float(fy[0])


def run(scen_set, label):
    print("\n" + "=" * 100)
    print("SIGN-NORMALISED saddle balance (steps 10-30), %s (%d scenarios)" % (label, len(scen_set)))
    print("=" * 100)
    # accumulators (sign-normalised so drifts add)
    A = {k: [] for k in ["vy_c", "vy_m", "wz_c", "wz_m",
                          "Fyr_c", "Fyr_m", "Fyf_c", "Fyf_m",
                          "Fyr_law", "Fyf_law",  # pwr3 law at Chrono state
                          "Mzf_c", "Mzr_c", "Mzf_m", "Mzr_m",
                          "alphar_c", "alphar_m", "alphaf_c", "alphaf_m"]}
    for si in scen_set:
        arr = C[f"sc{si}"]; r = mrow[si]
        sgn = np.sign(np.mean([arr[k, ci["vy"]] for k in range(10, 30)]))  # drift direction
        for k in range(10, min(30, arr.shape[0])):
            A["vy_c"].append(sgn * arr[k, ci["vy"]]); A["vy_m"].append(sgn * M["vy"][r, k])
            A["wz_c"].append(sgn * arr[k, ci["wz"]]); A["wz_m"].append(sgn * M["wz"][r, k])
            # rear/front axle Fy
            fyr_c = arr[k, ci["Fy_RL"]] + arr[k, ci["Fy_RR"]]
            fyf_c = arr[k, ci["Fy_FL"]] + arr[k, ci["Fy_FR"]]
            A["Fyr_c"].append(sgn * fyr_c); A["Fyf_c"].append(sgn * fyf_c)
            A["Fyr_m"].append(sgn * M["Fy_r"][r, k]); A["Fyf_m"].append(sgn * M["Fy_f"][r, k])
            # pwr3 LAW at Chrono per-wheel state
            rl = pwr3_fy(arr[k, ci["alpha_RL"]], arr[k, ci["Fz_RL"]], arr[k, ci["sx_RL"]])
            rr = pwr3_fy(arr[k, ci["alpha_RR"]], arr[k, ci["Fz_RR"]], arr[k, ci["sx_RR"]])
            fl = pwr3_fy(arr[k, ci["alpha_FL"]], arr[k, ci["Fz_FL"]], 0.0)
            fr = pwr3_fy(arr[k, ci["alpha_FR"]], arr[k, ci["Fz_FR"]], 0.0)
            A["Fyr_law"].append(sgn * (rl + rr)); A["Fyf_law"].append(sgn * (fl + fr))
            # yaw moments (body frame). front Fy rotated by steer; approximate small steer (cos~1)
            st_c = arr[k, ci["steer"]]
            fyf_c_body = fyf_c * np.cos(st_c)
            A["Mzf_c"].append(sgn * LF * fyf_c_body); A["Mzr_c"].append(sgn * (-LR * fyr_c))
            A["Mzf_m"].append(sgn * LF * M["Fy_f_body"][r, k]); A["Mzr_m"].append(sgn * (-LR * M["Fy_r"][r, k]))
            A["alphar_c"].append(0.5 * (arr[k, ci["alpha_RL"]] + arr[k, ci["alpha_RR"]]))
            A["alphar_m"].append(M["alpha_r_inst"][r, k])
            A["alphaf_c"].append(0.5 * (arr[k, ci["alpha_FL"]] + arr[k, ci["alpha_FR"]]))
            A["alphaf_m"].append(M["alpha_f_lag"][r, k])
    me = {k: np.mean(v) for k, v in A.items()}
    print("  state:   vy  C %+.3f  M %+.3f (Δ%+.3f)   |  wz  C %+.3f  M %+.3f (Δ%+.3f)" % (
        me["vy_c"], me["vy_m"], me["vy_m"] - me["vy_c"], me["wz_c"], me["wz_m"], me["wz_m"] - me["wz_c"]))
    print("  slip:    alpha_rear C %+.4f M %+.4f (Δ%+.4f) | alpha_front C %+.4f M %+.4f (Δ%+.4f)" % (
        me["alphar_c"], me["alphar_m"], me["alphar_m"] - me["alphar_c"],
        me["alphaf_c"], me["alphaf_m"], me["alphaf_m"] - me["alphaf_c"]))
    print()
    print("  --- axle LATERAL FORCE [N] (sign-normalised) ---")
    print("  REAR  Fy:  Chrono %+7.0f | pwr3(traj) %+7.0f (Δ%+5.0f) | pwr3-LAW@Chrono-state %+7.0f (Δ%+5.0f)" % (
        me["Fyr_c"], me["Fyr_m"], me["Fyr_m"] - me["Fyr_c"], me["Fyr_law"], me["Fyr_law"] - me["Fyr_c"]))
    print("  FRONT Fy:  Chrono %+7.0f | pwr3(traj) %+7.0f (Δ%+5.0f) | pwr3-LAW@Chrono-state %+7.0f (Δ%+5.0f)" % (
        me["Fyf_c"], me["Fyf_m"], me["Fyf_m"] - me["Fyf_c"], me["Fyf_law"], me["Fyf_law"] - me["Fyf_c"]))
    print()
    print("  --- YAW MOMENT [N·m] (sign-normalised; +=builds the drift) ---")
    print("  Mz_front:  Chrono %+7.0f | pwr3 %+7.0f (Δ%+5.0f)" % (me["Mzf_c"], me["Mzf_m"], me["Mzf_m"] - me["Mzf_c"]))
    print("  Mz_rear :  Chrono %+7.0f | pwr3 %+7.0f (Δ%+5.0f)" % (me["Mzr_c"], me["Mzr_m"], me["Mzr_m"] - me["Mzr_c"]))
    print("  Mz_net  :  Chrono %+7.0f | pwr3 %+7.0f (Δ%+5.0f)" % (
        me["Mzf_c"] + me["Mzr_c"], me["Mzf_m"] + me["Mzr_m"],
        (me["Mzf_m"] + me["Mzr_m"]) - (me["Mzf_c"] + me["Mzr_c"])))


run(WORST, "WORST honest-residual scenarios")
run(va_c, "ALL held-out")
