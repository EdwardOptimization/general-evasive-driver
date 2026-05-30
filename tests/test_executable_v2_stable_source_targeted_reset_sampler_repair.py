from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import executable_v2_stable_source_targeted_reset_sampler_repair as repair


def _spec(source: str, profile: str, label: str, hidden: str) -> dict[str, object]:
    return {
        "v2_panel_spec_id": f"{source}::{profile}",
        "materialized_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_src",
        "v2_role_surface_id": "stable_avoidance_aes",
        "role_panel_id": "stable_avoidance_aes",
        "profile_name": profile,
        "profile_config_path": f"configs/{profile}.json",
        "checkpoint_path": f"checkpoints/{profile}.pt",
        "v2_task_label": label,
        "allowed_labels_metadata_only": label,
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": hidden,
        "road_boundary_bucket": "nominal",
        "obstacle_timing_bucket": "medium",
        "obstacle_lateral_bucket": "center",
        "v2_primary_metric": "admissible_obstacle_pass_rate",
        "v2_primary_metric_direction": "higher_is_better",
        "v2_admissibility_gate": "collision_rate_low_and_off_track_rate_low",
        "reset_ready_spec": True,
        "reset_validation_required": True,
        "diagnostic_only_no_ranking_claim": True,
        "v2_ranking_admissible_by_default": False,
        "env_config": {
            "history_length": 1,
            "speed_range": [10.0, 18.0],
            "randomization": {"mu_range": [0.35, 1.0]},
            "obstacle": {
                "enabled": True,
                "allowed_labels": [label],
                "require_aeb_infeasible": label == "aes_feasible",
                "max_sample_attempts": 1000,
                "distance_range": [18.0, 42.0],
                "half_width_range": [0.55, 1.10],
                "ego_half_width": 0.9,
                "safety_margin": 0.3,
                "brake_mu_fraction": 0.9,
                "conventional_lateral_mu_fraction": 0.42,
                "drift_lateral_mu_fraction": 0.85,
            },
        },
    }


def _reset_row(spec: dict[str, object], success: bool) -> dict[str, object]:
    return {
        "v2_panel_spec_id": spec["v2_panel_spec_id"],
        "source_scenario_spec_id": spec["source_scenario_spec_id"],
        "v2_role_surface_id": spec["v2_role_surface_id"],
        "role_panel_id": spec["role_panel_id"],
        "profile_name": spec["profile_name"],
        "v2_task_label": spec["v2_task_label"],
        "allowed_labels_metadata_only": spec["allowed_labels_metadata_only"],
        "labels_enter_actor_input": False,
        "hidden_dynamics_bucket": spec["hidden_dynamics_bucket"],
        "road_boundary_bucket": spec["road_boundary_bucket"],
        "obstacle_timing_bucket": spec["obstacle_timing_bucket"],
        "obstacle_lateral_bucket": spec["obstacle_lateral_bucket"],
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
        "error_message": "" if success else "failed to sample an obstacle scenario matching the configured filters",
        "sampled_obstacle_label": spec["v2_task_label"] if success else "",
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    profiles = ("L0", "L1", "L2")
    specs = []
    for source, label, hidden in (("aes_src", "aes_feasible", "nominal"), ("aeb_src", "aeb_feasible", "brake_variation")):
        for profile in profiles:
            specs.append(_spec(source, profile, label, hidden))

    reset_rows = []
    for spec in specs:
        if spec["materialized_bounded_panel_spec_id"] == "aes_src":
            reset_rows.append(_reset_row(spec, success=False))
        else:
            reset_rows.append(_reset_row(spec, success=spec["profile_name"] != "L1"))

    specs_path = tmp_path / "targeted.json"
    reset_path = tmp_path / "reset.csv"
    write_json(specs_path, {"executable_v2_panel_specs": specs})
    write_csv_rows(reset_path, reset_rows)
    return specs_path, reset_path


def test_targeted_reset_sampler_repair_planner_writes_repaired_payload(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)

    summary = repair.run_targeted_reset_sampler_repair_planner(
        targeted_reset_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        target_repair_source_count=2,
        target_profile_count=3,
        target_repaired_spec_count=6,
    )

    assert summary["result_class"] == "targeted_reset_sampler_repair_planner_pass"
    assert summary["repair_target_source_count"] == 2
    assert summary["systematic_source_count"] == 1
    assert summary["sparse_source_count"] == 1
    assert summary["profile_control_count"] == 3
    assert summary["repaired_executable_spec_count"] == 6
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False

    payload = read_json(tmp_path / "out" / "repaired_targeted_reset_executable_v2_panel_specs.json")
    rows = payload["executable_v2_panel_specs"]
    assert len(rows) == 6
    by_id = {row["v2_panel_spec_id"]: row for row in rows}
    aes = by_id["aes_src::L0"]
    aeb = by_id["aeb_src::L0"]
    assert aes["source_sampler_repair_applied"] is True
    assert aes["source_sampler_repair_class"] == "systematic"
    assert aes["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"]
    assert aes["env_config"]["obstacle"]["require_aeb_infeasible"] is True
    assert aes["env_config"]["obstacle"]["max_sample_attempts"] >= 10000
    assert aeb["source_sampler_repair_class"] == "sparse"
    assert aeb["env_config"]["obstacle"]["allowed_labels"] == ["aeb_feasible"]
    assert aeb["env_config"]["obstacle"]["require_aeb_infeasible"] is False
    assert aeb["env_config"]["obstacle"]["max_sample_attempts"] >= 5000
    assert {row["profile_name"] for row in rows} == {"L0", "L1", "L2"}

    targets = (tmp_path / "out" / "source_sampler_repair_targets.csv").read_text()
    assert "systematic" in targets
    assert "sparse" in targets
    claim_boundary = (tmp_path / "out" / "source_sampler_repair_claim_boundary.csv").read_text()
    assert "reset_feasibility_repaired,False" in claim_boundary


def test_targeted_reset_sampler_repair_planner_passes_through_successful_sources(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)
    payload = read_json(specs_path)
    payload["executable_v2_panel_specs"].append(_spec("ok_src", "L0", "aeb_feasible", "nominal"))
    write_json(specs_path, payload)
    rows = repair.load_reset_rows(reset_path)
    rows.append(_reset_row(payload["executable_v2_panel_specs"][-1], success=True))
    write_csv_rows(reset_path, rows)

    summary = repair.run_targeted_reset_sampler_repair_planner(
        targeted_reset_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        target_repair_source_count=2,
        target_profile_count=3,
        target_repaired_spec_count=7,
    )

    assert summary["result_class"] == "targeted_reset_sampler_repair_planner_pass"
    payload = read_json(tmp_path / "out" / "repaired_targeted_reset_executable_v2_panel_specs.json")
    ok = next(row for row in payload["executable_v2_panel_specs"] if row["v2_panel_spec_id"] == "ok_src::L0")
    assert ok["source_sampler_repair_applied"] is False
