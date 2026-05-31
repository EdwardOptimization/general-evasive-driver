from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_outcome_support_materialization_preflight as preflight
from autodrift.artifacts import read_json, write_csv_rows
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


def _label_for_role(role: str) -> str:
    if role == preflight.ROLE_STABLE_AEB:
        return "aeb_feasible"
    if role == preflight.ROLE_STABLE_AES:
        return "aes_feasible"
    if role == preflight.ROLE_DRIFT_REQUIRED:
        return "drift_required"
    if role == preflight.ROLE_UNAVOIDABLE:
        return "unavoidable"
    return ""


def _source_row(source_id: str, *, axis: str, role: str, surface: str, index: int) -> dict[str, object]:
    return {
        "candidate_source_id": source_id,
        "repair_candidate_id": f"repair_{source_id}",
        "repair_axis": axis,
        "repair_source_kind": axis,
        "repair_source_family": f"family_{axis}",
        "source_split": "public_gate" if axis not in {"offtrack_anchor_relief", "offtrack_boundary_relief_extension"} else "public_debug",
        "source_role_semantics": role,
        "feasibility_tier_id": "tier_c_boundary_near_miss",
        "parent_feasibility_tier_id": "tier_parent",
        "normalized_surface_variant": surface,
        "sampled_obstacle_label": _label_for_role(role),
        "source_support_status": "supported",
        "speed_ref": 18.0,
        "mu": 0.4,
        "friction_step_enabled": surface == "post_friction_step",
        "friction_step_at": 20,
        "post_obstacle_track_width": 6.5,
        "base_geometry_source": "unit_test",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "sequence_index": index,
    }


def _quota_source_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for axis, quota in preflight.AXIS_SELECTED_QUOTAS.items():
        for index in range(quota):
            if axis == "offtrack_anchor_relief":
                role = preflight.ROLE_STABLE_AEB
            elif axis == "offtrack_boundary_relief_extension":
                role = preflight.ROLE_STABLE_AES
            elif axis == "collision_mitigation_relief":
                role = preflight.ROLE_UNAVOIDABLE
            elif axis == "mitigation_metric_isolation":
                role = preflight.ROLE_UNAVOIDABLE
            else:
                role = (
                    preflight.ROLE_STABLE_AEB,
                    preflight.ROLE_STABLE_AES,
                    preflight.ROLE_DRIFT_REQUIRED,
                    preflight.ROLE_UNAVOIDABLE,
                )[index % 4]
            rows.append(
                _source_row(
                    f"{axis}_{index:03d}",
                    axis=axis,
                    role=role,
                    surface=("post_friction_step" if index % 2 == 0 else "steady_surface"),
                    index=index,
                )
            )
    rows.append(
        {
            **_source_row(
                "unsupported_extra",
                axis="success_support_expansion",
                role=preflight.ROLE_STABLE_AEB,
                surface="steady_surface",
                index=999,
            ),
            "source_support_status": "unsupported",
        }
    )
    return rows


def _accepted_rows(sources: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in sources:
        if source["source_support_status"] != "supported":
            continue
        role = str(source["source_role_semantics"])
        rows.append(
            {
                "candidate_source_id": source["candidate_source_id"],
                "accepted": True,
                "source_role_semantics": role,
                "obstacle_distance": 52.0 if role == preflight.ROLE_STABLE_AEB else 20.0,
                "obstacle_half_width": 0.75 if role != preflight.ROLE_UNAVOIDABLE else 1.2,
                "label": _label_for_role(role),
                "threshold_score": 0.5,
                "time_to_obstacle": 2.0,
                "time_after_friction_step": 1.0,
                "friction_step_at": source["friction_step_at"],
            }
        )
    return rows


def _write_profile_artifacts(root: Path) -> None:
    for profile_name in EXPECTED_PROFILE_NAMES:
        config = root / "configs" / f"{profile_name}_seed167400.json"
        checkpoint = root / "profile_runs" / profile_name / "seed_167400" / "checkpoint.pt"
        config.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("{}\n", encoding="utf-8")
        checkpoint.write_bytes(b"synthetic")


def test_select_sources_uses_only_supported_rows() -> None:
    selected, failures = preflight.select_sources(_quota_source_rows())

    assert not failures
    assert len(selected) == 80
    assert all(row["source_support_status"] == "supported" for row in selected)
    assert preflight._count_by(selected, "repair_axis") == preflight.AXIS_SELECTED_QUOTAS


def test_representative_cell_prefers_stable_aeb_high_threshold() -> None:
    source = {"candidate_source_id": "s0", "source_role_semantics": preflight.ROLE_STABLE_AEB}
    cells = {
        "s0": [
            {"candidate_source_id": "s0", "threshold_score": 0.1, "obstacle_distance": 60.0},
            {"candidate_source_id": "s0", "threshold_score": 0.9, "obstacle_distance": 50.0},
        ]
    }

    cell, rule = preflight.representative_cell_for_source(source, cells)

    assert cell is not None
    assert cell["threshold_score"] == 0.9
    assert rule == "stable_aeb_max_threshold_then_farther_distance"


def test_run_outcome_support_materialization_preflight_writes_expected_artifacts(tmp_path: Path) -> None:
    source_rows = _quota_source_rows()
    source_path = tmp_path / "source_rows.csv"
    accepted_path = tmp_path / "accepted.csv"
    profile_dir = tmp_path / "profiles"
    output_dir = tmp_path / "out"
    _write_profile_artifacts(profile_dir)
    write_csv_rows(source_path, source_rows)
    write_csv_rows(accepted_path, _accepted_rows(source_rows))

    summary = preflight.run_outcome_support_materialization_preflight(
        source_rows_path=source_path,
        accepted_cells_path=accepted_path,
        profile_run_dir=profile_dir,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "task_quality_calibrated_outcome_support_materialization_preflight_pass"
    assert summary["selected_source_count"] == 80
    assert summary["executable_task_spec_count"] == 80
    assert summary["planned_workload_rows"] == 960
    assert summary["selected_unsupported_source_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["diagnostic_only_no_ranking_claim_count"] == 8
    assert (output_dir / "executable_task_specs.json").exists()
    assert (output_dir / "planned_workload.csv").exists()
    persisted = read_json(output_dir / "executable_task_specs.json")
    assert len(persisted["executable_task_specs"]) == 80
