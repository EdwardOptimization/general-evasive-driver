# M2775 Engineering Controller Route A Source-Only Action-Response Belief Intervention Delta Panel Materialization

## Metadata

- status: completed
- result class: `engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization_pass`
- summary: `runs/m2775_engineering_controller_route_a_source_only_action_response_belief_intervention_delta_panel_materialization/summary.json`
- source audit: `docs/m2774-engineering-controller-route-a-source-only-action-response-belief-intervention-materialization-result-audit.md`
- source dir: `runs/m2773_engineering_controller_route_a_source_only_action_response_belief_intervention_materialization_preflight`
- follow-up manifest: `experiments/manifests/m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit.json`
- next: `m2776-engineering-controller-route-a-source-only-action-response-belief-intervention-delta-panel-materialization-result-audit`

## Artifact Accounting

```text
source candidate rows: 32
source execution rows: 128
source trace rows: 10240
normal execution rows: 32
evaluator intervention execution rows: 96
delta rows: 96
role/dynamics aggregate rows: 24
intervention-condition aggregate rows: 3
mitigation reference guard rows: 8
actor guard rows: 7
claim boundary rows: 17
gate rows: 24
```

## Pairing Result

```text
pairing complete: True
missing pair count: 0
duplicate execution pair count: 0
trace pair accounting: True
matched trace pair rows: 7680
expected matched trace pair rows: 7680
```

## Delta Diagnostic Summary

```text
collision added delta rows: 0
collision removed delta rows: 0
road-departure added delta rows: 0
road-departure removed delta rows: 4
minimum obstacle clearance delta mean: 0.014285
minimum road margin delta mean: 0.063005
trace delta proxy delta mean: 1.260129
command response proxy delta mean: 0.048256
action L1 mean: 0.038371
physical action L1 mean: 0.038371
ego response L2 mean: 0.128866
```

These are source-only diagnostic deltas. They are not success-rate verdicts,
controller ranking metrics, driver-performance measurements, paper evidence,
high-fidelity validation evidence, or self-ID proof.

## Actor And Claim Boundary

```text
actor contract 72/action 3: True
hidden/oracle actor input detected: False
actor-visible label detected: False
mitigation reference rows guarded: True
new execution run: False
training run: False
ranking run: False
winner selected: False
success-rate verdict computed: False
driver-performance claim made: False
self-ID claim made: False
```

## Route Decision

Route to M2776 result audit before interpreting whether these source-only
normal-vs-intervention deltas warrant synthesis, artifact repair,
proof-extension design, or branch stop.
