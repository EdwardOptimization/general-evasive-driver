# M289 Row16-Aware Balanced Repeat Calibration

M289 tests a row16-aware repair after M288 found that M287 seed fragility was
caused by old M183/M170 terminal-margin row16 rather than loss of the
current-family M267/M264 direction.

No PPO or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Base balanced anchor:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/anchors/repeat2/combined_recovery_rejected_anchor.npz
```

Row16 recovery anchor source:

```text
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.npz
```

M289 appended additional copies of the M183/M170 row16 recovery anchor:

| Variant | Extra row16 repeats | Rows | Weight max | Weight mean |
| --- | ---: | ---: | ---: | ---: |
| extra64 | 64 | 3292 | 100 | 13.859877 |
| extra256 | 256 | 3484 | 100 | 18.606979 |

## Raw Calibration

Both raw updates improve exact M270 and protect M183/M170, but too much row16
pressure weakens M267/M264.

| Candidate | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | --- | ---: | --- | ---: |
| M272 base | 0.681375623 | true | 17 | true | 17 |
| extra64 raw | 0.676717937 | true | 17 | false | 15 |
| extra256 raw | 0.677119613 | true | 17 | false | 7 |

This confirms that row16-aware anchoring fixes the old-surface cliff, but it
must be balanced against current-family wrong-history retention.

## Extra64 Interpolation

M289 selected extra64 as the less destructive row16-aware direction and
interpolated from M272 toward it.

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| ---: | ---: | --- | ---: | --- | ---: |
| 0.000 | 0.681375623 | true | 17 | true | 17 |
| 0.100 | 0.680916071 | true | 17 | true | 17 |
| 0.300 | 0.679992855 | true | 17 | true | 17 |
| 0.500 | 0.679064095 | true | 17 | true | 17 |
| 0.600 | 0.678597569 | true | 17 | true | 17 |
| 0.700 | 0.678129792 | true | 17 | false | 16 |
| 1.000 | 0.676717937 | true | 17 | false | 15 |

Selected candidate:

```text
policy = m289x64_a600
checkpoint = runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
```

Objective improvement:

```text
0.6813756227493286 -> 0.6785975694656372
delta = -0.0027780532836914062
```

This is materially larger than M287 and slightly better than M286:

```text
M286 delta = -0.0025473833084106445
M287 delta = -0.00002682209014892578
M289 delta = -0.0027780532836914062
```

## Full Public Gates

The selected `m289x64_a600` candidate passes the full public replay stack.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | +0.000820881 | +0.000235982 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | +0.000834625 | +0.000230559 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | +0.000796615 | +0.000180103 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | +0.000769386 | +0.000177838 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | +0.000769468 | +0.000177847 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | +0.000769601 | +0.000177836 | true |

The old protected-key diagnostic passes and remains discriminative:

```text
runs/m289_row16_aware_balanced_repeat_calibration/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m272_base | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m289x64_a600 | 0.8625 | 0.1375 | 1.836175 |
| 9505 | m289x64_a600_reset | 0.8500 | 0.1500 | 1.834628 |
| 9505 | m289x64_a600_zero_all | 0.8000 | 0.2000 | 1.853607 |
| 9506 | m272_base | 0.8625 | 0.1375 | 1.852854 |
| 9506 | m289x64_a600 | 0.8625 | 0.1375 | 1.853723 |
| 9506 | m289x64_a600_reset | 0.8500 | 0.1500 | 1.850918 |
| 9506 | m289x64_a600_zero_all | 0.8000 | 0.2000 | 1.871539 |

## Interpretation

M289 repairs the M287 seed-fragility failure mode. Extra row16 recovery pressure
prevents the old M183/M170 row16 terminal-margin cliff, while interpolation at
alpha 0.6 preserves M267/M264 wrong-history success drops.

This is a stronger public-gate candidate than M286 on the fixed M270 objective
and public behavior metrics. It still should not immediately start PPO: the
row16-aware recipe itself needs one more fresh-seed repeat before PPO
continuation.

## Decision

Promote `m289x64_a600` as the current public-gate base:

```text
runs/m289_row16_aware_balanced_repeat_calibration/extra64_interpolation/checkpoints/alpha_0_6.pt
```

Decision:

```text
promote_m289x64_a600_public_gate_base
```

Next step:

```text
m290-row16-aware-balanced-repeat-fresh-seed
```

M290 should repeat the row16-aware extra64 recipe on a new optimizer seed before
any PPO continuation.
