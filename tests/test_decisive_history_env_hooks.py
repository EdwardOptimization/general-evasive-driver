import pytest

from autodrift.decisive_history_candidate_planner import CandidateSourcePlan
from autodrift.decisive_history_env_hooks import (
    build_env_hook_summary,
    default_hook_specs,
    env_config_for_hook_spec,
    hook_spec_to_candidate_stub,
    run_env_hook_dry_smoke,
    source_plan_to_hook_specs,
)


def test_default_hook_specs_cover_all_source_families_without_shortcuts():
    specs = default_hook_specs(seed_count=1)

    assert {spec.source_family for spec in specs} == {
        "t4_staged_warmup_capability",
        "t4_capability_step_temporal",
        "t4_actuator_delay_response",
        "t5_near_boundary_warmup",
        "t5_high_speed_close_obstacle",
        "t5_boundary_axis_retarget",
    }
    assert {spec.task_family for spec in specs} == {"T4", "T5"}
    assert all(spec.labels_enter_actor_input is False for spec in specs)
    assert all(spec.candidate_materialized is False for spec in specs)
    assert all(spec.simulator_rollout_started is False for spec in specs)


def test_env_configs_preserve_p0_contract_and_family_hooks():
    staged = env_config_for_hook_spec(
        source_family="t4_staged_warmup_capability",
        capability_pair="low_mu|high_mu",
        reveal_step=32,
    )
    temporal = env_config_for_hook_spec(
        source_family="t4_capability_step_temporal",
        capability_pair="drive_low|drive_high",
        reveal_step=36,
    )
    high_speed = env_config_for_hook_spec(
        source_family="t5_high_speed_close_obstacle",
        capability_pair="brake_low|brake_high",
        reveal_step=22,
    )

    for config in (staged, temporal, high_speed):
        assert config.history_length == 1
        assert config.action_history_mode == "full"
        assert config.include_privileged_params is False
        assert config.wheel_observation_mode == "none"
        assert config.obstacle_relative_velocity_mode == "zero"
        assert config.obstacle.enabled is True

    assert staged.warmup_gate.enabled is True
    assert temporal.friction_step.enabled is True
    assert high_speed.friction_limited_speed is False
    assert high_speed.speed_range[0] >= 14.0


def test_source_plan_conversion_rejects_invalid_plan():
    invalid = CandidateSourcePlan(
        source_family="bad",
        task_family="T6",
        seed_base=1,
        seed_count=1,
        capability_pairs=("a|b",),
        geometry_keys=("g",),
        reveal_steps=(10,),
    )

    with pytest.raises(ValueError, match="unknown_task_family"):
        source_plan_to_hook_specs(invalid)


def test_hook_spec_candidate_stub_is_not_materialized_evidence():
    spec = default_hook_specs(seed_count=1)[0]

    candidate = hook_spec_to_candidate_stub(spec)

    assert candidate.candidate_id == spec.candidate_id
    assert candidate.task_family == spec.task_family
    assert candidate.labels_enter_actor_input is False
    assert candidate.current_distance == 0.0
    assert candidate.older_history_distance == 0.0


def test_env_hook_dry_smoke_writes_artifacts_without_rollout(tmp_path):
    summary = run_env_hook_dry_smoke(tmp_path / "hooks", seed_count=2)

    assert summary["result_class"] == "decisive_history_env_hook_dry_smoke"
    assert summary["hook_spec_count"] == 12
    assert summary["source_family_count"] == 6
    assert summary["task_family_counts"] == {"T4": 6, "T5": 6}
    assert summary["unique_seeds"] == 12
    assert summary["guardrail_violation_count"] == 0
    assert summary["labels_enter_actor_input"] is False
    assert summary["candidate_materialized"] is False
    assert summary["simulator_rollout_started"] is False
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["training_corpus_exported"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert (tmp_path / "hooks" / "hook_spec_rows.csv").exists()
    assert (tmp_path / "hooks" / "hook_source_family_summary.csv").exists()
    assert (tmp_path / "hooks" / "hook_guardrail_summary.csv").exists()
    assert (tmp_path / "hooks" / "summary.json").exists()


def test_env_hook_summary_flags_guardrail_violations():
    spec = default_hook_specs(seed_count=1)[0]
    bad = type(spec)(
        **{
            **spec.__dict__,
            "labels_enter_actor_input": True,
        }
    )

    summary = build_env_hook_summary([bad])

    assert summary["labels_enter_actor_input"] is True
    assert summary["guardrail_violation_count"] == 1
