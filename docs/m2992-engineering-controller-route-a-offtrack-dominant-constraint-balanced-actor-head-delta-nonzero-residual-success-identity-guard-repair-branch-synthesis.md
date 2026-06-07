# M2992 Engineering Controller Route A Actor-Head Delta Nonzero Residual Success-Identity Guard Repair Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2993_success_identity_guard_constrained_fitting_preflight`
- manifest: `experiments/manifests/m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-repair-branch-synthesis.json`
- synthesis artifact: `docs/m2992-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-repair-branch-synthesis.md`
- parent audit: `docs/m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-result-audit.md`
- parent fitting summary: `runs/m2990_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight/summary.json`
- parent success guard rows: `runs/m2990_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_fitting_preflight/success_guard_loss_rows.csv`
- follow-up manifest: `experiments/manifests/m2993-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-preflight.json`
- next: `m2993-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-preflight`

M2992 synthesizes the M2983-M2991 target tensor, fitting-contract, bounded
fitting, and result-audit chain after the local-search cadence guard blocked
another ordinary design-only milestone. It keeps the branch alive because
M2990 produced a real offline fitting artifact, but it rejects direct
validation because the fitted candidate violates the intended success-identity
zero-residual behavior.

## Synthesis Questions

### evidence_summary

The accepted evidence chain is:

```text
M2983: materialized 43 candidate target tensor rows and 13 success identity zero-target guard tensors.
M2984: accepted those target tensor artifacts as complete and claim-safe, while preserving target_quality_validated false.
M2987: materialized fitting contracts, split denominators, mask/weight bindings, success guard bindings, stale exclusions, actor-input exclusions, and checkpoint side-effect guards.
M2988: accepted those fitting contracts as complete and claim-safe, but not target-quality validation or fitting readiness.
M2989: admitted one bounded offline fitting preflight without validation or promotion.
M2990: produced a bounded linear residual-head fitting artifact and loss trace.
M2991: accepted M2990 as artifact-complete and claim-safe, but rejected direct validation because success-identity guard predictions are nonzero.
```

The M2990 artifact state is:

```text
status_pass: true
gate_matrix_pass: true
fitting dataset rows: 43
fitting samples: 4204
fitting weight sum: 4204.0
initial weighted MSE: 0.0010713406183980136
final weighted MSE: 0.000613389726277548
final weighted L1: 0.017207752913310462
candidate residual-head artifact exists: true
success identity zero-target guard rows: 13
success guard predicted residual abs max: 0.07999999821186066
stale exclusion rows: 11
target_quality_validated: false
validation/ranking/promotion/checkpoint mutation: false
```

The active blocker is not artifact availability. The active blocker is that the
success-identity rows are only excluded guard checks in M2990; they are not
enforced as a zero-residual condition during fitting.

### supported_claims

M2992 supports these bounded claims:

```text
M2983-M2991 define a complete trainer-side target and fitting artifact chain.

M2990 proves the bounded offline fitting mechanics can consume the accepted
candidate denominator without actor-input or checkpoint side-effect violations.

M2991 proves the fitted candidate must not enter validation or promotion
because success-identity guard traces can receive residual action up to 0.08.

The next evidence-changing route is a guard-constrained offline fitting
preflight that explicitly accounts for success-identity zero-target rows during
fitting or fails closed.
```

These are branch synthesis and route-selection claims only.

### falsified_claims

M2992 rejects:

```text
M2990 established target quality: false
M2990 established direct validation readiness: false
M2990 established closed-loop repair success: false
M2990 improved driver performance: false
M2990 produced paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
success guard finite/bounded pass means identity behavior is preserved: false
bounded residual clipping is sufficient to protect success traces: false
another ordinary design-only milestone is justified before synthesis: false
```

The bounded residual artifact is useful, but the success-identity guard result
falsifies a direct validation route.

### failure_taxonomy_summary

The active failure taxonomy is:

```text
behavior_regression risk:
  success traces that should preserve identity behavior can receive nonzero
  residual action, so already-successful behavior may degrade.

objective_overfit risk:
  the 43 fitting rows are offtrack-dominant and can dominate a linear residual
  head unless success-zero rows are part of the fitting objective or constraint.

metric_artifact risk:
  fitting MSE improvement is an offline target metric and cannot stand in for
  target quality, closed-loop repair success, or validation readiness.

proof_washout risk:
  repeatedly producing process artifacts after M2990 would hide the fact that
  no new closed-loop or validation evidence exists.

contract_violation risk:
  any guard repair that exposes target labels, provenance, objective/admission
  labels, source rows, route verdicts, or paper labels to actor input would
  violate the actor contract.
```

The stale fixed-source rows remain excluded from fitting, validation, paper,
and self-ID denominators.

### public_gate_overfit_risk

Public-gate overfit risk is medium. The branch is still inside the same
current-sim Route A actor-head delta surface, and the validator already forced
this synthesis because the branch had too many consecutive non-evidence
milestones.

The reason to continue once is concrete: M2990 changed the artifact state by
producing a fitted residual-head candidate, and M2991 exposed a specific,
machine-checkable blocker on success-identity zero-target traces. A
guard-constrained fitting preflight can change the artifact state again by
testing whether the residual fitting path can preserve identity behavior
without weakening actor or claim boundaries.

M2992 rejects:

```text
direct environment validation
ranking the M2990 candidate
promoting or mutating checkpoints
claiming repair success or driver performance from fitting loss
adding actor-visible target labels or route/verdict metadata
opening another unconstrained fitting route that repeats M2990
```

### next_branch_decision

Decision:

```text
continue_to_m2993_success_identity_guard_constrained_fitting_preflight
```

M2993 must be an offline artifact preflight, not a validation or promotion
route. It may implement a guard-constrained or guard-penalized fitting path
that consumes the same accepted candidate denominator while also using the 13
success-identity zero-target guard rows as an explicit zero-residual guard.

The M2993 acceptance boundary is:

```text
candidate fitting denominator: the accepted 43 candidate rows only
success identity rows: zero-residual guard/penalty/constraint rows only
stale fixed-source rows: excluded
target labels/provenance/objective/source/route/verdict labels actor-visible: false
checkpoint mutation or promotion: false
environment validation/ranking/private holdout/performance measurement: false
success guard residual required to improve materially from M2990 and be checked explicitly
```

M2993 should fail closed if the constrained fit cannot preserve success-zero
guard semantics. A failed M2993 would still be useful evidence: it would route
the branch toward architecture repair or stop instead of hiding the blocker.
