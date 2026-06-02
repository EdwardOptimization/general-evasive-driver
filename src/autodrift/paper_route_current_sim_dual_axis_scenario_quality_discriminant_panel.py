"""Artifact-only scenario-quality discriminant panel for M2452."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path("runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation")
DEFAULT_SOURCE_SUMMARY = DEFAULT_SOURCE_DIR / "summary.json"
DEFAULT_EPISODE_ROWS = DEFAULT_SOURCE_DIR / "episode_rows.csv"
DEFAULT_M2449_DIR = Path(
    "runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation"
)
DEFAULT_TARGET_ROWS = DEFAULT_M2449_DIR / "target_rows.csv"
DEFAULT_GUARDRAIL_ROWS = DEFAULT_M2449_DIR / "guardrail_rows.csv"
DEFAULT_DIAGNOSTIC_ROWS = DEFAULT_M2449_DIR / "diagnostic_rows.csv"
DEFAULT_M2449_SUMMARY = DEFAULT_M2449_DIR / "summary.json"
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel"
)
DEFAULT_TARGET_EPISODE_COUNT = 5250
DEFAULT_TARGET_ROW_COUNT = 21
DEFAULT_GUARDRAIL_ROW_COUNT = 56
DEFAULT_NEXT_BLOCKER = (
    "m2453-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel-result-audit"
)

RESULT_PASS = "current_sim_dual_axis_scenario_quality_discriminant_panel_pass"
RESULT_FAIL = "current_sim_dual_axis_scenario_quality_discriminant_panel_incomplete_or_fail"

SCENARIO_QUALITY_ROUTE = "route_to_scenario_quality_result_audit_before_redesign_or_repair"

MONITORING_AXES = {
    "global",
    "profile_name",
    "profile_seed",
    "pack_id",
    "scenario_family_id",
    "termination_reason",
    "outcome_bucket",
}

PANEL_FIELDNAMES = [
    "panel_id",
    "panel_class",
    "panel_scope",
    "axis",
    "value",
    "source_row_ids",
    "episode_count",
    "actual_success_count",
    "actual_success_rate",
    "hard_offtrack_count",
    "hard_offtrack_rate",
    "soft_offtrack_violation_count",
    "soft_offtrack_violation_rate",
    "boundary_tolerated_success_count",
    "boundary_tolerated_success_rate",
    "collision_count",
    "collision_rate",
    "max_step_noncompletion_count",
    "max_step_noncompletion_rate",
    "other_count",
    "other_rate",
    "mean_min_clearance_margin",
    "min_min_clearance_margin",
    "mean_overshoot_m",
    "max_overshoot_m",
    "mean_steps",
    "diagnostic_pattern",
    "scenario_quality_blocker",
    "possible_repair_plan_candidate",
    "collision_mitigation_guardrail",
    "hidden_dynamics_guardrail",
    "geometry_timing_guardrail",
    "soft_boundary_diagnostic",
    "monitoring_only",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
    "reason",
]

GUARDRAIL_FIELDNAMES = [
    "guardrail",
    "value",
    "violation",
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


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _rate(count: int, total: int) -> float:
    return float(count) / float(total) if total else 0.0


def _finite_values(values: Iterable[Any]) -> list[float]:
    finite: list[float] = []
    for value in values:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            continue
        if parsed == parsed and parsed not in {float("inf"), float("-inf")}:
            finite.append(parsed)
    return finite


def _mean(values: Iterable[Any]) -> float:
    finite = _finite_values(values)
    return sum(finite) / len(finite) if finite else 0.0


def _min(values: Iterable[Any]) -> float:
    finite = _finite_values(values)
    return min(finite) if finite else 0.0


def _max(values: Iterable[Any]) -> float:
    finite = _finite_values(values)
    return max(finite) if finite else 0.0


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _flag_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    actual_success = sum(_bool(row.get("metric_selected_actual_success", row.get("success"))) for row in rows)
    hard_offtrack = sum(_bool(row.get("metric_selected_hard_offtrack_failure")) for row in rows)
    soft_violation = sum(_bool(row.get("metric_selected_soft_offtrack_violation")) for row in rows)
    boundary_tolerated_success = sum(_bool(row.get("metric_selected_boundary_tolerated_success")) for row in rows)
    collision = sum(_bool(row.get("collision")) for row in rows)
    max_step = sum(str(row.get("outcome_bucket", "")) == "max_steps_noncompletion" for row in rows)
    other = 0
    for row in rows:
        if not (
            _bool(row.get("metric_selected_actual_success", row.get("success")))
            or _bool(row.get("metric_selected_hard_offtrack_failure"))
            or _bool(row.get("metric_selected_soft_offtrack_violation"))
            or _bool(row.get("collision"))
            or str(row.get("outcome_bucket", "")) == "max_steps_noncompletion"
        ):
            other += 1
    return {
        "actual_success": actual_success,
        "hard_offtrack": hard_offtrack,
        "soft_violation": soft_violation,
        "boundary_tolerated_success": boundary_tolerated_success,
        "collision": collision,
        "max_step": max_step,
        "other": other,
    }


def _diagnostic_pattern(counts: Mapping[str, int], total: int) -> str:
    if total <= 0:
        return "empty"
    for name, count in (
        ("hard_offtrack_dominated", counts.get("hard_offtrack", 0)),
        ("collision_dominated", counts.get("collision", 0)),
        ("success_supported", counts.get("actual_success", 0)),
        ("soft_violation_visible", counts.get("soft_violation", 0)),
        ("max_step_dominated", counts.get("max_step", 0)),
    ):
        if _rate(int(count), total) >= 0.5:
            return name
    return "mixed"


def _metric_row_from_episodes(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    counts = _flag_counts(rows)
    return {
        "episode_count": total,
        "actual_success_count": counts["actual_success"],
        "actual_success_rate": _rate(counts["actual_success"], total),
        "hard_offtrack_count": counts["hard_offtrack"],
        "hard_offtrack_rate": _rate(counts["hard_offtrack"], total),
        "soft_offtrack_violation_count": counts["soft_violation"],
        "soft_offtrack_violation_rate": _rate(counts["soft_violation"], total),
        "boundary_tolerated_success_count": counts["boundary_tolerated_success"],
        "boundary_tolerated_success_rate": _rate(counts["boundary_tolerated_success"], total),
        "collision_count": counts["collision"],
        "collision_rate": _rate(counts["collision"], total),
        "max_step_noncompletion_count": counts["max_step"],
        "max_step_noncompletion_rate": _rate(counts["max_step"], total),
        "other_count": counts["other"],
        "other_rate": _rate(counts["other"], total),
        "mean_min_clearance_margin": _mean(row.get("min_clearance_margin") for row in rows),
        "min_min_clearance_margin": _min(row.get("min_clearance_margin") for row in rows),
        "mean_overshoot_m": _mean(row.get("metric_selected_max_offtrack_overshoot_m") for row in rows),
        "max_overshoot_m": _max(row.get("metric_selected_max_offtrack_overshoot_m") for row in rows),
        "mean_steps": _mean(row.get("steps") for row in rows),
        "diagnostic_pattern": _diagnostic_pattern(counts, total),
    }


def _metric_row_from_consolidated(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "episode_count": _int(row.get("episode_count")),
        "actual_success_count": _int(row.get("actual_success_count")),
        "actual_success_rate": _float(row.get("actual_success_rate")),
        "hard_offtrack_count": _int(row.get("hard_offtrack_count")),
        "hard_offtrack_rate": _float(row.get("hard_offtrack_rate")),
        "soft_offtrack_violation_count": _int(row.get("soft_offtrack_violation_count")),
        "soft_offtrack_violation_rate": _float(row.get("soft_offtrack_violation_rate")),
        "boundary_tolerated_success_count": _int(row.get("boundary_tolerated_success_count")),
        "boundary_tolerated_success_rate": _float(row.get("boundary_tolerated_success_rate")),
        "collision_count": _int(row.get("collision_count")),
        "collision_rate": _float(row.get("collision_rate")),
        "max_step_noncompletion_count": _int(row.get("max_step_noncompletion_count")),
        "max_step_noncompletion_rate": _float(row.get("max_step_noncompletion_rate")),
        "other_count": _int(row.get("other_count")),
        "other_rate": _float(row.get("other_rate")),
        "mean_min_clearance_margin": _float(row.get("mean_min_clearance_margin")),
        "min_min_clearance_margin": _float(row.get("min_min_clearance_margin")),
        "mean_overshoot_m": _float(row.get("mean_overshoot_m")),
        "max_overshoot_m": _float(row.get("max_overshoot_m")),
        "mean_steps": _float(row.get("mean_steps")),
        "diagnostic_pattern": str(row.get("diagnostic_pattern", "")),
    }


def _same_value(axis: str, value: str) -> Callable[[Mapping[str, Any]], bool]:
    return lambda row: str(row.get(axis, "")) == value


def _role_in(values: set[str]) -> Callable[[Mapping[str, Any]], bool]:
    return lambda row: str(row.get("role_family", "")) in values


def _label_is(value: str) -> Callable[[Mapping[str, Any]], bool]:
    return lambda row: str(row.get("sampled_obstacle_label", "")) == value


def _combine(*predicates: Callable[[Mapping[str, Any]], bool]) -> Callable[[Mapping[str, Any]], bool]:
    return lambda row: all(predicate(row) for predicate in predicates)


def _select_rows(
    episode_rows: Sequence[Mapping[str, Any]], predicate: Callable[[Mapping[str, Any]], bool]
) -> list[Mapping[str, Any]]:
    return [row for row in episode_rows if predicate(row)]


def _source_ids_for(
    consolidated_rows: Sequence[Mapping[str, Any]],
    *,
    axes_and_values: Sequence[tuple[str, str]],
) -> str:
    ids: list[str] = []
    for row in consolidated_rows:
        axis = str(row.get("axis", ""))
        value = str(row.get("value", ""))
        if (axis, value) in axes_and_values:
            ids.append(str(row.get("row_id", "")))
    return ";".join(row_id for row_id in ids if row_id)


def _panel_row(
    *,
    panel_id: str,
    panel_class: str,
    panel_scope: str,
    axis: str,
    value: str,
    source_row_ids: str,
    metrics: Mapping[str, Any],
    scenario_quality_blocker: bool = False,
    possible_repair_plan_candidate: bool = False,
    collision_mitigation_guardrail: bool = False,
    hidden_dynamics_guardrail: bool = False,
    geometry_timing_guardrail: bool = False,
    soft_boundary_diagnostic: bool = False,
    monitoring_only: bool = False,
    reason: str,
) -> dict[str, Any]:
    diagnostic_only = not possible_repair_plan_candidate or monitoring_only or scenario_quality_blocker
    row = {
        "panel_id": panel_id,
        "panel_class": panel_class,
        "panel_scope": panel_scope,
        "axis": axis,
        "value": value,
        "source_row_ids": source_row_ids,
        "scenario_quality_blocker": bool(scenario_quality_blocker),
        "possible_repair_plan_candidate": bool(possible_repair_plan_candidate),
        "collision_mitigation_guardrail": bool(collision_mitigation_guardrail),
        "hidden_dynamics_guardrail": bool(hidden_dynamics_guardrail),
        "geometry_timing_guardrail": bool(geometry_timing_guardrail),
        "soft_boundary_diagnostic": bool(soft_boundary_diagnostic),
        "monitoring_only": bool(monitoring_only),
        "diagnostic_only": bool(diagnostic_only),
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "reason": reason,
    }
    row.update({key: metrics.get(key, 0) for key in PANEL_FIELDNAMES if key in metrics})
    return row


def _primary_episode_panel_rows(
    episode_rows: Sequence[Mapping[str, Any]],
    consolidated_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = [
        {
            "panel_id": "m2452_stable_avoidable_task_quality",
            "panel_class": "scenario_quality_blocker",
            "panel_scope": "stable_avoidable_boundary_quality",
            "axis": "role_family+sampled_obstacle_label",
            "value": "R0_stable_avoidable|aeb_feasible",
            "predicate": _combine(_same_value("role_family", "R0_stable_avoidable"), _label_is("aeb_feasible")),
            "source_axes": [("role_family", "R0_stable_avoidable"), ("sampled_obstacle_label", "aeb_feasible")],
            "scenario_quality_blocker": True,
            "reason": "Stable avoidable/AEB-feasible rows are expected to be ordinary avoidance; hard-offtrack dominance is a task-quality blocker, not a handling-limit repair winner.",
        },
        {
            "panel_id": "m2452_stable_aes_task_quality",
            "panel_class": "scenario_quality_blocker",
            "panel_scope": "aeb_infeasible_stable_aes_quality",
            "axis": "role_family+sampled_obstacle_label",
            "value": "R1_aeb_infeasible_stable_aes|aes_feasible",
            "predicate": _combine(_same_value("role_family", "R1_aeb_infeasible_stable_aes"), _label_is("aes_feasible")),
            "source_axes": [("role_family", "R1_aeb_infeasible_stable_aes"), ("sampled_obstacle_label", "aes_feasible")],
            "scenario_quality_blocker": True,
            "reason": "Stable AES-feasible rows are not drift-required; broad hard-offtrack dominance points to scenario/task quality before repair training.",
        },
        {
            "panel_id": "m2452_handling_limit_drift_candidate",
            "panel_class": "possible_repair_plan_candidate",
            "panel_scope": "handling_limit_drift_required",
            "axis": "sampled_obstacle_label",
            "value": "drift_required",
            "predicate": _label_is("drift_required"),
            "source_axes": [("sampled_obstacle_label", "drift_required")],
            "possible_repair_plan_candidate": True,
            "collision_mitigation_guardrail": True,
            "reason": "Drift-required rows are the main handling-limit repair-planning candidate, but collision and boundary guardrails remain attached.",
        },
        {
            "panel_id": "m2452_unavoidable_mitigation_guardrail",
            "panel_class": "collision_mitigation_guardrail",
            "panel_scope": "unavoidable_mitigation",
            "axis": "sampled_obstacle_label",
            "value": "unavoidable",
            "predicate": _label_is("unavoidable"),
            "source_axes": [("role_family", "R4_unavoidable_mitigation"), ("sampled_obstacle_label", "unavoidable")],
            "collision_mitigation_guardrail": True,
            "reason": "Unavoidable rows are mitigation/collision guardrails; they must not be treated as offtrack repair winners.",
        },
        {
            "panel_id": "m2452_hidden_dynamics_stress_candidate",
            "panel_class": "possible_repair_plan_candidate",
            "panel_scope": "hidden_dynamics_stress",
            "axis": "hidden_dynamics_bucket",
            "value": "non_nominal_or_stress",
            "predicate": lambda row: str(row.get("hidden_dynamics_bucket", "")) not in {"nominal", ""},
            "source_axes": [],
            "possible_repair_plan_candidate": True,
            "hidden_dynamics_guardrail": True,
            "reason": "Non-nominal hidden-dynamics rows can guide bounded repair planning, but remain non-ranking and must preserve collision/behavior guardrails.",
        },
        {
            "panel_id": "m2452_geometry_timing_blocker",
            "panel_class": "scenario_quality_blocker",
            "panel_scope": "geometry_timing_distribution",
            "axis": "obstacle_geometry_timing",
            "value": "all_offsets_and_timings",
            "predicate": lambda row: True,
            "source_axes": [
                ("obstacle_longitudinal_timing_bucket", "early_far"),
                ("obstacle_longitudinal_timing_bucket", "mid"),
                ("obstacle_longitudinal_timing_bucket", "late_close"),
                ("obstacle_lateral_offset_bucket", "centerline"),
                ("obstacle_lateral_offset_bucket", "left_offset"),
                ("obstacle_lateral_offset_bucket", "right_offset"),
            ],
            "scenario_quality_blocker": True,
            "geometry_timing_guardrail": True,
            "reason": "Geometry/timing rows are broad distribution-quality axes; they should route to scenario-quality audit before repair/training.",
        },
    ]
    panel_rows: list[dict[str, Any]] = []
    for spec in specs:
        selected = _select_rows(episode_rows, spec["predicate"])
        metrics = _metric_row_from_episodes(selected)
        panel_rows.append(
            _panel_row(
                panel_id=str(spec["panel_id"]),
                panel_class=str(spec["panel_class"]),
                panel_scope=str(spec["panel_scope"]),
                axis=str(spec["axis"]),
                value=str(spec["value"]),
                source_row_ids=_source_ids_for(consolidated_rows, axes_and_values=spec.get("source_axes", [])),
                metrics=metrics,
                scenario_quality_blocker=bool(spec.get("scenario_quality_blocker", False)),
                possible_repair_plan_candidate=bool(spec.get("possible_repair_plan_candidate", False)),
                collision_mitigation_guardrail=bool(spec.get("collision_mitigation_guardrail", False)),
                hidden_dynamics_guardrail=bool(spec.get("hidden_dynamics_guardrail", False)),
                geometry_timing_guardrail=bool(spec.get("geometry_timing_guardrail", False)),
                soft_boundary_diagnostic=bool(metrics.get("soft_offtrack_violation_count", 0)),
                monitoring_only=False,
                reason=str(spec["reason"]),
            )
        )
    return panel_rows


def _target_guardrail_panel_rows(consolidated_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in consolidated_rows:
        axis = str(source.get("axis", ""))
        value = str(source.get("value", ""))
        source_row_id = str(source.get("row_id", ""))
        monitoring = axis in MONITORING_AXES
        repair_candidate = _bool(source.get("repair_target_admissible")) and not monitoring
        scenario_quality = axis in {"role_family", "sampled_obstacle_label"} and value in {
            "R0_stable_avoidable",
            "R1_aeb_infeasible_stable_aes",
            "aeb_feasible",
            "aes_feasible",
        }
        collision_guardrail = _bool(source.get("collision_guardrail_required"))
        hidden_guardrail = axis == "hidden_dynamics_bucket"
        geometry_guardrail = axis in {"obstacle_longitudinal_timing_bucket", "obstacle_lateral_offset_bucket"}
        if monitoring:
            panel_class = "monitoring_only"
            panel_scope = f"monitoring_{axis}"
            reason = "Profile, pack, checkpoint/family, outcome, termination, and global axes remain diagnostic-only and non-ranking."
        elif scenario_quality:
            panel_class = "scenario_quality_blocker"
            panel_scope = "stable_or_aes_quality"
            repair_candidate = False
            reason = "Stable avoidable/AES-feasible target rows are task-quality blockers before handling-limit repair planning."
        elif axis == "sampled_obstacle_label" and value == "unavoidable":
            panel_class = "collision_mitigation_guardrail"
            panel_scope = "unavoidable_mitigation"
            repair_candidate = False
            reason = "Unavoidable rows are mitigation guardrails, not offtrack-repair candidates."
        elif repair_candidate:
            panel_class = "possible_repair_plan_candidate"
            panel_scope = str(source.get("actionability_class", "repair_candidate"))
            reason = "Target row may inform a bounded repair plan, but it is not a ranking or winner."
        else:
            panel_class = "guardrail_diagnostic"
            panel_scope = str(source.get("actionability_class", "diagnostic"))
            reason = "Guardrail row is preserved for bounded next-route audit only."
        rows.append(
            _panel_row(
                panel_id=f"m2452_{source_row_id}",
                panel_class=panel_class,
                panel_scope=panel_scope,
                axis=axis,
                value=value,
                source_row_ids=source_row_id,
                metrics=_metric_row_from_consolidated(source),
                scenario_quality_blocker=scenario_quality,
                possible_repair_plan_candidate=repair_candidate,
                collision_mitigation_guardrail=collision_guardrail or panel_class == "collision_mitigation_guardrail",
                hidden_dynamics_guardrail=hidden_guardrail,
                geometry_timing_guardrail=geometry_guardrail,
                soft_boundary_diagnostic=_bool(source.get("soft_boundary_diagnostic")),
                monitoring_only=monitoring,
                reason=reason,
            )
        )
    return rows


def build_panel_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    target_rows: Sequence[Mapping[str, Any]],
    guardrail_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for source in list(target_rows) + list(guardrail_rows) + list(diagnostic_rows):
        row_id = str(source.get("row_id", ""))
        if row_id:
            by_id[row_id] = source
    consolidated = list(by_id.values())
    rows = _primary_episode_panel_rows(episode_rows, consolidated)
    rows.extend(_target_guardrail_panel_rows(consolidated))
    order = {
        "scenario_quality_blocker": 0,
        "possible_repair_plan_candidate": 1,
        "collision_mitigation_guardrail": 2,
        "guardrail_diagnostic": 3,
        "monitoring_only": 4,
    }
    return sorted(
        rows,
        key=lambda row: (
            order.get(str(row.get("panel_class")), 99),
            -_float(row.get("hard_offtrack_rate")),
            -_float(row.get("collision_rate")),
            str(row.get("panel_id", "")),
        ),
    )


def _guardrail_rows(*, panel_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranking_count = _flag_count(panel_rows, "ranking_admissible")
    winner_count = _flag_count(panel_rows, "winner_selected")
    scenario_redesign_claim = False
    rows = [
        (
            "artifact_only_existing_rows",
            False,
            "M2452 reads M2445/M2449 artifacts and does not rerun measured rollout.",
        ),
        ("policy_action_executed", False, "M2452 does not instantiate an environment or policy."),
        ("repair_execution_started", False, "M2452 does not execute repair levers."),
        ("training_started", False, "M2452 does not train."),
        ("replay_or_ppo_started", False, "M2452 does not run replay or PPO."),
        ("diagnostic_axes_used_for_ranking", ranking_count > 0, "All panel rows must remain non-ranking."),
        ("winner_selected", winner_count > 0, "M2452 selects no winner."),
        (
            "scenario_redesign_executed_claim_made",
            scenario_redesign_claim,
            "M2452 may route to scenario-quality audit but does not execute redesign.",
        ),
        ("current_sim_verdict_claim_made", False, "M2452 is not a current-sim verdict."),
        ("paper_or_self_id_claim_made", False, "M2452 makes no paper/FW-vs-GRU/level3 self-ID claim."),
    ]
    return [
        {
            "guardrail": key,
            "value": bool(value),
            "violation": bool(value),
            "reason": reason,
        }
        for key, value, reason in rows
    ]


def _decision_rows(*, next_blocker: str) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "artifact_only_discriminant_panel",
            "decision_value": "true",
            "admissible": True,
            "reason": "M2452 combines existing M2445 episode rows with M2449 target/guardrail rows.",
        },
        {
            "decision_key": "stable_avoidable_and_aes_rows",
            "decision_value": "scenario_quality_blocker",
            "admissible": True,
            "reason": "Stable/AES-feasible hard-offtrack dominance must be audited as task-quality evidence before repair/training.",
        },
        {
            "decision_key": "drift_and_hidden_dynamics_rows",
            "decision_value": "possible_repair_plan_candidate_with_guardrails",
            "admissible": True,
            "reason": "Handling-limit and hidden-dynamics rows can inform a later bounded repair plan but are not rankings or winners.",
        },
        {
            "decision_key": "unavoidable_rows",
            "decision_value": "collision_mitigation_guardrail",
            "admissible": True,
            "reason": "Unavoidable rows belong to mitigation/collision guardrail analysis, not offtrack repair selection.",
        },
        {
            "decision_key": "profile_pack_checkpoint_axes",
            "decision_value": "monitoring_only_non_ranking",
            "admissible": True,
            "reason": "Profile/pack/checkpoint axes remain diagnostic monitoring only.",
        },
        {
            "decision_key": "repair_training_ranking_or_winner_selection",
            "decision_value": "false",
            "admissible": True,
            "reason": "No repair, training, ranking, or winner selection is executed or claimed.",
        },
        {
            "decision_key": "next_route",
            "decision_value": next_blocker,
            "admissible": True,
            "reason": "Audit the discriminant panel before scenario redesign, repair-plan design, training, or verdict claims.",
        },
    ]


def run_scenario_quality_discriminant_panel(
    *,
    source_summary_path: Path | str = DEFAULT_SOURCE_SUMMARY,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    m2449_summary_path: Path | str = DEFAULT_M2449_SUMMARY,
    target_rows_path: Path | str = DEFAULT_TARGET_ROWS,
    guardrail_rows_path: Path | str = DEFAULT_GUARDRAIL_ROWS,
    diagnostic_rows_path: Path | str = DEFAULT_DIAGNOSTIC_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = DEFAULT_TARGET_EPISODE_COUNT,
    target_row_count: int = DEFAULT_TARGET_ROW_COUNT,
    guardrail_row_count: int = DEFAULT_GUARDRAIL_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(source_summary_path)
    m2449_summary = read_json(m2449_summary_path)
    episode_rows = read_csv_rows(episode_rows_path)
    target_rows = read_csv_rows(target_rows_path)
    guardrail_rows = read_csv_rows(guardrail_rows_path)
    diagnostic_rows = read_csv_rows(diagnostic_rows_path)
    panel_rows = build_panel_rows(
        episode_rows=episode_rows,
        target_rows=target_rows,
        guardrail_rows=guardrail_rows,
        diagnostic_rows=diagnostic_rows,
    )
    guards = _guardrail_rows(panel_rows=panel_rows)
    decisions = _decision_rows(next_blocker=str(next_blocker))

    class_counts = _count_by(panel_rows, "panel_class")
    scenario_quality_count = _flag_count(panel_rows, "scenario_quality_blocker")
    repair_candidate_count = _flag_count(panel_rows, "possible_repair_plan_candidate")
    collision_guardrail_count = _flag_count(panel_rows, "collision_mitigation_guardrail")
    monitoring_count = _flag_count(panel_rows, "monitoring_only")
    ranking_count = _flag_count(panel_rows, "ranking_admissible")
    winner_count = _flag_count(panel_rows, "winner_selected")
    guardrail_violation_count = _flag_count(guards, "violation")
    stable_blocker_count = sum(
        1
        for row in panel_rows
        if str(row.get("panel_scope")) in {"stable_avoidable_boundary_quality", "aeb_infeasible_stable_aes_quality"}
        and _bool(row.get("scenario_quality_blocker"))
    )
    drift_candidate_count = sum(
        1
        for row in panel_rows
        if str(row.get("panel_scope")) in {"handling_limit_drift_required", "scenario_label", "role_semantics"}
        and _bool(row.get("possible_repair_plan_candidate"))
    )
    hidden_candidate_count = sum(
        1 for row in panel_rows if _bool(row.get("hidden_dynamics_guardrail")) and not _bool(row.get("monitoring_only"))
    )
    geometry_panel_count = sum(
        1 for row in panel_rows if _bool(row.get("geometry_timing_guardrail")) and not _bool(row.get("monitoring_only"))
    )
    route_supported = (
        scenario_quality_count > 0
        and repair_candidate_count > 0
        and collision_guardrail_count > 0
        and monitoring_count > 0
        and stable_blocker_count >= 2
        and drift_candidate_count > 0
        and hidden_candidate_count > 0
        and geometry_panel_count > 0
    )
    source_result_class = str(source_summary.get("result_class", ""))
    m2449_result_class = str(m2449_summary.get("result_class", ""))
    passes = (
        source_result_class.endswith("_pass")
        and m2449_result_class.endswith("_pass")
        and len(episode_rows) == int(target_episode_count)
        and len(target_rows) == int(target_row_count)
        and len(guardrail_rows) == int(guardrail_row_count)
        and bool(panel_rows)
        and route_supported
        and ranking_count == 0
        and winner_count == 0
        and guardrail_violation_count == 0
    )

    failure_types: list[str] = []
    if not source_result_class.endswith("_pass") or not m2449_result_class.endswith("_pass"):
        failure_types.append("lineage_invalid")
    if not route_supported:
        failure_types.append("scenario_sampling_failure")
    if ranking_count or winner_count or guardrail_violation_count:
        failure_types.append("contract_violation")
    if len(episode_rows) != int(target_episode_count) or len(target_rows) != int(target_row_count):
        failure_types.append("metric_artifact")

    write_csv_rows(output / "panel_rows.csv", panel_rows, fieldnames=PANEL_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    global_panel = next((row for row in panel_rows if row.get("axis") == "obstacle_geometry_timing"), {})
    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "source_summary": str(source_summary_path),
            "episode_rows": str(episode_rows_path),
            "m2449_summary": str(m2449_summary_path),
            "target_rows": str(target_rows_path),
            "guardrail_rows": str(guardrail_rows_path),
            "diagnostic_rows": str(diagnostic_rows_path),
        },
        "source_result_class": source_result_class,
        "m2449_result_class": m2449_result_class,
        "episode_count": len(episode_rows),
        "target_episode_count": int(target_episode_count),
        "target_row_count": len(target_rows),
        "expected_target_row_count": int(target_row_count),
        "guardrail_row_count": len(guardrail_rows),
        "expected_guardrail_row_count": int(guardrail_row_count),
        "diagnostic_row_count": len(diagnostic_rows),
        "panel_row_count": len(panel_rows),
        "panel_class_counts": class_counts,
        "scenario_quality_blocker_count": scenario_quality_count,
        "possible_repair_plan_candidate_count": repair_candidate_count,
        "collision_mitigation_guardrail_count": collision_guardrail_count,
        "hidden_dynamics_guardrail_count": hidden_candidate_count,
        "geometry_timing_guardrail_count": geometry_panel_count,
        "monitoring_only_count": monitoring_count,
        "stable_task_quality_blocker_count": stable_blocker_count,
        "drift_candidate_count": drift_candidate_count,
        "route_supported": route_supported,
        "route_recommendation": SCENARIO_QUALITY_ROUTE,
        "bounded_next_route": str(next_blocker),
        "global_geometry_timing_panel": global_panel,
        "top_scenario_quality_blockers": [
            row for row in panel_rows if _bool(row.get("scenario_quality_blocker"))
        ][:8],
        "top_possible_repair_plan_candidates": [
            row for row in panel_rows if _bool(row.get("possible_repair_plan_candidate"))
        ][:8],
        "top_collision_guardrails": [
            row for row in panel_rows if _bool(row.get("collision_mitigation_guardrail"))
        ][:8],
        "ranking_admissible_count": ranking_count,
        "winner_selected_count": winner_count,
        "guardrail_violation_count": guardrail_violation_count,
        "guardrail_flags": {row["guardrail"]: bool(row["value"]) for row in guards},
        "environment_rollout_started": False,
        "measured_policy_rollout_started": False,
        "policy_action_executed": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "candidate_family_ranking_claim_made": False,
        "actual_success_improvement_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "failure_types_observed": failure_types,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "panel_rows": str(output / "panel_rows.csv"),
            "guardrail_rows": str(output / "guardrail_rows.csv"),
            "decision_rows": str(output / "decision_rows.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-summary", type=Path, default=DEFAULT_SOURCE_SUMMARY)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--m2449-summary", type=Path, default=DEFAULT_M2449_SUMMARY)
    parser.add_argument("--target-rows", type=Path, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--guardrail-rows", type=Path, default=DEFAULT_GUARDRAIL_ROWS)
    parser.add_argument("--diagnostic-rows", type=Path, default=DEFAULT_DIAGNOSTIC_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=DEFAULT_TARGET_EPISODE_COUNT)
    parser.add_argument("--target-row-count", type=int, default=DEFAULT_TARGET_ROW_COUNT)
    parser.add_argument("--guardrail-row-count", type=int, default=DEFAULT_GUARDRAIL_ROW_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_scenario_quality_discriminant_panel(
        source_summary_path=args.source_summary,
        episode_rows_path=args.episode_rows,
        m2449_summary_path=args.m2449_summary,
        target_rows_path=args.target_rows,
        guardrail_rows_path=args.guardrail_rows,
        diagnostic_rows_path=args.diagnostic_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        target_row_count=int(args.target_row_count),
        guardrail_row_count=int(args.guardrail_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"panel_row_count={summary['panel_row_count']}")
    print(f"scenario_quality_blocker_count={summary['scenario_quality_blocker_count']}")
    print(f"possible_repair_plan_candidate_count={summary['possible_repair_plan_candidate_count']}")
    print(f"collision_mitigation_guardrail_count={summary['collision_mitigation_guardrail_count']}")
    print(f"monitoring_only_count={summary['monitoring_only_count']}")
    print(f"route_supported={summary['route_supported']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    print(f"bounded_next_route={summary['bounded_next_route']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
