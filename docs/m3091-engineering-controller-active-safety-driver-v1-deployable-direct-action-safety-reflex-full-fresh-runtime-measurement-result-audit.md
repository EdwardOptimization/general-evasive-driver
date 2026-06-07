# M3091 Active Safety Driver v1 Full-Fresh Runtime Measurement Result Audit

## Audit Decision

- decision: `accept_m3090_artifacts_route_to_m3092_behavior_negative_repair_synthesis`
- audit status: `accepted_with_behavior_blocker`
- M3090 status_pass: `True`
- M3090 gate_matrix_pass: `True`
- required artifacts present: `True`
- contract guards pass: `True`
- claim-boundary guards pass: `True`
- parity outcome matches: `64/64`
- selected next action: `m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis`

## Evidence Summary

M3090 executed the packaged `ActiveSafetyReflexDriver.act(obs72)` deployable API as the full obs72-to-action3 action source on the complete 64-row M3084 fresh denominator. It recorded 64 episode rows, 0 execution failures, 43 successes, 5 obstacle-collision terminations, 5 off-track terminations, and 11 speed-too-low terminations.

The runtime path preserved the deployable contract: actor-visible obs72 input only, direct bounded action3 `[steer, throttle, brake]`, `runtime_base_policy_required=false`, `checkpoint_model_required=false`, no recurrent hidden state, and no hidden oracle, TTC, target, source, route, outcome, progress, or verdict actor input.

M3090 also recorded 64 same-row parity rows against M3084 helper-path rows. All 64 outcomes match, and the maximum clearance-margin and return deltas are both 0.0. This supports runtime integration parity only. It does not convert the rows into validation, ranking, promotion, driver-performance, robustness-result, current-sim verdict, high-fidelity, paper, full-driver, repair-success, or self-ID evidence.

## Supported Claims

- M3090 is a complete and claim-safe full-fresh deployable runtime measurement artifact set for audit.
- The packaged deployable API can run the full 64-row fresh denominator without execution failures.
- The packaged API reproduces M3084 same-row outcomes and selected scalar metrics exactly on this denominator.
- The actor contract remains obs72 to action3 direct `[steer, throttle, brake]` without runtime base policy, checkpoint model, recurrent hidden state, or hidden actor inputs.
- The branch can move to a behavior-negative repair synthesis because runtime packaging is no longer the blocker.

## Rejected Claims

- M3090 is not a validation result.
- M3090 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3090 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- Same-row parity is not behavior improvement; it only shows the deployable API matches the M3084 helper path.
- The 5 collision, 5 offtrack, and 11 speed-too-low rows cannot be hidden, averaged away, or treated as acceptable for the active-safety driver goal.

## Failure Taxonomy

- `contract_violation`: not observed; M3090 contract and hidden-input guards pass.
- `lineage_invalid`: not observed; M3090 routes from accepted M3089/M3088/M3086/M3084 artifacts.
- `metric_artifact`: not observed; row counts, finite metrics, parity rows, metric summaries, guards, and gate matrix are present.
- `scenario_sampling_failure`: not observed for M3090 scope; the full M3084 64-row denominator is accounted with 4 axes and 2 binding roles.
- `behavior_regression`: not decided as a regression against a different candidate; behavior blockers are present in the deployable path: 5 collision, 5 offtrack, and 11 speed-too-low rows.
- `objective_overfit`: active risk if the exact parity result is misread as progress toward safety rather than packaging parity.
- `proof_washout`: active risk if hard safety failures are summarized only by success rate or clearance mean.
- `seed_fragility`: unresolved; no broader validation or high-fidelity route is justified before repair synthesis.

## Public Gate Overfit Risk

Risk is medium. M3090 correctly broadened from the 8-row smoke panel to the full 64-row fresh denominator, but it is still the same current-sim denominator previously measured by M3084. The useful new evidence is deployable runtime parity, not improved behavior. Any next step that validates, promotes, ranks, or claims driver performance from these rows would overclaim.

The next route should therefore synthesize the observed safety blockers and choose a repair experiment that preserves the clean deployable contract. It must not tune hidden inputs, add a runtime base policy, use oracle labels, mutate a checkpoint, or reframe self-ID/GRU as the main route.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3092-engineering-controller-active-safety-driver-v1-full-fresh-runtime-behavior-negative-repair-synthesis
```

M3092 should use the M3090 artifacts to classify the non-success rows by termination reason, robustness axis, binding role, clearance/stability/action-pressure signatures, and same-row parity. It should then select one concrete repair route for the active-safety direct-action driver before any validation or promotion route.

M3092 must preserve the actor contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

## Boundary

M3091 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
