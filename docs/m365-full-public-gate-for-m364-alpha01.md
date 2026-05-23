# M365 Full Public Gate For M364 Alpha01

M365 runs the full public promotion gate for the M364 old-key-aware repair
candidate. It does not run PPO or change actor inputs.

## Candidate

Previous public-gate base:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

Candidate:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

## Proof Sources

M364 already established:

| Gate | Result |
| --- | --- |
| Old-key replay for alpha 0.1 | pass |
| Old-key replay for alpha 0.2 | fail |
| Source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |
| M267/M264 first replay | 17 / 17 pass |

The direct old-key-aware repaired candidate still failed closed-loop old-key
replay by one accepted regression; M365 promotes only the bounded alpha `0.1`
candidate after full public gate.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000012448 | +0.000002007 | true |
| M183/M170 | 17 | 17 / 17 | +0.000012247 | +0.000002125 | true |
| M193/M189 | 14 | 14 / 14 | +0.000010662 | +0.000006356 | true |
| M212/M204 | 17 | 17 / 17 | +0.000010433 | +0.000006112 | true |
| M223/M219 | 17 | 17 / 17 | +0.000010440 | +0.000006114 | true |
| M267/M264 | 17 | 17 / 17 | +0.000010445 | +0.000006120 | true |

Run roots:

```text
runs/m365_full_public_gate_for_m364_alpha01/full_gates
runs/m364_alpha01_m183_m170_first_replay
runs/m364_alpha01_m267_m264_first_replay
```

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m360_base | 0.8625 | 0.1375 | 1.835795 | 65.941575 |
| 9505 | m364a_0_1 | 0.8625 | 0.1375 | 1.835795 | 65.941566 |
| 9505 | m364a_0_1_reset | 0.8500 | 0.1500 | 1.834314 | 64.031152 |
| 9505 | m364a_0_1_zero_all | 0.8000 | 0.2000 | 1.852955 | 61.058114 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m360_base | 0.8625 | 0.1375 | 1.853281 | 66.217853 |
| 9506 | m364a_0_1 | 0.8625 | 0.1375 | 1.853281 | 66.217844 |
| 9506 | m364a_0_1_reset | 0.8500 | 0.1500 | 1.850594 | 64.321032 |
| 9506 | m364a_0_1_zero_all | 0.8000 | 0.2000 | 1.870837 | 61.320958 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844537794
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M365 promotes the M364 alpha `0.1` candidate as the current public-gate base.
This is a proof-safe incremental step after old-key-aware repair, not a large
driver-performance improvement. The important positive result is that the M363
old-key-aware repair hook produced a bounded candidate that passed the full
public proof and behavior stack.

The next blocker should inspect the alpha `0.2` old-key failure row. Since
alpha `0.2` fails by one accepted regression, the useful next move is a targeted
hard-row audit and weighting/constraint design, not longer PPO.

## Decision

Promote:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

Decision:

```text
promote_m364_alpha01_old_key_aware_public_gate_base
```

Next:

```text
m366-alpha02-old-key-regression-audit
```
