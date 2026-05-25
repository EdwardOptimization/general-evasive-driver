# M876 V4 Pair-Delta Corpus Dedup Resplit Design

## Purpose

M876 designs the no-training corpus transformation required after M875 rejected
direct objective design from the raw M873 split.

The design question is:

```text
How should the M873 pair-delta corpus be deduplicated and re-split so a later
objective-readiness audit can reason about unique evidence instead of repeated
axis labels?
```

M876 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## M875 Blocker

M873 is positive but not objective-ready in raw form:

```text
new accepted rows: 39
unique pair ids: 9
unique retarget geometries: 3
unique behavior tuples: 13
unique closed-loop signatures: 13
duplication factor rows/signatures: 3.0
retarget_delta: 0.0 for all new rows
```

The current split is also not objective-ready:

```text
train_public_rows: 28, new M873 rows: 0
eval_public_rows: 16, new M873 rows: 16
source_holdout_public_rows: 12, new M873 rows: 0
```

The next step must therefore transform the corpus before any objective design.

## Deduplication Key

M877 should deduplicate by closed-loop signature, not by row id or retarget
axis label.

Primary signature:

```text
left_source_group_id
right_source_group_id
left_step
right_step
left_seed
right_seed
left_fault_family
right_fault_family
retarget_target_body_x rounded to 1e-9
retarget_target_body_y rounded to 1e-9
retarget_target_half_width rounded to 1e-9
direction
hold_steps
epsilon_l2
normal_margin rounded to 1e-9
sequence_margin rounded to 1e-9
```

Fields intentionally excluded:

```text
pair_id
retarget_axis
normal_candidate_id
normal_boundary_source
```

Rationale:

```text
M873's new rows duplicate the same closed-loop outcome under three axis labels
when retarget_delta == 0.0. Those labels are useful diagnostics but should not
create independent objective samples.
```

Each deduplicated row should preserve duplicate metadata:

```text
dedup_signature
duplicate_row_count
duplicate_retarget_axes
duplicate_pair_ids
evidence_origin: existing_m867_or_m870 | new_m873
dedup_role: canonical
objective_sample_weight
```

Suggested weighting:

```text
objective_sample_weight = 1.0 for canonical dedup rows
duplicate_row_count is retained for diagnostics only, not as a training weight
```

## Existing vs New Evidence

M877 should keep evidence origin explicit:

```text
existing evidence:
  rows carried from M873 accepted_pair_delta_rows whose coverage_source is not
  m873_boundary_preserving.

new evidence:
  rows whose coverage_source == m873_boundary_preserving.
```

Expected new evidence after dedup:

```text
new_dedup_rows: 13
new left source groups: 12 and 33
new left seeds: 78048 and 78057
new missing caveat: 78055 remains absent from new accepted pair-delta rows
```

## Split Policy

M877 should produce purpose-specific splits rather than pretending the current
source split is objective-ready.

### Objective Train Public

Purpose:

```text
candidate training rows for later exact objective sanity, not yet used for
actor update.
```

Policy:

```text
include existing dedup rows from diverse source groups;
include at least one new M873 source group if available;
cap per source, seed, direction, and fault pair;
do not overweight duplicate groups.
```

### Objective Eval Public

Purpose:

```text
public diagnostic evaluation for transformed objective behavior.
```

Policy:

```text
include the other new M873 source group when possible;
include existing rows from source groups not used in train;
keep source overlap with train explicit in summary if unavoidable.
```

### Source Holdout Public

Purpose:

```text
source-held-out public diagnostic, mainly for existing M867/M870 evidence.
```

Constraint:

```text
Because new M873 accepted rows only cover two left source groups, a strict
three-way source split containing new rows in train, eval, and holdout is not
possible.
```

M877 should explicitly report:

```text
new_source_holdout_available: false
```

unless a strict held-out new source group can be assigned without starving
train/eval.

### New Signature Holdout Public

To compensate for limited new source groups, M877 should also write:

```text
new_signature_holdout_public_rows.csv
```

Purpose:

```text
within-source signature holdout for duplicate/behavior overfit checks on M873
new evidence.
```

This is not a replacement for private holdout or source generalization. It is a
public diagnostic that prevents later objective designs from using every new
closed-loop signature for fitting.

## Required Artifacts

M877 should write:

```text
src/autodrift/v4_pair_delta_corpus_dedup_resplit.py
tests/test_v4_pair_delta_corpus_dedup_resplit.py
runs/m877_v4_pair_delta_corpus_dedup_resplit/summary.json
runs/m877_v4_pair_delta_corpus_dedup_resplit/dedup_pair_delta_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/duplicate_group_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/objective_train_public_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/objective_eval_public_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/source_holdout_public_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/new_signature_holdout_public_rows.csv
runs/m877_v4_pair_delta_corpus_dedup_resplit/split_summary.json
runs/m877_v4_pair_delta_corpus_dedup_resplit/gate_summary.csv
docs/m877-v4-pair-delta-corpus-dedup-resplit-implementation.md
```

## Gates

Primary gates:

```text
dedup_rows > 0
new_dedup_rows >= 10
new_dedup_unique_left_source_group_count >= 2
new_duplicate_factor_after <= 1.25
objective_train_rows > 0
objective_eval_rows > 0
source_holdout_rows > 0
objective_train_new_rows > 0
objective_eval_new_rows > 0
new_signature_holdout_rows > 0
78055_caveat_recorded == true
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Classification:

```text
v4_pair_delta_corpus_dedup_resplit_pass
v4_pair_delta_corpus_dedup_resplit_split_limited
v4_pair_delta_corpus_dedup_resplit_too_sparse
v4_pair_delta_corpus_dedup_resplit_contract_violation
```

`pass` means the transformed corpus can be audited for objective design. It
does not mean objective training is admitted directly.

## Decision

Decision:

```text
pair_delta_corpus_dedup_resplit_design_admit_m877
```

Next:

```text
m877-v4-pair-delta-corpus-dedup-resplit-implementation
```
