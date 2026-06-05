# M2746 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Bounded Execution Preflight

## Summary

- status: completed
- result class: `engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight_pass`
- candidate rows: 14
- resolved candidates: 14/14
- execution rows: 14
- failure rows: 0
- accounted candidates: 14/14
- M2693 candidates: 7
- M2716 candidates: 7
- diagnostic outcomes: success 1 collision 1 offtrack 9
- diagnostic termination counts: {'obstacle_collision': 1, 'off_track': 9, 'speed_too_low': 3, 'unset_or_completed': 1}
- guardrail contexts: 5
- collision caution guard rows: 1
- diagnostic success context rows: 3
- negative-context guard rows: 31
- blocked same-surface guard rows: 1
- protected/HF3 exclusion guard rows: 11
- gate matrix pass: True

## Boundary

M2746 records bounded closed-loop diagnostic data only for resolved M2743 offtrack target rows. Collision caution, diagnostic success context, negative-context, blocked same-surface, protected, and HF3 rows are guardrails only and remain outside execution and success denominators.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, source-family ranking, task-family ranking, profile ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-audit`
- follow-up manifest: `experiments/manifests/m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-audit.json`
