"""Teacher-student DISTILLATION of a SINGLE policy that does BOTH drift and avoidance.

Hypothesis under test (the user's, believed correct): RL CAN do both regimes well; the
avoidance regression in the canonical pipeline is JOINT-PPO interference, not infeasibility.
Some seeds already hit drift=1.0 AND avoid=1.0. The fix: master each regime separately with a
STRONG teacher, then DISTILL both into one fresh gated actor-critic via behavior cloning, and
SKIP the interfering joint PPO entirely (pure distillation).

Teachers (both score well on Chrono):
  * DRIFT  -> the GPU-trained drift EXPERT (gpu_physics_policy_seed0.pt), a gated
              AsymmetricActorCritic that transfers to Chrono at drift=1.000. We probed it
              on Chrono: it holds controlled drift 73/90 steps (success). Its drift behaviour
              is the strong drift teacher (the weak e4 drift ORACLE is NOT used).
  * AVOID  -> make_avoidance_teacher(reveal, mu), the E2' entry-speed ORACLE, which scores
              ~0.98 in BC on Chrono.

Demos are collected on the REAL Chrono surrogate (obs72 -> teacher_action) via the frozen
phase4_f2_train.run_episode(collect="bc") machinery — the exact surrogate A5 validates on, so
there is no demo sim-to-sim gap. Drift collects every frame; avoidance collects the B2
reveal-post obs72-recoverable segment only (so no obs72-unobservable mu dependence is cloned).

We then BC-distill a FRESH gated AsymmetricActorCritic (shared trunk + actor_mean_a/b heads +
a learned gate from obs72) by minimising MSE(actor_forward(obs72), teacher_action) on the
POOLED demos. The gate self-organises to route drift vs avoidance from obs72 alone (the regime
label is NOT an actor input). NO PPO. Saved to distill_both_policy.pt for A5.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/distill_both.py \
        --workers 16 --drift-seeds 24 --avoid-seeds-per-cell 2 \
        --epochs 4000 --out runs/feasibility_audit/phase4_f2/distill_both_policy.pt
"""
from __future__ import annotations

import argparse
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
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

GPU_DRIFT_EXPERT = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2" / "gpu_physics_policy_seed0.pt"
DEFAULT_OUT = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2" / "distill_both_policy.pt"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"

# drift demos: cover E4's difficulty curriculum so the student learns the full drift map,
# not just the hardest entry; the eval/A5 drift grid uses "hard".
DRIFT_DIFFICULTIES = ("easy", "medium", "hard")
AVOID_MAX_STEPS = 285  # E2' avoidance episode length (matches A5's avoidance scenarios)


def load_drift_expert() -> f2.AsymmetricActorCritic:
    ck = torch.load(GPU_DRIFT_EXPERT, map_location="cpu")
    expert = f2.AsymmetricActorCritic(gated=bool(ck.get("gated", True)))
    expert.load_state_dict(ck["state_dict"])
    expert.eval()
    print(f"loaded GPU drift expert {GPU_DRIFT_EXPERT.name} "
          f"(gated={ck.get('gated')}, surrogate drift={ck.get('final_drift_succ')}, "
          f"avoid={ck.get('final_avoid_succ')})", flush=True)
    return expert


# ----------------------------------------------------------------- demo collection


def _drift_specs(n_seeds: int) -> list[dict]:
    """Drift demo scenarios across difficulties on a DISJOINT 'distill' seed namespace."""
    mu = float(f2._drift_cell()["mu"])
    specs = []
    for diff in DRIFT_DIFFICULTIES:
        for i in range(n_seeds):
            seed = int(f2._seed_for("distill", "drift", diff, i))
            specs.append({
                "regime": "drift", "difficulty": diff, "seed": seed, "mu": mu, "reveal": 0.0,
                "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty=diff),
            })
    return specs


def _avoid_specs(seeds_per_cell: int) -> list[dict]:
    """Avoidance demo scenarios over the full reveal×mu grid, disjoint seed namespace."""
    grid = f2._avoidance_grid(quick=False)
    specs = []
    for ci, (reveal, mu) in enumerate(grid):
        for i in range(seeds_per_cell):
            seed = int(f2._seed_for("distill", "avoidance", ci, i, round(reveal, 4), round(mu, 4)))
            specs.append({
                "regime": "avoidance", "seed": seed, "mu": float(mu), "reveal": float(reveal),
                "scenario": f2._avoidance_scenario(seed, max_steps=AVOID_MAX_STEPS, reveal=float(reveal), mu=float(mu)),
            })
    return specs


