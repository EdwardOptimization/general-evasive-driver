"""Materialize the Route B capability-prediction modeling contract.

M2891 converts the M2890 modeling-contract design into machine-checkable
contract rows. It is intentionally read-only: no simulator reset, rollout,
model fitting, training, ranking, promotion, or verdict claim is performed.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


DEFAULT_MILESTONE = (
    "m2891-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2891_paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight"
)
DEFAULT_M2887_DIR = Path("runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight")
DEFAULT_M2890_DESIGN = Path("docs/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2891 read-only capability-prediction modeling-contract materialization only. It reads "
    "M2887/M2888/M2889/M2890 artifacts and writes feature, label, split, loss, metric, "
    "baseline, gate, and claim contract rows. It does not reset, step, rollout, replay, "
    "validate, fit a model, train, run PPO, rank controllers, select a winner, promote a "
    "checkpoint, publish a package, or claim driver performance, paper evidence, "
    "finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation, "
    "full-driver completion, or level3 self-ID."
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller-family ranking, profile ranking, model quality, "
    "checkpoint promotion, finite-window-vs-GRU verdict, paper result, current-sim verdict, "
    "validation readiness/result, high-fidelity validation, full-driver completion, or "
    "level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "dependency_mutation_performed": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
    "model_fitting_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "package_published": False,
    "driver_performance_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

FEATURE_FIELDNAMES = [
    "feature_contract_id",
    "profile_name",
    "profile_level",
    "feature_family",
    "feature_source",
    "expected_shape",
    "actor_visible_allowed",
    "hidden_oracle_input_allowed",
    "future_target_input_allowed",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
LABEL_FIELDNAMES = [
    "label_contract_id",
    "target_family",
    "required_columns",
    "available_columns",
    "target_visibility",
    "actor_visible_allowed",
    "normalization_policy",
    "missing_value_policy",
    "loss_family",
    "metric_family",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
SPLIT_FIELDNAMES = [
    "split_contract_id",
    "split_family",
    "split_unit",
    "group_key",
    "task_source_count",
    "profile_task_count",
    "paper_holdout_admitted",
    "preflight_only",
    "non_leaking_split_possible",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
LOSS_METRIC_FIELDNAMES = [
    "loss_metric_contract_id",
    "target_family",
    "loss_family",
    "metric_family",
    "availability_mask_required",
    "paper_ranking_allowed",
    "status_pass",
    "failure_type",
    "claim_boundary",
]
BASELINE_FIELDNAMES = [
    "baseline_contract_id",
    "comparison_family",
    "profile_name",
    "profile_level",
    "profile_task_count",
    "training_scheduled",
    "environment_rollout_scheduled",
    "profile_specific_tuning",
    "status_pass",
    "failure_type",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
    "evidence_required_before_claim",
    "claim_boundary",
]

PROFILE_FEATURES = {
    "L0_current_masked": ("current_deployable_observation", "current deployable P0 frame only", "obs=72"),
    "L1_one_step": (
        "previous_command_and_actuator_state",
        "current deployable frame plus previous command and actuator state",
        "obs=72",
    ),
    "L2_window_13": ("finite_window_command_response_history", "explicit 13-step deployable history window", "obs=72;window=13"),
    "L2_window_13_current_tiled": (
        "current_tiled_history_control",
        "13-step current-frame tiled capacity control",
        "obs=72;window=13",
    ),
    "L2_window_25": ("finite_window_command_response_history", "explicit 25-step deployable history window", "obs=72;window=25"),
    "L2_window_25_current_tiled": (
        "current_tiled_history_control",
        "25-step current-frame tiled capacity control",
        "obs=72;window=25",
    ),
    "L2_window_50": ("finite_window_command_response_history", "explicit 50-step deployable history window", "obs=72;window=50"),
    "L2_window_50_current_tiled": (
        "current_tiled_history_control",
        "50-step current-frame tiled capacity control",
        "obs=72;window=50",
    ),
    "L2_window_100": ("finite_window_command_response_history", "explicit 100-step deployable history window", "obs=72;window=100"),
    "L2_window_100_current_tiled": (
        "current_tiled_history_control",
        "100-step current-frame tiled capacity control",
        "obs=72;window=100",
    ),
    "L3_online_gru": ("recurrent_hidden_state", "online recurrent hidden state from deployable observation stream", "obs=72;hidden=actor_internal"),
    "L3_reset_control_corrected": (
        "recurrent_hidden_state",
        "reset/truncated recurrent-state control",
        "obs=72;hidden=actor_internal_reset_control",
    ),
}

LABEL_POLICIES = {
    "future_braking_deceleration_envelope": ("robust_regression", "per_target_mae|per_target_rmse"),
    "future_yaw_authority": ("robust_regression", "per_target_mae|per_target_rmse"),
    "future_lateral_acceleration_response": ("robust_regression", "per_target_mae|per_target_rmse|tail_error_for_margin_targets"),
    "actuator_response_lag_proxy": ("robust_regression", "per_target_mae|per_target_rmse"),
    "recovery_margin_after_maneuver": ("robust_regression|binary_recoverability", "per_target_mae|per_target_rmse|tail_error_for_margin_targets"),
    "first_critical_action_quality": ("robust_regression", "per_target_mae|per_target_rmse|tail_error_for_margin_targets"),
}

COMPARISON_FAMILIES = {
    "L0_current_masked": "L0-current",
    "L1_one_step": "L1-one-step",
    "L2_window_13": "L2-finite-window",
    "L2_window_25": "L2-finite-window",
    "L2_window_50": "L2-finite-window",
    "L2_window_100": "L2-finite-window",
    "L2_window_13_current_tiled": "L2-current-tiled-control",
    "L2_window_25_current_tiled": "L2-current-tiled-control",
    "L2_window_50_current_tiled": "L2-current-tiled-control",
    "L2_window_100_current_tiled": "L2-current-tiled-control",
    "L3_online_gru": "L3-GRU",
    "L3_reset_control_corrected": "L3-reset-control",
}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _profile_level(profile_name: str) -> str:
    return profile_name.split("_", 1)[0] if "_" in profile_name else profile_name


def _required_columns_available(row: dict[str, str]) -> bool:
    required = {item for item in row.get("required_columns", "").split("|") if item}
    available = {item for item in row.get("available_columns", "").split("|") if item}
    return bool(required) and required.issubset(available)


def build_feature_contract_rows(profile_task_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_profile: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in profile_task_rows:
        by_profile[row.get("profile_name", "")].append(row)

    rows: list[dict[str, Any]] = []
    for index, profile_name in enumerate(REQUIRED_PROFILES, start=1):
        family, source, shape = PROFILE_FEATURES[profile_name]
        profile_rows = by_profile.get(profile_name, [])
        status_pass = bool(profile_rows) and all(
            _bool(row.get("status_pass"))
            and not _bool(row.get("environment_rollout_scheduled"))
            and not _bool(row.get("training_scheduled"))
            and not _bool(row.get("profile_specific_tuning"))
            and row.get("actor_visible_target_fields", "") == ""
            for row in profile_rows
        )
        rows.append(
            {
                "feature_contract_id": f"m2891-feature-contract-{index:04d}",
                "profile_name": profile_name,
                "profile_level": _profile_level(profile_name),
                "feature_family": family,
                "feature_source": source,
                "expected_shape": shape,
                "actor_visible_allowed": True,
                "hidden_oracle_input_allowed": False,
                "future_target_input_allowed": False,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_label_contract_rows(evaluator_target_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(evaluator_target_rows, start=1):
        target_family = row.get("target_family", "")
        loss_family, metric_family = LABEL_POLICIES.get(target_family, ("robust_regression", "per_target_mae|per_target_rmse"))
        status_pass = (
            _bool(row.get("status_pass"))
            and not _bool(row.get("actor_visible_allowed"))
            and row.get("target_visibility") == "evaluator_only_actor_invisible"
            and _required_columns_available(row)
        )
        rows.append(
            {
                "label_contract_id": f"m2891-label-contract-{index:04d}",
                "target_family": target_family,
                "required_columns": row.get("required_columns", ""),
                "available_columns": row.get("available_columns", ""),
                "target_visibility": row.get("target_visibility", ""),
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "normalization_policy": "robust_z_score",
                "missing_value_policy": "required_columns_block_optional_values_masked",
                "loss_family": loss_family,
                "metric_family": metric_family,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_split_contract_rows(
    *,
    usable_task_rows: list[dict[str, str]],
    profile_task_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    profile_count_by_task = Counter(row.get("task_source_id", "") for row in profile_task_rows)
    task_count_by_family = Counter(row.get("task_family", "") for row in usable_task_rows)
    task_count_by_env = Counter(row.get("env_template_family", "") for row in usable_task_rows)
    profile_count_by_env = Counter(row.get("env_template_family", "") for row in profile_task_rows)
    expected_profiles_per_task = len(REQUIRED_PROFILES)

    rows: list[dict[str, Any]] = []
    no_profile_leakage = bool(profile_count_by_task) and all(count == expected_profiles_per_task for count in profile_count_by_task.values())
    rows.append(
        {
            "split_contract_id": "m2891-split-contract-task-source-unit",
            "split_family": "task_source_no_profile_leakage",
            "split_unit": "task_source_id",
            "group_key": "all_usable_tasks",
            "task_source_count": len(profile_count_by_task),
            "profile_task_count": len(profile_task_rows),
            "paper_holdout_admitted": False,
            "preflight_only": True,
            "non_leaking_split_possible": no_profile_leakage,
            "status_pass": no_profile_leakage,
            "failure_type": "objective_overfit" if not no_profile_leakage else "none",
            "claim_boundary": CLAIM_SCOPE,
        }
    )
    for index, (family, count) in enumerate(sorted(task_count_by_family.items()), start=1):
        non_leaking = count >= 2
        rows.append(
            {
                "split_contract_id": f"m2891-split-contract-task-family-{index:04d}",
                "split_family": "task_family_preflight_split",
                "split_unit": "task_source_id",
                "group_key": family,
                "task_source_count": count,
                "profile_task_count": count * expected_profiles_per_task,
                "paper_holdout_admitted": False,
                "preflight_only": True,
                "non_leaking_split_possible": non_leaking,
                "status_pass": non_leaking,
                "failure_type": "scenario_sampling_failure" if not non_leaking else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    for index, (env_family, count) in enumerate(sorted(task_count_by_env.items()), start=1):
        non_leaking = count >= 2
        rows.append(
            {
                "split_contract_id": f"m2891-split-contract-env-family-{index:04d}",
                "split_family": "env_template_preflight_split",
                "split_unit": "task_source_id",
                "group_key": env_family,
                "task_source_count": count,
                "profile_task_count": profile_count_by_env.get(env_family, count * expected_profiles_per_task),
                "paper_holdout_admitted": False,
                "preflight_only": True,
                "non_leaking_split_possible": non_leaking,
                "status_pass": non_leaking,
                "failure_type": "scenario_sampling_failure" if not non_leaking else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_loss_metric_contract_rows(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(label_rows, start=1):
        status_pass = _bool(row["status_pass"]) and not _bool(row["actor_visible_allowed"])
        rows.append(
            {
                "loss_metric_contract_id": f"m2891-loss-metric-contract-{index:04d}",
                "target_family": row["target_family"],
                "loss_family": row["loss_family"],
                "metric_family": row["metric_family"],
                "availability_mask_required": True,
                "paper_ranking_allowed": False,
                "status_pass": status_pass,
                "failure_type": "metric_artifact" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_baseline_contract_rows(profile_task_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    count_by_profile = Counter(row.get("profile_name", "") for row in profile_task_rows)
    rows: list[dict[str, Any]] = []
    for index, profile_name in enumerate(REQUIRED_PROFILES, start=1):
        profile_rows = [row for row in profile_task_rows if row.get("profile_name") == profile_name]
        training_scheduled = any(_bool(row.get("training_scheduled")) for row in profile_rows)
        rollout_scheduled = any(_bool(row.get("environment_rollout_scheduled")) for row in profile_rows)
        tuning = any(_bool(row.get("profile_specific_tuning")) for row in profile_rows)
        status_pass = bool(profile_rows) and not (training_scheduled or rollout_scheduled or tuning)
        rows.append(
            {
                "baseline_contract_id": f"m2891-baseline-contract-{index:04d}",
                "comparison_family": COMPARISON_FAMILIES[profile_name],
                "profile_name": profile_name,
                "profile_level": _profile_level(profile_name),
                "profile_task_count": count_by_profile.get(profile_name, 0),
                "training_scheduled": training_scheduled,
                "environment_rollout_scheduled": rollout_scheduled,
                "profile_specific_tuning": tuning,
                "status_pass": status_pass,
                "failure_type": "contract_violation" if not status_pass else "none",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_rows() -> list[dict[str, Any]]:
    allowed_specs = [
        ("contract_materialized", "modeling-contract materialization completeness", "M2891 summary and row artifacts"),
        ("feature_rows_materialized", "actor-safe feature contract rows materialized", "feature_contract_rows.csv"),
        ("label_rows_materialized", "evaluator-only label contract rows materialized", "label_contract_rows.csv"),
        ("split_rows_materialized", "preflight split contract rows materialized", "split_contract_rows.csv"),
        ("baseline_rows_materialized", "baseline contract rows materialized", "baseline_contract_rows.csv"),
        ("bounded_audit_handoff", "bounded result-audit handoff", "M2892 manifest"),
    ]
    blocked_specs = [
        ("implementation", "model implementation", "separate implementation preflight and audit"),
        ("model_fitting", "model fitting", "separate training or fitting manifest"),
        ("training", "training", "separate training manifest with holdout policy"),
        ("controller_ranking", "controller-family ranking", "fair comparison evidence and audit"),
        ("driver_performance", "driver performance", "closed-loop validation and promotion evidence"),
        ("finite_window_vs_gru", "finite-window-vs-GRU verdict", "separate fair L0/L1/L2/L3 comparison"),
        ("paper", "paper result", "paper-route audit and holdout evidence"),
        ("self_id", "level3 self-ID", "source-diverse history-necessity intervention evidence"),
    ]
    rows = [
        {
            "claim_id": f"m2891-claim-{claim_id}",
            "claim_family": claim_family,
            "claim_made": True,
            "claim_allowed": True,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, claim_family, evidence in allowed_specs
    ]
    rows.extend(
        {
            "claim_id": f"m2891-claim-{claim_id}",
            "claim_family": claim_family,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, claim_family, evidence in blocked_specs
    )
    return rows


def build_gate_rows(
    *,
    m2890_design_exists: bool,
    m2887_summary: dict[str, Any],
    profile_task_rows: list[dict[str, str]],
    evaluator_target_rows: list[dict[str, str]],
    source_singleton_rows: list[dict[str, str]],
    guard_rows: list[dict[str, str]],
    actor_rows: list[dict[str, str]],
    feature_rows: list[dict[str, Any]],
    label_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    loss_metric_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    profile_counts = Counter(row.get("profile_name", "") for row in profile_task_rows)
    profile_coverage_pass = set(profile_counts) == set(REQUIRED_PROFILES) and all(
        profile_counts[profile] == int(m2887_summary.get("usable_task_row_count", 0)) for profile in REQUIRED_PROFILES
    )
    actor_contract_pass = (
        bool(actor_rows)
        and P0_OBSERVATION_DIM == 72
        and ACTION_DIM == 3
        and all(_bool(row.get("status_pass")) and not _bool(row.get("future_target_actor_visible")) for row in actor_rows)
    )
    target_invisible_pass = bool(evaluator_target_rows) and all(
        _bool(row.get("status_pass")) and not _bool(row.get("actor_visible_allowed")) for row in evaluator_target_rows
    )
    leakage_absent_pass = all(
        _bool(row["actor_visible_allowed"])
        and not _bool(row["hidden_oracle_input_allowed"])
        and not _bool(row["future_target_input_allowed"])
        for row in feature_rows
    ) and all(not _bool(row["actor_visible_allowed"]) for row in label_rows)
    blocked_claim_gate_pass = all(_bool(row["claim_allowed"]) or not _bool(row["claim_made"]) for row in claim_rows)
    no_forbidden_execution = True

    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": status,
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if status else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    return [
        gate(
            "m2891-parent-summary-status-pass",
            "lineage",
            _bool(m2887_summary.get("status_pass")) and _bool(m2887_summary.get("gate_matrix_pass")) and m2890_design_exists,
            f"m2887_status={m2887_summary.get('status_pass')};m2887_gates={m2887_summary.get('gate_matrix_pass')};m2890_design_exists={m2890_design_exists}",
            "m2887_status=True;m2887_gates=True;m2890_design_exists=True",
            "lineage_invalid",
        ),
        gate(
            "m2891-profile-task-row-count",
            "artifact_completeness",
            len(profile_task_rows) == int(m2887_summary.get("profile_task_row_count", 0)),
            len(profile_task_rows),
            m2887_summary.get("profile_task_row_count", 0),
            "metric_artifact",
        ),
        gate(
            "m2891-required-profile-coverage",
            "baseline_contract",
            profile_coverage_pass,
            ";".join(f"{name}:{profile_counts.get(name, 0)}" for name in REQUIRED_PROFILES),
            f"each={m2887_summary.get('usable_task_row_count', 0)}",
            "metric_artifact",
        ),
        gate(
            "m2891-actor-contract-preserved",
            "actor_contract",
            actor_contract_pass,
            f"actor_rows={len(actor_rows)};obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "actor_rows>0;obs=72;action=3",
            "contract_violation",
        ),
        gate(
            "m2891-evaluator-targets-actor-invisible",
            "target_boundary",
            target_invisible_pass,
            sum(not _bool(row.get("actor_visible_allowed")) for row in evaluator_target_rows),
            len(evaluator_target_rows),
            "contract_violation",
        ),
        gate(
            "m2891-forbidden-feature-leakage-absent",
            "contract_violation",
            leakage_absent_pass,
            "feature_hidden_oracle=false;feature_future_targets=false;labels_actor_visible=false",
            "feature_hidden_oracle=false;feature_future_targets=false;labels_actor_visible=false",
            "contract_violation",
        ),
        gate(
            "m2891-label-contract-complete",
            "label_contract",
            bool(label_rows) and all(_bool(row["status_pass"]) for row in label_rows),
            len(label_rows),
            len(evaluator_target_rows),
            "metric_artifact",
        ),
        gate(
            "m2891-split-contract-materialized",
            "split_contract",
            bool(split_rows) and all(_bool(row["status_pass"]) for row in split_rows),
            len(split_rows),
            ">=1",
            "scenario_sampling_failure",
        ),
        gate(
            "m2891-source-singleton-exclusions-preserved",
            "proof_boundary",
            len(source_singleton_rows) == int(m2887_summary.get("source_singleton_exclusion_row_count", 0))
            and all(not _bool(row.get("paper_proof_allowed")) for row in source_singleton_rows),
            len(source_singleton_rows),
            m2887_summary.get("source_singleton_exclusion_row_count", 0),
            "proof_washout",
        ),
        gate(
            "m2891-guard-exclusions-preserved",
            "proof_boundary",
            len(guard_rows) == int(m2887_summary.get("guard_exclusion_row_count", 0))
            and all(not _bool(row.get("ordinary_success_denominator_allowed")) for row in guard_rows),
            len(guard_rows),
            m2887_summary.get("guard_exclusion_row_count", 0),
            "proof_washout",
        ),
        gate(
            "m2891-loss-metric-baseline-contracts-materialized",
            "artifact_completeness",
            bool(loss_metric_rows) and bool(baseline_rows) and all(_bool(row["status_pass"]) for row in baseline_rows),
            f"loss_metric_rows={len(loss_metric_rows)};baseline_rows={len(baseline_rows)}",
            "loss_metric_rows>0;baseline_rows=12",
            "metric_artifact",
        ),
        gate(
            "m2891-no-implementation-or-training",
            "claim_boundary",
            no_forbidden_execution and blocked_claim_gate_pass,
            sum(_bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows),
            0,
            "proof_washout",
        ),
        gate(
            "m2891-follow-up-manifest-registered",
            "handoff",
            follow_up_manifest.exists(),
            follow_up_manifest.exists(),
            True,
            "lineage_invalid",
        ),
    ]


def build_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2891 capability-prediction modeling-contract materialization before any implementation or training.",
        "lineage": {
            "parent_checkpoint": summary["baseline_checkpoints"],
            "parent_dataset": [
                summary["artifacts"]["summary"],
                summary["artifacts"]["feature_contract_rows"],
                summary["artifacts"]["label_contract_rows"],
                summary["artifacts"]["split_contract_rows"],
                summary["artifacts"]["loss_metric_contract_rows"],
                summary["artifacts"]["baseline_contract_rows"],
                summary["artifacts"]["modeling_gate_rows"],
                summary["artifacts"]["claim_rows"],
                "docs/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.md",
                "docs/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.md",
            ],
            "parent_config": [
                f"experiments/manifests/{DEFAULT_MILESTONE}.json",
                "experiments/manifests/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.json",
            ],
            "parent_objective": [
                "audit whether M2891 materialized complete actor-safe capability-prediction modeling-contract rows"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design",
                "m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight",
            ],
            "blocked_by": [
                "M2891 must be audited before model implementation or training",
                "17 usable rows remain preflight contract evidence rather than paper proof",
                "evaluator-only targets and exclusion rows must remain outside actor input and proof denominators",
            ],
            "supersedes": [
                "starting capability-prediction implementation without contract materialization audit",
                "treating M2891 contract rows as model-quality or controller-family ranking evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2892 must audit M2891 summary feature label split loss metric baseline gate and claim rows",
            "M2892 must accept or reject actor-safe contract materialization completeness",
            "M2892 must preserve source-singleton guard and evaluator-only target boundaries",
            "M2892 must not train validate fit a model rank promote or claim driver performance finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout validate fit a model train rank promote or publish a package",
            "do not change actor input or action contract",
            "do not convert contract rows into paper proof or controller-family ranking",
            "do not claim driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
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
        "workflow_synthesis": {
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract",
            "evidence_axis": "route_b_capability_prediction_modeling_contract_result_audit",
            "evidence_increment": "audits the first machine-checkable modeling-contract materialization before implementation",
            "claim_scope": "Result audit only; no model implementation fitting training validation ranking finite-window-vs-GRU verdict or self-ID claim",
            "stop_condition": [
                "stop if feature label split loss metric or baseline rows are incomplete",
                "stop if actor or target boundaries fail",
                "stop if the audit would claim driver performance model quality or self-ID evidence",
            ],
            "fallback_plan": [
                "route to dataset repair if contract materialization is incomplete but actor-safe",
                "route to fresh/source-diverse panel design if split coverage is too weak",
                "route to implementation preflight only if audit accepts completeness and boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2891 writes modeling-contract materialization artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2891 capability-prediction modeling-contract materialization result audit",
            "admission_evidence": [
                "M2891 wrote modeling-contract materialization artifacts",
                "M2890 admitted read-only contract materialization before implementation",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation model fitting training ranking promotion",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as paper proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2892 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if the audit selects a route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2891 materialization is accepted or rejected",
                "one next Route B action or stop decision is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2892 audits contract materialization only and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2892; later tests require accepted implementation and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2887-M2891 Route B dataset and modeling-contract materialization.",
            "negative_result_policy": "Preserve insufficient contract or boundary failure as a negative result rather than weakening actor contract.",
            "allowed_claims": [
                "M2891 materialization accepted or rejected",
                "bounded follow-up route or stop decision",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "low",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0 if summary["status_pass"] else 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the newly materialized modeling contract",
            "paper_verdict_delta": "no verdict; may admit later implementation preflight if accepted",
            "must_synthesize_if": [
                "M2892 cannot decide whether M2891 materialization is sufficient",
                "M2892 would claim self-ID finite-window-vs-GRU driver performance or current-sim verdict",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2891 materialization completeness and claim safety",
            "audit selects exactly one bounded next route or stop decision",
        ],
        "failure_criteria": [
            "M2892 resets steps rolls out validates trains ranks promotes or executes policy action",
            "M2892 changes actor input or action contract",
            "M2892 claims driver performance finite-window-vs-GRU verdict paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "decision_rule": "Pass only if M2892 writes a claim-safe audit of M2891 materialization before implementation or training.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": summary["baseline_checkpoints"],
        "baseline_artifacts": [
            summary["artifacts"]["summary"],
            summary["artifacts"]["feature_contract_rows"],
            summary["artifacts"]["label_contract_rows"],
            summary["artifacts"]["split_contract_rows"],
            summary["artifacts"]["baseline_contract_rows"],
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2893-paper-route-l0-l1-l2-l3-capability-prediction-selected-contract-follow-up",
    }


def write_preflight_artifacts(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    m2887_dir: Path = DEFAULT_M2887_DIR,
    m2890_design: Path = DEFAULT_M2890_DESIGN,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    m2887_summary_path = m2887_dir / "summary.json"
    m2887_summary = read_json(m2887_summary_path) if m2887_summary_path.exists() else {}
    usable_task_rows = _read_csv_rows(m2887_dir / "usable_task_rows.csv")
    profile_task_rows = _read_csv_rows(m2887_dir / "profile_task_rows.csv")
    evaluator_target_rows = _read_csv_rows(m2887_dir / "evaluator_target_rows.csv")
    source_singleton_rows = _read_csv_rows(m2887_dir / "excluded_source_singleton_rows.csv")
    guard_rows = _read_csv_rows(m2887_dir / "excluded_guard_rows.csv")
    actor_rows = _read_csv_rows(m2887_dir / "actor_feature_contract_rows.csv")

    feature_rows = build_feature_contract_rows(profile_task_rows)
    label_rows = build_label_contract_rows(evaluator_target_rows)
    split_rows = build_split_contract_rows(usable_task_rows=usable_task_rows, profile_task_rows=profile_task_rows)
    loss_metric_rows = build_loss_metric_contract_rows(label_rows)
    baseline_rows = build_baseline_contract_rows(profile_task_rows)
    claim_rows = build_claim_rows()

    artifacts = {
        "summary": output_dir / "summary.json",
        "feature_contract_rows": output_dir / "feature_contract_rows.csv",
        "label_contract_rows": output_dir / "label_contract_rows.csv",
        "split_contract_rows": output_dir / "split_contract_rows.csv",
        "loss_metric_contract_rows": output_dir / "loss_metric_contract_rows.csv",
        "baseline_contract_rows": output_dir / "baseline_contract_rows.csv",
        "modeling_gate_rows": output_dir / "modeling_gate_rows.csv",
        "claim_rows": output_dir / "claim_rows.csv",
        "run_state": output_dir / "run_state.json",
    }

    baseline_checkpoints = [
        "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
    ]

    # Write the follow-up manifest before gate construction so the handoff gate
    # measures the final filesystem state.
    summary_stub = {
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "status_pass": False,
    }
    follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(follow_up_manifest, build_follow_up_manifest(summary_stub))

    gate_rows = build_gate_rows(
        m2890_design_exists=m2890_design.exists(),
        m2887_summary=m2887_summary,
        profile_task_rows=profile_task_rows,
        evaluator_target_rows=evaluator_target_rows,
        source_singleton_rows=source_singleton_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        feature_rows=feature_rows,
        label_rows=label_rows,
        split_rows=split_rows,
        loss_metric_rows=loss_metric_rows,
        baseline_rows=baseline_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up_manifest,
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    task_family_counts = Counter(row.get("task_family", "") for row in usable_task_rows)
    env_template_counts = Counter(row.get("env_template_family", "") for row in usable_task_rows)
    profile_level_counts = Counter(row.get("profile_level", "") for row in profile_task_rows)
    feature_family_counts = Counter(row.get("feature_family", "") for row in feature_rows)
    decision = (
        "modeling_contract_materialized_route_to_m2892_result_audit"
        if gate_matrix_pass
        else "modeling_contract_incomplete_route_to_m2892_result_audit"
    )

    summary: dict[str, Any] = {
        "milestone": DEFAULT_MILESTONE,
        "generated_at_utc": utc_timestamp(),
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m2887_dir": str(m2887_dir),
        "m2887_summary_exists": m2887_summary_path.exists(),
        "m2887_summary_status_pass": _bool(m2887_summary.get("status_pass")),
        "m2890_design": str(m2890_design),
        "m2890_design_exists": m2890_design.exists(),
        "usable_task_row_count": len(usable_task_rows),
        "profile_task_row_count": len(profile_task_rows),
        "evaluator_target_row_count": len(evaluator_target_rows),
        "source_singleton_exclusion_row_count": len(source_singleton_rows),
        "guard_exclusion_row_count": len(guard_rows),
        "actor_feature_contract_row_count": len(actor_rows),
        "feature_contract_row_count": len(feature_rows),
        "label_contract_row_count": len(label_rows),
        "split_contract_row_count": len(split_rows),
        "loss_metric_contract_row_count": len(loss_metric_rows),
        "baseline_contract_row_count": len(baseline_rows),
        "modeling_gate_row_count": len(gate_rows),
        "claim_row_count": len(claim_rows),
        "required_profile_count": len(REQUIRED_PROFILES),
        "required_profiles": REQUIRED_PROFILES,
        "usable_task_family_counts": dict(sorted(task_family_counts.items())),
        "usable_env_template_counts": dict(sorted(env_template_counts.items())),
        "profile_level_counts": dict(sorted(profile_level_counts.items())),
        "feature_family_counts": dict(sorted(feature_family_counts.items())),
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "hidden_oracle_actor_input_required": any(_bool(row["hidden_oracle_input_allowed"]) for row in feature_rows),
        "future_target_actor_input_required": any(_bool(row["future_target_input_allowed"]) for row in feature_rows),
        "evaluator_targets_actor_visible": any(_bool(row["actor_visible_allowed"]) for row in label_rows),
        "source_singleton_rows_paper_proof_allowed": any(_bool(row.get("paper_proof_allowed")) for row in source_singleton_rows),
        "guard_rows_ordinary_success_denominator_allowed": any(
            _bool(row.get("ordinary_success_denominator_allowed")) for row in guard_rows
        ),
        "paper_holdout_admitted": any(_bool(row["paper_holdout_admitted"]) for row in split_rows),
        "preflight_only_split": all(_bool(row["preflight_only"]) for row in split_rows),
        "all_required_targets_resolvable": all(_bool(row["status_pass"]) for row in label_rows),
        "all_required_features_resolvable": all(_bool(row["status_pass"]) for row in feature_rows),
        "all_required_baselines_resolvable": all(_bool(row["status_pass"]) for row in baseline_rows),
        "false_claim_flags": FALSE_CLAIM_FLAGS.copy(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
    }

    write_csv_rows(artifacts["feature_contract_rows"], feature_rows, fieldnames=FEATURE_FIELDNAMES)
    write_csv_rows(artifacts["label_contract_rows"], label_rows, fieldnames=LABEL_FIELDNAMES)
    write_csv_rows(artifacts["split_contract_rows"], split_rows, fieldnames=SPLIT_FIELDNAMES)
    write_csv_rows(artifacts["loss_metric_contract_rows"], loss_metric_rows, fieldnames=LOSS_METRIC_FIELDNAMES)
    write_csv_rows(artifacts["baseline_contract_rows"], baseline_rows, fieldnames=BASELINE_FIELDNAMES)
    write_csv_rows(artifacts["modeling_gate_rows"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(artifacts["run_state"], {"summary": summary, "follow_up_manifest": build_follow_up_manifest(summary)})
    write_json(artifacts["summary"], summary)
    write_json(follow_up_manifest, build_follow_up_manifest(summary))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--m2887-dir", type=Path, default=DEFAULT_M2887_DIR)
    parser.add_argument("--m2890-design", type=Path, default=DEFAULT_M2890_DESIGN)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = write_preflight_artifacts(
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        m2887_dir=args.m2887_dir,
        m2890_design=args.m2890_design,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"decision={summary['decision']}")
    print(f"feature_contract_row_count={summary['feature_contract_row_count']}")
    print(f"label_contract_row_count={summary['label_contract_row_count']}")
    print(f"split_contract_row_count={summary['split_contract_row_count']}")


if __name__ == "__main__":
    main()
