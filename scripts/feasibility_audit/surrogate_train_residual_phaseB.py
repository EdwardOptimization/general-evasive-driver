"""A1.i — Phase B: multi-step free-running unroll. Phase A fit the residual single-step
(teacher-forced); compounding over the 24-step sustain horizon leaves beta@24 p90=0.029 (passes
the 0.03 gate but above the aspirational 0.02) and drives some drift-success sustain-breaks. Here
we fine-tune the Phase-A residual by backprop through a differentiable K-step grey-box unroll
(loss on the free-running velocity trajectory vs Chrono), which directly penalises compounding.

Self-contained / conflict-free (loads Phase-A weights, saves residual_mlp_phaseB.pt; does not edit
the Phase-A trainer). Reports the open-loop gate before/after on the held-out split.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import make_param_batch, grey_box_step, ResidualDynamicsMLP  # noqa: E402

DT = 0.02
DEV = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_default_dtype(torch.float32)
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"
PHASE_A = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseA.pt"
PHASE_B = ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseB.pt"
HORIZON = 48  # unroll depth for BPTT (covers the 24-step sustain + margin)


def load():
    d = np.load(DATA, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    return A, V, init, float(d["mu"][0])


def unroll(A, V, init, P, mlp, horizon, grad=True):
    """Free-running grey-box unroll; returns (loss, sur_traj[R,T,3])."""
    R, T, _ = A.shape
    H = min(horizon, T)
    st = torch.zeros(R, 8, device=DEV); st[:, 3:6] = torch.tensor(init, device=DEV)
    A_t, V_t = torch.tensor(A, device=DEV), torch.tensor(V, device=DEV)
    loss = torch.zeros((), device=DEV); traj = []
    ctx = torch.enable_grad() if grad else torch.no_grad()
    with ctx:
        for t in range(H):
            st, _ = grey_box_step(st, A_t[:, t, :], P, DT, mlp)
            loss = loss + torch.nn.functional.huber_loss(st[:, 3:6], V_t[:, t, :], delta=0.05)
            traj.append(st[:, 3:6].detach())
    return loss / H, torch.stack(traj, 1)


def gate(A, V, init, P, mlp, label):
    R, T, _ = A.shape
    st = torch.zeros(R, 8, device=DEV); st[:, 3:6] = torch.tensor(init, device=DEV)
    A_t = torch.tensor(A, device=DEV); sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, _ = grey_box_step(st, A_t[:, t, :], P, DT, mlp); sur[:, t, :] = st[:, 3:6]
    Vt = torch.tensor(V, device=DEV)
    bc = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6); bs = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    b24 = (bc - bs).abs()[:, min(23, T - 1)]
    vx_rmse = ((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt()
    p90 = float(torch.quantile(b24, 0.9))
    print(f"  [{label:16s}] beta@24 p90={p90:.4f} mean={float(b24.mean()):.4f} vx_rmse={float(vx_rmse):.3f}")
    return p90


def main():
    A, V, init, mu = load()
    rng = np.random.default_rng(0); idx = rng.permutation(A.shape[0]); tr, va = idx[:130], idx[130:]
    Pva = make_param_batch(VehicleParams(mu=mu, mass=1684.0), len(va), device=DEV, dtype=torch.float32)
    Ptr = make_param_batch(VehicleParams(mu=mu, mass=1684.0), len(tr), device=DEV, dtype=torch.float32)

    mlp = ResidualDynamicsMLP().to(DEV); mlp.load_state_dict(torch.load(PHASE_A, map_location=DEV))
    print("=== held-out open-loop gate ===")
    gate(A[va], V[va], init[va], Pva, mlp, "phase A")

    opt = torch.optim.Adam(mlp.parameters(), lr=3e-4)
    print(f"=== Phase B: {HORIZON}-step unroll fine-tune (130 train rollouts) ===")
    for ep in range(120):
        opt.zero_grad()
        loss, _ = unroll(A[tr], V[tr], init[tr], Ptr, mlp, HORIZON, grad=True)
        loss.backward(); torch.nn.utils.clip_grad_norm_(mlp.parameters(), 5.0); opt.step()
        if ep % 30 == 0:
            print(f"  ep {ep} unroll_huber {float(loss.detach()):.5f}")

    p90 = gate(A[va], V[va], init[va], Pva, mlp, "phase B")
    torch.save(mlp.state_dict(), PHASE_B)
    print(f"saved {PHASE_B}")
    print(f"\nA1.i aspirational: beta@24 p90 <= 0.02. phase B p90 = {p90:.4f} -> "
          f"{'PASS' if p90 <= 0.02 else 'tighter than A (0.029) but >0.02' if p90 < 0.029 else 'no gain'}")


if __name__ == "__main__":
    main()
