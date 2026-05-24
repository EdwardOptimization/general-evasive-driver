# M641 Source-Diverse Sequence Target Corpus Implementation

## Purpose

M641 implements the M640 source-balanced sequence target corpus design. It
converts the M639 accepted projected sequence candidates into capped metadata,
source-balanced weights, heldout-source split metadata, and a materialized NPZ
sequence target corpus.

This is an infrastructure milestone only. It does not train, run PPO, update an
actor, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_diverse_sequence_target_corpus \
  --accepted-sequences runs/m639_combined_shape_source_diversity_expansion/accepted_expanded_sequences.csv \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --source-table runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --run-dir runs/m641_source_diverse_sequence_target_corpus
```

## Artifacts

- `runs/m641_source_diverse_sequence_target_corpus/summary.json`
- `runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv`
- `runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz`
- `runs/m641_source_diverse_sequence_target_corpus/top1_per_source.csv`
- `runs/m641_source_diverse_sequence_target_corpus/topk_per_source.csv`
- `runs/m641_source_diverse_sequence_target_corpus/source_balance_summary.csv`

## Result

```text
selected_rows: 431
selected_sources: 9
selected_physical_pairs: 8
selected_left_seeds: 6
selected_surfaces: 2
selected_targets: 3
selected_variants: 2
max_rows_per_source: 64
max_rows_per_source_grid: 32
source_balanced_weights: true
sequence_npz_written: true
training_started: false
ppo_used: false
promoted: false
```

Rows by source:

| Source | Split | Rows | Weight Sum |
| --- | --- | ---: | ---: |
| 0 | train | 24 | 0.111111 |
| 5 | train | 48 | 0.111111 |
| 7 | source_holdout_validation | 32 | 0.111111 |
| 8 | train | 32 | 0.111111 |
| 13 | train | 64 | 0.111111 |
| 14 | train | 64 | 0.111111 |
| 20 | source_holdout_validation | 64 | 0.111111 |
| 30 | train | 39 | 0.111111 |
| 32 | source_holdout_validation | 64 | 0.111111 |

Rows by grid:

| Grid | Rows |
| --- | ---: |
| `source7_preservation_style` | 211 |
| `source8_recovery_style` | 220 |

Rows by split:

| Split | Rows |
| --- | ---: |
| `train` | 271 |
| `source_holdout_validation` | 160 |

The heldout split keeps the shared physical-pair sources `20` and `32`
together, and also holds out source `7`. Source `5` remains in train because it
is the only selected source with the lateral target.

## NPZ Contents

The materialized corpus contains:

| Key | Shape | Dtype |
| --- | --- | --- |
| `observation` | `(431, 72)` | `float32` |
| `normal_hidden` | `(431, 64)` | `float32` |
| `variant_hidden` | `(431, 64)` | `float32` |
| `target_action_sequence` | `(431, 9, 3)` | `float32` |
| `normal_base_action_sequence` | `(431, 9, 3)` | `float32` |
| `sequence_mask` | `(431, 9)` | `float32` |
| `variant_base_action` | `(431, 3)` | `float32` |
| `weight` | `(431,)` | `float32` |
| `row_id` | `(431,)` | `int64` |
| `source_index` | `(431,)` | `int64` |
| `sequence_length` | `(431,)` | `int64` |

The actor input contract is unchanged: source ids, split labels, target names,
and target metadata are corpus metadata only and are not actor observations.

## Interpretation

M641 passes the M640 infrastructure gate. The positive result is that the
sequence-target branch now has a source-balanced, materialized corpus rather
than raw uneven candidate counts.

This does not admit actor training by itself. Before any BC-v2 or actor update,
M642 should run exact objective sanity on the corpus: load the NPZ, compare
target sequences against base sequences, report source-balanced loss
contributions, and separate train from source-heldout validation rows.

## Decision

`source_diverse_sequence_target_corpus_pass_admit_exact_sanity`

## Next

`m642-sequence-corpus-exact-objective-sanity`
