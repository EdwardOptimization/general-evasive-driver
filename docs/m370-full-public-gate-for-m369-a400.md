# M370 Full Public Gate For M369 A400

M370 runs the full public promotion gate for the M369 hard-row weighted repair
candidate. It does not run PPO or change actor inputs.

## Candidate

Previous public-gate base:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

Candidate:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

## Proof Sources

M369 already established:

| Gate | Result |
| --- | --- |
| Hard-row weighted direct repair | exact/surrogate pass, closed-loop endpoint fail |
| Old-key replay for alpha 0.4 | pass |
| Old-key replay for alpha 0.6 | fail on compact gap p10 |
| Source-diverse protected gate | 5 / 5 pass |
| M183/M170 first replay | 17 / 17 pass |
| M267/M264 first replay | 17 / 17 pass |

M370 promotes only the bounded alpha `0.4` candidate after full public gate.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000079341 | +0.000046984 | true |
| M183/M170 | 17 | 17 / 17 | +0.000078694 | +0.000046080 | true |
| M193/M189 | 14 | 14 / 14 | +0.000050676 | +0.000048992 | true |
| M212/M204 | 17 | 17 / 17 | +0.000057662 | +0.000050159 | true |
| M223/M219 | 17 | 17 / 17 | +0.000057662 | +0.000050166 | true |
| M267/M264 | 17 | 17 / 17 | +0.000057622 | +0.000050172 | true |

Run roots:

```text
runs/m370_full_public_gate_for_m369_a400/full_gates
runs/m369_hard_row_a400_m183_m170_first_replay
runs/m369_hard_row_a400_m267_m264_first_replay
```

## Behavior Retention

Behavior is retained on seeds `9505` and `9506`.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m365_base | 0.8625 | 0.1375 | 1.835795 | 65.941566 |
| 9505 | m369hr_a400 | 0.8625 | 0.1375 | 1.835518 | 65.948742 |
| 9505 | m369hr_a400_reset | 0.8500 | 0.1500 | 1.833915 | 64.053598 |
| 9505 | m369hr_a400_zero_all | 0.8000 | 0.2000 | 1.852706 | 61.066525 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m365_base | 0.8625 | 0.1375 | 1.853281 | 66.217844 |
| 9506 | m369hr_a400 | 0.8625 | 0.1375 | 1.852959 | 66.225656 |
| 9506 | m369hr_a400_reset | 0.8500 | 0.1500 | 1.850181 | 64.343603 |
| 9506 | m369hr_a400_zero_all | 0.8000 | 0.2000 | 1.870558 | 61.329729 |

Aggregate:

```text
success mean: 0.8625
termination mean: 0.1375
clearance margin mean: 1.844238544
reset success mean: 0.85
zero-all success mean: 0.80
```

## Interpretation

M370 promotes the M369 alpha `0.4` candidate as the current public-gate base.
This is still a proof-safe incremental step, not a large driver-performance
improvement. The important positive result is that hard-row weighted repair
creates a much stronger exact direction than M364, and a bounded interpolation
of that direction survives the full public proof and behavior stack.

The next blocker should audit the alpha `0.6` old-key gap-p10 failure. Since
alpha `0.6` has zero accepted regressions but fails the compact old-key gate on
gap distribution, the useful next step is a gap-erosion audit, not another
PPO run.

## Decision

Promote:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

Decision:

```text
promote_m369_a400_hard_row_weighted_public_gate_base
```

Next:

```text
m371-alpha06-old-key-gap-p10-audit
```
