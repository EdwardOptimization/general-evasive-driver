"""DIAGNOSTIC: is BRAKING the dominant lever for the avoidance vx_rmse gap?

The faithful L1 rewrite (gpu_physics_relax) predicts the avoidance collision boundary at
bal-acc 0.665 (beats grey-box 0.503) but is limited by vx_rmse 1.31 on avoidance (vs 0.235 on
drift), localised to the braking/longitudinal physics. This sweeps the powertrain longitudinal
params on the SAME A6.2 avoid-boundary replay and reports avoidance vx_rmse + collision bal-acc:

  - max_brake_torque sweep {2000,3000,4500,6000,8000,10000} N.m/wheel
  - drive_scale sweep (throttle/engine response contribution)
  - the gpu_physics_brake model (all-4-wheel braking, the MEASURED Chrono behaviour) for comparison:
    gpu_physics_relax brakes ONLY the 2 rear wheels (front sx=0 => no front brake force); the real
    Chrono Sedan brakes ALL 4 wheels at 2000 N.m each (extract_chrono_brake.py).

BATCHED over all 320 rollouts on GPU (pad to max T, mask by valid length) -- the per-rollout python
loop was too slow on CPU. This is a READ-ONLY diagnostic; it does NOT modify any gate or model.

    python scripts/feasibility_audit/surrogate_avoid_brake_diagnostic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_physics_relax import (  # noqa: E402  L1 (rear-only brake)
    PhysParams as RelaxParams, make_phys_param_batch as relax_batch,
    physics_step as relax_step, init_state as relax_init,
)

DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_boundary.npz"
SIGMA_SCALE = 0.165  # same contact-patch sigma the A6.2 gate uses
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def _load_batched():
    """Load + pad the avoid-boundary rollouts to [R, Tmax] tensors with a valid-length mask."""
    d = np.load(DATA, allow_pickle=True)
    pk = [str(k) for k in d["param_keys"]]
    A_l, S_l, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    R = len(A_l)
    lens = np.array([min(len(np.asarray(A_l[i])), len(np.asarray(S_l[i]))) for i in range(R)])
    Tmax = int(lens.max())
    A = np.zeros((R, Tmax, 3), np.float32)
    Sx = np.zeros((R, Tmax), np.float32)        # chrono vx
    for i in range(R):
        T = lens[i]
        A[i, :T] = np.asarray(A_l[i])[:T, :3]
        Sx[i, :T] = np.asarray(S_l[i])[:T, 3]
    mu = np.array([float(params[i][pk.index("mu")]) for i in range(R)], np.float32)
    pv0 = lambda k: float(params[0][pk.index(k)])  # noqa: E731
    meta = dict(
        R=R, Tmax=Tmax, lens=lens, init=init.astype(np.float32),
        crash_c=d["collision_any"].astype(bool),
        ox=d["obs_x"].astype(np.float32), oy=d["obs_y"].astype(np.float32),
        ehw=d["ego_half_width"].astype(np.float32), ohw=d["obs_half_width"].astype(np.float32),
        mass=pv0("mass"), iz=pv0("iz"), lf=pv0("lf"), lr=pv0("lr"),
    )
    return torch.tensor(A), torch.tensor(Sx), torch.tensor(mu), meta


def _eval_batched(make_batch, init_fn, step_fn, ParamCls, A, Sx, mu, meta, **overrides):
    """Batched replay over all R rollouts on DEV; return (vx_rmse, bal_acc, agree)."""
    R, Tmax = meta["R"], meta["Tmax"]
    lens = torch.tensor(meta["lens"], device=DEV)
    phys = ParamCls(mass=meta["mass"], izz=meta["iz"], wheelbase=2.776,
                    front_axle_share=meta["lr"] / (meta["lf"] + meta["lr"]),
                    sigma_scale=SIGMA_SCALE, **overrides)
    mu_t = mu.to(DEV)
    P = make_batch(phys, R, mu=mu_t, device=DEV, dtype=torch.float32)
    v = torch.tensor(meta["init"], device=DEV)
    st, gear = init_fn(v[:, 3], v[:, 4], v[:, 5], P)
    st = st.clone()
    st[:, 0], st[:, 1], st[:, 2] = v[:, 0], v[:, 1], v[:, 2]
    A_t = A.to(DEV); Sx_t = Sx.to(DEV)
    ox = torch.tensor(meta["ox"], device=DEV); oy = torch.tensor(meta["oy"], device=DEV)
    tidx = torch.arange(Tmax, device=DEV)
    valid = (tidx[None, :] < lens[:, None])           # [R, Tmax]
    mind = torch.full((R,), 1e9, device=DEV)
    se_sum = torch.zeros(R, device=DEV)
    with torch.no_grad():
        for t in range(Tmax):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, 0.02)
            vm = valid[:, t]
            clr = torch.hypot(ox - st[:, 0], oy - st[:, 1])
            mind = torch.where(vm, torch.minimum(mind, clr), mind)
            se_sum = se_sum + vm.float() * (st[:, 3] - Sx_t[:, t]) ** 2
    vx_rmse = float(torch.sqrt(se_sum.sum() / valid.float().sum()))
    ehw = torch.tensor(meta["ehw"], device=DEV); ohw = torch.tensor(meta["ohw"], device=DEV)
    crash_s = (mind <= (ehw + ohw)).cpu().numpy()
    crash_c = meta["crash_c"]
    tp = int((crash_s & crash_c).sum()); tn = int((~crash_s & ~crash_c).sum())
    fp = int((crash_s & ~crash_c).sum()); fn = int((~crash_s & crash_c).sum())
    bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
    return vx_rmse, bal, (tp + tn) / R


def main():
    A, Sx, mu, meta = _load_batched()
    print("device=%s  A6.2 avoid-boundary diagnostic: R=%d Tmax=%d Chrono crashes=%d/%d sigma_scale=%.3f"
          % (DEV, meta["R"], meta["Tmax"], int(meta["crash_c"].sum()), meta["R"], SIGMA_SCALE))
    print("baseline (L1 gpu_physics_relax, REAR-ONLY brake, max_brake_torque=2000): "
          "vx_rmse 1.31 / bal-acc 0.665 (published)\n")

    print("=== (1) max_brake_torque sweep — L1 gpu_physics_relax (REAR-only brake) ===")
    print("  the model brakes only the 2 rear wheels; raising per-wheel torque is the rear-only lever")
    print("  %-12s %-10s %-10s %-8s" % ("brake_torque", "vx_rmse", "bal_acc", "agree"))
    for bt in (2000, 3000, 4500, 6000, 8000, 10000):
        vr, bal, ag = _eval_batched(relax_batch, relax_init, relax_step, RelaxParams,
                                    A, Sx, mu, meta, max_brake_torque=float(bt))
        print("  %-12d %-10.3f %-10.3f %-8.3f" % (bt, vr, bal, ag))

    print("\n=== (2) drive_scale sweep — throttle/engine longitudinal response ===")
    print("  %-12s %-10s %-10s %-8s" % ("drive_scale", "vx_rmse", "bal_acc", "agree"))
    for ds in (0.5, 0.75, 1.0, 1.25, 1.5):
        vr, bal, ag = _eval_batched(relax_batch, relax_init, relax_step, RelaxParams,
                                    A, Sx, mu, meta, drive_scale=float(ds))
        print("  %-12.2f %-10.3f %-10.3f %-8.3f" % (ds, vr, bal, ag))

    # (3) all-4-wheel braking (the measured Chrono behaviour) via gpu_physics_brake, if present.
    try:
        from autodrift.gpu_physics_brake import (  # noqa: E402
            PhysParams as BrakeParams, make_phys_param_batch as brake_batch,
            physics_step as brake_step, init_state as brake_init,
        )
        print("\n=== (3) ALL-4-WHEEL braking (MEASURED Chrono) — gpu_physics_brake ===")
        print("  measured max_brake_torque=2000 N.m/wheel applied to ALL 4 wheels (front+rear)")
        print("  %-12s %-10s %-10s %-8s" % ("brake_torque", "vx_rmse", "bal_acc", "agree"))
        for bt in (2000, 3000, 4500, 6000):
            vr, bal, ag = _eval_batched(brake_batch, brake_init, brake_step, BrakeParams,
                                        A, Sx, mu, meta, max_brake_torque=float(bt))
            tag = "  <- MEASURED" if bt == 2000 else ""
            print("  %-12d %-10.3f %-10.3f %-8.3f%s" % (bt, vr, bal, ag, tag))
    except Exception as e:  # noqa: BLE001
        print("\n(3) gpu_physics_brake not importable yet (%s) — build it then re-run." % e)


if __name__ == "__main__":
    main()
