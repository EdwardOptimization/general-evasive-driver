# M646 BC-v2 Head-Only Smoke Implementation

## Purpose

M646 implements and runs the frozen-actor BC-v2 sequence-delta head-only smoke
designed in M645. It trains only an auxiliary `SequenceDeltaHead` on frozen
BC5660 recurrent features.

This milestone does not update the actor, run PPO, write an actor checkpoint,
or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_v2_head_only_smoke \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --epochs 300 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --seed 6460 \
  --device cpu \
  --run-dir runs/m646_bc_v2_head_only_smoke
```

## Artifacts

- `runs/m646_bc_v2_head_only_smoke/summary.json`
- `runs/m646_bc_v2_head_only_smoke/train_metrics.csv`
- `runs/m646_bc_v2_head_only_smoke/validation_metrics.csv`
- `runs/m646_bc_v2_head_only_smoke/row_predictions.csv`
- `runs/m646_bc_v2_head_only_smoke/source_head_summary.csv`
- `runs/m646_bc_v2_head_only_smoke/split_head_summary.csv`
- `runs/m646_bc_v2_head_only_smoke/target_head_summary.csv`
- `runs/m646_bc_v2_head_only_smoke/sequence_delta_head.pt`

No actor checkpoint is written.

## Result

```text
rows: 431
source_count: 9
epochs: 300
learning_rate: 0.001
weight_decay: 0.0001
hidden_dim: 64
seed: 6460

train_initial_delta_mse: 0.008720258250832558
train_final_delta_mse: 0.00023707130458205938
train_delta_mse_improvement: 0.9728137289329217

validation_initial_delta_mse: 0.008592789992690086
validation_final_delta_mse: 0.0013318904675543308
validation_delta_mse_improvement: 0.8449990668121327

normal_head_loss: 0.0006020110144433431
variant_head_loss: 0.0012412189240037432
normal_variant_prediction_gap_l2: 0.03197595750542504

actor_parameters_changed: false
head_checkpoint_written: true
actor_checkpoint_written: false
checkpoint_written: false
passed_head_only_smoke: true
```

The actor checksum is unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

Source weights remain balanced:

```text
source_count: 9
max_abs_source_weight_error: 0.0000000008278422947149977
total_weight: 1.0000000060535967
source_weight_balanced: true
```

## Split Summary

| Split | Rows | Sources | Normal Delta MSE | Variant Delta MSE | Prediction Gap L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `train` | 271 | 6 | 0.00023707131958574623 | 0.0007073434813747215 | 0.035628348361701 |
| `source_holdout_validation` | 160 | 3 | 0.001331890402629092 | 0.0023089698070243407 | 0.024671175808180124 |

## Target Summary

| Target | Rows | Sources | Normal Delta MSE | Variant Delta MSE | Prediction Gap L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `future_braking_deceleration` | 95 | 3 | 0.00043129155361493584 | 0.0013064996736079134 | 0.03362904137487133 |
| `future_lateral_accel_response` | 48 | 1 | 0.00027028166844953957 | 0.0008701454558763077 | 0.03891186214362582 |
| `future_yaw_response` | 288 | 5 | 0.0007707885597098619 | 0.0012762651680308813 | 0.029596926260273906 |

## Training Curve Note

M646 passes the pre-registered head-only smoke gate, but the validation curve is
not monotonic. The exact logged validation minimum is epoch `120`
(`0.000490287`) and the value then rises to the final `0.001331890`. The final
value is still much better than the initial `0.008592790`, but this curve should
be audited before designing any actor-coupling update.

## Interpretation

The positive result is clear but limited:

```text
frozen BC5660 recurrent features contain enough signal for a small auxiliary
head to predict the M641 local sequence-delta corrections.
```

This is not yet evidence that the deployed actor uses that signal, and it is
not a closed-loop driving improvement. It only validates the feature/target
learnability layer needed before an adapter or actor-coupling design.

The validation overfit after epoch 180 means the next milestone should be an
audit, not immediate actor coupling.

## Decision

`bc_v2_head_only_smoke_pass_admit_audit`

## Next

`m647-bc-v2-head-only-smoke-audit`
