"""Run M2993 success-identity guard-constrained residual fitting preflight.

M2993 consumes the accepted M2987 fitting contracts, M2983 target tensors, and
M2991/M2992 audit-synthesis route decision. It fits a second offline residual
artifact with success-identity zero-target rows included as explicit
zero-residual guard samples. It does not run environment validation, rank
candidates, mutate checkpoints, promote checkpoints, or make performance
claims.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_source_feasibility_preflight import (  # noqa: E501
    bool_value,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
import autodrift.engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight as m2990  # noqa: E501


MILESTONE_ID = (
    "m2993-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-preflight"
)
NEXT_ID = (
    "m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-result-audit"
)
DEFAULT_M2987_DIR = m2990.DEFAULT_M2987_DIR
DEFAULT_M2988_AUDIT = m2990.DEFAULT_M2988_AUDIT
DEFAULT_M2989_DESIGN = m2990.DEFAULT_M2989_DESIGN
DEFAULT_M2983_DIR = m2990.DEFAULT_M2983_DIR
DEFAULT_M2990_DIR = m2990.DEFAULT_OUTPUT_DIR
DEFAULT_M2991_AUDIT = Path(
    "docs/m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-bounded-fitting-result-audit.md"
)
DEFAULT_M2992_SYNTHESIS = Path(
    "docs/m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-repair-branch-synthesis.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "nonzero_residual_success_identity_guard_constrained_fitting_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2993-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "nonzero-residual-success-identity-guard-constrained-fitting-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit.json"
)

EXPECTED_CANDIDATE_COUNT = 43
EXPECTED_SUCCESS_GUARD_COUNT = 13
EXPECTED_STALE_EXCLUSION_COUNT = 11
GUARD_WEIGHT_MULTIPLIER = 1000.0
SUCCESS_GUARD_REQUIRED_ABS_MAX = 1.0e-3
M2990_EXPECTED_GUARD_ABS_MAX = 0.07999999821186066

CLAIM_SCOPE = (
    "M2993 Route A actor-head delta nonzero residual success-identity guard-constrained fitting "
    "preflight only; accepted M2987 fitting contracts, M2983 target tensors, M2991 result audit, "
    "and M2992 branch synthesis may be consumed to produce trainer-side offline constrained fitting "
    "artifacts and loss traces for a later M2994 audit. Candidate rows remain the fitting "
    "denominator, success identity rows are zero-residual guard penalty or constraint rows, and "
    "stale fixed-source rows remain excluded. Target labels, provenance, objective families, source "
    "rows, route decisions, and audit verdicts remain actor-invisible. No environment reset, policy "
    "rollout, validation, ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair success, driver-performance, paper, current-sim verdict, high-fidelity validation, full "
    "ideal driver, finite-window-vs-GRU, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target quality validation, closed-loop repair success, driver performance, validation readiness "
    "or result, controller/source/task/profile/checkpoint/candidate ranking, winner selection, "
    "checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, "
    "or level3 self-identification"
)

GUARD_CONSTRAINED_LOSS_FIELDNAMES = [
    "loss_trace_id",
    "fit_stage",
    "step",
    "candidate_sample_count",
    "candidate_weight_sum",
    "success_guard_sample_count",
    "success_guard_weight_sum",
    "candidate_weighted_mse",
    "candidate_weighted_l1",
    "success_guard_predicted_residual_abs_max",
    "success_guard_predicted_residual_mse",
    "combined_weighted_mse",
    "predicted_residual_abs_max",
    "status_pass",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = m2990.SUCCESS_GUARD_FIELDNAMES + [
    "guard_penalty_or_constraint_used",
    "m2990_predicted_residual_abs_max",
    "improved_from_m2990",
    "zero_residual_guard_satisfied",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2993",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
    "claim_boundary",
]
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "fitting_dataset_rows",
    "guard_constrained_loss_trace_rows",
    "success_guard_loss_rows",
    "stale_exclusion_audit_rows",
    "actor_input_exclusion_rows",
    "checkpoint_side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "candidate_residual_head_artifact",
    "run_state",
    "doc",
]


@dataclass(frozen=True)
class GuardBatch:
    observations: np.ndarray
    targets: np.ndarray
    weights: np.ndarray
    rows: list[dict[str, Any]]
    contracts_pass: bool


def run_success_identity_guard_constrained_fitting_preflight(
    *,
    m2987_dir: Path | str = DEFAULT_M2987_DIR,
    m2988_audit: Path | str = DEFAULT_M2988_AUDIT,
    m2989_design: Path | str = DEFAULT_M2989_DESIGN,
    m2991_audit: Path | str = DEFAULT_M2991_AUDIT,
    m2992_synthesis: Path | str = DEFAULT_M2992_SYNTHESIS,
    m2983_dir: Path | str = DEFAULT_M2983_DIR,
    m2990_dir: Path | str = DEFAULT_M2990_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = MILESTONE_ID,
    next_blocker: str = NEXT_ID,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        m2987_dir=Path(m2987_dir),
        m2988_audit=Path(m2988_audit),
        m2989_design=Path(m2989_design),
        m2991_audit=Path(m2991_audit),
        m2992_synthesis=Path(m2992_synthesis),
        m2983_dir=Path(m2983_dir),
        m2990_dir=Path(m2990_dir),
    )

    candidate_batch = rewrite_candidate_batch_for_m2993(m2990.build_fitting_batch(source))
    guard_batch = build_guard_batch(source, candidate_weight_sum=float(np.sum(candidate_batch.weights)))
    combined_batch = build_combined_batch(candidate_batch, guard_batch)
    source_ready = source_preconditions_pass(source)
    model = m2990.fit_linear_residual(combined_batch) if source_ready and combined_batch.contracts_pass else m2990.zero_model()
    fitting_executed = bool(source_ready and combined_batch.contracts_pass and model.fitted)

    candidate_zero = np.zeros_like(candidate_batch.targets, dtype=np.float32)
    guard_zero = np.zeros_like(guard_batch.targets, dtype=np.float32)
    candidate_pred = (
        m2990.predict_residual(model, candidate_batch.observations) if fitting_executed else candidate_zero
    )
    guard_pred = m2990.predict_residual(model, guard_batch.observations) if fitting_executed else guard_zero
    loss_rows = build_guard_constrained_loss_trace_rows(
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        candidate_predictions_before=candidate_zero,
        guard_predictions_before=guard_zero,
        candidate_predictions_after=candidate_pred,
        guard_predictions_after=guard_pred,
        fitting_executed=fitting_executed,
        m2990_guard_abs_max=m2990_guard_abs_max(source),
    )

    if fitting_executed:
        write_candidate_artifact(paths["candidate_residual_head_artifact"], model)

    success_rows = build_success_guard_loss_rows(
        source,
        model=model,
        fitting_executed=fitting_executed,
        m2990_abs_max=m2990_guard_abs_max(source),
    )
    stale_rows = _rewrite_claim_rows(
        m2990.build_stale_exclusion_audit_rows(source),
        id_prefix_from="m2990",
        id_prefix_to="m2993",
    )
    actor_rows = _rewrite_claim_rows(
        m2990.build_actor_input_exclusion_rows(),
        id_prefix_from="m2990",
        id_prefix_to="m2993",
    )
    side_effect_rows = _rewrite_claim_rows(
        m2990.build_checkpoint_side_effect_guard_rows(),
        id_prefix_from="m2990",
        id_prefix_to="m2993",
    )

    write_csv_rows(paths["fitting_dataset_rows"], candidate_batch.rows, fieldnames=m2990.FITTING_DATASET_FIELDNAMES)
    write_csv_rows(paths["guard_constrained_loss_trace_rows"], loss_rows, fieldnames=GUARD_CONSTRAINED_LOSS_FIELDNAMES)
    write_csv_rows(paths["success_guard_loss_rows"], success_rows, fieldnames=SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["stale_exclusion_audit_rows"], stale_rows, fieldnames=m2990.STALE_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["actor_input_exclusion_rows"], actor_rows, fieldnames=m2990.ACTOR_INPUT_EXCLUSION_FIELDNAMES)
    write_csv_rows(paths["checkpoint_side_effect_guard_rows"], side_effect_rows, fieldnames=m2990.SIDE_EFFECT_FIELDNAMES)

    write_follow_up_manifest(
        Path(follow_up_manifest),
        summary_path=paths["summary"],
        doc_path=paths["doc"],
        output_dir=output,
    )
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=False,
    )
    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=required_artifacts_present,
    )
    write_run_state(
        paths["run_state"],
        {
            "fitting_dataset_row_count": len(candidate_batch.rows),
            "fitting_sample_count": int(candidate_batch.observations.shape[0]),
            "success_guard_loss_row_count": len(success_rows),
            "success_guard_sample_count": int(guard_batch.observations.shape[0]),
            "success_guard_predicted_residual_abs_max": summary["success_guard_predicted_residual_abs_max"],
            "guard_constrained_fitting_run": fitting_executed,
            "validation_run": False,
            "checkpoint_mutated": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    summary = _write_summary_doc_and_gates(
        paths=paths,
        output_dir=output,
        source=source,
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        fitting_executed=fitting_executed,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
        required_artifacts_present=all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS),
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "fitting_dataset_rows": output_dir / "fitting_dataset_rows.csv",
        "guard_constrained_loss_trace_rows": output_dir / "guard_constrained_loss_trace_rows.csv",
        "success_guard_loss_rows": output_dir / "success_guard_loss_rows.csv",
        "stale_exclusion_audit_rows": output_dir / "stale_exclusion_audit_rows.csv",
        "actor_input_exclusion_rows": output_dir / "actor_input_exclusion_rows.csv",
        "checkpoint_side_effect_guard_rows": output_dir / "checkpoint_side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "candidate_residual_head_artifact": output_dir / "candidate_residual_head_artifact.npz",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    *,
    m2987_dir: Path,
    m2988_audit: Path,
    m2989_design: Path,
    m2991_audit: Path,
    m2992_synthesis: Path,
    m2983_dir: Path,
    m2990_dir: Path,
) -> dict[str, Any]:
    source = m2990.load_source_artifacts(
        m2987_dir=m2987_dir,
        m2988_audit=m2988_audit,
        m2989_design=m2989_design,
        m2983_dir=m2983_dir,
    )
    m2990_summary_path = m2990_dir / "summary.json"
    source["paths"] = dict(source["paths"])
    source["paths"].update(
        {
            "m2990_summary": m2990_summary_path,
            "m2991_audit": m2991_audit,
            "m2992_synthesis": m2992_synthesis,
        }
    )
    source["source_exists"] = dict(source["source_exists"])
    source["source_exists"].update(
        {
            "m2990_summary": m2990_summary_path.exists(),
            "m2991_audit": m2991_audit.exists(),
            "m2992_synthesis": m2992_synthesis.exists(),
        }
    )
    source["m2990_summary"] = read_json(m2990_summary_path) if m2990_summary_path.exists() else {}
    source["m2991_audit_text"] = m2991_audit.read_text(encoding="utf-8") if m2991_audit.exists() else ""
    source["m2992_synthesis_text"] = (
        m2992_synthesis.read_text(encoding="utf-8") if m2992_synthesis.exists() else ""
    )
    return source


def build_guard_batch(source: dict[str, Any], *, candidate_weight_sum: float) -> GuardBatch:
    success_rows_by_id = {
        row["success_identity_zero_target_guard_row_id"]: row
        for row in source["m2983_success_identity_zero_target_guard_rows"]
    }
    observations: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    rows: list[dict[str, Any]] = []
    total_guard_steps = 0
    for binding in source["success_identity_zero_guard_binding_rows"]:
        success_id = binding.get("success_identity_zero_target_guard_row_id", "")
        source_row = success_rows_by_id.get(success_id, {})
        observation = m2990._load_observation_trace(Path(source_row.get("raw_trace_path", "")))
        total_guard_steps += int(observation.shape[0])

    guard_weight = (candidate_weight_sum / max(float(total_guard_steps), 1.0)) * GUARD_WEIGHT_MULTIPLIER
    for index, binding in enumerate(source["success_identity_zero_guard_binding_rows"], start=1):
        success_id = binding.get("success_identity_zero_target_guard_row_id", "")
        source_row = success_rows_by_id.get(success_id, {})
        raw_trace_path = Path(source_row.get("raw_trace_path", ""))
        target_tensor_path = Path(binding.get("target_tensor_path", source_row.get("target_tensor_path", "")))
        observation = m2990._load_observation_trace(raw_trace_path)
        target_zero = float(binding.get("target_action_delta_abs_max", 1.0)) == 0.0
        zero_guard = bool_value(binding.get("zero_target_guard", False)) and not bool_value(
            binding.get("positive_residual_target", False)
        )
        not_candidate_denominator = not bool_value(
            binding.get("future_fitting_denominator_allowed_after_audit", True)
        )
        guard_allowed = bool_value(binding.get("guard_denominator_allowed", False))
        status_pass = (
            bool_value(binding.get("status_pass", False))
            and observation.shape[0] > 0
            and target_zero
            and zero_guard
            and not_candidate_denominator
            and guard_allowed
        )
        if status_pass:
            observations.append(observation)
            targets.append(np.zeros((observation.shape[0], ACTION_DIM), dtype=np.float32))
        rows.append(
            {
                "success_guard_loss_id": f"m2993-success-guard-training-{index:04d}",
                "success_identity_zero_guard_binding_id": binding.get("success_identity_zero_guard_binding_id", ""),
                "success_identity_zero_target_guard_row_id": success_id,
                "raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(target_tensor_path),
                "zero_target_guard": zero_guard,
                "fitting_denominator_used": False,
                "target_action_delta_abs_max": float(binding.get("target_action_delta_abs_max", 0.0)),
                "predicted_residual_abs_max": 0.0,
                "predicted_residual_mse": 0.0,
                "status_pass": status_pass,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    if observations:
        observation_array = np.concatenate(observations, axis=0).astype(np.float32)
        target_array = np.concatenate(targets, axis=0).astype(np.float32)
        weight_array = np.full((observation_array.shape[0],), guard_weight, dtype=np.float32)
    else:
        observation_array = np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32)
        target_array = np.zeros((0, ACTION_DIM), dtype=np.float32)
        weight_array = np.zeros((0,), dtype=np.float32)
    contracts_pass = (
        len(rows) == EXPECTED_SUCCESS_GUARD_COUNT
        and all(bool_value(row["status_pass"]) for row in rows)
        and observation_array.shape[0] > 0
    )
    return GuardBatch(
        observations=observation_array,
        targets=target_array,
        weights=weight_array,
        rows=rows,
        contracts_pass=contracts_pass,
    )


def build_combined_batch(candidate_batch: m2990.FittingBatch, guard_batch: GuardBatch) -> m2990.FittingBatch:
    if candidate_batch.observations.shape[0] == 0 or guard_batch.observations.shape[0] == 0:
        return m2990.FittingBatch(
            observations=np.zeros((0, P0_OBSERVATION_DIM), dtype=np.float32),
            targets=np.zeros((0, ACTION_DIM), dtype=np.float32),
            weights=np.zeros((0,), dtype=np.float32),
            rows=candidate_batch.rows,
            contracts_pass=False,
        )
    return m2990.FittingBatch(
        observations=np.concatenate([candidate_batch.observations, guard_batch.observations], axis=0),
        targets=np.concatenate([candidate_batch.targets, guard_batch.targets], axis=0),
        weights=np.concatenate([candidate_batch.weights, guard_batch.weights], axis=0),
        rows=candidate_batch.rows,
        contracts_pass=bool(candidate_batch.contracts_pass and guard_batch.contracts_pass),
    )


def rewrite_candidate_batch_for_m2993(batch: m2990.FittingBatch) -> m2990.FittingBatch:
    return m2990.FittingBatch(
        observations=batch.observations,
        targets=batch.targets,
        weights=batch.weights,
        rows=_rewrite_claim_rows(batch.rows, id_prefix_from="m2990", id_prefix_to="m2993"),
        contracts_pass=batch.contracts_pass,
    )


def source_preconditions_pass(source: dict[str, Any]) -> bool:
    m2987_summary = source["m2987_summary"]
    return (
        all(source["source_exists"].values())
        and bool_value(m2987_summary.get("status_pass"))
        and bool_value(m2987_summary.get("gate_matrix_pass"))
        and "accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design"
        in source["m2988_audit_text"]
        and "admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion"
        in source["m2989_design_text"]
        and "accept_m2990_artifact_claim_safe_reject_direct_validation_route_to_m2992_success_identity_guard_repair_branch_synthesis"
        in source["m2991_audit_text"]
        and "continue_to_m2993_success_identity_guard_constrained_fitting_preflight"
        in source["m2992_synthesis_text"]
    )


def m2990_guard_abs_max(source: dict[str, Any]) -> float:
    value = source.get("m2990_summary", {}).get("success_guard_predicted_residual_abs_max")
    try:
        return float(value)
    except (TypeError, ValueError):
        return M2990_EXPECTED_GUARD_ABS_MAX


def _combined_weighted_mse(
    candidate_prediction: np.ndarray,
    candidate_target: np.ndarray,
    candidate_weight: np.ndarray,
    guard_prediction: np.ndarray,
    guard_target: np.ndarray,
    guard_weight: np.ndarray,
) -> float:
    cand = m2990._weighted_metrics(candidate_prediction, candidate_target, candidate_weight)
    guard = m2990._weighted_metrics(guard_prediction, guard_target, guard_weight)
    candidate_denom = max(float(np.sum(candidate_weight)) * float(ACTION_DIM), m2990.EPS)
    guard_denom = max(float(np.sum(guard_weight)) * float(ACTION_DIM), m2990.EPS)
    return float((cand["weighted_mse"] * candidate_denom + guard["weighted_mse"] * guard_denom) / (candidate_denom + guard_denom))


def build_guard_constrained_loss_trace_rows(
    *,
    candidate_batch: m2990.FittingBatch,
    guard_batch: GuardBatch,
    candidate_predictions_before: np.ndarray,
    guard_predictions_before: np.ndarray,
    candidate_predictions_after: np.ndarray,
    guard_predictions_after: np.ndarray,
    fitting_executed: bool,
    m2990_guard_abs_max: float,
) -> list[dict[str, Any]]:
    before_candidate = m2990._weighted_metrics(candidate_predictions_before, candidate_batch.targets, candidate_batch.weights)
    after_candidate = m2990._weighted_metrics(candidate_predictions_after, candidate_batch.targets, candidate_batch.weights)
    before_guard = m2990._weighted_metrics(guard_predictions_before, guard_batch.targets, guard_batch.weights)
    after_guard = m2990._weighted_metrics(guard_predictions_after, guard_batch.targets, guard_batch.weights)
    before_combined = _combined_weighted_mse(
        candidate_predictions_before,
        candidate_batch.targets,
        candidate_batch.weights,
        guard_predictions_before,
        guard_batch.targets,
        guard_batch.weights,
    )
    after_combined = _combined_weighted_mse(
        candidate_predictions_after,
        candidate_batch.targets,
        candidate_batch.weights,
        guard_predictions_after,
        guard_batch.targets,
        guard_batch.weights,
    )
    after_pass = (
        fitting_executed
        and np.isfinite(after_candidate["weighted_mse"])
        and after_candidate["weighted_mse"] <= before_candidate["weighted_mse"] + 1.0e-9
        and after_guard["residual_abs_max"] <= SUCCESS_GUARD_REQUIRED_ABS_MAX + 1.0e-9
        and after_guard["residual_abs_max"] < m2990_guard_abs_max
    )
    return [
        {
            "loss_trace_id": "m2993-loss-0001-zero-residual-baseline",
            "fit_stage": "zero_residual_baseline",
            "step": 0,
            "candidate_sample_count": int(candidate_batch.observations.shape[0]),
            "candidate_weight_sum": float(np.sum(candidate_batch.weights)),
            "success_guard_sample_count": int(guard_batch.observations.shape[0]),
            "success_guard_weight_sum": float(np.sum(guard_batch.weights)),
            "candidate_weighted_mse": before_candidate["weighted_mse"],
            "candidate_weighted_l1": before_candidate["weighted_l1"],
            "success_guard_predicted_residual_abs_max": before_guard["residual_abs_max"],
            "success_guard_predicted_residual_mse": before_guard["weighted_mse"],
            "combined_weighted_mse": before_combined,
            "predicted_residual_abs_max": before_candidate["residual_abs_max"],
            "status_pass": candidate_batch.observations.shape[0] > 0 and guard_batch.observations.shape[0] > 0,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "loss_trace_id": "m2993-loss-0002-success-identity-guard-constrained-linear-residual",
            "fit_stage": "success_identity_guard_constrained_linear_residual",
            "step": 1,
            "candidate_sample_count": int(candidate_batch.observations.shape[0]),
            "candidate_weight_sum": float(np.sum(candidate_batch.weights)),
            "success_guard_sample_count": int(guard_batch.observations.shape[0]),
            "success_guard_weight_sum": float(np.sum(guard_batch.weights)),
            "candidate_weighted_mse": after_candidate["weighted_mse"],
            "candidate_weighted_l1": after_candidate["weighted_l1"],
            "success_guard_predicted_residual_abs_max": after_guard["residual_abs_max"],
            "success_guard_predicted_residual_mse": after_guard["weighted_mse"],
            "combined_weighted_mse": after_combined,
            "predicted_residual_abs_max": after_candidate["residual_abs_max"],
            "status_pass": after_pass,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]


def build_success_guard_loss_rows(
    source: dict[str, Any],
    *,
    model: m2990.FittedResidual,
    fitting_executed: bool,
    m2990_abs_max: float,
) -> list[dict[str, Any]]:
    rows = m2990.build_success_guard_loss_rows(source, model=model, fitting_executed=fitting_executed)
    rewritten: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        predicted_abs = float(row.get("predicted_residual_abs_max", 0.0))
        satisfied = predicted_abs <= SUCCESS_GUARD_REQUIRED_ABS_MAX + 1.0e-9
        improved = predicted_abs < m2990_abs_max
        new_row = dict(row)
        new_row["success_guard_loss_id"] = f"m2993-success-guard-loss-{index:04d}"
        new_row["status_pass"] = (
            fitting_executed
            and bool_value(row.get("status_pass", False))
            and satisfied
            and improved
        )
        new_row["claim_boundary"] = CLAIM_SCOPE
        new_row["guard_penalty_or_constraint_used"] = True
        new_row["m2990_predicted_residual_abs_max"] = m2990_abs_max
        new_row["improved_from_m2990"] = improved
        new_row["zero_residual_guard_satisfied"] = satisfied
        rewritten.append(new_row)
    return rewritten


def _rewrite_claim_rows(rows: list[dict[str, Any]], *, id_prefix_from: str, id_prefix_to: str) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for row in rows:
        new_row = dict(row)
        for key, value in list(new_row.items()):
            if key.endswith("_id") and isinstance(value, str):
                new_row[key] = value.replace(id_prefix_from, id_prefix_to, 1)
        new_row["claim_boundary"] = CLAIM_SCOPE
        rewritten.append(new_row)
    return rewritten


def write_candidate_artifact(path: Path, model: m2990.FittedResidual) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        linear_weight=model.weight.astype(np.float32),
        linear_bias=model.bias.astype(np.float32),
        residual_limit=np.asarray([model.residual_limit], dtype=np.float32),
        guard_weight_multiplier=np.asarray([GUARD_WEIGHT_MULTIPLIER], dtype=np.float32),
        success_guard_required_abs_max=np.asarray([SUCCESS_GUARD_REQUIRED_ABS_MAX], dtype=np.float32),
        observation_dim=np.asarray([P0_OBSERVATION_DIM], dtype=np.int64),
        action_dim=np.asarray([ACTION_DIM], dtype=np.int64),
        claim_scope=np.asarray([CLAIM_SCOPE]),
    )


def build_claim_boundary_rows(*, fitting_executed: bool, follow_up_manifest_registered: bool) -> list[dict[str, Any]]:
    allowed = [
        ("guard_constrained_offline_fitting_artifact", "artifact", fitting_executed, "M2993 constrained fitting artifact"),
        ("guard_constrained_loss_trace", "artifact", fitting_executed, "M2993 constrained loss trace rows"),
        ("success_identity_guard_accounting", "guardrail", fitting_executed, "M2993 success guard rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2994 audit manifest"),
    ]
    blocked = [
        ("target_quality_validated", "target_quality", "future target-quality audit"),
        ("validation_result", "validation", "future validation route"),
        ("ranking_or_winner", "ranking", "future audited comparison route"),
        ("checkpoint_mutation", "implementation", "future audited implementation admission"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_evidence", "paper", "future audited evidence matrix"),
        ("current_sim_verdict", "validation", "future current-sim verdict route"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation route"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [_claim_row(claim_id, family, True, bool(made), evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(_claim_row(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def _claim_row(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2993-{claim_id}",
        "claim_family": family,
        "allowed_in_m2993": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    candidate_batch: m2990.FittingBatch,
    guard_batch: GuardBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    fitting_executed: bool,
    candidate_artifact_exists: bool,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m2987_summary = source["m2987_summary"]
    final_loss = loss_rows[-1] if loss_rows else {}
    initial_loss = loss_rows[0] if loss_rows else {}
    m2993_guard_abs = float(final_loss.get("success_guard_predicted_residual_abs_max", float("inf")))
    m2990_guard_abs = m2990_guard_abs_max(source)
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        ("m2987_status_pass", "lineage", bool_value(m2987_summary.get("status_pass")), True, "lineage_invalid"),
        (
            "m2987_gate_matrix_pass",
            "lineage",
            bool_value(m2987_summary.get("gate_matrix_pass")),
            True,
            "lineage_invalid",
        ),
        (
            "m2988_accepts_m2987",
            "lineage",
            "accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design"
            in source["m2988_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2989_admits_m2990",
            "lineage",
            "admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion"
            in source["m2989_design_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2991_rejects_direct_validation",
            "lineage",
            "accept_m2990_artifact_claim_safe_reject_direct_validation_route_to_m2992_success_identity_guard_repair_branch_synthesis"
            in source["m2991_audit_text"],
            True,
            "lineage_invalid",
        ),
        (
            "m2992_selects_m2993",
            "lineage",
            "continue_to_m2993_success_identity_guard_constrained_fitting_preflight"
            in source["m2992_synthesis_text"],
            True,
            "lineage_invalid",
        ),
        ("candidate_row_count", "artifact", len(candidate_batch.rows), EXPECTED_CANDIDATE_COUNT, "metric_artifact"),
        ("candidate_contracts_pass", "contract", candidate_batch.contracts_pass, True, "contract_violation"),
        (
            "candidate_dataset_rows_pass",
            "contract",
            all(bool_value(row["status_pass"]) for row in candidate_batch.rows),
            True,
            "contract_violation",
        ),
        (
            "candidate_sample_count_positive",
            "artifact",
            int(candidate_batch.observations.shape[0]) > 0,
            True,
            "metric_artifact",
        ),
        (
            "success_guard_count",
            "guardrail",
            len(success_rows),
            EXPECTED_SUCCESS_GUARD_COUNT,
            "metric_artifact",
        ),
        (
            "success_guard_training_rows_pass",
            "guardrail",
            guard_batch.contracts_pass,
            True,
            "contract_violation",
        ),
        (
            "success_guard_sample_count_positive",
            "guardrail",
            int(guard_batch.observations.shape[0]) > 0,
            True,
            "metric_artifact",
        ),
        ("guard_constrained_fitting_executed", "execution", fitting_executed, True, "training_instability"),
        ("candidate_artifact_written", "artifact", candidate_artifact_exists, True, "metric_artifact"),
        (
            "candidate_loss_finite",
            "artifact",
            np.isfinite(float(final_loss.get("candidate_weighted_mse", float("inf")))),
            True,
            "training_instability",
        ),
        (
            "candidate_loss_not_worse_than_zero",
            "artifact",
            float(final_loss.get("candidate_weighted_mse", float("inf")))
            <= float(initial_loss.get("candidate_weighted_mse", -float("inf"))) + 1.0e-9,
            True,
            "training_instability",
        ),
        (
            "success_guard_improves_from_m2990",
            "guardrail",
            m2993_guard_abs < m2990_guard_abs,
            True,
            "behavior_regression",
        ),
        (
            "success_guard_zero_residual_satisfied",
            "guardrail",
            m2993_guard_abs <= SUCCESS_GUARD_REQUIRED_ABS_MAX + 1.0e-9,
            True,
            "behavior_regression",
        ),
        (
            "success_guard_rows_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in success_rows),
            True,
            "contract_violation",
        ),
        ("stale_exclusion_count", "guardrail", len(stale_rows), EXPECTED_STALE_EXCLUSION_COUNT, "metric_artifact"),
        (
            "stale_exclusion_rows_pass",
            "guardrail",
            all(bool_value(row["status_pass"]) for row in stale_rows),
            True,
            "contract_violation",
        ),
        (
            "actor_input_exclusions_pass",
            "actor_contract",
            all(not bool_value(row["actor_visible"]) and bool_value(row["status_pass"]) for row in actor_rows),
            True,
            "contract_violation",
        ),
        (
            "checkpoint_side_effect_guards_pass",
            "side_effect_guard",
            all(bool_value(row["status_pass"]) for row in side_effect_rows),
            True,
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            all(bool_value(row["status_pass"]) for row in claim_rows),
            True,
            "proof_washout",
        ),
        (
            "target_quality_validated_false",
            "claim_boundary",
            any(row["claim_id"] == "m2993-target_quality_validated" and not bool_value(row["claim_made"]) for row in claim_rows),
            True,
            "proof_washout",
        ),
        ("follow_up_audit_registered", "follow_up", source["follow_up_manifest_exists"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
    ]
    return [
        {
            "gate_id": f"m2993-gate-{index:04d}-{gate_id}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (gate_id, family, observed, expected, failure_type) in enumerate(gates, start=1)
    ]


def _write_summary_doc_and_gates(
    *,
    paths: dict[str, Path],
    output_dir: Path,
    source: dict[str, Any],
    candidate_batch: m2990.FittingBatch,
    guard_batch: GuardBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    fitting_executed: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
    required_artifacts_present: bool,
) -> dict[str, Any]:
    claim_rows = build_claim_boundary_rows(
        fitting_executed=fitting_executed,
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        fitting_executed=fitting_executed,
        candidate_artifact_exists=paths["candidate_residual_head_artifact"].exists(),
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=m2990.GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        paths=paths,
        source=source,
        candidate_batch=candidate_batch,
        guard_batch=guard_batch,
        loss_rows=loss_rows,
        success_rows=success_rows,
        stale_rows=stale_rows,
        actor_rows=actor_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        fitting_executed=fitting_executed,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=follow_up_manifest,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    candidate_batch: m2990.FittingBatch,
    guard_batch: GuardBatch,
    loss_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    stale_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    fitting_executed: bool,
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool_value(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    initial_loss = loss_rows[0] if loss_rows else {}
    final_loss = loss_rows[-1] if loss_rows else {}
    m2990_abs = m2990_guard_abs_max(source)
    m2993_abs = float(final_loss.get("success_guard_predicted_residual_abs_max", 0.0))
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "m2987_status_pass": bool_value(source["m2987_summary"].get("status_pass")),
        "m2987_gate_matrix_pass": bool_value(source["m2987_summary"].get("gate_matrix_pass")),
        "m2990_success_guard_predicted_residual_abs_max": m2990_abs,
        "success_guard_required_abs_max": SUCCESS_GUARD_REQUIRED_ABS_MAX,
        "guard_weight_multiplier": GUARD_WEIGHT_MULTIPLIER,
        "fitting_dataset_row_count": len(candidate_batch.rows),
        "fitting_sample_count": int(candidate_batch.observations.shape[0]),
        "fitting_weight_sum": float(np.sum(candidate_batch.weights)),
        "success_guard_sample_count": int(guard_batch.observations.shape[0]),
        "success_guard_weight_sum": float(np.sum(guard_batch.weights)),
        "initial_candidate_weighted_mse": float(initial_loss.get("candidate_weighted_mse", float("inf"))),
        "final_candidate_weighted_mse": float(final_loss.get("candidate_weighted_mse", float("inf"))),
        "final_candidate_weighted_l1": float(final_loss.get("candidate_weighted_l1", float("inf"))),
        "final_combined_weighted_mse": float(final_loss.get("combined_weighted_mse", float("inf"))),
        "candidate_loss_improved_or_equal": (
            float(final_loss.get("candidate_weighted_mse", float("inf")))
            <= float(initial_loss.get("candidate_weighted_mse", -float("inf"))) + 1.0e-9
        ),
        "candidate_residual_head_artifact": str(paths["candidate_residual_head_artifact"]),
        "candidate_residual_head_artifact_exists": paths["candidate_residual_head_artifact"].exists(),
        "success_guard_loss_row_count": len(success_rows),
        "success_guard_predicted_residual_abs_max": m2993_abs,
        "success_guard_predicted_residual_mse": float(final_loss.get("success_guard_predicted_residual_mse", 0.0)),
        "success_guard_improved_from_m2990": m2993_abs < m2990_abs,
        "success_guard_zero_residual_satisfied": m2993_abs <= SUCCESS_GUARD_REQUIRED_ABS_MAX + 1.0e-9,
        "stale_exclusion_audit_row_count": len(stale_rows),
        "actor_input_exclusion_row_count": len(actor_rows),
        "checkpoint_side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "candidate_target_tensor_row_count": len(candidate_batch.rows),
        "success_identity_zero_target_guard_row_count": len(success_rows),
        "stale_guardrail_exclusion_row_count": len(stale_rows),
        "target_quality_validated": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "actor_contract_shape_72_action_3": True,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "guard_constrained_offline_fitting_run": fitting_executed,
        "bounded_offline_fitting_run": fitting_executed,
        "residual_fitting_run": fitting_executed,
        "training_run": fitting_executed,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "next_blocker": next_blocker,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
        "result_class": (
            "engineering_controller_route_a_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight_fail"
        ),
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return f"""# M2993 Engineering Controller Route A Actor-Head Delta Nonzero Residual Success-Identity Guard-Constrained Fitting Preflight

