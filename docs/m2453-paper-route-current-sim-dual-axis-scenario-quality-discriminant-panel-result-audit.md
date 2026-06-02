# M2453 Paper-Route Current-Sim Dual-Axis Scenario-Quality Discriminant Panel Result Audit

- status: completed
- decision: `accept_panel_route_to_scenario_quality_redesign_protocol_design`
- manifest: `experiments/manifests/m2453-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel-result-audit.json`
- audited doc: `docs/m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel.md`
- audited summary: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/summary.json`
- audited panel rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/panel_rows.csv`
- audited guardrail rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/guardrail_rows.csv`
- audited decision rows: `runs/m2452_paper_route_current_sim_dual_axis_scenario_quality_discriminant_panel/decision_rows.csv`
- rerun/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2453 accepts M2452 as a complete artifact-only discriminant panel.

```text
result_class: current_sim_dual_axis_scenario_quality_discriminant_panel_pass
episode_count: 5250
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

The panel separates the broad hard-offtrack surface into useful next-route
classes, but it does not make any driver-improvement or paper-level claim.

## Main Finding

The stable task-quality blocker is strong enough to block direct repair or
training from the M2452 target rows.

```text
R0_stable_avoidable / aeb_feasible:
  actual_success_rate: 0.06111111111111111
  hard_offtrack_rate: 0.9333333333333333
  collision_rate: 0.0

R1_aeb_infeasible_stable_aes / aes_feasible:
  actual_success_rate: 0.3288888888888889
  hard_offtrack_rate: 0.66
  collision_rate: 0.011111111111111112
```

This is not a handling-limit self-ID result. It says the current scenario and
boundary design is still failing ordinary stable/AES cases mostly by road
departure rather than collision. A repair/training route that starts from
drift-required or hidden-dynamics rows would be under-specified while stable
avoidance itself remains task-quality blocked.

## Guarded Repair Candidate Surface

M2452 still preserves a handling-limit repair-planning surface:

```text
drift_required:
  episode_count: 2025
  actual_success_rate: 0.0
  hard_offtrack_rate: 0.7955555555555556
  collision_rate: 0.19407407407407407

possible_repair_plan_candidate_count: 19
hidden_dynamics_guardrail_count: 9
geometry_timing_guardrail_count: 7
```

This is not narrow enough for repair or training yet. It should remain a
guardrail surface for later, after the scenario-quality redesign protocol
defines what stable/AES feasibility should mean and how geometry/timing cases
will be admitted.

## Monitoring Axes

M2452 keeps monitoring axes non-ranking:

```text
monitoring_only_count: 41
ranking_admissible_count: 0
winner_selected_count: 0
```

Profile, pack, checkpoint/family, global, termination, and outcome rows must
not be converted into controller-family or candidate-family winners from this
panel.

## Decision

Accepted route:

```text
route_to_scenario_quality_redesign_protocol_design
```

Next milestone:

```text
m2454-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-design
```

M2454 should design, but not execute, the next scenario-quality protocol. It
should define role-specific feasibility, boundary, geometry/timing, and
guardrail rules before any scenario-redesign implementation, repair-plan
materialization, training, ranking, or verdict route.

## Rejected Routes

Rejected for now:

```text
direct repair/training from M2452 rows
direct scenario redesign execution without protocol design
candidate-family ranking
controller/profile/pack/checkpoint ranking
winner selection
current-sim verdict
paper-level or finite-window-vs-GRU verdict
level3 self-identification claim
```
