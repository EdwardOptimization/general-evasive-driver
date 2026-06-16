"""A5 — the decisive avoid-fix arbiter: validate the GPU-surrogate-trained policy back on CHRONO.

The GPU PPO smoke train hit drift=1.000 / avoid=1.000 on the SURROGATE. But the surrogate's
avoidance fidelity at the collision boundary is untested, so avoid=1.000 cannot be trusted. Here we
load the trained actor-critic and run it on real Chrono over the SAME frozen validation grid the
CPU four-arm verdict used (avoidance reveal×mu grid on the disjoint validation seed namespace; drift
on E4's frozen validation seeds), via the existing run_episode / _student_task_eval machinery.

The number that matters: does the policy's CHRONO avoid success hold near the surrogate's 1.000, or
collapse toward (or below) the CPU canonical 0.700 — i.e. was the surrogate avoid an artifact?

Usage: python a5_chrono_validate.py --policy <pt> [--avoid-units 40] [--drift-units 20] [--workers 16]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "feasibility_audit"))
sys.path.insert(0, str(ROOT / "src"))

import phase4_f2_train as f2  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402


def load_model(policy_path: Path):
    ckpt = torch.load(policy_path, map_location="cpu")
    gated = bool(ckpt.get("gated", True))
    model = f2.AsymmetricActorCritic(gated=gated)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    print(f"loaded policy {policy_path.name} (gated={gated}, seed={ckpt.get('seed')}, "
          f"surrogate final drift={ckpt.get('final_drift_succ')}, avoid={ckpt.get('final_avoid_succ')})")
    return model


def build_items(avoid_units: int, drift_units: int):
    """Mirror evaluate_arms' frozen validation grid (phase4_f2_train.py:2305-2339)."""
    grid = f2._avoidance_grid(quick=False)
    drift_seeds = list(f2._e4_drift_validation_seeds(f2.DRIFT_CELL_ID))
    items = []
    for unit in range(avoid_units):
        reveal, mu = grid[unit % len(grid)]
        f2._EVAL_MU_REGISTRY[round(float(reveal), 6)] = float(mu)  # single-threaded populate
        seed = f2._seed_for("validation", "avoidance", unit, round(reveal, 4), round(mu, 4))
        items.append({"regime": "avoidance", "reveal": float(reveal), "mu": float(mu), "seed": int(seed),
                      "scenario": f2._avoidance_scenario(seed, max_steps=285, reveal=float(reveal), mu=float(mu))})
    for unit in range(min(drift_units, len(drift_seeds))):
        mu = float(f2._drift_cell()["mu"])
        seed = int(drift_seeds[unit])
        items.append({"regime": "drift", "reveal": 0.0, "mu": mu, "seed": seed,
                      "scenario": f2._drift_scenario(seed, max_steps=f2.DRIFT_VALIDATION_MAX_STEPS, difficulty="hard")})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--avoid-units", type=int, default=40)
    ap.add_argument("--drift-units", type=int, default=20)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    model = load_model(Path(args.policy))
    items = build_items(args.avoid_units, args.drift_units)
    n_av = sum(1 for it in items if it["regime"] == "avoidance")
    n_dr = sum(1 for it in items if it["regime"] == "drift")
    print(f"Chrono validation: {n_av} avoidance + {n_dr} drift episodes, {args.workers} workers")

    clients = [ChronoWorkerClient(stderr_log=ROOT / f"runs/feasibility_audit/phase4_f2/a5_w{w}_stderr.log")
               for w in range(args.workers)]
    try:
        rates = f2._student_task_eval(clients, items, model)
    finally:
        for c in clients:
            c.close()

    drift = rates.get("drift", float("nan"))
    avoid = rates.get("avoidance", float("nan"))
    print("\n=== A5 CHRONO VALIDATION (GPU-trained policy on real Chrono) ===")
    print(f"  drift  success (Chrono) = {drift:.3f}   [surrogate 1.000 | CPU canonical 0.856]")
    print(f"  avoid  success (Chrono) = {avoid:.3f}   [surrogate 1.000 | CPU canonical 0.700]")
    print("\nVERDICT:")
    if avoid >= 0.80:
        print(f"  avoid {avoid:.3f} >= 0.80 -> the surrogate-trained policy HOLDS avoid on Chrono. "
              f"Large-batch GPU did NOT regress avoid (vs CPU 0.700) -> the avoid-fix hypothesis is SUPPORTED.")
    elif avoid <= 0.70:
        print(f"  avoid {avoid:.3f} <= 0.70 -> avoid=1.000 was largely a SURROGATE ARTIFACT; on Chrono the "
              f"policy is at/below the CPU canonical. Sim-to-sim gap dominates -> need surrogate boundary fidelity.")
    else:
        print(f"  avoid {avoid:.3f} -> partial: better than nothing but below the surrogate's 1.000; "
              f"real sim-to-sim gap. Inspect per-cell + boundary fidelity.")


if __name__ == "__main__":
    main()
