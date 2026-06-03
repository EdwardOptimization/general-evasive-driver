# M2567 Engineering Controller Route A Baseline HF3 Measured Reset-Feasibility Execution Design

- status: completed
- decision: `route_to_hf3_measured_reset_feasibility_execution_materialization_preflight`
- manifest: `experiments/manifests/m2567-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-design.json`
- parent synthesis: `docs/m2566-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-synthesis.md`
- parent audit: `docs/m2565-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-audit.md`
- follow-up manifest: `experiments/manifests/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.json`
- next: `m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight`

## Design Verdict

M2567 designs a bounded reset-only execution layer for the two accepted HF3
reset candidates. The next milestone may call the repo-local backend reset API
and record whether a P0 actor view is available after reset.

M2567 does not execute reset. M2568 may execute reset only under the contract
below. Neither milestone may execute policy actions, step the environment, run
rollouts, train, rank controllers, compute success rates, or claim validation,
driver performance, paper evidence, finite-window-vs-GRU, current-sim verdict,
high-fidelity validation, or self-ID.

## Source Evidence

Accepted source boundary:

```text
M2564/M2565 status: accepted
reset candidates: 2
backend availability checks: 4
reset request contracts: 2
reset execution plans: 2
reset outcome schema rows: 8
claim-boundary checks: 8
materialization gates: 9/9 pass
actor contract: P0 observation 72 / action 3
external install/import/run: false
dependency mutation: false
pilot admission: false
reset execution in M2564/M2565: false
reset success claim: false
validation/ranking/driver-performance claim: false
```

## M2568 Artifact Contract

M2568 should write:

```text
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_request_rows.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_backend_probe_rows.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_execution_rows.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_actor_view_contract_rows.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_reset_outcome_rows.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_claim_boundary_checks.csv
runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/measured_reset_gate_matrix.csv
docs/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.md
```

## Measured Reset Request Rows

M2568 should write two request rows:

```text
reset_request_id
reset_candidate_id
route_role_id
backend_family
scenario_spec_id
seed
actor_observation_shape
action_shape
policy_action_allowed
environment_step_allowed
rollout_allowed
actor_input_mutation_allowed
status_pass
claim_boundary
```

Required requests:

- `stable_avoidable_aeb_feasible_measured_reset_request`
- `stable_aes_aeb_infeasible_measured_reset_request`

Pass criteria:

- exactly two request rows exist
- requests preserve P0 `72/3`
- no actor input mutation is allowed
- policy action, environment step, and rollout are false
- requests map to the two M2564 reset candidates

## Backend Probe Rows

M2568 should write:

```text
backend_probe_id
reset_request_id
backend_family
backend_module
backend_class
external_install_allowed
external_import_allowed
dependency_mutation_allowed
backend_reset_allowed_in_m2568
backend_step_allowed_in_m2568
status_pass
claim_boundary
```

Pass criteria:

- backend family is `repo_local_dynamics_backend_contract`
- backend module is `autodrift.high_fidelity_interface`
- backend class is `CurrentSimDynamicsBackend`
- external install/import and dependency mutation are false
- backend reset is allowed only for M2568 reset-only execution
- backend step remains false

## Reset-Only Execution Rows

M2568 should write:

```text
reset_execution_id
reset_request_id
reset_attempted
reset_status
actor_view_available
diagnostics_recorded
policy_action_executed
environment_step_executed
rollout_executed
reset_success_claim_allowed
status_pass
claim_boundary
```

Pass criteria:

- exactly two reset-only execution rows exist
- reset may be attempted by the repo-local backend reset API
- policy action, environment step, and rollout execution are false
- diagnostics are recorded for audit only and are not actor-visible
- reset success claim remains false until M2568 is audited

## Actor-View Contract Rows

M2568 should write:

```text
actor_view_check_id
reset_execution_id
actor_observation_shape
action_shape
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- no hidden/oracle actor inputs are detected
- diagnostics and taxonomy labels are not actor-visible

## Reset Outcome Rows

M2568 should write:

```text
outcome_check_id
reset_execution_id
backend_available
reset_request_valid
reset_attempted
actor_view_available
reset_status_present
reset_success_claim_allowed
validation_claim_allowed
status_pass
claim_boundary
```

Pass criteria:

- backend availability and request validity are recorded
- reset attempted and actor-view availability are recorded
- reset status is present
- reset success claim is false in M2568
- validation claim is false in M2568

## Claim Boundary Checks

M2568 should write claim-boundary rows for:

- pilot admission
- reset execution observed
- reset success
- rollout feasibility
- high-fidelity validation readiness/result
- controller ranking/winner
- driver-performance claim
- paper/FW-vs-GRU/current-sim/self-ID claim

Only the operational claim `reset execution observed` may become true after
M2568 if both reset-only execution rows pass. Reset success, rollout
feasibility, validation, ranking, driver performance, paper evidence, and
self-ID remain false.

## Gate Matrix

M2568 should pass only if:

```text
source_artifacts_exist
measured_reset_requests_complete
backend_probe_rows_pass
reset_only_execution_rows_pass
actor_view_contract_rows_pass
reset_outcome_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, policy action, environment step, rollout, training, replay, PPO,
ranking, winner selection, checkpoint promotion, success-rate computation,
driver-performance claim, paper claim, finite-window-vs-GRU claim,
current-sim verdict claim, high-fidelity validation claim, and self-ID claim.

## Next Route

Route to M2568 measured reset-feasibility execution materialization preflight.
M2568 may execute reset only through the repo-local backend reset API and must
not step the environment or execute policy actions.
