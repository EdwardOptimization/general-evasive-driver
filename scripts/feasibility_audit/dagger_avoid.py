"""DAgger for the AVOIDANCE head of the distilled do-both gated student.

WHY (the user's diagnosis, believed correct): the distilled student already does drift=1.000
on Chrono, but avoid plateaus at 0.825. The 0.825 failures are OFF-LANE drift -- the student's
small per-step imitation error compounds over the post-reveal avoidance maneuver and it slides
off-lane (NOT a collision). This is the TEXTBOOK behavior-cloning failure mode: the student
visits states the oracle demos never showed (because the oracle never drifts off-lane), so it
has no recovery label there. DAgger is the canonical fix -- collect labels ON THE STUDENT'S OWN
state distribution.

WHAT this does (gated architecture => we ONLY touch the avoidance head/demos; drift stays 1.0):
  1. Start from the CURRENT distilled student (distill_both_policy.pt).
  2. DAgger rounds: run the CURRENT student on the FULL reveal x mu avoidance grid + extra seeds
     (oversampling the HARD cells -- small reveal 9.5/12 at low mu -- where it drifts off-lane)
     on REAL Chrono. At every visited reveal-post state, query the avoid ORACLE
     make_avoidance_teacher(reveal, mu) for the correct action -> (student-visited obs72,
     oracle_action) recovery labels. Append to the avoid demo pool (the original oracle demos
     are kept).
  3. Re-distill the gated student on (UNCHANGED drift demos) + (AUGMENTED avoid demos), with the
     SAME seed sweep + Chrono-task-score selection on the disjoint distill_select namespace (NOT
     the A5 grid), using distill_both.distill / distill_both._chrono_select_eval verbatim.
  4. Track the select-namespace avoid score per round to watch the gap close.
  5. Save runs/feasibility_audit/phase4_f2/distill_dagger_policy.pt.

The drift demos and the drift teacher are NEVER touched: drift_demo is collected once with the
GPU drift expert (identical to distill_both) and reused for every re-distill, so drift cannot
regress by construction (the only thing changing across rounds is the avoid demo pool).

Usage (base env has torch; ChronoWorkerClient spawns the chrono env):
    PYTHONPATH=src python scripts/feasibility_audit/dagger_avoid.py \
        --workers 16 --rounds 3 --seed-sweep 8 \
        --out runs/feasibility_audit/phase4_f2/distill_dagger_policy.pt
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_dagger_policy.pt"
START_STUDENT = RUN_DIR / "distill_both_policy.pt"

# The HARD cells: small reveal at low mu, where the post-reveal maneuver is tightest and the
# student's compounding off-lane error shows up. We oversample these in the DAgger roll-out set.
HARD_REVEALS = (9.5, 12.0)
HARD_MUS = (0.3625, 0.5875)


def _load_student(path: Path) -> f2.AsymmetricActorCritic:
    ck = torch.load(path, map_location="cpu")
    model = f2.AsymmetricActorCritic(gated=bool(ck.get("gated", True)))
    model.load_state_dict(ck["state_dict"])
    model.eval()
    print(f"loaded START student {path.name} "
          f"(gated={ck.get('gated')}, select_avoid={ck.get('select_avoid')}, "
          f"select_drift={ck.get('select_drift')})", flush=True)
    return model


# ----------------------------------------------------------------- DAgger roll-out spec set


def _dagger_specs(seeds_per_cell: int, hard_extra_seeds: int, round_idx: int) -> list[dict]:
    """Full reveal x mu grid (seeds_per_cell each) + extra seeds on the HARD cells.

    Disjoint seed namespace 'dagger' keyed by round so successive rounds visit FRESH scenarios
    (DAgger needs new states, not the same ones re-labeled). The A5 grid and the distill / distill_select
    namespaces are never touched.
    """
    grid = f2._avoidance_grid(quick=False)
    specs: list[dict] = []
    for ci, (reveal, mu) in enumerate(grid):
        n = seeds_per_cell
        if reveal in HARD_REVEALS and mu in HARD_MUS:
            n += hard_extra_seeds  # oversample the off-lane-prone hard cells
        for i in range(n):
            seed = int(f2._seed_for("dagger", round_idx, ci, i, round(reveal, 4), round(mu, 4)))
            specs.append({
                "regime": "avoidance", "seed": seed, "mu": float(mu), "reveal": float(reveal),
                "scenario": f2._avoidance_scenario(seed, max_steps=db.AVOID_MAX_STEPS,
                                                   reveal=float(reveal), mu=float(mu)),
            })
    return specs


# ----------------------------------------------------------------- DAgger episode (student drives, oracle labels)


def _dagger_episode(client: ChronoWorkerClient, model: f2.AsymmetricActorCritic, sp: dict) -> dict:
    """Run ONE avoidance episode driven by the STUDENT; label every reveal-post state with the ORACLE.

    This is run_episode's avoidance loop, but the ACTING policy is the student (model.act) while the
    LABEL at each visited obs72 is the oracle's action for that state (the DAgger interactive expert).
    Reveal-gating mirrors run_episode exactly (AVOIDANCE_BC_REVEAL_POST_ONLY + _obstacle_visible) so the
    recovery labels lie on the same obs72-observable segment the deployable actor acts on. The oracle is
    a stateful controller queried per visited state (no environment reset between query and the student's
    own step) -- it returns the correct action FOR THE STUDENT-VISITED state.
    """
    reveal, mu, seed = float(sp["reveal"]), float(sp["mu"]), int(sp["seed"])
    scenario = sp["scenario"]
    oracle = f2.make_avoidance_teacher(reveal=reveal, mu=mu).factory()  # fresh stateful oracle controller

    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=seed)
    obs = np.asarray(obs, dtype=np.float32)
    info = dict(reset_reply.get("info", {}))
    bc_frames: list[np.ndarray] = []
    bc_targets: list[np.ndarray] = []
    steps = 0
    terminated = truncated = False
    collision_any = False
    offtrack_any = False
    max_steps = int(scenario["max_steps"])
    while not (terminated or truncated) and steps < max_steps:
        revealed = f2._obstacle_visible(obs, info)
        if f2._finite_obs72(obs) and (revealed or not f2.AVOIDANCE_BC_REVEAL_POST_ONLY):
            # DAgger label: oracle's correct action AT THE STUDENT-VISITED state.
            oracle_a = np.clip(np.asarray(oracle(steps, obs), dtype=np.float32), -1.0, 1.0)
            bc_frames.append(obs.astype(np.float32).copy())
            bc_targets.append(oracle_a)
            action = np.clip(np.asarray(model.act(obs), dtype=np.float32), -1.0, 1.0)  # STUDENT drives
        else:
            # before reveal we still need to advance the episode; drive with the student.
            # (oracle is queried only on reveal-post states, matching the demo segment.)
            _ = oracle(steps, obs)  # keep the stateful oracle clock in lock-step with the env steps
            action = np.clip(np.asarray(model.act(obs), dtype=np.float32), -1.0, 1.0)
        obs, terminated, truncated, _status, info = client.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        info = dict(info)
        collision = bool(info.get("collision", False)) or str(info.get("termination_reason", "")) == "obstacle_collision"
        collision_any = collision_any or collision
        offtrack_any = offtrack_any or (str(info.get("termination_reason", "")) == "off_track")
        steps += 1
    success = f2._avoidance_success(collision_any, info)
    # honest failure forensics: the FINAL termination/completion tokens (so "other" failures
    # -- not collision, not off_track -- are named, not lumped).
    term_reason = str(info.get("termination_reason", ""))
    comp_reason = str(info.get("completion_reason", ""))
    return {
        "reveal": reveal, "mu": mu, "seed": seed,
        "success": bool(success), "collision": bool(collision_any), "offtrack": bool(offtrack_any),
        "termination_reason": term_reason, "completion_reason": comp_reason,
        "steps": int(steps),
        "bc_frames": np.stack(bc_frames).astype(np.float32) if bc_frames else np.zeros((0, f2.HUMAN_VIEW_OBS_DIM), np.float32),
        "bc_targets": np.stack(bc_targets).astype(np.float32) if bc_targets else np.zeros((0, f2.ACT_DIM), np.float32),
    }


def collect_dagger(clients: list[ChronoWorkerClient], specs: list[dict],
                   model: f2.AsymmetricActorCritic) -> dict:
    """W-way parallel DAgger roll-outs; pool (student-visited obs72 -> oracle action) recovery labels.

    Also returns a per-failure-mode breakdown so we can SEE the student's failures are off-lane
    (off_track) rather than collisions -- the diagnosis DAgger targets.
    """
    results: list[dict | None] = [None] * len(specs)
    n_workers = min(len(clients), len(specs)) if specs else 0
    next_i = 0
    lock = threading.Lock()

    def _worker(wi: int) -> None:
        nonlocal next_i
        client = clients[wi]
        while True:
            with lock:
                if next_i >= len(specs):
                    return
                i = next_i
                next_i += 1
            results[i] = _dagger_episode(client, model, specs[i])

    t0 = time.time()
    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    dt = time.time() - t0

    frames, targets = [], []
    n_succ = n_coll = n_off = n_other_fail = 0
    fail_cells: dict[tuple, int] = {}
    other_reasons: dict[str, int] = {}  # name the "other" failures honestly (term|comp tokens)
    for res in results:
        if res is None:
            continue
        if res["bc_frames"].shape[0] > 0:
            frames.append(res["bc_frames"])
            targets.append(res["bc_targets"])
        if res["success"]:
            n_succ += 1
        else:
            key = (round(res["reveal"], 2), round(res["mu"], 4))
            fail_cells[key] = fail_cells.get(key, 0) + 1
            if res["collision"]:
                n_coll += 1
            elif res["offtrack"]:
                n_off += 1
            else:
                n_other_fail += 1
                tok = f"term={res['termination_reason'] or '-'}|comp={res['completion_reason'] or '-'}"
                other_reasons[tok] = other_reasons.get(tok, 0) + 1
    obs = np.concatenate(frames, 0) if frames else np.zeros((0, f2.HUMAN_VIEW_OBS_DIM), np.float32)
    act = np.concatenate(targets, 0) if targets else np.zeros((0, f2.ACT_DIM), np.float32)
    n_fail = len(specs) - n_succ
    print(f"  [DAGGER roll-out] {len(specs)} student episodes: {n_succ} success / {n_fail} fail "
          f"(off_track={n_off}, collision={n_coll}, other={n_other_fail}); "
          f"{obs.shape[0]} recovery labels, {dt:.1f}s", flush=True)
    if other_reasons:
        print("    'other' fail tokens: " + ", ".join(f"{k}->{v}" for k, v in
              sorted(other_reasons.items(), key=lambda kv: -kv[1])), flush=True)
    if fail_cells:
        top = sorted(fail_cells.items(), key=lambda kv: -kv[1])[:6]
        print("    student-fail cells (reveal, mu)->n: " + ", ".join(f"{k}->{v}" for k, v in top), flush=True)
    return {
        "obs": obs, "act": act, "n_episodes": len(specs),
        "n_success": n_succ, "n_offtrack": n_off, "n_collision": n_coll, "n_other_fail": n_other_fail,
        "fail_cells": {f"{k[0]}|{k[1]}": v for k, v in fail_cells.items()},
        "other_reasons": other_reasons,
    }


# ----------------------------------------------------------------- re-distill on augmented avoid demos


def _redistill_select(clients, drift_demo: dict, avoid_demo: dict, *, epochs: int, lr: float, batch: int,
                      holdout_frac: float, seed0: int, seed_sweep: int,
                      select_avoid_units: int, select_drift_units: int):
    """distill_both.distill seed sweep + Chrono select (verbatim machinery) on the augmented avoid pool.

    drift_demo is the UNCHANGED drift demo dict (drift head can't regress). Returns the best model state,
    its stats, the winning seed, and the per-seed select scores.
    """
    best = None  # ((avoid, drift), state, stats, seed)
    per_seed = []
    for s in range(seed0, seed0 + max(1, int(seed_sweep))):
        print(f"\n  --- re-distill seed {s} ---", flush=True)
        m, st = db.distill(drift_demo, avoid_demo, epochs=epochs, lr=lr, batch=batch,
                           holdout_frac=holdout_frac, seed=s)
        sel = db._chrono_select_eval(clients, m, n_avoid=int(select_avoid_units), n_drift=int(select_drift_units))
        av, dr = float(sel.get("avoidance", 0.0)), float(sel.get("drift", 0.0))
        print(f"  seed {s} CHRONO SELECT: avoid={av:.3f} drift={dr:.3f}", flush=True)
        st["select_avoid"] = av; st["select_drift"] = dr; st["distill_seed"] = s
        per_seed.append({"seed": s, "select_avoid": av, "select_drift": dr})
        score = (av, dr)  # maximise avoid (bottleneck) then drift, like distill_both
        if best is None or score > best[0]:
            best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s)
    return best, per_seed


def main() -> None:
    ap = argparse.ArgumentParser(description="DAgger the avoidance head of the distilled do-both student.")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--rounds", type=int, default=3, help="DAgger rounds (2-3)")
    ap.add_argument("--start", type=str, default=str(START_STUDENT))
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    # demo collection (drift + base avoid oracle demos -- same defaults as distill_both)
    ap.add_argument("--drift-seeds", type=int, default=24, help="drift demo seeds PER difficulty (unchanged head)")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="base avoid oracle seeds per grid cell")
    # DAgger roll-out set
    ap.add_argument("--dagger-seeds-per-cell", type=int, default=3, help="student roll-out seeds per grid cell / round")
    ap.add_argument("--dagger-hard-extra", type=int, default=5, help="extra roll-out seeds on the HARD cells / round")
    # re-distill
    ap.add_argument("--epochs", type=int, default=6000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=8)
    ap.add_argument("--select-avoid-units", type=int, default=16)
    ap.add_argument("--select-drift-units", type=int, default=8)
    args = ap.parse_args()

    expert = db.load_drift_expert()
    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"dagger_w{w}_stderr.log") for w in range(args.workers)]
    history: list[dict] = []
    try:
        # --- DRIFT demos: collected ONCE with the GPU drift expert; reused every round (never changes) ---
        drift_specs = db._drift_specs(args.drift_seeds)
        drift_demo = db.collect_demos(clients, drift_specs, expert, label="DRIFT(frozen)")
        if drift_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: drift collected 0 frames.")

        # --- BASE avoid oracle demos (the original distill_both oracle demos -- kept across DAgger) ---
        avoid_specs = db._avoid_specs(args.avoid_seeds_per_cell)
        base_avoid = db.collect_demos(clients, avoid_specs, expert, label="AVOID-oracle(base)")
        if base_avoid["obs"].shape[0] == 0:
            raise SystemExit("FATAL: base avoid collected 0 frames.")
        base_n = int(base_avoid["obs"].shape[0])

        # the growing avoid pool: base oracle demos + accumulated DAgger recovery labels.
        avoid_obs = base_avoid["obs"].copy()
        avoid_act = base_avoid["act"].copy()

        # current student we roll out (round 0 = the START student).
        student = _load_student(Path(args.start))
        best_overall = None  # ((avoid, drift), state, stats, seed, round)

        for r in range(int(args.rounds)):
            print(f"\n========================= DAgger ROUND {r} =========================", flush=True)
            # 1) roll the CURRENT student out on fresh (incl. hard) scenarios; label with the oracle.
            dag = collect_dagger(clients,
                                 _dagger_specs(args.dagger_seeds_per_cell, args.dagger_hard_extra, r),
                                 student)
            if dag["obs"].shape[0] > 0:
                avoid_obs = np.concatenate([avoid_obs, dag["obs"]], 0)
                avoid_act = np.concatenate([avoid_act, dag["act"]], 0)
            aug_avoid = {"obs": avoid_obs, "act": avoid_act,
                         "n_episodes": base_avoid["n_episodes"], "n_success": base_avoid["n_success"]}
            print(f"  AUGMENTED avoid pool: {avoid_obs.shape[0]} frames "
                  f"(base {base_n} + DAgger {avoid_obs.shape[0]-base_n})", flush=True)

            # 2) re-distill on (frozen drift) + (augmented avoid); seed sweep + Chrono select.
            best, per_seed = _redistill_select(
                clients, drift_demo, aug_avoid, epochs=args.epochs, lr=args.lr, batch=args.batch,
                holdout_frac=args.holdout_frac, seed0=args.seed, seed_sweep=args.seed_sweep,
                select_avoid_units=args.select_avoid_units, select_drift_units=args.select_drift_units)
            (av, dr), state, stats, win_seed = best
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
                "dagger_frames_total": int(avoid_obs.shape[0] - base_n),
                "dagger_round_labels": int(dag["obs"].shape[0]),
                "dagger_rollout_success": int(dag["n_success"]),
                "dagger_rollout_offtrack": int(dag["n_offtrack"]),
                "dagger_rollout_collision": int(dag["n_collision"]),
                "dagger_rollout_other_fail": int(dag["n_other_fail"]),
                "dagger_rollout_episodes": int(dag["n_episodes"]),
                "per_seed": per_seed,
                "fail_cells": dag["fail_cells"],
                "other_reasons": dag["other_reasons"],
            })
            score_r = (av, dr)
            if best_overall is None or score_r > best_overall[0]:
                best_overall = (score_r, {k: v.clone() for k, v in state.items()}, stats, win_seed, r)

        # save the best student across all rounds.
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
        "label": "distill_dagger_avoid",
        "drift_teacher": "gpu_physics_policy_seed0", "avoid_teacher": "make_avoidance_teacher_oracle+DAgger",
        "select_avoid": float(sc_av), "select_drift": float(sc_dr),
        "best_round": int(best_round), "best_seed": int(best_seed),
        "drift_demo_frames": int(drift_demo["obs"].shape[0]),
        "avoid_demo_frames_final": int(avoid_obs.shape[0]),
        "base_avoid_frames": int(base_n),
        "dagger_history": history,
        **best_stats,
    }, out)

    print("\n=== DAGGER REPORT ===", flush=True)
    print(f"  DRIFT demos (frozen): {drift_demo['obs'].shape[0]} frames", flush=True)
    print(f"  BASE avoid oracle demos: {base_n} frames", flush=True)
    for h in history:
        print(f"  round {h['round']}: aug_avoid={h['aug_avoid_frames']} frames "
              f"(+{h['dagger_round_labels']} this round) | "
              f"roll-out {h['dagger_rollout_success']}/{h['dagger_rollout_episodes']} succ "
              f"(off_track={h['dagger_rollout_offtrack']}, coll={h['dagger_rollout_collision']}) | "
              f"SELECT avoid={h['select_avoid']:.3f} drift={h['select_drift']:.3f} (seed {h['win_seed']})", flush=True)
    print(f"  BEST: round {best_round} seed {best_seed} -> select avoid={sc_av:.3f} drift={sc_dr:.3f}", flush=True)
    print(f"\nsaved DAgger student -> {out}", flush=True)
    # dump history JSON for the record
    hist_path = RUN_DIR / "dagger_history.json"
    hist_path.write_text(json.dumps({"history": history, "best_round": best_round,
                                     "best_seed": best_seed, "select_avoid": sc_av,
                                     "select_drift": sc_dr, "base_avoid_frames": base_n,
                                     "drift_frames": int(drift_demo["obs"].shape[0])}, indent=2))
    print(f"saved DAgger history -> {hist_path}", flush=True)
    print(f"\nNext (FINAL A5): PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate.py "
          f"--policy {out} --avoid-units 40 --drift-units 20 --workers 16", flush=True)


if __name__ == "__main__":
    main()
