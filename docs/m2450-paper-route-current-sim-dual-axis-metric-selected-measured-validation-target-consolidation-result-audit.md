# M2450 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Target Consolidation Result Audit

- status: completed
- decision: `accept_target_consolidation_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2450-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation-result-audit.json`
- audited summary: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/summary.json`
- audited target rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/target_rows.csv`
- audited guardrail rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/guardrail_rows.csv`
- audited diagnostic rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/diagnostic_rows.csv`
- rerun/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2450 accepts M2449 as a complete target-consolidation artifact.

Audited evidence:

```text
result_class: current_sim_dual_axis_metric_selected_measured_validation_target_consolidation_pass
source_localization_row_count: 65
hard_offtrack_target_row_count: 21
guardrail_row_count: 56
collision_guardrail_row_count: 50
soft_boundary_diagnostic_row_count: 45
diagnostic_row_count: 44
monitoring_row_count: 41
diagnostic_axis_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

The target rows are compact enough to audit, but they are not narrow:

```text
role_family targets: 5
hidden_dynamics targets: 7
geometry/timing targets: 6
scenario-label targets: 3
```

Largest target rows:

```text
obstacle_lateral_offset_bucket=centerline:
  episode_count 2700, hard_offtrack_count 2050, hard_offtrack_rate 0.7592592592592593

sampled_obstacle_label=drift_required:
  episode_count 2025, hard_offtrack_count 1611, hard_offtrack_rate 0.7955555555555556

obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, hard_offtrack_count 1566, hard_offtrack_rate 0.87

obstacle_longitudinal_timing_bucket=mid:
  episode_count 1725, hard_offtrack_count 1251, hard_offtrack_rate 0.7252173913043478

sampled_obstacle_label=aes_feasible:
  episode_count 1575, hard_offtrack_count 1246, hard_offtrack_rate 0.7911111111111111
```

## Decision

Accepted claims:

```text
M2449 successfully separated hard-offtrack targets from collision,
soft-boundary, and monitoring guardrails.

Profile, pack, family/checkpoint, global, termination, and outcome axes remain
diagnostic-only and non-ranking.
```

Rejected claims:

```text
direct repair readiness
training readiness
scenario redesign success
controller/profile/checkpoint ranking
winner selection
actual success improvement
current-sim verdict
paper/FW-vs-GRU/level3 self-ID/training-repair verdict
```

Why branch synthesis, not direct repair:

```text
The target surface is broad and task-quality related. It includes ordinary
stable/avoidable rows, AES rows, drift-required rows, hidden-dynamics rows, and
geometry/timing rows. A direct repair route would risk another local-search
loop around target tables rather than a branch-level decision about scenario
quality, metric-selected validation, and repair-plan scope.
```

## Next Route

Next milestone:

```text
m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis
```

M2451 should synthesize M2443-M2450 and decide whether to continue, pivot, stop,
or promote to a named next branch. It must preserve the distinction between
fresh measured actual success, hard-offtrack target consolidation, and
diagnostic-only guardrails. It must not rerun, repair, train, rank, select
winners, or make verdict claims.
