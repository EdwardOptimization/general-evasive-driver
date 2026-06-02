"""Build a counterfactual boundary-threshold sensitivity panel."""

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
DEFAULT_OUTPUT_DIR = Path("runs/m2435_paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel")
DEFAULT_NEXT_BLOCKER = "m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit"

RESULT_PASS = "current_sim_dual_axis_boundary_threshold_sensitivity_panel_pass"
RESULT_FAIL = "current_sim_dual_axis_boundary_threshold_sensitivity_panel_incomplete_or_fail"
ROUTE_RECOMMENDATION = "route_to_boundary_threshold_sensitivity_result_audit"
THRESHOLDS_M = (0.02, 0.05, 0.10, 0.20)
HIGH_SENSITIVITY_GAIN_THRESHOLD = 0.50

PANEL_FIELDNAMES = [
    "panel_id",
    "source_milestone",
    "threshold_m",
    "episode_rows_path",
    "episode_count",
    "actual_success_count",
    "actual_success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "boundary_tolerated_count",
    "boundary_tolerated_rate_of_all",
    "boundary_tolerated_rate_of_offtrack",
    "counterfactual_soft_success_count",
    "counterfactual_soft_success_rate",
    "counterfactual_soft_success_gain",
    "remaining_failure_count",
    "remaining_failure_rate",
    "mean_boundary_tolerated_clearance_margin",
    "mean_boundary_tolerated_overshoot",
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


def _is_boundary_tolerated(row: Mapping[str, Any], *, threshold_m: float) -> bool:
    if not _is_offtrack(row) or _is_collision(row) or _is_success(row):
        return False
    clearance = _float(row.get("min_clearance_margin"))
    overshoot = _float(row.get("max_off_track_overshoot"))
    if clearance is None or overshoot is None:
        return False
    return clearance > 0.0 and 0.0 <= overshoot <= threshold_m


def _panel_row(
    *,
    panel_id: str,
    source_milestone: str,
    threshold_m: float,
    episode_rows_path: Path,
) -> dict[str, Any]:
    rows = read_csv_rows(episode_rows_path)
    episode_count = len(rows)
    success_count = sum(_is_success(row) for row in rows)
    collision_count = sum(_is_collision(row) for row in rows)
    offtrack_count = sum(_is_offtrack(row) for row in rows)
    tolerated_rows = [row for row in rows if _is_boundary_tolerated(row, threshold_m=threshold_m)]
    boundary_tolerated_count = len(tolerated_rows)
    soft_success_count = success_count + boundary_tolerated_count
    remaining_failure_count = max(0, episode_count - soft_success_count - collision_count)
    tolerated_clearance = [
        value for value in (_float(row.get("min_clearance_margin")) for row in tolerated_rows) if value is not None
    ]
    tolerated_overshoot = [
        value for value in (_float(row.get("max_off_track_overshoot")) for row in tolerated_rows) if value is not None
    ]
    soft_success_rate = _rate(soft_success_count, episode_count)
    actual_success_rate = _rate(success_count, episode_count)
    return {
        "panel_id": panel_id,
        "source_milestone": source_milestone,
        "threshold_m": threshold_m,
        "episode_rows_path": str(episode_rows_path),
        "episode_count": episode_count,
        "actual_success_count": success_count,
        "actual_success_rate": actual_success_rate,
        "collision_count": collision_count,
        "collision_rate": _rate(collision_count, episode_count),
        "offtrack_count": offtrack_count,
        "offtrack_rate": _rate(offtrack_count, episode_count),
        "boundary_tolerated_count": boundary_tolerated_count,
        "boundary_tolerated_rate_of_all": _rate(boundary_tolerated_count, episode_count),
        "boundary_tolerated_rate_of_offtrack": _rate(boundary_tolerated_count, offtrack_count),
        "counterfactual_soft_success_count": soft_success_count,
        "counterfactual_soft_success_rate": soft_success_rate,
        "counterfactual_soft_success_gain": soft_success_rate - actual_success_rate,
        "remaining_failure_count": remaining_failure_count,
        "remaining_failure_rate": _rate(remaining_failure_count, episode_count),
        "mean_boundary_tolerated_clearance_margin": _mean(tolerated_clearance),
        "mean_boundary_tolerated_overshoot": _mean(tolerated_overshoot),
        "diagnostic_only": True,
        "actual_success_claim": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _decision_rows(*, high_sensitivity_detected: bool) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "new_measured_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2435 reuses existing primary episode rows only.",
        },
        {
            "decision_key": "actual_success_improvement_claim",
            "decision_value": "false",
            "admissible": True,
            "reason": "Soft success is counterfactual metric sensitivity, not an executed rollout result.",
        },
        {
            "decision_key": "high_boundary_threshold_sensitivity",
            "decision_value": str(high_sensitivity_detected).lower(),
            "admissible": high_sensitivity_detected,
            "reason": "Sensitivity is high when every source gains at least 0.50 soft-success rate at the 0.20 m threshold.",
        },
        {
            "decision_key": "scenario_redesign_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2435 diagnoses threshold sensitivity but does not alter scenario definitions.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "Counterfactual threshold sensitivity is diagnostic; verdict requires a follow-up audit and selected task-change evidence.",
        },
        {
            "decision_key": "next_route",
            "decision_value": ROUTE_RECOMMENDATION,
            "admissible": True,
            "reason": "Audit threshold sensitivity before task-boundary redesign, more repair, training, or controller-family comparison.",
        },
    ]


