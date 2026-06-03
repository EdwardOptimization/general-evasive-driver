# M2561 Engineering Controller Route A Baseline HF3 Low-Cost Pilot Materialization Result Audit

- status: completed
- decision: `accept_hf3_low_cost_pilot_preflight_route_to_result_synthesis`
- manifest: `experiments/manifests/m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit.json`
- parent summary: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json`
- parent doc: `docs/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis.json`
- next: `m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis`

## Audit Verdict

M2561 accepts M2560 as source-level Route A HF3 low-cost pilot preflight
materialization evidence. The accepted claim is narrow: two pilot candidate
rows were materialized, reset-feasibility and rollout-feasibility plans were
written, external backend boundaries were checked, claim boundaries were
checked, and all M2560 gates passed.

M2561 does not accept pilot admission, reset success, rollout success,
high-fidelity validation readiness/result, driver-performance claim,
controller ranking, checkpoint promotion, success rate, paper evidence,
finite-window-vs-GRU result, current-sim verdict, or level3 self-identification
claim.

## Evidence Checks

Accepted M2560 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_low_cost_pilot_materialization_preflight_pass
source_artifacts_exist: true
pilot_candidate_row_count: 2
reset_feasibility_row_count: 2
rollout_feasibility_row_count: 2
external_boundary_check_count: 6
claim_boundary_check_count: 7
materialization_gate_count: 8
materialization_gates_all_pass: true
pilot_candidate_role_ids: stable_aes_aeb_infeasible, stable_avoidable_aeb_feasible
source_binding_status_counts: baseline_reference_binding=1, materialization_candidate_binding=1
candidate_rows_pilot_admitted: false
policy_action_allowed_in_m2560: false
environment_step_allowed_in_m2560: false
rollout_execution_allowed_in_m2560: false
claim_allowed_in_m2560: false
external_install_allowed: false
external_import_allowed: false
external_simulation_run_allowed: false
observation_shape: 72
action_shape: 3
```

Required artifact audit:

```text
summary.json: present
hf3_pilot_candidate_rows.csv: present
hf3_reset_feasibility_plan.csv: present
hf3_rollout_feasibility_plan.csv: present
hf3_external_backend_boundary_checks.csv: present
hf3_claim_boundary_checks.csv: present
materialization_gate_matrix.csv: present
milestone doc: present
```

Gate audit:

```text
source_artifacts_exist: pass
pilot_candidates_complete: pass
reset_feasibility_plan_complete: pass
rollout_feasibility_plan_complete: pass
external_backend_boundary_checks_pass: pass
claim_boundary_checks_pass: pass
actor_action_contract_preserved: pass
no_false_claim_flags: pass
```

## Supported Claims

Supported:

- HF3 low-cost pilot preflight artifacts are materialized for Route A
- exactly two pilot candidate rows are present
- stable avoidable/AEB-feasible and stable AES/AEB-infeasible are represented
- both candidate rows preserve P0 `72/3`
- both candidate rows remain not pilot-admitted
- reset and rollout feasibility plans are present without execution
- external backend boundary rows forbid install/import/run
- claim-boundary rows reject validation, ranking, performance, paper,
  FW-vs-GRU, current-sim, high-fidelity validation, and self-ID claims
- the branch is ready for bounded result synthesis before deciding execution
  design, repair, pivot, or stop

## Rejected Claims

Not supported:

- pilot admission
- reset success
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

The earlier mitigation-proof limitation remains unresolved. M2560/M2561 do
not repair driver behavior, run closed-loop policy rollouts, or evaluate
scenario success.

## Failure Taxonomy

No M2560/M2561 failure is accepted for:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 preflight route.
- `objective_overfit`: preflight rows must not be used as validation, ranking,
  or public-gate tuning evidence.
- `scenario_sampling_failure`: not triggered here, but execution design must
  separate reset feasibility from rollout feasibility and forbid immediate
  controller-family verdicts.

## Next Route

Route to:

```text
m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis
```

M2562 should synthesize M2560/M2561 and decide whether to continue to a
bounded reset-feasibility execution design, repair an artifact/contract/mapping
issue, pivot, or stop. It must not claim validation or driver performance.
