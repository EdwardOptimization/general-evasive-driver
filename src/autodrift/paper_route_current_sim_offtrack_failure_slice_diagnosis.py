"""No-rerun offtrack failure-slice diagnosis for M2244 vs M2253 rows."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json


DEFAULT_BASELINE_EPISODES = Path(
    "runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv"
)
DEFAULT_REPAIRED_EPISODES = Path(
    "runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis")
DEFAULT_NEXT_BLOCKER = "m2257-paper-route-current-sim-offtrack-failure-slice-diagnosis-result-audit"
EXPECTED_PANEL_ROWS = 480
MATERIAL_COUNT_DELTA = 5
MATERIAL_RELATIVE_INCREASE = 0.20

DELTA_FIELDNAMES = [
    "axis",
    "group_key",
    "baseline_count",
    "repaired_count",
    "count_delta",
    "baseline_success_count",
    "repaired_success_count",
    "success_delta",
    "baseline_offtrack_count",
    "repaired_offtrack_count",
    "offtrack_delta",
    "baseline_collision_count",
    "repaired_collision_count",
    "collision_delta",
    "baseline_mean_return",
    "repaired_mean_return",
    "mean_return_delta",
    "material_delta",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]

ROUTE_FIELDNAMES = [
    "route",
    "admitted",
    "support_reason",
    "support_axis",
    "support_group",
    "support_delta",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(parsed):
        return None
    return parsed


def _mean(values: Sequence[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    if not finite:
        return None
    return float(np.mean(finite))


def _is_success(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "success_obstacle_pass" or (
        _bool(row.get("obstacle_completed")) and not _bool(row.get("collision"))
    )


def _is_collision(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "collision_failure" or _bool(row.get("collision"))


def _is_offtrack(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "off_track_noncollision_noncompletion" or str(
        row.get("termination_reason", "")
    ) == "off_track"


def _is_max_step(row: Mapping[str, Any]) -> bool:
    return str(row.get("outcome_bucket", "")) == "max_steps_noncompletion" or _bool(row.get("truncated"))


def _offtrack_timing_bucket(row: Mapping[str, Any]) -> str:
    if not _is_offtrack(row):
        return "no_offtrack"
    time_s = _float_or_none(row.get("time_to_first_off_track_s"))
    if time_s is None:
        return "unknown_offtrack_time"
    if time_s <= 1.20:
        return "early_offtrack"
    if time_s <= 1.70:
        return "mid_offtrack"
    return "late_offtrack"


def _offtrack_severity_bucket(row: Mapping[str, Any]) -> str:
    overshoot = _float_or_none(row.get("max_off_track_overshoot"))
    if overshoot is None:
        return "unknown_overshoot"
    if overshoot <= 0.0:
        return "no_offtrack_overshoot"
    if overshoot <= 0.02:
        return "trace_overshoot"
    if overshoot <= 0.05:
        return "mild_overshoot"
    return "severe_overshoot"


def _clearance_risk_bucket(row: Mapping[str, Any]) -> str:
    if _is_collision(row):
        return "collision"
    margin = _float_or_none(row.get("min_clearance_margin"))
    if margin is None:
        return "unknown_clearance_margin"
    if margin < 0.0:
        return "negative_clearance_margin"
    if margin < 0.25:
        return "low_clearance_margin"
    if margin < 1.0:
        return "medium_clearance_margin"
    return "safe_clearance_margin"


def _sideslip_bucket(row: Mapping[str, Any]) -> str:
    value = _float_or_none(row.get("high_sideslip_fraction"))
    if value is None:
        return "unknown_sideslip"
    if value <= 0.0:
        return "zero_sideslip"
    if value < 0.05:
        return "low_sideslip"
    return "high_sideslip"


def _recovery_bucket(row: Mapping[str, Any]) -> str:
    if _is_success(row):
        return "success"
    if _bool(row.get("recovery_success")):
        return "recovery_success"
    if _bool(row.get("drift_used")):
        return "drift_without_recovery"
    return "no_recovery"


def _annotate_rows(rows: Sequence[Mapping[str, Any]], panel: str) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["panel"] = panel
        item["profile_seed"] = f"{item.get('profile_name', '')}|{item.get('seed_id', '')}"
        item["offtrack_timing_bucket"] = _offtrack_timing_bucket(item)
        item["offtrack_severity_bucket"] = _offtrack_severity_bucket(item)
        item["clearance_risk_bucket"] = _clearance_risk_bucket(item)
        item["sideslip_bucket"] = _sideslip_bucket(item)
        item["recovery_bucket"] = _recovery_bucket(item)
        annotated.append(item)
    return annotated


def _counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "success_count": sum(1 for row in rows if _is_success(row)),
        "offtrack_count": sum(1 for row in rows if _is_offtrack(row)),
        "collision_count": sum(1 for row in rows if _is_collision(row)),
        "max_step_count": sum(1 for row in rows if _is_max_step(row)),
        "mean_return": _mean([_float_or_none(row.get("return")) for row in rows]),
    }


def _group_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    return grouped


def _material_delta(delta: int, baseline_count: int) -> bool:
    if abs(delta) >= MATERIAL_COUNT_DELTA:
        return True
    if baseline_count > 0 and delta > 0 and float(delta) / float(baseline_count) >= MATERIAL_RELATIVE_INCREASE:
        return True
    return False


def _delta_rows(
    *,
    axis: str,
    baseline_rows: Sequence[Mapping[str, Any]],
    repaired_rows: Sequence[Mapping[str, Any]],
    key: str | None = None,
) -> list[dict[str, Any]]:
    if key is None:
        pairs = {"global": (list(baseline_rows), list(repaired_rows))}
    else:
        baseline_groups = _group_by(baseline_rows, key)
        repaired_groups = _group_by(repaired_rows, key)
        pairs = {
            group_key: (baseline_groups.get(group_key, []), repaired_groups.get(group_key, []))
            for group_key in sorted(set(baseline_groups) | set(repaired_groups))
        }
    output: list[dict[str, Any]] = []
    for group_key, (baseline_group, repaired_group) in pairs.items():
        b = _counts(baseline_group)
        r = _counts(repaired_group)
        mean_return_delta = None
        if b["mean_return"] is not None and r["mean_return"] is not None:
            mean_return_delta = float(r["mean_return"]) - float(b["mean_return"])
        output.append(
            {
                "axis": axis,
                "group_key": group_key,
                "baseline_count": b["count"],
                "repaired_count": r["count"],
                "count_delta": r["count"] - b["count"],
                "baseline_success_count": b["success_count"],
                "repaired_success_count": r["success_count"],
                "success_delta": r["success_count"] - b["success_count"],
                "baseline_offtrack_count": b["offtrack_count"],
                "repaired_offtrack_count": r["offtrack_count"],
                "offtrack_delta": r["offtrack_count"] - b["offtrack_count"],
                "baseline_collision_count": b["collision_count"],
                "repaired_collision_count": r["collision_count"],
                "collision_delta": r["collision_count"] - b["collision_count"],
                "baseline_mean_return": b["mean_return"],
                "repaired_mean_return": r["mean_return"],
                "mean_return_delta": mean_return_delta,
                "material_delta": _material_delta(
                    (r["offtrack_count"] - b["offtrack_count"]) + (r["collision_count"] - b["collision_count"]),
                    b["offtrack_count"] + b["collision_count"],
                ),
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def _panel_summary(panel: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = _counts(rows)
    total = max(1, counts["count"])
    return {
        "panel": panel,
        "episode_count": counts["count"],
        "success_count": counts["success_count"],
        "success_rate": counts["success_count"] / total,
        "offtrack_count": counts["offtrack_count"],
        "offtrack_rate": counts["offtrack_count"] / total,
        "collision_count": counts["collision_count"],
        "collision_rate": counts["collision_count"] / total,
        "max_step_count": counts["max_step_count"],
        "max_step_rate": counts["max_step_count"] / total,
        "mean_return": counts["mean_return"],
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _route_rows(
    *,
    global_delta: Mapping[str, Any],
    timing_rows: Sequence[Mapping[str, Any]],
    severity_rows: Sequence[Mapping[str, Any]],
    clearance_rows: Sequence[Mapping[str, Any]],
    profile_seed_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def add(route: str, reason: str, axis: str, group: str, delta: Any) -> None:
        candidates.append(
            {
                "route": route,
                "admitted": True,
                "support_reason": reason,
                "support_axis": axis,
                "support_group": group,
                "support_delta": delta,
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )

    offtrack_delta = int(global_delta.get("offtrack_delta", 0) or 0)
    collision_delta = int(global_delta.get("collision_delta", 0) or 0)

    early_delta = max(
        [int(row.get("offtrack_delta", 0) or 0) for row in timing_rows if row.get("group_key") == "early_offtrack"]
        or [0]
    )
    severe_delta = max(
        [int(row.get("offtrack_delta", 0) or 0) for row in severity_rows if row.get("group_key") == "severe_overshoot"]
        or [0]
    )
    negative_clearance_delta = max(
        [
            int(row.get("collision_delta", 0) or 0) + int(row.get("offtrack_delta", 0) or 0)
            for row in clearance_rows
            if row.get("group_key") in {"collision", "negative_clearance_margin"}
        ]
        or [0]
    )
    profile_seed_worst = max(
        profile_seed_rows,
        key=lambda row: int(row.get("offtrack_delta", 0) or 0) + int(row.get("collision_delta", 0) or 0),
        default={},
    )
    profile_seed_delta = int(profile_seed_worst.get("offtrack_delta", 0) or 0) + int(
        profile_seed_worst.get("collision_delta", 0) or 0
    )

    if offtrack_delta > 0 and (early_delta >= MATERIAL_COUNT_DELTA or severe_delta >= MATERIAL_COUNT_DELTA):
        add(
            "recovery_corridor_curriculum_redesign",
            "offtrack regression is concentrated in early timing or severe overshoot",
            "offtrack_timing_or_severity",
            f"early_delta={early_delta};severe_delta={severe_delta}",
            max(early_delta, severe_delta),
        )
    if offtrack_delta > 0:
        add(
            "stronger_offtrack_recovery_corridor_repair_design",
            "global offtrack count increased after the reward repair",
            "global",
            "offtrack_delta",
            offtrack_delta,
        )
    if collision_delta >= MATERIAL_COUNT_DELTA or negative_clearance_delta >= MATERIAL_COUNT_DELTA:
        add(
            "collision_clearance_guardrail_repair",
            "collision or negative-clearance risk increased materially",
            "clearance_risk",
            "collision_or_negative_clearance",
            max(collision_delta, negative_clearance_delta),
        )
    if profile_seed_delta >= MATERIAL_COUNT_DELTA:
        add(
            "profile_seed_support_audit",
            "one profile_seed group dominates the regression",
            "profile_seed",
            str(profile_seed_worst.get("group_key", "")),
            profile_seed_delta,
        )
    if not candidates:
        add(
            "branch_synthesis_or_stop",
            "no material actionable slice dominates",
            "global",
            "diffuse",
            0,
        )
    return candidates


def run_offtrack_failure_slice_diagnosis(
    *,
    baseline_episodes: Path | str = DEFAULT_BASELINE_EPISODES,
    repaired_episodes: Path | str = DEFAULT_REPAIRED_EPISODES,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    baseline_rows = _annotate_rows(read_csv_rows(baseline_episodes), "baseline_m2244")
    repaired_rows = _annotate_rows(read_csv_rows(repaired_episodes), "repaired_m2253")

    panel_rows = [_panel_summary("baseline_m2244", baseline_rows), _panel_summary("repaired_m2253", repaired_rows)]
    global_delta = _delta_rows(axis="global", baseline_rows=baseline_rows, repaired_rows=repaired_rows)[0]
    profile_seed_rows = _delta_rows(
        axis="profile_seed", baseline_rows=baseline_rows, repaired_rows=repaired_rows, key="profile_seed"
    )
    outcome_rows = _delta_rows(axis="outcome_bucket", baseline_rows=baseline_rows, repaired_rows=repaired_rows, key="outcome_bucket")
    timing_rows = _delta_rows(
        axis="offtrack_timing_bucket",
        baseline_rows=baseline_rows,
        repaired_rows=repaired_rows,
        key="offtrack_timing_bucket",
    )
    severity_rows = _delta_rows(
        axis="offtrack_severity_bucket",
        baseline_rows=baseline_rows,
        repaired_rows=repaired_rows,
        key="offtrack_severity_bucket",
    )
    clearance_rows = _delta_rows(
        axis="clearance_risk_bucket",
        baseline_rows=baseline_rows,
        repaired_rows=repaired_rows,
        key="clearance_risk_bucket",
    )
    route_rows = _route_rows(
        global_delta=global_delta,
        timing_rows=timing_rows,
        severity_rows=severity_rows,
        clearance_rows=clearance_rows,
        profile_seed_rows=profile_seed_rows,
    )

    write_csv_rows(output / "panel_summary.csv", panel_rows)
    write_csv_rows(output / "global_delta.csv", [global_delta], fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "profile_seed_delta.csv", profile_seed_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "outcome_delta.csv", outcome_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "offtrack_timing_delta.csv", timing_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "offtrack_severity_delta.csv", severity_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "clearance_risk_delta.csv", clearance_rows, fieldnames=DELTA_FIELDNAMES)
    write_csv_rows(output / "failure_slice_routes.csv", route_rows, fieldnames=ROUTE_FIELDNAMES)

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "training_started": False,
        "ppo_started": False,
        "replay_started": False,
        "private_holdout_used": False,
        "promoted": False,
        "controller_family_ranking_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "winner_selected": False,
    }
    guardrail_violation_count = sum(1 for value in guardrail_flags.values() if bool(value))
    support_complete = len(baseline_rows) == EXPECTED_PANEL_ROWS and len(repaired_rows) == EXPECTED_PANEL_ROWS
    result_class = (
        "current_sim_offtrack_failure_slice_diagnosis_pass"
        if support_complete and route_rows and guardrail_violation_count == 0
        else "current_sim_offtrack_failure_slice_diagnosis_fail"
    )
    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "baseline_episodes": str(baseline_episodes),
        "repaired_episodes": str(repaired_episodes),
        "output_dir": str(output),
        "baseline_episode_count": len(baseline_rows),
        "repaired_episode_count": len(repaired_rows),
        "expected_panel_rows": EXPECTED_PANEL_ROWS,
        "support_complete": support_complete,
        "global_delta": global_delta,
        "primary_route": route_rows[0]["route"] if route_rows else "",
        "route_count": len(route_rows),
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "panel_summary": str(output / "panel_summary.csv"),
            "global_delta": str(output / "global_delta.csv"),
            "profile_seed_delta": str(output / "profile_seed_delta.csv"),
            "outcome_delta": str(output / "outcome_delta.csv"),
            "offtrack_timing_delta": str(output / "offtrack_timing_delta.csv"),
            "offtrack_severity_delta": str(output / "offtrack_severity_delta.csv"),
            "clearance_risk_delta": str(output / "clearance_risk_delta.csv"),
            "failure_slice_routes": str(output / "failure_slice_routes.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-episodes", type=Path, default=DEFAULT_BASELINE_EPISODES)
    parser.add_argument("--repaired-episodes", type=Path, default=DEFAULT_REPAIRED_EPISODES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_offtrack_failure_slice_diagnosis(
        baseline_episodes=args.baseline_episodes,
        repaired_episodes=args.repaired_episodes,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"primary_route={summary['primary_route']}")
    print(f"result_class={summary['result_class']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
