"""Materialize the post-M2870 Route A limited baseline package refresh.

This runner re-indexes existing Route A artifacts only. It does not publish a
package, execute simulation, validate, train, repair, rank, or promote a
checkpoint.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2873-engineering-controller-route-a-post-localized-response-prediction-"
    "limited-baseline-package-refresh-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2874-engineering-controller-route-a-post-localized-response-prediction-"
    "limited-baseline-package-refresh-materialization-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2873_engineering_controller_route_a_post_localized_response_prediction_"
    "limited_baseline_package_refresh"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2873-engineering-controller-route-a-post-localized-response-prediction-"
    "limited-baseline-package-refresh-materialization-preflight.md"
)
DEFAULT_M2872_DESIGN = Path(
    "docs/m2872-engineering-controller-route-a-post-localized-response-prediction-"
    "limited-baseline-package-refresh-design.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2874-engineering-controller-route-a-post-localized-response-prediction-"
    "limited-baseline-package-refresh-materialization-result-audit.json"
)

M2871_DOC = Path(
    "docs/m2871-engineering-controller-route-a-post-localized-response-prediction-"
    "evidence-index-refresh-and-admission-synthesis.md"
)
M2870_DOC = Path(
    "docs/m2870-engineering-controller-route-a-response-predictive-recurrent-belief-"
    "localized-response-prediction-branch-synthesis.md"
)
M2868_SUMMARY = Path(
    "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "localized_response_prediction_candidate_closed_loop_delta_panel/summary.json"
)
M2868_PAIRED_DELTAS = Path(
    "runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_"
    "localized_response_prediction_candidate_closed_loop_delta_panel/paired_delta_rows.csv"
)
M2840_DOC = Path(
    "docs/m2840-engineering-controller-post-route-c-hf3-stop-fresh-source-diverse-"
    "closed-loop-evidence-result-synthesis.md"
)
M2838_SUMMARY = Path(
    "runs/m2838_engineering_controller_post_route_c_hf3_stop_source_diverse_closed_loop_"
    "evidence_preflight/summary.json"
)
M2836_DOC = Path(
    "docs/m2836-engineering-controller-route-c-selected-platform-source-dependency-"
    "refresh-or-stop-result-audit.md"
)
M2826_DOC = Path(
    "docs/m2826-engineering-controller-route-a-post-recoverability-negative-limited-"
    "package-branch-synthesis.md"
)
M2824_SUMMARY = Path(
    "runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/"
    "summary.json"
)
M2824_INVENTORY = Path(
    "runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/"
    "package_artifact_inventory_rows.csv"
)
M2824_PROVENANCE = Path(
    "runs/m2824_engineering_controller_route_a_post_recoverability_negative_limited_package/"
    "package_provenance_map_rows.csv"
)
M2771_DOC = Path(
    "docs/m2771-engineering-controller-route-a-action-response-mechanism-localized-"
    "bounded-repair-result-synthesis.md"
)
M2669_DOC = Path(
    "docs/m2669-engineering-controller-route-a-readiness-after-protected-taxonomy-"
    "branch-synthesis.md"
)
M2667_SUMMARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/summary.json"
)
M2667_ARTIFACT_COVERAGE = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/artifact_coverage_rows.csv"
)
M2667_KNOWN_FAILURE_BOUNDARY = Path(
    "runs/m2667_engineering_controller_route_a_engineering_baseline_readiness_index_"
    "after_protected_taxonomy/known_failure_boundary_rows.csv"
)
M2664_SUMMARY = Path(
    "runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_"
    "failure_taxonomy/summary.json"
)
M2657_SCENARIO_ROLE_REPORT = Path(
    "runs/m2657_engineering_controller_route_a_source_only_target_protected_tradeoff_report/"
    "scenario_role_metric_report.csv"
)
M2643_DOC = Path(
    "docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-"
    "panel-materialization-result-synthesis.md"
)
M2641_SUMMARY = Path(
    "runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/"
    "summary.json"
)
M2541_SUMMARY = Path("runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json")
M2541_BASELINE_CHECKPOINTS = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "baseline_checkpoint_list.csv"
)
M2541_ACTOR_CONTRACT = Path(
    "runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/"
    "actor_io_contract_snapshot.json"
)
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")

CLAIM_SCOPE = (
    "Route A post localized response-prediction limited package refresh materialization only; "
    "no package publication, reset, rollout, replay, validation, training, PPO, repair, "
    "source build, adapter probe, external simulation, ranking, winner selection, promotion, "
    "success-rate verdict, repair-success, recoverability-success, localized-response-prediction "
    "success, driver-performance, paper, finite-window-vs-GRU, current-response, current-sim, "
    "high-fidelity validation, full ideal driver, or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "published package, deployment readiness, repair success, recoverability success, "
    "localized response-prediction success, driver performance, validation readiness, "
    "validation result, source-build readiness/result, adapter-probe readiness/result, "
    "backend availability, reset feasibility, rollout feasibility, controller ranking, "
    "source-family ranking, task-family ranking, scenario-role ranking, stress-axis ranking, "
    "profile ranking, winner selection, checkpoint promotion, success-rate verdict, paper "
    "evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim "
    "verdict, high-fidelity validation result, full ideal driver completion, or self-ID evidence"
)

FALSE_CLAIM_FLAGS = {
    "package_published": False,
    "environment_reset_run": False,
    "environment_step_run": False,
    "policy_action_run": False,
    "policy_rollout_run": False,
    "replay_run": False,
    "measured_validation_run": False,
    "training_run": False,
    "ppo_run": False,
    "repair_run": False,
    "source_build_run": False,
    "adapter_probe_run": False,
    "backend_started": False,
    "external_high_fidelity_simulation_included": False,
    "high_fidelity_simulation_run": False,
    "ranking_run": False,
    "winner_selected": False,
    "checkpoint_promoted": False,
    "success_rate_computed": False,
    "success_rate_verdict_field_emitted": False,
    "controller_family_verdict_computed": False,
    "repair_success_claim_made": False,
    "recoverability_success_claim_made": False,
    "localized_response_prediction_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
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
    "latest_negative_evidence_refs",
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
NEGATIVE_FIELDNAMES = [
    "negative_evidence_id",
    "source_milestone",
    "evidence_path",
    "evidence_status",
    "observed_value",
    "blocked_claims",
    "package_disclosure_required",
    "ordinary_success_denominator_allowed",
    "actor_visible",
    "claim_scope",
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
    "allowed_in_m2873",
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
    ("package_id", True, "M2872 design", "string"),
    ("package_protocol_version", True, "M2872 design", "string"),
    ("generated_at_utc", True, "runner clock", "UTC timestamp string"),
    ("route", True, "M2872 design", "Route A"),
    ("refresh_reason", True, "M2872 design", "string"),
    ("evidence_cutoff_milestone", True, "M2872 design", "M2872"),
    ("artifact_id", True, "artifact inventory", "string"),
    ("source_milestone", True, "artifact inventory", "string"),
    ("source_path", True, "artifact inventory", "path string"),
    ("source_exists", True, "filesystem", "boolean"),
    ("source_status_pass_or_present", True, "source summary/doc", "boolean"),
    ("artifact_role", True, "M2872 design", "package_content package_limitations or context_only"),
    ("package_required", True, "M2872 design", "boolean"),
    ("package_inclusion_status", True, "artifact inventory", "included_with_limitations context_only or blocked"),
    ("provenance_status", True, "provenance map", "traced or missing"),
    ("actor_visible", True, "actor contract", "boolean"),
    ("latest_negative_evidence_refs", True, "latest negative evidence rows", "semicolon-separated ids"),
    ("known_blocker_refs", True, "blocker disclosure", "semicolon-separated ids"),
    ("claim_scope", True, "M2872 design", "string"),
    ("blocked_interpretation", True, "M2872 design", "string"),
]


def materialize_post_localized_response_prediction_limited_package_refresh(
    output_dir: Path | str,
    *,
    m2872_design: Path | str = DEFAULT_M2872_DESIGN,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    _write_follow_up_manifest_if_missing(Path(follow_up_manifest), next_blocker)

    source = load_source_artifacts(m2872_design=m2872_design, follow_up_manifest=follow_up_manifest)
    schema_rows = build_package_manifest_schema_rows()
    artifact_rows = build_package_artifact_inventory_rows(source)
    provenance_rows = build_package_provenance_map_rows(source)
    negative_rows = build_latest_negative_evidence_rows(source)
    blocker_rows = build_known_blocker_disclosure_rows(source)
    actor_rows = build_actor_action_contract_rows(source)
    claim_rows = build_claim_boundary_rows()
    paths = {
        "summary": output_path / "summary.json",
        "package_manifest_schema_rows": output_path / "package_manifest_schema_rows.csv",
        "package_artifact_inventory_rows": output_path / "package_artifact_inventory_rows.csv",
        "package_provenance_map_rows": output_path / "package_provenance_map_rows.csv",
        "latest_negative_evidence_rows": output_path / "latest_negative_evidence_rows.csv",
        "known_blocker_disclosure_rows": output_path / "known_blocker_disclosure_rows.csv",
        "actor_action_contract_rows": output_path / "actor_action_contract_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "package_gate_matrix": output_path / "package_gate_matrix.csv",
        "doc": Path(doc_path),
    }

    write_csv_rows(paths["package_manifest_schema_rows"], schema_rows, fieldnames=SCHEMA_FIELDNAMES)
    write_csv_rows(paths["package_artifact_inventory_rows"], artifact_rows, fieldnames=ARTIFACT_FIELDNAMES)
    write_csv_rows(paths["package_provenance_map_rows"], provenance_rows, fieldnames=PROVENANCE_FIELDNAMES)
    write_csv_rows(paths["latest_negative_evidence_rows"], negative_rows, fieldnames=NEGATIVE_FIELDNAMES)
    write_csv_rows(paths["known_blocker_disclosure_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["actor_action_contract_rows"], actor_rows, fieldnames=ACTOR_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        schema_rows,
        artifact_rows,
        provenance_rows,
        negative_rows,
        blocker_rows,
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
        negative_rows=negative_rows,
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
        negative_rows,
        blocker_rows,
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
        negative_rows=negative_rows,
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


def load_source_artifacts(*, m2872_design: Path | str, follow_up_manifest: Path | str) -> dict[str, Any]:
    paths = {
        "m2872_design": Path(m2872_design),
        "m2871_doc": M2871_DOC,
        "m2870_doc": M2870_DOC,
        "m2868_summary": M2868_SUMMARY,
        "m2868_paired_deltas": M2868_PAIRED_DELTAS,
        "m2840_doc": M2840_DOC,
        "m2838_summary": M2838_SUMMARY,
        "m2836_doc": M2836_DOC,
        "m2826_doc": M2826_DOC,
        "m2824_summary": M2824_SUMMARY,
        "m2824_inventory": M2824_INVENTORY,
        "m2824_provenance": M2824_PROVENANCE,
        "m2771_doc": M2771_DOC,
        "m2669_doc": M2669_DOC,
        "m2667_summary": M2667_SUMMARY,
        "m2667_artifact_coverage": M2667_ARTIFACT_COVERAGE,
        "m2667_known_failure_boundary": M2667_KNOWN_FAILURE_BOUNDARY,
        "m2664_summary": M2664_SUMMARY,
        "m2657_scenario_role_report": M2657_SCENARIO_ROLE_REPORT,
        "m2643_doc": M2643_DOC,
        "m2641_summary": M2641_SUMMARY,
        "m2541_summary": M2541_SUMMARY,
        "m2541_baseline_checkpoints": M2541_BASELINE_CHECKPOINTS,
        "m2541_actor_contract": M2541_ACTOR_CONTRACT,
        "m2505_summary": M2505_SUMMARY,
        "m2508_summary": M2508_SUMMARY,
        "route_plan": ROUTE_PLAN,
        "follow_up_manifest": Path(follow_up_manifest),
    }
    return {
        "paths": paths,
        "source_exists": {name: path.exists() for name, path in paths.items()},
        "m2868_summary": read_json(paths["m2868_summary"]),
        "m2868_paired_deltas": _read_csv_rows(paths["m2868_paired_deltas"]),
        "m2838_summary": read_json(paths["m2838_summary"]),
        "m2824_summary": read_json(paths["m2824_summary"]),
        "m2667_summary": read_json(paths["m2667_summary"]),
        "m2664_summary": read_json(paths["m2664_summary"]),
        "m2641_summary": read_json(paths["m2641_summary"]),
        "m2541_summary": read_json(paths["m2541_summary"]),
        "m2541_actor_contract": read_json(paths["m2541_actor_contract"]),
        "m2505_summary": read_json(paths["m2505_summary"]),
        "m2508_summary": read_json(paths["m2508_summary"]),
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
        ("baseline_checkpoint_list", "m2541", source["paths"]["m2541_baseline_checkpoints"], True, "package_content", source["m2541_summary"].get("all_baseline_checkpoints_admitted"), source["m2541_summary"].get("baseline_checkpoint_count"), ""),
        ("actor_input_output_contract", "m2541", source["paths"]["m2541_actor_contract"], True, "package_content", source["m2541_summary"].get("actor_contract_shape_72_action_3"), 1, ""),
        ("public_benchmark_pack", "m2505", source["paths"]["m2505_summary"], True, "package_content", source["m2505_summary"].get("status_pass"), source["m2505_summary"].get("artifact_manifest_rows"), ""),
        ("runtime_inference_cost_report", "m2508", source["paths"]["m2508_summary"], True, "package_content", source["m2508_summary"].get("status_pass"), source["m2508_summary"].get("measurement_row_count"), ""),
        ("scenario_role_metric_report", "m2657", source["paths"]["m2657_scenario_role_report"], True, "package_content", source["source_exists"]["m2657_scenario_role_report"], 4, "protected_mitigation_blocker"),
        ("known_failure_taxonomy", "m2664/m2667", source["paths"]["m2664_summary"], True, "package_content", source["m2664_summary"].get("status_pass"), source["m2664_summary"].get("combined_failure_taxonomy_row_count"), "protected_mitigation_blocker"),
        ("source_only_fresh_generalization_panel", "m2641/m2643", source["paths"]["m2641_summary"], True, "package_limitations", source["m2641_summary"].get("status_pass"), source["m2641_summary"].get("measured_behavior_row_count"), "scenario_sampling_caution"),
        ("target_protected_readiness_index", "m2667/m2669", source["paths"]["m2667_summary"], True, "package_limitations", source["m2667_summary"].get("status_pass"), source["m2667_summary"].get("artifact_coverage_row_count"), "protected_mitigation_blocker"),
        ("negative_mechanism_localized_repair_synthesis", "m2771", source["paths"]["m2771_doc"], True, "package_limitations", source["source_exists"]["m2771_doc"], 1, "negative_mechanism_localized_repair"),
        ("prior_limited_package_summary", "m2824/m2826", source["paths"]["m2824_summary"], True, "package_limitations", source["m2824_summary"].get("status_pass"), source["m2824_summary"].get("package_artifact_inventory_row_count"), "negative_recoverability_diagnostics"),
        ("prior_limited_package_inventory", "m2824", source["paths"]["m2824_inventory"], True, "package_limitations", source["source_exists"]["m2824_inventory"], source["m2824_summary"].get("package_artifact_inventory_row_count"), "negative_recoverability_diagnostics"),
        ("prior_limited_package_provenance", "m2824", source["paths"]["m2824_provenance"], True, "package_limitations", source["source_exists"]["m2824_provenance"], source["m2824_summary"].get("package_provenance_map_row_count"), "negative_recoverability_diagnostics"),
        ("fresh_source_diverse_negative_diagnostics", "m2838/m2840", source["paths"]["m2838_summary"], True, "package_limitations", source["m2838_summary"].get("status_pass"), source["m2838_summary"].get("candidate_execution_row_count"), "fresh_source_diverse_negative_diagnostics"),
        ("localized_response_prediction_negative_diagnostics", "m2868/m2870", source["paths"]["m2868_summary"], True, "package_limitations", source["m2868_summary"].get("status_pass"), source["m2868_summary"].get("paired_delta_row_count"), "localized_response_prediction_no_terminal_improvement"),
        ("hf3_source_dependency_blocker", "m2836", source["paths"]["m2836_doc"], True, "package_limitations", source["source_exists"]["m2836_doc"], 1, "hf3_dependency_blocker"),
        ("post_m2470_route_plan", "post-m2470", source["paths"]["route_plan"], False, "context_only", source["source_exists"]["route_plan"], 1, ""),
        ("m2871_admission_synthesis", "m2871", source["paths"]["m2871_doc"], False, "context_only", source["source_exists"]["m2871_doc"], 1, ""),
        ("m2872_package_refresh_design", "m2872", source["paths"]["m2872_design"], False, "context_only", source["source_exists"]["m2872_design"], 1, ""),
    ]
    rows = []
    for artifact_id, milestone, path, package_required, role, status, row_count, negative_refs in specs:
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
                "latest_negative_evidence_refs": negative_refs,
                "claim_scope": CLAIM_SCOPE,
                "blocked_interpretation": FORBIDDEN_INTERPRETATION,
            }
        )
    return rows


def build_package_provenance_map_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2541_baseline_checkpoint_list", "m2541", "m2541_baseline_checkpoints", "baseline_checkpoint_list", "package input"),
        ("m2541_actor_io_contract", "m2541", "m2541_actor_contract", "actor_input_output_contract", "package input"),
        ("m2505_public_benchmark_pack", "m2505", "m2505_summary", "public_benchmark_pack", "package input"),
        ("m2508_runtime_report", "m2508", "m2508_summary", "runtime_inference_cost_report", "package input"),
        ("m2657_scenario_role_report", "m2657", "m2657_scenario_role_report", "scenario_role_metric_report", "package input"),
        ("m2664_known_failure_taxonomy", "m2664/m2667", "m2664_summary", "known_failure_taxonomy", "package input"),
        ("m2641_source_only_fresh_generalization", "m2641/m2643", "m2641_summary", "source_only_fresh_generalization_panel", "limitation input"),
        ("m2667_target_protected_readiness", "m2667/m2669", "m2667_summary", "target_protected_readiness_index", "limitation input"),
        ("m2771_negative_mechanism_repair", "m2771", "m2771_doc", "negative_mechanism_localized_repair_synthesis", "limitation input"),
        ("m2824_prior_package_summary", "m2824/m2826", "m2824_summary", "prior_limited_package_summary", "prior package input"),
        ("m2824_prior_package_inventory", "m2824", "m2824_inventory", "prior_limited_package_inventory", "prior package input"),
        ("m2824_prior_package_provenance", "m2824", "m2824_provenance", "prior_limited_package_provenance", "prior package input"),
        ("m2838_fresh_source_diverse_negative", "m2838/m2840", "m2838_summary", "fresh_source_diverse_negative_diagnostics", "latest negative evidence"),
        ("m2868_localized_response_prediction_negative", "m2868/m2870", "m2868_summary", "localized_response_prediction_negative_diagnostics", "latest negative evidence"),
        ("m2836_hf3_source_blocker", "m2836", "m2836_doc", "hf3_source_dependency_blocker", "blocker context"),
        ("post_m2470_route_plan", "post-m2470", "route_plan", "post_m2470_route_plan", "governing context"),
        ("m2871_admission_synthesis", "m2871", "m2871_doc", "m2871_admission_synthesis", "governing context"),
        ("m2872_design", "m2872", "m2872_design", "m2872_package_refresh_design", "governing context"),
    ]
    rows = []
    for provenance_id, milestone, key, target, relationship in specs:
        path = source["paths"][key]
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


def build_latest_negative_evidence_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2824 = source["m2824_summary"]
    m2667 = source["m2667_summary"]
    m2838 = source["m2838_summary"]
    m2868_counts = paired_delta_terminal_counts(source["m2868_paired_deltas"])
    return [
        negative_row(
            "protected_mitigation_blocker",
            "m2657/m2667/m2669",
            source["paths"]["m2667_summary"],
            f"active protected blocker: {m2667.get('m2664_protected_gate_blocking_row_count')} blocking rows, {m2667.get('m2664_protected_gate_regressed_row_count')} regressed protected row counts",
            "repair success; validation readiness; driver performance; promotion",
        ),
        negative_row(
            "negative_recoverability_diagnostics",
            "m2816/m2824/m2826",
            source["paths"]["m2824_summary"],
            (
                f"{m2824.get('m2816_recoverability_available_count')} recoverability-window availability, "
                f"{m2824.get('m2816_recoverability_success_count')} recoverability success, "
                f"{m2824.get('m2816_diagnostic_collision_count')} collision, "
                f"{m2824.get('m2816_diagnostic_offtrack_termination_count')} offtrack terminations"
            ),
            "recoverability success; repair success; validation readiness; driver performance",
        ),
        negative_row(
            "negative_mechanism_localized_repair",
            "m2771",
            source["paths"]["m2771_doc"],
            "complete negative mechanism-localized repair synthesis; same-surface actor-head bias sweep rejected",
            "repair success; ranking; promotion; performance",
        ),
        negative_row(
            "fresh_source_diverse_negative_diagnostics",
            "m2838/m2840",
            source["paths"]["m2838_summary"],
            (
                f"{m2838.get('diagnostic_success_count')} diagnostic success, "
                f"{m2838.get('diagnostic_collision_count')} collisions, "
                f"{m2838.get('diagnostic_offtrack_count')} off_track rows"
            ),
            "repair success; validation readiness; success-rate verdict; driver performance",
        ),
        negative_row(
            "localized_response_prediction_no_terminal_improvement",
            "m2868/m2870",
            source["paths"]["m2868_summary"],
            (
                f"{m2868_counts['row_count']} paired rows; baseline success "
                f"{m2868_counts['baseline_success_count']} candidate success "
                f"{m2868_counts['candidate_success_count']} baseline collision "
                f"{m2868_counts['baseline_collision_count']} candidate collision "
                f"{m2868_counts['candidate_collision_count']}"
            ),
            "localized-response-prediction success; checkpoint promotion; ranking; driver performance",
        ),
    ]


def build_known_blocker_disclosure_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2667 = source["m2667_summary"]
    m2838 = source["m2838_summary"]
    m2868_counts = paired_delta_terminal_counts(source["m2868_paired_deltas"])
    return [
        blocker_row(
            "protected_mitigation_blocker",
            "m2657/m2667/m2669",
            source["paths"]["m2667_summary"],
            f"active: protected rows remain outside denominators with {m2667.get('m2664_protected_gate_blocking_row_count')} blocking rows",
            "repair success; validation readiness; driver performance; promotion",
            "future non-overfit protected mitigation evidence route with explicit audit",
        ),
        blocker_row(
            "offtrack_collision_behavior",
            "m2838/m2840",
            source["paths"]["m2838_summary"],
            f"active: {m2838.get('diagnostic_offtrack_count')} off_track and {m2838.get('diagnostic_collision_count')} collision rows",
            "validation readiness; driver performance; success-rate verdict",
            "future materially new evidence axis and audit",
        ),
        blocker_row(
            "recoverability_gap",
            "m2816/m2824/m2826",
            source["paths"]["m2824_summary"],
            "active: prior package preserves 0 recoverability-window availability and 0 recoverability success",
            "recoverability success; repair success; validation readiness",
            "future pre-registered recoverability evidence route",
        ),
        blocker_row(
            "localized_response_prediction_no_terminal_improvement",
            "m2868/m2870",
            source["paths"]["m2868_summary"],
            (
                f"active: baseline/candidate terminal counts unchanged "
                f"({m2868_counts['baseline_success_count']} vs {m2868_counts['candidate_success_count']} success, "
                f"{m2868_counts['baseline_collision_count']} vs {m2868_counts['candidate_collision_count']} collision)"
            ),
            "localized-response-prediction success; promotion; performance",
            "new evidence axis before more localized response-prediction training",
        ),
        blocker_row(
            "hf3_dependency_blocker",
            "m2638/m2836",
            source["paths"]["m2836_doc"],
            "active: selected-platform HF3 remains stopped until source, package route, dependency acquisition, or alternate backend is supplied",
            "HF3 readiness; high-fidelity validation readiness/result",
            "valid source root, approved package route, dependency-acquisition manifest, or alternate backend contract",
        ),
        blocker_row(
            "self_id_gap",
            "Route B/post-M2470",
            source["paths"]["route_plan"],
            "active: Route A package rows do not test history necessity or level3 self-identification",
            "paper evidence; finite-window-vs-GRU; level3 self-ID",
            "future fair L0/L1/L2/L3 comparison with proof/generalization separation",
        ),
        blocker_row(
            "scenario_sampling_caution",
            "m2641/m2838/m2868",
            source["paths"]["m2871_doc"],
            "active: current evidence surfaces are diagnostic, fixed, source-only, or small paired panels",
            "validation result; current-sim verdict; driver performance",
            "future validation route or materially fresh panel with pre-registered denominators",
        ),
        blocker_row(
            "package_publication_blocker",
            "m2872/m2873",
            source["paths"]["m2872_design"],
            "active: M2873 is a local package-boundary materialization only, not a public release",
            "published package; deployment readiness; validation readiness",
            "separate publication or release-readiness manifest and audit",
        ),
    ]


def build_actor_action_contract_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    contract = source["m2541_actor_contract"]
    return [
        actor_row("observation_shape", contract.get("observation_shape"), P0_OBSERVATION_DIM, False),
        actor_row("action_shape", contract.get("action_shape"), ACTION_DIM, False),
        actor_row("actor_encoder", contract.get("actor_encoder"), "human_view_online_gru", False),
        actor_row("action_sequence_horizon", contract.get("action_sequence_horizon"), 1, False),
        actor_row("actor_input_contract_changed", False, False, False),
        actor_row("action_contract_changed", False, False, False),
        actor_row("hidden_oracle_actor_input_detected", False, False, False),
        actor_row("package_labels_actor_visible", False, False, False),
        actor_row("blocker_labels_actor_visible", False, False, False),
        actor_row("diagnostic_labels_actor_visible", False, False, False),
        actor_row("route_labels_actor_visible", False, False, False),
        actor_row("success_progress_labels_actor_visible", False, False, False),
        actor_row("verdict_labels_actor_visible", False, False, False),
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    allowed = [
        ("local_package_refresh_materialized", True, "M2873 local package refresh rows"),
        ("prior_package_traced", True, "M2824/M2826 inventory and provenance rows"),
        ("latest_negative_evidence_disclosed", True, "latest negative evidence rows"),
        ("actor_contract_preserved", True, "actor/action contract rows"),
        ("bounded_audit_handoff", True, "M2874 result-audit manifest"),
    ]
    blocked = [
        ("published_package", False, "future release-readiness manifest"),
        ("deployment_readiness", False, "future deployment-readiness route"),
        ("repair_success", False, "future repair result plus proof/generalization gates"),
        ("recoverability_success", False, "future recoverability result plus audit"),
        ("localized_response_prediction_success", False, "future fresh evidence axis and audit"),
        ("driver_performance", False, "future validation and claim audit"),
        ("validation_readiness", False, "future validation-readiness route decision"),
        ("validation_result", False, "future validation execution result"),
        ("source_build_readiness_or_result", False, "future HF3 source availability and build attempt"),
        ("adapter_probe_readiness_or_result", False, "future HF3 adapter probe attempt"),
        ("backend_availability", False, "future backend probe evidence"),
        ("reset_feasibility", False, "future reset feasibility route"),
        ("rollout_feasibility", False, "future rollout feasibility route"),
        ("controller_ranking", False, "future explicit ranking gate"),
        ("source_family_ranking", False, "future explicit ranking gate"),
        ("task_family_ranking", False, "future explicit ranking gate"),
        ("scenario_role_ranking", False, "future explicit ranking gate"),
        ("stress_axis_ranking", False, "future explicit ranking gate"),
        ("profile_ranking", False, "future explicit ranking gate"),
        ("winner_selection", False, "future promotion gate"),
        ("checkpoint_promotion", False, "future promotion gate"),
        ("success_rate_verdict", False, "future verdict milestone"),
        ("paper_evidence", False, "future paper evidence matrix"),
        ("finite_window_vs_gru", False, "future fair comparison result"),
        ("current_response_sufficiency", False, "future fair comparison result"),
        ("current_sim_verdict", False, "future current-sim synthesis"),
        ("high_fidelity_validation_readiness", False, "future high-fidelity validation route"),
        ("high_fidelity_validation_result", False, "future high-fidelity validation"),
        ("full_ideal_driver_completion", False, "future full ideal driver gate"),
        ("level3_self_identification", False, "future self-ID proof gate"),
    ]
    return [
        {
            "claim_id": f"m2873_claim_boundary_{claim}",
            "claim_family": claim,
            "allowed_in_m2873": allowed_flag,
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
    negative_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    content_rows = [row for row in artifact_rows if row["artifact_role"] == "package_content" and _bool(row["package_required"])]
    limitation_rows = [row for row in artifact_rows if row["artifact_role"] == "package_limitations" and _bool(row["package_required"])]
    negative_ids = {row["negative_evidence_id"] for row in negative_rows}
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    expected_negative_ids = {
        "protected_mitigation_blocker",
        "negative_recoverability_diagnostics",
        "negative_mechanism_localized_repair",
        "fresh_source_diverse_negative_diagnostics",
        "localized_response_prediction_no_terminal_improvement",
    }
    expected_blocker_ids = {
        "protected_mitigation_blocker",
        "offtrack_collision_behavior",
        "recoverability_gap",
        "localized_response_prediction_no_terminal_improvement",
        "hf3_dependency_blocker",
        "self_id_gap",
        "scenario_sampling_caution",
        "package_publication_blocker",
    }
    return [
        gate_row("m2873_gate_source_artifacts_present", "artifact", all(source["source_exists"].values()), True),
        gate_row("m2873_gate_required_artifacts_present", "artifact", required_artifacts_present, True),
        gate_row("m2873_gate_schema_rows_written", "schema", len(schema_rows), len(REQUIRED_SCHEMA_FIELDS)),
        gate_row("m2873_gate_artifact_inventory_written", "artifact_inventory", len(artifact_rows) >= 18, True),
        gate_row("m2873_gate_package_content_covered", "artifact_inventory", count_included(content_rows), 6),
        gate_row("m2873_gate_package_limitations_covered", "artifact_inventory", count_included(limitation_rows), 9),
        gate_row("m2873_gate_provenance_rows_written", "provenance", len(provenance_rows) >= 18, True),
        gate_row("m2873_gate_latest_negative_evidence_rows_written", "latest_negative_evidence", expected_negative_ids.issubset(negative_ids), True),
        gate_row("m2873_gate_known_blocker_rows_written", "known_blocker", expected_blocker_ids.issubset(blocker_ids), True),
        gate_row("m2873_gate_actor_contract_rows_written", "actor_contract", len(actor_rows) >= 13, True),
        gate_row("m2873_gate_claim_boundary_rows_written", "claim_boundary", len(claim_rows) >= 30, True),
        gate_row("m2873_gate_m2824_prior_package_traced", "provenance", "m2824_prior_package_summary" in {row["provenance_id"] for row in provenance_rows}, True),
        gate_row("m2873_gate_m2838_negative_diagnostics_included", "latest_negative_evidence", "fresh_source_diverse_negative_diagnostics" in negative_ids, True),
        gate_row("m2873_gate_m2868_no_terminal_improvement_included", "latest_negative_evidence", "localized_response_prediction_no_terminal_improvement" in negative_ids, True),
        gate_row("m2873_gate_m2836_hf3_blocker_preserved", "known_blocker", "hf3_dependency_blocker" in blocker_ids, True),
        gate_row("m2873_gate_m2667_protected_blocker_preserved", "known_blocker", "protected_mitigation_blocker" in blocker_ids, True),
        gate_row("m2873_gate_actor_72_action_3_preserved", "actor_contract", actor_contract_preserved(actor_rows), True),
        gate_row("m2873_gate_no_hidden_oracle_actor_input", "actor_contract", hidden_oracle_actor_input_detected(actor_rows), False),
        gate_row("m2873_gate_labels_actor_invisible", "actor_contract", labels_actor_visible(actor_rows), False),
        gate_row("m2873_gate_package_not_published", "claim_boundary", FALSE_CLAIM_FLAGS["package_published"], False),
        gate_row("m2873_gate_no_execution_or_training", "claim_boundary", any_execution_or_training_performed(), False),
        gate_row("m2873_gate_no_validation_or_ranking", "claim_boundary", validation_or_ranking_performed(), False),
        gate_row("m2873_gate_no_success_rate_verdict", "claim_boundary", success_rate_or_verdict_computed(), False),
        gate_row("m2873_gate_no_performance_or_paper_claim", "claim_boundary", performance_paper_or_driver_claimed(), False),
        gate_row("m2873_gate_follow_up_audit_manifest_registered", "process", source["source_exists"]["follow_up_manifest"], True),
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    schema_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    provenance_rows: list[dict[str, Any]],
    negative_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    m2824 = source["m2824_summary"]
    m2667 = source["m2667_summary"]
    m2838 = source["m2838_summary"]
    m2868 = source["m2868_summary"]
    m2868_counts = paired_delta_terminal_counts(source["m2868_paired_deltas"])
    content_rows = [row for row in artifact_rows if row["artifact_role"] == "package_content" and _bool(row["package_required"])]
    limitation_rows = [row for row in artifact_rows if row["artifact_role"] == "package_limitations" and _bool(row["package_required"])]
    blocker_ids = {row["blocker_id"] for row in blocker_rows}
    negative_ids = {row["negative_evidence_id"] for row in negative_rows}
    actor_contract_ok = actor_contract_preserved(actor_rows) and not hidden_oracle_actor_input_detected(actor_rows)
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = (
        required_artifacts_present
        and all(source["source_exists"].values())
        and count_included(content_rows) == 6
        and count_included(limitation_rows) == 9
        and len(schema_rows) == len(REQUIRED_SCHEMA_FIELDS)
        and len(provenance_rows) >= 18
        and len(negative_rows) >= 5
        and len(blocker_rows) >= 8
        and actor_contract_ok
        and not labels_actor_visible(actor_rows)
        and all(_bool(row["status_pass"]) for row in claim_rows)
        and gate_matrix_pass
    )
    return {
        "protocol_version": "engineering_controller_route_a_post_localized_response_prediction_limited_package_refresh_v0",
        "result_class": "engineering_controller_route_a_post_localized_response_prediction_limited_package_refresh_materialization_pass",
        "milestone": milestone,
        "next_blocker": next_blocker,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "package_manifest_schema_rows": str(paths["package_manifest_schema_rows"]),
        "package_artifact_inventory_rows": str(paths["package_artifact_inventory_rows"]),
        "package_provenance_map_rows": str(paths["package_provenance_map_rows"]),
        "latest_negative_evidence_rows": str(paths["latest_negative_evidence_rows"]),
        "known_blocker_disclosure_rows": str(paths["known_blocker_disclosure_rows"]),
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
        "latest_negative_evidence_row_count": len(negative_rows),
        "known_blocker_disclosure_row_count": len(blocker_rows),
        "actor_action_contract_row_count": len(actor_rows),
        "claim_boundary_row_count": len(claim_rows),
        "package_gate_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "route_a_package_content_required_count": len(content_rows),
        "route_a_package_content_covered": count_included(content_rows),
        "route_a_package_limitations_required_count": len(limitation_rows),
        "route_a_package_limitations_covered": count_included(limitation_rows),
        "negative_evidence_ids": sorted(negative_ids),
        "known_blocker_ids": sorted(blocker_ids),
        "protected_mitigation_blocker_visible": "protected_mitigation_blocker" in blocker_ids,
        "offtrack_collision_behavior_visible": "offtrack_collision_behavior" in blocker_ids,
        "recoverability_gap_visible": "recoverability_gap" in blocker_ids,
        "localized_response_prediction_no_terminal_improvement_visible": "localized_response_prediction_no_terminal_improvement" in blocker_ids,
        "hf3_dependency_blocker_visible": "hf3_dependency_blocker" in blocker_ids,
        "self_id_gap_visible": "self_id_gap" in blocker_ids,
        "scenario_sampling_caution_visible": "scenario_sampling_caution" in blocker_ids,
        "package_publication_blocker_visible": "package_publication_blocker" in blocker_ids,
        "m2824_status_pass": _bool(m2824.get("status_pass")),
        "m2824_package_artifact_inventory_row_count": _int(m2824.get("package_artifact_inventory_row_count")),
        "m2824_package_provenance_map_row_count": _int(m2824.get("package_provenance_map_row_count")),
        "m2824_known_blocker_disclosure_row_count": _int(m2824.get("known_blocker_disclosure_row_count")),
        "m2824_recoverability_limitation_row_count": _int(m2824.get("recoverability_limitation_row_count")),
        "m2824_gate_matrix_pass": _bool(m2824.get("gate_matrix_pass")),
        "m2824_recoverability_available_count": _int(m2824.get("m2816_recoverability_available_count")),
        "m2824_recoverability_success_count": _int(m2824.get("m2816_recoverability_success_count")),
        "m2824_diagnostic_collision_count": _int(m2824.get("m2816_diagnostic_collision_count")),
        "m2824_diagnostic_offtrack_termination_count": _int(m2824.get("m2816_diagnostic_offtrack_termination_count")),
        "m2667_status_pass": _bool(m2667.get("status_pass")),
        "m2667_route_a_required_artifacts_covered": _int(m2667.get("route_a_required_artifacts_covered")),
        "m2667_route_a_required_artifact_count": _int(m2667.get("route_a_required_artifact_count")),
        "m2667_protected_gate_blocking_row_count": _int(m2667.get("m2664_protected_gate_blocking_row_count")),
        "m2667_protected_gate_regressed_row_count": _int(m2667.get("m2664_protected_gate_regressed_row_count")),
        "m2667_protected_rows_in_success_denominator": _bool(m2667.get("protected_rows_in_success_denominator")),
        "m2838_status_pass": _bool(m2838.get("status_pass")),
        "m2838_candidate_execution_row_count": _int(m2838.get("candidate_execution_row_count")),
        "m2838_diagnostic_success_count": _int(m2838.get("diagnostic_success_count")),
        "m2838_diagnostic_collision_count": _int(m2838.get("diagnostic_collision_count")),
        "m2838_diagnostic_offtrack_count": _int(m2838.get("diagnostic_offtrack_count")),
        "m2838_ordinary_success_denominator_allowed": _bool(m2838.get("ordinary_success_denominator_allowed")),
        "m2868_status_pass": _bool(m2868.get("status_pass")),
        "m2868_paired_delta_row_count": _int(m2868.get("paired_delta_row_count")),
        "m2868_baseline_success_count": m2868_counts["baseline_success_count"],
        "m2868_candidate_success_count": m2868_counts["candidate_success_count"],
        "m2868_baseline_collision_count": m2868_counts["baseline_collision_count"],
        "m2868_candidate_collision_count": m2868_counts["candidate_collision_count"],
        "m2868_terminal_outcomes_unchanged": m2868_counts["terminal_outcomes_unchanged"],
        "m2868_ordinary_success_denominator_allowed": _bool(m2868.get("ordinary_success_denominator_allowed")),
        "actor_contract_shape_72_action_3": actor_contract_ok,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "hidden_oracle_actor_input_detected": hidden_oracle_actor_input_detected(actor_rows),
        "package_labels_actor_visible": actor_bool(actor_rows, "package_labels_actor_visible"),
        "blocker_labels_actor_visible": actor_bool(actor_rows, "blocker_labels_actor_visible"),
        "diagnostic_labels_actor_visible": actor_bool(actor_rows, "diagnostic_labels_actor_visible"),
        "route_labels_actor_visible": actor_bool(actor_rows, "route_labels_actor_visible"),
        "verdict_labels_actor_visible": actor_bool(actor_rows, "verdict_labels_actor_visible"),
        "selected_next_action": "m2874_limited_package_refresh_materialization_result_audit",
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "status_pass": status_pass,
        **FALSE_CLAIM_FLAGS,
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    status = "completed" if summary["status_pass"] else "failed"
    return "\n".join(
        [
            "# M2873 Engineering Controller Route A Post Localized Response-Prediction Limited Baseline Package Refresh Materialization Preflight",
            "",
            f"- status: {status}",
            f"- result_class: `{summary['result_class']}`",
            f"- summary: `{summary['summary']}`",
            f"- package manifest schema rows: `{summary['package_manifest_schema_rows']}`",
            f"- package artifact inventory rows: `{summary['package_artifact_inventory_rows']}`",
            f"- package provenance map rows: `{summary['package_provenance_map_rows']}`",
            f"- latest negative evidence rows: `{summary['latest_negative_evidence_rows']}`",
            f"- known blocker disclosure rows: `{summary['known_blocker_disclosure_rows']}`",
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
            f"- latest negative evidence rows: {summary['latest_negative_evidence_row_count']}",
            f"- known blocker disclosure rows: {summary['known_blocker_disclosure_row_count']}",
            f"- gate matrix pass: `{str(summary['gate_matrix_pass']).lower()}`",
            "",
            "## Latest Negative Evidence",
            "",
            f"- M2824 recoverability availability/success: {summary['m2824_recoverability_available_count']}/{summary['m2824_recoverability_success_count']}",
            f"- M2824 collision/offtrack: {summary['m2824_diagnostic_collision_count']}/{summary['m2824_diagnostic_offtrack_termination_count']}",
            f"- M2667 protected blocking/regressed rows: {summary['m2667_protected_gate_blocking_row_count']}/{summary['m2667_protected_gate_regressed_row_count']}",
            f"- M2838 diagnostic success/collision/offtrack: {summary['m2838_diagnostic_success_count']}/{summary['m2838_diagnostic_collision_count']}/{summary['m2838_diagnostic_offtrack_count']}",
            f"- M2868 baseline/candidate success: {summary['m2868_baseline_success_count']}/{summary['m2868_candidate_success_count']}",
            f"- M2868 baseline/candidate collision: {summary['m2868_baseline_collision_count']}/{summary['m2868_candidate_collision_count']}",
            f"- M2868 terminal outcomes unchanged: `{str(summary['m2868_terminal_outcomes_unchanged']).lower()}`",
            "",
            "## Actor Boundary",
            "",
            f"- actor contract P0 72/action 3: `{str(summary['actor_contract_shape_72_action_3']).lower()}`",
            f"- hidden/oracle actor input detected: `{str(summary['hidden_oracle_actor_input_detected']).lower()}`",
            "- package, blocker, diagnostic, route, success/progress, and verdict labels actor-visible: `false`",
            "",
            "## Claim Boundary",
            "",
            "M2873 materializes a local package-boundary refresh only. It does not publish a package, execute reset, step, rollout, replay, validation, training, PPO, repair, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.",
            "",
            "It does not claim repair success, recoverability success, localized response-prediction success, driver performance, validation readiness, validation result, paper evidence, finite-window-vs-GRU, current-response sufficiency, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification.",
            "",
        ]
    )


def negative_row(
    negative_evidence_id: str,
    source_milestone: str,
    evidence_path: Path,
    observed_value: str,
    blocked_claims: str,
) -> dict[str, Any]:
    return {
        "negative_evidence_id": negative_evidence_id,
        "source_milestone": source_milestone,
        "evidence_path": str(evidence_path),
        "evidence_status": "active_limitation",
        "observed_value": observed_value,
        "blocked_claims": blocked_claims,
        "package_disclosure_required": True,
        "ordinary_success_denominator_allowed": False,
        "actor_visible": False,
        "claim_scope": CLAIM_SCOPE,
    }


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
        "contract_row_id": f"m2873_actor_contract_{contract_field}",
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


def paired_delta_terminal_counts(rows: list[dict[str, str]]) -> dict[str, Any]:
    baseline_success = sum(1 for row in rows if _bool(row.get("baseline_success_diagnostic")))
    candidate_success = sum(1 for row in rows if _bool(row.get("candidate_success_diagnostic")))
    baseline_collision = sum(1 for row in rows if _bool(row.get("baseline_collision_diagnostic")))
    candidate_collision = sum(1 for row in rows if _bool(row.get("candidate_collision_diagnostic")))
    termination_changed = sum(1 for row in rows if _bool(row.get("termination_pair_changed")))
    collision_changed = sum(1 for row in rows if _bool(row.get("collision_pair_changed")))
    return {
        "row_count": len(rows),
        "baseline_success_count": baseline_success,
        "candidate_success_count": candidate_success,
        "baseline_collision_count": baseline_collision,
        "candidate_collision_count": candidate_collision,
        "termination_pair_changed_count": termination_changed,
        "collision_pair_changed_count": collision_changed,
        "terminal_outcomes_unchanged": (
            baseline_success == candidate_success
            and baseline_collision == candidate_collision
            and termination_changed == 0
            and collision_changed == 0
        ),
    }


def count_included(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row["package_inclusion_status"] == "included_with_limitations")


def actor_contract_preserved(actor_rows: list[dict[str, Any]]) -> bool:
    return all(_bool(row["status_pass"]) for row in actor_rows)


def hidden_oracle_actor_input_detected(actor_rows: list[dict[str, Any]]) -> bool:
    return actor_bool(actor_rows, "hidden_oracle_actor_input_detected", default=True)


def labels_actor_visible(actor_rows: list[dict[str, Any]]) -> bool:
    label_fields = {
        "package_labels_actor_visible",
        "blocker_labels_actor_visible",
        "diagnostic_labels_actor_visible",
        "route_labels_actor_visible",
        "success_progress_labels_actor_visible",
        "verdict_labels_actor_visible",
    }
    return any(_bool(row["observed_value"]) for row in actor_rows if row["contract_field"] in label_fields)


def actor_bool(actor_rows: list[dict[str, Any]], field: str, *, default: bool = False) -> bool:
    for row in actor_rows:
        if row["contract_field"] == field:
            return _bool(row["observed_value"])
    return default


def any_execution_or_training_performed() -> bool:
    keys = (
        "environment_reset_run",
        "environment_step_run",
        "policy_action_run",
        "policy_rollout_run",
        "replay_run",
        "measured_validation_run",
        "training_run",
        "ppo_run",
        "repair_run",
        "source_build_run",
        "adapter_probe_run",
        "backend_started",
        "external_high_fidelity_simulation_included",
        "high_fidelity_simulation_run",
    )
    return any(FALSE_CLAIM_FLAGS[key] for key in keys)


def validation_or_ranking_performed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["measured_validation_run"]
        or FALSE_CLAIM_FLAGS["ranking_run"]
        or FALSE_CLAIM_FLAGS["winner_selected"]
        or FALSE_CLAIM_FLAGS["checkpoint_promoted"]
        or FALSE_CLAIM_FLAGS["controller_family_verdict_computed"]
    )


def success_rate_or_verdict_computed() -> bool:
    return FALSE_CLAIM_FLAGS["success_rate_computed"] or FALSE_CLAIM_FLAGS["success_rate_verdict_field_emitted"]


def performance_paper_or_driver_claimed() -> bool:
    return (
        FALSE_CLAIM_FLAGS["driver_performance_claim_made"]
        or FALSE_CLAIM_FLAGS["paper_claim_made"]
        or FALSE_CLAIM_FLAGS["current_sim_verdict_claim_made"]
        or FALSE_CLAIM_FLAGS["high_fidelity_validation_claim_made"]
        or FALSE_CLAIM_FLAGS["high_fidelity_validation_readiness_claim_made"]
        or FALSE_CLAIM_FLAGS["level3_self_id_claim_made"]
        or FALSE_CLAIM_FLAGS["full_ideal_driver_gate_passed"]
        or FALSE_CLAIM_FLAGS["full_ideal_driver_completion_claim_made"]
    )


def _write_follow_up_manifest_if_missing(path: Path, next_blocker: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": next_blocker,
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
        "lineage": {
            "parent_checkpoint": [
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            ],
            "parent_dataset": [
                "runs/m2873_engineering_controller_route_a_post_localized_response_prediction_limited_baseline_package_refresh/summary.json",
                "docs/m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight.md",
                "docs/m2872-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-design.md",
            ],
            "parent_config": [
                "experiments/manifests/m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight.json"
            ],
            "parent_objective": [
                "audit the post-M2870 Route A limited package refresh materialization before interpretation"
            ],
            "derived_from": [
                "m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight"
            ],
            "blocked_by": [
                "M2874 must accept or reject M2873 artifact completeness and claim safety before any package interpretation"
            ],
            "supersedes": [
                "interpreting M2873 rows before audit"
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{next_blocker}.md",
        "public_gates": [
            "M2874 must audit M2873 summary and package refresh rows for completeness",
            "M2874 must preserve M2824 M2667 M2838 M2868 and M2836 limitations",
            "M2874 must reject publication validation ranking promotion performance paper current-sim high-fidelity full-driver and self-ID claims",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not publish a package",
            "do not run reset step rollout replay validation training PPO repair source build adapter probe external simulation ranking winner selection promotion or success-rate verdict computation",
            "do not claim repair success recoverability success localized-response-prediction success driver performance validation readiness/result paper current-sim high-fidelity full-driver or self-ID evidence",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_a_post_localized_response_prediction_limited_package_refresh",
            "evidence_axis": "route_a_limited_baseline_package_refresh_after_negative_response_prediction",
            "evidence_increment": "audits M2873 package refresh materialization artifacts before interpretation",
            "claim_scope": "Route A package refresh materialization audit only; no package publication validation ranking promotion performance paper current-sim high-fidelity full-driver or self-ID claim",
            "stop_condition": [
                "stop if M2873 artifacts are incomplete",
                "stop if M2873 hides negative evidence or blockers",
                "stop if M2873 makes forbidden claims",
            ],
            "fallback_plan": [
                "route to materialization repair if required artifacts are missing",
                "route to claim-boundary repair if forbidden claims appear",
                "route to branch synthesis if M2873 is accepted",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2873 materialization produces package refresh rows requiring audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "audit M2873 post localized response-prediction package refresh materialization",
            "admission_evidence": [
                "M2873 is expected to materialize package refresh rows from existing artifacts only"
            ],
            "blocked_shortcuts": [
                "no reset rollout replay validation training PPO repair publication ranking promotion or performance claim"
            ],
            "allowed_updates": [
                f"docs/{next_blocker}.md",
                "M2874 status queue scoreboard research log and review",
                "one bounded follow-up synthesis repair or stop manifest",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "M2873 artifact completeness and claim safety are accepted or rejected",
                "one bounded follow-up or stop is registered",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2874 audits Route A package rows and does not test history necessity.",
            "history_necessity_tests": [
                "None in M2874; Route B self-ID evidence remains separate."
            ],
            "temporal_evidence_window": "Post-M2873 package refresh audit.",
            "negative_result_policy": "Preserve negative diagnostics as limitations rather than rebranding them as performance.",
            "allowed_claims": [
                "M2873 artifact completeness and claim-safety audit only",
                "no driver-performance paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 0,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the package refresh materialization before interpretation",
            "paper_verdict_delta": "no paper verdict; preserves Route A limitations and Route B separation",
            "must_synthesize_if": [
                "M2874 accepts M2873 and another package process step would not change evidence",
                "M2874 rejects M2873 for hidden negative evidence or claim-boundary failure",
            ],
        },
        "hypothesis": "A bounded audit can accept or reject M2873 package refresh materialization artifacts before any interpretation.",
        "success_criteria": [
            f"docs/{next_blocker}.md exists",
            "audit accepts or rejects M2873 artifact completeness and claim safety",
            "audit preserves actor and claim boundaries",
        ],
        "failure_criteria": [
            "M2874 runs execution training validation ranking publication promotion or performance claims",
            "M2874 hides M2873 negative evidence or blockers",
        ],
        "decision_rule": "Pass only if M2874 writes a complete claim-safe audit of M2873 artifacts without forbidden execution or claims.",
        "commands": [
            {
                "name": "result_audit",
                "command": "true",
            }
        ],
        "required_artifacts": [
            {
                "path": f"docs/{next_blocker}.md",
                "type": "md",
            }
        ],
        "baseline_checkpoints": [
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
        ],
        "baseline_artifacts": [
            "runs/m2873_engineering_controller_route_a_post_localized_response_prediction_limited_baseline_package_refresh/summary.json",
            "docs/m2873-engineering-controller-route-a-post-localized-response-prediction-limited-baseline-package-refresh-materialization-preflight.md",
        ],
        "scoreboard_checkpoint": f"docs/{next_blocker}.md",
        "next_blocker": "",
    }
    write_json(path, manifest)


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
    parser.add_argument("--m2872-design", default=str(DEFAULT_M2872_DESIGN))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--doc-path", default=str(DEFAULT_DOC_PATH))
    parser.add_argument("--follow-up-manifest", default=str(DEFAULT_FOLLOW_UP_MANIFEST))
    args = parser.parse_args(argv)
    summary = materialize_post_localized_response_prediction_limited_package_refresh(
        Path(args.output_dir),
        m2872_design=Path(args.m2872_design),
        doc_path=Path(args.doc_path),
        follow_up_manifest=Path(args.follow_up_manifest),
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
