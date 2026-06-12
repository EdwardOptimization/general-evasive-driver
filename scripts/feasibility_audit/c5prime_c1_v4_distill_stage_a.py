"""C1-v4 Stage A distill-then-RL gate on frozen C5-prime cells.

Stage A is a supervised representation and closed-loop gate before any C1-v4
RL is admitted. It trains a bounded residual head to imitate
v4_pertuned(obs) - fixed_v4(obs) on disjoint per-tuned rollouts, then judges the
deterministic closed-loop student against the frozen A3 v4_pertuned floor.

Run:
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_distill_stage_a.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_distill_stage_a.py --quick
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/c5prime_c1_v4_distill_stage_a.py --stage-a
"""

from __future__ import annotations

import argparse
import ast
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
import torch.nn.functional as F

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
import c5prime_c1_v3_residual_rl_smoke as smoke  # noqa: E402
from autodrift.active_safety_reflex_driver import ActiveSafetyReflexDriver  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.evaluate import outcome_bucket_from_info  # noqa: E402
from autodrift.scenarios import classify_obstacle_scenario  # noqa: E402


MILESTONE_ID = "m3246-c1-v4-distill-stage-a"
PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a_prereg.json"
QUICK_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a_quick.json"
RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a.json"
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_v4_distill_stage_a"

SEED_BASE = 20261001
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
TRAIN_ROWS_PER_LEVEL = 8
QUICK_TRAIN_ROWS_PER_LEVEL = 2
QUICK_VALIDATION_ROWS_PER_LEVEL = 4
HIDDEN = 64
BATCH_SIZE = 256
EPOCHS = 600
QUICK_EPOCHS = 80
LEARNING_RATE = 1e-3
PRIMARY_DELTA_MAX = smoke.DELTA_MAX.astype(np.float32)
GATE_WITHIN = 0.05
EXPLORATORY_MARGIN = 1.05

CLAIM_BOUNDARY = (
    "C1-v4 Stage A distillation engineering gate only: a supervised residual "
    "student is trained to imitate v4_pertuned minus frozen v4 on disjoint "
    "current-sim C5-prime training rows, then judged against frozen A3 "
    "v4_pertuned validation rows. No RL, incumbent mutation, validation ranking, "
    "driver-performance claim, high-fidelity sufficiency claim, repair-success "
    "claim, feasibility-proof, paper claim, or self-ID claim."
)

A3_GAPS = {
    "S1": 0.1597,
    "S2": 0.2153,
    "S3": 0.1736,
}


class ResidualDistiller(nn.Module):
    def __init__(self, hidden: int = HIDDEN):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(smoke.OBS_DIM, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, smoke.ACT_DIM),
            nn.Tanh(),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs)

    def act(self, obs: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            obs_t = torch.as_tensor(np.asarray(obs, dtype=np.float32), dtype=torch.float32).unsqueeze(0)
            action = self.forward(obs_t)[0].detach().cpu().numpy()
        return np.clip(action, -1.0, 1.0).astype(np.float32)


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


def _training_seed(level: str, instance: int, scan_k: int) -> int:
    return 8_800_000 + TARGET_LEVELS.index(level) * 200_000 + instance * 5_000 + scan_k * 17


def sample_training_rows(rows_per_level: int = TRAIN_ROWS_PER_LEVEL) -> list[dict[str, str]]:
    """Sample disjoint T-limit rows and attach the per-instance A3 pertuned grid."""

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
                        "pertuned_grid": template["pertuned_grid"],
                        "scan_k": str(scan_k),
                    }
                )
                accepted += 1
            scan_k += 1
        if accepted < rows_per_level:
            raise RuntimeError(f"could not sample {rows_per_level} admitted training rows for {level}")
    return rows


