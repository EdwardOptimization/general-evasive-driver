# M447 Fresh Policy-Difference Mining Run

M447 runs a larger fresh benchmark and applies the M446 policy-difference
miner. It is diagnostic only: no training, PPO, checkpoint promotion, threshold
relaxation, or actor input/output change.

## Benchmark

Benchmark run:

```text
runs/m447_fresh_policy_difference_benchmark_seed9700
```

Configuration:

```text
env config = configs/m121_human_view_zero_obstacle_relvel.json
episodes   = 512
seed       = 9700
```

Policy summary:

| Policy | Success | Collision | Return | Mean margin | Min margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | `0.302734` | `0.697266` | `43.394665` | `0.182480` | `-0.312266` |
| M399 base | `0.876953` | `0.123047` | `70.286337` | `1.831957` | `-0.257598` |
| M427 high-utility rejected | `0.876953` | `0.123047` | `70.272673` | `1.832165` | `-0.259425` |
| M434 `r0010` proof-safe | `0.876953` | `0.123047` | `70.291808` | `1.832139` | `-0.258343` |
| M438 `r0015` proof-safe | `0.876953` | `0.123047` | `70.291811` | `1.832118` | `-0.258579` |
| M442 tail v2 rejected | `0.876953` | `0.123047` | `70.283455` | `1.832144` | `-0.258514` |

Candidate deltas versus M399:

| Policy | Success delta | Collision delta | Return delta | Mean-margin delta | Min-margin delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| M427 high-utility rejected | `0.0` | `0.0` | `-0.013664` | `0.000208` | `-0.001828` |
| M434 `r0010` proof-safe | `0.0` | `0.0` | `0.005471` | `0.000182` | `-0.000745` |
| M438 `r0015` proof-safe | `0.0` | `0.0` | `0.005474` | `0.000161` | `-0.000981` |
| M442 tail v2 rejected | `0.0` | `0.0` | `-0.002882` | `0.000187` | `-0.000916` |

## Policy-Difference Mining

Miner run:

```text
runs/m447_fresh_policy_difference_mining_seed9700
```

Summary:

| Metric | Value |
| --- | ---: |
| comparison rows | `2048` |
| accepted rows | `3` |
| selected rows | `2` |
| accepted divergence types | `return_delta: 3` |
| selected divergence types | `return_delta: 2` |

Accepted rows:

| Seed | Policy | Type | Delta return | Delta margin |
| ---: | --- | --- | ---: | ---: |
| `9884` | `m427_high_utility` | `return_delta` | `-1.173514` | `0.006865` |
| `9706` | `m438_r0015` | `return_delta` | `1.482061` | `-0.001744` |
| `9706` | `m434_r0010` | `return_delta` | `1.471349` | `-0.001305` |

No candidate has:

```text
success_flip
collision_flip
margin_sign_flip
near_boundary_margin_delta
large_margin_delta
```

Per-policy maxima versus M399:

| Policy | Success diff count | Collision diff count | Margin sign diff count | Max absolute margin delta |
| --- | ---: | ---: | ---: | ---: |
| M427 high-utility rejected | `0` | `0` | `0` | `0.006865` |
| M434 `r0010` proof-safe | `0` | `0` | `0` | `0.002308` |
| M438 `r0015` proof-safe | `0` | `0` | `0` | `0.002870` |
| M442 tail v2 rejected | `0` | `0` | `0` | `0.003088` |

## Interpretation

The M444 conclusion holds on the larger fresh pool.

The recent candidate family is functionally indistinguishable from M399 on the
current M121 scenario distribution. M427's higher old-key recovery retained
does not produce broad success, collision, margin-sign, or near-boundary margin
differences. The only mined differences are small return shifts on safe
`aes_feasible` cases.

This rules out another useful local repair step on this candidate family. The
problem is no longer that the miner is missing rows; the current distribution
does not create meaningful closed-loop separation among these checkpoints.

## Decision

M447 passes as a diagnostic run:

- benchmark artifacts were produced;
- miner artifacts were produced;
- no checkpoint is promoted;
- no meaningful policy-difference surface is found;
- the active-boundary/recovery-retention candidate family should be archived
  as locally informative but not broad-performance relevant on M121.

Admit:

```text
m448-differentiating-challenge-distribution-design
```

M448 should design a more discriminative fresh scenario distribution before any
more objective design or PPO. The next distribution should make near-boundary
handling differences observable without adding hidden/oracle actor inputs.
