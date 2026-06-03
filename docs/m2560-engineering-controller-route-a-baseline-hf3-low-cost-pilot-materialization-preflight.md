# M2560 Engineering Controller Route A Baseline HF3 Low-Cost Pilot Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_hf3_low_cost_pilot_materialization_preflight_pass`
- manifest: `experiments/manifests/m2560-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_hf3_low_cost_pilot_materialization.py`
- summary: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json`
- pilot candidates: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_pilot_candidate_rows.csv`
- reset-feasibility plan: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_reset_feasibility_plan.csv`
- rollout-feasibility plan: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_rollout_feasibility_plan.csv`
- external-boundary checks: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_external_backend_boundary_checks.csv`
- claim-boundary checks: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/hf3_claim_boundary_checks.csv`
- materialization gate matrix: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/materialization_gate_matrix.csv`
- next milestone: `m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed: `false`
- policy action/reset/step/rollout/training/ranking/validation claims: `false`

## Materialized Artifacts

M2560 materializes Route A HF3 low-cost pilot preflight
artifacts for exactly two candidates: stable avoidable/AEB-feasible
and stable AES/AEB-infeasible. The rows define reset and rollout
feasibility plans only. They do not execute either feasibility
check and do not grant pilot admission.

Accepted summary:

```text
status_pass: true
pilot_candidate_row_count: 2
reset_feasibility_row_count: 2
rollout_feasibility_row_count: 2
external_boundary_check_count: 6
claim_boundary_check_count: 7
materialization_gate_count: 8
candidate_rows_pilot_admitted: false
policy_action_allowed_in_m2560: false
environment_step_allowed_in_m2560: false
rollout_execution_allowed_in_m2560: false
claim_allowed_in_m2560: false
observation_shape: 72
action_shape: 3
materialization_gates_all_pass: true
```

## Result Boundary

M2560 is a source-level HF3 preflight materialization. It does
not install, import, or run an external simulator; does not
execute policy actions, resets, steps, or rollouts; does not
rank policies, select a winner, promote checkpoints, compute
success rates, validate driver performance, or provide paper/
FW-vs-GRU/current-sim/high-fidelity/self-ID evidence.

## Next Route

Route to:

```text
m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit
```
