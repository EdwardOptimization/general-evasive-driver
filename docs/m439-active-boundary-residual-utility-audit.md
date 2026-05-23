# M439 Active-Boundary Residual Utility Audit

M439 audits the M438 active-boundary projection results. It does not run PPO,
promote a checkpoint, lower thresholds, or change actor inputs.

Audit artifacts:

```text
runs/m439_active_boundary_residual_utility_audit/policy_utility_summary.csv
runs/m439_active_boundary_residual_utility_audit/active_case_rows.csv
runs/m439_active_boundary_residual_utility_audit/summary.json
```

## Summary

| Policy | Old-key accepted | Normal-success cases | Recovery retained vs M406 | Active-boundary loss | Failed keys |
| --- | ---: | ---: | ---: | ---: | --- |
| M434 `r0010` | `40 / 40` | `40 / 40` | `0.103529` | n/a | none |
| M434 `r0015` | `39 / 40` | `40 / 40` | `0.119585` | n/a | `10023` |
| M434 `tail_r0010` | `37 / 40` | `40 / 40` | `0.145627` | n/a | `10004`, `10023`, `9998` |
| M438 `r0015`, active `1e12` | `40 / 40` | `40 / 40` | `0.120957` | `0.0010130818` | none |
| M438 `tail_r0010`, active `1e12` | `38 / 40` | `40 / 40` | `0.146932` | `0.0010130885` | `10004`, `10023` |
| M438 `tail_r0010`, active `1e14` | `34 / 40` | `34 / 40` | `-0.027594` | `0.0010128634` | normal collisions |

The active-boundary residual is useful but not sufficient:

- it turns M434 `r0015` from old-key `39 / 40` into `40 / 40`;
- it improves recovery retained vs M406 from M434 `r0010` `0.103529` to
  `0.120957`;
- it does not make `tail_r0010` proof-safe;
- a very high scalar weight reduces active-boundary loss but creates
  normal-branch collisions.

## Why `r0015` Is Repairable

M434 `r0015` was already close. It failed only `10023` gap erosion:

```text
10023 margin_gap: 0.001995761
reference gap:    0.002062268
```

M438 `r0015` active `1e12` moves that row to:

```text
10023 margin_gap: 0.002000734
accepted:         true
```

The improvement is small, but enough under the compact old-key gate because
the rest of the branch remains protected by the all-row `r0015` anchor.

The same candidate keeps the other active cases accepted:

| Key | Normal margin | Wrong-history margin | Margin gap | Accepted |
| --- | ---: | ---: | ---: | --- |
| `10004|perturbed|31|31` | `0.000613` | `-0.000177` | `0.000790` | true |
| `10023|perturbed|12|12` | `0.048695` | `0.046694` | `0.002001` | true |
| `9998|perturbed|25|25` | `0.001093` | `-0.000515` | `0.001608` | true |

## Why `tail_r0010` Still Fails

`tail_r0010` removes too much non-terminal protection on `10004`. With active
lambda `1e12`, it still fails:

| Key | Normal margin | Wrong-history margin | Margin gap | Failure |
| --- | ---: | ---: | ---: | --- |
| `10004|perturbed|31|31` | `0.000929` | `0.000143` | `0.000786` | wrong-history becomes safe |
| `10023|perturbed|12|12` | `0.048590` | `0.046605` | `0.001985` | gap erosion |

The exact active-boundary loss barely changes between M438 `r0015` and
`tail_r0010`:

```text
r0015 active loss:      0.0010130818
tail_r0010 active loss: 0.0010130885
```

That means the scalar one-step active-boundary loss is too weak as a standalone
closed-loop proof proxy. It can nudge a near-pass row, but it does not encode
enough trajectory or margin slack to protect the looser tail-only profile.

## Why Higher Weight Is Not Enough

`tail_r0010` with active lambda `1e14` lowers the exact active-boundary loss to
`0.0010128634`, but old-key compact falls to `34 / 40`, with only `34 / 40`
normal-success cases. It fixes neither the research problem nor the driver.

The failure mode shifts from wrong-history safety/gap erosion to normal-branch
collisions. Examples:

| Key | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: |
| `10004|perturbed|31|31` | `-0.001788` | `-0.002613` | `0.000825` |
| `9998|perturbed|25|25` | `-0.001704` | `-0.003376` | `0.001672` |

This is important: an exact residual can improve while closed-loop safety
gets worse. The closed-loop replay gates remain authoritative.

## Interpretation

The M437 residual has the right direction but the wrong granularity for the
next jump.

It is good enough to make the first failing radius profile (`r0015`) proof-safe.
It is not good enough to protect the higher-utility `tail_r0010` profile,
because it uses one compact active-boundary row per failure rather than a
trajectory-window or margin-slack representation of the active cases.

The active-boundary exact loss also cannot be used as a scalar promotion gate:

- `r0015` passes with a tiny active-loss improvement;
- `tail_r0010` fails with almost the same active loss;
- `1e14` improves active loss more, but creates normal-branch collisions.

## Recommendation

Admit an active-boundary v2 design milestone before another projection.

The v2 residual should be more specific, not just stronger:

1. Add compact trajectory-window snippets for the active cases `10004`,
   `10023`, and `9998`, especially the pre-terminal steps where `tail_r0010`
   lost protection.
2. Add row-specific branches:
   - `10004` and `9998`: wrong-history collision-side preference plus a small
     normal-branch safety/slack anchor;
   - `10023`: gap-floor or branch-separation residual calibrated to margin-gap
     erosion, not only one-step action logprob.
3. Include a normal-safety guard whenever active-boundary weight is high, so
   the residual cannot repair wrong-history proof by sacrificing normal success.
4. Keep M267/M264, old-key compact, and M183/M170 closed-loop replay gates as
   the final authority.

Do not run PPO yet. Do not promote M438. Do not do another scalar weight sweep
without row-level evidence.

## Decision

M439 classifies M438 as useful partial progress and admits:

```text
m440-active-boundary-v2-residual-design
```

The next design should specify whether active-boundary v2 is still worth
implementing, or whether the project should stop this proof/utility branch and
return to a broader objective.
