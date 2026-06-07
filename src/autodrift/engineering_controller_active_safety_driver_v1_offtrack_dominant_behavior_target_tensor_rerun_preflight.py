"""Materialize M3061 raw-trace-backed offtrack behavior target tensors.

M3061 consumes the M3060-accepted M3059 raw actor-view traces and converts them
into trainer-side numeric target tensor artifacts. It does not use the replayed
failed action trace as the corrected recovery target. Instead, it writes a
bounded recovery-window rule based only on actor-visible observation channels:
road-boundary center offset, body velocity, and yaw rate.

No fitting, rollout validation, ranking, promotion, high-fidelity evaluation,
finite-window-vs-GRU comparison, paper evidence, full-driver evaluation, or
self-ID test is run here.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3061-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-rerun-preflight"
)
NEXT_ID = (
    "m3062-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-rerun-result-audit"
)
M3060_ID = (
    "m3060-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-raw-trace-capture-result-audit"
)
M3059_ID = (
    "m3059-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-raw-trace-capture-preflight"
)
M3057_ID = (
    "m3057-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-materialization-preflight"
)
M3055_ID = (
    "m3055-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-fitting-contract-materialization-preflight"
)
M3053_ID = (
    "m3053-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-materialization-preflight"
)

DEFAULT_M3060_AUDIT = Path(f"docs/{M3060_ID}.md")
DEFAULT_M3059_DIR = Path(
    "runs/m3059_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_raw_trace_capture_preflight"
)
DEFAULT_M3057_DIR = Path(
    "runs/m3057_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_tensor_materialization_preflight"
)
DEFAULT_M3055_DIR = Path(
    "runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_fitting_contract_materialization_preflight"
)
DEFAULT_M3053_DIR = Path(
    "runs/m3053_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3061_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_tensor_rerun_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_TRACE_ROWS = 24
EXPECTED_LOSS_FAMILY_ROWS = 6
EXPECTED_ACTION_COMPONENTS = "steer;throttle;brake"
M3060_DECISION_MARKER = "continue_to_m3061_offtrack_dominant_behavior_target_tensor_rerun_preflight"
RECOVERY_WINDOW_MAX_STEPS = 32
TARGET_RULE_FAMILY = "actor_visible_road_center_terminal_recovery_window"
TARGET_RULE_INPUTS = "road_boundary_center_y;vx_body;vy_body;yaw_rate"

CLAIM_SCOPE = (
    "M3061 Active Safety Driver v1 offtrack-dominant behavior target tensor "
    "rerun preflight only; M3060 audit, M3059 raw actor-view traces, M3057 "
    "target tensor blocker rows, M3055 fitting contract rows, and M3053 "
    "behavior target-source/guard rows may be converted into trainer-side "
    "numeric target tensor artifacts and guards. No fitting, fitted policy "
    "quality, reset, step, rollout, local-action search, PPO, training, "
    "validation, ranking, winner selection, checkpoint mutation, checkpoint "
    "promotion, repair success, driver-performance verdict, current-sim "
    "verdict, high-fidelity validation, paper evidence, finite-window-vs-GRU "
    "evidence, full ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target tensor quality, fitted policy quality, repair success, validation "
    "result, driver-performance verdict, current-sim verdict, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, full "
    "ideal driver completion, or level3 self-identification"
)

TARGET_TENSOR_FIELDNAMES = [
    "target_tensor_row_id",
    "source_m3057_target_tensor_row_id",
    "raw_trace_index_row_id",
    "raw_trace_capture_plan_row_id",
    "source_offtrack_target_source_id",
    "measurement_episode_id",
    "baseline_measurement_row_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "eval_seed",
    "behavior_target_family",
    "intended_behavior",
    "output_semantics",
    "output_components",
    "actor_observation_shape",
    "actor_action_shape",
    "raw_actor_view_trace_path",
    "raw_actor_view_trace_available",
    "raw_trace_step_count",
    "raw_trace_termination_reason",
    "numeric_target_tensor_materialized",
    "target_tensor_path",
    "target_action_shape",
    "target_action_mask_shape",
    "target_loss_weight_shape",
    "target_action_abs_max",
    "target_action_min",
    "target_action_max",
    "target_loss_weight_sum",
    "masked_step_count",
    "recovery_window_start",
    "recovery_window_steps",
    "target_rule_family",
    "target_rule_inputs",
    "target_rule_uses_actor_visible_observation",
    "raw_action_trace_used_as_target",
    "raw_action_trace_preserved_for_audit",
    "trainer_side_only",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "local_action_search_run",
    "environment_reset_run",
    "environment_step_run",
    "fitting_run",
    "training_run",
    "validation_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_mutated",
    "checkpoint_promoted",
    "target_tensor_quality_claim_made",
    "status_pass",
    "blocker_family",
    "claim_boundary",
]
FILE_INDEX_FIELDNAMES = [
    "target_tensor_file_index_row_id",
    "target_tensor_row_id",
    "measurement_episode_id",
    "source_raw_trace_path",
    "target_tensor_path",
    "target_tensor_file_exists",
    "observation_shape",
    "raw_action_shape",
    "next_observation_shape",
    "reward_shape",
    "done_shape",
    "timeout_shape",
    "target_action_shape",
    "target_action_mask_shape",
    "target_loss_weight_shape",
    "observation_dtype",
    "target_action_dtype",
    "target_action_mask_dtype",
    "target_loss_weight_dtype",
    "all_tensors_finite",
    "masked_step_count",
    "target_loss_weight_sum",
    "target_action_abs_max",
    "raw_action_trace_used_as_target",
    "target_rule_family",
    "status_pass",
    "claim_boundary",
]
WEIGHT_FIELDNAMES = [
    "weight_row_id",
    "source_loss_family_id",
    "loss_family",
    "priority",
    "source_rows",
    "source_row_count",
    "weight_policy",
    "guard_dependency",
    "weight_spec_materialized",
    "numeric_weight_tensor_materialized",
    "numeric_weight_tensor_scope",
    "actor_visible",
    "status_pass",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "actor_guard_id",
    "guard_family",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
TARGET_VISIBILITY_FIELDNAMES = [
    "target_visibility_guard_id",
    "guard_family",
    "source_artifact",
    "observed",
    "expected",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
SIDE_EFFECT_FIELDNAMES = [
    "side_effect_guard_id",
    "side_effect",
    "scheduled_or_run",
    "expected",
    "status_pass",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3061",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _shape_text(value: np.ndarray) -> str:
    return "x".join(str(int(dim)) for dim in value.shape)


def _all_true(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    rows = list(rows)
    return bool(rows) and all(_bool(row.get(field)) for row in rows)


def _any_true(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    return any(_bool(row.get(field)) for row in rows)


def _all_false(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    return all(not _bool(row.get(field)) for row in rows)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    return read_json(path) if path.exists() else {}


def _read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def gate(name: str, family: str, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    status = observed == expected
    return {
        "gate_id": f"m3061-{name}",
        "gate_family": family,
        "status_pass": bool(status),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def actor_guard(field: str, observed: Any, expected: Any, *, actor_visible: bool = False) -> dict[str, Any]:
    return {
        "actor_guard_id": f"m3061-actor-contract-{field}",
        "guard_family": field,
        "observed": observed,
        "expected": expected,
        "status_pass": observed == expected,
        "actor_visible": actor_visible,
        "claim_boundary": CLAIM_SCOPE,
    }


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "behavior_target_tensor_rows": output_dir / "behavior_target_tensor_rows.csv",
        "target_tensor_file_index_rows": output_dir / "target_tensor_file_index_rows.csv",
        "target_tensor_weight_rows": output_dir / "target_tensor_weight_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "target_visibility_guard_rows": output_dir / "target_visibility_guard_rows.csv",
        "side_effect_guard_rows": output_dir / "side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def load_sources(
    *,
    m3060_audit: Path,
    m3059_dir: Path,
    m3057_dir: Path,
    m3055_dir: Path,
    m3053_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3060_audit": m3060_audit,
        "m3059_summary": m3059_dir / "summary.json",
        "m3059_raw_trace_index_rows": m3059_dir / "raw_trace_index_rows.csv",
        "m3059_raw_trace_availability_rows": m3059_dir / "raw_trace_availability_rows.csv",
        "m3059_raw_trace_guard_rows": m3059_dir / "raw_trace_guard_rows.csv",
        "m3059_actor_contract_guard_rows": m3059_dir / "actor_contract_guard_rows.csv",
        "m3059_claim_boundary_rows": m3059_dir / "claim_boundary_rows.csv",
        "m3059_gate_matrix": m3059_dir / "gate_matrix.csv",
        "m3057_summary": m3057_dir / "summary.json",
        "m3057_behavior_target_tensor_rows": m3057_dir / "behavior_target_tensor_rows.csv",
        "m3057_gate_matrix": m3057_dir / "gate_matrix.csv",
        "m3055_summary": m3055_dir / "summary.json",
        "m3055_fitting_contract_rows": m3055_dir / "fitting_contract_rows.csv",
        "m3055_loss_family_rows": m3055_dir / "loss_family_rows.csv",
        "m3055_row_admission_rows": m3055_dir / "row_admission_rows.csv",
        "m3055_gate_matrix": m3055_dir / "gate_matrix.csv",
        "m3053_summary": m3053_dir / "summary.json",
        "m3053_offtrack_rows": m3053_dir / "offtrack_behavior_target_source_rows.csv",
        "m3053_candidate_binding_blocker_rows": m3053_dir / "candidate_binding_blocker_rows.csv",
        "m3053_collision_guard_rows": m3053_dir / "collision_guard_rows.csv",
        "m3053_success_preservation_guard_rows": m3053_dir / "success_preservation_guard_rows.csv",
        "m3053_speed_floor_guard_rows": m3053_dir / "speed_floor_guard_rows.csv",
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m3060_audit_text": paths["m3060_audit"].read_text(encoding="utf-8") if exists["m3060_audit"] else "",
        "m3059_summary": _read_json_if_exists(paths["m3059_summary"]),
        "m3059_raw_trace_index_rows": _read_csv_if_exists(paths["m3059_raw_trace_index_rows"]),
        "m3059_raw_trace_availability_rows": _read_csv_if_exists(paths["m3059_raw_trace_availability_rows"]),
        "m3059_raw_trace_guard_rows": _read_csv_if_exists(paths["m3059_raw_trace_guard_rows"]),
        "m3059_actor_contract_guard_rows": _read_csv_if_exists(paths["m3059_actor_contract_guard_rows"]),
        "m3059_claim_boundary_rows": _read_csv_if_exists(paths["m3059_claim_boundary_rows"]),
        "m3059_gate_rows": _read_csv_if_exists(paths["m3059_gate_matrix"]),
        "m3057_summary": _read_json_if_exists(paths["m3057_summary"]),
        "m3057_behavior_target_tensor_rows": _read_csv_if_exists(paths["m3057_behavior_target_tensor_rows"]),
        "m3057_gate_rows": _read_csv_if_exists(paths["m3057_gate_matrix"]),
        "m3055_summary": _read_json_if_exists(paths["m3055_summary"]),
        "m3055_fitting_contract_rows": _read_csv_if_exists(paths["m3055_fitting_contract_rows"]),
        "m3055_loss_family_rows": _read_csv_if_exists(paths["m3055_loss_family_rows"]),
        "m3055_row_admission_rows": _read_csv_if_exists(paths["m3055_row_admission_rows"]),
        "m3055_gate_rows": _read_csv_if_exists(paths["m3055_gate_matrix"]),
        "m3053_summary": _read_json_if_exists(paths["m3053_summary"]),
        "m3053_offtrack_rows": _read_csv_if_exists(paths["m3053_offtrack_rows"]),
        "m3053_candidate_binding_blocker_rows": _read_csv_if_exists(paths["m3053_candidate_binding_blocker_rows"]),
        "m3053_collision_guard_rows": _read_csv_if_exists(paths["m3053_collision_guard_rows"]),
        "m3053_success_preservation_guard_rows": _read_csv_if_exists(paths["m3053_success_preservation_guard_rows"]),
        "m3053_speed_floor_guard_rows": _read_csv_if_exists(paths["m3053_speed_floor_guard_rows"]),
    }


def load_raw_trace(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as payload:
        return {key: np.asarray(payload[key]) for key in payload.files}


def validate_raw_trace(payload: Mapping[str, np.ndarray]) -> tuple[bool, str]:
    required = [
        "observation_trace",
        "action_trace",
        "next_observation_trace",
        "reward_trace",
        "done_trace",
        "timeout_trace",
    ]
    missing = [key for key in required if key not in payload]
    if missing:
        return False, f"missing arrays: {';'.join(missing)}"
    observation = np.asarray(payload["observation_trace"])
    action = np.asarray(payload["action_trace"])
    next_observation = np.asarray(payload["next_observation_trace"])
    reward = np.asarray(payload["reward_trace"])
    done = np.asarray(payload["done_trace"])
    timeout = np.asarray(payload["timeout_trace"])
    if observation.ndim != 2 or observation.shape[1] != P0_OBSERVATION_DIM:
        return False, f"observation shape {_shape_text(observation)} is not Tx{P0_OBSERVATION_DIM}"
    if action.ndim != 2 or action.shape[1] != ACTION_DIM:
        return False, f"action shape {_shape_text(action)} is not Tx{ACTION_DIM}"
    if next_observation.shape != observation.shape:
        return False, "next observation shape does not match observation shape"
    if reward.shape != (observation.shape[0],):
        return False, "reward shape does not match trace length"
    if done.shape != (observation.shape[0],):
        return False, "done shape does not match trace length"
    if timeout.shape != (observation.shape[0],):
        return False, "timeout shape does not match trace length"
    if not (
        np.isfinite(observation).all()
        and np.isfinite(action).all()
        and np.isfinite(next_observation).all()
        and np.isfinite(reward).all()
    ):
        return False, "raw trace contains non-finite numeric values"
    return True, ""


def target_rule_from_actor_observation(observation: np.ndarray) -> dict[str, np.ndarray | int | float]:
    trace_len = int(observation.shape[0])
    window_steps = min(RECOVERY_WINDOW_MAX_STEPS, trace_len)
    window_start = trace_len - window_steps

    target_action = np.zeros((trace_len, ACTION_DIM), dtype=np.float32)
    target_action_mask = np.zeros((trace_len, ACTION_DIM), dtype=np.float32)
    target_loss_weight = np.zeros((trace_len, ACTION_DIM), dtype=np.float32)

    left_y = observation[:, 13:28:2].astype(np.float32) * 20.0
    right_y = observation[:, 29:44:2].astype(np.float32) * 20.0
    center_y = 0.5 * (left_y + right_y)
    near_center_y = np.mean(center_y[:, :3], axis=1)
    mean_center_y = np.mean(center_y, axis=1)
    vx_body = observation[:, 0].astype(np.float32) * 20.0
    vy_body = observation[:, 1].astype(np.float32) * 12.0
    yaw_rate = observation[:, 2].astype(np.float32) * 2.5

    correction = np.tanh((0.70 * near_center_y + 0.30 * mean_center_y) / 2.0)
    stability_damping = np.tanh((0.08 * vy_body + 0.15 * yaw_rate) / 1.0)
    steer = np.clip(0.80 * correction - 0.20 * stability_damping, -0.85, 0.85)
    speed_excess = np.maximum((vx_body - 4.0) / 10.0, 0.0)
    throttle = np.full(trace_len, -1.0, dtype=np.float32)
    brake = np.clip(0.35 + 0.45 * speed_excess + 0.15 * np.abs(correction), -1.0, 1.0)

    target_action[:, 0] = steer.astype(np.float32)
    target_action[:, 1] = throttle.astype(np.float32)
    target_action[:, 2] = brake.astype(np.float32)

    ramp = np.linspace(0.40, 1.00, window_steps, dtype=np.float32)
    target_action_mask[window_start:, :] = 1.0
    target_loss_weight[window_start:, 0] = 1.00 * ramp
    target_loss_weight[window_start:, 1] = 0.65 * ramp
    target_loss_weight[window_start:, 2] = 0.85 * ramp

    return {
        "target_action": target_action,
        "target_action_mask": target_action_mask,
        "target_loss_weight": target_loss_weight,
        "road_center_y_m": mean_center_y.astype(np.float32),
        "near_road_center_y_m": near_center_y.astype(np.float32),
        "window_start": int(window_start),
        "window_steps": int(window_steps),
    }


def save_target_tensor(path: Path, *, raw_payload: Mapping[str, np.ndarray], tensor: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        observation_trace=np.asarray(raw_payload["observation_trace"], dtype=np.float32),
        raw_action_trace=np.asarray(raw_payload["action_trace"], dtype=np.float32),
        next_observation_trace=np.asarray(raw_payload["next_observation_trace"], dtype=np.float32),
        reward_trace=np.asarray(raw_payload["reward_trace"], dtype=np.float32),
        done_trace=np.asarray(raw_payload["done_trace"], dtype=np.bool_),
        timeout_trace=np.asarray(raw_payload["timeout_trace"], dtype=np.bool_),
        target_action=np.asarray(tensor["target_action"], dtype=np.float32),
        target_action_mask=np.asarray(tensor["target_action_mask"], dtype=np.float32),
        target_loss_weight=np.asarray(tensor["target_loss_weight"], dtype=np.float32),
        road_center_y_m=np.asarray(tensor["road_center_y_m"], dtype=np.float32),
        near_road_center_y_m=np.asarray(tensor["near_road_center_y_m"], dtype=np.float32),
        recovery_window=np.asarray([tensor["window_start"], tensor["window_steps"]], dtype=np.int32),
        raw_action_trace_used_as_target=np.asarray(False, dtype=np.bool_),
    )


def build_target_tensor_artifacts(
    *, source: Mapping[str, Any], output_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    m3057_by_target = {
        str(row.get("target_tensor_row_id", "")): row for row in source["m3057_behavior_target_tensor_rows"]
    }
    m3053_by_source = {
        str(row.get("offtrack_target_source_id", "")): row for row in source["m3053_offtrack_rows"]
    }
    tensor_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []

    for index, raw_row in enumerate(source["m3059_raw_trace_index_rows"], start=1):
        source_target_id = str(raw_row.get("target_tensor_row_id", ""))
        m3057_row = m3057_by_target.get(source_target_id, {})
        source_id = str(raw_row.get("source_offtrack_target_source_id", ""))
        m3053_row = m3053_by_source.get(source_id, {})
        target_row_id = f"m3061-target-tensor-{index:04d}"
        tensor_path = (
            output_dir
            / "target_tensors"
            / f"{target_row_id}_{raw_row.get('measurement_episode_id', '')}.npz"
        )
        raw_trace_path = Path(str(raw_row.get("raw_trace_path", "")))
        raw_trace_available = bool(raw_trace_path.exists() and _bool(raw_row.get("raw_trace_persisted")))
        blocker_family = ""
        status_pass = False
        payload: dict[str, np.ndarray] | None = None
        tensor: dict[str, Any] | None = None
        error = ""

        try:
            if not raw_trace_available:
                raise ValueError("raw_actor_view_trace_missing")
            if not m3057_row:
                raise ValueError("m3057_target_tensor_row_missing")
            if not m3053_row:
                raise ValueError("m3053_offtrack_source_row_missing")
            if _int(raw_row.get("actor_observation_dim"), -1) != P0_OBSERVATION_DIM:
                raise ValueError("raw_trace_actor_observation_dim_not_72")
            if _int(raw_row.get("actor_action_dim"), -1) != ACTION_DIM:
                raise ValueError("raw_trace_actor_action_dim_not_3")
            for field in (
                "hidden_oracle_actor_input_required",
                "target_labels_actor_visible",
                "target_provenance_actor_visible",
                "source_labels_actor_visible",
                "route_labels_actor_visible",
                "outcome_labels_actor_visible",
                "success_progress_labels_actor_visible",
                "verdict_labels_actor_visible",
                "ttc_actor_input_required",
            ):
                if _bool(raw_row.get(field)):
                    raise ValueError(f"forbidden_actor_input_flag:{field}")
            payload = load_raw_trace(raw_trace_path)
            trace_ok, trace_error = validate_raw_trace(payload)
            if not trace_ok:
                raise ValueError(trace_error)
            tensor = target_rule_from_actor_observation(np.asarray(payload["observation_trace"], dtype=np.float32))
            save_target_tensor(tensor_path, raw_payload=payload, tensor=tensor)
            status_pass = bool(tensor_path.exists())
        except Exception as exc:  # noqa: BLE001 - every denominator row remains accounted.
            blocker_family = type(exc).__name__
            error = str(exc)

        observation = np.asarray(payload["observation_trace"]) if payload is not None else np.asarray([])
        raw_action = np.asarray(payload["action_trace"]) if payload is not None else np.asarray([])
        next_observation = np.asarray(payload["next_observation_trace"]) if payload is not None else np.asarray([])
        reward = np.asarray(payload["reward_trace"]) if payload is not None else np.asarray([])
        done = np.asarray(payload["done_trace"]) if payload is not None else np.asarray([])
        timeout = np.asarray(payload["timeout_trace"]) if payload is not None else np.asarray([])
        target_action = np.asarray(tensor["target_action"]) if tensor is not None else np.asarray([])
        target_action_mask = np.asarray(tensor["target_action_mask"]) if tensor is not None else np.asarray([])
        target_loss_weight = np.asarray(tensor["target_loss_weight"]) if tensor is not None else np.asarray([])
        masked_step_count = int(np.count_nonzero(np.max(target_action_mask, axis=1) > 0.0)) if target_action_mask.size else 0
        target_loss_weight_sum = float(np.sum(target_loss_weight)) if target_loss_weight.size else 0.0
        target_action_abs_max = float(np.max(np.abs(target_action))) if target_action.size else 0.0
        target_min = float(np.min(target_action)) if target_action.size else 0.0
        target_max = float(np.max(target_action)) if target_action.size else 0.0
        all_tensors_finite = bool(
            status_pass
            and np.isfinite(observation).all()
            and np.isfinite(raw_action).all()
            and np.isfinite(next_observation).all()
            and np.isfinite(reward).all()
            and np.isfinite(target_action).all()
            and np.isfinite(target_action_mask).all()
            and np.isfinite(target_loss_weight).all()
        )
        if status_pass and not all_tensors_finite:
            status_pass = False
            blocker_family = "nonfinite_target_tensor"
            error = "materialized target tensor contains non-finite values"

        tensor_rows.append(
            {
                "target_tensor_row_id": target_row_id,
                "source_m3057_target_tensor_row_id": source_target_id,
                "raw_trace_index_row_id": raw_row.get("raw_trace_index_row_id", ""),
                "raw_trace_capture_plan_row_id": raw_row.get("raw_trace_capture_plan_row_id", ""),
                "source_offtrack_target_source_id": source_id,
                "measurement_episode_id": raw_row.get("measurement_episode_id", ""),
                "baseline_measurement_row_id": raw_row.get("baseline_measurement_row_id", ""),
                "binding_role": raw_row.get("binding_role", ""),
                "task_family": raw_row.get("task_family", ""),
                "source_edge": raw_row.get("source_edge", ""),
                "window_tag": raw_row.get("window_tag", ""),
                "eval_seed": raw_row.get("eval_seed", ""),
                "behavior_target_family": m3057_row.get("behavior_target_family", m3053_row.get("behavior_target_family", "")),
                "intended_behavior": m3057_row.get("intended_behavior", m3053_row.get("intended_behavior", "")),
                "output_semantics": "direct_action",
                "output_components": EXPECTED_ACTION_COMPONENTS,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "actor_action_shape": ACTION_DIM,
                "raw_actor_view_trace_path": str(raw_trace_path),
                "raw_actor_view_trace_available": raw_trace_available,
                "raw_trace_step_count": int(observation.shape[0]) if observation.ndim == 2 else 0,
                "raw_trace_termination_reason": raw_row.get("termination_reason", ""),
                "numeric_target_tensor_materialized": status_pass,
                "target_tensor_path": str(tensor_path) if status_pass else "",
                "target_action_shape": _shape_text(target_action) if target_action.size else "",
                "target_action_mask_shape": _shape_text(target_action_mask) if target_action_mask.size else "",
                "target_loss_weight_shape": _shape_text(target_loss_weight) if target_loss_weight.size else "",
                "target_action_abs_max": target_action_abs_max if status_pass else "",
                "target_action_min": target_min if status_pass else "",
                "target_action_max": target_max if status_pass else "",
                "target_loss_weight_sum": target_loss_weight_sum if status_pass else "",
                "masked_step_count": masked_step_count if status_pass else 0,
                "recovery_window_start": int(tensor["window_start"]) if tensor is not None else "",
                "recovery_window_steps": int(tensor["window_steps"]) if tensor is not None else "",
                "target_rule_family": TARGET_RULE_FAMILY,
                "target_rule_inputs": TARGET_RULE_INPUTS,
                "target_rule_uses_actor_visible_observation": True,
                "raw_action_trace_used_as_target": False,
                "raw_action_trace_preserved_for_audit": status_pass,
                "trainer_side_only": True,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "local_action_search_run": False,
                "environment_reset_run": False,
                "environment_step_run": False,
                "fitting_run": False,
                "training_run": False,
                "validation_run": False,
                "ranking_run": False,
                "winner_selected": False,
                "checkpoint_mutated": False,
                "checkpoint_promoted": False,
                "target_tensor_quality_claim_made": False,
                "status_pass": status_pass,
                "blocker_family": "" if status_pass else f"{blocker_family}:{error}",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        file_rows.append(
            {
                "target_tensor_file_index_row_id": f"m3061-target-tensor-file-{index:04d}",
                "target_tensor_row_id": target_row_id,
                "measurement_episode_id": raw_row.get("measurement_episode_id", ""),
                "source_raw_trace_path": str(raw_trace_path),
                "target_tensor_path": str(tensor_path),
                "target_tensor_file_exists": tensor_path.exists(),
                "observation_shape": _shape_text(observation) if observation.size else "",
                "raw_action_shape": _shape_text(raw_action) if raw_action.size else "",
                "next_observation_shape": _shape_text(next_observation) if next_observation.size else "",
                "reward_shape": _shape_text(reward) if reward.size else "",
                "done_shape": _shape_text(done) if done.size else "",
                "timeout_shape": _shape_text(timeout) if timeout.size else "",
                "target_action_shape": _shape_text(target_action) if target_action.size else "",
                "target_action_mask_shape": _shape_text(target_action_mask) if target_action_mask.size else "",
                "target_loss_weight_shape": _shape_text(target_loss_weight) if target_loss_weight.size else "",
                "observation_dtype": str(observation.dtype) if observation.size else "",
                "target_action_dtype": str(target_action.dtype) if target_action.size else "",
                "target_action_mask_dtype": str(target_action_mask.dtype) if target_action_mask.size else "",
                "target_loss_weight_dtype": str(target_loss_weight.dtype) if target_loss_weight.size else "",
                "all_tensors_finite": all_tensors_finite,
                "masked_step_count": masked_step_count,
                "target_loss_weight_sum": target_loss_weight_sum,
                "target_action_abs_max": target_action_abs_max,
                "raw_action_trace_used_as_target": False,
                "target_rule_family": TARGET_RULE_FAMILY,
                "status_pass": bool(status_pass and all_tensors_finite and masked_step_count > 0),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
        write_run_state(
            output_dir / "run_state.json",
            {
                "milestone": MILESTONE_ID,
                "scheduled_target_tensor_row_count": len(source["m3059_raw_trace_index_rows"]),
                "target_tensor_row_count": len(tensor_rows),
                "target_tensor_file_index_row_count": len(file_rows),
                "latest_target_tensor_row_id": target_row_id,
                "complete": False,
                "next_blocker": NEXT_ID,
            },
        )
    return tensor_rows, file_rows


def build_weight_rows(source: Mapping[str, Any], tensor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric_count = sum(_bool(row.get("numeric_target_tensor_materialized")) for row in tensor_rows)
    rows = []
    for index, row in enumerate(source["m3055_loss_family_rows"], start=1):
        loss_family = str(row.get("loss_family", ""))
        numeric_materialized = loss_family in {"offtrack_recovery", "stability_and_smoothness"}
        rows.append(
            {
                "weight_row_id": f"m3061-weight-{index:04d}",
                "source_loss_family_id": row.get("loss_family_id", ""),
                "loss_family": loss_family,
                "priority": row.get("priority", ""),
                "source_rows": row.get("source_rows", ""),
                "source_row_count": row.get("row_count", ""),
                "weight_policy": row.get("weight_policy", ""),
                "guard_dependency": row.get("guard_dependency", ""),
                "weight_spec_materialized": True,
                "numeric_weight_tensor_materialized": numeric_materialized,
                "numeric_weight_tensor_scope": "terminal_recovery_window"
                if numeric_materialized
                else "guard_only_no_numeric_tensor",
                "actor_visible": False,
                "status_pass": bool(numeric_count == EXPECTED_TRACE_ROWS),
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_contract_guard_rows(
    *,
    source: Mapping[str, Any],
    tensor_rows: list[dict[str, Any]],
    file_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    m3059_summary = source["m3059_summary"]
    m3055_summary = source["m3055_summary"]
    return [
        actor_guard("m3059_raw_trace_index_row_count", len(source["m3059_raw_trace_index_rows"]), EXPECTED_TRACE_ROWS),
        actor_guard("target_tensor_row_count", len(tensor_rows), EXPECTED_TRACE_ROWS),
        actor_guard("target_tensor_file_index_row_count", len(file_rows), EXPECTED_TRACE_ROWS),
        actor_guard("all_actor_observation_dim_72", all(_int(row.get("actor_observation_shape"), -1) == P0_OBSERVATION_DIM for row in tensor_rows), True),
        actor_guard("all_actor_action_dim_3", all(_int(row.get("actor_action_shape"), -1) == ACTION_DIM for row in tensor_rows), True),
        actor_guard("m3059_observation_shape", _int(m3059_summary.get("observation_shape"), -1), P0_OBSERVATION_DIM),
        actor_guard("m3059_action_shape", _int(m3059_summary.get("action_shape"), -1), ACTION_DIM),
        actor_guard("m3055_direct_action", m3055_summary.get("output_semantics"), "direct_action"),
        actor_guard("output_components", EXPECTED_ACTION_COMPONENTS, EXPECTED_ACTION_COMPONENTS),
        actor_guard("base_policy_required_at_runtime", _bool(m3055_summary.get("base_policy_required_at_runtime")), False),
        actor_guard("target_rule_uses_actor_visible_observation", _all_true(tensor_rows, "target_rule_uses_actor_visible_observation"), True),
        actor_guard("raw_action_trace_used_as_target", _any_true(tensor_rows, "raw_action_trace_used_as_target"), False),
        actor_guard("hidden_oracle_actor_input_required", _any_true(tensor_rows, "hidden_oracle_actor_input_required"), False),
        actor_guard("target_labels_actor_visible", _any_true(tensor_rows, "target_labels_actor_visible"), False),
        actor_guard("target_provenance_actor_visible", _any_true(tensor_rows, "target_provenance_actor_visible"), False),
        actor_guard("ttc_actor_input_required", _any_true(tensor_rows, "ttc_actor_input_required"), False),
    ]


def build_target_visibility_rows(
    *, source: Mapping[str, Any], tensor_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    specs = [
        (
            "m3059_raw_trace_rows_actor_inputs_clean",
            "raw_trace_index_rows.csv",
            _all_false(source["m3059_raw_trace_index_rows"], "hidden_oracle_actor_input_required")
            and _all_false(source["m3059_raw_trace_index_rows"], "target_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "target_provenance_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "source_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "route_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "outcome_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "success_progress_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "verdict_labels_actor_visible")
            and _all_false(source["m3059_raw_trace_index_rows"], "ttc_actor_input_required"),
            True,
        ),
        (
            "m3053_target_sources_actor_invisible",
            "offtrack_behavior_target_source_rows.csv",
            _all_false(source["m3053_offtrack_rows"], "actor_visible")
            and _all_false(source["m3053_offtrack_rows"], "target_labels_actor_visible")
            and _all_false(source["m3053_offtrack_rows"], "target_provenance_actor_visible"),
            True,
        ),
        (
            "m3061_target_labels_actor_invisible",
            "behavior_target_tensor_rows.csv",
            _all_false(tensor_rows, "target_labels_actor_visible"),
            True,
        ),
        (
            "m3061_target_provenance_actor_invisible",
            "behavior_target_tensor_rows.csv",
            _all_false(tensor_rows, "target_provenance_actor_visible"),
            True,
        ),
        (
            "m3061_target_rule_trainer_side_only",
            "behavior_target_tensor_rows.csv",
            _all_true(tensor_rows, "trainer_side_only"),
            True,
        ),
        (
            "m3061_raw_action_not_corrected_target",
            "behavior_target_tensor_rows.csv",
            _all_false(tensor_rows, "raw_action_trace_used_as_target"),
            True,
        ),
    ]
    return [
        {
            "target_visibility_guard_id": f"m3061-target-visibility-{index:04d}",
            "guard_family": family,
            "source_artifact": artifact,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, artifact, observed, expected) in enumerate(specs, start=1)
    ]


def build_side_effect_rows() -> list[dict[str, Any]]:
    side_effects = [
        "reset",
        "step",
        "rollout",
        "replay",
        "local_action_search",
        "target_tensor_fitting",
        "ppo",
        "training",
        "validation",
        "ranking",
        "winner_selection",
        "checkpoint_mutation",
        "checkpoint_promotion",
        "high_fidelity_validation",
        "finite_window_vs_gru",
        "self_id_testing",
    ]
    return [
        {
            "side_effect_guard_id": f"m3061-side-effect-{index:04d}",
            "side_effect": side_effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, side_effect in enumerate(side_effects, start=1)
    ]


def build_claim_rows(*, tensor_rows: list[dict[str, Any]], follow_up_manifest_exists: bool) -> list[dict[str, Any]]:
    numeric_count = sum(_bool(row.get("numeric_target_tensor_materialized")) for row in tensor_rows)
    raw_action_as_target = _any_true(tensor_rows, "raw_action_trace_used_as_target")
    specs = [
        ("numeric_target_tensor_artifacts_materialized", True, numeric_count == EXPECTED_TRACE_ROWS, "M3061 target tensor rows and npz file index"),
        ("bounded_target_rule_recorded", True, numeric_count == EXPECTED_TRACE_ROWS, "M3061 explicit actor-visible road-center rule"),
        ("follow_up_result_audit_manifest_registered", True, follow_up_manifest_exists, "M3062 manifest"),
        ("raw_trace_replay_action_used_as_corrected_target", False, raw_action_as_target, "explicit target rule must avoid copying failed replay actions"),
        ("target_tensor_quality", False, False, "future M3062 audit and fitting evidence"),
        ("fitting_or_training", False, False, "future fitting milestone"),
        ("validation_result", False, False, "future validation route"),
        ("ranking_or_winner_selection", False, False, "future ranking/promotion gate"),
        ("checkpoint_mutation_or_promotion", False, False, "future promotion gate"),
        ("repair_success", False, False, "future closed-loop measurement and audit"),
        ("driver_performance", False, False, "proof/generalization/promotion gates"),
        ("current_sim_verdict", False, False, "separate verdict synthesis"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation"),
        ("paper_claim", False, False, "paper route evidence matrix"),
        ("finite_window_vs_gru", False, False, "future same-case architecture comparison"),
        ("full_ideal_driver_completion", False, False, "future full-driver gate"),
        ("level3_self_id", False, False, "self-ID proof gates"),
    ]
    return [
        {
            "claim_id": f"m3061-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3061": allowed,
            "claim_made": made,
            "status_pass": (allowed and made) or ((not allowed) and (not made)),
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(specs, start=1)
    ]


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    tensor_rows: list[dict[str, Any]],
    file_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    m3059 = source["m3059_summary"]
    m3057 = source["m3057_summary"]
    m3055 = source["m3055_summary"]
    m3053 = source["m3053_summary"]
    numeric_count = sum(_bool(row.get("numeric_target_tensor_materialized")) for row in tensor_rows)
    file_count = sum(_bool(row.get("target_tensor_file_exists")) for row in file_rows)
    mask_count = sum(_int(row.get("masked_step_count"), 0) > 0 for row in file_rows)
    return [
        gate("source_artifacts_present", "lineage", all(source["source_exists"].values()), True, "lineage_invalid"),
        gate("m3060_routes_to_m3061", "lineage", M3060_DECISION_MARKER in source["m3060_audit_text"], True, "lineage_invalid"),
        gate("m3059_status_pass", "lineage", _bool(m3059.get("status_pass")), True, "lineage_invalid"),
        gate("m3059_gate_matrix_pass", "lineage", _bool(m3059.get("gate_matrix_pass")), True, "lineage_invalid"),
        gate("m3059_raw_trace_index_row_count", "denominator", _int(m3059.get("raw_trace_index_row_count"), -1), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("m3059_raw_trace_persisted_count", "artifact", _int(m3059.get("raw_trace_persisted_count"), -1), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("m3059_raw_trace_missing_count", "artifact", _int(m3059.get("raw_trace_missing_count"), -1), 0, "metric_artifact"),
        gate("m3059_trace_step_counts_match_m3050", "artifact", _bool(m3059.get("trace_step_counts_match_m3050")), True, "metric_artifact"),
        gate("m3059_actor_contract_guards_pass", "contract", _all_true(source["m3059_actor_contract_guard_rows"], "status_pass"), True, "contract_violation"),
        gate("m3059_claim_boundary_rows_pass", "claim_boundary", _all_true(source["m3059_claim_boundary_rows"], "status_pass"), True, "contract_violation"),
        gate("m3059_gate_rows_pass", "lineage", _all_true(source["m3059_gate_rows"], "status_pass"), True, "lineage_invalid"),
        gate("m3057_blocker_row_count", "denominator", len(source["m3057_behavior_target_tensor_rows"]), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("m3057_missing_raw_trace_fail_closed", "lineage", _bool(m3057.get("status_pass")), False, "lineage_invalid"),
        gate("m3055_status_pass", "lineage", _bool(m3055.get("status_pass")), True, "lineage_invalid"),
        gate("m3055_gate_matrix_pass", "lineage", _bool(m3055.get("gate_matrix_pass")), True, "lineage_invalid"),
        gate("m3055_direct_action", "contract", m3055.get("output_semantics"), "direct_action", "contract_violation"),
        gate("m3055_base_policy_required_false", "contract", _bool(m3055.get("base_policy_required_at_runtime")), False, "contract_violation"),
        gate("m3055_loss_family_rows", "denominator", len(source["m3055_loss_family_rows"]), EXPECTED_LOSS_FAMILY_ROWS, "metric_artifact"),
        gate("m3053_status_pass", "lineage", _bool(m3053.get("status_pass")), True, "lineage_invalid"),
        gate("m3053_gate_matrix_pass", "lineage", _bool(m3053.get("gate_matrix_pass")), True, "lineage_invalid"),
        gate("m3053_offtrack_source_rows", "denominator", len(source["m3053_offtrack_rows"]), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("target_tensor_row_count", "artifact", len(tensor_rows), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("target_tensor_file_index_row_count", "artifact", len(file_rows), EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("numeric_target_tensors_materialized", "artifact", numeric_count, EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("target_tensor_files_exist", "artifact", file_count, EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("target_tensor_files_finite", "artifact", _all_true(file_rows, "all_tensors_finite"), True, "metric_artifact"),
        gate("target_tensor_masks_nonzero", "artifact", mask_count, EXPECTED_TRACE_ROWS, "metric_artifact"),
        gate("target_action_abs_max_bounded", "contract", all(_float(row.get("target_action_abs_max"), 2.0) <= 1.0 for row in tensor_rows), True, "contract_violation"),
        gate("raw_actions_not_used_as_target", "contract", _any_true(tensor_rows, "raw_action_trace_used_as_target"), False, "contract_violation"),
        gate("weight_rows", "artifact", len(weight_rows), EXPECTED_LOSS_FAMILY_ROWS, "metric_artifact"),
        gate("weight_rows_pass", "artifact", _all_true(weight_rows, "status_pass"), True, "metric_artifact"),
        gate("actor_contract_guards_pass", "contract", _all_true(actor_rows, "status_pass"), True, "contract_violation"),
        gate("target_visibility_guards_pass", "contract", _all_true(visibility_rows, "status_pass"), True, "contract_violation"),
        gate("side_effects_absent", "side_effect", all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows), True, "contract_violation"),
        gate("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, "contract_violation"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30570,
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
        "hypothesis": "A bounded result audit can accept or reject the M3061 raw-trace-backed target tensor rerun artifacts before any fitting admission rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "behavior_target_tensor_rows.csv"),
                str(output_dir / "target_tensor_file_index_rows.csv"),
                str(output_dir / "target_tensor_weight_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "target_visibility_guard_rows.csv"),
                str(output_dir / "side_effect_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [
                f"experiments/manifests/{MILESTONE_ID}.json",
                f"experiments/manifests/{M3060_ID}.json",
            ],
            "parent_objective": [
                "audit raw-trace-backed target tensor artifacts before fitting admission"
            ],
            "derived_from": [MILESTONE_ID, M3060_ID, M3059_ID, M3055_ID],
            "blocked_by": [
                "M3061 target tensor artifacts require audit before fitting admission",
                "target tensor artifacts are not fitted policy quality repair-success validation or driver-performance evidence",
            ],
            "supersedes": ["direct fitting immediately after M3061 without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3062 must audit M3061 target tensor row file index weight actor target-visibility side-effect claim and gate artifacts",
            "M3062 must reject raw replay action copying as corrected recovery target",
            "M3062 must preserve actor observation 72 action 3 direct [steer throttle brake] and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs",
            "M3062 must reject fitted policy quality repair-success validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims",
            "M3062 must choose exactly one fitting admission artifact repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run fitting rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not treat raw replay actions as corrected recovery targets",
            "do not convert target tensor rows into target tensor quality fitted policy quality repair-success driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles residual artifacts or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_result_audit",
            "evidence_increment": "audits M3061 numeric target tensor artifacts before fitting admission",
            "claim_scope": "Result audit only; no fitting rollout validation ranking promotion performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3061 artifact set is incomplete",
                "stop if actor target-visibility side-effect or claim-boundary guards fail",
                "stop if target tensor artifacts are treated as fitted policy quality or performance evidence",
            ],
            "fallback_plan": [
                "route to fitting admission only if M3061 target tensor artifacts are complete and audit accepts claim safety",
                "route to artifact repair if target tensor files rows or guard artifacts are incomplete",
                "route to synthesis or stop if target tensor materialization is not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3061 completes target tensor rerun artifact materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit offtrack-dominant behavior target tensor rerun artifacts",
            "admission_evidence": [
                "M3061 summary and gate matrix",
                "M3061 behavior target tensor rows file index weight specs actor target visibility side-effect and claim rows",
            ],
            "blocked_shortcuts": [
                "no fitting rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3062 status queue scoreboard research log and review",
                "one follow-up manifest only if M3062 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3061 target tensor artifacts are accepted or rejected",
                "one next fitting admission repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3062 audits engineering target tensor artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3062; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3061 target tensor rerun artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety target tensor audit gates.",
            "allowed_claims": [
                "M3061 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits numeric target tensor artifacts before fitting route",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3062 prepares a claim-safe engineering continuation decision",
            "must_synthesize_if": [
                "M3062 cannot select fitting admission repair synthesis or stop route",
                "M3062 would require another materialization-only loop without changing evidence",
                "M3062 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3062 audits M3061 target tensor row file index weight actor target-visibility side-effect claim and gate artifacts",
            "M3062 rejects fitted policy quality repair-success validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3062 selects exactly one next fitting admission repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3062 treats target tensor rows as fitted policy quality or driver performance",
            "M3062 omits actor target-visibility side-effect or claim-boundary audits",
            "M3062 runs fitting validation ranking promotion high-fidelity or architecture comparison",
            "M3062 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3062 audits M3061 target tensor evidence and selects exactly one fitting admission repair synthesis or stop route without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_rerun_result_audit_doc",
                "command": "true",
            }
        ],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(summary_path),
            str(output_dir / "behavior_target_tensor_rows.csv"),
            str(output_dir / "target_tensor_file_index_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "follow_up_manifest": "",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def build_summary(
    *,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    source: Mapping[str, Any],
    tensor_rows: list[dict[str, Any]],
    file_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> dict[str, Any]:
    gate_matrix_pass = _all_true(gate_rows, "status_pass")
    actor_guard_pass = _all_true(actor_rows, "status_pass")
    visibility_guard_pass = _all_true(visibility_rows, "status_pass")
    side_effect_pass = all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows)
    claim_rows_pass = _all_true(claim_rows, "status_pass")
    numeric_count = sum(_bool(row.get("numeric_target_tensor_materialized")) for row in tensor_rows)
    file_count = sum(_bool(row.get("target_tensor_file_exists")) for row in file_rows)
    masked_step_total = sum(_int(row.get("masked_step_count"), 0) for row in file_rows)
    target_loss_weight_total = sum(_float(row.get("target_loss_weight_sum"), 0.0) for row in file_rows)
    status_pass = bool(gate_matrix_pass and numeric_count == EXPECTED_TRACE_ROWS)
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_preflight_fail_closed",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": "active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_route_to_m3062_result_audit"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_target_tensor_rerun_fail_closed_route_to_m3062_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "output_dir": str(output_dir),
        "source_artifacts_present": all(source["source_exists"].values()),
        "m3059_status_pass": _bool(source["m3059_summary"].get("status_pass")),
        "m3059_gate_matrix_pass": _bool(source["m3059_summary"].get("gate_matrix_pass")),
        "m3059_raw_trace_index_row_count": _int(source["m3059_summary"].get("raw_trace_index_row_count"), 0),
        "m3059_raw_trace_persisted_count": _int(source["m3059_summary"].get("raw_trace_persisted_count"), 0),
        "m3059_raw_trace_missing_count": _int(source["m3059_summary"].get("raw_trace_missing_count"), 0),
        "m3057_behavior_target_tensor_row_count": len(source["m3057_behavior_target_tensor_rows"]),
        "m3055_loss_family_row_count": len(source["m3055_loss_family_rows"]),
        "m3053_offtrack_source_row_count": len(source["m3053_offtrack_rows"]),
        "behavior_target_tensor_row_count": len(tensor_rows),
        "target_tensor_file_index_row_count": len(file_rows),
        "target_tensor_weight_row_count": len(weight_rows),
        "numeric_target_tensor_materialized_count": numeric_count,
        "target_tensor_file_exists_count": file_count,
        "target_tensor_missing_count": EXPECTED_TRACE_ROWS - numeric_count,
        "masked_step_count_total": masked_step_total,
        "target_loss_weight_sum_total": target_loss_weight_total,
        "target_rule_family": TARGET_RULE_FAMILY,
        "target_rule_inputs": TARGET_RULE_INPUTS,
        "target_rule_uses_actor_visible_observation": _all_true(tensor_rows, "target_rule_uses_actor_visible_observation"),
        "raw_action_trace_used_as_target": _any_true(tensor_rows, "raw_action_trace_used_as_target"),
        "raw_action_trace_preserved_for_audit": _all_true(tensor_rows, "raw_action_trace_preserved_for_audit"),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_guard_pass,
        "target_visibility_guard_row_count": len(visibility_rows),
        "target_visibility_guard_rows_pass": visibility_guard_pass,
        "side_effect_guard_row_count": len(side_effect_rows),
        "side_effect_guard_rows_pass": side_effect_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "required_artifacts_present": required_artifacts_present,
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": actor_guard_pass,
        "output_semantics": "direct_action",
        "output_components": ["steer", "throttle", "brake"],
        "base_policy_required_at_runtime": False,
        "hidden_oracle_actor_input_detected": _any_true(tensor_rows, "hidden_oracle_actor_input_required"),
        "target_labels_actor_visible": _any_true(tensor_rows, "target_labels_actor_visible"),
        "target_provenance_actor_visible": _any_true(tensor_rows, "target_provenance_actor_visible"),
        "ttc_actor_input_required": _any_true(tensor_rows, "ttc_actor_input_required"),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "local_action_search_run": False,
        "target_tensor_fitting_run": False,
        "fitting_run": False,
        "ppo_run": False,
        "training_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "target_tensor_quality_claim_made": False,
        "fitted_policy_quality_claim_made": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "driver_performance_verdict_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "validation_result_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": NEXT_ID,
        "paths": {
            "summary": str(output_dir / "summary.json"),
            "behavior_target_tensor_rows": str(output_dir / "behavior_target_tensor_rows.csv"),
            "target_tensor_file_index_rows": str(output_dir / "target_tensor_file_index_rows.csv"),
            "target_tensor_weight_rows": str(output_dir / "target_tensor_weight_rows.csv"),
            "actor_contract_guard_rows": str(output_dir / "actor_contract_guard_rows.csv"),
            "target_visibility_guard_rows": str(output_dir / "target_visibility_guard_rows.csv"),
            "side_effect_guard_rows": str(output_dir / "side_effect_guard_rows.csv"),
            "claim_boundary_rows": str(output_dir / "claim_boundary_rows.csv"),
            "gate_matrix": str(output_dir / "gate_matrix.csv"),
            "doc": str(doc_path),
            "follow_up_manifest": str(follow_up_manifest),
        },
    }


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "pass" if _bool(summary.get("status_pass")) else "fail_closed"
    path.write_text(
        f"""# M3061 Active Safety Driver v1 Offtrack-Dominant Behavior Target Tensor Rerun Preflight

