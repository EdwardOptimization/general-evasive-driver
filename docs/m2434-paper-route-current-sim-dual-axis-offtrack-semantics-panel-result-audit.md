# M2434 Paper-Route Current-Sim Dual-Axis Offtrack Semantics Panel Result Audit

- status: completed
- decision: `offtrack_semantics_panel_accepted_route_to_boundary_threshold_sensitivity`
- manifest: `experiments/manifests/m2434-paper-route-current-sim-dual-axis-offtrack-semantics-panel-result-audit.json`
- parent implementation: `docs/m2433-paper-route-current-sim-dual-axis-offtrack-semantics-panel-implementation.md`
- parent summary: `runs/m2433_paper_route_current_sim_dual_axis_offtrack_semantics_panel/summary.json`
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2434 accepts M2433 as a complete event-level offtrack semantics panel. The
result is strong enough to stop source-linked local repair and direct training
as the immediate next moves. It is not strong enough to claim driver success,
scenario redesign success, or a current-sim verdict.

Accepted evidence:

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
guardrail_violation_count: 0
failure_types_observed: []
```

Per-panel semantics:

```text
M2362:
  offtrack_rate: 0.7274074074074074
  positive-clearance low-overshoot offtrack rate: 0.9865071283095723
  mean offtrack clearance: 8.803955788608055
  mean offtrack overshoot: 0.07253051965912803

M2397:
  offtrack_rate: 0.8446721978200749
  positive-clearance low-overshoot offtrack rate: 0.9882130888640653
  mean offtrack clearance: 9.682986178953287
  mean offtrack overshoot: 0.07096953331844186

M2413:
  offtrack_rate: 0.7438095238095238
  positive-clearance low-overshoot offtrack rate: 0.9841229193341869
  mean offtrack clearance: 8.802030895592363
  mean offtrack overshoot: 0.07326005531775727
```

## Diagnosis

The dominant measured failure is not primarily obstacle contact or
zero-clearance inability. It is a road-boundary termination mode with large
clearance and small boundary overshoot. This is a task-quality blocker for the
current-sim paper route.

The next question should be threshold sensitivity:

```text
If offtrack episodes with positive obstacle clearance and small road-boundary
overshoot are marked as boundary-tolerated diagnostic events, how much of the
observed failure rate is metric/termination semantics versus true obstacle
failure?
```

This must remain a counterfactual metric analysis. It cannot be reported as
actual closed-loop success because the environment terminated the episode.

## Failure Taxonomy

Observed:

```text
task_quality_blocker:
  road-boundary dominated offtrack is repeated across three primary panels.

metric_semantics_sensitivity:
  the current offtrack metric is highly sensitive to small boundary overshoot.
```

Not observed:

```text
lineage_invalid
contract_violation
metric_artifact in M2433
scenario_sampling_failure in M2433
active config overwrite
repair execution
training repair success
candidate/controller ranking
winner selection
hidden/oracle actor-input injection
```

## Route Decision

Decision:

```text
offtrack_semantics_panel_accepted_route_to_boundary_threshold_sensitivity
```

Next milestone:

```text
m2435-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-implementation
```

M2435 should materialize a threshold-sensitivity panel over existing primary
episode rows:

```text
M2362 episode_rows.csv
M2397 episode_rows.csv
M2413 episode_rows.csv
```

The panel should evaluate tolerance thresholds without changing any rollout:

```text
0.02 m
0.05 m
0.10 m
0.20 m
```

For each source and threshold, it should report:

```text
original_success_rate
collision_rate
offtrack_rate
boundary_tolerated_count/rate
counterfactual_soft_success_rate
remaining_failure_rate
```

Allowed M2435 claims:

```text
counterfactual metric/termination sensitivity reanalysis
task-quality evidence about road-boundary threshold sensitivity
route recommendation for result audit
```

Blocked M2435 claims:

```text
new measured rollout
actual success improvement
repair execution
training/PPO
candidate/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```

## Claim Boundary

Supported:

```text
M2433 is accepted as a complete offtrack semantics panel.

Road-boundary dominated offtrack is strong enough to require task-boundary
metric sensitivity analysis before more repair or training.
```

Blocked:

```text
driver improvement
actual scenario repair
training repair success
current-sim verdict
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
```
