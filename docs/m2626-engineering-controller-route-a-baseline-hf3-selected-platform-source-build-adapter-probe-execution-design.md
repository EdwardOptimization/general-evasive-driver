# M2626 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Design

- status: completed
- decision: `route_to_hf3_selected_platform_source_build_adapter_probe_execution_materialization_preflight`
- manifest: `experiments/manifests/m2626-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-design.json`
- parent synthesis: `docs/m2625-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-synthesis.md`
- parent audit: `docs/m2624-engineering-controller-route-a-baseline-hf3-selected-platform-reset-execution-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2623_engineering_controller_route_a_hf3_selected_platform_reset_execution_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight.json`
- next: `m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight`

## Design Verdict

M2626 designs the bounded artifacts required to represent selected-platform
source-build and adapter-probe execution preparation for
`chrono_vehicle_or_equivalent_open_backend`. M2627 should materialize command
contracts, isolation guards, future artifact/trace capture contracts, outcome
taxonomy rows, actor/action guards, claim-boundary rows, a gate matrix, a
summary, and a milestone doc.

This design is still pre-execution. It does not install or import external
simulation dependencies, mutate dependencies, run source builds, run adapter
probes, start a backend, execute resets, execute policy actions, step
environments, execute rollouts, execute replay, execute validation, train,
rank controllers, promote checkpoints, compute success rates, or claim driver
performance.

If M2627 passes all gates, the allowed claim is limited to selected-platform
source-build/adapter-probe execution design artifacts materialized. That would
still not imply dependency execution readiness, source-build execution,
adapter-probe execution, backend availability, reset execution, reset success,
rollout feasibility, validation protocol readiness, validation admission,
high-fidelity validation readiness, validation result, current-sim verdict,
paper-level evidence, finite-window-vs-GRU evidence, level3 self-ID, or
professional driver behavior.

## Source Evidence

Accepted selected-platform reset-execution readiness boundary:

```text
M2625 synthesis decision: continue_to_hf3_selected_platform_source_build_adapter_probe_execution_design
M2624 audit decision: accept_hf3_selected_platform_reset_execution_readiness_materialization_route_to_result_synthesis
M2623 status_pass: true
source-build/adapter-probe evidence admission rows: 4/4 pass
backend availability fixture rows: 2/2 pass
reset invocation dry-run contract rows: 2/2 pass
reset request binding rows: 2/2 pass
actor-view after-reset extraction rows: 2/2 pass
reset outcome audit schema rows: 10/10 pass
actor/action guard rows: 2/2 pass
claim-boundary rows: 27/27 pass
materialization gates: 13/13 pass
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
actor contract: P0 observation 72 / action 3
```

Route C in `docs/post-m2470-route-plan.md` still controls the direction:
prepare a validation layer without migrating the full training loop too early,
keep current-sim diagnostic-only, prefer an open/auditable high-fidelity
vehicle dynamics layer, and limit HF3 to reset/rollout feasibility preparation
with no controller-family verdict.

The paper-governing route remains unchanged. Self-ID and GRU advantage are
bounded hypotheses. Source-build/adapter-probe execution design rows are
validation-layer preparation, not current-sim verdict, paper evidence,
finite-window-vs-GRU evidence, or level3 self-identification evidence.

## M2627 Artifact Contract

M2627 should write:

```text
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_command_contract_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_command_contract_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_dependency_environment_isolation_guard_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_artifact_capture_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_adapter_probe_trace_capture_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_outcome_taxonomy_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_actor_action_guard_rows.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/hf3_selected_platform_source_build_adapter_probe_claim_boundary_checks.csv
runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/selected_platform_source_build_adapter_probe_execution_gate_matrix.csv
docs/m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight.md
```

Every M2627 row should prove selected-platform source-build/adapter-probe
execution design artifacts only. Rows must keep:

