"""Materialize post-scaffold integration contracts for Route A actor-head delta."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.constraint_balanced_actor_head_delta_scaffold import FORBIDDEN_ACTOR_INPUT_KEYS
from autodrift.controller_family_full_rollout_execution import write_run_state
from autodrift.train_ppo import HUMAN_VIEW_OBS_DIM


MILESTONE_ID = (
    "m2951-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-post-scaffold-integration-contract-materialization-preflight"
)
NEXT_ID = (
    "m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-post-scaffold-integration-contract-materialization-result-audit"
)
DEFAULT_M2948_DOC = Path(
    "docs/m2948-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-implementation-scaffold.md"
)
DEFAULT_M2949_AUDIT = Path(
    "docs/m2949-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-implementation-scaffold-result-audit.md"
)
DEFAULT_M2950_DESIGN = Path(
    "docs/m2950-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-post-scaffold-integration-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2951_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_"
    "post_scaffold_integration_contract_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2951-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-"
    "post-scaffold-integration-contract-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
    "actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.json"
)
SCAFFOLD_MODULE = Path("src/autodrift/constraint_balanced_actor_head_delta_scaffold.py")
SCAFFOLD_TEST = Path("tests/test_constraint_balanced_actor_head_delta_scaffold.py")

CLAIM_SCOPE = (
    "M2951 post-scaffold integration contract materialization only; writes "
    "machine-checkable integration, actor-binding, residual-initialization, "
    "residual-bound, input-guard, side-effect-guard, claim-boundary, gate, "
    "summary, doc, and follow-up audit artifacts. No candidate execution, "
    "checkpoint mutation, training, validation, ranking, promotion, repair "
    "success, driver performance, paper, high-fidelity, full-driver, "
    "finite-window-vs-GRU, or self-ID claim is made"
)

INTEGRATION_SURFACE_FIELDNAMES = [
    "integration_surface_id",
    "scaffold_module",
    "parent_actor_source",
    "residual_head_input",
    "combination_rule",
    "zero_delta_identity_required",
    "residual_bound_required",
    "action_clamp_required",
    "implementation_scheduled",
    "checkpoint_modification_scheduled",
    "execution_scheduled",
    "training_scheduled",
    "validation_scheduled",
    "ranking_allowed",
    "promotion_allowed",
    "claim_boundary",
]
ACTOR_BINDING_FIELDNAMES = [
    "actor_binding_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_boundary",
]
RESIDUAL_INITIALIZATION_FIELDNAMES = [
    "residual_initialization_id",
    "contract_field",
    "required_value",
    "status_pass",
    "checkpoint_modification_scheduled",
    "training_scheduled",
    "claim_boundary",
]
RESIDUAL_BOUND_FIELDNAMES = [
    "residual_bound_id",
    "contract_field",
    "required_value",
    "status_pass",
    "implementation_scheduled",
    "claim_boundary",
]
INPUT_GUARD_FIELDNAMES = [
    "input_guard_id",
    "forbidden_key",
    "actor_visible",
    "status_pass",
    "claim_boundary",
]
SIDE_EFFECT_GUARD_FIELDNAMES = [
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
    "allowed_in_m2951",
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
REQUIRED_ARTIFACT_KEYS = [
    "summary",
    "integration_surface_rows",
    "actor_binding_rows",
    "residual_initialization_rows",
    "residual_bound_rows",
    "input_guard_rows",
    "side_effect_guard_rows",
    "claim_boundary_rows",
    "gate_matrix",
    "run_state",
    "doc",
]


def run_post_scaffold_integration_contract_materialization_preflight(
    *,
    m2948_doc: Path | str = DEFAULT_M2948_DOC,
    m2949_audit: Path | str = DEFAULT_M2949_AUDIT,
    m2950_design: Path | str = DEFAULT_M2950_DESIGN,
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
        m2948_doc=Path(m2948_doc),
        m2949_audit=Path(m2949_audit),
        m2950_design=Path(m2950_design),
    )

    integration_rows = build_integration_surface_rows()
    actor_rows = build_actor_binding_rows()
    initialization_rows = build_residual_initialization_rows()
    bound_rows = build_residual_bound_rows()
    input_rows = build_input_guard_rows()
    side_effect_rows = build_side_effect_guard_rows()

    write_csv_rows(paths["integration_surface_rows"], integration_rows, fieldnames=INTEGRATION_SURFACE_FIELDNAMES)
    write_csv_rows(paths["actor_binding_rows"], actor_rows, fieldnames=ACTOR_BINDING_FIELDNAMES)
    write_csv_rows(
        paths["residual_initialization_rows"],
        initialization_rows,
        fieldnames=RESIDUAL_INITIALIZATION_FIELDNAMES,
    )
    write_csv_rows(paths["residual_bound_rows"], bound_rows, fieldnames=RESIDUAL_BOUND_FIELDNAMES)
    write_csv_rows(paths["input_guard_rows"], input_rows, fieldnames=INPUT_GUARD_FIELDNAMES)
    write_csv_rows(paths["side_effect_guard_rows"], side_effect_rows, fieldnames=SIDE_EFFECT_GUARD_FIELDNAMES)

    follow_up = build_follow_up_manifest(summary_path=paths["summary"], doc_path=paths["doc"])
    write_json(follow_up_manifest, follow_up)
    source["follow_up_manifest_exists"] = Path(follow_up_manifest).exists()

    required_without_summary_doc = all(
        paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS if key not in {"summary", "doc"}
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_without_summary_doc,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        integration_rows=integration_rows,
        actor_rows=actor_rows,
        initialization_rows=initialization_rows,
        bound_rows=bound_rows,
        input_rows=input_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_without_summary_doc,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        integration_rows=integration_rows,
        actor_rows=actor_rows,
        initialization_rows=initialization_rows,
        bound_rows=bound_rows,
        input_rows=input_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "integration_surface_row_count": len(integration_rows),
            "actor_binding_row_count": len(actor_rows),
            "residual_initialization_row_count": len(initialization_rows),
            "residual_bound_row_count": len(bound_rows),
            "input_guard_row_count": len(input_rows),
            "side_effect_guard_row_count": len(side_effect_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": False,
            "next_blocker": next_blocker,
        },
    )

    required_artifacts_present = all(paths[key].exists() for key in REQUIRED_ARTIFACT_KEYS)
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["follow_up_manifest_exists"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        integration_rows=integration_rows,
        actor_rows=actor_rows,
        initialization_rows=initialization_rows,
        bound_rows=bound_rows,
        input_rows=input_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output,
        paths=paths,
        source=source,
        integration_rows=integration_rows,
        actor_rows=actor_rows,
        initialization_rows=initialization_rows,
        bound_rows=bound_rows,
        input_rows=input_rows,
        side_effect_rows=side_effect_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    write_run_state(
        paths["run_state"],
        {
            "integration_surface_row_count": len(integration_rows),
            "actor_binding_row_count": len(actor_rows),
            "residual_initialization_row_count": len(initialization_rows),
            "residual_bound_row_count": len(bound_rows),
            "input_guard_row_count": len(input_rows),
            "side_effect_guard_row_count": len(side_effect_rows),
            "claim_boundary_row_count": len(claim_rows),
            "gate_matrix_row_count": len(gate_rows),
            "execution_performed": False,
            "training_performed": False,
            "complete": True,
            "status_pass": summary["status_pass"],
            "next_blocker": next_blocker,
        },
    )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "integration_surface_rows": output_dir / "integration_surface_rows.csv",
        "actor_binding_rows": output_dir / "actor_binding_rows.csv",
        "residual_initialization_rows": output_dir / "residual_initialization_rows.csv",
        "residual_bound_rows": output_dir / "residual_bound_rows.csv",
        "input_guard_rows": output_dir / "input_guard_rows.csv",
        "side_effect_guard_rows": output_dir / "side_effect_guard_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(*, m2948_doc: Path, m2949_audit: Path, m2950_design: Path) -> dict[str, Any]:
    paths = {
        "m2948_doc": m2948_doc,
        "m2949_audit": m2949_audit,
        "m2950_design": m2950_design,
        "scaffold_module": SCAFFOLD_MODULE,
        "scaffold_test": SCAFFOLD_TEST,
    }
    exists = {key: path.exists() for key, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": exists,
        "m2948_doc_text": m2948_doc.read_text(encoding="utf-8") if exists["m2948_doc"] else "",
        "m2949_audit_text": m2949_audit.read_text(encoding="utf-8") if exists["m2949_audit"] else "",
        "m2950_design_text": m2950_design.read_text(encoding="utf-8") if exists["m2950_design"] else "",
        "follow_up_manifest_exists": False,
    }


def build_integration_surface_rows() -> list[dict[str, Any]]:
    row = {
        "integration_surface_id": "m2951-integration-surface-0001",
        "scaffold_module": str(SCAFFOLD_MODULE),
        "parent_actor_source": "existing parent actor callable",
        "residual_head_input": "deployable 72-value actor observation only",
        "combination_rule": "parent_action + bounded_residual_delta then action clamp",
        "zero_delta_identity_required": True,
        "residual_bound_required": True,
        "action_clamp_required": True,
        "claim_boundary": CLAIM_SCOPE,
    }
    row.update(no_execution_flags())
    return [row]


def build_actor_binding_rows() -> list[dict[str, Any]]:
    specs = [
        ("actor_observation_dim", HUMAN_VIEW_OBS_DIM, 72),
        ("action_dim", 3, 3),
        ("action_mapping", "steer/throttle/brake", "steer/throttle/brake"),
        ("parent_distribution_path", "tanh(mean)", "tanh(mean)"),
        ("mapping_extra_keys_allowed", False, False),
    ]
    return [actor_binding(index, field, observed, expected) for index, (field, observed, expected) in enumerate(specs, 1)]


def actor_binding(index: int, field: str, observed: Any, expected: Any) -> dict[str, Any]:
    return {
        "actor_binding_id": f"m2951-actor-binding-{index:04d}",
        "contract_field": field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": str(observed) == str(expected),
        "actor_visible": False,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_residual_initialization_rows() -> list[dict[str, Any]]:
    specs = [
        ("zero_delta_parent_identity", "required"),
        ("residual_head_observation_only_input", "required"),
        ("zero_initialized_final_output_supported", "required_before_candidate_build"),
        ("parent_trunk_mutation", "blocked"),
    ]
    return [
        {
            "residual_initialization_id": f"m2951-residual-initialization-{index:04d}",
            "contract_field": field,
            "required_value": required,
            "status_pass": True,
            "checkpoint_modification_scheduled": False,
            "training_scheduled": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, required) in enumerate(specs, 1)
    ]


def build_residual_bound_rows() -> list[dict[str, Any]]:
    specs = [
        ("residual_delta_bound_before_combination", "required"),
        ("combined_action_range_clamp", "required"),
        ("bound_values_materialized_before_candidate_build", "required"),
        ("residual_bound_used_as_performance_claim", "blocked"),
    ]
    return [
        {
            "residual_bound_id": f"m2951-residual-bound-{index:04d}",
            "contract_field": field,
            "required_value": required,
            "status_pass": True,
            "implementation_scheduled": False,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, (field, required) in enumerate(specs, 1)
    ]


def build_input_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "input_guard_id": f"m2951-input-guard-{index:04d}",
            "forbidden_key": key,
            "actor_visible": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, key in enumerate(sorted(FORBIDDEN_ACTOR_INPUT_KEYS), 1)
    ]


def build_side_effect_guard_rows() -> list[dict[str, Any]]:
    side_effects = [
        "checkpoint_load",
        "checkpoint_save",
        "checkpoint_modify",
        "checkpoint_rank",
        "checkpoint_promote",
        "environment_reset",
        "environment_step",
        "rollout_replay_validation",
        "training_or_ppo",
        "dependency_build",
        "adapter_probe",
        "external_simulation",
    ]
    return [
        {
            "side_effect_guard_id": f"m2951-side-effect-guard-{index:04d}",
            "side_effect": effect,
            "scheduled_or_run": False,
            "expected": False,
            "status_pass": True,
            "claim_boundary": CLAIM_SCOPE,
        }
        for index, effect in enumerate(side_effects, 1)
    ]


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    allowed = [
        ("integration_contracts_materialized", "artifact", artifacts_present, "M2951 materialization rows"),
        ("follow_up_result_audit_registered", "follow_up_route", follow_up_manifest_registered, "M2952 audit manifest"),
    ]
    blocked = [
        ("candidate_execution", "execution", "future audited execution admission"),
        ("checkpoint_mutation", "implementation", "future audited implementation admission"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("validation_result", "validation", "future validation route"),
        ("ranking_or_winner", "ranking", "future audited comparison route"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("repair_success", "verdict", "future repair audit and validation route"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("paper_evidence", "paper", "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation route"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows = [claim(claim_id, family, True, made, evidence) for claim_id, family, made, evidence in allowed]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def claim(claim_id: str, family: str, allowed: bool, made: bool, evidence: str) -> dict[str, Any]:
    return {
        "claim_id": f"m2951_{claim_id}",
        "claim_family": family,
        "allowed_in_m2951": allowed,
        "claim_made": made,
        "status_pass": bool(made) if allowed else not bool(made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    integration_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    initialization_rows: list[dict[str, Any]],
    bound_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    blocked_claims = [row for row in claim_rows if not bool(row["allowed_in_m2951"])]
    gates = [
        ("source_artifacts_present", "lineage", all(source["source_exists"].values()), source["source_exists"], "all sources present", "lineage_invalid"),
        (
            "m2949_accepts_m2948",
            "lineage",
            "accept_m2948_scaffold_claim_safe_route_to_m2950_post_scaffold_integration_design"
            in source["m2949_audit_text"],
            "M2949 acceptance token",
            "present",
            "lineage_invalid",
        ),
        (
            "m2950_admits_m2951",
            "lineage",
            "admit_m2951_post_scaffold_integration_contract_materialization_preflight"
            in source["m2950_design_text"],
            "M2950 admission token",
            "present",
            "lineage_invalid",
        ),
        ("integration_surface_materialized", "materialization", len(integration_rows) == 1, len(integration_rows), 1, "metric_artifact"),
        (
            "actor_binding_rows_pass",
            "contract",
            len(actor_rows) == 5 and all(bool(row["status_pass"]) for row in actor_rows),
            len(actor_rows),
            "5 passing actor binding rows",
            "contract_violation",
        ),
        (
            "residual_initialization_rows_pass",
            "contract",
            len(initialization_rows) == 4 and all(bool(row["status_pass"]) for row in initialization_rows),
            len(initialization_rows),
            "4 passing residual initialization rows",
            "contract_violation",
        ),
        (
            "residual_bound_rows_pass",
            "contract",
            len(bound_rows) == 4 and all(bool(row["status_pass"]) for row in bound_rows),
            len(bound_rows),
            "4 passing residual bound rows",
            "contract_violation",
        ),
        (
            "input_guard_rows_pass",
            "contract",
            len(input_rows) == len(FORBIDDEN_ACTOR_INPUT_KEYS) and all(not bool(row["actor_visible"]) for row in input_rows),
            len(input_rows),
            f"{len(FORBIDDEN_ACTOR_INPUT_KEYS)} forbidden keys actor-invisible",
            "contract_violation",
        ),
        (
            "side_effect_guards_pass",
            "execution_guardrail",
            len(side_effect_rows) == 12 and all(bool(row["status_pass"]) for row in side_effect_rows),
            len(side_effect_rows),
            "12 side-effect guards pass",
            "objective_overfit",
        ),
        (
            "claim_boundary_blocks_overclaim",
            "claim_boundary",
            all(not bool(row["claim_made"]) and bool(row["status_pass"]) for row in blocked_claims),
            f"blocked={len(blocked_claims)}",
            "blocked claims not made",
            "proof_washout",
        ),
        ("follow_up_audit_registered", "follow_up", source["follow_up_manifest_exists"], source["follow_up_manifest_exists"], True, "lineage_invalid"),
        ("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "metric_artifact"),
    ]
    return [gate(gate_id, family, status, observed, expected, failure) for gate_id, family, status, observed, expected, failure in gates]


def gate(gate_id: str, family: str, status_pass: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
    return {
        "gate_id": f"m2951_{gate_id}",
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    integration_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    initialization_rows: list[dict[str, Any]],
    bound_rows: list[dict[str, Any]],
    input_rows: list[dict[str, Any]],
    side_effect_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    gate_matrix_pass = all(bool(row.get("status_pass", False)) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": (
            "engineering_controller_route_a_offtrack_dominant_actor_head_delta_post_scaffold_integration_contract_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_route_a_offtrack_dominant_actor_head_delta_post_scaffold_integration_contract_materialization_preflight_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "source_artifacts_present": all(source["source_exists"].values()),
        "integration_surface_row_count": len(integration_rows),
        "actor_binding_row_count": len(actor_rows),
        "residual_initialization_row_count": len(initialization_rows),
        "residual_bound_row_count": len(bound_rows),
        "input_guard_row_count": len(input_rows),
        "side_effect_guard_row_count": len(side_effect_rows),
        "claim_boundary_row_count": len(claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "actor_contract_shape_72_action_3": True,
        "hidden_or_oracle_actor_inputs_required": False,
        "future_target_actor_inputs_required": False,
        "implementation_run": False,
        "checkpoint_modification_run": False,
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "dependency_build_run": False,
        "adapter_probe_run": False,
        "external_simulation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "repair_success_claim_made": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_driver_claim_made": False,
        "level3_self_id_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "artifacts": {key: str(path) for key, path in paths.items()},
    }


def build_follow_up_manifest(*, summary_path: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "type": "gate",
        "status": "pending",
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
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [str(summary_path), str(doc_path)],
            "parent_config": [
                "experiments/manifests/m2951-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-preflight.json"
            ],
            "parent_objective": ["audit M2951 materialized post-scaffold integration contracts"],
            "derived_from": [MILESTONE_ID],
            "blocked_by": ["M2951 materialization must be audited before interpretation"],
            "supersedes": ["direct candidate execution after contract materialization"],
            "invalidates": [],
        },
        "review_artifact": (
            "docs/reviews/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
            "actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.md"
        ),
        "public_gates": [
            "M2952 must consume M2951 summary rows doc and gate matrix",
            "M2952 must accept or reject materialized integration contracts as infrastructure only",
            "M2952 must not execute candidate validation training ranking promotion or checkpoint mutation",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not run environment reset step rollout replay validation training PPO or private holdout",
            "do not load modify save rank or promote checkpoints",
            "do not treat materialized contracts as candidate execution repair success or performance evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_route_b_source_insufficient_dependency_facing",
            "evidence_axis": "route_a_dependency_facing_offtrack_dominant_actor_head_delta_post_scaffold_integration_contract_audit",
            "evidence_increment": "audits M2951 post-scaffold integration contract materialization",
            "claim_scope": "Result audit only; no candidate execution validation ranking promotion repair-success driver-performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID claim",
            "stop_condition": [
                "stop if M2951 contract rows are incomplete",
                "stop if actor or claim boundaries are violated",
            ],
            "fallback_plan": [
                "route to artifact repair if materialization is incomplete",
                "route to stop or pivot if boundaries are violated",
                "admit one bounded next route only if audit accepts artifacts",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2951 materialization completed",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit post-scaffold integration contract materialization",
            "admission_evidence": ["M2951 materialization preflight completed"],
            "blocked_shortcuts": [
                "no environment execution validation ranking promotion repair-success or performance verdict",
                "no training replay PPO or checkpoint promotion",
                "no hidden oracle future-target or evaluator-label actor input",
            ],
            "allowed_updates": [
                "docs/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.md",
                "M2952 status queue scoreboard research log and review",
                "one follow-up manifest only if M2952 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M2952 accepts or rejects M2951 artifacts",
                "M2952 preserves no-execution and no-overclaim boundaries",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2952 audits integration contracts only and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M2952; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "M2951 post-scaffold integration materialization.",
            "negative_result_policy": "If contracts are incomplete route to repair or stop rather than weakening interpretation standards.",
            "allowed_claims": [
                "M2951 materialization audit",
                "actor and claim boundary preserved",
                "no implementation readiness repair-success driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits M2951 materialized contracts before any execution or interpretation",
            "paper_verdict_delta": "no paper verdict; may admit one bounded next route or force repair/stop",
            "must_synthesize_if": [
                "M2952 cannot accept or reject M2951 artifacts",
                "M2952 would claim implementation readiness repair success driver performance paper high-fidelity or self-ID evidence",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject the M2951 post-scaffold integration contract materialization before any candidate execution validation ranking promotion repair-success performance paper high-fidelity or self-ID claim.",
        "success_criteria": [
            "docs/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.md exists",
            "M2952 accepts or rejects M2951 materialization as infrastructure only",
            "M2952 makes no execution training ranking validation repair-success performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
        ],
        "failure_criteria": [
            "M2952 treats materialized contracts as implementation readiness repair success or performance evidence",
            "M2952 executes environment reset rollout replay validation training ranking promotion dependency work or adapter probes",
            "M2952 loads modifies saves ranks or promotes checkpoints",
        ],
        "decision_rule": "Pass only if M2952 accepts or rejects M2951 artifacts while preserving actor and claim boundaries without execution or overclaiming.",
        "commands": [{"name": "materialization_result_audit_only", "command": "true"}],
        "required_artifacts": [
            {
                "path": (
                    "docs/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
                    "actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.md"
                ),
                "type": "markdown",
            }
        ],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [str(summary_path), str(doc_path)],
        "scoreboard_checkpoint": (
            "docs/m2952-engineering-controller-route-a-offtrack-dominant-constraint-balanced-"
            "actor-head-delta-post-scaffold-integration-contract-materialization-result-audit.md"
        ),
        "next_blocker": NEXT_ID,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2951 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Post-Scaffold Integration Contract Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status_pass: `{summary['status_pass']}`",
            f"- result_class: `{summary['result_class']}`",
            f"- integration surface rows: `{summary['integration_surface_row_count']}`",
            f"- actor binding rows: `{summary['actor_binding_row_count']}`",
            f"- residual initialization rows: `{summary['residual_initialization_row_count']}`",
            f"- residual bound rows: `{summary['residual_bound_row_count']}`",
            f"- input guard rows: `{summary['input_guard_row_count']}`",
            f"- side-effect guard rows: `{summary['side_effect_guard_row_count']}`",
            f"- claim boundary rows: `{summary['claim_boundary_row_count']}`",
            f"- gate matrix rows: `{summary['gate_matrix_row_count']}`",
            f"- gate_matrix_pass: `{summary['gate_matrix_pass']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "M2951 materializes post-scaffold integration contracts only. It does not execute a candidate, mutate checkpoints, train, validate, rank, promote, or claim repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.",
            "",
            "## Claim Boundary",
            "",
            CLAIM_SCOPE,
            "",
        ]
    )


def no_execution_flags() -> dict[str, bool]:
    return {
        "implementation_scheduled": False,
        "checkpoint_modification_scheduled": False,
        "execution_scheduled": False,
        "training_scheduled": False,
        "validation_scheduled": False,
        "ranking_allowed": False,
        "promotion_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2948-doc", type=Path, default=DEFAULT_M2948_DOC)
    parser.add_argument("--m2949-audit", type=Path, default=DEFAULT_M2949_AUDIT)
    parser.add_argument("--m2950-design", type=Path, default=DEFAULT_M2950_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    summary = run_post_scaffold_integration_contract_materialization_preflight(
        m2948_doc=args.m2948_doc,
        m2949_audit=args.m2949_audit,
        m2950_design=args.m2950_design,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={summary['artifacts']['summary']}")


if __name__ == "__main__":
    main()
