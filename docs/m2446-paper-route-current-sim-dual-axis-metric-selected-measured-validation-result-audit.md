# M2446 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Result Audit

- status: completed
- decision: `accept_metric_selected_measured_artifact_route_to_outcome_localization`
- manifest: `experiments/manifests/m2446-paper-route-current-sim-dual-axis-metric-selected-measured-validation-result-audit.json`
- audited summary: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/summary.json`
- audited episode rows: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/episode_rows.csv`
- audited aggregate rows: `runs/m2445_paper_route_current_sim_dual_axis_metric_selected_measured_validation/aggregate_rows.csv`
- comparison source: `runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json`
- rerun/repair/training/replay/PPO/ranking/winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair verdict claims: `false`

## Audit Result

M2446 accepts M2445 as a complete measured-validation artifact.

Audited completeness:

```text
episode_count: 5250
target_episode_count: 5250
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
```

Audited raw outcome:

```text
metric_selected_actual_success_rate: 0.06685714285714285
metric_selected_hard_offtrack_failure_rate: 0.7468571428571429
metric_selected_soft_offtrack_violation_rate: 0.0032380952380952383
metric_selected_boundary_tolerated_success_rate: 0.0
global_collision_rate: 0.1761904761904762
global_offtrack_rate: 0.7453333333333333
global_dominant_failure_mode: offtrack_dominated_failure
```

This is a task-quality blocker classification, not a paper/current-sim verdict.

## M2438 vs M2445

M2438 old-row relabel panel reported:

```text
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
max_actual_success_rate: 0.06685714285714285
max_hard_offtrack_failure_rate_at_0_20m: 0.010476190476190476
```

M2445 fresh soft-boundary execution measured:

```text
actual_success_rate: 0.06685714285714285
hard_offtrack_failure_rate: 0.7468571428571429
soft_offtrack_violation_rate: 0.0032380952380952383
boundary_tolerated_success_rate: 0.0
```

The audit classification:

```text
M2438 old-row relabel was useful as a diagnostic that boundary semantics were
dominating the old metric. It was not a valid predictor that the same policy
would stay within a 0.20 m soft boundary when the environment actually allowed
continued rollout past the original boundary.
```

Reason:

```text
Old hard-termination rows stop at the first boundary crossing, so relabeling
them cannot test whether the closed-loop policy can recover or stay inside the
new soft tolerance after termination is removed. M2445 is the correct fresh
execution test for that question, and it shows the policy usually continues
into hard offtrack failure rather than converting into boundary-tolerated
success.
```

## Decision

Accepted claim:

```text
M2445 is a complete fresh metric-selected measured-validation artifact, and the
current selected-checkpoint set remains hard-offtrack dominated under true
soft-boundary execution.
```

Rejected claims:

```text
old-row diagnostic soft success implies fresh soft-boundary success
M2445 supports actual success improvement
M2445 supports candidate/controller ranking or winner selection
M2445 supports scenario redesign execution
M2445 supports paper/FW-vs-GRU/level3 self-ID/training-repair verdicts
```

## Next Route

Next milestone:

```text
m2447-paper-route-current-sim-dual-axis-metric-selected-measured-validation-outcome-localization
```

M2447 should localize the M2445 failures from artifacts only. It should identify
where hard offtrack is concentrated by profile, pack, role family, scenario
family, timing/lateral buckets, hidden-dynamics bucket, and overshoot severity.
It must keep all axes diagnostic-only and non-ranking, and it must not rerun,
repair, train, select winners, or claim a verdict.
