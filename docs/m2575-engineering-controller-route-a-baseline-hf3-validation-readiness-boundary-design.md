# M2575 Engineering Controller Route A Baseline HF3 Validation-Readiness Boundary Design

- status: completed
- decision: `route_to_hf3_validation_readiness_boundary_materialization_preflight`
- manifest: `experiments/manifests/m2575-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-design.json`
- parent synthesis: `docs/m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis.md`
- parent audit: `docs/m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit.md`
- parent materialization summary: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json`
- follow-up manifest: `experiments/manifests/m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight.json`
- next: `m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight`

## Design Verdict

M2575 designs the boundary artifacts required before Route A HF3
rollout-feasibility evidence can be routed toward later high-fidelity
validation planning. The next milestone may materialize validation-readiness
request, evidence-admission, platform-boundary, dependency-policy,
scenario-discrepancy-question, actor-input-isolation, claim-boundary, and gate
rows.

M2575 does not claim validation readiness. M2576 should materialize boundary
rows only. Neither milestone may install, import, or run an external simulator,
execute new resets/actions/steps/rollouts, run validation, train, rank,
promote, compute success rates, or claim driver performance.

## Route-Plan Binding

`docs/post-m2470-route-plan.md` defines HF3 and HF4 as:

```text
HF3:
  reset feasibility and rollout feasibility only
  no controller-family verdict yet

HF4:
  which current-sim failures reproduce
  which disappear under higher fidelity
  which new failures appear
  whether current-sim remains a valid mining layer
