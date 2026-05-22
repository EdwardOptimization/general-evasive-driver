# M250 Protected-Key Source Actor-Coupling Calibration

M250 tests whether a tiny no-PPO interpolation from the M239 public-gate base
toward the M249 protected-key source-only actor-coupling checkpoint can improve
the exact source objective without losing public proof or behavior retention.

Actor inputs are unchanged.

## Setup

Base checkpoint:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Target checkpoint:

```text
runs/m249_protected_key_source_actor_coupling_probe/optimized_checkpoint.pt
```

Selected checkpoint:

```text
runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
```

No PPO was run in this milestone.

## Exact Source Gate

The normal sweep from `0.001` to `0.1` improved exact source losses, but every
candidate failed M183/M170 replay retention. Micro alphas from `0.0001` to
`0.0005` also failed M183/M170 replay retention.

Nano alphas passed the M183/M170 replay gate. The largest tested passing alpha
is `0.00005`, labeled `m250_n00005`.

Exact source-aware deltas versus M239:

| Policy | Alpha | M232 delta | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: | ---: |
| m250_n00001 | 0.00001 | -0.000001788 | -0.000001512 | -0.000000276 |
| m250_n000025 | 0.000025 | -0.000004449 | -0.000003762 | -0.000000687 |
| m250_n00005 | 0.00005 | -0.000008885 | -0.000007513 | -0.000001372 |

The selected alpha satisfies the source gate:

```text
aggregate M232 delta < 0
M223 source delta < 0
protected_key source delta < 0
```

## Replay Gates

`m250_n00005` retains all public replay rows versus M239.

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.0000055 | -0.0000001 | true |
| M183 M170 | 17 | 17 / 17 | -0.0000055 | -0.0000001 | true |
| M193 M189 | 14 | 14 / 14 | -0.0000048 | -0.0000004 | true |
| M212 M204 | 17 | 17 / 17 | -0.0000051 | -0.0000003 | true |
| M223 M219 | 17 | 17 / 17 | -0.0000051 | -0.0000003 | true |

The result is intentionally small. `alpha=0.0001` already drops M183/M170
normal success to `16/17`, so the safe trust-region window is very narrow.

## Protected Key

Protected key `9944|perturbed|28|28` passes. The guard run also includes the
known-failing `m239_a750` checkpoint, so the gate remains discriminative.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m224_10063 | true | 0.186385 | 0.086925 | 0.099460 |
| m239_a500 | true | 0.195916 | 0.095117 | 0.100798 |
| m250_n00005 | true | 0.195854 | 0.095058 | 0.100797 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

Run directory:

```text
runs/m250_critical_key_seed9944_n00005
```

## Behavior Retention

The selected alpha retains broad behavior on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m239_a500 | 0.8625 | 0.1375 | 1.835358 |
| 9505 | m250_n00005 | 0.8625 | 0.1375 | 1.835355 |
| 9505 | m250_n00005_reset | 0.8500 | 0.1500 | 1.834004 |
| 9505 | m250_n00005_zero_all | 0.8000 | 0.2000 | 1.853246 |
| 9506 | m239_a500 | 0.8625 | 0.1375 | 1.852875 |
| 9506 | m250_n00005 | 0.8625 | 0.1375 | 1.852872 |
| 9506 | m250_n00005_reset | 0.8500 | 0.1500 | 1.850273 |
| 9506 | m250_n00005_zero_all | 0.8000 | 0.2000 | 1.871154 |

## Harness Finding

The built-in interpolation sweep currently rounds alpha file tokens to three
decimal places and alpha labels to thousandths. This caused sub-`0.001` alpha
collisions in the discarded run:

```text
runs/m250_micro_m239_to_protected_source_interpolation
```

The valid micro and nano checkpoints in this milestone were therefore written
with explicit custom paths. That infrastructure issue must be fixed before more
nano sweeps.

## Decision

Promote `m250_n00005` as the current public-gate base:

```text
runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
```

This is not a paper-level promotion. It is a public-gate base improvement that
slightly decreases exact source losses while retaining the existing proof and
behavior gates.

Next step:

```text
m251-checkpoint-interpolation-alpha-token-fix
```
