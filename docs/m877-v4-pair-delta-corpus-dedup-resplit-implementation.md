# M877 V4 Pair-Delta Corpus Dedup Resplit Implementation

## Purpose

M877 implements the M876 no-training corpus transformation.

The implementation question is:

```text
Can the M873 pair-delta corpus be deduplicated by closed-loop signature and
re-split so later objective design is not driven by repeated retarget-axis
labels?
```

M877 is no-training:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Command

```bash
PYTHONPATH=src python -m autodrift.v4_pair_delta_corpus_dedup_resplit \
  --accepted-pair-delta-rows runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/accepted_pair_delta_rows.csv \
  --new-accepted-pair-delta-rows runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/new_accepted_pair_delta_rows.csv \
  --run-dir runs/m877_v4_pair_delta_corpus_dedup_resplit
```

## Implementation

M877 adds:

```text
src/autodrift/v4_pair_delta_corpus_dedup_resplit.py
tests/test_v4_pair_delta_corpus_dedup_resplit.py
```

The tool:

```text
1. computes a closed-loop signature that excludes pair_id and retarget_axis;
2. collapses duplicate axis-label rows into one canonical sample;
3. preserves duplicate metadata such as axes and pair ids;
4. labels evidence_origin as existing_m867_or_m870 or new_m873;
5. writes objective_train, objective_eval, source_holdout, and
   new_signature_holdout public splits.
```

## Result

M877 passed the registered gates:

```text
result_class: v4_pair_delta_corpus_dedup_resplit_pass
raw_rows: 273
raw_new_rows: 39
dedup_rows: 247
existing_dedup_rows: 234
new_dedup_rows: 13
new_dedup_unique_left_seed_count: 2
new_dedup_unique_left_source_group_count: 2
new_duplicate_factor_before: 3.0
new_duplicate_factor_after: 1.0
caveat_78055_recorded: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Split result:

```text
objective_train_rows: 124
objective_train_new_rows: 8
objective_eval_rows: 22
objective_eval_new_rows: 2
source_holdout_rows: 98
source_holdout_new_rows: 0
new_signature_holdout_rows: 3
new_source_holdout_available: false
new_train_eval_source_overlap: false
```

## Split Interpretation

The transformed split fixes M875's immediate blockers:

```text
train now contains new M873 evidence;
eval now contains new M873 evidence;
new duplicate factor is reduced from 3.0 to 1.0;
new signature holdout preserves within-source unseen signatures.
```

But source holdout still has no new M873 rows:

```text
source_holdout_new_rows: 0
new_source_holdout_available: false
```

This is expected because new M873 accepted rows only cover two left source
groups:

```text
left_source_group_id 33: 10 dedup signatures
left_source_group_id 12: 3 dedup signatures
```

So the transformed corpus can be audited for objective design, but it cannot
support a claim of source-held-out new-evidence generalization.

## Gate Summary

```text
dedup_rows: pass
new_dedup_rows: pass
new_duplicate_factor_after: pass
objective_train_new_rows: pass
objective_eval_new_rows: pass
new_signature_holdout_rows: pass
caveat_78055_recorded: pass
ppo_blocked: pass
```

## Interpretation

Supported claims:

```text
M877 removes the most obvious duplicate-axis artifact from M873.
The transformed corpus has new M873 evidence in train and eval.
The 78055 caveat remains visible.
The transformed corpus is ready for an objective-readiness audit.
```

Unsupported claims:

```text
M877 admits objective training directly.
M877 proves learned self-identification.
M877 provides source-held-out new M873 evidence.
M877 solves the 78055 caveat.
M877 promotes a checkpoint.
```

Failure taxonomy:

```text
objective_overfit:
  reduced by deduplication and new-signature holdout.

scenario_sampling_failure:
  still present because 78055 and new source holdout remain limited.

metric_artifact:
  reduced by excluding retarget-axis labels from the dedup key.

contract_violation:
  not observed.
```

## Decision

Decision:

```text
v4_pair_delta_corpus_dedup_resplit_pass
```

Next:

```text
m878-v4-deduped-pair-delta-objective-readiness-audit
```
