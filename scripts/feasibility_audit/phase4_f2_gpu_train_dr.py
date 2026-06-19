"""Phase-4 F2 GPU PPO training on the DOMAIN-RANDOMIZED physics env (``gpu_env_physics_dr``).

THE DECISIVE AVOID-FIX EXPERIMENT.

A thin variant of ``phase4_f2_gpu_train_physics.py`` (which is itself a thin variant of
``phase4_f2_gpu_train.py``): it REUSES the entire training harness — BC warm-start, the GPU
rollout, GAE/PPO/BC, the ramped-drift-sustain re-pricing, the NaN mask, the per-regime
advantage norm, the eval loop, and the config presets — and ONLY swaps the environment to
the DOMAIN-RANDOMIZED physics env ``GPUPhysicsDRAutoDriftEnv``.

WHY: the physics-env-trained policy hit drift=1.0 / avoid=1.0 on the surrogate but
**avoid=0.000 on Chrono** (drift held at 1.0). That is sim-to-sim OVERFIT: the policy tuned
itself to the surrogate's exact residual dynamics — most decisively the vx / powertrain
timing — which is the dimension where the faithful rewrite still differs from Chrono.

THE FIX: train under DOMAIN RANDOMIZATION on the DYNAMICS (re-sampled per env, per episode):
mass/izz/front-share/sigma/grip/drive-scale/rolling-resistance jittered within physically
plausible ranges around the measured values, plus a small per-step body-accel process noise.
The longitudinal-timing band (drive_scale x U(0.7,1.3), rolling_resist x U(0.7,1.3)) is the
widest on purpose — it spans the Chrono operating point so the policy cannot exploit the
nominal surrogate's vx-timing and must avoid ROBUSTLY across the whole band. See
``src/autodrift/gpu_env_physics_dr.py`` for the full DR-range rationale.

EXPECTATION (healthy DR): avoid_succ on the DR env will PLATEAU LOWER than the 1.0 it hit
on the single fixed surrogate — that is the whole point: a policy robust to the band can't
also be perfectly tuned to one operating point. Drift should stay ~1.0 (the drift saddle is
friction/speed-insensitive, so DR barely touches it). The decisive number is the A5 Chrono
avoid of the resulting policy (run a5_chrono_validate.py on the saved .pt).

The DR env is a drop-in for ``GPUAutoDriftEnv`` (same public API), so the imported
rollout / BC / eval functions, which only touch that API, work UNCHANGED. The only
env-construction difference is here in ``build_env``.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f2_gpu_train_dr.py --smoke \\
        --n-envs 2048 --ppo-updates 60 \\
        --save-policy runs/feasibility_audit/phase4_f2/gpu_dr_policy_seed0.pt
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

from autodrift.gpu_env_physics_dr import GPUPhysicsDRAutoDriftEnv, DR_RANGES, ACCEL_PROCESS_NOISE  # noqa: E402

# Reuse the ENTIRE grey-box GPU harness (BC / rollout / GAE / PPO / eval / configs / train).
import phase4_f2_gpu_train as g  # noqa: E402
from phase4_f2_gpu_train import (  # noqa: E402
    smoke_config,
    full_config,
    train,
)


def build_env(
    device: torch.device, *, sigma_scale: float = 0.165,
    accel_process_noise: float = ACCEL_PROCESS_NOISE, dr_seed: int | None = None,
) -> GPUPhysicsDRAutoDriftEnv:
    """Construct the DOMAIN-RANDOMIZED physics env (drop-in for GPUAutoDriftEnv).

    ``sigma_scale`` is the NOMINAL relaxation scale the parent builds; the DR env overrides it
    per env with a fresh draw from the measured-physical band [0.10, 0.25] each reset, so this
    value is only the pre-DR default (effectively unused once DR fires)."""
    return GPUPhysicsDRAutoDriftEnv(
        device=device, dtype=torch.float32, sigma_scale=sigma_scale,
        accel_process_noise=accel_process_noise, dr_seed=dr_seed,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="GPU PPO trainer for the F2 gated actor-critic on the DOMAIN-RANDOMIZED physics env.")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--smoke", action="store_true", help="short learning-curve smoke run")
    grp.add_argument("--full", action="store_true", help="full multi-update training run")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n-envs", type=int, default=None)
    ap.add_argument("--ppo-updates", type=int, default=None)
    ap.add_argument("--sigma-scale", type=float, default=0.165)
    ap.add_argument("--accel-noise", type=float, default=ACCEL_PROCESS_NOISE,
                    help="per-step multiplicative body-accel process-noise std (default ~3%)")
    ap.add_argument("--dr-seed", type=int, default=None,
                    help="seed for the DR sampler (default: derived from --seed for reproducibility)")
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--out", type=str, default=None, help="optional JSON path for the learning curve")
    ap.add_argument("--save-policy", type=str, default=None,
                    help="optional .pt path to save the trained actor-critic state_dict (for A5)")
    args = ap.parse_args()

    device = torch.device(args.device if (args.device != "cuda" or torch.cuda.is_available()) else "cpu")
    if device.type != "cuda":
        print(f"WARNING: CUDA unavailable, running on {device} (slow).", flush=True)

    # DR needs a bit more PPO than the fixed-surrogate smoke (the brief: N>=2048, ~60 updates).
    if args.full:
        cfg = full_config(args.seed, n_envs=args.n_envs or 8192)
    else:
        cfg = smoke_config(args.seed, n_envs=args.n_envs or 2048)
        cfg.ppo_updates = 60
    if args.ppo_updates is not None:
        cfg.ppo_updates = int(args.ppo_updates)
    cfg.label = f"dr-{cfg.label}"

    dr_seed = args.dr_seed if args.dr_seed is not None else (args.seed + 7919)  # reproducible DR draws
    env = build_env(device, sigma_scale=args.sigma_scale,
                    accel_process_noise=args.accel_noise, dr_seed=dr_seed)
    print(
        f"=== GPU F2 DR-PHYSICS train [{cfg.label}] seed={cfg.seed} n_envs={cfg.n_envs} "
        f"ppo_updates={cfg.ppo_updates} horizon={cfg.rollout_horizon} sigma_scale={args.sigma_scale} "
        f"accel_noise={args.accel_noise} dr_seed={dr_seed} device={device} ===",
        flush=True,
    )
    print("DR ranges (per env, per episode reset):", flush=True)
    for k, (lo, hi) in DR_RANGES.items():
        print(f"    {k:20s} [{lo:.3f}, {hi:.3f}]", flush=True)
    print(f"    accel_process_noise   +/- {args.accel_noise:.3f} per step (mult on dvx/dvy)", flush=True)

    result = train(cfg, device=device, env=env, verbose=True)
    model = result.pop("model", None)
    if args.save_policy and model is not None:
        sp = Path(args.save_policy); sp.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "gated": bool(getattr(model, "gated", True)),
                    "seed": cfg.seed, "label": cfg.label, "env": "gpu_env_physics_dr",
                    "sigma_scale": float(args.sigma_scale),
                    "dr_ranges": DR_RANGES, "accel_process_noise": float(args.accel_noise),
                    "final_drift_succ": result["final_drift_succ"],
                    "final_avoid_succ": result["final_avoid_succ"]}, sp)
        print(f"saved trained actor-critic -> {sp}", flush=True)

    print("\n=== SUMMARY (DR-PHYSICS env) ===", flush=True)
    print(json.dumps({k: v for k, v in result.items() if k != "curve"}, indent=2, default=str), flush=True)
    print(f"\nBC baseline drift={result['bc_baseline_drift_succ']:.3f} -> "
          f"final drift={result['final_drift_succ']:.3f} "
          f"(avoid {result['bc_baseline_avoid_succ']:.3f} -> {result['final_avoid_succ']:.3f})", flush=True)
    print("NOTE: DR-env avoid is EXPECTED to plateau below 1.0 (robust, not tuned). The decisive\n"
          "      number is the A5 Chrono avoid of this saved policy.", flush=True)
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
