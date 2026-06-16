"""Train the grey-box residual (single-track + learned residual) on the collected Chrono drift
data and re-run the M1 open-loop divergence gate vs the analytic-only baseline.

Phase A: teacher-forced single-step residual = chrono_next_vel - analytic_next_vel, MLP fit.
Phase B (if A insufficient): multi-step free-running unroll to fight compounding on the saddle.
Gate: open-loop divergence of the grey-box vs Chrono on held-out rollouts (beta@24, vx RMSE).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import (  # noqa: E402
    make_param_batch, analytic_step, grey_box_step, residual_features, ResidualDynamicsMLP,
)

DT = 0.02
DEV = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_default_dtype(torch.float32)
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"


def load():
    d = np.load(DATA, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)        # (R,T,3)
    V = np.stack(d["chrono_v"]).astype(np.float32)       # (R,T,3) velocity AFTER each step
    init = d["init"].astype(np.float32)                  # (R,3) velocity before step 0
    mu = float(d["mu"][0])
    return A, V, init, mu


def reconstruct(A, V, init, P):
    """Vectorised over rollouts: returns per-step (feat[R,T,8], target_resid[R,T,3], analytic_next_vel)."""
    R, T, _ = A.shape
    cur = np.concatenate([init[:, None, :], V[:, :-1, :]], axis=1)  # current vel at each step
    A_t = torch.tensor(A, device=DEV); cur_t = torch.tensor(cur, device=DEV); V_t = torch.tensor(V, device=DEV)
    steer = torch.zeros(R, device=DEV); drive = torch.zeros(R, device=DEV)
    feats, targs = [], []
    for t in range(T):
        st = torch.zeros(R, 8, device=DEV)
        st[:, 3:6] = cur_t[:, t, :]; st[:, 6] = steer; st[:, 7] = drive
        nxt, _ = analytic_step(st, A_t[:, t, :], P, DT)
        feats.append(residual_features(st, A_t[:, t, :]))
        targs.append(V_t[:, t, :] - nxt[:, 3:6])  # residual = chrono_next - analytic_next
        steer, drive = nxt[:, 6], nxt[:, 7]
    return torch.stack(feats, 1), torch.stack(targs, 1)  # (R,T,8),(R,T,3)


def gate(A, V, init, P, mlp=None, label=""):
    """Open-loop divergence of analytic (mlp=None) or grey-box vs Chrono, per rollout."""
    R, T, _ = A.shape
    A_t = torch.tensor(A, device=DEV)
    st = torch.zeros(R, 8, device=DEV); st[:, 3:6] = torch.tensor(init, device=DEV)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, _ = (grey_box_step(st, A_t[:, t, :], P, DT, mlp) if mlp is not None
                     else analytic_step(st, A_t[:, t, :], P, DT))
            sur[:, t, :] = st[:, 3:6]
    Vt = torch.tensor(V, device=DEV)
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    bdiv = (beta_c - beta_s).abs()
    b24 = bdiv[:, min(23, T - 1)]
    vx_rmse = ((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt()
    print("[%s] beta_div @24: mean=%.4f p90=%.4f | max-over-traj mean=%.4f | vx_rmse=%.3f" % (
        label, b24.mean(), torch.quantile(b24, 0.9), bdiv.max(1).values.mean(), vx_rmse))
    return float(torch.quantile(b24, 0.9))


def main():
    A, V, init, mu = load()
    P = make_param_batch(VehicleParams(mu=mu, mass=1684.0), A.shape[0], device=DEV, dtype=torch.float32)
    rng = np.random.default_rng(0); idx = rng.permutation(A.shape[0])
    tr, va = idx[:130], idx[130:]

    print("=== baseline: analytic single-track (held-out) ===")
    Pva = make_param_batch(VehicleParams(mu=mu, mass=1684.0), len(va), device=DEV, dtype=torch.float32)
    gate(A[va], V[va], init[va], Pva, mlp=None, label="analytic")

    # Phase A: single-step residual
    feats, targs = reconstruct(A[tr], V[tr], init[tr], make_param_batch(VehicleParams(mu=mu, mass=1684.0), len(tr), device=DEV, dtype=torch.float32))
    F = feats.reshape(-1, 8); Tg = targs.reshape(-1, 3)
    mlp = ResidualDynamicsMLP().to(DEV); mlp.set_norm(F, Tg)
    opt = torch.optim.Adam(mlp.parameters(), lr=1e-3)
    n = F.shape[0]; perm = torch.randperm(n, device=DEV)
    print("=== Phase A: single-step residual (%d transitions) ===" % n)
    for ep in range(300):
        opt.zero_grad()
        b = perm[(ep * 4096) % n: (ep * 4096) % n + 4096]
        loss = torch.nn.functional.huber_loss(mlp(F[b]), Tg[b], delta=0.05)
        loss.backward(); opt.step()
        if ep % 60 == 0:
            print("  ep %d huber %.5f" % (ep, float(loss)))
    print("=== grey-box (analytic + Phase-A residual) held-out gate ===")
    p90 = gate(A[va], V[va], init[va], Pva, mlp=mlp, label="grey-box A")

    torch.save(mlp.state_dict(), ROOT / "runs/feasibility_audit/phase4_f2/residual_mlp_phaseA.pt")
    print("\nGATE wants p90 beta_div@24 <= 0.03. grey-box A p90 = %.4f -> %s" % (
        p90, "PASS" if p90 <= 0.03 else "needs Phase B unroll"))


if __name__ == "__main__":
    main()
