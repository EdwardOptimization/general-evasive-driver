# m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design Research Review

## Summary

- Generated at UTC: 20260531T132218Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_outcome_support_repaired_reset_rerun_command_design_admit_execution
- Decision reason: M1995 freezes exact repaired reset-only rerun command in fresh output directory for M1996 preserving M1990 fail artifacts

## Hypothesis

A repaired reset-only command can rerun the M1990 semantics in a fresh output directory using the artifact-driven quota validator.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_support_reset_validation_rerun_command_design
- parent_dataset: docs/m1994-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-quota-parameterization-implementation-audit.md, runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json
- parent_config: experiments/manifests/m1994-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-quota-parameterization-implementation-audit.json
- parent_objective: freeze repaired reset-validation rerun command after quota parameterization audit
- derived_from: m1994-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-quota-parameterization-implementation-audit
- blocked_by: M1986 reset-validation pass under repaired validator has not been rerun
- supersedes: rerunning M1990 in-place or without command design
- invalidates: None

## Success Criteria

- docs/m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design.md exists
- exact repaired reset-only command is specified
- fresh output directory is specified
- target reset/spec count is 80
- expected observation dimension is 72
- no reset rollout measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- command is ambiguous
- output directory overwrites M1990
- reset rollout measured execution or ranking is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1995 must freeze exact repaired reset-only rerun command
- M1995 must use a fresh output directory that preserves M1990 fail artifacts
- M1995 must target 80 specs and observation dimension 72
- M1995 must not run reset

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

- milestone: m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design
- type: gate
- checkpoint: docs/m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_outcome_support_repaired_reset_rerun_command_design_admit_execution
- reason: M1995 freezes exact repaired reset-only rerun command in fresh output directory for M1996 preserving M1990 fail artifacts

## Next Blocker

m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design
