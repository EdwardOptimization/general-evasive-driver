"""Run the EXACT avoid_gate + drift_gate from gpu_pwr3_gate.py on gpu_physics_pwrB (Approach B).

Reuses gpu_pwr3_gate's avoid_gate/drift_gate/_avoid_load_batched verbatim (imported), only swapping
the model module to pwrB. Reports pwrB vs the pwr3 baseline on both gates.
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

# the EXACT gate logic (avoid_gate, drift_gate, loaders) from the frozen pwr3 gate
import gpu_pwr3_gate as G  # noqa: E402

from autodrift.gpu_physics_pwr3 import (  # noqa: E402
    PhysParams as Pwr3Params, make_phys_param_batch as pwr3_batch,
    physics_step as pwr3_step, init_state as pwr3_init,
)
from autodrift.gpu_physics_pwrB import (  # noqa: E402
    PhysParams as PwrBParams, make_phys_param_batch as pwrB_batch,
    physics_step as pwrB_step, init_state as pwrB_init,
)


def main():
    print("device=%s  sigma_scale=%.3f" % (G.DEV, G.SIGMA_SCALE))
    print("\n=== (A) AVOIDANCE (pwr3 vs pwrB measured-surface) ===")
    A, Sx, Sy, mu, meta = G._avoid_load_batched()
    vr_p3, va_p3, vy_p3 = G.avoid_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params,
                                       "pwr3 (baseline)", A, Sx, Sy, mu, meta)
    vr_b, va_b, vy_b = G.avoid_gate(pwrB_batch, pwrB_init, pwrB_step, PwrBParams,
                                    "pwrB (measured Fx)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split idx[130:]; gate <=0.03) ===")
    p_p3, pt_p3, dv_p3 = G.drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3 (baseline)")
    p_b, pt_b, dv_b = G.drift_gate(pwrB_batch, pwrB_init, pwrB_step, PwrBParams, "pwrB")

    print("\n=== VERDICT (Approach B) ===")
    gap0 = vr_p3 - 0.235
    closed = (vr_p3 - vr_b) / gap0 * 100.0 if gap0 > 1e-6 else 0.0
    print("  avoid vx_rmse:        pwr3 %.3f -> pwrB %.3f   (closed %.1f%% of pwr3->0.235 floor gap)" % (
        vr_p3, vr_b, closed))
    print("  avoid vx_rmse accel:  pwr3 %.3f -> pwrB %.3f" % (va_p3, va_b))
    print("  avoid vy_rmse:        pwr3 %.3f -> pwrB %.3f" % (vy_p3, vy_b))
    print("  drift beta@24 p90:    pwr3 %.4f -> pwrB %.4f   (gate <=0.03)" % (p_p3, p_b))
    print("  drift beta@24 TRUEvx: pwr3 %.4f -> pwrB %.4f" % (pt_p3, pt_b))
    print("  drift vx_rmse:        pwr3 %.3f -> pwrB %.3f" % (dv_p3, dv_b))
    print("\n  STABLE (avoid finite & < pwr3 0.520): %s" % (np.isfinite(vr_b) and vr_b < 0.520))
    # machine-readable
    print("\nJSON %s" % {
        "avoid_vx_rmse": round(vr_b, 4), "avoid_accel": round(va_b, 4), "avoid_vy": round(vy_b, 4),
        "avoid_closed_pct": round(closed, 2),
        "drift_p90": round(p_b, 4), "drift_truevx": round(pt_b, 4), "drift_vx_rmse": round(dv_b, 4),
        "pwr3_avoid": round(vr_p3, 4), "pwr3_p90": round(p_p3, 4), "pwr3_truevx": round(pt_p3, 4),
    })


if __name__ == "__main__":
    main()
