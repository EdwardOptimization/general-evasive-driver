"""Build an event-level offtrack semantics panel from existing episode rows."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_M2362_DIR = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution")
DEFAULT_M2397_DIR = Path("runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation")
DEFAULT_M2413_DIR = Path("runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation")
DEFAULT_OUTPUT_DIR = Path("runs/m2433_paper_route_current_sim_dual_axis_offtrack_semantics_panel")
DEFAULT_NEXT_BLOCKER = "m2434-paper-route-current-sim-dual-axis-offtrack-semantics-panel-result-audit"

RESULT_PASS = "current_sim_dual_axis_offtrack_semantics_panel_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_semantics_panel_incomplete_or_fail"
ROUTE_RECOMMENDATION = "route_to_offtrack_boundary_task_semantics_reassessment_audit"

HIGH_CLEARANCE_M = 1.0
LOW_OVERSHOOT_M = 0.20
ROAD_BOUNDARY_DOMINANCE_THRESHOLD = 0.80

PANEL_FIELDNAMES = [
    "panel_id",
    "source_milestone",
    "episode_rows_path",
    "episode_count",
    "success_count",
    "success_rate",
    "collision_count",
    "collision_rate",
    "offtrack_count",
    "offtrack_rate",
    "offtrack_positive_clearance_count",
    "offtrack_positive_clearance_rate_of_offtrack",
    "offtrack_high_clearance_count",
    "offtrack_high_clearance_rate_of_offtrack",
    "offtrack_low_overshoot_count",
    "offtrack_low_overshoot_rate_of_offtrack",
    "offtrack_positive_clearance_low_overshoot_count",
    "offtrack_positive_clearance_low_overshoot_rate_of_offtrack",
    "mean_offtrack_clearance_margin",
    "mean_offtrack_max_overshoot",
    "mean_time_to_first_off_track_s",
    "offtrack_before_obstacle_pass_count",
    "offtrack_after_obstacle_pass_count",
    "offtrack_obstacle_pass_unavailable_count",
    "road_boundary_dominated_offtrack",
    "diagnostic_only",
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


def _mean(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values if value is not None]
    if not finite:
        return None
    return float(sum(finite) / len(finite))


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


def _panel_row(*, panel_id: str, source_milestone: str, episode_rows_path: Path) -> dict[str, Any]:
    rows = read_csv_rows(episode_rows_path)
    offtrack_rows = [row for row in rows if _is_offtrack(row)]
    episode_count = len(rows)
    offtrack_count = len(offtrack_rows)
    collision_count = sum(_is_collision(row) for row in rows)
    success_count = sum(_is_success(row) for row in rows)

    clearance_values = [_float(row.get("min_clearance_margin")) for row in offtrack_rows]
    overshoot_values = [_float(row.get("max_off_track_overshoot")) for row in offtrack_rows]
    time_values = [_float(row.get("time_to_first_off_track_s")) for row in offtrack_rows]
    offtrack_positive_clearance_count = sum((value is not None and value > 0.0) for value in clearance_values)
    offtrack_high_clearance_count = sum((value is not None and value >= HIGH_CLEARANCE_M) for value in clearance_values)
    offtrack_low_overshoot_count = sum((value is not None and 0.0 <= value <= LOW_OVERSHOOT_M) for value in overshoot_values)
    offtrack_positive_clearance_low_overshoot_count = sum(
        (clearance is not None and clearance > 0.0 and overshoot is not None and 0.0 <= overshoot <= LOW_OVERSHOOT_M)
        for clearance, overshoot in zip(clearance_values, overshoot_values)
    )

    before_pass = 0
    after_pass = 0
    unavailable_pass = 0
    for row in offtrack_rows:
        offtrack_time = _float(row.get("time_to_first_off_track_s"))
        pass_time = _float(row.get("first_obstacle_pass_time_s"))
        if offtrack_time is None or pass_time is None:
            unavailable_pass += 1
        elif offtrack_time < pass_time:
            before_pass += 1
        else:
            after_pass += 1

    positive_clearance_low_overshoot_rate = _rate(offtrack_positive_clearance_low_overshoot_count, offtrack_count)
    road_boundary_dominated = (
        offtrack_count > 0 and positive_clearance_low_overshoot_rate >= ROAD_BOUNDARY_DOMINANCE_THRESHOLD
    )
    return {
        "panel_id": panel_id,
        "source_milestone": source_milestone,
        "episode_rows_path": str(episode_rows_path),
        "episode_count": episode_count,
        "success_count": success_count,
        "success_rate": _rate(success_count, episode_count),
        "collision_count": collision_count,
        "collision_rate": _rate(collision_count, episode_count),
        "offtrack_count": offtrack_count,
        "offtrack_rate": _rate(offtrack_count, episode_count),
        "offtrack_positive_clearance_count": offtrack_positive_clearance_count,
        "offtrack_positive_clearance_rate_of_offtrack": _rate(offtrack_positive_clearance_count, offtrack_count),
        "offtrack_high_clearance_count": offtrack_high_clearance_count,
        "offtrack_high_clearance_rate_of_offtrack": _rate(offtrack_high_clearance_count, offtrack_count),
        "offtrack_low_overshoot_count": offtrack_low_overshoot_count,
        "offtrack_low_overshoot_rate_of_offtrack": _rate(offtrack_low_overshoot_count, offtrack_count),
        "offtrack_positive_clearance_low_overshoot_count": offtrack_positive_clearance_low_overshoot_count,
        "offtrack_positive_clearance_low_overshoot_rate_of_offtrack": positive_clearance_low_overshoot_rate,
        "mean_offtrack_clearance_margin": _mean(clearance_values),
        "mean_offtrack_max_overshoot": _mean(overshoot_values),
        "mean_time_to_first_off_track_s": _mean(time_values),
        "offtrack_before_obstacle_pass_count": before_pass,
        "offtrack_after_obstacle_pass_count": after_pass,
        "offtrack_obstacle_pass_unavailable_count": unavailable_pass,
        "road_boundary_dominated_offtrack": road_boundary_dominated,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _decision_rows(*, all_road_boundary_dominated: bool) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "new_measured_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2433 reuses existing primary episode rows only.",
        },
        {
            "decision_key": "candidate_or_controller_ranking",
            "decision_value": "false",
            "admissible": True,
            "reason": "Panel rows are source-level diagnostics and do not rank controllers or candidates.",
        },
        {
            "decision_key": "road_boundary_dominated_offtrack",
            "decision_value": str(all_road_boundary_dominated).lower(),
            "admissible": all_road_boundary_dominated,
            "reason": "Offtrack is treated as road-boundary dominated only when positive-clearance low-overshoot offtracks dominate every source panel.",
        },
        {
            "decision_key": "scenario_redesign_executed",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2433 diagnoses task semantics but does not change scenario definitions.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "Event-level semantics are diagnostic; verdict requires a follow-up audit and any selected task change evidence.",
        },
        {
            "decision_key": "next_route",
            "decision_value": ROUTE_RECOMMENDATION,
            "admissible": True,
            "reason": "Audit offtrack boundary semantics before more repair, training, or controller-family comparison.",
        },
    ]


def run_offtrack_semantics_panel(
    *,
    m2362_dir: Path | str = DEFAULT_M2362_DIR,
    m2397_dir: Path | str = DEFAULT_M2397_DIR,
    m2413_dir: Path | str = DEFAULT_M2413_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    m2362 = Path(m2362_dir)
    m2397 = Path(m2397_dir)
    m2413 = Path(m2413_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_summaries = {
        "m2362": read_json(m2362 / "summary.json"),
        "m2397": read_json(m2397 / "summary.json"),
        "m2413": read_json(m2413 / "summary.json"),
    }
    panel_rows = [
        _panel_row(
            panel_id="m2362_repaired_pack_primary",
            source_milestone="m2362",
            episode_rows_path=m2362 / "episode_rows.csv",
        ),
        _panel_row(
            panel_id="m2397_effective_candidate_primary",
            source_milestone="m2397",
            episode_rows_path=m2397 / "episode_rows.csv",
        ),
        _panel_row(
            panel_id="m2413_source_linked_primary",
            source_milestone="m2413",
            episode_rows_path=m2413 / "episode_rows.csv",
        ),
    ]
    all_road_boundary_dominated = bool(panel_rows) and all(
        _bool(row.get("road_boundary_dominated_offtrack")) for row in panel_rows
    )
    decision_rows = _decision_rows(all_road_boundary_dominated=all_road_boundary_dominated)
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in panel_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in panel_rows)
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
    failure_types_observed = []
    if len(panel_rows) != 3 or any(int(row["episode_count"]) <= 0 for row in panel_rows):
        failure_types_observed.append("scenario_sampling_failure")
    if ranking_admissible_count or winner_selected_count:
        failure_types_observed.append("contract_violation")
    if not all_road_boundary_dominated:
        failure_types_observed.append("metric_artifact")

    passes = (
        len(panel_rows) == 3
        and all(int(row["episode_count"]) > 0 for row in panel_rows)
        and all_road_boundary_dominated
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )
    result_class = RESULT_PASS if passes else RESULT_FAIL
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
        "source_result_classes": {
            source: summary.get("result_class", "") for source, summary in source_summaries.items()
        },
        "panel_row_count": len(panel_rows),
        "road_boundary_dominated_panel_count": sum(
            _bool(row.get("road_boundary_dominated_offtrack")) for row in panel_rows
        ),
        "all_panels_road_boundary_dominated_offtrack": all_road_boundary_dominated,
        "high_clearance_threshold_m": HIGH_CLEARANCE_M,
        "low_overshoot_threshold_m": LOW_OVERSHOOT_M,
        "road_boundary_dominance_threshold": ROAD_BOUNDARY_DOMINANCE_THRESHOLD,
        "min_positive_clearance_low_overshoot_rate": min(
            (float(row["offtrack_positive_clearance_low_overshoot_rate_of_offtrack"]) for row in panel_rows),
            default=0.0,
        ),
        "max_positive_clearance_low_overshoot_rate": max(
            (float(row["offtrack_positive_clearance_low_overshoot_rate_of_offtrack"]) for row in panel_rows),
            default=0.0,
        ),
        "min_offtrack_high_clearance_rate": min(
            (float(row["offtrack_high_clearance_rate_of_offtrack"]) for row in panel_rows),
            default=0.0,
        ),
        "max_mean_offtrack_max_overshoot": max(
            (float(row["mean_offtrack_max_overshoot"]) for row in panel_rows),
            default=0.0,
        ),
        "diagnostic_only": True,
        "new_measured_rollout_started": False,
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
    summary = run_offtrack_semantics_panel(
        m2362_dir=args.m2362_dir,
        m2397_dir=args.m2397_dir,
        m2413_dir=args.m2413_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"panel_row_count={summary['panel_row_count']}")
    print(f"road_boundary_dominated_panel_count={summary['road_boundary_dominated_panel_count']}")
    print(
        "min_positive_clearance_low_overshoot_rate="
        f"{summary['min_positive_clearance_low_overshoot_rate']}"
    )
    print(f"route_recommendation={summary['route_recommendation']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
