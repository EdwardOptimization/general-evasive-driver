# M3197 Preterminal Authority Boundary-Stability Candidate Full-Fresh Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3196_measurement_route_to_m3198_neutral_result_synthesis`
- result class: `accept_m3196_complete_claim_safe_hard_safety_neutral_vs_m3105_and_m3181`
- source summary: `runs/m3196_engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_candidate_full_fresh_measurement_preflight/summary.json`
- M3196 status pass: true
- M3196 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3198-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-neutral-result-synthesis`

## Artifact Audit

M3196 is accepted as complete and claim-safe:

- scheduled measurement rows: 64
- measurement episode rows: 64
- measurement failures: 0
- same-row comparison rows: 128
- same-row comparison baselines: 64 M3105 rows and 64 M3181 rows
- exact seed matches: all same-row comparisons match
- contract guard rows: 10
- contract guard rows pass: true
- claim boundary rows: 9
- claim boundary rows pass: true
- gate matrix rows: 17
- gate matrix pass: true
- follow-up manifest registered: true

The measured runtime driver is:

```text
m3194_preterminal_authority_boundary_stability_candidate
```

## Measurement Audit

M3196 executed the same 64-row denominator used by M3105 and M3181:

- success count: 57
- collision count: 5
- offtrack count: 2
- speed-too-low count: 0
- clearance margin mean: 11.016418745957584

Against the M3105/M3103 deployable incumbent:

- success delta: 0
- collision delta: 0
- offtrack delta: 0
- speed-too-low delta: 0
- clearance margin mean delta: +0.03511151864840212
- return mean delta: -0.6785203007015541
- speed mean delta: -0.07846375797199438

Against M3181:

- success delta: 0
- collision delta: 0
- offtrack delta: 0
- speed-too-low delta: 0
- clearance margin mean delta: +0.014034883277526888
- return mean delta: -0.24684443254995947
- speed mean delta: -0.021781701208581486

The inherited blockers remain unchanged:

- collision blockers: 5
- offtrack blockers: 2
- speed-too-low blockers: 0

The failed M3196 rows are the same hard-safety count class as the incumbent:

- 5 obstacle-collision terminations
- 2 off-track terminations

## Contract Audit

M3196 preserves:

- observation contract: actor-visible obs72 only
- output contract: direct clipped action3
- action components: steer, throttle, brake
- hidden runtime actor inputs used: false
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- public driver default mutated: false
- checkpoint mutated or promoted: false

M3196 did run reset, step, policy action, and rollout for measurement. It did
not run validation, replay, ranking, training, PPO, checkpoint promotion,
high-fidelity simulation, or public driver mutation.

## Interpretation

M3196 is a complete full-fresh measurement but not an improvement over M3105 or
M3181. The M3194 candidate produces a small positive clearance-margin shift on
the measured denominator, but it does not reduce collisions, offtrack
terminations, or total failures.

This means the M3192-M3196 preterminal authority and boundary-stability
candidate route should not proceed to validation, deployable-default mutation,
ranking, winner selection, or promotion. The route needs synthesis before any
new implementation tuning.

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

M3197 accepts M3196 as complete and claim-safe, but hard-safety neutral versus
M3105 and M3181. It routes to M3198 neutral-result synthesis.

M3198 must decide whether to stop this candidate route, pivot to a diagnostic
trace-delta route, or define an artifact-repair route. It must not promote
M3194, mutate `ActiveSafetyReflexDriver`, run validation, claim repair success,
or continue narrow tuning without a synthesis decision.
