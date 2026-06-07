# M3070 Active Safety Driver v1 Direct-Action Failure Decomposition Result Audit

## Summary

- status: completed
- decision: `continue_to_m3071_direct_action_multi_failure_repair_contract_materialization_preflight`
- audited milestone: `m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight`
- next route: `m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight`

M3070 accepts M3069 as a complete and claim-safe direct-action
failure-decomposition materialization artifact. It does not accept M3069 as
validation, ranking, promotion, driver-performance verdict, current-sim verdict,
repair success, high-fidelity readiness, paper evidence, finite-window-vs-GRU
evidence, full-driver completion, or self-ID evidence.

## Artifact Audit

Accepted M3069 facts:

```text
status_pass: true
gate_matrix_pass: true
measurement rows preserved: 32/32
measurement failure rows: 0
direct-action failure mode rows: 31
direct-action actuation pressure rows: 13
direct-action recovery stability rows: 13
direct-action repair requirement rows: 7
claim boundary rows: 21
gate matrix rows: 26
success rows: 8
collision rows: 4
offtrack rows: 16
speed-too-low rows: 5
candidate success rows: 3
parent success rows: 5
candidate action_clip_fraction_mean: 0.042289676871790735
parent action_clip_fraction_mean: 0.026749368598236827
raw_action_abs_max: 2.2606801986694336
action_clip_fraction_mean: 0.03451952273501378
final_action_abs_max: 1.0
actor contract: 72/action 3
candidate output: direct_action_clipped [steer throttle brake]
runtime base policy required: false
```

M3069 preserved the full M3067 denominator and separated the active repair
pressure into explicit requirement families:

```text
p0 offtrack_containment_recovery: 16/32 rows
p0 t5_collision_guard: 4 T5 collision rows
p1 speed_floor_recovery: 5 speed_too_low rows
p1 direct_action_actuation_pressure: raw_action_abs_max 2.2606801986694336 and all 32 rows with raw action above final bounds
p1 success_preservation: preserve 8 success rows across candidate and parent bindings
p1 stability_clearance_tradeoff: 18 high-sideslip rows despite positive aggregate clearance delta
p0 claim_boundary_guard: M3070 audit required before repair claims
```

The group-level decomposition is material for the next route:

```text
candidate binding: 3/16 success, 2 collision, 9 offtrack, 3 speed_too_low
parent binding: 5/16 success, 2 collision, 7 offtrack, 2 speed_too_low
T4: 3/16 success, 0 collision, 9 offtrack, 4 speed_too_low
T5: 5/16 success, 4 collision, 7 offtrack, 1 speed_too_low
candidate:T4: 1/8 success, 0 collision, 5 offtrack, 2 speed_too_low
candidate:T5: 2/8 success, 2 collision, 4 offtrack, 1 speed_too_low
parent:T4: 2/8 success, 0 collision, 4 offtrack, 2 speed_too_low
parent:T5: 3/8 success, 2 collision, 3 offtrack, 0 speed_too_low
```

## Guard Audit

M3069 is acceptable as repair input because it did not change the actor
boundary, run new episodes, fit a new candidate, or mutate any checkpoint:

```text
actor observation/action: 72/action 3
direct-action output: clipped [steer, throttle, brake]
runtime base-policy dependency: false
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
new reset/step/rollout/replay: false
fitting/PPO/training/validation/ranking/promotion: false
checkpoint mutation or promotion: false
direct-action adapter guards pass: true
actor-contract guards pass: true
side-effect guards pass: true
claim-boundary rows pass: true
```

## Rejected Claims

M3070 explicitly rejects:

```text
driver performance
validation result or validation readiness
current-sim verdict
repair success
checkpoint or candidate ranking
winner selection
checkpoint promotion
high-fidelity validation readiness or result
finite-window-vs-GRU conclusion
paper evidence
full ideal driver completion
level3 self-identification
```

The positive signal is bounded: the direct-action candidate improved the
same-denominator success/offtrack counts relative to the previous residual
route while preserving a deployable 72-to-3 actor contract. The negative signal
still dominates the engineering route: 24/32 rows are not successful, T5
collisions remain, speed-floor failures increased, and direct-action raw action
pressure is active.

## Route Decision

M3070 selects exactly one next route:

```text
m3071-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-materialization-preflight
```

M3071 should be a no-new-execution materialization milestone that converts the
M3070-accepted M3069 decomposition into one repair contract for a deployable
direct-action active-safety reflex. The contract must make these constraints
first-class gates before any future fitting:

```text
p0 offtrack containment and recovery rows
p0 T5 collision guard rows
p1 speed-floor recovery rows
p1 direct-action raw/final action pressure rows
p1 success-preservation rows
p1 stability/clearance tradeoff rows
p0 actor-contract and claim-boundary rows
```

M3071 must not run rollout, fitting, training, validation, ranking, promotion,
checkpoint mutation, high-fidelity simulation, paper-route comparison,
finite-window-vs-GRU comparison, or self-ID testing. It may only materialize
repair contract rows, loss-family rows, row-admission rows, guard rows, and a
M3072 result-audit manifest.

The deployable actor contract remains:

```text
input: observation vector shape 72
output: clipped [steer, throttle, brake]
runtime base policy required: false
forbidden actor inputs: hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels
```

## Boundary

M3070 does not run reset, step, rollout, replay, fitting, training, validation,
ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison,
or self-ID testing. It only audits M3069 and registers M3071.
