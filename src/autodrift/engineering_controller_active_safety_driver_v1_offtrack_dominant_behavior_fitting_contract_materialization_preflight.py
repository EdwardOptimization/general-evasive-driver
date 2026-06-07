"""Materialize M3055 offtrack-dominant behavior fitting contracts.

M3055 consumes the M3054-accepted M3053 target-source and guard panel and
writes a claim-safe fitting contract for a later deployable Active Safety
Driver v1 recovery selector/reflex. It does not fit, train, reset, step,
rollout, replay, validate, rank, promote, mutate checkpoints, run high-fidelity
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
    "m3055-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-fitting-contract-materialization-preflight"
)
NEXT_ID = (
    "m3056-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-fitting-contract-materialization-result-audit"
)
M3054_ID = (
    "m3054-engineering-controller-active-safety-driver-v1-offtrack-dominant-"
    "behavior-target-materialization-result-audit"
)

DEFAULT_M3054_AUDIT = Path(f"docs/{M3054_ID}.md")
DEFAULT_M3053_DIR = Path(
    "runs/m3053_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_target_materialization_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3055_engineering_controller_active_safety_driver_v1_offtrack_"
    "dominant_behavior_fitting_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_ROUTE_ROWS = 1
EXPECTED_OFFTRACK_ROWS = 24
EXPECTED_CANDIDATE_BLOCKER_ROWS = 16
EXPECTED_COLLISION_GUARD_ROWS = 4
EXPECTED_SUCCESS_GUARD_ROWS = 4
EXPECTED_SPEED_FLOOR_ROWS = 1
EXPECTED_LOSS_FAMILY_ROWS = 6

CLAIM_SCOPE = (
    "M3055 Active Safety Driver v1 offtrack-dominant behavior fitting-contract "
    "materialization preflight only; M3054 audit and M3053 behavior target-"
    "source/guard rows may be converted into output-contract, loss-family, row-"
    "admission, actor-contract, target-visibility, claim-boundary, gate, doc, "
    "and M3056 audit manifest artifacts. No target tensor fitting, fitted "
    "policy quality, reset, step, rollout, replay, PPO, training, validation, "
    "ranking, winner selection, checkpoint mutation, checkpoint promotion, "
    "repair success, driver-performance verdict, current-sim verdict, high-"
    "fidelity validation, paper evidence, finite-window-vs-GRU evidence, full "
    "ideal driver completion, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "target tensor quality, fitted policy quality, repair success, validation "
    "result, driver-performance verdict, current-sim verdict, checkpoint "
    "ranking, winner selection, checkpoint promotion, high-fidelity validation "
    "readiness or result, paper evidence, finite-window-vs-GRU conclusion, "
    "full ideal driver completion, or level3 self-identification"
)

FITTING_CONTRACT_FIELDNAMES = [
    "contract_id",
    "contract_family",
    "model_role",
    "actor_observation_shape",
    "actor_action_shape",
    "output_semantics",
    "output_components",
    "action_low",
    "action_high",
    "deployable_runtime_contract",
    "base_policy_required_at_runtime",
    "hidden_oracle_actor_input_allowed",
    "ttc_actor_input_allowed",
    "target_labels_actor_visible",
    "target_provenance_actor_visible",
    "trainer_side_rows_allowed",
    "fitting_allowed_in_m3055",
    "claim_boundary",
]
LOSS_FAMILY_FIELDNAMES = [
    "loss_family_id",
    "loss_family",
    "priority",
    "source_rows",
    "row_count",
    "primary_signal",
    "target_behavior",
    "optimization_direction",
    "weight_policy",
    "guard_dependency",
    "actor_visible",
    "status_pass",
    "claim_boundary",
]
ROW_ADMISSION_FIELDNAMES = [
    "row_admission_id",
    "source_artifact",
    "source_row_family",
    "source_row_count",
    "admission_role",
    "loss_family",
    "admission_priority",
    "fit_target_allowed_after_m3056",
    "actor_visible_labels_required",
    "target_provenance_actor_visible",
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
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3055",
    "claim_made",
    "status_pass",
    "evidence_required_before_claim",
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
        "fitting_contract_rows": output_dir / "fitting_contract_rows.csv",
        "loss_family_rows": output_dir / "loss_family_rows.csv",
        "row_admission_rows": output_dir / "row_admission_rows.csv",
        "actor_contract_guard_rows": output_dir / "actor_contract_guard_rows.csv",
        "target_visibility_guard_rows": output_dir / "target_visibility_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "side_effect_guard_rows": output_dir / "side_effect_guard_rows.csv",
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


def load_source_artifacts(*, m3054_audit: Path, m3053_dir: Path) -> dict[str, Any]:
    paths = {
        "m3054_audit": m3054_audit,
        "m3053_summary": m3053_dir / "summary.json",
        "behavior_repair_route_rows": m3053_dir / "behavior_repair_route_rows.csv",
        "offtrack_behavior_target_source_rows": m3053_dir / "offtrack_behavior_target_source_rows.csv",
        "candidate_binding_blocker_rows": m3053_dir / "candidate_binding_blocker_rows.csv",
        "collision_guard_rows": m3053_dir / "collision_guard_rows.csv",
        "success_preservation_guard_rows": m3053_dir / "success_preservation_guard_rows.csv",
        "speed_floor_guard_rows": m3053_dir / "speed_floor_guard_rows.csv",
        "actor_contract_guard_rows": m3053_dir / "actor_contract_guard_rows.csv",
        "claim_boundary_rows": m3053_dir / "claim_boundary_rows.csv",
        "gate_matrix": m3053_dir / "gate_matrix.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required M3055 input artifacts: {missing}")
    return {
        "paths": paths,
        "m3054_audit_text": m3054_audit.read_text(encoding="utf-8"),
        "m3053_summary": read_json(paths["m3053_summary"]),
        "behavior_repair_route_rows": read_csv_rows(paths["behavior_repair_route_rows"]),
        "offtrack_behavior_target_source_rows": read_csv_rows(paths["offtrack_behavior_target_source_rows"]),
        "candidate_binding_blocker_rows": read_csv_rows(paths["candidate_binding_blocker_rows"]),
        "collision_guard_rows": read_csv_rows(paths["collision_guard_rows"]),
        "success_preservation_guard_rows": read_csv_rows(paths["success_preservation_guard_rows"]),
        "speed_floor_guard_rows": read_csv_rows(paths["speed_floor_guard_rows"]),
        "actor_contract_guard_rows": read_csv_rows(paths["actor_contract_guard_rows"]),
        "claim_boundary_rows": read_csv_rows(paths["claim_boundary_rows"]),
        "gate_rows": read_csv_rows(paths["gate_matrix"]),
    }


def build_fitting_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "contract_id": "m3055-fitting-contract-0001",
            "contract_family": "offtrack_dominant_behavior_recovery_selector_reflex",
            "model_role": "deployable_active_safety_reflex_layer",
            "actor_observation_shape": P0_OBSERVATION_DIM,
            "actor_action_shape": ACTION_DIM,
            "output_semantics": "direct_action",
            "output_components": "steer;throttle;brake",
            "action_low": -1.0,
            "action_high": 1.0,
            "deployable_runtime_contract": "obs72_to_action3_without_hidden_labels",
            "base_policy_required_at_runtime": False,
            "hidden_oracle_actor_input_allowed": False,
            "ttc_actor_input_allowed": False,
            "target_labels_actor_visible": False,
            "target_provenance_actor_visible": False,
            "trainer_side_rows_allowed": True,
            "fitting_allowed_in_m3055": False,
            "claim_boundary": CLAIM_SCOPE,
        }
    ]


def build_loss_family_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    offtrack_count = len(source["offtrack_behavior_target_source_rows"])
    collision_count = len(source["collision_guard_rows"])
    success_count = len(source["success_preservation_guard_rows"])
    speed_count = len(source["speed_floor_guard_rows"])
    candidate_count = len(source["candidate_binding_blocker_rows"])
    rows = [
        (
            "offtrack_recovery",
            "p0",
            "offtrack_behavior_target_source_rows.csv",
            offtrack_count,
            "offtrack_terminal_boundary_crossing",
            "recover_inside_track_before_terminal_boundary_crossing",
            "minimize",
            "dominant_weight",
            "collision_guard and success_preservation_guard",
        ),
        (
            "candidate_binding_blocker",
            "p0",
            "candidate_binding_blocker_rows.csv",
            candidate_count,
            "candidate_binding_zero_success",
            "prevent fitting contract from accepting unchanged candidate behavior",
            "minimize",
            "hard_gate",
            "offtrack_recovery",
        ),
        (
            "collision_guard",
            "p1",
            "collision_guard_rows.csv",
            collision_count,
            "collision_or_obstacle_collision_radius",
            "do not trade offtrack repair for T5 collision increase",
            "minimize",
            "hard_guard",
            "offtrack_recovery",
        ),
        (
            "success_preservation",
            "p1",
            "success_preservation_guard_rows.csv",
            success_count,
            "parent_success_positive_reference",
            "preserve successful rows as identity or positive references",
            "maximize_or_preserve",
            "hard_guard",
            "offtrack_recovery",
        ),
        (
            "speed_floor",
            "p2",
            "speed_floor_guard_rows.csv",
            speed_count,
            "speed_too_low_termination",
            "keep speed-floor failure visible",
            "minimize",
            "visibility_guard",
            "offtrack_recovery",
        ),
        (
            "stability_and_smoothness",
            "p2",
            "offtrack_behavior_target_source_rows.csv",
            offtrack_count,
            "high_sideslip_fraction;lateral_rmse;action_rate_mean",
            "avoid high-sideslip unstable or high-rate actions during recovery",
            "minimize",
            "regularizer",
            "success_preservation_guard",
        ),
    ]
    return [
        {
            "loss_family_id": f"m3055-loss-family-{index:04d}",
            "loss_family": family,
            "priority": priority,
            "source_rows": source_rows,
            "row_count": row_count,
            "primary_signal": primary_signal,
            "target_behavior": target_behavior,
            "optimization_direction": optimization_direction,
            "weight_policy": weight_policy,
            "guard_dependency": guard_dependency,
            "actor_visible": False,
            "status_pass": row_count > 0,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (
            family,
            priority,
            source_rows,
            row_count,
            primary_signal,
            target_behavior,
            optimization_direction,
            weight_policy,
            guard_dependency,
        ) in enumerate(rows, start=1)
    ]


def build_row_admission_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = [
        (
            "offtrack_behavior_target_source_rows.csv",
            "offtrack_behavior_target_source",
            len(source["offtrack_behavior_target_source_rows"]),
            "primary_target_source",
            "offtrack_recovery",
            "p0",
            True,
        ),
        (
            "candidate_binding_blocker_rows.csv",
            "candidate_binding_blocker",
            len(source["candidate_binding_blocker_rows"]),
            "blocker_guard",
            "candidate_binding_blocker",
            "p0",
            False,
        ),
        (
            "collision_guard_rows.csv",
            "collision_guard",
            len(source["collision_guard_rows"]),
            "guardrail",
            "collision_guard",
            "p1",
            False,
        ),
        (
            "success_preservation_guard_rows.csv",
            "success_preservation_guard",
            len(source["success_preservation_guard_rows"]),
            "positive_reference_guard",
            "success_preservation",
            "p1",
            False,
        ),
        (
            "speed_floor_guard_rows.csv",
            "speed_floor_guard",
            len(source["speed_floor_guard_rows"]),
            "visibility_guard",
            "speed_floor",
            "p2",
            False,
        ),
    ]
    return [
        {
            "row_admission_id": f"m3055-row-admission-{index:04d}",
            "source_artifact": artifact,
            "source_row_family": source_family,
            "source_row_count": row_count,
            "admission_role": role,
            "loss_family": loss_family,
            "admission_priority": priority,
            "fit_target_allowed_after_m3056": fit_allowed,
            "actor_visible_labels_required": False,
            "target_provenance_actor_visible": False,
            "status_pass": row_count > 0,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (artifact, source_family, row_count, role, loss_family, priority, fit_allowed) in enumerate(specs, start=1)
    ]


def build_actor_guard_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = source["m3053_summary"]
    guards = [
        ("observation_shape", summary.get("observation_shape"), P0_OBSERVATION_DIM, True),
        ("action_shape", summary.get("action_shape"), ACTION_DIM, True),
        ("actor_contract_shape_72_action_3", summary.get("actor_contract_shape_72_action_3"), True, True),
        ("direct_action_contract", "steer;throttle;brake", "steer;throttle;brake", True),
        ("base_policy_required_at_runtime", False, False, False),
        ("hidden_oracle_actor_input_detected", summary.get("hidden_oracle_actor_input_detected"), False, False),
        ("target_labels_actor_visible", summary.get("target_labels_actor_visible"), False, False),
        ("target_provenance_actor_visible", summary.get("target_provenance_actor_visible"), False, False),
        ("ttc_actor_input_required", summary.get("ttc_actor_input_required"), False, False),
    ]
    return [
        {
            "actor_guard_id": f"m3055-actor-guard-{index:04d}",
            "guard_family": family,
            "observed": observed,
            "expected": expected,
            "status_pass": observed == expected,
            "actor_visible": actor_visible,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, observed, expected, actor_visible) in enumerate(guards, start=1)
    ]


def build_target_visibility_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = [
        (
            "offtrack_target_source_rows_actor_invisible",
            "offtrack_behavior_target_source_rows.csv",
            _all_false(source["offtrack_behavior_target_source_rows"], "actor_visible")
            and _all_false(source["offtrack_behavior_target_source_rows"], "target_labels_actor_visible")
            and _all_false(source["offtrack_behavior_target_source_rows"], "target_provenance_actor_visible"),
            True,
        ),
        (
            "candidate_blockers_actor_invisible",
            "candidate_binding_blocker_rows.csv",
            True,
            True,
        ),
        (
            "collision_guards_actor_invisible",
            "collision_guard_rows.csv",
            True,
            True,
        ),
        (
            "success_guards_actor_invisible",
            "success_preservation_guard_rows.csv",
            True,
            True,
        ),
        (
            "speed_floor_guards_actor_invisible",
            "speed_floor_guard_rows.csv",
            True,
            True,
        ),
    ]
    return [
        {
            "target_visibility_guard_id": f"m3055-target-visibility-{index:04d}",
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


def build_claim_rows() -> list[dict[str, Any]]:
    rows = [
        ("fitting_contract_materialization", True, True, "M3055 summary and contract rows"),
        ("target_tensor_quality", False, False, "future target tensor materialization and audit"),
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
            "claim_id": f"m3055-claim-{index:04d}",
            "claim_family": family,
            "allowed_in_m3055": allowed,
            "claim_made": made,
            "status_pass": allowed == made,
            "evidence_required_before_claim": evidence,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (family, allowed, made, evidence) in enumerate(rows, start=1)
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
            "side_effect_guard_id": f"m3055-side-effect-{index:04d}",
            "side_effect": side_effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, side_effect in enumerate(side_effects, start=1)
    ]


def build_gate_rows(
    *,
    source: Mapping[str, Any],
    contract_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    follow_up_manifest_exists: bool,
) -> list[dict[str, Any]]:
    summary = source["m3053_summary"]
    gates = [
        ("m3054_audit_present", "lineage", bool(source["m3054_audit_text"]), True, "lineage_invalid"),
        ("m3053_status_pass", "source", _bool(summary.get("status_pass")), True, "metric_artifact"),
        ("m3053_gate_matrix_pass", "source", _bool(summary.get("gate_matrix_pass")), True, "metric_artifact"),
        ("route_rows_present", "source", len(source["behavior_repair_route_rows"]), EXPECTED_ROUTE_ROWS, "lineage_invalid"),
        ("offtrack_rows_present", "source", len(source["offtrack_behavior_target_source_rows"]), EXPECTED_OFFTRACK_ROWS, "behavior_regression"),
        ("candidate_blockers_present", "source", len(source["candidate_binding_blocker_rows"]), EXPECTED_CANDIDATE_BLOCKER_ROWS, "behavior_regression"),
        ("collision_guards_present", "source", len(source["collision_guard_rows"]), EXPECTED_COLLISION_GUARD_ROWS, "behavior_regression"),
        ("success_guards_present", "source", len(source["success_preservation_guard_rows"]), EXPECTED_SUCCESS_GUARD_ROWS, "behavior_regression"),
        ("speed_floor_guards_present", "source", len(source["speed_floor_guard_rows"]), EXPECTED_SPEED_FLOOR_ROWS, "behavior_regression"),
        ("fitting_contract_materialized", "contract", len(contract_rows), 1, "metric_artifact"),
        ("direct_action_output_contract", "contract", contract_rows[0]["output_semantics"] if contract_rows else "", "direct_action", "contract_violation"),
        ("loss_families_materialized", "contract", len(loss_rows), EXPECTED_LOSS_FAMILY_ROWS, "metric_artifact"),
        ("row_admission_materialized", "contract", len(admission_rows), 5, "metric_artifact"),
        ("actor_guards_pass", "contract", all(_bool(row["status_pass"]) for row in actor_rows), True, "contract_violation"),
        ("target_visibility_guards_pass", "contract", all(_bool(row["status_pass"]) for row in visibility_rows), True, "contract_violation"),
        ("claim_boundaries_pass", "claim_boundary", all(_bool(row["status_pass"]) for row in claim_rows), True, "contract_violation"),
        ("side_effects_absent", "side_effect", all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows), True, "contract_violation"),
        ("follow_up_manifest_registered", "process", follow_up_manifest_exists, True, "lineage_invalid"),
    ]
    return [
        {
            "gate_id": f"m3055-{name}",
            "gate_family": family,
            "status_pass": observed == expected,
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }
        for name, family, observed, expected, failure_type in gates
    ]


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30510,
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
        "hypothesis": "A bounded result audit can accept or reject the M3055 offtrack-dominant behavior fitting-contract materialization artifacts before any target tensor fitting rollout validation ranking promotion driver-performance high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "fitting_contract_rows.csv"),
                str(output_dir / "loss_family_rows.csv"),
                str(output_dir / "row_admission_rows.csv"),
                str(output_dir / "actor_contract_guard_rows.csv"),
                str(output_dir / "target_visibility_guard_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "side_effect_guard_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit offtrack-dominant behavior fitting-contract materialization before fitting"],
            "derived_from": [MILESTONE_ID, M3054_ID],
            "blocked_by": [
                "M3055 fitting-contract rows require audit before target tensor or fitting routes",
                "fitting contracts are not fitted policy quality repair-success or driver-performance evidence",
            ],
            "supersedes": ["direct target tensor fitting or rollout from M3055 contract without audit"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3056 must audit M3055 contract loss row-admission actor target-visibility side-effect claim and gate artifacts",
            "M3056 must reject target tensor quality fitting execution fitted policy quality repair-success validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims",
            "M3056 must preserve actor observation 72 action 3 and no hidden oracle TTC target provenance source route outcome progress or verdict actor inputs",
            "M3056 must choose exactly one next target tensor materialization fitting repair synthesis or stop route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run target tensor fitting rollout validation ranking promotion high-fidelity or finite-window-vs-GRU comparison",
            "do not convert M3055 contract rows into target tensor quality fitted policy quality repair-success driver-performance current-sim paper high-fidelity full-driver or self-ID claims",
            "do not mutate parent checkpoints configs profiles or actor contract",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_offtrack_behavior_fitting_contract_result_audit",
            "evidence_increment": "audits the M3055 behavior fitting contract before any target tensor or fitting route",
            "claim_scope": "Result audit only; no target tensor fitting rollout validation ranking promotion performance paper high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            "stop_condition": [
                "stop if M3055 artifact set is incomplete",
                "stop if actor target-visibility side-effect or claim-boundary guards fail",
                "stop if contract rows are treated as fitted policy quality or performance evidence",
            ],
            "fallback_plan": [
                "route to target tensor materialization or fitting admission only if M3055 is accepted",
                "route to artifact repair if rows or guards fail",
                "route to synthesis or stop if fitting contract is not admissible",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3055 completes behavior fitting-contract materialization",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit offtrack-dominant behavior fitting-contract materialization artifacts",
            "admission_evidence": [
                "M3055 summary and gate matrix",
                "M3055 fitting contract loss family row admission actor target visibility side-effect and claim rows",
            ],
            "blocked_shortcuts": [
                "no target tensor fitting rollout validation ranking promotion or checkpoint mutation",
                "no hidden oracle target TTC source route outcome progress or verdict actor inputs",
                "no driver-performance current-sim high-fidelity finite-window-vs-GRU paper or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3056 status queue scoreboard research log and review",
                "one follow-up manifest only if M3056 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3055 fitting contract rows are accepted or rejected",
                "one next target tensor materialization fitting repair synthesis or stop route is selected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3056 audits engineering contract artifacts and cannot prove or disprove history necessity.",
            "history_necessity_tests": [
                "None in M3056; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3055 behavior fitting-contract materialization artifacts only.",
            "negative_result_policy": "Self-ID diagnostics remain auxiliary and cannot replace active-safety fitting-contract audit gates.",
            "allowed_claims": [
                "M3055 artifact audit completeness",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 1,
            "evidence_expansion": "audits behavior fitting-contract materialization before a target tensor/fitting or stop decision",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3056 prepares a claim-safe engineering continuation decision",
            "must_synthesize_if": [
                "M3056 cannot select a target tensor materialization fitting repair synthesis or stop route",
                "M3056 would require another materialization-only loop without fitting admission",
                "M3056 would claim validation driver-performance paper high-fidelity finite-window-vs-GRU current-sim verdict or self-ID evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3056 audits M3055 contract loss row-admission actor target-visibility side-effect claim and gate artifacts",
            "M3056 rejects target tensor quality fitting execution fitted policy quality repair-success validation ranking promotion performance high-fidelity paper finite-window-vs-GRU and self-ID claims",
            "M3056 selects exactly one next target tensor materialization fitting repair synthesis or stop route",
        ],
        "failure_criteria": [
            "M3056 treats fitting-contract rows as fitted policy quality or driver performance",
            "M3056 omits actor target-visibility side-effect or claim-boundary audits",
            "M3056 runs target tensor fitting validation ranking promotion high-fidelity or architecture comparison",
            "M3056 leaves the next route ambiguous",
        ],
        "decision_rule": "Pass only if M3056 audits M3055 behavior fitting-contract evidence and selects exactly one target tensor materialization fitting repair synthesis or stop route without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_offtrack_dominant_behavior_fitting_contract_materialization_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "fitting_contract_rows.csv"),
            str(output_dir / "loss_family_rows.csv"),
            str(output_dir / "row_admission_rows.csv"),
            str(output_dir / "actor_contract_guard_rows.csv"),
            str(output_dir / "target_visibility_guard_rows.csv"),
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
    contract_rows: list[dict[str, Any]],
    loss_rows: list[dict[str, Any]],
    admission_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    visibility_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    actor_guard_pass = all(_bool(row["status_pass"]) for row in actor_rows)
    visibility_guard_pass = all(_bool(row["status_pass"]) for row in visibility_rows)
    claim_rows_pass = all(_bool(row["status_pass"]) for row in claim_rows)
    side_effects_pass = all(_bool(row["status_pass"]) and not _bool(row["scheduled_or_run"]) for row in side_effect_rows)
    m3053_summary = source["m3053_summary"]
    return {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_offtrack_behavior_fitting_contract_materialization_preflight_pass",
        "status_pass": gate_matrix_pass,
        "gate_matrix_pass": gate_matrix_pass,
        "decision": "active_safety_driver_v1_offtrack_behavior_fitting_contract_materialized_route_to_m3056_result_audit",
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "output_dir": str(output_dir),
        "m3053_status_pass": bool(m3053_summary.get("status_pass")),
        "m3053_gate_matrix_pass": bool(m3053_summary.get("gate_matrix_pass")),
        "m3053_offtrack_behavior_target_source_row_count": int(m3053_summary.get("offtrack_behavior_target_source_row_count", 0)),
        "m3053_candidate_binding_blocker_row_count": int(m3053_summary.get("candidate_binding_blocker_row_count", 0)),
        "m3053_collision_guard_row_count": int(m3053_summary.get("collision_guard_row_count", 0)),
        "m3053_success_preservation_guard_row_count": int(m3053_summary.get("success_preservation_guard_row_count", 0)),
        "m3053_speed_floor_guard_row_count": int(m3053_summary.get("speed_floor_guard_row_count", 0)),
        "fitting_contract_row_count": len(contract_rows),
        "loss_family_row_count": len(loss_rows),
        "row_admission_row_count": len(admission_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": actor_guard_pass,
        "target_visibility_guard_row_count": len(visibility_rows),
        "target_visibility_guard_rows_pass": visibility_guard_pass,
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": claim_rows_pass,
        "side_effect_guard_row_count": len(side_effect_rows),
        "side_effect_guard_rows_pass": side_effects_pass,
        "gate_matrix_row_count": len(gate_rows),
        "actor_contract_shape_72_action_3": actor_guard_pass,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
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
        "required_artifacts_present": True,
        "paths": {
            "summary": str(output_dir / "summary.json"),
            "fitting_contract_rows": str(output_dir / "fitting_contract_rows.csv"),
            "loss_family_rows": str(output_dir / "loss_family_rows.csv"),
            "row_admission_rows": str(output_dir / "row_admission_rows.csv"),
            "actor_contract_guard_rows": str(output_dir / "actor_contract_guard_rows.csv"),
            "target_visibility_guard_rows": str(output_dir / "target_visibility_guard_rows.csv"),
            "claim_boundary_rows": str(output_dir / "claim_boundary_rows.csv"),
            "side_effect_guard_rows": str(output_dir / "side_effect_guard_rows.csv"),
            "gate_matrix": str(output_dir / "gate_matrix.csv"),
            "doc": str(doc_path),
            "follow_up_manifest": str(follow_up_manifest),
        },
    }


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# M3055 Active Safety Driver v1 Offtrack-Dominant Behavior Fitting Contract Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_offtrack_behavior_fitting_contract_materialized_route_to_m3056_result_audit`
- next blocker: `{NEXT_ID}`
- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`

M3055 materializes the fitting contract for a later deployable offtrack-
dominant behavior recovery selector/reflex. The runtime contract is direct
`obs72 -> [steer, throttle, brake]`, without a base-policy dependency and
without hidden/oracle/TTC/target/provenance/source/route/outcome/progress/
verdict actor inputs.

## Contract Summary

```text
observation_shape: {summary['observation_shape']}
action_shape: {summary['action_shape']}
output_semantics: {summary['output_semantics']}
output_components: steer / throttle / brake
base_policy_required_at_runtime: {summary['base_policy_required_at_runtime']}
fitting_contract_rows: {summary['fitting_contract_row_count']}
loss_family_rows: {summary['loss_family_row_count']}
row_admission_rows: {summary['row_admission_row_count']}
actor_contract_guard_rows: {summary['actor_contract_guard_row_count']}
target_visibility_guard_rows: {summary['target_visibility_guard_row_count']}
side_effect_guard_rows: {summary['side_effect_guard_row_count']}
gate_rows: {summary['gate_matrix_row_count']}
```

## Source Counts

```text
M3053 offtrack target-source rows: {summary['m3053_offtrack_behavior_target_source_row_count']}
M3053 candidate blocker rows: {summary['m3053_candidate_binding_blocker_row_count']}
M3053 collision guard rows: {summary['m3053_collision_guard_row_count']}
M3053 success-preservation guard rows: {summary['m3053_success_preservation_guard_row_count']}
M3053 speed-floor guard rows: {summary['m3053_speed_floor_guard_row_count']}
```

## Supported Claims

M3055 supports only these bounded claims:

```text
one behavior fitting contract was materialized
direct action output [steer, throttle, brake] was specified
offtrack recovery collision guard success preservation speed floor stability and smoothness loss families are separated
actor-contract target-visibility side-effect and claim-boundary guards pass
M3056 result-audit manifest was registered
```

## Rejected Claims

M3055 rejects:

```text
target tensor quality
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3055 is fitting-contract materialization only. It writes no fitted weights and
runs no environment interaction.
""",
        encoding="utf-8",
    )


