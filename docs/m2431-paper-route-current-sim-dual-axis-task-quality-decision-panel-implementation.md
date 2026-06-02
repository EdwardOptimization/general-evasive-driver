# M2431 Paper-Route Current-Sim Dual-Axis Task-Quality Decision Panel Implementation

- status: completed
- result_class: `current_sim_dual_axis_task_quality_decision_panel_pass`
- manifest: `experiments/manifests/m2431-paper-route-current-sim-dual-axis-task-quality-decision-panel-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_task_quality_decision_panel.py`
- focused tests: `2 passed`
- summary: `runs/m2431_paper_route_current_sim_dual_axis_task_quality_decision_panel/summary.json`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2431 built a cross-artifact task-quality decision panel from existing measured
artifacts only:

```text
M2362 repaired-pack measured execution
M2397 effective-candidate measured validation
M2413 source-linked measured validation
M2428 matched repair-candidate measured reindex
M2426/M2428 c04 source-coverage caveat
```

Result summary:

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
route_recommendation: route_to_task_semantics_reassessment_before_more_source_linked_repair
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Panel rows:

```text
m2362_repaired_pack_global:
  success_rate: 0.06518518518518518
  collision_rate: 0.19962962962962963
  offtrack_rate: 0.7262962962962963

m2397_effective_candidate_global:
  success_rate: 0.04054010086220921
  collision_rate: 0.10157800553115341
  offtrack_rate: 0.8425898812428827

m2413_source_linked_global:
  success_rate: 0.06685714285714285
  collision_rate: 0.1761904761904762
  offtrack_rate: 0.7424761904761905

m2428_c01_source_linked_geometry_timing_containment:
  success_rate: 0.06689655172413793
  collision_rate: 0.16114942528735632
  offtrack_rate: 0.7583908045977011

m2428_c02_source_linked_hidden_dynamics_response_containment:
  success_rate: 0.06
  collision_rate: 0.09547619047619048
  offtrack_rate: 0.8269047619047619

m2428_c03_source_linked_role_conditioned_containment:
  success_rate: 0.078
  collision_rate: 0.08933333333333333
  offtrack_rate: 0.8162222222222222
```

## Interpretation

M2431 does not claim a current-sim verdict, but it strengthens the route
decision from M2430:

```text
The offtrack-dominated blocker is not isolated to one repair-candidate reindex.
It repeats across repaired-pack, effective-candidate, source-linked, and
matched repair-candidate measured panels.
```

This makes more source-linked local repair a poor next move. Before training,
PPO, or another repair-candidate artifact, the project should audit whether the
current-sim task semantics, road-boundary/offtrack termination, and offtrack
metric are producing a task-quality blocker.

## Decision Rows

Supported:

```text
new_measured_rollout_started: false
candidate_ranking_or_winner: false
next_route: route_to_task_semantics_reassessment_before_more_source_linked_repair
```

Blocked:

```text
current_sim_verdict
self_id_or_finite_window_vs_gru_verdict
c04_source_coverage as measured evidence
more_source_linked_local_repair
```

The c04 outcome-failure-surface candidate remains a source-coverage gap:

```text
c04_source_coverage: gap_observed
admissible: false
reason: c04 remains excluded when the outcome-failure source key has no executable source match.
```

## Claim Boundary

Supported:

```text
M2431 generated a non-ranking task-quality decision panel.

All included measured panels are offtrack-dominated.

c04 source coverage remains missing and must not be treated as measured.

The next route should be a task-semantics reassessment audit before more
source-linked local repair.
```

Blocked:

```text
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
m2432-paper-route-current-sim-dual-axis-task-quality-decision-panel-result-audit
```

M2432 should audit M2431 and choose among:

```text
1. task-semantics reassessment route;
2. source-coverage repair only if c04 is essential to task-quality diagnosis;
3. high-fidelity/backend validation preparation if current-sim semantics are
   judged too weak for further local repair;
4. stop for user review if no bounded route is supported.
```

M2432 must not treat M2431 as a current-sim verdict or driver improvement.
