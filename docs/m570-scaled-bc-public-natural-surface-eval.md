# M570 Scaled BC Public Natural-Surface Eval

## Purpose

M570 evaluates the selected scaled BC checkpoint `BC5660` on the same four
public frozen-source natural surfaces used by M543, M550, and M565.

This is public diagnostic evidence only. It does not use a private holdout and
does not promote a checkpoint.

## Evaluated Checkpoints

```text
l0_s3540      = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
l2_s3540      = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
l3_m542_s3540 = runs/m542_matched_l3_variance_seed3540/checkpoint.pt
l3_bc5660     = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

All checkpoints keep the `P0_human_view_no_wheel_no_oracle` actor contract.

## Surface Runs

M570 ran `autodrift.frozen_source_surface_eval` on:

```text
runs/m570_public_eval_m497_short_reveal
runs/m570_public_eval_m497_warmup_capability
runs/m570_public_eval_m487_near_threshold
runs/m570_public_eval_m487_late_high_energy
runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json
```

The four source runs used the same source checkpoint, public pairs, tail
offsets, and continuation limits as M543/M550/M565.

## Counts

```text
input_outcome_rows = 8976
complete_quad_keys = 2244
incomplete_quad_keys = 0
actor_contract_changed = false
training_or_promotion_performed = false
```

## Aggregate Result

| Baseline | Level | Rows | Success | Completion | Collision | Return | Margin Mean | Margin Median |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | L0 | 2244 | 0.800802 | 0.799020 | 0.199198 | 35.718019 | 1.384059 | 1.096702 |
| `l2_s3540` | L2 | 2244 | 0.866310 | 0.862745 | 0.133690 | 38.202276 | 1.777833 | 1.524142 |
| `l3_bc5660` | L3 | 2244 | 0.866310 | 0.860517 | 0.133690 | 38.080081 | 1.782199 | 1.523971 |
| `l3_m542_s3540` | L3 | 2244 | 0.670677 | 0.668895 | 0.324421 | 28.966705 | 0.984809 | 0.619053 |

BC5660 matches L2 on success and collision, is slightly lower on completion,
and has slightly higher mean clearance margin.

## Paired Deltas

Positive success/completion/return/margin deltas favor the first item. Negative
collision deltas are better.

| Comparison | Rows | Success Delta | Completion Delta | Collision Delta | Return Delta | Margin Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BC5660 - L0 | 2244 | +0.065508 | +0.061497 | -0.065508 | +2.362062 | +0.398140 |
| BC5660 - L2 | 2244 | +0.000000 | -0.002228 | +0.000000 | -0.122195 | +0.004366 |
| BC5660 - M542 L3 | 2244 | +0.195633 | +0.191622 | -0.190731 | +9.113376 | +0.797390 |
| L2 - L0 | 2244 | +0.065508 | +0.063725 | -0.065508 | +2.484257 | +0.393774 |
| M542 L3 - L2 | 2244 | -0.195633 | -0.193850 | +0.190731 | -9.235571 | -0.793024 |

First-action mean deltas:

| Comparison | Steer | Throttle | Brake |
| --- | ---: | ---: | ---: |
| BC5660 - L2 | +0.146033 | +0.005578 | +0.083952 |
| BC5660 - M542 L3 | +0.680113 | -0.369266 | +0.338683 |
| BC5660 - L0 | +0.417991 | -0.043642 | +0.257995 |

BC5660 is behaviorally not identical to L2 at the first action, but it matches
L2 terminal success/collision and slightly improves mean margin on these public
surfaces.

## Interpretation

M570 confirms that the scaled BC repeat preserves the M565 public-surface repair:

```text
BC5660 is L2-competitive on public natural surfaces.
BC5660 strongly repairs the original M542 L3 regression.
The result remains public diagnostic evidence only.
```

The next required evidence layer is fresh non-public/generalization route
evaluation. Promotion and PPO remain premature.

## Decision

```text
scaled_bc_public_surface_pass_admit_fresh_route_generalization_design
```

M570 passes as a public diagnostic because selected BC5660 is L2-competitive and
repairs original L3 without actor-contract changes, training during eval,
private-holdout claims, or checkpoint promotion.

## Next

```text
M571: design fresh non-public route/generalization gates for BC5660.
```
