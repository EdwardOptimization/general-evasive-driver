"""Shared schema constants for the AutoDrift research harness."""

from __future__ import annotations


PROCESS_V2_ENFORCE_FROM_PRIORITY = 2220
PROCESS_V3_SYNTHESIS_ENFORCE_FROM_PRIORITY = 6850
PROCESS_V4_TRAINING_STAGE_ENFORCE_FROM_PRIORITY = 10820

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
