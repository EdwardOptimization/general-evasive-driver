# M2591 Engineering Controller Route A Baseline HF3 Source-Only Adapter Readiness Blocker Closure Design

- status: completed
- decision: `route_to_hf3_source_only_adapter_blocker_closure_materialization_preflight`
- manifest: `experiments/manifests/m2591-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-design.json`
- parent synthesis: `docs/m2590-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-result-synthesis.md`
- parent audit: `docs/m2589-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-result-audit.md`
- parent materialization summary: `runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/summary.json`
- follow-up manifest: `experiments/manifests/m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-preflight.json`
- next: `m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-preflight`

## Design Verdict

M2591 designs the bounded artifacts required to move from source-only blocker
definition evidence to source-only blocker closure materialization. M2592 should
materialize repo-local closure evidence for the four explicit blocker families:

```text
external_state_extraction_boundary
time_step_and_actuator_latency_contract
failure_status_taxonomy_mapping
source_only_fixture_smoke_lineage
```

This design intentionally keeps closure scoped to source-only adapter evidence.
It does not select a high-fidelity validation platform, install or import
external simulation dependencies, run external simulation, execute resets,
execute policy actions, step environments, execute rollouts, execute
validation, train, rank controllers, promote checkpoints, compute success
rates, or claim driver performance.

If M2592 passes all closure gates, the allowed claim is limited to repo-local
source-only adapter blocker closure materialized. That would still not imply
validation protocol readiness, validation admission, high-fidelity validation
readiness, validation result, HF4 discrepancy result, current-sim verdict,
paper-level evidence, finite-window-vs-GRU evidence, level3 self-ID, or
professional driver behavior.

## Source Evidence

Accepted source boundary:

```text
M2590 synthesis decision: continue_to_hf3_source_only_adapter_readiness_blocker_closure_design
M2589 audit decision: accept_hf3_source_only_adapter_readiness_blocker_materialization_route_to_result_synthesis
M2588 status_pass: true
external-state extraction boundary rows: 4/4 pass
time-step/actuator latency contract rows: 4/4 pass
failure/status taxonomy mapping rows: 4/4 pass
source-only fixture smoke lineage rows: 4/4 pass
actor-visibility guard rows: 4/4 pass
claim-boundary checks: 15/15 pass
materialization gates: 11/11 pass
actor contract: P0 observation 72 / action 3
readiness_satisfied_in_m2588: false
external_validation_execution_allowed_in_m2588: false
source_only_adapter_blockers_closed_claim_allowed: false
platform_selection_claim_allowed: false
validation_protocol_ready_claim_allowed: false
validation_admission_granted: false
```

M2588/M2589/M2590 are sufficient to design source-only closure artifacts. They
are not sufficient to claim that closure has happened, to select a platform, or
to run validation.

## M2592 Artifact Contract

M2592 should write:

```text
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/summary.json
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_external_state_extraction_closure_rows.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_time_step_actuator_latency_closure_rows.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_failure_status_taxonomy_closure_rows.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_fixture_smoke_closure_rows.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_adapter_closure_actor_visibility_guard_rows.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/hf3_source_only_adapter_closure_claim_boundary_checks.csv
runs/m2592_engineering_controller_route_a_hf3_source_only_adapter_blocker_closure/source_only_adapter_blocker_closure_gate_matrix.csv
docs/m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-preflight.md
```

Every M2592 closure row should prove a concrete repo-local source artifact,
schema, hash, or guard exists for the blocker family. Rows may close the
source-only adapter blocker only when they keep:

```text
source_only_closure_materialized_in_m2592: true
validation_protocol_ready_in_m2592: false
validation_admission_granted_in_m2592: false
external_validation_execution_allowed_in_m2592: false
platform_selected_in_m2592: false
driver_performance_claim_allowed_in_m2592: false
```

## External State Extraction Closure Rows

M2592 should write external state extraction closure rows:

