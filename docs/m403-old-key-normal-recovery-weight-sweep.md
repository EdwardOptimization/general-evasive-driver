# M403 Old-Key Normal-Recovery Weight Sweep

M403 runs a no-PPO weight sweep for the M398 old-key normal-margin recovery
residual from the M400 base. It does not promote a checkpoint, lower thresholds,
or change actor inputs.

## Base

Current public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Active case:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

M398 target action direction:

```text
[-0.04 steer, -0.06 throttle, +0.08 brake]
```

## Endpoint Sweep

All variants use the same exact repair stack and no PPO. Only
`lambda_old_key_recovery` changes.

| Variant | Exact pass | exact M297 delta | exact M270 delta | Recovery loss | Distance to recovery action | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1e6 | true | -0.000566959 | -0.000330269 | 0.004015091 | 0.109548 | exact-safe but moves opposite target |
| 1e8 | true | -0.000437856 | -0.000248373 | 0.003975875 | 0.109398 | exact-safe but still opposite target |
| 1e9 | false | +0.000663519 | +0.000401020 | 0.003749713 | not audited | recovery improves but exact fails |
| 1e10 | false | +0.000617981 | +0.000372767 | 0.003747069 | 0.106124 | moves toward target but exact fails |

The low-weight settings remain dominated by exact/current-family objectives and
move the action away from the recovery target. The high-weight settings express
the recovery direction but immediately violate exact M297/M270 no-regression.

## LRec 1e10 Interpolation

Because the 1e10 endpoint moves in the desired direction, M403 interpolates from
the M400 base to that endpoint.

Interpolation:

```text
runs/m403_lrec1e10_interpolation
```

Exact eval:

| Alpha | exact M297 delta | exact M270 delta | Exact pass |
| ---: | ---: | ---: | --- |
| 0.025 | +0.000015497 | +0.000009298 | false |
| 0.05 | +0.000030875 | +0.000018656 | false |
| 0.10 | +0.000061750 | +0.000037313 | false |
| 0.20 | +0.000123620 | +0.000074625 | false |
| 0.40 | +0.000247240 | +0.000149131 | false |
| 0.60 | +0.000370860 | +0.000223637 | false |

Old-key compact replay goes the other way: it improves enough to pass up to
alpha `0.60` before failing at larger alpha.

```text
runs/m403_lrec1e10_interpolation_old_key_targeted_replay
runs/m403_r1e10a600_old_key_replay_gate
```

At alpha `0.60`, formal old-key compact replay passes with zero accepted
regressions.

However, M267/M264 first replay fails at alpha `0.60`:

```text
runs/m403_r1e10a600_m267_m264_first_replay
```

Key values:

```text
candidate success drops: 14 / 17
candidate wrong-history success rate: 0.176471
gate pass: false
```

## Classification

M403 does not find a promotable proof candidate.

Primary blocker:

```text
exact_objective_conflict_with_recovery_direction
```

Secondary blocker at larger alpha:

```text
current_family_wrong_history_washout
```

This means the next step should not be another blind recovery weight increase.
The correct next step is to attribute which exact M297/M270 rows oppose the
recovery direction, then decide whether the exact corpus needs reweighting,
row-specific protection, or a different trajectory-level recovery residual.

## Decision

Reject M403 candidates and admit an exact conflict row audit:

```text
m404-recovery-exact-conflict-row-audit
```
