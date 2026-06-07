# M3053 Active Safety Driver v1 Offtrack-Dominant Behavior Target Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_offtrack_behavior_target_materialized_route_to_m3054_result_audit`
- next blocker: `m3054-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3054-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-materialization-result-audit.json`

M3053 materializes a trainer-side behavior target-source and guard panel for
the M3052-selected offtrack-dominant repair route. It does not run fitting,
training, rollout, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, paper-route evaluation, full-driver
evaluation, or self-ID testing.

## Evidence Summary

```text
M3043 success_rate: 0.125
M3050 success_rate: 0.125
M3043 collision_rate: 0.125
M3050 collision_rate: 0.125
M3043 action_clip_fraction_mean: 0.20621596252815533
M3050 action_clip_fraction_mean: 0.0
M3050 headroom_clip_fraction_mean: 0.19604308837476644
M3050 candidate success_rate: 0.0
```

## Materialized Rows

```text
behavior route rows: 1
offtrack behavior target-source rows: 24
candidate-binding blocker rows: 16
collision guard rows: 4
success-preservation guard rows: 4
speed-floor guard rows: 1
actor-contract guard rows: 8
claim-boundary rows: 12
gate rows: 18
```

## Supported Claims

M3053 supports only these bounded claims:

```text
one offtrack-dominant behavior target-source and guard panel was materialized
actor observation 72 and action 3 are preserved
offtrack collision success-preservation speed-floor actor and claim guards are separated
M3054 result-audit manifest was registered
```

## Rejected Claims

M3053 rejects:

```text
target tensor quality
fitting readiness
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3053 is materialization only. All target/source/guard rows remain
trainer-side or process-side evidence and are not actor inputs.