```text
selected_platform_source_build_adapter_probe_execution_design_materialized_in_m2627: true
selected_platform_family_in_m2627: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2627: false
external_import_allowed_in_m2627: false
runtime_execution_allowed_in_m2627: false
dependency_mutation_allowed_in_m2627: false
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
```

## Source-Build Command Contract Rows

M2627 should write source-build command contract rows:

```text
command_contract_id
command_family
selected_platform_family
source_tree_required
out_of_tree_build_required
dependency_mutation_allowed_in_m2627
network_access_allowed_in_m2627
build_execution_allowed_in_m2627
log_capture_required
artifact_capture_required
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `selected_platform_source_build_configure_command_contract`
- `selected_platform_source_build_compile_command_contract`

Pass criteria:

- exactly two rows exist
- source tree and out-of-tree build requirements are represented as command
  contracts only
- dependency mutation, network access, and build execution are false in M2627
- logs and artifacts are future capture requirements, not captured build
  results
- command metadata is not actor-visible

## Adapter-Probe Command Contract Rows

M2627 should write adapter-probe command contract rows:

```text
adapter_probe_contract_id
probe_family
selected_platform_family
adapter_import_required
backend_discovery_required
backend_start_allowed_in_m2627
reset_allowed_in_m2627
adapter_probe_execution_allowed_in_m2627
trace_capture_required
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `selected_platform_adapter_import_probe_contract`
- `selected_platform_adapter_backend_probe_contract`

Pass criteria:

- exactly two rows exist
- adapter import and backend discovery remain future probe requirements
- backend start, reset, and adapter-probe execution are false in M2627
- trace capture is a future audit requirement only
- probe metadata is not actor-visible

## Dependency And Environment Isolation Guard Rows

M2627 should write isolation guard rows:

```text
isolation_guard_id
guard_family
selected_platform_family
external_install_allowed_in_m2627
external_import_allowed_in_m2627
dependency_mutation_allowed_in_m2627
source_tree_mutation_allowed_in_m2627
network_access_allowed_in_m2627
external_runtime_allowed_in_m2627
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `dependency_install_guard`
- `source_tree_mutation_guard`
- `network_access_guard`
- `external_runtime_guard`

Pass criteria:

- exactly four rows exist
- install, import, dependency mutation, source-tree mutation, network access,
  and external runtime are false in M2627
- guard metadata is not actor-visible

## Source-Build Artifact Capture Rows

M2627 should write source-build artifact capture rows:

```text
artifact_capture_id
artifact_family
selected_platform_family
required_for_future_source_build_audit
required_for_future_adapter_probe_admission
materialized_in_m2627
source_build_executed_in_m2627
artifact_observed_in_m2627
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `configure_log_capture`
- `compile_log_capture`
- `build_artifact_manifest_capture`
- `build_environment_snapshot_capture`

Pass criteria:

- exactly four rows exist
- all rows are future capture contracts
- source build and artifact observation are false in M2627
- capture metadata is not actor-visible

## Adapter-Probe Trace Capture Rows

M2627 should write adapter-probe trace capture rows:

```text
trace_capture_id
trace_family
selected_platform_family
required_for_future_adapter_probe_audit
required_for_future_reset_execution_admission
materialized_in_m2627
adapter_probe_executed_in_m2627
backend_started_in_m2627
trace_observed_in_m2627
actor_visible_allowed
status_pass
claim_boundary
```

Required rows:

- `adapter_import_trace_capture`
- `backend_factory_trace_capture`
- `backend_capability_trace_capture`
- `adapter_failure_trace_capture`

Pass criteria:

- exactly four rows exist
- all rows are future trace contracts
- adapter probe, backend start, and trace observation are false in M2627
- trace metadata is not actor-visible

## Source-Build Adapter-Probe Outcome Taxonomy Rows

M2627 should write outcome taxonomy rows:

