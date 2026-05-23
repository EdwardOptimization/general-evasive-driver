# M395 Full Public Gate For M394 S02A010

M395 runs the full public promotion gate for the bounded M394 candidate. It
does not run PPO, lower thresholds, or change the actor input/output contract.

## Candidate

Previous public-gate base:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

Candidate:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

## Proof Sources

M394 already established:

| Gate | Result |
| --- | --- |
| exact M297/M270 | pass |
| M267/M264 first replay | 17 / 17 pass |
| cumulative old-key compact replay | pass |
| source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |

The direct repair endpoints remain rejected. The selected candidate is only the
bounded `alpha=0.1` interpolation toward the step2 repair direction.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

Run root:

```text
runs/m395_full_public_gate_for_m394_s02a010/full_gates
```

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | -0.000009384 | +0.000058467 | true |
| M183/M170 | 17 | 17 / 17 | -0.000010597 | +0.000057336 | true |
| M193/M189 | 14 | 14 / 14 | -0.000037582 | +0.000059422 | true |
| M212/M204 | 17 | 17 / 17 | -0.000029631 | +0.000060972 | true |
| M223/M219 | 17 | 17 / 17 | -0.000029636 | +0.000060976 | true |
| M267/M264 | 17 | 17 / 17 | -0.000029664 | +0.000060982 | true |

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m391_base | 0.8625 | 0.1375 | 1.835478 | 65.948934 |
| 9505 | s02a010 | 0.8625 | 0.1375 | 1.835377 | 65.948641 |
| 9505 | s02a010_reset | 0.8500 | 0.1500 | 1.833733 | 64.054139 |
| 9505 | s02a010_zero_all | 0.8000 | 0.2000 | 1.852592 | 61.067006 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m391_base | 0.8625 | 0.1375 | 1.852907 | 66.226002 |
| 9506 | s02a010 | 0.8625 | 0.1375 | 1.852802 | 66.225763 |
| 9506 | s02a010_reset | 0.8500 | 0.1500 | 1.849993 | 64.344192 |
| 9506 | s02a010_zero_all | 0.8000 | 0.2000 | 1.870433 | 61.330341 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844089403
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M395 promotes the M394 `s02 alpha 0.1` candidate as the new public-gate base.
It preserves exact, M267/M264, cumulative old-key, source-diverse, full replay,
and behavior gates.

This remains a proof-safe bounded repair, not yet a meaningful
driver-performance improvement. The next step should audit whether the move is
large enough to chain another repair or PPO step, and identify the next active
boundary.

## Decision

Promote:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

Decision:

```text
promote_m394_s02a010_public_gate_base
```

Next:

```text
m396-m395-micro-promotion-utility-audit
```
