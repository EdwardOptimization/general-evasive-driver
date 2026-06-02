"""Artifact-only bounded repair-plan materialization for M2401 targets."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift import paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation as source_tables
from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SOURCE_DIR = Path("runs/m2401_paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation")
DEFAULT_OUTPUT_DIR = Path("runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization")
DEFAULT_TARGET_CONSOLIDATED_ROW_COUNT = 1313
DEFAULT_NEXT_BLOCKER = "m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit"
RESULT_PASS = "current_sim_dual_axis_bounded_repair_plan_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_bounded_repair_plan_materialization_incomplete_or_fail"

PLAN_FIELDNAMES = [
    "slice_axis",
    "slice_key",
    "slice_value",
    "episode_count",
    "success_rate",
    "offtrack_rate",
    "collision_rate",
    "dominant_failure_mode",
    "source_consolidated_route",
    "source_actionability_class",
    "plan_route",
    "lever_family",
    "candidate_levers",
    "acceptance_gates",
    "stop_rules",
    "non_regression_guardrails",
    "diagnostic_only_monitoring",
    "repair_execution_allowed",
    "training_allowed",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
    "current_sim_verdict_claim_made",
]

CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]

DIAGNOSTIC_AXES = {
    "candidate_id",
    "candidate_id+pack_id",
    "candidate_id+profile_name",
    "candidate_id+role_family",
    "candidate_id+role_family+hidden_dynamics_bucket",
    "global",
    "pack_id",
    "pack_id+profile_name+role_family",
    "profile_name",
    "profile_name+role_family",
    "source_slice_axis",
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    return source_tables.read_csv_rows(path)


def _bool(value: Any, *, default: bool = False) -> bool:
    return source_tables._bool(value, default=default)


def _int(value: Any, *, default: int = 0) -> int:
    return source_tables._int(value, default=default)


def _float(value: Any, *, default: float = 0.0) -> float:
    return source_tables._float(value, default=default)


def _join(values: Sequence[str]) -> str:
    return "; ".join(value for value in values if value)


def _lever_family(row: Mapping[str, Any], *, plan_route: str) -> str:
    axis = str(row.get("slice_axis", ""))
    value = str(row.get("slice_value", ""))
    actionability = str(row.get("actionability_class", ""))
    if plan_route == "r4_mitigation_semantics_guardrail":
        return "unavoidable_mitigation_semantics"
    if plan_route == "collision_guardrail_constraint":
        return "collision_non_regression_guardrail"
    if plan_route == "diagnostic_monitoring_only":
        return "non_ranking_diagnostic_monitor"
    if axis in {"obstacle_lateral_offset_bucket", "obstacle_longitudinal_timing_bucket"}:
        return "geometry_timing_containment"
    if axis == "repair_family":
        return "offtrack_containment_repair_family"
    if "hidden_dynamics" in axis or "hidden_dynamics" in value or "slow_steer" in value or "weak_brake" in value:
        return "hidden_dynamics_actuator_response_robustness"
    if actionability.startswith("role_conditioned"):
        return "role_conditioned_containment"
    if axis in {"role_family", "scenario_family_id", "sampled_obstacle_label"}:
        return "role_semantics_containment"
    return "offtrack_containment_general"


def _candidate_levers(row: Mapping[str, Any], *, plan_route: str, lever_family: str) -> str:
    if plan_route == "diagnostic_monitoring_only":
        return "none; monitor only; do not rank or tune from this row"
    if plan_route == "r4_mitigation_semantics_guardrail":
        return _join(
            [
                "separate unavoidable-mitigation metric",
                "impact-speed and collision-severity guardrail",
                "do not treat R4 as ordinary avoidable offtrack repair",
            ]
        )
    if plan_route == "collision_guardrail_constraint":
        return _join(
            [
                "collision-rate non-regression gate",
                "clearance-margin tail guardrail",
                "reject offtrack repair that increases collision on this slice",
            ]
        )
    if lever_family == "geometry_timing_containment":
        return _join(
            [
                "road-boundary margin reward audit",
                "commitment timing and recovery-window audit",
                "offtrack terminal threshold audit",
            ]
        )
    if lever_family == "hidden_dynamics_actuator_response_robustness":
        return _join(
            [
                "actuator-delay and weak-brake response guardrail",
                "offtrack containment under hidden-dynamics buckets",
                "no hidden or oracle actor input",
            ]
        )
    if lever_family == "offtrack_containment_repair_family":
        return _join(
            [
                "offtrack-containment objective calibration",
                "road-departure terminal-margin gate",
                "collision and R4 non-regression guardrails",
            ]
        )
    return _join(
        [
            "offtrack-containment objective calibration",
            "role-conditioned road-boundary non-regression gate",
            "closed-loop measured-panel audit before any promotion",
        ]
    )


def _acceptance_gates(row: Mapping[str, Any], *, plan_route: str) -> str:
    if plan_route == "diagnostic_monitoring_only":
        return "diagnostic row remains non-ranking; no winner selection; no profile tuning"
    if plan_route == "r4_mitigation_semantics_guardrail":
        return "R4 collision-severity and mitigation semantics do not regress; no ordinary-avoidance success claim"
    if plan_route == "collision_guardrail_constraint":
        return "collision rate and clearance-tail do not regress on this guardrail slice"
    gates = [
        "target-slice offtrack rate decreases or terminal road-margin tail improves",
        "collision guardrails do not regress",
        "R4 mitigation semantics do not regress",
        "actor input contract unchanged",
    ]
    if _bool(row.get("collision_guardrail_required")):
        gates.append("paired collision guardrail for this same row passes")
    return _join(gates)


def _stop_rules(row: Mapping[str, Any], *, plan_route: str) -> str:
    common = [
        "stop if repair requires candidate/profile ranking",
        "stop if actor input contract would change",
        "stop if hidden/oracle features are needed",
    ]
    if plan_route == "diagnostic_monitoring_only":
        return _join(["stop if diagnostic row is converted into a repair target", *common])
    if plan_route == "r4_mitigation_semantics_guardrail":
        return _join(["stop if R4 is scored as ordinary avoidable success", *common])
    if plan_route == "collision_guardrail_constraint":
        return _join(["stop if collision rate increases while offtrack improves", *common])
    return _join(["stop if offtrack improves only by increasing collision or degrading R4", *common])


def _non_regression_guardrails(row: Mapping[str, Any], *, plan_route: str) -> str:
    if plan_route == "diagnostic_monitoring_only":
        return "non-ranking diagnostic boundary"
    if plan_route == "r4_mitigation_semantics_guardrail":
        return "R4 mitigation semantics; impact severity; collision rate"
    if plan_route == "collision_guardrail_constraint":
        return "collision rate; clearance margin tail; no collision-heavy regression"
    guardrails = ["collision guardrails", "R4 mitigation semantics", "no input contract change"]
    if _bool(row.get("collision_guardrail_required")):
        guardrails.append("same-row collision guardrail")
    return _join(guardrails)


def _plan_route(row: Mapping[str, Any]) -> str:
    route = str(row.get("consolidated_route", ""))
    if route == "r4_mitigation_semantics":
        return "r4_mitigation_semantics_guardrail"
    if route == "collision_guardrail":
        return "collision_guardrail_constraint"
    if route == "offtrack_repair_target_with_collision_guardrail":
        return "offtrack_repair_plan_with_collision_guardrail"
    if route == "offtrack_repair_target":
        return "offtrack_repair_plan"
    return "diagnostic_monitoring_only"


def materialize_plan_row(row: Mapping[str, Any]) -> dict[str, Any]:
    plan_route = _plan_route(row)
    lever_family = _lever_family(row, plan_route=plan_route)
    diagnostic = plan_route == "diagnostic_monitoring_only"
    return {
        "slice_axis": str(row.get("slice_axis", "")),
        "slice_key": str(row.get("slice_key", "")),
        "slice_value": str(row.get("slice_value", "")),
        "episode_count": _int(row.get("episode_count")),
        "success_rate": _float(row.get("success_rate")),
        "offtrack_rate": _float(row.get("offtrack_rate")),
        "collision_rate": _float(row.get("collision_rate")),
        "dominant_failure_mode": str(row.get("dominant_failure_mode", "")),
        "source_consolidated_route": str(row.get("consolidated_route", "")),
        "source_actionability_class": str(row.get("actionability_class", "")),
        "plan_route": plan_route,
        "lever_family": lever_family,
        "candidate_levers": _candidate_levers(row, plan_route=plan_route, lever_family=lever_family),
        "acceptance_gates": _acceptance_gates(row, plan_route=plan_route),
        "stop_rules": _stop_rules(row, plan_route=plan_route),
        "non_regression_guardrails": _non_regression_guardrails(row, plan_route=plan_route),
        "diagnostic_only_monitoring": diagnostic,
        "repair_execution_allowed": False,
        "training_allowed": False,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }


def materialize_plan_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    plan_rows = [materialize_plan_row(row) for row in rows]
    return sorted(
        plan_rows,
        key=lambda row: (
            row["plan_route"],
            row["lever_family"],
            -float(row["episode_count"]),
            row["slice_axis"],
            row["slice_value"],
        ),
    )


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_bounded_repair_plan_materialization",
            "admissible": True,
            "reason": "M2404 may claim only bounded repair-plan artifact materialization from M2401 targets",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2404 names levers and gates but does not execute repair",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2404 does not modify or execute scenarios",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2404 does not train, replay, or run PPO",
        },
        {
            "claim": "effective_candidate_ranking",
            "admissible": False,
            "reason": "candidate/profile/pack diagnostics remain non-ranking",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2404 does not run the fair controller matrix",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2404 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2404 is planning infrastructure, not a current-sim verdict",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_bounded_repair_plan_materialization(
    *,
    source_dir: Path | str = DEFAULT_SOURCE_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_consolidated_row_count: int = DEFAULT_TARGET_CONSOLIDATED_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source = Path(source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    summary_path = source / "summary.json"
    consolidated_path = source / "consolidated_rows.csv"
    source_summary = read_json(summary_path)
    source_rows = read_csv_rows(consolidated_path)
    plan_rows = materialize_plan_rows(source_rows)

    offtrack_rows = [row for row in plan_rows if str(row.get("plan_route", "")).startswith("offtrack_repair_plan")]
    collision_rows = [
        row
        for row in plan_rows
        if str(row.get("plan_route", "")) == "collision_guardrail_constraint"
        or str(row.get("plan_route", "")) == "offtrack_repair_plan_with_collision_guardrail"
    ]
    r4_rows = [row for row in plan_rows if str(row.get("plan_route", "")) == "r4_mitigation_semantics_guardrail"]
    diagnostic_rows = [row for row in plan_rows if _bool(row.get("diagnostic_only_monitoring"))]

    diagnostic_axis_repair_plan_count = sum(
        1
        for row in plan_rows
        if str(row.get("slice_axis", "")) in DIAGNOSTIC_AXES and str(row.get("plan_route", "")).startswith("offtrack_repair_plan")
    )
    r4_ordinary_repair_plan_count = sum(
        1
        for row in plan_rows
        if str(row.get("source_consolidated_route", "")) == "r4_mitigation_semantics"
        and str(row.get("plan_route", "")).startswith("offtrack_repair_plan")
    )
    collision_guardrail_as_plain_repair_count = sum(
        1
        for row in plan_rows
        if str(row.get("source_consolidated_route", "")) == "collision_guardrail"
        and str(row.get("plan_route", "")).startswith("offtrack_repair_plan")
    )
    repair_execution_allowed_count = _flag_count(plan_rows, "repair_execution_allowed")
    training_allowed_count = _flag_count(plan_rows, "training_allowed")
    ranking_admissible_count = _flag_count(plan_rows, "ranking_admissible")
    winner_selected_count = _flag_count(plan_rows, "winner_selected")

    guardrail_flags = {
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "effective_candidate_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    source_consolidated_row_count = len(source_rows)
    passes = (
        source_consolidated_row_count == int(target_consolidated_row_count)
        and str(source_summary.get("result_class", "")).endswith("_pass")
        and len(plan_rows) == source_consolidated_row_count
        and len(offtrack_rows) == _int(source_summary.get("offtrack_repair_target_row_count"))
        and len(collision_rows) == _int(source_summary.get("collision_guardrail_row_count"))
        and len(r4_rows) == _int(source_summary.get("r4_mitigation_semantics_row_count"))
        and len(diagnostic_rows) > 0
        and diagnostic_axis_repair_plan_count == 0
        and r4_ordinary_repair_plan_count == 0
        and collision_guardrail_as_plain_repair_count == 0
        and repair_execution_allowed_count == 0
        and training_allowed_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "repair_plan_rows.csv", plan_rows, fieldnames=PLAN_FIELDNAMES)
    write_csv_rows(output / "offtrack_repair_plan_rows.csv", offtrack_rows, fieldnames=PLAN_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_plan_rows.csv", collision_rows, fieldnames=PLAN_FIELDNAMES)
    write_csv_rows(output / "r4_mitigation_plan_rows.csv", r4_rows, fieldnames=PLAN_FIELDNAMES)
    write_csv_rows(output / "diagnostic_monitoring_rows.csv", diagnostic_rows, fieldnames=PLAN_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_dir": str(source),
        "source_summary": str(summary_path),
        "source_consolidated_rows": str(consolidated_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_consolidated_row_count": source_consolidated_row_count,
        "target_consolidated_row_count": int(target_consolidated_row_count),
        "repair_plan_row_count": len(plan_rows),
        "offtrack_repair_plan_row_count": len(offtrack_rows),
        "collision_guardrail_plan_row_count": len(collision_rows),
        "r4_mitigation_plan_row_count": len(r4_rows),
        "diagnostic_monitoring_row_count": len(diagnostic_rows),
        "plan_route_counts": _count_by(plan_rows, "plan_route"),
        "lever_family_counts": _count_by(plan_rows, "lever_family"),
        "diagnostic_axis_repair_plan_count": diagnostic_axis_repair_plan_count,
        "r4_ordinary_repair_plan_count": r4_ordinary_repair_plan_count,
        "collision_guardrail_as_plain_repair_count": collision_guardrail_as_plain_repair_count,
        "repair_execution_allowed_count": repair_execution_allowed_count,
        "training_allowed_count": training_allowed_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "top_offtrack_repair_plan_rows": offtrack_rows[:10],
        "top_collision_guardrail_plan_rows": collision_rows[:10],
        "top_r4_mitigation_plan_rows": r4_rows[:10],
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "repair_execution_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "effective_candidate_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repair_plan_rows": str(output / "repair_plan_rows.csv"),
            "offtrack_repair_plan_rows": str(output / "offtrack_repair_plan_rows.csv"),
            "collision_guardrail_plan_rows": str(output / "collision_guardrail_plan_rows.csv"),
            "r4_mitigation_plan_rows": str(output / "r4_mitigation_plan_rows.csv"),
            "diagnostic_monitoring_rows": str(output / "diagnostic_monitoring_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-consolidated-row-count", type=int, default=DEFAULT_TARGET_CONSOLIDATED_ROW_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_bounded_repair_plan_materialization(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        target_consolidated_row_count=int(args.target_consolidated_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_consolidated_row_count={summary['source_consolidated_row_count']}")
    print(f"repair_plan_row_count={summary['repair_plan_row_count']}")
    print(f"offtrack_repair_plan_row_count={summary['offtrack_repair_plan_row_count']}")
    print(f"collision_guardrail_plan_row_count={summary['collision_guardrail_plan_row_count']}")
    print(f"r4_mitigation_plan_row_count={summary['r4_mitigation_plan_row_count']}")
    print(f"diagnostic_monitoring_row_count={summary['diagnostic_monitoring_row_count']}")
    print(f"repair_execution_allowed_count={summary['repair_execution_allowed_count']}")
    print(f"ranking_admissible_count={summary['ranking_admissible_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
