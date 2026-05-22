# M290 Row16-Aware Balanced Repeat Fresh Seed

M290 repeats the M289 row16-aware extra64 no-PPO actor-coupling recipe on a
fresh optimizer/data seed before admitting any PPO continuation.

No PPO or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

M289 promoted checkpoint:

```text
runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
```

Fresh repeat update:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/update_row16_extra64_s10_lr5e5_seed10081/optimized_checkpoint.pt
```

The update reused the M289 row16-aware extra64 trajectory anchor:

```text
runs/m289_row16_aware_balanced_repeat_calibration/anchors/row16_extra64_combined_anchor.npz
```

## Raw Fresh Update

The raw fresh-seed update improves exact M270 and preserves M183/M170, but it
loses three M267/M264 wrong-history success drops. Raw is therefore rejected.

| Candidate | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | --- | ---: | --- | ---: |
| M272 base | 0.681375623 | true | 17 | true | 17 |
| M290 raw | 0.677158952 | true | 17 | false | 14 |

## Interpolation

M290 interpolated from M272 toward the raw fresh update.

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| ---: | ---: | --- | ---: | --- | ---: |
| 0.000 | 0.681375623 | true | 17 | true | 17 |
| 0.050 | 0.681166887 | true | 17 | true | 17 |
| 0.100 | 0.680957913 | true | 17 | true | 17 |
| 0.200 | 0.680539370 | true | 17 | true | 17 |
| 0.300 | 0.680119872 | true | 17 | true | 17 |
| 0.400 | 0.679699600 | true | 17 | true | 17 |
| 0.500 | 0.679278374 | true | 17 | true | 17 |
| 0.600 | 0.678856254 | true | 17 | false | 16 |
| 0.700 | 0.678433180 | true | 17 | false | 16 |
| 0.800 | 0.678009331 | true | 17 | false | 15 |
| 1.000 | 0.677158952 | true | 17 | false | 14 |

Selected candidate:

```text
policy = m290x64_a500
checkpoint = runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Objective improvement:

```text
0.6813756227493286 -> 0.6792783737182617
delta = -0.0020972490310668945
```

This is a material repeat. It is smaller than M289 but far larger than the M287
near-zero repeat:

```text
M287 delta = -0.00002682209014892578
M289 delta = -0.0027780532836914062
M290 delta = -0.0020972490310668945
```

## Full Public Gates

The selected `m290x64_a500` candidate passes the full public replay stack.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | +0.000811527 | +0.000202672 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | +0.000823844 | +0.000197880 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | +0.000784932 | +0.000154651 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | +0.000761019 | +0.000152810 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | +0.000761096 | +0.000152822 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | +0.000761183 | +0.000152819 | true |

The old protected-key diagnostic passes and remains discriminative:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m272_base | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m290x64_a500 | 0.8625 | 0.1375 | 1.836100 |
| 9505 | m290x64_a500_reset | 0.8500 | 0.1500 | 1.834572 |
| 9505 | m290x64_a500_zero_all | 0.8000 | 0.2000 | 1.853573 |
| 9506 | m272_base | 0.8625 | 0.1375 | 1.852854 |
| 9506 | m290x64_a500 | 0.8625 | 0.1375 | 1.853644 |
| 9506 | m290x64_a500_reset | 0.8500 | 0.1500 | 1.850860 |
| 9506 | m290x64_a500_zero_all | 0.8000 | 0.2000 | 1.871504 |

## Interpretation

M290 confirms that the row16-aware recipe is repeatable enough to leave the
actor-update-only repair loop. The fresh seed did not collapse back to a
near-zero safe alpha. It does still show the same tradeoff: raw update pressure
protects old row16 but weakens M267/M264 wrong-history retention, so the safe
checkpoint is still an interpolation candidate rather than raw update.

## Decision

Promote `m290x64_a500` as the current public-gate base and admit one
smoke-scale guarded PPO continuation:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Decision:

```text
promote_m290x64_a500_and_admit_ppo_smoke
```

Next step:

```text
m291-row16-aware-guarded-ppo-smoke
```

M291 should stay smoke-scale. It must treat any loss of M183/M170 row16,
M267/M264 wrong-history drops, protected key validity, or behavior retention as
proof washout, not as a reason to lengthen PPO.
