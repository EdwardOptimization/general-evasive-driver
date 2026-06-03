"""Known failure taxonomy materialization for engineering-controller artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = "m2510-engineering-controller-known-failure-taxonomy-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2511-engineering-controller-known-failure-taxonomy-result-audit"
FIELDNAMES = [
    "failure_id",
    "failure_category",
    "evidence_scope",
    "evidence_type",
    "source_artifact",
    "source_milestone",
    "severity",
    "known_limitation",
    "observed_evidence",
    "route_implication",
    "forbidden_interpretation",
    "source_exists",
]
M2498_SUMMARY = "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json"
M2498_PANEL = "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv"
M2501_SUMMARY = "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json"
M2501_PANEL = "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv"
M2505_SUMMARY = "public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/summary.json"
M2508_SUMMARY = "runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json"
POST_M2470_ROUTE_PLAN = "docs/post-m2470-route-plan.md"
M2507_SYNTHESIS = "docs/m2507-engineering-controller-public-benchmark-pack-branch-synthesis.md"
M2509_AUDIT = "docs/m2509-engineering-controller-runtime-inference-cost-report-result-audit.md"


@dataclass(frozen=True)
class FailureTaxonomyRow:
    failure_id: str
    failure_category: str
    evidence_scope: str
    evidence_type: str
    source_artifact: str
    source_milestone: str
    severity: str
    known_limitation: str
    observed_evidence: str
    route_implication: str
    forbidden_interpretation: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "failure_category": self.failure_category,
            "evidence_scope": self.evidence_scope,
            "evidence_type": self.evidence_type,
            "source_artifact": self.source_artifact,
            "source_milestone": self.source_milestone,
            "severity": self.severity,
            "known_limitation": self.known_limitation,
            "observed_evidence": self.observed_evidence,
            "route_implication": self.route_implication,
            "forbidden_interpretation": self.forbidden_interpretation,
            "source_exists": Path(self.source_artifact).exists(),
        }


def materialize_known_failure_taxonomy(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = _load_source_artifacts()
    rows = build_failure_taxonomy_rows(source)
    taxonomy_path = output_dir / "failure_taxonomy.csv"
    write_csv_rows(taxonomy_path, [row.to_csv_row() for row in rows], fieldnames=FIELDNAMES)
    summary = _summary(rows, source=source, taxonomy_path=taxonomy_path, milestone=milestone, next_blocker=next_blocker)
    write_json(output_dir / "summary.json", summary)
    return summary


def _load_source_artifacts() -> dict[str, Any]:
    return {
        "m2498_summary": read_json(M2498_SUMMARY),
        "m2498_panel_rows": _read_csv_rows(M2498_PANEL),
        "m2501_summary": read_json(M2501_SUMMARY),
        "m2501_panel_rows": _read_csv_rows(M2501_PANEL),
        "m2505_summary": read_json(M2505_SUMMARY),
        "m2508_summary": read_json(M2508_SUMMARY),
    }


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_failure_taxonomy_rows(source: dict[str, Any]) -> list[FailureTaxonomyRow]:
    m2498_summary = source["m2498_summary"]
    m2501_summary = source["m2501_summary"]
    m2505_summary = source["m2505_summary"]
    m2508_summary = source["m2508_summary"]
    m2498_panel_rows = source["m2498_panel_rows"]
    m2501_panel_rows = source["m2501_panel_rows"]
    max_abs_y = _max_float(row["abs_y_max"] for row in m2498_panel_rows)
    open_loop_saturation_rows = sum(
        1
        for row in m2501_panel_rows
        if row["comparison_subject_family"] == "open_loop_action"
        and float(row["saturated_action_fraction"]) > 0.0
    )

    return [
        FailureTaxonomyRow(
            failure_id="source_only_hf0_not_external_validation",
            failure_category="validation_boundary",
            evidence_scope="public_pack",
            evidence_type="known_limitation",
            source_artifact="public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/known_limitations.md",
            source_milestone="m2505",
            severity="high",
            known_limitation="The diagnostic pack uses source-only HF0 artifacts and does not include external high-fidelity validation.",
            observed_evidence=f"external_high_fidelity_simulation_included={m2505_summary['external_high_fidelity_simulation_included']}",
            route_implication="Use taxonomy as an engineering limitation until high-fidelity validation exists.",
            forbidden_interpretation="high-fidelity validation readiness",
        ),
        FailureTaxonomyRow(
            failure_id="fixed_public_fixture_scope",
            failure_category="objective_overfit",
            evidence_scope="source_only_roles",
            evidence_type="scope_limitation",
            source_artifact=M2505_SUMMARY,
            source_milestone="m2505",
            severity="medium",
            known_limitation="Role diagnostics are based on fixed public source-only fixtures.",
            observed_evidence=f"artifact_manifest_rows={m2505_summary['artifact_manifest_rows']}",
            route_implication="Avoid treating fixed-fixture telemetry as broad scenario generalization.",
            forbidden_interpretation="scenario generalization verdict",
        ),
        FailureTaxonomyRow(
            failure_id="no_success_or_outcome_semantics",
            failure_category="metric_artifact",
            evidence_scope="baseline_comparison",
            evidence_type="unsupported_metric",
            source_artifact=M2501_SUMMARY,
            source_milestone="m2501",
            severity="high",
            known_limitation="The comparison artifact does not compute success, collision, clearance, recovery-quality, or outcome verdicts.",
            observed_evidence=f"success_rate_computed={m2501_summary['success_rate_computed']}; role_subject_panel_row_count={m2501_summary['role_subject_panel_row_count']}",
            route_implication="Do not infer behavior quality from diagnostic rows.",
            forbidden_interpretation="driver performance or success-rate benchmark",
        ),
        FailureTaxonomyRow(
            failure_id="no_controller_ranking_or_winner",
            failure_category="metric_artifact",
            evidence_scope="baseline_comparison",
            evidence_type="claim_boundary",
            source_artifact=M2501_PANEL,
            source_milestone="m2501",
            severity="high",
            known_limitation="The policy, coast, and full-brake rows are diagnostic envelopes only and are not ranked.",
            observed_evidence=f"comparison_subject_count={m2501_summary['comparison_subject_count']}; ranking_run={m2501_summary['ranking_run']}; winner_selected={m2501_summary['winner_selected']}",
            route_implication="Require a separate audited ranking protocol before any winner claim.",
            forbidden_interpretation="controller-family ranking or winner selection",
        ),
        FailureTaxonomyRow(
            failure_id="self_id_and_fw_vs_gru_unsupported",
            failure_category="self_id_evidence_gap",
            evidence_scope="route_a_engineering",
            evidence_type="unsupported_claim",
            source_artifact=M2507_SYNTHESIS,
            source_milestone="m2507",
            severity="high",
            known_limitation="Route A artifacts do not test finite-window-vs-GRU, wrong-history controls, or level3 self-identification.",
            observed_evidence="M2507 rejects paper finite-window-vs-GRU and self-ID interpretations.",
            route_implication="Keep paper-route claims separate from engineering diagnostic artifacts.",
            forbidden_interpretation="finite-window-vs-GRU or level3 self-identification conclusion",
        ),
        FailureTaxonomyRow(
            failure_id="runtime_report_synthetic_observation_scope",
            failure_category="deployability_scope",
            evidence_scope="runtime_report",
            evidence_type="measurement_scope_limitation",
            source_artifact=M2508_SUMMARY,
            source_milestone="m2508",
            severity="medium",
            known_limitation="Runtime report uses seeded synthetic shape-only observations and actor-only forward timing.",
            observed_evidence=f"synthetic_observation_source={m2508_summary['synthetic_observation_source']}; measurement_row_count={m2508_summary['measurement_row_count']}",
            route_implication="Use timing as local actor inference cost, not simulator throughput or behavior quality.",
            forbidden_interpretation="deployment certification or simulator throughput",
        ),
        FailureTaxonomyRow(
            failure_id="behavior_regression_unmeasured",
            failure_category="behavior_regression",
            evidence_scope="route_a_engineering",
            evidence_type="unmeasured_behavior",
            source_artifact=M2509_AUDIT,
            source_milestone="m2509",
            severity="medium",
            known_limitation="Runtime and packaging artifacts do not measure behavior regression or outcome quality.",
            observed_evidence="M2509 accepts runtime cost only and rejects controller quality interpretation.",
            route_implication="Behavior gates require a separate rollout/outcome protocol.",
            forbidden_interpretation="behavior improvement or regression verdict",
        ),
        FailureTaxonomyRow(
            failure_id="current_sim_readiness_not_resolved",
            failure_category="scenario_sampling_failure",
            evidence_scope="post_m2470_route",
            evidence_type="route_boundary",
            source_artifact=POST_M2470_ROUTE_PLAN,
            source_milestone="post-m2470",
            severity="medium",
            known_limitation="Current-sim readiness remains a diagnostic/mining concern and is not repaired by source-only Route A artifacts.",
            observed_evidence="Route plan freezes current-sim as diagnostic/mining layer and starts parallel engineering/HF preparation.",
            route_implication="Do not treat Route A artifacts as current-sim benchmark readiness.",
            forbidden_interpretation="current-sim benchmark verdict",
        ),
        FailureTaxonomyRow(
            failure_id="large_lateral_envelope_outcome_unlabeled",
            failure_category="diagnostic_behavior_envelope",
            evidence_scope="source_only_roles",
            evidence_type="diagnostic_metric_limitation",
            source_artifact=M2498_PANEL,
            source_milestone="m2498",
            severity="medium",
            known_limitation="Source-only role telemetry exposes large lateral envelopes but has no outcome labels or success semantics.",
            observed_evidence=f"max role abs_y_max={max_abs_y:.6f}; success_rate_computed={m2498_summary['success_rate_computed']}",
            route_implication="Use lateral envelopes as diagnostic context only.",
            forbidden_interpretation="off-road, recovery, or collision verdict",
        ),
        FailureTaxonomyRow(
            failure_id="open_loop_baselines_not_controller_candidates",
            failure_category="baseline_scope",
            evidence_scope="baseline_comparison",
            evidence_type="baseline_limitation",
            source_artifact=M2501_PANEL,
            source_milestone="m2501",
            severity="low",
            known_limitation="Coast and straight-brake rows are fixed open-loop references, not controller candidates.",
            observed_evidence=f"open_loop_rows_with_saturation={open_loop_saturation_rows}; comparison_subject_count={m2501_summary['comparison_subject_count']}",
            route_implication="Keep open-loop rows as references in diagnostics, not as deployable controller families.",
            forbidden_interpretation="open-loop controller winner",
        ),
    ]


def _summary(
    rows: list[FailureTaxonomyRow],
    *,
    source: dict[str, Any],
    taxonomy_path: Path,
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    csv_rows = [row.to_csv_row() for row in rows]
    source_artifacts_exist = all(bool(row["source_exists"]) for row in csv_rows)
    missing_source_artifacts = [
        str(row["source_artifact"]) for row in csv_rows if not bool(row["source_exists"])
    ]
    m2498_summary = source["m2498_summary"]
    m2501_summary = source["m2501_summary"]
    m2508_summary = source["m2508_summary"]
    required_fields_present = all(all(field in row for field in FIELDNAMES) for row in csv_rows)
    severity_counts = Counter(str(row.severity) for row in rows)
    category_counts = Counter(str(row.failure_category) for row in rows)
    actor_contract_shape_72_action_3 = (
        int(m2498_summary["observation_shape"]) == 72
        and int(m2498_summary["action_shape"]) == 3
        and int(m2501_summary["observation_shape"]) == 72
        and int(m2501_summary["action_shape"]) == 3
        and int(m2508_summary["observation_shape"]) == 72
        and int(m2508_summary["action_shape"]) == 3
    )
    false_flags = _false_claim_flags()
    status_pass = (
        len(rows) >= 8
        and required_fields_present
        and source_artifacts_exist
        and actor_contract_shape_72_action_3
        and not any(false_flags.values())
    )
    return {
        "result_class": "engineering_controller_known_failure_taxonomy_materialization_pass"
        if status_pass
        else "engineering_controller_known_failure_taxonomy_materialization_failed",
        "status_pass": bool(status_pass),
        "taxonomy_path": str(taxonomy_path),
        "taxonomy_row_count": len(rows),
        "expected_min_taxonomy_row_count": 8,
        "required_fields": list(FIELDNAMES),
        "required_fields_present": bool(required_fields_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": missing_source_artifacts,
        "failure_categories": sorted(category_counts),
        "failure_category_counts": dict(sorted(category_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "source_only_diagnostic_scope": True,
        "milestone": str(milestone),
        "generated_at_utc": utc_timestamp(),
        "next_blocker": str(next_blocker),
        **false_flags,
    }


def _false_claim_flags() -> dict[str, bool]:
    return {
        "environment_rollout_run": False,
        "simulator_step_run": False,
        "external_high_fidelity_simulation_included": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
    }


def _max_float(values: Any) -> float:
    return max(float(value) for value in values)


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize known failure taxonomy.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = materialize_known_failure_taxonomy(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"taxonomy_row_count={summary['taxonomy_row_count']}")
    print(f"taxonomy_path={summary['taxonomy_path']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