## Summary

- status: {status}
- result class: `{summary['result_class']}`
- decision: `{summary['decision']}`
- next blocker: `{NEXT_ID}`
- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`

M3061 consumes the M3060-accepted M3059 raw actor-view traces and materializes
trainer-side target tensor files for the 24 offtrack-dominant rows. It does not
copy the failed replay action trace as the corrected recovery label. The target
rule is `actor_visible_road_center_terminal_recovery_window`: inside the last
up-to-32 steps of each offtrack trace, it estimates road-center offset from the
actor-visible left/right boundary points, damps with actor-visible body velocity
and yaw-rate channels, suppresses throttle, and increases brake.

## Artifact Summary

```text
M3059 raw trace rows: {summary['m3059_raw_trace_index_row_count']}
target tensor rows: {summary['behavior_target_tensor_row_count']}
target tensor files: {summary['target_tensor_file_exists_count']}
numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}
target tensor files missing: {summary['target_tensor_missing_count']}
masked recovery steps total: {summary['masked_step_count_total']}
target loss weight sum total: {summary['target_loss_weight_sum_total']}
weight rows: {summary['target_tensor_weight_row_count']}
actor-contract guard rows: {summary['actor_contract_guard_row_count']}
target-visibility guard rows: {summary['target_visibility_guard_row_count']}
side-effect guard rows: {summary['side_effect_guard_row_count']}
claim-boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Supported Claims

