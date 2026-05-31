# m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design Research Review

## Summary

- Generated at UTC: 20260531T074521Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_scenario_materialization_command_design_route_to_focused_materializer
- Decision reason: M1927 designs the exact no-rollout materialization route and requires a focused materializer because historical materializers are not exact schema matches

## Hypothesis

The M1926 source-only subset can be routed into an exact no-rollout materialization command with explicit target artifacts and counts.

## Lineage

- parent_checkpoint: not_applicable_task_quality_scenario_redesign_materialization_command_design
- parent_dataset: docs/m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation.md, configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json, runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation/summary.json
- parent_config: experiments/manifests/m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation.json
- parent_objective: design exact no-rollout command to convert the 80-source subset into executable task specs and workload rows
- derived_from: m1926-executable-v2-task-quality-scenario-redesign-materialization-implementation
- blocked_by: M1926 created a source-only subset but not executable task specs or workload rows
- supersedes: manual adaptation of historical controller-family materializers
- invalidates: None

## Success Criteria

- docs/m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design.md exists
- exact input subset artifact is named
- exact output directory and artifacts are named
- target executable spec and workload counts are explicit
- compatibility decision for existing materializers is explicit
- next manifest is explicit
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- materialization command route is ambiguous
- target counts are ambiguous
- holdout candidates would be used
- next route is ambiguous
- controller ranking or paper-level claims are made

## Evidence Gates

- M1927 must define exact no-rollout materialization command and target artifacts
- M1927 must define target counts for executable specs and workload rows
- M1927 must decide whether to adapt existing materializers or implement a focused new materializer
- M1927 must keep reset rollout measured execution controller ranking paper claims and level3 self-ID blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
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

- milestone: m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design
- type: gate
- checkpoint: docs/m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_scenario_materialization_command_design_route_to_focused_materializer
- reason: M1927 designs the exact no-rollout materialization route and requires a focused materializer because historical materializers are not exact schema matches

## Next Blocker

m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design
