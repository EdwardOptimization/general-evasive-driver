"""Materialize Route A package-with-limitations protocol rows.

This runner only reanalyzes existing Route A readiness and blocker artifacts.
It does not publish a package, run simulation, validate, train, rank, or
promote any checkpoint.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = "m2688-engineering-controller-route-a-package-with-limitations-protocol-materialization-preflight"
DEFAULT_NEXT_BLOCKER = (
    "m2689-engineering-controller-route-a-package-with-limitations-protocol-"
    "materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization")
DEFAULT_DOC_PATH = Path(
    "docs/m2688-engineering-controller-route-a-package-with-limitations-protocol-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2689-engineering-controller-route-a-package-with-limitations-protocol-materialization-result-audit.json"
)

M2687_DOC = Path("docs/m2687-engineering-controller-route-a-package-with-limitations-protocol-design.md")
M2686_DOC = Path(
    "docs/m2686-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-branch-synthesis.md"
)
M2669_DOC = Path("docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-branch-synthesis.md")
M2668_DOC = Path(
    "docs/m2668-engineering-controller-route-a-engineering-baseline-readiness-index-after-protected-taxonomy-materialization-result-audit.md"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/"
    "summary.json"
)
M2667_ARTIFACT_COVERAGE = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/"
    "artifact_coverage_rows.csv"
)
M2667_KNOWN_FAILURE = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_after_protected_taxonomy/"
    "known_failure_boundary_rows.csv"
)

M2541_BASELINE_CHECKPOINTS = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv"
)
M2541_ACTOR_CONTRACT = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json"
)
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
M2509_DOC = Path("docs/m2509-engineering-controller-runtime-inference-cost-report-result-audit.md")
M2657_SCENARIO_ROLE_REPORT = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "scenario_role_metric_report.csv"
)
M2664_SUMMARY = Path("runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json")
M2665_DOC = Path(
    "docs/m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-result-audit.md"
)
M2666_DOC = Path("docs/m2666-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-branch-synthesis.md")

M2684_SUMMARY = Path(
    "runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/"
    "summary.json"
)
M2684_OUTCOME_AGGREGATE = Path(
    "runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/"
    "outcome_aggregate.csv"
)
M2684_TERMINATION_AGGREGATE = Path(
    "runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/"
    "termination_reason_aggregate.csv"
)
M2635_SUMMARY = Path(
    "runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/"
    "summary.json"
)
M2638_DOC = Path("docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md")
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A package-with-limitations protocol materialization only; no package publication, "
    "reset, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, "
    "ranking, winner selection, promotion, success-rate verdict, driver-performance, paper, "
    "finite-window-vs-GRU, current-response, current-sim, high-fidelity validation, full ideal driver, "
    "or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "published package, deployment readiness, driver performance, validation readiness, validation result, "
    "source-build readiness/result, adapter-probe readiness/result, backend availability, reset feasibility, "
    "rollout feasibility, controller ranking, winner selection, checkpoint promotion, repair success, "
    "success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, "
    "current-sim verdict, high-fidelity validation result, full ideal driver completion, or self-ID evidence"
)

FALSE_CLAIM_FLAGS = {
    "package_published": False,
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
}

SCHEMA_FIELDNAMES = [
    "field_name",
    "required",
    "source",
    "allowed_values_or_type",
    "claim_scope",
    "blocked_interpretation",
]
ARTIFACT_FIELDNAMES = [
    "artifact_id",
    "source_milestone",
    "source_path",
    "source_exists",
    "status_pass_or_present",
    "package_required",
    "package_inclusion_status",
    "row_count_or_summary",
    "artifact_role",
    "claim_scope",
    "blocked_interpretation",
]
PROVENANCE_FIELDNAMES = [
    "provenance_id",
    "source_milestone",
    "source_path",
    "target_artifact_id",
    "relationship",
    "source_exists",
    "status_pass_or_present",
    "package_content_or_context",
    "claim_scope",
    "blocked_interpretation",
]
BLOCKER_FIELDNAMES = [
    "blocker_id",
    "source_milestone",
    "evidence_path",
    "blocker_status",
    "package_disclosure_required",
    "blocked_claims",
    "resume_condition",
    "actor_visible",
    "claim_scope",
]
ACTOR_FIELDNAMES = [
    "contract_row_id",
    "contract_field",
    "observed_value",
    "expected_value",
    "status_pass",
    "actor_visible",
    "claim_scope",
    "blocked_interpretation",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2688",
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

REQUIRED_SCHEMA_FIELDS = [
    ("package_id", True, "M2687 design", "string"),
    ("package_protocol_version", True, "M2687 design", "string"),
    ("generated_at_utc", True, "runner clock", "UTC timestamp string"),
    ("route", True, "M2687 design", "Route A"),
    ("artifact_id", True, "artifact inventory", "string"),
    ("source_milestone", True, "artifact inventory", "string"),
    ("source_path", True, "artifact inventory", "path string"),
    ("source_exists", True, "filesystem", "boolean"),
    ("source_status_pass_or_present", True, "source summary/doc", "boolean"),
    ("artifact_role", True, "M2687 design", "package_content or supporting_context"),
    ("package_required", True, "M2687 design", "boolean"),
    ("package_inclusion_status", True, "artifact inventory", "included_with_limitations or context_only"),
    ("provenance_status", True, "provenance map", "traced or missing"),
    ("actor_visible", True, "actor contract", "boolean"),
    ("claim_scope", True, "M2687 design", "string"),
    ("blocked_interpretation", True, "M2687 design", "string"),
    ("known_blocker_refs", True, "blocker disclosure", "semicolon-separated blocker ids"),
]


def materialize_package_with_limitations_protocol(
    output_dir: Path | str,
    *,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts(follow_up_manifest=follow_up_manifest)
    schema_rows = build_package_manifest_schema_rows()
    artifact_rows = build_package_artifact_inventory_rows(source)
    provenance_rows = build_package_provenance_map_rows(source)
    blocker_rows = build_known_blocker_disclosure_rows(source)
    actor_rows = build_actor_action_contract_rows(source)
    claim_rows = build_claim_boundary_rows()
    paths = {
        "summary": output_path / "summary.json",
        "package_manifest_schema_rows": output_path / "package_manifest_schema_rows.csv",
        "package_artifact_inventory_rows": output_path / "package_artifact_inventory_rows.csv",
        "package_provenance_map_rows": output_path / "package_provenance_map_rows.csv",
        "known_blocker_disclosure_rows": output_path / "known_blocker_disclosure_rows.csv",
        "actor_action_contract_rows": output_path / "actor_action_contract_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "package_protocol_gate_matrix": output_path / "package_protocol_gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["package_manifest_schema_rows"], schema_rows, fieldnames=SCHEMA_FIELDNAMES)
    write_csv_rows(paths["package_artifact_inventory_rows"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)
    write_csv_rows(paths["package_provenance_map_rows"], provenance_rows, fieldnames=PROVENANCE_FIELDNAMES)
    write_csv_rows(paths["known_blocker_disclosure_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["actor_action_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        schema_rows,
        artifact_rows,
        provenance_rows,
        blocker_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["package_protocol_gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        schema_rows=schema_rows,
        artifact_rows=artifact_rows,
        provenance_rows=provenance_rows,
        blocker_rows=blocker_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_matrix_rows(
        source,
        schema_rows,
        artifact_rows,
        provenance_rows,
        blocker_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["package_protocol_gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        schema_rows=schema_rows,
        artifact_rows=artifact_rows,
        provenance_rows=provenance_rows,
        blocker_rows=blocker_rows,
        actor_rows=actor_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["summary"], summary)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
    return summary


def load_source_artifacts(*, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2687_doc": M2687_DOC,
        "m2686_doc": M2686_DOC,
        "m2669_doc": M2669_DOC,
        "m2668_doc": M2668_DOC,
        "m2667_summary": M2667_SUMMARY,
        "m2667_artifact_coverage": M2667_ARTIFACT_COVERAGE,
        "m2667_known_failure": M2667_KNOWN_FAILURE,
        "m2541_baseline_checkpoints": M2541_BASELINE_CHECKPOINTS,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2505_summary": M2505_SUMMARY,
        "m2508_summary": M2508_SUMMARY,
        "m2509_doc": M2509_DOC,
        "m2657_scenario_role_report": M2657_SCENARIO_ROLE_REPORT,
        "m2664_summary": M2664_SUMMARY,
        "m2665_doc": M2665_DOC,
        "m2666_doc": M2666_DOC,
        "m2684_summary": M2684_SUMMARY,
        "m2684_outcome_aggregate": M2684_OUTCOME_AGGREGATE,
        "m2684_termination_aggregate": M2684_TERMINATION_AGGREGATE,
        "m2635_summary": M2635_SUMMARY,
        "m2638_doc": M2638_DOC,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2667_summary": read_json(paths["m2667_summary"]),
        "m2667_artifact_coverage": _read_csv_rows(paths["m2667_artifact_coverage"]),
        "m2667_known_failure": _read_csv_rows(paths["m2667_known_failure"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
        "m2664_summary": read_json(paths["m2664_summary"]),
        "m2684_summary": read_json(paths["m2684_summary"]),
        "m2684_outcome_aggregate": _read_csv_rows(paths["m2684_outcome_aggregate"]),
        "m2684_termination_aggregate": _read_csv_rows(paths["m2684_termination_aggregate"]),
        "m2635_summary": read_json(paths["m2635_summary"]),
    }


def build_package_manifest_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "field_name": field_name,
            "required": required,
            "source": source,
            "allowed_values_or_type": allowed_values_or_type,
            "claim_scope": CLAIM_SCOPE,
            "blocked_interpretation": FORBIDDEN_INTERPRETATION,
        }
        for field_name, required, source, allowed_values_or_type in REQUIRED_SCHEMA_FIELDS
    ]


def build_package_artifact_inventory_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2667_rows = {row["artifact_id"]: row for row in source["m2667_artifact_coverage"]}
    m2667 = source["m2667_summary"]
    specs = [
        (
            "baseline_checkpoint_list",
            "m2541",
            source["paths"]["m2541_baseline_checkpoints"],
            True,
            m2667_rows["baseline_checkpoint_list"].get("status_pass_or_present"),
            m2667_rows["baseline_checkpoint_list"].get("row_count"),
            "package_content",
        ),
        (
            "actor_input_output_contract",
            "m2541",
            source["paths"]["m2541_actor_contract"],
            True,
            m2667_rows["actor_input_output_contract"].get("status_pass_or_present"),
            m2667_rows["actor_input_output_contract"].get("row_count"),
            "package_content",
        ),
        (
            "public_benchmark_pack",
            "m2505",
            source["paths"]["m2505_summary"],
            True,
            m2667_rows["public_benchmark_pack"].get("status_pass_or_present"),
            m2667_rows["public_benchmark_pack"].get("row_count"),
            "package_content",
        ),
        (
            "runtime_inference_cost_report",
            "m2508/m2509",
            source["paths"]["m2508_summary"],
            True,
            m2667_rows["runtime_inference_cost_report"].get("status_pass_or_present"),
            m2667_rows["runtime_inference_cost_report"].get("row_count"),
            "package_content",
        ),
        (
            "scenario_role_metric_report",
            "m2657",
            source["paths"]["m2657_scenario_role_report"],
            True,
            m2667_rows["scenario_role_metric_report"].get("status_pass_or_present"),
            m2667_rows["scenario_role_metric_report"].get("row_count"),
            "package_content",
        ),
        (
            "known_failure_taxonomy",
            "m2664/m2665/m2666",
            source["paths"]["m2664_summary"],
            True,
            m2667_rows["known_failure_taxonomy"].get("status_pass_or_present"),
            m2667_rows["known_failure_taxonomy"].get("row_count"),
            "package_content",
        ),
        (
            "route_a_readiness_index",
            "m2667/m2668/m2669",
            source["paths"]["m2667_summary"],
            False,
            m2667.get("status_pass"),
            m2667.get("artifact_coverage_row_count"),
            "supporting_context",
        ),
        (
            "route_b_current_sim_offtrack_blocker",
            "m2684/m2685/m2686",
            source["paths"]["m2684_summary"],
            False,
            source["m2684_summary"].get("status_pass") and source["source_exists"]["m2686_doc"],
            source["m2684_summary"].get("episode_count"),
            "supporting_context",
        ),
        (
            "hf3_source_dependency_blocker",
            "m2635/m2636/m2637/m2638",
            source["paths"]["m2635_summary"],
            False,
            source["m2635_summary"].get("status_pass") and source["source_exists"]["m2638_doc"],
            source["m2635_summary"].get("artifact_manifest_row_count"),
            "supporting_context",
        ),
        (
            "post_m2470_route_plan",
            "post-m2470",
            source["paths"]["route_plan"],
            False,
            source["source_exists"]["route_plan"],
            1,
            "supporting_context",
        ),
    ]
    rows = []
    for artifact_id, milestone, path, package_required, status, row_count, role in specs:
        exists = Path(path).exists()
        status_pass = exists and _bool(status)
        rows.append(
            {
                "artifact_id": artifact_id,
                "source_milestone": milestone,
                "source_path": str(path),
                "source_exists": exists,
                "status_pass_or_present": status_pass,
                "package_required": package_required,
                "package_inclusion_status": (
                    "included_with_limitations"
                    if package_required and status_pass
                    else "context_only"
                    if status_pass
                    else "blocked_missing_or_not_passing"
                ),
                "row_count_or_summary": _int(row_count),
                "artifact_role": role,
                "claim_scope": CLAIM_SCOPE,
                "blocked_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_package_provenance_map_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2541_baseline_checkpoint_list", "m2541", source["paths"]["m2541_baseline_checkpoints"], "baseline_checkpoint_list", "package input"),
        ("m2541_actor_io_contract", "m2541", source["paths"]["m2541_actor_contract"], "actor_input_output_contract", "package input"),
        ("m2505_public_benchmark_pack", "m2505", source["paths"]["m2505_summary"], "public_benchmark_pack", "package input"),
        ("m2508_m2509_runtime_report", "m2508/m2509", source["paths"]["m2508_summary"], "runtime_inference_cost_report", "package input"),
        ("m2657_scenario_role_report", "m2657", source["paths"]["m2657_scenario_role_report"], "scenario_role_metric_report", "package input"),
        ("m2664_m2666_known_failure_taxonomy", "m2664/m2665/m2666", source["paths"]["m2664_summary"], "known_failure_taxonomy", "package input"),
        ("m2667_m2669_readiness_integration", "m2667/m2668/m2669", source["paths"]["m2667_summary"], "route_a_readiness_index", "readiness context"),
        ("m2684_m2686_current_sim_blocker", "m2684/m2685/m2686", source["paths"]["m2684_summary"], "route_b_current_sim_offtrack_blocker", "blocker context"),
        ("m2635_m2638_hf3_source_blocker", "m2635/m2636/m2637/m2638", source["paths"]["m2635_summary"], "hf3_source_dependency_blocker", "blocker context"),
        ("post_m2470_route_plan", "post-m2470", source["paths"]["route_plan"], "post_m2470_route_plan", "governing context"),
    ]
    rows = []
    for provenance_id, milestone, path, target, relationship in specs:
        exists = Path(path).exists()
        rows.append(
            {
                "provenance_id": provenance_id,
                "source_milestone": milestone,
                "source_path": str(path),
                "target_artifact_id": target,
                "relationship": relationship,
                "source_exists": exists,
                "status_pass_or_present": exists,
                "package_content_or_context": "package_content" if relationship == "package input" else "supporting_context",
                "claim_scope": CLAIM_SCOPE,
                "blocked_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_known_blocker_disclosure_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    offtrack_outcomes = _aggregate_count(source["m2684_outcome_aggregate"], "outcome_bucket", "off_track_noncollision_noncompletion")
    offtrack_terminations = _aggregate_count(source["m2684_termination_aggregate"], "termination_reason", "off_track")
    return [
        {
            "blocker_id": "protected_mitigation_blocker",
            "source_milestone": "m2664/m2665/m2666",
            "evidence_path": str(source["paths"]["m2667_known_failure"]),
            "blocker_status": (
                f"active: {source['m2667_summary'].get('m2664_protected_gate_blocking_row_count')} protected blocking rows "
                f"and {source['m2667_summary'].get('m2664_protected_gate_regressed_row_count')} regressed row count"
            ),
            "package_disclosure_required": True,
            "blocked_claims": "repair success; validation readiness; driver performance; checkpoint promotion",
            "resume_condition": "future protected mitigation evidence with gates preserved and explicit result audit",
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "blocker_id": "current_sim_offtrack_blocker",
            "source_milestone": "m2684/m2685/m2686",
            "evidence_path": str(source["paths"]["m2684_outcome_aggregate"]),
            "blocker_status": f"active: {offtrack_outcomes}/216 off-track outcomes and {offtrack_terminations}/216 off-track terminations",
            "package_disclosure_required": True,
            "blocked_claims": "controller ranking; paper evidence; current-sim verdict; driver performance; self-ID",
            "resume_condition": "future source-diverse outcome-relevant evidence with off-track blocker resolved or explicitly separated",
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "blocker_id": "hf3_source_dependency_blocker",
            "source_milestone": "m2635/m2636/m2637/m2638",
            "evidence_path": str(source["paths"]["m2635_summary"]),
            "blocker_status": (
                f"paused: {source['m2635_summary'].get('availability_blocker')} at "
                f"{source['m2635_summary'].get('source_root')}"
            ),
            "package_disclosure_required": True,
            "blocked_claims": "source-build readiness; adapter-probe readiness; backend availability; high-fidelity validation",
            "resume_condition": "user-supplied local source root, approved package route, or explicit dependency-acquisition manifest",
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
        {
            "blocker_id": "paper_self_id_blocker",
            "source_milestone": "m2686",
            "evidence_path": str(source["paths"]["m2686_doc"]),
            "blocker_status": "active: M2686 rejects paper, finite-window-vs-GRU, current-response, current-sim, full-driver, and self-ID claims",
            "package_disclosure_required": True,
            "blocked_claims": "paper evidence; finite-window-vs-GRU conclusion; current-response sufficiency; level3 self-ID",
            "resume_condition": "future fair L0/L1/L2/L3 source-diverse evidence with proof/generalization separation",
            "actor_visible": False,
            "claim_scope": CLAIM_SCOPE,
        },
    ]


def build_actor_action_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    contract = source["m2541_actor_contract"]
    rows = [
        actor_row("observation_shape", contract.get("observation_shape"), P0_OBSERVATION_DIM, True),
        actor_row("action_shape", contract.get("action_shape"), ACTION_DIM, True),
        actor_row("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_row("hidden_oracle_actor_input_detected", False, False, False),
        actor_row("taxonomy_labels_actor_visible", False, False, False),
        actor_row("route_labels_actor_visible", False, False, False),
        actor_row("package_labels_actor_visible", False, False, False),
        actor_row("blocker_labels_actor_visible", False, False, False),
        actor_row("verdict_labels_actor_visible", False, False, False),
    ]
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    allowed = [
        ("package_protocol_materialized", True, "M2688 protocol pack rows and gate matrix"),
        ("package_artifacts_traced", True, "artifact inventory and provenance rows"),
        ("package_limitations_disclosed", True, "known blocker disclosure rows"),
    ]
    blocked = [
        ("published_package", False, "explicit publication milestone and audit"),
        ("deployment_readiness", False, "future deployment readiness route"),
        ("driver_performance", False, "future validation and claim audit"),
        ("validation_readiness", False, "future validation-readiness route decision"),
        ("validation_result", False, "future validation execution result"),
        ("source_build_readiness_or_result", False, "future HF3 source availability and build attempt"),
        ("adapter_probe_readiness_or_result", False, "future HF3 adapter probe attempt"),
        ("backend_availability", False, "future backend probe evidence"),
        ("reset_feasibility", False, "future reset feasibility route"),
        ("rollout_feasibility", False, "future rollout feasibility route"),
        ("controller_ranking", False, "future explicit ranking gate"),
        ("winner_selection", False, "future promotion gate"),
        ("checkpoint_promotion", False, "future promotion gate"),
        ("repair_success", False, "future repair result plus protected gates"),
        ("success_rate_verdict", False, "future verdict milestone"),
        ("paper_evidence", False, "future paper evidence matrix"),
        ("finite_window_vs_gru", False, "future fair comparison result"),
        ("current_response_sufficiency", False, "future fair comparison result"),
        ("current_sim_verdict", False, "future current-sim synthesis"),
        ("high_fidelity_validation_result", False, "future high-fidelity validation"),
        ("full_ideal_driver_completion", False, "future full ideal driver gate"),
        ("level3_self_identification", False, "future self-ID proof gate"),
    ]
    return [
        {
            "claim_id": f"m2688_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2688": allowed_flag,
            "status_pass": True,
            "evidence_required_before_claim": evidence_required,
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim, allowed_flag, evidence_required in allowed + blocked
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    schema_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    provenance_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_package_rows = [row for row in artifact_rows if _bool(row["package_required"])]
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    return [
        gate_row("m2688_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2688_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2688_gate_route_a_required_artifacts_covered", "artifact_inventory", count_included(required_package_rows), 6),
        gate_row("m2688_gate_package_manifest_schema_complete", "schema", len(schema_rows), len(REQUIRED_SCHEMA_FIELDS)),
        gate_row("m2688_gate_artifact_inventory_complete", "artifact_inventory", len(artifact_rows) >= 10, True),
        gate_row("m2688_gate_provenance_map_complete", "provenance", len(provenance_rows) >= 10, True),
        gate_row(
            "m2688_gate_known_blocker_disclosures_complete",
            "known_blocker",
            {"protected_mitigation_blocker", "current_sim_offtrack_blocker", "hf3_source_dependency_blocker", "paper_self_id_blocker"}.issubset(blocker_ids),
            True,
        ),
        gate_row("m2688_gate_actor_action_contract_preserved", "actor_contract", actor_contract_preserved(actor_rows), True),
        gate_row("m2688_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_actor_input_detected(actor_rows), False),
        gate_row("m2688_gate_protected_mitigation_blocker_visible", "known_blocker", "protected_mitigation_blocker" in blocker_ids, True),
        gate_row("m2688_gate_current_sim_offtrack_blocker_visible", "known_blocker", "current_sim_offtrack_blocker" in blocker_ids, True),
        gate_row("m2688_gate_hf3_source_dependency_blocker_visible", "known_blocker", "hf3_source_dependency_blocker" in blocker_ids, True),
        gate_row("m2688_gate_claim_boundary_rows_complete", "claim_boundary", all(_bool(row["status_pass"]) for row in claim_rows), True),
        gate_row("m2688_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row("m2688_gate_no_package_publication", "claim_boundary", FALSE_CLAIM_FLAGS["package_published"], False),
        gate_row("m2688_gate_no_execution_performed", "claim_boundary", any_execution_performed(), False),
        gate_row("m2688_gate_no_training_or_ppo_performed", "claim_boundary", training_or_ppo_performed(), False),
        gate_row("m2688_gate_no_ranking_or_promotion_performed", "claim_boundary", ranking_or_promotion_performed(), False),
        gate_row("m2688_gate_no_validation_or_driver_performance_claim", "claim_boundary", validation_or_performance_claimed(), False),
        gate_row("m2688_gate_no_paper_current_sim_high_fidelity_or_self_id_claim", "claim_boundary", paper_current_sim_hf_or_self_id_claimed(), False),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    schema_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    provenance_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_package_rows = [row for row in artifact_rows if _bool(row["package_required"])]
    included_required_count = count_included(required_package_rows)
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    offtrack_outcomes = _aggregate_count(source["m2684_outcome_aggregate"], "outcome_bucket", "off_track_noncollision_noncompletion")
    offtrack_terminations = _aggregate_count(source["m2684_termination_aggregate"], "termination_reason", "off_track")
    actor_contract_ok = actor_contract_preserved(actor_rows) and not hidden_oracle_actor_input_detected(actor_rows)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and included_required_count == 6
        and len(schema_rows) == len(REQUIRED_SCHEMA_FIELDS)
        and len(provenance_rows) >= 10
        and {"protected_mitigation_blocker", "current_sim_offtrack_blocker", "hf3_source_dependency_blocker", "paper_self_id_blocker"}.issubset(blocker_ids)
        and actor_contract_ok
        and all(_bool(row["status_pass"]) for row in claim_rows)
        and gate_matrix_pass
    )
    return {
        "protocol_version": "engineering_controller_route_a_package_with_limitations_protocol_v0",
        "result_class": "engineering_controller_route_a_package_with_limitations_protocol_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "package_manifest_schema_rows": str(paths["package_manifest_schema_rows"]),
        "package_artifact_inventory_rows": str(paths["package_artifact_inventory_rows"]),
        "package_provenance_map_rows": str(paths["package_provenance_map_rows"]),
        "known_blocker_disclosure_rows": str(paths["known_blocker_disclosure_rows"]),
        "actor_action_contract_rows": str(paths["actor_action_contract_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "package_protocol_gate_matrix": str(paths["package_protocol_gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "package_published": False,
        "package_manifest_schema_row_count": len(schema_rows),
        "package_artifact_inventory_row_count": len(artifact_rows),
        "package_provenance_map_row_count": len(provenance_rows),
        "known_blocker_disclosure_row_count": len(blocker_rows),
        "actor_action_contract_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "package_protocol_gate_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "route_a_required_artifact_count": len(required_package_rows),
        "route_a_required_artifacts_covered": included_required_count,
        "route_a_artifact_coverage_complete": included_required_count == 6,
        "protected_mitigation_blocker_visible": "protected_mitigation_blocker" in blocker_ids,
        "current_sim_offtrack_blocker_visible": "current_sim_offtrack_blocker" in blocker_ids,
        "hf3_source_dependency_blocker_visible": "hf3_source_dependency_blocker" in blocker_ids,
        "paper_self_id_blocker_visible": "paper_self_id_blocker" in blocker_ids,
        "m2684_offtrack_outcome_count": offtrack_outcomes,
        "m2684_offtrack_termination_count": offtrack_terminations,
        "m2664_protected_gate_blocking_row_count": _int(source["m2667_summary"].get("m2664_protected_gate_blocking_row_count")),
        "m2664_protected_gate_regressed_row_count": _int(source["m2667_summary"].get("m2664_protected_gate_regressed_row_count")),
        "m2635_availability_blocker": source["m2635_summary"].get("availability_blocker"),
        "m2635_source_root": source["m2635_summary"].get("source_root"),
        "actor_contract_shape_72_action_3": actor_contract_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(actor_rows),
        "taxonomy_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "package_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "selected_next_action": "m2689_package_protocol_materialization_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    status = "completed" if summary["status_pass"] else "failed"
    return "\n".join(
        [
            "# M2688 Engineering Controller Route A Package With Limitations Protocol Materialization Preflight",
            "",
            f"- status: {status}",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- package manifest schema rows: `{summary['package_manifest_schema_rows']}`",
            f"- package artifact inventory rows: `{summary['package_artifact_inventory_rows']}`",
            f"- package provenance map rows: `{summary['package_provenance_map_rows']}`",
            f"- known blocker disclosure rows: `{summary['known_blocker_disclosure_rows']}`",
            f"- actor/action contract rows: `{summary['actor_action_contract_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- package protocol gate matrix: `{summary['package_protocol_gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Package Protocol Pack",
            "",
            f"- Route A required artifacts covered: {summary['route_a_required_artifacts_covered']}/{summary['route_a_required_artifact_count']}",
            f"- package manifest schema rows: {summary['package_manifest_schema_row_count']}",
            f"- artifact inventory rows: {summary['package_artifact_inventory_row_count']}",
            f"- provenance map rows: {summary['package_provenance_map_row_count']}",
            f"- known blocker disclosure rows: {summary['known_blocker_disclosure_row_count']}",
            f"- gate rows: {summary['package_protocol_gate_row_count']}",
            f"- gate matrix pass: `{str(summary['gate_matrix_pass']).lower()}`",
            "",
            "## Required Disclosures",
            "",
            f"- protected mitigation blocker visible: `{str(summary['protected_mitigation_blocker_visible']).lower()}`",
            f"- protected blocking rows: {summary['m2664_protected_gate_blocking_row_count']}",
            f"- protected regressed row count: {summary['m2664_protected_gate_regressed_row_count']}",
            f"- current-sim off-track blocker visible: `{str(summary['current_sim_offtrack_blocker_visible']).lower()}`",
            f"- M2684 off-track outcomes: {summary['m2684_offtrack_outcome_count']}/216",
            f"- M2684 off-track terminations: {summary['m2684_offtrack_termination_count']}/216",
            f"- HF3 source dependency blocker visible: `{str(summary['hf3_source_dependency_blocker_visible']).lower()}`",
            f"- HF3 availability blocker: `{summary['m2635_availability_blocker']}`",
            f"- HF3 source root: `{summary['m2635_source_root']}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- taxonomy, route, package, blocker, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2688 materializes a package protocol pack only. It does not publish a package, execute reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim driver performance, validation readiness, validation result, paper evidence, finite-window-vs-GRU, current-response sufficiency, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification.",
            "",
        ]
    )


def actor_row(contract_field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "contract_row_id": f"m2688_actor_contract_{contract_field}",
        "contract_field": contract_field,
        "observed_value": observed,
        "expected_value": expected,
        "status_pass": observed == expected,
        "actor_visible": actor_visible,
        "claim_scope": CLAIM_SCOPE,
        "blocked_interpretation": FORBIDDEN_INTERPRETATION,
    }


def gate_row(gate_id: str, gate_family: str, observed: Any, expected: Any, failure_type: str = "") -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": gate_family,
        "status_pass": observed == expected,
        "observed": observed,
        "expected": expected,
        "failure_type": "" if observed == expected else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def count_included(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row["package_inclusion_status"] == "included_with_limitations")


def actor_contract_preserved(actor_rows: list[dict[str, Any]]) -> bool:
    return all(_bool(row["status_pass"]) for row in actor_rows)


def hidden_oracle_actor_input_detected(actor_rows: list[dict[str, Any]]) -> bool:
    for row in actor_rows:
        if row["contract_field"] == "hidden_oracle_actor_input_detected":
            return _bool(row["observed_value"])
    return True


def any_execution_performed() -> bool:
    keys = (
        "external_high_fidelity_simulation_included",
        "high_fidelity_simulation_run",
        "source_build_run",
        "adapter_probe_run",
        "backend_started",
        "environment_reset_run",
        "environment_step_run",
        "policy_action_run",
        "policy_rollout_run",
        "replay_run",
        "measured_validation_run",
    )
    return any(FALSE_CLAIM_FLAGS[key] for key in keys)


def training_or_ppo_performed() -> bool:
    return FALSE_CLAIM_FLAGS["training_run"] or FALSE_CLAIM_FLAGS["ppo_run"]


def ranking_or_promotion_performed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["ranking_run"]
        or FALSE_CLAIM_FLAGS["winner_selected"]
        or FALSE_CLAIM_FLAGS["checkpoint_promoted"]
        or FALSE_CLAIM_FLAGS["success_rate_computed"]
        or FALSE_CLAIM_FLAGS["success_rate_verdict_field_emitted"]
        or FALSE_CLAIM_FLAGS["controller_family_verdict_computed"]
    )


def validation_or_performance_claimed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["validation_readiness_claim_made"]
        or FALSE_CLAIM_FLAGS["validation_result_claim_made"]
        or FALSE_CLAIM_FLAGS["driver_performance_claim_made"]
    )


def paper_current_sim_hf_or_self_id_claimed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["paper_claim_made"]
        or FALSE_CLAIM_FLAGS["finite_window_vs_gru_claim_made"]
        or FALSE_CLAIM_FLAGS["current_response_sufficiency_claim_made"]
        or FALSE_CLAIM_FLAGS["current_sim_verdict_claim_made"]
        or FALSE_CLAIM_FLAGS["high_fidelity_validation_claim_made"]
        or FALSE_CLAIM_FLAGS["level3_self_id_claim_made"]
        or FALSE_CLAIM_FLAGS["full_ideal_driver_gate_passed"]
    )


def _aggregate_count(rows: list[dict[str, str]], key: str, value: str) -> int:
    for row in rows:
        if row.get(key) == value:
            return _int(row.get("episode_count"))
    return 0


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "pass", "passed"}


def _int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=str(DEFAULT_DOC_PATH))
    parser.add_argument("--follow-up-manifest", default=str(DEFAULT_FOLLOW_UP_MANIFEST))
    args = parser.parse_args(argv)
    summary = materialize_package_with_limitations_protocol(
        Path(args.output_dir),
        doc_path=Path(args.doc_path),
        follow_up_manifest=Path(args.follow_up_manifest),
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
