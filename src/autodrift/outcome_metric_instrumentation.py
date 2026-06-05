"""Logging-only outcome metric helpers for task-quality evaluation."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable, Mapping

import numpy as np


RECOVERY_HOLD_SECONDS = 0.5
RECOVERY_BETA_LIMIT = 0.24
RECOVERY_YAW_RATE_LIMIT = 1.5
RECOVERY_MIN_SPEED = 2.0
RECOVERY_LATERAL_FRACTION = 0.8
DRIFT_USED_BETA_THRESHOLD = 0.35
IMPACT_PENETRATION_WEIGHT = 5.0
IMPACT_BETA_WEIGHT = 0.5
IMPACT_YAW_RATE_WEIGHT = 0.1
R4_MITIGATION_CANONICAL_FIELDS = (
    "impact_speed_mps",
    "impact_speed_mps_available",
    "delta_v_at_impact_mps",
    "delta_v_at_impact_mps_available",
    "time_to_collision_s",
    "time_to_collision_s_available",
    "collision_angle_or_side",
    "collision_angle_or_side_available",
    "collision_side_proxy",
    "post_event_speed_mps",
    "post_event_speed_mps_available",
    "post_event_yaw_rate_abs",
    "post_event_yaw_rate_abs_available",
    "post_event_offtrack_overshoot",
    "post_event_offtrack_overshoot_available",
    "recoverability_window_success",
    "recoverability_window_success_available",
)
BOOLEAN_OUTCOME_METRIC_FIELDS = {
    "recovery_success",
    "drift_used",
    "controlled_drift_recovery_success",
    "impact_speed_mps_available",
    "delta_v_at_impact_mps_available",
    "time_to_collision_s_available",
    "collision_angle_or_side_available",
    "post_event_speed_mps_available",
    "post_event_yaw_rate_abs_available",
    "post_event_offtrack_overshoot_available",
    "recoverability_window_success",
    "recoverability_window_success_available",
}
STRING_OUTCOME_METRIC_FIELDS = {
    "collision_angle_or_side",
    "collision_side_proxy",
}
OUTCOME_METRIC_FIELDS = (
    "dt",
    "track_width",
    "first_obstacle_pass_step",
    "first_obstacle_pass_time_s",
    "first_recovery_step",
    "first_recovery_time_s",
    "recovery_success",
    "recovery_time_proxy",
    "max_abs_beta",
    "max_abs_yaw_rate",
    "drift_used",
    "controlled_drift_recovery_success",
    "impact_speed_proxy",
    "impact_beta_abs",
    "impact_yaw_rate_abs",
    "impact_severity_proxy",
    "collision_mitigation_score",
    "max_off_track_overshoot",
    "time_to_first_off_track_s",
    "off_track_severity_proxy",
    *R4_MITIGATION_CANONICAL_FIELDS,
)


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _dt_from_infos(step_infos: list[Mapping[str, Any]], default_dt: float) -> float:
    for info in reversed(step_infos):
        value = _finite_float(info.get("dt"), default=float("nan"))
        if value > 0.0:
            return value
    return float(default_dt) if float(default_dt) > 0.0 else 0.02


def _track_width_from_infos(step_infos: list[Mapping[str, Any]], default_track_width: float) -> float:
    for info in reversed(step_infos):
        value = _finite_float(info.get("track_width"), default=float("nan"))
        if value > 0.0:
            return value
    return float(default_track_width) if float(default_track_width) > 0.0 else 5.0


def _step_number(info: Mapping[str, Any], fallback_index: int) -> float:
    step = _finite_float(info.get("step"), default=float("nan"))
    return step if np.isfinite(step) else float(fallback_index + 1)


def _stable_corridor(info: Mapping[str, Any], *, track_width: float) -> bool:
    termination_reason = str(info.get("termination_reason", "") or "")
    return (
        not _bool_value(info.get("collision", False))
        and termination_reason not in {"off_track", "yaw_rate_limit", "non_finite_state"}
        and abs(_finite_float(info.get("beta"))) <= RECOVERY_BETA_LIMIT
        and abs(_finite_float(info.get("yaw_rate"))) <= RECOVERY_YAW_RATE_LIMIT
        and _finite_float(info.get("speed")) >= RECOVERY_MIN_SPEED
        and abs(_finite_float(info.get("lateral_error"))) <= RECOVERY_LATERAL_FRACTION * track_width
    )


def _first_index(values: Iterable[bool]) -> int | None:
    for index, value in enumerate(values):
        if value:
            return index
    return None


def _default_outcome_metrics() -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field in OUTCOME_METRIC_FIELDS:
        if field in BOOLEAN_OUTCOME_METRIC_FIELDS:
            output[field] = False
        elif field in STRING_OUTCOME_METRIC_FIELDS:
            output[field] = ""
        else:
            output[field] = float("nan")
    return output


def _collision_side_proxy(info: Mapping[str, Any]) -> str:
    body_x = _finite_float(info.get("active_obstacle_body_x"), default=float("nan"))
    body_y = _finite_float(info.get("active_obstacle_body_y"), default=float("nan"))
    if not np.isfinite(body_x) or not np.isfinite(body_y):
        return ""
    if abs(body_x) >= abs(body_y):
        return "front" if body_x >= 0.0 else "rear"
    return "left" if body_y >= 0.0 else "right"


def _stable_recovery_index(step_infos: list[Mapping[str, Any]], *, pass_index: int, dt: float, track_width: float) -> int | None:
    hold_steps = max(1, int(math.ceil(RECOVERY_HOLD_SECONDS / max(dt, 1e-6))))
    stable = [_stable_corridor(info, track_width=track_width) for info in step_infos]
    for end_index in range(pass_index, len(step_infos)):
        start = max(0, end_index - hold_steps + 1)
        if end_index - start + 1 < hold_steps:
            continue
        if all(stable[start : end_index + 1]):
            return end_index
    return None


def _recoverability_window_success(
    step_infos: list[Mapping[str, Any]], *, off_track_index: int, dt: float, track_width: float
) -> tuple[bool, bool]:
    hold_steps = max(1, int(math.ceil(RECOVERY_HOLD_SECONDS / max(dt, 1e-6))))
    post_event_infos = step_infos[off_track_index + 1 :]
    if len(post_event_infos) < hold_steps:
        return False, False
    stable = [_stable_corridor(info, track_width=track_width) for info in post_event_infos]
    for end_index in range(hold_steps - 1, len(stable)):
        start = end_index - hold_steps + 1
        if all(stable[start : end_index + 1]):
            return True, True
    return False, True


def compute_episode_outcome_metrics(
    step_infos: list[Mapping[str, Any]],
    *,
    default_dt: float = 0.02,
    default_track_width: float = 5.0,
) -> dict[str, Any]:
    """Compute logging-only outcome metrics from evaluator step info rows."""

    if not step_infos:
        return _default_outcome_metrics()

    dt = _dt_from_infos(step_infos, default_dt)
    track_width = _track_width_from_infos(step_infos, default_track_width)
    steps = [_step_number(info, index) for index, info in enumerate(step_infos)]
    times = [step * dt for step in steps]
    pass_index = _first_index(
        _bool_value(info.get("obstacle_passed_raw", False)) or _bool_value(info.get("obstacle_completed", False))
        for info in step_infos
    )
    recovery_index = (
        _stable_recovery_index(step_infos, pass_index=pass_index, dt=dt, track_width=track_width)
        if pass_index is not None
        else None
    )
    collision_index = _first_index(_bool_value(info.get("collision", False)) for info in step_infos)
    overshoots = [
        max(abs(_finite_float(info.get("lateral_error"), default=0.0)) - track_width, 0.0)
        for info in step_infos
    ]
    off_track_index = _first_index(
        overshoot > 0.0 or str(info.get("termination_reason", "") or "") == "off_track"
        for overshoot, info in zip(overshoots, step_infos)
    )
    betas = [abs(_finite_float(info.get("beta"))) for info in step_infos]
    yaw_rates = [abs(_finite_float(info.get("yaw_rate"))) for info in step_infos]
    finite_betas = [value for value in betas if np.isfinite(value)]
    finite_yaw_rates = [value for value in yaw_rates if np.isfinite(value)]
    max_abs_beta = max(finite_betas) if finite_betas else float("nan")
    max_abs_yaw_rate = max(finite_yaw_rates) if finite_yaw_rates else float("nan")
    drift_used = bool(np.isfinite(max_abs_beta) and max_abs_beta >= DRIFT_USED_BETA_THRESHOLD)
    recovery_success = recovery_index is not None
    final_info = step_infos[-1]
    bad_terminal = str(final_info.get("termination_reason", "") or "") in {"off_track", "yaw_rate_limit", "non_finite_state"}
    controlled_drift_recovery_success = bool(
        pass_index is not None
        and recovery_success
        and not _bool_value(final_info.get("collision", False))
        and not bad_terminal
    )

    if pass_index is None:
        first_pass_step = float("nan")
        first_pass_time = float("nan")
    else:
        first_pass_step = steps[pass_index]
        first_pass_time = times[pass_index]
    if recovery_index is None:
        first_recovery_step = float("nan")
        first_recovery_time = float("nan")
        recovery_time_proxy = float("nan")
    else:
        first_recovery_step = steps[recovery_index]
        first_recovery_time = times[recovery_index]
        recovery_time_proxy = max(0.0, first_recovery_time - first_pass_time) if np.isfinite(first_pass_time) else float("nan")

    if collision_index is None:
        impact_speed = float("nan")
        impact_beta_abs = float("nan")
        impact_yaw_rate_abs = float("nan")
        impact_severity = float("nan")
        collision_mitigation_score = 0.0
        time_to_collision = float("nan")
        collision_side_proxy = ""
    else:
        impact_info = step_infos[collision_index]
        impact_speed = max(_finite_float(impact_info.get("speed"), default=0.0), 0.0)
        impact_beta_abs = abs(_finite_float(impact_info.get("beta"), default=0.0))
        impact_yaw_rate_abs = abs(_finite_float(impact_info.get("yaw_rate"), default=0.0))
        penetration = max(0.0, -_finite_float(impact_info.get("min_clearance_margin"), default=0.0))
        impact_severity = (
            impact_speed
            + IMPACT_PENETRATION_WEIGHT * penetration
            + IMPACT_BETA_WEIGHT * impact_beta_abs
            + IMPACT_YAW_RATE_WEIGHT * impact_yaw_rate_abs
        )
        collision_mitigation_score = impact_severity
        time_to_collision = times[collision_index]
        collision_side_proxy = _collision_side_proxy(impact_info)

    max_off_track_overshoot = max(overshoots) if overshoots else float("nan")
    time_to_first_off_track = times[off_track_index] if off_track_index is not None else float("nan")
    off_track_severity = max_off_track_overshoot
    collision_available = collision_index is not None
    event_index = off_track_index if off_track_index is not None else collision_index
    post_event_infos = step_infos[event_index + 1 :] if event_index is not None else []
    post_event_available = bool(post_event_infos)
    if post_event_available:
        post_event_speed = _finite_float(post_event_infos[-1].get("speed"), default=float("nan"))
        post_event_yaw_rate_abs = abs(_finite_float(post_event_infos[-1].get("yaw_rate"), default=float("nan")))
        post_event_offtrack_overshoot = max(overshoots[event_index + 1 :])
    else:
        post_event_speed = float("nan")
        post_event_yaw_rate_abs = float("nan")
        post_event_offtrack_overshoot = float("nan")
    if off_track_index is None:
        recoverability_success = False
        recoverability_available = False
    else:
        recoverability_success, recoverability_available = _recoverability_window_success(
            step_infos, off_track_index=off_track_index, dt=dt, track_width=track_width
        )
    return {
        "dt": dt,
        "track_width": track_width,
        "first_obstacle_pass_step": first_pass_step,
        "first_obstacle_pass_time_s": first_pass_time,
        "first_recovery_step": first_recovery_step,
        "first_recovery_time_s": first_recovery_time,
        "recovery_success": recovery_success,
        "recovery_time_proxy": recovery_time_proxy,
        "max_abs_beta": max_abs_beta,
        "max_abs_yaw_rate": max_abs_yaw_rate,
        "drift_used": drift_used,
        "controlled_drift_recovery_success": controlled_drift_recovery_success,
        "impact_speed_proxy": impact_speed,
        "impact_beta_abs": impact_beta_abs,
        "impact_yaw_rate_abs": impact_yaw_rate_abs,
        "impact_severity_proxy": impact_severity,
        "collision_mitigation_score": collision_mitigation_score,
        "max_off_track_overshoot": max_off_track_overshoot,
        "time_to_first_off_track_s": time_to_first_off_track,
        "off_track_severity_proxy": off_track_severity,
        "impact_speed_mps": impact_speed,
        "impact_speed_mps_available": bool(collision_available),
        "delta_v_at_impact_mps": float("nan"),
        "delta_v_at_impact_mps_available": False,
        "time_to_collision_s": time_to_collision,
        "time_to_collision_s_available": bool(collision_available),
        "collision_angle_or_side": "",
        "collision_angle_or_side_available": False,
        "collision_side_proxy": collision_side_proxy,
        "post_event_speed_mps": post_event_speed,
        "post_event_speed_mps_available": post_event_available,
        "post_event_yaw_rate_abs": post_event_yaw_rate_abs,
        "post_event_yaw_rate_abs_available": post_event_available,
        "post_event_offtrack_overshoot": post_event_offtrack_overshoot,
        "post_event_offtrack_overshoot_available": post_event_available,
        "recoverability_window_success": recoverability_success,
        "recoverability_window_success_available": recoverability_available,
    }


def _numeric_values(rows: Iterable[Mapping[str, Any]], key: str) -> list[float]:
    values = [_finite_float(row.get(key), default=float("nan")) for row in rows]
    return [value for value in values if np.isfinite(value)]


def _bool_rate(rows: list[Mapping[str, Any]], key: str) -> float:
    if not rows:
        return float("nan")
    return float(np.mean([_bool_value(row.get(key, False)) for row in rows]))


def _mean(rows: list[Mapping[str, Any]], key: str) -> float:
    values = _numeric_values(rows, key)
    return float(np.mean(values)) if values else float("nan")


def _collision_rate(rows: list[Mapping[str, Any]]) -> float:
    return _bool_rate(rows, "collision")


def _off_track_rate(rows: list[Mapping[str, Any]]) -> float:
    if not rows:
        return float("nan")
    return float(
        np.mean(
            [
                str(row.get("termination_reason", "") or "") == "off_track"
                or str(row.get("outcome_bucket", "") or "") == "off_track_noncollision_noncompletion"
                for row in rows
            ]
        )
    )


def outcome_metric_aggregate_fields(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "recovery_success_rate": _bool_rate(rows, "recovery_success"),
        "recovery_time_proxy_mean": _mean(rows, "recovery_time_proxy"),
        "controlled_drift_recovery_success_rate": _bool_rate(rows, "controlled_drift_recovery_success"),
        "drift_used_rate": _bool_rate(rows, "drift_used"),
        "impact_severity_proxy_mean": _mean(rows, "impact_severity_proxy"),
        "collision_mitigation_score_mean": _mean(rows, "collision_mitigation_score"),
        "max_off_track_overshoot_mean": _mean(rows, "max_off_track_overshoot"),
        "off_track_severity_proxy_mean": _mean(rows, "off_track_severity_proxy"),
    }


def hidden_dynamics_aggregate_rows(
    rows: list[dict[str, Any]],
    *,
    group_keys: tuple[str, ...] = ("profile_name", "hidden_dynamics_bucket"),
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not str(row.get("hidden_dynamics_bucket", "")).strip():
            continue
        groups[tuple(str(row.get(key, "")) for key in group_keys)].append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        item = {group_keys[index]: key[index] for index in range(len(group_keys))}
        item.update(
            {
                "episode_count": len(group),
                "success_rate": _bool_rate(group, "success"),
                "collision_rate": _collision_rate(group),
                "off_track_rate": _off_track_rate(group),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        item.update(outcome_metric_aggregate_fields(group))
        output.append(item)
    return output


def profile_hidden_dynamics_worst_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket_rows = hidden_dynamics_aggregate_rows(rows)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bucket_rows:
        groups[str(row.get("profile_name", ""))].append(row)

    output: list[dict[str, Any]] = []
    for profile_name in sorted(groups):
        group = groups[profile_name]
        success_rates = _numeric_values(group, "success_rate")
        recovery_rates = _numeric_values(group, "recovery_success_rate")
        controlled_rates = _numeric_values(group, "controlled_drift_recovery_success_rate")
        collision_rates = _numeric_values(group, "collision_rate")
        off_track_rates = _numeric_values(group, "off_track_rate")
        output.append(
            {
                "profile_name": profile_name,
                "hidden_dynamics_bucket_count": len(group),
                "worst_bucket_success_rate": min(success_rates) if success_rates else float("nan"),
                "max_bucket_success_rate": max(success_rates) if success_rates else float("nan"),
                "success_rate_bucket_spread": (max(success_rates) - min(success_rates)) if success_rates else float("nan"),
                "worst_bucket_recovery_success_rate": min(recovery_rates) if recovery_rates else float("nan"),
                "worst_bucket_controlled_drift_recovery_success_rate": (
                    min(controlled_rates) if controlled_rates else float("nan")
                ),
                "worst_bucket_collision_rate": max(collision_rates) if collision_rates else float("nan"),
                "worst_bucket_off_track_rate": max(off_track_rates) if off_track_rates else float("nan"),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
    return output
