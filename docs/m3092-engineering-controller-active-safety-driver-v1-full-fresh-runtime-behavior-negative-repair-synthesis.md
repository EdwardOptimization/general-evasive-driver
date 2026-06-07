# M3092 Active Safety Driver v1 Full-Fresh Runtime Behavior-Negative Repair Synthesis

## Summary

- status: completed
- synthesis decision: `pivot`
- decision: `route_to_m3093_speed_floor_aware_balanced_direct_action_repair_materialization`
- audited evidence: `m3090` full-fresh deployable runtime measurement and `m3091` result audit
- next route: `m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight`

M3092 accepts the M3090/M3091 conclusion that runtime packaging is no longer the blocker: the deployable `ActiveSafetyReflexDriver.act(obs72)` path executed 64/64 fresh rows with 0 execution failures and exact same-row parity against M3084. M3092 does not accept the behavior as sufficient. The active blockers remain 5 collision rows, 5 offtrack rows, and 11 speed-too-low rows.

The next branch should pivot from runtime packaging checks to a bounded direct-action repair materialization. It must preserve actor-visible obs72 input only, direct action3 `[steer, throttle, brake]`, no runtime base policy, no checkpoint model, no recurrent hidden state, and no hidden oracle, TTC, target, source, route, outcome, progress, or verdict actor input.

## evidence_summary

M3090 recorded:

```text
total rows: 64
success: 43
non-success: 21
collision: 5
offtrack: 5
speed_too_low: 11
success_rate: 0.671875
clearance_margin_mean: 11.341408769853288
runtime parity: 64/64 outcome match with M3084
max clearance delta: 0.0
max return delta: 0.0
```

Non-success rows by termination:

```text
speed_too_low: 11
obstacle_collision: 5
off_track: 5
```

Non-success rows by axis:

```text
offtrack_boundary_recovery: 7
collision_lateral_intrusion: 6
stability_action_pressure: 5
speed_floor_stress: 3
```

The speed-too-low cluster is the largest single blocker. It appears in all 5 stability-action-pressure failures, 2 speed-floor-stress failures, 2 collision-lateral-intrusion failures, and 2 offtrack-boundary-recovery failures. Its mean `speed_mean` is 4.444301251671898, while the success rows have mean `speed_mean` 7.61204219898079.

The collision cluster is smaller but hard-safety critical. Collision rows have mean `min_clearance_margin` -0.1558197644541167 and mean `speed_mean` 17.13912502137202. The offtrack cluster has mean `lateral_rmse` 2.21527078891786 and mean `high_sideslip_fraction` 0.5619586762321949.

The current v1 rule table uses a negative base throttle and subtracts additional throttle under brake, edge, and stability urgency:

```text
base_throttle_normalized: -0.35
brake_to_throttle_suppression: 1.20
edge_to_throttle_suppression: 0.35
stability_to_throttle_suppression: 0.25
speed relief condition: only vx_body < 1.0 and brake_physical < 0.2
```

This does not prove the root cause, but it is a plausible actor-visible repair target because the largest failure cluster is low-speed termination, and the existing relief condition is too narrow to cover the observed `speed_mean` range around 3.68 to 5.63 in speed-too-low rows.

## supported_claims

M3092 supports only these bounded claims:

```text
M3090/M3091 provide complete full-fresh deployable runtime evidence for repair synthesis
The deployable API and claim boundaries are not the current blocker
The next route should repair behavior before validation, ranking, promotion, or high-fidelity work
The largest observed blocker is speed-too-low, followed by collision and offtrack hard-safety blockers
A speed-floor-aware balanced direct-action rule/config materialization is the next bounded repair route
```

The selected repair direction is:

```text
M3093 materializes v2 speed-floor-aware balanced direct-action safety-reflex rules
It should add an actor-visible speed-floor recovery guard from obs[0] velocity
It should avoid excessive throttle suppression when obstacle and edge urgency are low
It should preserve hard obstacle/corridor safety by keeping urgent obstacle braking/steering and lane recovery branches
It should reduce saturation-driven action pressure where possible without claiming measured improvement
```

## falsified_claims

M3092 explicitly rejects these claims:

```text
M3090 validates the driver
M3090 proves current-sim driver performance
M3090 proves robustness success
M3090 proves repair success
M3090 justifies ranking, winner selection, checkpoint mutation, or promotion
M3090 establishes high-fidelity readiness
M3090 completes the full ideal driver
M3090 provides paper, finite-window-vs-GRU, or self-ID evidence
Exact runtime parity means behavior improved
Validation planning is the next route while 5 collision, 5 offtrack, and 11 speed-too-low blockers remain
Self-ID or GRU should return to the mainline before direct-action safety blockers are repaired
```

## failure_taxonomy_summary

```text
contract_violation: not observed in M3090/M3091; actor contract guards pass
lineage_invalid: not observed; M3092 routes from M3091/M3090/M3087/M3084
metric_artifact: not observed for synthesis; row counts, metric rows, parity rows, and gate rows exist
scenario_sampling_failure: not observed for M3090 scope; the complete 64-row M3084 fresh denominator is accounted
behavior_regression: not decided as regression, but behavior-negative blockers are active
objective_overfit: active if parity or success rate is used to mask hard failures
proof_washout: active if collision/offtrack/speed-low rows are summarized away
seed_fragility: unresolved; no broader validation is justified before repair and fresh measurement
```

## public_gate_overfit_risk

Risk is medium. The M3090 denominator is broader than the 8-row smoke panel, but it is still a current-sim denominator already known from M3084. The evidence is useful because it proves deployable runtime parity and preserves failure counts. It is not useful as a validation or performance claim.

The next route must therefore materialize one bounded repair and measure it later on the same full-fresh denominator before any stronger interpretation. It must not tune row selection, add hidden inputs, use a runtime base policy, mutate a learned checkpoint, or promote a result based on partial metrics.

## next_branch_decision

Route exactly one follow-up to:

```text
m3093-engineering-controller-active-safety-driver-v2-speed-floor-aware-direct-action-repair-materialization-preflight
```

M3093 should materialize a v2 direct-action safety-reflex rule/config package. It should target the largest speed-too-low blocker first while preserving hard obstacle and corridor safety:

```text
primary repair: speed-floor-aware throttle/brake release from actor-visible vx_body
secondary constraints: preserve urgent obstacle braking/steering and road-corridor recovery
contract: obs72 -> direct action3 [steer, throttle, brake]
no runtime base policy: true
no checkpoint model: true
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3093 is a materialization preflight only. It must write rule/config/guard/claim artifacts and register a result audit. It must not run measurement, validation, ranking, promotion, high-fidelity simulation, paper evidence, full-driver completion, repair-success, robustness-result, or self-ID tests.

## Boundary

M3092 is a synthesis decision only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
