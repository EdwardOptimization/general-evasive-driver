r"""FINAL INTEGRATED do-both driver: ONE FiLM network over the FULL drift+avoid SPECTRUM x ALL 3
vehicles -- the strongest, most general active-safety driver. Combines the TWO PROVEN pieces:

  * S1 full-scenario spectrum (distill_both_fullscenario.py): the 48-cell drift+avoid SPECTRUM --
    12 drift cells (beta*{0.18,0.28,0.36,0.45} x mu{0.35,0.45,0.55}, the precheck-feasible drift
    grid) + 36 avoid cells (reveal x mu x geometry, feasibility_fullscenario.json). THIS IS THE
    CELL SET.
  * FiLM cross-vehicle (distill_both_3vehicle_film.py): ONE network = a shared trunk with PER-
    VEHICLE FiLM (gamma/beta from the vehicle one-hot) + 1 shared DRIFT head + 3 per-vehicle AVOID
    heads + per-vehicle DAgger + worst-(vehicle) selection. THIS IS THE ARCHITECTURE.

The combination: the FiLM driver (obs75 = obs72 + 3-way vehicle one-hot) is BC-distilled on the
POOLED demos of {12 drift cells x 3 vehicles (only the per-vehicle FEASIBLE ones) + 36 avoid cells
x 3 vehicles}, then per-vehicle DAgger closes the closed-loop avoid gap, then seed-sweep + worst-
(vehicle,regime) selection, then VALIDATE per-(vehicle, cell-group) on Chrono.

DRIFT teachers (the 12 beta*xmu cells PER VEHICLE):
  Drift is physics-feasible at DIFFERENT entry speeds per vehicle (Sedan ~v12, UAZBUS power-over-
  steers low ~v6, BMW only at HIGH speed ~v16). So we GROUND each vehicle's feasible (cell, speed,
  spec) set in Chrono via spectrum_per_vehicle_drift_precheck.py FIRST (auto-run if its JSON is
  missing). Sedan = 12/12 @v12 (known). For each FEASIBLE (cell, vehicle) we run the tuned
  DriftFeedbackPolicy (the precheck winner spec for that cell/vehicle) at the cell's feasible entry
  speed. The ONE shared drift head + FiLM covers all feasible (cell, vehicle) drift pairs (drift
  generalizes, S2).

AVOID teachers (the 36 reveal x mu x geometry cells PER VEHICLE):
  The avoid cells are scenario-defined (vehicle-agnostic geometry). Per vehicle we run that vehicle's
  RE-PHYSICALIZED avoid oracle (Sedan default / UAZBUS Sedan-fitted oracle on the UAZBUS variant+mass
  / BMW re-physicalized FZR 9059.6 V_KNOTS 12). 3 per-vehicle avoid heads.

Then: pool all demos -> BC the FiLM driver -> per-vehicle DAgger (rounds) -> seed sweep + WORST-
(vehicle,regime) selection. Save distill_final_integrated_policy.pt. Validate PER-(vehicle, cell-
group) on Chrono: drift success over the feasible drift cells + avoid success over the avoid cells,
per vehicle, feeding the correct one-hot.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_final_integrated.py \
        --workers 16 --drift-seeds-per-cell 4 --avoid-seeds-per-cell 3 \
        --epochs 4000 --seed-sweep 3 --dagger-rounds 2 \
        --val-drift-seeds 5 --val-avoid-seeds 4 \
        --out runs/feasibility_audit/phase4_f2/distill_final_integrated_policy.pt
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
import phase4_e4_drift_regime_pricing as e4  # noqa: E402
import distill_both as db  # noqa: E402
import distill_both_uazbus as uaz  # noqa: E402
import distill_both_bmw as bmw  # noqa: E402
import distill_both_3vehicle as d3v  # noqa: E402  (per-vehicle patch install/verify, VERBATIM)
import distill_both_3vehicle_conditioned as cond  # noqa: E402  (one-hot helpers, VERBATIM)
import distill_both_3vehicle_film as film  # noqa: E402  (FiLM model + _distill_film + DAgger, VERBATIM)
import distill_both_fullscenario as fs  # noqa: E402  (avoid cell catalog + geometry scenario, VERBATIM)
import spectrum_s1_feasibility_precheck as precheck  # noqa: E402  (specs_for, scen, read-only)
import spectrum_per_vehicle_drift_precheck as pvpre  # noqa: E402  (per-vehicle feasible drift cells)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_final_integrated_policy.pt"
PV_PRECHECK_JSON = REPO_ROOT / "runs" / "feasibility_audit" / "spectrum_s1" / "feasibility_precheck_per_vehicle.json"

ResilientChronoClient = uaz.ResilientChronoClient

VEHICLES = cond.VEHICLES                 # ("sedan", "uazbus", "bmw")
ONEHOT_DIM = cond.ONEHOT_DIM             # 3
COND_OBS_DIM = cond.COND_OBS_DIM         # 75
OBS72_DIM = f2.HUMAN_VIEW_OBS_DIM        # 72
_vehicle_onehot = cond._vehicle_onehot
_append_onehot = cond._append_onehot
FiLMAvoidActorCritic = film.FiLMAvoidActorCritic

AVOID_MAX_STEPS = fs.AVOID_MAX_STEPS     # 285
DRIFT_MAX_STEPS = fs.DRIFT_MAX_STEPS     # 90

# DAgger hard-avoid spectrum cells: the small-reveal/low-grip corner where closed-loop compound
# error shows up (reused from dagger_avoid / the FiLM build).
import dagger_avoid as dag  # noqa: E402
HARD_AVOID_CELLS = tuple((float(r), float(m)) for r in dag.HARD_REVEALS for m in dag.HARD_MUS)


# ============================================================ per-vehicle DRIFT spectrum cells
# (12 beta*xmu cells, PRUNED to each vehicle's Chrono-feasible set + each cell's feasible
#  speed + winning DriftFeedbackPolicy spec, from spectrum_per_vehicle_drift_precheck.json)


def _ensure_pv_precheck(vehicles: tuple[str, ...]) -> dict[str, Any]:
    """Load (or run, if missing) the per-vehicle drift feasibility precheck for the given vehicles."""
    need_run = True
    if PV_PRECHECK_JSON.exists():
        data = json.loads(PV_PRECHECK_JSON.read_text())
        if all(v in data.get("per_vehicle", {}) for v in vehicles):
            need_run = False
    if need_run:
        print(f"[final-integrated] per-vehicle drift precheck missing for {vehicles}; running it now "
              f"(oracle rollouts, no training)...", flush=True)
        cmd = [sys.executable, str(SCRIPTS_DIR / "spectrum_per_vehicle_drift_precheck.py"),
               "--vehicles", *vehicles]
        env = {"PYTHONPATH": str(REPO_ROOT / "src")}
        import os
        full_env = dict(os.environ); full_env.update(env)
        subprocess.run(cmd, check=True, env=full_env, cwd=str(REPO_ROOT))
        data = json.loads(PV_PRECHECK_JSON.read_text())
    return data


def _spec_by_name(beta: float, name: str, vehicle: str) -> e4.DriftFeedbackSpec:
    """Resolve a DriftFeedbackPolicy spec by name from the per-vehicle candidate set."""
    for s in pvpre._candidate_specs(vehicle, beta):
        if s.name == name:
            return s
    raise KeyError(f"spec {name!r} not found for vehicle {vehicle} beta {beta}")


def _vehicle_drift_cells(vehicle: str, pv_data: dict[str, Any]) -> list[dict[str, Any]]:
    """The FEASIBLE drift spectrum cells for a vehicle (cell + winning speed/spec from the precheck)."""
    feas = pv_data["per_vehicle"][vehicle]["feasible_cells"]
    cells = []
    for c in feas:
        mu, beta = float(c["mu"]), float(c["beta"])
        spec = _spec_by_name(beta, c["spec"], vehicle)
        cells.append({"vehicle": vehicle, "mu": mu, "beta": beta, "speed": float(c["speed"]),
                      "spec": spec, "spec_name": spec.name, "precheck_sustain": int(c["longest"]),
                      "cell_id": f"drift-{vehicle}-mu{mu:.2f}-b{beta:.2f}"})
    return cells


def _drift_scenario(vehicle: str, cell: dict, seed: int) -> dict:
    """Per-vehicle drift spectrum scenario (precheck _scen with the vehicle's variant+mass+speed)."""
    sc = pvpre._scen(vehicle, cell["mu"], cell["speed"], cell["beta"], seed)
    sc["scenario_id"] = f"final-{cell['cell_id']}-seed{seed}"
    sc["max_steps"] = DRIFT_MAX_STEPS
    return sc


def _drift_teacher(cell: dict):
    return e4.DriftFeedbackPolicy(cell["spec"], side=cell["beta"])


# ============================================================ per-vehicle AVOID spectrum cells
# (36 reveal x mu x geometry cells, vehicle-agnostic geometry; per vehicle run on that vehicle's
#  variant+mass + re-physicalized avoid oracle by installing the vehicle's patches.)


def _load_avoid_cells() -> list[dict]:
    return fs._load_avoid_cells()


def _avoid_scenario(vehicle: str, cell: dict, seed: int) -> dict:
    """Per-vehicle avoid scenario: install the vehicle's patches so f2._avoidance_scenario carries
    the right variant+mass, then apply the cell's geometry (offset/half-width)."""
    sc = f2._avoidance_scenario(int(seed), max_steps=AVOID_MAX_STEPS,
                                reveal=float(cell["reveal"]), mu=float(cell["mu"]))
    fs.avoid_feas._apply_geometry(sc, lateral_offset_m=cell["lateral_offset_m"],
                                  half_width_m=cell["half_width_m"])
    sc["scenario_id"] = f"final-{cell['cell_id']}-{vehicle}-seed{seed}"
    sc["max_steps"] = AVOID_MAX_STEPS
    return sc


def _avoid_teacher(cell: dict):
    """The (per-vehicle re-physicalized, via installed patches) avoid oracle for this cell."""
    return f2.make_avoidance_teacher(reveal=cell["reveal"], mu=cell["mu"]).factory()


# ============================================================ demo collection (per vehicle, pooled)


def _drift_demo_specs(vehicle: str, cells: list[dict], seeds_per_cell: int) -> list[dict]:
    specs = []
    for ci, cell in enumerate(cells):
        for i in range(seeds_per_cell):
            seed = int(f2._seed_for("final_drift", vehicle, ci, i, round(cell["mu"], 3), round(cell["beta"], 3)))
            specs.append({"regime": "drift", "cell": cell, "seed": seed,
                          "scenario": _drift_scenario(vehicle, cell, seed)})
    return specs


def _avoid_demo_specs(vehicle: str, cells: list[dict], seeds_per_cell: int) -> list[dict]:
    specs = []
    for ci, cell in enumerate(cells):
        for i in range(seeds_per_cell):
            seed = int(f2._seed_for("final_avoid", vehicle, ci, i, round(cell["reveal"], 3),
                                    round(cell["mu"], 4), cell["geometry"]))
            specs.append({"regime": "avoidance", "cell": cell, "seed": seed,
                          "scenario": _avoid_scenario(vehicle, cell, seed)})
    return specs


def _collect_spectrum_demos(clients, specs: list[dict], *, label: str) -> dict:
    """Run each spec's teacher episode W-way parallel; pool obs72 -> teacher_action frames.
    The teacher is a per-cell drift OR avoid teacher (built from the cell), and the vehicle's
    patches MUST be installed before calling (so the avoid oracle is the re-physicalized one)."""
    results: list[dict | None] = [None] * len(specs)
    n_workers = min(len(clients), len(specs)) if specs else 0
    next_i = 0
    lock = threading.Lock()
    n_success = [0]

    def _worker(wi: int) -> None:
        nonlocal next_i
        client = clients[wi]
        while True:
            with lock:
                if next_i >= len(specs):
                    return
                i = next_i
                next_i += 1
            sp = specs[i]
            cell = sp["cell"]
            if sp["regime"] == "drift":
                policy = _drift_teacher(cell)
                reveal, mu = 0.0, cell["mu"]
            else:
                policy = _avoid_teacher(cell)
                reveal, mu = cell["reveal"], cell["mu"]
            res = f2.run_episode(client, sp["scenario"], sp["regime"], policy,
                                 seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal), collect="bc")
            results[i] = res
            if res["success"]:
                with lock:
                    n_success[0] += 1

    t0 = time.time()
    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    dt = time.time() - t0
    frames, targets = [], []
    for res in results:
        if res is None or res["bc_frames"].shape[0] == 0:
            continue
        frames.append(res["bc_frames"])
        targets.append(res["bc_targets"])
    obs = np.concatenate(frames, 0) if frames else np.zeros((0, OBS72_DIM), np.float32)
    act = np.concatenate(targets, 0) if targets else np.zeros((0, f2.ACT_DIM), np.float32)
    print(f"  [{label}] {len(specs)} episodes ({n_success[0]} teacher-success), "
          f"{obs.shape[0]} obs72->action frames, {dt:.1f}s", flush=True)
    return {"obs": obs, "act": act, "n_episodes": len(specs), "n_success": n_success[0]}


