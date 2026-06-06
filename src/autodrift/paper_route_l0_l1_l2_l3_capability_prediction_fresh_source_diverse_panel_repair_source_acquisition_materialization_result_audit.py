"""Audit M2905 repair/source-acquisition materialization results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MILESTONE_ID = (
    "m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-materialization-result-audit"
)
M2905_ID = (
    "m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-repair-source-acquisition-materialization-preflight"
)
NEXT_ID = (
    "m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-"
    "panel-source-execution-or-pivot-synthesis"
)
DEFAULT_M2905_DIR = Path(
    "runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_"
    "panel_repair_source_acquisition_materialization_preflight"
)
DEFAULT_M2905_SUMMARY = DEFAULT_M2905_DIR / "summary.json"
DEFAULT_OUTPUT_DOC = Path(
    "docs/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-"
    "diverse-panel-repair-source-acquisition-materialization-result-audit.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2907-paper-route-l0-l1-l2-l3-capability-prediction-"
    "fresh-source-diverse-panel-source-execution-or-pivot-synthesis.json"
)
CLAIM_SCOPE = (
    "repair_source_acquisition_materialization_audit_only_no_validation_no_model_"
    "quality_no_driver_performance_claim"
)
FORBIDDEN_INTERPRETATION = (
    "not_source_execution_not_validation_not_paper_proof_not_model_quality_not_driver_"
    "performance_not_self_id"
)
REQUIRED_ARTIFACT_KEYS = (
    "seed_gap_repair_rows",
    "candidate_support_repair_rows",
    "source_family_repair_rows",
    "dual_repair_rows",
    "acquisition_required_rows",
    "repaired_candidate_projection_rows",
    "exclusion_rows",
    "split_boundary_rows",
    "target_boundary_rows",
    "gate_rows",
    "rollback_rows",
    "claim_rows",
    "run_state",
)
CSV_ARTIFACT_KEYS = tuple(key for key in REQUIRED_ARTIFACT_KEYS if key != "run_state")


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


def _path_from_summary(summary: dict[str, Any], key: str, m2905_dir: Path) -> Path:
    artifacts = summary.get("artifacts", {})
    if isinstance(artifacts, dict) and key in artifacts:
        return Path(str(artifacts[key]))
    filename = {
        "seed_gap_repair_rows": "seed_gap_repair_rows.csv",
        "candidate_support_repair_rows": "candidate_support_repair_rows.csv",
        "source_family_repair_rows": "source_family_repair_rows.csv",
        "dual_repair_rows": "dual_repair_rows.csv",
        "acquisition_required_rows": "acquisition_required_rows.csv",
        "repaired_candidate_projection_rows": "repaired_candidate_projection_rows.csv",
        "exclusion_rows": "exclusion_rows.csv",
        "split_boundary_rows": "split_boundary_rows.csv",
        "target_boundary_rows": "target_boundary_rows.csv",
        "gate_rows": "gate_rows.csv",
        "rollback_rows": "rollback_rows.csv",
        "claim_rows": "claim_rows.csv",
        "run_state": "run_state.json",
    }[key]
    return m2905_dir / filename


def _artifact_paths(summary: dict[str, Any], m2905_dir: Path) -> dict[str, Path]:
    return {key: _path_from_summary(summary, key, m2905_dir) for key in REQUIRED_ARTIFACT_KEYS}


def _count_status(rows: Iterable[dict[str, str]], key: str = "status_pass") -> Counter[str]:
    return Counter(str(row.get(key, "")) for row in rows)


def _all_false(rows: Iterable[dict[str, str]], fields: Iterable[str]) -> bool:
    return all(not _bool(row.get(field)) for row in rows for field in fields)


def _missing_requirements(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for item in row.get("missing_requirement", "").split(";"):
            if item:
                counts[item] += 1
    return counts


def audit_m2905_artifacts(
    *,
    m2905_summary: Path,
    m2905_dir: Path,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    summary = _read_json(m2905_summary)
    paths = _artifact_paths(summary, m2905_dir)
    artifact_exists = {key: path.exists() for key, path in paths.items()}

    rows_by_key: dict[str, list[dict[str, str]]] = {}
    for key in CSV_ARTIFACT_KEYS:
        rows_by_key[key] = _read_csv_rows(paths[key]) if paths[key].exists() else []

    seed_rows = rows_by_key["seed_gap_repair_rows"]
    candidate_rows = rows_by_key["candidate_support_repair_rows"]
    source_rows = rows_by_key["source_family_repair_rows"]
    dual_rows = rows_by_key["dual_repair_rows"]
    acquisition_rows = rows_by_key["acquisition_required_rows"]
    projection_rows = rows_by_key["repaired_candidate_projection_rows"]
    exclusion_rows = rows_by_key["exclusion_rows"]
    split_rows = rows_by_key["split_boundary_rows"]
    target_rows = rows_by_key["target_boundary_rows"]
    gate_rows = rows_by_key["gate_rows"]
    rollback_rows = rows_by_key["rollback_rows"]
    claim_rows = rows_by_key["claim_rows"]

    summary_row_counts = summary.get("row_counts", {})
    observed_row_counts = {key: len(rows_by_key[key]) for key in CSV_ARTIFACT_KEYS}
    row_count_matches = {
        key: observed_row_counts[key] == _int(summary_row_counts.get(key))
        for key in CSV_ARTIFACT_KEYS
    }

    count_summary_matches = {
        "seed_gap_row_count": len(seed_rows) == _int(summary.get("seed_gap_row_count")),
        "candidate_support_gap_count": len(candidate_rows)
        == _int(summary.get("candidate_support_gap_count")),
        "source_family_gap_count": len(source_rows)
        == _int(summary.get("source_family_gap_count")),
        "dual_gap_count": len(dual_rows) == _int(summary.get("dual_gap_count")),
        "acquisition_required_count": len(acquisition_rows)
        == _int(summary.get("acquisition_required_count")),
        "repaired_candidate_projection_count": len(projection_rows)
        == _int(summary.get("repaired_candidate_projection_count")),
    }

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
    exclusion_boundary_pass = bool(exclusion_rows) and _all_false(
        exclusion_rows,
        (
            "paper_proof_allowed",
            "validation_denominator_allowed",
            "ordinary_success_denominator_allowed",
        ),
    )
    acquisition_boundary_pass = bool(acquisition_rows) and _all_false(
        acquisition_rows,
        (
            "paper_proof_allowed",
            "validation_denominator_allowed",
            "ordinary_success_denominator_allowed",
        ),
    )
    candidate_support_accounted = len(candidate_rows) == sum(
        _bool(row.get("candidate_support_gap")) for row in seed_rows
    )
    source_family_accounted = len(source_rows) == sum(
        _bool(row.get("source_family_gap")) for row in seed_rows
    )
    dual_accounted = len(dual_rows) == sum(_bool(row.get("dual_gap")) for row in seed_rows)
    acquisition_accounted = len(acquisition_rows) == sum(
        _bool(row.get("acquisition_required")) for row in seed_rows
    )
    negative_projection_preserved = (
        not _bool(summary.get("projected_design_targets_satisfied"))
        and len(projection_rows) == 0
        and _int(summary.get("projected_fresh_candidate_task_count")) == 0
        and _int(summary.get("projected_fresh_candidate_profile_task_count")) == 0
        and _int(summary.get("projected_source_family_count")) == 0
        and _int(summary.get("projected_task_family_count")) == 0
        and _int(summary.get("projected_target_family_coverage_count")) == 0
        and "existing_support_insufficient" in str(summary.get("decision", ""))
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
        and not _bool(summary.get("source_singleton_rows_paper_proof_allowed"))
        and not _bool(summary.get("guard_rows_ordinary_success_denominator_allowed"))
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
        "summary_counts_match_rows": all(count_summary_matches.values()),
        "m2905_gate_rows_pass": gate_rows_pass,
        "m2905_rollback_rows_pass": rollback_rows_pass,
        "split_boundary_pass": split_boundary_pass,
        "target_boundary_pass": target_boundary_pass,
        "claim_boundary_pass": claim_boundary_pass,
        "exclusion_boundary_pass": exclusion_boundary_pass,
        "acquisition_boundary_pass": acquisition_boundary_pass,
        "candidate_support_accounted": candidate_support_accounted,
        "source_family_accounted": source_family_accounted,
        "dual_repair_accounted": dual_accounted,
        "acquisition_required_accounted": acquisition_accounted,
        "negative_projection_result_preserved": negative_projection_preserved,
        "summary_boundary_pass": summary_boundary_pass,
    }
    status_pass = all(audit_gates.values())
    decision = (
        "accept_m2905_repair_source_acquisition_materialization_claim_safe_existing_support_insufficient_route_to_m2907_source_execution_or_pivot_synthesis"
        if status_pass
        else "reject_m2905_repair_source_acquisition_materialization_audit_route_to_manual_repair"
    )
    return {
        "milestone": MILESTONE_ID,
        "m2905_summary": str(m2905_summary),
        "m2905_dir": str(m2905_dir),
        "status_pass": status_pass,
        "decision": decision,
        "audit_gates": audit_gates,
        "artifact_exists": artifact_exists,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "summary": summary,
        "observed_row_counts": observed_row_counts,
        "summary_row_counts": summary_row_counts,
        "row_count_matches": row_count_matches,
        "count_summary_matches": count_summary_matches,
        "gate_status_counts": dict(_count_status(gate_rows)),
        "rollback_status_counts": dict(_count_status(rollback_rows)),
        "seed_gap_missing_requirements": dict(_missing_requirements(seed_rows)),
        "task_family_counts": dict(Counter(row.get("task_family", "") for row in seed_rows)),
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
        "acquisition_required_count": len(acquisition_rows),
        "projection_row_count": len(projection_rows),
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
            "A bounded synthesis gate can choose source-acquisition execution, "
            "Route A pivot, Route C pivot, or stop after the accepted M2906 audit "
            "preserves the M2905 zero-projection repair/source-acquisition result."
        ),
        "lineage": {
            "parent_checkpoint": [
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
                "runs/m2848_engineering_controller_route_a_response_predictive_recurrent_belief_core_training_bounded_continuation_preflight/checkpoints/m2848_response_predictive_recurrent_belief_continuation_candidate.pt",
                "runs/m2866_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_training_implementation_preflight/checkpoints/m2866_localized_response_prediction_training_candidate.pt",
            ],
            "parent_dataset": [
                audit_payload["m2905_summary"],
                audit_payload["artifact_paths"]["seed_gap_repair_rows"],
                audit_payload["artifact_paths"]["acquisition_required_rows"],
                str(audit_doc),
                "docs/post-m2470-route-plan.md",
            ],
            "parent_config": [
                "experiments/manifests/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.json",
                "experiments/manifests/m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-preflight.json",
                "experiments/manifests/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design.json",
            ],
            "parent_objective": [
                "choose whether the accepted repair/source-acquisition accounting should execute source acquisition, pivot, or stop"
            ],
            "derived_from": [
                MILESTONE_ID,
                M2905_ID,
                "m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design",
                "docs/post-m2470-route-plan.md",
            ],
            "blocked_by": [
                "M2905 projects zero repaired fresh/source-diverse candidate rows from existing support",
                "34 source-singleton seed-gap rows require acquisition before Route B model-quality work",
                "post-M2470 route plan warns against continuing static infrastructure loops without synthesis",
            ],
            "supersedes": [
                "another repair-only materialization milestone without source execution or pivot synthesis",
                "treating acquisition accounting as validation or paper evidence",
            ],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M2907 must synthesize the accepted M2905/M2906 negative repair result",
            "M2907 must choose exactly one next route: source-acquisition execution, Route A pivot, Route C pivot, or stop",
            "M2907 must not admit another static repair-only loop without changing evidence",
            "M2907 must preserve actor 72/action 3 and evaluator-only target boundaries",
            "M2907 must keep source-singleton guard and public-reference rows out of validation paper proof and ordinary denominators",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not reset step rollout replay validate fit train rank promote publish or select a winner",
            "do not change actor input or action contract",
            "do not expose hidden dynamics oracle labels future targets route labels or verdict labels to actor input",
            "do not downgrade source-diversity thresholds to force a pass",
            "do not treat public reference source-singleton guard or acquisition-required rows as model-quality or paper denominators",
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
            "evidence_axis": "fresh_source_diverse_panel_source_execution_or_pivot_synthesis",
            "evidence_increment": "forces a synthesis after M2905/M2906 show zero projected fresh candidates from existing support",
            "claim_scope": CLAIM_SCOPE,
            "stop_condition": [
                "stop if no source-acquisition execution path can change the fresh/source-diverse evidence surface",
                "stop if the next action would add another static accounting artifact without source execution or pivot",
                "stop if source-diversity thresholds would be weakened",
                "stop if source-singleton guard or acquisition rows would enter validation paper proof or ordinary denominators",
                "stop if model-quality driver-performance paper current-sim high-fidelity full-driver or self-ID evidence would be claimed",
            ],
            "fallback_plan": [
                "route to Route A engineering controller evidence if Route B cannot acquire fresh/source-diverse support",
                "route to Route C high-fidelity interface preparation if current-sim source availability blocks Route B",
                "write a stop decision if no actor-safe evidence-producing next action remains",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M2906 accepts M2905 but preserves zero repaired-candidate projections and 34 acquisition-required rows",
            "synthesis_decision": "not_applicable",
            "synthesis_artifact": f"docs/{NEXT_ID}.md",
            "synthesis_questions": [
                "evidence_summary",
                "supported_claims",
                "falsified_claims",
                "failure_taxonomy_summary",
                "public_gate_overfit_risk",
                "route_options",
                "next_branch_decision",
            ],
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Route B source execution or pivot synthesis after zero projected repaired candidates",
            "admission_evidence": [
                "M2906 accepts M2905 as complete and claim-safe",
                "M2905 reports 34 acquisition-required rows and zero repaired-candidate projections",
                "post-M2470 route plan requires avoiding static current-sim or paper-route infrastructure loops",
            ],
            "blocked_shortcuts": [
                "no reset rollout validation ranking promotion",
                "no additional optimizer step and no promoted fitted weights",
                "no hidden or oracle actor inputs",
                "no source-singleton guard acquisition-required rows as proof",
                "no driver-performance paper current-sim high-fidelity full ideal driver finite-window-vs-GRU or self-ID claim",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                "M2907 status queue scoreboard research log and review",
                "one bounded follow-up source execution Route A pivot Route C pivot or stop manifest",
            ],
            "next_stage_criteria": [
                "M2907 chooses exactly one next route",
                "the chosen route can change evidence or explicitly stops/pivots",
                "actor target split holdout and exclusion boundaries remain preserved",
                "no validation ranking promotion model-quality paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M2907 is a synthesis gate and cannot substitute acquisition accounting for history-necessity evidence.",
            "history_necessity_tests": [
                "None in M2907; later evidence requires accepted source-diverse panel data and fair L0/L1/L2/L3 comparisons."
            ],
            "temporal_evidence_window": "M2884-M2906 Route B capability-prediction fresh-panel design, materialization, repair, and audit chain.",
            "negative_result_policy": "Preserve zero repaired projections and choose execution, pivot, or stop rather than weakening self-ID gates.",
            "allowed_claims": [
                "bounded route synthesis outcome",
                "M2905/M2906 preserve 34 acquisition-required rows and zero repaired-candidate projections",
                "no model-quality driver-performance paper current-sim high-fidelity finite-window-vs-GRU full-driver or self-ID claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "synthesis_decision",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 2,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "forces source execution or pivot/stop after a complete negative repair materialization audit",
            "paper_verdict_delta": "no verdict; may choose the next evidence-producing route or stop Route B",
            "must_synthesize_if": [
                "M2907 cannot choose source execution Route A pivot Route C pivot or stop",
                "M2907 would claim model quality self-ID finite-window-vs-GRU driver performance or current-sim verdict",
                "M2907 would let source-singleton guard or acquisition-required rows enter paper proof",
                "M2907 would expose evaluator-only future targets to actor input",
                "another repair-only loop is proposed without source execution or route pivot",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "synthesis summarizes M2905/M2906 negative repair/acquisition result",
            "synthesis chooses exactly one source execution pivot or stop route",
            "synthesis preserves source-diversity thresholds and exclusion boundaries",
            "no validation ranking promotion performance paper finite-window-vs-GRU current-sim high-fidelity full-driver or self-ID claim is made",
        ],
        "failure_criteria": [
            "M2907 adds another static repair-only milestone without source execution or pivot",
            "M2907 weakens source-diversity thresholds to force a pass",
            "M2907 treats public reference source-singleton guard or acquisition-required rows as proof or denominators",
            "M2907 claims driver performance model quality paper current-sim high-fidelity full-driver finite-window-vs-GRU or self-ID evidence",
            "M2907 fails to select one bounded next route or stop decision",
        ],
        "decision_rule": (
            "Pass only if M2907 makes a bounded route decision after the accepted "
            "zero-projection repair/source-acquisition audit and avoids another "
            "static repair loop."
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
            audit_payload["m2905_summary"],
            audit_payload["artifact_paths"]["acquisition_required_rows"],
            str(audit_doc),
            "docs/post-m2470-route-plan.md",
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": (
            "m2908-paper-route-l0-l1-l2-l3-capability-prediction-source-execution-"
            "or-route-pivot-result"
        ),
    }


def _format_mapping(mapping: dict[str, Any]) -> list[str]:
    if not mapping:
        return ["none"]
    return [f"{key}: {value}" for key, value in sorted(mapping.items())]


def render_audit_markdown(audit: dict[str, Any], *, follow_up_manifest: Path) -> str:
    summary = audit["summary"]
    row_counts = audit["observed_row_counts"]
    decision = audit["decision"]
    lines = [
        "# M2906 Paper Route L0/L1/L2/L3 Capability-Prediction Repair Source-Acquisition Materialization Result Audit",
        "",
        "## Metadata",
        "",
        "- status: completed" if audit["status_pass"] else "- status: failed",
        f"- decision: `{decision}`",
        "- manifest: `experiments/manifests/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.json`",
        f"- audited M2905 summary: `{audit['m2905_summary']}`",
        f"- audited M2905 directory: `{audit['m2905_dir']}`",
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
                "M2906 accepts M2905 as a complete and claim-safe repair/source-acquisition materialization audit surface.",
                "",
                "The accepted result is still negative for immediate fresh/source-diverse panel readiness: M2905 materialized 34 acquisition-required rows and 0 repaired-candidate projections from existing support. This blocks model-quality validation and routes to a source-execution or pivot synthesis instead of another static repair loop.",
            ]
        )
    else:
        lines.extend(
            [
                "M2906 rejects M2905 pending repair because at least one artifact, row-count, boundary, accounting, or claim gate failed.",
                "",
                "No source execution, validation, ranking, model-quality, paper, or self-ID route is admitted from a failed audit.",
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
            "M2906 did not reset, step, roll out, replay, acquire new sources, fit new weights, train, validate, rank, select a winner, promote a checkpoint, publish a package, or claim model quality, driver performance, paper evidence, current-sim verdict, high-fidelity validation, full-driver completion, finite-window-vs-GRU evidence, or level3 self-identification.",
            "",
            "## Artifact Completeness",
            "",
            "M2905 summary:",
            "",
            "```text",
            f"status_pass: {summary.get('status_pass')}",
            f"gate_matrix_pass: {summary.get('gate_matrix_pass')}",
            f"decision: {summary.get('decision')}",
            f"projected_design_targets_satisfied: {summary.get('projected_design_targets_satisfied')}",
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
            "## Repair Result",
            "",
            "M2906 preserves the M2905 repair/source-acquisition result exactly:",
            "",
            "```text",
            f"seed_gap_row_count: {summary.get('seed_gap_row_count')}",
            f"candidate_support_gap_count: {summary.get('candidate_support_gap_count')}",
            f"source_family_gap_count: {summary.get('source_family_gap_count')}",
            f"dual_gap_count: {summary.get('dual_gap_count')}",
            f"acquisition_required_count: {summary.get('acquisition_required_count')}",
            f"repaired_candidate_projection_count: {summary.get('repaired_candidate_projection_count')}",
            f"projected_fresh_candidate_task_count: {summary.get('projected_fresh_candidate_task_count')}",
            f"projected_fresh_candidate_profile_task_count: {summary.get('projected_fresh_candidate_profile_task_count')}",
            f"projected_source_family_count: {summary.get('projected_source_family_count')}",
            f"projected_task_family_count: {summary.get('projected_task_family_count')}",
            f"projected_target_family_coverage_count: {summary.get('projected_target_family_coverage_count')}",
            "```",
            "",
            "Seed-gap missing requirements:",
            "",
            "```text",
            *_format_mapping(audit["seed_gap_missing_requirements"]),
            "```",
            "",
            "Task-family counts:",
            "",
            "```text",
            *_format_mapping(audit["task_family_counts"]),
            "```",
            "",
            "The acquisition-required rows are source-acquisition inputs only. They do not become validation, paper proof, or ordinary success denominators.",
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
            f"source_singleton_rows_paper_proof_allowed: {summary.get('source_singleton_rows_paper_proof_allowed')}",
            f"guard_rows_ordinary_success_denominator_allowed: {summary.get('guard_rows_ordinary_success_denominator_allowed')}",
            "```",
            "",
            "## Supported Claim",
            "",
            "M2906 supports only this bounded claim:",
            "",
            "```text",
            "M2905 produced a complete and claim-safe repair/source-acquisition accounting surface, and that surface shows existing repo-local support projects zero repaired fresh/source-diverse candidates while leaving 34 acquisition-required rows.",
            "```",
            "",
            "This is route-synthesis evidence, not driver evidence and not paper evidence.",
            "",
            "## Rejected Interpretations",
            "",
            "M2906 rejects these interpretations:",
            "",
            "```text",
            "fresh/source-diverse panel ready for model-quality validation: false",
            "acquisition-required rows may serve as paper proof: false",
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
            "M2906 registers exactly one next route:",
            "",
            "```text",
            NEXT_ID,
            "```",
            "",
            "M2907 must synthesize whether to execute source acquisition, pivot to Route A, pivot to Route C, or stop. It must not admit another static repair-only loop unless the route decision explains how that loop changes evidence rather than bookkeeping.",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_artifacts(
    *,
    m2905_summary: Path,
    m2905_dir: Path,
    output_doc: Path,
    follow_up_manifest: Path = DEFAULT_FOLLOW_UP_MANIFEST,
) -> dict[str, Any]:
    audit = audit_m2905_artifacts(
        m2905_summary=m2905_summary,
        m2905_dir=m2905_dir,
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
    parser.add_argument("--m2905-summary", type=Path, default=DEFAULT_M2905_SUMMARY)
    parser.add_argument("--m2905-dir", type=Path, default=DEFAULT_M2905_DIR)
    parser.add_argument("--output-doc", type=Path, default=DEFAULT_OUTPUT_DOC)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    args = parser.parse_args()
    audit = write_audit_artifacts(
        m2905_summary=args.m2905_summary,
        m2905_dir=args.m2905_dir,
        output_doc=args.output_doc,
        follow_up_manifest=args.follow_up_manifest,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
