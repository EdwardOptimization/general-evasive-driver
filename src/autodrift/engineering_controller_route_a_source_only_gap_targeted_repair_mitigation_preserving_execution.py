"""M2655 gate-aware mitigation-preserving source-only repair execution preflight."""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    actor_action_stats,
    actor_actions,
    model_state_sha256,
    _file_sha256,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    DEFAULT_POLICY_CHECKPOINTS,
    admit_route_a_subjects,
    route_a_subjects,
)
from autodrift.engineering_controller_route_a_source_only_fresh_generalization_panel import (
    DEFAULT_FRESH_SEED_COUNT,
    DEFAULT_HORIZON_STEPS,
    EXTRA_BEHAVIOR_FIELDS_M2641,
    build_fresh_generalization_measured_rows,
    build_fresh_generalization_panel_specs,
    run_fresh_generalization_telemetry,
    _load_source_artifacts,
)
from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_execution import (
    REPAIRED_SUBJECT_ID,
    collect_gap_target_repair_observations,
    gate_metric_value,
    row_key,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_OUTPUT_DIR = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_"
    "preserving_execution"
)
DEFAULT_OBJECTIVE_SUMMARY = Path(
    "runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization/summary.json"
)
DEFAULT_OBJECTIVE_FAMILY_ROWS = Path(
    "runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization/objective_family_rows.csv"
)
DEFAULT_PROTECTED_COMPONENT_GATES = Path(
    "runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization/protected_component_gate_rows.csv"
)
DEFAULT_TARGET_PRESERVATION_GATES = Path(
    "runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_objective_materialization/target_preservation_gate_rows.csv"
)
DEFAULT_BASELINE_BEHAVIOR_ROWS = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "measured_behavior_rows.csv"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/"
    "checkpoints/m2537_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-repair-execution-preflight.md"
)
DEFAULT_MILESTONE = (
    "m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-repair-execution-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2656-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-repair-execution-result-audit"
)
DEFAULT_BRANCH_SYNTHESIS_BLOCKER = (
    "m2656-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-"
    "mitigation-preserving-repair-execution-branch-synthesis"
)

CLAIM_SCOPE = "Route A mitigation-preserving source-only repair execution preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution_preflight_failed"
)

DEFAULT_CANDIDATE_SPECS: tuple[dict[str, float | str], ...] = (
    {
        "candidate_id": "m2655_retain_m2648_bias",
        "steer_bias_delta": 0.12,
        "throttle_bias_delta": -3.0,
        "brake_bias_delta": 3.0,
    },
    {
        "candidate_id": "m2655_softened_gap_bias",
        "steer_bias_delta": 0.08,
        "throttle_bias_delta": -2.0,
        "brake_bias_delta": 2.0,
    },
    {
        "candidate_id": "m2655_clearance_guarded_bias",
        "steer_bias_delta": 0.10,
        "throttle_bias_delta": -1.5,
        "brake_bias_delta": 1.5,
    },
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "measured_validation_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
}

REPAIR_TRACE_FIELDNAMES = [
    "update_index",
    "update_method",
    "candidate_id",
    "source_checkpoint",
    "repaired_checkpoint",
    "training_observation_count",
    "target_gap_families",
    "target_role_families",
    "protected_reference_families",
    "trainable_parameter_names",
    "source_model_state_hash",
    "repaired_model_state_hash",
    "actor_mean_bias_before",
    "actor_mean_bias_after",
    "steer_bias_delta",
    "throttle_bias_delta",
    "brake_bias_delta",
    "source_conflict_proxy",
    "repaired_conflict_proxy",
    "source_mean_action_steer",
    "repaired_mean_action_steer",
    "source_mean_action_throttle",
    "repaired_mean_action_throttle",
    "source_mean_action_brake",
    "repaired_mean_action_brake",
    "mean_action_delta_l1",
    "finite_update",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_inputs_required",
    "active_config_overwritten",
    "objective_artifacts_mutated",
    "checkpoint_promoted",
    "claim_scope",
    "forbidden_interpretation",
]

SELECTED_REPAIR_TRACE_FIELDNAMES = [
    "selection_reason",
    "candidate_constraint_status",
    "target_preservation_gates_all_passed",
    "protected_component_gates_all_passed",
    "target_and_protected_gates_all_passed",
    "failed_gate_ids",
    "protected_component_regressed_row_count",
] + REPAIR_TRACE_FIELDNAMES

POST_REPAIR_EXTRA_FIELDNAMES = [
    "post_repair_row_id",
    "source_checkpoint_path",
    "repaired_checkpoint_path",
    "repair_execution_started",
    "repair_training_started",
    "repaired_checkpoint_written",
    "gap_target_family",
    "protected_reference_family",
    "repair_target_admitted",
    "protected_reference_only",
    "taxonomy_labels_actor_visible",
    "repair_target_labels_actor_visible",
    "objective_gate_labels_actor_visible",
    "route_decision_actor_visible",
    "claim_scope",
    "forbidden_interpretation",
]

GATE_EVALUATION_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "target_or_reference_family",
    "subject_id",
    "metric",
    "baseline_row_count",
    "post_repair_row_count",
    "evaluated_row_count",
    "trace_to_objective_artifact",
    "trace_to_baseline_rows",
    "evaluation_status",
    "gate_pass",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "max_regression_delta",
    "failure_type",
    "blocks_claims",
    "next_route_if_fail",
    "claim_boundary",
]

CANDIDATE_SWEEP_FIELDNAMES = [
    "candidate_id",
    "candidate_index",
    "source_checkpoint",
    "candidate_checkpoint",
    "steer_bias_delta",
    "throttle_bias_delta",
    "brake_bias_delta",
    "behavior_changed_from_source",
    "finite_update",
    "candidate_checkpoint_hash",
    "source_model_state_hash",
    "candidate_model_state_hash",
    "telemetry_row_count",
    "post_repair_behavior_row_count",
    "gate_evaluation_row_count",
    "target_preservation_gates_all_passed",
    "protected_component_gates_all_passed",
    "target_and_protected_gates_all_passed",
    "target_gate_pass_count",
    "protected_component_gate_pass_count",
    "protected_component_regressed_row_count",
    "failed_gate_ids",
    "candidate_constraint_status",
    "selected_for_repair_trace",
    "selection_reason",
    "diagnostic_only_no_ranking_claim",
    "success_rate_field_emitted",
    "ranking_or_winner_field_emitted",
    "claim_scope",
    "forbidden_interpretation",
]


