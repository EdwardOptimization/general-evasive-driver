# M335 Short Source-Diverse PPO Escalation Run

M335 runs the 4096-step short PPO escalation registered by M334. The PPO
checkpoint is treated as proposal-only. M335 does not promote a new public
base.

## Raw PPO

Base:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

Config:

```text
configs/ppo_m335_short_source_diverse_escalation.json
```

Raw PPO run:

```text
runs/ppo_m335_short_source_diverse_escalation_seed5238
```

Raw PPO metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 72.522298 |
| reward_mean | 1.074854 |
| train termination_rate | 0.125000 |
| eval return_mean | 57.878072 |
| eval termination_rate | 0.200000 |

The raw PPO checkpoint is not promotable.

## Exact Repair

Exact repair run:

```text
runs/m335_exact_repair_from_raw_s40_seed10099
```

Repaired endpoint:

```text
runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
```

Exact objective retention versus M333:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000355124 |
| Exact M270 source-balanced outcome | -0.000168264 |

Both exact objectives pass no-regression at the repaired endpoint.

## Old-Key Gap Floor

The repaired endpoint fails the old-key gap floor:

| Policy | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: |
| m333_base | 0.216606 | 0.126452 | 0.090155 |
| m335_repaired | 0.235477 | 0.170117 | 0.065360 |

M335 therefore runs the registered bounded interpolation instead of running
first replay on the repaired endpoint.

## Bounded Interpolation

Run dir:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation
```

Alpha grid:

```text
0, 0.001, 0.0025, 0.005, 0.006, 0.00625, 0.0065, 0.0075, 0.01, 0.02, 0.05, 0.1, 0.2, 1.0
```

Old-key gap around the decision boundary:

| Policy | Alpha | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: | ---: |
| m335_a0065 | 0.0065 | 0.216759 | 0.126720 | 0.090039 |
| m335_a0075 | 0.0075 | 0.216783 | 0.126762 | 0.090021 |
| m335_a010 | 0.0100 | 0.216841 | 0.126865 | 0.089977 |
| m335_a1000 | 1.0000 | 0.235477 | 0.170117 | 0.065360 |

The largest alpha in the registered grid satisfying the old-key floor is:

```text
alpha = 0.0075
margin_gap = 0.09002140115294455
```

Exact objective retention for alpha `0.0075`:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000002742 |
| Exact M270 source-balanced outcome | -0.000001252 |

The movement is positive but very small because the old-key gap floor is again
the limiting constraint.

## Source-Diverse Protected Gate

Run dir:

```text
runs/m335_a0075_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass at alpha `0.0075`.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | +0.000004170 | +0.000002575 | true |
| m328_continuity_surface | 17 | 17 | +0.000094808 | +0.000040305 | true |
| m325_continuity_surface | 17 | 17 | +0.000288642 | +0.000125182 | true |
| m317_continuity_surface | 17 | 17 | +0.000483439 | +0.000205426 | true |
| m314_continuity_surface | 17 | 17 | +0.000483960 | +0.000205622 | true |

## First Replay Gates

Both first replay gates pass at alpha `0.0075`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000004931 | +0.000000892 | true |
| M267/M264 | 17 | 17 / 17 | +0.000004169 | +0.000002572 | true |

## Interpretation

M335 is a mixed positive result.

Positive:

```text
raw PPO completes,
exact repair produces a strong exact-objective improvement,
bounded alpha 0.0075 passes exact/source-diverse/old-key/first replay gates.
```

Limitation:

```text
the old 9944 gap floor only admits alpha 0.0075,
so the accepted movement is much smaller than the repaired endpoint.
```

This supports running a full public gate for the bounded candidate, but it also
shows that the short PPO direction is heavily constrained by old-key gap
erosion. If M336 promotes, the next research question should be whether to keep
using the fixed `9944` gap floor or refresh the old-key diagnostic into a
source-diverse gap distribution before further PPO escalation.

## Decision

Admit:

```text
m336-full-public-gate-for-m335-a0075
```

Decision:

```text
admit_m336_full_public_gate_for_m335_a0075
```
