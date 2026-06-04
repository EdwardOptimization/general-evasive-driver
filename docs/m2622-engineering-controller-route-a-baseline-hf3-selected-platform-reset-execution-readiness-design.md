# M2622 Engineering Controller Route A Baseline HF3 Selected-Platform Reset-Execution Readiness Design

- status: completed
- decision: `route_to_hf3_selected_platform_reset_execution_readiness_materialization_preflight`
- manifest: `experiments/manifests/m2622-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-design.json`
- parent synthesis: `docs/m2621-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-result-synthesis.md`
- parent audit: `docs/m2620-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-preflight.json`
- next: `m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-preflight`

## Design Verdict

M2622 designs the bounded artifacts required to represent selected-platform
reset-execution readiness for
`chrono_vehicle_or_equivalent_open_backend`. M2623 should materialize source
build and adapter probe evidence admission, backend availability fixture, reset
invocation dry-run contract, reset request binding, actor-view after-reset
extraction, reset outcome audit schema, reset-execution actor/action guard,
claim-boundary, and gate rows.

This design is still pre-execution. It does not install or import external
simulation dependencies, mutate dependencies, run source builds, run adapter
probes, execute resets, execute policy actions, step environments, execute
rollouts, execute replay, execute validation, train, rank controllers, promote
checkpoints, compute success rates, or claim driver performance.

If M2623 passes all gates, the allowed claim is limited to selected-platform
reset-execution readiness design artifacts materialized. That would still not
imply source-build execution, adapter-probe execution, reset execution, reset
success, rollout feasibility, validation protocol readiness, validation
admission, high-fidelity validation readiness, validation result, current-sim
verdict, paper-level evidence, finite-window-vs-GRU evidence, level3 self-ID,
or professional driver behavior.

## Source Evidence

Accepted selected-platform reset-feasibility readiness boundary:

```text
M2621 synthesis decision: continue_to_hf3_selected_platform_reset_execution_readiness_design
M2620 audit decision: accept_hf3_selected_platform_reset_feasibility_readiness_materialization_route_to_result_synthesis
M2619 status_pass: true
reset request schema rows: 2/2 pass
initial-state admission rows: 2/2 pass
actor-view parity rows: 2/2 pass
reset seed/lineage rows: 2/2 pass
reset outcome taxonomy guard rows: 8/8 pass
reset-execution precondition rows: 6/6 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 27/27 pass
materialization gates: 13/13 pass
selected_platform_family_in_m2619: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2619: false
external_import_allowed_in_m2619: false
runtime_execution_allowed_in_m2619: false
dependency_mutation_allowed_in_m2619: false
source_build_executed_in_m2619: false
adapter_probe_executed_in_m2619: false
reset_executed_in_m2619: false
environment_step_executed_in_m2619: false
policy_action_executed_in_m2619: false
rollout_executed_in_m2619: false
replay_executed_in_m2619: false
external_validation_execution_allowed_in_m2619: false
validation_protocol_ready_in_m2619: false
validation_admission_granted_in_m2619: false
validation_result_claim_allowed: false
reset_success_claim_allowed_in_m2619: false
rollout_feasibility_claim_allowed_in_m2619: false
driver_performance_claim_allowed_in_m2619: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, keep
current-sim diagnostic-only, prefer an open/auditable high-fidelity vehicle
dynamics layer, and use HF3 as reset/rollout feasibility only without a
controller-family verdict.

The paper-governing route remains unchanged. Self-ID and GRU advantage are
bounded hypotheses. Reset-execution readiness rows are validation-layer
preparation, not current-sim verdict, paper evidence, finite-window-vs-GRU
evidence, or level3 self-identification evidence.

## M2623 Artifact Contract

M2623 should write:

```text
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/summary.json
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_source_build_adapter_probe_evidence_admission_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_backend_availability_fixture_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_invocation_dry_run_contract_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_request_binding_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_actor_view_after_reset_extraction_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_outcome_audit_schema_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_actor_action_guard_rows.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/hf3_selected_platform_reset_execution_readiness_claim_boundary_checks.csv
runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/selected_platform_reset_execution_readiness_gate_matrix.csv
docs/m2623-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-preflight.md
```

Every M2623 row should prove selected-platform reset-execution readiness design
artifacts only. Rows must keep:

```text
selected_platform_reset_execution_readiness_design_materialized_in_m2623: true
selected_platform_family_in_m2623: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2623: false
external_import_allowed_in_m2623: false
runtime_execution_allowed_in_m2623: false
dependency_mutation_allowed_in_m2623: false
source_build_executed_in_m2623: false
adapter_probe_executed_in_m2623: false
reset_executed_in_m2623: false
environment_step_executed_in_m2623: false
policy_action_executed_in_m2623: false
rollout_executed_in_m2623: false
replay_executed_in_m2623: false
external_validation_execution_allowed_in_m2623: false
validation_protocol_ready_in_m2623: false
validation_admission_granted_in_m2623: false
validation_result_claim_allowed: false
reset_success_claim_allowed_in_m2623: false
rollout_feasibility_claim_allowed_in_m2623: false
driver_performance_claim_allowed_in_m2623: false
```

## Source-Build And Adapter-Probe Evidence Admission Rows

M2623 should write source-build and adapter-probe evidence admission rows:

```text
evidence_admission_id
evidence_family
selected_platform_family
required_before_reset_execution
materialized_in_m2623
satisfied_by_m2623
execution_allowed_in_m2623
source_build_execution_required_later
adapter_probe_execution_required_later
dependency_mutation_allowed_in_m2623
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `source_build_log_admission`
- `adapter_probe_trace_admission`
- `dependency_mutation_guard_admission`
- `source_equivalence_trace_admission`

