from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_json
from autodrift import executable_v2_support_first_reset_validation_adapter as adapter


def _spec(
    *,
    spec_id: str,
    role: str,
    surface: str,
    label: str,
    profile_name: str,
    speed: float,
    mu: float,
    half_width: float,
) -> dict[str, object]:
    friction_step_enabled = surface == "post_friction_step"
    return {
        "materialized_v2_panel_spec_id": spec_id,
        "support_contract_id": "executable_v2_support_first_task_source_v1",
        "materialization_contract_id": "support_first_materialization_v0",
        "candidate_source_id": f"{role}_{surface}_{speed}_{mu}",
        "source_v1_bounded_panel_spec_id": f"{role}_{surface}_{speed}_{mu}",
        "source_scenario_spec_id": f"{role}_{surface}_{speed}_{mu}_scenario",
        "source_role_semantics": role,
        "v2_task_label": label,
        "profile_name": profile_name,
        "profile_group": role,
        "source_family_id": surface,
        "surface_variant": surface,
        "speed_ref": speed,
        "mu": mu,
        "friction_step_enabled": friction_step_enabled,
        "friction_step_at": 20 if friction_step_enabled else "",
        "dt": 0.05,
        "min_time_after_friction_step": 0.3 if friction_step_enabled else 0.0,
        "obstacle_distance": 18.0,
        "obstacle_half_width": half_width,
        "threshold_score": 0.01,
        "cell_selection_kind": "boundary_min_threshold",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "reset_validation_required": True,
        "measured_execution_required": False,
        "env_config": {
            "track_kind": "circle",
            "track_radius": 18.0,
            "speed_range": [speed, speed],
            "randomization": {"mu_range": [mu, mu]},
            "friction_step": {"enabled": friction_step_enabled, "step_range": [20, 20]},
            "obstacle": {
                "enabled": True,
                "allowed_labels": [label],
                "distance_range": [18.0, 18.0],
                "half_width_range": [half_width, half_width],
                "max_sample_attempts": 1,
            },
        },
    }


