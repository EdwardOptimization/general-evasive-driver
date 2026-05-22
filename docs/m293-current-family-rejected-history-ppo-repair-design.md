# M293 Current-Family Rejected-History PPO Repair Design

M293 designs the next PPO smoke after M292 showed that raw M291 PPO made four
M267/M264 rejected-history rows safe. No PPO or actor-input change was
performed.

## Problem

M291 raw PPO failed because it raised wrong-history margins on M267/M264 rows
6, 11, 15, and 16:

```text
M267/M264 success drops: 17 -> 13
exact M270 delta: +0.000502706
```

The safe interpolation `m291_a100` retained gates, but still worsened exact
M270 by `+0.0000500679`, so it stayed diagnostic.

## Repair Strategy

The next PPO smoke should not only anchor baseline actions. It must explicitly
protect current-family rejected-history trajectories and reject exact M270
regression before replay promotion.

M293 therefore creates a targeted trajectory anchor:

```text
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

The anchor starts from the M289 row16-aware anchor and appends four extra
copies of rejected-history trajectory rows for M267/M264 failed rows:

```text
failed rows = [6, 11, 15, 16]
extra rows per repeat = 152
extra repeats = 4
base rows = 3292
output rows = 3900
weight max = 100.0
weight mean = 27.288900
```

This keeps old row16 protection while increasing pressure on the exact rows
that raw PPO made safe.

## M294 Config

M293 also defines the next executable smoke config:

```text
configs/ppo_m294_current_family_rejected_repair_smoke.json
```

Main changes versus M291:

| Setting | M291 | M294 |
| --- | ---: | ---: |
| outcome_intervention_aux_coef | 0.03 | 0.06 |
| snippet_action_anchor_batch_size | 128 | 256 |
| trajectory_action_anchor_coef | 100.0 | 150.0 |
| trajectory anchor | M289 row16 extra64 | M293 failed-row extra4 |
| PPO total steps | 1024 | 1024 |

M294 remains smoke-scale. It is a repair probe, not a long continuation.

## Required Gates

M294 should evaluate in this order:

```text
1. Exact M270 no-regression versus m290x64_a500.
2. M183/M170 first replay gate.
3. M267/M264 first replay gate.
4. Interpolation only if raw PPO fails but the direction is useful.
5. Full replay stack, protected key, and behavior seeds only after first gates pass.
```

Promotion must be blocked if:

```text
exact M270 gets worse
M267/M264 success drops fall below 17
M183/M170 row16 is lost
protected key fails
behavior seeds regress
safe alpha collapses near zero
```

## Decision

Admit M294 as the next executable smoke. Do not run medium or long PPO.

Decision:

```text
admit_m294_current_family_rejected_repair_smoke
```
