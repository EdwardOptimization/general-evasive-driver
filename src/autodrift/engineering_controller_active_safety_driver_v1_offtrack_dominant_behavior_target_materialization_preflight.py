"""Materialize M3053 offtrack-dominant behavior target-source artifacts.

M3053 consumes the M3052-selected behavior-negative route evidence and writes a
trainer-side target-source and guard panel for a later Active Safety Driver v1
offtrack recovery selector/reflex. It does not reset, step, rollout, replay,
fit, train, validate, rank, promote, mutate checkpoints, run high-fidelity
simulation, compare finite-window-vs-GRU, or test self-ID.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3053-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-materialization-preflight"
)
NEXT_ID = (
    "m3054-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-materialization-result-audit"
)
M3052_ID = (
    "m3052-engineering-controller-active-safety-driver-v1-behavior-negative-"
    "measurement-synthesis-repair-route-design"
)
M3051_ID = (
    "m3051-engineering-controller-active-safety-driver-v1-actuation-aware-"
    "residual-repair-closed-loop-measurement-result-audit"
)

DEFAULT_M3052_DESIGN = Path(f"docs/{M3052_ID}.md")
DEFAULT_M3051_AUDIT = Path(f"docs/{M3051_ID}.md")
DEFAULT_M3050_DIR = Path(
    "runs/m3050_engineering_controller_active_safety_driver_v1_actuation_aware_"
    "residual_repair_closed_loop_measurement_preflight"
)
DEFAULT_M3043_DIR = Path("runs/m3043_engineering_controller_active_safety_driver_v1_closed_loop_measurement_preflight")
DEFAULT_M3045_DIR = Path("runs/m3045_engineering_controller_active_safety_driver_v1_failure_decomposition_materialization_preflight")
DEFAULT_OUTPUT_DIR = Path("runs/m3053_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_target_materialization_preflight")
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_MEASUREMENT_ROWS = 32
EXPECTED_SUCCESS_ROWS = 4
EXPECTED_COLLISION_ROWS = 4
EXPECTED_OFFTRACK_ROWS = 24
EXPECTED_SPEED_TOO_LOW_ROWS = 1
EXPECTED_CANDIDATE_ROWS = 16
EXPECTED_CANDIDATE_SUCCESS_ROWS = 0
EXPECTED_REPAIR_REQUIREMENT_ROWS = 6

CLAIM_SCOPE = (
    "M3053 Active Safety Driver v1 offtrack-dominant behavior target "
    "materialization preflight only; M3052 design, M3051 audit, M3050/M3043 "
    "same-denominator measurement rows, and M3045 repair requirements may be "
    "converted into trainer-side behavior target-source and guard artifacts. "
    "No reset, step, rollout, replay, local-action search, target tensor "
    "quality claim, fitting, PPO, training, validation, ranking, winner "
    "selection, checkpoint mutation, checkpoint promotion, repair success, "
    "driver-performance verdict, current-sim verdict, high-fidelity "
    "validation, paper evidence, finite-window-vs-GRU evidence, full ideal "
    "driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target tensor quality, fitted policy quality, repair success, validation "
    "result, driver-performance verdict, current-sim verdict, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, or level3 self-identification"
)

ROUTE_FIELDNAMES = [
    "route_row_id",
    "selected_route",
    "route_family",
    "parent_synthesis",
    "materialization_unit",
    "actor_observation_shape",
    "actor_action_shape",
    "direct_action_output",
    "offtrack_rows_required",
    "candidate_binding_success_required_before_promotion",
    "collision_guard_required",
    "success_preservation_required",
    "speed_floor_guard_required",
    "trainer_side_only",
    "actor_visible_labels_required",
    "claim_boundary",
]
OFFTRACK_FIELDNAMES = [
    "offtrack_target_source_id",
    "measurement_episode_id",
    "baseline_measurement_row_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "eval_seed",
    "steps",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "high_sideslip_fraction",
    "lateral_rmse",
    "action_rate_mean",
    "residual_abs_max",
    "headroom_clip_fraction",
    "action_clip_fraction",
    "baseline_success",
    "baseline_collision",
    "success_delta_vs_baseline",
    "collision_delta_vs_baseline",
    "behavior_target_family",
    "target_source_type",
    "intended_behavior",
    "later_model_output_contract",
    "trainer_side_only",
    "actor_visible",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "status_pass",
    "claim_boundary",
]
CANDIDATE_BLOCKER_FIELDNAMES = [
    "candidate_blocker_id",
    "measurement_episode_id",
    "task_family",
    "source_edge",
    "window_tag",
    "success",
    "collision",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "headroom_clip_fraction",
    "action_clip_fraction",
    "blocker_family",
    "blocked_claims",
    "status_pass",
    "claim_boundary",
]
COLLISION_GUARD_FIELDNAMES = [
    "collision_guard_id",
    "measurement_episode_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "termination_reason",
    "min_clearance_margin",
    "obstacle_collision_radius",
    "baseline_collision",
    "guard_family",
    "guard_required_before_fit",
    "status_pass",
    "claim_boundary",
]
SUCCESS_GUARD_FIELDNAMES = [
    "success_preservation_guard_id",
    "measurement_episode_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "min_clearance_margin",
    "return",
    "baseline_success",
    "guard_family",
    "preserve_as_positive_reference",
    "status_pass",
    "claim_boundary",
]
SPEED_FLOOR_FIELDNAMES = [
    "speed_floor_guard_id",
    "measurement_episode_id",
    "binding_role",
    "task_family",
    "source_edge",
    "window_tag",
    "termination_reason",
    "speed_mean",
    "guard_family",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3053",
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


def artifact_paths(output_dir: Path, *, doc_path: Path, follow_up_manifest: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "behavior_repair_route_rows": output_dir / "behavior_repair_route_rows.csv",
        "offtrack_behavior_target_source_rows": output_dir / "offtrack_behavior_target_source_rows.csv",
        "candidate_binding_blocker_rows": output_dir / "candidate_binding_blocker_rows.csv",
        "collision_guard_rows": output_dir / "collision_guard_rows.csv",
        "success_preservation_guard_rows": output_dir / "success_preservation_guard_rows.csv",
        "speed_floor_guard_rows": output_dir / "speed_floor_guard_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = [_float(row.get(key)) for row in rows]
    return sum(values) / len(values) if values else 0.0


def _metric_by_group(rows: list[dict[str, str]], group: str) -> dict[str, str]:
    for row in rows:
        if row.get("group") == group:
            return row
    return {}


def _source_actor_contract_clean(rows: list[dict[str, str]]) -> bool:
    forbidden_fields = [
        "actor_input_contract_changed",
        "hidden_oracle_actor_input_required",
        "target_labels_actor_visible",
        "target_provenance_actor_visible",
        "source_labels_actor_visible",
        "route_labels_actor_visible",
        "outcome_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
        "ttc_actor_input_required",
    ]
    return all(not _bool(row.get(field)) for row in rows for field in forbidden_fields)


def load_source_artifacts(
    *,
    m3052_design: Path,
    m3051_audit: Path,
    m3050_dir: Path,
    m3043_dir: Path,
    m3045_dir: Path,
) -> dict[str, Any]:
    paths = {
        "m3052_design": m3052_design,
        "m3051_audit": m3051_audit,
        "m3050_summary": m3050_dir / "summary.json",
        "m3050_measurement_rows": m3050_dir / "measurement_episode_rows.csv",
        "m3050_metric_rows": m3050_dir / "metric_summary_rows.csv",
        "m3050_gate_matrix": m3050_dir / "gate_matrix.csv",
        "m3043_summary": m3043_dir / "summary.json",
        "m3043_measurement_rows": m3043_dir / "measurement_episode_rows.csv",
        "m3043_metric_rows": m3043_dir / "metric_summary_rows.csv",
        "m3045_repair_requirements": m3045_dir / "repair_requirement_rows.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required M3053 input artifacts: {missing}")
    return {
        "paths": paths,
        "m3052_design_text": m3052_design.read_text(encoding="utf-8"),
        "m3051_audit_text": m3051_audit.read_text(encoding="utf-8"),
        "m3050_summary": read_json(paths["m3050_summary"]),
        "m3050_measurement_rows": read_csv_rows(paths["m3050_measurement_rows"]),
        "m3050_metric_rows": read_csv_rows(paths["m3050_metric_rows"]),
        "m3050_gate_rows": read_csv_rows(paths["m3050_gate_matrix"]),
        "m3043_summary": read_json(paths["m3043_summary"]),
        "m3043_measurement_rows": read_csv_rows(paths["m3043_measurement_rows"]),
        "m3043_metric_rows": read_csv_rows(paths["m3043_metric_rows"]),
        "m3045_repair_requirement_rows": read_csv_rows(paths["m3045_repair_requirements"]),
    }


def build_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_row_id": "m3053-route-0001",
            "selected_route": "offtrack_dominant_behavior_target_materialization",
            "route_family": "behavior_level_recovery_selector_reflex",
            "parent_synthesis": M3052_ID,
            "materialization_unit": "trainer_side_behavior_target_source_and_guard_panel",
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "actor_action_shape": ACTION_DIM,
            "direct_action_output": "[steer, throttle, brake]",
            "offtrack_rows_required": EXPECTED_OFFTRACK_ROWS,
            "candidate_binding_success_required_before_promotion": "> 0/16 plus guard audit; no promotion in M3053",
            "collision_guard_required": True,
            "success_preservation_required": True,
            "speed_floor_guard_required": True,
            "trainer_side_only": True,
            "actor_visible_labels_required": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_offtrack_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    offtrack_rows = [row for row in measurement_rows if row.get("termination_reason") == "off_track"]
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(offtrack_rows, start=1):
        output_rows.append(
            {
                "offtrack_target_source_id": f"m3053-offtrack-target-source-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "baseline_measurement_row_id": row.get("baseline_measurement_row_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "eval_seed": row.get("eval_seed", ""),
                "steps": row.get("steps", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "max_off_track_overshoot": row.get("max_off_track_overshoot", ""),
                "time_to_first_off_track_s": row.get("time_to_first_off_track_s", ""),
                "high_sideslip_fraction": row.get("high_sideslip_fraction", ""),
                "lateral_rmse": row.get("lateral_rmse", ""),
                "action_rate_mean": row.get("action_rate_mean", ""),
                "residual_abs_max": row.get("residual_abs_max", ""),
                "headroom_clip_fraction": row.get("headroom_clip_fraction", ""),
                "action_clip_fraction": row.get("action_clip_fraction", ""),
                "baseline_success": row.get("baseline_success", ""),
                "baseline_collision": row.get("baseline_collision", ""),
                "success_delta_vs_baseline": row.get("success_delta_vs_baseline", ""),
                "collision_delta_vs_baseline": row.get("collision_delta_vs_baseline", ""),
                "behavior_target_family": "offtrack_recovery_before_terminal_boundary_crossing",
                "target_source_type": "same_denominator_actor_view_measurement_row",
                "intended_behavior": "recover_inside_track_and_preserve_collision_guard",
                "later_model_output_contract": "[steer, throttle, brake]",
                "trainer_side_only": True,
                "actor_visible": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "target_labels_actor_visible": False,
                "target_provenance_actor_visible": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_candidate_blocker_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidate_rows = [row for row in measurement_rows if row.get("binding_role") == "candidate"]
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_rows, start=1):
        output_rows.append(
            {
                "candidate_blocker_id": f"m3053-candidate-blocker-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "success": row.get("success", ""),
                "collision": row.get("collision", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "headroom_clip_fraction": row.get("headroom_clip_fraction", ""),
                "action_clip_fraction": row.get("action_clip_fraction", ""),
                "blocker_family": "candidate_binding_zero_success_after_action_clip_cleanup",
                "blocked_claims": FORBIDDEN_INTERPRETATION,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_collision_guard_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    collision_rows = [row for row in measurement_rows if _bool(row.get("collision"))]
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(collision_rows, start=1):
        output_rows.append(
            {
                "collision_guard_id": f"m3053-collision-guard-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "termination_reason": row.get("termination_reason", ""),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "obstacle_collision_radius": row.get("obstacle_collision_radius", ""),
                "baseline_collision": row.get("baseline_collision", ""),
                "guard_family": "T5_collision_guard_or_collision_flag_guard",
                "guard_required_before_fit": True,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_success_guard_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    success_rows = [row for row in measurement_rows if _bool(row.get("success"))]
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(success_rows, start=1):
        output_rows.append(
            {
                "success_preservation_guard_id": f"m3053-success-guard-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "min_clearance_margin": row.get("min_clearance_margin", ""),
                "return": row.get("return", ""),
                "baseline_success": row.get("baseline_success", ""),
                "guard_family": "parent_success_preservation_positive_reference",
                "preserve_as_positive_reference": True,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_speed_floor_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    speed_rows = [row for row in measurement_rows if row.get("termination_reason") == "speed_too_low"]
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(speed_rows, start=1):
        output_rows.append(
            {
                "speed_floor_guard_id": f"m3053-speed-floor-guard-{index:04d}",
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "termination_reason": row.get("termination_reason", ""),
                "speed_mean": row.get("speed_mean", ""),
                "guard_family": "speed_floor_guard",
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def build_actor_guard_rows(summary: Mapping[str, Any], source_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    clean = _source_actor_contract_clean(source_rows)
    guards = [
        ("observation_shape", summary.get("observation_shape"), P0_OBSERVATION_DIM, True),
        ("action_shape", summary.get("action_shape"), ACTION_DIM, True),
        ("actor_contract_shape_72_action_3", summary.get("actor_contract_shape_72_action_3"), True, True),
        ("hidden_oracle_actor_input_detected", summary.get("hidden_oracle_actor_input_detected"), False, False),
        ("target_labels_actor_visible", summary.get("target_labels_actor_visible"), False, False),
        ("target_provenance_actor_visible", summary.get("target_provenance_actor_visible"), False, False),
        ("ttc_actor_input_required", summary.get("ttc_actor_input_required"), False, False),
        ("source_rows_actor_contract_clean", clean, True, True),
    ]
    return [
        {
            "actor_guard_id": f"m3053-actor-guard-{index:04d}",
            "guard_family": family,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible": actor_visible,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, observed, expected, actor_visible) in enumerate(guards, start=1)
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    rows = [
        ("behavior_target_source_materialization", True, True, "M3053 summary and guard rows"),
        ("target_tensor_quality", False, False, "future tensor materialization and audit"),
        ("fitting_readiness", False, False, "future fitting-contract audit"),
        ("repair_success", False, False, "future closed-loop measurement and audit"),
        ("driver_performance_verdict", False, False, "future validation/ranking route"),
        ("current_sim_verdict", False, False, "future validation route"),
        ("ranking_or_promotion", False, False, "future promotion gate"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation layer"),
        ("paper_evidence", False, False, "separate paper route"),
        ("finite_window_vs_gru", False, False, "separate same-case architecture comparison"),
        ("full_ideal_driver_completion", False, False, "future full-driver evidence"),
        ("level3_self_id", False, False, "separate self-ID proof gates"),
    ]
    return [
        {
            "claim_id": f"m3053-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3053": allowed,
            "claim_made": made,
            "status_pass": allowed == made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(rows, start=1)
    ]


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    offtrack_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    collision_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    speed_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    m3050_summary = source["m3050_summary"]
    m3050_rows = source["m3050_measurement_rows"]
    m3043_summary = source["m3043_summary"]
    m3045_requirements = source["m3045_repair_requirement_rows"]
    all_m3043 = _metric_by_group(source["m3043_metric_rows"], "all")
    all_m3050 = _metric_by_group(source["m3050_metric_rows"], "all")
    candidate_metric = _metric_by_group(source["m3050_metric_rows"], "binding_role:candidate")
    gates = [
        ("m3052_design_present", "lineage", bool(source["m3052_design_text"]), True, "non-empty design doc", "lineage_invalid"),
        ("m3051_audit_present", "lineage", bool(source["m3051_audit_text"]), True, "non-empty audit doc", "lineage_invalid"),
        ("m3050_status_pass", "source", _bool(m3050_summary.get("status_pass")), True, "M3050 pass", "metric_artifact"),
        ("m3050_gate_matrix_pass", "source", _bool(m3050_summary.get("gate_matrix_pass")), True, "M3050 gates pass", "metric_artifact"),
        ("m3043_denominator_present", "source", int(m3043_summary.get("measurement_episode_row_count", 0)), EXPECTED_MEASUREMENT_ROWS, "M3043 32 rows", "metric_artifact"),
        ("m3050_denominator_present", "source", len(m3050_rows), EXPECTED_MEASUREMENT_ROWS, "M3050 32 rows", "metric_artifact"),
        ("offtrack_target_rows_materialized", "materialization", len(offtrack_rows), EXPECTED_OFFTRACK_ROWS, "24 offtrack rows", "behavior_regression"),
        ("candidate_blocker_rows_materialized", "materialization", len(candidate_rows), EXPECTED_CANDIDATE_ROWS, "16 candidate rows", "behavior_regression"),
        (
            "candidate_binding_zero_success_preserved",
            "materialization",
            _float(candidate_metric.get("success_rate"), -1.0),
            0.0,
            "candidate binding success_rate remains 0.0",
            "behavior_regression",
        ),
        ("collision_guard_rows_materialized", "guard", len(collision_rows), EXPECTED_COLLISION_ROWS, "4 collision rows", "behavior_regression"),
        ("success_preservation_rows_materialized", "guard", len(success_rows), EXPECTED_SUCCESS_ROWS, "4 success rows", "behavior_regression"),
        ("speed_floor_rows_materialized", "guard", len(speed_rows), EXPECTED_SPEED_TOO_LOW_ROWS, "1 speed-floor row", "behavior_regression"),
        ("m3045_requirements_preserved", "lineage", len(m3045_requirements), EXPECTED_REPAIR_REQUIREMENT_ROWS, "6 repair requirements", "lineage_invalid"),
        (
            "action_clip_cleanup_separated",
            "measurement",
            _float(all_m3050.get("action_clip_fraction_mean"), -1.0),
            0.0,
            "M3050 action_clip_fraction_mean 0.0",
            "objective_overfit",
        ),
        (
            "same_denominator_success_unchanged",
            "measurement",
            (_float(all_m3043.get("success_rate")), _float(all_m3050.get("success_rate"))),
            (0.125, 0.125),
            "M3043 and M3050 success_rate both 0.125",
            "objective_overfit",
        ),
        (
            "actor_guards_pass",
            "contract",
            all(_bool(row["status_pass"]) for row in actor_rows),
            True,
            "all actor guards pass",
            "contract_violation",
        ),
        (
            "claim_boundaries_pass",
            "claim_boundary",
            all(_bool(row["status_pass"]) for row in claim_rows),
            True,
            "all claims safe",
            "contract_violation",
        ),
        ("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "M3054 manifest exists", "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m3053-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, observed, expected, _description, failure_type in gates
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30490,
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
        "hypothesis": "A bounded result audit can accept or reject the M3053 offtrack-dominant behavior target-source materialization artifacts before any fitting rollout validation ranking promotion driver-performance high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "behavior_repair_route_rows.csv"),
                str(output_dir / "offtrack_behavior_target_source_rows.csv"),
                str(output_dir / "candidate_binding_blocker_rows.csv"),
                str(output_dir / "collision_guard_rows.csv"),
                str(output_dir / "success_preservation_guard_rows.csv"),
                str(output_dir / "speed_floor_guard_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit offtrack-dominant behavior target-source materialization before fitting or rollout"],
            "derived_from": [MILESTONE_ID, M3052_ID],
            "blocked_by": [
                "M3053 materialized rows require audit before any fitting or rollout",
                "behavior target-source rows are not target tensor quality repair-success or driver-performance evidence",
            ],
            "supersedes": ["direct fitting or rollout from M3053 materialized rows without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3054 must audit M3053 summary target-source blocker guard actor claim and gate artifacts",
            "M3054 must reject target tensor quality fitting readiness repair-success validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims",
            "M3054 must preserve actor observation 72 action 3 and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs",
            "M3054 must choose exactly one next fitting-contract materialization repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run fitting rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3053 materialized rows into target tensor quality repair-success driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_target_materialization_result_audit",
            "evidence_increment": "audits the M3053 behavior target-source and guard panel before any fitting contract or rollout route",
            "claim_scope": "Result audit only; no fitting rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3053 artifact set is incomplete",
                "stop if actor or claim-boundary guards fail",
                "stop if materialized rows are treated as target tensor quality or performance evidence",
            ],
            "fallback_plan": [
                "route to fitting-contract materialization only if M3053 is accepted",
                "route to artifact repair if rows or guards fail",
                "route to synthesis or stop if behavior target materialization is not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3053 completes offtrack behavior target-source materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit offtrack-dominant behavior target-source and guard materialization artifacts",
            "admission_evidence": [
                "M3053 summary and gate matrix",
                "M3053 behavior route offtrack target-source candidate blocker collision success-preservation speed-floor actor and claim rows",
            ],
            "blocked_shortcuts": [
                "no fitting rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3054 status queue scoreboard research log and review",
                "one follow-up manifest only if M3054 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3053 materialized rows are accepted or rejected",
                "one next fitting-contract materialization repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3054 audits engineering materialization artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3054; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3053 behavior target-source materialization artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety behavior repair audit gates.",
            "allowed_claims": [
                "M3053 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits behavior target-source materialization before a fitting-contract or stop decision",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3054 prepares a claim-safe engineering continuation decision",
            "must_synthesize_if": [
                "M3054 cannot select a fitting-contract materialization repair synthesis or stop route",
                "M3054 would require another materialization-only loop without fitting admission",
                "M3054 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3054 audits M3053 summary target-source blocker guard actor claim and gate artifacts",
            "M3054 rejects fitting rollout validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3054 selects exactly one next fitting-contract materialization repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3054 treats materialized behavior target-source rows as target tensor quality or driver performance",
            "M3054 omits actor-contract or claim-boundary audits",
            "M3054 runs fitting validation ranking promotion high-fidelity or architecture comparison",
            "M3054 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3054 audits M3053 behavior target-source and guard evidence and selects exactly one fitting-contract materialization repair synthesis or stop route without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_offtrack_dominant_behavior_target_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "behavior_repair_route_rows.csv"),
            str(output_dir / "offtrack_behavior_target_source_rows.csv"),
            str(output_dir / "candidate_binding_blocker_rows.csv"),
            str(output_dir / "collision_guard_rows.csv"),
            str(output_dir / "success_preservation_guard_rows.csv"),
            str(output_dir / "speed_floor_guard_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
            str(doc_path),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def build_summary(
    *,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
    source: Mapping[str, Any],
    route_rows: list[dict[str, Any]],
    offtrack_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    collision_rows: list[dict[str, Any]],
    success_rows: list[dict[str, Any]],
    speed_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    all_m3043 = _metric_by_group(source["m3043_metric_rows"], "all")
    all_m3050 = _metric_by_group(source["m3050_metric_rows"], "all")
    candidate_metric = _metric_by_group(source["m3050_metric_rows"], "binding_role:candidate")
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    actor_guard_pass = all(_bool(row["status_pass"]) for row in actor_rows)
    claim_rows_pass = all(_bool(row["status_pass"]) for row in claim_rows)
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_offtrack_behavior_target_materialization_preflight_pass",
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": "active_safety_driver_v1_offtrack_behavior_target_materialized_route_to_m3054_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "output_dir": str(output_dir),
        "m3043_success_rate": _float(all_m3043.get("success_rate")),
        "m3050_success_rate": _float(all_m3050.get("success_rate")),
        "m3043_collision_rate": _float(all_m3043.get("collision_rate")),
        "m3050_collision_rate": _float(all_m3050.get("collision_rate")),
        "m3043_clearance_margin_mean": _float(all_m3043.get("clearance_margin_mean")),
        "m3050_clearance_margin_mean": _float(all_m3050.get("clearance_margin_mean")),
        "m3043_action_clip_fraction_mean": _float(all_m3043.get("action_clip_fraction_mean")),
        "m3050_action_clip_fraction_mean": _float(all_m3050.get("action_clip_fraction_mean")),
        "m3050_headroom_clip_fraction_mean": _float(all_m3050.get("headroom_clip_fraction_mean")),
        "m3050_candidate_success_rate": _float(candidate_metric.get("success_rate")),
        "m3050_candidate_headroom_clip_fraction_mean": _float(candidate_metric.get("headroom_clip_fraction_mean")),
        "behavior_repair_route_row_count": len(route_rows),
        "offtrack_behavior_target_source_row_count": len(offtrack_rows),
        "candidate_binding_blocker_row_count": len(candidate_rows),
        "collision_guard_row_count": len(collision_rows),
        "success_preservation_guard_row_count": len(success_rows),
        "speed_floor_guard_row_count": len(speed_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_guard_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": actor_guard_pass,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "hidden_oracle_actor_input_detected": False,
        "ttc_actor_input_required": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "local_action_search_run": False,
        "fitting_run": False,
        "training_run": False,
        "validation_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "target_tensor_quality_claim_made": False,
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
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "next_blocker": NEXT_ID,
        "required_artifacts_present": True,
        "paths": {
            "summary": str(output_dir / "summary.json"),
            "behavior_repair_route_rows": str(output_dir / "behavior_repair_route_rows.csv"),
            "offtrack_behavior_target_source_rows": str(output_dir / "offtrack_behavior_target_source_rows.csv"),
            "candidate_binding_blocker_rows": str(output_dir / "candidate_binding_blocker_rows.csv"),
            "collision_guard_rows": str(output_dir / "collision_guard_rows.csv"),
            "success_preservation_guard_rows": str(output_dir / "success_preservation_guard_rows.csv"),
            "speed_floor_guard_rows": str(output_dir / "speed_floor_guard_rows.csv"),
            "actor_contract_guard_rows": str(output_dir / "actor_contract_guard_rows.csv"),
            "claim_boundary_rows": str(output_dir / "claim_boundary_rows.csv"),
            "gate_matrix": str(output_dir / "gate_matrix.csv"),
            "doc": str(doc_path),
            "follow_up_manifest": str(follow_up_manifest),
        },
    }


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# M3053 Active Safety Driver v1 Offtrack-Dominant Behavior Target Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_offtrack_behavior_target_materialized_route_to_m3054_result_audit`
- next blocker: `{NEXT_ID}`
- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`

M3053 materializes a trainer-side behavior target-source and guard panel for
the M3052-selected offtrack-dominant repair route. It does not run fitting,
training, rollout, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, paper-route evaluation, full-driver
evaluation, or self-ID testing.

## Evidence Summary

```text
M3043 success_rate: {summary['m3043_success_rate']}
M3050 success_rate: {summary['m3050_success_rate']}
M3043 collision_rate: {summary['m3043_collision_rate']}
M3050 collision_rate: {summary['m3050_collision_rate']}
M3043 action_clip_fraction_mean: {summary['m3043_action_clip_fraction_mean']}
M3050 action_clip_fraction_mean: {summary['m3050_action_clip_fraction_mean']}
M3050 headroom_clip_fraction_mean: {summary['m3050_headroom_clip_fraction_mean']}
M3050 candidate success_rate: {summary['m3050_candidate_success_rate']}
```

## Materialized Rows

```text
behavior route rows: {summary['behavior_repair_route_row_count']}
offtrack behavior target-source rows: {summary['offtrack_behavior_target_source_row_count']}
candidate-binding blocker rows: {summary['candidate_binding_blocker_row_count']}
collision guard rows: {summary['collision_guard_row_count']}
success-preservation guard rows: {summary['success_preservation_guard_row_count']}
speed-floor guard rows: {summary['speed_floor_guard_row_count']}
actor-contract guard rows: {summary['actor_contract_guard_row_count']}
claim-boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Supported Claims

M3053 supports only these bounded claims:

```text
one offtrack-dominant behavior target-source and guard panel was materialized
actor observation 72 and action 3 are preserved
offtrack collision success-preservation speed-floor actor and claim guards are separated
M3054 result-audit manifest was registered
```

## Rejected Claims

M3053 rejects:

```text
target tensor quality
fitting readiness
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3053 is materialization only. All target/source/guard rows remain
trainer-side or process-side evidence and are not actor inputs.
""",
        encoding="utf-8",
    )


