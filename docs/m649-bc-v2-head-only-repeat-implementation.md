# M649 BC-v2 Head-Only Repeat Implementation

## Purpose

M649 implements the early-stopped multi-seed frozen-head repeat designed in
M648. It runs three auxiliary sequence-delta head seeds, saves both final and
best-validation head checkpoints, and keeps the BC5660 actor frozen.

This milestone does not update the actor, run PPO, write an actor checkpoint,
or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_v2_head_only_repeat \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --seeds 6460,6461,6462 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --device cpu \
  --run-dir runs/m649_bc_v2_head_only_repeat
```

## Artifacts

- `runs/m649_bc_v2_head_only_repeat/summary.json`
- `runs/m649_bc_v2_head_only_repeat/seed_summary.csv`
- `runs/m649_bc_v2_head_only_repeat/seed_metrics.csv`
- `runs/m649_bc_v2_head_only_repeat/source_repeat_summary.csv`
- `runs/m649_bc_v2_head_only_repeat/target_repeat_summary.csv`
- `runs/m649_bc_v2_head_only_repeat/wrong_history_source_summary.csv`
- `runs/m649_bc_v2_head_only_repeat/seed_6460/sequence_delta_head_best_validation.pt`
- `runs/m649_bc_v2_head_only_repeat/seed_6461/sequence_delta_head_best_validation.pt`
- `runs/m649_bc_v2_head_only_repeat/seed_6462/sequence_delta_head_best_validation.pt`

No actor checkpoint is written.

## Result

```text
seeds: [6460, 6461, 6462]
passed_seed_count: 3
total_seed_count: 3
repeat_passed: true
all_actor_checksums_unchanged: true
all_best_heads_written: true
all_final_heads_written: true
actor_checkpoint_written: false
actor_parameters_changed: false
wrong_history_rows: 6
```

The actor checksum is unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Seed Summary

| Seed | Best Epoch | Best Train MSE | Best Validation MSE | Train Improvement | Validation Improvement | Final / Best Val | Passed |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 6460 | 52 | 0.000519 | 0.000486 | 0.940496 | 0.943446 | 1.604452 | true |
| 6461 | 39 | 0.000545 | 0.000458 | 0.955269 | 0.961764 | 1.193386 | true |
| 6462 | 47 | 0.000518 | 0.000502 | 0.924923 | 0.930663 | 2.276952 | true |

All three seeds satisfy the M648 pass thresholds:

```text
train improvement >= 0.30
validation improvement >= 0.50
best validation MSE <= 0.00075
final-vs-best validation ratio <= 3.0
```

## Wrong-History Source Summary

| Seed | Source | Target | Normal MSE | Variant MSE | Prediction Gap L2 |
| ---: | ---: | --- | ---: | ---: | ---: |
| 6460 | 30 | braking | 0.000330 | 0.000330 | 0.000648 |
| 6460 | 32 | yaw | 0.000441 | 0.000440 | 0.000596 |
| 6461 | 30 | braking | 0.000319 | 0.000317 | 0.000704 |
| 6461 | 32 | yaw | 0.000429 | 0.000430 | 0.000598 |
| 6462 | 30 | braking | 0.000328 | 0.000330 | 0.000651 |
| 6462 | 32 | yaw | 0.000462 | 0.000461 | 0.000526 |

## Interpretation

M649 strongly repeats the head-only learnability result. Best-validation
selection controls the final-epoch overfit seen in M646, and all three seeds
pass under the frozen-actor/no-promotion constraints.

However, the wrong-history diagnostic is negative for self-ID separation. The
best-validation heads predict almost the same sequence deltas for normal and
wrong-history features on sources `30` and `32`. This means the auxiliary head
has learned a useful local correction map from frozen features, but it has not
shown causal dependence on wrong-history recurrent state.

Therefore M649 should be audited before any adapter or actor-coupling design.
The likely next branch is not "couple this head into the actor directly"; it is
to add a wrong-history contrast or preference term to the head objective.

## Decision

`bc_v2_head_only_repeat_pass_admit_audit`

## Next

`m650-bc-v2-head-only-repeat-audit`
