"""Runtime and inference-cost report for the engineering controller actor."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import statistics
import time
from typing import Any

import numpy as np
import torch

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.hf0_source_only_closed_loop_fixture_pilot import admit_actor_checkpoint
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


DEFAULT_BATCH_SIZES = (1, 8, 32)
DEFAULT_WARMUP_ITERATIONS = 20
DEFAULT_MEASURED_ITERATIONS = 100
DEFAULT_SEED = 2508
DEFAULT_MILESTONE = "m2508-engineering-controller-runtime-inference-cost-report-preflight"
DEFAULT_NEXT_BLOCKER = "m2509-engineering-controller-runtime-inference-cost-report-result-audit"
RUNTIME_FIELDNAMES = [
    "batch_size",
    "iteration_index",
    "device",
    "timed_path",
    "observation_shape",
    "action_shape",
    "forward_time_us",
    "per_sample_time_us",
    "action_finite",
    "action_within_bounds",
    "synthetic_observation_source",
]


@dataclass(frozen=True)
class RuntimeMeasurementRow:
    batch_size: int
    iteration_index: int
    device: str
    timed_path: str
    observation_shape: int
    action_shape: int
    forward_time_us: float
    per_sample_time_us: float
    action_finite: bool
    action_within_bounds: bool
    synthetic_observation_source: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "iteration_index": self.iteration_index,
            "device": self.device,
            "timed_path": self.timed_path,
            "observation_shape": self.observation_shape,
            "action_shape": self.action_shape,
            "forward_time_us": self.forward_time_us,
            "per_sample_time_us": self.per_sample_time_us,
            "action_finite": self.action_finite,
            "action_within_bounds": self.action_within_bounds,
            "synthetic_observation_source": self.synthetic_observation_source,
        }


def parse_batch_sizes(value: str) -> tuple[int, ...]:
    sizes = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not sizes or any(size < 1 for size in sizes):
        raise ValueError("batch sizes must be a comma-separated list of positive integers")
    return sizes


def run_runtime_report(
    output_dir: Path,
    *,
    checkpoint_path: Path | str,
    batch_sizes: tuple[int, ...] = DEFAULT_BATCH_SIZES,
    warmup_iterations: int = DEFAULT_WARMUP_ITERATIONS,
    measured_iterations: int = DEFAULT_MEASURED_ITERATIONS,
    seed: int = DEFAULT_SEED,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, summary = measure_actor_forward_cost(
        checkpoint_path,
        batch_sizes=batch_sizes,
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        seed=seed,
        device=device,
    )
    rows_path = output_dir / "runtime_measurements.csv"
    write_csv_rows(rows_path, [row.to_csv_row() for row in rows], fieldnames=RUNTIME_FIELDNAMES)
    summary.update(
        {
            "milestone": str(milestone),
            "generated_at_utc": utc_timestamp(),
            "runtime_measurements": str(rows_path),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def measure_actor_forward_cost(
    checkpoint_path: Path | str,
    *,
    batch_sizes: tuple[int, ...] = DEFAULT_BATCH_SIZES,
    warmup_iterations: int = DEFAULT_WARMUP_ITERATIONS,
    measured_iterations: int = DEFAULT_MEASURED_ITERATIONS,
    seed: int = DEFAULT_SEED,
    device: str = "cpu",
) -> tuple[list[RuntimeMeasurementRow], dict[str, Any]]:
    if not batch_sizes or any(int(size) < 1 for size in batch_sizes):
        raise ValueError("batch_sizes must contain positive integers")
    if int(warmup_iterations) < 0:
        raise ValueError("warmup_iterations must be non-negative")
    if int(measured_iterations) < 1:
        raise ValueError("measured_iterations must be positive")

    model, admission = admit_actor_checkpoint(checkpoint_path, device=device)
    if model is None:
        return [], _summary_from_rows(
            [],
            checkpoint_path=checkpoint_path,
            model=None,
            batch_sizes=batch_sizes,
            warmup_iterations=warmup_iterations,
            measured_iterations=measured_iterations,
            seed=seed,
            device=device,
            admission_fields=admission.to_summary_fields(),
        )

    rows: list[RuntimeMeasurementRow] = []
    for batch_size in batch_sizes:
        observations = _synthetic_observations(
            batch_size=int(batch_size),
            obs_dim=P0_OBSERVATION_DIM,
            seed=int(seed) + int(batch_size),
        )
        rows.extend(
            _measure_batch_actor_forward(
                model,
                observations,
                batch_size=int(batch_size),
                warmup_iterations=int(warmup_iterations),
                measured_iterations=int(measured_iterations),
            )
        )

    summary = _summary_from_rows(
        rows,
        checkpoint_path=checkpoint_path,
        model=model,
        batch_sizes=batch_sizes,
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        seed=seed,
        device=device,
        admission_fields=admission.to_summary_fields(),
    )
    return rows, summary


def _synthetic_observations(*, batch_size: int, obs_dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    observations = rng.normal(loc=0.0, scale=0.1, size=(batch_size, obs_dim))
    return observations.astype(np.float32)


def _measure_batch_actor_forward(
    model: ActorCritic,
    observations: np.ndarray,
    *,
    batch_size: int,
    warmup_iterations: int,
    measured_iterations: int,
) -> list[RuntimeMeasurementRow]:
    torch_device = next(model.parameters()).device
    obs_t = torch.as_tensor(observations, dtype=torch.float32, device=torch_device)
    hidden = model.initial_hidden(batch_size, torch_device)
    timed_path = "recurrent_features_tensor_plus_actor_mean_tanh"

    with torch.no_grad():
        for _ in range(int(warmup_iterations)):
            _actor_forward(model, obs_t, hidden)
        _sync_if_needed(torch_device)

        rows: list[RuntimeMeasurementRow] = []
        for iteration_index in range(int(measured_iterations)):
            start_ns = time.perf_counter_ns()
            action = _actor_forward(model, obs_t, hidden)
            _sync_if_needed(torch_device)
            elapsed_us = (time.perf_counter_ns() - start_ns) / 1000.0
            rows.append(
                RuntimeMeasurementRow(
                    batch_size=int(batch_size),
                    iteration_index=iteration_index,
                    device=str(torch_device),
                    timed_path=timed_path,
                    observation_shape=int(obs_t.shape[-1]),
                    action_shape=int(action.shape[-1]),
                    forward_time_us=float(elapsed_us),
                    per_sample_time_us=float(elapsed_us / float(batch_size)),
                    action_finite=bool(torch.isfinite(action).all().item()),
                    action_within_bounds=bool(
                        (torch.all(action >= -1.0) & torch.all(action <= 1.0)).item()
                    ),
                    synthetic_observation_source="seeded_normal_shape_only",
                )
            )
    return rows


def _actor_forward(model: ActorCritic, obs_t: torch.Tensor, hidden: torch.Tensor) -> torch.Tensor:
    if not model.is_online_recurrent:
        raise RuntimeError("runtime report requires an online recurrent actor")
    features, _next_hidden = model.recurrent_features_tensor(obs_t, hidden)
    return torch.tanh(model.actor_mean(features))


def _sync_if_needed(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _summary_from_rows(
    rows: list[RuntimeMeasurementRow],
    *,
    checkpoint_path: Path | str,
    model: ActorCritic | None,
    batch_sizes: tuple[int, ...],
    warmup_iterations: int,
    measured_iterations: int,
    seed: int,
    device: str,
    admission_fields: dict[str, Any],
) -> dict[str, Any]:
    by_batch: dict[int, list[RuntimeMeasurementRow]] = {}
    for row in rows:
        by_batch.setdefault(row.batch_size, []).append(row)

    latency_by_batch = {
        str(batch_size): _latency_summary(batch_rows)
        for batch_size, batch_rows in sorted(by_batch.items())
    }
    expected_row_count = len(batch_sizes) * int(measured_iterations)
    all_observation_shape_72 = bool(rows) and all(
        row.observation_shape == P0_OBSERVATION_DIM for row in rows
    )
    all_action_shape_3 = bool(rows) and all(row.action_shape == ACTION_DIM for row in rows)
    all_actions_finite = bool(rows) and all(row.action_finite for row in rows)
    all_actions_within_bounds = bool(rows) and all(row.action_within_bounds for row in rows)
    all_forward_times_positive = bool(rows) and all(row.forward_time_us > 0.0 for row in rows)
    checkpoint_admitted = bool(admission_fields.get("checkpoint_admitted"))
    status_pass = (
        checkpoint_admitted
        and len(rows) == expected_row_count
        and all_observation_shape_72
        and all_action_shape_3
        and all_actions_finite
        and all_actions_within_bounds
        and all_forward_times_positive
        and str(admission_fields.get("checkpoint_actor_encoder")) == "human_view_online_gru"
        and int(admission_fields.get("checkpoint_action_sequence_horizon") or -1) == 1
    )
    return {
        "result_class": "engineering_controller_runtime_inference_cost_report_pass"
        if status_pass
        else "engineering_controller_runtime_inference_cost_report_failed",
        "status_pass": bool(status_pass),
        "checkpoint_path": str(checkpoint_path),
        **admission_fields,
        "checkpoint_file_size_bytes": Path(checkpoint_path).stat().st_size
        if Path(checkpoint_path).exists()
        else None,
        "model_parameter_count": _parameter_count(model),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_encoder": admission_fields.get("checkpoint_actor_encoder"),
        "action_sequence_horizon": admission_fields.get("checkpoint_action_sequence_horizon"),
        "device": str(device),
        "timed_path": "recurrent_features_tensor_plus_actor_mean_tanh",
        "synthetic_observation_source": "seeded_normal_shape_only",
        "batch_sizes": [int(size) for size in batch_sizes],
        "warmup_iterations": int(warmup_iterations),
        "measured_iterations": int(measured_iterations),
        "seed": int(seed),
        "measurement_row_count": len(rows),
        "expected_measurement_row_count": expected_row_count,
        "all_observation_shape_72": bool(all_observation_shape_72),
        "all_action_shape_3": bool(all_action_shape_3),
        "all_actions_finite": bool(all_actions_finite),
        "all_actions_within_bounds": bool(all_actions_within_bounds),
        "all_forward_times_positive": bool(all_forward_times_positive),
        "latency_by_batch": latency_by_batch,
        "actor_forward_pass_run": bool(rows),
        "environment_rollout_run": False,
        "simulator_step_run": False,
        "external_high_fidelity_simulation_included": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "action_outputs_interpreted_as_control": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def _latency_summary(rows: list[RuntimeMeasurementRow]) -> dict[str, float | int]:
    forward_times = [row.forward_time_us for row in rows]
    per_sample = [row.per_sample_time_us for row in rows]
    return {
        "measurement_count": len(rows),
        "forward_time_us_min": float(min(forward_times)),
        "forward_time_us_mean": float(statistics.fmean(forward_times)),
        "forward_time_us_p50": float(statistics.median(forward_times)),
        "forward_time_us_max": float(max(forward_times)),
        "per_sample_time_us_mean": float(statistics.fmean(per_sample)),
        "per_sample_time_us_p50": float(statistics.median(per_sample)),
    }


def _parameter_count(model: ActorCritic | None) -> int | None:
    if model is None:
        return None
    return int(sum(parameter.numel() for parameter in model.parameters()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Write engineering-controller runtime report.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--batch-sizes", default=",".join(str(size) for size in DEFAULT_BATCH_SIZES))
    parser.add_argument("--warmup-iterations", type=int, default=DEFAULT_WARMUP_ITERATIONS)
    parser.add_argument("--measured-iterations", type=int, default=DEFAULT_MEASURED_ITERATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = run_runtime_report(
        args.output_dir,
        checkpoint_path=args.checkpoint,
        batch_sizes=parse_batch_sizes(args.batch_sizes),
        warmup_iterations=args.warmup_iterations,
        measured_iterations=args.measured_iterations,
        seed=args.seed,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"measurement_row_count={summary['measurement_row_count']}")
    print(f"runtime_measurements={summary['runtime_measurements']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
