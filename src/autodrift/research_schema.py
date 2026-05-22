"""Shared schema constants for the AutoDrift research harness."""

from __future__ import annotations


PROCESS_V2_ENFORCE_FROM_PRIORITY = 2220

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
