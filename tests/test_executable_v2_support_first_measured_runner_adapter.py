from __future__ import annotations

from pathlib import Path

from autodrift import executable_v2_support_first_measured_runner_adapter as adapter
from autodrift.artifacts import read_json, write_json
from autodrift.controller_family_decisive_matrix_protocol import EXPECTED_PROFILE_NAMES


def _spec(
    *,
    spec_id: str,
    role: str,
    surface: str,
    label: str,
    scenario_profile_name: str,
    mu_bucket: str,
) -> dict[str, object]:
    return {
        "v2_panel_spec_id": spec_id,
        "support_first_materialized_v2_panel_spec_id": f"mat_{spec_id}",
        "source_scenario_spec_id": f"{spec_id}_scenario",
        "role_panel_id": role,
        "v2_role_surface_id": f"{role}::{surface}",
        "surface_variant": surface,
        "source_family_id": surface,
        "source_role_semantics": role,
        "profile_name": scenario_profile_name,
        "profile_group": role,
        "hidden_dynamics_bucket": mu_bucket,
        "road_boundary_bucket": "circle_r18",
        "obstacle_timing_bucket": surface,
        "obstacle_lateral_bucket": "support_first_width_0p7",
        "v2_task_label": label,
        "allowed_labels_metadata_only": label,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "diagnostic_only_no_ranking_claim": True,
        "env_config": {
            "track_kind": "circle",
            "track_radius": 18.0,
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "obstacle_relative_velocity_mode": "zero",
            "wheel_observation_mode": "none",
            "obstacle": {
                "enabled": True,
                "allowed_labels": [label],
                "max_sample_attempts": 1,
            },
        },
    }


