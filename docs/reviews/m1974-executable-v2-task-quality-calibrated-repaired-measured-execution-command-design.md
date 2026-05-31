# m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design Research Review

## Summary

- Generated at UTC: 20260531T113609Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_repaired_measured_execution_command_design_admit_execution
- Decision reason: M1974 freezes exact repaired measured execution command target 960 episodes 80 specs 12 profiles CPU output dir and pass gates

## Hypothesis

The repaired reset-valid calibrated panel can be given an exact measured execution command over M1969 repaired specs and workload without changing claim boundaries.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_measured_execution_command_design
- parent_dataset: docs/m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit.md, runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json, runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/planned_workload.csv
- parent_config: experiments/manifests/m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit.json
- parent_objective: freeze measured execution command over repaired reset-valid calibrated panel
- derived_from: m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit
- blocked_by: repaired measured execution command has not been frozen after reset validation
- supersedes: rerunning stale M1966 measured command over unrepaired M1958 workload
- invalidates: None

## Success Criteria

- docs/m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design.md exists
- exact measured execution command is specified
- target episode count is 960
- target spec count is 80
- target profile count is 12
- no measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- command is ambiguous
- stale M1958 artifacts are used
- target counts are ambiguous
- measured execution ranking or paper-level claims are made

## Evidence Gates

- M1974 must freeze exact measured execution command over M1969 repaired specs and workload
- M1974 must target 960 episodes 80 specs and 12 profiles
- M1974 must keep ranking paper and level3 claims blocked
- M1974 must not run measured execution

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

- milestone: m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design
- type: gate
- checkpoint: docs/m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0000000000
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_repaired_measured_execution_command_design_admit_execution
- reason: M1974 freezes exact repaired measured execution command target 960 episodes 80 specs 12 profiles CPU output dir and pass gates

## Next Blocker

m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design
