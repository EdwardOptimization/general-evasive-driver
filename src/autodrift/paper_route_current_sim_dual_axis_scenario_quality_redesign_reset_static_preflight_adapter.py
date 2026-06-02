"""Reset/static preflight adapter for M2455 scenario-quality protocol rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_M2455_DIR = Path(
    "runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight"
)
DEFAULT_M2455_SUMMARY = DEFAULT_M2455_DIR / "summary.json"
DEFAULT_CANDIDATE_ROWS = DEFAULT_M2455_DIR / "candidate_rows.csv"
DEFAULT_ROLE_PROTOCOL_ROWS = DEFAULT_M2455_DIR / "role_protocol_rows.csv"
DEFAULT_GEOMETRY_LEVER_ROWS = DEFAULT_M2455_DIR / "geometry_lever_rows.csv"
DEFAULT_GUARDRAIL_ROWS = DEFAULT_M2455_DIR / "guardrail_rows.csv"
DEFAULT_CLAIM_BOUNDARY = DEFAULT_M2455_DIR / "claim_boundary.csv"
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter"
)
DEFAULT_NEXT_BLOCKER = (
    "m2459-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-adapter-result-audit"
)

RESULT_STATIC_PASS_RESET_BLOCKED = (
    "scenario_quality_redesign_reset_static_preflight_adapter_static_pass_reset_blocked"
)
RESULT_RESET_PASS = "scenario_quality_redesign_reset_static_preflight_adapter_reset_pass"
RESULT_FAIL = "scenario_quality_redesign_reset_static_preflight_adapter_fail"

RESET_REQUIRED_GROUPS = {"stable_feasibility_support", "stable_aes_support"}
ALLOWED_SPLITS = {"public_debug", "public_gate"}
ALLOWED_OVERLAY_KEYS = {
    "track_width",
    "soft_offtrack_metric_enabled",
    "soft_offtrack_tolerance_m",
    "speed_range",
    "friction_limited_speed",
    "obstacle.enabled",
    "obstacle.distance_range",
    "obstacle.lateral_offset_range",
    "obstacle.half_width_range",
    "obstacle.allowed_labels",
    "obstacle.require_aeb_infeasible",
    "obstacle.max_threshold_score",
    "obstacle.perception_reveal_distance",
    "obstacle.perception_reveal_step",
    "obstacle.finish_on_pass",
    "obstacle.finish_pass_distance",
    "obstacle.max_sample_attempts",
}

WORK_ITEM_FIELDNAMES = [
    "preflight_id",
    "source_candidate_id",
    "source_panel_id",
    "candidate_group",
    "role_scope",
    "sampled_obstacle_label_scope",
    "split",
    "preflight_lane",
    "intended_evidence_role",
    "geometry_lever_class",
    "boundary_protocol_class",
    "static_check_required",
    "reset_check_required",
    "concrete_overlay_required",
    "concrete_overlay_available",
    "concrete_overlay_source",
    "env_config_overlay_json",
    "blocked_reason",
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "policy_action_executed",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]

STATIC_CHECK_FIELDNAMES = [
    "check_id",
    "preflight_id",
    "check_scope",
    "check_name",
    "value",
    "passed",
    "failure_type",
    "reason",
]

RESET_CHECK_FIELDNAMES = [
    "preflight_id",
    "reset_attempted",
    "reset_success",
    "observation_shape_unchanged",
    "blocked_reason",
    "failure_type",
    "reason",
]

OVERLAY_REQUIREMENT_FIELDNAMES = [
    "preflight_id",
    "candidate_group",
    "concrete_overlay_required",
    "concrete_overlay_available",
    "required_overlay_keys",
    "allowed_overlay_keys",
    "blocked_reason",
]

GUARDRAIL_FIELDNAMES = [
    "guardrail_id",
    "guardrail_class",
    "source_role_or_axis",
    "failure_mode_to_preserve",
    "metric_to_watch",
    "value",
    "violation",
    "reason",
]

CLAIM_FIELDNAMES = [
    "claim_key",
    "claim_value",
    "admissible",
    "reason",
]

DECISION_FIELDNAMES = [
    "decision_key",
    "decision_value",
    "admissible",
    "reason",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _overlay_from_row(row: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    for key in ("env_config_overlay_json", "concrete_env_overlay_json", "env_config"):
        raw = str(row.get(key, "")).strip()
        if raw and raw not in {"{}", "null", "None"}:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError(f"{key} must decode to an object")
            return parsed, key
    return {}, ""


def _flatten_overlay_keys(data: Mapping[str, Any], prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        flat_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            keys.update(_flatten_overlay_keys(value, flat_key))
        else:
            keys.add(flat_key)
    return keys


def _role_map(role_rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    roles: dict[str, Mapping[str, Any]] = {str(row.get("candidate_group", "")): row for row in role_rows}
    roles.setdefault(
        "geometry_timing_guardrail",
        {
            "candidate_group": "geometry_timing_guardrail",
            "role_scope": "geometry_timing_guardrail",
            "sampled_obstacle_label_scope": "metadata_only",
        },
    )
    return roles


def _evidence_role(group: str) -> str:
    if group == "stable_feasibility_support":
        return "stable road-contained obstacle-avoidance support"
    if group == "stable_aes_support":
        return "AEB-infeasible stable AES support"
    if group == "geometry_timing_guardrail":
        return "timing and lateral-offset distribution guardrail"
    if group == "handling_limit_guardrail":
        return "handling-limit and drift-required guardrail"
    if group == "hidden_dynamics_guardrail":
        return "hidden-dynamics metadata-only stress guardrail"
    if group == "mitigation_guardrail":
        return "unavoidable mitigation isolation guardrail"
    return "unclassified scenario-quality guardrail"


def build_preflight_work_items(
    candidate_rows: Sequence[Mapping[str, Any]],
    role_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    roles = _role_map(role_rows)
    work_items: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_rows, start=1):
        group = str(candidate.get("candidate_group", ""))
        role = roles.get(group, {})
        overlay, overlay_source = _overlay_from_row(candidate)
        overlay_keys = _flatten_overlay_keys(overlay)
        unknown_overlay_keys = sorted(overlay_keys - ALLOWED_OVERLAY_KEYS)
        concrete_overlay_available = bool(overlay) and not unknown_overlay_keys
        concrete_overlay_required = group in RESET_REQUIRED_GROUPS
        reset_check_required = concrete_overlay_required or bool(overlay)
        if reset_check_required and concrete_overlay_available:
            lane = "static_then_reset"
            blocked_reason = ""
        elif reset_check_required:
            lane = "reset_blocked"
            blocked_reason = (
                "reset_blocked_unknown_overlay_keys"
                if unknown_overlay_keys
                else "reset_blocked_missing_concrete_overlay"
            )
        else:
            lane = "static_only"
            blocked_reason = ""
        preflight_id = f"m2458_preflight_{index:03d}"
        work_items.append(
            {
                "preflight_id": preflight_id,
                "source_candidate_id": str(candidate.get("candidate_id", "")),
                "source_panel_id": str(candidate.get("source_panel_id", "")),
                "candidate_group": group,
                "role_scope": str(role.get("role_scope", "")),
                "sampled_obstacle_label_scope": str(
                    candidate.get("sampled_obstacle_label") or role.get("sampled_obstacle_label_scope", "")
                ),
                "split": str(candidate.get("split", "")),
                "preflight_lane": lane,
                "intended_evidence_role": _evidence_role(group),
                "geometry_lever_class": str(candidate.get("geometry_lever_class", "")),
                "boundary_protocol_class": str(candidate.get("boundary_protocol_class", "")),
                "static_check_required": True,
                "reset_check_required": reset_check_required,
                "concrete_overlay_required": concrete_overlay_required,
                "concrete_overlay_available": concrete_overlay_available,
                "concrete_overlay_source": overlay_source,
                "env_config_overlay_json": json.dumps(overlay, sort_keys=True) if overlay else "",
                "blocked_reason": blocked_reason,
                "labels_enter_actor_input": _bool(candidate.get("labels_enter_actor_input")),
                "actor_input_contract_changed": _bool(candidate.get("actor_input_contract_changed")),
                "scenario_redesign_executed": _bool(candidate.get("scenario_redesign_executed")),
                "policy_action_executed": _bool(candidate.get("policy_action_executed")),
                "repair_execution_started": _bool(candidate.get("repair_execution_started")),
                "training_started": _bool(candidate.get("training_started")),
                "ranking_admissible": _bool(candidate.get("ranking_admissible")),
                "winner_selected": _bool(candidate.get("winner_selected")),
            }
        )
    return work_items


def _check_row(
    rows: list[dict[str, Any]],
    *,
    check_id: str,
    preflight_id: str,
    check_scope: str,
    check_name: str,
    value: Any,
    passed: bool,
    failure_type: str,
    reason: str,
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "preflight_id": preflight_id,
            "check_scope": check_scope,
            "check_name": check_name,
            "value": value,
            "passed": passed,
            "failure_type": "" if passed else failure_type,
            "reason": reason,
        }
    )


def static_check_rows(
    *,
    m2455_summary: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    role_rows: Sequence[Mapping[str, Any]],
    geometry_lever_rows: Sequence[Mapping[str, Any]],
    source_guardrail_rows: Sequence[Mapping[str, Any]],
    source_claim_rows: Sequence[Mapping[str, Any]],
    work_items: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_result = str(m2455_summary.get("result_class", ""))
    _check_row(
        rows,
        check_id="m2458_global_source_result_pass",
        preflight_id="global",
        check_scope="source",
        check_name="m2455_summary_result_pass",
        value=source_result,
        passed=source_result.endswith("_pass"),
        failure_type="lineage_invalid",
        reason="M2458 requires a passing M2455 materialization summary.",
    )
    _check_row(
        rows,
        check_id="m2458_global_all_candidates_covered",
        preflight_id="global",
        check_scope="source",
        check_name="candidate_coverage",
        value=f"{len(work_items)}/{len(candidates)}",
        passed=len(work_items) == len(candidates) and len(candidates) > 0,
        failure_type="lineage_invalid",
        reason="Every M2455 candidate row must produce one preflight work item.",
    )
    duplicate_ids = len({str(row.get("preflight_id", "")) for row in work_items}) != len(work_items)
    _check_row(
        rows,
        check_id="m2458_global_unique_preflight_ids",
        preflight_id="global",
        check_scope="source",
        check_name="unique_preflight_ids",
        value=not duplicate_ids,
        passed=not duplicate_ids,
        failure_type="lineage_invalid",
        reason="Preflight work items must have unique IDs.",
    )
    source_guardrail_violation_count = _flag_count(source_guardrail_rows, "violation")
    _check_row(
        rows,
        check_id="m2458_global_source_guardrails",
        preflight_id="global",
        check_scope="guardrail",
        check_name="source_guardrail_violation_count",
        value=source_guardrail_violation_count,
        passed=source_guardrail_violation_count == 0,
        failure_type="contract_violation",
        reason="M2455 guardrail rows must remain nonviolating.",
    )
    claim_blocked = {
        str(row.get("claim_key", "")): str(row.get("claim_value", ""))
        for row in source_claim_rows
        if str(row.get("claim_value", "")) == "blocked"
    }
    _check_row(
        rows,
        check_id="m2458_global_claim_boundary",
        preflight_id="global",
        check_scope="claim_boundary",
        check_name="blocked_claim_rows_present",
        value=len(claim_blocked),
        passed=len(claim_blocked) >= 3,
        failure_type="metric_artifact",
        reason="Unsupported performance, paper, and current-sim claims must remain blocked.",
    )
    bounded_lever_violations = [row for row in geometry_lever_rows if not _bool(row.get("bounded"))]
    _check_row(
        rows,
        check_id="m2458_global_bounded_geometry_levers",
        preflight_id="global",
        check_scope="geometry",
        check_name="bounded_geometry_lever_violations",
        value=len(bounded_lever_violations),
        passed=not bounded_lever_violations,
        failure_type="scenario_sampling_failure",
        reason="Geometry levers must stay bounded before reset/static preflight.",
    )
    roles = _role_map(role_rows)
    for item in work_items:
        preflight_id = str(item.get("preflight_id", ""))
        group = str(item.get("candidate_group", ""))
        checks = [
            (
                "group_has_role",
                group in roles,
                "scenario_sampling_failure",
                "Candidate group must map to a role protocol row.",
                group,
            ),
            (
                "split_allowed",
                str(item.get("split", "")) in ALLOWED_SPLITS,
                "scenario_sampling_failure",
                "Candidate split must remain public_debug or public_gate.",
                item.get("split", ""),
            ),
            (
                "labels_not_actor_input",
                not _bool(item.get("labels_enter_actor_input")),
                "contract_violation",
                "Labels must remain metadata-only and out of actor input.",
                item.get("labels_enter_actor_input", ""),
            ),
            (
                "actor_input_contract_unchanged",
                not _bool(item.get("actor_input_contract_changed")),
                "contract_violation",
                "Actor input contract must remain unchanged.",
                item.get("actor_input_contract_changed", ""),
            ),
            (
                "no_scenario_redesign_execution",
                not _bool(item.get("scenario_redesign_executed")),
                "contract_violation",
                "Adapter materialization is not scenario redesign execution.",
                item.get("scenario_redesign_executed", ""),
            ),
            (
                "no_policy_action",
                not _bool(item.get("policy_action_executed")),
                "contract_violation",
                "M2458 must not execute policy actions.",
                item.get("policy_action_executed", ""),
            ),
            (
                "no_repair_training",
                not (_bool(item.get("repair_execution_started")) or _bool(item.get("training_started"))),
                "contract_violation",
                "M2458 must not execute repair or training.",
                f"{item.get('repair_execution_started')}|{item.get('training_started')}",
            ),
            (
                "no_ranking_or_winner",
                not (_bool(item.get("ranking_admissible")) or _bool(item.get("winner_selected"))),
                "metric_artifact",
                "M2458 must not rank candidates or select winners.",
                f"{item.get('ranking_admissible')}|{item.get('winner_selected')}",
            ),
        ]
        for check_index, (name, passed, failure_type, reason, value) in enumerate(checks, start=1):
            _check_row(
                rows,
                check_id=f"{preflight_id}_{check_index:02d}_{name}",
                preflight_id=preflight_id,
                check_scope="work_item",
                check_name=name,
                value=value,
                passed=bool(passed),
                failure_type=failure_type,
                reason=reason,
            )
    return rows


def reset_check_rows(work_items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in work_items:
        reset_required = _bool(item.get("reset_check_required"))
        overlay_available = _bool(item.get("concrete_overlay_available"))
        blocked_reason = str(item.get("blocked_reason", ""))
        if not reset_required:
            rows.append(
                {
                    "preflight_id": item.get("preflight_id", ""),
                    "reset_attempted": False,
                    "reset_success": False,
                    "observation_shape_unchanged": False,
                    "blocked_reason": "",
                    "failure_type": "",
                    "reason": "Reset not required for this static-only guardrail item.",
                }
            )
        elif not overlay_available:
            rows.append(
                {
                    "preflight_id": item.get("preflight_id", ""),
                    "reset_attempted": False,
                    "reset_success": False,
                    "observation_shape_unchanged": False,
                    "blocked_reason": blocked_reason or "reset_blocked_missing_concrete_overlay",
                    "failure_type": "scenario_sampling_failure",
                    "reason": "Reset is blocked until a concrete numeric env overlay is attached.",
                }
            )
        else:
            rows.append(
                {
                    "preflight_id": item.get("preflight_id", ""),
                    "reset_attempted": False,
                    "reset_success": False,
                    "observation_shape_unchanged": False,
                    "blocked_reason": "reset_execution_not_enabled_in_m2458_adapter",
                    "failure_type": "scenario_sampling_failure",
                    "reason": "Concrete overlay is present but M2458 keeps reset execution disabled until result audit admits it.",
                }
            )
    return rows


def overlay_requirement_rows(work_items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    stable_required = "obstacle.distance_range|obstacle.lateral_offset_range|obstacle.half_width_range|speed_range"
    return [
        {
            "preflight_id": item.get("preflight_id", ""),
            "candidate_group": item.get("candidate_group", ""),
            "concrete_overlay_required": item.get("concrete_overlay_required", ""),
            "concrete_overlay_available": item.get("concrete_overlay_available", ""),
            "required_overlay_keys": stable_required if _bool(item.get("concrete_overlay_required")) else "",
            "allowed_overlay_keys": "|".join(sorted(ALLOWED_OVERLAY_KEYS)),
            "blocked_reason": item.get("blocked_reason", ""),
        }
        for item in work_items
    ]


def guardrail_rows(
    *,
    work_items: Sequence[Mapping[str, Any]],
    static_rows: Sequence[Mapping[str, Any]],
    reset_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    static_fail_count = sum(not _bool(row.get("passed")) for row in static_rows)
    reset_attempted_count = _flag_count(reset_rows, "reset_attempted")
    reset_blocked_missing_count = sum(
        str(row.get("blocked_reason", "")) == "reset_blocked_missing_concrete_overlay" for row in reset_rows
    )
    guards = [
        (
            "m2458_static_checks_pass",
            "static_validation",
            "all_work_items",
            "contract_violation",
            "static_check_fail_count",
            static_fail_count,
            static_fail_count != 0,
            "All static checks must pass before any later reset or rollout route.",
        ),
        (
            "m2458_no_policy_action",
            "claim_boundary",
            "work_items",
            "contract_violation",
            "policy_action_executed_count",
            _flag_count(work_items, "policy_action_executed"),
            _flag_count(work_items, "policy_action_executed") != 0,
            "Preflight adapter must not execute policy actions.",
        ),
        (
            "m2458_no_actor_input_change",
            "claim_boundary",
            "work_items",
            "contract_violation",
            "actor_input_contract_changed_count",
            _flag_count(work_items, "actor_input_contract_changed"),
            _flag_count(work_items, "actor_input_contract_changed") != 0,
            "Actor input contract must remain unchanged.",
        ),
        (
            "m2458_no_ranking_or_winner",
            "claim_boundary",
            "work_items",
            "metric_artifact",
            "ranking_or_winner_count",
            _flag_count(work_items, "ranking_admissible") + _flag_count(work_items, "winner_selected"),
            (_flag_count(work_items, "ranking_admissible") + _flag_count(work_items, "winner_selected")) != 0,
            "No candidate ranking or winner selection is allowed.",
        ),
        (
            "m2458_reset_missing_overlay_classified",
            "reset_readiness",
            "reset_required_work_items",
            "scenario_sampling_failure",
            "reset_blocked_missing_concrete_overlay_count",
            reset_blocked_missing_count,
            False,
            "Missing concrete overlays are classified fail-closed rather than inferred unsafely.",
        ),
        (
            "m2458_no_reset_execution_without_audit",
            "claim_boundary",
            "reset_checks",
            "contract_violation",
            "reset_attempted_count",
            reset_attempted_count,
            reset_attempted_count != 0,
            "M2458 adapter records reset readiness but does not execute reset before result audit.",
        ),
    ]
    return [
        {
            "guardrail_id": guardrail_id,
            "guardrail_class": guardrail_class,
            "source_role_or_axis": axis,
            "failure_mode_to_preserve": failure_mode,
            "metric_to_watch": metric,
            "value": value,
            "violation": violation,
            "reason": reason,
        }
        for guardrail_id, guardrail_class, axis, failure_mode, metric, value, violation, reason in guards
    ]


def claim_boundary_rows(*, reset_attempted_count: int) -> list[dict[str, Any]]:
    return [
        {
            "claim_key": "reset_validation_started",
            "claim_value": "true" if reset_attempted_count else "false",
            "admissible": True,
            "reason": "Reset validation is allowed only after result audit; M2458 itself does not execute reset.",
        },
        {"claim_key": "measured_rollout_started", "claim_value": "false", "admissible": True, "reason": "No rollout is run."},
        {"claim_key": "policy_action_executed", "claim_value": "false", "admissible": True, "reason": "No policy action is executed."},
        {
            "claim_key": "scenario_redesign_executed",
            "claim_value": "false",
            "admissible": True,
            "reason": "Adapter materialization is preflight infrastructure only.",
        },
        {"claim_key": "repair_training_started", "claim_value": "false", "admissible": True, "reason": "No repair or training is executed."},
        {"claim_key": "ranking_or_winner", "claim_value": "false", "admissible": True, "reason": "No ranking or winner is selected."},
        {
            "claim_key": "actual_success_improvement",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No measured rollout is produced.",
        },
        {
            "claim_key": "paper_or_self_id_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "No controller-family or history-necessity test is run.",
        },
        {
            "claim_key": "current_sim_verdict",
            "claim_value": "blocked",
            "admissible": False,
            "reason": "This is not a final current-sim verdict.",
        },
    ]


def decision_rows(*, next_blocker: str, reset_blocked_missing_count: int, guardrail_violation_count: int) -> list[dict[str, Any]]:
    if guardrail_violation_count:
        next_reason = "Audit failures before any further preflight or execution."
    elif reset_blocked_missing_count:
        next_reason = "Audit reset-blocked missing-overlay evidence before concrete overlay design."
    else:
        next_reason = "Audit adapter result before any reset or measured rollout route."
    return [
        {
            "decision_key": "adapter_static_validation_complete",
            "decision_value": "true" if guardrail_violation_count == 0 else "false",
            "admissible": guardrail_violation_count == 0,
            "reason": "Static checks are complete for all work items.",
        },
        {
            "decision_key": "reset_blocked_missing_concrete_overlay",
            "decision_value": str(reset_blocked_missing_count),
            "admissible": True,
            "reason": "Missing overlays are explicit reset-readiness blockers, not driver failures.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "No repair, training, ranking, or winner selection is executed.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker,
            "admissible": True,
            "reason": next_reason,
        },
    ]


def run_reset_static_preflight_adapter(
    *,
    m2455_summary_path: Path | str = DEFAULT_M2455_SUMMARY,
    candidate_rows_path: Path | str = DEFAULT_CANDIDATE_ROWS,
    role_protocol_rows_path: Path | str = DEFAULT_ROLE_PROTOCOL_ROWS,
    geometry_lever_rows_path: Path | str = DEFAULT_GEOMETRY_LEVER_ROWS,
    source_guardrail_rows_path: Path | str = DEFAULT_GUARDRAIL_ROWS,
    source_claim_boundary_path: Path | str = DEFAULT_CLAIM_BOUNDARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    m2455_summary = read_json(m2455_summary_path)
    candidates = read_csv_rows(candidate_rows_path)
    roles = read_csv_rows(role_protocol_rows_path)
    levers = read_csv_rows(geometry_lever_rows_path)
    source_guards = read_csv_rows(source_guardrail_rows_path)
    source_claims = read_csv_rows(source_claim_boundary_path)

    work_items = build_preflight_work_items(candidates, roles)
    static_rows = static_check_rows(
        m2455_summary=m2455_summary,
        candidates=candidates,
        role_rows=roles,
        geometry_lever_rows=levers,
        source_guardrail_rows=source_guards,
        source_claim_rows=source_claims,
        work_items=work_items,
    )
    reset_rows = reset_check_rows(work_items)
    overlay_rows = overlay_requirement_rows(work_items)
    guards = guardrail_rows(work_items=work_items, static_rows=static_rows, reset_rows=reset_rows)
    guardrail_violation_count = _flag_count(guards, "violation")
    static_fail_count = sum(not _bool(row.get("passed")) for row in static_rows)
    reset_required_count = _flag_count(work_items, "reset_check_required")
    concrete_overlay_available_count = _flag_count(work_items, "concrete_overlay_available")
    reset_attempted_count = _flag_count(reset_rows, "reset_attempted")
    reset_success_count = _flag_count(reset_rows, "reset_success")
    reset_blocked_missing_count = sum(
        str(row.get("blocked_reason", "")) == "reset_blocked_missing_concrete_overlay" for row in reset_rows
    )
    claims = claim_boundary_rows(reset_attempted_count=reset_attempted_count)
    decisions = decision_rows(
        next_blocker=str(next_blocker),
        reset_blocked_missing_count=reset_blocked_missing_count,
        guardrail_violation_count=guardrail_violation_count,
    )
    passes_static = (
        len(candidates) > 0
        and len(work_items) == len(candidates)
        and static_fail_count == 0
        and guardrail_violation_count == 0
    )
    if not passes_static:
        result_class = RESULT_FAIL
    elif reset_required_count > reset_success_count:
        result_class = RESULT_STATIC_PASS_RESET_BLOCKED
    else:
        result_class = RESULT_RESET_PASS

    failure_types = sorted(
        {
            str(row.get("failure_type", ""))
            for row in list(static_rows) + list(reset_rows) + list(guards)
            if str(row.get("failure_type", ""))
            and (
                not _bool(row.get("passed"), default=True)
                or _bool(row.get("violation"))
                or str(row.get("blocked_reason", ""))
                in {"reset_blocked_missing_concrete_overlay", "reset_blocked_unknown_overlay_keys"}
            )
        }
    )
    if result_class == RESULT_STATIC_PASS_RESET_BLOCKED:
        failure_types = sorted(set(failure_types) | {"scenario_sampling_failure"})

    write_csv_rows(output / "preflight_work_items.csv", work_items, fieldnames=WORK_ITEM_FIELDNAMES)
    write_csv_rows(output / "static_check_rows.csv", static_rows, fieldnames=STATIC_CHECK_FIELDNAMES)
    write_csv_rows(output / "reset_check_rows.csv", reset_rows, fieldnames=RESET_CHECK_FIELDNAMES)
    write_csv_rows(output / "overlay_requirement_rows.csv", overlay_rows, fieldnames=OVERLAY_REQUIREMENT_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2455_summary": str(m2455_summary_path),
            "candidate_rows": str(candidate_rows_path),
            "role_protocol_rows": str(role_protocol_rows_path),
            "geometry_lever_rows": str(geometry_lever_rows_path),
            "source_guardrail_rows": str(source_guardrail_rows_path),
            "source_claim_boundary": str(source_claim_boundary_path),
        },
        "source_result_class": str(m2455_summary.get("result_class", "")),
        "source_candidate_row_count": len(candidates),
        "preflight_work_item_count": len(work_items),
        "candidate_group_counts": _count_by(work_items, "candidate_group"),
        "preflight_lane_counts": _count_by(work_items, "preflight_lane"),
        "static_check_row_count": len(static_rows),
        "static_check_pass_count": len(static_rows) - static_fail_count,
        "static_check_fail_count": static_fail_count,
        "reset_required_count": reset_required_count,
        "concrete_overlay_available_count": concrete_overlay_available_count,
        "reset_attempted_count": reset_attempted_count,
        "reset_success_count": reset_success_count,
        "reset_blocked_missing_concrete_overlay_count": reset_blocked_missing_count,
        "labels_enter_actor_input_count": _flag_count(work_items, "labels_enter_actor_input"),
        "actor_input_contract_changed_count": _flag_count(work_items, "actor_input_contract_changed"),
        "scenario_redesign_executed": False,
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "ranking_admissible_count": _flag_count(work_items, "ranking_admissible"),
        "winner_selected_count": _flag_count(work_items, "winner_selected"),
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "preflight_work_items": str(output / "preflight_work_items.csv"),
            "static_check_rows": str(output / "static_check_rows.csv"),
            "reset_check_rows": str(output / "reset_check_rows.csv"),
            "overlay_requirement_rows": str(output / "overlay_requirement_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2455-summary", type=Path, default=DEFAULT_M2455_SUMMARY)
    parser.add_argument("--candidate-rows", type=Path, default=DEFAULT_CANDIDATE_ROWS)
    parser.add_argument("--role-protocol-rows", type=Path, default=DEFAULT_ROLE_PROTOCOL_ROWS)
    parser.add_argument("--geometry-lever-rows", type=Path, default=DEFAULT_GEOMETRY_LEVER_ROWS)
    parser.add_argument("--source-guardrail-rows", type=Path, default=DEFAULT_GUARDRAIL_ROWS)
    parser.add_argument("--source-claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_reset_static_preflight_adapter(
        m2455_summary_path=args.m2455_summary,
        candidate_rows_path=args.candidate_rows,
        role_protocol_rows_path=args.role_protocol_rows,
        geometry_lever_rows_path=args.geometry_lever_rows,
        source_guardrail_rows_path=args.source_guardrail_rows,
        source_claim_boundary_path=args.source_claim_boundary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"preflight_work_item_count={summary['preflight_work_item_count']}")
    print(f"static_check_fail_count={summary['static_check_fail_count']}")
    print(f"reset_required_count={summary['reset_required_count']}")
    print(f"reset_attempted_count={summary['reset_attempted_count']}")
    print(f"reset_blocked_missing_concrete_overlay_count={summary['reset_blocked_missing_concrete_overlay_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    print(f"next_blocker={summary['next_blocker']}")
    return 0 if summary["result_class"] != RESULT_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
