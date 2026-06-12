"""C1-v4 Stage B guarded RL from the M3246 distillation warm start.

This is the final C1-v4 learning rung opened by the M3246 Stage A pass. It
starts from the primary M3245-bounded distiller, keeps the incumbent v4 frozen,
and trains a stochastic residual policy with a fixed log-std schedule. The
judging rule is unchanged from C1-v3: v4+residual must recapture at least 50%
of the A3 oracle-minus-v4_pertuned gap in at least 2 of the 3 frozen T-limit
cells.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.py --quick
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.py --stage-b
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.distributions import Normal
from torch.optim import Adam

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402
import c5prime_c1_v4_distill_stage_a as stage_a  # noqa: E402
from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.evaluate import outcome_bucket_from_info  # noqa: E402
from autodrift.scenarios import classify_obstacle_scenario  # noqa: E402
from autodrift.train_ppo import compute_gae_vectorized  # noqa: E402


MILESTONE_ID = "m3247-c1-v4-stage-b-guarded-rl"
PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_stage_b_guarded_rl_prereg.json"
QUICK_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_stage_b_guarded_rl_quick.json"
RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_stage_b_guarded_rl.json"
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_v4_stage_b_guarded_rl"
STAGE_A_RESULT_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a.json"
STAGE_A_PRIMARY_CHECKPOINT = (
    REPO / "runs" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a" / "stage_a" / "primary_distiller.pt"
)

SEED_BASE = 20261021
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
TRAINING_SEEDS = tuple(SEED_BASE + i for i in range(8))
TRAIN_ROWS_PER_LEVEL = 8
QUICK_TRAIN_ROWS_PER_LEVEL = 2
STAGE_B_STEPS_PER_SEED = 1_000_000
QUICK_STEPS_PER_SEED = 1024
ROLLOUT_STEPS = 512
BATCH_SIZE = 256
UPDATE_EPOCHS = 2
HIDDEN = 64
LEARNING_RATE = 2e-4
LOG_STD_FIXED = -1.4
ENT_COEF = 0.0005
VF_COEF = 0.5
CLIP_COEF = 0.2
MAX_GRAD_NORM = 0.5
MAX_WORKERS = 8
MOVEMENT_RECAPTURE_FLOOR = 0.15

CLAIM_BOUNDARY = (
    "C1-v4 Stage B guarded-RL engineering readout only: residual policies are "
    "initialized from the M3246 primary distiller, trained over frozen-v4 "
    "current-sim C5-prime rows, and judged against frozen A3 v4_pertuned and "
    "oracle rows. No incumbent mutation, validation ranking, driver-performance "
    "claim, high-fidelity sufficiency claim, repair-success claim, "
    "feasibility-proof, paper claim, or self-ID claim."
)


class WarmResidualActorCritic(nn.Module):
    def __init__(self, hidden: int = HIDDEN, log_std_init: float = LOG_STD_FIXED):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(smoke.OBS_DIM, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.actor_mean = nn.Linear(hidden, smoke.ACT_DIM)
        self.critic = nn.Linear(hidden, 1)
        self.log_std = nn.Parameter(torch.full((smoke.ACT_DIM,), float(log_std_init)), requires_grad=False)

    def forward(self, obs: torch.Tensor) -> tuple[Normal, torch.Tensor]:
        features = self.encoder(obs)
        mean = self.actor_mean(features)
        std = torch.exp(self.log_std).expand_as(mean)
        return Normal(mean, std), self.critic(features).squeeze(-1)

    def _squashed_log_prob(self, dist: Normal, raw_action: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        correction = torch.log(torch.clamp(1.0 - action.pow(2), min=1e-6)).sum(dim=-1)
        return dist.log_prob(raw_action).sum(dim=-1) - correction

    def act(self, obs: np.ndarray, deterministic: bool = False) -> tuple[np.ndarray, float, float]:
        obs_t = torch.as_tensor(np.asarray(obs, dtype=np.float32), dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            dist, value = self.forward(obs_t)
            raw_action = dist.mean if deterministic else dist.sample()
            action = torch.tanh(raw_action)
            log_prob = self._squashed_log_prob(dist, raw_action, action)
        return action.squeeze(0).cpu().numpy().astype(np.float32), float(log_prob.item()), float(value.item())

    def evaluate_actions(self, obs: torch.Tensor, actions: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        dist, value = self.forward(obs)
        clipped_actions = torch.clamp(actions, -1.0 + 1e-6, 1.0 - 1e-6)
        raw_actions = torch.atanh(clipped_actions)
        log_prob = self._squashed_log_prob(dist, raw_actions, clipped_actions)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy, value


def init_model_from_distiller_checkpoint(checkpoint: Path | str, seed: int) -> WarmResidualActorCritic:
    torch.manual_seed(seed)
    model = WarmResidualActorCritic()
    payload = torch.load(Path(checkpoint), map_location="cpu")
    state = payload["model_state"]
    with torch.no_grad():
        model.encoder[0].weight.copy_(state["net.0.weight"])
        model.encoder[0].bias.copy_(state["net.0.bias"])
        model.encoder[2].weight.copy_(state["net.2.weight"])
        model.encoder[2].bias.copy_(state["net.2.bias"])
        model.actor_mean.weight.copy_(state["net.4.weight"])
        model.actor_mean.bias.copy_(state["net.4.bias"])
        nn.init.zeros_(model.critic.weight)
        nn.init.zeros_(model.critic.bias)
    return model


def _read_source_rows() -> list[dict[str, str]]:
    with smoke.SOURCE_ROWS_CSV.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _source_rows() -> list[dict[str, str]]:
    return [row for row in _read_source_rows() if row["level"] in TARGET_LEVELS and row["surface"] == SURFACE]


def _veh_from_row(row: dict[str, str]) -> dict[str, float]:
    return {
        "mass": float(row["mass"]),
        "brake": float(row["brake"]),
        "drive": float(row["drive"]),
        "stiff": float(row["stiff"]),
        "tau": float(row["tau"]),
        "cg": float(row["cg_shift"]),
        "inertia": float(row["inertia_scale"]),
    }


def _vehicle_templates() -> dict[tuple[str, int], dict[str, str]]:
    out: dict[tuple[str, int], dict[str, str]] = {}
    for row in _source_rows():
        out.setdefault((row["level"], int(row["instance"])), row)
    missing = [
        (level, instance)
        for level in TARGET_LEVELS
        for instance in range(12)
        if (level, instance) not in out
    ]
    if missing:
        raise RuntimeError(f"missing A3 vehicle templates: {missing[:5]}")
    return out


def _training_eval_seed(level: str, instance: int, scan_k: int) -> int:
    return 9_000_000 + TARGET_LEVELS.index(level) * 200_000 + instance * 5_000 + scan_k * 17


def sample_training_rows(rows_per_level: int = TRAIN_ROWS_PER_LEVEL) -> list[dict[str, str]]:
    templates = _vehicle_templates()
    rows: list[dict[str, str]] = []
    for level in TARGET_LEVELS:
        accepted = 0
        scan_k = 0
        while accepted < rows_per_level and scan_k < 500:
            instance = scan_k % 12
            template = templates[(level, instance)]
            veh = _veh_from_row(template)
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
                        "eval_seed": str(_training_eval_seed(level, instance, scan_k)),
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


def _collect_rollout(
    model: WarmResidualActorCritic,
    pool: smoke.C5PrimeResidualPool,
    base_driver: ActiveSafetyReflexDriver,
    obs: np.ndarray,
    steps: int,
) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, Any]]:
    obs_rows = np.zeros((steps, smoke.OBS_DIM), dtype=np.float32)
    residual_rows = np.zeros((steps, smoke.ACT_DIM), dtype=np.float32)
    logp_rows = np.zeros(steps, dtype=np.float32)
    reward_rows = np.zeros(steps, dtype=np.float32)
    done_rows = np.zeros(steps, dtype=np.float32)
    value_rows = np.zeros(steps, dtype=np.float32)
    episode_count = 0
    success_count = 0
    episode_return_sum = 0.0
    episode_length_sum = 0
    current_return = 0.0
    current_length = 0

    for step in range(steps):
        residual_action, logp, value = model.act(obs)
        fixed = base_driver.act(obs)
        _base, _delta, final_action = smoke.compose_residual_action(fixed, residual_action, delta_max=stage_a.PRIMARY_DELTA_MAX)
        next_obs, reward, terminated, truncated, info = pool.step(final_action)
        done = terminated or truncated

        obs_rows[step] = obs
        residual_rows[step] = residual_action
        logp_rows[step] = logp
        reward_rows[step] = reward
        done_rows[step] = float(done)
        value_rows[step] = value
        current_return += float(reward)
        current_length += 1

        if done:
            bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            outcome = c5.failure_mode(bucket, str(info.get("termination_reason", "") or ""))
            episode_count += 1
            success_count += int(outcome == "success")
            episode_return_sum += current_return
            episode_length_sum += current_length
            obs, _reset_info = pool.reset()
            current_return = 0.0
            current_length = 0
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
        {
            "episodes": episode_count,
            "successes": success_count,
            "episode_return_sum": episode_return_sum,
            "episode_length_sum": episode_length_sum,
        },
    )


def _ppo_update(model: WarmResidualActorCritic, optimizer: Adam, rollout: dict[str, np.ndarray], last_obs: np.ndarray) -> list[float]:
    with torch.no_grad():
        _dist, last_value_t = model.forward(torch.as_tensor(last_obs, dtype=torch.float32).unsqueeze(0))
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
    for _ in range(UPDATE_EPOCHS):
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
                clip_coef=CLIP_COEF,
                vf_coef=VF_COEF,
                ent_coef=ENT_COEF,
            )
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
    return losses


def _parameters_l2_delta(before: list[torch.Tensor], model: nn.Module) -> float:
    total = 0.0
    for old, new in zip(before, model.parameters(), strict=True):
        diff = new.detach().cpu() - old
        total += float(torch.square(diff).sum().item())
    return float(total ** 0.5)


def train_one_seed(
    train_rows: list[dict[str, str]],
    eval_rows: list[dict[str, str]],
    training_seed: int,
    total_steps: int,
    checkpoint_path: str,
    run_dir: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    torch.set_num_threads(1)
    np.random.seed(training_seed)
    torch.manual_seed(training_seed)
    model = init_model_from_distiller_checkpoint(checkpoint_path, training_seed)
    optimizer = Adam([param for param in model.parameters() if param.requires_grad], lr=LEARNING_RATE)
    before = [param.detach().cpu().clone() for param in model.parameters()]
    base_driver = ActiveSafetyReflexDriver()
    pool = smoke.C5PrimeResidualPool(train_rows)
    obs, _info = pool.reset()
    run_path = Path(run_dir)
    progress_path = run_path / f"progress_seed_{training_seed}.json"
    losses: list[float] = []
    steps_done = 0
    episode_count = 0
    success_count = 0
    return_sum = 0.0
    length_sum = 0
    t0 = time.time()
    try:
        while steps_done < total_steps:
            rollout_steps = min(ROLLOUT_STEPS, total_steps - steps_done)
            rollout, obs, stats = _collect_rollout(model, pool, base_driver, obs, rollout_steps)
            losses.extend(_ppo_update(model, optimizer, rollout, obs))
            steps_done += rollout_steps
            episode_count += int(stats["episodes"])
            success_count += int(stats["successes"])
            return_sum += float(stats["episode_return_sum"])
            length_sum += int(stats["episode_length_sum"])
            if steps_done == total_steps or steps_done % 50_000 < rollout_steps:
                progress_path.write_text(
                    json.dumps(
                        {
                            "training_seed": training_seed,
                            "steps_done": steps_done,
                            "total_steps": total_steps,
                            "episodes": episode_count,
                            "success_rate_train_rollouts": success_count / max(episode_count, 1),
                            "elapsed_s": round(time.time() - t0, 1),
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
    finally:
        pool.close()
    checkpoint_out = run_path / f"stage_b_seed_{training_seed}.pt"
    torch.save(
        {
            "protocol": "c5prime_c1_v4_stage_b_guarded_rl",
            "training_seed": training_seed,
            "model_state": model.state_dict(),
            "model_config": {
                "obs_dim": smoke.OBS_DIM,
                "act_dim": smoke.ACT_DIM,
                "hidden": HIDDEN,
                "delta_max": stage_a.PRIMARY_DELTA_MAX.tolist(),
                "log_std_fixed": LOG_STD_FIXED,
            },
        },
        checkpoint_out,
    )
    metrics = {
        "training_seed": training_seed,
        "steps": int(total_steps),
        "episodes": int(episode_count),
        "success_rate_train_rollouts": round(float(success_count / max(episode_count, 1)), 4),
        "episode_return_mean": round(float(return_sum / max(episode_count, 1)), 4),
        "episode_length_mean": round(float(length_sum / max(episode_count, 1)), 4),
        "loss_initial": losses[0] if losses else float("nan"),
        "loss_final": losses[-1] if losses else float("nan"),
        "param_delta_l2": _parameters_l2_delta(before, model),
        "wall_time_s": round(time.time() - t0, 3),
    }
    candidate_rows = evaluate_model(model, eval_rows, training_seed)
    return metrics, candidate_rows, str(checkpoint_out.relative_to(REPO))


def evaluate_model(
    model: WarmResidualActorCritic,
    rows: list[dict[str, str]],
    training_seed: int,
) -> list[dict[str, Any]]:
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
            info: dict[str, Any] = {}
            while not (terminated or truncated):
                residual_action, _logp, _value = model.act(obs, deterministic=True)
                fixed = base_driver.act(obs)
                _base, _delta, final_action = smoke.compose_residual_action(
                    fixed,
                    residual_action,
                    delta_max=stage_a.PRIMARY_DELTA_MAX,
                )
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
                    "v4_stage_b_outcome": outcome,
                    "v4_stage_b_steps": steps,
                    "v4_stage_b_return": float(total_return),
                }
            )
        finally:
            env.close()
    return out


def _success_from_outcome(outcome: str) -> float:
    return 1.0 if outcome == "success" else 0.0


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
    rng = np.random.default_rng([SEED_BASE, 88])
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
                    rows_by_seed_id[(seed, row_id)]["v4_stage_b_outcome"]
                )
        seed_diffs = candidate.mean(axis=1) - pertuned.mean()
        gap = float(seed_diffs.mean())
        seed_se = float(np.std(seed_diffs, ddof=1) / np.sqrt(len(seed_diffs))) if len(seed_diffs) > 1 else float("nan")
        a3_gap = float(stage_a.A3_GAPS[level])
        recapture = gap / a3_gap if a3_gap > 0.0 else float("nan")
        cell_pass = bool(recapture >= 0.5)
        movement = bool(recapture >= MOVEMENT_RECAPTURE_FLOOR)
        cells[f"{level}/T_limit"] = {
            "n_validation_rows": len(row_ids),
            "n_training_seeds": len(seed_values),
            "fixed_v4_success": round(float(fixed_v4.mean()), 4),
            "v4_pertuned_success": round(float(pertuned.mean()), 4),
            "oracle_success": round(float(oracle.mean()), 4),
            "v4_stage_b_success": round(float(candidate.mean()), 4),
            "candidate_minus_pertuned": round(gap, 4),
            "candidate_minus_pertuned_paired_bootstrap_ci95": _paired_bootstrap_ci(candidate, pertuned, rng),
            "candidate_minus_pertuned_seed_clustered_se": round(seed_se, 4),
            "a3_oracle_minus_pertuned_gap": round(a3_gap, 4),
            "recapture_fraction": round(float(recapture), 4),
            "cell_pass": cell_pass,
            "movement_signal": movement,
            "seed_level_gaps": [round(float(value), 4) for value in seed_diffs],
        }
    pass_cells = [cell for cell, summary in cells.items() if summary["cell_pass"]]
    movement_cells = [cell for cell, summary in cells.items() if summary["movement_signal"]]
    stage_b_pass = len(pass_cells) >= 2
    extension_admitted = bool((not stage_b_pass) and len(movement_cells) >= 1)
    return {
        "cells": cells,
        "pass_cells": pass_cells,
        "n_pass_cells": len(pass_cells),
        "movement_cells": movement_cells,
        "n_movement_cells": len(movement_cells),
        "stage_b_pass": stage_b_pass,
        "extension_admitted": extension_admitted,
        "decision_rule": "PASS iff recapture_fraction >= 0.5 in at least 2 of S1/S2/S3 T-limit cells. If first rung does not pass but recapture_fraction >= 0.15 in at least 1 cell, one 4M-step extension is admitted; otherwise C1-v4 fails.",
    }


def _stage_a_primary_summary() -> dict[str, Any]:
    data = json.loads(STAGE_A_RESULT_JSON.read_text(encoding="utf-8"))
    return data["aggregate"]["primary"]


def preregistration_payload() -> dict[str, Any]:
    if not STAGE_A_RESULT_JSON.exists():
        raise FileNotFoundError(f"missing M3246 result {STAGE_A_RESULT_JSON}")
    train_rows = sample_training_rows()
    val_rows = stage_a.validation_rows()
    train_eval_seeds = [int(row["eval_seed"]) for row in train_rows]
    validation_eval_seeds = [int(row["eval_seed"]) for row in val_rows]
    stage_a_primary = _stage_a_primary_summary()
    return {
        "protocol": "c5prime_c1_v4_stage_b_guarded_rl",
        "milestone_id": MILESTONE_ID,
        "roadmap_unit": "C1-v4 Stage B guarded RL from distilled warm start",
        "frozen_at_utc": "2026-06-12T00:00:00Z",
        "frozen_before_any_c1_v4_stage_b_rollout": True,
        "final_attempt_clause": "C1-v4 is the final pre-registered learning attempt at the C5-prime prize; Stage B verdict closes Track C unless the frozen extension rule is triggered.",
        "claim_boundary": CLAIM_BOUNDARY,
        "admission_basis": {
            "stage_a_artifact": str(STAGE_A_RESULT_JSON.relative_to(REPO)),
            "stage_a_pass": bool(stage_a_primary["stage_a_pass"]),
            "stage_a_primary_pass_cells": stage_a_primary["pass_cells"],
            "warm_start_checkpoint": str(STAGE_A_PRIMARY_CHECKPOINT.relative_to(REPO)),
        },
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
            "seed_base": SEED_BASE,
            "training_seeds": list(TRAINING_SEEDS),
            "steps_per_training_seed": STAGE_B_STEPS_PER_SEED,
            "rollout_steps": ROLLOUT_STEPS,
            "train_rows_per_level": TRAIN_ROWS_PER_LEVEL,
            "train_row_ids": [smoke.row_id(row) for row in train_rows],
            "train_eval_seeds": train_eval_seeds,
            "base_policy": "ActiveSafetyReflexDriver incumbent v4, frozen",
            "warm_start": "M3246 primary_distiller.pt copied into a ReLU actor-critic with a fresh critic",
            "delta_max": stage_a.PRIMARY_DELTA_MAX.tolist(),
            "log_std_fixed": LOG_STD_FIXED,
            "entropy_coef": ENT_COEF,
            "learning_rate": LEARNING_RATE,
            "parallel_workers": MAX_WORKERS,
        },
        "validation_design": {
            "validation_source": str(smoke.SOURCE_ROWS_CSV.relative_to(REPO)),
            "validation_cells": [f"{level}/T_limit" for level in TARGET_LEVELS],
            "validation_rows_per_cell": 144,
            "validation_row_ids": [smoke.row_id(row) for row in val_rows],
            "arms": ["fixed_v4", "v4_pertuned", "v4_stage_b", "oracle"],
            "candidate_source": "deterministic mean action of each trained warm-start residual policy",
        },
        "seed_discipline": {
            "new_seed_base": SEED_BASE,
            "training_eval_seed_stream": "9_000_000 + level*200_000 + instance*5_000 + scan_k*17",
            "training_eval_seeds_disjoint_from_validation": set(train_eval_seeds).isdisjoint(validation_eval_seeds),
            "training_eval_seeds_disjoint_from_m3246_stage_a": True,
            "model_training_seed_count": len(TRAINING_SEEDS),
        },
        "decision_rule": {
            "primary": "v4_stage_b_success - v4_pertuned_success per cell, averaged across training seeds on paired validation rows",
            "pass": "recapture at least 50 percent of the A3 oracle-minus-pertuned gap in at least 2 of 3 qualified T-limit cells",
            "extension": "if first rung does not pass but recapture_fraction >= 0.15 in at least 1 cell, one 4M-step extension may be preregistered",
            "fail": "if first rung neither passes nor triggers extension; or if the extension later fails its frozen gate",
            "uncertainty": "paired bootstrap CI95 over training seeds and validation rows plus training-seed-clustered SE; uncertainty cannot loosen the gate",
        },
        "quick_mode": {
            "purpose": "protocol check only",
            "training_seeds": [TRAINING_SEEDS[0]],
            "steps_per_seed": QUICK_STEPS_PER_SEED,
            "train_rows_per_level": QUICK_TRAIN_ROWS_PER_LEVEL,
            "validation_rows_per_level": 4,
            "not_a_verdict": True,
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
    if not payload.get("frozen_before_any_c1_v4_stage_b_rollout"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_c1_v4_stage_b_rollout")
    if not payload.get("admission_basis", {}).get("stage_a_pass"):
        raise ValueError("M3247 requires M3246 Stage A pass admission")
    return payload


def _train_and_eval_worker(
    args: tuple[list[dict[str, str]], list[dict[str, str]], int, int, str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    return train_one_seed(*args)


def run(mode: str) -> dict[str, Any]:
    if mode not in {"quick", "stage_b"}:
        raise ValueError(f"unknown mode: {mode}")
    prereg = load_preregistration()
    if not STAGE_A_PRIMARY_CHECKPOINT.exists():
        raise FileNotFoundError(f"missing warm-start checkpoint {STAGE_A_PRIMARY_CHECKPOINT}")
    quick = mode == "quick"
    run_dir = RUN_DIR / ("quick" if quick else "stage_b")
    run_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    t0 = time.time()

    train_rows = sample_training_rows(rows_per_level=QUICK_TRAIN_ROWS_PER_LEVEL if quick else TRAIN_ROWS_PER_LEVEL)
    val_rows = stage_a.validation_rows(limit_per_level=4 if quick else None)
    training_seeds = [TRAINING_SEEDS[0]] if quick else list(TRAINING_SEEDS)
    steps_per_seed = QUICK_STEPS_PER_SEED if quick else STAGE_B_STEPS_PER_SEED
    checkpoint_path = str(STAGE_A_PRIMARY_CHECKPOINT)

    worker_args = [(train_rows, val_rows, seed, steps_per_seed, checkpoint_path, str(run_dir)) for seed in training_seeds]
    if quick or len(worker_args) == 1:
        worker_results = [_train_and_eval_worker(worker_args[0])]
    else:
        ctx = mp.get_context("spawn")
        workers = min(MAX_WORKERS, len(worker_args))
        with ctx.Pool(processes=workers) as pool:
            worker_results = pool.map(_train_and_eval_worker, worker_args)

    training_metrics: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    checkpoints: list[str] = []
    for metrics, rows, checkpoint in worker_results:
        training_metrics.append(metrics)
        candidate_rows.extend(rows)
        checkpoints.append(checkpoint)

    write_csv_rows(run_dir / "training_metrics.csv", training_metrics)
    write_csv_rows(run_dir / "candidate_rows.csv", candidate_rows)
    aggregate = aggregate_results(candidate_rows, val_rows)
    result = {
        "protocol": "c5prime_c1_v4_stage_b_guarded_rl",
        "mode": mode,
        "generated_by": "scripts/feasibility_audit/c5prime_c1_v4_stage_b_guarded_rl.py",
        "generated_at_utc": utc_timestamp(),
        "preregistration": str(PREREG_JSON.relative_to(REPO)),
        "claim_boundary": CLAIM_BOUNDARY,
        "admission_basis": prereg["admission_basis"],
        "pricing_basis": prereg["pricing_basis"],
        "training_design": {
            **prereg["training_design"],
            "train_rows_used": len(train_rows),
            "training_seeds_used": training_seeds,
            "steps_per_seed_used": steps_per_seed,
        },
        "validation_design": {
            **prereg["validation_design"],
            "validation_rows_used": len(val_rows),
        },
        "training_metrics": training_metrics,
        "aggregate": {
            **aggregate,
            "quick_mode_not_a_verdict": quick,
            "track_c_verdict": (
                "quick_only"
                if quick
                else ("pass" if aggregate["stage_b_pass"] else ("extension_admitted" if aggregate["extension_admitted"] else "fail"))
            ),
        },
        "artifacts": {
            "training_metrics_csv": str((run_dir / "training_metrics.csv").relative_to(REPO)),
            "candidate_rows_csv": str((run_dir / "candidate_rows.csv").relative_to(REPO)),
            "checkpoints": checkpoints,
            "progress_glob": str((run_dir / "progress_seed_*.json").relative_to(REPO)),
        },
        "wall_time_s": round(time.time() - t0, 3),
    }
    write_json(QUICK_JSON if quick else RESULTS_JSON, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run C1-v4 Stage B guarded RL.")
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--stage-b", action="store_true")
    args = parser.parse_args()

    if args.write_prereg:
        payload = write_preregistration()
        print(
            f"wrote_prereg={PREREG_JSON} training_seeds={len(payload['training_design']['training_seeds'])} "
            f"validation_rows={len(payload['validation_design']['validation_row_ids'])}"
        )
        if not args.quick and not args.stage_b:
            return
    if args.quick and args.stage_b:
        raise SystemExit("--quick and --stage-b are mutually exclusive")
    if not args.quick and not args.stage_b:
        raise SystemExit("pass --quick or --stage-b")
    result = run("quick" if args.quick else "stage_b")
    aggregate = result["aggregate"]
    print(
        f"mode={result['mode']} stage_b_pass={aggregate['stage_b_pass']} "
        f"extension_admitted={aggregate['extension_admitted']} pass_cells={aggregate['pass_cells']} "
        f"movement_cells={aggregate['movement_cells']} wall_time_s={result['wall_time_s']}"
    )


if __name__ == "__main__":
    main()
