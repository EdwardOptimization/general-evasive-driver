# M3081 Active Safety Driver v1 Deterministic Safety-Reflex Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3080_measurement_route_to_m3082_fresh_robustness_panel_materialization_preflight`
- audited milestone: `m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-preflight`
- next route: `m3082-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-preflight`

M3081 accepts M3080 as a complete and claim-safe same-denominator
closed-loop measurement artifact for the M3078 deterministic direct-action
safety-reflex actor. It does not accept M3080 as validation, ranking,
promotion, repair success, driver performance, current-sim verdict,
high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

The useful result is behavior-positive on the fixed denominator, with an
important remaining blocker: the fixed 32-row denominator cannot support a
robustness or deployment claim, and speed-too-low outcomes increased relative
to the earlier M3067 and M3075 direct-action measurements.

## Audited Facts

M3080 recorded:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
scheduled measurement rows: 32/32
measurement episode rows: 32
measurement failure rows: 0
success rows: 19
collision rows: 3
offtrack rows: 3
speed-too-low rows: 7
success rate recorded: 0.59375
collision rate recorded: 0.09375
offtrack rate recorded: 0.09375
speed-too-low rate recorded: 0.21875
clearance margin mean recorded: 11.22031853760992
high sideslip fraction mean recorded: 0.15814697934268326
lateral RMSE mean recorded: 1.4246135882107964
raw_action_abs_max: 1.0
raw_action_l2_mean: 1.1375218716205753
action_clip_fraction_mean: 0.0
final_action_abs_max: 1.0
actor contract: observation 72 / action 3
candidate output: direct_action_clipped [steer throttle brake]
runtime_base_policy_required: false
direct action formula: final_action = actor_visible_safety_reflex_action(obs72)
actor contract guards: pass
claim-boundary rows: pass
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
```

M3080 required no runtime base policy and did not mutate, rank, select, or
promote a checkpoint.

## Same-Denominator Comparison

The comparable fixed 32-row surface is:

```text
M3067 success/collision/offtrack/speed_low: 8 / 4 / 16 / 5
M3075 success/collision/offtrack/speed_low: 6 / 4 / 19 / 4
M3080 success/collision/offtrack/speed_low: 19 / 3 / 3 / 7

M3067 success_rate: 0.25
M3075 success_rate: 0.1875
M3080 success_rate: 0.59375

M3067 clearance_margin_mean: 8.495534898357793
M3075 clearance_margin_mean: 8.74188928150522
M3080 clearance_margin_mean: 11.22031853760992

M3067 raw_action_abs_max: 2.2606801986694336
M3075 raw_action_abs_max: 2.823486328125
M3080 raw_action_abs_max: 1.0

M3067 action_clip_fraction_mean: 0.03451952273501378
M3075 action_clip_fraction_mean: 0.03910273341603136
M3080 action_clip_fraction_mean: 0.0
```

On this same denominator, M3080 improves success count, collision count,
offtrack count, clearance margin, raw action pressure, and action clipping
relative to M3067 and M3075. This supports a measurement-level statement that
the deterministic safety-reflex route is worth testing on a fresh denominator.

It does not support a deployment or driver-performance conclusion because the
surface is fixed and was already used for prior route decisions.

## Supported Claims

M3081 supports only these bounded claims:

```text
M3080 produced complete same-denominator current-sim measurement artifacts
M3080 executed the M3078 deterministic safety-reflex as a direct obs72-to-action3 actor
M3080 required no runtime base policy
M3080 preserved direct [steer throttle brake] output semantics
M3080 kept hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels actor-invisible
M3080 improved the fixed-denominator behavior surface relative to M3067 and M3075 on success, collision, offtrack, clearance, raw action pressure, and clipping
M3080 kept validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success, and self-ID claims out of scope
M3080 is admissible for a fresh robustness panel materialization step
```

## Rejected Claims

M3081 rejects these interpretations:

```text
M3080 validates the driver
M3080 is a current-sim verdict or deployment verdict
M3080 proves driver performance or selects a winner
M3080 justifies promotion or checkpoint mutation
M3080 completes the full ideal driver
M3080 proves repair success beyond the fixed measurement denominator
M3080 establishes high-fidelity readiness
M3080 provides paper, finite-window-vs-GRU, or self-ID evidence
M3080 permits hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor input
```

## Failure Taxonomy

The M3080 artifact is contract-clean and behavior-positive on the fixed
denominator:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: unresolved; M3080 remains the fixed 32-row panel
behavior_regression: speed-too-low worsened to 7 rows versus 5 in M3067 and 4 in M3075
objective_overfit: active risk if the fixed panel is treated as a verdict
proof_washout: active risk if success rate is reported without speed-too-low and fixed-denominator caveats
seed_fragility: unresolved; no fresh seeds or fresh scenario distribution were measured
```

Failure priorities for the next route:

```text
P0 keep collision and offtrack gains under fresh seeds
P0 preserve actor 72/action 3 direct [steer throttle brake] and runtime_base_policy_required false
P1 measure speed-floor fragility directly because speed-too-low increased to 7/32
P1 keep clearance and action-pressure metrics visible with the same denominator accounting
P2 keep self-ID/GRU/paper evidence diagnostic only
```

## Next Route

M3081 routes exactly one follow-up:

```text
m3082-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-fresh-robustness-panel-materialization-preflight
```

M3082 must materialize a fresh robustness panel before any further measurement
claim. The panel should expand beyond the fixed M3067/M3075/M3080 denominator
using fresh seeds and scenario-distribution rows that directly test:

```text
collision preservation
offtrack containment
clearance margin
speed-too-low fragility
stability and recovery
action pressure and clipping
fresh-seed and fresh-scenario robustness
```

M3082 must not run validation, ranking, promotion, high-fidelity simulation,
paper routing, finite-window-vs-GRU comparison, full-driver certification,
repair-success declaration, or self-ID testing. M3082 must only materialize the
panel, admission gates, actor-contract guards, and claim-boundary rows, then
route to a result audit before execution if the harness requires it.

## Boundary

M3081 is a result audit only. It runs no reset, step, rollout, replay, fitting,
PPO, training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, or self-ID test.
