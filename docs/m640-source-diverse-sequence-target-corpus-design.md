# M640 Source-Diverse Sequence Target Corpus Design

## Purpose

M640 designs the source-balanced sequence target corpus after M639.

Question:

```text
How do we convert 9885 accepted M639 sequence candidates into a training-ready
corpus without letting high-count sources dominate?
```

Answer:

```text
Use source-balanced caps, group-aware splits, and equal source weighting. Do not
train yet.
```

This is design-only:

```text
no rollout
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Parent Evidence

M639 passes the source-diversity admission-candidate gate:

```text
selected_source_rows: 9
accepted_source_rows: 9
accepted_unique_physical_pairs: 8
accepted_unique_left_seeds: 6
accepted_surfaces: 2
accepted_targets: 3
accepted_variants: 2
trust_limits_preserved: true
target_corpus_admission_candidate: true
```

But raw accepted counts are imbalanced:

| Source | Target | Accepted |
| ---: | --- | ---: |
| `13` | future_yaw_response | `2123` |
| `14` | future_yaw_response | `2123` |
| `20` | future_yaw_response | `1532` |
| `32` | future_yaw_response | `1532` |
| `5` | future_lateral_accel_response | `1062` |
| `8` | future_yaw_response | `664` |
| `30` | future_braking_deceleration | `515` |
| `0` | future_braking_deceleration | `200` |
| `7` | future_braking_deceleration | `134` |

So M639 is broad enough to design a corpus, but raw sampling would over-weight
sources `13`, `14`, `20`, and `32`.

## Corpus Design Principle

The unit of evidence is source-level, not candidate-level.

M641 should make a compact, source-balanced corpus:

```text
each source contributes comparable total weight
each grid style remains represented when available
each target remains represented
heldout split is source/group-aware
actor input contract remains unchanged
```

Source labels, target names, grid names, and split labels are training metadata.
They must never enter actor observation.

## Candidate Ranking

For each group, rank accepted candidates by:

```text
1. higher margin_improvement
2. higher risk_improvement
3. lower sequence_mean_l2
4. lower sequence_max_l2
5. lower max_delta_delta_l2
```

The selected row should retain enough metadata to reconstruct or rematerialize
the target sequence:

```text
source_index
coupling_row_index
candidate_id
grid_name
family
raw_family
sequence_length
surface
target
variant
left_seed
right_seed
left_step
right_step
steer_delta
throttle_delta
brake_delta
projection_scale
trust metrics
margin / risk metrics
split
corpus_weight
```

## Caps

Pre-register these caps for M641:

```text
max_rows_per_source: 64
max_rows_per_source_grid: 32
max_rows_per_source_family: 16
max_rows_per_source_sequence_length: 24
min_rows_per_source_if_available: 32
```

For low-count sources, use all available candidates up to the caps. Source `7`
has `134` accepted rows, so it can still contribute a full capped set.

The corpus should also keep a small best-per-source file:

```text
top1_per_source.csv
topk_per_source.csv
```

These files are diagnostic and useful for later exact objective sanity checks.

## Splits

M641 should create group-aware splits. Do not split the same physical pair across
train and validation.

Primary split:

```text
train sources:
  13, 20, 5, 30, 0, 8

source_holdout_validation sources:
  14, 32, 7
```

Rationale:

```text
train covers all three targets:
  future_yaw_response
  future_lateral_accel_response
  future_braking_deceleration

validation covers fresh and ood surfaces:
  source 14: fresh yaw
  source 32: ood yaw / wrong_matched_history
  source 7: fresh braking
```

There is only one accepted lateral-accel source (`5`), so lateral response cannot
be source-heldout in this corpus without removing that target from training.
M641 should document this explicitly.

## Weights

Use source-balanced weights:

```text
source_total_weight = 1.0 / accepted_source_rows
row_weight = source_total_weight / selected_rows_for_source
```

Optional secondary normalization:

```text
within each source, split weight across grid_name groups when both grids have
selected rows
```

Do not use raw accepted candidate counts as sampling weights.

## Sequence Tensor Materialization

M639 CSV artifacts contain accepted candidate metadata, but the final training
corpus needs actual action sequences.

M641 must therefore produce both:

```text
balanced_sequence_targets.csv
balanced_sequence_target_corpus.npz
```

Implementation options:

1. Re-run a deterministic materialization pass for selected candidates using
   their source row, grid name, family, deltas, sequence length, and projection
   scale.
2. Or extend the M639-style runner to retain target and base action sequences
   for selected capped candidates.

The NPZ should contain at least:

```text
target_action_sequences
base_action_sequences
sequence_lengths
source_indices
row_weights
split_ids
```

Use padding and sequence length metadata, matching the existing
`sequence_target_miner.write_sequence_target_corpus` convention where possible.

## Required M641 Artifacts

```text
runs/m641_source_diverse_sequence_target_corpus/summary.json
runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv
runs/m641_source_diverse_sequence_target_corpus/top1_per_source.csv
runs/m641_source_diverse_sequence_target_corpus/topk_per_source.csv
runs/m641_source_diverse_sequence_target_corpus/source_balance_summary.csv
runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz
docs/m641-source-diverse-sequence-target-corpus-implementation.md
```

Required summary keys:

```text
selected_rows
selected_sources
selected_physical_pairs
selected_left_seeds
selected_surfaces
selected_targets
selected_variants
rows_by_source
rows_by_grid
rows_by_split
max_rows_per_source
max_rows_per_source_grid
source_balanced_weights
sequence_npz_written
diagnostic_only
training_started
ppo_used
promoted
```

## M641 Pass Criteria

M641 passes as corpus infrastructure if:

```text
selected_sources >= 9
selected_physical_pairs >= 8
selected_left_seeds >= 6
selected_surfaces >= 2
selected_targets >= 3
max_rows_per_source <= 64
source_balanced_weights == true
sequence_npz_written == true
training_started == false
ppo_used == false
promoted == false
```

If NPZ materialization is blocked by missing information, M641 should fail as
`lineage_invalid` or `metric_artifact` rather than silently writing a CSV-only
training corpus.

## Next After M641

If M641 passes, admit:

```text
m642 sequence-corpus exact objective sanity
```

M642 should evaluate the corpus as an exact objective before any actor update:

```text
base action reconstruction sanity
target action distance sanity
source-balanced loss contribution sanity
heldout-source objective reporting
no actor parameter update
```

Only after M642 should we consider a very small BC-v2 / actor-coupling update.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
source_diverse_sequence_target_corpus_design_admit_m641
```

Next:

```text
m641-source-diverse-sequence-target-corpus-implementation
```
