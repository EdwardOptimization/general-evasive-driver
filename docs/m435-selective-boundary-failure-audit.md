# M435 Selective Boundary Failure Audit

M435 audits the active boundary exposed by M434. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Boundary Sequence

M434 shows a clean radius/utility tradeoff:

| Profile | Recovery retained vs M406 | Old-key accepted | Boundary |
| --- | ---: | ---: | --- |
| `r0005` | `0.076823` | `40 / 40` | proof-safe, low utility |
| `r0010` | `0.103529` | `40 / 40` | best proof-safe profile |
| `r0015` | `0.119585` | `39 / 40` | `10023` gap erosion |
| `r0020` | `0.143915` | `38 / 40` | `10004`, `10023` |
| `tail_r0005` | `0.132169` | `38 / 40` | `10004`, `10023` |
| `tail_r0010` | `0.145627` | `37 / 40` | `10004`, `10023`, `9998` |

`r0010` passes:

- exact M297/M270/old-key no-regression;
- M267/M264 `17 / 17`;
- old-key compact `40 / 40`;
- old-key replay gate;
- M183/M170 `17 / 17`.

But `r0010` only retains `0.103529` of M406 recovery utility. That is above
M430 (`0.061702`) but below M427 (`0.174354`) and below the primary target
`0.20`.

## Failure Rows

First failing rows:

| Profile | Failed row | Normal margin | Wrong-history margin | Interpretation |
| --- | --- | ---: | ---: | --- |
| `r0015` | `10023|perturbed|12|12` | `0.048741066` | `0.046745305` | gap erosion after `10004` is relaxed |
| `r0020` | `10004|perturbed|31|31` | `0.001001260` | `0.000227536` | wrong-history becomes safe |
| `r0020` | `10023|perturbed|12|12` | `0.048739995` | `0.046754238` | gap erosion |
| `tail_r0005` | `10004|perturbed|31|31` | `0.000889123` | `0.000097324` | terminal-only guard is insufficient |
| `tail_r0005` | `10023|perturbed|12|12` | `0.048749559` | `0.046758650` | gap erosion |
| `tail_r0010` | `10004|perturbed|31|31` | `0.001036309` | `0.000254452` | wrong-history becomes safe |
| `tail_r0010` | `10023|perturbed|12|12` | `0.048712638` | `0.046730096` | gap erosion |
| `tail_r0010` | `9998|perturbed|25|25` | `0.001615405` | `0.000028410` | spillover wrong-history near zero |

The active boundary is not just `10004`. Once `10004` is relaxed enough to gain
utility, `10023` becomes the next limiting row. If the guard is made terminal
only, `10004` reopens and `9998` appears as a spillover.

## Interpretation

The radius-family path is now bounded:

- `10004` all-row radius `0.0010` is the largest tested proof-safe relaxation.
- `0.0015` improves utility only slightly and immediately fails `10023`.
- Tail-only profiles increase retained gradient ratio, but they do not preserve
  wrong-history proof on `10004`; they also expose `9998`.

This means more scalar radius tuning is unlikely to reach the `0.20` utility
target. The problem is no longer one source being too hard. It is a small
multi-key old-key boundary where action anchoring is the wrong residual shape.

## Recommendation

Next design should move from full-trajectory action radii to an outcome-aware
training residual for active old-key rows:

- keep exact M297/M270/old-key no-regression as first-class gates;
- keep M267/M264, old-key compact, and M183/M170 as closed-loop gates;
- build a compact active-boundary corpus around `10004`, `10023`, and `9998`;
- encode branch intent with rejected-history preference or terminal-margin
  slack, not full-trajectory action imitation;
- only anchor the minimum local action slices needed to preserve wrong-history
  failure and normal-branch safety.

This should be designed before another projection or any PPO.

## Decision

Admit:

```text
m436-old-key-active-boundary-residual-design
```

M436 should design the active-boundary residual and pre-register the next
implementation. It should not train or promote a checkpoint.
