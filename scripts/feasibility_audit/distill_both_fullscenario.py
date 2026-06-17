"""FULL-SCENARIO gated do-both distillation: generalize the PROVEN single-cell do-both recipe
(distill_both.py) to the frozen S1 48-cell spectrum (12 drift + 36 avoid), producing ONE gated
obs72 driver, then VALIDATE it PER-CELL on Chrono.

This is the direct generalization of scripts/feasibility_audit/distill_both.py:
  * SINGLE drift cell  -> the 12 FEASIBLE drift cells beta*{0.18,0.28,0.36,0.45} x mu{0.35,0.45,0.55}
                          (runs/feasibility_audit/spectrum_s1/feasibility_precheck.json). Each cell's
                          DRIFT TEACHER is the TUNED DriftFeedbackPolicy via the specs_for(beta) laws
                          (spectrum_s1_feasibility_precheck.specs_for): the existing e4 strong-gain
                          DRIFT_FEEDBACK_SPECS for beta<=0.28 plus the strong-gain 0.36/0.45
                          extrapolations (beta_gain 2.0-3.2, NOT the weak reflex gains). The cell's
                          feasible scenario is the precheck scen() builder (mass 1684, the precheck
                          params block, entry speed 12). DR over 12 cells: ONE drift head covers all.
  * BASE reveal x mu grid -> the 36 FEASIBLE avoid cells (base 20 + knife_edge 3 + offset 7 + width 6)
                          from runs/feasibility_audit/spectrum_s1/feasibility_fullscenario.json. Each
                          cell's teacher is make_avoidance_teacher(reveal, mu) (the proven E2' oracle),
                          on the e2_smoke scenario with the cell's geometry applied (_apply_geometry).

We pool ALL demos (12 drift cells + 36 avoid cells), BC a FRESH gated AsymmetricActorCritic (shared
trunk + actor_mean_a/b heads + a learned gate from obs72) -- the SAME architecture/loss as
distill_both.distill. The gate self-routes drift vs avoid from obs72; within drift the one head/policy
covers all 12 cells. NO joint PPO. We seed-sweep + select by a small Chrono task score (disjoint seed
namespace), save to distill_s1_fullscenario_policy.pt, then VALIDATE PER-CELL on Chrono and emit the
per-cell table.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both_fullscenario.py \
        --workers 16 --drift-seeds-per-cell 6 --avoid-seeds-per-cell 5 \
        --epochs 4000 --seed-sweep 3 \
        --val-drift-seeds 8 --val-avoid-seeds 6 \
        --out runs/feasibility_audit/phase4_f2/distill_s1_fullscenario_policy.pt
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
import phase4_e4_drift_regime_pricing as e4  # noqa: E402
import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402
import spectrum_s1_feasibility_precheck as precheck  # noqa: E402
import spectrum_s1_avoid_feasibility as avoid_feas  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_s1_fullscenario_policy.pt"
SPECTRUM_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "spectrum_s1"
PRECHECK_JSON = SPECTRUM_DIR / "feasibility_precheck.json"
FULLSCENARIO_JSON = SPECTRUM_DIR / "feasibility_fullscenario.json"

AVOID_MAX_STEPS = 285  # E2' avoidance episode length (matches feasibility_fullscenario + distill_both)
DRIFT_MAX_STEPS = int(precheck.MAX_STEPS)  # 90 (e4 frozen drift horizon)
VARIANT = precheck.VARIANT  # sedan_tmeasy


# ============================================================ cell catalogs (frozen spectrum)


def _load_drift_cells() -> list[dict]:
    """The 12 FEASIBLE drift cells + the best precheck spec per cell."""
    data = json.loads(PRECHECK_JSON.read_text())
    cells = []
    for c in data["feasible_cells"]:
        mu, beta = float(c["mu"]), float(c["beta"])
        # the spec the precheck verified clears this cell (best sustain), selected from specs_for(beta)
        spec = next(s for s in precheck.specs_for(beta) if s.name == c["spec"])
        cells.append({
            "mu": mu, "beta": beta, "speed": float(c["speed"]), "spec": spec,
            "spec_name": spec.name, "precheck_sustain": int(c["longest"]),
            "cell_id": f"drift-mu{mu:.2f}-b{beta:.2f}",
        })
    return cells


def _load_avoid_cells() -> list[dict]:
    """The 36 FEASIBLE avoid cells (base + knife_edge + offset + width geometry variants)."""
    data = json.loads(FULLSCENARIO_JSON.read_text())
    cells = []
    for c in data["avoid"]["feasible_cells"]:
        cells.append({
            "reveal": float(c["reveal"]), "mu": float(c["mu"]),
            "geometry": str(c["geometry"]),
            "lateral_offset_m": float(c.get("lateral_offset_m") or 0.0),
            "half_width_m": (None if c.get("half_width_m") in (None, "None") else float(c["half_width_m"])),
            "cell_id": f"avoid-r{float(c['reveal']):g}-mu{float(c['mu']):.4f}-{c['geometry']}",
        })
    return cells


# ============================================================ scenario builders


def _drift_scenario(cell: dict, seed: int) -> dict:
    """The precheck's exact feasible drift scenario (precheck.scen builder)."""
    sc = precheck.scen(cell["mu"], cell["speed"], cell["beta"], seed)
    sc["scenario_id"] = f"s1full-{cell['cell_id']}-seed{seed}"
    sc["max_steps"] = DRIFT_MAX_STEPS
    return sc


