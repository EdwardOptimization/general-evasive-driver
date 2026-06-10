"""Materialize M3153 residual action-delta counterfactual replay diagnostics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
import autodrift.engineering_controller_active_safety_driver_residual_failure_step_action_influence_trace_materialization_preflight as m3115
import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_action_delta_coverage_diagnostic_materialization_preflight as m3147
import autodrift.engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight as m3142
import autodrift.engineering_controller_active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_smoke_measurement_preflight as m3088
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3153-engineering-controller-active-safety-driver-residual-action-delta-"
    "counterfactual-replay-diagnostic-materialization-preflight"
)
NEXT_ID = (
    "m3154-engineering-controller-active-safety-driver-residual-action-delta-"
    "counterfactual-replay-diagnostic-result-audit"
)
M3152_ID = "m3152-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-synthesis"
M3151_ID = (
    "m3151-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-"
    "counterfactual-sensitivity-diagnostic-result-audit"
)
M3150_ID = (
    "m3150-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-"
    "counterfactual-sensitivity-diagnostic-materialization-preflight"
)
M3147_ID = (
    "m3147-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-"
    "action-delta-coverage-diagnostic-materialization-preflight"
)

DEFAULT_M3152_SYNTHESIS = Path(f"docs/{M3152_ID}.md")
DEFAULT_M3150_DIR = Path(
    "runs/m3150_engineering_controller_active_safety_driver_residual_action_delta_effectiveness_"
    "counterfactual_sensitivity_diagnostic_materialization_preflight"
)
DEFAULT_M3147_DIR = Path(
    "runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_"
    "speed_envelope_action_delta_coverage_diagnostic_materialization_preflight"
)
DEFAULT_M3012_DIR = Path(
    "runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_"
    "replay_diagnostic_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_RESIDUAL_ROWS = 7
EXPECTED_COLLISION_ROWS = 5
EXPECTED_OFFTRACK_ROWS = 2
EXPECTED_VARIANT_ROWS = 4
REFERENCE_VARIANT_ID = "m3142_reference"
CLAIM_SCOPE = (
    "M3153 Active Safety Driver residual action-delta counterfactual replay diagnostic only; "
    "the seven residual M3147/M3150 rows may be replayed with a fixed predeclared set of "
    "actor-visible obs72-to-action3 direct-action variants to diagnose action-channel "
    "sensitivity. No repair implementation, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, driver-performance verdict, current-sim verdict, repair "
    "success, robustness-result, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, feasibility proof, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "repair implementation, validation result, driver-performance verdict, current-sim verdict, "
    "robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, "
    "checkpoint promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification"
)

CONTEXT_FIELDNAMES = [
    "counterfactual_plan_row_id",
    "residual_failure_id",
    "effectiveness_row_id",
    "trace_episode_id",
    "m3144_measurement_episode_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "axis_id",
    "binding_role",
    "task_family",
    "executable_workload_id",
    "executable_source_spec_id",
    "task_source_id",
    "base_profile_name",
    "eval_seed",
    "target_failure_kind",
    "source_m3147_terminal_termination_reason",
    "source_m3147_terminal_outcome_bucket",
    "source_m3150_sensitivity_label",
]
VARIANT_FIELDNAMES = [
    "variant_id",
    "variant_order",
    "variant_family",
    "variant_description",
    "base_policy_id",
    "fixed_predeclared",
    "applies_to_all_residual_rows",
    "actor_observation_contract",
    "action_shape",
    "output_components",
    "output_semantics",
    "extra_throttle_drop",
    "extra_brake_physical_add",
    "lateral_delta_gain",
    "uses_hidden_label_at_runtime",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
EPISODE_FIELDNAMES = [
    "counterfactual_episode_id",
    *CONTEXT_FIELDNAMES,
    "variant_id",
    "variant_order",
    "variant_family",
    "policy",
    "steps",
    "terminated",
    "truncated",
    "success",
    "collision",
    "offtrack",
    "obstacle_completed",
    "termination_reason",
    "outcome_bucket",
    "min_obstacle_clearance",
    "obstacle_collision_radius",
    "min_clearance_margin",
    "return",
    "speed_mean",
    "action_rate_mean",
    "high_sideslip_fraction",
    "beta_abs_error_mean",
    "lateral_rmse",
    "max_off_track_overshoot",
    "direct_action_step_count",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction",
    "final_action_abs_max",
    "mean_overlay_alpha",
    "max_overlay_alpha",
    "mean_probe_alpha",
    "max_probe_alpha",
    "mean_delta_l1_vs_reference",
    "max_delta_abs_vs_reference",
    "action_saturation_fraction",
    "candidate_output_semantics",
    "runtime_driver_id",
    "runtime_base_policy_required",
    "checkpoint_model_required",
    "recurrent_hidden_state_required",
    "environment_reset_run",
    "environment_step_run",
    "policy_action_run",
    "policy_rollout_run",
    "validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "source_labels_actor_visible",
    "route_labels_actor_visible",
    "outcome_labels_actor_visible",
    "success_progress_labels_actor_visible",
    "verdict_labels_actor_visible",
    "ttc_actor_input_required",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "robustness_result_claim_made",
    "validation_result_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
    "full_ideal_driver_completion_claim_made",
    "feasibility_proof_claim_made",
    "level3_self_id_claim_made",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
FAILURE_FIELDNAMES = [
    "counterfactual_episode_id",
    *CONTEXT_FIELDNAMES,
    "variant_id",
    "variant_order",
    "variant_family",
    "error_type",
    "error_message",
    "runtime_base_policy_required",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
COMPARISON_FIELDNAMES = [
    "comparison_id",
    "residual_failure_id",
    "source_measurement_episode_id",
    "fresh_panel_row_id",
    "target_failure_kind",
    "source_m3150_sensitivity_label",
    "variant_id",
    "reference_variant_id",
    "reference_termination_reason",
    "variant_termination_reason",
    "reference_outcome_bucket",
    "variant_outcome_bucket",
    "outcome_bucket_match",
    "reference_success",
    "variant_success",
    "success_delta",
    "reference_collision",
    "variant_collision",
    "collision_delta",
    "reference_offtrack",
    "variant_offtrack",
    "offtrack_delta",
    "reference_min_clearance_margin",
    "variant_min_clearance_margin",
    "clearance_margin_delta",
    "reference_return",
    "variant_return",
    "return_delta",
    "reference_speed_mean",
    "variant_speed_mean",
    "speed_mean_delta",
    "reference_steps",
    "variant_steps",
    "steps_delta",
    "mean_delta_l1_vs_reference",
    "max_delta_abs_vs_reference",
    "counterfactual_diagnostic_label",
    "action_channel_sensitive_diagnostic",
    "repair_success_claim_made",
    "validation_run",
    "driver_performance_claim_made",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3153",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
GATE_FIELDNAMES = ["gate_id", "gate_family", "status_pass", "observed", "expected", "failure_type", "claim_boundary"]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: Iterable[float]) -> float | str:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else ""


def _physical(action_value: float) -> float:
    return float(np.clip(0.5 * (action_value + 1.0), 0.0, 1.0))


def _from_physical(physical_value: float) -> float:
    return float(-1.0 + 2.0 * np.clip(physical_value, 0.0, 1.0))


def _success(row: Mapping[str, Any]) -> bool:
    if "success" in row:
        return _bool(row.get("success", False))
    return _bool(row.get("obstacle_completed", False)) and not _bool(row.get("collision", False))


def _offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "") or "") == "off_track"


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "counterfactual_variant_rows": output_dir / "counterfactual_variant_rows.csv",
        "counterfactual_replay_episode_rows": output_dir / "counterfactual_replay_episode_rows.csv",
        "counterfactual_replay_failure_rows": output_dir / "counterfactual_replay_failure_rows.csv",
        "counterfactual_replay_comparison_rows": output_dir / "counterfactual_replay_comparison_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(*, m3152_synthesis: Path, m3150_dir: Path, m3147_dir: Path, m3012_dir: Path) -> dict[str, Any]:
    paths = {
        "m3152_synthesis": m3152_synthesis,
        "m3150_summary": m3150_dir / "summary.json",
        "m3150_effectiveness_rows": m3150_dir / "residual_delta_effectiveness_rows.csv",
        "m3150_gate_rows": m3150_dir / "gate_matrix.csv",
        "m3147_summary": m3147_dir / "summary.json",
        "m3147_coverage_rows": m3147_dir / "action_delta_coverage_rows.csv",
        "m3147_gate_rows": m3147_dir / "gate_matrix.csv",
        "m3012_summary": m3012_dir / "summary.json",
        "m3012_executable_specs": m3012_dir / "executable_source_specs.json",
        "m3012_workload_rows": m3012_dir / "executable_workload_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    spec_payload = read_json(paths["m3012_executable_specs"]) if exists["m3012_executable_specs"] else {}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3152_synthesis_text": paths["m3152_synthesis"].read_text(encoding="utf-8") if exists["m3152_synthesis"] else "",
        "m3150_summary": read_json(paths["m3150_summary"]) if exists["m3150_summary"] else {},
        "m3150_effectiveness_rows": read_csv_rows(paths["m3150_effectiveness_rows"]),
        "m3150_gate_rows": read_csv_rows(paths["m3150_gate_rows"]),
        "m3147_summary": read_json(paths["m3147_summary"]) if exists["m3147_summary"] else {},
        "m3147_coverage_rows": read_csv_rows(paths["m3147_coverage_rows"]),
        "m3147_gate_rows": read_csv_rows(paths["m3147_gate_rows"]),
        "m3012_summary": read_json(paths["m3012_summary"]) if exists["m3012_summary"] else {},
        "m3012_executable_specs": list(spec_payload.get("executable_source_specs", [])),
        "m3012_workload_rows": read_csv_rows(paths["m3012_workload_rows"]),
    }


def fixed_variant_rows() -> list[dict[str, Any]]:
    variants = [
        (
            REFERENCE_VARIANT_ID,
            "reference",
            "M3142 speed-envelope action; reference for same-row counterfactual comparison",
            0.0,
            0.0,
            0.0,
        ),
        (
            "decel_headroom_probe",
            "longitudinal_headroom",
            "Reference action plus bounded extra throttle drop and brake add when M3142 overlay is active",
            0.18,
            0.18,
            0.0,
        ),
        (
            "brake_saturation_probe",
            "longitudinal_saturation",
            "Reference action plus stronger bounded brake/headroom use under the same actor-visible overlay",
            0.28,
            0.32,
            0.0,
        ),
        (
            "lateral_headroom_probe",
            "lateral_headroom",
            "Reference action plus bounded lateral nudge under the same actor-visible overlay",
            0.10,
            0.12,
            0.22,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for order, (variant_id, family, description, throttle_drop, brake_add, lateral_gain) in enumerate(variants, start=1):
        rows.append(
            {
                "variant_id": variant_id,
                "variant_order": order,
                "variant_family": family,
                "variant_description": description,
                "base_policy_id": m3142.POLICY_ID,
                "fixed_predeclared": True,
                "applies_to_all_residual_rows": True,
                "actor_observation_contract": "actor_visible_obs72_only",
                "action_shape": ACTION_DIM,
                "output_components": "|".join(m3142.ACTION_COMPONENTS),
                "output_semantics": m3142.OUTPUT_SEMANTICS,
                "extra_throttle_drop": throttle_drop,
                "extra_brake_physical_add": brake_add,
                "lateral_delta_gain": lateral_gain,
                "uses_hidden_label_at_runtime": False,
                "runtime_base_policy_required": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def counterfactual_replay_plan(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build the seven-row replay plan from M3147/M3150 diagnostics."""

    effectiveness_by_residual = {
        str(row.get("residual_failure_id", "")): row for row in source.get("m3150_effectiveness_rows", [])
    }
    workload_by_id = {
        str(row.get("executable_workload_id", "")): row for row in source.get("m3012_workload_rows", [])
    }
    plan: list[dict[str, Any]] = []
    for index, coverage in enumerate(
        sorted(source.get("m3147_coverage_rows", []), key=lambda row: str(row.get("residual_failure_id", ""))),
        start=1,
    ):
        residual_failure_id = str(coverage.get("residual_failure_id", ""))
        effectiveness = effectiveness_by_residual.get(residual_failure_id, {})
        workload = workload_by_id.get(str(coverage.get("executable_workload_id", "")), {})
        config_path = str(workload.get("config_path", ""))
        target_kind = str(coverage.get("target_failure_kind", ""))
        hidden_label_violation = any(
            _bool(workload.get(field, False))
            for field in (
                "hidden_oracle_actor_input_required",
                "future_target_actor_input_required",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
            )
        )
        row = {
            "counterfactual_plan_row_id": f"m3153-counterfactual-plan-row-{index:04d}",
            "residual_failure_id": residual_failure_id,
            "effectiveness_row_id": effectiveness.get("effectiveness_row_id", ""),
            "trace_episode_id": coverage.get("trace_episode_id", ""),
            "m3144_measurement_episode_id": coverage.get("m3144_measurement_episode_id", ""),
            "source_measurement_episode_id": coverage.get("source_measurement_episode_id", ""),
            "fresh_panel_row_id": coverage.get("fresh_panel_row_id", ""),
            "axis_id": coverage.get("axis_id", ""),
            "binding_role": coverage.get("binding_role", ""),
            "task_family": coverage.get("task_family", ""),
            "executable_workload_id": coverage.get("executable_workload_id", ""),
            "executable_source_spec_id": coverage.get("executable_source_spec_id", ""),
            "task_source_id": coverage.get("task_source_id", ""),
            "base_profile_name": workload.get("profile_binding_name", coverage.get("base_profile_name", "")),
            "eval_seed": coverage.get("eval_seed", ""),
            "target_failure_kind": target_kind,
            "source_m3147_terminal_termination_reason": coverage.get("terminal_termination_reason", ""),
            "source_m3147_terminal_outcome_bucket": coverage.get("terminal_outcome_bucket", ""),
            "source_m3150_sensitivity_label": effectiveness.get("counterfactual_sensitivity_label", ""),
            "config_path": config_path,
            "status_pass": bool(
                residual_failure_id
                and effectiveness
                and target_kind in {"collision", "offtrack"}
                and workload
                and _bool(workload.get("status_pass", False))
                and config_path
                and Path(config_path).exists()
                and not hidden_label_violation
            ),
            "hidden_label_violation": hidden_label_violation,
            "claim_boundary": CLAIM_SCOPE,
        }
        plan.append(row)
    return plan


def _context_fields(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {field: plan.get(field, "") for field in CONTEXT_FIELDNAMES}


def _sample_overlay_observation() -> np.ndarray:
    obs = np.zeros(P0_OBSERVATION_DIM, dtype=np.float32)
    obs[0] = 0.90
    obs[44] = 1.0
    obs[45] = 0.20
    obs[46] = 0.02
    obs[49] = 0.30
    return obs


def counterfactual_variant_action(observation: np.ndarray, variant: Mapping[str, Any]) -> dict[str, Any]:
    obs = np.asarray(observation, dtype=np.float32)
    if obs.shape != (P0_OBSERVATION_DIM,):
        raise ValueError(f"expected observation shape {(P0_OBSERVATION_DIM,)}, got {obs.shape}")
    if not np.all(np.isfinite(obs)):
        raise ValueError("observation contains non-finite values")
    reference = np.asarray(m3142.residual_trajectory_timing_speed_envelope_action(obs, m3142.POLICY_CONFIG), dtype=np.float32)
    if reference.shape != (ACTION_DIM,):
        raise ValueError(f"reference action must be action3, got {reference.shape}")
    features = m3142.speed_envelope_features(obs, m3142.POLICY_CONFIG)
    actor_features = m3115.actor_visible_diagnostic_features(obs)
    alpha = float(np.clip(features["overlay_alpha"], 0.0, 1.0))
    action = reference.copy()
    if str(variant.get("variant_id", "")) != REFERENCE_VARIANT_ID and alpha > 0.0:
        throttle_drop = _float(variant.get("extra_throttle_drop"), 0.0)
        brake_add = _float(variant.get("extra_brake_physical_add"), 0.0)
        lateral_gain = _float(variant.get("lateral_delta_gain"), 0.0)
        action[1] = float(action[1]) - throttle_drop * alpha
        action[2] = _from_physical(_physical(float(action[2])) + brake_add * alpha)
        direction = float(features.get("obstacle_avoid_direction", 0.0))
        if abs(direction) < 1e-9:
            center_error = float(actor_features.get("road_center_error_actor_visible", 0.0))
            direction = -float(np.sign(center_error)) if abs(center_error) > 1e-9 else 0.0
        action[0] = float(action[0]) + lateral_gain * alpha * direction
    unclipped = action.copy()
    clipped = np.clip(action, -1.0, 1.0).astype(np.float32)
    delta = clipped - reference
    return {
        "action": clipped,
        "reference_action": reference,
        "unclipped_action": unclipped,
        "delta_vs_reference": delta.astype(np.float32),
        "features": features,
        "actor_features": actor_features,
        "probe_alpha": alpha,
        "clip_required": bool(np.max(np.abs(unclipped)) > 1.0 + 1e-7),
    }


class M3153CounterfactualPolicy:
    """Policy adapter for one fixed M3153 counterfactual variant."""

    def __init__(self, variant: Mapping[str, Any]):
        self.variant = dict(variant)
        self.last_sequence = None
        self.reset()

    def reset(self) -> None:
        self.last_sequence = None
        self.step_count = 0
        self.raw_action_abs_max = 0.0
        self.raw_action_l2_sum = 0.0
        self.final_action_abs_max = 0.0
        self.clip_count = 0
        self.saturation_count = 0
        self.overlay_sum = 0.0
        self.overlay_max = 0.0
        self.probe_alpha_sum = 0.0
        self.probe_alpha_max = 0.0
        self.delta_l1_sum = 0.0
        self.delta_abs_max = 0.0

    def act(self, observation: np.ndarray, info: dict[str, Any]) -> np.ndarray:
        del info
        payload = counterfactual_variant_action(observation, self.variant)
        action = np.asarray(payload["action"], dtype=np.float32)
        delta = np.asarray(payload["delta_vs_reference"], dtype=np.float32)
        features = dict(payload["features"])
        self.step_count += 1
        self.raw_action_abs_max = max(self.raw_action_abs_max, float(np.max(np.abs(payload["unclipped_action"]))))
        self.raw_action_l2_sum += float(np.linalg.norm(payload["unclipped_action"]))
        self.final_action_abs_max = max(self.final_action_abs_max, float(np.max(np.abs(action))))
        self.clip_count += int(bool(payload["clip_required"]))
        self.saturation_count += int(float(np.max(np.abs(action))) >= 0.999)
        self.overlay_sum += float(features["overlay_alpha"])
        self.overlay_max = max(self.overlay_max, float(features["overlay_alpha"]))
        self.probe_alpha_sum += float(payload["probe_alpha"])
        self.probe_alpha_max = max(self.probe_alpha_max, float(payload["probe_alpha"]))
        self.delta_l1_sum += float(np.sum(np.abs(delta)))
        self.delta_abs_max = max(self.delta_abs_max, float(np.max(np.abs(delta))))
        return action

    def telemetry(self) -> dict[str, Any]:
        steps = int(self.step_count)
        variant_id = str(self.variant.get("variant_id", ""))
        return {
            "runtime_driver_id": f"m3153_{variant_id}",
            "candidate_output_semantics": m3142.OUTPUT_SEMANTICS,
            "runtime_base_policy_required": False,
            "checkpoint_model_required": False,
            "recurrent_hidden_state_required": False,
            "direct_action_step_count": steps,
            "raw_action_abs_max": float(self.raw_action_abs_max),
            "raw_action_l2_mean": float(self.raw_action_l2_sum / steps) if steps else 0.0,
            "action_clip_fraction": float(self.clip_count / steps) if steps else 0.0,
            "final_action_abs_max": float(self.final_action_abs_max),
            "mean_overlay_alpha": float(self.overlay_sum / steps) if steps else 0.0,
            "max_overlay_alpha": float(self.overlay_max),
            "mean_probe_alpha": float(self.probe_alpha_sum / steps) if steps else 0.0,
            "max_probe_alpha": float(self.probe_alpha_max),
            "mean_delta_l1_vs_reference": float(self.delta_l1_sum / steps) if steps else 0.0,
            "max_delta_abs_vs_reference": float(self.delta_abs_max),
            "action_saturation_fraction": float(self.saturation_count / steps) if steps else 0.0,
        }


def episode_row_from_result(
    *,
    plan: Mapping[str, Any],
    variant: Mapping[str, Any],
    row: Mapping[str, Any],
    telemetry: Mapping[str, Any],
) -> dict[str, Any]:
    item = {field: "" for field in EPISODE_FIELDNAMES}
    item.update(_context_fields(plan))
    item.update(
        {
            "counterfactual_episode_id": (
                f"{plan.get('counterfactual_plan_row_id', 'm3153-counterfactual')}-"
                f"{variant.get('variant_id', '')}"
            ),
            "variant_id": variant.get("variant_id", ""),
            "variant_order": variant.get("variant_order", ""),
            "variant_family": variant.get("variant_family", ""),
            "policy": row.get("policy", ""),
            "steps": row.get("steps", ""),
            "terminated": row.get("terminated", ""),
            "truncated": row.get("truncated", ""),
            "success": _success(row),
            "collision": _bool(row.get("collision", False)),
            "offtrack": _offtrack(row),
            "obstacle_completed": _bool(row.get("obstacle_completed", False)),
            "termination_reason": row.get("termination_reason", ""),
            "outcome_bucket": row.get("outcome_bucket", ""),
            "min_obstacle_clearance": row.get("min_obstacle_clearance", ""),
            "obstacle_collision_radius": row.get("obstacle_collision_radius", ""),
            "min_clearance_margin": row.get("min_clearance_margin", ""),
            "return": row.get("return", ""),
            "speed_mean": row.get("speed_mean", ""),
            "action_rate_mean": row.get("action_rate_mean", ""),
            "high_sideslip_fraction": row.get("high_sideslip_fraction", ""),
            "beta_abs_error_mean": row.get("beta_abs_error_mean", ""),
            "lateral_rmse": row.get("lateral_rmse", ""),
            "max_off_track_overshoot": row.get("max_off_track_overshoot", ""),
        }
    )
    item.update(dict(telemetry))
    item.update(
        {
            "environment_reset_run": True,
            "environment_step_run": True,
            "policy_action_run": True,
            "policy_rollout_run": True,
            "validation_run": False,
            "training_run": False,
            "replay_run": False,
            "ppo_run": False,
            "ranking_run": False,
            "winner_selected": False,
            "checkpoint_mutated": False,
            "checkpoint_promoted": False,
            "actor_input_contract_changed": False,
            "hidden_oracle_actor_input_required": False,
            "target_labels_actor_visible": False,
            "target_provenance_actor_visible": False,
            "source_labels_actor_visible": False,
            "route_labels_actor_visible": False,
            "outcome_labels_actor_visible": False,
            "success_progress_labels_actor_visible": False,
            "verdict_labels_actor_visible": False,
            "ttc_actor_input_required": False,
            "driver_performance_claim_made": False,
            "repair_success_claim_made": False,
            "robustness_result_claim_made": False,
            "validation_result_claim_made": False,
            "paper_claim_made": False,
            "finite_window_vs_gru_claim_made": False,
            "current_sim_verdict_claim_made": False,
            "high_fidelity_validation_claim_made": False,
            "full_ideal_driver_completion_claim_made": False,
            "feasibility_proof_claim_made": False,
            "level3_self_id_claim_made": False,
            "diagnostic_only_no_verdict": True,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return item


def failure_row(
    *,
    plan: Mapping[str, Any],
    variant: Mapping[str, Any],
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    row = {field: "" for field in FAILURE_FIELDNAMES}
    row.update(_context_fields(plan))
    row.update(
        {
            "counterfactual_episode_id": (
                f"{plan.get('counterfactual_plan_row_id', 'm3153-counterfactual')}-"
                f"{variant.get('variant_id', '')}"
            ),
            "variant_id": variant.get("variant_id", ""),
            "variant_order": variant.get("variant_order", ""),
            "variant_family": variant.get("variant_family", ""),
            "error_type": error_type,
            "error_message": error_message,
            "runtime_base_policy_required": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "repair_success_claim_made": False,
            "validation_run": False,
            "driver_performance_claim_made": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    return row


def run_counterfactual_replay_plan(
    *,
    plan_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    executable_specs: list[dict[str, Any]],
    output_dir: Path,
    next_blocker: str,
) -> dict[str, list[dict[str, Any]]]:
    specs = {
        (str(row.get("task_source_id", "")), str(row.get("executable_source_spec_id", ""))): row
        for row in executable_specs
    }
    profile_cache: dict[tuple[str, str], dict[str, Any]] = {}
    episodes: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for plan in plan_rows:
        for variant in variant_rows:
            try:
                if not _bool(plan.get("status_pass", False)):
                    raise ValueError("M3153 counterfactual replay plan row failed guards")
                spec_key = (str(plan["task_source_id"]), str(plan["executable_source_spec_id"]))
                executable_spec = specs[spec_key]
                profile_name = str(plan["base_profile_name"])
                config_path = str(plan["config_path"])
                cache_key = (profile_name, config_path)
                if cache_key not in profile_cache:
                    profile_cache[cache_key] = m3088.m3075.profile_config_for_runtime(
                        read_json(config_path),
                        profile_name=profile_name,
                    )
                profile_config = profile_cache[cache_key]
                env_config = m3088.env_config_for_executable_profile(
                    executable_spec=executable_spec,
                    profile_config=profile_config,
                )
                env = m3088.wrap_env_with_profile_mask(m3088.AutoDriftEnv(env_config), profile_config)
                policy = M3153CounterfactualPolicy(variant)
                try:
                    if int(env.observation_space.shape[0]) != P0_OBSERVATION_DIM:
                        raise ValueError(f"env observation dim {env.observation_space.shape[0]} != {P0_OBSERVATION_DIM}")
                    if int(env.action_space.shape[0]) != ACTION_DIM:
                        raise ValueError(f"env action dim {env.action_space.shape[0]} != {ACTION_DIM}")
                    raw_row = m3088.run_episode_with_policy(
                        env,
                        policy,
                        str(variant["variant_id"]),
                        int(plan["eval_seed"]),
                    )
                finally:
                    env.close()
                episodes.append(episode_row_from_result(plan=plan, variant=variant, row=raw_row, telemetry=policy.telemetry()))
            except Exception as exc:  # noqa: BLE001 - every scheduled row must be accounted.
                failures.append(
                    failure_row(
                        plan=plan,
                        variant=variant,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
            write_run_state(
                output_dir / "run_state.json",
                {
                    "scheduled_counterfactual_plan_row_count": len(plan_rows),
                    "fixed_variant_row_count": len(variant_rows),
                    "expected_counterfactual_episode_row_count": len(plan_rows) * len(variant_rows),
                    "counterfactual_replay_episode_row_count": len(episodes),
                    "counterfactual_replay_failure_row_count": len(failures),
                    "recorded_row_count": len(episodes) + len(failures),
                    "latest_counterfactual_episode_id": (
                        f"{plan.get('counterfactual_plan_row_id', '')}-{variant.get('variant_id', '')}"
                    ),
                    "complete": False,
                    "next_blocker": next_blocker,
                },
            )
    return {"episodes": episodes, "failures": failures}


def _delta(variant: Mapping[str, Any], reference: Mapping[str, Any], field: str) -> float | str:
    variant_value = _float(variant.get(field))
    reference_value = _float(reference.get(field))
    if np.isfinite(variant_value) and np.isfinite(reference_value):
        return float(variant_value - reference_value)
    return ""


def _counterfactual_label(variant: Mapping[str, Any], reference: Mapping[str, Any]) -> tuple[str, bool]:
    ref_collision = _bool(reference.get("collision", False))
    var_collision = _bool(variant.get("collision", False))
    ref_offtrack = _bool(reference.get("offtrack", False))
    var_offtrack = _bool(variant.get("offtrack", False))
    ref_success = _bool(reference.get("success", False))
    var_success = _bool(variant.get("success", False))
    clearance_delta = _delta(variant, reference, "min_clearance_margin")
    if not ref_success and var_success:
        return "counterfactual_terminal_outcome_changed_to_success_diagnostic", True
    if ref_collision and not var_collision:
        return "counterfactual_collision_removed_or_shifted_diagnostic", True
    if ref_offtrack and not var_offtrack:
        return "counterfactual_offtrack_removed_or_shifted_diagnostic", True
    if isinstance(clearance_delta, float) and clearance_delta >= 0.25:
        return "counterfactual_clearance_margin_improved_diagnostic", True
    if isinstance(clearance_delta, float) and clearance_delta <= -0.25:
        return "counterfactual_clearance_margin_regressed_diagnostic", True
    return "counterfactual_terminal_outcome_unchanged_diagnostic", False


def counterfactual_comparison_rows(episode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reference_by_residual = {
        str(row.get("residual_failure_id", "")): row
        for row in episode_rows
        if str(row.get("variant_id", "")) == REFERENCE_VARIANT_ID
    }
    rows: list[dict[str, Any]] = []
    for episode in sorted(
        [row for row in episode_rows if str(row.get("variant_id", "")) != REFERENCE_VARIANT_ID],
        key=lambda row: (str(row.get("residual_failure_id", "")), str(row.get("variant_id", ""))),
    ):
        reference = reference_by_residual.get(str(episode.get("residual_failure_id", "")), {})
        label, sensitive = _counterfactual_label(episode, reference)
        rows.append(
            {
                "comparison_id": f"m3153-counterfactual-comparison-{len(rows) + 1:04d}",
                "residual_failure_id": episode.get("residual_failure_id", ""),
                "source_measurement_episode_id": episode.get("source_measurement_episode_id", ""),
                "fresh_panel_row_id": episode.get("fresh_panel_row_id", ""),
                "target_failure_kind": episode.get("target_failure_kind", ""),
                "source_m3150_sensitivity_label": episode.get("source_m3150_sensitivity_label", ""),
                "variant_id": episode.get("variant_id", ""),
                "reference_variant_id": REFERENCE_VARIANT_ID,
                "reference_termination_reason": reference.get("termination_reason", ""),
                "variant_termination_reason": episode.get("termination_reason", ""),
                "reference_outcome_bucket": reference.get("outcome_bucket", ""),
                "variant_outcome_bucket": episode.get("outcome_bucket", ""),
                "outcome_bucket_match": reference.get("outcome_bucket", "") == episode.get("outcome_bucket", ""),
                "reference_success": _bool(reference.get("success", False)),
                "variant_success": _bool(episode.get("success", False)),
                "success_delta": int(_bool(episode.get("success", False))) - int(_bool(reference.get("success", False))),
                "reference_collision": _bool(reference.get("collision", False)),
                "variant_collision": _bool(episode.get("collision", False)),
                "collision_delta": int(_bool(episode.get("collision", False))) - int(_bool(reference.get("collision", False))),
                "reference_offtrack": _bool(reference.get("offtrack", False)),
                "variant_offtrack": _bool(episode.get("offtrack", False)),
                "offtrack_delta": int(_bool(episode.get("offtrack", False))) - int(_bool(reference.get("offtrack", False))),
                "reference_min_clearance_margin": reference.get("min_clearance_margin", ""),
                "variant_min_clearance_margin": episode.get("min_clearance_margin", ""),
                "clearance_margin_delta": _delta(episode, reference, "min_clearance_margin"),
                "reference_return": reference.get("return", ""),
                "variant_return": episode.get("return", ""),
                "return_delta": _delta(episode, reference, "return"),
                "reference_speed_mean": reference.get("speed_mean", ""),
                "variant_speed_mean": episode.get("speed_mean", ""),
                "speed_mean_delta": _delta(episode, reference, "speed_mean"),
                "reference_steps": reference.get("steps", ""),
                "variant_steps": episode.get("steps", ""),
                "steps_delta": _delta(episode, reference, "steps"),
                "mean_delta_l1_vs_reference": episode.get("mean_delta_l1_vs_reference", ""),
                "max_delta_abs_vs_reference": episode.get("max_delta_abs_vs_reference", ""),
                "counterfactual_diagnostic_label": label,
                "action_channel_sensitive_diagnostic": sensitive,
                "repair_success_claim_made": False,
                "validation_run": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("fixed_variant_rows", "diagnostic_design", True, "counterfactual_variant_rows.csv"),
        ("counterfactual_replay_episode_rows", "diagnostic_replay", True, "counterfactual_replay_episode_rows.csv"),
        ("counterfactual_replay_failure_rows", "diagnostic_accounting", True, "counterfactual_replay_failure_rows.csv"),
        ("counterfactual_replay_comparison_rows", "diagnostic_comparison", True, "counterfactual_replay_comparison_rows.csv"),
        ("claim_boundary_guards", "guard", True, "claim_boundary_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3154 audit manifest"),
    ]
    blocked = [
        ("repair_implementation", "repair", "future audited repair synthesis route"),
        ("interactive_variant_tuning", "optimization", "future pre-registered repair route if selected"),
        ("per_row_hidden_label_conditioned_actor", "contract", "actor cannot use hidden or outcome labels"),
        ("validation_result", "validation", "future validation route"),
        ("driver_performance_verdict", "driver_performance", "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", "future audited ranking route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair measurement audit"),
        ("robustness_result", "verdict", "future robustness verification route"),
        ("feasibility_proof", "proof", "future feasibility proof route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", "future full goal gate"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("hidden_oracle_actor_inputs", "contract", "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", "actor contract forbids TTC shortcuts"),
        ("runtime_base_policy_dependency", "contract", "direct-action diagnostic variants forbid runtime base policy use"),
    ]
    rows = [
        {
            "claim_id": f"m3153-{claim_id}",
            "claim_family": family,
            "allowed_in_m3153": True,
            "claim_made": made,
            "status_pass": made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, evidence in allowed
    ]
    rows.extend(
        {
            "claim_id": f"m3153-{claim_id}",
            "claim_family": family,
            "allowed_in_m3153": False,
            "claim_made": False,
            "status_pass": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, evidence in blocked
    )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 31540,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3153 counterfactual replay diagnostic artifacts before any repair implementation validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [str(doc_path)],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "counterfactual_variant_rows.csv"),
                str(output_dir / "counterfactual_replay_episode_rows.csv"),
                str(output_dir / "counterfactual_replay_failure_rows.csv"),
                str(output_dir / "counterfactual_replay_comparison_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit M3153 fixed-variant residual counterfactual replay diagnostics"],
            "derived_from": [MILESTONE_ID, M3152_ID, M3151_ID, M3150_ID, M3147_ID],
            "blocked_by": [
                "M3153 diagnostics require audit before any repair or stop decision",
                "counterfactual replay rows are not validation, repair-success, or performance evidence",
            ],
            "supersedes": ["direct interpretation of M3153 replay diagnostics without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3154 must audit M3153 row counts gates actor contract fixed-variant design and claim boundaries",
            "M3154 must preserve obs72/action3 direct [steer throttle brake] contract and runtime_base_policy_required false",
            "M3154 must reject validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3154 must select exactly one next route: stop, synthesis, artifact repair, or bounded repair hypothesis",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun expand tune rank promote validate or mutate checkpoints",
            "do not convert M3153 replay rows into validation driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic",
            "evidence_axis": "residual_action_delta_counterfactual_replay_result_audit",
            "evidence_increment": "audits fixed-variant residual counterfactual replay diagnostics before any repair decision",
            "claim_scope": "Result audit only; no validation ranking promotion performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim",
            "stop_condition": [
                "stop if M3153 artifacts are missing or gate matrix fails",
                "stop if actor or direct-action contracts were violated",
                "synthesize before any repair if replay evidence is mixed or negative",
            ],
            "fallback_plan": [
                "route to M3153 artifact repair if diagnostics are incomplete or contract-unsafe",
                "route to stop or synthesis if action-channel sensitivity is absent or mixed",
                "route to bounded repair synthesis only if audit accepts a fixed actor-visible channel hypothesis",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3153 completes residual action-delta counterfactual replay diagnostic materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3153 counterfactual replay diagnostic artifacts",
            "admission_evidence": ["M3153 summary variant replay comparison gate and claim artifacts"],
            "blocked_shortcuts": [
                "no validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success robustness-result feasibility-proof or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3154 status queue scoreboard research log and review",
                "one follow-up manifest only if M3154 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3154 accepts or rejects M3153 as complete and claim-safe",
                "M3154 selects stop synthesis artifact repair or bounded repair route explicitly",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3154 audits engineering counterfactual replay artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": ["None in M3154; self-ID and GRU comparisons remain auxiliary diagnostics only."],
            "temporal_evidence_window": "M3153 residual counterfactual replay diagnostic artifacts only.",
            "negative_result_policy": "Preserve diagnostic evidence and route to engineering synthesis or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3153 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success robustness-result feasibility-proof or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fixed-variant replay evidence before another repair loop",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3154 audits engineering action-channel sensitivity evidence",
            "must_synthesize_if": [
                "M3154 cannot accept M3153 as complete and claim-safe",
                "M3154 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict robustness-result feasibility-proof or self-ID evidence",
                "M3154 cannot select stop synthesis artifact repair or bounded repair route",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3154 audits M3153 fixed-variant replay row counts gates actor contract and claim boundaries",
            "M3154 rejects validation ranking promotion driver-performance high-fidelity paper full-driver repair-success robustness-result feasibility-proof and self-ID claims",
            "M3154 selects exactly one next route or stop state",
        ],
        "failure_criteria": [
            "M3154 hides M3153 missing rows or missing artifacts",
            "M3154 treats M3153 diagnostics as validation repair-success or performance verdict",
            "M3154 changes actor input or action contract",
            "M3154 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3154 audits M3153 artifacts and selects one next route or stop state while preserving actor direct-action and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [str(output_dir / "summary.json")],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": f"m3153-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _all_forbidden_flags_clear(rows: list[dict[str, Any]]) -> bool:
    return not any(
        _bool(row.get(key, False))
        for row in rows
        for key in (
            "runtime_base_policy_required",
            "hidden_oracle_actor_input_required",
            "ttc_actor_input_required",
            "repair_success_claim_made",
            "validation_run",
            "driver_performance_claim_made",
            "validation_result_claim_made",
            "repair_success_claim_made",
            "robustness_result_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "full_ideal_driver_completion_claim_made",
            "feasibility_proof_claim_made",
            "level3_self_id_claim_made",
            "ranking_run",
            "winner_selected",
            "checkpoint_mutated",
            "checkpoint_promoted",
        )
    )


def required_artifacts_present(paths: Mapping[str, Path]) -> bool:
    late_written = {"summary", "gate_matrix", "doc", "run_state"}
    return all(path.exists() for key, path in paths.items() if key not in late_written)


def gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    plan_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_registered: bool,
) -> list[dict[str, Any]]:
    synthesis_text = str(source.get("m3152_synthesis_text", ""))
    kind_counts = Counter(str(row.get("target_failure_kind", "")) for row in plan_rows)
    episode_counts = Counter(str(row.get("variant_id", "")) for row in episode_rows)
    source_ids = {str(row.get("residual_failure_id", "")) for row in plan_rows}
    episode_source_ids = {str(row.get("residual_failure_id", "")) for row in episode_rows}
    reference_rows = [row for row in episode_rows if str(row.get("variant_id", "")) == REFERENCE_VARIANT_ID]
    sample_actions = [counterfactual_variant_action(_sample_overlay_observation(), variant) for variant in variant_rows]
    combined = variant_rows + episode_rows + failure_rows + comparison_rows
    return [
        gate("source_artifacts_present", "source", all(source["source_exists"].values()), source["source_exists"], "all required sources", "lineage_invalid"),
        gate("m3152_pivots_to_m3153", "lineage", "pivot_to_m3153_bounded_residual_action_delta_counterfactual_replay_diagnostic" in synthesis_text, "pivot marker", "present", "lineage_invalid"),
        gate("m3150_status_pass", "lineage", _bool(source["m3150_summary"].get("status_pass", False)), source["m3150_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3150_gate_matrix_pass", "lineage", _bool(source["m3150_summary"].get("gate_matrix_pass", False)), source["m3150_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3147_status_pass", "lineage", _bool(source["m3147_summary"].get("status_pass", False)), source["m3147_summary"].get("status_pass"), True, "lineage_invalid"),
        gate("m3147_gate_matrix_pass", "lineage", _bool(source["m3147_summary"].get("gate_matrix_pass", False)), source["m3147_summary"].get("gate_matrix_pass"), True, "lineage_invalid"),
        gate("m3150_effectiveness_rows", "source", len(source.get("m3150_effectiveness_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3150_effectiveness_rows", [])), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("m3147_coverage_rows", "source", len(source.get("m3147_coverage_rows", [])) == EXPECTED_RESIDUAL_ROWS, len(source.get("m3147_coverage_rows", [])), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("plan_row_count", "residual", len(plan_rows) == EXPECTED_RESIDUAL_ROWS, len(plan_rows), EXPECTED_RESIDUAL_ROWS, "scenario_sampling_failure"),
        gate("plan_collision_count", "residual", kind_counts.get("collision", 0) == EXPECTED_COLLISION_ROWS, dict(sorted(kind_counts.items())), EXPECTED_COLLISION_ROWS, "scenario_sampling_failure"),
        gate("plan_offtrack_count", "residual", kind_counts.get("offtrack", 0) == EXPECTED_OFFTRACK_ROWS, dict(sorted(kind_counts.items())), EXPECTED_OFFTRACK_ROWS, "scenario_sampling_failure"),
        gate("plan_rows_pass", "residual", all(_bool(row.get("status_pass", False)) for row in plan_rows), "all", "pass", "scenario_sampling_failure"),
        gate("fixed_variant_row_count", "variant", len(variant_rows) == EXPECTED_VARIANT_ROWS, len(variant_rows), EXPECTED_VARIANT_ROWS, "metric_artifact"),
        gate("fixed_variants_predeclared", "variant", all(_bool(row.get("fixed_predeclared", False)) and _bool(row.get("applies_to_all_residual_rows", False)) for row in variant_rows), "all", "fixed and all rows", "contract_violation"),
        gate("reference_variant_present", "variant", any(str(row.get("variant_id", "")) == REFERENCE_VARIANT_ID for row in variant_rows), [row.get("variant_id", "") for row in variant_rows], REFERENCE_VARIANT_ID, "metric_artifact"),
        gate("sample_variant_actions_shape", "contract", all(tuple(payload["action"].shape) == (ACTION_DIM,) for payload in sample_actions), "all", (ACTION_DIM,), "contract_violation"),
        gate("sample_variant_actions_finite_bounded", "contract", all(np.all(np.isfinite(payload["action"])) and float(np.max(np.abs(payload["action"]))) <= 1.0 for payload in sample_actions), "finite bounded", "finite bounded", "contract_violation"),
        gate("episode_rows_accounted", "execution", len(episode_rows) + len(failure_rows) == len(plan_rows) * len(variant_rows), len(episode_rows) + len(failure_rows), len(plan_rows) * len(variant_rows), "metric_artifact"),
        gate("episode_failure_rows", "execution", len(failure_rows) == 0, len(failure_rows), 0, "metric_artifact"),
        gate("episode_variant_coverage", "execution", all(episode_counts.get(str(row.get("variant_id", "")), 0) == len(plan_rows) for row in variant_rows), dict(sorted(episode_counts.items())), "each variant covers all residual rows", "metric_artifact"),
        gate("episode_residual_identity_complete", "execution", episode_source_ids == source_ids, sorted(episode_source_ids), sorted(source_ids), "metric_artifact"),
        gate("reference_episode_rows", "execution", len(reference_rows) == EXPECTED_RESIDUAL_ROWS, len(reference_rows), EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("reference_collision_count", "diagnostic_reference", sum(1 for row in reference_rows if _bool(row.get("collision", False))) == EXPECTED_COLLISION_ROWS, sum(1 for row in reference_rows if _bool(row.get("collision", False))), EXPECTED_COLLISION_ROWS, "behavior_regression"),
        gate("reference_offtrack_count", "diagnostic_reference", sum(1 for row in reference_rows if _bool(row.get("offtrack", False))) == EXPECTED_OFFTRACK_ROWS, sum(1 for row in reference_rows if _bool(row.get("offtrack", False))), EXPECTED_OFFTRACK_ROWS, "behavior_regression"),
        gate("comparison_rows", "diagnostic_comparison", len(comparison_rows) == (EXPECTED_VARIANT_ROWS - 1) * EXPECTED_RESIDUAL_ROWS, len(comparison_rows), (EXPECTED_VARIANT_ROWS - 1) * EXPECTED_RESIDUAL_ROWS, "metric_artifact"),
        gate("claim_boundary_pass", "claim", all(_bool(row.get("status_pass", False)) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("forbidden_flags_clear", "claim", _all_forbidden_flags_clear(combined), "forbidden claim flags", "clear", "contract_violation"),
        gate("required_artifacts_present", "process", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_registered, follow_up_manifest_registered, True, "lineage_invalid"),
    ]


def render_doc(summary: Mapping[str, Any]) -> str:
    terminal_lines = [
        f"- {variant}: {counts}"
        for variant, counts in sorted(dict(summary.get("variant_terminal_counts", {})).items())
    ]
    sensitivity_lines = [
        f"- {label}: {count}" for label, count in sorted(dict(summary.get("counterfactual_diagnostic_label_counts", {})).items())
    ]
    return "\n".join(
        [
            "# M3153 Residual Action-Delta Counterfactual Replay Diagnostic",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result class: `{summary['result_class']}`",
            f"- residual replay plan rows: {summary['counterfactual_plan_row_count']}/{summary['target_residual_row_count']}",
            f"- fixed variant rows: {summary['fixed_variant_row_count']}",
            f"- counterfactual episode rows: {summary['counterfactual_replay_episode_row_count']}",
            f"- counterfactual failure rows: {summary['counterfactual_replay_failure_row_count']}",
            f"- comparison rows: {summary['counterfactual_replay_comparison_row_count']}",
            f"- action-channel-sensitive diagnostic comparisons: {summary['action_channel_sensitive_comparison_count']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Variant Terminal Counts",
            "",
            *(terminal_lines or ["- none: 0"]),
            "",
            "## Diagnostic Labels",
            "",
            *(sensitivity_lines or ["- none: 0"]),
            "",
            "## Interpretation",
            "",
            "M3153 replays only the seven residual rows with fixed predeclared actor-visible direct-action variants. The replay rows diagnose whether residual terminal behavior is sensitive to bounded action-channel changes. They are not a repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
        ]
    )


def run_counterfactual_replay_diagnostic_preflight(
    *,
    m3152_synthesis: Path,
    m3150_dir: Path,
    m3147_dir: Path,
    m3012_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3152_synthesis=m3152_synthesis,
        m3150_dir=m3150_dir,
        m3147_dir=m3147_dir,
        m3012_dir=m3012_dir,
    )
    plan_rows = counterfactual_replay_plan(source)
    variant_rows = fixed_variant_rows()
    replay = run_counterfactual_replay_plan(
        plan_rows=plan_rows,
        variant_rows=variant_rows,
        executable_specs=source["m3012_executable_specs"],
        output_dir=output_dir,
        next_blocker=NEXT_ID,
    )
    episode_rows = replay["episodes"]
    failure_rows = replay["failures"]
    comparison_rows = counterfactual_comparison_rows(episode_rows)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))
    claim_rows = claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    for path, rows, fieldnames in (
        (paths["counterfactual_variant_rows"], variant_rows, VARIANT_FIELDNAMES),
        (paths["counterfactual_replay_episode_rows"], episode_rows, EPISODE_FIELDNAMES),
        (paths["counterfactual_replay_failure_rows"], failure_rows, FAILURE_FIELDNAMES),
        (paths["counterfactual_replay_comparison_rows"], comparison_rows, COMPARISON_FIELDNAMES),
        (paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES),
    ):
        write_csv_rows(path, rows, fieldnames=fieldnames)
    present = required_artifacts_present(paths)
    gates = gate_matrix_rows(
        source=source,
        plan_rows=plan_rows,
        variant_rows=variant_rows,
        episode_rows=episode_rows,
        failure_rows=failure_rows,
        comparison_rows=comparison_rows,
        claim_rows=claim_rows,
        required_artifacts_present=present,
        follow_up_manifest_registered=paths["follow_up_manifest"].exists(),
    )
    write_csv_rows(paths["gate_matrix"], gates, fieldnames=GATE_FIELDNAMES)
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gates)
    status_pass = bool(gate_matrix_pass and present)
    variant_terminal_counts: dict[str, dict[str, int]] = {}
    for variant in variant_rows:
        variant_id = str(variant["variant_id"])
        rows = [row for row in episode_rows if str(row.get("variant_id", "")) == variant_id]
        variant_terminal_counts[variant_id] = {
            "success": sum(1 for row in rows if _bool(row.get("success", False))),
            "collision": sum(1 for row in rows if _bool(row.get("collision", False))),
            "offtrack": sum(1 for row in rows if _bool(row.get("offtrack", False))),
            "speed_too_low": sum(1 for row in rows if str(row.get("termination_reason", "")) == "speed_too_low"),
        }
    diagnostic_labels = Counter(str(row.get("counterfactual_diagnostic_label", "")) for row in comparison_rows)
    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "result_class": (
            "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_pass"
            if status_pass
            else "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_fail"
        ),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "target_residual_row_count": EXPECTED_RESIDUAL_ROWS,
        "counterfactual_plan_row_count": len(plan_rows),
        "fixed_variant_row_count": len(variant_rows),
        "expected_counterfactual_episode_row_count": len(plan_rows) * len(variant_rows),
        "counterfactual_replay_episode_row_count": len(episode_rows),
        "counterfactual_replay_failure_row_count": len(failure_rows),
        "counterfactual_replay_comparison_row_count": len(comparison_rows),
        "action_channel_sensitive_comparison_count": sum(
            1 for row in comparison_rows if _bool(row.get("action_channel_sensitive_diagnostic", False))
        ),
        "variant_terminal_counts": variant_terminal_counts,
        "counterfactual_diagnostic_label_counts": dict(sorted(diagnostic_labels.items())),
        "reference_variant_id": REFERENCE_VARIANT_ID,
        "reference_terminal_counts": variant_terminal_counts.get(REFERENCE_VARIANT_ID, {}),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(_bool(row.get("status_pass", False)) for row in claim_rows),
        "gate_matrix_row_count": len(gates),
        "required_artifacts_present": present,
        "m3150_status_pass": _bool(source["m3150_summary"].get("status_pass", False)),
        "m3150_gate_matrix_pass": _bool(source["m3150_summary"].get("gate_matrix_pass", False)),
        "m3147_status_pass": _bool(source["m3147_summary"].get("status_pass", False)),
        "m3147_gate_matrix_pass": _bool(source["m3147_summary"].get("gate_matrix_pass", False)),
        "candidate_output_semantics": m3142.OUTPUT_SEMANTICS,
        "candidate_output_components": list(m3142.ACTION_COMPONENTS),
        "runtime_base_policy_required": False,
        "checkpoint_model_required": False,
        "recurrent_hidden_state_required": False,
        "fixed_predeclared_variants": True,
        "per_row_hidden_label_conditioned_actor": False,
        "environment_reset_run": bool(episode_rows),
        "environment_step_run": bool(episode_rows),
        "policy_action_run": bool(episode_rows),
        "policy_rollout_run": bool(episode_rows),
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "repair_materialization_run": False,
        "repair_success_claim_made": False,
        "robustness_result_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "feasibility_proof_claim_made": False,
        "level3_self_id_claim_made": False,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "decision": "active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_route_to_m3154_result_audit",
        "next_blocker": NEXT_ID,
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    write_json(paths["summary"], summary)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "scheduled_counterfactual_plan_row_count": len(plan_rows),
            "fixed_variant_row_count": len(variant_rows),
            "counterfactual_replay_episode_row_count": len(episode_rows),
            "counterfactual_replay_failure_row_count": len(failure_rows),
            "counterfactual_replay_comparison_row_count": len(comparison_rows),
            "complete": status_pass,
            "status_pass": status_pass,
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3152-synthesis", type=Path, default=DEFAULT_M3152_SYNTHESIS)
    parser.add_argument("--m3150-dir", type=Path, default=DEFAULT_M3150_DIR)
    parser.add_argument("--m3147-dir", type=Path, default=DEFAULT_M3147_DIR)
    parser.add_argument("--m3012-dir", type=Path, default=DEFAULT_M3012_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_counterfactual_replay_diagnostic_preflight(
        m3152_synthesis=args.m3152_synthesis,
        m3150_dir=args.m3150_dir,
        m3147_dir=args.m3147_dir,
        m3012_dir=args.m3012_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"counterfactual_plan_rows={summary['counterfactual_plan_row_count']}")
    print(f"fixed_variant_rows={summary['fixed_variant_row_count']}")
    print(f"counterfactual_replay_episode_rows={summary['counterfactual_replay_episode_row_count']}")
    print(f"counterfactual_replay_failures={summary['counterfactual_replay_failure_row_count']}")
    print(f"action_channel_sensitive_comparisons={summary['action_channel_sensitive_comparison_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
