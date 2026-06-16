"""BRAKE-fix verdict gate: does fixing the MEASURED braking powertrain close the avoidance
vx_rmse gap WITHOUT breaking drift?

Runs BOTH gates on ``autodrift.gpu_physics_brake`` (the L1 RELAX-TMeasy model with the MEASURED
Chrono Sedan brake applied to ALL FOUR wheels, vs gpu_physics_relax which braked only the rear 2):

  (A) AVOID-BOUNDARY collision gate — replays the 320 crash-boundary rollouts
      (surrogate_avoid_boundary.npz) through gpu_physics_brake re-parameterised for the avoid
      vehicle (mass=1450, izz=2300, front_share, Sedan wheelbase/steer/tyre), and reports
      vx_rmse + collision bal-acc. Baseline (gpu_physics_relax, rear-only brake): 1.31 / 0.665.

  (B) DRIFT gate — replays the held-out drift rollouts (surrogate_drift_data.npz) through
      gpu_physics_brake and reports beta@24 p90 (must still PASS ~0.0295 -- the brake change
      must not break drift, since drift is throttle-on / low-brake).

This gate does NOT modify gpu_physics_relax, its gate, or any other model/gate -- it imports them
read-only for the side-by-side baselines.

    python scripts/feasibility_audit/surrogate_physics_brake_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_brake import (  # noqa: E402  the BRAKE-fixed model
    PhysParams as BrakeParams, make_phys_param_batch as brake_batch,
    physics_step as brake_step, init_state as brake_init,
)
from autodrift.gpu_physics_relax import (  # noqa: E402  the L1 baseline (rear-only brake)
    PhysParams as RelaxParams, make_phys_param_batch as relax_batch,
    physics_step as relax_step, init_state as relax_init,
)

AVOID = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_boundary.npz"
DRIFT = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
SIGMA_SCALE = 0.165   # SAME contact-patch sigma as the A6.2 avoid-boundary gate
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DT = 0.02


# ----------------------------------------------------------------- (A) avoid-boundary collision gate
def avoid_gate(make_batch, init_fn, step_fn, ParamCls, label):
    d = np.load(AVOID, allow_pickle=True)
    A, S, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    pk = [str(k) for k in d["param_keys"]]
    crash_c = d["collision_any"].astype(bool)
    ox, oy, ehw, ohw = d["obs_x"], d["obs_y"], d["ego_half_width"], d["obs_half_width"]
    R = len(A)
    p0 = params[0]
    pv = lambda k: float(p0[pk.index(k)])  # noqa: E731
    lf, lr = pv("lf"), pv("lr")
    phys = ParamCls(mass=pv("mass"), izz=pv("iz"), wheelbase=2.776,
                    front_axle_share=lr / (lf + lr), sigma_scale=SIGMA_SCALE)
    crash_s = np.zeros(R, bool)
    vx_se = []
    for i in range(R):
        mu = float(params[i][pk.index("mu")])
        P = make_batch(phys, 1, mu=mu, device="cpu", dtype=torch.float32)
        v = init[i].astype(np.float32)
        st, gear = init_fn(torch.tensor([v[3]]), torch.tensor([v[4]]), torch.tensor([v[5]]), P)
        st = st.clone(); st[0, 0], st[0, 1], st[0, 2] = float(v[0]), float(v[1]), float(v[2])
        Ai = torch.tensor(A[i].astype(np.float32)); ch = S[i]; mind = 1e9
        T = min(len(Ai), len(ch))
        with torch.no_grad():
            for t in range(T):
                st, gear, _ = step_fn(st, Ai[t:t + 1], gear, P, DT)
                mind = min(mind, float(np.hypot(ox[i] - float(st[0, 0]), oy[i] - float(st[0, 1]))))
                vx_se.append((float(st[0, 3]) - ch[t, 3]) ** 2)
        crash_s[i] = mind <= (ehw[i] + ohw[i])
    vx_rmse = float(np.sqrt(np.mean(vx_se)))
    tp = int((crash_s & crash_c).sum()); tn = int((~crash_s & ~crash_c).sum())
    fp = int((crash_s & ~crash_c).sum()); fn = int((~crash_s & crash_c).sum())
    bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
    print("  [%-22s] vx_rmse=%.3f  bal_acc=%.3f  agree=%.3f  (TP=%d TN=%d FP=%d FN=%d)" % (
        label, vx_rmse, bal, (tp + tn) / R, tp, tn, fp, fn))
    return vx_rmse, bal


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
    va = idx[130:]                              # SAME held-out split as the relax/tmeasy gates
    Av, Vv, iv = A[va], V[va], init[va]
    R, T, _ = Av.shape
    P = make_batch(ParamCls(), R, mu=mu, device=DEV, dtype=torch.float32)
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
    print("  [%-22s] beta@24 p90=%.4f  mean=%.4f  vx_rmse=%.3f" % (
        label, p90, float(b24.mean()), vx_rmse))
    return p90


def main():
    print("=== (A) AVOID-BOUNDARY collision gate (sigma_scale=%.3f) ===" % SIGMA_SCALE)
    print("  baseline gpu_physics_relax (rear-only brake): vx_rmse 1.31 / bal-acc 0.665 (published)")
    vr_relax, bal_relax = avoid_gate(relax_batch, relax_init, relax_step, RelaxParams,
                                     "relax rear-only brake")
    vr_brake, bal_brake = avoid_gate(brake_batch, brake_init, brake_step, BrakeParams,
                                     "BRAKE measured 4-wheel")

    print("\n=== (B) DRIFT gate (held-out split; must still PASS ~0.0295) ===")
    print("  baseline gpu_physics_relax: beta@24 p90 ~0.0295 (PASSES)")
    p90_relax = drift_gate(relax_batch, relax_init, relax_step, RelaxParams, "relax (baseline)")
    p90_brake = drift_gate(brake_batch, brake_init, brake_step, BrakeParams, "BRAKE-fixed")

    print("\n=== VERDICT ===")
    print("  avoidance vx_rmse: relax %.3f -> brake %.3f  (drift floor 0.235)" % (vr_relax, vr_brake))
    print("  avoidance bal-acc: relax %.3f -> brake %.3f  (target 0.75+)" % (bal_relax, bal_brake))
    print("  drift beta@24 p90: relax %.4f -> brake %.4f  (gate <=0.03)" % (p90_relax, p90_brake))
    drift_ok = p90_brake <= 0.03
    improved = vr_brake < vr_relax - 1e-3
    if drift_ok and improved:
        print("  -> MEASURED brake REDUCES avoidance vx_rmse and KEEPS drift passing (%.4f<=0.03)." % p90_brake)
    elif not drift_ok:
        print("  -> WARNING: brake change BROKE the drift gate (p90 %.4f > 0.03) -- reject." % p90_brake)
    else:
        print("  -> brake change did NOT reduce avoidance vx_rmse (%.3f vs %.3f)." % (vr_brake, vr_relax))


if __name__ == "__main__":
    main()
