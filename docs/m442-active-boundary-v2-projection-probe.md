# M442 Active-Boundary V2 Projection Probe

M442 tests the M441 active-boundary v2 residual in a no-PPO exact projection.
No PPO was run, no checkpoint was promoted, no thresholds were lowered, and
actor inputs/outputs were unchanged.

## Probe Setup

Base checkpoint:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Raw recovery checkpoint:

```text
runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
```

V2 active-boundary corpus:

```text
runs/m441_active_boundary_v2_residual/active_boundary_v2_corpus.npz
```

Candidate:

```text
runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
```

The candidate uses the M433 `tail_r0010` selective anchor plus:

```text
lambda_active_boundary_v2 = 1e12
steps = 40
learning_rate = 2e-6
project_recovery_gradient = true
```

## Exact Projection

| Metric | Value |
| --- | ---: |
| selected step | `28` |
| exact M297 delta vs base | `-0.000000715` |
| exact M270 delta vs base | `-0.000051022` |
| old-key surrogate delta vs base | `-0.000981808` |
| active_boundary_v2_loss | `0.0059865378` |
| active_boundary_v2_wrong_loss | `0.0042643603` |
| active_boundary_v2_gap_loss | `0.0017221733` |
| active_boundary_v2_normal_loss | `0.0000000042` |
| exact lexicographic pass | `true` |

The exact objectives pass, but the v2 residual itself does not materially move
in the useful direction: active-boundary v2 loss is slightly higher than the
M441 no-update value `0.0059865140`.

Recovery retained vs M406 is:

```text
0.111895
```

This is below the M438 `r0015` proof-safe reference:

```text
0.120957
```

So the candidate fails the minimum useful utility criterion even before the
old-key replay failure is considered.

## Closed-Loop Gates

M267/M264 first replay:

```text
runs/m442_tail_v2_l1e12_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| normal success | `1.0` |
| wrong-history success | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000375` |
| margin gap mean delta | `-0.000130` |
| gate pass | `true` |

M183/M170 first replay:

```text
runs/m442_tail_v2_l1e12_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| normal success | `1.0` |
| wrong-history success | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000402` |
| margin gap mean delta | `-0.000174` |
| gate pass | `true` |

Old-key compact replay:

```text
runs/m442_tail_v2_l1e12_old_key_targeted_replay
```

| Metric | Value |
| --- | ---: |
| accepted cases | `39 / 40` |
| normal-success cases | `40 / 40` |
| margin gap mean | `0.008428` |
| margin gap min | `0.000769` |
| policy pass | `false` |

The failing row is:

| Key | Normal margin | Wrong-history margin | Margin gap | Accepted |
| --- | ---: | ---: | ---: | --- |
| `10004|perturbed|31|31` | `0.001000` | `0.000231` | `0.000769` | false |

This is a wrong-history-safety failure: the normal branch remains successful,
but the wrong-history branch becomes safe on the active old-key boundary.

## Interpretation

Active-boundary v2 does not solve the proof/utility conflict.

It preserves the M267/M264 and M183/M170 first replay surfaces, but it still
fails the compact old-key gate at `10004`, and it retains less recovery utility
than M438 `r0015`. The v2 trajectory-window terms therefore behave like a
retention-heavy local residual rather than a mechanism that opens a new
proof-safe recovery direction.

This also confirms the M440 stop condition: another scalar/window active-boundary
residual is not the next high-leverage move. The branch is now bounded by the
old-key `10004` wrong-history safety constraint and by weak recovery utility,
not by missing implementation coverage.

## Decision

M442 is rejected:

- exact M297/M270/old-key surrogate objectives pass;
- M267/M264 and M183/M170 first replay gates pass;
- old-key compact replay fails `39 / 40` on `10004`;
- recovery retained vs M406 is `0.111895`, below M438 `r0015` `0.120957`;
- no checkpoint is promoted.

Admit:

```text
m443-active-boundary-v2-stop-audit
```

M443 should close the active-boundary v2 branch, classify the repeated
proof/utility bottleneck, and choose the next research direction without
running PPO or another scalar active-boundary sweep.
