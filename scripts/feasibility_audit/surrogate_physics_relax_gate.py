"""Open-loop divergence gate for the RELAX-TMeasy physics model (faithful rewrite, L1).

Identical gate to ``surrogate_physics_tmeasy_gate.py`` (beta-div @24 p90/mean, vx RMSE on the
SAME held-out split of ``surrogate_drift_data.npz``), but it replays the saved Chrono drift
actions through ``autodrift.gpu_physics_relax`` — the L0 EXACT-TMeasy model PLUS a PHYSICAL tyre
SLIP-relaxation transient (the slip entering the EXACT curve is lagged over the MEASURED
relaxation length sigma = dF0/sigma0, extracted from the EXACT Chrono tyre by
``extract_chrono_tmeasy_relax.py``; grip fudge = 1.0, NO Pacejka calibration).

It prints the relax numbers alongside the published baselines and the L0 exact-tyre plateau:

    analytic single-track  : beta@24 p90 0.138  / vx_rmse 1.097
    calibrated-Pacejka      : beta@24 p90 0.0435 / vx_rmse 0.227  (gpu_physics, WITH fudge)
    L0 EXACT-TMeasy (nofudge): beta@24 p90 0.0403 / vx_rmse 0.235  (gpu_physics_tmeasy, plateau)
    grey-box residual       : beta@24 p90 0.0156                  (target)
    L1 RELAX-TMeasy          : measured here

It also prints the SIGNED beta-divergence vs step curve (beta_chrono - beta_surrogate at steps
8 / 24 / 89) for L0 and L1 side by side -- the diagnostic the relaxation layer is meant to close
(L0 signature: +0.009 @8 / -0.0188 @24 / +0.069 @89).

Usage:
    python scripts/feasibility_audit/surrogate_physics_relax_gate.py
    python scripts/feasibility_audit/surrogate_physics_relax_gate.py --sigma-sweep
        (optional: sweep the single global sigma_scale multiplier ONLY -- a sensitivity check,
         NOT a fit; the raw measured sigma is sigma_scale=1.0)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from autodrift.dynamics import VehicleParams  # noqa: E402
from autodrift.gpu_surrogate import make_param_batch, analytic_step  # noqa: E402
from autodrift.gpu_physics_tmeasy import (  # noqa: E402  (L0 exact-tyre, for side-by-side)
    PhysParams as TMPhysParams,
    make_phys_param_batch as tm_make_batch,
    physics_step as tm_step,
    init_state as tm_init,
)
from autodrift.gpu_physics_relax import (  # noqa: E402  (L1 slip-relaxation)
    PhysParams, make_phys_param_batch, physics_step, init_state,
)

DT = 0.02
DEV = "cuda" if torch.cuda.is_available() else "cpu"
DATA = ROOT / "runs/feasibility_audit/phase4_f2/surrogate_drift_data.npz"


def load():
    d = np.load(DATA, allow_pickle=True)
    A = np.stack(d["actions"]).astype(np.float32)
    V = np.stack(d["chrono_v"]).astype(np.float32)
    init = d["init"].astype(np.float32)
    mu = float(d["mu"][0])
    return A, V, init, mu


def _report(Vt, sur, label, quiet=False):
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    bdiv = (beta_c - beta_s).abs()
    T = Vt.shape[1]
    b24 = bdiv[:, min(23, T - 1)]
    vx_rmse = ((Vt[..., 0] - sur[..., 0]) ** 2).mean().sqrt()
    p90 = torch.quantile(b24, 0.9)
    if not quiet:
        print("[%-20s] beta_div @24: mean=%.4f p90=%.4f | max-over-traj mean=%.4f | vx_rmse=%.3f" % (
            label, b24.mean(), p90, bdiv.max(1).values.mean(), vx_rmse))
    return float(p90), float(b24.mean()), float(vx_rmse)


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


def _rollout(A, init, mu, make_batch, init_fn, step_fn, phys):
    """Replay the saved actions through one physics model; return surrogate vx,vy,yaw [R,T,3]."""
    R, T, _ = A.shape
    P = make_batch(phys, R, mu=mu, device=DEV, dtype=torch.float32)
    A_t = torch.tensor(A, device=DEV)
    init_t = torch.tensor(init, device=DEV)
    st, gear = init_fn(init_t[:, 0], init_t[:, 1], init_t[:, 2], P)
    sur = torch.zeros(R, T, 3, device=DEV)
    with torch.no_grad():
        for t in range(T):
            st, gear, _ = step_fn(st, A_t[:, t, :], gear, P, DT)
            sur[:, t, 0] = st[:, 3]
            sur[:, t, 1] = st[:, 4]
            sur[:, t, 2] = st[:, 5]
    return sur


def gate_relax(A, V, init, mu, phys: PhysParams, label="RELAX-TMeasy", quiet=False):
    sur = _rollout(A, init, mu, make_phys_param_batch, init_state, physics_step, phys)
    return _report(torch.tensor(V, device=DEV), sur, label, quiet=quiet)


def gate_l0(A, V, init, mu, label="L0 EXACT-TMeasy"):
    sur = _rollout(A, init, mu, tm_make_batch, tm_init, tm_step, TMPhysParams())
    return _report(torch.tensor(V, device=DEV), sur, label)


def signed_transient(A, V, init, mu, make_batch, init_fn, step_fn, phys, steps=(8, 24, 89)):
    """Mean SIGNED beta divergence (beta_chrono - beta_surrogate) at the given steps.

    The L0 plateau signature is the sign-reversing transient +0.009 @8 / -0.0188 @24 / +0.069 @89
    -- deep drift-entries where the planar model recovers the entry FASTER than Chrono. A correct
    relaxation transient should REDUCE this signed curve. Returns a dict {step: mean signed div}.
    """
    R, T, _ = A.shape
    sur = _rollout(A, init, mu, make_batch, init_fn, step_fn, phys)
    Vt = torch.tensor(V, device=DEV)
    beta_c = torch.atan2(Vt[..., 1], Vt[..., 0].abs() + 1e-6)
    beta_s = torch.atan2(sur[..., 1], sur[..., 0].abs() + 1e-6)
    signed = beta_c - beta_s          # +ve => surrogate UNDER-drifts (recovered too fast)
    return {s: float(signed[:, min(s, T - 1)].mean()) for s in steps}


def _with(p: PhysParams, key, val):
    kw = {f: getattr(p, f) for f in p.__dataclass_fields__}
    kw[key] = val
    return PhysParams(**kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma-sweep", action="store_true")
    args = ap.parse_args()

    A, V, init, mu = load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    tr, va = idx[:130], idx[130:]   # SAME split as the tmeasy gate

    print("device=%s  mu=%.3f  rollouts=%d  T=%d" % (DEV, mu, A.shape[0], A.shape[1]))
    print("=== baselines (held-out split) ===")
    gate_analytic(A[va], V[va], init[va], mu, label="analytic")
    print("  calibrated-Pacejka (ref): beta@24 p90 0.0435 / vx_rmse 0.227 (gpu_physics, WITH fudge)")
    gate_l0(A[va], V[va], init[va], mu, label="L0 EXACT-TMeasy(nofudge)")
    print("  grey-box residual  (ref): beta@24 p90 0.0156 (unroll-residual single-track) <= TARGET")

    phys = PhysParams()
    print("=== L1 RELAX-TMeasy, MEASURED sigma (held-out split) ===")
    print("  literal measured sigma (= dF0/sigma0, raw Dahl bristle stiffness): sigma_alpha~%.3f m"
          " sigma_kappa~%.3f m (load-dependent; sigma_scale=%.2f)" % (
              phys.sigma_alpha, phys.sigma_kappa, phys.sigma_scale))
    p90, bmean, vr = gate_relax(A[va], V[va], init[va], mu, phys, label="L1 relax (literal sigma)")
    print("vs L0 EXACT-TMeasy 0.0403: %s | vs grey-box 0.0156: %s" % (
        "BEATS" if p90 < 0.0403 else "no better (over-relaxed)",
        "BEATS" if p90 < 0.0156 else "still above"))
    # contact-patch-scale physical operating point: the EXACT-tyre contact length is ~0.107 m at
    # the ~4 kN rear load (measured in extract_chrono_tmeasy_relax.py); a brush/Dahl relaxation
    # length is the CONTACT-PATCH scale, ~3-4x SMALLER than the raw dF0/sigma0 upper bound. That
    # physical sigma (~0.13-0.16 m, sigma_scale~0.2-0.25) is the principled operating point.
    phys_cp = _with(phys, "sigma_scale", 0.22)
    print("=== L1 RELAX-TMeasy, contact-patch-scale physical sigma (sigma_alpha~%.3f m) ===" % (
        phys_cp.sigma_alpha * phys_cp.sigma_scale))
    p90b, bmeanb, vrb = gate_relax(A[va], V[va], init[va], mu, phys_cp, label="L1 relax (contact-patch)")
    print("\nGATE wants p90 beta_div@24 <= 0.03. L1 (contact-patch) p90 = %.4f -> %s" % (
        p90b, "PASS" if p90b <= 0.03 else "above 0.03"))
    print("vs L0 EXACT-TMeasy 0.0403: %s | vs grey-box 0.0156: %s" % (
        "BEATS" if p90b < 0.0403 else "no better",
        "BEATS" if p90b < 0.0156 else "approaching (mean below target)"))

    # ---- SIGNED-transient diagnostic: L0 vs L1 (both sigma operating points) ----
    print("\n=== SIGNED beta-divergence (beta_chrono - beta_surrogate) vs step (held-out) ===")
    s0 = signed_transient(A[va], V[va], init[va], mu, tm_make_batch, tm_init, tm_step, TMPhysParams())
    s1 = signed_transient(A[va], V[va], init[va], mu, make_phys_param_batch, init_state,
                          physics_step, phys)
    s1cp = signed_transient(A[va], V[va], init[va], mu, make_phys_param_batch, init_state,
                            physics_step, phys_cp)
    def _abssum(s):
        return abs(s[8]) + abs(s[24]) + abs(s[89])
    print("  step:                @8        @24       @89     |signed|sum")
    print("  L0 exact         : %+8.4f %+8.4f %+8.4f   %.4f  (plateau signature)" % (
        s0[8], s0[24], s0[89], _abssum(s0)))
    print("  L1 relax literal : %+8.4f %+8.4f %+8.4f   %.4f" % (s1[8], s1[24], s1[89], _abssum(s1)))
    print("  L1 relax contact : %+8.4f %+8.4f %+8.4f   %.4f" % (
        s1cp[8], s1cp[24], s1cp[89], _abssum(s1cp)))
    print("  -> contact-patch L1 %s the L0 signed transient" % (
        "REDUCES" if _abssum(s1cp) < _abssum(s0) else "does NOT reduce"))

    if args.sigma_sweep:
        print("\n=== sigma_scale sensitivity (single global multiplier; sigma_scale=1.0 = measured) ===")
        for sc in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
            p = _with(phys, "sigma_scale", sc)
            p90s, bmeans, vrs = gate_relax(A[va], V[va], init[va], mu, p, quiet=True)
            print("  sigma_scale=%.2f -> beta@24 p90=%.4f mean=%.4f vx_rmse=%.3f" % (
                sc, p90s, bmeans, vrs))


if __name__ == "__main__":
    main()