# avoid scenarios are built with the e2 context (loaded once, used read-only by builder calls)
_E2_CTX = None
_E2_LOCK = threading.Lock()


def _e2_ctx():
    global _E2_CTX
    if _E2_CTX is None:
        with _E2_LOCK:
            if _E2_CTX is None:
                _E2_CTX = f2.f1._e2_context()  # (reg, mod_b, interp)
    return _E2_CTX


def _avoid_scenario(cell: dict, seed: int) -> dict:
    reg, mod_b, interp = _e2_ctx()
    with _E2_LOCK:  # _make_scenario builds an env; serialize to be safe
        sc = e2_smoke._make_scenario(reg, mod_b, interp, reveal=cell["reveal"], mu=cell["mu"],
                                     seed=int(seed), variant=VARIANT)
    sc["max_steps"] = AVOID_MAX_STEPS
    avoid_feas._apply_geometry(sc, lateral_offset_m=cell["lateral_offset_m"],
                               half_width_m=cell["half_width_m"])
    sc["scenario_id"] = f"s1full-{cell['cell_id']}-seed{seed}"
    return sc


# ============================================================ teachers


def _drift_teacher(cell: dict):
    return e4.DriftFeedbackPolicy(cell["spec"], side=cell["beta"])


def _avoid_teacher(cell: dict):
    return f2.make_avoidance_teacher(reveal=cell["reveal"], mu=cell["mu"]).factory()


# ============================================================ demo specs


def _drift_demo_specs(drift_cells: list[dict], seeds_per_cell: int) -> list[dict]:
    specs = []
    for ci, cell in enumerate(drift_cells):
        for i in range(seeds_per_cell):
            seed = int(f2._seed_for("distill_fs", "drift", ci, i, round(cell["mu"], 3), round(cell["beta"], 3)))
            specs.append({"regime": "drift", "cell": cell, "seed": seed,
                          "scenario": _drift_scenario(cell, seed)})
    return specs


def _avoid_demo_specs(avoid_cells: list[dict], seeds_per_cell: int) -> list[dict]:
    specs = []
    for ci, cell in enumerate(avoid_cells):
        for i in range(seeds_per_cell):
            seed = int(f2._seed_for("distill_fs", "avoid", ci, i, round(cell["reveal"], 3),
                                    round(cell["mu"], 4), cell["geometry"]))
            specs.append({"regime": "avoidance", "cell": cell, "seed": seed,
                          "scenario": _avoid_scenario(cell, seed)})
    return specs


# ============================================================ demo collection


