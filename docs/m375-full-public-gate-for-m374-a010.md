# M375 Full Public Gate For M374 A010

M375 runs the full public promotion gate for the bounded M374 gap-tail weighted
repair candidate. It does not run PPO or change actor inputs.

## Candidate

Previous public-gate base:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

Candidate:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

## Proof Sources

M374 already established:

| Gate | Result |
| --- | --- |
| Exact M297/M270 | pass |
| Cumulative old-key replay for alpha `0.1` | pass |
| Cumulative old-key alpha `0.2` | first tested gap-p10 failure |
| Source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |
| M267/M264 first replay | 17 / 17 pass |

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000097677 | +0.000053718 | true |
| M183/M170 | 17 | 17 / 17 | +0.000096974 | +0.000052692 | true |
| M193/M189 | 14 | 14 / 14 | +0.000064518 | +0.000055133 | true |
| M212/M204 | 17 | 17 / 17 | +0.000072565 | +0.000056513 | true |
| M223/M219 | 17 | 17 / 17 | +0.000072563 | +0.000056517 | true |
| M267/M264 | 17 | 17 / 17 | +0.000072511 | +0.000056522 | true |

Run root:

```text
runs/m375_full_public_gate_for_m374_a010/full_gates
```

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m370_base | 0.8625 | 0.1375 | 1.835518 | 65.948742 |
| 9505 | m374gt_a010 | 0.8625 | 0.1375 | 1.835477 | 65.949149 |
| 9505 | m374gt_a010_reset | 0.8500 | 0.1500 | 1.833815 | 64.053762 |
| 9505 | m374gt_a010_zero_all | 0.8000 | 0.2000 | 1.852648 | 61.066707 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m370_base | 0.8625 | 0.1375 | 1.852959 | 66.225656 |
| 9506 | m374gt_a010 | 0.8625 | 0.1375 | 1.852909 | 66.226178 |
| 9506 | m374gt_a010_reset | 0.8500 | 0.1500 | 1.850077 | 64.343794 |
| 9506 | m374gt_a010_zero_all | 0.8000 | 0.2000 | 1.870493 | 61.329986 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844192756
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M375 promotes `m374gt_a010` as the current public-gate base. This is a bounded
proof-safe step from the M370 base, not a large behavior improvement. The
important result is that M373/M374 gap-tail feedback found a small admissible
direction beyond M370 while preserving the cumulative old-key gate, the
source-diverse protected surface, all six public replay surfaces, and public
behavior seeds.

The next blocker should audit the first failing tested alpha `0.2` toward the
M374 final repair endpoint. That audit should determine whether the new
boundary is still pure lower-tail gap erosion or whether accepted-regression
rows have reappeared.

## Decision

Promote:

```text
runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
```

Decision:

```text
promote_m374_a010_gap_tail_weighted_public_gate_base
```

Next:

```text
m376-m374-alpha02-cumulative-old-key-boundary-audit
```
