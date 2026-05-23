# M411 Combined Replay-Aware Projection Probe

M411 tests the M408/M409/M410 replay-aware projection idea without PPO,
promotion, threshold changes, or actor-input changes.

The question is whether the M406 exact-feasible replay failure can be repaired
by adding branch-specific replay-failure trajectory anchors as a secondary
projection residual.

## Combined Anchor

Run directory:

```text
runs/m411_combined_replay_failure_trajectory_anchor
```

Primary artifact:

```text
runs/m411_combined_replay_failure_trajectory_anchor/combined_replay_failure_trajectory_anchor.npz
```

| Source | Rows |
| --- | ---: |
| M409 M267/M264 replay-failure anchor | `669` |
| M410 old-key replay-failure anchor | `290` |
| combined anchor | `959` |

The M406 rejected candidate has combined replay-trajectory anchor loss
`7.238024e-05`, while the M400 base is near zero. This confirms the residual
sees the replay failure region.

## Projection Variants

All variants start from the same recovery-heavy raw checkpoint used by M406:

```text
runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
```

Base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

| Variant | Exact pass | M267/M264 | old-key compact | replay anchor loss | old-key recovery loss |
| --- | --- | ---: | ---: | ---: | ---: |
| `lambda_replay=1e11` | `true` | `5 / 17` | `34 / 40` | `2.541763e-05` | `0.003178101` |
| `lambda_replay=1e12` | `true` | `17 / 17` | `37 / 40` | `6.852042e-07` | `0.003610297` |
| `lambda_replay=1e13` | `true` | `17 / 17` | `40 / 40` | `2.168418e-08` | `0.003813319` |

The lower coefficients show the residual is correctly shaped but insufficient:
`1e11` improves M406 from `1/17` to `5/17` on M267/M264 and from `33/40` to
`34/40` on old-key compact, but still fails both gates. `1e12` fully repairs
M267/M264 but still leaves three old-key wrong-history-safe regressions.

## Selected Proof-Passing Candidate

Selected candidate:

```text
runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000014067` |
| exact M270 delta vs M400 | `-0.000023365` |
| old-key surrogate delta vs M400 | `-0.001078129` |
| exact lexicographic pass | `true` |
| selected step | `39` |

First proof gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| M267/M264 gate pass | `true` |
| old-key accepted regressions | `0` |
| old-key normal-success regressions | `0` |
| old-key gap p10 | `-0.000061514` |
| old-key gap min | `-0.000495151` |
| old-key gate pass | `true` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 gate pass | `true` |

## Interpretation

This is a positive proof-retention result, not a driver-performance result.

The strong `1e13` trajectory residual makes the replay branch behavior nearly
match the M400 base trajectory. It repairs M406's broad wrong-history washout
and old-key accepted regressions, but it also gives up most of the M406 recovery
movement:

- M406 recovery loss: `0.002919361`
- M411 `1e13` recovery loss: `0.003813319`
- M400 base recovery loss: `0.003873642`

So M411 proves that trajectory-level replay anchors can restore proof gates,
but the selected candidate is likely retention-heavy. It should not be promoted
or sent to full public gate until a utility/collapse audit quantifies whether it
has meaningful movement beyond M400.

## Decision

Admit:

```text
m412-replay-aware-projection-utility-audit
```

M412 should quantify whether the M411 `1e13` proof-passing candidate is useful
enough to chain, or whether it is effectively a base-projection/retention-only
result.