def _collect_vehicle_demos(vehicle: str, clients, drift_cells: list[dict], avoid_cells: list[dict],
                           *, drift_seeds_per_cell: int, avoid_seeds_per_cell: int) -> dict[str, Any]:
    """Install the vehicle's patches, verify variant, collect its drift + avoid spectrum demos."""
    d3v._install_vehicle(vehicle)
    verify = d3v._verify_vehicle_scenarios(vehicle, clients)
    if not verify["variant_ok"]:
        raise SystemExit(f"FATAL [{vehicle}]: scenarios are NOT carrying the {vehicle} variant; aborting.")
    drift_specs = _drift_demo_specs(vehicle, drift_cells, drift_seeds_per_cell)
    avoid_specs = _avoid_demo_specs(vehicle, avoid_cells, avoid_seeds_per_cell)
    print(f"[{vehicle}] collecting {len(drift_specs)} drift ({len(drift_cells)} feasible cells) + "
          f"{len(avoid_specs)} avoid ({len(avoid_cells)} cells) demo episodes", flush=True)
    drift_demo = _collect_spectrum_demos(clients, drift_specs, label=f"DRIFT[{vehicle}]")
    avoid_demo = _collect_spectrum_demos(clients, avoid_specs, label=f"AVOID[{vehicle}]")
    if drift_demo["obs"].shape[0] == 0 or avoid_demo["obs"].shape[0] == 0:
        raise SystemExit(f"FATAL [{vehicle}]: a regime collected 0 demo frames; cannot pool.")
    return {"verify": verify, "drift": drift_demo, "avoid": avoid_demo}


