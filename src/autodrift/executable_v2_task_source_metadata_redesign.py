"""Support-first task/source metadata helper for executable v2."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json


CONTRACT_ID = "executable_v2_support_first_task_source_v1"
ROLE_STABLE_AES = "stable_aes_only"
ROLE_STABLE_AEB = "stable_aeb"
ROLE_DRIFT_REQUIRED = "drift_required_recovery"
ROLE_UNAVOIDABLE = "unavoidable_mitigation"
SUPPORTED = "supported"
UNSUPPORTED = "unsupported"
UNKNOWN = "unknown"
INVALID = "invalid"
FAIL_NONE = "none"
FAIL_NO_ACCEPTED = "no_accepted_cells"
FAIL_LABEL_ROLE_MISMATCH = "label_role_mismatch"
FAIL_MISSING_EVIDENCE = "missing_support_artifact"
FAIL_METADATA_JOIN = "metadata_join_incomplete"
FAIL_CLAIM_CONTEXT = "claim_boundary_context_invalid"
BLOCK_NONE = "none"
BLOCK_UNSUPPORTED = "source_support_not_supported"
BLOCK_UNKNOWN = "source_support_unknown"
BLOCK_INVALID = "source_support_invalid"
CLAIM_CONTEXTS = (
    "implementation_only",
    "project_artifact_execution",
    "result_audit",
    "branch_synthesis",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
    "policy_action_executed",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"true", "1", "yes", "y"}:
            return True
        if stripped in {"false", "0", "no", "n", ""}:
            return False
    return default


def _int(value: Any, *, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(float(value))


def _json_counts(counts: Mapping[str, int]) -> str:
    return json.dumps(dict(sorted((str(k), int(v)) for k, v in counts.items())), sort_keys=True)


def _parse_json_counts(value: Any) -> dict[str, int]:
    if isinstance(value, Mapping):
        return {str(key): int(item) for key, item in value.items()}
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, Mapping):
        return {}
    return {str(key): int(item) for key, item in payload.items()}


def _read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _guardrail_flags() -> dict[str, bool]:
    return {key: False for key in FORBIDDEN_GUARDRAILS}


def _source_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get(
            "source_v1_bounded_panel_spec_id",
            row.get(
                "source_scenario_spec_id",
                row.get("source_id", ""),
            ),
        )
    )


def role_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "support_contract_id": CONTRACT_ID,
            "source_role_semantics": ROLE_STABLE_AES,
            "source_required_label": "aes_feasible",
            "source_allowed_labels": "aes_feasible",
            "requires_all_profiles_supported": True,
            "requires_accepted_cells": True,
            "materialization_role": "stable AES only",
        },
        {
            "support_contract_id": CONTRACT_ID,
            "source_role_semantics": ROLE_STABLE_AEB,
            "source_required_label": "aeb_feasible",
            "source_allowed_labels": "aeb_feasible",
            "requires_all_profiles_supported": True,
            "requires_accepted_cells": False,
            "materialization_role": "AEB only",
        },
        {
            "support_contract_id": CONTRACT_ID,
            "source_role_semantics": ROLE_DRIFT_REQUIRED,
            "source_required_label": "drift_required",
            "source_allowed_labels": "drift_required",
            "requires_all_profiles_supported": False,
            "requires_accepted_cells": False,
            "materialization_role": "drift-required recovery",
        },
        {
            "support_contract_id": CONTRACT_ID,
            "source_role_semantics": ROLE_UNAVOIDABLE,
            "source_required_label": "unavoidable",
            "source_allowed_labels": "unavoidable",
            "requires_all_profiles_supported": False,
            "requires_accepted_cells": False,
            "materialization_role": "unavoidable mitigation",
        },
    ]


def role_contract_by_semantics() -> dict[str, dict[str, Any]]:
    return {row["source_role_semantics"]: row for row in role_contract_rows()}


def aggregate_support_by_source(
    *,
    profile_rows: Iterable[Mapping[str, Any]],
    label_count_rows: Iterable[Mapping[str, Any]] | None = None,
    reject_reason_rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    grouped_profiles: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    reject_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in profile_rows:
        grouped_profiles[_source_key(row)].append(row)
    for row in label_count_rows or []:
        label_counts[_source_key(row)][str(row.get("label", ""))] += _int(row.get("count"))
    for row in reject_reason_rows or []:
        reject_counts[_source_key(row)][str(row.get("reject_reason", ""))] += _int(row.get("count"))

    output: dict[str, dict[str, Any]] = {}
    for source_key, rows in grouped_profiles.items():
        accepted_total = sum(_int(row.get("accepted_cell_count")) for row in rows)
        feasible_profiles = sum(_bool(row.get("feasible")) for row in rows)
        labels = dict(label_counts.get(source_key, Counter()))
        rejects = dict(reject_counts.get(source_key, Counter()))
        if not labels:
            labels = dict(Counter(str(row.get("dominant_label", "")) for row in rows if row.get("dominant_label", "")))
        if not rejects:
            rejects = dict(
                Counter(str(row.get("dominant_reject_reason", "")) for row in rows if row.get("dominant_reject_reason", ""))
            )
        output[source_key] = {
            "source_v1_bounded_panel_spec_id": source_key,
            "source_scenario_spec_id": rows[0].get("source_scenario_spec_id", "") if rows else "",
            "source_support_profile_count": len(rows),
            "source_support_feasible_profile_count": int(feasible_profiles),
            "source_support_accepted_cell_count_total": int(accepted_total),
            "source_support_label_counts": labels,
            "source_support_reject_reason_counts": rejects,
        }
    return output


def _status_from_support(
    *,
    role: Mapping[str, Any],
    support: Mapping[str, Any] | None,
) -> tuple[str, str]:
    if support is None:
        return UNKNOWN, FAIL_MISSING_EVIDENCE
    required_label = str(role["source_required_label"])
    label_counts = dict(support.get("source_support_label_counts", {}))
    profile_count = _int(support.get("source_support_profile_count"))
    feasible_profiles = _int(support.get("source_support_feasible_profile_count"))
    accepted_total = _int(support.get("source_support_accepted_cell_count_total"))
    if profile_count <= 0:
        return UNKNOWN, FAIL_MISSING_EVIDENCE
    if int(label_counts.get(required_label, 0)) <= 0:
        return UNSUPPORTED, FAIL_LABEL_ROLE_MISMATCH
    if _bool(role.get("requires_accepted_cells")) and accepted_total <= 0:
        return UNSUPPORTED, FAIL_NO_ACCEPTED
    if _bool(role.get("requires_all_profiles_supported")) and feasible_profiles < profile_count:
        return UNSUPPORTED, FAIL_NO_ACCEPTED
    return SUPPORTED, FAIL_NONE


def build_support_contract_rows(
    *,
    source_rows: Iterable[Mapping[str, Any]],
    support_by_source: Mapping[str, Mapping[str, Any]],
    support_evidence_artifact: str = "",
    support_evidence_stage: str = "pre_materialization_scan",
    claim_boundary_context: str = "implementation_only",
) -> list[dict[str, Any]]:
    roles = role_contract_by_semantics()
    output: list[dict[str, Any]] = []
    for source in source_rows:
        source_key = _source_key(source)
        role_name = str(source.get("source_role_semantics", source.get("v2_role_surface_id", "")))
        role = roles.get(role_name)
        if role is None:
            support = support_by_source.get(source_key)
            status = INVALID
            failure = FAIL_METADATA_JOIN
            required_label = str(source.get("source_required_label", ""))
            allowed_labels = str(source.get("source_allowed_labels", ""))
        else:
            support = support_by_source.get(source_key)
            status, failure = _status_from_support(role=role, support=support)
            required_label = str(role["source_required_label"])
            allowed_labels = str(role["source_allowed_labels"])
        support = support or {}
        if claim_boundary_context not in CLAIM_CONTEXTS:
            status = INVALID
            failure = FAIL_CLAIM_CONTEXT
        materialization_admissible = status == SUPPORTED
        if materialization_admissible:
            block_reason = BLOCK_NONE
        elif status == UNKNOWN:
            block_reason = BLOCK_UNKNOWN
        elif status == INVALID:
            block_reason = BLOCK_INVALID
        else:
            block_reason = BLOCK_UNSUPPORTED
        output.append(
            {
                "support_contract_id": CONTRACT_ID,
                "source_v1_bounded_panel_spec_id": source_key,
                "source_scenario_spec_id": source.get("source_scenario_spec_id", support.get("source_scenario_spec_id", "")),
                "source_role_semantics": role_name,
                "source_required_label": required_label,
                "source_allowed_labels": allowed_labels,
                "source_support_status": status,
                "source_support_evidence_artifact": support_evidence_artifact,
                "source_support_evidence_stage": support_evidence_stage,
                "source_support_profile_count": _int(support.get("source_support_profile_count")),
                "source_support_feasible_profile_count": _int(support.get("source_support_feasible_profile_count")),
                "source_support_accepted_cell_count_total": _int(
                    support.get("source_support_accepted_cell_count_total")
                ),
                "source_support_label_counts": _json_counts(_parse_json_counts(support.get("source_support_label_counts", {}))),
                "source_support_reject_reason_counts": _json_counts(
                    _parse_json_counts(support.get("source_support_reject_reason_counts", {}))
                ),
                "source_support_failure_reason": failure,
                "materialization_admissible": materialization_admissible,
                "materialization_block_reason": block_reason,
                "labels_enter_actor_input": _bool(source.get("labels_enter_actor_input")),
                "v2_ranking_admissible_by_default": _bool(source.get("v2_ranking_admissible_by_default")),
                "claim_boundary_context": claim_boundary_context,
            }
        )
    return sorted(output, key=lambda row: (str(row["source_v1_bounded_panel_spec_id"]), str(row["source_role_semantics"])))


def source_rows_from_profile_summary(
    *,
    profile_summary_rows: Iterable[Mapping[str, Any]],
    default_role: str = ROLE_STABLE_AES,
) -> list[dict[str, Any]]:
    rows_by_source: dict[str, dict[str, Any]] = {}
    for row in profile_summary_rows:
        source_key = _source_key(row)
        if not source_key or source_key in rows_by_source:
            continue
        rows_by_source[source_key] = {
            "source_v1_bounded_panel_spec_id": source_key,
            "source_scenario_spec_id": row.get("source_scenario_spec_id", ""),
            "source_role_semantics": default_role,
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
        }
    return sorted(rows_by_source.values(), key=lambda row: str(row["source_v1_bounded_panel_spec_id"]))


def claim_boundary_rows(context: str = "implementation_only") -> list[dict[str, Any]]:
    if context not in CLAIM_CONTEXTS:
        raise ValueError(f"unknown claim boundary context: {context}")
    project_execution = context == "project_artifact_execution"
    result_audit = context in {"result_audit", "branch_synthesis"}
    return [
        {
            "claim_context": context,
            "claim": "metadata_helper_implementation",
            "admissible": context == "implementation_only",
            "reason": "helper implementation is admissible only in implementation context",
        },
        {
            "claim_context": context,
            "claim": "project_artifact_execution",
            "admissible": project_execution,
            "reason": "project artifact execution requires an execution milestone",
        },
        {
            "claim_context": context,
            "claim": "result_audit",
            "admissible": result_audit,
            "reason": "result claims require audit or synthesis context",
        },
        {
            "claim_context": context,
            "claim": "source_repair_payload_generated",
            "admissible": False,
            "reason": "metadata redesign does not generate repair payloads",
        },
        {
            "claim_context": context,
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "metadata redesign is task-quality infrastructure, not ranking evidence",
        },
    ]


def run_task_source_metadata_redesign(
    *,
    source_rows: list[Mapping[str, Any]],
    profile_summary_rows: list[Mapping[str, Any]],
    label_count_rows: list[Mapping[str, Any]] | None = None,
    reject_reason_rows: list[Mapping[str, Any]] | None = None,
    output_dir: Path | str,
    support_evidence_artifact: str = "",
    support_evidence_stage: str = "pre_materialization_scan",
    claim_boundary_context: str = "implementation_only",
    next_blocker: str = "m1848-executable-v2-task-source-metadata-redesign-execution-design",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    support_by_source = aggregate_support_by_source(
        profile_rows=profile_summary_rows,
        label_count_rows=label_count_rows or [],
        reject_reason_rows=reject_reason_rows or [],
    )
    support_rows = build_support_contract_rows(
        source_rows=source_rows,
        support_by_source=support_by_source,
        support_evidence_artifact=support_evidence_artifact,
        support_evidence_stage=support_evidence_stage,
        claim_boundary_context=claim_boundary_context,
    )
    admissibility_rows = [
        {
            "source_v1_bounded_panel_spec_id": row["source_v1_bounded_panel_spec_id"],
            "source_role_semantics": row["source_role_semantics"],
            "source_support_status": row["source_support_status"],
            "materialization_admissible": row["materialization_admissible"],
            "materialization_block_reason": row["materialization_block_reason"],
            "source_support_failure_reason": row["source_support_failure_reason"],
        }
        for row in support_rows
    ]
    blocked_rows = [row for row in support_rows if not _bool(row.get("materialization_admissible"))]
    labels_enter_actor_input_count = sum(_bool(row.get("labels_enter_actor_input")) for row in support_rows)
    ranking_admissible_by_default_count = sum(_bool(row.get("v2_ranking_admissible_by_default")) for row in support_rows)
    guardrail_flags = _guardrail_flags()
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))

    write_csv_rows(output / "task_source_support_contract.csv", support_rows)
    write_csv_rows(output / "task_source_role_contract.csv", role_contract_rows())
    write_csv_rows(output / "task_source_materialization_admissibility.csv", admissibility_rows)
    write_csv_rows(output / "task_source_blocked_sources.csv", blocked_rows)
    write_csv_rows(output / "task_source_claim_boundary.csv", claim_boundary_rows(claim_boundary_context))

    status_counts = Counter(str(row.get("source_support_status", "")) for row in support_rows)
    context_counts = Counter(str(row.get("claim_boundary_context", "")) for row in support_rows)
    summary = {
        "contract_id": CONTRACT_ID,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "support_evidence_artifact": support_evidence_artifact,
        "support_evidence_stage": support_evidence_stage,
        "claim_boundary_context": claim_boundary_context,
        "input_source_count": len(support_rows),
        "input_profile_count": len(profile_summary_rows),
        "supported_source_count": int(status_counts.get(SUPPORTED, 0)),
        "unsupported_source_count": int(status_counts.get(UNSUPPORTED, 0)),
        "unknown_source_count": int(status_counts.get(UNKNOWN, 0)),
        "invalid_source_count": int(status_counts.get(INVALID, 0)),
        "materialization_admissible_source_count": sum(_bool(row.get("materialization_admissible")) for row in support_rows),
        "materialization_blocked_source_count": len(blocked_rows),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_admissible_by_default_count),
        "claim_boundary_context_count": dict(sorted(context_counts.items())),
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "task_source_support_contract": str(output / "task_source_support_contract.csv"),
            "task_source_role_contract": str(output / "task_source_role_contract.csv"),
            "task_source_materialization_admissibility": str(
                output / "task_source_materialization_admissibility.csv"
            ),
            "task_source_blocked_sources": str(output / "task_source_blocked_sources.csv"),
            "task_source_claim_boundary": str(output / "task_source_claim_boundary.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def run_task_source_metadata_redesign_from_paths(
    *,
    source_rows_path: Path | str | None,
    profile_summary_path: Path | str,
    output_dir: Path | str,
    label_counts_path: Path | str | None = None,
    reject_reason_counts_path: Path | str | None = None,
    support_evidence_artifact: str = "",
    support_evidence_stage: str = "pre_materialization_scan",
    claim_boundary_context: str = "project_artifact_execution",
    default_source_role: str = ROLE_STABLE_AES,
    next_blocker: str = "m1848-executable-v2-task-source-metadata-redesign-execution-design",
) -> dict[str, Any]:
    profile_summary_rows = _read_csv_rows(profile_summary_path)
    source_rows = (
        _read_csv_rows(source_rows_path)
        if source_rows_path
        else source_rows_from_profile_summary(profile_summary_rows=profile_summary_rows, default_role=default_source_role)
    )
    return run_task_source_metadata_redesign(
        source_rows=source_rows,
        profile_summary_rows=profile_summary_rows,
        label_count_rows=_read_csv_rows(label_counts_path) if label_counts_path else [],
        reject_reason_rows=_read_csv_rows(reject_reason_counts_path) if reject_reason_counts_path else [],
        output_dir=output_dir,
        support_evidence_artifact=support_evidence_artifact,
        support_evidence_stage=support_evidence_stage,
        claim_boundary_context=claim_boundary_context,
        next_blocker=next_blocker,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rows", type=Path, default=None)
    parser.add_argument("--profile-summary", type=Path, required=True)
    parser.add_argument("--label-counts", type=Path, default=None)
    parser.add_argument("--reject-reason-counts", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--support-evidence-artifact", default="")
    parser.add_argument("--support-evidence-stage", default="pre_materialization_scan")
    parser.add_argument("--claim-boundary-context", default="project_artifact_execution")
    parser.add_argument("--default-source-role", default=ROLE_STABLE_AES)
    parser.add_argument("--next-blocker", default="m1848-executable-v2-task-source-metadata-redesign-execution-design")
    args = parser.parse_args()
    summary = run_task_source_metadata_redesign_from_paths(
        source_rows_path=args.source_rows,
        profile_summary_path=args.profile_summary,
        output_dir=args.output_dir,
        label_counts_path=args.label_counts,
        reject_reason_counts_path=args.reject_reason_counts,
        support_evidence_artifact=args.support_evidence_artifact,
        support_evidence_stage=args.support_evidence_stage,
        claim_boundary_context=args.claim_boundary_context,
        default_source_role=str(args.default_source_role),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={summary['artifacts']['summary']}")
    print(f"contract_id={summary['contract_id']}")
    print(f"input_source_count={summary['input_source_count']}")
    print(f"materialization_admissible_source_count={summary['materialization_admissible_source_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
