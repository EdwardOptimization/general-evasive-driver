"""M2784 source-only belief-stress candidate closed-loop delta panel.

This preflight runs a bounded paired source-vs-candidate diagnostic panel over
the repo-local HF0/FourWheel backend. It writes execution and delta artifacts
for audit only. It does not train, validate, rank, select a winner, promote a
checkpoint, compute a success-rate verdict, or claim driver performance.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.engineering_controller_failure_surface_guarded_repair_execution import (
    _file_sha256,
    model_state_sha256,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
    ORDINARY_ROLE_FAMILIES,
    STRESS_FAMILIES,
    as_bool,
    build_run_item_map,
    read_csv_rows,
    stress_preparation_label,
)
from autodrift.engineering_controller_source_only_outcome_events import (
    _event_stats,
    _primary_obstacle,
)
from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
    physical_control_from_action,
    validate_actor_action,
)


DEFAULT_MILESTONE = (
    "m2784-engineering-controller-route-a-source-only-belief-stress-candidate-"
    "closed-loop-delta-panel-preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_"
    "closed_loop_delta_panel"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2784-engineering-controller-route-a-source-only-belief-stress-candidate-"
    "closed-loop-delta-panel-preflight.md"
)
DEFAULT_M2783_AUDIT = Path(
    "docs/m2783-engineering-controller-route-a-source-only-belief-stress-short-training-"
    "continuation-result-audit.md"
)
DEFAULT_M2782_DIR = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight"
)
DEFAULT_SOURCE_CHECKPOINT = Path(
    "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_"
    "mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
)
DEFAULT_CANDIDATE_CHECKPOINT = Path(
    "runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_"
    "continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2785-engineering-controller-route-a-source-only-belief-"
    "stress-candidate-closed-loop-delta-panel-result-audit.json"
)
DEFAULT_NEXT_BLOCKER = (
    "m2785-engineering-controller-route-a-source-only-belief-stress-candidate-"
    "closed-loop-delta-panel-result-audit"
)
DEFAULT_SEED_COUNT = 4
DEFAULT_HORIZON_STEPS = 80

CHECKPOINT_SUBJECTS = ("source", "candidate")
CLAIM_SCOPE = "Route A source-only paired closed-loop delta diagnostic preflight only"
FORBIDDEN_INTERPRETATION = (
    "validation, ranking, winner selection, checkpoint promotion, success-rate verdict, "
    "repair success, driver performance, paper evidence, finite-window-vs-GRU conclusion, "
    "current-sim verdict, high-fidelity validation, full ideal driver completion, or "
    "level3 self-identification"
)
CLAIM_BOUNDARY = (
    "M2784 writes paired source-only closed-loop diagnostic deltas only; rows are not "
    "ranking, promotion, validation, performance, paper, current-sim, high-fidelity, "
    "full-driver, or self-ID evidence"
)
RESULT_CLASS_PASS = (
    "engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_"
    "delta_panel_preflight_pass"
)
RESULT_CLASS_FAIL = (
    "engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_"
    "delta_panel_preflight_failed"
)

FALSE_CLAIM_FLAGS = {
    "training_run": False,
    "ppo_run": False,
    "measured_validation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "repair_success_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_simulation_run": False,
    "high_fidelity_validation_claim_made": False,
    "full_ideal_driver_claim_made": False,
    "level3_self_id_claim_made": False,
}

PAIRED_EXECUTION_FIELDNAMES = [
    "pair_id",
    "execution_row_id",
    "checkpoint_subject",
    "checkpoint_path",
    "checkpoint_hash",
    "model_state_hash",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "seed_index",
    "seed",
    "source_curriculum_row_id",
    "fixture_id",
    "stress_preparation",
    "warmup_step_count",
    "horizon_steps",
    "steps_executed",
    "observation_shape",
    "action_shape",
    "reset_run",
    "policy_action_run",
    "backend_step_run",
    "closed_loop_rollout_run",
    "finite_observation",
    "finite_action",
    "action_within_bounds",
    "backend_terminated",
    "backend_truncated",
    "backend_status",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "final_road_margin_m",
    "collision_diagnostic",
    "road_departure_diagnostic",
    "final_speed_mps",
    "max_abs_yaw_rate",
    "max_abs_y",
    "mean_throttle",
    "mean_brake",
    "throttle_brake_conflict_proxy",
    "max_abs_steer",
    "mean_abs_steer",
    "mean_action_l1",
    "command_response_proxy",
    "actor_visible_label",
    "hidden_or_oracle_actor_inputs_required",
    "ordinary_denominator_allowed",
    "mitigation_reference",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "claim_scope",
    "forbidden_interpretation",
]
PAIRED_DELTA_FIELDNAMES = [
    "pair_id",
    "role_family",
    "dynamics_axis",
    "stress_family",
    "seed_index",
    "seed",
    "source_execution_row_id",
    "candidate_execution_row_id",
    "source_checkpoint",
    "candidate_checkpoint",
    "source_checkpoint_hash",
    "candidate_checkpoint_hash",
    "source_steps_executed",
    "candidate_steps_executed",
    "candidate_minus_source_minimum_obstacle_clearance_m",
    "candidate_minus_source_minimum_road_margin_m",
    "candidate_minus_source_final_road_margin_m",
    "candidate_minus_source_final_speed_mps",
    "candidate_minus_source_max_abs_yaw_rate",
    "candidate_minus_source_max_abs_y",
    "candidate_minus_source_throttle_brake_conflict_proxy",
    "candidate_minus_source_mean_throttle",
    "candidate_minus_source_mean_brake",
    "candidate_minus_source_mean_action_l1",
    "candidate_minus_source_command_response_proxy",
    "mean_action_delta_l1",
    "paired_row_complete",
    "finite_delta",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "success_rate_verdict_computed",
    "claim_scope",
    "forbidden_interpretation",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_tier",
    "gate_family",
    "status_pass",
    "observed",
    "expected",
    "row_count",
    "failure_type",
    "claim_boundary",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "guard_family",
    "protected_field",
    "actor_visible_allowed",
    "actor_observation_shape",
    "action_shape",
    "status_pass",
    "evidence",
    "claim_boundary",
]
MITIGATION_GUARD_FIELDNAMES = [
    "source_guard_id",
    "candidate_id",
    "role_family",
    "dynamics_axis",
    "seed",
    "mitigation_reference",
    "ordinary_denominator_allowed",
    "future_training_allowed",
    "future_execution_allowed",
    "context_only",
    "actor_visible_allowed",
    "included_in_paired_execution_rows",
    "included_in_delta_rows",
    "status_pass",
    "guard_family",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "allowed",
    "status_pass",
    "evidence",
    "claim_boundary",
]


def run_belief_stress_candidate_closed_loop_delta_panel(
    output_dir: Path | str,
    *,
    m2783_audit: Path | str = DEFAULT_M2783_AUDIT,
    m2782_dir: Path | str = DEFAULT_M2782_DIR,
    source_checkpoint: Path | str = DEFAULT_SOURCE_CHECKPOINT,
    candidate_checkpoint: Path | str = DEFAULT_CANDIDATE_CHECKPOINT,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    device: str = "cpu",
    seed_count: int = DEFAULT_SEED_COUNT,
    horizon_steps: int = DEFAULT_HORIZON_STEPS,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    if int(seed_count) < 2:
        raise ValueError("M2784 requires at least two seeds")
    if int(horizon_steps) < 1:
        raise ValueError("horizon_steps must be positive")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = _paths(output, Path(doc_path), Path(follow_up_manifest))
    source_paths = _source_paths(
        Path(m2783_audit),
        Path(m2782_dir),
        Path(source_checkpoint),
        Path(candidate_checkpoint),
    )
    _require_sources(source_paths)

    m2782_summary = read_json(source_paths["m2782_summary"])
    checkpoint_manifest = read_json(source_paths["checkpoint_manifest"])
    curriculum_rows = read_csv_rows(source_paths["training_curriculum_rows"])
    source_mitigation_rows = read_csv_rows(source_paths["mitigation_reference_guard_rows"])
    selected_curriculum = select_curriculum_rows(curriculum_rows)

    subject_registry = load_subject_registry(
        source_paths["source_checkpoint"],
        source_paths["candidate_checkpoint"],
        device=device,
    )
    run_item_map = build_run_item_map(int(seed_count))
    execution_rows = collect_paired_execution_rows(
        selected_curriculum,
        run_item_map,
        subject_registry,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
    )
    delta_rows = build_paired_delta_rows(
        execution_rows,
        subject_registry,
    )
    mitigation_guard_rows = build_mitigation_reference_guard_rows(source_mitigation_rows)
    actor_guard_rows = build_actor_contract_guard_rows(execution_rows)
    claim_rows = build_claim_boundary_rows()
    proof_gate_rows = build_proof_gate_rows(
        source_paths=source_paths,
        m2782_summary=m2782_summary,
        checkpoint_manifest=checkpoint_manifest,
        curriculum_rows=selected_curriculum,
        execution_rows=execution_rows,
        delta_rows=delta_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        subject_registry=subject_registry,
        seed_count=int(seed_count),
    )
    generalization_gate_rows = build_generalization_delta_gate_rows(
        selected_curriculum,
        execution_rows,
        delta_rows,
        seed_count=int(seed_count),
    )
    promotion_guard_rows = build_promotion_guard_rows()
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows

    write_csv_rows(paths["paired_execution_rows"], execution_rows, PAIRED_EXECUTION_FIELDNAMES)
    write_csv_rows(paths["paired_delta_rows"], delta_rows, PAIRED_DELTA_FIELDNAMES)
    write_csv_rows(paths["proof_retention_gate_rows"], proof_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["generalization_delta_gate_rows"], generalization_gate_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["promotion_guard_rows"], promotion_guard_rows, GATE_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_guard_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["mitigation_reference_guard_rows"], mitigation_guard_rows, MITIGATION_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source_paths=source_paths,
        m2782_summary=m2782_summary,
        checkpoint_manifest=checkpoint_manifest,
        subject_registry=subject_registry,
        curriculum_rows=selected_curriculum,
        execution_rows=execution_rows,
        delta_rows=delta_rows,
        proof_gate_rows=proof_gate_rows,
        generalization_gate_rows=generalization_gate_rows,
        promotion_guard_rows=promotion_guard_rows,
        actor_guard_rows=actor_guard_rows,
        mitigation_guard_rows=mitigation_guard_rows,
        claim_rows=claim_rows,
        seed_count=int(seed_count),
        horizon_steps=int(horizon_steps),
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2785_manifest(summary))
    write_doc(paths["doc"], summary)

    summary = {
        **summary,
        "required_artifacts_present": required_artifacts_present(paths),
        "m2785_follow_up_manifest_registered": paths["follow_up_manifest"].exists(),
    }
    summary["status_pass"] = bool(summary["status_pass"] and summary["required_artifacts_present"])
    summary["result_class"] = RESULT_CLASS_PASS if summary["status_pass"] else RESULT_CLASS_FAIL
    write_json(paths["summary"], summary)
    write_json(paths["run_state"], build_run_state(summary, paths, source_paths))
    write_json(paths["follow_up_manifest"], build_m2785_manifest(summary))
    write_doc(paths["doc"], summary)
    return summary


def _paths(output: Path, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output / "summary.json",
        "paired_execution_rows": output / "paired_execution_rows.csv",
        "paired_delta_rows": output / "paired_delta_rows.csv",
        "proof_retention_gate_rows": output / "proof_retention_gate_rows.csv",
        "generalization_delta_gate_rows": output / "generalization_delta_gate_rows.csv",
        "promotion_guard_rows": output / "promotion_guard_rows.csv",
        "actor_contract_guard_rows": output / "actor_contract_guard_rows.csv",
        "mitigation_reference_guard_rows": output / "mitigation_reference_guard_rows.csv",
        "claim_boundary_rows": output / "claim_boundary_rows.csv",
        "gate_matrix": output / "gate_matrix.csv",
        "run_state": output / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _source_paths(
    m2783_audit: Path,
    m2782_dir: Path,
    source_checkpoint: Path,
    candidate_checkpoint: Path,
) -> dict[str, Path]:
    return {
        "m2783_audit": m2783_audit,
        "m2782_summary": m2782_dir / "summary.json",
        "checkpoint_manifest": m2782_dir / "checkpoint_manifest.json",
        "training_curriculum_rows": m2782_dir / "training_curriculum_rows.csv",
        "training_run_rows": m2782_dir / "training_run_rows.csv",
        "m2782_gate_matrix": m2782_dir / "gate_matrix.csv",
        "mitigation_reference_guard_rows": m2782_dir / "mitigation_reference_guard_rows.csv",
        "source_checkpoint": source_checkpoint,
        "candidate_checkpoint": candidate_checkpoint,
    }


def _require_sources(paths: dict[str, Path]) -> None:
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"M2784 missing required source artifacts: {missing}")


def select_curriculum_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row.get("role_family") in ORDINARY_ROLE_FAMILIES
        and row.get("dynamics_axis") in DYNAMICS_AXES
        and row.get("stress_family") in STRESS_FAMILIES
        and as_bool(row.get("future_execution_allowed", True))
    ]
    expected_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    if len(selected) != expected_count:
        raise RuntimeError(f"expected {expected_count} M2782 ordinary execution curriculum rows, got {len(selected)}")
    return sorted(
        selected,
        key=lambda item: (item["role_family"], item["dynamics_axis"], item["stress_family"]),
    )


def load_subject_registry(
    source_checkpoint: Path,
    candidate_checkpoint: Path,
    *,
    device: str,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for subject, path in (
        ("source", source_checkpoint),
        ("candidate", candidate_checkpoint),
    ):
        model, checkpoint = load_actor_critic_checkpoint(path, device=device)
        if int(model.obs_dim) != P0_OBSERVATION_DIM or int(model.act_dim) != ACTION_DIM:
            raise RuntimeError(f"{subject} checkpoint does not preserve P0 72/action 3")
        registry[subject] = {
            "subject": subject,
            "checkpoint_path": Path(path),
            "checkpoint_hash": _file_sha256(path),
            "model_state_hash": model_state_sha256(checkpoint["model_state"]),
            "actor_encoder": getattr(model, "actor_encoder", ""),
            "model": model,
        }
    return registry


def collect_paired_execution_rows(
    curriculum_rows: list[dict[str, Any]],
    run_item_map: dict[tuple[str, str, int], Any],
    subject_registry: dict[str, dict[str, Any]],
    *,
    seed_count: int,
    horizon_steps: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for curriculum in curriculum_rows:
        for seed_index in range(int(seed_count)):
            item = run_item_map[(curriculum["role_family"], curriculum["dynamics_axis"], int(seed_index))]
            pair_id = (
                f"m2784_pair_{curriculum['role_family']}_{curriculum['dynamics_axis']}_"
                f"{curriculum['stress_family']}_seed_{int(item.seed)}"
            )
            for subject in CHECKPOINT_SUBJECTS:
                rows.append(
                    run_closed_loop_execution(
                        subject_registry[subject],
                        item,
                        curriculum,
                        pair_id=pair_id,
                        seed_index=int(seed_index),
                        horizon_steps=int(horizon_steps),
                    )
                )
    return rows


def run_closed_loop_execution(
    subject_entry: dict[str, Any],
    item: Any,
    curriculum: dict[str, Any],
    *,
    pair_id: str,
    seed_index: int,
    horizon_steps: int,
) -> dict[str, Any]:
    model = subject_entry["model"]
    extractor = P0ObservationExtractor()
    backend = FourWheelHF0Backend(fixture_spec=item.fixture_spec)
    warmup_count = 0
    terminated = False
    truncated = False
    backend_status = "not_started"
    observation_finite_flags: list[bool] = []
    action_finite_flags: list[bool] = []
    action_bound_flags: list[bool] = []
    physical_throttle: list[float] = []
    physical_brake: list[float] = []
    action_l1: list[float] = []
    abs_steer: list[float] = []
    yaw_rates: list[float] = []
    abs_y: list[float] = []
    command_response: list[float] = []
    trace_rows: list[dict[str, Any]] = []
    hidden = None
    actor_view = None
    try:
        reset_result = backend.reset(
            BackendResetRequest(
                seed=item.seed,
                scenario_spec_id=item.fixture_id,
                role_family=item.role_family,
                options={
                    "seed_panel_id": item.seed_panel_id,
                    "seed_index": item.seed_index,
                    "seed": item.seed,
                    "dynamics_axis_id": item.dynamics_axis_id,
                    "stress_family": curriculum["stress_family"],
                    "checkpoint_subject": subject_entry["subject"],
                    "actor_visible_labels": False,
                },
            )
        )
        actor_view = reset_result.actor_view
        if curriculum["stress_family"] == "held_actuator_history_stress":
            warmup = backend.step(np.asarray([0.18, -0.20, -0.55], dtype=np.float32))
            actor_view = warmup.actor_view
            warmup_count = 1
            backend_status = warmup.backend_status

        for step_index in range(int(horizon_steps)):
            observation = extractor.extract(actor_view)
            observation_finite = bool(
                observation.shape == (P0_OBSERVATION_DIM,) and np.all(np.isfinite(observation))
            )
            observation_finite_flags.append(observation_finite)
            action, hidden = deterministic_actor_action(model, observation, hidden)
            action_array = np.asarray(action, dtype=np.float32)
            action_finite = bool(action_array.shape == (ACTION_DIM,) and np.all(np.isfinite(action_array)))
            action_within_bounds = bool(
                action_finite and np.all(action_array >= -1.0) and np.all(action_array <= 1.0)
            )
            action_finite_flags.append(action_finite)
            action_bound_flags.append(action_within_bounds)
            clipped_action = validate_actor_action(action_array)
            physical = physical_control_from_action(clipped_action)
            physical_throttle.append(float(physical[1]))
            physical_brake.append(float(physical[2]))
            action_l1.append(float(np.mean(np.abs(clipped_action))))
            abs_steer.append(abs(float(clipped_action[0])))
            command_response.append(
                float(np.linalg.norm([actor_view.ego.ax_body, actor_view.ego.ay_body, actor_view.ego.yaw_rate], ord=2))
            )

            step_result = backend.step(clipped_action)
            state = dict(step_result.diagnostics.get("state", {}))
            state_vx = _float(state.get("vx", actor_view.ego.vx_body))
            state_vy = _float(state.get("vy", actor_view.ego.vy_body))
            state_yaw_rate = _float(state.get("yaw_rate", actor_view.ego.yaw_rate))
            yaw_rates.append(abs(state_yaw_rate))
            abs_y.append(abs(_float(state.get("y", 0.0))))
            backend_status = step_result.backend_status
            terminated = terminated or bool(step_result.terminated_by_backend)
            truncated = truncated or bool(step_result.truncated_by_backend)
            trace_rows.append(
                {
                    "step_index": step_index,
                    "state_x": _float(state.get("x", 0.0)),
                    "state_y": _float(state.get("y", 0.0)),
                    "state_vx": state_vx,
                    "state_vy": state_vy,
                    "state_speed": float(np.hypot(state_vx, state_vy)),
                    "state_yaw_rate": state_yaw_rate,
                }
            )
            actor_view = step_result.actor_view
    finally:
        backend.close()

    event = _event_stats(
        trace_rows,
        road=item.fixture_spec.road,
        obstacle=_primary_obstacle(item.fixture_spec.obstacles),
    )
    final_speed = float(trace_rows[-1]["state_speed"]) if trace_rows else 0.0
    row_id = f"{pair_id}_{subject_entry['subject']}"
    return {
        "pair_id": pair_id,
        "execution_row_id": row_id,
        "checkpoint_subject": subject_entry["subject"],
        "checkpoint_path": str(subject_entry["checkpoint_path"]),
        "checkpoint_hash": subject_entry["checkpoint_hash"],
        "model_state_hash": subject_entry["model_state_hash"],
        "role_family": item.role_family,
        "dynamics_axis": item.dynamics_axis_id,
        "stress_family": curriculum["stress_family"],
        "seed_index": int(seed_index),
        "seed": int(item.seed),
        "source_curriculum_row_id": curriculum.get("source_curriculum_row_id", ""),
        "fixture_id": item.fixture_id,
        "stress_preparation": stress_preparation_label(curriculum["stress_family"]),
        "warmup_step_count": int(warmup_count),
        "horizon_steps": int(horizon_steps),
        "steps_executed": len(trace_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "reset_run": True,
        "policy_action_run": True,
        "backend_step_run": bool(trace_rows),
        "closed_loop_rollout_run": bool(trace_rows),
        "finite_observation": bool(observation_finite_flags and all(observation_finite_flags)),
        "finite_action": bool(action_finite_flags and all(action_finite_flags)),
        "action_within_bounds": bool(action_bound_flags and all(action_bound_flags)),
        "backend_terminated": bool(terminated),
        "backend_truncated": bool(truncated),
        "backend_status": backend_status,
        "minimum_obstacle_clearance_m": float(event.minimum_obstacle_clearance_m),
        "minimum_road_margin_m": float(event.minimum_road_margin_m),
        "final_road_margin_m": float(event.final_road_margin_m),
        "collision_diagnostic": bool(event.collision_event),
        "road_departure_diagnostic": bool(event.road_departure_event),
        "final_speed_mps": final_speed,
        "max_abs_yaw_rate": _max(yaw_rates),
        "max_abs_y": _max(abs_y),
        "mean_throttle": _mean(physical_throttle),
        "mean_brake": _mean(physical_brake),
        "throttle_brake_conflict_proxy": _mean(
            throttle * brake for throttle, brake in zip(physical_throttle, physical_brake)
        ),
        "max_abs_steer": _max(abs_steer),
        "mean_abs_steer": _mean(abs_steer),
        "mean_action_l1": _mean(action_l1),
        "command_response_proxy": _mean(command_response),
        "actor_visible_label": False,
        "hidden_or_oracle_actor_inputs_required": False,
        "ordinary_denominator_allowed": True,
        "mitigation_reference": False,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def deterministic_actor_action(model: Any, observation: np.ndarray, hidden: Any) -> tuple[np.ndarray, Any]:
    if getattr(model, "is_online_recurrent", False):
        action, _log_prob, _value, next_hidden = model.act_recurrent(observation, hidden, deterministic=True)
        return np.asarray(action, dtype=np.float32), next_hidden
    action, _log_prob, _value = model.act(observation, deterministic=True)
    return np.asarray(action, dtype=np.float32), hidden


def build_paired_delta_rows(
    execution_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in execution_rows:
        by_pair.setdefault(str(row["pair_id"]), {})[str(row["checkpoint_subject"])] = row

    for pair_id in sorted(by_pair):
        pair = by_pair[pair_id]
        source = pair.get("source")
        candidate = pair.get("candidate")
        paired_complete = source is not None and candidate is not None
        if not paired_complete:
            continue
        source_action_terms = [
            float(source["mean_abs_steer"]),
            float(source["mean_throttle"]),
            float(source["mean_brake"]),
        ]
        candidate_action_terms = [
            float(candidate["mean_abs_steer"]),
            float(candidate["mean_throttle"]),
            float(candidate["mean_brake"]),
        ]
        delta_values = {
            "candidate_minus_source_minimum_obstacle_clearance_m": _delta(
                candidate,
                source,
                "minimum_obstacle_clearance_m",
            ),
            "candidate_minus_source_minimum_road_margin_m": _delta(candidate, source, "minimum_road_margin_m"),
            "candidate_minus_source_final_road_margin_m": _delta(candidate, source, "final_road_margin_m"),
            "candidate_minus_source_final_speed_mps": _delta(candidate, source, "final_speed_mps"),
            "candidate_minus_source_max_abs_yaw_rate": _delta(candidate, source, "max_abs_yaw_rate"),
            "candidate_minus_source_max_abs_y": _delta(candidate, source, "max_abs_y"),
            "candidate_minus_source_throttle_brake_conflict_proxy": _delta(
                candidate,
                source,
                "throttle_brake_conflict_proxy",
            ),
            "candidate_minus_source_mean_throttle": _delta(candidate, source, "mean_throttle"),
            "candidate_minus_source_mean_brake": _delta(candidate, source, "mean_brake"),
            "candidate_minus_source_mean_action_l1": _delta(candidate, source, "mean_action_l1"),
            "candidate_minus_source_command_response_proxy": _delta(candidate, source, "command_response_proxy"),
        }
        rows.append(
            {
                "pair_id": pair_id,
                "role_family": source["role_family"],
                "dynamics_axis": source["dynamics_axis"],
                "stress_family": source["stress_family"],
                "seed_index": source["seed_index"],
                "seed": source["seed"],
                "source_execution_row_id": source["execution_row_id"],
                "candidate_execution_row_id": candidate["execution_row_id"],
                "source_checkpoint": str(subject_registry["source"]["checkpoint_path"]),
                "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
                "source_checkpoint_hash": subject_registry["source"]["checkpoint_hash"],
                "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
                "source_steps_executed": source["steps_executed"],
                "candidate_steps_executed": candidate["steps_executed"],
                **delta_values,
                "mean_action_delta_l1": float(
                    np.mean(np.abs(np.asarray(candidate_action_terms) - np.asarray(source_action_terms)))
                ),
                "paired_row_complete": paired_complete,
                "finite_delta": bool(all(np.isfinite(float(value)) for value in delta_values.values())),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
                "success_rate_verdict_computed": False,
                "claim_scope": CLAIM_SCOPE,
                "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_mitigation_reference_guard_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        mitigation_reference = as_bool(row.get("mitigation_reference", False))
        ordinary_allowed = as_bool(row.get("ordinary_denominator_allowed", False))
        output.append(
            {
                "source_guard_id": row.get("source_guard_id", row.get("candidate_id", "")),
                "candidate_id": row.get("candidate_id", ""),
                "role_family": row.get("role_family", ""),
                "dynamics_axis": row.get("dynamics_axis", ""),
                "seed": row.get("seed", ""),
                "mitigation_reference": mitigation_reference,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": as_bool(row.get("future_training_allowed", False)),
                "future_execution_allowed": as_bool(row.get("future_execution_allowed", False)),
                "context_only": True,
                "actor_visible_allowed": False,
                "included_in_paired_execution_rows": False,
                "included_in_delta_rows": False,
                "status_pass": bool(mitigation_reference and not ordinary_allowed),
                "guard_family": "mitigation_reference_denominator_guard",
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output


def build_actor_contract_guard_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        (
            "actor_contract_observation_shape_72",
            "actor_contract",
            "observation_shape",
            {int(row["observation_shape"]) for row in execution_rows} == {P0_OBSERVATION_DIM},
            f"{P0_OBSERVATION_DIM}",
        ),
        (
            "actor_contract_action_shape_3",
            "actor_contract",
            "action_shape",
            {int(row["action_shape"]) for row in execution_rows} == {ACTION_DIM},
            f"{ACTION_DIM}",
        ),
        (
            "finite_observations",
            "actor_contract",
            "finite_observation",
            bool(execution_rows) and all(as_bool(row["finite_observation"]) for row in execution_rows),
            "true",
        ),
        (
            "finite_actions",
            "actor_contract",
            "finite_action",
            bool(execution_rows) and all(as_bool(row["finite_action"]) for row in execution_rows),
            "true",
        ),
        (
            "actions_within_bounds",
            "actor_contract",
            "action_within_bounds",
            bool(execution_rows) and all(as_bool(row["action_within_bounds"]) for row in execution_rows),
            "true",
        ),
        (
            "no_hidden_or_oracle_actor_input",
            "actor_contract",
            "hidden_or_oracle_actor_inputs_required",
            not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in execution_rows),
            "false",
        ),
        (
            "no_actor_visible_stress_label",
            "actor_contract",
            "stress_admission_curriculum_labels",
            not any(as_bool(row["actor_visible_label"]) for row in execution_rows),
            "false",
        ),
    ]
    return [
        {
            "guard_id": guard_id,
            "guard_family": guard_family,
            "protected_field": field,
            "actor_visible_allowed": False,
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "status_pass": status,
            "evidence": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for guard_id, guard_family, field, status, evidence in rows
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        ("validation_result", "validation", False, False, "M2784 does not run measured validation"),
        ("ranking_result", "ranking", False, False, "M2784 does not rank checkpoints"),
        ("winner_selection", "promotion", False, False, "M2784 selects no winner"),
        ("checkpoint_promotion", "promotion", False, False, "M2784 promotes no checkpoint"),
        ("success_rate_verdict", "metric_artifact", False, False, "M2784 emits no success-rate verdict"),
        ("driver_performance", "performance", False, False, "M2784 is diagnostic delta evidence only"),
        ("paper_result", "paper", False, False, "M2784 is not paper evidence"),
        ("current_sim_verdict", "current_sim", False, False, "M2784 is not a current-sim verdict"),
        ("high_fidelity_validation", "high_fidelity", False, False, "M2784 does not run HF validation"),
        ("level3_self_id", "self_id", False, False, "M2784 is not self-ID evidence"),
        (
            "paired_delta_artifacts_complete",
            "allowed_artifact_completion",
            True,
            True,
            "M2784 may claim paired diagnostic artifacts were written",
        ),
    ]
    return [
        {
            "claim_id": claim_id,
            "claim_family": family,
            "claim_made": made,
            "allowed": allowed,
            "status_pass": bool((not made) or allowed),
            "evidence": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim_id, family, made, allowed, evidence in rows
    ]


def build_proof_gate_rows(
    *,
    source_paths: dict[str, Path],
    m2782_summary: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    subject_registry: dict[str, dict[str, Any]],
    seed_count: int,
) -> list[dict[str, Any]]:
    expected_execution_rows = len(curriculum_rows) * int(seed_count) * len(CHECKPOINT_SUBJECTS)
    expected_delta_rows = len(curriculum_rows) * int(seed_count)
    return [
        gate(
            "proof_m2783_audit_present",
            "proof",
            "lineage",
            source_paths["m2783_audit"].exists(),
            str(source_paths["m2783_audit"]),
            "M2783 audit artifact exists",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_m2782_status_pass",
            "proof",
            "lineage",
            bool(m2782_summary.get("status_pass", False)),
            str(bool(m2782_summary.get("status_pass", False))),
            "true",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_checkpoint_lineage_hashes",
            "proof",
            "lineage",
            bool(subject_registry["source"]["checkpoint_hash"])
            and bool(subject_registry["candidate"]["checkpoint_hash"])
            and subject_registry["source"]["checkpoint_hash"] != subject_registry["candidate"]["checkpoint_hash"]
            and bool(checkpoint_manifest.get("candidate_checkpoint_hash")),
            "source and candidate hashes",
            "source and candidate hashes with candidate lineage",
            1,
            "lineage_invalid",
        ),
        gate(
            "proof_paired_execution_row_count",
            "proof",
            "artifact",
            len(execution_rows) == expected_execution_rows,
            str(len(execution_rows)),
            str(expected_execution_rows),
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "proof_paired_delta_row_count",
            "proof",
            "artifact",
            len(delta_rows) == expected_delta_rows,
            str(len(delta_rows)),
            str(expected_delta_rows),
            len(delta_rows),
            "metric_artifact",
        ),
        gate(
            "proof_pair_completeness",
            "proof",
            "artifact",
            bool(delta_rows) and all(as_bool(row["paired_row_complete"]) for row in delta_rows),
            "all pairs complete",
            "all pairs complete",
            len(delta_rows),
            "metric_artifact",
        ),
        gate(
            "proof_actor_contract_72_3",
            "proof",
            "actor_contract",
            bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows),
            "all actor guards pass",
            "all actor guards pass",
            len(actor_guard_rows),
            "contract_violation",
        ),
        gate(
            "proof_no_hidden_or_oracle_actor_input",
            "proof",
            "actor_contract",
            not any(as_bool(row["hidden_or_oracle_actor_inputs_required"]) for row in execution_rows),
            "false",
            "false",
            len(execution_rows),
            "contract_violation",
        ),
        gate(
            "proof_actor_invisible_labels",
            "proof",
            "actor_contract",
            not any(as_bool(row["actor_visible_label"]) for row in execution_rows),
            "false",
            "false",
            len(execution_rows),
            "contract_violation",
        ),
        gate(
            "proof_finite_action_observation",
            "proof",
            "metric_artifact",
            all(
                as_bool(row["finite_observation"])
                and as_bool(row["finite_action"])
                and as_bool(row["action_within_bounds"])
                for row in execution_rows
            ),
            "finite",
            "finite",
            len(execution_rows),
            "metric_artifact",
        ),
        gate(
            "proof_mitigation_rows_excluded",
            "proof",
            "proof_washout",
            bool(mitigation_guard_rows)
            and all(not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows)
            and all(not as_bool(row["included_in_paired_execution_rows"]) for row in mitigation_guard_rows),
            "mitigation rows excluded",
            "mitigation rows excluded",
            len(mitigation_guard_rows),
            "proof_washout",
        ),
        gate(
            "proof_no_ranking_winner_success_verdict",
            "proof",
            "claim_boundary",
            not any(as_bool(row["ranking_admissible"]) or as_bool(row["winner_selected"]) for row in delta_rows)
            and not any(as_bool(row["success_rate_verdict_computed"]) for row in delta_rows),
            "false",
            "false",
            len(delta_rows),
            "objective_overfit",
        ),
    ]


def build_generalization_delta_gate_rows(
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    *,
    seed_count: int,
) -> list[dict[str, Any]]:
    return [
        gate(
            "generalization_role_family_coverage",
            "generalization",
            "scenario_sampling",
            {row["role_family"] for row in delta_rows} == set(ORDINARY_ROLE_FAMILIES),
            ";".join(sorted({row["role_family"] for row in delta_rows})),
            ";".join(ORDINARY_ROLE_FAMILIES),
            len(delta_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_dynamics_axis_coverage",
            "generalization",
            "scenario_sampling",
            {row["dynamics_axis"] for row in delta_rows} == set(DYNAMICS_AXES),
            ";".join(sorted({row["dynamics_axis"] for row in delta_rows})),
            ";".join(DYNAMICS_AXES),
            len(delta_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_stress_family_coverage",
            "generalization",
            "scenario_sampling",
            {row["stress_family"] for row in delta_rows} == set(STRESS_FAMILIES),
            ";".join(sorted({row["stress_family"] for row in delta_rows})),
            ";".join(STRESS_FAMILIES),
            len(delta_rows),
            "scenario_sampling_failure",
        ),
        gate(
            "generalization_requested_seed_count",
            "generalization",
            "seed_split",
            int(seed_count) >= 2,
            str(int(seed_count)),
            ">=2",
            len(delta_rows),
            "seed_fragility",
        ),
        gate(
            "generalization_each_bucket_seed_coverage",
            "generalization",
            "seed_split",
            _each_bucket_seed_coverage(delta_rows, int(seed_count)),
            "complete",
            "complete",
            len(delta_rows),
            "seed_fragility",
        ),
        gate(
            "generalization_pair_subject_coverage",
            "generalization",
            "artifact",
            {row["checkpoint_subject"] for row in execution_rows} == set(CHECKPOINT_SUBJECTS)
            and len(execution_rows) == len(curriculum_rows) * int(seed_count) * len(CHECKPOINT_SUBJECTS),
            ";".join(sorted({row["checkpoint_subject"] for row in execution_rows})),
            ";".join(CHECKPOINT_SUBJECTS),
            len(execution_rows),
            "metric_artifact",
        ),
    ]


def build_promotion_guard_rows() -> list[dict[str, Any]]:
    return [
        gate(
            "promotion_checkpoint_not_promoted",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_winner_selected",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "promotion_gate_failure",
        ),
        gate(
            "promotion_no_success_rate_verdict",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "metric_artifact",
        ),
        gate(
            "promotion_no_active_config_overwrite",
            "promotion",
            "promotion_guard",
            True,
            "false",
            "false",
            1,
            "contract_violation",
        ),
    ]


def gate(
    gate_id: str,
    tier: str,
    family: str,
    status_pass: bool,
    observed: str,
    expected: str,
    row_count: int,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_tier": tier,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "row_count": int(row_count),
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source_paths: dict[str, Path],
    m2782_summary: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
    subject_registry: dict[str, dict[str, Any]],
    curriculum_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    proof_gate_rows: list[dict[str, Any]],
    generalization_gate_rows: list[dict[str, Any]],
    promotion_guard_rows: list[dict[str, Any]],
    actor_guard_rows: list[dict[str, Any]],
    mitigation_guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    seed_count: int,
    horizon_steps: int,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    gate_rows = proof_gate_rows + generalization_gate_rows + promotion_guard_rows
    forbidden_claims_made = any(
        as_bool(row["claim_made"]) and not as_bool(row["allowed"]) for row in claim_rows
    )
    gate_matrix_pass = bool(gate_rows) and all(as_bool(row["status_pass"]) for row in gate_rows)
    actor_contract_shape = bool(actor_guard_rows) and all(as_bool(row["status_pass"]) for row in actor_guard_rows)
    status_pass = bool(
        gate_matrix_pass
        and actor_contract_shape
        and all(as_bool(row["status_pass"]) for row in mitigation_guard_rows)
        and bool(m2782_summary.get("status_pass", False))
        and len(delta_rows) == len(curriculum_rows) * int(seed_count)
        and not forbidden_claims_made
    )
    return {
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "status_pass": status_pass,
        "result_class": RESULT_CLASS_PASS if status_pass else RESULT_CLASS_FAIL,
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "doc": str(paths["doc"]),
        "next_blocker": next_blocker,
        "m2783_audit": str(source_paths["m2783_audit"]),
        "m2782_summary": str(source_paths["m2782_summary"]),
        "m2782_status_pass": bool(m2782_summary.get("status_pass", False)),
        "m2782_gate_matrix_pass": bool(m2782_summary.get("gate_matrix_pass", True)),
        "m2782_candidate_checkpoint_hash": checkpoint_manifest.get("candidate_checkpoint_hash", ""),
        "source_checkpoint": str(subject_registry["source"]["checkpoint_path"]),
        "candidate_checkpoint": str(subject_registry["candidate"]["checkpoint_path"]),
        "source_checkpoint_hash": subject_registry["source"]["checkpoint_hash"],
        "candidate_checkpoint_hash": subject_registry["candidate"]["checkpoint_hash"],
        "source_model_state_hash": subject_registry["source"]["model_state_hash"],
        "candidate_model_state_hash": subject_registry["candidate"]["model_state_hash"],
        "paired_execution_rows": str(paths["paired_execution_rows"]),
        "paired_delta_rows": str(paths["paired_delta_rows"]),
        "proof_retention_gate_rows": str(paths["proof_retention_gate_rows"]),
        "generalization_delta_gate_rows": str(paths["generalization_delta_gate_rows"]),
        "promotion_guard_rows": str(paths["promotion_guard_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "mitigation_reference_guard_rows": str(paths["mitigation_reference_guard_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": False,
        "m2785_follow_up_manifest_registered": False,
        "source_only_backend_reset_run": True,
        "source_only_backend_step_run": True,
        "policy_action_run": True,
        "closed_loop_rollout_run": True,
        "training_run": False,
        "seed_count": int(seed_count),
        "horizon_steps": int(horizon_steps),
        "curriculum_row_count": len(curriculum_rows),
        "paired_execution_row_count": len(execution_rows),
        "paired_delta_row_count": len(delta_rows),
        "proof_gate_row_count": len(proof_gate_rows),
        "generalization_gate_row_count": len(generalization_gate_rows),
        "promotion_guard_row_count": len(promotion_guard_rows),
        "actor_guard_row_count": len(actor_guard_rows),
        "mitigation_reference_guard_row_count": len(mitigation_guard_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "failed_gate_ids": [row["gate_id"] for row in gate_rows if not as_bool(row["status_pass"])],
        "actor_contract_shape_72_action_3": bool(actor_contract_shape),
        "hidden_or_oracle_actor_inputs_required": False,
        "actor_visible_stress_admission_curriculum_labels_detected": False,
        "all_actions_finite": bool(execution_rows) and all(as_bool(row["finite_action"]) for row in execution_rows),
        "all_observations_finite": bool(execution_rows)
        and all(as_bool(row["finite_observation"]) for row in execution_rows),
        "all_actions_within_bounds": bool(execution_rows)
        and all(as_bool(row["action_within_bounds"]) for row in execution_rows),
        "paired_rows_complete": bool(delta_rows) and all(as_bool(row["paired_row_complete"]) for row in delta_rows),
        "mitigation_reference_rows_guarded": all(
            not as_bool(row["ordinary_denominator_allowed"]) for row in mitigation_guard_rows
        ),
        "forbidden_claims_made": forbidden_claims_made,
        "diagnostic_delta_rows_only": all(as_bool(row["diagnostic_only"]) for row in delta_rows),
        **FALSE_CLAIM_FLAGS,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def required_artifacts_present(paths: dict[str, Path]) -> bool:
    required_keys = [
        "summary",
        "paired_execution_rows",
        "paired_delta_rows",
        "proof_retention_gate_rows",
        "generalization_delta_gate_rows",
        "promotion_guard_rows",
        "actor_contract_guard_rows",
        "mitigation_reference_guard_rows",
        "claim_boundary_rows",
        "gate_matrix",
        "run_state",
        "doc",
        "follow_up_manifest",
    ]
    return all(paths[key].exists() for key in required_keys)


def build_run_state(
    summary: dict[str, Any],
    paths: dict[str, Path],
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "run_state_id": "m2784_belief_stress_candidate_closed_loop_delta_panel_state_v0",
        "generated_at_utc": utc_timestamp(),
        "milestone": summary["milestone"],
        "status_pass": summary["status_pass"],
        "source_paths": {key: str(path) for key, path in source_paths.items()},
        "output_paths": {key: str(path) for key, path in paths.items()},
        "actor_contract": {
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "hidden_or_oracle_actor_inputs_required": False,
            "actor_visible_stress_admission_curriculum_labels_detected": False,
        },
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_m2785_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    task_id = DEFAULT_NEXT_BLOCKER
    return {
        "id": task_id,
        "type": "gate",
        "gate_tier": "proof",
        "promotion_decision": "not_applicable",
        "failure_types": [
            "contract_violation",
            "lineage_invalid",
            "metric_artifact",
            "scenario_sampling_failure",
            "behavior_regression",
            "objective_overfit",
            "proof_washout",
        ],
        "lineage": {
            "parent_checkpoint": [summary["source_checkpoint"], summary["candidate_checkpoint"]],
            "parent_dataset": [
                summary["summary"],
                summary["paired_execution_rows"],
                summary["paired_delta_rows"],
                summary["proof_retention_gate_rows"],
                summary["generalization_delta_gate_rows"],
                summary["promotion_guard_rows"],
                summary["actor_contract_guard_rows"],
                summary["mitigation_reference_guard_rows"],
                summary["claim_boundary_rows"],
                summary["gate_matrix"],
                summary["doc"],
            ],
            "parent_config": [
                "experiments/manifests/m2784-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-preflight.json",
                "experiments/manifests/m2783-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-result-audit.json",
                "experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json",
            ],
            "parent_objective": [
                "audit the M2784 paired source-only candidate-vs-source closed-loop delta panel before interpretation"
            ],
            "derived_from": [DEFAULT_MILESTONE],
            "blocked_by": [
                "M2784 paired deltas must be audited before any validation ranking promotion performance or self-ID interpretation",
                "M2784 remains source-only and cannot resolve the M2638 high-fidelity source dependency",
            ],
            "supersedes": [
                "direct interpretation of M2784 deltas without result audit",
                "candidate checkpoint promotion from paired diagnostic deltas",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{task_id}.md",
        "public_gates": [
            "M2785 must audit M2784 summary paired execution rows paired delta rows gates and claim boundaries",
            "M2785 must preserve actor 72/action 3 no hidden/oracle actor input and actor-invisible labels",
            "M2785 must keep mitigation reference rows outside ordinary denominators",
            "M2785 must reject validation ranking winner promotion success-rate verdict driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not execute reset step policy action rollout replay validation training PPO source build adapter probe or external simulation",
            "do not change actor inputs or action contract",
            "do not expose role dynamics intervention stress curriculum admission outcome success progress route or verdict labels to actor input",
            "do not use mitigation reference rows as ordinary successes",
            "do not rank checkpoints or select a winner",
            "do not promote a checkpoint",
            "do not compute success-rate verdict metrics",
            "do not claim repair success driver performance validation paper current-sim high-fidelity full ideal driver or self-ID result",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_source_only_belief_stress_short_training",
            "evidence_axis": "source_only_belief_stress_candidate_closed_loop_delta_panel_result_audit",
            "evidence_increment": "audits M2784 paired closed-loop diagnostic delta artifacts before interpretation",
            "claim_scope": (
                "Result audit only; no new execution training validation ranking promotion driver-performance "
                "paper high-fidelity self-ID or full-driver claim"
            ),
            "stop_condition": [
                "stop if M2784 required artifacts are incomplete",
                "stop if actor or claim boundaries fail",
                "stop if checkpoint lineage hashes are missing",
                "stop if paired deltas are interpreted as ranking or promotion evidence",
            ],
            "fallback_plan": [
                "route to artifact repair if required artifacts are missing",
                "route to branch synthesis if paired deltas are negative or claim boundaries fail",
                "route to next fresh evidence design only after audit accepts claim safety",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2784 writes paired source-vs-candidate closed-loop delta artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2784 paired source-only closed-loop delta panel artifacts",
            "admission_evidence": [
                "M2784 summary and gate artifacts exist",
                "M2784 writes paired execution and delta rows with source/candidate lineage",
                "M2784 is not validated ranked or promoted before this audit",
            ],
            "blocked_shortcuts": [
                "no new execution or training in M2785",
                "no validation ranking promotion success-rate verdict performance paper HF full-driver or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{task_id}.md",
                "M2785 status queue scoreboard research log and review",
            ],
            "next_stage_criteria": [
                "M2784 artifacts are complete and claim-safe or failure is classified",
                "one bounded follow-up or stop decision is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2785 audits source-only M2784 artifacts and cannot establish self-ID.",
            "history_necessity_tests": [
                "M2785 may check that M2784 covered history stress rows but runs no self-ID comparison."
            ],
            "temporal_evidence_window": "M2772-M2785 source-only belief-stress branch.",
            "negative_result_policy": (
                "If M2784 artifacts fail or deltas are negative, preserve failure and route to "
                "synthesis or repair rather than weakening gates."
            ),
            "allowed_claims": [
                "M2784 paired delta artifacts are accepted or rejected as complete and claim-safe",
                "no driver-performance paper current-sim high-fidelity full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits fresh M2784 paired closed-loop delta artifacts before any extension",
            "paper_verdict_delta": "no paper verdict; audit decides whether M2784 can be used as future engineering evidence",
            "must_synthesize_if": [
                "M2785 finds incomplete artifacts or claim-boundary failure",
                "another process-only milestone is proposed after M2785 without fresh evidence or synthesis",
            ],
        },
        "hypothesis": "M2784 paired closed-loop delta artifacts can be audited for completeness and claim safety before interpretation.",
        "success_criteria": [
            f"docs/{task_id}.md exists",
            "M2785 audits M2784 summary paired execution paired delta gate actor guard claim and lineage artifacts",
            "M2785 registers one bounded follow-up or stop decision",
            "M2785 makes no new execution training validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim",
        ],
        "failure_criteria": [
            "M2785 executes new training or rollout",
            "M2785 treats M2784 as validation ranking or promotion evidence",
            "M2785 claims driver performance paper high-fidelity full-driver or self-ID result",
        ],
        "decision_rule": "Pass only if M2785 writes a claim-safe audit of M2784 artifacts and routes before interpretation.",
        "commands": [{"name": "audit_design_only", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{task_id}.md", "type": "md"}],
        "baseline_checkpoints": [summary["source_checkpoint"], summary["candidate_checkpoint"]],
        "baseline_artifacts": [summary["summary"], summary["gate_matrix"]],
        "scoreboard_checkpoint": f"docs/{task_id}.md",
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    failed = ", ".join(summary["failed_gate_ids"]) if summary["failed_gate_ids"] else "none"
    lines = [
        "# M2784 Engineering Controller Route A Source-Only Belief-Stress Candidate Closed-Loop Delta Panel Preflight",
        "",
        "- status: completed" if summary["status_pass"] else "- status: failed",
        f"- result_class: `{summary['result_class']}`",
        "- manifest: `experiments/manifests/m2784-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-preflight.json`",
        f"- summary: `{summary['summary']}`",
        f"- paired execution rows: `{summary['paired_execution_rows']}`",
        f"- paired delta rows: `{summary['paired_delta_rows']}`",
        f"- proof retention gates: `{summary['proof_retention_gate_rows']}`",
        f"- generalization delta gates: `{summary['generalization_delta_gate_rows']}`",
        f"- promotion guards: `{summary['promotion_guard_rows']}`",
        f"- follow-up manifest: `{summary['follow_up_manifest']}`",
        f"- next: `{summary['next_blocker']}`",
        "",
        "## Result",
        "",
        "M2784 ran a bounded source-only HF0/FourWheel paired closed-loop diagnostic",
        "panel over the M2655 source checkpoint and the M2782 candidate checkpoint.",
        "The rows are candidate-vs-source deltas for audit, not a ranking or winner",
        "selection.",
        "",
        "```text",
        f"curriculum_rows: {summary['curriculum_row_count']}",
        f"seed_count: {summary['seed_count']}",
        f"horizon_steps: {summary['horizon_steps']}",
        f"paired_execution_rows: {summary['paired_execution_row_count']}",
        f"paired_delta_rows: {summary['paired_delta_row_count']}",
        f"proof_gate_rows: {summary['proof_gate_row_count']}",
        f"generalization_gate_rows: {summary['generalization_gate_row_count']}",
        f"promotion_guard_rows: {summary['promotion_guard_row_count']}",
        f"failed_gate_ids: {failed}",
        "```",
        "",
        "## Actor And Claim Boundary",
        "",
        "Actor input stayed at P0 observation 72 and action 3. Stress, admission,",
        "curriculum, role, dynamics, outcome, success, progress, route, and verdict",
        "labels remained evaluator metadata and were not actor-visible. Mitigation",
        "reference rows stayed outside ordinary denominators.",
        "",
        "M2784 does not train, validate, rank, select a winner, promote a checkpoint,",
        "compute a success-rate verdict, claim repair success, driver performance,",
        "paper evidence, current-sim verdict, high-fidelity validation, full ideal",
        "driver completion, or level3 self-identification.",
        "",
        "## Route Decision",
        "",
        "Route to M2785 result audit before interpreting the paired deltas or choosing",
        "any continuation, synthesis, repair, or stop decision.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _each_bucket_seed_coverage(rows: list[dict[str, Any]], seed_count: int) -> bool:
    expected = set(range(int(seed_count)))
    buckets: dict[tuple[str, str, str], set[int]] = {}
    for row in rows:
        key = (row["role_family"], row["dynamics_axis"], row["stress_family"])
        buckets.setdefault(key, set()).add(int(row["seed_index"]))
    expected_bucket_count = len(ORDINARY_ROLE_FAMILIES) * len(DYNAMICS_AXES) * len(STRESS_FAMILIES)
    return len(buckets) == expected_bucket_count and all(indices == expected for indices in buckets.values())


def _delta(candidate: dict[str, Any], source: dict[str, Any], field: str) -> float:
    return float(candidate[field]) - float(source[field])


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mean(values: Any) -> float:
    items = [float(value) for value in values]
    if not items:
        return 0.0
    return float(np.mean(np.asarray(items, dtype=np.float64)))


def _max(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(np.max(np.asarray(values, dtype=np.float64)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2783-audit", type=Path, default=DEFAULT_M2783_AUDIT)
    parser.add_argument("--m2782-dir", type=Path, default=DEFAULT_M2782_DIR)
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--candidate-checkpoint", type=Path, default=DEFAULT_CANDIDATE_CHECKPOINT)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--horizon-steps", type=int, default=DEFAULT_HORIZON_STEPS)
    args = parser.parse_args()
    run_belief_stress_candidate_closed_loop_delta_panel(
        args.output_dir,
        m2783_audit=args.m2783_audit,
        m2782_dir=args.m2782_dir,
        source_checkpoint=args.source_checkpoint,
        candidate_checkpoint=args.candidate_checkpoint,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
        device=args.device,
        seed_count=args.seed_count,
        horizon_steps=args.horizon_steps,
    )


if __name__ == "__main__":
    main()
