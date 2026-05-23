# M387 M386 Micro-Promotion Utility Audit

M387 audits whether the M386 promoted checkpoint is useful enough to chain more
repair or PPO. It does not train, promote another checkpoint, lower thresholds,
or change actor inputs.

## Inputs

New public-gate base:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

Previous public-gate base:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

Audit artifact:

```text
runs/m387_m386_micro_promotion_utility_audit/summary.json
```

## Utility Metrics

M386 is proof-safe, but the accepted movement is very small.

| Metric | Value |
| --- | ---: |
| selected alpha toward M385 repair endpoint | 0.00075 |
| first tested M267/M264 failure alpha | 0.001 |
| first tested cumulative old-key failure alpha | 0.02 |
| exact M297 delta vs previous base | -0.000011206 |
| exact M270 delta vs previous base | -0.000006974 |
| old-key surrogate delta vs previous base | -0.000010490 |
| old-key recovery loss delta vs previous base | -0.000001519 |

Behavior is unchanged at the public-gate scale:

| Metric | Value |
| --- | ---: |
| success mean | 0.8625 |
| termination mean | 0.1375 |
| clearance margin mean | 1.844183791 |
| reset success mean | 0.85 |
| zero-all success mean | 0.80 |

The selected checkpoint is only `75%` of the way to the first tested
M267/M264 failure alpha. It is not a meaningful driver-performance improvement.

## Active Boundary

The limiting row is M267/M264 row `15`:

```text
runs/m387_m386_micro_promotion_utility_audit/m267_row15_alpha_trace.csv
```

| Alpha | Wrong-history margin | Wrong-history success |
| ---: | ---: | --- |
| 0.00000 | -0.000015570 | false |
| 0.00075 | -0.000001064 | false |
| 0.00100 | +0.000003801 | true |
| 0.00250 | +0.000033 | true |
| 0.00500 | +0.000081 | true |
| 0.01000 | +0.000178 | true |

The old-key recovery residual improves exact objectives and can protect
cumulative old-key rows, but it also nudges current-family wrong-history row
`15` across the collision boundary. That means the next blocker is not another
old-key overlay and not PPO length. It is a cross-surface conflict: old-key
normal-margin recovery versus current-family wrong-history failure retention.

## Interpretation

M386 should be kept as the public-gate base because it passed the full
promotion gate. But it should not be used as evidence that the recovery
residual solved the broader training problem. The useful conclusion is more
specific:

- direct recovery repair has useful exact signal but large proof washout;
- cumulative old-key replay alone is too permissive for this direction;
- M267/M264 row `15` is now the binding active constraint;
- future repair needs an explicit current-family wrong-history boundary term
  before more repair or PPO.

## Decision

Classify:

```text
proof_safe_micro_retention_not_meaningful_driver_improvement
```

Admit:

```text
m388-m267-row15-conflict-residual-design
```

Decision:

```text
admit_m388_m267_row15_conflict_residual_design
```
