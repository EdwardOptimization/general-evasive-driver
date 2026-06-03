"""Guarded source-only repair execution for the M2528 failure-surface config."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_intervention_repair_smoke import (
    DEFAULT_CANDIDATE_CONFIG,
    DEFAULT_CHECKPOINT,
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
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
)


DEFAULT_OUTPUT_DIR = Path(
    "runs/m2532_engineering_controller_failure_surface_guarded_repair_execution"
)
DEFAULT_MILESTONE = (
    "m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight"
)
DEFAULT_RESULT_AUDIT_BLOCKER = (
    "m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit"
)
DEFAULT_PROOF_FAILURE_SYNTHESIS_BLOCKER = (
    "m2533-engineering-controller-failure-surface-guarded-repair-proof-failure-synthesis"
)

CLAIM_SCOPE = "guarded source-only repair execution preflight only"
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

REPAIR_TRAINING_TRACE_FIELDNAMES = [
    "update_index",
    "update_method",
    "source_checkpoint",
    "repaired_checkpoint",
    "training_observation_count",
    "trainable_parameter_names",
    "source_model_state_hash",
    "repaired_model_state_hash",
    "actor_mean_bias_before",
    "actor_mean_bias_after",
    "throttle_bias_delta",
    "brake_bias_delta",
    "source_conflict_proxy",
    "repaired_conflict_proxy",
    "source_mean_action_throttle",
    "repaired_mean_action_throttle",
    "source_mean_action_brake",
    "repaired_mean_action_brake",
    "mean_action_delta_l1",
    "finite_update",
    "actor_contract_shape_72_action_3",
    "hidden_or_oracle_actor_inputs_required",
    "active_config_overwritten",
    "candidate_config_mutated",
    "checkpoint_promoted",
    "claim_scope",
    "forbidden_interpretation",
]

POST_REPAIR_SMOKE_FIELDNAMES = REPAIR_SMOKE_FIELDNAMES + [
    "source_checkpoint_path",
    "repaired_checkpoint_path",
    "repair_execution_started",
    "repaired_checkpoint_written",
]


def run_guarded_repair_execution(
    output_dir: Path,
    *,
    candidate_config: Path | str = DEFAULT_CANDIDATE_CONFIG,
    gate_bindings: Path | str = DEFAULT_GATE_BINDINGS,
    protected_rows: Path | str = DEFAULT_PROTECTED_ROWS,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = 100,
    device: str = "cpu",
    throttle_bias_delta: float = -16.0,
    brake_bias_delta: float = 16.0,
    milestone: str = DEFAULT_MILESTONE,
) -> dict[str, Any]:
    if int(seed_count) < DEFAULT_SEED_COUNT:
        raise ValueError(f"seed_count must be at least {DEFAULT_SEED_COUNT}")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = Path(candidate_config)
    gate_binding_path = Path(gate_bindings)
    protected_rows_path = Path(protected_rows)
    source_checkpoint = Path(checkpoint_path)

    candidate = read_json(candidate_path)
    candidate_hash = _file_sha256(candidate_path)
    gate_binding_rows = _read_csv_rows(gate_binding_path)
    protected = _read_csv_rows(protected_rows_path)
    row_schema_fields = [row["field_name"] for row in _read_csv_rows(M2514_ROW_SCHEMA)]

    repaired_checkpoint = output_dir / "checkpoints" / "m2532_guarded_actor_head_repair.pt"
    training_observations = collect_protected_primary_reset_observations(
        protected,
        seed_count=int(seed_count),
    )
    repair_trace_rows, checkpoint_manifest = write_guarded_repaired_checkpoint(
        source_checkpoint,
        repaired_checkpoint,
        training_observations=training_observations,
        candidate=candidate,
        candidate_hash=candidate_hash,
        output_dir=output_dir,
        device=device,
        throttle_bias_delta=float(throttle_bias_delta),
        brake_bias_delta=float(brake_bias_delta),
        milestone=milestone,
    )

    run_items, _seed_panel_spec_rows = build_seed_panel_specs(seed_count=int(seed_count))
    telemetry_rows, telemetry_summary = run_fresh_seed_telemetry(
        run_items,
        checkpoint_path=repaired_checkpoint,
        horizon_steps=int(horizon_steps),
        device=device,
    )
    measured_behavior_rows, _measured_event_rows = build_fresh_seed_measured_rows(
        telemetry_rows,
        run_items=run_items,
        checkpoint_path=str(repaired_checkpoint),
        row_schema_fields=row_schema_fields,
        milestone=milestone,
    )
    post_repair_rows = build_post_repair_smoke_rows(
        protected,
        measured_behavior_rows,
        candidate=candidate,
        candidate_hash=candidate_hash,
        source_checkpoint=source_checkpoint,
        repaired_checkpoint=repaired_checkpoint,
        milestone=milestone,
    )

    candidate_snapshot_path = output_dir / "candidate_config_snapshot.json"
    repair_training_trace_path = output_dir / "repair_training_trace.csv"
    repaired_checkpoint_manifest_path = output_dir / "repaired_checkpoint_manifest.json"
    post_repair_rows_path = output_dir / "post_repair_smoke_rows.csv"
    protected_gate_evaluation_path = output_dir / "protected_gate_evaluation.csv"
    summary_path = output_dir / "summary.json"

    gate_evaluation_rows = build_post_repair_protected_gate_evaluation_rows(
        gate_binding_rows,
        post_repair_rows,
        post_repair_rows_path=post_repair_rows_path,
    )

    write_json(
        candidate_snapshot_path,
        {
            "candidate_config": candidate,
            "candidate_config_hash": candidate_hash,
            "candidate_config_source": str(candidate_path),
            "candidate_config_mutated": False,
            "active_config_overwritten": False,
            "loaded_for_guarded_repair_execution": True,
            "snapshot_milestone": milestone,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    write_csv_rows(
        repair_training_trace_path,
        repair_trace_rows,
        fieldnames=REPAIR_TRAINING_TRACE_FIELDNAMES,
    )
    write_json(repaired_checkpoint_manifest_path, checkpoint_manifest)
    write_csv_rows(
        post_repair_rows_path,
        post_repair_rows,
        fieldnames=POST_REPAIR_SMOKE_FIELDNAMES,
    )
    write_csv_rows(
        protected_gate_evaluation_path,
        gate_evaluation_rows,
        fieldnames=PROTECTED_GATE_EVALUATION_FIELDNAMES,
    )

    summary = build_summary(
        output_dir=output_dir,
        summary_path=summary_path,
        candidate_path=candidate_path,
        gate_binding_path=gate_binding_path,
        protected_rows_path=protected_rows_path,
        source_checkpoint=source_checkpoint,
        repaired_checkpoint=repaired_checkpoint,
        candidate=candidate,
        candidate_hash=candidate_hash,
        telemetry_summary=telemetry_summary,
        post_repair_rows=post_repair_rows,
        gate_evaluation_rows=gate_evaluation_rows,
        repair_trace_rows=repair_trace_rows,
        checkpoint_manifest=checkpoint_manifest,
        candidate_snapshot_path=candidate_snapshot_path,
        repair_training_trace_path=repair_training_trace_path,
        repaired_checkpoint_manifest_path=repaired_checkpoint_manifest_path,
        post_repair_rows_path=post_repair_rows_path,
        protected_gate_evaluation_path=protected_gate_evaluation_path,
        milestone=milestone,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    write_json(summary_path, summary)
    return summary


def collect_protected_primary_reset_observations(
    protected_rows: list[dict[str, str]],
    *,
    seed_count: int,
) -> np.ndarray:
    primary_keys = {
        (str(row["scenario_role"]), int(row["seed"]))
        for row in protected_rows
        if row["row_role"] == "primary_protected"
    }
    run_items, _rows = build_seed_panel_specs(seed_count=int(seed_count))
    items_by_key = {
        (str(item.role_family), int(item.seed)): item
        for item in run_items
    }
    extractor = P0ObservationExtractor()
    observations: list[np.ndarray] = []
    for key in sorted(primary_keys):
        item = items_by_key[key]
        backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
        try:
            reset_result = backend.reset(
                BackendResetRequest(
                    seed=item.seed,
                    scenario_spec_id=item.fixture_id,
                    role_family=item.role_family,
                    options={
                        "seed_panel_id": item.seed_panel_id,
                        "seed_index": item.seed_index,
                        "seed": item.seed,
                        "base_fixture_id": item.base_fixture_id,
                        "repair_observation_source": "protected_primary_reset",
                    },
                )
            )
            observation = extractor.extract(reset_result.actor_view)
            if observation.shape != (P0_OBSERVATION_DIM,):
                raise RuntimeError(
                    f"expected P0 observation shape {(P0_OBSERVATION_DIM,)}, got {observation.shape}"
                )
            observations.append(np.asarray(observation, dtype=np.float32))
        finally:
            backend.close()
    if len(observations) != len(primary_keys):
        raise RuntimeError("failed to collect all protected primary repair observations")
    return np.stack(observations, axis=0)


def write_guarded_repaired_checkpoint(
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
        "m2532_guarded_repair_execution": {
            "milestone": milestone,
            "update_method": "deterministic_guarded_actor_head_bias_projection",
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
        "update_method": "deterministic_guarded_actor_head_bias_projection",
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
        "manifest_id": "m2532_repaired_checkpoint_manifest_v0",
        "milestone": milestone,
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
        "update_method": "deterministic_guarded_actor_head_bias_projection",
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


def actor_actions(model: torch.nn.Module, observations: torch.Tensor) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        dist, _value = model.forward(observations)
        return torch.tanh(dist.mean)


def actor_action_stats(
    actions: torch.Tensor,
    *,
    reference_actions: torch.Tensor | None = None,
) -> dict[str, float]:
    with torch.no_grad():
        physical_throttle = 0.5 * (actions[:, 1] + 1.0)
        physical_brake = 0.5 * (actions[:, 2] + 1.0)
        conflict_proxy = torch.mean(physical_throttle * physical_brake)
        if reference_actions is None:
            action_delta = 0.0
        else:
            action_delta = float(torch.mean(torch.abs(actions - reference_actions)).detach().cpu().item())
    return {
        "conflict_proxy": float(conflict_proxy.detach().cpu().item()),
        "mean_action_throttle": float(actions[:, 1].mean().detach().cpu().item()),
        "mean_action_brake": float(actions[:, 2].mean().detach().cpu().item()),
        "mean_action_delta_l1_from_source": action_delta,
    }


def build_post_repair_smoke_rows(
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
            "post_repair_source_only_behavior_measured"
            if _as_bool(row["protected_row_matched"])
            else "protected_row_missing_from_post_repair_smoke"
        )
        row["repair_training_started"] = True
        row["claim_scope"] = CLAIM_SCOPE
        row["forbidden_interpretation"] = FORBIDDEN_INTERPRETATION
        row["source_checkpoint_path"] = str(source_checkpoint)
        row["repaired_checkpoint_path"] = str(repaired_checkpoint)
        row["repair_execution_started"] = True
        row["repaired_checkpoint_written"] = repaired_checkpoint.exists()
    return rows


def build_post_repair_protected_gate_evaluation_rows(
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
                "evaluation_status": status,
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


def build_summary(
    *,
    output_dir: Path,
    summary_path: Path,
    candidate_path: Path,
    gate_binding_path: Path,
    protected_rows_path: Path,
    source_checkpoint: Path,
    repaired_checkpoint: Path,
    candidate: dict[str, Any],
    candidate_hash: str,
    telemetry_summary: dict[str, Any],
    post_repair_rows: list[dict[str, Any]],
    gate_evaluation_rows: list[dict[str, Any]],
    repair_trace_rows: list[dict[str, Any]],
    checkpoint_manifest: dict[str, Any],
    candidate_snapshot_path: Path,
    repair_training_trace_path: Path,
    repaired_checkpoint_manifest_path: Path,
    post_repair_rows_path: Path,
    protected_gate_evaluation_path: Path,
    milestone: str,
    seed_count: int,
    horizon_steps: int,
) -> dict[str, Any]:
    required_artifacts_present = (
        candidate_snapshot_path.exists()
        and repair_training_trace_path.exists()
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
    proof_rows = [
        row
        for row in gate_evaluation_rows
        if row["gate_id"]
        in {"road_boundary_proof", "mitigation_proof", "command_conflict_proof"}
    ]
    proof_gates_all_passed = bool(proof_rows) and all(_as_bool(row["gate_pass"]) for row in proof_rows)
    proof_gate_fail_count = sum(not _as_bool(row["gate_pass"]) for row in proof_rows)
    proof_gate_pass_count = sum(_as_bool(row["gate_pass"]) for row in proof_rows)
    failed_gate_ids = [row["gate_id"] for row in proof_rows if not _as_bool(row["gate_pass"])]
    passed_gate_ids = [row["gate_id"] for row in gate_evaluation_rows if _as_bool(row["gate_pass"])]
    deferred_gate_count = sum(
        str(row["evaluation_status"]).startswith("deferred") for row in gate_evaluation_rows
    )
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
    )
    failure_types = {
        str(row["failure_type"])
        for row in gate_evaluation_rows
        if not _as_bool(row["gate_pass"]) and str(row["failure_type"]) not in {"", "none"}
    }
    if proof_gate_pass_count > 0 and proof_gate_fail_count > 0:
        failure_types.add("proof_washout")
    if not bool(checkpoint_manifest.get("finite_update")):
        failure_types.add("training_instability")

    same_three_proof_gates_failed = set(failed_gate_ids) == {
        "road_boundary_proof",
        "mitigation_proof",
        "command_conflict_proof",
    }
    next_blocker = (
        DEFAULT_PROOF_FAILURE_SYNTHESIS_BLOCKER
        if same_three_proof_gates_failed
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
        and repaired_checkpoint.exists()
        and bool(checkpoint_manifest.get("repaired_checkpoint_written"))
        and bool(checkpoint_manifest.get("behavior_changed"))
        and len(repair_trace_rows) >= 1
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
        "post_repair_all_proof_gates_passed"
        if status_pass and proof_gates_all_passed
        else "post_repair_partial_or_negative_proof_recorded"
        if status_pass
        else "guarded_repair_execution_incomplete"
    )
    return {
        "result_class": (
            "engineering_controller_failure_surface_guarded_repair_execution_pass"
            if status_pass
            else "engineering_controller_failure_surface_guarded_repair_execution_failed"
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
        "source_checkpoint": str(source_checkpoint),
        "repaired_checkpoint": str(repaired_checkpoint),
        "repair_training_trace": str(repair_training_trace_path),
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
        "telemetry_row_count": int(telemetry_summary.get("telemetry_row_count", 0)),
        "reset_count": int(telemetry_summary.get("reset_count", 0)),
        "repair_execution_started": True,
        "repair_training_started": True,
        "training_run": True,
        "repair_training_trace_row_count": len(repair_trace_rows),
        "repaired_checkpoint_written": bool(checkpoint_manifest.get("repaired_checkpoint_written")),
        "repaired_checkpoint_hash": checkpoint_manifest.get("repaired_checkpoint_hash", ""),
        "source_checkpoint_hash": checkpoint_manifest.get("source_checkpoint_hash", ""),
        "checkpoint_behavior_changed": bool(checkpoint_manifest.get("behavior_changed")),
        "post_repair_smoke_row_count": len(post_repair_rows),
        "protected_gate_evaluation_row_count": len(gate_evaluation_rows),
        "protected_row_match_count": sum(
            _as_bool(row["protected_row_matched"]) for row in post_repair_rows
        ),
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
        "protected_proof_gates_all_passed": bool(proof_gates_all_passed),
        "protected_proof_gate_pass_count": int(proof_gate_pass_count),
        "protected_proof_gate_fail_count": int(proof_gate_fail_count),
        "failed_proof_gate_ids": failed_gate_ids,
        "passed_gate_ids": passed_gate_ids,
        "same_three_proof_gates_failed_after_actual_repair": bool(same_three_proof_gates_failed),
        "same_failure_repeat_count_after_actual_repair": 3 if same_three_proof_gates_failed else 0,
        "deferred_gate_count": int(deferred_gate_count),
        "fresh_generalization_run": False,
        "failure_types_observed": sorted(failure_types),
        "claim_boundary": CLAIM_SCOPE,
        **FALSE_CLAIM_FLAGS,
    }


def _evaluate_post_repair_gate(
    gate_id: str,
    rows: list[dict[str, Any]],
) -> tuple[bool, str, str, int, int, int]:
    if gate_id == "contract_p0_72_3":
        gate_pass = (
            bool(rows)
            and _row_int_set(rows, "observation_shape") == {P0_OBSERVATION_DIM}
            and _row_int_set(rows, "action_shape") == {ACTION_DIM}
        )
        return gate_pass, "evaluated_contract", "none" if gate_pass else "contract_violation", 0, 0, 0
    if gate_id == "no_oracle_actor_inputs":
        gate_pass = bool(rows) and all(
            str(row["actor_input_leak_flags"]).lower() == "none"
            and not _as_bool(row["hidden_or_oracle_actor_inputs_required"])
            and not _as_bool(row["controller_mode_used"])
            and not _as_bool(row["mu_enter_actor_input"])
            for row in rows
        )
        return gate_pass, "evaluated_contract", "none" if gate_pass else "contract_violation", 0, 0, 0
    if gate_id == "road_boundary_proof":
        improved = sum(
            _float(row["road_margin_delta_m"]) > 1e-9
            and int(row["road_departure_delta"]) <= 0
            and not _as_bool(row["collision_regressed"])
            for row in rows
        )
        regressed = sum(
            _float(row["road_margin_delta_m"]) < -1e-9
            or int(row["road_departure_delta"]) > 0
            or _as_bool(row["collision_regressed"])
            for row in rows
        )
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_post_repair_pass" if gate_pass else "evaluated_post_repair_failed",
            "none" if gate_pass else "behavior_regression" if regressed else "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "mitigation_proof":
        improved = sum(
            _float(row["severity_delta"]) < -1e-9
            and _float(row["road_margin_delta_m"]) > 1e-9
            for row in rows
        )
        regressed = sum(
            _float(row["severity_delta"]) > 1e-9
            or _float(row["road_margin_delta_m"]) < -1e-9
            for row in rows
        )
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_post_repair_pass" if gate_pass else "evaluated_post_repair_failed",
            "none" if gate_pass else "behavior_regression" if regressed else "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "command_conflict_proof":
        improved = sum(_float(row["command_conflict_delta"]) < -1e-9 for row in rows)
        regressed = sum(_float(row["command_conflict_delta"]) > 1e-9 for row in rows)
        unchanged = max(0, len(rows) - improved - regressed)
        gate_pass = bool(rows) and improved == len(rows) and regressed == 0
        return (
            gate_pass,
            "evaluated_post_repair_pass" if gate_pass else "evaluated_post_repair_failed",
            "none" if gate_pass else "behavior_regression" if regressed else "objective_overfit",
            improved,
            regressed,
            unchanged,
        )
    if gate_id == "fresh_seed_generalization":
        return (
            False,
            "deferred_until_post_repair_proof_gate_success",
            "none",
            0,
            0,
            len(rows),
        )
    if gate_id == "no_ranking_no_success_rate":
        gate_pass = bool(rows) and all(
            not _as_bool(row["success_rate_field_emitted"])
            and not _as_bool(row["ranking_or_winner_field_emitted"])
            for row in rows
        )
        return gate_pass, "evaluated_claim_boundary", "none" if gate_pass else "metric_artifact", 0, 0, 0
    return False, "unknown_gate", "metric_artifact", 0, 0, len(rows)


def _next_route_if_fail(gate_id: str) -> str:
    return {
        "contract_p0_72_3": "contract repair before implementation",
        "no_oracle_actor_inputs": "design repair or branch synthesis",
        "road_boundary_proof": "guarded repair result audit or proof-failure synthesis",
        "mitigation_proof": "guarded repair result audit or proof-failure synthesis",
        "command_conflict_proof": "guarded repair result audit or proof-failure synthesis",
        "fresh_seed_generalization": "fresh-seed panel before promotion",
        "no_ranking_no_success_rate": "claim-boundary audit",
    }.get(gate_id, "guarded repair result audit")


def model_state_sha256(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _json_list(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(value):.9g}" for value in values) + "]"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the M2532 guarded source-only repair execution."
    )
    parser.add_argument("--candidate-config", type=Path, default=DEFAULT_CANDIDATE_CONFIG)
    parser.add_argument("--gate-bindings", type=Path, default=DEFAULT_GATE_BINDINGS)
    parser.add_argument("--protected-rows", type=Path, default=DEFAULT_PROTECTED_ROWS)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=100)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--throttle-bias-delta", type=float, default=-16.0)
    parser.add_argument("--brake-bias-delta", type=float, default=16.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_guarded_repair_execution(
        args.output_dir,
        candidate_config=args.candidate_config,
        gate_bindings=args.gate_bindings,
        protected_rows=args.protected_rows,
        checkpoint_path=args.checkpoint,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
        device=args.device,
        throttle_bias_delta=args.throttle_bias_delta,
        brake_bias_delta=args.brake_bias_delta,
    )
    print(
        "result_class={result_class} status_pass={status_pass} "
        "post_repair_outcome_class={post_repair_outcome_class} "
        "protected_proof_gate_fail_count={protected_proof_gate_fail_count} "
        "output_dir={output_dir}".format(**summary)
    )


if __name__ == "__main__":
    main()