def validation_rows(limit_per_level: int | None = None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for level in TARGET_LEVELS:
        sub = [row for row in _source_rows() if row["level"] == level]
        sub.sort(key=lambda row: (int(row["instance"]), int(row["eval_seed"])))
        out.extend(sub[:limit_per_level] if limit_per_level is not None else sub)
    return out


def pertuned_grid(row: dict[str, str]) -> tuple[float, float, float]:
    parsed = ast.literal_eval(row["pertuned_grid"])
    if not isinstance(parsed, tuple) or len(parsed) != 3:
        raise ValueError(f"bad pertuned_grid: {row['pertuned_grid']!r}")
    grid = tuple(float(value) for value in parsed)
    if grid not in c5.GRID:
        raise ValueError(f"pertuned_grid not in C5 grid: {grid!r}")
    return grid


def pertuned_cfgs(row: dict[str, str]) -> tuple[dict, dict]:
    return c5.grid_cfgs(*pertuned_grid(row))


def teacher_action(obs: np.ndarray, row: dict[str, str]) -> np.ndarray:
    v2cfg, v4cfg = pertuned_cfgs(row)
    return c5.composed_action(obs, v2cfg, v4cfg)


def base_action(base_driver: ActiveSafetyReflexDriver, obs: np.ndarray) -> np.ndarray:
    return np.asarray(base_driver.act(obs), dtype=np.float32)


def _success_from_outcome(outcome: str) -> float:
    return 1.0 if outcome == "success" else 0.0


def collect_distill_dataset(
    rows: list[dict[str, str]],
    delta_max: np.ndarray,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]], dict[str, Any]]:
    base_driver = ActiveSafetyReflexDriver()
    obs_rows: list[np.ndarray] = []
    target_rows: list[np.ndarray] = []
    target_clipped_rows: list[np.ndarray] = []
    delta_rows: list[np.ndarray] = []
    frame_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    delta_max = np.asarray(delta_max, dtype=np.float32)
    target_overbound = np.zeros(smoke.ACT_DIM, dtype=np.int64)
    total_return = 0.0

    for row in rows:
        env = smoke.env_from_source_row(row)
        row_steps = 0
        row_return = 0.0
        try:
            obs, _info = env.reset(seed=int(row["eval_seed"]))
            terminated = truncated = False
            info: dict[str, Any] = {}
            while not (terminated or truncated):
                obs_arr = np.asarray(obs, dtype=np.float32)
                fixed = base_action(base_driver, obs_arr)
                teacher = teacher_action(obs_arr, row)
                delta = (teacher - fixed).astype(np.float32)
                target_units = (delta / delta_max).astype(np.float32)
                target_clipped = np.clip(target_units, -1.0, 1.0).astype(np.float32)
                overbound = np.abs(target_units) > 1.0 + 1e-6

                obs_rows.append(obs_arr.copy())
                target_rows.append(target_units)
                target_clipped_rows.append(target_clipped)
                delta_rows.append(delta)
                target_overbound += overbound.astype(np.int64)
                frame_rows.append(
                    {
                        "row_id": smoke.row_id(row),
                        "level": row["level"],
                        "instance": int(row["instance"]),
                        "eval_seed": int(row["eval_seed"]),
                        "step": row_steps,
                        "target_steer_unit": float(target_units[0]),
                        "target_throttle_unit": float(target_units[1]),
                        "target_brake_unit": float(target_units[2]),
                        "overbound_steer": bool(overbound[0]),
                        "overbound_throttle": bool(overbound[1]),
                        "overbound_brake": bool(overbound[2]),
                    }
                )

                obs, reward, terminated, truncated, info = env.step(teacher)
                row_return += float(reward)
                total_return += float(reward)
                row_steps += 1
            bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            outcome = c5.failure_mode(bucket, str(info.get("termination_reason", "") or ""))
            rollout_rows.append(
                {
                    "row_id": smoke.row_id(row),
                    "level": row["level"],
                    "instance": int(row["instance"]),
                    "eval_seed": int(row["eval_seed"]),
                    "pertuned_grid": row["pertuned_grid"],
                    "teacher_outcome": outcome,
                    "teacher_steps": row_steps,
                    "teacher_return": float(row_return),
                }
            )
        finally:
            env.close()

    if not obs_rows:
        raise RuntimeError("distillation dataset is empty")
    obs_array = np.stack(obs_rows).astype(np.float32)
    target_array = np.stack(target_rows).astype(np.float32)
    target_clipped_array = np.stack(target_clipped_rows).astype(np.float32)
    delta_array = np.stack(delta_rows).astype(np.float32)
    max_abs_target_units = np.max(np.abs(target_array), axis=0)
    max_abs_delta = np.max(np.abs(delta_array), axis=0)
    dataset = {
        "obs": obs_array,
        "target_units": target_array,
        "target_clipped": target_clipped_array,
        "delta": delta_array,
    }
    summary = {
        "n_rows": len(rows),
        "n_frames": int(obs_array.shape[0]),
        "delta_max": delta_max.tolist(),
        "target_max_abs_units": [round(float(value), 6) for value in max_abs_target_units],
        "target_max_abs_delta": [round(float(value), 6) for value in max_abs_delta],
        "target_overbound_frames_by_channel": [int(value) for value in target_overbound.tolist()],
        "target_overbound_total_frames": int(np.any(np.abs(target_array) > 1.0 + 1e-6, axis=1).sum()),
        "target_overbound_share": round(float(np.any(np.abs(target_array) > 1.0 + 1e-6, axis=1).mean()), 6),
        "primary_representation_fits_delta_max": bool(np.all(max_abs_target_units <= 1.0 + 1e-6)),
        "teacher_success": round(float(np.mean([_success_from_outcome(row["teacher_outcome"]) for row in rollout_rows])), 4),
        "teacher_return_mean": round(float(total_return / len(rows)), 4),
    }
    return dataset, rollout_rows, summary


