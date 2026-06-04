# M2630 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Attempt Design

- status: completed
- decision: `route_to_hf3_selected_platform_source_build_adapter_probe_execution_attempt_materialization_preflight`
- manifest: `experiments/manifests/m2630-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-design.json`
- parent synthesis: `docs/m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis.md`
- parent audit: `docs/m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-audit.md`
- parent materialization summary: `runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json`
- follow-up manifest: `experiments/manifests/m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-preflight.json`
- next: `m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-preflight`

## Design Verdict

M2630 designs the bounded artifacts required to represent selected-platform
source-build/adapter-probe execution-attempt preparation for
`chrono_vehicle_or_equivalent_open_backend`. M2631 should materialize command
attempt/admission rows, dependency/runtime execution guards, execution-attempt
log capture rows, backend-discovery evidence capture rows, execution failure
taxonomy rows, actor/action guards, claim-boundary rows, a gate matrix, a
summary, and a milestone doc.

This design is still pre-execution. It does not install or import external
simulation dependencies, mutate dependencies, mutate source trees, use network
dependency resolution, run source builds, run adapter probes, start a backend,
execute resets, execute policy actions, step environments, execute rollouts,
execute replay, execute validation, train, rank controllers, promote
checkpoints, compute success rates, or claim driver performance.

If M2631 passes all gates, the allowed claim is limited to selected-platform
source-build/adapter-probe execution-attempt protocol artifacts materialized.
That would still not imply dependency execution readiness, source-build
execution, adapter-probe execution, backend discovery, backend availability,
reset execution, reset success, rollout feasibility, validation protocol
readiness, validation admission, high-fidelity validation readiness,
validation result, current-sim verdict, paper-level evidence,
finite-window-vs-GRU evidence, level3 self-ID, or professional driver
behavior.

## Source Evidence

Accepted selected-platform source-build/adapter-probe execution design
materialization boundary:

```text
M2629 synthesis decision: continue_to_hf3_selected_platform_source_build_adapter_probe_execution_attempt_design
M2628 audit decision: accept_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_route_to_result_synthesis
M2627 status_pass: true
source-build command contract rows: 2/2 pass
adapter-probe command contract rows: 2/2 pass
dependency/environment isolation guard rows: 4/4 pass
source-build artifact capture rows: 4/4 pass
adapter-probe trace capture rows: 4/4 pass
outcome taxonomy rows: 10/10 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 28/28 pass
materialization gates: 13/13 pass
selected_platform_family_in_m2627: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2627: false
external_import_allowed_in_m2627: false
runtime_execution_allowed_in_m2627: false
dependency_mutation_allowed_in_m2627: false
source_tree_mutation_allowed_in_m2627: false
network_access_allowed_in_m2627: false
source_build_executed_in_m2627: false
adapter_probe_executed_in_m2627: false
backend_started_in_m2627: false
reset_executed_in_m2627: false
environment_step_executed_in_m2627: false
policy_action_executed_in_m2627: false
rollout_executed_in_m2627: false
replay_executed_in_m2627: false
external_validation_execution_allowed_in_m2627: false
validation_protocol_ready_in_m2627: false
validation_admission_granted_in_m2627: false
validation_result_claim_allowed: false
backend_availability_claim_allowed_in_m2627: false
reset_success_claim_allowed_in_m2627: false
rollout_feasibility_claim_allowed_in_m2627: false
driver_performance_claim_allowed_in_m2627: false
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare validation without migrating the training loop too early, keep
current-sim diagnostic-only, prefer an open/auditable high-fidelity vehicle
dynamics layer, and use HF3 as reset/rollout feasibility preparation only
without a controller-family verdict.

The paper-governing route remains unchanged. Self-ID and GRU advantage are
bounded hypotheses. Execution-attempt protocol rows are validation-layer
preparation, not current-sim verdict, paper evidence, finite-window-vs-GRU
evidence, or level3 self-identification evidence.

## M2631 Artifact Contract

M2631 should write:

```text
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/summary.json
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_source_build_execution_attempt_admission_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_adapter_probe_execution_attempt_admission_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_dependency_runtime_execution_guard_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_execution_attempt_log_capture_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_backend_discovery_evidence_capture_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_execution_failure_taxonomy_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_execution_attempt_actor_action_guard_rows.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/hf3_selected_platform_execution_attempt_claim_boundary_checks.csv
runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/selected_platform_source_build_adapter_probe_execution_attempt_gate_matrix.csv
docs/m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-preflight.md
```

Every M2631 row should prove selected-platform source-build/adapter-probe
execution-attempt protocol materialization only. Rows must keep:

```text
selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized_in_m2631: true
selected_platform_family_in_m2631: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2631: false
external_import_allowed_in_m2631: false
runtime_execution_allowed_in_m2631: false
dependency_mutation_allowed_in_m2631: false
source_tree_mutation_allowed_in_m2631: false
network_access_allowed_in_m2631: false
source_build_executed_in_m2631: false
source_build_attempt_executed_in_m2631: false
source_build_success_claim_allowed_in_m2631: false
adapter_probe_executed_in_m2631: false
adapter_probe_attempt_executed_in_m2631: false
adapter_probe_success_claim_allowed_in_m2631: false
backend_started_in_m2631: false
backend_discovered_claim_allowed_in_m2631: false
backend_availability_claim_allowed_in_m2631: false
reset_executed_in_m2631: false
environment_step_executed_in_m2631: false
policy_action_executed_in_m2631: false
rollout_executed_in_m2631: false
replay_executed_in_m2631: false
external_validation_execution_allowed_in_m2631: false
validation_protocol_ready_in_m2631: false
validation_admission_granted_in_m2631: false
validation_result_claim_allowed: false
reset_success_claim_allowed_in_m2631: false
rollout_feasibility_claim_allowed_in_m2631: false
driver_performance_claim_allowed_in_m2631: false
```

## Source-Build Execution Attempt Admission Rows

M2631 should write source-build execution attempt admission rows:

```text
source_build_attempt_admission_id
command_family
selected_platform_family
command_contract_id
source_tree_required
out_of_tree_build_required
command_attempt_schema_materialized_in_m2631
execution_attempt_allowed_after_m2631_audit
source_build_executed_in_m2631
source_build_attempt_executed_in_m2631
dependency_mutation_allowed_in_m2631
network_access_allowed_in_m2631
log_capture_required
artifact_capture_required
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `selected_platform_source_build_configure_attempt_admission`
- `selected_platform_source_build_compile_attempt_admission`

