# M401 M400 Bounded-Promotion Utility Audit

M401 audits whether the M400 promotion is useful enough to chain another repair
or PPO step. It does not run PPO, promote a checkpoint, lower thresholds, or
change actor inputs.

## Current Base

M400 promoted:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

This candidate passed:

```text
six public replay surfaces
cumulative old-key compact replay
M267/M264 first replay
M183/M170 first replay
source-diverse protected gate
behavior seeds 9505 and 9506
```

## Utility

M400 is another proof-safe bounded promotion, not a meaningful
driver-performance improvement.

Versus the previous public base:

| Metric | Delta |
| --- | ---: |
| behavior success | 0.0 |
| behavior termination | 0.0 |
| mean clearance margin | -0.000049633 |
| mean return | +0.000928436 |

Exact/proof movement from the selected M399 alpha `0.05` is also small:

| Metric | Delta / value |
| --- | ---: |
| exact M297 delta | -0.000028372 |
| exact M270 delta | -0.000016451 |
| old-key surrogate delta | -0.000047207 |
| old-key recovery loss | 0.003873642 |
| current-family conflict loss | 0.001538875 |

This is useful only as a slightly improved proof-safe base. It is not evidence
that the driver policy became materially better.

## First Known Boundary

The first known post-M400 boundary remains the M399 interpolation alpha `0.10`
toward the same s02 repair endpoint:

```text
runs/m399_s02a100_old_key_replay_gate
```

Failing case:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

At alpha `0.10`:

| Normal margin | Wrong-history margin | Gap delta | Accepted regression | Normal-success regression |
| ---: | ---: | ---: | --- | --- |
| -0.000085 | -0.002228 | +0.000002 | true | true |

This is still a normal-branch terminal-margin cliff. It is not wrong-history
sensitivity loss, because the wrong-history branch remains collision-side and
the gap does not erode.

## Decision

Do not go directly to PPO. The next task should audit whether the M398
normal-margin recovery residual is aligned with closed-loop old-key replay near
the `9958` boundary. In particular, it should determine whether the limiting
factor is:

```text
target action selection
recovery residual weight
conflict with old-key/current-family anchors
closed-loop trajectory drift not represented by the one-step residual
```

Admit:

```text
m402-old-key-normal-recovery-alignment-audit
```
