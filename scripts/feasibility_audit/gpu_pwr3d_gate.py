"""APPROACH D gate: pwr3d (pwr3 + CLEAN front 4-wheel brake) vs pwr3 baseline.

Reuses the EXACT avoid_gate / drift_gate logic from gpu_pwr3_gate.py (imported, not copied) so the
numbers are directly comparable. Runs:
  - AVOIDANCE (replay surrogate_avoid_labels.npz): vx_rmse overall + accel/brake split.
  - DRIFT (held-out split idx[130:] of surrogate_drift_data.npz): beta@24 p90 + TRUE-vx beta@24.
for pwr3 (baseline) and pwr3d (Approach D). Also runs pwr3d with front_brake_scale=0 to confirm it
reduces to pwr3 exactly (a self-consistency check on the new code path).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
torch.set_default_dtype(torch.float32)

# reuse the EXACT gate logic + loaders from the canonical gate (do NOT re-implement)
from gpu_pwr3_gate import (  # noqa: E402
    _avoid_load_batched, avoid_gate, drift_gate,
)
from autodrift.gpu_physics_pwr3 import (  # noqa: E402
    PhysParams as Pwr3Params, make_phys_param_batch as pwr3_batch,
    physics_step as pwr3_step, init_state as pwr3_init,
)
from autodrift.gpu_physics_pwr3d import (  # noqa: E402  pwr3 + CLEAN front 4-wheel brake
    PhysParams as Pwr3dParams, make_phys_param_batch as pwr3d_batch,
    physics_step as pwr3d_step, init_state as pwr3d_init,
)


def _params_ctor(scale, net_gate=0.0):
    # PhysParams subclass that fixes front_brake_scale + net gate (so avoid_gate / drift_gate, which
    # only pass sigma_scale + geometry, get the right brake setting).
    def ctor(**kw):
        return Pwr3dParams(front_brake_scale=scale, front_brake_net_gate=net_gate, **kw)
    return ctor


def main():
    DEV = "cuda" if torch.cuda.is_available() else "cpu"
    print("device=%s  sigma_scale=0.165" % DEV)

    print("\n=== (A) AVOIDANCE: vx fidelity + accel/brake split ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    vr_p3, va_p3, vy_p3 = avoid_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params,
                                     "pwr3 (baseline)", A, Sx, Sy, mu, meta)
    vr_off, va_off, vy_off = avoid_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(0.0),
                                        "pwr3d brake OFF (==pwr3?)", A, Sx, Sy, mu, meta)
    vr_d, va_d, vy_d = avoid_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(1.0),
                                  "pwr3d brake ON (Approach D)", A, Sx, Sy, mu, meta)
    vr_n, va_n, vy_n = avoid_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(1.0, 1.0),
                                  "pwr3d brake ON net-gate", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split; gate <=0.03; HONEST = pass with TRUE vx) ===")
    p_p3, pt_p3, dv_p3 = drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3 (baseline)")
    p_off, pt_off, dv_off = drift_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(0.0),
                                       "pwr3d brake OFF (==pwr3?)")
    p_d, pt_d, dv_d = drift_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(1.0),
                                 "pwr3d brake ON (Approach D)")
    p_n, pt_n, dv_n = drift_gate(pwr3d_batch, pwr3d_init, pwr3d_step, _params_ctor(1.0, 1.0),
                                 "pwr3d brake ON net-gate")

    print("\n=== VERDICT (Approach D vs pwr3) ===")
    gap0 = vr_p3 - 0.235; gap1 = vr_d - 0.235
    closed = (gap0 - gap1) / gap0 * 100.0 if abs(gap0) > 1e-6 else 0.0
    print("  avoid vx_rmse:        pwr3 %.3f -> pwr3d %.3f   (closed %.1f%% of pwr3->0.235 floor gap)" % (
        vr_p3, vr_d, closed))
    print("  avoid vx_rmse accel:  pwr3 %.3f -> pwr3d %.3f" % (va_p3, va_d))
    print("  avoid vx_rmse brake (from full-set split below); see per-line accel/brake prints above")
    print("  drift beta@24 p90:    pwr3 %.4f -> pwr3d %.4f   (gate <=0.03)" % (p_p3, p_d))
    print("  drift beta@24 TRUEvx: pwr3 %.4f -> pwr3d %.4f   (HONEST)" % (pt_p3, pt_d))
    print("  drift vx_rmse:        pwr3 %.3f -> pwr3d %.3f" % (dv_p3, dv_d))
    gapn = vr_n - 0.235
    closedn = (gap0 - gapn) / gap0 * 100.0 if abs(gap0) > 1e-6 else 0.0
    print("\n  net-gate variant: avoid %.3f (accel %.3f) closed %.1f%% | drift p90 %.4f true %.4f vx %.3f" % (
        vr_n, va_n, closedn, p_n, pt_n, dv_n))
    print("\n  brake-OFF self-check: avoid %.3f vs pwr3 %.3f | drift p90 %.4f vs %.4f (should match)" % (
        vr_off, vr_p3, p_off, p_p3))


if __name__ == "__main__":
    main()
