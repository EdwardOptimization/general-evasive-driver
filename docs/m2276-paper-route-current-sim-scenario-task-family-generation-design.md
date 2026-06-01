# M2276 Paper-Route Current-Sim Scenario Task-Family Generation Design

- status: completed
- decision: `current_sim_scenario_task_family_generation_design_admit_config_materialization`
- manifest: `experiments/manifests/m2276-paper-route-current-sim-scenario-task-family-generation-design.json`
- parent audit: `docs/m2275-paper-route-current-sim-scenario-task-quality-support-audit-result-audit.md`
- next route: `m2277-paper-route-current-sim-scenario-task-family-config-materialization`

## Purpose

M2276 turns the M2274/M2275 support gaps into an executable, no-rollout
scenario-generation design. It does not run reset, rollout, measured execution,
training, replay, PPO, private holdout, promotion, controller ranking,
finite-window-vs-GRU verdicts, paper-level claims, or level3 self-ID claims.

The next evidence axis is:

```text
role-supported current-sim task-quality benchmark pack
```

This is a prerequisite before comparing driver profiles or training another
policy on the current-sim paper route.

## Semantic Correction

M2274 correctly found that the current artifacts have incomplete role and
scenario-axis support, but M2276 should not propagate its provisional
`aes_feasible -> R0` role mapping.

The simulator classifier semantics are:

```text
aeb_feasible:
  pure braking is feasible before the obstacle

aes_feasible:
  pure braking is not feasible, but conventional stable lateral avoidance is
  feasible

drift_required:
  conventional stable lateral avoidance is not enough, but a handling-limit or
  drift-like maneuver may be feasible

unavoidable:
  neither braking nor modeled lateral capability clears the obstacle
```

Therefore the M2277 materializer must use this corrected role mapping:

```text
R0_stable_avoidable:
  aeb_feasible

R1_aeb_infeasible_stable_aes:
  aes_feasible

R2_handling_limit_drift_capable_avoidance:
  drift_required

R3_recovery_after_limit:
  explicit recovery-after-limit scenario metadata, not a classifier shortcut

R4_unavoidable_mitigation:
  unavoidable

R5_hidden_dynamics_robustness:
  same-scene hidden-dynamics bundles, not a deployable actor input
```

With this correction, the old three-panel rows already contain R1 support via
`aes_feasible`, while R0 remains missing in those rows. The branch conclusion is
unchanged: the current artifacts are not yet a role-supported benchmark pack.

## Generation Targets

M2277 should materialize a public diagnostic v0 pack with:

```text
role families: 6
minimum scenario specs per role: 12
minimum total scenario specs: 72
minimum timing buckets per applicable role: 3
minimum lateral buckets per applicable role: 3
minimum hidden-dynamics buckets in R5: 4
ranking admissible by default: false
private holdout used: false
```

These are spec/materialization targets, not rollout episode counts. Future
rollout/training claims still require the M2273 readiness floors:

```text
>= 64 public diagnostic episodes per active role
>= 3 profile_seed groups per active role before profile-level claims
>= 95% role-family label completeness
>= 90% required scenario-axis completeness
```

## Role-Family Construction

M2277 should define every row with both a human-readable role and the simulator
mechanism used to sample it:

| role | generation mechanism | required metadata |
| --- | --- | --- |
| `R0_stable_avoidable` | obstacle labels restricted to `aeb_feasible` | braking-feasible role, stable baseline |
| `R1_aeb_infeasible_stable_aes` | obstacle labels restricted to `aes_feasible` | AEB-infeasible, stable AES feasible |
| `R2_handling_limit_drift_capable_avoidance` | obstacle labels restricted to `drift_required` | handling-limit avoidance role |
| `R3_recovery_after_limit` | high-yaw/high-sideslip-capable obstacle rows with `finish_on_pass=false` and a post-obstacle recovery window | recovery-window role, recovery horizon |
| `R4_unavoidable_mitigation` | obstacle labels restricted to `unavoidable` | mitigation role, impact metrics required |
| `R5_hidden_dynamics_robustness` | same scene templates crossed with hidden dynamics buckets | same-scene group id, hidden dynamics bucket |

R3 and R5 are explicit task families, not deployable actor inputs. Their labels
may appear in configs, diagnostics, corpus mining, and evaluation artifacts
only.

## Required Metadata Schema

Every materialized scenario spec and every derived config row must carry these
fields:

