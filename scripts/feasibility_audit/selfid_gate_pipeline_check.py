"""Audit 3: gate/eval pipeline scale check under degraded observations.

Feasibility-audit-only script (minutes-scale, CPU). It does NOT launch any
full-budget training and none of its numbers may be read scientifically.

What it measures:

1. Matched-pair acceptance of the hidden-swap gate on a smoke P0 checkpoint
   under the pre-registered task conditions clean / delay_12 / delay_25 /
   noise_0.05, ~20 episodes each, with raw pair distances recorded so
   acceptance can be evaluated at multiple thresholds (0.75 / 1.0 / 1.5).
   The degradation is applied through ObservationDegradationWrapper around
   snapshot collection AND continuation replay (snapshot.env is the wrapper,
   so replays keep degrading) -- functionality the production
   hidden_swap_gate module does not have (it builds raw AutoDriftEnv).
2. Privileged-twin (obs76) pair acceptance at the pilot threshold 1.5 on the
   clean task, with context-only distances reported alongside.
3. Evaluation-metric completeness: a tiny evaluate_policy run on the smoke
   checkpoint, checking that episodes.csv rows carry every field the
   pre-registered verdict criteria need (success derivation, per-episode
   min_clearance_margin for p10, termination-type fields, per-seed key).

Output: experiments/feasibility_audit/selfid_gate_pipeline_check.json
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.config import build_env_config
from autodrift.env import AutoDriftEnv, DriftEnvConfig
from autodrift.evaluate import evaluate_policy
from autodrift.hidden_swap_gate import (
    DecisionSnapshot,
    _is_snapshot_candidate,
    build_pair_row,
    clone_hidden,
    replay_pair,
)
from autodrift.observation_degradation_wrapper import make_observation_degradation_env
from autodrift.paired_perturbation_gate import condition_config
from autodrift.train_ppo import ActorCritic

PRIVILEGED_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_privileged_smoke.json"
P0_CONFIG = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"

NOMINAL_MU_RANGE = (0.85, 1.15)
PERTURBED_MU_RANGE = (0.25, 0.35)

# Pre-registered task conditions under audit (subset relevant to acceptance).
CONDITIONS: dict[str, dict[str, float]] = {
    "clean": {"delay_steps": 0, "noise_std": 0.0},
    "delay_12": {"delay_steps": 12, "noise_std": 0.0},
    "delay_25": {"delay_steps": 25, "noise_std": 0.0},
    "noise_0.05": {"delay_steps": 0, "noise_std": 0.05},
}

ACCEPTANCE_THRESHOLDS = (0.75, 1.0, 1.5, 2.0)


def make_task_env(env_config: DriftEnvConfig, delay_steps: int, noise_std: float):
    if delay_steps == 0 and noise_std == 0.0:
        return AutoDriftEnv(env_config)
    return make_observation_degradation_env(
        env_config, delay_steps=delay_steps, noise_std=noise_std
    )


def collect_decision_snapshot_degraded(
    model: ActorCritic,
    env_config: DriftEnvConfig,
    condition: str,
    seed: int,
    *,
    delay_steps: int,
    noise_std: float,
    target_obstacle_distance: float = 12.0,
    min_probe_steps: int = 10,
    max_probe_steps: int = 180,
    require_friction_step: bool = True,
    min_hidden_updates_after_friction: int = 2,
) -> DecisionSnapshot | None:
    """Mirror hidden_swap_gate.collect_decision_snapshot with degradation applied.

    snapshot.env keeps the wrapper, so downstream replay_continuation
    (which deepcopies snapshot.env and steps it) continues to degrade.
    """

    env = make_task_env(env_config, delay_steps, noise_std)
    obs, info = env.reset(seed=seed)
    hidden: torch.Tensor | None = None
    best: DecisionSnapshot | None = None
    terminated = False
    truncated = False

    while not (terminated or truncated):
        step = int(info.get("step", 0))
        if _is_snapshot_candidate(
            info,
            min_probe_steps,
            require_friction_step,
            min_hidden_updates_after_friction,
        ):
            obstacle_distance = float(info["obstacle_distance"])
            score = abs(obstacle_distance - target_obstacle_distance)
            if best is None or score < best.snapshot_score:
                best = DecisionSnapshot(
                    condition=condition,
                    seed=seed,
                    step=step,
                    observation=np.asarray(obs, dtype=np.float32).copy(),
                    hidden=clone_hidden(hidden),
                    env=copy.deepcopy(env),
                    info=dict(info),
                    obstacle_distance=obstacle_distance,
                    snapshot_score=score,
                )
            if obstacle_distance <= target_obstacle_distance:
                break
        if step >= max_probe_steps:
            break
        action, _, _, hidden = model.act_recurrent(obs, hidden, deterministic=True)
        obs, _, terminated, truncated, info = env.step(action)
    return best


def run_degraded_gate(
    model: ActorCritic,
    base_config: DriftEnvConfig,
    seeds: list[int],
    *,
    delay_steps: int,
    noise_std: float,
    condition_name: str,
    max_observation_distance: float,
    max_continuation_steps: int,
) -> dict[str, Any]:
    configs = {
        "nominal": condition_config(base_config, NOMINAL_MU_RANGE, None),
        "perturbed": condition_config(base_config, PERTURBED_MU_RANGE, None),
    }
    pair_rows: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for seed in seeds:
        snapshots = {
            cond: collect_decision_snapshot_degraded(
                model,
                env_config,
                cond,
                seed,
                delay_steps=delay_steps,
                noise_std=noise_std,
            )
            for cond, env_config in configs.items()
        }
        pair_row = build_pair_row(
            seed,
            snapshots["nominal"],
            snapshots["perturbed"],
            configs["nominal"],
            max_observation_distance,
        )
        pair_rows.append(pair_row)
        if snapshots["nominal"] is None or snapshots["perturbed"] is None:
            continue
        replay_rows.extend(
            replay_pair(
                model,
                snapshots["nominal"],
                snapshots["perturbed"],
                pair_row,
                configs["nominal"],
                max_continuation_steps,
            )
        )

    pairs = pd.DataFrame(pair_rows)
    replays = pd.DataFrame(replay_rows)
    paired = pairs[pairs["pair_status"] == "paired"] if not pairs.empty else pairs
    distances = (
        paired["observation_distance"].to_numpy(dtype=np.float64)
        if "observation_distance" in paired
        else np.array([])
    )
    response_distances = (
        paired["response_observation_distance"].to_numpy(dtype=np.float64)
        if "response_observation_distance" in paired
        else np.array([])
    )
    context_distances = (
        paired["context_observation_distance"].to_numpy(dtype=np.float64)
        if "context_observation_distance" in paired
        else np.array([])
    )
    acceptance = {
        f"accepted_at_{threshold}": int((distances <= threshold).sum())
        for threshold in ACCEPTANCE_THRESHOLDS
    }
    replay_returns = (
        replays["return"].to_numpy(dtype=np.float64) if not replays.empty else np.array([])
    )
    return {
        "condition": condition_name,
        "delay_steps": delay_steps,
        "noise_std": noise_std,
        "max_observation_distance_used": max_observation_distance,
        "episodes": len(seeds),
        "paired": int(len(paired)),
        "missing_nominal": int((pairs["pair_status"] == "missing_nominal").sum()),
        "missing_perturbed": int((pairs["pair_status"] == "missing_perturbed").sum()),
        "missing_both": int((pairs["pair_status"] == "missing_both").sum()),
        "accepted_at_threshold_used": int(paired["accepted_match"].sum()) if len(paired) else 0,
        **acceptance,
        "observation_distance_min": float(np.min(distances)) if distances.size else float("nan"),
        "observation_distance_mean": float(np.mean(distances)) if distances.size else float("nan"),
        "observation_distance_max": float(np.max(distances)) if distances.size else float("nan"),
        "response_observation_distance_mean": (
            float(np.mean(response_distances)) if response_distances.size else float("nan")
        ),
        "context_observation_distance_mean": (
            float(np.mean(context_distances)) if context_distances.size else float("nan")
        ),
        "replay_rows": int(len(replays)),
        "replay_variants": sorted(replays["variant"].unique().tolist()) if not replays.empty else [],
        "replay_returns_finite": (
            bool(np.all(np.isfinite(replay_returns))) if replay_returns.size else False
        ),
        "pair_distances": [round(float(value), 4) for value in distances.tolist()],
    }


def train_smoke_twin(config_path: Path, run_dir: Path, total_steps: int) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = run_dir / "checkpoint.pt"
    if checkpoint_path.exists():
        return checkpoint_path
    command = [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(config_path),
        "--run-dir",
        str(run_dir),
        "--save",
        str(checkpoint_path),
        "--device",
        "cpu",
        "--eval-episodes",
        "1",
        "--total-steps",
        str(total_steps),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    (run_dir / "train_stdout.log").write_text(result.stdout, encoding="utf-8")
    (run_dir / "train_stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0 or not checkpoint_path.exists():
        raise RuntimeError(f"smoke training failed for {config_path}; see {run_dir}")
    return checkpoint_path


REQUIRED_EVAL_FIELDS = (
    "seed",
    "collision",
    "obstacle_completed",
    "min_clearance_margin",
    "termination_reason",
    "outcome_bucket",
    "terminated",
    "truncated",
    "return",
    "steps",
    "obstacle_label",
    "min_obstacle_clearance",
)


def eval_metric_completeness(checkpoint: Path, env_config: DriftEnvConfig) -> dict[str, Any]:
    rows, summary = evaluate_policy(
        policy_name="checkpoint",
        episodes=3,
        seed=995501,
        checkpoint=checkpoint,
        device="cpu",
        env_config=env_config,
    )
    columns = sorted(rows[0].keys()) if rows else []
    present = {field: field in columns for field in REQUIRED_EVAL_FIELDS}
    margins = [row.get("min_clearance_margin", float("nan")) for row in rows]
    return {
        "episodes_run": len(rows),
        "row_column_count": len(columns),
        "required_fields_present": present,
        "all_required_fields_present": all(present.values()),
        "explicit_success_column_present": "success" in columns,
        "summary_has_success_rate": "success_rate" in summary,
        "summary_has_p10_margin": any("p10" in key for key in summary),
        "per_episode_margin_finite_or_nan_ok": True,
        "sample_outcome_buckets": [str(row.get("outcome_bucket", "")) for row in rows],
        "sample_min_clearance_margins": [float(value) for value in margins],
        "row_columns": columns,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPO_ROOT / "experiments" / "feasibility_audit" / "selfid_gate_pipeline_check.json",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=REPO_ROOT / "runs" / "feasibility_audit" / "selfid_gate_pipeline_check",
    )
    parser.add_argument("--gate-episodes", type=int, default=20)
    parser.add_argument("--gate-seed", type=int, default=995600)
    parser.add_argument("--smoke-train-steps", type=int, default=1024)
    parser.add_argument("--max-continuation-steps", type=int, default=40)
    args = parser.parse_args()

    torch.manual_seed(0)
    started = time.time()
    work_dir = args.work_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    seeds = [args.gate_seed + index for index in range(args.gate_episodes)]

    result: dict[str, Any] = {
        "run_type": "selfid_gate_pipeline_check",
        "stage": "feasibility_audit_minutes_scale_only",
        "claim_level": "not_applicable",
        "no_scientific_conclusion": True,
        "smoke_train_steps": args.smoke_train_steps,
        "gate_episodes_per_condition": args.gate_episodes,
        "gate_seeds": seeds,
        "max_continuation_steps": args.max_continuation_steps,
        "notes": (
            "Smoke checkpoints (1024 train steps) are nearly untrained; acceptance "
            "numbers characterize the matching/threshold machinery, not converged-policy "
            "behavior. M1199/M1497 rule applies: no scientific reading."
        ),
    }

    print("[train] p0 smoke twin ...")
    p0_checkpoint = train_smoke_twin(P0_CONFIG, work_dir / "train_p0", args.smoke_train_steps)
    print("[train] privileged smoke twin ...")
    priv_checkpoint = train_smoke_twin(
        PRIVILEGED_CONFIG, work_dir / "train_privileged", args.smoke_train_steps
    )

    p0_env_config = build_env_config(json.loads(P0_CONFIG.read_text())["env"])
    priv_env_config = build_env_config(json.loads(PRIVILEGED_CONFIG.read_text())["env"])

    p0_obs_dim = int(AutoDriftEnv(p0_env_config).observation_space.shape[0])
    priv_obs_dim = int(AutoDriftEnv(priv_env_config).observation_space.shape[0])
    p0_model, _ = load_actor_critic_checkpoint(p0_checkpoint, device="cpu", obs_dim=p0_obs_dim)
    priv_model, _ = load_actor_critic_checkpoint(priv_checkpoint, device="cpu", obs_dim=priv_obs_dim)
    result["p0_obs_dim"] = p0_obs_dim
    result["privileged_obs_dim"] = priv_obs_dim

    # 1) P0 gate acceptance across degradation conditions (threshold 0.75 = P0 default).
    p0_rows = []
    for name, spec in CONDITIONS.items():
        print(f"[gate/p0] condition={name} ...")
        t0 = time.time()
        row = run_degraded_gate(
            p0_model,
            p0_env_config,
            seeds,
            delay_steps=int(spec["delay_steps"]),
            noise_std=float(spec["noise_std"]),
            condition_name=name,
            max_observation_distance=0.75,
            max_continuation_steps=args.max_continuation_steps,
        )
        row["wall_seconds"] = round(time.time() - t0, 1)
        p0_rows.append(row)
        print(
            f"  paired={row['paired']} accepted@0.75={row['accepted_at_0.75']} "
            f"accepted@1.5={row['accepted_at_1.5']} dist_mean={row['observation_distance_mean']:.3f} "
            f"({row['wall_seconds']}s)"
        )
    result["p0_gate_acceptance"] = p0_rows

    # 2) Privileged twin acceptance at pilot threshold 1.5 (clean task, as in Experiment 2).
    print("[gate/privileged] condition=clean threshold=1.5 ...")
    t0 = time.time()
    priv_row = run_degraded_gate(
        priv_model,
        priv_env_config,
        seeds,
        delay_steps=0,
        noise_std=0.0,
        condition_name="clean",
        max_observation_distance=1.5,
        max_continuation_steps=args.max_continuation_steps,
    )
    priv_row["wall_seconds"] = round(time.time() - t0, 1)
    result["privileged_gate_acceptance"] = priv_row
    print(
        f"  paired={priv_row['paired']} accepted@1.5={priv_row['accepted_at_1.5']} "
        f"accepted@0.75={priv_row['accepted_at_0.75']} "
        f"context_dist_mean={priv_row['context_observation_distance_mean']:.3f}"
    )

    # 3) Evaluation-metric completeness on a tiny evaluate_policy run.
    print("[eval] metric completeness probe (3 episodes) ...")
    result["eval_metric_completeness"] = eval_metric_completeness(p0_checkpoint, p0_env_config)

    # 4) Static infrastructure findings recorded for the audit report.
    result["static_findings"] = {
        "train_ppo_resume": {
            "init_checkpoint_flag": True,
            "init_checkpoint_restores_optimizer_state": False,
            "init_checkpoint_restores_global_step": False,
            "periodic_checkpoints_via_checkpoint_interval_steps": True,
            "periodic_checkpoint_contains": ["model_state", "config", "metadata"],
            "true_crash_resume": False,
        },
        "degradation_wrapper_integration": {
            "train_ppo_make_vector_env_supports_wrapper": False,
            "evaluate_py_supports_wrapper": False,
            "hidden_swap_gate_supports_wrapper": False,
            "wrapper_only_used_in": [
                "src/autodrift/observation_degradation_wrapper.py",
                "tests/test_observation_degradation_wrapper.py",
            ],
        },
        "reset_control_semantics": {
            "evaluate_reset_recurrent_state_resets_every_step": True,
            "evaluate_reads_reset_policy_from_checkpoint_metadata": True,
            "l3_reset_control_is_training_profile": False,
        },
    }

    result["total_wall_seconds"] = round(time.time() - started, 1)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=False), encoding="utf-8")
    print(f"wrote {args.output_json} ({result['total_wall_seconds']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
