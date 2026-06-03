# M2587 Engineering Controller Route A Baseline HF3 Source-Only Adapter Readiness Blocker Design

- status: completed
- decision: `route_to_hf3_source_only_adapter_readiness_blocker_materialization_preflight`
- manifest: `experiments/manifests/m2587-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-design.json`
- parent synthesis: `docs/m2586-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-result-synthesis.md`
- parent audit: `docs/m2585-engineering-controller-route-a-baseline-hf3-validation-platform-protocol-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2584_engineering_controller_route_a_hf3_validation_platform_protocol_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-preflight.json`
- next: `m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-preflight`

## Design Verdict

M2587 designs the bounded artifacts required to turn the four source-only
adapter blockers identified by M2584/M2586 into explicit materialization rows.
M2588 should materialize blocker-definition evidence for external state
extraction, time-step and actuator latency, failure/status taxonomy mapping,
source-only fixture smoke lineage, actor-visibility guards, claim-boundary
checks, and a gate matrix.

M2587 does not close those blockers. M2588 must not treat blocker rows as
validation readiness, validation admission, validation protocol readiness, or
validation result. Neither milestone may select a platform, install or import
external simulation dependencies, run external simulation, execute resets,
execute policy actions, step environments, execute rollouts, run validation,
train, rank, promote, compute success rates, or claim driver performance.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines Route C as high-fidelity interface and
validation preparation without migrating the full training loop too early.
The relevant HF0/HF3 boundaries are:

```text
HF0:
  DynamicsBackend boundary
  reset/step API mapping
  time-step and actuator-latency contract
  state extraction boundary
  failure/status taxonomy

HF3:
  single-role stable avoidable pilot
  single-role stable AES pilot
  reset feasibility and rollout feasibility only
  no controller-family verdict yet
```

M2588 should materialize source-only adapter blocker rows that prepare those
interfaces. It must not run HF3 pilots or answer HF4 discrepancy questions.

## Source Evidence

Accepted source boundary:

```text
M2586 synthesis decision: continue_to_hf3_source_only_adapter_readiness_blocker_design
M2585 audit decision: accept_hf3_validation_platform_protocol_readiness_materialization_route_to_result_synthesis
M2584 status_pass: true
platform candidate rows: 3
dependency/import policy rows: 3
validation protocol skeleton rows: 2
source-only adapter prerequisite rows: 7
source-only adapter satisfied prerequisites: 3
source-only adapter missing prerequisites: 4
actor/action guard rows: 2
claim-boundary checks: 14
materialization gates: 10/10 pass
actor contract: P0 observation 72 / action 3
platform selected: false
dependency install/import/runtime execution: false
protocol skeleton defined: true
validation protocol ready claim: false
external validation execution allowed: false
```

The four remaining blockers are:

```text
external_state_extraction_boundary
time_step_and_actuator_latency_contract
failure_status_taxonomy_mapping
source_only_fixture_smoke_lineage
```

## M2588 Artifact Contract

M2588 should write:

```text
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/summary.json
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_external_state_extraction_boundary_rows.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_time_step_actuator_latency_contract_rows.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_failure_status_taxonomy_mapping_rows.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_source_only_fixture_smoke_lineage_rows.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_source_only_adapter_actor_visibility_guard_rows.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/hf3_source_only_adapter_claim_boundary_checks.csv
runs/m2588_engineering_controller_route_a_hf3_source_only_adapter_readiness_blocker/source_only_adapter_readiness_blocker_gate_matrix.csv
docs/m2588-engineering-controller-route-a-baseline-hf3-source-only-adapter-readiness-blocker-materialization-preflight.md
```

Every row family should include enough lineage to prove the blocker is defined
as a source-only adapter contract, not silently accepted as readiness:

```text
blocker_contract_defined_in_m2588: true
readiness_satisfied_in_m2588: false
external_validation_execution_allowed_in_m2588: false
status_pass: true
```

Actor guard and claim-boundary rows must also keep:

```text
actor_visible: false
hidden_or_oracle_actor_input_detected: false
```

wherever labels, diagnostics, backend status, reset outcome, rollout outcome,
validation outcome, platform selection, or protocol status might otherwise be
misread as actor-visible data.

## External State Extraction Boundary Rows

M2588 should write external state extraction boundary rows:

```text
state_boundary_id
boundary_family
source_artifact
adapter_contract_required_before_external_execution
backend_state_may_be_read_by_adapter
actor_visible
diagnostic_only
hidden_or_oracle_actor_input_detected
blocker_contract_defined_in_m2588
readiness_satisfied_in_m2588
external_validation_execution_allowed_in_m2588
status_pass
claim_boundary
```

Required boundary families:

- `ego_state_extraction_contract`
- `external_backend_state_mapping_contract`
- `diagnostic_state_redaction_contract`
- `validation_metadata_separation_contract`

Pass criteria:

- every row is source-only adapter contract evidence
- backend state may be read only by the adapter boundary, not by the deployed
  actor
