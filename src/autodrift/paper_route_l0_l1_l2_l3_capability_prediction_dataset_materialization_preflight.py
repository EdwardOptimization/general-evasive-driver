"""Materialize a Route B capability-prediction dataset contract.

M2887 converts the accepted M2884/M2885 panel inventory into actor-safe
dataset-contract rows. It is read-only with respect to simulation and policy
execution: no reset, step, rollout, validation, training, ranking, or promotion
is performed.
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


DEFAULT_MILESTONE = "m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit"
DEFAULT_OUTPUT_DIR = Path("runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight")
DEFAULT_M2884_DIR = Path("runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight")
DEFAULT_M1690_WORKLOAD = Path(
    "runs/m1690_controller_family_executable_workload_materialization_preflight/executable_workload_matrix.csv"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit.json"
)

CLAIM_SCOPE = (
    "M2887 read-only capability-prediction dataset materialization only. It reads "
    "M2884/M2885/M2886 and M1690 artifacts and writes dataset contract rows. It "
    "does not reset, step, rollout, replay, validate, train, run PPO, rank "
    "controllers, select a winner, promote a checkpoint, publish a package, or "
    "claim driver performance, paper evidence, finite-window-vs-GRU evidence, "
    "current-sim verdict, high-fidelity validation, full-driver completion, or "
    "level3 self-ID."
)
FORBIDDEN_INTERPRETATION = (
    "driver performance, controller-family ranking, profile ranking, checkpoint "
    "promotion, finite-window-vs-GRU verdict, paper result, current-sim verdict, "
    "validation readiness/result, high-fidelity validation, full-driver "
    "completion, or level3 self-identification"
)
ACTOR_FEATURE_SCHEMA = (
    "deployable history/current-response features only: ego kinematics, IMU-like "
    "response, actuator state, previous physical commands, ego-frame geometry, "
    "and recurrent state"
)
EVALUATOR_TARGET_SCOPE = "future-capability labels or availability flags are evaluator-only and actor-invisible"

FALSE_CLAIM_FLAGS = {
    "dependency_mutation_performed": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "validation_run": False,
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

USABLE_TASK_FIELDNAMES = [
    "materialized_task_id",
    "candidate_id",
    "task_source_id",
    "task_family",
    "source_edge",
    "window_tag",
    "executable_source_family",
    "env_template_family",
    "diagnostic_artifact_tags",
    "candidate_artifact_count",
    "guard_artifact_count",
    "paired_delta_count",
    "source_family_tag_count",
    "profile_count",
    "required_profile_count",
    "dataset_role",
    "actor_feature_schema",
    "evaluator_target_scope",
    "actor_visible_target_fields",
    "hidden_oracle_actor_input_required",
    "admitted_for_m2887_materialization",
    "paper_proof_allowed",
    "ordinary_success_denominator_allowed",
    "claim_boundary",
    "forbidden_interpretation",
]
PROFILE_TASK_FIELDNAMES = [
    "profile_task_id",
    "materialized_task_id",
    "candidate_id",
    "task_source_id",
    "profile_name",
    "profile_level",
    "profile_config_path",
    "checkpoint_path",
    "config_exists",
    "checkpoint_exists",
    "environment_rollout_scheduled",
    "training_scheduled",
    "profile_specific_tuning",
    "actor_feature_schema",
    "evaluator_target_scope",
    "actor_visible_target_fields",
    "status_pass",
    "claim_boundary",
]
EVALUATOR_TARGET_FIELDNAMES = [
    "dataset_target_id",
    "source_target_id",
    "target_family",
    "required_columns",
    "available_columns",
    "status_pass",
    "actor_visible_allowed",
    "target_visibility",
    "dataset_usage",
    "claim_boundary",
]
EXCLUSION_FIELDNAMES = [
    "excluded_row_id",
    "candidate_id",
    "task_source_id",
    "classification",
    "classification_reason",
    "task_family",
    "source_edge",
    "env_template_family",
    "diagnostic_artifact_tags",
    "candidate_artifact_count",
    "guard_artifact_count",
    "source_family_tag_count",
    "exclusion_reason",
    "paper_proof_allowed",
    "ordinary_success_denominator_allowed",
    "may_seed_future_panel",
    "claim_boundary",
]
ACTOR_FIELDNAMES = [
    "contract_row_id",
    "source_guard_id",
    "contract_field",
    "observed",
    "expected",
    "status_pass",
    "actor_visible_allowed",
    "dataset_actor_feature_allowed",
    "future_target_actor_visible",
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


def _required_workload_by_task(workload_rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    by_task: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in workload_rows:
        task_source_id = row.get("task_source_id", "")
        profile_name = row.get("profile_name", "")
        if task_source_id and profile_name:
            by_task[task_source_id][profile_name] = row
    return by_task


def build_usable_task_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    usable_rows = [row for row in candidate_rows if row.get("classification") == "usable"]
    for index, row in enumerate(usable_rows, start=1):
        rows.append(
            {
                "materialized_task_id": f"m2887-usable-task-{index:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "executable_source_family": row.get("executable_source_family", ""),
                "env_template_family": row.get("env_template_family", ""),
                "diagnostic_artifact_tags": row.get("diagnostic_artifact_tags", ""),
                "candidate_artifact_count": row.get("candidate_artifact_count", ""),
                "guard_artifact_count": row.get("guard_artifact_count", ""),
                "paired_delta_count": row.get("paired_delta_count", ""),
                "source_family_tag_count": row.get("source_family_tag_count", ""),
                "profile_count": row.get("profile_count", ""),
                "required_profile_count": row.get("required_profile_count", ""),
                "dataset_role": "accepted_usable_capability_prediction_task",
                "actor_feature_schema": ACTOR_FEATURE_SCHEMA,
                "evaluator_target_scope": EVALUATOR_TARGET_SCOPE,
                "actor_visible_target_fields": "",
                "hidden_oracle_actor_input_required": False,
                "admitted_for_m2887_materialization": True,
                "paper_proof_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "claim_boundary": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_profile_task_rows(
    *, usable_task_rows: list[dict[str, Any]], workload_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    workload_by_task = _required_workload_by_task(workload_rows)
    profile_rows: list[dict[str, Any]] = []
    for task in usable_task_rows:
        task_source_id = str(task["task_source_id"])
        profile_map = workload_by_task.get(task_source_id, {})
        for profile_index, profile_name in enumerate(REQUIRED_PROFILES, start=1):
            workload = profile_map.get(profile_name, {})
            status_pass = bool(workload) and _bool(workload.get("config_exists")) and _bool(workload.get("checkpoint_exists"))
            profile_rows.append(
                {
                    "profile_task_id": f"{task['materialized_task_id']}::profile-{profile_index:02d}",
                    "materialized_task_id": task["materialized_task_id"],
                    "candidate_id": task["candidate_id"],
                    "task_source_id": task_source_id,
                    "profile_name": profile_name,
                    "profile_level": _profile_level(profile_name),
                    "profile_config_path": workload.get("profile_config_path", ""),
                    "checkpoint_path": workload.get("checkpoint_path", ""),
                    "config_exists": workload.get("config_exists", False),
                    "checkpoint_exists": workload.get("checkpoint_exists", False),
                    "environment_rollout_scheduled": workload.get("environment_rollout_scheduled", False),
                    "training_scheduled": workload.get("training_scheduled", False),
                    "profile_specific_tuning": workload.get("profile_specific_tuning", False),
                    "actor_feature_schema": ACTOR_FEATURE_SCHEMA,
                    "evaluator_target_scope": EVALUATOR_TARGET_SCOPE,
                    "actor_visible_target_fields": "",
                    "status_pass": status_pass,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
    return profile_rows


def build_evaluator_target_rows(target_inventory_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(target_inventory_rows, start=1):
        rows.append(
            {
                "dataset_target_id": f"m2887-evaluator-target-{index:04d}",
                "source_target_id": row.get("target_id", ""),
                "target_family": row.get("target_family", ""),
                "required_columns": row.get("required_columns", ""),
                "available_columns": row.get("available_columns", ""),
                "status_pass": _bool(row.get("status_pass")),
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "target_visibility": "evaluator_only_actor_invisible",
                "dataset_usage": "target_value_or_availability_label_only",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_exclusion_rows(candidate_rows: list[dict[str, str]], classification: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_singleton = classification == "source-singleton"
    for index, row in enumerate((r for r in candidate_rows if r.get("classification") == classification), start=1):
        rows.append(
            {
                "excluded_row_id": f"m2887-excluded-{classification}-{index:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "task_source_id": row.get("task_source_id", ""),
                "classification": row.get("classification", ""),
                "classification_reason": row.get("classification_reason", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "env_template_family": row.get("env_template_family", ""),
                "diagnostic_artifact_tags": row.get("diagnostic_artifact_tags", ""),
                "candidate_artifact_count": row.get("candidate_artifact_count", ""),
                "guard_artifact_count": row.get("guard_artifact_count", ""),
                "source_family_tag_count": row.get("source_family_tag_count", ""),
                "exclusion_reason": "source_singleton_not_paper_proof"
                if source_singleton
                else "guard_only_not_dataset_proof",
                "paper_proof_allowed": False,
                "ordinary_success_denominator_allowed": False,
                "may_seed_future_panel": source_singleton,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_feature_contract_rows(actor_contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(actor_contract_rows, start=1):
        rows.append(
            {
                "contract_row_id": f"m2887-actor-contract-{index:04d}",
                "source_guard_id": row.get("guard_id", ""),
                "contract_field": row.get("guard_family", ""),
                "observed": row.get("observed", ""),
                "expected": row.get("expected", ""),
                "status_pass": _bool(row.get("status_pass")),
                "actor_visible_allowed": _bool(row.get("actor_visible_allowed")),
                "dataset_actor_feature_allowed": row.get("guard_family") in {"p0_observation_dim", "action_dim"},
                "future_target_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_claim_rows() -> list[dict[str, Any]]:
    allowed_specs = [
        ("dataset_materialized", "dataset materialization completeness", "M2887 summary and row artifacts"),
        ("exclusions_preserved", "source-singleton and guard exclusions preserved", "explicit exclusion row artifacts"),
        ("actor_contract_preserved", "actor feature contract preserved", "actor-feature contract rows"),
        ("bounded_audit_handoff", "bounded result-audit handoff", "M2888 manifest"),
    ]
    blocked_specs = [
        ("driver_performance", "driver performance", "closed-loop validation and promotion evidence"),
        ("controller_ranking", "controller-family ranking", "fair prediction or closed-loop comparison protocol"),
        ("finite_window_vs_gru", "finite-window-vs-GRU verdict", "separate fair L0/L1/L2/L3 comparison"),
        ("paper", "paper result", "paper-route audit and holdout evidence"),
        ("current_sim_verdict", "current-sim verdict", "current-sim benchmark pack and audit"),
        ("high_fidelity_validation", "high-fidelity validation", "HF source/build/reset/rollout gates"),
        ("full_driver", "full ideal driver completion", "full ideal driver gate"),
        ("level3_self_id", "level3 self-ID", "source-diverse intervention and history-necessity evidence"),
    ]
    rows = [
        {
            "claim_id": f"m2887-claim-{claim_id}",
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
            "claim_id": f"m2887-claim-{claim_id}",
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
    m2884_summary_exists: bool,
    m2884_summary_status_pass: bool,
    candidate_rows: list[dict[str, str]],
    usable_task_rows: list[dict[str, Any]],
    profile_task_rows: list[dict[str, Any]],
    evaluator_target_rows: list[dict[str, Any]],
    source_singleton_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    expected_usable_count: int,
    expected_profile_task_count: int,
    expected_source_singleton_count: int,
    expected_guard_count: int,
) -> list[dict[str, Any]]:
    target_gate_pass = bool(evaluator_target_rows) and all(
        _bool(row["status_pass"]) and not _bool(row["actor_visible_allowed"]) for row in evaluator_target_rows
    )
    actor_gate_pass = bool(actor_rows) and all(_bool(row["status_pass"]) and not _bool(row["future_target_actor_visible"]) for row in actor_rows)
    profile_gate_pass = len(profile_task_rows) == expected_profile_task_count and all(
        _bool(row["status_pass"]) and not _bool(row["environment_rollout_scheduled"]) and not _bool(row["training_scheduled"])
        for row in profile_task_rows
    )
    blocked_claim_gate_pass = all(
        _bool(row["claim_allowed"]) or not _bool(row["claim_made"]) for row in claim_rows
    )
    return [
        {
            "gate_id": "m2887-m2884-summary-accepted",
            "gate_family": "lineage",
            "status_pass": m2884_summary_exists and m2884_summary_status_pass,
            "observed": f"exists={m2884_summary_exists};status_pass={m2884_summary_status_pass}",
            "expected": "exists=True;status_pass=True",
            "failure_type": "lineage_invalid" if not (m2884_summary_exists and m2884_summary_status_pass) else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-candidate-inventory-read",
            "gate_family": "artifact_completeness",
            "status_pass": bool(candidate_rows),
            "observed": len(candidate_rows),
            "expected": ">0",
            "failure_type": "metric_artifact" if not candidate_rows else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-usable-task-row-count",
            "gate_family": "dataset_contract",
            "status_pass": len(usable_task_rows) == expected_usable_count,
            "observed": len(usable_task_rows),
            "expected": expected_usable_count,
            "failure_type": "scenario_sampling_failure" if len(usable_task_rows) != expected_usable_count else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-profile-task-row-count",
            "gate_family": "dataset_contract",
            "status_pass": profile_gate_pass,
            "observed": len(profile_task_rows),
            "expected": expected_profile_task_count,
            "failure_type": "metric_artifact" if not profile_gate_pass else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-source-singleton-exclusions-preserved",
            "gate_family": "proof_boundary",
            "status_pass": len(source_singleton_rows) == expected_source_singleton_count
            and all(not _bool(row["paper_proof_allowed"]) for row in source_singleton_rows),
            "observed": len(source_singleton_rows),
            "expected": expected_source_singleton_count,
            "failure_type": "proof_washout" if len(source_singleton_rows) != expected_source_singleton_count else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-guard-exclusions-preserved",
            "gate_family": "proof_boundary",
            "status_pass": len(guard_rows) == expected_guard_count
            and all(not _bool(row["ordinary_success_denominator_allowed"]) for row in guard_rows),
            "observed": len(guard_rows),
            "expected": expected_guard_count,
            "failure_type": "proof_washout" if len(guard_rows) != expected_guard_count else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-evaluator-targets-actor-invisible",
            "gate_family": "target_boundary",
            "status_pass": target_gate_pass,
            "observed": sum(not _bool(row["actor_visible_allowed"]) for row in evaluator_target_rows),
            "expected": len(evaluator_target_rows),
            "failure_type": "contract_violation" if not target_gate_pass else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-actor-contract-preserved",
            "gate_family": "actor_contract",
            "status_pass": actor_gate_pass and P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            "observed": f"actor_rows={sum(_bool(row['status_pass']) for row in actor_rows)};obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "expected": f"actor_rows={len(actor_rows)};obs=72;action=3",
            "failure_type": "contract_violation" if not actor_gate_pass else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "gate_id": "m2887-no-forbidden-claim-made",
            "gate_family": "claim_boundary",
            "status_pass": blocked_claim_gate_pass,
            "observed": sum(_bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows),
            "expected": 0,
            "failure_type": "proof_washout" if not blocked_claim_gate_pass else "none",
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_follow_up_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": DEFAULT_NEXT_BLOCKER,
        "type": "gate",
        "gate_tier": "process",
        "promotion_decision": "not_applicable",
        "hypothesis": "A bounded result audit can accept or reject the M2887 capability-prediction dataset materialization before any modeling or training.",
        "lineage": {
            "parent_checkpoint": summary["baseline_checkpoints"],
            "parent_dataset": [
                summary["artifacts"]["summary"],
                summary["artifacts"]["usable_task_rows"],
                summary["artifacts"]["profile_task_rows"],
                summary["artifacts"]["evaluator_target_rows"],
                summary["artifacts"]["excluded_source_singleton_rows"],
                summary["artifacts"]["excluded_guard_rows"],
                summary["artifacts"]["actor_feature_contract_rows"],
                "docs/m2886-paper-route-l0-l1-l2-l3-capability-prediction-panel-audit-synthesis-or-data-design.md",
                "docs/m2885-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-result-audit.md",
            ],
            "parent_config": [
                "experiments/manifests/m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight.json"
            ],
            "parent_objective": [
                "audit whether M2887 materialized a complete actor-safe capability-prediction dataset contract"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2886-paper-route-l0-l1-l2-l3-capability-prediction-panel-audit-synthesis-or-data-design",
                "m2884-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-preflight",
            ],
            "blocked_by": [
                "M2887 dataset materialization must be audited before modeling implementation",
                "17 usable rows remain a dataset contract and not paper proof by themselves",
                "34 source-singleton rows and 21 guard rows must remain excluded",
            ],
            "supersedes": [
                "starting capability-prediction modeling directly from inventory rows without materialization audit",
                "treating materialized rows as controller-family verdict evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{DEFAULT_NEXT_BLOCKER}.md",
        "public_gates": [
            "M2888 must audit M2887 summary row counts gates actor contract target boundary and claim rows",
            "M2888 must accept or reject the 17 usable task rows and 204 profile-task rows",
            "M2888 must preserve source-singleton and guard exclusions and evaluator-only target boundaries",
            "M2888 must not train validate rank promote or claim driver performance finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout validate train rank promote or publish a package",
            "do not change actor input or action contract",
            "do not convert materialized rows into paper proof or controller-family ranking",
            "do not claim driver performance paper current-sim high-fidelity full-driver or self-ID evidence",
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
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization",
            "evidence_axis": "route_b_capability_prediction_dataset_contract_result_audit",
            "evidence_increment": "audits the first actor-safe capability-prediction dataset contract before any modeling",
            "claim_scope": "Result audit only; no model training validation ranking finite-window-vs-GRU verdict or self-ID claim",
            "stop_condition": [
                "stop if row counts target boundaries or actor contract fail",
                "stop if source-singleton or guard exclusions are weakened",
                "stop if the audit would claim driver performance or self-ID evidence",
            ],
            "fallback_plan": [
                "route to dataset repair if materialization is incomplete but actor-safe",
                "route to fresh/source-diverse data-panel design if the 17-row contract is too weak",
                "route to capability-prediction modeling design only if audit accepts completeness and boundaries",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2887 writes dataset materialization artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "M2887 capability-prediction dataset materialization result audit",
            "admission_evidence": [
                "M2887 wrote dataset contract artifacts",
                "M2886 admitted read-only materialization over 17 usable rows",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation training ranking promotion",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as paper proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{DEFAULT_NEXT_BLOCKER}.md",
                "M2888 status queue scoreboard research log and review",
                "one bounded follow-up manifest only if the audit selects a route",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2887 materialization is accepted or rejected",
                "one next Route B action or stop decision is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2888 audits dataset materialization only and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2888; later tests require fair L0/L1/L2/L3 capability-prediction comparisons."
            ],
            "temporal_evidence_window": "M2884-M2887 Route B capability-prediction inventory and dataset contract.",
            "negative_result_policy": "Preserve insufficient dataset or boundary failure as a negative result rather than weakening actor contract.",
            "allowed_claims": [
                "M2887 materialization accepted or rejected",
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
            "evidence_expansion": "audits the newly materialized dataset contract",
            "paper_verdict_delta": "no verdict; may admit later capability-prediction modeling design if accepted",
            "must_synthesize_if": [
                "M2888 cannot decide whether M2887 materialization is sufficient",
                "M2888 would claim self-ID finite-window-vs-GRU driver performance or current-sim verdict",
            ],
        },
        "success_criteria": [
            f"docs/{DEFAULT_NEXT_BLOCKER}.md exists",
            "audit accepts or rejects M2887 materialization completeness and claim safety",
            "audit selects exactly one bounded next route or stop decision",
        ],
        "failure_criteria": [
            "M2888 resets steps rolls out validates trains ranks promotes or executes policy action",
            "M2888 changes actor input or action contract",
            "M2888 claims driver performance finite-window-vs-GRU verdict paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "decision_rule": "Pass only if M2888 writes a claim-safe audit of M2887 materialization before any modeling or training.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{DEFAULT_NEXT_BLOCKER}.md", "type": "md"}],
        "baseline_checkpoints": summary["baseline_checkpoints"],
        "baseline_artifacts": [
            summary["artifacts"]["summary"],
            summary["artifacts"]["usable_task_rows"],
            summary["artifacts"]["profile_task_rows"],
            summary["artifacts"]["evaluator_target_rows"],
            summary["artifacts"]["actor_feature_contract_rows"],
        ],
        "scoreboard_checkpoint": f"docs/{DEFAULT_NEXT_BLOCKER}.md",
        "next_blocker": "m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design",
    }


def write_preflight_artifacts(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
    m2884_dir: Path = DEFAULT_M2884_DIR,
    m1690_workload: Path = DEFAULT_M1690_WORKLOAD,
    expected_usable_count: int = 17,
    expected_source_singleton_count: int = 34,
    expected_guard_count: int = 21,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    m2884_summary_path = m2884_dir / "summary.json"
    m2884_summary = read_json(m2884_summary_path) if m2884_summary_path.exists() else {}
    candidate_rows = _read_csv_rows(m2884_dir / "candidate_panel_rows.csv")
    target_inventory_rows = _read_csv_rows(m2884_dir / "target_inventory_rows.csv")
    actor_contract_rows = _read_csv_rows(m2884_dir / "actor_contract_rows.csv")
    workload_rows = _read_csv_rows(m1690_workload)

    usable_task_rows = build_usable_task_rows(candidate_rows)
    profile_task_rows = build_profile_task_rows(usable_task_rows=usable_task_rows, workload_rows=workload_rows)
    evaluator_target_rows = build_evaluator_target_rows(target_inventory_rows)
    source_singleton_rows = build_exclusion_rows(candidate_rows, "source-singleton")
    guard_rows = build_exclusion_rows(candidate_rows, "guard")
    actor_rows = build_actor_feature_contract_rows(actor_contract_rows)
    claim_rows = build_claim_rows()
    expected_profile_task_count = expected_usable_count * len(REQUIRED_PROFILES)
    gate_rows = build_gate_rows(
        m2884_summary_exists=m2884_summary_path.exists(),
        m2884_summary_status_pass=_bool(m2884_summary.get("status_pass")),
        candidate_rows=candidate_rows,
        usable_task_rows=usable_task_rows,
        profile_task_rows=profile_task_rows,
        evaluator_target_rows=evaluator_target_rows,
        source_singleton_rows=source_singleton_rows,
        guard_rows=guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        expected_usable_count=expected_usable_count,
        expected_profile_task_count=expected_profile_task_count,
        expected_source_singleton_count=expected_source_singleton_count,
        expected_guard_count=expected_guard_count,
    )
    gate_matrix_pass = bool(gate_rows) and all(_bool(row["status_pass"]) for row in gate_rows)
    classification_counts = Counter(row.get("classification", "") for row in candidate_rows)
    task_family_counts = Counter(row.get("task_family", "") for row in usable_task_rows)
    env_template_counts = Counter(row.get("env_template_family", "") for row in usable_task_rows)
    profile_level_counts = Counter(row.get("profile_level", "") for row in profile_task_rows)
    decision = (
        "dataset_materialization_complete_route_to_m2888_result_audit"
        if gate_matrix_pass
        else "dataset_materialization_incomplete_route_to_m2888_result_audit"
    )
    artifacts = {
        "summary": output_dir / "summary.json",
        "usable_task_rows": output_dir / "usable_task_rows.csv",
        "profile_task_rows": output_dir / "profile_task_rows.csv",
        "evaluator_target_rows": output_dir / "evaluator_target_rows.csv",
        "excluded_source_singleton_rows": output_dir / "excluded_source_singleton_rows.csv",
        "excluded_guard_rows": output_dir / "excluded_guard_rows.csv",
        "actor_feature_contract_rows": output_dir / "actor_feature_contract_rows.csv",
        "dataset_gate_rows": output_dir / "dataset_gate_rows.csv",
        "claim_rows": output_dir / "claim_rows.csv",
        "run_state": output_dir / "run_state.json",
    }
    baseline_checkpoints = [
        "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
        "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
    ]
    summary: dict[str, Any] = {
        "milestone": DEFAULT_MILESTONE,
        "generated_at_utc": utc_timestamp(),
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": decision,
        "next_blocker": DEFAULT_NEXT_BLOCKER,
        "m2884_dir": str(m2884_dir),
        "m2884_summary_exists": m2884_summary_path.exists(),
        "m2884_summary_status_pass": _bool(m2884_summary.get("status_pass")),
        "m1690_workload": str(m1690_workload),
        "m1690_workload_exists": m1690_workload.exists(),
        "candidate_panel_row_count": len(candidate_rows),
        "usable_task_row_count": len(usable_task_rows),
        "profile_task_row_count": len(profile_task_rows),
        "expected_usable_task_row_count": expected_usable_count,
        "expected_profile_task_row_count": expected_profile_task_count,
        "source_singleton_exclusion_row_count": len(source_singleton_rows),
        "expected_source_singleton_exclusion_row_count": expected_source_singleton_count,
        "guard_exclusion_row_count": len(guard_rows),
        "expected_guard_exclusion_row_count": expected_guard_count,
        "evaluator_target_row_count": len(evaluator_target_rows),
        "actor_feature_contract_row_count": len(actor_rows),
        "dataset_gate_row_count": len(gate_rows),
        "claim_row_count": len(claim_rows),
        "classification_counts": dict(sorted(classification_counts.items())),
        "usable_task_family_counts": dict(sorted(task_family_counts.items())),
        "usable_env_template_counts": dict(sorted(env_template_counts.items())),
        "profile_level_counts": dict(sorted(profile_level_counts.items())),
        "required_profile_count": len(REQUIRED_PROFILES),
        "required_profiles": REQUIRED_PROFILES,
        "evaluator_targets_actor_visible": any(_bool(row["actor_visible_allowed"]) for row in evaluator_target_rows),
        "hidden_oracle_actor_input_required": False,
        "actor_contract_shape_72_action_3": P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
        "source_singleton_rows_paper_proof_allowed": any(_bool(row["paper_proof_allowed"]) for row in source_singleton_rows),
        "guard_rows_ordinary_success_denominator_allowed": any(
            _bool(row["ordinary_success_denominator_allowed"]) for row in guard_rows
        ),
        "false_claim_flags": FALSE_CLAIM_FLAGS.copy(),
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "baseline_checkpoints": baseline_checkpoints,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "follow_up_manifest": str(follow_up_manifest),
    }
    follow_up = build_follow_up_manifest(summary)
    follow_up_manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(follow_up_manifest, follow_up)
    summary["follow_up_manifest_exists"] = follow_up_manifest.exists()

    write_csv_rows(artifacts["usable_task_rows"], usable_task_rows, fieldnames=USABLE_TASK_FIELDNAMES)
    write_csv_rows(artifacts["profile_task_rows"], profile_task_rows, fieldnames=PROFILE_TASK_FIELDNAMES)
    write_csv_rows(artifacts["evaluator_target_rows"], evaluator_target_rows, fieldnames=EVALUATOR_TARGET_FIELDNAMES)
    write_csv_rows(artifacts["excluded_source_singleton_rows"], source_singleton_rows, fieldnames=EXCLUSION_FIELDNAMES)
    write_csv_rows(artifacts["excluded_guard_rows"], guard_rows, fieldnames=EXCLUSION_FIELDNAMES)
    write_csv_rows(artifacts["actor_feature_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(artifacts["dataset_gate_rows"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_csv_rows(artifacts["claim_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(artifacts["run_state"], {"summary": summary, "follow_up_manifest": follow_up})
    write_json(artifacts["summary"], summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--m2884-dir", type=Path, default=DEFAULT_M2884_DIR)
    parser.add_argument("--m1690-workload", type=Path, default=DEFAULT_M1690_WORKLOAD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = write_preflight_artifacts(
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        m2884_dir=args.m2884_dir,
        m1690_workload=args.m1690_workload,
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"decision={summary['decision']}")
    print(f"usable_task_row_count={summary['usable_task_row_count']}")
    print(f"profile_task_row_count={summary['profile_task_row_count']}")


if __name__ == "__main__":
    main()