def collect_demos(clients: list[ChronoWorkerClient], specs: list[dict], expert: f2.AsymmetricActorCritic,
                  *, label: str) -> dict:
    """Run each spec's teacher episode W-way parallel; pool obs72 -> teacher_action frames.

    DRIFT teacher  = the GPU drift expert (policy = expert.act(obs)).
    AVOID teacher  = make_avoidance_teacher(reveal, mu) oracle (reveal-post frames only, B2).
    """
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
            if sp["regime"] == "drift":
                policy = lambda step, obs: expert.act(obs)  # noqa: E731 (GPU drift expert)
            else:
                policy = f2.make_avoidance_teacher(reveal=sp["reveal"], mu=sp["mu"]).factory()
            res = f2.run_episode(client, sp["scenario"], sp["regime"], policy,
                                 seed=int(sp["seed"]), mu=float(sp["mu"]), reveal=float(sp["reveal"]),
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


# ----------------------------------------------------------------- BC distillation


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

    Loss = MSE(actor_forward(obs72), teacher_action), pooled over both regimes so the SAME
    actor must reproduce both teachers; the learned gate routes drift vs avoidance from obs72.
    Reports per-regime holdout MSE.
    """
    torch.manual_seed(f2._seed_for("distill_init", seed))
    np.random.seed(f2._seed_for("distill_np", seed) % (2**32))

    (dtr_o, dtr_a), (dho_o, dho_a) = _holdout_split(drift_demo["obs"], drift_demo["act"], frac=holdout_frac, seed=seed + 1)
    (atr_o, atr_a), (aho_o, aho_a) = _holdout_split(avoid_demo["obs"], avoid_demo["act"], frac=holdout_frac, seed=seed + 2)

    # pooled training set (regime id retained only for diagnostics / weighting, NOT an actor input)
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
    # per-regime sample weight: equalise the two regimes' contribution to the loss so the
    # larger frame pool (avoidance) does not dominate the gradient (the SAME equalisation the
    # canonical per-regime advantage norm targets, applied to BC).
    n_d = max(1, int((reg_t == 1).sum())); n_a = max(1, int((reg_t == 0).sum()))
    w = torch.where(reg_t == 1, 0.5 / n_d, 0.5 / n_a).float()
    w = w / w.sum() * len(w)  # normalise to mean 1

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
            combined = d_mse + a_mse  # select the checkpoint best on BOTH holdouts
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
        # gate-routing diagnostic: on each regime's holdout obs, what does the gate select?
        # g ~ 1 => head A; g ~ 0 => head B. We only need to SEE that the two regimes get
        # routed to DIFFERENT heads (the gate discriminates regime from obs72).
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


def _chrono_select_eval(clients: list[ChronoWorkerClient], model: f2.AsymmetricActorCritic,
                        *, n_avoid: int, n_drift: int) -> dict[str, float]:
    """Small Chrono task-score eval on a DISJOINT selection namespace (avoid select-on-test).

    Mirrors the canonical pipeline's task-score model selection: distillation BC of the
    avoidance oracle is seed-sensitive (canonical BC avoid ranged 0.0..1.0 across its 16
    seeds), so we select the distilled seed by real Chrono success, NOT by holdout MSE.
    The frozen A5 validation grid is never touched here.
    """
    grid = f2._avoidance_grid(quick=False)
    items = []
    for u in range(n_avoid):
        reveal, mu = grid[u % len(grid)]
        seed = int(f2._seed_for("distill_select", "avoidance", u, round(reveal, 4), round(mu, 4)))
        items.append({"regime": "avoidance", "reveal": float(reveal), "mu": float(mu), "seed": seed,
                      "scenario": f2._avoidance_scenario(seed, max_steps=AVOID_MAX_STEPS, reveal=float(reveal), mu=float(mu))})
    for u in range(n_drift):
        mu = float(f2._drift_cell()["mu"])
        seed = int(f2._seed_for("distill_select", "drift", u))
        items.append({"regime": "drift", "reveal": 0.0, "mu": mu, "seed": seed,
                      "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    return f2._student_task_eval(clients, items, model)


def main() -> None:
    ap = argparse.ArgumentParser(description="Distill ONE policy that does BOTH drift+avoidance (no joint PPO).")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--drift-seeds", type=int, default=24, help="drift demo seeds PER difficulty (x3 difficulties)")
    ap.add_argument("--avoid-seeds-per-cell", type=int, default=2, help="avoid demo seeds per reveal×mu grid cell (x20 cells)")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--holdout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seed-sweep", type=int, default=1,
                    help="distill this many seeds from the SAME demos; select the best by Chrono task score.")
    ap.add_argument("--select-avoid-units", type=int, default=16)
    ap.add_argument("--select-drift-units", type=int, default=8)
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    expert = load_drift_expert()
    drift_specs = _drift_specs(args.drift_seeds)
    avoid_specs = _avoid_specs(args.avoid_seeds_per_cell)
    print(f"collecting demos on Chrono: {len(drift_specs)} drift + {len(avoid_specs)} avoid episodes, "
          f"{args.workers} workers", flush=True)

    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"distill_w{w}_stderr.log") for w in range(args.workers)]
    drift_demo = avoid_demo = None
    best = None  # (combined_score, model, stats, seed, select_scores)
    try:
        drift_demo = collect_demos(clients, drift_specs, expert, label="DRIFT")
        avoid_demo = collect_demos(clients, avoid_specs, expert, label="AVOID")
        if drift_demo["obs"].shape[0] == 0 or avoid_demo["obs"].shape[0] == 0:
            raise SystemExit("FATAL: a regime collected 0 demo frames; cannot distill.")

        # distill N seeds from the SAME demos; select by Chrono task score (canonical-analog).
        for s in range(args.seed, args.seed + max(1, int(args.seed_sweep))):
            print(f"\n--- distill seed {s} ---", flush=True)
            m, st = distill(drift_demo, avoid_demo, epochs=args.epochs, lr=args.lr, batch=args.batch,
                            holdout_frac=args.holdout_frac, seed=s)
            sel = _chrono_select_eval(clients, m, n_avoid=int(args.select_avoid_units), n_drift=int(args.select_drift_units))
            av, dr = float(sel.get("avoidance", 0.0)), float(sel.get("drift", 0.0))
            # selection objective: maximise avoid (the bottleneck) then drift, like the canonical
            # task score (both regimes vs floor). Tie-break on combined.
            score = (av, dr)
            print(f"  seed {s} CHRONO SELECT: avoid={av:.3f} drift={dr:.3f}", flush=True)
            st["select_avoid"] = av; st["select_drift"] = dr; st["distill_seed"] = s
            if best is None or score > best[0]:
                best = (score, {k: v.detach().clone() for k, v in m.state_dict().items()}, st, s, sel)
        model = f2.AsymmetricActorCritic(gated=True)
        model.load_state_dict(best[1])
        stats = best[2]
        print(f"\nSELECTED distilled seed {best[3]} "
              f"(Chrono select avoid={best[2]['select_avoid']:.3f} drift={best[2]['select_drift']:.3f})", flush=True)
    finally:
        for c in clients:
            c.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(), "gated": True,
        "seed": args.seed, "label": "distill_both",
        "drift_teacher": "gpu_physics_policy_seed0", "avoid_teacher": "make_avoidance_teacher_oracle",
        "drift_demo_frames": int(drift_demo["obs"].shape[0]),
        "avoid_demo_frames": int(avoid_demo["obs"].shape[0]),
        "drift_demo_episodes": int(drift_demo["n_episodes"]), "avoid_demo_episodes": int(avoid_demo["n_episodes"]),
        "drift_teacher_success": int(drift_demo["n_success"]), "avoid_teacher_success": int(avoid_demo["n_success"]),
        **stats,
    }, out)
    print(f"\nsaved distilled student -> {out}", flush=True)

    print("\n=== DISTILLATION REPORT ===", flush=True)
    print(f"  DRIFT demos: {drift_demo['obs'].shape[0]} frames from {drift_demo['n_episodes']} episodes "
          f"({drift_demo['n_success']} teacher-success)", flush=True)
    print(f"  AVOID demos: {avoid_demo['obs'].shape[0]} frames from {avoid_demo['n_episodes']} episodes "
          f"({avoid_demo['n_success']} teacher-success)", flush=True)
    print(f"  drift  holdout MSE = {stats['drift_holdout_mse']:.3e}", flush=True)
    print(f"  avoid  holdout MSE = {stats['avoid_holdout_mse']:.3e}", flush=True)
    print(f"  gate routing: drift={stats['gate_mean_drift']:.3f} avoid={stats['gate_mean_avoid']:.3f} "
          f"(separation {abs(stats['gate_mean_drift']-stats['gate_mean_avoid']):.3f})", flush=True)
    if "select_avoid" in stats:
        print(f"  SELECTED seed {stats.get('distill_seed')}  Chrono-select avoid={stats['select_avoid']:.3f} "
              f"drift={stats['select_drift']:.3f}", flush=True)
    print(f"\nNext: PYTHONPATH=src python scripts/feasibility_audit/a5_chrono_validate.py "
          f"--policy {out} --avoid-units 40 --drift-units 20 --workers 16", flush=True)


if __name__ == "__main__":
    main()
