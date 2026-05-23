# M295 Current-Family PPO Repair Audit

M295 audits why the stronger M294 current-family rejected-history PPO repair
partially improves M267/M264 retention but still cannot be promoted. No PPO was
run, and actor inputs are unchanged.

## Inputs

Base checkpoint:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Audited raw PPO checkpoints:

```text
runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt
runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt
```

Audit artifacts:

```text
runs/m295_current_family_ppo_repair_audit/summary.json
runs/m295_current_family_ppo_repair_audit/failed_row_comparison.csv
```

## What Changed From M291 To M294

M291 raw PPO preserved M183/M170 but lost four M267/M264 current-family
wrong-history success drops. M294 added stronger rejected-history trajectory
anchoring from M293 and doubled the outcome intervention coefficient.

| Candidate | Exact M270 loss | Delta vs M290 | M183/M170 drops | M267/M264 drops | Failed M267/M264 rows |
| --- | ---: | ---: | ---: | ---: | --- |
| m290x64_a500 | 0.679278374 | 0.000000000 | 17 | 17 | none |
| m291raw | 0.679781079 | +0.000502706 | 17 | 13 | 6, 11, 15, 16 |
| m294raw | 0.679893672 | +0.000615299 | 17 | 14 | 6, 15, 16 |

M294 recovered row 11, but still failed rows 6, 15, and 16.

## Failed-Row Margins

The repair pressure does move the targeted rows in the right direction. M294
reduces wrong-history margins for all four rows that M291 lost.

| Row | Base wrong margin | M291 raw wrong margin | M294 raw wrong margin | M294 result |
| ---: | ---: | ---: | ---: | --- |
| 6 | -0.000093342 | +0.000635215 | +0.000451956 | obstacle_completed |
| 11 | -0.000499612 | +0.000057243 | -0.000083675 | collision |
| 15 | -0.000340077 | +0.000579999 | +0.000397208 | obstacle_completed |
| 16 | -0.000626075 | +0.000187822 | +0.000003145 | obstacle_completed |

Row 11 is the useful signal: stronger rejected-history trajectory anchoring can
recover a current-family row. Rows 6, 15, and 16 are the blocker: the same
mechanism shrinks the wrong-history margins but does not restore the required
success drops.

## Objective Regression

M294 is worse than M291 on exact M270:

```text
M291 raw delta vs M290: +0.000502706
M294 raw delta vs M290: +0.000615299
M294 minus M291:        +0.000112593
```

M294 also failed the exact M270 interpolation gate: every nonzero alpha from
the M290 base toward M294 raw increased exact M270 loss. Because of that, M294
correctly did not run broader replay/protected-key/behavior gates.

## Interpretation

M294 confirms that generic action-anchor pressure is a blunt control variable.
It can pull a local rejected-history row back toward collision, but it does not
directly encode the invariant that wrong-history rollouts on the current-family
surface should remain rejected while correct-history rollouts stay successful.

This is still the same failure class as M291:

```text
proof_washout
objective_overfit
```

The difference is that M294 shows the failed-row anchor has some signal, but
not enough specificity. Continuing to increase trajectory-anchor pressure would
risk more exact-M270 objective regression while only locally moving margins.

## Repair Direction

The next repair should stop treating the issue as only an action-matching
problem. The next milestone should design a direct current-family
rejected-history margin or pairwise preference objective:

```text
correct-history rollout should remain successful
wrong-history rollout should remain rejected
margin(correct) - margin(wrong) should stay above a pre-registered floor
exact M270 should not regress before any PPO promotion gates
```

The objective should be designed and validated before another PPO run.

## Decision

M294 remains rejected, and M290 remains the public-gate base.

Decision:

```text
design_direct_current_family_rejected_history_margin_preference_objective
```

Next step:

```text
m296-current-family-rejected-margin-objective-design
```
