# M2432 Paper-Route Current-Sim Dual-Axis Task-Quality Decision Panel Result Audit

- status: completed
- decision: `task_quality_panel_accepted_route_to_offtrack_semantics_panel`
- manifest: `experiments/manifests/m2432-paper-route-current-sim-dual-axis-task-quality-decision-panel-result-audit.json`
- parent implementation: `docs/m2431-paper-route-current-sim-dual-axis-task-quality-decision-panel-implementation.md`
- parent summary: `runs/m2431_paper_route_current_sim_dual_axis_task_quality_decision_panel/summary.json`
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2432 accepts M2431 as a complete task-quality decision panel. The result is
negative for continuing source-linked local repair and positive for routing to
task-semantics reassessment.

Accepted panel evidence:

```text
result_class: current_sim_dual_axis_task_quality_decision_panel_pass
measured_panel_count: 6
offtrack_dominated_panel_count: 6
all_measured_panels_offtrack_dominated: true
min_success_rate: 0.04054010086220921
max_success_rate: 0.078
min_offtrack_rate: 0.7262962962962963
max_offtrack_rate: 0.8425898812428827
c04_source_coverage_gap_observed: true
outcome_blocker: current_sim_task_quality_blocker_observed
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Included panels:

```text
M2362 repaired-pack global
M2397 effective-candidate global
M2413 source-linked global
M2428 c01 source-linked geometry/timing containment
M2428 c02 source-linked hidden-dynamics/response containment
M2428 c03 source-linked role-conditioned containment
```

All included rows are diagnostic-only and non-ranking.

## Diagnosis

The same dominant failure appears after multiple levels of current-sim repair
and source-linking:

```text
repaired-pack measured execution
  -> effective-candidate measured validation
  -> source-linked measured validation
  -> matched repair-candidate measured reindex
```

This means the next useful question is no longer:

```text
Which source-linked local repair candidate should we try next?
```

The next useful question is:

```text
What does offtrack mean in these current-sim panels?
```

The episode rows already contain event-level fields that can separate:

```text
offtrack with large obstacle clearance
offtrack with small road-boundary overshoot
offtrack before obstacle pass
offtrack after obstacle pass
collision-risk offtrack
recovery-capable versus non-recoverable offtrack
```

That distinction is necessary before another repair or training route. If the
offtrack blocker is mostly small road-boundary overshoot with large obstacle
clearance, the task-quality issue is different from a policy that collides or
cannot react to obstacles.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure:
  repeated measured panels remain offtrack-dominated.

source_coverage_gap:
  c04 outcome-failure-surface measured evidence remains unavailable.

task_quality_blocker:
  the dominant failure now needs event-level semantics before more local repair.
```

Not observed:

```text
lineage_invalid
contract_violation
metric_artifact in M2431
scenario_sampling_failure in M2431
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
task_quality_panel_accepted_route_to_offtrack_semantics_panel
```

Next milestone:

```text
m2433-paper-route-current-sim-dual-axis-offtrack-semantics-panel-implementation
```

M2433 should materialize an offtrack-semantics panel from existing primary
episode rows only:

```text
M2362 episode_rows.csv
M2397 episode_rows.csv
M2413 episode_rows.csv
```

The panel should report, per source:

```text
offtrack_count and offtrack_rate
offtrack_positive_clearance_count/rate
offtrack_high_clearance_count/rate
offtrack_low_overshoot_count/rate
offtrack_positive_clearance_low_overshoot_count/rate
mean time_to_first_off_track_s
mean max_off_track_overshoot
collision_count/rate
success_count/rate
```

Allowed M2433 claims:

```text
event-level offtrack semantics reanalysis
task-quality evidence for whether offtrack is road-boundary dominated
route recommendation for result audit
```

Blocked M2433 claims:

```text
new measured rollout
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
M2431 is accepted as a complete task-quality decision panel.

Repeated offtrack dominance is strong enough to stop source-linked local repair
as the immediate next branch.

The next bounded evidence-producing step is event-level offtrack semantics
analysis over existing episode rows.
```

Blocked:

```text
driver improvement
scenario redesign success
repair execution
training repair success
current-sim verdict
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
```
