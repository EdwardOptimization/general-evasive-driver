"""Role-bounded success semantics for current-sim scenario task-family rows."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


R0_STABLE_AVOIDABLE = "R0_stable_avoidable"


def bool_value(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def is_collision(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "collision_failure" or bool_value(row.get("collision"))


def is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion" or str(
        row.get("termination_reason", "")
    ) == "off_track"


def raw_obstacle_pass_success(row: Mapping[str, Any]) -> bool:
    if "raw_success" in row:
        return bool_value(row.get("raw_success"))
    if str(row.get("outcome_bucket", "")) == "success_obstacle_pass":
        return True
    if "success" in row:
        return bool_value(row.get("success"))
    return bool_value(row.get("obstacle_completed")) and not bool_value(row.get("collision"))


def is_r0_safe_stop_success(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("role_family", "")) == R0_STABLE_AVOIDABLE
        and str(row.get("termination_reason", "")) == "speed_too_low"
        and float_value(row.get("min_clearance_margin")) > 0.0
        and not is_collision(row)
        and not is_offtrack(row)
    )


def role_success(row: Mapping[str, Any]) -> bool:
    return raw_obstacle_pass_success(row) or is_r0_safe_stop_success(row)


def role_success_reason(row: Mapping[str, Any]) -> str:
    if raw_obstacle_pass_success(row):
        return "obstacle_pass_success"
    if is_r0_safe_stop_success(row):
        return "r0_safe_stop_success"
    if is_collision(row):
        return "collision_failure"
    if is_offtrack(row):
        return "offtrack_failure"
    if str(row.get("termination_reason", "")) == "speed_too_low":
        return "speed_too_low_non_success"
    if bool_value(row.get("truncated")) or str(row.get("outcome_bucket", "")) == "max_steps_noncompletion":
        return "max_step_noncompletion"
    return "other_non_success"


def role_success_outcome_bucket(row: Mapping[str, Any]) -> str:
    if raw_obstacle_pass_success(row):
        return "success_obstacle_pass"
    if is_r0_safe_stop_success(row):
        return "success_safe_stop"
    return str(row.get("outcome_bucket", ""))


def annotate_role_success(row: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(row)
    raw_success = raw_obstacle_pass_success(row)
    output["raw_success"] = raw_success
    output["role_success"] = role_success({**output, "raw_success": raw_success})
    output["role_success_reason"] = role_success_reason(output)
    output["role_success_outcome_bucket"] = role_success_outcome_bucket(output)
    output["success"] = output["role_success"]
    return output
