# M3106 Active Safety Driver v4 Full-Fresh Measurement Result Audit

## Audit Decision

- decision: `accept_m3105_artifacts_with_no_regression_plateau_route_to_m3107_residual_collision_offtrack_synthesis`
- audit status: `accepted_with_residual_hard_safety_blocker`
- M3105 status_pass: `True`
- M3105 gate_matrix_pass: `True`
- required artifacts present: `True`
- measurement rows: `64/64`
- measurement failures: `0`
- same-row comparison rows: `192`
- selected next action: `m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis`

## Evidence Summary

M3105 executed the M3103 v4 v2-fallback no-regression hard-safety direct-action repair as the full obs72-to-action3 action source on the complete 64-row M3084 fresh denominator. It recorded 57 successes, 5 obstacle-collision terminations, 2 off-track terminations, and 0 speed-too-low terminations.

Against M3095 on the same rows and seeds, M3105 recorded:

- success count delta: `0`
- collision count delta: `0`
- offtrack count delta: `0`
- speed-too-low count delta: `0`
- mean clearance-margin delta: `0.0011224892562964814`
- mean return delta: `-0.009582429768155099`
- mean speed delta: `-0.004289535331364308`

Against M3100 on the same rows and seeds, M3105 recorded:

- success count delta: `+2`
- collision count delta: `0`
- offtrack count delta: `-1`
- speed-too-low count delta: `-1`

Against M3090 on the same rows and seeds, M3105 recorded:

- success count delta: `+14`
- collision count delta: `0`
- offtrack count delta: `-3`
- speed-too-low count delta: `-11`

The measurement path preserved the deployable actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3105 registered the M3106 audit manifest, wrote measurement, metric, comparison, contract, claim, gate, and doc artifacts, and kept all forbidden claim flags false.

## Supported Claims

- M3105 is a complete and claim-safe full-fresh v4 repair measurement artifact set for audit.
- The M3103 v4 action function can run the complete 64-row fresh denominator without execution failures.
- The actor contract remains obs72 to direct action3 `[steer, throttle, brake]` without runtime base policy, checkpoint model, recurrent hidden state, or hidden actor inputs.
- Same-row comparison artifacts show that M3105 removes the M3100 behavior regressions: +2 successes, -1 offtrack, and -1 speed-too-low against M3100.
- Same-row comparison artifacts show that M3105 is effectively a no-regression plateau against M3095 rather than a new hard-safety improvement.

## Rejected Claims

- M3105 is not a validation result.
- M3105 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3105 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- M3105 does not solve the residual hard-safety blocker because 5 collisions and 2 offtrack failures remain.
- The M3100 regression repair cannot be counted as active-safety repair success relative to the best measured M3095/M3105 baseline.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3/direct-action/base-policy-free and hidden-input gates pass.
- `lineage_invalid`: not observed; M3105 routes from accepted M3104/M3103 and compares against M3095/M3100/M3090 on the same M3084 denominator.
- `metric_artifact`: not observed; row counts, finite metrics, comparison rows, metric summaries, guards, doc, and gate matrix are present.
- `scenario_sampling_failure`: not observed; the full 64-row denominator is accounted with 4 axes and 2 binding roles.
- `behavior_regression`: not observed relative to M3095 on aggregate counts; observed earlier M3100 regressions are removed.
- `objective_overfit`: still active if the branch keeps adding narrow local rules without reducing residual collision/offtrack blockers.
- `proof_washout`: active risk if recovering from M3100 regression is mistaken for repair success.
- `seed_fragility`: unresolved; no broader validation or high-fidelity route is justified before synthesis chooses a stronger residual hard-safety direction.

## Public Gate Overfit Risk

Risk is medium. M3105 is a complete same-denominator measurement and a useful guard against the M3100 regression pattern, but it does not expand evidence beyond the 64-row current-sim denominator and does not reduce the residual collision/offtrack blockers relative to M3095.

The next route should synthesize the plateau rather than continue small v4 no-regression edits. The key question is how to attack the remaining 5 collision and 2 offtrack failures without reopening the speed-floor gains.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3107-engineering-controller-active-safety-driver-v4-plateau-and-residual-collision-offtrack-hard-safety-synthesis
```

M3107 should classify why M3105 only matches M3095, preserve the deployable obs72/action3 direct-action boundary, and choose one next branch: a stronger residual collision/offtrack repair route, a broader scenario/failure decomposition route, or a stop/pivot route. It must not validate, rank, promote, tune on hidden labels, or claim repair success.

## Boundary

M3106 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
