# M2618 Engineering Controller Route A Baseline HF3 Selected-Platform Reset-Feasibility Readiness Design

- status: completed
- decision: `route_to_hf3_selected_platform_reset_feasibility_readiness_materialization_preflight`
- manifest: `experiments/manifests/m2618-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-design.json`
- parent synthesis: `docs/m2617-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-synthesis.md`
- parent audit: `docs/m2616-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2619-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-preflight.json`
- next: `m2619-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-preflight`

## Design Verdict

M2618 designs the bounded artifacts required to represent selected-platform
reset-feasibility readiness for
`chrono_vehicle_or_equivalent_open_backend`. M2619 should materialize reset
request schema, initial-state admission, actor-view parity, deterministic
seed/lineage, reset outcome taxonomy guard, reset-execution precondition,
actor/action guard, claim-boundary, and gate rows.

This design is intentionally still pre-execution. It does not install or import
external simulation dependencies, mutate dependencies, run source builds, run
adapter probes, execute resets, execute policy actions, step environments,
execute rollouts, execute replay, execute validation, train, rank controllers,
promote checkpoints, compute success rates, or claim driver performance.

If M2619 passes all gates, the allowed claim is limited to selected-platform
reset-feasibility readiness design artifacts materialized. That would still
not imply reset execution, reset success, rollout feasibility, validation
protocol readiness, validation admission, high-fidelity validation readiness,
validation result, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, level3 self-ID, or professional driver
behavior.

## Source Evidence

Accepted selected-platform executable-protocol readiness boundary:

```text
M2617 synthesis decision: continue_to_hf3_selected_platform_reset_feasibility_readiness_design
M2616 audit decision: accept_hf3_selected_platform_executable_protocol_readiness_materialization_route_to_result_synthesis
M2615 status_pass: true
source/dependency review rows: 4/4 pass
build/probe plan rows: 4/4 pass
reset/step API readiness rows: 2/2 pass
actor extractor parity rows: 2/2 pass
action mapping parity rows: 2/2 pass
scenario-role binding rows: 2/2 pass
result export/replay readiness rows: 3/3 pass
validation-admission prerequisite rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 28/28 pass
materialization gates: 14/14 pass
selected_platform_family_in_m2615: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2615: false
external_import_allowed_in_m2615: false
runtime_execution_allowed_in_m2615: false
dependency_mutation_allowed_in_m2615: false
source_build_executed_in_m2615: false
adapter_probe_executed_in_m2615: false
reset_executed_in_m2615: false
environment_step_executed_in_m2615: false
policy_action_executed_in_m2615: false
rollout_executed_in_m2615: false
replay_executed_in_m2615: false
external_validation_execution_allowed_in_m2615: false
validation_protocol_ready_in_m2615: false
validation_admission_granted_in_m2615: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2615: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, keep
current-sim diagnostic-only, prefer an open/auditable high-fidelity vehicle
dynamics layer, and use HF3 as reset/rollout feasibility only without a
controller-family verdict.

The paper-governing route remains unchanged. Self-ID and GRU advantage are
bounded hypotheses. Reset-feasibility readiness rows are validation-layer
preparation, not current-sim verdict, paper evidence, finite-window-vs-GRU
evidence, or level3 self-identification evidence.

## M2619 Artifact Contract

M2619 should write:

```text
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/summary.json
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_request_schema_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_initial_state_admission_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_actor_view_parity_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_seed_lineage_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_outcome_taxonomy_guard_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_execution_precondition_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_feasibility_actor_action_guard_rows.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/hf3_selected_platform_reset_feasibility_claim_boundary_checks.csv
runs/m2619_engineering_controller_route_a_hf3_selected_platform_reset_feasibility_readiness/selected_platform_reset_feasibility_readiness_gate_matrix.csv
docs/m2619-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-materialization-preflight.md
```

Every M2619 row should prove selected-platform reset-feasibility readiness
design artifacts only. Rows must keep:

```text
selected_platform_reset_feasibility_readiness_design_materialized_in_m2619: true
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
driver_performance_claim_allowed_in_m2619: false
```

## Reset Request Schema Rows

M2619 should write reset request schema rows:

```text
reset_request_schema_id
route_role_id
selected_platform_family
backend_family
scenario_binding_id
seed_policy
actor_observation_shape
action_shape
reset_request_schema_materialized_in_m2619
initial_state_required
actor_view_required_after_reset
source_build_required_before_execution
adapter_probe_required_before_execution
reset_executed_in_m2619
policy_action_allowed_in_m2619
environment_step_allowed_in_m2619
rollout_allowed_in_m2619
validation_result_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_request_schema`
- `stable_aes_aeb_infeasible_reset_request_schema`

Pass criteria:

- exactly two rows exist
- selected platform family is `chrono_vehicle_or_equivalent_open_backend`
- both rows preserve P0 `72/3`
- source build and adapter probe remain future prerequisites
- reset, policy action, environment step, rollout, and validation claims are
  false in M2619

## Initial-State Admission Rows

M2619 should write initial-state admission rows:

```text
initial_state_admission_id
route_role_id
selected_platform_family
initial_state_family
source_binding_id
initial_state_admission_materialized_in_m2619
geometry_binding_required
actor_view_required_after_reset
hidden_oracle_actor_input_allowed
feasibility_label_actor_visible
reset_status_actor_visible
validation_status_actor_visible
reset_execution_allowed_in_m2619
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_initial_state_admission`
- `stable_aes_aeb_infeasible_initial_state_admission`

Pass criteria:

- exactly two rows exist
- initial-state admission is a static schema and audit contract
- hidden/oracle inputs, feasibility labels, reset status, and validation status
  are not actor-visible
- reset execution is false in M2619

## Actor-View Parity Rows

M2619 should write actor-view parity rows:

```text
actor_view_parity_id
route_role_id
selected_platform_family
actor_observation_shape
action_shape
actor_view_contract_defined_in_m2619
ego_kinematics_included
actuator_state_included
previous_command_included
road_geometry_included
obstacle_geometry_included
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
selected_platform_actor_visible
protocol_status_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- observation shape is `72` and action shape is `3`
- actor-visible features remain deployable P0 information only
- hidden/oracle inputs, diagnostics, labels, backend status, reset outcome,
  selected platform, and protocol status are false

