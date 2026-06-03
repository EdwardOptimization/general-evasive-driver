# M2568 Engineering Controller Route A Baseline HF3 Measured Reset-Feasibility Execution Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_hf3_measured_reset_feasibility_execution_materialization_preflight_pass`
- manifest: `experiments/manifests/m2568-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_hf3_measured_reset_feasibility_execution.py`
- summary: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json`
- reset requests: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_request_rows.csv`
- backend probes: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_backend_probe_rows.csv`
- reset-only executions: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_measured_reset_execution_rows.csv`
- actor-view contract rows: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_actor_view_contract_rows.csv`
- reset outcome rows: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_reset_outcome_rows.csv`
- claim-boundary checks: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/hf3_claim_boundary_checks.csv`
- gate matrix: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/measured_reset_gate_matrix.csv`
- next milestone: `m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed: `false`
- policy-action/step/rollout/training/ranking/validation claims: `false`

## Materialized Artifacts

M2568 materializes Route A HF3 measured reset-feasibility
execution artifacts for the two accepted reset candidates. The
only execution performed is repo-local backend reset. M2568 does
not execute policy actions, environment steps, or rollouts.

Accepted summary:

```text
status_pass: true
measured_reset_request_row_count: 2
backend_probe_row_count: 2
reset_execution_row_count: 2
actor_view_contract_row_count: 2
reset_outcome_row_count: 2
claim_boundary_check_count: 8
materialization_gate_count: 9
reset_only_execution_run: true
reset_execution_attempted_count: 2
actor_view_available_count: 2
policy_action_executed: false
environment_step_executed: false
rollout_executed: false
reset_success_claim_allowed: false
reset_execution_observed_claim_allowed: true
forbidden_claim_allowed_in_m2568: false
observation_shape: 72
action_shape: 3
materialization_gates_all_pass: true
```

## Result Boundary

M2568 supports only the operational claim that repo-local reset
execution was observed and yielded actor-view contract rows for
both reset candidates. It does not support reset success, rollout
feasibility, validation readiness/result, driver performance,
controller ranking, paper evidence, FW-vs-GRU, current-sim
verdict, high-fidelity validation, or self-ID.

## Next Route

Route to:

```text
m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit
```
