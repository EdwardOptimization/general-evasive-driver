# M2439 Paper-Route Current-Sim Dual-Axis Hard/Soft Offtrack Metric Split Result Audit

- status: completed
- decision: `accept_metric_split_route_to_metric_selected_measured_validation_design`
- manifest: `experiments/manifests/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.json`
- audited summary: `runs/m2438_paper_route_current_sim_dual_axis_hard_soft_offtrack_metric_split/summary.json`
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Summary

M2439 accepts M2438 as a complete hard/soft offtrack metric split
implementation:

```text
result_class: current_sim_dual_axis_hard_soft_offtrack_metric_split_pass
panel_row_count: 12
source_count: 3
source_episode_counts:
  m2362: 5400
  m2397: 30735
  m2413: 5250
thresholds_m: [0.02, 0.05, 0.10, 0.20]
actual_success_preserved: true
actual_success_preservation_violation_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

The metric split is non-degenerate at the `0.20 m` threshold:

```text
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
max_actual_success_rate: 0.06685714285714285
max_hard_offtrack_failure_rate_at_0_20m: 0.010476190476190476
min_soft_offtrack_violation_rate_at_0_20m: 0.7175925925925926
```

This confirms the implementation can separate:

```text
actual_success_preserved
collision_or_obstacle_risk_failure
hard_offtrack_failure
soft_offtrack_violation
boundary_tolerated_diagnostic
counterfactual_soft_success
```

without overwriting measured actual success.

## Accepted Evidence

Accepted:

```text
M2438 generated all required artifacts.

M2438 included M2362, M2397, and M2413 rows.

M2438 evaluated the fixed threshold grid 0.02/0.05/0.10/0.20 m.

M2438 preserved measured actual_success exactly.

M2438 kept counterfactual soft success diagnostic-only.

M2438 reported zero guardrail violations.
```

Not accepted as driver evidence:

```text
The high counterfactual soft-success rate is still old-row relabel evidence.

It is not an executed rollout result under a selected metric.

It cannot support actual success improvement, controller ranking, scenario
redesign execution, current-sim verdict, paper-level evidence, or self-ID
claims.
```

## Failure Taxonomy

Observed:

```text
none
```

Specifically not observed:

```text
metric_artifact:
  hard and soft offtrack classes are both nonempty at the 0.20 m audit point.

lineage_invalid:
  M2438 uses M2437 design and the expected M2362/M2397/M2413 episode rows.

contract_violation:
  actual_success_preservation_violation_count is 0 and guardrail violations are
  0.

scenario_sampling_failure:
  all three sources and all required thresholds are present.
```

## Public Gate Overfit Risk

Risk level: `medium`.

Reason:

```text
M2438 still reuses public historical episode rows. It is valid as a metric
implementation and audit artifact, but another same-data relabel panel would
become process overhead.
```

Mitigation:

```text
Do not continue reprocessing the same old rows for success claims.

Route to a measured-validation design that explicitly freezes the hard/soft
metric, threshold policy, denominators, guardrails, and claim boundary before
any fresh rollout.
```

## Decision

M2439 decision:

```text
accept_metric_split_route_to_metric_selected_measured_validation_design
```

Rationale:

```text
The metric split is implemented and guardrailed.

The next useful question is how to measure policies under the selected
hard/soft task metric, not another local relabel or training step.

Fresh measured validation is required before any actual success or current-sim
claim can be made.
```

## Supported Claims

Supported:

```text
M2438 is accepted as a complete hard/soft offtrack metric split panel.

The task-boundary metric redesign branch can proceed to measured-validation
design.
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
m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design
```

M2440 should design a fresh measured-validation protocol under the hard/soft
offtrack metric. It should specify:

```text
threshold policy;
source scenarios and checkpoint set;
hard failure and soft violation reporting;
actual success semantics under the selected metric;
guardrails that preserve obstacle-risk failure and original hard-failure
reporting;
claim boundaries and next implementation criteria.
```

M2440 must not run the measured validation. It should produce a protocol only.
