# M2991 Engineering Controller Route A Actor-Head Delta Nonzero Residual Bounded Fitting Result Audit

## Metadata

- status: completed
- decision: `accept_m2990_artifact_claim_safe_reject_direct_validation_route_to_m2992_success_identity_guard_repair_branch_synthesis`
- manifest: `experiments/manifests/m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-result-audit.json`
- audited M2990 summary: `runs/m2990_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight/summary.json`
- audited M2990 directory: `runs/m2990_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight`
- follow-up manifest: `experiments/manifests/m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-repair-branch-synthesis.json`
- next: `m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-repair-branch-synthesis`

## Audit Decision

M2991 accepts M2990 as a complete and claim-safe bounded offline fitting
artifact package.

Formal decision:

```text
accept_m2990_artifact_claim_safe_reject_direct_validation_route_to_m2992_success_identity_guard_repair_branch_synthesis
```

The accepted result is artifact completeness and claim-boundary preservation
only. M2990 is not accepted as target-quality validation, deployment
readiness, closed-loop repair, direct validation admission, ranking admission,
promotion admission, driver-performance evidence, paper evidence,
current-sim evidence, high-fidelity evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

M2991 rejects direct validation or promotion because the success-identity
zero-target guard rows are not yet respected by the fitted candidate: the
maximum predicted residual on those rows is `0.07999999821186066`, equal to
the residual bound. The next route must repair or constrain the
success-identity guard behavior before any validation route is considered.

## M2990 Result

M2990 passes artifact and side-effect checks:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
fitting dataset rows: 43
fitting samples: 4204
fitting weight sum: 4204.0
initial weighted MSE: 0.0010713406183980136
final weighted MSE: 0.000613389726277548
final weighted L1: 0.017207752913310462
fitting loss improved or equal: true
candidate residual head artifact exists: true
success guard rows: 13
success guard predicted residual abs max: 0.07999999821186066
stale exclusion audit rows: 11
target_quality_validated: false
validation run: false
ranking run: false
checkpoint mutated: false
driver performance claim made: false
paper claim made: false
level3 self-ID claim made: false
```

The fitting trace is useful because it shows the bounded offline fitting
mechanics can consume the accepted trainer-side target tensors and contract
rows without mutating checkpoints or changing the actor contract. It is not a
target-quality or closed-loop capability result.

## Guard Audit

The M2990 success-identity zero-target rows are guard rows, not fitting
denominators:

```text
success identity zero-target guard rows: 13
fitting denominator used on success rows: false
target action delta abs max on success rows: 0.0
predicted residual abs max on success rows: 0.07999999821186066
success guard rows finite and bounded: true
success guard rows zero-residual satisfied: false
```

The M2990 gate marks these guard rows as passing because they are present,
finite, bounded, and excluded from the fitting denominator. That is a
claim-safety check. It is not evidence that the fitted residual head preserves
identity behavior on already-successful traces.

This is the decisive blocker for direct validation. A residual head that can
inject up to `0.08` action delta on success-identity traces may degrade already
successful behavior. The next milestone must choose a claim-safe repair route,
such as constrained fitting, an explicit guard penalty, an architectural
identity gate, or a stop/pivot if those would violate the actor or claim
boundary.

## Actor And Claim Boundary Audit

M2990 preserves the actor and side-effect boundaries:

```text
actor observation/action: 72/action 3
actor contract shape 72/action 3: true
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
stale fixed-source guardrails in fitting denominator: false
environment reset or rollout run: false
validation run: false
ranking run: false
winner selected: false
checkpoint mutated: false
checkpoint promoted: false
private holdout used: false
```

The candidate residual-head artifact is audit material only. It does not alter
the parent checkpoint and must not be treated as a deployed or promoted driver.

## Supported Claims

M2991 supports only:

```text
M2990 produced complete bounded offline fitting artifacts.

The fitting denominator contains 43 candidate rows and 4204 weighted samples.

The weighted fitting MSE decreased from 0.0010713406183980136 to
0.000613389726277548 under the bounded offline fitting preflight.

M2990 preserved 13 success-identity zero-target guard rows and 11 stale
exclusion rows as guard/accounting surfaces rather than actor inputs or
validation denominators.

M2990 preserved actor 72/action 3 and kept target labels, target provenance,
objective families, source rows, route decisions, and audit verdicts
actor-invisible.

M2990 did not validate, rank, select, promote, mutate checkpoints, or claim
repair success, driver performance, paper evidence, current-sim evidence,
high-fidelity evidence, full-driver completion, finite-window-vs-GRU evidence,
or self-ID evidence.
```

These are artifact completeness, offline fitting mechanics, guard accounting,
and claim-safety claims only.

## Rejected Claims

M2991 rejects:

```text
M2990 established target quality: false
M2990 established direct validation readiness: false
M2990 established deployment readiness: false
M2990 established closed-loop repair success: false
M2990 improved driver performance: false
M2990 produced paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
success guard finite/bounded pass means identity behavior is preserved: false
candidate residual-head artifact is promotable: false
```

The success-identity guard residual is the material reason for rejecting a
direct validation or promotion route after M2990.

## Next Route

M2991 selects exactly one next route:

```text
m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-repair-branch-synthesis
```

M2992 must be branch-synthesis only. It must answer the synthesis questions
and choose one claim-safe repair, pivot, or stop route for the nonzero residual
on success-identity guard traces. It must not run fitting, training,
validation, ranking, promotion, environment rollout, checkpoint mutation,
private holdout, performance measurement, paper evidence, high-fidelity
validation, finite-window-vs-GRU comparison, full-driver completion, or
self-ID evaluation.
