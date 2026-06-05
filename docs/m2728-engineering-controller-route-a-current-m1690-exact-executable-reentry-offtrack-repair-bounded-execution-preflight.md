# M2728 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Bounded Execution Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight_pass`
- candidate rows: 31
- repair execution rows: 31
- failure rows: 0
- accounted candidates: 31/31
- overlay application rows: 465
- guardrail audit rows: 17
- profile aggregate rows: 4
- anchor aggregate rows: 9
- active config overwritten: False
- gate matrix pass: True

## Boundary

M2728 records bounded closed-loop diagnostic repair data only for the M2725 candidate target rows. Guardrail and protected rows remain excluded from execution and ordinary success denominators.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/summary.json`
- repair_execution_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/repair_execution_rows.csv`
- candidate_execution_failure_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/candidate_execution_failure_rows.csv`
- profile_aggregate: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/profile_aggregate.csv`
- anchor_aggregate: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/anchor_aggregate.csv`
- repair_overlay_application_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/repair_overlay_application_rows.csv`
- guardrail_audit_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/guardrail_audit_rows.csv`
- actor_contract_join_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/actor_contract_join_rows.csv`
- claim_boundary_rows: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/claim_boundary_rows.csv`
- gate_matrix: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/gate_matrix.csv`
- run_state: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/run_state.json`
- doc: `docs/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-result-audit.json`
- next: `m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-result-audit`
