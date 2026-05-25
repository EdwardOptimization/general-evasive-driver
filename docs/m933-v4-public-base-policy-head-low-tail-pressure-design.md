# M933 V4 Public Base Policy-Head Low-Tail Pressure Design

## Purpose

M932 evaluated the saved M930 raw actor_mean direction through alpha `1.0`.
The direction remained normal-safe and weakly improved low-tail metrics, but it
did not pass the registered tail-lift gate.

This suggests the actor head is not obviously blocked by normal retention, but
the M930 objective is underpowered for the low-tail rows. M933 designs one more
actor_mean-only objective pass before any broader actor surface is considered.

M933 is design-only. It does not train, run exact compatibility, run replay,
run PPO, or promote.

## Evidence From M932

At alpha `1.0`, the M930 raw actor_mean direction has:

```text
normal_retention_pass: true
first_action_drift_from_base_mean: 0.0023831567
first_action_drift_from_base_p95:  0.0040617720
normal_anchor_mse_mean:            0.0000022419
normal_anchor_mse_p95:             0.0000054996
normal_intervention_gap_p10:       0.0074899575
base near_gap_p10:                 0.0069862247
gap_deficit_mean:                  0.0163790291
base gap_deficit_mean:             0.0168765560
low_tail_fraction:                 0.3973619044
base low_tail_fraction:            0.4105523495
target_action_mse_mean:            0.0005316580
baseline target MSE:               0.0005333332
strict_target_action_mse_mean:     0.0005362949
near_tail_target_action_mse_mean:  0.0005065208
```

The important detail is not that M932 passed. It did not. The important detail
is that the raw actor_mean direction still has normal-retention slack while
moving some low-tail metrics in the right direction.

## Design Choice

Do not broaden the trainable surface yet.

Trainable parameters for the next implementation:

```text
allowed:   model.actor_mean.weight, model.actor_mean.bias
forbidden: response_encoder, context_encoder, online_gru_cell,
           response_context_fusion, critic, log_std, actor inputs
```

The next implementation should start again from the M399 public base, not from
the M930 raw checkpoint, so lineage stays clean and interpolation remains
base-relative.

## Proposed Objective

The M930 objective gave too much room to a weak direction. M934 should keep the
same sample reconstruction and target join, but increase low-tail effect-size
pressure.

Recommended coefficients:

```text
target_action_coef:          0.10
low_tail_gap_floor_coef:    10.00
low_tail_deficit_coef:       6.00
normal_retention_coef:      12.00
intervention_anchor_coef:    0.50
parameter_anchor_coef:       0.001
epochs:                    80
lr:                         0.001
```

Rationale:

- low-tail pressure should dominate because M932 shows the weak direction is
  below effect-size thresholds;
- normal retention should remain strong because the raw M930 direction had
  slack but should not be allowed to drift into a residual-style trust-region
  conflict;
- target action should become an auxiliary, because M932 showed aggregate and
  near-tail target MSE improve while strict target MSE worsens slightly.

## Diagnostics

M934 should preserve the existing strict candidate gate, but it must also
report these diagnostics so the next audit can distinguish failure modes:

```text
strict_candidate:
  normal_retention_pass
  tail_lift_pass
  target_loss_pass

low_tail_effect_candidate:
  normal_retention_pass
  tail_lift_pass

target_tolerance_candidate:
  normal_retention_pass
  tail_lift_pass
  target_action_mse_mean <= baseline + 0.000005
  strict_target_action_mse_mean <= baseline + 0.000005

normal_safe_low_tail_trend:
  normal_retention_pass
  low_tail_fraction < base low_tail_fraction
  gap_deficit_mean < base gap_deficit_mean
```

Only `strict_candidate` can route toward exact/replay admission. The other
diagnostics are not promotion gates; they decide whether the next blocker is a
target-active-set audit or a trainable-surface audit.

## Alpha Grid

Use the same extended alpha grid as M932:

```text
0.001, 0.002, 0.005, 0.010, 0.020, 0.050,
0.100, 0.200, 0.350, 0.500, 0.750, 1.000
```

## Route Logic

If M934 produces a strict candidate:

```text
route: exact no-update compatibility design before replay
```

If M934 produces a low-tail effect candidate but target loss fails:

```text
route: target-active-set audit; do not broaden actor surface yet
```

If M934 only improves low-tail trend but no tail-lift gate:

```text
route: actor_mean leverage audit and branch synthesis before broader update
```

If M934 violates normal retention at useful alphas:

```text
route: trust-region conflict audit; do not increase pressure further
```

## Next Blocker

```text
m934-v4-public-base-policy-head-low-tail-pressure-implementation
```

M934 should implement coefficient-configurable actor_mean-only training and run
the stronger low-tail pressure recipe. Replay, PPO, and promotion remain
blocked.
