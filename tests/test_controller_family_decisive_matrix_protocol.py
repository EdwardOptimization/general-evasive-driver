from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_decisive_matrix_protocol import (
    EXPECTED_PROFILE_NAMES,
    profile_contract_violations,
    run_protocol_preflight,
)


def test_profile_contract_violations_flags_privileged_fields() -> None:
    config = {
        "controller_profile": {
            "input_contract": "P0_human_view_no_wheel_no_oracle",
            "corrected_profile_config": True,
            "uses_hidden_oracle_actor_inputs": True,
        },
        "env": {
            "include_privileged_params": True,
            "wheel_observation_mode": "raw",
            "obstacle_relative_velocity_mode": "ego",
        },
    }

    violations = profile_contract_violations(config)

    assert "profile_uses_hidden_oracle_actor_inputs_true" in violations
    assert "env_include_privileged_params_true" in violations
    assert "env_wheel_observation_mode_not_none" in violations
    assert "obstacle_relative_velocity_mode_not_zero" in violations


def test_run_protocol_preflight_writes_no_training_protocol(tmp_path: Path) -> None:
    summary = run_protocol_preflight(output_dir=tmp_path)

    protocol = read_json(tmp_path / "matrix_protocol.json")
    persisted_summary = read_json(tmp_path / "summary.json")

    assert summary["passes_public_smoke_gates"] is True
    assert persisted_summary["profile_config_count"] == len(EXPECTED_PROFILE_NAMES)
    assert persisted_summary["contract_violation_count"] == 0
    assert persisted_summary["training_started"] is False
    assert persisted_summary["replay_started"] is False
    assert persisted_summary["ppo_used"] is False
    assert persisted_summary["private_holdout_used"] is False
    assert persisted_summary["artifact_first_check_pass"] is False
    assert len(protocol["controller_families"]) == len(EXPECTED_PROFILE_NAMES)
    assert protocol["claim_scope"] == "public protocol preflight only"
    assert "L2_normal_minus_L2_current_tiled" in protocol["history_specific_comparisons"]
