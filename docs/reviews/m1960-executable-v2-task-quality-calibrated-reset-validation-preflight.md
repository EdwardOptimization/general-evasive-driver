# m1960-executable-v2-task-quality-calibrated-reset-validation-preflight Research Review

## Summary

- Generated at UTC: 20260531T103700Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_reset_validation_pass_route_to_result_audit
- Decision reason: M1960 reset-only validation pass 80 attempts 80 successes 0 failures finite obs 80 contract 0 forbidden-key 0 source quotas pass guardrail 0

## Hypothesis

The M1958 calibrated 80-spec public task-quality panel is reset-valid under the current simulator and strict human-view contract.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_reset_validation_preflight
- parent_dataset: docs/m1959-executable-v2-task-quality-calibrated-reset-validation-command-design.md, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json
- parent_config: experiments/manifests/m1959-executable-v2-task-quality-calibrated-reset-validation-command-design.json
- parent_objective: run reset-only validation over the M1958 calibrated executable task specs
- derived_from: m1959-executable-v2-task-quality-calibrated-reset-validation-command-design
- blocked_by: real reset validation has not been run over the M1958 calibrated executable panel
- supersedes: claiming reset validity from no-reset materialization preflight alone
- invalidates: None

## Success Criteria

- runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json exists
- result_class is task_quality_calibrated_reset_validation_preflight_pass
- reset_attempt_count equals 80
- reset_success_count equals 80
- reset_failure_count equals 0
- contract_violation_count equals 0
- guardrail_violation_count equals 0

## Failure Criteria

- summary is missing
- reset_attempt_count differs from 80
- any reset fails
- any contract or guardrail violation appears
- rollout measured execution ranking or paper-level claims are made

## Evidence Gates

- M1960 must run exactly the frozen reset-only command
- M1960 must attempt 80 resets and write reset rows preserving calibrated repair metadata
- M1960 must preserve failure rows if any reset fails
- M1960 must keep rollout measured execution ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1960-executable-v2-task-quality-calibrated-reset-validation-preflight
- type: infrastructure
- checkpoint: runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0000000000
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_reset_validation_pass_route_to_result_audit
- reason: M1960 reset-only validation pass 80 attempts 80 successes 0 failures finite obs 80 contract 0 forbidden-key 0 source quotas pass guardrail 0

## Next Blocker

m1960-executable-v2-task-quality-calibrated-reset-validation-preflight
