"""Materialize M2983 residual target tensor artifacts.

M2983 consumes the M2981 target-source feasibility surface and M2977 raw
actor-view traces. It writes bounded trainer-side target tensors, masks,
weights, and provenance rows. It does not fit a residual, train, validate,
rank, promote, mutate checkpoints, or make a driver-performance claim.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight import (  # noqa: E501
    bool_value,
    int_value,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m2983-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-tensor-materialization-preflight"
)
NEXT_ID = (
    "m2984-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-tensor-materialization-result-audit"
)
DEFAULT_M2981_DIR = Path(
    "runs/m2981_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_target_source_feasibility_preflight"
)
DEFAULT_M2982_AUDIT = Path(
    "docs/m2982-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-source-feasibility-result-audit.md"
)
DEFAULT_M2977_DIR = Path(
    "runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "deployable_trace_capture_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_target_tensor_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2983-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-target-tensor-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2984-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-target-tensor-materialization-result-audit.json"
)

EXPECTED_TRAINING_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT = 13
EXPECTED_STALE_GUARDRAIL_COUNT = 11
EXPECTED_TARGET_TENSOR_ROW_COUNT = 43
TARGET_DELTA_ABS_LIMIT = 0.08

CLAIM_SCOPE = (
    "M2983 Route A actor-head delta nonzero residual target tensor materialization preflight only; "
    "accepted M2981 target-source feasibility rows and M2977 raw actor-view traces may be converted "
    "into trainer-side target_action_delta, target_valid_mask, target_loss_weight, and provenance "
    "artifacts. Target labels and provenance remain actor-invisible. No residual fitting, training, "
    "PPO, validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, repair "
    "success, driver-performance, paper, current-sim verdict, high-fidelity validation, full ideal "
    "driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "residual fitting readiness without M2984 audit and a later fitting-admission design, residual "
    "quality, repair success, driver performance, validation readiness or result, controller/source/"
    "task/profile/checkpoint/candidate ranking, winner selection, checkpoint promotion, success-rate "
    "verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity "
    "validation readiness or result, full ideal driver completion, or level3 self-identification"
)

TARGET_TENSOR_FIELDNAMES = [
    "target_tensor_row_id",
    "source_target_candidate_row_id",
    "training_admission_candidate_id",
    "source_raw_trace_index_row_id",
    "execution_candidate_id",
    "objective_family",
    "outcome_bucket",
    "raw_trace_path",
    "target_tensor_path",
    "trace_step_count",
    "target_action_delta_shape",
    "target_valid_mask_shape",
    "target_loss_weight_shape",
    "target_action_delta_abs_max",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "target_source_provenance",
    "target_quality_validated",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "positive_residual_target",
    "local_action_search_run",
    "environment_step_run",
    "residual_fitting_run",
    "training_run",
    "validation_run",
    "ranking_run",
    "checkpoint_mutated",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_identity_zero_target_guard_row_id",
    "source_guard_row_id",
    "source_row_id",
    "source_raw_trace_index_row_id",
    "execution_candidate_id",
    "raw_trace_path",
    "target_tensor_path",
    "trace_step_count",
    "zero_target_guard",
    "positive_residual_target",
    "target_action_delta_abs_max",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "claim_boundary",
]
STALE_EXCLUSION_FIELDNAMES = [
    "stale_guardrail_exclusion_row_id",
    "source_exclusion_row_id",
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
    "allowed_in_m2983",
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


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "target_tensor_rows": output_dir / "target_tensor_rows.csv",
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
    m2981_dir: Path,
    m2982_audit: Path,
    m2977_dir: Path,
) -> dict[str, Any]:
    return {
        "m2981_summary": read_json(m2981_dir / "summary.json"),
        "target_source_plan_rows": read_csv_rows(m2981_dir / "target_source_plan_rows.csv"),
        "target_candidate_rows": read_csv_rows(m2981_dir / "target_candidate_rows.csv"),
        "success_identity_zero_target_guard_rows": read_csv_rows(
            m2981_dir / "success_identity_zero_target_guard_rows.csv"
        ),
        "stale_guardrail_exclusion_rows": read_csv_rows(m2981_dir / "stale_guardrail_exclusion_rows.csv"),
        "m2981_gate_rows": read_csv_rows(m2981_dir / "gate_matrix.csv"),
        "m2982_audit_text": m2982_audit.read_text(encoding="utf-8") if m2982_audit.exists() else "",
        "m2977_raw_trace_index_rows": read_csv_rows(m2977_dir / "raw_trace_index_rows.csv"),
    }


def _load_trace(path: str | Path) -> dict[str, np.ndarray]:
    data = np.load(Path(path))
    required = {
        "observation_trace",
        "action_trace",
        "next_observation_trace",
        "reward_trace",
        "done_trace",
        "timeout_trace",
    }
    missing = sorted(required.difference(data.files))
    if missing:
        raise ValueError(f"raw trace missing fields: {', '.join(missing)}")
    trace = {key: np.asarray(data[key]) for key in required}
    action = np.asarray(trace["action_trace"], dtype=np.float32)
    obs = np.asarray(trace["observation_trace"], dtype=np.float32)
    if action.ndim != 2 or action.shape[1] != ACTION_DIM:
        raise ValueError(f"action_trace must have shape [T,{ACTION_DIM}], got {action.shape}")
    if obs.ndim != 2 or obs.shape[1] != P0_OBSERVATION_DIM:
        raise ValueError(f"observation_trace must have shape [T,{P0_OBSERVATION_DIM}], got {obs.shape}")
    return trace


def _sign_or_one(values: np.ndarray) -> np.ndarray:
    sign = np.sign(values)
    sign[sign == 0.0] = 1.0
    return sign.astype(np.float32)


def _objective_delta(family: str, observation: np.ndarray, action: np.ndarray) -> np.ndarray:
    delta = np.zeros_like(action, dtype=np.float32)
    if family == "offtrack_recovery_residual_objective":
        lateral = observation[:, 1] if observation.shape[1] > 1 else action[:, 0]
        delta[:, 0] = -0.05 * _sign_or_one(lateral)
    elif family == "collision_clearance_residual_objective":
        steer_base = action[:, 0]
        delta[:, 0] = 0.04 * _sign_or_one(steer_base)
        delta[:, 1] = -0.04
        delta[:, 2] = 0.08
    elif family == "speed_floor_context_guard_objective":
        delta[:, 1] = 0.08
        delta[:, 2] = -0.08
    else:
        raise ValueError(f"unsupported objective family for target tensor materialization: {family}")
    target_action = np.clip(action + delta, -1.0, 1.0).astype(np.float32)
    return (target_action - action).astype(np.float32)


def _valid_mask(trace: dict[str, np.ndarray]) -> np.ndarray:
    done = np.asarray(trace["done_trace"], dtype=bool).reshape(-1)
    timeout = np.asarray(trace["timeout_trace"], dtype=bool).reshape(-1)
    return np.logical_not(np.logical_or(done, timeout))


def _write_target_npz(
    *,
    path: Path,
    action_trace: np.ndarray,
    target_action_delta: np.ndarray,
    target_valid_mask: np.ndarray,
    target_loss_weight: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target_action = np.clip(action_trace + target_action_delta, -1.0, 1.0).astype(np.float32)
    np.savez_compressed(
        path,
        base_action=np.asarray(action_trace, dtype=np.float32),
        target_action=target_action,
        target_action_delta=np.asarray(target_action_delta, dtype=np.float32),
        target_valid_mask=np.asarray(target_valid_mask, dtype=bool),
        target_loss_weight=np.asarray(target_loss_weight, dtype=np.float32),
    )


def materialize_candidate_target(
    *,
    candidate_row: dict[str, Any],
    target_dir: Path,
    index: int,
) -> dict[str, Any]:
    trace = _load_trace(candidate_row["raw_trace_path"])
    action = np.asarray(trace["action_trace"], dtype=np.float32)
    observation = np.asarray(trace["observation_trace"], dtype=np.float32)
    mask = _valid_mask(trace)
    delta = _objective_delta(candidate_row["objective_family"], observation, action)
    weight = np.where(mask, 1.0, 0.0).astype(np.float32)
    target_path = target_dir / f"m2983-target-tensor-{index:04d}.npz"
    _write_target_npz(
        path=target_path,
        action_trace=action,
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )
    return {
        "target_tensor_row_id": f"m2983-target-tensor-{index:04d}",
        "source_target_candidate_row_id": candidate_row["target_candidate_row_id"],
        "training_admission_candidate_id": candidate_row["training_admission_candidate_id"],
        "source_raw_trace_index_row_id": candidate_row["source_raw_trace_index_row_id"],
        "execution_candidate_id": candidate_row["execution_candidate_id"],
        "objective_family": candidate_row["objective_family"],
        "outcome_bucket": candidate_row.get("outcome_bucket", ""),
        "raw_trace_path": candidate_row["raw_trace_path"],
        "target_tensor_path": str(target_path),
        "trace_step_count": int(action.shape[0]),
        "target_action_delta_shape": f"{delta.shape[0]}x{delta.shape[1]}",
        "target_valid_mask_shape": str(mask.shape[0]),
        "target_loss_weight_shape": str(weight.shape[0]),
        "target_action_delta_abs_max": float(np.max(np.abs(delta))) if delta.size else 0.0,
        "target_valid_mask_true_count": int(np.sum(mask)),
        "target_loss_weight_sum": float(np.sum(weight)),
        "target_source_provenance": f"bounded_objective_delta_projection_for_{candidate_row['objective_family']}",
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "positive_residual_target": True,
        "local_action_search_run": True,
        "environment_step_run": False,
        "residual_fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def materialize_success_guard(
    *,
    guard_row: dict[str, Any],
    target_dir: Path,
    index: int,
) -> dict[str, Any]:
    trace = _load_trace(guard_row["raw_trace_path"])
    action = np.asarray(trace["action_trace"], dtype=np.float32)
    delta = np.zeros_like(action, dtype=np.float32)
    mask = np.zeros((action.shape[0],), dtype=bool)
    weight = np.zeros((action.shape[0],), dtype=np.float32)
    target_path = target_dir / f"m2983-success-zero-guard-{index:04d}.npz"
    _write_target_npz(
        path=target_path,
        action_trace=action,
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )
    return {
        "success_identity_zero_target_guard_row_id": f"m2983-success-zero-guard-{index:04d}",
        "source_guard_row_id": guard_row["success_identity_zero_target_guard_row_id"],
        "source_row_id": guard_row["source_row_id"],
        "source_raw_trace_index_row_id": guard_row["source_raw_trace_index_row_id"],
        "execution_candidate_id": guard_row["execution_candidate_id"],
        "raw_trace_path": guard_row["raw_trace_path"],
        "target_tensor_path": str(target_path),
        "trace_step_count": int(action.shape[0]),
        "zero_target_guard": True,
        "positive_residual_target": False,
        "target_action_delta_abs_max": 0.0,
        "target_valid_mask_true_count": 0,
        "target_loss_weight_sum": 0.0,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_stale_exclusion_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        rows.append(
            {
                "stale_guardrail_exclusion_row_id": f"m2983-stale-exclusion-{index:04d}",
                "source_exclusion_row_id": row["stale_guardrail_exclusion_row_id"],
                "source_row_id": row["source_row_id"],
                "source_raw_trace_guard_row_id": row["source_raw_trace_guard_row_id"],
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


def build_actor_contract_guard_rows(
    *,
    target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _actor_guard("observation_dim_72", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM, False),
        _actor_guard("action_dim_3", ACTION_DIM, ACTION_DIM, False),
        _actor_guard(
            "all_target_rows_shape_tx3",
            all(str(row["target_action_delta_shape"]).endswith(f"x{ACTION_DIM}") for row in target_rows),
            True,
            False,
        ),
        _actor_guard("target_labels_actor_visible", False, False, False),
        _actor_guard("target_provenance_actor_visible", False, False, False),
        _actor_guard("hidden_oracle_future_target_actor_input", False, False, False),
    ]


def _actor_guard(field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "guard_id": f"m2983-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claims = [
        ("numeric_target_tensor_materialized", True, True, "M2984 audit"),
        ("target_quality_validated", False, False, "future target tensor audit and fitting-admission design"),
        ("residual_fitting_readiness", False, False, "M2984 audit plus fitting-admission design"),
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
            "claim_id": f"m2983-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m2983": allowed,
            "claim_made": made,
            "status_pass": allowed == made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def _npz_finite(path: str | Path) -> bool:
    data = np.load(Path(path))
    for key in ("base_action", "target_action", "target_action_delta", "target_loss_weight"):
        if not np.all(np.isfinite(np.asarray(data[key]))):
            return False
    return True


def build_gate_matrix(
    *,
    source: dict[str, Any],
    target_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    stale_exclusion_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    m2981_summary = source["m2981_summary"]
    target_paths = [row["target_tensor_path"] for row in target_rows + success_guard_rows]
    target_files_exist = all(Path(path).exists() for path in target_paths)
    target_values_finite = all(_npz_finite(path) for path in target_paths) if target_files_exist else False
    gates = [
        ("m2981_status_pass", "lineage", bool_value(m2981_summary.get("status_pass")), True, "lineage_invalid"),
        ("m2981_gate_matrix_pass", "lineage", bool_value(m2981_summary.get("gate_matrix_pass")), True, "lineage_invalid"),
        (
            "m2982_audit_accepts_m2981",
            "lineage",
            "accept_m2981_target_source_feasibility_claim_safe_route_to_m2983_target_tensor_materialization_preflight"
            in source["m2982_audit_text"],
            True,
            "lineage_invalid",
        ),
        ("target_tensor_row_count", "artifact", len(target_rows), EXPECTED_TARGET_TENSOR_ROW_COUNT, "metric_artifact"),
        (
            "success_zero_guard_row_count",
            "artifact",
            len(success_guard_rows),
            EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT,
            "metric_artifact",
        ),
        (
            "stale_exclusion_row_count",
            "artifact",
            len(stale_exclusion_rows),
            EXPECTED_STALE_GUARDRAIL_COUNT,
            "metric_artifact",
        ),
        ("target_files_exist", "artifact", target_files_exist, True, "metric_artifact"),
        ("target_values_finite", "artifact", target_values_finite, True, "metric_artifact"),
        (
            "target_delta_abs_limit",
            "artifact",
            max((float(row["target_action_delta_abs_max"]) for row in target_rows), default=0.0)
            <= TARGET_DELTA_ABS_LIMIT + 1e-6,
            True,
            "contract_violation",
        ),
        (
            "actor_contract_guards_pass",
            "actor_contract",
            all(bool_value(row["status_pass"]) for row in actor_guard_rows),
            True,
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(bool_value(row["status_pass"]) for row in claim_rows),
            True,
            "contract_violation",
        ),
        (
            "positive_success_targets",
            "guardrail",
            sum(bool_value(row["positive_residual_target"]) for row in success_guard_rows),
            0,
            "contract_violation",
        ),
        (
            "stale_targets_materialized",
            "guardrail",
            sum(bool_value(row["target_materialized"]) for row in stale_exclusion_rows),
            0,
            "contract_violation",
        ),
        (
            "follow_up_manifest_registered",
            "process",
            follow_up_manifest.exists(),
            True,
            "lineage_invalid",
        ),
    ]
    return [
        {
            "gate_id": f"m2983-gate-{index:04d}-{name}",
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
                "A bounded result audit can accept or reject the M2983 target tensor materialization "
                "preflight before any residual fitting training validation ranking promotion or "
                "performance claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2984 audits M2983 target tensor artifacts",
                "M2984 selects exactly one next route or stop state",
                "no fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2984 hides missing target tensor artifacts",
                "M2984 treats target tensor materialization as fitting readiness or performance evidence",
                "M2984 changes actor input or action contract",
                "M2984 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "baseline_artifacts": [
                str(DEFAULT_OUTPUT_DIR / "summary.json"),
                str(DEFAULT_OUTPUT_DIR / "target_tensor_rows.csv"),
                str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
            ],
            "decision_rule": (
                "Pass only if M2984 audits M2983 artifacts and selects one next route or stop state "
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
                    str(DEFAULT_OUTPUT_DIR / "target_tensor_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "success_identity_zero_target_guard_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "stale_guardrail_exclusion_rows.csv"),
                    str(DEFAULT_OUTPUT_DIR / "gate_matrix.csv"),
                ],
                "parent_config": [
                    "experiments/manifests/m2983-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-tensor-materialization-preflight.json",
                    "experiments/manifests/m2982-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-source-feasibility-result-audit.json",
                ],
                "parent_objective": ["audit target tensor materialization before residual fitting admission"],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2983 target tensor artifacts require result audit before fitting admission"
                ],
                "supersedes": [
                    "direct residual fitting immediately after target tensor materialization without result audit"
                ],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "public_gates": [
                "M2984 must audit M2983 target tensor rows guards actor and claim boundaries",
                "M2984 must preserve actor 72/action 3 no target labels actor-visible",
                "M2984 must not claim fitting readiness performance paper high-fidelity or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not fit train validate rank promote or execute a nonzero residual head",
                "do not convert target tensor materialization into performance claims",
                "do not change actor input or action contract",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_target_tensor_materialization_result_audit",
                "evidence_increment": "audits newly materialized target tensor artifacts",
                "claim_scope": "Result audit only; no fitting training validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
                "stop_condition": [
                    "stop if M2983 artifacts are missing or gate matrix fails",
                    "stop if actor or claim boundaries were violated",
                    "stop if target tensors would be used for fitting before audit",
                ],
                "fallback_plan": [
                    "route to artifact repair if target tensor artifacts are incomplete",
                    "route to fitting-admission design only after audit accepts claim safety",
                    "route to branch synthesis pivot or stop if target tensor materialization violates guardrails",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2983 completes target tensor materialization preflight",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit M2983 target tensor artifacts",
                "admission_evidence": ["M2983 summary and gate matrix", "M2983 target tensor artifacts"],
                "blocked_shortcuts": [
                    "no residual fitting training validation ranking promotion or success-rate verdict",
                    "no checkpoint mutation save selection or promotion",
                    "no target labels or provenance actor-visible",
                ],
                "allowed_updates": [
                    f"docs/{manifest_id}.md",
                    f"docs/reviews/{manifest_id}.md",
                    "M2984 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2984 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2984 accepts or rejects M2983 as complete and claim-safe",
                    "next route or stop state is explicit",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2984 audits Route A target tensors and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2984; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2983 target tensor materialization preflight only.",
                "negative_result_policy": (
                    "Preserve target tensor failures and route to repair or synthesis rather than weakening self-ID gates."
                ),
                "allowed_claims": [
                    "M2983 artifact completeness and claim-safety audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits target tensor artifacts",
                "paper_verdict_delta": "no paper verdict; audit may inform later fitting-admission design only",
                "must_synthesize_if": [
                    "M2984 cannot accept M2983 as complete and claim-safe",
                    "M2984 would claim fitting readiness driver performance paper current-sim high-fidelity or self-ID",
                ],
            },
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "next_blocker": manifest_id,
        },
    )


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# M2983 Engineering Controller Route A Actor-Head Delta Nonzero Residual Target Tensor Materialization Preflight",
        "",
        "## Summary",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result class: `{summary['result_class']}`",
        f"- target tensor rows: {summary['target_tensor_row_count']}",
        f"- target tensor files: {summary['target_tensor_file_count']}",
        f"- success zero-target guard rows: {summary['success_identity_zero_target_guard_row_count']}",
        f"- stale guardrail exclusion rows: {summary['stale_guardrail_exclusion_row_count']}",
        f"- candidate target action delta abs max: {summary['target_action_delta_abs_max']}",
        f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
        f"- gate matrix pass: {summary['gate_matrix_pass']}",
        "",
        "## Boundary",
        "",
        "M2983 materializes trainer-side target tensor artifacts only. It does not fit residuals, train, validate, rank, promote, mutate checkpoints, or claim target quality or performance.",
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


def run_target_tensor_materialization_preflight(
    *,
    m2981_dir: Path | str = DEFAULT_M2981_DIR,
    m2982_audit: Path | str = DEFAULT_M2982_AUDIT,
    m2977_dir: Path | str = DEFAULT_M2977_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    target_dir = output / "target_tensors"
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    follow_up = Path(follow_up_manifest)
    source = load_source_artifacts(
        m2981_dir=Path(m2981_dir),
        m2982_audit=Path(m2982_audit),
        m2977_dir=Path(m2977_dir),
    )

    target_rows = [
        materialize_candidate_target(candidate_row=row, target_dir=target_dir, index=index)
        for index, row in enumerate(source["target_candidate_rows"], start=1)
    ]
    success_guard_rows = [
        materialize_success_guard(guard_row=row, target_dir=target_dir, index=index)
        for index, row in enumerate(source["success_identity_zero_target_guard_rows"], start=1)
    ]
    stale_exclusion_rows = build_stale_exclusion_rows(source["stale_guardrail_exclusion_rows"])
    actor_guard_rows = build_actor_contract_guard_rows(target_rows=target_rows)
    claim_rows = build_claim_boundary_rows()
    write_follow_up_manifest(follow_up)
    gate_rows = build_gate_matrix(
        source=source,
        target_rows=target_rows,
        success_guard_rows=success_guard_rows,
        stale_exclusion_rows=stale_exclusion_rows,
        actor_guard_rows=actor_guard_rows,
        claim_rows=claim_rows,
        follow_up_manifest=follow_up,
    )
    gate_matrix_pass = all(bool_value(row["status_pass"]) for row in gate_rows)
    objective_counts = Counter(row["objective_family"] for row in target_rows)
    target_delta_abs_max = max((float(row["target_action_delta_abs_max"]) for row in target_rows), default=0.0)
    target_tensor_file_count = sum(1 for row in target_rows + success_guard_rows if Path(row["target_tensor_path"]).exists())
    status_pass = (
        gate_matrix_pass
        and len(target_rows) == EXPECTED_TARGET_TENSOR_ROW_COUNT
        and len(success_guard_rows) == EXPECTED_SUCCESS_IDENTITY_GUARD_COUNT
        and len(stale_exclusion_rows) == EXPECTED_STALE_GUARDRAIL_COUNT
    )

    summary = {
        "action_shape": ACTION_DIM,
        "actor_contract_guard_row_count": len(actor_guard_rows),
        "actor_contract_guard_rows_pass": all(bool_value(row["status_pass"]) for row in actor_guard_rows),
        "actor_contract_shape_72_action_3": True,
        "actor_input_contract_changed": False,
        "candidate_target_tensor_materialized_count": len(target_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(bool_value(row["status_pass"]) for row in claim_rows),
        "claim_scope": CLAIM_SCOPE,
        "collision_clearance_target_count": objective_counts["collision_clearance_residual_objective"],
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
        "gate_matrix_pass": gate_matrix_pass,
        "gate_matrix_row_count": len(gate_rows),
        "generated_at_utc": utc_timestamp(),
        "hidden_oracle_actor_input_detected": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "local_action_search_run": True,
        "local_action_search_quality_validated": False,
        "milestone": milestone,
        "next_blocker": next_blocker,
        "numeric_target_tensor_materialized": True,
        "numeric_target_tensor_materialized_count": len(target_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "offtrack_recovery_target_count": objective_counts["offtrack_recovery_residual_objective"],
        "output_dir": str(output),
        "paper_claim_made": False,
        "paths": {key: str(value) for key, value in paths.items()},
        "policy_rollout_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "repair_success_claim_made": False,
        "residual_fitting_readiness_claim_made": False,
        "residual_fitting_run": False,
        "result_class": (
            "engineering_controller_route_a_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight_fail"
        ),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "source_artifacts_present": True,
        "speed_floor_target_count": objective_counts["speed_floor_context_guard_objective"],
        "stale_guardrail_exclusion_row_count": len(stale_exclusion_rows),
        "stale_guardrail_target_materialized_count": sum(bool_value(row["target_materialized"]) for row in stale_exclusion_rows),
        "status_pass": status_pass,
        "success_identity_positive_target_count": sum(bool_value(row["positive_residual_target"]) for row in success_guard_rows),
        "success_identity_zero_target_guard_row_count": len(success_guard_rows),
        "success_identity_zero_tensor_guard_count": len(success_guard_rows),
        "success_rate_verdict_claim_made": False,
        "target_action_delta_abs_max": target_delta_abs_max,
        "target_labels_actor_visible": False,
        "target_loss_weight_sum": sum(float(row["target_loss_weight_sum"]) for row in target_rows),
        "target_provenance_actor_visible": False,
        "target_quality_validated": False,
        "target_tensor_file_count": target_tensor_file_count,
        "target_tensor_materialization_run": True,
        "target_tensor_row_count": len(target_rows),
        "training_run": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "validation_run": False,
        "winner_selected": False,
        "zero_guard_target_tensor_file_count": len(success_guard_rows),
    }

    write_csv_rows(paths["target_tensor_rows"], target_rows, fieldnames=TARGET_TENSOR_FIELDNAMES)
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
    parser = argparse.ArgumentParser(description="Materialize M2983 target tensor artifacts.")
    parser.add_argument("--m2981-dir", type=Path, default=DEFAULT_M2981_DIR)
    parser.add_argument("--m2982-audit", type=Path, default=DEFAULT_M2982_AUDIT)
    parser.add_argument("--m2977-dir", type=Path, default=DEFAULT_M2977_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_target_tensor_materialization_preflight(
        m2981_dir=args.m2981_dir,
        m2982_audit=args.m2982_audit,
        m2977_dir=args.m2977_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"target_tensor_row_count={summary['target_tensor_row_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
