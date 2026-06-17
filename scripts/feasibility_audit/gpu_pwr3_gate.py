"""PWR3 verdict gate: does the FAITHFUL gear-SEED fix (init_state seeds the HIGHEST in-band gear, the
cruise-entry gear Chrono actually holds, instead of the lowest) close the avoid-vx over-accel WITHOUT
breaking drift -- and does it close it HONESTLY (drift still passes once the longitudinal over-drive,
which was propping the drift 'pass' via a too-high vx, is removed)?

Root cause (verified vs replay telemetry, docs/gpu-surrogate-design-2026-06.md "RESOLVED 2026-06-17"):
at the avoid cruise the model sat in gear 2 while Chrono held gear 3 (100% of matched steps; model rpm
1.49x, T_driveshaft 1.74x too high). Shift POINTS + FSM are correct (match the JSON); the bug was the
gear SEED in init_state -- it picked the lowest gear under its up-threshold (accelerate-from-rest), not
the highest gear in the [down,up] hysteresis band (cruise-entry). gpu_physics_pwr3 fixes ONLY the seed.

Reports, side-by-side pwr vs pwr3:
  (A) AVOIDANCE: the MEDIAN GEAR the model runs at cruise (target: 3, matching Chrono) + vx_rmse
      (baseline pwr 0.897; target toward the 0.235 drift floor) + the accel-heavy breakdown.
  (B) DRIFT: the seeded entry gear + beta@24 p90 (gate <=0.03) + drift vx_rmse. The HONEST check:
      pwr's drift pass leaned on vx +0.39 too high; if pwr3 fixes the over-drive, drift vx_rmse should
      DROP and beta@24 must STILL pass -> an honest pass, not a compensating-error pass.

    python scripts/feasibility_audit/gpu_pwr3_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_pwr3 import (  # noqa: E402  pwr + FAITHFUL highest-in-band gear seed
    PhysParams as Pwr3Params, make_phys_param_batch as pwr3_batch,
    physics_step as pwr3_step, init_state as pwr3_init,
)
from autodrift.gpu_physics_pwr import (  # noqa: E402  the pwr baseline (lowest-gear seed)
    PhysParams as PwrParams, make_phys_param_batch as pwr_batch,
    physics_step as pwr_step, init_state as pwr_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
SIGMA_SCALE = 0.165
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


def _avoid_load_batched():
    d = np.load(AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    A_l, S_l, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    R = len(A_l)
    lens = np.array([min(len(np.asarray(A_l[i])), len(np.asarray(S_l[i]))) for i in range(R)])
    Tmax = int(lens.max())
    A = np.zeros((R, Tmax, 3), np.float32); Sx = np.zeros((R, Tmax), np.float32)
    Sy = np.zeros((R, Tmax), np.float32)
    for i in range(R):
        T = lens[i]
        A[i, :T] = np.asarray(A_l[i])[:T, :3]
        Sx[i, :T] = np.asarray(S_l[i])[:T, 3]
        Sy[i, :T] = np.asarray(S_l[i])[:T, 4]
    mu = np.array([float(params[i][pk.index("mu")]) for i in range(R)], np.float32)
    pv0 = lambda k: float(params[0][pk.index(k)])  # noqa: E731
    brk0 = np.array([0.5 * (np.asarray(A_l[i])[:30, 2] + 1).mean() for i in range(R)])
    meta = dict(R=R, Tmax=Tmax, lens=lens, init=init.astype(np.float32),
                mass=pv0("mass"), iz=pv0("iz"), lf=pv0("lf"), lr=pv0("lr"),
                brake_heavy=np.where(brk0 > 0.2)[0], accel_heavy=np.where(brk0 <= 0.2)[0])
    return torch.tensor(A), torch.tensor(Sx), torch.tensor(Sy), torch.tensor(mu), meta


def avoid_gate(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta):
    R, Tmax = meta["R"], meta["Tmax"]
    lens = torch.tensor(meta["lens"], device=DEV)
    phys = ParamCls(mass=meta["mass"], izz=meta["iz"], wheelbase=2.776,
                    front_axle_share=meta["lr"] / (meta["lf"] + meta["lr"]), sigma_scale=SIGMA_SCALE)
    P = make_batch(phys, R, mu=mu.to(DEV), device=DEV, dtype=torch.float32)
    v = torch.tensor(meta["init"], device=DEV)
    st, gear = init_fn(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone(); st[:, 0], st[:, 1], st[:, 2] = v[:, 0], v[:, 1], v[:, 2]
    seed_gear = gear.clone()
    A_t = A.to(DEV); Sx_t = Sx.to(DEV); Sy_t = Sy.to(DEV)
    tidx = torch.arange(Tmax, device=DEV); valid = (tidx[None, :] < lens[:, None])
    se_x = torch.zeros(R, device=DEV); se_y = torch.zeros(R, device=DEV)
    err_x = torch.zeros(R, Tmax, device=DEV)
    gear_acc = torch.zeros(R, device=DEV); gear_cnt = torch.zeros(R, device=DEV)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            vm = valid[:, t].float()
            se_x = se_x + vm * (st[:, 3] - Sx_t[:, t]) ** 2
            se_y = se_y + vm * (st[:, 4] - Sy_t[:, t]) ** 2
            err_x[:, t] = (st[:, 3] - Sx_t[:, t])
            # accumulate gear over the mid-cruise window (steps 5..40, accel-ish)
            if 5 <= t <= 40:
                gear_acc = gear_acc + vm * gear.float(); gear_cnt = gear_cnt + vm
    nvalid = valid.float().sum()
    vx_rmse = float(torch.sqrt(se_x.sum() / nvalid)); vy_rmse = float(torch.sqrt(se_y.sum() / nvalid))
    def class_rmse(idx):
        if len(idx) == 0:
            return float("nan")
        ii = torch.tensor(idx, device=DEV)
        return float(torch.sqrt(se_x[ii].sum() / valid[ii].float().sum()))
    vx_accel = class_rmse(meta["accel_heavy"]); vx_brake = class_rmse(meta["brake_heavy"])
    cruise_gear = float((gear_acc / gear_cnt.clamp_min(1)).median())  # 0-indexed; +1 = Chrono gear
    seed_med = float(seed_gear.float().median())
    print("  [%-22s] seed gear(0idx)=%.0f->Chrono %.0f | cruise gear(0idx)=%.2f->Chrono ~%.0f | "
          "vx_rmse=%.3f (accel %.3f / brake %.3f)  vy=%.3f" % (
              label, seed_med, seed_med + 1, cruise_gear, cruise_gear + 1,
              vx_rmse, vx_accel, vx_brake, vy_rmse))
    return vx_rmse, vx_accel, vy_rmse


def _drift_load():
    d = np.load(DRIFT, allow_pickle=True)
    return (np.stack(d["actions"]).astype(np.float32), np.stack(d["chrono_v"]).astype(np.float32),
            d["init"].astype(np.float32), float(d["mu"][0]))


def drift_gate(make_batch, init_fn, step_fn, ParamCls, label):
    A, V, init, mu = _drift_load()
    idx = np.random.default_rng(0).permutation(A.shape[0]); va = idx[130:]
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    P = make_batch(ParamCls(sigma_scale=SIGMA_SCALE), R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(Av, device=DEV); it = torch.tensor(iv, device=DEV)
    st, gear = init_fn(it[:, 0], it[:, 1], it[:, 2], P)
    seed_med = float(gear.float().median())
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
    # HONEST check: beta@24 computed with Chrono's TRUE vx (model vy) -- removes any vx-compensation.
    beta_s_truevx = torch.atan2(sur[..., 1], Vt[..., 0].abs() + 1e-6)
    b24_true = (beta_c - beta_s_truevx).abs()[:, min(23, T - 1)]
    p90_true = float(torch.quantile(b24_true, 0.9))
    print("  [%-22s] seed gear(0idx)=%.0f | beta@24 p90=%.4f  (with TRUE vx=%.4f)  drift vx_rmse=%.3f" % (
        label, seed_med, p90, p90_true, vx_rmse))
    return p90, p90_true, vx_rmse


def main():
    print("device=%s  sigma_scale=%.3f" % (DEV, SIGMA_SCALE))
    print("\n=== (A) AVOIDANCE: gear used + vx fidelity (pwr lowest-seed vs pwr3 highest-in-band seed) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    vr_pwr, va_pwr, vy_pwr = avoid_gate(pwr_batch, pwr_init, pwr_step, PwrParams,
                                        "pwr (lowest seed)", A, Sx, Sy, mu, meta)
    vr_p3, va_p3, vy_p3 = avoid_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params,
                                     "pwr3 (highest-in-band)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; gate <=0.03; HONEST = pass with TRUE vx) ===")
    p_pwr, pt_pwr, dv_pwr = drift_gate(pwr_batch, pwr_init, pwr_step, PwrParams, "pwr (baseline)")
    p_p3, pt_p3, dv_p3 = drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3")

    print("\n=== VERDICT ===")
    gap0 = vr_pwr - 0.235; gap1 = vr_p3 - 0.235
    closed = (gap0 - gap1) / gap0 * 100.0 if gap0 > 1e-6 else 0.0
    print("  avoid vx_rmse:        pwr %.3f -> pwr3 %.3f   (closed %.0f%% of pwr->0.235 floor gap)" % (
        vr_pwr, vr_p3, closed))
    print("  avoid vx_rmse accel:  pwr %.3f -> pwr3 %.3f   (the gear-seed target)" % (va_pwr, va_p3))
    print("  drift beta@24 p90:    pwr %.4f -> pwr3 %.4f   (gate <=0.03)" % (p_pwr, p_p3))
    print("  drift beta@24 TRUEvx: pwr %.4f -> pwr3 %.4f   (HONEST: must be <=0.03, no vx prop)" % (
        pt_pwr, pt_p3))
    print("  drift vx_rmse:        pwr %.3f -> pwr3 %.3f   (lower = over-drive removed)" % (dv_pwr, dv_p3))
    ok_avoid = vr_p3 < vr_pwr - 1e-3
    ok_drift = p_p3 <= 0.03
    ok_honest = pt_p3 <= 0.03
    print("\n  -> avoid improved: %s | drift passes: %s | drift passes HONESTLY (true vx): %s" % (
        ok_avoid, ok_drift, ok_honest))
    if ok_avoid and ok_drift and ok_honest:
        print("  ** FAITHFUL gear-seed fix CLOSES avoid over-accel AND drift passes honestly. **")


if __name__ == "__main__":
    main()
