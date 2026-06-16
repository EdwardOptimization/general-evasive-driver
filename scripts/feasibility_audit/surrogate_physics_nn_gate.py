"""Open-loop divergence gate for the NN-FITTED-TMeasy physics model (faithful rewrite).

Identical gate to ``surrogate_physics_tmeasy_gate.py`` (beta-div @24 p90/mean, vx RMSE on the
SAME held-out split of ``surrogate_drift_data.npz``), but it replays the saved Chrono drift
actions through ``autodrift.gpu_physics_nn`` — the NN-tyre sibling of the TABLE variant. Its
tyre is two small fitted MLPs (slip,Fz)->force-ratio (trained by ``fit_tmeasy_tyre_nn.py`` from
the SAME sampled Chrono TMeasy curves the TABLE variant interpolates), evaluated at the runtime
(slip, Fz) every sub-step. The grip fudge factors are 1.0 and there is NO Pacejka calibration —
the curve IS the Chrono curve, only the representation (NN vs bilinear LUT) differs.

It prints the NN-tyre numbers alongside the published baselines and the TABLE variant:

    analytic single-track   : beta@24 p90 0.138  / vx_rmse 1.097
    calibrated-Pacejka       : beta@24 p90 0.0435 / vx_rmse 0.227  (gpu_physics, with fudge)
    grey-box residual        : beta@24 p90 0.0156                  (target)
    TABLE-TMeasy (no fudge)   : beta@24 p90 0.0403 / vx_rmse 0.235  (gpu_physics_tmeasy)
    NN-TMeasy   (no fudge)    : measured here

Usage:
    python scripts/feasibility_audit/surrogate_physics_nn_gate.py
    python scripts/feasibility_audit/surrogate_physics_nn_gate.py --calibrate-nontyre
        (optional: search ONLY the non-tyre knobs — driveline/roll/brake/load-transfer —
         to quantify how much of any residual gap is NON-tyre physics, never grip scales)
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
from autodrift.gpu_physics_nn import (  # noqa: E402
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


def gate_physics(A, V, init, mu, phys: PhysParams, label="NN-TMeasy", quiet=False):
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


def _with(p: PhysParams, key, val):
    kw = {f: getattr(p, f) for f in p.__dataclass_fields__}
    kw[key] = val
    return PhysParams(**kw)


def calibrate_nontyre(A, V, init, mu, tr):
    """Coordinate search over ONLY non-tyre knobs (driveline/roll/brake/load-transfer/relax).

    The grip scales and pac_* are NEVER touched — this measures how much of any residual gap
    is non-tyre physics the planar model can still absorb, not tyre calibration."""
    grids = {
        "drive_scale": [0.85, 0.9, 1.0, 1.1, 1.2],
        "rolling_resist_coeff": [0.012, 0.02, 0.03, 0.04],
        "max_brake_torque": [1500.0, 2000.0, 3000.0],
        "drag_coeff": [0.2, 0.4, 0.8],
        "h_cg_scale": [0.5, 0.75, 1.0, 1.25, 1.5],
        "relax_len_f": [0.05, 0.1, 0.2, 0.4],
        "relax_len_r": [0.05, 0.1, 0.2, 0.4],
    }
    cur = PhysParams()

    def score(p):
        p90, bmean, vr = gate_physics(A[tr], V[tr], init[tr], mu, p, quiet=True)
        return bmean + 0.05 * vr, (p90, bmean, vr)

    cur_obj, stats = score(cur)
    print("  init obj=%.4f (p90=%.4f mean=%.4f vx=%.3f)" % (cur_obj, *stats), flush=True)
    for sweep in range(2):
        improved = False
        for key, vals in grids.items():
            best = (cur_obj, getattr(cur, key))
            for v in vals:
                obj, _ = score(_with(cur, key, v))
                if obj < best[0] - 1e-5:
                    best = (obj, v)
            if best[1] != getattr(cur, key):
                improved = True
            setattr(cur, key, best[1])
            cur_obj = best[0]
        _, stats = score(cur)
        print("  sweep %d obj=%.4f (p90=%.4f mean=%.4f vx=%.3f)" % (sweep, cur_obj, *stats), flush=True)
        if not improved:
            break
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate-nontyre", action="store_true")
    args = ap.parse_args()

    A, V, init, mu = load()
    rng = np.random.default_rng(0)
    idx = rng.permutation(A.shape[0])
    tr, va = idx[:130], idx[130:]

    print("device=%s  mu=%.3f  rollouts=%d  T=%d" % (DEV, mu, A.shape[0], A.shape[1]))
    print("=== baselines (held-out split) ===")
    gate_analytic(A[va], V[va], init[va], mu, label="analytic")
    print("  calibrated-Pacejka (ref): beta@24 p90 0.0435 / vx_rmse 0.227 (gpu_physics, WITH fudge)")
    print("  grey-box residual  (ref): beta@24 p90 0.0156 (unroll-residual single-track)")
    print("  TABLE-TMeasy       (ref): beta@24 p90 0.0403 / vx_rmse 0.235 (gpu_physics_tmeasy, NO fudge)")

    phys = PhysParams()
    print("  grip fudge: front_grip_scale=%.2f rear_grip_scale=%.2f (faithful => 1.0)" % (
        phys.front_grip_scale, phys.rear_grip_scale))
    print("=== NN-TMeasy model, NO fudge (held-out split) ===")
    p90, bmean, vr = gate_physics(A[va], V[va], init[va], mu, phys, label="NN-TMeasy(nofudge)")
    print("\nGATE wants p90 beta_div@24 <= 0.03. NN-TMeasy p90 = %.4f -> %s" % (
        p90, "PASS" if p90 <= 0.03 else "above 0.03"))
    print("vs calibrated-Pacejka 0.0435: %s" % ("BEATS" if p90 < 0.0435 else "worse"))
    print("vs TABLE-TMeasy      0.0403: %s (|d|=%.4f)" % (
        "BEATS" if p90 < 0.0403 else ("matches" if abs(p90 - 0.0403) < 0.003 else "worse"),
        abs(p90 - 0.0403)))

    if args.calibrate_nontyre:
        print("=== calibrating NON-TYRE knobs only (grip scales stay 1.0) ===")
        ph = calibrate_nontyre(A, V, init, mu, tr)
        tuned = ("drive_scale", "rolling_resist_coeff", "max_brake_torque", "drag_coeff",
                 "h_cg_scale", "relax_len_f", "relax_len_r")
        print("calibrated(non-tyre):", {k: round(float(getattr(ph, k)), 4) for k in tuned})
        print("=== NN-TMeasy + non-tyre calibration (held-out split) ===")
        gate_physics(A[va], V[va], init[va], mu, ph, label="NN-TMeasy(+nontyre)")


if __name__ == "__main__":
    main()
