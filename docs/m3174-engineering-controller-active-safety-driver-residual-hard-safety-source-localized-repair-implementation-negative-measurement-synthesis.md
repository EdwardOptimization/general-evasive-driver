# M3174 Residual Hard-Safety Source-Localized Repair Implementation Negative-Measurement Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3175_behavior_negative_source_repair_decomposition_materialization`
- synthesis decision: pivot
- source audit: `docs/m3173-engineering-controller-active-safety-driver-residual-hard-safety-source-localized-repair-implementation-full-fresh-measurement-result-audit.md`
- source measurement: `runs/m3172_engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_full_fresh_measurement_preflight/summary.json`
- incumbent preserved: M3105/M3103 deployable direct-action driver
- selected next route: `m3175-engineering-controller-active-safety-driver-residual-hard-safety-behavior-negative-source-repair-decomposition-materialization-preflight`

## Evidence Summary

M3172 is artifact-complete and claim-safe, but behavior-negative against the current M3105/M3095 incumbent:

- full-fresh denominator: 64/64 rows
- measurement failures: 0
- M3172 success/collision/offtrack/speed-too-low: 56/6/2/0
- same-row comparisons: 256
- vs M3105: success -1, collision +1, offtrack 0, speed-too-low 0
- vs M3095: success -1, collision +1, offtrack 0, speed-too-low 0
- runtime contract: obs72 actor-visible input to direct `[steer, throttle, brake]`
- runtime base policy required: false
- validation, promotion, repair-success, robustness-result, performance, current-sim verdict, high-fidelity, paper, full-driver, feasibility-proof, and self-ID claims: all false

The single negative same-row regression versus M3105 is:

- measurement episode: `m3172-measurement-episode-0020`
- baseline episode: `m3105-measurement-episode-0020`
- fresh panel row: `m3082-fresh-panel-0020`
- axis: `offtrack_boundary_recovery`
- binding role: `parent`
- task family: `T5`
- eval seed: `401611`
- M3172 outcome: collision failure, clearance margin -0.11747365908727159, speed mean 8.274531189806964
- M3105 outcome: success, clearance margin 0.2678248895862312, speed mean 7.458127909213799

M3172 also inherits the prior hard-safety blockers: five collision rows and two offtrack rows remain on the complete denominator, with one of the six collision rows being newly introduced relative to M3105.

## Supported Claims

- M3172 provides complete full-fresh measurement artifacts for an M3170 source-localized candidate.
- The M3170 candidate preserves the direct action API shape and the no-runtime-base-policy contract.
- The M3170 candidate is not a deployable replacement for M3105/M3103 because it worsens same-denominator hard-safety counts.
- The next branch must isolate the behavior-negative source before another implementation attempt.

## Falsified Claims

- M3170/M3172 is not repair success.
- M3170/M3172 is not a promotion candidate.
- M3170/M3172 is not a validation result or driver-performance verdict.
- Same-row gains versus weaker older baselines do not override the regression versus M3105/M3095.
- The current source-localized overlay cannot be continued as-is.

## Failure Taxonomy Summary

- behavior_regression: one same-row M3105 success became an M3172 collision on `offtrack_boundary_recovery` parent row `m3082-fresh-panel-0020`.
- objective_overfit: the overlay improves some older-baseline comparisons but loses against the incumbent target denominator.
- lineage_invalid risk avoided: M3174 preserves M3105/M3103 as incumbent and routes away from promotion.
- contract_violation risk not observed: actor input and action output contracts remain intact.

## Public Gate Overfit Risk

The risk is medium. The negative row is only one row, but it occurs on the accepted 64-row fresh denominator and exactly against the incumbent. Optimizing directly for that row would be too narrow; the next step must therefore materialize a decomposition panel that separates:

- newly introduced collision regression versus M3105,
- inherited collision blockers,
- inherited offtrack blockers,
- actor-visible feature families that can be used in a future repair,
- labels and row outcomes that must stay out of actor runtime inputs.

## Next Branch Decision

M3174 pivots to M3175 behavior-negative source repair decomposition. M3175 may use existing M3172, M3173, M3170, and M3105 artifacts to produce no-new-execution decomposition rows, guard rows, claim rows, and a result-audit manifest.

M3175 must not implement or mutate the public driver. It must first prove whether the added collision can be decomposed into an actor-visible repair hypothesis. If the decomposition needs hidden row labels, source labels, outcome labels, baseline outcomes, route labels, progress labels, or verdict labels as runtime actor inputs, the route must stop or pivot again.

## Claim Boundary

M3174 is synthesis and route selection only. It makes no validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, full-driver, repair-success, robustness-result, feasibility-proof, paper, finite-window-vs-GRU, or self-ID claim.
