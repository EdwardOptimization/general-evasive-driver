# M2438 Paper-Route Current-Sim Dual-Axis Hard/Soft Offtrack Metric Split Implementation

- status: completed
- result_class: `current_sim_dual_axis_hard_soft_offtrack_metric_split_pass`
- manifest: `experiments/manifests/m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split.py`
- focused tests: `2 passed`
- summary: `runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2438 implemented the M2437 hard/soft offtrack metric split as a
classification/relabel panel over existing primary episode rows only:

```text
M2362 episode rows: 5400
M2397 episode rows: 30735
M2413 episode rows: 5250
```

The panel computes the fixed threshold grid from M2435:

```text
0.02 m
0.05 m
0.10 m
0.20 m
```

Classification priority:

```text
1. Preserve measured actual_success unchanged.
2. Classify collision or obstacle-risk failure.
3. Classify hard offtrack failure above the active threshold.
4. Classify soft offtrack violation at or below the active threshold.
5. Mark boundary-tolerated diagnostic and counterfactual soft success only for
   analysis.
```

Result summary:

```text
result_class: current_sim_dual_axis_hard_soft_offtrack_metric_split_pass
panel_row_count: 12
source_count: 3
thresholds_m: [0.02, 0.05, 0.10, 0.20]
actual_success_preserved: true
actual_success_preservation_violation_count: 0
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
max_actual_success_rate: 0.06685714285714285
max_hard_offtrack_failure_rate_at_0_20m: 0.010476190476190476
min_soft_offtrack_violation_rate_at_0_20m: 0.7175925925925926
guardrail_violation_count: 0
failure_types_observed: []
```

## Generated Artifacts

```text
runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json
runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/panel_rows.csv
runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/decision_rows.csv
```

Panel rows contain per-source, per-threshold counts for:

```text
actual_success_preserved
collision_or_obstacle_risk_failure
hard_offtrack_failure
soft_offtrack_violation
boundary_tolerated_diagnostic
counterfactual_soft_success
other_failure
```

Decision rows preserve:

```text
new_measured_rollout_started: false
actual_success_preserved: true
counterfactual_soft_success_is_actual_success: false
scenario_redesign_executed: false
current_sim_verdict: blocked
next_route: route_to_hard_soft_offtrack_metric_split_result_audit
```

## Interpretation

M2438 confirms that the M2437 metric contract can be materialized over the
existing current-sim episode rows without changing measured actual success.

At the `0.20 m` threshold, the diagnostic soft-success rate remains high, but
this is still a counterfactual metric-analysis signal:

```text
min counterfactual soft-success rate at 0.20 m: 0.7827777777777778
max counterfactual soft-success rate at 0.20 m: 0.8752562225475842
max actual success rate: 0.06685714285714285
```

This supports task-boundary metric audit readiness. It does not prove driver
improvement, scenario redesign, current-sim completion, paper-level evidence, or
history/self-identification.

## Claim Boundary

Supported:

```text
M2438 implemented a hard/soft offtrack classification panel.

M2438 preserved measured actual_success exactly.

M2438 generated guardrailed diagnostic columns for hard offtrack, soft offtrack,
collision/obstacle-risk failure, and boundary-tolerated diagnostics.

M2438 admits a bounded result audit.
```

Blocked:

```text
driver improvement
actual success improvement
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
m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit
```

M2439 should audit whether M2438 is sufficient to route to:

```text
1. metric-split measured-validation design;
2. task-boundary contract revision;
3. metric-lineage repair;
4. branch synthesis; or
5. stop for user review.
```

M2439 must not rerun measured rollout, execute repair, train, rank candidates or
controllers, select a winner, or make current-sim/paper/self-ID verdict claims.