## Deterministic Seed And Lineage Rows

M2619 should write deterministic seed and lineage rows:

```text
reset_seed_lineage_id
route_role_id
selected_platform_family
scenario_spec_id
seed_policy
parent_checkpoint_count
parent_summary
deterministic_seed_required
replay_lineage_required
lineage_materialized_in_m2619
reset_executed_in_m2619
replay_executed_in_m2619
status_pass
claim_boundary
```

Pass criteria:

- exactly two rows exist
- seed and lineage are audit metadata only
- reset and replay execution are false in M2619
- lineage metadata is not actor-visible

## Reset Outcome Taxonomy Guard Rows

M2619 should write reset outcome taxonomy guard rows:

```text
outcome_taxonomy_guard_id
outcome_field
field_family
actor_visible_allowed
audit_metadata_allowed
required_for_future_execution_audit
allowed_to_support_reset_success_after_execution
allowed_to_support_validation
reset_outcome_actor_visible
validation_outcome_actor_visible
status_pass
claim_boundary
```

Required outcome fields:

- `backend_available`
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
- outcome taxonomy rows are future execution-audit schema only
- reset success and validation claims remain false in M2619

## Reset-Execution Precondition Rows

M2619 should write reset-execution precondition rows:

```text
precondition_id
precondition_family
selected_platform_family
required_before_reset_execution
materialized_in_m2619
satisfied_by_m2619
source_build_required
adapter_probe_required
backend_availability_required
reset_request_schema_required
actor_view_parity_required
deterministic_lineage_required
claim_boundary_required
reset_execution_allowed_in_m2619
status_pass
claim_boundary
```

Required preconditions:

- `source_or_equivalent_trace_precondition`
- `source_build_precondition`
- `adapter_probe_precondition`
- `backend_availability_precondition`
- `reset_request_schema_precondition`
- `actor_view_and_lineage_precondition`

Pass criteria:

- exactly six rows exist
- every row states what is required before future reset execution
- source build, adapter probe, backend availability, request schema, actor
  view parity, deterministic lineage, and claim boundary remain prerequisites
- reset execution is false in M2619

## Actor/Action Guard Rows

M2619 should write actor/action guard rows:

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

Pass criteria:

- exactly two rows exist
- P0 `72/3` and `[steer, throttle, brake]` are preserved
- actor input and action contract mutation are false
- hidden/oracle actor input and metadata actor visibility are false

## Claim Boundary Checks

M2619 should write claim-boundary rows for:

- selected-platform reset-feasibility readiness materialization
- dependency execution readiness
- source build execution
- adapter probe execution
- reset execution
- reset success
- policy action execution
- environment step execution
- rollout execution
- replay execution
- validation protocol readiness
- validation admission
- validation readiness
- validation result
- external validation execution
- high-fidelity validation readiness/result
- HF4 discrepancy result
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

Only the materialization claim may be true. All execution, validation,
ranking, performance, paper, finite-window-vs-GRU, current-sim, high-fidelity
validation, and self-ID claims must be false in M2619.

## Gate Matrix

M2619 passes only if:

- all required artifacts exist
- exactly two reset request schema rows are present
- exactly two initial-state admission rows are present
- exactly two actor-view parity rows are present
- exactly two deterministic seed/lineage rows are present
- exactly eight reset outcome taxonomy guard rows are present
- exactly six reset-execution precondition rows are present
- exactly two actor/action guard rows are present
- claim-boundary rows are complete and scoped
- P0 `72/3` and `[steer, throttle, brake]` are preserved
- source build, adapter probe, reset, policy action, environment step, rollout,
  replay, validation, training, ranking, promotion, and success-rate execution
  flags are false
- validation readiness/result, reset success, rollout success,
  driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity
  validation, and self-ID claims are false

## Follow-Up

Route to M2619 materialization/preflight. M2619 may add a bounded repo-local
materializer and tests to write the artifacts above. It must not execute reset,
step environments, run external simulation, execute policy actions, run replay,
run validation, or interpret reset-feasibility readiness planning rows as
validation or driver performance.
