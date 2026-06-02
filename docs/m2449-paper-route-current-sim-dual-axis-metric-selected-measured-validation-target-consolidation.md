# M2449 Paper-Route Current-Sim Dual-Axis Metric-Selected Measured Validation Target Consolidation

- status: completed
- result_class: `current_sim_dual_axis_metric_selected_measured_validation_target_consolidation_pass`
- manifest: `experiments/manifests/m2449-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation.py`
- summary: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/summary.json`
- target rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/target_rows.csv`
- guardrail rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/guardrail_rows.csv`
- diagnostic rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/diagnostic_rows.csv`
- decision rows: `runs/m2449_paper_route_current_sim_dual_axis_metric_selected_measured_validation_target_consolidation/decision_rows.csv`
- rerun/policy action/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result

M2449 consolidated M2447 localization into artifact-only target and guardrail
tables.

```text
source_localization_row_count: 65
target_localization_row_count: 65
consolidated_row_count: 65
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

Row-class counts:

```text
hard_offtrack_target: 21
collision_guardrail: 35
soft_boundary_diagnostic: 4
monitoring_diagnostic: 5
```

Actionability-class counts:

```text
geometry_timing: 6
hidden_dynamics: 8
role_semantics: 6
scenario_label: 4
diagnostic_monitoring: 41
```

## Target Surface

M2449 defines hard-offtrack target rows only on non-ranking scenario and
condition axes:

```text
role_family
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
sampled_obstacle_label
```

The largest target rows are:

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

Rows can also require collision or soft-boundary guardrails. This does not make
them rankings or winners; it records that any later scenario-quality or repair
route must preserve the collision and boundary diagnostics attached to the same
slice.

## Guardrails And Diagnostics

Collision and soft-boundary rows are preserved separately:

```text
collision_guardrail_row_count: 50
soft_boundary_diagnostic_row_count: 45
```

Profile, pack, family/checkpoint, global, termination, and outcome axes remain
diagnostic-only:

```text
global
profile_name
profile_seed
pack_id
scenario_family_id
termination_reason
outcome_bucket
```

The consolidated artifact explicitly rejects these shortcuts:

```text
profile/pack/family/checkpoint ranking
winner selection
direct repair or training route
actual success improvement claim
scenario redesign executed claim
current-sim verdict
paper/FW-vs-GRU/level3 self-ID/training-repair verdict
```

## Decision

Accepted claim:

```text
M2449 converts M2447 localization into compact hard-offtrack target rows plus
collision, soft-boundary, and monitoring guardrail artifacts.
```

Rejected claims:

```text
driver improvement
repair readiness
training readiness
scenario redesign success
profile/pack/family/checkpoint ranking
winner selection
current-sim verdict
paper/FW-vs-GRU/level3 self-ID/training-repair verdict
```

## Next Route

Next milestone:

```text
m2450-paper-route-current-sim-dual-axis-metric-selected-measured-validation-target-consolidation-result-audit
```

M2450 should audit whether the 21 target rows and guardrail tables support a
bounded synthesis, scenario-quality route, repair-plan design, or stop. It must
not rerun, repair, train, rank, select winners, or make verdict claims.
