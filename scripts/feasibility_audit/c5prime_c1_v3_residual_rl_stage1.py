"""C1-v3 residual-RL stage-1 run on frozen C5-prime cells.

This is the first performance readout for the PI-reopened nonlocal route:
learn a bounded residual on top of the frozen v4 reflex, then judge it against
the frozen A3 v4_pertuned floor and oracle ceiling. It is engineering-only and
does not mutate the incumbent driver.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.py --quick
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.py --stage1
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.optim import Adam

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402
from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from autodrift.evaluate import outcome_bucket_from_info  # noqa: E402
from autodrift.scenarios import classify_obstacle_scenario  # noqa: E402
from autodrift.train_ppo import ActorCritic, compute_gae_vectorized  # noqa: E402


MILESTONE_ID = "m3245-c1-v3-residual-rl-stage1"
PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_stage1_prereg.json"
QUICK_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_stage1_quick.json"
RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_stage1.json"
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_v3_residual_rl_stage1"

SEED_BASE = 20260911
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
TRAINING_SEEDS = tuple(SEED_BASE + i for i in range(8))
TRAIN_ROWS_PER_LEVEL = 8
STAGE1_STEPS_PER_SEED = 8192
QUICK_STEPS_PER_SEED = 512
ROLLOUT_STEPS = 512
BATCH_SIZE = 256
HIDDEN = 64

A3_GAPS = {
    "S1": 0.1597,
    "S2": 0.2153,
    "S3": 0.1736,
}

CLAIM_BOUNDARY = (
    "C1-v3 residual-RL stage-1 engineering readout only: eight residual policies "
    "are trained on disjoint current-sim C5-prime training rows and judged against "
    "frozen A3 fixed-v4, v4_pertuned, and oracle rows. No incumbent mutation, "
    "promotion, validation ranking, high-fidelity sufficiency claim, repair-success "
    "claim, feasibility-proof, paper claim, or self-ID claim."
)


def _source_rows() -> list[dict[str, str]]:
    return [
        row
        for row in smoke.read_source_rows()
        if row["level"] in TARGET_LEVELS and row["surface"] == SURFACE
    ]


def _vehicle_templates() -> dict[tuple[str, int], dict[str, str]]:
    out: dict[tuple[str, int], dict[str, str]] = {}
    for row in _source_rows():
        key = (row["level"], int(row["instance"]))
        out.setdefault(key, row)
    missing = [
        (level, instance)
        for level in TARGET_LEVELS
        for instance in range(12)
        if (level, instance) not in out
    ]
    if missing:
        raise RuntimeError(f"missing A3 vehicle templates: {missing[:5]}")
    return out


def _training_seed(level: str, instance: int, scan_k: int) -> int:
    return 8_000_000 + TARGET_LEVELS.index(level) * 200_000 + instance * 5_000 + scan_k * 17


def sample_training_rows(rows_per_level: int = TRAIN_ROWS_PER_LEVEL) -> list[dict[str, str]]:
    """Sample disjoint C5-prime T-limit rows from a new C1-v3 seed stream."""

    templates = _vehicle_templates()
    rows: list[dict[str, str]] = []
    for level in TARGET_LEVELS:
        accepted = 0
        scan_k = 0
        while accepted < rows_per_level and scan_k < 500:
            instance = scan_k % 12
            template = templates[(level, instance)]
            veh = {
                "mass": float(template["mass"]),
                "brake": float(template["brake"]),
                "drive": float(template["drive"]),
                "stiff": float(template["stiff"]),
                "tau": float(template["tau"]),
                "cg": float(template["cg_shift"]),
                "inertia": float(template["inertia_scale"]),
            }
            rng = np.random.default_rng([SEED_BASE, TARGET_LEVELS.index(level), instance, scan_k])
            mu = float(rng.uniform(*c5.MU_DOMAIN))
            v = c5.capped_speed(float(rng.uniform(13.0, 22.0)), mu)
            s_arc = float(rng.uniform(20.0, 42.0))
            hw = float(rng.uniform(0.70, 1.40))
            distance = c5.TRACK_R * np.sin(s_arc / c5.TRACK_R)
            label = classify_obstacle_scenario(v, mu, distance, hw).label
            instance_label = c5.adjusted_label(v, mu, 16.0, hw, veh)
            admitted = label in ("aeb_feasible", "aes_feasible") and instance_label in ("aeb", "aes", "drift")
            if admitted:
                rows.append(
                    {
                        "level": level,
                        "surface": SURFACE,
                        "instance": str(instance),
                        "eval_seed": str(_training_seed(level, instance, scan_k)),
                        "v": f"{v:.6f}",
                        "mu": f"{mu:.6f}",
                        "s_arc": f"{s_arc:.6f}",
                        "hw": f"{hw:.6f}",
                        "gen_label": label,
                        "instance_label": instance_label,
                        "mass": template["mass"],
                        "brake": template["brake"],
                        "drive": template["drive"],
                        "stiff": template["stiff"],
                        "tau": template["tau"],
                        "cg_shift": template["cg_shift"],
                        "inertia_scale": template["inertia_scale"],
                        "scan_k": str(scan_k),
                    }
                )
                accepted += 1
            scan_k += 1
        if accepted < rows_per_level:
            raise RuntimeError(f"could not sample {rows_per_level} admitted training rows for {level}")
    return rows


def validation_rows(limit_per_level: int | None = None) -> list[dict[str, str]]:
    rows = _source_rows()
    out: list[dict[str, str]] = []
    for level in TARGET_LEVELS:
        sub = [row for row in rows if row["level"] == level]
        sub.sort(key=lambda row: (int(row["instance"]), int(row["eval_seed"])))
        out.extend(sub[:limit_per_level] if limit_per_level is not None else sub)
    return out


def _success_from_outcome(outcome: str) -> float:
    return 1.0 if outcome == "success" else 0.0


def _init_residual_model(seed: int) -> ActorCritic:
    torch.manual_seed(seed)
    model = ActorCritic(
        obs_dim=smoke.OBS_DIM,
        act_dim=smoke.ACT_DIM,
        hidden_size=HIDDEN,
        log_std_init=-1.2,
        log_std_min=-5.0,
        log_std_max=-0.6,
        actor_encoder="mlp",
    )
    nn.init.zeros_(model.actor_mean.weight)
    nn.init.zeros_(model.actor_mean.bias)
    return model


def _collect_rollout(
    model: ActorCritic,
    pool: smoke.C5PrimeResidualPool,
    base_driver: ActiveSafetyReflexDriver,
    obs: np.ndarray,
    steps: int,
) -> tuple[dict[str, np.ndarray], np.ndarray, list[dict[str, Any]]]:
    obs_rows = np.zeros((steps, smoke.OBS_DIM), dtype=np.float32)
    residual_rows = np.zeros((steps, smoke.ACT_DIM), dtype=np.float32)
    logp_rows = np.zeros(steps, dtype=np.float32)
    reward_rows = np.zeros(steps, dtype=np.float32)
    done_rows = np.zeros(steps, dtype=np.float32)
    value_rows = np.zeros(steps, dtype=np.float32)
    episode_rows: list[dict[str, Any]] = []
    episode_return = 0.0
    episode_length = 0

    for step in range(steps):
        residual_action, logp, value = model.act(obs)
        base_action = base_driver.act(obs)
        _base, _delta, final_action = smoke.compose_residual_action(base_action, residual_action)
        next_obs, reward, terminated, truncated, info = pool.step(final_action)
        done = terminated or truncated

        obs_rows[step] = obs
        residual_rows[step] = residual_action
        logp_rows[step] = logp
        reward_rows[step] = reward
        done_rows[step] = float(done)
        value_rows[step] = value
        episode_return += reward
        episode_length += 1

        if done:
            bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            episode_rows.append(
                {
                    "row_id": str(info["row_id"]),
                    "level": str(info["level"]),
                    "outcome_bucket": bucket,
                    "termination_reason": str(info.get("termination_reason", "") or ""),
                    "return": float(episode_return),
                    "length": int(episode_length),
                }
            )
            obs, _reset_info = pool.reset()
            episode_return = 0.0
            episode_length = 0
        else:
            obs = next_obs

    return (
        {
            "obs": obs_rows,
            "residual": residual_rows,
            "logp": logp_rows,
            "reward": reward_rows,
            "done": done_rows,
            "value": value_rows,
        },
        obs,
        episode_rows,
    )


def _ppo_update(model: ActorCritic, optimizer: Adam, rollout: dict[str, np.ndarray], last_obs: np.ndarray) -> list[float]:
    with torch.no_grad():
        _, last_value_t = model.forward(torch.as_tensor(last_obs, dtype=torch.float32).unsqueeze(0))
    advantages, returns = compute_gae_vectorized(
        rollout["reward"][:, None],
        rollout["done"][:, None],
        rollout["value"][:, None],
        last_value_t.detach().cpu().numpy().astype(np.float32),
        gamma=0.99,
        gae_lambda=0.95,
    )
    adv = advantages[:, 0]
    ret = returns[:, 0]
    adv = (adv - float(adv.mean())) / (float(adv.std()) + 1e-8)

    obs_t = torch.as_tensor(rollout["obs"], dtype=torch.float32)
    act_t = torch.as_tensor(rollout["residual"], dtype=torch.float32)
    old_logp_t = torch.as_tensor(rollout["logp"], dtype=torch.float32)
    adv_t = torch.as_tensor(adv, dtype=torch.float32)
    ret_t = torch.as_tensor(ret, dtype=torch.float32)
    indices = np.arange(len(obs_t))
    losses: list[float] = []
    for _ in range(2):
        np.random.shuffle(indices)
        for start in range(0, len(indices), BATCH_SIZE):
            mb = indices[start : start + BATCH_SIZE]
            loss = smoke._evaluate_loss(
                model,
                obs_t[mb],
                act_t[mb],
                old_logp_t[mb],
                adv_t[mb],
                ret_t[mb],
                clip_coef=0.2,
                vf_coef=0.5,
                ent_coef=0.001,
            )
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 0.5)
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
    return losses


def train_one_seed(train_rows: list[dict[str, str]], training_seed: int, total_steps: int) -> tuple[ActorCritic, dict[str, Any]]:
    np.random.seed(training_seed)
    torch.manual_seed(training_seed)
    model = _init_residual_model(training_seed)
    optimizer = Adam(model.parameters(), lr=3e-4)
    before = [param.detach().cpu().clone() for param in model.parameters()]
    base_driver = ActiveSafetyReflexDriver()
    pool = smoke.C5PrimeResidualPool(train_rows)
    obs, _info = pool.reset()
    losses: list[float] = []
    episodes: list[dict[str, Any]] = []
    steps_done = 0
    try:
        while steps_done < total_steps:
            rollout_steps = min(ROLLOUT_STEPS, total_steps - steps_done)
            rollout, obs, episode_rows = _collect_rollout(model, pool, base_driver, obs, rollout_steps)
            losses.extend(_ppo_update(model, optimizer, rollout, obs))
            episodes.extend(episode_rows)
            steps_done += rollout_steps
    finally:
        pool.close()
    return model, {
        "training_seed": training_seed,
        "steps": int(total_steps),
        "episodes": len(episodes),
        "episode_return_mean": float(np.mean([row["return"] for row in episodes])) if episodes else float("nan"),
        "loss_initial": losses[0] if losses else float("nan"),
        "loss_final": losses[-1] if losses else float("nan"),
        "param_delta_l2": smoke._parameters_l2_delta(before, model),
    }


def evaluate_model(model: ActorCritic, rows: list[dict[str, str]], training_seed: int) -> list[dict[str, Any]]:
    base_driver = ActiveSafetyReflexDriver()
    out: list[dict[str, Any]] = []
    model.eval()
    for row in rows:
        env = smoke.env_from_source_row(row)
        try:
            obs, _info = env.reset(seed=int(row["eval_seed"]))
            terminated = truncated = False
            steps = 0
            total_return = 0.0
            while not (terminated or truncated):
                residual_action, _logp, _value = model.act(obs, deterministic=True)
                base_action = base_driver.act(obs)
                _base, _delta, final_action = smoke.compose_residual_action(base_action, residual_action)
                obs, reward, terminated, truncated, info = env.step(final_action)
                total_return += float(reward)
                steps += 1
            bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            outcome = c5.failure_mode(bucket, str(info.get("termination_reason", "") or ""))
            out.append(
                {
                    "training_seed": training_seed,
                    "row_id": smoke.row_id(row),
                    "level": row["level"],
                    "instance": int(row["instance"]),
                    "eval_seed": int(row["eval_seed"]),
                    "fixed_v4_outcome": row["fixed_v4_incumbent_outcome"],
                    "v4_pertuned_outcome": row["v4_pertuned_outcome"],
                    "oracle_solved": row["oracle_solved"] == "True",
                    "v4_residual_outcome": outcome,
                    "v4_residual_steps": steps,
                    "v4_residual_return": float(total_return),
                }
            )
        finally:
            env.close()
    return out


def _paired_bootstrap_ci(candidate: np.ndarray, baseline: np.ndarray, rng: np.random.Generator) -> list[float]:
    if candidate.ndim != 2:
        raise ValueError("candidate must be training_seed x validation_row")
    n_seed, n_row = candidate.shape
    if baseline.shape != (n_row,):
        raise ValueError(f"baseline shape {baseline.shape} != {(n_row,)}")
    diffs = []
    for _ in range(2000):
        seed_idx = rng.integers(0, n_seed, size=n_seed)
        row_idx = rng.integers(0, n_row, size=n_row)
        cand = candidate[np.ix_(seed_idx, row_idx)].mean()
        base = baseline[row_idx].mean()
        diffs.append(float(cand - base))
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


def aggregate_results(candidate_rows: list[dict[str, Any]], val_rows: list[dict[str, str]]) -> dict[str, Any]:
    by_row_id = {smoke.row_id(row): row for row in val_rows}
    seed_values = sorted({int(row["training_seed"]) for row in candidate_rows})
    cells: dict[str, Any] = {}
    rng = np.random.default_rng([SEED_BASE, 77])
    for level in TARGET_LEVELS:
        row_ids = [smoke.row_id(row) for row in val_rows if row["level"] == level]
        fixed_v4 = np.asarray(
            [_success_from_outcome(by_row_id[row_id]["fixed_v4_incumbent_outcome"]) for row_id in row_ids],
            dtype=np.float64,
        )
        pertuned = np.asarray(
            [_success_from_outcome(by_row_id[row_id]["v4_pertuned_outcome"]) for row_id in row_ids],
            dtype=np.float64,
        )
        oracle = np.asarray([1.0 if by_row_id[row_id]["oracle_solved"] == "True" else 0.0 for row_id in row_ids])
        candidate = np.zeros((len(seed_values), len(row_ids)), dtype=np.float64)
        rows_by_seed_id = {
            (int(row["training_seed"]), row["row_id"]): row
            for row in candidate_rows
            if row["level"] == level
        }
        for seed_index, seed in enumerate(seed_values):
            for row_index, row_id in enumerate(row_ids):
                candidate[seed_index, row_index] = _success_from_outcome(
                    rows_by_seed_id[(seed, row_id)]["v4_residual_outcome"]
                )
        seed_diffs = candidate.mean(axis=1) - pertuned.mean()
        gap = float(seed_diffs.mean())
        seed_se = float(np.std(seed_diffs, ddof=1) / np.sqrt(len(seed_diffs))) if len(seed_diffs) > 1 else float("nan")
        a3_gap = float(A3_GAPS[level])
        recapture = gap / a3_gap if a3_gap > 0.0 else float("nan")
        cells[f"{level}/T_limit"] = {
            "n_validation_rows": len(row_ids),
            "n_training_seeds": len(seed_values),
            "fixed_v4_success": round(float(fixed_v4.mean()), 4),
            "v4_pertuned_success": round(float(pertuned.mean()), 4),
            "oracle_success": round(float(oracle.mean()), 4),
            "v4_residual_success": round(float(candidate.mean()), 4),
            "candidate_minus_pertuned": round(gap, 4),
            "candidate_minus_pertuned_paired_bootstrap_ci95": _paired_bootstrap_ci(candidate, pertuned, rng),
            "candidate_minus_pertuned_seed_clustered_se": round(seed_se, 4),
            "a3_oracle_minus_pertuned_gap": round(a3_gap, 4),
            "recapture_fraction": round(float(recapture), 4),
            "cell_pass": bool(recapture >= 0.5),
            "seed_level_gaps": [round(float(value), 4) for value in seed_diffs],
        }
    pass_cells = [cell for cell, summary in cells.items() if summary["cell_pass"]]
    return {
        "cells": cells,
        "pass_cells": pass_cells,
        "n_pass_cells": len(pass_cells),
        "stage1_pass": len(pass_cells) >= 2,
        "decision_rule": "PASS iff recapture_fraction >= 0.5 in at least 2 of S1/S2/S3 T-limit cells; paired CI and seed-clustered SE are reported, not used to loosen the gate.",
    }


def preregistration_payload() -> dict[str, Any]:
    val_rows = validation_rows()
    train_rows = sample_training_rows()
    train_eval_seeds = [int(row["eval_seed"]) for row in train_rows]
    validation_eval_seeds = [int(row["eval_seed"]) for row in val_rows]
    return {
        "protocol": "c5prime_c1_v3_residual_rl_stage1",
        "milestone_id": MILESTONE_ID,
        "roadmap_unit": "C1-v3 residual RL stage-1",
        "frozen_at_utc": "2026-06-12T00:00:00Z",
        "frozen_before_any_c1_v3_stage1_rollout": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "pricing_basis": {
            "primary_artifact": str(smoke.SOURCE_PRICING_JSON.relative_to(REPO)),
            "priced_gap_floor": 0.1597,
            "threshold": 0.15,
            "gap_meets_threshold": True,
            "qualified_cells": [f"{level}/T_limit" for level in TARGET_LEVELS],
            "chrono_direction_artifact": "experiments/feasibility_audit/chrono_native_oracle_pricing.json",
            "chrono_direction_positive": True,
        },
        "training_design": {
            "training_seeds": list(TRAINING_SEEDS),
            "steps_per_training_seed": STAGE1_STEPS_PER_SEED,
            "rollout_steps": ROLLOUT_STEPS,
            "train_rows_per_level": TRAIN_ROWS_PER_LEVEL,
            "train_row_ids": [smoke.row_id(row) for row in train_rows],
            "train_eval_seeds": [int(row["eval_seed"]) for row in train_rows],
            "delta_max": smoke.DELTA_MAX.tolist(),
            "base_policy": "ActiveSafetyReflexDriver incumbent v4, frozen",
            "actor": {"encoder": "mlp", "hidden_size": HIDDEN},
            "reward": {"pass_reward": smoke.PASS_REWARD, "collision_penalty": smoke.COLLISION_PENALTY},
        },
        "validation_design": {
            "validation_source": str(smoke.SOURCE_ROWS_CSV.relative_to(REPO)),
            "validation_cells": [f"{level}/T_limit" for level in TARGET_LEVELS],
            "validation_rows_per_cell": 144,
            "validation_row_ids": [smoke.row_id(row) for row in val_rows],
            "arms": ["fixed_v4", "v4_pertuned", "v4_residual", "oracle"],
            "fixed_v4_source": "A3 fixed_v4_incumbent_outcome",
            "v4_pertuned_source": "A3 v4_pertuned_outcome",
            "oracle_source": "A3 oracle_solved",
            "candidate_source": "deterministic mean action of each trained residual policy",
        },
        "seed_discipline": {
            "new_seed_base": SEED_BASE,
            "training_eval_seeds_disjoint_from_validation": set(train_eval_seeds).isdisjoint(validation_eval_seeds),
            "training_model_seeds_disjoint_from_m3244": True,
            "training_seed_count": len(TRAINING_SEEDS),
        },
        "decision_rule": {
            "primary": "v4_residual_success - v4_pertuned_success per cell, averaged across training seeds on paired validation rows",
            "uncertainty": "paired bootstrap CI95 over training seeds and validation rows plus training-seed-clustered SE",
            "pass": "recapture at least 50 percent of the A3 oracle-minus-pertuned gap in at least 2 of 3 qualified T-limit cells",
            "fail": "otherwise; no criteria loosening",
            "stop_rule": "two behavior-neutral C1-v3 results require stop and synthesis before further attempts",
        },
        "quick_mode": {
            "purpose": "protocol check only",
            "training_seeds": [TRAINING_SEEDS[0]],
            "steps_per_seed": QUICK_STEPS_PER_SEED,
            "validation_rows_per_level": 4,
        },
    }


def write_preregistration() -> dict[str, Any]:
    payload = preregistration_payload()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}")
    payload = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
    if not payload.get("frozen_before_any_c1_v3_stage1_rollout"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_c1_v3_stage1_rollout")
    return payload


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(mode: str) -> dict[str, Any]:
    if mode not in {"quick", "stage1"}:
        raise ValueError(f"unknown mode: {mode}")
    prereg = load_preregistration()
    quick = mode == "quick"
    run_dir = RUN_DIR / mode
    run_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    t0 = time.time()

    train_rows = sample_training_rows(rows_per_level=2 if quick else TRAIN_ROWS_PER_LEVEL)
    val_rows = validation_rows(limit_per_level=4 if quick else None)
    training_seeds = [TRAINING_SEEDS[0]] if quick else list(TRAINING_SEEDS)
    steps_per_seed = QUICK_STEPS_PER_SEED if quick else STAGE1_STEPS_PER_SEED
    progress_path = run_dir / "progress.json"

    training_metrics: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    checkpoints: dict[str, Any] = {
        "protocol": "c5prime_c1_v3_residual_rl_stage1",
        "mode": mode,
        "model_config": {
            "obs_dim": smoke.OBS_DIM,
            "act_dim": smoke.ACT_DIM,
            "hidden_size": HIDDEN,
            "actor_encoder": "mlp",
            "delta_max": smoke.DELTA_MAX.tolist(),
            "base_policy": "ActiveSafetyReflexDriver incumbent v4 frozen",
        },
        "states": {},
    }
    for index, seed in enumerate(training_seeds, start=1):
        model, metrics = train_one_seed(train_rows, seed, steps_per_seed)
        training_metrics.append(metrics)
        candidate_rows.extend(evaluate_model(model, val_rows, seed))
        checkpoints["states"][str(seed)] = model.state_dict()
        progress_path.write_text(
            json.dumps(
                {
                    "mode": mode,
                    "completed_training_seeds": index,
                    "total_training_seeds": len(training_seeds),
                    "elapsed_s": round(time.time() - t0, 1),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    _write_csv(run_dir / "training_metrics.csv", training_metrics)
    _write_csv(run_dir / "candidate_rows.csv", candidate_rows)
    torch.save(checkpoints, run_dir / "checkpoints.pt")

    aggregate = aggregate_results(candidate_rows, val_rows)
    result = {
        "protocol": "c5prime_c1_v3_residual_rl_stage1",
        "mode": mode,
        "generated_by": "scripts/feasibility_audit/c5prime_c1_v3_residual_rl_stage1.py",
        "generated_at_utc": utc_timestamp(),
        "preregistration": str(PREREG_JSON.relative_to(REPO)),
        "claim_boundary": CLAIM_BOUNDARY,
        "pricing_basis": prereg["pricing_basis"],
        "training_design": prereg["training_design"],
        "validation_design": {
            **prereg["validation_design"],
            "validation_rows_used": len(val_rows),
        },
        "training_metrics": training_metrics,
        "aggregate": aggregate,
        "artifacts": {
            "training_metrics_csv": str((run_dir / "training_metrics.csv").relative_to(REPO)),
            "candidate_rows_csv": str((run_dir / "candidate_rows.csv").relative_to(REPO)),
            "checkpoints": str((run_dir / "checkpoints.pt").relative_to(REPO)),
            "progress": str(progress_path.relative_to(REPO)),
        },
        "wall_time_s": round(time.time() - t0, 3),
    }
    output = QUICK_JSON if quick else RESULTS_JSON
    write_json(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run C1-v3 residual-RL stage-1.")
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--stage1", action="store_true")
    args = parser.parse_args()

    if args.write_prereg:
        payload = write_preregistration()
        print(
            f"wrote_prereg={PREREG_JSON} training_seeds={len(payload['training_design']['training_seeds'])} "
            f"validation_rows={len(payload['validation_design']['validation_row_ids'])}"
        )
        if not args.quick and not args.stage1:
            return
    if args.quick and args.stage1:
        raise SystemExit("--quick and --stage1 are mutually exclusive")
    if not args.quick and not args.stage1:
        raise SystemExit("pass --quick or --stage1")
    result = run("quick" if args.quick else "stage1")
    aggregate = result["aggregate"]
    print(
        f"mode={result['mode']} stage1_pass={aggregate['stage1_pass']} "
        f"pass_cells={aggregate['pass_cells']} wall_time_s={result['wall_time_s']}"
    )


if __name__ == "__main__":
    main()
