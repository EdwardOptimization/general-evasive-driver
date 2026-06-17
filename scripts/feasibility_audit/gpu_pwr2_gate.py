"""PWR2 verdict gate: do the TWO MEASURED avoid-vx fixes (gear shift map + front brake share) close
the residual avoid-vx 0.90 gap WITHOUT breaking drift? Side-by-side gpu_physics_pwr2 vs gpu_physics_pwr.

The faithful-rewrite gap decomposition (docs/gpu-surrogate-design-2026-06.md "FAITHFUL-REWRITE GAPS
DECOMPOSED TO ROOT") attributed the residual avoid-vx 0.90 gap (after the front-drive cap in
gpu_physics_pwr) to TWO measured PLANAR terms:
  (1) GEAR SHIFT MAP  -- measured by extract_chrono_shiftmap.py (the exact per-gear up/down rpm bands
      of the running veh.Sedan() AutomaticTransmissionSimpleMap).
  (2) FRONT BRAKE SHARE -- measured by extract_chrono_brake.py (Sedan brakes ALL 4 wheels at 2000
      N.m/wheel, no front/rear bias; gpu_physics_pwr brakes only the 2 rear).
gpu_physics_pwr2 applies BOTH from the MEASURED Chrono values (NOT tuned). This gate re-runs BOTH
gates on pwr2 and pwr (side-by-side), and a GEAR-FIX-ONLY ablation (pwr2 with the front brake force
disabled) so the brake fix's contribution is isolated.

  (A) AVOIDANCE vx check -- replay surrogate_avoid_labels.npz (mass=1450, izz=2300,
      front_axle_share=lr/(lf+lr)~0.518) at sigma_scale=0.165 -> vx_rmse + vy_rmse + the vx error
      profile. Baseline gpu_physics_pwr: vx 0.896 / vy 0.126. Target: vx toward the drift floor 0.235.
  (B) DRIFT gate -- replay the held-out drift split (surrogate_drift_data.npz) at sigma_scale=0.165 ->
      beta@24 p90 (must still PASS ~0.0295; the gear/brake fixes touch little of the drift regime,
      which uses tiny throttle/brake, so drift should be ~unchanged).

This gate does NOT modify gpu_physics_pwr / gpu_physics_pwr2 / any other model -- it imports them
read-only for the side-by-side baselines.

    python scripts/feasibility_audit/gpu_pwr2_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_pwr2 import (  # noqa: E402  pwr + measured gear-map + 4-wheel brake
    PhysParams as Pwr2Params, make_phys_param_batch as pwr2_batch,
    physics_step as pwr2_step, init_state as pwr2_init,
)
from autodrift.gpu_physics_pwr import (  # noqa: E402  the pwr baseline (front-drive, rear-only brake)
    PhysParams as PwrParams, make_phys_param_batch as pwr_batch,
    physics_step as pwr_step, init_state as pwr_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
SHIFT = ROOT / "runs/feasibility_audit/phase4_f2/chrono_shiftmap.npz"
BRAKE = ROOT / "runs/feasibility_audit/phase4_f2/chrono_brake.npz"
SIGMA_SCALE = 0.165
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ------------------------------------------------------------- (A) avoidance vx fidelity check
def _avoid_load_batched():
    d = np.load(AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    A_l, S_l, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    R = len(A_l)
    lens = np.array([min(len(np.asarray(A_l[i])), len(np.asarray(S_l[i]))) for i in range(R)])
    Tmax = int(lens.max())
    A = np.zeros((R, Tmax, 3), np.float32)
    Sx = np.zeros((R, Tmax), np.float32)
    Sy = np.zeros((R, Tmax), np.float32)
    for i in range(R):
        T = lens[i]
        A[i, :T] = np.asarray(A_l[i])[:T, :3]
        Sx[i, :T] = np.asarray(S_l[i])[:T, 3]
        Sy[i, :T] = np.asarray(S_l[i])[:T, 4]
    mu = np.array([float(params[i][pk.index("mu")]) for i in range(R)], np.float32)
    pv0 = lambda k: float(params[0][pk.index(k)])  # noqa: E731
    # split braking-heavy vs accel-heavy rollouts (first 30 control steps) for the breakdown.
    brk0 = np.array([0.5 * (np.asarray(A_l[i])[:30, 2] + 1).mean() for i in range(R)])
    brake_heavy = np.where(brk0 > 0.2)[0]
    accel_heavy = np.where(brk0 <= 0.2)[0]
    meta = dict(R=R, Tmax=Tmax, lens=lens, init=init.astype(np.float32),
                mass=pv0("mass"), iz=pv0("iz"), lf=pv0("lf"), lr=pv0("lr"),
                brake_heavy=brake_heavy, accel_heavy=accel_heavy)
    return torch.tensor(A), torch.tensor(Sx), torch.tensor(Sy), torch.tensor(mu), meta


def avoid_vx_gate(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta,
                  extra_params=None):
    R, Tmax = meta["R"], meta["Tmax"]
    lens = torch.tensor(meta["lens"], device=DEV)
    kw = dict(mass=meta["mass"], izz=meta["iz"], wheelbase=2.776,
              front_axle_share=meta["lr"] / (meta["lf"] + meta["lr"]),
              sigma_scale=SIGMA_SCALE)
    if extra_params:
        kw.update(extra_params)
    phys = ParamCls(**kw)
    P = make_batch(phys, R, mu=mu.to(DEV), device=DEV, dtype=torch.float32)
    v = torch.tensor(meta["init"], device=DEV)
    st, gear = init_fn(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone()
    st[:, 0], st[:, 1], st[:, 2] = v[:, 0], v[:, 1], v[:, 2]
    A_t = A.to(DEV); Sx_t = Sx.to(DEV); Sy_t = Sy.to(DEV)
    tidx = torch.arange(Tmax, device=DEV)
    valid = (tidx[None, :] < lens[:, None])
    se_x = torch.zeros(R, device=DEV); se_y = torch.zeros(R, device=DEV)
    err_x = torch.zeros(R, Tmax, device=DEV)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            vm = valid[:, t].float()
            se_x = se_x + vm * (st[:, 3] - Sx_t[:, t]) ** 2
            se_y = se_y + vm * (st[:, 4] - Sy_t[:, t]) ** 2
            err_x[:, t] = (st[:, 3] - Sx_t[:, t])
    nvalid = valid.float().sum()
    vx_rmse = float(torch.sqrt(se_x.sum() / nvalid))
    vy_rmse = float(torch.sqrt(se_y.sum() / nvalid))
    # per-class vx_rmse (braking-heavy vs accel-heavy)
    def class_rmse(idx):
        if len(idx) == 0:
            return float("nan")
        ii = torch.tensor(idx, device=DEV)
        return float(torch.sqrt(se_x[ii].sum() / valid[ii].float().sum()))
    vx_brake = class_rmse(meta["brake_heavy"])
    vx_accel = class_rmse(meta["accel_heavy"])
    prof = {s: float((err_x[:, s] * valid[:, s].float()).sum() / valid[:, s].float().sum().clamp_min(1))
            for s in (0, 10, 25, 50)}
    print("  [%-28s] vx_rmse=%.3f  vy_rmse=%.3f   vx_rmse(brake/accel)=%.3f/%.3f   "
          "mean vx err @0/10/25/50 = %+.3f/%+.3f/%+.3f/%+.3f" % (
              label, vx_rmse, vy_rmse, vx_brake, vx_accel, prof[0], prof[10], prof[25], prof[50]))
    return vx_rmse, vy_rmse, vx_brake, vx_accel


# --------------------------------------------------------------------------- (B) drift gate
def _drift_load():
    d = np.load(DRIFT, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    return A, V, init, mu


def drift_gate(make_batch, init_fn, step_fn, ParamCls, label, extra_params=None):
    A, V, init, mu = _drift_load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    va = idx[130:]                              # SAME held-out split as the relax/tmeasy/coast/pwr gates
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    kw = dict(sigma_scale=SIGMA_SCALE)
    if extra_params:
        kw.update(extra_params)
    P = make_batch(ParamCls(**kw), R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(Av, device=DEV)
    it = torch.tensor(iv, device=DEV)
    st, gear = init_fn(it[:, 0], it[:, 1], it[:, 2], P)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            sur[:, t, 0] = st[:, 3]; sur[:, t, 1] = st[:, 4]; sur[:, t, 2] = st[:, 5]
    Vt = torch.tensor(Vv, device=DEV)
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    b24 = (beta_c - beta_s).abs()[:, min(23, T - 1)]
    p90 = float(torch.quantile(b24, 0.9))
    vx_rmse = float(((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt())
    print("  [%-28s] beta@24 p90=%.4f  mean=%.4f  vx_rmse=%.3f" % (
        label, p90, float(b24.mean()), vx_rmse))
    return p90, vx_rmse


def main():
    print("device=%s  sigma_scale=%.3f" % (DEV, SIGMA_SCALE))

    # ---- report the MEASURED fixes the model installs ----
    if SHIFT.exists():
        s = np.load(SHIFT, allow_pickle=True)
        print("\nMEASURED SHIFT MAP (extract_chrono_shiftmap.py, running veh.Sedan()):")
        print("  shift_up   (per gear-idx 0..5) = %s" % np.array2string(s["shift_up"], precision=0))
        print("  shift_down (per gear-idx 0..5) = %s" % np.array2string(s["shift_down"], precision=0))
        print("  model_shift_up(prev JSON)      = %s   -> near-identical (gear thresholds were NOT the bug)" %
              np.array2string(s["model_shift_up"], precision=0))
    if BRAKE.exists():
        b = np.load(BRAKE, allow_pickle=True)
        print("\nMEASURED BRAKE DISTRIBUTION (extract_chrono_brake.py, ChBrakeSimple read-off):")
        print("  per-wheel max brake torque [%s] = %s N.m  (template %s)" % (
            ", ".join(str(x) for x in b["per_wheel_names"]),
            np.array2string(b["per_wheel_left_right"], precision=0), str(b["brake_template"])))
        print("  -> ALL 4 wheels brake at %.0f N.m/wheel, NO front/rear bias; pwr brakes only the 2 rear." %
              float(b["max_brake_torque_per_wheel"]))

    print("\n=== (A) AVOIDANCE vx check (avoid_labels, reparam mass=1450/izz=2300/front_share~0.518) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    print("  reparam: mass=%.0f izz=%.0f front_axle_share=%.4f wheelbase=2.776  (%d braking-heavy, %d accel-heavy rollouts)" % (
        meta["mass"], meta["iz"], meta["lr"] / (meta["lf"] + meta["lr"]),
        len(meta["brake_heavy"]), len(meta["accel_heavy"])))
    vr_pwr, vy_pwr, vxb_pwr, vxa_pwr = avoid_vx_gate(
        pwr_batch, pwr_init, pwr_step, PwrParams, "pwr (front-drive, rear-only brake)",
        A, Sx, Sy, mu, meta)
    # GEAR-FIX-ONLY ablation: pwr2 with the front-brake force disabled (front_brake_scale via brake=0
    # on the front term). We expose it through a model attribute if present; else skip.
    vr_g, vy_g, vxb_g, vxa_g = avoid_vx_gate(
        pwr2_batch, pwr2_init, pwr2_step, Pwr2Params, "pwr2 GEAR-FIX-ONLY (no front brake)",
        A, Sx, Sy, mu, meta, extra_params={"front_brake_scale": 0.0})
    vr_pwr2, vy_pwr2, vxb_pwr2, vxa_pwr2 = avoid_vx_gate(
        pwr2_batch, pwr2_init, pwr2_step, Pwr2Params, "pwr2 (gear-map + 4-wheel brake)",
        A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; sigma_scale=0.165; must still PASS ~0.0295) ===")
    p90_pwr, dvr_pwr = drift_gate(pwr_batch, pwr_init, pwr_step, PwrParams, "pwr (baseline)")
    p90_pwr2, dvr_pwr2 = drift_gate(pwr2_batch, pwr2_init, pwr2_step, Pwr2Params, "pwr2 (gear + brake)")

    print("\n=== VERDICT ===")
    print("  avoid vx_rmse: pwr %.3f -> pwr2 %.3f   (gear-only %.3f)   [drift floor 0.235]" % (
        vr_pwr, vr_pwr2, vr_g))
    print("  avoid vx_rmse braking-heavy: pwr %.3f -> pwr2 %.3f  (the brake-fix target)" % (vxb_pwr, vxb_pwr2))
    print("  avoid vx_rmse accel-heavy:   pwr %.3f -> pwr2 %.3f  (the gear-fix target)" % (vxa_pwr, vxa_pwr2))
    print("  avoid vy_rmse: pwr %.3f -> pwr2 %.3f  (lateral, should stay ~0.13)" % (vy_pwr, vy_pwr2))
    print("  drift beta@24 p90: pwr %.4f -> pwr2 %.4f  (gate <=0.03 @ sigma_scale=0.165)" % (
        p90_pwr, p90_pwr2))
    drift_ok = p90_pwr2 <= 0.03
    gap0 = vr_pwr - 0.235
    gap1 = vr_pwr2 - 0.235
    closed = (gap0 - gap1) / gap0 * 100.0 if gap0 > 1e-6 else 0.0
    print("\n  avoid-vx gap to drift floor: pwr %.3f -> pwr2 %.3f  (closed %.0f%% of the pwr->floor gap)" % (
        gap0, gap1, closed))
    if drift_ok and vr_pwr2 < vr_pwr - 1e-3:
        print("  -> the TWO MEASURED fixes REDUCE avoid vx_rmse and KEEP drift passing (%.4f<=0.03)." % p90_pwr2)
    elif not drift_ok:
        print("  -> WARNING: pwr2 BROKE the drift gate (p90 %.4f > 0.03) -- reject." % p90_pwr2)
    else:
        print("  -> pwr2 did NOT reduce avoid vx_rmse (%.3f vs %.3f)." % (vr_pwr2, vr_pwr))


if __name__ == "__main__":
    main()
