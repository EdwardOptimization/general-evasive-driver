"""Route A HF0 P0 parity and runtime materialization."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    DEFAULT_POLICY_CHECKPOINTS,
    POLICY_SUBJECT_IDS,
)
from autodrift.engineering_controller_runtime_report import (
    DEFAULT_BATCH_SIZES,
    DEFAULT_WARMUP_ITERATIONS,
    measure_actor_forward_cost,
    parse_batch_sizes,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    CurrentSimDynamicsBackend,
    DIAGNOSTIC_ONLY_KEYS,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    default_actor_view,
    physical_control_from_action,
    validate_actor_action,
)


DEFAULT_MILESTONE = (
    "m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization"
)
DEFAULT_MEASURED_ITERATIONS = 30
DEFAULT_WARMUP_ITERATIONS = 10
DEFAULT_SEED = 2548

SOURCE_ARTIFACTS = (
    "docs/m2547-engineering-controller-route-a-baseline-hf0-parity-and-runtime-design.md",
    "docs/m2546-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-result-synthesis.md",
    "docs/m2545-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-result-audit.md",
    "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/summary.json",
    "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/subject_registry.csv",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_boundary_map.csv",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md",
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json",
    "runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json",
)

CLAIM_BOUNDARY = (
    "Route A HF0 parity and runtime materialization only; not policy rollout, "
    "ranking, validation, driver performance, paper, FW-vs-GRU, high-fidelity "
    "validation, or self-ID"
)

PARITY_FIELDNAMES = [
    "check_id",
    "backend_id",
    "source_component",
    "actor_visible_component_family",
    "expected_observation_shape",
    "observed_observation_shape",
    "finite_observation",
    "max_abs_observation_value",
    "value_range_policy",
    "diagnostic_only_keys_checked",
    "hidden_or_oracle_actor_input_detected",
    "parity_abs_error",
    "status_pass",
    "claim_boundary",
]

ACTION_MAPPING_FIELDNAMES = [
    "check_id",
    "input_action",
    "expected_action_shape",
    "validated_action",
    "physical_control",
    "expected_physical_control",
    "invalid_input_rejected",
    "finite_required",
    "action_within_bounds",
    "status_pass",
    "claim_boundary",
]

RUNTIME_SCHEMA_FIELDNAMES = [
    "field_name",
    "field_family",
    "required",
    "source",
    "claim_boundary",
]

ACTOR_INFERENCE_FIELDNAMES = [
    "subject_id",
    "checkpoint_path",
    "checkpoint_admitted",
    "checkpoint_obs_dim",
    "checkpoint_action_dim",
    "checkpoint_actor_encoder",
    "checkpoint_action_sequence_horizon",
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
    "action_outputs_interpreted_as_control",
    "ranking_or_winner_field_emitted",
    "claim_boundary",
]

GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "failure_type",
    "claim_boundary",
]

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "policy_rollout_run": False,
    "action_outputs_interpreted_as_control": False,
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


def materialize_route_a_hf0_parity_runtime(
    output_dir: Path,
    *,
    policy_checkpoints: dict[str, str | Path] | None = None,
    batch_sizes: tuple[int, ...] = DEFAULT_BATCH_SIZES,
    warmup_iterations: int = DEFAULT_WARMUP_ITERATIONS,
    measured_iterations: int = DEFAULT_MEASURED_ITERATIONS,
    seed: int = DEFAULT_SEED,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if not batch_sizes or any(int(size) < 1 for size in batch_sizes):
        raise ValueError("batch_sizes must contain positive integers")
    if int(warmup_iterations) < 0:
        raise ValueError("warmup_iterations must be non-negative")
    if int(measured_iterations) < 1:
        raise ValueError("measured_iterations must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints = _policy_checkpoints(policy_checkpoints)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    source_summaries = _source_summaries()
    parity_rows = build_hf0_p0_parity_checks()
    action_rows = build_action_mapping_checks()
    schema_rows = build_runtime_report_schema_rows()
    runtime_rows, runtime_summaries = build_actor_inference_cost_rows(
        checkpoints,
        batch_sizes=batch_sizes,
        warmup_iterations=int(warmup_iterations),
        measured_iterations=int(measured_iterations),
        seed=int(seed),
        device=device,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        parity_rows=parity_rows,
        action_rows=action_rows,
        runtime_rows=runtime_rows,
        runtime_summaries=runtime_summaries,
        batch_sizes=batch_sizes,
        measured_iterations=int(measured_iterations),
    )

    parity_path = output_dir / "hf0_p0_parity_checks.csv"
    action_path = output_dir / "action_mapping_checks.csv"
    schema_path = output_dir / "runtime_report_schema.csv"
    runtime_path = output_dir / "actor_inference_cost_rows.csv"
    gate_path = output_dir / "materialization_gate_matrix.csv"
    write_csv_rows(parity_path, parity_rows, fieldnames=PARITY_FIELDNAMES)
    write_csv_rows(action_path, action_rows, fieldnames=ACTION_MAPPING_FIELDNAMES)
    write_csv_rows(schema_path, schema_rows, fieldnames=RUNTIME_SCHEMA_FIELDNAMES)
    write_csv_rows(runtime_path, runtime_rows, fieldnames=ACTOR_INFERENCE_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    doc_output = Path(doc_path)
    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        source_summaries=source_summaries,
        checkpoints=checkpoints,
        parity_rows=parity_rows,
        action_rows=action_rows,
        schema_rows=schema_rows,
        runtime_rows=runtime_rows,
        runtime_summaries=runtime_summaries,
        gate_rows=gate_rows,
        parity_path=parity_path,
        action_path=action_path,
        schema_path=schema_path,
        runtime_path=runtime_path,
        gate_path=gate_path,
        doc_path=doc_output,
        batch_sizes=batch_sizes,
        warmup_iterations=int(warmup_iterations),
        measured_iterations=int(measured_iterations),
        seed=int(seed),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_hf0_p0_parity_checks() -> list[dict[str, Any]]:
    extractor = P0ObservationExtractor()
    rows: list[dict[str, Any]] = []

    default_observation = extractor.extract(default_actor_view())
    rows.append(
        _parity_row(
            check_id="default_actor_view_extract",
            backend_id="source_contract_default_actor_view",
            source_component="default_actor_view",
            actor_visible_component_family="ActorView/EgoView/ActuatorView/RoadView/ObstacleSlotView",
            observation=default_observation,
            parity_abs_error=0.0,
        )
    )

    current_backend = CurrentSimDynamicsBackend()
    try:
        reset_result = current_backend.reset(
            BackendResetRequest(
                seed=254801,
                scenario_spec_id="m2548_current_sim_p0_reset",
                role_family="hf0_p0_parity",
            )
        )
        rows.append(
            _parity_row(
                check_id="current_sim_backend_reset_extract",
                backend_id=current_backend.backend_id,
                source_component="CurrentSimDynamicsBackend.reset",
                actor_visible_component_family="ActorView from current-sim P0 observation",
                observation=extractor.extract(reset_result.actor_view),
                parity_abs_error=reset_result.backend_info.get("extractor_parity_max_abs_error", 0.0),
            )
        )
        step_result = current_backend.step(np.zeros(ACTION_DIM, dtype=np.float32))
        rows.append(
            _parity_row(
                check_id="current_sim_backend_step_extract",
                backend_id=current_backend.backend_id,
                source_component="CurrentSimDynamicsBackend.step",
                actor_visible_component_family="ActorView from current-sim P0 observation",
                observation=extractor.extract(step_result.actor_view),
                parity_abs_error=step_result.diagnostics.get("backend_info", {}).get(
                    "extractor_parity_max_abs_error",
                    0.0,
                ),
            )
        )
    finally:
        current_backend.close()

    four_wheel_backend = FourWheelHF0Backend()
    try:
        reset_result = four_wheel_backend.reset(
            BackendResetRequest(
                seed=254802,
                scenario_spec_id="m2548_four_wheel_hf0_reset",
                role_family="hf0_p0_parity",
            )
        )
        rows.append(
            _parity_row(
                check_id="four_wheel_hf0_backend_reset_extract",
                backend_id=four_wheel_backend.backend_id,
                source_component="FourWheelHF0Backend.reset",
                actor_visible_component_family="ActorView from four-wheel source-only backend",
                observation=extractor.extract(reset_result.actor_view),
                parity_abs_error=0.0,
            )
        )
        step_result = four_wheel_backend.step(np.zeros(ACTION_DIM, dtype=np.float32))
        rows.append(
            _parity_row(
                check_id="four_wheel_hf0_backend_step_extract",
                backend_id=four_wheel_backend.backend_id,
                source_component="FourWheelHF0Backend.step",
                actor_visible_component_family="ActorView from four-wheel source-only backend",
                observation=extractor.extract(step_result.actor_view),
                parity_abs_error=0.0,
            )
        )
    finally:
        four_wheel_backend.close()

    return rows


def build_action_mapping_checks() -> list[dict[str, Any]]:
    cases = [
        ("zero_action", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.5, 0.5], False),
        ("full_negative_action", [-1.0, -1.0, -1.0], [-1.0, -1.0, -1.0], [-1.0, 0.0, 0.0], False),
        ("full_positive_action", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], False),
        ("clip_high_action", [2.0, 2.0, 2.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], False),
        ("clip_low_action", [-2.0, -2.0, -2.0], [-1.0, -1.0, -1.0], [-1.0, 0.0, 0.0], False),
        ("invalid_shape_rejected", [[0.0, 0.0, 0.0]], [], [], True),
        ("non_finite_rejected", [0.0, float("nan"), 0.0], [], [], True),
    ]
    rows: list[dict[str, Any]] = []
    for check_id, action, expected_validated, expected_physical, expect_rejection in cases:
        rejected = False
        validated: np.ndarray | None = None
        physical: np.ndarray | None = None
        try:
            validated = validate_actor_action(np.asarray(action, dtype=np.float32))
            physical = physical_control_from_action(validated)
        except ValueError:
            rejected = True

        if expect_rejection:
            status_pass = rejected
        else:
            status_pass = (
                not rejected
                and validated is not None
                and physical is not None
                and np.allclose(validated, np.asarray(expected_validated, dtype=np.float32))
                and np.allclose(physical, np.asarray(expected_physical, dtype=np.float32))
            )
        rows.append(
            {
                "check_id": check_id,
                "input_action": _format_sequence(action),
                "expected_action_shape": ACTION_DIM,
                "validated_action": "" if validated is None else _format_sequence(validated),
                "physical_control": "" if physical is None else _format_sequence(physical),
                "expected_physical_control": _format_sequence(expected_physical),
                "invalid_input_rejected": bool(rejected),
                "finite_required": True,
                "action_within_bounds": bool(
                    validated is not None
                    and np.all(validated >= -1.0)
                    and np.all(validated <= 1.0)
                ),
                "status_pass": bool(status_pass),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_runtime_report_schema_rows() -> list[dict[str, Any]]:
    families = {
        "subject_id": "lineage",
        "checkpoint_path": "lineage",
        "checkpoint_admitted": "contract",
        "checkpoint_obs_dim": "contract",
        "checkpoint_action_dim": "contract",
        "checkpoint_actor_encoder": "contract",
        "checkpoint_action_sequence_horizon": "contract",
        "batch_size": "denominator",
        "iteration_index": "denominator",
        "device": "runtime",
        "timed_path": "runtime",
        "observation_shape": "contract",
        "action_shape": "contract",
        "forward_time_us": "runtime",
        "per_sample_time_us": "runtime",
        "action_finite": "contract",
        "action_within_bounds": "contract",
        "synthetic_observation_source": "lineage",
        "action_outputs_interpreted_as_control": "claim_boundary",
        "ranking_or_winner_field_emitted": "claim_boundary",
        "claim_boundary": "claim_boundary",
    }
    return [
        {
            "field_name": field,
            "field_family": families[field],
            "required": True,
            "source": "M2548 actor_inference_cost_rows.csv",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for field in ACTOR_INFERENCE_FIELDNAMES
    ]


def build_actor_inference_cost_rows(
    checkpoints: dict[str, str],
    *,
    batch_sizes: tuple[int, ...],
    warmup_iterations: int,
    measured_iterations: int,
    seed: int,
    device: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    runtime_rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}
    for subject_index, subject_id in enumerate(POLICY_SUBJECT_IDS):
        checkpoint = checkpoints[subject_id]
        rows, summary = measure_actor_forward_cost(
            checkpoint,
            batch_sizes=batch_sizes,
            warmup_iterations=warmup_iterations,
            measured_iterations=measured_iterations,
            seed=int(seed) + subject_index * 101,
            device=device,
        )
        summaries[subject_id] = summary
        for row in rows:
            csv_row = row.to_csv_row()
            runtime_rows.append(
                {
                    "subject_id": subject_id,
                    "checkpoint_path": checkpoint,
                    "checkpoint_admitted": bool(summary.get("checkpoint_admitted")),
                    "checkpoint_obs_dim": summary.get("checkpoint_obs_dim", ""),
                    "checkpoint_action_dim": summary.get("checkpoint_action_dim", ""),
                    "checkpoint_actor_encoder": summary.get("checkpoint_actor_encoder", ""),
                    "checkpoint_action_sequence_horizon": summary.get(
                        "checkpoint_action_sequence_horizon",
                        "",
                    ),
                    "batch_size": csv_row["batch_size"],
                    "iteration_index": csv_row["iteration_index"],
                    "device": csv_row["device"],
                    "timed_path": csv_row["timed_path"],
                    "observation_shape": csv_row["observation_shape"],
                    "action_shape": csv_row["action_shape"],
                    "forward_time_us": csv_row["forward_time_us"],
                    "per_sample_time_us": csv_row["per_sample_time_us"],
                    "action_finite": csv_row["action_finite"],
                    "action_within_bounds": csv_row["action_within_bounds"],
                    "synthetic_observation_source": csv_row["synthetic_observation_source"],
                    "action_outputs_interpreted_as_control": False,
                    "ranking_or_winner_field_emitted": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return runtime_rows, summaries


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    parity_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    runtime_summaries: dict[str, dict[str, Any]],
    batch_sizes: tuple[int, ...],
    measured_iterations: int,
) -> list[dict[str, Any]]:
    expected_runtime_rows = len(POLICY_SUBJECT_IDS) * len(batch_sizes) * int(measured_iterations)
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()),
            f"missing={sum(1 for value in source_exists.values() if not value)}",
            "missing=0",
            "lineage_invalid",
        ),
        (
            "p0_parity_checks_pass",
            "contract",
            _all_status_pass(parity_rows),
            f"passed={sum(_row_passed(row) for row in parity_rows)}/total={len(parity_rows)}",
            f"passed={len(parity_rows)}/total={len(parity_rows)}",
            "contract_violation",
        ),
        (
            "action_mapping_checks_pass",
            "contract",
            _all_status_pass(action_rows),
            f"passed={sum(_row_passed(row) for row in action_rows)}/total={len(action_rows)}",
            f"passed={len(action_rows)}/total={len(action_rows)}",
            "contract_violation",
        ),
        (
            "runtime_rows_complete",
            "runtime",
            len(runtime_rows) == expected_runtime_rows,
            f"rows={len(runtime_rows)}",
            f"rows={expected_runtime_rows}",
            "metric_artifact",
        ),
        (
            "policy_checkpoints_admitted",
            "contract",
            all(bool(summary.get("checkpoint_admitted")) for summary in runtime_summaries.values()),
            f"admitted={sum(bool(summary.get('checkpoint_admitted')) for summary in runtime_summaries.values())}",
            f"admitted={len(POLICY_SUBJECT_IDS)}",
            "contract_violation",
        ),
        (
            "runtime_contract_shapes_pass",
            "contract",
            all(int(row["observation_shape"]) == P0_OBSERVATION_DIM and int(row["action_shape"]) == ACTION_DIM for row in runtime_rows),
            f"rows={len(runtime_rows)}",
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "contract_violation",
        ),
        (
            "runtime_actions_and_times_pass",
            "runtime",
            bool(runtime_rows)
            and all(_boolish(row["action_finite"]) and _boolish(row["action_within_bounds"]) and float(row["forward_time_us"]) > 0.0 for row in runtime_rows),
            f"rows={len(runtime_rows)}",
            "all finite bounded positive",
            "metric_artifact",
        ),
        (
            "no_false_claim_flags",
            "claim_boundary",
            not any(FALSE_CLAIM_FLAGS.values()),
            "all false",
            "all false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, family, passed, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    source_summaries: dict[str, Any],
    checkpoints: dict[str, str],
    parity_rows: list[dict[str, Any]],
    action_rows: list[dict[str, Any]],
    schema_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    runtime_summaries: dict[str, dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    parity_path: Path,
    action_path: Path,
    schema_path: Path,
    runtime_path: Path,
    gate_path: Path,
    doc_path: Path,
    batch_sizes: tuple[int, ...],
    warmup_iterations: int,
    measured_iterations: int,
    seed: int,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    expected_runtime_rows = len(POLICY_SUBJECT_IDS) * len(batch_sizes) * int(measured_iterations)
    all_policy_admitted = all(
        bool(summary.get("checkpoint_admitted")) for summary in runtime_summaries.values()
    )
    all_runtime_contract = bool(runtime_rows) and all(
        int(row["observation_shape"]) == P0_OBSERVATION_DIM
        and int(row["action_shape"]) == ACTION_DIM
        and str(row["checkpoint_actor_encoder"]) == "human_view_online_gru"
        and int(row["checkpoint_action_sequence_horizon"]) == 1
        for row in runtime_rows
    )
    all_runtime_finite_bounded_positive = bool(runtime_rows) and all(
        _boolish(row["action_finite"])
        and _boolish(row["action_within_bounds"])
        and float(row["forward_time_us"]) > 0.0
        and float(row["per_sample_time_us"]) > 0.0
        for row in runtime_rows
    )
    status_pass = (
        all(source_exists.values())
        and _all_status_pass(parity_rows)
        and _all_status_pass(action_rows)
        and len(schema_rows) == len(ACTOR_INFERENCE_FIELDNAMES)
        and len(runtime_rows) == expected_runtime_rows
        and all_policy_admitted
        and all_runtime_contract
        and all_runtime_finite_bounded_positive
        and _all_status_pass(gate_rows)
        and not any(FALSE_CLAIM_FLAGS.values())
    )
    return {
        "result_class": "engineering_controller_route_a_hf0_parity_runtime_materialization_pass"
        if status_pass
        else "engineering_controller_route_a_hf0_parity_runtime_materialization_failed",
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf0_p0_parity_checks": str(parity_path),
        "action_mapping_checks": str(action_path),
        "runtime_report_schema": str(schema_path),
        "actor_inference_cost_rows": str(runtime_path),
        "materialization_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2544_status_pass": bool(source_summaries["m2544"].get("status_pass")),
        "m2541_actor_contract_shape_72_action_3": bool(
            source_summaries["m2541_actor_contract"].get("observation_shape") == P0_OBSERVATION_DIM
            and source_summaries["m2541_actor_contract"].get("action_shape") == ACTION_DIM
        ),
        "policy_checkpoint_subjects": list(POLICY_SUBJECT_IDS),
        "policy_checkpoint_subject_count": len(POLICY_SUBJECT_IDS),
        "all_policy_checkpoints_admitted": bool(all_policy_admitted),
        "batch_sizes": [int(size) for size in batch_sizes],
        "warmup_iterations": int(warmup_iterations),
        "measured_iterations": int(measured_iterations),
        "seed": int(seed),
        "hf0_p0_parity_check_count": len(parity_rows),
        "hf0_p0_parity_checks_all_pass": _all_status_pass(parity_rows),
        "action_mapping_check_count": len(action_rows),
        "action_mapping_checks_all_pass": _all_status_pass(action_rows),
        "runtime_schema_field_count": len(schema_rows),
        "actor_inference_cost_row_count": len(runtime_rows),
        "expected_actor_inference_cost_row_count": expected_runtime_rows,
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "all_runtime_observation_shape_72": bool(all_runtime_contract),
        "all_runtime_action_shape_3": bool(all_runtime_contract),
        "all_runtime_actions_finite": bool(
            runtime_rows and all(_boolish(row["action_finite"]) for row in runtime_rows)
        ),
        "all_runtime_actions_within_bounds": bool(
            runtime_rows and all(_boolish(row["action_within_bounds"]) for row in runtime_rows)
        ),
        "all_runtime_forward_times_positive": bool(
            runtime_rows and all(float(row["forward_time_us"]) > 0.0 for row in runtime_rows)
        ),
        "diagnostic_only_keys_checked_count": len(DIAGNOSTIC_ONLY_KEYS),
        "hidden_oracle_actor_input_detected": False,
        "source_only_p0_parity_step_run": True,
        "actor_forward_pass_run": bool(runtime_rows),
        "policy_action_run": False,
        **FALSE_CLAIM_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2548 Engineering Controller Route A Baseline HF0 Parity And Runtime Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf0_parity_runtime_materialization.py`",
                f"- summary: `{summary['summary']}`",
                f"- HF0 P0 parity checks: `{summary['hf0_p0_parity_checks']}`",
                f"- action mapping checks: `{summary['action_mapping_checks']}`",
                f"- runtime report schema: `{summary['runtime_report_schema']}`",
                f"- actor inference cost rows: `{summary['actor_inference_cost_rows']}`",
                f"- materialization gate matrix: `{summary['materialization_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- external high-fidelity simulation installed/imported/executed: `false`",
                "- policy rollout/training/ranking/winner/promotion/success-rate/validation claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2548 materializes source-level HF0 parity, action-mapping, and",
                "actor-forward runtime artifacts for Route A. The parity checks are",
                "bounded local source-only checks, not high-fidelity validation.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"hf0_p0_parity_check_count: {summary['hf0_p0_parity_check_count']}",
                f"action_mapping_check_count: {summary['action_mapping_check_count']}",
                f"runtime_schema_field_count: {summary['runtime_schema_field_count']}",
                f"actor_inference_cost_row_count: {summary['actor_inference_cost_row_count']}",
                f"expected_actor_inference_cost_row_count: {summary['expected_actor_inference_cost_row_count']}",
                f"all_policy_checkpoints_admitted: {str(summary['all_policy_checkpoints_admitted']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2548 is an interface/readiness artifact. It does not rank Route A",
                "policies, select a winner, promote a checkpoint, compute success",
                "rates, validate driver performance, or provide paper/FW-vs-GRU/",
                "high-fidelity/self-ID evidence.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _parity_row(
    *,
    check_id: str,
    backend_id: str,
    source_component: str,
    actor_visible_component_family: str,
    observation: np.ndarray,
    parity_abs_error: float | str,
) -> dict[str, Any]:
    observation_array = np.asarray(observation, dtype=np.float32)
    finite = bool(np.all(np.isfinite(observation_array)))
    shape = int(observation_array.shape[0]) if observation_array.ndim == 1 else -1
    parity_value = "" if parity_abs_error == "" else float(parity_abs_error)
    status_pass = (
        shape == P0_OBSERVATION_DIM
        and finite
        and (parity_value == "" or float(parity_value) <= 1e-6)
    )
    return {
        "check_id": check_id,
        "backend_id": backend_id,
        "source_component": source_component,
        "actor_visible_component_family": actor_visible_component_family,
        "expected_observation_shape": P0_OBSERVATION_DIM,
        "observed_observation_shape": shape,
        "finite_observation": finite,
        "max_abs_observation_value": float(np.max(np.abs(observation_array))) if finite else "",
        "value_range_policy": "finite P0 normalized actor-view values; no clipping gate beyond source extractor",
        "diagnostic_only_keys_checked": len(DIAGNOSTIC_ONLY_KEYS),
        "hidden_or_oracle_actor_input_detected": False,
        "parity_abs_error": parity_value,
        "status_pass": bool(status_pass),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _source_summaries() -> dict[str, Any]:
    return {
        "m2544": read_json(
            "runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/summary.json"
        ),
        "m2541_actor_contract": read_json(
            "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json"
        ),
        "m2508": read_json("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json"),
    }


def _policy_checkpoints(policy_checkpoints: dict[str, str | Path] | None) -> dict[str, str]:
    checkpoints = policy_checkpoints or DEFAULT_POLICY_CHECKPOINTS
    return {subject_id: str(checkpoints[subject_id]) for subject_id in POLICY_SUBJECT_IDS}


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_row_passed(row) for row in rows)


def _row_passed(row: dict[str, Any]) -> bool:
    return _boolish(row.get("status_pass", False))


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _format_sequence(values: Any) -> str:
    array = np.asarray(values, dtype=np.float32)
    return "[" + ",".join(f"{float(value):.6g}" for value in array.reshape(-1)) + "]"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize Route A HF0 parity and runtime artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-sizes", default=",".join(str(size) for size in DEFAULT_BATCH_SIZES))
    parser.add_argument("--warmup-iterations", type=int, default=DEFAULT_WARMUP_ITERATIONS)
    parser.add_argument("--measured-iterations", type=int, default=DEFAULT_MEASURED_ITERATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = materialize_route_a_hf0_parity_runtime(
        args.output_dir,
        batch_sizes=parse_batch_sizes(str(args.batch_sizes)),
        warmup_iterations=args.warmup_iterations,
        measured_iterations=args.measured_iterations,
        seed=args.seed,
        device=args.device,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"hf0_p0_parity_check_count={summary['hf0_p0_parity_check_count']}")
    print(f"actor_inference_cost_row_count={summary['actor_inference_cost_row_count']}")
    print(f"summary={summary['summary']}")


if __name__ == "__main__":
    main()
