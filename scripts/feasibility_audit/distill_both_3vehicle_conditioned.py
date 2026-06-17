"""VEHICLE-CONDITIONED variant of distill_both_3vehicle: does a 3-way vehicle ONE-HOT
recover AVOID generality across the 3 contrasting vehicles?

The S2 vehicle-AGNOSTIC obs72 driver (distill_both_3vehicle) generalizes DRIFT across the
3 vehicles (Sedan/UAZBUS/BMW = 1.00/1.00/0.85, at the per-vehicle baseline) but COLLAPSES
AVOID on every vehicle (a5-validated 0.10/0.25/0.05 vs 1.00/1.00/1.00 baselines), because the
3 vehicles' safe-entry-speed budgets conflict and obs72 carries NO vehicle id, so one shared
avoid head cannot serve all 3 budgets at once.

THE FIX UNDER TEST: append a 3-way vehicle ONE-HOT to the policy input (obs72 -> obs75) for
BOTH the trunk/actor AND the demo collection (each demo frame tagged with its vehicle's
one-hot). Re-collect the 3 vehicles' demos WITH the one-hot, pool, and BC-distill ONE gated
student that now SEES which vehicle it is. Then validate per-(vehicle,regime) on Chrono with
the CORRECT one-hot per vehicle.

KEY VERDICT: does the vehicle one-hot RECOVER avoid (each vehicle back toward its 1.0
baseline)? If YES -> the practical cross-vehicle-general driver is delivered (drift
shared-general + avoid vehicle-conditioned) AND it confirms 'knowing the vehicle' is the
missing signal (RMA can then infer the id from obs72 history = the self-ID extension). If NO
(avoid still collapses even WITH the id) -> a deeper finding (the conflict is not just the id).

WHAT THIS CHANGES vs distill_both_3vehicle (NEW FILE ONLY; imports the recipe machinery and
the per-vehicle patch modules VERBATIM; no protected module is modified):
  1. Demo collection is identical (teacher acts on obs72, BC frames are obs72), BUT after
     pooling we APPEND the per-vehicle 3-way one-hot to every frame: obs72 -> obs75. The
     teacher action targets are UNCHANGED.
  2. The student is an AsymmetricActorCritic with obs_dim=75 (the constructor adjusts the
     actor's first Linear 72->75 and the critic's first Linear automatically; the gated
     dual-head architecture + the learned gate are kept verbatim).
  3. BC-distill ONE gated obs75 student on the pooled (obs75 -> teacher_action) demos.
  4. 3-seed sweep + Chrono-task-score selection, where the select eval FEEDS THE CORRECT
     one-hot per vehicle (obs72 from the backend -> obs75 with that vehicle's one-hot ->
     model.act). Save distill_3vehicle_conditioned_policy.pt.
  5. Per-(vehicle,regime) A5 validation on Chrono is done IN THIS SCRIPT (mirroring the
     per-vehicle a5 validators' frozen grids EXACTLY), feeding the correct one-hot per
     vehicle. No protected validator / _student_task_eval is modified.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_3vehicle_conditioned.py \
        --workers 16 --drift-seeds 8 --avoid-seeds-per-cell 2 --epochs 4000 \
        --seed-sweep 3 \
        --out runs/feasibility_audit/phase4_f2/distill_3vehicle_conditioned_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam

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
import distill_both_3vehicle as d3v  # noqa: E402  (the unconditioned collection machinery, VERBATIM)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_3vehicle_conditioned_policy.pt"

ResilientChronoClient = uaz.ResilientChronoClient

# 3-way vehicle one-hot order (FROZEN: this is the policy-input contract; eval must match).
VEHICLES = ("sedan", "uazbus", "bmw")
ONEHOT_DIM = len(VEHICLES)
COND_OBS_DIM = f2.HUMAN_VIEW_OBS_DIM + ONEHOT_DIM  # 72 + 3 = 75


def _vehicle_onehot(name: str) -> np.ndarray:
    """The FROZEN 3-way one-hot for a vehicle (sedan=[1,0,0], uazbus=[0,1,0], bmw=[0,0,1])."""
    oh = np.zeros((ONEHOT_DIM,), dtype=np.float32)
    oh[VEHICLES.index(name)] = 1.0
    return oh


def _append_onehot(obs72: np.ndarray, name: str) -> np.ndarray:
    """obs72 (N,72) -> obs75 (N,75) by appending vehicle ``name``'s one-hot to every row."""
    obs72 = np.asarray(obs72, dtype=np.float32)
    if obs72.ndim == 1:
        return np.concatenate([obs72, _vehicle_onehot(name)], 0).astype(np.float32)
    oh = np.tile(_vehicle_onehot(name), (obs72.shape[0], 1))
    return np.concatenate([obs72, oh], 1).astype(np.float32)


