# M392 M391 Micro-Promotion Utility Audit

M392 audits whether the M391 public-gate promotion is useful enough to chain
another repair or PPO step. It does not run PPO, promote another checkpoint,
lower thresholds, or change actor inputs.

## Inputs

Current public-gate base:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

Previous public-gate base:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

## Utility Metrics

M391 is proof-safe, but the accepted movement is small.

| Metric | Delta vs previous public base |
| --- | ---: |
| exact M297 | -0.000001192 |
| exact M270 | -0.000000298 |
| old-key surrogate | -0.000006199 |
| behavior success mean | +0.000000000 |
| behavior termination mean | +0.000000000 |
| behavior clearance margin mean | +0.000008543 |

Behavior remains effectively unchanged:

| Metric | Value |
| --- | ---: |
| success mean | 0.8625 |
| termination mean | 0.1375 |
| clearance margin mean | 1.844192334 |
| reset success mean | 0.85 |
| zero-all success mean | 0.80 |

## Active Boundary

The limiting surface remains M267/M264 row `15`.

| Candidate | Row15 wrong-history margin | Wrong-history success |
| --- | ---: | --- |
| M386 base | -0.000001064 | false |
| M391 base, alpha 0.005 | -0.000000469 | false |
| alpha 0.010 toward step17 | +0.000000131 | true |
| step17 endpoint | +0.000119062 | true |

M391 moved in the right exact-objective direction but consumed most of the
remaining row15 wrong-history collision slack. The selected alpha `0.005` is
not a meaningful driver-performance improvement; it is another proof-safe
micro-step.

## Interpretation

The M389 conflict residual used the current base wrong-history action as the
rejected-branch boundary action. That action is itself a near-cliff action:
under M391 it only keeps row15 at about `-4.7e-7` clearance margin. Anchoring to
that action cannot create margin slack; it only slows the drift toward
wrong-history success.

The next useful control variable is therefore not PPO length and not another
ordinary interpolation. The rejected branch needs a better target:

```text
wrong-history local action that remains on the collision side with more slack
```

This mirrors the old-key local recovery-target export, but for the current
family rejected-history branch. The target is training-only and must not enter
the actor observation.

## Decision

Classify:

```text
proof_safe_micro_retention_not_meaningful_driver_improvement
```

Admit:

```text
m393-current-family-rejected-boundary-target-export
```

Decision:

```text
admit_m393_current_family_rejected_boundary_target_export
```
