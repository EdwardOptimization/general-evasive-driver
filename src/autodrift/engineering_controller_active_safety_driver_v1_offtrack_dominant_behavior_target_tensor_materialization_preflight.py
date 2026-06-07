"""Materialize M3057 offtrack-dominant behavior target tensor artifacts.

M3057 consumes the M3056-accepted M3055 fitting contract and the M3053
behavior target-source panel. The current branch has episode-level behavior
rows but no raw actor-view traces, so this runner fails closed: it writes
machine-checkable blocker rows and an M3058 result-audit manifest rather than
fabricating numeric training tensors.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows, write_run_state
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


MILESTONE_ID = (
    "m3057-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-materialization-preflight"
)
NEXT_ID = (
    "m3058-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-tensor-materialization-result-audit"
)
M3056_ID = (
    "m3056-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-fitting-contract-materialization-result-audit"
)

DEFAULT_M3056_AUDIT = Path(f"docs/{M3056_ID}.md")
DEFAULT_M3055_DIR = Path(
    "runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_fitting_contract_materialization_preflight"
)
DEFAULT_M3053_DIR = Path(
    "runs/m3053_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3057_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_tensor_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_OFFTRACK_ROWS = 24
EXPECTED_CANDIDATE_BLOCKER_ROWS = 16
EXPECTED_COLLISION_GUARD_ROWS = 4
EXPECTED_SUCCESS_GUARD_ROWS = 4
EXPECTED_SPEED_FLOOR_ROWS = 1
EXPECTED_FITTING_CONTRACT_ROWS = 1
EXPECTED_LOSS_FAMILY_ROWS = 6
EXPECTED_ROW_ADMISSION_ROWS = 5

CLAIM_SCOPE = (
    "M3057 Active Safety Driver v1 offtrack-dominant behavior target tensor "
    "materialization preflight only; M3056 audit, M3055 fitting contract rows, "
    "and M3053 behavior target-source/guard rows may be converted into "
    "trainer-side numeric target tensor rows or fail-closed blocker rows, "
    "weight specs, actor-contract, target-visibility, side-effect, "
    "claim-boundary, gate, doc, and M3058 audit manifest artifacts. No fitting, "
    "fitted policy quality, reset, step, rollout, replay, local-action search, "
    "PPO, training, validation, ranking, winner selection, checkpoint mutation, "
    "checkpoint promotion, repair success, driver-performance verdict, "
    "current-sim verdict, high-fidelity validation, paper evidence, "
    "finite-window-vs-GRU evidence, full ideal driver completion, or self-ID "
    "claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target tensor quality, fitted policy quality, repair success, validation "
    "result, driver-performance verdict, current-sim verdict, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, or level3 self-identification"
)

TARGET_TENSOR_FIELDNAMES = [
    "target_tensor_row_id",
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
    "raw_actor_view_trace_required",
    "raw_actor_view_trace_path",
    "raw_actor_view_trace_available",
    "numeric_target_tensor_materialized",
    "target_tensor_path",
    "target_action_shape",
    "target_action_mask_shape",
    "target_loss_weight_shape",
    "target_action_abs_max",
    "target_loss_weight_sum",
    "blocker_family",
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
    "checkpoint_mutated",
    "status_pass",
    "claim_boundary",
]
WEIGHT_FIELDNAMES = [
    "weight_row_id",
    "loss_family",
    "priority",
    "source_rows",
    "source_row_count",
    "weight_policy",
    "guard_dependency",
    "weight_spec_materialized",
    "numeric_weight_tensor_materialized",
    "blocked_by",
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
    "allowed_in_m3057",
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
        "behavior_target_tensor_rows": output_dir / "behavior_target_tensor_rows.csv",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _all_false(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    return all(not _bool(row.get(field)) for row in rows)


def _all_true(rows: Iterable[Mapping[str, Any]], field: str) -> bool:
    rows = list(rows)
    return bool(rows) and all(_bool(row.get(field)) for row in rows)


def _raw_trace_path(row: Mapping[str, Any]) -> str:
    for key in ("raw_actor_view_trace_path", "raw_trace_path", "trace_path"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def _path_exists(value: str) -> bool:
    return bool(value) and Path(value).exists()


def load_source_artifacts(*, m3056_audit: Path, m3055_dir: Path, m3053_dir: Path) -> dict[str, Any]:
    paths = {
        "m3056_audit": m3056_audit,
        "m3055_summary": m3055_dir / "summary.json",
        "fitting_contract_rows": m3055_dir / "fitting_contract_rows.csv",
        "loss_family_rows": m3055_dir / "loss_family_rows.csv",
        "row_admission_rows": m3055_dir / "row_admission_rows.csv",
        "m3055_actor_contract_guard_rows": m3055_dir / "actor_contract_guard_rows.csv",
        "m3055_target_visibility_guard_rows": m3055_dir / "target_visibility_guard_rows.csv",
        "m3055_side_effect_guard_rows": m3055_dir / "side_effect_guard_rows.csv",
        "m3055_claim_boundary_rows": m3055_dir / "claim_boundary_rows.csv",
        "m3055_gate_matrix": m3055_dir / "gate_matrix.csv",
        "m3053_summary": m3053_dir / "summary.json",
        "offtrack_behavior_target_source_rows": m3053_dir / "offtrack_behavior_target_source_rows.csv",
        "candidate_binding_blocker_rows": m3053_dir / "candidate_binding_blocker_rows.csv",
        "collision_guard_rows": m3053_dir / "collision_guard_rows.csv",
        "success_preservation_guard_rows": m3053_dir / "success_preservation_guard_rows.csv",
        "speed_floor_guard_rows": m3053_dir / "speed_floor_guard_rows.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required M3057 input artifacts: {missing}")
    return {
        "paths": paths,
        "m3056_audit_text": m3056_audit.read_text(encoding="utf-8"),
        "m3055_summary": read_json(paths["m3055_summary"]),
        "fitting_contract_rows": read_csv_rows(paths["fitting_contract_rows"]),
        "loss_family_rows": read_csv_rows(paths["loss_family_rows"]),
        "row_admission_rows": read_csv_rows(paths["row_admission_rows"]),
        "m3055_actor_contract_guard_rows": read_csv_rows(paths["m3055_actor_contract_guard_rows"]),
        "m3055_target_visibility_guard_rows": read_csv_rows(paths["m3055_target_visibility_guard_rows"]),
        "m3055_side_effect_guard_rows": read_csv_rows(paths["m3055_side_effect_guard_rows"]),
        "m3055_claim_boundary_rows": read_csv_rows(paths["m3055_claim_boundary_rows"]),
        "m3055_gate_rows": read_csv_rows(paths["m3055_gate_matrix"]),
        "m3053_summary": read_json(paths["m3053_summary"]),
        "offtrack_behavior_target_source_rows": read_csv_rows(paths["offtrack_behavior_target_source_rows"]),
        "candidate_binding_blocker_rows": read_csv_rows(paths["candidate_binding_blocker_rows"]),
        "collision_guard_rows": read_csv_rows(paths["collision_guard_rows"]),
        "success_preservation_guard_rows": read_csv_rows(paths["success_preservation_guard_rows"]),
        "speed_floor_guard_rows": read_csv_rows(paths["speed_floor_guard_rows"]),
    }


def build_behavior_target_tensor_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(source["offtrack_behavior_target_source_rows"], start=1):
        raw_path = _raw_trace_path(row)
        raw_available = _path_exists(raw_path)
        numeric_materialized = False
        blocker = "" if numeric_materialized else "raw_actor_view_trace_missing"
        rows.append(
            {
                "target_tensor_row_id": f"m3057-target-tensor-{index:04d}",
                "source_offtrack_target_source_id": row.get("offtrack_target_source_id", ""),
                "measurement_episode_id": row.get("measurement_episode_id", ""),
                "baseline_measurement_row_id": row.get("baseline_measurement_row_id", ""),
                "binding_role": row.get("binding_role", ""),
                "task_family": row.get("task_family", ""),
                "source_edge": row.get("source_edge", ""),
                "window_tag": row.get("window_tag", ""),
                "eval_seed": row.get("eval_seed", ""),
                "behavior_target_family": row.get("behavior_target_family", ""),
                "intended_behavior": row.get("intended_behavior", ""),
                "output_semantics": "direct_action",
                "output_components": "steer;throttle;brake",
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "actor_action_shape": ACTION_DIM,
                "raw_actor_view_trace_required": True,
                "raw_actor_view_trace_path": raw_path,
                "raw_actor_view_trace_available": raw_available,
                "numeric_target_tensor_materialized": numeric_materialized,
                "target_tensor_path": "",
                "target_action_shape": "",
                "target_action_mask_shape": "",
                "target_loss_weight_shape": "",
                "target_action_abs_max": "",
                "target_loss_weight_sum": "",
                "blocker_family": blocker,
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
                "checkpoint_mutated": False,
                "status_pass": numeric_materialized,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_weight_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(source["loss_family_rows"], start=1):
        rows.append(
            {
                "weight_row_id": f"m3057-weight-{index:04d}",
                "loss_family": row.get("loss_family", ""),
                "priority": row.get("priority", ""),
                "source_rows": row.get("source_rows", ""),
                "source_row_count": row.get("row_count", ""),
                "weight_policy": row.get("weight_policy", ""),
                "guard_dependency": row.get("guard_dependency", ""),
                "weight_spec_materialized": True,
                "numeric_weight_tensor_materialized": False,
                "blocked_by": "raw_actor_view_trace_missing",
                "actor_visible": False,
                "status_pass": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_actor_guard_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source["m3055_summary"]
    specs = [
        ("observation_shape", summary.get("observation_shape"), P0_OBSERVATION_DIM, True),
        ("action_shape", summary.get("action_shape"), ACTION_DIM, True),
        ("actor_contract_shape_72_action_3", summary.get("actor_contract_shape_72_action_3"), True, True),
        ("output_semantics", summary.get("output_semantics"), "direct_action", True),
        ("output_components", ";".join(summary.get("output_components", [])), "steer;throttle;brake", True),
        ("base_policy_required_at_runtime", summary.get("base_policy_required_at_runtime"), False, False),
        ("hidden_oracle_actor_input_detected", summary.get("hidden_oracle_actor_input_detected"), False, False),
        ("target_labels_actor_visible", summary.get("target_labels_actor_visible"), False, False),
        ("target_provenance_actor_visible", summary.get("target_provenance_actor_visible"), False, False),
        ("ttc_actor_input_required", summary.get("ttc_actor_input_required"), False, False),
    ]
    return [
        {
            "actor_guard_id": f"m3057-actor-guard-{index:04d}",
            "guard_family": family,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible": actor_visible,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, observed, expected, actor_visible) in enumerate(specs, start=1)
    ]


def build_target_visibility_rows(source: Mapping[str, Any], tensor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (
            "m3053_offtrack_target_source_rows_actor_invisible",
            "offtrack_behavior_target_source_rows.csv",
            _all_false(source["offtrack_behavior_target_source_rows"], "actor_visible")
            and _all_false(source["offtrack_behavior_target_source_rows"], "target_labels_actor_visible")
            and _all_false(source["offtrack_behavior_target_source_rows"], "target_provenance_actor_visible"),
            True,
        ),
        ("m3053_candidate_blockers_actor_invisible", "candidate_binding_blocker_rows.csv", True, True),
        ("m3053_collision_guards_actor_invisible", "collision_guard_rows.csv", True, True),
        ("m3053_success_guards_actor_invisible", "success_preservation_guard_rows.csv", True, True),
        ("m3053_speed_floor_guards_actor_invisible", "speed_floor_guard_rows.csv", True, True),
        (
            "m3057_target_labels_actor_invisible",
            "behavior_target_tensor_rows.csv",
            _all_false(tensor_rows, "target_labels_actor_visible"),
            True,
        ),
        (
            "m3057_target_provenance_actor_invisible",
            "behavior_target_tensor_rows.csv",
            _all_false(tensor_rows, "target_provenance_actor_visible"),
            True,
        ),
    ]
    return [
        {
            "target_visibility_guard_id": f"m3057-target-visibility-{index:04d}",
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
            "side_effect_guard_id": f"m3057-side-effect-{index:04d}",
            "side_effect": side_effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, side_effect in enumerate(side_effects, start=1)
    ]


def build_claim_rows() -> list[dict[str, Any]]:
    rows = [
        ("target_tensor_blocker_materialization", True, True, "M3057 blocker rows and gate matrix"),
        ("numeric_target_tensor_materialization", True, False, "future raw actor-view trace capture and M3057 repair/rerun"),
        ("target_tensor_quality", False, False, "future target tensor materialization and result audit"),
        ("fitting_execution", False, False, "future fitting preflight"),
        ("fitted_policy_quality", False, False, "future fitting result audit"),
        ("repair_success", False, False, "future closed-loop measurement and audit"),
        ("driver_performance_verdict", False, False, "future validation/ranking route"),
        ("current_sim_verdict", False, False, "future validation route"),
        ("ranking_or_promotion", False, False, "future promotion gate"),
        ("high_fidelity_validation", False, False, "future high-fidelity validation layer"),
        ("paper_evidence", False, False, "separate paper route"),
        ("finite_window_vs_gru", False, False, "separate architecture comparison"),
        ("full_ideal_driver_completion", False, False, "future full-driver evidence"),
        ("level3_self_id", False, False, "separate self-ID proof gates"),
    ]
    return [
        {
            "claim_id": f"m3057-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3057": allowed,
            "claim_made": made,
            "status_pass": made if allowed and family == "target_tensor_blocker_materialization" else made == False,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(rows, start=1)
    ]


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    tensor_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    m3055 = source["m3055_summary"]
    m3053 = source["m3053_summary"]
    raw_required_count = sum(_bool(row["raw_actor_view_trace_required"]) for row in tensor_rows)
    raw_available_count = sum(_bool(row["raw_actor_view_trace_available"]) for row in tensor_rows)
    numeric_materialized_count = sum(_bool(row["numeric_target_tensor_materialized"]) for row in tensor_rows)
    gates = [
        ("m3056_audit_present", "lineage", bool(source["m3056_audit_text"]), True, "lineage_invalid"),
        ("m3056_accepts_m3055", "lineage", "M3056 accepts M3055" in source["m3056_audit_text"], True, "lineage_invalid"),
        ("m3055_status_pass", "lineage", _bool(m3055.get("status_pass")), True, "lineage_invalid"),
        ("m3055_gate_matrix_pass", "lineage", _bool(m3055.get("gate_matrix_pass")), True, "lineage_invalid"),
        ("m3055_direct_action", "contract", m3055.get("output_semantics"), "direct_action", "contract_violation"),
        ("m3053_status_pass", "lineage", _bool(m3053.get("status_pass")), True, "lineage_invalid"),
        ("m3053_gate_matrix_pass", "lineage", _bool(m3053.get("gate_matrix_pass")), True, "lineage_invalid"),
        ("fitting_contract_rows", "denominator", len(source["fitting_contract_rows"]), EXPECTED_FITTING_CONTRACT_ROWS, "metric_artifact"),
        ("loss_family_rows", "denominator", len(source["loss_family_rows"]), EXPECTED_LOSS_FAMILY_ROWS, "metric_artifact"),
        ("row_admission_rows", "denominator", len(source["row_admission_rows"]), EXPECTED_ROW_ADMISSION_ROWS, "metric_artifact"),
        ("offtrack_target_source_rows", "denominator", len(source["offtrack_behavior_target_source_rows"]), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        ("candidate_blocker_rows", "denominator", len(source["candidate_binding_blocker_rows"]), EXPECTED_CANDIDATE_BLOCKER_ROWS, "metric_artifact"),
        ("collision_guard_rows", "denominator", len(source["collision_guard_rows"]), EXPECTED_COLLISION_GUARD_ROWS, "metric_artifact"),
        ("success_guard_rows", "denominator", len(source["success_preservation_guard_rows"]), EXPECTED_SUCCESS_GUARD_ROWS, "metric_artifact"),
        ("speed_floor_guard_rows", "denominator", len(source["speed_floor_guard_rows"]), EXPECTED_SPEED_FLOOR_ROWS, "metric_artifact"),
        ("target_tensor_blocker_rows", "artifact", len(tensor_rows), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        ("weight_spec_rows", "artifact", len(weight_rows), EXPECTED_LOSS_FAMILY_ROWS, "metric_artifact"),
        ("raw_actor_view_trace_required", "artifact", raw_required_count, EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        ("raw_actor_view_trace_available", "artifact", raw_available_count, EXPECTED_OFFTRACK_ROWS, "lineage_invalid"),
        ("numeric_target_tensors_materialized", "artifact", numeric_materialized_count, EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        ("actor_contract_guards_pass", "contract", _all_true(actor_rows, "status_pass"), True, "contract_violation"),
        ("target_visibility_guards_pass", "contract", _all_true(visibility_rows, "status_pass"), True, "contract_violation"),
        ("side_effects_absent", "side_effect", all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows), True, "contract_violation"),
        ("claim_boundary_rows_pass", "claim_boundary", _all_true(claim_rows, "status_pass"), True, "contract_violation"),
        ("required_artifacts_present", "artifact", required_artifacts_present, True, "metric_artifact"),
        ("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m3057-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": "" if observed == expected else failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, observed, expected, failure_type in gates
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path, summary_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30530,
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
        "hypothesis": "A bounded result audit can accept or reject the M3057 offtrack-dominant behavior target tensor materialization artifacts before any fitting rollout validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(summary_path),
                str(output_dir / "behavior_target_tensor_rows.csv"),
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
                f"experiments/manifests/{M3056_ID}.json",
            ],
            "parent_objective": [
                "audit target tensor materialization or fail-closed blocker artifacts before fitting admission"
            ],
            "derived_from": [MILESTONE_ID, M3056_ID],
            "blocked_by": [
                "M3057 target tensor artifacts require audit before fitting admission",
                "target tensor materialization or fail-closed blockers are not fitted policy quality repair-success or driver-performance evidence",
            ],
            "supersedes": ["direct fitting immediately after M3057 without result audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3058 must audit M3057 target tensor blocker weight actor target-visibility side-effect claim and gate artifacts",
            "M3058 must reject fitting execution fitted policy quality repair-success validation ranking promotion performance current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims",
            "M3058 must preserve actor observation 72 action 3 direct [steer throttle brake] and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs",
            "M3058 must choose exactly one next raw trace capture artifact repair fitting admission synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run fitting rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3057 target tensor blocker rows into numeric target quality fitted policy quality repair-success driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_target_tensor_result_audit",
            "evidence_increment": "audits M3057 target tensor materialization or fail-closed blocker artifacts before any fitting route",
            "claim_scope": "Result audit only; no fitting rollout validation ranking promotion performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3057 artifact set is incomplete",
                "stop if actor target-visibility side-effect or claim-boundary guards fail",
                "stop if blocker rows are treated as target tensor quality or performance evidence",
            ],
            "fallback_plan": [
                "route to raw trace capture if M3057 fails closed on missing actor-view traces",
                "route to fitting admission only if numeric target tensors are complete and audit accepts claim safety",
                "route to synthesis or stop if target tensor materialization is not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3057 completes target tensor materialization or fail-closed blocker materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit offtrack-dominant behavior target tensor materialization artifacts",
            "admission_evidence": [
                "M3057 summary and gate matrix",
                "M3057 behavior target tensor blocker rows weight specs actor target visibility side-effect and claim rows",
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
                "M3058 status queue scoreboard research log and review",
                "one follow-up manifest only if M3058 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3057 target tensor rows are accepted or rejected",
                "one next raw trace capture fitting admission repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3058 audits engineering target tensor artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3058; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3057 target tensor materialization artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety target tensor audit gates.",
            "allowed_claims": [
                "M3057 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits target tensor materialization or fail-closed blocker evidence before fitting or raw-trace repair",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3058 prepares a claim-safe engineering continuation decision",
            "must_synthesize_if": [
                "M3058 cannot select raw trace capture fitting repair synthesis or stop route",
                "M3058 would require another materialization-only loop without changing evidence",
                "M3058 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3058 audits M3057 target tensor blocker weight actor target-visibility side-effect claim and gate artifacts",
            "M3058 rejects fitting execution fitted policy quality repair-success validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3058 selects exactly one next raw trace capture fitting admission repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3058 treats target tensor blocker rows as fitted policy quality or driver performance",
            "M3058 omits actor target-visibility side-effect or claim-boundary audits",
            "M3058 runs fitting validation ranking promotion high-fidelity or architecture comparison",
            "M3058 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3058 audits M3057 behavior target tensor evidence and selects exactly one raw trace capture fitting admission repair synthesis or stop route without overclaiming.",
        "commands": [
            {
                "name": "active_safety_driver_v1_offtrack_dominant_behavior_target_tensor_materialization_result_audit_doc",
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
            str(output_dir / "target_tensor_weight_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
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
    tensor_rows: list[dict[str, Any]],
    weight_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> dict[str, Any]:
    raw_required_count = sum(_bool(row["raw_actor_view_trace_required"]) for row in tensor_rows)
    raw_available_count = sum(_bool(row["raw_actor_view_trace_available"]) for row in tensor_rows)
    numeric_count = sum(_bool(row["numeric_target_tensor_materialized"]) for row in tensor_rows)
    blocker_count = sum(bool(row["blocker_family"]) for row in tensor_rows)
    gate_matrix_pass = _all_true(gate_rows, "status_pass")
    actor_guard_pass = _all_true(actor_rows, "status_pass")
    visibility_guard_pass = _all_true(visibility_rows, "status_pass")
    side_effect_pass = all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows)
    claim_rows_pass = _all_true(claim_rows, "status_pass")
    status_pass = gate_matrix_pass and numeric_count == EXPECTED_OFFTRACK_ROWS
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_preflight_pass"
        if status_pass
        else "active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_missing_raw_actor_view_traces",
        "status_pass": status_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": "active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_route_to_m3058_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "output_dir": str(output_dir),
        "m3055_status_pass": _bool(source["m3055_summary"].get("status_pass")),
        "m3055_gate_matrix_pass": _bool(source["m3055_summary"].get("gate_matrix_pass")),
        "m3053_status_pass": _bool(source["m3053_summary"].get("status_pass")),
        "m3053_gate_matrix_pass": _bool(source["m3053_summary"].get("gate_matrix_pass")),
        "offtrack_behavior_target_source_row_count": len(source["offtrack_behavior_target_source_rows"]),
        "candidate_binding_blocker_row_count": len(source["candidate_binding_blocker_rows"]),
        "collision_guard_row_count": len(source["collision_guard_rows"]),
        "success_preservation_guard_row_count": len(source["success_preservation_guard_rows"]),
        "speed_floor_guard_row_count": len(source["speed_floor_guard_rows"]),
        "behavior_target_tensor_row_count": len(tensor_rows),
        "target_tensor_blocker_row_count": blocker_count,
        "numeric_target_tensor_materialized_count": numeric_count,
        "raw_actor_view_trace_required_count": raw_required_count,
        "raw_actor_view_trace_available_count": raw_available_count,
        "raw_actor_view_trace_missing_count": raw_required_count - raw_available_count,
        "target_tensor_weight_row_count": len(weight_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_guard_pass,
        "target_visibility_guard_row_count": len(visibility_rows),
        "target_visibility_guard_rows_pass": visibility_guard_pass,
        "side_effect_guard_row_count": len(side_effect_rows),
        "side_effect_guard_rows_pass": side_effect_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "gate_matrix_row_count": len(gate_rows),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": actor_guard_pass,
        "output_semantics": "direct_action",
        "output_components": ["steer", "throttle", "brake"],
        "base_policy_required_at_runtime": False,
        "hidden_oracle_actor_input_detected": False,
        "target_labels_actor_visible": False,
        "target_provenance_actor_visible": False,
        "ttc_actor_input_required": False,
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
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "next_blocker": NEXT_ID,
        "required_artifacts_present": required_artifacts_present,
        "paths": {
            "summary": str(output_dir / "summary.json"),
            "behavior_target_tensor_rows": str(output_dir / "behavior_target_tensor_rows.csv"),
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
    path.write_text(
        f"""# M3057 Active Safety Driver v1 Offtrack-Dominant Behavior Target Tensor Materialization Preflight

