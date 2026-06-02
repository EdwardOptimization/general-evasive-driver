"""Artifact-only offtrack/guardrail config-patch application-plan materialization."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path("runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/summary.json")
DEFAULT_CONFIG_PATCH_MANIFEST = Path(
    "runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/config_patch_manifest.json"
)
DEFAULT_REWARD_PATCH_ROWS = Path(
    "runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/reward_config_patch_rows.csv"
)
DEFAULT_CURRICULUM_PATCH_ROWS = Path(
    "runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/curriculum_config_patch_rows.csv"
)
DEFAULT_GUARDRAIL_PATCH_ROWS = Path(
    "runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/guardrail_config_patch_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization"
)
DEFAULT_TARGET_REWARD_PATCH_ROW_COUNT = 162
DEFAULT_TARGET_CURRICULUM_PATCH_ROW_COUNT = 54
DEFAULT_TARGET_GUARDRAIL_PATCH_ROW_COUNT = 284
DEFAULT_TARGET_CANDIDATE_APPLICATION_SPEC_COUNT = 54
DEFAULT_TARGET_MIXED_GUARDED_CANDIDATE_REQUIREMENT_COUNT = 18
DEFAULT_NEXT_BLOCKER = "m2383-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization-result-audit"
RESULT_PASS = "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_incomplete_or_fail"

CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "priority_tier",
    "reward_patch_count",
    "curriculum_patch_count",
    "guardrail_patch_scope",
    "mixed_collision_guardrail_required",
    "active_config_overwritten",
    "config_patch_applied",
    "candidate_config_file_written",
    "actor_input_change",
    "hidden_oracle_feature_injection",
    "profile_specific_tuning",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
PATCH_REF_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "patch_id",
    "patch_family",
    "target_namespace",
    "target_key",
    "delta_value",
    "config_patch_applied",
    "active_config_overwritten",
    "candidate_config_file_written",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
GUARDRAIL_REF_FIELDNAMES = [
    "guardrail_scope_id",
    "patch_id",
    "source_constraint_id",
    "source_repair_spec_id",
    "repair_family",
    "constraint_family",
    "constraint_metric",
    "target_namespace",
    "target_key",
    "required",
    "config_patch_applied",
    "active_config_overwritten",
    "candidate_config_file_written",
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
MIXED_REQUIREMENT_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "source_slice_axis",
    "source_slice_value",
    "collision_guardrail_required",
    "guardrail_scope_id",
    "config_patch_applied",
    "active_config_overwritten",
    "candidate_config_file_written",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


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


def _group_by_spec(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_repair_spec_id", ""))].append(row)
    return dict(grouped)


def _candidate_id(index: int, spec_id: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in spec_id).strip("_")
    return f"candidate_application_{index:04d}_{safe}"


def build_application_plan_rows(
    reward_rows: Sequence[Mapping[str, Any]],
    curriculum_rows: Sequence[Mapping[str, Any]],
    guardrail_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    reward_by_spec = _group_by_spec(reward_rows)
    curriculum_by_spec = _group_by_spec(curriculum_rows)
    spec_ids = sorted(set(reward_by_spec) | set(curriculum_by_spec))
    candidate_rows: list[dict[str, Any]] = []
    reward_refs: list[dict[str, Any]] = []
    curriculum_refs: list[dict[str, Any]] = []
    mixed_requirements: list[dict[str, Any]] = []

    for index, spec_id in enumerate(spec_ids):
        candidate_id = _candidate_id(index, spec_id)
        reward_group = list(reward_by_spec.get(spec_id, []))
        curriculum_group = list(curriculum_by_spec.get(spec_id, []))
        source = reward_group[0] if reward_group else (curriculum_group[0] if curriculum_group else {})
        repair_family = str(source.get("repair_family", ""))
        mixed_required = repair_family == "guarded_offtrack_containment_repair" or any(
            _bool(row.get("collision_guardrail_required")) for row in [*reward_group, *curriculum_group]
        )
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": spec_id,
                "repair_family": repair_family,
                "source_slice_axis": str(source.get("source_slice_axis", "")),
                "source_slice_value": str(source.get("source_slice_value", "")),
                "priority_tier": str(source.get("priority_tier", "")),
                "reward_patch_count": len(reward_group),
                "curriculum_patch_count": len(curriculum_group),
                "guardrail_patch_scope": "global_guardrail_scope" if guardrail_rows else "",
                "mixed_collision_guardrail_required": mixed_required,
                "active_config_overwritten": False,
                "config_patch_applied": False,
                "candidate_config_file_written": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
        for row in reward_group:
            reward_refs.append(_patch_ref(candidate_id, spec_id, row))
        for row in curriculum_group:
            curriculum_refs.append(_patch_ref(candidate_id, spec_id, row))
        if mixed_required:
            mixed_requirements.append(
                {
                    "candidate_id": candidate_id,
                    "source_repair_spec_id": spec_id,
                    "repair_family": repair_family,
                    "source_slice_axis": str(source.get("source_slice_axis", "")),
                    "source_slice_value": str(source.get("source_slice_value", "")),
                    "collision_guardrail_required": True,
                    "guardrail_scope_id": "global_guardrail_scope",
                    "config_patch_applied": False,
                    "active_config_overwritten": False,
                    "candidate_config_file_written": False,
                    "repair_execution_started": False,
                    "training_started": False,
                    "ranking_admissible": False,
                    "winner_selected": False,
                }
            )

    guardrail_refs = [_guardrail_ref(row) for row in guardrail_rows]
    return candidate_rows, reward_refs, curriculum_refs, guardrail_refs, mixed_requirements


def _patch_ref(candidate_id: str, spec_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "source_repair_spec_id": spec_id,
        "patch_id": str(row.get("patch_id", "")),
        "patch_family": str(row.get("patch_family", "")),
        "target_namespace": str(row.get("target_namespace", "")),
        "target_key": str(row.get("target_key", "")),
        "delta_value": str(row.get("delta_value", "")),
        "config_patch_applied": False,
        "active_config_overwritten": False,
        "candidate_config_file_written": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _guardrail_ref(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "guardrail_scope_id": "global_guardrail_scope",
        "patch_id": str(row.get("patch_id", "")),
        "source_constraint_id": str(row.get("source_constraint_id", "")),
        "source_repair_spec_id": str(row.get("source_repair_spec_id", "")),
        "repair_family": str(row.get("repair_family", "")),
        "constraint_family": str(row.get("constraint_family", "")),
        "constraint_metric": str(row.get("constraint_metric", "")),
        "target_namespace": str(row.get("target_namespace", "")),
        "target_key": str(row.get("target_key", "")),
        "required": True,
        "config_patch_applied": False,
        "active_config_overwritten": False,
        "candidate_config_file_written": False,
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


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_application_plan_materialization",
            "admissible": True,
            "reason": "M2382 may claim only application-plan artifact materialization",
        },
        {
            "claim": "active_config_overwrite",
            "admissible": False,
            "reason": "M2382 writes application-plan artifacts only",
        },
        {
            "claim": "config_patch_application",
            "admissible": False,
            "reason": "M2382 references patches but does not apply them",
        },
        {
            "claim": "candidate_config_file_generation",
            "admissible": False,
            "reason": "M2382 writes no candidate config files",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2382 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2382 does not train or evaluate a repaired driver",
        },
        {
            "claim": "scenario_redesign_executed",
            "admissible": False,
            "reason": "M2382 does not modify or execute redesigned scenarios",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "application plans do not rank controller families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "application plans do not rank support policies",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2382 does not select a support policy or controller winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2382 is infrastructure, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2382 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2382 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2382 does not run validation needed for a current-sim verdict",
        },
    ]


def run_application_plan_materialization(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    config_patch_manifest_path: Path | str = DEFAULT_CONFIG_PATCH_MANIFEST,
    reward_config_patch_rows_path: Path | str = DEFAULT_REWARD_PATCH_ROWS,
    curriculum_config_patch_rows_path: Path | str = DEFAULT_CURRICULUM_PATCH_ROWS,
    guardrail_config_patch_rows_path: Path | str = DEFAULT_GUARDRAIL_PATCH_ROWS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_reward_patch_row_count: int = DEFAULT_TARGET_REWARD_PATCH_ROW_COUNT,
    target_curriculum_patch_row_count: int = DEFAULT_TARGET_CURRICULUM_PATCH_ROW_COUNT,
    target_guardrail_patch_row_count: int = DEFAULT_TARGET_GUARDRAIL_PATCH_ROW_COUNT,
    target_candidate_application_spec_count: int = DEFAULT_TARGET_CANDIDATE_APPLICATION_SPEC_COUNT,
    target_mixed_guarded_candidate_requirement_count: int = DEFAULT_TARGET_MIXED_GUARDED_CANDIDATE_REQUIREMENT_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(summary_path)
    config_patch_manifest = read_json(config_patch_manifest_path)
    reward_rows = read_csv_rows(reward_config_patch_rows_path)
    curriculum_rows = read_csv_rows(curriculum_config_patch_rows_path)
    guardrail_rows = read_csv_rows(guardrail_config_patch_rows_path)
    candidate_rows, reward_refs, curriculum_refs, guardrail_refs, mixed_requirements = build_application_plan_rows(
        reward_rows,
        curriculum_rows,
        guardrail_rows,
    )
    claim_rows = claim_boundary_rows()

    all_application_rows: list[Mapping[str, Any]] = [
        *candidate_rows,
        *reward_refs,
        *curriculum_refs,
        *guardrail_refs,
        *mixed_requirements,
    ]
    candidate_without_reward_patch_count = sum(int(row.get("reward_patch_count", 0)) == 0 for row in candidate_rows)
    candidate_without_curriculum_patch_count = sum(int(row.get("curriculum_patch_count", 0)) == 0 for row in candidate_rows)
    candidate_without_guardrail_scope_count = sum(not str(row.get("guardrail_patch_scope", "")) for row in candidate_rows)
    active_config_overwrite_count = _flag_count(all_application_rows, "active_config_overwritten")
    config_patch_applied_count = _flag_count(all_application_rows, "config_patch_applied")
    candidate_config_file_written_count = _flag_count(all_application_rows, "candidate_config_file_written")
    actor_input_change_count = _flag_count(all_application_rows, "actor_input_change")
    hidden_oracle_feature_injection_count = _flag_count(all_application_rows, "hidden_oracle_feature_injection")
    profile_specific_tuning_count = _flag_count(all_application_rows, "profile_specific_tuning")
    repair_execution_count = _flag_count(all_application_rows, "repair_execution_started")
    training_count = _flag_count(all_application_rows, "training_started")
    ranking_admissible_count = _flag_count(all_application_rows, "ranking_admissible")
    winner_selected_count = _flag_count(all_application_rows, "winner_selected")
    non_required_guardrail_reference_count = sum(not _bool(row.get("required"), default=True) for row in guardrail_refs)

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
        "config_patch_applied": False,
        "candidate_config_file_written": False,
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

    passes = (
        source_summary.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"
        and config_patch_manifest.get("result_class") == "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"
        and len(reward_rows) == int(target_reward_patch_row_count)
        and len(curriculum_rows) == int(target_curriculum_patch_row_count)
        and len(guardrail_rows) == int(target_guardrail_patch_row_count)
        and len(candidate_rows) == int(target_candidate_application_spec_count)
        and len(reward_refs) == len(reward_rows)
        and len(curriculum_refs) == len(curriculum_rows)
        and len(guardrail_refs) == len(guardrail_rows)
        and len(mixed_requirements) == int(target_mixed_guarded_candidate_requirement_count)
        and candidate_without_reward_patch_count == 0
        and candidate_without_curriculum_patch_count == 0
        and candidate_without_guardrail_scope_count == 0
        and active_config_overwrite_count == 0
        and config_patch_applied_count == 0
        and candidate_config_file_written_count == 0
        and actor_input_change_count == 0
        and hidden_oracle_feature_injection_count == 0
        and profile_specific_tuning_count == 0
        and repair_execution_count == 0
        and training_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and non_required_guardrail_reference_count == 0
        and guardrail_violation_count == 0
    )

    plan = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "source_artifacts": {
            "summary": str(summary_path),
            "config_patch_manifest": str(config_patch_manifest_path),
            "reward_config_patch_rows": str(reward_config_patch_rows_path),
            "curriculum_config_patch_rows": str(curriculum_config_patch_rows_path),
            "guardrail_config_patch_rows": str(guardrail_config_patch_rows_path),
        },
        "output_artifacts": {
            "candidate_application_specs": str(output / "candidate_application_specs.csv"),
            "reward_patch_application_refs": str(output / "reward_patch_application_refs.csv"),
            "curriculum_patch_application_refs": str(output / "curriculum_patch_application_refs.csv"),
            "guardrail_patch_application_refs": str(output / "guardrail_patch_application_refs.csv"),
            "mixed_guarded_candidate_requirements": str(output / "mixed_guarded_candidate_requirements.csv"),
            "config_copy_preview": str(output / "config_copy_preview.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "application_semantics": {
            "patches_are_referenced_not_applied": True,
            "candidate_config_files_written": False,
            "active_config_overwrite_allowed": False,
            "guardrail_scope": "global_guardrail_scope",
        },
        "source_counts": {
            "reward_config_patch_rows": len(reward_rows),
            "curriculum_config_patch_rows": len(curriculum_rows),
            "guardrail_config_patch_rows": len(guardrail_rows),
        },
        "output_counts": {
            "candidate_application_specs": len(candidate_rows),
            "reward_patch_application_refs": len(reward_refs),
            "curriculum_patch_application_refs": len(curriculum_refs),
            "guardrail_patch_application_refs": len(guardrail_refs),
            "mixed_guarded_candidate_requirements": len(mixed_requirements),
        },
        "guardrail_flags": guardrail_flags,
    }
    preview = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "candidate_application_spec_count": len(candidate_rows),
        "reward_patch_reference_count": len(reward_refs),
        "curriculum_patch_reference_count": len(curriculum_refs),
        "guardrail_patch_reference_count": len(guardrail_refs),
        "mixed_guarded_candidate_requirement_count": len(mixed_requirements),
        "candidate_repair_family_counts": _count_by(candidate_rows, "repair_family"),
        "guardrail_target_key_counts": _count_by(guardrail_refs, "target_key"),
        "active_config_overwritten": False,
        "config_patch_applied": False,
        "candidate_config_file_written": False,
    }

    write_json(output / "application_plan_manifest.json", plan)
    write_csv_rows(output / "candidate_application_specs.csv", candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(output / "reward_patch_application_refs.csv", reward_refs, fieldnames=PATCH_REF_FIELDNAMES)
    write_csv_rows(output / "curriculum_patch_application_refs.csv", curriculum_refs, fieldnames=PATCH_REF_FIELDNAMES)
    write_csv_rows(output / "guardrail_patch_application_refs.csv", guardrail_refs, fieldnames=GUARDRAIL_REF_FIELDNAMES)
    write_csv_rows(
        output / "mixed_guarded_candidate_requirements.csv",
        mixed_requirements,
        fieldnames=MIXED_REQUIREMENT_FIELDNAMES,
    )
    write_json(output / "config_copy_preview.json", preview)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_config_patch_manifest": str(config_patch_manifest_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_reward_config_patch_row_count": len(reward_rows),
        "target_reward_config_patch_row_count": int(target_reward_patch_row_count),
        "source_curriculum_config_patch_row_count": len(curriculum_rows),
        "target_curriculum_config_patch_row_count": int(target_curriculum_patch_row_count),
        "source_guardrail_config_patch_row_count": len(guardrail_rows),
        "target_guardrail_config_patch_row_count": int(target_guardrail_patch_row_count),
        "candidate_application_spec_count": len(candidate_rows),
        "target_candidate_application_spec_count": int(target_candidate_application_spec_count),
        "reward_patch_reference_count": len(reward_refs),
        "curriculum_patch_reference_count": len(curriculum_refs),
        "guardrail_patch_reference_count": len(guardrail_refs),
        "mixed_guarded_candidate_requirement_count": len(mixed_requirements),
        "target_mixed_guarded_candidate_requirement_count": int(target_mixed_guarded_candidate_requirement_count),
        "candidate_without_reward_patch_count": candidate_without_reward_patch_count,
        "candidate_without_curriculum_patch_count": candidate_without_curriculum_patch_count,
        "candidate_without_guardrail_scope_count": candidate_without_guardrail_scope_count,
        "candidate_repair_family_counts": _count_by(candidate_rows, "repair_family"),
        "guardrail_target_key_counts": _count_by(guardrail_refs, "target_key"),
        "claim_boundary_row_count": len(claim_rows),
        "active_config_overwrite_count": active_config_overwrite_count,
        "config_patch_applied_count": config_patch_applied_count,
        "candidate_config_file_written_count": candidate_config_file_written_count,
        "actor_input_change_count": actor_input_change_count,
        "hidden_oracle_feature_injection_count": hidden_oracle_feature_injection_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "repair_execution_count": repair_execution_count,
        "training_count": training_count,
        "ranking_admissible_count": ranking_admissible_count,
        "winner_selected_count": winner_selected_count,
        "non_required_guardrail_reference_count": non_required_guardrail_reference_count,
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
        "config_patch_applied": False,
        "candidate_config_file_written": False,
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
            "application_plan_manifest": str(output / "application_plan_manifest.json"),
            "candidate_application_specs": str(output / "candidate_application_specs.csv"),
            "reward_patch_application_refs": str(output / "reward_patch_application_refs.csv"),
            "curriculum_patch_application_refs": str(output / "curriculum_patch_application_refs.csv"),
            "guardrail_patch_application_refs": str(output / "guardrail_patch_application_refs.csv"),
            "mixed_guarded_candidate_requirements": str(output / "mixed_guarded_candidate_requirements.csv"),
            "config_copy_preview": str(output / "config_copy_preview.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--config-patch-manifest", type=Path, default=DEFAULT_CONFIG_PATCH_MANIFEST)
    parser.add_argument("--reward-config-patch-rows", type=Path, default=DEFAULT_REWARD_PATCH_ROWS)
    parser.add_argument("--curriculum-config-patch-rows", type=Path, default=DEFAULT_CURRICULUM_PATCH_ROWS)
    parser.add_argument("--guardrail-config-patch-rows", type=Path, default=DEFAULT_GUARDRAIL_PATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-reward-patch-row-count", type=int, default=DEFAULT_TARGET_REWARD_PATCH_ROW_COUNT)
    parser.add_argument("--target-curriculum-patch-row-count", type=int, default=DEFAULT_TARGET_CURRICULUM_PATCH_ROW_COUNT)
    parser.add_argument("--target-guardrail-patch-row-count", type=int, default=DEFAULT_TARGET_GUARDRAIL_PATCH_ROW_COUNT)
    parser.add_argument(
        "--target-candidate-application-spec-count",
        type=int,
        default=DEFAULT_TARGET_CANDIDATE_APPLICATION_SPEC_COUNT,
    )
    parser.add_argument(
        "--target-mixed-guarded-candidate-requirement-count",
        type=int,
        default=DEFAULT_TARGET_MIXED_GUARDED_CANDIDATE_REQUIREMENT_COUNT,
    )
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_application_plan_materialization(
        summary_path=args.summary,
        config_patch_manifest_path=args.config_patch_manifest,
        reward_config_patch_rows_path=args.reward_config_patch_rows,
        curriculum_config_patch_rows_path=args.curriculum_config_patch_rows,
        guardrail_config_patch_rows_path=args.guardrail_config_patch_rows,
        output_dir=args.output_dir,
        target_reward_patch_row_count=int(args.target_reward_patch_row_count),
        target_curriculum_patch_row_count=int(args.target_curriculum_patch_row_count),
        target_guardrail_patch_row_count=int(args.target_guardrail_patch_row_count),
        target_candidate_application_spec_count=int(args.target_candidate_application_spec_count),
        target_mixed_guarded_candidate_requirement_count=int(args.target_mixed_guarded_candidate_requirement_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_reward_config_patch_row_count={summary['source_reward_config_patch_row_count']}")
    print(f"source_curriculum_config_patch_row_count={summary['source_curriculum_config_patch_row_count']}")
    print(f"source_guardrail_config_patch_row_count={summary['source_guardrail_config_patch_row_count']}")
    print(f"candidate_application_spec_count={summary['candidate_application_spec_count']}")
    print(f"reward_patch_reference_count={summary['reward_patch_reference_count']}")
    print(f"curriculum_patch_reference_count={summary['curriculum_patch_reference_count']}")
    print(f"guardrail_patch_reference_count={summary['guardrail_patch_reference_count']}")
    print(f"mixed_guarded_candidate_requirement_count={summary['mixed_guarded_candidate_requirement_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
