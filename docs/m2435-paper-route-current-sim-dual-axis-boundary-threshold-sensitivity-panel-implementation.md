# M2435 Paper-Route Current-Sim Dual-Axis Boundary-Threshold Sensitivity Panel Implementation

- status: completed
- result_class: `current_sim_dual_axis_boundary_threshold_sensitivity_panel_pass`
- manifest: `experiments/manifests/m2435-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel.py`
- focused tests: `2 passed`
- summary: `runs/m2435_paper_route_current_sim_dual_axis_boundary_threshold_sensitivity_panel/summary.json`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2435 built a counterfactual boundary-threshold sensitivity panel from existing
primary episode rows only:

```text
M2362 episode_rows.csv
M2397 episode_rows.csv
M2413 episode_rows.csv
```

Evaluated thresholds:

```text
0.02 m
0.05 m
0.10 m
0.20 m
```

Counterfactual rule:

```text
boundary_tolerated iff
  episode terminated/off_bucketed as offtrack
  and no collision
  and not actual success
  and min_clearance_margin > 0
  and 0 <= max_off_track_overshoot <= threshold
```

The resulting `counterfactual_soft_success_rate` is diagnostic only. It is not
an executed rollout result and must not be reported as actual success.

Result summary:

```text
result_class: current_sim_dual_axis_boundary_threshold_sensitivity_panel_pass
panel_row_count: 12
source_count: 3
threshold_count: 4
thresholds_m: [0.02, 0.05, 0.10, 0.20]
all_required_thresholds_present: true
high_boundary_threshold_sensitivity_detected: true
high_sensitivity_gain_threshold: 0.5
max_actual_success_rate: 0.06685714285714285
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
actual_success_improvement_claim_made: false
guardrail_violation_count: 0
failure_types_observed: []
```

## Threshold Rows

At `0.02 m` tolerance:

```text
M2362 soft_success_rate: 0.18888888888888888
M2397 soft_success_rate: 0.18727834716121686
M2413 soft_success_rate: 0.19314285714285714
```

At `0.05 m` tolerance:

```text
M2362 soft_success_rate: 0.35703703703703704
M2397 soft_success_rate: 0.3927769643728648
M2413 soft_success_rate: 0.36952380952380953
```

At `0.10 m` tolerance:

```text
M2362 soft_success_rate: 0.5833333333333334
M2397 soft_success_rate: 0.6492598015292013
M2413 soft_success_rate: 0.5918095238095238
```

At `0.20 m` tolerance:

```text
M2362 soft_success_rate: 0.7827777777777778
M2397 soft_success_rate: 0.8752562225475842
M2413 soft_success_rate: 0.7988571428571428
```

The corresponding actual success rates remain:

```text
M2362 actual_success_rate: 0.06518518518518518
M2397 actual_success_rate: 0.04054010086220921
M2413 actual_success_rate: 0.06685714285714285
```

## Interpretation

M2435 strengthens the current-sim task-quality diagnosis:

```text
The measured failure rate is highly sensitive to small road-boundary tolerance.
At 0.20 m, counterfactual soft success would exceed 0.78 in all three panels,
while actual success remains below 0.067.
```

This is not driver capability evidence by itself. It is evidence that the
current measured panel is dominated by task/termination semantics, so the next
route should audit whether the current offtrack boundary should become:

```text
a hard safety failure,
a soft boundary violation with separate severity,
or a role-conditioned metric depending on obstacle clearance and recovery.
```

## Decision Rows

Supported:

```text
new_measured_rollout_started: false
actual_success_improvement_claim: false
high_boundary_threshold_sensitivity: true
scenario_redesign_executed: false
next_route: route_to_boundary_threshold_sensitivity_result_audit
```

Blocked:

```text
current_sim_verdict
actual success improvement
scenario redesign executed
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
training repair success
```

## Claim Boundary

Supported:

```text
M2435 generated a non-ranking counterfactual boundary-threshold sensitivity
panel.

The dominant current-sim measured failure is highly sensitive to small
positive-clearance road-boundary overshoot.

The next route should audit threshold sensitivity before task-boundary redesign,
more repair, training, or controller-family comparison.
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
m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit
```

M2436 should audit the M2435 threshold panel and decide whether to route to:

```text
1. task-boundary metric/termination redesign design;
2. hard/soft offtrack metric split;
3. high-fidelity/backend validation preparation;
4. branch synthesis or stop for user review.
```

M2436 must not treat M2435 as actual success improvement or a current-sim
verdict.
