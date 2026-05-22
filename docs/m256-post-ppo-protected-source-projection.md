# M256 Post-PPO Protected-Source Projection

M256 tests a no-PPO projection repair after the M254 exact source gate failure.
The projection repairs exact source losses, but no tested interpolation alpha
preserves the M183/M170 proof row. No new PPO was run and actor inputs are
unchanged.

## Setup

M253 public-gate base:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

M254 raw PPO checkpoint:

```text
runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt
```

Projection run:

```text
runs/m256_post_ppo_protected_source_projection_seed10067
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
```

## Projection Objective

The protected-key source projection decreases the protected source loss:

| Policy | Protected-key sampled loss |
| --- | ---: |
| before M254 raw | 0.035649 |
| after projection | 0.023381 |

The projection is therefore effective in the offline objective.

## Exact Source Gate

The full projected checkpoint strongly improves both sources versus M253:

| Policy | Exact M232 | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m253_a0_00008 | 0.244635209 | 0 | 0 |
| m254_raw | 0.244611919 | -0.000032320 | +0.000009006 |
| m256_proj | 0.162676275 | -0.069699631 | -0.012259328 |

The projection fixes the protected-key source regression.

Interpolating from M253 toward the projected checkpoint also gives exact source
improvement for every tested alpha:

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m256_a0_00001 | 0.00001 | -0.000000664 | -0.000000126 |
| m256_a0_000025 | 0.000025 | -0.000001669 | -0.000000316 |
| m256_a0_00005 | 0.00005 | -0.000003370 | -0.000000635 |
| m256_a0_0001 | 0.0001 | -0.000006738 | -0.000001277 |
| m256_a0_0005 | 0.0005 | -0.000033631 | -0.000006377 |
| m256_a010 | 0.01 | -0.000673334 | -0.000127666 |

## Proof Gate Failure

Despite exact source improvement, M183/M170 replay fails for every tested
projection interpolation alpha.

| Policy | Alpha | Gate pass | Normal success | Success drops | Normal margin delta |
| --- | ---: | --- | ---: | ---: | ---: |
| m256_a0_00001 | 0.00001 | false | 0.941176 | 16 / 17 | -0.000001 |
| m256_a0_000025 | 0.000025 | false | 0.941176 | 16 / 17 | -0.000001 |
| m256_a0_00005 | 0.00005 | false | 0.941176 | 16 / 17 | -0.000003 |
| m256_a0_0001 | 0.0001 | false | 0.941176 | 16 / 17 | -0.000006 |
| m256_a0_0005 | 0.0005 | false | 0.941176 | 16 / 17 | -0.000028 |
| m256_a001 | 0.001 | false | 0.941176 | 16 / 17 | -0.000055 |
| m256_a0_0025 | 0.0025 | false | 0.941176 | 16 / 17 | -0.000138 |
| m256_a005 | 0.005 | false | 0.882353 | 15 / 17 | -0.000276 |
| m256_a010 | 0.01 | false | 0.294118 | 5 / 17 | -0.000551 |

The first failure is again row `16`:

```text
row_id = 16
target = future_braking_deceleration
physical_pair_key = 9530:6:9550:6
```

At M253, row 16 has almost no margin:

```text
normal_margin = 0.000000252
normal_success = true
```

At projection alpha `0.00001`, it already flips to collision:

```text
normal_margin = -0.000000172
normal_success = false
```

## Interpretation

The post-PPO projection solves the exact-source conflict but has the wrong
closed-loop direction for the knife-edge replay row. Because the public proof
surface is already near zero margin, shrinking the alpha is not enough.

The next projection repair needs to include the fragile closed-loop trajectory
anchor, especially the M183 row16 anchor from M235, not just protected-key
snippet/source loss.

## Decision

Reject M256. Keep M253 as the current public-gate base:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

Next step:

```text
m257-trajectory-anchored-projection-implementation
```
