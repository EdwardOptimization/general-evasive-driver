# M2444 Paper-Route Current-Sim Dual-Axis Metric-Selected Validation Preflight Result Audit

- status: completed
- decision: `accept_metric_selected_preflight_route_to_full_measured_validation_implementation`
- manifest: `experiments/manifests/m2444-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-result-audit.json`
- audited summary: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/summary.json`
- audited workload rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/workload_rows.csv`
- audited reset rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/reset_validation_rows.csv`
- audited decision rows: `runs/m2443_paper_route_current_sim_dual_axis_metric_selected_validation_preflight/decision_rows.csv`
- new measured rollout/policy action/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2444 accepts M2443 as a complete metric-selected validation preflight.

Audited M2443 values:

```text
result_class: current_sim_dual_axis_metric_selected_validation_preflight_pass
workload_row_count: 5250
reset_target_count: 350
selected_checkpoint_count: 15
source_m2413_episode_count: 5250
source_m2413_reset_target_count: 350
source_m2413_selected_checkpoint_count: 15
source_m2413_unique_cell_count: 5250
source_m2413_duplicate_cell_count: 0
missing_source_target_count: 0
missing_source_selected_checkpoint_count: 0
missing_source_cell_count: 0
environment_reset_success_count: 350
environment_reset_failure_count: 0
actor_observation_shape_changed_count: 0
finite_observation_count: 350
soft_enabled_reset_count: 350
contract_guardrail_pass_count: 350
environment_step_count: 0
policy_action_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

## Decision

Accepted claim:

```text
The M2413 350 x 15 denominator is ready for a bounded metric-selected measured
validation implementation under soft_offtrack_metric_enabled=true and
soft_offtrack_tolerance_m=0.20.
```

Reason:

```text
M2443 verified complete source-cell coverage, no source duplicates, no missing
targets/checkpoints/cells, 350/350 soft-boundary reset success, unchanged actor
observation shape, finite reset observations, zero environment steps, zero
policy actions, zero ranking/winner flags, and zero guardrail violations.
```

Rejected claims:

```text
M2443/M2444 do not measure closed-loop driver performance.
M2443/M2444 do not establish actual success improvement.
M2443/M2444 do not execute scenario redesign, repair, training, replay, or PPO.
M2443/M2444 do not rank candidate families, controller families, or checkpoints.
M2443/M2444 do not support a paper verdict, finite-window vs GRU conclusion,
level3 self-identification claim, training-repair success, or current-sim
verdict.
```

## Route

Next milestone:

```text
m2445-paper-route-current-sim-dual-axis-metric-selected-measured-validation-implementation
```

M2445 may execute the bounded metric-selected measured-validation workload using
the M2443 workload/preflight artifacts. It should produce executed episode rows
and aggregate metrics under the hard/soft offtrack task boundary. It must not
repair, train, rank candidates/controllers, select a winner, promote a
checkpoint, or claim a paper/current-sim/self-ID verdict; those require a later
result audit.
