# M2740 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Failure Taxonomy Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization_pass`
- execution taxonomy rows: 18
- negative-context taxonomy rows: 31
- blocked-guard taxonomy rows: 12
- diagnostic success context rows: 3
- collision failure rows: 1
- offtrack rows: 14
- source-family context rows: 2
- task-family context rows: 2
- guardrail context rows: 3
- gate matrix pass: True

## Boundary

M2740 materializes taxonomy rows from existing M2737 diagnostics and guardrails only. It does not run environments, execute policies, or rank source/task/profile families.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, source-family ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json`
- source_accounting_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/source_accounting_rows.csv`
- taxonomy_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/taxonomy_rows.csv`
- taxonomy_aggregate_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/taxonomy_aggregate_rows.csv`
- source_family_context_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/source_family_context_rows.csv`
- task_family_context_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/task_family_context_rows.csv`
- guardrail_context_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/guardrail_context_rows.csv`
- actor_contract_join_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/actor_contract_join_rows.csv`
- claim_boundary_rows: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/claim_boundary_rows.csv`
- gate_matrix: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/gate_matrix.csv`
- doc: `docs/m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit.json`
- next: `m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit`
