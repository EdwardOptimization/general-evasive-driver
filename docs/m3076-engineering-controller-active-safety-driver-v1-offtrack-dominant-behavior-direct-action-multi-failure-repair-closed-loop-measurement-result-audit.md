# M3076 Active Safety Driver v1 Direct-Action Multi-Failure Repair Closed-Loop Measurement Result Audit

## Summary

- status: completed
- synthesis decision: `pivot`
- decision: `pivot_to_m3077_deployable_direct_action_safety_reflex_route_design`
- audited milestone: `m3075-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-preflight`
- next route: `m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-pivot-route-design`

M3076 accepts M3075 as a complete and claim-safe same-denominator closed-loop
measurement artifact. It rejects M3075 as repair success, driver performance,
validation, ranking, promotion, current-sim verdict, high-fidelity readiness,
paper evidence, finite-window-vs-GRU evidence, full-driver completion, or
self-ID evidence.

The key result is negative for the offline repair loop: the M3073 repaired
candidate preserves the deployable obs72-to-action3 `[steer throttle brake]`
contract, but it worsens the main same-denominator behavior surface relative
to the M3065 direct-action parent measurement.

## Synthesis Questions

### evidence_summary

Accepted M3075 facts:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
scheduled measurement rows: 32/32
measurement episode rows: 32
measurement failure rows: 0
success rows: 6
collision rows: 4
offtrack rows: 19
speed-too-low rows: 4
all-row success rate recorded: 0.1875
all-row collision rate recorded: 0.125
all-row clearance margin mean recorded: 8.74188928150522
raw_action_abs_max: 2.823486328125
action_clip_fraction_mean: 0.03910273341603136
final_action_abs_max: 1.0
actor contract: observation 72 / action 3
candidate output: direct_action_clipped [steer throttle brake]
runtime_base_policy_required: false
direct-action adapter guards: pass
actor contract guards: pass
checkpoint side-effect guards: pass
claim-boundary rows: pass
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
```

Same-denominator comparison against the M3067 parent direct-action measurement:

```text
M3067 success/collision/offtrack/speed_low: 8 / 4 / 16 / 5
M3075 success/collision/offtrack/speed_low: 6 / 4 / 19 / 4
M3067 success_rate: 0.25
M3075 success_rate: 0.1875
M3067 clearance_margin_mean: 8.495534898357793
M3075 clearance_margin_mean: 8.74188928150522
M3067 raw_action_abs_max: 2.2606801986694336
M3075 raw_action_abs_max: 2.823486328125
M3067 action_clip_fraction_mean: 0.03451952273501378
M3075 action_clip_fraction_mean: 0.03910273341603136
```

The repaired candidate improves no primary pass/fail safety outcome. Collision
count remains unchanged, success count drops, offtrack count increases, and
raw action pressure increases. The clearance-margin mean is higher, but that
aggregate is not sufficient to override worse success/offtrack behavior.

### supported_claims

M3076 supports only these bounded claims:

```text
M3075 produced complete same-denominator current-sim measurement artifacts
M3075 executed the M3073 repaired candidate as a direct obs72-to-action3 actor
M3075 did not require a runtime base policy
M3075 preserved the deployable [steer throttle brake] output contract
M3075 kept hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels actor-invisible
M3075 did not mutate parent checkpoints, configs, profiles, or candidate artifacts
M3075 kept validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success, and self-ID claims out of scope
M3075 provides closed-loop negative evidence for the M3071-M3075 offline repair route
```

### falsified_claims

M3076 rejects these claims based on M3075:

```text
the M3073 repaired candidate repairs the M3067 failure surface
the M3073 repaired candidate improves same-denominator success/offtrack behavior
offline multi-failure repair fitting loss is sufficient to predict closed-loop safety repair
continuing the same offline target fitting loop is the right next default
M3075 establishes a deployable driver, repair-success result, validation result, performance verdict, finite-window-vs-GRU conclusion, or self-ID conclusion
```

The negative result is useful because it separates artifact correctness from
driver sufficiency. The actor can run as a deployable direct-action reflex, but
the current learned offline repair route is not the right route to continue
without a pivot.

### failure_taxonomy_summary

The M3075 evidence is contract-clean and behavior-negative:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: not observed
behavior_regression: observed relative to M3067 on success and offtrack counts
objective_overfit: observed risk because offline repair fitting does not transfer to closed-loop repair
proof_washout: active risk if clearance mean is reported without success/offtrack counts
seed_fragility: unresolved because M3075 remains the fixed same-denominator panel
```

Failure priorities:

```text
P0 offtrack containment and recovery: 19/32 offtrack rows
P0 collision guard preservation: 4/32 collision rows
P1 action pressure: raw_action_abs_max increases to 2.823486328125
P1 success retention: success falls from 8/32 to 6/32
P2 speed-floor behavior: speed-too-low remains present at 4/32
```

### public_gate_overfit_risk

Risk is high for continuing this branch. The route has already fit against a
fixed target/contract surface, audited the artifact, and measured it on the
same denominator. The measurement is negative on the primary behavior counts.
Another small offline repair loop would be more likely to chase the fixed
panel than to produce a deployable active-safety reflex.

### next_branch_decision

Decision:

```text
pivot_to_m3077_deployable_direct_action_safety_reflex_route_design
```

M3077 should freeze exactly one new deployable direct-action safety-reflex route
before further implementation. The new branch must keep the actor-visible
obs72/action3 contract and direct `[steer throttle brake]` output, keep
self-ID/GRU/paper evidence diagnostic only, and prioritize closed-loop safety
metrics: collision, offtrack, clearance, stability, recovery, and robustness.

M3077 must not run new rollouts, fit, validate, rank, promote, or claim driver
performance. It should decide the implementation route for a deployable
active-safety reflex layer after the M3075 negative result, with explicit
forbidden shortcuts and a required follow-up measurement plan.

## Boundary

M3076 does not run reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It audits M3075 and closes the current offline
multi-failure repair branch with synthesis decision `pivot`.
