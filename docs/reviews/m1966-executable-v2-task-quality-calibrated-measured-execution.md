# m1966-executable-v2-task-quality-calibrated-measured-execution Research Review

## Summary

- Generated at UTC: 20260531T110621Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_measured_execution_validation_fail_route_to_audit
- Decision reason: M1966 runner failed closed before rollout with episode_count 0 due missing parent_feasibility_tier_id in 8 offtrack-boundary-relief task sources

## Hypothesis

The calibrated measured runner can execute the M1958 960-cell public diagnostic workload with complete metadata-preserving episode rows and no guardrail violations.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_measured_execution
- parent_dataset: docs/m1965-executable-v2-task-quality-calibrated-materialization-branch-synthesis.md, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1965-executable-v2-task-quality-calibrated-materialization-branch-synthesis.json
- parent_objective: run real calibrated measured execution over the M1958 960-cell workload after branch synthesis
- derived_from: m1965-executable-v2-task-quality-calibrated-materialization-branch-synthesis
- blocked_by: real measured execution has not been run over the calibrated 960-cell workload
- supersedes: claiming measured evidence from reset or no-rollout preflight
- invalidates: None

## Success Criteria

- runs/m1966_executable_v2_task_quality_calibrated_measured_execution/summary.json exists
- result_class is task_quality_calibrated_measured_execution_pass
- episode_count equals 960
- failure_count equals 0
- metric_completeness_failure_count equals 0
- guardrail_violation_count equals 0

## Failure Criteria

- summary is missing
- episode_count differs from 960
- any measured row fails
- metric completeness fails
- guardrail violation appears
- controller ranking or paper-level claims are made

## Evidence Gates

- M1966 must run only the calibrated measured execution command admitted by M1965
- M1966 must produce 960 episode rows or preserve failure rows
- M1966 must preserve calibrated repair metadata in episode and aggregate artifacts
- M1966 must keep controller ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m1966-executable-v2-task-quality-calibrated-measured-execution
- type: infrastructure
- checkpoint: runs/m1966_executable_v2_task_quality_calibrated_measured_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_measured_execution_validation_fail_route_to_audit
- reason: M1966 runner failed closed before rollout with episode_count 0 due missing parent_feasibility_tier_id in 8 offtrack-boundary-relief task sources

## Next Blocker

m1966-executable-v2-task-quality-calibrated-measured-execution
