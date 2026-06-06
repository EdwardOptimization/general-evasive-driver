# M2935 Engineering Controller Route A Offtrack-Dominant Repair Execution Outcome-Shift Localization Result Audit

## Metadata

- status: completed
- decision: `accept_m2934_outcome_shift_localization_claim_safe_route_to_m2936_repair_redesign`
- manifest: `experiments/manifests/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.json`
- audit doc: `docs/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.md`
- parent summary: `runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight/summary.json`
- parent doc: `docs/m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight.md`
- follow-up manifest: `experiments/manifests/m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign.json`
- next: `m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign`

## Audit Summary

M2935 accepts M2934 as a complete and claim-safe outcome-shift localization preflight. M2934 joined all 56 M2919 baseline diagnostic rows to the M2931 fixed-candidate repair diagnostic rows, preserved the 38 offtrack repair targets and 18 non-offtrack context rows, preserved all 27 coverage constraints and guardrails, and registered this result-audit route before interpretation.

Accepted M2934 artifact counts:

```text
summary status_pass: true
gate_matrix_pass: true
outcome shift rows: 56
offtrack target rows: 38
context rows: 18
coverage constraint audit rows: 27
source aggregate rows: 4
task aggregate rows: 2
actor-contract guard rows: 11
claim-boundary rows: 29
gate rows: 21
guardrails preserved: true
actor-contract guards pass: true
```

## Outcome-Shift Evidence

M2934 preserves the full same-panel transition accounting:

```text
offtrack -> success: 4
offtrack -> offtrack: 24
offtrack -> collision: 4
offtrack -> speed_too_low: 6
success -> offtrack: 5
success -> collision: 4
success -> success: 2
collision -> collision: 1
collision -> offtrack: 1
collision -> speed_too_low: 1
speed_too_low -> speed_too_low: 3
speed_too_low -> offtrack: 1
```

This is useful localization evidence, not a repair-success result. The fixed M2655 candidate repaired only 4 of 38 offtrack target rows to success. It left 24 offtrack targets offtrack and shifted 10 offtrack targets into collision or speed-too-low. It also regressed 9 previously successful context rows into offtrack or collision.

M2934 also correctly separates transition-label buckets from non-exclusive diagnostic accounting:

```text
M2919 diagnostic outcomes: success 11, collision 3, offtrack 38, speed_too_low 4
M2931 transition-label buckets: success 6, collision 9, offtrack 31, speed_too_low 10
M2931 diagnostic outcomes: success 6, collision 9, offtrack 32, speed_too_low 10
```

The M2931 offtrack diagnostic count remains 32 because one row overlaps collision and off_track diagnostic accounting. That overlap must remain visible; it cannot be hidden to make the transition labels look cleaner.

## Guardrail Audit

M2934 preserved the protected context:

```text
M2877 guard rows executed: false
Route B context executed: false
Route C context executed: false
coverage constraints preserved: true
shortcut exclusions preserved: true
actor shape: observation 72, action 3
hidden/oracle actor input detected: false
future-target actor input required: false
ranking claim made: false
repair-success claim made: false
driver-performance claim made: false
```

The 27 M2928 coverage constraints remain constraints rather than rankings. The 7 shortcut-exclusion families remain actor-invisible and block hidden dynamics, oracle labels, route labels, progress labels, rank/winner shortcuts, overclaim shortcuts, and direct execution/training shortcuts.

## Decision

M2935 accepts M2934 as complete and claim-safe, but rejects direct continuation into another fixed-candidate repair execution. The localized failure is a tradeoff problem:

```text
persistent offtrack: 24/38 offtrack targets
collision/speed substitution: 10/38 offtrack targets
success-context regression: 9 context rows
clean offtrack repair: 4/38 offtrack targets
```

The next route should be a bounded design-only repair redesign that uses this transition surface as constraints. It must not optimize only the offtrack target rows. It must preserve context rows, explicitly block collision and low-speed substitution, and avoid any ranking, validation, promotion, performance, paper, high-fidelity, finite-window-vs-GRU, full-driver, or self-ID claim.

Decision:

```text
accept_m2934_outcome_shift_localization_claim_safe_route_to_m2936_repair_redesign
```

Next:

```text
m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign
```

## Rejected Claims

```text
repair success
driver performance
validation readiness or result
source/task/checkpoint/environment/window/severity/time-band ranking
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
