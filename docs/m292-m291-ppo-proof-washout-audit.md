# M292 M291 PPO Proof-Washout Audit

M292 audits why the M291 raw PPO smoke failed M267/M264 while preserving
M183/M170. No PPO or actor-input change was performed.

## Inputs

Base:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Raw M291 PPO:

```text
runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt
```

Safe diagnostic interpolation:

```text
runs/m291_row16_aware_guarded_ppo_smoke/interpolation/checkpoints/alpha_0_1.pt
```

Audit artifact:

```text
runs/m292_m291_ppo_proof_washout_audit/failed_m267_m264_rows.csv
```

## Failure Rows

Raw M291 loses four M267/M264 success drops:

```text
rows = [6, 11, 15, 16]
```

These rows are all current-family rejected-history rows whose wrong-history
margins are only slightly negative in the M290 base. Raw PPO pushes them across
zero into successful wrong-history rollouts.

| Row | Base wrong margin | m291_a100 wrong margin | Raw wrong margin | Raw wrong result |
| ---: | ---: | ---: | ---: | --- |
| 6 | -0.000093342 | -0.000021021 | +0.000635215 | obstacle_completed |
| 11 | -0.000499612 | -0.000444075 | +0.000057243 | obstacle_completed |
| 15 | -0.000340077 | -0.000248764 | +0.000579999 | obstacle_completed |
| 16 | -0.000626075 | -0.000545410 | +0.000187822 | obstacle_completed |

The safe `m291_a100` interpolation keeps all four wrong-history margins
negative, but it also worsens exact M270 by `+0.0000500679`, so it remains a
diagnostic checkpoint rather than a promoted base.

## Aggregate Deltas

Across all 17 M267/M264 rows, raw PPO raises both normal and wrong-history
margins:

| Policy | Normal margin delta mean | Wrong-history margin delta mean | Margin-gap delta mean |
| --- | ---: | ---: | ---: |
| m291_a100 | +0.000089176 | +0.000072440 | +0.000016736 |
| m291raw | +0.000900709 | +0.000729773 | +0.000170937 |

The gate fails because raw PPO makes wrong-history rollouts safer, not because
normal rollouts become unsafe.

First-action deltas are small but directionally consistent. Raw PPO makes both
normal and wrong-history first actions slightly more lift/off-throttle and
slightly lower brake:

| Policy | Normal throttle delta mean | Normal brake delta mean | Wrong throttle delta mean | Wrong brake delta mean |
| --- | ---: | ---: | ---: | ---: |
| m291_a100 | -0.000319828 | -0.000107034 | -0.000245602 | -0.000071080 |
| m291raw | -0.003238155 | -0.001087414 | -0.002492757 | -0.000729552 |

That is enough to move the near-boundary wrong-history rows from collision to
obstacle completion.

## Interpretation

M291 is not an old-row16 failure. It is a current-family rejected-history
washout:

```text
raw PPO raises normal margins
raw PPO also raises wrong-history margins
four wrong-history rows cross from small negative margins to positive margins
M267/M264 success drops fall from 17 to 13
```

The current M291 PPO guard anchors actions and includes the M270 objective, but
it does not penalize PPO for making rejected-history trajectories safe. The
PPO reward can therefore improve generic clearance/recoverability while erasing
the proof that the policy behavior depends on the correct history.

## Repair Direction

The next PPO attempt should not simply lower learning rate. It needs an
explicit current-family rejected-history protection term.

Recommended repair:

```text
1. Add or strengthen a rejected-history trajectory anchor for M267/M264 rows.
2. Add an exact M270 no-regression check before any replay promotion.
3. Keep M183/M170 row16 and M267/M264 as first gates.
4. Run only a smoke-scale PPO after the repair design is documented.
```

This should be designed in M293 before another PPO run.

## Decision

Classify M291 as:

```text
proof_washout
objective_overfit
```

Decision:

```text
repair_current_family_rejected_history_ppo
```

Next step:

```text
m293-current-family-rejected-history-ppo-repair-design
```
