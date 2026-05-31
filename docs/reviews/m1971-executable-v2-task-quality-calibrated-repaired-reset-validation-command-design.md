# m1971-executable-v2-task-quality-calibrated-repaired-reset-validation-command-design Research Review

## Summary

- Generated at UTC: 20260531T112632Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_repaired_reset_command_design_admit_execution
- Decision reason: M1971 freezes exact reset-only command over repaired executable specs with target 80 obs dim 72 and no rollout

## Hypothesis

The repaired M1969 executable specs can be reset-validated with the focused calibrated reset validator using a frozen reset-only command.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_reset_validation_command_design
- parent_dataset: docs/m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit.md, runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json
- parent_config: experiments/manifests/m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit.json
- parent_objective: freeze reset-only command over repaired executable specs
- derived_from: m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit
- blocked_by: repaired executable specs have not been reset-validated
- supersedes: reusing old M1960 reset-validation artifacts after repaired materialization
- invalidates: None

## Success Criteria

- docs/m1971-executable-v2-task-quality-calibrated-repaired-reset-validation-command-design.md exists
- exact reset-only command is specified
- target reset/spec count is 80
- expected observation dimension is 72
- no reset rollout measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- command is ambiguous
- stale M1958 executable specs are used
- reset rollout measured execution or ranking is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1971 must freeze exact reset-only command over M1969 repaired executable specs
- M1971 must target 80 specs and observation dimension 72
- M1971 must keep rollout measured execution ranking paper and level3 claims blocked
- M1971 must not run reset

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

- milestone: m1971-executable-v2-task-quality-calibrated-repaired-reset-validation-command-design
- type: gate
- checkpoint: docs/m1971-executable-v2-task-quality-calibrated-repaired-reset-validation-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_repaired_reset_command_design_admit_execution
- reason: M1971 freezes exact reset-only command over repaired executable specs with target 80 obs dim 72 and no rollout

## Next Blocker

m1971-executable-v2-task-quality-calibrated-repaired-reset-validation-command-design
