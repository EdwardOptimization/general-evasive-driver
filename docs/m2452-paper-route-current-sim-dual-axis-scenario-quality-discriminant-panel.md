# M2452 Paper-Route Current-Sim Dual-Axis Scenario-Quality Discriminant Panel

- status: completed
- result_class: `current_sim_dual_axis_scenario_quality_discriminant_panel_pass`
- manifest: `experiments/manifests/m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel.py`
- summary: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/summary.json`
- panel rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/panel_rows.csv`
- guardrail rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/guardrail_rows.csv`
- decision rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/decision_rows.csv`
- rerun/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result

M2452 combines the existing M2445 episode rows with the M2449 target,
guardrail, and diagnostic rows. It does not rerun rollout or execute a policy.

```text
episode_count: 5250
target_row_count: 21
guardrail_row_count: 56
diagnostic_row_count: 44
panel_row_count: 71
scenario_quality_blocker_count: 7
possible_repair_plan_candidate_count: 19
collision_mitigation_guardrail_count: 52
hidden_dynamics_guardrail_count: 9
geometry_timing_guardrail_count: 7
monitoring_only_count: 41
stable_task_quality_blocker_count: 2
drift_candidate_count: 5
route_supported: true
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Panel-class counts:

```text
scenario_quality_blocker: 7
possible_repair_plan_candidate: 19
collision_mitigation_guardrail: 2
guardrail_diagnostic: 2
monitoring_only: 41
```

## Discriminant Split

M2452 separates the broad hard-offtrack surface into non-ranking classes:

```text
scenario_quality_blocker:
  stable avoidable / AEB-feasible rows
  stable AES feasible rows
  broad geometry/timing distribution rows

possible_repair_plan_candidate:
  drift-required rows
  R2/R3/R5 handling-limit and recovery rows
  hidden-dynamics stress rows
  geometry/timing target rows that may inform a later bounded repair plan

collision_mitigation_guardrail:
  unavoidable / R4 rows
  collision-bearing repair-candidate rows

monitoring_only:
  profile, profile_seed, pack, scenario_family, termination, outcome, and global rows
```

The strongest task-quality warning is that ordinary stable-avoidable rows remain
hard-offtrack dominated:

```text
R0_stable_avoidable / aeb_feasible:
  episode_count: 900
  actual_success_rate: 0.06111111111111111
  hard_offtrack_rate: 0.9333333333333333
  collision_rate: 0.0
```

Stable AES rows also remain hard-offtrack dominated:

```text
R1_aeb_infeasible_stable_aes / aes_feasible:
  episode_count: 900
  actual_success_rate: 0.3288888888888889
  hard_offtrack_rate: 0.66
  collision_rate: 0.011111111111111112
```

The handling-limit branch remains present but guarded:

```text
drift_required:
  episode_count: 2025
  actual_success_rate: 0.0
  hard_offtrack_rate: 0.7955555555555556
  collision_rate: 0.19407407407407407
```

The broad geometry/timing distribution is itself hard-offtrack dominated:

```text
all_offsets_and_timings:
  episode_count: 5250
  actual_success_rate: 0.06685714285714285
  hard_offtrack_rate: 0.7468571428571429
  collision_rate: 0.1761904761904762
  source rows: centerline, early_far, mid, late_close, left_offset, right_offset
```

## Supported Claims

Supported:

```text
M2452 can separate stable/AES task-quality blockers from handling-limit repair
candidate and collision-mitigation guardrail classes using only existing
M2445/M2449 artifacts.

Profile, pack, checkpoint/family, global, termination, and outcome axes remain
monitoring-only and non-ranking.

The next route should audit this discriminant panel before scenario redesign,
repair-plan design, training, ranking, or verdict claims.
```

## Rejected Claims

Rejected or still blocked:

```text
driver improvement
actual success improvement
scenario redesign executed
repair-plan success
training success
profile/pack/checkpoint ranking
candidate-family or controller-family ranking
winner selection
paper-level result
finite-window-vs-GRU result
level3 self-identification
current-sim verdict
```

## Decision

The panel supports a bounded result-audit route:

```text
m2453-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel-result-audit
```

M2453 should audit whether this discriminant panel routes to scenario redesign,
guarded repair-plan design, another branch synthesis, or stop. It must not
rerun, repair, train, rank, select winners, or make verdict claims.