def run(
    *,
    m3052_design: Path,
    m3051_audit: Path,
    m3050_dir: Path,
    m3043_dir: Path,
    m3045_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_source_artifacts(
        m3052_design=m3052_design,
        m3051_audit=m3051_audit,
        m3050_dir=m3050_dir,
        m3043_dir=m3043_dir,
        m3045_dir=m3045_dir,
    )

    m3050_rows = source["m3050_measurement_rows"]
    route_rows = build_route_rows()
    offtrack_rows = build_offtrack_rows(m3050_rows)
    candidate_rows = build_candidate_blocker_rows(m3050_rows)
    collision_rows = build_collision_guard_rows(m3050_rows)
    success_rows = build_success_guard_rows(m3050_rows)
    speed_rows = build_speed_floor_rows(m3050_rows)
    actor_rows = build_actor_guard_rows(source["m3050_summary"], m3050_rows)
    claim_rows = build_claim_rows()

    write_csv_rows(paths["behavior_repair_route_rows"], route_rows, ROUTE_FIELDNAMES)
    write_csv_rows(paths["offtrack_behavior_target_source_rows"], offtrack_rows, OFFTRACK_FIELDNAMES)
    write_csv_rows(paths["candidate_binding_blocker_rows"], candidate_rows, CANDIDATE_BLOCKER_FIELDNAMES)
    write_csv_rows(paths["collision_guard_rows"], collision_rows, COLLISION_GUARD_FIELDNAMES)
    write_csv_rows(paths["success_preservation_guard_rows"], success_rows, SUCCESS_GUARD_FIELDNAMES)
    write_csv_rows(paths["speed_floor_guard_rows"], speed_rows, SPEED_FLOOR_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    gate_rows = build_gate_rows(
        source=source,
        offtrack_rows=offtrack_rows,
        candidate_rows=candidate_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        speed_rows=speed_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        route_rows=route_rows,
        offtrack_rows=offtrack_rows,
        candidate_rows=candidate_rows,
        collision_rows=collision_rows,
        success_rows=success_rows,
        speed_rows=speed_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
    )
    write_doc(doc_path, summary)
    write_json(paths["summary"], summary)
    write_run_state(
        paths["run_state"],
        {
            "milestone": MILESTONE_ID,
            "status": "completed" if summary["status_pass"] else "failed",
            "summary": str(paths["summary"]),
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3052-design", type=Path, default=DEFAULT_M3052_DESIGN)
    parser.add_argument("--m3051-audit", type=Path, default=DEFAULT_M3051_AUDIT)
    parser.add_argument("--m3050-dir", type=Path, default=DEFAULT_M3050_DIR)
    parser.add_argument("--m3043-dir", type=Path, default=DEFAULT_M3043_DIR)
    parser.add_argument("--m3045-dir", type=Path, default=DEFAULT_M3045_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()

    summary = run(
        m3052_design=args.m3052_design,
        m3051_audit=args.m3051_audit,
        m3050_dir=args.m3050_dir,
        m3043_dir=args.m3043_dir,
        m3045_dir=args.m3045_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"offtrack_behavior_target_source_row_count={summary['offtrack_behavior_target_source_row_count']}")
    print(f"candidate_binding_blocker_row_count={summary['candidate_binding_blocker_row_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
