from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization import (
    read_csv_rows,
    run_config_patch_materialization,
)


REWARD_FIELDNAMES = [
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


def _reward(plan_id: str, spec_id: str, *, collision: bool = False) -> dict[str, object]:
    return {
        "plan_row_id": plan_id,
        "repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair" if collision else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if collision else "R0_stable_avoidable",
        "priority_tier": "P1",
        "target_metric": "offtrack_rate_down",
        "guardrail_metric": "collision_rate_not_worse" if collision else "collision_rate_monitor",
        "offtrack_margin_reward_delta": 0.08 if collision else 0.10,
        "recovery_window_reward_delta": 0.06 if collision else 0.07,
        "boundary_overshoot_penalty_delta": 0.04 if collision else 0.05,
        "collision_guardrail_required": collision,
        "active_config_overwritten": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _curriculum(plan_id: str, spec_id: str, *, collision: bool = False) -> dict[str, object]:
    return {
        "plan_row_id": plan_id,
        "repair_spec_id": spec_id,
        "repair_family": "guarded_offtrack_containment_repair" if collision else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if collision else "R0_stable_avoidable",
        "priority_tier": "P1",
        "sampling_weight_multiplier": 1.25 if collision else 1.5,
        "collision_guardrail_required": collision,
        "profile_specific_tuning": False,
        "active_config_overwritten": False,
        "repair_execution_started": False,
        "training_started": False,
        "ranking_admissible": False,
        "winner_selected": False,
    }


def _guardrail(
    constraint_id: str,
    spec_id: str,
    family: str,
    metric: str,
    *,
    repair_family: str = "collision_guardrail_constraint",
) -> dict[str, object]:
    return {
        "constraint_id": constraint_id,
        "repair_spec_id": spec_id,
        "repair_family": repair_family,
        "source_group": "collision_guardrail",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance",
        "constraint_family": family,
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


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    summary_path = tmp_path / "summary.json"
    repair_plan_path = tmp_path / "repair_plan.json"
    reward_path = tmp_path / "reward_delta_rows.csv"
    curriculum_path = tmp_path / "curriculum_weight_rows.csv"
    guardrail_path = tmp_path / "guardrail_constraint_rows.csv"
    mixed_path = tmp_path / "mixed_guarded_constraint_rows.csv"

    write_json(summary_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"})
    write_json(repair_plan_path, {"result_class": "current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization_pass"})
    reward_rows = [
        _reward("reward_delta_0000", "ordinary_0000"),
        _reward("reward_delta_0001", "mixed_0000", collision=True),
    ]
    curriculum_rows = [
        _curriculum("curriculum_weight_0000", "ordinary_0000"),
        _curriculum("curriculum_weight_0001", "mixed_0000", collision=True),
    ]
    guardrail_rows = [
        _guardrail(
            "guardrail_constraint_0000",
            "mixed_0000",
            "collision",
            "collision_rate_not_worse",
            repair_family="guarded_offtrack_containment_repair",
        ),
        _guardrail("guardrail_constraint_0001", "r4_0000", "r4_mitigation_semantics", "mitigation_semantics_preserved"),
        _guardrail("guardrail_constraint_0002", "diagnostic_0000", "diagnostic_no_ranking", "no_ranking_no_winner_claims"),
    ]
    write_csv_rows(reward_path, reward_rows, fieldnames=REWARD_FIELDNAMES)
    write_csv_rows(curriculum_path, curriculum_rows, fieldnames=CURRICULUM_FIELDNAMES)
    write_csv_rows(guardrail_path, guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(mixed_path, [guardrail_rows[0]], fieldnames=GUARDRAIL_FIELDNAMES)
    return summary_path, repair_plan_path, reward_path, curriculum_path, guardrail_path, mixed_path


def test_config_patch_materialization_writes_overlay_artifacts_without_application(tmp_path: Path) -> None:
    summary_path, repair_plan_path, reward_path, curriculum_path, guardrail_path, mixed_path = _inputs(tmp_path)

    summary = run_config_patch_materialization(
        summary_path=summary_path,
        repair_plan_path=repair_plan_path,
        reward_delta_rows_path=reward_path,
        curriculum_weight_rows_path=curriculum_path,
        guardrail_constraint_rows_path=guardrail_path,
        mixed_guarded_constraint_rows_path=mixed_path,
        output_dir=tmp_path / "out",
        target_reward_delta_row_count=2,
        target_curriculum_weight_row_count=2,
        target_guardrail_constraint_row_count=3,
        target_mixed_guarded_constraint_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass"
    assert summary["source_reward_delta_row_count"] == 2
    assert summary["source_curriculum_weight_row_count"] == 2
    assert summary["source_guardrail_constraint_row_count"] == 3
    assert summary["source_mixed_guarded_constraint_row_count"] == 1
    assert summary["reward_config_patch_row_count"] == 6
    assert summary["curriculum_config_patch_row_count"] == 2
    assert summary["guardrail_config_patch_row_count"] == 3
    assert summary["active_config_overwrite_count"] == 0
    assert summary["actor_input_change_count"] == 0
    assert summary["hidden_oracle_feature_injection_count"] == 0
    assert summary["profile_specific_tuning_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["winner_selected_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["repair_execution_started"] is False
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["current_sim_verdict_claim_made"] is False

    reward_patches = read_csv_rows(tmp_path / "out" / "reward_config_patch_rows.csv")
    assert {row["target_namespace"] for row in reward_patches} == {"candidate_reward_overlay"}
    assert {row["target_key"] for row in reward_patches} == {
        "reward.offtrack_margin_weight_delta",
        "reward.recovery_window_weight_delta",
        "reward.boundary_overshoot_penalty_delta",
    }

    guardrail_patches = read_csv_rows(tmp_path / "out" / "guardrail_config_patch_rows.csv")
    assert {row["target_namespace"] for row in guardrail_patches} == {"candidate_guardrail_overlay"}
    assert "guardrail.collision_rate_not_worse" in {row["target_key"] for row in guardrail_patches}

    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "active_config_overwrite,False" in claim_boundary
    assert "current_sim_verdict,False" in claim_boundary

    manifest = read_json(tmp_path / "out" / "config_patch_manifest.json")
    assert manifest["overlay_only"] is True
    assert manifest["active_config_overwrite_allowed"] is False

    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["artifacts"]["config_patch_manifest"].endswith("config_patch_manifest.json")


def test_config_patch_materialization_fails_closed_on_source_count_mismatch(tmp_path: Path) -> None:
    summary_path, repair_plan_path, reward_path, curriculum_path, guardrail_path, mixed_path = _inputs(tmp_path)

    summary = run_config_patch_materialization(
        summary_path=summary_path,
        repair_plan_path=repair_plan_path,
        reward_delta_rows_path=reward_path,
        curriculum_weight_rows_path=curriculum_path,
        guardrail_constraint_rows_path=guardrail_path,
        mixed_guarded_constraint_rows_path=mixed_path,
        output_dir=tmp_path / "out",
        target_reward_delta_row_count=3,
        target_curriculum_weight_row_count=2,
        target_guardrail_constraint_row_count=3,
        target_mixed_guarded_constraint_row_count=1,
    )

    assert summary["result_class"] == "current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_incomplete_or_fail"
    assert summary["source_reward_delta_row_count"] == 2
    assert summary["target_reward_delta_row_count"] == 3
    assert summary["active_config_overwritten"] is False
    assert summary["repair_execution_started"] is False
    assert summary["training_repair_success_claim_made"] is False
