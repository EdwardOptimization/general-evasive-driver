# M287 Balanced Rejected-Trajectory Repeat

M287 repeats the M286 repeat2 balanced rejected-history trajectory recipe on a
fresh optimizer seed.

No PPO or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

M286 promoted candidate:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
```

Fresh repeat update:

```text
runs/m287_balanced_rejected_trajectory_repeat/update_repeat2_s10_lr5e5_seed10080/optimized_checkpoint.pt
```

The update used the same repeat2 combined trajectory anchor as M286:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/anchors/repeat2/combined_recovery_rejected_anchor.npz
```

## Raw Fresh Update

The raw fresh-seed update improves exact M270 more than M286 raw, and it keeps
M267/M264 intact, but it is not proof-safe on the old M183/M170 surface.

| Candidate | Exact M270 loss | M183/M170 pass | M183/M170 normal success | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| M272 base | 0.681375623 | true | 1.000000 | 17 | true | 17 |
| M287 raw | 0.675918579 | false | 0.764706 | 13 | true | 17 |

This confirms that the repeat2 recipe keeps the current-family M267/M264
wrong-history surface, but the safe step size is optimizer-seed sensitive.

## Interpolation

The first coarse interpolation from M272 toward M287 raw found no nonzero safe
alpha at or above 0.05.

Refinement below 0.05 found the largest tested safe alpha at 0.005:

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| ---: | ---: | --- | ---: | --- | ---: |
| 0.0000 | 0.681375623 | true | 17 | true | 17 |
| 0.0005 | 0.681373119 | true | 17 | true | 17 |
| 0.0010 | 0.681370497 | true | 17 | true | 17 |
| 0.0020 | 0.681365550 | true | 17 | true | 17 |
| 0.0050 | 0.681348801 | true | 17 | true | 17 |
| 0.0100 | 0.681325078 | false | 16 | true | 17 |
| 0.0500 | 0.681107163 | false | 16 | true | 17 |

Selected safe repeat checkpoint:

```text
runs/m287_balanced_rejected_trajectory_repeat/interpolation_refine/checkpoints/alpha_0_005.pt
```

Objective improvement:

```text
0.6813756227493286 -> 0.6813488006591797
delta = -0.00002682209014892578
```

This is above the M285 micro-alpha result but far below the M286 selected
candidate:

```text
M286 delta = -0.0025473833084106445
M287 delta = -0.00002682209014892578
```

## Full Public Gates

The safe `m287r_a005` checkpoint passes the full public gate stack.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | -0.000002069 | +0.000000969 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | -0.000001979 | +0.000000953 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | -0.000001618 | +0.000000473 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | -0.000001817 | +0.000000478 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | -0.000001813 | +0.000000479 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | -0.000001812 | +0.000000480 | true |

The old protected-key diagnostic passes and remains discriminative:

```text
runs/m287_balanced_rejected_trajectory_repeat/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m272_base | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m287r_a005 | 0.8625 | 0.1375 | 1.835336 |
| 9505 | m287r_a005_reset | 0.8500 | 0.1500 | 1.833995 |
| 9505 | m287r_a005_zero_all | 0.8000 | 0.2000 | 1.853238 |
| 9506 | m272_base | 0.8625 | 0.1375 | 1.852854 |
| 9506 | m287r_a005 | 0.8625 | 0.1375 | 1.852852 |
| 9506 | m287r_a005_reset | 0.8500 | 0.1500 | 1.850265 |
| 9506 | m287r_a005_zero_all | 0.8000 | 0.2000 | 1.871146 |

## Interpretation

M287 is a weak repeat, not a PPO-unblocking repeat.

The important positive result is that the repeat2 recipe again points in a
direction that preserves M267/M264 and can be made public-gate safe. The
important negative result is that the safe alpha collapses from M286's 0.5 to
M287's 0.005. That is seed fragility. The current recipe is not stable enough
to justify PPO continuation.

The M286 checkpoint remains the better public-gate base. M287 should be archived
as repeat evidence and used to audit why the safe trust region varies so much
between optimizer seeds.

## Decision

Reject M287 as a promotion/PPO-admission repeat due to seed fragility.

Failure type:

```text
seed_fragility
```

Decision:

```text
reject_m287_balanced_repeat_seed_fragility
```

Next step:

```text
m288-balanced-repeat-seed-fragility-audit
```

M288 should compare M286 and M287 update directions on old-surface fragile rows
and decide whether the next repair is lower learning rate, fewer steps,
row-level terminal-margin anchoring, or per-source trust-region gating.