Pass criteria:

- exactly four rows exist
- all rows are audit metadata and not actor-visible
- source-build and adapter-probe execution remain future prerequisites
- dependency mutation and execution are false in M2623

## Backend Availability Fixture Rows

M2623 should write backend availability fixture rows:

```text
backend_fixture_id
route_role_id
selected_platform_family
backend_family
fixture_family
backend_availability_required_before_reset
fixture_schema_materialized_in_m2623
backend_started_in_m2623
backend_reset_called_in_m2623
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_backend_availability_fixture`
- `stable_aes_aeb_infeasible_backend_availability_fixture`

Pass criteria:

- exactly two rows exist
- backend availability is represented as a future fixture contract only
- backend start and reset calls are false in M2623
- fixture metadata is not actor-visible

## Reset Invocation Dry-Run Contract Rows

M2623 should write reset invocation dry-run contract rows:

```text
dry_run_contract_id
route_role_id
selected_platform_family
reset_api_family
initial_state_binding_required
deterministic_seed_required
actor_view_required_after_reset
source_build_required_before_execution
adapter_probe_required_before_execution
backend_availability_required_before_execution
reset_invocation_contract_materialized_in_m2623
reset_executed_in_m2623
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_invocation_dry_run_contract`
- `stable_aes_aeb_infeasible_reset_invocation_dry_run_contract`

Pass criteria:

- exactly two rows exist
- source build, adapter probe, and backend availability remain prerequisites
- reset execution is false in M2623

## Reset Request Binding Rows

M2623 should write reset request binding rows:

```text
reset_request_binding_id
route_role_id
selected_platform_family
reset_request_schema_id
initial_state_admission_id
seed_lineage_id
binding_materialized_in_m2623
reset_executed_in_m2623
replay_executed_in_m2623
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_request_binding`
- `stable_aes_aeb_infeasible_reset_request_binding`

Pass criteria:

- exactly two rows exist
- bindings reference the M2619 reset request, initial-state, and seed/lineage
  rows
- reset and replay execution are false in M2623
- binding metadata is not actor-visible

## Actor-View After-Reset Extraction Rows

M2623 should write actor-view after-reset extraction rows:

