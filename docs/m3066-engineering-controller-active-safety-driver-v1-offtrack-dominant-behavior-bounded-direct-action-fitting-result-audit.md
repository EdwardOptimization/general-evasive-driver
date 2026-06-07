# M3066 Active Safety Driver v1 Offtrack-Dominant Behavior Bounded Direct-Action Fitting Result Audit

## Summary

- status: completed
- decision: `accept_m3065_direct_action_fit_route_to_m3067_closed_loop_measurement_preflight`
- audited milestone: `m3065-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-bounded-direct-action-fitting-preflight`
- next route: `m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight`

M3066 accepts M3065 as a complete and claim-safe offline direct-action fitting
artifact. It accepts only artifact completeness and measurement admission. It
does not accept M3065 as target-quality validation, closed-loop repair success,
validation result, driver-performance verdict, current-sim verdict, ranking,
winner selection, promotion, high-fidelity result, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

## Artifact Audit

Accepted M3065 facts:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
behavior target tensor rows: 24
fitting dataset rows: 24
fit rows: 18
internal-accounting rows: 6
fit masked steps: 576
internal-accounting masked steps: 192
total masked recovery steps: 768
fitting samples: 2128
all-accounting samples: 2692
fit weight sum: 1008.0
all-accounting weight sum: 1344.0
initial fit weighted MSE: 0.6617927582032398
final fit weighted MSE: 0.00020769915329666637
all-accounting weighted MSE: 0.0023938326408113344
final predicted action abs max: 1.0
actor contract: observation 72 / action 3
output: direct [steer throttle brake]
base policy required at runtime: false
reset/step/rollout/replay/PPO/training/validation/ranking/promotion: false
driver-performance/current-sim/high-fidelity/paper/full-driver/self-ID claims: false
```

The candidate artifact is complete for direct-action measurement:

```text
candidate: runs/m3065_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight/candidate_direct_action_reflex_layer.npz
linear_weight: 72 x 3
linear_bias: 3
observation_dim: 72
action_dim: 3
action_low/action_high: [-1.0, -1.0, -1.0] / [1.0, 1.0, 1.0]
output_semantics: direct_action_clipped
output_components: steer; throttle; brake
base_policy_required_at_runtime: false
```

Candidate composition to preserve in M3067:

```text
raw_action = obs_72 @ linear_weight + linear_bias
final_action = clip(raw_action, action_low, action_high)
output = [steer, throttle, brake]
```

## Guard Audit

M3065 passes the required artifact, actor, side-effect, and claim guards:

```text
fitting dataset rows pass: 24/24
split rows pass: 2/2
mask weight rows pass: 24/24
loss trace rows pass: 3/3
target-quality boundary rows pass: 3/3
actor input exclusion rows pass: 14/14
checkpoint side-effect guard rows pass: 11/11
claim-boundary rows pass: 12/12
gate rows pass: 14/14
target labels actor-visible: false
target provenance actor-visible: false
hidden oracle actor input detected: false
TTC actor input required: false
raw action trace used as target: false
checkpoint mutated: false
checkpoint promoted: false
winner selected: false
```

This is sufficient to measure the direct-action candidate in closed loop. It is
not sufficient to claim that the target labels are high quality, that the
candidate repairs offtrack behavior, that it improves over any baseline, or
that it is deployable outside the bounded current-sim measurement contract.

## Rejected Claims

M3066 explicitly rejects:

```text
offline loss improvement as driver performance
target quality or fitted policy quality
closed-loop repair success
validation result or validation readiness
current-sim verdict
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

M3066 selects exactly one next route:

```text
m3067-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-closed-loop-measurement-preflight
```

M3067 must run a bounded same-denominator current-sim measurement preflight for
the M3065 direct-action candidate. It must execute the candidate as the full
action-producing actor, not as a residual on top of a base policy. The actor
input remains observation vector shape 72 only, and the output remains clipped
`[steer, throttle, brake]` shape 3. M3067 may write raw measurement rows,
safety/clearance/stability/recovery/action/robustness metric tables, adapter
guards, claim boundaries, and an M3068 result-audit manifest. It must not rank,
promote, select a winner, tune the denominator after seeing rows, or convert
current-sim rows into validation, driver-performance, high-fidelity, paper,
finite-window-vs-GRU, full-driver, or self-ID claims.

The deployable actor contract to preserve is:

```text
input: observation vector shape 72
runtime base policy: none
direct action: clipped 72-to-3 M3065 candidate
output: [steer, throttle, brake]
forbidden actor inputs: hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict labels
```

## Boundary

M3066 does not run reset, step, rollout, replay, validation, ranking,
promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or
self-ID testing. It only audits M3065 and registers M3067.
