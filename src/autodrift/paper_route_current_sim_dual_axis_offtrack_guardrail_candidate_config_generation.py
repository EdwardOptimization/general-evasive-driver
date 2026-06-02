"""Run-dir-only candidate config generation from application-plan artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_SUMMARY = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/summary.json"
)
DEFAULT_APPLICATION_PLAN_MANIFEST = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/application_plan_manifest.json"
)
DEFAULT_CANDIDATE_APPLICATION_SPECS = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/candidate_application_specs.csv"
)
DEFAULT_REWARD_PATCH_REFS = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/reward_patch_application_refs.csv"
)
DEFAULT_CURRICULUM_PATCH_REFS = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/curriculum_patch_application_refs.csv"
)
DEFAULT_GUARDRAIL_PATCH_REFS = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/guardrail_patch_application_refs.csv"
)
DEFAULT_MIXED_REQUIREMENTS = Path(
    "runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/mixed_guarded_candidate_requirements.csv"
)
DEFAULT_OUTPUT_DIR = Path("runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation")
DEFAULT_TARGET_CANDIDATE_SPEC_COUNT = 54
DEFAULT_TARGET_REWARD_REF_COUNT = 162
DEFAULT_TARGET_CURRICULUM_REF_COUNT = 54
DEFAULT_TARGET_GUARDRAIL_REF_COUNT = 284
DEFAULT_TARGET_MIXED_REQUIREMENT_COUNT = 18
DEFAULT_NEXT_BLOCKER = "m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis"
RESULT_PASS = "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
RESULT_FAIL = "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_incomplete_or_fail"

CANDIDATE_CONFIG_ROW_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "candidate_config_path",
    "reward_patch_count",
    "curriculum_patch_count",
    "guardrail_patch_scope",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required",
    "inside_run_dir",
    "active_config_overwritten",
    "loaded_into_environment",
    "environment_reset_started",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
PATCH_MATRIX_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "reward_patch_ids",
    "curriculum_patch_ids",
    "reward_patch_count",
    "curriculum_patch_count",
    "candidate_config_path",
    "active_config_overwritten",
    "loaded_into_environment",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
GUARDRAIL_SCOPE_FIELDNAMES = [
    "candidate_id",
    "guardrail_scope_id",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required",
    "candidate_config_path",
    "active_config_overwritten",
    "loaded_into_environment",
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


def _int_value(value: Any) -> int:
    try:
        return int(str(value).strip())
    except ValueError:
        return 0


def _count_by(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _flag_count(rows: Iterable[Mapping[str, Any]], key: str) -> int:
    return sum(_bool(row.get(key)) for row in rows)


def _group_by_candidate(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("candidate_id", ""))].append(row)
    return dict(grouped)


def _candidate_path(output_dir: Path, candidate_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in candidate_id).strip("_")
    return output_dir / "candidate_configs" / f"{safe}.json"


def _inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "artifact_only_candidate_config_generation",
            "admissible": True,
            "reason": "M2385 may claim only run-dir candidate config artifact generation",
        },
        {
            "claim": "active_config_overwrite",
            "admissible": False,
            "reason": "M2385 writes candidate configs under its run directory only",
        },
        {
            "claim": "environment_reset_or_rollout",
            "admissible": False,
            "reason": "M2385 does not load candidate configs into an environment",
        },
        {
            "claim": "repair_execution",
            "admissible": False,
            "reason": "M2385 does not execute repair levers",
        },
        {
            "claim": "training_repair_success",
            "admissible": False,
            "reason": "M2385 does not train or evaluate a repaired driver",
        },
        {
            "claim": "controller_family_ranking",
            "admissible": False,
            "reason": "candidate config generation does not rank controller families",
        },
        {
            "claim": "support_policy_ranking",
            "admissible": False,
            "reason": "candidate config generation does not rank support policies",
        },
        {
            "claim": "winner_selection",
            "admissible": False,
            "reason": "M2385 does not select a candidate winner",
        },
        {
            "claim": "paper_level_benchmark_result",
            "admissible": False,
            "reason": "M2385 is infrastructure, not a paper-level result",
        },
        {
            "claim": "finite_window_vs_gru_conclusion",
            "admissible": False,
            "reason": "M2385 does not run a finite-window-vs-GRU verdict protocol",
        },
        {
            "claim": "level3_self_identification",
            "admissible": False,
            "reason": "M2385 does not run history interventions",
        },
        {
            "claim": "current_sim_verdict",
            "admissible": False,
            "reason": "M2385 does not run validation needed for a current-sim verdict",
        },
    ]


def build_candidate_configs(
    *,
    output_dir: Path,
    candidate_specs: Sequence[Mapping[str, Any]],
    reward_refs: Sequence[Mapping[str, Any]],
    curriculum_refs: Sequence[Mapping[str, Any]],
    guardrail_refs: Sequence[Mapping[str, Any]],
    mixed_requirements: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    reward_by_candidate = _group_by_candidate(reward_refs)
    curriculum_by_candidate = _group_by_candidate(curriculum_refs)
    mixed_by_candidate = {str(row.get("candidate_id", "")): row for row in mixed_requirements}
    config_rows: list[dict[str, Any]] = []
    patch_matrix_rows: list[dict[str, Any]] = []
    guardrail_scope_rows: list[dict[str, Any]] = []

    for spec in candidate_specs:
        candidate_id = str(spec.get("candidate_id", ""))
        candidate_path = _candidate_path(output_dir, candidate_id)
        rewards = list(reward_by_candidate.get(candidate_id, []))
        curricula = list(curriculum_by_candidate.get(candidate_id, []))
        mixed_required = candidate_id in mixed_by_candidate or _bool(spec.get("mixed_collision_guardrail_required"))
        candidate_payload = {
            "candidate_id": candidate_id,
            "source_repair_spec_id": str(spec.get("source_repair_spec_id", "")),
            "repair_family": str(spec.get("repair_family", "")),
            "source_slice_axis": str(spec.get("source_slice_axis", "")),
            "source_slice_value": str(spec.get("source_slice_value", "")),
            "priority_tier": str(spec.get("priority_tier", "")),
            "reward_overlay": [
                {
                    "patch_id": str(row.get("patch_id", "")),
                    "target_key": str(row.get("target_key", "")),
                    "delta_value": str(row.get("delta_value", "")),
                }
                for row in rewards
            ],
            "curriculum_overlay": [
                {
                    "patch_id": str(row.get("patch_id", "")),
                    "target_key": str(row.get("target_key", "")),
                    "delta_value": str(row.get("delta_value", "")),
                }
                for row in curricula
            ],
            "guardrail_overlay": {
                "scope_id": "global_guardrail_scope",
                "guardrail_patch_count": len(guardrail_refs),
            },
            "mixed_guarded_requirements": {
                "collision_guardrail_required": mixed_required,
            },
            "claim_boundary": {
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "environment_reset_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            },
        }
        write_json(candidate_path, candidate_payload)
        inside = _inside_dir(candidate_path, output_dir)
        config_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": str(spec.get("source_repair_spec_id", "")),
                "repair_family": str(spec.get("repair_family", "")),
                "candidate_config_path": str(candidate_path),
                "reward_patch_count": len(rewards),
                "curriculum_patch_count": len(curricula),
                "guardrail_patch_scope": "global_guardrail_scope",
                "guardrail_patch_count": len(guardrail_refs),
                "mixed_collision_guardrail_required": mixed_required,
                "inside_run_dir": inside,
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "environment_reset_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
        patch_matrix_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": str(spec.get("source_repair_spec_id", "")),
                "reward_patch_ids": "|".join(str(row.get("patch_id", "")) for row in rewards),
                "curriculum_patch_ids": "|".join(str(row.get("patch_id", "")) for row in curricula),
                "reward_patch_count": len(rewards),
                "curriculum_patch_count": len(curricula),
                "candidate_config_path": str(candidate_path),
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
        guardrail_scope_rows.append(
            {
                "candidate_id": candidate_id,
                "guardrail_scope_id": "global_guardrail_scope",
                "guardrail_patch_count": len(guardrail_refs),
                "mixed_collision_guardrail_required": mixed_required,
                "candidate_config_path": str(candidate_path),
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )

    return config_rows, patch_matrix_rows, guardrail_scope_rows


def run_candidate_config_generation(
    *,
    summary_path: Path | str = DEFAULT_SUMMARY,
    application_plan_manifest_path: Path | str = DEFAULT_APPLICATION_PLAN_MANIFEST,
    candidate_application_specs_path: Path | str = DEFAULT_CANDIDATE_APPLICATION_SPECS,
    reward_patch_application_refs_path: Path | str = DEFAULT_REWARD_PATCH_REFS,
    curriculum_patch_application_refs_path: Path | str = DEFAULT_CURRICULUM_PATCH_REFS,
    guardrail_patch_application_refs_path: Path | str = DEFAULT_GUARDRAIL_PATCH_REFS,
    mixed_guarded_candidate_requirements_path: Path | str = DEFAULT_MIXED_REQUIREMENTS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    target_candidate_spec_count: int = DEFAULT_TARGET_CANDIDATE_SPEC_COUNT,
    target_reward_ref_count: int = DEFAULT_TARGET_REWARD_REF_COUNT,
    target_curriculum_ref_count: int = DEFAULT_TARGET_CURRICULUM_REF_COUNT,
    target_guardrail_ref_count: int = DEFAULT_TARGET_GUARDRAIL_REF_COUNT,
    target_mixed_requirement_count: int = DEFAULT_TARGET_MIXED_REQUIREMENT_COUNT,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_summary = read_json(summary_path)
    application_plan_manifest = read_json(application_plan_manifest_path)
    candidate_specs = read_csv_rows(candidate_application_specs_path)
    reward_refs = read_csv_rows(reward_patch_application_refs_path)
    curriculum_refs = read_csv_rows(curriculum_patch_application_refs_path)
    guardrail_refs = read_csv_rows(guardrail_patch_application_refs_path)
    mixed_requirements = read_csv_rows(mixed_guarded_candidate_requirements_path)
    config_rows, patch_matrix_rows, guardrail_scope_rows = build_candidate_configs(
        output_dir=output,
        candidate_specs=candidate_specs,
        reward_refs=reward_refs,
        curriculum_refs=curriculum_refs,
        guardrail_refs=guardrail_refs,
        mixed_requirements=mixed_requirements,
    )
    claim_rows = claim_boundary_rows()

    candidate_without_reward_overlay_count = sum(_int_value(row.get("reward_patch_count")) == 0 for row in config_rows)
    candidate_without_curriculum_overlay_count = sum(_int_value(row.get("curriculum_patch_count")) == 0 for row in config_rows)
    candidate_without_guardrail_overlay_count = sum(_int_value(row.get("guardrail_patch_count")) == 0 for row in config_rows)
    candidate_config_files_outside_run_dir_count = sum(not _bool(row.get("inside_run_dir")) for row in config_rows)
    active_config_overwrite_count = _flag_count(config_rows, "active_config_overwritten")
    loaded_into_environment_count = _flag_count(config_rows, "loaded_into_environment")
    environment_reset_count = _flag_count(config_rows, "environment_reset_started")
    repair_execution_count = _flag_count(config_rows, "repair_execution_started")
    training_count = _flag_count(config_rows, "training_started")
    ranking_admissible_count = _flag_count(config_rows, "ranking_admissible")
    winner_selected_count = _flag_count(config_rows, "winner_selected")
    active_config_patch_application_count = 0
    actor_input_change_count = 0
    hidden_oracle_feature_injection_count = 0
    profile_specific_tuning_count = 0

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
        "candidate_config_loaded": False,
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
        source_summary.get("result_class")
        == "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"
        and application_plan_manifest.get("result_class")
        == "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"
        and len(candidate_specs) == int(target_candidate_spec_count)
        and len(config_rows) == int(target_candidate_spec_count)
        and len(reward_refs) == int(target_reward_ref_count)
        and len(curriculum_refs) == int(target_curriculum_ref_count)
        and len(guardrail_refs) == int(target_guardrail_ref_count)
        and len(mixed_requirements) == int(target_mixed_requirement_count)
        and candidate_without_reward_overlay_count == 0
        and candidate_without_curriculum_overlay_count == 0
        and candidate_without_guardrail_overlay_count == 0
        and candidate_config_files_outside_run_dir_count == 0
        and active_config_overwrite_count == 0
        and active_config_patch_application_count == 0
        and loaded_into_environment_count == 0
        and environment_reset_count == 0
        and repair_execution_count == 0
        and training_count == 0
        and ranking_admissible_count == 0
        and winner_selected_count == 0
        and guardrail_violation_count == 0
    )

    manifest = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "source_artifacts": {
            "summary": str(summary_path),
            "application_plan_manifest": str(application_plan_manifest_path),
            "candidate_application_specs": str(candidate_application_specs_path),
            "reward_patch_application_refs": str(reward_patch_application_refs_path),
            "curriculum_patch_application_refs": str(curriculum_patch_application_refs_path),
            "guardrail_patch_application_refs": str(guardrail_patch_application_refs_path),
            "mixed_guarded_candidate_requirements": str(mixed_guarded_candidate_requirements_path),
        },
        "output_artifacts": {
            "candidate_config_rows": str(output / "candidate_config_rows.csv"),
            "candidate_patch_reference_matrix": str(output / "candidate_patch_reference_matrix.csv"),
            "candidate_guardrail_scope_rows": str(output / "candidate_guardrail_scope_rows.csv"),
            "candidate_configs_dir": str(output / "candidate_configs"),
            "active_config_safety_report": str(output / "active_config_safety_report.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
            "summary": str(output / "summary.json"),
        },
        "run_dir_only": True,
        "active_config_overwrite_allowed": False,
        "environment_loading_allowed": False,
        "source_counts": {
            "candidate_application_specs": len(candidate_specs),
            "reward_patch_application_refs": len(reward_refs),
            "curriculum_patch_application_refs": len(curriculum_refs),
            "guardrail_patch_application_refs": len(guardrail_refs),
            "mixed_guarded_candidate_requirements": len(mixed_requirements),
        },
        "output_counts": {
            "candidate_config_files": len(config_rows),
            "candidate_patch_reference_matrix_rows": len(patch_matrix_rows),
            "candidate_guardrail_scope_rows": len(guardrail_scope_rows),
        },
        "guardrail_flags": guardrail_flags,
    }
    safety_report = {
        "active_config_overwritten": False,
        "active_config_patch_application_count": active_config_patch_application_count,
        "candidate_config_file_written_count": len(config_rows),
        "candidate_config_files_outside_run_dir_count": candidate_config_files_outside_run_dir_count,
        "loaded_into_environment_count": loaded_into_environment_count,
        "environment_reset_started": False,
        "environment_rollout_started": False,
    }

    write_json(output / "candidate_config_generation_manifest.json", manifest)
    write_csv_rows(output / "candidate_config_rows.csv", config_rows, fieldnames=CANDIDATE_CONFIG_ROW_FIELDNAMES)
    write_csv_rows(output / "candidate_patch_reference_matrix.csv", patch_matrix_rows, fieldnames=PATCH_MATRIX_FIELDNAMES)
    write_csv_rows(output / "candidate_guardrail_scope_rows.csv", guardrail_scope_rows, fieldnames=GUARDRAIL_SCOPE_FIELDNAMES)
    write_json(output / "active_config_safety_report.json", safety_report)
    write_csv_rows(output / "claim_boundary.csv", claim_rows, fieldnames=CLAIM_FIELDNAMES)

    summary = {
        "result_class": RESULT_PASS if passes else RESULT_FAIL,
        "generated_at_utc": utc_timestamp(),
        "output_dir": str(output),
        "source_summary": str(summary_path),
        "source_application_plan_manifest": str(application_plan_manifest_path),
        "source_result_class": source_summary.get("result_class", ""),
        "source_candidate_application_spec_count": len(candidate_specs),
        "target_candidate_application_spec_count": int(target_candidate_spec_count),
        "candidate_config_file_written_count": len(config_rows),
        "candidate_config_files_outside_run_dir_count": candidate_config_files_outside_run_dir_count,
        "source_reward_patch_reference_count": len(reward_refs),
        "target_reward_patch_reference_count": int(target_reward_ref_count),
        "source_curriculum_patch_reference_count": len(curriculum_refs),
        "target_curriculum_patch_reference_count": int(target_curriculum_ref_count),
        "source_guardrail_patch_reference_count": len(guardrail_refs),
        "target_guardrail_patch_reference_count": int(target_guardrail_ref_count),
        "mixed_guarded_candidate_requirement_count": len(mixed_requirements),
        "target_mixed_guarded_candidate_requirement_count": int(target_mixed_requirement_count),
        "candidate_without_reward_overlay_count": candidate_without_reward_overlay_count,
        "candidate_without_curriculum_overlay_count": candidate_without_curriculum_overlay_count,
        "candidate_without_guardrail_overlay_count": candidate_without_guardrail_overlay_count,
        "candidate_repair_family_counts": _count_by(config_rows, "repair_family"),
        "claim_boundary_row_count": len(claim_rows),
        "active_config_overwrite_count": active_config_overwrite_count,
        "active_config_patch_application_count": active_config_patch_application_count,
        "loaded_into_environment_count": loaded_into_environment_count,
        "environment_reset_count": environment_reset_count,
        "actor_input_change_count": actor_input_change_count,
        "hidden_oracle_feature_injection_count": hidden_oracle_feature_injection_count,
        "profile_specific_tuning_count": profile_specific_tuning_count,
        "repair_execution_count": repair_execution_count,
        "training_count": training_count,
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
            "candidate_config_generation_manifest": str(output / "candidate_config_generation_manifest.json"),
            "candidate_config_rows": str(output / "candidate_config_rows.csv"),
            "candidate_patch_reference_matrix": str(output / "candidate_patch_reference_matrix.csv"),
            "candidate_guardrail_scope_rows": str(output / "candidate_guardrail_scope_rows.csv"),
            "candidate_configs_dir": str(output / "candidate_configs"),
            "active_config_safety_report": str(output / "active_config_safety_report.json"),
            "claim_boundary": str(output / "claim_boundary.csv"),
        },
        "next_blocker": str(next_blocker),
    }
    write_json(output / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--application-plan-manifest", type=Path, default=DEFAULT_APPLICATION_PLAN_MANIFEST)
    parser.add_argument("--candidate-application-specs", type=Path, default=DEFAULT_CANDIDATE_APPLICATION_SPECS)
    parser.add_argument("--reward-patch-application-refs", type=Path, default=DEFAULT_REWARD_PATCH_REFS)
    parser.add_argument("--curriculum-patch-application-refs", type=Path, default=DEFAULT_CURRICULUM_PATCH_REFS)
    parser.add_argument("--guardrail-patch-application-refs", type=Path, default=DEFAULT_GUARDRAIL_PATCH_REFS)
    parser.add_argument("--mixed-guarded-candidate-requirements", type=Path, default=DEFAULT_MIXED_REQUIREMENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-candidate-spec-count", type=int, default=DEFAULT_TARGET_CANDIDATE_SPEC_COUNT)
    parser.add_argument("--target-reward-ref-count", type=int, default=DEFAULT_TARGET_REWARD_REF_COUNT)
    parser.add_argument("--target-curriculum-ref-count", type=int, default=DEFAULT_TARGET_CURRICULUM_REF_COUNT)
    parser.add_argument("--target-guardrail-ref-count", type=int, default=DEFAULT_TARGET_GUARDRAIL_REF_COUNT)
    parser.add_argument("--target-mixed-requirement-count", type=int, default=DEFAULT_TARGET_MIXED_REQUIREMENT_COUNT)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = run_candidate_config_generation(
        summary_path=args.summary,
        application_plan_manifest_path=args.application_plan_manifest,
        candidate_application_specs_path=args.candidate_application_specs,
        reward_patch_application_refs_path=args.reward_patch_application_refs,
        curriculum_patch_application_refs_path=args.curriculum_patch_application_refs,
        guardrail_patch_application_refs_path=args.guardrail_patch_application_refs,
        mixed_guarded_candidate_requirements_path=args.mixed_guarded_candidate_requirements,
        output_dir=args.output_dir,
        target_candidate_spec_count=int(args.target_candidate_spec_count),
        target_reward_ref_count=int(args.target_reward_ref_count),
        target_curriculum_ref_count=int(args.target_curriculum_ref_count),
        target_guardrail_ref_count=int(args.target_guardrail_ref_count),
        target_mixed_requirement_count=int(args.target_mixed_requirement_count),
        next_blocker=str(args.next_blocker),
    )
    print(f"summary={Path(args.output_dir) / 'summary.json'}")
    print(f"result_class={summary['result_class']}")
    print(f"source_candidate_application_spec_count={summary['source_candidate_application_spec_count']}")
    print(f"candidate_config_file_written_count={summary['candidate_config_file_written_count']}")
    print(f"candidate_config_files_outside_run_dir_count={summary['candidate_config_files_outside_run_dir_count']}")
    print(f"source_reward_patch_reference_count={summary['source_reward_patch_reference_count']}")
    print(f"source_curriculum_patch_reference_count={summary['source_curriculum_patch_reference_count']}")
    print(f"source_guardrail_patch_reference_count={summary['source_guardrail_patch_reference_count']}")
    print(f"mixed_guarded_candidate_requirement_count={summary['mixed_guarded_candidate_requirement_count']}")
    print(f"guardrail_violation_count={summary['guardrail_violation_count']}")
    return 0 if str(summary["result_class"]).endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
