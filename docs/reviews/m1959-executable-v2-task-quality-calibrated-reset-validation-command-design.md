# m1959-executable-v2-task-quality-calibrated-reset-validation-command-design Research Review

## Summary

- Generated at UTC: 20260531T103148Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_reset_command_design_admit_focused_reset_validator
- Decision reason: M1959 freezes focused M1960 reset-only validation command over M1958 80 specs obs dim 72 while preserving calibrated repair metadata and keeping rollout/ranking blocked

## Hypothesis

An exact reset-only validation command can be designed for the M1958 executable task specs while preserving calibrated repair metadata, target counts, and human-view observation checks.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_reset_validation_command_design
- parent_dataset: docs/m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation.md, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation.json
- parent_objective: design exact calibrated reset-only validation command over M1958 executable task specs
- derived_from: m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation
- blocked_by: M1958 produces no-reset executable specs but reset validation has not been designed for the calibrated repair metadata schema
- supersedes: claiming reset validity from no-reset preflight artifacts
- invalidates: None

## Success Criteria

- docs/m1959-executable-v2-task-quality-calibrated-reset-validation-command-design.md exists
- reset-only command target and output directory are explicit
- target reset count is 80
- expected observation dimension is 72
- metadata preservation and pass/fail gates are explicit
- next implementation or execution route is explicit
- no reset rollout measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- reset command is ambiguous
- target counts are ambiguous
- calibrated repair metadata preservation is not specified
- reset rollout measured execution ranking or paper-level claims are made

## Evidence Gates

- M1959 must design the exact reset-only validation command for M1958 executable task specs
- M1959 must decide whether to wrap or extend the generic reset validator to preserve calibrated repair metadata
- M1959 must specify target reset counts observation dimension and pass/fail gates
- M1959 must keep rollout measured execution ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
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

- milestone: m1959-executable-v2-task-quality-calibrated-reset-validation-command-design
- type: gate
- checkpoint: docs/m1959-executable-v2-task-quality-calibrated-reset-validation-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_reset_command_design_admit_focused_reset_validator
- reason: M1959 freezes focused M1960 reset-only validation command over M1958 80 specs obs dim 72 while preserving calibrated repair metadata and keeping rollout/ranking blocked

## Next Blocker

m1959-executable-v2-task-quality-calibrated-reset-validation-command-design
