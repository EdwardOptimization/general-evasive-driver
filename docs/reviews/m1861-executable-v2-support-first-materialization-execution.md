# m1861-executable-v2-support-first-materialization-execution Research Review

## Summary

- Generated at UTC: 20260530T134219Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: support_first_materialization_execution_pass_route_to_result_audit
- Decision reason: M1861 materialized 180 capped executable-v2 candidate specs from 90 sources with duplicate 0 labels actor 0 guardrail 0

## Hypothesis

Bounded materialization can produce capped executable-v2 candidate artifacts from supported sources without reset or measured execution.

## Lineage

- parent_checkpoint: not_applicable_support_first_materialization_execution
- parent_dataset: docs/m1860-executable-v2-support-first-materialization-execution-design.md, runs/m1856_executable_v2_support_first_source_mining/support_first_accepted_cells.csv, runs/m1856_executable_v2_support_first_source_mining/support_first_materialization_admissibility_input.csv, configs/executable_v2_support_first_candidate_templates_v0.json
- parent_config: experiments/manifests/m1860-executable-v2-support-first-materialization-execution-design.json
- parent_objective: run bounded support-first materialization
- derived_from: m1860-executable-v2-support-first-materialization-execution-design
- blocked_by: M1860 fixes exact materialization command
- supersedes: unbounded materialization
- invalidates: None

## Success Criteria

- runs/m1861_executable_v2_support_first_materialization/summary.json exists
- selected_source_count is at most 96
- materialized_spec_count is at most 192
- duplicate_key_count equals 0
- labels_enter_actor_input_count equals 0
- guardrail_violation_count equals 0

## Failure Criteria

- materialization command fails
- summary is missing
- selected source or materialized spec count exceeds caps
- duplicate keys are present
- labels enter actor inputs
- execution runs reset rollout training replay PPO or ranking

## Evidence Gates

- M1861 must run the exact M1860 command
- M1861 must keep reset rollout measured rollout training replay PPO promotion ranking and paper-level claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun source mining
- do not generate source repair payload
- do not run environment reset
- do not run environment rollout
- do not run measured rollout
- do not execute policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1861-executable-v2-support-first-materialization-execution
- type: infrastructure
- checkpoint: runs/m1861_executable_v2_support_first_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: support_first_materialization_execution_pass_route_to_result_audit
- reason: M1861 materialized 180 capped executable-v2 candidate specs from 90 sources with duplicate 0 labels actor 0 guardrail 0

## Next Blocker

m1862-executable-v2-support-first-materialization-result-audit
