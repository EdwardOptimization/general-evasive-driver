"""Per-cell A5 forensics for the DAgger student: WHERE and WHY the residual avoid failures are.

Read-only. Reuses a5_chrono_validate.build_items (the EXACT frozen A5 grid -- 40 avoid + 20 drift on
the 'validation' seed namespace) and runs the student per episode, recording success + the final
termination/completion tokens. So the 4 residual avoid failures get named (off_track vs collision vs
speed_too_low) and located (which reveal x mu cells), to diagnose what's left after DAgger.

Usage: PYTHONPATH=src python scripts/feasibility_audit/dagger_a5_breakdown.py \
    --policy runs/feasibility_audit/phase4_f2/distill_dagger_policy.pt --workers 16
"""
from __future__ import annotations

import argparse
import sys
import threading
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
import a5_chrono_validate as a5  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402

RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f2"


def _run_one(client, model, it):
    """Run one A5 episode with the student; return success + final term/comp tokens."""
    scenario = it["scenario"]
    obs, reset_reply = client.reset(scenario, episode_id=str(scenario["scenario_id"]), seed=int(it["seed"]))
    obs = np.asarray(obs, dtype=np.float32)
    info = dict(reset_reply.get("info", {}))
    steps = 0
    terminated = truncated = False
    collision_any = False
    max_steps = int(scenario["max_steps"])
    while not (terminated or truncated) and steps < max_steps:
        action = np.clip(np.asarray(model.act(obs), dtype=np.float32), -1.0, 1.0)
        obs, terminated, truncated, _status, info = client.step(action)
        obs = np.asarray(obs, dtype=np.float32)
        info = dict(info)
        collision_any = collision_any or (bool(info.get("collision", False))
                                          or str(info.get("termination_reason", "")) == "obstacle_collision")
        steps += 1
    if it["regime"] == "avoidance":
        success = f2._avoidance_success(collision_any, info)
    else:
        # drift success uses the longest-controlled-run criterion; we only need the pass/fail here,
        # which _student_task_eval already confirmed (drift=1.000). Recompute a cheap proxy: not needed.
        success = None
    return {
        "regime": it["regime"], "reveal": float(it["reveal"]), "mu": float(it["mu"]), "seed": int(it["seed"]),
        "success": success, "collision": bool(collision_any),
        "termination_reason": str(info.get("termination_reason", "")),
        "completion_reason": str(info.get("completion_reason", "")),
        "steps": int(steps),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(RUN_DIR / "distill_dagger_policy.pt"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--avoid-units", type=int, default=40)
    args = ap.parse_args()

    ck = torch.load(args.policy, map_location="cpu")
    model = f2.AsymmetricActorCritic(gated=bool(ck.get("gated", True)))
    model.load_state_dict(ck["state_dict"])
    model.eval()
    print(f"loaded {Path(args.policy).name}", flush=True)

    items = [it for it in a5.build_items(args.avoid_units, 0) if it["regime"] == "avoidance"]
    print(f"A5 avoid grid: {len(items)} episodes", flush=True)

    clients = [ChronoWorkerClient(stderr_log=RUN_DIR / f"a5bd_w{w}_stderr.log") for w in range(args.workers)]
    results = [None] * len(items)
    next_i = 0
    lock = threading.Lock()

    def _worker(wi):
        nonlocal next_i
        c = clients[wi]
        while True:
            with lock:
                if next_i >= len(items):
                    return
                i = next_i; next_i += 1
            results[i] = _run_one(c, model, items[i])

    try:
        with ThreadPoolExecutor(max_workers=min(args.workers, len(items))) as ex:
            for fut in [ex.submit(_worker, w) for w in range(min(args.workers, len(items)))]:
                fut.result()
    finally:
        for c in clients:
            c.close()

    n_succ = sum(1 for r in results if r["success"])
    print(f"\n=== A5 AVOID per-cell breakdown ===  {n_succ}/{len(items)} success ({n_succ/len(items):.3f})", flush=True)
    print("FAILURES:", flush=True)
    fails = [r for r in results if not r["success"]]
    if not fails:
        print("  (none)", flush=True)
    for r in sorted(fails, key=lambda r: (r["reveal"], r["mu"])):
        mode = "collision" if r["collision"] else (
            r["termination_reason"] or r["completion_reason"] or "unknown")
        print(f"  reveal={r['reveal']:>5} mu={r['mu']:.4f} seed={r['seed']}: "
              f"FAIL ({mode}; term={r['termination_reason'] or '-'} comp={r['completion_reason'] or '-'} "
              f"steps={r['steps']})", flush=True)
    # aggregate by failure mode
    modes = {}
    for r in fails:
        m = "collision" if r["collision"] else (r["termination_reason"] or "comp:" + (r["completion_reason"] or "-"))
        modes[m] = modes.get(m, 0) + 1
    print("\nfailure-mode tally: " + (", ".join(f"{k}->{v}" for k, v in modes.items()) or "(none)"), flush=True)
    # per-cell success map
    print("\nper-cell success (reveal x mu):", flush=True)
    by_cell = {}
    for r in results:
        by_cell.setdefault((r["reveal"], r["mu"]), []).append(1 if r["success"] else 0)
    for (rv, mu), v in sorted(by_cell.items()):
        print(f"  reveal={rv:>5} mu={mu:.4f}: {sum(v)}/{len(v)}", flush=True)


if __name__ == "__main__":
    main()
