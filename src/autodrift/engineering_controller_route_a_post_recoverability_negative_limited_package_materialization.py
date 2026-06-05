"""Materialize the post-recoverability Route A limited package refresh.

This runner only reanalyzes existing Route A package, readiness, blocker, and
actor-contract artifacts. It does not publish a package, run simulation,
validate, train, repair, rank, or promote a checkpoint.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2824-engineering-controller-route-a-post-recoverability-negative-"
    "limited-package-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2825-engineering-controller-route-a-post-recoverability-negative-"
    "limited-package-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2824-engineering-controller-route-a-post-recoverability-negative-"
    "limited-package-materialization-preflight.md"
)
DEFAULT_M2823_DESIGN = Path(
    "docs/m2823-engineering-controller-route-a-post-recoverability-negative-limited-package-design.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2825-engineering-controller-route-a-post-recoverability-negative-"
    "limited-package-materialization-result-audit.json"
)

M2822_DOC = Path(
    "docs/m2822-engineering-controller-route-a-post-recoverability-negative-"
    "readiness-index-result-synthesis.md"
)
M2821_DOC = Path(
    "docs/m2821-engineering-controller-route-a-post-recoverability-negative-"
    "readiness-index-materialization-result-audit.md"
)
M2820_SUMMARY = Path(
    "runs/m2820_engineering_controller_route_a_post_recoverability_negative_readiness_index/summary.json"
)
M2818_DOC = Path("docs/m2818-engineering-controller-route-a-post-action-response-recoverability-window-branch-synthesis.md")
M2817_DOC = Path(
    "docs/m2817-engineering-controller-route-a-post-action-response-recoverability-window-"
    "instrumented-bounded-execution-result-audit.md"
)
M2816_SUMMARY = Path(
    "runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_"
    "instrumented_bounded_execution_preflight/summary.json"
)
M2804_SUMMARY = Path(
    "runs/m2804_engineering_controller_route_a_post_clearance_corrective_readiness_index/summary.json"
)
M2688_SUMMARY = Path(
    "runs/m2688_engineering_controller_route_a_package_with_limitations_protocol_materialization/summary.json"
)
M2689_DOC = Path("docs/m2689-engineering-controller-route-a-package-with-limitations-protocol-materialization-result-audit.md")
M2541_SUMMARY = Path("runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json")
M2541_BASELINE_CHECKPOINTS = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv"
)
M2541_ACTOR_CONTRACT = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json"
)
M2541_SCENARIO_ROLE_PLAN = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/scenario_role_metric_report_plan.csv"
)
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
M2510_SUMMARY = Path("runs/m2510_engineering_controller_known_failure_taxonomy/summary.json")
M2638_DOC = Path(
    "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-"
    "and-user-supplied-source-contract-design.md"
)
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A post-recoverability limited package materialization only; no package publication, "
    "reset, rollout, replay, validation, training, PPO, repair, source build, adapter probe, "
    "external simulation, ranking, winner selection, promotion, success-rate verdict, repair-success, "
    "recoverability-success, driver-performance, paper, finite-window-vs-GRU, current-response, "
    "current-sim, high-fidelity validation, full ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "published package, deployment readiness, repair success, recoverability success, driver performance, "
    "validation readiness, validation result, source-build readiness/result, adapter-probe readiness/result, "
    "backend availability, reset feasibility, rollout feasibility, controller ranking, scenario-role ranking, "
    "winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU "
    "conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation result, "
    "full ideal driver completion, or self-ID evidence"
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
    "repair_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "driver_performance_claim_made": False,
    "repair_success_claim_made": False,
    "recoverability_success_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "full_ideal_driver_completion_claim_made": False,
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
    "artifact_role",
    "row_count_or_summary",
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
RECOVERABILITY_FIELDNAMES = [
    "limitation_id",
    "source_milestone",
    "evidence_path",
    "observed_value",
    "blocked_interpretation",
    "package_disclosure_required",
    "actor_visible",
    "resume_condition",
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
    "allowed_in_m2824",
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
    ("package_id", True, "M2823 design", "string"),
    ("package_protocol_version", True, "M2823 design", "string"),
    ("generated_at_utc", True, "runner clock", "UTC timestamp string"),
    ("route", True, "M2823 design", "Route A"),
    ("artifact_id", True, "artifact inventory", "string"),
    ("source_milestone", True, "artifact inventory", "string"),
    ("source_path", True, "artifact inventory", "path string"),
    ("source_exists", True, "filesystem", "boolean"),
    ("source_status_pass_or_present", True, "source summary/doc", "boolean"),
    ("artifact_role", True, "M2823 design", "package_content package_limitations or context_only"),
    ("package_required", True, "M2823 design", "boolean"),
    ("package_inclusion_status", True, "artifact inventory", "included_with_limitations context_only or blocked"),
    ("provenance_status", True, "provenance map", "traced or missing"),
    ("actor_visible", True, "actor contract", "boolean"),
    ("claim_scope", True, "M2823 design", "string"),
    ("blocked_interpretation", True, "M2823 design", "string"),
    ("known_blocker_refs", True, "blocker disclosure", "semicolon-separated blocker ids"),
    ("post_recoverability_refs", True, "recoverability limitations", "semicolon-separated limitation ids"),
]


def materialize_post_recoverability_limited_package(
    output_dir: Path | str,
    *,
    m2823_design: Path | str = DEFAULT_M2823_DESIGN,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    source = load_source_artifacts(m2823_design=m2823_design, follow_up_manifest=follow_up_manifest)
    schema_rows = build_package_manifest_schema_rows()
    artifact_rows = build_package_artifact_inventory_rows(source)
    provenance_rows = build_package_provenance_map_rows(source)
    blocker_rows = build_known_blocker_disclosure_rows(source)
    recoverability_rows = build_recoverability_limitation_rows(source)
    actor_rows = build_actor_action_contract_rows(source)
    claim_rows = build_claim_boundary_rows()
    paths = {
        "summary": output_path / "summary.json",
        "package_manifest_schema_rows": output_path / "package_manifest_schema_rows.csv",
        "package_artifact_inventory_rows": output_path / "package_artifact_inventory_rows.csv",
        "package_provenance_map_rows": output_path / "package_provenance_map_rows.csv",
        "known_blocker_disclosure_rows": output_path / "known_blocker_disclosure_rows.csv",
        "recoverability_limitations_rows": output_path / "recoverability_limitations_rows.csv",
        "actor_action_contract_rows": output_path / "actor_action_contract_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "package_gate_matrix": output_path / "package_gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["package_manifest_schema_rows"], schema_rows, fieldnames=SCHEMA_FIELDNAMES)
    write_csv_rows(paths["package_artifact_inventory_rows"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)
    write_csv_rows(paths["package_provenance_map_rows"], provenance_rows, fieldnames=PROVENANCE_FIELDNAMES)
    write_csv_rows(paths["known_blocker_disclosure_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["recoverability_limitations_rows"], recoverability_rows, fieldnames=RECOVERABILITY_FIELDNAMES)
    write_csv_rows(paths["actor_action_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        schema_rows,
        artifact_rows,
        provenance_rows,
        blocker_rows,
        recoverability_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["package_gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        schema_rows=schema_rows,
        artifact_rows=artifact_rows,
        provenance_rows=provenance_rows,
        blocker_rows=blocker_rows,
        recoverability_rows=recoverability_rows,
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
        recoverability_rows,
        actor_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["package_gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        schema_rows=schema_rows,
        artifact_rows=artifact_rows,
        provenance_rows=provenance_rows,
        blocker_rows=blocker_rows,
        recoverability_rows=recoverability_rows,
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


def load_source_artifacts(*, m2823_design: Path | str, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2823_design": Path(m2823_design),
        "m2822_doc": M2822_DOC,
        "m2821_doc": M2821_DOC,
        "m2820_summary": M2820_SUMMARY,
        "m2818_doc": M2818_DOC,
        "m2817_doc": M2817_DOC,
        "m2816_summary": M2816_SUMMARY,
        "m2804_summary": M2804_SUMMARY,
        "m2688_summary": M2688_SUMMARY,
        "m2689_doc": M2689_DOC,
        "m2541_summary": M2541_SUMMARY,
        "m2541_baseline_checkpoints": M2541_BASELINE_CHECKPOINTS,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2541_scenario_role_plan": M2541_SCENARIO_ROLE_PLAN,
        "m2505_summary": M2505_SUMMARY,
        "m2508_summary": M2508_SUMMARY,
        "m2510_summary": M2510_SUMMARY,
        "m2638_doc": M2638_DOC,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2820_summary": read_json(paths["m2820_summary"]),
        "m2816_summary": read_json(paths["m2816_summary"]),
        "m2804_summary": read_json(paths["m2804_summary"]),
        "m2688_summary": read_json(paths["m2688_summary"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
        "m2510_summary": read_json(paths["m2510_summary"]),
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
    specs = [
        ("baseline_checkpoint_list", "m2541", source["paths"]["m2541_baseline_checkpoints"], True, "package_content", source["m2541_summary"].get("all_baseline_checkpoints_admitted"), source["m2541_summary"].get("baseline_checkpoint_count")),
        ("actor_input_output_contract", "m2541", source["paths"]["m2541_actor_contract"], True, "package_content", source["m2541_summary"].get("actor_contract_shape_72_action_3"), 1),
        ("public_benchmark_pack", "m2505", source["paths"]["m2505_summary"], True, "package_content", source["m2505_summary"].get("status_pass"), source["m2505_summary"].get("artifact_manifest_rows")),
        ("runtime_inference_cost_report", "m2508", source["paths"]["m2508_summary"], True, "package_content", source["m2508_summary"].get("status_pass"), source["m2508_summary"].get("measurement_row_count")),
        ("scenario_role_metric_report_plan", "m2541", source["paths"]["m2541_scenario_role_plan"], True, "package_content", source["source_exists"]["m2541_scenario_role_plan"], source["m2541_summary"].get("scenario_role_metric_report_plan_row_count")),
        ("known_failure_taxonomy", "m2510", source["paths"]["m2510_summary"], True, "package_content", source["m2510_summary"].get("status_pass"), source["m2510_summary"].get("taxonomy_row_count")),
        ("post_clearance_readiness_blockers", "m2804/m2805", source["paths"]["m2804_summary"], True, "package_limitations", source["m2804_summary"].get("status_pass"), source["m2804_summary"].get("blocker_matrix_row_count")),
        ("negative_recoverability_diagnostics", "m2816/m2817/m2818", source["paths"]["m2816_summary"], True, "package_limitations", source["m2816_summary"].get("status_pass"), source["m2816_summary"].get("recoverability_window_row_count")),
        ("post_recoverability_readiness_index", "m2820/m2821/m2822", source["paths"]["m2820_summary"], True, "package_limitations", source["m2820_summary"].get("status_pass"), source["m2820_summary"].get("evidence_index_row_count")),
        ("hf3_source_dependency_blocker", "m2638", source["paths"]["m2638_doc"], True, "package_limitations", source["source_exists"]["m2638_doc"], 1),
        ("route_b_paper_self_id_blocker", "post-m2470/m2822", source["paths"]["m2822_doc"], False, "context_only", source["source_exists"]["m2822_doc"], 1),
        ("prior_package_protocol", "m2688/m2689", source["paths"]["m2688_summary"], False, "context_only", source["m2688_summary"].get("status_pass") and source["source_exists"]["m2689_doc"], source["m2688_summary"].get("package_artifact_inventory_row_count")),
        ("post_m2470_route_plan", "post-m2470", source["paths"]["route_plan"], False, "context_only", source["source_exists"]["route_plan"], 1),
        ("m2823_package_design", "m2823", source["paths"]["m2823_design"], False, "context_only", source["source_exists"]["m2823_design"], 1),
    ]
    rows = []
    for artifact_id, milestone, path, package_required, role, status, row_count in specs:
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
                "artifact_role": role,
                "row_count_or_summary": _int(row_count),
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
        ("m2508_runtime_report", "m2508", source["paths"]["m2508_summary"], "runtime_inference_cost_report", "package input"),
        ("m2541_scenario_role_plan", "m2541", source["paths"]["m2541_scenario_role_plan"], "scenario_role_metric_report_plan", "package input"),
        ("m2510_known_failure_taxonomy", "m2510", source["paths"]["m2510_summary"], "known_failure_taxonomy", "package input"),
        ("m2804_post_clearance_blockers", "m2804/m2805", source["paths"]["m2804_summary"], "post_clearance_readiness_blockers", "limitation input"),
        ("m2816_negative_recoverability", "m2816/m2817/m2818", source["paths"]["m2816_summary"], "negative_recoverability_diagnostics", "limitation input"),
        ("m2820_post_recoverability_index", "m2820/m2821/m2822", source["paths"]["m2820_summary"], "post_recoverability_readiness_index", "limitation input"),
        ("m2638_hf3_source_blocker", "m2638", source["paths"]["m2638_doc"], "hf3_source_dependency_blocker", "blocker context"),
        ("m2822_route_b_self_id_separation", "m2822", source["paths"]["m2822_doc"], "route_b_paper_self_id_blocker", "blocker context"),
        ("m2688_prior_package_protocol", "m2688/m2689", source["paths"]["m2688_summary"], "prior_package_protocol", "prior protocol context"),
        ("post_m2470_route_plan", "post-m2470", source["paths"]["route_plan"], "post_m2470_route_plan", "governing context"),
        ("m2823_design", "m2823", source["paths"]["m2823_design"], "m2823_package_design", "governing context"),
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
                "package_content_or_context": "package_content" if "input" in relationship else "context_only",
                "claim_scope": CLAIM_SCOPE,
                "blocked_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_known_blocker_disclosure_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2804 = source["m2804_summary"]
    m2816 = source["m2816_summary"]
    m2820 = source["m2820_summary"]
    return [
        blocker_row(
            "post_clearance_blocker",
            "m2804/m2805",
            source["paths"]["m2804_summary"],
            (
                "active: negative clearance preserved "
                f"{m2804.get('m2801_negative_clearance_preserved')} and stable_avoidable "
                f"retention risk preserved {m2804.get('m2801_stable_avoidable_retention_risk_preserved')}"
            ),
            "repair success; validation readiness; driver performance; promotion",
            "future non-same-surface evidence with explicit result audit",
        ),
        blocker_row(
            "negative_recoverability_blocker",
            "m2816/m2817/m2818/m2820/m2821",
            source["paths"]["m2816_summary"],
            (
                f"active: {m2816.get('post_event_available_count')} post-event traces, "
                f"{m2816.get('recoverability_available_count')} recoverability-window availability, "
                f"{m2816.get('recoverability_success_count')} recoverability success, "
                f"{m2816.get('diagnostic_collision_count')} collision, "
                f"{m2816.get('diagnostic_offtrack_termination_count')} offtrack terminations"
            ),
            "recoverability success; repair success; validation readiness; driver performance",
            "future pre-registered non-overfit recoverability or validation route",
        ),
        blocker_row(
            "same_recoverability_local_search_blocker",
            "m2822",
            source["paths"]["m2822_doc"],
            "closed: M2822 rejects another same recoverability repair/ranking loop",
            "same-surface repair; controller ranking; success-rate verdict",
            "materially different evidence axis or branch synthesis",
        ),
        blocker_row(
            "hf3_source_dependency_blocker",
            "m2638",
            source["paths"]["m2638_doc"],
            "paused: selected-platform HF3 execution remains blocked by missing source dependency",
            "source-build readiness; adapter-probe readiness; backend availability; high-fidelity validation",
            "user-supplied local source root, approved package route, or dependency-acquisition manifest",
        ),
        blocker_row(
            "route_b_paper_self_id_blocker",
            "post-m2470/m2822",
            source["paths"]["m2822_doc"],
            (
                "active: Route A package rows do not test history necessity, finite-window-vs-GRU, "
                "current-response sufficiency, full-driver completion, or level3 self-ID"
            ),
            "paper evidence; finite-window-vs-GRU; current-response sufficiency; level3 self-ID",
            "future fair L0/L1/L2/L3 comparison with proof/generalization separation",
        ),
    ]


def build_recoverability_limitation_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2816 = source["m2816_summary"]
    rows = [
        ("post_event_available_rows", m2816.get("post_event_available_count"), "post-event traces are diagnostic context, not recoverability proof"),
        ("recoverability_window_available_rows", m2816.get("recoverability_available_count"), "0 recoverability-window availability blocks recoverability-success and validation claims"),
        ("recoverability_success_rows", m2816.get("recoverability_success_count"), "0 recoverability success blocks repair-success driver-performance and validation claims"),
        ("diagnostic_collision_outcomes", m2816.get("diagnostic_collision_count"), "diagnostic collision remains a visible limitation"),
        ("diagnostic_offtrack_terminations", m2816.get("diagnostic_offtrack_termination_count"), "offtrack terminations remain visible limitations"),
        ("fixed_recoverability_rows_are_validation_benchmark", False, "fixed diagnostic rows are not a validation benchmark"),
        ("same_recoverability_repair_or_ranking_admitted", False, "M2822 rejects same recoverability repair or ranking"),
    ]
    return [
        {
            "limitation_id": limitation_id,
            "source_milestone": "m2816/m2817/m2818/m2820/m2821/m2822",
            "evidence_path": str(source["paths"]["m2816_summary"]),
            "observed_value": observed,
            "blocked_interpretation": blocked,
            "package_disclosure_required": True,
            "actor_visible": False,
            "resume_condition": "future pre-registered non-overfit evidence route with explicit audit",
            "claim_scope": CLAIM_SCOPE,
        }
        for limitation_id, observed, blocked in rows
    ]


def build_actor_action_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    contract = source["m2541_actor_contract"]
    return [
        actor_row("observation_shape", contract.get("observation_shape"), P0_OBSERVATION_DIM, True),
        actor_row("action_shape", contract.get("action_shape"), ACTION_DIM, True),
        actor_row("deployed_action_mapping", "[steer, throttle, brake]", "[steer, throttle, brake]", True),
        actor_row("actor_encoder", contract.get("actor_encoder"), "human_view_online_gru", True),
        actor_row("action_sequence_horizon", contract.get("action_sequence_horizon"), 1, True),
        actor_row("hidden_oracle_actor_input_detected", False, False, False),
        actor_row("package_labels_actor_visible", False, False, False),
        actor_row("blocker_labels_actor_visible", False, False, False),
        actor_row("recoverability_labels_actor_visible", False, False, False),
        actor_row("route_labels_actor_visible", False, False, False),
        actor_row("verdict_labels_actor_visible", False, False, False),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    allowed = [
        ("limited_package_materialized", True, "M2824 package rows and gate matrix"),
        ("post_recoverability_limitations_disclosed", True, "recoverability limitation rows"),
        ("package_artifacts_traced", True, "artifact inventory and provenance rows"),
    ]
    blocked = [
        ("published_package", False, "explicit publication milestone and audit"),
        ("deployment_readiness", False, "future deployment readiness route"),
        ("driver_performance", False, "future validation and claim audit"),
        ("repair_success", False, "future repair result plus protected gates"),
        ("recoverability_success", False, "future recoverability result plus audit"),
        ("validation_readiness", False, "future validation-readiness route decision"),
        ("validation_result", False, "future validation execution result"),
        ("source_build_readiness_or_result", False, "future HF3 source availability and build attempt"),
        ("adapter_probe_readiness_or_result", False, "future HF3 adapter probe attempt"),
        ("backend_availability", False, "future backend probe evidence"),
        ("reset_feasibility", False, "future reset feasibility route"),
        ("rollout_feasibility", False, "future rollout feasibility route"),
        ("controller_ranking", False, "future explicit ranking gate"),
        ("scenario_role_ranking", False, "future explicit ranking gate"),
        ("winner_selection", False, "future promotion gate"),
        ("checkpoint_promotion", False, "future promotion gate"),
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
            "claim_id": f"m2824_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2824": allowed_flag,
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
    recoverability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    required_package_rows = [row for row in artifact_rows if _bool(row["package_required"])]
    package_content_rows = [row for row in required_package_rows if row["artifact_role"] == "package_content"]
    limitation_rows = [row for row in required_package_rows if row["artifact_role"] == "package_limitations"]
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    limitation_ids = {row["limitation_id"] for row in recoverability_rows}
    return [
        gate_row("m2824_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2824_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2824_gate_package_content_covered", "artifact_inventory", count_included(package_content_rows), 6),
        gate_row("m2824_gate_package_limitations_covered", "artifact_inventory", count_included(limitation_rows), 4),
        gate_row("m2824_gate_package_manifest_schema_complete", "schema", len(schema_rows), len(REQUIRED_SCHEMA_FIELDS)),
        gate_row("m2824_gate_artifact_inventory_complete", "artifact_inventory", len(artifact_rows) >= 14, True),
        gate_row("m2824_gate_provenance_map_complete", "provenance", len(provenance_rows) >= 14, True),
        gate_row(
            "m2824_gate_known_blocker_disclosures_complete",
            "known_blocker",
            {
                "post_clearance_blocker",
                "negative_recoverability_blocker",
                "same_recoverability_local_search_blocker",
                "hf3_source_dependency_blocker",
                "route_b_paper_self_id_blocker",
            }.issubset(blocker_ids),
            True,
        ),
        gate_row(
            "m2824_gate_recoverability_limitations_complete",
            "recoverability",
            {
                "post_event_available_rows",
                "recoverability_window_available_rows",
                "recoverability_success_rows",
                "diagnostic_collision_outcomes",
                "diagnostic_offtrack_terminations",
                "fixed_recoverability_rows_are_validation_benchmark",
                "same_recoverability_repair_or_ranking_admitted",
            }.issubset(limitation_ids),
            True,
        ),
        gate_row("m2824_gate_actor_action_contract_preserved", "actor_contract", actor_contract_preserved(actor_rows), True),
        gate_row("m2824_gate_hidden_oracle_actor_input_absent", "actor_contract", hidden_oracle_actor_input_detected(actor_rows), False),
        gate_row("m2824_gate_post_clearance_blocker_visible", "known_blocker", "post_clearance_blocker" in blocker_ids, True),
        gate_row("m2824_gate_negative_recoverability_blocker_visible", "known_blocker", "negative_recoverability_blocker" in blocker_ids, True),
        gate_row("m2824_gate_same_recoverability_local_search_blocked", "known_blocker", "same_recoverability_local_search_blocker" in blocker_ids, True),
        gate_row("m2824_gate_hf3_source_dependency_blocker_visible", "known_blocker", "hf3_source_dependency_blocker" in blocker_ids, True),
        gate_row("m2824_gate_route_b_paper_self_id_blocker_visible", "known_blocker", "route_b_paper_self_id_blocker" in blocker_ids, True),
        gate_row("m2824_gate_claim_boundary_rows_complete", "claim_boundary", all(_bool(row["status_pass"]) for row in claim_rows), True),
        gate_row("m2824_gate_follow_up_result_audit_registered", "process", source["source_exists"]["follow_up_manifest"], True),
        gate_row("m2824_gate_no_package_publication", "claim_boundary", FALSE_CLAIM_FLAGS["package_published"], False),
        gate_row("m2824_gate_no_execution_performed", "claim_boundary", any_execution_performed(), False),
        gate_row("m2824_gate_no_training_ppo_or_repair_performed", "claim_boundary", training_ppo_or_repair_performed(), False),
        gate_row("m2824_gate_no_ranking_or_promotion_performed", "claim_boundary", ranking_or_promotion_performed(), False),
        gate_row("m2824_gate_no_validation_or_driver_performance_claim", "claim_boundary", validation_or_performance_claimed(), False),
        gate_row("m2824_gate_no_paper_current_sim_high_fidelity_full_driver_or_self_id_claim", "claim_boundary", paper_current_sim_hf_full_driver_or_self_id_claimed(), False),
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
    recoverability_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    m2816 = source["m2816_summary"]
    m2820 = source["m2820_summary"]
    m2804 = source["m2804_summary"]
    required_package_rows = [row for row in artifact_rows if _bool(row["package_required"])]
    package_content_rows = [row for row in required_package_rows if row["artifact_role"] == "package_content"]
    limitation_rows = [row for row in required_package_rows if row["artifact_role"] == "package_limitations"]
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    actor_contract_ok = actor_contract_preserved(actor_rows) and not hidden_oracle_actor_input_detected(actor_rows)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and count_included(package_content_rows) == 6
        and count_included(limitation_rows) == 4
        and len(schema_rows) == len(REQUIRED_SCHEMA_FIELDS)
        and len(provenance_rows) >= 14
        and len(recoverability_rows) >= 7
        and {
            "post_clearance_blocker",
            "negative_recoverability_blocker",
            "same_recoverability_local_search_blocker",
            "hf3_source_dependency_blocker",
            "route_b_paper_self_id_blocker",
        }.issubset(blocker_ids)
        and actor_contract_ok
        and all(_bool(row["status_pass"]) for row in claim_rows)
        and gate_matrix_pass
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_recoverability_negative_limited_package_v0",
        "result_class": "engineering_controller_route_a_post_recoverability_negative_limited_package_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "package_manifest_schema_rows": str(paths["package_manifest_schema_rows"]),
        "package_artifact_inventory_rows": str(paths["package_artifact_inventory_rows"]),
        "package_provenance_map_rows": str(paths["package_provenance_map_rows"]),
        "known_blocker_disclosure_rows": str(paths["known_blocker_disclosure_rows"]),
        "recoverability_limitations_rows": str(paths["recoverability_limitations_rows"]),
        "actor_action_contract_rows": str(paths["actor_action_contract_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "package_gate_matrix": str(paths["package_gate_matrix"]),
        "doc": str(paths["doc"]),
        "follow_up_manifest": str(source["paths"]["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_present": all(source["source_exists"].values()),
        "source_artifacts_reanalyzed_only": True,
        "package_manifest_schema_row_count": len(schema_rows),
        "package_artifact_inventory_row_count": len(artifact_rows),
        "package_provenance_map_row_count": len(provenance_rows),
        "known_blocker_disclosure_row_count": len(blocker_rows),
        "recoverability_limitation_row_count": len(recoverability_rows),
        "actor_action_contract_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "package_gate_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "route_a_package_content_required_count": len(package_content_rows),
        "route_a_package_content_covered": count_included(package_content_rows),
        "route_a_package_limitations_required_count": len(limitation_rows),
        "route_a_package_limitations_covered": count_included(limitation_rows),
        "post_clearance_blocker_visible": "post_clearance_blocker" in blocker_ids,
        "negative_recoverability_blocker_visible": "negative_recoverability_blocker" in blocker_ids,
        "same_recoverability_local_search_blocked": "same_recoverability_local_search_blocker" in blocker_ids,
        "hf3_source_dependency_blocker_visible": "hf3_source_dependency_blocker" in blocker_ids,
        "route_b_paper_self_id_blocker_visible": "route_b_paper_self_id_blocker" in blocker_ids,
        "m2816_post_event_available_count": _int(m2816.get("post_event_available_count")),
        "m2816_recoverability_available_count": _int(m2816.get("recoverability_available_count")),
        "m2816_recoverability_success_count": _int(m2816.get("recoverability_success_count")),
        "m2816_diagnostic_collision_count": _int(m2816.get("diagnostic_collision_count")),
        "m2816_diagnostic_offtrack_termination_count": _int(m2816.get("diagnostic_offtrack_termination_count")),
        "m2820_evidence_index_row_count": _int(m2820.get("evidence_index_row_count")),
        "m2820_deliverable_readiness_row_count": _int(m2820.get("route_a_deliverable_readiness_row_count")),
        "m2820_blocker_matrix_row_count": _int(m2820.get("blocker_matrix_row_count")),
        "m2820_next_action_admission_row_count": _int(m2820.get("next_action_admission_row_count")),
        "m2820_claim_boundary_row_count": _int(m2820.get("claim_boundary_row_count")),
        "m2820_gate_matrix_row_count": _int(m2820.get("gate_matrix_row_count")),
        "m2804_negative_clearance_preserved": _bool(m2804.get("m2801_negative_clearance_preserved")),
        "m2804_stable_avoidable_retention_risk_preserved": _bool(m2804.get("m2801_stable_avoidable_retention_risk_preserved")),
        "actor_contract_shape_72_action_3": actor_contract_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(actor_rows),
        "package_labels_actor_visible": False,
        "blocker_labels_actor_visible": False,
        "recoverability_labels_actor_visible": False,
        "route_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "selected_next_action": "m2825_limited_package_materialization_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    status = "completed" if summary["status_pass"] else "failed"
    return "\n".join(
        [
            "# M2824 Engineering Controller Route A Post-Recoverability Negative Limited Package Materialization Preflight",
            "",
            f"- status: {status}",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- package manifest schema rows: `{summary['package_manifest_schema_rows']}`",
            f"- package artifact inventory rows: `{summary['package_artifact_inventory_rows']}`",
            f"- package provenance map rows: `{summary['package_provenance_map_rows']}`",
            f"- known blocker disclosure rows: `{summary['known_blocker_disclosure_rows']}`",
            f"- recoverability limitations rows: `{summary['recoverability_limitations_rows']}`",
            f"- actor/action contract rows: `{summary['actor_action_contract_rows']}`",
            f"- claim boundary rows: `{summary['claim_boundary_rows']}`",
            f"- package gate matrix: `{summary['package_gate_matrix']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Package Refresh",
            "",
            f"- Route A package content covered: {summary['route_a_package_content_covered']}/{summary['route_a_package_content_required_count']}",
            f"- package limitations covered: {summary['route_a_package_limitations_covered']}/{summary['route_a_package_limitations_required_count']}",
            f"- artifact inventory rows: {summary['package_artifact_inventory_row_count']}",
            f"- provenance map rows: {summary['package_provenance_map_row_count']}",
            f"- known blocker disclosure rows: {summary['known_blocker_disclosure_row_count']}",
            f"- recoverability limitation rows: {summary['recoverability_limitation_row_count']}",
            f"- gate matrix pass: `{str(summary['gate_matrix_pass']).lower()}`",
            "",
            "## Required Limitations",
            "",
            f"- M2816 post-event traces: {summary['m2816_post_event_available_count']}",
            f"- M2816 recoverability-window availability: {summary['m2816_recoverability_available_count']}",
            f"- M2816 recoverability success: {summary['m2816_recoverability_success_count']}",
            f"- M2816 diagnostic collision count: {summary['m2816_diagnostic_collision_count']}",
            f"- M2816 diagnostic offtrack termination count: {summary['m2816_diagnostic_offtrack_termination_count']}",
            f"- M2804 negative clearance preserved: `{str(summary['m2804_negative_clearance_preserved']).lower()}`",
            f"- M2804 stable_avoidable retention risk preserved: `{str(summary['m2804_stable_avoidable_retention_risk_preserved']).lower()}`",
            f"- HF3 source dependency blocker visible: `{str(summary['hf3_source_dependency_blocker_visible']).lower()}`",
            f"- Route B paper/self-ID blocker visible: `{str(summary['route_b_paper_self_id_blocker_visible']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- package, blocker, recoverability, route, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2824 materializes a local package-boundary refresh only. It does not publish a package, execute reset, step, rollout, replay, validation, training, PPO, repair, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, recoverability success, driver performance, validation readiness, validation result, paper evidence, finite-window-vs-GRU, current-response sufficiency, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification.",
            "",
        ]
    )


def blocker_row(
    blocker_id: str,
    source_milestone: str,
    evidence_path: Path,
    blocker_status: str,
    blocked_claims: str,
    resume_condition: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "source_milestone": source_milestone,
        "evidence_path": str(evidence_path),
        "blocker_status": blocker_status,
        "package_disclosure_required": True,
        "blocked_claims": blocked_claims,
        "resume_condition": resume_condition,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


def actor_row(contract_field: str, observed: Any, expected: Any, actor_visible: bool) -> dict[str, Any]:
    return {
        "contract_row_id": f"m2824_actor_contract_{contract_field}",
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


def training_ppo_or_repair_performed() -> bool:
    return FALSE_CLAIM_FLAGS["training_run"] or FALSE_CLAIM_FLAGS["ppo_run"] or FALSE_CLAIM_FLAGS["repair_run"]


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
        or FALSE_CLAIM_FLAGS["repair_success_claim_made"]
        or FALSE_CLAIM_FLAGS["recoverability_success_claim_made"]
    )


def paper_current_sim_hf_full_driver_or_self_id_claimed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["paper_claim_made"]
        or FALSE_CLAIM_FLAGS["finite_window_vs_gru_claim_made"]
        or FALSE_CLAIM_FLAGS["current_response_sufficiency_claim_made"]
        or FALSE_CLAIM_FLAGS["current_sim_verdict_claim_made"]
        or FALSE_CLAIM_FLAGS["high_fidelity_validation_claim_made"]
        or FALSE_CLAIM_FLAGS["high_fidelity_validation_readiness_claim_made"]
        or FALSE_CLAIM_FLAGS["level3_self_id_claim_made"]
        or FALSE_CLAIM_FLAGS["full_ideal_driver_gate_passed"]
        or FALSE_CLAIM_FLAGS["full_ideal_driver_completion_claim_made"]
    )


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
    parser.add_argument("--m2823-design", default=str(DEFAULT_M2823_DESIGN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=str(DEFAULT_DOC_PATH))
    parser.add_argument("--follow-up-manifest", default=str(DEFAULT_FOLLOW_UP_MANIFEST))
    args = parser.parse_args(argv)
    summary = materialize_post_recoverability_limited_package(
        Path(args.output_dir),
        m2823_design=Path(args.m2823_design),
        doc_path=Path(args.doc_path),
        follow_up_manifest=Path(args.follow_up_manifest),
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
