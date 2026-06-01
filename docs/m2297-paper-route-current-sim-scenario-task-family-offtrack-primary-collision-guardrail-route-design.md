# M2297 Paper-Route Current-Sim Scenario Task-Family Offtrack-Primary Collision-Guardrail Route Design

- status: completed
- decision: `route_to_offtrack_target_collision_guardrail_materialization`
- manifest: `experiments/manifests/m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design.json`
- parent audit: `docs/m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit.md`
- reset/rollout/policy action in M2297: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2297 accepts the M2296 route and selects a non-rollout implementation:

```text
m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation
```

M2298 should materialize explicit offtrack target slices and collision guardrail
slices from M2295 artifacts. It should not train. The goal is to convert the
failure diagnosis into a repair/evaluation target pack that a later training or
scenario-repair milestone can consume.

## Target Slice Rule

M2298 should read:

```text
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/all_slices.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/dominant_slices.csv
runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/route_recommendation.csv
```

Offtrack target candidates are admissible only from non-profile axes:

```text
termination_reason
outcome_bucket
role_family
sampled_obstacle_label
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
hidden_dynamics_bucket
```

Profile axes are diagnostic context only and must not define repair targets:

```text
profile_name
profile_seed
```

Admit an offtrack target slice if:

```text
dominant_failure_mode == offtrack_dominated_failure
and offtrack_count >= 100
```

Always include the two primary global-equivalent offtrack slices:

```text
termination_reason=off_track
outcome_bucket=off_track_noncollision_noncompletion
```

## Collision Guardrail Rule

Admit a collision guardrail slice if:

```text
dominant_failure_mode == collision_dominated_failure
or collision_count >= 50
```

Use the same non-profile axes. Collision guardrails should include at least:

```text
outcome_bucket=collision_failure
termination_reason=obstacle_collision
role_family=R4_unavoidable_mitigation
```

Guardrails are not success targets. They are constraints for later repair:
reducing offtrack is not acceptable if collision count or collision rate worsens
on these slices.

## Current Diagnostic Anchors

M2295 top offtrack anchors:

```text
termination_reason=off_track:
  offtrack_count: 785

outcome_bucket=off_track_noncollision_noncompletion:
  offtrack_count: 785

obstacle_lateral_offset_bucket=centerline:
  offtrack_count: 383

sampled_obstacle_label=drift_required:
  offtrack_count: 323

obstacle_longitudinal_timing_bucket=early_far:
  offtrack_count: 310

obstacle_longitudinal_timing_bucket=mid:
  offtrack_count: 256

sampled_obstacle_label=aes_feasible:
  offtrack_count: 249

hidden_dynamics_bucket=slow_steer_actuator:
  offtrack_count: 230
```

M2295 collision guardrail anchors:

```text
outcome_bucket=collision_failure:
  collision_count: 209

termination_reason=obstacle_collision:
  collision_count: 208

role_family=R4_unavoidable_mitigation:
  collision_count: 134

obstacle_longitudinal_timing_bucket=late_close:
  collision_count: 115
```

## M2298 Outputs

M2298 should write:

```text
summary.json
offtrack_target_slices.csv
collision_guardrail_slices.csv
profile_diagnostic_slices.csv
target_guardrail_matrix.csv
repair_gate_spec.json
claim_boundary.csv
```

The `repair_gate_spec.json` should define later pass/fail gates without running
them:

```text
offtrack target:
  reduce global offtrack_count and offtrack_rate
  reduce or hold offtrack_count on admitted target slices

collision guardrail:
  do not increase global collision_count
  do not increase collision_count on admitted guardrail slices

completeness:
  keep 1080/1080 measured execution support
  metadata_missing_count == 0
  metric_completeness_failure_count == 0
  guardrail_violation_count == 0

claim boundary:
  no ranking
  no winner
  no paper-level claim
  no finite-window vs GRU claim
  no level3 self-ID claim
```

## M2298 Pass Gates

M2298 passes only if:

```text
summary.json exists
input_slice_count > 0
offtrack_target_slice_count >= 8
collision_guardrail_slice_count >= 3
profile_target_slice_count == 0
profile_guardrail_slice_count == 0
repair_gate_spec exists
guardrail_violation_count == 0
```

## Claim Boundary

M2297 is a design artifact only. It does not claim that any repair works.

M2297 blocks:

- direct broad PPO/reward repair before target/guardrail materialization;
- profile ranking from diagnostic slices;
- changing actor inputs or scenario specs to improve this result;
- paper-level, finite-window vs GRU, or level3 self-ID claims.

## Next

Pre-registered:

```text
experiments/manifests/m2298-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-implementation.json
```