def collect_demos(clients: list[ChronoWorkerClient], specs: list[dict], *, label: str) -> dict:
    """Run each spec's teacher episode W-way parallel; pool obs72 -> teacher_action frames."""
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
                                 seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal),
                                 collect="bc")
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
    obs = np.concatenate(frames, 0) if frames else np.zeros((0, f2.HUMAN_VIEW_OBS_DIM), np.float32)
    act = np.concatenate(targets, 0) if targets else np.zeros((0, f2.ACT_DIM), np.float32)
    print(f"  [{label}] {len(specs)} episodes ({n_success[0]} teacher-success), "
          f"{obs.shape[0]} obs72->action frames, {dt:.1f}s", flush=True)
    return {"obs": obs, "act": act, "n_episodes": len(specs), "n_success": n_success[0]}


# ============================================================ BC distillation (same as distill_both)


def _holdout_split(obs: np.ndarray, act: np.ndarray, *, frac: float, seed: int):
    n = obs.shape[0]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    n_hold = max(1, int(round(n * frac)))
    hold, train = perm[:n_hold], perm[n_hold:]
    return (obs[train], act[train]), (obs[hold], act[hold])


def distill(drift_demo: dict, avoid_demo: dict, *, epochs: int, lr: float, batch: int,
            holdout_frac: float, seed: int) -> tuple[f2.AsymmetricActorCritic, dict]:
    """Distill a FRESH gated AsymmetricActorCritic by BC on the pooled demos (NO PPO).

    IDENTICAL machinery to distill_both.distill: MSE(actor_forward(obs72), teacher_action) pooled
    over both regimes, per-regime equalized sample weight, gated student, checkpoint selected by
    combined holdout MSE. The gate self-routes drift vs avoid from obs72.
    """
    torch.manual_seed(f2._seed_for("distill_fs_init", seed))
    np.random.seed(f2._seed_for("distill_fs_np", seed) % (2**32))

    (dtr_o, dtr_a), (dho_o, dho_a) = _holdout_split(drift_demo["obs"], drift_demo["act"], frac=holdout_frac, seed=seed + 1)
    (atr_o, atr_a), (aho_o, aho_a) = _holdout_split(avoid_demo["obs"], avoid_demo["act"], frac=holdout_frac, seed=seed + 2)

    train_o = np.concatenate([dtr_o, atr_o], 0).astype(np.float32)
    train_a = np.concatenate([dtr_a, atr_a], 0).astype(np.float32)
    train_reg = np.concatenate([np.ones(len(dtr_o), np.int64), np.zeros(len(atr_o), np.int64)], 0)  # 1=drift 0=avoid

    print(f"  distill train: {len(dtr_o)} drift + {len(atr_o)} avoid frames; "
          f"holdout: {len(dho_o)} drift + {len(aho_o)} avoid", flush=True)

    model = f2.AsymmetricActorCritic(gated=True)  # FRESH gated student
    opt = Adam(model.actor_parameters(), lr=lr)

    obs_t = torch.as_tensor(train_o, dtype=torch.float32)
    act_t = torch.clamp(torch.as_tensor(train_a, dtype=torch.float32), -1.0, 1.0)
    reg_t = torch.as_tensor(train_reg, dtype=torch.long)
    n_d = max(1, int((reg_t == 1).sum())); n_a = max(1, int((reg_t == 0).sum()))
    w = torch.where(reg_t == 1, 0.5 / n_d, 0.5 / n_a).float()
    w = w / w.sum() * len(w)  # normalise to mean 1

    dho_o_t = torch.as_tensor(dho_o, dtype=torch.float32)
    dho_a_t = torch.clamp(torch.as_tensor(dho_a, dtype=torch.float32), -1.0, 1.0)
    aho_o_t = torch.as_tensor(aho_o, dtype=torch.float32)
    aho_a_t = torch.clamp(torch.as_tensor(aho_a, dtype=torch.float32), -1.0, 1.0)

    n = obs_t.shape[0]
    rng = np.random.default_rng(f2._seed_for("distill_fs_mb", seed))
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


# ============================================================ Chrono validation (per-cell + select)


