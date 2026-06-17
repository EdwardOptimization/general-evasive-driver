"""Run the EXACT avoid_gate + drift_gate from gpu_pwr3_gate.py on the COMBINED B+D model (pwrBD).

Reuses gpu_pwr3_gate's avoid_gate/drift_gate/_avoid_load_batched verbatim (imported), only swapping
the model module. Reports pwr3 baseline vs pwrB vs pwrBD on:
  - avoid vx_rmse (overall + accel + brake split)
  - drift beta@24 p90 + TRUE-vx beta@24 + drift vx_rmse
The brake split is PRINTED by avoid_gate (not returned), so we capture each gate's stdout line and
parse the "brake X.XXX" token -- no re-implementation of the gate.

D's WINNING config is front_brake_scale=1.0, front_brake_net_gate=1.0 (both pwrBD defaults).
"""
from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout
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
from autodrift.gpu_physics_pwrBD import (  # noqa: E402  COMBINED B + D
    PhysParams as PwrBDParams, make_phys_param_batch as pwrBD_batch,
    physics_step as pwrBD_step, init_state as pwrBD_init,
)


def avoid_with_brake(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta):
    """Call the canonical avoid_gate (verbatim) and ALSO recover the brake-split it prints.

    avoid_gate returns (vx_rmse, vx_accel, vy_rmse) but prints '... (accel A / brake B) ...'. We
    capture its stdout, re-emit it, and parse the brake token so this runner can report it."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        vr, va, vy = G.avoid_gate(make_batch, init_fn, step_fn, ParamCls, label, A, Sx, Sy, mu, meta)
    out = buf.getvalue()
    sys.stdout.write(out)
    m = re.search(r"brake\s+([0-9.]+)\)", out)
    vbrk = float(m.group(1)) if m else float("nan")
    return vr, va, vbrk, vy


def main():
    print("device=%s  sigma_scale=%.3f" % (G.DEV, G.SIGMA_SCALE))
    print("\n=== (A) AVOIDANCE (pwr3 baseline vs pwrB vs pwrBD) -- vx_rmse overall/accel/brake ===")
    A, Sx, Sy, mu, meta = G._avoid_load_batched()
    vr_p3, va_p3, vb_p3, vy_p3 = avoid_with_brake(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params,
                                                  "pwr3 (baseline)", A, Sx, Sy, mu, meta)
    vr_b, va_b, vb_b, vy_b = avoid_with_brake(pwrB_batch, pwrB_init, pwrB_step, PwrBParams,
                                              "pwrB (measured drive)", A, Sx, Sy, mu, meta)
    vr_bd, va_bd, vb_bd, vy_bd = avoid_with_brake(pwrBD_batch, pwrBD_init, pwrBD_step, PwrBDParams,
                                                  "pwrBD (B + D brake)", A, Sx, Sy, mu, meta)

    print("\n=== (B) DRIFT gate (held-out split idx[130:]; gate <=0.03; HONEST = TRUE vx) ===")
    p_p3, pt_p3, dv_p3 = G.drift_gate(pwr3_batch, pwr3_init, pwr3_step, Pwr3Params, "pwr3 (baseline)")
    p_b, pt_b, dv_b = G.drift_gate(pwrB_batch, pwrB_init, pwrB_step, PwrBParams, "pwrB")
    p_bd, pt_bd, dv_bd = G.drift_gate(pwrBD_batch, pwrBD_init, pwrBD_step, PwrBDParams, "pwrBD")

    print("\n=== VERDICT (Combined B + D) ===")
    gap0 = vr_p3 - 0.235
    closed_b = (vr_p3 - vr_b) / gap0 * 100.0 if gap0 > 1e-6 else 0.0
    closed_bd = (vr_p3 - vr_bd) / gap0 * 100.0 if gap0 > 1e-6 else 0.0
    print("  avoid vx_rmse overall: pwr3 %.3f | pwrB %.3f | pwrBD %.3f" % (vr_p3, vr_b, vr_bd))
    print("  avoid vx_rmse accel:   pwr3 %.3f | pwrB %.3f | pwrBD %.3f" % (va_p3, va_b, va_bd))
    print("  avoid vx_rmse brake:   pwr3 %.3f | pwrB %.3f | pwrBD %.3f" % (vb_p3, vb_b, vb_bd))
    print("  avoid vy_rmse:         pwr3 %.3f | pwrB %.3f | pwrBD %.3f" % (vy_p3, vy_b, vy_bd))
    print("  drift beta@24 p90:     pwr3 %.4f | pwrB %.4f | pwrBD %.4f  (gate <=0.03)" % (p_p3, p_b, p_bd))
    print("  drift beta@24 TRUEvx:  pwr3 %.4f | pwrB %.4f | pwrBD %.4f  (HONEST)" % (pt_p3, pt_b, pt_bd))
    print("  drift vx_rmse:         pwr3 %.3f | pwrB %.3f | pwrBD %.3f" % (dv_p3, dv_b, dv_bd))
    print("\n  pwr3->0.235 gap closed:  pwrB %.1f%%  |  pwrBD %.1f%%" % (closed_b, closed_bd))
    beats_pwrB = vr_bd < vr_b - 1e-3
    drift_ok = p_bd <= 0.03 and pt_bd <= 0.03
    stable = bool(np.isfinite(vr_bd) and np.isfinite(vr_p3) and vr_bd < vr_p3)
    print("  pwrBD beats pwrB on avoid overall: %s" % beats_pwrB)
    print("  pwrBD drift passes (p90<=0.03 AND honest true-vx<=0.03): %s" % drift_ok)
    print("  STABLE (finite, no blow-up, avoid < pwr3 baseline): %s" % stable)

    print("\nJSON %s" % {
        "pwr3_avoid": round(vr_p3, 4), "pwr3_accel": round(va_p3, 4), "pwr3_brake": round(vb_p3, 4),
        "pwr3_p90": round(p_p3, 4), "pwr3_truevx": round(pt_p3, 4), "pwr3_drift_vx": round(dv_p3, 4),
        "pwrB_avoid": round(vr_b, 4), "pwrB_accel": round(va_b, 4), "pwrB_brake": round(vb_b, 4),
        "pwrB_p90": round(p_b, 4), "pwrB_truevx": round(pt_b, 4), "pwrB_drift_vx": round(dv_b, 4),
        "pwrBD_avoid": round(vr_bd, 4), "pwrBD_accel": round(va_bd, 4), "pwrBD_brake": round(vb_bd, 4),
        "pwrBD_vy": round(vy_bd, 4),
        "pwrBD_p90": round(p_bd, 4), "pwrBD_truevx": round(pt_bd, 4), "pwrBD_drift_vx": round(dv_bd, 4),
        "pwrB_closed_pct": round(closed_b, 2), "pwrBD_closed_pct": round(closed_bd, 2),
        "pwrBD_beats_pwrB": beats_pwrB, "pwrBD_drift_ok": drift_ok, "stable": stable,
    })


if __name__ == "__main__":
    main()
