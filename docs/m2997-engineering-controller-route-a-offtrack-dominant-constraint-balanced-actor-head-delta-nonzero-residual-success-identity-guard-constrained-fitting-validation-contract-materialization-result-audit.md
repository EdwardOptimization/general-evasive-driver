# M2997 Engineering Controller Route A Actor-Head Delta Nonzero Residual Validation Contract Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2996_validation_contract_materialization_claim_safe_route_to_m2998_validation_contract_branch_synthesis`
- manifest: `experiments/manifests/m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-result-audit.json`
- audited M2996 summary: `runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight/summary.json`
- audited M2996 directory: `runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight`
- follow-up manifest: `experiments/manifests/m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis.json`
- next: `m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis`

## Audit Decision

M2997 accepts M2996 as a complete and claim-safe validation-contract
materialization preflight.

Formal decision:

```text
accept_m2996_validation_contract_materialization_claim_safe_route_to_m2998_validation_contract_branch_synthesis
```

The accepted result is contract materialization only. It is not target-quality
validation, closed-loop validation, repair success, driver performance, paper
evidence, current-sim verdict, high-fidelity evidence, finite-window-vs-GRU
evidence, full-driver completion, or self-ID evidence.

M2997 rejects direct validation execution from the materialized contracts. The
local-search guard also rejects continuing immediately to another ordinary
process-only validation design, because that would produce six consecutive
non-evidence milestones in the same branch. The next step must therefore be a
branch synthesis that integrates M2993-M2997, decides whether bounded
validation design is still justified, and explicitly chooses continue, pivot,
stop, or another legal route.

## M2996 Result

M2996 passes artifact and claim-boundary checks:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
validation contract rows: 43
residual-head wrapper contract rows: 3
parent comparison plan rows: 3
success-behavior-retention rows: 13
stale exclusion rows: 11
actor input exclusion rows: 14
checkpoint side-effect guard rows: 12
claim boundary rows: 18
gate matrix rows: 25
candidate residual-head artifact: present
linear_weight shape: 72 x 3
linear_bias shape: 3
observation/action: 72/3
residual_limit: 0.07999999821186066
success_guard_required_abs_max: 0.0010000000474974513
success-retention residual abs max: 0.00034158502239733934
target_quality_validated: false
validation/ranking/winner/promotion/checkpoint mutation: false
```

## Contract Audit

M2996 materialized the surfaces required before a bounded validation preflight
can be designed:

```text
residual-head metadata and dimension binding: materialized
read-only parent and candidate wrapper contract: materialized
action-boundary and residual clipping contract: materialized
candidate validation denominator over accepted M2993 fitting rows: materialized
success-behavior-retention guard plan: materialized
stale fixed-source exclusion plan: materialized
parent-vs-candidate comparison report-only contract: materialized
actor input invisibility and forbidden metadata checks: materialized
checkpoint side-effect guards: materialized
claim-boundary rows: materialized
gate matrix rows: materialized
```

The split semantics remain claim-safe:

```text
candidate rows: future validation denominator after audit only
success identity rows: success-retention guard denominator
stale fixed-source guardrails: excluded from validation, paper, and self-ID denominators
parent comparison: report-only, no ranking, no winner selection, no promotion
```

## Actor And Claim Boundary Audit

M2996 preserves the actor and side-effect boundaries:

```text
actor observation/action: 72/3
actor input contract changed: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
parent checkpoint read-only: true
candidate residual-head artifact read-only: true
environment reset or rollout run: false
validation run: false
ranking run: false
winner selected: false
checkpoint mutated: false
checkpoint promoted: false
private holdout used: false
performance measurement run: false
```

These contracts are consistent with the post-M2470 route split: current-sim
validation remains a bounded engineering diagnostic layer and cannot be
promoted to paper, high-fidelity, finite-window-vs-GRU, full-driver, or self-ID
evidence by assertion.

## Supported Claims

M2997 supports only:

```text
M2996 materialized complete validation-contract artifacts.

M2996 binds the M2993 residual-head artifact as a read-only 72x3/action-3
candidate with residual clipping and success-retention accounting.

M2996 preserved 43 candidate validation rows, 13 success-retention rows, and
11 stale fixed-source exclusions.

M2996 preserved actor 72/3 and kept target labels, target provenance,
objective families, source rows, route decisions, audit verdicts, and paper
labels actor-invisible.

M2996 did not validate, rank, select, promote, mutate checkpoints, run private
holdout, measure performance, or claim repair success, driver performance,
paper evidence, current-sim verdict, high-fidelity evidence, full-driver
completion, finite-window-vs-GRU evidence, or self-ID evidence.

The next admissible step is a branch synthesis before any further ordinary
process-only validation design.
```

These are artifact completeness, accounting, and claim-safety claims only.

## Rejected Claims

M2997 rejects:

```text
M2996 established target quality: false
M2996 established closed-loop validation readiness by itself: false
M2996 ran validation, ranked candidates, selected a winner, or promoted a checkpoint: false
M2996 proved repair success or driver performance: false
M2996 produced paper, current-sim verdict, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
candidate residual-head artifact is promotable: false
success-retention contract alone proves closed-loop behavior retention: false
```

## Next Route

M2997 selects exactly one next route:

```text
m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis
```

M2998 must be a synthesis milestone. It must answer the required synthesis
questions, identify public-gate overfit and process-overhead risk, and choose
whether to continue to bounded validation design, pivot, stop, or require a new
evidence surface. It must not run environment reset, step, rollout, validation,
ranking, winner selection, promotion, private holdout, performance
measurement, mutate checkpoints, or claim repair success, driver performance,
paper evidence, current-sim verdict, high-fidelity evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.
