# M845 V4 Source-Diverse Sequence-Effective Corpus Audit

## Purpose

M845 audits M844 before any new corpus implementation or objective design.

The audit question is:

```text
Did M844 convert M841's sparse sequence-effectiveness evidence into a strong
source-diverse corpus, or should the next branch build real cross-source pairs?
```

M845 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
docs/m844-v4-source-diverse-sequence-effective-corpus-implementation.md
runs/m844_v4_source_diverse_sequence_effective_corpus/summary.json
runs/m844_v4_source_diverse_sequence_effective_corpus/diversity_summary.json
runs/m844_v4_source_diverse_sequence_effective_corpus/gate_summary.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/accepted_sequence_effective_rows.csv
runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv
```

M844 result class:

```text
v4_source_diverse_sequence_effective_corpus_source_limited
```

## Artifact And Contract Audit

M844 produced the expected corpus artifacts:

```text
candidate_source_rows: 39
boundary_rows: 39
reconstructed_snapshot_rows: 20
sequence_effective_rows: 1404
accepted_primary_sequence_effective_rows: 57
train_public_rows: 41
eval_public_rows: 11
source_holdout_public_rows: 5
```

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

The actor contract remains P0 human-view. M844 did not add hidden parameters,
fault labels, oracle feasibility, TTC, reference-path error, slip, tire force,
or controller-mode inputs to the actor. The sequence overrides remain offline
diagnostics only.

## Corpus Quality Audit

M844 improved source diversity relative to M841:

```text
M841 accepted rows: 73
M844 accepted rows: 57

M841 unique_left_source_group_count: 4
M844 unique_left_source_group_count: 10

M841 max_left_source_group_dominance: 0.5616
M844 max_left_source_group_dominance: 0.2807
```

That is a real improvement: the accepted source-group gate now passes.

But M844 does not pass the strong corpus gate:

```text
accepted_primary_sequence_effective_rows: 57 < 120
unique_left_seed_count: 3 < 4
unique_left_fault_family_count: 4 < 5
unique_fault_family_pair_count: 4 < 8
max_left_seed_dominance: 0.4211 > 0.35
```

The strongest evidence is still component-sequence controllability:

```text
direction families:
  throttle_axis: 30
  steer_axis:    20
  brake_axis:     7

hold_steps:
  6: 36
  4: 21
```

M844 has no pair-delta rows:

```text
pair_delta_positive rows: 0
pair_delta_negative rows: 0
```

This was expected because M844 used self-pair boundary rows to broaden source
coverage. But it means the corpus still does not test whether different source
dynamics imply different short-horizon maneuver intent.

## Boundary Surface Audit

The M844 boundary source before sequence filtering is broader than the accepted
sequence rows:

```text
boundary_rows: 39
boundary unique_left_source_group_count: 20
boundary unique_left_seed_count: 4
boundary unique_left_fault_family_count: 7
boundary unique_fault_family_pair_count: 7
```

After the component sequence scan, accepted rows collapse to:

```text
accepted unique_left_source_group_count: 10
accepted unique_left_seed_count: 3
accepted unique_left_fault_family_count: 4
accepted unique_fault_family_pair_count: 4
```

So the limitation is not only boundary availability. It is also that the
self-pair/component sequence filter accepts a narrower subset and cannot
exercise pair-delta directions.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. M844 improves source coverage but remains below the strong corpus
thresholds for rows, seeds, fault families, and fault-family pairs.

### metric_artifact

Secondary label. Direct sequence override success is a controllability
diagnostic. It does not prove learned response-history self-identification and
must not be used as a promotion claim.

### not contract_violation

Checksums stayed fixed, no training started, and no forbidden actor input was
introduced.

## Supported Claims

M845 supports:

- M844 is a useful no-training source-diversity improvement over M841.
- Short-horizon sequence controllability is still real, with max margin
  movement `0.0159017`.
- The branch has enough signal to continue data construction.
- The branch does not yet have enough source/fault diversity for objective
  training.

## Unsupported Claims

M845 does not support:

- PPO admission;
- checkpoint promotion;
- learned self-ID proof;
- outcome-coupled sequence objective training on the M844 corpus as-is;
- claiming pair-delta evidence from M844.

## Next Control Variable

The next highest-leverage step is a real cross-source sequence-effective pair
refresh.

M846 should design a no-training paired corpus construction that:

```text
1. pairs near-boundary states across distinct source groups and fault families;
2. requires matched ego/obstacle geometry and low normal margins on both sides;
3. computes pair-delta sequence directions from the paired policy actions;
4. replays pair-delta and component sequence overrides;
5. writes source-aware train/eval/source-holdout splits;
6. falls back to expanded boundary bracketing only if valid cross-source pairs
   are too sparse.
```

The goal is not yet to train. The goal is to test whether source-diverse
near-boundary states support pair-delta sequence evidence, which M844 could not
test.

## Decision

Decision:

```text
admit_cross_source_sequence_effective_pair_refresh_design
```

Next:

```text
m846-v4-cross-source-sequence-effective-pair-refresh-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and outcome-coupled objective training remain blocked.
