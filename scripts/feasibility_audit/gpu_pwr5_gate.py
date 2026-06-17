"""PWR5 verdict gate: does the MEASURED DRIVELINE ROTATIONAL-INERTIA effect (engine-speed lead on
throttle release, gpu_physics_pwr5) close any of the avoid down-ramp under-drive WITHOUT regressing
drift -- and is the closure HONEST (measured, not gate-tuned)?

Root cause (independently verified from the ground-truth replay telemetry,
runs/feasibility_audit/phase4_f2/avoid_term_decomp_{chrono,model_pwr3}.npz):
  At a SETTLED cruise Chrono's engine rpm == the model's rigid vx/r_eff*gear*final prediction
  (excess ~0-6 rpm). On the throttle RELEASE down-ramp Chrono's engine spins +260..+485 rpm above
  rigid (the "+315 rpm" driveline-inertia lead): the spinning ShaftsDriveline2WD inertia (Driveshaft
  0.5 + Differential 0.6 + wheels, NO torque converter) keeps the engine turning as the map torque
  drops. pwr5 carries this as an engine-speed LEAD state delta:
      d(delta)/dt = T_eng/I_eff - delta/tau
  tau = 189 ms (MEASURED from Chrono's rpm-excess decay), I_eff = 0.83 kg.m^2 (MEASURED from the
  torque-proportional windup slope, ~consistent with the JSON ChShaft chain 0.74). The engine torque
  map is read at the led rpm. NEITHER tau NOR I_eff is fit to the avoid gate.

HONEST EXPECTATION (measured before running the gate): the partial-throttle engine torque map is
nearly FLAT in the 1600-2000 rpm band, so the +300 rpm lead changes the drive force by only ~-9..-18 N
(and slightly NEGATIVE -- the flat map gives marginally less torque at higher rpm). So pwr5 is a
faithful, measured correction of a real omission, but its avoid-gate impact is expected to be tiny.
This gate REPORTS the measured numbers either way -- it does NOT claim closure without them.

Reports, side-by-side pwr3 vs pwr5:
  (A) AVOIDANCE: vx_rmse overall + accel/brake breakdown + vy (target stated: pwr5 accel < pwr3 0.479,
      overall < 0.520) -- and the measured down-ramp ax-gap (model ax_body - Chrono ax) before/after.
  (B) DRIFT: beta@24 p90 + the HONEST true-vx beta@24 + drift vx_rmse (MUST NOT regress: pwr3 is
      0.0323 / honest 0.0368; the inertia term touches longitudinal, drift uses tiny throttle).

    python scripts/feasibility_audit/gpu_pwr5_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_pwr5 import (  # noqa: E402  pwr3 + MEASURED driveline-inertia engine-speed lead
    PhysParams as Pwr5Params, make_phys_param_batch as pwr5_batch,
    physics_step as pwr5_step, init_state as pwr5_init,
    DRIVELINE_TAU, DRIVELINE_I_EFF,
)
from autodrift.gpu_physics_pwr3 import (  # noqa: E402  the carried baseline (gear-seed only, rigid coupling)
    PhysParams as Pwr3Params, make_phys_param_batch as pwr3_batch,
    physics_step as pwr3_step, init_state as pwr3_init,
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


# ---- measured down-ramp ax-gap (telemetry replay), pwr3 vs pwr5, vs the Chrono ground truth ----
def downramp_axgap():
    """Open-loop replay the avoid telemetry actions through pwr3/pwr5 and report the down-ramp
    ax_body gap vs Chrono's measured ax (steps 9-33 = the throttle-release window)."""
    cd = np.load(ROOT / "runs/feasibility_audit/phase4_f2/avoid_term_decomp_chrono.npz", allow_pickle=True)
    kc = list(cd["keys"]); eps = [f"ep{e}" for e in cd["episodes"]]

    def cc(ep, n):
        return cd[ep][:, kc.index(n)]

    # build per-episode actions from Chrono's recorded thr/brk/steer + replay vx as state
    # (these episodes are the avoid cruise; rebuild the action triple the model consumes)
    out = {}
    for tag, make_batch, init_fn, step_fn, ParamCls in [
        ("pwr3", pwr3_batch, pwr3_init, pwr3_step, Pwr3Params),
        ("pwr5", pwr5_batch, pwr5_init, pwr5_step, Pwr5Params),
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
                    # FEED Chrono's true vx/vy/wz each step (open-loop term-replay) so the ax gap is a
                    # pure per-step FORCE comparison, not an accumulated trajectory error.
                    st[:, 3] = vx[t]; st[:, 4] = vy[t]; st[:, 5] = wz[t]
                    # action triple in [-1,1]: steer/max_steer, 2*thr-1, 2*brk-1
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
    print("device=%s  sigma_scale=%.3f  DRIVELINE_TAU=%.3f s  I_eff=%.2f kg.m^2" % (
        DEV, SIGMA_SCALE, DRIVELINE_TAU, DRIVELINE_I_EFF))
    print("\n=== (A) AVOIDANCE: vx fidelity (pwr3 rigid coupling vs pwr5 +driveline-inertia lead) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    a3 = avoid_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3 (rigid)", A, Sx, Sy, mu, meta)
    a5 = avoid_gate(pwr5_batch, pwr5_init, pwr5_step, Pwr5Params, "pwr5 (+driveline inertia)",
                    A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; gate <=0.03; HONEST = pass with TRUE vx) ===")
    d3 = drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3")
    d5 = drift_gate(pwr5_batch, pwr5_init, pwr5_step, Pwr5Params, "pwr5")

    print("\n=== (C) measured down-ramp ax-gap (open-loop term-replay, steps 9-33) ===")
    dr = downramp_axgap()
    print("  ax_body - Chrono_ax  (m/s^2):  pwr3 %.3f -> pwr5 %.3f" % (dr["pwr3"], dr["pwr5"]))

    print("\n=== VERDICT (pwr3 -> pwr5) ===")
    print("  avoid vx_rmse:        %.3f -> %.3f   (target < 0.520)" % (a3["vx"], a5["vx"]))
    print("  avoid vx_rmse accel:  %.3f -> %.3f   (target < 0.479)" % (a3["accel"], a5["accel"]))
    print("  avoid vx_rmse brake:  %.3f -> %.3f" % (a3["brake"], a5["brake"]))
    print("  avoid vy_rmse:        %.3f -> %.3f" % (a3["vy"], a5["vy"]))
    print("  drift beta@24 p90:    %.4f -> %.4f   (must NOT regress; gate <=0.03)" % (d3["p90"], d5["p90"]))
    print("  drift beta@24 TRUEvx: %.4f -> %.4f   (honest, must NOT regress from 0.0368)" % (
        d3["p90_true"], d5["p90_true"]))
    print("  drift vx_rmse:        %.3f -> %.3f" % (d3["vx"], d5["vx"]))
    avoid_ok = a5["accel"] < 0.479 - 1e-3 and a5["vx"] < 0.520 - 1e-3
    drift_untouched = abs(d5["p90"] - d3["p90"]) < 1e-3 and abs(d5["p90_true"] - d3["p90_true"]) < 1e-3
    print("\n  -> avoid accel improved past target: %s | drift UNTOUCHED: %s" % (avoid_ok, drift_untouched))


if __name__ == "__main__":
    main()
