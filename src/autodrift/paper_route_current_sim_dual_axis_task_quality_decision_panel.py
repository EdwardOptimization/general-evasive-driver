"""Build a current-sim task-quality decision panel from existing artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_M2362_DIR = Path("runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution")
DEFAULT_M2397_DIR = Path("runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation")
DEFAULT_M2413_DIR = Path("runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation")
DEFAULT_M2426_DIR = Path("runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence")
DEFAULT_M2428_DIR = Path("runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex")
DEFAULT_OUTPUT_DIR = Path("runs/m2431_paper_route_current_sim_dual_axis_task_quality_decision_panel")
DEFAULT_NEXT_BLOCKER = "m2432-paper-route-current-sim-dual-axis-task-quality-decision-panel-result-audit"

RESULT_PASS = "current_sim_dual_axis_task_quality_decision_panel_pass"
RESULT_FAIL = "current_sim_dual_axis_task_quality_decision_panel_incomplete_or_fail"
OUTCOME_BLOCKER_OBSERVED = "current_sim_task_quality_blocker_observed"
ROUTE_RECOMMENDATION = "route_to_task_semantics_reassessment_before_more_source_linked_repair"

PANEL_FIELDNAMES = [
    "panel_id",
    "source_milestone",
    "panel_kind",
    "artifact_path",
    "episode_count",
    "success_rate",
    "collision_rate",
    "offtrack_rate",
    "max_step_noncompletion_rate",
    "other_failure_rate",
    "dominant_failure_mode",
    "offtrack_dominated",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
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


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def _outcome_from_summary(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    outcome = summary.get("global_outcome", {})
    return outcome if isinstance(outcome, Mapping) else {}


def _offtrack_dominated(row: Mapping[str, Any]) -> bool:
    return str(row.get("dominant_failure_mode", "")) == "offtrack_dominated_failure" or _float(
        row.get("offtrack_rate")
    ) >= 0.70


def _panel_row_from_outcome(
    *,
    panel_id: str,
    source_milestone: str,
    panel_kind: str,
    artifact_path: Path,
    outcome: Mapping[str, Any],
) -> dict[str, Any]:
    offtrack_dominated = _offtrack_dominated(outcome)
    return {
        "panel_id": panel_id,
        "source_milestone": source_milestone,
        "panel_kind": panel_kind,
        "artifact_path": str(artifact_path),
        "episode_count": _int(outcome.get("episode_count")),
        "success_rate": _float(outcome.get("success_rate")),
        "collision_rate": _float(outcome.get("collision_rate")),
        "offtrack_rate": _float(outcome.get("offtrack_rate")),
        "max_step_noncompletion_rate": _float(outcome.get("max_step_noncompletion_rate")),
        "other_failure_rate": _float(outcome.get("other_failure_rate")),
        "dominant_failure_mode": str(outcome.get("dominant_failure_mode", "")),
        "offtrack_dominated": offtrack_dominated,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _panel_rows_from_candidate_aggregate(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv_rows(path):
        candidate_id = str(row.get("group_value", ""))
        if not candidate_id:
            continue
        rows.append(
            _panel_row_from_outcome(
                panel_id=f"m2428_{candidate_id}",
                source_milestone="m2428",
                panel_kind="matched_repair_candidate_reindex",
                artifact_path=path,
                outcome=row,
            )
        )
    return rows


def _decision_rows(*, c04_coverage_gap: bool, all_offtrack_dominated: bool) -> list[dict[str, Any]]:
    return [
        {
            "decision_key": "new_measured_rollout_started",
            "decision_value": "false",
            "admissible": True,
            "reason": "M2431 reuses existing measured artifacts only.",
        },
        {
            "decision_key": "candidate_ranking_or_winner",
            "decision_value": "false",
            "admissible": True,
            "reason": "Panel rows are diagnostic-only and do not select a candidate or controller.",
        },
        {
            "decision_key": "current_sim_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "The panel is a task-quality blocker reanalysis, not a current-sim verdict.",
        },
        {
            "decision_key": "self_id_or_finite_window_vs_gru_verdict",
            "decision_value": "blocked",
            "admissible": False,
            "reason": "The panel does not compare history models or run history interventions.",
        },
        {
            "decision_key": "c04_source_coverage",
            "decision_value": "gap_observed" if c04_coverage_gap else "covered",
            "admissible": not c04_coverage_gap,
            "reason": "c04 remains excluded when the outcome-failure source key has no executable source match.",
        },
        {
            "decision_key": "more_source_linked_local_repair",
            "decision_value": "no_go" if all_offtrack_dominated else "conditional",
            "admissible": not all_offtrack_dominated,
            "reason": "Do not continue local source-linked repair if all current measured panels remain offtrack-dominated.",
        },
        {
            "decision_key": "next_route",
            "decision_value": ROUTE_RECOMMENDATION,
            "admissible": True,
            "reason": "Task semantics and offtrack boundary quality must be reassessed before more repair/training.",
        },
    ]


def run_task_quality_decision_panel(
    *,
    m2362_dir: Path | str = DEFAULT_M2362_DIR,
    m2397_dir: Path | str = DEFAULT_M2397_DIR,
    m2413_dir: Path | str = DEFAULT_M2413_DIR,
    m2426_dir: Path | str = DEFAULT_M2426_DIR,
    m2428_dir: Path | str = DEFAULT_M2428_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    m2362 = Path(m2362_dir)
    m2397 = Path(m2397_dir)
    m2413 = Path(m2413_dir)
    m2426 = Path(m2426_dir)
    m2428 = Path(m2428_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    panel_rows = [
        _panel_row_from_outcome(
            panel_id="m2362_repaired_pack_global",
            source_milestone="m2362",
            panel_kind="repaired_pack_global",
            artifact_path=m2362 / "summary.json",
            outcome=_outcome_from_summary(read_json(m2362 / "summary.json")),
        ),
        _panel_row_from_outcome(
            panel_id="m2397_effective_candidate_global",
            source_milestone="m2397",
            panel_kind="effective_candidate_global",
            artifact_path=m2397 / "summary.json",
            outcome=_outcome_from_summary(read_json(m2397 / "summary.json")),
        ),
        _panel_row_from_outcome(
            panel_id="m2413_source_linked_global",
            source_milestone="m2413",
            panel_kind="source_linked_global",
            artifact_path=m2413 / "summary.json",
            outcome=_outcome_from_summary(read_json(m2413 / "summary.json")),
        ),
    ]
    panel_rows.extend(_panel_rows_from_candidate_aggregate(m2428 / "aggregate_by_candidate.csv"))

    reset_summary = read_json(m2426 / "summary.json")
    reindex_summary = read_json(m2428 / "summary.json")
    c04_coverage_gap = bool(reindex_summary.get("c04_included_as_measured") is False) and _int(
        reindex_summary.get("excluded_candidate_count")
    ) > 0
    all_offtrack_dominated = bool(panel_rows) and all(_bool(row.get("offtrack_dominated")) for row in panel_rows)
    measured_panel_count = len(panel_rows)
    offtrack_dominated_panel_count = sum(_bool(row.get("offtrack_dominated")) for row in panel_rows)
    decision_rows = _decision_rows(c04_coverage_gap=c04_coverage_gap, all_offtrack_dominated=all_offtrack_dominated)

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
    ranking_admissible_count = sum(_bool(row.get("ranking_admissible")) for row in panel_rows)
    winner_selected_count = sum(_bool(row.get("winner_selected")) for row in panel_rows)
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    failure_types_observed = []
    if not all_offtrack_dominated:
        failure_types_observed.append("metric_artifact")
    if measured_panel_count < 6:
        failure_types_observed.append("scenario_sampling_failure")
    if ranking_admissible_count or winner_selected_count:
        failure_types_observed.append("contract_violation")

    passes = (
        measured_panel_count >= 6
        and all_offtrack_dominated
        and c04_coverage_gap
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
            "m2362_summary": str(m2362 / "summary.json"),
            "m2397_summary": str(m2397 / "summary.json"),
            "m2413_summary": str(m2413 / "summary.json"),
            "m2426_summary": str(m2426 / "summary.json"),
            "m2428_summary": str(m2428 / "summary.json"),
            "m2428_aggregate_by_candidate": str(m2428 / "aggregate_by_candidate.csv"),
        },
        "source_reset_result_class": reset_summary.get("result_class", ""),
        "source_reindex_result_class": reindex_summary.get("result_class", ""),
        "measured_panel_count": measured_panel_count,
        "offtrack_dominated_panel_count": offtrack_dominated_panel_count,
        "all_measured_panels_offtrack_dominated": all_offtrack_dominated,
        "min_success_rate": min((_float(row.get("success_rate")) for row in panel_rows), default=0.0),
        "max_success_rate": max((_float(row.get("success_rate")) for row in panel_rows), default=0.0),
        "min_offtrack_rate": min((_float(row.get("offtrack_rate")) for row in panel_rows), default=0.0),
        "max_offtrack_rate": max((_float(row.get("offtrack_rate")) for row in panel_rows), default=0.0),
        "c04_source_coverage_gap_observed": c04_coverage_gap,
        "outcome_blocker": OUTCOME_BLOCKER_OBSERVED if all_offtrack_dominated else "mixed_outcome_panel",
        "route_recommendation": ROUTE_RECOMMENDATION,
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
    parser.add_argument("--m2426-dir", type=Path, default=DEFAULT_M2426_DIR)
    parser.add_argument("--m2428-dir", type=Path, default=DEFAULT_M2428_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_task_quality_decision_panel(
        m2362_dir=args.m2362_dir,
        m2397_dir=args.m2397_dir,
        m2413_dir=args.m2413_dir,
        m2426_dir=args.m2426_dir,
        m2428_dir=args.m2428_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"measured_panel_count={summary['measured_panel_count']}")
    print(f"offtrack_dominated_panel_count={summary['offtrack_dominated_panel_count']}")
    print(f"c04_source_coverage_gap_observed={summary['c04_source_coverage_gap_observed']}")
    print(f"route_recommendation={summary['route_recommendation']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if summary["result_class"] == RESULT_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
