# m1964-executable-v2-task-quality-calibrated-measured-execution-command-design Research Review

## Summary

- Generated at UTC: 20260531T105454Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_measured_execution_command_design_admit_execution
- Decision reason: M1964 freezes exact M1965 calibrated measured execution command target 960 episodes 80 specs 12 profiles CPU output dir and pass gates

## Hypothesis

The M1963 calibrated measured runner can be given an exact command for the M1958 960-cell workload while preserving claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_measured_execution_command_design
- parent_dataset: docs/m1963-executable-v2-task-quality-calibrated-measured-runner-implementation.md, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1963-executable-v2-task-quality-calibrated-measured-runner-implementation.json
- parent_objective: freeze exact calibrated measured execution command over the M1958 planned workload
- derived_from: m1963-executable-v2-task-quality-calibrated-measured-runner-implementation
- blocked_by: M1963 implements the adapter but real measured execution command has not been frozen
- supersedes: ad hoc measured execution over M1958 workload
- invalidates: None

## Success Criteria

- docs/m1964-executable-v2-task-quality-calibrated-measured-execution-command-design.md exists
- exact measured execution command is specified
- target episode count is 960
- target spec count is 80
- target profile count is 12
- pass/fail gates are explicit
- no measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- command is ambiguous
- target counts are ambiguous
- pass gates omit metadata preservation
- measured execution ranking or paper-level claims are made

## Evidence Gates

- M1964 must freeze exact measured execution command target output dir and pass gates
- M1964 must specify target 960 episodes 80 specs and 12 profiles
- M1964 must keep ranking paper and level3 claims blocked
- M1964 must not run measured execution

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

- milestone: m1964-executable-v2-task-quality-calibrated-measured-execution-command-design
- type: gate
- checkpoint: docs/m1964-executable-v2-task-quality-calibrated-measured-execution-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0000000000
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_measured_execution_command_design_admit_execution
- reason: M1964 freezes exact M1965 calibrated measured execution command target 960 episodes 80 specs 12 profiles CPU output dir and pass gates

## Next Blocker

m1964-executable-v2-task-quality-calibrated-measured-execution-command-design
