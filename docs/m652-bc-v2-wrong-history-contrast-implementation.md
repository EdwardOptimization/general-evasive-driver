# M652 BC-v2 Wrong-History Contrast Implementation

## Purpose

M652 implements and runs the frozen-head wrong-history contrast smoke designed
in M651. It adds a wrong-history rejection margin and weak zero-delta anchor to
the head-only sequence-delta objective.

This milestone does not update the actor, run PPO, write an actor checkpoint,
or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_v2_wrong_history_contrast \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --seeds 6510,6511,6512 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --contrast-coef 1.0 \
  --wrong-zero-coef 0.05 \
  --margin-mse 0.00025 \
  --device cpu \
  --run-dir runs/m652_bc_v2_wrong_history_contrast
```

## Artifacts

- `runs/m652_bc_v2_wrong_history_contrast/summary.json`
- `runs/m652_bc_v2_wrong_history_contrast/seed_summary.csv`
- `runs/m652_bc_v2_wrong_history_contrast/seed_metrics.csv`
- `runs/m652_bc_v2_wrong_history_contrast/source_contrast_summary.csv`
- `runs/m652_bc_v2_wrong_history_contrast/target_contrast_summary.csv`
- `runs/m652_bc_v2_wrong_history_contrast/history_variant_summary.csv`
- per-seed best/final head checkpoints

No actor checkpoint is written.

## Result

```text
passed_seed_count: 0
total_seed_count: 3
contrast_passed: false
actor_parameters_changed: false
actor_checkpoint_written: false
all_best_heads_written: true
all_final_heads_written: true
```

Normal target retention is good:

| Seed | Normal Validation MSE | Normal Validation Improvement |
| ---: | ---: | ---: |
| 6510 | 0.000491 | 0.951448 |
| 6511 | 0.000508 | 0.936120 |
| 6512 | 0.000509 | 0.948946 |

Wrong-history gap fails by a wide margin:

| Seed | Wrong Train Gap MSE | Wrong Val Gap MSE | Wrong Train Gap L2 | Wrong Val Gap L2 |
| ---: | ---: | ---: | ---: | ---: |
| 6510 | 0.000004 | -0.000003 | 0.000940 | 0.000748 |
| 6511 | 0.000003 | -0.000002 | 0.000700 | 0.000624 |
| 6512 | 0.000005 | -0.000003 | 0.000774 | 0.000729 |

Pre-registered contrast thresholds were:

```text
wrong_train_gap_mse >= 0.00025
wrong_validation_gap_mse >= 0.00010
wrong_train_prediction_gap_l2 >= 0.01
wrong_validation_prediction_gap_l2 >= 0.005
```

No seed is close to the gap thresholds.

## Interpretation

M652 is a clean negative result.

The contrast objective preserves normal sequence-delta learning, but it does
not create meaningful wrong-history separation. The head still predicts nearly
the same correction for normal and wrong recurrent histories on sources `30`
and `32`.

This suggests the current frozen BC5660 feature representation may not contain
enough wrong-history separability for a small head to exploit. The next step
should audit feature separability and objective gradients before increasing
contrast coefficients or coupling anything into the actor.

## Decision

`bc_v2_wrong_history_contrast_negative_admit_feature_separability_audit`

## Next

`m653-bc-v2-wrong-history-contrast-audit`
