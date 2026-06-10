# M3096 Active Safety Driver v2 Full-Fresh Measurement Result Audit

## Audit Decision

- decision: `accept_m3095_artifacts_with_residual_hard_safety_blocker_route_to_m3097_collision_offtrack_repair_synthesis`
- audit status: `accepted_with_behavior_blocker`
- M3095 status_pass: `True`
- M3095 gate_matrix_pass: `True`
- required artifacts present: `True`
- contract guards pass: `True`
- claim-boundary guards pass: `True`
- same-row comparison rows: `64/64`
- selected next action: `m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis`

## Evidence Summary

M3095 executed the M3093 v2 speed-floor-aware direct-action repair as the full obs72-to-action3 action source on the complete 64-row M3084 fresh denominator. It recorded 64 episode rows, 0 execution failures, 57 successes, 5 obstacle-collision terminations, 2 off-track terminations, and 0 speed-too-low terminations.

Against M3090 on the same rows and seeds, M3095 recorded:

- success count delta: `+14`
- collision count delta: `0`
- offtrack count delta: `-3`
- speed-too-low count delta: `-11`
- mean clearance-margin delta: `-0.3612240318004013`
- mean return delta: `41.10099837962752`
- mean speed delta: `2.0170697533471933`

The measurement path preserved the deployable actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3095 also registered the M3096 audit manifest, wrote gate/claim/contract artifacts, and kept all forbidden claim flags false.

## Supported Claims

- M3095 is a complete and claim-safe full-fresh v2 repair measurement artifact set for audit.
- The v2 speed-floor-aware action function can run the complete 64-row fresh denominator without execution failures.
- The actor contract remains obs72 to direct action3 `[steer, throttle, brake]` without runtime base policy, checkpoint model, recurrent hidden state, or hidden actor inputs.
- Same-row comparison artifacts show speed-too-low was eliminated on this denominator and offtrack count decreased relative to M3090.
- The branch can move to residual hard-safety repair synthesis because 5 collision and 2 offtrack failures remain.

## Rejected Claims

- M3095 is not a validation result.
- M3095 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3095 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- The same-row improvements do not prove deployable active-safety success because 7/64 rows still fail, including 5 collision rows.
- The reduction of speed-too-low cannot be treated as a full repair while hard-safety failures remain.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action/base-policy-free and hidden-input gates pass.
- `lineage_invalid`: not observed; M3095 routes from accepted M3094/M3093/M3090/M3084 artifacts and registers M3096.
- `metric_artifact`: not observed; row counts, finite metrics, comparison rows, metric summaries, guards, doc, and gate matrix are present.
- `scenario_sampling_failure`: not observed; the full 64-row denominator is accounted with 4 axes and 2 binding roles.
- `behavior_regression`: not used as a verdict; same-row data shows improved success count and speed-floor behavior, but collision count remains unchanged.
- `objective_overfit`: active risk if speed-floor improvement is optimized at the expense of clearance margin or collision handling.
- `proof_washout`: active risk if self-ID/GRU/paper evidence is re-centered before hard safety failures are resolved.
- `seed_fragility`: unresolved; no broader validation or high-fidelity route is justified before residual hard-safety synthesis.

## Public Gate Overfit Risk

Risk is medium. M3095 uses the same 64-row current-sim denominator as M3090/M3084 and therefore supports artifact completeness plus same-row measurement only. It is strong enough to show the v2 repair changed behavior on the intended denominator, but not enough to justify validation, promotion, driver-performance, current-sim verdict, robustness-result, repair-success, high-fidelity, paper, full-driver, or self-ID claims.

The next route must analyze the remaining collision and offtrack rows before any validation route.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3097-engineering-controller-active-safety-driver-v2-residual-collision-offtrack-hard-safety-repair-synthesis
```

M3097 should classify the residual 5 collision and 2 offtrack rows by axis, binding role, clearance margin, lateral error, sideslip, speed, and action-pressure signatures, then select exactly one bounded repair materialization route that preserves obs72/action3 direct action and forbids hidden/oracle actor inputs.

M3097 must not validate, rank, promote, tune on hidden labels, or claim repair success.

## Boundary

M3096 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
