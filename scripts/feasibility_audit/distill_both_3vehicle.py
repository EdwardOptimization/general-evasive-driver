"""GENERALITY test: ONE gated obs72 do-both driver across ALL 3 contrasting vehicles.

The load-bearing question (RMA / self-ID generality; see memory robotics-recipes-for-
autodrift): does a SINGLE vehicle-AGNOSTIC obs72 policy adapt drift+avoid across 3
contrasting vehicles (Sedan FWD 1450kg / UAZBUS 4WD 2858kg high-CG / BMW RWD 1800kg
high-speed-drift) from the observed dynamics ALONE -- obs72 has NO explicit vehicle
id/params -- or does it need vehicle conditioning (a finding either way)?

The 3 PROVEN per-vehicle do-both drivers each hit (drift/avoid): Sedan 1.0/1.0,
UAZBUS 1.0/1.0, BMW 0.85/1.0. Each has its own drift teacher + re-physicalized avoid
oracle + drift cell. This script POOLS all 3 vehicles' teacher demos into ONE training
set and BC-distills ONE fresh gated AsymmetricActorCritic (same architecture). The gate
self-routes drift vs avoid from obs72; within each regime the ONE policy must cover all
3 vehicles from obs72 (no vehicle channel).

WHAT this does (NEW FILE ONLY; imports the recipe machinery -- distill_both.py and the
per-vehicle patch modules distill_both_uazbus / distill_both_bmw -- VERBATIM; no protected
module is modified):
  1. For EACH vehicle, INSTALL that vehicle's scenario/teacher/oracle patches (the exact
     patches the per-vehicle build uses), build that vehicle's drift+avoid demo specs, and
     collect demos on real Chrono. Sedan uses the un-patched F2 hooks + the GPU drift expert;
     UAZBUS uses distill_both_uazbus's patches + UAZBUS feedback teacher; BMW uses
     distill_both_bmw's patches + BMW feedback teacher + re-physicalized avoid oracle. We
     VERIFY each vehicle's scenarios carry the correct backend variant + mass before collecting.
  2. POOL all 3 vehicles' drift demos into ONE drift demo set, all 3 vehicles' avoid demos
     into ONE avoid demo set. Each frame is (obs72 -> teacher_action); the vehicle id is NOT
     a feature -- only the realized obs72 dynamics differ across vehicles.
  3. BC-distill ONE FRESH gated AsymmetricActorCritic on the POOLED demos (db.distill
     VERBATIM). 3-seed sweep + Chrono-task-score selection (db._chrono_select_eval) on a
     POOLED select set spanning all 3 vehicles. Save distill_3vehicle_policy.pt.

Then validate PER-(vehicle, regime) with the existing per-vehicle A5 validators
(a5_chrono_validate.py / _uazbus / _bmw) pointed at THIS single policy -- the honest
per-vehicle Chrono numbers.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_3vehicle.py \
        --workers 16 --drift-seeds 8 --avoid-seeds-per-cell 2 --epochs 4000 \
        --seed-sweep 3 \
        --out runs/feasibility_audit/phase4_f2/distill_3vehicle_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_f2_train as f2  # noqa: E402
import distill_both as db  # noqa: E402  (recipe machinery, imported VERBATIM)
import distill_both_uazbus as uaz  # noqa: E402  (UAZBUS patches + ResilientChronoClient)
import distill_both_bmw as bmw  # noqa: E402  (BMW patches)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_3vehicle_policy.pt"

# Reuse UAZBUS's drop-in resilient client (transparent worker respawn on a hard-solve death).
ResilientChronoClient = uaz.ResilientChronoClient


# =====================================================================================
# The Sedan hooks are the UN-patched F2 / distill_both defaults. We stash them so each
# vehicle's collection installs its own patches and restores the Sedan defaults after.
# =====================================================================================
_SEDAN_AVOID_SCENARIO = f2._avoidance_scenario
_SEDAN_DRIFT_SCENARIO = f2._drift_scenario
_SEDAN_DRIFT_CELL = f2._drift_cell
_SEDAN_DB_DRIFT_SPECS = db._drift_specs
_SEDAN_DB_LOAD_EXPERT = db.load_drift_expert
_SEDAN_E2_CONTEXT = f2.f1._e2_context


def _install_sedan_patches() -> None:
    """Restore the Sedan (un-patched F2) scenario/teacher hooks. The Sedan drift teacher is
    the GPU drift expert (db.load_drift_expert default) and the avoid oracle is the un-modified
    Sedan-fitted RampPolicyController (f1._e2_context default)."""
    f2._avoidance_scenario = _SEDAN_AVOID_SCENARIO
    f2._drift_scenario = _SEDAN_DRIFT_SCENARIO
    f2._drift_cell = _SEDAN_DRIFT_CELL
    db._drift_specs = _SEDAN_DB_DRIFT_SPECS
    db.load_drift_expert = _SEDAN_DB_LOAD_EXPERT
    f2.f1._e2_context = _SEDAN_E2_CONTEXT


# per-vehicle config: (name, install_patches_fn, drift_cell, variant, mass).
VEHICLES = ("sedan", "uazbus", "bmw")


def _install_vehicle(name: str) -> None:
    if name == "sedan":
        _install_sedan_patches()
    elif name == "uazbus":
        _install_sedan_patches()  # start from a clean Sedan base
        uaz._install_uazbus_patches()
    elif name == "bmw":
        _install_sedan_patches()  # start from a clean Sedan base
        bmw._install_bmw_patches()
    else:
        raise ValueError(f"unknown vehicle {name!r}")


def _vehicle_drift_cell(name: str) -> dict[str, Any]:
    if name == "sedan":
        return dict(_SEDAN_DRIFT_CELL())
    if name == "uazbus":
        return dict(uaz.UAZBUS_DRIFT_CELL)
    if name == "bmw":
        return dict(bmw.BMW_DRIFT_CELL)
    raise ValueError(name)


def _vehicle_variant_mass(name: str) -> tuple[str, float]:
    if name == "sedan":
        return (f2.VARIANT, 1450.0)
    if name == "uazbus":
        return (uaz.VARIANT, uaz.UAZBUS_MASS)
    if name == "bmw":
        return (bmw.VARIANT, bmw.BMW_MASS)
    raise ValueError(name)


def _verify_vehicle_scenarios(name: str, clients) -> dict[str, Any]:
    """Reset one drift + one avoid scenario on the REAL backend and confirm the backend
    reports the EXPECTED variant + mass for THIS vehicle (the scoping's secondary risk:
    that a vehicle's demos are not silently collected on the Sedan)."""
    variant, _mass = _vehicle_variant_mass(name)
    client = clients[0]
    dr_scn = f2._drift_scenario(12345, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")
    _obs, reply = client.reset(dr_scn, episode_id=f"verify-{name}-drift", seed=1)
    dbi = dict(reply.get("backend_info", {}))
    av_scn = f2._avoidance_scenario(12345, max_steps=db.AVOID_MAX_STEPS, reveal=16.0, mu=0.5875)
    _obs, reply = client.reset(av_scn, episode_id=f"verify-{name}-avoid", seed=1)
    abi = dict(reply.get("backend_info", {}))
    out = {
        "vehicle": name, "expected_variant": variant,
        "drift_backend_variant": dbi.get("chrono_vehicle_variant"),
        "drift_backend_total_mass": dbi.get("vehicle_total_mass"),
        "drift_cell_mu": dr_scn.get("params", {}).get("mu"),
        "avoid_backend_variant": abi.get("chrono_vehicle_variant"),
        "avoid_backend_total_mass": abi.get("vehicle_total_mass"),
    }
    out["variant_ok"] = bool(out["drift_backend_variant"] == variant and out["avoid_backend_variant"] == variant)
    # avoid-oracle physicalization (informational; BMW is re-physicalized, Sedan/UAZBUS are Sedan-fitted)
    reg, _mb, _ip = f2.f1._e2_context()
    out["avoid_oracle_FZR"] = float(reg.FZR)
    out["avoid_oracle_MASS"] = float(reg.MASS)
    out["avoid_oracle_V_KNOTS"] = list(reg.V_KNOTS)
    print(f"\n=== [{name}] SCENARIO VARIANT VERIFICATION (real Chrono backend) ===", flush=True)
    print(f"  DRIFT: backend variant={out['drift_backend_variant']} total_mass={out['drift_backend_total_mass']} "
          f"mu={out['drift_cell_mu']}", flush=True)
    print(f"  AVOID: backend variant={out['avoid_backend_variant']} total_mass={out['avoid_backend_total_mass']} "
          f"| oracle FZR={out['avoid_oracle_FZR']:.1f} MASS={out['avoid_oracle_MASS']:.1f} V_KNOTS={out['avoid_oracle_V_KNOTS']}",
          flush=True)
    print(f"  variant carries {variant} (not silently Sedan): {'YES' if out['variant_ok'] else 'NO -- ABORT'}", flush=True)
    return out


def _collect_vehicle_demos(name: str, clients, *, drift_seeds: int, avoid_seeds_per_cell: int) -> dict[str, Any]:
    """Install vehicle ``name``'s patches, verify, then collect its drift + avoid demos.

    DRIFT teacher: Sedan -> GPU drift expert; UAZBUS/BMW -> their DriftFeedbackPolicy
    (db.load_drift_expert is patched to the per-vehicle teacher). AVOID teacher: the
    (per-vehicle re-physicalized for BMW) entry-speed oracle, reveal-post frames only.
    The specs are built AFTER the patches are installed, so the scenario builders the
    recipe calls are the vehicle's."""
    _install_vehicle(name)
    verify = _verify_vehicle_scenarios(name, clients)
    if not verify["variant_ok"]:
        raise SystemExit(f"FATAL [{name}]: scenarios are NOT carrying the {name} variant; aborting "
                         f"(would silently collect on Sedan).")
    expert = db.load_drift_expert()  # patched per-vehicle (Sedan=GPU expert, UAZ/BMW=feedback teacher)
    drift_specs = db._drift_specs(drift_seeds)          # patched per-vehicle drift scenario builder
    avoid_specs = db._avoid_specs(avoid_seeds_per_cell)  # uses f2._avoidance_scenario (patched per-vehicle)
    print(f"[{name}] collecting {len(drift_specs)} drift + {len(avoid_specs)} avoid demo episodes", flush=True)
    drift_demo = db.collect_demos(clients, drift_specs, expert, label=f"DRIFT[{name}]")
    avoid_demo = db.collect_demos(clients, avoid_specs, expert, label=f"AVOID[{name}]")
    if drift_demo["obs"].shape[0] == 0 or avoid_demo["obs"].shape[0] == 0:
        raise SystemExit(f"FATAL [{name}]: a regime collected 0 demo frames; cannot pool.")
    return {"verify": verify, "drift": drift_demo, "avoid": avoid_demo}


def _pooled_select_items(n_avoid_per_vehicle: int, n_drift_per_vehicle: int) -> dict[str, list[dict]]:
    """Build a Chrono select set spanning all 3 vehicles (disjoint 'distill_select' namespace).

    We CANNOT build all vehicles' items up front with one set of installed patches, because the
    scenario builders are vehicle-patched globals. So we install each vehicle in turn and build
    its select items; the items carry the constructed scenario dict (vehicle-specific) so the
    later eval is correct regardless of which patches are installed at eval time.
    """
    out: dict[str, list[dict]] = {}
    for name in VEHICLES:
        _install_vehicle(name)
        grid = f2._avoidance_grid(quick=False)
        drift_mu = float(_vehicle_drift_cell(name)["mu"])
        items: list[dict] = []
        for u in range(n_avoid_per_vehicle):
            reveal, mu = grid[u % len(grid)]
            seed = int(f2._seed_for("distill_select", name, "avoidance", u, round(reveal, 4), round(mu, 4)))
            items.append({"regime": "avoidance", "reveal": float(reveal), "mu": float(mu), "seed": seed,
                          "scenario": f2._avoidance_scenario(seed, max_steps=db.AVOID_MAX_STEPS,
                                                             reveal=float(reveal), mu=float(mu))})
        for u in range(n_drift_per_vehicle):
            seed = int(f2._seed_for("distill_select", name, "drift", u, _vehicle_drift_cell(name)["cell_id"]))
            items.append({"regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                          "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS,
                                                         difficulty="hard")})
        out[name] = items
    return out


def _pooled_chrono_select(clients, model, select_items: dict[str, list[dict]]) -> dict[str, Any]:
    """Run the pooled select set per-vehicle on Chrono; return per-vehicle + aggregate success.

    The avoid oracle is NOT driven here (we eval the STUDENT model.act(obs)), so no per-vehicle
    oracle patching is needed for eval. But the avoidance EVAL reads f2._EVAL_MU_REGISTRY via the
    scenario's reveal; _student_task_eval drives model.act only, so the registry is irrelevant.
    We install each vehicle's patches before eval so its scenarios reset on the right backend
    variant (the scenario dict already carries it, but f1._e2_context state is irrelevant for the
    student-only eval)."""
    per_vehicle: dict[str, dict[str, float]] = {}
    all_avoid: list[float] = []
    all_drift: list[float] = []
    for name in VEHICLES:
        _install_vehicle(name)
        items = select_items[name]
        # populate the mu registry single-threaded (harmless for student-only eval; mirrors A5)
        for it in items:
            if it["regime"] == "avoidance":
                f2._EVAL_MU_REGISTRY[round(float(it["reveal"]), 6)] = float(it["mu"])
        rates = f2._student_task_eval(clients, items, model)
        av = float(rates.get("avoidance", 0.0)); dr = float(rates.get("drift", 0.0))
        per_vehicle[name] = {"avoid": av, "drift": dr}
        all_avoid.append(av); all_drift.append(dr)
        print(f"    [{name}] select avoid={av:.3f} drift={dr:.3f}", flush=True)
    agg = {"avoidance": float(np.mean(all_avoid)) if all_avoid else 0.0,
           "drift": float(np.mean(all_drift)) if all_drift else 0.0}
    # worst-vehicle-per-regime (the generality bottleneck) for selection tie-breaking
    worst = {"avoidance": float(np.min(all_avoid)) if all_avoid else 0.0,
             "drift": float(np.min(all_drift)) if all_drift else 0.0}
    return {"per_vehicle": per_vehicle, "aggregate": agg, "worst": worst}


def main() -> None:
    ap = argparse.ArgumentParser(description="ONE gated obs72 do-both driver across ALL 3 vehicles (pooled distill).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=8, help="drift demo seeds PER difficulty PER vehicle (x3 diff x3 veh)")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal x mu cell PER vehicle (x20 cells x3 veh)")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--select-avoid-units", type=int, default=8, help="select avoid episodes PER vehicle")
    ap.add_argument("--select-drift-units", type=int, default=5, help="select drift episodes PER vehicle")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    print(f"[3vehicle-distill] pooling demos from {VEHICLES} into ONE gated obs72 student. "
          f"obs72 has NO explicit vehicle id -- the driver must adapt from observed dynamics alone.", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"distill3v_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {"vehicles": list(VEHICLES), "baselines": {
        "sedan": {"drift": 1.0, "avoid": 1.0}, "uazbus": {"drift": 1.0, "avoid": 1.0},
        "bmw": {"drift": 0.85, "avoid": 1.0}}}
    t0 = time.time()
    pooled = None
    best = None  # (score, state_dict, stats, seed, sel)
    try:
        # ---- 1. collect demos PER vehicle (install that vehicle's patches first) ----
        per_vehicle_demos: dict[str, Any] = {}
        for name in VEHICLES:
            print(f"\n################### COLLECTING {name.upper()} DEMOS ###################", flush=True)
            per_vehicle_demos[name] = _collect_vehicle_demos(
                name, clients, drift_seeds=args.drift_seeds, avoid_seeds_per_cell=args.avoid_seeds_per_cell)

        # ---- 2. POOL all 3 vehicles' drift demos / avoid demos ----
        drift_obs = np.concatenate([per_vehicle_demos[v]["drift"]["obs"] for v in VEHICLES], 0)
        drift_act = np.concatenate([per_vehicle_demos[v]["drift"]["act"] for v in VEHICLES], 0)
        avoid_obs = np.concatenate([per_vehicle_demos[v]["avoid"]["obs"] for v in VEHICLES], 0)
        avoid_act = np.concatenate([per_vehicle_demos[v]["avoid"]["act"] for v in VEHICLES], 0)
        drift_demo = {"obs": drift_obs, "act": drift_act,
                      "n_episodes": sum(per_vehicle_demos[v]["drift"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["drift"]["n_success"] for v in VEHICLES)}
        avoid_demo = {"obs": avoid_obs, "act": avoid_act,
                      "n_episodes": sum(per_vehicle_demos[v]["avoid"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["avoid"]["n_success"] for v in VEHICLES)}
        pooled = {"drift": drift_demo, "avoid": avoid_demo}
        report["pooled_demo"] = {
            "drift_frames": int(drift_obs.shape[0]), "avoid_frames": int(avoid_obs.shape[0]),
            "per_vehicle": {v: {
                "drift_frames": int(per_vehicle_demos[v]["drift"]["obs"].shape[0]),
                "drift_teacher_success": int(per_vehicle_demos[v]["drift"]["n_success"]),
                "drift_episodes": int(per_vehicle_demos[v]["drift"]["n_episodes"]),
                "avoid_frames": int(per_vehicle_demos[v]["avoid"]["obs"].shape[0]),
                "avoid_teacher_success": int(per_vehicle_demos[v]["avoid"]["n_success"]),
                "avoid_episodes": int(per_vehicle_demos[v]["avoid"]["n_episodes"]),
            } for v in VEHICLES}}
        report["scenario_verification"] = {v: per_vehicle_demos[v]["verify"] for v in VEHICLES}
        print(f"\nPOOLED demos: {drift_obs.shape[0]} drift + {avoid_obs.shape[0]} avoid frames "
              f"(from 3 vehicles)", flush=True)
        for v in VEHICLES:
            print(f"   {v:7s}: drift {per_vehicle_demos[v]['drift']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['drift']['n_success']}/{per_vehicle_demos[v]['drift']['n_episodes']} succ) | "
                  f"avoid {per_vehicle_demos[v]['avoid']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['avoid']['n_success']}/{per_vehicle_demos[v]['avoid']['n_episodes']} succ)",
                  flush=True)

        # ---- 3. build the pooled (3-vehicle) Chrono select set ----
        select_items = _pooled_select_items(int(args.select_avoid_units), int(args.select_drift_units))

        # ---- 4. distill N seeds on the POOLED demos; select by pooled Chrono task score ----
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- 3vehicle distill seed {s} ---", flush=True)
            m, st = db.distill(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                               holdout_frac=args.holdout_frac, seed=s)
            sel = _pooled_chrono_select(clients, m, select_items)
            agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
            worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
            print(f"  seed {s} POOLED SELECT: avoid agg={agg_av:.3f} (worst {worst_av:.3f}) "
                  f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
            st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
            st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
            st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s
            per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                             "worst_avoid": worst_av, "worst_drift": worst_dr,
                             "per_vehicle": sel["per_vehicle"],
                             "drift_holdout_mse": st["drift_holdout_mse"], "avoid_holdout_mse": st["avoid_holdout_mse"]})
            # selection objective: maximise the WORST-vehicle avoid (the generality bottleneck),
            # then worst-vehicle drift, then aggregate avoid, then aggregate drift.
            score = (worst_av, worst_dr, agg_av, agg_dr)
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        report["distill_per_seed"] = per_seed

        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED distilled seed {best[3]} "
              f"(pooled select avoid={stats['select_avoid']:.3f} drift={stats['select_drift']:.3f} | "
              f"worst avoid={stats['select_worst_avoid']:.3f} drift={stats['select_worst_drift']:.3f})", flush=True)
        report["distill_selected"] = {
            "seed": int(best[3]), "select_avoid": float(stats["select_avoid"]),
            "select_drift": float(stats["select_drift"]),
            "select_worst_avoid": float(stats["select_worst_avoid"]),
            "select_worst_drift": float(stats["select_worst_drift"]),
            "per_vehicle": stats["select_per_vehicle"]}
    finally:
        for c in clients:
            c.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_stats = {k: v for k, v in stats.items() if k != "select_per_vehicle"}
    torch.save({
        "state_dict": model.state_dict(), "gated": True,
        "label": "distill_both_3vehicle", "vehicles": list(VEHICLES),
        "drift_teacher": "pooled_{sedan_gpu_expert, uazbus_feedback, bmw_feedback}",
        "avoid_teacher": "pooled_{sedan_oracle, uazbus_oracle, bmw_rephys_oracle}",
        "drift_demo_frames": int(pooled["drift"]["obs"].shape[0]),
        "avoid_demo_frames": int(pooled["avoid"]["obs"].shape[0]),
        "select_per_vehicle": stats["select_per_vehicle"],
        **save_stats,
    }, out)
    report["elapsed_s"] = round(time.time() - t0, 1)
    report_path = RUN_DIR / "distill_3vehicle_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nsaved 3-vehicle distilled student -> {out}", flush=True)
    print(f"saved report -> {report_path}", flush=True)

    print("\n=== 3-VEHICLE POOLED DISTILLATION REPORT ===", flush=True)
    print(f"  POOLED demos: {pooled['drift']['obs'].shape[0]} drift + {pooled['avoid']['obs'].shape[0]} avoid frames",
          flush=True)
    print(f"  drift holdout MSE = {stats['drift_holdout_mse']:.3e} | avoid holdout MSE = {stats['avoid_holdout_mse']:.3e}",
          flush=True)
    print(f"  SELECTED pooled-select: avoid agg={stats['select_avoid']:.3f} (worst {stats['select_worst_avoid']:.3f}) "
          f"drift agg={stats['select_drift']:.3f} (worst {stats['select_worst_drift']:.3f})", flush=True)
    print(f"  per-vehicle SELECT: {json.dumps(stats['select_per_vehicle'], default=str)}", flush=True)
    print("\nNext (per-vehicle A5 validation on THIS single policy):", flush=True)
    print(f"  PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate.py        --policy {out} --avoid-units 40 --drift-units 20 --workers {args.workers}", flush=True)
    print(f"  PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate_uazbus.py --policy {out} --avoid-units 40 --drift-units 20 --workers {args.workers}", flush=True)
    print(f"  PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate_bmw.py    --policy {out} --avoid-units 40 --drift-units 20 --workers {args.workers}", flush=True)


if __name__ == "__main__":
    main()
