# M2436 Paper-Route Current-Sim Dual-Axis Boundary-Threshold Sensitivity Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- route decision: `promote_to_task_boundary_metric_termination_redesign_branch`
- manifest: `experiments/manifests/m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit.json`
- synthesized branch: M2431-M2435 current-sim task-quality decision branch
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2431-M2435 converted the repeated offtrack-dominated current-sim result into a
task-boundary metric diagnosis.

Task-quality panel:

```text
M2431 result_class: current_sim_dual_axis_task_quality_decision_panel_pass
measured_panel_count: 6
offtrack_dominated_panel_count: 6
all_measured_panels_offtrack_dominated: true
min_success_rate: 0.04054010086220921
max_success_rate: 0.078
min_offtrack_rate: 0.7262962962962963
max_offtrack_rate: 0.8425898812428827
c04_source_coverage_gap_observed: true
```

Offtrack semantics panel:

```text
M2433 result_class: current_sim_dual_axis_offtrack_semantics_panel_pass
panel_row_count: 3
road_boundary_dominated_panel_count: 3
min_positive_clearance_low_overshoot_rate: 0.9841229193341869
max_positive_clearance_low_overshoot_rate: 0.9882130888640653
min_offtrack_high_clearance_rate: 0.895112016293279
max_mean_offtrack_max_overshoot: 0.07326005531775727
```

Boundary-threshold sensitivity panel:

```text
M2435 result_class: current_sim_dual_axis_boundary_threshold_sensitivity_panel_pass
thresholds_m: [0.02, 0.05, 0.10, 0.20]
high_boundary_threshold_sensitivity_detected: true
max_actual_success_rate: 0.06685714285714285
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
actual_success_improvement_claim_made: false
guardrail_violation_count: 0
```

## Supported Claims

Supported:

```text
The dominant current-sim measured failure is repeated offtrack dominance.

The offtrack dominance is primarily positive-clearance low-overshoot
road-boundary termination, not obstacle-contact or zero-clearance failure.

The measured failure rate is highly sensitive to road-boundary tolerance.

Counterfactual soft success must remain separate from actual success because no
new rollout, scenario redesign, or policy execution occurred.

The next route should design a hard/soft offtrack metric and termination split
before more repair, training, or controller-family comparison.
```

This advances scenario/task-quality evidence and workflow control. It does not
advance engineering driver performance or mechanism evidence for history
dependence.

## Falsified Claims

Falsified or blocked:

```text
Continue source-linked local repair:
  blocked because repeated panels show a task-boundary metric blocker.

Train/PPO directly from the offtrack-dominated panel:
  blocked because the dominant target may be a termination/metric artifact.

Treat counterfactual soft success as actual success:
  blocked because all M2435 rows are diagnostic-only and no rollout was rerun.

Claim current-sim verdict:
  blocked because task-boundary metric redesign has not been implemented or
  validated in fresh measured rollout.

Claim paper/FW-vs-GRU/self-ID result:
  blocked because this branch does not compare controller families or history
  interventions.
```

## Failure Taxonomy Summary

Observed:

```text
task_quality_blocker:
  current-sim offtrack semantics dominate measured outcomes.

metric_semantics_sensitivity:
  soft-success counterfactual changes are large at small boundary tolerances.

local_search_guard_triggered:
  another ordinary audit or design-only step would exceed the branch guard.
```

Not observed:

```text
lineage_invalid
contract_violation
scenario_sampling_failure in M2435
actual success improvement claim
active config overwrite
repair execution
training repair success
candidate/controller ranking
winner selection
hidden/oracle actor-input injection
```

## Public Gate Overfit Risk

Risk level: `medium-high` if the branch continues to reprocess the same measured
episode rows.

Why:

```text
M2431, M2433, and M2435 all use existing public measured artifacts. They add
real evidence by changing the analysis axis from aggregate offtrack to event
semantics and threshold sensitivity, but another same-data panel would become
local-search process overhead.
```

Required mitigation:

```text
Open a new branch that designs the metric/termination semantics explicitly.

Do not run more source-linked repair, PPO, or controller-family comparison
until the hard/soft offtrack metric split is specified.

Do not claim actual success from counterfactual soft-success rows.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before M2431, the project only knew the current-sim measured panels were
offtrack-dominated.

After M2435, the project knows that the dominant offtrack mode is
positive-clearance, low-road-boundary-overshoot, and highly threshold-sensitive.
```

Process overhead:

```text
high but productive
```

Reason:

```text
The branch used several audit/reanalysis steps, but it produced three concrete
panels and a clear next route. Continuing the same branch without redesign
would be over-local search.
```

Paper verdict delta:

```text
positive for task-quality readiness, neutral for driver capability.
```

The result improves the route toward a defensible current-sim benchmark, but no
paper-level driver/self-ID claim is supported yet.

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_current_sim_dual_axis_task_boundary_metric_redesign
```

Next milestone:

```text
m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design
```

M2437 should design a task-boundary metric/termination contract that separates:

```text
hard offtrack failure:
  severe road departure or safety-critical boundary violation.

soft offtrack violation:
  positive-clearance, low-overshoot road-boundary event with severity recorded
  separately and no actual success promotion.

collision or obstacle-risk failure:
  obstacle contact or low/negative clearance.

actual success:
  only an executed rollout outcome under the selected metric, never a
  counterfactual relabel.
```

Allowed M2437 claims:

```text
metric/termination redesign design
hard/soft offtrack claim-boundary specification
admission criteria for future measured rollout
```

Blocked M2437 claims:

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
