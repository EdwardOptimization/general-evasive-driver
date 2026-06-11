"""Shared schema constants for the AutoDrift research harness."""

from __future__ import annotations


PROCESS_V2_ENFORCE_FROM_PRIORITY = 2220
PROCESS_V3_SYNTHESIS_ENFORCE_FROM_PRIORITY = 6850
PROCESS_V4_TRAINING_STAGE_ENFORCE_FROM_PRIORITY = 10820
PROCESS_V5_SELF_ID_DISCIPLINE_ENFORCE_FROM_PRIORITY = 10850
PROCESS_V6_LOCAL_SEARCH_GUARD_ENFORCE_FROM_PRIORITY = 18910

SCOREBOARD_FIELDS = [
    "milestone",
    "type",
    "checkpoint",
    "success_rate",
    "termination_rate",
    "clearance_margin_mean",
    "reset_success",
    "zero_wheel_success",
    "zero_all_success",
    "wheel_gain_mu",
    "decision",
    "reason",
]

PROCESS_V2_GATE_TIERS = {
    "proof",
    "generalization",
    "promotion",
    "process",
    "infrastructure",
}

PROCESS_V2_FAILURE_TYPES = {
    "proof_washout",
    "objective_overfit",
    "behavior_regression",
    "seed_fragility",
    "lineage_invalid",
    "contract_violation",
    "metric_artifact",
    "training_instability",
    "scenario_sampling_failure",
    "protected_key_window_failure",
    "promotion_gate_failure",
    "private_holdout_contamination",
    "none",
}

PROCESS_V2_PROMOTION_DECISIONS = {
    "pending",
    "promote",
    "reject",
    "repair",
    "archive",
    "not_applicable",
}

PROCESS_V2_PRIVATE_HOLDOUT_POLICIES = {
    "not_used",
    "promotion_only",
    "rotate_after_repair",
}

PROCESS_V2_LINEAGE_FIELDS = [
    "parent_checkpoint",
    "parent_dataset",
    "parent_config",
    "parent_objective",
    "derived_from",
    "blocked_by",
    "supersedes",
    "invalidates",
]

PROCESS_V3_SYNTHESIS_FIELDS = [
    "branch",
    "evidence_axis",
    "evidence_increment",
    "claim_scope",
    "stop_condition",
    "fallback_plan",
    "synthesis_cadence",
    "synthesis_trigger",
    "synthesis_decision",
]

PROCESS_V3_SYNTHESIS_DECISIONS = {
    "not_applicable",
    "continue",
    "pivot",
    "stop",
    "promote_to_next_branch",
}

PROCESS_V3_SYNTHESIS_QUESTIONS = [
    "evidence_summary",
    "supported_claims",
    "falsified_claims",
    "failure_taxonomy_summary",
    "public_gate_overfit_risk",
    "next_branch_decision",
]

PROCESS_V4_TRAINING_STAGE_FIELDS = [
    "stage",
    "stage_objective",
    "admission_evidence",
    "blocked_shortcuts",
    "allowed_updates",
    "next_stage_criteria",
]

PROCESS_V4_TRAINING_STAGES = {
    "process",
    "infrastructure",
    "evaluation_only",
    "behavior_pretrain",
    "capability_pretrain",
    "action_grounding_posttrain",
    "guarded_rl",
}

PROCESS_V5_SELF_ID_DISCIPLINE_FIELDS = [
    "claim_level",
    "current_frame_substitution_risk",
    "history_necessity_tests",
    "temporal_evidence_window",
    "negative_result_policy",
    "allowed_claims",
]

PROCESS_V5_SELF_ID_CLAIM_LEVELS = {
    "not_applicable",
    "level0_no_adaptation",
    "level1_closed_loop_reactive",
    "level2_history_encoded_reactive",
    "level3_anticipatory_self_identification",
}

