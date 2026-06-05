# M2725 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Candidate Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization_pass`
- candidate target rows: 31
- shared repair overlay rows: 15
- guardrail rows: 17
- actor contract rows: 9
- gate matrix pass: True

## Boundary

M2725 materializes repair candidates only. It does not overwrite active configs or execute environments.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/summary.json`
- source_accounting_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/source_accounting_rows.csv`
- candidate_target_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/candidate_target_rows.csv`
- shared_repair_overlay_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/shared_repair_overlay_rows.csv`
- guardrail_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/guardrail_rows.csv`
- actor_contract_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/actor_contract_rows.csv`
- claim_boundary_rows: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/claim_boundary_rows.csv`
- gate_matrix: `runs/m2725_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_candidate_materialization/gate_matrix.csv`
- doc: `docs/m2725-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2726-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-result-audit.json`
- next: `m2726-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-candidate-materialization-result-audit`
