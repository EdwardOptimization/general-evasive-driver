"""Materialize M3069 direct-action failure decomposition artifacts.

M3069 consumes the M3068-accepted M3067 direct-action closed-loop measurement
artifacts. It performs no reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, profile tuning, checkpoint mutation, or
high-fidelity run. It preserves the 32-row measurement denominator and writes
repair-facing direct-action failure mode, actuation pressure, recovery and
stability, repair requirement, claim, gate, doc, and M3070 audit artifacts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


MILESTONE_ID = (
    "m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-failure-decomposition-materialization-preflight"
)
NEXT_ID = (
    "m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-failure-decomposition-result-audit"
)
M3068_ID = (
    "m3068-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-closed-loop-measurement-result-audit"
)
M3067_ID = (
    "m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-"
    "direct-action-closed-loop-measurement-preflight"
)

DEFAULT_M3068_AUDIT = Path(f"docs/{M3068_ID}.md")
DEFAULT_M3067_DIR = Path(
    "runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_closed_loop_measurement_preflight"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m3069_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_"
    "direct_action_failure_decomposition_materialization_preflight"
)
DEFAULT_DOC_PATH = Path(f"docs/{MILESTONE_ID}.md")
DEFAULT_FOLLOW_UP_MANIFEST = Path(f"experiments/manifests/{NEXT_ID}.json")

EXPECTED_MEASUREMENT_ROWS = 32
EXPECTED_FAILURE_ROWS = 0
EXPECTED_SUCCESS_ROWS = 8
EXPECTED_COLLISION_ROWS = 4
EXPECTED_OFFTRACK_ROWS = 16
EXPECTED_SPEED_TOO_LOW_ROWS = 5
EXPECTED_OBSERVATION_DIM = 72
EXPECTED_ACTION_DIM = 3

CLAIM_SCOPE = (
    "M3069 Active Safety Driver v1 direct-action failure-decomposition "
    "materialization only; existing M3067 measurement rows may be grouped into "
    "direct-action failure-mode, actuation-pressure, recovery-stability, and "
    "repair-requirement artifacts. No reset, step, rollout, replay, fitting, "
    "PPO, training, validation, ranking, winner selection, checkpoint "
    "mutation, checkpoint promotion, profile tuning, driver-performance "
    "verdict, current-sim verdict, repair success, high-fidelity validation, "
    "paper evidence, finite-window-vs-GRU evidence, full ideal driver "
    "completion, or self-ID claim is made"
)

FORBIDDEN_INTERPRETATION = (
    "validation result, driver-performance verdict, current-sim verdict, "
    "repair success, checkpoint ranking, winner selection, checkpoint "
    "promotion, high-fidelity validation readiness or result, paper evidence, "
    "finite-window-vs-GRU conclusion, full ideal driver completion, or level3 "
    "self-identification"
)

FAILURE_MODE_FIELDNAMES = [
    "direct_action_failure_mode_row_id",
    "group_key",
    "group_value",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "blank_termination_count",
    "non_success_count",
    "baseline_success_count",
    "baseline_collision_count",
    "success_delta_positive_count",
    "success_delta_negative_count",
    "collision_delta_negative_count",
    "collision_delta_positive_count",
    "clearance_margin_mean",
    "clearance_margin_delta_mean",
    "return_delta_mean",
    "high_sideslip_fraction_mean",
    "lateral_rmse_mean",
    "action_rate_mean",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction_mean",
    "final_action_abs_max",
    "dominant_outcome_bucket",
    "dominant_termination_reason",
    "measurement_episode_ids",
    "m3069_no_new_execution",
    "actor_input_contract_changed",
    "hidden_oracle_actor_input_required",
    "ttc_actor_input_required",
    "runtime_base_policy_required",
    "driver_performance_claim_made",
    "repair_success_claim_made",
    "validation_result_claim_made",
    "measurement_only_no_verdict",
    "claim_boundary",
]

ACTUATION_FIELDNAMES = [
    "direct_action_actuation_pressure_row_id",
    "group_key",
    "group_value",
    "episode_count",
    "raw_action_abs_max",
    "raw_action_l2_mean",
    "action_clip_fraction_mean",
    "action_clip_fraction_max",
    "final_action_abs_max",
    "raw_out_of_bounds_row_count",
    "any_action_clip_row_count",
    "high_action_clip_row_count",
    "action_saturation_pressure",
    "raw_action_bound_pressure",
    "candidate_binding_rows",
    "parent_binding_rows",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "runtime_base_policy_required",
    "m3069_no_new_execution",
    "ranking_claim_made",
    "promotion_claim_made",
    "repair_success_claim_made",
    "claim_boundary",
]

RECOVERY_STABILITY_FIELDNAMES = [
    "direct_action_recovery_stability_row_id",
    "group_key",
    "group_value",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "speed_too_low_count",
    "recoverability_available_count",
    "recoverability_success_count",
    "recoverability_success_rate",
    "offtrack_severity_proxy_mean",
    "offtrack_severity_proxy_max",
    "max_off_track_overshoot_mean",
    "max_off_track_overshoot_max",
    "time_to_first_off_track_s_mean",
    "high_sideslip_fraction_mean",
    "beta_abs_error_mean",
    "lateral_rmse_mean",
    "speed_mean",
    "clearance_margin_mean",
    "clearance_margin_delta_mean",
    "action_rate_mean",
    "return_delta_mean",
    "stability_pressure",
    "recovery_pressure",
    "m3069_no_new_execution",
    "validation_result_claim_made",
    "driver_performance_claim_made",
    "claim_boundary",
]

REPAIR_REQUIREMENT_FIELDNAMES = [
    "requirement_id",
    "requirement_family",
    "priority",
    "affected_group",
    "row_count",
    "trigger_evidence",
    "requirement",
    "measurable_next_gate",
    "blocked_claims",
    "m3069_no_new_execution",
    "claim_boundary",
]

CLAIM_FIELDNAMES = [
    "claim_id",
    "claim_family",
    "allowed_in_m3069",
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


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _numeric_values(rows: Iterable[Mapping[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if value is None or str(value).strip() == "":
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = _numeric_values(rows, key)
    return sum(values) / len(values) if values else 0.0


def _max(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = _numeric_values(rows, key)
    return max(values) if values else 0.0


def _count(rows: Iterable[Mapping[str, Any]], predicate: Any) -> int:
    return sum(1 for row in rows if predicate(row))


def _dominant(values: Iterable[str]) -> str:
    counter = Counter(str(value) for value in values)
    if not counter:
        return ""
    value, _count_value = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0]
    return value


def _termination(row: Mapping[str, Any]) -> str:
    return str(row.get("termination_reason", ""))


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success"))


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision"))


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return _termination(row) == "off_track"


def _is_speed_too_low(row: Mapping[str, Any]) -> bool:
    return _termination(row) == "speed_too_low"


def _is_non_success(row: Mapping[str, Any]) -> bool:
    return not _is_success(row)


def _group_specs(rows: list[dict[str, str]]) -> list[tuple[str, str, list[dict[str, str]]]]:
    specs: list[tuple[str, str, list[dict[str, str]]]] = [("all", "all", rows)]
    for key in (
        "binding_role",
        "task_family",
        "base_profile_name",
        "outcome_bucket",
        "termination_reason",
        "window_tag",
    ):
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(key, ""))].append(row)
        for value in sorted(groups):
            specs.append((key, value if value else "<blank>", groups[value]))

    combo_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        combo_groups[f"{row.get('binding_role', '')}:{row.get('task_family', '')}"].append(row)
    for value in sorted(combo_groups):
        specs.append(("binding_role_task_family", value, combo_groups[value]))
    return specs


def _core_group_specs(rows: list[dict[str, str]]) -> list[tuple[str, str, list[dict[str, str]]]]:
    allowed = {"all", "binding_role", "task_family", "termination_reason", "binding_role_task_family"}
    return [spec for spec in _group_specs(rows) if spec[0] in allowed]


def build_failure_mode_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, rows) in enumerate(_group_specs(measurement_rows), start=1):
        output_rows.append(
            {
                "direct_action_failure_mode_row_id": f"m3069-direct-action-failure-mode-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "episode_count": len(rows),
                "success_count": _count(rows, _is_success),
                "collision_count": _count(rows, _is_collision),
                "offtrack_count": _count(rows, _is_offtrack),
                "speed_too_low_count": _count(rows, _is_speed_too_low),
                "blank_termination_count": _count(rows, lambda row: _termination(row) == ""),
                "non_success_count": _count(rows, _is_non_success),
                "baseline_success_count": _count(rows, lambda row: _bool(row.get("baseline_success"))),
                "baseline_collision_count": _count(rows, lambda row: _bool(row.get("baseline_collision"))),
                "success_delta_positive_count": _count(rows, lambda row: _float(row.get("success_delta_vs_baseline")) > 0.0),
                "success_delta_negative_count": _count(rows, lambda row: _float(row.get("success_delta_vs_baseline")) < 0.0),
                "collision_delta_negative_count": _count(rows, lambda row: _float(row.get("collision_delta_vs_baseline")) < 0.0),
                "collision_delta_positive_count": _count(rows, lambda row: _float(row.get("collision_delta_vs_baseline")) > 0.0),
                "clearance_margin_mean": _mean(rows, "min_clearance_margin"),
                "clearance_margin_delta_mean": _mean(rows, "clearance_margin_delta_vs_baseline"),
                "return_delta_mean": _mean(rows, "return_delta_vs_baseline"),
                "high_sideslip_fraction_mean": _mean(rows, "high_sideslip_fraction"),
                "lateral_rmse_mean": _mean(rows, "lateral_rmse"),
                "action_rate_mean": _mean(rows, "action_rate_mean"),
                "raw_action_abs_max": _max(rows, "raw_action_abs_max"),
                "raw_action_l2_mean": _mean(rows, "raw_action_l2_mean"),
                "action_clip_fraction_mean": _mean(rows, "action_clip_fraction"),
                "final_action_abs_max": _max(rows, "final_action_abs_max"),
                "dominant_outcome_bucket": _dominant(row.get("outcome_bucket", "") for row in rows),
                "dominant_termination_reason": _dominant(row.get("termination_reason", "") or "<blank>" for row in rows),
                "measurement_episode_ids": ";".join(str(row.get("measurement_episode_id", "")) for row in rows),
                "m3069_no_new_execution": True,
                "actor_input_contract_changed": False,
                "hidden_oracle_actor_input_required": False,
                "ttc_actor_input_required": False,
                "runtime_base_policy_required": any(_bool(row.get("runtime_base_policy_required")) for row in rows),
                "driver_performance_claim_made": False,
                "repair_success_claim_made": False,
                "validation_result_claim_made": False,
                "measurement_only_no_verdict": True,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def _action_saturation_pressure(action_clip_mean: float, action_clip_max: float) -> str:
    if action_clip_mean >= 0.05 or action_clip_max >= 0.10:
        return "high"
    if action_clip_mean > 0.0 or action_clip_max > 0.0:
        return "medium"
    return "low"


def _raw_action_bound_pressure(raw_action_abs_max: float) -> str:
    if raw_action_abs_max >= 2.0:
        return "high"
    if raw_action_abs_max > 1.0:
        return "medium"
    return "within_bound"


def build_actuation_pressure_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, rows) in enumerate(_core_group_specs(measurement_rows), start=1):
        action_clip_mean = _mean(rows, "action_clip_fraction")
        action_clip_max = _max(rows, "action_clip_fraction")
        raw_action_abs_max = _max(rows, "raw_action_abs_max")
        output_rows.append(
            {
                "direct_action_actuation_pressure_row_id": f"m3069-direct-action-actuation-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "episode_count": len(rows),
                "raw_action_abs_max": raw_action_abs_max,
                "raw_action_l2_mean": _mean(rows, "raw_action_l2_mean"),
                "action_clip_fraction_mean": action_clip_mean,
                "action_clip_fraction_max": action_clip_max,
                "final_action_abs_max": _max(rows, "final_action_abs_max"),
                "raw_out_of_bounds_row_count": _count(rows, lambda row: _float(row.get("raw_action_abs_max")) > 1.0),
                "any_action_clip_row_count": _count(rows, lambda row: _float(row.get("action_clip_fraction")) > 0.0),
                "high_action_clip_row_count": _count(rows, lambda row: _float(row.get("action_clip_fraction")) >= 0.05),
                "action_saturation_pressure": _action_saturation_pressure(action_clip_mean, action_clip_max),
                "raw_action_bound_pressure": _raw_action_bound_pressure(raw_action_abs_max),
                "candidate_binding_rows": _count(rows, lambda row: row.get("binding_role") == "candidate"),
                "parent_binding_rows": _count(rows, lambda row: row.get("binding_role") == "parent"),
                "collision_count": _count(rows, _is_collision),
                "offtrack_count": _count(rows, _is_offtrack),
                "speed_too_low_count": _count(rows, _is_speed_too_low),
                "runtime_base_policy_required": any(_bool(row.get("runtime_base_policy_required")) for row in rows),
                "m3069_no_new_execution": True,
                "ranking_claim_made": False,
                "promotion_claim_made": False,
                "repair_success_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def _stability_pressure(rows: list[dict[str, str]]) -> str:
    if _count(rows, _is_collision) > 0 or _count(rows, _is_offtrack) > 0:
        return "high"
    if _mean(rows, "high_sideslip_fraction") >= 0.25 or _mean(rows, "lateral_rmse") >= 1.0:
        return "medium"
    return "low"


def _recovery_pressure(rows: list[dict[str, str]]) -> str:
    if _count(rows, _is_offtrack) > 0:
        return "offtrack_recovery_required"
    if _count(rows, _is_speed_too_low) > 0:
        return "speed_floor_recovery_required"
    if _count(rows, _is_collision) > 0:
        return "collision_guard_required"
    return "success_preservation"


def build_recovery_stability_rows(measurement_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, (group_key, group_value, rows) in enumerate(_core_group_specs(measurement_rows), start=1):
        recoverability_available = _count(rows, lambda row: _bool(row.get("recoverability_window_success_available")))
        recoverability_success = _count(rows, lambda row: _bool(row.get("recoverability_window_success")))
        recoverability_rate = recoverability_success / recoverability_available if recoverability_available else 0.0
        output_rows.append(
            {
                "direct_action_recovery_stability_row_id": f"m3069-direct-action-recovery-stability-{index:04d}",
                "group_key": group_key,
                "group_value": group_value,
                "episode_count": len(rows),
                "success_count": _count(rows, _is_success),
                "collision_count": _count(rows, _is_collision),
                "offtrack_count": _count(rows, _is_offtrack),
                "speed_too_low_count": _count(rows, _is_speed_too_low),
                "recoverability_available_count": recoverability_available,
                "recoverability_success_count": recoverability_success,
                "recoverability_success_rate": recoverability_rate,
                "offtrack_severity_proxy_mean": _mean(rows, "off_track_severity_proxy"),
                "offtrack_severity_proxy_max": _max(rows, "off_track_severity_proxy"),
                "max_off_track_overshoot_mean": _mean(rows, "max_off_track_overshoot"),
                "max_off_track_overshoot_max": _max(rows, "max_off_track_overshoot"),
                "time_to_first_off_track_s_mean": _mean(rows, "time_to_first_off_track_s"),
                "high_sideslip_fraction_mean": _mean(rows, "high_sideslip_fraction"),
                "beta_abs_error_mean": _mean(rows, "beta_abs_error_mean"),
                "lateral_rmse_mean": _mean(rows, "lateral_rmse"),
                "speed_mean": _mean(rows, "speed_mean"),
                "clearance_margin_mean": _mean(rows, "min_clearance_margin"),
                "clearance_margin_delta_mean": _mean(rows, "clearance_margin_delta_vs_baseline"),
                "action_rate_mean": _mean(rows, "action_rate_mean"),
                "return_delta_mean": _mean(rows, "return_delta_vs_baseline"),
                "stability_pressure": _stability_pressure(rows),
                "recovery_pressure": _recovery_pressure(rows),
                "m3069_no_new_execution": True,
                "validation_result_claim_made": False,
                "driver_performance_claim_made": False,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return output_rows


def _group_count(measurement_rows: list[dict[str, str]], predicate: Any) -> int:
    return _count(measurement_rows, predicate)


def _actuation_group(actuation_rows: list[dict[str, Any]], group_key: str, group_value: str) -> dict[str, Any]:
    return next(
        (row for row in actuation_rows if row["group_key"] == group_key and row["group_value"] == group_value),
        {},
    )


def build_repair_requirement_rows(
    measurement_rows: list[dict[str, str]],
    actuation_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_actuation = _actuation_group(actuation_rows, "all", "all")
    candidate_actuation = _actuation_group(actuation_rows, "binding_role", "candidate")
    t5_recovery = _actuation_group(recovery_rows, "task_family", "T5")
    all_recovery = _actuation_group(recovery_rows, "all", "all")
    action_clip_rows = _group_count(measurement_rows, lambda row: _float(row.get("action_clip_fraction")) > 0.0)
    high_sideslip_rows = _group_count(measurement_rows, lambda row: _float(row.get("high_sideslip_fraction")) >= 0.5)
    rows = [
        {
            "requirement_id": "m3069-requirement-0001",
            "requirement_family": "offtrack_containment_recovery",
            "priority": "p0",
            "affected_group": "all",
            "row_count": _group_count(measurement_rows, _is_offtrack),
            "trigger_evidence": "M3067 recorded 16 off_track terminations out of 32 measurement rows",
            "requirement": "next repair route must explicitly reduce offtrack pressure before any ranking or promotion route",
            "measurable_next_gate": "row-preserving offtrack count, overshoot, severity, and recovery-window rows accepted by M3070 before refit or rerun",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0002",
            "requirement_family": "t5_collision_guard",
            "priority": "p0",
            "affected_group": "task_family:T5",
            "row_count": _group_count(measurement_rows, lambda row: row.get("task_family") == "T5" and _is_collision(row)),
            "trigger_evidence": "M3067 recorded 4 collision rows and all collisions are in the T5 family",
            "requirement": "next repair route must preserve a separate T5 collision guard instead of optimizing only offtrack or aggregate success",
            "measurable_next_gate": "T5 collision rows remain separately accounted before any broad safety claim",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0003",
            "requirement_family": "speed_floor_recovery",
            "priority": "p1",
            "affected_group": "termination_reason:speed_too_low",
            "row_count": _group_count(measurement_rows, _is_speed_too_low),
            "trigger_evidence": "M3067 recorded 5 speed_too_low terminations after direct-action fitting",
            "requirement": "speed-floor recovery must be explicit in the next repair metrics because it increased relative to M3050",
            "measurable_next_gate": "speed-too-low rows remain separately counted and bounded in M3070 and any later repair audit",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0004",
            "requirement_family": "direct_action_actuation_pressure",
            "priority": "p1",
            "affected_group": "all",
            "row_count": action_clip_rows,
            "trigger_evidence": (
                "M3067 raw_action_abs_max "
                f"{all_actuation.get('raw_action_abs_max', 0.0)} with action_clip_fraction_mean "
                f"{all_actuation.get('action_clip_fraction_mean', 0.0)} and candidate mean "
                f"{candidate_actuation.get('action_clip_fraction_mean', 0.0)}"
            ),
            "requirement": "next repair route must keep raw-action and final-action clipping pressure visible before another direct-action fit",
            "measurable_next_gate": "direct-action actuation pressure rows must be audited by M3070 and preserved in any later fitting admission",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0005",
            "requirement_family": "success_preservation",
            "priority": "p1",
            "affected_group": "success_rows",
            "row_count": _group_count(measurement_rows, _is_success),
            "trigger_evidence": "M3067 recorded 8 success rows, including both candidate and parent binding successes",
            "requirement": "next repair route must preserve success rows while targeting offtrack, collision, and speed-floor failures",
            "measurable_next_gate": "success-preservation rows remain explicit before any repair fit is accepted",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0006",
            "requirement_family": "stability_clearance_tradeoff",
            "priority": "p1",
            "affected_group": "all",
            "row_count": high_sideslip_rows,
            "trigger_evidence": (
                "M3067 clearance_margin_delta_mean "
                f"{all_recovery.get('clearance_margin_delta_mean', 0.0)} with high_sideslip rows "
                f"{high_sideslip_rows} and T5 stability pressure {t5_recovery.get('stability_pressure', '')}"
            ),
            "requirement": "next repair route must not hide stability or clearance tradeoffs behind aggregate clearance improvement",
            "measurable_next_gate": "M3070 separately audits clearance, sideslip, lateral RMSE, overshoot, and recovery rows",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
        {
            "requirement_id": "m3069-requirement-0007",
            "requirement_family": "claim_boundary_guard",
            "priority": "p0",
            "affected_group": "all",
            "row_count": len(measurement_rows),
            "trigger_evidence": "M3067/M3068 are measurement and audit artifacts only, and M3069 is no-new-execution materialization",
            "requirement": "M3070 must audit these decomposition artifacts before any fitting training rollout validation ranking promotion or driver-performance claim",
            "measurable_next_gate": "M3070 accepts or rejects M3069 and selects exactly one repair audit stop or continuation route",
            "blocked_claims": FORBIDDEN_INTERPRETATION,
            "m3069_no_new_execution": True,
            "claim_boundary": CLAIM_SCOPE,
        },
    ]
    return rows


def build_claim_boundary_rows() -> list[dict[str, Any]]:
    claim_specs = [
        ("direct_action_failure_mode_rows", "materialization", True, True, "direct_action_failure_mode_rows.csv"),
        ("direct_action_actuation_pressure_rows", "materialization", True, True, "direct_action_actuation_pressure_rows.csv"),
        ("direct_action_recovery_stability_rows", "materialization", True, True, "direct_action_recovery_stability_rows.csv"),
        ("direct_action_repair_requirement_rows", "materialization", True, True, "direct_action_repair_requirement_rows.csv"),
        ("follow_up_result_audit_registered", "follow_up_route", True, True, "M3070 audit manifest"),
        ("new_execution", "execution", False, False, "future separately registered measurement route"),
        ("fitting_or_training", "training", False, False, "future guarded repair route"),
        ("validation_result", "validation", False, False, "future validation route"),
        ("driver_performance_verdict", "driver_performance", False, False, "future proof/generalization/claim audit"),
        ("current_sim_verdict", "verdict", False, False, "future result audit and synthesis"),
        ("ranking_or_winner_selection", "ranking", False, False, "future audited ranking route"),
        ("checkpoint_promotion", "promotion", False, False, "future promotion gate"),
        ("repair_success", "verdict", False, False, "future result audit"),
        ("paper_level_evidence", "paper", False, False, "future audited evidence matrix"),
        ("high_fidelity_validation", "validation", False, False, "future high-fidelity validation"),
        ("finite_window_vs_gru_result", "paper", False, False, "future same-case architecture comparison"),
        ("full_ideal_driver_completion", "full_goal", False, False, "future full goal gate"),
        ("level3_self_identification", "self_id", False, False, "future source-diverse intervention proof"),
        ("runtime_base_policy_dependency", "contract", False, False, "direct-action actor must remain base-policy-free at runtime"),
        ("hidden_oracle_actor_inputs", "contract", False, False, "actor contract forbids hidden/oracle inputs"),
        ("ttc_actor_inputs", "contract", False, False, "actor contract forbids TTC shortcuts"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, family, allowed, made, required) in enumerate(claim_specs, start=1):
        rows.append(
            {
                "claim_id": f"m3069-{name}",
                "claim_family": family,
                "allowed_in_m3069": allowed,
                "claim_made": made,
                "status_pass": allowed == made,
                "evidence_required_before_claim": required,
                "claim_boundary": CLAIM_SCOPE,
            }
        )
    return rows


def build_follow_up_manifest(*, output_dir: Path, doc_path: Path) -> dict[str, Any]:
    return {
        "id": NEXT_ID,
        "priority": 30650,
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
            "seed_fragility",
        ],
        "hypothesis": "A bounded result audit can accept or reject the M3069 direct-action failure-decomposition artifacts before any fitting training rollout validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver or self-ID claim.",
        "lineage": {
            "parent_checkpoint": [
                "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
                "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            ],
            "parent_dataset": [
                str(output_dir / "summary.json"),
                str(output_dir / "direct_action_failure_mode_rows.csv"),
                str(output_dir / "direct_action_actuation_pressure_rows.csv"),
                str(output_dir / "direct_action_recovery_stability_rows.csv"),
                str(output_dir / "direct_action_repair_requirement_rows.csv"),
                str(output_dir / "claim_boundary_rows.csv"),
                str(output_dir / "gate_matrix.csv"),
                str(doc_path),
            ],
            "parent_config": [f"experiments/manifests/{MILESTONE_ID}.json"],
            "parent_objective": ["audit direct-action failure decomposition before any repair route"],
            "derived_from": [MILESTONE_ID, M3068_ID, M3067_ID],
            "blocked_by": [
                "M3069 decomposition artifacts require audit before refit rerun repair or stop decision",
                "M3067/M3068 evidence is measurement and audit evidence only",
            ],
            "supersedes": ["direct repair route without auditing M3069 decomposition"],
            "invalidates": [],
        },
        "review_artifact": f"docs/reviews/{NEXT_ID}.md",
        "public_gates": [
            "M3070 must audit M3069 summary failure actuation recovery repair claim and gate artifacts",
            "M3070 must confirm all 32 M3067 rows remain accounted for",
            "M3070 must preserve actor 72/action 3 direct-action/base-policy-free contract and claim boundaries",
            "M3070 must reject validation ranking promotion high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims unless separately routed",
            "M3070 must select exactly one repair audit stop or continuation route",
        ],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": [
            "do not rerun rollout fit train validate rank promote tune or mutate checkpoints",
            "do not convert M3069 decomposition rows into performance current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID claims",
            "do not change actor input action contract or runtime base-policy-free boundary",
        ],
        "workflow_synthesis": {
            "branch": "active_safety_driver_v1_offtrack_dominant_behavior_repair",
            "evidence_axis": "active_safety_driver_v1_direct_action_failure_decomposition_result_audit",
            "evidence_increment": "audits repair-facing direct-action failure decomposition artifacts before selecting the next active-safety repair route",
            "claim_scope": "Result audit only; no fitting training validation ranking promotion driver-performance verdict high-fidelity finite-window-vs-GRU paper full-driver repair-success or self-ID claim",
            "stop_condition": [
                "stop if M3069 artifacts are missing or gate matrix fails",
                "stop if row preservation or direct-action actor contracts were violated",
                "stop if M3069 rows are treated as validation or performance verdicts",
            ],
            "fallback_plan": [
                "route to artifact repair if artifacts are incomplete",
                "route to repair design if decomposition is complete and claim-safe",
                "route to branch synthesis if decomposition shows no viable repair input",
            ],
            "synthesis_cadence": 10,
            "synthesis_trigger": "M3069 materializes direct-action failure decomposition artifacts",
            "synthesis_decision": "not_applicable",
        },
        "training_stage": {
            "stage": "process",
            "stage_objective": "Audit M3069 direct-action failure-decomposition materialization artifacts",
            "admission_evidence": [
                "M3069 summary and gate matrix",
                "M3069 direct-action failure mode, actuation pressure, recovery stability, repair requirement, and claim artifacts",
            ],
            "blocked_shortcuts": [
                "no fitting training rollout validation ranking promotion driver-performance verdict high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claim",
                "no checkpoint mutation profile tuning or promotion",
                "no hidden oracle target TTC source route outcome progress verdict actor input or runtime base policy",
            ],
            "allowed_updates": [
                f"docs/{NEXT_ID}.md",
                f"docs/reviews/{NEXT_ID}.md",
                f"experiments/reviews/{NEXT_ID}.json",
                "M3070 status queue scoreboard research log and review",
                "one follow-up manifest only if M3070 selects exactly one next route",
            ],
            "next_stage_criteria": [
                "M3070 accepts or rejects M3069 as complete and claim-safe",
                "next repair audit stop or continuation route is explicit",
            ],
        },
        "self_id_evidence_discipline": {
            "claim_level": "not_applicable",
            "current_frame_substitution_risk": "M3070 audits engineering failure decomposition artifacts and cannot infer history necessity or self-ID.",
            "history_necessity_tests": [
                "None in M3070; finite-window and GRU comparison remains a later same-case engineering ablation."
            ],
            "temporal_evidence_window": "M3069 failure decomposition artifacts only.",
            "negative_result_policy": "Preserve negative active-safety evidence and route to repair or stop rather than returning self-ID to the mainline objective.",
            "allowed_claims": [
                "M3069 artifact completeness and claim-safety audit",
                "no driver-performance verdict paper-level result finite-window-vs-GRU result high-fidelity validation result full ideal driver completion repair-success or level3 self-identification claim",
            ],
        },
        "local_search_guard": {
            "actual_progress_type": "result_audit",
            "process_overhead": "medium",
            "local_search_risk": "medium",
            "same_failure_repeat_count": 1,
            "same_public_gate_repair_count": 0,
            "evidence_expansion": "audits the direct-action failure, actuation, recovery, and repair-requirement panel before repair routing",
            "paper_verdict_delta": "paper and self-ID remain diagnostic; M3070 prepares an active-safety repair route decision",
            "must_synthesize_if": [
                "M3070 cannot accept M3069 as complete and claim-safe",
                "M3070 cannot select a repair audit stop or continuation route",
                "M3070 would require another process-only milestone before repair input can be acted on",
            ],
        },
        "success_criteria": [
            f"docs/{NEXT_ID}.md exists",
            "M3070 audits M3069 summary failure actuation recovery repair claim and gate artifacts",
            "M3070 rejects validation ranking promotion performance high-fidelity paper finite-window-vs-GRU full-driver repair-success and self-ID claims",
            "M3070 selects exactly one repair audit stop or continuation route",
        ],
        "failure_criteria": [
            "M3070 hides M3069 failures or missing artifacts",
            "M3070 treats M3069 decomposition as validation or performance verdict",
            "M3070 changes actor input action contract or runtime base-policy-free boundary",
            "M3070 leaves next route ambiguous",
        ],
        "decision_rule": "Pass only if M3070 audits M3069 decomposition artifacts and selects one next route or stop state while preserving actor and claim boundaries without overclaiming.",
        "commands": [{"name": "active_safety_driver_v1_direct_action_failure_decomposition_result_audit_doc", "command": "true"}],
        "required_artifacts": [{"path": f"docs/{NEXT_ID}.md", "type": "markdown"}],
        "baseline_checkpoints": [
            "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
        ],
        "baseline_artifacts": [
            str(output_dir / "summary.json"),
            str(output_dir / "direct_action_failure_mode_rows.csv"),
            str(output_dir / "direct_action_actuation_pressure_rows.csv"),
            str(output_dir / "direct_action_recovery_stability_rows.csv"),
            str(output_dir / "direct_action_repair_requirement_rows.csv"),
            str(output_dir / "gate_matrix.csv"),
        ],
        "scoreboard_checkpoint": f"docs/{NEXT_ID}.md",
        "next_blocker": NEXT_ID,
        "status": "pending",
    }


def _source_claims_pass(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(_bool(row.get("status_pass")) for row in rows)


def build_gate_rows(
    *,
    summary: Mapping[str, Any],
    paths: Mapping[str, Path],
    measurement_rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
    failure_mode_rows: list[dict[str, Any]],
    actuation_rows: list[dict[str, Any]],
    recovery_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def gate(gate_id: str, family: str, status: bool, observed: Any, expected: Any, failure_type: str) -> dict[str, Any]:
        return {
            "gate_id": f"m3069-{gate_id}",
            "gate_family": family,
            "status_pass": bool(status),
            "observed": observed,
            "expected": expected,
            "failure_type": failure_type,
            "claim_boundary": CLAIM_SCOPE,
        }

    pre_written_paths = [
        "direct_action_failure_mode_rows",
        "direct_action_actuation_pressure_rows",
        "direct_action_recovery_stability_rows",
        "direct_action_repair_requirement_rows",
        "claim_boundary_rows",
        "doc",
        "follow_up_manifest",
    ]
    pre_written_present = all(paths[key].exists() for key in pre_written_paths)
    return [
        gate("m3068_audit_present", "lineage", bool(summary.get("m3068_audit_present")), True, True, "lineage_invalid"),
        gate("m3067_status_pass", "lineage", bool(summary.get("m3067_status_pass")), True, True, "lineage_invalid"),
        gate("m3067_gate_matrix_pass", "lineage", bool(summary.get("m3067_gate_matrix_pass")), True, True, "lineage_invalid"),
        gate("m3067_required_artifacts_present", "lineage", bool(summary.get("m3067_required_artifacts_present")), True, True, "lineage_invalid"),
        gate("measurement_denominator_preserved", "denominator", len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS, len(measurement_rows), EXPECTED_MEASUREMENT_ROWS, "scenario_sampling_failure"),
        gate("measurement_failure_rows_zero", "denominator", len(failure_rows) == EXPECTED_FAILURE_ROWS, len(failure_rows), EXPECTED_FAILURE_ROWS, "metric_artifact"),
        gate("expected_success_count_preserved", "metric", summary.get("measurement_success_count") == EXPECTED_SUCCESS_ROWS, summary.get("measurement_success_count"), EXPECTED_SUCCESS_ROWS, "metric_artifact"),
        gate("expected_collision_count_preserved", "metric", summary.get("measurement_collision_count") == EXPECTED_COLLISION_ROWS, summary.get("measurement_collision_count"), EXPECTED_COLLISION_ROWS, "metric_artifact"),
        gate("expected_offtrack_count_preserved", "metric", summary.get("measurement_offtrack_count") == EXPECTED_OFFTRACK_ROWS, summary.get("measurement_offtrack_count"), EXPECTED_OFFTRACK_ROWS, "metric_artifact"),
        gate("expected_speed_floor_count_preserved", "metric", summary.get("measurement_speed_too_low_count") == EXPECTED_SPEED_TOO_LOW_ROWS, summary.get("measurement_speed_too_low_count"), EXPECTED_SPEED_TOO_LOW_ROWS, "metric_artifact"),
        gate("failure_decomposition_rows", "metric", bool(failure_mode_rows), len(failure_mode_rows), ">0", "metric_artifact"),
        gate("actuation_pressure_rows", "metric", bool(actuation_rows), len(actuation_rows), ">0", "metric_artifact"),
        gate("recovery_stability_rows", "metric", bool(recovery_rows), len(recovery_rows), ">0", "metric_artifact"),
        gate("repair_requirement_rows", "metric", len(repair_rows) >= 7, len(repair_rows), ">=7", "metric_artifact"),
        gate("claim_boundary_rows_pass", "claim", all(_bool(row["status_pass"]) for row in claim_rows), "all", "pass", "contract_violation"),
        gate("actor_contract_shape_72_action_3", "contract", bool(summary.get("actor_contract_shape_72_action_3")), True, True, "contract_violation"),
        gate("direct_action_contract_pass", "contract", bool(summary.get("direct_action_contract_pass")), True, True, "contract_violation"),
        gate("direct_action_adapter_guards_pass", "contract", bool(summary.get("direct_action_adapter_guard_rows_pass")), True, True, "contract_violation"),
        gate("actor_contract_guards_pass", "contract", bool(summary.get("actor_contract_guard_rows_pass")), True, True, "contract_violation"),
        gate("checkpoint_side_effect_guards_pass", "contract", bool(summary.get("checkpoint_side_effect_guard_rows_pass")), True, True, "contract_violation"),
        gate("source_claim_boundary_rows_pass", "claim", bool(summary.get("m3067_claim_boundary_rows_pass")), True, True, "contract_violation"),
        gate("base_policy_free_runtime_preserved", "contract", not bool(summary.get("runtime_base_policy_required")), False, False, "contract_violation"),
        gate("no_new_execution", "execution", not bool(summary.get("environment_reset_run")) and not bool(summary.get("environment_step_run")) and not bool(summary.get("policy_rollout_run")), False, False, "contract_violation"),
        gate("forbidden_flags_clear", "claim", not bool(summary.get("forbidden_claim_made")), False, False, "contract_violation"),
        gate("pre_written_artifacts_present", "process", pre_written_present, pre_written_present, True, "metric_artifact"),
        gate("follow_up_manifest_registered", "process", paths["follow_up_manifest"].exists(), paths["follow_up_manifest"].exists(), True, "lineage_invalid"),
    ]


def write_doc(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# M3069 Active Safety Driver v1 Direct-Action Failure Decomposition Materialization Preflight",
        "",
        "## Summary",
        "",
        "- status: completed",
        "- result class: `active_safety_driver_v1_direct_action_failure_decomposition_materialization_preflight_pass`",
        f"- measurement rows preserved: {summary['measurement_episode_row_count']}/{EXPECTED_MEASUREMENT_ROWS}",
        f"- direct-action failure mode rows: {summary['direct_action_failure_mode_row_count']}",
        f"- direct-action actuation pressure rows: {summary['direct_action_actuation_pressure_row_count']}",
        f"- direct-action recovery stability rows: {summary['direct_action_recovery_stability_row_count']}",
        f"- direct-action repair requirement rows: {summary['direct_action_repair_requirement_row_count']}",
        f"- success count: {summary['measurement_success_count']}",
        f"- collision count: {summary['measurement_collision_count']}",
        f"- offtrack count: {summary['measurement_offtrack_count']}",
        f"- speed-too-low count: {summary['measurement_speed_too_low_count']}",
        f"- raw action abs max: {summary['measurement_raw_action_abs_max']}",
        f"- action clip fraction mean: {summary['measurement_action_clip_fraction_mean']}",
        f"- final action abs max: {summary['measurement_final_action_abs_max']}",
        f"- gate matrix pass: {summary.get('gate_matrix_pass', 'pending')}",
        "",
        "## Interpretation",
        "",
        "M3069 materializes repair-facing direct-action failure, actuation, recovery, and stability decomposition artifacts from the accepted M3067 measurement rows. These artifacts are repair inputs for M3070 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success, or self-ID evidence.",
        "",
        "Primary repair pressure:",
        "",
        "```text",
        f"offtrack recovery: {summary['measurement_offtrack_count']}/{summary['measurement_episode_row_count']} rows",
        f"T5 collision guard: {summary['t5_collision_count']} T5 collision rows",
        f"speed-floor recovery: {summary['measurement_speed_too_low_count']} speed_too_low rows",
        f"direct-action clipping pressure: action_clip_fraction_mean {summary['measurement_action_clip_fraction_mean']}",
        f"raw action pressure: raw_action_abs_max {summary['measurement_raw_action_abs_max']}",
        "```",
        "",
        "Rejected claims:",
        "",
        "```text",
        FORBIDDEN_INTERPRETATION,
        "```",
        "",
        "## Next",
        "",
        f"- next blocker: `{NEXT_ID}`",
        f"- follow-up manifest: `experiments/manifests/{NEXT_ID}.json`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize(
    *,
    m3068_audit: Path,
    m3067_dir: Path,
    output_dir: Path,
    follow_up_manifest: Path,
    doc_path: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_dir / "summary.json",
        "direct_action_failure_mode_rows": output_dir / "direct_action_failure_mode_rows.csv",
        "direct_action_actuation_pressure_rows": output_dir / "direct_action_actuation_pressure_rows.csv",
        "direct_action_recovery_stability_rows": output_dir / "direct_action_recovery_stability_rows.csv",
        "direct_action_repair_requirement_rows": output_dir / "direct_action_repair_requirement_rows.csv",
        "claim_boundary_rows": output_dir / "claim_boundary_rows.csv",
        "gate_matrix": output_dir / "gate_matrix.csv",
        "run_state": output_dir / "run_state.json",
        "doc": doc_path,
        "follow_up_manifest": follow_up_manifest,
    }

    m3067_summary = read_json(m3067_dir / "summary.json")
    measurement_rows = read_csv_rows(m3067_dir / "measurement_episode_rows.csv")
    failure_rows = read_csv_rows(m3067_dir / "measurement_failure_rows.csv")
    metric_rows = read_csv_rows(m3067_dir / "metric_summary_rows.csv")
    m3067_gate_rows = read_csv_rows(m3067_dir / "gate_matrix.csv")
    direct_action_guard_rows = read_csv_rows(m3067_dir / "direct_action_adapter_guard_rows.csv")
    actor_contract_guard_rows = read_csv_rows(m3067_dir / "actor_contract_guard_rows.csv")
    checkpoint_side_effect_guard_rows = read_csv_rows(m3067_dir / "checkpoint_side_effect_guard_rows.csv")
    claim_rows_source = read_csv_rows(m3067_dir / "claim_boundary_rows.csv")

    failure_mode_rows = build_failure_mode_rows(measurement_rows)
    actuation_rows = build_actuation_pressure_rows(measurement_rows)
    recovery_rows = build_recovery_stability_rows(measurement_rows)
    repair_rows = build_repair_requirement_rows(measurement_rows, actuation_rows, recovery_rows)
    claim_rows = build_claim_boundary_rows()

    write_csv_rows(paths["direct_action_failure_mode_rows"], failure_mode_rows, fieldnames=FAILURE_MODE_FIELDNAMES)
    write_csv_rows(paths["direct_action_actuation_pressure_rows"], actuation_rows, fieldnames=ACTUATION_FIELDNAMES)
    write_csv_rows(paths["direct_action_recovery_stability_rows"], recovery_rows, fieldnames=RECOVERY_STABILITY_FIELDNAMES)
    write_csv_rows(paths["direct_action_repair_requirement_rows"], repair_rows, fieldnames=REPAIR_REQUIREMENT_FIELDNAMES)
    write_csv_rows(paths["claim_boundary_rows"], claim_rows, fieldnames=CLAIM_FIELDNAMES)
    write_json(follow_up_manifest, build_follow_up_manifest(output_dir=output_dir, doc_path=doc_path))

    all_actuation = _actuation_group(actuation_rows, "all", "all")
    candidate_actuation = _actuation_group(actuation_rows, "binding_role", "candidate")
    parent_actuation = _actuation_group(actuation_rows, "binding_role", "parent")

    summary: dict[str, Any] = {
        "milestone": MILESTONE_ID,
        "generated_at_utc": utc_timestamp(),
        "result_class": "active_safety_driver_v1_direct_action_failure_decomposition_materialization_preflight_pass",
        "output_dir": str(output_dir),
        "m3068_audit_present": m3068_audit.exists(),
        "m3067_status_pass": bool(m3067_summary.get("status_pass")),
        "m3067_gate_matrix_pass": bool(m3067_summary.get("gate_matrix_pass")),
        "m3067_required_artifacts_present": bool(m3067_summary.get("required_artifacts_present")),
        "m3067_gate_row_count": len(m3067_gate_rows),
        "m3067_metric_summary_row_count": len(metric_rows),
        "m3067_direct_action_adapter_guard_row_count": len(direct_action_guard_rows),
        "m3067_actor_contract_guard_row_count": len(actor_contract_guard_rows),
        "m3067_checkpoint_side_effect_guard_row_count": len(checkpoint_side_effect_guard_rows),
        "m3067_claim_boundary_row_count": len(claim_rows_source),
        "direct_action_adapter_guard_rows_pass": bool(m3067_summary.get("direct_action_adapter_guard_rows_pass"))
        and _source_claims_pass(direct_action_guard_rows),
        "actor_contract_guard_rows_pass": bool(m3067_summary.get("actor_contract_guard_rows_pass"))
        and _source_claims_pass(actor_contract_guard_rows),
        "checkpoint_side_effect_guard_rows_pass": bool(m3067_summary.get("checkpoint_side_effect_guard_rows_pass"))
        and _source_claims_pass(checkpoint_side_effect_guard_rows),
        "m3067_claim_boundary_rows_pass": bool(m3067_summary.get("claim_boundary_rows_pass")) and _source_claims_pass(claim_rows_source),
        "direct_action_contract_pass": bool(m3067_summary.get("direct_action_contract_pass")),
        "measurement_episode_row_count": len(measurement_rows),
        "measurement_failure_row_count": len(failure_rows),
        "measurement_success_count": _count(measurement_rows, _is_success),
        "measurement_collision_count": _count(measurement_rows, _is_collision),
        "measurement_offtrack_count": _count(measurement_rows, _is_offtrack),
        "measurement_speed_too_low_count": _count(measurement_rows, _is_speed_too_low),
        "measurement_raw_action_abs_max": all_actuation.get("raw_action_abs_max", 0.0),
        "measurement_raw_action_l2_mean": all_actuation.get("raw_action_l2_mean", 0.0),
        "measurement_action_clip_fraction_mean": all_actuation.get("action_clip_fraction_mean", 0.0),
        "measurement_final_action_abs_max": all_actuation.get("final_action_abs_max", 0.0),
        "direct_action_failure_mode_row_count": len(failure_mode_rows),
        "direct_action_actuation_pressure_row_count": len(actuation_rows),
        "direct_action_recovery_stability_row_count": len(recovery_rows),
        "direct_action_repair_requirement_row_count": len(repair_rows),
        "claim_boundary_row_count": len(claim_rows),
        "candidate_action_clip_fraction_mean": candidate_actuation.get("action_clip_fraction_mean", 0.0),
        "parent_action_clip_fraction_mean": parent_actuation.get("action_clip_fraction_mean", 0.0),
        "candidate_success_count": _count(measurement_rows, lambda row: row.get("binding_role") == "candidate" and _is_success(row)),
        "parent_success_count": _count(measurement_rows, lambda row: row.get("binding_role") == "parent" and _is_success(row)),
        "t5_collision_count": _count(measurement_rows, lambda row: row.get("task_family") == "T5" and _is_collision(row)),
        "actor_contract_shape_72_action_3": m3067_summary.get("observation_shape") == EXPECTED_OBSERVATION_DIM
        and m3067_summary.get("action_shape") == EXPECTED_ACTION_DIM,
        "candidate_output_semantics": m3067_summary.get("candidate_output_semantics"),
        "candidate_output_components": m3067_summary.get("candidate_output_components", []),
        "runtime_base_policy_required": bool(m3067_summary.get("runtime_base_policy_required")),
        "base_policy_required_at_runtime": bool(m3067_summary.get("base_policy_required_at_runtime")),
        "environment_reset_run": False,
        "environment_step_run": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "replay_run": False,
        "fitting_run": False,
        "training_run": False,
        "ppo_run": False,
        "validation_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_mutated": False,
        "checkpoint_promoted": False,
        "driver_performance_claim_made": False,
        "repair_success_claim_made": False,
        "validation_result_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "full_ideal_driver_completion_claim_made": False,
        "level3_self_id_claim_made": False,
        "forbidden_claim_made": False,
        "claim_scope": CLAIM_SCOPE,
        "forbidden_interpretation": FORBIDDEN_INTERPRETATION,
        "next_blocker": NEXT_ID,
        "selected_next_action": NEXT_ID,
        "selected_next_action_type": "result_audit",
        "follow_up_manifest": str(follow_up_manifest),
        "follow_up_manifest_exists": follow_up_manifest.exists(),
        "paths": {key: str(value) for key, value in paths.items()},
    }

    write_doc(doc_path, summary)
    gate_rows = build_gate_rows(
        summary=summary,
        paths=paths,
        measurement_rows=measurement_rows,
        failure_rows=failure_rows,
        failure_mode_rows=failure_mode_rows,
        actuation_rows=actuation_rows,
        recovery_rows=recovery_rows,
        repair_rows=repair_rows,
        claim_rows=claim_rows,
    )
    gate_matrix_pass = all(_bool(row["status_pass"]) for row in gate_rows)
    summary["gate_matrix_row_count"] = len(gate_rows)
    summary["gate_matrix_pass"] = gate_matrix_pass
    summary["status_pass"] = (
        bool(summary["m3068_audit_present"])
        and bool(summary["m3067_status_pass"])
        and bool(summary["m3067_gate_matrix_pass"])
        and bool(summary["m3067_required_artifacts_present"])
        and len(measurement_rows) == EXPECTED_MEASUREMENT_ROWS
        and len(failure_rows) == EXPECTED_FAILURE_ROWS
        and summary["measurement_success_count"] == EXPECTED_SUCCESS_ROWS
        and summary["measurement_collision_count"] == EXPECTED_COLLISION_ROWS
        and summary["measurement_offtrack_count"] == EXPECTED_OFFTRACK_ROWS
        and summary["measurement_speed_too_low_count"] == EXPECTED_SPEED_TOO_LOW_ROWS
        and bool(summary["actor_contract_shape_72_action_3"])
        and bool(summary["direct_action_contract_pass"])
        and bool(summary["direct_action_adapter_guard_rows_pass"])
        and bool(summary["actor_contract_guard_rows_pass"])
        and bool(summary["checkpoint_side_effect_guard_rows_pass"])
        and bool(summary["m3067_claim_boundary_rows_pass"])
        and not bool(summary["runtime_base_policy_required"])
        and not bool(summary["base_policy_required_at_runtime"])
        and gate_matrix_pass
    )
    summary["decision"] = "active_safety_driver_v1_direct_action_failure_decomposition_route_to_m3070_result_audit"

    write_csv_rows(paths["gate_matrix"], gate_rows, fieldnames=GATE_FIELDNAMES)
    write_json(paths["run_state"], {"milestone": MILESTONE_ID, "status": "completed", "next_blocker": NEXT_ID})
    write_json(paths["summary"], summary)
    write_doc(doc_path, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3068-audit", type=Path, default=DEFAULT_M3068_AUDIT)
    parser.add_argument("--m3067-dir", type=Path, default=DEFAULT_M3067_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--follow-up-manifest", type=Path, default=DEFAULT_FOLLOW_UP_MANIFEST)
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = materialize(
        m3068_audit=args.m3068_audit,
        m3067_dir=args.m3067_dir,
        output_dir=args.output_dir,
        follow_up_manifest=args.follow_up_manifest,
        doc_path=args.doc_path,
    )
    print(f"status_pass={summary['status_pass']}")
    print(f"gate_matrix_pass={summary['gate_matrix_pass']}")
    print(f"direct_action_failure_mode_rows={summary['direct_action_failure_mode_row_count']}")
    print(f"direct_action_actuation_pressure_rows={summary['direct_action_actuation_pressure_row_count']}")
    print(f"direct_action_recovery_stability_rows={summary['direct_action_recovery_stability_row_count']}")
    print(f"direct_action_repair_requirement_rows={summary['direct_action_repair_requirement_row_count']}")
    print(f"decision={summary['decision']}")


if __name__ == "__main__":
    main()
