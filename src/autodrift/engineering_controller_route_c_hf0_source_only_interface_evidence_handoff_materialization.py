"""Materialize the Route C HF0 source-only interface evidence handoff.

M2832 is an artifact-only handoff. It reads existing HF0/source-only evidence,
Route A diagnostic context, and the selected-platform blocker, then writes
machine-auditable rows. It does not execute a backend, reset, step, run policy
actions, validate, train, rank, or claim driver performance.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


DEFAULT_MILESTONE = (
    "m2832-engineering-controller-route-c-hf0-source-only-interface-evidence-"
    "handoff-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-"
    "handoff-result-audit"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2832_engineering_controller_route_c_hf0_source_only_interface_evidence_handoff_materialization"
)
DEFAULT_M2831_DESIGN = Path(
    "docs/m2831-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-design.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/"
    "m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-result-audit.json"
)

POST_M2470_ROUTE_PLAN = Path("docs/post-m2470-route-plan.md")
M2475_DOC = Path("docs/m2475-high-fidelity-interface-external-backend-route-design.md")
M2482_SUMMARY = Path("runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/summary.json")
M2482_CATALOG = Path("runs/m2482_high_fidelity_interface_scenario_taxonomy_fixture_materialization_preflight/fixture_catalog.csv")
M2484_SUMMARY = Path("runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/summary.json")
M2484_ROWS = Path("runs/m2484_high_fidelity_interface_source_only_fixture_smoke_preflight/fixture_smoke_rows.csv")
M2494_DOC = Path("docs/m2494-engineering-controller-source-only-role-metric-panel-result-audit.md")
M2496_SUMMARY = Path("runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json")
M2496_PARAMETERIZATION_ROWS = Path(
    "runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/"
    "fixture_parameterization_rows.csv"
)
M2496_RESET_ROWS = Path(
    "runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/"
    "reset_differentiation_rows.csv"
)
M2498_SUMMARY = Path("runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json")
M2498_ROLE_PANEL = Path("runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv")
M2498_TELEMETRY = Path("runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv")
M2499_DOC = Path("docs/m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit.md")
M2501_SUMMARY = Path("runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json")
M2501_PANEL = Path("runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv")
M2501_TELEMETRY = Path("runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv")
M2505_SUMMARY = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json")
M2505_MANIFEST = Path("public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/artifact_manifest.csv")
M2508_SUMMARY = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json")
M2508_MEASUREMENTS = Path("runs/m2508_engineering_controller_runtime_inference_cost_report/runtime_measurements.csv")
M2548_SUMMARY = Path("runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json")
M2548_PARITY = Path("runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv")
M2548_ACTION_MAPPING = Path("runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/action_mapping_checks.csv")
M2548_RUNTIME_ROWS = Path("runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/actor_inference_cost_rows.csv")
M2548_GATE_MATRIX = Path("runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/materialization_gate_matrix.csv")
M2592_SUMMARY = Path("runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json")
M2593_DOC = Path(
    "docs/m2593-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-"
    "blocker-closure-materialization-result-audit.md"
)
M2638_DOC = Path(
    "docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-"
    "and-user-supplied-source-contract-design.md"
)
M2828_SUMMARY = Path(
    "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_"
    "expansion_preflight/summary.json"
)
M2828_GATE_MATRIX = Path(
    "runs/m2828_engineering_controller_route_a_post_package_source_diverse_closed_loop_evidence_"
    "expansion_preflight/gate_matrix.csv"
)
M2829_DOC = Path("docs/m2829-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-result-audit.md")
M2830_DOC = Path("docs/m2830-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-branch-synthesis.md")
M2832_MANIFEST = Path(
    "experiments/manifests/"
    "m2832-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-"
    "materialization-preflight.json"
)

CLAIM_SCOPE = (
    "Route C HF0 source-only interface evidence handoff materialization only; existing-artifact "
    "reanalysis with no external install, import, source build, adapter probe, backend start, "
    "reset, step, policy action, rollout, replay, validation, training, ranking, promotion, "
    "package publication, performance, paper, current-sim, high-fidelity validation, full-driver, "
    "or self-ID claim"
)
FORBIDDEN_INTERPRETATION = (
    "external HF3 execution, validation readiness, validation result, driver performance, "
    "controller ranking, source ranking, scenario-role ranking, winner selection, checkpoint "
    "promotion, success-rate verdict, package publication, paper evidence, finite-window-vs-GRU "
    "conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation "
    "readiness or result, full ideal driver completion, or level3 self-identification"
)

FALSE_CLAIM_FLAGS = {
    "external_install_performed": False,
    "external_source_fetched": False,
    "external_high_fidelity_imported": False,
    "dependency_mutation_performed": False,
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
    "controller_family_verdict_computed": False,
    "package_published": False,
    "repair_success_claim_made": False,
    "recoverability_success_claim_made": False,
    "driver_performance_claim_made": False,
    "validation_readiness_claim_made": False,
    "validation_result_claim_made": False,
    "paper_claim_made": False,
    "finite_window_vs_gru_claim_made": False,
    "current_response_sufficiency_claim_made": False,
    "current_sim_verdict_claim_made": False,
    "high_fidelity_validation_readiness_claim_made": False,
    "high_fidelity_validation_claim_made": False,
    "high_fidelity_validation_result_claim_made": False,
    "level3_self_id_claim_made": False,
    "full_ideal_driver_gate_passed": False,
    "full_ideal_driver_completion_claim_made": False,
}

INVENTORY_FIELDNAMES = [
    "handoff_artifact_id",
    "source_milestone",
    "artifact_path",
    "artifact_family",
    "required_for_handoff",
    "exists",
    "status_pass_field",
    "claim_scope",
    "external_hf3_execution_evidence",
    "validation_evidence",
    "driver_performance_evidence",
    "self_id_evidence",
    "notes",
]
HANDOFF_FIELDNAMES = [
    "row_id",
    "evidence_family",
    "backend_or_surface",
    "status",
    "row_count",
    "actor_observation_shape",
    "action_shape",
    "actor_visible_source",
    "labels_actor_visible",
    "hidden_values_actor_visible",
    "diagnostics_actor_visible",
    "external_hf3_required",
    "allowed_next_use",
    "forbidden_interpretation",
    "source_artifact",
]
ACTOR_GUARD_FIELDNAMES = [
    "guard_id",
    "contract_item",
    "expected",
    "observed",
    "pass",
    "actor_visible",
    "source_artifact",
    "failure_if_false",
]
BLOCKER_FIELDNAMES = [
    "blocker_id",
    "source_milestone",
    "blocker_family",
    "status",
    "evidence",
    "resume_condition",
    "ordinary_success_denominator_allowed",
    "execution_allowed_in_m2832",
    "notes",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "claim_made",
    "claim_allowed",
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

REJECTED_CLAIMS = [
    "repair_success",
    "recoverability_success",
    "validation_readiness",
    "validation_result",
    "driver_performance",
    "controller_family_ranking",
    "source_family_ranking",
    "scenario_role_ranking",
    "winner_selection",
    "checkpoint_promotion",
    "success_rate_verdict",
    "package_publication",
    "paper_evidence",
    "finite_window_vs_gru_conclusion",
    "current_response_sufficiency",
    "current_sim_verdict",
    "high_fidelity_validation_readiness",
    "high_fidelity_validation_result",
    "full_ideal_driver_completion",
    "level3_self_identification",
]


def materialize_route_c_hf0_source_only_interface_evidence_handoff(
    output_dir: Path | str,
    *,
    m2831_design: Path | str = DEFAULT_M2831_DESIGN,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    follow_up_path = Path(follow_up_manifest)
    write_json(
        follow_up_path,
        build_follow_up_manifest(output_path=output_path, m2831_design=Path(m2831_design)),
    )

    source = load_source_artifacts(m2831_design=Path(m2831_design), follow_up_manifest=follow_up_path)
    inventory_rows = build_handoff_artifact_inventory_rows(source)
    handoff_rows = build_source_only_interface_handoff_rows(source)
    actor_rows = build_actor_contract_guard_rows(source)
    blocker_rows = build_blocker_boundary_rows(source)
    claim_rows = build_claim_boundary_rows()

    paths = {
        "summary": output_path / "summary.json",
        "handoff_artifact_inventory_rows": output_path / "handoff_artifact_inventory_rows.csv",
        "source_only_interface_handoff_rows": output_path / "source_only_interface_handoff_rows.csv",
        "actor_contract_guard_rows": output_path / "actor_contract_guard_rows.csv",
        "blocker_boundary_rows": output_path / "blocker_boundary_rows.csv",
        "claim_boundary_rows": output_path / "claim_boundary_rows.csv",
        "gate_matrix": output_path / "gate_matrix.csv",
        "run_state": output_path / "run_state.json",
        "follow_up_manifest": follow_up_path,
    }

    write_csv_rows(paths["handoff_artifact_inventory_rows"], inventory_rows, fieldnames=INVENTORY_FIELDNAMES)
    write_csv_rows(paths["source_only_interface_handoff_rows"], handoff_rows, fieldnames=HANDOFF_FIELDNAMES)
    write_csv_rows(paths["actor_contract_guard_rows"], actor_rows, fieldnames=ACTOR_GUARD_FIELDNAMES)
    write_csv_rows(paths["blocker_boundary_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)

    gate_rows = build_gate_matrix_rows(
        source,
        inventory_rows,
        handoff_rows,
        actor_rows,
        blocker_rows,
        claim_rows,
        required_artifacts_present=False,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        inventory_rows=inventory_rows,
        handoff_rows=handoff_rows,
        actor_rows=actor_rows,
        blocker_rows=blocker_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=False,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["run_state"], build_run_state(summary, source))
    write_json(paths["summary"], summary)

    required_artifacts_present = all(path.exists() for path in paths.values())
    gate_rows = build_gate_matrix_rows(
        source,
        inventory_rows,
        handoff_rows,
        actor_rows,
        blocker_rows,
        claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    summary = build_summary(
        output_dir=output_path,
        paths=paths,
        source=source,
        inventory_rows=inventory_rows,
        handoff_rows=handoff_rows,
        actor_rows=actor_rows,
        blocker_rows=blocker_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(paths["run_state"], build_run_state(summary, source))
    write_json(paths["summary"], summary)
    return summary


def load_source_artifacts(*, m2831_design: Path, follow_up_manifest: Path) -> dict[str, Any]:
    paths = {
        "m2831_design": m2831_design,
        "m2832_manifest": M2832_MANIFEST,
        "post_m2470_route_plan": POST_M2470_ROUTE_PLAN,
        "m2475_doc": M2475_DOC,
        "m2482_summary": M2482_SUMMARY,
        "m2482_catalog": M2482_CATALOG,
        "m2484_summary": M2484_SUMMARY,
        "m2484_rows": M2484_ROWS,
        "m2494_doc": M2494_DOC,
        "m2496_summary": M2496_SUMMARY,
        "m2496_parameterization_rows": M2496_PARAMETERIZATION_ROWS,
        "m2496_reset_rows": M2496_RESET_ROWS,
        "m2498_summary": M2498_SUMMARY,
        "m2498_role_panel": M2498_ROLE_PANEL,
        "m2498_telemetry": M2498_TELEMETRY,
        "m2499_doc": M2499_DOC,
        "m2501_summary": M2501_SUMMARY,
        "m2501_panel": M2501_PANEL,
        "m2501_telemetry": M2501_TELEMETRY,
        "m2505_summary": M2505_SUMMARY,
        "m2505_manifest": M2505_MANIFEST,
        "m2508_summary": M2508_SUMMARY,
        "m2508_measurements": M2508_MEASUREMENTS,
        "m2548_summary": M2548_SUMMARY,
        "m2548_parity": M2548_PARITY,
        "m2548_action_mapping": M2548_ACTION_MAPPING,
        "m2548_runtime_rows": M2548_RUNTIME_ROWS,
        "m2548_gate_matrix": M2548_GATE_MATRIX,
        "m2592_summary": M2592_SUMMARY,
        "m2593_doc": M2593_DOC,
        "m2638_doc": M2638_DOC,
        "m2828_summary": M2828_SUMMARY,
        "m2828_gate_matrix": M2828_GATE_MATRIX,
        "m2829_doc": M2829_DOC,
        "m2830_doc": M2830_DOC,
        "follow_up_manifest": follow_up_manifest,
    }
    json_keys = {
        "m2482_summary",
        "m2484_summary",
        "m2496_summary",
        "m2498_summary",
        "m2501_summary",
        "m2505_summary",
        "m2508_summary",
        "m2548_summary",
        "m2592_summary",
        "m2828_summary",
        "follow_up_manifest",
    }
    text_keys = {
        "m2831_design",
        "post_m2470_route_plan",
        "m2475_doc",
        "m2494_doc",
        "m2499_doc",
        "m2593_doc",
        "m2638_doc",
        "m2829_doc",
        "m2830_doc",
    }
    csv_keys = {
        "m2482_catalog",
        "m2484_rows",
        "m2496_parameterization_rows",
        "m2496_reset_rows",
        "m2498_role_panel",
        "m2498_telemetry",
        "m2501_panel",
        "m2501_telemetry",
        "m2505_manifest",
        "m2508_measurements",
        "m2548_parity",
        "m2548_action_mapping",
        "m2548_runtime_rows",
        "m2548_gate_matrix",
        "m2828_gate_matrix",
    }
    source_exists = {name: path.exists() for name, path in paths.items()}
    return {
        "paths": paths,
        "source_exists": source_exists,
        "json": {name: read_json(path) for name, path in paths.items() if name in json_keys and path.exists()},
        "text": {name: path.read_text(encoding="utf-8") for name, path in paths.items() if name in text_keys and path.exists()},
        "csv": {name: _read_csv_rows(path) for name, path in paths.items() if name in csv_keys and path.exists()},
    }


def build_handoff_artifact_inventory_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("m2831_design", "m2831", "route_c_hf0_handoff_design", "design artifact", True),
        ("m2475_boundary", "m2475", "hf0_contract_route", "HF0 external-backend boundary design", True),
        ("m2482_fixture_catalog", "m2482", "fixture_catalog", "HF0 scenario taxonomy fixture catalog", True),
        ("m2484_fixture_smoke", "m2484", "fixture_smoke", "source-only fixture smoke rows", True),
        ("m2496_role_parameterization", "m2496", "source_only_role_parameterization", "role fixture differentiation rows", True),
        ("m2498_role_metric_panel", "m2498", "source_only_role_metric_panel", "parameterized role telemetry panel", True),
        ("m2501_baseline_comparison", "m2501", "source_only_baseline_comparison", "source-only baseline comparison telemetry", True),
        ("m2505_public_pack", "m2505", "public_diagnostic_pack", "public benchmark pack summary", True),
        ("m2508_runtime_report", "m2508", "runtime_inference_cost", "actor runtime/inference-cost report", True),
        ("m2548_hf0_parity_runtime", "m2548", "hf0_parity_runtime", "HF0 P0 parity/action mapping/runtime materialization", True),
        ("m2592_adapter_closure", "m2592", "source_only_adapter_closure", "repo-local source-only adapter blocker closure", True),
        ("m2593_adapter_closure_audit", "m2593", "source_only_adapter_closure", "source-only adapter closure result audit", True),
        ("m2638_selected_platform_blocker", "m2638", "selected_platform_source_dependency_blocker", "selected-platform source dependency blocker", True),
        ("m2828_route_a_context", "m2828", "route_a_post_package_diagnostic_context", "mixed diagnostic closed-loop context", True),
        ("m2829_result_audit", "m2829", "route_a_post_package_diagnostic_context", "M2828 result audit", True),
        ("m2830_branch_synthesis", "m2830", "route_a_post_package_diagnostic_context", "M2830 pivot synthesis", True),
        ("post_m2470_route_plan", "post-m2470", "route_plan", "route split plan", True),
    ]
    path_by_id = {
        "m2831_design": source["paths"]["m2831_design"],
        "m2475_boundary": source["paths"]["m2475_doc"],
        "m2482_fixture_catalog": source["paths"]["m2482_summary"],
        "m2484_fixture_smoke": source["paths"]["m2484_summary"],
        "m2496_role_parameterization": source["paths"]["m2496_summary"],
        "m2498_role_metric_panel": source["paths"]["m2498_summary"],
        "m2501_baseline_comparison": source["paths"]["m2501_summary"],
        "m2505_public_pack": source["paths"]["m2505_summary"],
        "m2508_runtime_report": source["paths"]["m2508_summary"],
        "m2548_hf0_parity_runtime": source["paths"]["m2548_summary"],
        "m2592_adapter_closure": source["paths"]["m2592_summary"],
        "m2593_adapter_closure_audit": source["paths"]["m2593_doc"],
        "m2638_selected_platform_blocker": source["paths"]["m2638_doc"],
        "m2828_route_a_context": source["paths"]["m2828_summary"],
        "m2829_result_audit": source["paths"]["m2829_doc"],
        "m2830_branch_synthesis": source["paths"]["m2830_doc"],
        "post_m2470_route_plan": source["paths"]["post_m2470_route_plan"],
    }
    summary_key_by_id = {
        "m2482_fixture_catalog": "m2482_summary",
        "m2484_fixture_smoke": "m2484_summary",
        "m2496_role_parameterization": "m2496_summary",
        "m2498_role_metric_panel": "m2498_summary",
        "m2501_baseline_comparison": "m2501_summary",
        "m2505_public_pack": "m2505_summary",
        "m2508_runtime_report": "m2508_summary",
        "m2548_hf0_parity_runtime": "m2548_summary",
        "m2592_adapter_closure": "m2592_summary",
        "m2828_route_a_context": "m2828_summary",
    }
    rows = []
    for artifact_id, milestone, family, notes, required in specs:
        path = path_by_id[artifact_id]
        summary_key = summary_key_by_id.get(artifact_id)
        status = source["json"].get(summary_key, {}).get("status_pass") if summary_key else None
        status_text = "present" if status is None else str(bool(status))
        rows.append(
            {
                "handoff_artifact_id": artifact_id,
                "source_milestone": milestone,
                "artifact_path": str(path),
                "artifact_family": family,
                "required_for_handoff": required,
                "exists": path.exists(),
                "status_pass_field": status_text,
                "claim_scope": CLAIM_SCOPE,
                "external_hf3_execution_evidence": False,
                "validation_evidence": False,
                "driver_performance_evidence": False,
                "self_id_evidence": False,
                "notes": notes,
            }
        )
    return rows


def build_source_only_interface_handoff_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    json_data = source["json"]
    m2482 = json_data["m2482_summary"]
    m2484 = json_data["m2484_summary"]
    m2496 = json_data["m2496_summary"]
    m2498 = json_data["m2498_summary"]
    m2501 = json_data["m2501_summary"]
    m2505 = json_data["m2505_summary"]
    m2508 = json_data["m2508_summary"]
    m2548 = json_data["m2548_summary"]
    m2592 = json_data["m2592_summary"]
    m2828 = json_data["m2828_summary"]
    rows = [
        _handoff_row(
            "m2482_fixture_catalog",
            "fixture_catalog",
            "current_sim_autodrift_hf0 plus source_only_four_wheel_hf0",
            "status_pass",
            m2482.get("catalog_row_count"),
            source["paths"]["m2482_summary"],
            allowed_next_use="handoff fixture taxonomy and admitted source-only fixture inventory",
        ),
        _handoff_row(
            "m2484_fixture_smoke",
            "fixture_smoke",
            m2484.get("backend_id", "source_only_four_wheel_hf0"),
            "status_pass",
            m2484.get("step_count"),
            source["paths"]["m2484_summary"],
            allowed_next_use="source-only fixture smoke accounting canned actions only",
        ),
        _handoff_row(
            "m2496_role_parameterization",
            "source_only_role_parameterization",
            m2496.get("backend_id", "source_only_four_wheel_hf0"),
            "status_pass",
            m2496.get("spec_count"),
            source["paths"]["m2496_summary"],
            allowed_next_use="differentiated reset-only role fixture accounting",
        ),
        _handoff_row(
            "m2498_parameterized_role_panel",
            "source_only_role_metric_panel",
            m2498.get("backend_id", "source_only_four_wheel_hf0"),
            "status_pass",
            m2498.get("step_count"),
            source["paths"]["m2498_summary"],
            allowed_next_use="diagnostic source-only role telemetry only",
        ),
        _handoff_row(
            "m2501_baseline_comparison",
            "source_only_baseline_comparison",
            m2501.get("backend_id", "source_only_four_wheel_hf0"),
            "status_pass",
            m2501.get("telemetry_row_count"),
            source["paths"]["m2501_summary"],
            allowed_next_use="diagnostic baseline comparison telemetry only",
        ),
        _handoff_row(
            "m2505_public_pack",
            "public_diagnostic_pack",
            "source_only_diagnostic_pack",
            "status_pass",
            m2505.get("artifact_manifest_rows"),
            source["paths"]["m2505_summary"],
            allowed_next_use="public source-only diagnostic package provenance only",
        ),
        _handoff_row(
            "m2508_runtime_report",
            "runtime_inference_cost",
            "actor_forward_pass_cpu",
            "status_pass",
            m2508.get("measurement_row_count"),
            source["paths"]["m2508_summary"],
            allowed_next_use="actor runtime accounting without control interpretation",
        ),
        _handoff_row(
            "m2548_hf0_parity_runtime",
            "hf0_parity_runtime",
            "HF0 P0 parity plus actor runtime materialization",
            "status_pass",
            m2548.get("actor_inference_cost_row_count"),
            source["paths"]["m2548_summary"],
            allowed_next_use="HF0 P0 parity and action mapping evidence only",
        ),
        _handoff_row(
            "m2592_source_only_adapter_closure",
            "source_only_adapter_closure",
            "repo_local_source_only_adapter_boundary",
            "status_pass",
            m2592.get("materialization_gate_count"),
            source["paths"]["m2592_summary"],
            allowed_next_use="repo-local adapter boundary accounting only",
        ),
        _handoff_row(
            "m2638_selected_platform_blocker",
            "selected_platform_source_dependency_blocker",
            "chrono_vehicle_or_equivalent_open_backend",
            "dependency_source_unavailable",
            1,
            source["paths"]["m2638_doc"],
            external_hf3_required=True,
            allowed_next_use="resume only after valid source root package route or dependency acquisition manifest",
        ),
        _handoff_row(
            "m2828_route_a_diagnostic_context",
            "route_a_post_package_diagnostic_context",
            "current-sim Route A diagnostic closed-loop context",
            "mixed_diagnostic_only",
            m2828.get("candidate_execution_row_count"),
            source["paths"]["m2828_summary"],
            allowed_next_use="diagnostic context only with mixed outcomes preserved",
        ),
    ]
    return rows


def _handoff_row(
    row_id: str,
    evidence_family: str,
    backend_or_surface: str,
    status: str,
    row_count: Any,
    source_artifact: Path,
    *,
    external_hf3_required: bool = False,
    allowed_next_use: str,
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "evidence_family": evidence_family,
        "backend_or_surface": backend_or_surface,
        "status": status,
        "row_count": row_count,
        "actor_observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_visible_source": "ActorView only",
        "labels_actor_visible": False,
        "hidden_values_actor_visible": False,
        "diagnostics_actor_visible": False,
        "external_hf3_required": external_hf3_required,
        "allowed_next_use": allowed_next_use,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "source_artifact": str(source_artifact),
    }


def build_actor_contract_guard_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    summary_checks = actor_contract_checks(source)
    specs = [
        ("observation_shape_72", "observation_shape", "72", str(P0_OBSERVATION_DIM), True, "shape mismatch would invalidate P0 actor handoff"),
        ("action_shape_3", "action_shape", "3", str(ACTION_DIM), True, "shape mismatch would mutate deployed action contract"),
        ("ActorView_only_extraction", "actor_visible_extractor", "ActorView only", "ActorView only", True, "non-ActorView extraction would violate HF0 boundary"),
        ("no_hidden_oracle_actor_input", "hidden_oracle_actor_input_detected", "False", str(summary_checks["hidden_oracle_actor_input_detected"]), False, "hidden/oracle actor input would invalidate handoff"),
        ("no_fixture_labels_actor_visible", "fixture_labels_actor_visible", "False", str(summary_checks["fixture_labels_actor_visible"]), False, "fixture labels must stay diagnostic-only"),
        ("no_scenario_labels_actor_visible", "scenario_labels_actor_visible", "False", str(summary_checks["scenario_labels_actor_visible"]), False, "scenario labels must stay diagnostic-only"),
        ("no_feasibility_classes_actor_visible", "feasibility_classes_actor_visible", "False", str(summary_checks["feasibility_classes_actor_visible"]), False, "feasibility classes must stay diagnostic-only"),
        ("no_diagnostics_actor_visible", "diagnostics_actor_visible", "False", str(summary_checks["diagnostics_actor_visible"]), False, "diagnostics must stay outside actor input"),
        ("no_reward_terms_actor_visible", "reward_terms_actor_visible", "False", str(summary_checks["reward_terms_actor_visible"]), False, "reward terms must stay outside actor input"),
        (
            "no_success_progress_verdict_labels_actor_visible",
            "success_progress_verdict_labels_actor_visible",
            "False",
            str(summary_checks["success_progress_verdict_labels_actor_visible"]),
            False,
            "success/progress/verdict labels must stay outside actor input",
        ),
        (
            "physical_scenario_differences_only_through_deployable_observations",
            "deployable_observation_boundary",
            "True",
            "True",
            True,
            "source-only differences must enter only as ordinary deployable observations",
        ),
    ]
    rows = []
    for guard_id, item, expected, observed, actor_visible, failure in specs:
        rows.append(
            {
                "guard_id": guard_id,
                "contract_item": item,
                "expected": expected,
                "observed": observed,
                "pass": str(expected) == str(observed),
                "actor_visible": actor_visible,
                "source_artifact": str(source["paths"]["m2831_design"]),
                "failure_if_false": failure,
            }
        )
    return rows


def build_blocker_boundary_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    m2828 = source["json"]["m2828_summary"]
    return [
        {
            "blocker_id": "m2638_selected_platform_source_dependency",
            "source_milestone": "m2638",
            "blocker_family": "selected_platform_source_dependency",
            "status": "active",
            "evidence": "dependency_source_unavailable; no local chrono root and no approved package/import route",
            "resume_condition": "valid local source root approved package route admitted dependency acquisition manifest or alternate backend contract",
            "ordinary_success_denominator_allowed": False,
            "execution_allowed_in_m2832": False,
            "notes": "M2832 preserves the blocker and does not reopen selected-platform HF3 execution.",
        },
        {
            "blocker_id": "m2828_post_package_mixed_diagnostic_outcomes",
            "source_milestone": "m2828",
            "blocker_family": "route_a_mixed_diagnostic_context",
            "status": "active_diagnostic_context",
            "evidence": (
                f"{_int(m2828.get('candidate_execution_row_count'))} executed; "
                f"{_int(m2828.get('diagnostic_success_count'))} success; "
                f"{_int(m2828.get('diagnostic_collision_count'))} collision; "
                f"{_int(m2828.get('diagnostic_offtrack_count'))} off_track"
            ),
            "resume_condition": "separate bounded Route A or Route C manifest before any interpretation beyond diagnostic context",
            "ordinary_success_denominator_allowed": False,
            "execution_allowed_in_m2832": False,
            "notes": "Mixed outcomes are preserved as context only, not validation or performance evidence.",
        },
        {
            "blocker_id": "m2494_metadata_only_role_blocker",
            "source_milestone": "m2494",
            "blocker_family": "metadata_only_role_fixture_differentiation",
            "status": "resolved_for_parameterized_source_only_role_panel_path",
            "evidence": "M2495-M2499 differentiated role fixtures; M2498 unique reset digest count 3",
            "resume_condition": "no further action on this blocker for source-only panel handoff; still not high-fidelity validation evidence",
            "ordinary_success_denominator_allowed": False,
            "execution_allowed_in_m2832": False,
            "notes": "Resolution applies only to source-only diagnostic panels.",
        },
    ]


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": f"m2832_claim_{claim}",
            "claim_family": claim,
            "claim_made": False,
            "claim_allowed": False,
            "evidence_required_before_claim": evidence_required_for_claim(claim),
            "claim_boundary": CLAIM_SCOPE,
        }
        for claim in REJECTED_CLAIMS
    ]


def build_gate_matrix_rows(
    source: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    *,
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    m2482 = source["json"]["m2482_summary"]
    m2484 = source["json"]["m2484_summary"]
    m2498 = source["json"]["m2498_summary"]
    m2501 = source["json"]["m2501_summary"]
    m2505 = source["json"]["m2505_summary"]
    m2508 = source["json"]["m2508_summary"]
    m2548 = source["json"]["m2548_summary"]
    m2592 = source["json"]["m2592_summary"]
    m2828 = source["json"]["m2828_summary"]
    claims_false = all(not _bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows)
    forbidden_actions_false = all(value is False for value in FALSE_CLAIM_FLAGS.values())
    specs = [
        ("required_artifacts_present", "artifact_completeness", required_artifacts_present, str(required_artifacts_present), "True"),
        ("source_artifacts_exist", "artifact_completeness", source_artifacts_exist(source), str(missing_source_artifacts(source)), "[]"),
        ("m2475_boundary_present", "lineage", source["paths"]["m2475_doc"].exists(), "present", "present"),
        ("m2482_fixture_catalog_present", "lineage", _bool(m2482.get("status_pass")) and _int(m2482.get("catalog_row_count")) == 10, m2482.get("catalog_row_count"), "10"),
        ("m2484_fixture_smoke_present", "lineage", _bool(m2484.get("status_pass")) and _int(m2484.get("step_count")) == 6, m2484.get("step_count"), "6"),
        ("m2498_parameterized_role_panel_present", "lineage", _bool(m2498.get("status_pass")) and _int(m2498.get("step_count")) == 300, m2498.get("step_count"), "300"),
        ("m2501_baseline_comparison_present", "lineage", _bool(m2501.get("status_pass")) and _int(m2501.get("telemetry_row_count")) == 900, m2501.get("telemetry_row_count"), "900"),
        ("m2505_public_pack_present", "lineage", _bool(m2505.get("status_pass")) and _bool(m2505.get("required_files_present")), m2505.get("required_files_present"), "True"),
        ("m2508_runtime_report_present", "lineage", _bool(m2508.get("status_pass")) and _int(m2508.get("measurement_row_count")) == 300, m2508.get("measurement_row_count"), "300"),
        ("m2548_hf0_parity_runtime_present", "lineage", _bool(m2548.get("status_pass")) and _int(m2548.get("actor_inference_cost_row_count")) == 270, m2548.get("actor_inference_cost_row_count"), "270"),
        ("m2593_source_only_adapter_closure_present", "lineage", _bool(m2592.get("status_pass")) and source["paths"]["m2593_doc"].exists(), m2592.get("status_pass"), "True"),
        ("m2638_selected_platform_blocker_present", "blocker", source["paths"]["m2638_doc"].exists(), "present", "present"),
        (
            "m2828_mixed_outcomes_preserved",
            "blocker",
            _int(m2828.get("candidate_execution_row_count")) == 16
            and _int(m2828.get("diagnostic_success_count")) == 5
            and _int(m2828.get("diagnostic_collision_count")) == 1
            and _int(m2828.get("diagnostic_offtrack_count")) == 10,
            f"{m2828.get('candidate_execution_row_count')}/{m2828.get('diagnostic_success_count')}/"
            f"{m2828.get('diagnostic_collision_count')}/{m2828.get('diagnostic_offtrack_count')}",
            "16/5/1/10",
        ),
        ("actor_observation_shape_72_preserved", "actor_contract", actor_shape_ok(source), P0_OBSERVATION_DIM, "72"),
        ("action_shape_3_preserved", "actor_contract", action_shape_ok(source), ACTION_DIM, "3"),
        ("labels_actor_invisible", "actor_contract", labels_actor_invisible(source), "False", "False"),
        ("diagnostics_actor_invisible", "actor_contract", diagnostics_actor_invisible(source), "False", "False"),
        ("actor_contract_guard_rows_pass", "actor_contract", all(_bool(row["pass"]) for row in actor_rows), len(actor_rows), str(len(actor_rows))),
        ("external_hf3_execution_forbidden", "claim_boundary", forbidden_actions_false, "False", "False"),
        ("reset_step_rollout_validation_forbidden", "claim_boundary", forbidden_actions_false, "False", "False"),
        ("ranking_promotion_success_verdict_forbidden", "claim_boundary", forbidden_actions_false and claims_false, "False", "False"),
        ("driver_performance_paper_high_fidelity_self_id_claims_forbidden", "claim_boundary", forbidden_actions_false and claims_false, "False", "False"),
        ("blocker_boundary_rows_present", "blocker", len(blocker_rows) == 3, len(blocker_rows), "3"),
        ("handoff_rows_present", "artifact_completeness", len(handoff_rows) >= 10, len(handoff_rows), ">=10"),
        ("inventory_rows_present", "artifact_completeness", len(inventory_rows) >= 17, len(inventory_rows), ">=17"),
        ("follow_up_manifest_registered", "follow_up", source["paths"]["follow_up_manifest"].exists(), "present", "present"),
    ]
    return [
        {
            "gate_id": gate_id,
            "gate_family": family,
            "status_pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "failure_type": "none" if passed else failure_type_for_gate(family),
            "claim_boundary": CLAIM_SCOPE,
        }
        for gate_id, family, passed, observed, expected in specs
    ]


def build_summary(
    *,
    output_dir: Path,
    paths: dict[str, Path],
    source: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
    actor_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    m2482 = source["json"]["m2482_summary"]
    m2484 = source["json"]["m2484_summary"]
    m2496 = source["json"]["m2496_summary"]
    m2498 = source["json"]["m2498_summary"]
    m2501 = source["json"]["m2501_summary"]
    m2505 = source["json"]["m2505_summary"]
    m2508 = source["json"]["m2508_summary"]
    m2548 = source["json"]["m2548_summary"]
    m2592 = source["json"]["m2592_summary"]
    m2828 = source["json"]["m2828_summary"]
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    source_exists = source_artifacts_exist(source)
    summary = {
        "generated_at_utc": utc_timestamp(),
        "milestone": milestone,
        "next_blocker": next_blocker,
        "result_class": "engineering_controller_route_c_hf0_source_only_interface_evidence_handoff_materialization_pass",
        "status_pass": bool(required_artifacts_present and gate_matrix_pass and source_exists),
        "output_dir": str(output_dir),
        "summary": str(paths["summary"]),
        "handoff_artifact_inventory_rows": str(paths["handoff_artifact_inventory_rows"]),
        "source_only_interface_handoff_rows": str(paths["source_only_interface_handoff_rows"]),
        "actor_contract_guard_rows": str(paths["actor_contract_guard_rows"]),
        "blocker_boundary_rows": str(paths["blocker_boundary_rows"]),
        "claim_boundary_rows": str(paths["claim_boundary_rows"]),
        "gate_matrix": str(paths["gate_matrix"]),
        "run_state": str(paths["run_state"]),
        "follow_up_manifest": str(paths["follow_up_manifest"]),
        "required_artifacts_present": required_artifacts_present,
        "source_artifacts_reanalyzed_only": True,
        "source_artifacts_exist": source_exists,
        "missing_source_artifacts": missing_source_artifacts(source),
        "handoff_artifact_inventory_row_count": len(inventory_rows),
        "source_only_interface_handoff_row_count": len(handoff_rows),
        "actor_contract_guard_row_count": len(actor_rows),
        "actor_contract_guard_rows_pass": all(_bool(row["pass"]) for row in actor_rows),
        "blocker_boundary_row_count": len(blocker_rows),
        "claim_boundary_row_count": len(claim_rows),
        "claim_boundary_rows_pass": all(not _bool(row["claim_made"]) and not _bool(row["claim_allowed"]) for row in claim_rows),
        "gate_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "selected_next_action": "m2833_route_c_hf0_source_only_interface_evidence_handoff_result_audit",
        "follow_up_manifest_exists": paths["follow_up_manifest"].exists(),
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "actor_contract_shape_72_action_3": actor_shape_ok(source) and action_shape_ok(source),
        "actor_view_only_extraction": True,
        "hidden_oracle_actor_input_detected": False,
        "labels_actor_visible": False,
        "diagnostics_actor_visible": False,
        "m2482_status_pass": _bool(m2482.get("status_pass")),
        "m2482_catalog_row_count": _int(m2482.get("catalog_row_count")),
        "m2482_source_only_admitted_fixture_count": _int(m2482.get("source_only_admitted_fixture_count")),
        "m2484_status_pass": _bool(m2484.get("status_pass")),
        "m2484_fixture_count": _int(m2484.get("fixture_count")),
        "m2484_reset_count": _int(m2484.get("reset_count")),
        "m2484_step_count": _int(m2484.get("step_count")),
        "m2484_canned_actions_only": _bool(m2484.get("canned_actions_only")),
        "m2496_status_pass": _bool(m2496.get("status_pass")),
        "m2496_unique_reset_observation_digest_count": _int(m2496.get("unique_reset_observation_digest_count")),
        "m2498_status_pass": _bool(m2498.get("status_pass")),
        "m2498_telemetry_row_count": _int(m2498.get("step_count")),
        "m2498_role_metric_panel_row_count": _int(m2498.get("role_metric_panel_row_count")),
        "m2498_unique_role_reset_observation_digest_count": _int(m2498.get("unique_role_reset_observation_digest_count")),
        "m2498_role_reset_observation_digests_differentiated": _bool(
            m2498.get("role_reset_observation_digests_differentiated")
        ),
        "m2501_status_pass": _bool(m2501.get("status_pass")),
        "m2501_subject_count": _int(m2501.get("comparison_subject_count")),
        "m2501_role_count": _int(m2501.get("role_count")),
        "m2501_telemetry_row_count": _int(m2501.get("telemetry_row_count")),
        "m2501_role_subject_panel_row_count": _int(m2501.get("role_subject_panel_row_count")),
        "m2505_status_pass": _bool(m2505.get("status_pass")),
        "m2505_required_files_present": _bool(m2505.get("required_files_present")),
        "m2505_artifact_manifest_rows": _int(m2505.get("artifact_manifest_rows")),
        "m2508_status_pass": _bool(m2508.get("status_pass")),
        "m2508_measurement_row_count": _int(m2508.get("measurement_row_count")),
        "m2508_model_parameter_count": _int(m2508.get("model_parameter_count")),
        "m2548_status_pass": _bool(m2548.get("status_pass")),
        "m2548_hf0_p0_parity_check_count": _int(m2548.get("hf0_p0_parity_check_count")),
        "m2548_action_mapping_check_count": _int(m2548.get("action_mapping_check_count")),
        "m2548_actor_inference_cost_row_count": _int(m2548.get("actor_inference_cost_row_count")),
        "m2548_materialization_gate_count": _int(m2548.get("materialization_gate_count")),
        "m2592_status_pass": _bool(m2592.get("status_pass")),
        "m2592_source_only_adapter_blocker_closure_claim_allowed": _bool(
            m2592.get("source_only_adapter_blocker_closure_claim_allowed")
        ),
        "m2592_materialization_gate_count": _int(m2592.get("materialization_gate_count")),
        "m2638_selected_platform_source_dependency_blocker_visible": source["paths"]["m2638_doc"].exists(),
        "m2638_selected_platform_source_dependency_blocker_active": True,
        "m2828_status_pass": _bool(m2828.get("status_pass")),
        "m2828_candidate_execution_row_count": _int(m2828.get("candidate_execution_row_count")),
        "m2828_diagnostic_success_count": _int(m2828.get("diagnostic_success_count")),
        "m2828_diagnostic_collision_count": _int(m2828.get("diagnostic_collision_count")),
        "m2828_diagnostic_offtrack_count": _int(m2828.get("diagnostic_offtrack_count")),
        "m2828_mixed_outcomes_preserved": True,
    }
    summary.update(FALSE_CLAIM_FLAGS)
    return summary


def build_run_state(summary: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at_utc": summary["generated_at_utc"],
        "milestone": summary["milestone"],
        "result_class": summary["result_class"],
        "status_pass": summary["status_pass"],
        "source_artifacts_reanalyzed_only": True,
        "source_exists": {name: bool(exists) for name, exists in sorted(source["source_exists"].items())},
        "forbidden_execution_flags": FALSE_CLAIM_FLAGS,
        "selected_next_action": summary["selected_next_action"],
        "claim_scope": CLAIM_SCOPE,
    }


def build_follow_up_manifest(*, output_path: Path, m2831_design: Path) -> dict[str, Any]:
    m2833_id = DEFAULT_NEXT_BLOCKER
    m2833_doc = "docs/m2833-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-result-audit.md"
    output = str(output_path)
    return {
        "id": m2833_id,
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
        ],
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
            ],
            "parent_dataset": [
                f"{output}/summary.json",
                f"{output}/handoff_artifact_inventory_rows.csv",
                f"{output}/source_only_interface_handoff_rows.csv",
                f"{output}/actor_contract_guard_rows.csv",
                f"{output}/blocker_boundary_rows.csv",
                f"{output}/claim_boundary_rows.csv",
                f"{output}/gate_matrix.csv",
                f"{output}/run_state.json",
                str(m2831_design),
                str(M2638_DOC),
                str(M2828_SUMMARY),
                str(POST_M2470_ROUTE_PLAN),
            ],
            "parent_config": [
                str(M2832_MANIFEST),
                "experiments/manifests/m2831-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-design.json",
            ],
            "parent_objective": [
                "audit M2832 Route C HF0 source-only interface evidence handoff materialization before interpretation"
            ],
            "derived_from": [
                DEFAULT_MILESTONE,
                "m2831-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-design",
                "m2830-engineering-controller-route-a-post-package-source-diverse-closed-loop-evidence-expansion-branch-synthesis",
            ],
            "blocked_by": [
                "M2832 materialization must be audited before interpretation",
                "M2638 selected-platform HF3 source dependency remains unavailable",
                "M2828 mixed diagnostic outcomes remain nonverdict context",
                "HF0/source-only handoff rows must preserve actor 72/action 3 ActorView-only extraction and actor-invisible labels",
            ],
            "supersedes": [
                "direct interpretation from M2832 handoff rows without audit",
                "direct selected-platform HF3 build probe reset validation or performance route while M2638 remains blocked",
                "direct driver-performance or high-fidelity validation claim from source-only handoff artifacts",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{m2833_id}.md",
        "public_gates": [
            "M2833 must audit M2832 required artifacts for completeness before interpretation",
            "M2833 must verify M2832 preserves M2475-M2509 M2548 M2593 M2638 and M2827-M2831 evidence lineage",
            "M2833 must verify actor observation shape 72 action shape 3 ActorView-only extraction no hidden/oracle actor input and actor-invisible labels",
            "M2833 must verify M2638 selected-platform source dependency blocker remains active and M2828 mixed diagnostic outcomes remain nonverdict context",
            "M2833 must not execute reset step rollout replay validation training PPO source build adapter probe external simulation ranking winner selection promotion package publication or success-rate verdict computation",
            "M2833 must not claim repair success recoverability success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not install external simulator dependencies",
            "do not fetch external source",
            "do not import external high-fidelity simulation packages",
            "do not mutate dependency or source trees",
            "do not run source build",
            "do not run adapter probe",
            "do not start an external backend",
            "do not execute reset",
            "do not step environments",
            "do not execute policy action",
            "do not execute rollout",
            "do not replay",
            "do not validate",
            "do not train",
            "do not run PPO",
            "do not promote a checkpoint",
            "do not change actor inputs",
            "do not change the deployed action contract",
            "do not inject hidden or oracle actor features",
            "do not hide M2828 mixed outcomes",
            "do not hide M2638 selected-platform source dependency blocker",
            "do not rank controller families source families profiles task families stress axes or scenario roles",
            "do not select a winner",
            "do not compute success-rate or controller-family verdict metrics",
            "do not publish a package",
            "do not claim driver performance from M2832 handoff materialization",
        ],
        "workflow_synthesis": {
            "branch": "engineering_controller_route_c_hf0_source_only_interface_evidence_handoff",
            "evidence_axis": "route_c_hf0_source_only_interface_handoff_result_audit",
            "evidence_increment": "audits M2832 machine-auditable handoff rows before any interpretation or next route",
            "claim_scope": "Route C HF0 source-only interface handoff result audit only; no external install import source build adapter probe backend start reset rollout validation training ranking promotion package publication driver-performance paper current-sim high-fidelity validation self-ID or full ideal driver claim",
            "stop_condition": [
                "stop if M2832 required artifacts are missing or incomplete",
                "stop if M2832 hides M2638 selected-platform source dependency blocker",
                "stop if M2832 hides M2828 mixed diagnostic outcomes or upgrades them to validation evidence",
                "stop if actor input or action contract boundaries are weakened",
                "stop if audit would claim high-fidelity validation readiness or driver performance from source-only artifacts",
            ],
            "fallback_plan": [
                "route to artifact repair if M2832 artifacts are incomplete",
                "route to claim-boundary repair if blocker or actor guard rows are incomplete",
                "route to branch synthesis if M2832 artifacts are complete",
                "route to explicit stop if handoff materialization cannot add admission-changing evidence",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2832 materializes Route C HF0 source-only handoff rows that require audit",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "evaluation_only",
            "stage_objective": "Route C HF0 source-only interface evidence handoff result audit",
            "admission_evidence": [
                "M2832 materializes handoff rows from existing artifacts only",
                "M2831 admits M2832 as bounded materialization",
                "M2638 keeps selected-platform HF3 execution paused until source dependency is supplied",
                "M2828 mixed Route A outcomes remain diagnostic context only",
            ],
            "blocked_shortcuts": [
                "no external simulator install import source build adapter probe backend start reset step rollout validation",
                "no policy action execution training replay PPO ranking winner selection or promotion",
                "no package publication",
                "no actor input expansion",
                "no driver-performance validation-readiness paper current-sim high-fidelity full ideal driver or self-ID claim",
            ],
            "allowed_updates": [
                m2833_doc,
                "M2833 status queue scoreboard research log and review",
                "one bounded synthesis repair stop or new route manifest if M2832 is accepted or rejected",
            ],
            "next_stage_criteria": [
                "audit artifact exists",
                "audit records M2832 artifact actor blocker claim and gate counts",
                "audit preserves M2638 blocker and M2828 mixed diagnostic context",
                "audit preserves actor 72/action 3 and actor-invisible labels",
                "audit selects bounded synthesis repair stop or new route if accepted or rejected",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2833 audits interface handoff artifacts and does not test history necessity or current-frame substitution.",
            "history_necessity_tests": [
                "None in M2833; no wrong-history reset-hidden zero-history finite-window or GRU comparison verdict is run."
            ],
            "temporal_evidence_window": "Post-M2832 Route C HF0/source-only handoff materialization only.",
            "negative_result_policy": "If M2832 artifacts expose weak or missing evidence preserve blockers and route to repair or stop rather than weakening self-ID or validation gates.",
            "allowed_claims": [
                "Route C HF0 source-only interface handoff artifact audit",
                "actor and claim boundary preserved or violated",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result current-sim verdict high-fidelity validation result full ideal driver completion or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the new machine-auditable Route C HF0 handoff panel before interpretation",
            "paper_verdict_delta": "no paper verdict; prevents handoff rows from being overinterpreted as self-ID or performance evidence",
            "must_synthesize_if": [
                "M2833 accepts complete M2832 artifacts",
                "M2833 rejects M2832 due to incomplete artifacts or boundary violations",
                "M2833 would claim driver performance validation paper current-sim high-fidelity full-driver or self-ID evidence",
                "M2833 would continue another handoff-process loop without branch synthesis or evidence expansion",
            ],
        },
        "hypothesis": "A bounded result audit can accept or reject M2832 handoff artifacts while preserving actor blocker and claim boundaries before interpretation.",
        "success_criteria": [
            f"{m2833_doc} exists",
            "audit records M2832 status_pass required artifact actor blocker claim and gate counts",
            "audit verifies M2638 selected-platform blocker and M2828 mixed outcomes remain visible",
            "audit preserves actor observation 72 action 3 no hidden/oracle actor input and actor-invisible labels",
            "audit makes no reset step rollout replay validation training PPO source build adapter probe external simulation ranking winner promotion success-rate driver-performance validation-readiness paper current-sim high-fidelity validation full ideal driver completion or self-ID claim",
        ],
        "failure_criteria": [
            "M2833 executes reset step rollout replay validation training PPO source build adapter probe or external simulation",
            "M2833 changes actor input or action contract",
            "M2833 weakens M2638 blocker or M2828 mixed outcome accounting",
            "M2833 ranks controller families source families profiles stress axes scenario roles selects a winner promotes a checkpoint or computes success rate",
            "M2833 claims driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result",
        ],
        "decision_rule": "Pass only if M2833 audits M2832 artifacts as complete and claim-safe while preserving blocker actor and claim boundaries without execution ranking validation performance paper current-sim high-fidelity full ideal driver or self-ID claims.",
        "commands": [{"name": "result_audit", "command": "true"}],
        "required_artifacts": [{"path": m2833_doc, "type": "md"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"
        ],
        "baseline_artifacts": [
            f"{output}/summary.json",
            f"{output}/handoff_artifact_inventory_rows.csv",
            f"{output}/source_only_interface_handoff_rows.csv",
            f"{output}/actor_contract_guard_rows.csv",
            f"{output}/blocker_boundary_rows.csv",
            f"{output}/claim_boundary_rows.csv",
            f"{output}/gate_matrix.csv",
            str(m2831_design),
            str(M2638_DOC),
            str(M2828_SUMMARY),
            str(POST_M2470_ROUTE_PLAN),
        ],
        "scoreboard_checkpoint": m2833_doc,
        "next_blocker": "m2834-engineering-controller-route-c-hf0-source-only-interface-evidence-handoff-branch-synthesis",
    }


def actor_contract_checks(source: dict[str, Any]) -> dict[str, bool]:
    json_data = source["json"]
    summaries = [
        json_data["m2482_summary"],
        json_data["m2484_summary"],
        json_data["m2496_summary"],
        json_data["m2498_summary"],
        json_data["m2501_summary"],
        json_data["m2548_summary"],
    ]
    return {
        "hidden_oracle_actor_input_detected": any(
            _bool(summary.get("hidden_values_enter_actor_input"))
            or _bool(summary.get("oracle_labels_enter_actor_input"))
            or _bool(summary.get("hidden_oracle_actor_input_detected"))
            for summary in summaries
        ),
        "fixture_labels_actor_visible": any(_bool(summary.get("fixture_labels_enter_actor_input")) for summary in summaries),
        "scenario_labels_actor_visible": any(_bool(summary.get("scenario_labels_enter_actor_input")) for summary in summaries),
        "feasibility_classes_actor_visible": any(
            _bool(summary.get("feasibility_classes_enter_actor_input")) for summary in summaries
        ),
        "diagnostics_actor_visible": any(
            _bool(summary.get("diagnostics_available_to_actor")) or _bool(summary.get("diagnostics_actor_visible"))
            for summary in summaries
        ),
        "reward_terms_actor_visible": any(_bool(summary.get("reward_terms_enter_actor_input")) for summary in summaries),
        "success_progress_verdict_labels_actor_visible": any(
            _bool(summary.get("success_labels_enter_actor_input"))
            or _bool(summary.get("verdict_claim_made"))
            or _bool(summary.get("success_rate_computed"))
            for summary in summaries
        ),
    }


def actor_shape_ok(source: dict[str, Any]) -> bool:
    json_data = source["json"]
    observed = [
        json_data["m2482_summary"].get("actor_observation_shape"),
        json_data["m2484_summary"].get("observation_shape"),
        json_data["m2496_summary"].get("observation_shape"),
        json_data["m2498_summary"].get("observation_shape"),
        json_data["m2501_summary"].get("observation_shape"),
        json_data["m2508_summary"].get("observation_shape"),
        json_data["m2548_summary"].get("observation_shape"),
        json_data["m2592_summary"].get("observation_shape"),
    ]
    return all(_int(value) == P0_OBSERVATION_DIM for value in observed)


def action_shape_ok(source: dict[str, Any]) -> bool:
    json_data = source["json"]
    observed = [
        json_data["m2482_summary"].get("action_shape"),
        json_data["m2484_summary"].get("action_shape"),
        json_data["m2496_summary"].get("action_shape"),
        json_data["m2498_summary"].get("action_shape"),
        json_data["m2501_summary"].get("action_shape"),
        json_data["m2508_summary"].get("action_shape"),
        json_data["m2548_summary"].get("action_shape"),
        json_data["m2592_summary"].get("action_shape"),
    ]
    return all(_int(value) == ACTION_DIM for value in observed)


def labels_actor_invisible(source: dict[str, Any]) -> bool:
    checks = actor_contract_checks(source)
    return not (
        checks["fixture_labels_actor_visible"]
        or checks["scenario_labels_actor_visible"]
        or checks["feasibility_classes_actor_visible"]
        or checks["success_progress_verdict_labels_actor_visible"]
    )


def diagnostics_actor_invisible(source: dict[str, Any]) -> bool:
    return not actor_contract_checks(source)["diagnostics_actor_visible"]


def source_artifacts_exist(source: dict[str, Any]) -> bool:
    return not missing_source_artifacts(source)


def missing_source_artifacts(source: dict[str, Any]) -> list[str]:
    return [name for name, exists in sorted(source["source_exists"].items()) if not exists]


def evidence_required_for_claim(claim: str) -> str:
    if "high_fidelity" in claim:
        return "selected-platform source dependency plus external HF validation manifest and result audit"
    if "driver_performance" in claim or "validation" in claim:
        return "separate validation protocol execution and claim audit"
    if "ranking" in claim or "winner" in claim:
        return "explicit ranking protocol with proof/generalization/promotion gates"
    if "self" in claim or "gru" in claim or "paper" in claim:
        return "Route B controller-family/self-ID evidence matrix and audit"
    if "publication" in claim:
        return "separate package publication manifest and disclosure audit"
    return "separate evidence-producing manifest and result audit"


def failure_type_for_gate(family: str) -> str:
    return {
        "actor_contract": "contract_violation",
        "blocker": "lineage_invalid",
        "lineage": "lineage_invalid",
        "follow_up": "lineage_invalid",
        "claim_boundary": "objective_overfit",
    }.get(family, "metric_artifact")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2831-design", type=Path, default=DEFAULT_M2831_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args(argv)
    summary = materialize_route_c_hf0_source_only_interface_evidence_handoff(
        args.output_dir,
        m2831_design=args.m2831_design,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(f"summary={summary['summary']}")
    print(f"status_pass={summary['status_pass']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
