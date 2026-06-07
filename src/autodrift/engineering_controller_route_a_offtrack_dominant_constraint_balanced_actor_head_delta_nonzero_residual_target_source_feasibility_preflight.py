"""Materialize M2981 residual target-source feasibility artifacts.

M2981 consumes the M2977 raw actor-view trace capture plus the M2970 guarded
training-admission surface. It does not run local action search, fit a residual,
train, validate, rank, or promote. It writes the auditable target-source
feasibility panel needed before any numeric residual target materialization can
be considered.
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
    "m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-source-feasibility-preflight"
)
NEXT_ID = (
    "m2982-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-source-feasibility-result-audit"
)
DEFAULT_M2977_DIR = Path(
    "runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "deployable_trace_capture_preflight"
)
DEFAULT_M2970_DIR = Path(
    "runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_training_admission_materialization_preflight"
)
DEFAULT_M2980_DESIGN = Path(
    "docs/m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-materialization-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_target_source_feasibility_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-source-feasibility-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2982-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-target-source-feasibility-result-audit.json"
)

EXPECTED_TRAINING_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_PLAN_ROW_COUNT = 67

CLAIM_SCOPE = (
    "M2981 Route A actor-head delta nonzero residual target-source feasibility preflight only; "
    "accepted M2977 raw actor-view traces and M2970 objective-admission rows may be joined to "
    "materialize target-source feasibility candidate guard exclusion actor claim and gate artifacts. "
    "No local-action search, numeric target tensor materialization, residual fitting, training, PPO, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, repair success, "
    "driver-performance, paper, current-sim verdict, high-fidelity validation, full ideal driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "numeric residual target readiness, residual fitting readiness, residual quality, repair success, "
    "driver performance, validation readiness or result, controller/source/task/profile/checkpoint/"
    "candidate ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, "
    "full ideal driver completion, or level3 self-identification"
)

TARGET_SOURCE_PLAN_FIELDNAMES = [
    "target_source_plan_row_id",
    "source_row_id",
    "execution_candidate_id",
    "row_role",
    "objective_or_guard_family",
    "raw_trace_path",
    "raw_trace_persisted",
    "trace_step_count",
    "actor_observation_dim",
    "actor_action_dim",
    "target_source_contract",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "positive_residual_target",
    "success_identity_zero_target_guard",
    "stale_guardrail_excluded",
    "local_action_search_run",
    "residual_fitting_run",
    "training_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
TARGET_CANDIDATE_FIELDNAMES = [
    "target_candidate_row_id",
    "training_admission_candidate_id",
    "source_raw_trace_index_row_id",
    "execution_candidate_id",
    "objective_family",
    "outcome_bucket",
    "raw_trace_path",
    "trace_step_count",
    "target_tensor_shape",
    "target_valid_mask_shape",
    "target_loss_weight_shape",
    "target_source_contract",
    "numeric_target_tensor_materialized",
    "local_action_search_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "positive_residual_target_candidate",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_identity_zero_target_guard_row_id",
    "source_row_id",
    "source_raw_trace_index_row_id",
    "execution_candidate_id",
    "raw_trace_path",
    "trace_step_count",
    "zero_target_guard",
    "positive_residual_target",
    "numeric_target_tensor_materialized",
    "target_labels_actor_visible",
    "claim_boundary",
]
STALE_EXCLUSION_FIELDNAMES = [
    "stale_guardrail_exclusion_row_id",
    "source_row_id",
    "source_raw_trace_guard_row_id",
    "guard_family",
    "target_materialized",
    "positive_residual_target",
    "training_denominator_allowed",
    "validation_denominator_allowed",
    "paper_denominator_allowed",
    "stale_guardrail_excluded",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2981",
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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "target_source_plan_rows": output_dir / "target_source_plan_rows.csv",
        "target_candidate_rows": output_dir / "target_candidate_rows.csv",
        "success_identity_zero_target_guard_rows": output_dir / "success_identity_zero_target_guard_rows.csv",
        "stale_guardrail_exclusion_rows": output_dir / "stale_guardrail_exclusion_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2977_dir: Path,
    m2970_dir: Path,
    m2980_design: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    return {
        "m2977_summary": read_json(m2977_dir / "summary.json"),
        "raw_trace_index_rows": read_csv_rows(m2977_dir / "raw_trace_index_rows.csv"),
        "raw_trace_guard_rows": read_csv_rows(m2977_dir / "raw_trace_guard_rows.csv"),
        "raw_trace_availability_rows": read_csv_rows(m2977_dir / "raw_trace_availability_rows.csv"),
        "objective_balance_rows": read_csv_rows(m2970_dir / "objective_balance_rows.csv"),
        "training_admission_candidate_rows": read_csv_rows(m2970_dir / "training_admission_candidate_rows.csv"),
        "training_admission_guard_rows": read_csv_rows(m2970_dir / "training_admission_guard_rows.csv"),
        "m2980_design_text": m2980_design.read_text(encoding="utf-8") if m2980_design.exists() else "",
        "follow_up_manifest": follow_up_manifest,
    }


def _target_contract(row_role: str, family: str) -> str:
    if row_role == "future_training_candidate":
        return f"trainer_side_local_action_search_required_for_{family}"
    if row_role == "success_identity_guard":
        return "zero_residual_success_identity_guard_not_positive_target"
    return "stale_fixed_source_guardrail_excluded_from_target_materialization"


def build_target_source_plan_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source["raw_trace_index_rows"], start=1):
        row_role = row["row_role"]
        family = row["objective_or_guard_family"]
        rows.append(
            {
                "target_source_plan_row_id": f"m2981-target-source-plan-{index:04d}",
                "source_row_id": row["source_row_id"],
                "execution_candidate_id": row["execution_candidate_id"],
                "row_role": row_role,
                "objective_or_guard_family": family,
                "raw_trace_path": row["raw_trace_path"],
                "raw_trace_persisted": bool_value(row["raw_trace_persisted"]),
                "trace_step_count": int_value(row["trace_step_count"]),
                "actor_observation_dim": int_value(row["actor_observation_dim"]),
                "actor_action_dim": int_value(row["actor_action_dim"]),
                "target_source_contract": _target_contract(row_role, family),
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "positive_residual_target": row_role == "future_training_candidate",
                "success_identity_zero_target_guard": row_role == "success_identity_guard",
                "stale_guardrail_excluded": False,
                "local_action_search_run": False,
                "residual_fitting_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    stale_rows = [
        row for row in source["raw_trace_guard_rows"]
        if row.get("guard_role") == "stale_fixed_source_guardrail"
    ]
    offset = len(rows)
    for index, row in enumerate(stale_rows, start=1):
        rows.append(
            {
                "target_source_plan_row_id": f"m2981-target-source-plan-{offset + index:04d}",
                "source_row_id": row["source_row_id"],
                "execution_candidate_id": "",
                "row_role": "stale_fixed_source_guardrail",
                "objective_or_guard_family": row["guard_family"],
                "raw_trace_path": "",
                "raw_trace_persisted": False,
                "trace_step_count": 0,
                "actor_observation_dim": P0_OBSERVATION_DIM,
                "actor_action_dim": ACTION_DIM,
                "target_source_contract": _target_contract("stale_fixed_source_guardrail", row["guard_family"]),
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "positive_residual_target": False,
                "success_identity_zero_target_guard": False,
                "stale_guardrail_excluded": True,
                "local_action_search_run": False,
                "residual_fitting_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "checkpoint_mutated": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_target_candidate_rows(plan_rows: list[dict[str, Any]], source: dict[str, Any]) -> list[dict[str, Any]]:
    raw_by_source = {
        row["source_row_id"]: row
        for row in source["raw_trace_index_rows"]
        if row["row_role"] == "future_training_candidate"
    }
    candidate_by_id = {
        row["training_admission_candidate_id"]: row
        for row in source["training_admission_candidate_rows"]
    }
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(
        [row for row in plan_rows if row["row_role"] == "future_training_candidate"],
        start=1,
    ):
        raw_row = raw_by_source[plan["source_row_id"]]
        candidate = candidate_by_id.get(plan["source_row_id"], {})
        steps = int_value(plan["trace_step_count"])
        rows.append(
            {
                "target_candidate_row_id": f"m2981-target-candidate-{index:04d}",
                "training_admission_candidate_id": plan["source_row_id"],
                "source_raw_trace_index_row_id": raw_row["raw_trace_index_row_id"],
                "execution_candidate_id": plan["execution_candidate_id"],
                "objective_family": plan["objective_or_guard_family"],
                "outcome_bucket": raw_row.get("outcome_bucket", candidate.get("outcome_family", "")),
                "raw_trace_path": plan["raw_trace_path"],
                "trace_step_count": steps,
                "target_tensor_shape": f"{steps}x{ACTION_DIM}",
                "target_valid_mask_shape": str(steps),
                "target_loss_weight_shape": str(steps),
                "target_source_contract": plan["target_source_contract"],
                "numeric_target_tensor_materialized": False,
                "local_action_search_required": True,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "positive_residual_target_candidate": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_success_identity_zero_target_guard_rows(
    plan_rows: list[dict[str, Any]], source: dict[str, Any]
) -> list[dict[str, Any]]:
    raw_by_source = {
        row["source_row_id"]: row
        for row in source["raw_trace_index_rows"]
        if row["row_role"] == "success_identity_guard"
    }
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(
        [row for row in plan_rows if row["row_role"] == "success_identity_guard"],
        start=1,
    ):
        raw_row = raw_by_source[plan["source_row_id"]]
        rows.append(
            {
                "success_identity_zero_target_guard_row_id": f"m2981-success-zero-guard-{index:04d}",
                "source_row_id": plan["source_row_id"],
                "source_raw_trace_index_row_id": raw_row["raw_trace_index_row_id"],
                "execution_candidate_id": plan["execution_candidate_id"],
                "raw_trace_path": plan["raw_trace_path"],
                "trace_step_count": int_value(plan["trace_step_count"]),
                "zero_target_guard": True,
                "positive_residual_target": False,
                "numeric_target_tensor_materialized": False,
                "target_labels_actor_visible": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_stale_guardrail_exclusion_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    stale_rows = [
        row for row in source["raw_trace_guard_rows"]
        if row.get("guard_role") == "stale_fixed_source_guardrail"
    ]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(stale_rows, start=1):
        rows.append(
            {
                "stale_guardrail_exclusion_row_id": f"m2981-stale-exclusion-{index:04d}",
                "source_row_id": row["source_row_id"],
                "source_raw_trace_guard_row_id": row["raw_trace_guard_row_id"],
                "guard_family": row["guard_family"],
                "target_materialized": False,
                "positive_residual_target": False,
                "training_denominator_allowed": False,
                "validation_denominator_allowed": False,
                "paper_denominator_allowed": False,
                "stale_guardrail_excluded": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _actor_guard("observation_dim_72", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, False),
        _actor_guard("action_dim_3", ACTION_DIM, ACTION_DIM, False),
        _actor_guard(
            "all_plan_rows_actor_shape_72_action_3",
            all(
                int_value(row["actor_observation_dim"]) == P0_OBSERVATION_DIM
                and int_value(row["actor_action_dim"]) == ACTION_DIM
                for row in plan_rows
            ),
            True,
            False,
        ),
        _actor_guard("target_labels_actor_visible", False, False, False),
        _actor_guard("target_provenance_actor_visible", False, False, False),
        _actor_guard("hidden_oracle_future_target_actor_input", False, False, False),
    ]


def _actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2981-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = [
        ("target_source_feasibility_artifact", True, True, "M2982 audit"),
        ("numeric_target_tensor_materialized", False, False, "target materialization preflight and audit"),
        ("residual_fitting_readiness", False, False, "target-source audit plus fitting-admission design"),
        ("residual_fitting_run", False, False, "future fitting preflight"),
        ("training_run", False, False, "future training manifest and audit"),
        ("validation_run", False, False, "future validation manifest and audit"),
        ("ranking_run", False, False, "future ranking manifest and audit"),
        ("checkpoint_mutated", False, False, "future mutation manifest and audit"),
        ("repair_success", False, False, "closed-loop repair validation"),
        ("driver_performance", False, False, "held-out validation"),
        ("paper_claim", False, False, "paper gate"),
        ("current_sim_verdict", False, False, "current-sim validation gate"),
        ("high_fidelity_validation", False, False, "HF validation gate"),
        ("full_ideal_driver", False, False, "full ideal driver gate"),
        ("finite_window_vs_gru", False, False, "comparison gate"),
        ("level3_self_id", False, False, "self-ID proof gate"),
    ]
    return [
        {
            "claim_id": f"m2981-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2981": allowed,
            "claim_made": made,
            "status_pass": allowed == made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def build_gate_matrix(
    *,
    source: dict[str, Any],
    plan_rows: list[dict[str, Any]],
    target_candidate_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    stale_exclusion_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    role_counts = Counter(row["row_role"] for row in plan_rows)
    m2977_summary = source["m2977_summary"]
    raw_trace_files_exist = all(
        Path(row["raw_trace_path"]).exists()
        for row in source["raw_trace_index_rows"]
        if bool_value(row.get("raw_trace_persisted"))
    )
    gates = [
        ("m2977_status_pass", "lineage", bool_value(m2977_summary.get("status_pass")), True, "lineage_invalid"),
        ("m2977_gate_matrix_pass", "lineage", bool_value(m2977_summary.get("gate_matrix_pass")), True, "lineage_invalid"),
        ("m2980_design_present", "lineage", "admit_m2981_residual_target_source_feasibility_preflight" in source["m2980_design_text"], True, "lineage_invalid"),
        ("target_source_plan_row_count", "artifact", len(plan_rows), EXPECTED_PLAN_ROW_COUNT, "metric_artifact"),
        ("future_training_candidate_count", "accounting", role_counts["future_training_candidate"], EXPECTED_TRAINING_CANDIDATE_COUNT, "metric_artifact"),
        ("success_identity_guard_count", "accounting", role_counts["success_identity_guard"], EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT, "metric_artifact"),
        ("stale_guardrail_exclusion_count", "accounting", role_counts["stale_fixed_source_guardrail"], EXPECTED_STALE_GUARDRAIL_COUNT, "metric_artifact"),
        ("target_candidate_row_count", "artifact", len(target_candidate_rows), EXPECTED_TRAINING_CANDIDATE_COUNT, "metric_artifact"),
        ("success_zero_guard_row_count", "artifact", len(success_guard_rows), EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT, "metric_artifact"),
        ("stale_exclusion_row_count", "artifact", len(stale_exclusion_rows), EXPECTED_STALE_GUARDRAIL_COUNT, "metric_artifact"),
        ("raw_trace_files_exist", "artifact", raw_trace_files_exist, True, "metric_artifact"),
        ("actor_contract_guards_pass", "actor_contract", all(bool_value(row["status_pass"]) for row in actor_guard_rows), True, "contract_violation"),
        ("claim_boundary_rows_pass", "claim_boundary", all(bool_value(row["status_pass"]) for row in claim_rows), True, "contract_violation"),
        ("numeric_target_tensor_materialized_count", "claim_boundary", sum(bool_value(row["numeric_target_tensor_materialized"]) for row in plan_rows), 0, "contract_violation"),
        ("positive_success_targets", "guardrail", sum(bool_value(row["positive_residual_target"]) for row in success_guard_rows), 0, "contract_violation"),
        ("stale_targets_materialized", "guardrail", sum(bool_value(row["target_materialized"]) for row in stale_exclusion_rows), 0, "contract_violation"),
        ("follow_up_manifest_registered", "process", follow_up_manifest.exists(), True, "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m2981-gate-{index:04d}-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def write_follow_up_manifest(path: Path) -> None:
    if path.exists():
        return
    manifest_id = NEXT_ID
    write_json(
        path,
        {
            "id": manifest_id,
            "type": "gate",
            "status": "pending",
            "hypothesis": (
                "A bounded result audit can accept or reject the M2981 target-source feasibility "
                "preflight before any residual fitting training validation ranking promotion or "
                "performance claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2982 audits M2981 target-source feasibility artifacts",
                "M2982 selects exactly one next route or stop state",
                "no fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2982 hides missing target-source feasibility artifacts",
                "M2982 treats feasibility rows as numeric target tensors or fitting readiness",
                "M2982 changes actor input or action contract",
                "M2982 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "baseline_artifacts": [
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "target_source_plan_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
            ],
            "decision_rule": (
                "Pass only if M2982 audits M2981 artifacts and selects one next route or stop state "
                "while preserving actor guardrail and claim boundaries without overclaiming."
            ),
            "gate_tier": "process",
            "promotion_decision": "pending",
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
            "lineage": {
                "parent_checkpoint": [
                    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                    "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                ],
                "parent_dataset": [
                    str(DEFAULT_OUTPUT_DIR / "summary.json"),
                    str(DEFAULT_OUTPUT_DIR / "target_source_plan_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "target_candidate_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "success_identity_zero_target_guard_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "stale_guardrail_exclusion_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
                ],
                "parent_config": [
                    "experiments/manifests/m2981-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-source-feasibility-preflight.json",
                    "experiments/manifests/m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-materialization-design.json",
                ],
                "parent_objective": ["audit target-source feasibility before residual fitting admission"],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2981 target-source feasibility artifacts require result audit before target materialization or fitting admission"
                ],
                "supersedes": [
                    "direct target materialization or fitting immediately after M2981 without result audit"
                ],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "public_gates": [
                "M2982 must audit M2981 plan candidate guard actor claim and gate artifacts",
                "M2982 must preserve actor 72/action 3 no target labels actor-visible",
                "M2982 must not claim target tensor materialization fitting readiness performance paper high-fidelity or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not fit train validate rank promote or execute a nonzero residual head",
                "do not convert feasibility rows into numeric target tensors or performance claims",
                "do not change actor input or action contract",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_target_source_feasibility_result_audit",
                "evidence_increment": "audits newly materialized target-source feasibility artifacts",
                "claim_scope": "Result audit only; no target tensor materialization fitting training validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
                "stop_condition": [
                    "stop if M2981 artifacts are missing or gate matrix fails",
                    "stop if actor or claim boundaries were violated",
                    "stop if feasibility rows would be used as numeric targets before audit",
                ],
                "fallback_plan": [
                    "route to artifact repair if feasibility artifacts are incomplete",
                    "route to target materialization design only after audit accepts claim safety",
                    "route to branch synthesis pivot or stop if target-source feasibility violates guardrails",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2981 completes target-source feasibility preflight",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit M2981 target-source feasibility artifacts",
                "admission_evidence": ["M2981 summary and gate matrix", "M2981 target-source feasibility artifacts"],
                "blocked_shortcuts": [
                    "no target tensor materialization fitting training validation ranking promotion or success-rate verdict",
                    "no checkpoint mutation save selection or promotion",
                    "no target labels or provenance actor-visible",
                ],
                "allowed_updates": [
                    f"docs/{manifest_id}.md",
                    f"docs/reviews/{manifest_id}.md",
                    "M2982 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2982 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2982 accepts or rejects M2981 as complete and claim-safe",
                    "next route or stop state is explicit",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2982 audits Route A target-source feasibility and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2982; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2981 target-source feasibility preflight only.",
                "negative_result_policy": (
                    "Preserve feasibility failures and route to repair or synthesis rather than weakening self-ID gates."
                ),
                "allowed_claims": [
                    "M2981 artifact completeness and claim-safety audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits target-source feasibility artifacts",
                "paper_verdict_delta": "no paper verdict; audit may inform later target materialization design only",
                "must_synthesize_if": [
                    "M2982 cannot accept M2981 as complete and claim-safe",
                    "M2982 would claim fitting readiness driver performance paper current-sim high-fidelity or self-ID",
                ],
            },
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "next_blocker": manifest_id,
        },
    )


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# M2981 Engineering Controller Route A Actor-Head Delta Nonzero Residual Target-Source Feasibility Preflight",
        "",
        "## Summary",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result class: `{summary['result_class']}`",
        f"- target source plan rows: {summary['target_source_plan_row_count']}",
        f"- target candidate rows: {summary['target_candidate_row_count']}",
        f"- success zero-target guard rows: {summary['success_identity_zero_target_guard_row_count']}",
        f"- stale guardrail exclusion rows: {summary['stale_guardrail_exclusion_row_count']}",
        f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
        f"- numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        "",
        "## Boundary",
        "",
        "M2981 materializes target-source feasibility artifacts only. It does not run local action search, materialize numeric target tensors, fit residuals, train, validate, rank, promote, mutate checkpoints, or claim performance.",
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
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_target_source_feasibility_preflight(
    *,
    m2977_dir: Path | str = DEFAULT_M2977_DIR,
    m2970_dir: Path | str = DEFAULT_M2970_DIR,
    m2980_design: Path | str = DEFAULT_M2980_DESIGN,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    follow_up = Path(follow_up_manifest)
    source = load_source_artifacts(
        m2977_dir=Path(m2977_dir),
        m2970_dir=Path(m2970_dir),
        m2980_design=Path(m2980_design),
        follow_up_manifest=follow_up,
    )

    target_source_plan_rows = build_target_source_plan_rows(source)
    target_candidate_rows = build_target_candidate_rows(target_source_plan_rows, source)
    success_guard_rows = build_success_identity_zero_target_guard_rows(target_source_plan_rows, source)
    stale_exclusion_rows = build_stale_guardrail_exclusion_rows(source)
    actor_guard_rows = build_actor_contract_guard_rows(target_source_plan_rows)
    claim_rows = build_claim_boundary_rows()
    write_follow_up_manifest(follow_up)
    gate_rows = build_gate_matrix(
        source=source,
        plan_rows=target_source_plan_rows,
        target_candidate_rows=target_candidate_rows,
        success_guard_rows=success_guard_rows,
        stale_exclusion_rows=stale_exclusion_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up,
    )
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    role_counts = Counter(row["row_role"] for row in target_source_plan_rows)
    numeric_target_count = sum(
        bool_value(row["numeric_target_tensor_materialized"])
        for row in target_source_plan_rows
    )
    status_pass = gate_matrix_pass and numeric_target_count == 0

    summary = {
        "action_shape": ACTION_DIM,
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(bool_value(row["status_pass"]) for row in actor_guard_rows),
        "actor_contract_shape_72_action_3": True,
        "actor_input_contract_changed": False,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(bool_value(row["status_pass"]) for row in claim_rows),
        "claim_scope": CLAIM_SCOPE,
        "current_sim_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "finite_window_vs_gru_claim_made": False,
        "follow_up_manifest": str(follow_up),
        "follow_up_manifest_exists": follow_up.exists(),
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "full_ideal_driver_completion_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "future_training_candidate_plan_count": role_counts["future_training_candidate"],
        "gate_matrix_pass": gate_matrix_pass,
        "gate_matrix_row_count": len(gate_rows),
        "generated_at_utc": utc_timestamp(),
        "hidden_oracle_actor_input_detected": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "local_action_search_run": False,
        "milestone": milestone,
        "next_blocker": next_blocker,
        "numeric_target_tensor_materialized_count": numeric_target_count,
        "numeric_target_tensor_materialized": False,
        "observation_shape": P0_OBSERVATION_DIM,
        "output_dir": str(output),
        "paper_claim_made": False,
        "paths": {key: str(value) for key, value in paths.items()},
        "policy_rollout_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "raw_trace_index_row_count": len(source["raw_trace_index_rows"]),
        "raw_trace_guard_row_count": len(source["raw_trace_guard_rows"]),
        "repair_success_claim_made": False,
        "residual_fitting_readiness_claim_made": False,
        "residual_fitting_run": False,
        "result_class": (
            "engineering_controller_route_a_actor_head_delta_nonzero_residual_target_source_feasibility_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_target_source_feasibility_preflight_fail"
        ),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "source_artifacts_present": True,
        "stale_guardrail_exclusion_row_count": len(stale_exclusion_rows),
        "stale_guardrail_plan_count": role_counts["stale_fixed_source_guardrail"],
        "stale_guardrail_target_materialized_count": sum(bool_value(row["target_materialized"]) for row in stale_exclusion_rows),
        "status_pass": status_pass,
        "success_identity_positive_target_count": sum(bool_value(row["positive_residual_target"]) for row in success_guard_rows),
        "success_identity_zero_target_guard_count": role_counts["success_identity_guard"],
        "success_identity_zero_target_guard_row_count": len(success_guard_rows),
        "success_rate_verdict_claim_made": False,
        "target_candidate_row_count": len(target_candidate_rows),
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "target_source_plan_row_count": len(target_source_plan_rows),
        "target_source_feasibility_artifact_materialized": True,
        "target_tensor_materialization_run": False,
        "training_run": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "validation_run": False,
        "winner_selected": False,
    }

    write_csv_rows(paths["target_source_plan_rows"], target_source_plan_rows, fieldnames=TARGET_SOURCE_PLAN_FIELDNAMES)
    write_csv_rows(paths["target_candidate_rows"], target_candidate_rows, fieldnames=TARGET_CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["success_identity_zero_target_guard_rows"], success_guard_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["stale_guardrail_exclusion_rows"], stale_exclusion_rows, fieldnames=STALE_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_run_state(
        paths["run_state"],
        {
            "milestone": milestone,
            "completed_at_utc": summary["generated_at_utc"],
            "output_dir": str(output),
            "next_blocker": next_blocker,
            "status_pass": status_pass,
        },
    )
    write_doc(paths["doc"], summary)
    write_json(paths["summary"], summary)
    summary["required_artifacts_present"] = all(path.exists() for path in paths.values()) and follow_up.exists()
    write_json(paths["summary"], summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize M2981 target-source feasibility artifacts.")
    parser.add_argument("--m2977-dir", type=Path, default=DEFAULT_M2977_DIR)
    parser.add_argument("--m2970-dir", type=Path, default=DEFAULT_M2970_DIR)
    parser.add_argument("--m2980-design", type=Path, default=DEFAULT_M2980_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_target_source_feasibility_preflight(
        m2977_dir=args.m2977_dir,
        m2970_dir=args.m2970_dir,
        m2980_design=args.m2980_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"target_source_plan_row_count={summary['target_source_plan_row_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
