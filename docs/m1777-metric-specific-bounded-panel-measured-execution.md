# M1777 Metric-Specific Bounded Panel Measured Execution

- status: completed
- result class: `metric_specific_bounded_panel_measured_execution_pass`
- summary: `runs/m1777_metric_specific_bounded_panel_measured_execution/summary.json`
- output dir: `runs/m1777_metric_specific_bounded_panel_measured_execution`
- training/replay/PPO: false

## Summary

M1777 executes the fixed M1771 metric-specific bounded panel with the M1776
adapter. The execution completes all pre-registered cells and writes the
required diagnostic artifacts.

Execution pass facts:

```text
episode_count: 288 / 288
failure_count: 0
profile_count: 12 / 12
bounded_panel_spec_count: 24 / 24
role_panel_count: 4 / 4
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
success_obstacle_pass: 24
collision_failure: 122
off_track_noncollision_noncompletion: 142
```

Role panel outcome rates:

```text
stable_avoidance_aes:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.013889
  off_track_noncollision_noncompletion_rate: 0.916667

drift_required_recovery:
  success_obstacle_pass_rate: 0.152778
  collision_failure_rate: 0.305556
  off_track_noncollision_noncompletion_rate: 0.541667

hidden_dynamics_robustness:
  success_obstacle_pass_rate: 0.069444
  collision_failure_rate: 0.430556
  off_track_noncollision_noncompletion_rate: 0.500000

unavoidable_mitigation:
  success_obstacle_pass_rate: 0.041667
  collision_failure_rate: 0.944444
  off_track_noncollision_noncompletion_rate: 0.013889
```

The outcome distribution is intentionally not interpreted as a ranking here.
M1778 must audit whether these outcomes are role-appropriate, dominated by
off-track behavior, or require further metric-specific localization before any
comparison claim.

## Artifacts

```text
runs/m1777_metric_specific_bounded_panel_measured_execution/summary.json
runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/failure_rows.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/run_state.json
runs/m1777_metric_specific_bounded_panel_measured_execution/profile_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/role_panel_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/scenario_family_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/scenario_role_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/evaluation_role_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/primary_metric_family_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/road_boundary_bucket_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/obstacle_timing_bucket_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/sampled_obstacle_label_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/outcome_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/termination_reason_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/profile_outcome_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/role_panel_outcome_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/primary_metric_family_outcome_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/role_panel_sampled_label_aggregate.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/profile_hidden_dynamics_worst_bucket.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/metric_completeness_summary.csv
runs/m1777_metric_specific_bounded_panel_measured_execution/metric_completeness_failures.csv
```

`failure_rows.csv` and `metric_completeness_failures.csv` contain only headers.

## Guardrails

- environment rollout started: `true`
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

- the fixed `288`-cell bounded panel executed completely;
- required aggregate and metric-completeness artifacts were written;
- no failures or guardrail violations occurred.

Unsupported:

- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification;
- any conclusion that one profile family is better than another.

## Decision

Route to M1778 measured-execution result audit before any ranking, paper claim,
or further scenario repair.
