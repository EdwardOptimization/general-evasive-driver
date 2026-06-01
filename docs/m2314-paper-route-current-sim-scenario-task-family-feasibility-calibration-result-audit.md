# M2314 Paper-Route Current-Sim Scenario Task-Family Feasibility Calibration Result Audit

- status: completed
- decision: `route_to_metric_semantics_conflict_diagnosis`
- manifest: `experiments/manifests/m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit.json`
- parent summary: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/summary.json`
- parent support labels: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv`
- parent role summary: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv`
- reset/rollout/policy action in M2314: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2313 is complete enough for result audit:

```text
result_class: current_sim_scenario_task_family_feasibility_calibration_pass
episode_count: 1080
scenario_spec_count: 72
support_policy_count: 3
seed_repeat_count: 5
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
```

The M2313 claim boundary held. Support policies are diagnostic support bounds,
not controller-family candidates.

## Support Label Audit

Global support labels:

```text
support_clear: 12
support_mixed: 26
support_blocked: 21
metric_conflict: 13
```

Role support summary:

```text
R0_stable_avoidable:
  metric_conflict: 12 / 12

R1_aeb_infeasible_stable_aes:
  support_clear: 12 / 12

R2_handling_limit_drift_capable_avoidance:
  support_mixed: 7 / 12
  support_blocked: 5 / 12

R3_recovery_after_limit:
  support_mixed: 8 / 12
  support_blocked: 3 / 12
  metric_conflict: 1 / 12

R4_unavoidable_mitigation:
  support_mixed: 3 / 12
  support_blocked: 9 / 12

R5_hidden_dynamics_robustness:
  support_mixed: 8 / 12
  support_blocked: 4 / 12
```

## R0 Metric Conflict

R0 is the strongest blocker. It is labeled `aeb_feasible`, but the current
success semantics require `success_obstacle_pass`.

For R0 AEB rows:

```text
row_count: 60
termination_reason: speed_too_low in 60 / 60
collision_count: 0
offtrack_count: 0
min_clearance_margin_min: 10.96082732487428
min_clearance_margin_mean: 26.15242840807228
min_clearance_margin_max: 43.58735902844862
```

This is a metric semantics conflict, not ordinary infeasibility. In an
AEB-feasible role, stopping safely before the obstacle should be a meaningful
support outcome. Under the current role-family panel, those rows are counted as
non-success because they do not pass the obstacle. Direct training on this
semantics would push a driver to pass an obstacle in a role that is explicitly
defined as pure braking feasible.

## Route Decision

Route to no-rerun metric semantics conflict diagnosis:

```text
m2315-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-implementation
```

M2315 should consume only M2313 artifacts and quantify:

```text
safe-stop metric conflicts;
speed_too_low with positive clearance;
metric_conflict rows by role and support policy;
whether R0 should use safe-stop success semantics instead of obstacle-pass
success semantics;
which support_blocked roles remain after separating metric conflicts.
```

M2315 must not run reset, rollout, policy action, measured execution, training,
replay, PPO, private holdout, controller ranking, winner selection, paper-level
claims, finite-window vs GRU claims, or level3 self-ID claims.

## Blocked Routes

Blocked:

```text
direct training from M2313 support labels;
controller-family ranking from support-policy data;
claiming R0 as support_blocked;
weakening self-ID standards;
paper-level comparison before metric semantics are repaired.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2315-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-implementation.json
```
