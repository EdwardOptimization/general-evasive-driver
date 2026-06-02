# M2433 Paper-Route Current-Sim Dual-Axis Offtrack Semantics Panel Implementation

- status: completed
- result_class: `current_sim_dual_axis_offtrack_semantics_panel_pass`
- manifest: `experiments/manifests/m2433-paper-route-current-sim-dual-axis-offtrack-semantics-panel-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_semantics_panel.py`
- focused tests: `2 passed`
- summary: `runs/m2433_paper_route_current_sim_dual_axis_offtrack_semantics_panel/summary.json`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2433 built an event-level offtrack semantics panel from existing primary
episode rows only:

```text
M2362 episode_rows.csv
M2397 episode_rows.csv
M2413 episode_rows.csv
```

The panel uses termination/event-level offtrack semantics:

```text
offtrack if termination_reason == off_track or outcome_bucket starts with off_track
```

This intentionally diagnoses the event stream and may differ slightly from
summary-level outcome-only offtrack counts.

Result summary:

```text
result_class: current_sim_dual_axis_offtrack_semantics_panel_pass
panel_row_count: 3
road_boundary_dominated_panel_count: 3
all_panels_road_boundary_dominated_offtrack: true
high_clearance_threshold_m: 1.0
low_overshoot_threshold_m: 0.2
road_boundary_dominance_threshold: 0.8
min_positive_clearance_low_overshoot_rate: 0.9841229193341869
max_positive_clearance_low_overshoot_rate: 0.9882130888640653
min_offtrack_high_clearance_rate: 0.895112016293279
max_mean_offtrack_max_overshoot: 0.07326005531775727
route_recommendation: route_to_offtrack_boundary_task_semantics_reassessment_audit
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Panel rows:

```text
m2362_repaired_pack_primary:
  episode_count: 5400
  success_rate: 0.06518518518518518
  collision_rate: 0.19962962962962963
  offtrack_rate: 0.7274074074074074
  offtrack_positive_clearance_rate_of_offtrack: 0.9984725050916496
  offtrack_high_clearance_rate_of_offtrack: 0.895112016293279
  offtrack_low_overshoot_rate_of_offtrack: 0.9880346232179226
  offtrack_positive_clearance_low_overshoot_rate_of_offtrack: 0.9865071283095723
  mean_offtrack_clearance_margin: 8.803955788608055
  mean_offtrack_max_overshoot: 0.07253051965912803
  mean_time_to_first_off_track_s: 2.0398727087576374

m2397_effective_candidate_primary:
  episode_count: 30735
  success_rate: 0.04054010086220921
  collision_rate: 0.10157800553115341
  offtrack_rate: 0.8446721978200749
  offtrack_positive_clearance_rate_of_offtrack: 0.9975347636839875
  offtrack_high_clearance_rate_of_offtrack: 0.897692692885482
  offtrack_low_overshoot_rate_of_offtrack: 0.9906783251800778
  offtrack_positive_clearance_low_overshoot_rate_of_offtrack: 0.9882130888640653
  mean_offtrack_clearance_margin: 9.682986178953287
  mean_offtrack_max_overshoot: 0.07096953331844186
  mean_time_to_first_off_track_s: 2.1225060667924964

m2413_source_linked_primary:
  episode_count: 5250
  success_rate: 0.06685714285714285
  collision_rate: 0.1761904761904762
  offtrack_rate: 0.7438095238095238
  offtrack_positive_clearance_rate_of_offtrack: 0.9982074263764404
  offtrack_high_clearance_rate_of_offtrack: 0.8960307298335467
  offtrack_low_overshoot_rate_of_offtrack: 0.9859154929577465
  offtrack_positive_clearance_low_overshoot_rate_of_offtrack: 0.9841229193341869
  mean_offtrack_clearance_margin: 8.802030895592363
  mean_offtrack_max_overshoot: 0.07326005531775727
  mean_time_to_first_off_track_s: 2.006145966709347
```

## Interpretation

M2433 strengthens the task-quality diagnosis:

```text
Most offtrack terminations are not obstacle-contact or zero-clearance failures.
Across all three primary measured panels, more than 98.4% of offtrack events
combine positive obstacle clearance with <= 0.20 m road-boundary overshoot.
```

This supports a road-boundary/task-semantics reassessment route before more
source-linked local repair, training, PPO, or controller-family comparison.

It does not prove that the driver is good. It says the current dominant failure
metric is likely too entangled with road-boundary termination semantics to be
used as the next repair target without a dedicated audit.

## Decision Rows

Supported:

```text
new_measured_rollout_started: false
candidate_or_controller_ranking: false
road_boundary_dominated_offtrack: true
scenario_redesign_executed: false
next_route: route_to_offtrack_boundary_task_semantics_reassessment_audit
```

Blocked:

```text
current_sim_verdict
scenario redesign executed
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
training repair success
```

## Claim Boundary

Supported:

```text
M2433 generated a non-ranking event-level offtrack semantics panel.

All three primary measured panels are road-boundary dominated by the registered
positive-clearance low-overshoot criterion.

The next route should audit offtrack boundary/task semantics before more local
repair or training.
```

Blocked:

```text
driver improvement
new measured rollout result
repair execution
training repair success
candidate/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Next Step

Next milestone:

```text
m2434-paper-route-current-sim-dual-axis-offtrack-semantics-panel-result-audit
```

M2434 should audit the M2433 semantics panel and decide whether to route to:

```text
1. offtrack-boundary task-semantics reassessment;
2. metric/termination threshold design;
3. high-fidelity/backend validation preparation;
4. branch synthesis or stop for user review.
```

M2434 must not treat M2433 as a current-sim verdict or scenario redesign result.