```text
scenario_spec_id
scenario_family_id
role_family
role_semantics
sampled_obstacle_label
allowed_labels_metadata_only
labels_enter_actor_input
same_scene_group_id
obstacle_longitudinal_distance_m
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_m
obstacle_lateral_offset_bucket
obstacle_half_width_m
initial_speed_mps
initial_speed_bucket
track_kind
track_radius_m
track_width_m
road_curvature_bucket
friction_bucket
mu_range
brake_scale_bucket
brake_scale_range
actuator_lag_bucket
steer_tau_scale_range
drive_tau_scale_range
vehicle_mass_or_inertia_bucket
mass_scale_range
inertia_scale_range
tire_stiffness_bucket
front_tire_stiffness_scale_range
rear_tire_stiffness_scale_range
recovery_window_s
recovery_window_bucket
finish_on_pass
obstacle_relative_velocity_mode
wheel_observation_mode
include_privileged_params
history_length
actor_contract_id
diagnostic_only_no_ranking_claim
ranking_admissible
paper_level_claim_made
level3_self_id_claim_made
env_config
```

Required fixed actor-contract values:

```text
labels_enter_actor_input: false
obstacle_relative_velocity_mode: zero
wheel_observation_mode: none
include_privileged_params: false
history_length: 1
actor_contract_id: P0_human_view_no_wheel_no_oracle
diagnostic_only_no_ranking_claim: true
ranking_admissible: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

The schema may include hidden dynamics values because they are generation and
logging metadata. They must not enter actor observations.

## Timing And Lateral Axes

M2277 must represent timing and lateral geometry directly, not infer them from
rollout state after the fact.

Timing buckets:

```text
early_far
mid
late_close
```

These should be materialized through obstacle distance ranges coupled with the
scenario speed range. The actor does not receive the timing bucket or TTC.

Lateral buckets:

```text
centerline
left_offset
right_offset
```

Current emergency obstacles are centerline-only unless the simulator is extended
with an `obstacle.lateral_offset_range` field. M2277 must not silently
approximate lateral diversity with ego-state drift or road-frame artifacts. It
has two admissible choices:

```text
1. add a backward-compatible obstacle.lateral_offset_range field with default
   (0.0, 0.0), test it, and materialize left/center/right configs; or

2. report lateral-offset rows as unsupported capability rows and route to an
   instrumentation extension before any reset/rollout.
```

The first choice is preferred if it stays limited to simulator
instrumentation, preserves the actor contract, and remains no-rollout in M2277.

## Recovery Axis

The recovery window is an evaluation contract, not an actor input. R3 specs and
any handling-limit specs that require recovery should include:

```text
finish_on_pass: false
recovery_window_s: 1.0 to 3.0
recovery_window_bucket: short / medium / long
```

Future execution must compute recovery metrics after the obstacle zone. M2277
only materializes the metadata and config values.

## Hidden-Dynamics Axis

R5 must be a same-scene robustness family:

```text
same_scene_group_id:
  shared road, speed, obstacle timing, obstacle lateral offset, obstacle size

hidden_dynamics_bucket:
  nominal
  low_mu
  weak_brake
  slow_steer_actuator
  high_mass_or_inertia
  tire_stiffness_shift
```

The first M2277 v0 pack needs at least four hidden-dynamics buckets. More can be
added later, but not at the cost of hiding unsupported simulator capability.

## Unsupported Extreme Faults

The current single-track simulator should not pretend to cover wheel-specific or
driveline-specific failures. M2277 should preserve an explicit unsupported
capability table for:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
sensor_dropout_or_bias
```

These are valuable future scenario families for a higher-fidelity simulator, but
they are not current-sim v0 claims.

## M2277 Outputs

M2277 should be an infrastructure/materialization milestone and write:

```text
configs/paper_route_current_sim_scenario_task_family_v0.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/summary.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/scenario_family_specs.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/scenario_family_specs.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/materialized_config_matrix.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/metadata_schema.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/role_family_support_targets.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/unsupported_capability_rows.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/claim_boundary.csv
```

M2277 should also add focused tests for the materializer and any simulator
instrumentation it needs.

## Acceptance Gates

M2277 can pass as no-rollout materialization if:

```text
scenario_family_count == 6
scenario_spec_count >= 72
min_specs_per_role >= 12
metadata_missing_required_field_count == 0
duplicate_scenario_spec_id_count == 0
labels_enter_actor_input_count == 0
actor_contract_violation_count == 0
ranking_admissible_count == 0
winner_selected == false
training_started == false
environment_reset_started == false
environment_rollout_started == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If lateral offset or any other required axis is unsupported, M2277 may still
pass as an honest materialization preflight only if the unsupported rows are
explicitly reported and the next route is instrumentation repair, not execution
or ranking.

## Blocked Routes

Blocked after M2276:

```text
new rollout before M2277 materialization and M2278 audit
training before role-supported configs are materialized and audited
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as the primary route
silent approximation of unsupported fault modes
using role labels or hidden dynamics as deployable actor inputs
```

## Next

Pre-register:

```text
m2277-paper-route-current-sim-scenario-task-family-config-materialization
```
