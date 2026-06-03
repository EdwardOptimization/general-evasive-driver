# M2515 Engineering Controller Behavior/Outcome Protocol Materialization Result Audit

- status: completed
- decision: `accept_protocol_materialization_route_to_source_only_row_completeness_preflight`
- manifest: `experiments/manifests/m2515-engineering-controller-behavior-outcome-protocol-materialization-result-audit.json`
- audited summary: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json`
- audited protocol schema: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/protocol_schema.json`
- audited row schema: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv`
- audited metric registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv`
- audited audit gate registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/audit_gate_registry.csv`
- audited layer registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/layer_registry.csv`
- audited forbidden registry: `runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/forbidden_registry.csv`
- next milestone: `m2516-engineering-controller-source-only-behavior-outcome-row-completeness-preflight`
- external high-fidelity simulation installed/imported/executed in M2515: `false`
- environment rollout/simulator step/policy rollout in M2515: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2515: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Audit Decision

M2515 accepts M2514 as a valid no-rollout materialization of the
engineering-controller behavior/outcome protocol.

Accepted summary:

```text
result_class: engineering_controller_behavior_outcome_protocol_materialization_pass
status_pass: true
protocol_version: engineering_controller_behavior_outcome_v0
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

Artifact counts:

```text
row_schema_field_count: 51
metric_registry_row_count: 40
audit_gate_count: 15
layer_registry_count: 3
forbidden_registry_row_count: 39
taxonomy_row_count: 10
```

## Artifact Audit

Required artifacts exist:

```text
summary.json: present
protocol_schema.json: present
row_schema.csv: present
metric_registry.csv: present
audit_gate_registry.csv: present
layer_registry.csv: present
forbidden_registry.csv: present
```

The protocol schema preserves:

```text
actor_contract_id: P0_human_view_72_action_3_no_oracle
observation_shape: 72
action_shape: 3
actor_encoder: human_view_online_gru
action_horizon: 1
no_hidden_oracle_actor_inputs: true
```

The row schema includes evaluator-side fields for:

```text
identity
evidence layer
scenario role metadata
actor contract
episode status
action gates
avoidance/boundary metrics
response/recovery metrics
actuator/smoothness metrics
mitigation metrics
metric completeness flags
claim scope
forbidden interpretation
source artifact
```

## Layer Separation Audit

M2514 encodes the required layer split:

```text
source_only_diagnostic:
  permitted_now: true
  allowed claim: diagnostic behavior instrumentation only
  forbidden interpretation: driver performance or scenario generalization

current_sim_diagnostic_mining:
  permitted_now: false
  requires_future_manifest: true
  forbidden interpretation: current-sim benchmark readiness

future_high_fidelity_validation:
  permitted_now: false
  requires_future_manifest: true
  forbidden interpretation: high-fidelity validation readiness
```

This satisfies the M2513/M2514 requirement that source-only rows cannot be used
as high-fidelity validation evidence and current-sim diagnostics cannot be used
as current-sim benchmark readiness.

## Forbidden Registry Audit

The forbidden registry includes actor-input guards for:

```text
mu
mass
inertia
cg_shift
tire_stiffness
brake_scale
drive_scale
actuator_tau
slip
tire_force
controller_mode
scenario_role
speed_ref
beta_target
path_error
heading_error
path_curvature
ttc
required_clearance
oracle_stopping_distance
oracle_feasibility
aeb_aes_drift_labels
reward_terms
progress_counters
collision_labels
success_labels
```

It includes outcome-shortcut guards for:

```text
single_scalar_driver_score
mixed_role_success_rate_aggregate
controller_ranking
winner_selection
scenario_generalization_from_fixed_public_fixtures
current_sim_benchmark_verdict_from_source_only_rows
high_fidelity_validation_readiness_from_source_only_rows
paper_level_claim_from_engineering_diagnostics
finite_window_vs_gru_conclusion
level3_self_identification_conclusion
manual_rule_switch_labels_as_acceptance
precomputed_avoidance_progress_labels_as_success
```

These guards are adequate for admitting a source-only row-completeness preflight.
They are not adequate for behavior verdicts, controller ranking, high-fidelity
validation, or paper claims.

## Audit Gate Registry

The materialized audit gate registry covers:

```text
pre-execution:
  actor_contract_72_3
  no_hidden_oracle_actor_inputs
  protocol_layer_present
  scenario_role_metadata_only
  row_schema_complete
  metric_registry_complete
  forbidden_registry_complete
  layer_separation_preserved

future execution:
  all_attempted_rows_retained
  reset_vs_behavior_failure_split
  metric_completeness_per_row
  same_case_denominators
  no_ranking_or_winner_fields

claim:
  source_only_diagnostic_claim_only
  hf_validation_requires_later_audit
```

M2515 accepts these gates as sufficient for a no-rollout source-only row
completeness preflight over existing artifacts.

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

## Failure Taxonomy

Controlled:

```text
contract_violation:
  controlled by actor_contract_72_3 and no_hidden_oracle_actor_inputs gates.

lineage_invalid:
  controlled by source_artifact fields and all required artifact presence.

metric_artifact:
  controlled by row_schema, metric_registry, audit_gate_registry, and
  forbidden_registry artifacts.

validation_boundary:
  controlled for this audit by layer separation and forbidden validation
  overclaim registry rows.
```

Unresolved:

```text
behavior_regression:
  unresolved. The protocol is ready to check row completeness, but no measured
  behavior has been executed or audited.

scenario_sampling_failure:
  unresolved. Source-only fixed fixtures and current-sim readiness limits
  remain outside this audit.

objective_overfit:
  reduced but not resolved. The next route should avoid another schema-only
  artifact and instead check completeness against existing source-only rows.
```

## Route Decision

M2515 routes to:

```text
m2516-engineering-controller-source-only-behavior-outcome-row-completeness-preflight
```

M2516 should use existing source-only artifacts to materialize a bounded row
completeness panel against the M2514 schema. It should not execute new policy
actions, step a simulator, train, rank controllers, select a winner, compute
success-rate verdicts, or claim driver performance. Its only permitted claim is
whether existing source-only artifacts can populate the protocol rows and which
metric gaps remain explicit.
