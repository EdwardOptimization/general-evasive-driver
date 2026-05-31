# m1962-executable-v2-task-quality-calibrated-measured-execution-design Research Review

## Summary

- Generated at UTC: 20260531T104336Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_measured_execution_design_requires_focused_runner
- Decision reason: M1962 requires a focused calibrated measured runner before execution because legacy runner outputs do not preserve repair-source metadata as first-class evidence

## Hypothesis

A measured execution protocol can be designed for the reset-valid M1958 calibrated panel while preserving calibrated source metadata and keeping ranking claims blocked.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_measured_execution_design
- parent_dataset: docs/m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit.md, runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit.json
- parent_objective: design measured execution route for reset-valid calibrated task-quality panel
- derived_from: m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit
- blocked_by: M1961 admits measured execution design but no exact runner protocol is frozen
- supersedes: direct measured execution without metadata-preserving protocol design
- invalidates: None

## Success Criteria

- docs/m1962-executable-v2-task-quality-calibrated-measured-execution-design.md exists
- measured execution inputs outputs and pass gates are explicit
- target workload count is 960
- metadata preservation requirements are explicit
- next implementation or command route is explicit
- no reset rollout measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- measured execution route is ambiguous
- target counts are ambiguous
- metadata preservation is not specified
- reset rollout measured execution ranking or paper-level claims are made

## Evidence Gates

- M1962 must design the exact measured execution route for the M1958 planned workload
- M1962 must preserve calibrated source metadata and controller profile provenance
- M1962 must specify target counts output artifacts and pass/fail gates
- M1962 must keep controller ranking paper and level3 claims blocked

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

- milestone: m1962-executable-v2-task-quality-calibrated-measured-execution-design
- type: gate
- checkpoint: docs/m1962-executable-v2-task-quality-calibrated-measured-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 1.0000000000
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_measured_execution_design_requires_focused_runner
- reason: M1962 requires a focused calibrated measured runner before execution because legacy runner outputs do not preserve repair-source metadata as first-class evidence

## Next Blocker

m1962-executable-v2-task-quality-calibrated-measured-execution-design