```text
after_reset_actor_view_id
route_role_id
selected_platform_family
actor_observation_shape
action_shape
deployed_action_mapping
ego_kinematics_included
actuator_state_included
previous_command_included
road_geometry_included
obstacle_geometry_included
after_reset_extractor_contract_materialized_in_m2623
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
validation_outcome_actor_visible
selected_platform_actor_visible
protocol_status_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- observation shape is `72` and action shape is `3`
- deployed action mapping remains `[steer, throttle, brake]`
- actor-visible features remain deployable P0 information only
- hidden/oracle inputs, diagnostics, labels, backend status, reset outcome,
  validation outcome, selected platform, and protocol status are false

## Reset Outcome Audit Schema Rows

M2623 should write reset outcome audit schema rows:

```text
outcome_audit_schema_id
outcome_field
field_family
required_for_future_reset_execution_audit
allowed_to_support_reset_success_after_execution
allowed_to_support_rollout_feasibility_after_execution
allowed_to_support_validation_after_execution
actor_visible_allowed
materialized_in_m2623
status_pass
claim_boundary
```

Required outcome fields:

- `backend_available`
- `source_build_artifact`
- `adapter_probe_trace`
- `reset_request_valid`
- `reset_attempted`
- `reset_status`
- `actor_view_available`
- `diagnostics_available`
- `failure_reason`
- `execution_timestamp`

Pass criteria:

- all required outcome fields are present
- no outcome field is actor-visible
- outcome fields are schema only and do not claim reset success in M2623
- validation support remains future-only and execution-dependent

## Reset-Execution Actor/Action Guard Rows

M2623 should write actor/action guard rows:

```text
actor_action_guard_id
route_role_id
actor_observation_shape
action_shape
deployed_action_mapping
actor_input_mutation_detected
action_contract_mutation_detected
hidden_oracle_actor_input_detected
metadata_actor_visible
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_execution_actor_action_guard`
- `stable_aes_aeb_infeasible_reset_execution_actor_action_guard`

Pass criteria:

- exactly two rows exist
- P0 `72/3` is preserved
- deployed action mapping remains `[steer, throttle, brake]`
- no actor input or action contract mutation is detected
- no hidden/oracle or metadata actor input is visible

## Claim-Boundary Rows

M2623 should write claim-boundary rows for these claim families:

```text
selected_platform_reset_execution_readiness_design_materialized
dependency_ready_for_execution
source_build_executed
adapter_probe_executed
reset_executed
reset_success
policy_action_executed
environment_step_executed
rollout_executed
rollout_feasibility
replay_executed
validation_protocol_readiness
validation_admission
external_validation_execution
validation_readiness
validation_result
high_fidelity_validation_readiness
high_fidelity_validation_result
driver_performance
controller_family_ranking
winner_selection
success_rate
checkpoint_promotion
current_sim_verdict
paper_level_evidence
finite_window_vs_gru
level3_self_identification
```

Only `selected_platform_reset_execution_readiness_design_materialized` may be
true in M2623. All other claim families must be false.

## Gate Matrix

M2623 should write a gate matrix with these gates:

```text
source_artifacts_exist
m2619_m2620_m2621_reset_feasibility_readiness_evidence_accepted
source_build_adapter_probe_evidence_admission_rows_pass
backend_availability_fixture_rows_pass
reset_invocation_dry_run_contract_rows_pass
reset_request_binding_rows_pass
actor_view_after_reset_extraction_rows_pass
reset_outcome_audit_schema_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
no_build_probe_reset_step_action_rollout_replay_or_validation_execution
reset_success_rollout_validation_and_performance_forbidden
actor_action_contract_preserved
```

M2623 should pass only if all gates pass and the only supported claim is static
selected-platform reset-execution readiness design materialization.

## Supported Claims After M2622

Supported:

- selected-platform reset-execution readiness design artifacts are specified
- M2623 materialization artifacts, row schemas, row counts, and gates are
  specified
- selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- P0 `72/3` actor/action contract and deployed `[steer, throttle, brake]`
  mapping remain preserved

## Rejected Claims After M2622

Rejected:

- source build executed
- adapter probe executed
- dependency ready for execution
- reset executed
- reset success
- rollout feasibility
- policy action or environment step executed
- rollout or replay executed
- validation protocol readiness
- validation admission
- validation readiness or result
- external validation execution
- high-fidelity validation readiness or result
- controller ranking, success-rate verdict, or checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2622 is a design-only milestone. It creates no new closed-loop driver
performance evidence and no paper verdict delta.
