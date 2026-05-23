# M400 Full Public Gate For M399 S02A050

M400 runs the full public promotion gate for the bounded M399 alpha `0.05`
candidate. It does not run PPO, lower thresholds, or change the actor
input/output contract.

## Candidate

Previous public-gate base:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

Candidate:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

## Proof Sources

M399 already established:

| Gate | Result |
| --- | --- |
| exact M297/M270/old-key | pass |
| cumulative old-key compact replay | pass |
| M267/M264 first replay | 17 / 17 pass |
| M183/M170 first replay | 17 / 17 pass |
| source-diverse protected gate | 5 / 5 pass |

The alpha `0.10` interpolation remains rejected because it first fails old-key
case `9958|perturbed|39|36`.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

Run root:

```text
runs/m400_full_public_gate_for_m399_s02a050/full_gates
```

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | -0.000074 | +0.000060 | true |
| M183/M170 | 17 | 17 / 17 | -0.000075 | +0.000058 | true |
| M193/M189 | 14 | 14 / 14 | -0.000098 | +0.000060 | true |
| M212/M204 | 17 | 17 / 17 | -0.000090 | +0.000062 | true |
| M223/M219 | 17 | 17 / 17 | -0.000090 | +0.000062 | true |
| M267/M264 | 17 | 17 / 17 | -0.000090 | +0.000062 | true |

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m395_base | 0.8625 | 0.1375 | 1.835377 | 65.948641 |
| 9505 | m399s02_a050 | 0.8625 | 0.1375 | 1.835328 | 65.949556 |
| 9505 | m399s02_a050_reset | 0.8500 | 0.1500 | 1.833712 | 64.054345 |
| 9505 | m399s02_a050_zero_all | 0.8000 | 0.2000 | 1.852573 | 61.067216 |
| 9506 | m395_base | 0.8625 | 0.1375 | 1.852802 | 66.225763 |
| 9506 | m399s02_a050 | 0.8625 | 0.1375 | 1.852751 | 66.226705 |
| 9506 | m399s02_a050_reset | 0.8500 | 0.1500 | 1.849971 | 64.344403 |
| 9506 | m399s02_a050_zero_all | 0.8000 | 0.2000 | 1.870413 | 61.330565 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844039770
return mean: 66.088130
reset success mean: 0.85
zero-all success mean: 0.80
```

Versus the previous public base:

```text
success delta: 0.0
termination delta: 0.0
clearance margin delta: -0.000049788
return delta: +0.000928
```

## Interpretation

M400 promotes the M399 alpha `0.05` candidate as the new public-gate base. It
preserves the full public replay stack and behavior seeds, but the behavior
metrics are effectively unchanged. This remains a proof-safe bounded repair
promotion, not a meaningful driver-performance improvement.

The next step should audit whether the move is useful enough to chain another
repair or PPO step, and identify the next active boundary.

## Decision

Promote:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Decision:

```text
promote_m399_s02a050_public_gate_base
```

Next:

```text
m401-m400-bounded-promotion-utility-audit
```
