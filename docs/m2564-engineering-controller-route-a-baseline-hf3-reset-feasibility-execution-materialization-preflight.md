# M2564 Engineering Controller Route A Baseline HF3 Reset-Feasibility Execution Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_hf3_reset_feasibility_execution_materialization_preflight_pass`
- manifest: `experiments/manifests/m2564-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_hf3_reset_feasibility_execution_materialization.py`
- summary: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/summary.json`
- reset candidates: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_candidate_rows.csv`
- backend availability checks: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_backend_availability_checks.csv`
- reset request contract: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_request_contract.csv`
- reset execution plan: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_execution_plan.csv`
- reset outcome schema: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_reset_outcome_schema.csv`
- claim-boundary checks: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/hf3_claim_boundary_checks.csv`
- materialization gate matrix: `runs/m2564_engineering_controller_route_a_hf3_reset_feasibility_execution/materialization_gate_matrix.csv`
- next milestone: `m2565-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed: `false`
- reset/policy-action/step/rollout/training/ranking/validation claims: `false`

## Materialized Artifacts

M2564 materializes Route A HF3 reset-feasibility execution
boundary artifacts for the two accepted pilot candidates. The
rows define backend availability, reset request contracts, reset
execution plans, reset outcome schema, and claim boundaries. They
do not execute reset or grant pilot admission.

Accepted summary:

```text
status_pass: true
reset_execution_candidate_row_count: 2
backend_availability_check_count: 4
reset_request_contract_count: 2
reset_execution_plan_count: 2
reset_outcome_schema_row_count: 8
claim_boundary_check_count: 8
materialization_gate_count: 9
reset_execution_allowed_in_m2564: false
policy_action_allowed_in_m2564: false
environment_step_allowed_in_m2564: false
runtime_execution_allowed: false
claim_allowed_in_m2564: false
observation_shape: 72
action_shape: 3
materialization_gates_all_pass: true
```

## Result Boundary

M2564 is a source-level reset-feasibility execution boundary
materialization. It does not install, import, or run an external
simulator; does not execute reset, policy actions, steps, or
rollouts; does not rank policies, select a winner, promote
checkpoints, compute success rates, validate driver performance,
or provide paper/FW-vs-GRU/current-sim/high-fidelity/self-ID
evidence.

## Next Route

Route to:

```text
m2565-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-materialization-result-audit
```
