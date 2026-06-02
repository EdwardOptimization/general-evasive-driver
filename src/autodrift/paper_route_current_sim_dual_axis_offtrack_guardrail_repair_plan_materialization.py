"""Artifact-only offtrack/guardrail repair-plan materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json")
DEFAULT_REPAIR_SPEC_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/repair_spec_rows.csv"
)
DEFAULT_ORDINARY_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/ordinary_offtrack_repair_spec_rows.csv"
)
DEFAULT_MIXED_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/mixed_guarded_repair_spec_rows.csv"
)
DEFAULT_COLLISION_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/collision_guardrail_spec_rows.csv"
)
DEFAULT_R4_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/r4_guardrail_spec_rows.csv"
)
DEFAULT_DIAGNOSTIC_ROWS = Path(
    "runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/diagnostic_guardrail_spec_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization")
DEFAULT_TARGET_REPAIR_SPEC_ROW_COUNT = 320
DEFAULT_TARGET_ORDINARY_ROW_COUNT = 36
DEFAULT_TARGET_MIXED_ROW_COUNT = 18
DEFAULT_TARGET_COLLISION_ROW_COUNT = 28
DEFAULT_TARGET_R4_ROW_COUNT = 48
DEFAULT_TARGET_DIAGNOSTIC_ROW_COUNT = 190
RESULT_PASS = "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_incomplete_or_fail"
DEFAULT_NEXT_BLOCKER = "m2376-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization-result-audit"

REWARD_DELTA_FIELDNAMES = [
    "plan_row_id",
    "repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "priority_tier",
    "target_metric",
    "guardrail_metric",
    "offtrack_margin_reward_delta",
    "recovery_window_reward_delta",
    "boundary_overshoot_penalty_delta",
    "collision_guardrail_required",
    "active_config_overwritten",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
CURRICULUM_FIELDNAMES = [
    "plan_row_id",
    "repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "priority_tier",
    "sampling_weight_multiplier",
    "collision_guardrail_required",
    "profile_specific_tuning",
    "active_config_overwritten",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
GUARDRAIL_FIELDNAMES = [
    "constraint_id",
    "repair_spec_id",
    "repair_family",
    "source_group",
    "source_slice_axis",
    "source_slice_value",
    "constraint_family",
    "constraint_metric",
    "required",
    "active_config_overwritten",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
    "paper_level_claim_made",
    "finite_window_vs_gru_conclusion_made",
    "level3_self_id_claim_made",
    "scenario_redesign_executed_claim_made",
    "training_repair_success_claim_made",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]

DIRECT_REPAIR_FAMILIES = {
    "priority_offtrack_containment_repair",
    "offtrack_containment_repair",
    "guarded_offtrack_containment_repair",
}
ORDINARY_REPAIR_FAMILIES = {
    "priority_offtrack_containment_repair",
    "offtrack_containment_repair",
}
COLLISION_GUARDRAIL_FAMILIES = {
    "guarded_offtrack_containment_repair",
    "collision_guardrail_constraint",
}


def read_csv_rows(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n", "", "none", "nan"}:
        return False
    return default


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _reward_delta_for(row: Mapping[str, Any]) -> tuple[float, float, float]:
    family = str(row.get("repair_family", ""))
    priority = str(row.get("priority_tier", ""))
    if family == "priority_offtrack_containment_repair" or priority == "P0":
        return (0.15, 0.10, 0.08)
    if family == "guarded_offtrack_containment_repair":
        return (0.08, 0.06, 0.04)
    return (0.10, 0.07, 0.05)


def _curriculum_weight_for(row: Mapping[str, Any]) -> float:
    family = str(row.get("repair_family", ""))
    priority = str(row.get("priority_tier", ""))
    if family == "guarded_offtrack_containment_repair":
        return 1.25
    if priority == "P0":
        return 2.0
    return 1.5


def build_reward_delta_rows(spec_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        spec for spec in spec_rows if str(spec.get("repair_family", "")) in DIRECT_REPAIR_FAMILIES
    ):
        margin_delta, recovery_delta, overshoot_delta = _reward_delta_for(row)
        rows.append(
            {
                "plan_row_id": f"reward_delta_{index:04d}",
                "repair_spec_id": str(row.get("repair_spec_id", "")),
                "repair_family": str(row.get("repair_family", "")),
                "source_slice_axis": str(row.get("source_slice_axis", "")),
                "source_slice_value": str(row.get("source_slice_value", "")),
                "priority_tier": str(row.get("priority_tier", "")),
                "target_metric": str(row.get("target_metric", "")),
                "guardrail_metric": str(row.get("guardrail_metric", "")),
                "offtrack_margin_reward_delta": margin_delta,
                "recovery_window_reward_delta": recovery_delta,
                "boundary_overshoot_penalty_delta": overshoot_delta,
                "collision_guardrail_required": _bool(row.get("collision_guardrail_required")),
                "active_config_overwritten": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return rows


def build_curriculum_weight_rows(spec_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(
        spec for spec in spec_rows if str(spec.get("repair_family", "")) in DIRECT_REPAIR_FAMILIES
    ):
        rows.append(
            {
                "plan_row_id": f"curriculum_weight_{index:04d}",
                "repair_spec_id": str(row.get("repair_spec_id", "")),
                "repair_family": str(row.get("repair_family", "")),
                "source_slice_axis": str(row.get("source_slice_axis", "")),
                "source_slice_value": str(row.get("source_slice_value", "")),
                "priority_tier": str(row.get("priority_tier", "")),
                "sampling_weight_multiplier": _curriculum_weight_for(row),
                "collision_guardrail_required": _bool(row.get("collision_guardrail_required")),
                "profile_specific_tuning": False,
                "active_config_overwritten": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return rows


def _constraint_for(row: Mapping[str, Any]) -> tuple[str, str] | None:
    family = str(row.get("repair_family", ""))
    if family in COLLISION_GUARDRAIL_FAMILIES:
        return ("collision", "collision_rate_not_worse")
    if family == "r4_mitigation_semantics_guardrail":
        return ("r4_mitigation_semantics", "mitigation_semantics_preserved")
    if family == "diagnostic_no_ranking_guardrail":
        return ("diagnostic_no_ranking", "no_ranking_no_winner_claims")
    return None


def build_guardrail_constraint_rows(spec_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(spec for spec in spec_rows if _constraint_for(spec) is not None):
        constraint_family, metric = _constraint_for(row) or ("unknown", "unknown")
        rows.append(
            {
                "constraint_id": f"guardrail_constraint_{index:04d}",
                "repair_spec_id": str(row.get("repair_spec_id", "")),
                "repair_family": str(row.get("repair_family", "")),
                "source_group": str(row.get("source_group", "")),
                "source_slice_axis": str(row.get("source_slice_axis", "")),
                "source_slice_value": str(row.get("source_slice_value", "")),
                "constraint_family": constraint_family,
                "constraint_metric": metric,
                "required": True,
                "active_config_overwritten": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "finite_window_vs_gru_conclusion_made": False,
                "level3_self_id_claim_made": False,
                "scenario_redesign_executed_claim_made": False,
                "training_repair_success_claim_made": False,
            }
        )
    return rows


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_repair_plan_materialization",
            "admissible": True,
            "reason": "M2375 may claim only repair-plan artifact materialization",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2375 writes plan artifacts but does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2375 does not train or evaluate a repaired driver",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2375 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "repair plans do not rank controller families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "repair plans do not rank support policies",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2375 is artifact materialization, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2375 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2375 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2375 does not run validation needed for a current-sim verdict",
        },
    ]


def run_repair_plan_materialization(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    repair_spec_rows_path: Path | str = DEFAULT_REPAIR_SPEC_ROWS,
    ordinary_rows_path: Path | str = DEFAULT_ORDINARY_ROWS,
    mixed_rows_path: Path | str = DEFAULT_MIXED_ROWS,
    collision_rows_path: Path | str = DEFAULT_COLLISION_ROWS,
    r4_rows_path: Path | str = DEFAULT_R4_ROWS,
    diagnostic_rows_path: Path | str = DEFAULT_DIAGNOSTIC_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_repair_spec_row_count: int = DEFAULT_TARGET_REPAIR_SPEC_ROW_COUNT,
    target_ordinary_row_count: int = DEFAULT_TARGET_ORDINARY_ROW_COUNT,
    target_mixed_row_count: int = DEFAULT_TARGET_MIXED_ROW_COUNT,
    target_collision_row_count: int = DEFAULT_TARGET_COLLISION_ROW_COUNT,
    target_r4_row_count: int = DEFAULT_TARGET_R4_ROW_COUNT,
    target_diagnostic_row_count: int = DEFAULT_TARGET_DIAGNOSTIC_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    repair_spec_rows = read_csv_rows(repair_spec_rows_path)
    ordinary_rows = read_csv_rows(ordinary_rows_path)
    mixed_rows = read_csv_rows(mixed_rows_path)
    collision_rows = read_csv_rows(collision_rows_path)
    r4_rows = read_csv_rows(r4_rows_path)
    diagnostic_rows = read_csv_rows(diagnostic_rows_path)

    reward_delta_rows = build_reward_delta_rows(repair_spec_rows)
    curriculum_weight_rows = build_curriculum_weight_rows(repair_spec_rows)
    guardrail_constraint_rows = build_guardrail_constraint_rows(repair_spec_rows)
    mixed_guarded_constraint_rows = [
        row for row in guardrail_constraint_rows if row["repair_family"] == "guarded_offtrack_containment_repair"
    ]
    claim_rows = claim_boundary_rows()

    plan = {
        "result_class": RESULT_PASS,
        "source_summary": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_counts": {
            "repair_spec_rows": len(repair_spec_rows),
            "ordinary_offtrack_rows": len(ordinary_rows),
            "mixed_guarded_rows": len(mixed_rows),
            "collision_guardrail_rows": len(collision_rows),
            "r4_guardrail_rows": len(r4_rows),
            "diagnostic_guardrail_rows": len(diagnostic_rows),
        },
        "output_families": {
            "reward_delta_rows": "reward_delta_rows.csv",
            "curriculum_weight_rows": "curriculum_weight_rows.csv",
            "guardrail_constraint_rows": "guardrail_constraint_rows.csv",
            "mixed_guarded_constraint_rows": "mixed_guarded_constraint_rows.csv",
            "claim_boundary": "claim_boundary.csv",
        },
        "allowed_levers": [
            "offtrack_margin_reward",
            "recovery_window_reward",
            "boundary_overshoot_penalty",
            "curriculum_sampling_weight",
            "collision_guardrail_weight",
            "r4_mitigation_metric_guard",
        ],
        "blocked_levers": [
            "actor_input_change",
            "hidden_oracle_feature_injection",
            "profile_specific_tuning",
            "support_policy_ranking",
            "controller_family_ranking",
            "winner_selection",
            "active_scenario_config_overwrite",
            "r4_ordinary_avoidance_repair",
            "collision_blind_offtrack_objective",
            "scenario_redesign_executed_claim",
            "training_repair_success_claim",
        ],
    }

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
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    profile_specific_tuning_count = _flag_count(curriculum_weight_rows, "profile_specific_tuning")
    actor_input_change_count = int(guardrail_flags["actor_input_contract_changed"])
    hidden_oracle_feature_injection_count = int(guardrail_flags["hidden_oracle_feature_injection"])
    collision_blind_mixed_repair_count = sum(
        1
        for row in mixed_guarded_constraint_rows
        if str(row.get("constraint_family")) != "collision"
        or str(row.get("constraint_metric")) != "collision_rate_not_worse"
    )
    r4_ordinary_repair_count = sum(
        1
        for row in r4_rows
        if str(row.get("repair_family")) in ORDINARY_REPAIR_FAMILIES
        or str(row.get("target_metric")) == "offtrack_rate_down"
    )
    ranking_admissible_count = _flag_count(repair_spec_rows, "ranking_admissible")
    winner_selected_count = _flag_count(repair_spec_rows, "winner_selected")
    target_guardrail_constraint_min_count = (
        int(target_collision_row_count) + int(target_r4_row_count) + int(target_diagnostic_row_count)
    )

    passes = (
        len(repair_spec_rows) == int(target_repair_spec_row_count)
        and len(ordinary_rows) == int(target_ordinary_row_count)
        and len(mixed_rows) == int(target_mixed_row_count)
        and len(collision_rows) == int(target_collision_row_count)
        and len(r4_rows) == int(target_r4_row_count)
        and len(diagnostic_rows) == int(target_diagnostic_row_count)
        and len(reward_delta_rows) > 0
        and len(curriculum_weight_rows) > 0
        and len(guardrail_constraint_rows) >= target_guardrail_constraint_min_count
        and len(mixed_guarded_constraint_rows) == len(mixed_rows)
        and profile_specific_tuning_count == 0
        and actor_input_change_count == 0
        and hidden_oracle_feature_injection_count == 0
        and collision_blind_mixed_repair_count == 0
        and r4_ordinary_repair_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    write_json(output / "repair_implementation_plan.json", plan)
    write_csv_rows(output / "reward_delta_rows.csv", reward_delta_rows, fieldnames=REWARD_DELTA_FIELDNAMES)
    write_csv_rows(output / "curriculum_weight_rows.csv", curriculum_weight_rows, fieldnames=CURRICULUM_FIELDNAMES)
    write_csv_rows(output / "guardrail_constraint_rows.csv", guardrail_constraint_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(
        output / "mixed_guarded_constraint_rows.csv",
        mixed_guarded_constraint_rows,
        fieldnames=GUARDRAIL_FIELDNAMES,
    )
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "input_repair_spec_row_count": len(repair_spec_rows),
        "target_repair_spec_row_count": int(target_repair_spec_row_count),
        "ordinary_offtrack_source_count": len(ordinary_rows),
        "target_ordinary_offtrack_source_count": int(target_ordinary_row_count),
        "mixed_guarded_source_count": len(mixed_rows),
        "target_mixed_guarded_source_count": int(target_mixed_row_count),
        "collision_guardrail_source_count": len(collision_rows),
        "target_collision_guardrail_source_count": int(target_collision_row_count),
        "r4_guardrail_source_count": len(r4_rows),
        "target_r4_guardrail_source_count": int(target_r4_row_count),
        "diagnostic_guardrail_source_count": len(diagnostic_rows),
        "target_diagnostic_guardrail_source_count": int(target_diagnostic_row_count),
        "reward_delta_row_count": len(reward_delta_rows),
        "curriculum_weight_row_count": len(curriculum_weight_rows),
        "guardrail_constraint_row_count": len(guardrail_constraint_rows),
        "target_guardrail_constraint_min_count": target_guardrail_constraint_min_count,
        "mixed_guarded_constraint_row_count": len(mixed_guarded_constraint_rows),
        "claim_boundary_row_count": len(claim_rows),
        "repair_family_counts": _count_by(repair_spec_rows, "repair_family"),
        "constraint_family_counts": _count_by(guardrail_constraint_rows, "constraint_family"),
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "actor_input_change_count": actor_input_change_count,
        "hidden_oracle_feature_injection_count": hidden_oracle_feature_injection_count,
        "collision_blind_mixed_repair_count": collision_blind_mixed_repair_count,
        "r4_ordinary_repair_count": r4_ordinary_repair_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
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
        "active_config_overwritten": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repair_implementation_plan": str(output / "repair_implementation_plan.json"),
            "reward_delta_rows": str(output / "reward_delta_rows.csv"),
            "curriculum_weight_rows": str(output / "curriculum_weight_rows.csv"),
            "guardrail_constraint_rows": str(output / "guardrail_constraint_rows.csv"),
            "mixed_guarded_constraint_rows": str(output / "mixed_guarded_constraint_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--repair-spec-rows", type=Path, default=DEFAULT_REPAIR_SPEC_ROWS)
    parser.add_argument("--ordinary-rows", type=Path, default=DEFAULT_ORDINARY_ROWS)
    parser.add_argument("--mixed-rows", type=Path, default=DEFAULT_MIXED_ROWS)
    parser.add_argument("--collision-rows", type=Path, default=DEFAULT_COLLISION_ROWS)
    parser.add_argument("--r4-rows", type=Path, default=DEFAULT_R4_ROWS)
    parser.add_argument("--diagnostic-rows", type=Path, default=DEFAULT_DIAGNOSTIC_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-repair-spec-row-count", type=int, default=DEFAULT_TARGET_REPAIR_SPEC_ROW_COUNT)
    parser.add_argument("--target-ordinary-row-count", type=int, default=DEFAULT_TARGET_ORDINARY_ROW_COUNT)
    parser.add_argument("--target-mixed-row-count", type=int, default=DEFAULT_TARGET_MIXED_ROW_COUNT)
    parser.add_argument("--target-collision-row-count", type=int, default=DEFAULT_TARGET_COLLISION_ROW_COUNT)
    parser.add_argument("--target-r4-row-count", type=int, default=DEFAULT_TARGET_R4_ROW_COUNT)
    parser.add_argument("--target-diagnostic-row-count", type=int, default=DEFAULT_TARGET_DIAGNOSTIC_ROW_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_repair_plan_materialization(
        summary_path=args.summary,
        repair_spec_rows_path=args.repair_spec_rows,
        ordinary_rows_path=args.ordinary_rows,
        mixed_rows_path=args.mixed_rows,
        collision_rows_path=args.collision_rows,
        r4_rows_path=args.r4_rows,
        diagnostic_rows_path=args.diagnostic_rows,
        output_dir=args.output_dir,
        target_repair_spec_row_count=int(args.target_repair_spec_row_count),
        target_ordinary_row_count=int(args.target_ordinary_row_count),
        target_mixed_row_count=int(args.target_mixed_row_count),
        target_collision_row_count=int(args.target_collision_row_count),
        target_r4_row_count=int(args.target_r4_row_count),
        target_diagnostic_row_count=int(args.target_diagnostic_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"input_repair_spec_row_count={summary['input_repair_spec_row_count']}")
    print(f"ordinary_offtrack_source_count={summary['ordinary_offtrack_source_count']}")
    print(f"mixed_guarded_source_count={summary['mixed_guarded_source_count']}")
    print(f"collision_guardrail_source_count={summary['collision_guardrail_source_count']}")
    print(f"r4_guardrail_source_count={summary['r4_guardrail_source_count']}")
    print(f"diagnostic_guardrail_source_count={summary['diagnostic_guardrail_source_count']}")
    print(f"reward_delta_row_count={summary['reward_delta_row_count']}")
    print(f"curriculum_weight_row_count={summary['curriculum_weight_row_count']}")
    print(f"guardrail_constraint_row_count={summary['guardrail_constraint_row_count']}")
    print(f"mixed_guarded_constraint_row_count={summary['mixed_guarded_constraint_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
