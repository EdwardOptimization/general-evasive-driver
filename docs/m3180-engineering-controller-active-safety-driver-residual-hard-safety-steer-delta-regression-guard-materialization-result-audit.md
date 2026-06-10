# M3180 Steer-Delta Regression Guard Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m3179_steer_delta_guard_route_to_m3181_full_fresh_measurement_preflight`
- result class: `accept_m3179_complete_claim_safe_route_to_full_fresh_measurement`
- source summary: `runs/m3179_engineering_controller_active_safety_driver_residual_hard_safety_steer_delta_regression_guard_materialization_preflight/summary.json`
- M3179 status pass: true
- M3179 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3181-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-full-fresh-measurement-preflight`

## Artifact Audit

M3179 is accepted as complete and claim-safe:

- rule rows: 1
- runtime contract rows: 1
- runtime contract rows pass: true
- action probe rows: 2
- action probe rows pass: true
- claim boundary rows: 12
- claim boundary rows pass: true
- gate matrix rows: 19
- gate matrix pass: true
- follow-up manifest registered: true

The materialized candidate is `m3179_steer_delta_regression_guard_overlay`. It computes M3105/M3103 fallback and M3170 overlay from actor-visible obs72 only, preserves M3170 throttle and brake deltas, and zeroes the M3170 steer delta relative to fallback.

## Contract Audit

M3179 preserves:

- observation contract: actor-visible obs72 only
- output contract: direct clipped action3
- action components: steer, throttle, brake
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- hidden oracle actor input required: false
- TTC actor input required: false
- public driver default mutated: false

M3179 did not run reset, step, rollout, replay, validation, ranking, training, PPO, checkpoint mutation, checkpoint promotion, or public driver mutation.

## Probe Audit

The actor-visible collision overlay probe confirms the intended materialization:

- M3170 steer delta: -0.07466667890548706
- M3179 steer delta: 0.0
- M3170 throttle delta: -0.13066667318344116
- M3179 throttle delta: -0.13066667318344116
- M3170 brake delta: 0.2239999771118164
- M3179 brake delta: 0.2239999771118164

This supports a measurement preflight, not a repair-success claim.

## Claim Boundary

Rejected claims:

- measurement result
- validation result
- driver-performance verdict
- current-sim verdict
- robustness result
- ranking or winner selection
- checkpoint promotion
- public driver default replacement
- high-fidelity validation result
- paper evidence
- finite-window-vs-GRU conclusion
- full ideal driver completion
- repair success
- feasibility proof
- level3 self-identification

## Decision

M3180 accepts M3179 as a complete steer-delta guard materialization artifact and routes to M3181 full-fresh measurement preflight on the same denominator before any validation or promotion. M3181 may execute the M3179 candidate and compare against M3105 and M3172 same-row evidence. It may not claim validation, driver performance, current-sim verdict, repair success, robustness result, high-fidelity readiness, paper evidence, or self-ID evidence.

M3105/M3103 remains the deployable incumbent until a later audited same-denominator measurement improves hard-safety counts without contract violations.