# ============================================================ Chrono eval (per (vehicle, cell-group))
# The student is the FiLM model; we feed obs72 + the vehicle's one-hot (obs75). The eval drives
# model.act only (no oracle), so the avoid oracle physicalization is irrelevant for eval -- but we
# install the vehicle's patches so scenarios reset on the right backend variant.


def _cond_policy(model, vehicle: str):
    oh = _vehicle_onehot(vehicle)

    def _p(step: int, obs: np.ndarray) -> np.ndarray:
        obs75 = np.concatenate([np.asarray(obs, dtype=np.float32), oh], 0)
        return model.act(obs75)
    return _p


def _eval_cells(clients, model, vehicle: str, specs: list[dict], *, label: str) -> list[dict]:
    """Run the FiLM student per-cell on Chrono (with the vehicle's one-hot); per-cell success."""
    results: list[dict | None] = [None] * len(specs)
    n_workers = min(len(clients), len(specs)) if specs else 0
    next_i = 0
    lock = threading.Lock()
    policy = _cond_policy(model, vehicle)

    def _worker(wi: int) -> None:
        nonlocal next_i
        client = clients[wi]
        while True:
            with lock:
                if next_i >= len(specs):
                    return
                i = next_i
                next_i += 1
            sp = specs[i]
            cell = sp["cell"]
            if sp["regime"] == "drift":
                reveal, mu = 0.0, cell["mu"]
            else:
                reveal, mu = cell["reveal"], cell["mu"]
            res = f2.run_episode(client, sp["scenario"], sp["regime"], policy,
                                 seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal))
            results[i] = {"success": bool(res["success"]),
                          "sustain": int(res["longest_controlled_drift_run"]),
                          "collision": bool(res["collision"])}

    t0 = time.time()
    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    by_cell: dict[str, dict] = {}
    for sp, r in zip(specs, results):
        cid = sp["cell"]["cell_id"]
        agg = by_cell.setdefault(cid, {"cell": sp["cell"], "regime": sp["regime"], "n": 0, "n_succ": 0,
                                       "sustains": []})
        agg["n"] += 1
        agg["n_succ"] += int(r["success"]) if r else 0
        if sp["regime"] == "drift" and r:
            agg["sustains"].append(int(r["sustain"]))
    rows = []
    for cid, agg in by_cell.items():
        c = agg["cell"]
        row = {"cell_id": cid, "regime": agg["regime"], "n": agg["n"], "n_succ": agg["n_succ"],
               "success": agg["n_succ"] / max(1, agg["n"])}
        if agg["regime"] == "drift":
            row.update({"mu": c["mu"], "beta": c["beta"], "spec": c["spec_name"],
                        "precheck_sustain": c["precheck_sustain"],
                        "mean_sustain": float(np.mean(agg["sustains"])) if agg["sustains"] else 0.0})
        else:
            row.update({"reveal": c["reveal"], "mu": c["mu"], "geometry": c["geometry"]})
        rows.append(row)
    print(f"  [{label}] {len(specs)} episodes over {len(rows)} cells in {time.time()-t0:.1f}s", flush=True)
    return rows


