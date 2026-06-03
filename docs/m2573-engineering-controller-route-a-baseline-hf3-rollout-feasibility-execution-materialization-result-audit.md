# M2573 Engineering Controller Route A Baseline HF3 Rollout-Feasibility Execution Materialization Result Audit

- status: completed
- decision: `accept_hf3_rollout_feasibility_execution_route_to_result_synthesis`
- manifest: `experiments/manifests/m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit.json`
- parent summary: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json`
- parent doc: `docs/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis.json`
- next: `m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis`

## Audit Verdict

M2573 accepts M2572 as Route A HF3 rollout-feasibility execution evidence. The
accepted claim remains operational: bounded repo-local reset, fixed M1154 policy
action, and backend-step execution were observed for both accepted HF3
candidates while preserving the P0 `72/3` actor/action contract.

M2573 does not accept rollout success, high-fidelity validation readiness or
result, driver-performance claim, controller ranking, checkpoint promotion,
success rate, paper evidence, finite-window-vs-GRU result, current-sim verdict,
or level3 self-identification claim.

## Evidence Checks

Accepted M2572 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_rollout_feasibility_execution_materialization_preflight_pass
source_artifacts_exist: true
rollout_request_row_count: 2
fixed_policy_source_row_count: 1
rollout_plan_row_count: 2
policy_action_audit_row_count: 16
backend_step_outcome_row_count: 16
actor_view_contract_row_count: 18
claim_boundary_check_count: 9
materialization_gate_count: 10
materialization_gates_all_pass: true
policy_action_executed: true
environment_step_executed: true
rollout_execution_run: true
step_counts_by_rollout_request: stable_aes_aeb_infeasible_hf3_rollout_request=8, stable_avoidable_aeb_feasible_hf3_rollout_request=8
backend_status_counts: running=16
terminated_by_backend_count: 0
truncated_by_backend_count: 0
actor_view_available_after_step_count: 16
reset_execution_observed_claim_allowed: true
rollout_feasibility_execution_observed_claim_allowed: true
rollout_success_claim_allowed: false
validation_claim_allowed: false
forbidden_claim_allowed_in_m2572: false
observation_shape: 72
action_shape: 3
```

Required artifact audit:

```text
summary.json: present
hf3_rollout_request_rows.csv: present
hf3_fixed_policy_source_rows.csv: present
hf3_rollout_plan_rows.csv: present
hf3_policy_action_audit_rows.csv: present
hf3_backend_step_outcome_rows.csv: present
hf3_rollout_actor_view_contract_rows.csv: present
hf3_claim_boundary_checks.csv: present
rollout_feasibility_gate_matrix.csv: present
milestone doc: present
```

Gate audit:

```text
source_artifacts_exist: pass
rollout_request_rows_complete: pass
fixed_policy_source_rows_pass: pass
rollout_plan_rows_pass: pass
policy_action_audit_rows_pass: pass
backend_step_outcome_rows_pass: pass
actor_view_contract_rows_pass: pass
claim_boundary_rows_pass: pass
actor_action_contract_preserved: pass
no_forbidden_execution_or_claim_flags: pass
```

## Supported Claims

Supported:

- HF3 rollout-feasibility execution artifacts are present for Route A
- exactly two rollout requests are represented
- stable avoidable/AEB-feasible and stable AES/AEB-infeasible are represented
- exactly one fixed policy source is used: M1154 public-base `alpha_0_05`
- fixed policy source is not ranked, compared, or promoted
- both requests completed eight policy-action and backend-step audit rows
- all backend-step rows report actor-view availability after step
- actor-view contract rows preserve P0 `72/3`
- hidden/oracle actor input, diagnostics, taxonomy labels, backend statuses,
  reset outcomes, and rollout outcomes remain outside actor-visible input
- no external high-fidelity package was installed, imported, or run
- only `reset_execution_observed` and
  `rollout_feasibility_execution_observed` are allowed operational claims

## Rejected Claims

Not supported:

- pilot admission
- rollout success
- high-fidelity validation readiness or result
- external simulator behavior transfer
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2572/M2573 execute a short repo-local feasibility smoke only. They do not
measure scenario success, external high-fidelity behavior, controller-family
advantage, or driver performance.

## Failure Taxonomy

No M2572/M2573 failure is accepted for:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 feasibility route.
- `objective_overfit`: the new action/step rows can be overclaimed if treated
  as rollout success, validation, or public benchmark evidence.
- `scenario_sampling_failure`: not triggered here, but the evidence covers only
  two HF3 candidates and a short eight-step horizon.

## Next Route

Route to:

```text
m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis
```

M2574 should synthesize M2572/M2573 and decide whether to continue to bounded
validation-readiness boundary design, repair an artifact/contract/policy-source
issue, pivot, or stop. It must not claim rollout success, validation, driver
performance, ranking, paper evidence, or self-ID.
