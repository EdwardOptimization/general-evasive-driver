# M2552 Engineering Controller Route A Baseline HF1 P0 Parity Smoke Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_hf1_p0_parity_smoke_materialization_pass`
- manifest: `experiments/manifests/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_hf1_p0_parity_smoke_materialization.py`
- summary: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json`
- actor-visible field parity rows: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_actor_visible_field_parity_rows.csv`
- observation value-range checks: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_observation_value_range_checks.csv`
- action mapping parity checks: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_action_mapping_parity_checks.csv`
- external-backend boundary checks: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_external_backend_boundary_checks.csv`
- diagnostics exclusion checks: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_diagnostics_exclusion_checks.csv`
- materialization gate matrix: `runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/materialization_gate_matrix.csv`
- next milestone: `m2553-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-result-audit`
- external high-fidelity simulation installed/imported/executed: `false`
- policy rollout/training/ranking/winner/promotion/success-rate/validation claims: `false`

## Materialized Artifacts

M2552 materializes HF1 P0 parity-smoke artifacts for the Route A
baseline. The rows cover actor-visible field layout, observation
value ranges, action mapping, diagnostics exclusion, and external
adapter boundaries. The external rows are boundary checks only;
they do not install, import, or run external simulation.

Accepted summary:

```text
status_pass: true
actor_visible_field_parity_row_count: 7
p0_index_coverage_count: 72
observation_value_range_check_count: 5
action_mapping_check_count: 7
external_backend_boundary_check_count: 6
diagnostics_exclusion_check_count: 33
diagnostic_only_keys_checked_count: 33
observation_shape: 72
action_shape: 3
materialization_gates_all_pass: true
```

## Result Boundary

M2552 is an interface parity-smoke artifact. It does not rank
Route A policies, select a winner, promote a checkpoint, compute
success rates, validate driver performance, or provide paper/
FW-vs-GRU/current-sim/high-fidelity/self-ID evidence.

## Next Route

Route to:

```text
m2553-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-result-audit
```
