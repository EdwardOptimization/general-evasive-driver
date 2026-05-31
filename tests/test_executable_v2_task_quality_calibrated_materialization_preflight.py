from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_materialization_preflight as preflight
from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


def _label_for_role(role: str) -> str:
    if role == preflight.ROLE_STABLE_AEB:
        return "aeb_feasible"
    if role == preflight.ROLE_STABLE_AES_ONLY:
        return "aes_feasible"
    if role == preflight.ROLE_DRIFT_REQUIRED:
        return "drift_required"
    if role == preflight.ROLE_UNAVOIDABLE:
        return "unavoidable"
    return ""


def _selected_source(
    source_id: str,
    *,
    kind: str,
    role: str,
    surface: str,
    quota_name: str,
) -> dict[str, object]:
    return {
        "candidate_source_id": source_id,
        "repair_candidate_id": f"repair_{source_id}",
        "repair_source_kind": kind,
        "selection_quota_name": quota_name,
        "source_role_semantics": role,
        "parent_feasibility_tier_id": "" if kind == "offtrack_boundary_relief" else "tier_synthetic",
        "parent_surface_variant": "" if surface == "relief_surface_unspecified" else surface,
        "normalized_surface_variant": surface,
        "source_split": "public_gate",
        "source_v1_bounded_panel_spec_id": f"spec_{source_id}",
        "source_scenario_spec_id": f"scenario_{source_id}",
        "speed_ref": 18.0,
        "mu": 0.4,
        "friction_step_enabled": surface == "post_friction_step",
        "friction_step_at": 20,
        "base_geometry_source": "m1950_calibrated_anchor_fallback::synthetic"
        if kind == "anchor_neighborhood"
        else "m1928::parent_task_source_id",
        "post_obstacle_track_width": 7.0,
        "diagnostic_only_no_ranking_claim": True,
    }


def _quota_rows() -> list[dict[str, object]]:
    specs = [
        ("anchor_neighborhood", preflight.ROLE_STABLE_AEB, "post_friction_step", "anchor_post", 16),
        ("anchor_neighborhood", preflight.ROLE_STABLE_AEB, "steady_surface", "anchor_steady", 16),
        ("success_stabilizer", preflight.ROLE_STABLE_AEB, "post_friction_step", "success_aeb_post", 4),
        ("success_stabilizer", preflight.ROLE_STABLE_AEB, "steady_surface", "success_aeb_steady", 4),
        ("success_stabilizer", preflight.ROLE_STABLE_AES_ONLY, "post_friction_step", "success_aes_post", 3),
        ("success_stabilizer", preflight.ROLE_STABLE_AES_ONLY, "steady_surface", "success_aes_steady", 3),
        ("success_stabilizer", preflight.ROLE_DRIFT_REQUIRED, "post_friction_step", "success_drift_post", 4),
        ("success_stabilizer", preflight.ROLE_DRIFT_REQUIRED, "steady_surface", "success_drift_steady", 2),
        ("success_stabilizer", preflight.ROLE_UNAVOIDABLE, "post_friction_step", "success_unav_post", 1),
        ("success_stabilizer", preflight.ROLE_UNAVOIDABLE, "steady_surface", "success_unav_steady", 3),
        ("offtrack_boundary_relief", preflight.ROLE_STABLE_AES_ONLY, "relief_surface_unspecified", "offtrack", 8),
        ("mitigation_isolation_check", preflight.ROLE_UNAVOIDABLE, "post_friction_step", "mit_unav_post", 4),
        ("mitigation_isolation_check", preflight.ROLE_UNAVOIDABLE, "steady_surface", "mit_unav_steady", 5),
        ("mitigation_isolation_check", preflight.ROLE_STABLE_AEB, "post_friction_step", "mit_aeb_post", 4),
        ("mitigation_isolation_check", preflight.ROLE_DRIFT_REQUIRED, "steady_surface", "mit_drift_steady", 3),
    ]
    rows: list[dict[str, object]] = []
    for kind, role, surface, quota, count in specs:
        for index in range(count):
            rows.append(
                _selected_source(
                    f"{quota}_{index:03d}",
                    kind=kind,
                    role=role,
                    surface=surface,
                    quota_name=quota,
                )
            )
    return rows


