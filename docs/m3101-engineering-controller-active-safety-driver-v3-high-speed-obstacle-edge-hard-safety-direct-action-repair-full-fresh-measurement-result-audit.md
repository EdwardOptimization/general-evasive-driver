# M3101 Active Safety Driver v3 Full-Fresh Measurement Result Audit

## Audit Decision

- decision: `accept_m3100_artifacts_with_behavior_regression_route_to_m3102_v3_regression_and_v2_fallback_hard_safety_synthesis`
- audit status: `accepted_with_behavior_regression_blocker`
- M3100 status_pass: `True`
- M3100 gate_matrix_pass: `True`
- required artifacts present: `True`
- contract guards pass: `True`
- claim-boundary guards pass: `True`
- same-row comparison rows: `64/64`
- selected next action: `m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis`

## Evidence Summary

M3100 executed the M3098 v3 high-speed obstacle/edge hard-safety direct-action repair as the full obs72-to-action3 action source on the complete 64-row M3084 fresh denominator. It recorded 64 episode rows, 0 execution failures, 55 successes, 5 obstacle-collision terminations, 3 off-track terminations, and 1 speed-too-low termination.

Against M3095 on the same rows and seeds, M3100 recorded:

- success count delta: `-2`
- collision count delta: `0`
- offtrack count delta: `+1`
- speed-too-low count delta: `+1`
- mean clearance-margin delta: `0.40377854830976434`
- mean return delta: `-27.1564682847606`
- mean speed delta: `-1.3373704390077648`

Against M3090 on the same rows and seeds, M3100 recorded:

- success count delta: `+12`
- collision count delta: `0`
- offtrack count delta: `-2`
- speed-too-low count delta: `-10`
- mean clearance-margin delta: `0.04255451650936297`
- mean return delta: `13.94453009486692`
- mean speed delta: `0.6796993143394283`

The measurement path preserved the deployable actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3100 also registered the M3101 audit manifest, wrote gate/claim/contract artifacts, and kept all forbidden claim flags false.

## Supported Claims

- M3100 is a complete and claim-safe full-fresh v3 repair measurement artifact set for audit.
- The M3098 v3 action function can run the complete 64-row fresh denominator without execution failures.
- The actor contract remains obs72 to direct action3 `[steer, throttle, brake]` without runtime base policy, checkpoint model, recurrent hidden state, or hidden actor inputs.
- Same-row comparison artifacts show the v3 route improves over M3090 on aggregate success, offtrack count, and speed-too-low count.
- Same-row comparison artifacts also show behavior regression relative to M3095: 2 fewer successes, 1 additional offtrack, 1 speed-too-low recurrence, unchanged collision count, lower mean return, and lower mean speed.

## Rejected Claims

- M3100 is not a validation result.
- M3100 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3100 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- M3100 does not justify keeping the v3 high-speed obstacle/edge overlay as the next repair base without synthesis because it regresses against the M3095 measured baseline.
- The clearance-margin improvement cannot be treated as active-safety repair success while 5 collision, 3 offtrack, and 1 speed-too-low failures remain.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action/base-policy-free and hidden-input gates pass.
- `lineage_invalid`: not observed; M3100 routes from accepted M3099/M3098 and compares against M3095/M3090 on the same M3084 denominator.
- `metric_artifact`: not observed; row counts, finite metrics, comparison rows, metric summaries, guards, doc, and gate matrix are present.
- `scenario_sampling_failure`: not observed; the full 64-row denominator is accounted with 4 axes and 2 binding roles.
- `behavior_regression`: observed relative to M3095; success count drops by 2, offtrack increases by 1, speed-too-low recurs by 1, and collision remains 5.
- `objective_overfit`: active risk; high-speed braking/throttle suppression appears to improve clearance margin while harming completion, speed-floor, and return.
- `proof_washout`: active risk if aggregate improvement over M3090 hides the M3095 regression and unchanged collision blocker.
- `seed_fragility`: unresolved; no broader validation or high-fidelity route is justified before regression synthesis.

## Public Gate Overfit Risk

Risk is medium-high. M3100 uses the same 64-row current-sim denominator as M3095/M3090/M3084. It is sufficient to audit artifact completeness and same-row behavior deltas, but not sufficient for validation, promotion, driver-performance, current-sim verdict, robustness-result, repair-success, high-fidelity, paper, full-driver, or self-ID claims.

The next route must synthesize whether to reject the v3 overlay, fall back to the M3095 v2 repair as the measured base, or design a narrower hard-safety repair that does not reopen speed-floor failures.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3102-engineering-controller-active-safety-driver-v3-regression-and-v2-fallback-hard-safety-repair-synthesis
```

M3102 should classify the M3100 regressions against M3095 by axis, binding role, termination reason, clearance margin, speed, return, and action pressure. It should decide one bounded next route, with an explicit bias toward preserving the M3095 speed-floor gain unless the evidence supports a smaller actor-visible hard-safety repair. It must not validate, rank, promote, tune on hidden labels, or claim repair success.

## Boundary

M3101 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
