# M565 BC Public Natural-Surface Eval

## Purpose

M565 evaluates the M563 L3 behavior-cloning checkpoint on the same four public
frozen-source natural surfaces used by M543 and M550.

This is public diagnostic evidence only. It does not use a private holdout and
does not promote a checkpoint.

## Evaluated Checkpoints

```text
l0_s3540      = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
l2_s3540      = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
l3_m542_s3540 = runs/m542_matched_l3_variance_seed3540/checkpoint.pt
l3_m563_bc    = runs/m563_l3_behavior_cloning_smoke/checkpoint.pt
```

All checkpoints keep the `P0_human_view_no_wheel_no_oracle` actor contract.

## Surface Runs

M565 ran `autodrift.frozen_source_surface_eval` on:

```text
runs/m565_public_eval_m497_short_reveal
runs/m565_public_eval_m497_warmup_capability
runs/m565_public_eval_m487_near_threshold
runs/m565_public_eval_m487_late_high_energy
runs/m565_bc_public_natural_surface_eval_aggregate/summary.json
```

The four source runs used the same source checkpoint, public pairs, tail
offsets, and continuation limits as M543/M550.

## Route Counts

| Surface | Outcome Rows | Invalid Rows |
| --- | ---: | ---: |
| M497 short reveal | 1772 | 21 |
| M497 warmup capability | 2764 | 21 |
| M487 near threshold | 2196 | 79 |
| M487 late high energy | 2244 | 59 |

The aggregate has:

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
| `l3_m542_s3540` | L3 | 2244 | 0.670677 | 0.668895 | 0.324421 | 28.966705 | 0.984809 | 0.619053 |
| `l3_m563_bc` | L3 | 2244 | 0.866310 | 0.862745 | 0.133690 | 38.377408 | 1.770749 | 1.525372 |

M563_BC matches L2 on success, completion, and collision, has slightly higher
mean return, and is only `0.007084` below L2 on mean clearance margin.

## Paired Deltas

Positive success/completion/return/margin deltas favor the first item. Negative
collision deltas are better.

| Comparison | Rows | Success Delta | Completion Delta | Collision Delta | Return Delta | Margin Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M563_BC - L0 | 2244 | +0.065508 | +0.063725 | -0.065508 | +2.659389 | +0.386690 |
| M563_BC - L2 | 2244 | +0.000000 | +0.000000 | +0.000000 | +0.175132 | -0.007084 |
| M563_BC - M542 L3 | 2244 | +0.195633 | +0.193850 | -0.190731 | +9.410703 | +0.785940 |
| L2 - L0 | 2244 | +0.065508 | +0.063725 | -0.065508 | +2.484257 | +0.393774 |
| M542 L3 - L2 | 2244 | -0.195633 | -0.193850 | +0.190731 | -9.235571 | -0.793024 |

First-action mean deltas:

| Comparison | Steer | Throttle | Brake |
| --- | ---: | ---: | ---: |
| M563_BC - L2 | -0.001903 | +0.014242 | -0.019448 |
| M563_BC - M542 L3 | +0.532177 | -0.360602 | +0.235282 |
| M563_BC - L0 | +0.270054 | -0.034977 | +0.154595 |

The first-action comparison confirms that M563_BC is behaviorally very close to
L2 and far from the failed original M542 L3.

## Per-Surface Direction

M563_BC is L2-equivalent on success/collision on every public surface. Its mean
margin is slightly below L2 on every surface:

```text
M487 late high energy:  M563_BC - L2 margin = -0.009412
M487 near threshold:    M563_BC - L2 margin = -0.003078
M497 short reveal:      M563_BC - L2 margin = -0.004635
M497 warmup capability: M563_BC - L2 margin = -0.009946
```

Against the original M542 L3, M563_BC improves success and margin on every
surface.

## Interpretation

M565 is a strong positive public diagnostic for L2-to-L3 distillation:

```text
The L3 online-GRU student can mimic the L2 finite-window policy closely enough
to repair the M543 public-surface L3 regression.
```

The important limitation is that this was still a tiny BC smoke trained from a
small non-public corpus. The result should not be promoted directly. It should
trigger a scaled distillation repeat with larger non-public train/validation
corpora, fresh route-screen selection, and then generalization gates.

## Decision

```text
bc_public_surface_eval_pass_admit_scaled_bc_repeat_design
```

M565 passes because M563_BC is L2-competitive on the public natural surfaces and
strongly improves over the original M542 L3, without actor-contract changes,
private-holdout claims, training during eval, or checkpoint promotion.

## Next

```text
M566: design a scaled L2-to-L3 BC repeat.
```

The scaled repeat should:

```text
use larger non-public train and validation corpora
train multiple BC seeds
rotate route-screen selection away from 17560
avoid tuning from public frozen-source failures
keep PPO blocked until scaled BC route/generalization evidence is stable
```
