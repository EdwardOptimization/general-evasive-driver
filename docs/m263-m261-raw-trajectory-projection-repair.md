# M263 M261 Raw Trajectory Projection Repair

M263 repairs the M261 raw stage2 PPO checkpoint without running new PPO. Actor
inputs are unchanged.

## Setup

Current public-gate base:

```text
runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Raw PPO checkpoint repaired:

```text
runs/ppo_m261_stage2_repeat_from_m260_seed5228/checkpoint.pt
```

Projection run:

```text
runs/m263_m261_raw_trajectory_projection_seed10070
```

Projection settings:

```text
steps = 40
learning_rate = 5e-5
batch_size = 1
train_scope = actor_coupling
protected snippet = runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
snippet anchor checkpoint = M261 alpha 0.001
snippet anchor coef = 1.0
trajectory anchor = runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
trajectory anchor coef = 100.0
trajectory anchor batch size = 32
```

## Projection Objective

The projection repairs the protected-key snippet objective while reducing
trajectory-anchor error:

| Metric | Before | After |
| --- | ---: | ---: |
| protected snippet loss | 0.035641793 | 0.035368122 |
| snippet anchor MSE | 0.000000031 | 0.000000947 |
| trajectory anchor MSE | 0.000004955 | 0.000001305 |

## Exact Source Gate

The full projected checkpoint improves both sources versus M261:

| Policy | Aggregate delta | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m261_raw | -0.000322285334 | -0.000329149766 | +0.000006864431 |
| m263_proj | -0.000668191234 | -0.000401383640 | -0.000266807594 |

Interpolation from M261 toward the projection is exact-source safe across the
tested sweep:

| Policy | Alpha | Aggregate delta | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: | ---: |
| m263_a005 | 0.005 | -0.000003247032 | -0.000001945951 | -0.000001301081 |
| m263_a010 | 0.010 | -0.000006508478 | -0.000003900178 | -0.000002608300 |
| m263_a500 | 0.500 | -0.000329803371 | -0.000197804987 | -0.000131998384 |

## Protected-Key Boundary

Full projection passes M183/M170 replay but fails the protected key. The
protected-key interpolation boundary is between `alpha=0.005` and `alpha=0.010`:

| Policy | Protected pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m261_a001 | true | 0.199615 | 0.098992 | 0.100624 |
| m263_a0_0005 | true | 0.199645 | 0.099023 | 0.100622 |
| m263_a001 | true | 0.199674 | 0.099053 | 0.100621 |
| m263_a0_0025 | true | 0.199763 | 0.099146 | 0.100617 |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m263_a010 | false | 0.200200 | 0.099606 | 0.100594 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

`m263_a005` is selected as the largest checked protected-key-safe candidate.

## Replay Gates

All public replay gates pass for `m263_a005` versus M261:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000006821 | +0.000001523 | true |
| M183 M170 | 17 | 17 / 17 | +0.000006766 | +0.000001566 | true |
| M193 M189 | 14 | 14 / 14 | +0.000006173 | +0.000003373 | true |
| M212 M204 | 17 | 17 / 17 | +0.000005928 | +0.000003216 | true |
| M223 M219 | 17 | 17 / 17 | +0.000005927 | +0.000003208 | true |

M183/M170 row16 is retained:

```text
row_id = 16
normal_success = true
wrong_history_success = false
normal_margin = 0.000029
wrong_history_margin = -0.005919
margin_gap = 0.005949
```

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m261_a001 | 0.8625 | 0.1375 | 1.835353 | 65.964340 |
| 9505 | m263_a005 | 0.8625 | 0.1375 | 1.835352 | 65.964031 |
| 9505 | m263_a005_reset | 0.8500 | 0.1500 | 1.833998 | 64.059335 |
| 9505 | m263_a005_zero_all | 0.8000 | 0.2000 | 1.853242 | 61.043568 |
| 9506 | m261_a001 | 0.8625 | 0.1375 | 1.852870 | 66.240797 |
| 9506 | m263_a005 | 0.8625 | 0.1375 | 1.852869 | 66.240482 |
| 9506 | m263_a005_reset | 0.8500 | 0.1500 | 1.850267 | 64.349298 |
| 9506 | m263_a005_zero_all | 0.8000 | 0.2000 | 1.871151 | 61.306137 |

## Interpretation

M263 confirms that M261 raw PPO was not unusable. The protected-source
regression can be repaired by trajectory-anchored post-PPO projection, and the
repaired direction admits a larger proof-safe update than M261's raw
interpolation:

```text
M261 raw interpolation safe alpha = 0.001
M263 repaired interpolation safe alpha = 0.005
```

The limiting gate remains the protected-key normal-margin window. The full
projection and `alpha=0.010` both fail because normal-history margin moves
above `0.2`, not because replay or broad behavior collapses.

## Decision

Promote `m263_a005` as the current public-gate base:

```text
runs/m263_m261_to_projection_interpolation/checkpoints/alpha_0_005.pt
```

Next step:

```text
m264-repair-disciplined-stage2-repeat-from-m263
```
