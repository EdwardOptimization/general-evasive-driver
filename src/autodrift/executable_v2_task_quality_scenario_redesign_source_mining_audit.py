"""Audit scenario-redesign source mining by joining support rows to template metadata."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows


DEFAULT_TEMPLATE = Path("configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json")
DEFAULT_SOURCE_MINING_DIR = Path("runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution")
DEFAULT_OUTPUT_DIR = Path("runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit")
DEFAULT_NEXT_BLOCKER = "m1925-executable-v2-task-quality-scenario-redesign-materialization-design"
TIER_A = "tier_a_positive_support_sanity"
TIER_B = "tier_b_feasible_emergency"
TIER_C = "tier_c_boundary_near_miss"
TIER_D = "tier_d_handling_limit_drift_required"
TIER_E = "tier_e_mitigation_only"
AGGREGATE_SPECS: dict[str, tuple[str, ...]] = {
    "tier_support_aggregate": ("feasibility_tier_id",),
    "source_split_support_aggregate": ("source_split",),
    "role_support_aggregate": ("source_role_semantics",),
    "surface_support_aggregate": ("surface_variant",),
    "speed_support_aggregate": ("speed_ref",),
    "mu_support_aggregate": ("mu",),
    "tier_role_support_aggregate": ("feasibility_tier_id", "source_role_semantics"),
    "tier_split_support_aggregate": ("feasibility_tier_id", "source_split"),
    "tier_surface_support_aggregate": ("feasibility_tier_id", "surface_variant"),
}
FORBIDDEN_GUARDRAILS = (
    "source_mining_execution_started",
    "environment_reset_started",
    "environment_rollout_started",
    "measured_rollout_started",
    "training_started",
    "replay_started",
    "ppo_used",
    "promoted",
    "private_holdout_used",
    "actor_input_contract_changed",
    "profile_specific_tuning",
    "controller_family_ranking_claim_made",
    "paper_level_claim_made",
    "level3_self_id_claim_made",
)


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def load_template_rows(path: Path | str) -> list[dict[str, Any]]:
    payload = read_json(path)
    return [dict(row) for row in payload.get("candidate_sources", [])]


def join_support_rows(
    *,
    template_rows: Iterable[Mapping[str, Any]],
    materialization_rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    template_by_source = {str(row["candidate_source_id"]): dict(row) for row in template_rows}
    joined: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for row in materialization_rows:
        candidate_id = str(row.get("candidate_source_id", ""))
        template = template_by_source.get(candidate_id)
        if template is None:
            missing.append(dict(row))
            continue
        supported = _bool_value(row.get("materialization_admissible"))
        joined.append(
            {
                "candidate_source_id": candidate_id,
                "source_v1_bounded_panel_spec_id": row.get("source_v1_bounded_panel_spec_id", ""),
                "source_scenario_spec_id": row.get("source_scenario_spec_id", ""),
                "feasibility_tier_id": template.get("feasibility_tier_id", ""),
                "source_split": template.get("source_split", ""),
                "source_role_semantics": template.get("source_role_semantics", ""),
                "surface_variant": template.get("surface_variant", ""),
                "speed_ref": template.get("speed_ref", ""),
                "mu": template.get("mu", ""),
                "target_support_mode": template.get("target_support_mode", ""),
                "target_boundary_mode": template.get("target_boundary_mode", ""),
                "expected_joint_support": _bool_value(template.get("expected_joint_support")),
                "expected_near_miss_support": _bool_value(template.get("expected_near_miss_support")),
                "mitigation_only": _bool_value(template.get("mitigation_only")),
                "positive_support_gate_required": _bool_value(template.get("positive_support_gate_required")),
                "paper_holdout_candidate": _bool_value(template.get("paper_holdout_candidate")),
                "source_support_status": row.get("source_support_status", ""),
                "materialization_admissible": supported,
                "source_support_accepted_cell_count_total": _int_value(
                    row.get("source_support_accepted_cell_count_total")
                ),
                "source_support_feasible_profile_count": _int_value(row.get("source_support_feasible_profile_count")),
                "source_support_profile_count": _int_value(row.get("source_support_profile_count")),
                "source_support_failure_reason": row.get("source_support_failure_reason", ""),
                "source_support_label_counts": row.get("source_support_label_counts", ""),
                "source_support_reject_reason_counts": row.get("source_support_reject_reason_counts", ""),
                "labels_enter_actor_input": _bool_value(row.get("labels_enter_actor_input")),
                "v2_ranking_admissible_by_default": _bool_value(row.get("v2_ranking_admissible_by_default")),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
    return joined, missing


def _aggregate(rows: list[Mapping[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(key, "")) for key in keys)].append(row)
    out: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        supported = [row for row in group if _bool_value(row.get("materialization_admissible"))]
        candidate_count = len(group)
        supported_count = len(supported)
        aggregate = {keys[index]: key[index] for index in range(len(keys))}
        aggregate.update(
            {
                "candidate_source_count": candidate_count,
                "supported_source_count": supported_count,
                "unsupported_source_count": candidate_count - supported_count,
                "supported_source_rate": float(supported_count / candidate_count) if candidate_count else 0.0,
                "accepted_cell_count_total": sum(
                    _int_value(row.get("source_support_accepted_cell_count_total")) for row in group
                ),
                "positive_support_gate_required_count": sum(
                    _bool_value(row.get("positive_support_gate_required")) for row in group
                ),
                "expected_joint_support_count": sum(_bool_value(row.get("expected_joint_support")) for row in group),
                "expected_near_miss_support_count": sum(
                    _bool_value(row.get("expected_near_miss_support")) for row in group
                ),
                "mitigation_only_count": sum(_bool_value(row.get("mitigation_only")) for row in group),
                "paper_holdout_candidate_count": sum(_bool_value(row.get("paper_holdout_candidate")) for row in group),
                "diagnostic_only_no_ranking_claim": True,
            }
        )
        out.append(aggregate)
    return out


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _supported_count(rows: Iterable[Mapping[str, Any]], **filters: str) -> int:
    total = 0
    for row in rows:
        if not _bool_value(row.get("materialization_admissible")):
            continue
        if all(str(row.get(key, "")) == str(value) for key, value in filters.items()):
            total += 1
    return total


def audit_scenario_redesign_source_mining(
    *,
    template_path: Path | str = DEFAULT_TEMPLATE,
    source_mining_dir: Path | str = DEFAULT_SOURCE_MINING_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    source_dir = Path(source_mining_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    template_rows = load_template_rows(template_path)
    materialization_rows = [
        dict(row) for row in read_csv_rows(source_dir / "support_first_materialization_admissibility_input.csv")
    ]
    source_summary = read_json(source_dir / "summary.json") if (source_dir / "summary.json").exists() else {}
    joined_rows, missing_rows = join_support_rows(
        template_rows=template_rows,
        materialization_rows=materialization_rows,
    )

    write_csv_rows(output / "joined_source_support.csv", joined_rows)
    write_csv_rows(output / "template_join_missing_rows.csv", missing_rows)
    artifact_paths: dict[str, str] = {
        "summary": str(output / "summary.json"),
        "joined_source_support": str(output / "joined_source_support.csv"),
        "template_join_missing_rows": str(output / "template_join_missing_rows.csv"),
    }
    aggregate_row_counts: dict[str, int] = {
        "joined_source_support_rows": len(joined_rows),
        "template_join_missing_rows": len(missing_rows),
    }
    for name, keys in AGGREGATE_SPECS.items():
        rows = _aggregate(joined_rows, keys)
        write_csv_rows(output / f"{name}.csv", rows)
        artifact_paths[name] = str(output / f"{name}.csv")
        aggregate_row_counts[f"{name}_rows"] = len(rows)

    supported_source_count = sum(_bool_value(row.get("materialization_admissible")) for row in joined_rows)
    accepted_cell_count_total = sum(_int_value(row.get("source_support_accepted_cell_count_total")) for row in joined_rows)
    tier_supported_counts = {
        tier: _supported_count(joined_rows, feasibility_tier_id=tier)
        for tier in (TIER_A, TIER_B, TIER_C, TIER_D, TIER_E)
    }
    split_supported_counts = {
        split: _supported_count(joined_rows, source_split=split)
        for split in ("public_debug", "public_gate", "paper_holdout_candidate")
    }
    role_supported_counts = {
        role: _supported_count(joined_rows, source_role_semantics=role)
        for role in sorted(_count_by(joined_rows, "source_role_semantics"))
    }
    labels_enter_actor_input_count = sum(_bool_value(row.get("labels_enter_actor_input")) for row in joined_rows)
    ranking_default_count = sum(_bool_value(row.get("v2_ranking_admissible_by_default")) for row in joined_rows)
    tier_a_b_positive_support_pass = tier_supported_counts[TIER_A] > 0 and tier_supported_counts[TIER_B] > 0
    tier_c_d_near_miss_support_pass = tier_supported_counts[TIER_C] > 0 or tier_supported_counts[TIER_D] > 0
    split_support_pass = split_supported_counts["public_debug"] > 0 and split_supported_counts["public_gate"] > 0
    holdout_support_present = split_supported_counts["paper_holdout_candidate"] > 0
    guardrail_flags = {key: False for key in FORBIDDEN_GUARDRAILS}
    guardrail_violation_count = int(sum(bool(value) for value in guardrail_flags.values()))
    result_passes = (
        len(template_rows) == 640
        and len(materialization_rows) == 640
        and len(joined_rows) == 640
        and not missing_rows
        and supported_source_count > 0
        and accepted_cell_count_total > 0
        and labels_enter_actor_input_count == 0
        and ranking_default_count == 0
        and tier_a_b_positive_support_pass
        and tier_c_d_near_miss_support_pass
        and split_support_pass
        and guardrail_violation_count == 0
    )
    recommended_next_route = (
        "route_to_materialization_design"
        if result_passes
        else "route_to_template_or_source_mining_schema_repair"
    )

    summary = {
        "result_class": (
            "task_quality_scenario_source_mining_result_audit_pass"
            if result_passes
            else "task_quality_scenario_source_mining_result_audit_incomplete_or_fail"
        ),
        "generated_at_utc": utc_timestamp(),
        "template_path": str(template_path),
        "source_mining_dir": str(source_dir),
        "source_result_class": source_summary.get("result_class", ""),
        "source_supported_source_count": source_summary.get("supported_source_count", ""),
        "source_accepted_cell_count_total": source_summary.get("accepted_cell_count_total", ""),
        "template_candidate_count": len(template_rows),
        "materialization_row_count": len(materialization_rows),
        "joined_source_count": len(joined_rows),
        "template_join_missing_count": len(missing_rows),
        "supported_source_count": int(supported_source_count),
        "accepted_cell_count_total": int(accepted_cell_count_total),
        "tier_supported_counts": tier_supported_counts,
        "split_supported_counts": split_supported_counts,
        "role_supported_counts": role_supported_counts,
        "tier_counts": _count_by(joined_rows, "feasibility_tier_id"),
        "split_counts": _count_by(joined_rows, "source_split"),
        "role_counts": _count_by(joined_rows, "source_role_semantics"),
        "surface_counts": _count_by(joined_rows, "surface_variant"),
        "speed_counts": _count_by(joined_rows, "speed_ref"),
        "mu_counts": _count_by(joined_rows, "mu"),
        "tier_a_b_positive_support_pass": bool(tier_a_b_positive_support_pass),
        "tier_c_d_near_miss_support_pass": bool(tier_c_d_near_miss_support_pass),
        "split_support_pass": bool(split_support_pass),
        "holdout_support_present": bool(holdout_support_present),
        "labels_enter_actor_input_count": int(labels_enter_actor_input_count),
        "ranking_admissible_by_default_count": int(ranking_default_count),
        "ranking_blocked": True,
        "guardrail_flags": guardrail_flags,
        "guardrail_violation_count": guardrail_violation_count,
        "source_mining_execution_started": False,
        "environment_reset_started": False,
        "environment_rollout_started": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "recommended_next_route": recommended_next_route,
        **aggregate_row_counts,
        "artifacts": artifact_paths,
        "next_blocker": next_blocker,
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--source-mining-dir", type=Path, default=DEFAULT_SOURCE_MINING_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()
    summary = audit_scenario_redesign_source_mining(
        template_path=args.template,
        source_mining_dir=args.source_mining_dir,
        output_dir=args.output_dir,
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"joined_source_count={summary['joined_source_count']}")
    print(f"supported_source_count={summary['supported_source_count']}")
    print(f"tier_supported_counts={summary['tier_supported_counts']}")
    print(f"split_supported_counts={summary['split_supported_counts']}")
    print(f"recommended_next_route={summary['recommended_next_route']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")


if __name__ == "__main__":
    main()
