from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import executable_v2_stable_source_reset_validation_adapter as adapter


def _spec(
    *,
    index: int,
    label: str,
    hidden: str,
    road: str,
    timing: str,
    lateral: str,
) -> dict[str, object]:
    return {
        "stable_materialization_spec_id": f"mat_{index}",
        "bounded_panel_spec_id": f"stable_bp_{index}",
        "scenario_spec_id": f"stable_bp_{index}",
        "materialized_bounded_panel_spec_id": f"stable_bp_{index}",
        "source_scenario_spec_id": f"stable_src_{index}",
        "materialized_source_scenario_spec_id": f"stable_src_{index}",
        "target_bounded_panel_spec_id": f"target_bp_{index}",
        "target_source_scenario_spec_id": f"target_src_{index}",
        "target_v2_task_label": label,
        "allowed_labels_metadata_only": label,
        "v2_role_surface_id": "stable_avoidance_aes",
        "role_panel_id": "stable_avoidance_aes",
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": road,
        "obstacle_timing_bucket": timing,
        "obstacle_lateral_bucket": lateral,
        "stable_materialization_key": f"stable_avoidance_aes|{label}|{hidden}|{road}|{timing}|{lateral}",
        "materialization_strategy": "label_specific_stable_sampler_repair_v1",
        "sampler_repair_variant_id": "stable_source_label_materialization_v1",
        "source_basis_support_status": "unsupported_systematic",
        "near_candidate_ids": "",
        "profile_controls_preserved": True,
        "labels_enter_actor_input": False,
        "reset_validation_required": True,
        "diagnostic_only_no_ranking_claim": True,
        "controller_family_ranking_admissible": False,
        "env_config": {
            "history_length": 1,
            "marker": f"stable_bp_{index}",
            "obstacle": {
                "allowed_labels": [label],
                "require_aeb_infeasible": label == "aes_feasible",
            },
        },
    }


