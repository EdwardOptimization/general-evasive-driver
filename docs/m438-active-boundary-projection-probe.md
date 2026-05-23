# M438 Active-Boundary Projection Probe

M438 tests whether the M437 active-boundary residual can improve the no-PPO
projection beyond M434 `r0010` while preserving current-family and old-key
closed-loop proof gates. No PPO was run, no checkpoint was promoted, no
thresholds were lowered, and actor inputs/outputs were unchanged.

## Probe Setup

Base checkpoint:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Raw recovery checkpoint:

```text
runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
```

Active-boundary residual:

```text
runs/m437_active_boundary_residual/active_boundary_corpus.npz
```

The main positive candidate is:

```text
runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt
```

It uses the M433 `r0015` selective anchor plus:

```text
lambda_active_boundary = 1e12
steps = 40
learning_rate = 2e-6
project_recovery_gradient = true
```

## Projection Results

| Candidate | Exact pass | Old-key compact | M267/M264 | M183/M170 | Recovery retained vs M406 | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| M434 `r0010` baseline | true | `40 / 40` | `17 / 17` | `17 / 17` | `0.103529` | prior best proof-safe |
| M438 `r0015`, active `1e12` | true | `40 / 40` | `17 / 17` | `17 / 17` | `0.120957` | partial pass |
| M438 `tail_r0010`, active `1e12` | true | `38 / 40` | `17 / 17` | not run | `0.146932` | reject, old-key fails |
| M438 `tail_r0010`, active `1e14` | true | `34 / 40` | not run | not run | `-0.027594` | reject, too strong |

The `r0015` active-boundary candidate improves over M434 `r0010` while
preserving the required proof gates, but it remains below M427
(`0.174354`) and below the primary `0.20` recovery-retention target.

## Exact Metrics

For the selected `r0015` candidate:

| Metric | Value |
| --- | ---: |
| selected step | `38` |
| exact M297 delta vs base | `-0.000058293` |
| exact M270 delta vs base | `-0.000120997` |
| old-key surrogate delta vs base | `-0.000015259` |
| active_boundary_loss | `0.0010130818` |
| active_boundary_wrong_loss | `0.0005824725` |
| active_boundary_gap_loss | `0.0004306092` |
| active_boundary_normal_loss | `0.0` |
| replay trajectory anchor loss | `5.152192e-09` |
| exact lexicographic pass | `true` |

The active-boundary loss is slightly lower than the M399 no-update value
(`0.0010130878`), so it does not regress the M437 exact residual.

## Closed-Loop Gates

M267/M264 first replay:

```text
runs/m438_r0015_lactive1e12_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| normal success | `1.0` |
| wrong-history success | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000433` |
| margin gap mean delta | `-0.000155` |
| gate pass | `true` |

Old-key compact replay:

```text
runs/m438_r0015_lactive1e12_old_key_targeted_replay
runs/m438_r0015_lactive1e12_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| accepted cases | `40 / 40` |
| normal-success cases | `40 / 40` |
| margin gap mean | `0.008427` |
| margin gap min | `0.000790` |
| old-key replay gate | `true` |

Previously active boundary rows are now accepted:

| Key | Normal margin | Wrong-history margin | Margin gap | Accepted |
| --- | ---: | ---: | ---: | --- |
| `10004|perturbed|31|31` | `0.000613` | `-0.000177` | `0.000790` | true |
| `10023|perturbed|12|12` | `0.048695` | `0.046694` | `0.002001` | true |
| `9998|perturbed|25|25` | `0.001093` | `-0.000515` | `0.001608` | true |

M183/M170 first replay:

```text
runs/m438_r0015_lactive1e12_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| normal success | `1.0` |
| wrong-history success | `0.0` |
| success drops | `17 / 17` |
| normal margin mean delta | `-0.000470` |
| margin gap mean delta | `-0.000204` |
| gate pass | `true` |

## Negative Probes

`tail_r0010` with active `1e12` preserves M267/M264 but fails old-key compact
at two rows:

```text
10004|perturbed|31|31
10023|perturbed|12|12
```

This shows the residual helps, but does not yet protect the looser tail-only
trajectory profile.

Increasing active-boundary pressure to `1e14` is not a solution. It lowers the
exact active-boundary loss slightly, but collapses recovery utility and turns
old-key failures into normal-branch collisions:

```text
accepted cases: 34 / 40
normal-success cases: 34 / 40
```

## Interpretation

The M437 residual is useful but not sufficient as the final proof/utility
mechanism.

It can move the boundary from M434 `r0010` to a stronger proof-safe `r0015`
candidate, improving recovery retained vs M406 from `0.103529` to `0.120957`.
That is real progress because `r0015` was the first failing M434 profile.

However, the residual still does not make the higher-utility `tail_r0010`
profile proof-safe, and excessive active-boundary weight damages normal-branch
safety. The next step should audit the active-boundary residual's row-level
action and gradient alignment before adding another scalar weight sweep.

## Decision

M438 is a partial pass:

- proof gates pass for the `r0015` active-boundary candidate;
- recovery retained improves over M434 `r0010`;
- the candidate remains below M427 and below the `0.20` primary utility target;
- no checkpoint is promoted.

Admit:

```text
m439-active-boundary-residual-utility-audit
```

M439 should classify why `r0015` is repairable but `tail_r0010` is not, and
whether the active-boundary objective needs row-specific weighting, a margin
residual, or a different branch-separation term before another projection.
