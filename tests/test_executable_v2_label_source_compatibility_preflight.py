from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import executable_v2_label_source_compatibility_preflight as compat


def _spec(
    *,
    spec_id: str,
    source: str,
    surface: str,
    label: str,
    hidden: str,
    profile: str,
) -> dict[str, object]:
    return {
        "v2_panel_spec_id": spec_id,
        "source_v1_bounded_panel_spec_id": source,
        "source_v1_role_panel_id": surface,
        "source_scenario_spec_id": source,
        "v2_role_surface_id": surface,
        "role_panel_id": surface,
        "profile_name": profile,
        "profile_config_path": f"{profile}.json",
        "checkpoint_path": "unused.pt",
        "config_exists": True,
        "checkpoint_exists": True,
        "v2_task_label": label,
        "allowed_labels_metadata_only": label,
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": "moderate",
        "obstacle_timing_bucket": "late",
        "obstacle_lateral_bucket": "center",
        "v2_primary_metric": "admissible_obstacle_pass_rate",
        "v2_primary_metric_direction": "higher",
        "v2_supporting_metrics": "collision_failure_rate",
        "v2_admissibility_gate": "collision_rate_low_and_off_track_rate_low",
        "env_config": {"include_privileged_params": False, "marker": spec_id},
        "reset_ready_spec": True,
        "diagnostic_only_no_ranking_claim": True,
        "v2_ranking_admissible_by_default": False,
        "environment_reset_scheduled": False,
        "environment_rollout_scheduled": False,
        "training_scheduled": False,
        "profile_specific_tuning": False,
    }


