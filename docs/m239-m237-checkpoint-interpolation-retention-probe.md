# M239 M237 Checkpoint Interpolation Retention Probe

M239 tests whether M237 failed because the raw PPO update was too large for
near-boundary proof windows. No PPO is run in this milestone.

Actor inputs are unchanged.

## Setup

Base checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Target checkpoint:

```text
runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
```

Interpolation sweep:

```text
runs/m239_m224_to_m237_interpolation
```

Alphas:

| Policy | Alpha | Path |
| --- | ---: | --- |
| m239_a100 | 0.10 | `runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_1.pt` |
| m239_a250 | 0.25 | `runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_25.pt` |
| m239_a500 | 0.50 | `runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt` |
| m239_a750 | 0.75 | `runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_75.pt` |
| m239_a1000 | 1.00 | `runs/m239_m224_to_m237_interpolation/checkpoints/alpha_1.pt` |

## Fixed Objective

M232 combined objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.246506 |
| m239_a100 | 0.246503 |
| m239_a250 | 0.246499 |
| m239_a500 | 0.246492 |
| m239_a750 | 0.246486 |
| m239_a1000 | 0.246479 |

M223 objective:

| Policy | Loss |
| --- | ---: |
| m224_10063 | 0.209824 |
| m239_a100 | 0.209820 |
| m239_a250 | 0.209815 |
| m239_a500 | 0.209806 |
| m239_a750 | 0.209797 |
| m239_a1000 | 0.209789 |

The objective improvement is monotonic with alpha, so the raw PPO update is
moving in the intended offline-objective direction.

## Critical Proof Gates

M183 M170 replay:

| Policy | Alpha | Gate pass | Drops | Row 16 normal margin |
| --- | ---: | --- | ---: | ---: |
| m239_a100 | 0.10 | true | 17 / 17 | 0.000086 |
| m239_a250 | 0.25 | true | 17 / 17 | 0.000056 |
| m239_a500 | 0.50 | true | 17 / 17 | 0.000008 |
| m239_a750 | 0.75 | false | 16 / 17 | -0.000039 |
| m239_a1000 | 1.00 | false | 16 / 17 | -0.000084 |

Protected key `9944|perturbed|28|28`:

| Policy | Alpha | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 0.00 | true | 0.186385 | 0.086925 | 0.099460 |
| m239_a100 | 0.10 | true | 0.188361 | 0.088466 | 0.099895 |
| m239_a250 | 0.25 | true | 0.191347 | 0.090917 | 0.100429 |
| m239_a500 | 0.50 | true | 0.195916 | 0.095117 | 0.100798 |
| m239_a750 | 0.75 | false | 0.200336 | 0.099817 | 0.100519 |
| m239_a1000 | 1.00 | false | 0.204386 | 0.104743 | 0.099643 |

The failure boundary is consistent across both proof gates: `0.50` passes, while
`0.75` and `1.00` fail.

## Full Proof Retention For Selected Alpha

`m239_a500` also passes the broader replay surfaces:

| Corpus | Rows | Drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.000024 | 0.000053 | true |
| M183 M170 | 17 | 17 / 17 | -0.000028 | 0.000054 | true |
| M193 M189 | 14 | 14 / 14 | -0.000034 | 0.000103 | true |
| M212 M204 | 17 | 17 / 17 | -0.000039 | 0.000098 | true |
| M223 M219 | 17 | 17 / 17 | -0.000039 | 0.000098 | true |

## Behavior Diagnostic

`m239_a500` retains broad behavior on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m239_a500 | 0.8625 | 0.1375 | 1.835358 |
| 9505 | m239_a500_reset | 0.8500 | 0.1500 | 1.834003 |
| 9505 | m239_a500_zero_all | 0.8000 | 0.2000 | 1.853247 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m239_a500 | 0.8625 | 0.1375 | 1.852875 |
| 9506 | m239_a500_reset | 0.8500 | 0.1500 | 1.850272 |
| 9506 | m239_a500_zero_all | 0.8000 | 0.2000 | 1.871156 |

## Interpretation

M239 supports the M238 diagnosis. The M237 update direction is useful, but the
full step is too large for the near-boundary proof windows. A no-PPO
interpolation guard can retain some fixed-objective improvement while preserving
the proof surfaces.

`m239_a500` should be treated as a public-gate current base, not paper-level
promotion. It has not been evaluated on a private holdout or a broad fresh
scenario distribution.

## Decision

Promote this public-gate base:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Decision:

```text
promote_m239_a500_public_gate_base
```

Next step:

```text
m240-interpolation-guarded-ppo-repeat-from-m224
```

M240 should test repeatability: run one fresh trajectory-anchored PPO smoke from
M224, then apply the same interpolation guard before any candidate can be
accepted.
