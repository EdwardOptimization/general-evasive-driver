"""Audit M2908 source-acquisition execution results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MILESTONE_ID = (
    "m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-acquisition-execution-result-audit"
)
M2908_ID = (
    "m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-acquisition-execution-preflight"
)
NEXT_ID = (
    "m2910-paper-route-l0-l1-l2-l3-capability-prediction-post-source-"
    "acquisition-continuation-or-pivot-synthesis"
)
DEFAULT_M2908_DIR = Path(
    "runs/m2908_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_source_acquisition_execution_preflight"
)
DEFAULT_M2908_SUMMARY = DEFAULT_M2908_DIR / "summary.json"
DEFAULT_OUTPUT_DOC = Path(
    "docs/m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-"
    "diverse-panel-source-acquisition-execution-result-audit.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2910-paper-route-l0-l1-l2-l3-capability-prediction-"
    "post-source-acquisition-continuation-or-pivot-synthesis.json"
)
CLAIM_SCOPE = (
    "source_acquisition_execution_result_audit_only_no_validation_no_model_quality_"
    "no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_validation_not_paper_proof_not_model_quality_not_driver_performance_"
    "not_current_sim_not_high_fidelity_not_full_driver_not_finite_window_vs_gru_"
    "not_self_id"
)
REQUIRED_ARTIFACT_KEYS = (
    "source_acquisition_input_rows",
    "execution_resolution_rows",
    "source_acquisition_execution_rows",
    "acquisition_failure_rows",
    "candidate_support_evidence_rows",
    "source_family_evidence_rows",
    "repaired_candidate_projection_rows",
    "split_boundary_rows",
    "target_boundary_rows",
    "actor_contract_rows",
    "claim_rows",
    "gate_rows",
    "run_state",
)
CSV_ARTIFACT_KEYS = tuple(key for key in REQUIRED_ARTIFACT_KEYS if key != "run_state")
EXPECTED_INPUT_ROW_COUNT = 34
EXPECTED_CANDIDATE_SUPPORT_EVIDENCE_ADDED = 24
EXPECTED_SOURCE_FAMILY_EVIDENCE_ADDED = 0
EXPECTED_REPAIRED_PROJECTIONS = 17


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


def _all_false(rows: Iterable[dict[str, str]], fields: Iterable[str]) -> bool:
    return all(not _bool(row.get(field)) for row in rows for field in fields)


def _count_status(rows: Iterable[dict[str, str]], key: str = "status_pass") -> Counter[str]:
    return Counter(str(row.get(key, "")) for row in rows)


def _path_from_summary(summary: dict[str, Any], key: str, m2908_dir: Path) -> Path:
    artifacts = summary.get("artifacts", {})
    if isinstance(artifacts, dict) and key in artifacts:
        return Path(str(artifacts[key]))
    filename = {
        "source_acquisition_input_rows": "source_acquisition_input_rows.csv",
        "execution_resolution_rows": "execution_resolution_rows.csv",
        "source_acquisition_execution_rows": "source_acquisition_execution_rows.csv",
        "acquisition_failure_rows": "acquisition_failure_rows.csv",
        "candidate_support_evidence_rows": "candidate_support_evidence_rows.csv",
        "source_family_evidence_rows": "source_family_evidence_rows.csv",
        "repaired_candidate_projection_rows": "repaired_candidate_projection_rows.csv",
        "split_boundary_rows": "split_boundary_rows.csv",
        "target_boundary_rows": "target_boundary_rows.csv",
        "actor_contract_rows": "actor_contract_rows.csv",
        "claim_rows": "claim_rows.csv",
        "gate_rows": "gate_rows.csv",
        "run_state": "run_state.json",
    }[key]
    return m2908_dir / filename


def _artifact_paths(summary: dict[str, Any], m2908_dir: Path) -> dict[str, Path]:
    return {key: _path_from_summary(summary, key, m2908_dir) for key in REQUIRED_ARTIFACT_KEYS}


def _forbidden_summary_clear(summary: dict[str, Any]) -> bool:
    return (
        _bool(summary.get("status_pass"))
        and _bool(summary.get("gate_matrix_pass"))
        and _bool(summary.get("actor_contract_shape_72_action_3"))
        and not _bool(summary.get("hidden_oracle_actor_input_required"))
        and not _bool(summary.get("future_target_actor_input_required"))
        and not _bool(summary.get("evaluator_targets_actor_visible"))
        and not _bool(summary.get("paper_holdout_admitted"))
        and _bool(summary.get("preflight_only_split"))
        and not _bool(summary.get("source_acquisition_rows_paper_proof_allowed"))
        and not _bool(summary.get("source_acquisition_rows_validation_denominator_allowed"))
        and not _bool(summary.get("source_acquisition_rows_ordinary_success_denominator_allowed"))
        and not _bool(summary.get("ranking_run"))
        and not _bool(summary.get("winner_selected"))
        and not _bool(summary.get("checkpoint_promoted"))
        and not _bool(summary.get("model_quality_claim_made"))
        and not _bool(summary.get("paper_claim_made"))
        and not _bool(summary.get("finite_window_vs_gru_claim_made"))
        and not _bool(summary.get("level3_self_id_claim_made"))
        and not _bool(summary.get("driver_performance_claim_made"))
        and not _bool(summary.get("current_sim_verdict_claim_made"))
        and not _bool(summary.get("high_fidelity_validation_claim_made"))
        and not _bool(summary.get("full_ideal_driver_gate_passed"))
    )


def audit_m2908_artifacts(
    *,
    m2908_summary: Path,
    m2908_dir: Path,
) -> dict[str, Any]:
    summary = _read_json(m2908_summary)
    paths = _artifact_paths(summary, m2908_dir)
    artifact_exists = {key: path.exists() for key, path in paths.items()}

    rows_by_key: dict[str, list[dict[str, str]]] = {}
    for key in CSV_ARTIFACT_KEYS:
        rows_by_key[key] = _read_csv_rows(paths[key]) if paths[key].exists() else []

    input_rows = rows_by_key["source_acquisition_input_rows"]
    resolution_rows = rows_by_key["execution_resolution_rows"]
    execution_rows = rows_by_key["source_acquisition_execution_rows"]
    failure_rows = rows_by_key["acquisition_failure_rows"]
    candidate_rows = rows_by_key["candidate_support_evidence_rows"]
    source_rows = rows_by_key["source_family_evidence_rows"]
    projection_rows = rows_by_key["repaired_candidate_projection_rows"]
    split_rows = rows_by_key["split_boundary_rows"]
    target_rows = rows_by_key["target_boundary_rows"]
    actor_rows = rows_by_key["actor_contract_rows"]
    claim_rows = rows_by_key["claim_rows"]
    gate_rows = rows_by_key["gate_rows"]

    summary_row_counts = summary.get("row_counts", {})
    observed_row_counts = {key: len(rows_by_key[key]) for key in CSV_ARTIFACT_KEYS}
    row_count_matches = {
        key: observed_row_counts[key] == _int(summary_row_counts.get(key))
        for key in CSV_ARTIFACT_KEYS
    }
    summary_count_matches = {
        "fixed_m2905_acquisition_required_row_count": len(input_rows)
        == _int(summary.get("fixed_m2905_acquisition_required_row_count")),
        "source_acquisition_execution_row_count": len(execution_rows)
        == _int(summary.get("source_acquisition_execution_row_count")),
        "acquisition_failure_row_count": len(failure_rows)
        == _int(summary.get("acquisition_failure_row_count")),
        "candidate_support_required_count": len(candidate_rows)
        == _int(summary.get("candidate_support_required_count")),
        "source_family_required_count": len(source_rows)
        == _int(summary.get("source_family_required_count")),
        "repaired_candidate_projection_count": len(projection_rows)
        == _int(summary.get("repaired_candidate_projection_count")),
    }

    fixed_surface_preserved = (
        len(input_rows) == EXPECTED_INPUT_ROW_COUNT
        and len(resolution_rows) == EXPECTED_INPUT_ROW_COUNT
        and _int(summary.get("fixed_m2905_acquisition_required_row_count")) == EXPECTED_INPUT_ROW_COUNT
        and _int(summary.get("accounted_acquisition_row_count"))
        == len(execution_rows) + len(failure_rows)
    )
    execution_accounted = (
        len(execution_rows) + len(failure_rows) == len(input_rows)
        and _int(summary.get("source_acquisition_execution_row_count")) == len(execution_rows)
        and bool(execution_rows)
        and _bool(summary.get("all_selected_metrics_finite"))
    )
    candidate_support_preserved = (
        len(candidate_rows) == EXPECTED_CANDIDATE_SUPPORT_EVIDENCE_ADDED
        and _int(summary.get("candidate_support_evidence_added_count"))
        == EXPECTED_CANDIDATE_SUPPORT_EVIDENCE_ADDED
        and all(_bool(row.get("candidate_support_satisfied_after_acquisition")) for row in candidate_rows)
        and all(_int(row.get("added_candidate_artifact_count")) == 1 for row in candidate_rows)
    )
    source_family_preserved = (
        len(source_rows) == 17
        and _int(summary.get("independent_source_family_evidence_added_count"))
        == EXPECTED_SOURCE_FAMILY_EVIDENCE_ADDED
        and all(not _bool(row.get("independent_source_family_evidence_added")) for row in source_rows)
        and all(not _bool(row.get("source_family_satisfied_after_acquisition")) for row in source_rows)
        and Counter(row.get("source_family_evidence_rejection_reason", "") for row in source_rows)
        == Counter({"same_executable_source_family_not_independent": 17})
    )
    projection_result_preserved = (
        len(projection_rows) == EXPECTED_REPAIRED_PROJECTIONS
        and _int(summary.get("repaired_candidate_projection_count")) == EXPECTED_REPAIRED_PROJECTIONS
        and not _bool(summary.get("projected_design_targets_satisfied"))
        and _int(summary.get("projected_fresh_candidate_task_count")) == EXPECTED_REPAIRED_PROJECTIONS
        and _int(summary.get("projected_fresh_candidate_profile_task_count")) == 204
        and _int(summary.get("projected_target_family_coverage_count")) == 5
    )
    gate_rows_pass = bool(gate_rows) and all(_bool(row.get("status_pass")) for row in gate_rows)
    actor_contract_pass = bool(actor_rows) and all(_bool(row.get("status_pass")) for row in actor_rows)
    claim_boundary_pass = bool(claim_rows) and _all_false(claim_rows, ("claim_made", "claim_allowed"))
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
    execution_boundary_pass = _all_false(
        execution_rows + failure_rows + projection_rows,
        (
            "paper_proof_allowed",
            "validation_denominator_allowed",
            "ordinary_success_denominator_allowed",
            "ranking_run",
            "model_quality_claim_made",
            "paper_claim_made",
            "finite_window_vs_gru_claim_made",
            "level3_self_id_claim_made",
            "driver_performance_claim_made",
            "current_sim_verdict_claim_made",
            "high_fidelity_validation_claim_made",
            "full_ideal_driver_gate_passed",
        ),
    )

    audit_gates = {
        "artifact_paths_exist": all(artifact_exists.values()),
        "row_counts_match_summary": all(row_count_matches.values()),
        "summary_counts_match_rows": all(summary_count_matches.values()),
        "m2908_gate_rows_pass": gate_rows_pass,
        "fixed_m2905_surface_preserved": fixed_surface_preserved,
        "execution_accounted": execution_accounted,
        "candidate_support_result_preserved": candidate_support_preserved,
        "source_family_insufficiency_preserved": source_family_preserved,
        "partial_projection_result_preserved": projection_result_preserved,
        "split_boundary_pass": split_boundary_pass,
        "target_boundary_pass": target_boundary_pass,
        "actor_contract_pass": actor_contract_pass,
        "claim_boundary_pass": claim_boundary_pass,
        "execution_boundary_pass": execution_boundary_pass,
        "summary_boundary_pass": _forbidden_summary_clear(summary),
    }
    status_pass = all(audit_gates.values())
    decision = (
        "accept_m2908_source_acquisition_execution_claim_safe_partial_candidate_support_source_family_insufficient_route_to_m2910_continuation_or_pivot_synthesis"
        if status_pass
        else "reject_m2908_source_acquisition_execution_result_audit_route_to_manual_repair"
    )
    return {
        "milestone": MILESTONE_ID,
        "m2908_summary": str(m2908_summary),
        "m2908_dir": str(m2908_dir),
        "status_pass": status_pass,
        "decision": decision,
        "audit_gates": audit_gates,
        "artifact_exists": artifact_exists,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "summary": summary,
        "observed_row_counts": observed_row_counts,
        "summary_row_counts": summary_row_counts,
        "row_count_matches": row_count_matches,
        "summary_count_matches": summary_count_matches,
        "gate_status_counts": dict(_count_status(gate_rows)),
        "actor_status_counts": dict(_count_status(actor_rows)),
        "candidate_support_evidence_added_count": sum(
            _int(row.get("added_candidate_artifact_count")) for row in candidate_rows
        ),
        "independent_source_family_evidence_added_count": sum(
            _int(row.get("added_source_family_tag_count")) for row in source_rows
        ),
        "source_family_rejection_counts": dict(
            Counter(row.get("source_family_evidence_rejection_reason", "") for row in source_rows)
        ),
        "projection_row_count": len(projection_rows),
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
            "A bounded synthesis gate can decide whether Route B should pursue "
            "independent source-family acquisition, pivot to Route A or Route C, "
            "or stop after M2909 preserves M2908 partial candidate-support but "
            "source-family-insufficient execution evidence."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                audit_payload["m2908_summary"],
                audit_payload["artifact_paths"]["source_acquisition_execution_rows"],
                audit_payload["artifact_paths"]["candidate_support_evidence_rows"],
                audit_payload["artifact_paths"]["source_family_evidence_rows"],
                audit_payload["artifact_paths"]["repaired_candidate_projection_rows"],
                str(audit_doc),
                "docs/post-m2470-route-plan.md",
            ],
            "parent_config": [
                "experiments/manifests/m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-result-audit.json",
                "experiments/manifests/m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight.json",
                "experiments/manifests/m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis.json",
            ],
            "parent_objective": [
                "choose whether partial candidate-support acquisition can continue through independent source-family acquisition or must pivot/stop"
            ],
            "derived_from": [
                MILESTONE_ID,
                M2908_ID,
                "m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis",
                "docs/post-m2470-route-plan.md",
            ],
            "blocked_by": [
                "M2908 adds candidate-support evidence but zero independent source-family evidence",
                "M2908 projects only 17 repaired candidates with 204 profile tasks and 5 target families below Route B design targets",
                "same-family execution cannot be reinterpreted as independent source-family acquisition",
            ],
            "supersedes": [
                "another same-family source-acquisition execution loop",
                "direct model-quality validation from partial acquisition evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2910 must synthesize the accepted M2908/M2909 partial acquisition result",
            "M2910 must choose exactly one next route: independent source-family acquisition, Route A pivot, Route C pivot, or stop",
            "M2910 must not admit another same-family execution loop as source-family repair",
            "M2910 must preserve actor 72/action 3 and evaluator-only target boundaries",
            "M2910 must keep acquisition-required rows out of validation paper proof and ordinary denominators",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not train replay run PPO validate rank promote publish or select a winner",
            "do not change actor input or action contract",
            "do not expose hidden dynamics oracle labels future targets route labels success labels diagnostics or verdict labels to actor input",
            "do not reinterpret same-family execution as independent source-family evidence",
            "do not downgrade source-diversity or target coverage thresholds to force Route B readiness",
            "do not claim model quality driver performance paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
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
            "evidence_axis": "post_source_acquisition_continuation_or_pivot_synthesis",
            "evidence_increment": "forces route synthesis after M2908 creates partial candidate-support evidence but no independent source-family evidence",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if no independent source-family acquisition path exists",
                "stop if the next action would repeat same-family source execution",
                "stop if source-diversity or target coverage thresholds would be weakened",
                "stop if acquisition rows would enter validation paper proof or ordinary denominators",
                "stop if model-quality driver-performance paper current-sim high-fidelity full-driver or self-ID evidence would be claimed",
            ],
            "fallback_plan": [
                "route to Route A engineering controller evidence if Route B remains source-insufficient",
                "route to Route C high-fidelity interface preparation only if source availability changes",
                "write a stop decision if no actor-safe evidence-producing next action remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2909 accepts M2908 as claim-safe but Route B design targets remain unsatisfied",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B post-source-acquisition continuation or pivot synthesis",
            "admission_evidence": [
                "M2909 accepts M2908 as complete and claim-safe",
                "M2908 executes 34 acquisition-required rows and adds 24 candidate-support artifacts",
                "M2908 adds zero independent source-family evidence and leaves design targets unsatisfied",
            ],
            "blocked_shortcuts": [
                "no validation ranking promotion",
                "no training replay PPO or promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no same-family execution as independent source-family proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2910 status queue scoreboard research log and review",
                "one bounded follow-up source acquisition Route A Route C or stop manifest",
            ],
            "next_stage_criteria": [
                "M2910 chooses exactly one next route",
                "the chosen route can change evidence or explicitly stops/pivots",
                "target actor split holdout and exclusion boundaries remain preserved",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": (
                "M2910 is a synthesis gate and cannot substitute partial acquisition "
                "rows for history-necessity or self-ID evidence."
            ),
            "history_necessity_tests": [
                "None in M2910; later evidence requires accepted source-diverse panel data and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": (
                "M2884-M2909 Route B capability-prediction fresh-panel design, "
                "materialization, repair, source-acquisition execution, and audit chain."
            ),
            "negative_result_policy": (
                "Preserve source-family insufficiency and choose independent acquisition, "
                "pivot, or stop rather than weakening self-ID gates."
            ),
            "allowed_claims": [
                "bounded route synthesis outcome",
                "M2908/M2909 preserve partial candidate-support acquisition and source-family insufficiency",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "synthesis_decision",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "forces route synthesis after partial source acquisition cannot satisfy source-family gates",
            "paper_verdict_delta": "no verdict; may choose independent acquisition pivot or stop Route B",
            "must_synthesize_if": [
                "M2910 cannot choose independent source-family acquisition Route A pivot Route C pivot or stop",
                "M2910 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2910 would let acquisition-required rows enter paper proof",
                "M2910 would expose evaluator-only future targets to actor input",
                "another same-family execution loop is proposed as source-family acquisition",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "synthesis summarizes M2908/M2909 partial source-acquisition result",
            "synthesis chooses exactly one independent acquisition pivot or stop route",
            "synthesis preserves source-diversity thresholds and exclusion boundaries",
            "no validation ranking promotion performance paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2910 adds another same-family execution milestone as source-family repair",
            "M2910 weakens source-diversity or target-coverage thresholds to force a pass",
            "M2910 treats acquisition-required rows as proof or denominators",
            "M2910 claims driver performance model quality paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2910 fails to select one bounded next route or stop decision",
        ],
        "decision_rule": (
            "Pass only if M2910 makes a bounded route decision after the accepted "
            "partial source-acquisition audit and avoids another same-family repair loop."
        ),
        "commands": [{"name": "synthesis_doc", "command": command}],
        "command": command,
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "expected_artifacts": [f"docs/{NEXT_ID}.md"],
        "baseline_checkpoints": [
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
            "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
        ],
        "baseline_artifacts": [
            audit_payload["m2908_summary"],
            audit_payload["artifact_paths"]["source_family_evidence_rows"],
            audit_payload["artifact_paths"]["repaired_candidate_projection_rows"],
            str(audit_doc),
            "docs/post-m2470-route-plan.md",
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "m2909_result": {"summary_doc": str(audit_doc), "decision": audit_payload["decision"]},
    }


def _format_mapping(mapping: dict[str, Any]) -> list[str]:
    if not mapping:
        return ["none"]
    return [f"{key}: {value}" for key, value in sorted(mapping.items())]


def render_audit_markdown(audit: dict[str, Any], *, follow_up_manifest: Path) -> str:
    summary = audit["summary"]
    lines = [
        "# M2909 Paper Route L0/L1/L2/L3 Capability-Prediction Source-Acquisition Execution Result Audit",
        "",
        "## Metadata",
        "",
        "- status: completed" if audit["status_pass"] else "- status: failed",
        f"- decision: `{audit['decision']}`",
        "- manifest: `experiments/manifests/m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-result-audit.json`",
        f"- audited M2908 summary: `{audit['m2908_summary']}`",
        f"- audited M2908 directory: `{audit['m2908_dir']}`",
        f"- follow-up manifest: `{follow_up_manifest}`",
        f"- next: `{audit['next_blocker']}`",
        "- route split plan: `docs/post-m2470-route-plan.md`",
        "",
        "## Audit Decision",
        "",
    ]
    if audit["status_pass"]:
        lines.extend(
            [
                "M2909 accepts M2908 as a complete and claim-safe source-acquisition execution preflight.",
                "",
                "The accepted result is mixed: M2908 executed all 34 fixed acquisition-required rows and added 24 candidate-support artifacts, but it added 0 independent source-family evidence because the source-family-required rows resolved to the same executable source family. It therefore projects only 17 repaired candidates and leaves Route B design targets unsatisfied.",
            ]
        )
    else:
        lines.extend(
            [
                "M2909 rejects M2908 pending repair because at least one artifact, row-count, boundary, accounting, or claim gate failed.",
                "",
                "No continuation, validation, ranking, model-quality, paper, or self-ID route is admitted from a failed audit.",
            ]
        )
    lines.extend(
        [
            "",
            "Formal decision:",
            "",
            "```text",
            audit["decision"],
            "```",
            "",
            "M2909 did not reset, step, roll out, replay, acquire new sources, fit new weights, train, validate, rank, select a winner, promote a checkpoint, publish a package, or claim model quality, driver performance, paper evidence, current-sim verdict, high-fidelity validation, full-driver completion, finite-window-vs-GRU evidence, or level3 self-identification.",
            "",
            "## M2908 Result",
            "",
            "```text",
            f"status_pass: {summary.get('status_pass')}",
            f"gate_matrix_pass: {summary.get('gate_matrix_pass')}",
            f"decision: {summary.get('decision')}",
            f"fixed acquisition rows: {summary.get('fixed_m2905_acquisition_required_row_count')}",
            f"executions: {summary.get('source_acquisition_execution_row_count')}",
            f"failures: {summary.get('acquisition_failure_row_count')}",
            f"candidate-support evidence added: {summary.get('candidate_support_evidence_added_count')}",
            f"independent source-family evidence added: {summary.get('independent_source_family_evidence_added_count')}",
            f"repaired candidate projections: {summary.get('repaired_candidate_projection_count')}",
            f"projected design targets satisfied: {summary.get('projected_design_targets_satisfied')}",
            "```",
            "",
            "## Source-Family Boundary",
            "",
            "M2908 deliberately does not count same-family execution as independent source-family evidence. This is the key negative result preserved by M2909.",
            "",
            "```text",
            *_format_mapping(audit["source_family_rejection_counts"]),
            "```",
            "",
            "## Audit Gates",
            "",
            "```text",
            *_format_mapping(audit["audit_gates"]),
            "```",
            "",
            "## Artifact Completeness",
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
            *_format_mapping(audit["observed_row_counts"]),
            "```",
            "",
            "Row-count matches summary:",
            "",
            "```text",
            *_format_mapping(audit["row_count_matches"]),
            "```",
            "",
            "## Claim Boundary",
            "",
            "```text",
            f"claim_made_count: {audit['claim_made_count']}",
            f"claim_allowed_count: {audit['claim_allowed_count']}",
            f"target_actor_visible_count: {audit['target_actor_visible_count']}",
            f"split_denominator_admitted_count: {audit['split_denominator_admitted_count']}",
            "```",
            "",
            "No validation, ranking, promotion, model-quality, paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim is made.",
            "",
            "## Next Route",
            "",
            "M2909 routes to M2910 synthesis. M2910 must decide whether there is a concrete independent source-family acquisition route; otherwise it must pivot to Route A, pivot to Route C, or stop Route B rather than repeating same-family execution.",
            "",
            "```text",
            audit["next_blocker"],
            "```",
            "",
            "## Forbidden Interpretation",
            "",
            audit["forbidden_interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_artifacts(
    *,
    m2908_summary: Path = DEFAULT_M2908_SUMMARY,
    m2908_dir: Path = DEFAULT_M2908_DIR,
    output_doc: Path = DEFAULT_OUTPUT_DOC,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    audit = audit_m2908_artifacts(m2908_summary=m2908_summary, m2908_dir=m2908_dir)
    follow_up = build_follow_up_manifest(audit_doc=output_doc, audit_payload=audit)
    _write_json(follow_up_manifest, follow_up)
    audit["follow_up_manifest"] = str(follow_up_manifest)
    audit["audit_gates"]["follow_up_manifest_registered"] = follow_up_manifest.exists()
    audit["status_pass"] = all(audit["audit_gates"].values())
    audit["decision"] = (
        "accept_m2908_source_acquisition_execution_claim_safe_partial_candidate_support_source_family_insufficient_route_to_m2910_continuation_or_pivot_synthesis"
        if audit["status_pass"]
        else "reject_m2908_source_acquisition_execution_result_audit_route_to_manual_repair"
    )
    output_doc.parent.mkdir(parents=True, exist_ok=True)
    output_doc.write_text(render_audit_markdown(audit, follow_up_manifest=follow_up_manifest), encoding="utf-8")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2908-summary", type=Path, default=DEFAULT_M2908_SUMMARY)
    parser.add_argument("--m2908-dir", type=Path, default=DEFAULT_M2908_DIR)
    parser.add_argument("--output-doc", type=Path, default=DEFAULT_OUTPUT_DOC)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    audit = write_audit_artifacts(
        m2908_summary=args.m2908_summary,
        m2908_dir=args.m2908_dir,
        output_doc=args.output_doc,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(
        "M2909 source-acquisition execution result audit: "
        f"status={audit['status_pass']} "
        f"executions={audit['summary'].get('source_acquisition_execution_row_count')} "
        f"candidate_support_added={audit['candidate_support_evidence_added_count']} "
        f"source_family_added={audit['independent_source_family_evidence_added_count']} "
        f"projections={audit['projection_row_count']} "
        f"next={audit['next_blocker']}"
    )
    return 0 if audit["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
