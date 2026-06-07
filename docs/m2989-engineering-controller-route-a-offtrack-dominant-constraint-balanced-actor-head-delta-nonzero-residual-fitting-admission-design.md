# M2989 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Admission Design

## Metadata

- status: completed
- decision: `admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion`
- manifest: `experiments/manifests/m2989-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.json`
- parent audit: `docs/m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-result-audit.md`
- parent contracts: `runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-preflight.json`
- next: `m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-preflight`

## Design Decision

M2989 admits exactly one bounded residual fitting preflight.

Formal decision:

```text
admit_m2990_bounded_residual_fitting_preflight_without_validation_or_promotion
```

M2988 accepts M2987 fitting-contract materialization as complete and
claim-safe. That acceptance means the dataset, split, mask, weight,
success-identity, stale-exclusion, actor-input, side-effect, claim, and gate
contracts are now materialized enough for a bounded fitting attempt.

It does not mean target quality is validated. It also does not mean residual
fitting readiness, repair success, driver performance, paper evidence,
current-sim evidence, high-fidelity evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence. M2989 remains design-only and
does not fit, train, validate, rank, promote, execute, or mutate checkpoints.

The next route is M2990, a bounded offline fitting preflight that may consume
the accepted trainer-side target tensors and contract rows to produce a
candidate residual fitting artifact and loss trace for audit. M2990 must not
execute the environment, run validation, rank candidates, select a winner,
promote checkpoints, mutate the parent checkpoint, or make performance or
self-ID claims.

## Evidence Review

The accepted M2987/M2988 artifact state is:

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

The split semantics remain:

```text
candidate target tensor rows: future fitting denominator after audit only
success identity rows: guard denominator only
stale fixed-source guardrails: excluded from fitting, validation, paper, and self-ID denominators
```

## Admission Boundary

M2989 distinguishes four states:

```text
fitting-contract artifact availability: accepted
target-quality validation: false
legal bounded fitting preflight admission: true
deployment, validation, promotion, or performance readiness: false
```

The accepted contracts are sufficient to let M2990 attempt bounded offline
fitting, because the future fitting denominator is explicit, success identity
rows are guards, stale fixed-source rows are exclusions, and target labels and
provenance remain trainer-side metadata.

The accepted contracts are not sufficient to interpret any future loss decrease
as target quality, closed-loop repair, policy improvement, paper evidence, or
self-ID. M2990 can report fitting mechanics and guard behavior only. A later
M2991 result audit must accept or reject those artifacts before any further
route can be admitted.

## M2990 Preflight Contract

M2990 must consume:

```text
runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/summary.json
runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/mask_weight_binding_rows.csv
runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/success_identity_zero_guard_binding_rows.csv
runs/m2987_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_fitting_contract_materialization_preflight/stale_guardrail_exclusion_binding_rows.csv
runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight/target_tensor_rows.csv
runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight/target_tensors/*.npz
docs/m2988-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-result-audit.md
```

M2990 may:

```text
build a trainer-side fitting dataset from the 43 candidate mask/weight rows
use target_valid_mask and target_loss_weight for bounded loss computation
use success identity rows only as zero-residual guard checks
write fitting_dataset_rows.csv, fitting_loss_trace_rows.csv, success_guard_loss_rows.csv, gate_matrix.csv, and summary.json
write one candidate fitting artifact for audit
register M2991 result audit
```

M2990 must not:

```text
use target labels, target provenance, objective family, admission labels, source labels, route labels, verdict labels, or paper labels as actor inputs
include stale fixed-source guardrails in fitting, validation, paper, or self-ID denominators
convert success identity zero guards into positive residual targets
run environment reset, rollout, policy validation, ranking, winner selection, checkpoint promotion, or private holdout
mutate, replace, or promote the parent checkpoint
claim repair success, driver performance, paper evidence, current-sim evidence, high-fidelity evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence
```

## Actor And Guard Boundaries

M2989 preserves the existing actor contract:

```text
actor observation/action: 72/action 3
actor input contract changed: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
hidden/oracle/future-target actor input: false
success identity positive targets: 0
stale guardrail fitting denominator allowed: false
checkpoint mutation: false
```

Any residual head fitted by M2990 must be trained from actor-view observation
tensors plus trainer-side target deltas. Target metadata remains outside the
actor input path. The parent checkpoint remains read-only, and any candidate
artifact produced by M2990 is audit material only.

## Supported Claims

M2989 supports only:

```text
M2987/M2988 provide accepted fitting-contract artifacts for 43 candidate
target tensors, 13 success identity zero guards, and 11 stale exclusions.

The accepted contracts make one bounded offline residual fitting preflight
admissible.

M2990 is the only selected next route.
```

These are admission and route claims only.

## Rejected Claims

M2989 rejects:

```text
target quality validated: false
residual fitting executed in M2989: false
residual training executed in M2989: false
validation/ranking/promotion executed: false
winner selected: false
checkpoint mutated: false
repair success proved: false
driver performance improved: false
paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## Route Contract

M2989 selects exactly one next route:

```text
m2990-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-preflight
```

M2990 must be an artifact-only offline fitting preflight. It must register
M2991 result audit and fail closed if the accepted contracts cannot be consumed
without weakening target-quality, success-identity, stale-exclusion,
actor-input, checkpoint side-effect, or claim boundaries.
