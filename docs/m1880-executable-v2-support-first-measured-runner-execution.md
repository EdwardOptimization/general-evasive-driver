# M1880 Executable V2 Support-First Measured Runner Execution

- status: completed
- result class: `executable_v2_support_first_measured_runner_execution_pass`
- summary: `runs/m1880_executable_v2_support_first_measured_runner_execution/summary.json`
- output dir: `runs/m1880_executable_v2_support_first_measured_runner_execution`
- training/replay/PPO: false

## Summary

M1880 executes the fixed M1875 support-first measured workload with the M1878
runner. The execution completes all pre-registered cells and writes the
required diagnostic artifacts.

Execution pass facts:

```text
episode_count: 2160 / 2160
failure_count: 0
controller_profile_count: 12 / 12
support_first_spec_count: 180 / 180
role_panel_count: 4 / 4
role_surface_count: 8 / 8
profile_alias_mismatch_count: 0
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

This is a measured public diagnostic execution pass. It is not a
controller-family ranking, profile promotion, paper-level result, or level3
self-identification result.

## Outcome Snapshot

Overall outcome buckets:

```text
success_obstacle_pass: 0
collision_failure: 480
off_track_noncollision_noncompletion: 1680
```

Role panel outcome rates:

```text
drift_required_recovery:
  success_obstacle_pass_rate: 0.000000
  collision_failure_rate: 0.232639
  off_track_noncollision_noncompletion_rate: 0.767361

stable_aeb:
  success_obstacle_pass_rate: 0.000000
  collision_failure_rate: 0.112847
  off_track_noncollision_noncompletion_rate: 0.887153

stable_aes_only:
  success_obstacle_pass_rate: 0.000000
  collision_failure_rate: 0.001736
  off_track_noncollision_noncompletion_rate: 0.998264

unavoidable_mitigation:
  success_obstacle_pass_rate: 0.000000
  collision_failure_rate: 0.648148
  off_track_noncollision_noncompletion_rate: 0.351852
```

This outcome distribution is intentionally not interpreted as profile ranking.
M1881 must audit whether the result is a scenario/task-quality issue, a
controller-family weakness, an overly strict success metric, or an expected
diagnostic stress result before any comparison claim.

## Artifacts

```text
runs/m1880_executable_v2_support_first_measured_runner_execution/summary.json
runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/failure_rows.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/run_state.json
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_panel_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_surface_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/surface_variant_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/scenario_profile_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/road_boundary_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/obstacle_timing_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/sampled_obstacle_label_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/termination_reason_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_role_panel_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/controller_profile_role_surface_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_panel_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/role_surface_outcome_aggregate.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/profile_hidden_dynamics_worst_bucket.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/metric_completeness_summary.csv
runs/m1880_executable_v2_support_first_measured_runner_execution/metric_completeness_failures.csv
```

`failure_rows.csv` and `metric_completeness_failures.csv` contain only headers.

## Guardrails

- environment rollout started: `true`
- measured rollout started: `true`
- policy action executed: `true`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- the fixed `2160`-cell support-first public diagnostic workload executed
  completely;
- required support-first aggregate and metric-completeness artifacts were
  written;
- no failures or guardrail violations occurred.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any conclusion that one profile family is better than another.

## Decision

Route to M1881 measured-execution result audit before any ranking, paper claim,
or scenario repair decision.
