"""Reset-only scenario-distribution support atlas for M2468."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.config import build_env_config, env_config_to_dict
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.env import AutoDriftEnv


DEFAULT_M2455_DIR = Path(
    "runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight"
)
DEFAULT_M2466_DIR = Path(
    "runs/m2466_paper_route_current_sim_dual_axis_scenario_quality_r1_reset_sampling_diagnostic_panel"
)
DEFAULT_M2467_DOC = Path(
    "docs/m2467-paper-route-current-sim-dual-axis-scenario-quality-r1-reset-sampling-diagnostic-panel-result-audit.md"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2468_paper_route_current_sim_dual_axis_scenario_distribution_support_atlas")
DEFAULT_SEED_BASE = 246800
DEFAULT_SEEDS_PER_CELL = 8
DEFAULT_EXPECTED_OBSERVATION_DIM = 72
DEFAULT_NEXT_BLOCKER = "m2469-paper-route-current-sim-dual-axis-scenario-distribution-support-atlas-result-audit"

RESULT_COMPLETE = "scenario_distribution_support_atlas_complete"
RESULT_FAIL = "scenario_distribution_support_atlas_fail"

BASE_HUMAN_VIEW_CONTRACT: dict[str, Any] = {
    "history_length": 1,
    "action_history_mode": "full",
    "include_privileged_params": False,
    "wheel_observation_mode": "none",
    "obstacle_relative_velocity_mode": "zero",
}

DEFAULT_RANDOMIZATION = {
    "mu_range": [0.25, 1.15],
    "mass_scale_range": [0.85, 1.2],
    "cg_shift_range": [-0.12, 0.12],
    "inertia_scale_range": [0.85, 1.25],
    "tire_stiffness_scale_range": [0.65, 1.35],
    "drive_scale_range": [0.8, 1.15],
    "brake_scale_range": [0.8, 1.15],
    "actuator_tau_scale_range": [0.75, 1.75],
}

NOMINAL_RANDOMIZATION = {
    "mu_range": [0.9, 0.9],
    "mass_scale_range": [1.0, 1.0],
    "cg_shift_range": [0.0, 0.0],
    "inertia_scale_range": [1.0, 1.0],
    "tire_stiffness_scale_range": [1.0, 1.0],
    "drive_scale_range": [1.0, 1.0],
    "brake_scale_range": [1.0, 1.0],
    "actuator_tau_scale_range": [1.0, 1.0],
}

FIXED_M2464_R1_SIGNATURE = {
    "speed_range": [10.0, 14.0],
    "obstacle_distance_range": [20.0, 34.0],
    "obstacle_lateral_offset_range": [-0.4, 0.4],
    "obstacle_half_width_range": [0.55, 0.8],
    "obstacle_allowed_labels": ["aes_feasible"],
    "obstacle_require_aeb_infeasible": True,
    "obstacle_max_threshold_score": 0.35,
}

ATLAS_CELL_FIELDNAMES = [
    "atlas_cell_id",
    "role_family",
    "candidate_group",
    "parameter_bin",
    "hidden_dynamics_bucket",
    "sampled_obstacle_label_scope",
    "source_candidate_ids",
    "source_candidate_count",
    "split_scope",
    "effective_env_config_path",
    "actor_contract_guardrail_pass",
    "matches_fixed_m2464_r1_overlay",
    "diagnostic_only",
    "repair_candidate",
    "ranking_admissible",
    "winner_selected",
    "promoted",
    "cell_description",
]

RESET_ROW_FIELDNAMES = [
    "atlas_cell_id",
    "role_family",
    "candidate_group",
    "parameter_bin",
    "hidden_dynamics_bucket",
    "sampled_obstacle_label_scope",
    "reset_attempt_id",
    "reset_seed_index",
    "eval_seed",
    "effective_env_config_path",
    "environment_load_attempted",
    "environment_reset_attempted",
    "reset_success",
    "observation_length",
    "expected_observation_length",
    "observation_dimension_matches_expected",
    "observation_finite",
    "obstacle_initialized",
    "obstacle_label",
    "initial_mu",
    "mu",
    "mass_scale",
    "tire_stiffness_scale",
    "brake_scale",
    "steer_tau_scale",
    "drive_tau_scale",
    "speed_ref",
    "obstacle_distance",
    "obstacle_lateral_offset",
    "obstacle_half_width",
    "obstacle_threshold_score",
    "environment_step_count",
    "policy_action_executed",
    "environment_rollout_started",
    "measured_rollout_started",
    "repair_execution_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "active_config_overwritten",
    "actor_input_contract_changed",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
    "failure_type",
    "failure_reason",
]

CELL_SUMMARY_FIELDNAMES = [
    "atlas_cell_id",
    "role_family",
    "candidate_group",
    "parameter_bin",
    "hidden_dynamics_bucket",
    "sampled_obstacle_label_scope",
    "reset_attempt_count",
    "reset_success_count",
    "reset_failure_count",
    "reset_success_rate",
    "observation_dimension_failure_count",
    "obstacle_initialized_count",
    "failure_type_counts",
    "obstacle_label_counts",
    "support_class",
]

GROUP_SUMMARY_FIELDNAMES = [
    "candidate_group",
    "cell_count",
    "reset_attempt_count",
    "reset_success_count",
    "reset_failure_count",
    "reset_success_rate",
    "support_classes",
]

CLASSIFICATION_FIELDNAMES = ["classification_key", "classification_value", "admissible", "reason"]
GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_class",
    "source_role_or_axis",
    "failure_mode_to_preserve",
    "metric_to_watch",
    "value",
    "violation",
    "reason",
]
CLAIM_FIELDNAMES = ["claim_key", "claim_value", "admissible", "reason"]
DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _as_float(value: Any) -> float | str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return number if np.isfinite(number) else ""


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")
    return safe or "atlas_cell"


def _observation_length(obs: Any) -> int:
    array = np.asarray(obs, dtype=np.float64)
    if array.ndim == 0:
        return 0
    return int(array.size)


def _finite_observation(obs: Any) -> bool:
    try:
        array = np.asarray(obs, dtype=np.float64)
    except (TypeError, ValueError):
        return False
    return bool(array.size > 0 and np.all(np.isfinite(array)))


def _config_to_dict(config: Any, fallback: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return env_config_to_dict(config)
    except TypeError:
        data = getattr(config, "data", None)
        if isinstance(data, Mapping):
            return dict(data)
        return dict(fallback)


def _actor_contract_guardrail_pass(config: Mapping[str, Any]) -> bool:
    obstacle = config.get("obstacle", {})
    return (
        int(config.get("history_length", -1)) == 1
        and str(config.get("action_history_mode", "")) == "full"
        and not _bool(config.get("include_privileged_params"), default=True)
        and str(config.get("wheel_observation_mode", "")) == "none"
        and str(config.get("obstacle_relative_velocity_mode", "")) == "zero"
        and isinstance(obstacle, Mapping)
        and _bool(obstacle.get("enabled"))
    )


def _source_candidate_ids(candidate_rows: Sequence[Mapping[str, Any]], group: str) -> list[str]:
    return sorted(str(row.get("candidate_id", "")) for row in candidate_rows if str(row.get("candidate_group", "")) == group)


def _all_source_candidate_ids(candidate_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted(str(row.get("candidate_id", "")) for row in candidate_rows if str(row.get("candidate_id", "")))


def _env_config(
    *,
    speed_range: Sequence[float],
    allowed_labels: Sequence[str],
    distance_range: Sequence[float],
    lateral_offset_range: Sequence[float],
    half_width_range: Sequence[float],
    require_aeb_infeasible: bool,
    max_threshold_score: float | None,
    randomization: Mapping[str, Any],
    perception_reveal_distance: float,
    track_width: float = 7.5,
) -> dict[str, Any]:
    return {
        **BASE_HUMAN_VIEW_CONTRACT,
        "track_width": float(track_width),
        "speed_range": [float(speed_range[0]), float(speed_range[1])],
        "friction_limited_speed": False,
        "soft_offtrack_metric_enabled": True,
        "soft_offtrack_tolerance_m": 0.2,
        "randomization": deepcopy(dict(randomization)),
        "obstacle": {
            "enabled": True,
            "allowed_labels": list(allowed_labels),
            "distance_range": [float(distance_range[0]), float(distance_range[1])],
            "lateral_offset_range": [float(lateral_offset_range[0]), float(lateral_offset_range[1])],
            "half_width_range": [float(half_width_range[0]), float(half_width_range[1])],
            "require_aeb_infeasible": bool(require_aeb_infeasible),
            "max_threshold_score": max_threshold_score,
            "max_sample_attempts": 10000,
            "perception_reveal_step": 0,
            "perception_reveal_distance": float(perception_reveal_distance),
            "finish_on_pass": True,
            "finish_pass_distance": 1.0,
        },
    }


def _cell(
    *,
    atlas_cell_id: str,
    role_family: str,
    candidate_group: str,
    parameter_bin: str,
    hidden_dynamics_bucket: str,
    sampled_obstacle_label_scope: str,
    source_candidate_ids: Sequence[str],
    split_scope: str,
    config: Mapping[str, Any],
    cell_description: str,
) -> dict[str, Any]:
    return {
        "atlas_cell_id": atlas_cell_id,
        "role_family": role_family,
        "candidate_group": candidate_group,
        "parameter_bin": parameter_bin,
        "hidden_dynamics_bucket": hidden_dynamics_bucket,
        "sampled_obstacle_label_scope": sampled_obstacle_label_scope,
        "source_candidate_ids": list(source_candidate_ids),
        "split_scope": split_scope,
        "config": deepcopy(dict(config)),
        "cell_description": cell_description,
    }


def _atlas_cell_specs(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    stable = _source_candidate_ids(candidate_rows, "stable_feasibility_support")
    aes = _source_candidate_ids(candidate_rows, "stable_aes_support")
    handling = _source_candidate_ids(candidate_rows, "handling_limit_guardrail")
    hidden = _source_candidate_ids(candidate_rows, "hidden_dynamics_guardrail")
    mitigation = _source_candidate_ids(candidate_rows, "mitigation_guardrail")
    all_sources = _all_source_candidate_ids(candidate_rows)

    low_mu = {**DEFAULT_RANDOMIZATION, "mu_range": [0.3, 0.5]}
    weak_brake = {**DEFAULT_RANDOMIZATION, "brake_scale_range": [0.55, 0.75]}
    slow_steer = {**DEFAULT_RANDOMIZATION, "actuator_tau_scale_range": [1.5, 2.2]}

    return [
        _cell(
            atlas_cell_id="stable_avoidable_nominal_center",
            role_family="R0_stable_avoidable",
            candidate_group="stable_feasibility_support",
            parameter_bin="stable_center_reaction_distance",
            hidden_dynamics_bucket="nominal",
            sampled_obstacle_label_scope="aeb_feasible",
            source_candidate_ids=stable,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[8.0, 12.0],
                allowed_labels=["aeb_feasible"],
                distance_range=[36.0, 54.0],
                lateral_offset_range=[-0.25, 0.25],
                half_width_range=[0.45, 0.7],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=NOMINAL_RANDOMIZATION,
                perception_reveal_distance=70.0,
            ),
            cell_description="R0 nominal stable avoidable support away from the fixed R1 rows.",
        ),
        _cell(
            atlas_cell_id="stable_avoidable_lateral_span",
            role_family="R0_stable_avoidable",
            candidate_group="stable_feasibility_support",
            parameter_bin="stable_lateral_offset_span",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="aeb_feasible",
            source_candidate_ids=stable,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[8.0, 12.0],
                allowed_labels=["aeb_feasible"],
                distance_range=[34.0, 56.0],
                lateral_offset_range=[-0.8, 0.8],
                half_width_range=[0.45, 0.75],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=70.0,
            ),
            cell_description="R0 lateral-offset support bin.",
        ),
        _cell(
            atlas_cell_id="stable_avoidable_low_mu",
            role_family="R0_stable_avoidable",
            candidate_group="stable_feasibility_support",
            parameter_bin="stable_low_mu_long_distance",
            hidden_dynamics_bucket="low_mu",
            sampled_obstacle_label_scope="aeb_feasible",
            source_candidate_ids=stable,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[7.0, 10.0],
                allowed_labels=["aeb_feasible"],
                distance_range=[38.0, 58.0],
                lateral_offset_range=[-0.4, 0.4],
                half_width_range=[0.45, 0.7],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=low_mu,
                perception_reveal_distance=75.0,
            ),
            cell_description="R0 low-mu support bin with longer reaction distance.",
        ),
        _cell(
            atlas_cell_id="stable_aes_broad_threshold_free",
            role_family="R1_aeb_infeasible_stable_aes",
            candidate_group="stable_aes_support",
            parameter_bin="aes_broad_threshold_free",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="aes_feasible",
            source_candidate_ids=aes,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[10.0, 15.0],
                allowed_labels=["aes_feasible"],
                distance_range=[16.0, 40.0],
                lateral_offset_range=[-0.7, 0.7],
                half_width_range=[0.45, 0.95],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=60.0,
            ),
            cell_description="R1 broad support bin, not the M2464 fixed overlay.",
        ),
        _cell(
            atlas_cell_id="stable_aes_threshold_band",
            role_family="R1_aeb_infeasible_stable_aes",
            candidate_group="stable_aes_support",
            parameter_bin="aes_threshold_band_0p6",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="aes_feasible",
            source_candidate_ids=aes,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[10.0, 14.5],
                allowed_labels=["aes_feasible"],
                distance_range=[18.0, 38.0],
                lateral_offset_range=[-0.6, 0.6],
                half_width_range=[0.45, 0.85],
                require_aeb_infeasible=True,
                max_threshold_score=0.6,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=60.0,
            ),
            cell_description="R1 threshold-band atlas bin broader than the fixed M2464 R1 overlay.",
        ),
        _cell(
            atlas_cell_id="stable_aes_low_mu_near",
            role_family="R1_aeb_infeasible_stable_aes",
            candidate_group="stable_aes_support",
            parameter_bin="aes_low_mu_near",
            hidden_dynamics_bucket="low_mu",
            sampled_obstacle_label_scope="aes_feasible",
            source_candidate_ids=aes,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[8.0, 12.0],
                allowed_labels=["aes_feasible"],
                distance_range=[14.0, 32.0],
                lateral_offset_range=[-0.7, 0.7],
                half_width_range=[0.45, 0.85],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=low_mu,
                perception_reveal_distance=55.0,
            ),
            cell_description="R1 low-mu near-field support bin.",
        ),
        _cell(
            atlas_cell_id="drift_required_nominal",
            role_family="R2_handling_limit_drift_capable_avoidance",
            candidate_group="handling_limit_guardrail",
            parameter_bin="drift_required_nominal",
            hidden_dynamics_bucket="nominal",
            sampled_obstacle_label_scope="drift_required",
            source_candidate_ids=handling,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[12.0, 18.0],
                allowed_labels=["drift_required"],
                distance_range=[10.0, 26.0],
                lateral_offset_range=[-1.0, 1.0],
                half_width_range=[0.75, 1.25],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=NOMINAL_RANDOMIZATION,
                perception_reveal_distance=55.0,
            ),
            cell_description="Drift-required handling-limit support bin.",
        ),
        _cell(
            atlas_cell_id="drift_required_late_boundary",
            role_family="R3_recovery_after_limit",
            candidate_group="handling_limit_guardrail",
            parameter_bin="drift_required_late_boundary",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="drift_required",
            source_candidate_ids=handling,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[13.0, 19.0],
                allowed_labels=["drift_required"],
                distance_range=[8.0, 24.0],
                lateral_offset_range=[-1.2, 1.2],
                half_width_range=[0.75, 1.35],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=50.0,
            ),
            cell_description="Late handling-limit boundary support bin.",
        ),
        _cell(
            atlas_cell_id="drift_required_low_mu",
            role_family="R5_hidden_dynamics_robustness",
            candidate_group="handling_limit_guardrail",
            parameter_bin="drift_required_low_mu",
            hidden_dynamics_bucket="low_mu",
            sampled_obstacle_label_scope="drift_required",
            source_candidate_ids=handling,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[9.0, 15.0],
                allowed_labels=["drift_required"],
                distance_range=[8.0, 24.0],
                lateral_offset_range=[-1.1, 1.1],
                half_width_range=[0.7, 1.3],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=low_mu,
                perception_reveal_distance=50.0,
            ),
            cell_description="Low-mu drift-required support bin.",
        ),
        _cell(
            atlas_cell_id="unavoidable_close",
            role_family="R4_unavoidable_mitigation",
            candidate_group="mitigation_guardrail",
            parameter_bin="unavoidable_close",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="unavoidable",
            source_candidate_ids=mitigation,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[12.0, 18.0],
                allowed_labels=["unavoidable"],
                distance_range=[6.0, 18.0],
                lateral_offset_range=[-0.8, 0.8],
                half_width_range=[0.9, 1.5],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=45.0,
            ),
            cell_description="Unavoidable close-range mitigation support bin.",
        ),
        _cell(
            atlas_cell_id="unavoidable_high_speed",
            role_family="R4_unavoidable_mitigation",
            candidate_group="mitigation_guardrail",
            parameter_bin="unavoidable_high_speed",
            hidden_dynamics_bucket="mixed",
            sampled_obstacle_label_scope="unavoidable",
            source_candidate_ids=mitigation,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[16.0, 22.0],
                allowed_labels=["unavoidable"],
                distance_range=[8.0, 22.0],
                lateral_offset_range=[-0.8, 0.8],
                half_width_range=[0.85, 1.45],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=DEFAULT_RANDOMIZATION,
                perception_reveal_distance=45.0,
            ),
            cell_description="Unavoidable high-speed mitigation support bin.",
        ),
        _cell(
            atlas_cell_id="unavoidable_low_mu",
            role_family="R4_unavoidable_mitigation",
            candidate_group="mitigation_guardrail",
            parameter_bin="unavoidable_low_mu",
            hidden_dynamics_bucket="low_mu",
            sampled_obstacle_label_scope="unavoidable",
            source_candidate_ids=mitigation,
            split_scope="public_debug",
            config=_env_config(
                speed_range=[10.0, 16.0],
                allowed_labels=["unavoidable"],
                distance_range=[6.0, 20.0],
                lateral_offset_range=[-1.0, 1.0],
                half_width_range=[0.9, 1.5],
                require_aeb_infeasible=True,
                max_threshold_score=None,
                randomization=low_mu,
                perception_reveal_distance=45.0,
            ),
            cell_description="Low-mu unavoidable mitigation support bin.",
        ),
        _cell(
            atlas_cell_id="hidden_nominal_neighbor",
            role_family="R5_hidden_dynamics_robustness",
            candidate_group="hidden_dynamics_guardrail",
            parameter_bin="all_labels_nominal_neighbor",
            hidden_dynamics_bucket="nominal_neighbor",
            sampled_obstacle_label_scope="all_labels",
            source_candidate_ids=hidden or all_sources,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[8.0, 16.0],
                allowed_labels=["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"],
                distance_range=[12.0, 56.0],
                lateral_offset_range=[-1.0, 1.0],
                half_width_range=[0.45, 1.2],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=NOMINAL_RANDOMIZATION,
                perception_reveal_distance=65.0,
            ),
            cell_description="Nominal all-label support baseline for hidden-dynamics guardrail bins.",
        ),
        _cell(
            atlas_cell_id="hidden_weak_brake",
            role_family="R5_hidden_dynamics_robustness",
            candidate_group="hidden_dynamics_guardrail",
            parameter_bin="all_labels_weak_brake",
            hidden_dynamics_bucket="weak_brake",
            sampled_obstacle_label_scope="all_labels",
            source_candidate_ids=hidden or all_sources,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[8.0, 16.0],
                allowed_labels=["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"],
                distance_range=[12.0, 56.0],
                lateral_offset_range=[-1.0, 1.0],
                half_width_range=[0.45, 1.2],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=weak_brake,
                perception_reveal_distance=65.0,
            ),
            cell_description="Weak-brake all-label sampler support bin.",
        ),
        _cell(
            atlas_cell_id="hidden_slow_steer",
            role_family="R5_hidden_dynamics_robustness",
            candidate_group="hidden_dynamics_guardrail",
            parameter_bin="all_labels_slow_steer",
            hidden_dynamics_bucket="slow_steer_actuator",
            sampled_obstacle_label_scope="all_labels",
            source_candidate_ids=hidden or all_sources,
            split_scope="public_debug_or_gate",
            config=_env_config(
                speed_range=[8.0, 16.0],
                allowed_labels=["aeb_feasible", "aes_feasible", "drift_required", "unavoidable"],
                distance_range=[12.0, 56.0],
                lateral_offset_range=[-1.0, 1.0],
                half_width_range=[0.45, 1.2],
                require_aeb_infeasible=False,
                max_threshold_score=None,
                randomization=slow_steer,
                perception_reveal_distance=65.0,
            ),
            cell_description="Slow-steer all-label sampler support bin.",
        ),
    ]


def _matches_fixed_m2464_r1(config: Mapping[str, Any]) -> bool:
    obstacle = config.get("obstacle", {})
    if not isinstance(obstacle, Mapping):
        return False
    return (
        list(config.get("speed_range", [])) == FIXED_M2464_R1_SIGNATURE["speed_range"]
        and list(obstacle.get("distance_range", [])) == FIXED_M2464_R1_SIGNATURE["obstacle_distance_range"]
        and list(obstacle.get("lateral_offset_range", []))
        == FIXED_M2464_R1_SIGNATURE["obstacle_lateral_offset_range"]
        and list(obstacle.get("half_width_range", [])) == FIXED_M2464_R1_SIGNATURE["obstacle_half_width_range"]
        and list(obstacle.get("allowed_labels", [])) == FIXED_M2464_R1_SIGNATURE["obstacle_allowed_labels"]
        and bool(obstacle.get("require_aeb_infeasible")) is True
        and obstacle.get("max_threshold_score") == FIXED_M2464_R1_SIGNATURE["obstacle_max_threshold_score"]
    )


def _write_effective_config(
    *,
    output_dir: Path,
    cell: Mapping[str, Any],
    effective_config: Mapping[str, Any],
) -> Path:
    path = output_dir / "effective_env_configs" / f"{_safe_id(str(cell['atlas_cell_id']))}.json"
    write_json(
        path,
        {
            "atlas_cell_id": str(cell["atlas_cell_id"]),
            "role_family": str(cell["role_family"]),
            "candidate_group": str(cell["candidate_group"]),
            "parameter_bin": str(cell["parameter_bin"]),
            "hidden_dynamics_bucket": str(cell["hidden_dynamics_bucket"]),
            "sampled_obstacle_label_scope": str(cell["sampled_obstacle_label_scope"]),
            "source_candidate_ids": list(cell.get("source_candidate_ids", [])),
            "diagnostic_only": True,
            "repair_candidate": False,
            "ranking_admissible": False,
            "winner_selected": False,
            "promoted": False,
            "matches_fixed_m2464_r1_overlay": _matches_fixed_m2464_r1(effective_config),
            "effective_env_config": dict(effective_config),
            "claim_boundary": {
                "active_config_overwritten": False,
                "environment_step_count": 0,
                "policy_action_executed": False,
                "environment_rollout_started": False,
                "measured_rollout_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
        },
    )
    return path


def _reset_row(
    *,
    cell: Mapping[str, Any],
    config: Any,
    effective_config_path: Path,
    eval_seed: int,
    reset_seed_index: int,
    expected_observation_dim: int,
) -> dict[str, Any]:
    failure_type = ""
    failure_reason = ""
    environment_load_attempted = False
    environment_reset_attempted = False
    reset_success = False
    observation_length = 0
    observation_finite = False
    dimension_matches = False
    obstacle_initialized = False
    obstacle_label = ""
    environment_step_count = 0
    info: Mapping[str, Any] = {}
    env: Any | None = None
    try:
        environment_load_attempted = True
        env = AutoDriftEnv(config)
        environment_reset_attempted = True
        obs, reset_info = env.reset(seed=int(eval_seed))
        info = reset_info if isinstance(reset_info, Mapping) else {}
        observation_length = _observation_length(obs)
        observation_finite = _finite_observation(obs)
        dimension_matches = observation_length == int(expected_observation_dim)
        obstacle_scenario = getattr(env, "obstacle_scenario", None)
        obstacle_initialized = obstacle_scenario is not None
        obstacle_label = str(getattr(obstacle_scenario, "label", "") or info.get("obstacle_label", ""))
        environment_step_count = int(getattr(env, "step_count", 0))
        failures: list[str] = []
        if not observation_finite:
            failures.append("observation_non_finite")
        if not dimension_matches:
            failures.append(f"observation_length_{observation_length}_not_{expected_observation_dim}")
        if not obstacle_initialized:
            failures.append("obstacle_initialized_false")
        if environment_step_count != 0:
            failures.append("environment_step_count_nonzero")
        if failures:
            failure_type = "behavior_regression"
            failure_reason = "|".join(failures)
        else:
            reset_success = True
    except Exception as exc:  # noqa: BLE001 - reset diagnostics preserve exact exception text.
        failure_type = "scenario_sampling_failure"
        failure_reason = f"{type(exc).__name__}:{exc}"
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()

    return {
        "atlas_cell_id": str(cell["atlas_cell_id"]),
        "role_family": str(cell["role_family"]),
        "candidate_group": str(cell["candidate_group"]),
        "parameter_bin": str(cell["parameter_bin"]),
        "hidden_dynamics_bucket": str(cell["hidden_dynamics_bucket"]),
        "sampled_obstacle_label_scope": str(cell["sampled_obstacle_label_scope"]),
        "reset_attempt_id": f"{cell['atlas_cell_id']}_seed_{reset_seed_index:03d}",
        "reset_seed_index": int(reset_seed_index),
        "eval_seed": int(eval_seed),
        "effective_env_config_path": str(effective_config_path),
        "environment_load_attempted": environment_load_attempted,
        "environment_reset_attempted": environment_reset_attempted,
        "reset_success": reset_success,
        "observation_length": observation_length,
        "expected_observation_length": int(expected_observation_dim),
        "observation_dimension_matches_expected": dimension_matches,
        "observation_finite": observation_finite,
        "obstacle_initialized": obstacle_initialized,
        "obstacle_label": obstacle_label,
        "initial_mu": _as_float(info.get("initial_mu")),
        "mu": _as_float(info.get("mu", info.get("initial_mu"))),
        "mass_scale": _as_float(info.get("mass_scale")),
        "tire_stiffness_scale": _as_float(info.get("tire_stiffness_scale")),
        "brake_scale": _as_float(info.get("brake_scale")),
        "steer_tau_scale": _as_float(info.get("steer_tau_scale")),
        "drive_tau_scale": _as_float(info.get("drive_tau_scale")),
        "speed_ref": _as_float(info.get("speed_ref")),
        "obstacle_distance": _as_float(info.get("obstacle_distance")),
        "obstacle_lateral_offset": _as_float(info.get("obstacle_lateral_offset")),
        "obstacle_half_width": _as_float(info.get("active_obstacle_half_width")),
        "obstacle_threshold_score": _as_float(info.get("obstacle_threshold_score")),
        "environment_step_count": environment_step_count,
        "policy_action_executed": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "failure_type": failure_type,
        "failure_reason": failure_reason,
    }


def _support_class(success_count: int, attempt_count: int) -> str:
    if attempt_count <= 0:
        return "not_attempted"
    if success_count == attempt_count:
        return "reset_support_full"
    if success_count == 0:
        return "reset_support_absent"
    return "reset_support_partial"


def _cell_summary_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for cell_id in sorted({str(row.get("atlas_cell_id", "")) for row in rows}):
        cell_rows = [row for row in rows if str(row.get("atlas_cell_id", "")) == cell_id]
        success_count = sum(_bool(row.get("reset_success")) for row in cell_rows)
        attempt_count = len(cell_rows)
        summaries.append(
            {
                "atlas_cell_id": cell_id,
                "role_family": str(cell_rows[0].get("role_family", "")) if cell_rows else "",
                "candidate_group": str(cell_rows[0].get("candidate_group", "")) if cell_rows else "",
                "parameter_bin": str(cell_rows[0].get("parameter_bin", "")) if cell_rows else "",
                "hidden_dynamics_bucket": str(cell_rows[0].get("hidden_dynamics_bucket", "")) if cell_rows else "",
                "sampled_obstacle_label_scope": str(cell_rows[0].get("sampled_obstacle_label_scope", "")) if cell_rows else "",
                "reset_attempt_count": attempt_count,
                "reset_success_count": success_count,
                "reset_failure_count": attempt_count - success_count,
                "reset_success_rate": success_count / attempt_count if attempt_count else 0.0,
                "observation_dimension_failure_count": sum(
                    _bool(row.get("reset_success")) and not _bool(row.get("observation_dimension_matches_expected"))
                    for row in cell_rows
                ),
                "obstacle_initialized_count": sum(_bool(row.get("obstacle_initialized")) for row in cell_rows),
                "failure_type_counts": dict(_count_by([row for row in cell_rows if str(row.get("failure_type", ""))], "failure_type")),
                "obstacle_label_counts": dict(_count_by([row for row in cell_rows if str(row.get("obstacle_label", ""))], "obstacle_label")),
                "support_class": _support_class(success_count, attempt_count),
            }
        )
    return summaries


def _group_summary_rows(cell_summary_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for group in sorted({str(row.get("candidate_group", "")) for row in cell_summary_rows}):
        group_rows = [row for row in cell_summary_rows if str(row.get("candidate_group", "")) == group]
        attempt_count = sum(int(row.get("reset_attempt_count", 0) or 0) for row in group_rows)
        success_count = sum(int(row.get("reset_success_count", 0) or 0) for row in group_rows)
        support_classes = sorted({str(row.get("support_class", "")) for row in group_rows if str(row.get("support_class", ""))})
        summaries.append(
            {
                "candidate_group": group,
                "cell_count": len(group_rows),
                "reset_attempt_count": attempt_count,
                "reset_success_count": success_count,
                "reset_failure_count": attempt_count - success_count,
                "reset_success_rate": success_count / attempt_count if attempt_count else 0.0,
                "support_classes": "|".join(support_classes),
            }
        )
    return summaries


def _classification_rows(cell_summary_rows: Sequence[Mapping[str, Any]], *, complete: bool) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []

    def add(key: str, value: str, admissible: bool, reason: str) -> None:
        rows.append({"classification_key": key, "classification_value": value, "admissible": admissible, "reason": reason})

    if not complete:
        add("atlas_complete", "false", False, "atlas did not satisfy source or execution guardrails")
        return "atlas_incomplete", rows

    support_counts = Counter(str(row.get("support_class", "")) for row in cell_summary_rows)
    partial_cells = [
        str(row.get("atlas_cell_id", ""))
        for row in cell_summary_rows
        if str(row.get("support_class", "")) == "reset_support_partial"
    ]
    absent_cells = [
        str(row.get("atlas_cell_id", ""))
        for row in cell_summary_rows
        if str(row.get("support_class", "")) == "reset_support_absent"
    ]
    full_cells = [
        str(row.get("atlas_cell_id", ""))
        for row in cell_summary_rows
        if str(row.get("support_class", "")) == "reset_support_full"
    ]
    add("distribution_cell_count", str(len(cell_summary_rows)), True, "atlas cells were generated beyond fixed R1 rows")
    add("reset_support_full_cell_count", str(len(full_cells)), True, "full-support cells reset for every seed")
    add("reset_support_partial_cell_count", str(len(partial_cells)), True, "partial-support cells identify seed-fragile bins")
    add("reset_support_absent_cell_count", str(len(absent_cells)), True, "absent-support cells identify unsupported bins")
    signals: list[str] = ["distribution_support_atlas"]
    if partial_cells:
        signals.append("seed_fragility")
        add("seed_fragility", "|".join(partial_cells), True, "some distribution cells have partial reset support")
    if absent_cells:
        signals.append("unsupported_bins_present")
        add("unsupported_bins_present", "|".join(absent_cells), True, "some distribution cells have no reset support")
    if support_counts.get("reset_support_full", 0) == len(cell_summary_rows):
        signals.append("all_cells_full_support")
    return "|".join(signals), rows


def _claim_boundary_rows(result_class: str, classification: str) -> list[dict[str, Any]]:
    complete = result_class == RESULT_COMPLETE
    return [
        {
            "claim_key": "distribution_reset_sampler_support_atlas",
            "claim_value": classification,
            "admissible": complete,
            "reason": "M2468 may claim distribution-level reset sampler support only.",
        },
        {"claim_key": "environment_step_or_policy_action", "claim_value": "false", "admissible": True, "reason": "M2468 stops after reset."},
        {"claim_key": "measured_rollout_started", "claim_value": "false", "admissible": True, "reason": "No rollout is run."},
        {"claim_key": "scenario_redesign_executed", "claim_value": "false", "admissible": True, "reason": "Atlas rows are diagnostic-only support bins."},
        {"claim_key": "repair_training_started", "claim_value": "false", "admissible": True, "reason": "No repair or training is executed."},
        {"claim_key": "ranking_or_winner", "claim_value": "false", "admissible": True, "reason": "Atlas cells are not ranked and no winner is selected."},
        {
            "claim_key": "actual_success_improvement",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "Reset-only support is not measured controller performance.",
        },
        {
            "claim_key": "paper_or_self_id_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No controller-family or history-necessity verdict is run.",
        },
        {
            "claim_key": "current_sim_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "M2468 is a reset support atlas, not a current-sim verdict.",
        },
    ]


def _decision_rows(*, result_class: str, classification: str, next_blocker: str) -> list[dict[str, Any]]:
    complete = result_class == RESULT_COMPLETE
    return [
        {
            "decision_key": "distribution_support_atlas_complete",
            "decision_value": "true" if complete else "false",
            "admissible": complete,
            "reason": "The atlas wrote reset-only support evidence and classification rows.",
        },
        {
            "decision_key": "atlas_classification",
            "decision_value": classification,
            "admissible": complete,
            "reason": "Classification is diagnostic only and must be audited before repair or measured execution.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "No repair, training, ranking, or winner selection is executed.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker,
            "admissible": True,
            "reason": "Route atlas output to result audit.",
        },
    ]


def _guardrail_rows(
    *,
    source_admission_failure_count: int,
    atlas_cell_count: int,
    expected_min_cell_count: int,
    candidate_group_coverage_count: int,
    expected_group_coverage_count: int,
    fixed_m2464_r1_reuse_count: int,
    diagnostic_attempt_count: int,
    expected_attempt_count: int,
    actor_contract_failure_count: int,
    active_config_overwrite_count: int,
    environment_step_count: int,
    policy_action_executed: bool,
    environment_rollout_started: bool,
    measured_rollout_started: bool,
    repair_execution_started: bool,
    training_started: bool,
    replay_started: bool,
    ppo_used: bool,
    promoted: bool,
    private_holdout_used: bool,
    ranking_admissible_count: int,
    winner_selected_count: int,
    verdict_claim_count: int,
) -> list[dict[str, Any]]:
    specs = [
        (
            "m2468_source_admission",
            "lineage",
            "m2455_m2466_m2467",
            "lineage_invalid",
            "source_admission_failure_count",
            source_admission_failure_count,
            source_admission_failure_count != 0,
            "M2468 requires M2455 candidates, M2466 seed-fragility evidence, and M2467 pivot audit.",
        ),
        (
            "m2468_broad_atlas_cell_count",
            "atlas_design",
            "atlas_cell_rows",
            "lineage_invalid",
            "atlas_cell_count",
            atlas_cell_count,
            atlas_cell_count < expected_min_cell_count,
            "M2468 must generate a broad atlas, not a fixed-row retry.",
        ),
        (
            "m2468_candidate_group_coverage",
            "atlas_design",
            "atlas_cell_rows",
            "lineage_invalid",
            "candidate_group_coverage_count",
            candidate_group_coverage_count,
            candidate_group_coverage_count < expected_group_coverage_count,
            "M2468 must cover stable, AES, handling-limit, hidden-dynamics, and mitigation groups.",
        ),
        (
            "m2468_no_fixed_m2464_r1_reuse",
            "local_search_guard",
            "atlas_cell_rows",
            "objective_overfit",
            "fixed_m2464_r1_reuse_count",
            fixed_m2464_r1_reuse_count,
            fixed_m2464_r1_reuse_count != 0,
            "M2468 must not retry or repair the exact fixed M2464 R1 overlay rows.",
        ),
        (
            "m2468_diagnostic_attempt_count",
            "diagnostic_execution",
            "reset_rows",
            "lineage_invalid",
            "diagnostic_attempt_count",
            diagnostic_attempt_count,
            diagnostic_attempt_count != expected_attempt_count,
            "Every atlas cell must run the requested reset seed panel.",
        ),
        (
            "m2468_actor_contract_clear",
            "actor_contract",
            "effective_env_configs",
            "contract_violation",
            "actor_contract_failure_count",
            actor_contract_failure_count,
            actor_contract_failure_count != 0,
            "All atlas cells must preserve the P0 human-view actor contract.",
        ),
        (
            "m2468_no_active_config_overwrite",
            "execution_boundary",
            "effective_env_configs",
            "lineage_invalid",
            "active_config_overwrite_count",
            active_config_overwrite_count,
            active_config_overwrite_count != 0,
            "M2468 must write only run-dir effective configs.",
        ),
        (
            "m2468_no_environment_steps",
            "execution_boundary",
            "reset_rows",
            "contract_violation",
            "environment_step_count",
            environment_step_count,
            environment_step_count != 0,
            "M2468 must stop after reset.",
        ),
        (
            "m2468_no_policy_or_rollout",
            "execution_boundary",
            "reset_rows",
            "contract_violation",
            "policy_or_rollout",
            int(policy_action_executed or environment_rollout_started or measured_rollout_started),
            policy_action_executed or environment_rollout_started or measured_rollout_started,
            "M2468 must not execute policy actions or rollouts.",
        ),
        (
            "m2468_no_repair_training_replay_promotion",
            "execution_boundary",
            "summary",
            "contract_violation",
            "repair_training_replay_promotion",
            int(repair_execution_started or training_started or replay_started or ppo_used or promoted),
            repair_execution_started or training_started or replay_started or ppo_used or promoted,
            "Atlas cells are not repair execution, training, replay, PPO, or promotion.",
        ),
        (
            "m2468_no_private_holdout",
            "execution_boundary",
            "summary",
            "contract_violation",
            "private_holdout_used",
            private_holdout_used,
            private_holdout_used,
            "M2468 does not use private holdout data.",
        ),
        (
            "m2468_no_ranking_or_winner",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "ranking_or_winner_count",
            ranking_admissible_count + winner_selected_count,
            ranking_admissible_count != 0 or winner_selected_count != 0,
            "M2468 must not rank atlas cells or select winners.",
        ),
        (
            "m2468_no_verdict_claims",
            "claim_boundary",
            "summary",
            "metric_artifact",
            "verdict_claim_count",
            verdict_claim_count,
            verdict_claim_count != 0,
            "M2468 may not claim paper, self-ID, scenario-redesign, training-repair, or current-sim verdicts.",
        ),
    ]
    return [
        {
            "guardrail_id": guardrail_id,
            "guardrail_class": guardrail_class,
            "source_role_or_axis": source_role_or_axis,
            "failure_mode_to_preserve": failure_mode,
            "metric_to_watch": metric,
            "value": value,
            "violation": bool(violation),
            "reason": reason,
        }
        for guardrail_id, guardrail_class, source_role_or_axis, failure_mode, metric, value, violation, reason in specs
    ]


def _source_admission_failures(
    *,
    m2455_summary: Mapping[str, Any],
    m2466_summary: Mapping[str, Any],
    m2467_doc: Path,
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    failures: list[str] = []
    if str(m2455_summary.get("result_class", "")) != "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass":
        failures.append("m2455_result_class_not_pass")
    if int(m2455_summary.get("candidate_row_count", -1)) < 30:
        failures.append("m2455_candidate_row_count_too_low")
    for key in [
        "stable_feasibility_support_count",
        "stable_aes_support_count",
        "handling_limit_guardrail_count",
        "hidden_dynamics_guardrail_count",
        "mitigation_guardrail_count",
    ]:
        if int(m2455_summary.get(key, 0) or 0) <= 0:
            failures.append(f"m2455_{key}_missing")
    if int(m2455_summary.get("guardrail_violation_count", -1)) != 0:
        failures.append("m2455_guardrail_violation_count_not_0")
    if str(m2466_summary.get("result_class", "")) != "scenario_quality_r1_reset_sampling_diagnostic_panel_complete":
        failures.append("m2466_result_class_not_complete")
    if str(m2466_summary.get("diagnostic_classification", "")) != "seed_fragility":
        failures.append("m2466_classification_not_seed_fragility")
    if int(m2466_summary.get("guardrail_violation_count", -1)) != 0:
        failures.append("m2466_guardrail_violation_count_not_0")
    if not m2467_doc.exists():
        failures.append("m2467_audit_doc_missing")
    if not candidate_rows:
        failures.append("m2455_candidate_rows_missing")
    return failures


def run_scenario_distribution_support_atlas(
    *,
    m2455_dir: Path | str = DEFAULT_M2455_DIR,
    m2466_dir: Path | str = DEFAULT_M2466_DIR,
    m2467_doc: Path | str = DEFAULT_M2467_DOC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    seed_base: int = DEFAULT_SEED_BASE,
    seeds_per_cell: int = DEFAULT_SEEDS_PER_CELL,
    expected_observation_dim: int = DEFAULT_EXPECTED_OBSERVATION_DIM,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_m2455 = Path(m2455_dir)
    source_m2466 = Path(m2466_dir)
    audit_doc = Path(m2467_doc)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config_dir = output / "effective_env_configs"
    config_dir.mkdir(parents=True, exist_ok=True)

    m2455_summary = read_json(source_m2455 / "summary.json")
    m2466_summary = read_json(source_m2466 / "summary.json")
    candidate_rows = read_csv_rows(source_m2455 / "candidate_rows.csv")
    source_failures = _source_admission_failures(
        m2455_summary=m2455_summary,
        m2466_summary=m2466_summary,
        m2467_doc=audit_doc,
        candidate_rows=candidate_rows,
    )

    cells = _atlas_cell_specs(candidate_rows)
    atlas_cell_rows: list[dict[str, Any]] = []
    reset_rows: list[dict[str, Any]] = []
    effective_configs: dict[str, Any] = {}
    effective_config_paths: dict[str, Path] = {}
    actor_contract_failure_count = 0
    fixed_m2464_r1_reuse_count = 0

    for cell in cells:
        config_data = dict(cell["config"])
        config = build_env_config(config_data)
        effective_config = _config_to_dict(config, config_data)
        actor_contract_pass = _actor_contract_guardrail_pass(effective_config)
        if not actor_contract_pass:
            actor_contract_failure_count += 1
        matches_fixed = _matches_fixed_m2464_r1(effective_config)
        if matches_fixed:
            fixed_m2464_r1_reuse_count += 1
        path = _write_effective_config(output_dir=output, cell=cell, effective_config=effective_config)
        effective_configs[str(cell["atlas_cell_id"])] = config
        effective_config_paths[str(cell["atlas_cell_id"])] = path
        source_ids = list(cell.get("source_candidate_ids", []))
        atlas_cell_rows.append(
            {
                "atlas_cell_id": str(cell["atlas_cell_id"]),
                "role_family": str(cell["role_family"]),
                "candidate_group": str(cell["candidate_group"]),
                "parameter_bin": str(cell["parameter_bin"]),
                "hidden_dynamics_bucket": str(cell["hidden_dynamics_bucket"]),
                "sampled_obstacle_label_scope": str(cell["sampled_obstacle_label_scope"]),
                "source_candidate_ids": "|".join(str(item) for item in source_ids),
                "source_candidate_count": len(source_ids),
                "split_scope": str(cell["split_scope"]),
                "effective_env_config_path": str(path),
                "actor_contract_guardrail_pass": actor_contract_pass,
                "matches_fixed_m2464_r1_overlay": matches_fixed,
                "diagnostic_only": True,
                "repair_candidate": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "promoted": False,
                "cell_description": str(cell["cell_description"]),
            }
        )

    candidate_group_coverage_count = len({str(row.get("candidate_group", "")) for row in atlas_cell_rows})
    expected_min_cell_count = 12
    expected_group_coverage_count = 5
    source_clean = (
        not source_failures
        and len(cells) >= expected_min_cell_count
        and candidate_group_coverage_count >= expected_group_coverage_count
        and fixed_m2464_r1_reuse_count == 0
    )

    if source_clean and actor_contract_failure_count == 0:
        for cell_index, cell in enumerate(cells):
            cell_id = str(cell["atlas_cell_id"])
            for seed_index in range(int(seeds_per_cell)):
                eval_seed = int(seed_base) + cell_index * int(seeds_per_cell) + seed_index
                reset_rows.append(
                    _reset_row(
                        cell=cell,
                        config=effective_configs[cell_id],
                        effective_config_path=effective_config_paths[cell_id],
                        eval_seed=eval_seed,
                        reset_seed_index=seed_index,
                        expected_observation_dim=expected_observation_dim,
                    )
                )

    cell_summary_rows = _cell_summary_rows(reset_rows)
    group_summary_rows = _group_summary_rows(cell_summary_rows)
    expected_attempt_count = len(cells) * int(seeds_per_cell)
    reset_failure_rows = [dict(row) for row in reset_rows if not _bool(row.get("reset_success"))]
    reset_success_count = sum(_bool(row.get("reset_success")) for row in reset_rows)
    environment_step_count = sum(int(row.get("environment_step_count", 0) or 0) for row in reset_rows)
    active_config_overwrite_count = sum(
        not _inside_dir(Path(str(row.get("effective_env_config_path", ""))), output) for row in atlas_cell_rows
    ) + sum(_bool(row.get("active_config_overwritten")) for row in reset_rows)
    policy_action_executed = any(_bool(row.get("policy_action_executed")) for row in reset_rows)
    environment_rollout_started = any(_bool(row.get("environment_rollout_started")) for row in reset_rows)
    measured_rollout_started = any(_bool(row.get("measured_rollout_started")) for row in reset_rows)
    repair_execution_started = any(_bool(row.get("repair_execution_started")) for row in reset_rows)
    training_started = any(_bool(row.get("training_started")) for row in reset_rows)
    replay_started = any(_bool(row.get("replay_started")) for row in reset_rows)
    ppo_used = any(_bool(row.get("ppo_used")) for row in reset_rows)
    promoted = any(_bool(row.get("promoted")) for row in reset_rows) or any(_bool(row.get("promoted")) for row in atlas_cell_rows)
    private_holdout_used = any(_bool(row.get("private_holdout_used")) for row in reset_rows)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in reset_rows) + sum(
        _bool(row.get("ranking_admissible")) for row in atlas_cell_rows
    )
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in reset_rows) + sum(
        _bool(row.get("winner_selected")) for row in atlas_cell_rows
    )
    verdict_flags = [
        "paper_level_claim_made",
        "finite_window_vs_gru_conclusion_made",
        "level3_self_id_claim_made",
        "scenario_redesign_executed_claim_made",
        "training_repair_success_claim_made",
        "current_sim_verdict_claim_made",
    ]
    verdict_claim_count = sum(any(_bool(row.get(flag)) for flag in verdict_flags) for row in reset_rows)

    guards = _guardrail_rows(
        source_admission_failure_count=len(source_failures),
        atlas_cell_count=len(atlas_cell_rows),
        expected_min_cell_count=expected_min_cell_count,
        candidate_group_coverage_count=candidate_group_coverage_count,
        expected_group_coverage_count=expected_group_coverage_count,
        fixed_m2464_r1_reuse_count=fixed_m2464_r1_reuse_count,
        diagnostic_attempt_count=len(reset_rows),
        expected_attempt_count=expected_attempt_count,
        actor_contract_failure_count=actor_contract_failure_count,
        active_config_overwrite_count=active_config_overwrite_count,
        environment_step_count=environment_step_count,
        policy_action_executed=policy_action_executed,
        environment_rollout_started=environment_rollout_started,
        measured_rollout_started=measured_rollout_started,
        repair_execution_started=repair_execution_started,
        training_started=training_started,
        replay_started=replay_started,
        ppo_used=ppo_used,
        promoted=promoted,
        private_holdout_used=private_holdout_used,
        ranking_admissible_count=ranking_admissible_count,
        winner_selected_count=winner_selected_count,
        verdict_claim_count=verdict_claim_count,
    )
    guardrail_violation_count = sum(_bool(row.get("violation")) for row in guards)
    atlas_classification, classification_rows = _classification_rows(
        cell_summary_rows,
        complete=guardrail_violation_count == 0,
    )
    result_class = RESULT_COMPLETE if guardrail_violation_count == 0 else RESULT_FAIL
    claim_rows = _claim_boundary_rows(result_class, atlas_classification)
    decision_rows = _decision_rows(result_class=result_class, classification=atlas_classification, next_blocker=next_blocker)

    failure_types = sorted(
        {
            str(row.get("failure_mode_to_preserve", ""))
            for row in guards
            if _bool(row.get("violation")) and str(row.get("failure_mode_to_preserve", ""))
        }
        | {str(row.get("failure_type", "")) for row in reset_rows if str(row.get("failure_type", ""))}
    )
    if "seed_fragility" in atlas_classification:
        failure_types.append("seed_fragility")
    failure_types = sorted(set(item for item in failure_types if item))

    write_csv_rows(output / "atlas_cell_rows.csv", atlas_cell_rows, fieldnames=ATLAS_CELL_FIELDNAMES)
    write_csv_rows(output / "reset_rows.csv", reset_rows, fieldnames=RESET_ROW_FIELDNAMES)
    write_csv_rows(output / "reset_failure_rows.csv", reset_failure_rows, fieldnames=RESET_ROW_FIELDNAMES)
    write_csv_rows(output / "cell_summary_rows.csv", cell_summary_rows, fieldnames=CELL_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "group_summary_rows.csv", group_summary_rows, fieldnames=GROUP_SUMMARY_FIELDNAMES)
    write_csv_rows(output / "classification_rows.csv", classification_rows, fieldnames=CLASSIFICATION_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decision_rows, fieldnames=DECISION_FIELDNAMES)

    support_class_counts = dict(_count_by(cell_summary_rows, "support_class"))
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2455_summary": str(source_m2455 / "summary.json"),
            "m2455_candidate_rows": str(source_m2455 / "candidate_rows.csv"),
            "m2466_summary": str(source_m2466 / "summary.json"),
            "m2467_doc": str(audit_doc),
        },
        "source_admission_failure_count": len(source_failures),
        "source_admission_failures": source_failures,
        "source_candidate_row_count": len(candidate_rows),
        "atlas_cell_count": len(atlas_cell_rows),
        "expected_min_atlas_cell_count": expected_min_cell_count,
        "candidate_group_coverage_count": candidate_group_coverage_count,
        "expected_candidate_group_coverage_count": expected_group_coverage_count,
        "fixed_m2464_r1_reuse_count": fixed_m2464_r1_reuse_count,
        "seed_base": int(seed_base),
        "seeds_per_cell": int(seeds_per_cell),
        "expected_observation_dim": int(expected_observation_dim),
        "diagnostic_attempt_count": len(reset_rows),
        "expected_diagnostic_attempt_count": expected_attempt_count,
        "reset_success_count": reset_success_count,
        "reset_failure_count": len(reset_failure_rows),
        "reset_success_rate": reset_success_count / len(reset_rows) if reset_rows else 0.0,
        "support_class_counts": support_class_counts,
        "atlas_classification": atlas_classification,
        "actor_contract_failure_count": actor_contract_failure_count,
        "active_config_overwrite_count": active_config_overwrite_count,
        "environment_step_count": environment_step_count,
        "policy_action_executed": policy_action_executed,
        "environment_rollout_started": environment_rollout_started,
        "measured_rollout_started": measured_rollout_started,
        "repair_execution_started": repair_execution_started,
        "training_started": training_started,
        "replay_started": replay_started,
        "ppo_used": ppo_used,
        "promoted": promoted,
        "private_holdout_used": private_holdout_used,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "atlas_cell_rows": str(output / "atlas_cell_rows.csv"),
            "reset_rows": str(output / "reset_rows.csv"),
            "reset_failure_rows": str(output / "reset_failure_rows.csv"),
            "cell_summary_rows": str(output / "cell_summary_rows.csv"),
            "group_summary_rows": str(output / "group_summary_rows.csv"),
            "classification_rows": str(output / "classification_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
            "effective_env_configs": str(config_dir),
            "run_state": str(output / "run_state.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "task_id": "m2468-paper-route-current-sim-dual-axis-scenario-distribution-support-atlas",
            "status": "completed" if result_class == RESULT_COMPLETE else "failed",
            "result_class": result_class,
            "atlas_classification": atlas_classification,
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2455-dir", type=Path, default=DEFAULT_M2455_DIR)
    parser.add_argument("--m2466-dir", type=Path, default=DEFAULT_M2466_DIR)
    parser.add_argument("--m2467-doc", type=Path, default=DEFAULT_M2467_DOC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-base", type=int, default=DEFAULT_SEED_BASE)
    parser.add_argument("--seeds-per-cell", type=int, default=DEFAULT_SEEDS_PER_CELL)
    parser.add_argument("--expected-observation-dim", type=int, default=DEFAULT_EXPECTED_OBSERVATION_DIM)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_scenario_distribution_support_atlas(
        m2455_dir=args.m2455_dir,
        m2466_dir=args.m2466_dir,
        m2467_doc=args.m2467_doc,
        output_dir=args.output_dir,
        seed_base=args.seed_base,
        seeds_per_cell=args.seeds_per_cell,
        expected_observation_dim=args.expected_observation_dim,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary: {summary['artifacts']['summary']}")
    print(f"result_class: {summary['result_class']}")
    print(f"atlas_cell_count: {summary['atlas_cell_count']}")
    print(f"diagnostic_attempt_count: {summary['diagnostic_attempt_count']}")
    print(f"reset_success_count: {summary['reset_success_count']}")
    print(f"reset_failure_count: {summary['reset_failure_count']}")
    print(f"support_class_counts: {summary['support_class_counts']}")
    print(f"atlas_classification: {summary['atlas_classification']}")
    print(f"guardrail_violation_count: {summary['guardrail_violation_count']}")
    print(f"next_blocker: {summary['next_blocker']}")
    return 0 if summary["result_class"] == RESULT_COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(main())
