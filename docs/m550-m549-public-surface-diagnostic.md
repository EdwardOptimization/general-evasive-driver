# M550 M549 Public Surface Diagnostic

## Purpose

M550 evaluates the M549 route-selected L3 checkpoint on the same four public
frozen-source natural surfaces used by M543.

This is public diagnostic evidence. It does not use a private holdout and does
not promote a checkpoint.

## Evaluated Checkpoints

```text
l0_s3540         = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
l2_s3540         = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
l3_m542_s3540    = runs/m542_matched_l3_variance_seed3540/checkpoint.pt
l3_m549_fast2816 = runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt
```

All checkpoints keep the `P0_human_view_no_wheel_no_oracle` actor contract.

## Artifacts

```text
runs/m550_public_eval_m497_short_reveal
runs/m550_public_eval_m497_warmup_capability
runs/m550_public_eval_m487_near_threshold
runs/m550_public_eval_m487_late_high_energy
runs/m550_m549_public_surface_diagnostic_aggregate/summary.json
runs/m550_m549_public_surface_diagnostic_aggregate/aggregate_by_baseline.csv
runs/m550_m549_public_surface_diagnostic_aggregate/surface_by_baseline.csv
runs/m550_m549_public_surface_diagnostic_aggregate/paired_deltas.csv
runs/m550_m549_public_surface_diagnostic_aggregate/terminal_pair_deltas.csv
runs/m550_m549_public_surface_diagnostic_aggregate/first_action_deltas.csv
```

## Route Counts

| Surface | Input Pairs | Source Snapshots | Outcome Rows | Invalid Rows |
| --- | ---: | ---: | ---: | ---: |
| M497 short reveal | `116` | `294` | `1772` | `21` |
| M497 warmup capability | `178` | `508` | `2764` | `21` |
| M487 near threshold | `157` | `371` | `2196` | `79` |
| M487 late high energy | `155` | `374` | `2244` | `59` |

The invalid rows match source-tail availability misses. Actor contract did not
change, and no training or promotion was performed.

## Aggregate Result

| Baseline | Level | Rows | Success | Completion | Collision | Return | Margin Mean | Margin Median |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | L0 | `2244` | `0.800802` | `0.799020` | `0.199198` | `35.718019` | `1.384059` | `1.096702` |
| `l2_s3540` | L2 | `2244` | `0.866310` | `0.862745` | `0.133690` | `38.202276` | `1.777833` | `1.524142` |
| `l3_m542_s3540` | L3 | `2244` | `0.670677` | `0.668895` | `0.324421` | `28.966705` | `0.984809` | `0.619053` |
| `l3_m549_fast2816` | L3 | `2244` | `0.724599` | `0.724599` | `0.274510` | `32.124622` | `1.148824` | `0.882422` |

The M549 selected checkpoint improves the original M542 L3 checkpoint, but it
is still below L0 and far below L2.

## Paired Deltas

Positive success/completion/return/margin deltas favor the first item.
Negative collision deltas are better.

| Comparison | Rows | Success Delta | Completion Delta | Collision Delta | Return Delta | Margin Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M549 L3 - L0 | `2244` | `-0.076203` | `-0.074421` | `+0.075312` | `-3.593397` | `-0.235235` |
| M549 L3 - L2 | `2244` | `-0.141711` | `-0.138146` | `+0.140820` | `-6.077654` | `-0.629009` |
| M549 L3 - M542 L3 | `2244` | `+0.053922` | `+0.055704` | `-0.049911` | `+3.157917` | `+0.164015` |
| L2 - L0 | `2244` | `+0.065508` | `+0.063725` | `-0.065508` | `+2.484257` | `+0.393774` |
| M542 L3 - L2 | `2244` | `-0.195633` | `-0.193850` | `+0.190731` | `-9.235571` | `-0.793024` |

## Per-Surface Result

| Surface | L0 Success | L2 Success | M542 L3 Success | M549 L3 Success | M549 L3 Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| M487 late high energy | `0.755793` | `0.846702` | `0.575758` | `0.655971` | `0.792691` |
| M487 near threshold | `0.899818` | `0.927140` | `0.845173` | `0.868852` | `1.736493` |
| M497 short reveal | `0.641084` | `0.715576` | `0.480813` | `0.525959` | `0.495962` |
| M497 warmup capability | `0.861071` | `0.930535` | `0.730825` | `0.793054` | `1.389604` |

M549 L3 improves over M542 L3 on every surface, but remains below L2 on every
surface and below L0 on every surface.

## Failure Pattern

Relative to L2, M549 L3 has:

```text
L2 obstacle_completed -> M549 collision rows = 308
L2 obstacle_completed -> M549 obstacle_completed rows = 1626
M549 first steer delta vs L2 = -0.395329
M549 first throttle delta vs L2 = +0.280788
M549 first brake delta vs L2 = -0.337612
```

Relative to original M542 L3, M549 L3 has:

```text
M542 L3 collision -> M549 obstacle_completed rows = 129
M542 L3 obstacle_completed -> M549 collision rows = 4
M549 first steer delta vs M542 L3 = +0.138751
M549 first throttle delta vs M542 L3 = -0.094055
M549 first brake delta vs M542 L3 = -0.082881
```

This confirms checkpoint selection repaired part of the original L3 failure, but
not enough to compete with the finite-window L2 baseline.

## Interpretation

M550 rejects the M549 selected checkpoint as a public-surface repair.

The key process lesson is that the 5-episode route-health gate is too weak as a
pre-public screen. It admitted a checkpoint that passed route health but still
failed the broader public frozen-source surfaces. The next step should redesign
the route/public diagnostic bridge before launching another repair training
branch.

The correct conclusion is:

```text
checkpoint selection improves L3 over the failed final checkpoint,
but current route-selected L3 still regresses against L0/L2 public diagnostics.
```

## Decision

```text
public_surface_regression_reject_repair_admit_m551_route_health_redesign
```
