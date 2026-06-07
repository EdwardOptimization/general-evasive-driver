# M2994 Engineering Controller Route A Actor-Head Delta Nonzero Residual Success-Identity Guard-Constrained Fitting Result Audit

## Metadata

- status: completed
- decision: `accept_m2993_artifact_claim_safe_route_to_m2995_validation_admission_design`
- manifest: `experiments/manifests/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit.json`
- audited M2993 summary: `runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/summary.json`
- audited M2993 directory: `runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight`
- follow-up manifest: `experiments/manifests/m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design.json`
- next: `m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design`

## Audit Decision

M2994 accepts M2993 as a complete and claim-safe guard-constrained offline
fitting artifact package.

Formal decision:

```text
accept_m2993_artifact_claim_safe_route_to_m2995_validation_admission_design
```

The accepted result is artifact completeness, explicit success-identity guard
accounting, and claim-boundary preservation only. M2993 is not accepted as
target-quality validation, closed-loop repair success, deployment readiness,
ranking admission, promotion admission, driver-performance evidence, paper
evidence, current-sim evidence, high-fidelity evidence, finite-window-vs-GRU
evidence, full-driver completion, or self-ID evidence.

M2994 rejects direct validation or promotion from the fitting artifact alone.
The success-identity blocker that stopped M2990 is repaired at the offline
artifact level, but M2993 still has not loaded the residual head into an actor
wrapper, executed an environment, replayed a policy, validated target quality,
or tested closed-loop behavior. The next route must therefore be a bounded
validation-admission design, not execution.

## M2993 Result

M2993 passes artifact and side-effect checks:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
fitting dataset rows: 43
fitting samples: 4204
candidate weight sum: 4204.0
guard weight multiplier: 1000.0
success guard samples: 1416
success guard weight sum: 4203999.5
initial candidate weighted MSE: 0.0010713406183980136
final candidate weighted MSE: 0.001065189191153038
final combined weighted MSE: 1.0671760360409562e-06
M2990 success guard predicted residual abs max: 0.07999999821186066
M2993 success guard predicted residual abs max: 0.00034158502239733934
M2993 success guard predicted residual MSE: 3.053894363285702e-09
success guard required abs max: 0.001
success guard improved from M2990: true
success guard zero residual satisfied: true
candidate residual head artifact exists: true
```

The M2993 artifact contains a bounded linear residual head:

```text
linear_weight shape: 72 x 3
linear_bias shape: 3
residual_limit: 0.07999999821186066
observation/action: 72/3
```

M2993 produced a more conservative candidate fit than M2990 on the candidate
denominator, but it repaired the explicit success-identity guard behavior at
the offline artifact level. That tradeoff is acceptable for artifact audit
because the fitting loss remains no worse than the zero-residual baseline and
the success guard no longer produces a residual near the action-delta bound.

## Row And Gate Audit

M2994 audits the M2993 machine-checkable rows:

```text
gate matrix rows: 29, failures: 0
guard constrained loss trace rows: 2, failures: 0
success guard loss rows: 13, failures: 0
stale exclusion audit rows: 11, failures: 0
claim boundary rows: 17, failures: 0
actor input exclusion rows: 14
checkpoint side-effect guard rows: 12
```

The 13 success identity rows were used as zero-residual guard penalty or
constraint samples, not as positive target rows and not as fitting denominator
rows. Every success guard row reports:

```text
guard_penalty_or_constraint_used: true
improved_from_m2990: true
zero_residual_guard_satisfied: true
```

The 11 stale fixed-source guardrails remain excluded from fitting,
validation, paper, and self-ID denominators.

## Actor And Claim Boundary Audit

M2993 preserves the actor and side-effect boundaries:

```text
actor observation/action: 72/3
target quality validated: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
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

M2994 supports only:

```text
M2993 produced complete guard-constrained offline fitting artifacts.

The fitting denominator contains 43 candidate rows and 4204 weighted samples.

The candidate weighted MSE remained no worse than the zero-residual baseline:
0.0010713406183980136 to 0.001065189191153038.

The success identity guard residual improved from M2990 0.07999999821186066 to
0.00034158502239733934 and satisfies the 0.001 threshold.

M2993 preserved 13 success-identity zero-target guard rows and 11 stale
exclusion rows as guard/accounting surfaces rather than actor inputs or
validation denominators.

M2993 preserved actor 72/3 and kept target labels, target provenance, objective
families, source rows, route decisions, and audit verdicts actor-invisible.

M2993 did not validate, rank, select, promote, mutate checkpoints, or claim
repair success, driver performance, paper evidence, current-sim evidence,
high-fidelity evidence, full-driver completion, finite-window-vs-GRU evidence,
or self-ID evidence.
```

These are artifact completeness, offline fitting mechanics, guard accounting,
and claim-safety claims only.

## Rejected Claims

M2994 rejects:

```text
M2993 established target quality: false
M2993 established direct validation readiness: false
M2993 established deployment readiness: false
M2993 established closed-loop repair success: false
M2993 improved driver performance: false
M2993 produced paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
candidate residual-head artifact is promotable: false
success guard repair alone proves closed-loop behavior retention: false
```

The material reason for rejecting direct validation is not the success guard
residual anymore. The new blocker is validation admission: the branch needs a
bounded design that states exactly how the candidate artifact may be wrapped,
loaded, compared against the parent policy, checked for success behavior
retention, and audited without mutating checkpoints or turning a current-sim
artifact into performance or paper evidence.

## Next Route

M2994 selects exactly one next route:

```text
m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design
```

M2995 must be design-only. It must decide whether the accepted M2993 artifact
admits one bounded validation-preflight route, requires artifact repair,
requires additional target-quality checks, forces synthesis, or stops the
branch. It must not run environment validation, rank candidates, select a
winner, mutate or promote checkpoints, claim repair success, claim driver
performance, claim current-sim or high-fidelity validation, claim
finite-window-vs-GRU evidence, claim full ideal driver completion, or claim
self-ID evidence.
