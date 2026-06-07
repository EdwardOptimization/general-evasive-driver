# M2995 Engineering Controller Route A Actor-Head Delta Nonzero Residual Success-Identity Guard-Constrained Fitting Validation Admission Design

## Metadata

- status: completed
- decision: `admit_m2996_validation_contract_materialization_preflight_without_validation_or_promotion`
- manifest: `experiments/manifests/m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design.json`
- parent audit: `docs/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit.md`
- parent fitting summary: `runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/summary.json`
- parent residual-head artifact: `runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/candidate_residual_head_artifact.npz`
- follow-up manifest: `experiments/manifests/m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-preflight.json`
- next: `m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-preflight`

## Design Decision

M2995 admits exactly one validation-contract materialization preflight.

Formal decision:

```text
admit_m2996_validation_contract_materialization_preflight_without_validation_or_promotion
```

M2994 accepts M2993 as a complete and claim-safe guard-constrained offline
fitting artifact package. That acceptance means the residual-head artifact is
worth preparing for a bounded validation route. It does not mean the artifact
is validation-ready, promotable, or driver-performance evidence.

M2995 therefore does not run environment validation, rank candidates, select a
winner, promote checkpoints, mutate the parent checkpoint, or make repair
success, performance, paper, current-sim, high-fidelity, full-driver,
finite-window-vs-GRU, or self-ID claims.

The next route is M2996, a no-execution validation-contract materialization
preflight. M2996 must turn the accepted M2993/M2994 artifacts and this design
into machine-checkable wrapper, comparison, guard, side-effect, and claim rows
before any closed-loop validation can be considered.

## Evidence Review

The accepted M2993/M2994 artifact state is:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
fitting dataset rows: 43
fitting samples: 4204
candidate weighted MSE: 0.0010713406183980136 to 0.001065189191153038
M2990 success guard residual abs max: 0.07999999821186066
M2993 success guard residual abs max: 0.00034158502239733934
success guard required abs max: 0.001
success guard rows: 13
success guard rows satisfied: true
stale exclusion rows: 11
actor observation/action: 72/3
target_quality_validated: false
validation/ranking/promotion/checkpoint mutation: false
```

The accepted residual-head artifact is bounded and actor-shape compatible:

```text
linear_weight shape: 72 x 3
linear_bias shape: 3
residual_limit: 0.07999999821186066
guard_weight_multiplier: 1000.0
success_guard_required_abs_max: 0.001
```

The M2993 result changes the validation-admission question. The previous
blocker was success-identity residual behavior; M2994 accepts that blocker as
repaired at the offline artifact level. The remaining blocker is execution
contract materialization: the artifact has not yet been wrapped into a
read-only actor-head delta policy, compared against the parent policy, or
gated for success-behavior retention in closed loop.

## Admission Boundary

M2995 distinguishes four states:

```text
offline guard-constrained fitting artifact accepted: true
validation-contract materialization admitted: true
closed-loop validation executed: false
repair success, driver performance, paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim: false
```

The accepted artifact is sufficient to design and materialize validation
contracts because it includes actor-view dimensions, residual bounds,
success-identity guard metadata, fitting dataset rows, stale exclusions, and
side-effect guards. It is not sufficient for direct validation because the
evaluation wrapper, parent-comparison denominator, success-behavior-retention
gate, action-boundary semantics, and checkpoint side-effect policy are not yet
machine-checkable.

## M2996 Materialization Contract

M2996 must consume:

```text
docs/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit.md
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/summary.json
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/candidate_residual_head_artifact.npz
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/fitting_dataset_rows.csv
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/success_guard_loss_rows.csv
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/stale_exclusion_audit_rows.csv
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/actor_input_exclusion_rows.csv
runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/checkpoint_side_effect_guard_rows.csv
docs/m2995-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-admission-design.md
```

M2996 must write machine-checkable artifacts for:

```text
residual-head artifact metadata and dimension binding
read-only parent checkpoint and candidate residual-head wrapper contract
action-boundary and residual clipping contract
candidate validation denominator plan over the accepted 43 fitting rows
success-behavior-retention guard plan over the 13 success identity rows
stale fixed-source exclusion plan over the 11 stale guardrails
parent-vs-candidate comparison contract without ranking or winner selection
actor input invisibility and forbidden metadata checks
checkpoint side-effect guards
target_quality_validated false accounting
claim-boundary rows
gate matrix rows
one follow-up result-audit manifest
```

M2996 may produce one future bounded validation-preflight route only if those
contracts are complete and claim-safe. It must not execute environment reset,
step, rollout, policy validation, ranking, winner selection, checkpoint
promotion, private holdout, performance measurement, high-fidelity adapter
probe, paper comparison, finite-window-vs-GRU comparison, full-driver gate, or
self-ID evaluation.

## Required Future Validation Semantics

If a later audit accepts M2996 and admits a bounded validation preflight, that
future validation must be constrained by these semantics:

```text
parent checkpoint: read-only
candidate residual head: read-only artifact loaded into wrapper
actor input shape: 72
action shape: 3
actor-visible metadata additions: none
target tensors and labels: not actor-visible
candidate denominator: audited rows only, not stale rows
success retention denominator: 13 success identity rows or an audited superset
parent comparison: report-only, no ranking, no winner selection, no promotion
success-rate/performance claim: forbidden before result audit
current-sim verdict: forbidden before result synthesis
self-ID claim: forbidden
```

This keeps the validation path aligned with the post-M2470 route split:
current-sim remains a bounded engineering diagnostic layer and must not become
paper, high-fidelity, finite-window-vs-GRU, full-driver, or self-ID evidence by
assertion.

## Actor And Guard Boundaries

M2995 preserves the existing actor contract:

```text
actor observation/action: 72/3
actor input contract changed: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
hidden/oracle/future-target actor input: false
success identity positive targets: false
stale guardrail validation denominator allowed: false
checkpoint mutation: false
```

The M2993 residual head remains an external trainer-side artifact until a later
materialization and audit prove that it can be wrapped read-only without
weakening actor, guard, stale-exclusion, target-quality, checkpoint, or claim
boundaries.

## Supported Claims

M2995 supports only:

```text
M2993/M2994 provide an accepted guard-constrained offline fitting artifact.

The accepted artifact is actor-shape compatible and success-identity guarded
enough to justify one validation-contract materialization preflight.

Direct validation remains blocked until wrapper, comparison, success-retention,
side-effect, stale-exclusion, actor-input, and claim-boundary contracts are
materialized and audited.

M2996 is the only selected next route.
```

These are design and admission-boundary claims only.

## Rejected Claims

M2995 rejects:

```text
M2993/M2994 established target quality: false
direct closed-loop validation admitted without contract materialization: false
closed-loop validation executed in M2995: false
validation/ranking/promotion executed: false
winner selected: false
checkpoint mutated: false
repair success proved: false
driver performance improved: false
paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## Route Contract

M2995 selects exactly one next route:

```text
m2996-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-preflight
```

M2996 must be no-execution contract materialization only. It must fail closed
if the accepted M2993 residual-head artifact cannot be bound to a read-only
validation wrapper without weakening target-quality, success-identity,
stale-exclusion, actor-input, checkpoint side-effect, or claim boundaries.
