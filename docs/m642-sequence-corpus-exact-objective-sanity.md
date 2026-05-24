# M642 Sequence Corpus Exact Objective Sanity

## Purpose

M642 checks whether the M641 source-balanced sequence target corpus is usable
as an exact objective before any actor update. It only loads the metadata and
NPZ corpus, computes target/base sequence deltas, and reports source-balanced
and split-specific summaries.

No training, PPO, checkpoint interpolation, actor update, or promotion occurs.

## Command

```bash
PYTHONPATH=src python -m autodrift.sequence_corpus_exact_objective_sanity \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --run-dir runs/m642_sequence_corpus_exact_objective_sanity
```

## Artifacts

- `runs/m642_sequence_corpus_exact_objective_sanity/summary.json`
- `runs/m642_sequence_corpus_exact_objective_sanity/row_objective_metrics.csv`
- `runs/m642_sequence_corpus_exact_objective_sanity/source_objective_summary.csv`
- `runs/m642_sequence_corpus_exact_objective_sanity/split_objective_summary.csv`
- `runs/m642_sequence_corpus_exact_objective_sanity/target_objective_summary.csv`

## Result

```text
rows: 431
source_count: 9
observation_dim: 72
hidden_dim: 64
max_sequence_length: 9
nonzero_delta_rows: 431
all_rows_have_nonzero_target_delta: true
weighted_sequence_mse_mean: 0.00203998548446608
weighted_mean_step_l2: 0.0773480846102788
max_sequence_step_l2: 0.09999999403953552
outside_mask_abs_max: 0.0
finite_metrics: true
training_started: false
actor_parameters_changed: false
ppo_used: false
promoted: false
```

Source weight balance:

```text
expected_source_weight: 0.1111111111111111
min_source_weight: 0.11111111054196954
max_source_weight: 0.1111111119389534
max_abs_source_weight_error: 0.0000000008278422947149977
total_weight: 1.0000000060535967
source_weight_balanced: true
```

Split summary:

| Split | Rows | Sources | Weight Sum | Weighted MSE | Weighted Mean Step L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `train` | 271 | 6 | 0.6666666702367365 | 0.002054882368650409 | 0.07785627557365113 |
| `source_holdout_validation` | 160 | 3 | 0.3333333358168602 | 0.0020101917161598555 | 0.07633170268566396 |

Target summary:

| Target | Rows | Sources | Weight Sum | Weighted MSE | Weighted Mean Step L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `future_braking_deceleration` | 95 | 3 | 0.33333333441987634 | 0.0021187091297119477 | 0.07941706263657551 |
| `future_lateral_accel_response` | 48 | 1 | 0.1111111119389534 | 0.0021134772250603687 | 0.0791535838965017 |
| `future_yaw_response` | 288 | 5 | 0.555555559694767 | 0.0019780529493976587 | 0.07574559794245882 |

## Interpretation

M642 passes the exact sanity gate. The corpus is not a CSV-only artifact: the
materialized NPZ loads, row counts and weights align with metadata, all rows
have nonzero target/base sequence deltas, and padding outside the recorded mask
is zero.

The train and source-heldout splits have similar weighted objective scale, so
M641 does not appear to create an immediate split-scale artifact. Source-level
weights are balanced even though raw row counts differ by source.

The next step can be a design milestone for a source-balanced BC-v2 objective.
That design must keep the actor contract unchanged and should define exact
objective gates before allowing any actor update.

## Decision

`sequence_corpus_exact_sanity_pass_admit_bc_v2_design`

## Next

`m643-source-balanced-bc-v2-objective-design`