def _val_specs(drift_cells: list[dict], avoid_cells: list[dict], *, n_drift: int, n_avoid: int,
               namespace: str) -> list[dict]:
    """Per-cell validation specs over a DISJOINT seed namespace (no select-on-test)."""
    specs = []
    for ci, cell in enumerate(drift_cells):
        for i in range(n_drift):
            seed = int(f2._seed_for(namespace, "drift", ci, i, round(cell["mu"], 3), round(cell["beta"], 3)))
            specs.append({"regime": "drift", "cell": cell, "seed": seed,
                          "scenario": _drift_scenario(cell, seed)})
    for ci, cell in enumerate(avoid_cells):
        for i in range(n_avoid):
            seed = int(f2._seed_for(namespace, "avoid", ci, i, round(cell["reveal"], 3),
                                    round(cell["mu"], 4), cell["geometry"]))
            specs.append({"regime": "avoidance", "cell": cell, "seed": seed,
                          "scenario": _avoid_scenario(cell, seed)})
    return specs


def validate_per_cell(clients: list[ChronoWorkerClient], model: f2.AsymmetricActorCritic,
                      specs: list[dict], *, label: str) -> list[dict]:
    """Run the student per-cell on Chrono; collect per-(cell,seed) success."""
    results: list[dict | None] = [None] * len(specs)
    n_workers = min(len(clients), len(specs)) if specs else 0
    next_i = 0
    lock = threading.Lock()
    done = [0]

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
            res = f2.run_episode(client, sp["scenario"], sp["regime"],
                                 (lambda s, o: model.act(o)),
                                 seed=int(sp["seed"]), mu=float(mu), reveal=float(reveal))
            results[i] = {"success": bool(res["success"]),
                          "sustain": int(res["longest_controlled_drift_run"]),
                          "collision": bool(res["collision"])}
            with lock:
                done[0] += 1

    t0 = time.time()
    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    # aggregate per cell
    by_cell: dict[str, dict] = {}
    for sp, r in zip(specs, results):
        cid = sp["cell"]["cell_id"]
        agg = by_cell.setdefault(cid, {"cell": sp["cell"], "regime": sp["regime"],
                                       "n": 0, "n_succ": 0, "sustains": []})
        agg["n"] += 1
        agg["n_succ"] += int(r["success"])
        if sp["regime"] == "drift":
            agg["sustains"].append(int(r["sustain"]))
    rows = []
    for cid, agg in by_cell.items():
        row = {"cell_id": cid, "regime": agg["regime"], "n": agg["n"],
               "n_succ": agg["n_succ"], "success": agg["n_succ"] / max(1, agg["n"])}
        c = agg["cell"]
        if agg["regime"] == "drift":
            row.update({"mu": c["mu"], "beta": c["beta"], "spec": c["spec_name"],
                        "precheck_sustain": c["precheck_sustain"],
                        "mean_sustain": float(np.mean(agg["sustains"])) if agg["sustains"] else 0.0,
                        "max_sustain": int(np.max(agg["sustains"])) if agg["sustains"] else 0})
        else:
            row.update({"reveal": c["reveal"], "mu": c["mu"], "geometry": c["geometry"]})
        rows.append(row)
    print(f"  [{label}] validated {len(specs)} episodes over {len(rows)} cells in {time.time()-t0:.1f}s", flush=True)
    return rows


def _select_score(rows: list[dict]) -> tuple[float, float]:
    drift = [r["success"] for r in rows if r["regime"] == "drift"]
    avoid = [r["success"] for r in rows if r["regime"] == "avoidance"]
    av = float(np.mean(avoid)) if avoid else 0.0
    dr = float(np.mean(drift)) if drift else 0.0
    return (av + dr, dr)  # maximize total cleared, tie-break drift (the harder regime here)


