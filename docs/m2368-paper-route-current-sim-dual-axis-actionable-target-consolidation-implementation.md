# M2368 Paper-Route Current-Sim Dual-Axis Actionable Target Consolidation Implementation

- status: completed
- result_class: `current_sim_dual_axis_actionable_target_consolidation_pass`
- manifest: `experiments/manifests/m2368-paper-route-current-sim-dual-axis-actionable-target-consolidation-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_actionable_target_consolidation.py`
- focused tests: `2 passed`
- source summary: `runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json`
- source slice rows: `runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv`
- output summary: `runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json`
- reset/rollout/measured execution in M2368: `false`
- policy action executed in M2368: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID claims: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_actionable_target_consolidation \
  --summary runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json \
  --slice-rows runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv \
  --output-dir runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation \
  --target-slice-row-count 313 \
  --minimum-actionable-episode-count 30 \
  --next-blocker m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit
```

## Result

```text
source_slice_row_count: 313
consolidated_row_count: 313
offtrack_repair_target_row_count: 54
collision_guardrail_row_count: 28
r4_mitigation_semantics_row_count: 48
diagnostic_guardrail_row_count: 190
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Consolidated route counts:

```text
offtrack_repair_target: 36
offtrack_repair_target_with_collision_guardrail: 18
collision_guardrail: 10
r4_mitigation_semantics: 48
diagnostic_guardrail: 190
diagnostic_only: 11
```

Actionability class counts:

```text
diagnostic_guardrail: 190
geometry_timing: 6
hidden_dynamics: 7
role_conditioned_geometry_timing: 30
role_conditioned_hidden_dynamics: 19
role_semantics: 13
r4_mitigation_semantics: 48
```

## Consolidated Targets

Top offtrack repair targets:

```text
obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, offtrack_rate 0.8778, collision_rate 0.0478

sampled_obstacle_label=aes_feasible:
  episode_count 1575, offtrack_rate 0.7956, collision_rate 0.0025

hidden_dynamics_bucket=slow_steer_actuator:
  episode_count 1335, offtrack_rate 0.8097, collision_rate 0.0959

role_family=R0_stable_avoidable:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011
```

Top collision guardrails:

```text
obstacle_longitudinal_timing_bucket=late_close:
  episode_count 1800, offtrack_rate 0.6144, collision_rate 0.3156

obstacle_longitudinal_timing_bucket=mid:
  episode_count 1800, offtrack_rate 0.6867, collision_rate 0.2356

obstacle_lateral_offset_bucket=right_offset:
  episode_count 1380, offtrack_rate 0.6471, collision_rate 0.2797

hidden_dynamics_bucket=low_mu:
  episode_count 945, offtrack_rate 0.6889, collision_rate 0.2952
```

Diagnostic guardrails are preserved for global, pack, profile, and sampling
repair axes, but none are admissible ordinary repair targets.

## Artifacts

```text
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/consolidated_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/claim_boundary.csv
```

## Claim Boundary

M2368 may claim only:

```text
M2365 localization slices have been materialized into consolidated diagnostic
target and guardrail artifacts.
```

Still blocked:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-registered follow-up:

```text
m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit
```
