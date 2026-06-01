from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_current_sim_scenario_task_family_config_materialization import (
    REQUIRED_METADATA_FIELDS,
    TARGET_ROLE_FAMILY_COUNT,
    TARGET_SCENARIO_SPEC_COUNT,
    TARGET_SPECS_PER_ROLE,
    materialize_scenario_specs,
    run_config_materialization,
)


def test_materialized_specs_use_correct_role_mapping_and_contract() -> None:
    specs, contract_violations, unsupported_rows = materialize_scenario_specs()

    assert len(specs) == TARGET_SCENARIO_SPEC_COUNT
    assert not contract_violations
    role_counts = {}
    for row in specs:
        role_counts[row["role_family"]] = role_counts.get(row["role_family"], 0) + 1
    assert len(role_counts) == TARGET_ROLE_FAMILY_COUNT
    assert min(role_counts.values()) == TARGET_SPECS_PER_ROLE
    assert {row["sampled_obstacle_label"] for row in specs if row["scenario_family_id"] == "R0"} == {
        "aeb_feasible"
    }
    assert {row["sampled_obstacle_label"] for row in specs if row["scenario_family_id"] == "R1"} == {
        "aes_feasible"
    }
    assert all(row["labels_enter_actor_input"] is False for row in specs)
    assert all(row["ranking_admissible"] is False for row in specs)
    assert all(row["wheel_observation_mode"] == "none" for row in specs)
    assert all(row["obstacle_relative_velocity_mode"] == "zero" for row in specs)
    assert {row["obstacle_longitudinal_timing_bucket"] for row in specs} == {
        "early_far",
        "mid",
        "late_close",
    }
    assert {row["obstacle_lateral_offset_bucket"] for row in specs} == {
        "centerline",
        "left_offset",
        "right_offset",
    }
    assert len({row["hidden_dynamics_bucket"] for row in specs if row["scenario_family_id"] == "R5"}) >= 4
    assert not any(row["capability"] == "emergency_obstacle_lateral_offset" for row in unsupported_rows)
    assert all(row["silently_approximated"] is False for row in unsupported_rows)


def test_required_metadata_fields_are_present() -> None:
    specs, _, _ = materialize_scenario_specs()

    missing = []
    for row in specs:
        for field in REQUIRED_METADATA_FIELDS:
            value = row.get(field)
            if value is None or value == "" or (field == "env_config" and not value):
                missing.append((row["scenario_spec_id"], field))
    assert missing == []


def test_run_config_materialization_writes_no_reset_artifacts(tmp_path: Path) -> None:
    config_output = tmp_path / "paper_route_current_sim_scenario_task_family_v0.json"
    output_dir = tmp_path / "run"

    summary = run_config_materialization(config_output=config_output, output_dir=output_dir, next_blocker="next")

    assert summary["result_class"] == "current_sim_scenario_task_family_config_materialization_pass"
    assert summary["scenario_family_count"] == TARGET_ROLE_FAMILY_COUNT
    assert summary["scenario_spec_count"] == TARGET_SCENARIO_SPEC_COUNT
    assert summary["metadata_missing_required_field_count"] == 0
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["actor_contract_violation_count"] == 0
    assert summary["ranking_admissible_count"] == 0
    assert summary["guardrail_flags"]["environment_reset_started"] is False
    assert summary["guardrail_flags"]["environment_rollout_started"] is False
    assert summary["guardrail_flags"]["training_started"] is False
    assert summary["guardrail_violation_count"] == 0
    assert summary["unsupported_execution_blocker_count"] == 0
    assert summary["execution_admissible_without_instrumentation"] is True
    assert summary["primary_route"] == "scenario_task_family_result_audit_route_to_reset_validation_design"
    assert config_output.exists()
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "scenario_family_specs.csv").exists()
    assert (output_dir / "metadata_schema.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()

    payload = read_json(config_output)
    assert payload["actor_contract_id"] == "P0_human_view_no_wheel_no_oracle"
    assert len(payload["scenario_specs"]) == TARGET_SCENARIO_SPEC_COUNT
