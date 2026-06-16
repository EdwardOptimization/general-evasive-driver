"""COAST-fix verdict gate: does the MEASURED cruise longitudinal resistance close the avoidance
vx_rmse gap WITHOUT breaking drift?

Runs BOTH gates on ``autodrift.gpu_physics_coast`` (the L1 RELAX-TMeasy model with the MEASURED
Chrono Sedan COASTDOWN resistance: drag_coeff=0 / rolling_resist_coeff~0.0282, vs the drift-saddle-
CALIBRATED drag_coeff=0.80 / rolling_resist_coeff=0.03 in gpu_physics_relax):

  (A) AVOIDANCE vx check -- replays the 120 avoid oracle rollouts (surrogate_avoid_labels.npz)
      through the model RE-PARAMETERISED for the avoid vehicle (mass=1450, izz=2300,
      front_axle_share=lr/(lf+lr)~0.518, Sedan wheelbase/steer/tyre), at sigma_scale=0.165, and
      reports vx_rmse + vy_rmse. Baseline (gpu_physics_relax, calibrated resistance): 1.21 / 0.14.

  (B) DRIFT gate -- replays the held-out drift rollouts (surrogate_drift_data.npz) through the model
      at sigma_scale=0.165 and reports beta@24 p90 (must still PASS ~0.0295 -- the resistance change
      must not break drift, since drift is throttle-on and the resistance change only touches the
      longitudinal axis).

This gate does NOT modify gpu_physics_relax, its gate, or any other model/gate -- it imports them
read-only for the side-by-side baselines.

    python scripts/feasibility_audit/surrogate_physics_coast_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_coast import (  # noqa: E402  the COAST-fixed model (measured resistance)
    PhysParams as CoastParams, make_phys_param_batch as coast_batch,
    physics_step as coast_step, init_state as coast_init,
)
from autodrift.gpu_physics_relax import (  # noqa: E402  the L1 baseline (calibrated resistance)
    PhysParams as RelaxParams, make_phys_param_batch as relax_batch,
    physics_step as relax_step, init_state as relax_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
COAST = ROOT / "runs/feasibility_audit/phase4_f2/chrono_coastdown.npz"
SIGMA_SCALE = 0.165   # SAME contact-patch sigma the avoid-boundary / brake gates use
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ------------------------------------------------------------- (A) avoidance vx fidelity check
def _avoid_load_batched():
    """Load + pad the 120 avoid oracle rollouts to [R, Tmax] tensors with a valid-length mask."""
    d = np.load(AVOID, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    A_l, S_l, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    R = len(A_l)
    lens = np.array([min(len(np.asarray(A_l[i])), len(np.asarray(S_l[i]))) for i in range(R)])
    Tmax = int(lens.max())
    A = np.zeros((R, Tmax, 3), np.float32)
    Sx = np.zeros((R, Tmax), np.float32)        # chrono vx
    Sy = np.zeros((R, Tmax), np.float32)        # chrono vy
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


def avoid_vx_gate(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta):
    """Batched replay of all 120 avoid rollouts; report vx_rmse + vy_rmse + the vx error profile."""
    R, Tmax = meta["R"], meta["Tmax"]
    lens = torch.tensor(meta["lens"], device=DEV)
    phys = ParamCls(mass=meta["mass"], izz=meta["iz"], wheelbase=2.776,
                    front_axle_share=meta["lr"] / (meta["lf"] + meta["lr"]),
                    sigma_scale=SIGMA_SCALE)
    P = make_batch(phys, R, mu=mu.to(DEV), device=DEV, dtype=torch.float32)
    v = torch.tensor(meta["init"], device=DEV)
    st, gear = init_fn(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone()
    st[:, 0], st[:, 1], st[:, 2] = v[:, 0], v[:, 1], v[:, 2]
    A_t = A.to(DEV); Sx_t = Sx.to(DEV); Sy_t = Sy.to(DEV)
    tidx = torch.arange(Tmax, device=DEV)
    valid = (tidx[None, :] < lens[:, None])           # [R, Tmax]
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
    prof = {s: float((err_x[:, s] * valid[:, s].float()).sum() / valid[:, s].float().sum().clamp_min(1))
            for s in (0, 10, 25, 50)}
    print("  [%-26s] vx_rmse=%.3f  vy_rmse=%.3f   mean vx err(sur-chrono) @0/10/25/50 = "
          "%+.3f/%+.3f/%+.3f/%+.3f" % (label, vx_rmse, vy_rmse, prof[0], prof[10], prof[25], prof[50]))
    return vx_rmse, vy_rmse


# --------------------------------------------------------------------------- (B) drift gate
def _drift_load():
    d = np.load(DRIFT, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    return A, V, init, mu


def drift_gate(make_batch, init_fn, step_fn, ParamCls, label):
    A, V, init, mu = _drift_load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    va = idx[130:]                              # SAME held-out split as the relax/tmeasy/brake gates
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    # sigma_scale=0.165 explicitly (the relax gate's PASS ~0.0295 operating point)
    P = make_batch(ParamCls(sigma_scale=SIGMA_SCALE), R, mu=mu, device=DEV, dtype=torch.float32)
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
    print("  [%-26s] beta@24 p90=%.4f  mean=%.4f  vx_rmse=%.3f" % (
        label, p90, float(b24.mean()), vx_rmse))
    return p90, vx_rmse


def main():
    print("device=%s  sigma_scale=%.3f" % (DEV, SIGMA_SCALE))
    if COAST.exists():
        c = np.load(COAST, allow_pickle=True)
        print("MEASURED coastdown (chrono_coastdown.npz): drag_coeff=%.4f  rolling_resist_coeff=%.5f"
              "  (calibrated were drag=%.2f / Crr=%.3f)" % (
                  float(c["drag_coeff_measured"]), float(c["rolling_resist_coeff_measured"]),
                  float(c["drag_coeff_calibrated"]), float(c["rolling_resist_coeff_calibrated"])))
        print("  NOTE: Sedan has NO aero body -> coast decel is speed-FLAT (~0.28 m/s^2 @ 9-13 m/s);"
              " coast module uses drag_coeff=%.4f / Crr=%.4f (measured constant-decel)" % (
                  CoastParams().drag_coeff, CoastParams().rolling_resist_coeff))

    print("\n=== (A) AVOIDANCE vx check (avoid_labels, reparam mass=1450/izz=2300/front_share~0.518) ===")
    print("  baseline gpu_physics_relax (calibrated resistance): vx_rmse 1.21 / vy_rmse 0.14 (published)")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    print("  reparam: mass=%.0f izz=%.0f front_axle_share=%.4f wheelbase=2.776" % (
        meta["mass"], meta["iz"], meta["lr"] / (meta["lf"] + meta["lr"])))
    vr_relax, vy_relax = avoid_vx_gate(relax_batch, relax_init, relax_step, RelaxParams,
                                       "relax (calibrated resist)", A, Sx, Sy, mu, meta)
    vr_coast, vy_coast = avoid_vx_gate(coast_batch, coast_init, coast_step, CoastParams,
                                       "COAST (measured resist)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; sigma_scale=0.165; must still PASS ~0.0295) ===")
    print("  baseline gpu_physics_relax: beta@24 p90 ~0.0295 (PASSES at sigma_scale=0.165)")
    p90_relax, dvr_relax = drift_gate(relax_batch, relax_init, relax_step, RelaxParams,
                                      "relax (baseline)")
    p90_coast, dvr_coast = drift_gate(coast_batch, coast_init, coast_step, CoastParams,
                                      "COAST (measured resist)")

    print("\n=== VERDICT ===")
    print("  avoidance vx_rmse: relax %.3f -> COAST %.3f  (drift floor 0.235)" % (vr_relax, vr_coast))
    print("  avoidance vy_rmse: relax %.3f -> COAST %.3f  (lateral, should stay ~0.14)" % (vy_relax, vy_coast))
    print("  drift beta@24 p90: relax %.4f -> COAST %.4f  (gate <=0.03 @ sigma_scale=0.165)" % (
        p90_relax, p90_coast))
    drift_ok = p90_coast <= 0.03
    improved = vr_coast < vr_relax - 1e-3
    if drift_ok and improved:
        print("  -> MEASURED coast resistance REDUCES avoidance vx_rmse and KEEPS drift passing "
              "(%.4f<=0.03)." % p90_coast)
    elif drift_ok and not improved:
        print("  -> Drift STILL PASSES (%.4f<=0.03) but the measured coast resistance did NOT reduce "
              "avoidance vx_rmse (%.3f vs %.3f)." % (p90_coast, vr_coast, vr_relax))
        print("     The measured cruise resistance is LOWER (not higher) than the calibrated value, so")
        print("     it cannot be the source of the over-speeding. The residual avoidance vx gap is on")
        print("     the DRIVEN side (partial-throttle engine map / gear state / driveline loss), NOT")
        print("     the passive coast resistance.")
    else:
        print("  -> WARNING: coast change BROKE the drift gate (p90 %.4f > 0.03) -- reject." % p90_coast)


if __name__ == "__main__":
    main()
