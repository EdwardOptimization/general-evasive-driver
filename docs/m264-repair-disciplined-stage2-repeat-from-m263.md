# M264 Repair-Disciplined Stage2 Repeat From M263

M264 repeats the repaired 4096-step stage2 PPO discipline from the M263
public-gate base. Actor inputs are unchanged. No medium or long PPO was run.

## Setup

Current public-gate base:

```text
runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
```

Fresh stage2 PPO run:

```text
runs/ppo_m264_stage2_repeat_from_m263_seed5229
```

PPO settings:

```text
config = configs/ppo_m248_source_balanced_from_m239_smoke.json
init checkpoint = m263_a005
seed = 5229
total_steps = 4096
device = cuda
```

## Raw PPO Exact Source Gate

This raw PPO seed improves both exact sources versus M263:

| Policy | Aggregate delta | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m264_raw | -0.000365087956 | -0.000364443552 | -0.000000644403 |

Because the exact-source gate passes, no projection repair was needed for exact
source. Promotion still uses interpolation because the protected-key
normal-margin window remains tight.

## Interpolation Boundary

Selected interpolation exact-source deltas:

| Policy | Alpha | Aggregate delta | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: | ---: |
| m264_a001 | 0.0010 | -0.000000371610 | -0.000000368542 | -0.000000003069 |
| m264_a0_0025 | 0.0025 | -0.000000943879 | -0.000000931604 | -0.000000012274 |
| m264_a005 | 0.0050 | -0.000001886999 | -0.000001865518 | -0.000000021480 |
| m264_raw | 1.0000 | -0.000365087956 | -0.000364443552 | -0.000000644403 |

All listed candidates pass exact source, but protected-key replay limits the
safe alpha.

## Protected-Key Boundary

The protected-key boundary is between `alpha=0.001` and `alpha=0.0025`:

| Policy | Protected pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m264_a001 | true | 0.199971 | 0.099368 | 0.100604 |
| m264_a0_0025 | false | 0.200065 | 0.099470 | 0.100595 |
| m264_a005 | false | 0.200220 | 0.099640 | 0.100581 |
| m264_a010 | false | 0.200528 | 0.099976 | 0.100552 |
| m264_a050 | false | 0.202965 | 0.102972 | 0.099993 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

`m264_a001` is selected as the largest checked protected-key-safe candidate.
It leaves only:

```text
0.200000 - 0.199971 = 0.000029
```

of normal-margin slack.

## Replay Gates

All public replay gates pass for `m264_a001` versus M263:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000001036 | +0.000000392 | true |
| M183 M170 | 17 | 17 / 17 | +0.000001013 | +0.000000405 | true |
| M193 M189 | 14 | 14 / 14 | +0.000000884 | +0.000000794 | true |
| M212 M204 | 17 | 17 / 17 | +0.000000831 | +0.000000755 | true |
| M223 M219 | 17 | 17 / 17 | +0.000000833 | +0.000000760 | true |

M183/M170 row16 is retained:

```text
row_id = 16
normal_success = true
wrong_history_success = false
normal_margin = 0.000030
wrong_history_margin = -0.005919
margin_gap = 0.005949
```

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m263_a005 | 0.8625 | 0.1375 | 1.835352 | 65.964031 |
| 9505 | m264_a001 | 0.8625 | 0.1375 | 1.835352 | 65.963971 |
| 9505 | m264_a001_reset | 0.8500 | 0.1500 | 1.833997 | 64.059330 |
| 9505 | m264_a001_zero_all | 0.8000 | 0.2000 | 1.853242 | 61.043561 |
| 9506 | m263_a005 | 0.8625 | 0.1375 | 1.852869 | 66.240482 |
| 9506 | m264_a001 | 0.8625 | 0.1375 | 1.852869 | 66.240421 |
| 9506 | m264_a001_reset | 0.8500 | 0.1500 | 1.850267 | 64.349293 |
| 9506 | m264_a001_zero_all | 0.8000 | 0.2000 | 1.871150 | 61.306129 |

## Interpretation

M264 is positive but saturated. It repeats the repaired stage2 discipline in
the sense that raw PPO improves exact sources and the selected interpolation
passes replay, protected-key, and behavior gates.

It also shows that the protected-key normal-margin window has become the main
active constraint:

```text
M263 selected alpha = 0.005
M264 selected alpha = 0.001
M264 protected-key slack = 0.000029
```

Continuing PPO from here is likely to spend most of the harness effort on
single-key window preservation rather than learning a broader driver. The next
step should audit this saturation before any more PPO.

## Decision

Promote `m264_a001` as the current public-gate base:

```text
runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Next step:

```text
m265-protected-key-window-saturation-audit
```
