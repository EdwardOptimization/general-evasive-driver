"""S1 FULL-SCENARIO DAgger for the AVOIDANCE head of the gated do-both S1 driver.

WHY (the user's diagnosis, corroborated by the S1 report AND the feasibility JSON):
  distill_s1_fullscenario_policy.pt clears drift 12/12 (1.000) but avoid only 30/36. The 6
  misses are HIGH-MU avoid cells (a BC-fidelity gap, NOT infeasibility): the avoid ORACLE
  scored success=1.0 on EVERY feasible cell incl. these 6 (feasibility_fullscenario.json:
  avoid_teacher_success=180/180). So 1.0 IS reachable on those cells -- the residual is an
  imitation gap on the tightest high-mu cells, exactly what DAgger fixes (collect oracle
  labels ON THE STUDENT'S OWN state distribution).

THE 6 MISSED CELLS (from the S1 per-cell report, success<0.5):
  avoid-r9.5-mu0.3625-offset+0.45   (1/6)   <- the one inward-offset cell
  avoid-r12-mu0.8125-base           (2/6)
  avoid-r16-mu0.8125-base           (2/6)
  avoid-r22-mu0.8125-base           (1/6)
  avoid-r30-mu0.8125-base           (1/6)
  avoid-r30-mu1.0375-base           (0/6)
Pattern: high-mu high-entry-speed base cells + one inward offset.

WHAT this does (the PROVEN dagger_avoid.py recipe, GENERALIZED to the S1 cell catalog with
geometry -- so the DAgger states lie on the exact frozen S1 spectrum, incl. offset/width):
  1. Start from distill_s1_fullscenario_policy.pt (the S1 gated student, gate self-routes).
  2. DRIFT demos collected ONCE with the e4 tuned drift teacher (IDENTICAL to
     distill_both_fullscenario) and reused every round -> drift cannot regress by construction.
     We ALSO re-VALIDATE drift on the disjoint select namespace for EVERY distilled seed and
     flag any seed with drift<0.999 (the user's hard requirement: drift STAYS 12/12).
  3. BASE avoid oracle demos = the original S1 avoid demos (make_avoidance_teacher per cell on
     the geometry-applied scenario), kept across DAgger.
  4. DAgger rounds: roll the CURRENT student out on the S1 avoid cells with the rollout budget
     CONCENTRATED on the 6 HARD cells (--hard-cell-seeds) + the BORDERLINE high-mu cells
     (--mid-cell-seeds, r16-30 x mu0.5875-0.8125) and a light --easy-cell-seeds sweep over the
     rest (anchor, no regression). At every visited reveal-post state, query the avoid ORACLE
     make_avoidance_teacher(reveal,mu) for the correct action -> (student-obs72, oracle_action)
     recovery labels. Append to the avoid pool.
  5. Re-distill the gated student on (FROZEN drift demos) + (AUGMENTED avoid demos), SAME seed
     sweep + Chrono task-score selection on the disjoint 'select_fs' namespace
     (distill_both_fullscenario.distill / validate_per_cell verbatim).
  6. Save runs/feasibility_audit/phase4_f2/distill_s1_dagger_policy.pt.
  7. FINAL: per-cell Chrono validation on the FULL 48-cell spectrum (8 drift / 6 avoid seeds,
     disjoint 'validate_fs' namespace).

New file only; imports verbatim machinery from distill_both_fullscenario + phase4_f2_train.

Usage (base env has torch; ChronoWorkerClient spawns the chrono env):
    PYTHONPATH=src python scripts/feasibility_audit/dagger_s1_fullscenario.py \
        --workers 16 --rounds 3 \
        --hard-cell-seeds 14 --mid-cell-seeds 6 --easy-cell-seeds 2 \
        --seed-sweep 4 \
        --out runs/feasibility_audit/phase4_f2/distill_s1_dagger_policy.pt
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
import distill_both_fullscenario as dbf  # noqa: E402  (S1 cell catalog + distill + validate, verbatim)
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"
DEFAULT_OUT = RUN_DIR / "distill_s1_dagger_policy.pt"
START_STUDENT = RUN_DIR / "distill_s1_fullscenario_policy.pt"

# The 6 MISSED cells (success<0.5 in the S1 report): high-mu base + one inward offset.
# Keyed by (cell_id) so geometry is exact.
HARD_CELL_IDS = (
    "avoid-r9.5-mu0.3625-offset+0.45",
    "avoid-r12-mu0.8125-base",
    "avoid-r16-mu0.8125-base",
    "avoid-r22-mu0.8125-base",
    "avoid-r30-mu0.8125-base",
    "avoid-r30-mu1.0375-base",
)
# The BORDERLINE high-mu cells the user named: r16-30 x mu{0.5875,0.8125}. (mu0.8125 ones are
# already HARD; the extra here are the mu0.5875 base cells at the high reveals, near 0.5.)
MID_CELL_IDS = (
    "avoid-r16-mu0.5875-base",
    "avoid-r22-mu0.5875-base",
    "avoid-r30-mu0.5875-base",
    # also pour mid budget on the mu1.0375 high-reveal cells adjacent to the worst miss
    "avoid-r16-mu1.0375-base",
    "avoid-r22-mu1.0375-base",
    "avoid-r12-mu1.0375-base",
)


def _load_student(path: Path) -> f2.AsymmetricActorCritic:
    ck = torch.load(path, map_location="cpu")
    model = f2.AsymmetricActorCritic(gated=bool(ck.get("gated", True)))
    model.load_state_dict(ck["state_dict"])
    model.eval()
    print(f"loaded START student {path.name} "
          f"(gated={ck.get('gated')}, select_avoid={ck.get('select_avoid')}, "
          f"select_drift={ck.get('select_drift')})", flush=True)
    return model


# ----------------------------------------------------------------- DAgger rollout spec set (S1 cells)


def _dagger_specs(avoid_cells: list[dict], hard_seeds: int, mid_seeds: int, easy_seeds: int,
                  round_idx: int) -> list[dict]:
    """Roll-out specs over the S1 avoid cell catalog (geometry applied), budget concentrated on
    the HARD (6 missed) + MID (borderline high-mu) cells.

    Disjoint 'dagger_s1' seed namespace keyed by round so successive rounds visit FRESH scenarios
    (DAgger needs new states). The select_fs / validate_fs namespaces are never touched.
    """
    hard = set(HARD_CELL_IDS)
    mid = set(MID_CELL_IDS)
    specs: list[dict] = []
    for ci, cell in enumerate(avoid_cells):
        cid = cell["cell_id"]
        if cid in hard:
            n, tier = hard_seeds, "hard"
        elif cid in mid:
            n, tier = mid_seeds, "mid"
        else:
            n, tier = easy_seeds, "easy"
        for i in range(n):
            seed = int(f2._seed_for("dagger_s1", round_idx, ci, i, round(cell["reveal"], 3),
                                    round(cell["mu"], 4), cell["geometry"]))
            specs.append({"cell": cell, "seed": seed, "tier": tier,
                          "scenario": dbf._avoid_scenario(cell, seed)})
    return specs


# ------------------------------------------------- DAgger episode (student drives, oracle labels)


def _dagger_episode(client: ChronoWorkerClient, model: f2.AsymmetricActorCritic, sp: dict,
                    *, relabel_pre_reveal: bool = True) -> dict:
    """Run ONE S1 avoid episode driven by the STUDENT; label visited states with the ORACLE.

    Mirrors dagger_avoid._dagger_episode (student drives, stateful oracle clocked in lock-step with
    env steps), but the scenario carries the cell's S1 geometry (offset/width via dbf._avoid_scenario)
    so the labels lie on the frozen S1 spectrum. The oracle make_avoidance_teacher(reveal,mu) reacts
    to obs -> it handles the geometry implicitly (the same oracle cleared these cells 1.0 in the
    feasibility pass).

    relabel_pre_reveal (CRITICAL for the S1 avoid-tail; MEASURED): the 5 high-mu BASE misses fail by
    speed_too_low -- the student brakes the car below 1 m/s BEFORE the obstacle is revealed, so it
    never reaches the avoidance maneuver and the STANDARD reveal-post-only DAgger collects ZERO labels
    there (can't fix it). With relabel_pre_reveal=True we collect oracle labels on EVERY finite obs72
    (pre- AND post-reveal), so the oracle teaches the student to MAINTAIN ENTRY SPEED through the
    pre-reveal segment too. The oracle keeps speed up to the reveal (it reaches the obstacle on every
    seed), so these labels are the correct on-distribution recovery target. (For the offset cell, which
    DOES reach reveal, the extra pre-reveal labels are harmless -- the oracle just tracks the lane.)
    """
    cell = sp["cell"]
    reveal, mu, seed = float(cell["reveal"]), float(cell["mu"]), int(sp["seed"])
    scenario = sp["scenario"]
    oracle = f2.make_avoidance_teacher(reveal=reveal, mu=mu).factory()

    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=seed)
    obs = np.asarray(obs, dtype=np.float32)
    info = dict(reset_reply.get("info", {}))
    bc_frames: list[np.ndarray] = []
    bc_targets: list[np.ndarray] = []
    n_pre = n_post = 0
    steps = 0
    terminated = truncated = False
    collision_any = False
    offtrack_any = False
    revealed_ever = False
    max_steps = int(scenario["max_steps"])
    while not (terminated or truncated) and steps < max_steps:
        revealed = f2._obstacle_visible(obs, info)
        revealed_ever = revealed_ever or revealed
        # collect the oracle label whenever the obs is finite AND (post-reveal OR pre-reveal-relabel).
        label_here = f2._finite_obs72(obs) and (revealed or relabel_pre_reveal
                                                or not f2.AVOIDANCE_BC_REVEAL_POST_ONLY)
        oracle_a = np.clip(np.asarray(oracle(steps, obs), dtype=np.float32), -1.0, 1.0)
        if label_here:
            bc_frames.append(obs.astype(np.float32).copy())
            bc_targets.append(oracle_a)
            if revealed:
                n_post += 1
            else:
                n_pre += 1
        action = np.clip(np.asarray(model.act(obs), dtype=np.float32), -1.0, 1.0)  # STUDENT drives
        obs, terminated, truncated, _status, info = client.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        info = dict(info)
        collision = bool(info.get("collision", False)) or \
            str(info.get("termination_reason", "")) == "obstacle_collision"
        collision_any = collision_any or collision
        offtrack_any = offtrack_any or (str(info.get("termination_reason", "")) == "off_track")
        steps += 1
    success = f2._avoidance_success(collision_any, info)
    term_reason = str(info.get("termination_reason", ""))
    comp_reason = str(info.get("completion_reason", ""))
    return {
        "cell_id": cell["cell_id"], "reveal": reveal, "mu": mu, "seed": seed, "tier": sp["tier"],
        "success": bool(success), "collision": bool(collision_any), "offtrack": bool(offtrack_any),
        "revealed_ever": bool(revealed_ever), "n_pre": int(n_pre), "n_post": int(n_post),
        "termination_reason": term_reason, "completion_reason": comp_reason, "steps": int(steps),
        "bc_frames": np.stack(bc_frames).astype(np.float32) if bc_frames else np.zeros((0, f2.HUMAN_VIEW_OBS_DIM), np.float32),
        "bc_targets": np.stack(bc_targets).astype(np.float32) if bc_targets else np.zeros((0, f2.ACT_DIM), np.float32),
    }


def collect_dagger(clients: list[ChronoWorkerClient], specs: list[dict],
                   model: f2.AsymmetricActorCritic, *, relabel_pre_reveal: bool = True) -> dict:
    """W-way parallel DAgger roll-outs; pool (student-obs72 -> oracle action) recovery labels.

    Returns per-failure-mode + per-hard-cell rollout success (the trend the user asked for), plus
    pre/post-reveal label counts and a never-revealed (pre-reveal stall) count.
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
            results[i] = _dagger_episode(client, model, specs[i], relabel_pre_reveal=relabel_pre_reveal)

    t0 = time.time()
    if n_workers > 0:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for fut in [ex.submit(_worker, w) for w in range(n_workers)]:
                fut.result()
    dt = time.time() - t0

    frames, targets = [], []
    n_succ = n_coll = n_off = n_other = 0
    n_pre = n_post = n_never_revealed = 0
    per_cell: dict[str, dict] = {}
    other_reasons: dict[str, int] = {}
    for res in results:
        if res is None:
            continue
        if res["bc_frames"].shape[0] > 0:
            frames.append(res["bc_frames"])
            targets.append(res["bc_targets"])
        n_pre += int(res["n_pre"]); n_post += int(res["n_post"])
        if not res["revealed_ever"]:
            n_never_revealed += 1
        agg = per_cell.setdefault(res["cell_id"], {"n": 0, "succ": 0, "tier": res["tier"]})
        agg["n"] += 1
        if res["success"]:
            n_succ += 1
            agg["succ"] += 1
        else:
            if res["collision"]:
                n_coll += 1
            elif res["offtrack"]:
                n_off += 1
            else:
                n_other += 1
                tok = f"term={res['termination_reason'] or '-'}|comp={res['completion_reason'] or '-'}"
                other_reasons[tok] = other_reasons.get(tok, 0) + 1
    obs = np.concatenate(frames, 0) if frames else np.zeros((0, f2.HUMAN_VIEW_OBS_DIM), np.float32)
    act = np.concatenate(targets, 0) if targets else np.zeros((0, f2.ACT_DIM), np.float32)
    n_fail = len(specs) - n_succ
    print(f"  [DAGGER roll-out] {len(specs)} student episodes: {n_succ} success / {n_fail} fail "
          f"(off_track={n_off}, collision={n_coll}, other={n_other}); "
          f"{obs.shape[0]} recovery labels (pre-reveal={n_pre}, post-reveal={n_post}); "
          f"{n_never_revealed} eps stalled BEFORE reveal; {dt:.1f}s", flush=True)
    if other_reasons:
        print("    'other' fail tokens: " + ", ".join(f"{k}->{v}" for k, v in
              sorted(other_reasons.items(), key=lambda kv: -kv[1])), flush=True)
    # hard/mid-cell rollout trend
    hard_lines = []
    for cid in HARD_CELL_IDS + MID_CELL_IDS:
        if cid in per_cell:
            a = per_cell[cid]
            hard_lines.append(f"{cid}={a['succ']}/{a['n']}")
    print("    hard/mid-cell rollout: " + " ".join(hard_lines), flush=True)
    return {
        "obs": obs, "act": act, "n_episodes": len(specs),
        "n_success": n_succ, "n_offtrack": n_off, "n_collision": n_coll, "n_other_fail": n_other,
        "n_pre_reveal_labels": n_pre, "n_post_reveal_labels": n_post,
        "n_stalled_before_reveal": n_never_revealed,
        "per_cell": per_cell, "other_reasons": other_reasons,
    }


# ----------------------------------------------------------------- re-distill on augmented avoid demos


def _redistill_select(clients, drift_cells, avoid_cells, drift_demo: dict, avoid_demo: dict, *,
                      epochs: int, lr: float, batch: int, holdout_frac: float, seed0: int,
                      seed_sweep: int, sel_drift_seeds: int, sel_avoid_seeds: int):
    """dbf.distill seed sweep + dbf.validate_per_cell Chrono select on the augmented avoid pool.

    drift_demo is the UNCHANGED frozen drift demo dict. Selection maximizes total cleared then
    drift (dbf._select_score). Returns (best, per_seed) where per_seed records each seed's drift
    so we can flag any drift regression.
    """
    sel_specs = dbf._val_specs(drift_cells, avoid_cells, n_drift=sel_drift_seeds,
                               n_avoid=sel_avoid_seeds, namespace="select_fs")
    best = None  # (score, state, stats, seed, sel_rows)
    per_seed = []
    for s in range(seed0, seed0 + max(1, int(seed_sweep))):
        print(f"\n  --- re-distill seed {s} ---", flush=True)
        m, st = dbf.distill(drift_demo, avoid_demo, epochs=epochs, lr=lr, batch=batch,
                            holdout_frac=holdout_frac, seed=s)
        sel_rows = dbf.validate_per_cell(clients, m, sel_specs, label=f"SELECT seed{s}")
        score = dbf._select_score(sel_rows)
        dr = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "drift"]))
        av = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "avoidance"]))
        dr_cleared = sum(1 for r in sel_rows if r["regime"] == "drift" and r["success"] >= 0.5)
        av_cleared = sum(1 for r in sel_rows if r["regime"] == "avoidance" and r["success"] >= 0.5)
        print(f"  seed {s} CHRONO SELECT: avoid={av:.3f} ({av_cleared}/36) "
              f"drift={dr:.3f} ({dr_cleared}/12) score={score[0]:.3f}", flush=True)
        st["select_avoid"] = av; st["select_drift"] = dr; st["distill_seed"] = s
        per_seed.append({"seed": s, "select_avoid": av, "select_drift": dr,
                         "avoid_cleared": av_cleared, "drift_cleared": dr_cleared})
        if best is None or score > best[0]:
            best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel_rows)
    return best, per_seed