def run_boundary_threshold_sensitivity_panel(
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
    source_result_classes = {source: read_json(summary_path).get("result_class", "") for source, _, summary_path in source_specs}
    panel_rows: list[dict[str, Any]] = []
    for source, episode_path, _ in source_specs:
        for threshold_m in thresholds_m:
            panel_rows.append(
                _panel_row(
                    panel_id=f"{source}_threshold_{threshold_m:.2f}m",
                    source_milestone=source,
                    threshold_m=float(threshold_m),
                    episode_rows_path=episode_path,
                )
            )

    threshold_values = sorted({float(row["threshold_m"]) for row in panel_rows})
    source_values = sorted({str(row["source_milestone"]) for row in panel_rows})
    threshold_020_rows = [row for row in panel_rows if abs(float(row["threshold_m"]) - 0.20) < 1e-9]
    min_soft_success_gain_at_020 = min(
        (float(row["counterfactual_soft_success_gain"]) for row in threshold_020_rows),
        default=0.0,
    )
    min_soft_success_rate_at_020 = min(
        (float(row["counterfactual_soft_success_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    max_soft_success_rate_at_020 = max(
        (float(row["counterfactual_soft_success_rate"]) for row in threshold_020_rows),
        default=0.0,
    )
    max_actual_success_rate = max((float(row["actual_success_rate"]) for row in panel_rows), default=0.0)
    high_sensitivity_detected = min_soft_success_gain_at_020 >= HIGH_SENSITIVITY_GAIN_THRESHOLD

    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in panel_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in panel_rows)
    actual_success_claim_count = sum(_bool(row.get("actual_success_claim")) for row in panel_rows)
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
        "candidate_family_ranking_claim_made": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    required_thresholds = tuple(float(value) for value in THRESHOLDS_M)
    all_required_thresholds_present = all(value in threshold_values for value in required_thresholds)
    failure_types_observed = []
    if len(source_values) != 3 or not all_required_thresholds_present:
        failure_types_observed.append("scenario_sampling_failure")
    if ranking_admissible_count or winner_selected_count or actual_success_claim_count:
        failure_types_observed.append("contract_violation")
    if not high_sensitivity_detected:
        failure_types_observed.append("metric_artifact")

    passes = (
        len(source_values) == 3
        and all_required_thresholds_present
        and len(panel_rows) == len(source_values) * len(required_thresholds)
        and high_sensitivity_detected
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and actual_success_claim_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL
    decision_rows = _decision_rows(high_sensitivity_detected=high_sensitivity_detected)
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
        "threshold_count": len(threshold_values),
        "thresholds_m": threshold_values,
        "all_required_thresholds_present": all_required_thresholds_present,
        "high_sensitivity_gain_threshold": HIGH_SENSITIVITY_GAIN_THRESHOLD,
        "high_boundary_threshold_sensitivity_detected": high_sensitivity_detected,
        "min_soft_success_gain_at_0_20m": min_soft_success_gain_at_020,
        "min_counterfactual_soft_success_rate_at_0_20m": min_soft_success_rate_at_020,
        "max_counterfactual_soft_success_rate_at_0_20m": max_soft_success_rate_at_020,
        "max_actual_success_rate": max_actual_success_rate,
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
    summary = run_boundary_threshold_sensitivity_panel(
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
    print(f"min_soft_success_gain_at_0_20m={summary['min_soft_success_gain_at_0_20m']}")
    print(
        "min_counterfactual_soft_success_rate_at_0_20m="
        f"{summary['min_counterfactual_soft_success_rate_at_0_20m']}"
    )
    print(f"actual_success_improvement_claim_made={summary['actual_success_improvement_claim_made']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