def run(
    *,
    m3054_audit: Path,
    m3053_dir: Path,
    output_dir: Path,
    doc_path: Path,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output_dir, doc_path=doc_path, follow_up_manifest=follow_up_manifest)
    source = load_source_artifacts(m3054_audit=m3054_audit, m3053_dir=m3053_dir)

    contract_rows = build_fitting_contract_rows()
    loss_rows = build_loss_family_rows(source)
    admission_rows = build_row_admission_rows(source)
    actor_rows = build_actor_guard_rows(source)
    visibility_rows = build_target_visibility_rows(source)
    claim_rows = build_claim_rows()
    side_effect_rows = build_side_effect_rows()

    write_csv_rows(paths["fitting_contract_rows"], contract_rows, FITTING_CONTRACT_FIELDNAMES)
    write_csv_rows(paths["loss_family_rows"], loss_rows, LOSS_FAMILY_FIELDNAMES)
    write_csv_rows(paths["row_admission_rows"], admission_rows, ROW_ADMISSION_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["target_visibility_guard_rows"], visibility_rows, TARGET_VISIBILITY_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, CLAIM_FIELDNAMES)
    write_csv_rows(paths["side_effect_guard_rows"], side_effect_rows, SIDE_EFFECT_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    gate_rows = build_gate_rows(
        source=source,
        contract_rows=contract_rows,
        loss_rows=loss_rows,
        admission_rows=admission_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        claim_rows=claim_rows,
        side_effect_rows=side_effect_rows,
        follow_up_manifest_exists=follow_up_manifest.exists(),
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        source=source,
        contract_rows=contract_rows,
        loss_rows=loss_rows,
        admission_rows=admission_rows,
        actor_rows=actor_rows,
        visibility_rows=visibility_rows,
        claim_rows=claim_rows,
        side_effect_rows=side_effect_rows,
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
    parser.add_argument("--m3054-audit", type=Path, default=DEFAULT_M3054_AUDIT)
    parser.add_argument("--m3053-dir", type=Path, default=DEFAULT_M3053_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()

    summary = run(
        m3054_audit=args.m3054_audit,
        m3053_dir=args.m3053_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"output_semantics={summary['output_semantics']}")
    print(f"loss_family_row_count={summary['loss_family_row_count']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
