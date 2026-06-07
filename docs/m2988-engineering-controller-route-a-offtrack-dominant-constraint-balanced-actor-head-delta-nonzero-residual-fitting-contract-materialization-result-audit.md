# M2988 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Contract Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design`
- manifest: `experiments/manifests/m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-result-audit.json`
- audited M2987 summary: `runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/summary.json`
- audited M2987 directory: `runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight`
- follow-up manifest: `experiments/manifests/m2989-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.json`
- next: `m2989-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design`

## Audit Decision

M2988 accepts M2987 as a complete and claim-safe fitting-contract
materialization preflight.

Formal decision:

```text
accept_m2987_fitting_contract_materialization_claim_safe_route_to_m2989_fitting_admission_design
```

The accepted result is fitting-contract artifact materialization only. It is
complete enough to admit a bounded design-only fitting admission milestone, but
it is not target-quality validation, residual fitting readiness, residual
fitting, training, validation, ranking, promotion, repair success, driver
performance, paper evidence, current-sim evidence, high-fidelity evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.

## M2987 Result

M2987 passes the artifact and claim-boundary checks:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
dataset contract rows: 8
split denominator rows: 3
mask weight binding rows: 43
success identity zero-guard bindings: 13
stale guardrail exclusion bindings: 11
actor input exclusion rows: 14
checkpoint side-effect guard rows: 12
claim boundary rows: 18
gate rows: 20
actor observation/action: 72/action 3
target_action_delta_abs_max: 0.08
target_loss_weight_sum: 4204.0
target_quality_validated: false
target labels actor-visible: false
target provenance actor-visible: false
residual fitting/training/validation/ranking run: false
checkpoint mutated: false
```

## Contract Audit

M2987 materializes the contract surfaces needed before any future fitting
preflight can be considered:

```text
dataset surface and source artifact contract: materialized
candidate/success/stale split denominator contract: materialized
target mask and loss weight binding contract: materialized
success identity zero-target guard binding contract: materialized
stale fixed-source exclusion binding contract: materialized
actor input exclusion contract: materialized
checkpoint side-effect guard contract: materialized
claim-boundary rows: materialized
gate matrix rows: materialized
```

The split semantics are claim-safe:

```text
candidate target tensor rows: future fitting denominator after audit only
success identity rows: guard denominator only
stale fixed-source guardrails: excluded from fitting validation paper and self-ID denominators
```

## Actor And Claim Boundary Audit

M2987 preserves the actor contract and target-label boundary:

```text
actor observation/action: 72/action 3
actor input contract changed: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
target_quality_validated: false
success identity positive targets: 0
stale guardrail fitting denominator allowed: false
checkpoint mutation: false
residual fitting run: false
training run: false
validation run: false
ranking run: false
```

The M2987 rows are trainer-side contracts. They do not change actor inputs,
action shape, checkpoint lineage, deployment contract, or driver-performance
claims.

## Supported Claims

M2988 supports only:

```text
M2987 materialized complete fitting-contract artifacts from accepted M2983
target tensors and M2986 synthesis.

M2987 preserved 43 candidate target tensor rows, 13 success identity zero-target
guards, and 11 stale fixed-source exclusions.

M2987 preserved actor 72/action 3 and kept target labels, provenance, objective
families, source rows, route decisions, and audit verdicts actor-invisible.

M2987 did not fit, train, validate, rank, select, promote, mutate checkpoints,
or claim target quality, fitting readiness, repair success, or performance.

The next admissible step is a design-only fitting admission milestone.
```

These are artifact completeness, accounting, and claim-safety claims only.

## Rejected Claims

M2988 rejects:

```text
M2987 established target quality: false
M2987 established residual fitting readiness: false
M2987 fitted, trained, validated, ranked, selected, or promoted a residual head: false
M2987 changed actor inputs or action contract: false
M2987 proved repair success or driver performance: false
M2987 produced paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
```

## Next Route

M2988 selects exactly one next route:

```text
m2989-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design
```

M2989 must be design-only. It must decide whether the accepted M2987 fitting
contracts admit one bounded fitting preflight, require target-quality repair or
artifact repair, require another synthesis, or force stop. It must not fit,
train, validate, rank, select, promote, mutate checkpoints, or claim repair
success, driver performance, paper evidence, current-sim evidence,
high-fidelity evidence, finite-window-vs-GRU evidence, full-driver completion,
or self-ID evidence.
