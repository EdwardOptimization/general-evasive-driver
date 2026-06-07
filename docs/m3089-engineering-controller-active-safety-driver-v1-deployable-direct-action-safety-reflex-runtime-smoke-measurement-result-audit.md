# M3089 Active Safety Driver v1 Deployable Runtime-Smoke Measurement Result Audit

## Audit Decision

- decision: `accept_m3088_runtime_smoke_route_to_m3090_full_fresh_runtime_measurement_preflight`
- audit status: `accepted`
- M3088 status_pass: `True`
- M3088 gate_matrix_pass: `True`
- required artifacts present: `True`
- contract guards pass: `True`
- claim-boundary guards pass: `True`
- selected next action: `m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight`

## Evidence Summary

M3088 executed the packaged `ActiveSafetyReflexDriver.act(obs72)` deployable API as the full action source on 8/8 pre-registered smoke rows. It recorded 0 execution failures, 6 successes, 0 collisions, 1 offtrack termination, and 1 speed-too-low termination. The all-row smoke success rate is 0.75, mean clearance margin is 10.288422972097099, and mean action clip fraction is 0.0.

The denominator covered 4 robustness axes and 2 binding roles. The contract rows preserve obs72/action3 `direct_action_clipped` `[steer, throttle, brake]`, `runtime_base_policy_required=false`, `checkpoint_model_required=false`, no recurrent hidden state, and no hidden oracle, TTC, target, source, route, outcome, progress, or verdict actor input.

## Supported Claims

- M3088 is a complete deployable runtime-smoke artifact set for M3089 audit.
- The packaged runtime API can reset and step through the bounded smoke panel without integration failures.
- The deployable actor contract remains obs72 to action3 direct `[steer, throttle, brake]` with no runtime base policy or checkpoint model dependency.
- The result is safe to route to a broader deployable runtime measurement preflight.

## Rejected Claims

- M3088 is not a validation result.
- M3088 is not a ranking, winner-selection, or promotion result.
- M3088 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- The 8-row smoke denominator is not broad enough to decide whether behavior is sufficient; the one offtrack and one speed-too-low row remain measurement facts for the next audit path.

## Failure Taxonomy

- `contract_violation`: not observed; contract, source-package, sample-action, and hidden-input guards pass.
- `lineage_invalid`: not observed; M3087, M3086, M3084, and M3012 sources are present and accepted.
- `metric_artifact`: not observed; 8 rows are accounted, selected metrics are finite, and metric summary rows exist.
- `scenario_sampling_failure`: not observed for smoke scope; axis count is 4 and binding-role count is 2.
- `behavior_regression`: not decided here; offtrack and speed-too-low outcomes are behavior signals, not runtime-smoke execution failures.
- `objective_overfit`: residual risk remains medium because M3088 is a small existing-row smoke panel.
- `proof_washout`: not applicable; this branch is deployable runtime integration, not self-ID proof.
- `seed_fragility`: not decided; next step must broaden over the full M3084 fresh denominator.

## Public Gate Overfit Risk

Risk is medium. M3088 used a small, deterministic smoke sample derived from existing M3084 rows. It is appropriate for runtime packaging and integration, but not for behavior ranking or validation. The next route must not tune the driver or reselect rows after seeing M3088; it should run the packaged API over the full existing M3084 fresh denominator and compare same-row runtime parity before any stronger interpretation.

## Next Branch Decision

Route exactly one follow-up to `m3090-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-full-fresh-runtime-measurement-preflight`. M3090 should execute the packaged deployable API over the complete 64-row M3084 fresh robustness denominator, preserve the same actor and claim boundaries, write runtime measurement and same-row parity artifacts, and register M3091 result audit. M3090 still must not claim validation, ranking, promotion, driver performance, current-sim verdict, robustness result, high-fidelity, paper, full-driver completion, repair success, or self-ID.
