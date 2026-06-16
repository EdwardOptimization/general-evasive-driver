"""Open-loop divergence gate for the PHYSICS vehicle-dynamics model (physics rewrite).

Replays the saved Chrono drift actions through ``autodrift.gpu_physics`` from the saved
init velocity and compares to ``chrono_v``, using the SAME metric as the residual gate
(``surrogate_train_residual.gate``): beta-divergence @24 steps (mean, p90) and vx RMSE on
a held-out split. Reports the physics model alongside the three baselines:

    analytic single-track  : beta@24 p90 0.138 / vx_rmse 1.097
    grey-box residual (A)  : beta@24 p90 0.038 / vx_rmse 0.083  (target <= 0.03)
    PHYSICS (this module)  : measured here

No live Chrono needed; everything validates against the saved npz. The model is
branchless + batched and runs on cuda with N>=1000 envs (``--bench``).

Usage:
    python scripts/feasibility_audit/surrogate_physics_gate.py            # gate + baselines
    python scripts/feasibility_audit/surrogate_physics_gate.py --calibrate  # quick param search
    python scripts/feasibility_audit/surrogate_physics_gate.py --bench     # cuda N=4096 throughput
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import make_param_batch, analytic_step  # noqa: E402
from autodrift.gpu_physics import (  # noqa: E402
    PhysParams, make_phys_param_batch, physics_step, init_state,
)

DT = 0.02
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"


def load():
    d = np.load(DATA, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)   # (R,T,3)
    V = np.stack(d["chrono_v"]).astype(np.float32)  # (R,T,3) velocity AFTER each step
    init = d["init"].astype(np.float32)             # (R,3) velocity before step 0
    mu = float(d["mu"][0])
    return A, V, init, mu


# ------------------------------------------------------------------ metric (shared form)
def _report(Vt, sur, label, quiet=False):
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    bdiv = (beta_c - beta_s).abs()
    T = Vt.shape[1]
    b24 = bdiv[:, min(23, T - 1)]
    vx_rmse = ((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt()
    p90 = torch.quantile(b24, 0.9)
    if not quiet:
        print("[%-14s] beta_div @24: mean=%.4f p90=%.4f | max-over-traj mean=%.4f | vx_rmse=%.3f" % (
            label, b24.mean(), p90, bdiv.max(1).values.mean(), vx_rmse))
    return float(p90), float(b24.mean()), float(vx_rmse)


# ------------------------------------------------------------------ analytic baseline
def gate_analytic(A, V, init, mu, label="analytic"):
    R, T, _ = A.shape
    P = make_param_batch(VehicleParams(mu=mu, mass=1684.0), R, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(A, device=DEV)
    st = torch.zeros(R, 8, device=DEV)
    st[:, 3:6] = torch.tensor(init, device=DEV)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, _ = analytic_step(st, A_t[:, t, :], P, DT)
            sur[:, t, :] = st[:, 3:6]
    return _report(torch.tensor(V, device=DEV), sur, label)


# ------------------------------------------------------------------ physics gate
def gate_physics(A, V, init, mu, phys: PhysParams, label="physics", quiet=False):
    R, T, _ = A.shape
    P = make_phys_param_batch(phys, R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(A, device=DEV)
    init_t = torch.tensor(init, device=DEV)
    st, gear = init_state(init_t[:, 0], init_t[:, 1], init_t[:, 2], P)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, gear, _ = physics_step(st, A_t[:, t, :], gear, P, DT)
            sur[:, t, 0] = st[:, 3]
            sur[:, t, 1] = st[:, 4]
            sur[:, t, 2] = st[:, 5]
    return _report(torch.tensor(V, device=DEV), sur, label, quiet=quiet)


# ------------------------------------------------------------------ calibration
def calibrate(A, V, init, mu, tr, va):
    """Coarse coordinate search over the few calibration knobs against the train split."""
    # High-impact knobs first (axle balance + stiffness dominate beta; drive/roll/brake set vx).
    grids = {
        "front_grip_scale": [0.5, 0.65, 0.8, 0.95, 1.1],
        "rear_grip_scale": [0.7, 0.85, 1.0, 1.15, 1.3],
        "pac_By": [5.0, 6.5, 8.0, 9.5, 11.0],
        "pac_Dy": [1.1, 1.25, 1.4],
        "pac_Bx": [8.0, 11.0, 14.0],
        "drive_scale": [0.8, 1.0, 1.1, 1.2, 1.35],
        "rolling_resist_coeff": [0.012, 0.02, 0.03, 0.04],
        "max_brake_torque": [1500.0, 2000.0, 3000.0],
        "drag_coeff": [0.2, 0.4, 0.8],
        "k_deg": [0.0, 0.1, 0.2],
        "h_cg_scale": [0.5, 1.0, 1.5],
        "relax_len_r": [0.05, 0.2, 0.4],
    }
    cur = PhysParams()

    # objective: gate metric (beta_mean@24) + small vx_rmse weight, on the train split
    def score(p):
        p90, bmean, vr = gate_physics(A[tr], V[tr], init[tr], mu, p, label="cal", quiet=True)
        return bmean + 0.05 * vr, (p90, bmean, vr)

    cur_obj, cur_stats = score(cur)
    print("  init obj=%.4f (p90=%.4f mean=%.4f vx=%.3f)" % (cur_obj, *cur_stats), flush=True)
    for sweep in range(2):
        improved = False
        for key, vals in grids.items():
            best_local = (cur_obj, getattr(cur, key))
            for v in vals:
                trial = _with(cur, key, v)
                obj, _stats = score(trial)
                if obj < best_local[0] - 1e-5:
                    best_local = (obj, v)
            if best_local[1] != getattr(cur, key):
                improved = True
            setattr(cur, key, best_local[1])
            cur_obj = best_local[0]
        _, st = score(cur)
        print("  sweep %d obj=%.4f (p90=%.4f mean=%.4f vx=%.3f)" % (sweep, cur_obj, *st), flush=True)
        if not improved:
            break
    return cur


def _with(p: PhysParams, key, val):
    kw = {f: getattr(p, f) for f in p.__dataclass_fields__}
    kw[key] = val
    return PhysParams(**kw)


# ------------------------------------------------------------------ thin residual on physics
class _Residual(torch.nn.Module):
    """Tiny MLP correcting the physics per-step {vx,vy,yaw_rate} delta (same idea as the
    grey-box residual, but on top of the PHYSICS model). Quantifies the residual physics misses."""

    def __init__(self, in_dim=8, hidden=64):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(in_dim, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, 3),
        )
        self.register_buffer("im", torch.zeros(in_dim))
        self.register_buffer("istd", torch.ones(in_dim))
        self.register_buffer("om", torch.zeros(3))
        self.register_buffer("ostd", torch.ones(3))

    def setnorm(self, f, t):
        self.im.copy_(f.mean(0)); self.istd.copy_(f.std(0).clamp_min(1e-6))
        self.om.copy_(t.mean(0)); self.ostd.copy_(t.std(0).clamp_min(1e-9))

    def forward(self, f):
        return self.net((f - self.im) / self.istd) * self.ostd + self.om


def _phys_feats(st, action):
    # [vx,vy,yaw_rate, steer, throttle, brake] + [steer_cmd_raw, drive_raw]
    return torch.cat([st[:, 3:9], action[:, :2]], dim=1)


def fit_thin_residual(A, V, init, mu, phys, tr, va):
    """Teacher-forced fit of a thin residual on the physics model, then held-out gate."""
    R, T, _ = A.shape
    # ---- build teacher-forced residual targets on the train split ----
    Atr = A[tr]; Vtr = V[tr]; itr = init[tr]
    Rt = Atr.shape[0]
    P = make_phys_param_batch(phys, Rt, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(Atr, device=DEV); V_t = torch.tensor(Vtr, device=DEV)
    init_t = torch.tensor(itr, device=DEV)
    st, gear = init_state(init_t[:, 0], init_t[:, 1], init_t[:, 2], P)
    feats, targs = [], []
    with torch.no_grad():
        for t in range(T):
            f = _phys_feats(st, A_t[:, t, :])
            nxt, gear, _ = physics_step(st, A_t[:, t, :], gear, P, DT)
            feats.append(f)
            targs.append(V_t[:, t, :] - nxt[:, 3:6])  # chrono_next - phys_next
            # teacher force: set velocity to chrono truth for next step
            st = nxt.clone()
            st[:, 3:6] = V_t[:, t, :]
    F = torch.cat(feats, 0); Tg = torch.cat(targs, 0)
    mlp = _Residual().to(DEV); mlp.setnorm(F, Tg)
    opt = torch.optim.Adam(mlp.parameters(), lr=1e-3)
    n = F.shape[0]; perm = torch.randperm(n, device=DEV)
    for ep in range(400):
        opt.zero_grad()
        b = perm[(ep * 4096) % n: (ep * 4096) % n + 4096]
        loss = torch.nn.functional.huber_loss(mlp(F[b]), Tg[b], delta=0.03)
        loss.backward(); opt.step()

    # ---- free-running held-out gate WITH the residual ----
    Ava = A[va]; Vva = V[va]; iva = init[va]
    Rv = Ava.shape[0]
    Pv = make_phys_param_batch(phys, Rv, mu=mu, device=DEV, dtype=torch.float32)
    Av = torch.tensor(Ava, device=DEV)
    iv = torch.tensor(iva, device=DEV)
    stv, gv = init_state(iv[:, 0], iv[:, 1], iv[:, 2], Pv)
    sur = torch.zeros(Rv, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            f = _phys_feats(stv, Av[:, t, :])
            stv, gv, _ = physics_step(stv, Av[:, t, :], gv, Pv, DT)
            stv = stv.clone()
            stv[:, 3:6] = stv[:, 3:6] + mlp(f)
            sur[:, t, :] = stv[:, 3:6]
    # residual magnitude diagnostic
    res_rms = float((Tg ** 2).mean().sqrt())
    return _report(torch.tensor(Vva, device=DEV), sur, "physics+residual"), res_rms


# ------------------------------------------------------------------ throughput bench
def bench(n=4096):
    if not torch.cuda.is_available():
        print("[bench] cuda not available; skipping")
        return
    phys = PhysParams()
    P = make_phys_param_batch(phys, n, mu=0.48, device="cuda", dtype=torch.float32)
    vx0 = torch.full((n,), 9.0, device="cuda")
    vy0 = torch.full((n,), 1.5, device="cuda")
    yaw0 = torch.full((n,), 0.15, device="cuda")
    st, gear = init_state(vx0, vy0, yaw0, P)
    act = torch.zeros(n, 3, device="cuda")
    act[:, 0] = -0.2
    act[:, 1] = -0.1
    torch.cuda.synchronize()
    t0 = time.time()
    steps = 200
    with torch.no_grad():
        for _ in range(steps):
            st, gear, _ = physics_step(st, act, gear, P, DT)
    torch.cuda.synchronize()
    dt = time.time() - t0
    assert torch.isfinite(st).all(), "non-finite state in bench"
    print("[bench] N=%d, %d steps in %.3fs -> %.1f Msteps/s, finite=%s" % (
        n, steps, dt, n * steps / dt / 1e6, bool(torch.isfinite(st).all())))


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--residual", action="store_true", help="also fit a thin residual on physics")
    args = ap.parse_args()

    A, V, init, mu = load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    tr, va = idx[:130], idx[130:]

    print("device=%s  mu=%.3f  rollouts=%d  T=%d" % (DEV, mu, A.shape[0], A.shape[1]))
    print("=== baselines (held-out split) ===")
    gate_analytic(A[va], V[va], init[va], mu, label="analytic")
    print("  grey-box residual (ref): beta@24 p90~0.038 mean~0.016 vx_rmse~0.083")

    if args.calibrate:
        print("=== calibrating physics params on train split ===")
        phys = calibrate(A, V, init, mu, tr, va)
        tuned = ("front_grip_scale", "rear_grip_scale", "pac_By", "pac_Bx", "pac_Dy",
                 "pac_Dx", "drive_scale", "h_cg_scale", "k_deg", "max_brake_torque",
                 "rolling_resist_coeff", "drag_coeff", "relax_len_f", "relax_len_r")
        print("calibrated:", {k: round(float(getattr(phys, k)), 4) for k in tuned})
    else:
        phys = PhysParams()

    print("=== PHYSICS model (held-out split) ===")
    p90, bmean, vr = gate_physics(A[va], V[va], init[va], mu, phys, label="physics")
    print("\nGATE wants p90 beta_div@24 <= 0.03. physics p90 = %.4f -> %s" % (
        p90, "PASS" if p90 <= 0.03 else "above 0.03"))

    if args.residual:
        print("=== PHYSICS + thin learned residual (held-out split) ===")
        (rp90, rmean, rvr), res_rms = fit_thin_residual(A, V, init, mu, phys, tr, va)
        print("  thin-residual target RMS (per-step vel delta the physics misses): %.4f" % res_rms)
        print("  physics+residual p90 = %.4f -> %s" % (rp90, "PASS" if rp90 <= 0.03 else "above 0.03"))

    if args.bench:
        print("=== cuda throughput (N=4096) ===")
        bench(4096)


if __name__ == "__main__":
    main()
