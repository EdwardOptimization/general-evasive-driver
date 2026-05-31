# m1975-executable-v2-task-quality-calibrated-repaired-measured-execution Research Review

## Summary

- Generated at UTC: 20260531T114415Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_repaired_measured_execution_pass_route_to_result_synthesis
- Decision reason: M1975 repaired measured execution pass 960 episodes failure 0 metric completeness 0 guardrail 0 raw outcomes success 38 collision 150 offtrack 772 interpretation deferred to synthesis

## Hypothesis

The repaired calibrated measured runner can execute the M1969 960-cell public diagnostic workload with complete metadata-preserving episode rows and no guardrail violations.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_measured_execution
- parent_dataset: docs/m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design.md, runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json, runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/planned_workload.csv
- parent_config: experiments/manifests/m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design.json
- parent_objective: run repaired calibrated measured execution over the M1969 960-cell workload
- derived_from: m1974-executable-v2-task-quality-calibrated-repaired-measured-execution-command-design
- blocked_by: real repaired measured execution has not been run over the calibrated 960-cell workload
- supersedes: using stale M1966 measured execution result from unrepaired workload
- invalidates: None

## Success Criteria

- runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/summary.json exists
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

- M1975 must run only the frozen repaired measured execution command
- M1975 must produce 960 episode rows or preserve failure rows
- M1975 must preserve calibrated repair metadata in episode and aggregate artifacts
- M1975 must keep controller ranking paper and level3 claims blocked

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

- milestone: m1975-executable-v2-task-quality-calibrated-repaired-measured-execution
- type: infrastructure
- checkpoint: runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: 0.0395833333
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_repaired_measured_execution_pass_route_to_result_synthesis
- reason: M1975 repaired measured execution pass 960 episodes failure 0 metric completeness 0 guardrail 0 raw outcomes success 38 collision 150 offtrack 772 interpretation deferred to synthesis

## Next Blocker

m1975-executable-v2-task-quality-calibrated-repaired-measured-execution
