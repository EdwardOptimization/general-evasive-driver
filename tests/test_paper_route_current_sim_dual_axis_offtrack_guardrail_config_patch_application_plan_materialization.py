from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization import (
    read_csv_rows,
    run_application_plan_materialization,
)


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


def _reward_patch(spec_id: str, index: int, *, mixed: bool = False) -> dict[str, object]:
    return {
        "patch_id": f"reward_patch_{spec_id}_{index}",
        "patch_family": "reward_delta",
        "source_plan_row_id": f"reward_delta_{spec_id}",
        "source_repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair" if mixed else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if mixed else "R0_stable_avoidable",
        "priority_tier": "P1",
        "target_namespace": "candidate_reward_overlay",
        "target_key": [
            "reward.offtrack_margin_weight_delta",
            "reward.recovery_window_weight_delta",
            "reward.boundary_overshoot_penalty_delta",
        ][index],
        "delta_value": 0.1,
        "collision_guardrail_required": mixed,
        "active_config_overwritten": False,
        "actor_input_change": False,
        "hidden_oracle_feature_injection": False,
        "profile_specific_tuning": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _curriculum_patch(spec_id: str, *, mixed: bool = False) -> dict[str, object]:
    return {
        "patch_id": f"curriculum_patch_{spec_id}",
        "patch_family": "curriculum_weight",
        "source_plan_row_id": f"curriculum_weight_{spec_id}",
        "source_repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair" if mixed else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if mixed else "R0_stable_avoidable",
        "priority_tier": "P1",
        "target_namespace": "candidate_curriculum_overlay",
        "target_key": "curriculum.source_slice_sampling_weight_multiplier",
        "delta_value": 1.5,
        "collision_guardrail_required": mixed,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "actor_input_change": False,
        "hidden_oracle_feature_injection": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _guardrail_patch(index: int, family: str, metric: str) -> dict[str, object]:
    return {
        "patch_id": f"guardrail_patch_{index:04d}",
        "patch_family": "guardrail_constraint",
        "source_constraint_id": f"guardrail_constraint_{index:04d}",
        "source_repair_spec_id": f"guardrail_spec_{index:04d}",
        "repair_family": "collision_guardrail_constraint",
        "source_group": "collision_guardrail",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance",
        "constraint_family": family,
        "constraint_metric": metric,
        "target_namespace": "candidate_guardrail_overlay",
        "target_key": f"guardrail.{metric}",
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


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    manifest_path = tmp_path / "config_patch_manifest.json"
    reward_path = tmp_path / "reward_config_patch_rows.csv"
    curriculum_path = tmp_path / "curriculum_config_patch_rows.csv"
    guardrail_path = tmp_path / "guardrail_config_patch_rows.csv"

    write_json(summary_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"})
    write_json(manifest_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"})
    reward_rows = [
        *[_reward_patch("ordinary_0000", index) for index in range(3)],
        *[_reward_patch("mixed_0000", index, mixed=True) for index in range(3)],
    ]
    curriculum_rows = [
        _curriculum_patch("ordinary_0000"),
        _curriculum_patch("mixed_0000", mixed=True),
    ]
    guardrail_rows = [
        _guardrail_patch(0, "collision", "collision_rate_not_worse"),
        _guardrail_patch(1, "r4_mitigation_semantics", "r4_mitigation_semantics_preserved"),
        _guardrail_patch(2, "diagnostic_no_ranking", "no_ranking_no_winner_claims"),
    ]
    write_csv_rows(reward_path, reward_rows, fieldnames=REWARD_PATCH_FIELDNAMES)
    write_csv_rows(curriculum_path, curriculum_rows, fieldnames=CURRICULUM_PATCH_FIELDNAMES)
    write_csv_rows(guardrail_path, guardrail_rows, fieldnames=GUARDRAIL_PATCH_FIELDNAMES)
    return summary_path, manifest_path, reward_path, curriculum_path, guardrail_path


def test_application_plan_materialization_writes_plan_artifacts_without_applying_patches(tmp_path: Path) -> None:
    summary_path, manifest_path, reward_path, curriculum_path, guardrail_path = _inputs(tmp_path)

    summary = run_application_plan_materialization(
        summary_path=summary_path,
        config_patch_manifest_path=manifest_path,
        reward_config_patch_rows_path=reward_path,
        curriculum_config_patch_rows_path=curriculum_path,
        guardrail_config_patch_rows_path=guardrail_path,
        output_dir=tmp_path / "out",
        target_reward_patch_row_count=6,
        target_curriculum_patch_row_count=2,
        target_guardrail_patch_row_count=3,
        target_candidate_application_spec_count=2,
        target_mixed_guarded_candidate_requirement_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass"
    assert summary["source_reward_config_patch_row_count"] == 6
    assert summary["source_curriculum_config_patch_row_count"] == 2
    assert summary["source_guardrail_config_patch_row_count"] == 3
    assert summary["candidate_application_spec_count"] == 2
    assert summary["reward_patch_reference_count"] == 6
    assert summary["curriculum_patch_reference_count"] == 2
    assert summary["guardrail_patch_reference_count"] == 3
    assert summary["mixed_guarded_candidate_requirement_count"] == 1
    assert summary["candidate_without_reward_patch_count"] == 0
    assert summary["candidate_without_curriculum_patch_count"] == 0
    assert summary["candidate_without_guardrail_scope_count"] == 0
    assert summary["active_config_overwrite_count"] == 0
    assert summary["config_patch_applied_count"] == 0
    assert summary["candidate_config_file_written_count"] == 0
    assert summary["actor_input_change_count"] == 0
    assert summary["hidden_oracle_feature_injection_count"] == 0
    assert summary["profile_specific_tuning_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    candidates = read_csv_rows(tmp_path / "out" / "candidate_application_specs.csv")
    assert len(candidates) == 2
    assert {row["reward_patch_count"] for row in candidates} == {"3"}
    assert {row["curriculum_patch_count"] for row in candidates} == {"1"}

    mixed_requirements = read_csv_rows(tmp_path / "out" / "mixed_guarded_candidate_requirements.csv")
    assert len(mixed_requirements) == 1
    assert mixed_requirements[0]["collision_guardrail_required"] == "True"

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "config_patch_application,False" in claim_boundary
    assert "candidate_config_file_generation,False" in claim_boundary

    manifest = read_json(tmp_path / "out" / "application_plan_manifest.json")
    assert manifest["application_semantics"]["patches_are_referenced_not_applied"] is True
    assert manifest["application_semantics"]["candidate_config_files_written"] is False

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["application_plan_manifest"].endswith("application_plan_manifest.json")


def test_application_plan_materialization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    summary_path, manifest_path, reward_path, curriculum_path, guardrail_path = _inputs(tmp_path)

    summary = run_application_plan_materialization(
        summary_path=summary_path,
        config_patch_manifest_path=manifest_path,
        reward_config_patch_rows_path=reward_path,
        curriculum_config_patch_rows_path=curriculum_path,
        guardrail_config_patch_rows_path=guardrail_path,
        output_dir=tmp_path / "out",
        target_reward_patch_row_count=7,
        target_curriculum_patch_row_count=2,
        target_guardrail_patch_row_count=3,
        target_candidate_application_spec_count=2,
        target_mixed_guarded_candidate_requirement_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_incomplete_or_fail"
    assert summary["source_reward_config_patch_row_count"] == 6
    assert summary["target_reward_config_patch_row_count"] == 7
    assert summary["active_config_overwritten"] is False
    assert summary["config_patch_applied"] is False
    assert summary["training_repair_success_claim_made"] is False
