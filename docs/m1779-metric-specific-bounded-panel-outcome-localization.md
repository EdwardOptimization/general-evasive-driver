# M1779 Metric-Specific Bounded Panel Outcome Localization

- status: completed
- result class: `metric_specific_bounded_panel_outcome_localization_pass`
- summary: `runs/m1779_metric_specific_bounded_panel_outcome_localization/summary.json`
- source rows: `runs/m1777_metric_specific_bounded_panel_measured_execution/episode_rows.csv`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1779 localizes M1777 bounded-panel outcome dominance without rerunning reset or
rollout. The result confirms that ranking remains blocked: dominant
non-success slices are diffuse across role panels, profiles, and metric
families.

Observed localization state:

```text
result_class: metric_specific_bounded_panel_outcome_localization_pass
episode_count: 288 / 288
dominant_slice_count: 96
target_dominant_slice_count: 96
dominant_role_panel_count: 4
dominant_profile_count: 11
dominant_primary_metric_count: 4
outcome_dominance_class: diffuse_role_profile_outcome_dominance
ranking_blocked: true
guardrail_violation_count: 0
```

## Dominant Slice Types

Dominant slices by type:

```text
hidden_dynamics_bucket: 8
obstacle_lateral_bucket: 4
obstacle_timing_bucket: 4
primary_metric_family: 4
profile: 11
road_boundary_bucket: 4
role_panel: 4
role_panel_hidden_bucket: 12
role_panel_lateral_bucket: 12
role_panel_primary_metric: 4
role_panel_road_bucket: 8
role_panel_sampled_label: 6
role_panel_timing_bucket: 11
sampled_obstacle_label: 4
```

Top dominant slice:

```text
slice_type: role_panel_hidden_bucket
slice_id: unavoidable_mitigation::actuator_delay
episode_count: 36
success_obstacle_pass_rate: 0.0
collision_failure_rate: 1.0
off_track_noncollision_noncompletion_rate: 0.0
dominant_outcome: collision_failure
dominant_outcome_rate: 1.0
clearance_margin_mean: -0.15314358426032973
clearance_margin_p10: -0.2946291078939709
```

Other high-confidence blockers include:

- `stable_avoidance_aes::close` dominated by off-track noncompletion;
- `stable_avoidance_aes::aes_feasible` dominated by off-track noncompletion;
- `unavoidable_mitigation::very_close` dominated by collision;
- `hidden_dynamics_robustness::unavoidable` dominated by collision.

## Interpretation

M1779 does not rank profiles. It shows that the bounded panel is still an
execution and localization artifact, not a comparison-ready benchmark.

The dominant outcomes are not a single stale row or one role-only defect. They
span:

- all `4` role panels;
- `11` of `12` profiles;
- all `4` primary metric families;
- hidden-dynamics, road, timing, lateral, and sampled-label slices.

This makes direct global success-rate ranking invalid. A branch synthesis is
needed before deciding whether to repair panel semantics, adjust role-specific
metrics, split the panel by claim type, or stop this comparison route.

## Artifacts

```text
runs/m1779_metric_specific_bounded_panel_outcome_localization/summary.json
runs/m1779_metric_specific_bounded_panel_outcome_localization/dominant_slices.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/target_dominant_slices.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_profile_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_primary_metric_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_hidden_bucket_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_road_bucket_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_timing_bucket_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_lateral_bucket_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/role_panel_sampled_label_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/profile_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/profile_role_panel_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/profile_primary_metric_aggregate.csv
runs/m1779_metric_specific_bounded_panel_outcome_localization/primary_metric_family_aggregate.csv
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

- M1777 outcome dominance is diffuse across role/profile/metric dimensions;
- controller-family ranking remains blocked;
- branch synthesis is required before more narrow repair or ranking work.

Unsupported:

- profile ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1780 metric-specific bounded-panel branch synthesis.
