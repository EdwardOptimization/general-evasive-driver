"""Artifact-only R4 mitigation metric semantics audit."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import write_csv_rows, write_json


DEFAULT_INPUT_DIR = Path("runs/m2330_paper_route_current_sim_r4_metric_instrumented_support_diagnostic_rerun")
DEFAULT_OUTPUT_DIR = Path("runs/m2333_paper_route_current_sim_r4_mitigation_metric_semantics")
DEFAULT_TARGET_SCENARIO_COUNT = 12
DEFAULT_NEXT_BLOCKER = "m2334-paper-route-current-sim-r4-mitigation-metric-semantics-result-audit"
R4_ROLE_FAMILY = "R4_unavoidable_mitigation"
AVAILABLE_IMPACT_PROXY_FIELDS = (
    "impact_speed_mps",
    "impact_speed_mps_available",
    "time_to_collision_s",
    "time_to_collision_s_available",
    "collision_side_proxy",
    "impact_speed_proxy",
    "impact_beta_abs",
    "impact_yaw_rate_abs",
    "impact_severity_proxy",
    "collision_mitigation_score",
)
POST_COLLISION_AVAILABILITY_FIELDS = (
    "delta_v_at_impact_mps_available",
    "post_event_speed_mps_available",
    "post_event_yaw_rate_abs_available",
    "post_event_offtrack_overshoot_available",
    "recoverability_window_success_available",
)
SCENARIO_FIELDNAMES = [
    "scenario_spec_id",
    "role_family",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "impact_proxy_available_count",
    "impact_proxy_available_fraction",
    "post_collision_available_count",
    "support_label",
    "obstacle_passage_success_semantics",
    "impact_proxy_semantics",
    "post_collision_semantics",
    "r4_metric_semantics_status",
    "comparison_admissibility",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
POLICY_AGGREGATE_FIELDNAMES = [
    "support_policy_name",
    "episode_count",
    "success_count",
    "collision_count",
    "offtrack_count",
    "impact_proxy_available_count",
    "impact_speed_mps_mean",
    "collision_mitigation_score_mean",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
]
CLAIM_FIELDNAMES = [
    "claim",
    "allowed",
    "made",
    "reason",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y"}


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _mean(values: Sequence[float | None]) -> float:
    finite = [float(value) for value in values if value is not None and np.isfinite(value)]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool_value(row.get("success", False))


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool_value(row.get("collision", False)) or str(row.get("termination_reason", "")) == "obstacle_collision"


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track"


def _impact_proxy_available(row: Mapping[str, Any]) -> bool:
    return _bool_value(row.get("impact_speed_mps_available", False)) or _finite_float(row.get("impact_speed_mps")) is not None


def _post_collision_available(row: Mapping[str, Any]) -> bool:
    return any(_bool_value(row.get(field, False)) for field in POST_COLLISION_AVAILABILITY_FIELDS)


def _scenario_label_map(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for row in rows:
        scenario_id = str(row.get("scenario_spec_id", ""))
        if scenario_id:
            output[scenario_id] = str(row.get("support_label", ""))
    return output


def build_scenario_semantics_rows(
    episode_rows: Sequence[Mapping[str, Any]],
    scenario_label_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    labels = _scenario_label_map(scenario_label_rows)
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        if str(row.get("role_family", "")) == R4_ROLE_FAMILY:
            grouped[str(row.get("scenario_spec_id", ""))].append(row)

    output: list[dict[str, Any]] = []
    for scenario_id in sorted(grouped):
        rows = grouped[scenario_id]
        impact_available_count = sum(_impact_proxy_available(row) for row in rows)
        post_available_count = sum(_post_collision_available(row) for row in rows)
        impact_semantics = "available" if impact_available_count > 0 else "unavailable"
        post_semantics = (
            "available"
            if post_available_count > 0
            else "blocked_current_sim_collision_terminates"
        )
        if impact_semantics == "available" and post_semantics.startswith("blocked"):
            status = "proxy_metric_available_post_collision_blocked"
            comparison = "descriptive_proxy_audit_only"
        elif impact_semantics == "available":
            status = "post_collision_metric_available"
            comparison = "blocked_until_semantics_audited"
        else:
            status = "proxy_metric_unavailable"
            comparison = "blocked_until_semantics_audited"
        episode_count = len(rows)
        output.append(
            {
                "scenario_spec_id": scenario_id,
                "role_family": R4_ROLE_FAMILY,
                "episode_count": episode_count,
                "success_count": sum(_is_success(row) for row in rows),
                "collision_count": sum(_is_collision(row) for row in rows),
                "offtrack_count": sum(_is_offtrack(row) for row in rows),
                "impact_proxy_available_count": impact_available_count,
                "impact_proxy_available_fraction": (
                    impact_available_count / episode_count if episode_count else float("nan")
                ),
                "post_collision_available_count": post_available_count,
                "support_label": labels.get(scenario_id, ""),
                "obstacle_passage_success_semantics": "insufficient_for_r4",
                "impact_proxy_semantics": impact_semantics,
                "post_collision_semantics": post_semantics,
                "r4_metric_semantics_status": status,
                "comparison_admissibility": comparison,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
    return output


def build_policy_aggregate_rows(episode_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        if str(row.get("role_family", "")) == R4_ROLE_FAMILY:
            grouped[str(row.get("support_policy_name", ""))].append(row)

    output: list[dict[str, Any]] = []
    for policy_name in sorted(grouped):
        rows = grouped[policy_name]
        output.append(
            {
                "support_policy_name": policy_name,
                "episode_count": len(rows),
                "success_count": sum(_is_success(row) for row in rows),
                "collision_count": sum(_is_collision(row) for row in rows),
                "offtrack_count": sum(_is_offtrack(row) for row in rows),
                "impact_proxy_available_count": sum(_impact_proxy_available(row) for row in rows),
                "impact_speed_mps_mean": _mean([_finite_float(row.get("impact_speed_mps")) for row in rows]),
                "collision_mitigation_score_mean": _mean(
                    [_finite_float(row.get("collision_mitigation_score")) for row in rows]
                ),
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "level3_self_id_claim_made": False,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_r4_metric_semantics",
            "allowed": True,
            "made": True,
            "reason": "M2333 only materializes R4 semantics rows from existing artifacts.",
        },
        {
            "claim": "support_policy_ranking",
            "allowed": False,
            "made": False,
            "reason": "Per-policy aggregates are descriptive and non-ranking.",
        },
        {
            "claim": "paper_level_mitigation_performance",
            "allowed": False,
            "made": False,
            "reason": "Current-sim proxy metrics are not paper-level mitigation-performance evidence.",
        },
        {
            "claim": "post_collision_recovery_measured",
            "allowed": False,
            "made": False,
            "reason": "Collision-terminating rollouts do not expose post-collision recovery fields.",
        },
        {
            "claim": "level3_self_identification",
            "allowed": False,
            "made": False,
            "reason": "No history intervention or self-ID test is run.",
        },
    ]


def run_r4_mitigation_metric_semantics_audit(
    *,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_scenario_count: int = DEFAULT_TARGET_SCENARIO_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episode_rows = read_csv_rows(source / "episode_rows.csv")
    scenario_label_rows = read_csv_rows(source / "scenario_support_labels.csv")
    semantics_rows = build_scenario_semantics_rows(episode_rows, scenario_label_rows)
    policy_rows = build_policy_aggregate_rows(episode_rows)
    claims = claim_boundary_rows()

    write_csv_rows(output / "r4_metric_semantics_rows.csv", semantics_rows, fieldnames=SCENARIO_FIELDNAMES)
    write_csv_rows(output / "r4_metric_proxy_policy_aggregate.csv", policy_rows, fieldnames=POLICY_AGGREGATE_FIELDNAMES)
    write_csv_rows(output / "r4_claim_boundary.csv", claims, fieldnames=CLAIM_FIELDNAMES)

    scenario_count = len(semantics_rows)
    impact_proxy_available_scenario_count = sum(
        row["impact_proxy_semantics"] == "available" for row in semantics_rows
    )
    post_collision_blocked_scenario_count = sum(
        str(row["post_collision_semantics"]).startswith("blocked") for row in semantics_rows
    )
    obstacle_passage_success_insufficient_count = sum(
        row["obstacle_passage_success_semantics"] == "insufficient_for_r4" for row in semantics_rows
    )
    ranking_admissible_count = sum(_bool_value(row.get("ranking_admissible", False)) for row in semantics_rows + policy_rows)
    winner_selected_count = sum(_bool_value(row.get("winner_selected", False)) for row in semantics_rows + policy_rows)
    paper_level_claim_count = sum(_bool_value(row.get("paper_level_claim_made", False)) for row in semantics_rows + policy_rows)
    level3_self_id_claim_count = sum(_bool_value(row.get("level3_self_id_claim_made", False)) for row in semantics_rows + policy_rows)
    guardrail_violation_count = (
        ranking_admissible_count
        + winner_selected_count
        + paper_level_claim_count
        + level3_self_id_claim_count
    )
    result_passes = (
        scenario_count == int(target_scenario_count)
        and impact_proxy_available_scenario_count == int(target_scenario_count)
        and guardrail_violation_count == 0
    )
    summary = {
        "result_class": (
            "current_sim_r4_mitigation_metric_semantics_audit_pass"
            if result_passes
            else "current_sim_r4_mitigation_metric_semantics_audit_incomplete_or_fail"
        ),
        "input_dir": str(source),
        "output_dir": str(output),
        "scenario_count": scenario_count,
        "target_scenario_count": int(target_scenario_count),
        "episode_count": len(episode_rows),
        "policy_aggregate_count": len(policy_rows),
        "impact_proxy_available_scenario_count": impact_proxy_available_scenario_count,
        "post_collision_blocked_scenario_count": post_collision_blocked_scenario_count,
        "obstacle_passage_success_insufficient_count": obstacle_passage_success_insufficient_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "paper_level_claim_count": paper_level_claim_count,
        "level3_self_id_claim_count": level3_self_id_claim_count,
        "guardrail_violation_count": guardrail_violation_count,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "support_policy_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "r4_metric_semantics_rows": str(output / "r4_metric_semantics_rows.csv"),
            "r4_metric_proxy_policy_aggregate": str(output / "r4_metric_proxy_policy_aggregate.csv"),
            "r4_claim_boundary": str(output / "r4_claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-scenario-count", type=int, default=DEFAULT_TARGET_SCENARIO_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_r4_mitigation_metric_semantics_audit(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        target_scenario_count=int(args.target_scenario_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"scenario_count={summary['scenario_count']}")
    print(f"impact_proxy_available_scenario_count={summary['impact_proxy_available_scenario_count']}")
    print(f"post_collision_blocked_scenario_count={summary['post_collision_blocked_scenario_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
