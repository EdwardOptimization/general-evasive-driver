"""No-rollout candidate generation for outcome-supported decisive tasks."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_json


BRANCH_ID = "paper_route_outcome_supported_decisive_task_distribution"
CANDIDATE_SET_ID = "paper_route_outcome_supported_decisive_task_candidates_v0"
DEFAULT_OUTPUT = Path("configs/paper_route_outcome_supported_decisive_task_candidates_v0.json")
DEFAULT_NEXT_BLOCKER = "m2061-paper-route-outcome-supported-decisive-task-candidate-generation-result-audit"

FAMILY_TARGETS = {
    "T1_reactive_active_safety": 48,
    "T2_same_current_different_older_history": 60,
    "T3_active_diagnostic_warmup": 60,
    "T4_variable_diagnostic_delay": 36,
    "T5_terminal_boundary_near_constraint": 36,
}
SPLIT_TARGETS = {"public_debug": 144, "public_gate": 96, "private_holdout": 0}

DIFFICULTY_AXES = {
    "obstacle_distance_band": ("early", "medium", "late"),
    "road_width_band": ("generous", "nominal", "tight"),
    "curvature_band": ("straight_or_low", "moderate", "high"),
    "dynamics_band": ("nominal_mu", "low_mu", "mixed_mu", "actuator_delay"),
    "initial_speed_band": ("low", "nominal", "high"),
}

SENTINEL_PROFILES = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_50",
    "L3_online_gru",
    "L3_reset_control_corrected",
)
FULL_PROFILE_MATRIX = (
    "L0_current_masked",
    "L1_one_step",
    "L2_window_13",
    "L2_window_25",
    "L2_window_50",
    "L2_window_100",
    "L2_window_13_current_tiled",
    "L2_window_25_current_tiled",
    "L2_window_50_current_tiled",
    "L2_window_100_current_tiled",
    "L3_online_gru",
    "L3_reset_control_corrected",
)

ALLOWED_ACTOR_INPUT_FIELDS = (
    "ego_kinematics",
    "imu_like_response",
    "steering_actuator_state",
    "throttle_actuator_state",
    "brake_actuator_state",
    "previous_physical_commands",
    "ego_frame_road_free_space_obstacle_geometry",
    "finite_window_or_recurrent_command_response_history",
)
FORBIDDEN_ACTOR_INPUT_FIELDS = (
    "mu",
    "mass",
    "cg",
    "tire_stiffness",
    "brake_scale",
    "actuator_tau",
    "slip_ratio",
    "slip_angle",
    "tire_force",
    "friction_margin",
    "oracle_feasibility",
    "aeb_label",
    "aes_label",
    "drift_required_label",
    "controller_mode",
    "reference_path",
    "ttc",
    "required_clearance",
    "oracle_stopping_distance",
    "collision_label",
    "success_label",
    "progress_label",
)
FORBIDDEN_BOOL_FIELDS = (
    "labels_enter_actor_input",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)

FAMILY_SOURCE_KINDS = {
    "T1_reactive_active_safety": (
        "ordinary_reactive_stable_aes",
        "late_obstacle_reactive_evasion",
        "low_mu_reactive_evasion",
        "narrow_road_reactive_evasion",
        "high_speed_reactive_evasion",
        "curved_road_reactive_evasion",
    ),
    "T2_same_current_different_older_history": (
        "same_current_brake_authority_older_history",
        "same_current_yaw_authority_older_history",
        "same_current_steer_lag_older_history",
        "same_current_drive_brake_asymmetry_older_history",
        "same_current_rear_lateral_authority_older_history",
        "same_current_mixed_authority_older_history",
    ),
    "T3_active_diagnostic_warmup": (
        "warmup_brake_authority_probe",
        "warmup_yaw_authority_probe",
        "warmup_steering_lag_probe",
        "warmup_throttle_release_response",
        "warmup_combined_brake_steer_probe",
        "warmup_terminal_recovery_probe",
    ),
    "T4_variable_diagnostic_delay": (
        "short_delay_brake_evidence",
        "medium_delay_yaw_evidence",
        "long_delay_steer_lag_evidence",
        "variable_delay_mixed_authority",
        "stale_evidence_boundary_check",
        "delayed_obstacle_reveal_response",
    ),
    "T5_terminal_boundary_near_constraint": (
        "near_zero_clearance_margin",
        "late_terminal_boundary_margin",
        "tight_road_terminal_boundary",
        "low_grip_terminal_boundary",
        "actuator_delay_terminal_boundary",
        "mixed_dynamics_terminal_boundary",
    ),
}

WARMUP_MODES = ("none", "brake_tap", "steer_pulse", "throttle_release", "brake_plus_steer")
RECENT_WINDOWS_SECONDS = (0.25, 0.5, 1.0)
OLDER_HISTORY_OFFSETS_SECONDS = (1.5, 2.0, 3.0)
DIAGNOSTIC_DELAYS_SECONDS = (0.2, 0.5, 1.0, 1.5, 2.0)
TERMINAL_MARGIN_BUCKETS = ("near_zero_positive", "low_positive", "near_collision", "road_edge_limited")


def _split_for_index(index: int) -> str:
    if index < SPLIT_TARGETS["public_debug"]:
        return "public_debug"
    return "public_gate"


def _difficulty_values(local_index: int, *, family_offset: int) -> dict[str, str]:
    return {
        axis: values[(local_index + family_offset + axis_index) % len(values)]
        for axis_index, (axis, values) in enumerate(DIFFICULTY_AXES.items())
    }


def _clean_claim_flags() -> dict[str, bool]:
    return {
        "labels_enter_actor_input": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _family_specific_fields(family: str, local_index: int) -> dict[str, Any]:
    if family == "T1_reactive_active_safety":
        return {
            "same_current_constraint": False,
            "history_intervention_candidate": False,
            "warmup_mode": "none",
            "warmup_duration_seconds": 0.0,
            "obstacle_reveal_delay_seconds": 0.0,
            "recent_window_seconds": 0.0,
            "older_history_offset_seconds": 0.0,
            "diagnostic_delay_seconds": 0.0,
            "terminal_margin_bucket": "",
            "task_role_semantics": "reactive_evasive_driving_current_response_allowed",
        }
    if family == "T2_same_current_different_older_history":
        return {
            "same_current_constraint": True,
            "history_intervention_candidate": True,
            "warmup_mode": "none",
            "warmup_duration_seconds": 0.0,
            "obstacle_reveal_delay_seconds": 0.0,
            "recent_window_seconds": RECENT_WINDOWS_SECONDS[local_index % len(RECENT_WINDOWS_SECONDS)],
            "older_history_offset_seconds": OLDER_HISTORY_OFFSETS_SECONDS[
                (local_index // len(RECENT_WINDOWS_SECONDS)) % len(OLDER_HISTORY_OFFSETS_SECONDS)
            ],
            "diagnostic_delay_seconds": 0.0,
            "terminal_margin_bucket": "",
            "task_role_semantics": "same_current_same_recent_window_different_older_history",
        }
    if family == "T3_active_diagnostic_warmup":
        mode = WARMUP_MODES[(local_index % (len(WARMUP_MODES) - 1)) + 1]
        duration = (0.5, 1.0, 1.5, 2.0)[(local_index // 2) % 4]
        return {
            "same_current_constraint": False,
            "history_intervention_candidate": True,
            "warmup_mode": mode,
            "warmup_duration_seconds": duration,
            "obstacle_reveal_delay_seconds": (0.2, 0.5, 1.0)[local_index % 3],
            "recent_window_seconds": 0.0,
            "older_history_offset_seconds": 0.0,
            "diagnostic_delay_seconds": 0.0,
            "terminal_margin_bucket": "",
            "task_role_semantics": "active_diagnostic_warmup_before_obstacle_reveal",
        }
    if family == "T4_variable_diagnostic_delay":
        return {
            "same_current_constraint": False,
            "history_intervention_candidate": True,
            "warmup_mode": WARMUP_MODES[(local_index % (len(WARMUP_MODES) - 1)) + 1],
            "warmup_duration_seconds": (0.5, 1.0, 1.5)[local_index % 3],
            "obstacle_reveal_delay_seconds": DIAGNOSTIC_DELAYS_SECONDS[local_index % len(DIAGNOSTIC_DELAYS_SECONDS)],
            "recent_window_seconds": RECENT_WINDOWS_SECONDS[local_index % len(RECENT_WINDOWS_SECONDS)],
            "older_history_offset_seconds": OLDER_HISTORY_OFFSETS_SECONDS[local_index % len(OLDER_HISTORY_OFFSETS_SECONDS)],
            "diagnostic_delay_seconds": DIAGNOSTIC_DELAYS_SECONDS[local_index % len(DIAGNOSTIC_DELAYS_SECONDS)],
            "terminal_margin_bucket": "",
            "task_role_semantics": "variable_delay_between_response_evidence_and_decision",
        }
    if family == "T5_terminal_boundary_near_constraint":
        return {
            "same_current_constraint": False,
            "history_intervention_candidate": True,
            "warmup_mode": WARMUP_MODES[local_index % len(WARMUP_MODES)],
            "warmup_duration_seconds": (0.0, 0.5, 1.0, 1.5)[local_index % 4],
            "obstacle_reveal_delay_seconds": (0.0, 0.2, 0.5)[local_index % 3],
            "recent_window_seconds": RECENT_WINDOWS_SECONDS[local_index % len(RECENT_WINDOWS_SECONDS)],
            "older_history_offset_seconds": OLDER_HISTORY_OFFSETS_SECONDS[local_index % len(OLDER_HISTORY_OFFSETS_SECONDS)],
            "diagnostic_delay_seconds": DIAGNOSTIC_DELAYS_SECONDS[local_index % len(DIAGNOSTIC_DELAYS_SECONDS)],
            "terminal_margin_bucket": TERMINAL_MARGIN_BUCKETS[local_index % len(TERMINAL_MARGIN_BUCKETS)],
            "task_role_semantics": "terminal_boundary_near_constraint_avoidance",
        }
    raise ValueError(f"unknown task family {family}")


def build_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for family_index, (family, target_count) in enumerate(FAMILY_TARGETS.items()):
        source_kinds = FAMILY_SOURCE_KINDS[family]
        for local_index in range(target_count):
            global_index = len(candidates)
            source_kind = source_kinds[local_index % len(source_kinds)]
            difficulty = _difficulty_values(local_index, family_offset=family_index)
            candidate_id = f"osd_v0_{global_index:04d}_{family.split('_')[0].lower()}"
            candidates.append(
                {
                    "candidate_set_id": CANDIDATE_SET_ID,
                    "branch_id": BRANCH_ID,
                    "candidate_id": candidate_id,
                    "candidate_index": global_index,
                    "family_local_index": local_index,
                    "panel_task_family": family,
                    "family_target_count": target_count,
                    "source_split": _split_for_index(global_index),
                    "source_origin": "m2060_no_rollout_outcome_supported_decisive_generator",
                    "source_kind": source_kind,
                    "source_edge": "|".join(
                        [
                            family,
                            source_kind,
                            difficulty["obstacle_distance_band"],
                            difficulty["road_width_band"],
                            difficulty["curvature_band"],
                            difficulty["dynamics_band"],
                            difficulty["initial_speed_band"],
                        ]
                    ),
                    "window_tag": f"m2060_{family.split('_')[0].lower()}_{local_index:03d}",
                    "source_reference": candidate_id,
                    "materialization_semantics": "smoke_proxy",
                    "generated_source_row": True,
                    "paper_validity_claim": False,
                    "target_paper_validity_claim": False,
                    "candidate_semantics": "smoke_proxy_candidate_not_paper_validated",
                    "calibration_stage": "no_rollout_candidate_generation",
                    "calibration_before_full_comparison_required": True,
                    "private_holdout_candidate": False,
                    "tuning_target_profile": "none",
                    **difficulty,
                    **_family_specific_fields(family, local_index),
                    **_clean_claim_flags(),
                }
            )
    return candidates


def _axis_coverage(candidates: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    grouped: dict[str, dict[str, Counter[str]]] = {
        family: {axis: Counter() for axis in DIFFICULTY_AXES} for family in FAMILY_TARGETS
    }
    for candidate in candidates:
        family = str(candidate["panel_task_family"])
        for axis in DIFFICULTY_AXES:
            grouped[family][axis][str(candidate[axis])] += 1
    return {
        family: {axis: dict(sorted(counter.items())) for axis, counter in axis_counts.items()}
        for family, axis_counts in grouped.items()
    }


def _axis_coverage_pass(axis_coverage: Mapping[str, Mapping[str, Mapping[str, int]]]) -> bool:
    for family_counts in axis_coverage.values():
        for axis, expected_values in DIFFICULTY_AXES.items():
            if set(family_counts.get(axis, {})) != set(expected_values):
                return False
    return True


def _source_diversity(candidates: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[Mapping[str, Any]]] = {family: [] for family in FAMILY_TARGETS}
    for candidate in candidates:
        by_family[str(candidate["panel_task_family"])].append(candidate)
    summary: dict[str, dict[str, Any]] = {}
    for family, rows in by_family.items():
        source_kind_counts = Counter(str(row["source_kind"]) for row in rows)
        max_share = max(source_kind_counts.values(), default=0) / max(1, len(rows))
        summary[family] = {
            "source_kind_count": len(source_kind_counts),
            "max_single_source_kind_share": max_share,
            "source_kind_counts": dict(sorted(source_kind_counts.items())),
        }
    return summary


def summarize_candidates(*, candidates: list[dict[str, Any]], next_blocker: str = DEFAULT_NEXT_BLOCKER) -> dict[str, Any]:
    family_counts = {family: 0 for family in FAMILY_TARGETS}
    for family, count in Counter(str(row["panel_task_family"]) for row in candidates).items():
        family_counts[family] = count
    split_counts = {split: 0 for split in SPLIT_TARGETS}
    for split, count in Counter(str(row["source_split"]) for row in candidates).items():
        split_counts[split] = count
    forbidden_true_counts = {
        field: sum(1 for row in candidates if bool(row.get(field, False))) for field in FORBIDDEN_BOOL_FIELDS
    }
    paper_validity_claim_true_count = sum(1 for row in candidates if bool(row.get("paper_validity_claim", False)))
    actor_input_forbidden_keys_present = sorted(
        set(ALLOWED_ACTOR_INPUT_FIELDS).intersection(FORBIDDEN_ACTOR_INPUT_FIELDS)
    )
    axis_coverage = _axis_coverage(candidates)
    axis_pass = _axis_coverage_pass(axis_coverage)
    quota_pass = (
        len(candidates) == sum(FAMILY_TARGETS.values())
        and family_counts == FAMILY_TARGETS
        and split_counts == SPLIT_TARGETS
    )
    guardrail_violation_count = (
        sum(forbidden_true_counts.values())
        + paper_validity_claim_true_count
        + len(actor_input_forbidden_keys_present)
    )
    result_passes = quota_pass and axis_pass and guardrail_violation_count == 0
    return {
        "result_class": (
            "outcome_supported_decisive_task_candidate_generation_pass"
            if result_passes
            else "outcome_supported_decisive_task_candidate_generation_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "branch_id": BRANCH_ID,
        "candidate_set_id": CANDIDATE_SET_ID,
        "claim_scope": "no-rollout candidate generation only",
        "candidate_count": len(candidates),
        "expected_candidate_count": sum(FAMILY_TARGETS.values()),
        "family_counts": family_counts,
        "expected_family_counts": FAMILY_TARGETS,
        "source_split_counts": split_counts,
        "expected_source_split_counts": SPLIT_TARGETS,
        "quota_pass": quota_pass,
        "difficulty_axis_coverage": axis_coverage,
        "difficulty_axis_coverage_pass": axis_pass,
        "source_diversity": _source_diversity(candidates),
        "allowed_actor_input_fields": list(ALLOWED_ACTOR_INPUT_FIELDS),
        "forbidden_actor_input_fields": list(FORBIDDEN_ACTOR_INPUT_FIELDS),
        "actor_input_forbidden_keys_present": actor_input_forbidden_keys_present,
        "actor_input_forbidden_key_count": len(actor_input_forbidden_keys_present),
        "forbidden_true_counts": forbidden_true_counts,
        "paper_validity_claim_true_count": paper_validity_claim_true_count,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning_count": forbidden_true_counts["profile_specific_tuning"],
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "sentinel_profiles_for_future_smoke": list(SENTINEL_PROFILES),
        "full_profile_matrix_after_support_gate": list(FULL_PROFILE_MATRIX),
        "outcome_support_smoke_gates": {
            "global_success_rate_min": 0.08,
            "global_success_rate_max": 0.60,
            "global_offtrack_rate_max": 0.80,
            "global_collision_rate_max": 0.25,
            "family_success_count_min": 6,
            "family_success_source_count_min": 3,
            "family_profiles_with_success_min": 2,
            "max_single_source_share_of_successes": 0.25,
        },
        "private_holdout_policy": "defer until reset materialization and outcome-support smoke are stable",
        "next_blocker": next_blocker,
        "candidates": candidates,
    }


def generate_outcome_supported_decisive_task_candidates(
    *,
    output_path: Path | str = DEFAULT_OUTPUT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    payload = summarize_candidates(candidates=build_candidates(), next_blocker=next_blocker)
    write_json(output_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    payload = generate_outcome_supported_decisive_task_candidates(
        output_path=args.output,
        next_blocker=str(args.next_blocker),
    )
    print(f"output={args.output}")
    print(f"result_class={payload['result_class']}")
    print(f"candidate_count={payload['candidate_count']}")
    print(f"quota_pass={payload['quota_pass']}")
    print(f"difficulty_axis_coverage_pass={payload['difficulty_axis_coverage_pass']}")
    print(f"guardrail_violation_count={payload['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
