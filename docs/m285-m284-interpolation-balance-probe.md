# M285 M284 Interpolation Balance Probe

M285 probes no-training interpolation from the current M272 public-gate base
toward the rejected M284 actor update.

No PPO, actor update, promotion, or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Target checkpoint:

```text
runs/m284_m272_actor_coupling_m270_rejected_trajectory_anchor_s10_lr5e5_seed10078/optimized_checkpoint.pt
```

Artifacts:

```text
runs/m285_m272_to_m284_interpolation_balance/alpha_summary.csv
runs/m285_m272_to_m284_interpolation_balance/balance_summary.json
runs/m285_m272_to_m284_interpolation_balance/full_gate_summary.json
```

## Interpolation Sweep

M284 contains a useful M267/M264 rejected-history retention direction, but raw
M284 destroys old M183/M170 normal behavior. The interpolation sweep shows that
the safe trust region is extremely narrow.

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 normal success | M267/M264 pass | Both first gates |
| ---: | ---: | --- | ---: | --- | --- |
| 0.0000 | 0.681375623 | true | 1.000000 | true | true |
| 0.00005 | 0.681375384 | true | 1.000000 | true | true |
| 0.0001 | 0.681375146 | true | 1.000000 | true | true |
| 0.0002 | 0.681374669 | true | 1.000000 | true | true |
| 0.0005 | 0.681373298 | false | 0.941176 | true | false |
| 1.0000 | 0.676685393 | false | 0.176471 | true | false |

Largest alpha that passes both first proof gates:

```text
alpha = 0.0002
checkpoint = runs/m285_m272_to_m284_interpolation_balance/checkpoints/alpha_0_0002.pt
```

The exact M270 improvement at this alpha is only:

```text
0.6813756227493286 -> 0.6813746690750122
delta = -0.00000095367431640625
```

The first failing alpha is 0.0005. It fails M183/M170 row16 by normal-history
collision:

| Row | Normal success | Success drop | Normal margin | Wrong-history margin | Margin gap |
| ---: | --- | --- | ---: | ---: | ---: |
| 16 | false | false | -0.000000240 | -0.005950313 | 0.005950073 |

## Full Public Gates

Because alpha 0.0002 passed both first gates, M285 ran the full public proof and
behavior stack against the M272 base.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | -0.000000418 | +0.000000016 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | -0.000000418 | +0.000000013 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | -0.000000375 | -0.000000004 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | -0.000000380 | -0.000000002 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | -0.000000378 | -0.000000001 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | -0.000000379 | +0.000000002 | true |

The old protected-key diagnostic still passes and remains discriminative:

```text
runs/m285_m272_to_m284_interpolation_balance/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m285_a000 | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m285_a0_0002 | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m285_a0_0002_reset | 0.8500 | 0.1500 | 1.833993 |
| 9505 | m285_a0_0002_zero_all | 0.8000 | 0.2000 | 1.853238 |
| 9506 | m285_a000 | 0.8625 | 0.1375 | 1.852854 |
| 9506 | m285_a0_0002 | 0.8625 | 0.1375 | 1.852853 |
| 9506 | m285_a0_0002_reset | 0.8500 | 0.1500 | 1.850263 |
| 9506 | m285_a0_0002_zero_all | 0.8000 | 0.2000 | 1.871146 |

## Interpretation

M285 confirms that the M284 direction is not fundamentally invalid: a very tiny
interpolation preserves every public proof and behavior gate while improving
the exact M270 objective.

However, the useful movement is too small to justify a new base. The safe alpha
is 0.0002, the exact improvement is under one micro-unit, and alpha 0.0005
already crosses the M183/M170 row16 terminal-margin cliff. This is the same
trust-region problem seen in M276, now with the M267/M264 rejected trajectory
direction included.

The next useful step is not PPO and not promotion. The rejected-history
trajectory anchor needs balance calibration: lower rejected-repeat, lower
trajectory-anchor pressure, or a more source-balanced anchor composition.

## Decision

Archive M285 as a boundary diagnostic rather than promoting alpha 0.0002.

Decision:

```text
archive_m285_a0_0002_boundary_diagnostic
```

Next step:

```text
m286-rejected-trajectory-anchor-balance-sweep
```

M286 should run a no-PPO balance sweep for rejected-history trajectory anchoring.
It must keep M272 as the base, gate M183/M170 and M267/M264 first, and avoid
promoting any candidate whose improvement is only a microscopic interpolation
artifact.
