# M414 Source-Weighted Replay-Anchor Probe

M414 tests the M413 source-weighted replay-anchor design without PPO,
promotion, threshold changes, or actor-input changes.

## Weighted Anchor

Run directory:

```text
runs/m414_source_weighted_replay_failure_trajectory_anchor
```

Primary artifact:

```text
runs/m414_source_weighted_replay_failure_trajectory_anchor/source_weighted_replay_failure_trajectory_anchor.npz
```

| Source | Rows | Weight multiplier |
| --- | ---: | ---: |
| M267/M264 replay-failure anchor | `669` | `1.0` |
| old-key replay-failure anchor | `290` | `10.0` |
| combined source-weighted anchor | `959` | mixed |

The exact repair run uses:

```text
lambda_replay_trajectory_anchor = 1e12
```

This gives effective replay pressure:

```text
M267/M264: 1e12
old-key:   1e13
```

## Projection Result

Projection run:

```text
runs/m414_source_weighted_projection_ltraj1e12_s40_seed10145
```

Candidate:

```text
runs/m414_source_weighted_projection_ltraj1e12_s40_seed10145/candidate_checkpoint.pt
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000129223` |
| exact M270 delta vs M400 | `-0.000150025` |
| old-key surrogate delta vs M400 | `-0.000198841` |
| exact lexicographic pass | `true` |
| replay trajectory anchor loss | `7.801935e-07` |
| old-key recovery preferred loss | `0.003633610` |

## Proof Gates

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `15 / 17` |
| M267/M264 gate pass | `false` |
| old-key accepted cases | `38 / 40` |
| old-key accepted regressions | `2` |
| old-key gate pass | `false` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 gate pass | `true` |

The source-weighted candidate improves utility but fails first proof gates.

## Utility Audit

Utility audit:

```text
runs/m414_source_weighted_utility_audit
```

| Metric | Value |
| --- | ---: |
| M414 recovery improvement retained vs M406 | `0.230460` |
| required recovery-retention ratio | `0.20` |
| M414 source-weighted anchor MSE | `7.801935e-07` |
| M411 source-weighted anchor MSE | `4.894314e-08` |

M414 passes the utility target that M411 failed, but it does so by giving up
too much proof retention.

## Interpretation

The M413 source-weighted scalar fix is directionally informative but
insufficient:

- Global `1e13` replay pressure passes proof but collapses utility.
- Source-weighted effective `1e12/1e13` improves utility but fails proof.

That means the active tradeoff is not just source imbalance. The residual needs
to become row/branch selective, and it should penalize only unsafe movement
beyond a replay-safe radius rather than anchoring every trajectory action
tightly to M400.

## Decision

Reject M414 and admit active-set hinge design:

```text
m415-active-set-replay-hinge-design
```

M415 should design a hinge or slack-radius residual that preserves rows near
replay failure while allowing recovery movement on rows that have closed-loop
slack.
