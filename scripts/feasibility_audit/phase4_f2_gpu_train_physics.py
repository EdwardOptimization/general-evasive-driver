"""Phase-4 F2 GPU PPO training on the FAITHFUL PHYSICS env (``gpu_physics_pwr``).

A thin variant of ``phase4_f2_gpu_train.py``: it REUSES that harness's entire training
machinery — BC warm-start (``collect_bc_demos``), the GPU rollout (``collect_rollout``),
GAE/PPO/BC (``compute_gae``/``ppo_update``/``bc_update`` via the CPU trainer), the
ramped-drift-sustain re-pricing, the NaN mask, the per-regime advantage norm, the eval
loop, and the config presets — and ONLY swaps the environment from the grey-box
``GPUAutoDriftEnv`` to the collision-faithful ``GPUPhysicsAutoDriftEnv``.

WHY: A5 showed avoid=1.0 on the grey-box was an artifact (grey-box collision bal-acc 0.503
= chance — it is BLIND to collisions, so any policy "passes"). The PWR-TMeasy physics
rewrite is collision-better (0.695) and lateral-faithful: it is the surrogate that can
actually POSE the avoidance challenge. Training on it is the honest test of whether the
full-scenario driver still learns drift (it should — drift is faithful) and whether
avoidance is now a NON-TRIVIAL challenge (avoid_succ should NOT trivially saturate at 1.0).

The ``GPUPhysicsAutoDriftEnv`` is a drop-in for ``GPUAutoDriftEnv`` (same reset/step/
success/.priv6/.scenario_type/.done API), so the imported rollout/BC/eval functions, which
only touch that public API, work UNCHANGED. The only env-construction difference is here:
``build_env`` returns the physics env.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_gpu_train_physics.py --smoke \\
        --save-policy runs/feasibility_audit/phase4_f2/gpu_physics_policy_seed0.pt
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_gpu_train_physics.py --full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.gpu_env_physics import GPUPhysicsAutoDriftEnv  # noqa: E402

# Reuse the ENTIRE grey-box GPU harness (BC / rollout / GAE / PPO / eval / configs / train).
import phase4_f2_gpu_train as g  # noqa: E402
from phase4_f2_gpu_train import (  # noqa: E402
    smoke_config,
    full_config,
    train,
)


def build_env(device: torch.device, *, sigma_scale: float = 0.165) -> GPUPhysicsAutoDriftEnv:
    """Construct the collision-faithful physics env (drop-in for GPUAutoDriftEnv)."""
    return GPUPhysicsAutoDriftEnv(device=device, dtype=torch.float32, sigma_scale=sigma_scale)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="GPU PPO trainer for the F2 gated actor-critic on the FAITHFUL PHYSICS env.")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--smoke", action="store_true", help="short learning-curve smoke run")
    grp.add_argument("--full", action="store_true", help="full multi-update training run")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-envs", type=int, default=None)
    ap.add_argument("--ppo-updates", type=int, default=None)
    ap.add_argument("--sigma-scale", type=float, default=0.165)
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--out", type=str, default=None, help="optional JSON path for the learning curve")
    ap.add_argument("--save-policy", type=str, default=None,
                    help="optional .pt path to save the trained actor-critic state_dict")
    args = ap.parse_args()

    device = torch.device(args.device if (args.device != "cuda" or torch.cuda.is_available()) else "cpu")
    if device.type != "cuda":
        print(f"WARNING: CUDA unavailable, running on {device} (slow).", flush=True)

    if args.full:
        cfg = full_config(args.seed, n_envs=args.n_envs or 8192)
    else:
        cfg = smoke_config(args.seed, n_envs=args.n_envs or 4096)
    if args.ppo_updates is not None:
        cfg.ppo_updates = int(args.ppo_updates)
    cfg.label = f"physics-{cfg.label}"

    env = build_env(device, sigma_scale=args.sigma_scale)
    print(
        f"=== GPU F2 PHYSICS train [{cfg.label}] seed={cfg.seed} n_envs={cfg.n_envs} "
        f"ppo_updates={cfg.ppo_updates} horizon={cfg.rollout_horizon} sigma_scale={args.sigma_scale} "
        f"device={device} ===",
        flush=True,
    )
    result = train(cfg, device=device, env=env, verbose=True)
    model = result.pop("model", None)
    if args.save_policy and model is not None:
        sp = Path(args.save_policy); sp.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "gated": bool(getattr(model, "gated", True)),
                    "seed": cfg.seed, "label": cfg.label, "env": "gpu_physics_pwr",
                    "sigma_scale": float(args.sigma_scale),
                    "final_drift_succ": result["final_drift_succ"],
                    "final_avoid_succ": result["final_avoid_succ"]}, sp)
        print(f"saved trained actor-critic -> {sp}", flush=True)

    print("\n=== SUMMARY (PHYSICS env) ===", flush=True)
    print(json.dumps({k: v for k, v in result.items() if k != "curve"}, indent=2, default=str), flush=True)
    print(f"\nBC baseline drift={result['bc_baseline_drift_succ']:.3f} -> "
          f"final drift={result['final_drift_succ']:.3f} "
          f"(avoid {result['bc_baseline_avoid_succ']:.3f} -> {result['final_avoid_succ']:.3f})", flush=True)
    print(f"mean update wall={result['mean_update_wall_s']*1000:.0f}ms  "
          f"total wall={result['total_wall_s']:.1f}s  "
          f"rollout throughput={result['mean_rollout_throughput_steps_s']/1e6:.2f}M steps/s", flush=True)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"wrote learning curve -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
