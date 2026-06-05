# M2738 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Bounded Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2737_route_to_post_negative_diagnostic_source_diverse_bounded_execution_result_synthesis`
- manifest: `experiments/manifests/m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.json`
- audit doc: `docs/m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.md`
- parent summary: `runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/summary.json`
- parent doc: `docs/m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight.md`
- follow-up manifest: `experiments/manifests/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.json`
- next: `m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis`

## Audit Summary

M2738 accepts M2737 as a complete and claim-safe bounded diagnostic execution
preflight. M2737 produced the required artifacts, accounted for every M2734
candidate row, preserved negative/context/blocker guardrails, and registered a
result-audit route before interpretation.

Accepted M2737 artifact counts:

```text
summary status_pass: true
candidate rows: 18
resolved candidates: 18
candidate execution rows: 18
candidate execution failure rows: 0
source-family aggregate rows: 2
task-family aggregate rows: 2
negative-context guard rows: 31
blocked-surface guard rows: 12
actor-contract guard rows: 13
claim-boundary rows: 35
gate rows: 21
gate_matrix_pass: true
```

Candidate accounting is complete:

```text
M2693 candidates: 9
M2716 candidates: 9
resolution status: 18 resolved_to_current_m1690_workload
profile under test: L3_online_gru for all resolved rows
failure rows: 0
```

## Diagnostic Evidence

M2737 produced new closed-loop diagnostic rows. The outcome is useful Route A
engineering diagnostic evidence, but it remains offtrack-dominated and does not
support performance, validation, ranking, current-sim, paper, high-fidelity,
full-driver, or self-ID interpretation.

```text
overall diagnostic outcome:
  success: 3/18
  obstacle_collision: 1/18
  off_track: 14/18

source-family diagnostics:
  M2693 source_diverse_current_sim_offtrack:
    candidate rows: 9
    execution rows: 9
    success diagnostic rate: 1/9
    collision diagnostic rate: 1/9
    offtrack diagnostic rate: 7/9

  M2716 exact_executable_reentry_baseline:
    candidate rows: 9
    execution rows: 9
    success diagnostic rate: 2/9
    collision diagnostic rate: 0/9
    offtrack diagnostic rate: 7/9

task-family diagnostics:
  T4:
    candidate rows: 10
    execution rows: 10
    success diagnostic rate: 1/10
    collision diagnostic rate: 0/10
    offtrack diagnostic rate: 9/10

  T5:
    candidate rows: 8
    execution rows: 8
    success diagnostic rate: 2/8
    collision diagnostic rate: 1/8
    offtrack diagnostic rate: 5/8
```

These aggregate rates are diagnostic row summaries only. M2738 rejects using
them as source-family ranking, profile ranking, task-family ranking, controller
ranking, winner selection, success-rate verdict, repair success, validation
readiness, driver performance, paper, current-sim, high-fidelity, full ideal
driver, or self-identification claims.

## Guardrail Audit

M2737 preserved the exclusion surface:

```text
negative-context guard rows: 31
blocked-surface guard rows: 12
blocked families:
  same_surface_repair_loop: 1
  protected_mitigation_blocker: 10
  hf3_source_dependency_blocker: 1

guard execution admitted: false for all 43 guard rows
guard execution run: false for all 43 guard rows
protected rows in success denominator: false for all guard and execution rows
actor visible guard labels: false for all guard rows
```

This preserves the M2736 design boundary. M2728 negative context rows, direct
same-surface repair rows, protected blocker rows, and HF3 blocker rows were not
executed by M2737 and remain outside ordinary success denominators.

## Actor And Claim Boundary

M2737 preserved the actor contract:

```text
observation shape: 72
action shape: 3
action mapping: [steer, throttle, brake]
hidden/oracle actor input detected: false
actor input contract changed: false
target labels actor visible: false
protected labels actor visible: false
blocker labels actor visible: false
route labels actor visible: false
verdict labels actor visible: false
active config overwritten: false
```

Claim-boundary rows pass:

```text
allowed M2737 artifact/diagnostic claims: 14/14 made and passing
blocked interpretation claims: 21/21 not made and passing
gate rows: 21/21 passing
```

## Decision

M2738 accepts M2737 as complete and claim-safe bounded diagnostic execution
evidence, but rejects direct interpretation. The branch now has new
source-diverse closed-loop diagnostic data after M2728 negative same-surface
repair diagnostics, yet the result remains offtrack-dominated. The next
bounded step is a synthesis milestone, not another immediate execution.

Decision:

```text
accept_m2737_route_to_post_negative_diagnostic_source_diverse_bounded_execution_result_synthesis
```

Next:

```text
m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis
```

M2739 must answer the synthesis questions before any follow-up execution,
repair route, validation, ranking, performance, paper, current-sim,
high-fidelity, full ideal driver, or self-ID claim.

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