def _write_specs(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "support_first_reset_executable_v2_panel_specs.json"
    write_json(path, {"executable_v2_panel_specs": rows})
    return path


def _profile_rows(tmp_path: Path, names: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in names:
        config_path = tmp_path / "configs" / f"{name}.json"
        checkpoint_path = tmp_path / "profile_runs" / name / "checkpoint.pt"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}", encoding="utf-8")
        checkpoint_path.write_text("checkpoint", encoding="utf-8")
        rows.append(
            {
                "profile_name": name,
                "config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": True,
                "checkpoint_exists": True,
            }
        )
    return rows


def test_support_first_measured_runner_adapter_writes_profile_separated_workload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs_path = _write_specs(
        tmp_path,
        [
            _spec(
                spec_id="sfm_000",
                role="stable_aeb",
                surface="steady_surface",
                label="aeb_feasible",
                scenario_profile_name="stable_aeb_steady_surface_grid_v0",
                mu_bucket="mu_0p7::steady_surface",
            ),
            _spec(
                spec_id="sfm_001",
                role="drift_required_recovery",
                surface="post_friction_step",
                label="drift_required",
                scenario_profile_name="drift_required_recovery_post_friction_step_grid_v0",
                mu_bucket="mu_0p25::post_friction_step",
            ),
        ],
    )
    profiles = _profile_rows(tmp_path, ["L0_current_masked", "L3_online_gru"])
    monkeypatch.setattr(adapter, "profile_artifact_rows", lambda **_kwargs: profiles)

    summary = adapter.run_support_first_measured_runner_adapter(
        executable_v2_panel_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_support_first_spec_count=2,
        target_controller_profile_count=2,
        target_workload_cell_count=4,
        target_role_count=2,
        target_role_surface_count=2,
    )

    assert summary["result_class"] == "executable_v2_support_first_measured_runner_adapter_pass"
    assert summary["support_first_spec_count"] == 2
    assert summary["controller_profile_count"] == 2
    assert summary["workload_cell_count"] == 4
    assert summary["role_surface_count"] == 2
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["missing_profile_artifact_count"] == 0
    assert summary["profile_alias_mismatch_count"] == 0
    assert summary["scenario_as_controller_profile_count"] == 0
    assert summary["missing_required_field_count"] == 0
    assert summary["duplicate_key_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["measured_rollout_started"] is False

    payload = read_json(tmp_path / "out" / "support_first_measured_executable_specs.json")
    normalized = payload["support_first_measured_executable_specs"]
    assert len(normalized) == 2
    assert normalized[0]["task_source_id"] == "sfm_000"
    assert normalized[0]["scenario_profile_name"] == "stable_aeb_steady_surface_grid_v0"
    assert normalized[0]["sampled_obstacle_label"] == "aeb_feasible"
    assert normalized[0]["labels_enter_actor_input"] is False
    assert normalized[0]["v2_ranking_admissible_by_default"] is False
    assert normalized[0]["env_config"]["wheel_observation_mode"] == "none"

    workload_csv = (tmp_path / "out" / "support_first_measured_workload_matrix.csv").read_text()
    assert "scenario_profile_name" in workload_csv
    assert "controller_profile_name" in workload_csv
    assert "stable_aeb_steady_surface_grid_v0" in workload_csv
    assert "L3_online_gru" in workload_csv

    rows = [row for row in workload_csv.splitlines() if row.startswith("sfm_000::L0_current_masked")]
    assert rows
    assert "sfm_000::L0_current_masked" in rows[0]
    assert "L0_current_masked,L0_current_masked,stable_aeb_steady_surface_grid_v0" in rows[0]

    role_surface_counts = (tmp_path / "out" / "support_first_role_surface_counts.csv").read_text()
    assert "drift_required_recovery::post_friction_step,1" in role_surface_counts
    claim_boundary = (tmp_path / "out" / "support_first_measured_claim_boundary.csv").read_text()
    assert "support_first_measured_runner_adapter_ready" in claim_boundary
    assert "controller_family_ranking" in claim_boundary
    assert "level3_self_identification" in claim_boundary


def test_support_first_measured_runner_adapter_flags_scenario_profile_as_controller(
    tmp_path: Path,
    monkeypatch,
) -> None:
    scenario_profile = "stable_aeb_steady_surface_grid_v0"
    specs_path = _write_specs(
        tmp_path,
        [
            _spec(
                spec_id="sfm_000",
                role="stable_aeb",
                surface="steady_surface",
                label="aeb_feasible",
                scenario_profile_name=scenario_profile,
                mu_bucket="mu_0p7::steady_surface",
            )
        ],
    )
    monkeypatch.setattr(adapter, "profile_artifact_rows", lambda **_kwargs: _profile_rows(tmp_path, [scenario_profile]))

    summary = adapter.run_support_first_measured_runner_adapter(
        executable_v2_panel_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_support_first_spec_count=1,
        target_controller_profile_count=1,
        target_workload_cell_count=1,
        target_role_count=1,
        target_role_surface_count=1,
    )

    assert summary["result_class"] == "executable_v2_support_first_measured_runner_adapter_fail"
    assert summary["scenario_as_controller_profile_count"] == 1


def test_support_first_measured_runner_adapter_flags_duplicate_and_missing_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    specs_path = _write_specs(
        tmp_path,
        [
            _spec(
                spec_id="sfm_dup",
                role="stable_aeb",
                surface="steady_surface",
                label="aeb_feasible",
                scenario_profile_name="stable_aeb_steady_surface_grid_v0",
                mu_bucket="mu_0p7::steady_surface",
            ),
            _spec(
                spec_id="sfm_dup",
                role="",
                surface="steady_surface",
                label="aeb_feasible",
                scenario_profile_name="stable_aeb_steady_surface_grid_v0",
                mu_bucket="mu_0p8::steady_surface",
            ),
        ],
    )
    monkeypatch.setattr(adapter, "profile_artifact_rows", lambda **_kwargs: _profile_rows(tmp_path, ["L1_one_step"]))

    summary = adapter.run_support_first_measured_runner_adapter(
        executable_v2_panel_specs_path=specs_path,
        output_dir=tmp_path / "out",
        target_support_first_spec_count=2,
        target_controller_profile_count=1,
        target_workload_cell_count=2,
        target_role_count=None,
        target_role_surface_count=None,
    )

    assert summary["result_class"] == "executable_v2_support_first_measured_runner_adapter_fail"
    assert summary["duplicate_key_count"] >= 1
    assert summary["missing_required_field_count"] > 0
    duplicate_csv = (tmp_path / "out" / "support_first_measured_duplicate_key_rows.csv").read_text()
    missing_csv = (tmp_path / "out" / "support_first_measured_missing_field_rows.csv").read_text()
    assert "spec,sfm_dup,2" in duplicate_csv
    assert "missing_field" in missing_csv
    assert "role_panel_id" in missing_csv or "task_family" in missing_csv


def test_support_first_measured_runner_adapter_contract_matches_full_profile_set() -> None:
    assert adapter.TARGET_WORKLOAD_CELL_COUNT == adapter.TARGET_SUPPORT_FIRST_SPEC_COUNT * len(EXPECTED_PROFILE_NAMES)
    assert adapter.TARGET_CONTROLLER_PROFILE_COUNT == len(EXPECTED_PROFILE_NAMES)
