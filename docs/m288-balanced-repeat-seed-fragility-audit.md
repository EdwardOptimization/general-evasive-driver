# M288 Balanced-Repeat Seed-Fragility Audit

M288 audits why M286 produced a strong proof-safe balanced update while M287,
the fresh optimizer-seed repeat, only remained proof-safe at a tiny alpha.

No PPO, actor update, promotion, or actor-input change was performed.

## Inputs

M286 selected checkpoint:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
```

M287 selected checkpoint:

```text
runs/m287_balanced_rejected_trajectory_repeat/interpolation_refine/checkpoints/alpha_0_005.pt
```

Audit artifact:

```text
runs/m288_balanced_repeat_seed_fragility_audit/fragile_row_action_margin_audit.csv
runs/m288_balanced_repeat_seed_fragility_audit/summary.json
```

## Safe Alpha Collapse

The same repeat2 recipe has very different proof-safe interpolation ranges
across optimizer seeds:

| Milestone | Raw seed | Best public-gate-safe alpha | Exact M270 delta |
| --- | ---: | ---: | ---: |
| M286 | 10079 | 0.500 | -0.002547383 |
| M287 | 10080 | 0.005 | -0.000026822 |

The collapse ratio is:

```text
0.005 / 0.5 = 0.01
```

That is seed fragility, not a clean repeat.

## Failed Rows

M286 raw repeat2 fails only one M183/M170 row:

| Row | Target | Normal margin | Wrong-history margin |
| ---: | --- | ---: | ---: |
| 10 | future_braking_deceleration | -0.000204235 | -0.006872328 |

M287 raw fails four M183/M170 rows:

| Row | Target | Normal margin | Wrong-history margin |
| ---: | --- | ---: | ---: |
| 5 | future_braking_deceleration | -0.000092192 | -0.010207278 |
| 9 | future_lateral_accel_response | -0.000092192 | -0.007514443 |
| 10 | future_braking_deceleration | -0.000449074 | -0.007128911 |
| 16 | future_braking_deceleration | -0.000094650 | -0.006178539 |

At refined alpha, M287 first fails at `alpha=0.01`, and the failing row is
row16:

```text
row_id = 16
physical_pair_key = 9530:6:9550:6
base normal margin = 0.000000636
m287 alpha 0.005 normal margin = 0.000000158
m287 alpha 0.010 normal margin = -0.000000373
```

## Action And Margin Drift

The watch rows are rows 5, 9, 10, and 16. They are all M183/M170 old-surface
normal-success rows.

Row16 is the limiting row:

| Policy | Normal success | Normal margin | First-action L2 vs base |
| --- | --- | ---: | ---: |
| M272 base | true | 0.000000636 | 0 |
| M286 alpha 0.5 | true | 0.000085290 | 0.003234 |
| M286 raw repeat2 | true | 0.000173349 | 0.006476 |
| M287 alpha 0.005 | true | 0.000000158 | 0.000034 |
| M287 alpha 0.010 | false | -0.000000373 | 0.000068 |
| M287 raw | false | -0.000094650 | 0.006856 |

This shows why M287 can fail with very small action movement: row16 is a
terminal-margin cliff with essentially no positive slack under the base. M286
happened to move this row in a helpful direction; M287 moved it in the harmful
direction.

Row10 is also fragile but less limiting for the refined M287 search:

| Policy | Normal success | Normal margin | First-action L2 vs base |
| --- | --- | ---: | ---: |
| M272 base | true | 0.000416157 | 0 |
| M286 alpha 0.5 | true | 0.000104521 | 0.003912 |
| M286 raw repeat2 | false | -0.000204235 | 0.007795 |
| M287 alpha 0.005 | true | 0.000411835 | 0.000042 |
| M287 raw | false | -0.000449074 | 0.008392 |

## Interpretation

M287 does not lose the current-family M267/M264 direction. M267/M264 passes for
raw repeat2 and for every tested interpolation in both M286 and M287.

The unstable part is old-surface normal-success retention, especially row16.
Row16 has only `6.36e-7` base normal-margin slack. A useful update direction can
help it, as M286 did, but another optimizer seed can push it across the
terminal-margin cliff almost immediately.

So the next repair should not be PPO and should not be a longer actor update.
It should explicitly protect row16 and nearby old-surface terminal-margin rows
inside the update recipe.

## Decision

M288 completes the seed-fragility audit.

Decision:

```text
repair_with_row16_aware_balanced_repeat
```

Recommended next step:

```text
m289-row16-aware-balanced-repeat-calibration
```

M289 should use a smaller or row16-aware update recipe before any PPO:

```text
candidate repair knobs:
- lower learning rate or fewer update steps;
- stronger row16/current-hidden recovery anchor pressure;
- per-source trust-region gate on old M183/M170 rows;
- hard reject if row16 terminal margin does not improve or stay positive.
```

PPO remains blocked.