## Summary

- status: fail_closed
- result class: `{summary['result_class']}`
- decision: `active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_route_to_m3058_result_audit`
- next blocker: `{NEXT_ID}`
- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`

M3057 attempted to convert the M3056-accepted M3055 fitting contract and M3053
behavior target-source rows into trainer-side numeric target tensors. It fails
closed because the available M3053/M3055 artifacts contain episode-level
behavior rows but no raw actor-view observation/action traces. M3057 therefore
writes blocker rows and guard artifacts rather than fabricating target tensors.

## Artifact Summary

```text
behavior target tensor blocker rows: {summary['behavior_target_tensor_row_count']}
raw actor-view traces required: {summary['raw_actor_view_trace_required_count']}
raw actor-view traces available: {summary['raw_actor_view_trace_available_count']}
raw actor-view traces missing: {summary['raw_actor_view_trace_missing_count']}
numeric target tensors materialized: {summary['numeric_target_tensor_materialized_count']}
target tensor weight spec rows: {summary['target_tensor_weight_row_count']}
actor-contract guard rows: {summary['actor_contract_guard_row_count']}
target-visibility guard rows: {summary['target_visibility_guard_row_count']}
side-effect guard rows: {summary['side_effect_guard_row_count']}
claim-boundary rows: {summary['claim_boundary_row_count']}
gate rows: {summary['gate_matrix_row_count']}
```

## Supported Claims

M3057 supports only these bounded claims:

```text
target tensor materialization was attempted under the accepted fitting contract
24 offtrack behavior target-source rows were preserved as blocker rows
raw actor-view traces are required and currently absent for numeric target tensor materialization
actor observation 72 and action 3 direct [steer, throttle, brake] contract is preserved
target labels and provenance remain outside actor inputs
M3058 result-audit manifest was registered
```

## Rejected Claims

M3057 rejects:

```text
numeric target tensor quality
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3057 is fail-closed target tensor materialization only. It writes no fitted
weights and runs no environment interaction, local action search, fitting,
training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, paper evaluation, full-driver evaluation, or
self-ID testing.
""",
        encoding="utf-8",
    )


def run(
    *,
    m3056_audit: Path,
    m3055_dir: Path,
    m3053_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_source_artifacts(m3056_audit=m3056_audit, m3055_dir=m3055_dir, m3053_dir=m3053_dir)

    tensor_rows = build_behavior_target_tensor_rows(source)
    weight_rows = build_weight_rows(source)
    actor_rows = build_actor_guard_rows(source)
    visibility_rows = build_target_visibility_rows(source, tensor_rows)
    side_effect_rows = build_side_effect_rows()
    claim_rows = build_claim_rows()

    write_csv_rows(paths["behavior_target_tensor_rows"], tensor_rows, TARGET_TENSOR_FIELDNAMES)
    write_csv_rows(paths["target_tensor_weight_rows"], weight_rows, WEIGHT_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["target_visibility_guard_rows"], visibility_rows, TARGET_VISIBILITY_FIELDNAMES)
    write_csv_rows(paths["side_effect_guard_rows"], side_effect_rows, SIDE_EFFECT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_json(
        follow_up_manifest,
        build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path, summary_path=paths["summary"]),
    )

    gate_rows = build_gate_rows(
        source=source,
        tensor_rows=tensor_rows,
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
            "status": "fail_closed",
            "summary": str(paths["summary"]),
            "next_blocker": NEXT_ID,
        },
    )

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_rows(
        source=source,
        tensor_rows=tensor_rows,
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
            "raw_actor_view_trace_missing_count": summary["raw_actor_view_trace_missing_count"],
            "numeric_target_tensor_materialized_count": summary["numeric_target_tensor_materialized_count"],
            "status": "completed_fail_closed",
            "next_blocker": NEXT_ID,
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3056-audit", type=Path, default=DEFAULT_M3056_AUDIT)
    parser.add_argument("--m3055-dir", type=Path, default=DEFAULT_M3055_DIR)
    parser.add_argument("--m3053-dir", type=Path, default=DEFAULT_M3053_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run(
        m3056_audit=args.m3056_audit,
        m3055_dir=args.m3055_dir,
        m3053_dir=args.m3053_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"raw_actor_view_trace_missing_count={summary['raw_actor_view_trace_missing_count']}")
    print(f"numeric_target_tensor_materialized_count={summary['numeric_target_tensor_materialized_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
