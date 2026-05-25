# M768 V4 Fresh Source-Holdout Wave Audit

## Purpose

M768 audits the M767 disjoint-seed fresh source-holdout wave before any M761
residual replay, PPO, checkpoint promotion, or generalization claim.

The question is:

```text
Is the M767 fresh corpus clean enough for a limited residual holdout replay,
despite failing the stricter exporter corpus gate?
```

This audit is process-only:

```text
no residual replay
no actor training
no residual retraining
no PPO
no checkpoint promotion
```

## Evidence Summary

M767 produced three artifacts:

```text
runs/m767_v4_source_holdout_extreme_faults
runs/m767_v4_source_holdout_sequence_intervention
runs/m767_v4_source_holdout_corpus_export
```

Freshness:

```text
M749/M752/M755 seed range: 76000..76511
M767 seed range: 76512..77023
seed overlap: none
```

Corpus export result:

```text
result_class: v4_sequence_outcome_corpus_sparse
positive_rows: 995
normal_rows: 995
positive_intervention_rows: 995
hard_negative_rows: 1028
positives_without_hard_negative: 150
hard_negative_complete: true

positive_sentinel_rows: 0
duplicate_positive_keys: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0
positive_claim_boundary_levels:
  current_model_or_proxy

unique_positive_seeds: 25
unique_positive_fault_family_pairs: 13
max_positive_seed_dominance: 0.247236
max_positive_fault_family_pair_dominance: 0.265327
```

Strict exporter gates failed:

```text
positive_rows: 995 < 1000
unique_positive_fault_family_pairs: 13 < 16
max_positive_seed_dominance: 0.247236 > 0.2
```

M766 limited-holdout minimum gates passed:

```text
positive_rows >= 100
unique_positive_seeds >= 10
unique_positive_fault_family_pairs >= 6
max_positive_seed_share <= 0.25
claim_boundary_levels == [current_model_or_proxy]
sentinel_positive_rows == 0
missing_normal_matches == 0
metadata_missing_rows == 0
```

## Interpretation

M767 is not a clean broad source-holdout corpus under the stricter exporter
thresholds. It is, however, a fresh, clean, sizable limited holdout:

```text
fresh seed range
995 positives
25 seeds
13 fault-family pairs
0 sentinel positives
0 missing normal matches
0 metadata misses
hard-negative contrast available
```

Therefore M768 admits only a limited residual holdout replay with caveats. It
does not admit a promotion gate, PPO, or a broad generalization claim.

## Supported Claims

M768 supports:

```text
1. A fresh disjoint-seed corpus exists and is large enough for a limited
   residual holdout replay.

2. The corpus is metadata-clean and sentinel-clean.

3. The fresh source-holdout replay should be explicitly labeled limited /
   sparse because source balance is weaker than the public M755/M761 corpus.
```

## Falsified Claims

M768 falsifies:

```text
1. M767 produced no useful fresh holdout data.

2. M767 is clean enough for broad generalization or promotion claims.

3. Residual replay should proceed without caveats.
```

M768 does not prove:

```text
1. M761 residual generalizes.

2. M761 residual improves or preserves holdout closed-loop mechanism metrics.

3. PPO safety.

4. True four-wheel / single-wheel physical fault fidelity.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
M767 narrowly misses strict corpus gates and has source/fault-pair
concentration. This limits claim scope but does not block a limited holdout
replay.
```

Not failures:

```text
not metadata_artifact
not private_holdout_contamination
not contract_violation
not proof_washout
not training_instability
not promotion_gate_failure
```

## Next Branch Decision

Decision:

```text
promote_to_limited_residual_holdout_replay_design
```

M769 should design a no-PPO limited residual holdout replay:

```text
input corpus:
  runs/m767_v4_source_holdout_corpus_export/positive_sequence_outcomes.csv
  runs/m767_v4_source_holdout_corpus_export/contrast_rows.csv

primary alpha:
  0.2

diagnostic alphas:
  0.5
  1.0

base alpha:
  0.0
```

Pass/fail must be reported as limited source-holdout evidence only. A positive
M770 implementation would still need another audit before any stronger claim.

PPO and checkpoint promotion remain blocked.
