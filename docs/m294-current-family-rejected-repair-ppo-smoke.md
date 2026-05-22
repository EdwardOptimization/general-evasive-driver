# M294 Current-Family Rejected Repair PPO Smoke

M294 runs the stronger current-family rejected-history repair smoke designed in
M293. It remains smoke-scale at 1024 PPO steps.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Config:

```text
configs/ppo_m294_current_family_rejected_repair_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt
```

M294 increases current-family rejected-history pressure by using the M293
failed-row extra4 anchor and raises the fixed M270 objective coefficient.

## Raw PPO

Raw M294 is rejected. It preserves M183/M170 but still loses M267/M264 and
worsens exact M270.

| Candidate | Exact M270 loss | Delta vs M290 | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| m290x64_a500 | 0.679278374 | 0.000000000 | true | 17 | true | 17 |
| m294raw | 0.679893672 | +0.000615299 | true | 17 | false | 14 |

Compared with M291 raw, the targeted anchor recovers one current-family row:

| Run | Failed M267/M264 rows |
| --- | --- |
| M291 raw | 6, 11, 15, 16 |
| M294 raw | 6, 15, 16 |

This is partial evidence that the repair points in the right direction, but it
is not sufficient.

## Exact M270 Interpolation Gate

M294 requires exact M270 no-regression before broader gates. No nonzero
interpolation alpha satisfies that condition.

| Alpha | Exact M270 loss | Delta vs M290 |
| ---: | ---: | ---: |
| 0.000 | 0.679278374 | 0.000000000 |
| 0.001 | 0.679279029 | +0.000000656 |
| 0.005 | 0.679281473 | +0.000003099 |
| 0.010 | 0.679284573 | +0.000006199 |
| 0.050 | 0.679309309 | +0.000030935 |
| 0.100 | 0.679340303 | +0.000061929 |
| 0.200 | 0.679401219 | +0.000122845 |
| 0.500 | 0.679584861 | +0.000306487 |
| 1.000 | 0.679893672 | +0.000615299 |

Because exact M270 no-regression fails for every nonzero alpha, M294 does not
run full replay/protected-key/behavior gates.

## Interpretation

M294 confirms that simply increasing failed-row trajectory anchoring is not
enough. It reduces current-family washout from four rows to three, but PPO still
pushes wrong-history margins positive and now worsens the fixed objective more
than M291.

The next repair should audit why M294's stronger anchor improves M267 row count
but worsens exact M270. A likely direction is to stop treating this as a generic
action-anchor problem and introduce a more direct rejected-history margin or
pairwise preference protection for the current-family rows.

## Decision

Reject M294.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
reject_m294_repair_smoke_objective_regression_and_m267_washout
```

Next step:

```text
m295-current-family-ppo-repair-audit
```
