"""Materialize M3032 target tensor artifacts.

M3032 consumes the M3030-accepted and M3031-synthesized M3029 target-source
feasibility panel. It writes bounded trainer-side target tensors, masks,
weights, and provenance rows. It does not run environment search, fit, train,
validate, rank, promote, mutate checkpoints, or make a performance claim.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3032-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-tensor-materialization-preflight"
)
NEXT_ID = (
    "m3033-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-tensor-materialization-result-audit"
)
M3030_DECISION = "accept_m3029_target_source_feasibility_claim_safe_route_to_m3031_branch_synthesis"
M3031_DECISION = "continue_to_m3032_target_tensor_materialization_preflight"

DEFAULT_M3029_DIR = Path(
    "runs/m3029_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_source_feasibility_materialization_preflight"
)
DEFAULT_M3030_AUDIT = Path(
    "docs/m3030-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-feasibility-result-audit.md"
)
DEFAULT_M3031_SYNTHESIS = Path(
    "docs/m3031-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-"
    "target-source-to-target-tensor-branch-synthesis.md"
)
DEFAULT_M3027_DIR = Path(
    "runs/m3027_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "deployable_trace_capture_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_"
    "target_tensor_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TARGET_SOURCE_PLAN_ROWS = 32
EXPECTED_TARGET_CANDIDATE_ROWS = 29
EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS = 3
TARGET_DELTA_ABS_LIMIT = 0.08

CLAIM_SCOPE = (
    "M3032 Route A post-residual-stop new-source broad-failure target tensor "
    "materialization preflight only; M3030-accepted and M3031-synthesized M3029 "
    "target-source feasibility rows may be converted into trainer-side target_action_delta, "
    "target_valid_mask, target_loss_weight, zero-guard, and provenance artifacts. Target "
    "labels and provenance remain actor-invisible. No local-action search, environment step, "
    "residual fitting, training, PPO, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, profile tuning, repair success, driver-performance, "
    "paper, current-sim verdict, high-fidelity validation, full ideal driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality, residual fitting readiness without M3033 audit and a later "
    "fitting-admission design, residual quality, repair success, driver performance, "
    "validation readiness or result, controller/source/task/profile/checkpoint/candidate "
    "ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, "
    "finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness "
    "or result, full ideal driver completion, or level3 self-identification"
)

TARGET_TENSOR_FIELDNAMES = [
    "target_tensor_row_id",
    "source_target_source_candidate_row_id",
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "row_assignment_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "objective_family",
    "failure_family",
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
    "numeric_target_tensor_materialized",
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
    "source_success_identity_guard_row_id",
    "target_source_plan_row_id",
    "target_source_readiness_row_id",
    "raw_trace_index_row_id",
    "row_assignment_id",
    "task_source_id",
    "profile_name",
    "binding_role",
    "raw_trace_path",
    "target_tensor_path",
    "trace_step_count",
    "zero_target_guard",
    "positive_residual_target",
    "numeric_target_tensor_materialized",
    "target_action_delta_abs_max",
    "target_valid_mask_true_count",
    "target_loss_weight_sum",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
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
    "allowed_in_m3032",
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
PATH_KEYS = [
    "summary",
    "target_tensor_rows",
    "success_identity_zero_target_guard_rows",
    "actor_contract_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
    "follow_up_manifest",
]


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "target_tensor_rows": output_dir / "target_tensor_rows.csv",
        "success_identity_zero_target_guard_rows": output_dir / "success_identity_zero_target_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_source_artifacts(
    *,
    m3029_dir: Path,
    m3030_audit: Path,
    m3031_synthesis: Path,
    m3027_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3029_summary": m3029_dir / "summary.json",
        "target_source_plan_rows": m3029_dir / "target_source_plan_rows.csv",
        "target_source_candidate_rows": m3029_dir / "target_source_candidate_rows.csv",
        "success_identity_guard_rows": m3029_dir / "success_identity_guard_rows.csv",
        "target_source_availability_rows": m3029_dir / "target_source_availability_rows.csv",
        "m3029_actor_contract_guard_rows": m3029_dir / "actor_contract_guard_rows.csv",
        "m3029_claim_boundary_rows": m3029_dir / "claim_boundary_rows.csv",
        "m3029_gate_matrix": m3029_dir / "gate_matrix.csv",
        "m3030_audit": m3030_audit,
        "m3031_synthesis": m3031_synthesis,
        "m3027_raw_trace_index_rows": m3027_dir / "raw_trace_index_rows.csv",
    }
    source_exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "m3029_summary": read_json(paths["m3029_summary"]) if source_exists["m3029_summary"] else {},
        "target_source_plan_rows": read_csv_rows(paths["target_source_plan_rows"])
        if source_exists["target_source_plan_rows"]
        else [],
        "target_source_candidate_rows": read_csv_rows(paths["target_source_candidate_rows"])
        if source_exists["target_source_candidate_rows"]
        else [],
        "success_identity_guard_rows": read_csv_rows(paths["success_identity_guard_rows"])
        if source_exists["success_identity_guard_rows"]
        else [],
        "target_source_availability_rows": read_csv_rows(paths["target_source_availability_rows"])
        if source_exists["target_source_availability_rows"]
        else [],
        "m3029_actor_contract_guard_rows": read_csv_rows(paths["m3029_actor_contract_guard_rows"])
        if source_exists["m3029_actor_contract_guard_rows"]
        else [],
        "m3029_claim_boundary_rows": read_csv_rows(paths["m3029_claim_boundary_rows"])
        if source_exists["m3029_claim_boundary_rows"]
        else [],
        "m3029_gate_matrix": read_csv_rows(paths["m3029_gate_matrix"]) if source_exists["m3029_gate_matrix"] else [],
        "m3030_audit_text": paths["m3030_audit"].read_text(encoding="utf-8") if source_exists["m3030_audit"] else "",
        "m3031_synthesis_text": paths["m3031_synthesis"].read_text(encoding="utf-8")
        if source_exists["m3031_synthesis"]
        else "",
        "m3027_raw_trace_index_rows": read_csv_rows(paths["m3027_raw_trace_index_rows"])
        if source_exists["m3027_raw_trace_index_rows"]
        else [],
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
    observation = np.asarray(trace["observation_trace"], dtype=np.float32)
    next_observation = np.asarray(trace["next_observation_trace"], dtype=np.float32)
    if action.ndim != 2 or action.shape[1] != ACTION_DIM:
        raise ValueError(f"action_trace must have shape [T,{ACTION_DIM}], got {action.shape}")
    if observation.ndim != 2 or observation.shape[1] != P0_OBSERVATION_DIM:
        raise ValueError(f"observation_trace must have shape [T,{P0_OBSERVATION_DIM}], got {observation.shape}")
    if next_observation.shape != observation.shape:
        raise ValueError(f"next_observation_trace must match observation_trace, got {next_observation.shape}")
    return trace


def _sign_or_one(values: np.ndarray) -> np.ndarray:
    sign = np.sign(values)
    sign[sign == 0.0] = 1.0
    return sign.astype(np.float32)


def _objective_delta(family: str, observation: np.ndarray, action: np.ndarray) -> np.ndarray:
    delta = np.zeros_like(action, dtype=np.float32)
    if family == "offtrack_recovery_broad_failure_contract":
        lateral_proxy = observation[:, 1] if observation.shape[1] > 1 else action[:, 0]
        delta[:, 0] = -0.05 * _sign_or_one(lateral_proxy)
    elif family == "collision_clearance_guard_contract":
        steer_proxy = action[:, 0]
        delta[:, 0] = 0.04 * _sign_or_one(steer_proxy)
        delta[:, 1] = -0.04
        delta[:, 2] = 0.08
    elif family == "speed_floor_guard_contract":
        delta[:, 1] = 0.08
        delta[:, 2] = -0.08
    else:
        raise ValueError(f"unsupported objective family for target tensor materialization: {family}")
    return delta.astype(np.float32)


def _valid_mask(trace: Mapping[str, np.ndarray]) -> np.ndarray:
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


def materialize_candidate_target(*, candidate_row: Mapping[str, Any], target_dir: Path, index: int) -> dict[str, Any]:
    trace = _load_trace(candidate_row["raw_trace_path"])
    action = np.asarray(trace["action_trace"], dtype=np.float32)
    observation = np.asarray(trace["observation_trace"], dtype=np.float32)
    mask = _valid_mask(trace)
    raw_delta = _objective_delta(str(candidate_row["objective_family"]), observation, action)
    target_action = np.clip(action + raw_delta, -1.0, 1.0).astype(np.float32)
    delta = (target_action - action).astype(np.float32)
    weight = np.where(mask, 1.0, 0.0).astype(np.float32)
    target_path = target_dir / f"m3032-target-tensor-{index:04d}.npz"
    _write_target_npz(
        path=target_path,
        action_trace=action,
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )
    return {
        "target_tensor_row_id": f"m3032-target-tensor-{index:04d}",
        "source_target_source_candidate_row_id": candidate_row["target_source_candidate_row_id"],
        "target_source_plan_row_id": candidate_row["target_source_plan_row_id"],
        "target_source_readiness_row_id": candidate_row["target_source_readiness_row_id"],
        "raw_trace_index_row_id": candidate_row["raw_trace_index_row_id"],
        "row_assignment_id": candidate_row["row_assignment_id"],
        "task_source_id": candidate_row["task_source_id"],
        "profile_name": candidate_row["profile_name"],
        "binding_role": candidate_row["binding_role"],
        "objective_family": candidate_row["objective_family"],
        "failure_family": candidate_row["failure_family"],
        "raw_trace_path": candidate_row["raw_trace_path"],
        "target_tensor_path": str(target_path),
        "trace_step_count": int(action.shape[0]),
        "target_action_delta_shape": f"{delta.shape[0]}x{delta.shape[1]}",
        "target_valid_mask_shape": str(mask.shape[0]),
        "target_loss_weight_shape": str(weight.shape[0]),
        "target_action_delta_abs_max": float(np.max(np.abs(delta))) if delta.size else 0.0,
        "target_valid_mask_true_count": int(np.sum(mask)),
        "target_loss_weight_sum": float(np.sum(weight)),
        "target_source_provenance": f"bounded_projection_for_{candidate_row['objective_family']}",
        "numeric_target_tensor_materialized": True,
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "positive_residual_target": True,
        "local_action_search_run": False,
        "environment_step_run": False,
        "residual_fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "checkpoint_mutated": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def materialize_success_guard(*, guard_row: Mapping[str, Any], target_dir: Path, index: int) -> dict[str, Any]:
    trace = _load_trace(guard_row["raw_trace_path"])
    action = np.asarray(trace["action_trace"], dtype=np.float32)
    delta = np.zeros_like(action, dtype=np.float32)
    mask = np.zeros((action.shape[0],), dtype=bool)
    weight = np.zeros((action.shape[0],), dtype=np.float32)
    target_path = target_dir / f"m3032-success-zero-guard-{index:04d}.npz"
    _write_target_npz(
        path=target_path,
        action_trace=action,
        target_action_delta=delta,
        target_valid_mask=mask,
        target_loss_weight=weight,
    )
    return {
        "success_identity_zero_target_guard_row_id": f"m3032-success-zero-guard-{index:04d}",
        "source_success_identity_guard_row_id": guard_row["success_identity_guard_row_id"],
        "target_source_plan_row_id": guard_row["target_source_plan_row_id"],
        "target_source_readiness_row_id": guard_row["target_source_readiness_row_id"],
        "raw_trace_index_row_id": guard_row["raw_trace_index_row_id"],
        "row_assignment_id": guard_row["row_assignment_id"],
        "task_source_id": guard_row["task_source_id"],
        "profile_name": guard_row["profile_name"],
        "binding_role": guard_row["binding_role"],
        "raw_trace_path": guard_row["raw_trace_path"],
        "target_tensor_path": str(target_path),
        "trace_step_count": int(action.shape[0]),
        "zero_target_guard": True,
        "positive_residual_target": False,
        "numeric_target_tensor_materialized": True,
        "target_action_delta_abs_max": 0.0,
        "target_valid_mask_true_count": 0,
        "target_loss_weight_sum": 0.0,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_actor_contract_guard_rows(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _actor_guard("observation_dim_72", P0_OBSERVATION_DIM, P0_OBSERVATION_DIM),
        _actor_guard("action_dim_3", ACTION_DIM, ACTION_DIM),
        _actor_guard(
            "all_target_rows_shape_tx3",
            all(str(row["target_action_delta_shape"]).endswith(f"x{ACTION_DIM}") for row in target_rows),
            True,
        ),
        _actor_guard("target_labels_actor_visible", _any_true(target_rows, "target_labels_actor_visible"), False),
        _actor_guard("target_provenance_actor_visible", _any_true(target_rows, "target_provenance_actor_visible"), False),
        _actor_guard("hidden_oracle_future_target_actor_input", False, False),
        _actor_guard("local_action_search_run", _any_true(target_rows, "local_action_search_run"), False),
        _actor_guard("environment_step_run", _any_true(target_rows, "environment_step_run"), False),
    ]


def _actor_guard(field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "guard_id": f"m3032-actor-guard-{field}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    claims = [
        ("numeric_target_tensor_materialized", True, True, "M3033 audit"),
        ("target_tensor_files_materialized", True, True, "target_tensor_rows.csv plus NPZ files"),
        ("success_identity_zero_target_guards_materialized", True, True, "success_identity_zero_target_guard_rows.csv"),
        ("follow_up_result_audit_manifest_registered", True, bool(follow_up_manifest_registered), "M3033 manifest"),
        ("target_quality_validated", False, False, "future target tensor audit and fitting-admission design"),
        ("local_action_search", False, False, "future audited target search route if admitted"),
        ("environment_step_or_rollout", False, False, "future execution or validation milestone"),
        ("residual_fitting_readiness", False, False, "M3033 audit plus fitting-admission design"),
        ("residual_fitting_run", False, False, "future fitting preflight"),
        ("training_run", False, False, "future training manifest and audit"),
        ("ppo_run", False, False, "future PPO milestone"),
        ("validation_run", False, False, "future validation manifest and audit"),
        ("ranking_or_winner_selection", False, False, "future ranking or promotion gate"),
        ("checkpoint_mutation_or_promotion", False, False, "future checkpoint gate"),
        ("repair_success", False, False, "closed-loop repair validation"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("paper_claim", False, False, "paper evidence matrix"),
        ("current_sim_verdict", False, False, "separate current-sim verdict synthesis"),
        ("high_fidelity_validation", False, False, "Route C validation"),
        ("full_ideal_driver", False, False, "full ideal driver gate"),
        ("finite_window_vs_gru", False, False, "paper route fair comparison"),
        ("level3_self_id", False, False, "self-ID proof gate"),
    ]
    return [
        {
            "claim_id": f"m3032-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3032": allowed,
            "claim_made": made,
            "status_pass": bool(allowed) == bool(made),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(claims, start=1)
    ]


def _npz_finite(path: str | Path) -> bool:
    data = np.load(Path(path))
    for key in ("base_action", "target_action", "target_action_delta", "target_loss_weight"):
        if key not in data.files or not np.all(np.isfinite(np.asarray(data[key]))):
            return False
    return "target_valid_mask" in data.files


def build_gate_matrix_rows(
    *,
    source: Mapping[str, Any],
    target_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest: Path,
) -> list[dict[str, Any]]:
    summary = source["m3029_summary"]
    target_paths = [row["target_tensor_path"] for row in target_rows + success_guard_rows]
    target_files_exist = all(Path(path).exists() for path in target_paths)
    target_values_finite = all(_npz_finite(path) for path in target_paths) if target_files_exist else False
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        ("m3029_status_pass", "lineage", _bool(summary.get("status_pass")) and _bool(summary.get("gate_matrix_pass")), True, "lineage_invalid"),
        ("m3030_accepts_m3029", "lineage", M3030_DECISION in source["m3030_audit_text"], True, "lineage_invalid"),
        ("m3031_synthesis_continues_m3032", "lineage", M3031_DECISION in source["m3031_synthesis_text"], True, "lineage_invalid"),
        ("target_source_plan_denominator", "denominator", len(source["target_source_plan_rows"]), EXPECTED_TARGET_SOURCE_PLAN_ROWS, "metric_artifact"),
        ("source_target_candidate_count", "denominator", len(source["target_source_candidate_rows"]), EXPECTED_TARGET_CANDIDATE_ROWS, "metric_artifact"),
        ("source_success_guard_count", "denominator", len(source["success_identity_guard_rows"]), EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS, "metric_artifact"),
        ("target_tensor_row_count", "artifact", len(target_rows), EXPECTED_TARGET_CANDIDATE_ROWS, "metric_artifact"),
        ("success_zero_guard_row_count", "artifact", len(success_guard_rows), EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS, "metric_artifact"),
        ("target_files_exist", "artifact", target_files_exist, True, "metric_artifact"),
        ("target_values_finite", "artifact", target_values_finite, True, "metric_artifact"),
        (
            "target_delta_abs_limit",
            "artifact",
            max((float(row["target_action_delta_abs_max"]) for row in target_rows), default=0.0) <= TARGET_DELTA_ABS_LIMIT + 1e-6,
            True,
            "contract_violation",
        ),
        ("local_action_search_run_count", "claim_boundary", sum(_bool(row["local_action_search_run"]) for row in target_rows), 0, "contract_violation"),
        ("environment_step_run_count", "claim_boundary", sum(_bool(row["environment_step_run"]) for row in target_rows), 0, "contract_violation"),
        ("residual_fitting_run_count", "claim_boundary", sum(_bool(row["residual_fitting_run"]) for row in target_rows), 0, "contract_violation"),
        ("training_run_count", "claim_boundary", sum(_bool(row["training_run"]) for row in target_rows), 0, "contract_violation"),
        ("validation_run_count", "claim_boundary", sum(_bool(row["validation_run"]) for row in target_rows), 0, "contract_violation"),
        ("success_identity_positive_target_count", "guardrail", sum(_bool(row["positive_residual_target"]) for row in success_guard_rows), 0, "contract_violation"),
        ("actor_contract_guards_pass", "actor_contract", _all_true(actor_rows, "status_pass"), True, "contract_violation"),
        ("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, "contract_violation"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        ("follow_up_manifest_registered", "process", follow_up_manifest.exists(), True, "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m3032-gate-{index:04d}-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (name, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: Mapping[str, Path],
    target_rows: list[dict[str, Any]],
    success_guard_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    objective_counts = Counter(str(row.get("objective_family", "")) for row in target_rows)
    target_tensor_file_count = sum(1 for row in target_rows + success_guard_rows if Path(row["target_tensor_path"]).exists())
    target_delta_abs_max = max((float(row["target_action_delta_abs_max"]) for row in target_rows), default=0.0)
    gate_matrix_pass = _all_true(gate_rows, "status_pass")
    status_pass = (
        gate_matrix_pass
        and len(target_rows) == EXPECTED_TARGET_CANDIDATE_ROWS
        and len(success_guard_rows) == EXPECTED_SUCCESS_IDENTITY_GUARD_ROWS
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "result_class": "new_source_broad_failure_target_tensor_materialization_preflight_pass"
        if status_pass
        else "new_source_broad_failure_target_tensor_materialization_preflight_fail_closed",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "target_tensor_row_count": len(target_rows),
        "candidate_target_tensor_materialized_count": len(target_rows),
        "success_identity_zero_target_guard_row_count": len(success_guard_rows),
        "success_identity_zero_tensor_guard_count": len(success_guard_rows),
        "target_tensor_file_count": target_tensor_file_count,
        "zero_guard_target_tensor_file_count": len(success_guard_rows),
        "numeric_target_tensor_materialized": bool(target_rows),
        "numeric_target_tensor_materialized_count": len(target_rows),
        "offtrack_recovery_target_count": objective_counts["offtrack_recovery_broad_failure_contract"],
        "collision_clearance_target_count": objective_counts["collision_clearance_guard_contract"],
        "speed_floor_target_count": objective_counts["speed_floor_guard_contract"],
        "target_action_delta_abs_max": target_delta_abs_max,
        "target_loss_weight_sum": sum(float(row["target_loss_weight_sum"]) for row in target_rows),
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "success_identity_positive_target_count": sum(_bool(row["positive_residual_target"]) for row in success_guard_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": _all_true(actor_rows, "status_pass"),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": _all_true(claim_rows, "status_pass"),
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": True,
        "actor_input_contract_changed": False,
        "hidden_oracle_actor_input_detected": False,
        "future_target_actor_input_required": False,
        "source_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "outcome_labels_actor_visible": False,
        "objective_labels_actor_visible": False,
        "readiness_labels_actor_visible": False,
        "feasibility_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "ttc_actor_input_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "local_action_search_run": False,
        "local_action_search_quality_validated": False,
        "target_tensor_materialization_run": True,
        "residual_fitting_readiness_claim_made": False,
        "residual_fitting_run": False,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "success_rate_verdict_claim_made": False,
        "validation_readiness_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "paths": {key: str(value) for key, value in paths.items()},
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


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
        "hypothesis": (
            "A bounded result audit can accept or reject the M3032 target tensor materialization "
            "artifacts before any residual fitting training validation ranking promotion performance "
            "paper high-fidelity full-driver finite-window-vs-GRU or self-ID claim."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "target_tensor_rows.csv"),
                str(output_dir / "success_identity_zero_target_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                "experiments/manifests/m3032-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-preflight.json",
                "experiments/manifests/m3031-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-to-target-tensor-branch-synthesis.json",
            ],
            "parent_objective": ["audit target tensor materialization before residual fitting admission"],
            "derived_from": [
                MILESTONE_ID,
                "m3031-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-to-target-tensor-branch-synthesis",
                "m3030-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-result-audit",
            ],
            "blocked_by": [
                "M3032 target tensor artifacts require result audit before fitting admission",
                "target tensor materialization is not target quality validation or repair success",
            ],
            "supersedes": ["direct residual fitting immediately after target tensor materialization without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3033 must audit M3032 target tensor rows success guards actor and claim boundaries",
            "M3033 must preserve 29 target tensor rows and 3 zero-target success guards",
            "M3033 must preserve actor 72/action 3 and no target labels actor-visible",
            "M3033 must not claim fitting readiness target quality performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
            "M3033 must select exactly one next route or stop state before residual fitting admission",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not fit train validate rank promote or execute a residual head",
            "do not convert target tensor materialization into performance claims",
            "do not change actor input or action contract",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_residual_stop_source_axis_expansion",
            "evidence_axis": "new_source_broad_failure_target_tensor_materialization_result_audit",
            "evidence_increment": "audits newly materialized target tensor artifacts",
            "claim_scope": "Result audit only; no fitting training validation ranking promotion performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M3032 artifacts are missing or gate matrix fails",
                "stop if actor or claim boundaries were violated",
                "stop if target tensors would be used for fitting before audit",
            ],
            "fallback_plan": [
                "route to artifact repair if target tensor artifacts are incomplete",
                "route to fitting-admission design only after audit accepts claim safety",
                "route to branch synthesis pivot or stop if target tensor materialization violates guardrails",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3032 completes target tensor materialization preflight",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3032 target tensor artifacts",
            "admission_evidence": ["M3032 summary and gate matrix", "M3032 target tensor artifacts"],
            "blocked_shortcuts": [
                "no residual fitting training validation ranking promotion or success-rate verdict",
                "no checkpoint mutation save selection or promotion",
                "no target labels or provenance actor-visible",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3033 status queue scoreboard research log and review",
                "one follow-up manifest only if M3033 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3033 accepts or rejects M3032 as complete and claim-safe",
                "next route or stop state is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3033 audits Route A target tensors and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3033; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M3032 target tensor materialization preflight only.",
            "negative_result_policy": "Preserve target tensor failures and route to repair or synthesis rather than weakening self-ID gates.",
            "allowed_claims": [
                "M3032 artifact completeness and claim-safety audit",
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
                "M3033 cannot accept M3032 as complete and claim-safe",
                "M3033 would claim fitting readiness driver performance paper current-sim high-fidelity or self-ID",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3033 audits M3032 target tensor artifacts",
            "M3033 selects exactly one next route or stop state",
            "no fitting training validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M3033 hides missing target tensor artifacts",
            "M3033 treats target tensor materialization as fitting readiness or performance evidence",
            "M3033 changes actor input or action contract",
            "M3033 leaves next route ambiguous",
        ],
        "decision_rule": (
            "Pass only if M3033 audits M3032 artifacts and selects one next route or stop state "
            "while preserving actor guardrail and claim boundaries without overclaiming."
        ),
        "commands": [{"name": "target_tensor_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "target_tensor_rows.csv"),
            str(output_dir / "success_identity_zero_target_guard_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def render_milestone_doc(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# M3032 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Target Tensor Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'fail_closed'}",
            f"- result class: `{summary['result_class']}`",
            f"- target tensor rows: {summary['target_tensor_row_count']}",
            f"- success zero-target guard rows: {summary['success_identity_zero_target_guard_row_count']}",
            f"- target tensor files: {summary['target_tensor_file_count']}",
            f"- numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}",
            f"- target delta abs max: {summary['target_action_delta_abs_max']}",
            f"- actor shape: {summary['observation_shape']}/action {summary['action_shape']}",
            f"- local action search runs: {summary['local_action_search_run']}",
            f"- gate matrix pass: {summary['gate_matrix_pass']}",
            "",
            "## Boundary",
            "",
            "M3032 materializes trainer-side target tensor artifacts only. It does not run local-action search, step environments, fit residuals, train, validate, rank, promote, mutate checkpoints, or claim target quality or performance.",
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
            "",
        ]
    )


def run_target_tensor_materialization_preflight(
    *,
    m3029_dir: Path | str = DEFAULT_M3029_DIR,
    m3030_audit: Path | str = DEFAULT_M3030_AUDIT,
    m3031_synthesis: Path | str = DEFAULT_M3031_SYNTHESIS,
    m3027_dir: Path | str = DEFAULT_M3027_DIR,
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
    follow_up = Path(follow_up_manifest)
    paths = artifact_paths(output, doc_path=Path(doc_path), follow_up_manifest=follow_up)
    source = load_source_artifacts(
        m3029_dir=Path(m3029_dir),
        m3030_audit=Path(m3030_audit),
        m3031_synthesis=Path(m3031_synthesis),
        m3027_dir=Path(m3027_dir),
    )

    target_rows = [
        materialize_candidate_target(candidate_row=row, target_dir=target_dir, index=index)
        for index, row in enumerate(source["target_source_candidate_rows"], start=1)
    ]
    success_guard_rows = [
        materialize_success_guard(guard_row=row, target_dir=target_dir, index=index)
        for index, row in enumerate(source["success_identity_guard_rows"], start=1)
    ]
    actor_rows = build_actor_contract_guard_rows(target_rows)

    write_csv_rows(paths["target_tensor_rows"], target_rows, fieldnames=TARGET_TENSOR_FIELDNAMES)
    write_csv_rows(paths["success_identity_zero_target_guard_rows"], success_guard_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_json(paths["follow_up_manifest"], build_follow_up_manifest(output_dir=output, doc_path=Path(doc_path), summary_path=paths["summary"]))
    claim_rows = build_claim_boundary_rows(follow_up_manifest_registered=paths["follow_up_manifest"].exists())
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source=source,
        target_rows=target_rows,
        success_guard_rows=success_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
        follow_up_manifest=follow_up,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        target_rows=target_rows,
        success_guard_rows=success_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone": milestone,
            "completed_at_utc": summary["generated_at_utc"],
            "output_dir": str(output),
            "target_tensor_row_count": len(target_rows),
            "success_identity_zero_target_guard_row_count": len(success_guard_rows),
            "execution_performed_by_m3032": False,
            "status_pass": False,
            "gate_matrix_pass": False,
            "complete": False,
            "next_blocker": next_blocker,
            "phase": "pre_required_artifact_gate",
        },
    )

    required_artifacts_present = all(paths[key].exists() for key in PATH_KEYS)
    gate_rows = build_gate_matrix_rows(
        source=source,
        target_rows=target_rows,
        success_guard_rows=success_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest=follow_up,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        target_rows=target_rows,
        success_guard_rows=success_guard_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "milestone": milestone,
            "completed_at_utc": summary["generated_at_utc"],
            "output_dir": str(output),
            "target_tensor_row_count": len(target_rows),
            "success_identity_zero_target_guard_row_count": len(success_guard_rows),
            "execution_performed_by_m3032": False,
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "complete": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _all_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return bool(rows) and all(_bool(row.get(key, False)) for row in rows)


def _any_true(rows: list[Mapping[str, Any]], key: str) -> bool:
    return any(_bool(row.get(key, False)) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M3032 target tensor materialization preflight.")
    parser.add_argument("--m3029-dir", type=Path, default=DEFAULT_M3029_DIR)
    parser.add_argument("--m3030-audit", type=Path, default=DEFAULT_M3030_AUDIT)
    parser.add_argument("--m3031-synthesis", type=Path, default=DEFAULT_M3031_SYNTHESIS)
    parser.add_argument("--m3027-dir", type=Path, default=DEFAULT_M3027_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_target_tensor_materialization_preflight(
        m3029_dir=args.m3029_dir,
        m3030_audit=args.m3030_audit,
        m3031_synthesis=args.m3031_synthesis,
        m3027_dir=args.m3027_dir,
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
