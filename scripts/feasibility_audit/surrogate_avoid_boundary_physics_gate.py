"""A6.2 — the avoid-fix convergence test: does the FAITHFUL PHYSICS REWRITE (L1, exact tyre +
relaxation) predict the avoidance COLLISION boundary, where the grey-box was at chance (bal-acc
0.503, caught 2/50)? If yes, the rewrite is the collision-faithful surrogate the avoid-fix needs.

Re-parameterises gpu_physics_relax for the avoidance vehicle (Chrono overrides mass=1450, izz=2300,
CG via lf/lr — chrono_vehicle_backend.py:644-650; keeps the Sedan wheelbase/steer/tyre), replays the
crash-boundary actions from the recorded init pose, computes min clearance to the obstacle on the
physics pose trajectory, and compares the collision outcome to Chrono.

Reports vx_rmse first as a PARAMETERISATION SANITY CHECK (is the physics correctly set up for the
avoid vehicle?) before the collision bal-acc.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)
from autodrift.gpu_physics_relax import PhysParams, make_phys_param_batch, physics_step, init_state  # noqa: E402

DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_avoid_boundary.npz"
SIGMA_SCALE = 0.165  # contact-patch-scale physical relaxation (= measured contact length, principled)


def main():
    d = np.load(DATA, allow_pickle=True)
    A, S, init, params = d["actions"], d["chrono_state"], d["init"], d["params"]
    pk = [str(k) for k in d["param_keys"]]
    crash_c = d["collision_any"].astype(bool)
    ox, oy, ehw, ohw = d["obs_x"], d["obs_y"], d["ego_half_width"], d["obs_half_width"]
    R = len(A)
    p0 = params[0]
    def pv(k):
        return float(p0[pk.index(k)])
    lf, lr = pv("lf"), pv("lr")
    # avoidance vehicle: Chrono overrides total mass + yaw inertia + CG (front share); Sedan keeps its
    # fixed wheelbase 2.776, RackPinion max steer 0.43633, and TMeasy tyre (the sampled curves).
    phys = PhysParams(mass=pv("mass"), izz=pv("iz"), wheelbase=2.776,
                      front_axle_share=lr / (lf + lr), sigma_scale=SIGMA_SCALE)
    print(f"A6.2 physics on avoidance: mass={pv('mass')} izz={pv('iz')} front_share={lr/(lf+lr):.3f} "
          f"sigma_scale={SIGMA_SCALE} (sigma=contact length); R={R}, Chrono crashes={int(crash_c.sum())}/{R}")

    crash_s = np.zeros(R, bool)
    vx_se = []
    for i in range(R):
        mu = float(params[i][pk.index("mu")])
        P = make_phys_param_batch(phys, 1, mu=mu, device="cpu", dtype=torch.float32)
        v = init[i].astype(np.float32)
        st, gear = init_state(torch.tensor([v[3]]), torch.tensor([v[4]]), torch.tensor([v[5]]), P)
        st = st.clone(); st[0, 0], st[0, 1], st[0, 2] = float(v[0]), float(v[1]), float(v[2])
        Ai = torch.tensor(A[i].astype(np.float32)); ch = S[i]; mind = 1e9
        T = min(len(Ai), len(ch))
        with torch.no_grad():
            for t in range(T):
                st, gear, _ = physics_step(st, Ai[t:t+1], gear, P, 0.02)
                mind = min(mind, float(np.hypot(ox[i] - float(st[0, 0]), oy[i] - float(st[0, 1]))))
                vx_se.append((float(st[0, 3]) - ch[t, 3]) ** 2)
        crash_s[i] = mind <= (ehw[i] + ohw[i])

    vx_rmse = float(np.sqrt(np.mean(vx_se)))
    tp = int((crash_s & crash_c).sum()); tn = int((~crash_s & ~crash_c).sum())
    fp = int((crash_s & ~crash_c).sum()); fn = int((~crash_s & crash_c).sum())
    bal = 0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1))
    print(f"\n  [parameterisation sanity] vx_rmse={vx_rmse:.3f}  (grey-box avoid ~1.05; analytic ~1.57)")
    print(f"  [collision prediction] bal_acc={bal:.3f} agree={(tp+tn)/R:.3f} "
          f"TP={tp} TN={tn} FP={fp} FN={fn}")
    print(f"\n  vs grey-box collision bal_acc 0.503 (caught 2/50) / analytic 0.713:")
    if bal >= 0.75:
        print(f"  -> PHYSICS REWRITE is collision-faithful (bal_acc {bal:.3f}). The convergence holds: it IS "
              f"the avoid-fix surrogate. Next: re-train the GPU policy on it, re-run A5.")
    elif bal >= 0.60:
        print(f"  -> partial ({bal:.3f}): better than grey-box but not yet collision-faithful; check param/L2.")
    else:
        print(f"  -> not yet ({bal:.3f}): the rewrite alone doesn't nail the boundary; needs L2 (suspension) "
              f"or the parameterisation/tyre-load range needs work.")


if __name__ == "__main__":
    main()
