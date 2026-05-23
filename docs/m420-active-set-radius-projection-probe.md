# M420 Active-Set Radius Projection Probe

M420 probes the M419 radius anchors in no-PPO exact projection. It does not run
PPO, promote a checkpoint, lower thresholds, or change actor inputs.

## Probe Order

M418 pre-registered this order:

```text
medium -> conservative if proof fails -> loose if medium passes proof but utility < 0.20
```

Medium failed old-key proof, so M420 ran conservative next. Loose was not run
because its pre-registered branch condition was not met.

## Medium Radius

Projection run:

```text
runs/m420_medium_radius_projection_ltraj1e13_s40_seed10150
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000013351` |
| exact M270 delta vs M400 | `-0.000065207` |
| old-key surrogate delta vs M400 | `-0.000158787` |
| exact lexicographic pass | `true` |
| radius-anchor hinge loss | `2.354936e-08` |
| recovery retained vs M406 | `0.143419` |

First gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| M267/M264 pass | `true` |
| old-key accepted cases | `39 / 40` |
| old-key pass | `false` |

The single old-key failure is:

```text
10023|perturbed|12|12|11.000000|-0.800000|1.200000
```

The wrong-history margin remains positive under medium radius:

```text
wrong_history_margin = 0.0472326918
```

## Conservative Radius

Projection run:

```text
runs/m420_conservative_radius_projection_ltraj1e13_s40_seed10151
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000011086` |
| exact M270 delta vs M400 | `-0.000052273` |
| old-key surrogate delta vs M400 | `-0.000187397` |
| exact lexicographic pass | `true` |
| radius-anchor hinge loss | `2.313784e-08` |
| recovery retained vs M406 | `0.115403` |

First gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| M267/M264 pass | `true` |
| old-key accepted cases | `40 / 40` |
| old-key pass | `true` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 pass | `true` |

Conservative radius is proof-safe but still below the primary utility threshold
of `0.20` recovery retained vs M406.

## Interpretation

M420 improves over M417 zero-radius `1e13` on utility:

| Candidate | Proof | Recovery retained vs M406 |
| --- | --- | ---: |
| M417 zero-radius `1e13` | pass | `0.054387` |
| M420 conservative radius | pass | `0.115403` |
| M420 medium radius | old-key `39/40` | `0.143419` |

This is useful partial evidence: radius slack works in the intended direction,
but the current source-level radius profiles are still too coarse. The medium
profile loses exactly old-key case `10023`, while conservative recovers proof at
the cost of utility.

The next design should not lower thresholds and should not run PPO. It should
mix radii per case:

```text
start from medium radius
tighten only old-key 10023 to conservative or tighter
consider loose radii only on rows that did not become active proof failures
keep old-key spillover guards visible
```

## Decision

Reject M420 as a promotable candidate and admit mixed-radius boundary design:

```text
m421-mixed-radius-boundary-design
```
