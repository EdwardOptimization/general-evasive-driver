from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_executable_spec_materialization as materialization
from autodrift import paper_route_current_sim_terminal_boundary_reset_sampling_diagnostic as diagnostic
from autodrift.artifacts import read_json, write_json


def _write_target_spec(path: Path) -> dict[str, object]:
    summary = materialization.materialize_executable_specs(output_dir=path.parent / "materialization")
    assert summary["result_class"] == "current_sim_controlled_comparison_executable_spec_materialization_pass"
    specs = read_json(path.parent / "materialization" / "executable_task_specs.json")["executable_task_specs"]
    spec = specs[0]
    spec = dict(spec)
    spec["task_source_id"] = "target-row"
    write_json(path, {"protocol": "test", "executable_task_specs": [spec]})
    return spec


def _fake_reset(*, spec, eval_seed, expected_observation_dim):
    metadata = diagnostic.current_sim_metadata(spec)
    budget = int(spec["env_config"]["obstacle"]["max_sample_attempts"])
    success = int(eval_seed) == 10 and budget >= 800
    return {
        **metadata,
        "eval_seed": int(eval_seed),
        "reset_success": success,
        "error_type": "" if success else "RuntimeError",
        "error_message": "" if success else "failed to sample an obstacle scenario matching the configured filters",
        "observation_length": int(expected_observation_dim) if success else "",
        "expected_observation_length": int(expected_observation_dim),
        "observation_dimension_matches": success,
        "observation_finite": success,
        "obstacle_initialized": success,
        "reset_sampled_obstacle_label": "drift_required" if success else "",
        "initial_mu": 0.5 if success else "",
        "speed_ref": 18.0 if success else "",
        "obstacle_distance": 12.0 if success else "",
        "obstacle_half_width": 1.0 if success else "",
        "contract_violation_count": 0,
        "environment_reset_started": True,
        "environment_rollout_started": False,
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
        "finite_window_vs_gru_conclusion_made": False,
        "paper_level_claim_made": False,
        "level3_self_id_claim_made": False,
    }


def test_terminal_boundary_diagnostic_classifies_attempt_budget_limited(tmp_path: Path, monkeypatch) -> None:
    specs_path = tmp_path / "specs.json"
    _write_target_spec(specs_path)
    monkeypatch.setattr(diagnostic, "reset_current_sim_spec", _fake_reset)

    summary = diagnostic.run_terminal_boundary_reset_sampling_diagnostic(
        executable_task_specs_path=specs_path,
        target_task_source_id="target-row",
        output_dir=tmp_path / "out",
        eval_seeds=[10, 20],
        attempt_budgets=[200, 800, 1600],
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_terminal_boundary_reset_sampling_diagnostic_complete"
    assert summary["target_spec_count"] == 1
    assert summary["diagnostic_attempt_count"] == 6
    assert summary["observed_eval_seed_count"] == 2
    assert summary["observed_attempt_budget_count"] == 3
    assert summary["diagnostic_classification"] == "attempt_budget_limited"
    assert summary["contract_violation_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert (tmp_path / "out" / "diagnostic_rows.csv").exists()
    assert (tmp_path / "out" / "classification_rows.csv").exists()
    assert (tmp_path / "out" / "run_state.json").exists()


def test_terminal_boundary_diagnostic_fails_closed_on_missing_target(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    _write_target_spec(specs_path)

    summary = diagnostic.run_terminal_boundary_reset_sampling_diagnostic(
        executable_task_specs_path=specs_path,
        target_task_source_id="missing-row",
        output_dir=tmp_path / "out",
        eval_seeds=[10, 20],
        attempt_budgets=[200, 800, 1600],
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_terminal_boundary_reset_sampling_diagnostic_fail"
    assert summary["target_spec_count"] == 0
    assert summary["diagnostic_attempt_count"] == 0
