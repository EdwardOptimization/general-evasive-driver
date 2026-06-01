"""No-rerun metric semantics conflict diagnosis for scenario task-family support data."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import write_run_state


DEFAULT_EPISODE_ROWS = Path("runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv")
DEFAULT_SCENARIO_SUPPORT_LABELS = Path(
    "runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv"
)
DEFAULT_ROLE_SUPPORT_SUMMARY = Path(
    "runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit"

SCENARIO_FIELDS = [
    "scenario_spec_id",
    "scenario_family_id",
    "role_family",
    "sampled_obstacle_label",
    "hidden_dynamics_bucket",
    "obstacle_longitudinal_timing_bucket",
    "obstacle_lateral_offset_bucket",
]
SAFE_STOP_FIELDNAMES = [
    *SCENARIO_FIELDS,
    "workload_id",
    "support_policy_name",
    "seed_repeat_index",
    "eval_seed",
    "termination_reason",
    "outcome_bucket",
    "min_clearance_margin",
    "collision",
    "offtrack",
    "success",
    "safe_stop_metric_conflict",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
SCENARIO_DIAGNOSIS_FIELDNAMES = [
    *SCENARIO_FIELDS,
    "support_label",
    "episode_count",
    "safe_stop_episode_count",
    "aeb_safe_stop_episode_count",
    "speed_too_low_episode_count",
    "positive_clearance_noncollision_nonofftrack_count",
    "min_safe_stop_clearance_margin",
    "mean_safe_stop_clearance_margin",
    "max_safe_stop_clearance_margin",
    "metric_semantics_label",
    "metric_semantics_reason",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
ROLE_DIAGNOSIS_FIELDNAMES = [
    "role_family",
    "scenario_count",
    "metric_conflict_scenario_count",
    "support_blocked_scenario_count",
    "safe_stop_scenario_count",
    "safe_stop_episode_count",
    "aeb_safe_stop_episode_count",
    "min_safe_stop_clearance_margin",
    "mean_safe_stop_clearance_margin",
    "max_safe_stop_clearance_margin",
    "role_metric_semantics_label",
    "role_metric_semantics_recommendation",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


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
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite_values(values: Iterable[Any]) -> list[float]:
    output: list[float] = []
    for value in values:
        numeric = _float(value)
        if np.isfinite(numeric):
            output.append(float(numeric))
    return output


def _mean(values: Iterable[Any]) -> float | None:
    finite = _finite_values(values)
    if not finite:
        return None
    return float(np.mean(finite))


def _min(values: Iterable[Any]) -> float | None:
    finite = _finite_values(values)
    if not finite:
        return None
    return float(np.min(finite))


def _max(values: Iterable[Any]) -> float | None:
    finite = _finite_values(values)
    if not finite:
        return None
    return float(np.max(finite))


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("termination_reason", "")) == "off_track" or str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion"


def is_safe_stop_metric_conflict(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("termination_reason", "")) == "speed_too_low"
        and not _bool(row.get("collision"))
        and not _is_offtrack(row)
        and not _bool(row.get("success"))
        and _float(row.get("min_clearance_margin")) > 0.0
    )


def _scenario_key(row: Mapping[str, Any]) -> str:
    return str(row.get("scenario_spec_id", ""))


def _scenario_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in SCENARIO_FIELDS}


def safe_stop_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if not is_safe_stop_metric_conflict(row):
            continue
        output.append(
            {
                **_scenario_metadata(row),
                "workload_id": row.get("workload_id", ""),
                "support_policy_name": row.get("support_policy_name", ""),
                "seed_repeat_index": row.get("seed_repeat_index", ""),
                "eval_seed": row.get("eval_seed", ""),
                "termination_reason": row.get("termination_reason", ""),
                "outcome_bucket": row.get("outcome_bucket", ""),
                "min_clearance_margin": _float(row.get("min_clearance_margin")),
                "collision": _bool(row.get("collision")),
                "offtrack": _is_offtrack(row),
                "success": _bool(row.get("success")),
                "safe_stop_metric_conflict": True,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def scenario_diagnosis_rows(
    *,
    episode_rows: Sequence[Mapping[str, Any]],
    scenario_support_labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_scenario: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        rows_by_scenario[_scenario_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for label_row in scenario_support_labels:
        scenario_id = _scenario_key(label_row)
        rows = rows_by_scenario.get(scenario_id, [])
        safe_rows = [row for row in rows if is_safe_stop_metric_conflict(row)]
        aeb_safe_rows = [row for row in safe_rows if str(row.get("support_policy_name", "")) == "aeb"]
        speed_low_rows = [row for row in rows if str(row.get("termination_reason", "")) == "speed_too_low"]
        positive_safe_rows = [
            row
            for row in rows
            if _float(row.get("min_clearance_margin")) > 0.0
            and not _bool(row.get("collision"))
            and not _is_offtrack(row)
            and not _bool(row.get("success"))
        ]
        support_label = str(label_row.get("support_label", ""))
        if aeb_safe_rows and str(label_row.get("role_family", "")) == "R0_stable_avoidable":
            metric_label = "safe_stop_success_semantics_conflict"
            reason = "AEB support stops safely with positive clearance but obstacle-pass success is false"
        elif safe_rows:
            metric_label = "safe_stop_metric_conflict"
            reason = "support policy stops safely with positive clearance but success is false"
        elif support_label == "metric_conflict":
            metric_label = "unresolved_metric_conflict"
            reason = "scenario support label is metric_conflict but safe-stop evidence is absent"
        elif support_label == "support_blocked":
            metric_label = "residual_support_blocked"
            reason = "no safe-stop metric conflict evidence; remains support-blocked"
        else:
            metric_label = "non_metric_conflict"
            reason = "support label does not require metric semantics repair"
        output.append(
            {
                **_scenario_metadata(label_row),
                "support_label": support_label,
                "episode_count": len(rows),
                "safe_stop_episode_count": len(safe_rows),
                "aeb_safe_stop_episode_count": len(aeb_safe_rows),
                "speed_too_low_episode_count": len(speed_low_rows),
                "positive_clearance_noncollision_nonofftrack_count": len(positive_safe_rows),
                "min_safe_stop_clearance_margin": _min(row.get("min_clearance_margin") for row in safe_rows),
                "mean_safe_stop_clearance_margin": _mean(row.get("min_clearance_margin") for row in safe_rows),
                "max_safe_stop_clearance_margin": _max(row.get("min_clearance_margin") for row in safe_rows),
                "metric_semantics_label": metric_label,
                "metric_semantics_reason": reason,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def role_diagnosis_rows(scenario_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in scenario_rows:
        grouped[str(row.get("role_family", ""))].append(row)
    output: list[dict[str, Any]] = []
    for role, rows in sorted(grouped.items()):
        label_counts = Counter(str(row.get("metric_semantics_label", "")) for row in rows)
        safe_stop_rows_for_role = [row for row in rows if int(row.get("safe_stop_episode_count") or 0) > 0]
        safe_stop_values: list[float] = []
        safe_stop_episode_count = 0
        aeb_safe_stop_episode_count = 0
        for row in rows:
            safe_stop_episode_count += int(row.get("safe_stop_episode_count") or 0)
            aeb_safe_stop_episode_count += int(row.get("aeb_safe_stop_episode_count") or 0)
            for key in ("min_safe_stop_clearance_margin", "mean_safe_stop_clearance_margin", "max_safe_stop_clearance_margin"):
                value = _float(row.get(key))
                if np.isfinite(value):
                    safe_stop_values.append(value)
        scenario_count = len(rows)
        metric_conflict_count = sum(str(row.get("support_label", "")) == "metric_conflict" for row in rows)
        support_blocked_count = sum(str(row.get("support_label", "")) == "support_blocked" for row in rows)
        if role == "R0_stable_avoidable" and label_counts.get("safe_stop_success_semantics_conflict", 0) == scenario_count:
            role_label = "role_safe_stop_success_semantics_repair_required"
            recommendation = "define safe-stop success semantics before training or comparison"
        elif support_blocked_count > metric_conflict_count:
            role_label = "role_support_redesign_candidate"
            recommendation = "audit scenario support or support-policy coverage before training"
        elif metric_conflict_count:
            role_label = "role_metric_semantics_audit_required"
            recommendation = "audit role-specific success semantics before training"
        else:
            role_label = "role_non_metric_conflict"
            recommendation = "no metric-semantics blocker from this diagnosis"
        output.append(
            {
                "role_family": role,
                "scenario_count": scenario_count,
                "metric_conflict_scenario_count": metric_conflict_count,
                "support_blocked_scenario_count": support_blocked_count,
                "safe_stop_scenario_count": len(safe_stop_rows_for_role),
                "safe_stop_episode_count": safe_stop_episode_count,
                "aeb_safe_stop_episode_count": aeb_safe_stop_episode_count,
                "min_safe_stop_clearance_margin": _min(safe_stop_values),
                "mean_safe_stop_clearance_margin": _mean(safe_stop_values),
                "max_safe_stop_clearance_margin": _max(safe_stop_values),
                "role_metric_semantics_label": role_label,
                "role_metric_semantics_recommendation": recommendation,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "metric_semantics_conflict_diagnosis_completed",
            "admissible": True,
            "reason": "M2315 is an artifact-only diagnosis over M2313 rows",
        },
        {
            "claim": "environment_rollout_or_training",
            "admissible": False,
            "reason": "M2315 does not run environment reset, rollout, policy action, training, replay, or PPO",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "M2315 does not rank support policies or controller families",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2315 is public diagnostic reanalysis",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2315 does not compare controller families",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2315 runs no history intervention",
        },
    ]


def run_metric_semantics_conflict_diagnosis(
    *,
    episode_rows: Path | str = DEFAULT_EPISODE_ROWS,
    scenario_support_labels: Path | str = DEFAULT_SCENARIO_SUPPORT_LABELS,
    role_support_summary: Path | str = DEFAULT_ROLE_SUPPORT_SUMMARY,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    episodes = read_csv_rows(episode_rows)
    scenario_labels = read_csv_rows(scenario_support_labels)
    role_support_rows = read_csv_rows(role_support_summary)
    safe_rows = safe_stop_rows(episodes)
    scenario_rows = scenario_diagnosis_rows(episode_rows=episodes, scenario_support_labels=scenario_labels)
    role_rows = role_diagnosis_rows(scenario_rows)
    metric_conflict_rows = [row for row in scenario_rows if str(row.get("support_label", "")) == "metric_conflict"]
    residual_support_blocked_rows = [
        row for row in scenario_rows if str(row.get("metric_semantics_label", "")) == "residual_support_blocked"
    ]

    write_csv_rows(output / "safe_stop_metric_conflict_rows.csv", safe_rows, fieldnames=SAFE_STOP_FIELDNAMES)
    write_csv_rows(output / "scenario_metric_semantics_diagnosis.csv", scenario_rows, fieldnames=SCENARIO_DIAGNOSIS_FIELDNAMES)
    write_csv_rows(output / "metric_conflict_scenarios.csv", metric_conflict_rows, fieldnames=SCENARIO_DIAGNOSIS_FIELDNAMES)
    write_csv_rows(
        output / "residual_support_blocked_scenarios.csv",
        residual_support_blocked_rows,
        fieldnames=SCENARIO_DIAGNOSIS_FIELDNAMES,
    )
    write_csv_rows(output / "role_metric_semantics_summary.csv", role_rows, fieldnames=ROLE_DIAGNOSIS_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }
    guardrail_violation_count = sum(bool(value) for value in guardrail_flags.values())
    role_labels = {str(row.get("role_family", "")): str(row.get("role_metric_semantics_label", "")) for row in role_rows}
    r0_role = next((row for row in role_rows if str(row.get("role_family", "")) == "R0_stable_avoidable"), {})
    result_passes = (
        bool(episodes)
        and bool(scenario_labels)
        and len(scenario_rows) == len(scenario_labels)
        and guardrail_violation_count == 0
        and int(r0_role.get("aeb_safe_stop_episode_count") or 0) > 0
    )
    artifacts = {
        "summary": str(output / "summary.json"),
        "safe_stop_metric_conflict_rows": str(output / "safe_stop_metric_conflict_rows.csv"),
        "scenario_metric_semantics_diagnosis": str(output / "scenario_metric_semantics_diagnosis.csv"),
        "metric_conflict_scenarios": str(output / "metric_conflict_scenarios.csv"),
        "residual_support_blocked_scenarios": str(output / "residual_support_blocked_scenarios.csv"),
        "role_metric_semantics_summary": str(output / "role_metric_semantics_summary.csv"),
        "claim_boundary": str(output / "claim_boundary.csv"),
        "run_state": str(output / "run_state.json"),
    }
    summary = {
        "result_class": (
            "current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass"
            if result_passes
            else "current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "input_episode_count": len(episodes),
        "input_scenario_support_label_count": len(scenario_labels),
        "input_role_support_summary_count": len(role_support_rows),
        "scenario_metric_semantics_row_count": len(scenario_rows),
        "metric_conflict_scenario_count": len(metric_conflict_rows),
        "residual_support_blocked_scenario_count": len(residual_support_blocked_rows),
        "safe_stop_metric_conflict_episode_count": len(safe_rows),
        "safe_stop_metric_conflict_scenario_count": len({str(row.get("scenario_spec_id", "")) for row in safe_rows}),
        "r0_aeb_safe_stop_episode_count": int(r0_role.get("aeb_safe_stop_episode_count") or 0),
        "r0_safe_stop_episode_count": int(r0_role.get("safe_stop_episode_count") or 0),
        "r0_safe_stop_scenario_count": int(r0_role.get("safe_stop_scenario_count") or 0),
        "r0_min_safe_stop_clearance_margin": r0_role.get("min_safe_stop_clearance_margin"),
        "r0_mean_safe_stop_clearance_margin": r0_role.get("mean_safe_stop_clearance_margin"),
        "r0_max_safe_stop_clearance_margin": r0_role.get("max_safe_stop_clearance_margin"),
        "role_metric_semantics_labels": role_labels,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "controller_family_ranking_claim_made": False,
        "winner_selected": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only": True,
        "artifacts": artifacts,
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    write_run_state(
        output / "run_state.json",
        {
            "input_episode_count": len(episodes),
            "scenario_metric_semantics_row_count": len(scenario_rows),
            "safe_stop_metric_conflict_episode_count": len(safe_rows),
            "complete": bool(result_passes),
            "next_blocker": str(next_blocker),
        },
    )
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-rows", type=Path, default=DEFAULT_EPISODE_ROWS)
    parser.add_argument("--scenario-support-labels", type=Path, default=DEFAULT_SCENARIO_SUPPORT_LABELS)
    parser.add_argument("--role-support-summary", type=Path, default=DEFAULT_ROLE_SUPPORT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_metric_semantics_conflict_diagnosis(
        episode_rows=args.episode_rows,
        scenario_support_labels=args.scenario_support_labels,
        role_support_summary=args.role_support_summary,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_episode_count={summary['input_episode_count']}")
    print(f"safe_stop_metric_conflict_episode_count={summary['safe_stop_metric_conflict_episode_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
