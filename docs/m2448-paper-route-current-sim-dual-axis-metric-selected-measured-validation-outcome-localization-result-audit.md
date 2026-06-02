# M2448 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Outcome Localization Result Audit

- status: completed
- decision: `accept_localization_route_to_metric_selected_target_consolidation`
- manifest: `experiments/manifests/m2448-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization-result-audit.json`
- audited summary: `runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/summary.json`
- audited localization rows: `runs/m2447_paper_route_current_sim_dual_axis_metric_selected_measured_validation_outcome_localization/localization_rows.csv`
- rerun/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2448 accepts M2447 localization as complete and actionable enough for
artifact-only target consolidation.

Audited evidence:

```text
result_class: current_sim_dual_axis_metric_selected_measured_validation_outcome_localization_pass
episode_count: 5250
localization_row_count: 65
guardrail_violation_count: 0
failure_types_observed: []
global_actual_success_rate: 0.06685714285714285
global_hard_offtrack_rate: 0.7468571428571429
global_collision_rate: 0.1761904761904762
global_soft_offtrack_violation_rate: 0.0032380952380952383
global_diagnostic_pattern: hard_offtrack_dominated
```

Diagnostic slices with high hard-offtrack support:

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

## Decision

Accepted claim:

```text
M2447 localizes the fresh M2445 task-quality blocker into actionable
diagnostic slices, dominated by hard offtrack under true soft-boundary
execution.
```

Rejected claims:

```text
profile/pack/family/checkpoint ranking
winner selection
repair readiness
training route readiness
scenario redesign success
current-sim verdict
paper/FW-vs-GRU/level3 self-ID/training-repair verdict
```

Why target consolidation, not direct repair:

```text
The blocker is broad and task-quality related. M2447 identifies repeated
diagnostic axes but does not yet define compact target rows, guardrail rows, or
repair/scenario-quality semantics. A consolidation step should separate hard
offtrack targets, collision guardrails, soft-boundary diagnostics, and
monitoring-only axes before any repair, training, or scenario redesign route.
```

## Next Route

Next milestone:

```text
m2449-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation
```

M2449 should consolidate M2447 localization into artifact-only target and
guardrail rows. It must keep diagnostic axes non-ranking and must not rerun,
repair, train, select winners, or make verdict claims.