Pass criteria:

- exactly two rows exist
- selected platform family is `chrono_vehicle_or_equivalent_open_backend`
- source tree and out-of-tree build requirements are represented as
  attempt-admission metadata only
- dependency mutation, network access, source-build execution, and
  source-build attempt execution are false in M2631
- logs and artifacts are required for a future audited attempt, not captured
  build results
- command metadata is not actor-visible

## Adapter-Probe Execution Attempt Admission Rows

M2631 should write adapter-probe execution attempt admission rows:

```text
adapter_probe_attempt_admission_id
probe_family
selected_platform_family
adapter_probe_contract_id
adapter_import_required
backend_discovery_required
command_attempt_schema_materialized_in_m2631
adapter_probe_executed_in_m2631
adapter_probe_attempt_executed_in_m2631
backend_start_allowed_in_m2631
reset_allowed_in_m2631
trace_capture_required
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `selected_platform_adapter_import_attempt_admission`
- `selected_platform_adapter_backend_probe_attempt_admission`

Pass criteria:

- exactly two rows exist
- adapter import and backend discovery remain future attempt requirements
- adapter-probe execution, adapter-probe attempt execution, backend start,
  and reset are false in M2631
- trace capture is a future audit requirement only
- probe metadata is not actor-visible

## Dependency And Runtime Execution Guard Rows

M2631 should write dependency/runtime execution guard rows:

```text
execution_guard_id
guard_family
selected_platform_family
external_install_allowed_in_m2631
external_import_allowed_in_m2631
dependency_mutation_allowed_in_m2631
source_tree_mutation_allowed_in_m2631
network_access_allowed_in_m2631
external_runtime_allowed_in_m2631
source_build_execution_allowed_in_m2631
adapter_probe_execution_allowed_in_m2631
backend_start_allowed_in_m2631
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `dependency_install_guard`
- `source_tree_mutation_guard`
- `network_access_guard`
- `external_runtime_guard`
- `backend_start_guard`

Pass criteria:

- exactly five rows exist
- install, import, dependency mutation, source-tree mutation, network access,
  external runtime, source-build execution, adapter-probe execution, and
  backend start are false in M2631
- guard metadata is not actor-visible

## Execution-Attempt Log Capture Rows

M2631 should write execution-attempt log capture rows:

```text
execution_log_capture_id
log_family
selected_platform_family
required_for_future_execution_attempt_audit
command_attempt_schema_materialized_in_m2631
source_build_executed_in_m2631
adapter_probe_executed_in_m2631
log_observed_in_m2631
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `configure_attempt_log_capture`
- `compile_attempt_log_capture`
- `adapter_import_attempt_log_capture`
- `backend_probe_attempt_log_capture`
- `execution_environment_snapshot_log_capture`

Pass criteria:

- exactly five rows exist
- all rows are future log capture contracts
- source build, adapter probe, and log observation are false in M2631
- log metadata is not actor-visible

## Backend-Discovery Evidence Capture Rows

M2631 should write backend-discovery evidence capture rows:

```text
backend_discovery_capture_id
evidence_family
selected_platform_family
required_for_future_backend_availability_audit
required_for_future_reset_admission
backend_discovery_schema_materialized_in_m2631
adapter_probe_executed_in_m2631
backend_started_in_m2631
backend_discovered_claim_allowed_in_m2631
backend_availability_claim_allowed_in_m2631
reset_execution_allowed_in_m2631
evidence_observed_in_m2631
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `backend_factory_metadata_capture`
- `backend_capability_manifest_capture`
- `backend_healthcheck_trace_capture`
- `backend_failure_trace_capture`

