"""T3a FALSIFICATION GATE: does injecting the INSTANTANEOUS quasi-static GEOMETRIC load transfer into
tier_a close its drift regression? This decides whether the full-DAE (T3) is worth building.

The faithful-rewrite dig localized tier_a's drift regression (beta@24 0.0756 vs planar 0.028) to the
load-transfer PATH: Chrono's lateral transfer is ~99% instantaneous-geometric, but tier_a routes it
through the SLOW chassis roll DOF (the per-corner Fz lags during the fast drift). gpu_vehicle_tier_a_geom
bypasses the slow travel-based Fz and uses pwr3's exact quasi-static geometric path (ay~vx*wz). Three-way
drift gate, SAME held-out split + sigma_scale as every prior gate:
  - planar pwr3  : beta@24 ~0.028 (passes)
  - tier_a (slow): beta@24 ~0.0756 (regressed)
  - tier_a_geom  : beta@24 = ?   <- THE T3a ANSWER
VERDICT: if geom drops toward planar -> the load-transfer-path hypothesis is CONFIRMED, the full-DAE's
real geometric linkage would capture it -> T3 GO. If it stays ~0.0756 -> the regression is NOT the
load-transfer path -> T3 NO-GO (kill the 6-12wk build cheaply).

    python scripts/feasibility_audit/gpu_tier_a_geom_gate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/feasibility_audit"))
torch.set_default_dtype(torch.float32)

from gpu_tier_a_gate import drift_gate, avoid_gate, _avoid_load_batched  # noqa: E402

from autodrift.gpu_physics_pwr3 import (  # noqa: E402  planar baseline (carried model)
    PhysParams as P3, make_phys_param_batch as b3, physics_step as s3, init_state as i3)
from autodrift.gpu_vehicle_tier_a import (  # noqa: E402  slow roll-DOF transfer
    TierAParams, make_tier_a_param_batch as bta, physics_step as sta, init_state as ita, IDX as TA_IDX)
from autodrift.gpu_vehicle_tier_a_geom import (  # noqa: E402  INSTANTANEOUS geometric transfer (GEOMETRIC_FZ=True)
    TierAParams as TAGP, make_tier_a_param_batch as bgeo, physics_step as sgeo, init_state as igeo,
    IDX as TAG_IDX, GEOMETRIC_FZ)


def main():
    print("device=%s  GEOMETRIC_FZ(tier_a_geom)=%s" % (
        "cuda" if torch.cuda.is_available() else "cpu", GEOMETRIC_FZ))
    print("\n=== (B) DRIFT gate (held-out split; sigma_scale=0.165; gate <=0.03) — THE T3a TEST ===")
    p90_pwr, dvr_pwr = drift_gate(b3, i3, s3, P3, "planar pwr3 (baseline)", vx_col=3, vy_col=4, yaw_col=5)
    p90_ta, dvr_ta = drift_gate(bta, ita, sta, TierAParams, "tier_a (slow roll-DOF)",
                                vx_col=TA_IDX["vx"], vy_col=TA_IDX["vy"], yaw_col=TA_IDX["wz"])
    p90_geo, dvr_geo = drift_gate(bgeo, igeo, sgeo, TAGP, "tier_a_GEOM (instantaneous)",
                                  vx_col=TAG_IDX["vx"], vy_col=TAG_IDX["vy"], yaw_col=TAG_IDX["wz"])

    print("\n=== (A) AVOIDANCE vx (does the geometric Fz also help the avoid cornering gap?) ===")
    A, Sx, Sy, mu, meta = _avoid_load_batched()
    vr_pwr, vy_pwr = avoid_gate(b3, i3, s3, P3, "planar pwr3", A, Sx, Sy, mu, meta, vx_col=3, vy_col=4)
    vr_ta, vy_ta = avoid_gate(bta, ita, sta, TierAParams, "Tier-a (slow)", A, Sx, Sy, mu, meta,
                              vx_col=TA_IDX["vx"], vy_col=TA_IDX["vy"])
    vr_geo, vy_geo = avoid_gate(bgeo, igeo, sgeo, TAGP, "Tier-a_GEOM", A, Sx, Sy, mu, meta,
                                vx_col=TAG_IDX["vx"], vy_col=TAG_IDX["vy"])

    print("\n=== T3a VERDICT ===")
    print("  drift beta@24 p90:  planar %.4f | tier_a %.4f | tier_a_GEOM %.4f   (gate <=0.03)" % (
        p90_pwr, p90_ta, p90_geo))
    print("  avoid vx_rmse:      planar %.3f | tier_a %.3f | tier_a_GEOM %.3f" % (vr_pwr, vr_ta, vr_geo))
    closed = (p90_ta - p90_geo) / (p90_ta - p90_pwr) * 100.0 if (p90_ta - p90_pwr) > 1e-6 else 0.0
    print("\n  geometric Fz closed %.0f%% of the tier_a->planar drift-regression gap" % closed)
    if p90_geo <= p90_pwr + 0.005:
        print("  ** T3a = GO: geometric load transfer CLOSES tier_a's drift regression -> the load-transfer")
        print("     path is the cause; the full-DAE's real linkage geometry would capture it. **")
    elif p90_geo < p90_ta - 0.01:
        print("  ~ T3a = PARTIAL: geometric Fz helps but does not fully close -> load transfer is PART of it;")
        print("    weigh the residual before committing to the full-DAE build.")
    else:
        print("  ** T3a = NO-GO: geometric Fz does NOT close the regression -> tier_a's drift problem is NOT")
        print("     the load-transfer path; the 6-12wk full-DAE would likely not fix drift either. **")


if __name__ == "__main__":
    main()
