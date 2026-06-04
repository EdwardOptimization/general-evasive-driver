# M2719 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Failure Taxonomy Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_pass`
- exact execution taxonomy rows: 36
- protected exclusion taxonomy rows: 12
- diagnostic success rows: 3
- obstacle collision rows: 2
- offtrack rows: 31
- profile context rows: 4
- anchor context rows: 9
- gate matrix pass: True

## Boundary

M2719 materializes taxonomy rows from existing M2716 diagnostics only. It does not run environments or rank profiles.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/summary.json`
- source_accounting_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/source_accounting_rows.csv`
- taxonomy_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/taxonomy_rows.csv`
- taxonomy_aggregate_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/taxonomy_aggregate_rows.csv`
- profile_taxonomy_context_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/profile_taxonomy_context_rows.csv`
- anchor_taxonomy_context_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/anchor_taxonomy_context_rows.csv`
- actor_contract_join_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/actor_contract_join_rows.csv`
- claim_boundary_rows: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/claim_boundary_rows.csv`
- gate_matrix: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/gate_matrix.csv`
- doc: `docs/m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit.json`
- next: `m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit`
