"""PWR4 gate: the FULL faithful longitudinal model = pwr + FIX#1 gear-SEED + FIX#2 4-wheel brake, both
MEASURED. Side-by-side pwr (baseline) vs pwr3 (gear-seed only) vs pwr4 (gear-seed + 4-wheel brake) on the
avoid replay (accel + braking phases) and the drift gate (with the honest true-vx check).

    python scripts/feasibility_audit/gpu_pwr4_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/feasibility_audit"))
torch.set_default_dtype(torch.float32)

from gpu_pwr3_gate import _avoid_load_batched, avoid_gate, drift_gate  # noqa: E402

from autodrift.gpu_physics_pwr import (  # noqa: E402
    PhysParams as PwrP, make_phys_param_batch as pwr_b, physics_step as pwr_s, init_state as pwr_i)
from autodrift.gpu_physics_pwr3 import (  # noqa: E402
    PhysParams as P3, make_phys_param_batch as b3, physics_step as s3, init_state as i3)
from autodrift.gpu_physics_pwr4 import (  # noqa: E402  gear-seed + 4-wheel brake
    PhysParams as P4, make_phys_param_batch as b4, physics_step as s4, init_state as i4)


def main():
    print("=== (A) AVOIDANCE: pwr vs pwr3 (gear-seed) vs pwr4 (gear-seed + 4-wheel brake) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    vr_pwr, va_pwr, vy_pwr = avoid_gate(pwr_b, pwr_i, pwr_s, PwrP, "pwr (baseline)", A, Sx, Sy, mu, meta)
    vr_p3, va_p3, vy_p3 = avoid_gate(b3, i3, s3, P3, "pwr3 (gear-seed)", A, Sx, Sy, mu, meta)
    vr_p4, va_p4, vy_p4 = avoid_gate(b4, i4, s4, P4, "pwr4 (seed+4wheel brake)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT (gate <=0.03; HONEST = pass with TRUE vx) ===")
    p_pwr, pt_pwr, dv_pwr = drift_gate(pwr_b, pwr_i, pwr_s, PwrP, "pwr (baseline)")
    p_p3, pt_p3, dv_p3 = drift_gate(b3, i3, s3, P3, "pwr3 (gear-seed)")
    p_p4, pt_p4, dv_p4 = drift_gate(b4, i4, s4, P4, "pwr4 (seed+brake)")

    print("\n=== VERDICT (faithful longitudinal model) ===")
    fl = 0.235
    print("  avoid vx_rmse:        pwr %.3f -> pwr3 %.3f -> pwr4 %.3f   [drift floor %.3f]" % (
        vr_pwr, vr_p3, vr_p4, fl))
    print("    accel phase:        pwr %.3f -> pwr3 %.3f -> pwr4 %.3f   (gear-seed target)" % (
        va_pwr, va_p3, va_p4))
    print("  drift beta@24 p90:    pwr %.4f -> pwr3 %.4f -> pwr4 %.4f   (gate <=0.03)" % (p_pwr, p_p3, p_p4))
    print("  drift beta@24 TRUEvx: pwr %.4f -> pwr3 %.4f -> pwr4 %.4f   (HONEST)" % (pt_pwr, pt_p3, pt_p4))
    g0 = vr_pwr - fl
    print("\n  avoid gap closure (pwr->floor): pwr3 %.0f%%, pwr4 %.0f%%" % (
        (g0 - (vr_p3 - fl)) / g0 * 100, (g0 - (vr_p4 - fl)) / g0 * 100))


if __name__ == "__main__":
    main()
