# M1613 Paper-Route Contour-Aware Candidate Materialization Result Audit

## Summary

M1613 audits the M1612 offline candidate materialization result.

Decision:

```text
contour_aware_candidate_materialization_audit_admit_corpus_design
```

M1612 is a valid public artifact pass: 39 clean candidate rows were
materialized from primary rows, 232 diagnostic guardrail rows were kept
separate, and no training corpus was exported. The next step may design a
candidate corpus, but must not export it or train.

## Evidence

Candidate artifacts:

```text
candidate_directed_pair_count: 39
candidate_source_edge_count: 4
max_candidate_source_edge_share: 0.3333333333333333
candidate_rows_from_primary_only: true
candidate_rows_all_clean: true
candidate_rows_missing_variants_count: 0
candidate_pair_ids_unique: true
```

Diagnostic guardrails:

```text
diagnostic_guardrail_directed_pair_count: 232
diagnostic_reason_count: 3
diagnostic_dominated_or_control_count: 81
diagnostic_clean_share: 0.008620689655172414
diagnostic_rows_enter_candidate_rows: false
```

Process guardrails:

```text
candidate_materialized: true
candidate_materialization_only: true
training_corpus_exported: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

## Supported Claims

M1613 supports:

```text
M1612 correctly materialized public-pass candidate artifacts;
diagnostic guardrails remain separate from candidate rows;
the materialized artifacts are eligible for design-only corpus planning;
exact pair ids and source-edge accounting are preserved.
```

## Unsupported Claims

M1613 does not support:

```text
training corpus export;
loss/objective construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification.
```

## Public-Gate Overfit Risk

Risk:

```text
high
```

Reasons:

```text
candidate set is only 39 rows;
all artifacts come from public proof rows;
diagnostic guardrails protect row honesty but do not prove distribution-level behavior;
no private holdout or fresh scenario distribution was used.
```

Mitigation:

```text
design corpus before exporting it;
keep candidate and diagnostic rows in separate roles;
include explicit public-proof labeling and no-paper-claim metadata;
require corpus-export audit before any actor update or PPO.
```

## Route Decision

Admit design-only corpus planning:

```text
m1614-paper-route-contour-aware-candidate-corpus-design
```

M1614 should define how candidate rows, diagnostic guardrails, weights, metadata,
and failure gates would be assembled if a later export is admitted. It must not
export `training_corpus.csv`, build a loss, train, run PPO, or promote.

## Guardrails

```text
training_corpus_exported: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1614-paper-route-contour-aware-candidate-corpus-design
```
