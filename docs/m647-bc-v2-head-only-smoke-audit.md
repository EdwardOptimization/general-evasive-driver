# M647 BC-v2 Head-Only Smoke Audit

## Purpose

M647 audits M646 before any actor-coupling design. It checks whether the
head-only result is a clean enough proof of frozen-feature learnability and
whether validation behavior allows escalation.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M646 Summary

M646 passed its pre-registered head-only smoke gate:

```text
train_initial_delta_mse: 0.008720258250832558
train_final_delta_mse: 0.00023707130458205938
train_delta_mse_improvement: 0.9728137289329217

validation_initial_delta_mse: 0.008592789992690086
validation_final_delta_mse: 0.0013318904675543308
validation_delta_mse_improvement: 0.8449990668121327

actor_parameters_changed: false
head_checkpoint_written: true
actor_checkpoint_written: false
passed_head_only_smoke: true
```

The positive claim is valid:

```text
frozen BC5660 features contain enough signal for an auxiliary head to learn
the M641 source-balanced sequence-delta targets.
```

## Correction To M646 Note

The M646 implementation document described the best validation point as
"around epoch 180". The exact logged validation minimum is:

```text
best_validation_epoch: 120
best_validation_normal_delta_mse: 0.000490287085995
final_validation_normal_delta_mse: 0.0013318904675543
final_vs_best_ratio: 2.7165522111424383
```

Epoch `180` is still much better than the final epoch, but it is not the best
logged validation point. M647 treats epoch `120` as the correct best checkpoint
for audit purposes.

## Learning Curve

Validation curve:

| Epoch | Validation Normal MSE | Validation Variant MSE |
| ---: | ---: | ---: |
| 0 | 0.008592790 | 0.008597 |
| 30 | 0.000572 | 0.000568 |
| 60 | 0.000499 | 0.000489 |
| 90 | 0.000495 | 0.000483 |
| 120 | 0.000490 | 0.000478 |
| 150 | 0.000494 | 0.000488 |
| 180 | 0.000517 | 0.000536 |
| 210 | 0.000591 | 0.000690 |
| 240 | 0.000780 | 0.001092 |
| 270 | 0.001107 | 0.001795 |
| 300 | 0.001332 | 0.002309 |

Train loss keeps falling through epoch `300`, while validation bottoms near
epoch `120` and then regresses. This is classic head-level overfit. The final
head is still much better than initialization, but it is not the best available
head under the branch's own validation signal.

## Source Audit

Final source-level normal delta MSE:

| Source | Split | Target | Variant | Normal MSE | Variant MSE | Gap L2 |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 0 | train | braking | delayed | 0.000108 | 0.001011 | 0.051868 |
| 5 | train | lateral | delayed | 0.000270 | 0.000870 | 0.038912 |
| 7 | source-heldout | braking | delayed | 0.000916 | 0.002576 | 0.036950 |
| 8 | train | yaw | delayed | 0.000104 | 0.000412 | 0.036563 |
| 13 | train | yaw | delayed | 0.000335 | 0.000809 | 0.037179 |
| 14 | train | yaw | delayed | 0.000335 | 0.000809 | 0.037179 |
| 20 | source-heldout | yaw | delayed | 0.001540 | 0.003068 | 0.030242 |
| 30 | train | braking | wrong | 0.000270 | 0.000332 | 0.012069 |
| 32 | source-heldout | yaw | wrong | 0.001540 | 0.001283 | 0.006822 |

The source audit has two implications:

1. The head learns delayed-history correction targets well on several train and
   heldout sources.
2. Wrong-history source separation remains weak. Source `32` even has lower
   variant loss than normal loss at the final epoch, and source `30` has a
   small normal/variant prediction gap.

So M646 supports feature learnability, not self-identification proof.

## Decision

M647 classifies M646 as:

```text
pass_with_overfit_caveat
```

The result is strong enough to justify a cleaner head-only repeat with
early-stopping and multiple seeds. It is not strong enough to admit actor
coupling yet.

## Next Branch

M648 should design an early-stopped head-only repeat:

```text
multiple head seeds
save best validation head
shorter epoch budget or patience
same frozen actor
same source-balanced corpus
same no-promotion rule
```

Only after that repeat should the project decide whether to design an adapter
or actor-coupling update.

## Decision Label

`bc_v2_head_only_smoke_audit_pass_with_overfit_admit_repeat_design`

## Next

`m648-bc-v2-head-only-repeat-design`
