# M379 Full Public Gate For M378 A005

M379 runs the full public promotion gate for the bounded M378 cumulative
gap-tail v2 repair candidate. It does not run PPO or change actor inputs.

## Candidate

Previous public-gate base:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Candidate:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

## Proof Sources

M378 already established:

| Gate | Result |
| --- | --- |
| Exact M297/M270 | pass |
| Cumulative old-key replay for alpha `0.05` | pass |
| Cumulative old-key alpha `0.1` | first tested gap-p10 failure |
| Source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |
| M267/M264 first replay | 17 / 17 pass |

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000107910 | +0.000057154 | true |
| M183/M170 | 17 | 17 / 17 | +0.000107188 | +0.000056053 | true |
| M193/M189 | 14 | 14 / 14 | +0.000072385 | +0.000058274 | true |
| M212/M204 | 17 | 17 / 17 | +0.000080945 | +0.000059772 | true |
| M223/M219 | 17 | 17 / 17 | +0.000080942 | +0.000059779 | true |
| M267/M264 | 17 | 17 / 17 | +0.000080887 | +0.000059786 | true |

Run root:

```text
runs/m379_full_public_gate_for_m378_a005/full_gates
```

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m375_base | 0.8625 | 0.1375 | 1.835477 | 65.949149 |
| 9505 | m378v2_a005 | 0.8625 | 0.1375 | 1.835458 | 65.949214 |
| 9505 | m378v2_a005_reset | 0.8500 | 0.1500 | 1.833767 | 64.053785 |
| 9505 | m378v2_a005_zero_all | 0.8000 | 0.2000 | 1.852620 | 61.066635 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m375_base | 0.8625 | 0.1375 | 1.852909 | 66.226178 |
| 9506 | m378v2_a005 | 0.8625 | 0.1375 | 1.852885 | 66.226296 |
| 9506 | m378v2_a005_reset | 0.8500 | 0.1500 | 1.850028 | 64.343829 |
| 9506 | m378v2_a005_zero_all | 0.8000 | 0.2000 | 1.870462 | 61.329951 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844171520
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M379 promotes `m378v2_a005` as the current public-gate base. This is another
bounded proof-safe step, not a large behavior improvement. The important result
is that the M377/M378 v2 gap-tail feedback recovered a small admissible
direction beyond M375 while preserving the cumulative old-key gate,
source-diverse protected surface, all six public replay surfaces, and public
behavior seeds.

The next blocker should audit the first failing tested alpha `0.1` toward the
M378 final repair endpoint. That audit should determine whether the new
boundary is still pure lower-tail gap erosion or whether accepted-regression
rows have reappeared.

## Decision

Promote:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

Decision:

```text
promote_m378_a005_gap_tail_v2_public_gate_base
```

Next:

```text
m380-m378-alpha01-cumulative-old-key-boundary-audit
```
