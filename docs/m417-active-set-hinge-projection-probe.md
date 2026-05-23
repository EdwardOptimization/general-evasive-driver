# M417 Active-Set Hinge Projection Probe

M417 probes the M416 active-set hinge anchor without PPO, promotion, threshold
changes, or actor-input changes.

## Projection Variants

Both variants use:

```text
base: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
raw:  runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
anchor: runs/m416_active_set_hinge_anchor/active_set_hinge_trajectory_anchor.npz
```

## Lambda `1e12`

Projection run:

```text
runs/m417_active_set_hinge_projection_ltraj1e12_s40_seed10147
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000040531` |
| exact M270 delta vs M400 | `-0.000014901` |
| old-key surrogate delta vs M400 | `-0.000134945` |
| exact lexicographic pass | `true` |
| active-set hinge loss | `6.001700e-07` |
| recovery retained vs M406 | `0.226007` |

First gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `15 / 17` |
| M267/M264 pass | `false` |
| old-key accepted cases | `35 / 40` |
| old-key pass | `false` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 pass | `true` |

This variant preserves enough recovery utility but fails proof.

## Lambda `1e13`

Projection run:

```text
runs/m417_active_set_hinge_projection_ltraj1e13_s40_seed10148
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000022888` |
| exact M270 delta vs M400 | `-0.000020683` |
| old-key surrogate delta vs M400 | `-0.003199100` |
| exact lexicographic pass | `true` |
| active-set hinge loss | `1.852823e-08` |
| recovery retained vs M406 | `0.054387` |

First gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| M267/M264 pass | `true` |
| old-key accepted regressions | `0` |
| old-key pass | `true` |
| M183/M170 success drops | `17 / 17` |
| M183/M170 pass | `true` |

This variant repairs proof but fails the pre-registered utility gate
(`>= 0.20` recovery retained vs M406).

## Interpretation

M417 shows the active-set selection is useful but zero-radius active anchors
still create a hard proof/utility switch:

- `1e12`: utility passes, proof fails.
- `1e13`: proof passes, utility fails.

The next residual should use the radius field that M416 added, not another
scalar weight. The radius should allow bounded action movement around the safe
anchor while still preventing the specific wrong-history branches from crossing
into success.

## Decision

Reject M417 as a candidate and admit radius calibration design:

```text
m418-active-set-radius-calibration-design
```