```text
state_closure_id
closure_family
definition_source_artifact
closure_source_artifact
fixture_schema_declared
extractor_output_schema_declared
backend_state_read_by_adapter_only
adapter_only_fields_redacted_from_actor
actor_observation_shape
actor_visible
diagnostic_only
hidden_or_oracle_actor_input_detected
source_only_closure_materialized_in_m2592
validation_protocol_ready_in_m2592
external_validation_execution_allowed_in_m2592
status_pass
claim_boundary
```

Required closure families:

- `ego_state_extractor_schema_closure`
- `external_backend_to_p0_mapping_closure`
- `diagnostic_state_redaction_closure`
- `validation_metadata_non_actor_channel_closure`

Pass criteria:

- every row has a source-only closure artifact or explicit schema target for
  M2592 materialization
- backend state may be read by adapter code only, never by the deployed actor
- adapter-only fields are redacted before the P0 actor observation projection
- actor observation shape remains `72`
- no hidden/oracle actor input, validation metadata, backend diagnostics,
  reset outcome, rollout outcome, validation outcome, platform selection, or
  protocol status enters actor input
- no row claims platform selection, validation protocol readiness, validation
  admission, validation readiness, validation result, HF4 discrepancy result,
  or driver performance

## Time-Step And Actuator-Latency Closure Rows

M2592 should write timing and latency closure rows:

```text
timing_closure_id
closure_family
definition_source_artifact
closure_source_artifact
simulation_time_step_value_declared
control_update_rate_value_declared
actuator_latency_channel_mapping_declared
command_hold_or_delay_semantics_declared
actor_observation_shape
action_shape
deployed_action_mapping_preserved
action_contract_mutation_detected
source_only_closure_materialized_in_m2592
validation_protocol_ready_in_m2592
external_validation_execution_allowed_in_m2592
status_pass
claim_boundary
```

Required closure families:

- `simulation_time_step_value_closure`
- `control_update_rate_alignment_closure`
- `actuator_latency_channel_mapping_closure`
- `command_hold_delay_semantics_closure`

Pass criteria:

- every timing contract has an explicit value, mapping, or semantic target for
  M2592 materialization
- P0 observation shape remains `72`
- action shape remains `3`
- deployed action mapping remains `[steer, throttle, brake]`
- no row changes actor input, action contract, update mode, or controller mode
- no row executes reset/action/step/rollout/validation or claims validation
  protocol readiness/result

## Failure/Status Taxonomy Closure Rows

M2592 should write failure/status taxonomy closure rows:

```text
status_closure_id
closure_family
definition_source_artifact
closure_source_artifact
repo_local_status_class_declared
terminal_or_abort_semantics_declared
backend_status_actor_visible
taxonomy_label_actor_visible
diagnostics_actor_visible
reset_outcome_actor_visible
rollout_outcome_actor_visible
validation_outcome_actor_visible
source_only_closure_materialized_in_m2592
validation_protocol_ready_in_m2592
external_validation_execution_allowed_in_m2592
status_pass
claim_boundary
```

Required closure families:

- `reset_failure_status_closure`
- `step_failure_status_closure`
- `collision_or_contact_status_closure`
- `validation_abort_status_closure`

Pass criteria:

- every external status path maps to a repo-local audit class
- terminal, abort, collision, and contact semantics are declared as adapter
  diagnostics, not actor features
- taxonomy labels, feasibility classes, backend statuses, diagnostics, reset
  outcomes, rollout outcomes, and validation outcomes remain outside actor
  inputs
- no row turns status mapping into validation admission, validation result,
  ranking, or driver-performance evidence

## Source-Only Fixture Smoke Closure Rows

M2592 should write source-only fixture smoke closure rows:

```text
fixture_closure_id
closure_family
definition_source_artifact
closure_source_artifact
fixture_source_declared
expected_schema_declared
fixture_hash_declared
fixture_smoke_replay_declared
external_runtime_required
external_runtime_executed_in_m2592
source_only_closure_materialized_in_m2592
validation_protocol_ready_in_m2592
external_validation_execution_allowed_in_m2592
status_pass
claim_boundary
```

Required closure families:

- `fixture_source_manifest_closure`
- `fixture_expected_schema_closure`
- `fixture_no_external_runtime_closure`
- `fixture_replayable_hash_and_smoke_closure`

Pass criteria:

- every fixture row has source, schema, hash, and smoke lineage sufficient for
  repo-local replay or inspection
- fixture smoke remains source-only and does not require external simulator
  installation, import, runtime execution, reset, policy action, environment
  step, rollout, or validation
- fixture lineage may support source-only blocker closure but not validation
  readiness, validation result, controller ranking, or driver performance

## Actor-Visibility Guard Rows

M2592 should write actor-visibility guard rows:

```text
actor_visibility_guard_id
blocker_family
actor_observation_shape
action_shape
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
rollout_outcome_actor_visible
validation_outcome_actor_visible
platform_selection_actor_visible
protocol_status_actor_visible
action_contract_mutation_detected
source_only_closure_materialized_in_m2592
validation_protocol_ready_in_m2592
external_validation_execution_allowed_in_m2592
status_pass
claim_boundary
```

Required blocker families:

- `external_state_extraction_boundary`
- `time_step_and_actuator_latency_contract`
- `failure_status_taxonomy_mapping`
- `source_only_fixture_smoke_lineage`

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- hidden/oracle, diagnostics, labels, backend status, reset outcome, rollout
  outcome, validation outcome, platform selection, and protocol status are
  false for actor-visible inputs
- action contract mutation is false
- no guard row permits rule switching or high-level oracle controller mode

## Claim-Boundary Checks

M2592 should write claim-boundary rows for:

- source-only adapter blocker closure materialized
- platform selected for validation
- validation protocol ready
- validation admission granted
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- HF4 discrepancy result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

The only future positive claim allowed after M2592, if every gate passes, is:

```text
repo_local_source_only_adapter_blocker_closure_materialized: true
```

All validation, platform, ranking, performance, paper, finite-window-vs-GRU,
current-sim, high-fidelity, and self-ID claims must remain false.

## M2592 Gate Matrix

M2592 should pass only if:

```text
source_artifacts_exist
m2591_design_artifact_exists
m2590_synthesis_accepted
external_state_extraction_closure_rows_complete
time_step_actuator_latency_closure_rows_complete
failure_status_taxonomy_closure_rows_complete
source_only_fixture_smoke_closure_rows_complete
actor_visibility_guard_rows_pass
claim_boundary_rows_pass
no_external_runtime_or_dependency_mutation
actor_action_contract_preserved
source_only_blocker_closure_claim_scoped
validation_readiness_and_execution_forbidden
```

The expected result class is:

```text
engineering_controller_route_a_hf3_source_only_adapter_blocker_closure_materialization_preflight_pass
```

Failure should be classified as:

- `contract_violation` if P0 `72/3`, no-oracle, no-label, or action mapping
  boundaries fail
- `lineage_invalid` if closure artifacts cannot be traced to M2588/M2590/M2591
  source evidence
- `metric_artifact` if a closure row is treated as validation readiness,
  validation result, ranking, or performance evidence
- `scenario_sampling_failure` if fixture lineage depends on untracked or
  non-replayable scenario material
- `behavior_regression` if a closure path requires changing deployed actor
  inputs or action semantics
- `objective_overfit` if fixed closure rows are expanded without creating
  concrete adapter evidence

## Follow-Up

Register and run:

```text
m2592-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-closure-materialization-preflight
```

M2592 may materialize source-only blocker closure evidence. It must not select a
platform, install/import/run external simulation, execute reset/action/step,
run rollouts or validation, train, rank, promote, compute success rates, or
claim validation readiness/result or driver performance.