## Summary

- status pass: `{summary["status_pass"]}`
- gate matrix pass: `{summary["gate_matrix_pass"]}`
- required artifacts present: `{summary["required_artifacts_present"]}`
- fitting dataset rows: `{summary["fitting_dataset_row_count"]}`
- fitting samples: `{summary["fitting_sample_count"]}`
- initial candidate weighted MSE: `{summary["initial_candidate_weighted_mse"]}`
- final candidate weighted MSE: `{summary["final_candidate_weighted_mse"]}`
- M2990 success guard predicted residual abs max: `{summary["m2990_success_guard_predicted_residual_abs_max"]}`
- M2993 success guard predicted residual abs max: `{summary["success_guard_predicted_residual_abs_max"]}`
- success guard required abs max: `{summary["success_guard_required_abs_max"]}`
- success guard improved from M2990: `{summary["success_guard_improved_from_m2990"]}`
- success guard zero residual satisfied: `{summary["success_guard_zero_residual_satisfied"]}`
- stale exclusion rows: `{summary["stale_exclusion_audit_row_count"]}`
- target quality validated: `{summary["target_quality_validated"]}`
- guard-constrained offline fitting run: `{summary["guard_constrained_offline_fitting_run"]}`
- validation run: `{summary["validation_run"]}`
- ranking run: `{summary["ranking_run"]}`
- checkpoint mutated: `{summary["checkpoint_mutated"]}`
- next blocker: `{summary["next_blocker"]}`
- follow-up manifest: `{summary["follow_up_manifest"]}`

