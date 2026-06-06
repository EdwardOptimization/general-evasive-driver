"""Audit M2902 fresh/source-diverse panel materialization results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MILESTONE_ID = (
    "m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-materialization-result-audit"
)
M2902_ID = (
    "m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-materialization-preflight"
)
NEXT_ID = (
    "m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-design"
)
DEFAULT_M2902_DIR = Path(
    "runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_materialization_preflight"
)
DEFAULT_M2902_SUMMARY = DEFAULT_M2902_DIR / "summary.json"
DEFAULT_OUTPUT_DOC = Path(
    "docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-"
    "diverse-panel-materialization-result-audit.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2904-paper-route-l0-l1-l2-l3-capability-prediction-"
    "fresh-source-diverse-panel-repair-source-acquisition-design.json"
)
CLAIM_SCOPE = (
    "preflight_accounting_only_no_validation_no_model_quality_no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_paper_proof_not_validation_not_full_driver_not_self_identification_evidence"
)
REQUIRED_ARTIFACT_KEYS = (
    "panel_row_taxonomy_rows",
    "source_diversity_rows",
    "split_contract_rows",
    "target_coverage_rows",
    "seed_gap_rows",
    "guard_exclusion_rows",
    "materialization_gate_rows",
    "rollback_rows",
    "claim_rows",
    "run_state",
)
CSV_ARTIFACT_KEYS = tuple(key for key in REQUIRED_ARTIFACT_KEYS if key != "run_state")
EXPECTED_ROW_CLASSES = (
    "public_reference_usable",
    "fresh_source_diverse_candidate",
    "source_singleton_seed",
    "fresh_panel_gap",
    "guard_exclusion",
    "rejected_boundary_violation",
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(str(value))
    except ValueError:
        return default


def _path_from_summary(summary: dict[str, Any], key: str, m2902_dir: Path) -> Path:
    artifacts = summary.get("artifacts", {})
    if isinstance(artifacts, dict) and key in artifacts:
        return Path(str(artifacts[key]))
    filename = {
        "panel_row_taxonomy_rows": "panel_row_taxonomy_rows.csv",
        "source_diversity_rows": "source_diversity_rows.csv",
        "split_contract_rows": "split_contract_rows.csv",
        "target_coverage_rows": "target_coverage_rows.csv",
        "seed_gap_rows": "seed_gap_rows.csv",
        "guard_exclusion_rows": "guard_exclusion_rows.csv",
        "materialization_gate_rows": "materialization_gate_rows.csv",
        "rollback_rows": "rollback_rows.csv",
        "claim_rows": "claim_rows.csv",
        "run_state": "run_state.json",
    }[key]
    return m2902_dir / filename


def _artifact_paths(summary: dict[str, Any], m2902_dir: Path) -> dict[str, Path]:
    return {
        key: _path_from_summary(summary, key, m2902_dir)
        for key in REQUIRED_ARTIFACT_KEYS
    }


def _count_status(rows: Iterable[dict[str, str]], key: str = "status_pass") -> Counter[str]:
    return Counter(str(row.get(key, "")) for row in rows)


def _missing_requirements(seed_rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in seed_rows:
        for item in row.get("missing_requirement", "").split(";"):
            if item:
                counts[item] += 1
    return counts


def _all_false(rows: Iterable[dict[str, str]], fields: Iterable[str]) -> bool:
    return all(not _bool(row.get(field)) for row in rows for field in fields)


def audit_m2902_artifacts(
    *,
    m2902_summary: Path,
    m2902_dir: Path,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    summary = _read_json(m2902_summary)
    paths = _artifact_paths(summary, m2902_dir)
    artifact_exists = {key: path.exists() for key, path in paths.items()}

    rows_by_key: dict[str, list[dict[str, str]]] = {}
    for key in CSV_ARTIFACT_KEYS:
        if paths[key].exists():
            rows_by_key[key] = _read_csv_rows(paths[key])
        else:
            rows_by_key[key] = []

    taxonomy_rows = rows_by_key["panel_row_taxonomy_rows"]
    diversity_rows = rows_by_key["source_diversity_rows"]
    split_rows = rows_by_key["split_contract_rows"]
    target_rows = rows_by_key["target_coverage_rows"]
    seed_rows = rows_by_key["seed_gap_rows"]
    guard_rows = rows_by_key["guard_exclusion_rows"]
    gate_rows = rows_by_key["materialization_gate_rows"]
    rollback_rows = rows_by_key["rollback_rows"]
    claim_rows = rows_by_key["claim_rows"]

    summary_row_counts = summary.get("row_counts", {})
    observed_row_counts = {key: len(rows_by_key[key]) for key in CSV_ARTIFACT_KEYS}
    row_count_matches = {
        key: observed_row_counts[key] == _int(summary_row_counts.get(key))
        for key in CSV_ARTIFACT_KEYS
    }

    row_class_counts = Counter(row.get("source_row_class", "") for row in taxonomy_rows)
    taxonomy_summary_matches = {
        "public_reference_usable_count": row_class_counts["public_reference_usable"]
        == _int(summary.get("public_reference_usable_count")),
        "fresh_candidate_task_count": row_class_counts["fresh_source_diverse_candidate"]
        == _int(summary.get("fresh_candidate_task_count")),
        "source_singleton_seed_count": row_class_counts["source_singleton_seed"]
        == _int(summary.get("source_singleton_seed_count")),
        "guard_exclusion_count": row_class_counts["guard_exclusion"]
        == _int(summary.get("guard_exclusion_count")),
        "fresh_panel_gap_count": row_class_counts["fresh_panel_gap"]
        == _int(summary.get("fresh_panel_gap_count")),
        "rejected_boundary_violation_count": row_class_counts["rejected_boundary_violation"]
        == _int(summary.get("rejected_boundary_violation_count")),
    }

    fresh_diversity_rows = [
        row for row in diversity_rows if row.get("row_class") == "fresh_source_diverse_candidate"
    ]
    fresh_diversity_row = fresh_diversity_rows[0] if fresh_diversity_rows else {}
    diversity_result_preserved = (
        not _bool(summary.get("fresh_source_diverse_targets_satisfied"))
        and not _bool(fresh_diversity_row.get("fresh_source_diverse_targets_satisfied"))
        and _int(summary.get("fresh_candidate_task_count")) == 0
        and _int(summary.get("target_family_coverage_count")) == 0
        and "insufficient_diversity" in str(summary.get("decision", ""))
    )

    gate_rows_pass = bool(gate_rows) and all(_bool(row.get("status_pass")) for row in gate_rows)
    rollback_rows_pass = bool(rollback_rows) and all(
        _bool(row.get("status_pass")) for row in rollback_rows
    )
    split_boundary_pass = bool(split_rows) and _all_false(
        split_rows,
        (
            "paper_holdout_admitted",
            "validation_denominator_allowed",
            "model_quality_denominator_allowed",
            "ordinary_success_denominator_allowed",
        ),
    )
    target_boundary_pass = bool(target_rows) and all(
        _bool(row.get("status_pass")) and not _bool(row.get("actor_visible_allowed"))
        for row in target_rows
    )
    claim_boundary_pass = bool(claim_rows) and _all_false(
        claim_rows,
        ("claim_made", "claim_allowed"),
    )
    guard_boundary_pass = bool(guard_rows) and _all_false(
        guard_rows,
        ("paper_proof_allowed", "ordinary_success_denominator_allowed"),
    )
    seed_boundary_pass = bool(seed_rows) and _all_false(
        seed_rows,
        ("paper_proof_allowed", "ordinary_success_denominator_allowed"),
    )
    summary_boundary_pass = (
        _bool(summary.get("status_pass"))
        and _bool(summary.get("gate_matrix_pass"))
        and _bool(summary.get("actor_contract_shape_72_action_3"))
        and not _bool(summary.get("hidden_oracle_actor_input_required"))
        and not _bool(summary.get("future_target_actor_input_required"))
        and not _bool(summary.get("evaluator_targets_actor_visible"))
        and not _bool(summary.get("paper_holdout_admitted"))
        and _bool(summary.get("preflight_only_split"))
        and not _bool(summary.get("model_quality_claim_made"))
        and not _bool(summary.get("paper_claim_made"))
        and not _bool(summary.get("finite_window_vs_gru_claim_made"))
        and not _bool(summary.get("level3_self_id_claim_made"))
        and not _bool(summary.get("driver_performance_claim_made"))
        and not _bool(summary.get("current_sim_verdict_claim_made"))
        and not _bool(summary.get("high_fidelity_validation_claim_made"))
        and not _bool(summary.get("full_ideal_driver_gate_passed"))
    )

    audit_gates = {
        "artifact_paths_exist": all(artifact_exists.values()),
        "row_counts_match_summary": all(row_count_matches.values()),
        "taxonomy_counts_match_summary": all(taxonomy_summary_matches.values()),
        "m2902_gate_rows_pass": gate_rows_pass,
        "m2902_rollback_rows_pass": rollback_rows_pass,
        "split_boundary_pass": split_boundary_pass,
        "target_boundary_pass": target_boundary_pass,
        "seed_boundary_pass": seed_boundary_pass,
        "guard_boundary_pass": guard_boundary_pass,
        "claim_boundary_pass": claim_boundary_pass,
        "summary_boundary_pass": summary_boundary_pass,
        "negative_diversity_result_preserved": diversity_result_preserved,
    }
    status_pass = all(audit_gates.values())
    decision = (
        "accept_m2902_materialization_claim_safe_insufficient_diversity_route_to_m2904_repair_source_acquisition_design"
        if status_pass
        else "reject_m2902_materialization_audit_route_to_manual_repair"
    )
    return {
        "milestone": MILESTONE_ID,
        "m2902_summary": str(m2902_summary),
        "m2902_dir": str(m2902_dir),
        "status_pass": status_pass,
        "decision": decision,
        "audit_gates": audit_gates,
        "artifact_exists": artifact_exists,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "summary": summary,
        "observed_row_counts": observed_row_counts,
        "summary_row_counts": summary_row_counts,
        "row_count_matches": row_count_matches,
        "row_class_counts": dict(row_class_counts),
        "taxonomy_summary_matches": taxonomy_summary_matches,
        "gate_status_counts": dict(_count_status(gate_rows)),
        "rollback_status_counts": dict(_count_status(rollback_rows)),
        "claim_made_count": sum(_bool(row.get("claim_made")) for row in claim_rows),
        "claim_allowed_count": sum(_bool(row.get("claim_allowed")) for row in claim_rows),
        "target_actor_visible_count": sum(_bool(row.get("actor_visible_allowed")) for row in target_rows),
        "split_denominator_admitted_count": sum(
            _bool(row.get("paper_holdout_admitted"))
            or _bool(row.get("validation_denominator_allowed"))
            or _bool(row.get("model_quality_denominator_allowed"))
            or _bool(row.get("ordinary_success_denominator_allowed"))
            for row in split_rows
        ),
        "seed_gap_missing_requirements": dict(_missing_requirements(seed_rows)),
        "fresh_diversity_row": fresh_diversity_row,
        "follow_up_manifest": str(follow_up_manifest),
        "next_blocker": NEXT_ID,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
    }


def build_follow_up_manifest(*, audit_doc: Path, audit_payload: dict[str, Any]) -> dict[str, Any]:
    command = "true"
    return {
        "id": NEXT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_milestone": MILESTONE_ID,
        "type": "gate",
        "gate_tier": "process",
        "status": "pending",
        "risk": "medium",
        "promotion_decision": "not_applicable",
        "hypothesis": (
            "A bounded design-only milestone can convert the accepted M2903 negative "
            "fresh/source-diverse panel audit into a source-acquisition repair plan "
            "without validation ranking model-quality paper or self-ID claims."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                audit_payload["m2902_summary"],
                audit_payload["artifact_paths"]["panel_row_taxonomy_rows"],
                audit_payload["artifact_paths"]["source_diversity_rows"],
                audit_payload["artifact_paths"]["seed_gap_rows"],
                str(audit_doc),
            ],
            "parent_config": [
                "experiments/manifests/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.json",
                "experiments/manifests/m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight.json",
            ],
            "parent_objective": [
                "design a bounded repair/source-acquisition route for zero admitted fresh/source-diverse candidates"
            ],
            "derived_from": [
                MILESTONE_ID,
                M2902_ID,
                "m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design",
            ],
            "blocked_by": [
                "M2902/M2903 found zero fresh_source_diverse_candidate rows",
                "existing source-singleton rows are seed gaps only and cannot be paper proof",
                "Route B cannot proceed to model-quality validation before fresh/source-diverse repair",
            ],
            "supersedes": [
                "direct model-quality design from the 17 public reference rows",
                "treating source-singleton rows as validation or paper denominators",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2904 must design a source-acquisition repair route for zero admitted fresh candidates",
            "M2904 must preserve M2901 source-diversity thresholds without weakening them",
            "M2904 must keep public reference source-singleton and guard rows out of validation paper proof and ordinary denominators",
            "M2904 must preserve actor 72/action 3 and evaluator-only future target boundaries",
            "M2904 must select exactly one bounded next action: repair materialization, route pivot, synthesis, or stop",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate fit train rank promote publish or select a winner",
            "do not change actor input or action contract",
            "do not expose hidden dynamics oracle labels future targets route labels or verdict labels to actor input",
            "do not downgrade source-diversity thresholds to force a pass",
            "do not treat public reference source-singleton or guard rows as model-quality or paper denominators",
            "do not claim prediction quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
        ],
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
        "workflow_synthesis": {
            "branch": "paper_route_l0_l1_l2_l3_capability_prediction_fresh_panel_expansion",
            "evidence_axis": "fresh_source_diverse_panel_repair_source_acquisition_design",
            "evidence_increment": "turns the negative M2903 audit into a bounded repair/source-acquisition design before any validation",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if the design cannot preserve source-diversity thresholds",
                "stop if the design would treat source-singleton or guard rows as proof",
                "stop if actor-visible evaluator targets or oracle labels would be required",
                "stop if another repair loop is proposed without a concrete new panel evidence path",
            ],
            "fallback_plan": [
                "pivot to Route A closed-loop evidence if Route B source acquisition is unavailable",
                "pivot to Route C only if dependency source availability changes",
                "write a stop synthesis if no claim-safe repair materialization path exists",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2903 accepts M2902 but preserves zero admitted fresh/source-diverse candidates",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B source-acquisition repair design after a negative fresh panel audit",
            "admission_evidence": [
                "M2903 accepts M2902 as complete and claim-safe while preserving zero fresh candidates",
                "M2902 writes 34 source-singleton seed-gap rows and 21 guard exclusions",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion",
                "no additional optimizer step and no promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no source-singleton or guard rows as proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2904 status queue scoreboard research log and review",
                "one bounded follow-up repair materialization synthesis pivot or stop manifest",
            ],
            "next_stage_criteria": [
                "repair/source acquisition criteria are explicit and do not weaken M2901 thresholds",
                "source-singleton seed rows are separated from proof rows",
                "one bounded materialization, synthesis, pivot, or stop route is selected",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2904 is a repair design only and cannot substitute source acquisition for history-necessity evidence.",
            "history_necessity_tests": [
                "None in M2904; later tests require accepted source-diverse panel data and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2884-M2903 Route B capability-prediction panel inventory dataset contract fitting design materialization and audit chain.",
            "negative_result_policy": "Preserve zero fresh candidates as the blocker and design repair or stop without weakening self-ID gates.",
            "allowed_claims": [
                "bounded repair/source-acquisition design outcome",
                "zero admitted fresh/source-diverse candidates remain the current Route B blocker",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "design_only",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "designs a repair path from audited seed-gap rows rather than optimizing public proof rows",
            "paper_verdict_delta": "no verdict; defines whether Route B can acquire the prerequisite panel evidence",
            "must_synthesize_if": [
                "M2904 cannot choose between repair materialization Route A pivot Route C pivot or stop",
                "M2904 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2904 would let source-singleton or guard rows enter paper proof",
                "M2904 would expose evaluator-only future targets to actor input",
                "another repair-only loop is proposed without materializing new panel evidence",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "design preserves M2901 fresh/source-diverse thresholds",
            "design separates seed-gap rows from validation paper proof and ordinary denominators",
            "design registers exactly one bounded next route or stop decision",
            "no validation ranking promotion performance paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2904 weakens source-diversity thresholds to force a pass",
            "M2904 treats public reference source-singleton or guard rows as proof or denominators",
            "M2904 admits model-quality validation without new fresh/source-diverse candidates",
            "M2904 claims driver performance model quality paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2904 fails to select one bounded next route",
        ],
        "decision_rule": (
            "Pass only if M2904 designs a claim-safe repair/source-acquisition route "
            "for the audited zero-fresh-candidate result without validation or threshold weakening."
        ),
        "commands": [{"name": "design_doc", "command": command}],
        "command": command,
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "expected_artifacts": [f"docs/{NEXT_ID}.md"],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            audit_payload["m2902_summary"],
            audit_payload["artifact_paths"]["seed_gap_rows"],
            str(audit_doc),
            "docs/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.md",
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": (
            "m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
            "panel-repair-source-acquisition-materialization-preflight"
        ),
    }


def _format_mapping(mapping: dict[str, Any]) -> list[str]:
    if not mapping:
        return ["none"]
    return [f"{key}: {value}" for key, value in sorted(mapping.items())]


def render_audit_markdown(audit: dict[str, Any], *, follow_up_manifest: Path) -> str:
    summary = audit["summary"]
    row_counts = audit["observed_row_counts"]
    row_classes = audit["row_class_counts"]
    seed_requirements = audit["seed_gap_missing_requirements"]
    decision = audit["decision"]
    lines = [
        "# M2903 Paper Route L0/L1/L2/L3 Capability-Prediction Fresh Source-Diverse Panel Materialization Result Audit",
        "",
        "## Metadata",
        "",
        "- status: completed" if audit["status_pass"] else "- status: failed",
        f"- decision: `{decision}`",
        "- manifest: `experiments/manifests/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.json`",
        f"- audited M2902 summary: `{audit['m2902_summary']}`",
        f"- audited M2902 directory: `{audit['m2902_dir']}`",
        f"- follow-up manifest: `{follow_up_manifest}`",
        f"- next: `{audit['next_blocker']}`",
        "",
        "## Audit Decision",
        "",
    ]
    if audit["status_pass"]:
        lines.extend(
            [
                "M2903 accepts M2902 as complete and claim-safe materialization-preflight evidence.",
                "",
                "The acceptance is intentionally negative with respect to fresh/source-diverse panel readiness: M2902 materialized the accounting surface, but it found zero admitted fresh/source-diverse candidates. This blocks model-quality validation and routes to source-acquisition repair design.",
            ]
        )
    else:
        lines.extend(
            [
                "M2903 rejects M2902 pending repair because at least one artifact, row-count, boundary, or claim gate failed.",
                "",
                "No downstream repair, validation, ranking, or model-quality route is admitted from a failed audit.",
            ]
        )
    lines.extend(
        [
            "",
            "Formal decision:",
            "",
            "```text",
            decision,
            "```",
            "",
            "M2903 did not reset, step, roll out, replay, fit new weights, train, validate, rank, select a winner, promote a checkpoint, publish a package, or claim model quality, driver performance, paper evidence, current-sim verdict, high-fidelity validation, full-driver completion, finite-window-vs-GRU evidence, or level3 self-identification.",
            "",
            "## Artifact Completeness",
            "",
            "M2902 summary:",
            "",
            "```text",
            f"status_pass: {summary.get('status_pass')}",
            f"gate_matrix_pass: {summary.get('gate_matrix_pass')}",
            f"decision: {summary.get('decision')}",
            f"fresh_source_diverse_targets_satisfied: {summary.get('fresh_source_diverse_targets_satisfied')}",
            "```",
            "",
            "Artifact existence gates:",
            "",
            "```text",
            *_format_mapping(audit["artifact_exists"]),
            "```",
            "",
            "Observed row counts:",
            "",
            "```text",
            *_format_mapping(row_counts),
            "```",
            "",
            "Row-count matches summary:",
            "",
            "```text",
            *_format_mapping(audit["row_count_matches"]),
            "```",
            "",
            "## Diversity Result",
            "",
            "M2903 preserves the M2902 negative diversity result exactly:",
            "",
            "```text",
            f"public_reference_usable_count: {summary.get('public_reference_usable_count')}",
            f"fresh_candidate_task_count: {summary.get('fresh_candidate_task_count')}",
            f"fresh_candidate_profile_task_count: {summary.get('fresh_candidate_profile_task_count')}",
            f"source_singleton_seed_count: {summary.get('source_singleton_seed_count')}",
            f"guard_exclusion_count: {summary.get('guard_exclusion_count')}",
            f"target_family_coverage_count: {summary.get('target_family_coverage_count')}",
            f"source_family_count: {summary.get('source_family_count')}",
            f"task_family_count: {summary.get('task_family_count')}",
            "```",
            "",
            "Taxonomy row classes:",
            "",
            "```text",
            *[f"{key}: {row_classes.get(key, 0)}" for key in EXPECTED_ROW_CLASSES],
            "```",
            "",
            "The seed-gap rows are repair inputs only:",
            "",
            "```text",
            *_format_mapping(seed_requirements),
            "```",
            "",
            "The active blocker is not row absence; it is candidate sufficiency. Existing source-singleton rows need additional candidate/source-family support before any fresh panel can be admitted.",
            "",
            "## Boundary Findings",
            "",
            "Audit gates:",
            "",
            "```text",
            *_format_mapping(audit["audit_gates"]),
            "```",
            "",
            "Boundary counters:",
            "",
            "```text",
            f"claim_made_count: {audit['claim_made_count']}",
            f"claim_allowed_count: {audit['claim_allowed_count']}",
            f"target_actor_visible_count: {audit['target_actor_visible_count']}",
            f"split_denominator_admitted_count: {audit['split_denominator_admitted_count']}",
            "```",
            "",
            "Accepted boundary state:",
            "",
            "```text",
            f"actor_contract_shape_72_action_3: {summary.get('actor_contract_shape_72_action_3')}",
            f"hidden_oracle_actor_input_required: {summary.get('hidden_oracle_actor_input_required')}",
            f"future_target_actor_input_required: {summary.get('future_target_actor_input_required')}",
            f"evaluator_targets_actor_visible: {summary.get('evaluator_targets_actor_visible')}",
            f"paper_holdout_admitted: {summary.get('paper_holdout_admitted')}",
            f"preflight_only_split: {summary.get('preflight_only_split')}",
            "```",
            "",
            "## Supported Claim",
            "",
            "M2903 supports only this bounded claim:",
            "",
            "```text",
            "M2902 produced a complete and claim-safe panel materialization accounting surface, and that surface shows the current Route B materialized panel has zero fresh/source-diverse candidate rows under the M2901 criteria.",
            "```",
            "",
            "This is repair-routing evidence, not driver evidence and not paper evidence.",
            "",
            "## Rejected Interpretations",
            "",
            "M2903 rejects these interpretations:",
            "",
            "```text",
            "fresh/source-diverse panel ready for model-quality validation: false",
            "source-singleton rows may serve as paper proof: false",
            "public reference rows may serve as validation denominator: false",
            "guard rows may enter ordinary success denominator: false",
            "validated prediction quality: false",
            "driver-performance evidence: false",
            "finite-window-vs-GRU verdict: false",
            "current-sim verdict: false",
            "high-fidelity validation readiness/result: false",
            "full ideal driver completion: false",
            "level3 self-identification evidence: false",
            "```",
            "",
            "## Follow-Up Route",
            "",
            "M2903 registers exactly one next route:",
            "",
            "```text",
            NEXT_ID,
            "```",
            "",
            "M2904 must design a repair/source-acquisition route for the zero-fresh-candidate result. It must not weaken M2901 thresholds, treat source-singleton or guard rows as proof, validate, rank, promote, claim model quality, claim driver performance, claim a finite-window-vs-GRU verdict, claim paper evidence, claim current-sim or high-fidelity evidence, or claim self-identification.",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_artifacts(
    *,
    m2902_summary: Path,
    m2902_dir: Path,
    output_doc: Path,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    audit = audit_m2902_artifacts(
        m2902_summary=m2902_summary,
        m2902_dir=m2902_dir,
        follow_up_manifest=follow_up_manifest,
    )
    output_doc.parent.mkdir(parents=True, exist_ok=True)
    output_doc.write_text(
        render_audit_markdown(audit, follow_up_manifest=follow_up_manifest),
        encoding="utf-8",
    )
    follow_up = build_follow_up_manifest(audit_doc=output_doc, audit_payload=audit)
    _write_json(follow_up_manifest, follow_up)
    audit["output_doc"] = str(output_doc)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2902-summary", type=Path, default=DEFAULT_M2902_SUMMARY)
    parser.add_argument("--m2902-dir", type=Path, default=DEFAULT_M2902_DIR)
    parser.add_argument("--output-doc", type=Path, default=DEFAULT_OUTPUT_DOC)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    audit = write_audit_artifacts(
        m2902_summary=args.m2902_summary,
        m2902_dir=args.m2902_dir,
        output_doc=args.output_doc,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
