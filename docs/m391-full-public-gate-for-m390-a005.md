# M391 Full Public Gate For M390 A005

M391 runs the full public promotion gate for the M390 alpha `0.005` bounded
repair candidate. It does not run PPO, lower thresholds, or change the actor
input/output contract.

## Candidate

Previous public-gate base:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

Candidate:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

## Proof Sources

M390 already established:

| Gate | Result |
| --- | --- |
| exact M297/M270 | pass |
| M267/M264 first replay | 17 / 17 pass |
| cumulative old-key replay | pass |
| source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |

The step17 endpoint remains rejected, and interpolation alpha `0.01` remains
the first tested M267/M264 failure. M391 only tests alpha `0.005` for
promotion.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

Run root:

```text
runs/m391_full_public_gate_for_m390_a005/full_gates
```

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000123541 | +0.000056219 | true |
| M183/M170 | 17 | 17 / 17 | +0.000122972 | +0.000055120 | true |
| M193/M189 | 14 | 14 / 14 | +0.000088186 | +0.000057302 | true |
| M212/M204 | 17 | 17 / 17 | +0.000096250 | +0.000058795 | true |
| M223/M219 | 17 | 17 / 17 | +0.000096249 | +0.000058798 | true |
| M267/M264 | 17 | 17 / 17 | +0.000096197 | +0.000058811 | true |

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m385micro_a0_00075 | 0.8625 | 0.1375 | 1.835470 | 65.949080 |
| 9505 | m390step17_a005 | 0.8625 | 0.1375 | 1.835478 | 65.948934 |
| 9505 | m390step17_a005_reset | 0.8500 | 0.1500 | 1.833776 | 64.053703 |
| 9505 | m390step17_a005_zero_all | 0.8000 | 0.2000 | 1.852631 | 61.066534 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m385micro_a0_00075 | 0.8625 | 0.1375 | 1.852898 | 66.226158 |
| 9506 | m390step17_a005 | 0.8625 | 0.1375 | 1.852907 | 66.226002 |
| 9506 | m390step17_a005_reset | 0.8500 | 0.1500 | 1.850037 | 64.343744 |
| 9506 | m390step17_a005_zero_all | 0.8000 | 0.2000 | 1.870475 | 61.329841 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844192334
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M391 promotes the M390 alpha `0.005` candidate as the new public-gate base. It
preserves exact, M267/M264, cumulative old-key, source-diverse, full replay,
and behavior gates. The movement is still small: M390 alpha `0.01` is already a
known M267/M264 row15 failure, so the next step should audit whether this
promotion is meaningful enough to chain or whether another active-boundary
objective redesign is needed.

## Decision

Promote:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

Decision:

```text
promote_m390_step17_a005_public_gate_base
```

Next:

```text
m392-m391-micro-promotion-utility-audit
```