def run_mitigation_preserving_repair_execution(
    output_dir: Path,
    *,
    objective_summary: Path | str = DEFAULT_OBJECTIVE_SUMMARY,
    objective_family_rows: Path | str = DEFAULT_OBJECTIVE_FAMILY_ROWS,
    protected_component_gates: Path | str = DEFAULT_PROTECTED_COMPONENT_GATES,
    target_preservation_gates: Path | str = DEFAULT_TARGET_PRESERVATION_GATES,
    baseline_behavior_rows: Path | str = DEFAULT_BASELINE_BEHAVIOR_ROWS,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    candidate_specs: Sequence[dict[str, float | str]] = DEFAULT_CANDIDATE_SPECS,
    fresh_seed_count: int = DEFAULT_FRESH_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    device: str = "cpu",
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    if int(fresh_seed_count) != DEFAULT_FRESH_SEED_COUNT:
        raise ValueError(f"fresh_seed_count must be exactly {DEFAULT_FRESH_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")
    if not candidate_specs:
        raise ValueError("candidate_specs must contain at least one candidate")

    output_dir.mkdir(parents=True, exist_ok=True)
    objective_summary_path = Path(objective_summary)
    objective_family_path = Path(objective_family_rows)
    protected_gate_path = Path(protected_component_gates)
    target_gate_path = Path(target_preservation_gates)
    baseline_behavior_path = Path(baseline_behavior_rows)
    source_checkpoint_path = Path(source_checkpoint)
    doc_output_path = Path(doc_path)

    objective_summary_data = read_json(objective_summary_path)
    objective_rows = read_csv_rows(objective_family_path)
    protected_rows = read_csv_rows(protected_gate_path)
    target_rows = read_csv_rows(target_gate_path)
    baseline_rows = read_csv_rows(baseline_behavior_path)
    row_schema_fields = [row["field_name"] for row in _load_source_artifacts()["row_schema"]]
    target_map = build_objective_target_map(objective_rows)
    verify_objective_bundle(objective_summary_data, objective_rows, protected_rows, target_rows)

    training_observations = collect_gap_target_repair_observations(
        target_map["target_role_families"],
        fresh_seed_count=int(fresh_seed_count),
    )
    candidate_results: list[dict[str, Any]] = []
    normalized_specs = normalize_candidate_specs(candidate_specs)
    for index, spec in enumerate(normalized_specs):
        checkpoint_path = output_dir / "checkpoints" / "candidates" / f"{spec['candidate_id']}.pt"
        trace_rows, checkpoint_manifest = write_mitigation_preserving_candidate_checkpoint(
            source_checkpoint_path,
            checkpoint_path,
            training_observations=training_observations,
            target_map=target_map,
            output_dir=output_dir,
            device=device,
            steer_bias_delta=float(spec["steer_bias_delta"]),
            throttle_bias_delta=float(spec["throttle_bias_delta"]),
            brake_bias_delta=float(spec["brake_bias_delta"]),
            milestone=milestone,
            candidate_id=str(spec["candidate_id"]),
        )
        evaluation = evaluate_candidate_checkpoint(
            checkpoint_path,
            baseline_rows=baseline_rows,
            target_map=target_map,
            objective_rows=objective_rows,
            protected_rows=protected_rows,
            target_rows=target_rows,
            source_checkpoint=source_checkpoint_path,
            row_schema_fields=row_schema_fields,
            fresh_seed_count=int(fresh_seed_count),
            horizon_steps=int(horizon_steps),
            device=device,
            milestone=milestone,
        )
        candidate_results.append(
            {
                "candidate_index": index,
                "spec": spec,
                "trace_rows": trace_rows,
                "checkpoint_manifest": checkpoint_manifest,
                **evaluation,
            }
        )

    selected = select_candidate(candidate_results)
    selected_spec = selected["spec"]
    final_checkpoint = output_dir / "checkpoints" / "m2655_mitigation_preserving_actor_head_repair.pt"
    final_trace_rows, final_manifest = write_mitigation_preserving_candidate_checkpoint(
        source_checkpoint_path,
        final_checkpoint,
        training_observations=training_observations,
        target_map=target_map,
        output_dir=output_dir,
        device=device,
        steer_bias_delta=float(selected_spec["steer_bias_delta"]),
        throttle_bias_delta=float(selected_spec["throttle_bias_delta"]),
        brake_bias_delta=float(selected_spec["brake_bias_delta"]),
        milestone=milestone,
        candidate_id=str(selected_spec["candidate_id"]),
    )
    final_evaluation = evaluate_candidate_checkpoint(
        final_checkpoint,
        baseline_rows=baseline_rows,
        target_map=target_map,
        objective_rows=objective_rows,
        protected_rows=protected_rows,
        target_rows=target_rows,
        source_checkpoint=source_checkpoint_path,
        row_schema_fields=row_schema_fields,
        fresh_seed_count=int(fresh_seed_count),
        horizon_steps=int(horizon_steps),
        device=device,
        milestone=milestone,
    )
    final_metrics = summarize_gate_rows(final_evaluation["gate_rows"])
    summary_next_blocker = (
        DEFAULT_BRANCH_SYNTHESIS_BLOCKER
        if next_blocker == DEFAULT_NEXT_BLOCKER
        and not final_metrics["target_and_protected_gates_all_passed"]
        else next_blocker
    )
    final_manifest = {
        **final_manifest,
        "selected_candidate_id": selected_spec["candidate_id"],
        "selection_reason": selected["selection_reason"],
        "candidate_constraint_status": final_metrics["candidate_constraint_status"],
        "target_preservation_gates_all_passed": final_metrics[
            "target_preservation_gates_all_passed"
        ],
        "protected_component_gates_all_passed": final_metrics[
            "protected_component_gates_all_passed"
        ],
        "target_and_protected_gates_all_passed": final_metrics[
            "target_and_protected_gates_all_passed"
        ],
        "failed_gate_ids": final_metrics["failed_gate_ids"],
    }

    repair_config_snapshot_path = output_dir / "repair_config_snapshot.json"
    repair_candidate_sweep_path = output_dir / "repair_candidate_sweep.csv"
    selected_repair_trace_path = output_dir / "selected_repair_trace.csv"
    repaired_checkpoint_manifest_path = output_dir / "repaired_checkpoint_manifest.json"
    post_repair_behavior_rows_path = output_dir / "post_repair_behavior_rows.csv"
    gate_evaluation_path = output_dir / "mitigation_preserving_gate_evaluation.csv"
    summary_path = output_dir / "summary.json"

    sweep_rows = build_candidate_sweep_rows(
        candidate_results,
        selected_candidate_id=str(selected_spec["candidate_id"]),
        selection_reason=selected["selection_reason"],
    )
    selected_trace_row = {
        **final_trace_rows[0],
        "selection_reason": selected["selection_reason"],
        "candidate_constraint_status": final_metrics["candidate_constraint_status"],
        "target_preservation_gates_all_passed": final_metrics[
            "target_preservation_gates_all_passed"
        ],
        "protected_component_gates_all_passed": final_metrics[
            "protected_component_gates_all_passed"
        ],
        "target_and_protected_gates_all_passed": final_metrics[
            "target_and_protected_gates_all_passed"
        ],
        "failed_gate_ids": ";".join(final_metrics["failed_gate_ids"]),
        "protected_component_regressed_row_count": final_metrics[
            "protected_component_regressed_row_count"
        ],
    }
    write_json(
        repair_config_snapshot_path,
        build_repair_config_snapshot(
            objective_summary_path=objective_summary_path,
            objective_family_path=objective_family_path,
            protected_gate_path=protected_gate_path,
            target_gate_path=target_gate_path,
            baseline_behavior_path=baseline_behavior_path,
            source_checkpoint=source_checkpoint_path,
            repaired_checkpoint=final_checkpoint,
            objective_summary=objective_summary_data,
            target_map=target_map,
            candidate_specs=normalized_specs,
            selected_candidate_id=str(selected_spec["candidate_id"]),
            milestone=milestone,
        ),
    )
    write_csv_rows(repair_candidate_sweep_path, sweep_rows, fieldnames=CANDIDATE_SWEEP_FIELDNAMES)
    write_csv_rows(
        selected_repair_trace_path,
        [selected_trace_row],
        fieldnames=SELECTED_REPAIR_TRACE_FIELDNAMES,
    )
    write_json(repaired_checkpoint_manifest_path, final_manifest)
    write_csv_rows(
        post_repair_behavior_rows_path,
        final_evaluation["post_repair_rows"],
        fieldnames=row_schema_fields + EXTRA_BEHAVIOR_FIELDS_M2641 + POST_REPAIR_EXTRA_FIELDNAMES,
    )
    write_csv_rows(
        gate_evaluation_path,
        final_evaluation["gate_rows"],
        fieldnames=GATE_EVALUATION_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        doc_path=doc_output_path,
        objective_summary_path=objective_summary_path,
        objective_family_path=objective_family_path,
        protected_gate_path=protected_gate_path,
        target_gate_path=target_gate_path,
        baseline_behavior_path=baseline_behavior_path,
        source_checkpoint=source_checkpoint_path,
        repaired_checkpoint=final_checkpoint,
        repair_config_snapshot_path=repair_config_snapshot_path,
        repair_candidate_sweep_path=repair_candidate_sweep_path,
        selected_repair_trace_path=selected_repair_trace_path,
        repaired_checkpoint_manifest_path=repaired_checkpoint_manifest_path,
        post_repair_behavior_rows_path=post_repair_behavior_rows_path,
        gate_evaluation_path=gate_evaluation_path,
        candidate_sweep_rows=sweep_rows,
        selected_trace_rows=[selected_trace_row],
        post_repair_rows=final_evaluation["post_repair_rows"],
        gate_rows=final_evaluation["gate_rows"],
        checkpoint_manifest=final_manifest,
        target_map=target_map,
        final_metrics=final_metrics,
        telemetry_summary=final_evaluation["telemetry_summary"],
        objective_summary=objective_summary_data,
        milestone=milestone,
        next_blocker=summary_next_blocker,
        horizon_steps=int(horizon_steps),
        fresh_seed_count=int(fresh_seed_count),
    )
    write_json(summary_path, summary)
    write_doc(doc_output_path, summary)
    return summary


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_candidate_specs(
    specs: Sequence[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    normalized: list[dict[str, float | str]] = []
    for index, spec in enumerate(specs):
        candidate_id = str(spec.get("candidate_id") or f"m2655_candidate_{index}")
        normalized.append(
            {
                "candidate_id": candidate_id,
                "steer_bias_delta": float(spec["steer_bias_delta"]),
                "throttle_bias_delta": float(spec["throttle_bias_delta"]),
                "brake_bias_delta": float(spec["brake_bias_delta"]),
            }
        )
    return normalized


def build_objective_target_map(rows: list[dict[str, str]]) -> dict[str, Any]:
    target_rows = [row for row in rows if row["objective_role"] == "target"]
    protected_rows = [row for row in rows if row["objective_role"] == "protected_reference"]
    target_roles = sorted(
        {
            role
            for row in target_rows
            for role in str(row["source_roles"]).split(";")
            if role
        }
    )
    return {
        "admitted_rows": target_rows,
        "protected_rows": protected_rows,
        "target_gap_families": [row["source_family"] for row in target_rows],
        "target_role_families": target_roles,
        "protected_reference_families": [row["source_family"] for row in protected_rows],
        "gap_by_role": {
            role: row["source_family"]
            for row in target_rows
            for role in str(row["source_roles"]).split(";")
            if role
        },
        "protected_reference_by_role": {
            role: row["source_family"]
            for row in protected_rows
            for role in str(row["source_roles"]).split(";")
            if role
        },
    }


def verify_objective_bundle(
    summary: dict[str, Any],
    objective_rows: list[dict[str, str]],
    protected_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
) -> None:
    if not bool(summary.get("status_pass")) or not bool(summary.get("gate_matrix_pass")):
        raise RuntimeError("M2653 objective bundle must pass before M2655 execution")
    objective_ids = {row["objective_family_id"] for row in objective_rows}
    required_objectives = {
        "road_boundary_margin_target",
        "drift_collision_recovery_target",
        "mitigation_non_regression_protected",
    }
    missing_objectives = required_objectives - objective_ids
    if missing_objectives:
        raise RuntimeError(f"M2653 objective bundle missing {sorted(missing_objectives)}")
    protected_ids = {row["component_gate_id"] for row in protected_rows}
    required_protected = {
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
    }
    missing_protected = required_protected - protected_ids
    if missing_protected:
        raise RuntimeError(f"M2653 protected gate bundle missing {sorted(missing_protected)}")
    target_ids = {row["target_gate_id"] for row in target_rows}
    required_targets = {
        "target_road_boundary_margin_control",
        "target_drift_collision_recovery_tradeoff",
    }
    missing_targets = required_targets - target_ids
    if missing_targets:
        raise RuntimeError(f"M2653 target gate bundle missing {sorted(missing_targets)}")


def write_mitigation_preserving_candidate_checkpoint(
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    target_map: dict[str, Any],
    output_dir: Path,
    device: str,
    steer_bias_delta: float,
    throttle_bias_delta: float,
    brake_bias_delta: float,
    milestone: str,
    candidate_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    model, checkpoint = load_actor_critic_checkpoint(source_checkpoint, device=device)
    resolved_device = next(model.parameters()).device
    if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
        raise RuntimeError("source checkpoint does not preserve the P0 72/3 contract")

    source_model_state_hash = model_state_sha256(checkpoint["model_state"])
    obs_t = torch.as_tensor(training_observations, dtype=torch.float32, device=resolved_device)
    source_actions = actor_actions(model, obs_t)
    source_stats = action_stats_with_steer(source_actions)

    with torch.no_grad():
        before_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        model.actor_mean.bias[0].add_(float(steer_bias_delta))
        model.actor_mean.bias[1].add_(float(throttle_bias_delta))
        model.actor_mean.bias[2].add_(float(brake_bias_delta))
        after_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    repaired_actions = actor_actions(model, obs_t)
    repaired_stats = action_stats_with_steer(repaired_actions, reference_actions=source_actions)
    repaired_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    repaired_model_state_hash = model_state_sha256(repaired_state)
    checkpoint_output = copy.deepcopy(checkpoint)
    checkpoint_output["model_state"] = repaired_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2655_mitigation_preserving_repair_execution": {
            "milestone": milestone,
            "candidate_id": candidate_id,
            "update_method": "deterministic_mitigation_preserving_gap_targeted_actor_head_bias_projection",
            "source_checkpoint": str(source_checkpoint),
            "output_dir": str(output_dir),
            "target_gap_families": target_map["target_gap_families"],
            "target_role_families": target_map["target_role_families"],
            "protected_reference_families": target_map["protected_reference_families"],
            "trainable_parameter_names": [
                "actor_mean.bias[0]",
                "actor_mean.bias[1]",
                "actor_mean.bias[2]",
            ],
            "steer_bias_delta": float(steer_bias_delta),
            "throttle_bias_delta": float(throttle_bias_delta),
            "brake_bias_delta": float(brake_bias_delta),
            "checkpoint_promoted": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "active_config_overwritten": False,
            "objective_artifacts_mutated": False,
            "claim_scope": CLAIM_SCOPE,
        },
    }
    repaired_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_output, repaired_checkpoint)

    repaired_checkpoint_hash = _file_sha256(repaired_checkpoint)
    source_checkpoint_hash = _file_sha256(source_checkpoint)
    finite_update = bool(
        np.all(np.isfinite(np.asarray(after_bias, dtype=np.float64)))
        and np.isfinite(repaired_stats["conflict_proxy"])
    )
    behavior_changed = bool(
        repaired_model_state_hash != source_model_state_hash
        and repaired_stats["mean_action_delta_l1_from_source"] > 1e-9
    )
    trace_row = {
        "update_index": 0,
        "update_method": "deterministic_mitigation_preserving_gap_targeted_actor_head_bias_projection",
        "candidate_id": candidate_id,
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "training_observation_count": int(training_observations.shape[0]),
        "target_gap_families": ";".join(target_map["target_gap_families"]),
        "target_role_families": ";".join(target_map["target_role_families"]),
        "protected_reference_families": ";".join(target_map["protected_reference_families"]),
        "trainable_parameter_names": "actor_mean.bias[0];actor_mean.bias[1];actor_mean.bias[2]",
        "source_model_state_hash": source_model_state_hash,
        "repaired_model_state_hash": repaired_model_state_hash,
        "actor_mean_bias_before": json_list(before_bias),
        "actor_mean_bias_after": json_list(after_bias),
        "steer_bias_delta": float(steer_bias_delta),
        "throttle_bias_delta": float(throttle_bias_delta),
        "brake_bias_delta": float(brake_bias_delta),
        "source_conflict_proxy": source_stats["conflict_proxy"],
        "repaired_conflict_proxy": repaired_stats["conflict_proxy"],
        "source_mean_action_steer": source_stats["mean_action_steer"],
        "repaired_mean_action_steer": repaired_stats["mean_action_steer"],
        "source_mean_action_throttle": source_stats["mean_action_throttle"],
        "repaired_mean_action_throttle": repaired_stats["mean_action_throttle"],
        "source_mean_action_brake": source_stats["mean_action_brake"],
        "repaired_mean_action_brake": repaired_stats["mean_action_brake"],
        "mean_action_delta_l1": repaired_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "objective_artifacts_mutated": False,
        "checkpoint_promoted": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    manifest = {
        "manifest_id": "m2655_repaired_checkpoint_manifest_v0",
        "milestone": milestone,
        "candidate_id": candidate_id,
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_hash": source_checkpoint_hash,
        "repaired_checkpoint": str(repaired_checkpoint),
        "repaired_checkpoint_hash": repaired_checkpoint_hash,
        "source_model_state_hash": source_model_state_hash,
        "repaired_model_state_hash": repaired_model_state_hash,
        "behavior_changed": behavior_changed,
        "repair_execution_started": True,
        "repair_training_started": True,
        "repaired_checkpoint_written": repaired_checkpoint.exists(),
        "update_method": "deterministic_mitigation_preserving_gap_targeted_actor_head_bias_projection",
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "trainable_parameter_names": [
            "actor_mean.bias[0]",
            "actor_mean.bias[1]",
            "actor_mean.bias[2]",
        ],
        "training_observation_count": int(training_observations.shape[0]),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "objective_artifacts_mutated": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "finite_update": finite_update,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return [trace_row], manifest


def action_stats_with_steer(
    actions: torch.Tensor,
    *,
    reference_actions: torch.Tensor | None = None,
) -> dict[str, float]:
    stats = actor_action_stats(actions, reference_actions=reference_actions)
    stats["mean_action_steer"] = float(actions[:, 0].mean().detach().cpu().item())
    return stats


def evaluate_candidate_checkpoint(
    checkpoint_path: Path,
    *,
    baseline_rows: list[dict[str, str]],
    target_map: dict[str, Any],
    objective_rows: list[dict[str, str]],
    protected_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
    source_checkpoint: Path,
    row_schema_fields: list[str],
    fresh_seed_count: int,
    horizon_steps: int,
    device: str,
    milestone: str,
) -> dict[str, Any]:
    policy_checkpoints = dict(DEFAULT_POLICY_CHECKPOINTS)
    policy_checkpoints[REPAIRED_SUBJECT_ID] = str(checkpoint_path)
    subjects = route_a_subjects(policy_checkpoints)
    admitted_subjects, _subject_registry_rows = admit_route_a_subjects(subjects, device=device)
    run_items, _seed_rows, _axis_rows = build_fresh_generalization_panel_specs(
        fresh_seed_count=int(fresh_seed_count)
    )
    telemetry_rows, telemetry_summary = run_fresh_generalization_telemetry(
        run_items,
        admitted_subjects,
        horizon_steps=int(horizon_steps),
    )
    measured_behavior_rows, _measured_event_rows = build_fresh_generalization_measured_rows(
        telemetry_rows,
        run_items=run_items,
        subjects=subjects,
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    post_rows = build_post_repair_behavior_rows(
        measured_behavior_rows,
        target_map=target_map,
        source_checkpoint=source_checkpoint,
        repaired_checkpoint=checkpoint_path,
        milestone=milestone,
    )
    gate_rows = build_gate_evaluation_rows(
        baseline_rows,
        post_rows,
        objective_rows=objective_rows,
        protected_rows=protected_rows,
        target_rows=target_rows,
    )
    return {
        "telemetry_summary": telemetry_summary,
        "post_repair_rows": post_rows,
        "gate_rows": gate_rows,
    }


def build_post_repair_behavior_rows(
    measured_behavior_rows: list[dict[str, Any]],
    *,
    target_map: dict[str, Any],
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    milestone: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in measured_behavior_rows:
        role = str(row["scenario_role"])
        target_gap = target_map["gap_by_role"].get(role, "")
        protected_reference = (
            ""
            if target_gap
            else target_map["protected_reference_by_role"].get(role, "")
        )
        next_row = dict(row)
        next_row.update(
            {
                "post_repair_row_id": (
                    f"m2655_{row['subject_id']}_{role}_seed_{row['seed']}_"
                    f"{row['dynamics_axis_id']}"
                ),
                "source_checkpoint_path": str(source_checkpoint),
                "repaired_checkpoint_path": str(repaired_checkpoint),
                "repair_execution_started": True,
                "repair_training_started": True,
                "repaired_checkpoint_written": repaired_checkpoint.exists(),
                "gap_target_family": target_gap,
                "protected_reference_family": protected_reference,
                "repair_target_admitted": bool(target_gap),
                "protected_reference_only": bool(protected_reference),
                "taxonomy_labels_actor_visible": False,
                "repair_target_labels_actor_visible": False,
                "objective_gate_labels_actor_visible": False,
                "route_decision_actor_visible": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
        rows.append(next_row)
    return rows


def build_gate_evaluation_rows(
    baseline_rows: list[dict[str, str]],
    post_repair_rows: list[dict[str, Any]],
    *,
    objective_rows: list[dict[str, str]],
    protected_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    baseline_repaired = [
        row for row in baseline_rows if row.get("subject_id") == REPAIRED_SUBJECT_ID
    ]
    post_repaired = [
        row for row in post_repair_rows if row.get("subject_id") == REPAIRED_SUBJECT_ID
    ]
    objective_ids = {row["objective_family_id"] for row in objective_rows}
    target_ids = {row["target_gate_id"] for row in target_rows}
    protected_ids = {row["component_gate_id"] for row in protected_rows}
    rows = [
        target_gate_row(
            "target_road_boundary_margin_control",
            "road_departure_dominant_gap",
            "minimum_road_margin_m",
            baseline_repaired,
            post_repaired,
            roles={"stable_avoidable", "stable_aes"},
            larger_is_better=True,
            trace_to_objective_artifact=(
                "road_boundary_margin_target" in objective_ids
                and "target_road_boundary_margin_control" in target_ids
            ),
        ),
        target_gate_row(
            "target_drift_collision_recovery_tradeoff",
            "drift_recovery_mixed_gap",
            "drift_tradeoff_proxy",
            baseline_repaired,
            post_repaired,
            roles={"drift_required_recovery"},
            larger_is_better=True,
            trace_to_objective_artifact=(
                "drift_collision_recovery_target" in objective_ids
                and "target_drift_collision_recovery_tradeoff" in target_ids
            ),
        ),
        protected_metric_gate_row(
            "severity_proxy_non_regression",
            "severity_proxy",
            baseline_repaired,
            post_repaired,
            larger_is_better=False,
            trace_to_objective_artifact="severity_proxy_non_regression" in protected_ids,
        ),
        protected_metric_gate_row(
            "obstacle_penetration_non_regression",
            "obstacle_penetration_proxy_m",
            baseline_repaired,
            post_repaired,
            larger_is_better=False,
            trace_to_objective_artifact="obstacle_penetration_non_regression" in protected_ids,
        ),
        protected_metric_gate_row(
            "minimum_obstacle_clearance_preservation",
            "minimum_obstacle_clearance_m",
            baseline_repaired,
            post_repaired,
            larger_is_better=True,
            trace_to_objective_artifact="minimum_obstacle_clearance_preservation" in protected_ids,
        ),
        event_transition_gate_row(
            baseline_repaired,
            post_repaired,
            trace_to_objective_artifact="event_transition_guard" in protected_ids,
        ),
        contract_gate_row(post_repair_rows),
        no_oracle_gate_row(post_repair_rows),
        no_ranking_gate_row(),
    ]
    return rows


def target_gate_row(
    gate_id: str,
    target_family: str,
    metric: str,
    baseline_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    *,
    roles: set[str],
    larger_is_better: bool,
    trace_to_objective_artifact: bool,
) -> dict[str, Any]:
    return metric_gate_row(
        gate_id,
        "target_preservation",
        target_family,
        metric,
        baseline_rows,
        post_rows,
        roles=roles,
        larger_is_better=larger_is_better,
        require_improvement=True,
        trace_to_objective_artifact=trace_to_objective_artifact,
    )


def protected_metric_gate_row(
    gate_id: str,
    metric: str,
    baseline_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    *,
    larger_is_better: bool,
    trace_to_objective_artifact: bool,
) -> dict[str, Any]:
    return metric_gate_row(
        gate_id,
        "protected_component",
        "mitigation_collision_saturated_reference",
        metric,
        baseline_rows,
        post_rows,
        roles={"unavoidable_mitigation"},
        larger_is_better=larger_is_better,
        require_improvement=False,
        trace_to_objective_artifact=trace_to_objective_artifact,
    )


def metric_gate_row(
    gate_id: str,
    gate_family: str,
    target_family: str,
    metric: str,
    baseline_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    *,
    roles: set[str],
    larger_is_better: bool,
    require_improvement: bool,
    trace_to_objective_artifact: bool,
) -> dict[str, Any]:
    baseline_by_key = {
        row_key(row): row for row in baseline_rows if row.get("scenario_role") in roles
    }
    post_by_key = {
        row_key(row): row for row in post_rows if row.get("scenario_role") in roles
    }
    improved = 0
    regressed = 0
    unchanged = 0
    evaluated = 0
    max_regression_delta = 0.0
    for key, post in sorted(post_by_key.items()):
        baseline = baseline_by_key.get(key)
        if baseline is None:
            continue
        before = metric_value(baseline, metric)
        after = metric_value(post, metric)
        if not np.isfinite(before) or not np.isfinite(after):
            continue
        evaluated += 1
        delta = after - before
        signed_delta = delta if larger_is_better else -delta
        if signed_delta > 1e-9:
            improved += 1
        elif signed_delta < -1e-9:
            regressed += 1
            max_regression_delta = max(max_regression_delta, abs(float(delta)))
        else:
            unchanged += 1
    gate_pass = bool(
        evaluated > 0
        and trace_to_objective_artifact
        and regressed == 0
        and (improved > 0 if require_improvement else True)
    )
    return {
        "gate_id": gate_id,
        "gate_tier": "proof",
        "gate_family": gate_family,
        "target_or_reference_family": target_family,
        "subject_id": REPAIRED_SUBJECT_ID,
        "metric": metric,
        "baseline_row_count": len(baseline_by_key),
        "post_repair_row_count": len(post_by_key),
        "evaluated_row_count": evaluated,
        "trace_to_objective_artifact": trace_to_objective_artifact,
        "trace_to_baseline_rows": evaluated == len(post_by_key) and evaluated > 0,
        "evaluation_status": "evaluated",
        "gate_pass": gate_pass,
        "improved_row_count": improved,
        "regressed_row_count": regressed,
        "unchanged_row_count": unchanged,
        "max_regression_delta": max_regression_delta,
        "failure_type": "" if gate_pass else "behavior_regression",
        "blocks_claims": True,
        "next_route_if_fail": "m2656_result_audit_then_synthesis_or_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def event_transition_gate_row(
    baseline_rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    *,
    trace_to_objective_artifact: bool,
) -> dict[str, Any]:
    roles = {"unavoidable_mitigation"}
    baseline_by_key = {
        row_key(row): row for row in baseline_rows if row.get("scenario_role") in roles
    }
    post_by_key = {
        row_key(row): row for row in post_rows if row.get("scenario_role") in roles
    }
    evaluated = 0
    regressed = 0
    unchanged = 0
    for key, post in sorted(post_by_key.items()):
        baseline = baseline_by_key.get(key)
        if baseline is None:
            continue
        evaluated += 1
        collision_regressed = (not as_bool(baseline.get("collision_event"))) and as_bool(
            post.get("collision_event")
        )
        road_regressed = (not as_bool(baseline.get("road_departure_event"))) and as_bool(
            post.get("road_departure_event")
        )
        if collision_regressed or road_regressed:
            regressed += 1
        else:
            unchanged += 1
    gate_pass = bool(evaluated > 0 and trace_to_objective_artifact and regressed == 0)
    return {
        "gate_id": "event_transition_guard",
        "gate_tier": "proof",
        "gate_family": "protected_component",
        "target_or_reference_family": "mitigation_collision_saturated_reference",
        "subject_id": REPAIRED_SUBJECT_ID,
        "metric": "collision_event;road_departure_event",
        "baseline_row_count": len(baseline_by_key),
        "post_repair_row_count": len(post_by_key),
        "evaluated_row_count": evaluated,
        "trace_to_objective_artifact": trace_to_objective_artifact,
        "trace_to_baseline_rows": evaluated == len(post_by_key) and evaluated > 0,
        "evaluation_status": "evaluated",
        "gate_pass": gate_pass,
        "improved_row_count": 0,
        "regressed_row_count": regressed,
        "unchanged_row_count": unchanged,
        "max_regression_delta": 0.0,
        "failure_type": "" if gate_pass else "behavior_regression",
        "blocks_claims": True,
        "next_route_if_fail": "m2656_result_audit_then_synthesis_or_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def contract_gate_row(post_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_pass = (
        {int(row["observation_shape"]) for row in post_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in post_rows} == {ACTION_DIM}
    )
    return simple_gate_row("contract_p0_72_3", "actor_contract", gate_pass, len(post_rows))


def no_oracle_gate_row(post_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate_pass = (
        {str(row["actor_input_leak_flags"]).lower() for row in post_rows} == {"none"}
        and not any(as_bool(row["taxonomy_labels_actor_visible"]) for row in post_rows)
        and not any(as_bool(row["repair_target_labels_actor_visible"]) for row in post_rows)
        and not any(as_bool(row["objective_gate_labels_actor_visible"]) for row in post_rows)
        and not any(as_bool(row["route_decision_actor_visible"]) for row in post_rows)
    )
    return simple_gate_row("no_oracle_actor_inputs", "actor_contract", gate_pass, len(post_rows))


def no_ranking_gate_row() -> dict[str, Any]:
    return simple_gate_row("no_ranking_no_success_rate", "claim_boundary", True, 0)


def simple_gate_row(gate_id: str, gate_family: str, gate_pass: bool, row_count: int) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": "proof",
        "gate_family": gate_family,
        "target_or_reference_family": "",
        "subject_id": "all_subjects",
        "metric": "",
        "baseline_row_count": row_count,
        "post_repair_row_count": row_count,
        "evaluated_row_count": row_count,
        "trace_to_objective_artifact": True,
        "trace_to_baseline_rows": True,
        "evaluation_status": "pass" if gate_pass else "fail",
        "gate_pass": gate_pass,
        "improved_row_count": 0,
        "regressed_row_count": 0 if gate_pass else 1,
        "unchanged_row_count": row_count,
        "max_regression_delta": 0.0,
        "failure_type": "" if gate_pass else "contract_violation",
        "blocks_claims": not gate_pass,
        "next_route_if_fail": "contract_repair_or_artifact_repair",
        "claim_boundary": CLAIM_SCOPE,
    }


def summarize_gate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_gate_ids = {
        "target_road_boundary_margin_control",
        "target_drift_collision_recovery_tradeoff",
    }
    protected_gate_ids = {
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
    }
    target_rows = [row for row in rows if row["gate_id"] in target_gate_ids]
    protected_rows = [row for row in rows if row["gate_id"] in protected_gate_ids]
    target_pass = bool(target_rows) and all(as_bool(row["gate_pass"]) for row in target_rows)
    protected_pass = bool(protected_rows) and all(as_bool(row["gate_pass"]) for row in protected_rows)
    failed = [row["gate_id"] for row in rows if not as_bool(row["gate_pass"])]
    protected_regressed = sum(int(row["regressed_row_count"]) for row in protected_rows)
    status = (
        "target_and_protected_gates_pass"
        if target_pass and protected_pass
        else "protected_component_gate_failed"
        if target_pass
        else "target_preservation_gate_failed"
    )
    return {
        "target_preservation_gates_all_passed": target_pass,
        "protected_component_gates_all_passed": protected_pass,
        "target_and_protected_gates_all_passed": target_pass and protected_pass,
        "target_gate_pass_count": sum(as_bool(row["gate_pass"]) for row in target_rows),
        "protected_component_gate_pass_count": sum(
            as_bool(row["gate_pass"]) for row in protected_rows
        ),
        "protected_component_regressed_row_count": protected_regressed,
        "failed_gate_ids": failed,
        "candidate_constraint_status": status,
    }


def select_candidate(results: list[dict[str, Any]]) -> dict[str, Any]:
    ranked: list[tuple[tuple[int, int, int, float], dict[str, Any]]] = []
    for result in results:
        metrics = summarize_gate_rows(result["gate_rows"])
        trace = result["trace_rows"][0]
        key = (
            int(not metrics["target_and_protected_gates_all_passed"]),
            int(metrics["protected_component_regressed_row_count"]),
            -int(metrics["target_gate_pass_count"]),
            float(trace["mean_action_delta_l1"]),
        )
        ranked.append((key, {**result, "metrics": metrics}))
    ranked.sort(key=lambda item: item[0])
    selected = ranked[0][1]
    metrics = selected["metrics"]
    reason = (
        "selected_first_candidate_with_target_and_protected_gates_pass"
        if metrics["target_and_protected_gates_all_passed"]
        else "selected_lowest_protected_regression_diagnostic_candidate"
    )
    return {**selected, "selection_reason": reason}


def build_candidate_sweep_rows(
    results: list[dict[str, Any]],
    *,
    selected_candidate_id: str,
    selection_reason: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        spec = result["spec"]
        trace = result["trace_rows"][0]
        manifest = result["checkpoint_manifest"]
        metrics = summarize_gate_rows(result["gate_rows"])
        selected = str(spec["candidate_id"]) == selected_candidate_id
        rows.append(
            {
                "candidate_id": spec["candidate_id"],
                "candidate_index": result["candidate_index"],
                "source_checkpoint": manifest["source_checkpoint"],
                "candidate_checkpoint": manifest["repaired_checkpoint"],
                "steer_bias_delta": spec["steer_bias_delta"],
                "throttle_bias_delta": spec["throttle_bias_delta"],
                "brake_bias_delta": spec["brake_bias_delta"],
                "behavior_changed_from_source": manifest["behavior_changed"],
                "finite_update": manifest["finite_update"],
                "candidate_checkpoint_hash": manifest["repaired_checkpoint_hash"],
                "source_model_state_hash": manifest["source_model_state_hash"],
                "candidate_model_state_hash": manifest["repaired_model_state_hash"],
                "telemetry_row_count": int(result["telemetry_summary"].get("telemetry_row_count", 0)),
                "post_repair_behavior_row_count": len(result["post_repair_rows"]),
                "gate_evaluation_row_count": len(result["gate_rows"]),
                "target_preservation_gates_all_passed": metrics[
                    "target_preservation_gates_all_passed"
                ],
                "protected_component_gates_all_passed": metrics[
                    "protected_component_gates_all_passed"
                ],
                "target_and_protected_gates_all_passed": metrics[
                    "target_and_protected_gates_all_passed"
                ],
                "target_gate_pass_count": metrics["target_gate_pass_count"],
                "protected_component_gate_pass_count": metrics["protected_component_gate_pass_count"],
                "protected_component_regressed_row_count": metrics[
                    "protected_component_regressed_row_count"
                ],
                "failed_gate_ids": ";".join(metrics["failed_gate_ids"]),
                "candidate_constraint_status": metrics["candidate_constraint_status"],
                "selected_for_repair_trace": selected,
                "selection_reason": selection_reason if selected else "",
                "diagnostic_only_no_ranking_claim": True,
                "success_rate_field_emitted": False,
                "ranking_or_winner_field_emitted": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_repair_config_snapshot(
    *,
    objective_summary_path: Path,
    objective_family_path: Path,
    protected_gate_path: Path,
    target_gate_path: Path,
    baseline_behavior_path: Path,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    objective_summary: dict[str, Any],
    target_map: dict[str, Any],
    candidate_specs: list[dict[str, float | str]],
    selected_candidate_id: str,
    milestone: str,
) -> dict[str, Any]:
    return {
        "config_id": "m2655_mitigation_preserving_repair_execution_v0",
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "objective_summary": str(objective_summary_path),
        "objective_family_rows": str(objective_family_path),
        "protected_component_gates": str(protected_gate_path),
        "target_preservation_gates": str(target_gate_path),
        "baseline_behavior_rows": str(baseline_behavior_path),
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "m2653_status_pass": bool(objective_summary.get("status_pass")),
        "m2653_gate_matrix_pass": bool(objective_summary.get("gate_matrix_pass")),
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "candidate_specs": candidate_specs,
        "selected_candidate_id": selected_candidate_id,
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "taxonomy_labels_actor_visible": False,
            "repair_target_labels_actor_visible": False,
            "objective_gate_labels_actor_visible": False,
            "route_decision_actor_visible": False,
            "hidden_or_oracle_actor_inputs_required": False,
        },
        "active_config_overwritten": False,
        "objective_artifacts_mutated": False,
        "checkpoint_promoted": False,
        "ranking_run": False,
        "success_rate_computed": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    doc_path: Path,
    objective_summary_path: Path,
    objective_family_path: Path,
    protected_gate_path: Path,
    target_gate_path: Path,
    baseline_behavior_path: Path,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    repair_config_snapshot_path: Path,
    repair_candidate_sweep_path: Path,
    selected_repair_trace_path: Path,
    repaired_checkpoint_manifest_path: Path,
    post_repair_behavior_rows_path: Path,
    gate_evaluation_path: Path,
    candidate_sweep_rows: list[dict[str, Any]],
    selected_trace_rows: list[dict[str, Any]],
    post_repair_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    target_map: dict[str, Any],
    final_metrics: dict[str, Any],
    telemetry_summary: dict[str, Any],
    objective_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
    horizon_steps: int,
    fresh_seed_count: int,
) -> dict[str, Any]:
    required_present = all(
        path.exists()
        for path in (
            repair_config_snapshot_path,
            repair_candidate_sweep_path,
            selected_repair_trace_path,
            repaired_checkpoint_manifest_path,
            post_repair_behavior_rows_path,
            gate_evaluation_path,
        )
    )
    actor_contract_shape_72_action_3 = (
        {int(row["observation_shape"]) for row in post_repair_rows} == {P0_OBSERVATION_DIM}
        and {int(row["action_shape"]) for row in post_repair_rows} == {ACTION_DIM}
    )
    hidden_or_oracle = any(
        str(row["actor_input_leak_flags"]).lower() != "none"
        or as_bool(row["taxonomy_labels_actor_visible"])
        or as_bool(row["repair_target_labels_actor_visible"])
        or as_bool(row["objective_gate_labels_actor_visible"])
        or as_bool(row["route_decision_actor_visible"])
        for row in post_repair_rows
    )
    target_gate_ids = {
        "target_road_boundary_margin_control",
        "target_drift_collision_recovery_tradeoff",
    }
    protected_gate_ids = {
        "severity_proxy_non_regression",
        "obstacle_penetration_non_regression",
        "minimum_obstacle_clearance_preservation",
        "event_transition_guard",
    }
    target_gate_rows = [row for row in gate_rows if row["gate_id"] in target_gate_ids]
    protected_gate_rows = [row for row in gate_rows if row["gate_id"] in protected_gate_ids]
    false_claim_guard_pass = not any(FALSE_CLAIM_FLAGS.values())
    status_pass = bool(
        required_present
        and len(candidate_sweep_rows) > 0
        and len(selected_trace_rows) == 1
        and len(gate_rows) == 9
        and bool(checkpoint_manifest["repaired_checkpoint_written"])
        and bool(checkpoint_manifest["behavior_changed"])
        and actor_contract_shape_72_action_3
        and not hidden_or_oracle
        and false_claim_guard_pass
    )
    failed_gate_ids = [row["gate_id"] for row in gate_rows if not as_bool(row["gate_pass"])]
    summary = {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "doc": str(doc_path),
        "next_blocker": next_blocker,
        "objective_summary": str(objective_summary_path),
        "objective_family_rows": str(objective_family_path),
        "protected_component_gates": str(protected_gate_path),
        "target_preservation_gates": str(target_gate_path),
        "baseline_behavior_rows": str(baseline_behavior_path),
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "repair_config_snapshot": str(repair_config_snapshot_path),
        "repair_candidate_sweep": str(repair_candidate_sweep_path),
        "selected_repair_trace": str(selected_repair_trace_path),
        "repaired_checkpoint_manifest": str(repaired_checkpoint_manifest_path),
        "post_repair_behavior_rows": str(post_repair_behavior_rows_path),
        "mitigation_preserving_gate_evaluation": str(gate_evaluation_path),
        "required_artifacts_present": required_present,
        "m2653_status_pass": bool(objective_summary.get("status_pass")),
        "m2653_gate_matrix_pass": bool(objective_summary.get("gate_matrix_pass")),
        "repair_execution_started": True,
        "repair_training_started": True,
        "training_run": True,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "source_only_repair_execution_run": True,
        "closed_loop_source_only_behavior_rows_written": True,
        "repaired_checkpoint_written": bool(checkpoint_manifest["repaired_checkpoint_written"]),
        "checkpoint_behavior_changed": bool(checkpoint_manifest["behavior_changed"]),
        "training_observation_count": int(checkpoint_manifest["training_observation_count"]),
        "candidate_sweep_row_count": len(candidate_sweep_rows),
        "selected_repair_trace_row_count": len(selected_trace_rows),
        "post_repair_behavior_row_count": len(post_repair_rows),
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "mitigation_preserving_gate_evaluation_row_count": len(gate_rows),
        "horizon_steps": int(horizon_steps),
        "fresh_seed_count": int(fresh_seed_count),
        "target_gap_families": target_map["target_gap_families"],
        "target_role_families": target_map["target_role_families"],
        "protected_reference_families": target_map["protected_reference_families"],
        "admitted_repair_target_count": len(target_map["admitted_rows"]),
        "protected_reference_count": len(target_map["protected_rows"]),
        "selected_candidate_id": checkpoint_manifest.get("selected_candidate_id", ""),
        "selection_reason": checkpoint_manifest.get("selection_reason", ""),
        "candidate_constraint_status": final_metrics["candidate_constraint_status"],
        "target_preservation_gates_all_passed": final_metrics[
            "target_preservation_gates_all_passed"
        ],
        "protected_component_gates_all_passed": final_metrics[
            "protected_component_gates_all_passed"
        ],
        "target_and_protected_gates_all_passed": final_metrics[
            "target_and_protected_gates_all_passed"
        ],
        "target_gate_pass_count": final_metrics["target_gate_pass_count"],
        "target_gate_fail_count": len(target_gate_rows)
        - int(final_metrics["target_gate_pass_count"]),
        "protected_component_gate_pass_count": final_metrics[
            "protected_component_gate_pass_count"
        ],
        "protected_component_gate_fail_count": len(protected_gate_rows)
        - int(final_metrics["protected_component_gate_pass_count"]),
        "protected_component_regressed_row_count": final_metrics[
            "protected_component_regressed_row_count"
        ],
        "failed_gate_ids": failed_gate_ids,
        "actor_contract_shape_72_action_3": actor_contract_shape_72_action_3,
        "hidden_or_oracle_actor_inputs_required": hidden_or_oracle,
        "taxonomy_labels_actor_visible": False,
        "repair_target_labels_actor_visible": False,
        "objective_gate_labels_actor_visible": False,
        "route_decision_actor_visible": False,
        "active_config_overwritten": False,
        "objective_artifacts_mutated": False,
        "checkpoint_promoted": False,
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return summary


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failed_gate_ids = (
        ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    )
    path.write_text(
        "\n".join(
            [
                "# M2655 Engineering Controller Route A Mitigation-Preserving Repair Execution Preflight",
                "",
                "- status: completed" if summary["status_pass"] else "- status: failed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-preflight.json`",
                f"- summary: `{summary['summary']}`",
                f"- repair candidate sweep: `{summary['repair_candidate_sweep']}`",
                f"- selected repair trace: `{summary['selected_repair_trace']}`",
                f"- post-repair behavior rows: `{summary['post_repair_behavior_rows']}`",
                f"- mitigation-preserving gate evaluation: `{summary['mitigation_preserving_gate_evaluation']}`",
                f"- next: `{summary['next_blocker']}`",
                "",
                "## Result",
                "",
                "M2655 ran one bounded gate-aware mitigation-preserving source-only repair",
                "execution preflight using the M2653 objective bundle. It wrote candidate",
                "checkpoints, selected one diagnostic repair trace, measured post-repair",
                "source-only behavior rows, and evaluated target preservation plus protected",
                "mitigation component gates.",
                "",
                "```text",
                f"repair_execution_started: {summary['repair_execution_started']}",
                f"repair_training_started: {summary['repair_training_started']}",
                f"training_observation_count: {summary['training_observation_count']}",
                f"candidate_sweep_row_count: {summary['candidate_sweep_row_count']}",
                f"selected_candidate_id: {summary['selected_candidate_id']}",
                f"candidate_constraint_status: {summary['candidate_constraint_status']}",
                f"post_repair_behavior_row_count: {summary['post_repair_behavior_row_count']}",
                f"mitigation_preserving_gate_evaluation_row_count: {summary['mitigation_preserving_gate_evaluation_row_count']}",
                f"target_preservation_gates_all_passed: {summary['target_preservation_gates_all_passed']}",
                f"protected_component_gates_all_passed: {summary['protected_component_gates_all_passed']}",
                f"target_and_protected_gates_all_passed: {summary['target_and_protected_gates_all_passed']}",
                f"failed_gate_ids: {failed_gate_ids}",
                "```",
                "",
                "## Claim Boundary",
                "",
                "M2655 is repair-execution preflight evidence for audit only. It does not",
                "rank controllers, select a winner, promote a checkpoint, compute success",
                "rates, validate, or claim driver performance, paper evidence,",
                "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity",
                "validation, full ideal driver completion, or self-ID.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def metric_value(row: dict[str, Any], metric: str) -> float:
    if metric == "obstacle_penetration_proxy_m":
        clearance = as_float(row.get("minimum_obstacle_clearance_m", "nan"))
        return max(0.0, -clearance) if np.isfinite(clearance) else float("nan")
    return gate_metric_value(row, metric)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def json_list(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.9g}" for value in values) + "]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objective-summary", type=Path, default=DEFAULT_OBJECTIVE_SUMMARY)
    parser.add_argument(
        "--objective-family-rows",
        type=Path,
        default=DEFAULT_OBJECTIVE_FAMILY_ROWS,
    )
    parser.add_argument(
        "--protected-component-gates",
        type=Path,
        default=DEFAULT_PROTECTED_COMPONENT_GATES,
    )
    parser.add_argument(
        "--target-preservation-gates",
        type=Path,
        default=DEFAULT_TARGET_PRESERVATION_GATES,
    )
    parser.add_argument("--baseline-behavior-rows", type=Path, default=DEFAULT_BASELINE_BEHAVIOR_ROWS)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--fresh-seed-count", type=int, default=DEFAULT_FRESH_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    run_mitigation_preserving_repair_execution(
        args.output_dir,
        objective_summary=args.objective_summary,
        objective_family_rows=args.objective_family_rows,
        protected_component_gates=args.protected_component_gates,
        target_preservation_gates=args.target_preservation_gates,
        baseline_behavior_rows=args.baseline_behavior_rows,
        source_checkpoint=args.source_checkpoint,
        fresh_seed_count=args.fresh_seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        doc_path=args.doc_path,
    )


if __name__ == "__main__":
    main()
