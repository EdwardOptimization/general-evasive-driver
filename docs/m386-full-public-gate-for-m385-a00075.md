# M386 Full Public Gate For M385 A00075

M386 runs the full public promotion gate for the M385 micro-alpha candidate. It
does not run PPO, lower thresholds, or change the actor input/output contract.

## Candidate

Previous public-gate base:

```text
runs/m378_v2_gap_tail_final_interpolation/checkpoints/alpha_0_05.pt
```

Candidate:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

## Proof Sources

M385 already established:

| Gate | Result |
| --- | --- |
| exact M297/M270 | pass |
| cumulative old-key replay | pass |
| source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |
| M267/M264 first replay | 17 / 17 pass |

The direct M385 repair endpoint and ordinary alphas remain rejected. Alpha
`0.001` is the first tested M267/M264 knife-edge failure.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

Run root:

```text
runs/m386_full_public_gate_for_m385_a00075/full_gates
```

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000122711 | +0.000056342 | true |
| M183/M170 | 17 | 17 / 17 | +0.000122153 | +0.000055249 | true |
| M193/M189 | 14 | 14 / 14 | +0.000087161 | +0.000057265 | true |
| M212/M204 | 17 | 17 / 17 | +0.000095406 | +0.000058787 | true |
| M223/M219 | 17 | 17 / 17 | +0.000095403 | +0.000058792 | true |
| M267/M264 | 17 | 17 / 17 | +0.000095346 | +0.000058800 | true |

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m378v2_a005 | 0.8625 | 0.1375 | 1.835458 | 65.949214 |
| 9505 | m385micro_a0_00075 | 0.8625 | 0.1375 | 1.835470 | 65.949080 |
| 9505 | m385micro_a0_00075_reset | 0.8500 | 0.1500 | 1.833771 | 64.053736 |
| 9505 | m385micro_a0_00075_zero_all | 0.8000 | 0.2000 | 1.852625 | 61.066574 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m378v2_a005 | 0.8625 | 0.1375 | 1.852885 | 66.226296 |
| 9506 | m385micro_a0_00075 | 0.8625 | 0.1375 | 1.852898 | 66.226158 |
| 9506 | m385micro_a0_00075_reset | 0.8500 | 0.1500 | 1.850032 | 64.343779 |
| 9506 | m385micro_a0_00075_zero_all | 0.8000 | 0.2000 | 1.870467 | 61.329887 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844183791
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M386 promotes the M385 micro-alpha candidate as the new public-gate base. This
is a proof-safe micro promotion. It preserves exact, cumulative old-key,
source-diverse, public replay, and behavior gates, but the admissible step is
very small because M267/M264 row `15` flips at alpha `0.001`.

The next blocker should audit whether this micro promotion is meaningful enough
to chain more repair or PPO. Given the accepted alpha is only `0.00075`, the
likely answer is that M386 is mostly retention progress, not driver-performance
progress.

## Decision

Promote:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

Decision:

```text
promote_m385_micro_a00075_public_gate_base
```

Next:

```text
m387-m386-micro-promotion-utility-audit
```
