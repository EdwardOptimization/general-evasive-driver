from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_offtrack_support_repair_templates as templates
from autodrift.artifacts import read_json, write_csv_rows


def _comparison_row(surface: str) -> dict[str, object]:
    return {
        "feasibility_tier_id": "tier_c_boundary_near_miss",
        "source_role_semantics": "stable_aeb",
        "surface_variant": surface,
        "sampled_obstacle_label": "aeb_feasible",
        "episode_count": 24,
        "success_count": 5,
        "collision_count": 1,
        "offtrack_outcome_count": 18,
        "profiles_with_success": "L1_one_step;L3_online_gru",
        "support_label": "candidate_support",
    }


def _success_row(index: int, *, tier: str, role: str, surface: str, label: str) -> dict[str, object]:
    speed = 12 + (index % 4) * 6
    mu = ("0p25", "0p4", "0p6", "0p8")[index % 4]
    source_id = f"tqsr_v0_{tier}_{role}_{surface}_v{speed}_mu{mu}"
    return {
        "workload_id": f"{source_id}::L1_one_step",
        "candidate_source_id": source_id,
        "task_source_id": f"exec_{source_id}",
        "profile_name": "L1_one_step",
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "surface_variant": surface,
        "sampled_obstacle_label": label,
        "target_boundary_mode": "near_miss",
        "target_support_mode": "boundary_mixed_support",
        "selected_accepted_cell_rule": "positive_support_max_threshold",
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "",
        "min_clearance_margin": 1.0,
        "return": 10.0,
        "steps": 20,
    }


def _offtrack_row(index: int, *, tier: str, role: str, surface: str, label: str) -> dict[str, object]:
    return {
        "slice_kind": "outcome_by_profile_role",
        "dominance_type": "offtrack",
        "episode_count": 16,
        "success_count": 0,
        "collision_count": 1,
        "offtrack_outcome_count": 15,
        "collision_rate": 0.0625,
        "offtrack_outcome_rate": 0.9375,
        "support_label": "no_support",
        "profile_name": "L2_window_13",
        "feasibility_tier_id": tier,
        "source_role_semantics": role,
        "surface_variant": surface,
        "sampled_obstacle_label": label,
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    comparison_path = tmp_path / "comparison.csv"
    success_path = tmp_path / "success.csv"
    offtrack_path = tmp_path / "offtrack.csv"
    write_csv_rows(comparison_path, [_comparison_row("post_friction_step"), _comparison_row("steady_surface")])
    success_rows = []
    for index in range(32):
        success_rows.append(
            _success_row(
                index,
                tier=(
                    "tier_b_feasible_emergency",
                    "tier_c_boundary_near_miss",
                    "tier_d_handling_limit_drift_required",
                )[index % 3],
                role=("stable_aeb", "stable_aes_only", "drift_required_recovery")[index % 3],
                surface=("post_friction_step", "steady_surface")[index % 2],
                label=("aeb_feasible", "aes_feasible", "drift_required")[index % 3],
            )
        )
    for index in range(8):
        success_rows.append(
            _success_row(
                100 + index,
                tier="tier_e_mitigation_only",
                role="unavoidable_mitigation",
                surface=("post_friction_step", "steady_surface")[index % 2],
                label="unavoidable",
            )
        )
    write_csv_rows(success_path, success_rows)
    write_csv_rows(
        offtrack_path,
        [
            _offtrack_row(
                index,
                tier=("tier_b_feasible_emergency", "tier_c_boundary_near_miss")[index % 2],
                role=("stable_aeb", "stable_aes_only")[index % 2],
                surface=("post_friction_step", "steady_surface")[index % 2],
                label=("aeb_feasible", "aes_feasible")[index % 2],
            )
            for index in range(8)
        ],
    )
    return success_path, comparison_path, offtrack_path


def test_offtrack_support_template_generator_writes_exact_counts(tmp_path: Path) -> None:
    success_path, comparison_path, offtrack_path = _write_inputs(tmp_path)
    output = tmp_path / "repair_candidates.json"

    artifact = templates.build_repair_template_artifact(
        success_source_rows_path=success_path,
        comparison_support_candidates_path=comparison_path,
        offtrack_dominance_rows_path=offtrack_path,
        output_path=output,
    )

    summary = artifact["summary"]
    rows = artifact["repair_candidate_sources"]
    assert summary["result_class"] == "task_quality_offtrack_support_repair_templates_pass"
    assert summary["candidate_source_count"] == 160
    assert summary["source_kind_counts"] == templates.SOURCE_KIND_TARGETS
    assert summary["source_split_counts"] == templates.SPLIT_TARGETS
    assert summary["paper_holdout_candidate_count"] == 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["v2_ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert len({row["repair_candidate_id"] for row in rows}) == 160
    assert {row["source_split"] for row in rows} == {"public_debug", "public_gate"}
    assert all(row["profile_specific_tuning"] is False for row in rows)
    assert output.exists()
    persisted = read_json(output)
    assert persisted["summary"]["candidate_source_count"] == 160


def test_offtrack_support_template_generator_fails_when_required_anchor_missing(tmp_path: Path) -> None:
    success_path, _comparison_path, offtrack_path = _write_inputs(tmp_path)
    empty_comparison = tmp_path / "empty_comparison.csv"
    write_csv_rows(empty_comparison, [], fieldnames=["feasibility_tier_id"])

    try:
        templates.build_repair_template_artifact(
            success_source_rows_path=success_path,
            comparison_support_candidates_path=empty_comparison,
            offtrack_dominance_rows_path=offtrack_path,
            output_path=tmp_path / "repair_candidates.json",
        )
    except ValueError as exc:
        assert "anchor_neighborhood" in str(exc)
    else:
        raise AssertionError("missing comparison anchors should fail closed")
