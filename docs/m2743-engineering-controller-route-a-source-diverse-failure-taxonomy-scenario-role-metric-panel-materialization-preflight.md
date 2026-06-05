# M2743 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization_pass`
- scenario role rows: 6
- metric contract rows: 6
- target panel rows: 18
- offtrack target rows: 14
- collision caution rows: 1
- diagnostic success context rows: 3
- negative-context guard rows: 31
- same-surface blocked guard rows: 1
- protected/HF3 exclusion guard rows: 11
- gate matrix pass: True

## Boundary

M2743 materializes actor-invisible scenario-role metric panel artifacts from existing M2740 taxonomy rows only. It does not execute environments, train, validate, rank, or claim driver performance.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, source-family ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/summary.json`
- source_accounting_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/source_accounting_rows.csv`
- scenario_role_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/scenario_role_rows.csv`
- metric_contract_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/metric_contract_rows.csv`
- target_panel_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/target_panel_rows.csv`
- guardrail_context_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/guardrail_context_rows.csv`
- actor_contract_guard_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/actor_contract_guard_rows.csv`
- claim_boundary_rows: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/claim_boundary_rows.csv`
- gate_matrix: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/gate_matrix.csv`
- doc: `docs/m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit.json`
- next: `m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit`
