# M3182 Steer-Delta Regression Guard Full-Fresh Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3181_measurement_route_to_m3183_equivalence_synthesis`
- result class: `accept_m3181_complete_claim_safe_regression_neutral_vs_m3105`
- source summary: `runs/m3181_engineering_controller_active_safety_driver_residual_hard_safety_steer_delta_regression_guard_full_fresh_measurement_preflight/summary.json`
- M3181 status pass: true
- M3181 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3183-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-equivalence-synthesis`

## Artifact Audit

M3181 is accepted as complete and claim-safe:

- scheduled measurement rows: 64
- measurement episode rows: 64
- measurement failures: 0
- same-row comparison rows: 128
- same-row comparison baselines: 64 M3105 rows and 64 M3172 rows
- exact seed matches: all same-row comparisons match
- contract guard rows: 10
- contract guard rows pass: true
- claim boundary rows: 9
- claim boundary rows pass: true
- gate matrix rows: 16
- gate matrix pass: true
- follow-up manifest registered: true

The measured runtime driver is `m3179_steer_delta_regression_guard_overlay`.

## Measurement Audit

M3181 executed the same 64-row denominator used by M3172:

- success count: 57
- collision count: 5
- offtrack count: 2
- speed-too-low count: 0
- clearance margin mean: 11.002383862680057

Against the M3105/M3103 deployable incumbent:

- success delta: 0
- collision delta: 0
- offtrack delta: 0
- speed-too-low delta: 0

Against the M3172 source-localized candidate:

- success delta: +1
- collision delta: -1
- offtrack delta: 0
- speed-too-low delta: 0

This accepts M3181 as evidence that the M3179 steer-delta guard removes the
single M3170/M3172 new collision regression on the measured denominator. It
does not show improvement over the M3105/M3103 incumbent.

## Contract Audit

M3181 preserves:

- observation contract: actor-visible obs72 only
- output contract: direct clipped action3
- action components: steer, throttle, brake
- hidden runtime actor inputs used: false
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- public driver default mutated: false
- checkpoint mutated or promoted: false

M3181 did run reset, step, policy action, and rollout for measurement. It did
not run validation, replay, ranking, training, PPO, checkpoint promotion, or
public driver mutation.

## Interpretation

M3181 is a regression-neutral measurement versus M3105 and a recovery from the
behavior-negative M3172 result. The accepted interpretation is:

- M3177 localized the new M3172 collision regression to the M3170 steer delta.
- M3179 materialized a direct obs72-to-action3 guard that zeros that steer
  delta while preserving the M3170 throttle and brake overlay.
- M3181 measured the guard on the full fresh denominator and restored M3105
  hard-safety parity.
- The seven inherited residual blockers remain: 5 collision rows and 2
  offtrack rows.

M3105/M3103 remains the deployable incumbent because M3181 does not improve the
same-denominator hard-safety counts over M3105.

## Claim Boundary

Rejected claims:

- validation result
- driver-performance verdict
- current-sim verdict
- robustness result
- ranking or winner selection
- checkpoint promotion
- public driver default replacement
- high-fidelity validation readiness or result
- paper evidence
- finite-window-vs-GRU conclusion
- full ideal driver completion
- repair success
- feasibility proof
- level3 self-identification

## Decision

M3182 accepts M3181 as a complete full-fresh measurement and routes to M3183
equivalence synthesis. M3183 must decide whether to close the steer-delta guard
branch, keep M3179 only as regression-neutral evidence, and pivot to a new
residual-blocker evidence axis. It must not promote M3179, mutate the public
driver default, claim repair success, or continue narrow steer-delta tuning.