Pass criteria:

- exactly four rows exist
- all rows are future backend-discovery audit contracts
- adapter probe, backend start, reset execution, backend-discovered claims,
  backend-availability claims, and evidence observation are false in M2631
- discovery metadata is not actor-visible

## Execution Failure Taxonomy Rows

M2631 should write execution failure taxonomy rows:

```text
failure_taxonomy_id
failure_field
field_family
required_for_future_execution_attempt_audit
allowed_to_support_failure_classification_after_execution
actor_visible_allowed
materialized_in_m2631
status_pass
claim_boundary
```

Required failure fields:

- `source_missing`
- `configure_failed`
- `compile_failed`
- `artifact_missing`
- `adapter_import_failed`
- `backend_probe_failed`
- `backend_unavailable`
- `dependency_mutation_detected`
- `network_access_detected`
- `timeout`
- `unknown_failure`

Pass criteria:

- exactly eleven rows exist
- no failure field is actor-visible
- failure fields are schema only and do not claim source-build execution,
  adapter-probe execution, backend availability, reset execution, or validation
  readiness in M2631

## Execution-Attempt Actor/Action Guard Rows

M2631 should write actor/action guard rows:

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

- `stable_avoidable_aeb_feasible_execution_attempt_actor_action_guard`
- `stable_aes_aeb_infeasible_execution_attempt_actor_action_guard`

Pass criteria:

- exactly two rows exist
- P0 `72/3` is preserved
- deployed action mapping remains `[steer, throttle, brake]`
- no actor input or action contract mutation is detected
- no hidden/oracle or metadata actor input is visible

## Claim-Boundary Rows

M2631 should write claim-boundary rows for these claim families:

```text
selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized
dependency_ready_for_execution
source_build_attempt_executed
source_build_succeeded
adapter_probe_attempt_executed
adapter_probe_succeeded
backend_discovered
backend_available
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

Only
`selected_platform_source_build_adapter_probe_execution_attempt_protocol_materialized`
may be true in M2631. All other claim families must be false.

## Gate Matrix

M2631 should write a gate matrix with these gates:

```text
source_artifacts_exist
m2627_m2628_m2629_source_build_adapter_probe_design_evidence_accepted
source_build_attempt_admission_rows_pass
adapter_probe_attempt_admission_rows_pass
dependency_runtime_guard_rows_pass
execution_attempt_log_capture_rows_pass
backend_discovery_evidence_capture_rows_pass
execution_failure_taxonomy_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
no_install_import_mutation_build_probe_backend_reset_step_action_rollout_replay_or_validation_execution
execution_readiness_backend_reset_validation_and_performance_forbidden
actor_action_contract_preserved
m2632_result_audit_handoff_defined
```

Pass criteria:

- exactly fourteen gates exist
- every gate passes
- gate language separates protocol materialization from source-build execution,
  adapter-probe execution, backend availability, reset execution, validation,
  and performance claims

## Supported Claims

Supported:

- HF3 selected-platform source-build/adapter-probe execution-attempt protocol
  artifacts are specified for future materialization
- the selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- M2631 may materialize command attempt/admission rows, runtime guards,
  future log/trace/evidence capture contracts, failure taxonomy rows,
  actor/action guard rows, claim-boundary rows, and gates
- actor/action guard rows preserve P0 `72/3` and the deployed
  `[steer, throttle, brake]` mapping
- source-build/adapter-probe outcomes, backend statuses, failure taxonomy, and
  execution logs remain actor-invisible audit metadata

## Rejected Claims

Not supported, and explicitly rejected:

- dependency ready for execution
- source build attempted or executed
- source build succeeded
- adapter probe attempted or executed
- adapter probe succeeded
- backend discovered
- backend availability
- reset executed
- reset success
- environment step executed
- policy action executed
- rollout executed
- replay executed
- rollout feasibility
- validation protocol ready
- validation admission granted
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2630 is execution-attempt design only. It does not install, import, build,
probe, start a backend, reset, step, run a policy action, roll out, replay,
validate, compare controller families, or prove professional driver behavior.

## Next Branch Decision

Continue to:

```text
m2631-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-preflight
```

M2631 should materialize the bounded source-build/adapter-probe
execution-attempt protocol artifacts listed above. It should still be a
materialization preflight, not actual source-build or adapter-probe execution.
It must not install/import external simulation dependencies, mutate
dependencies, mutate source trees, use network access, execute source build,
execute adapter probe, start a backend, execute reset, execute policy actions,
step environments, roll out, replay, run validation, train, rank controllers,
promote checkpoints, compute success rates, or make driver-performance,
paper, finite-window-vs-GRU, current-sim, high-fidelity validation, or self-ID
claims.