M3061 supports only these bounded claims:

```text
raw-trace-backed trainer-side target tensor artifacts were materialized for M3059 rows
actor observation 72 and action 3 direct [steer, throttle, brake] contract is preserved
target values are generated by an explicit bounded rule using actor-visible road-boundary and body-state channels
raw replay actions are preserved for audit but are not used as corrected recovery targets
target labels, target provenance, source labels, route labels, outcome labels, progress labels, verdict labels, TTC, and oracle values remain outside actor inputs
M3062 result-audit manifest was registered
```

## Rejected Claims

M3061 rejects:

```text
target tensor quality
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3061 is target tensor artifact materialization only. It writes no fitted
weights or policy checkpoints and runs no reset, step, rollout, replay,
local-action search, fitting, training, validation, ranking, promotion,
high-fidelity simulation, finite-window-vs-GRU comparison, paper evaluation,
full-driver evaluation, or self-ID testing.
""",
        encoding="utf-8",
    )


def run(
    *,
    m3060_audit: Path,
    m3059_dir: Path,
    m3057_dir: Path,
    m3055_dir: Path,
    m3053_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_sources(
        m3060_audit=m3060_audit,
        m3059_dir=m3059_dir,
        m3057_dir=m3057_dir,
        m3055_dir=m3055_dir,
        m3053_dir=m3053_dir,
    )

    tensor_rows, file_rows = build_target_tensor_artifacts(source=source, output_dir=output_dir)
    weight_rows = build_weight_rows(source, tensor_rows)
    actor_rows = build_actor_contract_guard_rows(source=source, tensor_rows=tensor_rows, file_rows=file_rows)
    visibility_rows = build_target_visibility_rows(source=source, tensor_rows=tensor_rows)
    side_effect_rows = build_side_effect_rows()
    claim_rows = build_claim_rows(tensor_rows=tensor_rows, follow_up_manifest_exists=follow_up_manifest.exists())

    write_csv_rows(paths["behavior_target_tensor_rows"], tensor_rows, TARGET_TENSOR_FIELDNAMES)
    write_csv_rows(paths["target_tensor_file_index_rows"], file_rows, FILE_INDEX_FIELDNAMES)
    write_csv_rows(paths["target_tensor_weight_rows"], weight_rows, WEIGHT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["target_visibility_guard_rows"], visibility_rows, TARGET_VISIBILITY_FIELDNAMES)
    write_csv_rows(paths["side_effect_guard_rows"], side_effect_rows, SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_json(
        follow_up_manifest,
        build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path, summary_path=paths["summary"]),
    )

    claim_rows = build_claim_rows(tensor_rows=tensor_rows, follow_up_manifest_exists=follow_up_manifest.exists())
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    gate_rows = build_gate_rows(
        source=source,
        tensor_rows=tensor_rows,
        file_rows=file_rows,
        weight_rows=weight_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        tensor_rows=tensor_rows,
        file_rows=file_rows,
        weight_rows=weight_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
    )
    write_doc(doc_path, summary)
    write_json(paths["summary"], summary)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "phase": "pre_required_artifact_gate",
            "status": "materialized_pending_required_artifact_gate",
            "summary": str(paths["summary"]),
            "next_blocker": NEXT_ID,
        },
    )

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_rows(
        source=source,
        tensor_rows=tensor_rows,
        file_rows=file_rows,
        weight_rows=weight_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        tensor_rows=tensor_rows,
        file_rows=file_rows,
        weight_rows=weight_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_doc(doc_path, summary)
    write_json(paths["summary"], summary)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "completed_at_utc": summary["generated_at_utc"],
            "output_dir": str(output_dir),
            "status_pass": summary["status_pass"],
            "gate_matrix_pass": summary["gate_matrix_pass"],
            "numeric_target_tensor_materialized_count": summary["numeric_target_tensor_materialized_count"],
            "target_tensor_file_exists_count": summary["target_tensor_file_exists_count"],
            "raw_action_trace_used_as_target": summary["raw_action_trace_used_as_target"],
            "status": "completed" if summary["status_pass"] else "completed_fail_closed",
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3060-audit", type=Path, default=DEFAULT_M3060_AUDIT)
    parser.add_argument("--m3059-dir", type=Path, default=DEFAULT_M3059_DIR)
    parser.add_argument("--m3057-dir", type=Path, default=DEFAULT_M3057_DIR)
    parser.add_argument("--m3055-dir", type=Path, default=DEFAULT_M3055_DIR)
    parser.add_argument("--m3053-dir", type=Path, default=DEFAULT_M3053_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run(
        m3060_audit=args.m3060_audit,
        m3059_dir=args.m3059_dir,
        m3057_dir=args.m3057_dir,
        m3055_dir=args.m3055_dir,
        m3053_dir=args.m3053_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"numeric_target_tensor_materialized_count={summary['numeric_target_tensor_materialized_count']}")
    print(f"target_tensor_file_exists_count={summary['target_tensor_file_exists_count']}")
    print(f"raw_action_trace_used_as_target={summary['raw_action_trace_used_as_target']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