def _select_specs(vehicle: str, drift_cells: list[dict], avoid_cells: list[dict],
                  *, n_drift: int, n_avoid: int, namespace: str) -> list[dict]:
    """Disjoint-namespace select/validation specs (per-cell). MUST be built with the vehicle
    patches installed (avoid scenarios are vehicle-patched globals)."""
    specs = []
    for ci, cell in enumerate(drift_cells):
        for i in range(n_drift):
            seed = int(f2._seed_for(namespace, vehicle, "drift", ci, i, round(cell["mu"], 3), round(cell["beta"], 3)))
            specs.append({"regime": "drift", "cell": cell, "seed": seed,
                          "scenario": _drift_scenario(vehicle, cell, seed)})
    for ci, cell in enumerate(avoid_cells):
        for i in range(n_avoid):
            seed = int(f2._seed_for(namespace, vehicle, "avoid", ci, i, round(cell["reveal"], 3),
                                    round(cell["mu"], 4), cell["geometry"]))
            specs.append({"regime": "avoidance", "cell": cell, "seed": seed,
                          "scenario": _avoid_scenario(vehicle, cell, seed)})
    return specs


def _build_select_specs(drift_cells_by_v, avoid_cells, *, n_drift, n_avoid, namespace) -> dict[str, list[dict]]:
    out = {}
    for v in VEHICLES:
        d3v._install_vehicle(v)
        out[v] = _select_specs(v, drift_cells_by_v[v], avoid_cells, n_drift=n_drift, n_avoid=n_avoid,
                               namespace=namespace)
    return out


def _select_eval(clients, model, select_specs: dict[str, list[dict]]) -> dict[str, Any]:
    """Per-vehicle, per-regime select success over the spectrum cells (cheap seed count)."""
    per_vehicle = {}
    all_avoid, all_drift = [], []
    for v in VEHICLES:
        d3v._install_vehicle(v)
        rows = _eval_cells(clients, model, v, select_specs[v], label=f"SELECT[{v}]")
        dr = [r["success"] for r in rows if r["regime"] == "drift"]
        av = [r["success"] for r in rows if r["regime"] == "avoidance"]
        # cell-level mean success (mean over cells of per-cell success rate)
        dr_m = float(np.mean(dr)) if dr else 0.0
        av_m = float(np.mean(av)) if av else 0.0
        per_vehicle[v] = {"avoid": av_m, "drift": dr_m}
        all_avoid.append(av_m); all_drift.append(dr_m)
        print(f"    [{v}] select avoid={av_m:.3f} drift={dr_m:.3f}", flush=True)
    agg = {"avoidance": float(np.mean(all_avoid)), "drift": float(np.mean(all_drift))}
    worst = {"avoidance": float(np.min(all_avoid)), "drift": float(np.min(all_drift))}
    return {"per_vehicle": per_vehicle, "aggregate": agg, "worst": worst}


# ============================================================ per-vehicle DAgger on avoid spectrum


def _dagger_avoid_specs(vehicle: str, avoid_cells: list[dict], *, hard_seeds: int, easy_seeds: int,
                        round_idx: int) -> list[dict]:
    """Hard-avoid-focused DAgger rollout specs over the 36-cell avoid spectrum for this vehicle.
    Cells whose (reveal,mu) is in the hard corner get hard_seeds rollouts; others get easy_seeds.
    Disjoint 'final_dagger' seed namespace keyed by (vehicle, round). Vehicle patches MUST be
    installed so the oracle (queried inside _dagger_episode) is the per-vehicle re-physicalized one."""
    hard_set = {(round(r, 4), round(m, 4)) for (r, m) in HARD_AVOID_CELLS}
    specs = []
    for ci, cell in enumerate(avoid_cells):
        is_hard = (round(cell["reveal"], 4), round(cell["mu"], 4)) in hard_set
        n = hard_seeds if is_hard else easy_seeds
        for i in range(n):
            seed = int(f2._seed_for("final_dagger", vehicle, round_idx, ci, i,
                                    round(cell["reveal"], 4), round(cell["mu"], 4), cell["geometry"]))
            specs.append({"regime": "avoidance", "reveal": float(cell["reveal"]), "mu": float(cell["mu"]),
                          "seed": seed, "scenario": _avoid_scenario(vehicle, cell, seed), "is_hard": is_hard})
    return specs


