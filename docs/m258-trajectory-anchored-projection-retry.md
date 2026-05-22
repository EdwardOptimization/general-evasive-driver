# M258 Trajectory-Anchored Projection Retry

M258 retries the M256 post-PPO projection repair with the M235 closed-loop
trajectory action anchor enabled. No new PPO was run. Actor inputs and the
human-view contract are unchanged.

## Setup

Public-gate base:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

Raw PPO checkpoint being repaired:

```text
runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt
```

Projection run:

```text
runs/m258_trajectory_anchored_projection_seed10068
```

Projection settings:

```text
steps = 40
learning_rate = 5e-5
batch_size = 1
train_scope = actor_coupling
protected snippet = runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
snippet anchor checkpoint = M253
snippet anchor coef = 1.0
trajectory anchor = runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
trajectory anchor coef = 100.0
trajectory anchor batch size = 32
```

## Projection Objective

The trajectory-anchored projection repairs the protected-key sampled objective,
but much more conservatively than M256:

| Metric | Before | After |
| --- | ---: | ---: |
| protected snippet loss | 0.035649199 | 0.035388511 |
| snippet anchor MSE | 0.000000008 | 0.000000685 |
| trajectory anchor MSE | 0.000000398 | 0.000000791 |

The objective improves without the large closed-loop-destructive movement seen
in M256.

## Exact Source Gate

The full projected checkpoint improves both sources versus M253:

| Policy | Exact M232 | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m253_a0_00008 | 0.244635209 | 0 | 0 |
| m254_raw | 0.244611919 | -0.000032320 | +0.000009006 |
| m258_proj | 0.244167 | -0.000216 | -0.000252 |

Interpolation from M253 toward the projected checkpoint keeps both source
deltas non-positive from `alpha=0.00005` onward:

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m258_a0_00005 | 0.00005 | -0.000000000124 | -0.000000009206 |
| m258_a0_0001 | 0.0001 | -0.000000012107 | -0.000000024549 |
| m258_a0_00025 | 0.00025 | -0.000000063633 | -0.000000064440 |
| m258_a0_0005 | 0.0005 | -0.000000113420 | -0.000000122744 |
| m258_a001 | 0.001 | -0.000000204752 | -0.000000242418 |
| m258_a0_0025 | 0.0025 | -0.000000547803 | -0.000000619855 |
| m258_a005 | 0.005 | -0.000001073425 | -0.000001233572 |
| m258_a010 | 0.01 | -0.000002160161 | -0.000002479419 |

`m258_a010` is the largest tested exact-gated alpha and advances to public
proof gates.

## Replay Gates

All public replay gates pass versus M253:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000004158 | +0.000001236 | true |
| M183 M170 | 17 | 17 / 17 | +0.000004161 | +0.000001271 | true |
| M193 M189 | 14 | 14 / 14 | +0.000003904 | +0.000002115 | true |
| M212 M204 | 17 | 17 / 17 | +0.000003641 | +0.000001959 | true |
| M223 M219 | 17 | 17 / 17 | +0.000003642 | +0.000001958 | true |

The M256 failure row is retained:

```text
row_id = 16
target = future_braking_deceleration
physical_pair_key = 9530:6:9550:6
normal_success = true
wrong_history_success = false
normal_margin = 0.000000252
wrong_history_margin = -0.005918427
margin_gap = 0.005918679
```

## Protected Key

Protected key `9944|perturbed|28|28` passes, and the known failing control
`m239_a750` still fails:

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m224_10063 | true | 0.186385 | 0.086925 | 0.099460 |
| m253_a0_00008 | true | 0.195820 | 0.095022 | 0.100799 |
| m258_a010 | true | 0.195973 | 0.095118 | 0.100855 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m253_a0_00008 | 0.8625 | 0.1375 | 1.835353 |
| 9505 | m258_a010 | 0.8625 | 0.1375 | 1.835355 |
| 9505 | m258_a010_reset | 0.8500 | 0.1500 | 1.834009 |
| 9505 | m258_a010_zero_all | 0.8000 | 0.2000 | 1.853254 |
| 9506 | m253_a0_00008 | 0.8625 | 0.1375 | 1.852870 |
| 9506 | m258_a010 | 0.8625 | 0.1375 | 1.852874 |
| 9506 | m258_a010_reset | 0.8500 | 0.1500 | 1.850279 |
| 9506 | m258_a010_zero_all | 0.8000 | 0.2000 | 1.871163 |

## Interpretation

M258 confirms the M256 failure was not caused by source projection itself. The
missing constraint was closed-loop trajectory retention. Adding the M235
trajectory anchor keeps the protected source repair direction small enough to
retain the knife-edge row16 proof surface and the protected key.

This is still single-seed repair evidence for the M254 PPO seed. It is strong
enough to promote `m258_a010` as the current public-gate base, but not enough
to lengthen PPO.

## Decision

Promote `m258_a010` as the current public-gate base:

```text
runs/m258_m253_to_projection_interpolation/checkpoints/alpha_0_01.pt
```

Next step:

```text
m259-trajectory-anchored-repair-repeat
```
