"""Materialize Route B task-quality and role-semantics repair candidates.

M2682 is a no-rollout reanalysis of the existing M2677 public T4/T5 rows and
M2680 outcome-dominance calibration panels. It writes an admission panel for a
future measured subset. It does not reset environments, execute policy actions,
train, rank controller families, select winners, promote checkpoints, or make
paper/self-ID claims.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_MILESTONE = (
    "m2682-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "repair-materialization-preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2683-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "repair-materialization-result-audit"
)
DEFAULT_M2677_DIR = Path(
    "runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight"
)
DEFAULT_M2680_DIR = Path(
    "runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2682_paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization"
)
DEFAULT_DOC_PATH = Path(
    "docs/m2682-paper-route-history-vs-current-response-task-quality-role-semantics-"
    "repair-materialization-preflight.md"
)
DEFAULT_FOLLOW_UP_MANIFEST = Path(
    "experiments/manifests/m2683-paper-route-history-vs-current-response-task-quality-"
    "role-semantics-repair-materialization-result-audit.json"
)

TARGET_EPISODE_COUNT = 864
TARGET_PROFILE_COUNT = 12
TARGET_SPEC_COUNT = 72
MAX_CANDIDATE_GROUPS = 10
MAX_SPECS_PER_CANDIDATE = 2

OUTCOME_SUCCESS = "success_obstacle_pass"
OUTCOME_COLLISION = "collision_failure"
OUTCOME_OFFTRACK = "off_track_noncollision_noncompletion"
OUTCOME_SPEED_TOO_LOW = "speed_too_low_noncollision_noncompletion"

CLAIM_SCOPE = (
    "Route B task-quality and role-semantics repair materialization only; "
    "existing M2677 and M2680 rows may be reaggregated into diagnostic blocker, "
    "candidate, excluded, and proposed future measured-subset panels, but no "
    "reset, step, rollout, replay, validation, training, PPO, private holdout, "
    "profile-specific tuning, controller-family ranking, winner selection, "
    "promotion, success-rate verdict, driver-performance, paper, finite-window-"
    "vs-GRU, current-response sufficiency, current-sim, high-fidelity "
    "validation, full ideal driver, or self-ID claim is made"
)
FORBIDDEN_INTERPRETATION = (
    "controller-family ranking, winner selection, checkpoint promotion, "
    "success-rate verdict, comparison-delta verdict, driver performance, "
    "validation readiness or result, paper-level evidence, finite-window-vs-"
    "GRU result, current-response sufficiency result, current-sim verdict, "
    "high-fidelity validation, full ideal driver completion, or level3 "
    "self-identification"
)

BLOCKER_FIELDNAMES = [
    "task_family",
    "source_edge",
    "role_semantics_proxy",
    "episode_count",
    "profile_count",
    "spec_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_count",
    "speed_too_low_count",
    "termination_offtrack_count",
    "success_rate",
    "collision_rate",
    "offtrack_outcome_rate",
    "dominant_outcome",
    "dominance_share",
    "blocked_by_offtrack_dominance",
    "blocked_by_low_success_support",
    "blocked_by_missing_role_semantics",
    "hidden_dynamics_bucket_required",
    "repair_priority_score",
    "repair_priority",
    "repair_recommendation",
    "claim_boundary",
]
CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "task_family",
    "source_edge",
    "role_semantics_proxy",
    "candidate_reason",
    "proposed_repair_action",
    "required_instrumentation",
    "proposed_measured_subset_role",
    "episode_count",
    "profile_count",
    "spec_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_rate",
    "repair_priority_score",
    "candidate_priority",
    "actor_input_contract_changed",
    "role_semantics_actor_visible",
    "hidden_oracle_actor_input_required",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
EXCLUDED_FIELDNAMES = [
    "task_family",
    "source_edge",
    "role_semantics_proxy",
    "episode_count",
    "profile_count",
    "spec_count",
    "success_count",
    "collision_count",
    "offtrack_outcome_rate",
    "repair_priority_score",
    "candidate_exclusion_reason",
    "actor_input_contract_changed",
    "role_semantics_actor_visible",
    "diagnostic_only_no_verdict",
    "claim_boundary",
]
SUBSET_FIELDNAMES = [
    "subset_row_id",
    "candidate_id",
    "task_source_id",
    "workload_id",
    "profile_name",
    "task_family",
    "source_edge",
    "role_semantics_proxy",
    "window_tag",
    "strata",
    "existing_outcome_bucket",
    "existing_termination_reason",
    "existing_profile_env_history_length",
    "future_execution_reason",
    "proposed_execution_stage",
    "diagnostic_only_no_verdict",
    "not_selected_from_success_only",
    "actor_input_contract_changed",
    "role_semantics_actor_visible",
    "hidden_oracle_actor_input_required",
    "claim_boundary",
]
CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m2682",
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


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def materialize_task_quality_role_semantics_repair(
    *,
    m2677_dir: Path | str = DEFAULT_M2677_DIR,
    m2680_dir: Path | str = DEFAULT_M2680_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    doc_path: Path | str = DEFAULT_DOC_PATH,
    follow_up_manifest: Path | str = DEFAULT_FOLLOW_UP_MANIFEST,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_m2677 = Path(m2677_dir)
    source_m2680 = Path(m2680_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(output, doc_path=Path(doc_path))
    source = load_source_artifacts(
        source_m2677,
        source_m2680,
        follow_up_manifest=Path(follow_up_manifest),
    )

    episode_rows = source["m2677_episode_rows"]
    blocker_rows = build_role_task_quality_blocker_rows(episode_rows)
    repair_candidate_rows, excluded_candidate_rows = build_repair_candidate_rows(blocker_rows)
    proposed_subset_rows = build_proposed_measured_subset_rows(
        episode_rows,
        repair_candidate_rows,
        specs_per_candidate=MAX_SPECS_PER_CANDIDATE,
    )
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=False,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        blocker_rows=blocker_rows,
        repair_candidate_rows=repair_candidate_rows,
        excluded_candidate_rows=excluded_candidate_rows,
        proposed_subset_rows=proposed_subset_rows,
        claim_rows=claim_rows,
        required_artifacts_present=False,
    )

    write_csv_rows(paths["role_task_quality_blocker_rows"], blocker_rows, fieldnames=BLOCKER_FIELDNAMES)
    write_csv_rows(paths["repair_candidate_rows"], repair_candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(paths["excluded_candidate_rows"], excluded_candidate_rows, fieldnames=EXCLUDED_FIELDNAMES)
    write_csv_rows(paths["proposed_measured_subset_rows"], proposed_subset_rows, fieldnames=SUBSET_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"complete": False, "completed_count": 0, "failure_count": 1})

    required_artifacts_present = all(path.exists() for key, path in paths.items() if key != "doc")
    claim_rows = build_claim_boundary_rows(
        follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
        artifacts_present=required_artifacts_present,
    )
    gate_rows = build_gate_matrix_rows(
        source=source,
        blocker_rows=blocker_rows,
        repair_candidate_rows=repair_candidate_rows,
        excluded_candidate_rows=excluded_candidate_rows,
        proposed_subset_rows=proposed_subset_rows,
        claim_rows=claim_rows,
        required_artifacts_present=required_artifacts_present,
    )
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)

    summary = build_summary(
        source=source,
        output_dir=output,
        paths=paths,
        blocker_rows=blocker_rows,
        repair_candidate_rows=repair_candidate_rows,
        excluded_candidate_rows=excluded_candidate_rows,
        proposed_subset_rows=proposed_subset_rows,
        claim_rows=claim_rows,
        gate_rows=gate_rows,
        required_artifacts_present=required_artifacts_present,
        milestone=milestone,
        next_blocker=next_blocker,
        follow_up_manifest=Path(follow_up_manifest),
    )
    write_json(paths["summary"], summary)
    write_json(
        paths["run_state"],
        {
            "target_episode_count": TARGET_EPISODE_COUNT,
            "completed_count": len(episode_rows),
            "failure_count": 0 if summary["status_pass"] else 1,
            "complete": bool(summary["status_pass"]),
        },
    )
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")

    required_artifacts_present = all(path.exists() for path in paths.values())
    if required_artifacts_present:
        claim_rows = build_claim_boundary_rows(
            follow_up_manifest_registered=source["source_exists"]["follow_up_manifest"],
            artifacts_present=True,
        )
        gate_rows = build_gate_matrix_rows(
            source=source,
            blocker_rows=blocker_rows,
            repair_candidate_rows=repair_candidate_rows,
            excluded_candidate_rows=excluded_candidate_rows,
            proposed_subset_rows=proposed_subset_rows,
            claim_rows=claim_rows,
            required_artifacts_present=True,
        )
        write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
        write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
        summary = build_summary(
            source=source,
            output_dir=output,
            paths=paths,
            blocker_rows=blocker_rows,
            repair_candidate_rows=repair_candidate_rows,
            excluded_candidate_rows=excluded_candidate_rows,
            proposed_subset_rows=proposed_subset_rows,
            claim_rows=claim_rows,
            gate_rows=gate_rows,
            required_artifacts_present=True,
            milestone=milestone,
            next_blocker=next_blocker,
            follow_up_manifest=Path(follow_up_manifest),
        )
        write_json(paths["summary"], summary)
        paths["doc"].write_text(render_milestone_doc(summary), encoding="utf-8")
        write_json(
            paths["run_state"],
            {
                "target_episode_count": TARGET_EPISODE_COUNT,
                "completed_count": len(episode_rows),
                "failure_count": 0 if summary["status_pass"] else 1,
                "complete": bool(summary["status_pass"]),
            },
        )
    return summary


def artifact_paths(output_dir: Path, *, doc_path: Path) -> dict[str, Path]:
    return {
        "summary": output_dir / "summary.json",
        "role_task_quality_blocker_rows": output_dir / "role_task_quality_blocker_rows.csv",
        "repair_candidate_rows": output_dir / "repair_candidate_rows.csv",
        "excluded_candidate_rows": output_dir / "excluded_candidate_rows.csv",
        "proposed_measured_subset_rows": output_dir / "proposed_measured_subset_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
    }


def load_source_artifacts(
    m2677_dir: Path,
    m2680_dir: Path,
    *,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    paths = {
        "m2677_summary": m2677_dir / "summary.json",
        "m2677_episode_rows": m2677_dir / "episode_rows.csv",
        "m2677_profile_aggregate": m2677_dir / "profile_aggregate.csv",
        "m2677_spec_aggregate": m2677_dir / "spec_aggregate.csv",
        "m2677_comparison_aggregate": m2677_dir / "comparison_aggregate.csv",
        "m2680_summary": m2680_dir / "summary.json",
        "m2680_spec_outcome_dominance_rows": m2680_dir / "spec_outcome_dominance_rows.csv",
        "m2680_profile_outcome_dominance_rows": m2680_dir / "profile_outcome_dominance_rows.csv",
        "m2680_task_family_outcome_dominance_rows": m2680_dir / "task_family_outcome_dominance_rows.csv",
        "m2680_comparison_interpretability_rows": m2680_dir / "comparison_interpretability_rows.csv",
        "m2680_calibration_gap_rows": m2680_dir / "calibration_gap_rows.csv",
        "m2680_claim_boundary_rows": m2680_dir / "claim_boundary_rows.csv",
        "m2680_gate_matrix": m2680_dir / "gate_matrix.csv",
        "follow_up_manifest": follow_up_manifest,
    }
    return {
        "paths": paths,
        "source_exists": {key: path.exists() for key, path in paths.items()},
        "m2677_summary": read_json(paths["m2677_summary"]) if paths["m2677_summary"].exists() else {},
        "m2677_episode_rows": read_csv_rows(paths["m2677_episode_rows"]),
        "m2677_profile_aggregate_rows": read_csv_rows(paths["m2677_profile_aggregate"]),
        "m2677_spec_aggregate_rows": read_csv_rows(paths["m2677_spec_aggregate"]),
        "m2677_comparison_aggregate_rows": read_csv_rows(paths["m2677_comparison_aggregate"]),
        "m2680_summary": read_json(paths["m2680_summary"]) if paths["m2680_summary"].exists() else {},
        "m2680_spec_outcome_dominance_rows": read_csv_rows(paths["m2680_spec_outcome_dominance_rows"]),
        "m2680_profile_outcome_dominance_rows": read_csv_rows(paths["m2680_profile_outcome_dominance_rows"]),
        "m2680_task_family_outcome_dominance_rows": read_csv_rows(
            paths["m2680_task_family_outcome_dominance_rows"]
        ),
        "m2680_comparison_interpretability_rows": read_csv_rows(
            paths["m2680_comparison_interpretability_rows"]
        ),
        "m2680_calibration_gap_rows": read_csv_rows(paths["m2680_calibration_gap_rows"]),
        "m2680_claim_boundary_rows": read_csv_rows(paths["m2680_claim_boundary_rows"]),
        "m2680_gate_matrix_rows": read_csv_rows(paths["m2680_gate_matrix"]),
    }


def build_role_task_quality_blocker_rows(
    episode_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        grouped[
            (
                str(row.get("task_family", "")),
                str(row.get("source_edge", "")),
                role_semantics_proxy(row),
            )
        ].append(row)
    for (task_family, source_edge, role_proxy), group_rows in sorted(grouped.items()):
        rows.append(build_one_blocker_row(task_family, source_edge, role_proxy, group_rows))
    return rows


def build_one_blocker_row(
    task_family: str,
    source_edge: str,
    role_proxy: str,
    group_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    outcome_counts = Counter(str(row.get("outcome_bucket", "")) for row in group_rows)
    termination_counts = Counter(str(row.get("termination_reason", "")) for row in group_rows)
    episode_count = len(group_rows)
    dominant_outcome, dominant_count = max(outcome_counts.items(), key=lambda item: (item[1], item[0]))
    dominance_share = dominant_count / episode_count if episode_count else 0.0
    success_count = int(outcome_counts.get(OUTCOME_SUCCESS, 0))
    collision_count = int(outcome_counts.get(OUTCOME_COLLISION, 0))
    offtrack_count = int(outcome_counts.get(OUTCOME_OFFTRACK, 0))
    speed_too_low_count = int(outcome_counts.get(OUTCOME_SPEED_TOO_LOW, 0))
    offtrack_rate = offtrack_count / episode_count if episode_count else 0.0
    priority_score = repair_priority_score(
        success_count=success_count,
        collision_count=collision_count,
        offtrack_rate=offtrack_rate,
        role_proxy=role_proxy,
    )
    return {
        "task_family": task_family,
        "source_edge": source_edge,
        "role_semantics_proxy": role_proxy,
        "episode_count": episode_count,
        "profile_count": len({str(row.get("profile_name", "")) for row in group_rows}),
        "spec_count": len({str(row.get("task_source_id", "")) for row in group_rows}),
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_outcome_count": offtrack_count,
        "speed_too_low_count": speed_too_low_count,
        "termination_offtrack_count": int(termination_counts.get("off_track", 0)),
        "success_rate": success_count / episode_count if episode_count else 0.0,
        "collision_rate": collision_count / episode_count if episode_count else 0.0,
        "offtrack_outcome_rate": offtrack_rate,
        "dominant_outcome": dominant_outcome,
        "dominance_share": dominance_share,
        "blocked_by_offtrack_dominance": offtrack_rate >= 0.70,
        "blocked_by_low_success_support": success_count == 0 or success_count < 3,
        "blocked_by_missing_role_semantics": True,
        "hidden_dynamics_bucket_required": role_proxy in {
            "hidden_dynamics_or_actuator_response",
            "hidden_dynamics_or_surface_response",
        },
        "repair_priority_score": priority_score,
        "repair_priority": priority_label(priority_score),
        "repair_recommendation": repair_recommendation(role_proxy),
        "claim_boundary": CLAIM_SCOPE,
    }


def role_semantics_proxy(row: Mapping[str, Any]) -> str:
    task_family = str(row.get("task_family", "")).strip().upper()
    text = " ".join(
        str(row.get(key, ""))
        for key in (
            "source_edge",
            "executable_source_family",
            "env_template_family",
            "window_tag",
            "strata",
        )
    ).lower()
    actuator_tokens = (
        "actuator_delay",
        "capability_step",
        "brake_fade",
        "brake_loss",
        "drive_loss",
        "steer_tau",
        "drive_tau",
    )
    surface_tokens = ("friction", "mu_step", "low_mu")
    boundary_tokens = ("curved_boundary", "near_boundary", "late_reveal", "boundary", "reveal")
    if any(token in text for token in actuator_tokens):
        return "hidden_dynamics_or_actuator_response"
    if any(token in text for token in surface_tokens):
        return "hidden_dynamics_or_surface_response"
    if any(token in text for token in boundary_tokens):
        return "boundary_or_reveal_geometry"
    if task_family == "T4":
        return "history_response_diagnostic"
    if task_family == "T5":
        return "near_boundary_generalization"
    return "unassigned_role_semantics_proxy"


def repair_priority_score(
    *,
    success_count: int,
    collision_count: int,
    offtrack_rate: float,
    role_proxy: str,
) -> int:
    score = 0
    if success_count > 0:
        score += 3
    if collision_count > 0:
        score += 2
    if offtrack_rate >= 0.85:
        score += 1
    if role_proxy in {"hidden_dynamics_or_actuator_response", "hidden_dynamics_or_surface_response"}:
        score += 1
    return score


def priority_label(score: int) -> str:
    if score >= 7:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def repair_recommendation(role_proxy: str) -> str:
    if role_proxy in {"hidden_dynamics_or_actuator_response", "hidden_dynamics_or_surface_response"}:
        return "materialize diagnostic role buckets and repair task quality for response/timing support before measured execution"
    if role_proxy == "boundary_or_reveal_geometry":
        return "materialize boundary/reveal role buckets and repair geometry support before measured execution"
    return "materialize explicit role semantics before any comparison interpretation"


def build_repair_candidate_rows(
    blocker_rows: list[Mapping[str, Any]],
    *,
    max_candidates: int = MAX_CANDIDATE_GROUPS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ranked = sorted(
        blocker_rows,
        key=lambda row: (
            -_int_or_zero(row.get("repair_priority_score", 0)),
            -_int_or_zero(row.get("success_count", 0)),
            -_int_or_zero(row.get("collision_count", 0)),
            str(row.get("task_family", "")),
            str(row.get("source_edge", "")),
        ),
    )
    selected_keys: set[tuple[str, str, str]] = set()
    for row in ranked[: max(0, max_candidates - 2)]:
        selected_keys.add(blocker_key(row))
    for task_family in sorted({str(row.get("task_family", "")) for row in blocker_rows}):
        best = best_row_for(
            blocker_rows,
            lambda row, family=task_family: str(row.get("task_family", "")) == family,
        )
        if best is not None:
            selected_keys.add(blocker_key(best))
    for role_proxy in sorted({str(row.get("role_semantics_proxy", "")) for row in blocker_rows}):
        best = best_row_for(
            blocker_rows,
            lambda row, proxy=role_proxy: str(row.get("role_semantics_proxy", "")) == proxy,
        )
        if best is not None:
            selected_keys.add(blocker_key(best))
    while len(selected_keys) > max_candidates:
        lowest = min(
            (row for row in blocker_rows if blocker_key(row) in selected_keys),
            key=lambda row: (
                _int_or_zero(row.get("repair_priority_score", 0)),
                _int_or_zero(row.get("success_count", 0)),
                _int_or_zero(row.get("collision_count", 0)),
                str(row.get("task_family", "")),
                str(row.get("source_edge", "")),
            ),
        )
        selected_keys.remove(blocker_key(lowest))

    selected_rows = [
        row
        for row in sorted(
            blocker_rows,
            key=lambda item: (
                -_int_or_zero(item.get("repair_priority_score", 0)),
                str(item.get("task_family", "")),
                str(item.get("source_edge", "")),
            ),
        )
        if blocker_key(row) in selected_keys
    ]
    candidate_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected_rows, start=1):
        candidate_rows.append(candidate_from_blocker(row, candidate_id=f"m2682-candidate-{index:03d}"))

    excluded_rows: list[dict[str, Any]] = []
    for row in blocker_rows:
        if blocker_key(row) in selected_keys:
            continue
        excluded_rows.append(excluded_from_blocker(row))
    return candidate_rows, excluded_rows


def best_row_for(
    rows: list[Mapping[str, Any]],
    predicate: Any,
) -> Mapping[str, Any] | None:
    matches = [row for row in rows if predicate(row)]
    if not matches:
        return None
    return sorted(
        matches,
        key=lambda row: (
            -_int_or_zero(row.get("repair_priority_score", 0)),
            -_int_or_zero(row.get("success_count", 0)),
            -_int_or_zero(row.get("collision_count", 0)),
            str(row.get("task_family", "")),
            str(row.get("source_edge", "")),
        ),
    )[0]


def candidate_from_blocker(row: Mapping[str, Any], *, candidate_id: str) -> dict[str, Any]:
    success_count = _int_or_zero(row.get("success_count", 0))
    collision_count = _int_or_zero(row.get("collision_count", 0))
    reason_parts = ["repair admission candidate, not a winner or verdict"]
    if success_count > 0:
        reason_parts.append("has sparse success support to preserve during repair")
    if collision_count > 0:
        reason_parts.append("has collision support for mitigation-boundary diagnostics")
    if _bool(row.get("blocked_by_offtrack_dominance", False)):
        reason_parts.append("offtrack dominance must be reduced before interpretation")
    return {
        "candidate_id": candidate_id,
        "task_family": row.get("task_family", ""),
        "source_edge": row.get("source_edge", ""),
        "role_semantics_proxy": row.get("role_semantics_proxy", ""),
        "candidate_reason": "; ".join(reason_parts),
        "proposed_repair_action": repair_recommendation(str(row.get("role_semantics_proxy", ""))),
        "required_instrumentation": "analysis-only role bucket plus task-quality blocker audit; no actor-visible labels",
        "proposed_measured_subset_role": "future_measured_execution_admission_probe_after_result_audit",
        "episode_count": _int_or_zero(row.get("episode_count", 0)),
        "profile_count": _int_or_zero(row.get("profile_count", 0)),
        "spec_count": _int_or_zero(row.get("spec_count", 0)),
        "success_count": success_count,
        "collision_count": collision_count,
        "offtrack_outcome_rate": _float_or_zero(row.get("offtrack_outcome_rate", 0.0)),
        "repair_priority_score": _int_or_zero(row.get("repair_priority_score", 0)),
        "candidate_priority": row.get("repair_priority", ""),
        "actor_input_contract_changed": False,
        "role_semantics_actor_visible": False,
        "hidden_oracle_actor_input_required": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def excluded_from_blocker(row: Mapping[str, Any]) -> dict[str, Any]:
    reason = "lower-priority repair admission group kept as excluded diagnostic evidence"
    if _int_or_zero(row.get("success_count", 0)) == 0 and _int_or_zero(row.get("collision_count", 0)) == 0:
        reason = "excluded from first measured subset because current rows have only offtrack/no sparse support"
    return {
        "task_family": row.get("task_family", ""),
        "source_edge": row.get("source_edge", ""),
        "role_semantics_proxy": row.get("role_semantics_proxy", ""),
        "episode_count": _int_or_zero(row.get("episode_count", 0)),
        "profile_count": _int_or_zero(row.get("profile_count", 0)),
        "spec_count": _int_or_zero(row.get("spec_count", 0)),
        "success_count": _int_or_zero(row.get("success_count", 0)),
        "collision_count": _int_or_zero(row.get("collision_count", 0)),
        "offtrack_outcome_rate": _float_or_zero(row.get("offtrack_outcome_rate", 0.0)),
        "repair_priority_score": _int_or_zero(row.get("repair_priority_score", 0)),
        "candidate_exclusion_reason": reason,
        "actor_input_contract_changed": False,
        "role_semantics_actor_visible": False,
        "diagnostic_only_no_verdict": True,
        "claim_boundary": CLAIM_SCOPE,
    }


def build_proposed_measured_subset_rows(
    episode_rows: list[Mapping[str, Any]],
    repair_candidate_rows: list[Mapping[str, Any]],
    *,
    specs_per_candidate: int = MAX_SPECS_PER_CANDIDATE,
) -> list[dict[str, Any]]:
    candidate_by_key = {candidate_key(row): row for row in repair_candidate_rows}
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        key = (
            str(row.get("task_family", "")),
            str(row.get("source_edge", "")),
            role_semantics_proxy(row),
        )
        if key in candidate_by_key:
            grouped[key].append(row)

    subset_rows: list[dict[str, Any]] = []
    subset_index = 1
    for key, group_rows in sorted(grouped.items()):
        candidate = candidate_by_key[key]
        selected_specs = select_specs_for_candidate(group_rows, max_specs=specs_per_candidate)
        for row in sorted(
            group_rows,
            key=lambda item: (str(item.get("task_source_id", "")), str(item.get("profile_name", ""))),
        ):
            if str(row.get("task_source_id", "")) not in selected_specs:
                continue
            subset_rows.append(
                {
                    "subset_row_id": f"m2682-subset-{subset_index:04d}",
                    "candidate_id": candidate.get("candidate_id", ""),
                    "task_source_id": row.get("task_source_id", ""),
                    "workload_id": row.get("workload_id", ""),
                    "profile_name": row.get("profile_name", ""),
                    "task_family": row.get("task_family", ""),
                    "source_edge": row.get("source_edge", ""),
                    "role_semantics_proxy": key[2],
                    "window_tag": row.get("window_tag", ""),
                    "strata": row.get("strata", ""),
                    "existing_outcome_bucket": row.get("outcome_bucket", ""),
                    "existing_termination_reason": row.get("termination_reason", ""),
                    "existing_profile_env_history_length": row.get("profile_env_history_length", ""),
                    "future_execution_reason": "candidate admits whole spec/profile cells for post-audit measured execution, not current-row interpretation",
                    "proposed_execution_stage": "post_audit_measured_subset_candidate",
                    "diagnostic_only_no_verdict": True,
                    "not_selected_from_success_only": True,
                    "actor_input_contract_changed": False,
                    "role_semantics_actor_visible": False,
                    "hidden_oracle_actor_input_required": False,
                    "claim_boundary": CLAIM_SCOPE,
                }
            )
            subset_index += 1
    return subset_rows


def select_specs_for_candidate(
    group_rows: list[Mapping[str, Any]],
    *,
    max_specs: int,
) -> set[str]:
    spec_groups = _group_rows(group_rows, ("task_source_id",))
    ranked_specs = sorted(
        spec_groups.items(),
        key=lambda item: (
            -spec_support_score(item[1]),
            str(item[0][0]),
        ),
    )
    return {spec_key[0] for spec_key, _rows in ranked_specs[:max_specs]}


def spec_support_score(rows: list[Mapping[str, Any]]) -> int:
    counts = Counter(str(row.get("outcome_bucket", "")) for row in rows)
    offtrack = int(counts.get(OUTCOME_OFFTRACK, 0))
    episode_count = len(rows)
    return (
        10 * int(counts.get(OUTCOME_SUCCESS, 0))
        + 5 * int(counts.get(OUTCOME_COLLISION, 0))
        + max(0, episode_count - offtrack)
    )


def build_claim_boundary_rows(*, follow_up_manifest_registered: bool, artifacts_present: bool) -> list[dict[str, Any]]:
    rows = [
        claim("repair_materialization", "artifact", True, artifacts_present, "summary and repair panel rows"),
        claim("role_task_quality_blocker_rows", "artifact", True, artifacts_present, "role/task-quality blocker CSV"),
        claim("repair_candidate_rows", "artifact", True, artifacts_present, "repair candidate CSV"),
        claim("excluded_candidate_rows", "artifact", True, artifacts_present, "excluded diagnostic CSV"),
        claim("proposed_measured_subset_rows", "artifact", True, artifacts_present, "future subset candidate CSV"),
        claim("claim_boundary_rows", "artifact", True, artifacts_present, "claim boundary CSV"),
        claim("gate_matrix", "artifact", True, artifacts_present, "gate matrix CSV"),
        claim("diagnostic_role_semantics_proxy", "diagnostic", True, True, "analysis-only role proxy rows"),
        claim("follow_up_audit_registered", "follow_up_route", True, follow_up_manifest_registered, "M2683 result audit manifest"),
    ]
    blocked = [
        ("reset_or_rollout_execution", "execution", "future measured execution manifest"),
        ("measured_execution", "execution", "future measured execution manifest"),
        ("training_or_ppo", "execution", "future training manifest"),
        ("replay_or_validation", "execution", "future replay or validation manifest"),
        ("private_holdout_tuning", "holdout_policy", "forbidden in public repair materialization"),
        ("actor_input_contract_change", "contract", "future actor contract review"),
        ("hidden_oracle_actor_input", "contract", "forbidden actor input"),
        ("profile_specific_tuning", "objective_overfit", "future controlled tuning protocol"),
        ("controller_family_ranking", "ranking", "future audited comparison interpretation"),
        ("winner_selection", "promotion", "future promotion gate"),
        ("checkpoint_promotion", "promotion", "future promotion gate"),
        ("success_rate_verdict", "verdict", "future result audit and verdict milestone"),
        ("comparison_delta_verdict", "verdict", "future result audit and interpretation milestone"),
        ("driver_performance", "driver_performance", "future proof/generalization/claim audit"),
        ("validation_readiness", "validation", "future validation-readiness route"),
        ("paper_level_evidence", "paper", "future audited evidence matrix"),
        ("finite_window_vs_gru_result", "paper", "future fair comparison audit"),
        ("current_response_sufficiency_result", "paper", "future fair comparison audit"),
        ("current_sim_verdict", "paper", "future current-sim synthesis"),
        ("high_fidelity_validation", "validation", "future high-fidelity validation"),
        ("level3_self_identification", "self_id", "future source-diverse intervention proof"),
        ("full_ideal_driver_completion", "full_goal", "future full ideal driver gate"),
    ]
    rows.extend(claim(claim_id, family, False, False, evidence) for claim_id, family, evidence in blocked)
    return rows


def build_gate_matrix_rows(
    *,
    source: dict[str, Any],
    blocker_rows: list[Mapping[str, Any]],
    repair_candidate_rows: list[Mapping[str, Any]],
    excluded_candidate_rows: list[Mapping[str, Any]],
    proposed_subset_rows: list[Mapping[str, Any]],
    claim_rows: list[Mapping[str, Any]],
    required_artifacts_present: bool,
) -> list[dict[str, Any]]:
    episode_rows = source["m2677_episode_rows"]
    source_m2677_summary = source["m2677_summary"]
    source_m2680_summary = source["m2680_summary"]
    source_present = all(source["source_exists"].values())
    profile_count = len({str(row.get("profile_name", "")) for row in episode_rows})
    spec_count = len({str(row.get("task_source_id", "")) for row in episode_rows})
    subset_profile_count = len({str(row.get("profile_name", "")) for row in proposed_subset_rows})
    subset_spec_count = len({str(row.get("task_source_id", "")) for row in proposed_subset_rows})
    subset_task_family_count = len({str(row.get("task_family", "")) for row in proposed_subset_rows})
    full_matrix = len(proposed_subset_rows) == len(episode_rows) and {
        str(row.get("workload_id", "")) for row in proposed_subset_rows
    } == {str(row.get("workload_id", "")) for row in episode_rows}
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2682"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2682"])]
    return [
        gate("source_artifacts_present", "lineage", source_present, source["source_exists"], "all M2677/M2680 source artifacts and M2683 follow-up manifest present", "lineage_invalid"),
        gate("m2677_status_pass", "lineage", _bool(source_m2677_summary.get("status_pass", False)), source_m2677_summary.get("status_pass", None), True, "lineage_invalid"),
        gate("m2680_status_pass", "lineage", _bool(source_m2680_summary.get("status_pass", False)), source_m2680_summary.get("status_pass", None), True, "lineage_invalid"),
        gate("episode_rows_complete", "lineage", len(episode_rows) == TARGET_EPISODE_COUNT, len(episode_rows), TARGET_EPISODE_COUNT, "lineage_invalid"),
        gate("profile_count_complete", "lineage", profile_count == TARGET_PROFILE_COUNT, profile_count, TARGET_PROFILE_COUNT, "lineage_invalid"),
        gate("spec_count_complete", "lineage", spec_count == TARGET_SPEC_COUNT, spec_count, TARGET_SPEC_COUNT, "lineage_invalid"),
        gate("m2680_interpretation_blocker_reflected", "metric_artifact", _int_or_zero(source_m2680_summary.get("comparison_ranking_interpretable_count", 1)) == 0, source_m2680_summary.get("comparison_ranking_interpretable_count", None), 0, "proof_washout"),
        gate("m2680_hidden_dynamics_missing_reflected", "metric_artifact", _bool(source_m2680_summary.get("hidden_dynamics_bucket_missing", False)), source_m2680_summary.get("hidden_dynamics_bucket_missing", None), True, "metric_artifact"),
        gate("role_task_quality_blocker_rows_present", "artifact", len(blocker_rows) > 0, len(blocker_rows), ">0 role/task-quality blocker rows", "metric_artifact"),
        gate("repair_candidate_rows_present", "artifact", len(repair_candidate_rows) > 0, len(repair_candidate_rows), ">0 repair candidate rows", "metric_artifact"),
        gate("excluded_candidate_rows_present", "artifact", len(excluded_candidate_rows) > 0, len(excluded_candidate_rows), ">0 excluded candidate rows", "metric_artifact"),
        gate("proposed_subset_rows_present", "artifact", len(proposed_subset_rows) > 0, len(proposed_subset_rows), ">0 proposed subset rows", "metric_artifact"),
        gate("proposed_subset_not_full_public_matrix", "local_search_guard", not full_matrix and len(proposed_subset_rows) < len(episode_rows), len(proposed_subset_rows), f"<{len(episode_rows)} and not identical to full public matrix", "objective_overfit"),
        gate("proposed_subset_multi_profile", "artifact", subset_profile_count >= min(TARGET_PROFILE_COUNT, profile_count), subset_profile_count, f">={min(TARGET_PROFILE_COUNT, profile_count)} profiles", "metric_artifact"),
        gate("proposed_subset_multi_spec", "artifact", subset_spec_count >= 4, subset_spec_count, ">=4 specs", "metric_artifact"),
        gate("proposed_subset_task_family_coverage", "artifact", subset_task_family_count >= 2, subset_task_family_count, ">=2 task families", "metric_artifact"),
        gate("candidate_rows_diagnostic_only", "claim_boundary", repair_candidate_rows and all(_bool(row.get("diagnostic_only_no_verdict", False)) for row in repair_candidate_rows), "all candidate rows diagnostic-only", "all candidate rows diagnostic-only", "proof_washout"),
        gate("subset_rows_diagnostic_only", "claim_boundary", proposed_subset_rows and all(_bool(row.get("diagnostic_only_no_verdict", False)) and _bool(row.get("not_selected_from_success_only", False)) for row in proposed_subset_rows), "all subset rows whole-cell diagnostic candidates", "all subset rows whole-cell diagnostic candidates", "proof_washout"),
        gate("role_semantics_not_actor_visible", "contract", all(not _bool(row.get("role_semantics_actor_visible", True)) for row in repair_candidate_rows + proposed_subset_rows), "analysis-only role semantics", "role semantics not actor-visible", "contract_violation"),
        gate("no_environment_execution_or_policy_action", "execution_guardrail", True, "M2682 reads CSV/JSON only", "no reset step rollout replay validation policy action", "objective_overfit"),
        gate("actor_contract_preserved", "contract", True, "P0 observation 72/action 3 unchanged", "P0 observation 72/action 3 unchanged", "contract_violation"),
        gate("claim_boundary_blocks_overclaim", "claim_boundary", all(_bool(row["status_pass"]) for row in allowed_claim_rows) and all(not _bool(row["claim_made"]) and _bool(row["status_pass"]) for row in blocked_claim_rows), f"allowed={len(allowed_claim_rows)} blocked={len(blocked_claim_rows)}", "allowed claims true and blocked claims not made", "proof_washout"),
        gate("required_artifacts_present", "artifact", required_artifacts_present, required_artifacts_present, True, "lineage_invalid"),
    ]


def build_summary(
    *,
    source: dict[str, Any],
    output_dir: Path,
    paths: dict[str, Path],
    blocker_rows: list[Mapping[str, Any]],
    repair_candidate_rows: list[Mapping[str, Any]],
    excluded_candidate_rows: list[Mapping[str, Any]],
    proposed_subset_rows: list[Mapping[str, Any]],
    claim_rows: list[Mapping[str, Any]],
    gate_rows: list[Mapping[str, Any]],
    required_artifacts_present: bool,
    milestone: str,
    next_blocker: str,
    follow_up_manifest: Path,
) -> dict[str, Any]:
    episode_rows = source["m2677_episode_rows"]
    outcome_counts = dict(sorted(Counter(str(row.get("outcome_bucket", "")) for row in episode_rows).items()))
    termination_counts = dict(sorted(Counter(str(row.get("termination_reason", "")) for row in episode_rows).items()))
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    status_pass = bool(gate_matrix_pass and required_artifacts_present)
    allowed_claim_rows = [row for row in claim_rows if _bool(row["allowed_in_m2682"])]
    blocked_claim_rows = [row for row in claim_rows if not _bool(row["allowed_in_m2682"])]
    subset_workloads = {str(row.get("workload_id", "")) for row in proposed_subset_rows}
    full_workloads = {str(row.get("workload_id", "")) for row in episode_rows}
    proposed_subset_is_full_public_matrix = len(proposed_subset_rows) == len(episode_rows) and subset_workloads == full_workloads
    return {
        "milestone": milestone,
        "status_pass": status_pass,
        "result_class": _result_class(status_pass),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output_dir),
        "source_m2677_dir": str(source["paths"]["m2677_summary"].parent),
        "source_m2680_dir": str(source["paths"]["m2680_summary"].parent),
        "source_m2677_status_pass": _bool(source["m2677_summary"].get("status_pass", False)),
        "source_m2680_status_pass": _bool(source["m2680_summary"].get("status_pass", False)),
        "next_blocker": next_blocker,
        "selected_next_action": next_blocker,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "episode_count": len(episode_rows),
        "target_episode_count": TARGET_EPISODE_COUNT,
        "profile_count": len({str(row.get("profile_name", "")) for row in episode_rows}),
        "target_profile_count": TARGET_PROFILE_COUNT,
        "spec_count": len({str(row.get("task_source_id", "")) for row in episode_rows}),
        "target_spec_count": TARGET_SPEC_COUNT,
        "task_family_count": len({str(row.get("task_family", "")) for row in episode_rows}),
        "outcome_counts": outcome_counts,
        "termination_reason_counts": termination_counts,
        "success_count": int(outcome_counts.get(OUTCOME_SUCCESS, 0)),
        "collision_count": int(outcome_counts.get(OUTCOME_COLLISION, 0)),
        "offtrack_outcome_count": int(outcome_counts.get(OUTCOME_OFFTRACK, 0)),
        "termination_offtrack_count": int(termination_counts.get("off_track", 0)),
        "m2680_global_outcome_dominance_blocked": _bool(source["m2680_summary"].get("global_outcome_dominance_blocked", False)),
        "m2680_hidden_dynamics_bucket_missing": _bool(source["m2680_summary"].get("hidden_dynamics_bucket_missing", False)),
        "m2680_comparison_ranking_interpretable_count": _int_or_zero(source["m2680_summary"].get("comparison_ranking_interpretable_count", 0)),
        "role_task_quality_blocker_row_count": len(blocker_rows),
        "repair_candidate_row_count": len(repair_candidate_rows),
        "excluded_candidate_row_count": len(excluded_candidate_rows),
        "proposed_measured_subset_row_count": len(proposed_subset_rows),
        "proposed_measured_subset_spec_count": len({str(row.get("task_source_id", "")) for row in proposed_subset_rows}),
        "proposed_measured_subset_profile_count": len({str(row.get("profile_name", "")) for row in proposed_subset_rows}),
        "proposed_measured_subset_task_family_count": len({str(row.get("task_family", "")) for row in proposed_subset_rows}),
        "proposed_subset_is_full_public_matrix": proposed_subset_is_full_public_matrix,
        "proposed_subset_selected_from_success_only": False,
        "role_semantics_proxy_count": len({str(row.get("role_semantics_proxy", "")) for row in blocker_rows}),
        "claim_boundary_row_count": len(claim_rows),
        "allowed_claim_boundary_row_count": len(allowed_claim_rows),
        "blocked_claim_boundary_row_count": len(blocked_claim_rows),
        "gate_matrix_row_count": len(gate_rows),
        "gate_matrix_pass": gate_matrix_pass,
        "required_artifacts_present": required_artifacts_present,
        "environment_reset_started": False,
        "environment_step_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_execution_started": False,
        "measured_validation_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "private_holdout_used": False,
        "profile_specific_tuning": False,
        "actor_input_contract_changed": False,
        "actor_contract_shape_72_action_3": True,
        "role_semantics_actor_visible": False,
        "hidden_oracle_actor_input_detected": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "promoted": False,
        "success_rate_verdict_claim_made": False,
        "comparison_delta_verdict_claim_made": False,
        "driver_performance_claim_made": False,
        "validation_readiness_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_response_sufficiency_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "level3_self_id_claim_made": False,
        "full_ideal_driver_gate_passed": False,
        "full_ideal_driver_completion_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "paths": {key: str(path) for key, path in paths.items()},
    }


def render_milestone_doc(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# M2682 Paper Route History Vs Current Response Task Quality Role Semantics Repair Materialization Preflight",
            "",
            "## Summary",
            "",
            f"- status: {'completed' if summary['status_pass'] else 'failed'}",
            f"- result_class: `{summary['result_class']}`",
            f"- generated_at_utc: `{summary['generated_at_utc']}`",
            f"- manifest: `experiments/manifests/{DEFAULT_MILESTONE}.json`",
            f"- source M2677 status pass: {summary['source_m2677_status_pass']}",
            f"- source M2680 status pass: {summary['source_m2680_status_pass']}",
            f"- summary: `{summary['paths']['summary']}`",
            f"- blocker rows: `{summary['paths']['role_task_quality_blocker_rows']}`",
            f"- repair candidate rows: `{summary['paths']['repair_candidate_rows']}`",
            f"- excluded candidate rows: `{summary['paths']['excluded_candidate_rows']}`",
            f"- proposed measured subset rows: `{summary['paths']['proposed_measured_subset_rows']}`",
            f"- claim boundary rows: `{summary['paths']['claim_boundary_rows']}`",
            f"- gate matrix: `{summary['paths']['gate_matrix']}`",
            f"- run state: `{summary['paths']['run_state']}`",
            f"- follow-up manifest: `{summary['follow_up_manifest']}`",
            f"- next: `{summary['next_blocker']}`",
            "",
            "## Materialized Repair Surface",
            "",
            f"- episode rows consumed: {summary['episode_count']} / {summary['target_episode_count']}",
            f"- profiles covered: {summary['profile_count']} / {summary['target_profile_count']}",
            f"- specs covered: {summary['spec_count']} / {summary['target_spec_count']}",
            f"- task families covered: {summary['task_family_count']}",
            f"- role/task-quality blocker rows: {summary['role_task_quality_blocker_row_count']}",
            f"- repair candidate rows: {summary['repair_candidate_row_count']}",
            f"- excluded candidate rows: {summary['excluded_candidate_row_count']}",
            f"- role semantics proxies: {summary['role_semantics_proxy_count']}",
            "",
            "## Proposed Future Measured Subset",
            "",
            f"- proposed rows: {summary['proposed_measured_subset_row_count']}",
            f"- proposed specs: {summary['proposed_measured_subset_spec_count']}",
            f"- proposed profiles: {summary['proposed_measured_subset_profile_count']}",
            f"- proposed task families: {summary['proposed_measured_subset_task_family_count']}",
            f"- identical to full public matrix: {summary['proposed_subset_is_full_public_matrix']}",
            f"- selected from success rows only: {summary['proposed_subset_selected_from_success_only']}",
            "",
            "## Source Blockers Preserved",
            "",
            f"- M2680 global outcome dominance blocked: {summary['m2680_global_outcome_dominance_blocked']}",
            f"- M2680 hidden-dynamics bucket missing: {summary['m2680_hidden_dynamics_bucket_missing']}",
            f"- M2680 comparison rows interpretable for ranking: {summary['m2680_comparison_ranking_interpretable_count']}",
            f"- success count: {summary['success_count']}",
            f"- collision count: {summary['collision_count']}",
            f"- offtrack outcome count: {summary['offtrack_outcome_count']}",
            f"- offtrack termination count: {summary['termination_offtrack_count']}",
            "",
            "## Guardrails",
            "",
            f"- environment reset started: {summary['environment_reset_started']}",
            f"- environment rollout started: {summary['environment_rollout_started']}",
            f"- policy action executed: {summary['policy_action_executed']}",
            f"- measured execution started: {summary['measured_execution_started']}",
            f"- measured validation started: {summary['measured_validation_started']}",
            f"- training started: {summary['training_started']}",
            f"- replay started: {summary['replay_started']}",
            f"- PPO used: {summary['ppo_used']}",
            f"- private holdout used: {summary['private_holdout_used']}",
            f"- profile-specific tuning: {summary['profile_specific_tuning']}",
            f"- actor input contract changed: {summary['actor_input_contract_changed']}",
            f"- role semantics actor visible: {summary['role_semantics_actor_visible']}",
            f"- hidden/oracle actor input detected: {summary['hidden_oracle_actor_input_detected']}",
            f"- controller-family ranking claim made: {summary['controller_family_ranking_claim_made']}",
            f"- success-rate verdict claim made: {summary['success_rate_verdict_claim_made']}",
            f"- paper-level claim made: {summary['paper_level_claim_made']}",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
            "",
            "```text",
            "No-rollout repair admission materialization and diagnostic role/task-quality localization from existing M2677/M2680 rows.",
            "```",
            "",
            "Rejected:",
            "",
            "```text",
            summary["forbidden_interpretation"],
            "```",
            "",
            "M2682 passes only if the candidate panel is complete, the proposed",
            "future measured subset is smaller than the full public matrix, and",
            "role semantics remain analysis-only. It does not make M2677 or",
            "M2680 interpretable as controller-family ranking, paper evidence,",
            "current-sim verdict, finite-window-vs-GRU evidence, current-",
            "response sufficiency, high-fidelity validation, full ideal driver",
            "completion, or self-ID.",
            "",
        ]
    )


def blocker_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("task_family", "")),
        str(row.get("source_edge", "")),
        str(row.get("role_semantics_proxy", "")),
    )


def candidate_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return blocker_key(row)


def _group_rows(
    rows: Iterable[Mapping[str, Any]],
    keys: Sequence[str],
) -> dict[tuple[str, ...], list[Mapping[str, Any]]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return dict(sorted(groups.items()))


def _result_class(status_pass: bool) -> str:
    if status_pass:
        return "paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization_pass"
    return "paper_route_history_vs_current_response_task_quality_role_semantics_repair_materialization_fail"


def claim(
    claim_id: str,
    family: str,
    allowed: bool,
    claim_made: bool,
    evidence: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim_family": family,
        "allowed_in_m2682": bool(allowed),
        "claim_made": bool(claim_made),
        "status_pass": bool(claim_made) if allowed else not bool(claim_made),
        "evidence_required_before_claim": evidence,
        "claim_boundary": CLAIM_SCOPE,
    }


def gate(
    gate_id: str,
    family: str,
    status_pass: bool,
    observed: Any,
    expected: Any,
    failure_type: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_family": family,
        "status_pass": bool(status_pass),
        "observed": observed,
        "expected": expected,
        "failure_type": "" if status_pass else failure_type,
        "claim_boundary": CLAIM_SCOPE,
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_or_zero(value: Any) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _float_or_zero(value: Any) -> float:
    value_float = _float_or_nan(value)
    return value_float if math.isfinite(value_float) else 0.0


def _float_or_nan(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2677-dir", type=Path, default=DEFAULT_M2677_DIR)
    parser.add_argument("--m2680-dir", type=Path, default=DEFAULT_M2680_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args(argv)
    summary = materialize_task_quality_role_semantics_repair(
        m2677_dir=args.m2677_dir,
        m2680_dir=args.m2680_dir,
        output_dir=args.output_dir,
        doc_path=args.doc_path,
        follow_up_manifest=args.follow_up_manifest,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['paths']['summary']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"blocker_rows={summary['role_task_quality_blocker_row_count']}")
    print(f"candidate_rows={summary['repair_candidate_row_count']}")
    print(f"excluded_rows={summary['excluded_candidate_row_count']}")
    print(f"proposed_subset_rows={summary['proposed_measured_subset_row_count']}")
    print(f"next={summary['next_blocker']}")
    return 0 if summary["status_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
