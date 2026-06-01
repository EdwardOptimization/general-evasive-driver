# M2296 Paper-Route Current-Sim Scenario Task-Family Failure-Slice Diagnosis Result Audit

- status: completed
- decision: `accept_offtrack_primary_collision_guardrail_route_design`
- manifest: `experiments/manifests/m2296-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-result-audit.json`
- parent summary: `runs/m2295_paper_route_current_sim_scenario_task_family_failure_slice_diagnosis/summary.json`
- rerun/reset/rollout/policy action in M2296: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2296 accepts M2295 as a valid artifact-only failure-slice diagnosis:

```text
result_class: current_sim_scenario_task_family_failure_slice_diagnosis_pass
input_episode_count: 1080
episode_count_match: true
success_count_match: true
offtrack_count_match: true
collision_count_match: true
max_step_count_match: true
guardrail_violation_count: 0
```

The primary route is accepted:

```text
offtrack_primary_collision_guardrail_failure_slice_result_audit
```

Rationale:

```text
global_success_rate: 0.06388888888888888
global_offtrack_rate: 0.7268518518518519
global_collision_rate: 0.1935185185185185
global_dominant_failure_mode: offtrack_dominated_failure
```

## Slice Interpretation

M2295 shows that offtrack is not a minor tail failure. It dominates the first
complete role-family panel.

The strongest offtrack slices include:

```text
termination_reason=off_track:
  offtrack_count: 785

outcome_bucket=off_track_noncollision_noncompletion:
  offtrack_count: 785

obstacle_lateral_offset_bucket=centerline:
  offtrack_count: 383
  collision_count: 84

sampled_obstacle_label=drift_required:
  offtrack_count: 323
  collision_count: 73

obstacle_longitudinal_timing_bucket=early_far:
  offtrack_count: 310
  collision_count: 18

hidden_dynamics_bucket=slow_steer_actuator:
  offtrack_count: 230
  collision_count: 31
```

Collision remains a guardrail, not an ignorable secondary metric:

```text
outcome_bucket=collision_failure:
  collision_count: 209

termination_reason=obstacle_collision:
  collision_count: 208
```

This means the next route should not simply add an offtrack penalty and optimize
return. It needs a route design that explicitly couples offtrack containment
with collision guardrail retention.

## Blocked Shortcuts

M2296 blocks these paths:

- ranking the five profile families from M2293/M2295 aggregates;
- promoting any checkpoint;
- direct PPO or reward repair without a design gate;
- paper-level claim;
- finite-window vs GRU claim;
- level3 self-ID claim.

## Next Route

Pre-register:

```text
m2297-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-route-design
```

M2297 should design the next repair route, not execute it. The route design must
define:

- target offtrack slices from M2295;
- collision guardrail slices from M2295;
- whether the next implementation is artifact target extraction, reward/config
  repair, curriculum/training, or scenario-task reshaping;
- exact pass/fail gates for any later measured execution;
- no actor-input change and no ranking/paper/self-ID claims.

## Claim Boundary

M2296 may claim only that M2295 is accepted as a valid failure-slice diagnosis
and that the next route should be offtrack-primary with collision guardrails.

M2296 cannot claim:

- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.
