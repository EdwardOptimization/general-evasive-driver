# M3068 Active Safety Driver v1 Direct-Action Closed-Loop Measurement Result Audit

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m3069_direct_action_failure_decomposition_materialization_preflight`
- audited milestone: `m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight`
- next route: `m3069-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-materialization-preflight`

M3068 accepts M3067 as a complete and claim-safe same-denominator closed-loop
measurement artifact. It does not accept M3067 as validation, ranking,
promotion, driver-performance verdict, current-sim verdict, repair success,
high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

## Synthesis Questions

### evidence_summary

Accepted M3067 facts:

```text
status_pass: true
gate_matrix_pass: true
scheduled measurement rows: 32/32
measurement episode rows: 32
measurement failure rows: 0
success rows: 8
collision rows: 4
offtrack rows: 16
speed-too-low rows: 5
all-row success rate recorded: 0.25
all-row collision rate recorded: 0.125
all-row clearance margin mean recorded: 8.495534898357793
all-row clearance margin delta mean recorded: 1.2911769017645085
all-row return delta mean recorded: -30.17201354191871
raw_action_abs_max: 2.2606801986694336
action_clip_fraction_mean: 0.03451952273501378
final_action_abs_max: 1.0
actor contract: observation 72 / action 3
candidate output: direct_action_clipped [steer throttle brake]
base_policy_required_at_runtime: false
runtime_base_policy_required: false
direct-action adapter guards: pass
actor contract guards: pass
checkpoint side-effect guards: pass
claim-boundary rows: pass
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: false
```

The direct-action closed-loop measurement changes the failure surface compared
with the preceding residual measurements, but it does not close the driver
problem. It records more successes and fewer off-track terminations than the
M3050 action-headroom residual measurement, while leaving collisions present
and adding a speed-floor failure mode:

```text
M3050 success/collision/offtrack/speed_low: 4 / 4 / 24 / 1
M3067 success/collision/offtrack/speed_low: 8 / 4 / 16 / 5
M3050 action_clip_fraction_mean: 0.0
M3067 action_clip_fraction_mean: 0.03451952273501378
```

The group structure is material for the next repair route:

```text
candidate binding: 3/16 success, 2 collision, 9 offtrack, 3 speed_low
parent binding: 5/16 success, 2 collision, 7 offtrack, 2 speed_low
T4: 3/16 success, 0 collision, 9 offtrack, 4 speed_low
T5: 5/16 success, 4 collision, 7 offtrack, 1 speed_low
```

### supported_claims

M3068 supports only these bounded claims:

```text
M3067 produced complete same-denominator current-sim measurement artifacts
M3067 executed the M3065 candidate as a direct obs72-to-action3 actor
M3067 did not require a runtime base policy
M3067 preserved the deployable [steer throttle brake] actor output contract
M3067 kept hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels actor-invisible
M3067 did not mutate parent checkpoints, configs, profiles, or the M3065 candidate artifact
M3067 kept validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, and self-ID claims out of scope
M3067 provides row-level evidence for the next offtrack/collision/speed-floor/action-clip failure decomposition
```

### falsified_claims

M3068 rejects these claims based on M3067:

```text
the M3065 direct-action fit is already a deployable active-safety driver
the M3065 direct-action fit is ready for ranking, promotion, validation, or driver-performance verdict
offline direct-action fitting loss alone predicts closed-loop safety sufficiency
same-denominator current-sim measurement is high-fidelity readiness or paper-level evidence
M3067 establishes a finite-window-vs-GRU or self-ID conclusion
```

The useful positive signal is engineering-relevant but bounded: a direct
obs72-to-action3 adapter can run closed loop without a base policy and without
contract shortcuts. The useful negative signal is stronger for the next
milestone: offtrack is still the dominant failure, T5 collisions remain, and
the speed-floor failure count increased. The next milestone must preserve all
rows and decompose these failure modes before another fitting or rollout claim.

### failure_taxonomy_summary

The M3067 evidence is contract-clean but behavior-incomplete:

```text
contract_violation: not observed
lineage_invalid: not observed
metric_artifact: not observed
scenario_sampling_failure: not observed
behavior_regression: active risk because 24/32 rows still fail
objective_overfit: active risk because offline fit quality did not transfer to deployable closed-loop sufficiency
proof_washout: active risk if future work reports only the success-rate improvement and hides speed/collision/offtrack rows
seed_fragility: unresolved because M3067 remains a same-denominator measurement only
```

Failure decomposition priorities:

```text
P0 offtrack containment and recovery: 16/32 offtrack rows
P0 collision guard preservation: 4/32 collision rows, all on T5
P1 speed-floor recovery: 5/32 speed-too-low rows
P1 direct-action clipping pressure: raw action exceeds bounds but final action remains bounded
P1 stability/clearance tradeoff: clearance margin improves in aggregate but failures persist
```

### public_gate_overfit_risk

Risk is medium. M3067 uses the fixed 32-row denominator, and its measurement
rows include both positive and negative signals. The next milestone must not
optimize only the public success count or the aggregate clearance delta. It
must preserve candidate, parent, T4, T5, collision, offtrack, speed-low, action
clip, stability, recovery, and clearance rows without ranking or promotion.

### next_branch_decision

Decision:

```text
continue_to_m3069_direct_action_failure_decomposition_materialization_preflight
```

M3069 should be a no-new-execution materialization milestone. It may read M3068
and M3067 summary, episode, metric, direct-action adapter, actor-contract,
side-effect, claim, and gate artifacts, then write row-preserving failure-mode,
actuation-pressure, recovery/stability, repair-requirement, claim-boundary,
gate, summary, doc, and M3070 audit artifacts.

M3069 must not run rollouts, train, fit, validate, rank, select a winner,
promote or mutate checkpoints, tune profiles, or claim repair success,
driver performance, current-sim verdict, high-fidelity validation, paper
evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID
evidence.

## Boundary

M3068 does not run reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It only audits M3067 and registers M3069.
