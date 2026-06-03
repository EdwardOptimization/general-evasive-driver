# M2514 Engineering Controller Behavior/Outcome Protocol Materialization Preflight

- status: completed
- result_class: `engineering_controller_behavior_outcome_protocol_materialization_pass`
- manifest: `experiments/manifests/m2514-engineering-controller-behavior-outcome-protocol-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_behavior_outcome_protocol.py`
- summary: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json`
- protocol schema: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/protocol_schema.json`
- row schema: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv`
- metric registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv`
- audit gate registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/audit_gate_registry.csv`
- layer registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/layer_registry.csv`
- forbidden registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/forbidden_registry.csv`
- next milestone: `m2515-engineering-controller-behavior-outcome-protocol-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed in M2514: `false`
- environment rollout/simulator step/policy rollout in M2514: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2514: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Materialized Artifacts

M2514 materializes the M2513 evaluator-side behavior/outcome protocol as
machine-readable no-rollout artifacts. It does not run a simulator, step an
environment, execute a policy action, or compute behavior results.

Generated artifacts:

```text
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/protocol_schema.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/audit_gate_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/layer_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/forbidden_registry.csv
```

Protocol identity:

```text
protocol_version: engineering_controller_behavior_outcome_v0
claim_scope: no-rollout engineering-controller behavior/outcome protocol materialization
actor_contract_id: P0_human_view_72_action_3_no_oracle
observation/action: 72 / 3
actor_encoder: human_view_online_gru
action_horizon: 1
```

## Summary Gates

Accepted summary:

```text
result_class: engineering_controller_behavior_outcome_protocol_materialization_pass
status_pass: true
required_artifacts_present: true
source_artifacts_exist: true
missing_source_artifacts: []
actor_contract_shape_72_action_3: true
no_hidden_oracle_actor_inputs_encoded: true
forbidden_actor_inputs_encoded: true
forbidden_outcome_shortcuts_encoded: true
claim_boundary_encoded: true
layer_registry_contains_required_layers: true
source_only_layer_separated_from_validation: true
no_rollout_scope: true
```

Artifact sizes:

```text
row_schema_field_count: 51
metric_registry_row_count: 40
audit_gate_count: 15
layer_registry_count: 3
forbidden_registry_row_count: 39
taxonomy_row_count: 10
```

The materialized protocol preserves the M2513 layer split:

```text
source_only_diagnostic
current_sim_diagnostic_mining
future_high_fidelity_validation
```

Only `source_only_diagnostic` is permitted immediately, and only for diagnostic
behavior instrumentation. The current-sim and high-fidelity layers require
future manifests before use.

## Row Schema And Metric Registry

The row schema defines the fields future behavior/outcome rows must carry:

```text
identity fields:
  protocol_version milestone_id run_id row_id

layer and metadata fields:
  evidence_layer surface_id scenario_role fixture_id seed subject_id checkpoint_path

actor contract fields:
  actor_contract_id observation_shape action_shape actor_encoder action_horizon actor_input_leak_flags

episode and action fields:
  reset_status backend_status episode_started episode_completed step_count terminal_status action_finite action_within_bounds

outcome and response fields:
  collision_event obstacle_passed_event road_departure_event
  minimum_obstacle_clearance_m minimum_road_margin_m final_road_margin_m
  maximum_abs_lateral_velocity maximum_abs_yaw_rate maximum_abs_lateral_position
  final_abs_lateral_velocity final_abs_yaw_rate recovery_time_proxy_s

actuator and mitigation fields:
  steering_saturation_fraction throttle_saturation_fraction brake_saturation_fraction
  command_delta_l1_mean simultaneous_throttle_brake_fraction
  collision_speed_proxy impact_angle_proxy severity_proxy mitigation_delta_against_reference

claim boundary fields:
  metric_completeness_flags diagnostic_only_no_ranking_claim claim_scope forbidden_interpretation source_artifact
```

The metric registry records contract, episode status, avoidance/boundary,
response/recovery, actuator/smoothness, mitigation, and metadata/completeness
metric families. Non-contract metrics require a future manifest before they can
support any claim.

## Audit Gates

The audit gate registry contains pre-execution gates:

```text
actor_contract_72_3
no_hidden_oracle_actor_inputs
protocol_layer_present
scenario_role_metadata_only
row_schema_complete
metric_registry_complete
forbidden_registry_complete
layer_separation_preserved
```

It also defines future execution and claim gates:

```text
all_attempted_rows_retained
reset_vs_behavior_failure_split
metric_completeness_per_row
same_case_denominators
no_ranking_or_winner_fields
source_only_diagnostic_claim_only
hf_validation_requires_later_audit
```

These gates are protocol guardrails. M2514 itself does not execute rows or
audit measured behavior.

## Forbidden Registry

The forbidden registry encodes both forbidden actor inputs and forbidden
outcome shortcuts.

Actor-input examples:

```text
mu
mass
tire_stiffness
actuator_tau
slip
tire_force
controller_mode
speed_ref
beta_target
path_error
heading_error
path_curvature
ttc
required_clearance
oracle_stopping_distance
oracle_feasibility
collision_labels
success_labels
```

Outcome shortcut examples:

```text
single_scalar_driver_score
mixed_role_success_rate_aggregate
controller_ranking
winner_selection
current_sim_benchmark_verdict_from_source_only_rows
high_fidelity_validation_readiness_from_source_only_rows
paper_level_claim_from_engineering_diagnostics
finite_window_vs_gru_conclusion
level3_self_identification_conclusion
```

## Blocked Execution And Claim Flags

```text
environment_rollout_run: false
simulator_step_run: false
external_high_fidelity_simulation_included: false
policy_action_run: false
policy_rollout_run: false
measured_validation_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
controller_family_verdict_computed: false
driver_performance_claim_made: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Result

M2514 passes as a no-rollout protocol materialization preflight. It turns the
M2513 behavior/outcome design into schema and registry artifacts that can be
audited before any measured behavior execution.

It still does not prove driver behavior, behavior regression, success rate,
controller ranking, high-fidelity validation, paper evidence, or
self-identification.

## Next Route

Route to:

```text
m2515-engineering-controller-behavior-outcome-protocol-materialization-result-audit
```

M2515 should audit the summary, schema, registries, layer separation, forbidden
registry, actor contract, and false claim flags before any source-only row
completeness preflight or measured behavior route.
