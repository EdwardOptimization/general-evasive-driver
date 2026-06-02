from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation import (
    read_csv_rows,
    run_candidate_config_generation,
)


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
MIXED_FIELDNAMES = [
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


def _candidate(candidate_id: str, spec_id: str, *, mixed: bool = False) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair" if mixed else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if mixed else "R0_stable_avoidable",
        "priority_tier": "P1",
        "reward_patch_count": 3,
        "curriculum_patch_count": 1,
        "guardrail_patch_scope": "global_guardrail_scope",
        "mixed_collision_guardrail_required": mixed,
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


def _patch_ref(candidate_id: str, spec_id: str, index: int, family: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_repair_spec_id": spec_id,
        "patch_id": f"{family}_{candidate_id}_{index}",
        "patch_family": family,
        "target_namespace": f"candidate_{family}_overlay",
        "target_key": f"{family}.target_{index}",
        "delta_value": 0.1,
        "config_patch_applied": False,
        "active_config_overwritten": False,
        "candidate_config_file_written": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _guardrail(index: int) -> dict[str, object]:
    return {
        "guardrail_scope_id": "global_guardrail_scope",
        "patch_id": f"guardrail_patch_{index}",
        "source_constraint_id": f"guardrail_constraint_{index}",
        "source_repair_spec_id": f"guardrail_spec_{index}",
        "repair_family": "collision_guardrail_constraint",
        "constraint_family": "collision",
        "constraint_metric": "collision_rate_not_worse",
        "target_namespace": "candidate_guardrail_overlay",
        "target_key": "guardrail.collision_rate_not_worse",
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


def _mixed(candidate_id: str, spec_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance",
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


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    manifest_path = tmp_path / "application_plan_manifest.json"
    candidate_path = tmp_path / "candidate_application_specs.csv"
    reward_path = tmp_path / "reward_patch_refs.csv"
    curriculum_path = tmp_path / "curriculum_patch_refs.csv"
    guardrail_path = tmp_path / "guardrail_patch_refs.csv"
    mixed_path = tmp_path / "mixed_requirements.csv"

    write_json(summary_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"})
    write_json(manifest_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"})
    candidate_rows = [
        _candidate("candidate_ordinary", "ordinary_0000"),
        _candidate("candidate_mixed", "mixed_0000", mixed=True),
    ]
    reward_rows = [
        *[_patch_ref("candidate_ordinary", "ordinary_0000", index, "reward") for index in range(3)],
        *[_patch_ref("candidate_mixed", "mixed_0000", index, "reward") for index in range(3)],
    ]
    curriculum_rows = [
        _patch_ref("candidate_ordinary", "ordinary_0000", 0, "curriculum"),
        _patch_ref("candidate_mixed", "mixed_0000", 0, "curriculum"),
    ]
    guardrail_rows = [_guardrail(0), _guardrail(1), _guardrail(2)]
    mixed_rows = [_mixed("candidate_mixed", "mixed_0000")]
    write_csv_rows(candidate_path, candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(reward_path, reward_rows, fieldnames=PATCH_REF_FIELDNAMES)
    write_csv_rows(curriculum_path, curriculum_rows, fieldnames=PATCH_REF_FIELDNAMES)
    write_csv_rows(guardrail_path, guardrail_rows, fieldnames=GUARDRAIL_REF_FIELDNAMES)
    write_csv_rows(mixed_path, mixed_rows, fieldnames=MIXED_FIELDNAMES)
    return summary_path, manifest_path, candidate_path, reward_path, curriculum_path, guardrail_path, mixed_path


def test_candidate_config_generation_writes_configs_under_run_dir_only(tmp_path: Path) -> None:
    summary_path, manifest_path, candidate_path, reward_path, curriculum_path, guardrail_path, mixed_path = _inputs(tmp_path)

    summary = run_candidate_config_generation(
        summary_path=summary_path,
        application_plan_manifest_path=manifest_path,
        candidate_application_specs_path=candidate_path,
        reward_patch_application_refs_path=reward_path,
        curriculum_patch_application_refs_path=curriculum_path,
        guardrail_patch_application_refs_path=guardrail_path,
        mixed_guarded_candidate_requirements_path=mixed_path,
        output_dir=tmp_path / "out",
        target_candidate_spec_count=2,
        target_reward_ref_count=6,
        target_curriculum_ref_count=2,
        target_guardrail_ref_count=3,
        target_mixed_requirement_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"
    assert summary["source_candidate_application_spec_count"] == 2
    assert summary["candidate_config_file_written_count"] == 2
    assert summary["candidate_config_files_outside_run_dir_count"] == 0
    assert summary["source_reward_patch_reference_count"] == 6
    assert summary["source_curriculum_patch_reference_count"] == 2
    assert summary["source_guardrail_patch_reference_count"] == 3
    assert summary["mixed_guarded_candidate_requirement_count"] == 1
    assert summary["candidate_without_reward_overlay_count"] == 0
    assert summary["candidate_without_curriculum_overlay_count"] == 0
    assert summary["candidate_without_guardrail_overlay_count"] == 0
    assert summary["active_config_overwrite_count"] == 0
    assert summary["active_config_patch_application_count"] == 0
    assert summary["loaded_into_environment_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    rows = read_csv_rows(tmp_path / "out" / "candidate_config_rows.csv")
    assert len(rows) == 2
    assert {row["inside_run_dir"] for row in rows} == {"True"}

    payload = read_json(tmp_path / "out" / "candidate_configs" / "candidate_mixed.json")
    assert payload["mixed_guarded_requirements"]["collision_guardrail_required"] is True
    assert payload["claim_boundary"]["loaded_into_environment"] is False

    safety = read_json(tmp_path / "out" / "active_config_safety_report.json")
    assert safety["active_config_overwritten"] is False
    assert safety["candidate_config_file_written_count"] == 2


def test_candidate_config_generation_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    summary_path, manifest_path, candidate_path, reward_path, curriculum_path, guardrail_path, mixed_path = _inputs(tmp_path)

    summary = run_candidate_config_generation(
        summary_path=summary_path,
        application_plan_manifest_path=manifest_path,
        candidate_application_specs_path=candidate_path,
        reward_patch_application_refs_path=reward_path,
        curriculum_patch_application_refs_path=curriculum_path,
        guardrail_patch_application_refs_path=guardrail_path,
        mixed_guarded_candidate_requirements_path=mixed_path,
        output_dir=tmp_path / "out",
        target_candidate_spec_count=3,
        target_reward_ref_count=6,
        target_curriculum_ref_count=2,
        target_guardrail_ref_count=3,
        target_mixed_requirement_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_incomplete_or_fail"
    assert summary["source_candidate_application_spec_count"] == 2
    assert summary["target_candidate_application_spec_count"] == 3
    assert summary["active_config_overwritten"] is False
    assert summary["training_repair_success_claim_made"] is False
