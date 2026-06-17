"""PWR6 verdict gate — the DECISIVE UNIFIED both-gate test: does giving the FRONT wheels a REAL
longitudinal-slip degree of freedom (gpu_physics_pwr6, the last identified omitted DOF) close the
DRIFT lateral residual (honest beta@24 0.0368 -> target <=0.03) AND/OR the AVOID accel residual
(0.479), WITHOUT regressing the gear-seed gain (avoid must not exceed pwr3's 0.520)?

Root cause (verified, docs/gpu-surrogate-design-2026-06.md "DRIFT LATERAL residual ROOT-CAUSED"):
pwr3 hard-codes the FRONT longitudinal slip to ZERO (free-rolling front), so its combined-slip
friction circle never robs the front Fy the way Chrono's does in the braking/drive-laden drift entry
(corr(|front sx|, pwr3 front-Fy over-production) = -0.84). The same omitted DOF is the leading
hypothesis for the avoid down-ramp ax-gap (Chrono front kappa +0.22 on release, unmodelled).

THE FIX (pwr6): a PHYSICALLY CORRECT FWD restructure -- the powertrain drives REAL front spin states
(omega_fl/fr), the rear axle is non-driven (rolling + brake only), the front longitudinal slip EMERGES
from the front wheel dynamics, and feeds the EXACT TMeasy combined-slip. CRITICAL (measured, NOT tuned):
piping the FULL emergent front sx through pwr3's friction-circle ellipse OVER-corrects (too aggressive at
high sx); the front Fy(alpha,sx) coupling is re-extracted from Chrono (the SAME validation the rear law
passed) and softened to FRONT_SX_COUPLING ~= 0.40. The front-traction-CAP kludge is removed (the front
force self-limits via the real friction circle).

This gate REPORTS the measured numbers either way (it does NOT claim closure without them):
  (V) FRONT Fy vs Chrono at the MEASURED front state (drift_heldout_lateral_chrono.npz): pwr3 ellipse
      (sx=0 and full-sx) vs pwr6 softened coupling vs Chrono's per-wheel Fy, in |sx| bins -- the
      faithfulness check on the combined-slip law.
  (A) AVOIDANCE: vx_rmse overall + accel/brake + vy (does the front slip cut the avoid accel 0.479?)
      + the measured down-ramp ax-gap (model ax_body - Chrono ax, steps 9-33).
  (B) DRIFT: beta@24 p90 + the HONEST true-vx beta@24 (target <=0.03) + drift vx_rmse (must not wreck).

    python scripts/feasibility_audit/gpu_pwr6_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_pwr6 import (  # noqa: E402  pwr3 + FRONT longitudinal-slip DOF (FWD restructure)
    PhysParams as Pwr6Params, make_phys_param_batch as pwr6_batch,
    physics_step as pwr6_step, init_state as pwr6_init,
    _wheel_forces as pwr6_wheel_forces, FRONT_SX_COUPLING,
)
from autodrift.gpu_physics_pwr3 import (  # noqa: E402  the carried baseline (front sx hard-coded 0)
    PhysParams as Pwr3Params, make_phys_param_batch as pwr3_batch,
    physics_step as pwr3_step, init_state as pwr3_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
DRIFT_LAT = ROOT / "runs/feasibility_audit/phase4_f2/drift_heldout_lateral_chrono.npz"
AVOID_DEC = ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_chrono.npz"
SIGMA_SCALE = 0.165
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ============================================================ (V) FRONT Fy faithfulness vs Chrono
def front_fy_validation():
    """Compare the front-wheel lateral force pwr3 (sx=0 and full-sx) vs pwr6 (softened coupling) vs
    Chrono's MEASURED per-wheel Fy, at the SAVED per-wheel front state (drift_heldout_lateral). This
    is the same validation the REAR law passed; it is the faithfulness check on the combined slip.

    NB pwr6's combined-slip is the SAME _wheel_forces with sx scaled by FRONT_SX_COUPLING, so we test
    it by feeding (FRONT_SX_COUPLING * measured sx) into _wheel_forces at the measured (alpha, Fz)."""
    d = np.load(DRIFT_LAT, allow_pickle=True)
    cols = list(map(str, d["columns"])); ci = {c: i for i, c in enumerate(cols)}
    mu = float(d["mu"]); muscale = mu / 0.8
    scs = [k for k in d.files if k.startswith("sc")]
    rows = []
    for sc in scs:
        a = d[sc]
        for w in ["FL", "FR"]:
            for t in range(a.shape[0]):
                rows.append((a[t, ci["sx_" + w]], a[t, ci["alpha_" + w]],
                             a[t, ci["Fy_" + w]], a[t, ci["Fz_" + w]]))
    R = np.array(rows)
    n = R.shape[0]
    P = pwr6_batch(Pwr6Params(), n, mu=mu, device="cpu", dtype=torch.float32)
    fz_nom = P["mass"][0] * P["gravity"][0] * P["front_axle_share"][0] * 0.5
    sx_t = torch.tensor(R[:, 0], dtype=torch.float32)
    al_t = torch.tensor(R[:, 1], dtype=torch.float32)
    fz_t = torch.tensor(R[:, 3], dtype=torch.float32)
    chr_fy = R[:, 2]; asx = np.abs(R[:, 0])
    _, fy_sx0 = pwr6_wheel_forces(torch.zeros_like(sx_t), al_t, fz_t, fz_nom, muscale, P, 1.0)
    _, fy_full = pwr6_wheel_forces(sx_t, al_t, fz_t, fz_nom, muscale, P, 1.0)
    _, fy_soft = pwr6_wheel_forces(FRONT_SX_COUPLING * sx_t, al_t, fz_t, fz_nom, muscale, P, 1.0)
    fy_sx0 = fy_sx0.numpy(); fy_full = fy_full.numpy(); fy_soft = fy_soft.numpy()

    print("  front samples=%d  mu=%.2f  FRONT_SX_COUPLING=%.2f" % (n, mu, FRONT_SX_COUPLING))
    print("  per-|sx| bin     n   Chrono_Fy   pwr3(sx=0)   pwr3(full sx)   pwr6(soft %.2f)" % FRONT_SX_COUPLING)
    for lo, hi in [(0.0, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 0.60)]:
        m = (asx >= lo) & (asx < hi)
        if m.sum() < 3:
            continue
        print("  [%.2f,%.2f]  %5d  %9.1f  %10.1f  %12.1f  %14.1f" % (
            lo, hi, m.sum(), chr_fy[m].mean(), fy_sx0[m].mean(), fy_full[m].mean(), fy_soft[m].mean()))
    tail = asx > 0.05

    def rmse(p, msk):
        return float(np.sqrt(((p[msk] - chr_fy[msk]) ** 2).mean()))
    print("  TAIL(|sx|>0.05) Fy RMSE vs Chrono: pwr3(sx=0)=%.1f  pwr3(full)=%.1f  pwr6(soft)=%.1f N" % (
        rmse(fy_sx0, tail), rmse(fy_full, tail), rmse(fy_soft, tail)))
    print("  TAIL Fy meanErr (pred-Chrono):     pwr3(sx=0)=%+.1f  pwr3(full)=%+.1f  pwr6(soft)=%+.1f N" % (
        (fy_sx0[tail] - chr_fy[tail]).mean(), (fy_full[tail] - chr_fy[tail]).mean(),
        (fy_soft[tail] - chr_fy[tail]).mean()))


# ============================================================ (A) AVOIDANCE vx fidelity
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
    A_t = A.to(DEV); Sx_t = Sx.to(DEV); Sy_t = Sy.to(DEV)
    tidx = torch.arange(Tmax, device=DEV); valid = (tidx[None, :] < lens[:, None])
    se_x = torch.zeros(R, device=DEV); se_y = torch.zeros(R, device=DEV)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            vm = valid[:, t].float()
            se_x = se_x + vm * (st[:, 3] - Sx_t[:, t]) ** 2
            se_y = se_y + vm * (st[:, 4] - Sy_t[:, t]) ** 2
    nvalid = valid.float().sum()
    vx_rmse = float(torch.sqrt(se_x.sum() / nvalid)); vy_rmse = float(torch.sqrt(se_y.sum() / nvalid))

    def class_rmse(idx):
        if len(idx) == 0:
            return float("nan")
        ii = torch.tensor(idx, device=DEV)
        return float(torch.sqrt(se_x[ii].sum() / valid[ii].float().sum()))

    vx_accel = class_rmse(meta["accel_heavy"]); vx_brake = class_rmse(meta["brake_heavy"])
    print("  [%-26s] vx_rmse=%.3f (accel %.3f / brake %.3f)  vy=%.3f" % (
        label, vx_rmse, vx_accel, vx_brake, vy_rmse))
    return dict(vx=vx_rmse, accel=vx_accel, brake=vx_brake, vy=vy_rmse)


# ============================================================ (B) DRIFT beta@24
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
    beta_s_truevx = torch.atan2(sur[..., 1], Vt[..., 0].abs() + 1e-6)
    b24_true = (beta_c - beta_s_truevx).abs()[:, min(23, T - 1)]
    p90_true = float(torch.quantile(b24_true, 0.9))
    print("  [%-26s] beta@24 p90=%.4f  (TRUE vx=%.4f)  drift vx_rmse=%.3f" % (
        label, p90, p90_true, vx_rmse))
    return dict(p90=p90, p90_true=p90_true, vx=vx_rmse)


# ============================================================ (C) measured down-ramp ax-gap
def downramp_axgap():
    """Open-loop replay the avoid telemetry actions through pwr3/pwr6 and report the down-ramp
    ax_body gap vs Chrono's measured ax (steps 9-33 = the throttle-release window). Chrono's true
    vx/vy/wz are fed each step so the gap is a pure per-step FORCE comparison."""
    cd = np.load(AVOID_DEC, allow_pickle=True)
    kc = list(map(str, cd["keys"])); eps = [f"ep{e}" for e in cd["episodes"]]

    def cc(ep, n):
        return cd[ep][:, kc.index(n)]

    out = {}
    for tag, make_batch, init_fn, step_fn, ParamCls in [
        ("pwr3", pwr3_batch, pwr3_init, pwr3_step, Pwr3Params),
        ("pwr6", pwr6_batch, pwr6_init, pwr6_step, Pwr6Params),
    ]:
        gaps = []
        for ep in eps:
            thr = cc(ep, "thr_in"); brk = cc(ep, "brk_in"); steer = cc(ep, "steer")
            vx = cc(ep, "vx"); vy = cc(ep, "vy"); wz = cc(ep, "wz")
            ax_chr = cc(ep, "ax"); mu = 0.3625; T = len(thr)
            P = make_batch(ParamCls(mass=1450.0, izz=2300.0, sigma_scale=SIGMA_SCALE),
                           1, mu=mu, device=DEV, dtype=torch.float32)
            st, gear = init_fn(torch.tensor([vx[0]], device=DEV),
                               torch.tensor([vy[0]], device=DEV),
                               torch.tensor([wz[0]], device=DEV), P)
            ax_model = np.zeros(T)
            with torch.no_grad():
                for t in range(T):
                    st[:, 3] = vx[t]; st[:, 4] = vy[t]; st[:, 5] = wz[t]
                    a = torch.tensor([[float(np.clip(steer[t] / 0.62, -1, 1)),
                                       2 * thr[t] - 1, 2 * brk[t] - 1]], device=DEV, dtype=torch.float32)
                    vx_before = float(st[:, 3])
                    st, gear, _ = step_fn(st, a, gear, P, DT)
                    ax_model[t] = (float(st[:, 3]) - vx_before) / DT
            gaps.append(ax_model[9:33] - ax_chr[9:33])
        g = np.concatenate(gaps)
        out[tag] = float(g.mean())
    return out


def main():
    print("device=%s  sigma_scale=%.3f  FRONT_SX_COUPLING=%.2f" % (DEV, SIGMA_SCALE, FRONT_SX_COUPLING))

    print("\n=== (V) FRONT Fy faithfulness vs Chrono per-wheel (the combined-slip law check) ===")
    front_fy_validation()

    print("\n=== (A) AVOIDANCE: vx fidelity (pwr3 front-sx=0 vs pwr6 +front-slip DOF) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    a3 = avoid_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3 (front sx=0)", A, Sx, Sy, mu, meta)
    a6 = avoid_gate(pwr6_batch, pwr6_init, pwr6_step, Pwr6Params, "pwr6 (+front slip DOF)",
                    A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; gate <=0.03; HONEST = pass with TRUE vx) ===")
    d3 = drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3")
    d6 = drift_gate(pwr6_batch, pwr6_init, pwr6_step, Pwr6Params, "pwr6")

    print("\n=== (C) measured down-ramp ax-gap (open-loop term-replay, steps 9-33) ===")
    dr = downramp_axgap()
    print("  ax_body - Chrono_ax  (m/s^2):  pwr3 %.3f -> pwr6 %.3f" % (dr["pwr3"], dr["pwr6"]))

    print("\n=== VERDICT (pwr3 -> pwr6) — the DECISIVE UNIFIED test ===")
    print("  avoid vx_rmse:        %.3f -> %.3f   (must NOT regress above pwr3 0.520)" % (a3["vx"], a6["vx"]))
    print("  avoid vx_rmse accel:  %.3f -> %.3f   (avoid accel residual 0.479)" % (a3["accel"], a6["accel"]))
    print("  avoid vx_rmse brake:  %.3f -> %.3f" % (a3["brake"], a6["brake"]))
    print("  avoid vy_rmse:        %.3f -> %.3f" % (a3["vy"], a6["vy"]))
    print("  drift beta@24 p90:    %.4f -> %.4f   (gate <=0.03)" % (d3["p90"], d6["p90"]))
    print("  drift beta@24 TRUEvx: %.4f -> %.4f   (HONEST: target <=0.03 -- close the 0.0368)" % (
        d3["p90_true"], d6["p90_true"]))
    print("  drift vx_rmse:        %.3f -> %.3f   (must not wreck drift vx)" % (d3["vx"], d6["vx"]))

    drift_closed = d6["p90_true"] <= 0.03 and d6["p90"] <= 0.03
    drift_vx_ok = d6["vx"] <= d3["vx"] + 0.05
    avoid_no_regress = a6["vx"] <= 0.520 + 1e-3
    avoid_accel_cut = a6["accel"] < a3["accel"] - 1e-3
    print("\n  UNIFIED VERDICT:")
    print("    drift residual CLOSED (honest <=0.03):       %s  (%.4f -> %.4f)" % (
        drift_closed, d3["p90_true"], d6["p90_true"]))
    print("    drift vx not wrecked:                        %s" % drift_vx_ok)
    print("    avoid accel residual CUT:                    %s  (%.3f -> %.3f)" % (
        avoid_accel_cut, a3["accel"], a6["accel"]))
    print("    avoid gear-seed gain preserved (<=0.520):    %s  (%.3f)" % (avoid_no_regress, a6["vx"]))
    if drift_closed and drift_vx_ok and avoid_no_regress:
        print("  ** pwr6 cleanly closes DRIFT without regressing AVOID -> next carried model. **")
    else:
        print("  ** pwr6 does NOT cleanly close both -- see measured deltas above (honest, no closure claim). **")


if __name__ == "__main__":
    main()
