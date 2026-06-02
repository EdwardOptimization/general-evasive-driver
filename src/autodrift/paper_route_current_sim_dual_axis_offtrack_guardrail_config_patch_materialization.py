"""Artifact-only offtrack/guardrail config-patch materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json")
DEFAULT_REPAIR_PLAN = Path(
    "runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/repair_implementation_plan.json"
)
DEFAULT_REWARD_DELTA_ROWS = Path(
    "runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/reward_delta_rows.csv"
)
DEFAULT_CURRICULUM_WEIGHT_ROWS = Path(
    "runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/curriculum_weight_rows.csv"
)
DEFAULT_GUARDRAIL_CONSTRAINT_ROWS = Path(
    "runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/guardrail_constraint_rows.csv"
)
DEFAULT_MIXED_GUARDED_CONSTRAINT_ROWS = Path(
    "runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/mixed_guarded_constraint_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization")
DEFAULT_TARGET_REWARD_DELTA_ROW_COUNT = 54
DEFAULT_TARGET_CURRICULUM_WEIGHT_ROW_COUNT = 54
DEFAULT_TARGET_GUARDRAIL_CONSTRAINT_ROW_COUNT = 284
DEFAULT_TARGET_MIXED_GUARDED_CONSTRAINT_ROW_COUNT = 18
DEFAULT_NEXT_BLOCKER = "m2379-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-materialization-result-audit"
RESULT_PASS = "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_incomplete_or_fail"

REWARD_TARGETS = [
    ("reward.offtrack_margin_weight_delta", "offtrack_margin_reward_delta"),
    ("reward.recovery_window_weight_delta", "recovery_window_reward_delta"),
    ("reward.boundary_overshoot_penalty_delta", "boundary_overshoot_penalty_delta"),
]

REWARD_PATCH_FIELDNAMES = [
    "patch_id",
    "patch_family",
    "source_plan_row_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "priority_tier",
    "target_namespace",
    "target_key",
    "delta_value",
    "collision_guardrail_required",
    "active_config_overwritten",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "profile_specific_tuning",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]

CURRICULUM_PATCH_FIELDNAMES = [
    "patch_id",
    "patch_family",
    "source_plan_row_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "priority_tier",
    "target_namespace",
    "target_key",
    "delta_value",
    "collision_guardrail_required",
    "profile_specific_tuning",
    "active_config_overwritten",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]

GUARDRAIL_PATCH_FIELDNAMES = [
    "patch_id",
    "patch_family",
    "source_constraint_id",
    "source_repair_spec_id",
    "repair_family",
    "source_group",
    "source_slice_axis",
    "source_slice_value",
    "constraint_family",
    "constraint_metric",
    "target_namespace",
    "target_key",
    "required",
    "active_config_overwritten",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "profile_specific_tuning",
    "repair_execution_started",
    "training_started",
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
OVERLAY_NAMESPACES = {
    "candidate_reward_overlay",
    "candidate_curriculum_overlay",
    "candidate_guardrail_overlay",
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


def _float_value(row: Mapping[str, Any], key: str) -> float:
    try:
        return float(str(row.get(key, "0")).strip())
    except ValueError:
        return 0.0


def build_reward_config_patch_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        for target_index, (target_key, source_key) in enumerate(REWARD_TARGETS):
            patches.append(
                {
                    "patch_id": f"reward_patch_{row_index:04d}_{target_index}",
                    "patch_family": "reward_delta",
                    "source_plan_row_id": str(row.get("plan_row_id", "")),
                    "source_repair_spec_id": str(row.get("repair_spec_id", "")),
                    "repair_family": str(row.get("repair_family", "")),
                    "source_slice_axis": str(row.get("source_slice_axis", "")),
                    "source_slice_value": str(row.get("source_slice_value", "")),
                    "priority_tier": str(row.get("priority_tier", "")),
                    "target_namespace": "candidate_reward_overlay",
                    "target_key": target_key,
                    "delta_value": _float_value(row, source_key),
                    "collision_guardrail_required": _bool(row.get("collision_guardrail_required")),
                    "active_config_overwritten": False,
                    "actor_input_change": False,
                    "hidden_oracle_feature_injection": False,
                    "profile_specific_tuning": False,
                    "repair_execution_started": False,
                    "training_started": False,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )
    return patches


def build_curriculum_config_patch_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        patches.append(
            {
                "patch_id": f"curriculum_patch_{row_index:04d}",
                "patch_family": "curriculum_weight",
                "source_plan_row_id": str(row.get("plan_row_id", "")),
                "source_repair_spec_id": str(row.get("repair_spec_id", "")),
                "repair_family": str(row.get("repair_family", "")),
                "source_slice_axis": str(row.get("source_slice_axis", "")),
                "source_slice_value": str(row.get("source_slice_value", "")),
                "priority_tier": str(row.get("priority_tier", "")),
                "target_namespace": "candidate_curriculum_overlay",
                "target_key": "curriculum.source_slice_sampling_weight_multiplier",
                "delta_value": _float_value(row, "sampling_weight_multiplier"),
                "collision_guardrail_required": _bool(row.get("collision_guardrail_required")),
                "profile_specific_tuning": False,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    return patches


def _guardrail_target_key(row: Mapping[str, Any]) -> str:
    constraint_family = str(row.get("constraint_family", ""))
    constraint_metric = str(row.get("constraint_metric", ""))
    if constraint_family == "collision" or constraint_metric == "collision_rate_not_worse":
        return "guardrail.collision_rate_not_worse"
    if constraint_family == "r4_mitigation_semantics" or constraint_metric == "mitigation_semantics_preserved":
        return "guardrail.r4_mitigation_semantics_preserved"
    if constraint_family == "diagnostic_no_ranking" or constraint_metric == "no_ranking_no_winner_claims":
        return "guardrail.no_ranking_no_winner_claims"
    return f"guardrail.{constraint_metric or constraint_family or 'unknown'}"


def build_guardrail_config_patch_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        patches.append(
            {
                "patch_id": f"guardrail_patch_{row_index:04d}",
                "patch_family": "guardrail_constraint",
                "source_constraint_id": str(row.get("constraint_id", "")),
                "source_repair_spec_id": str(row.get("repair_spec_id", "")),
                "repair_family": str(row.get("repair_family", "")),
                "source_group": str(row.get("source_group", "")),
                "source_slice_axis": str(row.get("source_slice_axis", "")),
                "source_slice_value": str(row.get("source_slice_value", "")),
                "constraint_family": str(row.get("constraint_family", "")),
                "constraint_metric": str(row.get("constraint_metric", "")),
                "target_namespace": "candidate_guardrail_overlay",
                "target_key": _guardrail_target_key(row),
                "required": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "paper_level_claim_made": False,
                "finite_window_vs_gru_conclusion_made": False,
                "level3_self_id_claim_made": False,
                "scenario_redesign_executed_claim_made": False,
                "training_repair_success_claim_made": False,
                "current_sim_verdict_claim_made": False,
            }
        )
    return patches


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_config_patch_materialization",
            "admissible": True,
            "reason": "M2378 may claim only overlay config-patch artifact materialization",
        },
        {
            "claim": "active_config_overwrite",
            "admissible": False,
            "reason": "M2378 writes candidate overlay artifacts only",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2378 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2378 does not train or evaluate a repaired driver",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2378 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "config patches do not rank controller families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "config patches do not rank support policies",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2378 does not select a support policy or controller winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2378 is infrastructure, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2378 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2378 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2378 does not run validation needed for a current-sim verdict",
        },
    ]


def _namespace_violation_count(rows: Iterable[Mapping[str, Any]]) -> int:
    return sum(str(row.get("target_namespace", "")) not in OVERLAY_NAMESPACES for row in rows)


def _all_patch_rows(
    reward_patches: Sequence[Mapping[str, Any]],
    curriculum_patches: Sequence[Mapping[str, Any]],
    guardrail_patches: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    return [*reward_patches, *curriculum_patches, *guardrail_patches]


def run_config_patch_materialization(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    repair_plan_path: Path | str = DEFAULT_REPAIR_PLAN,
    reward_delta_rows_path: Path | str = DEFAULT_REWARD_DELTA_ROWS,
    curriculum_weight_rows_path: Path | str = DEFAULT_CURRICULUM_WEIGHT_ROWS,
    guardrail_constraint_rows_path: Path | str = DEFAULT_GUARDRAIL_CONSTRAINT_ROWS,
    mixed_guarded_constraint_rows_path: Path | str = DEFAULT_MIXED_GUARDED_CONSTRAINT_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_reward_delta_row_count: int = DEFAULT_TARGET_REWARD_DELTA_ROW_COUNT,
    target_curriculum_weight_row_count: int = DEFAULT_TARGET_CURRICULUM_WEIGHT_ROW_COUNT,
    target_guardrail_constraint_row_count: int = DEFAULT_TARGET_GUARDRAIL_CONSTRAINT_ROW_COUNT,
    target_mixed_guarded_constraint_row_count: int = DEFAULT_TARGET_MIXED_GUARDED_CONSTRAINT_ROW_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(summary_path)
    repair_plan = read_json(repair_plan_path)
    reward_delta_rows = read_csv_rows(reward_delta_rows_path)
    curriculum_weight_rows = read_csv_rows(curriculum_weight_rows_path)
    guardrail_constraint_rows = read_csv_rows(guardrail_constraint_rows_path)
    mixed_guarded_constraint_rows = read_csv_rows(mixed_guarded_constraint_rows_path)

    reward_patches = build_reward_config_patch_rows(reward_delta_rows)
    curriculum_patches = build_curriculum_config_patch_rows(curriculum_weight_rows)
    guardrail_patches = build_guardrail_config_patch_rows(guardrail_constraint_rows)
    all_patches = _all_patch_rows(reward_patches, curriculum_patches, guardrail_patches)
    claim_rows = claim_boundary_rows()

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
    active_config_overwrite_count = _flag_count(all_patches, "active_config_overwritten")
    actor_input_change_count = _flag_count(all_patches, "actor_input_change")
    hidden_oracle_feature_injection_count = _flag_count(all_patches, "hidden_oracle_feature_injection")
    profile_specific_tuning_count = _flag_count(all_patches, "profile_specific_tuning")
    repair_execution_count = _flag_count(all_patches, "repair_execution_started")
    training_count = _flag_count(all_patches, "training_started")
    ranking_admissible_count = _flag_count(all_patches, "ranking_admissible")
    winner_selected_count = _flag_count(all_patches, "winner_selected")
    namespace_violation_count = _namespace_violation_count(all_patches)
    mixed_ids = {str(row.get("constraint_id", "")) for row in mixed_guarded_constraint_rows}
    guarded_ids = {str(row.get("source_constraint_id", "")) for row in guardrail_patches}
    mixed_guarded_missing_count = len(mixed_ids - guarded_ids)
    non_required_guardrail_count = sum(not _bool(row.get("required"), default=True) for row in guardrail_patches)
    expected_reward_patch_count = len(reward_delta_rows) * len(REWARD_TARGETS)

    passes = (
        source_summary.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"
        and repair_plan.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"
        and len(reward_delta_rows) == int(target_reward_delta_row_count)
        and len(curriculum_weight_rows) == int(target_curriculum_weight_row_count)
        and len(guardrail_constraint_rows) == int(target_guardrail_constraint_row_count)
        and len(mixed_guarded_constraint_rows) == int(target_mixed_guarded_constraint_row_count)
        and len(reward_patches) == expected_reward_patch_count
        and len(curriculum_patches) == len(curriculum_weight_rows)
        and len(guardrail_patches) == len(guardrail_constraint_rows)
        and active_config_overwrite_count == 0
        and actor_input_change_count == 0
        and hidden_oracle_feature_injection_count == 0
        and profile_specific_tuning_count == 0
        and repair_execution_count == 0
        and training_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and namespace_violation_count == 0
        and mixed_guarded_missing_count == 0
        and non_required_guardrail_count == 0
        and guardrail_violation_count == 0
    )

    manifest = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "source_artifacts": {
            "summary": str(summary_path),
            "repair_plan": str(repair_plan_path),
            "reward_delta_rows": str(reward_delta_rows_path),
            "curriculum_weight_rows": str(curriculum_weight_rows_path),
            "guardrail_constraint_rows": str(guardrail_constraint_rows_path),
            "mixed_guarded_constraint_rows": str(mixed_guarded_constraint_rows_path),
        },
        "output_artifacts": {
            "reward_config_patch_rows": str(output / "reward_config_patch_rows.csv"),
            "curriculum_config_patch_rows": str(output / "curriculum_config_patch_rows.csv"),
            "guardrail_config_patch_rows": str(output / "guardrail_config_patch_rows.csv"),
            "config_patch_preview": str(output / "config_patch_preview.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "target_namespaces": sorted(OVERLAY_NAMESPACES),
        "overlay_only": True,
        "active_config_overwrite_allowed": False,
        "source_counts": {
            "reward_delta_rows": len(reward_delta_rows),
            "curriculum_weight_rows": len(curriculum_weight_rows),
            "guardrail_constraint_rows": len(guardrail_constraint_rows),
            "mixed_guarded_constraint_rows": len(mixed_guarded_constraint_rows),
        },
        "output_counts": {
            "reward_config_patch_rows": len(reward_patches),
            "curriculum_config_patch_rows": len(curriculum_patches),
            "guardrail_config_patch_rows": len(guardrail_patches),
        },
        "blocked_levers": [
            "active_scenario_config_overwrite",
            "actor_input_change",
            "hidden_oracle_feature_injection",
            "profile_specific_tuning",
            "repair_execution",
            "training",
            "replay",
            "ppo",
            "support_policy_ranking",
            "controller_family_ranking",
            "winner_selection",
            "paper_level_claim",
            "finite_window_vs_gru_conclusion",
            "level3_self_identification_claim",
            "current_sim_verdict_claim",
        ],
        "guardrail_flags": guardrail_flags,
    }
    preview = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "overlay_only": True,
        "target_namespace_counts": _count_by(all_patches, "target_namespace"),
        "patch_family_counts": _count_by(all_patches, "patch_family"),
        "reward_target_key_counts": _count_by(reward_patches, "target_key"),
        "guardrail_target_key_counts": _count_by(guardrail_patches, "target_key"),
        "active_config_overwritten": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
    }

    write_json(output / "config_patch_manifest.json", manifest)
    write_csv_rows(output / "reward_config_patch_rows.csv", reward_patches, fieldnames=REWARD_PATCH_FIELDNAMES)
    write_csv_rows(
        output / "curriculum_config_patch_rows.csv",
        curriculum_patches,
        fieldnames=CURRICULUM_PATCH_FIELDNAMES,
    )
    write_csv_rows(output / "guardrail_config_patch_rows.csv", guardrail_patches, fieldnames=GUARDRAIL_PATCH_FIELDNAMES)
    write_json(output / "config_patch_preview.json", preview)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_repair_plan": str(repair_plan_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_reward_delta_row_count": len(reward_delta_rows),
        "target_reward_delta_row_count": int(target_reward_delta_row_count),
        "source_curriculum_weight_row_count": len(curriculum_weight_rows),
        "target_curriculum_weight_row_count": int(target_curriculum_weight_row_count),
        "source_guardrail_constraint_row_count": len(guardrail_constraint_rows),
        "target_guardrail_constraint_row_count": int(target_guardrail_constraint_row_count),
        "source_mixed_guarded_constraint_row_count": len(mixed_guarded_constraint_rows),
        "target_mixed_guarded_constraint_row_count": int(target_mixed_guarded_constraint_row_count),
        "reward_config_patch_row_count": len(reward_patches),
        "expected_reward_config_patch_row_count": expected_reward_patch_count,
        "curriculum_config_patch_row_count": len(curriculum_patches),
        "guardrail_config_patch_row_count": len(guardrail_patches),
        "claim_boundary_row_count": len(claim_rows),
        "patch_family_counts": _count_by(all_patches, "patch_family"),
        "target_namespace_counts": _count_by(all_patches, "target_namespace"),
        "guardrail_target_key_counts": _count_by(guardrail_patches, "target_key"),
        "active_config_overwrite_count": active_config_overwrite_count,
        "actor_input_change_count": actor_input_change_count,
        "hidden_oracle_feature_injection_count": hidden_oracle_feature_injection_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "repair_execution_count": repair_execution_count,
        "training_count": training_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "namespace_violation_count": namespace_violation_count,
        "mixed_guarded_missing_count": mixed_guarded_missing_count,
        "non_required_guardrail_count": non_required_guardrail_count,
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
        "hidden_oracle_feature_injection": False,
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
            "config_patch_manifest": str(output / "config_patch_manifest.json"),
            "reward_config_patch_rows": str(output / "reward_config_patch_rows.csv"),
            "curriculum_config_patch_rows": str(output / "curriculum_config_patch_rows.csv"),
            "guardrail_config_patch_rows": str(output / "guardrail_config_patch_rows.csv"),
            "config_patch_preview": str(output / "config_patch_preview.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--repair-plan", type=Path, default=DEFAULT_REPAIR_PLAN)
    parser.add_argument("--reward-delta-rows", type=Path, default=DEFAULT_REWARD_DELTA_ROWS)
    parser.add_argument("--curriculum-weight-rows", type=Path, default=DEFAULT_CURRICULUM_WEIGHT_ROWS)
    parser.add_argument("--guardrail-constraint-rows", type=Path, default=DEFAULT_GUARDRAIL_CONSTRAINT_ROWS)
    parser.add_argument("--mixed-guarded-constraint-rows", type=Path, default=DEFAULT_MIXED_GUARDED_CONSTRAINT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-reward-delta-row-count", type=int, default=DEFAULT_TARGET_REWARD_DELTA_ROW_COUNT)
    parser.add_argument("--target-curriculum-weight-row-count", type=int, default=DEFAULT_TARGET_CURRICULUM_WEIGHT_ROW_COUNT)
    parser.add_argument("--target-guardrail-constraint-row-count", type=int, default=DEFAULT_TARGET_GUARDRAIL_CONSTRAINT_ROW_COUNT)
    parser.add_argument(
        "--target-mixed-guarded-constraint-row-count",
        type=int,
        default=DEFAULT_TARGET_MIXED_GUARDED_CONSTRAINT_ROW_COUNT,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_config_patch_materialization(
        summary_path=args.summary,
        repair_plan_path=args.repair_plan,
        reward_delta_rows_path=args.reward_delta_rows,
        curriculum_weight_rows_path=args.curriculum_weight_rows,
        guardrail_constraint_rows_path=args.guardrail_constraint_rows,
        mixed_guarded_constraint_rows_path=args.mixed_guarded_constraint_rows,
        output_dir=args.output_dir,
        target_reward_delta_row_count=int(args.target_reward_delta_row_count),
        target_curriculum_weight_row_count=int(args.target_curriculum_weight_row_count),
        target_guardrail_constraint_row_count=int(args.target_guardrail_constraint_row_count),
        target_mixed_guarded_constraint_row_count=int(args.target_mixed_guarded_constraint_row_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_reward_delta_row_count={summary['source_reward_delta_row_count']}")
    print(f"source_curriculum_weight_row_count={summary['source_curriculum_weight_row_count']}")
    print(f"source_guardrail_constraint_row_count={summary['source_guardrail_constraint_row_count']}")
    print(f"source_mixed_guarded_constraint_row_count={summary['source_mixed_guarded_constraint_row_count']}")
    print(f"reward_config_patch_row_count={summary['reward_config_patch_row_count']}")
    print(f"curriculum_config_patch_row_count={summary['curriculum_config_patch_row_count']}")
    print(f"guardrail_config_patch_row_count={summary['guardrail_config_patch_row_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