PROCESS_V6_LOCAL_SEARCH_GUARD_FIELDS = [
    "actual_progress_type",
    "process_overhead",
    "local_search_risk",
    "same_failure_repeat_count",
    "same_public_gate_repair_count",
    "evidence_expansion",
    "paper_verdict_delta",
    "must_synthesize_if",
]

PROCESS_V6_ACTUAL_PROGRESS_TYPES = {
    "new_closed_loop_data",
    "new_dataset_or_panel",
    "new_tool_or_infra",
    "new_scenario_distribution",
    "new_baseline_comparison",
    "result_audit",
    "evidence_reanalysis",
    "synthesis_decision",
    "design_only",
    "repair_only",
}

PROCESS_V6_LOCAL_SEARCH_RISK_LEVELS = {
    "low",
    "medium",
    "high",
}

PROCESS_V6_EVIDENCE_PROGRESS_TYPES = {
    "new_closed_loop_data",
    "new_dataset_or_panel",
    "new_scenario_distribution",
    "new_baseline_comparison",
}

PROCESS_V6_DEFAULT_NON_EVIDENCE_STREAK_LIMIT = 5

# Process v7 (WP6.2 guardrails): feasibility-oracle-first pricing gate and
# blocked-dependency escalation protocol. Enforced only for priority >= 32200
# (M3220+); the 3138 historical enforced tasks are unaffected by design.
PROCESS_V7_FEASIBILITY_PRICING_ENFORCE_FROM_PRIORITY = 32200

PROCESS_V7_FEASIBILITY_PRICING_FIELDS = [
    "pricing_artifact",
    "priced_gap",
    "threshold",
    "gap_meets_threshold",
]

# Explicit declaration (new optional manifest field `milestone_intent`).
# When present it overrides evidence-axis inference.
PROCESS_V7_PRICED_INTENTS = {
    "repair",
    "improvement",
    "training",
}

# Inference fallback: workflow_synthesis.evidence_axis substrings that mark a
# repair/improvement/training milestone (feasibility pricing required).
PROCESS_V7_PRICED_EVIDENCE_AXIS_TOKENS = (
    "repair",
    "improv",
    "train",
    "retun",
    "tuning",
)

# Certified dead ends (auto-reject without a NEW pricing artifact):
# the 7 residual hard-safety rows certified unrepairable by the oracle
# certification (43,372 privileged rollouts, 7/7 hard-fail in both tiers).
PROCESS_V7_CERTIFIED_DEAD_END_RESIDUAL_SEEDS = (
    "401530",
    "401541",
    "401560",
    "401631",
    "401640",
    "401641",
    "401660",
)

PROCESS_V7_DEAD_END_CERTIFICATION_ARTIFACTS = (
    "experiments/feasibility_audit/oracle_certification_results.json",
    "experiments/feasibility_audit/c5_reflex_degradation.json",
)

PROCESS_V7_REPAIR_LIKE_TOKENS = (
    "repair",
    "fix",
    "rescue",
    "recover",
    "retrain",
    "retune",
    "retuning",
    "re-tune",
    "tune",
    "tuning",
)

# Process v7b: dependency-unavailable semantics in completed-task notes or
# hypotheses. Two or more consecutive completed milestones on the same
# workflow_synthesis.branch matching these tokens require an escalation file
# under docs/escalations/ (escalate instead of bookkeeping).
PROCESS_V7B_DEPENDENCY_UNAVAILABLE_TOKENS = (
    "dependency-unavailable",
    "dependency unavailable",
    "unavailable dependency",
    "blocked dependency",
    "blocked-dependency",
    "blocked on dependency",
    "blocked on external",
    "missing dependency",
    "dependency missing",
    "dependency is missing",
    "dependency not available",
    "upstream unavailable",
    "waiting on dependency",
    "waiting for dependency",
    "external dependency unavailable",
)

PROCESS_V7B_ESCALATION_DIR = "docs/escalations"
PROCESS_V7B_DEPENDENCY_STREAK_LIMIT = 2
