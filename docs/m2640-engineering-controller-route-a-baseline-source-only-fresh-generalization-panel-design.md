# M2640 Engineering Controller Route A Baseline Source-Only Fresh Generalization Panel Design

- status: completed
- decision: `route_to_source_only_fresh_generalization_panel_materialization_preflight`
- manifest: `experiments/manifests/m2640-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-design.json`
- parent summary: `runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/summary.json`
- parent evidence index: `runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/evidence_index.csv`
- parent gap matrix: `runs/m2639_engineering_controller_route_a_baseline_evidence_index_refresh/gap_matrix.csv`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2641-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-preflight.json`
- next: `m2641-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-preflight`

## Purpose

M2639 admitted one next evidence-expanding action:

```text
m2640_route_a_source_only_fresh_generalization_panel_design
```

M2640 designs that panel. The panel should move Route A from evidence indexing
back to measured source-only evidence while HF3 selected-platform execution
remains paused at the source dependency boundary.

The design is not a controller ranking, promotion, validation result, or driver
performance claim. It only defines the bounded M2641 materialization preflight.

## Panel Scope

M2641 should extend the M2544 source-only readiness panel in three ways:

```text
1. Add a stable_avoidable role family so Route A covers ordinary stable
   obstacle avoidance, not only stable_aes, drift_required_recovery, and
   unavoidable_mitigation.
2. Use fresh seeds that do not reuse M2544 seed IDs.
3. Add explicit source-only dynamics axes for friction/fault variation and
   actuator delay/noise diagnostics.
```

Bounded panel size:

```text
role_families: 4
fresh_seed_count_per_role: 4
dynamics_axes_per_role_seed: 2
comparison_subjects: 5
horizon_steps: 80
expected_behavior_rows: 160
expected_telemetry_rows: 12800
```

This is large enough to produce fresh measured evidence and small enough to
avoid turning the design into a long benchmark campaign.

## Role Families

M2641 should materialize these role families:

```text
stable_avoidable:
  purpose: ordinary stable avoidance / AEB-feasible proxy
  initial condition: moderate speed, centered lane position, nominal yaw
  obstacle layout: earlier obstacle at avoidable distance, broad clearance
  allowed claim: diagnostic coverage of stable avoidable source-only role

stable_aes:
  purpose: AEB-infeasible stable evasive steering
  source: extends M2496/M2544 stable_aes fixture family
  allowed claim: diagnostic coverage under fresh seeds and variation axes

drift_required_recovery:
  purpose: lateral velocity/yaw recovery under asymmetric or reduced grip
  source: extends M2496/M2544 drift_required_recovery fixture family
  allowed claim: diagnostic coverage of recovery-shaped source-only role

unavoidable_mitigation:
  purpose: unavoidable or near-unavoidable impact mitigation reference
  source: extends M2496/M2544 unavoidable_mitigation fixture family
  allowed claim: diagnostic mitigation evidence surface only
```

Role labels and fixture metadata are diagnostic-only. They must never enter
actor input.

## Fresh Seeds

M2641 should use a new seed namespace:

```text
base_seed: 264100
stable_avoidable: 264100-264103
stable_aes: 265100-265103
drift_required_recovery: 266100-266103
unavoidable_mitigation: 267100-267103
```

Seed rows should include:

```text
seed_panel_id
role_family
seed_index
seed
base_fixture_id
fixture_id
surface_id
role_metadata_only
seed_metadata_only
hidden_diagnostics_metadata_only
actor_input_contract_changed
variant_reason
```

The seeds are for fixture generation and diagnostic lineage only. Seed IDs must
not become actor-visible inputs.

## Dynamics Axes

For each role/seed pair, M2641 should materialize two source-only axes:

```text
fresh_nominal_or_role_default:
  variation: role-appropriate fresh geometry and initial state
  claim boundary: source-only diagnostic role coverage

fresh_fault_delay_noise:
  variation: bounded friction/fault scale perturbation plus actuator delay/noise
  claim boundary: source-only diagnostic robustness coverage
