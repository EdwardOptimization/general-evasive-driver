# M443 Active-Boundary V2 Stop Audit

M443 closes the active-boundary v2 branch after M442. It does not run PPO,
promote a checkpoint, lower thresholds, or change the actor input/output
contract.

## Evidence Reviewed

| Milestone | Best proof-safe result | Recovery retained vs M406 | Binding failure |
| --- | --- | ---: | --- |
| M434 selective radius | `r0010` | `0.103529` | looser profiles fail old-key |
| M438 active-boundary v1 | `r0015` | `0.120957` | `tail_r0010` still fails old-key |
| M442 active-boundary v2 | none | `0.111895` | `tail_r0010` fails old-key `39 / 40` |

M427 remains the best recovery-utility diagnostic:

```text
recovery retained vs M406 = 0.174354
```

But M427 is not proof-safe because old-key compact falls to `36 / 40`.

## Binding Rows

The repeated active boundary is no longer a single stale key. It is a small
old-key family:

```text
10004 wrong-history safety
10023 margin-gap erosion
9998 wrong-history / spillover boundary
```

M442 narrows the immediate failure to:

```text
10004|perturbed|31|31
```

with:

```text
normal margin        = 0.001000
wrong-history margin = 0.000231
margin gap           = 0.000769
accepted             = false
```

That means the normal branch remains safe, but the wrong-history branch is too
safe. This is exactly the kind of proof row the project must protect for
self-identification evidence.

## Why The Branch Should Stop

The active-boundary branch tested three increasingly specific controls:

1. selective radius anchors;
2. v1 compact active-boundary residual;
3. v2 trajectory-window active-boundary residual with normal-safety rows.

The branch did improve over M430 and M434, but it did not open a new useful
direction:

- v1 can repair the first failing profile, `r0015`;
- v1 cannot make `tail_r0010` proof-safe;
- v2 also cannot make `tail_r0010` proof-safe;
- v2 retention is worse than M438 `r0015`;
- very high active-boundary pressure creates normal-branch collisions;
- exact residual movement is not a reliable closed-loop replay proxy.

Continuing with another scalar/window active-boundary sweep would mostly
optimize the same public old-key rows. That is poor evidence governance and
risks turning the loop into a gate-passing machine.

## Interpretation

The current public-gate base remains:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M438 `r0015` is the best proof-safe active-boundary diagnostic, not a promoted
base. M442 is rejected. M427 is the best high-utility diagnostic, but it is
proof-unsafe.

The important unresolved question is no longer "can one more active-boundary
residual repair `tail_r0010`?" The better question is:

```text
Do the proof-rejected high-recovery candidates actually improve broad
evasive-driving behavior on fresh scenarios, or are we optimizing a narrow
recovery surrogate that does not matter outside the old-key proof surface?
```

If proof-rejected high-utility candidates improve broad scenario success or
margin, then the old-key proof/gate stack needs a better distributional
interpretation before further repair. If they do not, then the M406 recovery
target is not worth more local objective design.

## Decision

M443 passes as a process audit:

- active-boundary v2 is stopped;
- no checkpoint is promoted;
- no PPO is admitted;
- no actor input/output contract changes are made;
- the next milestone must not be another active-boundary scalar sweep.

Admit:

```text
m444-proof-utility-generalization-audit
```

M444 should run a non-promotion benchmark comparing the current base,
proof-safe active-boundary candidates, and proof-rejected high-utility
candidates on a fresh randomized scenario distribution. Its purpose is to
measure whether the local proof/utility conflict corresponds to real driver
performance, not to select a new base.
