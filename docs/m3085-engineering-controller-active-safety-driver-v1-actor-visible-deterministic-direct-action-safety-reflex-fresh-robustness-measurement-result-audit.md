# M3085 Active Safety Driver v1 Fresh Robustness Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3084_measurement_route_to_m3086_deployable_runtime_contract_materialization_preflight`
- audited milestone: `m3084-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-measurement-preflight`
- next route: `m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight`

M3085 accepts M3084 as a complete and claim-safe fresh robustness measurement
artifact for the M3078 deterministic direct-action safety-reflex actor. It does
not accept M3084 as validation, ranking, promotion, repair success, driver
performance, current-sim verdict, high-fidelity readiness, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

The useful route decision is that M3084 is strong enough to justify packaging
the candidate behind a deployable obs72-to-action3 runtime contract, while the
remaining collision, offtrack, and speed-floor failures must stay visible as
future verification and repair blockers.

## Audited Facts

M3084 recorded:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
scheduled measurement rows: 64/64
measurement episode rows: 64
measurement failure rows: 0
M3080 seed overlap count: 0
robustness axes: 4
success rows: 43
collision rows: 5
offtrack rows: 5
speed-too-low rows: 11
success rate recorded: 0.671875
collision rate recorded: 0.078125
offtrack rate recorded: 0.078125
speed-too-low rate recorded: 0.171875
clearance margin mean recorded: 11.341408769853288
high sideslip fraction mean recorded: 0.1453887937478719
lateral RMSE mean recorded: 1.3956723862912284
raw_action_abs_max: 1.0
raw_action_l2_mean: 1.1297335504261263
action_clip_fraction_mean: 0.0
final_action_abs_max: 1.0
actor contract: observation 72 / action 3
candidate output: direct_action_clipped [steer throttle brake]
runtime_base_policy_required: false
direct action formula: final_action = actor_visible_safety_reflex_action(obs72)
actor contract guards: 22/22 pass
claim-boundary rows: 20/20 pass
gate matrix rows: 19/19 pass
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
```

M3084 required no runtime base policy and did not mutate, rank, select, or
promote a checkpoint.

## Fresh Axis Surface

The fresh M3082 denominator produced:

```text
all rows: 64 rows, success 0.671875, collision 0.078125, offtrack 0.078125, speed-too-low 0.171875, clearance_mean 11.341408769853288

collision_lateral_intrusion: 16 rows, success 0.625, collision 0.125, offtrack 0.125, speed-too-low 0.125, clearance_mean 6.777648471005319
offtrack_boundary_recovery: 16 rows, success 0.5625, collision 0.1875, offtrack 0.125, speed-too-low 0.125, clearance_mean 5.818895162012969
speed_floor_stress: 16 rows, success 0.8125, collision 0.0, offtrack 0.0625, speed-too-low 0.125, clearance_mean 18.791267131532592
stability_action_pressure: 16 rows, success 0.6875, collision 0.0, offtrack 0.0, speed-too-low 0.3125, clearance_mean 13.977824314862268

candidate binding: 32 rows, success 0.6875, collision 0.09375, offtrack 0.09375, speed-too-low 0.125, clearance_mean 12.399732106365228
parent binding: 32 rows, success 0.65625, collision 0.0625, offtrack 0.0625, speed-too-low 0.21875, clearance_mean 10.283085433341345
```

The fresh panel preserves the direct-action actor boundary and shows no action
clip pressure. The weakest surfaces are offtrack-boundary recovery for
collision/offtrack and stability-action-pressure for speed-too-low. Those
remain engineering blockers for later verification and repair.

## Fixed-Panel Context

M3080 remains the fixed-panel context:

```text
M3080 rows: 32
M3080 success/collision/offtrack/speed_low: 19 / 3 / 3 / 7
M3080 success_rate: 0.59375
M3080 collision_rate: 0.09375
M3080 offtrack_rate: 0.09375
M3080 speed_too_low_rate: 0.21875
M3080 clearance_margin_mean: 11.22031853760992
M3080 action_clip_fraction_mean: 0.0
```

M3084 is not a same-denominator validation comparison to M3080. The useful
bounded observation is that M3084 kept the same actor contract and showed a
fresh-denominator measurement surface without seed overlap, while still leaving
hard safety failures unresolved.

## Supported Claims

M3085 supports only these bounded claims:

```text
M3084 produced complete fresh robustness current-sim measurement artifacts
M3084 executed the M3078 deterministic safety-reflex as a direct obs72-to-action3 actor
M3084 required no runtime base policy
M3084 preserved direct [steer throttle brake] output semantics
M3084 used 64 fresh panel rows with 0 M3080 seed overlap
M3084 reported success, collision, offtrack, speed-too-low, clearance, stability, recovery, action-pressure, actor-contract, claim-boundary, and gate artifacts by axis and all rows
M3084 kept hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels actor-invisible
M3084 kept validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success, robustness-result, and self-ID claims out of scope
M3084 is admissible for deployable runtime-contract materialization before any stronger verification claim
```

## Rejected Claims

M3085 rejects these interpretations:

```text
M3084 validates the driver
M3084 is a current-sim verdict or deployment verdict
M3084 proves driver performance or selects a winner
M3084 justifies promotion or checkpoint mutation
M3084 completes the full ideal driver
M3084 proves repair success or robustness success
M3084 establishes high-fidelity readiness
M3084 provides paper, finite-window-vs-GRU, or self-ID evidence
M3084 permits hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor input
M3084 permits dropping collision/offtrack/speed-floor failures from future gates
```

## Failure Taxonomy

M3084 is artifact-complete and contract-clean:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: not observed for the M3082 fresh panel denominator
behavior_regression: not claimed either way because M3084 is a fresh-denominator measurement
objective_overfit: reduced relative to fixed-panel only evidence, but active if M3084 is treated as a verdict
proof_washout: active risk if success rate is reported without the 5 collision, 5 offtrack, and 11 speed-too-low rows
seed_fragility: reduced by 64 fresh seeds with 0 M3080 seed overlap, but not eliminated
```

Failure priorities for the next route:

```text
P0 preserve actor 72/action 3 direct [steer throttle brake] and runtime_base_policy_required false
P0 materialize a stable deployable runtime contract so the safety-reflex layer can be called directly
P0 keep collision, offtrack, clearance, stability, recovery, action-pressure, and seed-lineage checks in the package
P1 keep offtrack-boundary recovery and stability-action-pressure failures explicit as future verification blockers
P1 keep no hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs
P2 keep self-ID/GRU/paper evidence diagnostic only
```

## Next Route

M3085 routes exactly one follow-up:

```text
m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight
```

M3086 must materialize a deployable runtime contract and package for the
deterministic safety-reflex layer before further validation claims. The package
must expose an obs72-to-action3 interface that directly returns:

```text
[steer, throttle, brake]
```

M3086 should write contract, probe, actor-input-exclusion, claim-boundary, gate,
summary, and follow-up audit artifacts. It must not run rollout validation,
ranking, promotion, high-fidelity simulation, paper routing,
finite-window-vs-GRU comparison, full-driver certification, repair-success
declaration, or self-ID testing.

## Boundary

M3085 is a result audit only. It runs no reset, step, rollout, replay, fitting,
PPO, training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, or self-ID test.
