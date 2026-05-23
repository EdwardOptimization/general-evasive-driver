# M434 Selective 10004 Projection Probe

M434 runs the M430 no-PPO projected-recovery recipe across the six M433
selective `10004` anchors. It does not run PPO, promote a checkpoint, lower
thresholds, or change actor inputs.

## Exact Projection

All six profiles pass exact M297/M270/old-key no-regression.

| Profile | Exact pass | Recovery retained vs M406 | Anchor loss | Selected step |
| --- | --- | ---: | ---: | ---: |
| `r0005` | true | `0.076823` | `1.740793e-09` | `33` |
| `r0010` | true | `0.103529` | `4.245227e-09` | `33` |
| `r0015` | true | `0.119585` | `4.288862e-09` | `39` |
| `r0020` | true | `0.143915` | `5.224678e-09` | `38` |
| `tail_r0005` | true | `0.132169` | `5.217599e-09` | `35` |
| `tail_r0010` | true | `0.145627` | `5.489437e-09` | `39` |

The best exact utility profile is `tail_r0010`, but exact gates alone are not
the promotion criterion.

## First Replay Gates

All profiles preserve M267/M264 `17 / 17` success drops.

Old-key compact replay is the limiting gate:

| Profile | M267/M264 | Old-key accepted | Old-key normal-success | Result |
| --- | ---: | ---: | ---: | --- |
| `r0005` | `17 / 17` | `40 / 40` | `40 / 40` | proof-safe but low utility |
| `r0010` | `17 / 17` | `40 / 40` | `40 / 40` | best proof-safe profile |
| `r0015` | `17 / 17` | `39 / 40` | `40 / 40` | old-key gap failure |
| `r0020` | `17 / 17` | `38 / 40` | `40 / 40` | old-key gap failure |
| `tail_r0005` | `17 / 17` | `38 / 40` | `40 / 40` | old-key gap failure |
| `tail_r0010` | `17 / 17` | `37 / 40` | `40 / 40` | old-key gap failure |

`r0010` then passes the old-key replay gate and M183/M170:

| Gate | Result |
| --- | ---: |
| old-key replay gate | `pass` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 normal success | `1.0` |
| M183/M170 wrong-history success | `0.0` |

## Failure Boundary

First failing old-key rows:

| Profile | Failed case(s) |
| --- | --- |
| `r0015` | `10023|perturbed|12|12`, gap erosion |
| `r0020` | `10004|perturbed|31|31`, `10023|perturbed|12|12` |
| `tail_r0005` | `10004|perturbed|31|31`, `10023|perturbed|12|12` |
| `tail_r0010` | `10004|perturbed|31|31`, `10023|perturbed|12|12`, `9998|perturbed|25|25` |

This means the selective radius family helps, but it does not solve the
underlying proof/utility tradeoff. Relaxing `10004` from `0.0002` to `0.0010`
is safe and improves utility over M430 (`0.061702 -> 0.103529`). Relaxing to
`0.0015` shifts the active boundary to `10023`; looser or terminal-only profiles
reopen `10004` and spillover `9998`.

## Decision

Reject M434 as a primary pass:

- it does not reach the `0.20` recovery-retention target;
- it does not beat M427's `0.174354` recovery retention;
- looser profiles fail old-key compact.

The best proof-safe candidate is:

```text
runs/m434_selective_10004_projection_r0010/candidate_checkpoint.pt
```

It is useful diagnostic evidence, not a new base.

Admit:

```text
m435-selective-boundary-failure-audit
```

M435 should audit the new active boundary (`10023`, then `10004`/`9998`) and
decide whether the next residual should move from trajectory action radii to a
terminal-margin or rejected-branch preference objective.
