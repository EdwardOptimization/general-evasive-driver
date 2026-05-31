from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_task_quality_calibrated_source_materialization_selector as selector
from autodrift.artifacts import read_json, write_csv_rows


def _row(
    source_id: str,
    *,
    kind: str,
    role: str,
    surface: str,
    split: str = "public_gate",
    accepted_cells: int = 5,
    base_geometry_source: str = "m1928::parent_task_source_id",
    supported: bool = True,
) -> dict[str, object]:
    return {
        "repair_candidate_id": f"repair_{source_id}",
        "repair_source_kind": kind,
        "repair_source_family": "synthetic_family",
        "source_split": split,
        "offtrack_repair_mode": "synthetic_mode",
        "recovery_corridor_profile": "synthetic_corridor",
        "parent_candidate_source_id": f"parent_{source_id}",
        "parent_task_source_id": f"task_{source_id}",
        "parent_profile_name": "synthetic_profile",
        "parent_feasibility_tier_id": "tier_synthetic",
        "parent_source_role_semantics": role,
        "parent_surface_variant": surface,
        "candidate_source_id": source_id,
        "source_v1_bounded_panel_spec_id": f"spec_{source_id}",
        "source_scenario_spec_id": f"scenario_{source_id}",
        "source_role_semantics": role,
        "profile_name": "synthetic_profile",
        "profile_group": "synthetic_group",
        "speed_ref": 18.0,
        "mu": 0.4,
        "friction_step_enabled": surface == selector.SURFACE_POST,
        "friction_step_at": 20,
        "grid_cell_count": 48,
        "accepted_cell_count": accepted_cells,
        "source_support_status": "supported" if supported else "unsupported",
        "accepted_distance_min": 44.0,
        "accepted_distance_max": 56.0,
        "accepted_half_width_min": 0.6,
        "accepted_half_width_max": 1.0,
        "dominant_label": "aeb_feasible",
        "post_obstacle_track_width": 7.0,
        "base_geometry_source": base_geometry_source,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _add_rows(rows: list[dict[str, object]], prefix: str, count: int, **kwargs: object) -> None:
    for index in range(count):
        rows.append(_row(f"{prefix}_{index:03d}", accepted_cells=100 - index, **kwargs))


def _complete_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    anchor_base = "m1950_calibrated_anchor_fallback::post_friction_step"
    _add_rows(
        rows,
        "anchor_post",
        18,
        kind="anchor_neighborhood",
        role=selector.ROLE_STABLE_AEB,
        surface=selector.SURFACE_POST,
        split="public_debug",
        base_geometry_source=anchor_base,
    )
    _add_rows(
        rows,
        "anchor_steady",
        18,
        kind="anchor_neighborhood",
        role=selector.ROLE_STABLE_AEB,
        surface=selector.SURFACE_STEADY,
        split="public_debug",
        base_geometry_source="m1950_calibrated_anchor_fallback::steady_surface",
    )
    _add_rows(rows, "succ_aeb_post", 5, kind="success_stabilizer", role=selector.ROLE_STABLE_AEB, surface=selector.SURFACE_POST)
    _add_rows(
        rows,
        "succ_aeb_steady",
        5,
        kind="success_stabilizer",
        role=selector.ROLE_STABLE_AEB,
        surface=selector.SURFACE_STEADY,
    )
    _add_rows(
        rows,
        "succ_aes_post",
        4,
        kind="success_stabilizer",
        role=selector.ROLE_STABLE_AES_ONLY,
        surface=selector.SURFACE_POST,
    )
    _add_rows(
        rows,
        "succ_aes_steady",
        4,
        kind="success_stabilizer",
        role=selector.ROLE_STABLE_AES_ONLY,
        surface=selector.SURFACE_STEADY,
    )
    _add_rows(
        rows,
        "succ_drift_post",
        4,
        kind="success_stabilizer",
        role=selector.ROLE_DRIFT_REQUIRED,
        surface=selector.SURFACE_POST,
    )
    _add_rows(
        rows,
        "succ_drift_steady",
        2,
        kind="success_stabilizer",
        role=selector.ROLE_DRIFT_REQUIRED,
        surface=selector.SURFACE_STEADY,
    )
    _add_rows(
        rows,
        "succ_unav_post",
        2,
        kind="success_stabilizer",
        role=selector.ROLE_UNAVOIDABLE,
        surface=selector.SURFACE_POST,
    )
    _add_rows(
        rows,
        "succ_unav_steady",
        3,
        kind="success_stabilizer",
        role=selector.ROLE_UNAVOIDABLE,
        surface=selector.SURFACE_STEADY,
    )
    _add_rows(
        rows,
        "offtrack_aes",
        9,
        kind="offtrack_boundary_relief",
        role=selector.ROLE_STABLE_AES_ONLY,
        surface="",
        split="public_gate",
        base_geometry_source="tier_role_surface_default",
    )
    _add_rows(
        rows,
        "mit_unav_post",
        4,
        kind="mitigation_isolation_check",
        role=selector.ROLE_UNAVOIDABLE,
        surface=selector.SURFACE_POST,
    )
    _add_rows(
        rows,
        "mit_unav_steady",
        5,
        kind="mitigation_isolation_check",
        role=selector.ROLE_UNAVOIDABLE,
        surface=selector.SURFACE_STEADY,
    )
    _add_rows(
        rows,
        "mit_aeb_post",
        4,
        kind="mitigation_isolation_check",
        role=selector.ROLE_STABLE_AEB,
        surface=selector.SURFACE_POST,
    )
    _add_rows(
        rows,
        "mit_drift_steady",
        3,
        kind="mitigation_isolation_check",
        role=selector.ROLE_DRIFT_REQUIRED,
        surface=selector.SURFACE_STEADY,
    )
    rows.append(
        _row(
            "forbidden_actor_input",
            kind="offtrack_boundary_relief",
            role=selector.ROLE_STABLE_AES_ONLY,
            surface="",
            split="public_gate",
        )
    )
    rows[-1]["labels_enter_actor_input"] = True
    return rows


def test_selector_matches_m1955_quotas() -> None:
    selected, failures = selector.select_calibrated_materialization_sources(_complete_rows())

    assert not failures
    assert len(selected) == 80
    assert selector._count_by(selected, "repair_source_kind") == {
        "anchor_neighborhood": 32,
        "mitigation_isolation_check": 16,
        "offtrack_boundary_relief": 8,
        "success_stabilizer": 24,
    }
    assert sum(row["selection_quota_name"] == "anchor_post" for row in selected) == 16
    assert sum(row["selection_quota_name"] == "anchor_steady" for row in selected) == 16
    assert sum(row["selection_quota_name"].startswith("success_") for row in selected) == 24
    assert sum(row["normalized_surface_variant"] == selector.SURFACE_RELIEF_UNSPECIFIED for row in selected) == 8
    assert not any(row["labels_enter_actor_input"] for row in selected)


def test_selector_fails_closed_when_quota_is_missing() -> None:
    rows = [
        row
        for row in _complete_rows()
        if not (
            row["repair_source_kind"] == "anchor_neighborhood"
            and row["parent_surface_variant"] == selector.SURFACE_STEADY
        )
    ]

    selected, failures = selector.select_calibrated_materialization_sources(rows)

    assert len(selected) == 64
    assert failures
    assert failures[0]["quota_name"] == "anchor_steady"
    assert failures[0]["failure_reason"] == "insufficient_eligible_quota_candidates"


def test_materialize_calibrated_source_subset_writes_expected_artifacts(tmp_path: Path) -> None:
    source_rows = tmp_path / "repair_source_rows.csv"
    accepted_cells = tmp_path / "repair_accepted_cells.csv"
    output_config = tmp_path / "subset.json"
    output_dir = tmp_path / "run"
    rows = _complete_rows()
    write_csv_rows(source_rows, rows)
    write_csv_rows(
        accepted_cells,
        [
            {"candidate_source_id": row["candidate_source_id"], "accepted": True, "obstacle_distance": 52.0}
            for row in rows
        ],
    )

    summary = selector.materialize_calibrated_source_subset(
        repair_source_rows_path=source_rows,
        repair_accepted_cells_path=accepted_cells,
        output_config_path=output_config,
        output_dir=output_dir,
    )

    assert summary["result_class"] == "task_quality_calibrated_materialization_selector_pass"
    assert summary["selected_source_count"] == 80
    assert summary["expected_planned_workload_cell_count"] == 960
    assert summary["calibrated_anchor_post_friction_step_selected_count"] == 16
    assert summary["calibrated_anchor_steady_surface_selected_count"] == 16
    assert summary["guardrail_violation_count"] == 0
    assert (output_dir / "selected_sources.csv").exists()
    assert (output_dir / "source_kind_quota_summary.csv").exists()
    assert (output_dir / "role_surface_quota_summary.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    persisted = read_json(output_config)
    assert persisted["selected_source_count"] == 80
    assert (
        persisted["selection_summary"]["recommended_next_route"]
        == "route_to_calibrated_materialization_preflight_command_design"
    )
