# M2747 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Bounded Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2746_route_to_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_result_synthesis`
- manifest: `experiments/manifests/m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-audit.json`
- audit doc: `docs/m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-audit.md`
- parent summary: `runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/summary.json`
- parent doc: `docs/m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-synthesis.json`
- next: `m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-synthesis`

## Audit Summary

M2747 accepts M2746 as a complete and claim-safe bounded role-panel diagnostic
execution preflight. M2746 produced the required artifacts, accounted for every
M2743 offtrack target candidate, preserved guardrail rows outside execution and
ordinary denominators, and registered this result-audit route before
interpretation.

Accepted M2746 artifact counts:

```text
summary status_pass: true
required artifacts present: true
candidate rows: 14
resolved candidates: 14
candidate execution rows: 14
candidate execution failure rows: 0
guardrail context rows: 5
actor-contract guard rows: 18
claim-boundary rows: 34
gate rows: 21
gate_matrix_pass: true
```

Candidate accounting is complete:

```text
M2693 candidates: 7
M2716 candidates: 7
resolved candidate count: 14
profile under test: L3_online_gru for all resolved rows
failure rows: 0
```

## Diagnostic Evidence

M2746 produced new closed-loop diagnostic rows over the M2743
`offtrack_containment_target` surface. These rows are useful Route A engineering
diagnostics, but they are not a performance verdict and do not support
validation, ranking, current-sim, paper, high-fidelity, full-driver, or self-ID
interpretation.

```text
overall diagnostic outcome:
  diagnostic_success_count: 1
  diagnostic_collision_count: 1
  diagnostic_offtrack_count: 9
  diagnostic_speed_too_low_count: 3

termination counts:
  obstacle_collision: 1
  off_track: 9
  speed_too_low: 3
  unset_or_completed: 1
```

The diagnostic surface is still weak. Only 1 of 14 rows is a diagnostic
success context, while the rest preserve offtrack, speed-too-low, collision,
or unset/completed termination evidence. M2747 keeps this weakness visible
instead of rebranding the row accounting as a success-rate verdict.

M2746 recorded `success_rate_metric_recorded: true`, but also recorded
`success_rate_verdict_claim_made: false`. M2747 preserves that boundary:
diagnostic row counts may be cited as artifact accounting, not as source-family
ranking, task-family ranking, profile ranking, controller ranking, repair
success, validation readiness, driver performance, current-sim verdict, paper
evidence, high-fidelity result, full ideal driver completion, or
self-identification.

## Guardrail Audit

M2746 preserved the exclusion surface:

```text
guardrail context rows: 5
collision caution guard rows: 1
diagnostic success context rows: 3
negative-context guard rows: 31
blocked same-surface guard rows: 1
protected/HF3 exclusion guard rows: 11
guardrail_execution: false
collision_caution_execution: false
diagnostic_success_context_execution: false
negative_context_execution: false
blocked_same_surface_execution: false
protected_hf3_execution: false
guardrail_rows_in_success_denominator: false
```

Collision caution, diagnostic success context, negative-context, blocked
same-surface, protected, and HF3 rows were not executed by M2746 and remain
outside ordinary success denominators. This preserves the M2745 design boundary
and prevents guardrail rows from becoming hidden positive or negative training
targets.

## Actor And Claim Boundary

M2746 preserved the actor contract:

```text
observation shape: 72
action shape: 3
action mapping: [steer, throttle, brake]
hidden/oracle actor input detected: false
actor input contract changed: false
scenario-role labels actor visible: false
metric labels actor visible: false
target labels actor visible: false
protected labels actor visible: false
blocker labels actor visible: false
route labels actor visible: false
success/progress labels actor visible: false
verdict labels actor visible: false
active config overwritten: false
repair overlay applied: false
```

Claim-boundary rows pass:

```text
actor-contract guard rows passing: true
claim-boundary rows: 34
gate rows: 21
gate_matrix_pass: true
ranking_run: false
winner_selected: false
checkpoint_promoted: false
repair_success_claim_made: false
driver_performance_claim_made: false
validation_readiness_claim_made: false
validation_result_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
full_ideal_driver_completion_claim_made: false
level3_self_id_claim_made: false
```

## Route Decision

M2747 accepts M2746 as complete and claim-safe, but rejects direct
interpretation. The branch has now designed, materialized, audited, executed,
and audited a source-diverse failure-taxonomy scenario-role metric panel. The
new data are diagnostic and mostly weak. Another immediate narrow execution
would risk local search unless a synthesis milestone identifies a changed
evidence surface.

Decision:

```text
accept_m2746_route_to_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_result_synthesis
```

Next:

```text
m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-synthesis
```

M2748 must synthesize the M2742-M2747 role-panel branch before any follow-up
execution, repair route, validation, ranking, performance, paper, current-sim,
high-fidelity, full ideal driver, or self-ID claim. The synthesis should answer
whether the branch should continue, pivot, stop, or promote to a different
bounded Route A evidence branch.

## Rejected Claims

```text
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
profile ranking
task-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
