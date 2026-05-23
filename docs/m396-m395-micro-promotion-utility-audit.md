# M396 M395 Micro-Promotion Utility Audit

M396 audits whether the M395 public-gate promotion is useful enough to chain
another repair or PPO step. It does not run PPO, promote another checkpoint,
lower thresholds, or change actor inputs.

## Inputs

Current public-gate base:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

Previous public-gate base:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

## Utility Metrics

M395 is proof-safe, but the accepted movement is still small.

| Metric | Delta vs previous public base |
| --- | ---: |
| exact M297 | -0.000048637 |
| exact M270 | -0.000028133 |
| old-key surrogate | -0.000130653 |
| current-family conflict loss | -0.000017316 |
| behavior success mean | +0.000000000 |
| behavior termination mean | +0.000000000 |
| behavior clearance margin mean | -0.000102931 |

Behavior remains effectively unchanged:

| Metric | Value |
| --- | ---: |
| success mean | 0.8625 |
| termination mean | 0.1375 |
| clearance margin mean | 1.844089403 |
| reset success mean | 0.85 |
| zero-all success mean | 0.80 |

## Active Boundary

The limiting surface has shifted from M267/M264 row15 to a cumulative old-key
compact case:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

The first known failing candidate is the next tested interpolation,
`s02 alpha 0.2`:

```text
runs/m396_s02a020_old_key_replay_gate
```

| Candidate | Accepted rows | Failing case normal margin | Failing case wrong-history margin | Failure |
| --- | ---: | ---: | ---: | --- |
| M395 selected, alpha 0.1 | 40 / 40 | +0.000086 | -0.002055 | none |
| alpha 0.2 | 39 / 40 | -0.000089 | -0.002232 | normal-branch collision |

The margin gap does not collapse on the failing row. The problem is normal
branch terminal-margin sign crossing on one compact old-key case, not loss of
wrong-history sensitivity.

## Interpretation

M395 should be treated as another proof-safe bounded promotion, not a
meaningful driver-performance improvement. The M393/M394 repair direction is
useful, but the admissible region is clipped by old-key normal-branch slack.

The next useful task is not PPO. It is a focused audit of the alpha `0.2`
old-key boundary, to determine whether the row is a stale singleton, a
representative old-key normal-margin cliff, or a target for another
training-only local recovery residual.

## Decision

Classify:

```text
proof_safe_bounded_promotion_not_meaningful_driver_improvement
```

Admit:

```text
m397-m395-alpha02-old-key-boundary-audit
```

Decision:

```text
admit_m397_m395_alpha02_old_key_boundary_audit
```