def _reset_row(spec: dict[str, object], *, success: bool, message: str = "") -> dict[str, object]:
    return {
        "v2_panel_spec_id": spec["v2_panel_spec_id"],
        "source_v1_bounded_panel_spec_id": spec["source_v1_bounded_panel_spec_id"],
        "source_v1_role_panel_id": spec["source_v1_role_panel_id"],
        "source_scenario_spec_id": spec["source_scenario_spec_id"],
        "v2_role_surface_id": spec["v2_role_surface_id"],
        "role_panel_id": spec["role_panel_id"],
        "profile_name": spec["profile_name"],
        "eval_seed": 9000,
        "v2_task_label": spec["v2_task_label"],
        "allowed_labels_metadata_only": spec["allowed_labels_metadata_only"],
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": spec["hidden_dynamics_bucket"],
        "road_boundary_bucket": spec["road_boundary_bucket"],
        "obstacle_timing_bucket": spec["obstacle_timing_bucket"],
        "obstacle_lateral_bucket": spec["obstacle_lateral_bucket"],
        "v2_primary_metric": spec["v2_primary_metric"],
        "v2_primary_metric_direction": spec["v2_primary_metric_direction"],
        "v2_admissibility_gate": spec["v2_admissibility_gate"],
        "reset_ready_spec": True,
        "diagnostic_only_no_ranking_claim": True,
        "v2_ranking_admissible_by_default": False,
        "environment_reset_started": True,
        "policy_action_executed": False,
        "measured_rollout_started": False,
        "training_started": False,
        "replay_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "actor_input_contract_changed": False,
        "profile_specific_tuning": False,
        "controller_family_ranking_claim_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
        "reset_success": success,
        "error_type": "" if success else "RuntimeError",
        "error_message": message,
        "sampled_obstacle_label": spec["v2_task_label"] if success else "",
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    specs = [
        _spec(spec_id="s0", source="src_supported", surface="stable_avoidance_aes", label="aeb_feasible", hidden="nominal", profile="p0"),
        _spec(spec_id="s1", source="src_supported", surface="stable_avoidance_aes", label="aeb_feasible", hidden="nominal", profile="p1"),
        _spec(spec_id="u0", source="src_unsupported", surface="stable_avoidance_aes", label="aes_feasible", hidden="friction_step", profile="p0"),
        _spec(spec_id="u1", source="src_unsupported", surface="stable_avoidance_aes", label="aes_feasible", hidden="friction_step", profile="p1"),
        _spec(spec_id="f0", source="src_sparse", surface="hidden_robust_aes_feasible", label="aes_feasible", hidden="actuator_delay", profile="p0"),
        _spec(spec_id="f1", source="src_sparse", surface="hidden_robust_aes_feasible", label="aes_feasible", hidden="actuator_delay", profile="p1"),
        _spec(spec_id="f2", source="src_sparse", surface="hidden_robust_aes_feasible", label="aes_feasible", hidden="actuator_delay", profile="p2"),
    ]
    reset_rows = [
        _reset_row(specs[0], success=True),
        _reset_row(specs[1], success=True),
        _reset_row(specs[2], success=False, message="systematic source-label failure"),
        _reset_row(specs[3], success=False, message="systematic source-label failure"),
        _reset_row(specs[4], success=True),
        _reset_row(specs[5], success=False, message="sparse profile failure"),
        _reset_row(specs[6], success=True),
    ]
    specs_path = tmp_path / "specs.json"
    reset_path = tmp_path / "reset_rows.csv"
    write_json(specs_path, {"executable_v2_panel_specs": specs})
    write_csv_rows(reset_path, reset_rows)
    return specs_path, reset_path


def test_label_source_compatibility_preflight_classifies_support_and_writes_outputs(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)

    summary = compat.run_executable_v2_label_source_compatibility_preflight(
        executable_v2_panel_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        target_input_spec_count=7,
        target_profile_count=3,
    )

    assert summary["result_class"] == "executable_v2_label_source_compatibility_preflight_pass"
    assert summary["input_spec_count"] == 7
    assert summary["compatible_spec_count"] == 4
    assert summary["compatibility_violation_count"] == 2
    assert summary["sparse_failure_count"] == 1
    assert summary["replacement_need_count"] == 2
    assert summary["support_status_counts"] == {
        "sparse_fragile": 1,
        "supported_observed": 1,
        "unsupported_systematic": 1,
    }
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["measured_execution_admissible"] is False
    assert summary["controller_family_ranking_admissible"] is False

    support_csv = (tmp_path / "out" / "source_label_support.csv").read_text()
    assert "supported_observed" in support_csv
    assert "unsupported_systematic" in support_csv
    assert "sparse_fragile" in support_csv
    assert "source_label_group_id" in support_csv

    violations = (tmp_path / "out" / "compatibility_violation_rows.csv").read_text()
    assert "u0" in violations
    assert "systematic source-label failure" in violations
    sparse = (tmp_path / "out" / "sparse_failure_rows.csv").read_text()
    assert "f1" in sparse
    assert "sparse profile failure" in sparse
    replacements = (tmp_path / "out" / "replacement_need_rows.csv").read_text()
    assert "find_or_materialize_alternate_source_with_observed_label_support" in replacements
    assert "run_seed_fragility_or_tight_filter_probe_after_systematic_repair" in replacements

    compatible_payload = read_json(tmp_path / "out" / "compatible_executable_v2_panel_specs.json")
    compatible_ids = {row["v2_panel_spec_id"] for row in compatible_payload["executable_v2_panel_specs"]}
    assert compatible_ids == {"s0", "s1", "f0", "f2"}
    by_id = {row["v2_panel_spec_id"]: row for row in compatible_payload["executable_v2_panel_specs"]}
    assert by_id["s0"]["env_config"]["marker"] == "s0"
    assert by_id["s0"]["compatible_for_reset_rerun"] is True
    claim_boundary = (tmp_path / "out" / "claim_boundary.csv").read_text()
    assert "controller_family_ranking" in claim_boundary
    assert "False" in claim_boundary


def test_label_source_compatibility_preflight_tracks_unobserved_specs(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)
    payload = read_json(specs_path)
    payload["executable_v2_panel_specs"].append(
        _spec(spec_id="missing", source="src_missing", surface="stable_avoidance_aes", label="aes_feasible", hidden="nominal", profile="p0")
    )
    write_json(specs_path, payload)

    summary = compat.run_executable_v2_label_source_compatibility_preflight(
        executable_v2_panel_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        target_input_spec_count=8,
        target_profile_count=3,
    )

    assert summary["input_spec_count"] == 8
    assert summary["unobserved_count"] == 1
    assert summary["replacement_need_count"] == 3
    unobserved = (tmp_path / "out" / "unobserved_rows.csv").read_text()
    assert "missing" in unobserved
    assert "missing reset row" in unobserved
