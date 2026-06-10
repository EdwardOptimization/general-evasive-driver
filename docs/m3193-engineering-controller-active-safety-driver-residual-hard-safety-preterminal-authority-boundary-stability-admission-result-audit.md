# M3193 Preterminal Authority Boundary-Stability Admission Result Audit

## Summary

- status: completed
- decision: `accept_m3192_admission_route_to_m3194_candidate_implementation_materialization`
- result class: `accept_m3192_complete_claim_safe_implementation_materialization_admitted_after_audit`
- source summary: `runs/m3192_engineering_controller_active_safety_driver_residual_hard_safety_preterminal_authority_boundary_stability_admission_materialization_preflight/summary.json`
- M3192 status pass: true
- M3192 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3194-engineering-controller-active-safety-driver-residual-hard-safety-preterminal-authority-boundary-stability-candidate-implementation-materialization-preflight`

## Artifact Audit

M3192 is accepted as complete and claim-safe:

- implementation admission rows: 3
- implementation-recommended rows: 2
- guard-only rows: 1
- rule contract rows: 9
- forbidden-label guard rows: 5
- claim boundary rows: 11
- gate matrix pass: true
- follow-up manifest registered: true

M3192 admits two candidate implementation families after this audit:

- `preterminal_clearance_authority_timing`: targets the five collision blockers
  across `clearance_timing_axis` and `boundary_recovery_collision_axis`.
- `boundary_stability_recovery_authority`: targets the two offtrack blockers
  across `boundary_recovery_stability_axis`.

M3192 keeps `action_authority_saturation_guard` as a cross-cutting guard only.
It is not a standalone implementation thesis.

## Contract Audit

The admitted candidate implementation route must preserve:

```text
obs72 actor-visible input -> direct [steer, throttle, brake] action3
```

Accepted implementation surface:

- deterministic candidate artifact only.
- actor runtime input remains obs72 only.
- allowed actor-visible proxies are ego speed, obstacle geometry, relative
  clearance, lane corridor geometry, lateral error, heading alignment, sideslip
  proxy, and lane boundary geometry as represented in obs72.
- output remains clipped direct action3.
- M3105/M3103 remains the deployable incumbent until a later measurement and
  audit show a hard-safety improvement.

Forbidden implementation surface:

- hidden oracle labels, TTC, target/source/route/outcome/progress/verdict
  labels, baseline outcomes, future terminal status, runtime base policy,
  checkpoint model, recurrent hidden state, ranking, checkpoint promotion, and
  public driver default mutation.

## Decision

M3193 accepts M3192 and routes to M3194 candidate implementation
materialization.

M3194 may materialize a deterministic obs72-to-action3 candidate artifact using
the two admitted rule families:

- earlier pre-terminal collision-clearance authority timing,
- boundary-stability recovery authority,
- action-authority saturation as a guard against terminal-only overfit.

M3194 must not run measurement or validation and must not mutate
`ActiveSafetyReflexDriver` as the public default. It must write candidate
policy/config/rule/contract/action-probe/claim/gate/doc artifacts and an M3195
result-audit manifest.

## Claim Boundary

M3193 is result audit and route selection only. It makes no repair-success,
measurement, validation, ranking, promotion, driver-performance, current-sim
verdict, high-fidelity, full-driver, robustness-result, feasibility-proof,
paper, finite-window-vs-GRU, or self-ID claim.