```

Allowed source-only hidden variation ranges for diagnostics:

```text
uniform_grip_scale: [0.62, 1.08]
left_right_split_mu_scale: [0.65, 1.10]
lateral_stiffness_scale: [0.68, 1.10]
brake_scale: [0.72, 1.08]
steering_delay_steps: [0, 2]
throttle_delay_steps: [0, 2]
brake_delay_steps: [0, 2]
sensor_noise_std: [0.0, 0.03]
```

These values may appear in diagnostics and source fixture metadata, but they
must not enter the actor observation. M2641 should include explicit
actor-visibility guard rows proving this.

## Subjects

M2641 should reuse the M2544 subject set:

```text
m1154_original_policy
m2532_guarded_repair_policy
m2537_mitigation_preserving_policy
coast_open_loop
straight_full_brake_open_loop
```

The policy checkpoints are diagnostic subjects only. M2641 must not rank them,
select a winner, promote a checkpoint, or emit success-rate verdict fields.
Open-loop rows remain references, not competitors.

## Metrics

M2641 should reuse the M2514/M2544 behavior/outcome protocol fields and require
complete support for:

```text
contract:
  observation_shape
  action_shape
  actor_contract_id
  actor_input_leak_flags
  action_finite
  action_within_bounds

episode_status:
  episode_started
  episode_completed
  terminal_status
  step_count
  reset_status
  backend_status

avoidance_boundary:
  collision_event
  obstacle_passed_event
  road_departure_event
  minimum_obstacle_clearance_m
  minimum_road_margin_m
  final_road_margin_m

response_recovery:
  maximum_abs_lateral_velocity
  maximum_abs_yaw_rate
  maximum_abs_lateral_position
  final_abs_lateral_velocity
  final_abs_yaw_rate
  recovery_time_proxy_s

actuator_smoothness:
  steering_saturation_fraction
  throttle_saturation_fraction
  brake_saturation_fraction
  command_delta_l1_mean
  simultaneous_throttle_brake_fraction

mitigation:
  collision_speed_proxy
  impact_angle_proxy
  severity_proxy
  mitigation_delta_against_reference
```

M2641 may compute diagnostic aggregates in the materialization summary, but it
must not compute success-rate verdicts, controller-family verdict metrics,
winner fields, or promotion fields.

## Artifact Schema

Required M2641 artifacts:

```text
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/seed_panel_spec.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/subject_registry.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/dynamics_axis_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/actor_visibility_guard_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/telemetry_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_behavior_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_event_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/metric_completeness_rows.csv
runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/gate_matrix.csv
docs/m2641-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-preflight.md
```

## Pass/Fail Gates

M2641 passes only if:

```text
source_artifacts_exist: true
role_family_count: 4
fresh_seed_count_per_role: 4
dynamics_axis_count: 2
comparison_subject_count: 5
expected_behavior_rows: 160
expected_telemetry_rows: 12800
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_detected: false
all_policy_checkpoints_admitted: true
all_actions_finite: true
all_actions_within_bounds: true
all_rows_diagnostic_only_no_ranking_claim: true
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
```

M2641 fails if any diagnostic hidden value, role label, seed, source dependency
status, dynamics axis, reset outcome, rollout outcome, metric label, or route
decision becomes actor-visible.

## Claim Boundary

Allowed claims:

```text
source-only fresh generalization panel materialized
fresh role/seed/dynamics-axis diagnostic rows produced
P0 actor contract preserved
new measured source-only diagnostic evidence available for later audit
```

Rejected claims:

```text
driver performance
deployment readiness
controller ranking
winner selection
checkpoint promotion
success-rate verdict
validation admission
validation result
paper evidence
finite-window-vs-GRU result
current-sim verdict
high-fidelity validation readiness or result
level3 self-identification
full ideal driver completion
```

M2640 executes no policy actions, environment steps, rollouts, replay,
validation, training, source build, adapter probe, external simulation, ranking,
winner selection, or promotion. Those remain M2641 materialization boundaries.
