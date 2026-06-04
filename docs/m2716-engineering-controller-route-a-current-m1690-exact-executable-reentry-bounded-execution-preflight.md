# M2716 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Bounded Execution Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight_pass`
- candidate rows: 36
- exact execution rows: 36
- failure rows: 0
- accounted candidates: 36/36
- profile aggregate rows: 4
- anchor aggregate rows: 9
- protected exclusion audit rows: 12
- gate matrix pass: True

## Boundary

M2716 records bounded closed-loop diagnostic data only for the M2714 exact executable candidate rows. M2710 protected proposal rows remain excluded from execution and ordinary success denominators.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/summary.json`
- exact_execution_rows: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/exact_execution_rows.csv`
- profile_aggregate: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/profile_aggregate.csv`
- anchor_aggregate: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/anchor_aggregate.csv`
- protected_proposal_exclusion_audit_rows: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/protected_proposal_exclusion_audit_rows.csv`
- actor_contract_join_rows: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/actor_contract_join_rows.csv`
- claim_boundary_rows: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/claim_boundary_rows.csv`
- gate_matrix: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/gate_matrix.csv`
- failure_rows: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/failure_rows.csv`
- run_state: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/run_state.json`
- doc: `docs/m2716-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit.json`
- next: `m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit`