def main() -> None:
    ap = argparse.ArgumentParser(description="S1 full-scenario DAgger for the avoid head (drift frozen).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--start", type=str, default=str(START_STUDENT))
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    # base demos (frozen drift + base avoid oracle, same defaults as distill_both_fullscenario)
    ap.add_argument("--drift-seeds-per-cell", type=int, default=6)
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=5)
    # DAgger rollout budget (concentrate on the hard/mid cells)
    ap.add_argument("--hard-cell-seeds", type=int, default=14, help="rollout seeds per HARD (missed) cell / round")
    ap.add_argument("--mid-cell-seeds", type=int, default=6, help="rollout seeds per BORDERLINE cell / round")
    ap.add_argument("--easy-cell-seeds", type=int, default=2, help="rollout seeds per other cell / round (anchor)")
    ap.add_argument("--no-pre-reveal-relabel", action="store_true",
                    help="disable pre-reveal oracle relabeling (default ON: needed for the speed_too_low "
                         "stall misses where the student never reaches the reveal).")
    # re-distill
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=4)
    ap.add_argument("--select-drift-seeds", type=int, default=3)
    ap.add_argument("--select-avoid-seeds", type=int, default=3)
    # FINAL per-cell validation
    ap.add_argument("--val-drift-seeds", type=int, default=8)
    ap.add_argument("--val-avoid-seeds", type=int, default=6)
    ap.add_argument("--report", type=str, default=str(RUN_DIR / "distill_s1_dagger_report.json"))
    args = ap.parse_args()

    drift_cells = dbf._load_drift_cells()
    avoid_cells = dbf._load_avoid_cells()
    print(f"S1 spectrum: {len(drift_cells)} drift + {len(avoid_cells)} avoid cells", flush=True)
    print(f"HARD (6 missed) cells: {HARD_CELL_IDS}", flush=True)
    print(f"MID (borderline) cells: {MID_CELL_IDS}", flush=True)

    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"dagger_s1_w{w}_stderr.log", read_timeout_s=600.0)
               for w in range(args.workers)]
    history: list[dict] = []
    drift_demo = None
    best_overall = None  # (score, state, stats, seed, round, sel_rows)
    try:
        # --- FROZEN drift demos: collected ONCE (e4 drift teacher); reused every round ---
        drift_specs = dbf._drift_demo_specs(drift_cells, args.drift_seeds_per_cell)
        drift_demo = dbf.collect_demos(clients, drift_specs, label="DRIFT(frozen)")
        if drift_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: drift collected 0 frames.")

        # --- BASE avoid oracle demos (the original S1 avoid demos -- kept across DAgger) ---
        avoid_specs = dbf._avoid_demo_specs(avoid_cells, args.avoid_seeds_per_cell)
        base_avoid = dbf.collect_demos(clients, avoid_specs, label="AVOID-oracle(base)")
        if base_avoid["obs"].shape[0] == 0:
            raise SystemExit("FATAL: base avoid collected 0 frames.")
        base_n = int(base_avoid["obs"].shape[0])
        avoid_obs = base_avoid["obs"].copy()
        avoid_act = base_avoid["act"].copy()

        student = _load_student(Path(args.start))

        for r in range(int(args.rounds)):
            print(f"\n========================= DAgger-S1 ROUND {r} =========================", flush=True)
            specs = _dagger_specs(avoid_cells, args.hard_cell_seeds, args.mid_cell_seeds,
                                  args.easy_cell_seeds, r)
            n_hard = sum(1 for s in specs if s["tier"] == "hard")
            n_mid = sum(1 for s in specs if s["tier"] == "mid")
            print(f"  roll-out: {len(specs)} episodes ({n_hard} hard @ {args.hard_cell_seeds}/cell, "
                  f"{n_mid} mid @ {args.mid_cell_seeds}/cell, rest @ {args.easy_cell_seeds}/cell); "
                  f"pre-reveal-relabel={not args.no_pre_reveal_relabel}", flush=True)
            dag = collect_dagger(clients, specs, student,
                                 relabel_pre_reveal=not args.no_pre_reveal_relabel)
            if dag["obs"].shape[0] > 0:
                avoid_obs = np.concatenate([avoid_obs, dag["obs"]], 0)
                avoid_act = np.concatenate([avoid_act, dag["act"]], 0)
            aug_avoid = {"obs": avoid_obs, "act": avoid_act,
                         "n_episodes": base_avoid["n_episodes"], "n_success": base_avoid["n_success"]}
            print(f"  AUGMENTED avoid pool: {avoid_obs.shape[0]} frames "
                  f"(base {base_n} + DAgger {avoid_obs.shape[0]-base_n})", flush=True)

            best, per_seed = _redistill_select(
                clients, drift_cells, avoid_cells, drift_demo, aug_avoid,
                epochs=args.epochs, lr=args.lr, batch=args.batch, holdout_frac=args.holdout_frac,
                seed0=args.seed, seed_sweep=args.seed_sweep,
                sel_drift_seeds=args.select_drift_seeds, sel_avoid_seeds=args.select_avoid_seeds)
            score, state, stats, win_seed, sel_rows = best
            drift_regressed = [ps for ps in per_seed if ps["select_drift"] < 0.999]
            if drift_regressed:
                print(f"  !! WARNING: drift<1.000 on seeds "
                      f"{[(ps['seed'], ps['select_drift']) for ps in drift_regressed]}", flush=True)
            sel_dr = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "drift"]))
            sel_av = float(np.mean([r["success"] for r in sel_rows if r["regime"] == "avoidance"]))
            print(f"\n  ROUND {r} SELECTED seed {win_seed}: select avoid={sel_av:.3f} drift={sel_dr:.3f}", flush=True)

            # next round rolls out THIS round's selected student
            student = f2.AsymmetricActorCritic(gated=True)
            student.load_state_dict(state)
            student.eval()

            history.append({
                "round": r, "select_avoid": sel_av, "select_drift": sel_dr, "win_seed": int(win_seed),
                "aug_avoid_frames": int(avoid_obs.shape[0]), "base_avoid_frames": int(base_n),
                "dagger_round_labels": int(dag["obs"].shape[0]),
                "dagger_pre_reveal_labels": int(dag["n_pre_reveal_labels"]),
                "dagger_post_reveal_labels": int(dag["n_post_reveal_labels"]),
                "dagger_stalled_before_reveal": int(dag["n_stalled_before_reveal"]),
                "dagger_rollout_success": int(dag["n_success"]),
                "dagger_rollout_offtrack": int(dag["n_offtrack"]),
                "dagger_rollout_collision": int(dag["n_collision"]),
                "dagger_rollout_other_fail": int(dag["n_other_fail"]),
                "dagger_rollout_episodes": int(dag["n_episodes"]),
                "hard_mid_cell_rollout": {cid: dag["per_cell"][cid] for cid in
                                          (HARD_CELL_IDS + MID_CELL_IDS) if cid in dag["per_cell"]},
                "per_seed": per_seed,
                "drift_all_seeds_1000": bool(not drift_regressed),
            })
            if best_overall is None or score > best_overall[0]:
                best_overall = (score, {k: v.clone() for k, v in state.items()}, stats, win_seed, r, sel_rows)

        score, best_state, best_stats, best_seed, best_round, _ = best_overall
        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best_state)

        # save BEFORE final validation (durable if validation interrupted)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": model.state_dict(), "gated": True,
            "label": "distill_s1_dagger_avoid",
            "drift_teacher": "tuned_DriftFeedbackPolicy_specs_for(frozen)",
            "avoid_teacher": "make_avoidance_teacher_oracle+DAgger(S1 hard/mid focus)",
            "select_avoid": float(best_stats["select_avoid"]), "select_drift": float(best_stats["select_drift"]),
            "best_round": int(best_round), "best_seed": int(best_seed),
            "start_from": str(args.start),
            "drift_demo_frames": int(drift_demo["obs"].shape[0]),
            "avoid_demo_frames_final": int(avoid_obs.shape[0]), "base_avoid_frames": int(base_n),
            "hard_cell_ids": list(HARD_CELL_IDS), "mid_cell_ids": list(MID_CELL_IDS),
            "dagger_history": history,
            **best_stats,
        }, out)
        print(f"\nsaved DAgger-S1 student -> {out}", flush=True)

        # ===================== FINAL per-cell Chrono validation (FULL 48-cell spectrum) =====================
        print(f"\n=== FINAL PER-CELL CHRONO VALIDATION ({args.val_drift_seeds} drift / "
              f"{args.val_avoid_seeds} avoid seeds per cell) ===", flush=True)
        val_specs = dbf._val_specs(drift_cells, avoid_cells, n_drift=args.val_drift_seeds,
                                   n_avoid=args.val_avoid_seeds, namespace="validate_fs")
        val_rows = dbf.validate_per_cell(clients, model, val_specs, label="VALIDATE")
    finally:
        for c in clients:
            c.close()

    drift_rows = sorted([r for r in val_rows if r["regime"] == "drift"], key=lambda r: (r["mu"], r["beta"]))
    avoid_rows = sorted([r for r in val_rows if r["regime"] == "avoidance"],
                        key=lambda r: (r["reveal"], r["mu"], r["geometry"]))

    print("\n=== PER-CELL DRIFT VALIDATION (12 cells) ===", flush=True)
    print(f"  {'cell':26s} {'spec':18s} {'succ':>8s} {'mean_sus':>9s}", flush=True)
    for r in drift_rows:
        cleared = "OK" if r["success"] >= 0.5 else "MISS"
        print(f"  {r['cell_id']:26s} {r['spec']:18s} {r['n_succ']}/{r['n']}={r['success']:.2f} "
              f"{r['mean_sustain']:9.1f}  {cleared}", flush=True)

    print("\n=== PER-CELL AVOID VALIDATION (36 cells) ===", flush=True)
    print(f"  {'cell':42s} {'succ':>8s}", flush=True)
    miss_now, hard_now = [], {}
    for r in avoid_rows:
        cleared = "OK" if r["success"] >= 0.5 else "MISS"
        tag = "  [was-MISS]" if r["cell_id"] in HARD_CELL_IDS else ""
        print(f"  {r['cell_id']:42s} {r['n_succ']}/{r['n']}={r['success']:.2f}  {cleared}{tag}", flush=True)
        if r["success"] < 0.5:
            miss_now.append(r["cell_id"])
        if r["cell_id"] in HARD_CELL_IDS:
            hard_now[r["cell_id"]] = (r["n_succ"], r["n"], r["success"])

    n_drift = len(drift_rows); n_avoid = len(avoid_rows)
    drift_cleared = sum(1 for r in drift_rows if r["success"] >= 0.5)
    avoid_cleared = sum(1 for r in avoid_rows if r["success"] >= 0.5)
    total_cleared = drift_cleared + avoid_cleared
    n_hard_now_cleared = sum(1 for cid in HARD_CELL_IDS if hard_now.get(cid, (0, 1, 0))[2] >= 0.5)

    print("\n=== HEADLINE: S1 DAGGER ===", flush=True)
    print(f"  cells cleared (success>=0.5): {total_cleared}/{n_drift+n_avoid} "
          f"(drift {drift_cleared}/{n_drift}, avoid {avoid_cleared}/{n_avoid})", flush=True)
    print(f"  PREVIOUSLY-MISSED cells now cleared: {n_hard_now_cleared}/6", flush=True)
    for cid in HARD_CELL_IDS:
        s, n, su = hard_now.get(cid, (0, 0, 0.0))
        print(f"    {cid:42s} {s}/{n}={su:.2f}  {'CLEARED' if su >= 0.5 else 'STILL-MISS'}", flush=True)
    print(f"  DRIFT stays 12/12: {drift_cleared == 12}", flush=True)
    if miss_now:
        print(f"  STILL-MISSING avoid cells: {miss_now}", flush=True)

    report = {
        "protocol": "dagger_s1_fullscenario",
        "policy_path": str(Path(args.out)),
        "start_from": str(args.start),
        "best_round": best_round, "best_seed": best_seed,
        "validation": {"val_drift_seeds": args.val_drift_seeds, "val_avoid_seeds": args.val_avoid_seeds,
                       "drift_cells": drift_rows, "avoid_cells": avoid_rows},
        "headline": {
            "total_cells": n_drift + n_avoid, "total_cleared": total_cleared,
            "drift_cleared": drift_cleared, "avoid_cleared": avoid_cleared,
            "prev_missed_now_cleared": n_hard_now_cleared, "prev_missed_total": len(HARD_CELL_IDS),
            "still_missing": miss_now, "drift_stays_12": bool(drift_cleared == 12),
        },
        "dagger_history": history,
    }
    Path(args.report).write_text(json.dumps(report, indent=2, default=float))
    print(f"\nwrote report -> {args.report}", flush=True)


if __name__ == "__main__":
    main()
