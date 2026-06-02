"""Artifact-only offtrack/guardrail repair-spec materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json")
DEFAULT_OFFTRACK_TARGET_ROWS = Path(
    "runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv"
)
DEFAULT_COLLISION_GUARDRAIL_ROWS = Path(
    "runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv"
)
DEFAULT_R4_ROWS = Path(
    "runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv"
)
DEFAULT_DIAGNOSTIC_GUARDRAIL_ROWS = Path(
    "runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization")
DEFAULT_TARGET_OFFTRACK_ROW_COUNT = 54
DEFAULT_TARGET_COLLISION_GUARDRAIL_ROW_COUNT = 28
DEFAULT_TARGET_R4_ROW_COUNT = 48
DEFAULT_TARGET_DIAGNOSTIC_GUARDRAIL_ROW_COUNT = 190
RESULT_PASS = "current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization_incomplete_or_fail"
DEFAULT_NEXT_BLOCKER = "m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit"

DIAGNOSTIC_AXES = {
    "global",
    "pack_id",
    "profile_name",
    "sampling_repair_class",
    "pack_id+role_family",
    "profile_name+role_family",
    "pack_id+profile_name+role_family",
}
REPAIR_SPEC_FIELDNAMES = [
    "repair_spec_id",
    "source_group",
    "source_slice_axis",
    "source_slice_value",
    "source_consolidated_route",
    "actionability_class",
    "repair_family",
    "priority_tier",
    "target_metric",
    "guardrail_metric",
    "allowed_repair_levers",
    "blocked_levers",
    "collision_guardrail_required",
    "r4_mitigation_semantics",
    "diagnostic_no_ranking_guardrail",
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
OFFTRACK_LEVERS = [
    "offtrack_margin_reward",
    "recovery_window_reward",
    "boundary_overshoot_penalty",
    "curriculum_sampling_weight",
]
GUARDED_LEVERS = [*OFFTRACK_LEVERS, "collision_guardrail_weight"]
COLLISION_GUARDRAIL_LEVERS = ["collision_guardrail_weight", "collision_rate_not_worse_check"]
R4_LEVERS = ["r4_mitigation_metric_guard"]
DIAGNOSTIC_LEVERS = ["no_ranking_no_winner_check"]
BLOCKED_LEVERS = [
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "profile_specific_tuning",
    "winner_selection",
    "r4_ordinary_avoidance_repair",
    "collision_blind_offtrack_objective",
    "scenario_redesign_executed_claim",
    "training_repair_success_claim",
]


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


def _join(values: Sequence[str]) -> str:
    return "|".join(values)


def _repair_spec_id(source_group: str, index: int, row: Mapping[str, Any]) -> str:
    axis = str(row.get("slice_axis", "")).replace("+", "_").replace(" ", "_")
    value = str(row.get("slice_value", "")).replace("|", "__").replace(" ", "_")
    return f"{source_group}_{index:04d}_{axis}_{value}"


def _offtrack_spec(row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    collision_guardrail = _bool(row.get("collision_guardrail_required"))
    high_priority = _bool(row.get("is_high_priority_offtrack"))
    if collision_guardrail:
        family = "guarded_offtrack_containment_repair"
        levers = GUARDED_LEVERS
        priority = "P0" if high_priority else "P1"
        guardrail_metric = "collision_rate_not_worse"
    elif high_priority:
        family = "priority_offtrack_containment_repair"
        levers = OFFTRACK_LEVERS
        priority = "P0"
        guardrail_metric = "collision_rate_monitor"
    else:
        family = "offtrack_containment_repair"
        levers = OFFTRACK_LEVERS
        priority = "P1"
        guardrail_metric = "collision_rate_monitor"
    return _base_spec(
        row,
        source_group="offtrack_target",
        index=index,
        repair_family=family,
        priority_tier=priority,
        target_metric="offtrack_rate_down",
        guardrail_metric=guardrail_metric,
        allowed_repair_levers=levers,
        collision_guardrail_required=collision_guardrail,
    )


def _collision_spec(row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    return _base_spec(
        row,
        source_group="collision_guardrail",
        index=index,
        repair_family="collision_guardrail_constraint",
        priority_tier="G0",
        target_metric="not_applicable_guardrail_only",
        guardrail_metric="collision_rate_not_worse",
        allowed_repair_levers=COLLISION_GUARDRAIL_LEVERS,
        collision_guardrail_required=True,
    )


def _r4_spec(row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    return _base_spec(
        row,
        source_group="r4_mitigation",
        index=index,
        repair_family="r4_mitigation_semantics_guardrail",
        priority_tier="R4",
        target_metric="mitigation_semantics_preserved",
        guardrail_metric="r4_not_ordinary_avoidance",
        allowed_repair_levers=R4_LEVERS,
        collision_guardrail_required=False,
        r4_mitigation_semantics=True,
    )


def _diagnostic_spec(row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    return _base_spec(
        row,
        source_group="diagnostic_guardrail",
        index=index,
        repair_family="diagnostic_no_ranking_guardrail",
        priority_tier="D0",
        target_metric="not_applicable_diagnostic_only",
        guardrail_metric="no_ranking_no_winner_claims",
        allowed_repair_levers=DIAGNOSTIC_LEVERS,
        collision_guardrail_required=False,
        diagnostic_no_ranking_guardrail=True,
    )


def _base_spec(
    row: Mapping[str, Any],
    *,
    source_group: str,
    index: int,
    repair_family: str,
    priority_tier: str,
    target_metric: str,
    guardrail_metric: str,
    allowed_repair_levers: Sequence[str],
    collision_guardrail_required: bool,
    r4_mitigation_semantics: bool = False,
    diagnostic_no_ranking_guardrail: bool = False,
) -> dict[str, Any]:
    return {
        "repair_spec_id": _repair_spec_id(source_group, index, row),
        "source_group": source_group,
        "source_slice_axis": str(row.get("slice_axis", "")),
        "source_slice_value": str(row.get("slice_value", "")),
        "source_consolidated_route": str(row.get("consolidated_route", "")),
        "actionability_class": str(row.get("actionability_class", "")),
        "repair_family": repair_family,
        "priority_tier": priority_tier,
        "target_metric": target_metric,
        "guardrail_metric": guardrail_metric,
        "allowed_repair_levers": _join(list(allowed_repair_levers)),
        "blocked_levers": _join(BLOCKED_LEVERS),
        "collision_guardrail_required": bool(collision_guardrail_required),
        "r4_mitigation_semantics": bool(r4_mitigation_semantics),
        "diagnostic_no_ranking_guardrail": bool(diagnostic_no_ranking_guardrail),
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


def build_repair_specs(
    *,
    offtrack_rows: Sequence[Mapping[str, Any]],
    collision_rows: Sequence[Mapping[str, Any]],
    r4_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    specs.extend(_offtrack_spec(row, index=index) for index, row in enumerate(offtrack_rows))
    specs.extend(_collision_spec(row, index=index) for index, row in enumerate(collision_rows))
    specs.extend(_r4_spec(row, index=index) for index, row in enumerate(r4_rows))
    specs.extend(_diagnostic_spec(row, index=index) for index, row in enumerate(diagnostic_rows))
    return specs


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_repair_spec_materialization",
            "admissible": True,
            "reason": "M2371 may claim only repair-spec artifact materialization",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2371 names repair levers but does not execute them",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2371 does not train or evaluate a repaired driver",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2371 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "repair specs do not rank controller families",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2371 is artifact materialization, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2371 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2371 does not run history interventions",
        },
    ]


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def run_repair_spec_materialization(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    offtrack_target_rows_path: Path | str = DEFAULT_OFFTRACK_TARGET_ROWS,
    collision_guardrail_rows_path: Path | str = DEFAULT_COLLISION_GUARDRAIL_ROWS,
    r4_rows_path: Path | str = DEFAULT_R4_ROWS,
    diagnostic_guardrail_rows_path: Path | str = DEFAULT_DIAGNOSTIC_GUARDRAIL_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_offtrack_row_count: int = DEFAULT_TARGET_OFFTRACK_ROW_COUNT,
    target_collision_guardrail_row_count: int = DEFAULT_TARGET_COLLISION_GUARDRAIL_ROW_COUNT,
    target_r4_row_count: int = DEFAULT_TARGET_R4_ROW_COUNT,
    target_diagnostic_guardrail_row_count: int = DEFAULT_TARGET_DIAGNOSTIC_GUARDRAIL_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    offtrack_rows = read_csv_rows(offtrack_target_rows_path)
    collision_rows = read_csv_rows(collision_guardrail_rows_path)
    r4_rows = read_csv_rows(r4_rows_path)
    diagnostic_rows = read_csv_rows(diagnostic_guardrail_rows_path)

    specs = build_repair_specs(
        offtrack_rows=offtrack_rows,
        collision_rows=collision_rows,
        r4_rows=r4_rows,
        diagnostic_rows=diagnostic_rows,
    )
    ordinary_offtrack_specs = [
        row
        for row in specs
        if row["repair_family"] in {"priority_offtrack_containment_repair", "offtrack_containment_repair"}
    ]
    mixed_guarded_specs = [row for row in specs if row["repair_family"] == "guarded_offtrack_containment_repair"]
    collision_specs = [row for row in specs if row["repair_family"] == "collision_guardrail_constraint"]
    r4_specs = [row for row in specs if row["repair_family"] == "r4_mitigation_semantics_guardrail"]
    diagnostic_specs = [row for row in specs if row["repair_family"] == "diagnostic_no_ranking_guardrail"]

    profile_or_pack_repair_spec_count = sum(
        1
        for row in specs
        if row["repair_family"]
        in {"priority_offtrack_containment_repair", "offtrack_containment_repair", "guarded_offtrack_containment_repair"}
        and str(row["source_slice_axis"]) in DIAGNOSTIC_AXES
    )
    r4_ordinary_repair_spec_count = sum(
        1
        for row in specs
        if _bool(row.get("r4_mitigation_semantics"))
        and row["repair_family"]
        in {"priority_offtrack_containment_repair", "offtrack_containment_repair", "guarded_offtrack_containment_repair"}
    )
    collision_blind_mixed_repair_spec_count = sum(
        1
        for row in mixed_guarded_specs
        if not _bool(row.get("collision_guardrail_required"))
        or "collision" not in str(row.get("guardrail_metric", ""))
    )
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
        "winner_selected": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
    }
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    ranking_admissible_count = _flag_count(specs, "ranking_admissible")
    winner_selected_count = _flag_count(specs, "winner_selected")

    passes = (
        len(offtrack_rows) == int(target_offtrack_row_count)
        and len(collision_rows) == int(target_collision_guardrail_row_count)
        and len(r4_rows) == int(target_r4_row_count)
        and len(diagnostic_rows) == int(target_diagnostic_guardrail_row_count)
        and len(specs) > 0
        and len(ordinary_offtrack_specs) > 0
        and len(mixed_guarded_specs) > 0
        and len(collision_specs) > 0
        and len(r4_specs) > 0
        and len(diagnostic_specs) > 0
        and profile_or_pack_repair_spec_count == 0
        and r4_ordinary_repair_spec_count == 0
        and collision_blind_mixed_repair_spec_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    write_csv_rows(output / "repair_spec_rows.csv", specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "ordinary_offtrack_repair_spec_rows.csv", ordinary_offtrack_specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "mixed_guarded_repair_spec_rows.csv", mixed_guarded_specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "collision_guardrail_spec_rows.csv", collision_specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "r4_guardrail_spec_rows.csv", r4_specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "diagnostic_guardrail_spec_rows.csv", diagnostic_specs, fieldnames=REPAIR_SPEC_FIELDNAMES)
    write_csv_rows(output / "claim_boundary.csv", claim_boundary_rows(), fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_offtrack_row_count": len(offtrack_rows),
        "target_offtrack_row_count": int(target_offtrack_row_count),
        "source_collision_guardrail_row_count": len(collision_rows),
        "target_collision_guardrail_row_count": int(target_collision_guardrail_row_count),
        "source_r4_row_count": len(r4_rows),
        "target_r4_row_count": int(target_r4_row_count),
        "source_diagnostic_guardrail_row_count": len(diagnostic_rows),
        "target_diagnostic_guardrail_row_count": int(target_diagnostic_guardrail_row_count),
        "repair_spec_row_count": len(specs),
        "ordinary_offtrack_repair_spec_count": len(ordinary_offtrack_specs),
        "mixed_guarded_repair_spec_count": len(mixed_guarded_specs),
        "collision_guardrail_spec_count": len(collision_specs),
        "r4_guardrail_spec_count": len(r4_specs),
        "diagnostic_guardrail_spec_count": len(diagnostic_specs),
        "profile_or_pack_repair_spec_count": profile_or_pack_repair_spec_count,
        "r4_ordinary_repair_spec_count": r4_ordinary_repair_spec_count,
        "collision_blind_mixed_repair_spec_count": collision_blind_mixed_repair_spec_count,
        "repair_family_counts": _count_by(specs, "repair_family"),
        "priority_tier_counts": _count_by(specs, "priority_tier"),
        "top_repair_specs": specs[:10],
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
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "support_policy_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "finite_window_vs_gru_conclusion_made": False,
        "level3_self_id_claim_made": False,
        "scenario_redesign_executed_claim_made": False,
        "training_repair_success_claim_made": False,
        "artifacts": {
            "summary": str(output / "summary.json"),
            "repair_spec_rows": str(output / "repair_spec_rows.csv"),
            "ordinary_offtrack_repair_spec_rows": str(output / "ordinary_offtrack_repair_spec_rows.csv"),
            "mixed_guarded_repair_spec_rows": str(output / "mixed_guarded_repair_spec_rows.csv"),
            "collision_guardrail_spec_rows": str(output / "collision_guardrail_spec_rows.csv"),
            "r4_guardrail_spec_rows": str(output / "r4_guardrail_spec_rows.csv"),
            "diagnostic_guardrail_spec_rows": str(output / "diagnostic_guardrail_spec_rows.csv"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--offtrack-target-rows", type=Path, default=DEFAULT_OFFTRACK_TARGET_ROWS)
    parser.add_argument("--collision-guardrail-rows", type=Path, default=DEFAULT_COLLISION_GUARDRAIL_ROWS)
    parser.add_argument("--r4-rows", type=Path, default=DEFAULT_R4_ROWS)
    parser.add_argument("--diagnostic-guardrail-rows", type=Path, default=DEFAULT_DIAGNOSTIC_GUARDRAIL_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-offtrack-row-count", type=int, default=DEFAULT_TARGET_OFFTRACK_ROW_COUNT)
    parser.add_argument(
        "--target-collision-guardrail-row-count",
        type=int,
        default=DEFAULT_TARGET_COLLISION_GUARDRAIL_ROW_COUNT,
    )
    parser.add_argument("--target-r4-row-count", type=int, default=DEFAULT_TARGET_R4_ROW_COUNT)
    parser.add_argument(
        "--target-diagnostic-guardrail-row-count",
        type=int,
        default=DEFAULT_TARGET_DIAGNOSTIC_GUARDRAIL_ROW_COUNT,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_repair_spec_materialization(
        summary_path=args.summary,
        offtrack_target_rows_path=args.offtrack_target_rows,
        collision_guardrail_rows_path=args.collision_guardrail_rows,
        r4_rows_path=args.r4_rows,
        diagnostic_guardrail_rows_path=args.diagnostic_guardrail_rows,
        output_dir=args.output_dir,
        target_offtrack_row_count=int(args.target_offtrack_row_count),
        target_collision_guardrail_row_count=int(args.target_collision_guardrail_row_count),
        target_r4_row_count=int(args.target_r4_row_count),
        target_diagnostic_guardrail_row_count=int(args.target_diagnostic_guardrail_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"repair_spec_row_count={summary['repair_spec_row_count']}")
    print(f"ordinary_offtrack_repair_spec_count={summary['ordinary_offtrack_repair_spec_count']}")
    print(f"mixed_guarded_repair_spec_count={summary['mixed_guarded_repair_spec_count']}")
    print(f"collision_guardrail_spec_count={summary['collision_guardrail_spec_count']}")
    print(f"r4_guardrail_spec_count={summary['r4_guardrail_spec_count']}")
    print(f"diagnostic_guardrail_spec_count={summary['diagnostic_guardrail_spec_count']}")
    print(f"profile_or_pack_repair_spec_count={summary['profile_or_pack_repair_spec_count']}")
    print(f"r4_ordinary_repair_spec_count={summary['r4_ordinary_repair_spec_count']}")
    print(f"collision_blind_mixed_repair_spec_count={summary['collision_blind_mixed_repair_spec_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
