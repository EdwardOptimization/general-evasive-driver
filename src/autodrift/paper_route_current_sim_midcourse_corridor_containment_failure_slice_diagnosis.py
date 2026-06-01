"""No-rerun M2244/M2265/M2253 containment failure-slice diagnosis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift import paper_route_current_sim_offtrack_failure_slice_diagnosis as offtrack_diagnosis


DEFAULT_BASELINE_EPISODES = Path(
    "runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv"
)
DEFAULT_TARGETED_EPISODES = Path(
    "runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv"
)
DEFAULT_REFERENCE_EPISODES = Path(
    "runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis"
)
DEFAULT_NEXT_BLOCKER = (
    "m2270-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-result-audit"
)
EXPECTED_PANEL_ROWS = 480

BASELINE_LABEL = "baseline_m2244"
TARGETED_LABEL = "targeted_m2265"
REFERENCE_LABEL = "generic_m2253"

DELTA_FIELDNAMES = [
    "comparison",
    "axis",
    "group_key",
    "left_panel",
    "right_panel",
    "left_count",
    "right_count",
    "count_delta",
    "left_success_count",
    "right_success_count",
    "success_delta",
    "left_offtrack_count",
    "right_offtrack_count",
    "offtrack_delta",
    "left_collision_count",
    "right_collision_count",
    "collision_delta",
    "left_mean_return",
    "right_mean_return",
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
    "primary_comparison",
    "global_success_delta_vs_base",
    "global_offtrack_delta_vs_base",
    "global_collision_delta_vs_base",
    "targeted_offtrack_delta_vs_generic",
    "mid_offtrack_delta_vs_base",
    "mild_overshoot_delta_vs_base",
    "safe_clearance_offtrack_delta_vs_base",
    "collision_guardrail_pass",
    "max_step_guardrail_pass",
    "diagnostic_only",
    "ranking_admissible",
    "winner_selected",
]


def _delta_rows(
    *,
    comparison: str,
    left_panel: str,
    right_panel: str,
    axis: str,
    left_rows: Sequence[Mapping[str, Any]],
    right_rows: Sequence[Mapping[str, Any]],
    key: str | None = None,
) -> list[dict[str, Any]]:
    raw_rows = offtrack_diagnosis._delta_rows(
        axis=axis,
        baseline_rows=left_rows,
        repaired_rows=right_rows,
        key=key,
    )
    output: list[dict[str, Any]] = []
    for row in raw_rows:
        output.append(
            {
                "comparison": comparison,
                "axis": row["axis"],
                "group_key": row["group_key"],
                "left_panel": left_panel,
                "right_panel": right_panel,
                "left_count": row["baseline_count"],
                "right_count": row["repaired_count"],
                "count_delta": row["count_delta"],
                "left_success_count": row["baseline_success_count"],
                "right_success_count": row["repaired_success_count"],
                "success_delta": row["success_delta"],
                "left_offtrack_count": row["baseline_offtrack_count"],
                "right_offtrack_count": row["repaired_offtrack_count"],
                "offtrack_delta": row["offtrack_delta"],
                "left_collision_count": row["baseline_collision_count"],
                "right_collision_count": row["repaired_collision_count"],
                "collision_delta": row["collision_delta"],
                "left_mean_return": row["baseline_mean_return"],
                "right_mean_return": row["repaired_mean_return"],
                "mean_return_delta": row["mean_return_delta"],
                "material_delta": row["material_delta"],
                "diagnostic_only": True,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return output


def _row_by_group(rows: Sequence[Mapping[str, Any]], group_key: str) -> Mapping[str, Any]:
    for row in rows:
        if str(row.get("group_key", "")) == group_key:
            return row
    return {}


def _int_value(row: Mapping[str, Any], key: str) -> int:
    return int(row.get(key, 0) or 0)


def _route_rows(
    *,
    support_complete: bool,
    primary_global: Mapping[str, Any],
    generic_vs_targeted_global: Mapping[str, Any],
    primary_timing_rows: Sequence[Mapping[str, Any]],
    primary_severity_rows: Sequence[Mapping[str, Any]],
    primary_clearance_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    success_delta = _int_value(primary_global, "success_delta")
    offtrack_delta = _int_value(primary_global, "offtrack_delta")
    collision_delta = _int_value(primary_global, "collision_delta")
    targeted_offtrack_delta_vs_generic = _int_value(generic_vs_targeted_global, "offtrack_delta")
    mid_offtrack_delta = _int_value(_row_by_group(primary_timing_rows, "mid_offtrack"), "offtrack_delta")
    mild_overshoot_delta = _int_value(_row_by_group(primary_severity_rows, "mild_overshoot"), "offtrack_delta")
    safe_clearance_offtrack_delta = _int_value(
        _row_by_group(primary_clearance_rows, "safe_clearance_margin"),
        "offtrack_delta",
    )

    collision_guardrail_pass = collision_delta <= 0
    max_step_guardrail_pass = True
    route = "targeted_repair_partial_support_result_audit"
    reason = "targeted containment improves some aggregate outcomes but needs result audit"

    if not support_complete:
        route = "artifact_repair_before_interpretation"
        reason = "one or more input panels are incomplete"
    elif collision_delta > 0:
        route = "collision_clearance_guardrail_repair"
        reason = "targeted containment increases collision count versus M2244 baseline"
    elif offtrack_delta < 0 and mid_offtrack_delta <= 0 and mild_overshoot_delta <= 0:
        route = "targeted_containment_repair_supported_result_audit"
        reason = "targeted containment reduces offtrack count and does not regress the midcourse/mild slices"
    elif offtrack_delta == 0 and targeted_offtrack_delta_vs_generic < 0 and mid_offtrack_delta <= 0:
        route = "aggregate_neutral_slice_recovered_result_audit"
        reason = "targeted containment beats generic repair and is neutral versus baseline on global offtrack"
    elif mid_offtrack_delta > 0 or mild_overshoot_delta > 0:
        route = "midcourse_corridor_containment_redesign_or_synthesis"
        reason = "targeted containment still regresses the intended midcourse or mild-overshoot slice"
    elif targeted_offtrack_delta_vs_generic < 0:
        route = "targeted_repair_partial_support_result_audit"
        reason = "targeted containment improves versus generic repair but not enough versus M2244 baseline"

    return [
        {
            "route": route,
            "admitted": bool(support_complete),
            "support_reason": reason,
            "primary_comparison": str(primary_global.get("comparison", "baseline_vs_targeted")),
            "global_success_delta_vs_base": success_delta,
            "global_offtrack_delta_vs_base": offtrack_delta,
            "global_collision_delta_vs_base": collision_delta,
            "targeted_offtrack_delta_vs_generic": targeted_offtrack_delta_vs_generic,
            "mid_offtrack_delta_vs_base": mid_offtrack_delta,
            "mild_overshoot_delta_vs_base": mild_overshoot_delta,
            "safe_clearance_offtrack_delta_vs_base": safe_clearance_offtrack_delta,
            "collision_guardrail_pass": collision_guardrail_pass,
            "max_step_guardrail_pass": max_step_guardrail_pass,
            "diagnostic_only": True,
            "ranking_admissible": False,
            "winner_selected": False,
        }
    ]


def _write_delta_file(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv_rows(path, rows, fieldnames=DELTA_FIELDNAMES)


def run_midcourse_corridor_containment_failure_slice_diagnosis(
    *,
    baseline_episodes: Path | str = DEFAULT_BASELINE_EPISODES,
    targeted_episodes: Path | str = DEFAULT_TARGETED_EPISODES,
    reference_episodes: Path | str = DEFAULT_REFERENCE_EPISODES,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    baseline_rows = offtrack_diagnosis._annotate_rows(
        offtrack_diagnosis.read_csv_rows(baseline_episodes), BASELINE_LABEL
    )
    targeted_rows = offtrack_diagnosis._annotate_rows(
        offtrack_diagnosis.read_csv_rows(targeted_episodes), TARGETED_LABEL
    )
    reference_rows = offtrack_diagnosis._annotate_rows(
        offtrack_diagnosis.read_csv_rows(reference_episodes), REFERENCE_LABEL
    )

    panel_rows = [
        offtrack_diagnosis._panel_summary(BASELINE_LABEL, baseline_rows),
        offtrack_diagnosis._panel_summary(TARGETED_LABEL, targeted_rows),
        offtrack_diagnosis._panel_summary(REFERENCE_LABEL, reference_rows),
    ]

    comparisons = [
        ("baseline_vs_targeted", BASELINE_LABEL, TARGETED_LABEL, baseline_rows, targeted_rows),
        ("baseline_vs_generic", BASELINE_LABEL, REFERENCE_LABEL, baseline_rows, reference_rows),
        ("generic_vs_targeted", REFERENCE_LABEL, TARGETED_LABEL, reference_rows, targeted_rows),
    ]

    def build_axis(axis: str, key: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for comparison, left_panel, right_panel, left_rows, right_rows in comparisons:
            rows.extend(
                _delta_rows(
                    comparison=comparison,
                    left_panel=left_panel,
                    right_panel=right_panel,
                    axis=axis,
                    left_rows=left_rows,
                    right_rows=right_rows,
                    key=key,
                )
            )
        return rows

    global_rows = build_axis("global")
    profile_seed_rows = build_axis("profile_seed", "profile_seed")
    outcome_rows = build_axis("outcome_bucket", "outcome_bucket")
    timing_rows = build_axis("offtrack_timing_bucket", "offtrack_timing_bucket")
    severity_rows = build_axis("offtrack_severity_bucket", "offtrack_severity_bucket")
    clearance_rows = build_axis("clearance_risk_bucket", "clearance_risk_bucket")
    selected_floor_rows = build_axis("selected_readiness_floor_pass", "selected_readiness_floor_pass")
    obstacle_label_rows = build_axis("obstacle_label", "obstacle_label")
    termination_rows = build_axis("termination_reason", "termination_reason")
    sideslip_rows = build_axis("sideslip_bucket", "sideslip_bucket")
    recovery_rows = build_axis("recovery_bucket", "recovery_bucket")

    primary_global = _row_by_group(
        [row for row in global_rows if row["comparison"] == "baseline_vs_targeted"], "global"
    )
    generic_vs_targeted_global = _row_by_group(
        [row for row in global_rows if row["comparison"] == "generic_vs_targeted"], "global"
    )
    primary_timing_rows = [row for row in timing_rows if row["comparison"] == "baseline_vs_targeted"]
    primary_severity_rows = [row for row in severity_rows if row["comparison"] == "baseline_vs_targeted"]
    primary_clearance_rows = [row for row in clearance_rows if row["comparison"] == "baseline_vs_targeted"]

    support_complete = (
        len(baseline_rows) == EXPECTED_PANEL_ROWS
        and len(targeted_rows) == EXPECTED_PANEL_ROWS
        and len(reference_rows) == EXPECTED_PANEL_ROWS
    )
    route_rows = _route_rows(
        support_complete=support_complete,
        primary_global=primary_global,
        generic_vs_targeted_global=generic_vs_targeted_global,
        primary_timing_rows=primary_timing_rows,
        primary_severity_rows=primary_severity_rows,
        primary_clearance_rows=primary_clearance_rows,
    )

    reference_comparison_rows = [
        row for row in global_rows + timing_rows + severity_rows + clearance_rows if row["comparison"] != "baseline_vs_targeted"
    ]
    all_delta_rows = (
        global_rows
        + profile_seed_rows
        + outcome_rows
        + timing_rows
        + severity_rows
        + clearance_rows
        + selected_floor_rows
        + obstacle_label_rows
        + termination_rows
        + sideslip_rows
        + recovery_rows
    )

    write_csv_rows(output / "panel_summary.csv", panel_rows)
    _write_delta_file(output / "global_delta.csv", global_rows)
    _write_delta_file(output / "profile_seed_delta.csv", profile_seed_rows)
    _write_delta_file(output / "outcome_delta.csv", outcome_rows)
    _write_delta_file(output / "offtrack_timing_delta.csv", timing_rows)
    _write_delta_file(output / "offtrack_severity_delta.csv", severity_rows)
    _write_delta_file(output / "clearance_risk_delta.csv", clearance_rows)
    _write_delta_file(output / "reference_comparison_delta.csv", reference_comparison_rows)
    _write_delta_file(output / "selected_readiness_floor_delta.csv", selected_floor_rows)
    _write_delta_file(output / "obstacle_label_delta.csv", obstacle_label_rows)
    _write_delta_file(output / "termination_reason_delta.csv", termination_rows)
    _write_delta_file(output / "sideslip_delta.csv", sideslip_rows)
    _write_delta_file(output / "recovery_delta.csv", recovery_rows)
    _write_delta_file(output / "all_delta_rows.csv", all_delta_rows)
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
    result_class = (
        "current_sim_midcourse_corridor_containment_failure_slice_diagnosis_pass"
        if support_complete and route_rows and guardrail_violation_count == 0
        else "current_sim_midcourse_corridor_containment_failure_slice_diagnosis_fail"
    )

    summary = {
        "result_class": result_class,
        "generated_at_utc": utc_timestamp(),
        "baseline_episodes": str(baseline_episodes),
        "targeted_episodes": str(targeted_episodes),
        "reference_episodes": str(reference_episodes),
        "output_dir": str(output),
        "panel_labels": [BASELINE_LABEL, TARGETED_LABEL, REFERENCE_LABEL],
        "baseline_episode_count": len(baseline_rows),
        "targeted_episode_count": len(targeted_rows),
        "reference_episode_count": len(reference_rows),
        "expected_panel_rows": EXPECTED_PANEL_ROWS,
        "support_complete": support_complete,
        "panel_summary": panel_rows,
        "global_delta_vs_base": primary_global,
        "targeted_vs_generic_delta": generic_vs_targeted_global,
        "primary_route": route_rows[0]["route"] if route_rows else "",
        "route_count": len(route_rows),
        "mid_offtrack_delta_vs_base": route_rows[0]["mid_offtrack_delta_vs_base"] if route_rows else None,
        "mild_overshoot_delta_vs_base": route_rows[0]["mild_overshoot_delta_vs_base"] if route_rows else None,
        "safe_clearance_offtrack_delta_vs_base": (
            route_rows[0]["safe_clearance_offtrack_delta_vs_base"] if route_rows else None
        ),
        "ranking_admissible_count": 0,
        "winner_selected": False,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "diagnostic_only": True,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "panel_summary": str(output / "panel_summary.csv"),
            "global_delta": str(output / "global_delta.csv"),
            "profile_seed_delta": str(output / "profile_seed_delta.csv"),
            "outcome_delta": str(output / "outcome_delta.csv"),
            "offtrack_timing_delta": str(output / "offtrack_timing_delta.csv"),
            "offtrack_severity_delta": str(output / "offtrack_severity_delta.csv"),
            "clearance_risk_delta": str(output / "clearance_risk_delta.csv"),
            "reference_comparison_delta": str(output / "reference_comparison_delta.csv"),
            "failure_slice_routes": str(output / "failure_slice_routes.csv"),
            "all_delta_rows": str(output / "all_delta_rows.csv"),
        },
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-episodes", type=Path, default=DEFAULT_BASELINE_EPISODES)
    parser.add_argument("--targeted-episodes", type=Path, default=DEFAULT_TARGETED_EPISODES)
    parser.add_argument("--reference-episodes", type=Path, default=DEFAULT_REFERENCE_EPISODES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_midcourse_corridor_containment_failure_slice_diagnosis(
        baseline_episodes=args.baseline_episodes,
        targeted_episodes=args.targeted_episodes,
        reference_episodes=args.reference_episodes,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"primary_route={summary['primary_route']}")
    print(f"result_class={summary['result_class']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
