# M2572 Engineering Controller Route A Baseline HF3 Rollout-Feasibility Execution Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_hf3_rollout_feasibility_execution_materialization_preflight_pass`
- manifest: `experiments/manifests/m2572-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_hf3_rollout_feasibility_execution.py`
- summary: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json`
- rollout requests: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_request_rows.csv`
- fixed policy source: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_fixed_policy_source_rows.csv`
- rollout plans: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_plan_rows.csv`
- policy-action audit rows: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_policy_action_audit_rows.csv`
- backend step/outcome rows: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_backend_step_outcome_rows.csv`
- actor-view contract rows: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_rollout_actor_view_contract_rows.csv`
- claim-boundary checks: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/hf3_claim_boundary_checks.csv`
- gate matrix: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/rollout_feasibility_gate_matrix.csv`
- next milestone: `m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed: `false`
- training/ranking/success-rate/validation claims: `false`

## Materialized Artifacts

M2572 materializes Route A HF3 rollout-feasibility execution
artifacts for the two accepted reset candidates. The bounded
execution uses the repo-local `CurrentSimDynamicsBackend`, the
fixed M1154 public-base checkpoint, and the P0 `72/3` actor
contract. It does not run external high-fidelity simulation and
does not compare or promote controllers.

Accepted summary:

```text
status_pass: true
rollout_request_row_count: 2
fixed_policy_source_row_count: 1
rollout_plan_row_count: 2
policy_action_audit_row_count: 16
backend_step_outcome_row_count: 16
actor_view_contract_row_count: 18
claim_boundary_check_count: 9
materialization_gate_count: 10
target_horizon_steps: 8
step_counts_by_rollout_request: {'stable_aes_aeb_infeasible_hf3_rollout_request': 8, 'stable_avoidable_aeb_feasible_hf3_rollout_request': 8}
policy_action_executed: true
environment_step_executed: true
rollout_execution_run: true
reset_execution_observed_claim_allowed: true
rollout_feasibility_execution_observed_claim_allowed: true
rollout_success_claim_allowed: false
validation_claim_allowed: false
forbidden_claim_allowed_in_m2572: false
observation_shape: 72
action_shape: 3
materialization_gates_all_pass: true
```

## Result Boundary

M2572 supports only the operational claim that bounded
repo-local reset, fixed-policy action, and backend-step
execution were observed while preserving the P0 actor/action
contract. It does not support rollout success, high-fidelity
validation readiness/result, driver performance, controller
ranking, checkpoint promotion, success rate, paper evidence,
FW-vs-GRU, current-sim verdict, high-fidelity validation, or
self-ID.

## Next Route

Route to:

```text
m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit
```
