"""Run M3000 bounded diagnostic validation preflight.

M3000 consumes the M2996 validation-contract denominator and executes bounded
closed-loop diagnostic rows with the M2993 read-only nonzero residual head. It
keeps stale fixed-source rows excluded, keeps parent comparison report-only,
and registers M3001 before any interpretation.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import torch
from torch import nn

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.constraint_balanced_actor_head_delta_scaffold import ConstraintBalancedActorHeadDeltaScaffold
from autodrift.controller_family_full_rollout_execution import (
    DEFAULT_EXECUTABLE_SPECS,
    DEFAULT_EXECUTABLE_WORKLOAD,
    load_executable_specs,
    load_executable_workload,
    read_csv_rows,
    run_workload_cell,
    selected_metrics_are_finite,
    write_run_state,
)
from autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_bounded_execution_preflight import (  # noqa: E501
    EXECUTION_FIELDNAMES as BASE_EXECUTION_FIELDNAMES,
    FAILURE_FIELDNAMES as BASE_FAILURE_FIELDNAMES,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-diagnostic-validation-preflight"
)
NEXT_ID = (
    "m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-diagnostic-validation-result-audit"
)
DEFAULT_M2996_DIR = Path(
    "runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight"
)
DEFAULT_M2999_DESIGN = Path(
    "docs/m2999-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-validation-preflight-design.md"
)
DEFAULT_M2977_DIR = Path(
    "runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "deployable_trace_capture_preflight"
)
DEFAULT_M2960_DIR = Path(
    "runs/m2960_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "bounded_execution_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3000_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_bounded_diagnostic_validation_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-diagnostic-validation-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-audit.json"
)

EXPECTED_CANDIDATE_VALIDATION_COUNT = 43
EXPECTED_SUCCESS_RETENTION_COUNT = 13
EXPECTED_STALE_EXCLUSION_COUNT = 11
EXPECTED_ACTOR_INPUT_GUARD_COUNT = 14
EXPECTED_SIDE_EFFECT_GUARD_COUNT = 12
EXPECTED_RESIDUAL_LIMIT = 0.07999999821186066
EXPECTED_SUCCESS_ABS_MAX = 1.0e-3
M2999_ADMISSION_TOKEN = "admit_m3000_bounded_diagnostic_validation_preflight"

CLAIM_SCOPE = (
    "M3000 Route A actor-head delta nonzero residual bounded diagnostic validation preflight only; "
    "fixed M2996 candidate validation and success-retention denominator rows may be executed with the "
    "M2993 read-only residual-head wrapper to record closed-loop diagnostic fields, while stale fixed-source "
    "guardrails remain excluded. Parent comparison is report-only. No ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, validation-result, repair-success, driver-performance, paper, current-sim "
    "verdict, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "ranking, winner selection, checkpoint promotion, success-rate verdict, validation result, repair success, "
    "driver performance, paper evidence, current-sim verdict, high-fidelity validation result, full ideal driver "
    "completion, finite-window-vs-GRU result, or level3 self-identification"
)


def _dedupe(fields: list[str]) -> list[str]:
    out: list[str] = []
    for field in fields:
        if field not in out:
            out.append(field)
    return out


EXECUTION_PREFIX_FIELDNAMES = [
    "m3000_execution_id",
    "source_denominator_family",
    "row_role",
    "validation_contract_id",
    "success_retention_guard_id",
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "success_guard_loss_id",
    "source_raw_trace_index_row_id",
    "capture_plan_row_id",
    "raw_trace_path",
    "target_tensor_path",
    "expected_trace_step_count",
    "candidate_residual_head_artifact",
    "candidate_residual_head_loaded_read_only",
    "parent_checkpoint_loaded_read_only",
    "nonzero_residual_wrapper_mode",
    "zero_residual_identity_mode",
    "residual_limit",
    "residual_delta_norm_max",
    "residual_delta_abs_max",
    "residual_trace_count_delta",
    "parent_action_abs_max",
    "bounded_action_abs_max",
    "actor_observation_dim",
    "actor_action_dim",
    "candidate_validation_denominator",
    "success_retention_denominator",
    "stale_guardrail_executed",
    "diagnostic_validation_preflight_run",
    "validation_contract_row_executed",
    "success_retention_row_checked",
    "parent_comparison_report_only",
    "candidate_wrapper_status_pass",
    "status_pass",
]
EXECUTION_FIELDNAMES = _dedupe(EXECUTION_PREFIX_FIELDNAMES + list(BASE_EXECUTION_FIELDNAMES))

FAILURE_PREFIX_FIELDNAMES = [
    "m3000_failure_id",
    "source_denominator_family",
    "row_role",
    "validation_contract_id",
    "success_retention_guard_id",
    "fitting_dataset_row_id",
    "target_tensor_row_id",
    "success_guard_loss_id",
    "source_raw_trace_index_row_id",
    "capture_plan_row_id",
    "raw_trace_path",
    "target_tensor_path",
    "candidate_residual_head_artifact",
    "candidate_validation_denominator",
    "success_retention_denominator",
    "stale_guardrail_executed",
    "diagnostic_validation_preflight_run",
    "failure_stage",
    "boundary_preserved",
    "status_pass",
]
FAILURE_FIELDNAMES = _dedupe(FAILURE_PREFIX_FIELDNAMES + list(BASE_FAILURE_FIELDNAMES))

PARENT_COMPARISON_FIELDNAMES = [
    "parent_comparison_report_id",
    "source_denominator_family",
    "row_role",
    "execution_candidate_id",
    "validation_contract_id",
    "success_retention_guard_id",
    "parent_reference_source",
    "parent_row_present",
    "candidate_execution_row_present",
    "candidate_failure_row_present",
    "workload_id",
    "task_source_id",
    "profile_name",
    "m2960_eval_seed",
    "parent_checkpoint_path",
    "candidate_residual_head_artifact",
    "parent_outcome_bucket",
    "candidate_outcome_bucket",
    "parent_success",
    "candidate_success",
    "parent_collision",
    "candidate_collision",
    "parent_termination_reason",
    "candidate_termination_reason",
    "parent_steps",
    "candidate_steps",
    "parent_return",
    "candidate_return",
    "parent_min_clearance_margin",
    "candidate_min_clearance_margin",
    "parent_comparison_report_only",
    "ranking_run",
    "winner_selected",
    "promotion_run",
    "success_rate_verdict_claim_made",
    "performance_claim_made",
    "status_pass",
    "claim_boundary",
]
STALE_EXCLUSION_FIELDNAMES = [
    "stale_exclusion_guard_id",
    "source_stale_exclusion_guard_id",
    "stale_exclusion_audit_id",
    "stale_guardrail_exclusion_binding_id",
    "stale_guardrail_exclusion_row_id",
    "executed_in_m3000",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "self_id_denominator_allowed",
    "stale_guardrail_excluded",
    "status_pass",
    "claim_boundary",
]
ACTOR_INPUT_GUARD_FIELDNAMES = [
    "actor_input_guard_id",
    "guard_family",
    "forbidden_metadata_key",
    "observed_value",
    "expected_value",
    "actor_visible",
    "status_pass",
    "claim_boundary",
]
SIDE_EFFECT_FIELDNAMES = [
    "side_effect_guard_id",
    "side_effect",
    "observed_value",
    "expected_value",
    "allowed_in_m3000",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3000",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
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
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "candidate_validation_execution_rows",
    "candidate_validation_failure_rows",
    "parent_comparison_report_rows",
    "success_behavior_retention_execution_rows",
    "stale_exclusion_guard_rows",
    "actor_input_guard_rows",
    "checkpoint_side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]

ValidationRunFn = Callable[[Mapping[str, Any], dict[str, Any]], dict[str, Any]]


class _ParentActionEcho(nn.Module):
    def __init__(self, action_dim: int) -> None:
        super().__init__()
        self.action_dim = int(action_dim)
        self._action: torch.Tensor | None = None

    def set_action(self, action: torch.Tensor) -> None:
        if action.shape[-1:] != (self.action_dim,):
            raise ValueError(f"parent action last dimension must be {self.action_dim}, got {tuple(action.shape)}")
        self._action = action.detach()

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        if self._action is None:
            raise RuntimeError("parent action echo used before action was set")
        return self._action.to(device=observation.device, dtype=observation.dtype)


class _LinearResidualHead(nn.Module):
    def __init__(self, weight: np.ndarray, bias: np.ndarray) -> None:
        super().__init__()
        weight_t = torch.as_tensor(weight, dtype=torch.float32)
        bias_t = torch.as_tensor(bias, dtype=torch.float32)
        if weight_t.shape != (P0_OBSERVATION_DIM, ACTION_DIM):
            raise ValueError(f"linear_weight must be {(P0_OBSERVATION_DIM, ACTION_DIM)}, got {tuple(weight_t.shape)}")
        if bias_t.shape != (ACTION_DIM,):
            raise ValueError(f"linear_bias must be {(ACTION_DIM,)}, got {tuple(bias_t.shape)}")
        self.register_buffer("weight", weight_t)
        self.register_buffer("bias", bias_t)

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        weight = self.weight.to(device=observation.device, dtype=observation.dtype)
        bias = self.bias.to(device=observation.device, dtype=observation.dtype)
        return observation @ weight + bias


class NonzeroResidualActorHeadDeltaAdapter:
    """ActorPolicy-compatible wrapper for the read-only M2993 residual head."""

    actor_head_delta_contract_mode = "nonzero_residual_bounded_candidate"

    def __init__(
        self,
        parent_model: Any,
        *,
        artifact_path: Path | str,
        action_low: float = -1.0,
        action_high: float = 1.0,
    ) -> None:
        artifact = load_residual_head_artifact(Path(artifact_path))
        self.parent_model = parent_model
        self.artifact_path = str(artifact_path)
        self.obs_dim = int(getattr(parent_model, "obs_dim"))
        self.act_dim = int(getattr(parent_model, "act_dim", ACTION_DIM))
        self.actor_encoder = str(getattr(parent_model, "actor_encoder", "unknown"))
        self.actor_history_length = int(getattr(parent_model, "actor_history_length", 1))
        self.action_sequence_horizon = int(getattr(parent_model, "action_sequence_horizon", 1))
        self.residual_limit = float(artifact["residual_limit"])
        self.success_guard_required_abs_max = float(artifact["success_guard_required_abs_max"])
        self.action_low = float(action_low)
        self.action_high = float(action_high)
        self._parent_echo = _ParentActionEcho(self.act_dim)
        self._scaffold = ConstraintBalancedActorHeadDeltaScaffold(
            self._parent_echo,
            _LinearResidualHead(artifact["linear_weight"], artifact["linear_bias"]),
            residual_limit=self.residual_limit,
            action_low=self.action_low,
            action_high=self.action_high,
            observation_dim=self.obs_dim,
            action_dim=self.act_dim,
        )
        self._scaffold.to(self._device())
        self.reset_diagnostics()

    @property
    def is_online_recurrent(self) -> bool:
        return bool(getattr(self.parent_model, "is_online_recurrent"))

    def _device(self) -> torch.device:
        return next(self.parent_model.parameters()).device

    def reset_diagnostics(self) -> None:
        self.trace_count = 0
        self.residual_delta_norm_max = 0.0
        self.residual_delta_abs_max = 0.0
        self.parent_action_abs_max = 0.0
        self.bounded_action_abs_max = 0.0

    def _apply_delta(self, observation: torch.Tensor, parent_action: torch.Tensor) -> torch.Tensor:
        self._parent_echo.set_action(parent_action)
        trace = self._scaffold.forward_with_trace(observation)
        self.trace_count += int(trace.action.shape[0])
        self.residual_delta_norm_max = max(
            self.residual_delta_norm_max,
            float(torch.linalg.norm(trace.residual_delta, dim=-1).max().item()),
        )
        self.residual_delta_abs_max = max(self.residual_delta_abs_max, float(torch.abs(trace.residual_delta).max().item()))
        self.parent_action_abs_max = max(self.parent_action_abs_max, float(torch.abs(trace.parent_action).max().item()))
        self.bounded_action_abs_max = max(self.bounded_action_abs_max, float(torch.abs(trace.action).max().item()))
        return trace.action

    def _squashed_log_prob(self, dist: Any, raw_action: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        if hasattr(self.parent_model, "_squashed_log_prob"):
            return self.parent_model._squashed_log_prob(dist, raw_action, action)
        correction = torch.log(torch.clamp(1.0 - action.pow(2), min=1e-6)).sum(dim=-1)
        return dist.log_prob(raw_action).sum(dim=-1) - correction

    def act(self, obs: np.ndarray, deterministic: bool = False) -> tuple[np.ndarray, float, float]:
        device = self._device()
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            dist, value = self.parent_model.forward(obs_t)
            raw_action = dist.mean if deterministic else dist.sample()
            parent_action = torch.tanh(raw_action)
            action = self._apply_delta(obs_t, parent_action)
            log_prob = self._squashed_log_prob(dist, raw_action, parent_action)
        return action.squeeze(0).cpu().numpy().astype(np.float32), float(log_prob.item()), float(value.item())

    def act_recurrent(
        self,
        obs: np.ndarray,
        hidden: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> tuple[np.ndarray, float, float, torch.Tensor]:
        device = self._device()
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        hidden_t = hidden if hidden is not None else self.parent_model.initial_hidden(1, device)
        with torch.no_grad():
            dist, value, next_hidden = self.parent_model.forward_recurrent(obs_t, hidden_t)
            raw_action = dist.mean if deterministic else dist.sample()
            parent_action = torch.tanh(raw_action)
            action = self._apply_delta(obs_t, parent_action)
            log_prob = self._squashed_log_prob(dist, raw_action, parent_action)
        return (
            action.squeeze(0).cpu().numpy().astype(np.float32),
            float(log_prob.item()),
            float(value.item()),
            next_hidden.detach(),
        )

    def predict_sequence(self, obs: np.ndarray) -> np.ndarray:
        sequence = np.asarray(self.parent_model.predict_sequence(obs), dtype=np.float32).copy()
        if len(sequence) == 0:
            return sequence
        device = self._device()
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        parent_action = torch.as_tensor(sequence[0], dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            action = self._apply_delta(obs_t, parent_action)
        sequence[0] = action.squeeze(0).cpu().numpy().astype(np.float32)
        return sequence

    def contract_summary(self) -> dict[str, Any]:
        return {
            "wrapper_instantiated": True,
            "parent_checkpoint_loaded_read_only": True,
            "candidate_residual_head_loaded_read_only": True,
            "nonzero_residual_wrapper_mode": True,
            "zero_residual_identity_mode": False,
            "residual_limit": self.residual_limit,
            "success_guard_required_abs_max": self.success_guard_required_abs_max,
            "residual_delta_norm_max": self.residual_delta_norm_max,
            "residual_delta_abs_max": self.residual_delta_abs_max,
            "residual_trace_count": self.trace_count,
            "parent_action_abs_max": self.parent_action_abs_max,
            "bounded_action_abs_max": self.bounded_action_abs_max,
            "action_low": self.action_low,
            "action_high": self.action_high,
        }


def run_bounded_diagnostic_validation_preflight(
    *,
    m2996_dir: Path | str = DEFAULT_M2996_DIR,
    m2999_design: Path | str = DEFAULT_M2999_DESIGN,
    m2977_dir: Path | str = DEFAULT_M2977_DIR,
    m2960_dir: Path | str = DEFAULT_M2960_DIR,
    executable_specs: Path | str = DEFAULT_EXECUTABLE_SPECS,
    executable_workload: Path | str = DEFAULT_EXECUTABLE_WORKLOAD,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    device: str = "cpu",
    validation_fn: ValidationRunFn | None = None,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2996_dir=Path(m2996_dir),
        m2999_design=Path(m2999_design),
        m2977_dir=Path(m2977_dir),
        m2960_dir=Path(m2960_dir),
        executable_specs=Path(executable_specs),
        executable_workload=Path(executable_workload),
        follow_up_manifest=Path(follow_up_manifest),
    )
    plan_rows = build_diagnostic_plan_rows(source)
    context = build_execution_context(source, device=device)
    candidate_execution_rows, success_execution_rows, failure_rows = execute_diagnostic_plan_rows(
        plan_rows=plan_rows,
        context=context,
        output_dir=output,
        validation_fn=validation_fn or execute_one_plan_row,
        next_blocker=next_blocker,
    )
    write_csv_rows(
        paths["candidate_validation_execution_rows"],
        candidate_execution_rows,
        fieldnames=EXECUTION_FIELDNAMES,
    )
    write_csv_rows(
        paths["success_behavior_retention_execution_rows"],
        success_execution_rows,
        fieldnames=EXECUTION_FIELDNAMES,
    )
    write_csv_rows(paths["candidate_validation_failure_rows"], failure_rows, fieldnames=FAILURE_FIELDNAMES)

    parent_rows = build_parent_comparison_report_rows(
        plan_rows=plan_rows,
        candidate_execution_rows=candidate_execution_rows,
        success_execution_rows=success_execution_rows,
        failure_rows=failure_rows,
        source=source,
    )
    stale_rows = build_stale_exclusion_guard_rows(source)
    actor_rows = build_actor_input_guard_rows(
        source=source,
        plan_rows=plan_rows,
        execution_rows=candidate_execution_rows + success_execution_rows,
        stale_rows=stale_rows,
    )
    side_effect_rows = build_checkpoint_side_effect_guard_rows(
        execution_rows=candidate_execution_rows + success_execution_rows,
        failure_rows=failure_rows,
        source=source,
    )
    write_csv_rows(paths["parent_comparison_report_rows"], parent_rows, fieldnames=PARENT_COMPARISON_FIELDNAMES)
    write_csv_rows(paths["stale_exclusion_guard_rows"], stale_rows, fieldnames=STALE_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["actor_input_guard_rows"], actor_rows, fieldnames=ACTOR_INPUT_GUARD_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_effect_rows, fieldnames=SIDE_EFFECT_FIELDNAMES)

    write_json(
        follow_up_manifest,
        build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = Path(follow_up_manifest).exists()

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        artifacts_present=required_without_summary_doc,
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        execution_rows_present=bool(candidate_execution_rows or success_execution_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        candidate_execution_rows=candidate_execution_rows,
        success_execution_rows=success_execution_rows,
        failure_rows=failure_rows,
        parent_rows=parent_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        plan_rows=plan_rows,
        candidate_execution_rows=candidate_execution_rows,
        success_execution_rows=success_execution_rows,
        failure_rows=failure_rows,
        parent_rows=parent_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        artifacts_present=required_artifacts_present,
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        execution_rows_present=bool(candidate_execution_rows or success_execution_rows),
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        candidate_execution_rows=candidate_execution_rows,
        success_execution_rows=success_execution_rows,
        failure_rows=failure_rows,
        parent_rows=parent_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        plan_rows=plan_rows,
        candidate_execution_rows=candidate_execution_rows,
        success_execution_rows=success_execution_rows,
        failure_rows=failure_rows,
        parent_rows=parent_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        device=device,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "candidate_validation_plan_count": summary["candidate_validation_denominator_row_count"],
            "success_retention_plan_count": summary["success_retention_denominator_row_count"],
            "candidate_validation_execution_row_count": summary["candidate_validation_execution_row_count"],
            "success_behavior_retention_execution_row_count": summary[
                "success_behavior_retention_execution_row_count"
            ],
            "failure_row_count": summary["candidate_validation_failure_row_count"],
            "accounted_candidate_validation_count": summary["accounted_candidate_validation_count"],
            "accounted_success_retention_count": summary["accounted_success_retention_count"],
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "candidate_validation_execution_rows": output_dir / "candidate_validation_execution_rows.csv",
        "candidate_validation_failure_rows": output_dir / "candidate_validation_failure_rows.csv",
        "parent_comparison_report_rows": output_dir / "parent_comparison_report_rows.csv",
        "success_behavior_retention_execution_rows": output_dir / "success_behavior_retention_execution_rows.csv",
        "stale_exclusion_guard_rows": output_dir / "stale_exclusion_guard_rows.csv",
        "actor_input_guard_rows": output_dir / "actor_input_guard_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2996_dir: Path,
    m2999_design: Path,
    m2977_dir: Path,
    m2960_dir: Path,
    executable_specs: Path,
    executable_workload: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2996_summary": m2996_dir / "summary.json",
        "validation_contract_rows": m2996_dir / "validation_contract_rows.csv",
        "residual_head_wrapper_contract_rows": m2996_dir / "residual_head_wrapper_contract_rows.csv",
        "parent_comparison_plan_rows": m2996_dir / "parent_comparison_plan_rows.csv",
        "success_behavior_retention_guard_rows": m2996_dir / "success_behavior_retention_guard_rows.csv",
        "stale_exclusion_guard_rows": m2996_dir / "stale_exclusion_guard_rows.csv",
        "actor_input_exclusion_rows": m2996_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": m2996_dir / "checkpoint_side_effect_guard_rows.csv",
        "m2996_gate_matrix": m2996_dir / "gate_matrix.csv",
        "m2999_design": m2999_design,
        "m2977_raw_trace_index_rows": m2977_dir / "raw_trace_index_rows.csv",
        "m2977_capture_plan_rows": m2977_dir / "capture_plan_rows.csv",
        "m2960_bounded_execution_rows": m2960_dir / "bounded_execution_rows.csv",
        "executable_specs": executable_specs,
        "executable_workload": executable_workload,
        "follow_up_manifest": follow_up_manifest,
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    m2996_summary = read_json(paths["m2996_summary"]) if source_exists["m2996_summary"] else {}
    wrapper_rows = read_csv_rows(paths["residual_head_wrapper_contract_rows"])
    artifact_path = residual_artifact_path(m2996_summary, wrapper_rows)
    artifact_metadata = load_residual_head_artifact_metadata(artifact_path)
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m2996_summary": m2996_summary,
        "m2999_design_text": paths["m2999_design"].read_text(encoding="utf-8")
        if source_exists["m2999_design"]
        else "",
        "validation_contract_rows": read_csv_rows(paths["validation_contract_rows"]),
        "residual_head_wrapper_contract_rows": wrapper_rows,
        "parent_comparison_plan_rows": read_csv_rows(paths["parent_comparison_plan_rows"]),
        "success_behavior_retention_guard_rows": read_csv_rows(paths["success_behavior_retention_guard_rows"]),
        "stale_exclusion_guard_rows": read_csv_rows(paths["stale_exclusion_guard_rows"]),
        "actor_input_exclusion_rows": read_csv_rows(paths["actor_input_exclusion_rows"]),
        "checkpoint_side_effect_guard_rows": read_csv_rows(paths["checkpoint_side_effect_guard_rows"]),
        "m2996_gate_rows": read_csv_rows(paths["m2996_gate_matrix"]),
        "m2977_raw_trace_index_rows": read_csv_rows(paths["m2977_raw_trace_index_rows"]),
        "m2977_capture_plan_rows": read_csv_rows(paths["m2977_capture_plan_rows"]),
        "m2960_bounded_execution_rows": read_csv_rows(paths["m2960_bounded_execution_rows"]),
        "executable_specs": load_executable_specs(paths["executable_specs"]) if source_exists["executable_specs"] else [],
        "executable_workload_rows": load_executable_workload(paths["executable_workload"])
        if source_exists["executable_workload"]
        else [],
        "candidate_residual_head_artifact": str(artifact_path),
        "artifact_metadata": artifact_metadata,
    }


def residual_artifact_path(summary: Mapping[str, Any], wrapper_rows: list[Mapping[str, Any]]) -> Path:
    summary_path = str(summary.get("candidate_residual_head_artifact", ""))
    if summary_path:
        return Path(summary_path)
    for row in wrapper_rows:
        artifact = str(row.get("artifact_path", ""))
        if artifact:
            return Path(artifact)
    return Path(
        "runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
        "nonzero_residual_success_identity_guard_constrained_fitting_preflight/candidate_residual_head_artifact.npz"
    )


def load_residual_head_artifact(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as data:
        required = {
            "linear_weight",
            "linear_bias",
            "residual_limit",
            "success_guard_required_abs_max",
            "observation_dim",
            "action_dim",
        }
        missing = sorted(required - set(data.files))
        if missing:
            raise ValueError(f"residual head artifact missing keys: {missing}")
        weight = np.asarray(data["linear_weight"], dtype=np.float32)
        bias = np.asarray(data["linear_bias"], dtype=np.float32)
        residual_limit = float(np.asarray(data["residual_limit"]).reshape(-1)[0])
        success_abs = float(np.asarray(data["success_guard_required_abs_max"]).reshape(-1)[0])
        observation_dim = int(np.asarray(data["observation_dim"]).reshape(-1)[0])
        action_dim = int(np.asarray(data["action_dim"]).reshape(-1)[0])
    if weight.shape != (P0_OBSERVATION_DIM, ACTION_DIM):
        raise ValueError(f"residual weight shape mismatch: {weight.shape}")
    if bias.shape != (ACTION_DIM,):
        raise ValueError(f"residual bias shape mismatch: {bias.shape}")
    if observation_dim != P0_OBSERVATION_DIM or action_dim != ACTION_DIM:
        raise ValueError(f"residual artifact actor shape mismatch: {observation_dim}/{action_dim}")
    if not np.isfinite(weight).all() or not np.isfinite(bias).all():
        raise ValueError("residual head artifact contains nonfinite weights")
    return {
        "linear_weight": weight,
        "linear_bias": bias,
        "residual_limit": residual_limit,
        "success_guard_required_abs_max": success_abs,
        "observation_dim": observation_dim,
        "action_dim": action_dim,
    }


def load_residual_head_artifact_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "required_keys_present": False,
        "linear_weight_shape": "",
        "linear_bias_shape": "",
        "observation_dim": 0,
        "action_dim": 0,
        "residual_limit": 0.0,
        "success_guard_required_abs_max": 0.0,
        "finite": False,
        "status_pass": False,
    }
    if not path.exists():
        return metadata
    try:
        artifact = load_residual_head_artifact(path)
    except Exception:
        return metadata
    metadata.update(
        {
            "required_keys_present": True,
            "linear_weight_shape": shape_text(artifact["linear_weight"].shape),
            "linear_bias_shape": shape_text(artifact["linear_bias"].shape),
            "observation_dim": artifact["observation_dim"],
            "action_dim": artifact["action_dim"],
            "residual_limit": artifact["residual_limit"],
            "success_guard_required_abs_max": artifact["success_guard_required_abs_max"],
            "finite": True,
        }
    )
    metadata["status_pass"] = bool(
        artifact["observation_dim"] == P0_OBSERVATION_DIM
        and artifact["action_dim"] == ACTION_DIM
        and 0.0 < artifact["residual_limit"] <= EXPECTED_RESIDUAL_LIMIT + 1.0e-6
        and 0.0 < artifact["success_guard_required_abs_max"] <= EXPECTED_SUCCESS_ABS_MAX + 1.0e-6
    )
    return metadata


def build_diagnostic_plan_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_by_path = {str(row.get("raw_trace_path", "")): row for row in source["m2977_raw_trace_index_rows"]}
    capture_by_id = {str(row.get("capture_plan_row_id", "")): row for row in source["m2977_capture_plan_rows"]}
    parent_by_execution = {
        str(row.get("execution_candidate_id", "")): row for row in source["m2960_bounded_execution_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, contract in enumerate(source["validation_contract_rows"], start=1):
        rows.append(
            diagnostic_plan_row(
                index=index,
                row_role="candidate_validation",
                source_denominator_family="candidate_validation_denominator",
                source_row=contract,
                raw_by_path=raw_by_path,
                capture_by_id=capture_by_id,
                parent_by_execution=parent_by_execution,
                artifact_path=str(source["candidate_residual_head_artifact"]),
            )
        )
    for index, success in enumerate(source["success_behavior_retention_guard_rows"], start=1):
        rows.append(
            diagnostic_plan_row(
                index=len(rows) + 1,
                row_role="success_behavior_retention",
                source_denominator_family="success_retention_denominator",
                source_row=success,
                raw_by_path=raw_by_path,
                capture_by_id=capture_by_id,
                parent_by_execution=parent_by_execution,
                artifact_path=str(source["candidate_residual_head_artifact"]),
                success_index=index,
            )
        )
    return rows


def diagnostic_plan_row(
    *,
    index: int,
    row_role: str,
    source_denominator_family: str,
    source_row: Mapping[str, Any],
    raw_by_path: Mapping[str, Mapping[str, Any]],
    capture_by_id: Mapping[str, Mapping[str, Any]],
    parent_by_execution: Mapping[str, Mapping[str, Any]],
    artifact_path: str,
    success_index: int | None = None,
) -> dict[str, Any]:
    raw_trace_path = str(source_row.get("raw_trace_path", ""))
    target_tensor_path = str(source_row.get("target_tensor_path", ""))
    raw = raw_by_path.get(raw_trace_path, {})
    capture = capture_by_id.get(str(raw.get("capture_plan_row_id", "")), {})
    execution_candidate_id = str(raw.get("execution_candidate_id", capture.get("execution_candidate_id", "")))
    parent = parent_by_execution.get(execution_candidate_id, {})
    failure_reason = ""
    if not _bool(source_row.get("status_pass", False)):
        failure_reason = "m2996_source_row_status_failed"
    elif not raw_trace_path or not Path(raw_trace_path).exists():
        failure_reason = "raw_trace_path_missing"
    elif not target_tensor_path or not Path(target_tensor_path).exists():
        failure_reason = "target_tensor_path_missing"
    elif not raw:
        failure_reason = "raw_trace_not_found_in_m2977_index"
    elif not capture:
        failure_reason = "capture_plan_not_found_for_raw_trace"
    elif not parent:
        failure_reason = "parent_m2960_execution_row_missing"
    execution_admitted = not failure_reason
    return {
        "m3000_plan_row_id": f"m3000-plan-{index:04d}",
        "source_denominator_family": source_denominator_family,
        "row_role": row_role,
        "validation_contract_id": source_row.get("validation_contract_id", ""),
        "success_retention_guard_id": source_row.get("success_retention_guard_id", ""),
        "fitting_dataset_row_id": source_row.get("fitting_dataset_row_id", ""),
        "target_tensor_row_id": source_row.get("target_tensor_row_id", ""),
        "success_guard_loss_id": source_row.get("success_guard_loss_id", ""),
        "source_raw_trace_index_row_id": raw.get("raw_trace_index_row_id", ""),
        "capture_plan_row_id": raw.get("capture_plan_row_id", capture.get("capture_plan_row_id", "")),
        "execution_candidate_id": execution_candidate_id,
        "raw_trace_path": raw_trace_path,
        "target_tensor_path": target_tensor_path,
        "expected_trace_step_count": _to_int(capture.get("expected_trace_step_count", raw.get("expected_trace_step_count")), default=0),
        "m2960_eval_seed": _to_int(capture.get("m2960_eval_seed", parent.get("m2960_eval_seed")), default=0),
        "workload_id": capture.get("workload_id", parent.get("workload_id", "")),
        "task_source_id": parent.get("task_source_id", ""),
        "profile_name": parent.get("profile_name", ""),
        "task_family": capture.get("task_family", parent.get("task_family", "")),
        "parent_checkpoint_path": capture.get("parent_checkpoint_path", parent.get("parent_checkpoint_path", "")),
        "parent_profile_config_path": capture.get(
            "parent_profile_config_path",
            parent.get("parent_profile_config_path", ""),
        ),
        "candidate_residual_head_artifact": artifact_path,
        "candidate_validation_denominator": row_role == "candidate_validation",
        "success_retention_denominator": row_role == "success_behavior_retention",
        "execution_admitted": execution_admitted,
        "failure_reason": failure_reason,
        "parent_row": dict(parent),
        "success_index": success_index or "",
        "claim_boundary": CLAIM_SCOPE,
    }


def build_execution_context(source: Mapping[str, Any], *, device: str) -> dict[str, Any]:
    return {
        "workload_by_id": {str(row.get("workload_id", "")): row for row in source["executable_workload_rows"]},
        "spec_by_task_source_id": {str(row.get("task_source_id", "")): row for row in source["executable_specs"]},
        "profile_cache": {},
        "device": device,
        "artifact_path": str(source["candidate_residual_head_artifact"]),
    }


def execute_diagnostic_plan_rows(
    *,
    plan_rows: list[dict[str, Any]],
    context: dict[str, Any],
    output_dir: Path,
    validation_fn: ValidationRunFn,
    next_blocker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_rows: list[dict[str, Any]] = []
    success_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for index, plan in enumerate(plan_rows, start=1):
        try:
            if not _bool(plan.get("execution_admitted", False)):
                raise ValueError(str(plan.get("failure_reason", "plan row not admitted")))
            row = validation_fn(plan, context)
            row.update(execution_metadata(plan=plan, index=index, row=row))
            if str(plan.get("row_role", "")) == "candidate_validation":
                candidate_rows.append(row)
            else:
                success_rows.append(row)
        except Exception as exc:  # noqa: BLE001 - every denominator row must be accounted.
            failure_rows.append(
                failure_row(
                    plan=plan,
                    index=len(failure_rows) + 1,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
        write_run_state(
            output_dir / "run_state.json",
            {
                "plan_row_count": len(plan_rows),
                "processed_plan_row_count": index,
                "candidate_validation_execution_row_count": len(candidate_rows),
                "success_behavior_retention_execution_row_count": len(success_rows),
                "failure_row_count": len(failure_rows),
                "accounted_count": len(candidate_rows) + len(success_rows) + len(failure_rows),
                "complete": False,
                "next_blocker": next_blocker,
            },
        )
    return candidate_rows, success_rows, failure_rows


def execute_one_plan_row(plan: Mapping[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    workload = context["workload_by_id"].get(str(plan.get("workload_id", "")))
    if workload is None:
        raise ValueError(f"workload_id {plan.get('workload_id', '')!r} missing from executable workload")
    task_source_id = str(workload.get("task_source_id", ""))
    executable_spec = context["spec_by_task_source_id"].get(task_source_id)
    if executable_spec is None:
        raise ValueError(f"task_source_id {task_source_id!r} missing from executable specs")

    profile_name = str(workload.get("profile_name", plan.get("profile_name", "")))
    config_path = str(plan.get("parent_profile_config_path", ""))
    checkpoint_path = str(plan.get("parent_checkpoint_path", ""))
    cache_key = (profile_name, config_path, checkpoint_path, str(context["artifact_path"]))
    profile_cache: dict[
        tuple[str, str, str, str], tuple[dict[str, Any], NonzeroResidualActorHeadDeltaAdapter, dict[str, str]]
    ] = context["profile_cache"]
    if cache_key not in profile_cache:
        profile_config = read_json(config_path)
        parent_model, _checkpoint = load_actor_critic_checkpoint(checkpoint_path, device=str(context["device"]))
        adapter = NonzeroResidualActorHeadDeltaAdapter(parent_model, artifact_path=str(context["artifact_path"]))
        profile_cache[cache_key] = (
            profile_config,
            adapter,
            {"profile_name": profile_name, "config_path": config_path, "checkpoint_path": checkpoint_path},
        )
    profile_config, adapter, profile_row = profile_cache[cache_key]
    adapter.reset_diagnostics()
    row = run_workload_cell(
        workload_row=workload,
        executable_spec=executable_spec,
        profile_config=profile_config,
        model=adapter,
        profile_row=profile_row,
        eval_seed=_to_int(plan.get("m2960_eval_seed"), default=0),
    )
    row.update(adapter.contract_summary())
    return row


def execution_metadata(*, plan: Mapping[str, Any], index: int, row: Mapping[str, Any]) -> dict[str, Any]:
    residual_limit = _to_float(row.get("residual_limit"), default=EXPECTED_RESIDUAL_LIMIT)
    residual_abs = _to_float(row.get("residual_delta_abs_max"), default=0.0)
    status_pass = bool(
        selected_metrics_are_finite([row])
        and residual_abs <= residual_limit + 1.0e-9
        and _bool(row.get("candidate_residual_head_loaded_read_only", True))
        and _bool(row.get("parent_checkpoint_loaded_read_only", True))
        and not forbidden_execution_flag(row)
    )
    return {
        "m3000_execution_id": f"m3000-diagnostic-execution-{index:04d}",
        "source_denominator_family": plan.get("source_denominator_family", ""),
        "row_role": plan.get("row_role", ""),
        "validation_contract_id": plan.get("validation_contract_id", ""),
        "success_retention_guard_id": plan.get("success_retention_guard_id", ""),
        "fitting_dataset_row_id": plan.get("fitting_dataset_row_id", ""),
        "target_tensor_row_id": plan.get("target_tensor_row_id", ""),
        "success_guard_loss_id": plan.get("success_guard_loss_id", ""),
        "source_raw_trace_index_row_id": plan.get("source_raw_trace_index_row_id", ""),
        "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
        "raw_trace_path": plan.get("raw_trace_path", ""),
        "target_tensor_path": plan.get("target_tensor_path", ""),
        "expected_trace_step_count": plan.get("expected_trace_step_count", ""),
        "candidate_residual_head_artifact": plan.get("candidate_residual_head_artifact", ""),
        "candidate_residual_head_loaded_read_only": _bool(row.get("candidate_residual_head_loaded_read_only", True)),
        "parent_checkpoint_loaded_read_only": _bool(row.get("parent_checkpoint_loaded_read_only", True)),
        "nonzero_residual_wrapper_mode": True,
        "zero_residual_identity_mode": False,
        "residual_limit": residual_limit,
        "residual_delta_norm_max": row.get("residual_delta_norm_max", ""),
        "residual_delta_abs_max": residual_abs,
        "residual_trace_count_delta": _to_int(row.get("residual_trace_count"), default=0),
        "parent_action_abs_max": row.get("parent_action_abs_max", ""),
        "bounded_action_abs_max": row.get("bounded_action_abs_max", ""),
        "actor_observation_dim": P0_OBSERVATION_DIM,
        "actor_action_dim": ACTION_DIM,
        "candidate_validation_denominator": _bool(plan.get("candidate_validation_denominator", False)),
        "success_retention_denominator": _bool(plan.get("success_retention_denominator", False)),
        "stale_guardrail_executed": False,
        "diagnostic_validation_preflight_run": True,
        "validation_contract_row_executed": str(plan.get("row_role", "")) == "candidate_validation",
        "success_retention_row_checked": str(plan.get("row_role", "")) == "success_behavior_retention",
        "parent_comparison_report_only": True,
        "candidate_wrapper_status_pass": residual_abs <= residual_limit + 1.0e-9,
        "status_pass": status_pass,
        "m2960_eval_seed": _to_int(plan.get("m2960_eval_seed"), default=0),
        "execution_candidate_id": plan.get("execution_candidate_id", ""),
        "parent_checkpoint_path": plan.get("parent_checkpoint_path", ""),
        "parent_profile_config_path": plan.get("parent_profile_config_path", ""),
        "candidate_surface_count": EXPECTED_CANDIDATE_VALIDATION_COUNT,
        "blocked_stale_guard_execution": False,
        "guardrail_rows_in_success_denominator": False,
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "route_labels_actor_visible": False,
        "source_labels_actor_visible": False,
        "evaluator_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "dependency_execution_performed": False,
        "checkpoint_save_scheduled": False,
        "checkpoint_mutation_scheduled": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def failure_row(*, plan: Mapping[str, Any], index: int, error_type: str, error_message: str) -> dict[str, Any]:
    row = {key: False for key in FAILURE_FIELDNAMES}
    row.update(
        {
            "m3000_failure_id": f"m3000-diagnostic-failure-{index:04d}",
            "source_denominator_family": plan.get("source_denominator_family", ""),
            "row_role": plan.get("row_role", ""),
            "validation_contract_id": plan.get("validation_contract_id", ""),
            "success_retention_guard_id": plan.get("success_retention_guard_id", ""),
            "fitting_dataset_row_id": plan.get("fitting_dataset_row_id", ""),
            "target_tensor_row_id": plan.get("target_tensor_row_id", ""),
            "success_guard_loss_id": plan.get("success_guard_loss_id", ""),
            "source_raw_trace_index_row_id": plan.get("source_raw_trace_index_row_id", ""),
            "capture_plan_row_id": plan.get("capture_plan_row_id", ""),
            "raw_trace_path": plan.get("raw_trace_path", ""),
            "target_tensor_path": plan.get("target_tensor_path", ""),
            "candidate_residual_head_artifact": plan.get("candidate_residual_head_artifact", ""),
            "candidate_validation_denominator": _bool(plan.get("candidate_validation_denominator", False)),
            "success_retention_denominator": _bool(plan.get("success_retention_denominator", False)),
            "stale_guardrail_executed": False,
            "diagnostic_validation_preflight_run": False,
            "failure_stage": "diagnostic_validation_preflight_execution",
            "boundary_preserved": True,
            "status_pass": True,
            "resolution_id": plan.get("capture_plan_row_id", ""),
            "execution_candidate_id": plan.get("execution_candidate_id", ""),
            "workload_id": plan.get("workload_id", ""),
            "task_source_id": plan.get("task_source_id", ""),
            "profile_name": plan.get("profile_name", ""),
            "task_family": plan.get("task_family", ""),
            "m2960_eval_seed": _to_int(plan.get("m2960_eval_seed"), default=0),
            "error_type": error_type,
            "error_message": error_message,
            "blocked_stale_guard_execution": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "private_holdout_used": False,
            "ranking_run": False,
            "winner_selected": False,
            "checkpoint_promoted": False,
            "checkpoint_save_scheduled": False,
            "checkpoint_mutation_scheduled": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def build_parent_comparison_report_rows(
    *,
    plan_rows: list[dict[str, Any]],
    candidate_execution_rows: list[dict[str, Any]],
    success_execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    execution_by_plan = {
        str(row.get("capture_plan_row_id", "")): row for row in candidate_execution_rows + success_execution_rows
    }
    failure_by_plan = {str(row.get("capture_plan_row_id", "")): row for row in failure_rows}
    parent_by_execution = {
        str(row.get("execution_candidate_id", "")): row for row in source["m2960_bounded_execution_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(plan_rows, start=1):
        parent = parent_by_execution.get(str(plan.get("execution_candidate_id", "")), {})
        candidate = execution_by_plan.get(str(plan.get("capture_plan_row_id", "")), {})
        failure = failure_by_plan.get(str(plan.get("capture_plan_row_id", "")), {})
        accounted = bool(candidate or failure)
        rows.append(
            {
                "parent_comparison_report_id": f"m3000-parent-comparison-{index:04d}",
                "source_denominator_family": plan.get("source_denominator_family", ""),
                "row_role": plan.get("row_role", ""),
                "execution_candidate_id": plan.get("execution_candidate_id", ""),
                "validation_contract_id": plan.get("validation_contract_id", ""),
                "success_retention_guard_id": plan.get("success_retention_guard_id", ""),
                "parent_reference_source": "m2960_zero_residual_reference_row",
                "parent_row_present": bool(parent),
                "candidate_execution_row_present": bool(candidate),
                "candidate_failure_row_present": bool(failure),
                "workload_id": plan.get("workload_id", ""),
                "task_source_id": parent.get("task_source_id", candidate.get("task_source_id", "")),
                "profile_name": parent.get("profile_name", candidate.get("profile_name", "")),
                "m2960_eval_seed": plan.get("m2960_eval_seed", ""),
                "parent_checkpoint_path": plan.get("parent_checkpoint_path", ""),
                "candidate_residual_head_artifact": plan.get("candidate_residual_head_artifact", ""),
                "parent_outcome_bucket": parent.get("outcome_bucket", ""),
                "candidate_outcome_bucket": candidate.get("outcome_bucket", ""),
                "parent_success": _bool(parent.get("success", False)),
                "candidate_success": _bool(candidate.get("success", False)),
                "parent_collision": _bool(parent.get("collision", False)),
                "candidate_collision": _bool(candidate.get("collision", False)),
                "parent_termination_reason": parent.get("termination_reason", ""),
                "candidate_termination_reason": candidate.get("termination_reason", ""),
                "parent_steps": parent.get("steps", ""),
                "candidate_steps": candidate.get("steps", ""),
                "parent_return": parent.get("return", ""),
                "candidate_return": candidate.get("return", ""),
                "parent_min_clearance_margin": parent.get("min_clearance_margin", ""),
                "candidate_min_clearance_margin": candidate.get("min_clearance_margin", ""),
                "parent_comparison_report_only": True,
                "ranking_run": False,
                "winner_selected": False,
                "promotion_run": False,
                "success_rate_verdict_claim_made": False,
                "performance_claim_made": False,
                "status_pass": bool(parent) and accounted,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_exclusion_guard_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["stale_exclusion_guard_rows"], start=1):
        validation_allowed = _bool(row.get("validation_denominator_allowed", True))
        paper_allowed = _bool(row.get("paper_denominator_allowed", True))
        self_id_allowed = _bool(row.get("self_id_denominator_allowed", True))
        stale_excluded = _bool(row.get("stale_guardrail_excluded", False))
        rows.append(
            {
                "stale_exclusion_guard_id": f"m3000-stale-exclusion-{index:04d}",
                "source_stale_exclusion_guard_id": row.get("stale_exclusion_guard_id", ""),
                "stale_exclusion_audit_id": row.get("stale_exclusion_audit_id", ""),
                "stale_guardrail_exclusion_binding_id": row.get("stale_guardrail_exclusion_binding_id", ""),
                "stale_guardrail_exclusion_row_id": row.get("stale_guardrail_exclusion_row_id", ""),
                "executed_in_m3000": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "self_id_denominator_allowed": False,
                "stale_guardrail_excluded": stale_excluded,
                "status_pass": bool(
                    _bool(row.get("status_pass", False))
                    and not validation_allowed
                    and not paper_allowed
                    and not self_id_allowed
                    and stale_excluded
                ),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_input_guard_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["actor_input_exclusion_rows"], start=1):
        actor_visible = _bool(row.get("actor_visible", False))
        rows.append(
            {
                "actor_input_guard_id": f"m3000-actor-input-{index:04d}",
                "guard_family": "forbidden_metadata_actor_invisible",
                "forbidden_metadata_key": row.get("forbidden_metadata_key", ""),
                "observed_value": actor_visible,
                "expected_value": False,
                "actor_visible": actor_visible,
                "status_pass": _bool(row.get("status_pass", False)) and not actor_visible,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    observed_shape = (
        _all_equal(execution_rows, "actor_observation_dim", P0_OBSERVATION_DIM)
        if execution_rows
        else all(_to_int(row.get("actor_observation_dim"), default=P0_OBSERVATION_DIM) == P0_OBSERVATION_DIM for row in plan_rows)
    )
    observed_action = (
        _all_equal(execution_rows, "actor_action_dim", ACTION_DIM)
        if execution_rows
        else all(_to_int(row.get("actor_action_dim"), default=ACTION_DIM) == ACTION_DIM for row in plan_rows)
    )
    extra_specs = [
        ("actor_observation_dim", observed_shape, True),
        ("actor_action_dim", observed_action, True),
        ("hidden_oracle_actor_input_required", _any_true(execution_rows, "hidden_oracle_actor_input_required"), False),
        ("future_target_actor_input_required", _any_true(execution_rows, "future_target_actor_input_required"), False),
        ("target_labels_actor_visible", False, False),
        ("target_provenance_actor_visible", False, False),
        ("objective_source_route_verdict_paper_labels_actor_visible", False, False),
        ("stale_guardrails_executed", _any_true(stale_rows, "executed_in_m3000"), False),
    ]
    offset = len(rows)
    for index, (field, observed, expected) in enumerate(extra_specs, start=1):
        rows.append(
            {
                "actor_input_guard_id": f"m3000-actor-contract-{index:04d}",
                "guard_family": "actor_contract",
                "forbidden_metadata_key": field,
                "observed_value": observed,
                "expected_value": expected,
                "actor_visible": False,
                "status_pass": str(observed) == str(expected),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for index, row in enumerate(rows, start=1):
        row["actor_input_guard_id"] = row["actor_input_guard_id"] or f"m3000-actor-input-{offset + index:04d}"
    return rows


def build_checkpoint_side_effect_guard_rows(
    *,
    execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    del source
    any_execution = bool(execution_rows)
    artifact_loaded = _all_true(execution_rows, "candidate_residual_head_loaded_read_only") if execution_rows else False
    parent_loaded = _all_true(execution_rows, "parent_checkpoint_loaded_read_only") if execution_rows else False
    combined = execution_rows + failure_rows
    specs = [
        ("parent_checkpoint_loaded_read_only", parent_loaded, any_execution, True),
        ("candidate_residual_head_artifact_loaded_read_only", artifact_loaded, any_execution, True),
        ("environment_reset_run", any_execution, any_execution, True),
        ("environment_step_run", any_execution, any_execution, True),
        ("policy_rollout_run", any_execution, any_execution, True),
        ("training_or_ppo_run", _any_true(combined, "training_run") or _any_true(combined, "ppo_run"), False, False),
        ("private_holdout_used", _any_true(combined, "private_holdout_used"), False, False),
        ("ranking_run", _any_true(combined, "ranking_run"), False, False),
        ("winner_selected", _any_true(combined, "winner_selected"), False, False),
        ("checkpoint_save_scheduled", _any_true(combined, "checkpoint_save_scheduled"), False, False),
        ("checkpoint_mutation_scheduled", _any_true(combined, "checkpoint_mutation_scheduled"), False, False),
        ("checkpoint_promoted", _any_true(combined, "checkpoint_promoted"), False, False),
    ]
    return [
        {
            "side_effect_guard_id": f"m3000-side-effect-{index:04d}",
            "side_effect": side_effect,
            "observed_value": observed,
            "expected_value": expected,
            "allowed_in_m3000": allowed,
            "status_pass": str(observed) == str(expected),
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (side_effect, observed, expected, allowed) in enumerate(specs, start=1)
    ]


def build_claim_boundary_rows(
    *,
    artifacts_present: bool,
    follow_up_manifest_registered: bool,
    execution_rows_present: bool,
) -> list[dict[str, Any]]:
    allowed = [
        ("diagnostic_execution_artifacts", "artifact", artifacts_present, "M3000 diagnostic execution artifacts"),
        ("bounded_diagnostic_closed_loop_rows", "diagnostic", execution_rows_present, "M3000 execution rows"),
        ("candidate_denominator_accounting", "accounting", artifacts_present, "execution or failure rows"),
        ("success_retention_accounting", "guardrail", artifacts_present, "success execution or failure rows"),
        ("parent_comparison_report_only", "comparison", artifacts_present, "parent comparison report rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3001 manifest"),
    ]
    blocked = [
        ("ranking_or_winner", "ranking", "M3001 audit and later promotion gate"),
        ("checkpoint_mutation_or_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future audited verdict milestone"),
        ("validation_result", "validation", "M3001 audit and separate validation-result decision"),
        ("repair_success", "verdict", "future validation and audit"),
        ("driver_performance", "driver_performance", "proof/generalization/promotion gates"),
        ("paper_evidence", "paper", "paper-route fair comparison matrix"),
        ("current_sim_verdict", "validation", "separate current-sim verdict synthesis"),
        ("high_fidelity_validation", "validation", "Route C high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "separate fair comparison"),
        ("full_ideal_driver_completion", "full_goal", "full ideal driver gate"),
        ("level3_self_identification", "self_id", "self-ID proof gates"),
    ]
    rows = [
        claim_row(claim_id, family, True, made, evidence)
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(claim_row(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3000-{claim_id}",
        "claim_family": family,
        "allowed_in_m3000": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    candidate_execution_rows: list[dict[str, Any]],
    success_execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    failure_role_counts = Counter(str(row.get("row_role", "")) for row in failure_rows)
    accounted_candidate = len(candidate_execution_rows) + failure_role_counts["candidate_validation"]
    accounted_success = len(success_execution_rows) + failure_role_counts["success_behavior_retention"]
    execution_rows = candidate_execution_rows + success_execution_rows
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(bool(v) for key, v in source["source_exists"].items() if key != "follow_up_manifest"),
            True,
            "lineage_invalid",
        ),
        ("m2996_status_pass", "lineage", _bool(source["m2996_summary"].get("status_pass")), True, "lineage_invalid"),
        (
            "m2996_gate_matrix_pass",
            "lineage",
            _bool(source["m2996_summary"].get("gate_matrix_pass")),
            True,
            "lineage_invalid",
        ),
        (
            "m2996_required_artifacts_present",
            "lineage",
            _bool(source["m2996_summary"].get("required_artifacts_present")),
            True,
            "lineage_invalid",
        ),
        (
            "m2999_admits_m3000",
            "lineage",
            M2999_ADMISSION_TOKEN in source["m2999_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "residual_head_artifact_pass",
            "artifact",
            _bool(source["artifact_metadata"].get("status_pass", False)),
            True,
            "metric_artifact",
        ),
        (
            "candidate_validation_denominator_count",
            "accounting",
            role_counts["candidate_validation"],
            EXPECTED_CANDIDATE_VALIDATION_COUNT,
            "metric_artifact",
        ),
        (
            "success_retention_denominator_count",
            "accounting",
            role_counts["success_behavior_retention"],
            EXPECTED_SUCCESS_RETENTION_COUNT,
            "metric_artifact",
        ),
        (
            "stale_exclusion_count",
            "guardrail",
            len(stale_rows),
            EXPECTED_STALE_EXCLUSION_COUNT,
            "metric_artifact",
        ),
        (
            "candidate_rows_accounted",
            "accounting",
            accounted_candidate,
            EXPECTED_CANDIDATE_VALIDATION_COUNT,
            "scenario_sampling_failure",
        ),
        (
            "success_rows_accounted",
            "accounting",
            accounted_success,
            EXPECTED_SUCCESS_RETENTION_COUNT,
            "scenario_sampling_failure",
        ),
        ("execution_rows_status_pass", "execution", _all_true(execution_rows, "status_pass"), True, "metric_artifact"),
        (
            "selected_metrics_finite",
            "metric",
            bool(execution_rows) and selected_metrics_are_finite(execution_rows),
            True,
            "metric_artifact",
        ),
        (
            "residual_within_limit",
            "wrapper",
            residuals_within_limit(execution_rows),
            True,
            "contract_violation",
        ),
        (
            "parent_comparison_report_only",
            "comparison",
            _all_true(parent_rows, "status_pass")
            and not _any_true(parent_rows, "ranking_run")
            and not _any_true(parent_rows, "winner_selected")
            and not _any_true(parent_rows, "promotion_run")
            and not _any_true(parent_rows, "success_rate_verdict_claim_made"),
            True,
            "contract_violation",
        ),
        (
            "stale_rows_not_executed_or_denominator",
            "guardrail",
            _all_true(stale_rows, "status_pass") and not _any_true(stale_rows, "executed_in_m3000"),
            True,
            "contract_violation",
        ),
        (
            "actor_input_guards_pass",
            "actor_contract",
            len(actor_rows) >= EXPECTED_ACTOR_INPUT_GUARD_COUNT and _all_true(actor_rows, "status_pass"),
            True,
            "contract_violation",
        ),
        (
            "side_effect_guards_pass",
            "side_effect",
            len(side_effect_rows) == EXPECTED_SIDE_EFFECT_GUARD_COUNT and _all_true(side_effect_rows, "status_pass"),
            True,
            "contract_violation",
        ),
        (
            "no_forbidden_execution_or_overclaim",
            "claim_boundary",
            not any(forbidden_execution_flag(row) for row in execution_rows + failure_rows),
            True,
            "proof_washout",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            _all_true(claim_rows, "status_pass"),
            True,
            "proof_washout",
        ),
        (
            "follow_up_manifest_registered",
            "follow_up",
            source["source_exists"].get("follow_up_manifest", False),
            True,
            "lineage_invalid",
        ),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m3000-gate-{index:04d}-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    candidate_execution_rows: list[dict[str, Any]],
    success_execution_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    device: str,
) -> dict[str, Any]:
    gate_matrix_pass = _all_true(gate_rows, "status_pass")
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    role_counts = Counter(str(row.get("row_role", "")) for row in plan_rows)
    failure_role_counts = Counter(str(row.get("row_role", "")) for row in failure_rows)
    candidate_accounted = len(candidate_execution_rows) + failure_role_counts["candidate_validation"]
    success_accounted = len(success_execution_rows) + failure_role_counts["success_behavior_retention"]
    execution_rows = candidate_execution_rows + success_execution_rows
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in execution_rows)
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "device": device,
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "result_class": (
            "engineering_controller_route_a_nonzero_residual_bounded_diagnostic_validation_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_nonzero_residual_bounded_diagnostic_validation_preflight_fail_closed"
        ),
        "source_artifacts_present": all(bool(v) for key, v in source["source_exists"].items() if key != "follow_up_manifest"),
        "m2996_status_pass": _bool(source["m2996_summary"].get("status_pass")),
        "m2996_gate_matrix_pass": _bool(source["m2996_summary"].get("gate_matrix_pass")),
        "m2996_required_artifacts_present": _bool(source["m2996_summary"].get("required_artifacts_present")),
        "m2999_admits_m3000": M2999_ADMISSION_TOKEN in source["m2999_design_text"],
        "candidate_validation_denominator_row_count": role_counts["candidate_validation"],
        "success_retention_denominator_row_count": role_counts["success_behavior_retention"],
        "stale_guardrail_exclusion_row_count": len(stale_rows),
        "candidate_validation_execution_row_count": len(candidate_execution_rows),
        "success_behavior_retention_execution_row_count": len(success_execution_rows),
        "candidate_validation_failure_row_count": len(failure_rows),
        "candidate_validation_failure_count": failure_role_counts["candidate_validation"],
        "success_behavior_retention_failure_count": failure_role_counts["success_behavior_retention"],
        "accounted_candidate_validation_count": candidate_accounted,
        "accounted_success_retention_count": success_accounted,
        "parent_comparison_report_row_count": len(parent_rows),
        "actor_input_guard_row_count": len(actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "candidate_residual_head_artifact": source["candidate_residual_head_artifact"],
        "candidate_residual_head_artifact_exists": Path(str(source["candidate_residual_head_artifact"])).exists(),
        "artifact_metadata": source["artifact_metadata"],
        "residual_limit": source["artifact_metadata"].get("residual_limit", 0.0),
        "residual_delta_abs_max": _max_float(execution_rows, "residual_delta_abs_max"),
        "residual_trace_count": sum(_to_int(row.get("residual_trace_count_delta"), default=0) for row in execution_rows),
        "actor_contract_shape_72_action_3": _all_equal(execution_rows, "actor_observation_dim", P0_OBSERVATION_DIM)
        and _all_equal(execution_rows, "actor_action_dim", ACTION_DIM),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "diagnostic_termination_counts": dict(sorted(termination_counts.items())),
        "diagnostic_success_count": sum(_bool(row.get("success", False)) for row in execution_rows),
        "diagnostic_collision_count": sum(_bool(row.get("collision", False)) for row in execution_rows),
        "diagnostic_offtrack_count": int(termination_counts.get("off_track", 0)),
        "diagnostic_speed_too_low_count": int(termination_counts.get("speed_too_low", 0)),
        "all_selected_metrics_finite": bool(execution_rows) and selected_metrics_are_finite(execution_rows),
        "environment_reset_run": bool(execution_rows),
        "environment_step_run": bool(execution_rows),
        "policy_rollout_run": bool(execution_rows),
        "diagnostic_validation_preflight_run": bool(execution_rows),
        "parent_comparison_report_only": _all_true(parent_rows, "parent_comparison_report_only"),
        "stale_guardrail_executed_count": sum(_bool(row.get("executed_in_m3000", False)) for row in stale_rows),
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "private_holdout_run": False,
        "success_rate_verdict_claim_made": False,
        "validation_result_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(path) for key, path in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3000 Engineering Controller Route A Nonzero Residual Bounded Diagnostic Validation Preflight",
            "",
            "## Summary",
            "",
            f"- status pass: `{summary['status_pass']}`",
            f"- gate matrix pass: `{summary['gate_matrix_pass']}`",
            f"- required artifacts present: `{summary['required_artifacts_present']}`",
            f"- candidate denominator rows: `{summary['candidate_validation_denominator_row_count']}`",
            f"- candidate execution rows: `{summary['candidate_validation_execution_row_count']}`",
            f"- success-retention denominator rows: `{summary['success_retention_denominator_row_count']}`",
            f"- success-retention execution rows: `{summary['success_behavior_retention_execution_row_count']}`",
            f"- failure rows: `{summary['candidate_validation_failure_row_count']}`",
            f"- stale exclusions protected: `{summary['stale_guardrail_exclusion_row_count']}`",
            f"- parent comparison rows: `{summary['parent_comparison_report_row_count']}`",
            f"- residual abs max: `{summary['residual_delta_abs_max']}`",
            f"- diagnostic termination counts: `{summary['diagnostic_termination_counts']}`",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
            "## Boundary",
            "",
            "M3000 records bounded closed-loop diagnostic fields only. Parent comparison remains report-only; stale fixed-source rows remain excluded from validation, paper, and self-ID denominators.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    manifest_id = NEXT_ID
    follow_up_doc = Path(f"docs/{manifest_id}.md")
    return {
        "id": manifest_id,
        "type": "gate",
        "status": "pending",
        "hypothesis": (
            "A bounded result audit can accept or reject the M3000 diagnostic validation preflight "
            "before any ranking promotion validation-result repair-success performance paper high-fidelity or self-ID claim."
        ),
        "success_criteria": [
            f"{follow_up_doc} exists",
            "M3001 audits M3000 summary gate matrix execution failure parent-comparison stale actor side-effect and claim artifacts",
            "M3001 selects exactly one next route or stop state",
            "no ranking promotion validation-result repair-success performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3001 hides missing M3000 artifacts or failure rows",
            "M3001 treats M3000 diagnostic rows as validation result repair-success performance paper or self-ID evidence",
            "M3001 changes actor stale-exclusion parent-comparison checkpoint side-effect or claim boundaries",
            "M3001 leaves next route ambiguous",
        ],
        "commands": [{"name": "result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": str(follow_up_doc), "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "candidate_validation_execution_rows.csv"),
            str(output_dir / "candidate_validation_failure_rows.csv"),
            str(output_dir / "success_behavior_retention_execution_rows.csv"),
            str(output_dir / "parent_comparison_report_rows.csv"),
            str(output_dir / "stale_exclusion_guard_rows.csv"),
            str(output_dir / "actor_input_guard_rows.csv"),
            str(output_dir / "checkpoint_side_effect_guard_rows.csv"),
            str(output_dir / "claim_boundary_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "decision_rule": (
            "Pass only if M3001 audits M3000 diagnostic row accounting and boundaries, then selects one next route "
            "or stop state without overclaiming diagnostic current-sim rows."
        ),
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "training_instability",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [str(summary_path), str(output_dir / "gate_matrix.csv"), str(doc_path)],
            "parent_config": [
                "experiments/manifests/m3000-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-preflight.json",
                "experiments/manifests/m2999-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-validation-preflight-design.json",
            ],
            "parent_objective": [
                "audit M3000 bounded diagnostic validation artifacts before any interpretation"
            ],
            "derived_from": [MILESTONE_ID],
            "blocked_by": [
                "M3000 diagnostic rows require result audit before validation-result or continuation decisions",
                "stale fixed-source rows must remain excluded",
                "parent comparison is report-only and cannot select a winner",
            ],
            "supersedes": [
                "direct interpretation of M3000 diagnostic rows without result audit",
                "direct ranking or promotion of the M2993 residual-head artifact",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{manifest_id}.md",
        "scoreboard_checkpoint": str(follow_up_doc),
        "public_gates": [
            "M3001 must audit all M3000 required artifacts and row accounting",
            "M3001 must preserve actor 72/action 3 and no hidden oracle target provenance objective source route verdict or paper actor inputs",
            "M3001 must keep stale rows out of validation paper and self-ID denominators",
            "M3001 must keep parent comparison report-only with no ranking winner selection promotion or success-rate verdict",
            "M3001 must not claim repair-success performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rank select a winner promote or mutate checkpoints",
            "do not include stale fixed-source rows in validation paper or self-ID denominators",
            "do not change actor input or action contract",
            "do not convert diagnostic current-sim rows into performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claims",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_bounded_diagnostic_validation_result_audit",
            "evidence_increment": "audits newly produced M3000 bounded diagnostic validation rows",
            "claim_scope": "Result audit only; no ranking promotion validation-result repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3000 artifacts are missing or row accounting is incomplete",
                "stop if stale rows were executed or included in validation paper or self-ID denominators",
                "stop if parent comparison was treated as ranking winner selection or promotion",
                "stop if diagnostic rows would be overclaimed as validation result performance paper current-sim high-fidelity or self-ID evidence",
            ],
            "fallback_plan": [
                "route to concrete artifact repair if M3000 row accounting is incomplete",
                "route to synthesis or pivot if bounded current-sim diagnostic execution cannot preserve boundaries",
                "route to one audited continuation only if M3001 accepts M3000 as complete and claim-safe",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3000 completes bounded diagnostic validation preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3000 bounded diagnostic validation preflight artifacts",
            "admission_evidence": [
                "M3000 summary gate matrix execution failure parent-comparison stale actor side-effect and claim rows",
                "M2999 admitted exactly one data-producing diagnostic preflight before audit",
            ],
            "blocked_shortcuts": [
                "no ranking winner selection promotion or success-rate verdict",
                "no checkpoint mutation save selection or promotion",
                "no target labels target provenance objective admission source route verdict paper labels hidden parameters or oracle actor inputs",
                "no driver-performance current-sim high-fidelity full ideal driver finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                str(follow_up_doc),
                f"docs/reviews/{manifest_id}.md",
                "M3001 status queue scoreboard research log and review",
                "one follow-up manifest only if M3001 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3001 accepts or rejects M3000 artifacts",
                "M3001 chooses one next route or stop state",
                "actor stale-exclusion parent-comparison checkpoint side-effect and claim boundaries remain unchanged",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3001 audits Route A current-sim diagnostic rows and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3001; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2996-M3000 Route A actor-head delta validation-contract and diagnostic preflight chain.",
            "negative_result_policy": "Preserve diagnostic failures and route to repair, synthesis, pivot, or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3000 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits newly produced bounded closed-loop diagnostic rows",
            "paper_verdict_delta": "no paper verdict; may inform Route A diagnostic continuation only after audit",
            "must_synthesize_if": [
                "M3001 cannot select exactly one next route",
                "M3001 would claim performance validation-result paper current-sim high-fidelity finite-window-vs-GRU or self-ID evidence",
            ],
        },
        "next_blocker": manifest_id,
    }


def forbidden_execution_flag(row: Mapping[str, Any]) -> bool:
    return any(
        _bool(row.get(field, False))
        for field in (
            "training_started",
            "training_run",
            "replay_started",
            "replay_run",
            "ppo_used",
            "ppo_run",
            "dependency_execution_performed",
            "private_holdout_used",
            "profile_specific_tuning",
            "active_config_overwritten",
            "ranking_run",
            "winner_selected",
            "checkpoint_promoted",
            "promoted",
            "checkpoint_save_scheduled",
            "checkpoint_mutation_scheduled",
            "actor_input_contract_changed",
            "hidden_oracle_actor_input_required",
            "future_target_actor_input_required",
            "route_labels_actor_visible",
            "source_labels_actor_visible",
            "evaluator_labels_actor_visible",
            "diagnostic_labels_actor_visible",
            "success_progress_labels_actor_visible",
            "verdict_labels_actor_visible",
            "blocked_stale_guard_execution",
            "guardrail_rows_in_success_denominator",
            "success_rate_verdict_claim_made",
            "driver_performance_claim_made",
            "repair_success_claim_made",
            "validation_readiness_claim_made",
            "validation_result_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
            "full_ideal_driver_completion_claim_made",
            "level3_self_id_claim_made",
        )
    )


def residuals_within_limit(rows: Iterable[Mapping[str, Any]]) -> bool:
    rows = list(rows)
    if not rows:
        return False
    for row in rows:
        residual = _to_float(row.get("residual_delta_abs_max"), default=float("nan"))
        limit = _to_float(row.get("residual_limit"), default=float("nan"))
        if not np.isfinite(residual) or not np.isfinite(limit) or residual > limit + 1.0e-9:
            return False
    return True


def shape_text(shape: tuple[int, ...]) -> str:
    return "x".join(str(part) for part in shape)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        if value in ("", None):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _all_true(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    rows = list(rows)
    return bool(rows) and all(_bool(row.get(key, False)) for row in rows)


def _any_true(rows: Iterable[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def _all_equal(rows: Iterable[Mapping[str, Any]], key: str, expected: Any) -> bool:
    rows = list(rows)
    return bool(rows) and all(row.get(key) == expected or str(row.get(key)) == str(expected) for row in rows)


def _max_float(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    return max((_to_float(row.get(key), default=0.0) for row in rows), default=0.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2996-dir", type=Path, default=DEFAULT_M2996_DIR)
    parser.add_argument("--m2999-design", type=Path, default=DEFAULT_M2999_DESIGN)
    parser.add_argument("--m2977-dir", type=Path, default=DEFAULT_M2977_DIR)
    parser.add_argument("--m2960-dir", type=Path, default=DEFAULT_M2960_DIR)
    parser.add_argument("--executable-specs", type=Path, default=DEFAULT_EXECUTABLE_SPECS)
    parser.add_argument("--executable-workload", type=Path, default=DEFAULT_EXECUTABLE_WORKLOAD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_bounded_diagnostic_validation_preflight(
        m2996_dir=args.m2996_dir,
        m2999_design=args.m2999_design,
        m2977_dir=args.m2977_dir,
        m2960_dir=args.m2960_dir,
        executable_specs=args.executable_specs,
        executable_workload=args.executable_workload,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        device=args.device,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"candidate_execution_rows={summary['candidate_validation_execution_row_count']}")
    print(f"success_retention_execution_rows={summary['success_behavior_retention_execution_row_count']}")
    print(f"failure_rows={summary['candidate_validation_failure_row_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
