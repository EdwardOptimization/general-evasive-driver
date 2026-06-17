"""DAgger v2 — WARM-START + HARD-CELL-FOCUSED continuation of the avoidance head.

WHY (the user's diagnosis, believed correct AND now corroborated by A5): the do-both distilled
student already does drift=1.000 on Chrono and avoid plateaus at 0.900. The 4/40 A5 avoid
failures are COLLISIONS at the tightest cells: reveal=9.5 x mu in {0.3625, 0.5875} and
reveal=12.0 x mu=0.5875 (smallest reveal + lowest grip). The avoid ORACLE scores 40/40=1.000
on that SAME A5 grid INCLUDING those cells, so 1.0 IS reachable -- the residual is an imitation
gap on the tightest cells, NOT physics. DAgger (collect oracle labels ON THE STUDENT'S OWN
state distribution) is the canonical fix; concentrating it on the failing cells closes the gap
there without spending budget where the student is already perfect.

WHAT this does differently from dagger_avoid.py (which RESTARTS from base demos each run):
  1. WARM-START the student: round-0 rollouts are driven by the CURRENT best DAgger student
     (distill_dagger_policy.pt, avoid=0.900) instead of distill_both_policy.pt -- so we
     CONTINUE from 0.900 rather than restart from ~0.56.
  2. WARM-START the demo pool: if a persisted DAgger demo .npz exists (dagger_demos_v2.npz),
     load it as the starting avoid pool (base oracle demos + accumulated recovery labels). On a
     cold first v2 run there is no .npz (the prior run only persisted COUNTS in
     dagger_history.json, not the demo arrays), so we instead REGENERATE the recovery pool by
     rolling the loaded 0.900 student out -- those labels are on-distribution for the current
     policy, which is exactly what DAgger wants. Every round APPENDS and the pool is RE-SAVED so
     subsequent v2 runs truly warm-start the demos.
  3. HARD-CELLS-FOCUSED rollout budget: instead of uniform seeds/cell + a small hard extra, pour
     MOST of the rollout budget into the 4 failing cells (--hard-cell-seeds, e.g. 10-15) with a
     light --easy-cell-seeds (e.g. 1-2) sweep over the rest of the grid to keep the easy cells
     anchored (no regression). This is the user's HARD-CELLS-FOCUSED mode.

The drift head is NEVER touched: drift_demo is collected once with the GPU drift expert (identical
to distill_both) and reused for every re-distill, so drift cannot regress by construction. We ALSO
VERIFY drift=1.000 on the Chrono select namespace for EVERY distilled seed (the user's requirement).

New file only. Imports the verbatim machinery from dagger_avoid.py + distill_both.py (no protected
module is modified). Reuses the disjoint 'dagger_v2' seed namespace for rollouts and the
'distill_select' namespace (via distill_both._chrono_select_eval) for selection -- the frozen A5
'validation' grid is never touched.

Usage (base env has torch; ChronoWorkerClient spawns the chrono env):
    PYTHONPATH=src python scripts/feasibility_audit/dagger_avoid_v2.py \
        --workers 16 --rounds 3 --seed-sweep 6 \
        --hard-cell-seeds 12 --easy-cell-seeds 2 \
        --warm-start runs/feasibility_audit/phase4_f2/distill_dagger_policy.pt \
        --out runs/feasibility_audit/phase4_f2/distill_dagger_v2_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import phase4_f2_train as f2  # noqa: E402
import distill_both as db  # noqa: E402
import dagger_avoid as dag  # noqa: E402  (reuse the verbatim DAgger episode + re-distill machinery)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_dagger_v2_policy.pt"
DEFAULT_WARM = RUN_DIR / "distill_dagger_policy.pt"
DEMO_CACHE = RUN_DIR / "dagger_demos_v2.npz"  # persisted growing avoid pool (warm-start across runs)

# The FAILING set from the user / A5 breakdown: smallest reveal + lowest grip (collisions).
HARD_CELLS = (
    (9.5, 0.3625),
    (9.5, 0.5875),
    (12.0, 0.3625),  # included: adjacent low-mu small-reveal cell (oracle-perfect, near the boundary)
    (12.0, 0.5875),
)


# ----------------------------------------------------------------- hard-cell-focused roll-out spec set


def _hard_focus_specs(hard_cell_seeds: int, easy_cell_seeds: int, round_idx: int) -> list[dict]:
    """MOST of the budget on the 4 failing cells; a light sweep over the rest of the grid.

    Disjoint 'dagger_v2' seed namespace keyed by round so successive rounds visit FRESH scenarios
    (DAgger needs new states, not the same ones re-labeled). The A5 'validation' grid and the
    'distill'/'distill_select' namespaces are never touched.
    """
    grid = f2._avoidance_grid(quick=False)
    hard_set = {(round(r, 4), round(m, 4)) for (r, m) in HARD_CELLS}
    specs: list[dict] = []
    for ci, (reveal, mu) in enumerate(grid):
        is_hard = (round(reveal, 4), round(mu, 4)) in hard_set
        n = hard_cell_seeds if is_hard else easy_cell_seeds
        for i in range(n):
            seed = int(f2._seed_for("dagger_v2", round_idx, ci, i, round(reveal, 4), round(mu, 4)))
            specs.append({
                "regime": "avoidance", "seed": seed, "mu": float(mu), "reveal": float(reveal),
                "scenario": f2._avoidance_scenario(seed, max_steps=db.AVOID_MAX_STEPS,
                                                   reveal=float(reveal), mu=float(mu)),
                "is_hard": is_hard,
            })
    return specs


def _load_student(path: Path) -> f2.AsymmetricActorCritic:
    ck = torch.load(path, map_location="cpu")
    model = f2.AsymmetricActorCritic(gated=bool(ck.get("gated", True)))
    model.load_state_dict(ck["state_dict"])
    model.eval()
    print(f"WARM-START student {path.name} "
          f"(label={ck.get('label')}, select_avoid={ck.get('select_avoid')}, "
          f"select_drift={ck.get('select_drift')})", flush=True)
    return model


def main() -> None:
    ap = argparse.ArgumentParser(description="Warm-start, hard-cell-focused DAgger for the avoid head.")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--rounds", type=int, default=3, help="DAgger rounds (2-3)")
    ap.add_argument("--warm-start", type=str, default=str(DEFAULT_WARM),
                    help="checkpoint to load as the round-0 student (continue from its avoid).")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    # frozen drift head (unchanged) + base oracle avoid demos (deterministic, cheap)
    ap.add_argument("--drift-seeds", type=int, default=24, help="drift demo seeds PER difficulty (unchanged head)")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="base avoid oracle seeds per grid cell")
    # HARD-FOCUS rollout set
    ap.add_argument("--hard-cell-seeds", type=int, default=12, help="student roll-out seeds per HARD cell / round")
    ap.add_argument("--easy-cell-seeds", type=int, default=2, help="student roll-out seeds per non-hard cell / round")
    # demo-pool warm-start
    ap.add_argument("--demo-cache", type=str, default=str(DEMO_CACHE),
                    help="persisted growing avoid pool (.npz); loaded if present, re-saved each round.")
    ap.add_argument("--no-demo-cache", action="store_true", help="ignore any persisted demo pool (cold start).")
    # re-distill
    ap.add_argument("--epochs", type=int, default=6000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=6)
    ap.add_argument("--select-avoid-units", type=int, default=20)
    ap.add_argument("--select-drift-units", type=int, default=8)
    args = ap.parse_args()

    expert = db.load_drift_expert()
    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"dagger_v2_w{w}_stderr.log") for w in range(args.workers)]
    history: list[dict] = []
    demo_cache = Path(args.demo_cache)
    try:
        # --- DRIFT demos: collected ONCE with the GPU drift expert; reused every round (never changes) ---
        drift_specs = db._drift_specs(args.drift_seeds)
        drift_demo = db.collect_demos(clients, drift_specs, expert, label="DRIFT(frozen)")
        if drift_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: drift collected 0 frames.")

        # --- avoid pool warm-start: persisted .npz if available, else regenerate base oracle demos ---
        if demo_cache.exists() and not args.no_demo_cache:
            z = np.load(demo_cache)
            avoid_obs = z["obs"].astype(np.float32)
            avoid_act = z["act"].astype(np.float32)
            base_n = int(z["base_n"]) if "base_n" in z else int(avoid_obs.shape[0])
            base_avoid = {"n_episodes": int(z["base_episodes"]) if "base_episodes" in z else 0,
                          "n_success": int(z["base_success"]) if "base_success" in z else 0}
            print(f"WARM-START demo pool from {demo_cache.name}: {avoid_obs.shape[0]} frames "
                  f"(base {base_n} + accumulated DAgger {avoid_obs.shape[0]-base_n})", flush=True)
        else:
            avoid_specs = db._avoid_specs(args.avoid_seeds_per_cell)
            base_avoid = db.collect_demos(clients, avoid_specs, expert, label="AVOID-oracle(base)")
            if base_avoid["obs"].shape[0] == 0:
                raise SystemExit("FATAL: base avoid collected 0 frames.")
            base_n = int(base_avoid["obs"].shape[0])
            avoid_obs = base_avoid["obs"].copy()
            avoid_act = base_avoid["act"].copy()
            print(f"COLD demo pool: {base_n} base oracle frames "
                  f"(no persisted dagger_demos_v2.npz; will REGENERATE recovery labels by rolling out "
                  f"the warm-started 0.900 student -- on-distribution for the current policy).", flush=True)

        # round-0 student = the warm-start checkpoint (continue from its avoid, ~0.900).
        student = _load_student(Path(args.warm_start))
        best_overall = None  # ((avoid, drift), state, stats, seed, round)

        for r in range(int(args.rounds)):
            print(f"\n========================= DAgger-v2 ROUND {r} =========================", flush=True)
            # 1) roll the CURRENT student out HARD-FOCUSED; label every reveal-post state with the oracle.
            specs = _hard_focus_specs(args.hard_cell_seeds, args.easy_cell_seeds, r)
            n_hard = sum(1 for s in specs if s["is_hard"])
            print(f"  HARD-FOCUS roll-out: {len(specs)} episodes "
                  f"({n_hard} on the 4 hard cells @ {args.hard_cell_seeds}/cell, "
                  f"{len(specs)-n_hard} on the rest @ {args.easy_cell_seeds}/cell)", flush=True)
            dagout = dag.collect_dagger(clients, specs, student)

            # per-hard-cell rollout success (the trend the user asked for), derived EXACTLY and for
            # FREE from collect_dagger's output: totals-per-cell come from the spec grid, fails-per-cell
            # come from dagout["fail_cells"] (already counted), success = total - fails. No re-rollout.
            hard_succ = _hard_cell_trend_from_failcells(specs, dagout["fail_cells"])

            if dagout["obs"].shape[0] > 0:
                avoid_obs = np.concatenate([avoid_obs, dagout["obs"]], 0)
                avoid_act = np.concatenate([avoid_act, dagout["act"]], 0)
            aug_avoid = {"obs": avoid_obs, "act": avoid_act,
                         "n_episodes": base_avoid.get("n_episodes", 0),
                         "n_success": base_avoid.get("n_success", 0)}
            print(f"  AUGMENTED avoid pool: {avoid_obs.shape[0]} frames "
                  f"(base {base_n} + DAgger {avoid_obs.shape[0]-base_n})", flush=True)
            print(f"  HARD-CELL rollout success this round: {hard_succ['summary']}", flush=True)

            # persist the growing pool so the NEXT v2 run truly warm-starts the demos.
            np.savez_compressed(demo_cache, obs=avoid_obs, act=avoid_act, base_n=base_n,
                                base_episodes=base_avoid.get("n_episodes", 0),
                                base_success=base_avoid.get("n_success", 0))

            # 2) re-distill on (frozen drift) + (augmented avoid); seed sweep + Chrono select.
            best, per_seed = dag._redistill_select(
                clients, drift_demo, aug_avoid, epochs=args.epochs, lr=args.lr, batch=args.batch,
                holdout_frac=args.holdout_frac, seed0=args.seed, seed_sweep=args.seed_sweep,
                select_avoid_units=args.select_avoid_units, select_drift_units=args.select_drift_units)
            (av, dr), state, stats, win_seed = best
            # HARD requirement: drift must stay 1.000 on EVERY distilled seed; flag any regression.
            drift_regressed = [ps for ps in per_seed if ps["select_drift"] < 0.999]
            if drift_regressed:
                print(f"  !! WARNING: drift < 1.000 on seeds "
                      f"{[(ps['seed'], ps['select_drift']) for ps in drift_regressed]}", flush=True)
            print(f"\n  ROUND {r} SELECTED seed {win_seed}: select avoid={av:.3f} drift={dr:.3f}", flush=True)

            # 3) the next round rolls out THIS round's selected student (DAgger iterates on its own states).
            student = f2.AsymmetricActorCritic(gated=True)
            student.load_state_dict(state)
            student.eval()

            history.append({
                "round": r,
                "select_avoid": av, "select_drift": dr, "win_seed": int(win_seed),
                "aug_avoid_frames": int(avoid_obs.shape[0]),
                "base_avoid_frames": int(base_n),
                "dagger_round_labels": int(dagout["obs"].shape[0]),
                "dagger_rollout_success": int(dagout["n_success"]),
                "dagger_rollout_offtrack": int(dagout["n_offtrack"]),
                "dagger_rollout_collision": int(dagout["n_collision"]),
                "dagger_rollout_other_fail": int(dagout["n_other_fail"]),
                "dagger_rollout_episodes": int(dagout["n_episodes"]),
                "hard_cell_rollout": hard_succ["per_cell"],
                "hard_cell_rollout_summary": hard_succ["summary"],
                "per_seed": per_seed,
                "fail_cells": dagout["fail_cells"],
                "other_reasons": dagout["other_reasons"],
                "drift_all_seeds_1000": bool(not drift_regressed),
            })
            score_r = (av, dr)
            if best_overall is None or score_r > best_overall[0]:
                best_overall = (score_r, {k: v.clone() for k, v in state.items()}, stats, win_seed, r)

        (sc_av, sc_dr), best_state, best_stats, best_seed, best_round = best_overall
        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best_state)
    finally:
        for c in clients:
            c.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(), "gated": True,
        "label": "distill_dagger_v2_avoid_hardfocus",
        "drift_teacher": "gpu_physics_policy_seed0",
        "avoid_teacher": "make_avoidance_teacher_oracle+DAgger(warm+hardfocus)",
        "select_avoid": float(sc_av), "select_drift": float(sc_dr),
        "best_round": int(best_round), "best_seed": int(best_seed),
        "warm_start_from": str(args.warm_start),
        "drift_demo_frames": int(drift_demo["obs"].shape[0]),
        "avoid_demo_frames_final": int(avoid_obs.shape[0]),
        "base_avoid_frames": int(base_n),
        "hard_cells": list(HARD_CELLS),
        "dagger_history": history,
        **best_stats,
    }, out)

    print("\n=== DAGGER-v2 REPORT ===", flush=True)
    print(f"  DRIFT demos (frozen): {drift_demo['obs'].shape[0]} frames", flush=True)
    print(f"  BASE avoid frames: {base_n}", flush=True)
    for h in history:
        print(f"  round {h['round']}: aug_avoid={h['aug_avoid_frames']} frames "
              f"(+{h['dagger_round_labels']} this round) | "
              f"hard-cell rollout {h['hard_cell_rollout_summary']} | "
              f"SELECT avoid={h['select_avoid']:.3f} drift={h['select_drift']:.3f} (seed {h['win_seed']})"
              f"{'  [DRIFT-REGRESSION!]' if not h['drift_all_seeds_1000'] else ''}", flush=True)
    print(f"  BEST: round {best_round} seed {best_seed} -> select avoid={sc_av:.3f} drift={sc_dr:.3f}", flush=True)
    print(f"\nsaved DAgger-v2 student -> {out}", flush=True)
    hist_path = RUN_DIR / "dagger_v2_history.json"
    hist_path.write_text(json.dumps({"history": history, "best_round": best_round,
                                     "best_seed": best_seed, "select_avoid": sc_av,
                                     "select_drift": sc_dr, "base_avoid_frames": base_n,
                                     "drift_frames": int(drift_demo["obs"].shape[0]),
                                     "warm_start_from": str(args.warm_start)}, indent=2))
    print(f"saved DAgger-v2 history -> {hist_path}", flush=True)
    print(f"\nNext (FINAL A5): PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate.py "
          f"--policy {out} --avoid-units 40 --drift-units 20 --workers 16", flush=True)
    print(f"Then per-cell: PYTHONPATH=src python scripts/feasibility_audit/dagger_a5_breakdown.py "
          f"--policy {out} --workers 16", flush=True)


def _hard_cell_trend_from_failcells(specs, fail_cells: dict) -> dict:
    """Exact per-hard-cell rollout success, derived for FREE from collect_dagger's output.

    collect_dagger keys its fail_cells dict as f"{round(reveal,2)}|{round(mu,4)}" -> n_fail.
    Totals per cell are known from the spec grid. success = total - fails. No extra rollout.
    """
    hard_set = {(round(r, 4), round(m, 4)) for (r, m) in HARD_CELLS}
    totals: dict[tuple, int] = {}
    for s in specs:
        k = (round(s["reveal"], 4), round(s["mu"], 4))
        if k in hard_set:
            totals[(round(s["reveal"], 2), round(s["mu"], 4))] = totals.get((round(s["reveal"], 2), round(s["mu"], 4)), 0) + 1
    per_cell: dict[str, dict] = {}
    for (rv, mu), n in sorted(totals.items()):
        n_fail = int(fail_cells.get(f"{rv}|{mu}", 0))
        succ = max(0, n - n_fail)
        per_cell[f"{rv}x{mu}"] = {"succ": succ, "n": n}
    tot_s = sum(v["succ"] for v in per_cell.values())
    tot_n = sum(v["n"] for v in per_cell.values())
    summary = " ".join(f"{k}={v['succ']}/{v['n']}" for k, v in per_cell.items())
    summary = f"{summary}  [TOTAL {tot_s}/{tot_n}={tot_s/max(1,tot_n):.3f}]"
    return {"per_cell": per_cell, "summary": summary}


if __name__ == "__main__":
    main()
