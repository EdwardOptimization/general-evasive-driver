"""Combined writer for the S1 full-scenario feasibility pre-check: merges the DRIFT half
(spectrum_s1_feasibility_precheck.py -> feasibility_precheck.json) and the AVOID half
(spectrum_s1_avoid_feasibility.py -> avoid_feasibility.json) into one frozen artifact,
runs/feasibility_audit/spectrum_s1/feasibility_fullscenario.json.

Emits the full-scenario feasible-cell list grounding the S1 spectrum:
  - feasible DRIFT cells (mu, beta, speed, sustain)
  - feasible AVOID cells (reveal, mu, geometry, success)
plus the prune summary (drift cells that can't drift / are infeasible, avoid geometry
extensions that stay avoidable vs. drop out).

Run (after both halves finish):
    python scripts/feasibility_audit/spectrum_s1_merge_fullscenario.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RUN_DIR = REPO / "runs" / "feasibility_audit" / "spectrum_s1"
DRIFT_JSON = RUN_DIR / "feasibility_precheck.json"
AVOID_JSON = RUN_DIR / "avoid_feasibility.json"
OUT = RUN_DIR / "feasibility_fullscenario.json"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing half-output: {path} (run that half first)")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    drift = _load(DRIFT_JSON)
    avoid = _load(AVOID_JSON)

    # ---- DRIFT half ----
    drift_cells = drift.get("cells", [])
    drift_feasible = [
        {"mu": c["mu"], "beta": c["beta"], "speed": c["speed"], "sustain": c["longest"],
         "rear_saturation_steps": c["rearsat"], "beta_max": c["beta_max"], "spec": c["spec"]}
        for c in drift_cells if c.get("feasible")
    ]
    # prune buckets: infeasible (can't break+hold the rear) vs trivial-near (sustain in [18, MIN))
    min_sustain = int(drift.get("min_sustain", 24))
    drift_infeasible = [
        {"mu": c["mu"], "beta": c["beta"], "best_sustain": c["longest"], "rearsat": c["rearsat"],
         "reason": ("cannot_drift_low_sustain" if c["longest"] < 18 else "near_threshold")}
        for c in drift_cells if not c.get("feasible")
    ]

    # ---- AVOID half ----
    avoid_cells = avoid.get("cells", [])
    avoid_feasible = [
        {"reveal": c["reveal"], "mu": c["mu"], "geometry": c["geometry"],
         "lateral_offset_m": c.get("lateral_offset_m", 0.0), "half_width_m": c.get("half_width_m"),
         "success": c["success"]}
        for c in avoid_cells if c.get("feasible")
    ]
    avoid_infeasible = [
        {"reveal": c["reveal"], "mu": c["mu"], "geometry": c["geometry"],
         "lateral_offset_m": c.get("lateral_offset_m", 0.0), "half_width_m": c.get("half_width_m"),
         "success": c["success"], "reason": "oracle_success_below_0.8"}
        for c in avoid_cells if not c.get("feasible")
    ]
    geom_summary = avoid.get("geometry_family_summary", {})

    payload = {
        "protocol": "spectrum_s1_feasibility_fullscenario",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": (
            "Full-scenario S1 feasibility pre-check on the Sedan (sedan_tmeasy), BOTH task families. "
            "Drift cells run the parameterized DriftFeedbackPolicy oracle (feasible if "
            "longest_controlled_drift_run >= MIN_SUSTAIN AND rear_saturation_steps >= MIN_SUSTAIN); "
            "avoid cells run the Sedan-fitted ramp_policy_voi_regime oracle (feasible if avoid "
            "success >= 0.8). Oracle rollouts only, no training. This is the data that freezes the "
            "S1 spectrum."
        ),
        "variant": "sedan_tmeasy",
        "drift": {
            "source_json": str(DRIFT_JSON.relative_to(REPO)),
            "min_sustain_steps": min_sustain,
            "grid": drift.get("grid"),
            "n_cells": len(drift_cells),
            "n_feasible": len(drift_feasible),
            "feasible_cells": drift_feasible,
            "infeasible_cells": drift_infeasible,
        },
        "avoid": {
            "source_json": str(AVOID_JSON.relative_to(REPO)),
            "feasible_threshold": avoid.get("feasible_threshold", 0.8),
            "oracle": avoid.get("oracle"),
            "grid": avoid.get("grid"),
            "n_cells": len(avoid_cells),
            "n_feasible": len(avoid_feasible),
            "feasible_cells": avoid_feasible,
            "infeasible_cells": avoid_infeasible,
            "geometry_family_summary": geom_summary,
        },
        "headline": {
            "drift_feasible_over_total": f"{len(drift_feasible)}/{len(drift_cells)}",
            "avoid_feasible_over_total": f"{len(avoid_feasible)}/{len(avoid_cells)}",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print("=== S1 FULL-SCENARIO FEASIBILITY (Sedan, both families) ===")
    print(f"DRIFT feasible: {len(drift_feasible)}/{len(drift_cells)} cells "
          f"(min_sustain={min_sustain})")
    for c in drift_feasible:
        print(f"  drift  mu={c['mu']:.2f} beta*={c['beta']:.2f} v{c['speed']} "
              f"sustain={c['sustain']} rearsat={c['rear_saturation_steps']}")
    print(f"AVOID feasible: {len(avoid_feasible)}/{len(avoid_cells)} cells (oracle>=0.8)")
    for fam, gg in geom_summary.items():
        print(f"  avoid [{fam}] {gg['feasible']}/{gg['total']} feasible")
    if avoid_infeasible:
        print("  avoid pruned (infeasible):")
        for c in avoid_infeasible:
            print(f"    reveal={c['reveal']:>4.1f} mu={c['mu']:.4f} geom={c['geometry']} "
                  f"success={c['success']:.2f}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
