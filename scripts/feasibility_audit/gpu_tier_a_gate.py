"""Tier-a verdict gate: does the chassis-6DOF + per-corner DYNAMIC load transfer close the avoid
vx gap (planar 0.90) toward the drift floor WITHOUT breaking drift (planar ~0.0295)?

Replays the SAME saved Chrono rollouts the planar ``surrogate_physics_pwr_gate.py`` uses, through
BOTH models from the recorded init, and reports the SAME metrics side-by-side:

  (A) AVOIDANCE (surrogate_avoid_labels.npz, re-param mass=1450/izz=2300/front_share~0.518):
      vx_rmse + vy_rmse over all 120 oracle rollouts.   Planar gpu_physics_pwr baseline (published
      in surrogate_physics_pwr_gate): vx_rmse ~0.90, vy_rmse ~0.13.

  (B) DRIFT (surrogate_drift_data.npz, SAME held-out split idx[130:]): beta@24 p90 + vx_rmse.
      Planar gpu_physics_pwr baseline: beta@24 p90 ~0.0295, vx_rmse ~0.27.

The planar baseline is computed LIVE here (imported read-only from autodrift.gpu_physics_pwr) so the
comparison is apples-to-apples on this machine, not just the published numbers.

The KEY question (reported in the VERDICT): did the Tier-a chassis roll/pitch + per-corner DYNAMIC
load transfer move avoid vx_rmse toward the drift floor, and did drift hold ~0.03?

    python scripts/feasibility_audit/gpu_tier_a_gate.py

Does NOT modify gpu_physics*.py / gpu_env*.py / any existing gate -- imports them read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_vehicle_tier_a import (  # noqa: E402  the Tier-a chassis-6DOF + 4-corner model
    TierAParams, make_tier_a_param_batch, physics_step as tier_a_step, init_state as tier_a_init,
    IDX as TA_IDX,
)
from autodrift.gpu_physics_pwr import (  # noqa: E402  the planar baseline (FWD + measured resist)
    PhysParams as PwrParams, make_phys_param_batch as pwr_batch,
    physics_step as pwr_step, init_state as pwr_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
SIGMA_SCALE = 0.165   # SAME contact-patch sigma the pwr / avoid-boundary / brake / coast gates use
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ------------------------------------------------------------- (A) avoidance vx fidelity
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
    meta = dict(R=R, Tmax=Tmax, lens=lens, init=init.astype(np.float32),
                mass=pv0("mass"), iz=pv0("iz"), lf=pv0("lf"), lr=pv0("lr"))
    return torch.tensor(A), torch.tensor(Sx), torch.tensor(Sy), torch.tensor(mu), meta


def avoid_gate(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta,
               vx_col, vy_col, extra=None):
    R, Tmax = meta["R"], meta["Tmax"]
    lens = torch.tensor(meta["lens"], device=DEV)
    kw = dict(mass=meta["mass"], izz=meta["iz"], wheelbase=2.776,
              front_axle_share=meta["lr"] / (meta["lf"] + meta["lr"]), sigma_scale=SIGMA_SCALE)
    if extra:
        kw.update(extra)
    phys = ParamCls(**kw)
    P = make_batch(phys, R, mu=mu.to(DEV), device=DEV, dtype=torch.float32)
    v = torch.tensor(meta["init"], device=DEV)
    st, gear = init_fn(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone()
    st[:, 0], st[:, 1] = v[:, 0], v[:, 1]
    # planar yaw col=2; Tier-a yaw col differs -> set via the index map passed implicitly by label.
    yaw_col = TA_IDX["yaw"] if "Tier" in label else 2
    st[:, yaw_col] = v[:, 2]
    A_t = A.to(DEV); Sx_t = Sx.to(DEV); Sy_t = Sy.to(DEV)
    tidx = torch.arange(Tmax, device=DEV)
    valid = (tidx[None, :] < lens[:, None])
    se_x = torch.zeros(R, device=DEV); se_y = torch.zeros(R, device=DEV)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            vm = valid[:, t].float()
            se_x = se_x + vm * (st[:, vx_col] - Sx_t[:, t]) ** 2
            se_y = se_y + vm * (st[:, vy_col] - Sy_t[:, t]) ** 2
    nvalid = valid.float().sum()
    vx_rmse = float(torch.sqrt(se_x.sum() / nvalid))
    vy_rmse = float(torch.sqrt(se_y.sum() / nvalid))
    print("  [%-24s] vx_rmse=%.3f  vy_rmse=%.3f" % (label, vx_rmse, vy_rmse))
    return vx_rmse, vy_rmse


# --------------------------------------------------------------------------- (B) drift gate
def _drift_load():
    d = np.load(DRIFT, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    return A, V, init, mu


def drift_gate(make_batch, init_fn, step_fn, ParamCls, label, vx_col, vy_col, yaw_col):
    A, V, init, mu = _drift_load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    va = idx[130:]                              # SAME held-out split as pwr/relax/coast gates
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    P = make_batch(ParamCls(sigma_scale=SIGMA_SCALE), R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(Av, device=DEV)
    it = torch.tensor(iv, device=DEV)
    st, gear = init_fn(it[:, 0], it[:, 1], it[:, 2], P)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            sur[:, t, 0] = st[:, vx_col]; sur[:, t, 1] = st[:, vy_col]; sur[:, t, 2] = st[:, yaw_col]
    Vt = torch.tensor(Vv, device=DEV)
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    b24 = (beta_c - beta_s).abs()[:, min(23, T - 1)]
    p90 = float(torch.quantile(b24, 0.9))
    vx_rmse = float(((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt())
    print("  [%-24s] beta@24 p90=%.4f  mean=%.4f  vx_rmse=%.3f" % (
        label, p90, float(b24.mean()), vx_rmse))
    return p90, vx_rmse


def main():
    print("device=%s  sigma_scale=%.3f" % (DEV, SIGMA_SCALE))
    print("Tier-a: chassis-6DOF + 4 kinematic corners (measured Chrono Sedan suspension/tyre/powertrain)")
    print("  measured shock dampers: FRONT 10000 / REAR 15000 N.s/m (Sedan suspension JSON Shock"
          " ForceFunctor); wheel-rate damping = c_shock*MR^2 (MR_f=0.763, MR_r=0.335) ->"
          " c_wheel ~5822/1683, zeta_f~0.69 zeta_r~0.30")

    print("\n=== (A) AVOIDANCE vx/vy (avoid_labels; reparam mass=1450/izz=2300/front_share~0.518) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    print("  reparam: mass=%.0f izz=%.0f front_axle_share=%.4f" % (
        meta["mass"], meta["iz"], meta["lr"] / (meta["lf"] + meta["lr"])))
    vr_pwr, vy_pwr = avoid_gate(pwr_batch, pwr_init, pwr_step, PwrParams,
                                "planar pwr (baseline)", A, Sx, Sy, mu, meta, vx_col=3, vy_col=4)
    vr_ta, vy_ta = avoid_gate(make_tier_a_param_batch, tier_a_init, tier_a_step, TierAParams,
                              "Tier-a (6DOF+corners)", A, Sx, Sy, mu, meta,
                              vx_col=TA_IDX["vx"], vy_col=TA_IDX["vy"])

    print("\n=== (B) DRIFT (held-out split; sigma_scale=0.165; must still PASS ~0.0295) ===")
    p90_pwr, dvr_pwr = drift_gate(pwr_batch, pwr_init, pwr_step, PwrParams,
                                  "planar pwr (baseline)", vx_col=3, vy_col=4, yaw_col=5)
    p90_ta, dvr_ta = drift_gate(make_tier_a_param_batch, tier_a_init, tier_a_step, TierAParams,
                                "Tier-a (6DOF+corners)", vx_col=TA_IDX["vx"], vy_col=TA_IDX["vy"],
                                yaw_col=TA_IDX["wz"])

    print("\n=== VERDICT ===")
    print("  avoid vx_rmse:  planar %.3f -> Tier-a %.3f   (drift floor ~0.24)" % (vr_pwr, vr_ta))
    print("  avoid vy_rmse:  planar %.3f -> Tier-a %.3f" % (vy_pwr, vy_ta))
    print("  drift beta@24 p90: planar %.4f -> Tier-a %.4f   (gate <=0.03)" % (p90_pwr, p90_ta))
    print("  drift vx_rmse:  planar %.3f -> Tier-a %.3f" % (dvr_pwr, dvr_ta))
    drift_ok = p90_ta <= 0.03
    avoid_better = vr_ta < vr_pwr - 1e-3
    if drift_ok and avoid_better:
        print("  -> Tier-a chassis roll/pitch + per-corner DYNAMIC load transfer REDUCES avoid vx_rmse"
              " (%.3f -> %.3f) and KEEPS drift passing (%.4f <= 0.03)." % (vr_pwr, vr_ta, p90_ta))
    elif not drift_ok and avoid_better:
        print("  -> Tier-a improves avoid (%.3f -> %.3f) but BREAKS drift (p90 %.4f > 0.03)." % (
            vr_pwr, vr_ta, p90_ta))
    elif drift_ok and not avoid_better:
        print("  -> Tier-a holds drift (%.4f) but did NOT reduce avoid vx_rmse (%.3f vs %.3f)." % (
            p90_ta, vr_ta, vr_pwr))
    else:
        print("  -> Tier-a neither improved avoid nor held drift.")


if __name__ == "__main__":
    main()
