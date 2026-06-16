"""PWR-fix verdict gate: does matching the MEASURED partial-throttle DRIVEN force (the Chrono Sedan
is FRONT-wheel drive) close the avoidance vx gap WITHOUT breaking drift?

Runs BOTH gates on ``autodrift.gpu_physics_pwr`` (the L1 RELAX-TMeasy model with the driven axle
moved to the FRONT -- the measured Chrono Sedan driveline ``ShaftsDriveline2WD`` drives axle 0 =
the FRONT axle -- plus the MEASURED cruise resistance drag=0/Crr=0.0282):

  (A) AVOIDANCE vx check -- replays the avoid oracle rollouts (surrogate_avoid_labels.npz) through
      the model RE-PARAMETERISED for the avoid vehicle (mass=1450, izz=2300,
      front_axle_share=lr/(lf+lr)~0.518, Sedan wheelbase/steer/tyre), at sigma_scale=0.165, and
      reports vx_rmse + vy_rmse. Baseline (gpu_physics_relax, RWD + calibrated resistance):
      1.21 / 0.14. Target: vx toward the drift floor 0.235, vy stays ~0.14.

  (B) DRIFT gate -- replays the held-out drift rollouts (surrogate_drift_data.npz) through the model
      at sigma_scale=0.165 and reports beta@24 p90 (must still PASS ~0.0295 -- moving the drive to
      the front changes which axle's longitudinal slip carries the drive force during a drift, so
      drift is re-checked here).

WHY (measured, from extract_chrono_powertrain.py):
  - Chrono's STEADY-STATE driven force, engine-torque blend, gear schedule, conical final drive
    (0.2) and rpm all MATCH gpu_physics_relax to within ~1.5-7% at the avoid operating points
    (verified: engine torque within 1.5% at every throttle; gear 2 @ 8 m/s in both; final-drive
    0.2 in the JSON). So the partial-throttle TORQUE and the GEAR were NOT the bug.
  - The bug is the DRIVE AXLE: gpu_physics_relax drives the REAR; the Sedan drives the FRONT. Under
    forward accel the quasi-static load transfer UNLOADS the front and LOADS the rear, so a rear-
    drive model has the friction cap of the load-GAINING axle while the real front-drive car is
    traction-limited on the load-LOSING front. Replaying the avoid oracle, relax shows ax ~3.0-3.3
    m/s^2 in the throttle ramp where Chrono shows ~1.1-1.7 (the ~1.75x). Moving the drive to the
    FRONT axle makes the model traction-limited exactly like Chrono.

This gate does NOT modify gpu_physics_relax, its gate, or any other model/gate -- it imports them
read-only for the side-by-side baselines.

    python scripts/feasibility_audit/surrogate_physics_pwr_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_pwr import (  # noqa: E402  the PWR-fixed model (front-drive + measured resist)
    PhysParams as PwrParams, make_phys_param_batch as pwr_batch,
    physics_step as pwr_step, init_state as pwr_init,
)
from autodrift.gpu_physics_relax import (  # noqa: E402  the L1 baseline (RWD + calibrated resist)
    PhysParams as RelaxParams, make_phys_param_batch as relax_batch,
    physics_step as relax_step, init_state as relax_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_labels.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
PWR = ROOT / "runs/feasibility_audit/phase4_f2/chrono_powertrain.npz"
SIGMA_SCALE = 0.165   # SAME contact-patch sigma the avoid-boundary / brake / coast gates use
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ------------------------------------------------------------- (A) avoidance vx fidelity check
def _avoid_load_batched():
    """Load + pad the avoid oracle rollouts to [R, Tmax] tensors with a valid-length mask."""
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
    """Batched replay of all avoid rollouts; report vx_rmse + vy_rmse + the vx error profile."""
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
    va = idx[130:]                              # SAME held-out split as the relax/tmeasy/coast gates
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
    if PWR.exists():
        c = np.load(PWR, allow_pickle=True)
        thr = c["throttles"]; spd = c["speed_cells"]; Fsp = c["F_spindle"]; gear = c["gear"]
        ti = list(thr).index(0.16) if 0.16 in list(thr) else 0
        si = list(spd).index(8.0) if 8.0 in list(spd) else 0
        print("MEASURED powertrain (chrono_powertrain.npz): driven axle = %s (Sedan FWD)" % str(c["driven_axle"]))
        print("  F_drive(spindle read-off) @ throttle 0.16 / 8 m/s = %.0f N  (Chrono gear %d @ 8 m/s)" % (
            Fsp[ti, si], int(gear[ti, si])))
        print("  F_drive(spindle) @ throttle 0.50 / 8 m/s = %.0f N  (Chrono gear %d)" % (
            Fsp[list(thr).index(0.50), si], int(gear[list(thr).index(0.50), si])))

    print("\n=== (A) AVOIDANCE vx check (avoid_labels, reparam mass=1450/izz=2300/front_share~0.518) ===")
    print("  baseline gpu_physics_relax (RWD + calibrated resist): vx_rmse 1.21 / vy_rmse 0.14 (published)")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    print("  reparam: mass=%.0f izz=%.0f front_axle_share=%.4f wheelbase=2.776" % (
        meta["mass"], meta["iz"], meta["lr"] / (meta["lf"] + meta["lr"])))
    vr_relax, vy_relax = avoid_vx_gate(relax_batch, relax_init, relax_step, RelaxParams,
                                       "relax (RWD, calib resist)", A, Sx, Sy, mu, meta)
    vr_pwr, vy_pwr = avoid_vx_gate(pwr_batch, pwr_init, pwr_step, PwrParams,
                                   "PWR (FWD, measured resist)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; sigma_scale=0.165; must still PASS ~0.0295) ===")
    print("  baseline gpu_physics_relax: beta@24 p90 ~0.0295 (PASSES at sigma_scale=0.165)")
    p90_relax, dvr_relax = drift_gate(relax_batch, relax_init, relax_step, RelaxParams,
                                      "relax (baseline)")
    p90_pwr, dvr_pwr = drift_gate(pwr_batch, pwr_init, pwr_step, PwrParams,
                                  "PWR (front-drive)")

    print("\n=== VERDICT ===")
    print("  avoidance vx_rmse: relax %.3f -> PWR %.3f  (drift floor 0.235)" % (vr_relax, vr_pwr))
    print("  avoidance vy_rmse: relax %.3f -> PWR %.3f  (lateral, should stay ~0.14)" % (vy_relax, vy_pwr))
    print("  drift beta@24 p90: relax %.4f -> PWR %.4f  (gate <=0.03 @ sigma_scale=0.165)" % (
        p90_relax, p90_pwr))
    drift_ok = p90_pwr <= 0.03
    improved = vr_pwr < vr_relax - 1e-3
    if drift_ok and improved:
        print("  -> MEASURED front-drive powertrain REDUCES avoidance vx_rmse and KEEPS drift passing "
              "(%.4f<=0.03)." % p90_pwr)
        gap = vr_pwr - 0.235
        print("     Residual avoid vx_rmse %.3f vs drift floor 0.235 (gap %.3f). The fix is the "
              "MEASURED drive axle (front), NOT a tuned drive_scale." % (vr_pwr, gap))
    elif not drift_ok:
        print("  -> WARNING: front-drive change BROKE the drift gate (p90 %.4f > 0.03) -- reject." % p90_pwr)
    else:
        print("  -> front-drive change did NOT reduce avoidance vx_rmse (%.3f vs %.3f)." % (vr_pwr, vr_relax))


if __name__ == "__main__":
    main()
