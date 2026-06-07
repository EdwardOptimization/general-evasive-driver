# M3052 Active Safety Driver v1 Behavior-Negative Measurement Synthesis Repair Route Design

## Summary

- status: completed
- synthesis decision: `pivot_to_offtrack_dominant_behavior_target_materialization`
- decision: `continue_to_m3053_offtrack_dominant_behavior_target_materialization_preflight`
- parent audit: `docs/m3051-engineering-controller-active-safety-driver-v1-actuation-aware-residual-repair-closed-loop-measurement-result-audit.md`
- next route: `m3053-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-materialization-preflight`

M3052 accepts the M3051/M3050 measurement chain as complete and claim-safe, but
behavior-negative. The actuation-aware residual route fixed a final-action
clipping artifact without improving the closed-loop safety outcome. The next
route must therefore stop residual-only saturation repair and move to a
behavior-level offtrack recovery materialization step.

M3052 does not run reset, step, rollout, replay, fitting, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, paper-route evaluation, full-driver evaluation, or self-ID testing.

## Evidence Summary

Same-denominator comparison:

```text
M3043 success/collision/offtrack/speed_low: 4 / 4 / 24 / 1
M3050 success/collision/offtrack/speed_low: 4 / 4 / 24 / 1
M3043 all-row success_rate: 0.125
M3050 all-row success_rate: 0.125
M3043 all-row collision_rate: 0.125
M3050 all-row collision_rate: 0.125
M3043 all-row clearance_margin_mean: 7.361927716635305
M3050 all-row clearance_margin_mean: 7.3486834346961585
M3043 all-row return_mean: -9.207271997412152
M3050 all-row return_mean: -9.429755974366582
M3043 all-row action_clip_fraction_mean: 0.20621596252815533
M3050 all-row action_clip_fraction_mean: 0.0
M3050 all-row headroom_clip_fraction_mean: 0.19604308837476644
```

Role-specific comparison:

```text
candidate binding M3043 success_rate: 0.0
candidate binding M3050 success_rate: 0.0
candidate binding M3043 action_clip_fraction_mean: 0.41243192505631066
candidate binding M3050 action_clip_fraction_mean: 0.0
candidate binding M3050 headroom_clip_fraction_mean: 0.39208617674953294
parent binding M3043 success_rate: 0.25
parent binding M3050 success_rate: 0.25
parent binding M3050 action_clip_fraction_mean: 0.0
```

Task-family comparison:

```text
T4 M3043 success_rate/collision_rate: 0.0625 / 0.0
T4 M3050 success_rate/collision_rate: 0.0625 / 0.0
T5 M3043 success_rate/collision_rate: 0.1875 / 0.25
T5 M3050 success_rate/collision_rate: 0.1875 / 0.25
```

## Supported Claims

M3052 supports only these bounded claims:

```text
M3050 removed final action clipping from the measurement telemetry
M3050 preserved actor observation 72 and action 3
M3050 preserved residual adapter and checkpoint side-effect guards
M3050 did not improve same-denominator success collision offtrack or speed-floor outcomes
M3051 correctly rejects repair-success validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver and self-ID claims
```

## Falsified Claims

M3052 rejects these claims:

```text
another linear residual-only saturation repair is the right immediate next step
action clipping cleanup is sufficient to repair offtrack-dominant behavior
offline residual loss is a reliable proxy for closed-loop recovery behavior here
M3048/M3050 is ready for validation ranking promotion or driver-performance verdict
M3050 is paper evidence finite-window-vs-GRU evidence full-driver evidence or self-ID evidence
```

## Failure Taxonomy Summary

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: unresolved because M3043/M3050 are same-denominator measurements
behavior_regression: active risk because offtrack-dominant failures remain unchanged
objective_overfit: active risk because offline residual loss and action clipping cleanup did not transfer to closed-loop success
proof_washout: active risk if future milestones report only action clipping cleanup
seed_fragility: unresolved because no fresh distribution or holdout route has been run
```

## Route Decision

M3052 freezes exactly one next route:

```text
m3053-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-materialization-preflight
```

The selected route changes the repair unit from a small linear residual-only
delta to a behavior-level recovery materialization. M3053 must materialize the
trainer-side target-source and guard rows needed for a later deployable
offtrack recovery selector/reflex that still consumes the 72-dimensional
human-view observation and directly emits `[steer, throttle, brake]`.

The selected route has these priorities:

```text
p0 offtrack recovery behavior targets for the 24 persistent offtrack rows
p0 candidate-binding blocker rows because candidate binding remains 0/16 success
p1 T5 collision guard rows kept separate from offtrack repair
p1 parent success-preservation rows kept separate from failure rows
p2 speed-floor row kept visible
p0 actor-contract and claim-boundary rows
```

## Rejected Routes

M3052 rejects these immediate next routes:

```text
another saturation-only residual fit
direct rollout validation ranking promotion or winner selection
high-fidelity validation readiness claim from current-sim same-denominator rows
paper-route finite-window-vs-GRU or self-ID conclusion
target tensor quality claim before behavior target-source and guard materialization
```

## M3053 Requirements

M3053 must write one bounded artifact set:

```text
behavior repair route row
offtrack behavior target-source rows
candidate-binding blocker rows
T5 collision guard rows
parent success-preservation rows
speed-floor guard row
actor contract guard rows
claim-boundary rows
gate matrix
summary
M3054 result-audit manifest
```

M3053 may use M3043, M3050, M3045, and M3051 artifacts as trainer-side or
process-side evidence. It must not add hidden/oracle/TTC/target/provenance/
source/route/outcome/progress/verdict labels to the actor input. It must not
run local-action search, target tensor fitting, rollout, validation, ranking,
promotion, checkpoint mutation, high-fidelity simulation, paper-route
comparison, or self-ID testing.

## Boundary

M3052 is a route-design and synthesis milestone only. It does not claim repair
success or driver performance. It only preserves the negative measurement
evidence and routes exactly once to M3053.