def _profile_rows(specs: list[dict[str, object]], profiles: tuple[str, ...] = ("L0", "L1", "L2")) -> list[dict[str, object]]:
    rows = []
    for spec in specs:
        for profile in profiles:
            bounded_id = str(spec["materialized_bounded_panel_spec_id"])
            rows.append(
                {
                    "stable_materialization_workload_id": f"{bounded_id}::{profile}",
                    "scenario_workload_id": f"{bounded_id}::{profile}",
                    "scenario_spec_id": bounded_id,
                    "bounded_panel_spec_id": bounded_id,
                    "source_scenario_spec_id": str(spec["materialized_source_scenario_spec_id"]),
                    "target_bounded_panel_spec_id": str(spec["target_bounded_panel_spec_id"]),
                    "target_v2_task_label": str(spec["target_v2_task_label"]),
                    "v2_role_surface_id": "stable_avoidance_aes",
                    "stable_materialization_key": str(spec["stable_materialization_key"]),
                    "role_panel_id": "stable_avoidance_aes",
                    "hidden_dynamics_bucket": str(spec["hidden_dynamics_bucket"]),
                    "road_boundary_bucket": str(spec["road_boundary_bucket"]),
                    "obstacle_timing_bucket": str(spec["obstacle_timing_bucket"]),
                    "obstacle_lateral_bucket": str(spec["obstacle_lateral_bucket"]),
                    "profile_name": profile,
                    "profile_config_path": f"configs/{profile}.json",
                    "checkpoint_path": f"checkpoints/{profile}.pt",
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "evaluation_role": "benchmark",
                    "primary_metric_family": "avoidance_success",
                    "labels_enter_actor_input": False,
                    "reset_validation_required": True,
                    "measured_execution_admissible": False,
                    "controller_family_ranking_admissible": False,
                    "diagnostic_only_no_ranking_claim": True,
                    "environment_reset_scheduled": False,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    return rows


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, list[dict[str, object]]]:
    specs = [
        _spec(index=0, label="aes_feasible", hidden="nominal", road="nominal", timing="medium", lateral="center"),
        _spec(index=1, label="aeb_feasible", hidden="brake_variation", road="moderate", timing="late", lateral="wide"),
    ]
    specs_path = tmp_path / "stable_source_materialization_specs.json"
    matrix_path = tmp_path / "stable_source_materialization_matrix.csv"
    write_json(specs_path, {"stable_source_materialization_specs": specs})
    write_csv_rows(matrix_path, _profile_rows(specs))
    return specs_path, matrix_path, specs


def test_stable_source_reset_validation_adapter_writes_executable_v2_payload(tmp_path: Path) -> None:
    specs_path, matrix_path, _specs = _write_inputs(tmp_path)

    summary = adapter.run_executable_v2_stable_source_reset_validation_adapter(
        stable_materialization_specs_path=specs_path,
        stable_materialization_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
        target_materialization_spec_count=2,
        target_executable_spec_count=6,
        target_profile_count=3,
        target_role_surface_count=1,
    )

    assert summary["result_class"] == "executable_v2_stable_source_reset_validation_adapter_pass"
    assert summary["input_materialization_spec_count"] == 2
    assert summary["input_materialization_matrix_row_count"] == 6
    assert summary["targeted_reset_executable_spec_count"] == 6
    assert summary["profile_control_count"] == 3
    assert summary["role_surface_count"] == 1
    assert summary["reset_ready_spec_count"] == 6
    assert summary["reset_validation_required_count"] == 6
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["env_config_missing_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False

    payload = read_json(tmp_path / "out" / "targeted_reset_executable_v2_panel_specs.json")
    rows = payload["executable_v2_panel_specs"]
    assert len(rows) == 6
    row_by_id = {row["v2_panel_spec_id"]: row for row in rows}
    first = row_by_id["stable_bp_0::L0"]
    assert first["source_v1_bounded_panel_spec_id"] == "target_bp_0"
    assert first["source_scenario_spec_id"] == "stable_src_0"
    assert first["materialized_bounded_panel_spec_id"] == "stable_bp_0"
    assert first["profile_config_path"] == "configs/L0.json"
    assert first["v2_task_label"] == "aes_feasible"
    assert first["v2_primary_metric"] == "admissible_obstacle_pass_rate"
    assert first["v2_primary_metric_direction"] == "higher_is_better"
    assert first["v2_admissibility_gate"] == "collision_rate_low_and_off_track_rate_low"
    assert first["reset_ready_spec"] is True
    assert first["diagnostic_only_no_ranking_claim"] is True
    assert first["v2_ranking_admissible_by_default"] is False
    assert first["labels_enter_actor_input"] is False
    assert first["env_config"]["marker"] == "stable_bp_0"
    assert first["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"]

    matrix_csv = (tmp_path / "out" / "targeted_reset_validation_matrix.csv").read_text()
    assert "stable_bp_1::L2" in matrix_csv
    claim_boundary = (tmp_path / "out" / "targeted_reset_validation_claim_boundary.csv").read_text()
    assert "targeted_reset_validation_payload_ready" in claim_boundary
    assert "controller_family_ranking" in claim_boundary


def test_stable_source_reset_validation_adapter_flags_missing_and_duplicate_rows(tmp_path: Path) -> None:
    specs_path, matrix_path, specs = _write_inputs(tmp_path)
    rows = _profile_rows(specs, profiles=("L0",))
    rows.append(dict(rows[0]))
    rows.append(
        {
            **dict(rows[0]),
            "stable_materialization_workload_id": "missing_bp::L0",
            "bounded_panel_spec_id": "missing_bp",
            "scenario_spec_id": "missing_bp",
        }
    )
    write_csv_rows(matrix_path, rows)

    summary = adapter.run_executable_v2_stable_source_reset_validation_adapter(
        stable_materialization_specs_path=specs_path,
        stable_materialization_matrix_path=matrix_path,
        output_dir=tmp_path / "out",
        target_materialization_spec_count=2,
        target_executable_spec_count=3,
        target_profile_count=1,
        target_role_surface_count=1,
    )

    assert summary["result_class"] == "executable_v2_stable_source_reset_validation_adapter_fail"
    assert summary["missing_join_count"] == 1
    assert summary["duplicate_workload_count"] == 1
    missing = (tmp_path / "out" / "targeted_reset_missing_join_rows.csv").read_text()
    duplicates = (tmp_path / "out" / "targeted_reset_duplicate_workload_rows.csv").read_text()
    assert "missing_bp::L0" in missing
    assert "missing materialized stable source spec" in missing
    assert "stable_bp_0::L0" in duplicates
