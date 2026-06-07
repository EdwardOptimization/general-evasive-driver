# M3046 Active Safety Driver v1 Failure Decomposition Result Audit

## Summary

- status: completed
- decision: `continue_to_m3047_actuation_aware_repair_design`
- audited milestone: `m3045-engineering-controller-active-safety-driver-v1-failure-decomposition-materialization-preflight`
- next route: `m3047-engineering-controller-active-safety-driver-v1-actuation-aware-repair-design`

M3046 accepts M3045 as a complete and claim-safe failure-decomposition
materialization artifact. It does not accept M3045 as validation, ranking,
promotion, driver-performance verdict, current-sim verdict, repair success,
high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

## Artifact Audit

Accepted M3045 facts:

```text
status_pass: true
gate_matrix_pass: true
measurement rows preserved: 32/32
failure mode rows: 17
actuation saturation rows: 9
repair requirement rows: 6
claim boundary rows: 19
offtrack rows: 24
collision rows: 4
speed-too-low rows: 1
candidate success rows: 0
parent success rows: 4
candidate action_clip_fraction_mean: 0.41243192505631066
parent action_clip_fraction_mean: 0.0
actor contract: 72/action 3
reset/step/rollout/replay/fitting/training/validation/ranking/promotion: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

M3045 preserved the full M3043 denominator and separated the active repair
pressure into explicit requirement families:

```text
p0 offtrack_recovery: 24/32 rows
p0 candidate_action_saturation: candidate 0/16 success and high action clipping
p1 collision_guard: 4 T5 collision rows
p1 success_preservation: preserve all 4 parent success rows and the positive success delta row
p2 speed_floor_guard: 1 speed_too_low row
p0 claim_boundary_guard: M3046 audit required before repair claims
```

## Guard Audit

M3045 is acceptable as repair input because it did not change the actor
boundary, run new episodes, or mutate any candidate:

```text
actor observation/action: 72/action 3
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
new reset/step/rollout/replay: false
fitting/PPO/training/validation/ranking/promotion: false
checkpoint mutation or promotion: false
claim-boundary rows pass: true
```

## Rejected Claims

M3046 explicitly rejects:

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

## Route Decision

M3046 selects exactly one next route:

```text
m3047-engineering-controller-active-safety-driver-v1-actuation-aware-repair-design
```

M3047 should be a design-only process milestone that freezes the next
actuation-aware repair route before any refit, rollout, validation, ranking, or
promotion. The design must make candidate action saturation a first-class gate
rather than optimizing only residual fitting loss or offtrack counts. It must
also preserve parent success rows and keep T5 collision rows separately guarded.

The deployable actor contract remains:

```text
input: observation vector shape 72
output: clipped [steer, throttle, brake]
forbidden actor inputs: hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels
```

## Boundary

M3046 does not run reset, step, rollout, replay, fitting, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It only audits M3045 and registers M3047.
