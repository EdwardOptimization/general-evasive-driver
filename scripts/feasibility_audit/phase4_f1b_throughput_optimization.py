"""Phase-4 F1b Chrono training-throughput optimization benchmark.

F1b is still the F1 wall-clock stop. It adds a batched Chrono worker protocol,
scales worker count beyond the two-worker F1 smoke, measures both
training-equivalent closed-loop stepping and batched action-sequence IPC
amortization, re-projects 100M-step wall-clock, and stops before F2.

Usage:
    PYTHONPATH=src python scripts/feasibility_audit/phase4_f1b_throughput_optimization.py --write-prereg
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f1b_throughput_optimization.py --quick --resume
    PYTHONPATH=src OMP_NUM_THREADS=1 python scripts/feasibility_audit/phase4_f1b_throughput_optimization.py --full --resume
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json  # noqa: E402
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_OBS_DIM  # noqa: E402
from chrono_worker_client import ChronoWorkerClient  # noqa: E402
import phase4_f1_training_infra_smoke as f1  # noqa: E402


MILESTONE_ID = "m3263-phase4-f1b-throughput-optimization"
PREREG_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1b_throughput_prereg.json"
QUICK_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1b_throughput_quick.json"
FULL_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1b_throughput.json"
RUN_DIR = REPO_ROOT / "runs" / "feasibility_audit" / "phase4_f1b_throughput"
ROWS_QUICK_CSV = RUN_DIR / "worker_step_rows_quick.csv"
ROWS_FULL_CSV = RUN_DIR / "worker_step_rows_full.csv"
METRICS_QUICK_CSV = RUN_DIR / "metrics_quick.csv"
METRICS_FULL_CSV = RUN_DIR / "metrics_full.csv"
PROGRESS_QUICK_JSONL = RUN_DIR / "progress_quick.jsonl"
PROGRESS_FULL_JSONL = RUN_DIR / "progress_full.jsonl"
STDERR_QUICK_LOG = RUN_DIR / "chrono_worker_stderr_quick.log"
STDERR_FULL_LOG = RUN_DIR / "chrono_worker_stderr_full.log"
DOC_PATH = REPO_ROOT / "docs" / "m3263-phase4-f1b-throughput-optimization.md"
REVIEW_MD = REPO_ROOT / "docs" / "reviews" / "m3263-phase4-f1b-throughput-optimization.md"
REVIEW_JSON = REPO_ROOT / "experiments" / "reviews" / "m3263-phase4-f1b-throughput-optimization.json"

F1_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_f1_training_infra.json"
E4_JSON = REPO_ROOT / "experiments" / "feasibility_audit" / "phase4_e4_drift_regime_pricing.json"

SEED_BASE = 2026061406
VARIANT = f1.VARIANT
ACT_DIM = f1.ACT_DIM
HIDDEN_SIZE = f1.HIDDEN_SIZE
TARGET_STEPS = 100_000_000
TARGET_AGGREGATE_STEPS_PER_S = 1000.0
QUICK_WORKERS = 2
QUICK_STEPS_PER_UNIT = 4
QUICK_BATCH_HORIZON = 2
FULL_STEPS_PER_UNIT = 32
FULL_BATCH_HORIZON = 8
FULL_WORKER_CAP = 30

CLAIM_BOUNDARY = (
    "Phase-4 F1b throughput optimization only: batched Chrono worker transport, "
    "scaled worker-count rollout timing, obs72/action3 contract preservation, "
    "determinism replay, and 100M-step wall-clock re-projection for the PI stop. "
    "F1b does not launch F2, does not run PPO, does not write a policy checkpoint "
    "for promotion, does not mutate ActiveSafetyReflexDriver, and makes no "
    "validation ranking, promotion, driver-performance, current-sim sufficiency, "
    "full high-fidelity sufficiency, paper, repair-success, robustness-result, "
    "feasibility-proof, F2-training admission, or self-ID claim."
)

ROW_FIELDS = [
    "mode",
    "protocol",
    "worker_index",
    "unit_index",
    "regime",
    "scenario_id",
    "seed",
    "step_index",
    "batch_index",
    "batch_horizon",
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
    gates = summary["protocol_gates"]
    rows = [
        {"metric": "protocol_gates_passed", "value": int(bool(gates["all_passed"]))},
        {"metric": "target_1000_steps_per_s_met", "value": int(bool(gates["target_1000_steps_per_s_met"]))},
        {"metric": "obs72_contract_held", "value": int(bool(gates["obs72_contract_held"]))},
        {"metric": "action3_contract_held", "value": int(bool(gates["action3_contract_held"]))},
        {"metric": "determinism_replay_passed", "value": int(bool(gates["determinism_replay_passed"]))},
        {"metric": "worker_count", "value": throughput["worker_count"]},
        {"metric": "batch_horizon", "value": throughput["batch_horizon"]},
        {"metric": "closed_loop_aggregate_steps_per_s", "value": throughput["closed_loop"]["aggregate_steps_per_s"]},
        {"metric": "batched_action_sequence_aggregate_steps_per_s", "value": throughput["batched_action_sequence"]["aggregate_steps_per_s"]},
        {"metric": "best_aggregate_steps_per_s", "value": throughput["best_aggregate_steps_per_s"]},
        {"metric": "best_projected_100m_wall_clock_hours", "value": throughput["best_projected_100m_wall_clock_hours"]},
        {"metric": "f1_baseline_aggregate_steps_per_s", "value": throughput["f1_baseline_aggregate_steps_per_s"]},
        {"metric": "speedup_vs_f1_baseline", "value": throughput["speedup_vs_f1_baseline"]},
        {"metric": "f2_training_admitted", "value": 0},
    ]
    write_csv_rows(path, rows, fieldnames=["metric", "value"])


def _default_full_workers() -> int:
    cpu_count = os.cpu_count() or 2
    return max(1, min(FULL_WORKER_CAP, max(1, cpu_count - 2)))


def _worker_count(quick: bool, requested: int | None) -> int:
    if requested is not None:
        return max(1, int(requested))
    return QUICK_WORKERS if quick else _default_full_workers()


def _steps_per_unit(quick: bool, requested: int | None) -> int:
    if requested is not None:
        return max(1, int(requested))
    return QUICK_STEPS_PER_UNIT if quick else FULL_STEPS_PER_UNIT


def _batch_horizon(quick: bool, requested: int | None) -> int:
    if requested is not None:
        return max(1, int(requested))
    return QUICK_BATCH_HORIZON if quick else FULL_BATCH_HORIZON


def _dependency_summary() -> dict[str, Any]:
    f1_summary = _read_json(F1_JSON)
    e4_summary = _read_json(E4_JSON)
    if not f1_summary.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("F1 infrastructure artifact is not passing")
    if not e4_summary.get("protocol_gates", {}).get("all_passed"):
        raise RuntimeError("E4 drift-regime artifact is not passing")
    return {
        "f1_artifact": str(F1_JSON.relative_to(REPO_ROOT)),
        "f1_aggregate_steps_per_s": f1_summary.get("throughput", {}).get("aggregate_steps_per_s"),
        "f1_projected_100m_wall_clock_hours": f1_summary.get("throughput", {}).get("projected_100m_wall_clock_hours"),
        "f1_worker_count": f1_summary.get("throughput", {}).get("worker_count"),
        "f1_total_steps": f1_summary.get("throughput", {}).get("total_steps"),
        "e4_artifact": str(E4_JSON.relative_to(REPO_ROOT)),
        "e4_low_mu_oracle_gap": 0.4,
        "pi_f1_disposition": "F1 as built is too slow; optimize worker scale and per-step IPC before any F2 launch",
    }


def build_preregistration() -> dict[str, Any]:
    deps = _dependency_summary()
    avoidance_seeds = [_seed_for("avoidance", i) for i in range(64)]
    drift_seeds = [_seed_for("drift", i) for i in range(64)]
    return {
        "protocol": "phase4_f1b_throughput_optimization_preregistration",
        "milestone": MILESTONE_ID,
        "roadmap_unit": "Phase-4 F1b training-throughput optimization",
        "frozen_at_utc": utc_timestamp(),
        "frozen_before_any_f1b_run": True,
        "seed_base": SEED_BASE,
        "claim_boundary": CLAIM_BOUNDARY,
        "dependencies": deps,
        "throughput_target": {
            "target_aggregate_steps_per_s": TARGET_AGGREGATE_STEPS_PER_S,
            "target_100m_wall_clock_hours": TARGET_STEPS / TARGET_AGGREGATE_STEPS_PER_S / 3600.0,
            "target_100m_wall_clock_days": TARGET_STEPS / TARGET_AGGREGATE_STEPS_PER_S / 86400.0,
            "f1_baseline_steps_per_s": deps["f1_aggregate_steps_per_s"],
        },
        "optimization_axes": {
            "worker_scaling": {
                "quick_workers": QUICK_WORKERS,
                "full_default_workers": _default_full_workers(),
                "full_worker_cap": FULL_WORKER_CAP,
            },
            "ipc_amortization": {
                "protocol": "step_many JSONL command with batched action-sequence transport",
                "quick_batch_horizon": QUICK_BATCH_HORIZON,
                "full_batch_horizon": FULL_BATCH_HORIZON,
                "closed_loop_baseline_retained": True,
            },
        },
        "seed_streams": {
            "avoidance_benchmark": avoidance_seeds,
            "drift_benchmark": drift_seeds,
            "determinism_replay": [_seed_for("determinism", i) for i in range(2)],
            "actor_init": [_seed_for("actor_init", i) for i in range(2)],
        },
        "acceptance": {
            "quick_before_full": "quick artifact must exist before full",
            "mixed_regime_coverage": "full rows include avoidance_clean_reveal_9p5 and drift_low_mu_power_oversteer",
            "obs72_action3_contract": "all reset and step observations finite shape 72; all actions finite shape 3 and bounded [-1, 1]",
            "batched_transport": "step_many worker command exercised and reported separately from closed-loop one-step transport",
            "throughput_report": "closed-loop and batched aggregate steps/s plus 100M wall-clock projections reported",
            "target_policy": "target >=1000 steps/s is a PI feasibility target; missing it completes F1b as negative throughput evidence, not as F2 admission",
            "stop_rule": "after F1b, F2 remains blocked on PI wall-clock/go review",
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
    if payload.get("frozen_before_any_f1b_run") is not True:
        raise ValueError(f"{PREREG_JSON} is not frozen_before_any_f1b_run")
    return payload


def _make_units(prereg: dict[str, Any], *, worker_count: int, steps_per_unit: int) -> list[dict[str, Any]]:
    seeds = prereg["seed_streams"]
    avoidance_idx = 0
    drift_idx = 0
    units: list[dict[str, Any]] = []
    for index in range(worker_count):
        if index % 2 == 0:
            seed = int(seeds["avoidance_benchmark"][avoidance_idx])
            avoidance_idx += 1
            scenario = f1._avoidance_scenario(seed, max_steps=steps_per_unit)
            regime = "avoidance_clean_reveal_9p5"
            scenario["scenario_id"] = f"m3263-avoidance-clean-r9p5-seed{seed}"
        else:
            seed = int(seeds["drift_benchmark"][drift_idx])
            drift_idx += 1
            scenario = f1._drift_scenario(seed, max_steps=steps_per_unit)
            regime = "drift_low_mu_power_oversteer"
            scenario["scenario_id"] = f"m3263-drift-low-mu-power-oversteer-seed{seed}"
        scenario["max_steps"] = int(steps_per_unit)
        units.append(
            {
                "unit_index": len(units),
                "regime": regime,
                "seed": seed,
                "scenario": scenario,
                "max_steps": int(steps_per_unit),
            }
        )
    return units


def _launch_clients(worker_count: int, stderr_log: Path) -> tuple[list[ChronoWorkerClient], float]:
    started = time.perf_counter()
    clients: list[ChronoWorkerClient | None] = [None] * worker_count
    launched: list[ChronoWorkerClient] = []
    try:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(ChronoWorkerClient, stderr_log=stderr_log) for _ in range(worker_count)]
            for index, future in enumerate(futures):
                client = future.result()
                clients[index] = client
                launched.append(client)
        return [client for client in clients if client is not None], time.perf_counter() - started
    except Exception:
        for client in launched:
            client.close()
        raise


def _reset_client(client: ChronoWorkerClient, unit: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    obs, reply = client.reset(unit["scenario"], episode_id=unit["scenario"]["scenario_id"], seed=int(unit["seed"]))
    return np.asarray(obs, dtype=np.float32), dict(reply)


def _step_client(client: ChronoWorkerClient, action: np.ndarray):
    return client.step(np.asarray(action, dtype=np.float32))


def _step_many_client(client: ChronoWorkerClient, actions: np.ndarray):
    return client.step_many(np.asarray(actions, dtype=np.float32))


def _action_sequences(model: ActorCritic, obs_batch: np.ndarray, horizon: int) -> np.ndarray:
    device = next(model.parameters()).device
    obs_t = torch.as_tensor(obs_batch, dtype=torch.float32, device=device)
    with torch.no_grad():
        return model.action_sequence_tensor(obs_t).cpu().numpy().astype(np.float32)[:, :horizon, :]


def _row(
    *,
    mode: str,
    protocol: str,
    worker_index: int,
    unit: dict[str, Any],
    state: dict[str, Any],
    obs_before: np.ndarray,
    action: np.ndarray,
    obs_after: np.ndarray,
    terminated: bool,
    truncated: bool,
    status: str,
    info: dict[str, Any],
    batch_index: int,
    batch_horizon: int,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "protocol": protocol,
        "worker_index": worker_index,
        "unit_index": unit["unit_index"],
        "regime": unit["regime"],
        "scenario_id": unit["scenario"]["scenario_id"],
        "seed": unit["seed"],
        "step_index": state["step_in_unit"],
        "batch_index": batch_index,
        "batch_horizon": batch_horizon,
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


def _initialized_worker_state(
    clients: list[ChronoWorkerClient],
    units: list[dict[str, Any]],
    *,
    worker_count: int,
) -> list[dict[str, Any]]:
    worker_state: list[dict[str, Any] | None] = [None] * worker_count
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(_reset_client, clients[index], units[index]) for index in range(worker_count)]
        for index, future in enumerate(futures):
            obs, reply = future.result()
            worker_state[index] = {
                "worker_index": index,
                "unit": units[index],
                "obs": obs,
                "backend": dict(reply.get("backend_info", {})),
                "step_in_unit": 0,
                "reset_finite": _finite_obs72(obs),
                "done": False,
            }
    return [state for state in worker_state if state is not None]


def collect_rollout(
    prereg: dict[str, Any],
    *,
    mode: str,
    protocol: str,
    worker_count: int,
    steps_per_unit: int,
    batch_horizon: int,
    stderr_log: Path,
    progress: Path,
) -> dict[str, Any]:
    if protocol not in {"closed_loop_step", "batched_action_sequence"}:
        raise ValueError(f"unknown protocol {protocol!r}")
    units = _make_units(prereg, worker_count=worker_count, steps_per_unit=steps_per_unit)
    torch.manual_seed(_seed_for("actor_init", mode, protocol, worker_count, steps_per_unit, batch_horizon))
    model = ActorCritic(
        HUMAN_VIEW_OBS_DIM,
        ACT_DIM,
        hidden_size=HIDDEN_SIZE,
        action_sequence_horizon=max(1, batch_horizon),
    )
    model.eval()

    clients: list[ChronoWorkerClient] = []
    rows: list[dict[str, Any]] = []
    policy_elapsed_s = 0.0
    rpc_elapsed_s = 0.0
    worker_launch_s = float("inf")
    rollout_elapsed_s = float("inf")
    try:
        clients, worker_launch_s = _launch_clients(worker_count, stderr_log)
        worker_state = _initialized_worker_state(clients, units, worker_count=worker_count)
        rollout_started = time.perf_counter()
        batch_index = 0
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            while any(not state["done"] for state in worker_state):
                active_indices = [
                    idx
                    for idx, state in enumerate(worker_state)
                    if not state["done"]
                ]
                obs_batch = np.stack([worker_state[idx]["obs"] for idx in active_indices]).astype(np.float32)
                policy_started = time.perf_counter()
                if protocol == "closed_loop_step":
                    actions, _logp, _value = model.act_batch(obs_batch, deterministic=True)
                    sequences = actions[:, None, :]
                else:
                    remaining = [
                        int(worker_state[idx]["unit"]["max_steps"]) - int(worker_state[idx]["step_in_unit"])
                        for idx in active_indices
                    ]
                    horizon = max(1, min(int(batch_horizon), max(remaining)))
                    sequences = _action_sequences(model, obs_batch, horizon)
                policy_elapsed_s += time.perf_counter() - policy_started

                rpc_started = time.perf_counter()
                futures = []
                for action_idx, worker_index in enumerate(active_indices):
                    state = worker_state[worker_index]
                    remaining = int(state["unit"]["max_steps"]) - int(state["step_in_unit"])
                    count = 1 if protocol == "closed_loop_step" else min(int(batch_horizon), remaining)
                    actions_for_worker = np.asarray(sequences[action_idx, :count, :], dtype=np.float32)
                    if protocol == "closed_loop_step":
                        futures.append((worker_index, actions_for_worker, executor.submit(_step_client, clients[worker_index], actions_for_worker[0])))
                    else:
                        futures.append((worker_index, actions_for_worker, executor.submit(_step_many_client, clients[worker_index], actions_for_worker)))
                for worker_index, actions_for_worker, future in futures:
                    state = worker_state[worker_index]
                    unit = state["unit"]
                    if protocol == "closed_loop_step":
                        step_results = [future.result()]
                    else:
                        step_results, _stopped_early = future.result()
                    for step_offset, result in enumerate(step_results):
                        obs_before = np.asarray(state["obs"], dtype=np.float32)
                        action = np.asarray(actions_for_worker[step_offset], dtype=np.float32)
                        obs_after, terminated, truncated, status, info = result
                        obs_after = np.asarray(obs_after, dtype=np.float32)
                        rows.append(
                            _row(
                                mode=mode,
                                protocol=protocol,
                                worker_index=worker_index,
                                unit=unit,
                                state=state,
                                obs_before=obs_before,
                                action=action,
                                obs_after=obs_after,
                                terminated=terminated,
                                truncated=truncated,
                                status=status,
                                info=dict(info),
                                batch_index=batch_index,
                                batch_horizon=(1 if protocol == "closed_loop_step" else int(batch_horizon)),
                            )
                        )
                        state["obs"] = obs_after
                        state["step_in_unit"] += 1
                        if bool(terminated or truncated) or state["step_in_unit"] >= int(unit["max_steps"]):
                            state["done"] = True
                            break
                    _progress(
                        progress,
                        {
                            "mode": mode,
                            "protocol": protocol,
                            "rows": len(rows),
                            "worker_index": worker_index,
                            "elapsed_s": round(time.perf_counter() - rollout_started, 3),
                        },
                    )
                rpc_elapsed_s += time.perf_counter() - rpc_started
                batch_index += 1
        rollout_elapsed_s = time.perf_counter() - rollout_started
    finally:
        for client in clients:
            client.close()

    steps_per_s = len(rows) / max(rollout_elapsed_s, 1e-9)
    return {
        "protocol": protocol,
        "rows": rows,
        "worker_count": int(worker_count),
        "unit_count": len(units),
        "total_steps": len(rows),
        "worker_launch_s": float(worker_launch_s),
        "rollout_elapsed_s": float(rollout_elapsed_s),
        "policy_elapsed_s": float(policy_elapsed_s),
        "rpc_elapsed_s": float(rpc_elapsed_s),
        "aggregate_steps_per_s": float(steps_per_s),
        "projected_100m_wall_clock_hours": float(TARGET_STEPS / max(steps_per_s, 1e-9) / 3600.0),
        "projected_100m_wall_clock_days": float(TARGET_STEPS / max(steps_per_s, 1e-9) / 86400.0),
    }


def determinism_replay(prereg: dict[str, Any], *, steps: int, stderr_log: Path) -> dict[str, Any]:
    seed = int(prereg["seed_streams"]["determinism_replay"][0])
    scenario = f1._avoidance_scenario(seed, max_steps=steps)
    scenario["scenario_id"] = f"m3263-determinism-replay-seed{seed}"
    rng = np.random.default_rng(_seed_for("determinism_actions", steps))
    actions = np.tanh(rng.normal(size=(steps, ACT_DIM))).astype(np.float32)
    client = ChronoWorkerClient(stderr_log=stderr_log)
    try:
        traces = []
        for episode_index in range(2):
            obs, _reply = client.reset(scenario, episode_id=f"{scenario['scenario_id']}-rep{episode_index}", seed=seed)
            steps_out, stopped_early = client.step_many(actions)
            obs_sums = [float(np.sum(obs, dtype=np.float64))]
            obs_sums.extend(float(np.sum(row[0], dtype=np.float64)) for row in steps_out)
            statuses = [row[3] for row in steps_out]
            traces.append(
                {
                    "obs_sums": obs_sums,
                    "statuses": statuses,
                    "stopped_early": bool(stopped_early),
                    "step_count": len(steps_out),
                }
            )
    finally:
        client.close()
    max_abs_diff = 0.0
    if len(traces[0]["obs_sums"]) == len(traces[1]["obs_sums"]):
        diffs = [abs(a - b) for a, b in zip(traces[0]["obs_sums"], traces[1]["obs_sums"], strict=True)]
        max_abs_diff = max(diffs) if diffs else 0.0
    else:
        max_abs_diff = float("inf")
    return {
        "seed": seed,
        "steps_requested": int(steps),
        "trace_lengths": [trace["step_count"] for trace in traces],
        "statuses_match": traces[0]["statuses"] == traces[1]["statuses"],
        "max_abs_obs_sum_diff": float(max_abs_diff),
        "passed": bool(max_abs_diff <= 1e-6 and traces[0]["statuses"] == traces[1]["statuses"]),
    }


def _protocol_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["protocol"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _regime_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["regime"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def summarize(
    prereg: dict[str, Any],
    closed_loop: dict[str, Any],
    batched: dict[str, Any],
    determinism: dict[str, Any],
    *,
    quick: bool,
    elapsed_s: float,
    worker_count: int,
    steps_per_unit: int,
    batch_horizon: int,
) -> dict[str, Any]:
    rows = [*closed_loop["rows"], *batched["rows"]]
    regime_counts = _regime_counts(rows)
    protocol_counts = _protocol_counts(rows)
    f1_baseline = float(prereg["dependencies"]["f1_aggregate_steps_per_s"])
    best_steps_per_s = max(float(closed_loop["aggregate_steps_per_s"]), float(batched["aggregate_steps_per_s"]))
    best_hours = TARGET_STEPS / max(best_steps_per_s, 1e-9) / 3600.0
    expected_full_workers = _default_full_workers()
    gates = {
        "preregistration_present": PREREG_JSON.exists(),
        "quick_before_full": quick or QUICK_JSON.exists(),
        "worker_count_scaled": bool(quick or worker_count >= min(expected_full_workers, FULL_WORKER_CAP)),
        "mixed_regime_coverage": set(regime_counts) >= {"avoidance_clean_reveal_9p5", "drift_low_mu_power_oversteer"},
        "closed_loop_protocol_exercised": protocol_counts.get("closed_loop_step", 0) > 0,
        "batched_transport_protocol_exercised": protocol_counts.get("batched_action_sequence", 0) > 0,
        "obs72_contract_held": bool(rows) and all(row["obs72_finite_before"] and row["obs72_finite_after"] for row in rows),
        "action3_contract_held": bool(rows) and all(row["action3_finite"] and row["action3_bounded"] for row in rows),
        "determinism_replay_passed": bool(determinism.get("passed")),
        "throughput_positive": bool(best_steps_per_s > 0.0 and math.isfinite(best_steps_per_s)),
        "projected_wall_clock_present": bool(math.isfinite(best_hours) and best_hours > 0.0),
        "target_1000_steps_per_s_met": bool(best_steps_per_s >= TARGET_AGGREGATE_STEPS_PER_S),
        "target_miss_reportable": True,
        "f2_training_admitted_false": True,
        "stop_for_pi_wall_clock_review": True,
    }
    non_target_gates = {key: value for key, value in gates.items() if key != "target_1000_steps_per_s_met"}
    gates["all_passed"] = all(bool(value) for value in non_target_gates.values())
    bottleneck = (
        "target_met_stop_for_pi"
        if gates["target_1000_steps_per_s_met"]
        else "closed_loop_policy_step_rpc_or_chrono_worker_throughput_below_pi_target"
    )
    return {
        "milestone": MILESTONE_ID,
        "mode": "quick" if quick else "full",
        "generated_at_utc": utc_timestamp(),
        "elapsed_s": float(elapsed_s),
        "claim_boundary": CLAIM_BOUNDARY,
        "preregistration": str(PREREG_JSON.relative_to(REPO_ROOT)),
        "protocol_gates": gates,
        "row_count": len(rows),
        "regime_step_counts": regime_counts,
        "protocol_step_counts": protocol_counts,
        "throughput": {
            "worker_count": int(worker_count),
            "default_full_worker_count": expected_full_workers,
            "steps_per_unit": int(steps_per_unit),
            "batch_horizon": int(batch_horizon),
            "closed_loop": {key: value for key, value in closed_loop.items() if key != "rows"},
            "batched_action_sequence": {key: value for key, value in batched.items() if key != "rows"},
            "best_aggregate_steps_per_s": float(best_steps_per_s),
            "best_projected_100m_wall_clock_hours": float(best_hours),
            "best_projected_100m_wall_clock_days": float(best_hours / 24.0),
            "projection_target_steps": TARGET_STEPS,
            "target_aggregate_steps_per_s": TARGET_AGGREGATE_STEPS_PER_S,
            "target_100m_wall_clock_hours": TARGET_STEPS / TARGET_AGGREGATE_STEPS_PER_S / 3600.0,
            "f1_baseline_aggregate_steps_per_s": f1_baseline,
            "speedup_vs_f1_baseline": float(best_steps_per_s / max(f1_baseline, 1e-9)),
        },
        "determinism_replay": determinism,
        "decision": {
            "f1b_verdict": (
                "quick_smoke_passed" if quick and gates["all_passed"]
                else "f1b_throughput_target_met" if gates["all_passed"] and gates["target_1000_steps_per_s_met"]
                else "f1b_throughput_target_missed_reported" if gates["all_passed"]
                else "f1b_throughput_protocol_failed"
            ),
            "f1b_completed": bool((not quick) and gates["all_passed"]),
            "target_met": bool(gates["target_1000_steps_per_s_met"]),
            "remaining_bottleneck": bottleneck,
            "f2_training_admitted": False,
            "next_step": "STOP_FOR_PI_WALL_CLOCK_REVIEW" if not quick else "RUN_FULL_F1B",
        },
    }


def write_doc(summary: dict[str, Any]) -> None:
    throughput = summary["throughput"]
    closed_loop = throughput["closed_loop"]
    batched = throughput["batched_action_sequence"]
    gates = summary["protocol_gates"]
    decision = summary["decision"]
    lines = [
        "# M3263 Phase-4 F1b Throughput Optimization",
        "",
        "## Status",
        "",
        "- Verdict: " + decision["f1b_verdict"],
        "- Scope: throughput optimization and wall-clock reprojection only; no F2 launch and no driver-performance claim.",
        "- Remaining bottleneck: " + decision["remaining_bottleneck"],
        "",
        "## Measured",
        "",
        f"- Chrono workers: {throughput['worker_count']} (default full target {throughput['default_full_worker_count']})",
        f"- Steps per unit: {throughput['steps_per_unit']}; batch horizon: {throughput['batch_horizon']}",
        f"- Closed-loop one-step throughput: {closed_loop['aggregate_steps_per_s']:.4f} steps/s",
        f"- Batched action-sequence throughput: {batched['aggregate_steps_per_s']:.4f} steps/s",
        f"- Best aggregate throughput: {throughput['best_aggregate_steps_per_s']:.4f} steps/s",
        f"- Speedup vs F1 baseline: {throughput['speedup_vs_f1_baseline']:.2f}x",
        f"- Projected 100M-step wall-clock from best path: {throughput['best_projected_100m_wall_clock_hours']:.2f} h ({throughput['best_projected_100m_wall_clock_days']:.2f} days)",
        f"- PI target: {throughput['target_aggregate_steps_per_s']:.1f} steps/s ({throughput['target_100m_wall_clock_hours']:.2f} h for 100M)",
        f"- Mixed-regime worker steps: {summary['row_count']} ({summary['regime_step_counts']})",
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
            "F1b reports whether worker scaling plus batched IPC makes the F2 calendar-cost target plausible. A target miss is a completed negative throughput result, not permission to start F2.",
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
            "F2/F3 remain blocked until PI reviews the F1b throughput report and gives the next go.",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_review(summary: dict[str, Any]) -> None:
    REVIEW_MD.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_JSON.parent.mkdir(parents=True, exist_ok=True)
    gates = summary["protocol_gates"]
    lines = [
        "# Review: M3263 Phase-4 F1b Throughput Optimization",
        "",
        "## Findings",
        "",
        "- No F2 launch, PPO run, checkpoint promotion, or incumbent mutation is present in F1b artifacts.",
        "- Target >=1000 steps/s is recorded as a PI feasibility target; missing it remains a reportable F1b result.",
        "- Batched IPC is reported separately from training-equivalent closed-loop stepping.",
        "",
        "## Gate Summary",
        "",
    ]
    for key, value in gates.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Residual Risk",
            "",
            "Batched action-sequence throughput is an IPC-amortization prototype. PI should treat closed-loop one-step throughput as the conservative training-equivalent floor unless F2 explicitly adopts an action-sequence collection design.",
            "",
        ]
    )
    REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")
    write_json(
        REVIEW_JSON,
        {
            "milestone": MILESTONE_ID,
            "reviewed_at_utc": utc_timestamp(),
            "protocol_gates": gates,
            "decision": summary["decision"],
            "risk": "batched action-sequence throughput is not identical to one-step closed-loop policy collection",
        },
    )


def run_benchmark(
    *,
    quick: bool,
    worker_count: int,
    steps_per_unit: int,
    batch_horizon: int,
) -> dict[str, Any]:
    prereg = load_preregistration()
    mode = "quick" if quick else "full"
    started = time.perf_counter()
    stderr_log = STDERR_QUICK_LOG if quick else STDERR_FULL_LOG
    progress = PROGRESS_QUICK_JSONL if quick else PROGRESS_FULL_JSONL
    closed_loop = collect_rollout(
        prereg,
        mode=mode,
        protocol="closed_loop_step",
        worker_count=worker_count,
        steps_per_unit=steps_per_unit,
        batch_horizon=1,
        stderr_log=stderr_log,
        progress=progress,
    )
    batched = collect_rollout(
        prereg,
        mode=mode,
        protocol="batched_action_sequence",
        worker_count=worker_count,
        steps_per_unit=steps_per_unit,
        batch_horizon=batch_horizon,
        stderr_log=stderr_log,
        progress=progress,
    )
    determinism = determinism_replay(prereg, steps=min(max(2, batch_horizon), steps_per_unit), stderr_log=stderr_log)
    summary = summarize(
        prereg,
        closed_loop,
        batched,
        determinism,
        quick=quick,
        elapsed_s=time.perf_counter() - started,
        worker_count=worker_count,
        steps_per_unit=steps_per_unit,
        batch_horizon=batch_horizon,
    )
    rows_path = ROWS_QUICK_CSV if quick else ROWS_FULL_CSV
    metrics_path = METRICS_QUICK_CSV if quick else METRICS_FULL_CSV
    result_path = QUICK_JSON if quick else FULL_JSON
    _write_rows(rows_path, [*closed_loop["rows"], *batched["rows"]])
    write_json(result_path, summary)
    _write_metrics(metrics_path, summary)
    if not quick:
        write_doc(summary)
        write_review(summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-prereg", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Accepted for harness consistency; F1b rewrites deterministic artifacts.")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--steps-per-unit", type=int, default=None)
    parser.add_argument("--batch-horizon", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if sum([bool(args.write_prereg), bool(args.quick), bool(args.full)]) != 1:
        raise SystemExit("choose exactly one of --write-prereg, --quick, or --full")
    if args.write_prereg:
        payload = write_preregistration()
        print(json.dumps({"wrote": str(PREREG_JSON), "protocol": payload["protocol"]}, sort_keys=True))
        return
    quick = bool(args.quick)
    summary = run_benchmark(
        quick=quick,
        worker_count=_worker_count(quick, args.workers),
        steps_per_unit=_steps_per_unit(quick, args.steps_per_unit),
        batch_horizon=_batch_horizon(quick, args.batch_horizon),
    )
    print(
        json.dumps(
            {
                "mode": summary["mode"],
                "decision": summary["decision"],
                "throughput": summary["throughput"],
                "gates": summary["protocol_gates"],
            },
            sort_keys=True,
        )
    )
    if not summary["protocol_gates"]["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
