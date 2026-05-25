# M875 V4 Pair-Delta Objective-Readiness Audit

## Purpose

M875 audits whether the M873 pair-delta corpus is ready for objective design or
actor update.

M875 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Artifact Completeness

M873 produced the objective-readiness inputs:

```text
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/summary.json
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/new_accepted_pair_delta_rows.csv
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/balanced_pair_delta_rows.csv
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/train_public_rows.csv
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/eval_public_rows.csv
runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/source_holdout_public_rows.csv
```

The run is clean:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

## Corpus Strength

M873 is a real improvement over M867/M870:

```text
new_accepted_pair_delta_rows: 39
accepted_pair_delta_rows: 273
balanced_pair_delta_rows: 56
balanced_unique_left_seed_count: 4
balanced_unique_left_source_group_count: 11
balanced_unique_left_fault_family_count: 8
balanced_unique_fault_family_pair_count: 27
```

New accepted rows cover:

```text
78057: 30
78048: 9
```

The combined balanced corpus covers:

```text
78058: 20
78050: 20
78048: 8
78057: 8
```

## Duplicate Pressure

The new M873 rows are not 39 independent closed-loop facts.

New accepted row counts:

```text
new accepted rows: 39
unique pair ids: 9
unique retarget geometries: 3
unique behavior tuples: 13
unique closed-loop signatures: 13
duplication factor rows/signatures: 3.0
```

All new accepted rows have:

```text
retarget_delta: 0.0
```

The three retarget axes are balanced in metadata:

```text
obstacle_half_width: 13
obstacle_lateral_offset: 13
obstacle_timing: 13
```

But because `retarget_delta == 0.0`, the axis labels duplicate the same
underlying geometry. This is useful for proving the M870 normal-window issue,
but it is too duplicate-heavy for direct objective training.

## Split Quality

The current source-aware split is not objective-ready:

```text
train_public_rows: 28
eval_public_rows: 16
source_holdout_public_rows: 12
```

Split contents:

```text
train:
  rows: 28
  seeds: 78050, 78058
  new M873 rows: 0

eval:
  rows: 16
  seeds: 78048, 78057
  new M873 rows: 16

source_holdout:
  rows: 12
  seeds: 78050, 78058
  new M873 rows: 0
```

This split is fine as a diagnostic split, but not for objective design:

```text
training would not see the new M873 rows;
eval would be dominated by exactly the new rows;
holdout would not test M873-style new evidence.
```

## 78055 Caveat

M873 found accepted normal-window candidates for all missing seeds:

```text
78048 accepted_window: 15
78055 accepted_window: 24
78057 accepted_window: 9
```

But new accepted pair-delta rows cover only:

```text
78048
78057
```

So `78055` remains a caveat:

```text
accepted normal-window candidates exist, but pair-delta sequence interventions
did not produce accepted primary rows for this seed.
```

This caveat does not erase the positive M873 result, but it blocks any claim
that the missing-seed problem is fully solved.

## Decision

M875 rejects direct objective design from the raw M873 split.

Decision:

```text
route_to_pair_delta_corpus_dedup_resplit_design
```

Required next step:

```text
m876-v4-pair-delta-corpus-dedup-resplit-design
```

M876 should design a no-training corpus transformation that:

```text
1. deduplicates M873 rows by closed-loop signature or retarget geometry;
2. preserves existing M867 evidence and new M873 evidence explicitly;
3. produces train/eval/holdout splits where each split's purpose is clear;
4. avoids using duplicate axis labels as independent training samples;
5. keeps the 78055 caveat explicit;
6. keeps objective training, PPO, and promotion blocked until the transformed
   corpus is audited.
```

## Failure Taxonomy

`objective_overfit`:

```text
Direct objective design on the raw M873 split would overfit duplicate delta=0
axis copies and a split where train has zero new rows.
```

`scenario_sampling_failure`:

```text
Reduced but not eliminated; 78055 still has no new accepted pair-delta rows.
```

`metric_artifact`:

```text
Axis-balance metrics overstate independent evidence when all new accepted rows
have retarget_delta 0.0.
```

`contract_violation`:

```text
Not observed.
```
