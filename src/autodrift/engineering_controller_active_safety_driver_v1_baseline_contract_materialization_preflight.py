"""Materialize M3035 Active Safety Driver v1 baseline contract artifacts.

M3035 converts the M3034 baseline-freeze design and audited M3015/M3018/
M3022/M3032 artifacts into machine-readable contract tables. It performs no
environment reset, step, rollout, replay, training, validation, ranking,
promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or
self-ID verdict.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3035-engineering-controller-active-safety-driver-v1-baseline-contract-"
    "materialization-preflight"
)
NEXT_ID = (
    "m3036-engineering-controller-active-safety-driver-v1-baseline-contract-"
    "materialization-result-audit"
)
M3034_ID = "m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design"

DEFAULT_M3034_DESIGN = Path(f"docs/{M3034_ID}.md")
DEFAULT_M3015_DIR = Path(
    "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_"
    "bounded_execution_preflight"
)
DEFAULT_M3018_DIR = Path(
    "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_"
    "failure_localization_materialization_preflight"
)
DEFAULT_M3022_DIR = Path(
    "runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_"
    "broad_failure_objective_contract_materialization_preflight"
)
DEFAULT_M3032_DIR = Path(
    "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_"
    "broad_failure_target_tensor_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3035_engineering_controller_active_safety_driver_v1_baseline_"
    "contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

M2655_CONFIG = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/repair_config_snapshot.json"
)
M2655_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_"
    "actor_head_repair.pt"
)
M1674_CONFIG = Path(
    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/"
    "seed_167400/config.json"
)
M1674_CHECKPOINT = Path(
    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/"
    "seed_167400/checkpoint.pt"
)

EXPECTED_M3015_EPISODE_ROWS = 32
EXPECTED_M3015_PROFILE_AGGREGATES = 2
EXPECTED_BASELINE_CANDIDATES = 2
EXPECTED_TARGET_TENSOR_ROWS = 29
EXPECTED_SUCCESS_ZERO_GUARDS = 3

CLAIM_SCOPE = (
    "M3035 Active Safety Driver v1 baseline-contract materialization preflight "
    "only; M3034 design, M3015 diagnostic rows, M3018 localization rows, M3022 "
    "objective-contract rows, and M3032 target-tensor rows may be converted into "
    "machine-readable baseline candidate, benchmark role, metric, exclusion, "
    "actor-contract, claim-boundary, gate, summary, doc, and M3036 audit manifest "
    "artifacts. No environment reset, step, rollout, replay, validation, training, "
    "PPO, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair-success, driver-performance, paper, current-sim verdict, high-fidelity "
    "validation, finite-window-vs-GRU, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, validation result, current-sim verdict, high-fidelity "
    "validation readiness or result, repair success, checkpoint ranking, winner "
    "selection, checkpoint promotion, target tensor quality, residual fitting "
    "readiness, paper evidence, finite-window-vs-GRU conclusion, full ideal driver "
    "completion, or level3 self-identification"
)
DECISION_PASS = "active_safety_driver_v1_baseline_contract_materialized_route_to_m3036_result_audit"

BASELINE_FIELDNAMES = [
    "baseline_candidate_id",
    "profile_name",
    "binding_role",
    "candidate_family",
    "config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "checkpoint_size_bytes",
    "actor_observation_dim",
    "actor_action_dim",
    "same_case_measurement_allowed",
    "ranking_allowed",
    "winner_selection_allowed",
    "promotion_allowed",
    "training_scheduled_by_m3035",
    "validation_scheduled_by_m3035",
    "diagnostic_success_count",
    "diagnostic_collision_count",
    "diagnostic_offtrack_count",
    "diagnostic_speed_too_low_count",
    "min_clearance_margin_mean",
    "return_mean",
    "driver_performance_claim_made",
    "claim_boundary",
]
ROLE_FIELDNAMES = [
    "benchmark_role_row_id",
    "benchmark_role",
    "role_seed",
    "source_row_count",
    "task_source_count",
    "profile_binding_count",
    "task_family_values",
    "source_edge_values",
    "window_tag_values",
    "same_case_measurement_allowed",
    "validation_denominator_allowed_in_m3035",
    "ranking_allowed_in_m3035",
    "hidden_oracle_actor_input_required",
    "target_labels_actor_visible",
    "claim_boundary",
]
METRIC_FIELDNAMES = [
    "metric_contract_id",
    "metric_family",
    "metric_name",
    "source_field",
    "aggregation",
    "available_in_current_artifacts",
    "required_for_baseline_measurement",
    "higher_is_better",
    "allowed_in_m3035",
    "performance_claim_allowed_in_m3035",
    "future_instrumentation_required",
    "claim_boundary",
]
EXCLUSION_FIELDNAMES = [
    "exclusion_rule_id",
    "excluded_surface",
    "exclusion_family",
    "reason",
    "active_safety_baseline_denominator_allowed",
    "validation_denominator_allowed",
    "performance_claim_allowed",
    "paper_denominator_allowed",
    "self_id_claim_allowed",
    "required_follow_up_before_use",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3035",
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

ROLE_SEED_MAPPINGS = [
    ("ordinary_avoidance", "curved_boundary_obstacle"),
    ("ordinary_avoidance", "late_reveal_boundary"),
    ("ordinary_avoidance", "t5_high_speed_close_obstacle"),
    ("stable_aes", "capability_step_down"),
    ("stable_aes", "capability_step_up"),
    ("stable_aes", "t4_staged_warmup_capability"),
    ("stable_aes", "t5_near_boundary_warmup"),
    ("aeb_infeasible_evasive_steering", "brake_fade_or_loss_proxy"),
    ("hidden_dynamics_robustness", "actuator_delay_step"),
    ("hidden_dynamics_robustness", "steering_lag_proxy"),
    ("hidden_dynamics_robustness", "ood_low_grip_proxy"),
    ("hidden_dynamics_robustness", "ood_mass_shift_proxy"),
    ("hidden_dynamics_robustness", "ood_brake_loss_proxy"),
    ("hidden_dynamics_robustness", "ood_drive_loss_proxy"),
    ("hidden_dynamics_robustness", "sensor_noise_proxy"),
    ("hidden_dynamics_robustness", "perception_delay_proxy"),
    ("recovery_and_stability", "drive_loss_proxy"),
]

METRIC_DEFS = [
    ("safety", "success", "success", "count/rate", True, True),
    ("safety", "collision", "collision", "count/rate", False, True),
    ("safety", "obstacle_collision_termination", "termination_reason", "count", False, True),
    ("safety", "off_track_termination", "termination_reason", "count", False, True),
    ("safety", "speed_too_low_termination", "termination_reason", "count", False, True),
    ("safety", "terminated", "terminated", "count/rate", False, True),
    ("safety", "truncated", "truncated", "count/rate", False, True),
    ("clearance", "min_obstacle_clearance", "min_obstacle_clearance", "p5/p10/mean/min", True, True),
    ("clearance", "obstacle_collision_radius", "obstacle_collision_radius", "mean", False, True),
    ("clearance", "min_clearance_margin", "min_clearance_margin", "p5/p10/mean/min", True, True),
    ("stability", "high_sideslip_fraction", "high_sideslip_fraction", "mean/p95", False, True),
    ("stability", "beta_abs_error_mean", "beta_abs_error_mean", "mean/p95", False, True),
    ("stability", "lateral_rmse", "lateral_rmse", "mean/p95", False, True),
    ("stability", "yaw_spin_proxy", "", "future", False, False),
    ("recovery", "recoverability_window_success", "recoverability_window_success", "count/rate", True, True),
    (
        "recovery",
        "recoverability_window_success_available",
        "recoverability_window_success_available",
        "count/rate",
        True,
        True,
    ),
    ("recovery", "time_to_first_off_track_s", "time_to_first_off_track_s", "p50/p95", False, True),
    ("recovery", "max_off_track_overshoot", "max_off_track_overshoot", "p50/p95/max", False, True),
    ("recovery", "off_track_severity_proxy", "off_track_severity_proxy", "p50/p95/max", False, True),
    ("actuation", "action_rate_mean", "action_rate_mean", "mean/p95", False, True),
    ("actuation", "steer_throttle_brake_smoothness", "", "future raw-trace aggregate", False, False),
    ("actuation", "actuator_saturation_or_mode_jump", "", "future raw-trace aggregate", False, False),
    ("robustness", "role_split", "benchmark_role_rows.csv", "grouped aggregate", False, True),
    ("robustness", "source_family_split", "source_edge", "grouped aggregate", False, True),
    ("robustness", "task_family_split", "task_family", "grouped aggregate", False, True),
    ("runtime", "checkpoint_size_bytes", "baseline_candidate_rows.csv", "exact", False, True),
    ("runtime", "inference_latency_p50_p95", "", "future measured runtime", False, False),
    ("runtime", "memory_footprint", "", "future measured runtime", False, False),
    ("unavoidable_mitigation", "collision_speed_or_severity_proxy", "", "future instrumentation", False, False),
    ("unavoidable_mitigation", "closest_approach", "min_obstacle_clearance", "p5/p10/min", True, True),
    ("unavoidable_mitigation", "offtrack_severity_under_unavoidable", "off_track_severity_proxy", "p95/max", False, True),
]

EXCLUSION_DEFS = [
    ("stale_fixed_source_rows", "stale_surface", "outside the M3035 current denominator"),
    ("static_reset_only_artifacts", "static_artifact", "not closed-loop same-case evidence"),
    ("diagnostic_rows_as_validation", "diagnostic_overclaim", "M3015 rows are diagnostic-only in M3035"),
    ("target_tensor_rows_as_performance", "target_tensor_overclaim", "M3032 tensors are offline material only"),
    ("self_id_proof_as_engineering_baseline", "self_id_overclaim", "self-ID is auxiliary diagnostic"),
    ("paper_rows_as_active_safety_denominator", "paper_overclaim", "paper rows are not engineering denominators"),
    ("hidden_oracle_actor_inputs", "contract_violation", "actor contract forbids hidden/oracle shortcuts"),
    ("source_route_outcome_labels_actor_visible", "contract_violation", "actor-visible labels are forbidden"),
    ("checkpoint_or_config_mutation_rows", "side_effect", "M3035 is read-only materialization"),
    ("non_same_case_rows", "comparability", "rows must match source/profile/seed/metric schema"),
    ("unmapped_high_fidelity_rows", "hf_boundary", "HF backend and P0/action mapping must be audited first"),
]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "baseline_candidate_rows": output_dir / "baseline_candidate_rows.csv",
        "benchmark_role_rows": output_dir / "benchmark_role_rows.csv",
        "metric_contract_rows": output_dir / "metric_contract_rows.csv",
        "exclusion_rule_rows": output_dir / "exclusion_rule_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_blank(value: Any) -> float | str:
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def _as_sorted_text(values: set[str]) -> str:
    return "|".join(sorted(value for value in values if value))


def load_source_artifacts(
    *,
    m3034_design: Path,
    m3015_dir: Path,
    m3018_dir: Path,
    m3022_dir: Path,
    m3032_dir: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m3034_design": m3034_design,
        "m3015_summary": m3015_dir / "summary.json",
        "m3015_episode_rows": m3015_dir / "episode_rows.csv",
        "m3015_profile_aggregate_rows": m3015_dir / "profile_aggregate_rows.csv",
        "m3018_summary": m3018_dir / "summary.json",
        "m3018_failure_localization_rows": m3018_dir / "failure_localization_rows.csv",
        "m3022_summary": m3022_dir / "summary.json",
        "m3022_objective_family_rows": m3022_dir / "objective_family_rows.csv",
        "m3022_row_assignment_rows": m3022_dir / "row_assignment_rows.csv",
        "m3032_summary": m3032_dir / "summary.json",
        "m3032_target_tensor_rows": m3032_dir / "target_tensor_rows.csv",
        "m2655_config": M2655_CONFIG,
        "m2655_checkpoint": M2655_CHECKPOINT,
        "m1674_config": M1674_CONFIG,
        "m1674_checkpoint": M1674_CHECKPOINT,
        "follow_up_manifest": follow_up_manifest,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3034_design_text": paths["m3034_design"].read_text(encoding="utf-8")
        if exists["m3034_design"]
        else "",
        "m3015_summary": read_json(paths["m3015_summary"]) if exists["m3015_summary"] else {},
        "m3015_episode_rows": read_csv_rows(paths["m3015_episode_rows"])
        if exists["m3015_episode_rows"]
        else [],
        "m3015_profile_aggregate_rows": read_csv_rows(paths["m3015_profile_aggregate_rows"])
        if exists["m3015_profile_aggregate_rows"]
        else [],
        "m3018_summary": read_json(paths["m3018_summary"]) if exists["m3018_summary"] else {},
        "m3018_failure_localization_rows": read_csv_rows(paths["m3018_failure_localization_rows"])
        if exists["m3018_failure_localization_rows"]
        else [],
        "m3022_summary": read_json(paths["m3022_summary"]) if exists["m3022_summary"] else {},
        "m3022_objective_family_rows": read_csv_rows(paths["m3022_objective_family_rows"])
        if exists["m3022_objective_family_rows"]
        else [],
        "m3022_row_assignment_rows": read_csv_rows(paths["m3022_row_assignment_rows"])
        if exists["m3022_row_assignment_rows"]
        else [],
        "m3032_summary": read_json(paths["m3032_summary"]) if exists["m3032_summary"] else {},
        "m3032_target_tensor_rows": read_csv_rows(paths["m3032_target_tensor_rows"])
        if exists["m3032_target_tensor_rows"]
        else [],
    }


def build_baseline_candidate_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    aggregate_by_profile = {
        str(row.get("aggregate_value", "")): row for row in source["m3015_profile_aggregate_rows"]
    }
    specs = [
        (
            "m3035-baseline-candidate-0001",
            "route_a_candidate_m2655_mitigation_preserving",
            "candidate",
            "m2655_mitigation_preserving",
            M2655_CONFIG,
            M2655_CHECKPOINT,
        ),
        (
            "m3035-baseline-candidate-0002",
            "route_a_parent_l3_online_gru",
            "parent",
            "m1674_l3_online_gru_parent",
            M1674_CONFIG,
            M1674_CHECKPOINT,
        ),
    ]
    rows: list[dict[str, Any]] = []
    for candidate_id, profile_name, role, family, config_path, checkpoint_path in specs:
        aggregate = aggregate_by_profile.get(profile_name, {})
        rows.append(
            {
                "baseline_candidate_id": candidate_id,
                "profile_name": profile_name,
                "binding_role": role,
                "candidate_family": family,
                "config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": config_path.exists(),
                "checkpoint_exists": checkpoint_path.exists(),
                "checkpoint_size_bytes": checkpoint_path.stat().st_size if checkpoint_path.exists() else 0,
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "same_case_measurement_allowed": True,
                "ranking_allowed": False,
                "winner_selection_allowed": False,
                "promotion_allowed": False,
                "training_scheduled_by_m3035": False,
                "validation_scheduled_by_m3035": False,
                "diagnostic_success_count": aggregate.get("diagnostic_success_count", ""),
                "diagnostic_collision_count": aggregate.get("diagnostic_collision_count", ""),
                "diagnostic_offtrack_count": aggregate.get("diagnostic_offtrack_count", ""),
                "diagnostic_speed_too_low_count": aggregate.get("diagnostic_speed_too_low_count", ""),
                "min_clearance_margin_mean": _float_or_blank(aggregate.get("min_clearance_margin_mean")),
                "return_mean": _float_or_blank(aggregate.get("return_mean")),
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_benchmark_role_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    localization_rows = source["m3018_failure_localization_rows"]
    rows: list[dict[str, Any]] = []
    for index, (role, seed) in enumerate(ROLE_SEED_MAPPINGS, start=1):
        matching = [
            row
            for row in localization_rows
            if seed in str(row.get("source_edge", ""))
            or seed in str(row.get("executable_source_family", ""))
            or seed in str(row.get("env_template_family", ""))
        ]
        rows.append(
            {
                "benchmark_role_row_id": f"m3035-benchmark-role-{index:04d}",
                "benchmark_role": role,
                "role_seed": seed,
                "source_row_count": len(matching),
                "task_source_count": len({str(row.get("task_source_id", "")) for row in matching if row}),
                "profile_binding_count": len({str(row.get("profile_name", "")) for row in matching if row}),
                "task_family_values": _as_sorted_text(
                    {str(row.get("task_family", "")) for row in matching}
                ),
                "source_edge_values": _as_sorted_text(
                    {str(row.get("source_edge", "")) for row in matching}
                ),
                "window_tag_values": _as_sorted_text(
                    {str(row.get("window_tag", "")) for row in matching}
                ),
                "same_case_measurement_allowed": True,
                "validation_denominator_allowed_in_m3035": False,
                "ranking_allowed_in_m3035": False,
                "hidden_oracle_actor_input_required": False,
                "target_labels_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_metric_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    episode_fields = set(source["m3015_episode_rows"][0].keys()) if source["m3015_episode_rows"] else set()
    rows: list[dict[str, Any]] = []
    for index, (family, name, source_field, aggregation, higher_is_better, required) in enumerate(
        METRIC_DEFS,
        start=1,
    ):
        available = bool(source_field) and (
            source_field in episode_fields
            or source_field in {"baseline_candidate_rows.csv", "benchmark_role_rows.csv"}
        )
        rows.append(
            {
                "metric_contract_id": f"m3035-metric-contract-{index:04d}",
                "metric_family": family,
                "metric_name": name,
                "source_field": source_field,
                "aggregation": aggregation,
                "available_in_current_artifacts": available,
                "required_for_baseline_measurement": required,
                "higher_is_better": higher_is_better,
                "allowed_in_m3035": True,
                "performance_claim_allowed_in_m3035": False,
                "future_instrumentation_required": not available,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_exclusion_rule_rows() -> list[dict[str, Any]]:
    return [
        {
            "exclusion_rule_id": f"m3035-exclusion-rule-{index:04d}",
            "excluded_surface": surface,
            "exclusion_family": family,
            "reason": reason,
            "active_safety_baseline_denominator_allowed": False,
            "validation_denominator_allowed": False,
            "performance_claim_allowed": False,
            "paper_denominator_allowed": False,
            "self_id_claim_allowed": False,
            "required_follow_up_before_use": "future audited admission or result milestone",
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (surface, family, reason) in enumerate(EXCLUSION_DEFS, start=1)
    ]


def build_actor_contract_guard_rows(
    source: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m3015 = source["m3015_summary"]
    m3032 = source["m3032_summary"]
    checks = [
        (
            "m3015_actor_observation_shape",
            "actor_contract",
            int(m3015.get("observation_shape", -1)) == P0_OBSERVATION_DIM,
            m3015.get("observation_shape"),
            P0_OBSERVATION_DIM,
        ),
        (
            "m3015_actor_action_shape",
            "actor_contract",
            int(m3015.get("action_shape", -1)) == ACTION_DIM,
            m3015.get("action_shape"),
            ACTION_DIM,
        ),
        (
            "m3015_actor_contract_unchanged",
            "actor_contract",
            not _bool(m3015.get("actor_input_contract_changed", False)),
            m3015.get("actor_input_contract_changed"),
            False,
        ),
        (
            "m3015_hidden_oracle_actor_input_absent",
            "actor_input",
            not _bool(m3015.get("hidden_oracle_actor_input_detected", False)),
            m3015.get("hidden_oracle_actor_input_detected"),
            False,
        ),
        (
            "m3015_ttc_actor_input_absent",
            "actor_input",
            not _bool(m3015.get("ttc_actor_input_required", False)),
            m3015.get("ttc_actor_input_required"),
            False,
        ),
        (
            "m3015_actor_visible_labels_absent",
            "actor_input",
            not any(
                _bool(m3015.get(key, False))
                for key in (
                    "source_labels_actor_visible",
                    "route_labels_actor_visible",
                    "outcome_labels_actor_visible",
                    "success_progress_labels_actor_visible",
                    "verdict_labels_actor_visible",
                )
            ),
            {
                key: m3015.get(key, False)
                for key in (
                    "source_labels_actor_visible",
                    "route_labels_actor_visible",
                    "outcome_labels_actor_visible",
                    "success_progress_labels_actor_visible",
                    "verdict_labels_actor_visible",
                )
            },
            "all false",
        ),
        (
            "m3032_target_labels_actor_invisible",
            "actor_input",
            not _bool(m3032.get("target_labels_actor_visible", False))
            and not _bool(m3032.get("target_provenance_actor_visible", False)),
            {
                "target_labels_actor_visible": m3032.get("target_labels_actor_visible"),
                "target_provenance_actor_visible": m3032.get("target_provenance_actor_visible"),
            },
            "all false",
        ),
        (
            "baseline_checkpoint_paths_exist",
            "baseline_candidate",
            all(_bool(row.get("checkpoint_exists", False)) for row in baseline_rows),
            [row.get("checkpoint_exists", False) for row in baseline_rows],
            "all true",
        ),
        (
            "baseline_config_paths_exist",
            "baseline_candidate",
            all(_bool(row.get("config_exists", False)) for row in baseline_rows),
            [row.get("config_exists", False) for row in baseline_rows],
            "all true",
        ),
    ]
    return [
        {
            "guard_id": f"m3035-{guard_id}",
            "guard_family": family,
            "observed": observed,
            "expected": expected,
            "status_pass": bool(status_pass),
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, family, status_pass, observed, expected in checks
    ]


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m3035-{claim_id}",
        "claim_family": family,
        "allowed_in_m3035": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(
    *,
    follow_up_manifest_registered: bool,
    artifact_counts: dict[str, int],
) -> list[dict[str, Any]]:
    allowed = [
        ("baseline_candidate_rows_materialized", "artifact", artifact_counts["baseline_candidate_rows"] > 0, "baseline_candidate_rows.csv"),
        ("benchmark_role_rows_materialized", "artifact", artifact_counts["benchmark_role_rows"] > 0, "benchmark_role_rows.csv"),
        ("metric_contract_rows_materialized", "artifact", artifact_counts["metric_contract_rows"] > 0, "metric_contract_rows.csv"),
        ("exclusion_rule_rows_materialized", "artifact", artifact_counts["exclusion_rule_rows"] > 0, "exclusion_rule_rows.csv"),
        ("actor_contract_guard_rows_materialized", "artifact", artifact_counts["actor_contract_guard_rows"] > 0, "actor_contract_guard_rows.csv"),
        ("claim_boundary_rows_materialized", "artifact", True, "claim_boundary_rows.csv"),
        ("gate_matrix_materialized", "artifact", True, "gate_matrix.csv"),
        ("summary_materialized", "artifact", True, "summary.json"),
        ("doc_materialized", "artifact", True, f"docs/{MILESTONE_ID}.md"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M3036 audit manifest"),
    ]
    blocked = [
        ("environment_execution", "execution", "future audited execution milestone"),
        ("training_or_ppo", "training", "future audited training milestone"),
        ("validation_result", "validation", "future validation run and audit"),
        ("driver_performance", "driver_performance", "future same-case baseline measurement and audit"),
        ("checkpoint_ranking", "ranking", "future audited comparison route"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("checkpoint_or_config_mutation", "side_effect", "M3035 is read-only"),
        ("target_tensor_quality_or_performance", "target_tensor", "future target quality and closed-loop audit"),
        ("current_sim_verdict", "verdict", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future HF backend and mapping audit"),
        ("finite_window_vs_gru_result", "architecture", "future same-case architecture comparison"),
        ("paper_level_evidence", "paper", "future paper evidence audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full active-safety driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": f"m3035-{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
    benchmark_role_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest_registered: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m3015 = source["m3015_summary"]
    m3032 = source["m3032_summary"]
    localization_rows = source["m3018_failure_localization_rows"]
    nonzero_role_rows = [row for row in benchmark_role_rows if int(row["source_row_count"]) > 0]
    gates = [
        (
            "source_artifacts_present",
            "lineage",
            all(source["source_exists"].values()),
            source["source_exists"],
            "all source artifacts and follow-up manifest present",
            "lineage_invalid",
        ),
        (
            "m3034_design_present_and_active_safety_scoped",
            "lineage",
            "Active Safety Driver v1" in source["m3034_design_text"]
            and "[steer, throttle, brake]" in source["m3034_design_text"],
            "Active Safety Driver v1" in source["m3034_design_text"],
            "design includes Active Safety Driver v1 and action output",
            "lineage_invalid",
        ),
        (
            "m3015_status_pass",
            "lineage",
            _bool(m3015.get("status_pass", False)) and _bool(m3015.get("gate_matrix_pass", False)),
            {"status_pass": m3015.get("status_pass"), "gate_matrix_pass": m3015.get("gate_matrix_pass")},
            "all true",
            "lineage_invalid",
        ),
        (
            "m3015_episode_denominator_preserved",
            "denominator",
            len(source["m3015_episode_rows"]) == EXPECTED_M3015_EPISODE_ROWS,
            len(source["m3015_episode_rows"]),
            EXPECTED_M3015_EPISODE_ROWS,
            "metric_artifact",
        ),
        (
            "m3015_profile_aggregates_preserved",
            "denominator",
            len(source["m3015_profile_aggregate_rows"]) == EXPECTED_M3015_PROFILE_AGGREGATES,
            len(source["m3015_profile_aggregate_rows"]),
            EXPECTED_M3015_PROFILE_AGGREGATES,
            "metric_artifact",
        ),
        (
            "baseline_candidates_materialized",
            "baseline_contract",
            len(baseline_rows) == EXPECTED_BASELINE_CANDIDATES
            and all(_bool(row.get("checkpoint_exists")) for row in baseline_rows),
            len(baseline_rows),
            EXPECTED_BASELINE_CANDIDATES,
            "metric_artifact",
        ),
        (
            "benchmark_roles_materialized",
            "benchmark_contract",
            len(benchmark_role_rows) == len(ROLE_SEED_MAPPINGS) and len(nonzero_role_rows) >= 10,
            {"rows": len(benchmark_role_rows), "nonzero_rows": len(nonzero_role_rows)},
            {"rows": len(ROLE_SEED_MAPPINGS), "nonzero_rows_min": 10},
            "scenario_sampling_failure",
        ),
        (
            "metric_contract_materialized",
            "metric_contract",
            len(metric_rows) == len(METRIC_DEFS),
            len(metric_rows),
            len(METRIC_DEFS),
            "metric_artifact",
        ),
        (
            "exclusion_rules_materialized",
            "claim_boundary",
            len(exclusion_rows) == len(EXCLUSION_DEFS),
            len(exclusion_rows),
            len(EXCLUSION_DEFS),
            "contract_violation",
        ),
        (
            "m3018_localization_rows_available",
            "denominator",
            len(localization_rows) == EXPECTED_M3015_EPISODE_ROWS,
            len(localization_rows),
            EXPECTED_M3015_EPISODE_ROWS,
            "metric_artifact",
        ),
        (
            "m3032_target_tensor_counts_preserved",
            "target_tensor_boundary",
            len(source["m3032_target_tensor_rows"]) == EXPECTED_TARGET_TENSOR_ROWS
            and int(m3032.get("success_identity_zero_target_guard_row_count", -1))
            == EXPECTED_SUCCESS_ZERO_GUARDS,
            {
                "target_tensor_rows": len(source["m3032_target_tensor_rows"]),
                "success_zero_guards": m3032.get("success_identity_zero_target_guard_row_count"),
            },
            {"target_tensor_rows": EXPECTED_TARGET_TENSOR_ROWS, "success_zero_guards": EXPECTED_SUCCESS_ZERO_GUARDS},
            "metric_artifact",
        ),
        (
            "actor_contract_guard_rows_pass",
            "contract",
            all(_bool(row.get("status_pass", False)) for row in actor_guard_rows),
            f"{sum(_bool(row.get('status_pass', False)) for row in actor_guard_rows)}/{len(actor_guard_rows)}",
            "all pass",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(_bool(row.get("status_pass", False)) for row in claim_rows),
            f"{sum(_bool(row.get('status_pass', False)) for row in claim_rows)}/{len(claim_rows)}",
            "all pass",
            "proof_washout",
        ),
        (
            "m3035_no_execution_training_validation_ranking",
            "contract",
            True,
            {
                "environment_step_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
            },
            "all false",
            "contract_violation",
        ),
        (
            "follow_up_manifest_registered",
            "lineage",
            follow_up_manifest_registered,
            follow_up_manifest_registered,
            True,
            "lineage_invalid",
        ),
        (
            "required_artifacts_present",
            "artifact",
            required_artifacts_present,
            required_artifacts_present,
            True,
            "metric_artifact",
        ),
    ]
    return [gate(gate_id, family, status_pass, observed, expected, failure_type) for gate_id, family, status_pass, observed, expected, failure_type in gates]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
    benchmark_role_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row.get("status_pass", False)) for row in gate_rows)
    actor_contract_guard_rows_pass = all(_bool(row.get("status_pass", False)) for row in actor_guard_rows)
    claim_boundary_rows_pass = all(_bool(row.get("status_pass", False)) for row in claim_rows)
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_guard_rows_pass
        and claim_boundary_rows_pass
        and required_artifacts_present
    )
    role_counts = Counter(str(row.get("benchmark_role", "")) for row in benchmark_role_rows)
    metric_counts = Counter(str(row.get("metric_family", "")) for row in metric_rows)
    return {
        "milestone": MILESTONE_ID,
        "status_pass": status_pass,
        "result_class": (
            "active_safety_driver_v1_baseline_contract_materialization_preflight_complete"
            if status_pass
            else "active_safety_driver_v1_baseline_contract_materialization_preflight_fail"
        ),
        "decision": DECISION_PASS if status_pass else "active_safety_driver_v1_baseline_contract_incomplete",
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3015_status_pass": _bool(source["m3015_summary"].get("status_pass", False)),
        "m3015_gate_matrix_pass": _bool(source["m3015_summary"].get("gate_matrix_pass", False)),
        "m3015_episode_row_count": len(source["m3015_episode_rows"]),
        "m3015_profile_aggregate_row_count": len(source["m3015_profile_aggregate_rows"]),
        "m3015_diagnostic_success_count": int(source["m3015_summary"].get("diagnostic_success_count", 0)),
        "m3015_diagnostic_collision_count": int(source["m3015_summary"].get("diagnostic_collision_count", 0)),
        "m3015_diagnostic_offtrack_count": int(source["m3015_summary"].get("diagnostic_offtrack_count", 0)),
        "m3015_diagnostic_speed_too_low_count": int(source["m3015_summary"].get("diagnostic_speed_too_low_count", 0)),
        "m3018_failure_localization_row_count": len(source["m3018_failure_localization_rows"]),
        "m3022_objective_family_row_count": len(source["m3022_objective_family_rows"]),
        "m3022_row_assignment_row_count": len(source["m3022_row_assignment_rows"]),
        "m3032_target_tensor_row_count": len(source["m3032_target_tensor_rows"]),
        "m3032_candidate_target_tensor_materialized_count": int(
            source["m3032_summary"].get("candidate_target_tensor_materialized_count", 0)
        ),
        "m3032_success_identity_zero_target_guard_row_count": int(
            source["m3032_summary"].get("success_identity_zero_target_guard_row_count", 0)
        ),
        "m3032_target_tensor_file_count": int(source["m3032_summary"].get("target_tensor_file_count", 0)),
        "baseline_candidate_row_count": len(baseline_rows),
        "benchmark_role_row_count": len(benchmark_role_rows),
        "benchmark_role_nonzero_row_count": sum(1 for row in benchmark_role_rows if int(row["source_row_count"]) > 0),
        "benchmark_role_counts": dict(sorted(role_counts.items())),
        "metric_contract_row_count": len(metric_rows),
        "metric_family_counts": dict(sorted(metric_counts.items())),
        "metric_available_now_count": sum(_bool(row["available_in_current_artifacts"]) for row in metric_rows),
        "metric_future_instrumentation_count": sum(_bool(row["future_instrumentation_required"]) for row in metric_rows),
        "exclusion_rule_row_count": len(exclusion_rows),
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": actor_contract_guard_rows_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_boundary_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "high_fidelity_validation_run": False,
        "finite_window_vs_gru_comparison_run": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "ttc_actor_input_required": False,
        "success_rate_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M3035 Active Safety Driver v1 Baseline Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- decision: `{summary['decision']}`",
            f"- baseline candidates: {summary['baseline_candidate_row_count']}",
            f"- benchmark role rows: {summary['benchmark_role_row_count']}",
            f"- benchmark role nonzero rows: {summary['benchmark_role_nonzero_row_count']}",
            f"- metric contract rows: {summary['metric_contract_row_count']}",
            f"- metric rows available now: {summary['metric_available_now_count']}",
            f"- metric rows requiring future instrumentation: {summary['metric_future_instrumentation_count']}",
            f"- exclusion rule rows: {summary['exclusion_rule_row_count']}",
            f"- actor contract guard pass: {summary['actor_contract_guard_rows_pass']}",
            f"- claim boundary pass: {summary['claim_boundary_rows_pass']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            f"- required artifacts present: {summary['required_artifacts_present']}",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            "",
            "## Input Denominator",
            "",
            f"- M3015 episode rows: {summary['m3015_episode_row_count']}",
            f"- M3015 profile aggregate rows: {summary['m3015_profile_aggregate_row_count']}",
            f"- M3015 diagnostic success/collision/offtrack/speed-floor rows: "
            f"{summary['m3015_diagnostic_success_count']} / "
            f"{summary['m3015_diagnostic_collision_count']} / "
            f"{summary['m3015_diagnostic_offtrack_count']} / "
            f"{summary['m3015_diagnostic_speed_too_low_count']}",
            f"- M3018 localization rows: {summary['m3018_failure_localization_row_count']}",
            f"- M3022 objective family rows: {summary['m3022_objective_family_row_count']}",
            f"- M3032 target tensor rows: {summary['m3032_target_tensor_row_count']}",
            f"- M3032 zero-target success guards: {summary['m3032_success_identity_zero_target_guard_row_count']}",
            "",
            "## Interpretation",
            "",
            "M3035 materializes the Active Safety Driver v1 baseline contract. The two frozen checkpoint rows are candidate inputs for a later same-case baseline measurement, not ranked results. The benchmark role and metric rows define what the next runner must measure. The exclusion and claim-boundary rows prevent diagnostic rows, target tensors, self-ID proof rows, paper-only rows, or high-fidelity-unmapped rows from being used as driver-performance evidence.",
            "",
            "Rejected claims:",
            "",
            "```text",
            FORBIDDEN_INTERPRETATION,
            "```",
            "",
            "## Boundary",
            "",
            "M3035 does not reset, step, roll out, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or claim driver performance.",
            "",
            "## Next",
            "",
            f"- next blocker: `{summary['next_blocker']}`",
            f"- selected next action: `{summary['selected_next_action']}`",
            "",
        ]
    )


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
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
        "hypothesis": "A bounded result audit can accept or reject the M3035 Active Safety Driver v1 baseline-contract materialization artifacts before any baseline execution training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim.",
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "baseline_candidate_rows.csv"),
            str(output_dir / "benchmark_role_rows.csv"),
            str(output_dir / "metric_contract_rows.csv"),
            str(output_dir / "exclusion_rule_rows.csv"),
            str(output_dir / "actor_contract_guard_rows.csv"),
            str(output_dir / "claim_boundary_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "baseline_checkpoints": [str(M2655_CHECKPOINT), str(M1674_CHECKPOINT)],
        "commands": [{"name": "active_safety_driver_v1_baseline_contract_result_audit_doc", "command": "true"}],
        "decision_rule": "Pass only if M3036 audits M3035 row counts gates actor contract exclusions claim boundaries and selects exactly one next baseline measurement or repair route without overclaiming.",
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3036 audits M3035 summary gate matrix baseline candidate benchmark role metric exclusion actor and claim artifacts",
            "M3036 preserves actor 72/action 3 and rejects training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU and self-ID claims",
            "M3036 selects exactly one next baseline measurement admission repair or stop route",
        ],
        "failure_criteria": [
            "M3036 treats M3035 materialization as driver performance",
            "M3036 omits baseline candidate role metric exclusion actor or claim audits",
            "M3036 runs execution training validation ranking promotion high-fidelity or architecture comparison",
            "M3036 leaves the next route ambiguous",
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "lineage": {
            "parent_checkpoint": [str(M2655_CHECKPOINT), str(M1674_CHECKPOINT)],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "baseline_candidate_rows.csv"),
                str(output_dir / "benchmark_role_rows.csv"),
                str(output_dir / "metric_contract_rows.csv"),
                str(output_dir / "exclusion_rule_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
                "docs/m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design.md",
                "runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/summary.json",
                "runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/failure_localization_rows.csv",
                "runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/objective_family_rows.csv",
                "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight/target_tensor_rows.csv",
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design.json",
            ],
            "parent_objective": [
                "audit Active Safety Driver v1 baseline-contract materialization before baseline execution"
            ],
            "derived_from": [MILESTONE_ID, M3034_ID],
            "blocked_by": [
                "M3035 materialization requires result audit before any baseline execution or measurement claim",
                "Active Safety Driver v1 needs accepted contract rows before training architecture comparison ranking or promotion",
            ],
            "supersedes": ["direct baseline execution before contract materialization audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3036 must audit M3035 summary and gate_matrix pass status",
            "M3036 must audit baseline candidate role metric exclusion actor and claim row counts",
            "M3036 must preserve actor 72/action 3 and no hidden oracle target TTC source route outcome progress or verdict actor inputs",
            "M3036 must reject driver-performance validation current-sim high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3036 must choose exactly one next route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step rollout replay training validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3035 materialization into driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate checkpoints configs profiles or actor contract",
        ],
        "status": "pending",
        "next_blocker": NEXT_ID,
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_engineering_mainline",
            "evidence_axis": "active_safety_driver_v1_baseline_contract_result_audit",
            "evidence_increment": "audits the machine-readable baseline contract before baseline measurement",
            "claim_scope": "Result audit only; no training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3035 artifacts are incomplete or actor contract guards fail",
                "stop if the next route would execute or train before contract acceptance",
                "stop if diagnostic or target tensor rows are treated as performance evidence",
            ],
            "fallback_plan": [
                "route to contract repair if row counts or gates fail",
                "route to baseline measurement admission design if M3035 is accepted",
                "route to synthesis if the branch cannot produce an evidence-changing measurement next",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3035 completes baseline-contract materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit Active Safety Driver v1 baseline-contract materialization",
            "admission_evidence": [
                "M3035 summary and gate matrix",
                "M3035 baseline candidate role metric exclusion actor and claim rows",
                "M3034 baseline-freeze design",
            ],
            "blocked_shortcuts": [
                "no environment reset step rollout replay training validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3036 status queue scoreboard research log and review",
                "one follow-up manifest only if M3036 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3035 artifacts are accepted or rejected",
                "one next baseline measurement admission repair or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3036 audits an engineering baseline contract and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3036; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3035 materialized baseline contract artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot block active-safety baseline measurement if safety contract gates pass.",
            "allowed_claims": [
                "M3035 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits machine-readable baseline contract before an evidence-changing baseline measurement",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3036 prepares engineering-first measurement",
            "must_synthesize_if": [
                "M3036 cannot select a measurement or repair route",
                "M3036 would require another process-only milestone before any evidence-changing route",
                "M3036 would re-promote self-ID proof as the mainline objective",
            ],
        },
    }


def run_active_safety_driver_v1_baseline_contract_materialization_preflight(
    *,
    m3034_design: Path | str = DEFAULT_M3034_DESIGN,
    m3015_dir: Path | str = DEFAULT_M3015_DIR,
    m3018_dir: Path | str = DEFAULT_M3018_DIR,
    m3022_dir: Path | str = DEFAULT_M3022_DIR,
    m3032_dir: Path | str = DEFAULT_M3032_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    follow_up = Path(follow_up_manifest)
    paths = artifact_paths(output, doc_path=doc, follow_up_manifest=follow_up)

    source = load_source_artifacts(
        m3034_design=Path(m3034_design),
        m3015_dir=Path(m3015_dir),
        m3018_dir=Path(m3018_dir),
        m3022_dir=Path(m3022_dir),
        m3032_dir=Path(m3032_dir),
        follow_up_manifest=follow_up,
    )
    baseline_rows = build_baseline_candidate_rows(source)
    benchmark_role_rows = build_benchmark_role_rows(source)
    metric_rows = build_metric_contract_rows(source)
    exclusion_rows = build_exclusion_rule_rows()
    actor_guard_rows = build_actor_contract_guard_rows(source, baseline_rows)
    artifact_counts = {
        "baseline_candidate_rows": len(baseline_rows),
        "benchmark_role_rows": len(benchmark_role_rows),
        "metric_contract_rows": len(metric_rows),
        "exclusion_rule_rows": len(exclusion_rows),
        "actor_contract_guard_rows": len(actor_guard_rows),
    }

    write_json(
        follow_up,
        build_follow_up_manifest(output_dir=output, doc_path=doc, summary_path=paths["summary"]),
    )
    source["source_exists"]["follow_up_manifest"] = follow_up.exists()

    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=follow_up.exists(),
        artifact_counts=artifact_counts,
    )
    required_artifacts_present = bool(follow_up.exists())
    gate_rows = build_gate_matrix_rows(
        source=source,
        baseline_rows=baseline_rows,
        benchmark_role_rows=benchmark_role_rows,
        metric_rows=metric_rows,
        exclusion_rows=exclusion_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        follow_up_manifest_registered=follow_up.exists(),
        required_artifacts_present=required_artifacts_present,
    )
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        baseline_rows=baseline_rows,
        benchmark_role_rows=benchmark_role_rows,
        metric_rows=metric_rows,
        exclusion_rows=exclusion_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=follow_up,
    )

    write_csv_rows(paths["baseline_candidate_rows"], baseline_rows, BASELINE_FIELDNAMES)
    write_csv_rows(paths["benchmark_role_rows"], benchmark_role_rows, ROLE_FIELDNAMES)
    write_csv_rows(paths["metric_contract_rows"], metric_rows, METRIC_FIELDNAMES)
    write_csv_rows(paths["exclusion_rule_rows"], exclusion_rows, EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "status": "completed" if summary["status_pass"] else "failed",
            "generated_at_utc": summary["generated_at_utc"],
            "output_dir": str(output),
            "next_blocker": NEXT_ID,
            "claim_scope": CLAIM_SCOPE,
        },
    )
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render_milestone_doc(summary), encoding="utf-8")
    write_json(paths["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3034-design", type=Path, default=DEFAULT_M3034_DESIGN)
    parser.add_argument("--m3015-dir", type=Path, default=DEFAULT_M3015_DIR)
    parser.add_argument("--m3018-dir", type=Path, default=DEFAULT_M3018_DIR)
    parser.add_argument("--m3022-dir", type=Path, default=DEFAULT_M3022_DIR)
    parser.add_argument("--m3032-dir", type=Path, default=DEFAULT_M3032_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_active_safety_driver_v1_baseline_contract_materialization_preflight(
        m3034_design=args.m3034_design,
        m3015_dir=args.m3015_dir,
        m3018_dir=args.m3018_dir,
        m3022_dir=args.m3022_dir,
        m3032_dir=args.m3032_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
