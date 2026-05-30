"""No-rollout role-specific metric scorecard extraction."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_bounded_calibration_smoke_execution import aggregate_outcome_rows
from autodrift.controller_family_full_rollout_execution import read_csv_rows


DEFAULT_EPISODE_ROWS = Path("runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv")
DEFAULT_OUTPUT_DIR = Path("runs/m1783_role_specific_metric_scorecard_extraction")
DEFAULT_NEXT_BLOCKER = "m1784-paper-route-role-specific-metric-scorecard-result-audit"
TARGET_EPISODE_COUNT = 288
TARGET_ROLE_PANEL_COUNT = 4
TARGET_PROFILE_COUNT = 12
ROLE_IDS = (
    "stable_avoidance_aes",
    "drift_required_recovery",
    "hidden_dynamics_robustness",
    "unavoidable_mitigation",
)
FORBIDDEN_GUARDRAILS = (
    "environment_reset_started",
    "environment_rollout_started",
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


def _float(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _finite_values(rows: Iterable[Mapping[str, Any]], key: str) -> list[float]:
    values = [_float(row.get(key)) for row in rows]
    return [value for value in values if np.isfinite(value)]


def _mean(rows: list[Mapping[str, Any]], key: str) -> float:
    values = _finite_values(rows, key)
    return float(np.mean(values)) if values else float("nan")


def _rate(rows: list[Mapping[str, Any]], key: str) -> float:
    return float(np.mean([_bool(row.get(key, False)) for row in rows])) if rows else float("nan")


def metric_contract_rows() -> list[dict[str, Any]]:
    rows = [
        ("stable_avoidance_aes", "success_obstacle_pass_rate", "higher", True),
        ("stable_avoidance_aes", "collision_failure_rate", "lower", False),
        ("stable_avoidance_aes", "off_track_noncollision_noncompletion_rate", "lower", False),
        ("stable_avoidance_aes", "recovery_success_rate", "higher", True),
        ("stable_avoidance_aes", "clearance_margin_p10", "higher", True),
        ("drift_required_recovery", "controlled_drift_recovery_success_rate", "higher", True),
        ("drift_required_recovery", "drift_used_rate", "higher", True),
        ("drift_required_recovery", "recovery_success_rate", "higher", True),
        ("drift_required_recovery", "collision_failure_rate", "lower", False),
        ("drift_required_recovery", "off_track_noncollision_noncompletion_rate", "lower", False),
        ("hidden_dynamics_robustness", "worst_hidden_bucket_success_rate", "higher", True),
        ("hidden_dynamics_robustness", "worst_hidden_bucket_collision_rate", "lower", True),
        ("hidden_dynamics_robustness", "worst_hidden_bucket_off_track_rate", "lower", True),
        ("hidden_dynamics_robustness", "hidden_bucket_success_spread", "lower", False),
        ("unavoidable_mitigation", "impact_severity_proxy_mean", "lower", True),
        ("unavoidable_mitigation", "collision_mitigation_score_mean", "lower", True),
        ("unavoidable_mitigation", "impact_speed_proxy_mean", "lower", True),
        ("unavoidable_mitigation", "impact_beta_abs_mean", "lower", True),
        ("unavoidable_mitigation", "impact_yaw_rate_abs_mean", "lower", True),
        ("unavoidable_mitigation", "off_track_severity_proxy_mean", "lower", False),
    ]
    return [
        {
            "role_panel_id": role,
            "metric_name": metric,
            "direction": direction,
            "primary_metric": primary,
            "ranking_admissible_after_audit": False,
            "diagnostic_only_no_ranking_claim": True,
        }
        for role, metric, direction, primary in rows
    ]


def _group_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    return dict(sorted(groups.items()))


def _role_primary_metric_value(role: str, aggregate: Mapping[str, Any]) -> tuple[str, float, str]:
    if role == "stable_avoidance_aes":
        return "success_obstacle_pass_rate", _float(aggregate.get("success_obstacle_pass_rate")), "higher"
    if role == "drift_required_recovery":
        return (
            "controlled_drift_recovery_success_rate",
            _float(aggregate.get("controlled_drift_recovery_success_rate")),
            "higher",
        )
    if role == "hidden_dynamics_robustness":
        return "success_obstacle_pass_rate", _float(aggregate.get("success_obstacle_pass_rate")), "higher"
    if role == "unavoidable_mitigation":
        return "impact_severity_proxy_mean", _float(aggregate.get("impact_severity_proxy_mean")), "lower"
    return "success_obstacle_pass_rate", _float(aggregate.get("success_obstacle_pass_rate")), "higher"


def _extended_score_row(aggregate: Mapping[str, Any], group_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    role = str(aggregate.get("role_panel_id", ""))
    metric_name, metric_value, direction = _role_primary_metric_value(role, aggregate)
    return {
        **dict(aggregate),
        "impact_speed_proxy_mean": _mean(group_rows, "impact_speed_proxy"),
        "impact_beta_abs_mean": _mean(group_rows, "impact_beta_abs"),
        "impact_yaw_rate_abs_mean": _mean(group_rows, "impact_yaw_rate_abs"),
        "primary_role_metric": metric_name,
        "primary_role_metric_value": metric_value,
        "primary_role_metric_direction": direction,
        "ranking_admissible_after_audit": False,
        "diagnostic_only_no_ranking_claim": True,
    }


def scorecard_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    aggregates = aggregate_outcome_rows(rows, keys)
    groups = _group_rows(rows, keys)
    output: list[dict[str, Any]] = []
    for aggregate in aggregates:
        key = tuple(str(aggregate.get(item, "")) for item in keys)
        output.append(_extended_score_row(aggregate, groups.get(key, [])))
    return output


def _hidden_bucket_score_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_out = scorecard_rows(rows, ("profile_name", "role_panel_id", "hidden_dynamics_bucket"))
    for row in rows_out:
        row["hidden_bucket_scorecard"] = True
    return rows_out


def _admissibility_blockers(role: str, row: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    success = _float(row.get("success_obstacle_pass_rate"), 0.0)
    collision = _float(row.get("collision_failure_rate"), 0.0)
    off_track = _float(row.get("off_track_noncollision_noncompletion_rate"), 0.0)
    recovery = _float(row.get("recovery_success_rate"), 0.0)
    controlled = _float(row.get("controlled_drift_recovery_success_rate"), 0.0)
    drift_used = _float(row.get("drift_used_rate"), 0.0)
    if int(float(row.get("episode_count", 0))) <= 0:
        blockers.append("empty_role")
    if role == "stable_avoidance_aes":
        if collision > 0.05:
            blockers.append("stable_collision_rate_high")
        if off_track > 0.50:
            blockers.append("stable_off_track_dominance")
        if success < 0.50:
            blockers.append("stable_success_low")
    elif role == "drift_required_recovery":
        if controlled < 0.20:
            blockers.append("drift_controlled_recovery_low")
        if drift_used < 0.20:
            blockers.append("drift_used_low")
        if collision + off_track > 0.75:
            blockers.append("drift_non_success_dominance")
    elif role == "hidden_dynamics_robustness":
        if success < 0.30:
            blockers.append("hidden_success_low")
        if collision + off_track > 0.75:
            blockers.append("hidden_non_success_dominance")
    elif role == "unavoidable_mitigation":
        if off_track > 0.10:
            blockers.append("mitigation_off_track_interference")
        if not np.isfinite(_float(row.get("impact_severity_proxy_mean"))):
            blockers.append("mitigation_impact_metric_missing")
    return blockers


def role_admissibility_rows(role_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    admissibility: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for row in role_rows:
        role = str(row.get("role_panel_id", ""))
        role_blockers = _admissibility_blockers(role, row)
        admissibility.append(
            {
                "role_panel_id": role,
                "episode_count": row.get("episode_count", 0),
                "ranking_admissible_after_audit": False,
                "blocker_count": len(role_blockers),
                "blockers": ";".join(role_blockers),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        for blocker in role_blockers or ["ranking_blocked_pending_audit"]:
            blockers.append(
                {
                    "role_panel_id": role,
                    "blocker": blocker,
                    "ranking_admissible_after_audit": False,
                    "diagnostic_only_no_ranking_claim": True,
                }
            )
    return admissibility, blockers


def run_role_specific_metric_scorecard_extraction(
    *,
    episode_rows_path: Path | str = DEFAULT_EPISODE_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_episode_count: int = TARGET_EPISODE_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [dict(row) for row in read_csv_rows(episode_rows_path)]

    profile_role = scorecard_rows(rows, ("profile_name", "role_panel_id"))
    role_panel = scorecard_rows(rows, ("role_panel_id",))
    profile_role_hidden = _hidden_bucket_score_rows(rows)
    profile_role_label = scorecard_rows(rows, ("profile_name", "role_panel_id", "sampled_obstacle_label"))
    contract = metric_contract_rows()
    role_admissibility, ranking_blockers = role_admissibility_rows(role_panel)

    write_csv_rows(output / "profile_role_scorecard.csv", profile_role)
    write_csv_rows(output / "role_panel_scorecard.csv", role_panel)
    write_csv_rows(output / "profile_role_hidden_bucket_scorecard.csv", profile_role_hidden)
    write_csv_rows(output / "profile_role_sampled_label_scorecard.csv", profile_role_label)
    write_csv_rows(output / "role_admissibility.csv", role_admissibility)
    write_csv_rows(output / "ranking_blockers.csv", ranking_blockers)
    write_csv_rows(output / "metric_contract.csv", contract)

    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    role_ids_present = {str(row.get("role_panel_id", "")) for row in role_panel}
    profile_count = len({str(row.get("profile_name", "")) for row in rows})
    mitigation_contract_uses_success = any(
        row["role_panel_id"] == "unavoidable_mitigation"
        and row["metric_name"] == "success_obstacle_pass_rate"
        and bool(row["primary_metric"])
        for row in contract
    )
    result_passes = (
        len(rows) == target_episode_count
        and role_ids_present == set(ROLE_IDS)
        and profile_count == TARGET_PROFILE_COUNT
        and len(role_panel) == TARGET_ROLE_PANEL_COUNT
        and bool(profile_role)
        and bool(role_admissibility)
        and bool(ranking_blockers)
        and not mitigation_contract_uses_success
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "role_specific_metric_scorecard_extraction_pass"
            if result_passes
            else "role_specific_metric_scorecard_extraction_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "episode_rows_path": str(episode_rows_path),
        "episode_count": len(rows),
        "target_episode_count": target_episode_count,
        "profile_count": profile_count,
        "target_profile_count": TARGET_PROFILE_COUNT,
        "role_panel_count": len(role_ids_present),
        "target_role_panel_count": TARGET_ROLE_PANEL_COUNT,
        "profile_role_scorecard_rows": len(profile_role),
        "role_panel_scorecard_rows": len(role_panel),
        "profile_role_hidden_bucket_scorecard_rows": len(profile_role_hidden),
        "profile_role_sampled_label_scorecard_rows": len(profile_role_label),
        "role_admissibility_rows": len(role_admissibility),
        "ranking_blocker_rows": len(ranking_blockers),
        "metric_contract_rows": len(contract),
        "mitigation_contract_uses_success_as_primary": mitigation_contract_uses_success,
        "ranking_admissible_after_audit": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
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
            "profile_role_scorecard": str(output / "profile_role_scorecard.csv"),
            "role_panel_scorecard": str(output / "role_panel_scorecard.csv"),
            "profile_role_hidden_bucket_scorecard": str(output / "profile_role_hidden_bucket_scorecard.csv"),
            "profile_role_sampled_label_scorecard": str(output / "profile_role_sampled_label_scorecard.csv"),
            "role_admissibility": str(output / "role_admissibility.csv"),
            "ranking_blockers": str(output / "ranking_blockers.csv"),
            "metric_contract": str(output / "metric_contract.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract role-specific metric scorecards without rollout.")
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-episode-count", type=int, default=TARGET_EPISODE_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    summary = run_role_specific_metric_scorecard_extraction(
        episode_rows_path=args.episode_rows,
        output_dir=args.output_dir,
        target_episode_count=int(args.target_episode_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"episode_count={summary['episode_count']}")
    print(f"profile_role_scorecard_rows={summary['profile_role_scorecard_rows']}")
    print(f"ranking_blocker_rows={summary['ranking_blocker_rows']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