```text
outcome_taxonomy_id
outcome_field
field_family
required_for_future_source_build_adapter_probe_audit
allowed_to_support_backend_availability_after_execution
allowed_to_support_reset_execution_admission_after_execution
actor_visible_allowed
materialized_in_m2627
status_pass
claim_boundary
```

Required outcome fields:

- `source_available`
- `configure_attempted`
- `compile_attempted`
- `build_artifact_available`
- `adapter_import_attempted`
- `adapter_probe_attempted`
- `backend_discovered`
- `probe_status`
- `failure_reason`
- `execution_timestamp`

Pass criteria:

- exactly ten rows exist
- no outcome field is actor-visible
- outcome fields are schema only and do not claim backend availability,
  source-build execution, adapter-probe execution, reset execution, or
  validation readiness in M2627

## Source-Build Adapter-Probe Actor/Action Guard Rows

M2627 should write actor/action guard rows:

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

- `stable_avoidable_aeb_feasible_source_build_adapter_probe_actor_action_guard`
- `stable_aes_aeb_infeasible_source_build_adapter_probe_actor_action_guard`

Pass criteria:

- exactly two rows exist
- P0 `72/3` is preserved
- deployed action mapping remains `[steer, throttle, brake]`
- no actor input or action contract mutation is detected
- no hidden/oracle or metadata actor input is visible

## Claim-Boundary Rows

M2627 should write claim-boundary rows for these claim families:

```text
selected_platform_source_build_adapter_probe_execution_design_materialized
dependency_ready_for_execution
source_build_executed
adapter_probe_executed
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

Only `selected_platform_source_build_adapter_probe_execution_design_materialized`
may be true in M2627. All other claim families must be false.

## Gate Matrix

M2627 should write a gate matrix with these gates:

```text
source_artifacts_exist
m2623_m2624_m2625_reset_execution_readiness_evidence_accepted
source_build_command_contract_rows_pass
adapter_probe_command_contract_rows_pass
dependency_environment_isolation_guard_rows_pass
source_build_artifact_capture_rows_pass
adapter_probe_trace_capture_rows_pass
outcome_taxonomy_rows_pass
actor_action_guard_rows_pass
claim_boundary_rows_pass
no_install_import_mutation_build_probe_reset_step_action_rollout_replay_or_validation_execution
source_build_adapter_probe_reset_validation_and_performance_forbidden
actor_action_contract_preserved
```

Pass criteria:

- exactly thirteen gates exist
- every gate passes
- gate language separates design materialization from execution, readiness,
  availability, validation, and performance claims

## Supported Claims

Supported:

- HF3 selected-platform source-build/adapter-probe execution design artifacts
  are specified for future materialization
- the selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- M2627 may materialize command contracts, environment guards, future
  artifact/trace capture contracts, outcome taxonomy rows, actor/action guard
  rows, claim-boundary rows, and gates
- actor/action guard rows preserve P0 `72/3` and the deployed
  `[steer, throttle, brake]` mapping
- source-build/adapter-probe outcomes and backend statuses remain
  actor-invisible audit metadata

## Rejected Claims

Not supported, and explicitly rejected:

- dependency ready for execution
- source build executed
- adapter probe executed
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

M2626 is source-build/adapter-probe execution design only. It does not install,
import, build, probe, start a backend, reset, step, run a policy action, roll
out, replay, validate, compare controller families, or prove professional
driver behavior.

## Next Branch Decision

Continue to:

```text
m2627-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-preflight
```

M2627 should materialize the bounded source-build/adapter-probe execution
design artifacts listed above. It should still be a materialization preflight,
not actual source-build or adapter-probe execution. It must not install/import
external simulation dependencies, mutate dependencies, execute source build,
execute adapter probe, start a backend, execute reset, execute policy actions,
step environments, roll out, replay, run validation, train, rank controllers,
promote checkpoints, compute success rates, or make driver-performance, paper,
finite-window-vs-GRU, current-sim, high-fidelity validation, or self-ID claims.