# ============================================================ main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds-per-cell", type=int, default=6)
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=3)
    ap.add_argument("--select-drift-seeds", type=int, default=3, help="per-cell drift seeds for seed-SELECTION eval")
    ap.add_argument("--select-avoid-seeds", type=int, default=2, help="per-cell avoid seeds for seed-SELECTION eval")
    ap.add_argument("--val-drift-seeds", type=int, default=8, help="per-cell drift seeds for FINAL per-cell validation")
    ap.add_argument("--val-avoid-seeds", type=int, default=6, help="per-cell avoid seeds for FINAL per-cell validation")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    ap.add_argument("--report", type=str, default=str(RUN_DIR / "distill_s1_fullscenario_report.json"))
    args = ap.parse_args()

    drift_cells = _load_drift_cells()
    avoid_cells = _load_avoid_cells()
    print(f"FULL-SCENARIO spectrum: {len(drift_cells)} drift cells + {len(avoid_cells)} avoid cells "
          f"= {len(drift_cells)+len(avoid_cells)} cells", flush=True)
    for c in drift_cells:
        print(f"  DRIFT cell {c['cell_id']:24s} spec={c['spec_name']:18s} precheck_sustain={c['precheck_sustain']}", flush=True)

    drift_specs = _drift_demo_specs(drift_cells, args.drift_seeds_per_cell)
    avoid_specs = _avoid_demo_specs(avoid_cells, args.avoid_seeds_per_cell)
    print(f"\ncollecting demos on Chrono: {len(drift_specs)} drift + {len(avoid_specs)} avoid episodes, "
          f"{args.workers} workers", flush=True)

    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"distill_fs_w{w}_stderr.log", read_timeout_s=600.0)
               for w in range(args.workers)]
    drift_demo = avoid_demo = None
    best = None  # (score, state_dict, stats, seed, select_rows)
    try:
        drift_demo = collect_demos(clients, drift_specs, label="DRIFT")
        avoid_demo = collect_demos(clients, avoid_specs, label="AVOID")
        if drift_demo["obs"].shape[0] == 0 or avoid_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: a regime collected 0 demo frames; cannot distill.")

        # seed-selection validation specs (disjoint namespace, modest seed count)
        sel_specs = _val_specs(drift_cells, avoid_cells, n_drift=args.select_drift_seeds,
                               n_avoid=args.select_avoid_seeds, namespace="select_fs")

        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- distill seed {s} ---", flush=True)
            m, st = distill(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                            holdout_frac=args.holdout_frac, seed=s)
            sel_rows = validate_per_cell(clients, m, sel_specs, label=f"SELECT seed{s}")
            score = _select_score(sel_rows)
            dr = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "drift"]))
            av = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "avoidance"]))
            print(f"  seed {s} CHRONO SELECT: avoid={av:.3f} drift={dr:.3f} (score={score[0]:.3f})", flush=True)
            st["select_avoid"] = av; st["select_drift"] = dr; st["distill_seed"] = s
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel_rows)

        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED distilled seed {best[3]} "
              f"(Chrono select avoid={stats['select_avoid']:.3f} drift={stats['select_drift']:.3f})", flush=True)

        # save BEFORE final validation so the policy is durable even if validation is interrupted
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": model.state_dict(), "gated": True,
            "seed": args.seed, "label": "distill_both_fullscenario",
            "n_drift_cells": len(drift_cells), "n_avoid_cells": len(avoid_cells),
            "drift_teacher": "tuned_DriftFeedbackPolicy_specs_for", "avoid_teacher": "make_avoidance_teacher_oracle",
            "drift_demo_frames": int(drift_demo["obs"].shape[0]),
            "avoid_demo_frames": int(avoid_demo["obs"].shape[0]),
            "drift_demo_episodes": int(drift_demo["n_episodes"]), "avoid_demo_episodes": int(avoid_demo["n_episodes"]),
            "drift_teacher_success": int(drift_demo["n_success"]), "avoid_teacher_success": int(avoid_demo["n_success"]),
            **stats,
        }, out)
        print(f"saved distilled student -> {out}", flush=True)

        # ===================== FINAL per-cell Chrono validation (disjoint namespace) =====================
        print(f"\n=== FINAL PER-CELL CHRONO VALIDATION ({args.val_drift_seeds} drift / "
              f"{args.val_avoid_seeds} avoid seeds per cell) ===", flush=True)
        val_specs = _val_specs(drift_cells, avoid_cells, n_drift=args.val_drift_seeds,
                               n_avoid=args.val_avoid_seeds, namespace="validate_fs")
        val_rows = validate_per_cell(clients, model, val_specs, label="VALIDATE")
    finally:
        for c in clients:
            c.close()

    drift_rows = sorted([r for r in val_rows if r["regime"] == "drift"], key=lambda r: (r["mu"], r["beta"]))
    avoid_rows = sorted([r for r in val_rows if r["regime"] == "avoidance"],
                        key=lambda r: (r["reveal"], r["mu"], r["geometry"]))

    print("\n=== PER-CELL DRIFT VALIDATION (12 cells) ===", flush=True)
    print(f"  {'cell':26s} {'spec':18s} {'succ':>6s} {'mean_sus':>9s} {'max_sus':>8s} {'pre_sus':>8s}", flush=True)
    for r in drift_rows:
        cleared = "OK" if r["success"] >= 0.5 else "MISS"
        print(f"  {r['cell_id']:26s} {r['spec']:18s} {r['n_succ']}/{r['n']}={r['success']:.2f} "
              f"{r['mean_sustain']:9.1f} {r['max_sustain']:8d} {r['precheck_sustain']:8d}  {cleared}", flush=True)

    print("\n=== PER-CELL AVOID VALIDATION (36 cells) ===", flush=True)
    print(f"  {'cell':40s} {'succ':>8s}", flush=True)
    for r in avoid_rows:
        cleared = "OK" if r["success"] >= 0.5 else "MISS"
        print(f"  {r['cell_id']:40s} {r['n_succ']}/{r['n']}={r['success']:.2f}  {cleared}", flush=True)

    # headline
    n_drift = len(drift_rows); n_avoid = len(avoid_rows)
    drift_cleared = sum(1 for r in drift_rows if r["success"] >= 0.5)
    avoid_cleared = sum(1 for r in avoid_rows if r["success"] >= 0.5)
    mean_drift_succ = float(np.mean([r["success"] for r in drift_rows])) if drift_rows else 0.0
    mean_avoid_succ = float(np.mean([r["success"] for r in avoid_rows])) if avoid_rows else 0.0
    mean_drift_sustain = float(np.mean([r["mean_sustain"] for r in drift_rows])) if drift_rows else 0.0
    total_cleared = drift_cleared + avoid_cleared

    print("\n=== HEADLINE: ONE GATED FULL-SCENARIO DRIVER ===", flush=True)
    print(f"  cells cleared (success>=0.5): {total_cleared}/{n_drift+n_avoid} "
          f"(drift {drift_cleared}/{n_drift}, avoid {avoid_cleared}/{n_avoid})", flush=True)
    print(f"  mean drift success={mean_drift_succ:.3f}  mean drift sustain={mean_drift_sustain:.1f} steps", flush=True)
    print(f"  mean avoid success={mean_avoid_succ:.3f}", flush=True)
    print(f"  gate routing: drift={stats['gate_mean_drift']:.3f} avoid={stats['gate_mean_avoid']:.3f} "
          f"(separation {abs(stats['gate_mean_drift']-stats['gate_mean_avoid']):.3f})", flush=True)

    report = {
        "protocol": "distill_both_fullscenario",
        "policy_path": str(Path(args.out)),
        "n_drift_cells": n_drift, "n_avoid_cells": n_avoid,
        "selected_seed": best[3],
        "demo": {
            "drift_episodes": int(drift_demo["n_episodes"]), "drift_teacher_success": int(drift_demo["n_success"]),
            "drift_frames": int(drift_demo["obs"].shape[0]),
            "avoid_episodes": int(avoid_demo["n_episodes"]), "avoid_teacher_success": int(avoid_demo["n_success"]),
            "avoid_frames": int(avoid_demo["obs"].shape[0]),
            "drift_seeds_per_cell": args.drift_seeds_per_cell, "avoid_seeds_per_cell": args.avoid_seeds_per_cell,
        },
        "distill": {k: stats[k] for k in stats},
        "validation": {
            "val_drift_seeds": args.val_drift_seeds, "val_avoid_seeds": args.val_avoid_seeds,
            "drift_cells": drift_rows, "avoid_cells": avoid_rows,
        },
        "headline": {
            "total_cells": n_drift + n_avoid, "total_cleared": total_cleared,
            "drift_cleared": drift_cleared, "avoid_cleared": avoid_cleared,
            "mean_drift_success": mean_drift_succ, "mean_avoid_success": mean_avoid_succ,
            "mean_drift_sustain": mean_drift_sustain,
        },
    }
    Path(args.report).write_text(json.dumps(report, indent=2, default=float))
    print(f"\nwrote report -> {args.report}", flush=True)


if __name__ == "__main__":
    main()
