"""Materialize the hard/soft offtrack metric split panel."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_M2362_DIR = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution")
DEFAULT_M2397_DIR = Path("runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation")
DEFAULT_M2413_DIR = Path("runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation")
DEFAULT_OUTPUT_DIR = Path("runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split")
DEFAULT_NEXT_BLOCKER = "m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit"

RESULT_PASS = "current_sim_dual_axis_hard_soft_offtrack_metric_split_pass"
RESULT_FAIL = "current_sim_dual_axis_hard_soft_offtrack_metric_split_incomplete_or_fail"
ROUTE_RECOMMENDATION = "route_to_hard_soft_offtrack_metric_split_result_audit"
THRESHOLDS_M = (0.02, 0.05, 0.10, 0.20)

PANEL_FIELDNAMES = [
    "panel_id",
    "source_milestone",
    "threshold_m",
    "episode_rows_path",
    "episode_count",
    "actual_success_original_count",
    "actual_success_preserved_count",
    "actual_success_preserved_rate",
    "actual_success_preservation_violation_count",
    "collision_or_obstacle_risk_failure_count",
    "collision_or_obstacle_risk_failure_rate",
    "hard_offtrack_failure_count",
    "hard_offtrack_failure_rate",
    "soft_offtrack_violation_count",
    "soft_offtrack_violation_rate",
    "boundary_tolerated_diagnostic_count",
    "boundary_tolerated_diagnostic_rate",
    "counterfactual_soft_success_count",
    "counterfactual_soft_success_rate",
    "counterfactual_soft_success_gain",
    "other_failure_count",
    "other_failure_rate",
    "mean_soft_offtrack_clearance_margin",
    "mean_soft_offtrack_overshoot_m",
    "mean_hard_offtrack_overshoot_m",
    "diagnostic_only",
    "actual_success_claim",
    "ranking_admissible",
    "winner_selected",
]

DECISION_FIELDNAMES = ["decision_key", "decision_value", "admissible", "reason"]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n", ""}:
        return False
    return default


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _rate(count: int, total: int) -> float:
    return float(count / total) if total else 0.0


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track" or str(row.get("outcome_bucket", "")).startswith(
        "off_track"
    )


def _is_collision(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("collision")) or str(row.get("termination_reason", "")) == "obstacle_collision"


def _is_success(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("success")) or _bool(row.get("role_success"))


def _is_obstacle_risk_failure(row: Mapping[str, Any]) -> bool:
    clearance = _float(row.get("min_clearance_margin"))
    return _is_collision(row) or (clearance is not None and clearance <= 0.0)


def classify_episode(row: Mapping[str, Any], *, threshold_m: float) -> dict[str, bool]:
    actual_success = _is_success(row)
    risk_failure = False if actual_success else _is_obstacle_risk_failure(row)
    offtrack = _is_offtrack(row)
    overshoot = _float(row.get("max_off_track_overshoot"))
    soft_offtrack = (
        not actual_success
        and not risk_failure
        and offtrack
        and overshoot is not None
        and 0.0 <= overshoot <= threshold_m
    )
    hard_offtrack = (
        not actual_success
        and not risk_failure
        and offtrack
        and overshoot is not None
        and overshoot > threshold_m
    )
    boundary_tolerated = soft_offtrack
    return {
        "actual_success_preserved": actual_success,
        "collision_or_obstacle_risk_failure": risk_failure,
        "hard_offtrack_failure": hard_offtrack,
        "soft_offtrack_violation": soft_offtrack,
        "boundary_tolerated_diagnostic": boundary_tolerated,
        "counterfactual_soft_success": actual_success or boundary_tolerated,
    }


def _panel_row(
    *,
    panel_id: str,
    source_milestone: str,
    threshold_m: float,
    episode_rows_path: Path,
) -> dict[str, Any]:
    rows = read_csv_rows(episode_rows_path)
    episode_count = len(rows)
    classes = [classify_episode(row, threshold_m=threshold_m) for row in rows]
    actual_success_original_count = sum(_is_success(row) for row in rows)
    actual_success_preserved_count = sum(item["actual_success_preserved"] for item in classes)
    preservation_violation_count = sum(
        item["actual_success_preserved"] != _is_success(row) for item, row in zip(classes, rows, strict=True)
    )
    risk_count = sum(item["collision_or_obstacle_risk_failure"] for item in classes)
    hard_count = sum(item["hard_offtrack_failure"] for item in classes)
    soft_count = sum(item["soft_offtrack_violation"] for item in classes)
    boundary_count = sum(item["boundary_tolerated_diagnostic"] for item in classes)
    soft_success_count = sum(item["counterfactual_soft_success"] for item in classes)
    assigned_count = actual_success_preserved_count + risk_count + hard_count + soft_count
    other_failure_count = max(0, episode_count - assigned_count)
    soft_rows = [row for row, item in zip(rows, classes, strict=True) if item["soft_offtrack_violation"]]
    hard_rows = [row for row, item in zip(rows, classes, strict=True) if item["hard_offtrack_failure"]]
    soft_clearance = [
        value for value in (_float(row.get("min_clearance_margin")) for row in soft_rows) if value is not None
    ]
    soft_overshoot = [
        value for value in (_float(row.get("max_off_track_overshoot")) for row in soft_rows) if value is not None
    ]
    hard_overshoot = [
        value for value in (_float(row.get("max_off_track_overshoot")) for row in hard_rows) if value is not None
    ]
    actual_success_rate = _rate(actual_success_preserved_count, episode_count)
    soft_success_rate = _rate(soft_success_count, episode_count)
    return {
        "panel_id": panel_id,
        "source_milestone": source_milestone,
        "threshold_m": threshold_m,
        "episode_rows_path": str(episode_rows_path),
        "episode_count": episode_count,
        "actual_success_original_count": actual_success_original_count,
        "actual_success_preserved_count": actual_success_preserved_count,
        "actual_success_preserved_rate": actual_success_rate,
        "actual_success_preservation_violation_count": preservation_violation_count,
        "collision_or_obstacle_risk_failure_count": risk_count,
        "collision_or_obstacle_risk_failure_rate": _rate(risk_count, episode_count),
        "hard_offtrack_failure_count": hard_count,
        "hard_offtrack_failure_rate": _rate(hard_count, episode_count),
        "soft_offtrack_violation_count": soft_count,
        "soft_offtrack_violation_rate": _rate(soft_count, episode_count),
        "boundary_tolerated_diagnostic_count": boundary_count,
        "boundary_tolerated_diagnostic_rate": _rate(boundary_count, episode_count),
        "counterfactual_soft_success_count": soft_success_count,
        "counterfactual_soft_success_rate": soft_success_rate,
        "counterfactual_soft_success_gain": soft_success_rate - actual_success_rate,
        "other_failure_count": other_failure_count,
        "other_failure_rate": _rate(other_failure_count, episode_count),
        "mean_soft_offtrack_clearance_margin": _mean(soft_clearance),
        "mean_soft_offtrack_overshoot_m": _mean(soft_overshoot),
        "mean_hard_offtrack_overshoot_m": _mean(hard_overshoot),
        "diagnostic_only": True,
        "actual_success_claim": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "new_measured_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2438 reuses existing primary episode rows only.",
        },
        {
            "decision_key": "actual_success_preserved",
            "decision_value": "true",
            "admissible": True,
            "reason": "Measured actual_success is copied into actual_success_preserved and never overwritten.",
        },
        {
            "decision_key": "counterfactual_soft_success_is_actual_success",
            "decision_value": "false",
            "admissible": True,
            "reason": "Counterfactual soft success is diagnostic-only and cannot promote measured success.",
        },
        {
            "decision_key": "scenario_redesign_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2438 materializes metric classes but does not alter scenarios or termination.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "Metric split implementation requires result audit and later measured validation before any verdict.",
        },
        {
            "decision_key": "next_route",
            "decision_value": ROUTE_RECOMMENDATION,
            "admissible": True,
            "reason": "Audit the metric-split panel before any measured rollout, repair, training, or controller comparison.",
        },
    ]


def run_hard_soft_offtrack_metric_split_panel(
    *,
    m2362_dir: Path | str = DEFAULT_M2362_DIR,
    m2397_dir: Path | str = DEFAULT_M2397_DIR,
    m2413_dir: Path | str = DEFAULT_M2413_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
    thresholds_m: Sequence[float] = THRESHOLDS_M,
) -> dict[str, Any]:
    m2362 = Path(m2362_dir)
    m2397 = Path(m2397_dir)
    m2413 = Path(m2413_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_specs = [
        ("m2362", m2362 / "episode_rows.csv", m2362 / "summary.json"),
        ("m2397", m2397 / "episode_rows.csv", m2397 / "summary.json"),
        ("m2413", m2413 / "episode_rows.csv", m2413 / "summary.json"),
    ]
    source_result_classes = {
        source: read_json(summary_path).get("result_class", "") if summary_path.exists() else ""
        for source, _, summary_path in source_specs
    }
    panel_rows: list[dict[str, Any]] = []
    for source, episode_path, _ in source_specs:
        for threshold_m in thresholds_m:
            panel_rows.append(
                _panel_row(
                    panel_id=f"{source}_hard_soft_{threshold_m:.2f}m",
                    source_milestone=source,
                    threshold_m=float(threshold_m),
                    episode_rows_path=episode_path,
                )
            )

    source_values = sorted({str(row["source_milestone"]) for row in panel_rows})
    threshold_values = sorted({float(row["threshold_m"]) for row in panel_rows})
    required_thresholds = tuple(float(value) for value in THRESHOLDS_M)
    all_required_thresholds_present = all(value in threshold_values for value in required_thresholds)
    source_episode_counts = {
        str(row["source_milestone"]): int(row["episode_count"])
        for row in panel_rows
        if abs(float(row["threshold_m"]) - required_thresholds[0]) < 1e-9
    }
    min_episode_count = min(source_episode_counts.values(), default=0)
    preservation_violation_count = sum(int(row["actual_success_preservation_violation_count"]) for row in panel_rows)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in panel_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in panel_rows)
    actual_success_claim_count = sum(_bool(row.get("actual_success_claim")) for row in panel_rows)
    threshold_020_rows = [row for row in panel_rows if abs(float(row["threshold_m"]) - 0.20) < 1e-9]
    min_counterfactual_soft_success_rate_at_020 = min(
        (float(row["counterfactual_soft_success_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    max_counterfactual_soft_success_rate_at_020 = max(
        (float(row["counterfactual_soft_success_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    min_soft_success_gain_at_020 = min(
        (float(row["counterfactual_soft_success_gain"]) for row in threshold_020_rows),
        default=0.0,
    )
    max_actual_success_rate = max((float(row["actual_success_preserved_rate"]) for row in panel_rows), default=0.0)
    max_hard_offtrack_rate_at_020 = max(
        (float(row["hard_offtrack_failure_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    min_soft_offtrack_rate_at_020 = min(
        (float(row["soft_offtrack_violation_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    guardrail_flags = {
        "new_measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "actual_success_improvement_claim_made": bool(actual_success_claim_count),
        "actual_success_preservation_violation": bool(preservation_violation_count),
        "counterfactual_soft_success_reported_as_actual_success": False,
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": bool(winner_selected_count),
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = []
    if len(source_values) != 3 or not all_required_thresholds_present or min_episode_count <= 0:
        failure_types_observed.append("scenario_sampling_failure")
    if preservation_violation_count or ranking_admissible_count or winner_selected_count or actual_success_claim_count:
        failure_types_observed.append("contract_violation")
    if min_soft_offtrack_rate_at_020 <= 0.0 or max_hard_offtrack_rate_at_020 <= 0.0:
        failure_types_observed.append("metric_artifact")

    passes = (
        len(source_values) == 3
        and all_required_thresholds_present
        and len(panel_rows) == len(source_values) * len(required_thresholds)
        and min_episode_count > 0
        and preservation_violation_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and actual_success_claim_count == 0
        and guardrail_violation_count == 0
        and min_soft_offtrack_rate_at_020 > 0.0
        and max_hard_offtrack_rate_at_020 > 0.0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL
    decision_rows = _decision_rows()
    artifacts = {
        "summary": str(output / "summary.json"),
        "panel_rows": str(output / "panel_rows.csv"),
        "decision_rows": str(output / "decision_rows.csv"),
    }
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_artifacts": {
            "m2362_episode_rows": str(m2362 / "episode_rows.csv"),
            "m2397_episode_rows": str(m2397 / "episode_rows.csv"),
            "m2413_episode_rows": str(m2413 / "episode_rows.csv"),
        },
        "source_result_classes": source_result_classes,
        "panel_row_count": len(panel_rows),
        "source_count": len(source_values),
        "source_episode_counts": source_episode_counts,
        "threshold_count": len(threshold_values),
        "thresholds_m": threshold_values,
        "all_required_thresholds_present": all_required_thresholds_present,
        "actual_success_preserved": preservation_violation_count == 0,
        "actual_success_preservation_violation_count": preservation_violation_count,
        "min_soft_success_gain_at_0_20m": min_soft_success_gain_at_020,
        "min_counterfactual_soft_success_rate_at_0_20m": min_counterfactual_soft_success_rate_at_020,
        "max_counterfactual_soft_success_rate_at_0_20m": max_counterfactual_soft_success_rate_at_020,
        "max_actual_success_rate": max_actual_success_rate,
        "max_hard_offtrack_failure_rate_at_0_20m": max_hard_offtrack_rate_at_020,
        "min_soft_offtrack_violation_rate_at_0_20m": min_soft_offtrack_rate_at_020,
        "diagnostic_only": True,
        "counterfactual_metric_analysis_only": True,
        "new_measured_rollout_started": False,
        "actual_success_improvement_claim_made": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "failure_types_observed": failure_types_observed,
        "route_recommendation": ROUTE_RECOMMENDATION,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_csv_rows(output / "panel_rows.csv", panel_rows, fieldnames=PANEL_FIELDNAMES)
    write_csv_rows(output / "decision_rows.csv", decision_rows, fieldnames=DECISION_FIELDNAMES)
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2362-dir", type=Path, default=DEFAULT_M2362_DIR)
    parser.add_argument("--m2397-dir", type=Path, default=DEFAULT_M2397_DIR)
    parser.add_argument("--m2413-dir", type=Path, default=DEFAULT_M2413_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_hard_soft_offtrack_metric_split_panel(
        m2362_dir=args.m2362_dir,
        m2397_dir=args.m2397_dir,
        m2413_dir=args.m2413_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_row_count={summary['panel_row_count']}")
    print(f"thresholds_m={summary['thresholds_m']}")
    print(f"actual_success_preserved={summary['actual_success_preserved']}")
    print(f"min_soft_success_gain_at_0_20m={summary['min_soft_success_gain_at_0_20m']}")
    print(f"max_hard_offtrack_failure_rate_at_0_20m={summary['max_hard_offtrack_failure_rate_at_0_20m']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
