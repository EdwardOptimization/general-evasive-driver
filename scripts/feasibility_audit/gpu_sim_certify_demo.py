"""Demo the gpu_sim certificate keystone: certify each rung against frozen Chrono through the ONE
config-driven harness, and show .dominates() picks the better posttrain config by MEASUREMENT — not
DOF count (rung-1 has more DOFs but regressed drift, so the certificate must rank rung-0 above it)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from autodrift.gpu_sim import FidelityConfig  # noqa: E402
from autodrift.gpu_sim.certify import certify  # noqa: E402


def show(cert):
    print(f"  [{cert.config_id}]")
    print(f"    drift beta@24 p90={cert.drift_beta24_p90:.4f}  (true-vx {cert.drift_beta24_truevx_p90:.4f}"
          f", passes={cert.drift_passes})   avoid vx_rmse={cert.avoid_vx_rmse:.3f}")
    print(f"    {cert.notes}")


def main():
    print("=== certify each rung on frozen Chrono (one harness, by-name state, EAGER) ===")
    c0 = certify(FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy"), device="cpu")
    c1 = certify(FidelityConfig(rung=1, vehicle_variant="sedan_tmeasy"), device="cpu")
    show(c0); show(c1)
    print("\n=== the arbiter: .dominates() (certificate, NOT DOF count) ===")
    print(f"  rung-0 (17-dim planar) dominates rung-1 (30-dim, more DOFs)? {c0.dominates(c1)}")
    print(f"  rung-1 dominates rung-0?                                     {c1.dominates(c0)}")
    better = "rung-0" if c0.dominates(c1) else ("rung-1" if c1.dominates(c0) else "neither dominates")
    print(f"  -> posttrain should pick: {better}")
    print("  (rung-1 has MORE DOFs but the MEASURED certificate ranks rung-0 above it — exactly the")
    print("   'certificate not DOF count' principle the dig forced into the design.)")


if __name__ == "__main__":
    main()