def _dagger_collect_per_vehicle(clients, model, avoid_cells, *, hard_seeds, easy_seeds, round_idx):
    """Roll the CURRENT FiLM student out PER VEHICLE on the avoid spectrum; relabel visited reveal-
    post states with that vehicle's avoid oracle. Returns per-vehicle one-hot-tagged recovery labels."""
    out = {}
    for v in VEHICLES:
        d3v._install_vehicle(v)
        specs = _dagger_avoid_specs(v, avoid_cells, hard_seeds=hard_seeds, easy_seeds=easy_seeds,
                                    round_idx=round_idx)
        n_hard = sum(1 for s in specs if s["is_hard"])
        oh_student = film._OneHotStudent(model, v)
        dagout = dag.collect_dagger(clients, specs, oh_student)
        obs72 = dagout["obs"]
        obs75 = _append_onehot(obs72, v) if obs72.shape[0] > 0 else np.zeros((0, COND_OBS_DIM), np.float32)
        out[v] = {"obs75": obs75, "act": dagout["act"],
                  "n_episodes": int(dagout["n_episodes"]), "n_success": int(dagout["n_success"]),
                  "n_offtrack": int(dagout["n_offtrack"]), "n_collision": int(dagout["n_collision"]),
                  "n_other_fail": int(dagout["n_other_fail"]), "n_hard_eps": int(n_hard),
                  "fail_cells": dagout["fail_cells"], "labels": int(obs75.shape[0])}
        succ = dagout["n_success"] / max(1, dagout["n_episodes"])
        print(f"    [{v}] DAgger rollout: {dagout['n_success']}/{dagout['n_episodes']} succ ({succ:.3f}; "
              f"off={dagout['n_offtrack']} coll={dagout['n_collision']} other={dagout['n_other_fail']}) "
              f"-> {obs75.shape[0]} recovery labels", flush=True)
    return out


# ============================================================ main