```

M2576 should materialize the readiness boundary for asking those HF4 questions
later. It must not answer them yet.

## Source Evidence

Accepted source boundary:

```text
M2574 synthesis decision: continue_to_hf3_validation_readiness_boundary_design
M2573 audit decision: accept_hf3_rollout_feasibility_execution_route_to_result_synthesis
M2572 status_pass: true
rollout requests: 2
fixed M1154 policy source rows: 1
rollout plans: 2
policy-action audit rows: 16
backend step/outcome rows: 16
actor-view contract rows: 18
claim-boundary checks: 9
materialization gates: 10/10 pass
actor contract: P0 observation 72 / action 3
allowed operational claims: reset execution observed, rollout-feasibility execution observed
rollout success claim: false
validation claim: false
ranking/promotion/driver-performance/self-ID claim: false
external high-fidelity simulation install/import/run: false
```

## M2576 Artifact Contract

M2576 should write:

```text
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/summary.json
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_validation_readiness_request_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_evidence_admission_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_platform_boundary_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_dependency_policy_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_scenario_discrepancy_question_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_actor_input_isolation_rows.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/hf3_claim_boundary_checks.csv
runs/m2576_engineering_controller_route_a_hf3_validation_readiness_boundary/validation_readiness_gate_matrix.csv
docs/m2576-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-materialization-preflight.md
```

## Validation-Readiness Request Rows

M2576 should write two request rows:

```text
readiness_request_id
source_rollout_request_id
route_role_id
candidate_role_label
actor_observation_shape
action_shape
accepted_feasibility_evidence
validation_admission_allowed
validation_execution_allowed_in_m2576
external_simulation_allowed_in_m2576
status_pass
claim_boundary
```

Required rows:

- `stable_avoidable_aeb_feasible_validation_readiness_request`
- `stable_aes_aeb_infeasible_validation_readiness_request`

Pass criteria:

- exactly two rows exist
- both rows map to accepted M2572 rollout requests
- both rows preserve P0 `72/3`
- validation admission remains false
- validation execution and external simulation remain false

## Evidence Admission Rows

M2576 should write admission rows:

```text
evidence_admission_id
readiness_request_id
source_artifact
source_evidence_type
accepted_as_boundary_input
accepted_as_validation_result
accepted_as_driver_performance
accepted_as_ranking_evidence
status_pass
claim_boundary
```

Required source evidence types:

- `m2572_rollout_feasibility_execution_summary`
- `m2572_policy_action_audit_rows`
- `m2572_backend_step_outcome_rows`
- `m2572_actor_view_contract_rows`
- `m2573_result_audit`
- `m2574_result_synthesis`

Pass criteria:

- source artifacts exist
- every row is accepted only as boundary input
- validation result, driver performance, and ranking evidence are false

## Platform Boundary Rows

M2576 should write platform boundary rows:

```text
platform_boundary_id
platform_layer
platform_scope
repo_local_adapter_evidence_allowed
external_high_fidelity_execution_allowed_in_m2576
external_validation_result_allowed
preferred_future_platform_direction
status_pass
claim_boundary
```

Required layers:

- `repo_local_current_sim_adapter`
- `external_high_fidelity_vehicle_dynamics_layer`
- `future_hf4_discrepancy_report_layer`

Pass criteria:

- repo-local adapter evidence is admitted only as feasibility/readiness input
- external execution is false in M2576
- validation result is false in M2576
- preferred future platform direction remains open/auditable vehicle dynamics
  such as Chrono/Chrono::Vehicle, not a black-box-only dependency

## Dependency Policy Rows

M2576 should write dependency policy rows:

```text
dependency_policy_id
dependency_family
install_allowed_in_m2576
import_allowed_in_m2576
runtime_execution_allowed_in_m2576
dependency_mutation_allowed_in_m2576
future_validation_allowed_after_readiness_audit
status_pass
claim_boundary
```

Required dependency families:

- `chrono_vehicle_or_equivalent_open_backend`
- `black_box_industry_demonstration_backend`
- `repo_local_current_sim_backend`

Pass criteria:

- install/import/runtime execution/dependency mutation are false in M2576
- future validation remains conditional on later audited readiness and explicit
  validation manifest

## Scenario-Discrepancy Question Rows

M2576 should write HF4 question rows:

```text
discrepancy_question_id
route_role_id
hf4_question
requires_external_validation_execution
answer_allowed_in_m2576
driver_performance_claim_allowed
status_pass
claim_boundary
```

Required HF4 questions:

- current-sim failure reproduces
- current-sim failure disappears
- new high-fidelity failure appears
- current-sim remains valid mining layer

Pass criteria:

- every row is a future question only
- every row requires later external validation execution
- answers, driver-performance claims, and current-sim verdicts are false

## Actor-Input Isolation Rows

M2576 should write actor-input isolation rows:

```text
actor_input_isolation_id
readiness_request_id
actor_observation_shape
action_shape
hidden_oracle_actor_input_detected
diagnostics_actor_visible
taxonomy_label_actor_visible
backend_status_actor_visible
reset_outcome_actor_visible
rollout_outcome_actor_visible
validation_outcome_actor_visible
status_pass
claim_boundary
```

Pass criteria:

- actor observation shape is `72`
- action shape is `3`
- all hidden/oracle, diagnostic, label, backend-status, reset-outcome,
  rollout-outcome, and validation-outcome actor-visible fields are false

## Claim Boundary Checks

M2576 should write claim-boundary rows for:

- validation-readiness boundary materialized
- validation admission
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- paper, FW-vs-GRU, current-sim, or self-ID claim

Only the operational claim `validation-readiness boundary materialized` may
become true after M2576 if all boundary rows pass. Validation admission,
validation readiness/result, rollout success, ranking, promotion, success
rate, driver performance, paper evidence, and self-ID remain false.

## Gate Matrix

M2576 should pass only if:

```text
source_artifacts_exist
validation_readiness_request_rows_complete
evidence_admission_rows_pass
platform_boundary_rows_pass
dependency_policy_rows_pass
scenario_discrepancy_question_rows_pass
actor_input_isolation_rows_pass
claim_boundary_rows_pass
actor_action_contract_preserved
no_forbidden_execution_or_claim_flags
```

The forbidden flags include external simulator install/import/run, dependency
mutation, actor input mutation, action contract mutation, reset execution,
policy action, environment step, rollout execution, validation execution,
training, replay, PPO, ranking, winner selection, checkpoint promotion,
success-rate computation, rollout success claim, validation readiness/result
claim, driver-performance claim, paper claim, finite-window-vs-GRU claim,
current-sim verdict claim, high-fidelity validation claim, and self-ID claim.

## Follow-Up

Route to M2576 validation-readiness boundary materialization preflight. M2576
should materialize static boundary artifacts only. If M2576 passes, the next
task should audit the boundary before any external validation design or
execution route is selected.