def _accepted_rows(selected_sources: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in selected_sources:
        role = str(source["source_role_semantics"])
        source_id = str(source["candidate_source_id"])
        rows.append(
            {
                "candidate_source_id": source_id,
                "accepted": True,
                "source_role_semantics": role,
                "obstacle_distance": 52.0,
                "obstacle_half_width": 0.75,
                "label": _label_for_role(role),
                "threshold_score": 0.2,
                "time_to_obstacle": 2.8,
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


def test_offtrack_blank_parent_tier_normalizes_to_explicit_sentinel() -> None:
    source = _selected_source(
        "offtrack_blank_parent",
        kind="offtrack_boundary_relief",
        role=preflight.ROLE_STABLE_AES_ONLY,
        surface="relief_surface_unspecified",
        quota_name="offtrack",
    )
    cell = {
        "obstacle_distance": 52.0,
        "obstacle_half_width": 0.75,
        "label": "aes_feasible",
        "threshold_score": 0.2,
        "time_to_obstacle": 2.8,
        "time_after_friction_step": 1.0,
    }

    spec = preflight.materialize_executable_spec(
        source=source,
        cell=cell,
        representative_cell_rule="boundary_min_threshold_then_closer_wider",
        index=0,
    )

    assert spec["parent_feasibility_tier_id"] == preflight.OFFTRACK_PARENT_TIER_SENTINEL


def test_non_offtrack_blank_parent_tier_remains_fail_closed() -> None:
    source = _selected_source(
        "success_blank_parent",
        kind="success_stabilizer",
        role=preflight.ROLE_STABLE_AES_ONLY,
        surface="steady_surface",
        quota_name="success_aes_steady",
    )
    source["parent_feasibility_tier_id"] = ""

    assert preflight.normalized_parent_feasibility_tier_id(source) == ""


def test_run_calibrated_materialization_preflight_writes_expected_artifacts(tmp_path: Path) -> None:
    selected_sources = _quota_rows()
    subset_config = tmp_path / "subset.json"
    accepted_cells = tmp_path / "accepted.csv"
    profile_dir = tmp_path / "profiles"
    output_dir = tmp_path / "out"
    _write_profile_artifacts(profile_dir)
    write_json(
        subset_config,
        {
            "selected_source_count": len(selected_sources),
            "selected_sources": selected_sources,
        },
    )
    write_csv_rows(accepted_cells, _accepted_rows(selected_sources))

    summary = preflight.run_calibrated_materialization_preflight(
        subset_config_path=subset_config,
        repair_accepted_cells_path=accepted_cells,
        profile_run_dir=profile_dir,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "task_quality_calibrated_materialization_preflight_pass"
    assert summary["selected_source_count"] == 80
    assert summary["executable_task_spec_count"] == 80
    assert summary["controller_profile_count"] == 12
    assert summary["planned_workload_cell_count"] == 960
    assert summary["parent_feasibility_tier_blank_spec_count"] == 0
    assert summary["parent_feasibility_tier_blank_workload_count"] == 0
    assert summary["parent_feasibility_tier_normalized_spec_count"] == 8
    assert summary["parent_feasibility_tier_normalized_workload_count"] == 8 * len(EXPECTED_PROFILE_NAMES)
    assert summary["contract_violation_count"] == 0
    assert summary["forbidden_key_violation_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "executable_task_specs.json").exists()
    assert (output_dir / "planned_workload.csv").exists()
    persisted = read_json(output_dir / "executable_task_specs.json")
    assert len(persisted["executable_task_specs"]) == 80
    offtrack_specs = [
        spec for spec in persisted["executable_task_specs"] if spec["repair_source_kind"] == "offtrack_boundary_relief"
    ]
    assert {spec["parent_feasibility_tier_id"] for spec in offtrack_specs} == {
        preflight.OFFTRACK_PARENT_TIER_SENTINEL
    }
