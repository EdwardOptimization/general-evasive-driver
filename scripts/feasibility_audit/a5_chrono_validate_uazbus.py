"""UAZBUS A5 — validate the cross-vehicle do-both driver back on real Chrono (UAZBUS grid).

The UAZBUS analog of a5_chrono_validate.py. It loads the UAZBUS-distilled gated student and
runs it on real Chrono over the SAME frozen validation grid the Sedan A5 used, but with the
UAZBUS variant + measured mass threaded through every scenario and the drift cell re-tuned to
the de-risked mu0.25/v6 controllable-drift cell. We re-use the EXACT a5 build_items /
_student_task_eval machinery (so the drift/avoid success semantics are identical to the Sedan
A5), only swapping the F2 scenario hooks to the UAZBUS builders via distill_both_uazbus's
patches.

The number that matters: does the cross-vehicle do-both driver reach high drift + high avoid on
UAZBUS's OWN Chrono grid -- proving the recipe is cross-vehicle by config?

Usage: PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate_uazbus.py \
           --policy runs/feasibility_audit/phase4_f2/distill_uazbus_policy.pt \
           --avoid-units 40 --drift-units 20 --workers 16
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_f2_train as f2  # noqa: E402
import distill_both_uazbus as uaz  # noqa: E402  (installs the UAZBUS scenario patches)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = ROOT / "runs" / "feasibility_audit" / "phase4_f2"


def load_model(policy_path: Path):
    ckpt = torch.load(policy_path, map_location="cpu")
    gated = bool(ckpt.get("gated", True))
    model = f2.AsymmetricActorCritic(gated=gated)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    print(f"loaded policy {policy_path.name} (label={ckpt.get('label')}, variant={ckpt.get('variant')}, "
          f"gated={gated}, select_avoid={ckpt.get('select_avoid')}, select_drift={ckpt.get('select_drift')})")
    return model, ckpt


def build_items(avoid_units: int, drift_units: int):
    """Mirror a5_chrono_validate.build_items EXACTLY, but the F2 scenario hooks now build
    UAZBUS scenarios (patched by distill_both_uazbus). The frozen 'validation' seed namespace
    is identical to the Sedan A5 (so the grid/seeds match; only the vehicle differs).

    DRIFT seeds: the Sedan A5 reads E4's frozen low_mu validation seeds. The UAZBUS drift cell
    is a DIFFERENT cell, so we generate drift validation seeds in a UAZBUS namespace (the
    validation grid is for THIS vehicle's controllable-drift cell)."""
    grid = f2._avoidance_grid(quick=False)
    items = []
    for unit in range(avoid_units):
        reveal, mu = grid[unit % len(grid)]
        f2._EVAL_MU_REGISTRY[round(float(reveal), 6)] = float(mu)
        seed = f2._seed_for("validation", "avoidance", unit, round(reveal, 4), round(mu, 4))
        items.append({"regime": "avoidance", "reveal": float(reveal), "mu": float(mu), "seed": int(seed),
                      "scenario": f2._avoidance_scenario(seed, max_steps=285, reveal=float(reveal), mu=float(mu))})
    drift_mu = float(uaz.UAZBUS_DRIFT_CELL["mu"])
    for unit in range(drift_units):
        seed = int(f2._seed_for("uaz_validation", "drift", unit, uaz.UAZBUS_DRIFT_CELL["cell_id"]))
        items.append({"regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                      "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--avoid-units", type=int, default=40)
    ap.add_argument("--drift-units", type=int, default=20)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    uaz._install_uazbus_patches()  # thread UAZBUS variant + params + drift cell into f2 scenario builders
    model, ckpt = load_model(Path(args.policy))
    items = build_items(args.avoid_units, args.drift_units)
    n_av = sum(1 for it in items if it["regime"] == "avoidance")
    n_dr = sum(1 for it in items if it["regime"] == "drift")
    print(f"UAZBUS Chrono validation: {n_av} avoidance + {n_dr} drift episodes, {args.workers} workers")
    print(f"  variant={uaz.VARIANT} mass={uaz.UAZBUS_MASS} drift_cell={uaz.UAZBUS_DRIFT_CELL['cell_id']} "
          f"(mu{uaz.UAZBUS_DRIFT_CELL['mu']} v{uaz.UAZBUS_DRIFT_CELL['speed_mps']:g})")

    clients = [uaz.ResilientChronoClient(stderr_log=RUN_DIR / f"a5_uaz_w{w}_stderr.log")
               for w in range(args.workers)]
    # verify the scenarios carry the UAZBUS variant (not silently Sedan)
    verify = uaz._verify_uazbus_scenarios(clients)
    try:
        rates = f2._student_task_eval(clients, items, model)
    finally:
        for c in clients:
            c.close()

    drift = rates.get("drift", float("nan"))
    avoid = rates.get("avoidance", float("nan"))
    print("\n=== UAZBUS A5 CHRONO VALIDATION (cross-vehicle do-both driver on real Chrono) ===")
    print(f"  variant verified UAZBUS (not Sedan): {verify['all_uazbus']}")
    print(f"  drift  success (Chrono, UAZBUS mu{uaz.UAZBUS_DRIFT_CELL['mu']} cell) = {drift:.3f}")
    print(f"  avoid  success (Chrono, UAZBUS grid)                = {avoid:.3f}")
    print("\nVERDICT:")
    if avoid >= 0.80 and drift >= 0.80:
        print(f"  CROSS-VEHICLE do-both ACHIEVED on UAZBUS: drift={drift:.3f} avoid={avoid:.3f} (both >= 0.80). "
              f"The Sedan distill->DAgger recipe transfers to UAZBUS by config.")
    else:
        weak = []
        if drift < 0.80:
            weak.append(f"drift {drift:.3f}")
        if avoid < 0.80:
            weak.append(f"avoid {avoid:.3f}")
        print(f"  PARTIAL: {', '.join(weak)} below 0.80. Report where it lands; "
              f"a UAZBUS GPU drift expert and/or more DAgger may be needed (honest).")

    out = {
        "policy": str(args.policy), "variant": uaz.VARIANT, "mass": uaz.UAZBUS_MASS,
        "drift_cell": uaz.UAZBUS_DRIFT_CELL, "scenario_verification": verify,
        "avoid_units": int(n_av), "drift_units": int(n_dr),
        "drift_success_chrono": float(drift), "avoid_success_chrono": float(avoid),
        "ckpt_select_avoid": ckpt.get("select_avoid"), "ckpt_select_drift": ckpt.get("select_drift"),
    }
    out_path = RUN_DIR / "a5_uazbus_result.json"
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nresult -> {out_path}")


if __name__ == "__main__":
    main()
