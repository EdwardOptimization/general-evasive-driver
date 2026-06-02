"""Materialize M2454 scenario-quality redesign protocol artifacts for M2455."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_M2452_DIR = Path("runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel")
DEFAULT_PANEL_ROWS = DEFAULT_M2452_DIR / "panel_rows.csv"
DEFAULT_M2452_SUMMARY = DEFAULT_M2452_DIR / "summary.json"
DEFAULT_PROTOCOL_DOC = Path(
    "docs/m2454-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-design.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight"
)
DEFAULT_NEXT_BLOCKER = (
    "m2456-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-materialization-result-audit"
)

RESULT_PASS = "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass"
RESULT_FAIL = "current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_incomplete_or_fail"

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "candidate_group",
    "source_panel_id",
    "source_panel_class",
    "source_panel_scope",
    "role_family",
    "sampled_obstacle_label",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
    "geometry_lever_class",
    "boundary_protocol_class",
    "split",
    "episode_count",
    "actual_success_rate",
    "hard_offtrack_rate",
    "collision_rate",
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "policy_action_executed",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "reason",
]

ROLE_PROTOCOL_FIELDNAMES = [
    "role_protocol_id",
    "candidate_group",
    "role_scope",
    "sampled_obstacle_label_scope",
    "purpose",
    "candidate_count",
    "admission_rule",
    "guardrail_rule",
    "labels_enter_actor_input",
    "actor_input_contract_changed",
    "scenario_redesign_executed",
    "ranking_admissible",
    "winner_selected",
]

GEOMETRY_LEVER_FIELDNAMES = [
    "lever_id",
    "geometry_lever_class",
    "candidate_group",
    "description",
    "bounded",
    "scenario_redesign_executed",
    "labels_enter_actor_input",
    "ranking_admissible",
    "winner_selected",
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


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _source_value(row: Mapping[str, Any], axis: str) -> str:
    return str(row.get("value", "")) if str(row.get("axis", "")) == axis else ""


def _role_from_panel(row: Mapping[str, Any]) -> str:
    axis = str(row.get("axis", ""))
    value = str(row.get("value", ""))
    if axis == "role_family":
        return value
    if axis == "role_family+sampled_obstacle_label":
        return value.split("|", 1)[0]
    scope = str(row.get("panel_scope", ""))
    if scope == "stable_avoidable_boundary_quality":
        return "R0_stable_avoidable"
    if scope == "aeb_infeasible_stable_aes_quality":
        return "R1_aeb_infeasible_stable_aes"
    if scope == "handling_limit_drift_required":
        return "R2_R3_R5_handling_limit"
    if scope == "unavoidable_mitigation":
        return "R4_unavoidable_mitigation"
    return ""


def _label_from_panel(row: Mapping[str, Any]) -> str:
    axis = str(row.get("axis", ""))
    value = str(row.get("value", ""))
    if axis == "sampled_obstacle_label":
        return value
    if axis == "role_family+sampled_obstacle_label" and "|" in value:
        return value.split("|", 1)[1]
    scope = str(row.get("panel_scope", ""))
    if scope == "stable_avoidable_boundary_quality":
        return "aeb_feasible"
    if scope == "aeb_infeasible_stable_aes_quality":
        return "aes_feasible"
    if scope == "handling_limit_drift_required":
        return "drift_required"
    if scope == "unavoidable_mitigation":
        return "unavoidable"
    return ""


def _candidate_group(row: Mapping[str, Any]) -> str:
    scope = str(row.get("panel_scope", ""))
    axis = str(row.get("axis", ""))
    value = str(row.get("value", ""))
    if scope == "stable_avoidable_boundary_quality" or value in {"R0_stable_avoidable", "aeb_feasible"}:
        return "stable_feasibility_support"
    if scope == "aeb_infeasible_stable_aes_quality" or value in {"R1_aeb_infeasible_stable_aes", "aes_feasible"}:
        return "stable_aes_support"
    if scope == "unavoidable_mitigation" or value in {"R4_unavoidable_mitigation", "unavoidable"}:
        return "mitigation_guardrail"
    if _bool(row.get("hidden_dynamics_guardrail")) or axis == "hidden_dynamics_bucket":
        return "hidden_dynamics_guardrail"
    if value in {
        "R2_handling_limit_drift_capable_avoidance",
        "R3_recovery_after_limit",
        "R5_hidden_dynamics_robustness",
        "drift_required",
    } or scope in {"handling_limit_drift_required", "role_semantics", "scenario_label"}:
        return "handling_limit_guardrail"
    if _bool(row.get("geometry_timing_guardrail")):
        return "geometry_timing_guardrail"
    return ""


def _geometry_lever_class(row: Mapping[str, Any], group: str) -> str:
    axis = str(row.get("axis", ""))
    if group == "stable_feasibility_support":
        return "stable_recovery_corridor_and_reaction_distance"
    if group == "stable_aes_support":
        return "stable_aes_corridor_and_obstacle_width"
    if group == "handling_limit_guardrail":
        return "handling_limit_preservation"
    if group == "hidden_dynamics_guardrail":
        return "hidden_dynamics_stress_preservation"
    if group == "mitigation_guardrail":
        return "mitigation_isolation"
    if axis == "obstacle_longitudinal_timing_bucket":
        return "timing_bucket_balance"
    if axis == "obstacle_lateral_offset_bucket":
        return "lateral_offset_balance"
    return "general_geometry_guardrail"


def _boundary_protocol_class(group: str) -> str:
    if group in {"stable_feasibility_support", "stable_aes_support"}:
        return "road_containment_actual_success_required"
    if group == "mitigation_guardrail":
        return "mitigation_not_success_ranking"
    if group in {"handling_limit_guardrail", "hidden_dynamics_guardrail", "geometry_timing_guardrail"}:
        return "guardrail_not_winner"
    return "diagnostic_only"


def candidate_rows(panel_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_counters: Counter[str] = Counter()
    for panel in panel_rows:
        if _bool(panel.get("monitoring_only")):
            continue
        group = _candidate_group(panel)
        if not group:
            continue
        group_counters[group] += 1
        index = group_counters[group]
        split = "public_debug" if index % 5 in {1, 2, 3} else "public_gate"
        rows.append(
            {
                "candidate_id": f"m2455_{group}_{index:03d}",
                "candidate_group": group,
                "source_panel_id": str(panel.get("panel_id", "")),
                "source_panel_class": str(panel.get("panel_class", "")),
                "source_panel_scope": str(panel.get("panel_scope", "")),
                "role_family": _role_from_panel(panel),
                "sampled_obstacle_label": _label_from_panel(panel),
                "hidden_dynamics_bucket": _source_value(panel, "hidden_dynamics_bucket"),
                "obstacle_longitudinal_timing_bucket": _source_value(panel, "obstacle_longitudinal_timing_bucket"),
                "obstacle_lateral_offset_bucket": _source_value(panel, "obstacle_lateral_offset_bucket"),
                "geometry_lever_class": _geometry_lever_class(panel, group),
                "boundary_protocol_class": _boundary_protocol_class(group),
                "split": split,
                "episode_count": _int(panel.get("episode_count")),
                "actual_success_rate": _float(panel.get("actual_success_rate")),
                "hard_offtrack_rate": _float(panel.get("hard_offtrack_rate")),
                "collision_rate": _float(panel.get("collision_rate")),
                "labels_enter_actor_input": False,
                "actor_input_contract_changed": False,
                "scenario_redesign_executed": False,
                "policy_action_executed": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "reason": "Protocol materialization row only; no scenario redesign execution or winner selection.",
            }
        )
    order = {
        "stable_feasibility_support": 0,
        "stable_aes_support": 1,
        "geometry_timing_guardrail": 2,
        "handling_limit_guardrail": 3,
        "hidden_dynamics_guardrail": 4,
        "mitigation_guardrail": 5,
    }
    return sorted(rows, key=lambda row: (order.get(str(row.get("candidate_group")), 99), str(row["candidate_id"])))


def role_protocol_rows(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("candidate_group", "")) for row in candidates)
    specs = [
        (
            "m2455_role_stable_feasibility",
            "stable_feasibility_support",
            "R0_stable_avoidable",
            "aeb_feasible",
            "Basic road-contained obstacle avoidance support.",
            "Require collision-free road-contained stable avoidance geometry before measured rollout.",
            "Do not erase drift-required or mitigation guardrails.",
        ),
        (
            "m2455_role_stable_aes",
            "stable_aes_support",
            "R1_aeb_infeasible_stable_aes",
            "aes_feasible",
            "AEB-infeasible but stable steering avoidance support.",
            "AEB infeasibility may be metadata only; stable road-contained AES must be plausible.",
            "Preserve collision and offtrack guardrails.",
        ),
        (
            "m2455_role_handling_limit",
            "handling_limit_guardrail",
            "R2/R3/R5",
            "drift_required",
            "Handling-limit and recovery guardrail preservation.",
            "Do not use handling-limit rows to tune stable task quality.",
            "Keep drift-required rows as guarded repair-plan candidates only.",
        ),
        (
            "m2455_role_hidden_dynamics",
            "hidden_dynamics_guardrail",
            "R5/hidden-dynamics stress",
            "metadata_only",
            "Hidden-dynamics stress preservation.",
            "Keep hidden dynamics metadata out of actor input.",
            "Preserve low_mu, weak_brake, slow steer, tire shift, and related stress rows.",
        ),
        (
            "m2455_role_mitigation",
            "mitigation_guardrail",
            "R4_unavoidable_mitigation",
            "unavoidable",
            "Mitigation rows isolated from success ranking.",
            "Track impact and mitigation metrics separately from success support.",
            "Unavoidable rows must not become offtrack repair winners.",
        ),
    ]
    return [
        {
            "role_protocol_id": protocol_id,
            "candidate_group": group,
            "role_scope": role_scope,
            "sampled_obstacle_label_scope": label_scope,
            "purpose": purpose,
            "candidate_count": counts[group],
            "admission_rule": admission_rule,
            "guardrail_rule": guardrail_rule,
            "labels_enter_actor_input": False,
            "actor_input_contract_changed": False,
            "scenario_redesign_executed": False,
            "ranking_admissible": False,
            "winner_selected": False,
        }
        for protocol_id, group, role_scope, label_scope, purpose, admission_rule, guardrail_rule in specs
    ]


def geometry_lever_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "m2455_lever_reaction_distance",
            "reaction_distance_margin",
            "stable_feasibility_support",
            "Bound obstacle reveal distance and initial speed so R0 has stable response support.",
        ),
        (
            "m2455_lever_recovery_corridor",
            "post_obstacle_recovery_corridor",
            "stable_feasibility_support",
            "Require post-obstacle road containment support rather than immediate offtrack saturation.",
        ),
        (
            "m2455_lever_obstacle_width",
            "obstacle_half_width_bounds",
            "stable_aes_support",
            "Keep AES obstacle width bounded so stable steering avoidance remains plausible.",
        ),
        (
            "m2455_lever_lateral_offset",
            "lateral_offset_balance",
            "geometry_timing_guardrail",
            "Balance centerline, left, and right offsets without ranking them as winners.",
        ),
        (
            "m2455_lever_timing",
            "timing_bucket_balance",
            "geometry_timing_guardrail",
            "Preserve early, mid, and late timing buckets as guardrails.",
        ),
        (
            "m2455_lever_mitigation_isolation",
            "mitigation_isolation",
            "mitigation_guardrail",
            "Keep unavoidable mitigation metrics separate from success support.",
        ),
    ]
    return [
        {
            "lever_id": lever_id,
            "geometry_lever_class": lever_class,
            "candidate_group": group,
            "description": description,
            "bounded": True,
            "scenario_redesign_executed": False,
            "labels_enter_actor_input": False,
            "ranking_admissible": False,
            "winner_selected": False,
        }
        for lever_id, lever_class, group, description in specs
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "scenario_redesign_executed",
            "false",
            True,
            "M2455 materializes protocol artifacts only.",
        ),
        ("measured_rollout_started", "false", True, "No environment rollout is run."),
        ("policy_action_executed", "false", True, "No policy action is executed."),
        ("repair_training_started", "false", True, "No repair or training is executed."),
        ("ranking_or_winner", "false", True, "No scenario candidate or controller winner is selected."),
        ("actual_success_improvement", "blocked", False, "No fresh measured rollout is produced."),
        ("paper_or_self_id_verdict", "blocked", False, "No controller-family or history-necessity study is run."),
        ("current_sim_verdict", "blocked", False, "This is not a final current-sim verdict."),
    ]
    return [
        {
            "claim_key": key,
            "claim_value": value,
            "admissible": admissible,
            "reason": reason,
        }
        for key, value, admissible, reason in rows
    ]


def guardrail_rows(
    *,
    candidates: Sequence[Mapping[str, Any]],
    role_rows: Sequence[Mapping[str, Any]],
    claim_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    group_counts = Counter(str(row.get("candidate_group", "")) for row in candidates)
    guards: list[dict[str, Any]] = []
    required_groups = [
        "stable_feasibility_support",
        "stable_aes_support",
        "handling_limit_guardrail",
        "hidden_dynamics_guardrail",
        "mitigation_guardrail",
    ]
    for group in required_groups:
        count = group_counts[group]
        guards.append(
            {
                "guardrail_id": f"m2455_nonempty_{group}",
                "guardrail_class": "group_nonempty",
                "source_role_or_axis": group,
                "failure_mode_to_preserve": "scenario_sampling_failure",
                "metric_to_watch": "candidate_count",
                "value": count,
                "violation": count <= 0,
                "reason": f"{group} must be nonempty before reset/preflight or measured validation.",
            }
        )
    flag_checks = [
        ("labels_enter_actor_input", _flag_count(candidates, "labels_enter_actor_input")),
        ("actor_input_contract_changed", _flag_count(candidates, "actor_input_contract_changed")),
        ("scenario_redesign_executed", _flag_count(candidates, "scenario_redesign_executed")),
        ("policy_action_executed", _flag_count(candidates, "policy_action_executed")),
        ("repair_execution_started", _flag_count(candidates, "repair_execution_started")),
        ("training_started", _flag_count(candidates, "training_started")),
        ("ranking_admissible", _flag_count(candidates, "ranking_admissible")),
        ("winner_selected", _flag_count(candidates, "winner_selected")),
    ]
    for key, value in flag_checks:
        guards.append(
            {
                "guardrail_id": f"m2455_flag_{key}",
                "guardrail_class": "claim_boundary",
                "source_role_or_axis": "candidate_rows",
                "failure_mode_to_preserve": "contract_violation",
                "metric_to_watch": key,
                "value": value,
                "violation": value != 0,
                "reason": f"{key} must remain false or zero in materialized candidates.",
            }
        )
    guards.append(
        {
            "guardrail_id": "m2455_role_protocol_complete",
            "guardrail_class": "role_protocol",
            "source_role_or_axis": "role_protocol_rows",
            "failure_mode_to_preserve": "scenario_sampling_failure",
            "metric_to_watch": "role_protocol_row_count",
            "value": len(role_rows),
            "violation": len(role_rows) < 5,
            "reason": "All role protocol groups must be represented.",
        }
    )
    guards.append(
        {
            "guardrail_id": "m2455_claim_boundary_complete",
            "guardrail_class": "claim_boundary",
            "source_role_or_axis": "claim_boundary",
            "failure_mode_to_preserve": "metric_artifact",
            "metric_to_watch": "claim_boundary_row_count",
            "value": len(claim_rows),
            "violation": len(claim_rows) < 8,
            "reason": "Claim boundary rows must explicitly block unsupported claims.",
        }
    )
    return guards


def decision_rows(next_blocker: str) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "protocol_materialized",
            "decision_value": "true",
            "admissible": True,
            "reason": "M2455 materializes M2454 protocol artifacts.",
        },
        {
            "decision_key": "scenario_redesign_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2455 is materialization/preflight only.",
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
            "reason": "Audit materialized protocol artifacts before reset/preflight, measured rollout, or redesign execution.",
        },
    ]


def run_protocol_materialization_preflight(
    *,
    panel_rows_path: Path | str = DEFAULT_PANEL_ROWS,
    m2452_summary_path: Path | str = DEFAULT_M2452_SUMMARY,
    protocol_doc_path: Path | str = DEFAULT_PROTOCOL_DOC,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    panel_rows = read_csv_rows(panel_rows_path)
    m2452_summary = read_json(m2452_summary_path)
    protocol_doc_exists = Path(protocol_doc_path).exists()
    candidates = candidate_rows(panel_rows)
    roles = role_protocol_rows(candidates)
    levers = geometry_lever_rows()
    claims = claim_boundary_rows()
    guards = guardrail_rows(candidates=candidates, role_rows=roles, claim_rows=claims)
    decisions = decision_rows(str(next_blocker))

    group_counts = _count_by(candidates, "candidate_group")
    split_counts = _count_by(candidates, "split")
    guardrail_violation_count = _flag_count(guards, "violation")
    labels_enter_actor_input_count = _flag_count(candidates, "labels_enter_actor_input")
    actor_input_contract_changed_count = _flag_count(candidates, "actor_input_contract_changed")
    ranking_admissible_count = _flag_count(candidates, "ranking_admissible")
    winner_selected_count = _flag_count(candidates, "winner_selected")
    required_groups = {
        "stable_feasibility_support",
        "stable_aes_support",
        "handling_limit_guardrail",
        "hidden_dynamics_guardrail",
        "mitigation_guardrail",
    }
    missing_groups = sorted(group for group in required_groups if int(group_counts.get(group, 0)) <= 0)
    source_result_class = str(m2452_summary.get("result_class", ""))
    passes = (
        source_result_class.endswith("_pass")
        and protocol_doc_exists
        and len(panel_rows) > 0
        and len(candidates) > 0
        and not missing_groups
        and len(roles) >= 5
        and len(levers) >= 6
        and len(claims) >= 8
        and labels_enter_actor_input_count == 0
        and actor_input_contract_changed_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    failure_types: list[str] = []
    if not source_result_class.endswith("_pass") or not protocol_doc_exists:
        failure_types.append("lineage_invalid")
    if missing_groups:
        failure_types.append("scenario_sampling_failure")
    if (
        labels_enter_actor_input_count
        or actor_input_contract_changed_count
        or ranking_admissible_count
        or winner_selected_count
        or guardrail_violation_count
    ):
        failure_types.append("contract_violation")

    write_csv_rows(output / "candidate_rows.csv", candidates, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "role_protocol_rows.csv", roles, fieldnames=ROLE_PROTOCOL_FIELDNAMES)
    write_csv_rows(output / "geometry_lever_rows.csv", levers, fieldnames=GEOMETRY_LEVER_FIELDNAMES)
    write_csv_rows(output / "guardrail_rows.csv", guards, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decisions, fieldnames=DECISION_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "panel_rows": str(panel_rows_path),
            "m2452_summary": str(m2452_summary_path),
            "protocol_doc": str(protocol_doc_path),
        },
        "source_result_class": source_result_class,
        "protocol_doc_exists": protocol_doc_exists,
        "source_panel_row_count": len(panel_rows),
        "candidate_row_count": len(candidates),
        "role_protocol_row_count": len(roles),
        "geometry_lever_row_count": len(levers),
        "guardrail_row_count": len(guards),
        "claim_boundary_row_count": len(claims),
        "decision_row_count": len(decisions),
        "candidate_group_counts": group_counts,
        "candidate_split_counts": split_counts,
        "missing_required_groups": missing_groups,
        "stable_feasibility_support_count": int(group_counts.get("stable_feasibility_support", 0)),
        "stable_aes_support_count": int(group_counts.get("stable_aes_support", 0)),
        "handling_limit_guardrail_count": int(group_counts.get("handling_limit_guardrail", 0)),
        "hidden_dynamics_guardrail_count": int(group_counts.get("hidden_dynamics_guardrail", 0)),
        "mitigation_guardrail_count": int(group_counts.get("mitigation_guardrail", 0)),
        "labels_enter_actor_input_count": labels_enter_actor_input_count,
        "actor_input_contract_changed_count": actor_input_contract_changed_count,
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
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
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
            "candidate_rows": str(output / "candidate_rows.csv"),
            "role_protocol_rows": str(output / "role_protocol_rows.csv"),
            "geometry_lever_rows": str(output / "geometry_lever_rows.csv"),
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
    parser.add_argument("--panel-rows", type=Path, default=DEFAULT_PANEL_ROWS)
    parser.add_argument("--m2452-summary", type=Path, default=DEFAULT_M2452_SUMMARY)
    parser.add_argument("--protocol-doc", type=Path, default=DEFAULT_PROTOCOL_DOC)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_protocol_materialization_preflight(
        panel_rows_path=args.panel_rows,
        m2452_summary_path=args.m2452_summary,
        protocol_doc_path=args.protocol_doc,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"candidate_row_count={summary['candidate_row_count']}")
    print(f"candidate_group_counts={summary['candidate_group_counts']}")
    print(f"missing_required_groups={summary['missing_required_groups']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    print(f"next_blocker={summary['next_blocker']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
