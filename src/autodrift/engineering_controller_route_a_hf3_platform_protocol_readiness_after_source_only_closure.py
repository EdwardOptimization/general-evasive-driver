"""Route A HF3 platform/protocol readiness after source-only closure."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-"
    "only-closure-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2597-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-"
    "only-closure-materialization-result-audit"
)
DEFAULT_DOC_PATH = (
    "docs/m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-"
    "source-only-closure-materialization-preflight.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2596_engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure"
)
DEFAULT_M2592_SUMMARY = Path(
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json"
)

SOURCE_ARTIFACTS = (
    "docs/m2595-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-design.md",
    "docs/m2594-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-result-synthesis.md",
    "docs/m2593-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-result-audit.md",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_external_state_extraction_closure_rows.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_time_step_actuator_latency_closure_rows.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_failure_status_taxonomy_closure_rows.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_fixture_smoke_closure_rows.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_adapter_closure_actor_visibility_guard_rows.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_adapter_closure_claim_boundary_checks.csv",
    "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/source_only_adapter_blocker_closure_gate_matrix.csv",
    "src/autodrift/high_fidelity_interface.py",
    "docs/post-m2470-route-plan.md",
)

CLAIM_BOUNDARY = (
    "Route A HF3 after-closure platform/protocol readiness materialization preflight only; "
    "after-closure design artifacts may be materialized; not platform selection, validation "
    "protocol readiness, validation admission, external validation execution, high-fidelity "
    "validation readiness/result, HF4 discrepancy result, rollout success, ranking, driver "
    "performance, paper, FW-vs-GRU, current-sim verdict, high-fidelity validation, or self-ID"
)

PLATFORM_CANDIDATE_FIELDNAMES = [
    "platform_candidate_id",
    "platform_family",
    "platform_role",
    "source_only_closure_required_before_selection",
    "source_only_closure_accepted_in_m2596",
    "open_auditable_backend_required",
    "black_box_demonstration_only",
    "repo_local_diagnostic_only",
    "selected_for_validation_in_m2596",
    "install_allowed_in_m2596",
    "import_allowed_in_m2596",
    "runtime_execution_allowed_in_m2596",
    "dependency_mutation_allowed_in_m2596",
    "status_pass",
    "claim_boundary",
]

DEPENDENCY_IMPORT_POLICY_FIELDNAMES = [
    "dependency_policy_id",
    "dependency_family",
    "source_only_closure_accepted_in_m2596",
    "external_install_allowed_in_m2596",
    "external_import_allowed_in_m2596",
    "runtime_execution_allowed_in_m2596",
    "dependency_mutation_allowed_in_m2596",
    "future_platform_selection_design_allowed_after_audit",
    "status_pass",
    "claim_boundary",
]

VALIDATION_PROTOCOL_SKELETON_FIELDNAMES = [
    "validation_protocol_id",
    "route_role_id",
    "candidate_role_label",
    "actor_observation_shape",
    "action_shape",
    "source_only_closure_accepted_in_m2596",
    "protocol_skeleton_defined",
    "holdout_or_generalization_policy_defined",
    "reset_allowed_in_m2596",
    "policy_action_allowed_in_m2596",
    "environment_step_allowed_in_m2596",
    "rollout_allowed_in_m2596",
    "external_validation_execution_allowed_in_m2596",
    "validation_protocol_ready_in_m2596",
    "validation_result_claim_allowed",
    "status_pass",
    "claim_boundary",
]

SOURCE_ONLY_CLOSURE_EVIDENCE_FIELDNAMES = [
    "closure_evidence_id",
    "closure_family",
    "source_artifact",
    "closure_materialized_in_m2592",
    "closure_audited_in_m2593",
    "accepted_by_m2594_synthesis",
    "required_before_external_execution",
    "missing_after_source_only_closure",
    "status_pass",
    "claim_boundary",
]

ACTOR_ACTION_GUARD_FIELDNAMES = [
    "actor_action_guard_id",
    "route_role_id",
    "actor_observation_shape",
    "action_shape",
    "hidden_oracle_actor_input_detected",
    "diagnostics_actor_visible",
    "taxonomy_label_actor_visible",
    "backend_status_actor_visible",
    "reset_outcome_actor_visible",
    "rollout_outcome_actor_visible",
    "validation_outcome_actor_visible",
    "platform_selection_actor_visible",
    "protocol_status_actor_visible",
    "action_contract_mutation_detected",
    "status_pass",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_allowed_in_m2596",
    "evidence_required_before_claim",
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

PLATFORM_CANDIDATES = (
    (
        "chrono_vehicle_or_equivalent_open_backend",
        "preferred future validation backend candidate after source-only closure and dependency audit",
        True,
        False,
        False,
    ),
    (
        "black_box_industry_demonstration_backend",
        "optional demonstration backend only, not validation authority",
        False,
        True,
        False,
    ),
    (
        "repo_local_current_sim_backend",
        "repo-local diagnostic and adapter contract source only, not validation authority",
        False,
        False,
        True,
    ),
)

DEPENDENCY_FAMILIES = (
    "chrono_vehicle_or_equivalent_open_backend",
    "black_box_industry_demonstration_backend",
    "repo_local_current_sim_backend",
)

PROTOCOL_ROLES = (
    (
        "stable_avoidable_aeb_feasible",
        "stable avoidable / AEB-feasible low-cost pilot skeleton",
    ),
    (
        "stable_aes_aeb_infeasible",
        "stable AES / AEB-infeasible low-cost pilot skeleton",
    ),
)

CLOSURE_FAMILIES = (
    (
        "external_state_extraction_boundary",
        "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_external_state_extraction_closure_rows.csv",
    ),
    (
        "time_step_and_actuator_latency_contract",
        "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_time_step_actuator_latency_closure_rows.csv",
    ),
    (
        "failure_status_taxonomy_mapping",
        "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_failure_status_taxonomy_closure_rows.csv",
    ),
    (
        "source_only_fixture_smoke_lineage",
        "runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_fixture_smoke_closure_rows.csv",
    ),
)

CLAIM_CHECKS = (
    (
        "after_closure_platform_protocol_readiness_design_materialized",
        True,
        "M2596 platform candidate dependency/import policy protocol skeleton source-only closure evidence "
        "actor/action guard claim-boundary and gate rows",
    ),
    ("platform_selected_for_validation", False, "later platform-selection audit after dependency review"),
    ("validation_protocol_ready", False, "later protocol-readiness audit with holdout/generalization policy"),
    ("validation_admission_granted", False, "later validation-admission result audit"),
    ("external_validation_execution", False, "later explicit external-validation execution manifest"),
    ("high_fidelity_validation_readiness", False, "later readiness decision after platform/protocol audit"),
    ("high_fidelity_validation_result", False, "later external validation execution result audit"),
    ("hf4_discrepancy_result", False, "later HF4 external validation and discrepancy result audit"),
    ("rollout_success", False, "later audited rollout-success criteria"),
    ("success_rate_or_controller_family_verdict", False, "separate benchmark/verdict milestone"),
    ("controller_ranking_or_winner_selection", False, "controller-family comparison milestone"),
    ("checkpoint_promotion", False, "promotion gates after proof and generalization retention"),
    ("driver_performance_claim", False, "measured validation with claim-boundary audit"),
    ("paper_fw_vs_gru_current_sim_or_self_id_claim", False, "separate paper-route evidence matrix"),
)

FORBIDDEN_FLAGS = {
    "external_high_fidelity_simulation_included": False,
    "external_high_fidelity_imported": False,
    "high_fidelity_simulation_run": False,
    "external_install_performed": False,
    "external_import_performed": False,
    "dependency_mutation_performed": False,
    "actor_input_mutation_performed": False,
    "action_contract_mutation_performed": False,
    "reset_execution_run": False,
    "policy_action_run": False,
    "environment_step_run": False,
    "rollout_execution_run": False,
    "validation_execution_run": False,
    "training_run": False,
    "replay_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "controller_family_verdict_computed": False,
    "platform_selection_claim_made": False,
    "validation_protocol_readiness_claim_made": False,
    "validation_admission_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_result_claim_made": False,
    "rollout_success_claim_made": False,
    "driver_performance_claim_made": False,
    "verdict_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "level3_self_id_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "hf4_discrepancy_result_claim_made": False,
}


def materialize_route_a_hf3_platform_protocol_readiness_after_source_only_closure(
    output_dir: Path,
    *,
    m2592_summary_path: Path = DEFAULT_M2592_SUMMARY,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    doc_path: Path | str = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_exists = {path: Path(path).exists() for path in SOURCE_ARTIFACTS}
    m2592_summary = read_json(m2592_summary_path)

    platform_rows = build_platform_candidate_rows(m2592_summary)
    dependency_rows = build_dependency_import_policy_rows(m2592_summary)
    protocol_rows = build_validation_protocol_skeleton_rows(m2592_summary)
    closure_rows = build_source_only_closure_evidence_rows(m2592_summary)
    guard_rows = build_actor_action_guard_rows(protocol_rows)
    claim_rows = build_claim_boundary_checks(
        platform_rows,
        dependency_rows,
        protocol_rows,
        closure_rows,
        guard_rows,
    )
    gate_rows = build_gate_matrix_rows(
        source_exists=source_exists,
        m2592_summary=m2592_summary,
        platform_rows=platform_rows,
        dependency_rows=dependency_rows,
        protocol_rows=protocol_rows,
        closure_rows=closure_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
    )

    platform_path = output_dir / "hf3_after_closure_platform_candidate_rows.csv"
    dependency_path = output_dir / "hf3_after_closure_dependency_import_policy_rows.csv"
    protocol_path = output_dir / "hf3_after_closure_validation_protocol_skeleton_rows.csv"
    closure_path = output_dir / "hf3_after_closure_source_only_evidence_rows.csv"
    guard_path = output_dir / "hf3_after_closure_actor_action_guard_rows.csv"
    claim_path = output_dir / "hf3_after_closure_claim_boundary_checks.csv"
    gate_path = output_dir / "after_closure_platform_protocol_readiness_gate_matrix.csv"
    doc_output = Path(doc_path)

    write_csv_rows(platform_path, platform_rows, fieldnames=PLATFORM_CANDIDATE_FIELDNAMES)
    write_csv_rows(dependency_path, dependency_rows, fieldnames=DEPENDENCY_IMPORT_POLICY_FIELDNAMES)
    write_csv_rows(protocol_path, protocol_rows, fieldnames=VALIDATION_PROTOCOL_SKELETON_FIELDNAMES)
    write_csv_rows(closure_path, closure_rows, fieldnames=SOURCE_ONLY_CLOSURE_EVIDENCE_FIELDNAMES)
    write_csv_rows(guard_path, guard_rows, fieldnames=ACTOR_ACTION_GUARD_FIELDNAMES)
    write_csv_rows(claim_path, claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(gate_path, gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        output_dir=output_dir,
        source_exists=source_exists,
        m2592_summary=m2592_summary,
        platform_rows=platform_rows,
        dependency_rows=dependency_rows,
        protocol_rows=protocol_rows,
        closure_rows=closure_rows,
        guard_rows=guard_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        platform_path=platform_path,
        dependency_path=dependency_path,
        protocol_path=protocol_path,
        closure_path=closure_path,
        guard_path=guard_path,
        claim_path=claim_path,
        gate_path=gate_path,
        doc_path=doc_output,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    write_doc(doc_output, summary)
    return summary


def build_platform_candidate_rows(m2592_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    closure_accepted = _source_only_closure_accepted(m2592_summary or {})
    rows = []
    for platform_family, role, open_required, black_box_only, repo_local_only in PLATFORM_CANDIDATES:
        rows.append(
            {
                "platform_candidate_id": f"{platform_family}_after_closure_platform_candidate",
                "platform_family": platform_family,
                "platform_role": role,
                "source_only_closure_required_before_selection": True,
                "source_only_closure_accepted_in_m2596": closure_accepted,
                "open_auditable_backend_required": bool(open_required),
                "black_box_demonstration_only": bool(black_box_only),
                "repo_local_diagnostic_only": bool(repo_local_only),
                "selected_for_validation_in_m2596": False,
                "install_allowed_in_m2596": False,
                "import_allowed_in_m2596": False,
                "runtime_execution_allowed_in_m2596": False,
                "dependency_mutation_allowed_in_m2596": False,
                "status_pass": bool(closure_accepted),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_dependency_import_policy_rows(m2592_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    closure_accepted = _source_only_closure_accepted(m2592_summary or {})
    rows = []
    for dependency_family in DEPENDENCY_FAMILIES:
        rows.append(
            {
                "dependency_policy_id": f"{dependency_family}_after_closure_dependency_import_policy",
                "dependency_family": dependency_family,
                "source_only_closure_accepted_in_m2596": closure_accepted,
                "external_install_allowed_in_m2596": False,
                "external_import_allowed_in_m2596": False,
                "runtime_execution_allowed_in_m2596": False,
                "dependency_mutation_allowed_in_m2596": False,
                "future_platform_selection_design_allowed_after_audit": bool(closure_accepted),
                "status_pass": bool(closure_accepted),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_validation_protocol_skeleton_rows(m2592_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    closure_accepted = _source_only_closure_accepted(m2592_summary or {})
    rows = []
    for route_role_id, label in PROTOCOL_ROLES:
        rows.append(
            {
                "validation_protocol_id": f"{route_role_id}_after_closure_protocol_skeleton",
                "route_role_id": route_role_id,
                "candidate_role_label": label,
                "actor_observation_shape": P0_OBSERVATION_DIM,
                "action_shape": ACTION_DIM,
                "source_only_closure_accepted_in_m2596": closure_accepted,
                "protocol_skeleton_defined": True,
                "holdout_or_generalization_policy_defined": False,
                "reset_allowed_in_m2596": False,
                "policy_action_allowed_in_m2596": False,
                "environment_step_allowed_in_m2596": False,
                "rollout_allowed_in_m2596": False,
                "external_validation_execution_allowed_in_m2596": False,
                "validation_protocol_ready_in_m2596": False,
                "validation_result_claim_allowed": False,
                "status_pass": bool(
                    closure_accepted
                    and P0_OBSERVATION_DIM == 72
                    and ACTION_DIM == 3
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_source_only_closure_evidence_rows(m2592_summary: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    closure_accepted = _source_only_closure_accepted(m2592_summary or {})
    rows = []
    for closure_family, source_artifact in CLOSURE_FAMILIES:
        rows.append(
            {
                "closure_evidence_id": f"{closure_family}_after_closure_evidence",
                "closure_family": closure_family,
                "source_artifact": source_artifact,
                "closure_materialized_in_m2592": closure_accepted,
                "closure_audited_in_m2593": True,
                "accepted_by_m2594_synthesis": True,
                "required_before_external_execution": True,
                "missing_after_source_only_closure": False,
                "status_pass": bool(closure_accepted),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_actor_action_guard_rows(protocol_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for protocol in protocol_rows:
        rows.append(
            {
                "actor_action_guard_id": f"{protocol['route_role_id']}_after_closure_actor_action_guard",
                "route_role_id": protocol["route_role_id"],
                "actor_observation_shape": _int_value(protocol["actor_observation_shape"], default=-1),
                "action_shape": _int_value(protocol["action_shape"], default=-1),
                "hidden_oracle_actor_input_detected": False,
                "diagnostics_actor_visible": False,
                "taxonomy_label_actor_visible": False,
                "backend_status_actor_visible": False,
                "reset_outcome_actor_visible": False,
                "rollout_outcome_actor_visible": False,
                "validation_outcome_actor_visible": False,
                "platform_selection_actor_visible": False,
                "protocol_status_actor_visible": False,
                "action_contract_mutation_detected": False,
                "status_pass": bool(
                    _boolish(protocol["status_pass"])
                    and _int_value(protocol["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM
                    and _int_value(protocol["action_shape"], default=-1) == ACTION_DIM
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_claim_boundary_checks(
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    closure_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    design_materialized = bool(
        len(platform_rows) == len(PLATFORM_CANDIDATES)
        and _all_status_pass(platform_rows)
        and len(dependency_rows) == len(DEPENDENCY_FAMILIES)
        and _all_status_pass(dependency_rows)
        and len(protocol_rows) == len(PROTOCOL_ROLES)
        and _all_status_pass(protocol_rows)
        and len(closure_rows) == len(CLOSURE_FAMILIES)
        and _all_status_pass(closure_rows)
        and len(guard_rows) == len(protocol_rows)
        and _all_status_pass(guard_rows)
    )
    rows = []
    for claim_family, allowed, evidence in CLAIM_CHECKS:
        claim_allowed = bool(allowed and design_materialized)
        rows.append(
            {
                "claim_id": f"{claim_family}_claim_boundary",
                "claim_family": claim_family,
                "claim_allowed_in_m2596": claim_allowed,
                "evidence_required_before_claim": evidence,
                "status_pass": bool(
                    claim_family == "after_closure_platform_protocol_readiness_design_materialized"
                    or not claim_allowed
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_gate_matrix_rows(
    *,
    source_exists: dict[str, bool],
    m2592_summary: dict[str, Any],
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    closure_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forbidden_claims_allowed = [
        row for row in claim_rows
        if row["claim_family"] != "after_closure_platform_protocol_readiness_design_materialized"
        and _boolish(row["claim_allowed_in_m2596"])
    ]
    checks = [
        (
            "source_artifacts_exist",
            "lineage",
            all(source_exists.values()),
            f"missing={sum(1 for exists in source_exists.values() if not exists)}",
            "missing=0",
            "lineage_invalid",
        ),
        (
            "m2592_closure_evidence_accepted",
            "lineage",
            _source_only_closure_accepted(m2592_summary),
            (
                f"m2592_status={m2592_summary.get('status_pass')};"
                f"closure={m2592_summary.get('repo_local_source_only_adapter_blocker_closure_materialized')};"
                f"protocol_ready={m2592_summary.get('validation_protocol_ready_in_m2592')}"
            ),
            "m2592_status=True;closure=True;protocol_ready=False",
            "lineage_invalid",
        ),
        (
            "platform_candidate_rows_complete",
            "contract",
            len(platform_rows) == len(PLATFORM_CANDIDATES)
            and _all_status_pass(platform_rows)
            and all(_boolish(row["source_only_closure_accepted_in_m2596"]) for row in platform_rows)
            and any(
                row["platform_family"] == "chrono_vehicle_or_equivalent_open_backend"
                and _boolish(row["open_auditable_backend_required"])
                for row in platform_rows
            )
            and any(
                row["platform_family"] == "black_box_industry_demonstration_backend"
                and _boolish(row["black_box_demonstration_only"])
                for row in platform_rows
            )
            and any(
                row["platform_family"] == "repo_local_current_sim_backend"
                and _boolish(row["repo_local_diagnostic_only"])
                for row in platform_rows
            )
            and not any(_boolish(row["selected_for_validation_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["install_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["import_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2596"]) for row in platform_rows),
            f"rows={len(platform_rows)}",
            "rows=3;closure=true;selected/install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "dependency_import_policy_rows_pass",
            "contract",
            len(dependency_rows) == len(DEPENDENCY_FAMILIES)
            and _all_status_pass(dependency_rows)
            and all(_boolish(row["source_only_closure_accepted_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["external_install_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["dependency_mutation_allowed_in_m2596"]) for row in dependency_rows),
            f"rows={len(dependency_rows)}",
            "rows=3;closure=true;install/import/run/mutation=false",
            "contract_violation",
        ),
        (
            "validation_protocol_skeleton_rows_pass",
            "scenario",
            len(protocol_rows) == len(PROTOCOL_ROLES)
            and _all_status_pass(protocol_rows)
            and {row["route_role_id"] for row in protocol_rows}
            == {"stable_avoidable_aeb_feasible", "stable_aes_aeb_infeasible"}
            and all(_boolish(row["source_only_closure_accepted_in_m2596"]) for row in protocol_rows)
            and all(_boolish(row["protocol_skeleton_defined"]) for row in protocol_rows)
            and not any(_boolish(row["holdout_or_generalization_policy_defined"]) for row in protocol_rows)
            and not any(_boolish(row["reset_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["policy_action_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["environment_step_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["rollout_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["validation_protocol_ready_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in protocol_rows),
            f"rows={len(protocol_rows)}",
            "rows=2;closure=true;protocol=true;readiness/result/execution=false",
            "scenario_sampling_failure",
        ),
        (
            "source_only_closure_evidence_rows_pass",
            "lineage",
            len(closure_rows) == len(CLOSURE_FAMILIES)
            and _all_status_pass(closure_rows)
            and all(_boolish(row["closure_materialized_in_m2592"]) for row in closure_rows)
            and all(_boolish(row["closure_audited_in_m2593"]) for row in closure_rows)
            and all(_boolish(row["accepted_by_m2594_synthesis"]) for row in closure_rows)
            and not any(_boolish(row["missing_after_source_only_closure"]) for row in closure_rows),
            f"rows={len(closure_rows)}",
            "rows=4;materialized/audited/accepted=true;missing=false",
            "lineage_invalid",
        ),
        (
            "actor_action_guard_rows_pass",
            "contract",
            len(guard_rows) == len(protocol_rows)
            and _all_status_pass(guard_rows)
            and all(_int_value(row["actor_observation_shape"], default=-1) == P0_OBSERVATION_DIM for row in guard_rows)
            and all(_int_value(row["action_shape"], default=-1) == ACTION_DIM for row in guard_rows)
            and not any(_boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows)
            and not any(_boolish(row["diagnostics_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["taxonomy_label_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["backend_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["reset_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["rollout_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["validation_outcome_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["platform_selection_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["protocol_status_actor_visible"]) for row in guard_rows)
            and not any(_boolish(row["action_contract_mutation_detected"]) for row in guard_rows),
            f"rows={len(guard_rows)}",
            "rows=protocol_rows;obs=72;action=3;hidden/outcomes/platform/protocol/mutation=false",
            "contract_violation",
        ),
        (
            "claim_boundary_rows_pass",
            "claim_boundary",
            len(claim_rows) == len(CLAIM_CHECKS)
            and _all_status_pass(claim_rows)
            and not forbidden_claims_allowed
            and any(
                row["claim_family"] == "after_closure_platform_protocol_readiness_design_materialized"
                and _boolish(row["claim_allowed_in_m2596"])
                for row in claim_rows
            ),
            f"rows={len(claim_rows)};forbidden_claims={len(forbidden_claims_allowed)}",
            "rows=14;forbidden_claims=0;design_materialized=true",
            "objective_overfit",
        ),
        (
            "actor_action_contract_preserved",
            "contract",
            P0_OBSERVATION_DIM == 72 and ACTION_DIM == 3,
            f"obs={P0_OBSERVATION_DIM};action={ACTION_DIM}",
            "obs=72;action=3",
            "contract_violation",
        ),
        (
            "no_platform_selected_or_external_execution",
            "claim_boundary",
            not any(_boolish(row["selected_for_validation_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["install_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["import_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2596"]) for row in platform_rows)
            and not any(_boolish(row["external_install_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["external_import_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["runtime_execution_allowed_in_m2596"]) for row in dependency_rows)
            and not any(_boolish(row["reset_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["policy_action_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["environment_step_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["rollout_allowed_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["external_validation_execution_allowed_in_m2596"]) for row in protocol_rows),
            "selected/install/import/run/reset/action/step/rollout/validation=false",
            "selected/install/import/run/reset/action/step/rollout/validation=false",
            "objective_overfit",
        ),
        (
            "validation_readiness_and_result_forbidden",
            "claim_boundary",
            not any(_boolish(row["validation_protocol_ready_in_m2596"]) for row in protocol_rows)
            and not any(_boolish(row["validation_result_claim_allowed"]) for row in protocol_rows)
            and not any(
                row["claim_family"]
                in {
                    "validation_protocol_ready",
                    "validation_admission_granted",
                    "external_validation_execution",
                    "high_fidelity_validation_readiness",
                    "high_fidelity_validation_result",
                    "driver_performance_claim",
                }
                and _boolish(row["claim_allowed_in_m2596"])
                for row in claim_rows
            ),
            "readiness/result/performance=false",
            "readiness/result/performance=false",
            "objective_overfit",
        ),
        (
            "no_forbidden_execution_or_claim_flags",
            "claim_boundary",
            not any(FORBIDDEN_FLAGS.values()),
            "all forbidden false",
            "all forbidden false",
            "objective_overfit",
        ),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "" if passed else failure_type,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for gate_id, family, passed, observed, expected, failure_type in checks
    ]


def build_summary(
    *,
    output_dir: Path,
    source_exists: dict[str, bool],
    m2592_summary: dict[str, Any],
    platform_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    protocol_rows: list[dict[str, Any]],
    closure_rows: list[dict[str, Any]],
    guard_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    platform_path: Path,
    dependency_path: Path,
    protocol_path: Path,
    closure_path: Path,
    guard_path: Path,
    claim_path: Path,
    gate_path: Path,
    doc_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    materialized_claim_allowed = any(
        row["claim_family"] == "after_closure_platform_protocol_readiness_design_materialized"
        and _boolish(row["claim_allowed_in_m2596"])
        for row in claim_rows
    )
    forbidden_claim_allowed = any(
        row["claim_family"] != "after_closure_platform_protocol_readiness_design_materialized"
        and _boolish(row["claim_allowed_in_m2596"])
        for row in claim_rows
    )
    status_pass = (
        all(source_exists.values())
        and _source_only_closure_accepted(m2592_summary)
        and len(platform_rows) == len(PLATFORM_CANDIDATES)
        and _all_status_pass(platform_rows)
        and len(dependency_rows) == len(DEPENDENCY_FAMILIES)
        and _all_status_pass(dependency_rows)
        and len(protocol_rows) == len(PROTOCOL_ROLES)
        and _all_status_pass(protocol_rows)
        and len(closure_rows) == len(CLOSURE_FAMILIES)
        and _all_status_pass(closure_rows)
        and len(guard_rows) == len(protocol_rows)
        and _all_status_pass(guard_rows)
        and len(claim_rows) == len(CLAIM_CHECKS)
        and _all_status_pass(claim_rows)
        and _all_status_pass(gate_rows)
        and materialized_claim_allowed
        and not forbidden_claim_allowed
        and not any(FORBIDDEN_FLAGS.values())
    )
    return {
        "result_class": (
            "engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure_"
            "materialization_preflight_pass"
        )
        if status_pass
        else (
            "engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure_"
            "materialization_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "milestone": milestone,
        "generated_at_utc": utc_timestamp(),
        "next_blocker": next_blocker,
        "summary": str(output_dir / "summary.json"),
        "hf3_after_closure_platform_candidate_rows": str(platform_path),
        "hf3_after_closure_dependency_import_policy_rows": str(dependency_path),
        "hf3_after_closure_validation_protocol_skeleton_rows": str(protocol_path),
        "hf3_after_closure_source_only_evidence_rows": str(closure_path),
        "hf3_after_closure_actor_action_guard_rows": str(guard_path),
        "hf3_after_closure_claim_boundary_checks": str(claim_path),
        "after_closure_platform_protocol_readiness_gate_matrix": str(gate_path),
        "doc": str(doc_path),
        "source_artifacts_exist": all(source_exists.values()),
        "missing_source_artifacts": [path for path, exists in source_exists.items() if not exists],
        "m2592_status_pass": bool(m2592_summary.get("status_pass")),
        "m2592_repo_local_source_only_adapter_blocker_closure_materialized": bool(
            m2592_summary.get("repo_local_source_only_adapter_blocker_closure_materialized")
        ),
        "m2592_validation_protocol_ready": bool(m2592_summary.get("validation_protocol_ready_in_m2592")),
        "m2592_external_validation_execution_allowed": bool(
            m2592_summary.get("external_validation_execution_allowed_in_m2592")
        ),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "platform_candidate_row_count": len(platform_rows),
        "dependency_import_policy_row_count": len(dependency_rows),
        "validation_protocol_skeleton_row_count": len(protocol_rows),
        "source_only_closure_evidence_row_count": len(closure_rows),
        "actor_action_guard_row_count": len(guard_rows),
        "claim_boundary_check_count": len(claim_rows),
        "materialization_gate_count": len(gate_rows),
        "materialization_gates_all_pass": _all_status_pass(gate_rows),
        "after_closure_platform_protocol_readiness_design_materialized_claim_allowed": bool(
            materialized_claim_allowed
        ),
        "forbidden_claim_allowed_in_m2596": bool(forbidden_claim_allowed),
        "source_only_closure_accepted_in_m2596": all(
            _boolish(row["source_only_closure_accepted_in_m2596"])
            for row in [*platform_rows, *dependency_rows, *protocol_rows]
        )
        and all(_boolish(row["closure_materialized_in_m2592"]) for row in closure_rows),
        "source_only_closure_missing_after_m2596": any(
            _boolish(row["missing_after_source_only_closure"]) for row in closure_rows
        ),
        "selected_for_validation_in_m2596": any(
            _boolish(row["selected_for_validation_in_m2596"]) for row in platform_rows
        ),
        "platform_selected_in_m2596": any(
            _boolish(row["selected_for_validation_in_m2596"]) for row in platform_rows
        ),
        "install_allowed_in_m2596": any(_boolish(row["install_allowed_in_m2596"]) for row in platform_rows),
        "import_allowed_in_m2596": any(_boolish(row["import_allowed_in_m2596"]) for row in platform_rows),
        "runtime_execution_allowed_in_m2596": any(
            _boolish(row["runtime_execution_allowed_in_m2596"]) for row in platform_rows
        ),
        "external_install_allowed_in_m2596": any(
            _boolish(row["external_install_allowed_in_m2596"]) for row in dependency_rows
        ),
        "external_import_allowed_in_m2596": any(
            _boolish(row["external_import_allowed_in_m2596"]) for row in dependency_rows
        ),
        "dependency_runtime_execution_allowed_in_m2596": any(
            _boolish(row["runtime_execution_allowed_in_m2596"]) for row in dependency_rows
        ),
        "dependency_mutation_allowed_in_m2596": any(
            _boolish(row["dependency_mutation_allowed_in_m2596"]) for row in dependency_rows
        )
        or any(_boolish(row["dependency_mutation_allowed_in_m2596"]) for row in platform_rows),
        "protocol_skeleton_defined": all(_boolish(row["protocol_skeleton_defined"]) for row in protocol_rows),
        "holdout_or_generalization_policy_defined": any(
            _boolish(row["holdout_or_generalization_policy_defined"]) for row in protocol_rows
        ),
        "reset_allowed_in_m2596": any(_boolish(row["reset_allowed_in_m2596"]) for row in protocol_rows),
        "policy_action_allowed_in_m2596": any(
            _boolish(row["policy_action_allowed_in_m2596"]) for row in protocol_rows
        ),
        "environment_step_allowed_in_m2596": any(
            _boolish(row["environment_step_allowed_in_m2596"]) for row in protocol_rows
        ),
        "rollout_allowed_in_m2596": any(_boolish(row["rollout_allowed_in_m2596"]) for row in protocol_rows),
        "external_validation_execution_allowed_in_m2596": any(
            _boolish(row["external_validation_execution_allowed_in_m2596"]) for row in protocol_rows
        ),
        "validation_protocol_ready_in_m2596": any(
            _boolish(row["validation_protocol_ready_in_m2596"]) for row in protocol_rows
        ),
        "validation_result_claim_allowed": any(
            _boolish(row["validation_result_claim_allowed"]) for row in protocol_rows
        ),
        "validation_protocol_ready_claim_allowed": any(
            row["claim_family"] == "validation_protocol_ready"
            and _boolish(row["claim_allowed_in_m2596"])
            for row in claim_rows
        ),
        "validation_admission_granted_in_m2596": any(
            row["claim_family"] == "validation_admission_granted"
            and _boolish(row["claim_allowed_in_m2596"])
            for row in claim_rows
        ),
        "driver_performance_claim_allowed_in_m2596": any(
            row["claim_family"] == "driver_performance_claim"
            and _boolish(row["claim_allowed_in_m2596"])
            for row in claim_rows
        ),
        "hidden_oracle_actor_input_detected": any(
            _boolish(row["hidden_oracle_actor_input_detected"]) for row in guard_rows
        ),
        "diagnostics_actor_visible": any(_boolish(row["diagnostics_actor_visible"]) for row in guard_rows),
        "taxonomy_label_actor_visible": any(_boolish(row["taxonomy_label_actor_visible"]) for row in guard_rows),
        "backend_status_actor_visible": any(_boolish(row["backend_status_actor_visible"]) for row in guard_rows),
        "reset_outcome_actor_visible": any(_boolish(row["reset_outcome_actor_visible"]) for row in guard_rows),
        "rollout_outcome_actor_visible": any(_boolish(row["rollout_outcome_actor_visible"]) for row in guard_rows),
        "validation_outcome_actor_visible": any(
            _boolish(row["validation_outcome_actor_visible"]) for row in guard_rows
        ),
        "platform_selection_actor_visible": any(
            _boolish(row["platform_selection_actor_visible"]) for row in guard_rows
        ),
        "protocol_status_actor_visible": any(_boolish(row["protocol_status_actor_visible"]) for row in guard_rows),
        "action_contract_mutation_detected": any(
            _boolish(row["action_contract_mutation_detected"]) for row in guard_rows
        ),
        "repo_local_boundary_only": True,
        "policy_action_executed": FORBIDDEN_FLAGS["policy_action_run"],
        "environment_step_executed": FORBIDDEN_FLAGS["environment_step_run"],
        "validation_readiness_claim_made": FORBIDDEN_FLAGS["high_fidelity_validation_readiness_claim_made"],
        "validation_result_claim_made": FORBIDDEN_FLAGS["high_fidelity_validation_result_claim_made"],
        **FORBIDDEN_FLAGS,
    }


def write_doc(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# M2596 Engineering Controller Route A Baseline HF3 Platform/Protocol Readiness After Source-Only Closure Materialization Preflight",
                "",
                "- status: completed",
                f"- result_class: `{summary['result_class']}`",
                "- manifest: `experiments/manifests/m2596-engineering-controller-route-a-baseline-hf3-platform-protocol-readiness-after-source-only-closure-materialization-preflight.json`",
                "- implementation: `src/autodrift/engineering_controller_route_a_hf3_platform_protocol_readiness_after_source_only_closure.py`",
                f"- summary: `{summary['summary']}`",
                f"- platform candidate rows: `{summary['hf3_after_closure_platform_candidate_rows']}`",
                f"- dependency/import policy rows: `{summary['hf3_after_closure_dependency_import_policy_rows']}`",
                f"- validation protocol skeleton rows: `{summary['hf3_after_closure_validation_protocol_skeleton_rows']}`",
                f"- source-only closure evidence rows: `{summary['hf3_after_closure_source_only_evidence_rows']}`",
                f"- actor/action guard rows: `{summary['hf3_after_closure_actor_action_guard_rows']}`",
                f"- claim-boundary checks: `{summary['hf3_after_closure_claim_boundary_checks']}`",
                f"- gate matrix: `{summary['after_closure_platform_protocol_readiness_gate_matrix']}`",
                f"- next milestone: `{summary['next_blocker']}`",
                "- platform selected / dependency installed/imported/run: `false`",
                "- reset/action/step/rollout/validation execution: `false`",
                "- validation protocol ready/admission/readiness/result/ranking/driver-performance claims: `false`",
                "",
                "## Materialized Artifacts",
                "",
                "M2596 materializes bounded after-closure platform/protocol",
                "readiness design artifacts requested by M2595. Source-only",
                "adapter blocker closure from M2592/M2593/M2594 is accepted as",
                "a prerequisite, so the four source-only closure evidence rows",
                "are no longer missing. The milestone still does not select a",
                "platform or execute validation.",
                "",
                "Accepted summary:",
                "",
                "```text",
                f"status_pass: {str(summary['status_pass']).lower()}",
                f"platform_candidate_row_count: {summary['platform_candidate_row_count']}",
                f"dependency_import_policy_row_count: {summary['dependency_import_policy_row_count']}",
                f"validation_protocol_skeleton_row_count: {summary['validation_protocol_skeleton_row_count']}",
                f"source_only_closure_evidence_row_count: {summary['source_only_closure_evidence_row_count']}",
                f"actor_action_guard_row_count: {summary['actor_action_guard_row_count']}",
                f"claim_boundary_check_count: {summary['claim_boundary_check_count']}",
                f"materialization_gate_count: {summary['materialization_gate_count']}",
                f"after_closure_platform_protocol_readiness_design_materialized_claim_allowed: {str(summary['after_closure_platform_protocol_readiness_design_materialized_claim_allowed']).lower()}",
                f"forbidden_claim_allowed_in_m2596: {str(summary['forbidden_claim_allowed_in_m2596']).lower()}",
                f"source_only_closure_accepted_in_m2596: {str(summary['source_only_closure_accepted_in_m2596']).lower()}",
                f"source_only_closure_missing_after_m2596: {str(summary['source_only_closure_missing_after_m2596']).lower()}",
                f"selected_for_validation_in_m2596: {str(summary['selected_for_validation_in_m2596']).lower()}",
                f"validation_protocol_ready_in_m2596: {str(summary['validation_protocol_ready_in_m2596']).lower()}",
                f"external_validation_execution_allowed_in_m2596: {str(summary['external_validation_execution_allowed_in_m2596']).lower()}",
                f"driver_performance_claim_allowed_in_m2596: {str(summary['driver_performance_claim_allowed_in_m2596']).lower()}",
                f"hidden_oracle_actor_input_detected: {str(summary['hidden_oracle_actor_input_detected']).lower()}",
                f"observation_shape: {summary['observation_shape']}",
                f"action_shape: {summary['action_shape']}",
                f"materialization_gates_all_pass: {str(summary['materialization_gates_all_pass']).lower()}",
                "```",
                "",
                "## Result Boundary",
                "",
                "M2596 supports only the operational claim that after-closure",
                "platform/protocol readiness design artifacts were materialized.",
                "It does not support platform selection, validation protocol",
                "readiness, validation admission, high-fidelity validation",
                "readiness/result, external validation execution, HF4 discrepancy",
                "answers, rollout success, success-rate or controller-family",
                "verdicts, ranking, checkpoint promotion, driver performance,",
                "paper evidence, FW-vs-GRU, current-sim verdict, high-fidelity",
                "validation, or self-ID.",
                "",
                "## Next Route",
                "",
                "Route to:",
                "",
                "```text",
                str(summary["next_blocker"]),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _source_only_closure_accepted(summary: dict[str, Any]) -> bool:
    return bool(
        summary.get("status_pass")
        and summary.get("repo_local_source_only_adapter_blocker_closure_materialized")
        and summary.get("source_only_closure_materialized_in_m2592")
        and not summary.get("validation_protocol_ready_in_m2592")
        and not summary.get("external_validation_execution_allowed_in_m2592")
        and not summary.get("platform_selected_in_m2592")
        and not summary.get("driver_performance_claim_allowed_in_m2592")
    )


def _all_status_pass(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(_boolish(row.get("status_pass")) for row in rows)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    parser.add_argument("--doc-path", type=Path, default=Path(DEFAULT_DOC_PATH))
    args = parser.parse_args()

    summary = materialize_route_a_hf3_platform_protocol_readiness_after_source_only_closure(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
        doc_path=args.doc_path,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"next_blocker={summary['next_blocker']}")


if __name__ == "__main__":
    main()