## Boundary

M2993 performs guard-constrained offline fitting only. It writes a candidate
linear residual-head artifact and constrained loss trace for M2994 audit while
preserving actor observation/action `{summary["observation_shape"]}/{summary["action_shape"]}`.
Candidate rows remain the fitting denominator; success identity rows are
zero-residual guard penalty or constraint rows; stale fixed-source guardrails
remain excluded.

M2993 does not run an environment, validate a policy, rank candidates, select a
winner, mutate or promote checkpoints, or claim target quality, repair success,
driver performance, paper evidence, current-sim verdict, high-fidelity
validation, finite-window-vs-GRU evidence, full-driver completion, or self-ID
evidence.
"""


def write_follow_up_manifest(path: Path, *, summary_path: Path, doc_path: Path, output_dir: Path) -> None:
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
                "A bounded result audit can accept or reject M2993 guard-constrained offline fitting "
                "artifacts before any validation ranking promotion repair-success performance or self-ID claim."
            ),
            "success_criteria": [
                f"docs/{manifest_id}.md exists",
                "M2994 audits M2993 guard-constrained fitting artifacts",
                "M2994 decides whether constrained fitting artifacts are claim-safe and whether the linear residual family remains viable",
                "M2994 selects exactly one next route or stop state",
                "no validation ranking promotion performance paper high-fidelity finite-window-vs-GRU or self-ID claim is made",
            ],
            "failure_criteria": [
                "M2994 hides missing M2993 fitting artifacts",
                "M2994 treats constrained fitting loss or guard improvement as target-quality validation repair success or performance evidence",
                "M2994 changes actor input or action contract",
                "M2994 leaves next route ambiguous",
            ],
            "commands": [{"name": "result_audit_doc", "command": "true"}],
            "required_artifacts": [{"path": f"docs/{manifest_id}.md", "type": "markdown"}],
            "baseline_checkpoints": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "baseline_artifacts": [
                str(summary_path),
                str(output_dir / "fitting_dataset_rows.csv"),
                str(output_dir / "guard_constrained_loss_trace_rows.csv"),
                str(output_dir / "success_guard_loss_rows.csv"),
                str(output_dir / "stale_exclusion_audit_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(output_dir / "candidate_residual_head_artifact.npz"),
                str(doc_path),
            ],
            "decision_rule": (
                "Pass only if M2994 audits M2993 guard-constrained fitting artifacts and selects one next "
                "route or stop state while preserving actor guard stale exclusion target-quality checkpoint and claim boundaries."
            ),
            "gate_tier": "process",
            "promotion_decision": "pending",
            "failure_types": [
                "contract_violation",
                "lineage_invalid",
                "metric_artifact",
                "training_instability",
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
                    str(summary_path),
                    str(output_dir / "success_guard_loss_rows.csv"),
                    str(output_dir / "gate_matrix.csv"),
                    str(doc_path),
                ],
                "parent_config": [
                    "experiments/manifests/m2993-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-preflight.json"
                ],
                "parent_objective": [
                    "audit guard-constrained offline residual fitting artifacts before any validation or promotion route"
                ],
                "derived_from": [MILESTONE_ID],
                "blocked_by": [
                    "M2993 may produce guard-constrained fitting artifacts but cannot establish target quality repair success or performance"
                ],
                "supersedes": ["direct validation or promotion immediately after M2993 without result audit"],
                "invalidates": [],
            },
            "review_artifact": f"docs/reviews/{manifest_id}.md",
            "scoreboard_checkpoint": f"docs/{manifest_id}.md",
            "public_gates": [
                "M2994 must audit M2993 fitting dataset guard-constrained loss trace success guard stale exclusion artifact and gate rows",
                "M2994 must preserve target_quality_validated false unless a later target-quality audit is explicitly admitted",
                "M2994 must preserve actor 72/action 3 no target labels or provenance actor inputs",
                "M2994 must not validate rank promote mutate checkpoints or claim performance paper high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            ],
            "private_holdout_policy": "not_used",
            "forbidden_shortcuts": [
                "do not run environment validation ranking winner selection private holdout or performance measurement",
                "do not mutate save replace or promote checkpoints",
                "do not change actor input or action contract",
                "do not convert fitting loss or success-guard improvement into target-quality validation repair-success performance paper high-fidelity finite-window-vs-GRU or self-ID claims",
            ],
            "workflow_synthesis": {
                "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
                "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_result_audit",
                "evidence_increment": "audits M2993 guard-constrained offline fitting artifacts before any further route",
                "claim_scope": "Result audit only; no validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
                "stop_condition": [
                    "stop if M2993 fitting artifacts are incomplete or claim-unsafe",
                    "stop if actor target guard stale exclusion or side-effect boundaries are weakened",
                    "stop if the result would be interpreted as target-quality validation performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID evidence",
                ],
                "fallback_plan": [
                    "route to artifact repair if fitting rows are incomplete",
                    "route to architecture repair synthesis if constrained fitting cannot preserve success-zero semantics",
                    "route to validation design only after accepting constrained fitting as claim-safe and still non-deployment evidence",
                    "route to synthesis pivot or stop if fitting cannot preserve boundaries",
                ],
                "synthesis_cadence": 10,
                "synthesis_trigger": "M2993 produces guard-constrained offline fitting artifacts",
                "synthesis_decision": "not_applicable",
            },
            "training_stage": {
                "stage": "process",
                "stage_objective": "Audit guard-constrained fitting artifacts before validation or promotion",
                "admission_evidence": [
                    "M2993 is expected to write fitting dataset constrained loss trace success guard stale exclusion artifact and gate rows",
                    "M2993 must preserve target_quality_validated false and no validation/ranking/promotion claims",
                ],
                "blocked_shortcuts": [
                    "no environment validation ranking promotion or success-rate verdict",
                    "no checkpoint mutation save selection or promotion",
                    "no target labels target provenance objective admission source route verdict or paper actor inputs",
                    "no driver-performance current-sim high-fidelity full ideal driver finite-window-vs-GRU paper or self-ID claim",
                ],
                "allowed_updates": [
                    f"docs/{manifest_id}.md",
                    f"docs/reviews/{manifest_id}.md",
                    "M2994 status queue scoreboard research log and review",
                    "one follow-up manifest only if M2994 selects exactly one next route",
                ],
                "next_stage_criteria": [
                    "M2994 accepts or rejects M2993 artifacts",
                    "M2994 chooses one next route or stop state",
                    "actor guard and claim boundaries remain unchanged",
                ],
            },
            "self_id_evidence_discipline": {
                "claim_level": "not_applicable",
                "current_frame_substitution_risk": "M2994 audits fitting artifacts and cannot infer history necessity or self-ID.",
                "history_necessity_tests": [
                    "None in M2994; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
                ],
                "temporal_evidence_window": "M2983-M2993 Route A actor-head delta target tensor fitting-contract constrained fitting chain.",
                "negative_result_policy": "Preserve fitting blockers rather than weakening self-ID proof gates.",
                "allowed_claims": [
                    "M2993 artifact completeness after audit",
                    "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
                ],
            },
            "local_search_guard": {
                "actual_progress_type": "result_audit",
                "process_overhead": "medium",
                "local_search_risk": "medium",
                "same_failure_repeat_count": 0,
                "same_public_gate_repair_count": 0,
                "evidence_expansion": "audits newly produced guard-constrained fitting artifacts",
                "paper_verdict_delta": "no paper verdict; may enable later target-quality or validation design only",
                "must_synthesize_if": [
                    "M2994 cannot select exactly one next route",
                    "M2994 would claim performance validation paper current-sim high-fidelity finite-window-vs-GRU or self-ID evidence",
                ],
            },
            "next_blocker": manifest_id,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2987-dir", type=Path, default=DEFAULT_M2987_DIR)
    parser.add_argument("--m2988-audit", type=Path, default=DEFAULT_M2988_AUDIT)
    parser.add_argument("--m2989-design", type=Path, default=DEFAULT_M2989_DESIGN)
    parser.add_argument("--m2991-audit", type=Path, default=DEFAULT_M2991_AUDIT)
    parser.add_argument("--m2992-synthesis", type=Path, default=DEFAULT_M2992_SYNTHESIS)
    parser.add_argument("--m2983-dir", type=Path, default=DEFAULT_M2983_DIR)
    parser.add_argument("--m2990-dir", type=Path, default=DEFAULT_M2990_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_success_identity_guard_constrained_fitting_preflight(
        m2987_dir=args.m2987_dir,
        m2988_audit=args.m2988_audit,
        m2989_design=args.m2989_design,
        m2991_audit=args.m2991_audit,
        m2992_synthesis=args.m2992_synthesis,
        m2983_dir=args.m2983_dir,
        m2990_dir=args.m2990_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )


if __name__ == "__main__":
    main()
