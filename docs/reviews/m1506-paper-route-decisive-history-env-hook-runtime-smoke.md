# m1506-paper-route-decisive-history-env-hook-runtime-smoke Research Review

## Summary

- Generated at UTC: 20260529T083806Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: decisive_history_env_hook_runtime_smoke_pass_admit_rollout_candidate_design
- Decision reason: M1506 reset-only current-sim runtime smoke passed 6 of 6 source families after hook sampling repair with zero guardrail violations

## Hypothesis

The M1505 hook specs can instantiate current-sim env configs for a tiny source-diverse subset without actor-input or guardrail violations.

## Lineage

- parent_checkpoint: not_applicable_infrastructure_task
- parent_dataset: docs/m1505-paper-route-decisive-history-env-hook-implementation.md, runs/m1505_decisive_history_env_hook_dry_smoke/summary.json
- parent_config: experiments/manifests/m1505-paper-route-decisive-history-env-hook-implementation.json
- parent_objective: run reset-only current-sim runtime smoke for decisive-history hook specs
- derived_from: m1505-paper-route-decisive-history-env-hook-implementation
- blocked_by: dry hook specs exist, but current-sim reset/runtime viability is untested
- supersedes: full policy replay before reset-only hook runtime smoke
- invalidates: None

## Success Criteria

- runs/m1506_decisive_history_env_hook_runtime_smoke/summary.json exists
- all six source families have at least one reset/runtime pass row
- reset/runtime failure count is zero or failures are explicitly classified
- labels_enter_actor_input is false
- actor_input_contract_changed is false
- policy_replay_started training_started replay_started ppo_used promoted private_holdout_used training_corpus_exported are false
- candidate_materialized is false

## Failure Criteria

- summary is missing
- source-family reset/runtime viability is unreported
- guardrail flags are violated
- result is interpreted as decisive-history candidate or self-ID evidence

## Evidence Gates

- M1506 must instantiate current-sim env configs for a tiny source-diverse hook subset
- M1506 must use reset-only or explicitly bounded no-policy runtime checks
- M1506 must not run policy replay, PPO, training, promotion, private holdout, actor-input changes, or corpus export
- M1506 must report per-source-family reset success and guardrails
- M1506 must route to rollout-candidate design or env-hook repair

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run policy replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not materialize decisive-history candidates from reset-only evidence
- do not claim self-identification from reset-only runtime smoke

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1506-paper-route-decisive-history-env-hook-runtime-smoke
- type: infrastructure
- checkpoint: runs/m1506_decisive_history_env_hook_runtime_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: decisive_history_env_hook_runtime_smoke_pass_admit_rollout_candidate_design
- reason: M1506 reset-only current-sim runtime smoke passed 6 of 6 source families after hook sampling repair with zero guardrail violations

## Next Blocker

m1507-paper-route-decisive-history-rollout-candidate-design
