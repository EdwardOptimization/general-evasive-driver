# m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair Research Review

## Summary

- Generated at UTC: 20260531T064006Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: geometry_delta_mapping_repair_pass_admit_measured_rerun
- Decision reason: M1914 skips obstacle delta env mutations for road_geometry_fixed rows and focused tests pass 9 passed while real execution remains deferred

## Hypothesis

Skipping obstacle-delta env mutations when road_geometry_fixed=true will remove the M1912 sampling failure mechanism without changing actor inputs or controller profiles.

## Lineage

- parent_checkpoint: not_applicable_task_quality_repair_axis_geometry_delta_mapping_repair
- parent_dataset: docs/m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit.md, runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution/failure_rows.csv
- parent_config: experiments/manifests/m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit.json
- parent_objective: repair road_geometry_fixed obstacle-delta mapping before rerunning measured execution
- derived_from: m1913-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-failure-audit
- blocked_by: M1912 contained-collision feasibility rows failed sampling after M1911 mapped obstacle deltas into env_config
- supersedes: rerunning M1912 without geometry-delta mapping repair
- invalidates: None

## Success Criteria

- src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py skips obstacle delta env mutations for road_geometry_fixed rows
- tests/test_executable_v2_support_first_task_quality_repair_axis_execution.py covers road_geometry_fixed and non-fixed delta mapping
- focused tests pass
- docs/m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair.md exists
- real M1902 execution remains deferred

## Failure Criteria

- mapping repair is missing
- focused tests fail
- repair changes actor inputs or controller profiles
- M1914 reruns measured execution
- next route is ambiguous

## Evidence Gates

- M1914 must repair road_geometry_fixed obstacle-delta mapping without rerunning execution
- M1914 must keep dry-run and measured CLI tests passing
- M1914 must not change actor inputs or controller profiles
- M1914 must not run environment reset rollout measured execution training replay PPO private holdout ranking paper claims or level3 self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not run measured execution
- do not run the real M1902 workload
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

- scenario_sampling_failure

## Scoreboard

- milestone: m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair
- type: infrastructure
- checkpoint: docs/m1914-executable-v2-support-first-task-quality-repair-axis-geometry-delta-mapping-repair.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: geometry_delta_mapping_repair_pass_admit_measured_rerun
- reason: M1914 skips obstacle delta env mutations for road_geometry_fixed rows and focused tests pass 9 passed while real execution remains deferred

## Next Blocker

m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun
