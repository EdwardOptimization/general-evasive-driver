from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_current_sim_dual_axis_candidate_config_materialization import (
    run_dual_axis_candidate_config_materialization,
)


def _candidate(
    scenario_id: str,
    candidate_id: str,
    axis: str,
    route: str,
    transform: str,
    *,
    timing_after: str = "mid",
    lateral_after: str = "centerline",
    hidden_after: str = "low_mu",
) -> dict[str, object]:
    return {
        "scenario_spec_id": scenario_id,
        "candidate_id": candidate_id,
        "candidate_axis": axis,
        "source_recommended_route": route,
        "role_family": "R2_handling_limit_drift_capable_avoidance",
        "scenario_family_id": "R2",
        "same_scene_group_id": scenario_id,
        "hidden_dynamics_bucket_before": "low_mu",
        "hidden_dynamics_bucket_after": hidden_after,
        "timing_bucket_before": "late_close",
        "timing_bucket_after": timing_after,
        "lateral_bucket_before": "right_offset",
        "lateral_bucket_after": lateral_after,
        "initial_speed_mps_before": 16.0,
        "initial_speed_mps_after": 14.0,
        "track_width_m_before": 6.0,
        "track_width_m_after": 6.0,
        "track_radius_m_before": 80.0,
        "track_radius_m_after": 80.0,
        "transform_name": transform,
        "transform_reason": "test",
        "combined_candidate_reason": "",
        "active_for_materialization": True,
        "diagnostic_only": True,
        "ranking_admissible": False,
        "winner_selected": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def _write_inputs(root: Path) -> tuple[Path, Path]:
    candidate_dir = root / "candidates"
    candidate_dir.mkdir()
    rows = [
        _candidate(
            "g1",
            "g1::G01",
            "G",
            "geometry_timing_rebalance_candidate",
            "timing_step_earlier",
            hidden_after="low_mu",
        ),
        _candidate(
            "g1",
            "g1::G02",
            "G",
            "geometry_timing_rebalance_candidate",
            "speed_step_down",
            timing_after="late_close",
            hidden_after="low_mu",
        ),
        _candidate(
            "h1",
            "h1::H01",
            "H",
            "hidden_dynamics_range_rebalance_candidate",
            "low_mu_step_toward_nominal",
            timing_after="early_far",
            lateral_after="centerline",
            hidden_after="nominal_neighbor",
        ),
        _candidate(
            "g1",
            "g1::GH03",
            "GH",
            "geometry_timing_rebalance_candidate",
            "timing_step_earlier+low_mu_step_toward_nominal",
            hidden_after="nominal_neighbor",
        ),
    ]
    write_csv_rows(candidate_dir / "calibration_candidate_rows.csv", rows)
    write_json(candidate_dir / "calibration_config_candidates.json", {"candidate_count": len(rows)})
    config = root / "config.json"
    base_spec = {
        "scenario_family_id": "R2",
        "role_family": "R2_handling_limit_drift_capable_avoidance",
        "actor_contract_id": "P0_human_view_no_wheel_no_oracle",
        "obstacle_longitudinal_timing_bucket": "late_close",
        "obstacle_lateral_offset_bucket": "right_offset",
        "hidden_dynamics_bucket": "low_mu",
        "initial_speed_mps": 16.0,
        "track_width_m": 6.0,
        "track_radius_m": 80.0,
        "env_config": {
            "speed_range": [16.0, 16.0],
            "track_width": 6.0,
            "track_radius": 80.0,
            "obstacle": {"distance_range": [11.0, 22.0], "lateral_offset_range": [-1.2, -1.2]},
            "randomization": {"mu_range": [0.25, 0.65]},
        },
    }
    write_json(
        config,
        {
            "scenario_specs": [
                {"scenario_spec_id": "g1", **base_spec},
                {"scenario_spec_id": "h1", **base_spec},
                {
                    "scenario_spec_id": "nominal_ref",
                    **{
                        **base_spec,
                        "hidden_dynamics_bucket": "nominal",
                        "obstacle_longitudinal_timing_bucket": "mid",
                        "obstacle_lateral_offset_bucket": "centerline",
                        "env_config": {
                            "speed_range": [13.0, 13.0],
                            "track_width": 6.0,
                            "track_radius": 80.0,
                            "obstacle": {
                                "distance_range": [20.0, 34.0],
                                "lateral_offset_range": [0.0, 0.0],
                            },
                            "randomization": {"mu_range": [0.55, 1.1]},
                        },
                    },
                },
            ]
        },
    )
    return candidate_dir, config


def test_candidate_config_materializer_writes_five_bounded_packs(tmp_path: Path) -> None:
    candidate_dir, config = _write_inputs(tmp_path)
    output_dir = tmp_path / "out"

    summary = run_dual_axis_candidate_config_materialization(
        candidate_dir=candidate_dir,
        config=config,
        output_dir=output_dir,
        target_candidate_input_count=4,
        target_g_primary_selection_count=1,
        target_h_primary_selection_count=1,
        target_g_h_primary_selection_count=2,
        target_gh_minimal_selection_count=2,
    )

    assert summary["result_class"] == "current_sim_dual_axis_candidate_config_materialization_pass"
    assert summary["config_pack_count"] == 5
    assert summary["modified_config_pack_count"] == 4
    assert summary["baseline_reference_pack_count"] == 1
    assert summary["g_primary_selection_count"] == 1
    assert summary["h_primary_selection_count"] == 1
    assert summary["g_h_primary_selection_count"] == 2
    assert summary["gh_minimal_selection_count"] == 2
    assert summary["active_config_overwritten"] is False
    assert summary["guardrail_violation_count"] == 0

    manifest = read_json(output_dir / "config_pack_manifest.json")
    assert manifest["config_pack_count"] == 5

    selection_rows = (output_dir / "candidate_selection_rows.csv").read_text(encoding="utf-8")
    assert "g_primary_priority" in selection_rows
    assert "h_primary_unique" in selection_rows
    assert "gh_minimal_prefer_gh_else_primary" in selection_rows

    patch_rows = (output_dir / "scenario_spec_patch_rows.csv").read_text(encoding="utf-8")
    assert "env_config_patch" in patch_rows or "mixed_env_and_metadata" in patch_rows

    g_pack = read_json(output_dir / "config_packs" / "g_primary_pack.json")
    g1 = next(spec for spec in g_pack["scenario_specs"] if spec["scenario_spec_id"] == "g1")
    assert g1["obstacle_longitudinal_timing_bucket"] == "mid"
    assert g1["env_config"]["speed_range"] == [14.0, 14.0]

    claims = (output_dir / "claim_boundary.csv").read_text(encoding="utf-8")
    assert "active_config_overwrite,False,False" in claims
