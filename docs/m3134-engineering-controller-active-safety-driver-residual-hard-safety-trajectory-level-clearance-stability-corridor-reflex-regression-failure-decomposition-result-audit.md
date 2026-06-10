# M3134 Corridor Reflex Regression Failure Decomposition Result Audit

## Decision

- decision: `accept_m3133_regression_decomposition_reject_standalone_corridor_route_to_m3135_guarded_fallback_hybrid_materialization`
- selected next action: `m3135-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-preflight`
- result class: `accept_m3133_complete_claim_safe_behavior_negative_decomposition`

## Evidence Summary

M3133 is complete and claim-safe as a no-new-execution regression decomposition artifact:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
source full-fresh rows: 64
decomposition rows: 64
M3105 same-row comparison rows: 64
M3105 exact seed matches: 64
row identity preserved: True
same-row M3105 alignment preserved: True
no new execution: True
repair_success_claim_made: False
driver_performance_claim_made: False
```

The decomposition confirms that the standalone M3129 corridor reflex is a behavior-negative route against M3105:

```text
success delta vs M3105: -22
collision delta vs M3105: +2
offtrack delta vs M3105: +12
speed_too_low delta vs M3105: +8
clearance margin delta mean vs M3105: -2.429528843793889
return delta mean vs M3105: -70.2271982962308
speed mean delta mean vs M3105: -1.8374728781348109
success regressions: 22
success improvements: 0
added collision rows: 2
added offtrack rows: 12
added speed-too-low rows: 8
clearance-margin regressions: 44
return regressions: 60
stability regressions: 46
```

Primary regression axes:

```text
added_collision_regression: 2
added_offtrack_regression: 12
added_speed_floor_regression: 8
clearance_margin_loss: 31
return_or_success_loss: 6
stability_recovery_loss: 5
```

## Accepted Claims

- M3133 artifacts are complete and claim-safe.
- M3133 preserves M3131 row identity and M3105 same-row exact-seed alignment.
- M3133 shows that standalone corridor reflex behavior regresses broad fresh-denominator safety and recovery metrics against M3105.
- M3133 supports rejecting a standalone corridor-reflex continuation.
- M3133 supports a next guarded fallback/hybrid materialization route that defaults to the M3105 no-regression baseline and admits corridor behavior only behind actor-visible regression guards.

## Rejected Claims

- M3133 is not repair-success evidence.
- M3133 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.
- M3133 does not justify another blind corridor gain edit.
- M3133 does not justify using M3133 row labels, M3105 outcomes, source labels, route labels, verdict labels, hidden oracle values, or TTC as runtime actor inputs.
- M3133 does not promote M3105 or M3129 as a final full driver.

## Failure Taxonomy

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: observed and decomposed.
- `objective_overfit`: observed risk for standalone corridor reflex.
- `proof_washout`: high risk if M3133 is described as a repair result instead of a decomposition.
- `seed_fragility`: unresolved; no validation or robustness claim is allowed.

## Next

Route to M3135 guarded fallback/hybrid materialization. M3135 should materialize a deployable direct `[steer, throttle, brake]` action function that preserves the M3105 behavior as the default path and gates any corridor-style adjustment behind actor-visible hard-safety guards. It must block the regression axes exposed by M3133: added offtrack, added speed-too-low, added collision, clearance-margin loss, return loss, and stability/recovery loss. M3135 is still a materialization preflight only and must not claim measurement success, validation, ranking, promotion, driver performance, robustness result, current-sim verdict, high-fidelity result, feasibility proof, or self-ID evidence.
