"""No-rollout candidate generation for comparison-support scenario redesign."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_json


BRANCH_ID = "paper_route_outcome_supported_decisive_comparison_support_scenario_redesign"
CANDIDATE_SET_ID = "paper_route_outcome_supported_decisive_comparison_support_candidates_v0"
DEFAULT_OUTPUT = Path("configs/paper_route_outcome_supported_decisive_comparison_support_candidates_v0.json")
DEFAULT_NEXT_BLOCKER = "m2116-paper-route-outcome-supported-decisive-comparison-support-candidate-generation-result-audit"

INTENT_TARGETS = {
    "support_ladder_easy": 60,
    "support_ladder_medium": 60,
    "discriminative_boundary": 60,
    "collision_relief_probe": 60,
}
SOURCE_FAMILIES = (
    "T1_reactive_active_safety",
    "T3_active_diagnostic_warmup",
    "T4_variable_diagnostic_delay",
    "T5_terminal_boundary_near_constraint",
)
SOURCE_KINDS_BY_INTENT = {
    "support_ladder_easy": (
        "wide_corridor_stable_evasion",
        "early_obstacle_stable_evasion",
        "nominal_mu_multi_profile_support",
        "gentle_yaw_authority_probe",
        "moderate_speed_clearance_support",
        "low_collision_baseline_support",
    ),
    "support_ladder_medium": (
        "medium_timing_stable_evasion",
        "moderate_low_mu_support",
        "nominal_delay_support_boundary",
        "medium_corridor_yaw_support",
        "recoverable_terminal_margin",
        "profile_diversity_support",
    ),
    "discriminative_boundary": (
        "window_length_discriminative_boundary",
        "gru_memory_discriminative_boundary",
        "current_response_discriminative_boundary",
        "reset_hidden_discriminative_boundary",
        "actuator_delay_discriminative_boundary",
        "mixed_authority_discriminative_boundary",
    ),
    "collision_relief_probe": (
        "late_boundary_collision_relief",
        "low_grip_collision_relief",
        "tight_road_collision_relief",
        "actuator_delay_collision_relief",
        "near_zero_margin_collision_relief",
        "mixed_dynamics_collision_relief",
    ),
}
TARGET_SUPPORT_TIER_BY_INTENT = {
    "support_ladder_easy": "multi_profile_easy_support",
    "support_ladder_medium": "multi_profile_medium_support",
    "discriminative_boundary": "comparison_boundary_support",
    "collision_relief_probe": "collision_dominance_relief_support",
}
DIFFICULTY_VALUES = {
    "support_ladder_easy": {
        "obstacle_timing_band": ("early", "early", "medium"),
        "road_width_band": ("generous", "generous", "nominal"),
        "dynamics_band": ("nominal_mu", "nominal_mu", "mixed_mu"),
        "initial_speed_band": ("low", "nominal", "nominal"),
    },
    "support_ladder_medium": {
        "obstacle_timing_band": ("early", "medium", "medium"),
        "road_width_band": ("generous", "nominal", "nominal"),
        "dynamics_band": ("nominal_mu", "mixed_mu", "low_mu", "actuator_delay"),
        "initial_speed_band": ("nominal", "nominal", "high"),
    },
    "discriminative_boundary": {
        "obstacle_timing_band": ("medium", "medium", "late"),
        "road_width_band": ("nominal", "tight"),
        "dynamics_band": ("low_mu", "mixed_mu", "actuator_delay"),
        "initial_speed_band": ("nominal", "high"),
    },
    "collision_relief_probe": {
        "obstacle_timing_band": ("early", "medium"),
        "road_width_band": ("generous", "nominal"),
        "dynamics_band": ("low_mu", "mixed_mu", "actuator_delay"),
        "initial_speed_band": ("nominal", "high"),
    },
}
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


def _pick(values: tuple[str, ...], index: int) -> str:
    return values[index % len(values)]


def _difficulty(intent: str, local_index: int) -> dict[str, str]:
    values = DIFFICULTY_VALUES[intent]
    return {key: _pick(tuple(options), local_index + axis_index) for axis_index, (key, options) in enumerate(values.items())}


def _claim_flags() -> dict[str, bool]:
    return {
        "paper_validity_claim": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _candidate(*, global_index: int, intent: str, local_index: int) -> dict[str, Any]:
    difficulty = _difficulty(intent, local_index)
    source_kind = _pick(SOURCE_KINDS_BY_INTENT[intent], local_index)
    source_family = _pick(SOURCE_FAMILIES, local_index + len(intent))
    candidate = {
        "candidate_id": f"cs_v0_{global_index:04d}",
        "candidate_set_id": CANDIDATE_SET_ID,
        "scenario_redesign_branch": BRANCH_ID,
        "comparison_support_intent": intent,
        "target_support_tier": TARGET_SUPPORT_TIER_BY_INTENT[intent],
        "source_family": source_family,
        "source_kind": source_kind,
        "difficulty_axis": (
            f"{difficulty['obstacle_timing_band']}|{difficulty['road_width_band']}|"
            f"{difficulty['dynamics_band']}|{difficulty['initial_speed_band']}"
        ),
        "dynamics_band": difficulty["dynamics_band"],
        "obstacle_timing_band": difficulty["obstacle_timing_band"],
        "road_width_band": difficulty["road_width_band"],
        "initial_speed_band": difficulty["initial_speed_band"],
        "generated_source_row": True,
        "materialization_semantics": "comparison_support_smoke_proxy",
        "actor_input_contract": "human_view_no_privileged_inputs",
        "actor_input_fields": [
            "ego_kinematics",
            "imu_like_response",
            "actuator_state",
            "previous_physical_commands",
            "ego_frame_road_and_obstacle_geometry",
            "finite_window_or_recurrent_command_response_history",
        ],
        "forbidden_actor_input_fields": [],
        "comparison_ready_goal": {
            "min_episode_count": 24,
            "min_success_count": 6,
            "min_success_profile_count": 3,
            "min_success_source_count": 3,
            "max_collision_rate": 0.30,
            "max_offtrack_outcome_rate": 0.70,
        },
    }
    candidate.update(_claim_flags())
    return candidate


def build_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    global_index = 0
    for intent, count in INTENT_TARGETS.items():
        for local_index in range(count):
            candidates.append(_candidate(global_index=global_index, intent=intent, local_index=local_index))
            global_index += 1
    return candidates


def _count_true(candidates: Iterable[Mapping[str, Any]], field: str) -> int:
    return sum(1 for row in candidates if bool(row.get(field, False)))


def _forbidden_actor_input_count(candidates: Iterable[Mapping[str, Any]]) -> int:
    forbidden = set(FORBIDDEN_ACTOR_INPUT_FIELDS)
    count = 0
    for row in candidates:
        actor_fields = {str(value) for value in row.get("actor_input_fields", [])}
        declared_forbidden = {str(value) for value in row.get("forbidden_actor_input_fields", [])}
        if actor_fields & forbidden or declared_forbidden:
            count += 1
    return count


def summarize_candidates(*, candidates: list[dict[str, Any]], next_blocker: str = DEFAULT_NEXT_BLOCKER) -> dict[str, Any]:
    intent_counts = dict(sorted(Counter(str(row["comparison_support_intent"]) for row in candidates).items()))
    candidate_ids = [str(row["candidate_id"]) for row in candidates]
    duplicate_candidate_id_count = len(candidate_ids) - len(set(candidate_ids))
    paper_validity_claim_true_count = _count_true(candidates, "paper_validity_claim")
    profile_specific_tuning_true_count = _count_true(candidates, "profile_specific_tuning")
    actor_input_forbidden_key_count = _forbidden_actor_input_count(candidates)
    quota_pass = intent_counts == INTENT_TARGETS and len(candidates) == sum(INTENT_TARGETS.values())
    guardrail_flags = {
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
        "profile_specific_tuning": profile_specific_tuning_true_count > 0,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if value)
    result_passes = (
        quota_pass
        and duplicate_candidate_id_count == 0
        and paper_validity_claim_true_count == 0
        and profile_specific_tuning_true_count == 0
        and actor_input_forbidden_key_count == 0
        and guardrail_violation_count == 0
    )
    return {
        "result_class": (
            "comparison_support_candidate_generation_pass"
            if result_passes
            else "comparison_support_candidate_generation_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "protocol": CANDIDATE_SET_ID,
        "branch_id": BRANCH_ID,
        "candidate_count": len(candidates),
        "target_candidate_count": sum(INTENT_TARGETS.values()),
        "intent_counts": intent_counts,
        "target_intent_counts": INTENT_TARGETS,
        "quota_pass": quota_pass,
        "duplicate_candidate_id_count": duplicate_candidate_id_count,
        "paper_validity_claim_true_count": paper_validity_claim_true_count,
        "profile_specific_tuning_true_count": profile_specific_tuning_true_count,
        "actor_input_forbidden_key_count": actor_input_forbidden_key_count,
        "guardrail_flags": guardrail_flags,
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
        "profile_specific_tuning": profile_specific_tuning_true_count > 0,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "candidates": candidates,
        "next_blocker": str(next_blocker),
    }


def generate_comparison_support_candidates(
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
    payload = generate_comparison_support_candidates(output_path=args.output, next_blocker=str(args.next_blocker))
    print(f"output={args.output}")
    print(f"result_class={payload['result_class']}")
    print(f"candidate_count={payload['candidate_count']}")
    print(f"intent_counts={payload['intent_counts']}")
    print(f"guardrail_violation_count={payload['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
