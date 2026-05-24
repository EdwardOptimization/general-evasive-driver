# M658 Wrong-History Fusion-Boundary Probe Implementation

## Purpose

M658 implements and runs the frozen feature-view comparison probe designed in
M657.

This milestone trains diagnostic auxiliary heads only:

```text
BC5660 actor/recurrent/critic/log_std frozen
no actor update
no PPO
no actor checkpoint
no promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_fusion_boundary_probe \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --seeds 6570,6571,6572 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --contrast-coef 1.0 \
  --wrong-zero-coef 0.05 \
  --margin-mse 0.00025 \
  --views fused,next_hidden,fused_plus_next_hidden \
  --device cpu \
  --run-dir runs/m658_wrong_history_fusion_boundary_probe
```

## Artifacts

```text
runs/m658_wrong_history_fusion_boundary_probe/summary.json
runs/m658_wrong_history_fusion_boundary_probe/seed_view_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/view_metrics.csv
runs/m658_wrong_history_fusion_boundary_probe/view_row_contrast_metrics.csv
runs/m658_wrong_history_fusion_boundary_probe/view_source_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/view_target_summary.csv
runs/m658_wrong_history_fusion_boundary_probe/view_history_variant_summary.csv
```

Diagnostic head checkpoints were written under:

```text
runs/m658_wrong_history_fusion_boundary_probe/seed_*/view_*/
```

These are auxiliary head checkpoints only. No actor checkpoint was written.

## Contract Checks

```text
actor_parameters_changed: false
actor_checkpoint_written: false
actor_training_started: false
ppo_used: false
promoted: false
diagnostic_head_checkpoints_written: true
```

Model checksum was unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Overall Result

M658 did not pass the diagnostic gate:

```text
diagnostic_passed: false
passed_views: []
fused_weak_seed_count: 3
```

The fused baseline remained weak for all seeds, which matches the M652/M655
diagnosis. `next_hidden` improved wrong-history prediction L2 relative to the
same-seed fused baseline, but not enough to pass the absolute wrong-history
thresholds or make gap MSE reliably positive.

## Seed/View Summary

| Seed | View | Normal Val MSE | Wrong Val Gap MSE | Wrong Val Gap L2 | Gap L2 / Fused |
| ---: | --- | ---: | ---: | ---: | ---: |
| 6570 | fused | 0.000464 | -0.000001 | 0.000516 | 1.000 |
| 6571 | fused | 0.000494 | -0.000000 | 0.000467 | 1.000 |
| 6572 | fused | 0.000501 | -0.000000 | 0.000431 | 1.000 |
| 6570 | next_hidden | 0.000483 | -0.000003 | 0.001613 | 3.126 |
| 6571 | next_hidden | 0.000474 | 0.000001 | 0.001659 | 3.549 |
| 6572 | next_hidden | 0.000517 | -0.000008 | 0.001923 | 4.466 |
| 6570 | fused_plus_next_hidden | 0.000481 | -0.000002 | 0.001622 | 3.143 |
| 6571 | fused_plus_next_hidden | 0.000501 | -0.000003 | 0.001512 | 3.237 |
| 6572 | fused_plus_next_hidden | 0.000466 | -0.000004 | 0.000986 | 2.290 |

Mean by view:

| View | Normal Val MSE | Wrong Val Gap MSE | Wrong Val Gap L2 | Gap L2 / Fused |
| --- | ---: | ---: | ---: | ---: |
| fused | 0.000486 | -0.0000005 | 0.000471 | 1.000 |
| next_hidden | 0.000491 | -0.0000030 | 0.001732 | 3.714 |
| fused_plus_next_hidden | 0.000483 | -0.0000027 | 0.001374 | 2.890 |

## Interpretation

What worked:

```text
normal validation retention stayed good for all views;
next_hidden increased wrong-history prediction L2 by 3.1x to 4.5x over fused;
actor checksum stayed unchanged;
the same-run fused baseline reproduced the weak separation pattern.
```

What failed:

```text
no pre-fusion or concat view reached wrong_validation_prediction_gap_l2 >= 0.005;
wrong_validation_gap_mse did not become reliably positive;
source-heldout source 32 remained weak;
fused_plus_next_hidden did not dominate next_hidden.
```

This weakens the simple hypothesis that the blocker is only the
response/context fusion boundary. The pre-fusion belief state carries more
wrong-history signal than fused features, but the current corpus/objective still
does not turn that signal into a strong rejected-history branch.

## Process Decision

Do not:

- couple this auxiliary head into the actor;
- run PPO;
- increase fused-only contrast coefficients;
- promote any checkpoint;
- claim closed-loop self-ID proof.

The next audit should decide whether to pivot to:

```text
stronger action-divergent wrong-history corpus mining
an objective with explicit rejected-history target actions
a different preference formulation
```

## Decision

`wrong_history_fusion_boundary_probe_negative_admit_audit`

## Next

`m659-wrong-history-fusion-boundary-probe-audit`
