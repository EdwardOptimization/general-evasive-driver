"""Phase-4 F1 Chrono training infrastructure smoke and throughput benchmark.

F1 is infrastructure only. It proves that a single obs72/action3 policy can
collect mixed avoidance + drift Chrono rollouts through parallel workers,
perform a finite torch update, and report a 100M-step wall-clock projection.
It does not launch F2 or claim driver performance.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f1_training_infra_smoke.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f1_training_infra_smoke.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f1_training_infra_smoke.py --full --resume
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.optim import Adam

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_e2_chrono_two_regime_smoke as e2_smoke  # noqa: E402
import phase4_e4_drift_regime_pricing as e4  # noqa: E402


MILESTONE_ID = "m3261-phase4-f1-training-infrastructure"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra_quick.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f1_training_infra"
ROWS_QUICK_CSV = RUN_DIR / "worker_step_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "worker_step_rows_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3261-phase4-f1-training-infrastructure.md"

E1PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e1prime_spread_revival_repricing.json"
E2PRIME_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e2prime_chrono_two_regime_hardened.json"
E4_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing.json"

SEED_BASE = 2026061405
VARIANT = "sedan_tmeasy"
FULL_WORKERS = 2
QUICK_WORKERS = 1
FULL_STEPS_PER_UNIT = 12
QUICK_STEPS_PER_UNIT = 3
HIDDEN_SIZE = 64
ACT_DIM = 3
TARGET_STEPS = 100_000_000

CLAIM_BOUNDARY = (
    "Phase-4 F1 training infrastructure only: parallel Chrono worker rollout, "
    "obs72/action3 contract smoke, finite torch actor-critic update, throughput "
    "benchmark, and 100M-step wall-clock projection for the PI stop. F1 does not "
    "launch F2, does not write a policy checkpoint for promotion, does not mutate "
    "ActiveSafetyReflexDriver, and makes no validation ranking, promotion, "
    "driver-performance, current-sim sufficiency, full high-fidelity sufficiency, "
    "paper, repair-success, robustness-result, feasibility-proof, or self-ID claim."
)

ROW_FIELDS = [
    "mode",
    "worker_index",
    "unit_index",
    "regime",
    "scenario_id",
    "seed",
    "step_index",
    "obs72_finite_before",
    "obs72_finite_after",
    "action3_finite",
    "action3_bounded",
    "terminated",
    "truncated",
    "status",
    "termination_reason",
    "completion_reason",
    "backend_variant",
    "backend_model",
    "backend_tire",
    "action_abs_max",
    "obs_sum_before",
    "obs_sum_after",
    "claim_boundary",
]


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else repr(number)
    return value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _seed_for(*parts: Any) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in (SEED_BASE, *parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % 2_000_000_000


def _finite_obs72(obs: np.ndarray) -> bool:
    return bool(np.asarray(obs).shape == (HUMAN_VIEW_OBS_DIM,) and np.isfinite(obs).all())


def _progress(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(payload), sort_keys=True) + "\n")


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv_rows(path, rows, fieldnames=ROW_FIELDS)


def _write_metrics(path: Path, summary: dict[str, Any]) -> None:
    throughput = summary["throughput"]
    update = summary["torch_update"]
    gates = summary["protocol_gates"]
    rows = [
        {"metric": "protocol_gates_passed", "value": int(bool(gates["all_passed"]))},
        {"metric": "obs72_contract_held", "value": int(bool(gates["obs72_contract_held"]))},
        {"metric": "action3_contract_held", "value": int(bool(gates["action3_contract_held"]))},
        {"metric": "finite_losses", "value": int(bool(gates["finite_losses"]))},
        {"metric": "finite_gradients", "value": int(bool(gates["finite_gradients"]))},
        {"metric": "optimizer_changed_parameters", "value": int(bool(gates["optimizer_changed_parameters"]))},
        {"metric": "aggregate_steps_per_s", "value": throughput["aggregate_steps_per_s"]},
        {"metric": "projected_100m_wall_clock_hours", "value": throughput["projected_100m_wall_clock_hours"]},
        {"metric": "chrono_worker_count", "value": throughput["worker_count"]},
        {"metric": "total_chrono_steps", "value": throughput["total_steps"]},
        {"metric": "loss_before", "value": update["loss_before"]},
        {"metric": "loss_after", "value": update["loss_after"]},
        {"metric": "grad_norm", "value": update["grad_norm"]},
        {"metric": "f2_training_admitted", "value": 0},
    ]
    write_csv_rows(path, rows, fieldnames=["metric", "value"])


def _dependency_summary() -> dict[str, Any]:
    e1p = _read_json(E1PRIME_JSON)
    e2p = _read_json(E2PRIME_JSON)
    e4_summary = _read_json(E4_JSON)
    if not e1p.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E1' repricing artifact is not passing")
    if not e2p.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E2' hardening artifact is not passing")
    if not e4_summary.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E4 drift-regime artifact is not passing")
    return {
        "e1prime_artifact": str(E1PRIME_JSON.relative_to(REPO_ROOT)),
        "e1prime_structural_gap": 0.1806,
        "e2prime_artifact": str(E2PRIME_JSON.relative_to(REPO_ROOT)),
        "e2prime_max_clean_belief_value": e2p.get("decision", {}).get("max_clean_oracle_minus_floor", 0.7667),
        "e4_artifact": str(E4_JSON.relative_to(REPO_ROOT)),
        "e4_positive_drift_prize_cells": e4_summary.get("decision", {}).get("positive_drift_prize_cells", []),
        "e4_low_mu_oracle_gap": 0.4,
        "pi_e4_disposition": "Track F approved at full-scenario scope; F1 only, then stop for PI wall-clock review",
    }


def build_preregistration() -> dict[str, Any]:
    deps = _dependency_summary()
    avoidance_seeds = [_seed_for("avoidance", i) for i in range(4)]
    drift_seeds = [_seed_for("drift", i) for i in range(4)]
    return {
        "protocol": "phase4_f1_training_infra_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 F1 training infrastructure",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_f1_infra_run": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": deps,
        "full_scenario_training_target": {
            "one_driver": True,
            "avoidance_regime": {
                "source": "E2'/E1'",
                "teacher": "avoidance oracle",
                "priced_gaps": ["E1' structural gap +0.1806", "E2' clean belief value up to +0.7667"],
            },
            "drift_regime": {
                "source": "E4 low_mu_power_oversteer",
                "teacher": "drift-specialized feedback oracle, not generic CEM",
                "priced_gap": 0.4,
            },
        },
        "worker_smoke": {
            "quick_workers": QUICK_WORKERS,
            "full_workers": FULL_WORKERS,
            "quick_steps_per_unit": QUICK_STEPS_PER_UNIT,
            "full_steps_per_unit": FULL_STEPS_PER_UNIT,
            "chrono_variant": VARIANT,
            "regimes_smoked": ["avoidance_clean_reveal_9p5", "drift_low_mu_power_oversteer"],
        },
        "seed_streams": {
            "avoidance_smoke": avoidance_seeds,
            "drift_smoke": drift_seeds,
            "torch_update": [_seed_for("torch", i) for i in range(4)],
        },
        "acceptance": {
            "obs72_action3_contract": "all reset and step observations finite shape 72; all policy actions finite shape 3 and bounded [-1, 1]",
            "torch_update": "actor-critic loss and gradients finite; optimizer changes parameters",
            "throughput": "aggregate Chrono steps/s > 0 and projected 100M wall-clock reported",
            "device_recheck": "CPU measured; CUDA measured if available, otherwise explicitly recorded unavailable",
            "stop_rule": "after F1, F2 remains blocked on PI wall-clock/go review",
        },
        "quick_mode_is_verdict": False,
    }


def write_preregistration() -> dict[str, Any]:
    payload = build_preregistration()
    write_json(PREREG_JSON, payload)
    return payload


def load_preregistration() -> dict[str, Any]:
    if not PREREG_JSON.exists():
        raise FileNotFoundError(f"missing preregistration {PREREG_JSON}; run --write-prereg first")
    payload = _read_json(PREREG_JSON)
    if payload.get("frozen_before_any_f1_infra_run") is not True:
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_f1_infra_run")
    return payload


def _e2_context():
    reg = _load_module(e2_smoke.REGIME_SCRIPT, "phase4_f1_ramp_policy_voi_regime")
    mod_b = _load_module(e2_smoke.TASK_B_SCRIPT, "phase4_f1_voi_commitment_task_design")
    mod_c = _load_module(e2_smoke.COND_SCRIPT, "phase4_f1_voi_conditional_prior")
    return reg, mod_b, mod_c.interp_lin


def _avoidance_scenario(seed: int, *, max_steps: int) -> dict[str, Any]:
    reg, mod_b, interp = _e2_context()
    scenario = e2_smoke._make_scenario(
        reg,
        mod_b,
        interp,
        reveal=9.5,
        mu=0.3625,
        seed=int(seed),
        variant=VARIANT,
    )
    scenario["scenario_id"] = f"m3261-avoidance-clean-r9p5-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def _drift_scenario(seed: int, *, max_steps: int) -> dict[str, Any]:
    cell = [item for item in e4._cell_catalog() if item["cell_id"] == "low_mu_power_oversteer"][0]
    scenario = e4.scenario_for_cell(cell, seed=int(seed), mode="validation")
    scenario["scenario_id"] = f"m3261-drift-low-mu-power-oversteer-seed{seed}"
    scenario["max_steps"] = int(max_steps)
    return scenario


def _smoke_units(prereg: dict[str, Any], *, quick: bool) -> list[dict[str, Any]]:
    seeds = prereg["seed_streams"]
    per_regime = 1 if quick else 2
    max_steps = QUICK_STEPS_PER_UNIT if quick else FULL_STEPS_PER_UNIT
    units: list[dict[str, Any]] = []
    for idx, seed in enumerate(seeds["avoidance_smoke"][:per_regime]):
        units.append(
            {
                "unit_index": len(units),
                "regime": "avoidance_clean_reveal_9p5",
                "seed": int(seed),
                "scenario": _avoidance_scenario(int(seed), max_steps=max_steps),
                "max_steps": max_steps,
            }
        )
    for idx, seed in enumerate(seeds["drift_smoke"][:per_regime]):
        units.append(
            {
                "unit_index": len(units),
                "regime": "drift_low_mu_power_oversteer",
                "seed": int(seed),
                "scenario": _drift_scenario(int(seed), max_steps=max_steps),
                "max_steps": max_steps,
            }
        )
    return units


def _reset_worker(client: ChronoWorkerClient, unit: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    obs, reply = client.reset(unit["scenario"], episode_id=unit["scenario"]["scenario_id"], seed=int(unit["seed"]))
    return np.asarray(obs, dtype=np.float32), dict(reply)


def _step_client(client: ChronoWorkerClient, action: np.ndarray):
    return client.step(np.asarray(action, dtype=np.float32))


def collect_parallel_chrono_rollout(
    prereg: dict[str, Any],
    *,
    quick: bool,
    model: ActorCritic | None = None,
) -> dict[str, Any]:
    mode = "quick" if quick else "full"
    units = _smoke_units(prereg, quick=quick)
    worker_count = QUICK_WORKERS if quick else FULL_WORKERS
    stderr_log = STDERR_QUICK_LOG if quick else STDERR_FULL_LOG
    progress = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    torch.manual_seed(_seed_for("actor_init", mode))
    model = model or ActorCritic(HUMAN_VIEW_OBS_DIM, ACT_DIM, hidden_size=HIDDEN_SIZE)
    model.eval()

    clients: list[ChronoWorkerClient] = []
    worker_state: list[dict[str, Any] | None] = []
    rows: list[dict[str, Any]] = []
    observations_for_update: list[np.ndarray] = []
    actions_for_update: list[np.ndarray] = []
    worker_launch_started = time.perf_counter()
    try:
        for _ in range(worker_count):
            clients.append(ChronoWorkerClient(stderr_log=stderr_log))
        worker_launch_s = time.perf_counter() - worker_launch_started
        next_unit = 0
        for worker_index, client in enumerate(clients):
            if next_unit >= len(units):
                worker_state.append(None)
                continue
            unit = units[next_unit]
            next_unit += 1
            obs, reply = _reset_worker(client, unit)
            backend = dict(reply.get("backend_info", {}))
            worker_state.append(
                {
                    "worker_index": worker_index,
                    "unit": unit,
                    "obs": obs,
                    "backend": backend,
                    "step_in_unit": 0,
                    "reset_finite": _finite_obs72(obs),
                }
            )

        rollout_started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            while any(state is not None for state in worker_state):
                active_indices = [idx for idx, state in enumerate(worker_state) if state is not None]
                obs_batch = np.stack([worker_state[idx]["obs"] for idx in active_indices]).astype(np.float32)
                actions, _logp, _value = model.act_batch(obs_batch, deterministic=True)
                futures = {
                    executor.submit(_step_client, clients[idx], actions[action_idx]): (idx, action_idx)
                    for action_idx, idx in enumerate(active_indices)
                }
                for future, (worker_index, action_idx) in futures.items():
                    state = worker_state[worker_index]
                    assert state is not None
                    unit = state["unit"]
                    obs_before = state["obs"]
                    action = np.asarray(actions[action_idx], dtype=np.float32)
                    obs_after, terminated, truncated, status, info = future.result()
                    obs_after = np.asarray(obs_after, dtype=np.float32)
                    row = {
                        "mode": mode,
                        "worker_index": worker_index,
                        "unit_index": unit["unit_index"],
                        "regime": unit["regime"],
                        "scenario_id": unit["scenario"]["scenario_id"],
                        "seed": unit["seed"],
                        "step_index": state["step_in_unit"],
                        "obs72_finite_before": _finite_obs72(obs_before),
                        "obs72_finite_after": _finite_obs72(obs_after),
                        "action3_finite": bool(action.shape == (ACT_DIM,) and np.isfinite(action).all()),
                        "action3_bounded": bool(action.shape == (ACT_DIM,) and float(np.max(np.abs(action))) <= 1.00001),
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                        "status": str(status),
                        "termination_reason": str(info.get("termination_reason", "") or ""),
                        "completion_reason": str(info.get("completion_reason", "") or ""),
                        "backend_variant": state["backend"].get("chrono_vehicle_variant", ""),
                        "backend_model": state["backend"].get("chrono_vehicle_model", ""),
                        "backend_tire": state["backend"].get("chrono_tire_model", ""),
                        "action_abs_max": float(np.max(np.abs(action))) if action.size else float("inf"),
                        "obs_sum_before": float(np.sum(obs_before, dtype=np.float64)),
                        "obs_sum_after": float(np.sum(obs_after, dtype=np.float64)) if np.isfinite(obs_after).all() else float("inf"),
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                    rows.append(row)
                    if row["obs72_finite_before"] and row["action3_finite"]:
                        observations_for_update.append(np.asarray(obs_before, dtype=np.float32))
                        actions_for_update.append(action)
                    state["obs"] = obs_after
                    state["step_in_unit"] += 1
                    done = bool(terminated or truncated or state["step_in_unit"] >= int(unit["max_steps"]))
                    if done:
                        if next_unit >= len(units):
                            worker_state[worker_index] = None
                        else:
                            new_unit = units[next_unit]
                            next_unit += 1
                            obs, reply = _reset_worker(clients[worker_index], new_unit)
                            backend = dict(reply.get("backend_info", {}))
                            worker_state[worker_index] = {
                                "worker_index": worker_index,
                                "unit": new_unit,
                                "obs": obs,
                                "backend": backend,
                                "step_in_unit": 0,
                                "reset_finite": _finite_obs72(obs),
                            }
                    _progress(
                        progress,
                        {
                            "mode": mode,
                            "rows": len(rows),
                            "regime": unit["regime"],
                            "worker_index": worker_index,
                            "elapsed_s": round(time.perf_counter() - rollout_started, 3),
                        },
                    )
        rollout_elapsed_s = time.perf_counter() - rollout_started
    finally:
        for client in clients:
            client.close()

    return {
        "rows": rows,
        "observations": np.stack(observations_for_update).astype(np.float32) if observations_for_update else np.zeros((0, HUMAN_VIEW_OBS_DIM), dtype=np.float32),
        "actions": np.stack(actions_for_update).astype(np.float32) if actions_for_update else np.zeros((0, ACT_DIM), dtype=np.float32),
        "worker_launch_s": float(worker_launch_s) if "worker_launch_s" in locals() else float("inf"),
        "rollout_elapsed_s": float(rollout_elapsed_s) if "rollout_elapsed_s" in locals() else float("inf"),
        "worker_count": int(worker_count),
        "unit_count": len(units),
    }


def torch_update_smoke(observations: np.ndarray, target_actions: np.ndarray, *, device: str = "cpu") -> dict[str, Any]:
    if observations.shape[0] < 1:
        raise ValueError("torch update smoke requires at least one observation")
    resolved = torch.device(device)
    torch.manual_seed(_seed_for("torch_update", device))
    model = ActorCritic(HUMAN_VIEW_OBS_DIM, ACT_DIM, hidden_size=HIDDEN_SIZE).to(resolved)
    optimizer = Adam(model.parameters(), lr=3e-4)
    obs = torch.as_tensor(observations, dtype=torch.float32, device=resolved)
    target = torch.as_tensor(target_actions, dtype=torch.float32, device=resolved)
    target = torch.clamp(target, -1.0, 1.0)

    before = [param.detach().clone() for param in model.parameters()]
    dist, value = model(obs)
    action_mean = torch.tanh(dist.mean)
    policy_loss = torch.mean((action_mean - target).pow(2))
    value_loss = torch.mean(value.pow(2))
    entropy_loss = -0.001 * torch.mean(dist.entropy())
    loss = policy_loss + 0.5 * value_loss + entropy_loss
    loss_before = float(loss.detach().cpu())
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    total_sq = 0.0
    finite_gradients = True
    for param in model.parameters():
        if param.grad is None:
            continue
        grad = param.grad.detach()
        finite_gradients = finite_gradients and bool(torch.isfinite(grad).all().item())
        total_sq += float(torch.sum(grad.pow(2)).detach().cpu())
    grad_norm = math.sqrt(total_sq)
    optimizer.step()
    with torch.no_grad():
        dist_after, value_after = model(obs)
        action_after = torch.tanh(dist_after.mean)
        loss_after_t = torch.mean((action_after - target).pow(2)) + 0.5 * torch.mean(value_after.pow(2)) - 0.001 * torch.mean(dist_after.entropy())
    delta_sq = 0.0
    for old, new in zip(before, model.parameters(), strict=True):
        delta_sq += float(torch.sum((new.detach().cpu() - old.cpu()).pow(2)))
    return {
        "device": str(resolved),
        "batch_size": int(observations.shape[0]),
        "loss_before": loss_before,
        "loss_after": float(loss_after_t.detach().cpu()),
        "loss_finite": bool(math.isfinite(loss_before) and math.isfinite(float(loss_after_t.detach().cpu()))),
        "finite_gradients": bool(finite_gradients and math.isfinite(grad_norm)),
        "grad_norm": float(grad_norm),
        "parameter_delta_l2": float(math.sqrt(delta_sq)),
        "optimizer_changed_parameters": bool(delta_sq > 0.0),
    }


def device_recheck(observations: np.ndarray, actions: np.ndarray) -> dict[str, Any]:
    cpu_started = time.perf_counter()
    cpu = torch_update_smoke(observations, actions, device="cpu")
    cpu_elapsed = time.perf_counter() - cpu_started
    result: dict[str, Any] = {
        "cpu": {**cpu, "elapsed_s": float(cpu_elapsed)},
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda": None,
        "device_recheck_complete": True,
        "selected_training_device_for_f2": "cpu" if not torch.cuda.is_available() else "pending_pi_after_f1_report",
    }
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        gpu_started = time.perf_counter()
        cuda = torch_update_smoke(observations, actions, device="cuda")
        torch.cuda.synchronize()
        gpu_elapsed = time.perf_counter() - gpu_started
        result["cuda"] = {**cuda, "elapsed_s": float(gpu_elapsed)}
        cpu_rate = float(cpu["batch_size"]) / max(cpu_elapsed, 1e-9)
        gpu_rate = float(cuda["batch_size"]) / max(gpu_elapsed, 1e-9)
        result["cpu_batch_updates_per_s"] = cpu_rate
        result["cuda_batch_updates_per_s"] = gpu_rate
        result["cuda_vs_cpu_update_speed_ratio"] = gpu_rate / max(cpu_rate, 1e-9)
    return result


def summarize(prereg: dict[str, Any], rollout: dict[str, Any], update: dict[str, Any], devices: dict[str, Any], *, quick: bool, elapsed_s: float) -> dict[str, Any]:
    rows = rollout["rows"]
    total_steps = len(rows)
    rollout_elapsed = float(rollout["rollout_elapsed_s"])
    steps_per_s = total_steps / max(rollout_elapsed, 1e-9)
    projected_hours = TARGET_STEPS / max(steps_per_s, 1e-9) / 3600.0
    regime_counts: dict[str, int] = {}
    for row in rows:
        regime_counts[row["regime"]] = regime_counts.get(row["regime"], 0) + 1
    unique_seeds = {(row["regime"], row["seed"]) for row in rows}
    expected_seed_count = len({(unit["regime"], unit["seed"]) for unit in _smoke_units(prereg, quick=quick)})
    gates = {
        "preregistration_present": PREREG_JSON.exists(),
        "quick_before_full": quick or QUICK_JSON.exists(),
        "chrono_worker_count_met": int(rollout["worker_count"]) >= (QUICK_WORKERS if quick else FULL_WORKERS),
        "mixed_regime_coverage": set(regime_counts) >= {"avoidance_clean_reveal_9p5", "drift_low_mu_power_oversteer"},
        "obs72_contract_held": bool(rows) and all(row["obs72_finite_before"] and row["obs72_finite_after"] for row in rows),
        "action3_contract_held": bool(rows) and all(row["action3_finite"] and row["action3_bounded"] for row in rows),
        "finite_losses": bool(update["loss_finite"]),
        "finite_gradients": bool(update["finite_gradients"]),
        "optimizer_changed_parameters": bool(update["optimizer_changed_parameters"]),
        "deterministic_seed_handling": len(unique_seeds) == expected_seed_count,
        "throughput_positive": bool(steps_per_s > 0.0 and math.isfinite(steps_per_s)),
        "projected_wall_clock_present": bool(math.isfinite(projected_hours) and projected_hours > 0.0),
        "device_recheck_complete": bool(devices.get("device_recheck_complete")),
        "f2_training_admitted_false": True,
        "stop_for_pi_wall_clock_review": True,
    }
    gates["all_passed"] = all(bool(value) for value in gates.values())
    return {
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "generated_at_utc": utc_timestamp(),
        "elapsed_s": float(elapsed_s),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "protocol_gates": gates,
        "row_count": total_steps,
        "regime_step_counts": regime_counts,
        "throughput": {
            "worker_count": int(rollout["worker_count"]),
            "unit_count": int(rollout["unit_count"]),
            "total_steps": int(total_steps),
            "worker_launch_s": float(rollout["worker_launch_s"]),
            "rollout_elapsed_s": rollout_elapsed,
            "aggregate_steps_per_s": float(steps_per_s),
            "projected_100m_wall_clock_hours": float(projected_hours),
            "projected_100m_wall_clock_days": float(projected_hours / 24.0),
            "projection_target_steps": TARGET_STEPS,
        },
        "torch_update": update,
        "device_recheck": devices,
        "decision": {
            "f1_verdict": (
                "quick_smoke_passed" if quick and gates["all_passed"]
                else "f1_training_infrastructure_completed" if gates["all_passed"]
                else "f1_training_infrastructure_failed"
            ),
            "f1_completed": bool((not quick) and gates["all_passed"]),
            "f2_training_admitted": False,
            "next_step": "STOP_FOR_PI_WALL_CLOCK_REVIEW" if not quick else "RUN_FULL_F1",
        },
    }


def write_doc(summary: dict[str, Any]) -> None:
    throughput = summary["throughput"]
    gates = summary["protocol_gates"]
    device = summary["device_recheck"]
    lines = [
        "# M3261 Phase-4 F1 Training Infrastructure",
        "",
        "## Status",
        "",
        "- Verdict: " + summary["decision"]["f1_verdict"],
        "- Scope: infrastructure smoke and throughput only; no F2 launch and no driver-performance claim.",
        "",
        "## Measured",
        "",
        f"- Parallel Chrono workers: {throughput['worker_count']}",
        f"- Mixed-regime worker steps: {throughput['total_steps']} ({summary['regime_step_counts']})",
        f"- Aggregate throughput: {throughput['aggregate_steps_per_s']:.4f} steps/s",
        f"- Projected 100M-step wall-clock: {throughput['projected_100m_wall_clock_hours']:.2f} h ({throughput['projected_100m_wall_clock_days']:.2f} days)",
        f"- Torch loss before/after: {summary['torch_update']['loss_before']:.6f} / {summary['torch_update']['loss_after']:.6f}",
        f"- Grad norm: {summary['torch_update']['grad_norm']:.6f}; parameter delta L2: {summary['torch_update']['parameter_delta_l2']:.6f}",
        f"- CUDA available: {device['cuda_available']}",
        "",
        "## Gates",
        "",
    ]
    for key, value in gates.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Inferred",
            "",
            "F1 proves the training-infrastructure path can collect mixed avoidance/drift Chrono rollouts, run a finite actor-critic update, and estimate 100M-step wall-clock. It does not prove driver performance or admit F2.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{FULL_JSON.relative_to(REPO_ROOT)}`",
            f"- Rows: `{ROWS_FULL_CSV.relative_to(REPO_ROOT)}`",
            f"- Metrics: `{METRICS_FULL_CSV.relative_to(REPO_ROOT)}`",
            f"- Preregistration: `{PREREG_JSON.relative_to(REPO_ROOT)}`",
            "",
            "## Stop",
            "",
            "F2/F3 remain blocked until PI reviews the F1 wall-clock/throughput report and gives the next go.",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_smoke(*, quick: bool) -> dict[str, Any]:
    prereg = load_preregistration()
    started = time.perf_counter()
    rollout = collect_parallel_chrono_rollout(prereg, quick=quick)
    rows_path = ROWS_QUICK_CSV if quick else ROWS_FULL_CSV
    metrics_path = METRICS_QUICK_CSV if quick else METRICS_FULL_CSV
    result_path = QUICK_JSON if quick else FULL_JSON
    _write_rows(rows_path, rollout["rows"])
    update = torch_update_smoke(rollout["observations"], rollout["actions"], device="cpu")
    devices = device_recheck(rollout["observations"], rollout["actions"])
    summary = summarize(prereg, rollout, update, devices, quick=quick, elapsed_s=time.perf_counter() - started)
    write_json(result_path, summary)
    _write_metrics(metrics_path, summary)
    if not quick:
        write_doc(summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Accepted for harness consistency; F1 smoke rewrites deterministic artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sum([bool(args.write_prereg), bool(args.quick), bool(args.full)]) != 1:
        raise SystemExit("choose exactly one of --write-prereg, --quick, or --full")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"wrote": str(PREREG_JSON), "protocol": payload["protocol"]}, sort_keys=True))
        return
    summary = run_smoke(quick=bool(args.quick))
    print(json.dumps({"mode": summary["mode"], "decision": summary["decision"], "gates": summary["protocol_gates"]}, sort_keys=True))
    if not summary["protocol_gates"]["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