# =====================================================================================
# Conditioned distillation: a VERBATIM copy of db.distill, but the student model is built
# with obs_dim=COND_OBS_DIM (75). Every other line -- the pooled loss, the per-regime
# sample weighting, the holdout split, the gate-routing diagnostic, the best-on-both-
# holdouts checkpointing -- is identical to db.distill. (We cannot call db.distill because
# it hard-codes f2.AsymmetricActorCritic(gated=True) at obs72.)
# =====================================================================================


def _distill_conditioned(drift_demo: dict, avoid_demo: dict, *, epochs: int, lr: float, batch: int,
                         holdout_frac: float, seed: int) -> tuple[f2.AsymmetricActorCritic, dict]:
    """BC-distill a FRESH gated obs75 AsymmetricActorCritic on the pooled CONDITIONED demos.

    drift_demo / avoid_demo carry obs75 frames (obs72 + per-vehicle one-hot) -> teacher_action.
    Mirrors distill_both.distill exactly except the model is obs_dim=75 (so the actor's first
    Linear is 75->hidden and the gate/dual-head route from the conditioned trunk)."""
    torch.manual_seed(f2._seed_for("distill_init", seed))
    np.random.seed(f2._seed_for("distill_np", seed) % (2**32))

    (dtr_o, dtr_a), (dho_o, dho_a) = db._holdout_split(drift_demo["obs"], drift_demo["act"], frac=holdout_frac, seed=seed + 1)
    (atr_o, atr_a), (aho_o, aho_a) = db._holdout_split(avoid_demo["obs"], avoid_demo["act"], frac=holdout_frac, seed=seed + 2)

    train_o = np.concatenate([dtr_o, atr_o], 0).astype(np.float32)
    train_a = np.concatenate([dtr_a, atr_a], 0).astype(np.float32)
    train_reg = np.concatenate([np.ones(len(dtr_o), np.int64), np.zeros(len(atr_o), np.int64)], 0)  # 1=drift 0=avoid

    print(f"  distill train: {len(dtr_o)} drift + {len(atr_o)} avoid frames (obs{train_o.shape[1]}); "
          f"holdout: {len(dho_o)} drift + {len(aho_o)} avoid", flush=True)

    model = f2.AsymmetricActorCritic(obs_dim=COND_OBS_DIM, gated=True)  # FRESH gated obs75 student
    opt = Adam(model.actor_parameters(), lr=lr)

    obs_t = torch.as_tensor(train_o, dtype=torch.float32)
    act_t = torch.clamp(torch.as_tensor(train_a, dtype=torch.float32), -1.0, 1.0)
    reg_t = torch.as_tensor(train_reg, dtype=torch.long)
    n_d = max(1, int((reg_t == 1).sum())); n_a = max(1, int((reg_t == 0).sum()))
    w = torch.where(reg_t == 1, 0.5 / n_d, 0.5 / n_a).float()
    w = w / w.sum() * len(w)

    dho_o_t = torch.as_tensor(dho_o, dtype=torch.float32)
    dho_a_t = torch.clamp(torch.as_tensor(dho_a, dtype=torch.float32), -1.0, 1.0)
    aho_o_t = torch.as_tensor(aho_o, dtype=torch.float32)
    aho_a_t = torch.clamp(torch.as_tensor(aho_a, dtype=torch.float32), -1.0, 1.0)

    n = obs_t.shape[0]
    rng = np.random.default_rng(f2._seed_for("distill_mb", seed))
    t0 = time.time()
    best_combined = float("inf")
    best_state = None
    for ep in range(int(epochs)):
        order = rng.permutation(n)
        if batch <= 0 or batch >= n:
            mbs = [order]
        else:
            mbs = [order[s:s + batch] for s in range(0, n, batch)]
        for mb in mbs:
            idx = torch.as_tensor(mb, dtype=torch.long)
            mean = model.actor_forward(obs_t[idx])
            err = (mean - act_t[idx]).pow(2).mean(dim=-1)
            loss = (w[idx] * err).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.actor_parameters(), 1.0)
            opt.step()
        if ep % max(1, epochs // 20) == 0 or ep == epochs - 1:
            with torch.no_grad():
                d_mse = float((model.actor_forward(dho_o_t) - dho_a_t).pow(2).mean())
                a_mse = float((model.actor_forward(aho_o_t) - aho_a_t).pow(2).mean())
            combined = d_mse + a_mse
            if combined < best_combined:
                best_combined = combined
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            if ep % max(1, epochs // 10) == 0 or ep == epochs - 1:
                print(f"    ep {ep:5d}  drift_holdout_MSE={d_mse:.2e}  avoid_holdout_MSE={a_mse:.2e}", flush=True)
    if best_state is not None:
        model.load_state_dict(best_state)

    with torch.no_grad():
        d_mse = float((model.actor_forward(dho_o_t) - dho_a_t).pow(2).mean())
        a_mse = float((model.actor_forward(aho_o_t) - aho_a_t).pow(2).mean())

        def _gate(obs):
            h = model.actor(obs)
            return torch.sigmoid(model.actor_gate(h)).squeeze(-1)
        g_drift = float(_gate(dho_o_t).mean())
        g_avoid = float(_gate(aho_o_t).mean())
    print(f"  distillation done in {time.time()-t0:.1f}s  "
          f"drift_holdout_MSE={d_mse:.3e}  avoid_holdout_MSE={a_mse:.3e}", flush=True)
    print(f"  gate routing (mean sigmoid; 1=>headA, 0=>headB): drift={g_drift:.3f}  avoid={g_avoid:.3f}  "
          f"|separation|={abs(g_drift-g_avoid):.3f}", flush=True)
    return model, {
        "drift_holdout_mse": d_mse, "avoid_holdout_mse": a_mse,
        "gate_mean_drift": g_drift, "gate_mean_avoid": g_avoid,
        "n_train_drift": int(len(dtr_o)), "n_train_avoid": int(len(atr_o)),
        "n_holdout_drift": int(len(dho_o)), "n_holdout_avoid": int(len(aho_o)),
    }


# =====================================================================================
# Conditioned Chrono eval. The backend returns obs72; we APPEND the item's vehicle one-hot
# (obs72 -> obs75) before model.act. Mirrors f2._eval_success_parallel / _student_task_eval
# (the protected selection/early-stop metric) but with the per-item one-hot. Every item must
# carry a "vehicle" key so the correct one-hot is fed.
# =====================================================================================


def _conditioned_task_eval(clients, items: list[dict], model: f2.AsymmetricActorCritic) -> dict[str, float]:
    """Run each item's episode W-way parallel; the student sees obs75 (obs72 + item's one-hot).

    The teacher is NOT driven here -- we eval model.act only, so no oracle/mu-registry coupling
    matters (the avoidance success is read from the backend collision/clearance, not the oracle).
    """
    if isinstance(clients, ChronoWorkerClient):
        clients = [clients]
    results: list[float | None] = [None] * len(items)
    n_workers = min(len(clients), len(items)) if items else 0
    next_i = 0
    lock = threading.Lock()

    def _cond_policy(name: str):
        oh = _vehicle_onehot(name)

        def _p(step: int, obs: np.ndarray) -> np.ndarray:
            obs75 = np.concatenate([np.asarray(obs, dtype=np.float32), oh], 0)
            return model.act(obs75)
        return _p

    def _worker(wi: int) -> None:
        nonlocal next_i
        client = clients[wi]
        while True:
            with lock:
                if next_i >= len(items):
                    return
                i = next_i
                next_i += 1
            it = items[i]
            policy = _cond_policy(it["vehicle"])
            res = f2.run_episode(client, it["scenario"], it["regime"], policy,
                                 seed=int(it["seed"]), mu=float(it["mu"]), reveal=float(it["reveal"]))
            results[i] = 1.0 if res["success"] else 0.0

    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    by: dict[str, list[float]] = {}
    for it, s in zip(items, results):
        if s is None:
            continue
        by.setdefault(it["regime"], []).append(float(s))
    return {r: float(np.mean(v)) for r, v in by.items()}


# --------- pooled select set (per-vehicle, each item tagged with its vehicle) -----------


def _pooled_select_items(n_avoid_per_vehicle: int, n_drift_per_vehicle: int) -> dict[str, list[dict]]:
    """Same construction as distill_both_3vehicle._pooled_select_items, but each item carries a
    'vehicle' key (the one-hot to feed). Scenario builders are vehicle-patched globals, so we
    install each vehicle's patches in turn to build its (vehicle-specific) scenario dicts."""
    out: dict[str, list[dict]] = {}
    for name in VEHICLES:
        d3v._install_vehicle(name)
        grid = f2._avoidance_grid(quick=False)
        drift_mu = float(d3v._vehicle_drift_cell(name)["mu"])
        items: list[dict] = []
        for u in range(n_avoid_per_vehicle):
            reveal, mu = grid[u % len(grid)]
            seed = int(f2._seed_for("distill_select", name, "avoidance", u, round(reveal, 4), round(mu, 4)))
            items.append({"vehicle": name, "regime": "avoidance", "reveal": float(reveal), "mu": float(mu),
                          "seed": seed,
                          "scenario": f2._avoidance_scenario(seed, max_steps=db.AVOID_MAX_STEPS,
                                                             reveal=float(reveal), mu=float(mu))})
        for u in range(n_drift_per_vehicle):
            seed = int(f2._seed_for("distill_select", name, "drift", u, d3v._vehicle_drift_cell(name)["cell_id"]))
            items.append({"vehicle": name, "regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                          "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS,
                                                         difficulty="hard")})
        out[name] = items
    return out


def _pooled_conditioned_select(clients, model, select_items: dict[str, list[dict]]) -> dict[str, Any]:
    """Run the pooled select set per-vehicle on Chrono, feeding each vehicle's one-hot."""
    per_vehicle: dict[str, dict[str, float]] = {}
    all_avoid: list[float] = []
    all_drift: list[float] = []
    for name in VEHICLES:
        d3v._install_vehicle(name)
        items = select_items[name]
        rates = _conditioned_task_eval(clients, items, model)
        av = float(rates.get("avoidance", 0.0)); dr = float(rates.get("drift", 0.0))
        per_vehicle[name] = {"avoid": av, "drift": dr}
        all_avoid.append(av); all_drift.append(dr)
        print(f"    [{name}] select avoid={av:.3f} drift={dr:.3f}", flush=True)
    agg = {"avoidance": float(np.mean(all_avoid)) if all_avoid else 0.0,
           "drift": float(np.mean(all_drift)) if all_drift else 0.0}
    worst = {"avoidance": float(np.min(all_avoid)) if all_avoid else 0.0,
             "drift": float(np.min(all_drift)) if all_drift else 0.0}
    return {"per_vehicle": per_vehicle, "aggregate": agg, "worst": worst}


# --------- per-(vehicle, regime) A5 validation (FROZEN grids, mirrors the a5 validators) -----


def _a5_items_for_vehicle(name: str, avoid_units: int, drift_units: int) -> list[dict]:
    """Build THIS vehicle's frozen A5 validation items, EXACTLY as the per-vehicle a5 validators do.

    The vehicle's patches must already be installed (so f2._avoidance_scenario / _drift_scenario
    build the right variant + mass + drift cell). Avoid grid + 'validation' seed namespace is
    shared across vehicles (only the variant differs); drift seeds use the per-vehicle namespace
    the a5 validators use: Sedan -> E4 frozen low_mu validation seeds; UAZBUS -> 'uaz_validation';
    BMW -> 'bmw_validation'. Each item is tagged with its vehicle (the one-hot to feed)."""
    grid = f2._avoidance_grid(quick=False)
    items: list[dict] = []
    for unit in range(avoid_units):
        reveal, mu = grid[unit % len(grid)]
        seed = int(f2._seed_for("validation", "avoidance", unit, round(reveal, 4), round(mu, 4)))
        items.append({"vehicle": name, "regime": "avoidance", "reveal": float(reveal), "mu": float(mu),
                      "seed": seed,
                      "scenario": f2._avoidance_scenario(seed, max_steps=285, reveal=float(reveal), mu=float(mu))})
    if name == "sedan":
        drift_seeds = list(f2._e4_drift_validation_seeds(f2.DRIFT_CELL_ID))
        drift_mu = float(f2._drift_cell()["mu"])
        for unit in range(min(drift_units, len(drift_seeds))):
            seed = int(drift_seeds[unit])
            items.append({"vehicle": name, "regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                          "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    elif name == "uazbus":
        drift_mu = float(uaz.UAZBUS_DRIFT_CELL["mu"])
        for unit in range(drift_units):
            seed = int(f2._seed_for("uaz_validation", "drift", unit, uaz.UAZBUS_DRIFT_CELL["cell_id"]))
            items.append({"vehicle": name, "regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                          "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    elif name == "bmw":
        drift_mu = float(bmw.BMW_DRIFT_CELL["mu"])
        for unit in range(drift_units):
            seed = int(f2._seed_for("bmw_validation", "drift", unit, bmw.BMW_DRIFT_CELL["cell_id"]))
            items.append({"vehicle": name, "regime": "drift", "reveal": 0.0, "mu": drift_mu, "seed": seed,
                          "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    else:
        raise ValueError(name)
    return items


def _validate_per_vehicle(clients, model, avoid_units: int, drift_units: int) -> dict[str, dict[str, Any]]:
    """Run the frozen per-(vehicle, regime) A5 validation on Chrono with the correct one-hot per
    vehicle. Installs each vehicle's patches (so scenarios reset on the right backend variant) and
    verifies the variant before validating (the same secondary-risk guard the collection uses)."""
    out: dict[str, dict[str, Any]] = {}
    for name in VEHICLES:
        print(f"\n################### A5 VALIDATE {name.upper()} (conditioned, one-hot fed) ###################", flush=True)
        d3v._install_vehicle(name)
        verify = d3v._verify_vehicle_scenarios(name, clients)
        if not verify["variant_ok"]:
            raise SystemExit(f"FATAL [{name}]: A5 scenarios are NOT carrying the {name} variant; aborting.")
        items = _a5_items_for_vehicle(name, avoid_units, drift_units)
        n_av = sum(1 for it in items if it["regime"] == "avoidance")
        n_dr = sum(1 for it in items if it["regime"] == "drift")
        rates = _conditioned_task_eval(clients, items, model)
        av = float(rates.get("avoidance", float("nan"))); dr = float(rates.get("drift", float("nan")))
        out[name] = {"avoid": av, "drift": dr, "n_avoid": n_av, "n_drift": n_dr,
                     "variant": verify.get("drift_backend_variant"),
                     "mass": verify.get("drift_backend_total_mass"), "verify": verify}
        print(f"  [{name}] A5 CHRONO (one-hot {list(_vehicle_onehot(name))}): "
              f"avoid={av:.3f} ({n_av} eps) drift={dr:.3f} ({n_dr} eps)", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="VEHICLE-CONDITIONED 3-vehicle do-both driver (obs75; one-hot).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=8, help="drift demo seeds PER difficulty PER vehicle")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal x mu cell PER vehicle")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--select-avoid-units", type=int, default=8, help="select avoid episodes PER vehicle")
    ap.add_argument("--select-drift-units", type=int, default=5, help="select drift episodes PER vehicle")
    ap.add_argument("--a5-avoid-units", type=int, default=40, help="A5 avoid validation episodes PER vehicle")
    ap.add_argument("--a5-drift-units", type=int, default=20, help="A5 drift validation episodes PER vehicle")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    print(f"[3vehicle-conditioned] pooling demos from {VEHICLES} into ONE gated obs{COND_OBS_DIM} student. "
          f"Each frame carries its vehicle's 3-way one-hot -- the driver KNOWS which vehicle it is.", flush=True)
    print(f"  one-hot order (FROZEN): {[(v, list(_vehicle_onehot(v))) for v in VEHICLES]}", flush=True)

    clients = [ResilientChronoClient(stderr_log=RUN_DIR / f"distill3vc_w{w}_stderr.log")
               for w in range(args.workers)]
    report: dict[str, Any] = {
        "vehicles": list(VEHICLES), "onehot_dim": ONEHOT_DIM, "cond_obs_dim": COND_OBS_DIM,
        "baselines": {"sedan": {"drift": 1.0, "avoid": 1.0}, "uazbus": {"drift": 1.0, "avoid": 1.0},
                      "bmw": {"drift": 0.85, "avoid": 1.0}},
        "s2_unconditioned_a5": {"sedan": {"drift": 1.0, "avoid": 0.10}, "uazbus": {"drift": 1.0, "avoid": 0.25},
                                "bmw": {"drift": 0.85, "avoid": 0.05}}}
    t0 = time.time()
    pooled = None
    best = None  # (score, state_dict, stats, seed, sel)
    try:
        # ---- 1. collect demos PER vehicle (VERBATIM from distill_both_3vehicle) ----
        per_vehicle_demos: dict[str, Any] = {}
        for name in VEHICLES:
            print(f"\n################### COLLECTING {name.upper()} DEMOS ###################", flush=True)
            per_vehicle_demos[name] = d3v._collect_vehicle_demos(
                name, clients, drift_seeds=args.drift_seeds, avoid_seeds_per_cell=args.avoid_seeds_per_cell)

        # ---- 2. APPEND per-vehicle one-hot (obs72 -> obs75), then POOL ----
        drift_obs = np.concatenate([_append_onehot(per_vehicle_demos[v]["drift"]["obs"], v) for v in VEHICLES], 0)
        drift_act = np.concatenate([per_vehicle_demos[v]["drift"]["act"] for v in VEHICLES], 0)
        avoid_obs = np.concatenate([_append_onehot(per_vehicle_demos[v]["avoid"]["obs"], v) for v in VEHICLES], 0)
        avoid_act = np.concatenate([per_vehicle_demos[v]["avoid"]["act"] for v in VEHICLES], 0)
        assert drift_obs.shape[1] == COND_OBS_DIM and avoid_obs.shape[1] == COND_OBS_DIM, \
            f"conditioned obs dim mismatch: {drift_obs.shape[1]}/{avoid_obs.shape[1]} != {COND_OBS_DIM}"
        drift_demo = {"obs": drift_obs, "act": drift_act,
                      "n_episodes": sum(per_vehicle_demos[v]["drift"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["drift"]["n_success"] for v in VEHICLES)}
        avoid_demo = {"obs": avoid_obs, "act": avoid_act,
                      "n_episodes": sum(per_vehicle_demos[v]["avoid"]["n_episodes"] for v in VEHICLES),
                      "n_success": sum(per_vehicle_demos[v]["avoid"]["n_success"] for v in VEHICLES)}
        pooled = {"drift": drift_demo, "avoid": avoid_demo}
        report["pooled_demo"] = {
            "drift_frames": int(drift_obs.shape[0]), "avoid_frames": int(avoid_obs.shape[0]),
            "cond_obs_dim": int(drift_obs.shape[1]),
            "per_vehicle": {v: {
                "drift_frames": int(per_vehicle_demos[v]["drift"]["obs"].shape[0]),
                "drift_teacher_success": int(per_vehicle_demos[v]["drift"]["n_success"]),
                "drift_episodes": int(per_vehicle_demos[v]["drift"]["n_episodes"]),
                "avoid_frames": int(per_vehicle_demos[v]["avoid"]["obs"].shape[0]),
                "avoid_teacher_success": int(per_vehicle_demos[v]["avoid"]["n_success"]),
                "avoid_episodes": int(per_vehicle_demos[v]["avoid"]["n_episodes"]),
                "onehot": list(_vehicle_onehot(v)),
            } for v in VEHICLES}}
        report["scenario_verification"] = {v: per_vehicle_demos[v]["verify"] for v in VEHICLES}
        print(f"\nPOOLED conditioned demos: {drift_obs.shape[0]} drift + {avoid_obs.shape[0]} avoid frames "
              f"(obs{drift_obs.shape[1]}, from 3 vehicles WITH one-hot)", flush=True)
        for v in VEHICLES:
            print(f"   {v:7s} oh={list(_vehicle_onehot(v))}: "
                  f"drift {per_vehicle_demos[v]['drift']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['drift']['n_success']}/{per_vehicle_demos[v]['drift']['n_episodes']} succ) | "
                  f"avoid {per_vehicle_demos[v]['avoid']['obs'].shape[0]:6d} frames "
                  f"({per_vehicle_demos[v]['avoid']['n_success']}/{per_vehicle_demos[v]['avoid']['n_episodes']} succ)",
                  flush=True)

        # ---- 3. build the pooled (per-vehicle-tagged) Chrono select set ----
        select_items = _pooled_select_items(int(args.select_avoid_units), int(args.select_drift_units))

        # ---- 4. distill N seeds on the POOLED conditioned demos; select by conditioned Chrono task score ----
        per_seed = []
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- 3vehicle CONDITIONED distill seed {s} ---", flush=True)
            m, st = _distill_conditioned(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                                         holdout_frac=args.holdout_frac, seed=s)
            sel = _pooled_conditioned_select(clients, m, select_items)
            agg_av = sel["aggregate"]["avoidance"]; agg_dr = sel["aggregate"]["drift"]
            worst_av = sel["worst"]["avoidance"]; worst_dr = sel["worst"]["drift"]
            print(f"  seed {s} POOLED COND SELECT: avoid agg={agg_av:.3f} (worst {worst_av:.3f}) "
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

        model = f2.AsymmetricActorCritic(obs_dim=COND_OBS_DIM, gated=True)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED conditioned seed {best[3]} "
              f"(pooled select avoid={stats['select_avoid']:.3f} drift={stats['select_drift']:.3f} | "
              f"worst avoid={stats['select_worst_avoid']:.3f} drift={stats['select_worst_drift']:.3f})", flush=True)
        report["distill_selected"] = {
            "seed": int(best[3]), "select_avoid": float(stats["select_avoid"]),
            "select_drift": float(stats["select_drift"]),
            "select_worst_avoid": float(stats["select_worst_avoid"]),
            "select_worst_drift": float(stats["select_worst_drift"]),
            "per_vehicle": stats["select_per_vehicle"]}

        # ---- 5. save the policy BEFORE the (longer) A5 validation, so a crash can't lose it ----
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_stats = {k: v for k, v in stats.items() if k != "select_per_vehicle"}
        torch.save({
            "state_dict": model.state_dict(), "gated": True,
            "obs_dim": COND_OBS_DIM, "onehot_dim": ONEHOT_DIM, "vehicle_order": list(VEHICLES),
            "label": "distill_both_3vehicle_conditioned", "vehicles": list(VEHICLES),
            "conditioning": "3way_vehicle_onehot_appended_obs72_to_obs75",
            "drift_teacher": "pooled_{sedan_gpu_expert, uazbus_feedback, bmw_feedback}",
            "avoid_teacher": "pooled_{sedan_oracle, uazbus_oracle, bmw_rephys_oracle}",
            "drift_demo_frames": int(pooled["drift"]["obs"].shape[0]),
            "avoid_demo_frames": int(pooled["avoid"]["obs"].shape[0]),
            "select_per_vehicle": stats["select_per_vehicle"],
            **save_stats,
        }, out)
        print(f"\nsaved CONDITIONED 3-vehicle distilled student -> {out}", flush=True)

        # ---- 6. per-(vehicle, regime) A5 validation on Chrono (correct one-hot per vehicle) ----
        a5 = _validate_per_vehicle(clients, model, int(args.a5_avoid_units), int(args.a5_drift_units))
        report["a5_per_vehicle"] = {v: {k: a5[v][k] for k in ("avoid", "drift", "n_avoid", "n_drift", "variant", "mass")}
                                    for v in VEHICLES}
    finally:
        for c in clients:
            c.close()

    report["elapsed_s"] = round(time.time() - t0, 1)

    # ---- verdict: did the one-hot recover avoid? ----
    base = report["baselines"]; s2 = report["s2_unconditioned_a5"]; a5p = report["a5_per_vehicle"]
    recovered = {v: bool(a5p[v]["avoid"] >= 0.80) for v in VEHICLES}
    improved = {v: bool(a5p[v]["avoid"] > s2[v]["avoid"] + 1e-9) for v in VEHICLES}
    drift_held = {v: bool(a5p[v]["drift"] >= base[v]["drift"] - 1e-9) for v in VEHICLES}
    all_recovered = all(recovered.values())
    any_improved = any(improved.values())
    report["verdict"] = {
        "avoid_recovered_per_vehicle": recovered,
        "avoid_improved_vs_s2_per_vehicle": improved,
        "drift_held_at_baseline_per_vehicle": drift_held,
        "ALL_avoid_recovered": all_recovered,
        "ANY_avoid_improved": any_improved,
        "key": ("YES -- vehicle one-hot RECOVERS avoid on all 3 vehicles (each >= 0.80): the "
                "practical cross-vehicle-general driver is delivered (drift shared-general + avoid "
                "vehicle-conditioned), and 'knowing the vehicle' is CONFIRMED as the missing signal "
                "-> RMA can infer the id from obs72 history = the self-ID extension."
                if all_recovered else
                ("PARTIAL -- the one-hot IMPROVES avoid on at least one vehicle but does NOT recover "
                 "all 3 to >= 0.80: the id helps but is not sufficient; the conflict is not purely the id."
                 if any_improved else
                 "NO -- avoid still collapses even WITH the vehicle id: a deeper finding (the "
                 "cross-vehicle avoid conflict is NOT just the missing vehicle id).")),
    }

    report_path = RUN_DIR / "distill_3vehicle_conditioned_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"saved report -> {report_path}", flush=True)

    # ---- consolidated, re-verifiable per-(vehicle, regime) table ----
    consolidated = {
        "experiment": "VEHICLE-CONDITIONED 3-vehicle do-both driver (obs75; 3-way vehicle one-hot)",
        "question": "Does a vehicle ONE-HOT (obs72 -> obs75) RECOVER avoid generality across the 3 vehicles?",
        "policy": str(args.out), "policy_label": "distill_both_3vehicle_conditioned",
        "obs_dim": COND_OBS_DIM, "onehot_order": list(VEHICLES),
        "selected_seed": int(best[3]),
        "pooled_demo_frames": {"drift": int(pooled["drift"]["obs"].shape[0]), "avoid": int(pooled["avoid"]["obs"].shape[0])},
        "distill_holdout_mse": {"drift": float(stats["drift_holdout_mse"]), "avoid": float(stats["avoid_holdout_mse"])},
        "a5_validation_units_per_vehicle": {"avoid": int(args.a5_avoid_units), "drift": int(args.a5_drift_units)},
        "per_vehicle_regime_chrono_CONDITIONED": {
            v: {"variant": a5p[v]["variant"], "mass": a5p[v]["mass"],
                "drift": round(float(a5p[v]["drift"]), 4), "avoid": round(float(a5p[v]["avoid"]), 4),
                "onehot_fed": list(_vehicle_onehot(v)),
                "drift_baseline": base[v]["drift"], "avoid_baseline": base[v]["avoid"],
                "s2_unconditioned_avoid": s2[v]["avoid"], "s2_unconditioned_drift": s2[v]["drift"]}
            for v in VEHICLES},
        "verdict": report["verdict"]["key"],
    }
    cons_path = RUN_DIR / "a5_3vehicle_conditioned_consolidated.json"
    cons_path.write_text(json.dumps(consolidated, indent=2, default=str), encoding="utf-8")
    print(f"saved consolidated table -> {cons_path}", flush=True)

    # ---- human-readable verdict ----
    print("\n" + "=" * 90, flush=True)
    print("=== VEHICLE-CONDITIONED 3-VEHICLE DO-BOTH DRIVER: per-(vehicle, regime) Chrono ===", flush=True)
    print(f"{'vehicle':8s} | {'drift':>7s} (base) | {'avoid':>7s} (base) | {'avoid S2-uncond':>16s} | recovered?", flush=True)
    for v in VEHICLES:
        print(f"{v:8s} | {a5p[v]['drift']:7.3f} ({base[v]['drift']:.2f}) | "
              f"{a5p[v]['avoid']:7.3f} ({base[v]['avoid']:.2f}) | {s2[v]['avoid']:16.3f} | "
              f"{'YES' if recovered[v] else ('improved' if improved[v] else 'no')}", flush=True)
    print("-" * 90, flush=True)
    print(f"KEY VERDICT: {report['verdict']['key']}", flush=True)
    print(f"  drift held at baseline (1.0/1.0/0.85): "
          f"{ {v: drift_held[v] for v in VEHICLES} }", flush=True)
    print("=" * 90, flush=True)


if __name__ == "__main__":
    main()
