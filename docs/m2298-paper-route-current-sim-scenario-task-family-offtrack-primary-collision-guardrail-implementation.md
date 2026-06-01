# M2298 Paper-Route Current-Sim Scenario Task-Family Offtrack-Primary Collision-Guardrail Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass`
- manifest: `experiments/manifests/m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation.json`
- summary: `runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_offtrack_collision_guardrail_materialization.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_offtrack_collision_guardrail_materialization.py`
- reset/rollout/policy action: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_offtrack_collision_guardrail_materialization \
  --all-slices runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/all_slices.csv \
  --dominant-slices runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv \
  --route-recommendation runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/route_recommendation.csv \
  --output-dir runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail \
  --next-blocker m2299-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-result-audit
```

## Materialization Result

```text
input_slice_count: 57
dominant_slice_count: 56
route_recommendation_count: 1
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
profile_diagnostic_slice_count: 20
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
repair_gate_spec_exists: true
guardrail_violation_count: 0
```

Primary route:

```text
offtrack_primary_collision_guardrail_failure_slice_result_audit
```

## Offtrack Targets

M2298 admits 20 non-profile target slices. Examples:

```text
role_family=R0_stable_avoidable
role_family=R1_aeb_infeasible_stable_aes
role_family=R2_handling_limit_drift_capable_avoidance
role_family=R3_recovery_after_limit
role_family=R5_hidden_dynamics_robustness
sampled_obstacle_label=aeb_feasible
sampled_obstacle_label=aes_feasible
sampled_obstacle_label=drift_required
obstacle_longitudinal_timing_bucket=early_far
obstacle_longitudinal_timing_bucket=mid
obstacle_longitudinal_timing_bucket=late_close
obstacle_lateral_offset_bucket=centerline
obstacle_lateral_offset_bucket=left_offset
obstacle_lateral_offset_bucket=right_offset
hidden_dynamics_bucket=low_mu
hidden_dynamics_bucket=nominal
hidden_dynamics_bucket=slow_steer_actuator
hidden_dynamics_bucket=tire_stiffness_shift
outcome_bucket=off_track_noncollision_noncompletion
termination_reason=off_track
```

## Collision Guardrails

M2298 admits 11 non-profile guardrail slices. Examples:

```text
role_family=R4_unavoidable_mitigation
sampled_obstacle_label=drift_required
sampled_obstacle_label=unavoidable
obstacle_longitudinal_timing_bucket=late_close
obstacle_longitudinal_timing_bucket=mid
obstacle_lateral_offset_bucket=centerline
obstacle_lateral_offset_bucket=right_offset
hidden_dynamics_bucket=high_mass_or_inertia
hidden_dynamics_bucket=low_mu
outcome_bucket=collision_failure
termination_reason=obstacle_collision
```

## Repair Gate Spec

`repair_gate_spec.json` defines the later repair gates:

```text
offtrack target policy:
  reduce_global_offtrack_count: true
  reduce_or_hold_target_slice_offtrack_count: true
  target_slice_count: 20

collision guardrail policy:
  do_not_increase_global_collision_count: true
  do_not_increase_guardrail_slice_collision_count: true
  guardrail_slice_count: 11

completeness policy:
  target_episode_count: 1080
  metadata_missing_count: 0
  metric_completeness_failure_count: 0
  guardrail_violation_count: 0
```

Profile axes are explicitly excluded from target/guardrail materialization:

```text
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
```

## Artifacts

```text
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/offtrack_target_slices.csv
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/collision_guardrail_slices.csv
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/profile_diagnostic_slices.csv
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/target_guardrail_matrix.csv
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json
runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/claim_boundary.csv
```

## Claim Boundary

M2298 is artifact materialization only. It does not prove any repair works.

M2298 cannot claim:

- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Pre-registered follow-up:

```text
m2299-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-result-audit
```