- diagnostics, taxonomy labels, backend status, reset outcome, rollout
  outcome, validation outcome, platform selection, and protocol status remain
  actor-invisible
- no row implies readiness, platform selection, external execution, or
  validation result

## Time-Step And Actuator-Latency Contract Rows

M2588 should write time-step and actuator-latency rows:

```text
timing_contract_id
contract_family
source_artifact
adapter_contract_required_before_external_execution
simulation_time_step_defined
control_update_rate_defined
actuator_latency_mapping_defined
command_hold_or_delay_defined
actor_observation_shape
action_shape
action_contract_mutation_detected
blocker_contract_defined_in_m2588
readiness_satisfied_in_m2588
external_validation_execution_allowed_in_m2588
status_pass
claim_boundary
```

Required contract families:

- `simulation_time_step_contract`
- `control_update_rate_contract`
- `actuator_latency_mapping_contract`
- `command_hold_and_delay_contract`

Pass criteria:

- every row preserves P0 observation shape `72` and action shape `3`
- the deployed action mapping remains `[steer, throttle, brake]`
- timing and latency contracts are definitions only
- no reset/action/step/rollout/validation execution is allowed in M2588

## Failure/Status Taxonomy Mapping Rows

M2588 should write failure/status taxonomy mapping rows:

```text
status_mapping_id
mapping_family
source_artifact
adapter_contract_required_before_external_execution
backend_status_actor_visible
taxonomy_label_actor_visible
diagnostics_actor_visible
maps_to_repo_local_status_class
blocker_contract_defined_in_m2588
readiness_satisfied_in_m2588
external_validation_execution_allowed_in_m2588
status_pass
claim_boundary
```

Required mapping families:

- `reset_failure_status_mapping`
- `step_failure_status_mapping`
- `collision_or_contact_status_mapping`
- `validation_abort_status_mapping`

Pass criteria:

- taxonomy/status data may be represented for audit and adapter diagnostics
  only
- taxonomy labels, feasibility classes, backend statuses, diagnostics, reset
  outcomes, rollout outcomes, and validation outcomes remain outside actor
  inputs
- rows do not claim validation admission, validation protocol readiness,
  validation readiness, validation result, HF4 discrepancy result, or driver
  performance

## Source-Only Fixture Smoke Lineage Rows

M2588 should write source-only fixture smoke lineage rows:

```text
fixture_lineage_id
lineage_family
source_artifact
fixture_source_declared
expected_schema_declared
external_runtime_required
external_runtime_executed_in_m2588
replayable_artifact_hash_declared
blocker_contract_defined_in_m2588
readiness_satisfied_in_m2588
external_validation_execution_allowed_in_m2588
status_pass
claim_boundary
```

Required lineage families:

- `fixture_source_manifest_lineage`
- `fixture_expected_schema_lineage`
- `fixture_no_external_runtime_lineage`
- `fixture_replayable_artifact_hash_lineage`

Pass criteria:

- source-only fixture smoke lineage is declared without external runtime
- no external simulator install/import/run occurs
- no validation execution or rollout execution occurs
- fixture lineage is not platform selection or validation-result evidence

## Actor-Visibility Guard Rows

M2588 should write actor-visibility guard rows:

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
- hidden/oracle actor input is false
- diagnostics, taxonomy labels, backend status, reset outcome, rollout
  outcome, validation outcome, platform selection, and protocol status are
  false for actor-visible inputs
- action contract mutation is false

## Claim Boundary Checks

M2588 may set only this operational claim true:

- source-only adapter readiness blocker design materialized

All of these remain false:

- source-only adapter blockers closed
- platform selection
- validation protocol readiness
- validation admission
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- HF4 discrepancy result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- paper-level evidence
- finite-window-vs-GRU result
- current-sim verdict
- level3 self-identification evidence

## Gate Matrix

M2588 should pass only if:

```text
source_artifacts_exist
external_state_extraction_boundary_rows_complete
time_step_actuator_latency_contract_rows_complete
failure_status_taxonomy_mapping_rows_complete
source_only_fixture_smoke_lineage_rows_complete
actor_visibility_guard_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_blocker_closed_or_readiness_claim
no_platform_selection_or_external_execution
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, actor input mutation, action contract mutation, reset execution,
policy action, environment step, rollout execution, validation execution,
training, replay, PPO, ranking, winner selection, checkpoint promotion,
success-rate computation, platform-selection claim, validation protocol
readiness claim, validation admission claim, validation readiness claim,
validation result claim, rollout success claim, driver-performance claim,
paper claim, finite-window-vs-GRU claim, current-sim verdict claim,
high-fidelity validation claim, HF4 discrepancy result claim, and self-ID
claim.

## Follow-Up

Route to M2588 source-only adapter readiness blocker materialization preflight.
M2588 should materialize structured blocker-definition rows only. If M2588
passes, the next task should audit the materialization before any blocker
closure, platform selection, external dependency preparation, executable
validation protocol, validation admission, or validation execution design is
selected.