def main() -> None:
    ap = argparse.ArgumentParser(description="FINAL integrated FiLM driver over the full drift+avoid spectrum x 3 vehicles.")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds-per-cell", type=int, default=4, help="drift demo seeds per FEASIBLE drift cell PER vehicle")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=3, help="avoid demo seeds per avoid cell PER vehicle")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--dagger-epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--dagger-rounds", type=int, default=2)
    ap.add_argument("--dagger-hard-cell-seeds", type=int, default=6)
    ap.add_argument("--dagger-easy-cell-seeds", type=int, default=1)
    ap.add_argument("--select-drift-seeds", type=int, default=2, help="per-cell drift seeds for seed SELECTION")
    ap.add_argument("--select-avoid-seeds", type=int, default=2, help="per-cell avoid seeds for seed SELECTION")
    ap.add_argument("--val-drift-seeds", type=int, default=5, help="per-cell drift seeds for FINAL validation")
    ap.add_argument("--val-avoid-seeds", type=int, default=4, help="per-cell avoid seeds for FINAL validation")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    # ---- 0. ground each vehicle's feasible drift spectrum cells (precheck; auto-run if missing) ----
    pv_data = _ensure_pv_precheck(VEHICLES)
    drift_cells_by_v = {v: _vehicle_drift_cells(v, pv_data) for v in VEHICLES}
    avoid_cells = _load_avoid_cells()
    print(f"\n[final-integrated] FULL SPECTRUM x 3 vehicles:", flush=True)
    for v in VEHICLES:
        print(f"  {v:7s}: {len(drift_cells_by_v[v])}/12 feasible drift cells + {len(avoid_cells)} avoid cells", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"final_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {
        "vehicles": list(VEHICLES), "onehot_dim": ONEHOT_DIM, "cond_obs_dim": COND_OBS_DIM,
        "architecture": "FiLM_shared_trunk(per_vehicle_gamma_beta) + regime_gate + 1_drift_head + 3_avoid_heads(routed) + per_vehicle_DAgger",
        "spectrum": {"drift_cells_per_vehicle": {v: len(drift_cells_by_v[v]) for v in VEHICLES},
                     "avoid_cells": len(avoid_cells)},
        "drift_feasible_cells": {v: [c["cell_id"] for c in drift_cells_by_v[v]] for v in VEHICLES},
        "dagger_rounds": int(args.dagger_rounds)}
    t0 = time.time()
    best = None  # (score, state, stats, seed, sel)
    pooled = None
    avoid_demo = None
    dagger_history: list[dict] = []
    try:
        # ---- 1. collect demos PER vehicle over the spectrum ----
        per_vehicle_demos: dict[str, Any] = {}
        for v in VEHICLES:
            print(f"\n################### COLLECTING {v.upper()} SPECTRUM DEMOS ###################", flush=True)
            per_vehicle_demos[v] = _collect_vehicle_demos(
                v, clients, drift_cells_by_v[v], avoid_cells,
                drift_seeds_per_cell=args.drift_seeds_per_cell, avoid_seeds_per_cell=args.avoid_seeds_per_cell)

        # ---- 2. append one-hot, pool (drift pooled; avoid kept per-vehicle for DAgger) ----
        drift_obs = np.concatenate([_append_onehot(per_vehicle_demos[v]["drift"]["obs"], v) for v in VEHICLES], 0)
        drift_act = np.concatenate([per_vehicle_demos[v]["drift"]["act"] for v in VEHICLES], 0)
        per_vehicle_avoid = {v: {"obs75": _append_onehot(per_vehicle_demos[v]["avoid"]["obs"], v),
                                 "act": np.asarray(per_vehicle_demos[v]["avoid"]["act"], dtype=np.float32)}
                             for v in VEHICLES}
        per_vehicle_base_n = {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES}

        def _pool_avoid():
            ao = np.concatenate([per_vehicle_avoid[v]["obs75"] for v in VEHICLES], 0).astype(np.float32)
            aa = np.concatenate([per_vehicle_avoid[v]["act"] for v in VEHICLES], 0).astype(np.float32)
            return {"obs": ao, "act": aa,
                    "n_episodes": sum(per_vehicle_demos[v]["avoid"]["n_episodes"] for v in VEHICLES),
                    "n_success": sum(per_vehicle_demos[v]["avoid"]["n_success"] for v in VEHICLES)}

        drift_demo = {"obs": drift_obs, "act": drift_act,
                      "n_episodes": sum(per_vehicle_demos[v]["drift"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["drift"]["n_success"] for v in VEHICLES)}
        avoid_demo = _pool_avoid()
        assert drift_obs.shape[1] == COND_OBS_DIM and avoid_demo["obs"].shape[1] == COND_OBS_DIM
        pooled = {"drift": drift_demo, "avoid": avoid_demo}
        report["pooled_demo"] = {
            "drift_frames": int(drift_obs.shape[0]), "avoid_frames": int(avoid_demo["obs"].shape[0]),
            "per_vehicle": {v: {
                "drift_cells": len(drift_cells_by_v[v]),
                "drift_frames": int(per_vehicle_demos[v]["drift"]["obs"].shape[0]),
                "drift_teacher_success": int(per_vehicle_demos[v]["drift"]["n_success"]),
                "drift_episodes": int(per_vehicle_demos[v]["drift"]["n_episodes"]),
                "avoid_frames": int(per_vehicle_base_n[v]),
                "avoid_teacher_success": int(per_vehicle_demos[v]["avoid"]["n_success"]),
                "avoid_episodes": int(per_vehicle_demos[v]["avoid"]["n_episodes"]),
                "onehot": list(_vehicle_onehot(v))} for v in VEHICLES}}
        report["scenario_verification"] = {v: per_vehicle_demos[v]["verify"] for v in VEHICLES}
        print(f"\nPOOLED spectrum demos: {drift_obs.shape[0]} drift + {avoid_demo['obs'].shape[0]} avoid frames "
              f"(obs{COND_OBS_DIM}, 3 vehicles WITH one-hot)", flush=True)

        # ---- 3. build select specs (cheap per-cell seed count) ----
        select_specs = _build_select_specs(drift_cells_by_v, avoid_cells,
                                           n_drift=args.select_drift_seeds, n_avoid=args.select_avoid_seeds,
                                           namespace="final_select")

        # ---- 4. BC-distill N seeds; select by WORST-vehicle avoid (then worst drift, then agg) ----
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- FINAL FiLM BC distill seed {s} ---", flush=True)
            m, st = film._distill_film(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                                       holdout_frac=args.holdout_frac, seed=s)
            sel = _select_eval(clients, m, select_specs)
            agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
            worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
            print(f"  seed {s} SELECT: avoid agg={agg_av:.3f} (WORST {worst_av:.3f}) "
                  f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
            st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
            st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
            st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s
            per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                             "worst_avoid": worst_av, "worst_drift": worst_dr, "per_vehicle": sel["per_vehicle"]})
            score = (worst_av, worst_dr, agg_av, agg_dr)
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        report["bc_distill_per_seed"] = per_seed
        bc_score, bc_state, bc_stats, bc_seed, bc_sel = best
        print(f"\nBEST BC seed {bc_seed}: WORST avoid={bc_score[0]:.3f} worst drift={bc_score[1]:.3f} "
              f"(agg avoid={bc_score[2]:.3f} drift={bc_score[3]:.3f}) -> DAgger warm-start", flush=True)
        report["bc_selected"] = {"seed": int(bc_seed), "worst_avoid": float(bc_score[0]),
                                 "worst_drift": float(bc_score[1]), "per_vehicle": bc_sel["per_vehicle"]}

        # ---- 5. per-vehicle DAgger on the avoid spectrum (drift FROZEN) ----
        cur_model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
        cur_model.load_state_dict(bc_state)
        cur_model.eval()
        for rd in range(int(args.dagger_rounds)):
            print(f"\n========================= DAgger ROUND {rd} (per vehicle, avoid spectrum) =========================", flush=True)
            dag_out = _dagger_collect_per_vehicle(clients, cur_model, avoid_cells,
                                                  hard_seeds=args.dagger_hard_cell_seeds,
                                                  easy_seeds=args.dagger_easy_cell_seeds, round_idx=rd)
            for v in VEHICLES:
                if dag_out[v]["obs75"].shape[0] > 0:
                    per_vehicle_avoid[v]["obs75"] = np.concatenate(
                        [per_vehicle_avoid[v]["obs75"], dag_out[v]["obs75"]], 0).astype(np.float32)
                    per_vehicle_avoid[v]["act"] = np.concatenate(
                        [per_vehicle_avoid[v]["act"], dag_out[v]["act"]], 0).astype(np.float32)
            avoid_demo = _pool_avoid()
            for v in VEHICLES:
                print(f"  [{v}] avoid pool: {per_vehicle_avoid[v]['obs75'].shape[0]} frames "
                      f"(base {per_vehicle_base_n[v]} + DAgger {per_vehicle_avoid[v]['obs75'].shape[0]-per_vehicle_base_n[v]})",
                      flush=True)
            round_best = None
            round_per_seed = []
            for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
                print(f"\n--- DAgger round {rd} re-BC seed {s} ---", flush=True)
                m, st = film._distill_film(drift_demo, avoid_demo, epochs=args.dagger_epochs, lr=args.lr,
                                           batch=args.batch, holdout_frac=args.holdout_frac, seed=s,
                                           init_state=bc_state)
                sel = _select_eval(clients, m, select_specs)
                agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
                worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
                print(f"  round {rd} seed {s} SELECT: avoid agg={agg_av:.3f} (WORST {worst_av:.3f}) "
                      f"drift agg={agg_dr:.3f} (worst {worst_dr:.3f})", flush=True)
                st["select_avoid"] = agg_av; st["select_drift"] = agg_dr
                st["select_worst_avoid"] = worst_av; st["select_worst_drift"] = worst_dr
                st["select_per_vehicle"] = sel["per_vehicle"]; st["distill_seed"] = s; st["dagger_round"] = rd
                round_per_seed.append({"seed": s, "select_avoid": agg_av, "select_drift": agg_dr,
                                       "worst_avoid": worst_av, "worst_drift": worst_dr, "per_vehicle": sel["per_vehicle"]})
                score = (worst_av, worst_dr, agg_av, agg_dr)
                if round_best is None or score > round_best[0]:
                    round_best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
                if score > best[0]:
                    best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
            r_score, r_state, r_stats, r_seed, r_sel = round_best
            cur_model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
            cur_model.load_state_dict(r_state)
            cur_model.eval()
            dagger_history.append({
                "round": rd, "round_best_seed": int(r_seed),
                "round_best_worst_avoid": float(r_score[0]), "round_best_worst_drift": float(r_score[1]),
                "round_best_agg_avoid": float(r_score[2]), "round_best_agg_drift": float(r_score[3]),
                "round_best_per_vehicle": r_sel["per_vehicle"], "per_seed": round_per_seed,
                "rollout": {v: {k: dag_out[v][k] for k in
                                ("n_episodes", "n_success", "n_offtrack", "n_collision", "n_other_fail",
                                 "n_hard_eps", "labels")} for v in VEHICLES},
                "avoid_pool_frames": {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES}})
            print(f"\n  ROUND {rd} BEST seed {r_seed}: WORST avoid={r_score[0]:.3f} (agg {r_score[2]:.3f}) "
                  f"worst drift={r_score[1]:.3f} (agg {r_score[3]:.3f})", flush=True)
        report["dagger_history"] = dagger_history

        # ---- 6. finalize globally-best model ----
        model = FiLMAvoidActorCritic(obs_dim=COND_OBS_DIM)
        model.load_state_dict(best[1])
        stats = best[2]
        sel_round = stats.get("dagger_round", "BC")
        print(f"\nSELECTED seed {best[3]} (round {sel_round}) on WORST-vehicle avoid "
              f"(WORST avoid={stats['select_worst_avoid']:.3f} worst drift={stats['select_worst_drift']:.3f})", flush=True)
        report["distill_selected"] = {
            "seed": int(best[3]), "dagger_round": sel_round,
            "select_worst_avoid": float(stats["select_worst_avoid"]),
            "select_worst_drift": float(stats["select_worst_drift"]),
            "select_avoid": float(stats["select_avoid"]), "select_drift": float(stats["select_drift"]),
            "per_vehicle": stats["select_per_vehicle"]}

        # ---- 7. save BEFORE the (longer) per-cell validation ----
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_stats = {k: vv for k, vv in stats.items() if k != "select_per_vehicle"}
        torch.save({
            "state_dict": model.state_dict(), "gated": True, "model_class": "FiLMAvoidActorCritic",
            "obs_dim": COND_OBS_DIM, "onehot_dim": ONEHOT_DIM, "vehicle_order": list(VEHICLES),
            "label": "distill_both_final_integrated", "vehicles": list(VEHICLES),
            "architecture": report["architecture"],
            "spectrum": report["spectrum"], "drift_feasible_cells": report["drift_feasible_cells"],
            "drift_teacher": "per_vehicle_tuned_DriftFeedbackPolicy over feasible 12-cell spectrum",
            "avoid_teacher": "per_vehicle_rephysicalized_oracle over 36-cell spectrum + per_vehicle_DAgger",
            "drift_demo_frames": int(pooled["drift"]["obs"].shape[0]),
            "avoid_demo_frames_final": int(avoid_demo["obs"].shape[0]),
            "per_vehicle_avoid_frames_final": {v: int(per_vehicle_avoid[v]["obs75"].shape[0]) for v in VEHICLES},
            "dagger_rounds": int(args.dagger_rounds), "selected_dagger_round": sel_round,
            **save_stats}, out)
        print(f"\nsaved FINAL integrated FiLM student -> {out}", flush=True)

        # ---- 8. per-(vehicle, cell-group) FINAL validation on Chrono (correct one-hot) ----
        print(f"\n=== FINAL PER-(VEHICLE, CELL-GROUP) CHRONO VALIDATION "
              f"({args.val_drift_seeds} drift / {args.val_avoid_seeds} avoid seeds per cell) ===", flush=True)
        val = {}
        for v in VEHICLES:
            print(f"\n################### VALIDATE {v.upper()} (one-hot fed) ###################", flush=True)
            d3v._install_vehicle(v)
            verify = d3v._verify_vehicle_scenarios(v, clients)
            if not verify["variant_ok"]:
                raise SystemExit(f"FATAL [{v}]: validation scenarios NOT carrying the {v} variant; aborting.")
            specs = _select_specs(v, drift_cells_by_v[v], avoid_cells, n_drift=args.val_drift_seeds,
                                  n_avoid=args.val_avoid_seeds, namespace="final_validate")
            rows = _eval_cells(clients, model, v, specs, label=f"VALIDATE[{v}]")
            drift_rows = sorted([r for r in rows if r["regime"] == "drift"], key=lambda r: (r["mu"], r["beta"]))
            avoid_rows = sorted([r for r in rows if r["regime"] == "avoidance"],
                                key=lambda r: (r["reveal"], r["mu"], r["geometry"]))
            d_cleared = sum(1 for r in drift_rows if r["success"] >= 0.5)
            a_cleared = sum(1 for r in avoid_rows if r["success"] >= 0.5)
            d_mean = float(np.mean([r["success"] for r in drift_rows])) if drift_rows else 0.0
            a_mean = float(np.mean([r["success"] for r in avoid_rows])) if avoid_rows else 0.0
            val[v] = {"variant": verify.get("drift_backend_variant"), "mass": verify.get("drift_backend_total_mass"),
                      "drift_rows": drift_rows, "avoid_rows": avoid_rows,
                      "drift_cells": len(drift_rows), "drift_cleared": d_cleared, "drift_mean": d_mean,
                      "avoid_cells": len(avoid_rows), "avoid_cleared": a_cleared, "avoid_mean": a_mean}
            print(f"  [{v}] DRIFT {d_cleared}/{len(drift_rows)} cells cleared (mean {d_mean:.3f}) | "
                  f"AVOID {a_cleared}/{len(avoid_rows)} cells cleared (mean {a_mean:.3f})", flush=True)
        report["validation_per_vehicle"] = val
    finally:
        for c in clients:
            c.close()

    report["elapsed_s"] = round(time.time() - t0, 1)

    # ---- headline + verdict ----
    total_cells = sum(val[v]["drift_cells"] + val[v]["avoid_cells"] for v in VEHICLES)
    total_cleared = sum(val[v]["drift_cleared"] + val[v]["avoid_cleared"] for v in VEHICLES)
    drift_total = sum(val[v]["drift_cells"] for v in VEHICLES)
    drift_cleared = sum(val[v]["drift_cleared"] for v in VEHICLES)
    avoid_total = sum(val[v]["avoid_cells"] for v in VEHICLES)
    avoid_cleared = sum(val[v]["avoid_cleared"] for v in VEHICLES)
    report["headline"] = {"total_cells": total_cells, "total_cleared": total_cleared,
                          "drift_total": drift_total, "drift_cleared": drift_cleared,
                          "avoid_total": avoid_total, "avoid_cleared": avoid_cleared}

    report_path = RUN_DIR / "distill_final_integrated_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nsaved report -> {report_path}", flush=True)

    # ---- consolidated, re-verifiable per-(vehicle, cell-group) table ----
    consolidated = {
        "experiment": "FINAL integrated FiLM driver: ONE network over full drift+avoid spectrum x 3 vehicles",
        "policy": str(args.out), "policy_label": "distill_both_final_integrated",
        "architecture": report["architecture"], "obs_dim": COND_OBS_DIM, "onehot_order": list(VEHICLES),
        "selected_seed": int(best[3]), "selected_dagger_round": str(report["distill_selected"]["dagger_round"]),
        "selection_objective": "max WORST-vehicle avoid (min over 3 vehicles), then worst drift",
        "dagger_rounds": int(args.dagger_rounds),
        "validation_seeds_per_cell": {"drift": int(args.val_drift_seeds), "avoid": int(args.val_avoid_seeds)},
        "per_vehicle_cellgroup_chrono": {
            v: {"variant": val[v]["variant"], "mass": val[v]["mass"], "onehot_fed": list(_vehicle_onehot(v)),
                "drift": {"cells_cleared": val[v]["drift_cleared"], "cells_total": val[v]["drift_cells"],
                          "mean_success": round(val[v]["drift_mean"], 4)},
                "avoid": {"cells_cleared": val[v]["avoid_cleared"], "cells_total": val[v]["avoid_cells"],
                          "mean_success": round(val[v]["avoid_mean"], 4)}}
            for v in VEHICLES},
        "headline": report["headline"]}
    cons_path = RUN_DIR / "a5_final_integrated_consolidated.json"
    cons_path.write_text(json.dumps(consolidated, indent=2, default=str), encoding="utf-8")
    print(f"saved consolidated table -> {cons_path}", flush=True)

    # ---- human-readable table ----
    print("\n" + "=" * 110, flush=True)
    print("=== FINAL INTEGRATED FiLM DRIVER: per-(vehicle, cell-group) Chrono (cells cleared / total) ===", flush=True)
    print(f"{'vehicle':8s} | {'DRIFT cleared/total':>20s} (mean) | {'AVOID cleared/total':>20s} (mean)", flush=True)
    for v in VEHICLES:
        d = val[v]
        print(f"{v:8s} | {d['drift_cleared']:9d}/{d['drift_cells']:<10d} ({d['drift_mean']:.3f}) | "
              f"{d['avoid_cleared']:9d}/{d['avoid_cells']:<10d} ({d['avoid_mean']:.3f})", flush=True)
    print("-" * 110, flush=True)
    print(f"HEADLINE: {total_cleared}/{total_cells} cells cleared across 3 vehicles "
          f"(drift {drift_cleared}/{drift_total}, avoid {avoid_cleared}/{avoid_total})", flush=True)
    print("=" * 110, flush=True)


if __name__ == "__main__":
    main()
