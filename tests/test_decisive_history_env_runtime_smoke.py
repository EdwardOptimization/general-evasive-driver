from dataclasses import replace

from autodrift.decisive_history_env_hooks import default_hook_specs
from autodrift.decisive_history_env_runtime_smoke import (
    build_runtime_smoke_summary,
    reset_hook_spec,
    run_env_hook_runtime_smoke,
)


def test_reset_hook_spec_instantiates_env_without_policy_replay():
    spec = default_hook_specs(seed_count=1)[0]

    row = reset_hook_spec(spec)

    assert row.reset_success is True
    assert row.failure_type == "none"
    assert row.observation_dim == row.expected_observation_dim == 72
    assert row.obstacle_enabled is True
    assert row.policy_replay_started is False
    assert row.replay_started is False
    assert row.training_started is False
    assert row.candidate_materialized is False


def test_runtime_smoke_writes_reset_only_artifacts(tmp_path):
    summary = run_env_hook_runtime_smoke(tmp_path / "runtime", seed_count=1)

    assert summary["result_class"] == "decisive_history_env_hook_runtime_smoke"
    assert summary["runtime_scope"] == "reset_only"
    assert summary["hook_spec_count"] == 6
    assert summary["source_family_count"] == 6
    assert summary["reset_success_count"] == 6
    assert summary["reset_failure_count"] == 0
    assert summary["all_source_families_reset"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["env_reset_called"] is True
    assert summary["env_step_called"] is False
    assert summary["candidate_materialized"] is False
    assert summary["policy_replay_started"] is False
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["training_corpus_exported"] is False
    assert summary["labels_enter_actor_input"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert (tmp_path / "runtime" / "runtime_rows.csv").exists()
    assert (tmp_path / "runtime" / "runtime_source_family_summary.csv").exists()
    assert (tmp_path / "runtime" / "runtime_guardrail_summary.csv").exists()
    assert (tmp_path / "runtime" / "summary.json").exists()


def test_runtime_summary_counts_failures_without_promoting_evidence():
    spec = default_hook_specs(seed_count=1)[0]
    ok = reset_hook_spec(spec)
    failed = replace(ok, reset_success=False, failure_type="scenario_sampling_failure")

    summary = build_runtime_smoke_summary([ok, failed])

    assert summary["reset_success_count"] == 1
    assert summary["reset_failure_count"] == 1
    assert summary["failure_type_counts"] == {"scenario_sampling_failure": 1}
    assert summary["candidate_materialized"] is False
    assert summary["policy_replay_started"] is False
