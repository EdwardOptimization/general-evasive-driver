"""Mitigation-preserving repair execution for the M2537 failure-surface branch."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    REPAIR_TRAINING_TRACE_FIELDNAMES,
    actor_action_stats,
    actor_actions,
    collect_protected_primary_reset_observations,
    model_state_sha256,
    _evaluate_post_repair_gate,
    _json_list,
)
from autodrift.engineering_controller_failure_surface_intervention_repair_smoke import (
    DEFAULT_CANDIDATE_CONFIG,
    DEFAULT_GATE_BINDINGS,
    DEFAULT_PROTECTED_ROWS,
    PROTECTED_GATE_EVALUATION_FIELDNAMES,
    REPAIR_SMOKE_FIELDNAMES,
    build_repair_smoke_rows,
    _as_bool,
    _blocks_claims,
    _bound_rows_for_group,
    _file_sha256,
    _float,
    _read_csv_rows,
    _row_int_set,
)
from autodrift.engineering_controller_source_only_fresh_seed_measured_behavior_panel import (
    DEFAULT_SEED_COUNT,
    M2514_ROW_SCHEMA,
    build_fresh_seed_measured_rows,
    build_seed_panel_specs,
    run_fresh_seed_telemetry,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_OUTPUT_DIR = Path(
    "runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/"
    "checkpoints/m2532_guarded_actor_head_repair.pt"
)
DEFAULT_M2534_LOCALIZATION = Path(
    "runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/"
    "summary.json"
)
DEFAULT_MILESTONE = (
    "m2537-engineering-controller-failure-surface-mitigation-preserving-repair-execution-preflight"
)
DEFAULT_RESULT_AUDIT_BLOCKER = (
    "m2538-engineering-controller-failure-surface-mitigation-preserving-repair-execution-result-audit"
)
DEFAULT_BRANCH_SYNTHESIS_BLOCKER = (
    "m2538-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis"
)
DEFAULT_FRESH_GENERALIZATION_BLOCKER = (
    "m2538-engineering-controller-failure-surface-fresh-generalization-design"
)
DEFAULT_RELAXATION_AMOUNTS = (0.0, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0)

CLAIM_SCOPE = "engineering-controller mitigation-preserving repair execution preflight only"
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller ranking, winner selection, success-rate verdict, "
    "validation, paper, finite-window-vs-GRU, current-sim verdict, high-fidelity "
    "validation, or self-ID claim"
)

FALSE_CLAIM_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "environment_rollout_run": False,
    "simulator_step_run": False,
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

POST_REPAIR_SMOKE_FIELDNAMES = REPAIR_SMOKE_FIELDNAMES + [
    "source_checkpoint_path",
    "repaired_checkpoint_path",
    "repair_execution_started",
    "repaired_checkpoint_written",
]

CANDIDATE_SWEEP_FIELDNAMES = [
    "candidate_id",
    "candidate_index",
    "source_checkpoint",
    "candidate_checkpoint",
    "relaxation_amount",
    "throttle_bias_delta",
    "brake_bias_delta",
    "behavior_changed_from_source",
    "finite_update",
    "candidate_checkpoint_hash",
    "source_model_state_hash",
    "candidate_model_state_hash",
    "telemetry_row_count",
    "reset_count",
    "post_repair_smoke_row_count",
    "protected_gate_evaluation_row_count",
    "protected_row_match_count",
    "all_protected_rows_matched",
    "gate_evaluation_traceable",
    "retained_road_boundary_proof_pass",
    "retained_command_conflict_proof_pass",
    "retained_proof_gates_all_passed",
    "mitigation_preserving_proof_pass",
    "protected_proof_gates_all_passed",
    "protected_proof_gate_pass_count",
    "protected_proof_gate_fail_count",
    "failed_proof_gate_ids",
    "mitigation_primary_evaluated_row_count",
    "mitigation_improved_row_count",
    "mitigation_regressed_row_count",
    "mitigation_unchanged_row_count",
    "max_mitigation_severity_delta",
    "sum_positive_mitigation_severity_delta",
    "min_mitigation_road_margin_delta_m",
    "max_command_conflict_delta",
    "eligible_for_repair_trace",
    "selected_for_repair_trace",
    "candidate_constraint_status",
    "selection_reason",
    "diagnostic_only_no_ranking_claim",
    "success_rate_field_emitted",
    "ranking_or_winner_field_emitted",
    "claim_scope",
    "forbidden_interpretation",
]

SELECTED_REPAIR_TRACE_FIELDNAMES = [
    "candidate_id",
    "selection_reason",
    "candidate_constraint_status",
    "relaxation_amount",
    "retained_road_boundary_proof_pass",
    "retained_command_conflict_proof_pass",
    "retained_proof_gates_all_passed",
    "mitigation_preserving_proof_pass",
    "protected_proof_gates_all_passed",
    "mitigation_primary_evaluated_row_count",
    "mitigation_regressed_row_count",
    "sum_positive_mitigation_severity_delta",
] + REPAIR_TRAINING_TRACE_FIELDNAMES


def run_mitigation_preserving_repair_execution(
    output_dir: Path,
    *,
    candidate_config: Path | str = DEFAULT_CANDIDATE_CONFIG,
    gate_bindings: Path | str = DEFAULT_GATE_BINDINGS,
    protected_rows: Path | str = DEFAULT_PROTECTED_ROWS,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    m2534_localization: Path | str = DEFAULT_M2534_LOCALIZATION,
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = 100,
    device: str = "cpu",
    candidate_relaxations: Sequence[float] = DEFAULT_RELAXATION_AMOUNTS,
    milestone: str = DEFAULT_MILESTONE,
) -> dict[str, Any]:
    if int(seed_count) < DEFAULT_SEED_COUNT:
        raise ValueError(f"seed_count must be at least {DEFAULT_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")
    if not candidate_relaxations:
        raise ValueError("candidate_relaxations must contain at least one amount")

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = Path(candidate_config)
    gate_binding_path = Path(gate_bindings)
    protected_rows_path = Path(protected_rows)
    source_checkpoint_path = Path(source_checkpoint)
    localization_path = Path(m2534_localization)

    candidate = read_json(candidate_path)
    candidate_hash = _file_sha256(candidate_path)
    m2534_summary = read_json(localization_path)
    gate_binding_rows = _read_csv_rows(gate_binding_path)
    protected = _read_csv_rows(protected_rows_path)
    row_schema_fields = [row["field_name"] for row in _read_csv_rows(M2514_ROW_SCHEMA)]
    run_items, _seed_panel_spec_rows = build_seed_panel_specs(seed_count=int(seed_count))
    training_observations = collect_protected_primary_reset_observations(
        protected,
        seed_count=int(seed_count),
    )

    candidate_specs = [
        {
            "candidate_id": f"m2537_relax_m2532_bias_{_amount_slug(amount)}",
            "candidate_index": index,
            "relaxation_amount": float(amount),
            "throttle_bias_delta": float(amount),
            "brake_bias_delta": -float(amount),
        }
        for index, amount in enumerate(candidate_relaxations)
    ]

    candidate_dir = output_dir / "checkpoints" / "candidates"
    candidate_results: list[dict[str, Any]] = []
    for spec in candidate_specs:
        checkpoint_path = candidate_dir / f"{spec['candidate_id']}.pt"
        trace_rows, checkpoint_manifest = write_mitigation_preserving_repaired_checkpoint(
            source_checkpoint_path,
            checkpoint_path,
            training_observations=training_observations,
            candidate=candidate,
            candidate_hash=candidate_hash,
            output_dir=output_dir,
            device=device,
            throttle_bias_delta=float(spec["throttle_bias_delta"]),
            brake_bias_delta=float(spec["brake_bias_delta"]),
            milestone=milestone,
            candidate_id=str(spec["candidate_id"]),
        )
        evaluation = evaluate_repair_checkpoint(
            checkpoint_path,
            protected=protected,
            gate_binding_rows=gate_binding_rows,
            candidate=candidate,
            candidate_hash=candidate_hash,
            source_checkpoint=source_checkpoint_path,
            row_schema_fields=row_schema_fields,
            run_items=run_items,
            horizon_steps=int(horizon_steps),
            device=device,
            milestone=milestone,
        )
        candidate_results.append(
            {
                "spec": spec,
                "trace_rows": trace_rows,
                "checkpoint_manifest": checkpoint_manifest,
                **evaluation,
            }
        )

    selected_result, selection_reason = select_repair_candidate(candidate_results)
    selected_spec = selected_result["spec"]

    final_checkpoint = output_dir / "checkpoints" / "m2537_mitigation_preserving_actor_head_repair.pt"
    final_post_repair_rows_path = output_dir / "post_repair_smoke_rows.csv"
    final_trace_rows, final_checkpoint_manifest = write_mitigation_preserving_repaired_checkpoint(
        source_checkpoint_path,
        final_checkpoint,
        training_observations=training_observations,
        candidate=candidate,
        candidate_hash=candidate_hash,
        output_dir=output_dir,
        device=device,
        throttle_bias_delta=float(selected_spec["throttle_bias_delta"]),
        brake_bias_delta=float(selected_spec["brake_bias_delta"]),
        milestone=milestone,
        candidate_id=str(selected_spec["candidate_id"]),
    )
    final_evaluation = evaluate_repair_checkpoint(
        final_checkpoint,
        protected=protected,
        gate_binding_rows=gate_binding_rows,
        candidate=candidate,
        candidate_hash=candidate_hash,
        source_checkpoint=source_checkpoint_path,
        row_schema_fields=row_schema_fields,
        run_items=run_items,
        horizon_steps=int(horizon_steps),
        device=device,
        milestone=milestone,
        post_repair_rows_path=final_post_repair_rows_path,
    )
    final_metrics = summarize_candidate_result(
        final_evaluation["post_repair_rows"],
        final_evaluation["gate_evaluation_rows"],
        final_evaluation["telemetry_summary"],
    )

    candidate_snapshot_path = output_dir / "candidate_config_snapshot.json"
    repair_candidate_sweep_path = output_dir / "repair_candidate_sweep.csv"
    selected_repair_trace_path = output_dir / "selected_repair_trace.csv"
    repaired_checkpoint_manifest_path = output_dir / "repaired_checkpoint_manifest.json"
    post_repair_rows_path = final_post_repair_rows_path
    protected_gate_evaluation_path = output_dir / "protected_gate_evaluation.csv"
    summary_path = output_dir / "summary.json"

    sweep_rows = build_candidate_sweep_rows(
        candidate_results,
        selected_candidate_id=str(selected_spec["candidate_id"]),
        selection_reason=selection_reason,
    )
    selected_trace_row = {
        **final_trace_rows[0],
        **{
            "candidate_id": selected_spec["candidate_id"],
            "selection_reason": selection_reason,
            "candidate_constraint_status": final_metrics["candidate_constraint_status"],
            "relaxation_amount": float(selected_spec["relaxation_amount"]),
            "retained_road_boundary_proof_pass": final_metrics[
                "retained_road_boundary_proof_pass"
            ],
            "retained_command_conflict_proof_pass": final_metrics[
                "retained_command_conflict_proof_pass"
            ],
            "retained_proof_gates_all_passed": final_metrics[
                "retained_proof_gates_all_passed"
            ],
            "mitigation_preserving_proof_pass": final_metrics[
                "mitigation_preserving_proof_pass"
            ],
            "protected_proof_gates_all_passed": final_metrics[
                "protected_proof_gates_all_passed"
            ],
            "mitigation_primary_evaluated_row_count": final_metrics[
                "mitigation_primary_evaluated_row_count"
            ],
            "mitigation_regressed_row_count": final_metrics[
                "mitigation_regressed_row_count"
            ],
            "sum_positive_mitigation_severity_delta": final_metrics[
                "sum_positive_mitigation_severity_delta"
            ],
        },
    }
    final_checkpoint_manifest = {
        **final_checkpoint_manifest,
        "repair_candidate_sweep": str(repair_candidate_sweep_path),
        "selected_repair_trace": str(selected_repair_trace_path),
        "selected_candidate_id": selected_spec["candidate_id"],
        "selection_reason": selection_reason,
        "candidate_constraint_status": final_metrics["candidate_constraint_status"],
        "retained_road_boundary_proof_pass": final_metrics[
            "retained_road_boundary_proof_pass"
        ],
        "retained_command_conflict_proof_pass": final_metrics[
            "retained_command_conflict_proof_pass"
        ],
        "mitigation_preserving_proof_pass": final_metrics[
            "mitigation_preserving_proof_pass"
        ],
        "protected_proof_gates_all_passed": final_metrics["protected_proof_gates_all_passed"],
    }

    write_json(
        candidate_snapshot_path,
        {
            "candidate_config": candidate,
            "candidate_config_hash": candidate_hash,
            "candidate_config_source": str(candidate_path),
            "candidate_config_mutated": False,
            "active_config_overwritten": False,
            "loaded_for_mitigation_preserving_repair_execution": True,
            "m2534_localization": str(localization_path),
            "m2534_regressed_seed": m2534_summary.get("regressed_seed"),
            "candidate_relaxations": [float(amount) for amount in candidate_relaxations],
            "snapshot_milestone": milestone,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    write_csv_rows(
        repair_candidate_sweep_path,
        sweep_rows,
        fieldnames=CANDIDATE_SWEEP_FIELDNAMES,
    )
    write_csv_rows(
        selected_repair_trace_path,
        [selected_trace_row],
        fieldnames=SELECTED_REPAIR_TRACE_FIELDNAMES,
    )
    write_json(repaired_checkpoint_manifest_path, final_checkpoint_manifest)
    write_csv_rows(
        post_repair_rows_path,
        final_evaluation["post_repair_rows"],
        fieldnames=POST_REPAIR_SMOKE_FIELDNAMES,
    )
    write_csv_rows(
        protected_gate_evaluation_path,
        final_evaluation["gate_evaluation_rows"],
        fieldnames=PROTECTED_GATE_EVALUATION_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        candidate_path=candidate_path,
        gate_binding_path=gate_binding_path,
        protected_rows_path=protected_rows_path,
        source_checkpoint=source_checkpoint_path,
        repaired_checkpoint=final_checkpoint,
        m2534_localization=localization_path,
        candidate=candidate,
        candidate_hash=candidate_hash,
        m2534_summary=m2534_summary,
        telemetry_summary=final_evaluation["telemetry_summary"],
        post_repair_rows=final_evaluation["post_repair_rows"],
        gate_evaluation_rows=final_evaluation["gate_evaluation_rows"],
        repair_candidate_sweep_rows=sweep_rows,
        selected_trace_rows=[selected_trace_row],
        checkpoint_manifest=final_checkpoint_manifest,
        candidate_snapshot_path=candidate_snapshot_path,
        repair_candidate_sweep_path=repair_candidate_sweep_path,
        selected_repair_trace_path=selected_repair_trace_path,
        repaired_checkpoint_manifest_path=repaired_checkpoint_manifest_path,
        post_repair_rows_path=post_repair_rows_path,
        protected_gate_evaluation_path=protected_gate_evaluation_path,
        selected_candidate_id=str(selected_spec["candidate_id"]),
        selected_relaxation_amount=float(selected_spec["relaxation_amount"]),
        selection_reason=selection_reason,
        milestone=milestone,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    write_json(summary_path, summary)
    return summary


def write_mitigation_preserving_repaired_checkpoint(
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    *,
    training_observations: np.ndarray,
    candidate: dict[str, Any],
    candidate_hash: str,
    output_dir: Path,
    device: str,
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
    source_stats = actor_action_stats(source_actions)

    with torch.no_grad():
        before_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()
        model.actor_mean.bias[1].add_(float(throttle_bias_delta))
        model.actor_mean.bias[2].add_(float(brake_bias_delta))
        after_bias = model.actor_mean.bias.detach().cpu().numpy().astype(float).tolist()

    repaired_actions = actor_actions(model, obs_t)
    repaired_stats = actor_action_stats(repaired_actions, reference_actions=source_actions)
    repaired_state = {
        key: value.detach().cpu()
        for key, value in model.state_dict().items()
    }
    repaired_model_state_hash = model_state_sha256(repaired_state)
    checkpoint_output = copy.deepcopy(checkpoint)
    checkpoint_output["model_state"] = repaired_state
    checkpoint_output.setdefault("metadata", {})
    checkpoint_output["metadata"] = {
        **dict(checkpoint_output.get("metadata", {})),
        "m2537_mitigation_preserving_repair_execution": {
            "milestone": milestone,
            "candidate_id": candidate_id,
            "update_method": "deterministic_mitigation_preserving_actor_head_bias_projection",
            "candidate_config_id": candidate.get("config_id", ""),
            "candidate_config_hash": candidate_hash,
            "source_checkpoint": str(source_checkpoint),
            "output_dir": str(output_dir),
            "trainable_parameter_names": ["actor_mean.bias[1]", "actor_mean.bias[2]"],
            "throttle_bias_delta": float(throttle_bias_delta),
            "brake_bias_delta": float(brake_bias_delta),
            "checkpoint_promoted": False,
            "hidden_or_oracle_actor_inputs_required": False,
            "active_config_overwritten": False,
            "candidate_config_mutated": False,
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
        "update_method": "deterministic_mitigation_preserving_actor_head_bias_projection",
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "training_observation_count": int(training_observations.shape[0]),
        "trainable_parameter_names": "actor_mean.bias[1];actor_mean.bias[2]",
        "source_model_state_hash": source_model_state_hash,
        "repaired_model_state_hash": repaired_model_state_hash,
        "actor_mean_bias_before": _json_list(before_bias),
        "actor_mean_bias_after": _json_list(after_bias),
        "throttle_bias_delta": float(throttle_bias_delta),
        "brake_bias_delta": float(brake_bias_delta),
        "source_conflict_proxy": source_stats["conflict_proxy"],
        "repaired_conflict_proxy": repaired_stats["conflict_proxy"],
        "source_mean_action_throttle": source_stats["mean_action_throttle"],
        "repaired_mean_action_throttle": repaired_stats["mean_action_throttle"],
        "source_mean_action_brake": source_stats["mean_action_brake"],
        "repaired_mean_action_brake": repaired_stats["mean_action_brake"],
        "mean_action_delta_l1": repaired_stats["mean_action_delta_l1_from_source"],
        "finite_update": finite_update,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "candidate_config_mutated": False,
        "checkpoint_promoted": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    manifest = {
        "manifest_id": "m2537_repaired_checkpoint_manifest_v0",
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
        "update_method": "deterministic_mitigation_preserving_actor_head_bias_projection",
        "trainable_parameter_names": ["actor_mean.bias[1]", "actor_mean.bias[2]"],
        "training_observation_count": int(training_observations.shape[0]),
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "active_config_overwritten": False,
        "candidate_config_mutated": False,
        "checkpoint_promoted": False,
        "promotion_metadata_written": False,
        "finite_update": finite_update,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }
    return [trace_row], manifest


def evaluate_repair_checkpoint(
    checkpoint_path: Path,
    *,
    protected: list[dict[str, str]],
    gate_binding_rows: list[dict[str, str]],
    candidate: dict[str, Any],
    candidate_hash: str,
    source_checkpoint: Path,
    row_schema_fields: list[str],
    run_items: list[Any],
    horizon_steps: int,
    device: str,
    milestone: str,
    post_repair_rows_path: Path | None = None,
) -> dict[str, Any]:
    telemetry_rows, telemetry_summary = run_fresh_seed_telemetry(
        run_items,
        checkpoint_path=checkpoint_path,
        horizon_steps=int(horizon_steps),
        device=device,
    )
    measured_behavior_rows, _measured_event_rows = build_fresh_seed_measured_rows(
        telemetry_rows,
        run_items=run_items,
        checkpoint_path=str(checkpoint_path),
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    post_repair_rows = build_mitigation_preserving_post_repair_smoke_rows(
        protected,
        measured_behavior_rows,
        candidate=candidate,
        candidate_hash=candidate_hash,
        source_checkpoint=source_checkpoint,
        repaired_checkpoint=checkpoint_path,
        milestone=milestone,
    )
    gate_evaluation_rows = build_mitigation_preserving_gate_evaluation_rows(
        gate_binding_rows,
        post_repair_rows,
        post_repair_rows_path=post_repair_rows_path or Path("post_repair_smoke_rows.csv"),
    )
    return {
        "telemetry_summary": telemetry_summary,
        "post_repair_rows": post_repair_rows,
        "gate_evaluation_rows": gate_evaluation_rows,
    }


def build_mitigation_preserving_post_repair_smoke_rows(
    protected_rows: list[dict[str, str]],
    measured_behavior_rows: list[dict[str, Any]],
    *,
    candidate: dict[str, Any],
    candidate_hash: str,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    milestone: str,
) -> list[dict[str, Any]]:
    rows = build_repair_smoke_rows(
        protected_rows,
        measured_behavior_rows,
        candidate=candidate,
        candidate_hash=candidate_hash,
        milestone=milestone,
    )
    for row in rows:
        row["repair_smoke_status"] = (
            "mitigation_preserving_post_repair_source_only_behavior_measured"
            if _as_bool(row["protected_row_matched"])
            else "protected_row_missing_from_mitigation_preserving_post_repair_smoke"
        )
        row["repair_training_started"] = True
        row["claim_scope"] = CLAIM_SCOPE
        row["forbidden_interpretation"] = FORBIDDEN_INTERPRETATION
        row["source_checkpoint_path"] = str(source_checkpoint)
        row["repaired_checkpoint_path"] = str(repaired_checkpoint)
        row["repair_execution_started"] = True
        row["repaired_checkpoint_written"] = repaired_checkpoint.exists()
    return rows


def build_mitigation_preserving_gate_evaluation_rows(
    gate_bindings: list[dict[str, str]],
    post_repair_rows: list[dict[str, Any]],
    *,
    post_repair_rows_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for binding in gate_bindings:
        gate_id = binding["gate_id"]
        bound_rows = _bound_rows_for_group(post_repair_rows, binding["protected_group"])
        gate_pass, status, failure_type, improved, regressed, unchanged = _evaluate_post_repair_gate(
            gate_id,
            bound_rows,
        )
        rows.append(
            {
                "gate_id": gate_id,
                "gate_tier": binding["gate_tier"],
                "protected_group": binding["protected_group"],
                "metric": binding["metric"],
                "binding_status": binding["binding_status"],
                "bound_row_count": int(binding["protected_row_count"]),
                "evaluated_row_count": len(bound_rows),
                "trace_to_gate_binding": True,
                "trace_to_protected_rows": len(bound_rows)
                == int(binding["protected_row_count"]),
                "evaluation_status": _m2537_evaluation_status(gate_id, status),
                "gate_pass": gate_pass,
                "improved_row_count": improved,
                "regressed_row_count": regressed,
                "unchanged_row_count": unchanged,
                "failure_type": failure_type,
                "blocks_claims": _blocks_claims(gate_id),
                "next_route_if_fail": _next_route_if_fail(gate_id),
                "source_gate_artifact": binding["source_gate_artifact"],
                "source_rows_artifact": binding["source_rows_artifact"],
                "repair_smoke_rows": str(post_repair_rows_path),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def summarize_candidate_result(
    post_repair_rows: list[dict[str, Any]],
    gate_evaluation_rows: list[dict[str, Any]],
    telemetry_summary: dict[str, Any],
) -> dict[str, Any]:
    gate_by_id = {row["gate_id"]: row for row in gate_evaluation_rows}
    proof_gate_ids = ["road_boundary_proof", "mitigation_proof", "command_conflict_proof"]
    failed_proof_gate_ids = [
        gate_id
        for gate_id in proof_gate_ids
        if not _as_bool(gate_by_id.get(gate_id, {}).get("gate_pass"))
    ]
    proof_pass_count = len(proof_gate_ids) - len(failed_proof_gate_ids)
    mitigation_rows = [
        row
        for row in post_repair_rows
        if row["protected_group"] == "mitigation_primary"
        and row["row_role"] == "primary_protected"
    ]
    mitigation_improved = sum(
        _float(row["severity_delta"]) < -1e-9
        and _float(row["road_margin_delta_m"]) > 1e-9
        for row in mitigation_rows
    )
    mitigation_regressed = sum(
        _float(row["severity_delta"]) > 1e-9
        or _float(row["road_margin_delta_m"]) < -1e-9
        for row in mitigation_rows
    )
    mitigation_unchanged = max(0, len(mitigation_rows) - mitigation_improved - mitigation_regressed)
    positive_severity_deltas = [
        max(0.0, _float(row["severity_delta"]))
        for row in mitigation_rows
    ]
    retained_road_pass = _as_bool(gate_by_id.get("road_boundary_proof", {}).get("gate_pass"))
    retained_conflict_pass = _as_bool(
        gate_by_id.get("command_conflict_proof", {}).get("gate_pass")
    )
    mitigation_pass = _as_bool(gate_by_id.get("mitigation_proof", {}).get("gate_pass"))
    retained_all_pass = retained_road_pass and retained_conflict_pass
    proof_all_pass = retained_all_pass and mitigation_pass
    return {
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "post_repair_smoke_row_count": len(post_repair_rows),
        "protected_gate_evaluation_row_count": len(gate_evaluation_rows),
        "protected_row_match_count": sum(
            _as_bool(row["protected_row_matched"]) for row in post_repair_rows
        ),
        "all_protected_rows_matched": bool(post_repair_rows)
        and all(_as_bool(row["protected_row_matched"]) for row in post_repair_rows),
        "gate_evaluation_traceable": bool(gate_evaluation_rows)
        and all(
            _as_bool(row["trace_to_gate_binding"]) and _as_bool(row["trace_to_protected_rows"])
            for row in gate_evaluation_rows
        ),
        "retained_road_boundary_proof_pass": retained_road_pass,
        "retained_command_conflict_proof_pass": retained_conflict_pass,
        "retained_proof_gates_all_passed": retained_all_pass,
        "mitigation_preserving_proof_pass": mitigation_pass,
        "protected_proof_gates_all_passed": proof_all_pass,
        "protected_proof_gate_pass_count": proof_pass_count,
        "protected_proof_gate_fail_count": len(failed_proof_gate_ids),
        "failed_proof_gate_ids": failed_proof_gate_ids,
        "mitigation_primary_evaluated_row_count": len(mitigation_rows),
        "mitigation_improved_row_count": int(mitigation_improved),
        "mitigation_regressed_row_count": int(mitigation_regressed),
        "mitigation_unchanged_row_count": int(mitigation_unchanged),
        "max_mitigation_severity_delta": max(
            (_float(row["severity_delta"]) for row in mitigation_rows),
            default=0.0,
        ),
        "sum_positive_mitigation_severity_delta": float(sum(positive_severity_deltas)),
        "min_mitigation_road_margin_delta_m": min(
            (_float(row["road_margin_delta_m"]) for row in mitigation_rows),
            default=0.0,
        ),
        "max_command_conflict_delta": max(
            (_float(row["command_conflict_delta"]) for row in post_repair_rows),
            default=0.0,
        ),
        "candidate_constraint_status": (
            "all_protected_proof_gates_passed"
            if proof_all_pass
            else "retained_gates_passed_mitigation_preserving_failed"
            if retained_all_pass
            else "retained_gate_washout"
        ),
    }


def build_candidate_sweep_rows(
    candidate_results: list[dict[str, Any]],
    *,
    selected_candidate_id: str,
    selection_reason: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in candidate_results:
        spec = result["spec"]
        manifest = result["checkpoint_manifest"]
        metrics = summarize_candidate_result(
            result["post_repair_rows"],
            result["gate_evaluation_rows"],
            result["telemetry_summary"],
        )
        behavior_changed = bool(manifest.get("behavior_changed"))
        selected = str(spec["candidate_id"]) == selected_candidate_id
        rows.append(
            {
                "candidate_id": spec["candidate_id"],
                "candidate_index": spec["candidate_index"],
                "source_checkpoint": manifest.get("source_checkpoint", ""),
                "candidate_checkpoint": manifest.get("repaired_checkpoint", ""),
                "relaxation_amount": spec["relaxation_amount"],
                "throttle_bias_delta": spec["throttle_bias_delta"],
                "brake_bias_delta": spec["brake_bias_delta"],
                "behavior_changed_from_source": behavior_changed,
                "finite_update": bool(manifest.get("finite_update")),
                "candidate_checkpoint_hash": manifest.get("repaired_checkpoint_hash", ""),
                "source_model_state_hash": manifest.get("source_model_state_hash", ""),
                "candidate_model_state_hash": manifest.get("repaired_model_state_hash", ""),
                "eligible_for_repair_trace": behavior_changed,
                "selected_for_repair_trace": selected,
                "selection_reason": selection_reason if selected else "",
                "diagnostic_only_no_ranking_claim": True,
                "success_rate_field_emitted": False,
                "ranking_or_winner_field_emitted": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
                **{
                    key: (
                        ";".join(metrics[key])
                        if key == "failed_proof_gate_ids"
                        else metrics[key]
                    )
                    for key in metrics
                },
            }
        )
    return rows


def select_repair_candidate(
    candidate_results: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    candidates = [
        result
        for result in candidate_results
        if bool(result["checkpoint_manifest"].get("behavior_changed"))
    ]
    behavior_changed_candidate_available = bool(candidates)
    if not candidates:
        candidates = list(candidate_results)
    selected = min(candidates, key=_selection_key)
    metrics = summarize_candidate_result(
        selected["post_repair_rows"],
        selected["gate_evaluation_rows"],
        selected["telemetry_summary"],
    )
    if not behavior_changed_candidate_available:
        reason = "no_behavior_changed_candidate_available_selected_best_traceable_candidate"
    elif metrics["protected_proof_gates_all_passed"]:
        reason = "behavior_changed_candidate_satisfies_retained_and_mitigation_proof_constraints"
    elif metrics["retained_proof_gates_all_passed"]:
        reason = "behavior_changed_candidate_retains_road_boundary_and_command_conflict_but_mitigation_proof_remains_failed"
    else:
        reason = "behavior_changed_candidate_selected_for_trace_after_retained_gate_washout"
    return selected, reason


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    candidate_path: Path,
    gate_binding_path: Path,
    protected_rows_path: Path,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    m2534_localization: Path,
    candidate: dict[str, Any],
    candidate_hash: str,
    m2534_summary: dict[str, Any],
    telemetry_summary: dict[str, Any],
    post_repair_rows: list[dict[str, Any]],
    gate_evaluation_rows: list[dict[str, Any]],
    repair_candidate_sweep_rows: list[dict[str, Any]],
    selected_trace_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    candidate_snapshot_path: Path,
    repair_candidate_sweep_path: Path,
    selected_repair_trace_path: Path,
    repaired_checkpoint_manifest_path: Path,
    post_repair_rows_path: Path,
    protected_gate_evaluation_path: Path,
    selected_candidate_id: str,
    selected_relaxation_amount: float,
    selection_reason: str,
    milestone: str,
    seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    required_artifacts_present = (
        candidate_snapshot_path.exists()
        and repair_candidate_sweep_path.exists()
        and selected_repair_trace_path.exists()
        and repaired_checkpoint_manifest_path.exists()
        and post_repair_rows_path.exists()
        and protected_gate_evaluation_path.exists()
    )
    actor_contract = candidate.get("actor_contract", {})
    actor_contract_shape = (
        int(actor_contract.get("observation_shape", -1)) == P0_OBSERVATION_DIM
        and int(actor_contract.get("action_shape", -1)) == ACTION_DIM
        and _row_int_set(post_repair_rows, "observation_shape") == {P0_OBSERVATION_DIM}
        and _row_int_set(post_repair_rows, "action_shape") == {ACTION_DIM}
    )
    all_rows_matched = bool(post_repair_rows) and all(
        _as_bool(row["protected_row_matched"]) for row in post_repair_rows
    )
    gate_rows_traceable = bool(gate_evaluation_rows) and all(
        _as_bool(row["trace_to_gate_binding"]) and _as_bool(row["trace_to_protected_rows"])
        for row in gate_evaluation_rows
    )
    evaluated_gate_ids = {row["gate_id"] for row in gate_evaluation_rows}
    metrics = summarize_candidate_result(post_repair_rows, gate_evaluation_rows, telemetry_summary)
    deferred_gate_count = sum(
        str(row["evaluation_status"]).startswith("deferred") for row in gate_evaluation_rows
    )
    passed_gate_ids = [row["gate_id"] for row in gate_evaluation_rows if _as_bool(row["gate_pass"])]
    no_hidden_or_oracle = (
        not bool(candidate.get("actor_contract", {}).get("actor_input_contract_changed", True))
        and not bool(actor_contract.get("rule_switching_controller_modes_allowed", True))
        and {str(row["actor_input_leak_flags"]).lower() for row in post_repair_rows}
        == {"none"}
        and not any(_as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in post_repair_rows)
        and not any(_as_bool(row["controller_mode_used"]) for row in post_repair_rows)
        and not any(_as_bool(row["mu_enter_actor_input"]) for row in post_repair_rows)
    )
    no_claim_boundary_violation = (
        not any(FALSE_CLAIM_FLAGS.values())
        and not any(_as_bool(row["success_rate_field_emitted"]) for row in post_repair_rows)
        and not any(_as_bool(row["ranking_or_winner_field_emitted"]) for row in post_repair_rows)
        and not any(_as_bool(row["success_rate_field_emitted"]) for row in repair_candidate_sweep_rows)
        and not any(_as_bool(row["ranking_or_winner_field_emitted"]) for row in repair_candidate_sweep_rows)
    )
    failure_types = {
        str(row["failure_type"])
        for row in gate_evaluation_rows
        if not _as_bool(row["gate_pass"]) and str(row["failure_type"]) not in {"", "none"}
    }
    if metrics["retained_proof_gates_all_passed"] and not metrics["protected_proof_gates_all_passed"]:
        failure_types.add("proof_washout")
    if metrics["mitigation_regressed_row_count"] > 0:
        failure_types.add("behavior_regression")
    if not bool(checkpoint_manifest.get("finite_update")):
        failure_types.add("training_instability")
    if not gate_rows_traceable:
        failure_types.add("lineage_invalid")

    next_blocker = (
        DEFAULT_FRESH_GENERALIZATION_BLOCKER
        if metrics["protected_proof_gates_all_passed"]
        else DEFAULT_BRANCH_SYNTHESIS_BLOCKER
        if not metrics["retained_proof_gates_all_passed"]
        else DEFAULT_RESULT_AUDIT_BLOCKER
    )
    status_pass = (
        bool(telemetry_summary.get("checkpoint_admitted"))
        and required_artifacts_present
        and output_dir.exists()
        and candidate_path.exists()
        and gate_binding_path.exists()
        and protected_rows_path.exists()
        and source_checkpoint.exists()
        and m2534_localization.exists()
        and repaired_checkpoint.exists()
        and bool(checkpoint_manifest.get("repaired_checkpoint_written"))
        and bool(checkpoint_manifest.get("behavior_changed"))
        and len(repair_candidate_sweep_rows) >= 1
        and len(selected_trace_rows) == 1
        and len(post_repair_rows) == 45
        and len(gate_evaluation_rows) == 7
        and evaluated_gate_ids
        == {
            "contract_p0_72_3",
            "no_oracle_actor_inputs",
            "road_boundary_proof",
            "mitigation_proof",
            "command_conflict_proof",
            "fresh_seed_generalization",
            "no_ranking_no_success_rate",
        }
        and all_rows_matched
        and gate_rows_traceable
        and actor_contract_shape
        and no_hidden_or_oracle
        and no_claim_boundary_violation
    )
    outcome_class = (
        "mitigation_preserving_repair_all_proof_gates_passed"
        if status_pass and metrics["protected_proof_gates_all_passed"]
        else "mitigation_preserving_repair_retained_gates_passed_mitigation_failed"
        if status_pass and metrics["retained_proof_gates_all_passed"]
        else "mitigation_preserving_repair_retained_gate_washout_recorded"
        if status_pass
        else "mitigation_preserving_repair_execution_incomplete"
    )
    return {
        "result_class": (
            "engineering_controller_failure_surface_mitigation_preserving_repair_execution_pass"
            if status_pass
            else "engineering_controller_failure_surface_mitigation_preserving_repair_execution_failed"
        ),
        "status_pass": bool(status_pass),
        "post_repair_outcome_class": outcome_class,
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "output_dir": str(output_dir),
        "summary": str(summary_path),
        "candidate_config": str(candidate_path),
        "candidate_config_hash": candidate_hash,
        "candidate_config_id": candidate.get("config_id", ""),
        "candidate_config_snapshot": str(candidate_snapshot_path),
        "protected_gate_bindings": str(gate_binding_path),
        "protected_rows": str(protected_rows_path),
        "m2534_localization": str(m2534_localization),
        "m2534_regressed_seed": m2534_summary.get("regressed_seed"),
        "m2534_regressed_source_row_id": m2534_summary.get("regressed_source_row_id"),
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "repair_candidate_sweep": str(repair_candidate_sweep_path),
        "selected_repair_trace": str(selected_repair_trace_path),
        "repaired_checkpoint_manifest": str(repaired_checkpoint_manifest_path),
        "post_repair_smoke_rows": str(post_repair_rows_path),
        "protected_gate_evaluation": str(protected_gate_evaluation_path),
        "required_artifacts_present": bool(required_artifacts_present),
        "candidate_config_loaded": True,
        "candidate_config_mutated": False,
        "active_config_overwritten": False,
        "immutable_candidate_config": bool(candidate.get("immutable_candidate_config")),
        "seed_count_per_role": int(seed_count),
        "horizon_steps": int(horizon_steps),
        "selected_candidate_id": selected_candidate_id,
        "selected_relaxation_amount": float(selected_relaxation_amount),
        "selection_reason": selection_reason,
        "candidate_sweep_row_count": len(repair_candidate_sweep_rows),
        "selected_repair_trace_row_count": len(selected_trace_rows),
        "repair_execution_started": True,
        "repair_training_started": True,
        "training_run": True,
        "repaired_checkpoint_written": bool(checkpoint_manifest.get("repaired_checkpoint_written")),
        "repaired_checkpoint_hash": checkpoint_manifest.get("repaired_checkpoint_hash", ""),
        "source_checkpoint_hash": checkpoint_manifest.get("source_checkpoint_hash", ""),
        "checkpoint_behavior_changed": bool(checkpoint_manifest.get("behavior_changed")),
        "post_repair_smoke_row_count": len(post_repair_rows),
        "protected_gate_evaluation_row_count": len(gate_evaluation_rows),
        "protected_row_match_count": metrics["protected_row_match_count"],
        "all_protected_rows_matched": bool(all_rows_matched),
        "gate_evaluation_traceable": bool(gate_rows_traceable),
        "actor_contract_id": actor_contract.get("actor_contract_id", ""),
        "observation_shape": int(actor_contract.get("observation_shape", -1)),
        "action_shape": int(actor_contract.get("action_shape", -1)),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "actor_input_contract_changed": bool(actor_contract.get("actor_input_contract_changed", True)),
        "hidden_or_oracle_actor_inputs_required": False,
        "rule_switching_controller_modes_allowed": bool(
            actor_contract.get("rule_switching_controller_modes_allowed", True)
        ),
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "open_loop_action_rollout_run": True,
        "retained_road_boundary_proof_pass": metrics["retained_road_boundary_proof_pass"],
        "retained_command_conflict_proof_pass": metrics[
            "retained_command_conflict_proof_pass"
        ],
        "retained_proof_gates_all_passed": metrics["retained_proof_gates_all_passed"],
        "mitigation_preserving_proof_pass": metrics["mitigation_preserving_proof_pass"],
        "protected_proof_gates_all_passed": metrics["protected_proof_gates_all_passed"],
        "protected_proof_gate_pass_count": metrics["protected_proof_gate_pass_count"],
        "protected_proof_gate_fail_count": metrics["protected_proof_gate_fail_count"],
        "failed_proof_gate_ids": metrics["failed_proof_gate_ids"],
        "passed_gate_ids": passed_gate_ids,
        "mitigation_primary_evaluated_row_count": metrics[
            "mitigation_primary_evaluated_row_count"
        ],
        "all_mitigation_primary_rows_considered": metrics[
            "mitigation_primary_evaluated_row_count"
        ]
        == 5,
        "mitigation_improved_row_count": metrics["mitigation_improved_row_count"],
        "mitigation_regressed_row_count": metrics["mitigation_regressed_row_count"],
        "mitigation_unchanged_row_count": metrics["mitigation_unchanged_row_count"],
        "max_mitigation_severity_delta": metrics["max_mitigation_severity_delta"],
        "sum_positive_mitigation_severity_delta": metrics[
            "sum_positive_mitigation_severity_delta"
        ],
        "min_mitigation_road_margin_delta_m": metrics[
            "min_mitigation_road_margin_delta_m"
        ],
        "max_command_conflict_delta": metrics["max_command_conflict_delta"],
        "candidate_constraint_status": metrics["candidate_constraint_status"],
        "deferred_gate_count": int(deferred_gate_count),
        "fresh_generalization_run": False,
        "failure_types_observed": sorted(failure_types),
        "claim_boundary": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def _selection_key(result: dict[str, Any]) -> tuple[Any, ...]:
    spec = result["spec"]
    manifest = result["checkpoint_manifest"]
    metrics = summarize_candidate_result(
        result["post_repair_rows"],
        result["gate_evaluation_rows"],
        result["telemetry_summary"],
    )
    return (
        not metrics["protected_proof_gates_all_passed"],
        not metrics["retained_proof_gates_all_passed"],
        not metrics["mitigation_preserving_proof_pass"],
        int(metrics["protected_proof_gate_fail_count"]),
        int(not bool(manifest.get("behavior_changed"))),
        int(metrics["mitigation_regressed_row_count"]),
        float(metrics["sum_positive_mitigation_severity_delta"]),
        float(metrics["max_mitigation_severity_delta"]),
        -int(metrics["mitigation_improved_row_count"]),
        abs(float(spec["relaxation_amount"])),
        int(spec["candidate_index"]),
    )


def _m2537_evaluation_status(gate_id: str, status: str) -> str:
    if gate_id == "road_boundary_proof":
        return f"retained_road_boundary_{status}"
    if gate_id == "command_conflict_proof":
        return f"retained_command_conflict_{status}"
    if gate_id == "mitigation_proof":
        return f"mitigation_preserving_{status}"
    return status


def _next_route_if_fail(gate_id: str) -> str:
    return {
        "contract_p0_72_3": "contract repair before implementation",
        "no_oracle_actor_inputs": "design repair or branch synthesis",
        "road_boundary_proof": DEFAULT_BRANCH_SYNTHESIS_BLOCKER,
        "mitigation_proof": DEFAULT_RESULT_AUDIT_BLOCKER,
        "command_conflict_proof": DEFAULT_BRANCH_SYNTHESIS_BLOCKER,
        "fresh_seed_generalization": DEFAULT_FRESH_GENERALIZATION_BLOCKER,
        "no_ranking_no_success_rate": "claim-boundary audit",
    }.get(gate_id, DEFAULT_RESULT_AUDIT_BLOCKER)


def _amount_slug(amount: float) -> str:
    text = f"{float(amount):.3f}".rstrip("0").rstrip(".")
    if text == "":
        text = "0"
    return text.replace("-", "neg").replace(".", "p")


def _parse_relaxations(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the M2537 mitigation-preserving repair execution."
    )
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    parser.add_argument("--gate-bindings", type=Path, default=DEFAULT_GATE_BINDINGS)
    parser.add_argument("--protected-rows", type=Path, default=DEFAULT_PROTECTED_ROWS)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--m2534-localization", type=Path, default=DEFAULT_M2534_LOCALIZATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--candidate-relaxations",
        default=",".join(str(amount) for amount in DEFAULT_RELAXATION_AMOUNTS),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_mitigation_preserving_repair_execution(
        args.output_dir,
        candidate_config=args.candidate_config,
        gate_bindings=args.gate_bindings,
        protected_rows=args.protected_rows,
        source_checkpoint=args.source_checkpoint,
        m2534_localization=args.m2534_localization,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        candidate_relaxations=_parse_relaxations(args.candidate_relaxations),
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "post_repair_outcome_class={post_repair_outcome_class} "
        "protected_proof_gate_fail_count={protected_proof_gate_fail_count} "
        "selected_candidate_id={selected_candidate_id} output_dir={output_dir}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
