# M2563 Engineering Controller Route A Baseline HF3 Reset-Feasibility Execution Design

- status: completed
- decision: `route_to_hf3_reset_feasibility_execution_materialization_preflight`
- manifest: `experiments/manifests/m2563-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-design.json`
- parent synthesis: `docs/m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis.md`
- parent audit: `docs/m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit.md`
- HF3 preflight summary: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json`
- HF3 candidate source: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv`
- follow-up manifest: `experiments/manifests/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.json`
- next: `m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight`

## Scope

M2563 designs the Route A HF3 reset-feasibility execution materialization after
accepted HF3 low-cost pilot preflight evidence. The design prepares M2564 to
write machine-readable reset-execution candidate, backend availability, reset
request contract, reset execution plan, reset outcome schema, claim-boundary,
and gate artifacts.

M2563 is design-only. It does not install, import, or run external
high-fidelity simulation. It does not execute reset, policy actions, steps,
rollouts, training, replay, ranking, promotion, success-rate computation, or
validation.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines HF3 low-cost pilot as reset feasibility
and rollout feasibility only, with no controller-family verdict yet. M2564
should materialize the reset-feasibility execution boundary before any real
reset execution or rollout planning.

The M2564 artifacts must keep this ordering:

```text
backend availability boundary
-> reset request contract
-> reset execution plan
-> reset outcome schema
-> later reset execution audit
-> only then rollout feasibility design/execution
```

## Source Contracts

M2564 should bind to the accepted HF3 preflight contract:

```text
P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
pilot candidates = 2
candidate roles = stable avoidable/AEB-feasible, stable AES/AEB-infeasible
candidate admission = requires_m2560_reset_and_rollout_feasibility
external install/import/run in M2560/M2561 = false
policy action/reset/step/rollout execution in M2560/M2561 = false
```

Candidate labels, backend availability, reset feasibility status, and reset
outcomes are metadata and audit fields. They must not enter actor-visible
inputs.

## M2564 Required Artifacts

M2564 should write:

```text
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/summary.json
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_candidate_rows.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_backend_availability_checks.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_request_contract.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_plan.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_outcome_schema.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_claim_boundary_checks.csv
runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/materialization_gate_matrix.csv
docs/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.md
```

## Reset-Execution Candidate Rows

M2564 should write rows:

```text
reset_candidate_id
source_candidate_id
route_role_id
route_role_label
source_binding_id
source_binding_status
actor_observation_shape
action_shape
pilot_admission_status
reset_execution_status
reset_success_claim_allowed
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_reset_execution_candidate`
- `stable_aes_aeb_infeasible_reset_execution_candidate`

Pass criteria:

- exactly two rows exist
- P0 `72/3` is preserved
- pilot admission remains false
- reset execution status is `planned_not_executed_in_m2564`
- reset success claim is false

## Backend Availability Checks

M2564 should write rows:

```text
availability_check_id
backend_family
availability_source
install_allowed
import_allowed
runtime_execution_allowed
dependency_mutation_allowed
availability_claim_scope
status_pass
claim_boundary
```

Required checks:

- repo-local backend contract availability
- external Chrono/Chrono::Vehicle boundary
- black-box simulator boundary
- local dependency mutation boundary

Pass criteria:

- no dependency install is allowed
- no external package import is allowed
- no runtime simulation execution is allowed
- availability status is an audit field, not an actor input

## Reset Request Contract

M2564 should write request contract rows:

```text
request_contract_id
reset_candidate_id
backend_family
scenario_spec_id
seed_policy
actor_observation_shape
action_shape
actor_input_mutation_allowed
oracle_field_allowed
metadata_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- every reset candidate has a request contract
- P0 `72/3` is preserved
- actor input mutation is false
- oracle fields and metadata visibility are false

## Reset Execution Plan

M2564 should write reset execution plan rows:

```text
reset_plan_id
reset_candidate_id
backend_family
requires_backend_availability
requires_reset_request_contract
reset_execution_allowed_in_m2564
policy_action_allowed_in_m2564
environment_step_allowed_in_m2564
rollout_execution_allowed_in_m2564
required_before_reset_success_claim
status_pass
claim_boundary
```

Pass criteria:

- every reset candidate has a reset plan
- reset execution remains false in M2564
- policy action, environment step, and rollout execution remain false
- each row names the later execution artifact required before reset success
  can be claimed

## Reset Outcome Schema

M2564 should write reset outcome schema rows:

```text
outcome_field
field_family
actor_visible_allowed
required_for_execution_audit
allowed_to_support_reset_success_after_execution
allowed_to_support_validation
status_pass
claim_boundary
```

Required outcome fields:

- backend_available
- reset_request_valid
- reset_attempted
- reset_status
- actor_view_available
- diagnostics_available
- failure_reason
- execution_timestamp

Pass criteria:

- all required outcome fields are present
- no outcome field is actor-visible
- reset success remains false until a later execution artifact records it
- validation remains false even after reset success unless rollout and
  validation gates are separately passed

## Claim Boundary Checks

M2564 should write claim rows for:

- pilot admission
- reset execution
- reset success
- rollout feasibility
- high-fidelity validation readiness/result
- controller ranking or winner selection
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

All claim rows must be false in M2564.

## Gate Matrix

M2564 passes only if:

- all required artifacts exist
- exactly two reset candidates are represented
- backend availability checks pass without install/import/run
- reset request contracts preserve P0 `72/3` and no-oracle actor boundary
- reset execution plans are complete but not executed
- reset outcome schema rows are complete and metadata-only
- claim-boundary checks reject pilot admission, reset success, rollout success,
  validation, ranking, driver-performance, paper, FW-vs-GRU, current-sim, and
  self-ID claims
- no external simulator install/import/run occurs
- no policy action, reset execution, step, rollout, training, replay, PPO,
  ranking, winner selection, checkpoint promotion, success-rate, validation,
  driver-performance, paper, FW-vs-GRU, current-sim, high-fidelity validation,
  or self-ID claim is made

## Follow-Up

Route to M2564 materialization/preflight. M2564 may add a bounded source-only
materializer and tests to write the artifacts above. It must not execute reset,
step environments, run external simulation, execute policy actions, or
interpret reset-execution planning rows as validation or driver performance.
