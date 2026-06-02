# M2447 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Outcome Localization

- status: completed
- result_class: `current_sim_dual_axis_metric_selected_measured_validation_outcome_localization_pass`
- manifest: `experiments/manifests/m2447-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization.py`
- summary: `runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/summary.json`
- localization rows: `runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/localization_rows.csv`
- decision rows: `runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/decision_rows.csv`
- measured rollout/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result

M2447 localized M2445 measured outcomes from artifacts only.

```text
episode_count: 5250
target_episode_count: 5250
localization_row_count: 65
guardrail_violation_count: 0
failure_types_observed: []
```

Global localization:

```text
actual_success_count: 351
actual_success_rate: 0.06685714285714285
hard_offtrack_count: 3921
hard_offtrack_rate: 0.7468571428571429
soft_offtrack_violation_count: 17
soft_offtrack_violation_rate: 0.0032380952380952383
boundary_tolerated_success_count: 0
boundary_tolerated_success_rate: 0.0
collision_count: 925
collision_rate: 0.1761904761904762
max_step_noncompletion_count: 33
max_step_noncompletion_rate: 0.006285714285714286
other_count: 23
other_rate: 0.004380952380952381
diagnostic_pattern: hard_offtrack_dominated
```

Top hard-offtrack diagnostic slices by count:

```text
termination_reason=off_track:
  episode_count 3921, hard_offtrack_count 3921, hard_offtrack_rate 1.0

outcome_bucket=off_track_noncollision_noncompletion:
  episode_count 3913, hard_offtrack_count 3913, hard_offtrack_rate 1.0

obstacle_lateral_offset_bucket=centerline:
  episode_count 2700, hard_offtrack_count 2050, hard_offtrack_rate 0.7592592592592593

sampled_obstacle_label=drift_required:
  episode_count 2025, hard_offtrack_count 1611, hard_offtrack_rate 0.7955555555555556

obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, hard_offtrack_count 1566, hard_offtrack_rate 0.87
```

All rows are diagnostic-only:

```text
ranking_admissible: false
winner_selected: false
```

## Interpretation Boundary

Allowed claim:

```text
M2447 identifies where M2445 hard-offtrack-dominated outcomes concentrate
across diagnostic axes.
```

Blocked claims:

```text
candidate-family ranking
controller-family ranking
selected-checkpoint ranking
winner selection
actual success improvement
repair execution
training repair success
paper-level result
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign execution
current-sim verdict
```

## Next Step

Next milestone:

```text
m2448-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization-result-audit
```

M2448 should audit whether the localization is actionable enough to route to
target consolidation, scenario-quality synthesis, or stop. It must not rerun,
repair, train, rank, select winners, or make verdict claims.
