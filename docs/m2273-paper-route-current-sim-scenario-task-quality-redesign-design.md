# M2273 Paper-Route Current-Sim Scenario/Task-Quality Redesign Design

- status: completed
- decision: `current_sim_scenario_task_quality_redesign_design_admit_support_audit`
- manifest: `experiments/manifests/m2273-paper-route-current-sim-scenario-task-quality-redesign-design.json`
- next artifact route: `m2274-paper-route-current-sim-scenario-task-quality-support-audit-implementation`

## Purpose

M2273 starts the branch selected by M2272:

```text
paper_route_current_sim_scenario_task_quality_redesign
```

The purpose is to define a paper-relevant current-sim benchmark pack before any
new rollout, training, measured execution, or controller-family ranking. This
milestone is design-only. It does not change reward scalars or start another
training run.

## Role-Specific Task Families

Future current-sim task quality should be organized by role, not only by
aggregate success/offtrack/collision:

```text
R0_stable_avoidable:
  The obstacle is avoidable by stable steering/braking without requiring
  handling-limit yaw or drift. This is the baseline AES role.

R1_aeb_infeasible_stable_aes:
  Pure AEB is insufficient, but stable AES should still avoid the obstacle
  without large sideslip or road departure.

R2_handling_limit_drift_capable_avoidance:
  Stable AES is not enough or has low margin. A successful driver may need
  high yaw authority, transient oversteer, or drift-like motion, followed by
  recovery.

R3_recovery_after_limit:
  The main task is not only first obstacle avoidance but post-maneuver
  recovery: stay on road, reduce sideslip, and avoid secondary departure.

R4_unavoidable_mitigation:
  Collision may be unavoidable under current geometry/dynamics. The role is to
  reduce impact speed, impact angle, or secondary road departure rather than to
  count all failures equally.

R5_hidden_dynamics_robustness:
  Same scene family under varied friction, brake scale, actuator lag, vehicle
  mass/inertia, or tire scale. This is task-quality support for later
  self-ID/finite-window tests, not itself a level3 self-ID claim.
```

These labels may be used by scenario generation, diagnostics, teachers,
miners, and evaluation. They must not enter the deployable actor input.

## Scenario Axes

The support audit and future redesign should track at least these axes:

```text
initial_speed_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
road_width_bucket
road_curvature_bucket
friction_bucket
brake_scale_bucket
actuator_lag_bucket
vehicle_mass_or_inertia_bucket
recovery_window_bucket
role_family
```

The first artifact-only audit may find that current episode rows do not contain
enough columns to infer all buckets. That should be reported as a support gap,
not patched by guessing.

## Metrics

Primary role metrics:

```text
success_rate
collision_rate
offtrack_rate
spin_or_high_sideslip_rate
clearance_margin_tail
impact_speed_or_mitigation_proxy
recovery_success_rate
post_maneuver_stability_rate
control_smoothness
role_completion_rate
```

Diagnostic metrics:

```text
termination_reason_histogram
offtrack_timing_bucket
offtrack_severity_bucket
clearance_risk_bucket
profile_seed_stability
scenario_axis_coverage
max_source_dominance
missing_label_rate
```

Mechanism metrics such as wrong-history degradation, reset-hidden degradation,
finite-window-vs-GRU deltas, and history intervention margins remain blocked
until a role-supported benchmark pack exists.

## Readiness Floors

M2273 does not declare the current panel ready. It freezes candidate future
readiness floors for the support audit to assess feasibility:

```text
support completeness:
  role_family present or inferable for >= 95% of rows
  required scenario axes present or inferable for >= 90% of rows
  each active role has >= 64 public diagnostic episodes before training claims
  each active role has >= 3 profile_seed groups before profile-level claims

outcome quality:
  collision does not increase when repairing offtrack
  offtrack does not improve only by increasing collision
  success/mitigation metrics are reported per role, not only globally

comparison readiness:
  no controller-family ranking until role support is complete
  no finite-window-vs-GRU conclusion until L0/L1/L2/L3 are evaluated under the
  same role distribution, budget, and actor contract

self-ID readiness:
  no level3 self-ID claim until source-diverse role-supported history
  interventions affect terminal outcome, not only action or aggregate return
```

These are audit targets, not current claims.

## M2274 Artifact-Only Support Audit

M2274 should implement an artifact-only audit over existing current-sim rows and
configs. It should not run reset, rollout, measured execution, training, replay,
PPO, or private holdout.

Inputs:

```text
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2227_paper_route_current_sim_matched_budget_profile_training_configs/training_matrix.csv
runs/m2233_paper_route_current_sim_matched_budget_medium_training_configs/training_matrix.csv
runs/m2248_paper_route_current_sim_offtrack_recovery_corridor_reward_extension_materialization/training_matrix.csv
runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv
```

Required outputs:

```text
summary.json
role_support.csv
scenario_axis_support.csv
metric_coverage.csv
readiness_floor_gap.csv
support_gap_report.csv
redesign_routes.csv
```

The audit should answer:

```text
Can existing artifacts support role-specific task labels?
Which axes are present, inferable, missing, or unsafe to infer?
Which role families are under-supported?
Which metrics can be computed now without rerun?
What scenario/task redesign is needed before training?
```

## Blocked Shortcuts

Blocked:

```text
reward scalar tuning before support audit
new rollout before support audit
training before role/floor design
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as the primary route
```

## Next

Pre-register:

```text
m2274-paper-route-current-sim-scenario-task-quality-support-audit-implementation
```