def exploratory_delta_max_from_dataset(dataset: dict[str, np.ndarray]) -> np.ndarray:
    max_abs_delta = np.max(np.abs(dataset["delta"]), axis=0).astype(np.float32)
    return np.maximum(PRIMARY_DELTA_MAX, max_abs_delta * EXPLORATORY_MARGIN).astype(np.float32)


def _train_val_indices(n_frames: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng([SEED_BASE, seed, n_frames])
    indices = np.arange(n_frames)
    rng.shuffle(indices)
    split = max(1, int(n_frames * 0.8))
    train_idx = indices[:split]
    val_idx = indices[split:]
    if len(val_idx) == 0:
        val_idx = indices[:1]
    return train_idx, val_idx


def train_model(
    dataset: dict[str, np.ndarray],
    *,
    seed: int,
    epochs: int,
    run_dir: Path,
    arm_name: str,
) -> tuple[ResidualDistiller, dict[str, Any], list[dict[str, Any]]]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = ResidualDistiller()
    optimizer = Adam(model.parameters(), lr=LEARNING_RATE)
    obs_t = torch.as_tensor(dataset["obs"], dtype=torch.float32)
    target_t = torch.as_tensor(dataset["target_clipped"], dtype=torch.float32)
    train_idx, val_idx = _train_val_indices(len(obs_t), seed)
    train_rows: list[dict[str, Any]] = []
    losses: list[float] = []
    batch_size = min(BATCH_SIZE, len(train_idx))

    for epoch in range(1, epochs + 1):
        epoch_idx = train_idx.copy()
        np.random.shuffle(epoch_idx)
        batch_losses: list[float] = []
        for start in range(0, len(epoch_idx), batch_size):
            mb = epoch_idx[start : start + batch_size]
            pred = model(obs_t[mb])
            loss = F.mse_loss(pred, target_t[mb])
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            batch_losses.append(float(loss.detach().cpu().item()))
        if epoch == 1 or epoch == epochs or epoch % max(1, epochs // 10) == 0:
            with torch.no_grad():
                train_loss = F.mse_loss(model(obs_t[train_idx]), target_t[train_idx]).item()
                val_loss = F.mse_loss(model(obs_t[val_idx]), target_t[val_idx]).item()
            losses.append(float(val_loss))
            train_rows.append(
                {
                    "arm": arm_name,
                    "epoch": epoch,
                    "batch_loss_mean": float(np.mean(batch_losses)),
                    "train_mse": float(train_loss),
                    "val_mse": float(val_loss),
                }
            )

    with torch.no_grad():
        pred_all = model(obs_t).detach().cpu().numpy()
    target_all = dataset["target_clipped"]
    channel_mse = np.mean(np.square(pred_all - target_all), axis=0)
    metrics = {
        "arm": arm_name,
        "seed": seed,
        "epochs": epochs,
        "frames": int(len(obs_t)),
        "train_frames": int(len(train_idx)),
        "val_frames": int(len(val_idx)),
        "initial_logged_val_mse": float(train_rows[0]["val_mse"]),
        "final_val_mse": float(train_rows[-1]["val_mse"]),
        "final_train_mse": float(train_rows[-1]["train_mse"]),
        "channel_mse": [round(float(value), 6) for value in channel_mse],
    }
    torch.save(
        {
            "protocol": "c5prime_c1_v4_distill_stage_a",
            "arm": arm_name,
            "seed": seed,
            "model_state": model.state_dict(),
            "model_config": {"obs_dim": smoke.OBS_DIM, "act_dim": smoke.ACT_DIM, "hidden": HIDDEN},
        },
        run_dir / f"{arm_name}_distiller.pt",
    )
    return model, metrics, train_rows


def evaluate_model(
    model: ResidualDistiller,
    rows: list[dict[str, str]],
    delta_max: np.ndarray,
    arm_name: str,
) -> list[dict[str, Any]]:
    base_driver = ActiveSafetyReflexDriver()
    delta_max = np.asarray(delta_max, dtype=np.float32)
    out: list[dict[str, Any]] = []
    model.eval()
    for row in rows:
        env = smoke.env_from_source_row(row)
        steps = 0
        total_return = 0.0
        delta_abs_max = np.zeros(smoke.ACT_DIM, dtype=np.float32)
        try:
            obs, _info = env.reset(seed=int(row["eval_seed"]))
            terminated = truncated = False
            info: dict[str, Any] = {}
            while not (terminated or truncated):
                residual_unit = model.act(obs)
                fixed = base_action(base_driver, obs)
                _base, delta, final = smoke.compose_residual_action(fixed, residual_unit, delta_max=delta_max)
                delta_abs_max = np.maximum(delta_abs_max, np.abs(delta))
                obs, reward, terminated, truncated, info = env.step(final)
                total_return += float(reward)
                steps += 1
            bucket = outcome_bucket_from_info(info, terminated=terminated, truncated=truncated)
            outcome = c5.failure_mode(bucket, str(info.get("termination_reason", "") or ""))
            out.append(
                {
                    "arm": arm_name,
                    "row_id": smoke.row_id(row),
                    "level": row["level"],
                    "instance": int(row["instance"]),
                    "eval_seed": int(row["eval_seed"]),
                    "fixed_v4_outcome": row["fixed_v4_incumbent_outcome"],
                    "v4_pertuned_outcome": row["v4_pertuned_outcome"],
                    "oracle_solved": row["oracle_solved"] == "True",
                    "candidate_outcome": outcome,
                    "candidate_steps": steps,
                    "candidate_return": float(total_return),
                    "max_abs_delta_steer": float(delta_abs_max[0]),
                    "max_abs_delta_throttle": float(delta_abs_max[1]),
                    "max_abs_delta_brake": float(delta_abs_max[2]),
                }
            )
        finally:
            env.close()
    return out


def _paired_bootstrap_ci(candidate: np.ndarray, baseline: np.ndarray, rng: np.random.Generator) -> list[float]:
    if candidate.shape != baseline.shape:
        raise ValueError(f"candidate shape {candidate.shape} != baseline shape {baseline.shape}")
    diffs = []
    n = len(candidate)
    for _ in range(2000):
        idx = rng.integers(0, n, size=n)
        diffs.append(float(candidate[idx].mean() - baseline[idx].mean()))
    return [round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)]


def aggregate_candidate(
    candidate_rows: list[dict[str, Any]],
    val_rows: list[dict[str, str]],
    *,
    arm_name: str,
) -> dict[str, Any]:
    by_row_id = {smoke.row_id(row): row for row in val_rows}
    candidate_by_id = {row["row_id"]: row for row in candidate_rows if row["arm"] == arm_name}
    cells: dict[str, Any] = {}
    rng = np.random.default_rng([SEED_BASE, 44, len(candidate_rows)])
    for level in TARGET_LEVELS:
        row_ids = [smoke.row_id(row) for row in val_rows if row["level"] == level]
        missing = [row_id for row_id in row_ids if row_id not in candidate_by_id]
        if missing:
            raise ValueError(f"missing candidate rows for {arm_name}: {missing[:3]}")
        fixed_v4 = np.asarray(
            [_success_from_outcome(by_row_id[row_id]["fixed_v4_incumbent_outcome"]) for row_id in row_ids],
            dtype=np.float64,
        )
        pertuned = np.asarray(
            [_success_from_outcome(by_row_id[row_id]["v4_pertuned_outcome"]) for row_id in row_ids],
            dtype=np.float64,
        )
        oracle = np.asarray([1.0 if by_row_id[row_id]["oracle_solved"] == "True" else 0.0 for row_id in row_ids])
        candidate = np.asarray(
            [_success_from_outcome(candidate_by_id[row_id]["candidate_outcome"]) for row_id in row_ids],
            dtype=np.float64,
        )
        gap = float(candidate.mean() - pertuned.mean())
        cell_pass = bool(gap >= -GATE_WITHIN)
        cells[f"{level}/T_limit"] = {
            "n_validation_rows": len(row_ids),
            "fixed_v4_success": round(float(fixed_v4.mean()), 4),
            "v4_pertuned_success": round(float(pertuned.mean()), 4),
            "oracle_success": round(float(oracle.mean()), 4),
            "candidate_success": round(float(candidate.mean()), 4),
            "candidate_minus_pertuned": round(gap, 4),
            "candidate_minus_pertuned_paired_bootstrap_ci95": _paired_bootstrap_ci(candidate, pertuned, rng),
            "a3_oracle_minus_pertuned_gap": round(float(A3_GAPS[level]), 4),
            "within_0p05": cell_pass,
            "cell_pass": cell_pass,
            "paired_disagreements": int(np.sum(candidate != pertuned)),
            "candidate_successes": int(candidate.sum()),
            "pertuned_successes": int(pertuned.sum()),
        }
    pass_cells = [cell for cell, summary in cells.items() if summary["cell_pass"]]
    return {
        "arm": arm_name,
        "cells": cells,
        "pass_cells": pass_cells,
        "n_pass_cells": len(pass_cells),
        "stage_a_pass": len(pass_cells) == len(TARGET_LEVELS),
        "decision_rule": "PASS iff candidate_success - v4_pertuned_success >= -0.05 in all S1/S2/S3 T-limit cells; bootstrap CI is reported and cannot loosen the gate.",
    }


def preregistration_payload() -> dict[str, Any]:
    train_rows = sample_training_rows()
    val_rows = validation_rows()
    train_eval_seeds = [int(row["eval_seed"]) for row in train_rows]
    validation_eval_seeds = [int(row["eval_seed"]) for row in val_rows]
    return {
        "protocol": "c5prime_c1_v4_distill_stage_a",
        "milestone_id": MILESTONE_ID,
        "roadmap_unit": "C1-v4 distill-then-RL Stage A",
        "frozen_at_utc": "2026-06-12T00:00:00Z",
        "frozen_before_any_c1_v4_stage_a_rollout": True,
        "final_attempt_clause": "C1-v4 is the final pre-registered learning attempt at the C5-prime prize; Stage A failure stops before RL.",
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
            "seed_base": SEED_BASE,
            "train_rows_per_level": TRAIN_ROWS_PER_LEVEL,
            "train_row_ids": [smoke.row_id(row) for row in train_rows],
            "train_eval_seeds": train_eval_seeds,
            "teacher": "per-instance v4_pertuned reconstructed from A3 pertuned_grid",
            "base_policy": "ActiveSafetyReflexDriver incumbent v4, frozen",
            "student": {
                "architecture": "obs72 -> MLP(64,64) -> tanh(3)",
                "primary_delta_max": PRIMARY_DELTA_MAX.tolist(),
                "loss": "MSE on clipped residual units (teacher - fixed_v4) / delta_max",
                "epochs": EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
            },
            "exploratory_arm": {
                "enabled_if_primary_targets_exceed_bounds": True,
                "delta_max_rule": "max(primary_delta_max, 1.05 * max_abs_teacher_minus_base_delta_on_training_frames)",
                "not_a_gate": True,
            },
        },
        "validation_design": {
            "validation_source": str(smoke.SOURCE_ROWS_CSV.relative_to(REPO)),
            "validation_cells": [f"{level}/T_limit" for level in TARGET_LEVELS],
            "validation_rows_per_cell": 144,
            "validation_row_ids": [smoke.row_id(row) for row in val_rows],
            "floor": "A3 v4_pertuned_outcome on the same validation rows",
            "candidate": "deterministic distilled residual over frozen v4",
        },
        "seed_discipline": {
            "new_seed_base": SEED_BASE,
            "training_eval_seed_stream": "8_800_000 + level*200_000 + instance*5_000 + scan_k*17",
            "training_eval_seeds_disjoint_from_validation": set(train_eval_seeds).isdisjoint(validation_eval_seeds),
            "training_eval_seeds_disjoint_from_m3245": True,
            "model_seed": SEED_BASE + 17,
        },
        "decision_rule": {
            "primary_gate": "primary distilled residual with M3245 delta_max must be within 0.05 paired success of v4_pertuned in all three cells",
            "pass": "candidate_success - v4_pertuned_success >= -0.05 in S1, S2, and S3 T-limit",
            "fail": "otherwise; stop before Stage B RL",
            "exploratory": "wider delta_max arm is reported only if representation check fails and cannot admit RL",
        },
        "quick_mode": {
            "purpose": "protocol check only",
            "train_rows_per_level": QUICK_TRAIN_ROWS_PER_LEVEL,
            "validation_rows_per_level": QUICK_VALIDATION_ROWS_PER_LEVEL,
            "epochs": QUICK_EPOCHS,
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
    if not payload.get("frozen_before_any_c1_v4_stage_a_rollout"):
        raise ValueError(f"{PREREG_JSON} is not marked frozen_before_any_c1_v4_stage_a_rollout")
    return payload


def run(mode: str) -> dict[str, Any]:
    if mode not in {"quick", "stage_a"}:
        raise ValueError(f"unknown mode: {mode}")
    prereg = load_preregistration()
    quick = mode == "quick"
    run_dir = RUN_DIR / ("quick" if quick else "stage_a")
    run_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    t0 = time.time()

    train_rows = sample_training_rows(rows_per_level=QUICK_TRAIN_ROWS_PER_LEVEL if quick else TRAIN_ROWS_PER_LEVEL)
    val_rows = validation_rows(limit_per_level=QUICK_VALIDATION_ROWS_PER_LEVEL if quick else None)
    epochs = QUICK_EPOCHS if quick else EPOCHS
    model_seed = SEED_BASE + (3 if quick else 17)

    primary_dataset, teacher_rollouts, primary_dataset_summary = collect_distill_dataset(
        train_rows,
        PRIMARY_DELTA_MAX,
    )
    primary_model, primary_train_summary, primary_training_rows = train_model(
        primary_dataset,
        seed=model_seed,
        epochs=epochs,
        run_dir=run_dir,
        arm_name="primary",
    )
    primary_candidate_rows = evaluate_model(primary_model, val_rows, PRIMARY_DELTA_MAX, "primary")
    primary_aggregate = aggregate_candidate(primary_candidate_rows, val_rows, arm_name="primary")

    exploratory_delta = exploratory_delta_max_from_dataset(primary_dataset)
    exploratory_ran = bool(np.any(exploratory_delta > PRIMARY_DELTA_MAX + 1e-6))
    exploratory_dataset_summary: dict[str, Any] | None = None
    exploratory_train_summary: dict[str, Any] | None = None
    exploratory_training_rows: list[dict[str, Any]] = []
    exploratory_candidate_rows: list[dict[str, Any]] = []
    exploratory_aggregate: dict[str, Any] | None = None
    if exploratory_ran:
        exploratory_dataset, _teacher_rollouts2, exploratory_dataset_summary = collect_distill_dataset(
            train_rows,
            exploratory_delta,
        )
        exploratory_model, exploratory_train_summary, exploratory_training_rows = train_model(
            exploratory_dataset,
            seed=model_seed + 1,
            epochs=epochs,
            run_dir=run_dir,
            arm_name="exploratory",
        )
        exploratory_candidate_rows = evaluate_model(
            exploratory_model,
            val_rows,
            exploratory_delta,
            "exploratory",
        )
        exploratory_aggregate = aggregate_candidate(exploratory_candidate_rows, val_rows, arm_name="exploratory")

    write_csv_rows(run_dir / "teacher_rollout_rows.csv", teacher_rollouts)
    write_csv_rows(run_dir / "training_metrics.csv", primary_training_rows + exploratory_training_rows)
    write_csv_rows(run_dir / "candidate_rows_primary.csv", primary_candidate_rows)
    if exploratory_candidate_rows:
        write_csv_rows(run_dir / "candidate_rows_exploratory.csv", exploratory_candidate_rows)
    np.savez_compressed(
        run_dir / "distill_dataset_primary.npz",
        obs=primary_dataset["obs"],
        target_units=primary_dataset["target_units"],
        target_clipped=primary_dataset["target_clipped"],
        delta=primary_dataset["delta"],
    )

    result = {
        "protocol": "c5prime_c1_v4_distill_stage_a",
        "mode": mode,
        "generated_by": "scripts/feasibility_audit/c5prime_c1_v4_distill_stage_a.py",
        "generated_at_utc": utc_timestamp(),
        "preregistration": str(PREREG_JSON.relative_to(REPO)),
        "claim_boundary": CLAIM_BOUNDARY,
        "pricing_basis": prereg["pricing_basis"],
        "training_design": {
            **prereg["training_design"],
            "train_rows_used": len(train_rows),
            "epochs_used": epochs,
            "model_seed_used": model_seed,
        },
        "validation_design": {
            **prereg["validation_design"],
            "validation_rows_used": len(val_rows),
        },
        "representation_check": {
            "primary": primary_dataset_summary,
            "exploratory_delta_max": [round(float(value), 6) for value in exploratory_delta.tolist()],
            "exploratory_ran": exploratory_ran,
            "exploratory": exploratory_dataset_summary,
        },
        "train_summary": {
            "primary": primary_train_summary,
            "exploratory": exploratory_train_summary,
        },
        "aggregate": {
            "primary": primary_aggregate,
            "exploratory": exploratory_aggregate,
            "stage_a_pass": bool(primary_aggregate["stage_a_pass"] and not quick),
            "quick_mode_not_a_verdict": quick,
            "stage_b_admitted": bool(primary_aggregate["stage_a_pass"] and not quick),
            "decision_rule": prereg["decision_rule"],
        },
        "artifacts": {
            "teacher_rollout_rows_csv": str((run_dir / "teacher_rollout_rows.csv").relative_to(REPO)),
            "training_metrics_csv": str((run_dir / "training_metrics.csv").relative_to(REPO)),
            "candidate_rows_primary_csv": str((run_dir / "candidate_rows_primary.csv").relative_to(REPO)),
            "candidate_rows_exploratory_csv": (
                str((run_dir / "candidate_rows_exploratory.csv").relative_to(REPO))
                if exploratory_candidate_rows
                else None
            ),
            "distill_dataset_primary_npz": str((run_dir / "distill_dataset_primary.npz").relative_to(REPO)),
            "primary_checkpoint": str((run_dir / "primary_distiller.pt").relative_to(REPO)),
            "exploratory_checkpoint": (
                str((run_dir / "exploratory_distiller.pt").relative_to(REPO)) if exploratory_candidate_rows else None
            ),
        },
        "wall_time_s": round(time.time() - t0, 3),
    }
    write_json(QUICK_JSON if quick else RESULTS_JSON, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run C1-v4 Stage A distillation gate.")
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--stage-a", action="store_true")
    args = parser.parse_args()

    if args.write_prereg:
        payload = write_preregistration()
        print(
            f"wrote_prereg={PREREG_JSON} train_rows={len(payload['training_design']['train_row_ids'])} "
            f"validation_rows={len(payload['validation_design']['validation_row_ids'])}"
        )
        if not args.quick and not args.stage_a:
            return
    if args.quick and args.stage_a:
        raise SystemExit("--quick and --stage-a are mutually exclusive")
    if not args.quick and not args.stage_a:
        raise SystemExit("pass --quick or --stage-a")
    result = run("quick" if args.quick else "stage_a")
    primary = result["aggregate"]["primary"]
    print(
        f"mode={result['mode']} stage_a_pass={result['aggregate']['stage_a_pass']} "
        f"primary_pass_cells={primary['pass_cells']} exploratory_ran={result['representation_check']['exploratory_ran']} "
        f"wall_time_s={result['wall_time_s']}"
    )


if __name__ == "__main__":
    main()
