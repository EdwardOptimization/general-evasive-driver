# M1882 Executable V2 Support-First Outcome Localization

- status: completed
- result class: `support_first_outcome_localization_pass`
- summary: `runs/m1882_executable_v2_support_first_outcome_localization/summary.json`
- parent execution: `runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv`
- reset/rollout in M1882: false
- training/replay/PPO: false

## Summary

M1882 localizes the M1880 zero-success outcome dominance without rerunning the
environment. It consumes only the completed M1880 measured artifacts.

Localization facts:

```text
episode_count: 2160 / 2160
outcome_counts:
  collision_failure: 480
  off_track_noncollision_noncompletion: 1680
dominant_slice_count: 526
target_dominant_slice_count: 526
dominant_role_panel_count: 4
dominant_role_surface_count: 8
dominant_profile_count: 12
outcome_dominance_class: diffuse_support_first_outcome_dominance
recommended_next_route: success_metric_semantics_and_task_quality_repair_design
guardrail_violation_count: 0
```

The required localization slice types are all represented:

```text
hidden_dynamics_bucket
obstacle_lateral_bucket
obstacle_timing_bucket
profile
profile_role_panel
profile_role_surface
road_boundary_bucket
role_panel
role_panel_profile
role_surface
role_surface_hidden_bucket
role_surface_lateral_bucket
role_surface_profile
role_surface_road_bucket
role_surface_sampled_label
role_surface_timing_bucket
sampled_obstacle_label
scenario_profile
```

## Interpretation

This is diffuse outcome dominance, not a profile-specific ranking signal.
Every role panel, every role-surface, and every controller profile appears in
dominant non-success slices. A direct controller-family comparison is therefore
not valid.

The dominant outcomes are split by task structure:

- many stable and post-friction slices terminate off-track while maintaining
  positive clearance margins;
- unavoidable steady-surface slices are collision-heavy as expected for the
  mitigation role;
- all slices have zero `success_obstacle_pass` under the current success
  semantics.

The next route should first audit and repair success semantics and task-quality
geometry before training or ranking. In particular, the project needs to know
whether off-track terminations are caused by road width, obstacle pass
definition, finish timing, or genuinely poor control.

## Artifacts

```text
runs/m1882_executable_v2_support_first_outcome_localization/summary.json
runs/m1882_executable_v2_support_first_outcome_localization/dominant_slices.csv
runs/m1882_executable_v2_support_first_outcome_localization/target_dominant_slices.csv
runs/m1882_executable_v2_support_first_outcome_localization/role_panel_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/role_surface_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/role_panel_profile_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/role_surface_profile_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/profile_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/profile_role_panel_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/profile_role_surface_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/hidden_dynamics_bucket_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/road_boundary_bucket_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/obstacle_timing_bucket_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/obstacle_lateral_bucket_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/sampled_obstacle_label_aggregate.csv
runs/m1882_executable_v2_support_first_outcome_localization/scenario_profile_aggregate.csv
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
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

- M1880 outcome dominance is diffuse across roles, role-surfaces, and profiles;
- ranking remains blocked;
- success semantics and task-quality repair design is the next valid route.

Unsupported:

- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1883 success-metric semantics and task-quality repair design. Do not
train, tune controller profiles, or rank controller families from M1880/M1882.