def _write_payload(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "support_first_materialized_executable_v2_panel_specs.json"
    write_json(path, {"executable_v2_panel_specs": rows})
    return path


def test_support_first_reset_validation_adapter_writes_executable_v2_payload(tmp_path: Path) -> None:
    specs_path = _write_payload(
        tmp_path,
        [
            _spec(
                spec_id="mat_000",
                role="stable_aes_only",
                surface="steady_surface",
                label="aes_feasible",
                profile_name="stable_aes_only_steady_surface_grid_v0",
                speed=12.0,
                mu=0.5,
                half_width=0.7,
            ),
            _spec(
                spec_id="mat_001",
                role="drift_required_recovery",
                surface="post_friction_step",
                label="drift_required",
                profile_name="drift_required_recovery_post_friction_step_grid_v0",
                speed=14.0,
                mu=0.25,
                half_width=1.3,
            ),
        ],
    )

    summary = adapter.run_support_first_reset_validation_adapter(
        support_first_materialized_specs_path=specs_path,
        output_dir=tmp_path / "out",
        profile_config_path=tmp_path / "profile.json",
        target_materialized_spec_count=2,
        target_executable_spec_count=2,
        target_profile_count=2,
        target_role_count=2,
        target_surface_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_support_first_reset_validation_adapter_pass"
    assert summary["input_materialized_spec_count"] == 2
    assert summary["targeted_reset_executable_spec_count"] == 2
    assert summary["role_count"] == 2
    assert summary["surface_count"] == 2
    assert summary["role_surface_count"] == 2
    assert summary["profile_count"] == 2
    assert summary["reset_ready_spec_count"] == 2
    assert summary["reset_validation_required_count"] == 2
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["measured_execution_admissible_count"] == 0
    assert summary["controller_family_ranking_admissible_count"] == 0
    assert summary["missing_required_field_count"] == 0
    assert summary["duplicate_key_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False

    payload = read_json(tmp_path / "out" / "support_first_reset_executable_v2_panel_specs.json")
    rows = payload["executable_v2_panel_specs"]
    assert len(rows) == 2
    by_id = {row["v2_panel_spec_id"]: row for row in rows}
    first = by_id["mat_000"]
    assert first["support_first_materialized_v2_panel_spec_id"] == "mat_000"
    assert first["source_v1_bounded_panel_spec_id"] == "stable_aes_only_steady_surface_12.0_0.5"
    assert first["source_v1_role_panel_id"] == "stable_aes_only"
    assert first["v2_role_surface_id"] == "stable_aes_only::steady_surface"
    assert first["role_panel_id"] == "stable_aes_only"
    assert first["profile_config_path"] == str(tmp_path / "profile.json")
    assert first["v2_task_label"] == "aes_feasible"
    assert first["allowed_labels_metadata_only"] == "aes_feasible"
    assert first["labels_enter_actor_input"] is False
    assert first["hidden_dynamics_bucket"] == "mu_0p5::steady_surface"
    assert first["road_boundary_bucket"] == "circle_r18"
    assert first["obstacle_timing_bucket"] == "steady_surface"
    assert first["obstacle_lateral_bucket"] == "support_first_width_0p7"
    assert first["v2_primary_metric"] == "reset_feasibility_sampling_success_rate"
    assert first["v2_primary_metric_direction"] == "higher_is_better"
    assert first["v2_admissibility_gate"] == "all_specs_resettable_without_label_leakage_or_ranking"
    assert first["reset_ready_spec"] is True
    assert first["diagnostic_only_no_ranking_claim"] is True
    assert first["v2_ranking_admissible_by_default"] is False
    assert first["measured_execution_admissible"] is False
    assert first["controller_family_ranking_admissible"] is False
    assert first["environment_reset_scheduled"] is False
    assert first["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"]
    assert first["env_config"]["history_length"] == 1
    assert first["env_config"]["obstacle_relative_velocity_mode"] == "zero"
    assert first["env_config"]["wheel_observation_mode"] == "none"

    matrix_csv = (tmp_path / "out" / "support_first_reset_validation_matrix.csv").read_text()
    assert "drift_required_recovery::post_friction_step" in matrix_csv
    claim_boundary = (tmp_path / "out" / "support_first_reset_validation_claim_boundary.csv").read_text()
    assert "support_first_reset_validation_payload_ready" in claim_boundary
    assert "controller_family_ranking" in claim_boundary
    assert "level3_self_identification" in claim_boundary


def test_support_first_reset_validation_adapter_flags_duplicate_and_missing_required_fields(tmp_path: Path) -> None:
    rows = [
        _spec(
            spec_id="mat_dup",
            role="stable_aeb",
            surface="steady_surface",
            label="aeb_feasible",
            profile_name="stable_aeb_steady_surface_grid_v0",
            speed=10.0,
            mu=0.7,
            half_width=0.4,
        ),
        _spec(
            spec_id="mat_dup",
            role="stable_aeb",
            surface="steady_surface",
            label="aeb_feasible",
            profile_name="stable_aeb_steady_surface_grid_v0",
            speed=11.0,
            mu=0.8,
            half_width=0.5,
        ),
        _spec(
            spec_id="mat_missing",
            role="",
            surface="steady_surface",
            label="aeb_feasible",
            profile_name="stable_aeb_steady_surface_grid_v0",
            speed=12.0,
            mu=0.9,
            half_width=0.6,
        ),
    ]
    specs_path = _write_payload(tmp_path, rows)

    summary = adapter.run_support_first_reset_validation_adapter(
        support_first_materialized_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_materialized_spec_count=3,
        target_executable_spec_count=3,
        target_profile_count=1,
        target_role_count=None,
        target_surface_count=1,
        target_role_surface_count=None,
    )

    assert summary["result_class"] == "executable_v2_support_first_reset_validation_adapter_fail"
    assert summary["duplicate_key_count"] == 1
    assert summary["missing_required_field_count"] > 0
    duplicate_csv = (tmp_path / "out" / "support_first_reset_duplicate_key_rows.csv").read_text()
    missing_csv = (tmp_path / "out" / "support_first_reset_missing_field_rows.csv").read_text()
    assert "mat_dup,2" in duplicate_csv
    assert "mat_missing" in missing_csv
    assert "source_v1_role_panel_id" in missing_csv or "role_panel_id" in missing_csv


def test_claim_boundary_blocks_reset_measured_ranking_and_level3_claims() -> None:
    rows = adapter.claim_boundary_rows()
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["support_first_reset_validation_payload_ready"]["admissible"] is True
    assert by_claim["reset_feasibility"]["admissible"] is False
    assert by_claim["measured_execution"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
    assert by_claim["level3_self_identification"]["admissible"] is False
