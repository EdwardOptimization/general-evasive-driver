# M648 BC-v2 Head-Only Repeat Design

## Purpose

M648 designs a cleaner repeat of the M646 frozen-actor head-only smoke. The
repeat should preserve the positive learnability result while controlling the
validation overfit found in M647.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M647 Blocker

M646 passed, but final epoch was not the best validation point:

```text
best_validation_epoch: 120
best_validation_normal_delta_mse: 0.000490287
final_validation_normal_delta_mse: 0.001331890
final_vs_best_ratio: 2.716552
```

M646 also showed weak wrong-history source separation:

```text
source 30 gap_l2: 0.012069
source 32 gap_l2: 0.006822
source 32 variant loss < normal loss
```

So the next step must not be actor coupling. It should first make the head-only
result repeatable and save the best validation head.

## Repeat Protocol

M649 should run three frozen-head seeds:

```text
6460
6461
6462
```

Use the same corpus and checkpoint:

```text
corpus:     runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz
metadata:   runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

Training settings:

```text
epochs: 240
learning_rate: 0.001
weight_decay: 0.0001
hidden_dim: 64
log_interval: 15 or 30
device: cpu
```

The epoch cap is lower than M646's `300` because validation already worsened
after epoch `120`.

## Best-Validation Rule

For each seed, M649 must save:

```text
sequence_delta_head_final.pt
sequence_delta_head_best_validation.pt
```

The selected head for branch analysis is the best-validation head, not the
final head.

Best validation is selected by:

```text
minimum source_holdout_validation normal_delta_mse
```

M649 should still report final metrics so overfit is visible.

## Required Artifacts

M649 should write:

```text
summary.json
seed_summary.csv
seed_metrics.csv
source_repeat_summary.csv
target_repeat_summary.csv
wrong_history_source_summary.csv
seed_6460/sequence_delta_head_best_validation.pt
seed_6461/sequence_delta_head_best_validation.pt
seed_6462/sequence_delta_head_best_validation.pt
```

No actor checkpoint may be written.

## Pass Criteria

M649 passes as head-only repeat evidence if:

```text
all 3 actor checksums unchanged
all 3 write best-validation head checkpoints
all 3 write no actor checkpoint
at least 2/3 seeds:
  train_delta_mse_improvement_at_best >= 0.30
  validation_delta_mse_improvement_at_best >= 0.50
  best_validation_delta_mse <= 0.00075
  final_vs_best_validation_ratio <= 3.0
source-balanced weights preserved
wrong-history sources reported separately
```

The `0.00075` best-validation threshold is intentionally looser than M646's
best `0.000490287`; it checks repeatability without overfitting the next run to
one exact number.

## Failure Interpretation

| Result | Interpretation |
| --- | --- |
| 3/3 seeds pass | strong head-only learnability repeat; adapter design can be considered after audit |
| 2/3 seeds pass | acceptable but seed-sensitive; audit before adapter design |
| 0-1 seeds pass | M646 was seed-fragile; do not couple actor |
| actor checksum changes | contract violation |
| wrong-history sources remain weak | do not claim self-identification |

## Next After M649

Regardless of pass/fail, M650 should audit before any actor-coupling design.

If M649 passes strongly, M650 may admit an adapter design with exact retention
gates.

If M649 is seed-sensitive or wrong-history remains weak, M650 should design a
better wrong-history objective rather than actor coupling.

## Decision

`bc_v2_head_only_repeat_design_admit_m649`

## Next

`m649-bc-v2-head-only-repeat-implementation`
