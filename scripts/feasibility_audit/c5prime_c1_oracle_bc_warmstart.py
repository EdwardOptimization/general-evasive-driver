"""C1 C5-prime oracle-demo generator + BC warm-start smoke.

This is the first executable Track-C unit after CP-1 conditional approval. It
uses the frozen A3 C5-prime target rows, replays only reproducible structured
oracle actions, and trains a small behavior-cloned warm-start policy with
held-out epoch selection. The output is engineering-only warm-start evidence,
not validation, ranking, promotion, high-fidelity, or self-ID evidence.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py --quick
    PYTHONPATH=src python scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py --full
    PYTHONPATH=src python scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py --revision v2_tail_balanced --write-prereg
    PYTHONPATH=src python scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py --revision v2_tail_balanced --quick
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import c5_reflex_degradation as c5  # noqa: E402
from autodrift.artifacts import utc_timestamp, write_json  # noqa: E402
from autodrift.env import AutoDriftEnv  # noqa: E402
from autodrift.evaluate import outcome_bucket_from_info  # noqa: E402
from autodrift.train_ppo import ActorCritic  # noqa: E402


PREREG_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_prereg.json"
RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart.json"
QUICK_RESULTS_JSON = (
    REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart_quick.json"
)
PREREG_JSON_V2 = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_v2_prereg.json"
RESULTS_JSON_V2 = REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart_v2.json"
QUICK_RESULTS_JSON_V2 = (
    REPO / "experiments" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart_v2_quick.json"
)
RUN_DIR = REPO / "runs" / "feasibility_audit" / "c5prime_c1_oracle_bc_warmstart"
SOURCE_ROWS_CSV = REPO / "runs" / "feasibility_audit" / "c5prime_target_consolidation" / "episode_rows.csv"
SOURCE_RESULTS_JSON = REPO / "experiments" / "feasibility_audit" / "c5prime_target_consolidation.json"

SEED_BASE = 20260817
SEED_BASE_V2 = 20260819
REVISION_M3228 = "m3228"
REVISION_V2 = "v2_tail_balanced"
REVISIONS = (REVISION_M3228, REVISION_V2)
TARGET_LEVELS = ("S1", "S2", "S3")
SURFACE = "T_limit"
OBS_DIM = 72
ACT_DIM = 3
HIDDEN = 128
ROLE_MOD = 6
ROLE_BY_MOD = {0: "validation", 1: "selection"}
RARE_TAIL_ORACLES_V2 = ("structured:coast_steer_+0.7", "structured:coast_steer_-0.7")

CLAIM_BOUNDARY = (
    "C1 C5-prime oracle-demo and behavior-cloning warm-start engineering only: "
    "structured A3 oracle rows are replayed in current-sim, a small BC policy is "
    "fit with held-out epoch selection and a DAgger-lite relabeling pass, and the "
    "result is a warm-start artifact for later guarded stages. No incumbent driver "
    "mutation, validation ranking, promotion, high-fidelity sufficiency, paper, "
    "repair-success, robustness-result, feasibility-proof, or self-ID claim."
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _stable_hash(*parts: object) -> str:
    return hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _role_for(level: str, instance: int, eval_seed: int, *, seed_base: int = SEED_BASE) -> str:
    value = int(_stable_hash(seed_base, "role", level, instance, eval_seed)[:8], 16)
    return ROLE_BY_MOD.get(value % ROLE_MOD, "train")


def _eligible_rows() -> list[dict[str, str]]:
    rows = _read_csv(SOURCE_ROWS_CSV)
    return [
        row
        for row in rows
        if row.get("level") in TARGET_LEVELS
        and row.get("surface") == SURFACE
        and row.get("oracle_solved") == "True"
        and str(row.get("oracle_by", "")).startswith("structured:")
    ]


def _source_row_id(row: dict[str, str]) -> str:
    return f"{row['level']}-inst{int(row['instance']):02d}-seed{int(row['eval_seed'])}"


def _selected_record(row: dict[str, str], *, role: str, selection_source: str) -> dict[str, Any]:
    return {
        "row_id": _source_row_id(row),
        "level": row["level"],
        "surface": SURFACE,
        "instance": int(row["instance"]),
        "eval_seed": int(row["eval_seed"]),
        "bc_role": role,
        "oracle_by": row["oracle_by"],
        "v4_pertuned_outcome": row["v4_pertuned_outcome"],
        "gap_row": row["v4_pertuned_outcome"] != "success",
        "reveal_step": int(row["reveal_step"]),
        "pertuned_grid": list(ast.literal_eval(row["pertuned_grid"])),
        "selection_source": selection_source,
    }


def select_prereg_rows() -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    rows = _eligible_rows()
    for level in TARGET_LEVELS:
        for instance in range(12):
            candidates = [
                row for row in rows if row["level"] == level and int(row["instance"]) == instance
            ]
            if not candidates:
                raise RuntimeError(f"missing structured oracle row for {level}/inst{instance}")
            candidates.sort(
                key=lambda row: (
                    _stable_hash(SEED_BASE, "select", level, instance, row["eval_seed"]),
                    int(row["eval_seed"]),
                )
            )
            row = candidates[0]
            eval_seed = int(row["eval_seed"])
            selected.append(_selected_record(row, role=_role_for(level, instance, eval_seed), selection_source="base"))
    return selected


def select_prereg_rows_v2() -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    eligible = _eligible_rows()
    selected_ids: set[str] = set()
    for level in TARGET_LEVELS:
        for instance in range(12):
            candidates = [
                row for row in eligible if row["level"] == level and int(row["instance"]) == instance
            ]
            if not candidates:
                raise RuntimeError(f"missing structured oracle row for {level}/inst{instance}")
            candidates.sort(
                key=lambda row: (
                    _stable_hash(SEED_BASE_V2, "select", level, instance, row["eval_seed"]),
                    int(row["eval_seed"]),
                )
            )
            row = candidates[0]
            eval_seed = int(row["eval_seed"])
            selected.append(
                _selected_record(
                    row,
                    role=_role_for(level, instance, eval_seed, seed_base=SEED_BASE_V2),
                    selection_source="base",
                )
            )
            selected_ids.add(_source_row_id(row))

    def ensure_oracle_role(oracle_by: str, role: str, selection_source: str) -> None:
        nonlocal selected_ids
        if any(row["oracle_by"] == oracle_by and row["bc_role"] == role for row in selected):
            return
        candidates = [
            row
            for row in eligible
            if row["oracle_by"] == oracle_by and _source_row_id(row) not in selected_ids
        ]
        if not candidates:
            raise RuntimeError(f"cannot add v2 {role} row for required oracle family {oracle_by}")
        candidates.sort(
            key=lambda row: (
                _stable_hash(SEED_BASE_V2, selection_source, oracle_by, row["level"], row["instance"], row["eval_seed"]),
                row["level"],
                int(row["instance"]),
                int(row["eval_seed"]),
            )
        )
        chosen = candidates[0]
        selected.append(_selected_record(chosen, role=role, selection_source=selection_source))
        selected_ids.add(_source_row_id(chosen))

    for oracle_by in RARE_TAIL_ORACLES_V2:
        ensure_oracle_role(oracle_by, "train", "rare_tail_train_support")
        ensure_oracle_role(oracle_by, "validation", "rare_tail_validation_probe")

    train_oracles = {row["oracle_by"] for row in selected if row["bc_role"] == "train"}
    heldout_oracles = {row["oracle_by"] for row in selected if row["bc_role"] in {"selection", "validation"}}
    missing_support = sorted(heldout_oracles - train_oracles)
    for oracle_by in missing_support:
        candidates = [
            row
            for row in eligible
            if row["oracle_by"] == oracle_by and _source_row_id(row) not in selected_ids
        ]
        if not candidates:
            raise RuntimeError(f"cannot add v2 train support row for held-out oracle family {oracle_by}")
        candidates.sort(
            key=lambda row: (
                _stable_hash(SEED_BASE_V2, "support", oracle_by, row["level"], row["instance"], row["eval_seed"]),
                row["level"],
                int(row["instance"]),
                int(row["eval_seed"]),
            )
        )
        support = candidates[0]
        selected.append(_selected_record(support, role="train", selection_source="heldout_oracle_family_support"))
        selected_ids.add(_source_row_id(support))
    return selected


def _paths_for_revision(revision: str) -> tuple[Path, Path, Path, Path]:
    if revision == REVISION_M3228:
        return PREREG_JSON, RESULTS_JSON, QUICK_RESULTS_JSON, RUN_DIR
    if revision == REVISION_V2:
        return PREREG_JSON_V2, RESULTS_JSON_V2, QUICK_RESULTS_JSON_V2, RUN_DIR / "v2_tail_balanced"
    raise ValueError(f"unknown C1 revision {revision!r}")


def _seed_base_for_revision(revision: str) -> int:
    if revision == REVISION_M3228:
        return SEED_BASE
    if revision == REVISION_V2:
        return SEED_BASE_V2
    raise ValueError(f"unknown C1 revision {revision!r}")


def build_preregistration(revision: str = REVISION_M3228) -> dict[str, Any]:
    rows = select_prereg_rows_v2() if revision == REVISION_V2 else select_prereg_rows()
    seed_base = _seed_base_for_revision(revision)
    role_counts = {role: sum(row["bc_role"] == role for row in rows) for role in ("train", "selection", "validation")}
    train_oracles = sorted({row["oracle_by"] for row in rows if row["bc_role"] == "train"})
    heldout_oracles = sorted({row["oracle_by"] for row in rows if row["bc_role"] in {"selection", "validation"}})
    return {
        "protocol": "c5prime_c1_oracle_bc_warmstart_preregistration",
        "revision": revision,
        "roadmap_unit": "C1 Oracle demo generator + BC warm-start",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_c1_rollout": True,
        "seed_base": seed_base,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": {
            "a3_summary_json": str(SOURCE_RESULTS_JSON),
            "a3_episode_rows_csv": str(SOURCE_ROWS_CSV),
            "a3_prereg": "experiments/feasibility_audit/c5prime_prereg.json",
        },
        "selection_rule": {
            "target_cells": [f"{level}/{SURFACE}" for level in TARGET_LEVELS],
            "rows": "one reproducible structured-oracle A3 row per target level x instance",
            "row_filter": "oracle_solved == True and oracle_by starts with structured:",
            "sort_key": f"sha256({seed_base}:select:<level>:<instance>:<eval_seed>), then eval_seed",
            "role_split": f"sha256({seed_base}:role:<level>:<instance>:<eval_seed>) % 6 => 0 validation, 1 selection, else train",
            "role_counts": role_counts,
            "v2_tail_balanced_rule": (
                "if revision == v2_tail_balanced, add distinct train-role support and validation "
                "probe rows for rare coast-steer tail families, then add train-role support rows "
                "for any other oracle_by action family present in selection/validation but absent "
                "from train"
            ),
            "v2_required_rare_tail_oracles": list(RARE_TAIL_ORACLES_V2),
            "train_oracle_families": train_oracles,
            "heldout_oracle_families": heldout_oracles,
        },
        "selected_rows": rows,
        "bc_protocol": {
            "model": "ActorCritic(obs_dim=72, act_dim=3, hidden_size=128, actor_encoder=mlp)",
            "target": "tanh(actor_mean(obs)) fitted to structured-oracle action labels",
            "initial_bc_epochs": {"quick": 4, "full": 12},
            "final_bc_epochs": {"quick": 12, "full": 60},
            "dagger_lite": (
                "after initial BC, roll the model on train-role rows and relabel visited "
                "states with the same frozen structured-oracle step rule; cap 80 steps/row"
            ),
            "epoch_selection": "lowest selection-role action MSE; validation-role rows reported only after selection",
            "primary_smoke_gate": "validation action MSE <= 0.12 and at least 25% lower than zero-action baseline MSE",
            "v2_revision_motivation": (
                "M3229 localized the first failure to selection/validation tail-action generalization, "
                "especially held-out coast-steer tails absent from train. The v2 revision freezes "
                "oracle-family support before rollout instead of relaxing the MSE gate."
            ),
        },
        "runtime_gates": [
            "preregistration file exists and is marked frozen before any C1 rollout",
            "all demo reset observations are finite obs72",
            "all replayed structured-oracle demos succeed on the selected rows",
            "BC checkpoint and dataset artifacts are written",
            "validation action MSE clears the frozen smoke gate",
        ],
        "decision_rule": (
            "The C1 warm-start smoke completes if the selected structured-oracle "
            "demos replay successfully, the BC checkpoint is written, held-out epoch "
            "selection is used, and the validation action-MSE gate passes. BC rollout "
            "success is reported as context only and is not a driver-performance claim."
        ),
    }


def write_preregistration(path: Path | None = None, revision: str = REVISION_M3228) -> dict[str, Any]:
    prereg_path, _results_path, _quick_path, _run_root = _paths_for_revision(revision)
    payload = build_preregistration(revision=revision)
    path = path or prereg_path
    write_json(path, payload)
    return payload


def load_preregistration(revision: str = REVISION_M3228) -> dict[str, Any]:
    prereg_path, _results_path, _quick_path, _run_root = _paths_for_revision(revision)
    if not prereg_path.exists():
        raise FileNotFoundError(f"missing preregistration {prereg_path}; run --write-prereg first")
    payload = json.loads(prereg_path.read_text(encoding="utf-8"))
    if not payload.get("frozen_before_any_c1_rollout"):
        raise ValueError(f"{prereg_path} is not marked frozen_before_any_c1_rollout")
    if payload.get("revision", REVISION_M3228) != revision:
        raise ValueError(f"{prereg_path} revision {payload.get('revision')} != requested {revision}")
    return payload


def _source_row_by_id() -> dict[str, dict[str, str]]:
    out = {}
    for row in _read_csv(SOURCE_ROWS_CSV):
        row_id = f"{row['level']}-inst{int(row['instance']):02d}-seed{int(row['eval_seed'])}"
        out[row_id] = row
    return out


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


def _env_from_row(row: dict[str, str]) -> AutoDriftEnv:
    cfg = c5.row_env_config(
        row["surface"],
        float(row["v"]),
        float(row["mu"]),
        float(row["s_arc"]),
        float(row["hw"]),
        _veh_from_row(row),
    )
    return AutoDriftEnv(cfg)


def structured_tail_action(oracle_by: str, rel_step: int) -> np.ndarray:
    name = oracle_by.removeprefix("structured:")
    if name == "full_brake":
        return np.array([0.0, -1.0, 1.0], dtype=np.float32)
    match = re.fullmatch(r"brake_steer_([+-]\d(?:\.\d)?)", name)
    if match:
        return np.array([float(match.group(1)), -1.0, 1.0], dtype=np.float32)
    match = re.fullmatch(r"coast_steer_([+-]\d(?:\.\d)?)", name)
    if match:
        return np.array([float(match.group(1)), -1.0, -1.0], dtype=np.float32)
    match = re.fullmatch(r"swerve_([+-]\d)_n(\d+)", name)
    if match:
        steer = float(match.group(1))
        cutoff = int(match.group(2))
        if rel_step < cutoff:
            return np.array([steer, -1.0, 1.0], dtype=np.float32)
        return np.array([0.0, -1.0, 1.0], dtype=np.float32)
    raise ValueError(f"unsupported structured oracle action: {oracle_by}")


def _fixed_star_cfg() -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(SOURCE_RESULTS_JSON.read_text(encoding="utf-8"))
    grid = tuple(float(x) for x in data["fixed_star"]["grid"])
    return c5.grid_cfgs(*grid)


def oracle_action(obs: np.ndarray, step: int, reveal_step: int, oracle_by: str, fixed_cfg: tuple[dict, dict]) -> np.ndarray:
    if step < reveal_step:
        return c5.composed_action(obs, fixed_cfg[0], fixed_cfg[1])
    return structured_tail_action(oracle_by, step - reveal_step)


def rollout_oracle_demo(
    source_row: dict[str, str],
    selected_row: dict[str, Any],
    fixed_cfg: tuple[dict, dict],
) -> dict[str, Any]:
    env = _env_from_row(source_row)
    obs_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    try:
        obs, _info = env.reset(seed=int(source_row["eval_seed"]))
        term = trunc = False
        step = 0
        while not (term or trunc):
            obs_arr = np.asarray(obs, dtype=np.float32)
            if obs_arr.shape != (OBS_DIM,) or not np.all(np.isfinite(obs_arr)):
                raise RuntimeError(f"non-finite or wrong-shape obs on {selected_row['row_id']} step {step}")
            action = oracle_action(
                obs_arr,
                step,
                int(selected_row["reveal_step"]),
                str(selected_row["oracle_by"]),
                fixed_cfg,
            )
            obs_rows.append(obs_arr)
            action_rows.append(np.asarray(action, dtype=np.float32))
            obs, _reward, term, trunc, info = env.step(action)
            step += 1
        bucket = outcome_bucket_from_info(info, terminated=term, truncated=trunc)
        return {
            "row_id": selected_row["row_id"],
            "role": selected_row["bc_role"],
            "level": selected_row["level"],
            "instance": selected_row["instance"],
            "eval_seed": selected_row["eval_seed"],
            "oracle_by": selected_row["oracle_by"],
            "outcome_bucket": bucket,
            "termination_reason": str(info.get("termination_reason", "") or ""),
            "steps": int(info.get("step", step)),
            "obs": np.asarray(obs_rows, dtype=np.float32),
            "actions": np.asarray(action_rows, dtype=np.float32),
        }
    finally:
        env.close()


def _model_action(model: ActorCritic, obs: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        action = torch.tanh(model.actor_mean(model.features_tensor(obs_t)))
    return action.squeeze(0).cpu().numpy().astype(np.float32)


def rollout_dagger_labels(
    model: ActorCritic,
    source_row: dict[str, str],
    selected_row: dict[str, Any],
    fixed_cfg: tuple[dict, dict],
    max_steps: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    env = _env_from_row(source_row)
    obs_rows: list[np.ndarray] = []
    action_rows: list[np.ndarray] = []
    try:
        obs, _info = env.reset(seed=int(source_row["eval_seed"]))
        term = trunc = False
        step = 0
        while not (term or trunc) and step < max_steps:
            obs_arr = np.asarray(obs, dtype=np.float32)
            obs_rows.append(obs_arr)
            action_rows.append(
                oracle_action(
                    obs_arr,
                    step,
                    int(selected_row["reveal_step"]),
                    str(selected_row["oracle_by"]),
                    fixed_cfg,
                )
            )
            obs, _reward, term, trunc, info = env.step(_model_action(model, obs_arr))
            step += 1
        bucket = outcome_bucket_from_info(info, terminated=term, truncated=trunc) if (term or trunc) else "truncated_by_dagger_cap"
        meta = {
            "row_id": selected_row["row_id"],
            "steps": step,
            "outcome_bucket": bucket,
            "termination_reason": str(info.get("termination_reason", "") or "") if (term or trunc) else "",
        }
        return np.asarray(obs_rows, dtype=np.float32), np.asarray(action_rows, dtype=np.float32), meta
    finally:
        env.close()


def rollout_bc_policy(model: ActorCritic, source_row: dict[str, str], selected_row: dict[str, Any]) -> dict[str, Any]:
    env = _env_from_row(source_row)
    try:
        obs, _info = env.reset(seed=int(source_row["eval_seed"]))
        term = trunc = False
        step = 0
        while not (term or trunc):
            action = _model_action(model, np.asarray(obs, dtype=np.float32))
            obs, _reward, term, trunc, info = env.step(action)
            step += 1
        bucket = outcome_bucket_from_info(info, terminated=term, truncated=trunc)
        return {
            "row_id": selected_row["row_id"],
            "role": selected_row["bc_role"],
            "outcome_bucket": bucket,
            "termination_reason": str(info.get("termination_reason", "") or ""),
            "steps": int(info.get("step", step)),
        }
    finally:
        env.close()


def _stack_by_role(demos: list[dict[str, Any]], role: str) -> tuple[np.ndarray, np.ndarray]:
    obs = [demo["obs"] for demo in demos if demo["role"] == role]
    actions = [demo["actions"] for demo in demos if demo["role"] == role]
    if not obs:
        raise RuntimeError(f"no demo frames for role {role}")
    return np.concatenate(obs, axis=0), np.concatenate(actions, axis=0)


def _mse(model: ActorCritic, obs: np.ndarray, actions: np.ndarray) -> float:
    with torch.no_grad():
        pred = torch.tanh(model.actor_mean(model.features_tensor(torch.as_tensor(obs, dtype=torch.float32))))
        target = torch.as_tensor(actions, dtype=torch.float32)
        return float(F.mse_loss(pred, target).item())


def _train_bc(
    train_obs: np.ndarray,
    train_actions: np.ndarray,
    sel_obs: np.ndarray,
    sel_actions: np.ndarray,
    *,
    seed: int,
    seed_base: int,
    epochs: int,
    eval_every: int,
    batch_size: int,
    start_model: ActorCritic | None = None,
) -> tuple[ActorCritic, dict[str, Any]]:
    torch.manual_seed(seed)
    model = start_model or ActorCritic(OBS_DIM, ACT_DIM, hidden_size=HIDDEN, actor_encoder="mlp")
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    x = torch.as_tensor(train_obs, dtype=torch.float32)
    y = torch.as_tensor(train_actions, dtype=torch.float32)
    rng = np.random.default_rng([seed_base, seed, len(train_obs), epochs])
    best = {
        "selection_mse": float("inf"),
        "epoch": 0,
        "state": {key: value.detach().clone() for key, value in model.state_dict().items()},
    }
    history: list[dict[str, float | int]] = []
    for epoch in range(1, epochs + 1):
        perm = rng.permutation(len(train_obs))
        model.train()
        for start in range(0, len(perm), batch_size):
            idx = torch.as_tensor(perm[start : start + batch_size], dtype=torch.long)
            pred = torch.tanh(model.actor_mean(model.features_tensor(x[idx])))
            loss = F.mse_loss(pred, y[idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        if epoch % eval_every == 0 or epoch == epochs:
            model.eval()
            sel_mse = _mse(model, sel_obs, sel_actions)
            train_mse = _mse(model, train_obs, train_actions)
            history.append({"epoch": epoch, "train_mse": round(train_mse, 6), "selection_mse": round(sel_mse, 6)})
            if sel_mse < float(best["selection_mse"]):
                best = {
                    "selection_mse": sel_mse,
                    "train_mse": train_mse,
                    "epoch": epoch,
                    "state": {key: value.detach().clone() for key, value in model.state_dict().items()},
                }
    model.load_state_dict(best["state"])
    model.eval()
    return model, {
        "best_epoch": int(best["epoch"]),
        "best_train_mse": round(float(best.get("train_mse", float("nan"))), 6),
        "best_selection_mse": round(float(best["selection_mse"]), 6),
        "history": history,
    }


def _rows_for_mode(prereg: dict[str, Any], quick: bool) -> list[dict[str, Any]]:
    rows = list(prereg["selected_rows"])
    if not quick:
        return rows
    by_role: dict[str, list[dict[str, Any]]] = {"train": [], "selection": [], "validation": []}
    for row in rows:
        by_role[str(row["bc_role"])].append(row)
    if prereg.get("revision") == REVISION_V2:
        support_rows = [
            row
            for row in by_role["train"]
            if row.get("selection_source") in {"heldout_oracle_family_support", "rare_tail_train_support"}
        ]
        support_sources = {"heldout_oracle_family_support", "rare_tail_train_support"}
        base_train = [row for row in by_role["train"] if row.get("selection_source") not in support_sources]
        train_rows = support_rows + base_train[: max(3, 6 - len(support_rows))]
        validation_probes = [
            row for row in by_role["validation"] if row.get("selection_source") == "rare_tail_validation_probe"
        ]
        base_validation = [
            row for row in by_role["validation"] if row.get("selection_source") != "rare_tail_validation_probe"
        ]
        quick_rows = train_rows + by_role["selection"][:2] + validation_probes + base_validation[:1]
    else:
        quick_rows = by_role["train"][:3] + by_role["selection"][:2] + by_role["validation"][:1]
    if len(quick_rows) < 6:
        raise RuntimeError(f"quick C1 row split too small: { {k: len(v) for k, v in by_role.items()} }")
    return quick_rows


def run(quick: bool, revision: str = REVISION_M3228) -> dict[str, Any]:
    torch.set_num_threads(1)
    t0 = time.time()
    prereg_path, results_path, quick_results_path, run_root = _paths_for_revision(revision)
    seed_base = _seed_base_for_revision(revision)
    prereg = load_preregistration(revision=revision)
    selected_rows = _rows_for_mode(prereg, quick)
    source_rows = _source_row_by_id()
    fixed_cfg = _fixed_star_cfg()
    run_dir = run_root / ("quick" if quick else "full")
    run_dir.mkdir(parents=True, exist_ok=True)

    demos: list[dict[str, Any]] = []
    for selected in selected_rows:
        demos.append(rollout_oracle_demo(source_rows[selected["row_id"]], selected, fixed_cfg))
    failed_demos = [demo for demo in demos if demo["outcome_bucket"] != "success_obstacle_pass"]
    if failed_demos:
        raise RuntimeError(f"structured-oracle demo replay failures: {failed_demos[:3]}")

    train_obs, train_actions = _stack_by_role(demos, "train")
    sel_obs, sel_actions = _stack_by_role(demos, "selection")
    val_obs, val_actions = _stack_by_role(demos, "validation")

    initial_epochs = 4 if quick else 12
    final_epochs = 12 if quick else 60
    eval_every = 2 if quick else 5
    batch_size = 128
    initial_model, initial_report = _train_bc(
        train_obs,
        train_actions,
        sel_obs,
        sel_actions,
        seed=seed_base + 1,
        seed_base=seed_base,
        epochs=initial_epochs,
        eval_every=max(1, initial_epochs // 2),
        batch_size=batch_size,
    )

    dagger_obs_parts = [train_obs]
    dagger_action_parts = [train_actions]
    dagger_meta = []
    for selected in [row for row in selected_rows if row["bc_role"] == "train"]:
        obs_aug, act_aug, meta = rollout_dagger_labels(
            initial_model,
            source_rows[selected["row_id"]],
            selected,
            fixed_cfg,
            max_steps=80,
        )
        dagger_obs_parts.append(obs_aug)
        dagger_action_parts.append(act_aug)
        dagger_meta.append(meta)
    combined_train_obs = np.concatenate(dagger_obs_parts, axis=0)
    combined_train_actions = np.concatenate(dagger_action_parts, axis=0)

    model, final_report = _train_bc(
        combined_train_obs,
        combined_train_actions,
        sel_obs,
        sel_actions,
        seed=seed_base + 2,
        seed_base=seed_base,
        epochs=final_epochs,
        eval_every=eval_every,
        batch_size=batch_size,
    )

    val_mse = _mse(model, val_obs, val_actions)
    zero_baseline_mse = float(np.mean(np.square(val_actions)))
    validation_gate = bool(val_mse <= 0.12 and val_mse <= 0.75 * zero_baseline_mse)
    bc_rollouts = [rollout_bc_policy(model, source_rows[row["row_id"]], row) for row in selected_rows if row["bc_role"] == "validation"]

    dataset_path = run_dir / "dataset.npz"
    checkpoint_path = run_dir / "checkpoint.pt"
    np.savez_compressed(
        dataset_path,
        train_obs=combined_train_obs.astype(np.float32),
        train_actions=combined_train_actions.astype(np.float32),
        selection_obs=sel_obs.astype(np.float32),
        selection_actions=sel_actions.astype(np.float32),
        validation_obs=val_obs.astype(np.float32),
        validation_actions=val_actions.astype(np.float32),
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "model_config": {
                "obs_dim": OBS_DIM,
                "act_dim": ACT_DIM,
                "hidden_size": HIDDEN,
                "actor_encoder": "mlp",
            },
            "preregistration": str(prereg_path),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        checkpoint_path,
    )

    role_counts = {
        role: sum(demo["role"] == role for demo in demos)
        for role in ("train", "selection", "validation")
    }
    demo_frame_counts = {
        role: int(sum(len(demo["obs"]) for demo in demos if demo["role"] == role))
        for role in ("train", "selection", "validation")
    }
    summary = {
        "protocol": "c5prime_c1_oracle_bc_warmstart",
        "revision": revision,
        "generated_by": "scripts/feasibility_audit/c5prime_c1_oracle_bc_warmstart.py",
        "quick_mode": quick,
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(prereg_path),
        "preregistration_frozen_before_rollout": bool(prereg.get("frozen_before_any_c1_rollout")),
        "source_artifacts": prereg["source_artifacts"],
        "selected_rows": [
            {
                key: row[key]
                for key in (
                    "row_id",
                    "level",
                    "instance",
                    "eval_seed",
                    "bc_role",
                    "oracle_by",
                    "gap_row",
                    "selection_source",
                )
                if key in row
            }
            for row in selected_rows
        ],
        "role_counts": role_counts,
        "demo_frame_counts": demo_frame_counts,
        "demo_outcomes": {
            demo["row_id"]: {
                "role": demo["role"],
                "outcome_bucket": demo["outcome_bucket"],
                "steps": demo["steps"],
                "oracle_by": demo["oracle_by"],
            }
            for demo in demos
        },
        "dagger_lite": {
            "source": "BC rollouts on train-role rows, relabeled by frozen structured-oracle step rule",
            "rollouts": dagger_meta,
            "base_train_frames": int(len(train_obs)),
            "augmented_train_frames": int(len(combined_train_obs) - len(train_obs)),
            "combined_train_frames": int(len(combined_train_obs)),
        },
        "bc_training": {
            "model": {"obs_dim": OBS_DIM, "act_dim": ACT_DIM, "hidden_size": HIDDEN, "actor_encoder": "mlp"},
            "initial": initial_report,
            "final": final_report,
            "validation_action_mse": round(float(val_mse), 6),
            "validation_zero_action_baseline_mse": round(float(zero_baseline_mse), 6),
            "validation_mse_gate_passed": validation_gate,
            "validation_bc_rollouts": bc_rollouts,
            "validation_bc_success_rate_context": round(
                sum(r["outcome_bucket"] == "success_obstacle_pass" for r in bc_rollouts) / max(len(bc_rollouts), 1),
                4,
            ),
            "checkpoint": str(checkpoint_path),
            "dataset_npz": str(dataset_path),
        },
        "gates": {
            "demo_replay_all_success": len(failed_demos) == 0,
            "checkpoint_exists": checkpoint_path.exists(),
            "dataset_exists": dataset_path.exists(),
            "validation_action_mse_gate_passed": validation_gate,
            "all_passed": bool(len(failed_demos) == 0 and checkpoint_path.exists() and dataset_path.exists() and validation_gate),
        },
        "elapsed_s": round(time.time() - t0, 3),
    }
    out_path = quick_results_path if quick else results_path
    write_json(out_path, summary)
    if not validation_gate:
        raise RuntimeError(
            f"C1 BC validation gate failed: mse={val_mse:.6f}, zero_baseline={zero_baseline_mse:.6f}"
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", choices=REVISIONS, default=REVISION_M3228)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    if args.write_prereg:
        prereg_path, _results_path, _quick_path, _run_root = _paths_for_revision(args.revision)
        payload = write_preregistration(revision=args.revision)
        print(f"wrote {prereg_path} rows={len(payload['selected_rows'])}")
    if args.quick and args.full:
        raise SystemExit("--quick and --full are mutually exclusive")
    if args.quick or args.full:
        _prereg_path, results_path, quick_results_path, _run_root = _paths_for_revision(args.revision)
        summary = run(quick=args.quick, revision=args.revision)
        out_path = quick_results_path if args.quick else results_path
        print(
            f"wrote {out_path} demos={len(summary['selected_rows'])} "
            f"val_mse={summary['bc_training']['validation_action_mse']}"
        )
    if not (args.write_prereg or args.quick or args.full):
        parser.error("choose --write-prereg, --quick, or --full")


if __name__ == "__main__":
    main()
