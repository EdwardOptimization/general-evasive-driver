from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_outcome_support_repair_templates as templates
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _success_row(index: int, *, role: str = "stable_aes_only", label: str = "aes_feasible") -> dict[str, object]:
    return {
        "workload_id": f"success_{index}::L1_one_step",
        "candidate_source_id": f"success_candidate_{index}",
        "task_source_id": f"success_task_{index}",
        "profile_name": "L1_one_step",
        "repair_source_kind": "success_stabilizer",
        "selection_quota_name": "success_support",
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "tier_b_feasible_emergency",
        "parent_surface_variant": "steady_surface",
        "normalized_surface_variant": "steady_surface",
        "sampled_obstacle_label": label,
        "base_geometry_source": "unit_success",
        "outcome_bucket": "success_obstacle_pass",
        "termination_reason": "",
        "speed_ref": 18.0,
        "mu": 0.4,
    }


def _dominance_row(
    index: int,
    *,
    dominance_type: str,
    repair_source_kind: str,
    role: str,
    label: str,
) -> dict[str, object]:
    return {
        "slice_kind": "outcome_by_repair_source_kind",
        "dominance_type": dominance_type,
        "episode_count": 32,
        "success_count": 0 if dominance_type == "offtrack" else 5,
        "collision_count": 0 if dominance_type == "offtrack" else 27,
        "offtrack_outcome_count": 32 if dominance_type == "offtrack" else 0,
        "collision_rate": 0.0 if dominance_type == "offtrack" else 0.84,
        "offtrack_outcome_rate": 1.0 if dominance_type == "offtrack" else 0.0,
        "support_label": "no_support",
        "profile_name": "",
        "repair_source_kind": repair_source_kind,
        "source_role_semantics": role,
        "parent_feasibility_tier_id": (
            "tier_not_applicable_offtrack_boundary_relief"
            if repair_source_kind == "offtrack_boundary_relief"
            else "tier_c_boundary_near_miss"
        ),
        "normalized_surface_variant": (
            "relief_surface_unspecified"
            if repair_source_kind == "offtrack_boundary_relief"
            else "steady_surface"
        ),
        "sampled_obstacle_label": label,
        "candidate_source_id": f"{repair_source_kind}_{dominance_type}_{index}",
    }


def _write_localization_artifacts(tmp_path: Path) -> Path:
    output_dir = tmp_path / "loc"
    output_dir.mkdir()
    success_rows = [_success_row(index) for index in range(16)]
    success_rows.extend(_success_row(100 + index, role="unavoidable_mitigation", label="unavoidable") for index in range(8))
    offtrack_rows = [
        _dominance_row(
            index,
            dominance_type="offtrack",
            repair_source_kind=("anchor_neighborhood" if index < 4 else "offtrack_boundary_relief"),
            role=("stable_aeb" if index < 4 else "stable_aes_only"),
            label=("aeb_feasible" if index < 4 else "aes_feasible"),
        )
        for index in range(8)
    ]
    collision_rows = [
        _dominance_row(
            index,
            dominance_type="collision",
            repair_source_kind="mitigation_isolation_check",
            role="unavoidable_mitigation",
            label="unavoidable",
        )
        for index in range(8)
    ]
    write_csv_rows(output_dir / "success_source_rows.csv", success_rows)
    write_csv_rows(output_dir / "offtrack_dominance_rows.csv", offtrack_rows)
    write_csv_rows(output_dir / "collision_dominance_rows.csv", collision_rows)
    summary_path = output_dir / "summary.json"
    write_json(
        summary_path,
        {
            "result_class": "task_quality_calibrated_repaired_measured_outcome_localization_pass",
            "artifacts": {
                "success_source_rows": str(output_dir / "success_source_rows.csv"),
                "offtrack_dominance_rows": str(output_dir / "offtrack_dominance_rows.csv"),
                "collision_dominance_rows": str(output_dir / "collision_dominance_rows.csv"),
            },
        },
    )
    return summary_path


def test_calibrated_outcome_support_template_generator_writes_exact_counts(tmp_path: Path) -> None:
    summary_path = _write_localization_artifacts(tmp_path)
    output = tmp_path / "repair_candidates.json"

    artifact = templates.build_repair_template_artifact(localization_summary_path=summary_path, output_path=output)

    summary = artifact["summary"]
    rows = artifact["repair_candidate_sources"]
    assert summary["result_class"] == "task_quality_calibrated_outcome_support_repair_templates_pass"
    assert summary["candidate_source_count"] == 192
    assert summary["repair_axis_counts"] == templates.REPAIR_AXIS_TARGETS
    assert summary["source_split_counts"] == templates.SPLIT_TARGETS
    assert summary["paper_holdout_candidate_count"] == 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["v2_ranking_admissible_by_default_count"] == 0
    assert summary["profile_specific_tuning_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert len({row["repair_candidate_id"] for row in rows}) == 192
    assert {row["source_split"] for row in rows} == {"public_debug", "public_gate"}
    assert all(row["profile_specific_tuning"] is False for row in rows)
    assert output.exists()
    persisted = read_json(output)
    assert persisted["summary"]["candidate_source_count"] == 192


def test_calibrated_outcome_support_template_generator_fails_when_required_axis_missing(tmp_path: Path) -> None:
    summary_path = _write_localization_artifacts(tmp_path)
    summary = read_json(summary_path)
    empty_offtrack = tmp_path / "empty_offtrack.csv"
    write_csv_rows(empty_offtrack, [], fieldnames=["repair_source_kind"])
    summary["artifacts"]["offtrack_dominance_rows"] = str(empty_offtrack)
    write_json(summary_path, summary)

    try:
        templates.build_repair_template_artifact(
            localization_summary_path=summary_path,
            output_path=tmp_path / "repair_candidates.json",
        )
    except ValueError as exc:
        assert "offtrack_anchor_relief" in str(exc)
    else:
        raise AssertionError("missing offtrack anchors should fail closed")
