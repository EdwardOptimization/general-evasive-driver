"""Self-ID degradation pipeline G1 ignition gate (pre-registered, infrastructure only).

Purpose
-------

M3214 closes the loop on the D1 observation-degradation pipeline integration:
every training/evaluation/gate entry point now constructs envs through
``autodrift.observation_degradation_wrapper.make_env_from_config``. Before any
full-budget cell of the pre-registered 20-cell matrix
(docs/selfid-completion-experiment-design-2026-06.md) is funded, this script
answers ONE infrastructure question at minutes scale:

    Does the delay-25 task condition produce a measurable outcome-distribution
    difference against the wrapped-clean condition when the degradation runs
    through the real, integrated training -> checkpoint -> evaluation chain?

This is an IGNITION gate for spending the full matrix budget. It is NOT a
scientific experiment: the per-seed budget here (65,536 steps) is ~13% of the
pre-registered 500k floor, and M1199/M1497 established that short-budget
numbers must never be read as profile rankings, gate validity, information
ceilings, dose-response shapes, or self-identification evidence at any level.
``self_id_evidence_discipline.claim_level`` for this gate: ``not_applicable``.

Pre-registered design (frozen BEFORE the run; also echoed into summary.json)
----------------------------------------------------------------------------

Conditions (both constructed through the wrapper so the construction path is
identical; the clean cell is the T1 wrapped-clean cell of the matrix):

    clean     observation_degradation = {delay_steps: 0,  noise_std: 0.0}
    delay_25  observation_degradation = {delay_steps: 25, noise_std: 0.0}

Budget and seeds (fixed):

    base config            configs/selfid_positive_control_p0_smoke.json
                           (obs72 P0 contract, online_gru, M1207-lineage
                           emergency-avoidance env block)
    training seeds         [710001, 710002, 710003, 710004]  (N=4 per condition)
    training steps         65,536 per seed, num_envs=16, sync vector env,
                           device=cpu, OMP_NUM_THREADS=1, 8 concurrent jobs
    evaluation             200 fresh episodes per run, evaluated in the run's
                           OWN condition (task-family contract), shared eval
                           seed list = eval_seed_base + [0..199],
                           eval_seed_base = 7,700,000 (disjoint from training)
    no condition-specific tuning; identical optimizer/rollout/env count.

G1 verdict criteria (frozen; no post-hoc weakening permitted):

    For each metric in {success_rate, clearance_margin_p10} compute the
    seed-paired deltas  d_i = metric(delay_25, seed_i) - metric(clean, seed_i),
    i = 1..4, where success_rate = mean(outcome_bucket == 'success_obstacle_pass')
    and clearance_margin_p10 = nan-aware 10th percentile of episode
    min_clearance_margin over the 200 eval episodes.

    Bootstrap: B = 20,000 resamples (with replacement, size 4) of the paired
    deltas, deterministic numpy seed 20260611; 95% percentile CI = [2.5%, 97.5%].

    G1 PASS  iff  the 95% CI of the success_rate paired deltas excludes 0
             OR   the 95% CI of the clearance_margin_p10 paired deltas excludes 0.

    G1 FAIL  means the degradation axis does not measurably bite episode
             outcomes through the integrated pipeline at ignition budget.
             Pre-registered routing (Outcome B/D analogue of the design doc):
             the full 20-cell matrix is CANCELLED and the task design goes
             back to the drawing board; thresholds are not weakened and the
             budget is not silently extended.

Auxiliary readout (reported, NOT part of the verdict): action-level policy
divergence. For each seed pair, the clean-policy observation stream (4 probe
episodes, seeds 7,800,000..7,800,003, <=200 steps, recorded in the wrapped-clean
env) is replayed open-loop into both checkpoints (deterministic actions) and
the mean L2 action distance is reported, alongside a clean-vs-clean different
seed baseline on the same streams.

Execution health (exit code semantics):

    exit 0   every training/eval link executed, metrics finite where required,
             and a verdict (pass OR fail) was recorded deterministically.
    exit 1   any training/eval subprocess failed, a checkpoint or episodes.csv
             is missing/short, or a required metric is non-finite. No verdict.

Outputs:

    <output-dir>/summary.json       pre-registered criteria + per-seed table +
                                    bootstrap CIs + verdict + health block
    <output-dir>/g1_run_rows.csv    one row per (condition, seed) run
    <output-dir>/runs/...           per-run train/eval artifacts

Usage:

    PYTHONPATH=src OMP_NUM_THREADS=1 python \
        scripts/feasibility_audit/selfid_g1_ignition_gate.py \
        --output-dir runs/feasibility_audit/selfid_g1_ignition_gate

Budget overrides exist for plumbing smoke only; any override flips
``budget_is_preregistered`` to false in summary.json and the run must not be
used for the M3214 verdict.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import pandas as pd  # noqa: E402
import torch  # noqa: E402

from autodrift.checkpoints import load_actor_critic_checkpoint  # noqa: E402
from autodrift.config import build_env_config  # noqa: E402
from autodrift.observation_degradation_wrapper import make_env_from_config  # noqa: E402

BASE_CONFIG_PATH = REPO_ROOT / "configs" / "selfid_positive_control_p0_smoke.json"


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)

# ---- pre-registered constants (frozen before the run) ----------------------
PREREGISTERED_TRAIN_STEPS = 65536
PREREGISTERED_EVAL_EPISODES = 200
PREREGISTERED_TRAIN_SEEDS = (710001, 710002, 710003, 710004)
PREREGISTERED_EVAL_SEED_BASE = 7_700_000
PREREGISTERED_NUM_ENVS = 16
PREREGISTERED_BOOTSTRAP_RESAMPLES = 20000
PREREGISTERED_BOOTSTRAP_SEED = 20260611
PREREGISTERED_CONDITIONS = {
    "clean": {"delay_steps": 0, "noise_std": 0.0},
    "delay_25": {"delay_steps": 25, "noise_std": 0.0},
}
PROBE_SEEDS = (7_800_000, 7_800_001, 7_800_002, 7_800_003)
PROBE_MAX_STEPS = 200

PREREGISTERED_CRITERIA_TEXT = (
    "G1 PASS iff the 95% percentile bootstrap CI (B=20000, numpy seed 20260611) of the "
    "seed-paired deltas delay_25-minus-clean excludes 0 for success_rate OR for "
    "clearance_margin_p10 (4 training seeds, 200 shared-seed eval episodes per run, "
    "65536 training steps per seed). G1 FAIL routes to the pre-registered Outcome B/D "
    "analogue: cancel the full 20-cell matrix and return to task design; no threshold "
    "weakening, no budget extension, no scientific reading of any number at this budget."
)


@dataclass
class RunSpec:
    condition: str
    train_seed: int
    config_path: Path
    run_dir: Path
    checkpoint_path: Path
    eval_dir: Path


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    return env


def build_cell_config(base_raw: dict[str, Any], condition: str, train_seed: int, train_steps: int) -> dict[str, Any]:
    env_block = json.loads(json.dumps(base_raw["env"]))
    ppo_block = json.loads(json.dumps(base_raw["ppo"]))
    env_block["observation_degradation"] = dict(PREREGISTERED_CONDITIONS[condition])
    ppo_block.update(
        {
            "seed": int(train_seed),
            "total_steps": int(train_steps),
            "num_envs": PREREGISTERED_NUM_ENVS,
            "vector_env_mode": "sync",
            "device": "cpu",
            "eval_episodes": 1,
        }
    )
    return {
        "selfid_g1": {
            "role": "g1_ignition_gate_cell",
            "condition": condition,
            "train_seed": int(train_seed),
            "claim_level": "not_applicable",
            "note": "throwaway diagnostic training; checkpoint must never be promoted or reused as a parent",
        },
        "env": env_block,
        "ppo": ppo_block,
    }


def run_training(spec: RunSpec) -> dict[str, Any]:
    spec.run_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "autodrift.train_ppo",
        "--config",
        str(spec.config_path),
        "--run-dir",
        str(spec.run_dir),
        "--save",
        str(spec.checkpoint_path),
        "--device",
        "cpu",
        "--eval-episodes",
        "1",
    ]
    start = time.perf_counter()
    result = subprocess.run(command, cwd=REPO_ROOT, env=_child_env(), capture_output=True, text=True)
    wall = time.perf_counter() - start
    (spec.run_dir / "train_stdout.log").write_text(result.stdout, encoding="utf-8")
    (spec.run_dir / "train_stderr.log").write_text(result.stderr, encoding="utf-8")
    return {
        "returncode": int(result.returncode),
        "wall_s": round(wall, 2),
        "checkpoint_exists": spec.checkpoint_path.exists(),
    }


def run_evaluation(spec: RunSpec, eval_episodes: int, eval_seed_base: int) -> dict[str, Any]:
    spec.eval_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "autodrift.evaluate",
        "--policy",
        "checkpoint",
        "--checkpoint",
        str(spec.checkpoint_path),
        "--episodes",
        str(int(eval_episodes)),
        "--seed",
        str(int(eval_seed_base)),
        "--device",
        "cpu",
        "--run-dir",
        str(spec.eval_dir),
    ]
    start = time.perf_counter()
    result = subprocess.run(command, cwd=REPO_ROOT, env=_child_env(), capture_output=True, text=True)
    wall = time.perf_counter() - start
    (spec.eval_dir / "eval_stdout.log").write_text(result.stdout, encoding="utf-8")
    (spec.eval_dir / "eval_stderr.log").write_text(result.stderr, encoding="utf-8")
    return {
        "returncode": int(result.returncode),
        "wall_s": round(wall, 2),
        "episodes_csv_exists": (spec.eval_dir / "episodes.csv").exists(),
    }


def metrics_from_episodes(episodes_csv: Path) -> dict[str, Any]:
    frame = pd.read_csv(episodes_csv)
    margins = frame["min_clearance_margin"].to_numpy(dtype=np.float64)
    finite_margins = margins[np.isfinite(margins)]
    return {
        "episodes": int(len(frame)),
        "success_rate": float((frame["outcome_bucket"] == "success_obstacle_pass").mean()),
        "collision_rate": float(frame["collision"].astype(bool).mean()),
        "offtrack_rate": float((frame["termination_reason"] == "off_road").mean()),
        "clearance_margin_p10": (
            float(np.percentile(finite_margins, 10.0)) if finite_margins.size else float("nan")
        ),
        "clearance_margin_mean": float(np.mean(finite_margins)) if finite_margins.size else float("nan"),
        "clearance_margin_nan_episodes": int(np.sum(~np.isfinite(margins))),
        "return_mean": float(frame["return"].mean()),
        "steps_mean": float(frame["steps"].mean()),
    }


def paired_bootstrap_ci(deltas: np.ndarray, resamples: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = deltas.shape[0]
    indices = rng.integers(0, n, size=(resamples, n))
    means = deltas[indices].mean(axis=1)
    return {
        "mean": float(deltas.mean()),
        "ci_low": float(np.percentile(means, 2.5)),
        "ci_high": float(np.percentile(means, 97.5)),
    }


def ci_excludes_zero(ci: dict[str, float]) -> bool:
    return bool(ci["ci_low"] > 0.0 or ci["ci_high"] < 0.0)


def collect_probe_streams(base_raw: dict[str, Any], clean_checkpoints: list[Path]) -> list[list[np.ndarray]]:
    """Record clean-condition observation streams driven by the seed-matched clean policy."""

    env_block = json.loads(json.dumps(base_raw["env"]))
    env_block["observation_degradation"] = dict(PREREGISTERED_CONDITIONS["clean"])
    env_config = build_env_config(env_block)
    streams: list[list[np.ndarray]] = []
    for pair_index, probe_seed in enumerate(PROBE_SEEDS):
        model, _ = load_actor_critic_checkpoint(clean_checkpoints[pair_index % len(clean_checkpoints)], device="cpu")
        env = make_env_from_config(env_config)
        obs, _ = env.reset(seed=int(probe_seed))
        stream = [np.asarray(obs, dtype=np.float32).copy()]
        hidden = None
        for _ in range(PROBE_MAX_STEPS):
            action, _, _, hidden = model.act_recurrent(stream[-1], hidden, deterministic=True)
            obs, _, terminated, truncated, _ = env.step(action)
            stream.append(np.asarray(obs, dtype=np.float32).copy())
            if terminated or truncated:
                break
        streams.append(stream)
    return streams


def open_loop_actions(model: Any, stream: list[np.ndarray]) -> np.ndarray:
    hidden = None
    actions = []
    for obs in stream:
        action, _, _, hidden = model.act_recurrent(obs, hidden, deterministic=True)
        actions.append(action)
    return np.asarray(actions, dtype=np.float32)


def action_divergence_probe(
    base_raw: dict[str, Any],
    train_seeds: list[int],
    checkpoints: dict[tuple[str, int], Path],
) -> dict[str, Any]:
    torch.set_num_threads(1)
    clean_ckpts = [checkpoints[("clean", seed)] for seed in train_seeds]
    streams = collect_probe_streams(base_raw, clean_ckpts)
    rows = []
    for index, seed in enumerate(train_seeds):
        clean_model, _ = load_actor_critic_checkpoint(checkpoints[("clean", seed)], device="cpu")
        delay_model, _ = load_actor_critic_checkpoint(checkpoints[("delay_25", seed)], device="cpu")
        other_seed = train_seeds[(index + 1) % len(train_seeds)]
        other_clean_model, _ = load_actor_critic_checkpoint(checkpoints[("clean", other_seed)], device="cpu")
        cross_distances = []
        baseline_distances = []
        first_action_distances = []
        for stream in streams:
            clean_actions = open_loop_actions(clean_model, stream)
            delay_actions = open_loop_actions(delay_model, stream)
            other_actions = open_loop_actions(other_clean_model, stream)
            cross = np.linalg.norm(clean_actions - delay_actions, axis=1)
            baseline = np.linalg.norm(clean_actions - other_actions, axis=1)
            cross_distances.append(float(cross.mean()))
            baseline_distances.append(float(baseline.mean()))
            first_action_distances.append(float(cross[0]))
        rows.append(
            {
                "train_seed": int(seed),
                "mean_action_l2_clean_vs_delay25": float(np.mean(cross_distances)),
                "mean_action_l2_clean_vs_other_clean_seed": float(np.mean(baseline_distances)),
                "mean_first_action_l2_clean_vs_delay25": float(np.mean(first_action_distances)),
            }
        )
    return {
        "note": (
            "auxiliary readout only, NOT part of the G1 verdict; deterministic actions on "
            "identical clean-stream observations replayed open loop into both checkpoints; "
            "baseline column is clean vs a different clean training seed on the same streams"
        ),
        "probe_seeds": list(PROBE_SEEDS),
        "probe_max_steps": PROBE_MAX_STEPS,
        "per_seed": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=Path("runs/feasibility_audit/selfid_g1_ignition_gate"))
    parser.add_argument("--train-steps", type=int, default=PREREGISTERED_TRAIN_STEPS)
    parser.add_argument("--eval-episodes", type=int, default=PREREGISTERED_EVAL_EPISODES)
    parser.add_argument("--train-seeds", type=str, default=",".join(str(s) for s in PREREGISTERED_TRAIN_SEEDS))
    parser.add_argument("--eval-seed-base", type=int, default=PREREGISTERED_EVAL_SEED_BASE)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--skip-probe", action="store_true", help="plumbing smoke only")
    args = parser.parse_args()

    train_seeds = [int(token) for token in args.train_seeds.split(",") if token.strip()]
    budget_is_preregistered = (
        args.train_steps == PREREGISTERED_TRAIN_STEPS
        and args.eval_episodes == PREREGISTERED_EVAL_EPISODES
        and tuple(train_seeds) == PREREGISTERED_TRAIN_SEEDS
        and args.eval_seed_base == PREREGISTERED_EVAL_SEED_BASE
        and not args.skip_probe
    )

    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    configs_dir = output_dir / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)

    base_raw = json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))

    specs: list[RunSpec] = []
    for condition in PREREGISTERED_CONDITIONS:
        for seed in train_seeds:
            run_dir = output_dir / "runs" / f"{condition}_seed{seed}"
            config_path = configs_dir / f"{condition}_seed{seed}.json"
            config_path.write_text(
                json.dumps(build_cell_config(base_raw, condition, seed, args.train_steps), indent=2) + "\n",
                encoding="utf-8",
            )
            specs.append(
                RunSpec(
                    condition=condition,
                    train_seed=seed,
                    config_path=config_path,
                    run_dir=run_dir,
                    checkpoint_path=run_dir / "checkpoint.pt",
                    eval_dir=run_dir / "eval",
                )
            )

    health: dict[str, Any] = {"train_failures": [], "eval_failures": [], "non_finite_metrics": []}

    train_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        train_results = list(pool.map(run_training, specs))
    train_wall = time.perf_counter() - train_start
    for spec, result in zip(specs, train_results):
        if result["returncode"] != 0 or not result["checkpoint_exists"]:
            health["train_failures"].append(f"{spec.condition}_seed{spec.train_seed}: {result}")

    if health["train_failures"]:
        summary = {
            "run_type": "selfid_g1_ignition_gate",
            "status": "execution_failed",
            "health": health,
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 1

    eval_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        eval_results = list(
            pool.map(lambda spec: run_evaluation(spec, args.eval_episodes, args.eval_seed_base), specs)
        )
    eval_wall = time.perf_counter() - eval_start
    for spec, result in zip(specs, eval_results):
        if result["returncode"] != 0 or not result["episodes_csv_exists"]:
            health["eval_failures"].append(f"{spec.condition}_seed{spec.train_seed}: {result}")

    if health["eval_failures"]:
        summary = {
            "run_type": "selfid_g1_ignition_gate",
            "status": "execution_failed",
            "health": health,
        }
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 1

    run_rows: list[dict[str, Any]] = []
    metrics_by_run: dict[tuple[str, int], dict[str, Any]] = {}
    for spec, train_result, eval_result in zip(specs, train_results, eval_results):
        metrics = metrics_from_episodes(spec.eval_dir / "episodes.csv")
        metrics_by_run[(spec.condition, spec.train_seed)] = metrics
        if metrics["episodes"] != args.eval_episodes:
            health["eval_failures"].append(
                f"{spec.condition}_seed{spec.train_seed}: expected {args.eval_episodes} episodes, "
                f"got {metrics['episodes']}"
            )
        for key in ("success_rate", "collision_rate", "offtrack_rate", "clearance_margin_p10", "return_mean"):
            if not np.isfinite(metrics[key]):
                health["non_finite_metrics"].append(f"{spec.condition}_seed{spec.train_seed}: {key}")
        run_rows.append(
            {
                "condition": spec.condition,
                "train_seed": spec.train_seed,
                "train_steps": args.train_steps,
                "train_returncode": train_result["returncode"],
                "train_wall_s": train_result["wall_s"],
                "eval_episodes": metrics["episodes"],
                "eval_wall_s": eval_result["wall_s"],
                "success_rate": metrics["success_rate"],
                "collision_rate": metrics["collision_rate"],
                "offtrack_rate": metrics["offtrack_rate"],
                "clearance_margin_p10": metrics["clearance_margin_p10"],
                "clearance_margin_mean": metrics["clearance_margin_mean"],
                "clearance_margin_nan_episodes": metrics["clearance_margin_nan_episodes"],
                "return_mean": metrics["return_mean"],
                "steps_mean": metrics["steps_mean"],
                "checkpoint": _repo_relative(spec.checkpoint_path),
            }
        )

    rows_path = output_dir / "g1_run_rows.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(run_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(run_rows)

    execution_ok = not (health["train_failures"] or health["eval_failures"] or health["non_finite_metrics"])

    deltas: dict[str, list[float]] = {"success_rate": [], "clearance_margin_p10": []}
    for seed in train_seeds:
        for metric in deltas:
            deltas[metric].append(
                metrics_by_run[("delay_25", seed)][metric] - metrics_by_run[("clean", seed)][metric]
            )

    bootstrap: dict[str, Any] = {}
    for metric, values in deltas.items():
        array = np.asarray(values, dtype=np.float64)
        ci = paired_bootstrap_ci(array, PREREGISTERED_BOOTSTRAP_RESAMPLES, PREREGISTERED_BOOTSTRAP_SEED)
        bootstrap[metric] = {
            "paired_deltas_delay25_minus_clean": [float(v) for v in array],
            "sign_counts": {
                "negative": int(np.sum(array < 0)),
                "zero": int(np.sum(array == 0)),
                "positive": int(np.sum(array > 0)),
            },
            **ci,
            "ci_excludes_zero": ci_excludes_zero(ci),
        }

    g1_pass = bool(
        bootstrap["success_rate"]["ci_excludes_zero"]
        or bootstrap["clearance_margin_p10"]["ci_excludes_zero"]
    )

    probe = None
    if not args.skip_probe:
        checkpoints = {(spec.condition, spec.train_seed): spec.checkpoint_path for spec in specs}
        probe = action_divergence_probe(base_raw, train_seeds, checkpoints)

    summary = {
        "run_type": "selfid_g1_ignition_gate",
        "stage": "infrastructure_ignition_gate_minutes_scale_only",
        "claim_level": "not_applicable",
        "no_scientific_conclusion": True,
        "budget_is_preregistered": budget_is_preregistered,
        "preregistered_criteria": PREREGISTERED_CRITERIA_TEXT,
        "preregistered_design": {
            "base_config": _repo_relative(BASE_CONFIG_PATH),
            "conditions": PREREGISTERED_CONDITIONS,
            "train_seeds": train_seeds,
            "train_steps_per_seed": args.train_steps,
            "num_envs": PREREGISTERED_NUM_ENVS,
            "vector_env_mode": "sync",
            "device": "cpu",
            "omp_num_threads": 1,
            "eval_episodes_per_run": args.eval_episodes,
            "eval_seed_base": args.eval_seed_base,
            "eval_seeds_shared_across_runs": True,
            "bootstrap_resamples": PREREGISTERED_BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": PREREGISTERED_BOOTSTRAP_SEED,
        },
        "status": "completed" if execution_ok else "execution_failed",
        "health": health,
        "wall_seconds": {
            "training_total": round(train_wall, 2),
            "evaluation_total": round(eval_wall, 2),
            "aggregate_train_env_steps_per_s": round(len(specs) * args.train_steps / train_wall, 1),
        },
        "per_run_metrics": run_rows,
        "paired_bootstrap": bootstrap,
        "g1_verdict": "pass" if g1_pass else "fail",
        "g1_verdict_meaning": {
            "pass": (
                "the degradation axis measurably changes outcome distributions through the "
                "integrated pipeline; the remaining repair-list items and a FRESH full-budget "
                "pre-registration may proceed (no scientific claim from these numbers)"
            ),
            "fail": (
                "degradation does not bite outcomes at ignition budget; per pre-registration "
                "the full 20-cell matrix is cancelled and the task design is reworked "
                "(Outcome B/D routing); thresholds must not be weakened"
            ),
        },
        "claim_boundary": (
            "Infrastructure ignition evidence only. Auxiliary diagnostic branch; the active-safety "
            "driver objective boundary is unchanged. No profile ranking, no gate validity, no "
            "information ceiling, no dose-response shape, no driver-performance, no validation, "
            "no promotion, and no self-identification claim at any level."
        ),
        "action_divergence_probe": probe,
        "artifacts": {
            "summary_json": _repo_relative(output_dir / "summary.json"),
            "run_rows_csv": _repo_relative(rows_path),
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("status", "g1_verdict", "budget_is_preregistered", "wall_seconds")}, indent=2))
    print(f"summary={output_dir / 'summary.json'}")
    return 0 if execution_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
