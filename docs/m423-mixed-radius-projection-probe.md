# M423 Mixed-Radius Projection Probe

M423 probes the M422 mixed-radius anchors in no-PPO exact projection. It does
not run PPO, promote a checkpoint, lower thresholds, or change actor inputs.

## Summary

M423 improves the proof-safe utility floor relative to M420 conservative, but
does not reach the primary recovery-retention threshold.

| Candidate | Proof result | Recovery retained vs M406 |
| --- | --- | ---: |
| M420 conservative | proof pass | `0.115403` |
| `mixed_a` | proof pass | `0.126033` |
| `mixed_b` | proof pass | `0.133154` |
| `mixed_c` | proof fail | `0.142650` |
| M420 medium | old-key `39/40` | `0.143419` |

The best proof-passing candidate is `mixed_b`, but it remains below the primary
`0.20` utility target. The highest-utility mixed candidate, `mixed_c`, reopens
the same active proof failures.

## `mixed_a`

Projection run:

```text
runs/m423_mixed_a_projection_ltraj1e13_s40_seed10153
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000053525` |
| exact M270 delta vs M400 | `-0.000081539` |
| old-key surrogate delta vs M400 | `-0.000093460` |
| exact lexicographic pass | `true` |
| radius-anchor hinge loss | `1.830185e-08` |
| recovery retained vs M406 | `0.126033` |

Proof gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| old-key accepted cases | `40 / 40` |
| M183/M170 success drops | `17 / 17` |

## `mixed_b`

Projection run:

```text
runs/m423_mixed_b_projection_ltraj1e13_s40_seed10154
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000047445` |
| exact M270 delta vs M400 | `-0.000078201` |
| old-key surrogate delta vs M400 | `-0.000109196` |
| exact lexicographic pass | `true` |
| radius-anchor hinge loss | `1.960652e-08` |
| recovery retained vs M406 | `0.133154` |

Proof gates:

| Gate | Result |
| --- | ---: |
| M267/M264 success drops | `17 / 17` |
| old-key accepted cases | `40 / 40` |
| M183/M170 success drops | `17 / 17` |

`mixed_b` is the best proof-passing M423 candidate, but it is not promotable
because recovery retained vs M406 is below `0.20`.

## `mixed_c`

Projection run:

```text
runs/m423_mixed_c_projection_ltraj1e13_s40_seed10155
```

Exact metrics:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 | `-0.000022531` |
| exact M270 delta vs M400 | `-0.000065804` |
| old-key surrogate delta vs M400 | `-0.000041485` |
| exact lexicographic pass | `true` |
| radius-anchor hinge loss | `1.946606e-08` |
| recovery retained vs M406 | `0.142650` |

Proof failures:

| Surface | Failure |
| --- | --- |
| M267/M264 | `15 / 17` success drops; rows `6` and `15` become wrong-history successes |
| old-key compact | `39 / 40`; old-key `10023` remains accepted |

The M267 wrong-history margins that cross positive are small but decisive:

```text
row 6:  +0.000032680
row 15: +0.000028111
```

## Interpretation

Radius-only mixing has almost exhausted its useful range:

- tightening `10023` repairs old-key proof;
- loosening `10004` helps utility only modestly;
- loosening M267 rows reopens the same row `6` and `15` wrong-history proof
  failures;
- the best proof-safe utility is still only `0.133154`.

The next step should audit the utility ceiling before designing another anchor.
The likely issue is that the M398 recovery movement conflicts with exact
M297/M270 and replay proof rows in a broader way than the current per-source
radius profile can express.

## Decision

Reject M423 as a promotable candidate and admit utility ceiling audit:

```text
m424-mixed-radius-utility-ceiling-audit
```
